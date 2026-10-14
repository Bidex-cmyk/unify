# Screenshots

Captured locally against a dev server with sample data only — no real tokens,
passwords, or private information. Each image is 1200×750 PNG.

- `login.png` — the sign-in page.
- `notes.png` — notes list containing three sample notes.
- `bookmarks.png` — bookmarks list containing three sample bookmarks with titles populated.
- `expenses.png` — monthly summary, category chart, and an expense list.
- `swagger.png` — the `/docs` Swagger UI page.

To refresh them, start the app on a scratch database, sign in, add sample data, then
capture each page at a 1200×750 viewport:

```sh
rm -f verify.db && UNIFY_DATABASE_URL=sqlite:///./verify.db uv run alembic upgrade head
UNIFY_DATABASE_URL=sqlite:///./verify.db uv run uvicorn unify.main:app --port 8000
```
