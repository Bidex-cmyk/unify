# unify

Self-hosted personal API unifying notes, bookmarks, expenses, and habits.

[![CI](https://github.com/Bidex-cmyk/unify/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Bidex-cmyk/unify/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## What it is

unify is a self-hosted personal API for bringing everyday personal data into one place.
The goal is to manage notes, bookmarks, expenses, and habits through a consistent API
that you can run and control yourself. This repository currently contains the initial
application scaffold and health endpoint.

## Stack

- FastAPI
- SQLModel
- HTMX (planned)
- Postgres
- Docker
- uv
- Ruff
- pytest

## Quickstart (local)

```sh
cp .env.example .env
make install
make migrate
make dev
```

Open <http://localhost:8000/health> to check that the API is running. The scaffold
currently uses SQLite; Postgres is included in the Docker Compose setup for later
database wiring.

## Quickstart (Docker)

```sh
cp .env.example .env
docker compose up --build
```

## Development

```sh
make test
make lint
make fmt
```

### Auth

All routes under `/api` require a bearer token. Set `UNIFY_API_TOKEN` in `.env`. The
default development token is `dev-token-change-me`.

```sh
curl -H "Authorization: Bearer $UNIFY_API_TOKEN" http://localhost:8000/api/whoami
```

## API

Routes use the `/api` prefix. Every route under `/api` requires the bearer token.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/notes` | List notes; `include_deleted=true` includes soft-deleted notes |
| POST | `/api/notes` | Create a note |
| GET | `/api/notes/{note_id}` | Get a note by ID |
| PATCH | `/api/notes/{note_id}` | Partially update a note |
| DELETE | `/api/notes/{note_id}` | Soft-delete a note; `hard=true` permanently deletes it |
| GET | `/api/bookmarks` | List bookmarks; `include_deleted=true` includes soft-deleted bookmarks |
| POST | `/api/bookmarks` | Create a bookmark; fetches title and description in the background |
| GET | `/api/bookmarks/{bookmark_id}` | Get a bookmark by ID |
| PATCH | `/api/bookmarks/{bookmark_id}` | Partially update a bookmark |
| DELETE | `/api/bookmarks/{bookmark_id}` | Soft-delete a bookmark; `hard=true` permanently deletes it |

## Migrations

```sh
make revision m="add x"
make migrate
make downgrade
```

## Roadmap

- [x] Scaffold
- [x] DB models
- [x] Auth
- [x] Notes API
- [x] Bookmarks API
- [ ] HTMX UI
- [ ] VPS deploy
- [ ] CI/CD

## License

MIT
