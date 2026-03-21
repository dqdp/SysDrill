import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("vite proxy config", () => {
  it("proxies the launcher backend surface in local dev", () => {
    const configSource = readFileSync(resolve(__dirname, "../vite.config.ts"), "utf-8");

    expect(configSource).toContain('"/content": "http://127.0.0.1:8000"');
    expect(configSource).toContain('"/learner": "http://127.0.0.1:8000"');
    expect(configSource).toContain('"/recommendations": "http://127.0.0.1:8000"');
    expect(configSource).toContain('"/runtime": "http://127.0.0.1:8000"');
    expect(configSource).toContain('"/health": "http://127.0.0.1:8000"');
  });
});
