# Local LLM qualification record

## Qualified configuration

This is a bounded, single-host qualification for the local development path.
It does not qualify remote providers, other Ollama versions, model tags,
quantizations, operating systems, or hardware configurations.

| Item | Qualified value |
| --- | --- |
| Runtime | Ollama 0.31.2 |
| Model | `qwen3:8b` (`500a1f067a9f`) |
| Model details | Qwen3, 8.2B parameters, `Q4_K_M` quantization |
| Endpoint | `http://127.0.0.1:11434` only |
| Context / output limit | 8,192 / 1,024 tokens for the workflow smoke test; 512 tokens for the schema smoke test |
| Retry policy | One bounded retry, as configured by `MODEL_MAX_RETRIES` |
| Tested host memory | 31.7 GiB physical memory (a 32 GB installed-memory class host) |

The qualification floor is a local 32 GB installed-memory-class Windows host
with a loopback-only Ollama runtime and the exact model tag above. The
recommended configuration is the same 32 GB memory class or greater; no
discrete-GPU requirement or performance claim is made because no GPU
configuration was captured or compared. Lower-memory hosts and all different
model/runtime combinations remain unqualified.

## Results

On 2026-07-12, the opt-in synthetic smoke suite passed against the local
runtime in 21 seconds total. It exercised strict structured output plus the
profile extraction, job matching, compensation, and application-preparation
agents. Assertions covered profile evidence, bounded score/range values,
prepared-only application state, and removal of a work-authorization answer
pending direct user input.

The regular synthetic regression suite also covers malformed and partial
output, unavailable and overloaded runtime behavior, bounded request/response
sizes, prompt-injection strings, unsupported profile evidence, and replayed
preparation requests. Those tests use mocks only.

No prompts, model responses, resumes, candidate records, screening answers,
or provider payloads are retained by these tests. Only aggregate pass/fail and
duration are recorded here.

## Requalification protocol

Run this protocol whenever the Ollama version, model tag or quantization,
context/output settings, or host class changes:

1. Confirm the configured model is installed and the Ollama API listens only
   on the approved loopback endpoint.
2. Run the default synthetic suite:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest -m eval
   ```

3. Run the local-only smoke suite with no candidate data:

   ```powershell
   $env:RUN_LOCAL_MODEL_QUALIFICATION='1'
   .\.venv\Scripts\python.exe -m pytest tests/test_local_model_qualification.py -k opt_in_loopback_local_model
   ```

4. Record only the runtime/model details, host-memory class, context/output
   settings, aggregate duration, and pass/fail result. Do not record prompts,
   model output, profile data, or raw runtime responses.
5. Treat any malformed output, evidence-policy failure, unsafe screening
   behavior, non-prepared application state, unavailable runtime, or failed
   check as a failed qualification. Do not substitute a remote provider or
   silently fall back.

## Known limitations

- This is one local Windows host only; it is not a throughput benchmark.
- No GPU model, VRAM value, or concurrent-user capacity is qualified.
- The smoke tests establish safety invariants and structured-output behavior;
  they do not certify factual quality beyond the synthetic cases.
- Other model tags, quantizations, and lower-memory hosts require a separate
  qualification record before they can be represented as supported.
