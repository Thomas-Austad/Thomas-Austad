# Issue 28 implementation plan: secure local installation and startup

## Scope and risk

Scope/risk: high; Windows launcher, local credentials, configuration, database
startup, loopback process lifecycle, and user-facing onboarding.  The launcher
must not expose secrets or weaken the local authentication and approval model.

Route: Sol high; this work changes the supported application entry point and
coordinates the browser-session trust boundary with the local service lifecycle.

Verify: focused launcher and browser-session tests, browser typecheck/test/build,
then the repository lint, test, eval, and migration-SQL completion checks.

Blockers/approval: a user must explicitly choose any first-run dependency
installation; no launcher action may silently install software or publish a
network service.

## Delivery plan

1. Make the Python local launcher create a fresh browser bootstrap through the
   running local API after health verification. This permits a repeat launch to
   attach safely to an existing Talent Advisor instance without reading or
   exposing a bearer credential to the browser.
2. Extend the graphical Windows launcher with non-sensitive prerequisite,
   configuration, local-port, database, migration, asset, and health checks.
   Each problem must give a plain-language next action and preserve existing
   configuration and data.
3. Cover the new lifecycle and launcher safeguards with focused tests.
4. Replace the obsolete manual/MCP-only user guide with one canonical
   double-click workflow, recovery steps, and the explicit non-submission
   boundary. Keep command-line instructions only as developer support material.

## Security decisions

- The launcher obtains a short-lived bootstrap value only through the existing
  locally authenticated launch endpoint. It does not place the bearer token in
  the browser, URL, logs, or frontend bundle.
- A repeat run does not reset `.env`, storage, or migrations. A local port used
  by a non-Talent-Advisor process is rejected with a recovery message.
- All started services stay on the configured loopback address. The launcher
  does not create tunnels, change firewall rules, or silently install software.
- The Windows entry point uses a maintained command launcher that invokes the
  PowerShell workflow directly; it does not rely on the deprecated VBScript
  host or relax PowerShell execution policy.
