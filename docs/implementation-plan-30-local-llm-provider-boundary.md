# Issue 30 implementation plan: local LLM provider boundary

## Scope and trust boundaries

This change establishes a typed internal model-service contract and a
configuration policy for a future Ollama adapter. Candidate records, resumes,
job listings, screening questions, and generated materials remain untrusted or
sensitive inputs. The local runtime endpoint is a network trust boundary even
when it is intended to be loopback-only.

## External effects and approvals

- No provider, runtime, or model is installed, downloaded, or contacted by this
  change.
- The existing OpenAI integration remains available only when the operator
  explicitly selects it; an unavailable local provider never falls back to it.
- This change does not alter application approval, submission, retention, or
  audit behavior.

## Implementation steps

1. Define a provider-neutral typed protocol, safe exception hierarchy, and
   factory for model services.
2. Change agents to depend on that protocol rather than the OpenAI service
   class, and translate provider errors to non-sensitive API recovery messages.
3. Add validated local-runtime settings for provider kind, loopback endpoint,
   model identifier, timeouts, retries, output limit, and context limit.
4. Document the endpoint policy and explicitly defer the Ollama implementation
   to issue #31; add focused configuration, factory, and API error tests.

## Validation

- `.venv\\Scripts\\python.exe -m pytest tests/test_config.py tests/test_model_service.py tests/test_profile_service_errors.py`
- `.venv\\Scripts\\python.exe -m ruff check .`
- `.venv\\Scripts\\python.exe -m pytest`
- `.venv\\Scripts\\python.exe -m pytest -m eval`
