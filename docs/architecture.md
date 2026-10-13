# Architecture

## Request and data flow

```text
HTTP request
    |
    v
Router  -->  Service  -->  SQLModel table  -->  Database
    |            |                |
    |            |                +-- storage structure and persistence types
    |            +-- business rules and database operations
    +-- HTTP validation, status codes, and response schemas

Schemas (schemas.py) define request and response wire formats at the router boundary.
```

Routers handle HTTP concerns: parsing inputs, dependencies, status codes, and mapping
not-found or conflict results to HTTP responses. Services own business logic and database
operations; they can be called from both API and UI routes without routing through HTTP.
Models describe persisted tables and their storage types. Schemas define the public wire
format independently of storage.

The API does not return SQLModel tables directly as its contract. Read schemas explicitly
select exposed fields, so internal columns (such as `deleted_at`) stay private and future
storage changes do not silently change API responses.

## Soft deletion

Notes and bookmarks have a nullable `deleted_at`. A normal delete marks the timestamp
instead of erasing the row, preserving the option to recover user data. List endpoints
exclude deleted rows by default; `?include_deleted=true` includes them. Hard deletion is
available explicitly with `?hard=true` and cannot be undone.

## Migrations

Alembic owns application schema creation and changes. Use `make revision m="..."` to
generate a migration and `make migrate` to apply it. `SQLModel.metadata.create_all` is
used only in isolated tests; application startup must not create or mutate the schema.

## Authentication

The `/api` router applies `require_token` as a router-wide dependency, so new API routes
are protected by default. It compares a configured single-user bearer token in constant
time. `/health` and the development-only UI are outside that router. When the UI gains
real authentication, it should use server-side sessions and a login flow rather than
requiring the API bearer token in browser forms.

## Bookmark metadata fetch

Bookmark creation schedules metadata extraction as a fire-and-forget background task.
The request can return promptly; metadata failure does not undo a saved bookmark. The
task opens its own database session because the request session is scoped to the request
and may be closed before background work runs. The task catches and logs failures so
network or parser errors cannot crash request handling.

The metadata fetcher accepts only HTTP(S), resolves the hostname, and rejects private,
loopback, link-local, and reserved addresses. It checks redirect destinations as well,
blocking attempts to reach local services or private networks through a public URL.
Only HTML responses are parsed, and fetch failures produce empty metadata.

## Testing

Tests use an in-memory SQLite engine with `StaticPool` so the test client and fixture
sessions share the same database. FastAPI `dependency_overrides` inject that session into
requests. Metadata-fetch tests use `httpx.MockTransport`; API and UI tests stub the
background fetcher. Tests do not need external network access.
