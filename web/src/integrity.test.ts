import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";

import { canonicalJson, sha256, verifyTrace } from "./integrity";
import type { ExecutionTrace, TraceEvent } from "./types";

async function validTrace(): Promise<ExecutionTrace> {
  const body = {
    sequence: 0,
    timestamp: "2026-09-18T00:00:00Z",
    event_type: "decision" as const,
    tool: "read_profile",
    payload: { outcome: "allow" },
  };
  const event: TraceEvent = {
    ...body,
    previous_hash: "0".repeat(64),
    event_hash: await sha256(`${"0".repeat(64)}:${canonicalJson(body)}`),
  };
  const trace = {
    schema_version: "1.0" as const,
    trace_id: "trace-1",
    started_at: "2026-09-18T00:00:00Z",
    completed_at: "2026-09-18T00:00:01Z",
    server: { name: "demo", version: "1", protocol_version: "2026-07-28" },
    tool: "read_profile",
    integrity: "sha256-chain-v1" as const,
    events: [event],
    summary: {
      outcome: "allow" as const,
      call_executed: true,
      response_is_error: false,
      redaction_count: 0,
      event_count: 1,
      duration_ms: 1,
    },
    trace_hash: "",
  };
  const seal = {
    schema_version: "1.0",
    trace_id: trace.trace_id,
    started_at: trace.started_at,
    completed_at: trace.completed_at,
    server: trace.server,
    tool: trace.tool,
    integrity: trace.integrity,
    event_root: event.event_hash,
    summary: trace.summary,
  };
  trace.trace_hash = await sha256(canonicalJson(seal));
  return trace;
}

describe("trace integrity", () => {
  it("canonicalizes object key order", () => {
    expect(canonicalJson({ b: 2, a: 1 })).toBe(canonicalJson({ a: 1, b: 2 }));
  });

  it("verifies the chain and final seal", async () => {
    expect(await verifyTrace(await validTrace())).toEqual([]);
  });

  it("detects event tampering", async () => {
    const trace = await validTrace();
    trace.events[0]!.payload.outcome = "deny";
    expect(await verifyTrace(trace)).toContain(
      "event 0: content hash mismatch",
    );
  });

  it("verifies a trace sealed by the Python implementation", async () => {
    const path = new URL("../public/demo/profile.trace.json", import.meta.url);
    const trace = JSON.parse(await readFile(path, "utf8")) as ExecutionTrace;
    expect(await verifyTrace(trace)).toEqual([]);
  });
});
