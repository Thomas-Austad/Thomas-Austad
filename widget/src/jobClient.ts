import {
  compensationEstimateSchema,
  jobMatchSchema,
  jobSearchInputSchema,
  jobSearchResultSchema,
  type CompensationEstimate,
  type JobMatch,
  type JobSearchInput,
  type JobSearchResult
} from "./contracts";

export interface JobToolClient {
  callTool(
    name: "find_jobs" | "evaluate_job_match" | "estimate_market_compensation",
    args: Record<string, unknown>
  ): Promise<unknown>;
}

export async function searchJobs(client: JobToolClient, input: JobSearchInput): Promise<JobSearchResult> {
  const validated = jobSearchInputSchema.parse(input);
  return jobSearchResultSchema.parse(await client.callTool("find_jobs", validated));
}

export async function loadJobMatch(client: JobToolClient, candidateId: string, jobId: string): Promise<JobMatch> {
  return jobMatchSchema.parse(
    await client.callTool("evaluate_job_match", { candidate_id: candidateId.trim(), job_id: jobId })
  );
}

export async function loadCompensation(
  client: JobToolClient,
  candidateId: string,
  roleFamily: string,
  geography: string
): Promise<CompensationEstimate> {
  return compensationEstimateSchema.parse(
    await client.callTool("estimate_market_compensation", {
      candidate_id: candidateId.trim(),
      role_family: roleFamily.trim(),
      geography: geography.trim()
    })
  );
}
