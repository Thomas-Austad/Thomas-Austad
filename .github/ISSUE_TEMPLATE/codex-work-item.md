---
name: Codex work item
about: A bounded implementation task for the autonomous development workflow
title: ""
labels: codex-work-item
assignees: ""
---

## Problem or Required Capability

Describe the defect, gap, or capability in concrete terms.

## Why This Is Necessary

Explain the production, security, privacy, correctness, user, or maintainability
reason for doing this now.

## Bounded Scope

List what is included and what is explicitly out of scope.

## Acceptance Criteria

- [ ] The expected behavior is implemented.
- [ ] Relevant failure or abuse paths are handled.
- [ ] Public behavior, setup, configuration, or schemas are documented when they
      change.

## Required Testing

- [ ] Unit tests cover the primary behavior.
- [ ] Failure-path or edge-case tests are included where relevant.
- [ ] `ruff check .` passes.
- [ ] `pytest` passes.

## Relevant Files or Components

List known files, packages, endpoints, services, docs, or tests likely to be
involved.

## Dependencies or Blockers

List dependencies, unavailable decisions, required secrets, upstream issues, or
blocking work. Write `None` if there are no known blockers.

## Security and Privacy Considerations

Describe data touched, trust boundaries, authorization behavior, approval
requirements, logging/audit impact, and secret or PII handling.

## Definition of Done

- [ ] Acceptance criteria are satisfied.
- [ ] Tests and required checks pass.
- [ ] Documentation is current.
- [ ] No secrets, PII, generated artifacts, caches, or unrelated files are
      committed.
- [ ] Completion summary is posted before the issue is closed.

