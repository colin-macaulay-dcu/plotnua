#!/usr/bin/env python3
"""
DISCOVERY JOURNEY CTA — one prominent journey call-to-action directly below
the hero of every Discovery that has an existing, functioning interactive
homeowner journey (15 Nov 2026).

WHAT IT DOES
  Inserts one <aside class="pn-jcta"> between the hero (or its AI-image note)
  and the rest of the page, and links assets/components/pn-journey-cta.css.
  Both are fenced by markers, so the build is idempotent and reversible.

WHAT IT DOES NOT DO
  * It never adds a button to a Discovery without a functioning journey. The
    table below is the whole list, and every href in it is the SAME journey
    URL the page's own closing section already links to. No new route.
  * It does not touch or remove the existing journey buttons at the bottom
    of each page.
  * It changes no wording, image, link or caution anywhere else on the page.

    python3 atlas-tools/build-discovery-journey-cta.py           # apply
    python3 atlas-tools/build-discovery-journey-cta.py --check   # exit 1 if not applied
    python3 atlas-tools/build-discovery-journey-cta.py --revert  # remove
"""
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSS_HREF = "assets/components/pn-journey-cta.css?v=1"
BEGIN = "<!-- PN-JOURNEY-CTA v1 · BEGIN · built by atlas-tools/build-discovery-journey-cta.py — do not hand-edit -->"
END = "<!-- PN-JOURNEY-CTA v1 · END -->"
CSS_LINE = '<link rel="stylesheet" href="%s"><!-- PN-JOURNEY-CTA v1 css -->' % CSS_HREF

# page -> (kicker, line, [(label, href, primary?)])
# Every href below is copied from the page's own closing journey section.
PAGES = {
    "discovery-living-in-the-garden.html": (
        "Your garden",
        "See what your own garden could take: a garden room, or a garden home.",
        [("Check for a garden room", "your-plot.html?discovery=garden-room", True),
         ("Check for a garden home", "your-plot.html?discovery=residential", True)]),
    "discovery-a-home-for-art.html": (
        "Your home",
        "Two short, private checks. No address or personal details required.",
        [("Explore my space", "disc024-open-your-home-to-art.html?start=1", True),
         ("Explore art for my home", "disc023-buy-original-irish-art.html?start=1", False)]),
    "discovery-driveway-income.html": (
        "Your driveway",
        "Check what your own driveway could support.",
        [("Check your driveway", "disc014-driveway-income.html", True)]),
    "discovery-hidden-bins.html": (
        "Your property",
        "Five short questions about the ground your bins stand on.",
        [("Start the property check", "disc029-hidden-bins-check.html", True)]),
    "discovery-hidden-cars.html": (
        "Your property",
        "Five short questions about the ground your cars stand on.",
        [("Start the check", "disc022-hidden-cars-check.html?start=1", True)]),
    "discovery-home-exchange.html": (
        "Your home",
        "Run the Property Check against your own home and your own year.",
        [("Start the property check", "disc005-home-exchange.html", True)]),
    "discovery-house-as-power-station.html": (
        "Your home",
        "See what your own house could do today, and what it would be asked.",
        [("See what your home could do today", "disc026-power-station.html", True),
         ("What would a house be asked?", "disc026-compute-readiness-check.html", False)]),
    "discovery-neighbourhood-parcel-house.html": (
        "Your home",
        "Check this against your own door. No address required.",
        [("Could my home work?", "disc027-neighbourhood-parcel-house.html", True)]),
    "discovery-the-borrowed-garden.html": (
        "Your garden",
        "Whether you have the ground or want to grow on it, check it in a few questions.",
        [("Check your garden", "disc025-borrowed-garden-check.html?start=1", True),
         ("Check your interest", "disc025-borrowed-garden-grower-check.html?start=1", False)]),
}

HERO_END = re.compile(r'(<header class="d-hero[^"]*"[\s\S]*?</header>)(\s*<p class="pn-hero-note[^"]*">[\s\S]*?</p>)?')


def block(kicker, line, buttons):
    acts = "\n".join(
        '      <a class="pn-jcta-btn%s" href="%s">%s <span aria-hidden="true">&rarr;</span></a>'
        % ("" if primary else " is-alt", html.escape(href, quote=True), html.escape(label))
        for label, href, primary in buttons)
    n = len(buttons)
    return (
        BEGIN + "\n"
        '<link rel="stylesheet" href="%s">\n' % CSS_HREF +
        '<aside class="pn-jcta%s" aria-label="Check your own property">\n'
        '  <div class="pn-jcta-in">\n'
        '    <div class="pn-jcta-copy">\n'
        '      <p class="pn-jcta-k">%s</p>\n'
        '      <p class="pn-jcta-t">%s</p>\n'
        '    </div>\n'
        '    <div class="pn-jcta-acts">\n%s\n    </div>\n'
        '  </div>\n'
        '</aside>\n' % (" pn-jcta--two" if n > 1 else "", html.escape(kicker), html.escape(line), acts)
        + END)


def strip(s):
    s = re.sub(r"\n\n" + re.escape(BEGIN) + r"[\s\S]*?" + re.escape(END), "", s)
    s = s.replace("\n" + CSS_LINE, "").replace(CSS_LINE, "")
    return s


def apply(s, spec):
    s = strip(s)
    m = HERO_END.search(s)
    if not m:
        raise SystemExit("hero not found")
    at = m.end()
    s = s[:at] + "\n\n" + block(*spec) + s[at:]
    return s


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    bad = 0
    for name, spec in PAGES.items():
        p = ROOT / name
        s = p.read_text(encoding="utf-8")
        for _, href, _ in spec[2]:
            target = (ROOT / href.split("?")[0])
            if not target.exists():
                raise SystemExit("journey missing for %s: %s" % (name, href))
        if mode == "--revert":
            p.write_text(strip(s), encoding="utf-8"); continue
        want = apply(s, spec)
        if mode == "--check":
            if want != s:
                print("NOT APPLIED:", name); bad += 1
            continue
        if want != s:
            p.write_text(want, encoding="utf-8")
        print("ok", name)
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
