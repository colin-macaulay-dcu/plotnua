#!/usr/bin/env python3
"""
VISUAL REVIEW CAPTURE · JOB 1 journey exits
===============================================================================
Renders the EXACT candidate files — no harness copy, no modified markup — over a
local HTTP server from the repository root, drives each journey to its real end
state by clicking its own controls, and captures desktop and 390px views.

NOTHING IS WRITTEN TO ANY CANDIDATE FILE. The server is read-only and the only
outputs are PNGs under the capture directory.

The journeys are driven through their own UI: the real Start control, then the
first option on each question screen, until the page's own reveal section
carries .is-on. No state is injected and no engine function is called directly,
so what is captured is a real end state the page produced for itself.

    python3 capture-journey-exit-review.py [--outdir DIR]
"""

import http.server
import os
import pathlib
import socketserver
import sys
import threading
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(os.environ.get("CAPTURE_OUT", "/tmp/job1-review"))
if "--outdir" in sys.argv:
    OUT = pathlib.Path(sys.argv[sys.argv.index("--outdir") + 1])
OUT.mkdir(parents=True, exist_ok=True)

PORT = 8787
DESKTOP = {"width": 1440, "height": 1000}
MOBILE = {"width": 390, "height": 844}

# (label, url, prefix) — prefix is the journey's own DOM prefix
TARGETS = [
    ("A · ordinary Property Check — Hidden Bins",
     "disc029-hidden-bins-check.html", "hb"),
    ("B · DISC-025 The Borrowed Garden (preview-gated interest)",
     "disc025-borrowed-garden-check.html?interest=preview", "bg"),
]


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def translate_path(self, path):
        rel = path.split("?", 1)[0].split("#", 1)[0].lstrip("/")
        return str(ROOT / rel)


def serve():
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


DRIVE = """
(prefix) => {
  const start = document.getElementById(prefix + 'Start');
  if (start) start.click();
  return !!start;
}
"""

ANSWER = """
(prefix) => {
  const box = document.getElementById(prefix + 'Opts');
  if (!box) return 'no-opts';
  const o = box.querySelector('button, [role="button"], .pc-opt, a');
  if (!o) return 'no-option';
  o.click();
  return 'clicked';
}
"""

REVEALED = """
(prefix) => {
  const r = document.getElementById(prefix + 'Reveal');
  return !!(r && r.classList.contains('is-on'));
}
"""


def shot(page, path, full=True):
    page.screenshot(path=str(path), full_page=full)
    kb = path.stat().st_size // 1024
    print("      %-52s %4d KB" % (path.name, kb))


def main():
    from playwright.sync_api import sync_playwright
    httpd = serve()
    base = "http://127.0.0.1:%d/" % PORT
    print("\n  VISUAL REVIEW CAPTURE · JOB 1")
    print("  serving %s at %s\n" % (ROOT.name, base))
    notes = []

    with sync_playwright() as p:
        br = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage",
                                     "--disable-gpu",
                                     "--force-prefers-reduced-motion"])
        for label, url, pfx in TARGETS:
            print("  %s" % label)
            for name, vp in (("desktop-1440", DESKTOP), ("mobile-390", MOBILE)):
                pg = br.new_page(viewport=vp, device_scale_factor=2 if
                                 name.startswith("mobile") else 1)
                pg.goto(base + url, wait_until="load")
                pg.wait_for_timeout(500)
                if not pg.evaluate(DRIVE, pfx):
                    notes.append("%s: no %sStart control found" % (url, pfx))
                pg.wait_for_timeout(250)
                for i in range(12):
                    if pg.evaluate(REVEALED, pfx):
                        break
                    r = pg.evaluate(ANSWER, pfx)
                    if r != "clicked":
                        break
                    pg.wait_for_timeout(220)
                ok = pg.evaluate(REVEALED, pfx)
                if not ok:
                    notes.append("%s (%s): reveal not reached" % (url, name))
                tag = url.split(".html")[0].split("?")[0]
                # the end state, full page, so the footer is in frame
                shot(pg, OUT / ("%s__%s__END+FOOTER.png" % (tag, name)))
                # and the boundary: the last of the experience + the footer
                pg.evaluate("""() => {
                  const m = document.querySelector('main');
                  const f = document.querySelector('footer.pnx');
                  if (f) f.scrollIntoView({block:'center'});
                  else if (m) window.scrollTo(0, document.body.scrollHeight);
                }""")
                pg.wait_for_timeout(300)
                shot(pg, OUT / ("%s__%s__BOUNDARY.png" % (tag, name)),
                     full=False)
                pg.close()
            print()

        # C · the power station: no header home link before this change
        print("  C · disc026-power-station.html")
        for name, vp in (("desktop-1440", DESKTOP), ("mobile-390", MOBILE)):
            pg = br.new_page(viewport=vp, device_scale_factor=2 if
                             name.startswith("mobile") else 1)
            pg.goto(base + "disc026-power-station.html", wait_until="load")
            pg.wait_for_timeout(900)
            pg.evaluate("""() => {
              const f = document.querySelector('footer.pnx');
              if (f) f.scrollIntoView({block:'center'});
            }""")
            pg.wait_for_timeout(300)
            shot(pg, OUT / ("disc026-power-station__%s__FOOTER.png" % name),
                 full=False)
            routes = pg.evaluate("""() => {
              const f = document.querySelector('footer.pnx');
              if (!f) return null;
              return Array.from(f.querySelectorAll('a')).map(a => ({
                text: a.textContent.trim(), href: a.getAttribute('href')
              }));
            }""")
            if name == "desktop-1440":
                print("      footer routes actually in the DOM:")
                for r in (routes or []):
                    print("        %-34s -> %s" % (r["text"][:34], r["href"]))
            pg.close()
        print()

        # D · the 404 and its new Search pill
        print("  D · 404.html")
        for name, vp in (("desktop-1440", DESKTOP), ("mobile-390", MOBILE)):
            pg = br.new_page(viewport=vp, device_scale_factor=2 if
                             name.startswith("mobile") else 1)
            pg.goto(base + "404.html", wait_until="load")
            # MEASURED, not guessed. search.css gives .pns-pill
            # `transition: opacity 1.6s ease` and the page's own script adds
            # .brand-mark.in at 900ms, which is what triggers
            # `.brand-mark.in ~ .pns-pill { opacity:1 }`. Opacity therefore
            # reaches 1 at about 2.5s. A 1400ms wait caught the pill mid-fade at
            # 0.24 and the first capture run reported it as possibly broken; it
            # was the capture that was wrong, not the page.
            pg.wait_for_timeout(3400)
            assert pg.evaluate(
                "()=>getComputedStyle(document.querySelector('a.pns-pill'))"
                ".opacity === '1'"), "pill had not finished fading in"
            shot(pg, OUT / ("404__%s__TOP.png" % name), full=False)
            box = pg.evaluate("""() => {
              const p = document.querySelector('a.pns-pill');
              if (!p) return null;
              const r = p.getBoundingClientRect();
              const cs = getComputedStyle(p);
              return {x:Math.round(r.x), y:Math.round(r.y),
                      w:Math.round(r.width), h:Math.round(r.height),
                      opacity:cs.opacity, visibility:cs.visibility,
                      label:p.textContent.trim(), href:p.getAttribute('href')};
            }""")
            print("      pill @%s: %s" % (name, box))
            if not box:
                notes.append("404 (%s): no .pns-pill in the DOM" % name)
            elif float(box["opacity"]) < 0.9:
                notes.append("404 (%s): pill opacity %s — may not have faded in"
                             % (name, box["opacity"]))
            pg.close()
        br.close()
    httpd.shutdown()

    print("\n  captured to %s" % OUT)
    if notes:
        print("\n  NOTES — things the capture could not establish:")
        for n in notes:
            print("    - %s" % n)
    else:
        print("\n  every target reached its intended state.")
    print()


if __name__ == "__main__":
    main()
