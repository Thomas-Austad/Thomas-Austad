## Context and motivation

Issue #11 needs a user-facing widget, but the repository has no widget runtime,
component architecture, or documented HTTP/MCP contract for the local-first
application. Implementing feature screens before those decisions would create
inconsistent approval and authentication behavior.

## Why this work is necessary

A small, implementation-ready design is needed to make the widget work
incremental, accessible, and compatible with the local API/MCP boundaries.

## Bounded scope

- Document the selected widget runtime, TypeScript/tooling approach, and
  repository layout.
- Define the navigation, core user journeys, responsive layouts, and component
  boundaries for profile, jobs, matches, compensation, and applications.
- Map existing HTTP/MCP contracts to typed UI requests and responses.
- Define the local-auth, confirmation, error, and loading-state boundary.

## Acceptance criteria

- The design identifies the chosen UI runtime and build/test tooling with a
  documented rationale.
- It specifies typed contracts and error states for every existing core API
  workflow the widget will call.
- It distinguishes read-only review from consequential approval actions and
  requires an explicit confirmation interaction for the latter.
- It includes responsive and keyboard-accessible interaction requirements.
- It divides the remaining implementation into the child issues created from
  #11 without adding a second UI architecture.

## Relevant files or components

- `widget/`
- `app/main.py`
- `app/mcp_server.py`
- `app/models/schemas.py`
- `docs/`

## Dependencies or blockers

- Depends on the stable local API and authentication behavior already present.
- No provider integration or assisted-apply capability is selected here.

## Security and privacy considerations

- Keep API credentials and privileged logic outside browser-visible state.
- Render external job and profile text as text, never instructions or HTML.
- Make application approval distinct from preparation; do not add submission.

## Testing considerations

- Review the design against existing API tests and documented auth/approval
  boundaries.
- Validate referenced paths and commands, then run `git diff --check`.

## Definition of done

- A documented, implementation-ready UI architecture exists.
- It is consistent with #11 and its child issue dependencies.
- No application behavior, credentials, or external action is changed.
