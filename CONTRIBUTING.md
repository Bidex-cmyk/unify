# Contributing

This is a personal project. PRs are welcome, but they are not actively solicited.

## Local setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
cp .env.example .env
make migrate
make dev
```

## Checks

```sh
uv run pytest
uv run ruff check .
uv run mypy src/unify
```

Install the optional local hooks with `uv run pre-commit install`.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/), for example:
`feat(notes): add archive filter` or `fix(auth): reject empty tokens`.
