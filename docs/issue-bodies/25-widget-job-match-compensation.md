## Context and motivation

Job search, match explanations, and compensation estimates are currently only
available through raw API calls, leaving users unable to evaluate opportunities
in the intended workflow.

## Why this work is necessary

The widget must make existing job, match, and compensation outputs readable and
actionable before users prepare an application.

## Bounded scope

- Implement job search/result views using supported current sources.
- Implement job-detail, match-explanation, gaps, and compensation views.
- Provide responsive, accessible filtering and error/empty states.
- Reuse existing API contracts; provider expansion remains in #17.

## Acceptance criteria

- A user can search configured supported sources and inspect returned jobs.
- A user can view match scores, reasons, gaps, and compensation assumptions for
  a selected profile/job without raw API calls.
- Provider errors are shown safely and do not erase results from other sources.
- External job text is rendered as text and never controls UI permissions.
- UI tests cover loading, failed, empty, and successful job-review states.

## Relevant files or components

- `widget/`
- `app/main.py`
- `app/services/job_service.py`
- `app/models/schemas.py`

## Dependencies or blockers

- Depends on #22 and #23.
- Does not add sources, scraping, or provider credentials; those remain #17.

## Security and privacy considerations

- Treat job content and provider failures as untrusted data.
- Do not persist candidate data or tokens in browser storage.

## Testing considerations

- Test supported-source search, selection, provider-error isolation, and
  rendering of injection-like external job text.

## Definition of done

- Users can browse jobs and inspect match/compensation outputs through the
  widget using only supported existing backend contracts.
