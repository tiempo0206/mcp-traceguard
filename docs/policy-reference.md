# Policy reference

Policies use strict JSON: unknown fields fail validation instead of being
silently ignored. The canonical example is
[`examples/runtime.policy.json`](../examples/runtime.policy.json).

## Catalog fields

| Field                          | Meaning                                                             |
| ------------------------------ | ------------------------------------------------------------------- |
| `schema_version`               | Currently `1.0`                                                     |
| `allowed_tools`                | Exact tool-name allowlist; `null` disables this catalog check       |
| `denied_name_patterns`         | Regular expressions checked against every advertised name           |
| `require_descriptions`         | Emit `TG003` when a description is empty                            |
| `require_closed_input_schemas` | Emit `TG004` unless object input sets `additionalProperties: false` |
| `fail_on`                      | Exit 1 on `error`, on `warning` or error, or `never`                |

Catalog rule IDs are stable: `TG001` allowlist, `TG002` denied name, `TG003`
missing description, `TG004` open object, `TG101` added tool, `TG102` removed
tool, and `TG103` changed contract.

## Runtime fields

`default_runtime_action` applies when no rule matches and defaults to `deny`.
Each runtime rule has a stable `id`, a full-match regular expression in
`tool_pattern`, an `action`, a reviewer-facing `reason`, and zero or more
conditions.

All matching rules are evaluated. Actions have fixed precedence:

```text
deny > require_approval > allow
```

Supplying `--approved` satisfies only `require_approval`; it can never override
`deny`.

Conditions resolve `path` as an RFC 6901-style JSON Pointer into tool
arguments. Supported operators are:

| Operator                  | Matches when                                       |
| ------------------------- | -------------------------------------------------- |
| `exists`                  | Presence equals the Boolean `value`                |
| `equals` / `not_equals`   | Argument equals / differs from `value`             |
| `matches` / `not_matches` | String form matches / does not match regex `value` |
| `in` / `not_in`           | Argument is / is not in list `value`               |
| `url_scheme_not_in`       | Parsed URL scheme is outside list `value`          |
| `url_host_not_in`         | Parsed hostname is outside list `value`            |

A condition can escalate its containing rule to `deny` or
`require_approval`. Conditions do not downgrade a stronger decision.

## Redaction fields

`sensitive_key_patterns` is a list of regular expressions applied to object
keys at every depth, including parseable embedded JSON strings. `replacement`
defaults to `[REDACTED]`. `max_string_length` bounds stored strings; byte values
become size-only placeholders.

Redaction is not a data-loss-prevention system. Add domain-specific key
patterns and inspect traces before sharing them.

## Validation

The machine-readable contract is
[`schemas/v1/policy.schema.json`](../schemas/v1/policy.schema.json). A quick
end-to-end validation is:

```bash
mcp-traceguard call \
  --tool read_profile \
  --arguments '{"user_id":"demo"}' \
  --policy examples/runtime.policy.json \
  --trace /tmp/profile.trace.json \
  -- python examples/runtime_server.py
```
