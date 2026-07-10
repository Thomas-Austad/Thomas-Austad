# Local Development Setup

This repo is easiest to work on with a dedicated virtual environment.

## Recommended setup

From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install setuptools wheel
python -m pip install -e ".[dev]" --no-build-isolation
Copy-Item .env.example .env
# Edit .env: set a unique POSTGRES_PASSWORD and set DATABASE_URL to the
# matching local PostgreSQL connection URL.
docker compose up -d db
python -m alembic upgrade head
```

## Day-to-day commands

```powershell
python -m ruff check .
python -m pytest
python -m pytest -m eval
python -m alembic upgrade head
```

## Notes

- The repo targets Python 3.11+, and the local environment used here was Python 3.14.
- The sandboxed desktop environment blocks direct PyPI access for build isolation, so `--no-build-isolation` was needed to finish the editable install locally.
- If you recreate the environment later and `python -m pip install -e ".[dev]"` works without the extra flag, that is fine too.
- `DATABASE_URL` must point at PostgreSQL. For a local process, use the
  username, password, and database selected in `.env` with the `localhost`
  host; Docker Compose sets the API container to use the `db` service host.
- Docker Compose is for local development. Its published ports bind to
  `127.0.0.1`; do not use this file as a production deployment configuration.
