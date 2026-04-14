# 16 Bus Backend

FastAPI scaffold for the `16 Bus` South African taxi operations platform.

## Getting Started

### Prerequisites

- [uv](https://github.com/astral-sh/uv)
- [Docker](https://www.docker.com/)

### Setup

1. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Spin up infrastructure (Database & Redis):
   ```bash
   docker compose up -d
   ```

4. Run migrations:
   ```bash
   uv run alembic upgrade head
   ```

5. Seed reference data:
   ```bash
   uv run python -m app.core.bootstrap seed
   ```

### Run locally

```bash
uv run uvicorn app.main:app --reload
```

Or using the Makefile:
```bash
make run
```

## Structure

- `alembic`: schema and seed migrations
- `app/core`: platform configuration and infrastructure glue
- `app/api`: HTTP and WebSocket entrypoints
- `app/domain`: business domains aligned to the architecture document
- `app/integrations`: external provider adapters
- `app/workers`: async consumers and background task hooks
- `tests`: backend smoke tests

## Testing

```bash
pytest
```
