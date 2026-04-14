.PHONY: setup install test run migrate seed docker-up docker-down

setup:
	cp .env.example .env
	uv sync

install:
	uv sync

test:
	pytest

run:
	uv run uvicorn app.main:app --reload

migrate:
	uv run alembic upgrade head

seed:
	uv run python -m app.core.bootstrap seed

docker-up:
	docker compose up -d

docker-down:
	docker compose down
