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
    # A6 (12 Nov 2026): the governed alias input the builder now reads.
    shutil.copy2(ROOT / "atlas-tools" / "search-supplier-aliases.json",
                 tmp / "atlas-tools" / "search-supplier-aliases.json")
    for f in PAGES:
        if (ROOT / f).exists():
            # Sitemap pages may sit in sub-folders (plotart/, suppliers/): create the folder first.
            # Pre-existing harness defect, repaired 10 Nov 2026 (Amendment A4 work): the suite crashed.
            (tmp / f).parent.mkdir(parents=True, exist_ok=True)
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
        if mutate_builder and b == BUILDER_SRC:
            # A builder mutation whose anchor no longer exists changes nothing, so the
            # unmutated builder passes and the case reports BLIND for the wrong reason
            # (C9b, found 11 Nov 2026: its anchor went stale when price_current() was
            # added to euro_price()). Fail it as a stale anchor, naming the cause.
            failed += 1
            print("  [*** STALE] %-48s %-8s the mutation anchor is not in the builder" % (label, kind))
            return
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
             '    if euro_price(r):\n        rec["price"] = r["price"]',
             '    if is_price(r.get("price")):\n        rec["price"] = r["price"]'))

run_case("C9  G7b a price-safe product loses its price", "BUILDER",
         "G7b price-safe products not carrying a price",
         mutate_builder=lambda b: b.replace(
             '    if euro_price(r):\n        rec["price"] = r["price"]',
             '    if euro_price(r) and r.get("organisation") != "Adman Steel Sheds":\n        rec["price"] = r["price"]'))
# Re-anchored 6 Nov 2026 (Stage 3D-B1): the original sabotage (dropping float prices)
# no longer bites, because every float price in the garden corpus was GBP and those
# prices now correctly carry no euro figure. The case still drops price-safe EUR
# prices silently, which is what G7b exists to catch.

# ------------------------------------------------------------------------ G7f
# AMENDMENT A5 (10 Nov 2026): "From" only where the source records "Starting From".
run_case("C9d G7f a 'From' is inferred for a fixed price", "BUILDER",
         "G7f starting-price marks",
         mutate_builder=lambda b: b.replace(
             '        if norm_space(r.get("priceType") or "") == STARTING_FROM:\n            rec["pf"] = 1',
             '        if norm_space(r.get("priceType") or "") in (STARTING_FROM, "Standard Price"):\n            rec["pf"] = 1'))
run_case("C9e G7f an explicit starting price loses its 'From'", "BUILDER",
         "G7f starting-price marks",
         mutate_builder=lambda b: b.replace(
             '        if norm_space(r.get("priceType") or "") == STARTING_FROM:\n            rec["pf"] = 1',
             '        if norm_space(r.get("priceType") or "") == STARTING_FROM and r.get("organisation") != "SIPS-House":\n            rec["pf"] = 1'))

# ------------------------------------------------------------------------ G7c
# STAGE 3D-B1 (6 Nov 2026): Search shows every price as euro. These two cases
# re-create the defect found in Stage 3D-A (GBP/USD prices shown with a euro sign,
# matched by euro filters, and setting euro supplier ranges) and prove G7c refuses.
run_case("C9b G7c a GBP/USD price is shown as euro", "BUILDER",
         "G7c a non-EUR price would be shown as euro",
         mutate_builder=lambda b: b.replace(
             '            and r.get("currency") == "EUR" and price_current(r))',
             '            and price_current(r))'))
run_case("C9c G7c a supplier range is built from GBP/USD", "BUILDER",
         "G7c supplier",
         mutate_builder=lambda b: b.replace(
             '    prices = [x["price"] for x in rs if euro_price(x)]',
             '    prices = [x["price"] for x in rs\n              if x.get("priceSafeForMatching") and is_price(x.get("price"))]'))

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
# Amendment A4 (founder approval 10 Nov 2026): the single 180 KB raw-size guard became three
# performance guards. Each is proved separately, and each refusal must still say the guard is
# NOT a corpus ceiling (nothing dropped to fit). The real index passes all three, so each
# BUILDER case lowers exactly one limit below the real corpus and leaves the other two alone.
run_case("C13a G10a the compressed index exceeds its guard", "BUILDER",
         "G10a the complete governed corpus compresses",
         mutate_builder=lambda b: b.replace("GZIP_GUARD = 40 * 1024", "GZIP_GUARD = 4 * 1024"))
run_case("C13b G10b the uncompressed index exceeds its guard", "BUILDER",
         "G10b the complete governed corpus is",
         mutate_builder=lambda b: b.replace("RAW_GUARD = 256 * 1024", "RAW_GUARD = 4 * 1024"))
run_case("C13c G10c the record count exceeds its guard", "BUILDER",
         "G10c the complete governed corpus has",
         mutate_builder=lambda b: b.replace("RECORD_GUARD = 1100", "RECORD_GUARD = 100"))
run_case("C13d every G10 refusal says it is not a corpus ceiling", "BUILDER",
         "THESE GUARDS ARE NOT A CORPUS CEILING",
         mutate_builder=lambda b: b.replace("RECORD_GUARD = 1100", "RECORD_GUARD = 100"))


def _grow_corpus(d):
    # INPUT growth: clone eligible products under new ids until the corpus has more than
    # 1,100 searchable records. The real G10c limit (not a lowered one) must refuse it.
    # The harness corpus is smaller than the live one (it carries the garden-room universe only), so
    # 450 clones are needed to pass 1,100. Each clone gets a well-formed governed id (rec + 14).
    base = list(d["products"])
    for i in range(450):
        c = json.loads(json.dumps(base[i % len(base)]))
        c["id"] = "recA4G%011d" % i
        d["products"].append(c)


run_case("C13e G10c the real corpus grows past 1,100 records", "INPUT",
         "G10c the complete governed corpus has",
         mutate_tree=lambda t: set_universe(t, _grow_corpus))


def _fatten_compressible(d):
    # INPUT: every product name (productName, what the index shows) gains 200 highly compressible characters. The raw index passes
    # 256 KB while the compressed size and the record count stay inside their limits: only G10b fires.
    for p in d["products"]:
        p["productName"] = (p.get("productName") or p["name"]) + " " + "a" * 200


def _fatten_incompressible(d):
    # INPUT: every product name (productName) gains 40 pseudo-random characters (fixed seed, reproducible).
    # gzip cannot remove them, so the download passes 40 KB while the raw size stays under
    # 256 KB and the record count is unchanged: only G10a fires.
    import random
    rnd = random.Random(20261110)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    for p in d["products"]:
        p["productName"] = (p.get("productName") or p["name"]) + " " + "".join(rnd.choice(alphabet) for _ in range(40))


run_case("C13f G10b the real corpus grows past 256 KB uncompressed", "INPUT",
         "G10b the complete governed corpus is",
         mutate_tree=lambda t: set_universe(t, _fatten_compressible))
run_case("C13g G10a the real corpus grows past 40 KB compressed", "INPUT",
         "G10a the complete governed corpus compresses",
         mutate_tree=lambda t: set_universe(t, _fatten_incompressible))

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

# ------------------------------------- SEARCH-V1 amendment A1 (4 Nov 2026)
# Wellness products route through the second envelope template (routes.wellness),
# named by "rt": "wellness". These cases run with the real wellness universe copied
# in, so R1 has wellness products to judge.
def _with_wellness(t):
    shutil.copy2(ROOT / "wellness-universe-v1.json", t / "wellness-universe-v1.json")

run_case("C20 A1 a wellness product loses its template key", "BUILDER",
         "must name the wellness template", mutate_tree=_with_wellness,
         mutate_builder=lambda b: b.replace('        rec["rt"] = WL_TEMPLATE_KEY', '        pass'))

run_case("C21 A1 a product carries a per-record route again", "BUILDER",
         "carries a per-record route", mutate_tree=_with_wellness,
         # One product is enough to prove R1 refuses a per-record route. Injecting it
         # into all 128 wellness products pushed the corpus over the 180 KB guard once
         # DISC-035 joined the index, so G10 fired first and masked R1 (4 Nov 2026).
         # The 180 KB guard itself is unchanged.
         mutate_builder=lambda b: b.replace('        rec["rt"] = WL_TEMPLATE_KEY',
                                            '        rec["rt"] = WL_TEMPLATE_KEY\n        if rec["id"] == "prod-recdDCBpXBKOa7leI":\n            rec["route"] = wl_route(rec["id"][5:])'))

run_case("C22 A1 the wellness template points somewhere else", "BUILDER",
         "not its own explorer entry", mutate_tree=_with_wellness,
         mutate_builder=lambda b: b.replace('WL_TEMPLATE = WL_PAGE + "#p-{id}"',
                                            'WL_TEMPLATE = "discovery-living-in-the-garden.html#p-{id}"'))


# ------------------------------------------------------------------------- A6
# AMENDMENT A6 (founder approval, 12 Nov 2026): supplier recognition aliases.
# Each case breaks exactly one A6 rule in the governed alias input (or, for A6e,
# in the builder) and must be refused by that guard alone.
def _aliases(fn):
    def m(tmp):
        p = tmp / "atlas-tools" / "search-supplier-aliases.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        fn(d)
        p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return m


def _org(d, name):
    return next(e for e in d["organisations"] if e["name"] == name)


run_case("C23 A6b two organisations claim one domain", "INPUT", "A6b DUPLICATE ALIAS",
         mutate_tree=_aliases(lambda d: _org(d, "Loghouse").__setitem__("website", "https://www.sproutpod.ie/")))
run_case("C24 A6b a descriptor is read as a trading name", "INPUT", "A6b DUPLICATE ALIAS 'gardenrooms'",
         mutate_tree=_aliases(lambda d: d.__setitem__("excludedNames", [])))
run_case("C25 A6a a permitted domain without a confirmed grant", "INPUT", "A6a",
         mutate_tree=_aliases(lambda d: _org(d, "Shomera")["permittedDomains"].append(
             {"domain": "shomera.com", "ref": "X", "outcome": "Unknown — Awaiting Reply"})))
run_case("C26 A6a a permitted domain that is not a hostname", "INPUT", "A6a",
         mutate_tree=_aliases(lambda d: _org(d, "Shomera")["permittedDomains"].append(
             {"domain": "https://shomera.ie/garden-rooms", "ref": "X",
              "outcome": "Granted — Founder Confirmed"})))
run_case("C27 A6c a trading name for an unpublished organisation", "INPUT", "A6c",
         mutate_tree=_aliases(lambda d: d["tradingNames"].append(
             {"organisation": "Shed Factory Ireland", "name": "Shed Factory", "evidence": "test"})))
run_case("C28 A6 a retail-channel alias (deferred)", "INPUT", "retail-channel aliases are deferred",
         mutate_tree=_aliases(lambda d: d.__setitem__("channels", [
             {"alias": "Summerhouse24", "hosts": ["summerhouse24.ie"], "target": "Hansa24 Group"}])))
run_case("C29 A6d a trading name under four characters", "INPUT", "A6d",
         mutate_tree=_aliases(lambda d: d["tradingNames"].append(
             {"organisation": "Shomera", "name": "SH", "evidence": "test"})))
run_case("C30 A6e an alias names a pool-only organisation", "BUILDER", "A6e",
         mutate_builder=lambda b: b.replace(
             "a6_published = a6_emitted | set(PAGE_ORG.values())",
             "a6_published = a6_emitted | set(PAGE_ORG.values()) | {'Steeltech Sheds'}"))

print()
print("  %d guards proven capable, %d blind" % (passed, failed))
print()
print("  ORDERING NOTE. G13 is the catch-all and runs AFTER the specific guards,")
print("  deliberately, so a precise diagnosis wins over a generic one and each")
print("  specific guard stays independently fireable rather than masked. C15 and")
print("  C16 reach G13 only because no earlier guard claims those shapes.")
sys.exit(1 if failed else 0)
