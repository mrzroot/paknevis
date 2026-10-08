"""End-to-end test of the playground with a headless browser (Playwright).

Serves ``docs/`` locally (or tests ``--url``), waits for Pyodide to load the
real package, types messy Persian text and checks that fixes appear.

    pip install playwright && playwright install chromium
    python scripts/e2e_playground.py [--url https://mrzroot.github.io/paknevis/] [--shots DIR]
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import socketserver
import sys
import threading
from collections.abc import Iterator
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

DOCS = Path(__file__).resolve().parent.parent / "docs"
TYPED = "علي مي خواهد , كتاب هاي خوب بخواند ?"
EXPECTED = "علی می\u200cخواهد، کتاب\u200cهای خوب بخواند؟"


@contextlib.contextmanager
def serve_docs() -> Iterator[str]:
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass

    handler = functools.partial(QuietHandler, directory=str(DOCS))
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_address[1]}/"
        finally:
            server.shutdown()


def run(url: str, shots: Path | None, channel: str | None) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=channel) if channel else p.chromium.launch()
        for scheme in ("light", "dark"):
            page = browser.new_page(
                viewport={"width": 1360, "height": 1000}, color_scheme=scheme, device_scale_factor=1
            )
            errors: list[str] = []
            page.on("pageerror", lambda exc, errs=errors: errs.append(str(exc)))
            page.goto(url)
            expect(page.locator("body")).to_have_attribute("data-engine", "ready", timeout=180_000)
            expect(page.locator("#status")).to_have_attribute("data-state", "ready")
            if scheme == "light":
                # Type fresh text and wait for the live fixes.
                page.click('[data-sample="clear"]')
                page.locator("#input").press_sequentially(TYPED, delay=15)
                page.click("#tab-fixed")
                expect(page.locator("#view-fixed")).to_have_text(EXPECTED, timeout=30_000)
                assert int(page.locator(".diag-list li").count()) >= 5, "expected diagnostics in the list"
                page.click("#tab-issues")
                expect(page.locator("mark.issue").first).to_be_visible()
                # The real Markdown sample: code must be untouched.
                page.click('[data-sample="markdown"]')
                page.click("#tab-fixed")
                expect(page.locator("#view-fixed")).to_contain_text("pip install paknevis  # كد دست نمي خورد , ?")
                expect(page.locator("#view-fixed")).to_contain_text("راهنمای نصب پروژه")
                page.click("#tab-issues")
            page.click('[data-sample="blog"]')
            page.locator("#input").blur()
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(400)
            if shots:
                shots.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(shots / f"playground-fa-{scheme}.png"), full_page=False)
                if scheme == "light":
                    page.click("#tab-fixed")
                    page.evaluate("window.scrollTo(0, 0)")
                    page.wait_for_timeout(200)
                    page.screenshot(path=str(shots / "playground-fa-fixed.png"), full_page=False)
                    page.screenshot(path=str(shots / "playground-fa-full.png"), full_page=True)
                    page.click("#tab-issues")
                    page.click("#lang-toggle")
                    expect(page.locator("html")).to_have_attribute("dir", "ltr")
                    page.wait_for_timeout(200)
                    page.screenshot(path=str(shots / "playground-en-light.png"), full_page=False)
                    page.click("#lang-toggle")
            assert not errors, f"page errors: {errors}"
            page.close()
        browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", help="test a deployed playground instead of serving docs/ locally")
    parser.add_argument("--shots", type=Path, help="directory to write screenshots to")
    parser.add_argument("--channel", help="browser channel, e.g. 'chrome' to use an installed Google Chrome")
    args = parser.parse_args()
    if args.url:
        run(args.url, args.shots, args.channel)
    else:
        with serve_docs() as url:
            run(url, args.shots, args.channel)
    print("playground e2e: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
