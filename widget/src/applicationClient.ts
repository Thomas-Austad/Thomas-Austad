import {
  applicationApprovalInputSchema,
  candidateIdSchema,
  applicationIdSchema,
  applicationPackageSchema,
  jobIdSchema,
  screeningAnswerInputSchema,
  type ApplicationApprovalInput,
  type ApplicationPackage,
  type ScreeningAnswerInput
} from "./contracts";

export interface ApplicationToolClient {
  callTool(
    name: "prepare_job_application" | "get_application_review" | "resolve_application_screening_answer" | "approve_prepared_application_review",
    args: Record<string, unknown>
  ): Promise<unknown>;
}

export async function prepareApplicationPackage(
  client: ApplicationToolClient,
  candidateId: string,
  jobId: string
): Promise<ApplicationPackage> {
  return applicationPackageSchema.parse(
    await client.callTool("prepare_job_application", {
      candidate_id: candidateIdSchema.parse(candidateId),
      job_id: jobIdSchema.parse(jobId),
      screening_questions: []
    })
  );
}

export async function loadApplicationReview(
  client: ApplicationToolClient,
  applicationId: string
): Promise<ApplicationPackage> {
  return applicationPackageSchema.parse(
    await client.callTool("get_application_review", { application_id: applicationIdSchema.parse(applicationId) })
  );
}

export async function resolveScreeningAnswer(
  client: ApplicationToolClient,
  input: ScreeningAnswerInput
): Promise<ApplicationPackage> {
  const validated = screeningAnswerInputSchema.parse(input);
  return applicationPackageSchema.parse(
    await client.callTool("resolve_application_screening_answer", {
      ...validated,
      confirmed_by_user: true
    })
  );
}

export async function approveApplication(
  client: ApplicationToolClient,
  input: ApplicationApprovalInput
): Promise<ApplicationPackage> {
  const validated = applicationApprovalInputSchema.parse(input);
  return applicationPackageSchema.parse(
    await client.callTool("approve_prepared_application_review", {
      ...validated,
      confirmed_by_user: true
    })
  );
}
