# Issue 34 implementation plan: remove the OpenAI inference runtime

## Scope and trust boundaries

Candidate records and job data must remain on the configured loopback-only
local model path. Configuration, service construction, API recovery messages,
and setup documentation can otherwise route users toward a remote provider or
misrepresent the data boundary.

## External effects and approvals

- The application will make no OpenAI Platform inference request or fallback.
- Removing the SDK and provider path changes local dependencies only; it does
  not alter application approval, submission, retention, or audit state.
- MCP/App SDK documentation is retained where it concerns the UI integration
  rather than backend model inference.

## Implementation steps

1. Make the local Ollama provider/model the only validated application
   configuration and delete the remote service and factory branch.
2. Remove the OpenAI SDK dependency and provider-specific tests/errors.
3. Update setup and recovery documentation to state the local runtime, model,
   32 GB memory-class qualification floor, disk impact, and loopback-only
   boundary without retaining an OpenAI account or internet prerequisite.
4. Add regression tests proving a clean configuration selects only Ollama and
   that no remote provider service can be constructed.
5. Audit all remaining OpenAI mentions; retain only non-inference MCP/App SDK
   references with clear local-runtime wording.

## Validation

- Focused configuration, model-service, readiness, and documentation tests.
- `git diff --check`
- `python -m ruff check .`
- `python -m pytest`
- `python -m pytest -m eval`
