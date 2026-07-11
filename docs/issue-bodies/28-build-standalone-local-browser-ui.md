## Context and motivation

Talent Advisor currently exposes a FastAPI API and an MCP widget resource. It
does not provide a standalone local browser interface that a personal user can
open, authenticate to safely, and use without configuring an MCP client or
calling REST endpoints manually.

Build a complete local-first browser UI for the core candidate-to-application
review workflow. This must be a real user-facing product surface, not a thin
demo around unsafe API calls or a replacement for explicit review and approval.

## Product requirement: non-technical users

Assume the primary user has never used a command line, an API client, an MCP
server, a developer tool, or a configuration file. Every ordinary task must be
expressed in plain language and completed through visible, guided controls.
Technical terms such as bearer token, endpoint, database, migration, JSON,
environment variable, Docker, and MCP must not be prerequisites for using the
application.

## Scope

- Design and implement a browser UI served only from the local application
  stack, opened automatically by the supported local launcher rather than
  requiring users to enter a loopback URL or run a terminal command.
- Include first-run guidance and an in-product readiness screen that explains
  only the user actions required to begin. It must not expose infrastructure,
  developer diagnostics, or configuration-file instructions.
- Cover the primary workflow: profile/resume intake, evidence review and
  corrections, supported job-board search and job review, match and
  compensation results, application-package review, screening-question
  resolution, explicit local approval, DOCX download, and browser handoff.
- Add accessible loading, empty, validation, error, and success states.
- Integrate with typed backend contracts; keep business rules, authorization,
  data protection, and approval decisions on the server.
- Provide UI architecture, privacy/security decisions, and end-user operating
  documentation. Reuse the existing widget only where it is safe and useful;
  do not require ChatGPT/MCP to use the browser interface.

## Acceptance criteria

- After the local startup workflow completes, a user can open one documented
  local application UI and complete the core workflow without a terminal,
  Postman, curl, manual bearer-token copying, a configuration file, or an MCP
  client.
- The UI uses task-oriented, plain-language labels and guided next steps. It
  never expects a user to supply an API endpoint, database value, secret,
  request header, raw job-board identifier, or JSON payload.
- The UI uses TypeScript with strict mode and runtime-validated messages at
  every browser/server boundary. External job, resume, and generated text is
  rendered as text, not trusted HTML.
- Local authentication is designed so the browser does not store or expose the
  local bearer credential in localStorage, page source, logs, or frontend
  bundles. It also must not ask the user to retrieve or paste a bearer token.
  State-changing requests have the appropriate local security and CSRF
  protections.
- Profile corrections, screening-answer resolution, approval, export, deletion,
  retention purge, and browser handoff each require clear, target-specific
  confirmation. Approval is visibly distinct from application submission.
- The UI never presents browser handoff as a submission and clearly states that
  the user must finish any employer form and submission themselves.
- Sensitive screening questions remain unresolved until the user directly
  enters and confirms each answer. The UI must not prefill, infer, or suggest
  legally meaningful or sensitive answers.
- Repeated clicks cannot create duplicate consequential actions; frontend state
  reflects backend idempotency and safe retry outcomes.
- The UI is keyboard operable and uses semantic controls, labels, focus
  management, and status announcements for asynchronous operations.
- The UI has automated tests for the main happy path and important error,
  authorization, confirmation, duplicate-action, and injection cases.

## Relevant files or components

- `widget/` and its existing TypeScript/React components and tests
- `app/main.py`, `app/mcp_server.py`, `app/models/schemas.py`, and API routes
- `app/services/local_auth_service.py`, audit services, rate limiting, and data
  protection services
- `app/agents/`, `app/connectors/`, repositories, and migrations as required
- `README.md`, local setup documentation, and operations runbook

## Dependencies and blockers

- Decide whether to evolve `widget/` into the standalone UI or introduce a
  separate frontend package while preserving the existing MCP widget.
- Establish the server-side browser authentication/session and CSRF design
  before exposing private API operations to browser pages.
- Coordinate the final local UI URL and startup command with the streamlined
  setup/onboarding issue.
- No provider submission integration is included; issue #27 remains separate.

## Security and privacy considerations

- Keep candidate PII, tokens, credentials, full prompts, generated documents,
  and sensitive screening answers out of browser storage, analytics, logs, and
  error payloads.
- Do not leak technical diagnostic details to end users. Offer a simple,
  privacy-preserving recovery action and reserve detailed diagnostics for an
  explicitly requested support/export flow.
- Bind the UI/API only to loopback and use an explicit same-origin/CORS policy.
- Treat uploaded resumes, job descriptions, provider data, and model output as
  untrusted content. Do not allow any of it to choose tools, destinations,
  consent, or approval state.
- Server-side code must validate ownership, state transitions, confirmations,
  idempotency, and audit recording; UI confirmation alone is never sufficient.
- Do not add third-party scripts, remote fonts, analytics, or trackers without
  a documented privacy and security review.

## Testing considerations

- Add focused frontend tests for input validation, profile correction,
  approval/handoff confirmation, unresolved sensitive questions, duplicate
  clicks, API failure states, and safe rendering of injection-like external
  text.
- Add backend integration tests for browser authentication/authorization,
  CSRF (if applicable), idempotency, and confirmation enforcement.
- Use synthetic candidates, jobs, resumes, and screening questions only.
- Run `pnpm --dir widget typecheck`, `pnpm --dir widget test --run`,
  `python -m ruff check .`, `python -m pytest`, and `python -m pytest -m eval`
  before completion.
