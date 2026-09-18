"""Generate committed JSON Schemas for TraceGuard interchange artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from mcp_traceguard.models import AnalysisReport, ExecutionTrace, Policy, ToolCatalogSnapshot
from mcp_traceguard.snapshot import write_json

SCHEMA_BASE = "https://raw.githubusercontent.com/tiempo0206/mcp-traceguard/main/schemas/v1"
SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "policy.schema.json": Policy,
    "report.schema.json": AnalysisReport,
    "snapshot.schema.json": ToolCatalogSnapshot,
    "trace.schema.json": ExecutionTrace,
}


def artifact_schemas() -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for filename, model in SCHEMA_MODELS.items():
        document = model.model_json_schema()
        document["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        document["$id"] = f"{SCHEMA_BASE}/{filename}"
        documents[filename] = document
    return documents


def export_artifact_schemas(output_dir: Path, *, force: bool = False) -> list[Path]:
    written: list[Path] = []
    for filename, document in artifact_schemas().items():
        path = output_dir / filename
        write_json(path, document, force=force)
        written.append(path)
    return written
