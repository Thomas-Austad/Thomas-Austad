import { describe, expect, it } from "vitest";

import { localModelReadinessFailureMessage } from "../src/browser/localModelReadiness";

describe("localModelReadinessFailureMessage", () => {
  it("gives a safe unavailable state without claiming a completed operation", () => {
    const message = localModelReadinessFailureMessage();

    expect(message).toContain("Start Ollama");
    expect(message).toContain("qwen3:8b");
    expect(message).toContain("No profile or application was created.");
  });
});
