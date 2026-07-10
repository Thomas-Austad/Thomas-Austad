# Operations Runbook

## Quality Gates

Run before deployment or main-branch maintenance commits:

```powershell
python -m ruff check .
python -m pytest
python -m pytest -m eval
.\.venv\Scripts\python.exe -m alembic upgrade head --sql
```

CI runs lint, the full test suite, and the eval subset on pushes and pull
requests targeting `main`.

## Configuration

- `OPENAI_TIMEOUT_SECONDS` controls model request timeout seconds.
- `OPENAI_MAX_RETRIES` controls SDK-level retries for model calls.
- `CONNECTOR_TIMEOUT_SECONDS` controls ATS connector HTTP timeouts.
- `CONNECTOR_MAX_ATTEMPTS` controls read-only connector retry attempts.
- `API_RATE_LIMIT_ENABLED` enables process-local fixed-window API limits.
- `API_RATE_LIMIT_WINDOW_SECONDS` controls the fixed-window duration.
- `API_DEFAULT_RATE_LIMIT` controls uncategorized endpoint requests per window.
- `API_MODEL_RATE_LIMIT` controls model-backed endpoints such as profile,
  matching, compensation, and application preparation.
- `API_UPLOAD_RATE_LIMIT` controls resume extraction uploads.
- `API_JOB_SEARCH_RATE_LIMIT` controls job search requests.
- `API_DOCUMENT_RATE_LIMIT` controls generated resume downloads.
- `API_WRITE_RATE_LIMIT` controls approval-like write endpoints.

Keep secrets in environment variables or `.env`; do not commit credentials.

## Container deployment

The checked-in Compose file supports local development only. It binds the API
and database ports to loopback, and it requires a user-chosen
`POSTGRES_PASSWORD`; never expose the database port in production.

For a production deployment, build the pinned image, run it as its included
non-root user, inject configuration through a secret manager, apply migrations
as a controlled deployment step, and expose only the API through HTTPS. Verify
the container health check after startup and allow at least 30 seconds for
graceful Uvicorn shutdown before replacing or stopping a replica.

To smoke-test an image on a Docker-enabled host:

```powershell
docker build --tag talent-advisor-platform:smoke .
docker run --detach --rm --name talent-advisor-smoke --publish 127.0.0.1:18000:8000 talent-advisor-platform:smoke
Invoke-WebRequest http://127.0.0.1:18000/health
docker stop talent-advisor-smoke
```

The built-in limiter is intentionally coarse and process-local. Use an
authenticated, shared rate-limit service for production deployments with
multiple workers or hosts.

## Logs and Metrics

Structured events are emitted through the `talent_advisor` logger and contain
event names, provider names, counts, and error classes only. Do not add resumes,
profile text, prompts, screening answers, generated documents, raw provider
payloads, or tokens to logs.

In-process metrics are process-local counters for smoke testing and diagnostics.
They are not durable and are not a substitute for production metrics storage.

## Failure Handling

- Connector failures are retried only for HTTP and timeout errors.
- Failed provider reads are skipped so another provider can still return jobs.
- Approval and future submission-like write actions must not be retried unless
  they are explicitly idempotent and approval-gated.
