"""Capture and persist stable MCP tool capability snapshots."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp import Client

from mcp_traceguard.models import ServerIdentity, ToolCatalogSnapshot, ToolContract


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _json_value(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True, exclude_none=True)
    if isinstance(value, Mapping):
        return dict(value)
    return value


def _field(tool: Any, name: str, default: Any = None) -> Any:
    if isinstance(tool, Mapping):
        return tool.get(name, default)
    return getattr(tool, name, default)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def build_tool_contract(tool: Any) -> ToolContract:
    """Normalize one SDK tool and fingerprint only its security-relevant contract."""

    contract = {
        "name": _field(tool, "name"),
        "title": _field(tool, "title"),
        "description": _field(tool, "description"),
        "input_schema": _json_value(_field(tool, "input_schema", {})),
        "output_schema": _json_value(_field(tool, "output_schema")),
        "annotations": _json_value(_field(tool, "annotations")),
    }
    digest = hashlib.sha256(canonical_json(contract).encode()).hexdigest()
    return ToolContract(**contract, fingerprint=digest)


async def capture_from_client(client: Client) -> ToolCatalogSnapshot:
    """Collect every paginated tool definition from an entered client."""

    tools: list[Any] = []
    cursor: str | None = None
    while True:
        page = await client.list_tools(cursor=cursor) if cursor else await client.list_tools()
        tools.extend(page.tools)
        cursor = page.next_cursor
        if cursor is None:
            break

    server_info = client.server_info
    identity = ServerIdentity(
        name=getattr(server_info, "name", None),
        version=getattr(server_info, "version", None),
        protocol_version=str(client.protocol_version),
    )
    contracts = sorted((build_tool_contract(tool) for tool in tools), key=lambda tool: tool.name)
    return ToolCatalogSnapshot(captured_at=utc_now(), server=identity, tools=contracts)


async def capture_snapshot(target: Any) -> ToolCatalogSnapshot:
    """Connect to an MCP target and collect every paginated tool definition."""

    async with Client(target) as client:
        return await capture_from_client(client)


def write_json(path: Path, value: Any, *, force: bool = False) -> None:
    """Atomically write a Pydantic model without overwriting by accident."""

    path = path.expanduser().resolve()
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {path}; pass --force to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as temporary:
        temporary.write(text)
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def load_snapshot(path: Path) -> ToolCatalogSnapshot:
    return ToolCatalogSnapshot.model_validate_json(path.read_text(encoding="utf-8"))
