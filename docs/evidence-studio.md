# Evidence Studio

Evidence Studio is the local browser companion to the TraceGuard CLI. It makes
machine-readable security evidence reviewable without introducing a backend or
uploading MCP data.

## Supported artifacts

The import detector accepts schema version `1.0` for:

- catalog snapshots;
- catalog analysis reports;
- runtime scenario reports;
- tamper-evident execution traces; and
- catalog-scale benchmark reports.

Unknown versions and unrecognized document shapes are rejected. Imported text
is escaped before rendering. The UI does not evaluate tool output as markup.

## Review workflows

### Catalog drift

Load an analysis report, inspect its deterministic risk contribution, filter by
severity, and expand `TG103` findings. Each contract change preserves a JSON
Pointer, impact classification, explanation, and before/after values.

### Scenario replay

Load a scenario report to inspect overall and per-category scores. Every case
shows whether TraceGuard observed the expected policy outcome, call execution,
redaction count, matched rules, and trace integrity.

### Trace integrity

The browser independently reimplements TraceGuard canonical JSON and SHA-256
verification. It checks sequence numbers, every previous-hash link, every event
content hash, the summary event count, and the final seal over trace metadata,
event root, and summary. This is cross-language verification, not a UI label
copied from the Python result.

### Baseline approval

Load a snapshot, inspect its complete tool contracts, add a review note, and
approve it. The browser hashes the full snapshot and stores up to ten approvals
in localStorage. An approval receipt can be exported as JSON. The receipt proves
which snapshot was approved; it does not provide a cryptographic identity or
digital signature.

## Trust boundary

- Imported and bundled artifacts stay inside the browser process.
- No API request sends artifact content to another service.
- Demo files are served as static assets by Vite.
- localStorage persists approvals only for the current origin.
- A SHA-256 seal detects modification; it does not prove who created the trace.
- A malicious MCP server must still be isolated by the operator. TraceGuard is a
  policy and evidence layer, not a process sandbox.

## Verification

Run the frontend checks from `web/`:

```bash
npm run format:check
npm run typecheck
npm test
npm run build
npm audit --audit-level=high
```

The unit suite includes a cross-language test that verifies a trace generated
and sealed by the Python implementation with the TypeScript implementation.
