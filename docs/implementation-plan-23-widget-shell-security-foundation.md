# Issue 23 implementation plan: secure widget shell and bridge

## Scope and trust boundaries

This issue creates the TypeScript widget foundation described in
`docs/widget-ui-architecture.md`. The widget runs in an Apps SDK-compatible
iframe and receives untrusted tool results and job/profile text. It must never
receive the local bearer credential, OpenAI key, database URL, or direct
FastAPI access.

## External effects and approvals

- The widget invokes no direct HTTP requests and makes no submission,
  messaging, upload-to-provider, or other third-party action.
- The bridge has an explicit allowlist of currently read/preparation MCP tool
  names. It exposes no approval or submission tool in this issue.
- Installing pinned build/test dependencies is a local development change only.

## Implementation steps

1. Add a pinned `pnpm` workspace with strict TypeScript, React, Vite, Zod, and
   Vitest/Testing Library; commit the lockfile.
2. Implement a runtime-validated JSON-RPC bridge that accepts messages only
   from a configured host origin and exposes an allowlisted tool-call surface.
3. Implement an accessible responsive shell with profile, jobs, and
   applications navigation; loading, empty, error, and read-only status
   primitives; and an explicit reusable confirmation dialog.
4. Register the built static widget resource with the local MCP server without
   exposing credentials or adding a public listener.
5. Add unit tests for bridge origin/schema handling, keyboard navigation,
   status states, and confirmation behavior.

## Dependency review

- React, React DOM, Vite, TypeScript, Zod, Vitest, jsdom, and Testing Library
  are actively maintained, widely used project dependencies. Their exact
  versions are pinned in `package.json` and resolved with integrity hashes in
  `pnpm-lock.yaml`.
- No third-party script, font, analytics SDK, credential helper, or browser
  storage package is introduced.

## Validation

- `pnpm --dir widget typecheck`
- `pnpm --dir widget test --run`
- `pnpm --dir widget build`
- `.venv\\Scripts\\python.exe -m ruff check .`
- `.venv\\Scripts\\python.exe -m pytest`
