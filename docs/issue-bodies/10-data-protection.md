## Context and motivation
Resumes, generated documents, and screening answers may contain sensitive personal data. Before broader use, the platform needs stronger at-rest protection and clear privacy lifecycle controls.

## Acceptance criteria
- Sensitive stored documents or fields are protected at rest.
- Data retention, export, and deletion behaviors are defined and implemented.
- Data handling expectations are documented for operators and users.

## Relevant files or components
- persistence/storage modules
- `app/config.py`
- document ingestion and generation services
- privacy documentation under `docs/`

## Dependencies or blockers
- Depends on persistence and document storage decisions.
- Should be designed alongside auth and audit work.

## Security considerations
- Protect personal data at rest and minimize retained content.
- Ensure encryption key handling does not leak secrets into source control or logs.

## Testing considerations
- Add tests for redaction, retention behavior, and export/delete flows where implemented.
- Validate that sensitive data is not exposed through logs or unsafe API responses.
