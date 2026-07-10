## Context and motivation

The widget needs a secure, accessible shell before feature screens can consume
candidate or application data. There is currently no `widget/` implementation.

## Why this work is necessary

Shared runtime validation, navigation, status handling, and typed API access
prevent each feature screen from inventing its own security and error behavior.

## Bounded scope

- Scaffold the runtime selected in #22 with TypeScript strict mode.
- Add the typed, validated client boundary for approved local API/MCP calls.
- Implement an accessible responsive shell, navigation, loading, error, and
  empty states.
- Establish reusable components for read-only status and explicit confirmation.

## Acceptance criteria

- The widget compiles and tests with the chosen repository tooling.
- Cross-boundary inputs and responses are runtime-validated.
- No secret or bearer credential is stored in `localStorage` or rendered in the
  UI.
- Navigation, status, focus, and keyboard behavior are accessible on desktop
  and mobile layouts.
- The shell contains no application submission capability.

## Relevant files or components

- `widget/`
- `app/main.py`
- `app/mcp_server.py`
- `app/models/schemas.py`

## Dependencies or blockers

- Depends on #22 for the approved runtime and contract design.

## Security and privacy considerations

- Keep all privileged credentials server-side or in the approved bridge.
- Validate bridge/network messages and render external strings as text.

## Testing considerations

- Add unit tests for validation, navigation, error handling, and confirmation
  primitives.
- Run the selected widget checks plus the existing backend completion gate.

## Definition of done

- A secure reusable shell is available for the profile, job, and application
  child issues without duplicating access-control or confirmation logic.
