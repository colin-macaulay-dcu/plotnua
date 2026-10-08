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

# IMG-REFRESH — the artefact this run acts on.
#
# Default: the committed universe, exactly as every hand-run invocation has
# always used. `--universe PATH` points it at a generated candidate instead,
# so the Atlas refresh workflow can reapply imagery to the candidate BEFORE it
# is validated, rather than publishing a universe with no imagery at all.
#
# This changes WHICH FILE is read and written. It does not change the rule:
# grants still come from the canonical manifest, assets still come from
# ATLAS_ASSETS, and an unproven image still yields nothing.
if "--universe" in sys.argv:
    UNIVERSE = pathlib.Path(sys.argv[sys.argv.index("--universe") + 1]).resolve()

# A FLOOR, NOT AN EQUALITY. Rights growing is fine and must not fail a run.
# Rights shrinking is a deliberate act that should lower this number by hand,
# so a silent collapse -- the defect this whole pass exists to close -- cannot
# reach validation, let alone publication.
REQUIRE_MIN = 0
if "--require-min" in sys.argv:
    REQUIRE_MIN = int(sys.argv[sys.argv.index("--require-min") + 1])
MANIFEST = REPO / "image-rights-manifest.json"

CHECK = "--check" in sys.argv
PROVE = "--prove" in sys.argv

# THE MATCHING-CRITICAL SURFACE. Every key a product carries that could change
# what the engine thinks of it. The guards assert these are byte-identical
# before and after. `imagery` is deliberately absent: it is the only key this
# script is allowed to touch.
MATCH_KEYS_EXCLUDED = {"imagery", "imagerySet"}


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
        "organisation": "Powersheds",
        "url": "https://cdn.shopify.com/s/files/1/0601/8967/1489/files/"
               "1610PALCTIMWDDW_d5c78ede-b4ff-441b-926e-8198c72f4ce4.png",
        "alt": "A Powersheds Apex Classic Log Cabin in a garden",
        "products": ["recLcmGihJ0mrfdwV", "recYM6hUVXceIrmmv"],
    },
    {
        "asset": "recp5bQqCAp5GszpJ",
        "organisation": "Powersheds",
        "url": "https://cdn.shopify.com/s/files/1/0601/8967/1489/files/"
               "POW01001_CGI_LIFESTYLE_IMAGES_MAY24_SC03_LOGCABIN_S02_"
               "ADOBE_98.jpg",
        "alt": "A Powersheds Apex Log Cabin in a garden",
        "products": ["recrmlUXvX9TbgTj7"],
    },
    {
        "asset": "recO0UwmtZcKhGJrP",
        "organisation": "Powersheds",
        "url": "https://cdn.shopify.com/s/files/1/0601/8967/1489/files/"
               "POW01001_CGI_LIFESTYLE_IMAGES_MAY24_SC03_LOGCABIN_S02_"
               "12x6_POWER_APEX_SUMMERHOUSE_SHIPLAP_ADOBE_98_"
               "1eb4bcc2-9cc2-47f8-9f06-3561a381ca1e.jpg",
        "alt": "A Powersheds Apex Summerhouse in a garden",
        "products": ["recR4W832LLj1TU3D", "rec6ZL9spIzGuTUwN",
                     "recCTdPJOw6vBuS0C", "rect9SsPZ8vKIHHMz",
                     "reckm6GuLVBIXoLTZ"],
    },
    {
        "asset": "recp011XSIIwlMfCY",
        "organisation": "Powersheds",
        "url": "https://cdn.shopify.com/s/files/1/0601/8967/1489/files/"
               "1412PAWSLCDD28.jpg",
        "alt": "A Powersheds Apex Workshop Log Cabin in a garden",
        "products": ["recwvpChVgFSc2RWQ"],
    },

    # ---- YARD BOX -------------------------------------------------------
    # Created in Atlas 29 September 2026 to close the gap the previous pass
    # reported. PRODUCT ASSOCIATION IS DOM CONTAINMENT on yardbox.co.uk/models:
    # each image sits INSIDE the same card element as its model's heading and
    # description. That is Yard Box's own association of photograph to model on
    # their own site -- not PlotNua inferring identity from the fact that an
    # image happens to be Yard Box's, which the brief explicitly forbids.
    {
        "asset": "reca1N71LmZi78HvZ",
        "organisation": "Yard Box",
        "url": "https://images.squarespace-cdn.com/content/v1/"
               "619124cac9d9895faff3d303/b8f49726-43f3-4a54-895b-149a5349bc82/"
               "whistler+5.PNG",
        "alt": "The Yard Box Whistler, a compact garden room",
        # STRONGEST OF THE THREE: card containment AND the filename names the
        # product. Two independent signals agree.
        "products": ["receaph6vCI7xtS5K"],
    },
    {
        "asset": "recOwRs3TWWSUyiOr",
        "organisation": "Yard Box",
        "url": "https://images.squarespace-cdn.com/content/v1/"
               "619124cac9d9895faff3d303/8d487648-027f-4435-89d9-ae906fe9a790/"
               "854A5433+copy-2.jpg",
        "alt": "The Yard Box Vancouver, a mid-range garden room",
        # Card containment only; the filename is a camera code. Recorded as the
        # weaker association in the Atlas note rather than levelled up.
        "products": ["reckMDqp4tVjAjM7b"],
    },
    {
        "asset": "rec3FDMBST0pgNyyy",
        "organisation": "Yard Box",
        "url": "https://images.squarespace-cdn.com/content/v1/"
               "619124cac9d9895faff3d303/dca56524-1fb1-424b-8fac-ac5ad731b557/"
               "Yard-Box-Patrick-26+%281%29.JPG",
        "alt": "The Yard Box Toronto, a garden room installed in a garden",
        # ACCEPTED WITH A CAVEAT, which the Atlas note carries in full: the same
        # photograph is also the models page's site-wide hero, so it is the
        # supplier's chosen representation of The Toronto rather than an
        # isolated product shot. No stronger candidate exists.
        "products": ["recLEonLKyhNTUiAt"],
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
        # THE PERMITTED SCOPE TRAVELS WITH THE IMAGE.
        # The runtime cannot execute the node gate, and shipping the whole
        # rights manifest to every browser would be a second imagery
        # architecture. So the ONE fact the renderer needs to re-check the
        # gate's own rule -- the prefix this URL had to sit inside to be
        # authorised -- is carried on the asset. The renderer asserts the url
        # still starts with it before drawing anything. A tampered or
        # hand-edited url therefore fails closed at render time, not just at
        # publication time.
        scope = None
        u = urlparse(a["url"])
        host = (u.hostname or "").lower()
        host = host[4:] if host.startswith("www.") else host
        own = (grant.get("permitted_domain") or "").lower()
        own = own[4:] if own.startswith("www.") else own
        if own and (host == own or host.endswith("." + own)):
            scope = u.scheme + "://" + (u.hostname or "") + "/"
        else:
            for d in grant.get("permitted_delivery_hosts") or ():
                h = (d.get("host") or "").lower()
                h = h[4:] if h.startswith("www.") else h
                prefix = d.get("path_prefix") or ""
                if prefix and host == h and u.path.startswith(prefix):
                    scope = u.scheme + "://" + (u.hostname or "") + prefix
                    break
        if not scope:
            trace.append((a["asset"], org, "REFUSED",
                          "could not derive a permitted scope"))
            continue
        hit = 0
        for pid in a["products"]:
            if pid not in known:
                continue          # linked in Atlas, not in THIS universe
            hit += 1
            # ONE PRODUCT, EVERY AUTHORISED IMAGE. This was an
            # assignment, so the second asset to name a product silently
            # destroyed the first. It is now an ordered list, and the
            # same file linked twice is refused HERE rather than
            # deduplicated in two different renderers later.
            blocks = by_product.setdefault(pid, [])
            if any(b["url"] == a["url"] for b in blocks):
                continue
            blocks.append({
                "url": a["url"],
                "alt": a["alt"],
                "credit": credit,
                "supplier": org,
                "rightsRecord": grant.get("atlas_permission_ref"),
                "assetRecord": a["asset"],
                # Re-checked by the renderer before the image is drawn.
                "permittedPrefix": scope,
                # PLOTNUA'S OWN UNDERTAKING, WHERE ONE EXISTS. Carried so a
                # public surface can honour it without re-reading the record.
                "linkBack": (grant.get("publication_requirements")
                             and grant.get("permitted_domain")
                             and ("https://www." + grant["permitted_domain"] + "/")
                             or None),
                # STATE, NOT SCORE. Consumers read this to choose a richer
                # presentation. Nothing downstream may read it as quality.
                "presentationTier": "A",
            })
        trace.append((a["asset"], org, "ALLOWED",
                      "%d product(s) in this universe" % hit))
    return by_product, trace


def apply(doc, by_product):
    changed = 0
    for p in doc["products"]:
        pid = p.get("productId") or p.get("id")
        ims = by_product.get(pid)
        if ims:
            # `imagery` KEEPS ITS EXACT SHAPE -- a single block, the
            # first authorised image. Every existing consumer reads it
            # unchanged, so a one-image product is byte-identical.
            #
            # `imagerySet` is written ONLY when there are two or more.
            # Its ABSENCE is what says "one image", which is why adding
            # this capability changes no product in the universe today.
            if p.get("imagery") != ims[0]:
                changed += 1
            p["imagery"] = ims[0]
            if len(ims) > 1:
                if p.get("imagerySet") != ims:
                    changed += 1
                p["imagerySet"] = ims
            elif "imagerySet" in p:
                del p["imagerySet"]
                changed += 1
        else:
            # WITHDRAWAL PATH. No special case: losing the grant means no
            # resolved imagery, and BOTH keys go. A set left behind after
            # the primary was withdrawn would be unauthorised imagery
            # still on the page, which is the one outcome that must be
            # impossible.
            for k in ("imagery", "imagerySet"):
                if k in p:
                    del p[k]
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

    # PER-SUPPLIER, NOT GLOBAL. The first version of these guards mutated only
    # Powersheds and then asserted that NOTHING resolved. That held while one
    # supplier had imagery; the moment Yard Box was added the guards failed --
    # correctly, because the assertion was too narrow, not because the data was
    # wrong. Withdrawing one supplier's grant must remove EXACTLY that
    # supplier's images and leave every other supplier untouched, which is a
    # stronger claim than the original and scales to any number of grants.
    suppliers = sorted({a["organisation"] for a in ATLAS_ASSETS})
    for sup in suppliers:
        key = sup.strip().lower()
        if key not in grants:
            continue
        mine = {pid for pid, ims in by_product.items()
                if any(b["supplier"] == sup for b in ims)}
        others = {pid for pid in by_product if pid not in mine}

        # G5 — no live grant for THIS supplier: none of its images resolve,
        # and nobody else's disappear.
        gone = {k: v for k, v in grants.items() if k != key}
        bp, _ = resolve(copy.deepcopy(doc_before["products"]), gone)
        check("G5 %s without a live grant resolves no imagery" % sup,
              not (set(bp) & mine), "%d of its own resolved" % len(set(bp) & mine))
        check("G5 %s losing its grant disturbs no other supplier" % sup,
              others <= set(bp), "%d others kept" % len(others & set(bp)))

        # G6 — withdrawal, applied to a universe that already carries imagery.
        wdoc = copy.deepcopy(after_doc)
        wb, _ = resolve(wdoc["products"], gone)
        apply(wdoc, wb)
        still = {p.get("productId") for p in wdoc["products"] if p.get("imagery")}
        check("G6 withdrawing %s removes its images" % sup,
              not (still & mine))
        check("G6 withdrawing %s leaves the matching surface untouched" % sup,
              match_surface(wdoc) == before)

        # G7 — the scoping rule is authoritative, per supplier.
        grant = grants[key]
        hosts = grant.get("permitted_delivery_hosts") or []
        if hosts:
            bare = copy.deepcopy(grants)
            b = copy.deepcopy(grant)
            b["permitted_delivery_hosts"] = [{"host": hosts[0]["host"]}]
            bare[key] = b
            bp2, _ = resolve(copy.deepcopy(doc_before["products"]), bare)
            check("G7 %s: a bare host with no path prefix authorises nothing"
                  % sup, not (set(bp2) & mine),
                  "%d resolved" % len(set(bp2) & mine))

            other = copy.deepcopy(grants)
            o = copy.deepcopy(grant)
            o["permitted_delivery_hosts"] = [
                {"host": hosts[0]["host"],
                 "path_prefix": "/content/v1/0000000000000000/"
                 if "squarespace" in hosts[0]["host"]
                 else "/s/files/1/9999/9999/"}]
            other[key] = o
            bp3, _ = resolve(copy.deepcopy(doc_before["products"]), other)
            check("G7 %s: another tenant's prefix authorises nothing" % sup,
                  not (set(bp3) & mine),
                  "%d resolved" % len(set(bp3) & mine))

    # G-CREDIT — the grant's required credit travels with every image.
    # EVERY image in the set, not just the first. A gallery whose second
    # picture has no credit breaches the grant exactly as loudly as one
    # whose first does.
    missing = [pid for pid, ims in by_product.items()
               if any(not b.get("credit") for b in ims)]
    check("every resolved image carries its grant's required credit",
          not missing, "%d without credit" % len(missing))

    # THE SET IS A SET. Every block in it passed the same gate as the
    # primary, no url appears twice, and the primary is its first member.
    # Without this, "the gallery" could disagree with "the hero".
    bad = []
    for pid, ims in by_product.items():
        urls = [b["url"] for b in ims]
        if len(set(urls)) != len(urls):
            bad.append(pid + " duplicate url")
        for b in ims:
            if not b.get("permittedPrefix") or \
                    not b["url"].startswith(b["permittedPrefix"]):
                bad.append(pid + " unscoped url")
            if not b["url"].startswith("https://"):
                bad.append(pid + " not https")
    check("every image in a set is scoped, https and unique",
          not bad, "; ".join(bad[:4]))

    plural = {pid: len(ims) for pid, ims in by_product.items() if len(ims) > 1}
    check("the primary image is the first member of every set",
          all(by_product[pid][0]["url"] ==
              next(p["imagery"]["url"] for p in after_doc["products"]
                   if (p.get("productId") or p.get("id")) == pid)
              for pid in by_product),
          "%d product(s) carry 2+ images" % len(plural))

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

    # IMG-REFRESH — THE FLOOR. Checked BEFORE the write, so a collapsed
    # imagery layer never reaches a file, let alone a validator.
    if len(by_product) < REQUIRE_MIN:
        print("\nABORT: %d product(s) carry authorised imagery; at least %d "
              "were required. Nothing was written.\n"
              "       A grant has been withdrawn, or the asset/product links "
              "have moved.\n       Both are decisions a person makes and then "
              "lowers the floor for — not\n       something an unattended "
              "refresh may absorb quietly."
              % (len(by_product), REQUIRE_MIN))
        return 1
    UNIVERSE.write_text(
        json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\nwrote " + UNIVERSE.name + "  (%d product(s) changed)" % changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
