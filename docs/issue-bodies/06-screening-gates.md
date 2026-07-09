## Context and motivation
Sensitive screening questions are a core trust boundary for this product. The platform must never guess legally meaningful or personal answers and must require direct user confirmation.

## Acceptance criteria
- Sensitive screening questions are identified and flagged.
- Application approval is blocked until required user input is resolved.
- Approval and consent decisions are stored durably.
- Unresolved items are shown clearly in the review experience.

## Relevant files or components
- `app/agents/application_agent.py`
- `app/main.py`
- `app/models/schemas.py`
- future UI flows in `widget/`

## Dependencies or blockers
- Depends on a review/approval workflow.
- Benefits from durable consent and audit storage.

## Security considerations
- Do not auto-fill or infer legal, demographic, disability, criminal-history, salary-history, or work-authorization answers.
- Preserve an auditable record of user confirmation for sensitive actions.

## Testing considerations
- Add negative tests proving unresolved questions block approval.
- Add regression tests ensuring generated answers do not bypass confirmation requirements.
