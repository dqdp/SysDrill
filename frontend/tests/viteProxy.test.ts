import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("vite proxy config", () => {
  it("proxies recommendation requests to the backend in local dev", () => {
    const configSource = readFileSync(resolve(__dirname, "../vite.config.ts"), "utf-8");

    expect(configSource).toContain('"/recommendations": "http://127.0.0.1:8000"');
  });
});
