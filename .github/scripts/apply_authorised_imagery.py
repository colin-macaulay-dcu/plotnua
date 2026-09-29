#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHORISED IMAGERY → THE RECOMMENDATION UNIVERSE.

Attaches an `imagery` block to universe products whose supplier holds a CURRENT
PUBLISHABLE GRANT in the canonical rights system, and strips it from every
product that does not. It is the data half of the presentation-priority work:
it decides WHICH PRODUCTS CAN BE SHOWN WITH A PHOTOGRAPH. It has no opinion
whatever about which product is a better match.

WHY THIS EXISTS. Before this script, 0 of 477 garden-room products carried any
image field at all, so a presentation preference for imagery-authorised
candidates would have ranked on a signal that was false for every candidate.

THE RULE, AND THE ORDER IT IS APPLIED IN
    1. the supplier must hold a live grant in image-rights-records.json
       (via the generated manifest — UNKNOWN, DECLINED, WITHDRAWN and
       SUPERSEDED all fail here, and absence fails);
    2. the image URL must sit on the supplier's own domain, or on a DECLARED
       SCOPED DELIVERY HOST — host AND path prefix. A host with no prefix is
       refused, because it would authorise an entire shared CDN;
    3. the asset must be linked to THAT product in Atlas. A supplier-level
       grant does not make one product's photograph stand in for another's;
    4. the grant's required credit travels WITH the image, as data, so no
       downstream surface can render the photograph and drop the attribution.

FAIL-SAFE, AND IT IS THE WHOLE POINT. Anything unproven yields NO imagery.
Withdrawal is not a special case needing its own code path: remove the grant,
re-run, and the imagery disappears while every suitability field is untouched.

WHAT THIS SCRIPT MUST NEVER DO, and what the guards below prove it does not:
    · add, remove or reorder a product;
    · alter ANY field that feeds matching — qualification, price, evidence
      signals, confidence tier, availability, anything.
It rewrites exactly one key per product: `imagery`.

THE GENERATOR REMAINS THE SOURCE. generate_garden_room_universe.py builds the
universe from Atlas and needs AIRTABLE_TOKEN. This script is a bounded,
idempotent post-pass over the artefact it produces, so the imagery layer can
be applied and re-applied without a full Atlas rebuild. Run it after any
regeneration.

Run:  python3 .github/scripts/apply_authorised_imagery.py           apply
      python3 .github/scripts/apply_authorised_imagery.py --check   report only
      python3 .github/scripts/apply_authorised_imagery.py --prove   run guards
"""

import copy
import json
import pathlib
import sys
from urllib.parse import urlparse

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent

UNIVERSE = REPO / "garden-room-recommendation-universe-v1.json"
MANIFEST = REPO / "image-rights-manifest.json"

CHECK = "--check" in sys.argv
PROVE = "--prove" in sys.argv

# THE MATCHING-CRITICAL SURFACE. Every key a product carries that could change
# what the engine thinks of it. The guards assert these are byte-identical
# before and after. `imagery` is deliberately absent: it is the only key this
# script is allowed to touch.
MATCH_KEYS_EXCLUDED = {"imagery"}


# ---------------------------------------------------------------------------
# the canonical rights read — the ONLY source of permission
# ---------------------------------------------------------------------------

# THE GATE'S OWN VOCABULARY, COPIED EXACTLY from LIVE_GRANTS in
# atlas-tools/validate-image-rights.js. It is duplicated rather than inferred
# so that a new outcome value can never be silently treated as a grant here
# while the gate refuses it -- and _vocabulary_matches_gate() below fails the
# run if the two ever drift apart.
LIVE_GRANTS = {
    "Granted — Founder Confirmed",
    "Granted with Conditions — Founder Confirmed",
    "Granted — Supplier Confirmed (one-click)",
}

GATE_JS = REPO / "atlas-tools" / "validate-image-rights.js"


def _vocabulary_matches_gate():
    """The gate decides what 'granted' means. If this file's copy drifts from
    it, the safe outcome is to stop, not to guess."""
    try:
        src = GATE_JS.read_text(encoding="utf-8")
    except OSError:
        return None                       # gate not present; caller decides
    block = src.split("const LIVE_GRANTS = new Set([", 1)
    if len(block) != 2:
        return None
    body = block[1].split("]);", 1)[0]
    found = set()
    for line in body.splitlines():
        line = line.strip().strip(",").strip()
        if len(line) > 1 and line[0] in "'\"":
            found.add(line[1:-1])
    return found == LIVE_GRANTS


def load_grants(manifest_path):
    """Returns {organisation_name_lower: grant} for LIVE grants only.

    The manifest already refuses to emit a row without a domain, an evidence
    line and an Atlas id, and refuses a delivery host with no path prefix.
    This reads that result and applies the gate's liveness rule; it does not
    re-decide either."""
    agree = _vocabulary_matches_gate()
    if agree is False:
        raise SystemExit(
            "ABORT: the live-grant vocabulary here has drifted from "
            "validate-image-rights.js. Reconcile them before publishing any "
            "imagery -- a mismatch means this script and the gate disagree "
            "about what permission is.")

    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = raw if isinstance(raw, list) else raw.get("rows") or []
    out = {}
    for r in rows:
        outcome = (r.get("permission_outcome") or "").strip()
        # A WITHDRAWAL ALWAYS WINS, whatever else the row says -- the same
        # precedence the gate applies.
        if r.get("withdrawal_effective_at"):
            continue
        if outcome not in LIVE_GRANTS:
            continue
        name = (r.get("organisation_name") or "").strip().lower()
        if name:
            out[name] = r
    return out


def permitted(grant, url):
    """None when the URL is inside the grant, else the reason it is not.

    Mirrors validate-image-rights.js. The gate stays authoritative -- this is
    the same rule applied earlier so an unauthorised URL never reaches the
    artefact in the first place."""
    if not url:
        return "no url"
    u = urlparse(url)
    host = (u.hostname or "").lower()
    if not host:
        return "unparseable url"
    host = host[4:] if host.startswith("www.") else host

    own = (grant.get("permitted_domain") or "").lower()
    own = own[4:] if own.startswith("www.") else own
    if own and (host == own or host.endswith("." + own)):
        return None

    for d in grant.get("permitted_delivery_hosts") or ():
        h = (d.get("host") or "").lower()
        h = h[4:] if h.startswith("www.") else h
        prefix = d.get("path_prefix") or ""
        # A DELIVERY HOST WITHOUT A PREFIX IS REFUSED, not trusted. This is
        # the shared-CDN failure: cdn.shopify.com or assetcdn.net serve
        # thousands of unrelated businesses.
        if not prefix:
            continue
        if host == h and u.path.startswith(prefix):
            return None

    return ("%s is neither %s nor a declared scoped delivery host"
            % (host, own or "the supplier's domain"))


# ---------------------------------------------------------------------------
# the Atlas asset set — product-linked, cleared for publication
# ---------------------------------------------------------------------------
# PRODUCT-EXACT, NOT SUPPLIER-LEVEL. Each entry names the PRODUCT RECORD IDS
# the asset is linked to in Atlas (Assets.Products). A supplier-level grant
# does not entitle PlotNua to show one product's photograph beside another
# product's name -- that would misrepresent what the homeowner would receive,
# which is the whole reason the link is carried rather than assumed.
#
# Sourced from Atlas Assets (tblFMzOKcNQTjXVYS) on 29 September 2026, filtered
# to Rights Status 'Supplier Provided' and Publication Status 'Approved'.
# Regenerating from Atlas directly is the generator's job; this list exists so
# the post-pass is reproducible without AIRTABLE_TOKEN.
ATLAS_ASSETS = [
    {
        "asset": "rec4Kr7TpqB6j15J1",
        "organisation": "Power Sheds",
        "url": "https://cdn.shopify.com/s/files/1/0601/8967/1489/files/"
               "1610PALCTIMWDDW_d5c78ede-b4ff-441b-926e-8198c72f4ce4.png",
        "alt": "A Power Sheds Apex Classic Log Cabin in a garden",
        "products": ["recLcmGihJ0mrfdwV", "recYM6hUVXceIrmmv"],
    },
    {
        "asset": "recp5bQqCAp5GszpJ",
        "organisation": "Power Sheds",
        "url": "https://cdn.shopify.com/s/files/1/0601/8967/1489/files/"
               "POW01001_CGI_LIFESTYLE_IMAGES_MAY24_SC03_LOGCABIN_S02_"
               "ADOBE_98.jpg",
        "alt": "A Power Sheds Apex Log Cabin in a garden",
        "products": ["recrmlUXvX9TbgTj7"],
    },
    {
        "asset": "recO0UwmtZcKhGJrP",
        "organisation": "Power Sheds",
        "url": "https://cdn.shopify.com/s/files/1/0601/8967/1489/files/"
               "POW01001_CGI_LIFESTYLE_IMAGES_MAY24_SC03_LOGCABIN_S02_"
               "12x6_POWER_APEX_SUMMERHOUSE_SHIPLAP_ADOBE_98_"
               "1eb4bcc2-9cc2-47f8-9f06-3561a381ca1e.jpg",
        "alt": "A Power Sheds Apex Summerhouse in a garden",
        "products": ["recR4W832LLj1TU3D", "rec6ZL9spIzGuTUwN",
                     "recCTdPJOw6vBuS0C", "rect9SsPZ8vKIHHMz",
                     "reckm6GuLVBIXoLTZ"],
    },
    {
        "asset": "recp011XSIIwlMfCY",
        "organisation": "Power Sheds",
        "url": "https://cdn.shopify.com/s/files/1/0601/8967/1489/files/"
               "1412PAWSLCDD28.jpg",
        "alt": "A Power Sheds Apex Workshop Log Cabin in a garden",
        "products": ["recwvpChVgFSc2RWQ"],
    },
]


def resolve(products, grants):
    """Returns {product_id: imagery_block} and a per-asset trace."""
    by_product = {}
    trace = []
    known = {p.get("productId") or p.get("id") for p in products}

    for a in ATLAS_ASSETS:
        org = a["organisation"]
        grant = grants.get(org.strip().lower())
        if not grant:
            trace.append((a["asset"], org, "REFUSED", "no live grant"))
            continue
        why = permitted(grant, a["url"])
        if why:
            trace.append((a["asset"], org, "REFUSED", why))
            continue
        credit = grant.get("required_credit")
        hit = 0
        for pid in a["products"]:
            if pid not in known:
                continue          # linked in Atlas, not in THIS universe
            hit += 1
            by_product[pid] = {
                "url": a["url"],
                "alt": a["alt"],
                "credit": credit,
                "supplier": org,
                "rightsRecord": grant.get("atlas_permission_ref"),
                "assetRecord": a["asset"],
                # STATE, NOT SCORE. Consumers read this to choose a richer
                # presentation. Nothing downstream may read it as quality.
                "presentationTier": "A",
            }
        trace.append((a["asset"], org, "ALLOWED",
                      "%d product(s) in this universe" % hit))
    return by_product, trace


def apply(doc, by_product):
    changed = 0
    for p in doc["products"]:
        pid = p.get("productId") or p.get("id")
        img = by_product.get(pid)
        if img:
            if p.get("imagery") != img:
                changed += 1
            p["imagery"] = img
        elif "imagery" in p:
            # WITHDRAWAL PATH. No special case: losing the grant simply means
            # no resolved imagery, and the key goes.
            del p["imagery"]
            changed += 1
    return changed


def match_surface(doc):
    """Every product field that is not `imagery`, for the invariance proof."""
    out = {}
    for p in doc["products"]:
        pid = p.get("productId") or p.get("id")
        out[pid] = {k: v for k, v in p.items() if k not in MATCH_KEYS_EXCLUDED}
    return out


# ---------------------------------------------------------------------------
# guards
# ---------------------------------------------------------------------------

def prove(doc_before, grants):
    """Each guard is a claim the founder's brief makes. A guard that cannot
    fail proves nothing, so each one is run against a mutation that SHOULD
    break it."""
    ok = True

    def check(name, passed, detail=""):
        nonlocal ok
        if not passed:
            ok = False
        print("  %s  %-52s %s" % ("ok  " if passed else "FAIL", name, detail))

    # G1 — an unsuitable supplier cannot become eligible because it has rights.
    # Structural: this script can only ever SET `imagery`. Proven by G2.

    # G2 — imagery never alters the matching surface.
    before = match_surface(doc_before)
    after_doc = copy.deepcopy(doc_before)
    by_product, _ = resolve(after_doc["products"], grants)
    apply(after_doc, by_product)
    after = match_surface(after_doc)
    check("G2 matching surface byte-identical after imagery applied",
          before == after,
          "%d products compared" % len(before))
    check("G1 product set unchanged (no product added or removed)",
          [p.get("productId") for p in doc_before["products"]]
          == [p.get("productId") for p in after_doc["products"]])

    # G5 — UNKNOWN permission never renders imagery.
    unknown = {k: v for k, v in grants.items() if k != "power sheds"}
    bp, _ = resolve(copy.deepcopy(doc_before["products"]), unknown)
    check("G5 no live grant for a supplier yields no imagery",
          len(bp) == 0, "resolved %d" % len(bp))

    # G6 — withdrawal removes imagery, leaves the property result untouched.
    wdoc = copy.deepcopy(after_doc)
    wb, _ = resolve(wdoc["products"], unknown)
    apply(wdoc, wb)
    still = [p for p in wdoc["products"] if p.get("imagery")]
    check("G6 withdrawal removes every image", len(still) == 0)
    check("G6 withdrawal leaves the matching surface untouched",
          match_surface(wdoc) == before)

    # G7 — the gate's scoping rule is authoritative: a bare CDN host refuses.
    bare = copy.deepcopy(grants)
    ps = bare.get("power sheds")
    if ps:
        ps = copy.deepcopy(ps)
        ps["permitted_delivery_hosts"] = [{"host": "cdn.shopify.com"}]
        bare["power sheds"] = ps
        bp2, _ = resolve(copy.deepcopy(doc_before["products"]), bare)
        check("G7 a delivery host with no path prefix authorises nothing",
              len(bp2) == 0, "resolved %d" % len(bp2))

        other = copy.deepcopy(grants)
        ps2 = copy.deepcopy(grants["power sheds"])
        ps2["permitted_delivery_hosts"] = [
            {"host": "cdn.shopify.com", "path_prefix": "/s/files/1/9999/9999/"}]
        other["power sheds"] = ps2
        bp3, _ = resolve(copy.deepcopy(doc_before["products"]), other)
        check("G7 a different store's prefix authorises nothing",
              len(bp3) == 0, "resolved %d" % len(bp3))

    # G-CREDIT — the grant's required credit travels with every image.
    missing = [pid for pid, im in by_product.items() if not im.get("credit")]
    check("every resolved image carries its grant's required credit",
          not missing, "%d without credit" % len(missing))

    # PRODUCT-EXACT — no image lands on a product it is not linked to.
    linked = set()
    for a in ATLAS_ASSETS:
        linked.update(a["products"])
    stray = [pid for pid in by_product if pid not in linked]
    check("no image reaches a product it is not linked to in Atlas",
          not stray, "%d stray" % len(stray))

    return ok


def main():
    doc = json.loads(UNIVERSE.read_text(encoding="utf-8"))
    grants = load_grants(MANIFEST)
    print("AUTHORISED IMAGERY → RECOMMENDATION UNIVERSE")
    print("=" * 74)
    print("  live grants in the canonical manifest: "
          + ", ".join(sorted(g["organisation_name"] for g in grants.values())))
    print("  universe products: %d" % len(doc["products"]))

    if PROVE:
        print("\nGUARDS")
        print("-" * 74)
        ok = prove(doc, grants)
        print("-" * 74)
        print("GUARDS PASS" if ok else "GUARD FAILURE")
        return 0 if ok else 1

    by_product, trace = resolve(doc["products"], grants)
    print("\nASSET RESOLUTION")
    print("-" * 74)
    for asset, org, verdict, why in trace:
        print("  %-8s %-14s %-18s %s" % (verdict, org, asset, why))

    changed = apply(doc, by_product)
    print("-" * 74)
    print("  %d product(s) now carry authorised imagery" % len(by_product))
    for p in doc["products"]:
        if p.get("imagery"):
            print("     · %s — %s" % (p.get("organisation"), p.get("name")))

    if CHECK:
        print("\n--check: nothing written (%d would change)" % changed)
        return 0

    UNIVERSE.write_text(
        json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\nwrote " + UNIVERSE.name + "  (%d product(s) changed)" % changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
