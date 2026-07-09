## Context and motivation
The platform depends heavily on model behavior, but it currently lacks a regression harness to tell us when profile generation, matching, compensation, or application drafting has drifted.

## Acceptance criteria
- Representative candidate/job fixtures exist for key scenarios.
- Evals cover strong fit, weak fit, missing evidence, over-level, and salary mismatch cases.
- Core behavioral invariants are asserted without relying on exact prose.
- Evals can run locally and in CI.

## Relevant files or components
- `app/agents/`
- `app/services/openai_service.py`
- `tests/`
- future eval harness files under `tests/` or `docs/`

## Dependencies or blockers
- Can begin before the full UI exists.
- Benefits from stable schemas and deterministic business-rule boundaries.

## Security considerations
- Use only synthetic candidate and job data in fixtures.
- Avoid storing sensitive prompt contents unnecessarily in eval output.

## Testing considerations
- Add a repeatable test/eval command for CI.
- Verify that safety invariants remain true even when model wording varies.
