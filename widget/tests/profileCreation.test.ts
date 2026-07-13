import { describe, expect, it } from "vitest";

import { profileCreationFailureMessage } from "../src/browser/profileCreation";

describe("profileCreationFailureMessage", () => {
  it("gives a non-sensitive recovery message for an unavailable profile service", () => {
    expect(profileCreationFailureMessage(503)).toContain("local model service");
  });

  it("does not expose server details for unexpected failures", () => {
    expect(profileCreationFailureMessage(500)).toBe("Your profile could not be created. Your text is still here so you can try again.");
  });
});
