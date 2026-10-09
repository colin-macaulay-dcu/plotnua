#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JOB 6 · INTERACTION SEMANTICS — RUNTIME PROOF
===============================================================================
Search modal focus containment + background inertness, and the My Plot season
controls' semantics.

WHY THIS IS A RUNTIME PROOF AND NOT A SOURCE GREP. The defects Job 6 fixes are
behavioural: "focus escapes forward after five Tabs", "one Shift+Tab reaches
the pill behind the overlay", "the background stays interactive", "inert is
left behind after Back". A static check can only observe whether some code
exists; it cannot observe where focus actually goes. So every Search assertion
here drives real Chromium with real key presses and reads document.activeElement.

The My Plot assertions are DOM-state assertions in the same live page, because
"exactly one button reports pressed" is also a runtime fact.

Usage:  python3 atlas-tools/prove-job6-interaction.py
        python3 atlas-tools/prove-job6-interaction.py --root /some/tree
Exit 0 only if every check passes.
"""
import argparse
import functools
import http.server
import pathlib
import socketserver
import sys
import threading

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parent

# Pages that carry the modal Search panel. your-plot.html deliberately does NOT
# appear here: it carries neither the Search pill nor the panel, so there is no
# modal on it to contain. search.html carries the pill but no panel and is
# asserted separately as the must-not-trap case.
MODAL_PAGES = ["index.html", "discovery-hidden-bins.html", "404.html", "about.html"]
NO_PANEL_PAGE = "search.html"
MYPLOT_PAGE = "your-plot.html"

DESC = """() => {
  const a = document.activeElement;
  if (!a) return 'null';
  const p = document.getElementById('pnsPanel');
  const inside = !!(p && p.contains(a));
  const id = a.id ? ('#' + a.id) : '';
  const cls = (typeof a.className === 'string' && a.className)
    ? ('.' + a.className.trim().split(/\\s+/)[0]) : '';
  return (inside ? 'IN ' : 'OUT ') + a.tagName + id + cls;
}"""

FOCUSABLES = """() => {
  const p = document.getElementById('pnsPanel');
  if (!p) return 0;
  const sel = 'a[href],area[href],button,input,select,textarea,iframe,object,'
            + 'embed,[contenteditable="true"],[tabindex]:not([tabindex="-1"])';
  return [...p.querySelectorAll(sel)]
    .filter(e => !e.disabled && e.getAttribute('aria-hidden') !== 'true'
                 && e.getClientRects().length
                 && getComputedStyle(e).visibility !== 'hidden').length;
}"""

INERT_STATE = """() => {
  const p = document.getElementById('pnsPanel');
  const kids = [...document.body.children];
  return {
    inertCount: kids.filter(k => k.inert).length,
    panelInert: !!(p && p.inert),
    bodyKids: kids.length,
    mainInert: !!(document.querySelector('main') || {}).inert,
    pillInert: !!(document.getElementById('pnsOpen') || {}).inert
  };
}"""


def serve(root, port):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(root))
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


class Checks(object):
    def __init__(self):
        self.rows = []

    def ok(self, cid, label, detail=""):
        self.rows.append((cid, label, True, detail))

    def fail(self, cid, label, detail=""):
        self.rows.append((cid, label, False, detail))

    def that(self, cond, cid, label, detail=""):
        (self.ok if cond else self.fail)(cid, label, detail)
        return bool(cond)

    @property
    def failed(self):
        return [r for r in self.rows if not r[2]]


def open_search(pg):
    """Open via the pill with a real keyboard activation, as a homeowner would."""
    pg.evaluate("() => document.getElementById('pnsOpen').focus()")
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(700)


def run_modal_page(pg, base, page, c, width):
    tag = "%s@%d" % (page.replace(".html", ""), width)
    pg.goto(base + page, wait_until="load")
    pg.wait_for_timeout(2200)

    # --- J1 open: focus enters the field -----------------------------------
    open_search(pg)
    got = pg.evaluate(DESC)
    c.that(got.startswith("IN INPUT#pnsInput"), "J1",
           "%s open -> focus is #pnsInput" % tag, got)

    # --- J2 background inert while open ------------------------------------
    st = pg.evaluate(INERT_STATE)
    c.that(st["inertCount"] >= 1 and not st["panelInert"] and st["mainInert"],
           "J2", "%s background inert, panel not inert" % tag,
           "inert=%d/%d panelInert=%s mainInert=%s"
           % (st["inertCount"], st["bodyKids"], st["panelInert"], st["mainInert"]))

    # --- query with multiple results ---------------------------------------
    pg.keyboard.type("powersheds")
    pg.wait_for_timeout(1500)
    status = pg.eval_on_selector("#pnsStatus", "e => e.textContent.trim()")
    c.that(status == "4 results", "J3",
           "%s query 'powersheds' -> status preserved" % tag, status)
    n = pg.evaluate(FOCUSABLES)
    c.that(n >= 2, "J4", "%s panel exposes focusables" % tag, "n=%d" % n)

    # --- J5 forward containment: two full laps, never leaves ---------------
    escaped = None
    for i in range(1, n * 2 + 3):
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(45)
        d = pg.evaluate(DESC)
        if d.startswith("OUT"):
            escaped = "Tab %d -> %s" % (i, d)
            break
    c.that(escaped is None, "J5",
           "%s forward Tab never leaves the dialog (2 laps)" % tag,
           escaped or "stayed inside for %d presses" % (n * 2 + 2))

    # --- J6 forward wrap: last -> first ------------------------------------
    pg.evaluate("""() => {
      const p = document.getElementById('pnsPanel');
      const sel = 'a[href],button,input,select,textarea,[tabindex]:not([tabindex="-1"])';
      const f = [...p.querySelectorAll(sel)].filter(e => !e.disabled && e.getClientRects().length);
      f[f.length - 1].focus();
    }""")
    pg.keyboard.press("Tab")
    pg.wait_for_timeout(80)
    first_id = pg.evaluate("""() => {
      const p = document.getElementById('pnsPanel');
      const sel = 'a[href],button,input,select,textarea,[tabindex]:not([tabindex="-1"])';
      const f = [...p.querySelectorAll(sel)].filter(e => !e.disabled && e.getClientRects().length);
      return document.activeElement === f[0];
    }""")
    c.that(first_id, "J6", "%s Tab on last wraps to first" % tag)

    # --- J7 backward wrap: first -> last, never the pill -------------------
    pg.evaluate("""() => {
      const p = document.getElementById('pnsPanel');
      const sel = 'a[href],button,input,select,textarea,[tabindex]:not([tabindex=\"-1\"])';
      const f = [...p.querySelectorAll(sel)].filter(e => !e.disabled && e.getClientRects().length);
      f[0].focus();
    }""")
    pg.keyboard.press("Shift+Tab")
    pg.wait_for_timeout(80)
    d = pg.evaluate(DESC)
    last_ok = pg.evaluate("""() => {
      const p = document.getElementById('pnsPanel');
      const sel = 'a[href],button,input,select,textarea,[tabindex]:not([tabindex="-1"])';
      const f = [...p.querySelectorAll(sel)].filter(e => !e.disabled && e.getClientRects().length);
      return document.activeElement === f[f.length - 1];
    }""")
    c.that(d.startswith("IN") and last_ok, "J7",
           "%s Shift+Tab on first wraps to last, not the pill" % tag, d)

    # --- J8 zero-result state still participates ---------------------------
    pg.evaluate("() => document.getElementById('pnsInput').focus()")
    pg.keyboard.press("Control+A")
    pg.keyboard.type("zzzzqqq")
    pg.wait_for_timeout(1300)
    z_status = pg.eval_on_selector("#pnsStatus", "e => e.textContent.trim()")
    zesc = None
    for i in range(1, 8):
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(45)
        if pg.evaluate(DESC).startswith("OUT"):
            zesc = "escaped on Tab %d" % i
            break
    c.that(z_status == "No results" and zesc is None, "J8",
           "%s zero-result state contained" % tag,
           "status=%r %s" % (z_status, zesc or "no escape"))

    # --- J9 back to results: trap adapts to the new control set ------------
    pg.evaluate("() => document.getElementById('pnsInput').focus()")
    pg.keyboard.press("Control+A")
    pg.keyboard.type("powersheds")
    pg.wait_for_timeout(1500)
    resc = None
    for i in range(1, pg.evaluate(FOCUSABLES) + 3):
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(45)
        if pg.evaluate(DESC).startswith("OUT"):
            resc = "escaped on Tab %d" % i
            break
    c.that(resc is None, "J9",
           "%s trap adapts when results return" % tag, resc or "contained")

    # --- J10 Escape close: inert cleared, focus back on the pill -----------
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(500)
    st = pg.evaluate(INERT_STATE)
    d = pg.evaluate(DESC)
    c.that(st["inertCount"] == 0 and not st["pillInert"]
           and d == "OUT A#pnsOpen.pns-pill", "J10",
           "%s Escape: inert cleared, focus on pill" % tag,
           "inert=%d focus=%s" % (st["inertCount"], d))

    # --- J11 close-button route -------------------------------------------
    open_search(pg)
    pg.evaluate("() => document.getElementById('pnsClose').click()")
    pg.wait_for_timeout(500)
    st = pg.evaluate(INERT_STATE)
    c.that(st["inertCount"] == 0, "J11",
           "%s close button: no stale inert" % tag, "inert=%d" % st["inertCount"])



def run_popstate_page(b, base, page, c, width):
    """J12 needs a PRISTINE history. openPanel() pushes an entry every time it
    opens, and re-goto-ing the same URL does not reliably create a new entry —
    so in a reused tab, Back lands on an EARLIER Search entry and correctly
    RE-OPENS Search. An earlier revision of this proof asserted against that
    and reported a false failure. A fresh context gives one clean entry, so
    Back provably lands somewhere with no Search state."""
    tag = "%s@%d" % (page.replace(".html", ""), width)
    ctx = b.new_context(viewport={"width": width, "height": 900})
    pg = ctx.new_page()
    pg.goto(base + page, wait_until="load")
    pg.wait_for_timeout(2200)
    depth_before = pg.evaluate("() => history.length")
    open_search(pg)
    pg.wait_for_timeout(600)
    pushed = pg.evaluate("() => history.length") > depth_before
    pg.go_back()
    pg.wait_for_timeout(1400)
    st = pg.evaluate(INERT_STATE)
    hidden = pg.evaluate("() => { const p = document.getElementById('pnsPanel');"
                         " return !p || p.hidden; }")
    usable = pg.evaluate("() => { const m = document.querySelector('main');"
                         " return !!m && !m.inert; }")
    state_now = pg.evaluate("() => !!(history.state && history.state.pnSearch)")
    c.that(pushed and not state_now and st["inertCount"] == 0 and hidden and usable,
           "J12", "%s Back: panel closed, no stale inert, page usable" % tag,
           "pushedEntry=%s landedOnSearchEntry=%s inert=%d hidden=%s mainUsable=%s"
           % (pushed, state_now, st["inertCount"], hidden, usable))
    ctx.close()

def run(root, port, pages, widths, do_tail):
    from playwright.sync_api import sync_playwright
    base = "http://127.0.0.1:%d/" % port
    c = Checks()
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--no-sandbox"])
        for width in widths:
            ctx = b.new_context(viewport={"width": width, "height": 900})
            pg = ctx.new_page()
            for page in pages:
                run_modal_page(pg, base, page, c, width)
            ctx.close()
            for page in pages:
                run_popstate_page(b, base, page, c, width)
        if not do_tail:
            b.close()
            return report(c)

        # --- J13 the dedicated page must NOT acquire modal behaviour -------
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        pg = ctx.new_page()
        pg.goto(base + NO_PANEL_PAGE, wait_until="load")
        pg.wait_for_timeout(2000)
        st = pg.evaluate(INERT_STATE)
        has_panel = pg.evaluate("() => !!document.getElementById('pnsPanel')")
        pg.evaluate("() => document.getElementById('pnsInput').focus()")
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(120)
        moved = pg.evaluate("() => document.activeElement && "
                            "document.activeElement.id !== 'pnsInput'")
        c.that(not has_panel and st["inertCount"] == 0 and moved, "J13",
               "search.html: no panel, nothing inert, Tab moves freely",
               "panel=%s inert=%d tabMoved=%s"
               % (has_panel, st["inertCount"], moved))

        # --- My Plot season controls --------------------------------------
        pg.goto(base + MYPLOT_PAGE, wait_until="load")
        pg.wait_for_timeout(5000)
        sem = pg.evaluate("""() => {
          const g = document.querySelector('.season-tabs');
          const btns = [...document.querySelectorAll('.season-tab')];
          return {
            role: g ? g.getAttribute('role') : null,
            label: g ? g.getAttribute('aria-label') : null,
            tablists: document.querySelectorAll('[role="tablist"]').length,
            tabs: document.querySelectorAll('[role="tab"]').length,
            tabpanels: document.querySelectorAll('[role="tabpanel"]').length,
            selected: document.querySelectorAll('[aria-selected]').length,
            n: btns.length,
            pressed: btns.map(b => b.getAttribute('aria-pressed')),
            active: btns.map(b => b.classList.contains('is-active'))
          };
        }""")
        c.that(sem["role"] == "group" and sem["label"] == "Season", "J14",
               "season container is a labelled group", str(sem["role"]))
        c.that(sem["tablists"] == 0 and sem["tabs"] == 0
               and sem["tabpanels"] == 0 and sem["selected"] == 0, "J15",
               "no false tab semantics anywhere on My Plot",
               "tablist=%d tab=%d tabpanel=%d aria-selected=%d"
               % (sem["tablists"], sem["tabs"], sem["tabpanels"], sem["selected"]))
        c.that(sem["n"] == 3 and sem["pressed"].count("true") == 1, "J16",
               "exactly one season reports pressed",
               "n=%d pressed=%s" % (sem["n"], sem["pressed"]))
        c.that([p == "true" for p in sem["pressed"]] == sem["active"], "J17",
               "pressed state matches the visual active state",
               "pressed=%s active=%s" % (sem["pressed"], sem["active"]))

        # click each season: pressed must follow, and the sun state must move
        allok, detail = True, []
        for want in ("summer", "winter", "today"):
            pg.evaluate("(s) => document.querySelector('.season-tab[data-season=\"'+s+'\"]').click()", want)
            pg.wait_for_timeout(700)
            got = pg.evaluate("""() => {
              const b = [...document.querySelectorAll('.season-tab')];
              const on = b.filter(x => x.getAttribute('aria-pressed') === 'true');
              return { n: on.length,
                       season: on.length ? on[0].dataset.season : null,
                       active: on.length ? on[0].classList.contains('is-active') : false };
            }""")
            good = got["n"] == 1 and got["season"] == want and got["active"]
            allok = allok and good
            detail.append("%s->%s%s" % (want, got["season"], "" if good else "!"))
        c.that(allok, "J18", "clicking each season moves pressed correctly",
               " ".join(detail))
        ctx.close()
        b.close()
    return report(c)


def report(c):
    print("\nJOB 6 · INTERACTION SEMANTICS — RUNTIME PROOF")
    print("=" * 78)
    for cid, label, good, detail in c.rows:
        print("  %-4s %-5s %-62s" % (cid, "PASS" if good else "FAIL", label[:62]))
        if detail and not good:
            print("        %s" % detail)
    print("\n  %d passed, %d failed" % (len(c.rows) - len(c.failed), len(c.failed)))
    return 1 if c.failed else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--port", type=int, default=9611)
    ap.add_argument("--pages", default=",".join(MODAL_PAGES),
                    help="comma-separated modal pages to test")
    ap.add_argument("--widths", default="1440,390")
    ap.add_argument("--no-tail", action="store_true",
                    help="skip the search.html and My Plot checks")
    a = ap.parse_args()
    root = pathlib.Path(a.root).resolve()
    pages = [x for x in a.pages.split(",") if x]
    widths = [int(x) for x in a.widths.split(",") if x]
    httpd = serve(root, a.port)
    try:
        return run(root, a.port, pages, widths, not a.no_tail)
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    sys.exit(main())
