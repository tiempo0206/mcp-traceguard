import { describe, expect, it } from "vitest";

import { escapeHtml, renderAnalysis } from "./render";
import type { AnalysisReport } from "./types";

describe("rendering", () => {
  it("escapes imported text", () => {
    expect(escapeHtml('<script>alert("x")</script>')).not.toContain("<script>");
  });

  it("renders explainable change paths", () => {
    const report: AnalysisReport = {
      schema_version: "1.0",
      generated_at: "2026-09-18T00:00:00Z",
      current_captured_at: "2026-09-18T00:00:00Z",
      baseline_captured_at: null,
      passed: false,
      fail_on: "error",
      summary: { errors: 1, warnings: 0, total: 1 },
      risk: { score: 3, rating: "low", contributions: [] },
      findings: [
        {
          rule_id: "TG103",
          severity: "error",
          message: "changed",
          tool: "read_note",
          details: {
            changes: [
              {
                path: "/description",
                impact: "metadata",
                explanation: "Tool description changed",
                before: "old",
                after: "new",
              },
            ],
          },
        },
      ],
    };
    expect(renderAnalysis(report)).toContain("/description");
    expect(renderAnalysis(report)).toContain("metadata");
  });
});
