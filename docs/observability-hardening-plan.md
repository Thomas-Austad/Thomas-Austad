# Observability and Release Hardening Plan

## Scope

Implement issue #12 with a bounded reliability pass for model calls, connector
calls, CI quality gates, and operational documentation.

## Trust Boundaries and Data

- Logs and metrics must describe events and outcomes without storing resumes,
  prompts, screening answers, generated documents, or raw provider payloads.
- Retry logic is limited to read-only model and connector calls; application
  approval and future consequential writes remain non-retried unless explicitly
  designed with idempotency.
- CI must run repository quality gates without requiring production secrets.

## Implementation Steps

1. Add configuration knobs for OpenAI and connector timeout/retry policies.
2. Add structured logging and minimal in-process metrics counters for read-only
   service events.
3. Apply connector retries in `JobService` and configure OpenAI client timeout
   and retry behavior.
4. Add CI for lint, tests, and eval tests with least-privilege permissions.
5. Document operational commands, expected logs, and failure handling.

## Validation

- `ruff check .`
- `pytest`
- `pytest -m eval`
