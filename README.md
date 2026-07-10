# Talent Advisor Platform

A personal-use, ChatGPT-native AI career platform MVP.

## Included

- Evidence-grounded candidate profile agent
- Compensation estimate agent
- Greenhouse and Lever job connectors
- Multi-factor job-match scoring
- Truthful resume and cover-letter tailoring
- Screening-question guardrails
- Application approval state
- DOCX resume export
- FastAPI backend
- MCP tool surface for ChatGPT
- PostgreSQL starter schema

## Run locally

```bash
cp .env.example .env
# Add OPENAI_API_KEY and a unique POSTGRES_PASSWORD.
# Set DATABASE_URL to the matching local PostgreSQL URL before running locally.
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .[dev]
docker compose up -d db
alembic upgrade head
uvicorn app.main:app --reload
```

Health check: `http://localhost:8000/health`

Run MCP server:

```bash
python -m app.mcp_server
```

Expose the MCP endpoint through an HTTPS development tunnel, then add it in ChatGPT under developer/app connector settings.

## Typical workflow

1. `POST /profiles`
2. `POST /jobs/search`
3. `POST /matches/{candidate_id}/{job_id}`
4. `POST /compensation/{candidate_id}`
5. `POST /applications/prepare`
6. Resolve required user inputs
7. `POST /applications/{application_id}/approve`
8. Download `/applications/{application_id}/resume.docx`

## Important boundary

This MVP prepares and tracks applications. Direct submission must be implemented only through approved ATS/job-board APIs or a user-controlled browser assistant. Never guess legally meaningful screening answers or submit without explicit approval.

API datetime fields are serialized as ISO 8601 timestamps with explicit UTC offsets.
Sensitive screening questions are surfaced in `unresolved_screening_questions`, removed from generated screening answers, and block approval until resolved. Successful approvals write non-sensitive JSONL audit receipts to `AUDIT_LOG_PATH` (default `var/audit/events.jsonl`).

## Container safety

`docker-compose.yml` is for local development only. Its API and database ports
bind to loopback so they are not exposed to the local network. Before using the
stack, copy `.env.example` to `.env`, choose a unique local database password,
and set `DATABASE_URL` to the matching local PostgreSQL connection URL.

Do not deploy this Compose file directly to production. Use a managed database
that is not publicly reachable, inject secrets through an approved secret
manager, run migrations as a controlled deployment step, and expose only the
API through an HTTPS-capable reverse proxy or platform ingress.

## Development workflow

Repository-specific engineering rules live in `AGENTS.md`.

For explicit autonomous maintenance runs, use
`docs/autonomous-application-development-workflow.md`. An example invocation and
expected stop report are in `docs/autonomous-workflow-example.md`.
