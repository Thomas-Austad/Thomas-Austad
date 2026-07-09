## Context and motivation
Current automated coverage is minimal and not enough for dependable use. The core API and agent flows need broader happy-path and failure-path tests.

## Acceptance criteria
- Unit tests cover services and key agent boundaries.
- Integration tests cover profile -> jobs -> match -> compensation -> application -> approval.
- Failure-path tests cover missing data, connector failures, and model failures.
- MCP tool surface contracts are covered where practical.

## Relevant files or components
- `tests/`
- `app/main.py`
- `app/mcp_server.py`
- `app/services/`
- `app/agents/`

## Dependencies or blockers
- Can start immediately, but some tests depend on persistence and workflow hardening.
- May share fixtures with eval work.

## Security considerations
- Include negative tests for unauthorized access, malformed input, and duplicate or replayed actions as auth and write paths mature.
- Ensure tests do not log or persist sensitive fixture data beyond what is needed.

## Testing considerations
- This issue is itself about testing coverage and should result in measurable new tests.
- Prioritize stable assertions on schemas, invariants, and state transitions.
