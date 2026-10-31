#!/usr/bin/env python3
"""
PASS 2 · RELEASE 5 · Before / Possible hero sliders (founder approval, 31 Oct 2026; "Do not deploy anything")
for two Discoveries, with the Release 3/4 design (pn-compare hero standard, opening at 100% BEFORE via
build-hero-start-before.py). The pairs are the pages' own pictures, aligned by routine pair preparation
(atlas-tools/build-release5-hero-pairs.py):

  Driveway Income (DISC-014)      b5cbac3f empty driveway  ->  4a4a1e4b two cars parked in it
  Your Home on Screen (DISC-021)  ea3f24ee the house       ->  80614bf6 a small shoot at the same house

Only the hero changes; the hero copy is carried over byte for byte. No AI label: neither pair is a declared
record. The Hidden Cars follows when its edited POSSIBLE is returned.

  python3 atlas-tools/build-release5-hero-sliders.py          build
  python3 atlas-tools/build-release5-hero-sliders.py --check  verify, write nothing
"""
import importlib.util, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("r3", ROOT / "atlas-tools/build-release3-hero-sliders.py")
r3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r3)
CHECK = "--check" in sys.argv
SIZES = r3.SIZES

COMMENT = """  <!-- Pass 2 Release 5 (founder approval, 31 Oct 2026): the shared Before -> Possible
       component, hero standard, opening on the complete BEFORE. %s -->
"""

PAGES = {
    "discovery-driveway-income.html": dict(
        cls="di-hero", name="Driveway Income", fid="diHeroCompare", subject="the driveway", focus="84% 50%", wh=(1343, 732),
        aria="Compare the driveway standing empty and with two cars parked in it. Higher values show more of the driveway before.",
        bef_jpg="assets/disc014/img/DISC-014-HERO-BEFORE.jpg",
        bef_webp=[("assets/disc014/img/DISC-014-HERO-BEFORE-960.webp", 960), ("assets/disc014/img/DISC-014-HERO-BEFORE-full.webp", 1343)],
        bef_alt="Before: an Irish semi-detached house on a suburban street, its two-space driveway standing empty while cars line the kerb and one is parked on the grass verge, with offices a short walk away.",
        pos_jpg="assets/disc014/img/DISC-014-HERO-POSSIBLE.jpg",
        pos_webp=[("assets/disc014/img/DISC-014-HERO-POSSIBLE-960.webp", 960), ("assets/disc014/img/DISC-014-HERO-POSSIBLE-full.webp", 1343)],
        pos_alt="The same house as it could be: two cars parked in the two driveway spaces that stood empty, for people who work nearby.",
        preload_old='<link rel="preload" as="image" type="image/webp" imagesrcset="assets/img/b5cbac3fff9072d4-960w.webp 960w, assets/img/b5cbac3fff9072d4.webp 1408w" imagesizes="max(100vw, 161vh)" fetchpriority="high">\n',
        preload_new='<link rel="preload" as="image" type="image/webp" imagesrcset="assets/disc014/img/DISC-014-HERO-POSSIBLE-960.webp 960w, assets/disc014/img/DISC-014-HERO-POSSIBLE-full.webp 1343w" imagesizes="%s" fetchpriority="high">\n' % SIZES,
        comment=COMMENT % "Same house, one framing: the driveway empty, then\n       two cars parked in it. Both layers are pair-prepared copies (build-release5-hero-pairs.py); the sources\n       and their other uses are unchanged."),
    "discovery-your-home-on-screen.html": dict(
        cls="ys-hero", name="Your Home on Screen", fid="ysHeroCompare", subject="the house", focus="60% 50%", wh=(1385, 755),
        aria="Compare the house as it is and during a small film shoot. Higher values show more of the house before.",
        bef_jpg="assets/disc021/img/DISC-021-HERO-BEFORE.jpg",
        bef_webp=[("assets/disc021/img/DISC-021-HERO-BEFORE-960.webp", 960), ("assets/disc021/img/DISC-021-HERO-BEFORE-full.webp", 1385)],
        bef_alt="Before: an ordinary Irish semi-detached house seen from the road, pebbledash above and red brick below, three wheelie bins at the hedge and a car on a concrete-strip driveway.",
        pos_jpg="assets/disc021/img/DISC-021-HERO-POSSIBLE.jpg",
        pos_webp=[("assets/disc021/img/DISC-021-HERO-POSSIBLE-960.webp", 960), ("assets/disc021/img/DISC-021-HERO-POSSIBLE-full.webp", 1385)],
        pos_alt="The same house as it could be, during a small shoot: a lamp on a stand aimed at the front window, a camera on the driveway, taped cable runs, flight cases and a handful of crew.",
        preload_old=None,
        preload_new='<link rel="preload" as="image" type="image/webp" imagesrcset="assets/disc021/img/DISC-021-HERO-POSSIBLE-960.webp 960w, assets/disc021/img/DISC-021-HERO-POSSIBLE-full.webp 1385w" imagesizes="%s" fetchpriority="high">\n' % SIZES,
        comment=COMMENT % "Same house, one framing: as it is, then a small\n       shoot. Both layers are pair-prepared copies (build-release5-hero-pairs.py); the sources and their other\n       uses are unchanged."),
}

EXTRA_CSS = """<style>
/* Release 5 (as Release 4): the pages' own hero image rules (an id-level object-position, a fade-in scale) must not
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
            if 'class="pn-compare pn-compare--hero"' not in cur or "Pass 2 Release 5" not in cur or EXTRA_CSS not in cur:
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
        print("RELEASE 5 HERO SLIDERS · " + ("OK" if not bad else "NOT BUILT: %s" % bad)); sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
