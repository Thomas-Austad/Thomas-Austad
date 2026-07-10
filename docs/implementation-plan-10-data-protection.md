# Issue 10 implementation plan: local data protection and lifecycle controls

## Approved policy

This local-first application protects against loss or offline copying of the
device/database. It does not claim to protect against an administrator, malware,
or a process running as the same logged-in operating-system user.

- Sensitive persisted payloads use versioned AES-256-GCM application-layer
  encryption in addition to the host operating system's full-disk encryption.
- A random active data key is held only in the operating-system credential store.
  Keys are versioned; new writes use the configured active version and old keys
  remain readable during rotation. There is no provider-held recovery or key
  escrow: loss of all local keys makes encrypted data unrecoverable.
- Profiles, evidence, and correction history become due for review after 24
  months of inactivity; application packages after 12 months. This local MVP
  exposes due records and requires current user confirmation to purge them.
- Exports are generated in memory and streamed; no export artifact is retained.
  Deletion removes live profile-related data immediately. Managed backup copies
  must expire within 30 days; user-controlled backups are disclosed as outside
  the application’s control.
- Minimal audit receipts are retained for 12 months and never contain profile,
  document, correction, or export content.

## Trust boundaries

- Candidate profiles, evidence, correction values, and application packages are
  sensitive. Jobs remain provider data and are not treated as candidate records.
- Ciphertext, nonces, key versions, and opaque database identifiers are not
  secrets; plaintext and encryption keys are secrets and must not be logged.
- The local bearer credential identifies the sole principal. Export and deletion
  require that credential plus immediate, explicit confirmation.

## Implementation steps

1. Add the maintained `cryptography` dependency and a typed data-protection
   service backed by the operating-system credential store. Use AES-GCM with
   random nonces, strict encrypted-envelope validation, authenticated context,
   key versioning, and a fail-closed key-store error.
2. Encrypt persisted candidate-profile payloads, evidence excerpts and claim
   references, correction values, match payloads, and application packages.
   Add a migration-safe envelope format and preserve compatibility only through
   an explicit migration path; never silently write new plaintext.
3. Add bounded retention timestamps and repository operations to list due
   records and delete one candidate’s live profile-related data transactionally.
4. Add confirmed, authenticated export, deletion, and retention-purge API/MCP
   operations. Stream exports from memory, prohibit arbitrary output paths, and
   emit minimal audit receipts without sensitive data.
5. Document the local threat model, key lifecycle, rotation procedure, recovery
   limitation, data inventory, retention schedule, export contents, and backup
   deletion boundary.
6. Add unit and integration tests for unavailable keys, malformed/tampered
   ciphertext, encryption round trips, key-version reads, no plaintext storage,
   confirmation gates, deletion scope, retention eligibility, exports, and audit
   redaction.

## Legacy-data rollout

Run `python -m app.privacy_migrate` first to report remaining plaintext
records, then run `python -m app.privacy_migrate --apply` on the local machine
that owns the OS-keystore key. The command skips encrypted records, so it can
be safely resumed. Verify a zero-result dry run before enabling
`REQUIRE_ENCRYPTED_STORAGE=true`; that flag then rejects any legacy plaintext
instead of silently accepting it.

## Validation

- Focused data-protection, repository, and API workflow tests.
- `.venv\Scripts\python.exe -m alembic upgrade head --sql`
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest`
