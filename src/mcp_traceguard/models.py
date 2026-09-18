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


class Policy(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    allowed_tools: list[str] | None = None
    denied_name_patterns: list[str] = Field(default_factory=list)
    require_descriptions: bool = True
    require_closed_input_schemas: bool = False
    fail_on: Literal["warning", "error", "never"] = "error"


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


class AnalysisReport(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at: str
    baseline_captured_at: str | None = None
    current_captured_at: str
    passed: bool
    fail_on: Literal["warning", "error", "never"]
    summary: ReportSummary
    findings: list[Finding]
