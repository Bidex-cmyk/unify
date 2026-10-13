.DEFAULT_GOAL := help

.PHONY: install dev test lint typecheck coverage fmt clean migrate revision downgrade up-local down-local help

install:
	uv sync

dev:
	uv run uvicorn unify.main:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest

lint:
	uv run ruff check .

typecheck:
	uv run mypy src/unify

coverage:
	uv run pytest

fmt:
	uv run ruff format . && uv run ruff check --fix .

up-local:
	docker compose -f docker-compose.yml -f docker-compose.local.yml up --build

down-local:
	docker compose -f docker-compose.yml -f docker-compose.local.yml down

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
	rm -f ./*.db

migrate:
	uv run alembic upgrade head

revision:
	@test -n "$(m)" || (echo 'Usage: make revision m="migration message"' >&2; exit 1)
	uv run alembic revision --autogenerate -m "$(m)"

downgrade:
	uv run alembic downgrade -1

help:
	@printf '%s\n' \
		'install - Install project dependencies' \
		'dev     - Run the development server' \
		'test    - Run the test suite' \
		'lint    - Check code with Ruff' \
		'typecheck - Run strict mypy checks' \
		'coverage - Run tests with coverage reporting' \
		'fmt     - Format code and apply Ruff fixes' \
		'up-local - Start local Docker Compose development stack' \
		'down-local - Stop local Docker Compose development stack' \
		'migrate - Apply all database migrations' \
		'revision - Generate a migration (requires m="message")' \
		'downgrade - Revert the latest database migration' \
		'clean   - Remove caches and SQLite databases' \
		'help    - List available targets'
