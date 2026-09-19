import { canonicalJson, sha256 } from "./integrity";
import type { ServerIdentity, ToolCatalogSnapshot } from "./types";

const STORAGE_KEY = "mcp-traceguard.approvals.v1";
const MAX_APPROVALS = 10;

export interface BaselineApproval {
  snapshot_hash: string;
  approved_at: string;
  note: string;
  source_name: string;
  server: ServerIdentity;
  tool_count: number;
  snapshot: ToolCatalogSnapshot;
}

export function loadApprovals(
  storage: Storage = localStorage,
): BaselineApproval[] {
  try {
    const value = JSON.parse(storage.getItem(STORAGE_KEY) ?? "[]") as unknown;
    return Array.isArray(value) ? (value as BaselineApproval[]) : [];
  } catch {
    return [];
  }
}

export async function approveSnapshot(
  snapshot: ToolCatalogSnapshot,
  sourceName: string,
  note: string,
  storage: Storage = localStorage,
): Promise<BaselineApproval> {
  const approval: BaselineApproval = {
    snapshot_hash: await sha256(canonicalJson(snapshot)),
    approved_at: new Date().toISOString(),
    note: note.trim(),
    source_name: sourceName,
    server: snapshot.server,
    tool_count: snapshot.tools.length,
    snapshot,
  };
  const approvals = [approval, ...loadApprovals(storage)].slice(
    0,
    MAX_APPROVALS,
  );
  storage.setItem(STORAGE_KEY, JSON.stringify(approvals));
  return approval;
}

export function clearApprovals(storage: Storage = localStorage): void {
  storage.removeItem(STORAGE_KEY);
}

export function approvalReceipt(
  approval: BaselineApproval,
): Record<string, unknown> {
  return {
    schema_version: "1.0",
    kind: "mcp-traceguard-baseline-approval",
    snapshot_hash: approval.snapshot_hash,
    approved_at: approval.approved_at,
    note: approval.note,
    source_name: approval.source_name,
    server: approval.server,
    tool_count: approval.tool_count,
  };
}
