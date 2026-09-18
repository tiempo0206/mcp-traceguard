from mcp_traceguard.schema_diff import diff_tool_contract
from mcp_traceguard.snapshot import build_tool_contract


def tool(input_schema: dict[str, object], description: str = "Read one note"):
    return build_tool_contract(
        {
            "name": "read_note",
            "description": description,
            "input_schema": input_schema,
        }
    )


def test_schema_diff_explains_required_and_property_changes() -> None:
    before = tool(
        {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
            "additionalProperties": False,
        }
    )
    after = tool(
        {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "scope": {"type": "string"},
            },
            "required": [],
            "additionalProperties": True,
        }
    )

    changes = diff_tool_contract(before, after)
    by_path = {change.path: change for change in changes}
    assert by_path["/input_schema/properties/scope"].impact == "broadening"
    assert by_path["/input_schema/required"].impact == "broadening"
    assert by_path["/input_schema/additionalProperties"].impact == "broadening"


def test_schema_diff_classifies_enum_and_type_directions() -> None:
    before = tool(
        {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["safe"]},
                "value": {"type": "string"},
            },
        }
    )
    after = tool(
        {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["safe", "admin"]},
                "value": {"type": ["string", "number"]},
            },
        }
    )
    changes = diff_tool_contract(before, after)
    assert {(change.path, change.impact) for change in changes} == {
        ("/input_schema/properties/mode/enum", "broadening"),
        ("/input_schema/properties/value/type", "broadening"),
    }


def test_description_change_is_metadata() -> None:
    before = tool({}, "Read one note")
    after = tool({}, "Read every note")
    changes = diff_tool_contract(before, after)
    assert len(changes) == 1
    assert changes[0].path == "/description"
    assert changes[0].impact == "metadata"
