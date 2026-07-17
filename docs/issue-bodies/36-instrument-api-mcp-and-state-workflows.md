## Context and motivation

After the privacy-safe debug-logging foundation is available, the interactive
entry points and local state transitions need detailed lifecycle visibility.
This work covers the FastAPI API, MCP tools, browser-session flow, local
authentication outcomes, document operations, retention actions, and approval
workflows. It must preserve the product rule that preparation, approval,
browser handoff, and any future submission are separate operations.

## Scope

- Instrument FastAPI request lifecycle, route selection, validation failures,
  status outcome, duration, rate-limit decision, and unexpected internal
  errors with the shared safe event schema.
- Instrument each MCP resource/tool invocation with tool name, lifecycle
  outcome, duration, and correlation ID while keeping tool arguments and
  results out of logs.
- Add safe debug events around browser-session bootstrap/logout, local auth
  success/failure class, profile/document actions, retention review/purge,
  profile corrections, screening confirmations, application preparation,
  approval, and browser handoff.
- Instrument in-memory/repository state-operation outcomes without logging
  stored candidate data or unbounded identifiers.
- Document an event inventory that lets operators distinguish a rejected,
  failed, completed, and no-op/idempotent operation.

## Acceptance criteria

- All supported API routes and MCP tools emit safe start/completion/failure
  lifecycle events using the foundation established by its prerequisite.
- Events expose only route/template or tool name, safe outcome/error class,
  duration, status/decision category, and correlation metadata; they do not
  include request or response bodies, raw path/query values, cookies, tokens,
  candidates, profiles, jobs, resumes, documents, answers, or generated text.
- Authentication, authorization, CSRF, confirmation, validation, rate-limit,
  and idempotency failures are observable by category without revealing why a
  particular credential or secret failed.
- State-changing action events never imply that an application was externally
  submitted; browser handoff is named and logged as a non-submitting local
  operation.
- Exceptions continue to produce the existing safe client responses, and
  instrumentation cannot mask, retry, or alter an action.
- Tests cover representative API and MCP success/failure paths plus assertions
  that sensitive arguments and outputs never appear in captured logs.

## Relevant files or components

- `app/main.py`, `app/mcp_server.py`, and `app/rate_limit.py`
- `app/services/local_auth_service.py`, `app/services/browser_session_service.py`,
  `app/services/document_service.py`, and `app/services/audit_service.py`
- `app/store.py`, `app/repositories.py`, and relevant persistence paths
- API, MCP, browser-session, document, auth, and repository tests

## Dependencies or blockers

- Depends on the privacy-safe logging foundation issue.
- This issue does not add submission, browser automation, or any new external
  write capability.

## Security considerations

- Never log bearer credentials, session/bootstrap/CSRF values, request bodies,
  paths containing object IDs, filenames, file contents, audit payloads, or
  confirmation/screening content.
- Preserve the existing authorization, ownership, explicit confirmation,
  idempotency, and audit constraints; logs are diagnostic metadata only.

## Testing considerations

- Use synthetic fixtures only.
- Add negative tests for invalid credentials, malformed input, CSRF failure,
  missing confirmation, replay/idempotency paths, and audit-write failure.
- Run `python -m ruff check .` and `python -m pytest` before completion.
