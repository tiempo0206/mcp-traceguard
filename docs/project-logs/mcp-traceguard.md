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
- Initial implementation commit: [`020a883`](https://github.com/tiempo0206/mcp-traceguard/commit/020a88380f70bd9133b15a8698fb2ec0d2c38a8a).
- First GitHub Actions run: [all checks passed](https://github.com/tiempo0206/mcp-traceguard/actions/runs/35325518074).

### Next task

Add field-level JSON Schema diffs so a finding explains whether a change widened
accepted inputs, altered a description, or changed output guarantees.

## 2026-09-18 — Day 1 continued: explainable contract drift

### Goal

Replace opaque "hash changed" alerts with evidence a reviewer can understand
and later render in SARIF and the browser viewer.

### Work completed

- Added deterministic JSON-Pointer-addressed contract changes.
- Classified changes as capability broadening, narrowing, behavioral, or
  metadata impact.
- Explained property, required-field, enum, JSON type, additional-property,
  numeric, length, item-count, title, description, and annotation changes.
- Embedded individual changes and impact counts in `TG103` findings.
- Added strict Draft 2020-12 JSON Schemas for snapshots, policies, and reports.
- Added an export command and a regression test that fails if committed schemas
  drift from runtime Pydantic models.

### Verification

- Ruff format and lint: passed.
- Pytest: 12 tests passed.
- Negative stdio fixture still fails with the expected four findings.
- The changed-description finding now identifies `/description`, preserves old
  and new values, and classifies the change as metadata impact.

### Next task

Build the runtime policy layer and a tamper-evident, secret-redacted call trace
so TraceGuard can test what a server does in addition to what it advertises.

## 2026-09-18 — Day 1 continued: guarded runtime traces

### Goal

Enforce a capability boundary before a real MCP tool call and retain useful
evidence without persisting secrets.

### Work completed

- Added deny-by-default runtime rules with regex tool matching.
- Added argument conditions for equality, regex, membership, URL schemes, and
  URL hosts.
- Implemented deny-over-approval precedence and an explicit `--approved` gate.
- Ensured denied and unapproved calls never reach the MCP server.
- Added recursive key-based redaction, embedded-JSON sanitization, binary
  placeholders, and bounded text storage.
- Added a `call` command that connects to a real MCP server, makes a policy
  decision, conditionally invokes the tool, and writes an execution trace.
- Chained every event to the previous event with SHA-256 and sealed metadata,
  the event root, and summary in a final trace hash.
- Added `verify-trace` and a versioned trace JSON Schema.
- Added safe runtime fixtures for allow, approval, conditional deny, secret
  redaction, and unconditional deny behavior.

### Verification

- Ruff format and lint: passed.
- Pytest: 17 tests passed.
- Allowed stdio call: four events, two redactions, trace verification passed,
  and the fake token was absent from the persisted file.
- Shell fixture: denied before execution.
- Publish fixture: required approval, executed only with `--approved`, and was
  still denied for the forbidden `all-company` channel.
- Tampering with either an event or the summary is detected by verification.

### Next task

Turn individual guarded calls into versioned, replayable adversarial scenarios
with expected outcomes and a deterministic benchmark score.
