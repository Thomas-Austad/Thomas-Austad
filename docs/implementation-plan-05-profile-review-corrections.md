# Issue 5 implementation plan: profile review and corrections

## Scope

Add a local, authenticated API workflow for reviewing a stored candidate profile,
its source-backed evidence, and its user-provided corrections. Corrections are
persisted as immutable field-level records and merged into the canonical profile
used by matching, compensation, and application preparation.

## Trust boundaries and data

- Candidate profiles, evidence excerpts, and correction values are sensitive
  local personal data.
- The local bearer credential establishes the sole local user; no caller can
  select a different owner.
- A correction is user-provided data, never evidence for an inferred claim.
- Profile review and correction are local state changes only; they do not submit
  applications or answer screening questions.
- Audit events identify the action and target without including profile or
  correction content.

## Implementation steps

1. Define bounded correction and review response schemas, including explicit
   field provenance and immutable correction records.
2. Add a migration and repository support for correction records; preserve
   existing source evidence when a canonical profile is updated.
3. Add authenticated profile-review and correction endpoints plus local stdio
   MCP tools. Require the target profile to exist, reject an empty correction,
   require direct confirmation for the MCP write tool, and record a
   non-sensitive audit receipt before reporting success.
4. Ensure downstream profile consumers continue to read the canonical, corrected
   profile without any interface change.
5. Add repository and API tests for durable corrections, provenance, downstream
   use, validation failures, and audit-write rollback.

## Validation

- Focused repository and API workflow tests.
- `python -m ruff check .`
- `python -m pytest`
- `.venv\Scripts\python.exe -m alembic upgrade head --sql` when the local
  environment is available.

## MCP tool contracts

### `review_candidate_profile`

- **Effect:** Read-only. Returns the canonical profile, source evidence, and
  correction history for one candidate ID.
- **Authorization and data:** Local stdio only; the launching local operating
  system user is the sole principal. It reads that user's profile and evidence.
- **Approval, idempotency, and audit:** No approval or audit event is required;
  repeated calls have no effect.
- **Errors and retry:** Returns a safe not-found error for an unknown profile;
  retry is safe after transient local storage failures.

### `correct_candidate_profile`

- **Effect:** Write-capable. Saves one or more typed, user-provided profile
  field replacements and returns the resulting review state.
- **Authorization and data:** Local stdio only; it changes the local user's
  profile and stores the correction values separately from source evidence.
- **Approval, idempotency, and audit:** Requires `confirmed_by_user=True`
  immediately before execution. Each accepted call records a non-sensitive
  `profile.correct` audit receipt; calls are not idempotent because each is a
  separate user correction record.
- **Errors and retry:** Rejects missing confirmation, malformed or empty
  corrections, and unknown profiles. Audit-write failures roll back the profile
  update and can be retried after local storage is available.
