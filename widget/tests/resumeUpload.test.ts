import { describe, expect, it, vi } from "vitest";

import { extractResumeFromFile } from "../src/browser/resumeUpload";

describe("extractResumeFromFile", () => {
  it("uploads a file with browser-session CSRF protection and validates extracted text", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        filename: "resume.docx",
        content_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        text: "Avery Example\nBuilt safe systems.",
        character_count: 33
      })
    });
    vi.stubGlobal("fetch", fetchMock);

    const text = await extractResumeFromFile(new File(["synthetic"], "resume.docx"), "csrf-token");

    expect(text).toContain("Avery Example");
    expect(fetchMock).toHaveBeenCalledWith("/resumes/extract", expect.objectContaining({
      method: "POST",
      headers: { "X-CSRF-Token": "csrf-token" }
    }));
  });

  it("rejects malformed extraction responses instead of treating them as resume text", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ text: 42 }) }));

    await expect(extractResumeFromFile(new File(["synthetic"], "resume.docx"), "csrf-token")).rejects.toThrow();
  });
});
