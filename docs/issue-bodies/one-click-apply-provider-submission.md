## Context and motivation

The product currently prepares and locally approves application packages. The
planned browser-handoff flow can help users navigate to an employer's apply
page, but it must never be mistaken for a submission. A future one-click apply
operation needs an explicit, provider-approved architecture before any external
write capability is implemented.

This issue implements one selected provider's consent-gated write workflow
only after the prerequisites below are supplied. It is intentionally distinct
from issue #20: #20 owns the broader assisted-apply design; this issue is the
bounded provider-specific delivery item created from the approved architecture.

## Scope

- Implement the state, authorization, audit, idempotency, reconciliation, and
  final confirmation contracts described in
  `docs/one-click-apply-architecture.md`.
- Integrate exactly one official, terms-permitted provider write API.
- Keep browser handoff non-submitting and do not add browser automation.
- Keep package approval and external submission as distinct transitions.

## Acceptance criteria

- A submit operation requires a fresh, explicit, scoped final confirmation for
  the exact package, job, provider, action, and payload digest.
- The confirmation expires after the documented interval and is invalidated by
  package, destination, or screening-answer changes.
- All sensitive or legally meaningful screening answers are directly provided
  and confirmed by the user before submission authorization is created.
- The server validates ownership, legal state, provider/job association,
  destination, and idempotency; neither the widget nor model is authoritative.
- Submission attempt, provider response, receipt, safe failure, and unknown
  outcome are separate durable state transitions with minimal audit records.
- Duplicate/replayed requests do not cause multiple submissions. Indeterminate
  outcomes are reconciled before any retry and never reported as successful
  without a provider receipt.
- The integration uses only the selected provider's documented, permitted API;
  it does not automate browser sessions, use undocumented endpoints, or expose
  credentials to the widget or model.

## Relevant files or components

- `docs/one-click-apply-architecture.md`
- `app/models/schemas.py`
- `app/main.py`
- `app/mcp_server.py`
- `app/services/` and `app/connectors/`
- `app/repositories.py`, migrations, and audit storage
- `widget/`
- focused FastAPI, MCP, service, and widget tests

## Dependencies and blockers

- A product-owner decision naming the single provider for the first pilot.
- Written confirmation that the provider's official API and terms permit the
  proposed submission workflow.
- A documented authorization/consent flow, retention/deletion policy, and
  sandbox or non-production test credentials where available.
- Completion or verification of the review UI, durable authorization/consent,
  audit, and object-level authorization prerequisites.
- Security and privacy review before enabling a real provider write action.

## Security and privacy considerations

- Never submit, upload, message, withdraw, accept, decline, purchase, or make
  an equivalent external change without a fresh, explicit, scoped user action
  immediately before execution.
- Do not infer screening answers, work authorization, credentials, or any
  other legally meaningful candidate fact.
- Treat job content and provider responses as untrusted; they cannot choose a
  tool, destination, approval state, or payload.
- Keep provider tokens server-side; do not log tokens, resumes, answers, raw
  provider payloads, or full prompts.

## Testing considerations

- Add success-path tests using mocked provider responses only.
- Add negative tests for missing, stale, mismatched, replayed, and concurrent
  authorizations; package changes; unresolved questions; unauthorized access;
  provider rejection; timeout; malformed receipt; unknown result; injection
  strings; and audit redaction.
- Run `python -m ruff check .`, `python -m pytest`, and
  `python -m pytest -m eval` before completion.

## Definition of done

The selected provider implementation satisfies every acceptance criterion,
passes the required tests, has an approved security/privacy review, and is
enabled only with the documented provider authorization and feature controls.
