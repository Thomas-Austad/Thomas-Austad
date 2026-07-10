import { z } from "zod";

export const routeSchema = z.enum(["profile", "jobs", "applications"]);
export type Route = z.infer<typeof routeSchema>;

export const allowedToolNameSchema = z.enum([
  "review_candidate_profile",
  "correct_candidate_profile",
  "find_jobs",
  "evaluate_job_match",
  "estimate_market_compensation",
  "prepare_job_application"
]);
export type AllowedToolName = z.infer<typeof allowedToolNameSchema>;

export const toolArgumentsSchema = z.record(z.string(), z.unknown());

export const jsonRpcEnvelopeSchema = z
  .object({
    jsonrpc: z.literal("2.0"),
    id: z.number().int().nonnegative().optional(),
    method: z.string().min(1).optional(),
    params: z.unknown().optional(),
    result: z.unknown().optional(),
    error: z
      .object({
        code: z.number(),
        message: z.string().min(1),
        data: z.unknown().optional()
      })
      .optional()
  })
  .refine((value) => value.id !== undefined || value.method !== undefined, {
    message: "A JSON-RPC message needs an id or method."
  });

export type JsonRpcEnvelope = z.infer<typeof jsonRpcEnvelopeSchema>;

export const statusKindSchema = z.enum(["loading", "empty", "error", "ready"]);
export type StatusKind = z.infer<typeof statusKindSchema>;

const profileFieldSchema = z.enum(["name", "headline", "current_level"]);
export type EditableProfileField = z.infer<typeof profileFieldSchema>;

const evidenceRecordSchema = z.object({
  candidate_id: z.string().min(1),
  claim_type: z.enum(["skill", "experience", "ambiguity"]),
  claim_ref: z.string(),
  source: z.enum(["resume", "linkedin", "user", "job", "profile"]),
  text: z.string(),
  confidence: z.number().min(0).max(1),
  source_ref: z.string().nullable().optional()
});

const profileCorrectionRecordSchema = z.object({
  correction_id: z.string().min(1),
  candidate_id: z.string().min(1),
  field: z.string().min(1),
  value: z.unknown(),
  corrected_at: z.string().min(1)
});

export const profileReviewSchema = z.object({
  profile: z.object({
    candidate_id: z.string().min(1),
    name: z.string().nullable(),
    headline: z.string(),
    current_level: z.string(),
    primary_functions: z.array(z.string()),
    skills: z.array(
      z.object({
        name: z.string(),
        proficiency: z.number().min(0).max(1),
        years: z.number().nonnegative().nullable().optional()
      })
    ),
    experience: z.array(
      z.object({
        employer: z.string(),
        title: z.string(),
        start_date: z.string().nullable().optional(),
        end_date: z.string().nullable().optional(),
        achievements: z.array(z.string())
      })
    ),
    education: z.array(z.string()),
    certifications: z.array(z.string()),
    ambiguities: z.array(z.string()),
    generated_at: z.string().min(1)
  }),
  evidence: z.array(evidenceRecordSchema),
  corrections: z.array(profileCorrectionRecordSchema)
});
export type ProfileReview = z.infer<typeof profileReviewSchema>;

export const profileCorrectionInputSchema = z.object({
  candidate_id: z.string().trim().min(1).max(128),
  field: profileFieldSchema,
  value: z.string().trim().min(1).max(2_000)
});
export type ProfileCorrectionInput = z.infer<typeof profileCorrectionInputSchema>;
