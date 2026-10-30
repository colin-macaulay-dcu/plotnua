#!/usr/bin/env python3
"""
PASS 2 · RELEASE 4 · Before / Possible hero sliders (founder development approval, 30 Oct 2026:
"DO NOT DEPLOY TO PRODUCTION") for three Discoveries, with the Release 3 design (pn-compare hero
standard, opening at 100% BEFORE via build-hero-start-before.py):

  DISC-025 The Borrowed Garden        DISC-025-HERO-BEFORE (59d566ff, own annotation removed;
                                      build-disc025-hero-before.py)  ->  faeb58a1 (raised beds)
  Garden Retreat (DISC-001)           45a270b7 (lawn, one small sauna cabin)  ->  7d5f5718 (full retreat)
  The Neighbourhood Parcel House      8b20a096 (the house and porch)  ->  e0d57804 (a neighbour collecting)

All three pairs are the pages' own approved pictures, measured as one framing (SIFT median 0.25-0.63 px).
Only the hero changes: the hero copy (eyebrow, H1, subtitle, intro, Garden Retreat's two links) is
carried over byte for byte. The Borrowed Garden's registers, checks and publication state are untouched;
Garden Retreat's supplier gallery and Maker Explorer are untouched. No AI label is added: none of these
pictures is a declared record (see the Release 4 report).

  python3 atlas-tools/build-release4-hero-sliders.py          build
  python3 atlas-tools/build-release4-hero-sliders.py --check  verify, write nothing
"""
import importlib.util, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("r3", ROOT / "atlas-tools/build-release3-hero-sliders.py")
r3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r3)
CHECK = "--check" in sys.argv
SIZES = r3.SIZES

COMMENT = """  <!-- Pass 2 Release 4 (founder development approval, 30 Oct 2026): the shared Before -> Possible
       component, hero standard, opening on the complete BEFORE. %s -->
"""

PAGES = {
    "discovery-the-borrowed-garden.html": dict(
        cls="bg-hero", name="The Borrowed Garden", fid="bgHeroCompare", subject="the garden", focus="45% 50%",
        aria="Compare the garden with its open lawn and with raised growing beds on part of it. Higher values show more of the garden before.",
        bef_jpg="assets/disc025/img/DISC-025-HERO-BEFORE.jpg",
        bef_webp=[("assets/disc025/img/DISC-025-HERO-BEFORE-960.webp", 960), ("assets/disc025/img/DISC-025-HERO-BEFORE-1408.webp", 1408)],
        bef_alt="Before: an Irish back garden with a wide striped lawn, one raised bed and a timber store by the wall, and a woman reading on the patio by the house.",
        pos_jpg="assets/img/faeb58a1d6a8ed1a.jpg",
        pos_webp=[("assets/img/faeb58a1d6a8ed1a-960w.webp", 960), ("assets/img/faeb58a1d6a8ed1a.webp", 1408)],
        pos_alt="The same garden as it could be: raised timber beds, gravel paths, herbs and vegetables on one side of the lawn, with the rest of the lawn and the patio unchanged.",
        preload_old=None,
        preload_new='<link rel="preload" as="image" type="image/webp" imagesrcset="assets/img/faeb58a1d6a8ed1a-960w.webp 960w, assets/img/faeb58a1d6a8ed1a.webp 1408w" imagesizes="%s" fetchpriority="high">\n' % SIZES,
        comment=COMMENT % "Same garden, one framing: the open lawn, then\n       growing beds on part of it. The BEFORE is a copy of 59d566ff with PlotNua's own burned-in annotation\n       removed (atlas-tools/build-disc025-hero-before.py); the source and its later use on this page are unchanged."),
    "discovery-garden-retreat.html": dict(
        cls="gr-hero", name="Garden Retreat", fid="grHeroCompare", subject="the garden", focus="62% 50%",
        aria="Compare the garden with a single sauna cabin and with the full retreat. Higher values show more of the garden before.",
        bef_jpg="assets/img/45a270b7716e4a94.jpg",
        bef_webp=[("assets/img/45a270b7716e4a94-960w.webp", 960), ("assets/img/45a270b7716e4a94.webp", 1408)],
        bef_alt="Before: an established Irish suburban garden with the lawn left clear and a single small timber sauna cabin in the far corner.",
        pos_jpg="assets/img/7d5f5718cf9cd3da.jpg",
        pos_webp=[("assets/img/7d5f5718cf9cd3da-960w.webp", 960), ("assets/img/7d5f5718cf9cd3da.webp", 1408)],
        pos_alt="The same garden as it could be: a timber garden room, a barrel sauna, a hot tub and a plunge pool set among decking and planting.",
        preload_old='<link rel="preload" as="image" type="image/webp" imagesrcset="assets/img/7d5f5718cf9cd3da-960w.webp 960w, assets/img/7d5f5718cf9cd3da.webp 1408w" imagesizes="max(100vw, 161vh)" fetchpriority="high">\n',
        preload_new='<link rel="preload" as="image" type="image/webp" imagesrcset="assets/img/7d5f5718cf9cd3da-960w.webp 960w, assets/img/7d5f5718cf9cd3da.webp 1408w" imagesizes="%s" fetchpriority="high">\n' % SIZES,
        comment=COMMENT % "Same garden, one framing: one modest step, then\n       the full retreat (the page's two existing pictures)."),
    "discovery-neighbourhood-parcel-house.html": dict(
        cls="ph-hero", name="The Neighbourhood Parcel House", fid="phHeroCompare", subject="the house", focus="40% 50%",
        aria="Compare the house as it is and with its porch used as a neighbourhood parcel point. Higher values show more of the house before.",
        bef_jpg="assets/img/8b20a0968b1fc5a1.jpg",
        bef_webp=[("assets/img/8b20a0968b1fc5a1-960w.webp", 960), ("assets/img/8b20a0968b1fc5a1.webp", 1408)],
        bef_alt="Before: an Irish house on a summer afternoon with a timber porch over a closed front door and a car in the gravel driveway.",
        pos_jpg="assets/img/e0d578046cd29bda.jpg",
        pos_webp=[("assets/img/e0d578046cd29bda-960w.webp", 960), ("assets/img/e0d578046cd29bda.webp", 1408)],
        pos_alt="The same house as it could be: the front door open under the porch and a neighbour collecting a parcel from the householder.",
        preload_old=None,
        preload_new='<link rel="preload" as="image" type="image/webp" imagesrcset="assets/img/e0d578046cd29bda-960w.webp 960w, assets/img/e0d578046cd29bda.webp 1408w" imagesizes="%s" fetchpriority="high">\n' % SIZES,
        comment=COMMENT % "Same house, one framing: the porch as it is, then\n       a neighbour collecting a parcel. The annotated Potential Asset plate (b52ce590) is no longer the hero."),
}

EXTRA_CSS = """<style>
/* Release 4: the pages' own hero image rules (an id-level object-position, a fade-in scale) must not
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
            if 'class="pn-compare pn-compare--hero"' not in cur or "Pass 2 Release 4" not in cur or EXTRA_CSS not in cur:
                bad.append(name)
            continue
        if 'class="pn-compare pn-compare--hero"' in cur:
            print("already built: " + name); continue
        t = r3.build(name, dict(p, ai_label=""), cur)
        t = t.replace("</head>", EXTRA_CSS + "</head>", 1)
        path.write_text(t, encoding="utf-8")
        print("built: " + name)
    if CHECK:
        print("RELEASE 4 HERO SLIDERS · " + ("OK" if not bad else "NOT BUILT: %s" % bad)); sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
