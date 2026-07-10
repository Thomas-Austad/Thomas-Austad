## Context and motivation

The runtime configuration defaults `OPENAI_MODEL` to `gpt-5.5`, while the
repository policy prohibits selecting that model unless explicitly requested or
required for documented compatibility. The checked-in environment template
already specifies `gpt-5.6`, so a new local installation that omits the setting
silently diverges from the documented configuration.

## Why this work is necessary

The default model is used for profile, matching, compensation, and application
preparation requests. A policy-compliant, documented default is needed before
the application can be used reliably without bespoke environment overrides.

## Bounded scope

- Align the `Settings.openai_model` default with the documented supported
  default.
- Add regression coverage for the default and explicit environment override.
- Document the model-selection policy and configuration behavior where users
  configure the application.

## Acceptance criteria

- A `Settings` instance with no `OPENAI_MODEL` override selects `gpt-5.6`.
- `OPENAI_MODEL` remains configurable through the existing settings mechanism.
- Configuration tests prevent drift between the runtime default and the example
  configuration.
- Repository documentation does not recommend or select `gpt-5.5` without a
  documented compatibility reason.

## Relevant files or components

- `app/config.py`
- `tests/test_config.py`
- `.env.example`
- `README.md`

## Dependencies or blockers

- None. This does not change credentials, billing, or external service access.

## Security and privacy considerations

- Keep model selection configurable without exposing API keys or customer data.
- Do not introduce fallback behavior that silently selects a disallowed model.

## Testing considerations

- Add focused settings tests for the default and explicit override.
- Run `python -m ruff check .` and `python -m pytest` before completion.

## Definition of done

- Acceptance criteria and required tests pass.
- The diff contains only issue-related configuration, documentation, and test
  changes.
- The change is committed, pushed to `main`, and summarized on this issue.
