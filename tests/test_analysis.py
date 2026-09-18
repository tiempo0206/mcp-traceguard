from mcp_traceguard.analysis import analyze_snapshot
from mcp_traceguard.models import Policy, ServerIdentity, ToolCatalogSnapshot
from mcp_traceguard.snapshot import build_tool_contract


def snapshot(*tools: dict[str, object]) -> ToolCatalogSnapshot:
    return ToolCatalogSnapshot(
        captured_at="2026-09-18T00:00:00Z",
        server=ServerIdentity(name="test", version="1", protocol_version="2026-07-28"),
        tools=[build_tool_contract(tool) for tool in tools],
    )


def test_clean_snapshot_passes() -> None:
    current = snapshot(
        {
            "name": "read_note",
            "description": "Read one note",
            "input_schema": {"type": "object", "additionalProperties": False},
        }
    )
    report = analyze_snapshot(
        current,
        policy=Policy(allowed_tools=["read_note"], require_closed_input_schemas=True),
    )
    assert report.passed
    assert report.summary.total == 0
    assert report.risk.score == 0
    assert report.risk.rating == "none"


def test_added_and_changed_tools_fail_baseline() -> None:
    baseline = snapshot({"name": "read_note", "description": "Read one note", "input_schema": {}})
    current = snapshot(
        {"name": "read_note", "description": "Read every note", "input_schema": {}},
        {"name": "delete_note", "description": "Delete one note", "input_schema": {}},
    )
    report = analyze_snapshot(
        current,
        baseline=baseline,
        policy=Policy(allowed_tools=None, require_descriptions=True),
    )
    assert not report.passed
    assert {finding.rule_id for finding in report.findings} == {"TG101", "TG103"}
    changed = next(finding for finding in report.findings if finding.rule_id == "TG103")
    assert changed.details["changes"][0]["path"] == "/description"
    assert changed.details["impact_counts"]["metadata"] == 1
    assert report.risk.score == 28
    assert report.risk.rating == "moderate"


def test_allowlist_and_denied_pattern_are_independent_findings() -> None:
    current = snapshot({"name": "shell_exec", "description": "Execute a shell", "input_schema": {}})
    report = analyze_snapshot(
        current,
        policy=Policy(
            allowed_tools=["read_note"],
            denied_name_patterns=["shell|exec"],
        ),
    )
    assert not report.passed
    assert [finding.rule_id for finding in report.findings] == ["TG001", "TG002"]


def test_warning_threshold_is_configurable() -> None:
    current = snapshot({"name": "read_note", "description": None, "input_schema": {}})
    passing = analyze_snapshot(current, policy=Policy(fail_on="error"))
    failing = analyze_snapshot(current, policy=Policy(fail_on="warning"))
    assert passing.passed
    assert not failing.passed
