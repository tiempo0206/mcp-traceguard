from mcp_traceguard.snapshot import build_tool_contract, canonical_json


def test_canonical_json_is_order_independent() -> None:
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})


def test_tool_fingerprint_is_stable_across_schema_key_order() -> None:
    left = build_tool_contract(
        {
            "name": "read_note",
            "description": "Read a note",
            "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}},
        }
    )
    right = build_tool_contract(
        {
            "input_schema": {"properties": {"id": {"type": "string"}}, "type": "object"},
            "description": "Read a note",
            "name": "read_note",
        }
    )
    assert left.fingerprint == right.fingerprint


def test_tool_fingerprint_changes_with_description() -> None:
    original = build_tool_contract(
        {"name": "read_note", "description": "Read one note", "input_schema": {}}
    )
    changed = build_tool_contract(
        {"name": "read_note", "description": "Read all notes", "input_schema": {}}
    )
    assert original.fingerprint != changed.fingerprint
