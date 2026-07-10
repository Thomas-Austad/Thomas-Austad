## Context and motivation

Prepared application packages and sensitive screening gates need an explicit
review surface before any assisted-apply work can be considered.

## Why this work is necessary

The product boundary requires users to distinguish preparation, user-confirmed
sensitive answers, and approval; raw API calls cannot provide adequate clarity.

## Bounded scope

- Implement package review for tailored resume, cover letter, warnings, and
  unresolved screening questions.
- Implement direct user confirmation and approval using current endpoints.
- Clearly show the legal state and outcome of preparation versus approval.
- Do not add submission, upload-to-provider, messaging, or browser automation.

## Acceptance criteria

- A user can review a prepared package before any approval action.
- Unresolved screening questions are visible and block approval in the UI.
- A sensitive answer requires direct user confirmation before it is sent to the
  existing resolution endpoint.
- Approval uses a visually distinct explicit confirmation and prevents repeat
  activation while a request is pending.
- The UI shows approved state and safe API failures without implying submission.

## Relevant files or components

- `widget/`
- `app/main.py`
- `app/mcp_server.py`
- `app/models/schemas.py`
- `tests/test_api_workflow.py`

## Dependencies or blockers

- Depends on #22 and #23; benefits from #24 and #25 for the complete journey.
- This is a prerequisite for #20 but does not authorize or implement assisted
  application submission.

## Security and privacy considerations

- Never infer sensitive or legally meaningful answers.
- Keep prepare, screening confirmation, approval, and submission visually and
  technically separate.
- Do not expose secrets or store screening answers in browser storage.

## Testing considerations

- Add negative UI tests for missing confirmation, unresolved questions, repeated
  approval, malformed responses, and failed requests.
- Add an integration test for the review-to-approval path where practical.

## Definition of done

- A user can safely review and approve an application package without raw API
  calls, while submission remains unavailable and unambiguous.
