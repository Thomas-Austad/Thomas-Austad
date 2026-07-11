# Issue #20 execution plan — consent-gated browser handoff

## Scope and safety boundary

This delivery adds a local, user-controlled handoff from an **already locally
approved** application package to the corresponding public employer apply page.
It does not upload a resume, prefill or send a form, submit an application,
store employer credentials, automate a browser, scrape an authenticated page,
or claim that a submission occurred.

The browser itself performs the only external navigation when the user activates
an ordinary link. The server never launches a browser and does not treat the
link activation as a provider response or an application receipt.

## Design

1. Add typed browser-handoff and receipt models to the application schema.
   A receipt binds an idempotency key to the exact validated public destination
   and is persisted with the existing application package; it records only
   non-sensitive handoff metadata.
2. Add a domain helper and authenticated HTTP route that require the package to
   be locally approved and require direct user confirmation. The helper derives
   the destination from the stored job record, validates HTTPS, no userinfo,
   default HTTPS port, and the known provider host for Greenhouse, Lever, or
   Ashby. It never accepts a caller-provided URL.
3. Record a minimal audit event after persisting the handoff receipt. On audit
   failure, revert the receipt and return a safe error. Repeated use of the
   same idempotency key returns the same handoff response without a duplicate
   audit record.
4. Expose the exact narrow operation through an MCP tool that demands direct
   confirmation and uses the shared domain helper.
5. Add a widget confirmation dialog. Only after the tool returns the validated
   destination does the widget render a user-activated, `noopener` external
   link. It must not call `window.open`, offer a submission button, or report a
   handoff as a submission.

## Verification

- Focused API tests cover missing confirmation, unresolved/unapproved state,
  missing jobs, untrusted/mismatched destinations, audit rollback, idempotent
  retries, and redaction.
- MCP tests prove a direct confirmation is required and the new tool uses the
  widget template.
- Widget tests prove the confirmed handoff renders a safe external link, never
  exposes a submission control, and prevents duplicate activation while pending.
- Run `pnpm --dir widget typecheck`, `pnpm --dir widget test --run`,
  `pnpm --dir widget build`, `python -m ruff check .`, `python -m pytest`, and
  `python -m pytest -m eval`.
