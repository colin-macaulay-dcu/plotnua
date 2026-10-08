#!/usr/bin/env python3
"""
GUARD-CAPABILITY PROOF · build-search-index.py
===============================================================================
A guard that has never been seen to fail is not a proven guard.

This driver builds a disposable copy of the repository layout, breaks ONE thing
per case, runs the builder in --check mode against the copy, and asserts the
builder REFUSES with the expected guard named in the refusal.

Two kinds of sabotage, each labelled:

  INPUT    the corpus handed to the builder is corrupted. Proves the guard
           catches bad data.
  BUILDER  the builder's own logic is corrupted. Proves the guard catches a
           builder that would emit the wrong thing — the failure mode that
           actually ships.

Nothing here touches the real index, the real universe, any page, or Airtable.

    python3 prove-search-guards.py
"""

import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILDER_SRC = (ROOT / "atlas-tools" / "build-search-index.py").read_text(encoding="utf-8")

# Files the builder reads. Copied, never touched in place.
NEEDED = ["garden-room-recommendation-universe-v1.json", "sitemap.xml",
          "atlas-recognition-pool.json"]
PAGES = sorted(set(
    [p for p in re.findall(r"<loc>https://plotnua\.ie/([^<]*)</loc>",
                           (ROOT / "sitemap.xml").read_text(encoding="utf-8"))
     if p.endswith(".html")]
    + ["your-plot.html"]
    + [f for f in [
        "disc025-borrowed-garden-check.html", "disc026-power-station.html",
        "disc022-hidden-cars-check.html", "disc029-hidden-bins-check.html",
        "disc014-driveway-income.html", "disc005-home-exchange.html",
        "disc027-neighbourhood-parcel-house.html",
        "disc024-open-your-home-to-art.html",
        "disc023-buy-original-irish-art.html"] if (ROOT / f).exists()]
))

PRODUCT_REC = """        "tier": tier,
        "caveats": caveats,
    }"""

passed = failed = 0


def make_tree(tmp):
    (tmp / "atlas-tools").mkdir(parents=True, exist_ok=True)
    for f in NEEDED:
        shutil.copy2(ROOT / f, tmp / f)
    shutil.copy2(ROOT / "atlas-tools" / "search-topic-map.json",
                 tmp / "atlas-tools" / "search-topic-map.json")
    for f in PAGES:
        if (ROOT / f).exists():
            shutil.copy2(ROOT / f, tmp / f)
    # One real preview, so the G2 sabotage has something true to leak.
    prev = sorted(ROOT.glob("*-preview.html"))
    if prev:
        shutil.copy2(prev[0], tmp / prev[0].name)


def run_case(label, kind, expect, mutate_tree=None, mutate_builder=None,
             refresh_sha=True):
    global passed, failed
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="sguard-"))
    try:
        make_tree(tmp)
        if mutate_tree:
            mutate_tree(tmp)
        b = mutate_builder(BUILDER_SRC) if mutate_builder else BUILDER_SRC
        if refresh_sha:
            # So the case under test fires rather than the base-sha guard, which
            # has its own case (C4).
            import hashlib
            s = hashlib.sha256(
                (tmp / "garden-room-recommendation-universe-v1.json").read_bytes()
            ).hexdigest()
            b = re.sub(r'BASE_UNIVERSE_SHA = "[0-9a-f]{64}"',
                       'BASE_UNIVERSE_SHA = "%s"' % s, b)
        (tmp / "atlas-tools" / "b.py").write_text(b, encoding="utf-8")
        r = subprocess.run([sys.executable, str(tmp / "atlas-tools" / "b.py"), "--check"],
                           capture_output=True, text=True)
        out = r.stdout + r.stderr
        ok = r.returncode == 1 and "REFUSED:" in out and expect in out
        if ok:
            passed += 1
            why = out.split("REFUSED:")[1].strip().split("\n")[0]
            print("  [CAPABLE  ] %-48s %-8s %s" % (label, kind, why[:60]))
        else:
            failed += 1
            print("  [*** BLIND] %-48s %-8s rc=%s" % (label, kind, r.returncode))
            print("              expected a refusal naming %r" % expect)
            print("              got: %s" % out.strip().replace("\n", " | ")[-260:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def set_universe(tmp, fn):
    p = tmp / "garden-room-recommendation-universe-v1.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    fn(d)
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


print("\n  GUARD-CAPABILITY PROOF · build-search-index.py\n")

# ----------------------------------------------------------------- G1 / G1b
# ===================== RE-AIMED AFTER THE ARCHITECTURE CHANGED ==============
# Products no longer carry a per-record route (the size guard forced the
# template into the envelope), so the old sabotage — rewriting PRODUCT_ROUTE —
# has nothing to rewrite and the case went blind at rc=0. The records that DO
# still carry a route are possibilities and journeys, so G1 is attacked there.
# CURRENT INVARIANT BROKEN: a record's route page must be sitemap-listed or
# declared. A possibility is pointed at a private preview page.
run_case("C1  G1 a possibility routes outside the allowlist", "BUILDER",
         "G1 allowlist",
         mutate_builder=lambda b: b.replace(
             '        "route": fname,', '        "route": "auroom-wellness-preview.html",'))

# RE-AIMED. your-plot.html is no longer any record's route, so the old
# "declare thanks.html and point products at it" sabotage could not reach G1b.
# The exempt routes now in use are the nine journeys, so the sabotage declares
# a TENTH journey whose file exists but which nothing links to.
# CURRENT INVARIANT BROKEN: a non-sitemap route must be reachable from a public
# page today — the clause that stops DECLARED_ROUTES becoming a back door.
run_case("C2  G1b an exempt route nothing links to", "BUILDER", "G1b",
         mutate_builder=lambda b: b.replace(
             'JOURNEYS = {',
             'JOURNEYS = {\n    "thanks.html": "discovery-hidden-cars.html",'),
         mutate_tree=lambda tmp: (tmp / "thanks.html").write_text(
             "<title>Thanks | PlotNua</title>", encoding="utf-8"))

# RE-AIMED. The old sabotage injected a preview name through a helper that
# wrote into the product "name" alongside a per-record route; that anchor is
# gone. It now writes into productType, which is a field the CURRENT schema
# really carries, so the leak is as realistic as it was.
# CURRENT INVARIANT BROKEN: no private-preview filename, path or template may
# appear anywhere in the index.
run_case("C3  G2 a private preview reaches the index", "BUILDER",
         "G2 PRIVATE PREVIEW LEAK",
         mutate_builder=lambda b: b.replace(
             '        "productType": norm_space(r.get("productType")),',
             '        "productType": "see auroom-wellness-preview.html",'))

run_case("C4  G4 universe is not the frozen corpus", "INPUT",
         "refusing to build against an unexpected corpus",
         mutate_tree=lambda t: set_universe(t, lambda d: d.setdefault("x", 1)),
         refresh_sha=False)

run_case("C5  G3a a retired 'Moved' stub becomes a possibility", "INPUT",
         "G3a",
         mutate_tree=lambda t: (
             (t / "discovery-artist-studio.html").write_text(
                 "<title>Moved | PlotNua</title>", encoding="utf-8"),
             (t / "sitemap.xml").write_text(
                 (t / "sitemap.xml").read_text(encoding="utf-8").replace(
                     "</urlset>",
                     "<url><loc>https://plotnua.ie/discovery-artist-studio.html</loc></url></urlset>"),
                 encoding="utf-8")))

# ------------------------------------------------------------------------- G5
# RE-ANCHORED ONLY. The rule and the sabotage are unchanged in substance; the
# product record literal lost its "route" line, so the old anchor text no
# longer existed and the case went blind.
# CURRENT INVARIANT BROKEN: no qualification/evidence field may be copied into
# the index.
run_case("C6  G5 an evidence field is copied through", "BUILDER",
         "G5 forbidden field",
         mutate_builder=lambda b: b.replace(
             PRODUCT_REC,
             '        "tier": tier,\n'
             '        "caveats": caveats,\n'
             '        "priceEvidence": r.get("priceEvidence"),\n    }'))

run_case("C7  G6 a tier is upgraded", "BUILDER",
         "G6",
         mutate_builder=lambda b: b.replace(
             '        "tier": tier,', '        "tier": "HIGH_CONFIDENCE",'))

run_case("C8  G7 an unsafe price is emitted", "BUILDER",
         "G7 product",
         mutate_builder=lambda b: b.replace(
             'if r.get("priceSafeForMatching") and is_price(r.get("price")):',
             'if is_price(r.get("price")):'))

run_case("C9  G7b a price-safe product loses its price", "BUILDER",
         "G7b price-safe products not carrying a price",
         mutate_builder=lambda b: b.replace(
             'if r.get("priceSafeForMatching") and is_price(r.get("price")):',
             'if r.get("priceSafeForMatching") and isinstance(r.get("price"), int):'))

# ------------------------------------------------------------------------- G8
# RE-ANCHORED ONLY, same reason as C6.
# CURRENT INVARIANT BROKEN: Search V1 is text-only — no imagery-shaped field
# may exist, so unauthorised imagery cannot leak through Search at all.
run_case("C10 G8 imagery is added to a product", "BUILDER",
         "G8 imagery-shaped field",
         mutate_builder=lambda b: b.replace(
             PRODUCT_REC,
             '        "tier": tier,\n'
             '        "caveats": caveats,\n'
             '        "imagery": {"alt": "x"},\n    }'))

run_case("C11 G8 an image URL hides in a text field", "BUILDER",
         "G8 an image file reference",
         mutate_builder=lambda b: b.replace(
             '        "productType": norm_space(r.get("productType")),',
             '        "productType": "shed assets/img/abc.jpg",'))

# ------------------------------------------------------------------------- G9
run_case("C12 G9 the Irish-route caveat is dropped", "BUILDER",
         "G9 noPublishedIrishRoute",
         mutate_builder=lambda b: b.replace(
             '    if r.get("noPublishedIrishRoute"):\n'
             '        caveats.append("no-published-irish-route")',
             '    if False:\n        caveats.append("no-published-irish-route")'))

# ------------------------------------------------------------------------ G10
run_case("C13 G10 the corpus exceeds the performance guard", "BUILDER",
         "180 KB IS NOT A CORPUS CEILING",
         mutate_builder=lambda b: b.replace("SIZE_GUARD = 180 * 1024",
                                            "SIZE_GUARD = 4 * 1024"))

# ------------------------------------------------------------------------ G12
# C14 ORIGINALLY MIS-AIMED. A journey file that does not exist is also a file
# nothing links to, so G1b fired first and G12 was never reached — the guard was
# fine, the sabotage was wrong. Deleting a file that IS linked lets G1b pass and
# puts G12 under test, which is the point.
# RE-AIMED, AND THE HARDEST OF THE SEVEN TO AIM HONESTLY.
#
# G12 ("every route resolves to a file that exists") now only bites journeys:
# products compose their route from the envelope template, and a possibility
# pointing at a missing file is caught earlier by the sitemap existence check.
# Reaching G12 therefore needs a route that passes G1 (it is a declared
# journey), passes G1b (it IS linked from a public page), and whose file is
# nevertheless absent.
#
# That takes TWO mutations, and both are stated plainly rather than hidden: the
# journey file is deleted from the disposable tree, and the builder's own
# existence pre-check and title read are removed so the record is still
# emitted. Without the second mutation the builder would crash reading a
# missing file instead of refusing, and a crash is not a guard firing.
# CURRENT INVARIANT BROKEN: a route must resolve to a file that exists.
run_case("C14 G12 a journey route points at a missing file", "BUILDER",
         "G12 record",
         mutate_builder=lambda b: b.replace(
             '    if not (ROOT / jfile).exists():\n        continue\n',
             '').replace(
             '    title, _ = page_fields(jfile)',
             '    title = "Hidden Cars \u2014 Property Check"'),
         mutate_tree=lambda tmp: (tmp / "disc022-hidden-cars-check.html").unlink())

# RE-ANCHORED ONLY, same reason as C6.
# CURRENT INVARIANT BROKEN: the catch-all — nothing outside the four declared
# types and their declared fields. It runs LAST, so reaching it also proves no
# earlier guard claims this shape.
run_case("C15 G13 an undeclared field is smuggled in", "BUILDER",
         "G13 record",
         mutate_builder=lambda b: b.replace(
             PRODUCT_REC,
             '        "tier": tier,\n'
             '        "caveats": caveats,\n'
             '        "relevanceBoost": 2,\n    }'))

run_case("C16 G13 the envelope gains a key", "BUILDER",
         "G13 the envelope carries undeclared keys",
         mutate_builder=lambda b: b.replace(
             '    "records": records,\n}',
             '    "records": records,\n    "atlasRank": 1,\n}'))

# -------------------------------------------------------------- topic-map gate
run_case("C17 an unapproved topic-map entry", "INPUT",
         "not APPROVED",
         mutate_tree=lambda t: (t / "atlas-tools" / "search-topic-map.json").write_text(
             json.dumps({"version": "1", "entries": [
                 {"phrase": "x", "targets": ["about.html"], "status": "PROPOSED"}]}),
             encoding="utf-8"))

run_case("C18 a topic-map entry targets a non-public page", "INPUT",
         "not in the sitemap allowlist",
         mutate_tree=lambda t: (t / "atlas-tools" / "search-topic-map.json").write_text(
             json.dumps({"version": "1", "entries": [
                 {"phrase": "sauna", "targets": ["auroom-wellness-preview.html"],
                  "status": "APPROVED"}]}),
             encoding="utf-8"))

run_case("C19 the sitemap yields no allowlist at all", "INPUT",
         "refusing to build an ungated index",
         mutate_tree=lambda t: (t / "sitemap.xml").write_text(
             "<urlset></urlset>", encoding="utf-8"))

print()
print("  %d guards proven capable, %d blind" % (passed, failed))
print()
print("  ORDERING NOTE. G13 is the catch-all and runs AFTER the specific guards,")
print("  deliberately, so a precise diagnosis wins over a generic one and each")
print("  specific guard stays independently fireable rather than masked. C15 and")
print("  C16 reach G13 only because no earlier guard claims those shapes.")
sys.exit(1 if failed else 0)
