"""Reproducible synthetic scale benchmark for catalog fingerprinting and analysis."""

from __future__ import annotations

import math
import platform
import statistics
import sys
import time
from collections.abc import Callable
from typing import Any

from mcp_traceguard.analysis import analyze_snapshot
from mcp_traceguard.models import (
    BenchmarkBudget,
    BenchmarkBudgetReport,
    BenchmarkBudgetViolation,
    BenchmarkConfig,
    BenchmarkEnvironment,
    BenchmarkTiming,
    CatalogBenchmarkReport,
    Policy,
    ScaleBenchmarkResult,
    ServerIdentity,
    ToolCatalogSnapshot,
)
from mcp_traceguard.snapshot import build_tool_contract, canonical_json, utc_now


def _tool(index: int, *, drifted: bool = False) -> dict[str, Any]:
    mode_values = ["read", "write"] if drifted else ["read"]
    return {
        "name": f"catalog_tool_{index:05d}",
        "description": (
            f"Read or write deterministic item {index}"
            if drifted
            else f"Read deterministic item {index}"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "minLength": 1},
                "mode": {"type": "string", "enum": mode_values},
            },
            "required": ["item_id"],
            "additionalProperties": False,
        },
        "output_schema": {
            "type": "object",
            "properties": {"value": {"type": "string"}},
            "required": ["value"],
            "additionalProperties": False,
        },
    }


def _timed(operation: Callable[[], Any], *, trials: int, warmups: int) -> tuple[Any, list[float]]:
    for _ in range(warmups):
        operation()
    durations: list[float] = []
    result: Any = None
    for _ in range(trials):
        start = time.perf_counter()
        result = operation()
        durations.append((time.perf_counter() - start) * 1000)
    return result, durations


def _timing(values: list[float]) -> BenchmarkTiming:
    ordered = sorted(values)
    p95_index = max(0, math.ceil(len(ordered) * 0.95) - 1)
    return BenchmarkTiming(
        median_ms=round(statistics.median(ordered), 3),
        p95_ms=round(ordered[p95_index], 3),
    )


def _snapshot(tools: list[Any]) -> ToolCatalogSnapshot:
    return ToolCatalogSnapshot(
        captured_at="benchmark",
        server=ServerIdentity(
            name="synthetic-catalog",
            version="1.0",
            protocol_version="2026-07-28",
        ),
        tools=tools,
    )


def benchmark_catalog(
    *,
    sizes: list[int],
    trials: int = 7,
    warmups: int = 2,
) -> CatalogBenchmarkReport:
    """Benchmark controlled catalogs; no network, model, or server is required."""

    if not sizes or any(size <= 1 for size in sizes):
        raise ValueError("Benchmark sizes must all be greater than one")
    if trials <= 0 or warmups < 0:
        raise ValueError("Trials must be positive and warmups cannot be negative")

    results: list[ScaleBenchmarkResult] = []
    for size in sizes:
        baseline_specs = [_tool(index) for index in range(size)]
        drift_count = max(1, size // 100)
        current_specs = [_tool(index, drifted=index < drift_count) for index in range(size - 1)]
        current_specs.append(
            {
                "name": "shell_exec_added",
                "description": "Controlled high-risk tool added for benchmark scoring",
                "input_schema": {
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"],
                },
            }
        )

        baseline_tools = [build_tool_contract(spec) for spec in baseline_specs]
        baseline = _snapshot(baseline_tools)

        def fingerprint_operation(specs: list[dict[str, Any]] = current_specs) -> list[Any]:
            return [build_tool_contract(spec) for spec in specs]

        current_tools, fingerprint_durations = _timed(
            fingerprint_operation,
            trials=trials,
            warmups=warmups,
        )
        current = _snapshot(current_tools)
        policy = Policy(
            allowed_tools=[tool.name for tool in baseline.tools],
            denied_name_patterns=[r"(^|_)(exec|shell)(_|$)"],
        )

        def analysis_operation(
            current_snapshot: ToolCatalogSnapshot = current,
            baseline_snapshot: ToolCatalogSnapshot = baseline,
            current_policy: Policy = policy,
        ):
            return analyze_snapshot(
                current_snapshot,
                baseline=baseline_snapshot,
                policy=current_policy,
            )

        report, analysis_durations = _timed(
            analysis_operation,
            trials=trials,
            warmups=warmups,
        )
        fingerprint_timing = _timing(fingerprint_durations)
        throughput = (
            size / (fingerprint_timing.median_ms / 1000) if fingerprint_timing.median_ms else 0
        )
        results.append(
            ScaleBenchmarkResult(
                tool_count=size,
                controlled_changes=drift_count + 2,
                fingerprint=fingerprint_timing,
                analysis=_timing(analysis_durations),
                fingerprint_tools_per_second=round(throughput, 2),
                snapshot_bytes=len(canonical_json(current.model_dump(mode="json")).encode()),
                report_bytes=len(canonical_json(report.model_dump(mode="json")).encode()),
                findings=report.summary.total,
                risk_score=report.risk.score,
            )
        )

    return CatalogBenchmarkReport(
        generated_at=utc_now(),
        environment=BenchmarkEnvironment(
            python=sys.version.split()[0],
            platform=platform.platform(),
            processor=platform.processor() or platform.machine(),
        ),
        config=BenchmarkConfig(sizes=sizes, trials=trials, warmups=warmups),
        results=results,
    )


def check_benchmark_budget(
    report: CatalogBenchmarkReport,
    budget: BenchmarkBudget,
) -> BenchmarkBudgetReport:
    """Compare a benchmark report with explicit, machine-independent guardrails."""

    results = {result.tool_count: result for result in report.results}
    violations: list[BenchmarkBudgetViolation] = []

    def compare(
        *,
        tool_count: int,
        metric: str,
        actual: float,
        operator: str,
        limit: float,
    ) -> None:
        failed = actual > limit if operator == "<=" else actual < limit
        if failed:
            violations.append(
                BenchmarkBudgetViolation(
                    tool_count=tool_count,
                    metric=metric,
                    actual=actual,
                    operator=operator,
                    limit=limit,
                    message=f"{metric} was {actual:g}; required {operator} {limit:g}",
                )
            )

    for limit in budget.limits:
        result = results.get(limit.tool_count)
        if result is None:
            violations.append(
                BenchmarkBudgetViolation(
                    tool_count=limit.tool_count,
                    metric="result_present",
                    actual=0,
                    operator=">=",
                    limit=1,
                    message=f"No benchmark result exists for {limit.tool_count} tools",
                )
            )
            continue
        compare(
            tool_count=limit.tool_count,
            metric="fingerprint.median_ms",
            actual=result.fingerprint.median_ms,
            operator="<=",
            limit=limit.max_fingerprint_median_ms,
        )
        compare(
            tool_count=limit.tool_count,
            metric="analysis.median_ms",
            actual=result.analysis.median_ms,
            operator="<=",
            limit=limit.max_analysis_median_ms,
        )
        compare(
            tool_count=limit.tool_count,
            metric="fingerprint_tools_per_second",
            actual=result.fingerprint_tools_per_second,
            operator=">=",
            limit=limit.min_fingerprint_tools_per_second,
        )
        compare(
            tool_count=limit.tool_count,
            metric="snapshot_bytes",
            actual=result.snapshot_bytes,
            operator="<=",
            limit=limit.max_snapshot_bytes,
        )
        compare(
            tool_count=limit.tool_count,
            metric="report_bytes",
            actual=result.report_bytes,
            operator="<=",
            limit=limit.max_report_bytes,
        )

    return BenchmarkBudgetReport(
        generated_at=utc_now(),
        benchmark_generated_at=report.generated_at,
        passed=not violations,
        evaluated_limits=len(budget.limits),
        violations=violations,
    )
