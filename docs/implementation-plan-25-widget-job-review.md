# Issue #25 execution plan — widget job, match, and compensation review

## Scope and safety boundary

Job descriptions and provider results are untrusted content. The widget will
validate all tool results, render provider and job text only as text, avoid
direct HTTP requests and browser persistence, and never use job content to
choose permissions or invoke a write-capable tool.

The existing search result currently discards connector failures. To meet the
issue's provider-error criterion without disclosing raw errors, credentials, or
requested provider targets, the response will add an optional safe
`provider_errors` list containing provider labels only. Existing `count` and
`jobs` fields remain unchanged, and successful jobs remain available when a
different provider fails.

## Implementation steps

1. Add a safe, typed provider-error result field and preserve successful
   results in the job service and API/MCP search response.
2. Define validated job-search, match, and compensation widget contracts and a
   typed MCP client for the existing read-only tools.
3. Add accessible search, job-detail, match, and compensation UI states,
   treating all returned text as plain text.
4. Add focused provider-isolation, injection-like-text, loading, empty, error,
   and successful-review tests; then run the completion checks.

## Verification

- `pnpm --dir widget typecheck`
- `pnpm --dir widget test --run`
- `pnpm --dir widget build`
- `.venv\\Scripts\\python.exe -m ruff check .`
- `.venv\\Scripts\\python.exe -m pytest`
- `.venv\\Scripts\\python.exe -m pytest -m eval`
