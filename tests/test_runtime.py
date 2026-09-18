import asyncio

from mcp.server import MCPServer

from mcp_traceguard.models import Policy, RedactionPolicy, RuntimeCondition, RuntimeRule
from mcp_traceguard.runtime import (
    evaluate_runtime,
    execute_guarded_call,
    redact,
    verify_trace,
)
from mcp_traceguard.snapshot import canonical_json


def test_runtime_deny_takes_precedence_over_approval() -> None:
    policy = Policy(
        default_runtime_action="allow",
        runtime_rules=[
            RuntimeRule(
                id="publish",
                tool_pattern="publish_message",
                action="require_approval",
                reason="Publishing needs approval",
                conditions=[
                    RuntimeCondition(
                        path="/channel",
                        operator="equals",
                        value="all-company",
                        action="deny",
                        reason="The all-company channel is forbidden",
                    )
                ],
            )
        ],
    )
    decision = evaluate_runtime(
        policy,
        "publish_message",
        {"channel": "all-company"},
        approved=True,
    )
    assert decision.outcome == "deny"


def test_runtime_approval_is_explicit() -> None:
    policy = Policy(
        runtime_rules=[
            RuntimeRule(
                id="publish",
                tool_pattern="publish_message",
                action="require_approval",
                reason="Publishing needs approval",
            )
        ]
    )
    assert evaluate_runtime(policy, "publish_message", {}).outcome == "approval_required"
    assert evaluate_runtime(policy, "publish_message", {}, approved=True).outcome == "allow"


def test_redaction_is_recursive_and_bounds_strings() -> None:
    policy = RedactionPolicy(max_string_length=32)
    result = redact(
        {
            "profile": {"api_token": "not-a-real-secret"},
            "message": "x" * 40,
        },
        policy,
    )
    assert result.value["profile"]["api_token"] == "[REDACTED]"
    assert "truncated 8 chars" in result.value["message"]
    assert result.paths == ("/message", "/profile/api_token")


def test_guarded_call_redacts_result_and_verifies_hash_chain() -> None:
    server = MCPServer("runtime-test")

    @server.tool()
    def profile(user_id: str) -> dict[str, str]:
        """Return one profile."""

        return {"user_id": user_id, "api_token": "fake-token"}

    policy = Policy(
        runtime_rules=[
            RuntimeRule(
                id="profile-read",
                tool_pattern="profile",
                action="allow",
                reason="Read-only fixture",
            )
        ]
    )
    trace = asyncio.run(
        execute_guarded_call(
            server,
            tool="profile",
            arguments={"user_id": "u-1"},
            policy=policy,
        )
    )
    assert trace.summary.outcome == "allow"
    assert trace.summary.call_executed
    assert trace.summary.redaction_count >= 1
    assert "fake-token" not in canonical_json(trace.model_dump(mode="json"))
    assert "[REDACTED]" in canonical_json(trace.model_dump(mode="json"))
    assert verify_trace(trace) == []

    tampered = trace.model_copy(deep=True)
    tampered.events[1].payload["arguments"] = {"user_id": "altered"}
    assert "event 1: event hash does not match content" in verify_trace(tampered)

    summary_tampered = trace.model_copy(deep=True)
    summary_tampered.summary.duration_ms = 0
    assert "trace hash does not match metadata, event root, and summary" in verify_trace(
        summary_tampered
    )


def test_denied_call_never_reaches_server() -> None:
    calls: list[str] = []
    server = MCPServer("blocked-test")

    @server.tool()
    def dangerous(command: str) -> str:
        """Record a call for the test only."""

        calls.append(command)
        return command

    trace = asyncio.run(
        execute_guarded_call(
            server,
            tool="dangerous",
            arguments={"command": "do-not-run"},
            policy=Policy(default_runtime_action="deny"),
        )
    )
    assert trace.summary.outcome == "deny"
    assert not trace.summary.call_executed
    assert calls == []
