# Issue #17 execution plan — Ashby search coverage and manual filtering

## Scope and safety boundary

This increment adds Ashby's permitted public job-board read API to the existing
Greenhouse and Lever connectors. It keeps refresh user-initiated: every search
fetches the requested source identifiers and no provider targets, job payloads,
or credentials are persisted or scheduled for later retrieval.

Employer career-page ingestion is explicitly out of scope because no approved
domains or permitted API agreements have been supplied. All provider responses
remain untrusted data: requests use fixed HTTPS provider endpoints, bounded
source lists, existing timeouts/retries, defensive parsing, and safe
provider-name-only error responses.

## Approved product decisions

- Add Ashby public job-board support; retain Greenhouse and Lever.
- Use manual refresh only; do not implement scheduled collection.
- A filter excludes a job when the required provider field is absent.
- Do not add generic employer-page scraping or ingestion.

## Implementation steps

1. Add an Ashby connector that normalizes only active postings into the existing
   `JobListing` shape and extend provider error validation safely.
2. Extend the read-only search request, service, and MCP tool with bounded
   Ashby board names and validated filters for company, location, remote mode,
   compensation, employment type, and freshness.
3. Apply the filters deterministically before storing returned jobs; retain
   source-URL deduplication and isolate individual provider failures.
4. Update the widget contracts and search form for the new source and filters,
   rendering all returned provider/job text as text.
5. Add synthetic connector, service, API, and widget tests for normalization,
   failure isolation, deduplication, every filter's missing-data behavior, and
   manual-refresh request semantics. Update the operations runbook.

## Verification

- Focused Python connector, job-service, API workflow, and MCP tests.
- `python -m ruff check .`
- `python -m pytest`
- `python -m pytest -m eval`
- `pnpm --dir widget typecheck`
- `pnpm --dir widget test --run`
- `pnpm --dir widget build`
