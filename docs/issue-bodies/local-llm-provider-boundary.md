## Context and motivation

Talent Advisor currently calls the OpenAI Responses API directly through
`OpenAIService`. A local model runtime must not become an unbounded or
user-controlled network client, and the application must preserve its typed
outputs, prompt-injection isolation, and truthful-claim safeguards.

Define the provider-neutral contract and local-runtime security policy before
implementing an adapter or changing the launcher.

## Scope

- Document and implement a typed internal model-service protocol used by all
  agents, including structured-output and plain-text operations where needed.
- Define a local-runtime configuration contract: provider kind, fixed loopback
  base URL, model identifier, connect/read timeout, retry limit, output limit,
  and bounded context policy.
- Define provider-neutral exception classes and safe recovery semantics for
  unavailable runtime, missing model, malformed output, timeout, and overload.
- Define the local endpoint trust boundary: HTTPS is not required for an
  authenticated loopback-only runtime, but arbitrary hosts, redirects,
  user-supplied headers, and user-controlled destination URLs are prohibited.

## Acceptance criteria

- Every agent depends on a typed internal protocol rather than an OpenAI SDK
  class or API-specific response type.
- The contract supports Pydantic-validated structured output without treating
  schema-valid model content as trusted evidence or user approval.
- Configuration rejects unsupported provider kinds, non-loopback local URLs,
  insecure schemes where applicable, and unbounded/invalid limits.
- Error classes do not expose prompts, candidate data, model output, endpoint
  credentials, or provider internals to API clients, logs, or audit records.
- The design records whether an optional remote provider remains supported; it
  must not be selected implicitly when local inference is unavailable.
- The architecture and security decision are documented in `docs/`.

## Relevant files or components

- `app/services/openai_service.py`
- `app/agents/`
- `app/config.py`
- `app/main.py`
- `docs/`
- focused service, configuration, and API error tests

## Dependencies and blockers

- No external credential is required.
- The selected first local runtime is Ollama unless a documented product-owner
  decision selects another compatible runtime.
- Subsequent adapter, launcher, documentation, and evaluation issues depend on
  this contract.

## Security and privacy considerations

- Candidate resumes, profiles, jobs, and generated materials stay on the local
  machine in local mode and must never be silently sent to a remote provider.
- Treat model output and runtime errors as untrusted data.
- Preserve existing prompt-boundary instructions, evidence requirements,
  sensitive-screening gates, approval gates, and minimal logging rules.

## Testing considerations

- Unit-test configuration validation, endpoint allowlisting, error mapping, and
  dependency injection with fakes.
- Include negative cases for private/non-loopback host bypasses, malformed URLs,
  output limits, injection-like source text, and no implicit remote fallback.
- Run `python -m ruff check .` and `python -m pytest` before completion.
