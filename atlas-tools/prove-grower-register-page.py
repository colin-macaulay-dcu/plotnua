#!/usr/bin/env python3
"""PlotNua · Grower Register page · browser proof (Playwright, Chromium).

Serves the repo locally and drives borrowed-garden-grower-register.html in a
real browser. The register endpoint is STUBBED: a fake that mimics the
Worker's reply shapes (received / not_open / refused / failure) and keeps an
in-memory set of addresses, so duplicates can be measured. NO request leaves
the machine: every non-local request is aborted. No real personal data is
used; all addresses are @example.com.

  python3 atlas-tools/prove-grower-register-page.py [--shots DIR] [--axe PATH/TO/axe.min.js]
"""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import socketserver
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PAGE = "borrowed-garden-grower-register.html"
ENDPOINT = "https://plotnua-garden-register.colin-a41.workers.dev/v1/garden-register/grower"
CONSENT = "I'm over 18, and I'd like PlotNua to keep this and tell me about possible growing space nearby."
ALLOWED = {"first_name", "email", "district", "travel_radius", "space_wanted", "timing", "growing_note",
           "over_18", "consent_text", "source"}

results = []


def check(name, cond, detail=""):
    results.append((bool(cond), name, detail))
    print(("  [PASS] " if cond else "  [FAIL] ") + name + ("" if cond else f"   {detail}"))


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve():
    handler = functools.partial(Quiet, directory=str(ROOT))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


class FakeRegister:
    """Worker reply shapes, nothing more. mode: received | not_open | refused | fail."""

    def __init__(self):
        self.mode = "received"
        self.requests = []
        self.store = set()

    def handle(self, route):
        req = route.request
        if req.method == "OPTIONS":
            return route.fulfill(status=204, headers={"access-control-allow-origin": "*",
                                                       "access-control-allow-headers": "content-type",
                                                       "access-control-allow-methods": "POST"})
        body = json.loads(req.post_data or "{}")
        self.requests.append(body)
        hdr = {"access-control-allow-origin": "*", "content-type": "application/json"}
        if self.mode == "fail":
            return route.abort()
        if self.mode == "not_open":
            return route.fulfill(status=503, headers=hdr, body='{"ok":false,"state":"not_open"}')
        if self.mode == "refused":
            return route.fulfill(status=400, headers=hdr, body='{"ok":false,"state":"refused","field":"district"}')
        self.store.add(body.get("email", "").lower())
        return route.fulfill(status=200, headers=hdr, body='{"ok":true,"state":"received"}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots")
    ap.add_argument("--axe")
    args = ap.parse_args()
    shots = Path(args.shots) if args.shots else None
    if shots:
        shots.mkdir(parents=True, exist_ok=True)
    httpd, port = serve()
    base = f"http://127.0.0.1:{port}/{PAGE}"
    fake = FakeRegister()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        def new_page(viewport):
            ctx = browser.new_context(viewport=viewport, reduced_motion="reduce")
            page = ctx.new_page()

            def router(route):
                u = route.request.url
                if u.startswith(ENDPOINT):
                    return fake.handle(route)
                if u.startswith(f"http://127.0.0.1:{port}/"):
                    return route.continue_()
                return route.abort()
            page.route("**/*", router)
            return page

        def reveal_all(page):
            page.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('in'))")

        def axe(page, label):
            if not args.axe:
                return
            page.add_script_tag(path=args.axe)
            res = page.evaluate("""async () => (await axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations
                .map(v => ({id:v.id, impact:v.impact, n:v.nodes.length, t:v.nodes.slice(0,2).map(n=>n.target.join(' '))}))""")
            serious = [v for v in res if v["impact"] in ("serious", "critical")]
            check(f"A11Y {label}: no serious or critical axe violations (WCAG 2.1 AA)", not serious, json.dumps(serious))
            minor = [v for v in res if v["impact"] not in ("serious", "critical")]
            if minor:
                print("        (minor axe findings, recorded: " + json.dumps(minor) + ")")

        # ---------------------------------------------------------- P1 closed --
        page = new_page({"width": 1280, "height": 900})
        page.goto(base)
        check("P1 closed: the register form is not in the DOM", page.locator("#grCard").count() == 0)
        check("P1b closed: 'isn't open yet' is shown", page.locator("#grClosed").is_visible())
        check("P1c closed: no email input exists anywhere", page.locator("input[type=email]").count() == 0)
        check("P1d closed: the page is noindex", page.locator('meta[name=robots]').get_attribute("content") == "noindex, nofollow")
        reveal_all(page)
        axe(page, "closed page")
        page.close()

        # ------------------------------------------------- P2–P9 preview desktop --
        page = new_page({"width": 1280, "height": 900})
        page.goto(base + "?register=preview")
        reveal_all(page)
        check("P2 preview: the form is shown with the preview label", page.locator("#grForm").is_visible() and page.locator("#grPrev").is_visible())
        check("P2b consent text rendered is the Worker's frozen sentence", page.locator("#grConsentText").inner_text() == CONSENT)
        if shots:
            page.screenshot(path=str(shots / "desktop-full.png"), full_page=True)
        axe(page, "preview form")

        # P3 empty submit, field by field
        page.click("#grSend")
        check("P3 empty submit: first name is named, nothing sent", "first name" in page.inner_text("#grMsg") and not fake.requests)
        check("P3b the flagged field is marked aria-invalid and focused",
              page.get_attribute("#grName", "aria-invalid") == "true" and page.evaluate("document.activeElement.id") == "grName")
        page.fill("#grName", "Testgrower")
        page.fill("#grEmail", "not-an-email")
        page.click("#grSend")
        check("P4 invalid email is flagged locally", "email" in page.inner_text("#grMsg") and not fake.requests)
        page.fill("#grEmail", "test.grower@example.com")
        page.click("#grSend")
        check("P3c area is required next", "your area" in page.inner_text("#grMsg"))

        # P5 interest check
        page.click("#gcGo")
        check("P5 unanswered check asks for question 1", "question 1" in page.inner_text("#gcMsg"))
        for k, v in [("district", "killester"), ("travel_radius", "up_to_2km"), ("space_band", "small"),
                     ("timing", "next_season"), ("experience", "new"), ("style", "together")]:
            page.check(f"#gc_{k}_{v}")
        page.click("#gcGo")
        txt = page.inner_text("#gcResult")
        check("P5b result shown for a pilot area, beginner, working together",
              "first areas" in txt and "beginners are welcome" in txt and "alongside you" in txt)
        check("P5c result is honest: no garden available, nothing sent",
              "No garden is available through PlotNua today" in txt and "sent anywhere" in txt)
        check("P5d the four kept answers pre-fill the form",
              page.input_value("#grDistrict") == "killester" and page.input_value("#grTravel") == "up_to_2km"
              and page.input_value("#grSpace") == "small" and page.input_value("#grTiming") == "next_season")
        check("P5e the check sent nothing", not fake.requests)
        col = page.evaluate("(()=>{const e=document.getElementById('gcJoin');const c=getComputedStyle(e);return [c.color,c.backgroundColor,c.textDecorationLine]})()")
        check("P5f the 'Join' button text is ivory on green, not underlined", col[0] == "rgb(242, 239, 230)" and col[1] == "rgb(31, 59, 46)" and col[2] == "none", col)
        if shots:
            page.locator("#check").screenshot(path=str(shots / "desktop-check-result.png"))

        # consent still required
        page.click("#grSend")
        check("P3d consent is required last", "over 18" in page.inner_text("#grMsg") and not fake.requests)

        # P6 success
        page.check("#grConsent")
        page.fill("#grNote", "Beginner, would love to grow salad leaves. Saturdays suit me.")
        page.click("#grSend")
        page.wait_for_selector("#grDone[data-state=received]")
        b = fake.requests[-1]
        check("P6 a valid registration reaches 'You're on the Grower Register'",
              "You’re on the Grower Register" in page.inner_text("#grDoneH"))
        check("P6b exactly the allowed keys are sent", set(b) <= ALLOWED and {"first_name", "email", "district",
              "travel_radius", "space_wanted", "timing", "over_18", "consent_text", "source"} <= set(b), sorted(b))
        check("P6c the check-only answers (experience, style) are never sent",
              "experience" not in json.dumps(b) and "together" not in json.dumps(b) and "style" not in b)
        check("P6d consent is sent verbatim with over_18 true and source grower_register",
              b["consent_text"] == CONSENT and b["over_18"] is True and b["source"] == "grower_register")
        check("P6e focus moves to the confirmation heading", page.evaluate("document.activeElement.id") == "grDoneH")
        if shots:
            page.locator("#register").screenshot(path=str(shots / "desktop-received.png"))
        page.close()

        # P7 duplicate
        page = new_page({"width": 1280, "height": 900})
        page.goto(base + "?register=preview")
        before = len(fake.store)
        page.fill("#grName", "Testgrower")
        page.fill("#grEmail", "TEST.grower@example.com")
        for sel, v in [("#grDistrict", "killester"), ("#grTravel", "up_to_2km"), ("#grSpace", "small"), ("#grTiming", "flexible")]:
            page.select_option(sel, v)
        page.check("#grConsent")
        page.click("#grSend")
        page.wait_for_selector("#grDone[data-state=received]")
        check("P7 a repeat submission gets the same confirmation (no 'already registered' oracle)",
              "You’re on the Grower Register" in page.inner_text("#grDoneH") and "already" not in page.inner_text("#grDone").lower())
        check("P7b the repeat address is stored once (case-insensitive key)", len(fake.store) == before)
        page.close()

        # P8 not_open / refused / failure; P9 honeypot
        def filled(mode, honeypot=False, district="artane"):
            fake.mode = mode
            pg = new_page({"width": 1280, "height": 900})
            pg.goto(base + "?register=preview")
            pg.fill("#grName", "Testgrower")
            pg.fill("#grEmail", f"{mode}@example.com")
            for sel, v in [("#grDistrict", district), ("#grTravel", "walking"), ("#grSpace", "very_small"), ("#grTiming", "this_season")]:
                pg.select_option(sel, v)
            pg.check("#grConsent")
            if honeypot:
                pg.evaluate("document.getElementById('grWebsite').value='spam'")
            n0 = len(fake.requests)
            pg.click("#grSend")
            pg.wait_for_timeout(400)
            return pg, len(fake.requests) - n0

        pg, _ = filled("not_open")
        check("P8 not_open reply: 'isn't open yet', details not saved",
              pg.get_attribute("#grDone", "data-state") == "not_open" and "haven’t been saved" in pg.inner_text("#grDone"))
        pg.close()
        pg, _ = filled("refused")
        check("P8b refused reply: the form stays and the field is named", pg.locator("#grForm").is_visible()
              and "your area" in pg.inner_text("#grMsg") and "Nothing has been saved" in pg.inner_text("#grMsg"))
        pg.close()
        pg, _ = filled("fail")
        check("P8c network failure: truthful 'didn't go through'", pg.get_attribute("#grDone", "data-state") == "unavailable")
        pg.close()
        pg, sent = filled("received", honeypot=True)
        check("P9 honeypot filled: nothing sent, truthful not-saved state",
              sent == 0 and pg.get_attribute("#grDone", "data-state") == "unavailable")
        pg.close()
        pg, _ = filled("received", district="elsewhere_in_ireland")
        check("P6f out-of-pilot confirmation says we aren't introducing outside the four areas",
              "outside those areas" in pg.inner_text("#grDone"))
        pg.close()
        fake.mode = "received"

        # ------------------------------------------------------- P10 mobile ----
        page = new_page({"width": 390, "height": 844})
        page.goto(base + "?register=preview")
        reveal_all(page)
        sw = page.evaluate("document.documentElement.scrollWidth")
        check("P10 mobile 390px: no horizontal scroll", sw <= 390, sw)
        small = page.evaluate("""() => [...document.querySelectorAll('main .gr-tick, main .gr-cta, main select, main input[type=text], main input[type=email], main textarea, main .gr-link')]
            
            .filter(e => e.offsetParent && !e.closest('.gr-hp')).map(e => [e.id || e.className, Math.round(e.getBoundingClientRect().height)]).filter(x => x[1] < 44)""")
        check("P10b mobile: every control is at least 44px tall", not small, small)
        fs = page.evaluate("Math.min(...[...document.querySelectorAll('main input, main select, main textarea')].filter(e=>e.offsetParent && !e.closest('.gr-hp') && e.type!=='checkbox' && e.type!=='radio').map(e=>parseFloat(getComputedStyle(e).fontSize)))")
        check("P10c mobile: inputs are 16px or larger (no iOS zoom)", fs >= 16, fs)
        if shots:
            page.screenshot(path=str(shots / "mobile-top.png"))
            page.screenshot(path=str(shots / "mobile-full.png"), full_page=True)
        for k, v in [("district", "elsewhere_in_dublin"), ("travel_radius", "up_to_5km"), ("space_band", "large"),
                     ("timing", "flexible"), ("experience", "lots"), ("style", "own")]:
            page.check(f"#gc_{k}_{v}")
        page.click("#gcGo")
        txt = page.inner_text("#gcResult")
        check("P10d mobile check result for out-of-pilot, experienced, large",
              "welcome to join" in txt and "Experienced growers" in txt and "Larger spaces are rarer" in txt)
        if shots:
            page.locator("#check").screenshot(path=str(shots / "mobile-check-result.png"))
        page.fill("#grName", "Testgrower")
        page.fill("#grEmail", "mobile.test@example.com")
        page.check("#grConsent")
        page.click("#grSend")
        page.wait_for_selector("#grDone[data-state=received]")
        check("P10e mobile registration completes", True)
        if shots:
            page.locator("#register").screenshot(path=str(shots / "mobile-received.png"))
        page.close()

        # ------------------------------------------------ P11 keyboard only ----
        page = new_page({"width": 1280, "height": 900})
        page.goto(base + "?register=preview")
        page.focus("#grName")
        page.keyboard.type("Keyboard")
        page.keyboard.press("Tab"); page.keyboard.type("keys@example.com")
        for _ in range(4):   # each select: Tab to it, ArrowDown picks the first real option
            page.keyboard.press("Tab"); page.keyboard.press("ArrowDown")
        page.focus("#grConsent"); page.keyboard.press("Space")
        page.focus("#grSend"); page.keyboard.press("Enter")
        page.wait_for_timeout(400)
        check("P11 the form can be completed with the keyboard alone",
              page.get_attribute("#grDone", "data-state") == "received", page.inner_text("#grMsg") if page.locator("#grMsg").is_visible() else "")
        page.close()

        browser.close()
    httpd.shutdown()

    passed = sum(1 for r in results if r[0])
    print(f"\n  {passed} passed, {len(results) - passed} failed")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
