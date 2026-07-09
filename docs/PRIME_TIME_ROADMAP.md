# Prime-Time Roadmap

## Goal

Take the Talent Advisor Platform from local MVP/demo quality to dependable private-beta and production-ready quality.

The platform should be considered prime-time when it:

- persists user and application data reliably
- allows review and correction of important AI-generated outputs
- never guesses or submits legally meaningful answers without explicit user confirmation
- has strong automated test coverage across core workflows
- enforces authentication, audit, and privacy controls
- provides enough observability and operational safeguards to run predictably

## Current State

The repo already proves the core concept:

- candidate profile generation
- job ingestion from Greenhouse and Lever
- match scoring
- compensation estimation
- application package drafting
- DOCX resume export
- MCP tool surface for ChatGPT

The main blockers to prime time are:

- in-memory persistence instead of database-backed repositories
- no end-user review and correction flow
- limited automated tests
- no authentication or production-grade privacy controls
- no operational hardening for failures, retries, metrics, and deployment

## Milestones

### Milestone 1: Persistence and data integrity

Replace demo-state storage with durable persistence and clean repository boundaries.

Deliverables:

- SQLAlchemy models or equivalent repository layer aligned to `sql/schema.sql`
- migration workflow
- Postgres wired into application runtime
- durable storage for profiles, jobs, matches, applications, and consent records
- transactional write paths and structured persistence errors

Exit criteria:

- restarting the API does not lose user state
- application endpoints read and write from Postgres instead of `app/store.py`
- the local Docker stack starts cleanly against the configured database

### Milestone 2: Document ingestion and evidence pipeline

Support real source documents and durable evidence tracking.

Deliverables:

- PDF resume parsing
- DOCX resume parsing
- ingestion pipeline that extracts source text and metadata
- evidence records tied to extracted skills, roles, dates, and claims
- stored artifacts and source references for later review

Exit criteria:

- a user can upload a resume instead of pasting raw text
- generated profile claims can be traced back to source snippets
- low-confidence or conflicting extractions are surfaced clearly

### Milestone 3: Review and approval workflow

Add the user control layer that keeps the platform trustworthy.

Deliverables:

- profile review and correction flow
- match review with explanation of score, gaps, and disqualifiers
- compensation review with visible assumptions and confidence
- application package review for resume, cover letter, and screening responses
- explicit unresolved-input gating for sensitive questions

Exit criteria:

- every important AI-generated artifact can be reviewed before downstream use
- sensitive answers always require explicit user confirmation
- approval state is durable and auditable

### Milestone 4: Model quality and test coverage

Make outputs more reliable and measurable.

Deliverables:

- stronger structured prompts and schemas
- regression fixtures for representative candidate/job scenarios
- unit tests for services and agent boundaries
- integration tests for the core end-to-end flow
- fallback handling for model or connector failures

Exit criteria:

- happy-path and failure-path flows are covered by automated tests
- agent regressions can be caught before release
- model failures degrade gracefully instead of breaking the workflow

### Milestone 5: Security, privacy, and trust

Protect personal data and make the workflow safe to operate.

Deliverables:

- authentication and per-user authorization
- audit trail for profile creation, approvals, and future submission actions
- encryption for stored sensitive files and personal data
- prompt-injection isolation for job content
- privacy controls for export, retention, and deletion

Exit criteria:

- only authorized users can access their own data
- high-risk actions are auditable
- job content cannot directly manipulate downstream model behavior

### Milestone 6: UI and MCP product surface

Complete the user-facing experience.

Deliverables:

- widget/UI for profile, jobs, matches, compensation, and application review
- shared business logic between HTTP and MCP flows
- application pipeline/status views
- clearer API and tool contracts

Exit criteria:

- the product can be used without manually orchestrating raw API calls
- MCP and HTTP paths produce consistent outcomes

### Milestone 7: Reliability and operations

Prepare the system to run predictably.

Deliverables:

- structured logging, metrics, and alertable errors
- retry and timeout policies for connectors and model calls
- rate limiting and backoff
- CI for tests and linting
- deployment and environment documentation
- private beta hardening pass

Exit criteria:

- failures are visible and diagnosable
- deployments are repeatable
- the system can survive expected dependency failures without silent corruption

## Recommended Build Order

1. Persistence and migrations
2. Document ingestion and evidence
3. Review and approval workflow
4. Test coverage and evaluation harness
5. Security and privacy controls
6. UI completion
7. Operational hardening and beta release

## Definition of Done

The platform is ready for prime time when a user can:

1. upload source documents
2. generate and correct their profile
3. search and review jobs
4. inspect fit and compensation recommendations
5. prepare a truthful application package
6. explicitly approve sensitive answers
7. return later without losing data or trust in the system
