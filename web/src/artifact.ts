import type {
  AnalysisReport,
  Artifact,
  CatalogBenchmarkReport,
  ExecutionTrace,
  Json,
  ScenarioReport,
  ToolCatalogSnapshot,
} from "./types";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requireArray(value: Record<string, unknown>, key: string): void {
  if (!Array.isArray(value[key])) {
    throw new Error(`Invalid TraceGuard artifact: ${key} must be an array`);
  }
}

export function parseArtifact(input: unknown): Artifact {
  if (!isRecord(input) || input.schema_version !== "1.0") {
    throw new Error(
      "Unsupported artifact: expected a TraceGuard schema_version of 1.0",
    );
  }
  if (
    Array.isArray(input.findings) &&
    isRecord(input.risk) &&
    isRecord(input.summary)
  ) {
    return { kind: "analysis", data: input as unknown as AnalysisReport };
  }
  if (Array.isArray(input.results) && typeof input.suite_name === "string") {
    return { kind: "scenario", data: input as unknown as ScenarioReport };
  }
  if (Array.isArray(input.events) && typeof input.trace_hash === "string") {
    return { kind: "trace", data: input as unknown as ExecutionTrace };
  }
  if (Array.isArray(input.tools) && typeof input.captured_at === "string") {
    return { kind: "snapshot", data: input as unknown as ToolCatalogSnapshot };
  }
  if (
    Array.isArray(input.results) &&
    isRecord(input.environment) &&
    isRecord(input.config)
  ) {
    requireArray(input, "results");
    return {
      kind: "benchmark",
      data: input as unknown as CatalogBenchmarkReport,
    };
  }
  throw new Error("Unsupported TraceGuard artifact type");
}

export function parseArtifactJson(text: string): Artifact {
  let value: Json;
  try {
    value = JSON.parse(text) as Json;
  } catch (error) {
    throw new Error(
      `Invalid JSON: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
  return parseArtifact(value);
}
