## Context and motivation
The product can fetch Greenhouse and Lever postings, but a practical career workflow needs broader job-source coverage, better filtering, and refresh behavior so users can find relevant roles without repeatedly supplying raw board identifiers.

## Acceptance criteria
- Additional supported sources are prioritized and implemented through official or permitted APIs where available.
- Search filters cover title, company, location, remote mode, compensation, employment type, and freshness where provider data supports them.
- Job refresh behavior is explicit, deduplicated, and avoids indiscriminate scraping or mass collection.
- Provider failures are visible to the user without failing the entire search when other sources succeed.

## Relevant files or components
- `app/connectors/`
- `app/services/job_service.py`
- `app/models/schemas.py`
- `app/main.py`
- future UI surfaces in `widget/`
- `docs/operations-runbook.md`

## Dependencies or blockers
- Some provider integrations may require credentials, terms review, or licensed API access.
- UI work will determine the final search and filter ergonomics.

## Security considerations
- Treat all provider payloads as untrusted content.
- Do not scrape or automate platforms in violation of terms, access controls, robots policies, or applicable law.
- Use explicit provider allowlists, HTTPS, timeouts, response-size limits, and redirect limits.

## Testing considerations
- Mock all provider APIs; do not require real credentials in tests.
- Add tests for deduplication, filtering, provider failure isolation, malformed provider payloads, and prompt-injection content in job descriptions.
