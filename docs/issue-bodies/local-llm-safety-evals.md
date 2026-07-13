## Context and motivation

Local model behavior varies by model, quantization, hardware, and runtime.
Talent Advisor cannot declare the migration safe merely because a local runtime
returns parseable JSON: the product must retain conservative matching,
evidence-grounded claims, prompt-injection resistance, and screening/approval
protections.

## Scope

- Extend the existing synthetic regression-evaluation plan with a local-model
  qualification suite and documented model/version test matrix.
- Define release gates for supported local model configurations, structured
  output reliability, and safety invariants.
- Provide a manual smoke-test protocol that uses only synthetic data and does
  not capture prompts, resumes, model responses, or other candidate PII.

## Acceptance criteria

- The suite covers profile extraction, job matching, compensation, and
  application preparation using synthetic fixtures.
- Tests assert schemas, evidence links, conservative recommendations,
  unsupported-claim rejection, unresolved sensitive screening questions,
  approval separation, and safe failure—not exact prose.
- Negative cases include prompt-injection strings in resumes/job listings,
  malformed JSON, partial outputs, context/output limit failures, unavailable
  runtime, model overload, and repeated/replayed preparation attempts.
- A documented qualification result identifies supported local runtime/model
  versions, quantization, minimum and recommended hardware, context setting,
  and known limitations.
- Unsupported model configurations are not represented as equivalent to a
  qualified configuration.

## Relevant files or components

- `docs/agent-regression-evals-plan.md`
- `tests/` and any pytest evaluation fixtures/markers
- `app/agents/`
- `app/services/`
- launcher and operations documentation

## Dependencies and blockers

- Depends on the Ollama adapter.
- Hardware qualification requires access to one or more representative local
  machines; all automated tests must use synthetic fixtures and mocked runtime
  responses unless an explicitly controlled local test environment is used.

## Security and privacy considerations

- Never use production resumes, profiles, screening answers, tokens, or raw
  provider payloads in evaluations or benchmark records.
- Do not weaken approval gates, evidence requirements, or screening protections
  to accommodate a local model's limitations.

## Testing considerations

- Run the focused evaluation suite, `python -m ruff check .`,
  `python -m pytest`, and `python -m pytest -m eval` before completion.
- Record only aggregate, non-sensitive pass/fail and latency information.
