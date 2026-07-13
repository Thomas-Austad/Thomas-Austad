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

`MODEL_PROVIDER=ollama` selects the sole local-only Ollama adapter. No remote
provider or fallback exists; an unavailable configured runtime or model fails
closed.

Local runtime configuration is fixed process configuration, never HTTP, MCP,
or model input. `LOCAL_MODEL_BASE_URL` must be an HTTP or HTTPS URL with the
literal loopback host `localhost`, `127.0.0.1`, or `::1`; it cannot contain
credentials, paths, queries, fragments, or a non-loopback port. HTTP is
permitted only because the endpoint is loopback-only. Redirects, arbitrary
hosts, user-supplied headers, and user-controlled destinations are prohibited.

`LOCAL_MODEL_NAME`, connect/read timeouts, retry bound, request/response-byte
and output-token bounds, and context bound are validated settings. An Ollama
selection requires a nonempty model name. Output tokens reserve capacity within
the context limit, and request bytes cannot exceed the remaining context budget.

## Safe failure behavior

Unavailable runtimes, timeouts, overload, malformed output, and invalid
configuration are represented by distinct internal exceptions. They are safe
to retry only after the user corrects the local runtime/configuration or after
a transient condition clears. The adapter uses bounded requests, no
sensitive-content logging, strict schema validation, and no remote fallback.
