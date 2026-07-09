## Context and motivation
The current profile flow requires raw pasted text. Real users will need to upload PDF and DOCX resumes directly, and the system needs a supported ingestion pipeline before it is practical.

## Acceptance criteria
- Users can submit PDF and DOCX resumes.
- The system extracts normalized text and basic metadata for downstream profile generation.
- Parsing failures return clear, actionable errors.
- Unsupported files are rejected safely.

## Relevant files or components
- `app/main.py`
- `app/services/document_service.py`
- `app/agents/profile_agent.py`
- upload/ingestion modules to be added

## Dependencies or blockers
- May depend on persistence decisions if source documents or extracted text are stored.
- Can be built in parallel with evidence-tracking work.

## Security considerations
- Validate file type by content, not extension alone.
- Enforce file size and decompression limits.
- Prevent path traversal and unsafe document handling.

## Testing considerations
- Add unit tests for PDF and DOCX extraction.
- Add negative tests for malformed, oversized, or unsupported files.
