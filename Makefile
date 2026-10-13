.DEFAULT_GOAL := help

.PHONY: install dev test lint fmt clean migrate revision downgrade help

install:
	uv sync

dev:
	uv run uvicorn unify.main:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest

lint:
	uv run ruff check .

fmt:
	uv run ruff format . && uv run ruff check --fix .

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
		'fmt     - Format code and apply Ruff fixes' \
		'migrate - Apply all database migrations' \
		'revision - Generate a migration (requires m="message")' \
		'downgrade - Revert the latest database migration' \
		'clean   - Remove caches and SQLite databases' \
		'help    - List available targets'
