# Agent Regression Evals Plan

## Scope

Implement issue #7 with a local pytest-based regression harness using synthetic
candidate and job fixtures. Issue #33 extends that harness to qualify the
configured local model without collecting candidate data or model transcripts.

## Trust Boundaries and Data

- Evals must use synthetic candidate and job data only.
- Eval assertions should avoid exact LLM prose and focus on schemas,
  recommendations, score ranges, evidence links, disqualifiers, and safety
  invariants.
- Eval output must not store private prompts, resumes, or provider payloads.

## Implementation Steps

1. Add representative synthetic cases for strong fit, weak fit, missing
   evidence, over-level, and salary mismatch scenarios.
2. Define reusable invariant assertions that validate match outputs without
   depending on exact wording.
3. Add a pytest marker and tests so the harness runs locally and in CI with the
   normal test suite.
4. Document the eval command for developers.

## Issue #33 local-model qualification

### Scope and trust boundaries

The qualification suite exercises profile extraction, job matching,
compensation, and application preparation with synthetic inputs and mocked
provider replies. Resumes, jobs, screening questions, model output, and
runtime errors are untrusted. The suite must prove that provider failures do
not bypass evidence requirements, prompt-injection isolation, sensitive
screening review, or the separation between preparation and approval.

### Implementation steps

1. Add synthetic cross-agent cases that assert schema routing, evidence-linked
   profile output, conservative match recommendations, compensation bounds,
   and prepared-only application state.
2. Cover malformed and partial provider replies, overload and unavailable
   runtime failures, bounded retries, and replayed preparation requests using
   test doubles only.
3. Include prompt-injection strings in synthetic resume and job inputs, and
   verify that the typed service contract and deterministic screening guard
   retain control of approval-related state.
4. Add an opt-in loopback-only smoke test and a manual protocol. It may use
   only the configured local runtime and synthetic inputs, and must not record
   prompts, responses, resumes, or model payloads.
5. Record the exact runtime/model configuration and measured host capability
   only after the smoke test passes. Do not represent untested hardware or
   model variants as qualified.

### Qualification gates

- A test failure, malformed schema output, evidence-policy failure, unsafe
  screening result, or non-prepared application state fails qualification.
- The local smoke test is opt-in and requires `MODEL_PROVIDER=ollama`, a
  loopback-only `LOCAL_MODEL_BASE_URL`, and the selected installed model.
- Model/version, quantization, context setting, and host hardware are recorded
  as a qualified configuration only with an aggregate pass/fail result.
- No remote fallback, production data, raw prompts, raw model responses, or
  benchmark artifacts may be retained by the test suite.

## Validation

- `ruff check .`
- `pytest`
- `pytest -m eval`
