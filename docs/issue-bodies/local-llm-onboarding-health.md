## Context and motivation

The Windows launcher currently asks for an OpenAI API key and assumes outbound
access to `api.openai.com`. A local-first product needs a transparent,
consent-based setup path that detects the local runtime and model without
automatically installing software or downloading a large model.

## Scope

- Replace API-key setup with local-provider configuration in the Windows
  launcher and example environment configuration.
- Add a local runtime/model readiness check to the application health or a
  dedicated authenticated readiness endpoint.
- Give plain-language recovery guidance for absent runtime, stopped runtime,
  missing model, unsupported hardware, or insufficient configured limits.
- Require a clear user confirmation before any launcher-initiated runtime or
  model download/install action; retain a manual-install path.

## Acceptance criteria

- Normal local setup does not request, store, display, or validate an OpenAI
  API key.
- The launcher verifies the configured local runtime is loopback-only, running,
  and has the selected model available before opening the workspace.
- A readiness failure names the next local action without exposing tokens,
  private configuration, resume content, or raw runtime errors.
- Model download/install is never automatic: the exact runtime/model and disk
  impact are shown and the user must explicitly confirm before it begins.
- The browser workspace presents a safe, understandable unavailable state and
  does not imply that a profile or application was generated when inference
  failed.

## Relevant files or components

- `scripts/Start-TalentAdvisor.ps1`
- `scripts/Start-TalentAdvisor.cmd`
- `app/local_launcher.py`
- `app/main.py`
- `app/config.py`
- `.env.example`
- browser UI source and launcher/API tests

## Dependencies and blockers

- Depends on the provider contract and Ollama adapter issues.
- The exact default model and minimum/recommended hardware guidance must be
  selected from the local-model qualification issue before release.

## Security and privacy considerations

- The launcher must not download, execute, or configure third-party software
  without explicit user confirmation.
- Limit runtime communication to the approved loopback endpoint; do not create
  a public tunnel or expose local model APIs on the network.
- Do not put runtime tokens, user settings, or candidate data in launcher
  dialogs, process arguments, logs, or the browser.

## Testing considerations

- Add launcher and configuration tests for no key prompt, unavailable runtime,
  absent model, invalid host, safe recovery messaging, and declined download.
- Add API/UI tests for readiness and unavailable-state behavior.
- Run `python -m ruff check .`, `python -m pytest`, plus relevant widget tests
  and type checking if widget source changes.
