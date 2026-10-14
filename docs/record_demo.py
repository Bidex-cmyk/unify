"""Record the README demo GIF by driving the unify UI in a real browser.

The walkthrough is captured as a Chrome DevTools Protocol screencast (real compositor
frames, not periodic screenshots), captioned, then encoded to a palette GIF.

Prerequisites
-------------
- ffmpeg on PATH (used for the two-pass palette encode; a ffmpeg-free encode is roughly
  8x larger and overshoots the 3 MB budget).
- Playwright with Chromium: ``uv run --with playwright playwright install chromium``.
- A dev server on a *fresh* database, so the walkthrough starts from an empty state::

      rm -f unify.db && make migrate
      make dev

Run it with::

    uv run --with playwright --with pillow python docs/record_demo.py

The script waits on the app's own UI state at each step, so it fails loudly if a screen
or control changes rather than silently recording an error page.
"""

from __future__ import annotations

import argparse
import base64
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

FPS = 12
WIDTH, HEIGHT = 1200, 750
FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
)


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def record(base_url: str, frames_dir: Path, password: str) -> tuple[list[float], list[dict], float]:
    """Drive the walkthrough, returning frame timestamps, caption marks, and duration."""
    frames: list[tuple[float, bytes]] = []
    marks: list[tuple[int, str]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            device_scale_factor=1,
            color_scheme="light",
        )
        page = context.new_page()

        # Warm the CDN cache so the recording does not open on a cold start.
        page.goto(f"{base_url}/", wait_until="networkidle")
        page.goto(f"{base_url}/login", wait_until="networkidle")

        cdp = context.new_cdp_session(page)

        def on_frame(params: dict) -> None:
            frames.append(
                (float(params["metadata"]["timestamp"]), base64.b64decode(params["data"]))
            )
            cdp.send("Page.screencastFrameAck", {"sessionId": params["sessionId"]})

        cdp.on("Page.screencastFrame", on_frame)
        cdp.send(
            "Page.startScreencast",
            {"format": "jpeg", "quality": 82, "maxWidth": WIDTH, "maxHeight": HEIGHT},
        )
        started = time.monotonic()

        def caption(text: str) -> None:
            marks.append((len(frames), text))
            print(f"    caption: {text}")

        caption("One self-hosted home for notes, bookmarks, and expenses")
        page.goto(f"{base_url}/", wait_until="networkidle")
        page.wait_for_timeout(1400)

        caption("Sign in")
        page.click("nav a:has-text('Notes')")
        page.wait_for_url("**/login")
        page.wait_for_timeout(500)
        page.keyboard.type(password, delay=45)
        page.keyboard.press("Enter")
        page.wait_for_url("**/ui/notes")
        page.wait_for_timeout(600)

        caption("Add a note")
        page.click("input[name=title]")
        page.keyboard.type("Groceries list", delay=55)
        page.click("textarea[name=body]")
        page.keyboard.type("milk, eggs, bread, coffee", delay=40)
        page.click("button:has-text('Add note')")
        page.wait_for_timeout(1400)

        page.click("nav a:has-text('Bookmarks')")
        page.wait_for_url("**/ui/bookmarks")
        page.wait_for_timeout(400)
        caption("Bookmarks fetch their own titles in the background")
        page.click("input[name=url]")
        page.keyboard.type("https://example.com", delay=45)
        page.click("button:has-text('Add bookmark')")
        # Wait for the background fetch to land in the row, rather than guessing a delay.
        page.wait_for_selector(
            "#bookmarks-list article h3:has-text('Example Domain')", timeout=15000
        )

        page.click("nav a:has-text('Expenses')")
        page.wait_for_url("**/ui/expenses")
        page.wait_for_timeout(400)
        caption("Log spending — the month's summary and chart keep up")
        for amount, category, note in (
            ("12.50", "food", "lunch"),
            ("42.00", "transport", "train pass"),
        ):
            page.click("input[name=amount]")
            page.keyboard.type(amount, delay=70)
            page.click("input[name=category]")
            page.keyboard.press("Control+a")
            page.keyboard.type(category, delay=55)
            page.click("input[name=note]")
            page.keyboard.type(note, delay=50)
            page.click("button:has-text('Add expense')")
            page.wait_for_timeout(1100)

        caption("The same data over the authenticated JSON API")
        page.set_extra_http_headers({"Authorization": f"Bearer {api_token()}"})
        response = page.goto(f"{base_url}/api/expenses", wait_until="networkidle")
        if response is None or response.status != 200:
            status = response.status if response is not None else "no response"
            raise SystemExit(f"API step failed ({status}); is UNIFY_API_TOKEN the dev default?")
        page.wait_for_timeout(3800)

        cdp.send("Page.stopScreencast")
        stopped = time.monotonic()
        browser.close()

    if not frames:
        raise SystemExit("no screencast frames were captured")

    base = frames[0][0]
    for index, (_, data) in enumerate(frames):
        (frames_dir / f"raw_{index:05d}.jpg").write_bytes(data)

    stamps = [ts - base for ts, _ in frames]
    caption_marks = [
        {"at": stamps[min(index, len(stamps) - 1)], "text": text} for index, text in marks
    ]
    return stamps, caption_marks, stopped - started


def api_token() -> str:
    """The bearer token the running dev server expects."""
    return os.environ.get("UNIFY_API_TOKEN", "dev-token-change-me")


def render(
    frames_dir: Path,
    out_dir: Path,
    stamps: list[float],
    marks: list[dict],
    duration: float,
) -> int:
    """Resample to a constant frame rate and burn the phase captions into each frame."""
    font = load_font(26)
    pad_x, pad_y = 20, 14
    cached_index, cached_image = -1, None

    for number in range(int(duration * FPS)):
        moment = number / FPS
        index = 0
        for i, stamp in enumerate(stamps):
            if stamp > moment:
                break
            index = i
        if index != cached_index:
            cached_image = Image.open(frames_dir / f"raw_{index:05d}.jpg").convert("RGB")
            cached_index = index
        assert cached_image is not None
        frame = cached_image.copy()

        text = ""
        for mark in marks:
            if moment >= mark["at"]:
                text = mark["text"]
        if text:
            draw = ImageDraw.Draw(frame, "RGBA")
            box = draw.textbbox((0, 0), text, font=font)
            text_w, text_h = box[2] - box[0], box[3] - box[1]
            x, y = 32, HEIGHT - 32 - text_h - pad_y * 2
            draw.rounded_rectangle(
                (x, y, x + text_w + pad_x * 2, y + text_h + pad_y * 2),
                radius=10,
                fill=(15, 18, 24, 196),
            )
            draw.text((x + pad_x, y + pad_y - box[1]), text, font=font, fill=(255, 255, 255))

        frame.save(out_dir / f"f{number:04d}.png")
    return len(list(out_dir.glob("f*.png")))


def encode(frames_dir: Path, target: Path) -> None:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required to encode the GIF (see this module's docstring)")
    target.parent.mkdir(parents=True, exist_ok=True)
    filters = (
        "scale=1000:-1:flags=lanczos,split[s0][s1];"
        "[s0]palettegen=max_colors=256:stats_mode=full[p];"
        "[s1][p]paletteuse=dither=none"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-framerate",
            str(FPS),
            "-i",
            str(frames_dir / "f%04d.png"),
            "-vf",
            filters,
            "-loop",
            "0",
            str(target),
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--out", default="docs/demo.gif")
    parser.add_argument("--password", default="dev-password-change-me")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="unify-demo-") as tmp:
        work = Path(tmp)
        raw, rendered = work / "raw", work / "frames"
        raw.mkdir()
        rendered.mkdir()

        print("recording the walkthrough...")
        stamps, marks, duration = record(args.base_url, raw, args.password)
        print(f"  {len(stamps)} frames over {duration:.1f}s")

        print("rendering frames and captions...")
        count = render(raw, rendered, stamps, marks, duration)
        print(f"  {count} frames at {FPS} fps ({count / FPS:.1f}s)")

        print(f"encoding {args.out}...")
        encode(rendered, Path(args.out))

    size_kb = Path(args.out).stat().st_size / 1024
    print(f"wrote {args.out} ({size_kb:.0f} KB)")
    if size_kb > 3 * 1024:
        raise SystemExit("GIF exceeds the 3 MB budget; lower FPS, width, or max_colors")


if __name__ == "__main__":
    main()
