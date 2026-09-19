export type Json =
  null | boolean | number | string | Json[] | { [key: string]: Json };

export interface ServerIdentity {
  name: string | null;
  version: string | null;
  protocol_version: string;
}

export interface Finding {
  rule_id: string;
  severity: "warning" | "error";
  message: string;
  tool: string | null;
  details: Record<string, Json>;
}

export interface RiskContribution {
  rule_id: string;
  tool: string | null;
  points: number;
  reason: string;
}

export interface AnalysisReport {
  schema_version: "1.0";
  generated_at: string;
  current_captured_at: string;
  baseline_captured_at: string | null;
  passed: boolean;
  fail_on: string;
  summary: { errors: number; warnings: number; total: number };
  risk: {
    score: number;
    rating: "none" | "low" | "moderate" | "high" | "critical";
    contributions: RiskContribution[];
  };
  findings: Finding[];
}

export interface ScenarioCheck {
  name: string;
  passed: boolean;
  expected: Json;
  observed: Json;
}

export interface ScenarioResult {
  id: string;
  title: string;
  category: string;
  passed: boolean;
  trace_file: string;
  trace_id: string;
  checks: ScenarioCheck[];
}

export interface ScenarioReport {
  schema_version: "1.0";
  suite_name: string;
  generated_at: string;
  server: ServerIdentity;
  passed: boolean;
  summary: {
    passed: number;
    failed: number;
    total: number;
    score_percent: number;
    category_scores: Record<string, number>;
  };
  results: ScenarioResult[];
}

export interface TraceEvent {
  sequence: number;
  timestamp: string;
  event_type: "catalog" | "request" | "decision" | "response" | "error";
  tool: string | null;
  payload: Record<string, Json>;
  previous_hash: string;
  event_hash: string;
}

export interface ExecutionTrace {
  schema_version: "1.0";
  trace_id: string;
  started_at: string;
  completed_at: string;
  server: ServerIdentity;
  tool: string;
  integrity: "sha256-chain-v1";
  events: TraceEvent[];
  summary: {
    outcome: "allow" | "deny" | "approval_required" | "error";
    call_executed: boolean;
    response_is_error: boolean | null;
    redaction_count: number;
    event_count: number;
    duration_ms: number;
  };
  trace_hash: string;
}

export interface ToolContract {
  name: string;
  title: string | null;
  description: string | null;
  input_schema: Record<string, Json>;
  output_schema: Record<string, Json> | null;
  annotations: Record<string, Json> | null;
  fingerprint: string;
}

export interface ToolCatalogSnapshot {
  schema_version: "1.0";
  captured_at: string;
  server: ServerIdentity;
  tools: ToolContract[];
}

export interface CatalogBenchmarkReport {
  schema_version: "1.0";
  generated_at: string;
  environment: { python: string; platform: string; processor: string };
  config: { sizes: number[]; trials: number; warmups: number };
  results: Array<{
    tool_count: number;
    controlled_changes: number;
    fingerprint: { median_ms: number; p95_ms: number };
    analysis: { median_ms: number; p95_ms: number };
    fingerprint_tools_per_second: number;
    snapshot_bytes: number;
    report_bytes: number;
    findings: number;
    risk_score: number;
  }>;
}

export type Artifact =
  | { kind: "analysis"; data: AnalysisReport }
  | { kind: "scenario"; data: ScenarioReport }
  | { kind: "trace"; data: ExecutionTrace }
  | { kind: "snapshot"; data: ToolCatalogSnapshot }
  | { kind: "benchmark"; data: CatalogBenchmarkReport };
