.PHONY: setup install test run migrate seed docker-up docker-down web-setup web-run web-build

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

web-setup:
	cd web && npm install

web-run:
	cd web && npm run dev

web-build:
	cd web && npm run build
