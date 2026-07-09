# GitHub Ticket Drafts

These issue drafts are sized to seed a Kanban board for the prime-time push.

Suggested labels:

- `roadmap`
- `backend`
- `frontend`
- `ai`
- `security`
- `infra`
- `testing`
- `priority-high`

## 1. Replace in-memory store with Postgres-backed repositories

**Suggested labels:** `backend`, `priority-high`

**Body:**

```md
## Summary
Replace the demo-only in-memory dictionaries in `app/store.py` with durable Postgres-backed repositories.

## Why
The current application loses all state on restart and is not suitable for real usage.

## Scope
- add a repository layer for profiles, jobs, matches, applications, and consent records
- wire persistence into the existing FastAPI endpoints
- remove direct runtime dependency on `app/store.py` for production flows
- align the persistence model with `sql/schema.sql`

## Acceptance criteria
- data persists across API restarts
- core endpoints read and write from Postgres
- repository interfaces are testable in isolation
- local Docker setup runs cleanly against the configured database
```

## 2. Add migrations and environment-safe database configuration

**Suggested labels:** `backend`, `infra`, `priority-high`

**Body:**

```md
## Summary
Introduce a migration workflow and clean up runtime configuration so local, test, and production environments use the right database safely.

## Why
The repo includes a schema and Docker database service, but the runtime still defaults to SQLite and lacks a migration path.

## Scope
- add a migration tool and initial migration set
- normalize `DATABASE_URL` handling across app, tests, and Docker
- document setup for local development
- add startup checks for missing or invalid database config

## Acceptance criteria
- schema changes can be applied and rolled forward through migrations
- Docker and local runtime use consistent configuration
- developers can bootstrap the database without manual SQL execution
```

## 3. Support PDF and DOCX resume ingestion

**Suggested labels:** `backend`, `priority-high`

**Body:**

```md
## Summary
Allow users to upload PDF and DOCX resumes instead of pasting raw text.

## Why
Pasted text is fine for demos, but not for real-world use or reliable extraction.

## Scope
- add upload endpoints or ingestion services for PDF and DOCX files
- extract normalized text and basic metadata
- handle parsing failures and unsupported files gracefully
- prepare the output for downstream profile generation

## Acceptance criteria
- users can submit PDF and DOCX resumes
- extracted text is available to the profile pipeline
- failures return clear, actionable errors
```

## 4. Persist evidence records for extracted candidate claims

**Suggested labels:** `backend`, `ai`, `priority-high`

**Body:**

```md
## Summary
Store evidence snippets and confidence metadata for profile claims so the system can justify what it inferred.

## Why
The product promise is evidence-grounded output. That needs durable evidence records, not just generated summaries.

## Scope
- persist evidence records tied to candidate profiles
- link extracted skills, experience, and ambiguities to source snippets
- surface low-confidence and conflicting evidence cleanly

## Acceptance criteria
- profile claims can be traced back to stored evidence
- ambiguous or weakly supported claims are clearly marked
- downstream features can access evidence without reparsing source files
```

## 5. Build a profile review and correction workflow

**Suggested labels:** `frontend`, `backend`, `priority-high`

**Body:**

```md
## Summary
Create a user-facing workflow to review, correct, and approve generated candidate profiles before they are used downstream.

## Why
A trustworthy career product cannot treat model output as final without user review.

## Scope
- render profile sections, skills, experience, and ambiguities for review
- allow user corrections and preference updates
- store corrections durably
- preserve a distinction between source evidence and user edits

## Acceptance criteria
- users can inspect and correct generated profiles
- corrections persist across sessions
- downstream match and application flows use the corrected profile
```

## 6. Add application review gating for sensitive screening questions

**Suggested labels:** `backend`, `frontend`, `security`, `priority-high`

**Body:**

```md
## Summary
Enforce explicit user confirmation for personal, legal, demographic, disability, criminal-history, salary-history, and work-authorization questions.

## Why
This is a core product boundary and the most important trust safeguard in the application flow.

## Scope
- classify and flag sensitive screening questions
- block approval until required user input is resolved
- persist the approval and consent decision
- expose unresolved items clearly in the review experience

## Acceptance criteria
- sensitive questions never pass through as guessed answers
- application approval is blocked until required confirmations are complete
- consent and approval state are stored durably
```

## 7. Add agent regression fixtures and evaluation harness

**Suggested labels:** `ai`, `testing`, `priority-high`

**Body:**

```md
## Summary
Create a repeatable evaluation harness for profile generation, match scoring, compensation estimation, and application drafting.

## Why
The current system depends heavily on model behavior without a regression safety net.

## Scope
- add representative candidate/job fixtures
- cover strong-fit, weak-fit, missing-evidence, over-level, and salary-mismatch scenarios
- add assertions for schema quality and core behavioral rules
- make eval runs easy to execute locally and in CI

## Acceptance criteria
- critical agent behaviors are checked against known scenarios
- regressions are visible before release
- results can be run as part of CI or release validation
```

## 8. Expand automated test coverage for core workflows and failures

**Suggested labels:** `testing`, `backend`

**Body:**

```md
## Summary
Add meaningful unit and integration tests across the platform's main workflows and failure cases.

## Why
Current test coverage is too light for dependable use.

## Scope
- add unit tests for services and agent boundaries
- add integration tests for profile -> jobs -> match -> compensation -> application -> approval
- add failure-path tests for missing data, connector failures, and model errors
- cover MCP tool surface contracts where practical

## Acceptance criteria
- happy-path and failure-path flows are both tested
- core regressions are caught automatically
- tests are easy to run locally and in CI
```

## 9. Add authentication, authorization, and audit logging

**Suggested labels:** `security`, `backend`, `priority-high`

**Body:**

```md
## Summary
Add authentication and per-user access control, plus an audit trail for high-risk actions.

## Why
The platform handles sensitive personal data and approval-driven workflows.

## Scope
- add user authentication
- enforce per-user access to profiles, jobs, matches, and applications
- record audit events for profile creation, edits, approvals, and future submission steps
- protect APIs and MCP surfaces appropriately

## Acceptance criteria
- users can only access their own data
- high-risk actions create durable audit records
- unauthorized access attempts are blocked and observable
```

## 10. Protect stored personal data and uploaded documents

**Suggested labels:** `security`, `backend`

**Body:**

```md
## Summary
Introduce encryption and privacy controls for stored personal data and user-uploaded artifacts.

## Why
Resumes, application materials, and personal responses should not be stored casually.

## Scope
- encrypt stored sensitive documents and fields
- define retention, export, and deletion behavior
- document data handling expectations

## Acceptance criteria
- sensitive data is protected at rest
- users have a clear path to export or delete their data
- retention behavior is explicit and testable
```

## 11. Build the widget/UI for end-to-end application workflow

**Suggested labels:** `frontend`, `priority-high`

**Body:**

```md
## Summary
Build the missing user-facing interface for profile review, job browsing, match inspection, compensation review, and application approval.

## Why
The backend proves the concept, but the product is not usable day-to-day without a real interface.

## Scope
- implement views for candidate profile, jobs, matches, compensation, and applications
- show unresolved questions and approval gates clearly
- preserve the existing product boundary around truthful, user-controlled apply flows

## Acceptance criteria
- a user can complete the core workflow without manually calling raw endpoints
- review and approval states are visible and understandable
- UI works on desktop and mobile layouts
```

## 12. Add observability, retries, and release hardening

**Suggested labels:** `infra`, `backend`

**Body:**

```md
## Summary
Add the operational safeguards needed to run the platform reliably in private beta and beyond.

## Why
The app depends on external APIs, model calls, and document processing; failures need visibility and safe recovery behavior.

## Scope
- add structured logging and basic metrics
- add retries and timeouts for model and ATS connector calls
- add rate limiting and backoff where appropriate
- document deployment, environment setup, and operational runbooks
- set up CI for tests and linting

## Acceptance criteria
- failures are visible and diagnosable
- external dependency issues do not cause silent corruption
- CI validates the main quality gates before release
```

## Suggested Initial Kanban Columns

- `Backlog`
- `Ready`
- `In Progress`
- `Blocked`
- `In Review`
- `Done`

## Suggested First Sprint

Start with these four tickets:

1. Replace in-memory store with Postgres-backed repositories
2. Add migrations and environment-safe database configuration
3. Support PDF and DOCX resume ingestion
4. Persist evidence records for extracted candidate claims
