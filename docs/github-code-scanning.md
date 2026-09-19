# GitHub code scanning integration

TraceGuard emits the SARIF 2.1.0 subset accepted by GitHub code scanning. The
repository's normal CI preserves SARIF as a downloadable artifact without
requesting write access. A consuming repository can opt into Security-tab
alerts with a separate workflow like this:

```yaml
name: MCP capability scan

on:
  pull_request:
  push:

permissions:
  contents: read
  security-events: write

jobs:
  traceguard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - run: >-
          python -m pip install
          "mcp-traceguard @ git+https://github.com/tiempo0206/mcp-traceguard.git@v1.0.0"
      - name: Analyze MCP catalog
        continue-on-error: true
        run: |
          mcp-traceguard check \
            --baseline security/mcp-baseline.json \
            --policy security/mcp-policy.json \
            --report /tmp/traceguard-report.json \
            -- python server.py
      - name: Convert to SARIF
        run: |
          mcp-traceguard sarif \
            --report /tmp/traceguard-report.json \
            --output /tmp/traceguard.sarif \
            --artifact server.py
      - name: Upload findings
        uses: github/codeql-action/upload-sarif@v4
        with:
          sarif_file: /tmp/traceguard.sarif
```

The analysis step uses `continue-on-error` only so the conversion and upload can
still run when TraceGuard correctly returns exit code 1. Add a later policy gate
if the workflow must also fail the pull request.

GitHub documents the required `security-events: write` permission and the
`github/codeql-action/upload-sarif` action in its
[SARIF upload guide](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/integrate-with-existing-tools/upload-sarif-file).
TraceGuard emits SARIF version `2.1.0`, matching GitHub's
[supported SARIF format](https://docs.github.com/en/code-security/concepts/code-scanning/sarif-files).
