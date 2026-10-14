# Demo GIF

`docs/demo.gif` is a 1000 px wide, 12 fps walkthrough of the app. It plays in about 20
seconds and sits well under the 3 MB budget so GitHub's CDN serves it quickly.

## What it shows

| Time | Beat |
| --- | --- |
| 0–2s | The landing page, logged out: three cards for notes, bookmarks, and expenses. |
| 2–4s | Clicking **Notes** redirects to `/login`; signing in with the UI password. |
| 4–8s | Adding a note; the new row appears and the form resets. |
| 8–13s | Adding a bookmark; the row fills in its title from the background fetch, without a reload. |
| 13–18s | Logging two expenses; the monthly total and the category chart update as they are added. |
| 18–19s | The same data read back over the authenticated JSON API (`GET /api/expenses`). |

A short caption names each beat.

## Reproducing it

The GIF is captured by script rather than by hand. `docs/record_demo.py` drives the UI in
Chromium and records a real Chrome DevTools Protocol screencast, so the frames are the
browser's own compositor output rather than periodic screenshots.

Prerequisites:

- `ffmpeg` on `PATH` (used for the two-pass palette encode; a Pillow-only encode is roughly
  8x larger and overshoots the 3 MB budget).
- Chromium for Playwright: `uv run --with playwright playwright install chromium`.

Start a dev server on a **fresh** database, so the walkthrough begins from an empty state:

```sh
rm -f unify.db && make migrate
make dev
```

Then record, caption, and encode in one pass:

```sh
uv run --with playwright --with pillow python docs/record_demo.py
```

The script waits on the app's own UI state at every step, so a changed screen or control
makes it fail loudly instead of quietly recording an error page. `--base-url`, `--out`, and
`--password` override the defaults.

## Recording by hand

To capture it manually instead — Peek on Linux, Kap on macOS, ScreenToGif on Windows — size
the window near 1200×750 and keep a second terminal ready for the final API request:

```sh
TOKEN="${UNIFY_API_TOKEN:-dev-token-change-me}"
curl -sS http://localhost:8000/api/expenses \
  -H "Authorization: Bearer $TOKEN"
```

Convert the capture to an optimized GIF, then check the size and reduce the frame rate,
dimensions, or duration as needed:

```sh
ffmpeg -i in.mp4 -vf "fps=12,scale=1000:-1" -loop 0 docs/demo.gif
```
