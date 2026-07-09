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
# Add OPENAI_API_KEY
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .[dev]
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

## Development workflow

Repository-specific engineering rules live in `AGENTS.md`.

For explicit autonomous maintenance runs, use
`docs/autonomous-application-development-workflow.md`. An example invocation and
expected stop report are in `docs/autonomous-workflow-example.md`.
