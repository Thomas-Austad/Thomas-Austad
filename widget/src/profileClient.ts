import {
  profileCorrectionInputSchema,
  profileReviewSchema,
  type ProfileCorrectionInput,
  type ProfileReview
} from "./contracts";

export interface ProfileToolClient {
  callTool(name: "review_candidate_profile" | "correct_candidate_profile", args: Record<string, unknown>): Promise<unknown>;
}

export async function loadProfileReview(client: ProfileToolClient, candidateId: string): Promise<ProfileReview> {
  return profileReviewSchema.parse(
    await client.callTool("review_candidate_profile", { candidate_id: candidateId.trim() })
  );
}

export async function saveProfileCorrection(
  client: ProfileToolClient,
  correction: ProfileCorrectionInput
): Promise<ProfileReview> {
  const input = profileCorrectionInputSchema.parse(correction);
  return profileReviewSchema.parse(
    await client.callTool("correct_candidate_profile", {
      candidate_id: input.candidate_id,
      corrections: { [input.field]: input.value },
      confirmed_by_user: true
    })
  );
}
