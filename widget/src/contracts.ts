import { z } from "zod";

export const routeSchema = z.enum(["profile", "jobs", "applications"]);
export type Route = z.infer<typeof routeSchema>;

export const allowedToolNameSchema = z.enum([
  "review_candidate_profile",
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
