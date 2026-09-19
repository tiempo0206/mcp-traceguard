import type { ExecutionTrace, Json, TraceEvent } from "./types";

function normalize(value: unknown): Json {
  if (
    value === null ||
    typeof value === "boolean" ||
    typeof value === "number"
  ) {
    return value;
  }
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map(normalize);
  }
  if (typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .filter(([, child]) => child !== undefined)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, child]) => [key, normalize(child)]),
    );
  }
  throw new Error(`Cannot canonicalize ${typeof value}`);
}

export function canonicalJson(value: unknown): string {
  return JSON.stringify(normalize(value));
}

export async function sha256(text: string): Promise<string> {
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

function eventBody(event: TraceEvent): Record<string, unknown> {
  return {
    sequence: event.sequence,
    timestamp: event.timestamp,
    event_type: event.event_type,
    tool: event.tool,
    payload: event.payload,
  };
}

export async function verifyTrace(trace: ExecutionTrace): Promise<string[]> {
  const errors: string[] = [];
  let previous = "0".repeat(64);
  for (const [index, event] of trace.events.entries()) {
    if (event.sequence !== index)
      errors.push(`event ${index}: sequence mismatch`);
    if (event.previous_hash !== previous)
      errors.push(`event ${index}: previous hash mismatch`);
    const expected = await sha256(
      `${event.previous_hash}:${canonicalJson(eventBody(event))}`,
    );
    if (event.event_hash !== expected)
      errors.push(`event ${index}: content hash mismatch`);
    previous = event.event_hash;
  }
  if (trace.summary.event_count !== trace.events.length) {
    errors.push("summary event count mismatch");
  }
  const seal = {
    schema_version: "1.0",
    trace_id: trace.trace_id,
    started_at: trace.started_at,
    completed_at: trace.completed_at,
    server: trace.server,
    tool: trace.tool,
    integrity: trace.integrity,
    event_root: trace.events.at(-1)?.event_hash ?? "0".repeat(64),
    summary: trace.summary,
  };
  if (trace.trace_hash !== (await sha256(canonicalJson(seal)))) {
    errors.push("final trace seal mismatch");
  }
  return errors;
}
