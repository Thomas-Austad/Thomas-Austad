# Postgres Repositories Plan

## Scope

Implement issue #1 by replacing the runtime in-memory store with SQLAlchemy
repository mappings backed by PostgreSQL tables while preserving the existing
FastAPI and MCP behavior.

## Trust Boundaries and Data

- Candidate profiles, job listings, matches, and application packages can
  contain sensitive personal data or untrusted job content.
- Repository code must not log stored payloads or expose database credentials.
- This change stores existing API payloads but does not change approval,
  submission, authorization, candidate-claim generation, deletion, retention, or
  audit semantics.

## Implementation Steps

1. Add SQLAlchemy table metadata and repository-backed mapping classes for
   profiles, jobs, matches, and applications.
2. Add a migration that bridges API string identifiers to the existing UUID
   schema and stores complete model payloads as JSON.
3. Keep test runs isolated from external services with an explicit test-mode
   in-memory store, while adding repository unit tests against a transient
   SQLAlchemy engine.
4. Update schema reference documentation where it would otherwise drift.

## Validation

- `ruff check .`
- `pytest`
- Alembic offline migration generation
