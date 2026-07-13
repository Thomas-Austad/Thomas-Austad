import { describe, expect, it } from "vitest";

import { profileCreationFailureMessage } from "../src/browser/profileCreation";

describe("profileCreationFailureMessage", () => {
  it("gives a non-sensitive recovery message for an unavailable local model service", () => {
    expect(profileCreationFailureMessage(503)).toContain("local model service");
  });

  it("distinguishes invalid model output from an unavailable local runtime", () => {
    expect(profileCreationFailureMessage(502)).toContain("invalid local model response");
    expect(profileCreationFailureMessage(502)).toContain("No profile was created");
  });

  it("does not expose server details for unexpected failures", () => {
    expect(profileCreationFailureMessage(500)).toBe("Your profile could not be created. Your text is still here so you can try again.");
  });
});
