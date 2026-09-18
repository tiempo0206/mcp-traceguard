"""Command-line interface for snapshotting and checking MCP servers."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import StdioServerParameters

from mcp_traceguard.analysis import analyze_snapshot
from mcp_traceguard.artifact_schemas import export_artifact_schemas
from mcp_traceguard.models import ExecutionTrace, Policy
from mcp_traceguard.runtime import execute_guarded_call, verify_trace
from mcp_traceguard.snapshot import capture_snapshot, load_snapshot, write_json


def _target(args: argparse.Namespace) -> Any:
    if args.url:
        return args.url
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise ValueError("Provide --url URL or a command after --")
    return StdioServerParameters(command=command[0], args=command[1:], cwd=args.cwd)


def _add_target_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--url", help="Streamable HTTP MCP endpoint")
    parser.add_argument("--cwd", help="Working directory for a stdio server")
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="stdio server command, placed after -- (for example: -- python server.py)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mcp-traceguard",
        description="Deterministic capability-contract testing for MCP servers",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    snapshot = subparsers.add_parser("snapshot", help="Capture an approved tool baseline")
    snapshot.add_argument("-o", "--output", type=Path, required=True)
    snapshot.add_argument("--force", action="store_true")
    _add_target_arguments(snapshot)

    check = subparsers.add_parser("check", help="Check a live server against policy and baseline")
    check.add_argument("--baseline", type=Path)
    check.add_argument("--policy", type=Path, required=True)
    check.add_argument("--report", type=Path)
    check.add_argument("--current-output", type=Path)
    check.add_argument("--force", action="store_true")
    _add_target_arguments(check)

    schemas = subparsers.add_parser("export-schemas", help="Write versioned artifact schemas")
    schemas.add_argument("--output-dir", type=Path, default=Path("schemas/v1"))
    schemas.add_argument("--force", action="store_true")

    call = subparsers.add_parser("call", help="Policy-check and call one MCP tool")
    call.add_argument("--tool", required=True)
    call.add_argument(
        "--arguments",
        default="{}",
        help="JSON object or @path/to/arguments.json",
    )
    call.add_argument("--policy", type=Path, required=True)
    call.add_argument("--trace", type=Path, required=True)
    call.add_argument("--approved", action="store_true")
    call.add_argument("--force", action="store_true")
    _add_target_arguments(call)

    verify = subparsers.add_parser("verify-trace", help="Verify a trace hash chain")
    verify.add_argument("trace", type=Path)
    return parser


def _read_policy(path: Path) -> Policy:
    return Policy.model_validate_json(path.read_text(encoding="utf-8"))


def _snapshot_command(args: argparse.Namespace) -> int:
    snapshot = asyncio.run(capture_snapshot(_target(args)))
    write_json(args.output, snapshot, force=args.force)
    print(f"Captured {len(snapshot.tools)} tools to {args.output}")
    return 0


def _check_command(args: argparse.Namespace) -> int:
    current = asyncio.run(capture_snapshot(_target(args)))
    baseline = load_snapshot(args.baseline) if args.baseline else None
    report = analyze_snapshot(current, policy=_read_policy(args.policy), baseline=baseline)
    if args.current_output:
        write_json(args.current_output, current, force=args.force)
    if args.report:
        write_json(args.report, report, force=args.force)
    else:
        print(json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False))
    status = "PASS" if report.passed else "FAIL"
    print(
        f"{status}: {report.summary.errors} errors, "
        f"{report.summary.warnings} warnings, {report.summary.total} findings",
        file=sys.stderr,
    )
    return 0 if report.passed else 1


def _read_arguments(value: str) -> dict[str, Any]:
    if value.startswith("@"):
        payload = json.loads(Path(value[1:]).read_text(encoding="utf-8"))
    else:
        payload = json.loads(value)
    if not isinstance(payload, dict):
        raise ValueError("Tool arguments must be a JSON object")
    return payload


def _call_command(args: argparse.Namespace) -> int:
    trace = asyncio.run(
        execute_guarded_call(
            _target(args),
            tool=args.tool,
            arguments=_read_arguments(args.arguments),
            policy=_read_policy(args.policy),
            approved=args.approved,
        )
    )
    write_json(args.trace, trace, force=args.force)
    print(
        f"{trace.summary.outcome.upper()}: {trace.summary.event_count} events, "
        f"{trace.summary.redaction_count} redactions, {trace.summary.duration_ms:.3f} ms",
        file=sys.stderr,
    )
    return 0 if trace.summary.outcome == "allow" and trace.summary.call_executed else 1


def _verify_trace_command(args: argparse.Namespace) -> int:
    trace = ExecutionTrace.model_validate_json(args.trace.read_text(encoding="utf-8"))
    errors = verify_trace(trace)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: verified {len(trace.events)} chained events")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.subcommand == "snapshot":
            code = _snapshot_command(args)
        elif args.subcommand == "check":
            code = _check_command(args)
        elif args.subcommand == "export-schemas":
            written = export_artifact_schemas(args.output_dir, force=args.force)
            print(f"Wrote {len(written)} schemas to {args.output_dir}")
            code = 0
        elif args.subcommand == "call":
            code = _call_command(args)
        else:
            code = _verify_trace_command(args)
    except (FileExistsError, OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
