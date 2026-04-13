# 16 Bus Backend

FastAPI scaffold for the `16 Bus` South African taxi operations platform.

## Run locally

```bash
uv venv .venv
.venv\Scripts\activate
uv sync --extra dev
uv run alembic upgrade head
uvicorn app.main:app --reload
```

## Migrations

```bash
uv run alembic upgrade head
uv run alembic current
```

## Structure

- `alembic`: schema and seed migrations
- `app/core`: platform configuration and infrastructure glue
- `app/api`: HTTP and WebSocket entrypoints
- `app/domain`: business domains aligned to the architecture document
- `app/integrations`: external provider adapters
- `app/workers`: async consumers and background task hooks
- `tests`: backend smoke tests
