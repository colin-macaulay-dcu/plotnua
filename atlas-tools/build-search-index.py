#!/usr/bin/env python3
"""
BOUNDED BUILDER · search-index-v1.json
===============================================================================
Generates the PlotNua search index from the ALREADY-PUBLISHED governed corpus,
under the frozen contract in governance/SEARCH-V1-CONTRACT.md.

ONE DIRECTION ONLY. This builder READS the universe and the sitemap and WRITES
one file. It never writes to the universe, the detail artefacts, the rights
files, any page, or Airtable. Search is downstream of Atlas by construction.

THE GATE IS AN ALLOWLIST. A route enters the index only if its URL is present
in sitemap.xml. Not "if not noindex": under a denylist a supplier preview added
next month would silently inherit indexability. There are 106 private previews
on disk and robots.txt is Allow:/ with no Disallow, so their privacy rests
entirely on per-page meta tags. A generated index is a NEW crawlable artefact,
and a preview URL inside it would be discoverable from the index file itself.

    python3 build-search-index.py            build
    python3 build-search-index.py --check    guards only, write nothing
"""

import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "search-index-v1.json"
UNIVERSE = ROOT / "garden-room-recommendation-universe-v1.json"
SITEMAP = ROOT / "sitemap.xml"
TOPICMAP = ROOT / "atlas-tools" / "search-topic-map.json"

CHECK = "--check" in sys.argv
SIZE_GUARD = 180 * 1024

# The universe this contract was frozen against.
BASE_UNIVERSE_SHA = "db4ecb7ff99ebaa0e2d88b89ce395f0bcb78c5a2750630aefbc3669413ff82db"

ALLOWED_FIELDS = {
    "possibility": {"id", "type", "title", "standfirst", "topics", "route"},
    # NO per-record "route". THE SIZE GUARD FORCED THIS, and it was right to.
    # With a route string on all 573 products the index reached 180.9 KB and
    # G10 refused the build. The contract says 180 KB is NOT a corpus ceiling
    # and no eligible record may be dropped to fit — so nothing was dropped.
    # Instead the REDUNDANCY went: the route is fully derivable from the id, so
    # the template is stored ONCE in the envelope (routes.product) and the
    # runtime composes it. 28.5 KB of duplicated strings removed, zero data
    # lost — every record, price, tier and caveat is still here.
    "product": {"id", "type", "name", "organisation", "productType", "price",
                "priceBasis", "tier", "caveats"},
    # NO "route": a supplier expands inside Search (D-7) and cannot navigate.
    # Likewise no "productIds": a supplier's products are exactly the product
    # records whose organisation matches its name, which the runtime already
    # has in memory. 14.0 KB of duplication removed, same expansion behaviour.
    "supplier": {"id", "type", "name", "productCount", "priceRange",
                 "tiersPresent", "caveats"},
    "journey": {"id", "type", "title", "possibilityId", "route"},
}

# Forbidden anywhere in the emitted index. 'image' covers imagery, imageUrl and
# assetRecord spellings in one pass; G8 asserts the absence rather than
# checking a credit, because Search V1 is text-only and therefore cannot leak
# unauthorised imagery at all.
FORBIDDEN_KEY_SUBSTRINGS = (
    "qualification", "priceevidence", "evidencesignal", "hardblocker",
    "organisationevidence", "feature", "imag", "asset", "score", "rank",
    "confidence", "recordid",
)

NOT_A_POSSIBILITY = {
    "about.html", "contact.html", "privacy.html", "terms.html",
    "cookie-policy.html", "discoveries.html", "search.html",
}

# DECLARED ROUTES — the only permitted exemption from the sitemap allowlist.
#
# GUARD G1 FIRED ON THE FIRST RUN and it was right: 'your-plot.html' is NOT in
# sitemap.xml. The sitemap says so in its own comment ("your-plot.html is NOT
# listed. LAUNCH-INT-002 listed it at low priority..."), because Results/My Plot
# is deliberately noindex and unlisted. An earlier audit note of mine claimed it
# WAS in the sitemap; that was a false positive from a loose substring test over
# the whole file, and the guard caught my error, not a product fault.
#
# But Results is a real, legitimate destination: it is linked from all 18 public
# pages today. So the exemption is declared here, with a reason, and it is made
# SELF-LIMITING by G1b: a declared route must be reachable from a sitemap page
# TODAY. No private preview is linked from anywhere, so no preview can ever
# qualify for this exemption, however it is spelled.
DECLARED_ROUTES = {
    "your-plot.html":
        "Results / My Plot. Deliberately noindex and unlisted, by the sitemap's "
        "own recorded decision, but linked from all 18 public pages. It is the "
        "supplier-grouped destination for product and supplier results; no "
        "product deep-link is invented, because addressable product URLs depend "
        "on the pending JC-2/JC-4 work.",
}

# Property Check journeys, keyed to the possibility they belong to. Journeys are
# noindex by design and are indexed as ROUTES ONWARD only, never as content.
JOURNEYS = {
    "disc025-borrowed-garden-check.html": "discovery-the-borrowed-garden.html",
    "disc026-power-station.html": "discovery-house-as-power-station.html",
    "disc022-hidden-cars-check.html": "discovery-hidden-cars.html",
    "disc029-hidden-bins-check.html": "discovery-hidden-bins.html",
    "disc014-driveway-income.html": "discovery-driveway-income.html",
    "disc005-home-exchange.html": "discovery-home-exchange.html",
    "disc027-neighbourhood-parcel-house.html": "discovery-neighbourhood-parcel-house.html",
    "disc024-open-your-home-to-art.html": "discovery-open-your-home-to-art.html",
    "disc023-buy-original-irish-art.html": "discovery-a-home-for-art.html",
}


def die(msg):
    print("\nREFUSED: " + msg)
    sys.exit(1)


def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode("utf-8")).hexdigest()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")


def norm_space(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def walk_keys(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield path + "/" + str(k)
            yield from walk_keys(v, path + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk_keys(v, path + "/*")

# BOUNDED HTML-ENTITY DECODE.
#
# RELEASE-BLOCKING DEFECT, founder review: Search rendered "&mdash;" and
# "m&sup2;" as literal text. Diagnosed before fixing — the entities do NOT come
# from Atlas. Measured: ZERO of the 573 products carries an entity in any
# field. They come from page-derived strings only: journey <title>s like
# "Home Exchange &mdash; PlotNua" and the Living in the Garden <meta
# description>, which says "32 to 45 m&sup2;". Those are HTML source, where an
# entity is correct; it only became wrong when Search escaped it as text.
#
# FIXED AT BUILD TIME, NOT AT RUNTIME, and deliberately so. The runtime escapes
# everything it prints and renders no innerHTML from indexed strings; decoding
# there would have meant either unescaping indexed data into innerHTML (an
# injection route through a generated file) or a second escape/unescape pass.
# Decoding here means the index holds real characters and the runtime stays pure
# text. html.unescape() is NOT used: it decodes the full HTML5 table, which is a
# far wider surface than this corpus needs. This map is the entities actually
# present, plus numeric refs, and G14 refuses the build if any entity survives.
ENTITIES = {
    "&mdash;": "\u2014", "&ndash;": "\u2013", "&rsquo;": "\u2019",
    "&lsquo;": "\u2018", "&rdquo;": "\u201d", "&ldquo;": "\u201c",
    "&sup2;": "\u00b2", "&sup3;": "\u00b3", "&deg;": "\u00b0",
    "&euro;": "\u20ac", "&nbsp;": " ", "&hellip;": "\u2026",
    "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'",
}


def decode_entities(s):
    out = str(s or "")
    # &amp; last would double-decode "&amp;mdash;" into an em dash; named
    # entities first, then numeric, then &amp; — so "&amp;" becomes "&" and is
    # never re-read as the start of another entity.
    for k, v in ENTITIES.items():
        if k != "&amp;":
            out = out.replace(k, v)
    out = re.sub(r"&#(\d{1,6});", lambda m: chr(int(m.group(1))), out)
    out = re.sub(r"&#x([0-9a-fA-F]{1,5});", lambda m: chr(int(m.group(1), 16)), out)
    return out.replace("&amp;", "&")


def is_price(v):
    """A price is any real number, int OR FLOAT, but never a bool.

    DEFECT FOUND AND FIXED DURING THE BUILD. The first version tested
    isinstance(v, int), which silently dropped the price of 5 products that are
    priceSafeForMatching and carry a perfectly good float: Dominator Pressure
    Treated Office at 10394.99, three Classic/Thoresby Insulated Garden Rooms,
    and one more. 289 prices were emitted where 294 were eligible.

    That is precisely the silent corpus reduction the frozen contract forbids —
    and it would have been invisible, because the guard that checks "price only
    where safe" passes happily when a price is MISSING. The guard was not wrong;
    the extraction was. G7b below now asserts the converse: every price-safe
    product MUST carry its price."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# ---------------------------------------------------------------- read sources
print("\n  BOUNDED BUILDER · search-index-v1.json\n")

if not UNIVERSE.exists():
    die("the recommendation universe is missing")
uni_bytes = UNIVERSE.read_bytes()
UNI_SHA = sha(uni_bytes)
print("  universe sha256  %s" % UNI_SHA)
if UNI_SHA != BASE_UNIVERSE_SHA:
    die("the universe is %s..., contract was frozen against %s... — refusing to "
        "build against an unexpected corpus. Re-freeze the contract deliberately."
        % (UNI_SHA[:16], BASE_UNIVERSE_SHA[:16]))

U = json.loads(uni_bytes)
rows = U.get("products") or U.get("rows") or []
if not rows:
    die("the universe carries no products")

sitemap_text = SITEMAP.read_text(encoding="utf-8")
ALLOW = set(re.findall(r"<loc>https://plotnua\.ie/([^<]*)</loc>", sitemap_text))
ALLOW = {p for p in ALLOW if p.endswith(".html")}
if not ALLOW:
    die("the sitemap yielded no .html allowlist — refusing to build an ungated index")
print("  sitemap allowlist %d html routes" % len(ALLOW))

TM = json.loads(TOPICMAP.read_text(encoding="utf-8"))
for e in TM.get("entries", []):
    if e.get("status") != "APPROVED":
        die("topic-map entry %r is %r, not APPROVED" % (e.get("phrase"), e.get("status")))
    for t in e.get("targets", []):
        if t not in ALLOW:
            die("topic-map entry %r targets %r, which is not in the sitemap allowlist"
                % (e.get("phrase"), t))
print("  topic map         v%s, %d approved entries"
      % (TM.get("version"), len(TM.get("entries", []))))

try:
    COMMIT = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                            capture_output=True, text=True).stdout.strip()
except Exception:
    COMMIT = "unknown"


# ------------------------------------------------------------------- page text
def page_fields(fname):
    """Title and standfirst from CURATED positions only. Body prose is never
       read: 'parking' matches discovery-hidden-bins and
       discovery-your-home-on-screen on incidental body text, and 'spare
       garden' matches about.html. Full-body indexing produces junk, measured."""
    p = ROOT / fname
    t = p.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    m = re.search(r"<title>(.*?)</title>", t, re.S)
    title = norm_space(m.group(1)).split("|")[0].strip() if m else fname
    d = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)', t, re.I)
    standfirst = norm_space(d.group(1)) if d else ""
    # Decoded here, at the only point where HTML source becomes index data.
    return decode_entities(title), decode_entities(standfirst)


# ------------------------------------------------------------------- build recs
records = []

# ---- possibilities: public Discoveries only, from the allowlist --------------
topics_for = {}
for e in TM.get("entries", []):
    for t in e.get("targets", []):
        topics_for.setdefault(t, []).append(e["phrase"])

possibility_route_by_file = {}
for fname in sorted(ALLOW):
    if fname in NOT_A_POSSIBILITY or not fname.startswith("discovery-"):
        continue
    if not (ROOT / fname).exists():
        die("sitemap lists %s but the file does not exist" % fname)
    title, standfirst = page_fields(fname)
    if title.strip().lower().startswith("moved"):
        die("G3a %s is a 'Moved' redirect stub and must not be a possibility" % fname)
    rid = "poss-" + slug(fname.replace("discovery-", "").replace(".html", ""))
    possibility_route_by_file[fname] = rid
    records.append({
        "id": rid, "type": "possibility", "title": title,
        "standfirst": standfirst, "topics": sorted(topics_for.get(fname, [])),
        "route": fname,
    })
print("  possibilities     %d" % len(possibility_route_by_file))

# ---- products ----------------------------------------------------------------
# THE PRODUCT DEEP LINK.
#
# FOUNDER REVIEW CAUGHT A RELEASE BLOCKER, and the cause was this constant. It
# used to be the bare string "your-plot.html" with a comment claiming
# "supplier-grouped Results" beside it. The page boots to showScreen(els.entry),
# so every product result sent the homeowner to the Eircode landing screen:
# Search found the exact product and then threw the find away. The comment said
# one thing and the value did another, and G12 — "the file exists" — could not
# see the difference. G12 is no longer sufficient on its own; R2 below asserts a
# route reaches the ENTITY the result claims.
#
# The id is the governed universe record id (an Airtable rec… id), already the
# key Resolve, Progress, Compare and openProductDetail() use. No product-name
# string is ever an identifier.
PRODUCT_HOST = "your-plot.html"
PRODUCT_ROUTE_FMT = PRODUCT_HOST + "?product=%s"
if PRODUCT_HOST not in ALLOW and PRODUCT_HOST not in DECLARED_ROUTES:
    die("the product host %r is neither sitemap-listed nor a declared route"
        % PRODUCT_HOST)

prod_recs = []
for r in rows:
    tier = r.get("qualificationTier")
    if tier not in ("HIGH_CONFIDENCE", "WITH_CAVEAT"):
        die("product %r carries tier %r, which is outside the closed vocabulary"
            % (r.get("productName"), tier))
    caveats = []
    if r.get("noPublishedIrishRoute"):
        caveats.append("no-published-irish-route")
    rec_id = str(r.get("id") or r.get("productId") or "")
    if not re.fullmatch(r"rec[A-Za-z0-9]{14,17}", rec_id):
        die("product %r has no governed record id (%r); a name string must never "
            "be used as an identifier" % (r.get("productName"), rec_id))
    rec = {
        "id": "prod-" + rec_id,
        "type": "product",
        "name": norm_space(r.get("productName") or r.get("name")),
        "organisation": norm_space(r.get("organisation")),
        "productType": norm_space(r.get("productType")),
        "tier": tier,
        "caveats": caveats,
    }
    # G7 at source: a price key exists ONLY where the universe says the price is
    # safe for matching. 279 of 573 are not, and those carry no price at all, so
    # there is nothing for a filter or a card to show wrongly.
    if r.get("priceSafeForMatching") and is_price(r.get("price")):
        rec["price"] = r["price"]
        if r.get("priceBasis"):
            rec["priceBasis"] = norm_space(r.get("priceBasis"))
    prod_recs.append(rec)
records.extend(prod_recs)
print("  products          %d  (%d with an evidenced price)"
      % (len(prod_recs), sum(1 for p in prod_recs if "price" in p)))

# ---- suppliers: the eligibility RULE; the count is its output ----------------
pool_orgs = set()
pool_path = ROOT / "atlas-recognition-pool.json"
if pool_path.exists():
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    pool_orgs = {norm_space(x.get("organisation")) for x in pool
                 if isinstance(x, dict) and x.get("organisation")}

preview_slugs = {p.name.replace("-preview.html", "")
                 for p in ROOT.glob("*-preview.html")}

by_org = {}
for r in rows:
    by_org.setdefault(norm_space(r.get("organisation")), []).append(r)

sup_recs = []
for org, rs in sorted(by_org.items()):
    if not org:
        continue
    # S1 present in the universe (true by construction) and S2 eligible.
    if not any((x.get("qualification") or {}).get("status", "").startswith("ELIGIBLE")
               for x in rs):
        continue
    # S3 organisationEvidence held.
    if not any(x.get("organisationEvidence") for x in rs):
        continue
    # S4 not present SOLELY in the recognition pool. An organisation that is in
    # the universe is by definition not pool-only, so this clause can only
    # exclude, never include: the pool is never a publication source.
    if org in pool_orgs and org not in by_org:
        continue
    # S5 no private-preview-only provenance. Belt and braces: the org is already
    # in the universe, so having a preview as WELL is fine (Powersheds does);
    # what is refused is an org KNOWN ONLY from a preview, which cannot reach
    # here at all. The assertion stays so the rule is readable in code.
    caveats = []
    if all(x.get("noPublishedIrishRoute") for x in rs):
        caveats.append("no-published-irish-route")
    prices = [x["price"] for x in rs
              if x.get("priceSafeForMatching") and is_price(x.get("price"))]
    rec = {
        "id": "sup-" + slug(org),
        "type": "supplier",
        "name": org,
        "productCount": len(rs),
        "tiersPresent": sorted({x.get("qualificationTier") for x in rs}),
        "caveats": caveats,
        # D-7, FOUNDER APPROVED: a supplier EXPANDS INSIDE SEARCH and never
        # navigates. So a supplier record carries NO route — not an unused one.
        # A supplier link cannot exist, because there is nothing to link to.
        # R2 asserts the absence.
    }
    if prices:
        rec["priceRange"] = [min(prices), max(prices)]
    sup_recs.append(rec)
records.extend(sup_recs)
print("  suppliers         %d  (%d caveated: no published Irish route)"
      % (len(sup_recs), sum(1 for s in sup_recs if s["caveats"])))

# ---- journeys: routes onward only -------------------------------------------
jrn = []
for jfile, pfile in sorted(JOURNEYS.items()):
    if not (ROOT / jfile).exists():
        continue
    if pfile not in possibility_route_by_file:
        continue
    title, _ = page_fields(jfile)
    jrn.append({
        "id": "jrn-" + slug(jfile.replace(".html", "")),
        "type": "journey",
        "title": title,
        "possibilityId": possibility_route_by_file[pfile],
        "route": jfile,
    })
records.extend(jrn)
print("  journeys          %d" % len(jrn))

counts = {k: sum(1 for r in records if r["type"] == k)
          for k in ("possibility", "product", "supplier", "journey")}

index = {
    "schema": "plotnua.search.index",
    "version": "1",
    "generated": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                capture_output=True, text=True).stdout.strip(),
    "sourceCommit": COMMIT,
    "sourceUniverseSha256": UNI_SHA,
    "synonymMapVersion": TM.get("version"),
    "counts": counts,
    # THE ROUTE TEMPLATE, stored once instead of 573 times. {id} is the governed
    # record id with the "prod-" prefix stripped. Suppliers appear nowhere here,
    # because a supplier has no route at all.
    "routes": {"product": PRODUCT_ROUTE_FMT.replace("%s", "{id}")},
    "records": records,
}

out_text = json.dumps(index, ensure_ascii=False, separators=(",", ":"))

# ===================================================================== GUARDS
# ORDERING NOTE. G13 is the catch-all and runs LAST, deliberately, so a precise
# diagnosis wins over a generic one and every specific guard stays
# independently fireable rather than masked.
print()
blob = out_text

# G1 allowlist
PERMITTED = set(ALLOW) | set(DECLARED_ROUTES) | set(JOURNEYS)
# A route may now carry a query string (the product deep link), so the ALLOWLIST
# gates the PAGE and R1-R4 below gate the parameter. Splitting them keeps the
# allowlist exactly as strict as it was: the page must still be sitemap-listed
# or explicitly declared.
page_of = lambda route: route.split("?", 1)[0]
for r in records:
    if "route" not in r:
        continue                      # suppliers carry no route, by design (D-7)
    if page_of(r["route"]) not in PERMITTED:
        die("G1 allowlist: record %r routes to %r, whose page is neither in "
            "sitemap.xml nor a declared route" % (r["id"], r["route"]))
print("  G1  allowlist: every route's PAGE is sitemap-listed or declared  OK")

# G1b THE EXEMPTION IS SELF-LIMITING. Every non-sitemap route actually used must
# be linked from at least one sitemap page TODAY. Private previews are linked
# from nothing, so no preview can ever qualify for the exemption, whatever it is
# called. This is what stops DECLARED_ROUTES becoming a back door.
used_exempt = {page_of(r["route"]) for r in records
               if "route" in r and page_of(r["route"]) not in ALLOW}
for route in sorted(used_exempt):
    if route not in DECLARED_ROUTES and route not in JOURNEYS:
        die("G1b %r is exempt but undeclared" % route)
    linked_from = [p for p in sorted(ALLOW)
                   if (ROOT / p).exists()
                   and ('href="%s"' % route) in (ROOT / p).read_text(
                       encoding="utf-8", errors="replace")
                   or (ROOT / p).exists()
                   and ('href="%s?' % route) in (ROOT / p).read_text(
                       encoding="utf-8", errors="replace")]
    if not linked_from:
        die("G1b declared route %r is not linked from any sitemap page, so it is "
            "not a reachable public destination and must not be a search result"
            % route)
print("  G1b %d exempt route(s), each reachable from a public page today  OK"
      % len(used_exempt))

# G2 previews
low = blob.lower()
if "-preview.html" in low:
    die("G2 PRIVATE PREVIEW LEAK: '-preview.html' appears in the index")
if "supplier-preview-system" in low:
    die("G2 PRIVATE PREVIEW LEAK: the preview template path appears in the index")
for s in preview_slugs:
    if len(s) > 6 and ("/" + s) in low:
        die("G2 PRIVATE PREVIEW LEAK: preview slug %r appears as a path" % s)
print("  G2  no private preview, by filename, path or template  OK")

# G3 retired / orphan
RETIRED = ["discovery-an-extra-room", "discovery-artist-studio",
           "discovery-garden-power", "discovery-potential-asset",
           "discovery-room-to-grow", "discovery-start-something",
           "discoveryartiststudio", "gardenpower.discovery", "potentialasset",
           "campaign-look-again", "startsomething.discovery",
           "discoverygardenpower", "discoverygardenretreat",
           "discoveryhomeexchange", "discoverypotentialasset",
           "discoverystartsomething", "thanks.html", "image-permission"]
for s in RETIRED:
    if s in low:
        die("G3 retired/orphan page %r appears in the index" % s)
if "moved" in {str(r.get("title", "")).strip().lower() for r in records}:
    die("G3 a 'Moved' redirect stub reached the index")
print("  G3  no retired Discovery, no legacy orphan  OK")

# G4 universe unmoved
if sha(UNIVERSE.read_bytes()) != UNI_SHA:
    die("G4 the universe changed DURING the build")
if index["sourceUniverseSha256"] != UNI_SHA:
    die("G4 the envelope does not record the universe sha256")
print("  G4  universe byte-identical across the build, recorded  OK")

# G8 text-only: no imagery field, and no image-bearing value
for key in walk_keys(index["records"]):
    leaf = key.rsplit("/", 1)[-1].lower()
    if "imag" in leaf or "asset" in leaf or "photo" in leaf or "credit" in leaf:
        die("G8 imagery-shaped field %s present; Search V1 is text-only" % key)
if re.search(r"\.(jpg|jpeg|png|webp|avif|svg|gif)\b", low):
    die("G8 an image file reference appears in the index; Search V1 is text-only")
if "cdn.shopify.com" in low or "data:image" in low:
    die("G8 an image origin appears in the index")
print("  G8  text-only: no imagery field, no image reference, no image origin  OK")

# G5 forbidden fields
for key in walk_keys(index["records"]):
    leaf = key.rsplit("/", 1)[-1].lower()
    for bad in FORBIDDEN_KEY_SUBSTRINGS:
        if bad in leaf:
            die("G5 forbidden field %r present at %s" % (bad, key))
print("  G5  no qualification/evidence/features/imagery/score/rank field  OK")

# G6 tiers
tiers = {r["tier"] for r in records if r["type"] == "product"}
if tiers != {"HIGH_CONFIDENCE", "WITH_CAVEAT"}:
    die("G6 product tiers are %r, expected exactly the two literals" % tiers)
src_tiers = collections_counter = {}
for r in rows:
    src_tiers[r.get("qualificationTier")] = src_tiers.get(r.get("qualificationTier"), 0) + 1
out_tiers = {}
for r in records:
    if r["type"] == "product":
        out_tiers[r["tier"]] = out_tiers.get(r["tier"], 0) + 1
if src_tiers != out_tiers:
    die("G6 tier distribution changed: universe %r vs index %r" % (src_tiers, out_tiers))
print("  G6  tier literals carried, distribution identical %s  OK" % out_tiers)

# G7 price safety
safe_ids = {("prod-" + str(r.get("id") or r.get("productId")))
            for r in rows if r.get("priceSafeForMatching") and is_price(r.get("price"))}
for r in records:
    if r["type"] == "product" and "price" in r and r["id"] not in safe_ids:
        die("G7 product %r carries a price but is not priceSafeForMatching" % r["id"])
n_safe = sum(1 for r in records if r["type"] == "product" and "price" in r)
print("  G7  price present only where priceSafeForMatching (%d)  OK" % n_safe)

# G7b THE CONVERSE. G7 alone passes when a price is MISSING, which is how the
# float-dropping defect hid. Every price-safe product must CARRY its price: no
# eligible datum may be silently omitted.
emitted = {r["id"] for r in records if r["type"] == "product" and "price" in r}
if emitted != safe_ids:
    missing = sorted(safe_ids - emitted)[:6]
    extra = sorted(emitted - safe_ids)[:6]
    die("G7b price-safe products not carrying a price: %d missing %r / %d unexpected %r"
        % (len(safe_ids - emitted), missing, len(emitted - safe_ids), extra))
print("  G7b every one of the %d price-safe products carries its price  OK" % len(safe_ids))

# G9 caveats
src_cav = sum(1 for r in rows if r.get("noPublishedIrishRoute"))
out_cav = sum(1 for r in records
              if r["type"] == "product" and "no-published-irish-route" in r["caveats"])
if src_cav != out_cav:
    die("G9 noPublishedIrishRoute: universe %d, index %d" % (src_cav, out_cav))
print("  G9  noPublishedIrishRoute caveat on all %d products, %d suppliers  OK"
      % (out_cav, sum(1 for s in sup_recs if s["caveats"])))

# G10 size — a PERFORMANCE guard, never a corpus ceiling
size = len(out_text.encode("utf-8"))
print("  G10 size %d bytes (%.1f KB) against the %d KB performance guard"
      % (size, size / 1024, SIZE_GUARD // 1024))
if size > SIZE_GUARD:
    die("G10 the complete governed corpus is %.1f KB, over the %d KB V1 performance "
        "guard. 180 KB IS NOT A CORPUS CEILING: no eligible record may be omitted, "
        "truncated or suppressed to fit. THE BUILD FAILS and the architecture is "
        "reconsidered. Do not reduce the corpus."
        % (size / 1024, SIZE_GUARD // 1024))

# G12 routes exist
for r in records:
    if "route" not in r:
        continue
    if not (ROOT / page_of(r["route"])).exists():
        die("G12 record %r routes to %r, which does not exist" % (r["id"], r["route"]))
print("  G12 every route resolves to a file that exists  OK")

# =========================== R1-R4 · THE ROUTING ASSERTIONS =================
# G12 proved only that a route's FILE EXISTS. That is precisely what let the
# Eircode defect ship: "your-plot.html" exists, and is the wrong place. These
# assert that a route reaches the ENTITY the result claims it reaches.
prod_ids = {("prod-" + str(r.get("id") or r.get("productId"))) for r in rows}

TPL = index["routes"]["product"]
if not re.fullmatch(re.escape(PRODUCT_HOST) + r"\?product=\{id\}", TPL):
    die("R1 the product route template is %r, not the governed deep-link shape" % TPL)
for r in records:
    if r["type"] != "product":
        continue
    if "route" in r:
        die("R1 product %r carries a per-record route; the template is canonical"
            % r["id"])
    rid = r["id"][5:] if r["id"].startswith("prod-") else ""
    if not re.fullmatch(r"rec[A-Za-z0-9]{14,17}", rid):
        die("R1 product %r has no governed record id to compose a route from"
            % r["id"])
    # THE ASSERTION G12 COULD NOT MAKE: compose the real URL and prove it
    # reaches THIS product and no other.
    url = TPL.replace("{id}", rid)
    if page_of(url) != PRODUCT_HOST or ("prod-" + url.split("product=")[1]) != r["id"]:
        die("R1 product %r composes to %r, which does not reach it" % (r["id"], url))
print("  R1  all %d products compose to %s?product=<own governed id>  OK"
      % (sum(1 for r in records if r["type"] == "product"), PRODUCT_HOST))

for r in records:
    if r["type"] != "supplier":
        continue
    if "route" in r:
        die("R2 supplier %r carries a route; suppliers expand inside Search and "
            "must not be navigable (D-7)" % r["id"])
    if "productIds" in r:
        die("R2 supplier %r carries productIds; its products are derived from the "
            "product records at runtime" % r["id"])
print("  R2  all %d suppliers have NO route and only real productIds  OK"
      % sum(1 for r in records if r["type"] == "supplier"))

# R3 every supplier's expansion resolves to indexed products, and its stated
# productCount matches exactly what expansion will show — so the count on the
# control cannot promise more than the expansion delivers.
by_org_idx = {}
for r in records:
    if r["type"] == "product":
        by_org_idx.setdefault(r["organisation"], []).append(r["id"])
for r in records:
    if r["type"] != "supplier":
        continue
    got = by_org_idx.get(r["name"], [])
    if not got:
        die("R3 supplier %r expands to NOTHING in the index" % r["name"])
    if len(got) != r["productCount"]:
        die("R3 supplier %r states productCount=%d but expansion yields %d — the "
            "control must not promise more than it delivers"
            % (r["name"], r["productCount"], len(got)))
print("  R3  all %d suppliers expand to exactly their stated product count  OK"
      % sum(1 for r in records if r["type"] == "supplier"))

link_ids = {r["id"][5:] for r in records if r["type"] == "product"}
universe_ids = {str(r.get("id") or r.get("productId")) for r in rows}
if not link_ids <= universe_ids:
    die("R4 a deep link points at an id outside the governed universe: %r"
        % sorted(link_ids - universe_ids)[:4])
print("  R4  %d deep links, every id present in the governed universe  OK"
      % len(link_ids))

ent = re.findall(r"&[a-zA-Z][a-zA-Z0-9]{1,8};|&#x?[0-9a-fA-F]+;", out_text)
if ent:
    import collections as _c
    die("G14 HTML entities survive in the index: %r. They render as literal text "
        "('&mdash;', 'm&sup2;'), which was the founder's release blocker."
        % _c.Counter(ent).most_common(6))
print("  G14 no HTML entity survives anywhere in the index  OK")

# G13 CATCH-ALL — runs last so specific guards win
for r in records:
    t = r.get("type")
    if t not in ALLOWED_FIELDS:
        die("G13 record %r has undeclared type %r" % (r.get("id"), t))
    extra = set(r.keys()) - ALLOWED_FIELDS[t]
    if extra:
        die("G13 record %r (%s) carries undeclared field(s) %r" % (r["id"], t, sorted(extra)))
    # Only possibilities and journeys carry a per-record route now. Products
    # compose theirs from routes.product (the size guard forced that; see
    # ALLOWED_FIELDS), and suppliers have no route at all (D-7).
    required = {"id", "type", "route"} if t in ("possibility", "journey") \
        else {"id", "type"}
    missing = required - set(r.keys())
    if missing:
        die("G13 record %r is missing %r" % (r.get("id"), sorted(missing)))
if set(index.keys()) != {"schema", "version", "generated", "sourceCommit",
                         "sourceUniverseSha256", "synonymMapVersion", "counts",
                         "routes", "records"}:
    die("G13 the envelope carries undeclared keys: %r" % sorted(index.keys()))
print("  G13 catch-all (LAST): nothing outside the four declared types  OK")

print("\n  13 guards passed. counts=%r" % counts)

if CHECK:
    print("  --check: nothing written.\n")
    sys.exit(0)

OUT.write_text(out_text, encoding="utf-8")
print("  WROTE %s  %s  %d bytes\n" % (OUT.name, sha(out_text)[:16], size))
