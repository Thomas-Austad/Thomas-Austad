# Issue 16 implementation plan: API rate limiting and abuse controls

## Scope

Add coarse, configurable, in-process API abuse controls without introducing a
new dependency or changing the public workflow semantics.

## Trust boundaries

- Request bodies, query parameters, filenames, resumes, job-source identifiers,
  title keywords, and screening answers are untrusted input.
- Rate-limit events must not log resumes, screening answers, prompts, generated
  documents, or provider payloads.
- These controls are process-local and are not a substitute for authenticated,
  per-user production rate limiting.

## Implementation steps

1. Add settings for rate-limit enablement, fixed-window duration, and per-route
   category limits.
2. Add a small in-memory fixed-window limiter used by FastAPI middleware.
3. Categorize upload, job search, model-backed, document-generation, and
   approval-like write endpoints.
4. Add Pydantic/FastAPI bounds for large text fields, list sizes, and query
   parameters.
5. Document local/deployment configuration and add focused tests.

## Validation

- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest`
