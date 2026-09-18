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
from mcp_traceguard.models import Policy
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


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        code = _snapshot_command(args) if args.subcommand == "snapshot" else _check_command(args)
    except (FileExistsError, OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
