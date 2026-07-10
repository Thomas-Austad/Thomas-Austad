# Issue 15 implementation plan: persistence schema hardening

## Scope

Strengthen repository metadata, SQL schema, and migrations for required lookup
columns, foreign keys, status constraints, and common indexes.

## Trust boundaries

- Persisted profiles, evidence, jobs, matches, and application packages may
  contain sensitive candidate data or untrusted provider content.
- Database constraints must reduce orphaned records and invalid state, but they
  do not replace the future authentication and authorization layer.
- This change must not store secrets or introduce new free-form secret storage.

## Implementation steps

1. Align SQLAlchemy metadata with existing PostgreSQL schema ownership columns.
2. Require repository lookup/payload columns that the application depends on.
3. Add foreign keys, check constraints, and indexes for profile, evidence, job,
   match, and application relationships.
4. Add a forward migration with explicit preflight checks before applying
   `NOT NULL` constraints to existing nullable columns.
5. Add repository tests for orphan rejection, invalid status constraints, and
   transactional rollback.

## Validation

- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest`
- `.venv\Scripts\python.exe -m alembic upgrade head --sql`
