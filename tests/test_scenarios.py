import asyncio

from mcp.server import MCPServer

from mcp_traceguard.models import (
    Policy,
    RuntimeRule,
    ScenarioCase,
    ScenarioExpectation,
    ScenarioSuite,
)
from mcp_traceguard.scenarios import replay_suite


def test_replay_scores_each_observable_contract() -> None:
    calls: list[str] = []
    server = MCPServer("scenario-test")

    @server.tool()
    def echo(text: str) -> str:
        """Echo one string."""

        calls.append(text)
        return text

    policy = Policy(
        runtime_rules=[
            RuntimeRule(
                id="echo-allowed",
                tool_pattern="echo",
                action="allow",
                reason="Test fixture",
            )
        ]
    )
    suite = ScenarioSuite(
        name="test",
        description="test suite",
        cases=[
            ScenarioCase(
                id="echo-works",
                title="Echo works",
                category="correctness",
                tool="echo",
                arguments={"text": "hello"},
                expect=ScenarioExpectation(
                    outcome="allow",
                    call_executed=True,
                    matched_rules=["echo-allowed"],
                ),
            )
        ],
    )
    report, traces = asyncio.run(replay_suite(server, suite=suite, policy=policy))
    assert report.passed
    assert report.summary.score_percent == 100
    assert report.summary.category_scores == {"correctness": 100.0}
    assert traces["echo-works"].summary.outcome == "allow"
    assert calls == ["hello"]


def test_replay_reports_mismatched_expectation() -> None:
    server = MCPServer("scenario-failure-test")

    @server.tool()
    def echo(text: str) -> str:
        """Echo one string."""

        return text

    suite = ScenarioSuite(
        name="test",
        description="test suite",
        cases=[
            ScenarioCase(
                id="wrong-expectation",
                title="Wrong expectation",
                category="correctness",
                tool="echo",
                arguments={"text": "hello"},
                expect=ScenarioExpectation(outcome="allow", call_executed=True),
            )
        ],
    )
    report, _ = asyncio.run(replay_suite(server, suite=suite, policy=Policy()))
    assert not report.passed
    assert report.summary.failed == 1
    failed_checks = [check.name for check in report.results[0].checks if not check.passed]
    assert failed_checks == ["outcome", "call_executed"]
