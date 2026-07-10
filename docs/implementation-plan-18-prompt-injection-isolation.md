# Issue 18 implementation plan: prompt-injection isolation

## Scope

Add a shared prompt-safety helper and update model-backed agents to label and
delimit untrusted candidate, job, and screening-question content before sending
it to the model.

## Trust boundaries

- Resume text, LinkedIn text, preferences, job descriptions, job raw payloads,
  and screening questions are untrusted data.
- Candidate/profile/job schema shape and approval state are application state,
  but free-text fields inside those objects can still contain untrusted content.
- Model output is not approval. Application preparation remains separate from
  approval and submission.

## Implementation steps

1. Add helper functions for trusted JSON context, untrusted content blocks, and
   prompt-injection signal detection.
2. Update profile, match, compensation, and application agents to use those
   helpers and reinforce the system prompt boundary.
3. Keep existing sensitive-screening post-processing as an invariant check after
   schema parsing.
4. Add tests proving prompt-injection strings are delimited as data and do not
   remove screening guardrails.

## Validation

- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest`
