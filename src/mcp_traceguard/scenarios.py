"""Replay versioned security scenarios against a real MCP target."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from mcp_traceguard.models import (
    ExecutionTrace,
    Policy,
    ScenarioCaseResult,
    ScenarioCheck,
    ScenarioReport,
    ScenarioSuite,
    ScenarioSummary,
)
from mcp_traceguard.runtime import execute_guarded_call, verify_trace
from mcp_traceguard.snapshot import utc_now


def _matched_rules(trace: ExecutionTrace) -> list[str]:
    decision = next(
        (event for event in trace.events if event.event_type == "decision"),
        None,
    )
    if decision is None:
        return []
    value = decision.payload.get("matched_rules", [])
    return list(value) if isinstance(value, list) else []


async def replay_suite(
    target: Any,
    *,
    suite: ScenarioSuite,
    policy: Policy,
) -> tuple[ScenarioReport, dict[str, ExecutionTrace]]:
    """Execute every case and score observable behavior against expectations."""

    traces: dict[str, ExecutionTrace] = {}
    results: list[ScenarioCaseResult] = []
    for case in suite.cases:
        trace = await execute_guarded_call(
            target,
            tool=case.tool,
            arguments=case.arguments,
            policy=policy,
            approved=case.approved,
        )
        traces[case.id] = trace
        observed_rules = _matched_rules(trace)
        integrity_errors = verify_trace(trace)
        checks = [
            ScenarioCheck(
                name="outcome",
                passed=trace.summary.outcome == case.expect.outcome,
                expected=case.expect.outcome,
                observed=trace.summary.outcome,
            ),
            ScenarioCheck(
                name="call_executed",
                passed=trace.summary.call_executed == case.expect.call_executed,
                expected=case.expect.call_executed,
                observed=trace.summary.call_executed,
            ),
            ScenarioCheck(
                name="minimum_redactions",
                passed=trace.summary.redaction_count >= case.expect.minimum_redactions,
                expected=case.expect.minimum_redactions,
                observed=trace.summary.redaction_count,
            ),
            ScenarioCheck(
                name="matched_rules",
                passed=observed_rules == case.expect.matched_rules,
                expected=case.expect.matched_rules,
                observed=observed_rules,
            ),
            ScenarioCheck(
                name="trace_integrity",
                passed=not integrity_errors,
                expected=[],
                observed=integrity_errors,
            ),
        ]
        results.append(
            ScenarioCaseResult(
                id=case.id,
                title=case.title,
                category=case.category,
                passed=all(check.passed for check in checks),
                trace_file=f"{case.id}.trace.json",
                trace_id=trace.trace_id,
                checks=checks,
            )
        )

    passed = sum(result.passed for result in results)
    category_totals: dict[str, int] = defaultdict(int)
    category_passed: dict[str, int] = defaultdict(int)
    for result in results:
        category_totals[result.category] += 1
        category_passed[result.category] += int(result.passed)
    category_scores = {
        category: round(category_passed[category] / total * 100, 2)
        for category, total in sorted(category_totals.items())
    }
    summary = ScenarioSummary(
        passed=passed,
        failed=len(results) - passed,
        total=len(results),
        score_percent=round(passed / len(results) * 100, 2),
        category_scores=category_scores,
    )
    return (
        ScenarioReport(
            suite_name=suite.name,
            generated_at=utc_now(),
            server=next(iter(traces.values())).server,
            passed=passed == len(results),
            summary=summary,
            results=results,
        ),
        traces,
    )
