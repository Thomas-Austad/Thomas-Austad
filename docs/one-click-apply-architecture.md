# Consent-gated one-click apply architecture

Issue: #27

Status: proposed design; no submission capability is implemented or authorized
by this document.

## Purpose and scope

This design defines a future **one-click apply** operation for the Talent
Advisor Platform. It is deliberately narrower than general browser automation:
after an application package has been reviewed and approved, one explicit user
confirmation may cause the platform to submit that exact package through a
specific provider's approved write API.

The design does not authorize an implementation, submission, credential
collection, browser automation, document upload, messaging, withdrawal,
acceptance, decline, or any other external action. Browser handoff is the safe
initial delivery: it can open the employer's application page only after a
user action and never transfers credentials or submits on the user's behalf.

## Non-negotiable boundaries

- The final `Submit application` confirmation is the only operation described
  as one-click. It must name the employer, job, destination, exact documents,
  and any user-confirmed screening answers immediately before execution.
- No approval of a prepared package is approval to submit it. Preparation,
  approval, submission authorization, submission attempt, provider response,
  and receipt are separate server-owned transitions.
- Only a provider with documented write-API permission, a reviewed integration,
  and a valid user-granted authorization may receive a submission request.
  Otherwise the product must offer the browser-handoff flow or no action.
- The service must not automate a browser, bypass access controls, replay
  cookies, scrape authenticated pages, solve challenges, or use undocumented
  endpoints.
- Sensitive or legally meaningful questions require direct, per-question user
  input before the submission authorization can be issued; the product never
  guesses, pre-fills, or transmits an inferred answer.
- The API, not the widget or model, validates ownership, legal state,
  authorization freshness, destination, and idempotency. Untrusted job content
  cannot choose a provider, tool, payload, destination, or approval state.

## Preconditions

Before a provider-specific implementation can begin, the product owner must
approve all of the following for the selected provider:

1. The official API, terms, user-consent requirements, and permitted submission
   workflow.
2. The authorization method, permitted scopes, token storage/rotation, and
   revocation behavior. Credentials must be kept server-side and never exposed
   to the widget or model.
3. The provider's idempotency, duplicate-detection, document-upload, and
   receipt semantics.
4. Retention and deletion policy for provider identifiers, submission receipts,
   and error records.
5. A non-production test account or sandbox, where the provider offers one.

Without these approvals, the write capability remains disabled by default.

## State model

```text
prepared
  -> approved_locally
  -> submission_authorized
  -> submission_attempted
  -> submitted | submission_failed | submission_unknown
```

- `prepared`: materials are generated and reviewable.
- `approved_locally`: all required direct inputs are resolved and the package is
  locally approved; this has no external effect.
- `submission_authorized`: a fresh, scoped authorization exists for one package,
  destination, payload digest, and provider action. It is invalidated by any
  package, destination, or screening-answer change and expires after a short,
  configurable interval (recommended: 15 minutes).
- `submission_attempted`: a durable attempt receipt is recorded before the
  provider request. Replays reuse the same idempotency key and must return the
  known outcome rather than make a second attempt.
- `submitted`: the provider returned a verifiable receipt or application ID.
- `submission_failed`: the provider safely rejected or failed the request
  before a submission receipt was returned.
- `submission_unknown`: the network or provider response was indeterminate.
  The product must require a provider-status reconciliation before retrying and
  must not claim a submission succeeded.

Only documented legal transitions are permitted. Terminal outcomes are
immutable audit facts; a retry, when safe, is a new explicit authorization and
attempt linked to the original idempotency key and provider status check.

## Submission protocol

1. The user reviews the exact package and completes all direct screening
   confirmations.
2. The user approves the package locally.
3. The service verifies the requested provider/job association, current object
   ownership, provider availability, and server-calculated payload digest.
4. The widget presents a distinct final confirmation dialog using server
   supplied, validated destination and payload summary. The button is labelled
   `Submit application` and is disabled while pending.
5. The final confirmation creates a short-lived, single-purpose submission
   authorization bound to the package ID, provider, job ID, payload digest,
   action (`submit`), actor, expiry, and an idempotency key.
6. The service records `submission_attempted`, then invokes the approved
   provider adapter with bounded timeouts, size limits, and no user-controlled
   headers or URLs.
7. The service records the provider-safe outcome and returns a minimal receipt.
   Provider payloads, sensitive answers, resumes, access tokens, and full
   prompts must not be logged or included in audit events.

The browser-handoff alternative ends after step 3. Issue #20 implements this
non-submitting baseline: after local approval, the service validates a known
provider HTTPS destination and records a handoff receipt only after direct user
confirmation. It then returns a user-activated external link; all form
completion and submission remain in the user's browser. The service never
receives a provider response or claims a submission outcome for this path.

## Component boundaries

| Component | Responsibility | Prohibited responsibility |
| --- | --- | --- |
| `widget/` | Render state, collect a direct final confirmation, prevent repeated UI activation | Holding credentials, determining authorization, invoking arbitrary URLs |
| `app/mcp_server.py` | Expose narrow read and confirmation-gated tools with typed input/output | Accepting provider tokens or treating tool text as approval |
| `app/main.py` / domain service | Enforce ownership, state transitions, freshness, audit, and idempotency | Provider-specific HTTP parsing in routes |
| Provider adapter | Enforce a fixed official API host, payload schema, timeout, and receipt mapping | Following user-controlled URLs, redirects, or headers |
| Audit/repository layer | Persist minimal transition metadata and idempotency/reconciliation records | Persisting candidate documents, answers, tokens, or raw provider payloads in audit rows |

## Required validation

A future implementation must add focused tests for successful submission only
with a fresh scoped authorization, plus negative tests for missing/stale/wrong
authorization, package mutation, unresolved screening questions, duplicate or
concurrent requests, unauthorized object access, provider rejection, timeout,
malformed receipt, unknown result, prompt-injection text, and audit redaction.
It must run the repository completion gate: `python -m ruff check .`,
`python -m pytest`, and `python -m pytest -m eval`.

## Delivery sequence

1. **Complete (#20):** browser handoff is the non-submitting baseline.
2. Select and approve one official provider and its terms/API constraints.
3. Implement the server-side state, authorization, audit, idempotency, and
   reconciliation model with no provider write call enabled.
4. Add one reviewed provider adapter behind an explicit feature configuration.
5. Add the final confirmation UI and end-to-end sandbox tests.
6. Conduct a security and privacy review before enabling any real write action.
