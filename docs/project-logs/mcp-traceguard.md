# MCP TraceGuard project log

## 2026-09-18 — Day 1: capability-contract foundation

### Goal

Create the first end-to-end slice of a second, independent portfolio project:
connect to a real MCP server, discover its tools, save an auditable baseline,
and fail a check when the server exceeds policy or changes its advertised
contract.

### Work completed

- Chose MCP capability-boundary testing as a topic distinct from EvalMerge.
- Defined versioned snapshot, policy, finding, and report data models.
- Added official MCP Python SDK support for in-memory, stdio, and Streamable
  HTTP targets.
- Implemented complete paginated tool discovery.
- Canonicalized tool metadata and generated stable SHA-256 fingerprints.
- Added atomic JSON writes and explicit overwrite protection.
- Implemented allowlist, denied-name, description, closed-schema, added-tool,
  removed-tool, and changed-contract checks.
- Added a demo MCP server, example policy, automated tests, and GitHub Actions.

### Concepts learned

- An MCP tool contract is more than a function name: its description, input and
  output JSON Schemas, and annotations all influence what an agent believes it
  can do.
- Canonical JSON makes semantically identical dictionaries hash identically even
  when key insertion order differs.
- A baseline catches "rug pull" behavior: a previously reviewed server can add
  a tool or silently widen an existing contract later.
- Policy checks and drift checks answer different questions. Policy describes
  what is allowed in general; a baseline records what was actually approved.

### Verification

- Ruff formatting check: passed.
- Ruff lint: passed.
- Pytest: 8 tests passed, including a real in-memory MCP protocol connection.
- Positive stdio smoke test: captured two tools and returned `PASS` with zero
  findings.
- Negative stdio smoke test: returned the expected exit status `1` with four
  findings: an allowlist violation, a denied name, a newly added tool, and a
  changed description.
- GitHub commit and CI links will be recorded after the initial push.

### Next task

Add field-level JSON Schema diffs so a finding explains whether a change widened
accepted inputs, altered a description, or changed output guarantees.
