# Issue 31 implementation plan: Ollama local LLM adapter

## Scope and trust boundaries

This change adds the Ollama implementation of the internal model-service
contract. Resumes, profiles, jobs, screening questions, prompts, model output,
and runtime errors remain sensitive or untrusted. The adapter may contact only
the validated loopback runtime address from server configuration.

## External effects and approvals

- The adapter makes local-only inference requests to the selected Ollama model.
- It does not submit applications, change approval state, or make any remote
  model request or fallback.
- The user explicitly installed Ollama and downloaded `qwen3:8b`; smoke tests
  will use synthetic data and will not log prompts or generated content.

## Implementation steps

1. Implement a bounded `httpx` Ollama client using the provider-neutral
   contract, strict JSON-schema structured output, and provider-neutral errors.
2. Wire the factory to the explicit `ollama` configuration and preserve the
   existing evidence, screening, and approval gates in the agents.
3. Add mocked adapter tests for success, invalid output, network failures,
   overload, timeout, output-size limits, retry bounds, and fixed destination.
4. Add synthetic agent safety tests and execute a local smoke test against the
   installed loopback runtime without storing its prompt or response.

## Validation

- `.venv\\Scripts\\python.exe -m pytest tests/test_ollama_service.py tests/test_model_service.py tests/test_config.py`
- `.venv\\Scripts\\python.exe -m ruff check .`
- `.venv\\Scripts\\python.exe -m pytest -m eval`
- `.venv\\Scripts\\python.exe -m pytest`
