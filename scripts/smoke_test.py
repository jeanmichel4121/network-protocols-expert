#!/usr/bin/env python3
"""Browser smoke test of the built site (CLAUDE.md "Definition of done", docs/web-standards.md).

Serves the site directory (default: public/) on a local port and, in headless Chromium:
- every page: no request leaves the local server, no console error, no uncaught exception;
- accessibility: axe-core, WCAG 2.0/2.1/2.2 A+AA rules, in the light AND the dark theme;
- layout stability: cumulative layout shift below 0.1 (Core Web Vitals "good");
- reduced motion: no CSS animation running at load when the user asks for less motion;
- language pages (/xx/...): the FR/EN/NL/DE buttons switch <html lang> in place and move
  the URL to the matching language; canonical + hreflang (4 + x-default) are consistent;
- mobile: no horizontal page scroll at 360 px;
- the root page sends the visitor to a language.
axe-core is downloaded once from the npm registry at a pinned version and verified
against its pinned sha512 integrity before use.
Exit code 1 if any page fails.
"""

import base64
import functools
import hashlib
import http.server
import io
import json
import pathlib
import re
import sys
import tarfile
import threading
import urllib.request

from playwright.sync_api import sync_playwright

LANGS = ("fr", "en", "nl", "de")
AXE_VERSION = "4.14.0"
AXE_INTEGRITY = (
    "sha512-9WTZxEjsZ7b13TH8JPmbV2z8CHbl80/2hm3XPEG4JgNdQLK81IBRXmSxHfMAOkSqQeRxT/0dwNDz2GOm3zzpcQ=="
)
AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
CLS_BUDGET = 0.1
CACHE = pathlib.Path(".cache")

CLS_PROBE = """
window.__cls = 0;
new PerformanceObserver(list => {
  for (const e of list.getEntries()) if (!e.hadRecentInput) window.__cls += e.value;
}).observe({ type: "layout-shift", buffered: true });
"""


def axe_source() -> str:
    cached = CACHE / f"axe-{AXE_VERSION}.min.js"
    if cached.exists():
        return cached.read_text(encoding="utf-8")
    url = f"https://registry.npmjs.org/axe-core/-/axe-core-{AXE_VERSION}.tgz"
    blob = urllib.request.urlopen(url, timeout=60).read()
    digest = "sha512-" + base64.b64encode(hashlib.sha512(blob).digest()).decode()
    if digest != AXE_INTEGRITY:
        sys.exit(f"axe-core {AXE_VERSION}: integrity mismatch ({digest})")
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        src = tar.extractfile("package/axe.min.js").read().decode("utf-8")
    CACHE.mkdir(exist_ok=True)
    cached.write_text(src, encoding="utf-8")
    return src


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep CI logs readable
        pass


def serve(root: pathlib.Path):
    handler = functools.partial(QuietHandler, directory=str(root))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def new_page(browser, base: str, errors: list, **ctx_opts):
    ctx = browser.new_context(**ctx_opts)
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
    page.add_init_script(CLS_PROBE)
    return ctx, page


def run_axe(page, axe: str, label: str) -> list:
    page.add_script_tag(content=axe)
    res = page.evaluate(
        "tags => axe.run(document, { runOnly: { type: 'tag', values: tags }, resultTypes: ['violations'] })",
        AXE_TAGS,
    )
    out = []
    for v in res["violations"]:
        targets = ", ".join(" ".join(n["target"]) for n in v["nodes"][:3])
        out.append(f"axe [{label}] {v['id']} ({v['impact']}): {v['help']}: {targets}")
    return out


def check_alternates(page, base: str, rel: str) -> list:
    errors = []
    lang, path = rel.split("/", 1)
    path = path[: -len("index.html")]
    links = page.evaluate(
        """() => ({
          canonical: document.querySelector('link[rel=canonical]')?.href || '',
          alts: [...document.querySelectorAll('link[rel=alternate][hreflang]')].map(l => [l.hreflang, l.href])
        })"""
    )
    if not links["canonical"].endswith(f"/{lang}/{path}"):
        errors.append(f"canonical {links['canonical']!r} does not point to this page")
    alts = dict(links["alts"])
    for code in LANGS:
        if not alts.get(code, "").endswith(f"/{code}/{path}"):
            errors.append(f"hreflang '{code}' missing or wrong: {alts.get(code)!r}")
    if "x-default" not in alts:
        errors.append("hreflang 'x-default' missing")
    return errors


def check_page(browser, base: str, rel: str, axe: str) -> list:
    errors = []
    built = re.match(r"^(fr|en|nl|de)/", rel)

    # Desktop, light theme: axe, CLS, language switching, alternates.
    ctx, page = new_page(browser, base, errors, viewport={"width": 1280, "height": 900}, color_scheme="light")
    page.goto(f"{base}/{rel}", wait_until="load")
    page.wait_for_timeout(400)
    cls = page.evaluate("window.__cls")
    if cls > CLS_BUDGET:
        errors.append(f"cumulative layout shift {cls:.3f} > {CLS_BUDGET}")
    errors += run_axe(page, axe, "light")
    if built:
        errors += check_alternates(page, base, rel)
        for lang in LANGS:
            btn = page.locator(f'button[data-lang="{lang}"]')
            if btn.count() == 0:
                errors.append(f"no language button for '{lang}'")
                continue
            btn.first.click()
            got = page.evaluate("document.documentElement.lang")
            if got != lang:
                errors.append(f"button '{lang}' sets <html lang>='{got}'")
            if not page.evaluate("location.pathname").startswith(f"/{lang}/"):
                errors.append(f"button '{lang}' does not move the URL to /{lang}/")
    ctx.close()

    # Dark theme: colour contrast must hold in both themes.
    ctx, page = new_page(browser, base, errors, viewport={"width": 1280, "height": 900}, color_scheme="dark")
    page.goto(f"{base}/{rel}", wait_until="load")
    errors += run_axe(page, axe, "dark")
    ctx.close()

    # Reduced motion: nothing animates on its own.
    ctx, page = new_page(
        browser, base, errors, viewport={"width": 1280, "height": 900}, reduced_motion="reduce"
    )
    page.goto(f"{base}/{rel}", wait_until="load")
    page.wait_for_timeout(300)
    running = page.evaluate(
        "document.getAnimations().filter(a => a.playState === 'running'"
        " && a.effect && a.effect.getComputedTiming().duration > 50).length"
    )
    if running:
        errors.append(f"{running} animation(s) running at load with prefers-reduced-motion: reduce")
    # Script-driven motion (e.g. the hero topology) must stay still too.
    probe = (
        "[...document.querySelectorAll('svg [transform]')].map(n => n.getAttribute('transform')).join('|')"
    )
    before = page.evaluate(probe)
    page.wait_for_timeout(700)
    if page.evaluate(probe) != before:
        errors.append("script animation moves with prefers-reduced-motion: reduce")
    ctx.close()

    # Mobile: no horizontal page scroll at 360 px, and axe again (the layout changes).
    ctx, page = new_page(browser, base, errors, viewport={"width": 360, "height": 780})
    page.goto(f"{base}/{rel}", wait_until="load")
    errors += run_axe(page, axe, "mobile")
    overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    if overflow > 0:
        errors.append(f"horizontal scroll at 360 px ({overflow} px overflow)")
    ctx.close()
    return errors


def check_root(browser, base: str) -> list:
    errors = []
    ctx, page = new_page(browser, base, errors, locale="de-DE")
    page.goto(f"{base}/", wait_until="load")
    page.wait_for_url(re.compile(r".*/de/$"), timeout=5000)
    ctx.close()
    return errors


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "public").resolve()
    pages = sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*.html")
        if p.relative_to(root).as_posix() != "index.html"
    )
    if not pages:
        print(f"FAIL no HTML page found in {root}")
        return 1
    axe = axe_source()
    srv, base = serve(root)
    failed = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        results = [("index.html", check_root(browser, base) if (root / "index.html").exists() else [])]
        results += [(rel, check_page(browser, base, rel, axe)) for rel in pages]
        browser.close()
    srv.shutdown()
    for rel, errs in results:
        if errs:
            failed += 1
            for e in errs:
                print(f"FAIL {rel}: {e}")
        else:
            print(f"OK   {rel}")
    print(json.dumps({"pages": len(results), "failed": failed}))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
