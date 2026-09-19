# Tutorial: protect a small MCP server

This walkthrough shows the complete review loop on the safe fixtures included
in the repository.

## 1. Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## 2. Capture what you approve

```bash
mcp-traceguard snapshot \
  --output /tmp/approved.json \
  -- python examples/demo_server.py
```

The CLI negotiates MCP, follows all `tools/list` pages, sorts contracts by
name, and fingerprints security-relevant fields. Review `/tmp/approved.json`
before treating it as a baseline.

## 3. Detect a capability change

```bash
mcp-traceguard check \
  --baseline /tmp/approved.json \
  --policy examples/traceguard.policy.json \
  --report /tmp/drift.json \
  -- python examples/drifted_server.py
```

Exit status `1` is expected. The fixture advertises a new shell-shaped tool and
changes an existing description, but does not execute shell commands. Inspect
the `TG103` JSON Pointer changes rather than relying only on the risk score.

## 4. Guard a real protocol call

```bash
mcp-traceguard call \
  --tool read_profile \
  --arguments '{"user_id":"student"}' \
  --policy examples/runtime.policy.json \
  --trace /tmp/profile.trace.json \
  -- python examples/runtime_server.py

mcp-traceguard verify-trace /tmp/profile.trace.json
```

The fixture returns a fake token. TraceGuard persists `[REDACTED]`, records the
path, and seals four events. Try `publish_message` without and with
`--approved`, then try channel `all-company`: approval permits the ordinary
publish case but never overrides the conditional deny.

## 5. Replay the security claims

```bash
mcp-traceguard replay \
  --suite scenarios/runtime-security.json \
  --policy examples/runtime.policy.json \
  --output /tmp/scenarios.json \
  --trace-dir /tmp/traces \
  -- python examples/runtime_server.py
```

The eight cases make the expected decision, execution, redaction, rule match,
and integrity behavior reproducible without an API key.

## 6. Review locally

```bash
cd web
npm ci
npm run dev
```

Open <http://127.0.0.1:5174>, load the bundled demos, then import the artifacts
from `/tmp`. The browser independently verifies trace hashes and can create a
local approval receipt for a reviewed baseline.
