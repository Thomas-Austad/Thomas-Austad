# Migrations and Database Configuration Plan

## Scope

Implement issue #2 by introducing a versioned migration workflow and making
database configuration explicit and PostgreSQL-oriented across local
development, Docker, and tests.

## Trust Boundaries and Data

- Database URLs can contain credentials and must stay in environment variables
  or local `.env` files.
- Migration files are source-controlled schema definitions and must not contain
  production secrets or data.
- This change does not persist candidate data at runtime yet and does not alter
  application approval, submission, authorization, or audit semantics.

## Implementation Steps

1. Add Alembic as the migration tool and configure it to read `DATABASE_URL`
   through `app.config.Settings`.
2. Represent the current `sql/schema.sql` tables in an initial Alembic
   migration.
3. Update configuration defaults and examples so local runtime uses PostgreSQL
   and Docker uses the Compose database service.
4. Add tests for database URL validation and migration configuration behavior.
5. Update developer documentation with database bootstrap commands.

## Validation

- `ruff check .`
- `pytest`
