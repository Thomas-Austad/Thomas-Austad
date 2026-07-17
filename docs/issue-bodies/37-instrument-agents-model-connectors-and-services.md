## Context and motivation

The model/agent pipeline and job connectors are the most important diagnostic
boundaries for this local-first application. They handle sensitive candidate
material and untrusted external responses, so they need verbose operational
metadata without ever capturing prompt, resume, job-description, or provider
payload content.

## Scope

- Add safe lifecycle instrumentation to profile, match, compensation, and
  application agents; prompt-safety handling; model-service selection; and
  Ollama/local-model readiness calls.
- Add safe instrumentation to Greenhouse, Lever, Ashby, and shared HTTP
  connector paths, including retry attempt/outcome, timeout category,
  response-size limit outcome, normalization/filter/dedup counts, and provider
  error class.
- Add safe events for data-protection and privacy-migration services where
  present, and for any other application service not covered by the API/MCP
  workflow issue.
- Make event names/counts sufficiently consistent to diagnose where a
  pipeline stopped, while preserving current retry bounds and safe failure
  behavior.
- Extend the operations runbook event inventory and troubleshooting guidance.

## Acceptance criteria

- Each agent and service boundary emits safe start/completion/failure events
  with correlation ID, operation name, duration where measurable, and a
  bounded error/outcome category.
- Connector events identify the provider, safe retry attempt number, and
  count/limit outcome, but never board keys, company names, request URLs,
  headers, raw response bodies, job descriptions, or provider error text.
- Model events identify the local provider/operation and safe request/output
  size category, schema-validation outcome, and timeout/availability class,
  but never system/user prompts, resume/profile content, screening content,
  generated output, or model responses.
- Prompt-injection detections are observable as a category only; malicious or
  untrusted source text is never copied into logs.
- Logging does not change matching, evidence grounding, screening gates,
  timeout/retry policy, or model/connector control flow.
- Focused tests capture logs for model errors, malformed responses, connector
  errors/retries, and injection strings, proving sensitive content is absent.

## Relevant files or components

- `app/agents/`, including `prompt_safety.py`
- `app/services/ollama_service.py`, `model_service.py`,
  `local_model_readiness_service.py`, `job_service.py`, and
  `data_protection_service.py`
- `app/connectors/`, including `http.py`, `greenhouse.py`, `lever.py`, and
  `ashby.py`
- service, connector, prompt-safety, and agent regression tests
- `docs/operations-runbook.md`

## Dependencies or blockers

- Depends on the privacy-safe logging foundation issue.
- Coordinate event vocabulary with the API/MCP instrumentation issue, but the
  two implementation efforts may proceed independently after the foundation.

## Security considerations

- Treat resumes, LinkedIn exports, job content, provider responses, and model
  output as untrusted and sensitive content, never as logging fields.
- Do not log local provider URLs if they contain credentials, or exception
  strings before they have passed through the approved safe categorization.
- Logging must not influence tools, destinations, approval state, or retries.

## Testing considerations

- Mock model and provider calls; do not use local production data or real
  credentials.
- Include injection-like strings, private URLs, provider error bodies, and
  oversized responses in redaction/absence assertions.
- Run `python -m ruff check .`, `python -m pytest`, and
  `python -m pytest -m eval` before completion.
