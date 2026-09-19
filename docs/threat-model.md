# Threat model

## Security objective

TraceGuard helps an MCP client detect when a server advertises more capability
than was approved, reject disallowed calls before invocation, and retain
reviewable evidence without intentionally storing common secret fields.

## Assets and trust boundaries

- **Approved capability boundary:** tool names, descriptions, input/output
  schemas, annotations, and runtime argument constraints.
- **Secrets in evidence:** tokens, passwords, cookies, authorization values,
  API keys, and configured sensitive fields.
- **Evidence integrity:** catalog reports, scenario results, and execution
  traces used in CI or a review.
- **Operator intent:** explicit approval for side-effecting calls and baseline
  changes.

The MCP server, its tool descriptions, schemas, annotations, and returned data
are untrusted. The local policy, reviewed baseline, TraceGuard process, and CI
configuration are trusted. A browser session used for Evidence Studio is
trusted only to the degree of the local machine and origin.

## Addressed threats

| Threat                                     | Control                                         | Evidence                                   |
| ------------------------------------------ | ----------------------------------------------- | ------------------------------------------ |
| A server adds an unreviewed tool           | Allowlist and `TG101` baseline drift            | Non-zero CI exit, JSON, SARIF              |
| A tool silently widens accepted input      | Canonical fingerprint plus semantic schema diff | JSON Pointer and broadening classification |
| A description or safety annotation changes | Whole-contract fingerprint                      | Behavioral/metadata diff                   |
| A dangerous name is exposed                | Denied-name regexes                             | `TG002` finding                            |
| A call exceeds argument bounds             | Pre-call conditions and default deny            | Decision event; call is not executed       |
| Approval is used to bypass a deny          | Fixed deny-over-approval precedence             | Replay scenario                            |
| Common secret fields enter a trace         | Recursive key-based redaction and truncation    | Redacted paths and scenario checks         |
| A saved trace is edited                    | Event hash chain and final trace seal           | Python and browser verification            |
| A regression makes checks impractical      | Reproducible benchmark budgets                  | CI budget verdict                          |

## Important limitations

- TraceGuard is not a process sandbox, network firewall, authorization server,
  malware scanner, or substitute for OS/container isolation.
- SHA-256 chaining detects modification of a trace; it does not authenticate
  the author, establish trusted time, or prevent deletion. Use signatures and
  an append-only store if identity and non-repudiation are required.
- Redaction is key-pattern based and best effort. A secret hidden under an
  innocuous key or inside opaque prose can remain visible. Operators should
  minimize captured data and extend patterns for their environment.
- Tool descriptions and annotations are evidence, not proof of behavior. A
  server can advertise a read-only tool that performs side effects.
- Baseline approval proves only that a particular JSON document was reviewed
  in the local workflow. It does not attest to server binaries or deployment
  identity.
- Regex and URL rules inspect provided arguments, not every downstream request
  a server may make. DNS rebinding, redirects, and server-side transformations
  require enforcement closer to the network boundary.
- Streamable HTTP authentication, transport encryption, server identity, and
  OAuth configuration remain responsibilities of the MCP client and operator.

## Safe deployment guidance

Run untrusted servers with least OS privilege, restrict filesystem and network
access, pin dependencies, review policy and baseline changes like code, keep
approval artifacts outside untrusted repositories, and treat a TraceGuard pass
as one defense layer rather than a complete security claim.

Report suspected vulnerabilities privately as described in
[`SECURITY.md`](../SECURITY.md).
