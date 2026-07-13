# Resume Ingestion Execution Plan

## Scope

Address issue #3 with a minimal, non-persistent ingestion path for PDF and DOCX resumes.

## Trust boundaries and data touched

- Uploaded resumes are untrusted user files and may contain PII.
- The API reads uploaded bytes only long enough to validate type and extract normalized text.
- The first implementation does not store raw files, extracted text, or metadata.
- DOCX files are ZIP archives and must be validated before XML parsing to bound
  decompression work and reject unsafe member paths.

## External effects and approvals

- No external network calls are introduced.
- No application submission or externally consequential action is performed.
- User approval is not required for extraction, but downstream application approval remains separate.

## Implementation steps

1. Add a bounded upload endpoint for resume extraction.
2. Validate file type by content signature, not only filename or MIME type.
3. Before parsing a DOCX, enforce bounded ZIP member count, total uncompressed
   bytes, compression ratio, and safe member names.
4. Extract text from PDF and DOCX using existing dependencies.
5. Return clear errors for unsupported, oversized, malformed, unsafe, or
   text-empty files.
6. Add service and API tests for success and failure paths, including archive
   resource-exhaustion and path-traversal cases.
7. Expose the existing extraction endpoint in the same-origin browser workspace
   with a DOCX/PDF file picker. Validate the response at the browser boundary,
   keep the raw file out of browser storage, and require the user to review the
   extracted text before profile creation.

## Archive safety limits

- A DOCX archive may contain at most 256 file members.
- Its aggregate declared uncompressed size may not exceed 20 MiB.
- No individual file member may exceed a 100:1 declared compression ratio.
- Archive entries with absolute paths or parent-directory traversal are
  rejected. The application never extracts uploaded archives to disk.
