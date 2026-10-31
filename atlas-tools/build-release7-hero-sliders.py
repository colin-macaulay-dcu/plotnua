#!/usr/bin/env python3
"""
PASS 2 · RELEASE 7 · Before / Possible hero slider for The Hidden Cars (founder instruction, 31 Oct 2026; private
preview, not deployed), as Releases 3-6: the shared pn-compare component, hero standard, with the founder's own pair
used whole (atlas-tools/build-disc022-hero-pair.py):

  The Hidden Cars (DISC-022)   PlotNua_Hidden_Cars_BEFORE.png  ->  PlotNua_Underground_Car_Lift_Possible.png

Only the hero changes. The hero copy is carried over byte for byte; the static hero image and its HTML
"Potential Asset" annotation are replaced by the comparison (founder instruction: "Remove the existing Potential
Asset annotation from the hero"). The lift close-up (9aa6c362) stays in the body, unchanged.

START POSITION. It opens on the complete BEFORE (100), as every other Discovery hero (founder directive,
30 Oct 2026; confirmed for this page by the founder, 31 Oct 2026, after the 50 per cent preview).

  python3 atlas-tools/build-release7-hero-sliders.py          build
  python3 atlas-tools/build-release7-hero-sliders.py --check  verify, write nothing
"""
import importlib.util, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("r3", ROOT / "atlas-tools/build-release3-hero-sliders.py")
r3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r3)
CHECK = "--check" in sys.argv
SIZES = r3.SIZES
D = "assets/disc022/img/"
B, P = D + "PlotNua_Hidden_Cars_BEFORE", D + "PlotNua_Underground_Car_Lift_Possible"
START = 100

COMMENT = """  <!-- Pass 2 Release 7 (founder instruction, 31 Oct 2026): the shared Before -> Possible
       component, hero standard, opening on the complete BEFORE. %s -->
"""

PAGES = {
    "discovery-hidden-cars.html": dict(
        cls="hc-hero", name="Hidden Cars", fid="hcHeroCompare", subject="the driveway", focus="50% 50%", wh=(1678, 937),
        aria="Compare the street with the family car parked on the driveway and with the driveway as a car lift, a second car lowered into a lit chamber below. Higher values show more of the driveway before.",
        bef_jpg=B + ".png",
        bef_webp=[(B + "-960.webp", 960), (B + "-1408.webp", 1408), (B + "-1678.webp", 1678)],
        bef_alt="Before: an Irish street of period houses, the family car parked on the paved driveway between clipped hedges, other cars on neighbouring drives and at the kerb.",
        pos_jpg=P + ".png",
        pos_webp=[(P + "-960.webp", 960), (P + "-1408.webp", 1408), (P + "-1678.webp", 1678)],
        pos_alt="The same street as it could be: the driveway is a car-lift platform carrying one car, with a second car parked in a lit chamber beneath it.",
        preload_old=None,
        preload_new='<link rel="preload" as="image" type="image/webp" imagesrcset="%s-960.webp 960w, %s-1408.webp 1408w, %s-1678.webp 1678w" imagesizes="%s" fetchpriority="high">\n' % (B, B, B, SIZES),
        comment=COMMENT % "Same street, one framing: the family car on the\n       driveway, then the driveway as a car lift. The founder's pair, used whole\n       (build-disc022-hero-pair.py)."),
}

EXTRA_CSS = """<style>
/* Release 7 (as Releases 4-6): the page's own hero image rules must not reach the comparison layers. */
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
            if ('class="pn-compare pn-compare--hero"' not in cur or "Pass 2 Release 7" not in cur or EXTRA_CSS not in cur
                    or 'data-start="%d"' % START not in cur or 'class="pa-annot"' in cur.split('<header class="d-hero', 1)[1].split("</header>", 1)[0]):
                bad.append(name)
            continue
        if 'class="pn-compare pn-compare--hero"' in cur:
            print("already built: " + name); continue
        t = r3.build(name, dict(p, ai_label=""), cur)
        w, h = p["wh"]
        for img in (p["bef_jpg"], p["pos_jpg"]):
            old = 'src="%s" width="1408" height="768"' % img
            assert t.count(old) == 1, name + ": " + img
            t = t.replace(old, 'src="%s" width="%d" height="%d"' % (img, w, h), 1)
        t = t.replace("</head>", EXTRA_CSS + "</head>", 1)
        path.write_text(t, encoding="utf-8")
        print("built: " + name)
    if CHECK:
        print("RELEASE 7 HERO SLIDER · " + ("OK" if not bad else "NOT BUILT: %s" % bad)); sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
