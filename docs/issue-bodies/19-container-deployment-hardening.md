## Context and motivation
The repository has a basic Dockerfile and Compose setup for local development, but the container and deployment defaults are not hardened enough for production-like use with sensitive candidate data.

## Acceptance criteria
- The runtime image uses a non-root user and a minimal, pinned base image strategy.
- Dependency manifests are copied before source to improve reproducible caching.
- A `.dockerignore` excludes local caches, virtualenvs, generated artifacts, secrets, databases, and development-only files.
- Health checks and graceful shutdown behavior are documented and configured where appropriate.
- Production guidance avoids publishing database ports and avoids development default passwords.

## Relevant files or components
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `.env.example`
- `docs/dev-setup.md`
- `docs/operations-runbook.md`

## Dependencies or blockers
- Should be coordinated with final deployment target decisions and secret-management choices.
- Does not require application feature changes.

## Security considerations
- Do not bake secrets into images or build arguments.
- Avoid committing generated documents, databases, local `.env` files, or cache directories.
- Reduce container privileges and writable filesystem surface where feasible.

## Testing considerations
- Add or document a container smoke test that builds the image and verifies `/health`.
- Validate local development remains straightforward while production guidance is safer.
