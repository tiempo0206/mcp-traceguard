import "./style.css";

import { parseArtifact, parseArtifactJson } from "./artifact";
import { verifyTrace } from "./integrity";
import {
  renderAnalysis,
  renderBenchmark,
  renderScenario,
  renderSnapshot,
  renderTrace,
} from "./render";
import {
  approvalReceipt,
  approveSnapshot,
  clearApprovals,
  loadApprovals,
  type BaselineApproval,
} from "./storage";
import type { Artifact } from "./types";

const demoFiles: Record<string, string> = {
  "drift-report": "/demo/drift-report.json",
  "runtime-scenarios": "/demo/runtime-security.report.json",
  "execution-trace": "/demo/profile.trace.json",
  "catalog-benchmark": "/demo/catalog-scale.json",
  baseline: "/demo/demo-baseline.json",
};

const fileInput = document.querySelector<HTMLInputElement>("#file-input")!;
const importButton =
  document.querySelector<HTMLButtonElement>("#import-button")!;
const demoButton = document.querySelector<HTMLButtonElement>("#demo-button")!;
const demoSelect = document.querySelector<HTMLSelectElement>("#demo-select")!;
const clearButton = document.querySelector<HTMLButtonElement>("#clear-button")!;
const workspace = document.querySelector<HTMLElement>("#workspace")!;
const principles = document.querySelector<HTMLElement>("#empty-principles")!;
const artifactView = document.querySelector<HTMLElement>("#artifact-view")!;
const artifactKind = document.querySelector<HTMLElement>("#artifact-kind")!;
const artifactTitle = document.querySelector<HTMLElement>("#artifact-title")!;
const artifactSubtitle =
  document.querySelector<HTMLElement>("#artifact-subtitle")!;
const sourceChip = document.querySelector<HTMLElement>("#source-chip")!;
const errorMessage = document.querySelector<HTMLElement>("#error-message")!;

let currentArtifact: Artifact | null = null;
let currentSource = "";

function showError(message: string): void {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
}

function clearError(): void {
  errorMessage.hidden = true;
  errorMessage.textContent = "";
}

function metadata(artifact: Artifact): [string, string, string] {
  switch (artifact.kind) {
    case "analysis":
      return [
        "CATALOG ANALYSIS",
        "Capability drift report",
        `${artifact.data.summary.total} findings · risk ${artifact.data.risk.score}/100`,
      ];
    case "scenario":
      return [
        "SCENARIO REPLAY",
        artifact.data.suite_name,
        `${artifact.data.summary.passed}/${artifact.data.summary.total} observable contracts passed`,
      ];
    case "trace":
      return [
        "EXECUTION TRACE",
        artifact.data.tool,
        `${artifact.data.events.length} chained events · ${artifact.data.server.name ?? "unnamed server"}`,
      ];
    case "snapshot":
      return [
        "CAPABILITY BASELINE",
        artifact.data.server.name ?? "Tool catalog",
        `${artifact.data.tools.length} tools · ${artifact.data.server.protocol_version}`,
      ];
    case "benchmark":
      return [
        "SCALE BENCHMARK",
        "Catalog performance",
        `${artifact.data.results.length} catalog sizes · ${artifact.data.config.trials} trials`,
      ];
  }
}

async function renderCurrent(): Promise<void> {
  if (!currentArtifact) return;
  const [kind, title, subtitle] = metadata(currentArtifact);
  artifactKind.textContent = kind;
  artifactTitle.textContent = title;
  artifactSubtitle.textContent = subtitle;
  sourceChip.textContent = currentSource;
  workspace.hidden = false;
  principles.hidden = true;
  switch (currentArtifact.kind) {
    case "analysis":
      artifactView.innerHTML = renderAnalysis(currentArtifact.data);
      break;
    case "scenario":
      artifactView.innerHTML = renderScenario(currentArtifact.data);
      break;
    case "trace": {
      artifactView.innerHTML = renderTrace(currentArtifact.data, null);
      const errors = await verifyTrace(currentArtifact.data);
      if (currentArtifact?.kind === "trace")
        artifactView.innerHTML = renderTrace(currentArtifact.data, errors);
      break;
    }
    case "snapshot":
      artifactView.innerHTML = renderSnapshot(
        currentArtifact.data,
        loadApprovals(),
      );
      break;
    case "benchmark":
      artifactView.innerHTML = renderBenchmark(currentArtifact.data);
      break;
  }
  workspace.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function openArtifact(artifact: Artifact, source: string): Promise<void> {
  currentArtifact = artifact;
  currentSource = source;
  clearError();
  await renderCurrent();
}

function downloadJson(filename: string, value: unknown): void {
  const url = URL.createObjectURL(
    new Blob([`${JSON.stringify(value, null, 2)}\n`], {
      type: "application/json",
    }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

importButton.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", async () => {
  const file = fileInput.files?.[0];
  if (!file) return;
  try {
    await openArtifact(parseArtifactJson(await file.text()), file.name);
  } catch (error) {
    showError(error instanceof Error ? error.message : String(error));
  } finally {
    fileInput.value = "";
  }
});

demoButton.addEventListener("click", async () => {
  try {
    const path = demoFiles[demoSelect.value];
    if (!path) throw new Error("Unknown demo selection");
    const response = await fetch(path);
    if (!response.ok)
      throw new Error(`Could not load demo (${response.status})`);
    await openArtifact(
      parseArtifact(await response.json()),
      path.split("/").at(-1) ?? "demo",
    );
  } catch (error) {
    showError(error instanceof Error ? error.message : String(error));
  }
});

clearButton.addEventListener("click", () => {
  currentArtifact = null;
  artifactView.innerHTML = "";
  workspace.hidden = true;
  principles.hidden = false;
});

artifactView.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;

  const filter = target.closest<HTMLButtonElement>("[data-filter]");
  if (filter) {
    const value = filter.dataset.filter;
    document
      .querySelectorAll(".filter")
      .forEach((button) => button.classList.remove("active"));
    filter.classList.add("active");
    artifactView
      .querySelectorAll<HTMLElement>(".finding")
      .forEach((finding) => {
        finding.hidden = value !== "all" && finding.dataset.severity !== value;
      });
    return;
  }

  if (
    target.closest("#approve-button") &&
    currentArtifact?.kind === "snapshot"
  ) {
    const note =
      artifactView.querySelector<HTMLInputElement>("#approval-note")?.value ??
      "";
    await approveSnapshot(currentArtifact.data, currentSource, note);
    await renderCurrent();
    return;
  }

  if (target.closest("#clear-approvals")) {
    clearApprovals();
    await renderCurrent();
    return;
  }

  const receiptButton = target.closest<HTMLButtonElement>("[data-receipt]");
  if (receiptButton) {
    const approval = loadApprovals().find(
      (item: BaselineApproval) =>
        item.snapshot_hash === receiptButton.dataset.receipt,
    );
    if (approval)
      downloadJson(
        `traceguard-approval-${approval.snapshot_hash.slice(0, 8)}.json`,
        approvalReceipt(approval),
      );
  }
});

window.addEventListener("dragover", (event) => event.preventDefault());
window.addEventListener("drop", async (event) => {
  event.preventDefault();
  const file = event.dataTransfer?.files[0];
  if (!file) return;
  try {
    await openArtifact(parseArtifactJson(await file.text()), file.name);
  } catch (error) {
    showError(error instanceof Error ? error.message : String(error));
  }
});
