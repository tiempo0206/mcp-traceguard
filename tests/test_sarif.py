from mcp_traceguard.analysis import analyze_snapshot
from mcp_traceguard.models import Policy, ServerIdentity, ToolCatalogSnapshot
from mcp_traceguard.sarif import analysis_to_sarif
from mcp_traceguard.snapshot import build_tool_contract


def test_sarif_contains_rules_results_and_stable_fingerprints() -> None:
    baseline = ToolCatalogSnapshot(
        captured_at="2026-09-18T00:00:00Z",
        server=ServerIdentity(name="test", version="1", protocol_version="2026-07-28"),
        tools=[],
    )
    current = baseline.model_copy(
        update={
            "tools": [
                build_tool_contract(
                    {"name": "shell_exec", "description": "Run", "input_schema": {}}
                )
            ]
        }
    )
    report = analyze_snapshot(
        current,
        baseline=baseline,
        policy=Policy(
            allowed_tools=[],
            denied_name_patterns=["shell"],
        ),
    )
    first = analysis_to_sarif(report, artifact_uri="examples/drifted_server.py")
    second = analysis_to_sarif(report, artifact_uri="examples/drifted_server.py")
    run = first["runs"][0]
    assert first["version"] == "2.1.0"
    assert {rule["id"] for rule in run["tool"]["driver"]["rules"]} == {
        "TG001",
        "TG002",
        "TG101",
    }
    assert len(run["results"]) == 3
    assert (
        run["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
        == "examples/drifted_server.py"
    )
    assert (
        run["results"][0]["partialFingerprints"]
        == second["runs"][0]["results"][0]["partialFingerprints"]
    )
