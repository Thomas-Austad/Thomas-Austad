# Run and use Talent Advisor locally (Windows)

This guide is for the personal, single-user version of Talent Advisor. It runs
only on your computer and is designed to keep its API on the loopback interface
(`127.0.0.1`). Do not expose the API or MCP server through a tunnel or public
URL.

Talent Advisor prepares, reviews, and tracks application materials. It does
not submit applications. Any employer-page handoff is a user-activated link
only; it does not transfer credentials, upload documents, or report a
submission.

## 1. Install and verify the prerequisites

Install these before starting:

- Python 3.11 or newer.
- Docker Desktop, with its Docker engine running. Docker supplies PostgreSQL.
- An OpenAI API key whose account can use the configured model.
- Node.js and pnpm if you want to build or use the ChatGPT/MCP widget.

From the repository root, verify the tools that apply to the path you plan to
use:

```powershell
py --version
docker version
node --version
pnpm --version
```

If `docker version` cannot connect to the daemon, start Docker Desktop and wait
until it reports that the engine is running. If `node` is not recognized,
install the current Node.js LTS release, open a new PowerShell window, and run
the checks again. If `node` works but `pnpm` is not recognized, install the
project's declared pnpm version with:

```powershell
npm install --global pnpm@11.7.0
pnpm --version
```

## 2. Create and activate the Python environment

Run these commands from the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install setuptools wheel
python -m pip install -e ".[dev]" --no-build-isolation
```

The `--no-build-isolation` option is useful in restricted environments. If a
normal editable install works on your computer, it is also acceptable.

## 3. Create your private local configuration

Copy the template; `.env` is ignored by Git and must never be committed:

```powershell
Copy-Item .env.example .env
```

Open `.env` in an editor and set at least these values:

```dotenv
APP_ENV=development
OPENAI_API_KEY=your_openai_api_key
POSTGRES_USER=talent
POSTGRES_PASSWORD=a-long-unique-url-safe-password
POSTGRES_DB=talent
DATABASE_URL=postgresql+psycopg://talent:a-long-unique-url-safe-password@localhost:5432/talent
PUBLIC_BASE_URL=http://localhost:8000
LOCAL_ACCESS_TOKEN=a-separate-random-secret-of-at-least-32-characters
```

Use a different, strong secret for `POSTGRES_PASSWORD` and
`LOCAL_ACCESS_TOKEN`. Keep the database password URL-safe (letters, numbers,
hyphens, and underscores are simplest); otherwise URL-encode it in
`DATABASE_URL`. The token is especially useful for REST/API clients because
every non-health API route requires a bearer token.

The application can store a token and encryption key in your operating-system
credential store when no `LOCAL_ACCESS_TOKEN` is set. Setting the token
explicitly is simpler for manual API use and local automation. Never put either
secret in source code, a chat transcript, or a screenshot.

To generate a URL-safe random secret that also works in Windows PowerShell 5.1,
run this command twice and paste each output into the appropriate field:

```powershell
$bytes = New-Object byte[] 32; $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create(); $rng.GetBytes($bytes); $rng.Dispose(); -join ($bytes | ForEach-Object { $_.ToString('x2') })
```

Use the first output for `POSTGRES_PASSWORD` (and the same value in
`DATABASE_URL`) and the second for `LOCAL_ACCESS_TOKEN`.

## 4. Start PostgreSQL and apply the schema

With Docker Desktop running, start only the local database:

```powershell
docker compose up -d db
docker compose ps
python -m alembic upgrade head
```

`docker compose ps` should show the `db` service as healthy before the
migration command runs. The database port is bound to your local computer only.

## 5. Start and check the API

In the same activated PowerShell session, run:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

In a second PowerShell window, confirm the unauthenticated health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

It should return `ok` set to `true`. All other API requests need the bearer
token you put in `.env`. For example, in a PowerShell API client session:

```powershell
$token = "paste-the-LOCAL_ACCESS_TOKEN-value-here"
$headers = @{ Authorization = "Bearer $token" }
```

There is no standalone browser dashboard served by FastAPI. Use an API client
that can attach this header, or use the MCP workflow below.

## 6. Build and run the ChatGPT/MCP workflow (recommended)

This path provides the review-oriented widget and MCP tools. Do this after
Node.js and pnpm are available. Run these build commands from the repository
root, after starting PostgreSQL in step 4 and activating the Python environment
in step 2:

```powershell
pnpm --dir widget install --frozen-lockfile
pnpm --dir widget typecheck
pnpm --dir widget test --run
pnpm --dir widget build
python -m app.mcp_server
```

The final command starts an MCP server over local standard input/output; it is
not a web server and will not open a browser page. Normally, configure your
MCP-capable ChatGPT client to launch it using this working directory and
command, rather than starting it manually in a terminal:

```text
working directory: <repository root>
command: <repository root>\.venv\Scripts\python.exe
arguments: -m app.mcp_server
```

Do not publish this process through a tunnel or remote MCP transport. The
widget calls the local MCP tools; it does not receive your bearer token or call
the loopback API directly.

## 7. Use the application safely

The intended flow is:

1. Create a candidate profile from your resume (and optional LinkedIn export).
2. Review the extracted evidence and correct any mistakes.
3. Search specific public Greenhouse, Lever, or Ashby job boards.
4. Evaluate a match and, if useful, request a compensation estimate.
5. Prepare a tailored resume, cover letter, and screening-answer draft.
6. Answer any unresolved screening questions yourself. The app will not guess
   legal, personal, demographic, salary-history, disability, criminal-history,
   or work-authorization answers.
7. Review and explicitly approve the prepared package.
8. Optionally request browser handoff, review the destination, and open the
   employer page yourself.

No preparation, approval, or browser handoff submits an application. Complete
the employer form and any final submission yourself.

Candidate and job text used for AI-backed profile, matching, compensation, or
document work is sent to the OpenAI API configured by `OPENAI_API_KEY`. Only
use data you are authorized to provide and treat `.env`, the local database,
credential store, and `var/audit/` as private.

## 8. Run the local checks before relying on an update

```powershell
python -m ruff check .
python -m pytest
python -m pytest -m eval
python -m alembic upgrade head --sql
```

For widget changes, also run the typecheck, test, and build commands from step
6.

## Troubleshooting

- **`node` is not recognized:** install Node.js, reopen PowerShell, then rerun
  `node --version` and the widget commands.
- **Docker cannot connect:** start Docker Desktop, ensure its engine is ready,
  then rerun `docker compose up -d db`.
- **Database connection failed:** confirm Docker reports a healthy `db` service
  and that `DATABASE_URL` has the same user, password, database name, and
  `localhost:5432` host as the `.env` PostgreSQL settings.
- **`401 Local authentication required`:** attach
  `Authorization: Bearer <LOCAL_ACCESS_TOKEN>` to the request.
- **OpenAI authentication or model error:** verify `OPENAI_API_KEY` and that
  your account can use `OPENAI_MODEL`; restart the API after changing `.env`.
- **Port 8000 is already in use:** stop the process using it or launch Uvicorn
  with another loopback port and update `PUBLIC_BASE_URL` to match.

## Stop the local services

Stop Uvicorn and the MCP server with `Ctrl+C`. When you are done with the
database, stop it without deleting its data:

```powershell
docker compose stop db
```

Do not remove Docker volumes unless you intentionally want to delete your local
candidate, job, and application data.
