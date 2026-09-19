"""Versioned data contracts used by snapshots, policies, and reports."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Reject unknown fields so policy typos do not silently weaken checks."""

    model_config = ConfigDict(extra="forbid")


class ServerIdentity(StrictModel):
    name: str | None = None
    version: str | None = None
    protocol_version: str


class ToolContract(StrictModel):
    name: str
    title: str | None = None
    description: str | None = None
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] | None = None
    annotations: dict[str, Any] | None = None
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class ToolCatalogSnapshot(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    captured_at: str
    server: ServerIdentity
    tools: list[ToolContract]


class RedactionPolicy(StrictModel):
    sensitive_key_patterns: list[str] = Field(
        default_factory=lambda: [
            r"(?i)(^|[-_])(api[-_]?key|authorization|cookie|password|secret|token)([-_]|$)"
        ]
    )
    replacement: str = "[REDACTED]"
    max_string_length: int = Field(default=2048, ge=32, le=1_000_000)


class RuntimeCondition(StrictModel):
    path: str = Field(pattern=r"^(/([^/~]|~[01])*)*$")
    operator: Literal[
        "exists",
        "equals",
        "not_equals",
        "matches",
        "not_matches",
        "in",
        "not_in",
        "url_scheme_not_in",
        "url_host_not_in",
    ]
    value: Any = None
    action: Literal["deny", "require_approval"] = "deny"
    reason: str


class RuntimeRule(StrictModel):
    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    tool_pattern: str
    action: Literal["allow", "deny", "require_approval"] = "allow"
    reason: str
    conditions: list[RuntimeCondition] = Field(default_factory=list)


class Policy(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    allowed_tools: list[str] | None = None
    denied_name_patterns: list[str] = Field(default_factory=list)
    require_descriptions: bool = True
    require_closed_input_schemas: bool = False
    fail_on: Literal["warning", "error", "never"] = "error"
    default_runtime_action: Literal["allow", "deny", "require_approval"] = "deny"
    runtime_rules: list[RuntimeRule] = Field(default_factory=list)
    redaction: RedactionPolicy = Field(default_factory=RedactionPolicy)


class ContractChange(StrictModel):
    path: str
    kind: Literal["added", "removed", "changed"]
    impact: Literal["broadening", "narrowing", "behavioral", "metadata"]
    before: Any = None
    after: Any = None
    explanation: str


class Finding(StrictModel):
    rule_id: str
    severity: Literal["warning", "error"]
    message: str
    tool: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ReportSummary(StrictModel):
    errors: int
    warnings: int
    total: int


class RiskContribution(StrictModel):
    rule_id: str
    tool: str | None = None
    points: int = Field(ge=0)
    reason: str


class RiskSummary(StrictModel):
    score: int = Field(ge=0, le=100)
    rating: Literal["none", "low", "moderate", "high", "critical"]
    contributions: list[RiskContribution]


class AnalysisReport(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at: str
    baseline_captured_at: str | None = None
    current_captured_at: str
    passed: bool
    fail_on: Literal["warning", "error", "never"]
    summary: ReportSummary
    risk: RiskSummary
    findings: list[Finding]


class RuntimeDecision(StrictModel):
    outcome: Literal["allow", "deny", "approval_required"]
    approved: bool = False
    matched_rules: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class TraceEvent(StrictModel):
    sequence: int = Field(ge=0)
    timestamp: str
    event_type: Literal["catalog", "request", "decision", "response", "error"]
    tool: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    previous_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    event_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class TraceSummary(StrictModel):
    outcome: Literal["allow", "deny", "approval_required", "error"]
    call_executed: bool
    response_is_error: bool | None = None
    redaction_count: int = Field(ge=0)
    event_count: int = Field(ge=0)
    duration_ms: float = Field(ge=0)


class ExecutionTrace(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    trace_id: str
    started_at: str
    completed_at: str
    server: ServerIdentity
    tool: str
    integrity: Literal["sha256-chain-v1"] = "sha256-chain-v1"
    events: list[TraceEvent]
    summary: TraceSummary
    trace_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class ScenarioExpectation(StrictModel):
    outcome: Literal["allow", "deny", "approval_required", "error"]
    call_executed: bool
    minimum_redactions: int = Field(default=0, ge=0)
    matched_rules: list[str] = Field(default_factory=list)


class ScenarioCase(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    title: str
    category: str = Field(min_length=1)
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    approved: bool = False
    expect: ScenarioExpectation


class ScenarioSuite(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    name: str
    description: str
    cases: list[ScenarioCase] = Field(min_length=1)


class ScenarioCheck(StrictModel):
    name: str
    passed: bool
    expected: Any = None
    observed: Any = None


class ScenarioCaseResult(StrictModel):
    id: str
    title: str
    category: str
    passed: bool
    trace_file: str
    trace_id: str
    checks: list[ScenarioCheck]


class ScenarioSummary(StrictModel):
    passed: int = Field(ge=0)
    failed: int = Field(ge=0)
    total: int = Field(ge=0)
    score_percent: float = Field(ge=0, le=100)
    category_scores: dict[str, float]


class ScenarioReport(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    suite_name: str
    generated_at: str
    server: ServerIdentity
    passed: bool
    summary: ScenarioSummary
    results: list[ScenarioCaseResult]


class BenchmarkTiming(StrictModel):
    median_ms: float = Field(ge=0)
    p95_ms: float = Field(ge=0)


class ScaleBenchmarkResult(StrictModel):
    tool_count: int = Field(gt=0)
    controlled_changes: int = Field(ge=0)
    fingerprint: BenchmarkTiming
    analysis: BenchmarkTiming
    fingerprint_tools_per_second: float = Field(ge=0)
    snapshot_bytes: int = Field(ge=0)
    report_bytes: int = Field(ge=0)
    findings: int = Field(ge=0)
    risk_score: int = Field(ge=0, le=100)


class BenchmarkEnvironment(StrictModel):
    python: str
    platform: str
    processor: str


class BenchmarkConfig(StrictModel):
    sizes: list[int]
    trials: int = Field(gt=0)
    warmups: int = Field(ge=0)


class CatalogBenchmarkReport(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at: str
    environment: BenchmarkEnvironment
    config: BenchmarkConfig
    results: list[ScaleBenchmarkResult]


class BenchmarkBudgetLimit(StrictModel):
    tool_count: int = Field(gt=0)
    max_fingerprint_median_ms: float = Field(gt=0)
    max_analysis_median_ms: float = Field(gt=0)
    min_fingerprint_tools_per_second: float = Field(ge=0)
    max_snapshot_bytes: int = Field(gt=0)
    max_report_bytes: int = Field(gt=0)


class BenchmarkBudget(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    description: str
    limits: list[BenchmarkBudgetLimit] = Field(min_length=1)


class BenchmarkBudgetViolation(StrictModel):
    tool_count: int = Field(gt=0)
    metric: str
    actual: float
    operator: Literal["<=", ">="]
    limit: float
    message: str


class BenchmarkBudgetReport(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at: str
    benchmark_generated_at: str
    passed: bool
    evaluated_limits: int = Field(ge=0)
    violations: list[BenchmarkBudgetViolation]
