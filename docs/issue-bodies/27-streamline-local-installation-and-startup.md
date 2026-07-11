## Context and motivation

The current local setup requires users to manually install and coordinate
Python, a virtual environment, Docker/PostgreSQL, Node.js, pnpm, environment
configuration, database migrations, the API, and a separate MCP process. The
MCP widget is not a browser UI and its client-registration path is not
actionable for a non-developer user.

This is too fragile and developer-oriented for a personal-use product. Create
a reliable, guided local onboarding and startup workflow that makes all
prerequisites, configuration, verification, and the chosen user interface
explicit.

## Product requirement: non-technical users

Assume the primary user has never opened a command-line window and cannot be
asked to edit `.env` files, install packages, interpret stack traces, manage a
database, configure an MCP client, or copy a bearer token. The supported
product path must be a graphical installer/launcher and first-run experience.
Command-line commands may remain as a developer troubleshooting path, but they
are not an acceptable prerequisite for ordinary use.

## Scope

- Add a Windows-first setup and startup experience with small, reviewable
  scripts or commands for developers, plus a graphical installer/launcher for
  non-technical users. The user-facing path handles prerequisite checks,
  dependency-installation guidance, configuration validation, database
  startup, migration, and health verification without requiring a terminal.
- Provide a graphical first-run configuration path that never prints, logs, or
  commits secrets. It may request an OpenAI API key using plain language but
  must generate/manage local database and API credentials without requiring
  users to edit a configuration file or copy a token.
- Detect and explain missing or unusable Python, Docker daemon, Node.js, pnpm,
  PostgreSQL health, OpenAI configuration, database connectivity, widget
  assets, and occupied local ports.
- Make the startup path clear for the API and for the standalone browser UI
  delivered by the companion UI issue. Do not present a raw MCP stdio server as
  a terminal-interactive application.
- Update user-facing documentation with one canonical, copy/pasteable local
  workflow and recovery steps.

## Acceptance criteria

- A first-time Windows user can follow one documented entry point to discover
  prerequisites and configure the application without opening a terminal,
  reading source code, or editing a configuration file.
- The supported entry point is discoverable as a normal local application
  (installer/shortcut/launcher) and opens the standalone UI after successful
  startup; it does not require a user to find or start a Python process.
- The entry point validates required configuration before starting services and
  reports actionable, non-sensitive errors in plain language for every missing
  dependency, with a clear next action rather than a command, traceback, or
  package name.
- It never silently installs software, starts a network-exposed service, or
  creates a weak/default credential. Any installer or external change requires
  a clear user action.
- It creates or validates only a local, loopback-bound deployment; no command
  publishes ports, creates a public tunnel, or configures remote MCP transport.
- It starts PostgreSQL, applies migrations, verifies API health, and identifies
  the local application UI when it is ready; database and API implementation
  details are not shown to ordinary users.
- A repeat run is safe: it preserves existing `.env` values and database data,
  does not duplicate migrations, and clearly distinguishes stop/restart from
  destructive reset actions.
- Documentation states that current application actions prepare, review, and
  locally approve application packages; they do not submit an application.

## Relevant files or components

- `README.md`
- `docs/dev-setup.md`, `docs/operations-runbook.md`, and local-user guides
- `.env.example`, `docker-compose.yml`, `Dockerfile`, and `pyproject.toml`
- Alembic configuration and migrations
- `app/config.py`, `app/services/local_auth_service.py`, and local audit paths
- `widget/package.json` and the standalone UI delivery work

## Dependencies and blockers

- The standalone browser UI issue must define the supported browser entrypoint
  before the onboarding flow can advertise a final user-facing URL.
- Users still need a valid OpenAI API key and local permission to run Docker.
- Choose whether the setup helper is PowerShell-only or whether a documented
  cross-platform equivalent is also in scope.

## Security considerations

- Never echo or write API keys, database passwords, access tokens, resumes, or
  candidate data to the console, logs, scripts, Git, or generated diagnostics.
- Do not expose `.env`, database URLs, bearer tokens, Docker details, or MCP
  configuration in the ordinary user interface.
- Validate that all application services bind to loopback only.
- Do not disable local authentication, encryption/keyring behavior, rate
  limits, approval gates, or audit requirements to simplify setup.
- Any generated secret must be cryptographically secure, user-controlled, and
  stored only in the intended local secret/configuration location.

## Testing considerations

- Exercise the non-destructive prerequisite and configuration checks in a clean
  local environment and with synthetic configuration only.
- Verify failures for a missing Docker daemon, missing Node/pnpm, invalid or
  absent database URL, unavailable PostgreSQL, unavailable credential store,
  missing widget build, occupied port, and invalid OpenAI configuration.
- Verify repeat runs leave existing `.env` values and database data intact.
- Run `python -m ruff check .`, `python -m pytest`, and any focused validation
  added for the setup workflow before completion.
