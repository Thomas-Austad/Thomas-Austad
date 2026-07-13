## Context and motivation

Once a qualified local provider, adapter, and onboarding flow are in place,
the project must no longer present paid OpenAI Platform access as a requirement
or retain a remote default that could transmit candidate data unexpectedly.

## Scope

- Remove the required OpenAI API key/model configuration, SDK dependency, and
  OpenAI-specific exception handling from the default local application path.
- Update README, local user guide, developer setup, operations runbook,
  example configuration, tests, and launcher language for the local model
  deployment.
- Audit the repository for obsolete remote-runtime references while preserving
  MCP/App SDK documentation that is unrelated to backend model inference.

## Acceptance criteria

- A clean local installation can run all supported application workflows with
  no OpenAI Platform account, API key, API credits, or outbound request to
  OpenAI.
- The default configuration selects only the qualified local provider and
  model; it has no implicit remote fallback.
- `pyproject.toml` contains no unnecessary OpenAI SDK runtime dependency after
  the local adapter migration.
- API routes map provider-neutral errors to safe, accurate recovery messages;
  no response tells a user to configure an OpenAI key or internet access for
  local inference.
- All user-facing prerequisites and recovery instructions accurately describe
  local hardware, disk, runtime, and model requirements.

## Relevant files or components

- `pyproject.toml`
- `.env.example`
- `README.md`
- `docs/local-run-and-use-guide.md`
- `docs/dev-setup.md`
- `docs/operations-runbook.md`
- `app/main.py`, `app/config.py`, `app/services/`
- `scripts/`, `tests/`

## Dependencies and blockers

- Depends on the provider boundary, Ollama adapter, local onboarding/health,
  and local-model safety qualification issues.
- Do not remove a dependency or documentation path until replacement behavior
  has passed the required checks.

## Security and privacy considerations

- Confirm through configuration and test doubles that no candidate data can be
  silently routed to a remote model service.
- Do not expose local runtime connection details or any credentials in the UI,
  logs, documentation examples, fixtures, or commits.

## Testing considerations

- Add regression tests proving clean local configuration requires no API key and
  performs no remote model call.
- Run `git diff --check`, `python -m ruff check .`, `python -m pytest`, and
  `python -m pytest -m eval` before completion.
