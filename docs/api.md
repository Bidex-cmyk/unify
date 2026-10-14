# API reference

The JSON API under `/api/*` requires `Authorization: Bearer $UNIFY_API_TOKEN`.
The server-rendered UI under `/ui/*` requires a signed `unify_session` cookie created
by logging in at `/login`. `/`, `/login`, `/logout`, and `/health` are public routes;
UI routes are registered only in development.

## Endpoints

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/health` | None | Health and version information |
| GET | `/` | None | Public landing page |
| GET | `/login` | None | Sign-in form |
| POST | `/login` | None | Sign in and issue a session cookie |
| POST | `/logout` | None | Sign out and clear the cookie |
| GET | `/api/whoami` | Bearer | Check API token authentication |
| GET | `/api/notes` | Bearer | List notes |
| POST | `/api/notes` | Bearer | Create a note |
| GET | `/api/notes/{note_id}` | Bearer | Get a note |
| PATCH | `/api/notes/{note_id}` | Bearer | Partially update a note |
| DELETE | `/api/notes/{note_id}` | Bearer | Soft-delete a note (`hard=true` permanently deletes) |
| GET | `/api/bookmarks` | Bearer | List bookmarks |
| POST | `/api/bookmarks` | Bearer | Create a bookmark and fetch metadata in the background |
| GET | `/api/bookmarks/{bookmark_id}` | Bearer | Get a bookmark |
| PATCH | `/api/bookmarks/{bookmark_id}` | Bearer | Partially update a bookmark |
| DELETE | `/api/bookmarks/{bookmark_id}` | Bearer | Soft-delete a bookmark (`hard=true` permanently deletes) |
| GET | `/ui/notes` | Session cookie | Render notes page |
| POST | `/ui/notes` | Session cookie | Create a note and return its HTML row |
| DELETE | `/ui/notes/{note_id}` | Session cookie | Soft-delete a note |
| GET | `/ui/bookmarks` | Session cookie | Render bookmarks page |
| POST | `/ui/bookmarks` | Session cookie | Create a bookmark and return its HTML row |
| DELETE | `/ui/bookmarks/{bookmark_id}` | Session cookie | Soft-delete a bookmark |

List endpoints accept `include_deleted=true` to include soft-deleted records.

## Expenses

All expense endpoints require the API bearer token. Expense amounts are represented as
integer minor units (for example, `1299` is USD 12.99). List results are newest first;
`since` and `until` filter by occurrence time. Deletes are soft by default and accept
`hard=true` for permanent deletion.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/expenses` | List expenses; accepts `since`, `until`, and `include_deleted` |
| GET | `/api/expenses/summary?month=YYYY-MM` | Get the month total and category totals |
| GET | `/api/expenses/{expense_id}` | Get an expense |
| POST | `/api/expenses` | Create an expense |
| PATCH | `/api/expenses/{expense_id}` | Partially update an expense |
| DELETE | `/api/expenses/{expense_id}?hard=true` | Soft-delete by default; permanently delete with `hard=true` |

## Examples

Create a note:

```sh
BASE_URL=http://localhost:8000
curl -X POST "$BASE_URL/api/notes" \
  -H "Authorization: Bearer $UNIFY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Idea","body":"Build something useful","tags":["work"]}'
```

List notes:

```sh
curl "$BASE_URL/api/notes" -H "Authorization: Bearer $UNIFY_API_TOKEN"
```

Create a bookmark:

```sh
curl -X POST "$BASE_URL/api/bookmarks" \
  -H "Authorization: Bearer $UNIFY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","tags":["reference"]}'
```

Create an expense (USD 12.99):

```sh
curl -X POST "$BASE_URL/api/expenses" \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"amount_minor":1299,"currency":"USD","category":"dining","note":"Lunch"}'
```

Get the summary for the current month:

```sh
curl "$BASE_URL/api/expenses/summary?month=$(date +%Y-%m)" \
  -H "Authorization: ******"
```

List expenses for a date range:

```sh
curl --get "$BASE_URL/api/expenses" \
  -H "Authorization: ******" \
  --data-urlencode "since=2026-10-01T00:00:00Z" \
  --data-urlencode "until=2026-10-31T23:59:59Z"
```

An unauthenticated API request returns 401:

```sh
curl -i "$BASE_URL/api/notes"
```

The app's current OpenAPI snapshot is [openapi.json](openapi.json). While the app is
running, `make openapi` refreshes it. Interactive documentation is available at
[`/docs`](http://localhost:8000/docs) (Swagger UI) and
[`/redoc`](http://localhost:8000/redoc).
