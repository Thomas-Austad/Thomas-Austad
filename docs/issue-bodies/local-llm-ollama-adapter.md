## Context and motivation

After the provider contract is established, Talent Advisor needs a local model
implementation that can run without OpenAI Platform credits. Ollama is the
initial runtime because it provides a supported local service model suitable
for a Windows desktop installation.

## Scope

- Implement an Ollama-backed local model service behind the provider-neutral
  contract.
- Support strict JSON/schema-constrained structured generation, bounded model
  output, Pydantic parsing, and safe rejection of malformed or incomplete
  responses.
- Apply explicit connect/read timeouts, bounded retries, request correlation,
  and no sensitive-content logging.
- Wire all current profile, match, compensation, and application agents to the
  provider-neutral service without weakening their prompt boundaries or
  deterministic screening-question gates.

## Acceptance criteria

- A configured, running local Ollama runtime can complete each existing agent
  workflow without an OpenAI API key or external model request.
- Every structured response is validated against its existing Pydantic schema;
  invalid JSON, missing fields, extra/unexpected content, and empty output fail
  safely without persisting a profile, match, estimate, or package.
- Request size, output size, context size, timeouts, and retries are bounded
  by configuration and produce provider-neutral safe errors.
- The adapter uses only the fixed, validated local runtime configuration and
  never accepts a runtime URL, headers, or credentials from an HTTP/MCP user or
  model content.
- Agent-level evidence, claim-traceability, approval, and sensitive-screening
  protections behave identically or more conservatively than before.

## Relevant files or components

- `app/services/`
- `app/agents/profile_agent.py`
- `app/agents/match_agent.py`
- `app/agents/compensation_agent.py`
- `app/agents/application_agent.py`
- `app/config.py`
- `app/main.py`
- `tests/`

## Dependencies and blockers

- Depends on the local LLM provider-boundary issue.
- Requires Ollama's local API and a locally downloaded compatible model during
  manual smoke testing; unit tests must mock the runtime and need no model.

## Security and privacy considerations

- Do not log resumes, profile text, prompts, screening answers, generated
  documents, raw model responses, or local runtime authorization values.
- Model output cannot authorize submission, answer sensitive questions, or add
  unsupported candidate facts.
- Fail closed when the local runtime is absent or returns malformed content;
  never silently call a remote service.

## Testing considerations

- Add mocked success, timeout, connection failure, overload, malformed JSON,
  schema mismatch, output-limit, and retry-boundary tests.
- Add agent tests proving unsupported claims and sensitive answers are not
  persisted after local-model output.
- Run `python -m ruff check .`, `python -m pytest`, and
  `python -m pytest -m eval` before completion.
