#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED HOLD — A SUPPLIER WHO ASKED TO SEE A PREVIEW FIRST LEAVES THE
GARDEN-ROOM UNIVERSE NOW, WITHOUT A FULL ATLAS REFRESH (14 OCTOBER 2026).

Founder brief "Garden Retreat — controlled text-only publication expansion",
item 5. Cosy Cabins, 2 Oct 2026 (Gmail 1a0fd84efd61b0fa), answering outreach
that offered YES or PREVIEW: "PREVIEW please — I'd like to see how Cosy Cabins
would appear on PlotNua before anything is published." PlotNua replied the same
day that "nothing from Cosy Cabins has been published into the PlotNua
homeowner experience" and that the preview showed Cosy Cabins "through a
separate garden-room journey" as well as the sauna. The garden-room listing
(Athlone Garden Room 4.5m x 2.5m) entered the universe on 6 Oct, Search on
8 Oct and Living in the Garden on 13 Oct, with the request unanswered. The
request clearly covers it, so it is held.

The durable rule is Blocker F in generate_garden_room_universe.py, which reads
atlas-tools/preview-only-suppliers.json: the next refresh keeps the product
out. This script applies the same rule to the committed universe today and
changes nothing else:
  * removes every product whose organisation is in the preview-only register;
  * adjusts exactly the header counts those products contributed to, and
    recomputes the governed digest with the generator's own function;
  * refuses if a removed product has detail-partition or supplier entries
    (none exist for Cosy Cabins; removing them is a different change).

  python3 atlas-tools/apply-preview-request-hold.py           apply
  python3 atlas-tools/apply-preview-request-hold.py --check   verify only
"""
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GEN = ROOT / ".github" / "scripts" / "generate_garden_room_universe.py"
UNIVERSE = ROOT / "garden-room-recommendation-universe-v1.json"
INDEX = ROOT / "garden-room-detail-index-v1.json"
CHECK = "--check" in sys.argv


def die(m):
    print("REFUSED: " + m)
    sys.exit(2)


def gen():
    sys.path.insert(0, str(GEN.parent))
    spec = importlib.util.spec_from_file_location("grgen_hold", GEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    g = gen()
    held = g.preview_requested()
    raw = UNIVERSE.read_text(encoding="utf-8")
    u = json.loads(raw)
    if g.governed_digest(u["products"]) != u["governedDigest"]:
        die("the committed governedDigest does not match the committed products")
    out = [p for p in u["products"] if g._norm_org_name(p.get("organisation")) in held]
    keep = [p for p in u["products"] if g._norm_org_name(p.get("organisation")) not in held]

    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    for part in idx["partitions"]:
        d = json.loads((ROOT / part["file"]).read_text(encoding="utf-8"))
        for p in out:
            if p["productId"] in d.get("products", {}):
                die("%s has an entry in %s; this script does not remove detail" % (p["productId"], part["file"]))
        if part["category"] == "suppliers":
            names = {v.get("name") for v in d["products"].values()}
            for p in out:
                if p["organisation"] in names:
                    die("%s has a supplier entry; this script does not remove it" % p["organisation"])

    if out:
        orgs_left = {p["organisation"] for p in keep}
        for p in out:
            q = p["qualification"]
            tier = q["confidenceTier"]
            u["eligibleCount"] -= 1
            u[{"HIGH_CONFIDENCE": "highConfidenceCount", "WITH_CAVEAT": "withCaveatCount",
               "LIMITED_EVIDENCE": "limitedEvidenceCount"}[tier]] -= 1
            u["excludedCount"] += 1
            u["exclusionSummaryByReason"]["F"] = u["exclusionSummaryByReason"].get("F", 0) + 1
            # priceEvidenceSummary, missingPriceCount and quoteOnlyPriceCount
            # count EMITTED products only; the Irish and URL counts cover
            # emitted + excluded and so do not move.
            ps = q["evidenceSignals"]["price"]
            u["priceEvidenceSummary"][ps] -= 1
            if ps == "missing":
                u["missingPriceCount"] -= 1
            if ps == "quote-only":
                u["quoteOnlyPriceCount"] -= 1
        u["organisationCount"] = len(orgs_left)
        u["products"] = keep
        u["governedDigest"] = g.governed_digest(keep)
    if any(g._norm_org_name(p.get("organisation")) in held for p in u["products"]):
        die("a preview-requested supplier is still in the universe")
    if u["eligibleCount"] != len(u["products"]):
        die("eligibleCount does not match the product list")
    new = json.dumps(u, indent=1, ensure_ascii=False) + "\n"
    if CHECK:
        if new != raw or out:
            print("CHECK FAILED: %d product(s) from preview-requested suppliers are published" % len(out))
            sys.exit(1)
        print("preview-request hold · CHECK OK — no product from %s is in the garden-room universe"
              % ", ".join(sorted(held)))
        return
    UNIVERSE.write_text(new, encoding="utf-8")
    print("APPLIED — removed %d product(s): %s" % (len(out), ", ".join(
        "%s (%s)" % (p["productId"], p["organisation"]) for p in out) or "none"))


if __name__ == "__main__":
    main()
