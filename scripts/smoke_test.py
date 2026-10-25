#!/usr/bin/env python3
"""Browser smoke test of the built site (CLAUDE.md "Definition of done").

For every HTML page in the site directory (default: public/), in headless Chromium:
- no request leaves the local server (the page is self-contained),
- no console error and no uncaught JavaScript exception,
- each language button FR/EN/NL/DE switches <html lang>,
- the page renders without horizontal scroll at 360 px wide.
Exit code 1 if any page fails.
"""

import functools
import http.server
import pathlib
import sys
import threading

from playwright.sync_api import sync_playwright

LANGS = ("fr", "en", "nl", "de")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep CI logs readable
        pass


def serve(root: pathlib.Path):
    handler = functools.partial(QuietHandler, directory=str(root))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def check_page(browser, base: str, rel: str) -> list:
    errors = []
    for width, label in ((1280, "desktop"), (360, "mobile")):
        ctx = browser.new_context(viewport={"width": width, "height": 800})
        page = ctx.new_page()
        page.on("console", lambda m: m.type == "error" and errors.append(f"console error: {m.text}"))
        page.on("pageerror", lambda e: errors.append(f"uncaught exception: {e}"))

        def guard(route):
            if route.request.url.startswith(base):
                route.continue_()
            else:
                errors.append(f"external request blocked: {route.request.url}")
                route.abort()

        page.route("**/*", guard)
        page.goto(f"{base}/{rel}", wait_until="load")
        if label == "desktop":
            for lang in LANGS:
                btn = page.locator(f'button[data-lang="{lang}"]')
                if btn.count() == 0:
                    errors.append(f"no language button for '{lang}'")
                    continue
                btn.first.click()
                got = page.evaluate("document.documentElement.lang")
                if got != lang:
                    errors.append(f"button '{lang}' sets <html lang>='{got}'")
        else:
            overflow = page.evaluate(
                "document.documentElement.scrollWidth - document.documentElement.clientWidth"
            )
            if overflow > 0:
                errors.append(f"horizontal scroll at 360 px ({overflow} px overflow)")
        ctx.close()
    return errors


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "public").resolve()
    pages = sorted(p.relative_to(root).as_posix() for p in root.rglob("*.html"))
    if not pages:
        print(f"FAIL no HTML page found in {root}")
        return 1
    srv, base = serve(root)
    failed = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for rel in pages:
            errs = check_page(browser, base, rel)
            if errs:
                failed += 1
                for e in errs:
                    print(f"FAIL {rel}: {e}")
            else:
                print(f"OK   {rel}")
        browser.close()
    srv.shutdown()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
