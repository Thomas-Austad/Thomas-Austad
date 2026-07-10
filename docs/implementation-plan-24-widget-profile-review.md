# Issue #24 execution plan — widget profile review and correction

## Scope and safety boundary

The profile review contains candidate information and evidence from untrusted
sources. The widget will render that data only as text after runtime validation,
will not persist it in the browser, and will send no direct HTTP requests. A
correction is limited to a directly user-entered profile field, is shown in an
explicit confirmation step, and is then sent through the existing
`correct_candidate_profile` MCP tool with its existing confirmation contract.

This work does not change candidate-generation, provenance, ownership,
approval, audit, or retention semantics.

## Implementation steps

1. Define runtime-validated profile-review and correction contracts for the
   widget's MCP client boundary.
2. Add a keyboard-accessible profile review view with loading, empty, error,
   evidence, ambiguity, past-correction, and correction-confirmation states.
3. Expose the existing correction tool to the widget resource and retain its
   server-side confirmation requirement.
4. Add focused widget and MCP metadata tests, then run widget checks and the
   repository completion gate.

## Verification

- `pnpm --dir widget typecheck`
- `pnpm --dir widget test --run`
- `pnpm --dir widget build`
- `.venv\\Scripts\\python.exe -m ruff check .`
- `.venv\\Scripts\\python.exe -m pytest`
- `.venv\\Scripts\\python.exe -m pytest -m eval`
