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
    ("F1 an image on the Environment entrance", "index.html", 'data-pa-placeholder="environment"', 'data-pa-placeholder="environment"><img src="assets/hero/founder-01-abstract.webp" alt="x"', "L21 the environment entrance shows an image but no authorised entrance artwork"),
    ("F2 'Gallery open' on the Being entrance", "index.html", '<p class="pa-gx-status">In preparation</p><h2>Being.</h2>', '<p class="pa-gx-status">Gallery open</p><h2>Being.</h2>', "L21 the being entrance"),
    ("F3 an Artists in Focus section on a holding page", "environment/index.html", '<p class="pa-gh-status">In preparation</p>', '<p class="pa-gh-status">In preparation</p><h2>Artists in Focus</h2>', "L21 environment/index.html must be a holding page"),
    ("F4 an artist's artwork on a holding page", "being/index.html", '<figure class="pa-gh-art">', '<figure class="pa-gh-art"><img src="../artists/carolyn-walsh/img/coastal-series-8-1-600.webp" alt="x">', "L21 being/index.html must be a holding page"),
    ("F5 a holding page made indexable", "environment/index.html", '<meta name="robots" content="noindex, follow">', '<meta name="robots" content="index, follow">', "L21 environment/index.html must be noindex"),
    ("F6 entrance artwork cropped", "assets/plotart-galleries.css", "object-fit:contain", "object-fit:cover", "L21 gallery entrance artwork must be shown whole"),
    ("F7 the gallery tabs removed from Contemporary", "gallery/index.html", '<nav class="pa-gtabs"', '<nav class="pa-gtabs-gone"', "L21 gallery/index.html must carry the gallery tabs"),
    ("F8 the Contemporary heading reverted", "gallery/index.html", "<h1>Contemporary.</h1>", "<h1>Contemporary Art.</h1>", "L21 the Contemporary gallery's heading must be 'Contemporary.'"),
    ("F9 an extra label under the homepage heading", "index.html", "A new home for Irish art.</h1>", "A new home for Irish art.</h1><p>Three curated galleries</p>", "L6 the homepage heading must be exactly"),
    ("F10 'Real art. Real homes.' restored", "index.html", "<h3>Living Gallery</h3>", "<h3>Real art. Real homes.</h3>", "L21 the homepage must present the Living Gallery"),
    ("F11 Art for Hire enquiries wording removed", "index.html", " Hire enquiries are not yet open.</p>", "</p>", "L21 the homepage must say Art for Hire enquiries are not yet open"),
    ("F12 an Artists' Gallery pill back on an artwork page", "artists/carolyn-walsh/coastal-series-8.html", 'data-pa-track="nav_mobile_gallery">Mobile Gallery</a>',
     'data-pa-track="nav_mobile_gallery">Mobile Gallery</a><a class="pa-pill" href="../../gallery/" data-pa-track="nav_virtual_gallery">Artists’ Gallery</a>', "L21 artists/carolyn-walsh/coastal-series-8.html must carry exactly one Galleries menu"),
    # Mobile Gallery restored to the primary navigation (founder brief 25 Nov 2026)
    ("F31 the Mobile Gallery pill folded back into the Galleries menu", "artists/carolyn-walsh/coastal-series-8.html",
     '</div></details><a class="pa-pill" href="../../mobile-gallery/" data-pa-track="nav_mobile_gallery">Mobile Gallery</a>',
     '<a class="pa-dd-link" href="../../mobile-gallery/" data-pa-track="nav_mobile_gallery">Mobile Gallery</a></div></details>', "L21 artists/carolyn-walsh/coastal-series-8.html must carry exactly one Galleries menu, then the Mobile Gallery pill"),
    ("F32 the Mobile Gallery pill dropped from the homepage", "index.html", '<a class="pa-pill" href="mobile-gallery/" data-pa-track="nav_mobile_gallery">Mobile Gallery</a>', "", "L11 index.html navigation is"),
    ("F33 the Mobile Gallery pill not marked current on its own page", "mobile-gallery/index.html", 'href="index.html" aria-current="page" data-pa-track="nav_mobile_gallery">', 'href="index.html" data-pa-track="nav_mobile_gallery">', "L11 mobile-gallery/index.html current pill"),
    # Beyond the Gallery (founder brief 25 Nov 2026)
    ("F34 Beyond the Gallery heading changed", "index.html", '<h2 id="beyondH">Beyond the Gallery.</h2>', '<h2 id="beyondH">Experiences.</h2>', "L21 the homepage must carry 'Beyond the Gallery.'"),
    ("F35 a prospective gallery named as taking part", "index.html", "We’re inviting galleries to join,", "With Artworld and The Doorway Gallery taking part,", "L21 Beyond the Gallery must not name a prospective gallery"),
    ("F36 an artist's artwork on a Beyond tile", "index.html", 'src="assets/living/plotart-living-gallery-colin-macaulay-artwork.webp" width="1564"', 'src="artists/carolyn-walsh/img/coastal-series-8-1-600.webp" width="1564"', "L21 the living-gallery tile may show only its declared illustration"),
    ("F37 the illustration label removed from the Mobile Gallery tile", "index.html", '<span class="pa-chip pa-chip--illus">AI-generated illustration</span> Painting by Colin MacAulay, PlotArt’s founder. Not from', '<span class="pa-chip">Photograph</span> Painting by Colin MacAulay, PlotArt’s founder. Not from', "L21 the mobile-gallery tile's picture must carry its illustration label"),
    ("F38 the tiles reordered", "index.html", 'data-pa-beyond="mobile-gallery"', 'data-pa-beyond="mobile-gallery-x"', "L21 Beyond the Gallery must show Mobile Gallery, Living Gallery and Art for Hire, in that order"),
    ("F39 the Mobile Gallery appointment caveat removed", "index.html", " so appointments can’t yet be arranged through PlotArt.", ".", "L21 Beyond the Gallery must keep the Mobile Gallery and Living Gallery status sentences"),
    ("F40 Beyond the Gallery moved below Artist Submissions", "index.html", "<!-- pa-galleries:end -->\n", "<!-- pa-galleries:end -->\n<p>x</p>\n", "L21 the homepage must carry 'Beyond the Gallery.' straight after the three galleries"),
    ("F13 a holding page implying an opening date", "being/index.html", "This gallery is being prepared.", "This gallery is opening soon.", "L9"),
    ("F16 an artist link on the Being entrance", "index.html", '<p class="pa-gx-text">Life, identity', '<a href="artists/carolyn-walsh/">x</a><p class="pa-gx-text">Life, identity', "L21 the being entrance must say In preparation, link only to its holding page and never to an artist"),
    ("F17 the Contemporary search title reverted", "gallery/index.html", "<title>Contemporary Irish Art Gallery | PlotArt</title>", "<title>Irish Artists &amp; Original Art | Artists’ Gallery | PlotArt</title>", "L11 the Contemporary Art gallery's search title"),
    # final gallery identity (24 Nov 2026): names, editorial full stops, descriptions, plain navigation and redirects
    ("F21 a former name (Landscape Art) back in a footer", "about.html", '>Environment</a></li>', '>Landscape Art</a></li>', "L21 about.html still uses a former gallery name"),
    ("F22 a link to a former address (portraiture/)", "for-artists.html", 'href="being/" data-pa-track="nav_gallery_being">', 'href="portraiture/" data-pa-track="nav_gallery_being">', "L21 for-artists.html still uses a former gallery name"),
    ("F23 the approved Environment description shortened", "environment/index.html", " diverse artistic interpretations of our surroundings.</p>", ".</p>", "L21 environment/index.html must carry the approved name, title and gallery description"),
    ("F24 a redirect made indexable", "portraiture/index.html", '<meta name="robots" content="noindex, follow">', '<meta name="robots" content="index, follow">', "L21 portraiture/index.html must be exactly the generated permanent redirect"),
    ("F25 a redirect chain (landscape/ → places-and-spaces/)", "landscape/index.html", 'location.replace("../environment/"', 'location.replace("../places-and-spaces/"', "L21 landscape/index.html must be exactly the generated permanent redirect"),
    ("F27 a full stop in the navigation", "index.html", 'data-pa-track="nav_gallery_being">Being<', 'data-pa-track="nav_gallery_being">Being.<', "L21 the navigation must name the galleries Contemporary, Environment and Being, without full stops"),
    ("F28 the editorial full stop dropped from an entrance", "index.html", "<h2>Environment.</h2>", "<h2>Environment</h2>", "L21 the environment entrance must read 'Environment.'"),
    ("F29 a Being introduction changed", "index.html", "Life, identity, emotion and existence.", "Portraits and the human subject.", "L21 the being entrance must read 'Being.'"),
    ("F30 the Places & Spaces redirect pointed elsewhere", "places-and-spaces/index.html", 'location.replace("../environment/"', 'location.replace("../gallery/"', "L21 places-and-spaces/index.html must be exactly the generated permanent redirect"),
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
        sw["environment_gallery_state"] = "open"
        swp = os.path.join(tmp, "switches-open.json")
        json.dump(sw, open(swp, "w", encoding="utf-8"))
        out = guard(copy_site(tmp, 99), swp)
        check("F15 Environment switched open before Phase E → refused", "L21 Environment and Being must stay in_preparation" in out, out[:300])
        sw = json.load(open(SW, encoding="utf-8")); sw["landscape_gallery_state"] = "in_preparation"
        swp2 = os.path.join(tmp, "switches-legacy.json"); json.dump(sw, open(swp2, "w", encoding="utf-8"))
        out = guard(copy_site(tmp, 98), swp2)
        check("F26 a retired gallery switch (landscape_gallery_state) reintroduced → refused", "L21 retired gallery switches must not come back" in out, out[:300])
        # entrance artwork (final Phase A refinement): only an artist's published artwork with per-use consent, shown whole
        import importlib.util
        spec = importlib.util.spec_from_file_location("gx", os.path.join(ROOT, "atlas-tools", "build-plotart-galleries.py"))
        GX = importlib.util.module_from_spec(spec); spec.loader.exec_module(GX)
        good = {"artist_slug": "carolyn-walsh", "image": "artists/carolyn-walsh/img/coastal-series-8-1-1200.webp", "width": 900, "height": 1200,
                "alt": "Coastal Series 8 by Carolyn Walsh", "credit": "Carolyn Walsh, Coastal Series 8", "consent_ref": "TEST-CONSENT-0001"}
        cases = [("F18 entrance artwork with a provenance record and per-use consent → accepted, shown whole", dict(good), True, ""),
                 ("F19 entrance artwork without a consent reference → refused", dict(good, consent_ref=""), False, "no consent_ref"),
                 ("F20 the artist's portrait photograph as entrance artwork → refused", dict(good, image="artists/carolyn-walsh/img/portrait-600.webp", width=398, height=600),
                  False, "L21 the environment entrance artwork must be an artist's published artwork")]
        for n, (name, art, ok, want) in enumerate(cases, 200):
            site = copy_site(tmp, n)
            ent = os.path.join(tmp, "entrances-%d.json" % n)
            d = json.load(open(GX.ENTRANCES, encoding="utf-8")); d["environment"]["artwork"] = art
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
