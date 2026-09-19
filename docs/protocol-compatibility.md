# Protocol compatibility

TraceGuard uses the official Python SDK client rather than implementing MCP
framing itself. Compatibility tests exercise protocol negotiation and tool
discovery at three boundaries.

| Path                   | Test                            | Protocol evidence                     | CI status                   |
| ---------------------- | ------------------------------- | ------------------------------------- | --------------------------- |
| In-memory, modern      | Real `MCPServer` and `Client`   | Negotiates `2026-07-28`               | Automated                   |
| In-memory, legacy mode | Official client `mode="legacy"` | Negotiates an older version           | Automated                   |
| Streamable HTTP        | Real Uvicorn loopback server    | Negotiates `2026-07-28`               | Automated                   |
| stdio                  | Python subprocess fixture       | Snapshot/check/call/replay smoke path | Automated in GitHub Actions |

The tests live in [`tests/test_capture.py`](../tests/test_capture.py) and the
stdio workflow in [`.github/workflows/test.yml`](../.github/workflows/test.yml).

For literal loopback URLs and `localhost`, TraceGuard disables environment
proxy inheritance. This avoids accidental interception of local test traffic
on systems with a global HTTP proxy. Remote targets retain the SDK and HTTP
client defaults.

## Boundaries of this matrix

- It proves the tested SDK version can negotiate and paginate `tools/list` over
  these transports; it is not certification of every MCP feature.
- SSE-only legacy transports, authentication providers, OAuth flows, sampling,
  elicitation, resources, prompts, and production TLS are outside the current
  scope.
- The package currently supports `mcp>=2.2,<3` and Python 3.11 or newer.
