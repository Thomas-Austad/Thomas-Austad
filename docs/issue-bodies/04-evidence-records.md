## Context and motivation
The product promise is evidence-grounded output. Today, the system generates a profile but does not persist durable evidence records tying claims back to source text.

## Acceptance criteria
- Evidence snippets and confidence metadata are stored for extracted claims.
- Skills, experience items, and ambiguities can be traced back to source snippets.
- Downstream features can access evidence without reparsing source files.
- Weak or conflicting evidence is surfaced clearly.

## Relevant files or components
- `app/models/schemas.py`
- `app/agents/profile_agent.py`
- `sql/schema.sql`
- future evidence persistence modules

## Dependencies or blockers
- Depends on persistence work.
- Benefits from document ingestion being available.

## Security considerations
- Evidence storage may contain sensitive personal data and must follow least-retention principles.
- Avoid exposing raw evidence broadly in logs or error messages.

## Testing considerations
- Add tests that confirm profile claims map back to stored evidence.
- Add edge cases for conflicting or low-confidence evidence.
