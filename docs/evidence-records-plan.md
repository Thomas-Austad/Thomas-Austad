# Evidence Records Plan

## Scope

Implement issue #4 by persisting source evidence records for profile claims when
candidate profiles are saved through the repository layer.

## Trust Boundaries and Data

- Evidence excerpts can contain sensitive personal data from resumes, LinkedIn
  exports, or user-provided text.
- Evidence records are stored for traceability and must not be logged or exposed
  through errors.
- This change records evidence already present in structured profile output; it
  does not add new model claims or infer facts.

## Implementation Steps

1. Add an evidence record schema that preserves source type, source reference,
   excerpt, confidence, claim type, and claim reference.
2. Extend the repository metadata and migrations so `career_evidence` can tie
   snippets back to specific extracted skills or other supported claim types.
3. Save skill evidence records in the same transaction as profile upserts and
   replace stale evidence for updated profiles.
4. Expose repository access for downstream code to read evidence by candidate.
5. Add tests for persistence, replacement on update, and low-confidence evidence
   preservation.

## Validation

- `ruff check .`
- `pytest`
- Alembic offline migration generation
