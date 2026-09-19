# Contributing

Small, evidence-backed changes are welcome.

1. Create a focused branch and install `python -m pip install -e ".[dev]"`.
2. If changing the studio, run `npm ci` in `web/`.
3. Add a test or safe fixture for behavior changes.
4. Regenerate schemas with
   `mcp-traceguard export-schemas --output-dir schemas/v1 --force` after model
   changes.
5. Run the same checks as CI:

```bash
ruff format --check .
ruff check .
pytest
npm --prefix web run format:check
npm --prefix web run typecheck
npm --prefix web test
npm --prefix web run build
npm --prefix web audit --audit-level=high
```

New policy rules need a stable rule ID, positive and negative fixtures,
human-readable evidence, SARIF behavior where applicable, and documentation.
Never commit real credentials, private MCP responses, or production traces.
