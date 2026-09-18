import json
from pathlib import Path

from mcp_traceguard.artifact_schemas import artifact_schemas


def test_committed_artifact_schemas_are_current() -> None:
    root = Path(__file__).parents[1]
    generated = artifact_schemas()
    committed = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((root / "schemas" / "v1").glob("*.schema.json"))
    }
    assert committed == generated
