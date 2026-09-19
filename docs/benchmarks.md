# Benchmarks and regression budgets

The catalog benchmark isolates local canonicalization, SHA-256 fingerprinting,
policy checks, and baseline comparison. It intentionally excludes network,
server, model, and subprocess startup time.

## Committed result

The committed run used Python 3.13, seven measured trials, two warmups, and a
synthetic catalog with deterministic controlled drift.

| Tools | Fingerprint median | Analysis median | Fingerprint throughput |    Snapshot |   Report |
| ----: | -----------------: | --------------: | ---------------------: | ----------: | -------: |
|    10 |           0.060 ms |        0.052 ms |        166,667 tools/s |     4,931 B |  2,176 B |
|   100 |           0.569 ms |        0.087 ms |        175,747 tools/s |    49,390 B |  2,176 B |
| 1,000 |           6.080 ms |        0.819 ms |        164,474 tools/s |   495,042 B |  8,758 B |
| 5,000 |          32.411 ms |        4.509 ms |        154,269 tools/s | 2,479,721 B | 38,078 B |

Source: [`benchmarks/results/catalog-scale.json`](../benchmarks/results/catalog-scale.json).
These values describe one machine and are not universal latency claims.

## Reproduce

```bash
mcp-traceguard benchmark \
  --output /tmp/catalog-scale.json \
  --sizes 10 100 1000 5000 \
  --trials 7 \
  --warmups 2

mcp-traceguard benchmark-check \
  --benchmark /tmp/catalog-scale.json \
  --budget benchmarks/catalog-budget.json \
  --output /tmp/catalog-budget.report.json
```

The versioned report records Python and platform metadata, median and P95
timings, throughput, artifact sizes, finding counts, and risk scores.

## Why budgets are looser than the measured result

[`benchmarks/catalog-budget.json`](../benchmarks/catalog-budget.json) is a
portable regression gate, not a leaderboard. Its ceilings leave room for
shared GitHub runners while still catching order-of-magnitude regressions,
unexpected artifact growth, and missing scale results. CI benchmarks all four
scales and exits non-zero on any violation.

For microbenchmark decisions, compare repeated runs on the same idle machine;
do not infer network or full end-to-end latency from this CPU-only benchmark.
