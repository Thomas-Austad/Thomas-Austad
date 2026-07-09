# Agent Regression Evals Plan

## Scope

Implement issue #7 with a local pytest-based regression harness using synthetic
candidate and job fixtures.

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

## Validation

- `ruff check .`
- `pytest`
