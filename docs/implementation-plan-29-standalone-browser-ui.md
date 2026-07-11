# Issue 29 implementation plan: standalone local browser UI

## Approved architecture

The existing `widget/` stays an MCP Apps iframe. A separate React/TypeScript
browser build is served by FastAPI from the same loopback origin as the API.
It reuses only presentational components and runtime schemas; it never uses the
MCP bridge or receives the local bearer credential.

The supported launcher obtains a random, single-use bootstrap value from the
local process, opens `/app#bootstrap=<value>`, and the minimal UI exchanges the
fragment over a same-origin POST. The server immediately creates an opaque,
server-side session and returns an `HttpOnly`, `SameSite=Strict`, host-only
cookie. The fragment is removed before the application is rendered. Bootstrap
values expire quickly and are neither logged nor persisted.

All browser write requests require a synchronizer CSRF value, exact loopback
`Origin` validation, and Fetch Metadata checks. The CSRF value is scoped to the
server-side session and is held only in browser memory. The bearer-only API
continues to serve MCP and automation callers; browser-session routes reject
bearer authentication and all browser requests remain loopback-only.

## Trust boundaries and data handling

- Resume text, job content, generated materials, and provider responses are
  untrusted text and are rendered only as text.
- Session identifiers and bearer credentials are never exposed to JavaScript,
  browser storage, source bundles, URLs after bootstrap, logs, or diagnostics.
- The server remains authoritative for ownership, direct confirmations,
  idempotency, approvals, browser handoff validation, and audit receipts.
- The browser UI cannot submit an application or invoke any provider write API.

## Delivery steps

1. Add an in-memory, bounded browser-session service with one-time bootstrap,
   expiry, secure cookie, CSRF, origin, and Fetch Metadata validation.
2. Serve an independently built, same-origin browser application and add its
   typed REST client. Reuse no credential-bearing MCP path.
3. Cover profile intake/review/correction, job search and review, match and
   compensation, package review, sensitive-answer confirmation, local approval,
   DOCX export, and browser handoff with accessible controls and statuses.
4. Add backend and browser tests for authorization, CSRF, replay, confirmation,
   duplicate actions, and injection-like content.
5. Document local operation, launcher integration, privacy assumptions, and the
   explicit distinction between local approval, browser handoff, and submission.

## Validation

- Focused browser-session and API tests.
- `pnpm --dir widget typecheck`
- `pnpm --dir widget test --run`
- `pnpm --dir widget build`
- `python -m ruff check .`
- `python -m pytest`
- `python -m pytest -m eval`
