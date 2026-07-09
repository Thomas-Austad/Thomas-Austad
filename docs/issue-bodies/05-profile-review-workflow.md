## Context and motivation
A trustworthy career product cannot treat generated profile output as final without a user review and correction step. Users need a way to approve or correct extracted skills, experience, and preferences before downstream use.

## Acceptance criteria
- Users can inspect generated profiles, ambiguities, and preferences.
- Users can correct profile data and save those corrections durably.
- The system preserves a distinction between source-backed evidence and user edits.
- Downstream matching and application flows use the corrected profile.

## Relevant files or components
- `widget/`
- `app/main.py`
- `app/models/schemas.py`
- persistence modules for profile corrections

## Dependencies or blockers
- Depends on persistence work.
- Benefits from evidence storage so corrections can be shown against source support.

## Security considerations
- Only the owning user should be able to view or edit their profile.
- Avoid losing provenance when a user overrides generated data.

## Testing considerations
- Add integration tests for review, correction, and subsequent reuse of the corrected profile.
- Add authorization tests once auth exists.
