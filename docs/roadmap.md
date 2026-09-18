# Two-week roadmap

MCP TraceGuard is scoped as a complete portfolio project that can be built and
verified without paid model credentials.

## Week 1 — trustworthy capability contracts

- Day 1: repository, official MCP SDK connection, deterministic tool snapshots,
  SHA-256 fingerprints, policy checks, baseline drift detection, tests, and CI.
- Day 2: richer schema-diff explanations and versioned JSON Schemas for every
  artifact.
- Day 3: adversarial fixture servers for tool addition, description poisoning,
  schema widening, and misleading safety annotations.
- Day 4: runtime call recorder with secret redaction and bounded trace storage.
- Day 5: replayable security scenarios and a deterministic risk scorer.
- Day 6: SARIF output and a GitHub code-scanning example.
- Day 7: reliability benchmark and first committed result set.

## Week 2 — usable security product

- Day 8: local browser trace viewer and finding explorer.
- Day 9: baseline approval workflow and human-readable contract diff.
- Day 10: protocol-version compatibility matrix for stdio and Streamable HTTP.
- Day 11: performance measurements and regression budgets.
- Day 12: end-to-end tests, threat model, and security documentation.
- Day 13: public demo, screenshots, architecture documentation, and resume copy.
- Day 14: final QA, tagged release, and one carefully scoped upstream contribution.

## Definition of done

The project is complete when a user can snapshot a real MCP server, approve a
least-privilege baseline, detect contract and runtime policy violations in CI,
inspect evidence locally, reproduce benchmark results, and understand both the
security model and known limitations from the documentation.

