# Two-week roadmap

MCP TraceGuard is scoped as a complete portfolio project that can be built and
verified without paid model credentials.

## Week 1 — trustworthy capability contracts (complete)

- [x] Day 1: repository, official MCP SDK connection, deterministic tool snapshots,
      SHA-256 fingerprints, policy checks, baseline drift detection, tests, and CI.
- [x] Day 2: richer schema-diff explanations and versioned JSON Schemas for every
      artifact.
- [x] Day 3: adversarial fixture servers for tool addition, description poisoning,
      schema widening, and misleading safety annotations.
- [x] Day 4: runtime call recorder with secret redaction and bounded trace storage.
- [x] Day 5: replayable security scenarios and a deterministic risk scorer.
- [x] Day 6: SARIF output and a GitHub code-scanning example.
- [x] Day 7: reliability benchmark and first committed result set.

## Week 2 — usable security product (complete)

- [x] Day 8: local browser trace viewer and finding explorer.
- [x] Day 9: baseline approval workflow and human-readable contract diff.
- [x] Day 10: protocol-version compatibility matrix for stdio and Streamable HTTP.
- [x] Day 11: performance measurements and regression budgets.
- [x] Day 12: end-to-end tests, threat model, and security documentation.
- [x] Day 13: public demo, screenshot, architecture documentation, and resume copy.
- [x] Day 14: final QA, tagged `v1.0.0` release, and a carefully scoped
      upstream contribution candidate. External submission remains an explicit
      owner decision under the upstream project's human-review policy.

## Definition of done

The project is complete when a user can snapshot a real MCP server, approve a
least-privilege baseline, detect contract and runtime policy violations in CI,
inspect evidence locally, reproduce benchmark results, and understand both the
security model and known limitations from the documentation.

Evidence for each criterion is linked from the README and recorded in the
project log. The release scope deliberately excludes sandboxing, authenticated
audit storage, and automated submission to third-party repositories.
