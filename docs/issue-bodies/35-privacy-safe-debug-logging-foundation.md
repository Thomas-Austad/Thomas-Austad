## Context and motivation

The current `talent_advisor` logger emits only a few ad hoc informational
events. The application needs a consistent, opt-in debug-logging foundation
before endpoint, MCP, model, connector, persistence, document, authentication,
and approval flows can be traced safely.

This issue replaces the logging-specific portion of closed issue #12 with a
privacy-preserving scope. “Verbose” means detailed lifecycle metadata and
safe error context, never verbose capture of candidate or provider content.

## Scope

- Define a structured event schema and a shared logging API in
  `app/observability.py`.
- Configure named loggers and an opt-in debug level through validated runtime
  configuration; keep production defaults conservative.
- Establish correlation/request IDs at FastAPI and MCP entry points and make
  them available to downstream components without relying on user-controlled
  IDs as trusted identity.
- Define a small allowlist of safe fields, redaction rules, error-class
  reporting, duration/count fields, and event naming conventions.
- Keep operational logs distinct from the append-only audit receipts in
  `app/services/audit_service.py`.
- Update the operations runbook with safe debug enablement, log destinations,
  and a troubleshooting example using synthetic data only.

## Acceptance criteria

- A single documented structured logging contract supports `DEBUG`, `INFO`,
  `WARNING`, and `ERROR` events and is usable from synchronous and async code.
- Every event has an event name, severity, correlation ID when a request/tool
  invocation exists, and only allowlisted context fields.
- Debug logging can be explicitly enabled for local troubleshooting without
  changing business behavior, and it is disabled by default in normal runs.
- Log helpers reject, redact, or omit sensitive/unsafe fields rather than
  serializing arbitrary `**kwargs` values.
- Resume text, LinkedIn/profile text, prompts, model responses, generated
  documents, screening questions/answers, bearer/session/bootstrap tokens,
  cookies, raw request bodies, raw provider payloads, and URLs containing
  secrets are never emitted.
- The audit log remains a minimal business record; debug logging neither
  substitutes for it nor alters approval/submission behavior.
- Focused tests prove correlation, level configuration, and redaction; the
  project completion checks pass.

## Relevant files or components

- `app/observability.py`, `app/config.py`, and `app/main.py`
- `app/mcp_server.py`
- `app/services/audit_service.py`
- `docs/operations-runbook.md`
- focused observability, FastAPI, and MCP tests

## Dependencies or blockers

- None. This is the prerequisite for the two instrumentation issues that add
  events to individual application paths.
- It supersedes only the unfinished logging detail of closed issue #12; its
  retry, CI, and release-hardening scope remains outside this issue.

## Security considerations

- Treat all application content, external content, and headers as untrusted
  logging input.
- Do not add candidate identifiers, actor identifiers, or job/application IDs
  unless their format, necessity, and retention impact are explicitly reviewed.
- Never make debug output available through an API, MCP response, widget, or
  public endpoint.

## Testing considerations

- Test safe formatting and redaction for nested mappings, exception messages,
  URLs, and commonly sensitive keys.
- Test that debug mode does not expose request contents or credentials.
- Run `python -m ruff check .` and `python -m pytest` before completion.
