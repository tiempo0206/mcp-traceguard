"""Convert TraceGuard findings into GitHub-compatible SARIF 2.1.0."""

from __future__ import annotations

import hashlib
from typing import Any

from mcp_traceguard import __version__
from mcp_traceguard.models import AnalysisReport, Finding

RULE_HELP = {
    "TG001": ("Unapproved tool", "The tool is absent from the explicit policy allowlist."),
    "TG002": ("Denied tool name", "The tool name matches a denied capability pattern."),
    "TG003": ("Missing description", "The tool has no human-readable description."),
    "TG004": (
        "Open input schema",
        "The object schema permits properties that were not explicitly declared.",
    ),
    "TG101": ("Tool added", "The live server added a tool after baseline approval."),
    "TG102": ("Tool removed", "The live server removed a tool from the baseline."),
    "TG103": ("Tool contract changed", "The live tool contract differs from its baseline."),
}


def _rule(finding: Finding) -> dict[str, Any]:
    name, help_text = RULE_HELP.get(finding.rule_id, (finding.rule_id, finding.message))
    return {
        "id": finding.rule_id,
        "name": name.replace(" ", ""),
        "shortDescription": {"text": name},
        "fullDescription": {"text": help_text},
        "help": {"text": help_text},
        "defaultConfiguration": {"level": "error" if finding.severity == "error" else "warning"},
        "properties": {"tags": ["security", "mcp", "capability-contract"]},
    }


def analysis_to_sarif(
    report: AnalysisReport,
    *,
    artifact_uri: str,
    automation_id: str = "mcp-traceguard/catalog",
) -> dict[str, Any]:
    """Create the SARIF subset supported by GitHub code scanning."""

    unique_rules = {finding.rule_id: _rule(finding) for finding in report.findings}
    risk_points = {(item.rule_id, item.tool): item.points for item in report.risk.contributions}
    results = []
    for finding in report.findings:
        identity = f"{finding.rule_id}:{finding.tool or ''}:{artifact_uri}"
        fingerprint = hashlib.sha256(identity.encode()).hexdigest()
        results.append(
            {
                "ruleId": finding.rule_id,
                "level": "error" if finding.severity == "error" else "warning",
                "message": {"text": finding.message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": artifact_uri, "uriBaseId": "%SRCROOT%"}
                        },
                        "message": {
                            "text": f"MCP tool: {finding.tool}" if finding.tool else "MCP server"
                        },
                    }
                ],
                "partialFingerprints": {"traceguardFinding/v1": fingerprint},
                "properties": {
                    "tool": finding.tool,
                    "riskPoints": risk_points.get((finding.rule_id, finding.tool), 0),
                    "details": finding.details,
                },
            }
        )
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "automationDetails": {"id": automation_id},
                "tool": {
                    "driver": {
                        "name": "MCP TraceGuard",
                        "semanticVersion": __version__,
                        "informationUri": "https://github.com/tiempo0206/mcp-traceguard",
                        "rules": [unique_rules[key] for key in sorted(unique_rules)],
                    }
                },
                "originalUriBaseIds": {"%SRCROOT%": {"uri": "file:///github/workspace/"}},
                "invocations": [{"executionSuccessful": True}],
                "results": results,
                "properties": {
                    "traceguardRiskScore": report.risk.score,
                    "traceguardRiskRating": report.risk.rating,
                },
            }
        ],
    }
