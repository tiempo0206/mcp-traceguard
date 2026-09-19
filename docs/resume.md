# Resume and interview evidence

Use claims that match the repository evidence. Replace generic wording with
your own role and what you personally learned before submitting an application.

## 中文简历版本

**MCP TraceGuard — MCP 能力契约测试与运行时审计工具**

Python、TypeScript、MCP、Pydantic、Vite、GitHub Actions、SARIF

- 基于官方 MCP SDK 开发确定性能力契约测试工具，支持 in-memory、stdio 与
  Streamable HTTP；通过规范化 JSON 与 SHA-256 指纹检测未授权工具新增、描述
  变化及输入/输出 Schema 漂移。
- 设计 deny-by-default 运行时策略、参数级条件与人工审批门；实现密钥脱敏、
  SHA-256 事件链和 Python/TypeScript 跨语言完整性校验，并用 8 个对抗场景、
  40 项断言复现安全行为。
- 构建本地 Evidence Studio、SARIF/JSON Schema 输出及双栈 CI；在可复现的
  5,000 工具合成基准中，指纹中位耗时 32.411 ms、策略分析 4.509 ms，并以
  性能预算防止回归（结果仅代表已记录测试环境）。

## English resume version

**MCP TraceGuard — capability-contract testing and runtime evidence for MCP**

Python, TypeScript, MCP, Pydantic, Vite, GitHub Actions, SARIF

- Built a deterministic capability-contract harness on the official MCP SDK
  across in-memory, stdio, and Streamable HTTP transports; canonicalized and
  fingerprinted tool contracts to detect unapproved capabilities and semantic
  JSON Schema drift.
- Designed deny-by-default runtime policies, argument constraints, approval
  gates, recursive redaction, and tamper-evident traces independently verified
  in Python and TypeScript; replayed 8 adversarial scenarios with 40 checks.
- Shipped a local Evidence Studio, strict versioned schemas, SARIF export, and
  dual-stack CI; measured 32.411 ms median fingerprinting and 4.509 ms analysis
  for a synthetic 5,000-tool catalog, with portable regression budgets.

## Evidence map

| Claim                          | Repository evidence                                        |
| ------------------------------ | ---------------------------------------------------------- |
| Real MCP integration           | `tests/test_capture.py`, CI stdio smoke tests              |
| Semantic drift detection       | `schema_diff.py`, `tests/test_schema_diff.py`, demo report |
| Runtime policy and redaction   | `runtime.py`, runtime policy, sealed traces                |
| Reproducible security behavior | Eight-case scenario pack and report                        |
| Cross-language verification    | `web/src/integrity.ts` and frontend tests                  |
| Scale claim                    | Committed benchmark JSON and budget gate                   |
| Product usability              | Evidence Studio, local approval workflow, browser QA       |

## Interview prompts

Be ready to explain why canonicalization precedes hashing, why descriptions are
part of the security-relevant contract, how deny precedence prevents approval
bypass, what the trace seal can and cannot prove, why key-based redaction is
incomplete, and why benchmark budgets are wider than one laptop's result.

## Claim boundaries

Do not describe TraceGuard as a sandbox, formal verification system, DLP
product, authenticated audit ledger, or complete MCP conformance suite. Do not
generalize the committed synthetic benchmark to network latency or production
server performance.
