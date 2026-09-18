# MCP TraceGuard

[![test](https://github.com/tiempo0206/mcp-traceguard/actions/workflows/test.yml/badge.svg)](https://github.com/tiempo0206/mcp-traceguard/actions/workflows/test.yml)

MCP TraceGuard is a deterministic capability-contract test harness for
[Model Context Protocol](https://modelcontextprotocol.io/) servers. It records
what a server exposes, fingerprints each tool's description and JSON Schemas,
and fails CI when a server adds an unapproved capability or changes an approved
contract.

The project targets a practical trust gap: an MCP server may keep the same
installation entry while changing the tools and instructions presented to an
agent. TraceGuard makes those changes reviewable and testable without an LLM or
an API key.

## First working slice

- real MCP discovery over in-memory, stdio, or Streamable HTTP transports;
- pagination-safe tool catalog capture;
- stable SHA-256 fingerprints over normalized tool contracts;
- versioned JSON snapshots, policies, findings, and reports;
- policy checks for tool allowlists, denied names, missing descriptions, and
  open input objects;
- baseline checks for added, removed, and changed tools;
- atomic output writes with overwrite protection; and
- a CI-friendly exit code plus machine-readable JSON report.

## Quick start

Create an isolated environment and install the project:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Capture the demo server's approved baseline:

```bash
mcp-traceguard snapshot \
  --output artifacts/demo-baseline.json \
  -- python examples/demo_server.py
```

Check the live server against both that baseline and an explicit policy:

```bash
mcp-traceguard check \
  --baseline artifacts/demo-baseline.json \
  --policy examples/traceguard.policy.json \
  --report artifacts/demo-report.json \
  -- python examples/demo_server.py
```

A clean server exits with status `0`. A policy violation or unapproved contract
change exits with status `1`, making the same command suitable for GitHub
Actions. Existing output is never replaced unless `--force` is provided.

The repository also includes a safe, deliberately drifted fixture. It changes a
reviewed description and advertises a new `shell_exec` tool without actually
executing shell commands:

```bash
mcp-traceguard check \
  --baseline artifacts/demo-baseline.json \
  --policy examples/traceguard.policy.json \
  --report artifacts/drift-report.json \
  -- python examples/drifted_server.py
```

This command exits with status `1` and reports the allowlist violation, denied
name, added tool, and changed contract.

Use `--url https://example.com/mcp` instead of the command after `--` to inspect
a Streamable HTTP server.

## Why this is separate from EvalMerge

EvalMerge focuses on offline human review of LLM evaluation results. MCP
TraceGuard focuses on protocol-facing capability security and CI regression
testing. The shared engineering skills are useful, but the core data model,
threat model, product workflow, and technical claims are independent.

See the [two-week roadmap](docs/roadmap.md) and the
[daily project log](docs/project-logs/mcp-traceguard.md).

## Status

MCP TraceGuard is under active development. Version 0.1 establishes the
capability baseline; runtime trace recording, adversarial scenario replay,
SARIF export, a local evidence viewer, and published benchmarks are the next
milestones.

## License

MIT
