#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED HOLD — PRODUCTS WHOSE LINK IS NOT CURRENTLY SAFE LEAVE THE PUBLIC
PRODUCT DATA NOW, WITHOUT A FULL ATLAS REFRESH (19 OCTOBER 2026).

Founder direction, 19 Oct 2026: "APPROVE a temporary public-data hold on the
five Premium Log House products because of the reported unsafe redirects."
Evidence: opening a Premium Log House product page in a real browser redirected
to an advertising network and then an unrelated games site.

The durable rule lives in two generators, both reading
atlas-tools/safety-hold-products.json:
  * generate_garden_room_universe.py, Blocker G: a held product is excluded;
  * generate_recognition_pool.py: a held product keeps its identity (id, name,
    organisation) but its outbound url is withheld.
This script applies exactly those two rules to the committed files today, and
changes nothing else:
  * garden-room-recommendation-universe-v1.json: removes every held product,
    adjusts exactly the header counts those products contributed to (the same
    accounting as apply-preview-request-hold.py), records them under
    exclusionSummaryByReason "G", and recomputes the governed digest with the
    generator's own function;
  * atlas-recognition-pool.json: sets url to null on every held product.
It refuses if a held product has a product-level detail-partition entry
(removing detail is a different change).

  python3 atlas-tools/apply-safety-hold.py           apply
  python3 atlas-tools/apply-safety-hold.py --check   verify only
"""
import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GEN = ROOT / ".github" / "scripts" / "generate_garden_room_universe.py"
REGISTER = ROOT / "atlas-tools" / "safety-hold-products.json"
UNIVERSE = ROOT / "garden-room-recommendation-universe-v1.json"
POOL = ROOT / "atlas-recognition-pool.json"
INDEX = ROOT / "garden-room-detail-index-v1.json"
CHECK = "--check" in sys.argv


def die(m):
    print("REFUSED: " + m)
    sys.exit(2)


def gen():
    sys.path.insert(0, str(GEN.parent))
    spec = importlib.util.spec_from_file_location("grgen_safety_hold", GEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    held = {r["productId"] for r in reg["holds"]}
    if not held:
        die("the safety-hold register is empty")
    g = gen()
    if g.safety_held() != held:
        die("the generator does not read the same register")

    # ---- the universe ---------------------------------------------------
    raw = UNIVERSE.read_text(encoding="utf-8")
    u = json.loads(raw)
    if g.governed_digest(u["products"]) != u["governedDigest"]:
        die("the committed governedDigest does not match the committed products")
    out = [p for p in u["products"] if p["productId"] in held]
    keep = [p for p in u["products"] if p["productId"] not in held]

    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    for part in idx["partitions"]:
        if part["category"] == "suppliers":
            continue            # keyed by supplier, carries no product link
        d = json.loads((ROOT / part["file"]).read_text(encoding="utf-8"))
        for p in out:
            if p["productId"] in d.get("products", {}):
                die("%s has an entry in %s; this script does not remove detail"
                    % (p["productId"], part["file"]))

    for p in out:
        q = p["qualification"]
        u["eligibleCount"] -= 1
        u[{"HIGH_CONFIDENCE": "highConfidenceCount", "WITH_CAVEAT": "withCaveatCount",
           "LIMITED_EVIDENCE": "limitedEvidenceCount"}[q["confidenceTier"]]] -= 1
        u["excludedCount"] += 1
        u["exclusionSummaryByReason"]["G"] = u["exclusionSummaryByReason"].get("G", 0) + 1
        ps = q["evidenceSignals"]["price"]
        u["priceEvidenceSummary"][ps] -= 1
        if ps == "missing":
            u["missingPriceCount"] -= 1
        if ps == "quote-only":
            u["quoteOnlyPriceCount"] -= 1
    if out:
        u["organisationCount"] = len({p["organisation"] for p in keep})
        u["products"] = keep
        u["governedDigest"] = g.governed_digest(keep)
    if any(p["productId"] in held for p in u["products"]):
        die("a held product is still in the universe")
    if u["eligibleCount"] != len(u["products"]):
        die("eligibleCount does not match the product list")
    new_u = json.dumps(u, indent=1, ensure_ascii=False) + "\n"

    # ---- the recognition pool --------------------------------------------
    # Edited in place, not re-serialised: the committed file's own formatting
    # (one compact line) is kept, and only the held records' url values move.
    praw = POOL.read_text(encoding="utf-8")
    pool = json.loads(praw)
    linked = [r for r in pool if r["id"] in held and r.get("url")]
    new_p = praw
    for r in linked:
        pat = re.compile(r'(\{"id": "%s", [^{}]*?"url": )"(?:[^"\\]|\\.)*"' % re.escape(r["id"]))
        new_p, n = pat.subn(r"\1null", new_p)
        if n != 1:
            die("could not locate exactly one url for %s in the pool" % r["id"])
    after = json.loads(new_p)
    if len(after) != len(pool):
        die("the pool edit changed the number of records")
    for a, b in zip(pool, after):
        want = dict(a, url=None) if a["id"] in held else a
        if b != want:
            die("the pool edit changed something other than a held url (%s)" % a["id"])
    if not any(r["id"] in held for r in pool):
        print("note: no held product is in the recognition pool")

    if CHECK:
        if new_u != raw or new_p != praw or out or linked:
            print("CHECK FAILED: %d held product(s) in the universe, %d held link(s) in the pool"
                  % (len(out), len(linked)))
            sys.exit(1)
        print("safety hold · CHECK OK — %d held product(s): none in the garden-room universe, "
              "no outbound link in the recognition pool" % len(held))
        return
    UNIVERSE.write_text(new_u, encoding="utf-8")
    POOL.write_text(new_p, encoding="utf-8")
    print("APPLIED — removed %d product(s) from the universe; withheld %d link(s) in the pool"
          % (len(out), len(linked)))
    for p in out:
        print("  %s  %s" % (p["productId"], p["productName"]))


if __name__ == "__main__":
    main()
