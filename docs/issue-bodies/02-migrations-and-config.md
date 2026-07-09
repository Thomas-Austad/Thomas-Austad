## Context and motivation
The repo includes a schema and a Docker database service, but runtime configuration still defaults to SQLite and there is no migration workflow. That creates drift between development, test, and deployment environments.

## Acceptance criteria
- A migration tool is introduced and the initial schema is represented as versioned migrations.
- `DATABASE_URL` handling is consistent across app runtime, tests, and Docker.
- Developers can bootstrap the database without manually running SQL files.
- Startup failures produce clear errors for invalid or missing database configuration.

## Relevant files or components
- `app/config.py`
- `docker-compose.yml`
- `Dockerfile`
- `sql/schema.sql`
- future migration config and scripts

## Dependencies or blockers
- Should be coordinated with repository/persistence work.
- May require selecting a migration tool and local developer workflow.

## Security considerations
- Avoid unsafe defaults that accidentally point local or test code at production data.
- Ensure secrets stay in environment variables and are not baked into migration scripts or images.

## Testing considerations
- Add tests or validation checks for config parsing.
- Verify migrations apply cleanly in a fresh database and on an existing database state.
