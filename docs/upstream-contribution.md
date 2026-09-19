# Upstream contribution candidate

## Topic

Document loopback behavior when a developer machine has a global HTTP proxy.
During TraceGuard's real Streamable HTTP integration test, the default HTTP
client inherited the proxy environment and a request to `127.0.0.1` received a
proxy-generated 502 before reaching Uvicorn. A custom `httpx2.AsyncClient` with
`trust_env=False` fixed the literal loopback path.

This is a documentation/triage candidate, not a claim that the SDK is
incorrect. Inheriting environment proxies is a reasonable default for remote
servers, and automatically bypassing them could surprise users.

## Minimal reproduction

1. Configure `HTTP_PROXY`/`HTTPS_PROXY` without a matching `NO_PROXY` entry.
2. Start an official `MCPServer.streamable_http_app()` on `127.0.0.1`.
3. Connect with `Client("http://127.0.0.1:<port>/mcp")`.
4. Observe whether the proxy handles the request.
5. Repeat with an owned `httpx2.AsyncClient(trust_env=False)` passed to
   `streamable_http_client`; the loopback request should reach the server.

TraceGuard's regression coverage is in `tests/test_capture.py`, and its narrow
workaround is in `src/mcp_traceguard/connection.py`. The workaround disables
proxy inheritance only for `localhost` and literal loopback addresses. Remote
URLs retain the SDK default.

## Proposed issue text

**Title:** Document local Streamable HTTP behavior with environment proxies

**Body:** The client transport documentation explains how to provide an owned
`httpx2.AsyncClient` for proxy control. A short troubleshooting note could make
one local-development edge case easier to diagnose: when global proxy variables
are set and `NO_PROXY` does not cover localhost, a loopback MCP request may be
sent to the proxy. Please confirm whether the preferred guidance is to configure
`NO_PROXY` or pass `httpx2.AsyncClient(trust_env=False)` for a local-only test.
I can submit a small documentation patch and test after maintainer direction.

AI assistance was used to structure this reproduction and draft. I reviewed
the behavior against a real loopback server and can explain and maintain the
proposed change.

## Submission checklist

- Search for an existing issue immediately before submission.
- Open an issue first and wait for maintainer buy-in or `ready for work`.
- Disclose AI assistance, as required by the upstream policy.
- Keep any patch documentation-only unless maintainers request an API change.
- Run upstream `pytest`, `pyright`, Ruff, and documentation checks.

The official SDK already documents custom HTTP clients in its
[transport guide](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/client/transports.md),
and its
[contribution guide](https://github.com/modelcontextprotocol/python-sdk/blob/main/CONTRIBUTING.md)
requires an issue before non-trivial work. No external issue or PR has been
opened automatically; the repository owner should review and submit it.
