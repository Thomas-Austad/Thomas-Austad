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
uvicorn app.main:app --host 127.0.0.1 --reload
```

Health check: `http://localhost:8000/health`

Run MCP server:

```bash
cd widget
pnpm install --frozen-lockfile
pnpm build
cd ..
python -m app.mcp_server
```

MCP uses local stdio. Do not expose it through a development tunnel or public URL.
The widget build is required because the local MCP resource serves the generated
UI assets. Run `pnpm test --run` and `pnpm typecheck` from `widget/` while
developing the UI. The widget does not receive the local bearer credential and
does not call the loopback API directly.

## Typical workflow

1. `POST /profiles`
2. `GET /profiles/{candidate_id}/review`
3. `PATCH /profiles/{candidate_id}` to save user corrections
4. `POST /jobs/search`
5. `POST /matches/{candidate_id}/{job_id}`
6. `POST /compensation/{candidate_id}`
7. `POST /applications/prepare`
8. Resolve required user inputs
9. `POST /applications/{application_id}/approve`
10. Optionally review `GET /applications/{application_id}/browser-handoff`, then
    directly confirm `POST /applications/{application_id}/browser-handoff` to
    receive a validated employer-page link
11. Download `/applications/{application_id}/resume.docx`

## Important boundary

This MVP prepares and tracks applications. Direct submission must be implemented only through approved ATS/job-board APIs or a user-controlled browser assistant. Never guess legally meaningful screening answers or submit without explicit approval.

Browser handoff is not application submission. It is available only for a
locally approved package and a known HTTPS Greenhouse, Lever, or Ashby employer
page. After direct confirmation, the app returns a user-activated external link
without uploading materials, transferring employer credentials, prefilling a
form, or representing a submission outcome.

API datetime fields are serialized as ISO 8601 timestamps with explicit UTC offsets.
Sensitive screening questions are surfaced in `unresolved_screening_questions`, removed from generated screening answers, and block approval until resolved. Successful approvals and direct sensitive-screening confirmations write non-sensitive JSONL audit receipts to `AUDIT_LOG_PATH` (default `var/audit/events.jsonl`).

## Local-only security model

This is a single-user, local-first application. The API is intended to bind only
to a loopback address and requires a bearer credential for every private route.
On a normal desktop installation, the application creates and stores that
credential in the operating system credential store; `LOCAL_ACCESS_TOKEN` is a
headless or automation fallback and must be at least 32 characters. The local
operating-system user is the sole application principal, and no hosted accounts,
sharing, or remote MCP transport are supported.

This model relies on the security of the user's operating-system account and
disk encryption. It cannot protect information from an administrator, malware,
or another process running as that same user.

## Container safety

`docker-compose.yml` is for local development only. Its API and database ports
bind to loopback so they are not exposed to the local network. Before using the
stack, copy `.env.example` to `.env`, choose a unique local database password,
and set `DATABASE_URL` to the matching local PostgreSQL connection URL.

Do not deploy this Compose file as a hosted service. This project is designed
to run on the user's own computer with loopback-only access.

## Development workflow

Repository-specific engineering rules live in `AGENTS.md`.

For explicit autonomous maintenance runs, use
`docs/autonomous-application-development-workflow.md`. An example invocation and
expected stop report are in `docs/autonomous-workflow-example.md`.
