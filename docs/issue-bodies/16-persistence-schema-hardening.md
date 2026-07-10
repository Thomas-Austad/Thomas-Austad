## Context and motivation
The repository layer and migrations now provide durable storage, but the production data model still needs stronger integrity rules before real candidate data is trusted to it. Several migration-added columns are nullable, ownership fields are not yet enforced by repositories, and status/state constraints are mostly application conventions.

## Acceptance criteria
- Required repository lookup and payload columns are migrated to `NOT NULL` where the domain requires them.
- Foreign keys, uniqueness, indexes, and status `CHECK` constraints reflect legal application states and common lookup paths.
- Candidate/profile/application records are ownership-ready for object-level authorization.
- Multi-record writes that update profiles and evidence are transactional and tested.
- Schema definitions, migrations, and repository metadata stay aligned.

## Relevant files or components
- `app/repositories.py`
- `migrations/versions/`
- `sql/schema.sql`
- `app/models/schemas.py`
- `tests/test_repositories.py`

## Dependencies or blockers
- Should be coordinated with authentication/authorization work.
- Requires a careful migration path for any existing development data.

## Security considerations
- Strong database constraints reduce the chance of cross-user access, orphaned sensitive data, inconsistent approvals, and silent data corruption.
- Do not store secrets in JSONB/free-form metadata while hardening the schema.

## Testing considerations
- Add migration and repository tests for constraint violations, missing ownership, invalid statuses, duplicate keys, and transactional rollback.
- Include negative tests for malformed or boundary-size payloads.
