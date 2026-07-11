import { z } from "zod";

export const routeSchema = z.enum(["profile", "jobs", "applications"]);
export type Route = z.infer<typeof routeSchema>;

export const allowedToolNameSchema = z.enum([
  "review_candidate_profile",
  "correct_candidate_profile",
  "find_jobs",
  "evaluate_job_match",
  "estimate_market_compensation",
  "prepare_job_application",
  "get_application_review",
  "get_browser_handoff_preview",
  "begin_browser_handoff",
  "resolve_application_screening_answer",
  "approve_prepared_application_review"
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
  provider_errors: z.array(z.object({ provider: z.enum(["ashby", "greenhouse", "lever"]) })).default([])
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
const publicBoardUrlSchema = z.string().url().max(2_000).refine((value) => {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && ["boards.greenhouse.io", "job-boards.greenhouse.io", "jobs.lever.co", "jobs.ashbyhq.com"].includes(url.hostname);
  } catch {
    return false;
  }
}, "Use a supported public careers-board link.");

export const jobSearchInputSchema = z.object({
  greenhouse_boards: sourceListSchema,
  lever_companies: sourceListSchema,
  ashby_job_boards: sourceListSchema,
  public_job_board_urls: z.array(publicBoardUrlSchema).max(25).default([]),
  title_keywords: z.array(z.string().trim().min(1).max(256)).max(20),
  company_keywords: z.array(z.string().trim().min(1).max(256)).max(20),
  location_keywords: z.array(z.string().trim().min(1).max(256)).max(20),
  remote_mode: z.enum(["remote", "hybrid", "onsite"]).optional(),
  minimum_salary: z.number().int().nonnegative().optional(),
  compensation_currency: z.string().regex(/^[A-Z]{3}$/).optional(),
  employment_types: z.array(z.string().trim().min(1).max(128)).max(10),
  freshness_days: z.number().int().min(1).max(365).optional()
}).superRefine((input, context) => {
  if (input.minimum_salary !== undefined && input.compensation_currency === undefined) {
    context.addIssue({ code: "custom", message: "Compensation currency is required with a minimum salary.", path: ["compensation_currency"] });
  }
});
export type JobSearchInput = z.infer<typeof jobSearchInputSchema>;

export const applicationPackageSchema = z.object({
  application_id: z.string().min(1),
  candidate_id: z.string().min(1),
  job_id: z.string().min(1),
  tailored_resume_markdown: z.string(),
  cover_letter: z.string(),
  factual_warnings: z.array(z.string()),
  requires_user_input: z.array(z.string()),
  unresolved_screening_questions: z.array(
    z.object({
      question: z.string().min(1),
      category: z.enum([
        "personal",
        "legal",
        "demographic",
        "disability",
        "criminal_history",
        "salary_history",
        "work_authorization"
      ]),
      reason: z.string()
    })
  ),
  confirmed_screening_answers: z.array(
    z.object({
      question: z.string().min(1),
      category: z.string().min(1),
      confirmed_at: z.string().min(1)
    })
  ),
  status: z.enum(["prepared", "approved", "submitted", "failed"])
});
export type ApplicationPackage = z.infer<typeof applicationPackageSchema>;

export const browserHandoffPreviewSchema = z.object({
  application_id: z.string().min(1),
  job_id: z.string().min(1),
  provider: z.enum(["ashby", "greenhouse", "lever"]),
  company: z.string().min(1),
  title: z.string().min(1),
  destination_url: z.string().url()
});
export type BrowserHandoffPreview = z.infer<typeof browserHandoffPreviewSchema>;

export const browserHandoffSchema = z.object({
  application_id: z.string().min(1),
  job_id: z.string().min(1),
  provider: z.enum(["ashby", "greenhouse", "lever"]),
  destination_url: z.string().url(),
  status: z.literal("ready"),
  request_id: z.string().uuid()
});
export type BrowserHandoff = z.infer<typeof browserHandoffSchema>;

export const applicationIdSchema = z.string().trim().min(1).max(128);
export const candidateIdSchema = z.string().trim().min(1).max(128);
export const jobIdSchema = z.string().trim().min(1).max(2_000);
export const screeningAnswerInputSchema = z.object({
  application_id: applicationIdSchema,
  question: z.string().trim().min(1).max(1_000),
  answer: z.string().trim().min(1).max(5_000),
  idempotency_key: z.string().uuid()
});
export type ScreeningAnswerInput = z.infer<typeof screeningAnswerInputSchema>;

export const applicationApprovalInputSchema = z.object({
  application_id: applicationIdSchema,
  idempotency_key: z.string().uuid()
});
export type ApplicationApprovalInput = z.infer<typeof applicationApprovalInputSchema>;

export const browserHandoffInputSchema = z.object({
  application_id: applicationIdSchema,
  expected_destination_url: z.string().url(),
  idempotency_key: z.string().uuid()
});
export type BrowserHandoffInput = z.infer<typeof browserHandoffInputSchema>;
