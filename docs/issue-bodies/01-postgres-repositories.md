## Context and motivation
The application currently stores profiles, jobs, matches, and applications in `app/store.py` using in-memory dictionaries. That works for a local demo, but it loses all state on restart and prevents reliable real-world use.

## Acceptance criteria
- Core entities are persisted in PostgreSQL instead of process memory.
- FastAPI endpoints read and write through repository or data-access abstractions.
- Restarting the API does not lose user state.
- Persistence behavior is covered by automated tests.

## Relevant files or components
- `app/store.py`
- `app/main.py`
- `app/models/`
- `sql/schema.sql`
- future repository/data-access modules under `app/`

## Dependencies or blockers
- Depends on choosing and wiring a migration approach.
- Likely sequenced with database configuration cleanup.

## Security considerations
- Enforce object ownership and authorization boundaries at the data-access layer.
- Avoid logging sensitive profile or application payloads during persistence failures.
- Preserve consent and audit-related data needed for consequential actions.

## Testing considerations
- Add unit tests for repository behavior.
- Add integration tests covering create/read/update flows through the API.
- Include negative tests for missing records and invalid ownership access once auth is introduced.
