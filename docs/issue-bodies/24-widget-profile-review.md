## Context and motivation

Users need to inspect generated candidate claims, their supporting evidence,
and their corrections before downstream matching or preparation uses them.

## Why this work is necessary

The existing profile review/correction API is not practical without a guided
UI that preserves the distinction between evidence and user-provided edits.

## Bounded scope

- Implement profile review, evidence display, ambiguities, and corrections.
- Use the existing profile review and correction contracts without changing
  candidate-claim generation rules.
- Provide accessible responsive states for absent, loading, failed, and
  corrected profiles.

## Acceptance criteria

- A user can review generated profile fields, evidence, ambiguities, and past
  corrections in the widget.
- A user can submit bounded profile corrections through the established API.
- The UI identifies user edits separately from source evidence.
- Errors do not disclose credentials or unrelated candidate data.
- Desktop and mobile flows are keyboard-operable and covered by UI tests.

## Relevant files or components

- `widget/`
- `app/main.py`
- `app/models/schemas.py`
- `tests/test_api_workflow.py`

## Dependencies or blockers

- Depends on #22 and #23.
- Uses the existing local authentication and profile review workflow.

## Security and privacy considerations

- Candidate data remains in transient UI state only.
- Do not fabricate, merge, or silently alter profile claims in the client.

## Testing considerations

- Test successful review/correction plus unauthorized, malformed, and failed
  API response states.

## Definition of done

- Profile review and correction are usable without raw HTTP calls and preserve
  the evidence/user-edit boundary.
