# Codex Usage Policy Implementation Plan

## Objective

Add repository-specific Codex model-routing, context, retry, validation, and
blocked-work guidance while preserving the Talent Advisor Platform's existing
security, privacy, issue-tracking, and autonomous-workflow rules.

## Repository findings

- The repository is a 113-file Python 3.11+ FastAPI MVP with Pydantic,
  SQLAlchemy/Alembic, HTTPX connectors, OpenAI Responses API integration, MCP,
  PostgreSQL, and a future TypeScript widget.
- CI runs Ruff, the full pytest suite, and the synthetic eval subset. The
  operations runbook adds an offline Alembic SQL rendering check.
- The main risks are candidate PII, evidence-grounded claims, screening and
  approval gates, authentication/authorization, audit records, untrusted ATS
  content, SSRF, document processing, database constraints, and external
  consequential actions.
- The autonomous workflow works directly on `main`, selects a single actionable
  GitHub issue, and has explicit stop conditions. Existing open issues are
  mainly high-risk or cross-system work.
- Generated/local material includes `.venv/`, `.env`, Python caches, Ruff and
  pytest caches, egg-info, `var/`, and Docker database volumes; these should not
  enter routine context or commits.

## Implementation steps

1. Add a concise task-assessment and model-routing section to the root
   `AGENTS.md`, with Terra/medium as the normal implementation default and
   evidence-based Luna and Sol conditions.
2. Add project-specific context, retry, escalation, blocked-work, and
   validation guidance that refers to the existing CI and runbook commands.
3. Extend the root issue/autonomous guidance with model-routing and bounded
   issue-loop checkpoints, without changing its explicit activation or
   main-branch rules.
4. Do not add nested `AGENTS.md` files: the present source directories are
   small, tightly coupled, and already covered by the root security rules.
5. Review the diff and verify the documented paths and commands exist. Run a
   lightweight instruction-content check rather than application tests because
   this change only updates repository instructions.

## Trust boundaries and external effects

The policy must not weaken candidate-data handling, approval gates, model-output
validation, GitHub write rules, or account usage limits. It documents that
model-switching depends on the active Codex environment and may need user or
orchestrator action; it does not grant agents authority to change models,
credentials, billing, or GitHub state.
