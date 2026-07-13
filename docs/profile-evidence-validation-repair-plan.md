# Profile evidence validation repair plan

## Scope and trust boundaries

Profile extraction receives untrusted resume and LinkedIn text, and model output
must remain traceable without requiring users to rewrite otherwise valid
documents. Evidence validation must reject unsupported claims while tolerating
non-verbatim summaries of supplied evidence. Browser recovery text must not
misstate a model-output rejection as a local-runtime outage.

## Implementation

1. Replace exact-substring-only evidence validation with a bounded lexical
   support check: each evidence item must have meaningful overlap with its
   declared source, and skills require source support for their named term.
2. Keep candidate ID, source, empty-evidence, and unsupported-claim rejection
   fail-closed.
3. Add negative and paraphrase regression tests using synthetic data only.
4. Map HTTP 502 to an accurate, non-sensitive retry/review message; retain the
   Ollama recovery message only for HTTP 503.
5. Rebuild the browser asset and run focused, full, and eval checks.
