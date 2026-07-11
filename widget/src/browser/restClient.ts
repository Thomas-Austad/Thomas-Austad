import type { ApplicationToolClient } from "../applicationClient";
import type { JobToolClient } from "../jobClient";
import type { ProfileToolClient } from "../profileClient";

type ToolName = Parameters<ApplicationToolClient["callTool"]>[0] | Parameters<JobToolClient["callTool"]>[0] | Parameters<ProfileToolClient["callTool"]>[0];

export class RestToolClient implements ApplicationToolClient, JobToolClient, ProfileToolClient {
  constructor(private readonly csrfToken: string) {}

  async callTool(name: ToolName, args: Record<string, unknown>): Promise<unknown> {
    const request = this.toRequest(name, args);
    const headers: Record<string, string> = request.method === "GET" ? {} : {
      "Content-Type": "application/json",
      "X-CSRF-Token": this.csrfToken
    };
    if (name === "correct_candidate_profile" || name === "approve_prepared_application_review") {
      headers["X-User-Confirmed"] = "true";
    }
    const response = await fetch(request.path, {
      method: request.method,
      credentials: "same-origin",
      headers,
      body: request.body === undefined ? undefined : JSON.stringify(request.body)
    });
    if (!response.ok) throw new Error("The requested local action could not be completed.");
    return response.json();
  }

  private toRequest(name: ToolName, args: Record<string, unknown>): { method: "GET" | "PATCH" | "POST"; path: string; body?: unknown } {
    const candidateId = String(args.candidate_id ?? "");
    const applicationId = String(args.application_id ?? "");
    switch (name) {
      case "review_candidate_profile": return { method: "GET", path: `/profiles/${encodeURIComponent(candidateId)}/review` };
      case "correct_candidate_profile": return { method: "PATCH", path: `/profiles/${encodeURIComponent(candidateId)}`, body: args.corrections };
      case "find_jobs": return { method: "POST", path: "/jobs/search", body: args };
      case "evaluate_job_match": return { method: "POST", path: `/matches/${encodeURIComponent(candidateId)}/${encodeURIComponent(String(args.job_id ?? ""))}` };
      case "estimate_market_compensation": {
        const params = new URLSearchParams({ role_family: String(args.role_family ?? ""), geography: String(args.geography ?? "") });
        return { method: "POST", path: `/compensation/${encodeURIComponent(candidateId)}?${params.toString()}` };
      }
      case "prepare_job_application": return { method: "POST", path: "/applications/prepare", body: args };
      case "get_application_review": return { method: "GET", path: `/applications/${encodeURIComponent(applicationId)}` };
      case "get_browser_handoff_preview": return { method: "GET", path: `/applications/${encodeURIComponent(applicationId)}/browser-handoff` };
      case "begin_browser_handoff": return { method: "POST", path: `/applications/${encodeURIComponent(applicationId)}/browser-handoff`, body: args };
      case "resolve_application_screening_answer": return { method: "POST", path: `/applications/${encodeURIComponent(applicationId)}/screening-questions/resolve`, body: args };
      case "approve_prepared_application_review": return { method: "POST", path: `/applications/${encodeURIComponent(applicationId)}/approve`, body: args };
    }
  }
}
