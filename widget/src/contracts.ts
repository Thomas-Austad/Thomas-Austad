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

const jobListingSchema = z.object({
  job_id: z.string().min(1),
  source: z.string().min(1),
  source_url: z.string().url(),
  company: z.string(),
  title: z.string(),
  location: z.string().nullable().optional(),
  remote_type: z.string().nullable().optional(),
  description: z.string(),
  salary_min: z.number().nullable().optional(),
  salary_max: z.number().nullable().optional(),
  currency: z.string(),
  employment_type: z.string().nullable().optional(),
  posted_at: z.string().nullable().optional(),
  active: z.boolean()
});
export type JobListing = z.infer<typeof jobListingSchema>;

export const jobSearchResultSchema = z.object({
  count: z.number().int().nonnegative(),
  jobs: z.array(jobListingSchema),
  provider_errors: z.array(z.object({ provider: z.enum(["greenhouse", "lever"]) })).default([])
});
export type JobSearchResult = z.infer<typeof jobSearchResultSchema>;

const scoreDetailSchema = z.object({ score: z.number().min(0).max(100), reasons: z.array(z.string()) });

export const jobMatchSchema = z.object({
  candidate_id: z.string().min(1),
  job_id: z.string().min(1),
  qualification_fit: scoreDetailSchema,
  evidence_strength: scoreDetailSchema,
  seniority_alignment: scoreDetailSchema,
  compensation_alignment: scoreDetailSchema,
  preference_fit: scoreDetailSchema,
  competitiveness: scoreDetailSchema,
  overall_score: z.number().min(0).max(100),
  hard_disqualifiers: z.array(z.string()),
  gaps: z.array(z.string()),
  recommendation: z.enum(["apply", "consider", "skip"])
});
export type JobMatch = z.infer<typeof jobMatchSchema>;

export const compensationEstimateSchema = z.object({
  role_family: z.string(),
  geography: z.string(),
  base_low: z.number().finite(),
  base_mid: z.number().finite(),
  base_high: z.number().finite(),
  total_comp_low: z.number().finite().nullable().optional(),
  total_comp_high: z.number().finite().nullable().optional(),
  confidence: z.number().min(0).max(1),
  rationale: z.array(z.string()),
  as_of: z.string().min(1)
});
export type CompensationEstimate = z.infer<typeof compensationEstimateSchema>;

const sourceListSchema = z.array(z.string().trim().min(1).max(256)).max(25);

export const jobSearchInputSchema = z.object({
  greenhouse_boards: sourceListSchema,
  lever_companies: sourceListSchema,
  title_keywords: z.array(z.string().trim().min(1).max(256)).max(20)
});
export type JobSearchInput = z.infer<typeof jobSearchInputSchema>;
