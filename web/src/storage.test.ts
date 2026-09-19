import { describe, expect, it } from "vitest";

import {
  approvalReceipt,
  approveSnapshot,
  clearApprovals,
  loadApprovals,
} from "./storage";
import type { ToolCatalogSnapshot } from "./types";

class MemoryStorage implements Storage {
  private readonly values = new Map<string, string>();

  get length(): number {
    return this.values.size;
  }

  clear(): void {
    this.values.clear();
  }

  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  key(index: number): string | null {
    return [...this.values.keys()][index] ?? null;
  }

  removeItem(key: string): void {
    this.values.delete(key);
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }
}

const snapshot: ToolCatalogSnapshot = {
  schema_version: "1.0",
  captured_at: "2026-09-18T00:00:00Z",
  server: { name: "demo", version: "1", protocol_version: "2026-07-28" },
  tools: [],
};

describe("baseline approvals", () => {
  it("stores a hash-bound receipt locally", async () => {
    const storage = new MemoryStorage();
    const approval = await approveSnapshot(
      snapshot,
      "demo.json",
      "reviewed",
      storage,
    );
    expect(approval.snapshot_hash).toHaveLength(64);
    expect(loadApprovals(storage)).toHaveLength(1);
    expect(approvalReceipt(approval)).toMatchObject({
      kind: "mcp-traceguard-baseline-approval",
      snapshot_hash: approval.snapshot_hash,
      tool_count: 0,
    });
    clearApprovals(storage);
    expect(loadApprovals(storage)).toEqual([]);
  });
});
