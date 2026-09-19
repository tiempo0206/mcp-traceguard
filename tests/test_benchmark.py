from mcp_traceguard.benchmark import benchmark_catalog, check_benchmark_budget
from mcp_traceguard.models import BenchmarkBudget, BenchmarkBudgetLimit


def test_catalog_benchmark_reports_controlled_scale() -> None:
    report = benchmark_catalog(sizes=[10], trials=2, warmups=0)
    result = report.results[0]
    assert report.config.sizes == [10]
    assert result.tool_count == 10
    assert result.controlled_changes == 3
    assert result.findings == 5
    assert result.risk_score > 0
    assert result.snapshot_bytes > result.report_bytes
    assert result.fingerprint_tools_per_second > 0


def test_benchmark_budget_passes_and_reports_regressions() -> None:
    benchmark = benchmark_catalog(sizes=[10], trials=1, warmups=0)
    result = benchmark.results[0]
    passing = BenchmarkBudget(
        description="test",
        limits=[
            BenchmarkBudgetLimit(
                tool_count=10,
                max_fingerprint_median_ms=result.fingerprint.median_ms + 1,
                max_analysis_median_ms=result.analysis.median_ms + 1,
                min_fingerprint_tools_per_second=0,
                max_snapshot_bytes=result.snapshot_bytes + 1,
                max_report_bytes=result.report_bytes + 1,
            )
        ],
    )
    assert check_benchmark_budget(benchmark, passing).passed

    failing = passing.model_copy(deep=True)
    failing.limits[0].max_report_bytes = result.report_bytes - 1
    checked = check_benchmark_budget(benchmark, failing)
    assert not checked.passed
    assert checked.violations[0].metric == "report_bytes"


def test_benchmark_budget_requires_each_configured_scale() -> None:
    benchmark = benchmark_catalog(sizes=[10], trials=1, warmups=0)
    budget = BenchmarkBudget(
        description="missing scale",
        limits=[
            BenchmarkBudgetLimit(
                tool_count=100,
                max_fingerprint_median_ms=100,
                max_analysis_median_ms=100,
                min_fingerprint_tools_per_second=0,
                max_snapshot_bytes=1_000_000,
                max_report_bytes=1_000_000,
            )
        ],
    )
    checked = check_benchmark_budget(benchmark, budget)
    assert not checked.passed
    assert checked.violations[0].metric == "result_present"
