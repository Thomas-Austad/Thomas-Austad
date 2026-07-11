# Issue #26 execution plan — widget application review and approval

## Scope and safety boundary

Application packages and screening answers may contain sensitive candidate data.
The widget will keep this data in disposable component state, render package
content as text, and send only direct user-entered screening answers through a
narrow MCP tool after a second confirmation. It will not infer an answer,
create a submission path, upload a document, contact an employer, or automate a
browser.

Approval is an audited local state transition, not application submission. The
widget will require a visually distinct confirmation immediately before the
write call, include a generated idempotency key, disable the approval control
while pending, and display an approved state only from a fresh server response.

## Implementation steps

1. Extract the existing screening-resolution and approval transitions into
   shared helpers so FastAPI and narrow MCP tools retain the same state checks,
   audit rollback, actor, and request/idempotency identifiers.
2. Add a read-only application-package MCP tool plus confirmation-gated
   screening-resolution and approval MCP tools. No submission tool is added.
3. Define validated package contracts and add an accessible application review
   view with preparation, unresolved-question, approved, empty, and safe-error
   states.
4. Add negative MCP/widget tests for missing confirmations, unresolved
   questions, repeat pending activation, malformed responses, and failed
   requests; then run the complete validation gate.

## Verification

- `pnpm --dir widget typecheck`
- `pnpm --dir widget test --run`
- `pnpm --dir widget build`
- `.venv\\Scripts\\python.exe -m ruff check .`
- `.venv\\Scripts\\python.exe -m pytest`
- `.venv\\Scripts\\python.exe -m pytest -m eval`
