"""Guard MCP tool calls and emit redacted, tamper-evident execution traces."""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from mcp_traceguard.connection import client_for_target
from mcp_traceguard.models import (
    ExecutionTrace,
    Policy,
    RedactionPolicy,
    RuntimeCondition,
    RuntimeDecision,
    RuntimeRule,
    TraceEvent,
    TraceSummary,
)
from mcp_traceguard.snapshot import canonical_json, capture_from_client, utc_now

ZERO_HASH = "0" * 64
_MISSING = object()
_ACTION_RANK = {"allow": 0, "require_approval": 1, "deny": 2}


@dataclass(frozen=True)
class RedactionResult:
    value: Any
    paths: tuple[str, ...]


def _pointer(parent: str, key: str) -> str:
    escaped = key.replace("~", "~0").replace("/", "~1")
    return f"{parent}/{escaped}" if parent else f"/{escaped}"


def redact(value: Any, policy: RedactionPolicy) -> RedactionResult:
    """Redact sensitive keys and bound strings while preserving JSON shape."""

    try:
        key_patterns = [re.compile(pattern) for pattern in policy.sensitive_key_patterns]
    except re.error as error:
        raise ValueError(f"Invalid sensitive_key_patterns regular expression: {error}") from error
    paths: list[str] = []

    def visit(item: Any, path: str, key: str | None = None) -> Any:
        if key is not None and any(pattern.search(key) for pattern in key_patterns):
            paths.append(path or "/")
            return policy.replacement
        if hasattr(item, "model_dump"):
            item = item.model_dump(mode="json", by_alias=True, exclude_none=True)
        if isinstance(item, dict):
            return {
                str(child_key): visit(
                    child_value,
                    _pointer(path, str(child_key)),
                    str(child_key),
                )
                for child_key, child_value in item.items()
            }
        if isinstance(item, (list, tuple)):
            return [visit(child, _pointer(path, str(index))) for index, child in enumerate(item)]
        if isinstance(item, str):
            stripped = item.strip()
            if stripped.startswith(("{", "[")):
                try:
                    embedded = json.loads(item)
                except json.JSONDecodeError:
                    embedded = None
                if isinstance(embedded, (dict, list)):
                    sanitized = visit(embedded, path)
                    item = json.dumps(sanitized, sort_keys=True, ensure_ascii=False)
            if len(item) > policy.max_string_length:
                paths.append(path or "/")
                omitted = len(item) - policy.max_string_length
                return f"{item[: policy.max_string_length]}…[truncated {omitted} chars]"
            return item
        if isinstance(item, bytes):
            paths.append(path or "/")
            return f"[BINARY {len(item)} bytes]"
        return item

    return RedactionResult(visit(value, ""), tuple(sorted(set(paths))))


def _resolve_pointer(value: Any, pointer: str) -> Any:
    if pointer == "":
        return value
    current = value
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            return _MISSING
    return current


def _condition_matches(condition: RuntimeCondition, arguments: dict[str, Any]) -> bool:
    actual = _resolve_pointer(arguments, condition.path)
    operator = condition.operator
    expected = condition.value
    if operator == "exists":
        return (actual is not _MISSING) is bool(expected)
    if actual is _MISSING:
        return False
    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator in {"matches", "not_matches"}:
        try:
            matched = re.search(str(expected), str(actual)) is not None
        except re.error as error:
            raise ValueError(f"Invalid runtime condition regular expression: {error}") from error
        return matched if operator == "matches" else not matched
    if operator in {"in", "not_in"}:
        if not isinstance(expected, list):
            raise ValueError(f"Runtime operator {operator!r} requires a list value")
        contained = actual in expected
        return contained if operator == "in" else not contained
    parsed = urlparse(str(actual))
    if not isinstance(expected, list):
        raise ValueError(f"Runtime operator {operator!r} requires a list value")
    if operator == "url_scheme_not_in":
        return parsed.scheme.lower() not in {str(value).lower() for value in expected}
    if operator == "url_host_not_in":
        return (parsed.hostname or "").lower() not in {str(value).lower() for value in expected}
    raise ValueError(f"Unsupported runtime operator {operator!r}")


def _compile_tool_pattern(rule: RuntimeRule) -> re.Pattern[str]:
    try:
        return re.compile(rule.tool_pattern)
    except re.error as error:
        raise ValueError(f"Invalid tool pattern for runtime rule {rule.id!r}: {error}") from error


def evaluate_runtime(
    policy: Policy,
    tool: str,
    arguments: dict[str, Any],
    *,
    approved: bool = False,
) -> RuntimeDecision:
    """Evaluate matching runtime rules with deny-over-approval precedence."""

    selected_action: str | None = None
    matched_rules: list[str] = []
    reasons: list[str] = []

    def apply(action: str, reason: str) -> None:
        nonlocal selected_action
        if selected_action is None or _ACTION_RANK[action] > _ACTION_RANK[selected_action]:
            selected_action = action
        reasons.append(reason)

    for rule in policy.runtime_rules:
        if _compile_tool_pattern(rule).fullmatch(tool) is None:
            continue
        matched_rules.append(rule.id)
        apply(rule.action, rule.reason)
        for condition in rule.conditions:
            if _condition_matches(condition, arguments):
                apply(condition.action, condition.reason)

    if selected_action is None:
        selected_action = policy.default_runtime_action
        reasons.append(f"No runtime rule matched; default action is {selected_action}")

    if selected_action == "deny":
        outcome = "deny"
    elif selected_action == "require_approval" and not approved:
        outcome = "approval_required"
    else:
        outcome = "allow"
        if selected_action == "require_approval":
            reasons.append("Required approval was supplied")

    return RuntimeDecision(
        outcome=outcome,
        approved=approved,
        matched_rules=matched_rules,
        reasons=reasons,
    )


class TraceRecorder:
    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def add(self, event_type: str, *, tool: str | None, payload: dict[str, Any]) -> None:
        sequence = len(self.events)
        timestamp = utc_now()
        previous_hash = self.events[-1].event_hash if self.events else ZERO_HASH
        body = {
            "sequence": sequence,
            "timestamp": timestamp,
            "event_type": event_type,
            "tool": tool,
            "payload": payload,
        }
        event_hash = hashlib.sha256(f"{previous_hash}:{canonical_json(body)}".encode()).hexdigest()
        self.events.append(
            TraceEvent(
                **body,
                previous_hash=previous_hash,
                event_hash=event_hash,
            )
        )


def verify_trace(trace: ExecutionTrace) -> list[str]:
    """Return integrity errors; an empty list proves the full event chain."""

    errors: list[str] = []
    expected_previous = ZERO_HASH
    for index, event in enumerate(trace.events):
        if event.sequence != index:
            errors.append(f"event {index}: sequence is {event.sequence}")
        if event.previous_hash != expected_previous:
            errors.append(f"event {index}: previous hash does not match")
        body = {
            "sequence": event.sequence,
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "tool": event.tool,
            "payload": event.payload,
        }
        expected_hash = hashlib.sha256(
            f"{event.previous_hash}:{canonical_json(body)}".encode()
        ).hexdigest()
        if event.event_hash != expected_hash:
            errors.append(f"event {index}: event hash does not match content")
        expected_previous = event.event_hash
    if trace.summary.event_count != len(trace.events):
        errors.append("summary event_count does not match event list")
    expected_trace_hash = _trace_hash(
        trace_id=trace.trace_id,
        started_at=trace.started_at,
        completed_at=trace.completed_at,
        server=trace.server.model_dump(mode="json"),
        tool=trace.tool,
        events=trace.events,
        summary=trace.summary.model_dump(mode="json"),
    )
    if trace.trace_hash != expected_trace_hash:
        errors.append("trace hash does not match metadata, event root, and summary")
    return errors


def _trace_hash(
    *,
    trace_id: str,
    started_at: str,
    completed_at: str,
    server: dict[str, Any],
    tool: str,
    events: list[TraceEvent],
    summary: dict[str, Any],
) -> str:
    payload = {
        "schema_version": "1.0",
        "trace_id": trace_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "server": server,
        "tool": tool,
        "integrity": "sha256-chain-v1",
        "event_root": events[-1].event_hash if events else ZERO_HASH,
        "summary": summary,
    }
    return hashlib.sha256(canonical_json(payload).encode()).hexdigest()


async def execute_guarded_call(
    target: Any,
    *,
    tool: str,
    arguments: dict[str, Any],
    policy: Policy,
    approved: bool = False,
) -> ExecutionTrace:
    """Evaluate a call, execute only when allowed, and preserve redacted evidence."""

    started_at = utc_now()
    started = time.perf_counter()
    recorder = TraceRecorder()
    redaction_paths: set[str] = set()
    response_is_error: bool | None = None
    outcome = "error"
    call_executed = False

    async with client_for_target(target) as client:
        snapshot = await capture_from_client(client)
        contract = next((item for item in snapshot.tools if item.name == tool), None)
        if contract is None:
            recorder.add(
                "error",
                tool=tool,
                payload={"message": f"Server does not advertise tool {tool!r}"},
            )
        else:
            recorder.add(
                "catalog",
                tool=tool,
                payload={
                    "fingerprint": contract.fingerprint,
                    "contract": contract.model_dump(mode="json"),
                },
            )
            redacted_request = redact(arguments, policy.redaction)
            redaction_paths.update(f"request{path}" for path in redacted_request.paths)
            recorder.add(
                "request",
                tool=tool,
                payload={
                    "arguments": redacted_request.value,
                    "redacted_paths": list(redacted_request.paths),
                },
            )
            decision = evaluate_runtime(policy, tool, arguments, approved=approved)
            recorder.add(
                "decision",
                tool=tool,
                payload=decision.model_dump(mode="json"),
            )
            outcome = decision.outcome
            if decision.outcome == "allow":
                try:
                    call_executed = True
                    result = await client.call_tool(tool, arguments)
                    response_is_error = bool(result.is_error)
                    redacted_response = redact(result, policy.redaction)
                    redaction_paths.update(f"response{path}" for path in redacted_response.paths)
                    recorder.add(
                        "response",
                        tool=tool,
                        payload={
                            "result": redacted_response.value,
                            "redacted_paths": list(redacted_response.paths),
                        },
                    )
                    if response_is_error:
                        outcome = "error"
                except Exception as error:
                    outcome = "error"
                    recorder.add(
                        "error",
                        tool=tool,
                        payload={"error_type": type(error).__name__, "message": str(error)},
                    )

    duration_ms = (time.perf_counter() - started) * 1000
    completed_at = utc_now()
    trace_id = str(uuid.uuid4())
    summary = TraceSummary(
        outcome=outcome,
        call_executed=call_executed,
        response_is_error=response_is_error,
        redaction_count=len(redaction_paths),
        event_count=len(recorder.events),
        duration_ms=round(duration_ms, 3),
    )
    trace_hash = _trace_hash(
        trace_id=trace_id,
        started_at=started_at,
        completed_at=completed_at,
        server=snapshot.server.model_dump(mode="json"),
        tool=tool,
        events=recorder.events,
        summary=summary.model_dump(mode="json"),
    )
    return ExecutionTrace(
        trace_id=trace_id,
        started_at=started_at,
        completed_at=completed_at,
        server=snapshot.server,
        tool=tool,
        events=recorder.events,
        summary=summary,
        trace_hash=trace_hash,
    )
