#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEARCH V1 · RUNTIME PROOF FOR THE SEARCH PAGE'S OWN FIELD
===============================================================================
THE PROOF THAT WAS MISSING. prove-search-acceptance.mjs reads the source and
passed 149/149 while the big visible field on search.html did nothing: it was
wired to a hidden duplicate, and no amount of reading the markup reveals which
element getElementById actually returns at runtime. That took a browser.

So this one opens a real browser, types like a homeowner, and asserts on what
comes back. It is deliberately narrow — it proves the DEFECT cannot return, not
that Search is correct. Ranking, corpus and copy stay the business of the
acceptance suite.

    python3 atlas-tools/prove-search-page-runtime.py

Needs Playwright with Chromium. If the browser cannot start it says so and
exits 2 — an unrunnable proof must not read as a pass.
"""

import http.server
import pathlib
import socketserver
import sys
import threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
PORT = 8831
QUERY = "powersheds"          # the frozen acceptance query
GOVERNED_IDS = ("pnsInput", "pnsStatus", "pnsResults", "pnsPanel",
                "pnsOpen", "pnsClose")
OTHER_SURFACES = ("index.html", "discoveries.html", "about.html", "404.html")

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print("  [PASS] " + name)
    else:
        failed += 1
        print("  [FAIL] " + name + (("\n         " + str(detail)) if detail else ""))


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def translate_path(self, path):
        return str(ROOT / path.split("?", 1)[0].split("#", 1)[0].lstrip("/"))


def main():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:                                  # pragma: no cover
        print("CANNOT RUN: playwright is not available (%s)" % exc)
        return 2

    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d/" % PORT

    print("\n  SEARCH V1 · RUNTIME PROOF — the Search page's own field\n")
    try:
        with sync_playwright() as p:
            try:
                br = p.chromium.launch(args=["--no-sandbox",
                                             "--disable-dev-shm-usage",
                                             "--disable-gpu"])
            except Exception as exc:
                print("CANNOT RUN: chromium would not start (%s)" % exc)
                return 2

            # ---------------------------------------------- search.html itself
            pg = br.new_page(viewport={"width": 1440, "height": 1000})
            fetched = []
            pg.on("response", lambda r: fetched.append(r.url)
                  if "search-index" in r.url else None)
            pg.goto(base + "search.html", wait_until="load")
            pg.wait_for_timeout(1500)

            # 10 · no duplicate governed id survives anywhere on the page
            dupes = {}
            for gid in GOVERNED_IDS:
                n = pg.evaluate("(g) => document.querySelectorAll('#' + g).length", gid)
                if n > 1:
                    dupes[gid] = n
            check("S1 no governed Search id appears twice on search.html",
                  not dupes, dupes)

            # 2 · the VISIBLE primary field, found the way a homeowner finds it
            vis = [e for e in pg.query_selector_all("input.pns-input")
                   if e.is_visible()]
            check("S2 exactly one visible primary search field", len(vis) == 1,
                  "found %d" % len(vis))
            if not vis:
                br.close()
                return 1
            field = vis[0]

            # 4 · the index is available (eagerly loaded when there is no panel)
            check("S3 the Search V1 index is fetched without the homeowner "
                  "having to open anything", bool(fetched), fetched)

            # 3 · type the frozen acceptance query
            field.click()
            pg.keyboard.type(QUERY, delay=60)
            pg.wait_for_timeout(1800)

            # 5 · visible results
            links = pg.evaluate(
                "() => document.getElementById('pnsResults')"
                ".querySelectorAll('a').length")
            check("S4 typing %r into the visible field returns results" % QUERY,
                  links > 0, "%d links" % links)

            shown = pg.evaluate("""() => {
              const r = document.getElementById('pnsResults');
              const b = r.getBoundingClientRect();
              return b.height > 0 && (r.textContent || '').trim().length > 0;
            }""")
            check("S5 the results area is actually visible, not just populated",
                  shown)

            # 6 · the expected Powersheds supplier/product behaviour
            txt = pg.evaluate(
                "() => document.getElementById('pnsResults').textContent"
                ".replace(/\\s+/g, ' ')")
            check("S6 the Powersheds supplier result is present",
                  "Powersheds" in txt, txt[:120])
            check("S7 its products are offered under it",
                  "products in Atlas" in txt or "View 3 products" in txt,
                  txt[:160])

            # 7 · the status line updates
            status = pg.evaluate(
                "() => document.getElementById('pnsStatus').textContent.trim()")
            check("S8 the visible status line updates", bool(status),
                  repr(status))

            # 8 · the pill is still there, and on this page it focuses the field
            pill = pg.evaluate("""() => {
              const o = document.getElementById('pnsOpen');
              if (!o) return null;
              const r = o.getBoundingClientRect();
              return { visible: r.width > 0 && r.height > 0,
                       current: o.getAttribute('data-pns-current'),
                       href: o.getAttribute('href') };
            }""")
            check("S9 the approved Search pill is still present and visible",
                  pill and pill["visible"], pill)
            check("S10 on search.html the pill is marked current and points at "
                  "search.html", pill and pill["current"] == "true"
                  and pill["href"] == "search.html", pill)
            pg.evaluate("() => document.getElementById('pnsOpen').click()")
            pg.wait_for_timeout(400)
            check("S11 clicking the pill focuses the field already on the page "
                  "rather than opening a second Search",
                  pg.evaluate("() => document.activeElement === "
                              "document.getElementById('pnsInput')"))

            check("S12 no horizontal overflow on search.html",
                  pg.evaluate("() => document.documentElement.scrollWidth - "
                              "document.documentElement.clientWidth") <= 1)
            pg.close()

            # 9 · Search still works from representative non-search pages
            for page in OTHER_SURFACES:
                p2 = br.new_page(viewport={"width": 1440, "height": 1000})
                p2.goto(base + page, wait_until="load")
                p2.wait_for_timeout(1200)
                p2.evaluate("() => document.querySelector('a.pns-pill').click()")
                p2.wait_for_timeout(700)
                ins = [e for e in p2.query_selector_all("input.pns-input")
                       if e.is_visible()]
                n = 0
                if ins:
                    ins[0].click()
                    p2.keyboard.type(QUERY, delay=50)
                    p2.wait_for_timeout(1700)
                    n = p2.evaluate(
                        "() => document.getElementById('pnsResults')"
                        ".querySelectorAll('a').length")
                check("S13 Search still works through the overlay on %s" % page,
                      n > 0, "%d links" % n)
                p2.close()

            br.close()
    finally:
        httpd.shutdown()

    print("\n  %d passed, %d failed\n" % (passed, failed))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
