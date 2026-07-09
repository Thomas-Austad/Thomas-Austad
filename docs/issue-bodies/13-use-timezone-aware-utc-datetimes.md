## Context and motivation

The test suite emits a deprecation warning from `CandidateProfile.generated_at` because it uses `datetime.utcnow()`. The repository standards require timezone-aware UTC datetimes internally, and Python 3.14 warns that naive UTC helpers are deprecated.

## Acceptance criteria

- Domain models use timezone-aware UTC defaults for generated timestamps.
- Existing API responses remain backwards-compatible or any response shape change is documented.
- Tests assert timestamp timezone behavior for model defaults.
- Any related datetime usage introduced later follows the same helper or pattern.

## Relevant files or components

- `app/models/schemas.py`
- tests covering model defaults and API serialization

## Dependencies or blockers

- None.

## Security considerations

- Accurate, timezone-aware timestamps are important for future consent, audit, and application-state records.
- Avoid exposing unrelated profile or application payloads while adding tests.

## Testing considerations

- Add a focused unit test that verifies generated timestamps are UTC-aware.
- Run `ruff check .` and `pytest`.
