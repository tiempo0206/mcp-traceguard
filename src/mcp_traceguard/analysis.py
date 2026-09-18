"""Policy and baseline analysis for MCP tool catalogs."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from mcp_traceguard.models import (
    AnalysisReport,
    Finding,
    Policy,
    ReportSummary,
    ToolCatalogSnapshot,
    ToolContract,
)


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _changed_fields(before: ToolContract, after: ToolContract) -> list[str]:
    fields = ("title", "description", "input_schema", "output_schema", "annotations")
    return [field for field in fields if getattr(before, field) != getattr(after, field)]


def _is_open_object_schema(tool: ToolContract) -> bool:
    schema = tool.input_schema
    return schema.get("type") == "object" and schema.get("additionalProperties") is not False


def _baseline_findings(
    current: ToolCatalogSnapshot, baseline: ToolCatalogSnapshot
) -> list[Finding]:
    findings: list[Finding] = []
    current_by_name = {tool.name: tool for tool in current.tools}
    baseline_by_name = {tool.name: tool for tool in baseline.tools}

    for name in sorted(current_by_name.keys() - baseline_by_name.keys()):
        findings.append(
            Finding(
                rule_id="TG101",
                severity="error",
                tool=name,
                message=f"Tool {name!r} was added after the approved baseline",
            )
        )
    for name in sorted(baseline_by_name.keys() - current_by_name.keys()):
        findings.append(
            Finding(
                rule_id="TG102",
                severity="warning",
                tool=name,
                message=f"Tool {name!r} was removed after the approved baseline",
            )
        )
    for name in sorted(current_by_name.keys() & baseline_by_name.keys()):
        before = baseline_by_name[name]
        after = current_by_name[name]
        if before.fingerprint != after.fingerprint:
            findings.append(
                Finding(
                    rule_id="TG103",
                    severity="error",
                    tool=name,
                    message=f"Tool {name!r} changed its advertised contract",
                    details={"changed_fields": _changed_fields(before, after)},
                )
            )
    return findings


def _policy_findings(snapshot: ToolCatalogSnapshot, policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    allowed = set(policy.allowed_tools) if policy.allowed_tools is not None else None
    try:
        denied_patterns = [re.compile(pattern) for pattern in policy.denied_name_patterns]
    except re.error as error:
        raise ValueError(f"Invalid denied_name_patterns regular expression: {error}") from error

    for tool in snapshot.tools:
        if allowed is not None and tool.name not in allowed:
            findings.append(
                Finding(
                    rule_id="TG001",
                    severity="error",
                    tool=tool.name,
                    message=f"Tool {tool.name!r} is not in the policy allowlist",
                )
            )
        for pattern in denied_patterns:
            if pattern.search(tool.name):
                findings.append(
                    Finding(
                        rule_id="TG002",
                        severity="error",
                        tool=tool.name,
                        message=f"Tool name matches denied pattern {pattern.pattern!r}",
                        details={"pattern": pattern.pattern},
                    )
                )
        if policy.require_descriptions and not (tool.description or "").strip():
            findings.append(
                Finding(
                    rule_id="TG003",
                    severity="warning",
                    tool=tool.name,
                    message="Tool has no human-readable description",
                )
            )
        if policy.require_closed_input_schemas and _is_open_object_schema(tool):
            findings.append(
                Finding(
                    rule_id="TG004",
                    severity="warning",
                    tool=tool.name,
                    message="Tool input object does not set additionalProperties to false",
                )
            )
    return findings


def analyze_snapshot(
    current: ToolCatalogSnapshot,
    *,
    policy: Policy,
    baseline: ToolCatalogSnapshot | None = None,
) -> AnalysisReport:
    findings = _policy_findings(current, policy)
    if baseline is not None:
        findings.extend(_baseline_findings(current, baseline))
    findings.sort(key=lambda item: (item.rule_id, item.tool or "", item.message))

    errors = sum(finding.severity == "error" for finding in findings)
    warnings = sum(finding.severity == "warning" for finding in findings)
    passed = (
        True
        if policy.fail_on == "never"
        else errors == 0 and (policy.fail_on != "warning" or warnings == 0)
    )
    return AnalysisReport(
        generated_at=_now(),
        baseline_captured_at=baseline.captured_at if baseline else None,
        current_captured_at=current.captured_at,
        passed=passed,
        fail_on=policy.fail_on,
        summary=ReportSummary(errors=errors, warnings=warnings, total=len(findings)),
        findings=findings,
    )
