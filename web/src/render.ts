import type {
  AnalysisReport,
  CatalogBenchmarkReport,
  ExecutionTrace,
  Finding,
  ScenarioReport,
  ToolCatalogSnapshot,
} from "./types";
import type { BaselineApproval } from "./storage";

export function escapeHtml(value: unknown): string {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString();
}

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(2)} MB`;
}

function card(
  label: string,
  value: string | number,
  detail: string,
  tone = "neutral",
): string {
  return `<article class="metric-card ${tone}"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(detail)}</small></article>`;
}

function jsonBlock(value: unknown): string {
  return `<pre>${escapeHtml(JSON.stringify(value, null, 2))}</pre>`;
}

function renderFinding(finding: Finding): string {
  const changes = Array.isArray(finding.details.changes)
    ? (finding.details.changes as Array<Record<string, unknown>>)
    : [];
  const changeRows = changes
    .map(
      (change) => `<tr>
        <td><code>${escapeHtml(change.path)}</code></td>
        <td><span class="impact ${escapeHtml(change.impact)}">${escapeHtml(change.impact)}</span></td>
        <td>${escapeHtml(change.explanation)}</td>
        <td>${jsonBlock({ before: change.before, after: change.after })}</td>
      </tr>`,
    )
    .join("");
  return `<details class="finding" data-severity="${finding.severity}" open>
    <summary>
      <span class="rule-badge">${escapeHtml(finding.rule_id)}</span>
      <span class="severity ${finding.severity}">${escapeHtml(finding.severity)}</span>
      <strong>${escapeHtml(finding.message)}</strong>
      <code>${escapeHtml(finding.tool ?? "server")}</code>
    </summary>
    <div class="finding-body">
      ${
        changeRows
          ? `<div class="table-wrap"><table><thead><tr><th>Path</th><th>Impact</th><th>Explanation</th><th>Evidence</th></tr></thead><tbody>${changeRows}</tbody></table></div>`
          : jsonBlock(finding.details)
      }
    </div>
  </details>`;
}

export function renderAnalysis(report: AnalysisReport): string {
  const riskTone =
    report.risk.rating === "none"
      ? "good"
      : report.risk.score >= 50
        ? "bad"
        : "warn";
  return `<div class="metric-grid">
    ${card("Decision", report.passed ? "PASS" : "FAIL", `threshold: ${report.fail_on}`, report.passed ? "good" : "bad")}
    ${card("Risk", `${report.risk.score}/100`, report.risk.rating, riskTone)}
    ${card("Errors", report.summary.errors, `${report.summary.total} total findings`, report.summary.errors ? "bad" : "good")}
    ${card("Warnings", report.summary.warnings, formatDate(report.generated_at), report.summary.warnings ? "warn" : "neutral")}
  </div>
  <section class="panel split-panel">
    <div class="risk-visual" style="--risk-score:${report.risk.score}">
      <div><strong>${report.risk.score}</strong><span>risk score</span></div>
    </div>
    <div>
      <p class="eyebrow">TRANSPARENT PRIORITIZATION</p>
      <h3>${escapeHtml(report.risk.rating)} catalog risk</h3>
      <p>Every point is traceable to a finding. This score ranks review urgency; it is not an exploit probability.</p>
      <div class="contribution-list">${report.risk.contributions
        .map(
          (item) =>
            `<span><b>+${item.points}</b> ${escapeHtml(item.rule_id)} · ${escapeHtml(item.tool ?? "server")}</span>`,
        )
        .join("")}</div>
    </div>
  </section>
  <section class="panel">
    <div class="panel-heading"><div><p class="eyebrow">FINDINGS</p><h3>Explainable contract evidence</h3></div>
      <div class="filter-group" role="group" aria-label="Filter findings">
        <button class="filter active" data-filter="all">All ${report.summary.total}</button>
        <button class="filter" data-filter="error">Errors ${report.summary.errors}</button>
        <button class="filter" data-filter="warning">Warnings ${report.summary.warnings}</button>
      </div>
    </div>
    <div class="findings-list">${report.findings.map(renderFinding).join("") || '<p class="empty-copy">No findings. The live catalog matches policy and baseline.</p>'}</div>
  </section>`;
}

export function renderScenario(report: ScenarioReport): string {
  const categories = Object.entries(report.summary.category_scores)
    .map(
      ([name, score]) =>
        `<div class="category-score"><span>${escapeHtml(name)}</span><strong>${score.toFixed(0)}%</strong><div><i style="width:${score}%"></i></div></div>`,
    )
    .join("");
  const cases = report.results
    .map(
      (
        result,
      ) => `<article class="scenario-card ${result.passed ? "passed" : "failed"}">
        <div class="scenario-title"><span>${result.passed ? "✓" : "×"}</span><div><small>${escapeHtml(result.category)}</small><h4>${escapeHtml(result.title)}</h4></div></div>
        <div class="check-grid">${result.checks
          .map(
            (check) =>
              `<div class="check ${check.passed ? "ok" : "no"}"><span>${check.passed ? "PASS" : "FAIL"}</span><strong>${escapeHtml(check.name)}</strong><small>expected ${escapeHtml(JSON.stringify(check.expected))}<br>observed ${escapeHtml(JSON.stringify(check.observed))}</small></div>`,
          )
          .join("")}</div>
        <footer><code>${escapeHtml(result.trace_file)}</code><span>${escapeHtml(result.trace_id.slice(0, 8))}</span></footer>
      </article>`,
    )
    .join("");
  return `<div class="metric-grid">
    ${card("Suite", report.passed ? "PASS" : "FAIL", report.suite_name, report.passed ? "good" : "bad")}
    ${card("Score", `${report.summary.score_percent.toFixed(0)}%`, `${report.summary.passed}/${report.summary.total} cases`, report.passed ? "good" : "warn")}
    ${card("Passed", report.summary.passed, "observable contracts", "good")}
    ${card("Failed", report.summary.failed, formatDate(report.generated_at), report.summary.failed ? "bad" : "neutral")}
  </div>
  <section class="panel"><div class="panel-heading"><div><p class="eyebrow">COVERAGE</p><h3>Category scorecard</h3></div></div><div class="category-grid">${categories}</div></section>
  <section class="panel"><div class="panel-heading"><div><p class="eyebrow">REPLAY EVIDENCE</p><h3>Scenario checks</h3></div></div><div class="scenario-list">${cases}</div></section>`;
}

export function renderTrace(
  trace: ExecutionTrace,
  integrityErrors: string[] | null,
): string {
  const integrityLabel =
    integrityErrors === null
      ? "VERIFYING"
      : integrityErrors.length
        ? "TAMPERED"
        : "VERIFIED";
  const integrityTone =
    integrityErrors === null ? "warn" : integrityErrors.length ? "bad" : "good";
  const events = trace.events
    .map(
      (event) => `<article class="trace-event ${event.event_type}">
        <div class="event-marker"><span>${event.sequence}</span></div>
        <div class="event-content"><header><span class="event-type">${escapeHtml(event.event_type)}</span><time>${escapeHtml(formatDate(event.timestamp))}</time></header>
          ${jsonBlock(event.payload)}
          <footer><span>prev ${escapeHtml(event.previous_hash.slice(0, 12))}…</span><span>hash ${escapeHtml(event.event_hash.slice(0, 12))}…</span></footer>
        </div>
      </article>`,
    )
    .join("");
  return `<div class="metric-grid">
    ${card("Integrity", integrityLabel, "SHA-256 chain + final seal", integrityTone)}
    ${card("Decision", trace.summary.outcome.toUpperCase(), trace.summary.call_executed ? "tool executed" : "not executed", trace.summary.outcome === "allow" ? "good" : trace.summary.outcome === "error" ? "bad" : "warn")}
    ${card("Redactions", trace.summary.redaction_count, "sensitive or bounded fields", trace.summary.redaction_count ? "warn" : "neutral")}
    ${card("Duration", `${trace.summary.duration_ms.toFixed(1)} ms`, `${trace.summary.event_count} chained events`)}
  </div>
  ${integrityErrors?.length ? `<div class="integrity-errors">${integrityErrors.map((error) => `<p>${escapeHtml(error)}</p>`).join("")}</div>` : ""}
  <section class="panel"><div class="panel-heading"><div><p class="eyebrow">TRACE ${escapeHtml(trace.trace_id.slice(0, 8))}</p><h3>${escapeHtml(trace.tool)} event timeline</h3></div><code class="hash-chip">seal ${escapeHtml(trace.trace_hash.slice(0, 16))}…</code></div><div class="trace-timeline">${events}</div></section>`;
}

export function renderBenchmark(report: CatalogBenchmarkReport): string {
  const maxFingerprint = Math.max(
    ...report.results.map((item) => item.fingerprint.median_ms),
  );
  const rows = report.results
    .map(
      (result) => `<tr>
        <td><strong>${result.tool_count.toLocaleString()}</strong></td>
        <td><div class="bench-value"><span>${result.fingerprint.median_ms.toFixed(3)} ms</span><i style="width:${(result.fingerprint.median_ms / maxFingerprint) * 100}%"></i></div><small>P95 ${result.fingerprint.p95_ms.toFixed(3)} ms</small></td>
        <td>${result.analysis.median_ms.toFixed(3)} ms<br><small>P95 ${result.analysis.p95_ms.toFixed(3)} ms</small></td>
        <td>${Math.round(result.fingerprint_tools_per_second).toLocaleString()}/s</td>
        <td>${formatBytes(result.snapshot_bytes)}</td>
        <td>${result.findings}</td>
      </tr>`,
    )
    .join("");
  const largest = report.results.at(-1)!;
  return `<div class="metric-grid">
    ${card("Largest catalog", largest.tool_count.toLocaleString(), `${formatBytes(largest.snapshot_bytes)} snapshot`)}
    ${card("Fingerprint", `${largest.fingerprint.median_ms.toFixed(1)} ms`, "median at largest scale", "good")}
    ${card("Analysis", `${largest.analysis.median_ms.toFixed(1)} ms`, `${largest.controlled_changes} controlled changes`, "good")}
    ${card("Throughput", `${Math.round(largest.fingerprint_tools_per_second / 1000)}k/s`, `Python ${report.environment.python}`)}
  </div>
  <section class="panel"><div class="panel-heading"><div><p class="eyebrow">SYNTHETIC CATALOG SCALE</p><h3>Canonicalization and policy analysis</h3></div><span class="source-chip">${report.config.trials} trials · ${report.config.warmups} warmups</span></div>
    <div class="table-wrap"><table class="benchmark-table"><thead><tr><th>Tools</th><th>Fingerprint median</th><th>Analysis median</th><th>Throughput</th><th>Snapshot</th><th>Findings</th></tr></thead><tbody>${rows}</tbody></table></div>
    <p class="method-note">No network or model calls. Timings are machine-specific: ${escapeHtml(report.environment.platform)} · ${escapeHtml(formatDate(report.generated_at))}.</p>
  </section>`;
}

export function renderSnapshot(
  snapshot: ToolCatalogSnapshot,
  approvals: BaselineApproval[],
): string {
  const latest = approvals[0];
  const tools = snapshot.tools
    .map(
      (tool) =>
        `<details class="tool-card"><summary><div><strong>${escapeHtml(tool.name)}</strong><span>${escapeHtml(tool.description ?? "No description")}</span></div><code>${escapeHtml(tool.fingerprint.slice(0, 12))}…</code></summary><div class="tool-contract"><h5>Input Schema</h5>${jsonBlock(tool.input_schema)}<h5>Output Schema</h5>${jsonBlock(tool.output_schema)}</div></details>`,
    )
    .join("");
  const history = approvals
    .map(
      (approval) =>
        `<article><div><strong>${escapeHtml(approval.server.name ?? "Unnamed server")}</strong><span>${approval.tool_count} tools · ${escapeHtml(formatDate(approval.approved_at))}</span></div><code>${escapeHtml(approval.snapshot_hash.slice(0, 16))}…</code><button class="text-button" data-receipt="${escapeHtml(approval.snapshot_hash)}">Export receipt</button></article>`,
    )
    .join("");
  return `<div class="metric-grid">
    ${card("Tools", snapshot.tools.length, "advertised contracts")}
    ${card("Protocol", snapshot.server.protocol_version, snapshot.server.version || "server version unset")}
    ${card("Captured", formatDate(snapshot.captured_at), snapshot.server.name ?? "Unnamed server")}
    ${card("Approved baselines", approvals.length, latest ? `latest ${formatDate(latest.approved_at)}` : "none yet", approvals.length ? "good" : "warn")}
  </div>
  <section class="panel approval-panel"><div><p class="eyebrow">HUMAN CHECKPOINT</p><h3>Approve this exact capability baseline</h3><p>The receipt binds server identity, tool count, source name, note, and a browser-computed SHA-256 snapshot hash.</p></div><div class="approval-form"><label for="approval-note">Approval note</label><input id="approval-note" placeholder="Reviewed tool scope and schemas" maxlength="240"><button class="button primary" id="approve-button">Approve baseline</button></div></section>
  <div class="catalog-layout"><section class="panel"><div class="panel-heading"><div><p class="eyebrow">CATALOG</p><h3>Tool contracts</h3></div></div><div class="tool-list">${tools}</div></section><section class="panel history-panel"><div class="panel-heading"><div><p class="eyebrow">LOCAL HISTORY</p><h3>Approval receipts</h3></div>${approvals.length ? '<button class="text-button danger" id="clear-approvals">Clear</button>' : ""}</div>${history || '<p class="empty-copy">No approved baseline is stored in this browser.</p>'}</section></div>`;
}
