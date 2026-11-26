#!/usr/bin/env python3
"""PROOF · the three-gallery rules of the PlotArt launch guard can fail (Phase A, 24 Nov 2026). Read-only on the repository.

    python3 atlas-tools/prove-plotart-three-galleries.py

Copies the published PlotArt pages to a scratch site, confirms prove-plotart-launch.py passes on the untouched copy, then
breaks one thing at a time and requires the guard to refuse with the rule that is meant to catch it. Also checks that the
Galleries menu patch (plotart-galleries-nav.py) and the gallery builder (build-plotart-galleries.py) have nothing left to do.
A guard that cannot fail proves nothing."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SW = os.path.join(ROOT, "atlas-tools", "release", "plotart-launch-switches.json")
MAN = os.path.join(ROOT, "atlas-tools", "release", "plotart-launch-manifest.json")
results = []


def guard(site, switches=SW, entrances=None):
    p = subprocess.run([sys.executable, os.path.join(ROOT, "atlas-tools", "prove-plotart-launch.py"), site, "--switches", switches, "--manifest", MAN]
                       + (["--entrances", entrances] if entrances else []),
                       capture_output=True, text=True, cwd=ROOT)
    return p.stdout + p.stderr


def copy_site(tmp, n):
    site = os.path.join(tmp, "s%d" % n)
    shutil.copytree(os.path.join(ROOT, "plotart"), os.path.join(site, "plotart"))
    for f in ("sitemap.xml", "image-provenance-records.json"):   # L11 reads the sitemap, L14 the provenance records
        shutil.copy(os.path.join(ROOT, f), os.path.join(site, f))
    return site


def edit(site, rel, old, new):
    p = os.path.join(site, "plotart", rel)
    s = open(p, encoding="utf-8").read()
    if old not in s:
        raise SystemExit("PROOF SETUP: %r not found in %s" % (old[:60], rel))
    open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))


def check(name, ok, detail=""):
    results.append((name, ok, detail))


FAULTS = [
    ("F1 an image on the Spaces entrance", "index.html", 'data-pa-placeholder="spaces"', 'data-pa-placeholder="spaces"><img src="assets/hero/founder-01-abstract.webp" alt="x"', "L21 the spaces entrance shows an image but no authorised entrance artwork"),
    ("F2 'Gallery open' on the Being entrance", "index.html", '<p class="pa-gx-status">In preparation</p><h2>Being.</h2>', '<p class="pa-gx-status">Gallery open</p><h2>Being.</h2>', "L21 the being entrance"),
    ("F3 an Artists in Focus section on a holding page", "spaces/index.html", '<p class="pa-gh-status">In preparation</p>', '<p class="pa-gh-status">In preparation</p><h2>Artists in Focus</h2>', "L21 spaces/index.html must be a holding page"),
    ("F4 an artist's artwork on a holding page", "being/index.html", '<figure class="pa-gh-art">', '<figure class="pa-gh-art"><img src="../artists/carolyn-walsh/img/coastal-series-8-1-600.webp" alt="x">', "L21 being/index.html must be a holding page"),
    ("F5 a holding page made indexable", "spaces/index.html", '<meta name="robots" content="noindex, follow">', '<meta name="robots" content="index, follow">', "L21 spaces/index.html must be noindex"),
    ("F6 entrance artwork cropped", "assets/plotart-galleries.css", "object-fit:contain", "object-fit:cover", "L21 gallery entrance artwork must be shown whole"),
    ("F7 the gallery tabs removed from Contemporary", "gallery/index.html", '<nav class="pa-gtabs"', '<nav class="pa-gtabs-gone"', "L21 gallery/index.html must carry the gallery tabs"),
    ("F8 the Contemporary heading reverted", "gallery/index.html", 'id="vgH">Contemporary.</h1>', 'id="vgH">Contemporary Art.</h1>', "L21 gallery/index.html must open with the shared heading block"),
    ("F9 an extra label under the homepage heading", "index.html", "A new home for Irish art.</h1>", "A new home for Irish art.</h1><p>Three curated galleries</p>", "L6 the homepage heading must be exactly"),
    ("F10 'Real art. Real homes.' restored", "index.html", "<h3>Living Gallery</h3>", "<h3>Real art. Real homes.</h3>", "L21 the homepage must present the Living Gallery"),
    ("F11 Art for Hire enquiries wording removed", "index.html", " Hire enquiries are not yet open.</p>", "</p>", "L21 the homepage must say Art for Hire enquiries are not yet open"),
    ("F12 an Artists' Gallery pill back on an artwork page", "artists/carolyn-walsh/coastal-series-8.html", 'data-pa-track="nav_mobile_gallery">Mobile Gallery</a>',
     'data-pa-track="nav_mobile_gallery">Mobile Gallery</a><a class="pa-pill" href="../../gallery/" data-pa-track="nav_virtual_gallery">Artists’ Gallery</a>', "L21 artists/carolyn-walsh/coastal-series-8.html must carry exactly one Galleries menu"),
    ("F13 a holding page implying an opening date", "being/index.html", "This gallery is being prepared.", "This gallery is opening soon.", "L9"),
    ("F16 an artist link on the Being entrance", "index.html", '<p class="pa-gx-text">Life, identity', '<a href="artists/carolyn-walsh/">x</a><p class="pa-gx-text">Life, identity', "L21 the being entrance must say In preparation, link only to its holding page and never to an artist"),
    ("F17 the Contemporary search title reverted", "gallery/index.html", "<title>Contemporary Irish Art Gallery | PlotArt</title>", "<title>Irish Artists &amp; Original Art | Artists’ Gallery | PlotArt</title>", "L11 the Contemporary Art gallery's search title"),
    # final curatorial identity (25 Nov 2026): names, editorial full stops, taglines, introductions, plain navigation and redirects
    ("F21 a former name (Landscape Art) back in a footer", "about.html", '>Spaces</a></li>', '>Landscape Art</a></li>', "L21 about.html still uses a former gallery name"),
    ("F22 a link to a former address (portraiture/)", "for-artists.html", 'href="being/" data-pa-track="nav_gallery_being">', 'href="portraiture/" data-pa-track="nav_gallery_being">', "L21 for-artists.html still uses a former gallery name"),
    ("F23 the approved Spaces introduction shortened", "spaces/index.html", " interiors and imagined places.</p></div>", ".</p></div>", "L21 spaces/index.html must open with the shared heading block"),
    ("F24 a redirect made indexable", "portraiture/index.html", '<meta name="robots" content="noindex, follow">', '<meta name="robots" content="index, follow">', "L21 portraiture/index.html must be exactly the generated permanent redirect"),
    ("F25 a redirect chain (landscape/ → places-and-spaces/)", "landscape/index.html", 'location.replace("../spaces/"', 'location.replace("../places-and-spaces/"', "L21 landscape/index.html must be exactly the generated permanent redirect"),
    ("F27 a full stop in the navigation", "index.html", 'data-pa-track="nav_gallery_being">Being<', 'data-pa-track="nav_gallery_being">Being.<', "L21 the navigation must name the galleries Contemporary, Spaces and Being, without full stops"),
    ("F28 the editorial full stop dropped from an entrance", "index.html", "<h2>Spaces.</h2>", "<h2>Spaces</h2>", "L21 the spaces entrance must read 'Spaces.'"),
    ("F29 a Being introduction changed", "index.html", "Life, identity, emotion and existence.", "Portraits and the human subject.", "L21 the being entrance must read 'Being.'"),
    ("F30 the Places & Spaces redirect pointed elsewhere", "places-and-spaces/index.html", 'location.replace("../spaces/"', 'location.replace("../gallery/"', "L21 places-and-spaces/index.html must be exactly the generated permanent redirect"),
    # final curatorial identity (25 Nov 2026): the founder's exact wording, the shared heading block, Environment retired
    ("F31 the Spaces tagline altered on its page", "spaces/index.html", '<p class="pa-gt-tag">The spaces we inhabit, encounter and imagine.</p>', '<p class="pa-gt-tag">The places we live in.</p>', "L21 spaces/index.html must open with the shared heading block"),
    # Contemporary has no introduction since 26 Nov 2026 (Report 35): reinstating one must be caught
    ("F32 an introduction reinstated on Contemporary", "gallery/index.html", '<p class="pa-gt-tag">Abstraction, expression and experimentation.</p>',
     '<p class="pa-gt-tag">Abstraction, expression and experimentation.</p>\n  <p class="pa-gt-intro">Exploring artistic expression.</p>', "L21 gallery/index.html must open with the shared heading block"),
    ("F33 the Being heading style overridden for one page", "being/index.html", '<div class="pa-gt"><h1 class="pa-gt-h"', '<div class="pa-gt-x"><h1 class="pa-gt-h"', "L21 being/index.html must open with the shared heading block"),
    ("F34 the former name Environment back in the footer", "about.html", '>Spaces</a></li>', '>Environment</a></li>', "L21 about.html still uses a former gallery name"),
    ("F35 a link to the former address environment/", "for-artists.html", 'href="spaces/" data-pa-track="nav_gallery_spaces">', 'href="environment/" data-pa-track="nav_gallery_spaces">', "L21 for-artists.html still uses a former gallery name"),
    ("F36 a redirect chain (landscape/ → environment/)", "landscape/index.html", 'location.replace("../spaces/"', 'location.replace("../environment/"', "L21 landscape/index.html must be exactly the generated permanent redirect"),
    ("F37 the environment/ redirect made indexable", "environment/index.html", '<meta name="robots" content="noindex, follow">', '<meta name="robots" content="index, follow">', "L21 environment/index.html must be exactly the generated permanent redirect"),
    ("F38 the gallery heading style removed", "assets/plotart-galleries.css", ".pa-gt .pa-gt-tag{", ".pa-gt-tag-old{", "L21 the gallery heading block (pa-gt) must be styled once"),
    # Mobile Gallery restored (25 Nov 2026): its own pill straight after the Galleries menu, before Living Gallery
    ("F39 the Mobile Gallery pill removed from a page", "about.html", '<a class="pa-pill" href="mobile-gallery/" data-pa-track="nav_mobile_gallery">Mobile Gallery</a>', '', "L21 about.html must carry exactly one Galleries menu"),
    ("F40 the Mobile Gallery pill moved after Living Gallery", "join.html", '<a class="pa-pill" href="mobile-gallery/" data-pa-track="nav_mobile_gallery">Mobile Gallery</a><a class="pa-pill" href="living-gallery.html" data-pa-track="nav_living_gallery">Living Gallery</a>',
     '<a class="pa-pill" href="living-gallery.html" data-pa-track="nav_living_gallery">Living Gallery</a><a class="pa-pill" href="mobile-gallery/" data-pa-track="nav_mobile_gallery">Mobile Gallery</a>', "L21 join.html must carry exactly one Galleries menu"),
    ("F41 the homepage claims Mobile Gallery appointments are available", "index.html", " so appointments can’t yet be arranged through PlotArt.", " and appointments are available now.", "L21 Beyond the Gallery must keep the Mobile Gallery and Living Gallery status sentences"),
    ("F42 Beyond the Gallery heading changed", "index.html", '<h2 id="beyondH">Beyond the Gallery.</h2>', '<h2 id="beyondH">Experiences.</h2>', "L21 the homepage must carry 'Beyond the Gallery.'"),
    ("F43 a prospective gallery named as taking part", "index.html", "We’re inviting galleries to join,", "With Artworld and The Doorway Gallery taking part,", "L21 Beyond the Gallery must not name a prospective gallery"),
    ("F44 an artist's artwork on a Beyond tile", "index.html", 'src="assets/living/plotart-living-gallery-colin-macaulay-artwork.webp" width="1564"', 'src="artists/carolyn-walsh/img/coastal-series-8-1-600.webp" width="1564"', "L21 the living-gallery tile may show only its declared illustration"),
    ("F45 the illustration label removed from the Mobile Gallery tile", "index.html", '<span class="pa-chip pa-chip--illus">AI-generated illustration</span> Painting by Colin MacAulay, PlotArt’s founder. Not from', '<span class="pa-chip">Photograph</span> Painting by Colin MacAulay, PlotArt’s founder. Not from', "L21 the mobile-gallery tile's picture must carry its illustration label"),
    ("F46 the tiles reordered", "index.html", 'data-pa-beyond="mobile-gallery"', 'data-pa-beyond="mobile-gallery-x"', "L21 Beyond the Gallery must show Mobile Gallery, Living Gallery and Art for Hire, in that order"),
    ("F47 Beyond the Gallery not straight after the three galleries", "index.html", "<!-- pa-galleries:end -->\n", "<!-- pa-galleries:end -->\n<p>x</p>\n", "L21 the homepage must carry 'Beyond the Gallery.' straight after the three galleries"),
    ("F48 'Not offered for hire' dropped from the Art for Hire picture", "index.html", "PlotArt’s founder. Not offered for hire.", "PlotArt’s founder.", "L21 the Art for Hire picture must say"),
    ("F14 a Galleries menu link changed on the homepage", "index.html", 'href="being/" data-pa-track="nav_gallery_being">Being<span', 'href="being/" data-pa-track="nav_gallery_being">Beings<span', "L11 index.html must carry the one Galleries menu"),
]


def main():
    tmp = tempfile.mkdtemp(prefix="pa-3g-")
    try:
        base = guard(copy_site(tmp, 0))
        check("G0 the guard passes on the untouched pages", "PLOTART LAUNCH · OK" in base, base.strip().splitlines()[0] if base.strip() else "")
        for i, (name, rel, old, new, want) in enumerate(FAULTS, 1):
            site = copy_site(tmp, i)
            edit(site, rel, old, new)
            out = guard(site)
            check(name + " → refused", "PLOTART LAUNCH · FAILED" in out and want in out, "" if want in out else out[:300])
        sw = json.load(open(SW, encoding="utf-8"))
        sw["spaces_gallery_state"] = "open"
        swp = os.path.join(tmp, "switches-open.json")
        json.dump(sw, open(swp, "w", encoding="utf-8"))
        out = guard(copy_site(tmp, 99), swp)
        check("F15 Spaces switched open before Phase E → refused", "L21 Spaces and Being must stay in_preparation" in out, out[:300])
        sw = json.load(open(SW, encoding="utf-8")); sw["environment_gallery_state"] = "in_preparation"
        swp2 = os.path.join(tmp, "switches-legacy.json"); json.dump(sw, open(swp2, "w", encoding="utf-8"))
        out = guard(copy_site(tmp, 98), swp2)
        check("F26 a retired gallery switch (environment_gallery_state) reintroduced → refused", "L21 retired gallery switches must not come back" in out, out[:300])
        # entrance artwork (final Phase A refinement): only an artist's published artwork with per-use consent, shown whole
        import importlib.util
        spec = importlib.util.spec_from_file_location("gx", os.path.join(ROOT, "atlas-tools", "build-plotart-galleries.py"))
        GX = importlib.util.module_from_spec(spec); spec.loader.exec_module(GX)
        good = {"artist_slug": "carolyn-walsh", "image": "artists/carolyn-walsh/img/coastal-series-8-1-1200.webp", "width": 900, "height": 1200,
                "alt": "Coastal Series 8 by Carolyn Walsh", "credit": "Carolyn Walsh, Coastal Series 8", "consent_ref": "TEST-CONSENT-0001"}
        cases = [("F18 entrance artwork with a provenance record and per-use consent → accepted, shown whole", dict(good), True, ""),
                 ("F19 entrance artwork without a consent reference → refused", dict(good, consent_ref=""), False, "no consent_ref"),
                 ("F20 the artist's portrait photograph as entrance artwork → refused", dict(good, image="artists/carolyn-walsh/img/portrait-600.webp", width=398, height=600),
                  False, "L21 the spaces entrance artwork must be an artist's published artwork")]
        for n, (name, art, ok, want) in enumerate(cases, 200):
            site = copy_site(tmp, n)
            ent = os.path.join(tmp, "entrances-%d.json" % n)
            d = json.load(open(GX.ENTRANCES, encoding="utf-8")); d["spaces"]["artwork"] = art
            json.dump(d, open(ent, "w", encoding="utf-8"))
            try:
                built = GX.home_region(GX.entrances(ent))
                home = os.path.join(site, "plotart", "index.html")
                doc = GX.replace_region(open(home, encoding="utf-8").read(), GX.HOME_BEGIN, GX.HOME_END, built, "index.html")
                open(home, "w", encoding="utf-8").write(doc)
            except ValueError as e:
                check(name, not ok and want in str(e), str(e)[:200]); continue
            out = guard(site, entrances=ent)
            l21 = [l for l in out.splitlines() if l.strip().startswith(("L21", "L6"))]
            if ok:   # the only complaint allowed is the manifest pin of the rebuilt homepage
                check(name, not l21 and 'src="artists/carolyn-walsh/img/coastal-series-8-1-1200.webp"' in built, "; ".join(l21)[:300])
            else:
                check(name, want in out, out[:300])
        for tool in ("plotart-galleries-nav.py", "build-plotart-galleries.py"):
            p = subprocess.run([sys.executable, os.path.join(ROOT, "atlas-tools", tool), ROOT, "--check"], capture_output=True, text=True)
            check("C %s --check has nothing left to do" % tool, p.returncode == 0, (p.stdout + p.stderr).strip()[:200])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for name, ok, detail in results:
        print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, ("  [" + detail + "]") if (detail and not ok) else ""))
    bad = sum(not ok for _, ok, _ in results)
    print("PLOTART THREE GALLERIES · %d checks, %d passed, %d failed" % (len(results), len(results) - bad, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
