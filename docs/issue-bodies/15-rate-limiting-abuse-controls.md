## Context and motivation
The API exposes expensive and sensitive workflows for uploads, job searches, model calls, document generation, and approval-like writes, but it does not yet enforce rate limits, request-size policy beyond resume bytes, or abuse controls.

## Acceptance criteria
- Rate limits are defined and enforced for authentication-sensitive, upload, job search, model-backed, document-generation, and write endpoints.
- Large list inputs, long free-text fields, and pagination-like request sizes are bounded consistently.
- Abuse controls fail closed with safe, non-sensitive errors.
- Limits are configurable per environment and documented for local development and deployment.

## Relevant files or components
- `app/main.py`
- `app/config.py`
- `app/services/job_service.py`
- `app/services/openai_service.py`
- `app/services/document_service.py`
- `tests/`
- `docs/operations-runbook.md`

## Dependencies or blockers
- Auth work will improve per-user limits, but coarse IP or process-level limits can start earlier.
- Should align with observability so rejected requests are visible without logging sensitive payloads.

## Security considerations
- Prevent resource exhaustion, model-cost spikes, upload abuse, and repeated approval attempts.
- Do not log resumes, screening answers, prompts, generated documents, or raw provider payloads while recording limit events.

## Testing considerations
- Add tests for allowed requests, throttled requests, boundary sizes, oversized text/list inputs, and safe error bodies.
- Include duplicate/replayed write-action tests once idempotency keys are introduced.
