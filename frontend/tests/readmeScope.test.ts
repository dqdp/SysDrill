import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("frontend README scope", () => {
  it("documents the bounded mock shell and browser-local persistence boundary", () => {
    const readme = readFileSync(resolve(__dirname, "../README.md"), "utf-8");

    expect(readme).toContain("bounded mock");
    expect(readme).toContain("MockInterview / ReadinessCheck");
    expect(readme).toContain("browser-local");
    expect(readme).not.toContain("It does not implement learner dashboards, scenario/mock flows");
  });
});
