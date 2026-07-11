# Issue #11 completion plan — prepare package from a selected job

## Scope and safety boundary

The widget already supports profile review, job review, and review/approval of
an existing application package. This final step adds the missing transition:
the user explicitly asks to prepare a package for the selected job, and the
returned package opens in the Application review view.

Preparation remains distinct from approval and submission. It invokes only the
existing `prepare_job_application` MCP tool with the selected job and a
user-provided candidate ID; it sends no application to an employer and adds no
submission, messaging, upload, or browser-automation capability. Returned
model-generated content is runtime-validated and rendered as text by the
existing review view.

## Implementation steps

1. Add a typed, runtime-validated preparation client and normalize the MCP
   preparation response as JSON-compatible data.
2. Add a selected-job “Prepare application for review” action that requires a
   candidate ID, prevents duplicate activation while pending, and retains the
   selected job on safe failure.
3. Route a successfully prepared package directly into the Application review
   view without browser persistence; retain the manual package-load flow.
4. Add UI/MCP tests for successful handoff, missing candidate ID, malformed or
   failed preparation, and the continued absence of submission controls.

## Verification

- `pnpm --dir widget typecheck`
- `pnpm --dir widget test --run`
- `pnpm --dir widget build`
- `.venv\\Scripts\\python.exe -m ruff check .`
- `.venv\\Scripts\\python.exe -m pytest`
- `.venv\\Scripts\\python.exe -m pytest -m eval`
