# Resume Ingestion Execution Plan

## Scope

Address issue #3 with a minimal, non-persistent ingestion path for PDF and DOCX resumes.

## Trust boundaries and data touched

- Uploaded resumes are untrusted user files and may contain PII.
- The API reads uploaded bytes only long enough to validate type and extract normalized text.
- The first implementation does not store raw files, extracted text, or metadata.

## External effects and approvals

- No external network calls are introduced.
- No application submission or externally consequential action is performed.
- User approval is not required for extraction, but downstream application approval remains separate.

## Implementation steps

1. Add a bounded upload endpoint for resume extraction.
2. Validate file type by content signature, not only filename or MIME type.
3. Extract text from PDF and DOCX using existing dependencies.
4. Return clear errors for unsupported, oversized, malformed, or text-empty files.
5. Add service and API tests for success and failure paths.
