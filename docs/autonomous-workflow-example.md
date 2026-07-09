# Example: Running the Autonomous Workflow

This example shows how to use the production-ready autonomous workflow in this
project.

## Start command

Ask Codex:

```text
Run the autonomous application development workflow for this repo. Work directly
on main and stop at the first defined stop condition.
```

That instruction activates `docs/autonomous-application-development-workflow.md`.
Without a command like this, ordinary coding requests should not start the
autonomous loop.

## What Codex should do first

Codex should begin with a preflight:

```bash
git status --short --branch
git pull --ff-only origin main
gh issue list --repo Thomas-Austad/Thomas-Austad --state open --limit 100 --json number,title,labels,body,url,assignees
```

If the branch is not `main`, the working tree contains unexplained changes, or
`main` cannot fast-forward, Codex should stop and report the problem.

## Example issue choice

If an open high-priority issue exists for adding authorization checks, Codex
should select it before lower-priority feature or documentation work because
authorization defects are release-blocking for this product.

If no suitable issue exists, Codex should create one bounded issue, for example:

```text
Title: Add audit events for application approval

Problem:
Application approval is externally consequential and should leave a durable,
reviewable audit trail.

Acceptance criteria:
- Approval emits an audit event with actor, action, target, timestamp, result,
  and request ID.
- Audit records do not include resumes, generated documents, screening answers,
  secrets, or unnecessary free text.
- Duplicate approval attempts are represented safely.
- Tests cover successful approval, duplicate approval, and audit redaction.
```

## Example implementation flow

For the selected issue, Codex should:

1. Read the issue, `AGENTS.md`, `README.md`, relevant docs, existing code, and
   tests.
2. Identify data touched, trust boundaries, external effects, and approval
   requirements.
3. Implement the smallest complete change.
4. Add or update meaningful automated tests.
5. Run:

```bash
ruff check .
pytest
```

6. Review the diff and staged files.
7. Commit only the issue-related files:

```bash
git add app tests docs
git commit -m "feat(audit): record application approval events (#123)"
git push origin main
```

8. Comment on issue `#123` with what changed, files modified, tests run,
   validation results, and the commit hash.
9. Close issue `#123`.
10. Continue to the next issue unless a stop condition has been reached.

## Example stop report

When the loop stops, Codex should summarize:

```text
Issues completed:
- #123 Add audit events for application approval

Issues created:
- #124 Add redaction tests for generated document errors

Commits pushed to main:
- abc1234 feat(audit): record application approval events (#123)

Tests and checks run:
- ruff check .
- pytest

Remaining open issues reviewed:
- #124 Add redaction tests for generated document errors

Blocked issues:
- None

Uncommitted local changes:
- None

Stop reason:
- No additional open actionable issue was ready without a product decision.
```

