## Context and motivation
The backend demonstrates the concept, but the platform is not practical for day-to-day use without a real interface for profile review, job browsing, match inspection, compensation review, and application approval.

## Acceptance criteria
- A user can complete the core workflow without manually orchestrating raw API calls.
- Review and approval states are visible and understandable.
- The UI works on desktop and mobile layouts.
- The interface preserves the truthful, user-controlled apply boundary.

## Relevant files or components
- `widget/`
- `app/main.py`
- `app/mcp_server.py`
- supporting API contracts and schemas

## Dependencies or blockers
- Depends on the review workflow and stable backend contracts.
- Benefits from persistence and auth being in place first.

## Security considerations
- Do not expose secrets or privileged logic to the client.
- Make consequential write actions visually distinct and confirmation-gated.

## Testing considerations
- Add front-end tests for core workflow states and approval gating.
- Add integration coverage for UI-to-API contract behavior where practical.
