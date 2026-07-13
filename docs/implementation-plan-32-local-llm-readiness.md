# Issue 32 implementation plan: local LLM readiness and consent-based onboarding

## Scope and trust boundaries

This change replaces remote-key onboarding with a local Ollama readiness path.
Launcher configuration, the local runtime response, browser workspace state,
and environment settings cross trust boundaries. Runtime responses are
untrusted and must be reduced to safe readiness state; candidate data, tokens,
raw runtime errors, and model output must not appear in dialogs, API responses,
or browser state.

## External effects and approvals

- The launcher may query only the configured loopback Ollama endpoint.
- It must not install software, download a model, or change runtime settings.
- Any future download/install action remains a manual user step; the launcher
  provides only the exact model name and disk impact in recovery guidance.
- No application, profile, approval, or browser handoff state changes as part
  of readiness checking.

## Implementation steps

1. Make the local provider/model the launcher and example-configuration
   default without requesting or retaining an OpenAI API key.
2. Add a bounded, loopback-only readiness service that verifies the configured
   model is present and maps unavailable, malformed, and missing-model cases
   to safe recovery codes.
3. Expose an authenticated readiness endpoint and use it from the launcher
   before opening a browser workspace.
4. Return an explicit unavailable state to the browser workspace without
   implying a profile or application operation completed.
5. Add launcher, configuration, API, service, and browser tests for success,
   invalid hosts, unavailable runtime, missing model, and no automatic
   download/install behavior.

## Validation

- Focused Python readiness, launcher, and browser tests.
- Widget unit tests, type check, and build if widget source changes.
- `python -m ruff check .`
- `python -m pytest`
