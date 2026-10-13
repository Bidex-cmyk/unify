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

## Documentation

Keep [architecture.md](docs/architecture.md), [api.md](docs/api.md), and
[demo.md](docs/demo.md) aligned with behavior and developer workflows. Package public
documentation with concise Markdown, working relative links, and no secrets or personal
data in examples. Refresh the OpenAPI snapshot with `make openapi` while the app runs.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/), for example:
`feat(notes): add archive filter` or `fix(auth): reject empty tokens`.
