# Issue 19 implementation plan: container and deployment hardening

## Scope

Harden the container build and document safe deployment defaults without
changing application behavior, data handling, authentication, or approval
semantics.

## Trust boundaries

- Container images must not contain local secrets, candidate data, generated
  documents, database files, caches, or development environments.
- The runtime must run with reduced privileges and expose only the API service
  it needs to serve.
- Docker Compose remains a local-development convenience; production requires
  separately managed secrets and a database that is not publicly published.

## Implementation steps

1. Pin the Python base image to a supported Debian slim release, install
   dependencies before application source, and use an unprivileged runtime user.
2. Add a `.dockerignore` for source-control metadata, credentials, virtual
   environments, caches, generated artifacts, and local database state.
3. Add an API health check and graceful Uvicorn shutdown configuration.
4. Clarify local-versus-production Compose behavior, including database-port,
   credentials, secrets, and health-check expectations.
5. Verify the Dockerfile and Compose configuration with the available local
   tooling, then run the repository quality gates.

## Validation

- Docker or Compose configuration/build smoke check when Docker is available.
- `.venv\\Scripts\\python.exe -m ruff check .`
- `.venv\\Scripts\\python.exe -m pytest`
- `git diff --check`
