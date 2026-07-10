## Context and motivation
The current system prepares and approves application materials, but it does not yet provide a user-controlled assisted-apply workflow. For the platform to help beyond document preparation, externally consequential actions must be designed explicitly and kept separate from preparation.

## Acceptance criteria
- A concrete assisted-apply design is documented before implementation.
- Any submit, message, withdraw, accept, decline, upload, or equivalent external action requires explicit, current, scoped user approval.
- The apply workflow uses approved ATS/job-board APIs or a user-controlled browser assistant only where terms and access controls permit it.
- Prepared materials, user approval, submission attempt, provider response, and receipt/confirmation are tracked as separate state transitions.
- Duplicate submissions are prevented with idempotency keys or equivalent provider-safe controls.

## Relevant files or components
- `app/models/schemas.py`
- `app/main.py`
- `app/mcp_server.py`
- future apply services/connectors
- future UI surfaces in `widget/`
- audit and consent storage
- `docs/`

## Dependencies or blockers
- Depends on authentication, authorization, durable audit/consent, and review UI work.
- Provider capabilities and terms may limit what can be implemented safely.

## Security considerations
- Never submit, withdraw, message, purchase, accept, decline, delete, or otherwise perform an externally consequential action without explicit user approval immediately before execution.
- Do not infer legally meaningful or sensitive answers.
- Emit an audit receipt for every attempt and safe failure.

## Testing considerations
- Add tests proving prepare and submit remain separate operations.
- Add negative tests for missing approval, stale approval, duplicate/replayed requests, invalid state transitions, provider errors, and sensitive unanswered questions.
