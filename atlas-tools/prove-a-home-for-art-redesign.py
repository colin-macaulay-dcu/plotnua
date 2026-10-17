#!/usr/bin/env python3
"""Mutation proof for the A Home for Art editorial redesign guards (17 Oct 2026).

Each break below is applied IN MEMORY to the generated page (no file on disk is
touched) and handed to build-a-home-for-art-merge.py's guards(). Every break
must be refused, and the unbroken page must pass. Usage:

    python3 atlas-tools/prove-a-home-for-art-redesign.py
"""
import contextlib
import importlib.util
import io
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("hfa", ROOT / "atlas-tools" / "build-a-home-for-art-merge.py")
hfa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hfa)
PAGE = (ROOT / hfa.MERGED).read_text(encoding="utf-8")
START23, START24 = hfa.START23, hfa.START24


def refused(page):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            hfa.guards(page)
        except SystemExit:
            return buf.getvalue().strip()
    return None


def sub(old, new, count=1, page=None):
    page = PAGE if page is None else page
    if old not in page:
        raise SystemExit("PROOF ERROR: mutation anchor not found: %r" % old[:80])
    return page.replace(old, new, count)


def top():
    i = PAGE.index('<section class="hfa-band is-forest hfa-assess" id="hfa-checks-top"')
    return PAGE[i:PAGE.index("</section>\n", i) + len("</section>\n")]


def settle_band():
    i = PAGE.rindex('<div class="hfa-band is-stone">', 0, PAGE.index('id="before-anything-arrives"'))
    j = PAGE.index("</div>\n", PAGE.index("  </section>\n", PAGE.index('id="before-anything-arrives"')))
    j = PAGE.index("</div>\n", j + 1) + len("</div>\n")
    return PAGE[i:j]


T = top()
host_card = T[T.index('      <div class="hfa-check">'):T.index('      <div class="hfa-check">', T.index('hfa-check">') + 20)]
own_card = T[T.index(host_card) + len(host_card):T.index("    </div>\n    <p class=\"hfa-assess-note\">")]
WALL = '<section class="imagine-photo pa-frame reveal">'
B = settle_band()

BREAKS = [
    ("M3 top band loses its buying card", sub(T, T.replace(own_card, ""))),
    ("M3 top band cards swapped (buying first)", sub(T, T.replace(host_card + own_card, own_card + host_card))),
    ("M3 a third DISC-023 link outside the assessments",
     sub("<h2>%s</h2>" % hfa.OVERLOOKED_H2, '<h2>%s</h2>\n<a href="%s">x</a>' % (hfa.OVERLOOKED_H2, START23))),
    ("M3 the top assessment band removed", sub(T, "")),
    ("M10 top assessments moved below the empty wall",
     sub(WALL, "%s" % WALL, page=sub(T, "")).replace("<div class=\"hfa-nav-wrap\">", T + "<div class=\"hfa-nav-wrap\">", 1)),
    ("M10 the in-page navigation removed", sub(hfa.NAV, "")),
    ("M12 navigation unlabelled", sub('aria-label="On this page"', 'aria-label=""')),
    ("M12 navigation out of order", sub('<li><a href="#live-with-art">', '<li><a href="#discover-and-own">', page=sub(
        '<li><a href="#discover-and-own">', '<li><a href="#live-with-art">'))),
    ("M12 the chooser cards return", sub('<div class="hfa-nav-wrap">', '<ul class="hfa-paths"></ul>\n<div class="hfa-nav-wrap">')),
    ("M12 deep forest used behind Live with art (CSS)", sub("  .hfa-band.is-sage{ background:#EEF2E8; }",
                                                           "  .hfa-band.is-sage{ background:#1F3B2E; }")),
    ("M12 deep forest band reused for Live with art (markup)", sub('<div class="hfa-band is-sage">',
                                                                    '<div class="hfa-band is-forest">')),
    ("M12 terracotta used as a background", sub("  .hfa-num{ display:block;", "  .hfa-num{ background:#BD6A46; display:block;")),
    ("M12 a photograph's alt text edited", sub('alt="The same living room in the evening, a family reading',
                                              'alt="A living room in the evening, a family reading')),
    ("M12 a photograph's dimensions dropped", sub('<img src="assets/img/6442d19ec2dd1df0.jpg" width="1408" height="768" ',
                                                 '<img src="assets/img/6442d19ec2dd1df0.jpg" ')),
    ("M12 two photographs with no heading between", sub('    <h2 id="hfaOpenH">Open your home to art</h2>\n',
                                                      '    <p>Open your home to art</p>\n')),
    ("M12 an extra photograph in the main column", sub(hfa.NAV, hfa.NAV + hfa.O_IMG_PA)),
    ("M12 two stone bands in a row", sub(B, B + '<div class="hfa-band is-stone">\n<div class="article">\n</div>\n</div>\n')),
    ("M12 headline caution (B2_P2) folded away", sub("    <p><strong>%s</strong>" % hfa.B2_P2,
                                                    "    <details><summary>Common questions.</summary><p><strong>%s</strong>" % hfa.B2_P2).replace(
        "%s</p>\n" % hfa.LIVE_NOT_PLOTNUA, "%s</p></details>\n" % hfa.LIVE_NOT_PLOTNUA, 1)),
    ("M12 'not live yet' folded away", sub(
        "      </div>\n    </details>\n    <p class=\"dq-note\">This matching service is not live yet.</p>\n",
        "    <p class=\"dq-note\">This matching service is not live yet.</p>\n      </div>\n    </details>\n")),
    ("M12 a folded caution in an unlabelled expander",
     sub('<summary><h3><span class="hfa-more-k">Before You Buy</span>Four things worth settling in writing.</h3>',
         '<summary><h3></h3>')),
    ("M6 a folded caution deleted", sub("Household policies often cap individual items. ", "")),
    ("M1 untraceable expander label", sub('<span class="hfa-more-k">Commissioning</span>', '<span class="hfa-more-k">Bespoke art</span>')),
]


def main():
    ok = refused(PAGE)
    if ok:
        print("PROOF ERROR: the unbroken page is refused: " + ok)
        sys.exit(1)
    caught = 0
    for name, page in BREAKS:
        if page == PAGE:
            print("  NO-OP   %s" % name)
            continue
        msg = refused(page)
        caught += bool(msg)
        print("  %s  %s%s" % ("CAUGHT" if msg else "MISSED", name, ("  ->  " + msg[9:110]) if msg else ""))
    print("%d/%d breaks caught — %s" % (caught, len(BREAKS), "PROVEN" if caught == len(BREAKS) else "NOT PROVEN"))
    sys.exit(0 if caught == len(BREAKS) else 1)


if __name__ == "__main__":
    main()
