import { extractedResumeSchema } from "../contracts";

export async function extractResumeFromFile(file: File, csrfToken: string): Promise<string> {
  const formData = new FormData();
  formData.append("file", file, file.name);
  const response = await fetch("/resumes/extract", {
    method: "POST",
    credentials: "same-origin",
    headers: { "X-CSRF-Token": csrfToken },
    body: formData
  });
  if (!response.ok) throw new Error("Resume extraction failed");
  return extractedResumeSchema.parse(await response.json()).text;
}
