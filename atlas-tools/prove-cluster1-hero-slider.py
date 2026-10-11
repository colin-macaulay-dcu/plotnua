#!/usr/bin/env python3
"""
PROVE CLUSTER 1 · HERO BEFORE/AFTER SLIDER
==========================================
A real-browser regression test for the #gardenCompare hero control, written
after the founder reported on 11 October 2026 that the handle did not appear
draggable.

The audit found the control already fully implemented: pointer drag, touch
drag, keyboard, ARIA and clamping all worked. Nothing was rebuilt. This file
exists so that finding is a measurement with a date on it rather than a
recollection, and so a future change that silently breaks the interaction
fails loudly.

Twelve assertions, each reaching a distinct property. A missing element is a
FAILURE, never a skip, so no assertion can pass vacuously.

    python3 atlas-tools/prove-cluster1-hero-slider.py [--page PATH]

Requires Playwright with Chromium. Exit 0 = all pass.
"""
import argparse
import pathlib
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("REFUSE: Playwright is not installed. This is an instrument "
             "failure, not a page failure: do not record it as a pass.")

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_PAGE = HERE.parent / "discovery-living-in-the-garden.html"

READ = """() => {
  const el = document.getElementById('gardenCompare');
  if (!el) return null;
  const r = el.querySelector('.cmp-range');
  const d = el.querySelector('.cmp-divider');
  const h = el.querySelector('.cmp-handle');
  const over = el.querySelector('.cmp-over');
  const box = el.getBoundingClientRect();
  const hb = h ? h.getBoundingClientRect() : null;
  const db = d ? d.getBoundingClientRect() : null;
  return {
    live: el.classList.contains('is-live'),
    pos: parseFloat(getComputedStyle(el).getPropertyValue('--pos')),
    value: r ? Number(r.value) : null,
    min: r ? r.min : null, max: r ? r.max : null,
    label: r ? r.getAttribute('aria-label') : null,
    valuetext: r ? r.getAttribute('aria-valuetext') : null,
    tabIndex: r ? r.tabIndex : null,
    disabled: r ? r.disabled : null,
    rendered: r ? !!r.offsetParent : null,
    clip: over ? getComputedStyle(over).clipPath : null,
    tagA: (el.querySelector('.cmp-tag-a') || {}).textContent,
    tagB: (el.querySelector('.cmp-tag-b') || {}).textContent,
    handle: hb and null,
    handleW: hb ? Math.round(hb.width) : null,
    handleH: hb ? Math.round(hb.height) : null,
    handleCx: hb ? Math.round(hb.x + hb.width / 2) : null,
    dividerCx: db ? Math.round(db.x + db.width / 2) : null,
    box: {x: box.x, y: box.y, w: box.width, h: box.height},
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  };
}"""
# `hb and null` is Python-ism; strip it out of the JS we actually send.
READ = READ.replace("    handle: hb and null,\n", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default=str(DEFAULT_PAGE))
    args = ap.parse_args()
    url = pathlib.Path(args.page).resolve().as_uri()

    results = []

    def check(cid, desc, condition, detail=""):
        results.append((cid, bool(condition), desc, detail))

    with sync_playwright() as pw:
        b = pw.chromium.launch()

        # ---- desktop: pointer, keyboard, clamping -------------------------
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        p = ctx.new_page()
        errors = []
        p.on("pageerror", lambda e: errors.append(str(e)[:120]))
        p.goto(url, wait_until="load")
        p.wait_for_timeout(300)

        s = p.evaluate(READ)
        if s is None:
            print("FAIL  H0  #gardenCompare is not on the page — guard could not run")
            sys.exit(1)
        check("H1", "script upgrades the component to is-live", s["live"])
        check("H2", "a real range input backs it, 0-100, enabled and focusable",
              s["min"] == "0" and s["max"] == "100" and s["disabled"] is False
              and s["tabIndex"] == 0 and s["rendered"],
              f"min={s['min']} max={s['max']} tabIndex={s['tabIndex']}")
        check("H3", "an aria-label describes the comparison",
              bool(s["label"]) and "today" in (s["label"] or "").lower())
        check("H4", "TODAY / POSSIBLE labels are present",
              (s["tagA"] or "").strip().lower() == "today"
              and (s["tagB"] or "").strip().lower() == "possible",
              f"{s['tagA']!r} / {s['tagB']!r}")
        check("H5", "the 44px handle sits on the divider",
              s["handleW"] == 44 and s["handleH"] == 44
              and abs(s["handleCx"] - s["dividerCx"]) <= 1,
              f"{s['handleW']}x{s['handleH']} at {s['handleCx']} vs divider {s['dividerCx']}")

        box = s["box"]
        cy = box["y"] + box["h"] / 2

        def drag(frac_from, to_x):
            p.mouse.move(box["x"] + box["w"] * frac_from, cy)
            p.mouse.down()
            p.mouse.move(to_x, cy, steps=10)
            p.mouse.up()
            p.wait_for_timeout(80)
            return p.evaluate(READ)

        a = drag(0.65, box["x"] + box["w"] * 0.25)
        check("H6", "a mouse drag moves the divider", abs(a["pos"] - 25) <= 1 and a["value"] == 25,
              f"--pos={a['pos']} value={a['value']}")
        check("H7", "the overlay clip tracks the divider",
              "75%" in (a["clip"] or ""), a["clip"])

        lo = drag(0.5, box["x"] - 600)
        hi = drag(0.5, box["x"] + box["w"] + 900)
        check("H8", "the drag is clamped to the image bounds",
              lo["pos"] == 0 and hi["pos"] == 100, f"low={lo['pos']} high={hi['pos']}")

        p.evaluate("() => document.querySelector('.cmp-range').focus()")
        focused = p.evaluate("() => (document.activeElement.className || '')")
        before_k = p.evaluate(READ)["value"]
        for _ in range(5):
            p.keyboard.press("ArrowLeft")
        p.wait_for_timeout(60)
        k = p.evaluate(READ)
        check("H9", "the control is keyboard operable",
              "cmp-range" in focused and k["value"] == before_k - 5,
              f"focus={focused!r} {before_k} -> {k['value']}")

        p.keyboard.press("Home")
        p.wait_for_timeout(50)
        home = p.evaluate(READ)
        p.keyboard.press("End")
        p.wait_for_timeout(50)
        end = p.evaluate(READ)
        check("H10", "aria-valuetext is live and meaningful at both ends",
              home["valuetext"] != end["valuetext"]
              and "detached home" in (home["valuetext"] or "")
              and "as it is today" in (end["valuetext"] or ""),
              f"{home['valuetext']!r} / {end['valuetext']!r}")

        check("H11", "no page errors and no horizontal page overflow",
              not errors and end["overflow"] <= 0,
              f"errors={errors} overflow={end['overflow']}px")
        ctx.close()

        # ---- touch --------------------------------------------------------
        ctx = b.new_context(viewport={"width": 390, "height": 844},
                            has_touch=True, is_mobile=True)
        p = ctx.new_page()
        p.goto(url, wait_until="load")
        p.wait_for_timeout(300)
        t0 = p.evaluate(READ)
        tb = t0["box"]
        p.evaluate(
            """([x0, x1, y]) => {
                 const el = document.getElementById('gardenCompare');
                 const fire = (type, x) => el.dispatchEvent(new PointerEvent(type, {
                   pointerId: 1, pointerType: 'touch', isPrimary: true,
                   clientX: x, clientY: y, bubbles: true, cancelable: true, button: 0 }));
                 fire('pointerdown', x0); fire('pointermove', (x0 + x1) / 2);
                 fire('pointermove', x1); fire('pointerup', x1);
               }""",
            [tb["x"] + tb["w"] * 0.8, tb["x"] + tb["w"] * 0.2, tb["y"] + tb["h"] / 2])
        p.wait_for_timeout(100)
        t1 = p.evaluate(READ)
        check("H12", "a touch drag moves the divider at 390px",
              abs(t1["pos"] - 20) <= 2 and t1["overflow"] <= 0,
              f"--pos={t1['pos']} overflow={t1['overflow']}px")
        ctx.close()
        b.close()

    print("\nCLUSTER 1 HERO SLIDER · REGRESSION\n")
    failed = 0
    for cid, okk, desc, detail in results:
        print(f"  {'PASS' if okk else 'FAIL'}  {cid:<4} {desc}" + (f"  [{detail}]" if detail else ""))
        failed += 0 if okk else 1
    print(f"\n{len(results)} checks, {len(results) - failed} passed, {failed} failed\n")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
