#!/usr/bin/env python3
"""
PASS 2 · RELEASE 6 · Before / Possible hero slider for A Home for Art (founder approval, 31 Oct 2026; private
preview, not deployed), as Release 5, with the Release 3/4 design (pn-compare hero standard, opening at 100% BEFORE via
build-hero-start-before.py). The pairs are the pages' own pictures, aligned by routine pair preparation
(atlas-tools/build-disc023-hero-pair.py):

  A Home for Art (DISC-023)       5dc201be empty wall (own label removed)  ->  c0f5bfcd the same room with a painting

Only the hero changes; the hero copy is carried over byte for byte. The approved AI disclosure goes beneath the hero
(build-ai-disclosure-below.py). The existing hosting hero picture (dfb125ba) moves into the hosting section.

  python3 atlas-tools/build-release6-hero-sliders.py          build
  python3 atlas-tools/build-release6-hero-sliders.py --check  verify, write nothing
"""
import importlib.util, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("r3", ROOT / "atlas-tools/build-release3-hero-sliders.py")
r3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r3)
CHECK = "--check" in sys.argv
SIZES = r3.SIZES

COMMENT = """  <!-- Pass 2 Release 6 (founder approval, 31 Oct 2026): the shared Before -> Possible
       component, hero standard, opening on the complete BEFORE. %s -->
"""

PAGES = {
    "discovery-a-home-for-art.html": dict(
        cls="hfa-hero", name="A Home for Art", fid="hfaHeroCompare", subject="the room", focus="55% 50%", wh=(1408, 768),
        aria="Compare the living room with its wall empty and with an original landscape painting above the fireplace. Higher values show more of the room before.",
        bef_jpg="assets/disc023/img/DISC-023-HERO-BEFORE.jpg",
        bef_webp=[("assets/disc023/img/DISC-023-HERO-BEFORE-960.webp", 960), ("assets/disc023/img/DISC-023-HERO-BEFORE-1408.webp", 1408)],
        bef_alt="Before: a bright Irish living room with a sea view, a sofa, an armchair and a fireplace beneath a large empty plaster wall.",
        pos_jpg="assets/disc023/img/A-Home-for-Art-02-Possible-MASTER.jpeg",
        pos_webp=[("assets/disc023/img/DISC-023-HERO-POSSIBLE-960.webp", 960), ("assets/disc023/img/DISC-023-HERO-POSSIBLE-1408.webp", 1408)],
        pos_alt="The same room as it could be: an original landscape painting of the coast hung on the wall above the fireplace.",
        preload_old=None,
        preload_new='<link rel="preload" as="image" type="image/webp" imagesrcset="assets/disc023/img/DISC-023-HERO-POSSIBLE-960.webp 960w, assets/disc023/img/DISC-023-HERO-POSSIBLE-1408.webp 1408w" imagesizes="%s" fetchpriority="high">\n' % SIZES,
        comment=COMMENT % "Same room, one framing: an empty wall, then an\n       original painting. BEFORE: the credentialed master with PlotNua's own label removed; POSSIBLE: the\n       credentialed master (build-disc023-hero-pair.py)."),
}

EXTRA_CSS = """<style>
/* Release 6 (as Release 4): the pages' own hero image rules (an id-level object-position, a fade-in scale) must not
   reach the comparison layers, so both layers keep one framing. */
body.pn-id.pn-pd .d-hero.pn-hero-compare .pn-compare__stage img,
body.pn-id.pn-pd .d-hero.pn-hero-compare .pn-compare__stage #dHeroImg{ object-position:var(--pnc-focus,50% 50%); }
</style>
"""


def main():
    bad = []
    for name, p in PAGES.items():
        path = ROOT / name
        cur = path.read_text(encoding="utf-8")
        if CHECK:
            if 'class="pn-compare pn-compare--hero"' not in cur or "Pass 2 Release 6" not in cur or EXTRA_CSS not in cur:
                bad.append(name)
            continue
        if 'class="pn-compare pn-compare--hero"' in cur:
            print("already built: " + name); continue
        t = r3.build(name, dict(p, ai_label=""), cur)
        w, h = p["wh"]
        for jpg in (p["bef_jpg"], p["pos_jpg"]):
            old = 'src="%s" width="1408" height="768"' % jpg
            assert t.count(old) == 1, name + ": " + jpg
            t = t.replace(old, 'src="%s" width="%d" height="%d"' % (jpg, w, h), 1)
        t = t.replace("</head>", EXTRA_CSS + "</head>", 1)
        path.write_text(t, encoding="utf-8")
        print("built: " + name)
    if CHECK:
        print("RELEASE 6 HERO SLIDERS · " + ("OK" if not bad else "NOT BUILT: %s" % bad)); sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
