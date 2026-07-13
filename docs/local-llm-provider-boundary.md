# Local LLM provider boundary

## Provider contract

Agents depend on `app.services.model_service.ModelService`, which supports
structured Pydantic output and plain text. Provider implementations must raise
only the provider-neutral `ModelServiceError` subclasses at the application
boundary. API responses use fixed recovery messages and never include prompts,
candidate data, model output, credentials, or provider internals.

Schema validation is not evidence validation or approval: existing agents keep
their prompt boundaries, evidence requirements, deterministic sensitive
screening gates, and application approval checks.

## Endpoint policy

`MODEL_PROVIDER` selects exactly one provider. The currently retained OpenAI
provider is selected only by `MODEL_PROVIDER=openai`; it is never used as a
fallback when a local provider fails. `MODEL_PROVIDER=ollama` reserves the
local provider path for the adapter delivered in issue #31 and fails closed
until that adapter is available.

Local runtime configuration is fixed process configuration, never HTTP, MCP,
or model input. `LOCAL_MODEL_BASE_URL` must be an HTTP or HTTPS URL with the
literal loopback host `localhost`, `127.0.0.1`, or `::1`; it cannot contain
credentials, paths, queries, fragments, or a non-loopback port. HTTP is
permitted only because the endpoint is loopback-only. Redirects, arbitrary
hosts, user-supplied headers, and user-controlled destinations are prohibited.

`LOCAL_MODEL_NAME`, connect/read timeouts, retry bound, output-token bound, and
context bound are validated settings. An Ollama selection requires a nonempty
model name, and output tokens may not exceed the context bound.

## Safe failure behavior

Unavailable runtimes, timeouts, overload, malformed output, and invalid
configuration are represented by distinct internal exceptions. They are safe
to retry only after the user corrects the local runtime/configuration or after
a transient condition clears. The future adapter must retain bounded requests,
no sensitive-content logging, strict schema validation, and no remote fallback.
