# Issue 9 implementation plan: local authentication and audit

## Deployment decision

The application is local-first and single-user. It runs on the user's computer
without a hosted backend, identity provider, multi-user tenancy, or sharing.
The operating-system user is the sole owner of the local instance. Private HTTP
operations require a per-installation bearer credential obtained from the OS
credential store; a configured environment value is an explicit fallback for
headless or automated local use. MCP uses stdio only, so the launching local
user is the authenticated principal.

This boundary does not protect against an administrator, malware, or another
process running as the same OS user. The API must remain loopback-only.

## Trust boundaries

- Resumes, profiles, generated documents, and application packages are private
  local data.
- The `Authorization` header is a secret and must never be logged or placed in
  audit records.
- Candidate- and application-supplied identifiers are untrusted input; no
  caller may choose an owner identity.
- Approval and sensitive-screening confirmation are consequential local state
  changes and require an audit receipt.

## Implementation steps

1. Add a local credential service that retrieves or creates a random token in
   the operating system credential store, with a deliberately configured
   environment fallback and safe service-unavailable behavior.
2. Require a constant-time checked bearer token for every private FastAPI
   route, leaving only `/health` unauthenticated.
3. Represent the authenticated actor as the fixed `local_user` principal. In
   this single-user edition, all local records belong to that principal and no
   request accepts a user or tenant identifier.
4. Add actor metadata to minimal JSONL audit events and emit receipts for
   approval and direct sensitive-screening confirmation without storing answers
   or other sensitive payloads.
5. Run MCP over stdio rather than streamable HTTP and document the local-only
   operating boundary.
6. Add negative tests for missing, malformed, invalid, and unavailable local
   credentials, plus audit assertions proving that tokens and screening answers
   are absent.

## Validation

- Focused authorization and API workflow tests.
- `python -m ruff check .`
- `python -m pytest`

## Deferred work

- At-rest encryption, data export, and deletion are issue #10.
- Hosted identity, multi-user authorization, remote MCP, and sharing are out
  of scope for this local-only product.
