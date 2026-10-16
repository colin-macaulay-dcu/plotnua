#!/usr/bin/env python3
"""PlotNua · The Borrowed Garden · both journeys, in a real browser (Chromium).

  A  Discovery -> Owner check  (disc025-borrowed-garden-check.html)  -> Register -> Confirmation
  B  Discovery -> Grower check (disc025-borrowed-garden-grower-check.html) -> Register -> Confirmation

Uses the LAUNCH version of the Discovery (built by build-grower-register.py
--preview-discovery into a temporary file; the repo copy is not changed).
Both register endpoints are STUBBED; every non-local request is aborted. No
real personal data: every address is @example.com.

  python3 atlas-tools/prove-grower-register-page.py [--shots DIR] [--axe axe.min.js]
"""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import socketserver
import subprocess
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
GROWER = "disc025-borrowed-garden-grower-check.html"
HOST = "disc025-borrowed-garden-check.html"
DISC_PREVIEW = "_launch-preview-discovery.html"
W = "https://plotnua-garden-register.colin-a41.workers.dev/v1/garden-register/"
CONSENT_G = "I'm over 18, and I'd like PlotNua to keep this and tell me about possible growing space nearby."
ALLOWED = {"first_name", "email", "district", "travel_radius", "space_wanted", "timing", "growing_note",
           "over_18", "consent_text", "source"}
results = []


def check(name, cond, detail=""):
    results.append(bool(cond))
    print(("  [PASS] " if cond else "  [FAIL] ") + name + ("" if cond else f"   {detail}"))


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class Fake:
    def __init__(self):
        self.mode, self.reqs, self.store = "received", [], set()

    def handle(self, route):
        r = route.request
        hdr = {"access-control-allow-origin": "*", "content-type": "application/json",
               "access-control-allow-headers": "content-type"}
        if r.method == "OPTIONS":
            return route.fulfill(status=204, headers=hdr)
        body = json.loads(r.post_data or "{}")
        self.reqs.append((r.url.rsplit("/", 1)[-1], body))
        if self.mode == "fail":
            return route.abort()
        if self.mode == "not_open":
            return route.fulfill(status=503, headers=hdr, body='{"ok":false,"state":"not_open"}')
        if self.mode == "refused":
            return route.fulfill(status=400, headers=hdr, body='{"ok":false,"state":"refused","field":"district"}')
        self.store.add(body.get("email", "").lower())
        return route.fulfill(status=200, headers=hdr, body='{"ok":true,"state":"received"}')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--shots"); ap.add_argument("--axe")
    a = ap.parse_args()
    shots = Path(a.shots) if a.shots else None
    if shots:
        shots.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "atlas-tools/build-grower-register.py", "--preview-discovery", DISC_PREVIEW],
                   cwd=ROOT, check=True, capture_output=True)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}/"
    fake = Fake()
    try:
        with sync_playwright() as p:
            br = p.chromium.launch()

            def page(vp=(1280, 900)):
                ctx = br.new_context(viewport={"width": vp[0], "height": vp[1]}, reduced_motion="reduce")
                pg = ctx.new_page()
                pg.route("**/*", lambda route: fake.handle(route) if route.request.url.startswith(W)
                         else (route.continue_() if route.request.url.startswith(base) else route.abort()))
                return pg

            def reveal_all(pg):
                pg.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('in'))")

            def axe(pg, label, baseline=None, measure=False):
                if not a.axe:
                    return
                pg.wait_for_timeout(1500)   # let reveal fade-ins finish
                pg.add_script_tag(path=a.axe)
                v = pg.evaluate("""async()=>(await axe.run({exclude:[['#bgIntPrev']]},{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}}))
                    .violations.filter(v=>['serious','critical'].includes(v.impact)).flatMap(v=>v.nodes.map(n=>v.id+' '+n.target.join(' ')))""")
                if measure:
                    print(f"        (baseline, pre-existing on the live page: {v})")
                    return v
                if baseline is not None:
                    new = [x for x in v if x not in baseline]
                    check(f"A11Y {label}: no NEW serious/critical axe violations vs the live page", not new, new)
                    return v
                check(f"A11Y {label}: no serious/critical axe violations (WCAG 2.1 AA)", not v, v)
                return v

            # ------------------------------------------------------ Discovery --
            d = page()
            d.goto(base + DISC_PREVIEW + "#discover-your-property")
            reveal_all(d)
            hrefs = d.eval_on_selector_all(".hfa-check a.btn-primary", "e=>e.map(a=>a.getAttribute('href'))")
            heads = d.eval_on_selector_all(".hfa-check h3", "e=>e.map(h=>h.textContent)")
            check("D1 Discovery offers exactly two routes",
                  hrefs == [HOST + "?start=1", GROWER + "?start=1"] and heads ==
                  ["I have garden space to share", "I’m looking for somewhere to grow"], (hrefs, heads))
            if shots:
                d.locator("#discover-your-property").screenshot(path=str(shots / "1-discovery-two-routes.png"))
            live = page(); live.goto(base + "discovery-the-borrowed-garden.html"); reveal_all(live)
            base_v = axe(live, "live Discovery", measure=True) or []
            live.close()
            axe(d, "Discovery (launch version)", baseline=base_v)
            m = page((390, 844)); m.goto(base + DISC_PREVIEW + "#discover-your-property"); reveal_all(m)
            check("D2 Discovery mobile: no horizontal scroll", m.evaluate("document.documentElement.scrollWidth") <= 390)
            if shots:
                m.locator("#discover-your-property").screenshot(path=str(shots / "1m-discovery-mobile.png"))
            m.close()

            # ---------------------------------------- Journey A · owner (host) --
            d.click(f'a[href="{HOST}?start=1"]')
            d.wait_for_selector("#bgQ.is-on")
            check("A1 owner route opens the Property Check at question 1", "Question 1" in d.text_content("#bgProg"))
            for _ in range(8):
                if d.locator("#bgReveal.is-on").count():
                    break
                d.locator("#bgOpts .pc-opt").first.click()
            check("A2 owner check reaches its result", d.locator("#bgReveal.is-on").count() == 1)
            if d.locator("#bgIntOpen").count() and d.locator("#bgIntOpen").is_visible():
                d.click("#bgIntOpen")
                d.fill("#bgIntName", "Testhost"); d.fill("#bgIntEmail", "host.journey@example.com")
                for sel in ["#bgIntDistrict", "#bgIntWater", "#bgIntSize", "#bgIntTiming"]:
                    d.select_option(sel, index=1)
                d.check("#bgIntConsent")
                if d.locator("#bgIntPerm").is_visible():
                    d.check("#bgIntPerm"); d.fill("#bgIntNote", "My landlord knows and has agreed to it.")
                d.click("#bgIntSend")
                d.wait_for_selector("#bgIntDone:not([hidden])")
                route, body = fake.reqs[-1]
                check("A3 owner registers -> 'You're on the register' (garden route, unchanged)",
                      route == "garden" and "on the register" in d.inner_text("#bgIntDoneH").lower(), (route, body))
            else:
                check("A3 owner register panel is shown on the live Property Check", False, "panel not visible")
            d.close()

            # --------------------------------------------- Journey B · grower --
            g = page()
            g.goto(base + DISC_PREVIEW + "#discover-your-property")
            g.click(f'a[href="{GROWER}?start=1"]')
            g.wait_for_selector("#bgQ.is-on")
            check("B1 grower route opens the Grower Check at question 1 of 4", g.text_content("#bgProg") == "Question 1 of 4")
            check("B1b same components as the owner check (dots, stacked options, Back)",
                  g.locator("#bgDots .pc-dot").count() == 4 and g.locator("#bgOpts .pc-opt").count() == 6)
            if shots:
                g.screenshot(path=str(shots / "2-grower-question.png"))
            g.get_by_role("button", name="Killester", exact=True).click(); g.get_by_role("button", name="Up to 2 km", exact=True).click()
            g.click("#bgBack")
            check("B2 Back returns to the previous question", g.text_content("#bgProg") == "Question 2 of 4")
            g.get_by_role("button", name="Up to 2 km", exact=True).click(); g.get_by_role("button", name="Small — a corner", exact=True).click(); g.get_by_role("button", name="Next season", exact=True).click()
            g.wait_for_selector("#bgReveal.is-on")
            txt = g.inner_text("#bgReveal")
            check("B3 result: pilot area, beginners welcome, honest", "first areas" in txt and "beginners are welcome" in txt
                  and "No garden is available through PlotNua today" in txt and "never find a garden" in txt)
            check("B3b the check sent nothing", not [r for r in fake.reqs if r[0] == "grower"])
            # closed in production: the register panel is removed from the DOM
            check("B4 CLOSED: without ?interest=preview the register panel is not in the DOM",
                  g.locator("#bgInterest").count() == 0 and g.locator("input[type=email]").count() == 0)
            g.close()

            g = page()
            g.goto(base + GROWER + "?start=1&interest=preview")
            for t in ["Killester", "Up to 2 km", "Small — a corner", "Next season"]:
                g.get_by_role("button", name=t, exact=True).click()
            g.wait_for_selector("#bgReveal.is-on")
            if shots:
                g.screenshot(path=str(shots / "3-grower-result.png"), full_page=True)
            g.click("#bgIntOpen")
            check("B5 the four kept answers pre-fill the register form",
                  [g.input_value(s) for s in ["#bgIntDistrict", "#bgIntTravel", "#bgIntSize", "#bgIntTiming"]]
                  == ["killester", "up_to_2km", "small", "next_season"])
            check("B5b consent text is the frozen G1B sentence", g.inner_text("#bgIntConsentText") == CONSENT_G)
            axe(g, "Grower Check result + register form")
            g.click("#bgIntSend")
            check("B6 validation names the first missing field; nothing sent", "first name" in g.inner_text("#bgIntMsg")
                  and not [r for r in fake.reqs if r[0] == "grower"])
            g.fill("#bgIntName", "Testgrower"); g.fill("#bgIntEmail", "bad"); g.click("#bgIntSend")
            check("B6b invalid email flagged", "email" in g.inner_text("#bgIntMsg"))
            g.fill("#bgIntEmail", "grower.journey@example.com"); g.click("#bgIntSend")
            check("B6c consent required", "over 18" in g.inner_text("#bgIntMsg"))
            g.check("#bgIntConsent"); g.fill("#bgIntNote", "New to growing; salad and herbs; Saturdays.")
            if shots:
                g.locator("#bgInterest").screenshot(path=str(shots / "4-grower-form.png"))
            g.click("#bgIntSend")
            g.wait_for_selector("#bgIntDone[data-state=received]")
            route, body = fake.reqs[-1]
            check("B7 grower registers -> 'You're on the register'", route == "grower" and
                  g.inner_text("#bgIntDoneH") == "You’re on the register")
            check("B7b payload: only the allowed keys, consent verbatim, source grower_register",
                  set(body) <= ALLOWED and body["consent_text"] == CONSENT_G and body["source"] == "grower_register"
                  and body["over_18"] is True, sorted(body))
            check("B7c focus moves to the confirmation", g.evaluate("document.activeElement.id") == "bgIntDoneH")
            if shots:
                g.locator("#bgInterest").screenshot(path=str(shots / "5-grower-confirmation.png"))
            g.close()

            # duplicate, states, honeypot
            def run(mode, email, honey=False, district="artane"):
                fake.mode = mode
                pg = page(); pg.goto(base + GROWER + "?start=1&interest=preview")
                for t in ["Artane" if district == "artane" else "Elsewhere in Ireland", "Within walking distance",
                          "Not sure yet", "I’m flexible"]:
                    pg.get_by_role("button", name=t, exact=True).click()
                pg.wait_for_selector("#bgReveal.is-on"); pg.click("#bgIntOpen")
                pg.fill("#bgIntName", "Testgrower"); pg.fill("#bgIntEmail", email); pg.check("#bgIntConsent")
                if honey:
                    pg.evaluate("document.getElementById('bgIntWebsite').value='spam'")
                n = len(fake.reqs); pg.click("#bgIntSend"); pg.wait_for_timeout(400)
                return pg, len(fake.reqs) - n
            before = len(fake.store)
            pg, _ = run("received", "GROWER.journey@example.com")
            check("B8 repeat address: same confirmation, stored once", pg.inner_text("#bgIntDoneH") == "You’re on the register"
                  and len(fake.store) == before); pg.close()
            pg, _ = run("not_open", "x1@example.com")
            check("B9 Worker closed -> 'The register isn't open yet', nothing saved",
                  pg.get_attribute("#bgIntDone", "data-state") == "not_open"); pg.close()
            pg, _ = run("refused", "x2@example.com")
            check("B9b refused -> field named, form kept", "your area" in pg.inner_text("#bgIntMsg")); pg.close()
            pg, _ = run("fail", "x3@example.com")
            check("B9c network failure -> truthful 'didn't go through'", pg.get_attribute("#bgIntDone", "data-state") == "unavailable"); pg.close()
            pg, sent = run("received", "x4@example.com", honey=True)
            check("B9d honeypot -> nothing sent", sent == 0); pg.close()
            pg, _ = run("received", "x5@example.com", district="elsewhere")
            check("B9e out-of-area confirmation is honest", "outside those areas" in pg.inner_text("#bgIntDone")); pg.close()
            fake.mode = "received"

            # mobile
            mg = page((390, 844))
            mg.goto(base + GROWER + "?start=1&interest=preview")
            check("M1 grower check mobile: no horizontal scroll", mg.evaluate("document.documentElement.scrollWidth") <= 390)
            small = mg.evaluate("[...document.querySelectorAll('#bgOpts .pc-opt')].map(b=>b.getBoundingClientRect().height).filter(h=>h<44)")
            check("M2 mobile options are at least 44px tall", not small, small)
            if shots:
                mg.screenshot(path=str(shots / "6-grower-question-mobile.png"))
            for t in ["Raheny", "Within walking distance", "Very small — a bed or two", "This season"]:
                mg.get_by_role("button", name=t, exact=True).click()
            mg.click("#bgIntOpen")
            check("M3 mobile form fits: no horizontal scroll", mg.evaluate("document.documentElement.scrollWidth") <= 390)
            if shots:
                mg.screenshot(path=str(shots / "7-grower-form-mobile.png"), full_page=True)
            mg.close()
            br.close()
    finally:
        httpd.shutdown()
        (ROOT / DISC_PREVIEW).unlink(missing_ok=True)
    n = len(results); ok = sum(results)
    print(f"\n  {ok} passed, {n - ok} failed")
    sys.exit(0 if ok == n else 1)


if __name__ == "__main__":
    main()
