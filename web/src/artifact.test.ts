import { describe, expect, it } from "vitest";

import { parseArtifact, parseArtifactJson } from "./artifact";

describe("artifact parsing", () => {
  it("detects an analysis report", () => {
    const artifact = parseArtifact({
      schema_version: "1.0",
      findings: [],
      risk: {},
      summary: {},
    });
    expect(artifact.kind).toBe("analysis");
  });

  it("rejects an unknown version", () => {
    expect(() =>
      parseArtifact({ schema_version: "2.0", findings: [] }),
    ).toThrow("schema_version of 1.0");
  });

  it("reports invalid JSON", () => {
    expect(() => parseArtifactJson("{broken")).toThrow("Invalid JSON");
  });
});
