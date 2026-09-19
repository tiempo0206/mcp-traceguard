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

## 2026-09-18 — Day 1 continued: replayable security pack and SARIF

### Goal

Make security claims reproducible across machines and export evidence in a form
that existing CI platforms understand.

### Work completed

- Added a versioned scenario-suite contract and replay runner.
- Built an eight-case security pack covering secret redaction, shell denial,
  explicit approval, deny precedence, default deny, and URL scheme/host bounds.
- Scored five observable properties per case: decision, actual execution,
  redaction count, matched rules, and trace integrity.
- Added per-category scores and preserved one sealed trace per case.
- Added a transparent 0–100 catalog risk score with per-finding contributions
  and documented that it is a prioritization aid rather than probability.
- Added GitHub-compatible SARIF 2.1.0 output with stable partial fingerprints,
  rule metadata, locations, and risk properties.
- Extended CI to replay the pack, create SARIF, and upload it as an artifact.
- Added strict JSON Schemas for scenario suites and scenario reports.

### Verification

- Ruff format and lint: passed.
- Pytest: 20 tests passed.
- Runtime Security Pack: 8/8 scenarios passed with all generated trace chains
  independently verified.
- Drift fixture: four findings converted to four SARIF 2.1.0 results.
- Committed artifact-schema regression test covers all six current formats.

### Next task

Build reproducible scale benchmarks and stable result summaries, then surface
catalog, scenario, SARIF, and trace evidence in a local browser application.

## 2026-09-18 — Day 1 continued: scale benchmark

### Goal

Measure the CPU-side cost and artifact growth of catalog assurance without
mixing network or model latency into the result.

### Work completed

- Added a versioned synthetic catalog benchmark for 10, 100, 1000, and 5000
  tools with controlled additions, removals, description changes, and enum
  widening.
- Measured canonicalization plus SHA-256 fingerprinting separately from policy
  and baseline analysis over seven trials and two warmups.
- Recorded median, P95, throughput, snapshot bytes, report bytes, finding count,
  and risk score with Python/platform provenance.
- Added a benchmark JSON Schema, CLI command, CI smoke run, and regression test.

### Verification

- 5000-tool fingerprint median: 32.411 ms.
- 5000-tool analysis median: 4.509 ms.
- Fingerprint throughput across tested sizes: 154,269–175,747 tools/second.
- The committed result is explicitly scoped to an in-memory synthetic catalog.

## 2026-09-18 — Day 1 continued: Evidence Studio

### Goal

Turn the JSON outputs into a local product that a reviewer can use without a
backend or specialized command-line knowledge.

### Work completed

- Built a responsive TypeScript/Vite Evidence Studio with no remote assets.
- Added local import and bundled demos for catalog, scenario, trace, benchmark,
  and baseline artifacts.
- Added finding filters, risk contributions, human-readable contract diffs,
  scenario scorecards, trace timelines, and scale tables.
- Independently implemented canonical JSON and SHA-256 trace verification in
  TypeScript, including a test against a Python-generated trace.
- Added localStorage baseline approvals, browser-computed hashes, history, and
  exportable receipts.
- Escaped all imported text and documented the browser trust boundary.
- Added a second GitHub Actions job for format, strict typecheck, tests, build,
  and dependency audit.

### Verification

- Frontend unit tests: 10 passed.
- TypeScript strict typecheck: passed.
- Production build: passed (about 17.6 KB JavaScript and 14.6 KB CSS before
  gzip at this milestone).
- npm audit: zero vulnerabilities.
- Real browser QA passed on desktop and a 390 px mobile viewport.
- Verified all five demos, four finding filters, 8 scenarios/40 checks,
  browser-side Python trace verification, approval persistence after refresh,
  and zero browser console warnings/errors.
- Browser QA found and fixed a CSS specificity bug that prevented the empty
  state from hiding after evidence was loaded.

## 2026-09-18 — Day 1 continued: protocol compatibility

### Goal

Prove the tool does not depend on only one in-process happy path.

### Work completed

- Added integration coverage for the 2026-07-28 protocol over in-memory and
  real loopback Streamable HTTP transports.
- Added legacy-handshake coverage through the official client's legacy mode.
- Retained the existing subprocess stdio smoke path in CI.
- Diagnosed a macOS system-proxy interception that returned 502 before local
  MCP traffic reached the server.
- Added narrowly scoped loopback detection that disables environment proxies
  only for `localhost` and literal loopback IP addresses; remote HTTP targets
  keep the official SDK defaults.

### Verification

- In-memory modern discovery: passed.
- In-memory legacy handshake and discovery: passed.
- Real Streamable HTTP discovery: passed.
- Stdio discovery and analysis remain exercised by CI.

### Next task

Complete the threat model, architecture, policy reference, benchmark report,
resume evidence, release packaging, and final requirement-by-requirement audit.

## 2026-09-19 — Day 2: performance gates and release candidate

### Goal

Turn the working prototype into a complete, reproducible portfolio release with
explicit claim boundaries and enough evidence for another developer to audit
the implementation.

### Work completed

- Added versioned benchmark-budget and budget-report models, JSON Schemas, a
  `benchmark-check` command, missing-scale detection, and CI enforcement across
  10, 100, 1,000, and 5,000 tools.
- Added portable ceilings for timing, throughput, snapshot size, and report
  size; kept them deliberately wider than one laptop's measurements.
- Added architecture, threat model, policy reference, benchmark methodology,
  protocol compatibility, SARIF upload, tutorial, Evidence Studio, and
  Chinese/English resume documentation.
- Added contribution, vulnerability-reporting, changelog, and upstream
  contribution-candidate documents.
- Captured a real Evidence Studio screenshot and promoted package and frontend
  metadata to version 1.0.0.
- Added `--version` and flattened nested exception groups so transport failures
  show the actionable leaf errors.

### Verification lesson

The first release script invoked the CLI from `.venv` but launched a fixture
with the system `python`, which correctly failed because that interpreter did
not contain the MCP dependency. This exposed the weak nested TaskGroup message.
The CLI now reports leaf errors, and the corrected verification explicitly uses
the virtual environment's Python for child MCP servers. A normal quick-start
session also works because activating the environment places that Python first
on `PATH`.

### Final local verification

- Python dependency check: passed.
- Ruff formatting and lint: passed.
- Python tests: 28 passed, including modern/legacy in-memory negotiation, real
  Streamable HTTP, semantic diffs, trace tampering, scenarios, SARIF, benchmark
  budgets, schema regression, and CLI errors.
- All nine generated JSON Schemas exactly matched the committed copies.
- Python wheel `mcp_traceguard-1.0.0-py3-none-any.whl` built, installed into an
  isolated target, imported, and reported version 1.0.0.
- Real stdio positive check: 0 findings; deliberate drift: 4 errors and exit 1.
- Guarded profile call: allowed, 4 chained events, 2 redactions; independent
  verification passed and the fake credential literal was absent on disk.
- Runtime Security Pack: 8/8 cases and all 40 checks passed.
- SARIF: 4 results, SARIF 2.1.0, tool semantic version 1.0.0.
- Fresh performance run satisfied all four portable budgets; the 5,000-tool
  run fingerprinted in 33.526 ms median and analyzed in 4.759 ms median on the
  release machine.
- Clean `npm ci`, Prettier, strict TypeScript check, 10 frontend tests,
  production build, and high-severity dependency audit all passed; audit found
  zero vulnerabilities.

### Final browser verification

- Loaded catalog drift, scenario, trace, benchmark, and baseline demos in the
  real in-app browser.
- Observed 4 explainable findings at risk 83/100, 8/8 scenario cases at 100%, a
  verified four-event trace with two redactions, and the 5,000-tool benchmark.
- Approved the exact baseline and confirmed two approval receipts remained
  visible after a full page reload.
- Confirmed 1280 px desktop and 390 px mobile layouts had equal client and
  document widths (no horizontal overflow).
- Browser console contained zero warnings or errors.

### Release

- Release implementation commit:
  [`6f7d606`](https://github.com/tiempo0206/mcp-traceguard/commit/6f7d606864b11a026e9a1a128a6d5386c619562a).
- Clean GitHub Actions run:
  [`35418095710`](https://github.com/tiempo0206/mcp-traceguard/actions/runs/35418095710),
  with the Python and Web jobs both passing.
- Published tag and release:
  [`v1.0.0`](https://github.com/tiempo0206/mcp-traceguard/releases/tag/v1.0.0).
- Upgraded SARIF artifact upload from `actions/upload-artifact@v4` to the
  current Node 24-based `v7` after the successful release run surfaced the
  platform's Node 20 retirement annotation.
- Pinned both CI jobs to `ubuntu-24.04` instead of the migrating
  `ubuntu-latest` alias so benchmark and compatibility evidence keep an
  explicit runner baseline.

### External contribution boundary

No third-party issue or pull request was opened automatically. The upstream
candidate follows the SDK's issue-first and AI-disclosure rules and is ready for
the repository owner to review and submit.
