# Security policy

## Reporting a vulnerability

Please do not open a public issue for a vulnerability that could expose secrets
or enable policy bypass. Use GitHub's private vulnerability reporting for this
repository when available, and include the affected version, a minimal safe
reproduction, impact, and suggested mitigation. Do not include real tokens or
private MCP data.

## Supported version

Security fixes target the latest tagged release on `main`.

## Scope reminder

TraceGuard is a policy and evidence layer, not a sandbox. Its hash chains detect
artifact modification but do not authenticate authors. Redaction is best effort
and must be configured for local data. See
[`docs/threat-model.md`](docs/threat-model.md) for the complete boundary.
