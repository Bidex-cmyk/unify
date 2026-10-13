# Demo recording plan

Target duration: 20–25 seconds. Record at 12 fps and around 1000 px wide; keep the
finished GIF below 3 MB so it loads quickly from GitHub's CDN.

## Before recording

Start the app in a terminal:

```sh
make dev
```

Use a browser window sized to roughly 1200×750. Keep a second terminal ready for the
final API request. The development login password is `UNIFY_UI_PASSWORD` from `.env`
(the default is `dev-password-change-me`).

## Timed sequence

| Time | Action |
| --- | --- |
| 0–2s | Show the terminal with `make dev` running, then switch to `http://localhost:8000/`. |
| 2–5s | Click **Notes** in the navigation. At `/login`, enter the configured UI password and click **Sign in**. |
| 5–9s | Type a short title and note body; click **Add note** and pause for the new row. |
| 9–12s | Click **Bookmarks**. Enter `https://example.com` and click **Add bookmark**. |
| 12–15s | Pause briefly for the background title fetch to populate the bookmark row. |
| 15–17s | Click **Delete** on the bookmark and show the row disappearing. |
| 17–22s | Switch to the terminal and run the authenticated API example below. Show its JSON response. |

Optional short captions: “Sign in”, “Add a note”, “Metadata fetched in background”, and
“Same data, authenticated API”. Keep captions readable and avoid covering form controls.

For the final terminal shot, set the token from `.env` or use the development default:

```sh
TOKEN="${UNIFY_API_TOKEN:-dev-token-change-me}"
curl -sS http://localhost:8000/api/notes \
  -H "Authorization: Bearer $TOKEN"
```

## Recording tools

- Linux: Peek
- macOS: Kap
- Windows: ScreenToGif
- Linux purists: ffmpeg with `x11grab`

Convert a captured MP4 to an optimized starting-point GIF:

```sh
ffmpeg -i in.mp4 -vf "fps=12,scale=1000:-1" -loop 0 docs/demo.gif
```

Check the file size and reduce the frame rate, dimensions, or clip duration as needed to
stay below 3 MB. If `docs/demo.gif` does not exist yet, the README image link will 404 on
GitHub until the GIF is added; that is fine for now.
