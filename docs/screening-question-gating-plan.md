# Screening Question Gating Execution Plan

## Scope

Address issue #6 with deterministic server-side safeguards for sensitive
screening questions during application preparation and approval.

## Trust Boundaries And Data Touched

- Screening questions are untrusted user or job-provider text.
- Candidate profiles, generated applications, screening answers, and unresolved
  inputs can contain sensitive data.
- The classifier will inspect question text only and persist only non-sensitive
  approval audit metadata.
- Generated draft content from the model remains untrusted until validated by
  application code.

## External Effects And Approvals

- No external submission, messaging, purchase, deletion, or job-board action is
  introduced.
- Preparing an application remains separate from approving an application.
- Approval remains blocked while sensitive or unresolved screening questions
  require direct user input.
- The approval endpoint records a local audit receipt only after approval
  succeeds.

## Implementation Steps

1. Add deterministic screening question classification for personal, legal,
   demographic, disability, criminal-history, salary-history, and
   work-authorization questions.
2. Ensure sensitive questions are removed from generated screening answers and
   added to review-visible unresolved inputs.
3. Add structured review metadata to application packages so callers can show
   unresolved sensitive questions clearly.
4. Persist non-sensitive approval audit records with timestamp, action, target,
   result, and request ID metadata.
5. Add focused tests proving sensitive questions cannot be guessed or approved
   without resolution.

## Validation

- `python -m ruff check .`
- `python -m pytest`

