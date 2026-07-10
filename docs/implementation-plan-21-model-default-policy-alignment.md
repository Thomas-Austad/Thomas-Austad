# Issue 21 implementation plan: model-default policy alignment

## Scope and trust boundaries

This change updates only the default model identifier used when a local user
has not supplied `OPENAI_MODEL`. It touches model-provider configuration but
does not send data, change credentials, or alter approval behavior.

## External effects and approvals

- No external request is made as part of the implementation.
- A local user can continue to choose a configured model through
  `OPENAI_MODEL`.
- No application submission or other consequential action is introduced.

## Implementation steps

1. Change the settings default to the documented model default.
2. Add tests for the default and a caller-supplied model override.
3. Update user-facing configuration documentation if it needs clarification.
4. Run the focused configuration test, then lint and the full test suite.

## Validation

- `.venv\\Scripts\\python.exe -m pytest tests/test_config.py`
- `.venv\\Scripts\\python.exe -m ruff check .`
- `.venv\\Scripts\\python.exe -m pytest`
