"""Explain security-relevant differences between MCP tool contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from mcp_traceguard.models import ContractChange, ToolContract
from mcp_traceguard.snapshot import canonical_json


def _pointer(parent: str, key: str) -> str:
    escaped = key.replace("~", "~0").replace("/", "~1")
    return f"{parent}/{escaped}" if parent else f"/{escaped}"


def _different(before: Any, after: Any) -> bool:
    return canonical_json(before) != canonical_json(after)


def _type_set(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return {item for item in value if isinstance(item, str)}
    return set()


def _change(
    *,
    path: str,
    kind: str,
    impact: str,
    before: Any,
    after: Any,
    explanation: str,
) -> ContractChange:
    return ContractChange(
        path=path,
        kind=kind,
        impact=impact,
        before=before,
        after=after,
        explanation=explanation,
    )


def _diff_type(before: Any, after: Any, path: str) -> list[ContractChange]:
    if not _different(before, after):
        return []
    before_types = _type_set(before)
    after_types = _type_set(after)
    if before_types and after_types and before_types < after_types:
        impact = "broadening"
        explanation = "Accepted JSON types were expanded"
    elif before_types and after_types and after_types < before_types:
        impact = "narrowing"
        explanation = "Accepted JSON types were reduced"
    else:
        impact = "behavioral"
        explanation = "Accepted JSON type changed"
    return [
        _change(
            path=path,
            kind="changed",
            impact=impact,
            before=before,
            after=after,
            explanation=explanation,
        )
    ]


def _diff_set_keyword(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    parent: str,
    keyword: str,
) -> list[ContractChange]:
    before_values = set(before.get(keyword, []))
    after_values = set(after.get(keyword, []))
    if before_values == after_values:
        return []
    changes: list[ContractChange] = []
    path = _pointer(parent, keyword)
    if keyword == "required":
        for value in sorted(after_values - before_values):
            changes.append(
                _change(
                    path=path,
                    kind="added",
                    impact="narrowing",
                    before=None,
                    after=value,
                    explanation=f"Property {value!r} became required",
                )
            )
        for value in sorted(before_values - after_values):
            changes.append(
                _change(
                    path=path,
                    kind="removed",
                    impact="broadening",
                    before=value,
                    after=None,
                    explanation=f"Property {value!r} is no longer required",
                )
            )
    else:
        for value in sorted(after_values - before_values, key=str):
            changes.append(
                _change(
                    path=path,
                    kind="added",
                    impact="broadening",
                    before=None,
                    after=value,
                    explanation=f"Allowed value {value!r} was added",
                )
            )
        for value in sorted(before_values - after_values, key=str):
            changes.append(
                _change(
                    path=path,
                    kind="removed",
                    impact="narrowing",
                    before=value,
                    after=None,
                    explanation=f"Allowed value {value!r} was removed",
                )
            )
    return changes


def _constraint_impact(keyword: str, before: Any, after: Any) -> str:
    if not isinstance(before, (int, float)) or not isinstance(after, (int, float)):
        return "behavioral"
    lower_bounds = {"minimum", "exclusiveMinimum", "minLength", "minItems", "minProperties"}
    upper_bounds = {"maximum", "exclusiveMaximum", "maxLength", "maxItems", "maxProperties"}
    if keyword in lower_bounds:
        return "broadening" if after < before else "narrowing"
    if keyword in upper_bounds:
        return "broadening" if after > before else "narrowing"
    return "behavioral"


def _diff_schema(before: Any, after: Any, parent: str) -> list[ContractChange]:
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        if _different(before, after):
            return [
                _change(
                    path=parent or "/",
                    kind="changed",
                    impact="behavioral",
                    before=before,
                    after=after,
                    explanation="Schema value changed",
                )
            ]
        return []

    changes: list[ContractChange] = []
    if "type" in before or "type" in after:
        changes.extend(_diff_type(before.get("type"), after.get("type"), _pointer(parent, "type")))
    if "required" in before or "required" in after:
        changes.extend(_diff_set_keyword(before, after, parent=parent, keyword="required"))
    if "enum" in before or "enum" in after:
        changes.extend(_diff_set_keyword(before, after, parent=parent, keyword="enum"))

    before_properties = before.get("properties", {})
    after_properties = after.get("properties", {})
    if isinstance(before_properties, Mapping) and isinstance(after_properties, Mapping):
        properties_path = _pointer(parent, "properties")
        for name in sorted(after_properties.keys() - before_properties.keys()):
            changes.append(
                _change(
                    path=_pointer(properties_path, str(name)),
                    kind="added",
                    impact="broadening",
                    before=None,
                    after=after_properties[name],
                    explanation=f"Input property {name!r} was added",
                )
            )
        for name in sorted(before_properties.keys() - after_properties.keys()):
            changes.append(
                _change(
                    path=_pointer(properties_path, str(name)),
                    kind="removed",
                    impact="narrowing",
                    before=before_properties[name],
                    after=None,
                    explanation=f"Input property {name!r} was removed",
                )
            )
        for name in sorted(before_properties.keys() & after_properties.keys()):
            changes.extend(
                _diff_schema(
                    before_properties[name],
                    after_properties[name],
                    _pointer(properties_path, str(name)),
                )
            )

    if "items" in before or "items" in after:
        changes.extend(
            _diff_schema(before.get("items"), after.get("items"), _pointer(parent, "items"))
        )

    if "additionalProperties" in before or "additionalProperties" in after:
        old_additional = before.get("additionalProperties", True)
        new_additional = after.get("additionalProperties", True)
        if _different(old_additional, new_additional):
            if old_additional is False and new_additional is not False:
                impact = "broadening"
                explanation = "Additional object properties became allowed"
            elif old_additional is not False and new_additional is False:
                impact = "narrowing"
                explanation = "Additional object properties became forbidden"
            else:
                impact = "behavioral"
                explanation = "Additional-property validation changed"
            changes.append(
                _change(
                    path=_pointer(parent, "additionalProperties"),
                    kind="changed",
                    impact=impact,
                    before=old_additional,
                    after=new_additional,
                    explanation=explanation,
                )
            )

    constraint_keys = {
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
        "minProperties",
        "maxProperties",
    }
    for keyword in sorted(constraint_keys & (before.keys() | after.keys())):
        old_value = before.get(keyword)
        new_value = after.get(keyword)
        if _different(old_value, new_value):
            changes.append(
                _change(
                    path=_pointer(parent, keyword),
                    kind=(
                        "added"
                        if keyword not in before
                        else "removed"
                        if keyword not in after
                        else "changed"
                    ),
                    impact=_constraint_impact(keyword, old_value, new_value),
                    before=old_value,
                    after=new_value,
                    explanation=f"Validation constraint {keyword!r} changed",
                )
            )

    handled = {
        "type",
        "required",
        "enum",
        "properties",
        "items",
        "additionalProperties",
        *constraint_keys,
    }
    for keyword in sorted((before.keys() | after.keys()) - handled):
        old_value = before.get(keyword)
        new_value = after.get(keyword)
        if _different(old_value, new_value):
            changes.append(
                _change(
                    path=_pointer(parent, str(keyword)),
                    kind=(
                        "added"
                        if keyword not in before
                        else "removed"
                        if keyword not in after
                        else "changed"
                    ),
                    impact="metadata"
                    if keyword in {"title", "description", "$comment"}
                    else "behavioral",
                    before=old_value,
                    after=new_value,
                    explanation=f"Schema keyword {keyword!r} changed",
                )
            )
    return changes


def diff_tool_contract(before: ToolContract, after: ToolContract) -> list[ContractChange]:
    """Return deterministic, JSON-Pointer-addressed changes for one tool."""

    changes: list[ContractChange] = []
    for field in ("title", "description", "annotations"):
        old_value = getattr(before, field)
        new_value = getattr(after, field)
        if _different(old_value, new_value):
            changes.append(
                _change(
                    path=f"/{field}",
                    kind="changed",
                    impact="metadata",
                    before=old_value,
                    after=new_value,
                    explanation=f"Tool {field} changed",
                )
            )
    changes.extend(_diff_schema(before.input_schema, after.input_schema, "/input_schema"))
    changes.extend(_diff_schema(before.output_schema, after.output_schema, "/output_schema"))
    return sorted(changes, key=lambda item: (item.path, item.kind, item.explanation))
