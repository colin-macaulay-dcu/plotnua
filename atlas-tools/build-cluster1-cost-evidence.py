#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLUSTER 1 COST EVIDENCE: A DETERMINISTIC, COMMITTED GENERATOR (SEO-C1, 20 Oct 2026)

atlas-tools/cluster1-cost-evidence.json is the governed evidence behind two
pages: garden-room-prices-ireland.html (through its frozen extract, rule R6)
and the price section of discovery-living-in-the-garden.html. It was produced
once, on 11 October 2026, by a script that was never committed. This generator
closes that gap.

  1. FIDELITY FIRST. From the base snapshot (the universe revision whose sha256
     the register names), with NO correction applied, it must reproduce the
     evidence as first committed (register: baseEvidence.revision) BYTE FOR
     BYTE. If it cannot, it refuses and writes nothing.
  2. Only then does it apply atlas-tools/cost-evidence-corrections.json: each
     listed product takes its record from the universe at a deployed commit
     (or leaves the snapshot), and every figure is recomputed by the SAME
     functions. No figure is typed anywhere.

The definitions are shared, not copied: relevance and price basis come from
atlas-tools/build-garden-room-prices.py (relevant(), segment()).

  python3 atlas-tools/build-cluster1-cost-evidence.py --prove-base   fidelity only
  python3 atlas-tools/build-cluster1-cost-evidence.py --check        fidelity + committed file == generated
  python3 atlas-tools/build-cluster1-cost-evidence.py --apply        fidelity, then write
"""
import hashlib
import importlib.util
import json
import pathlib
import statistics
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "atlas-tools" / "cluster1-cost-evidence.json"
REGISTER = ROOT / "atlas-tools" / "cost-evidence-corrections.json"
UNIVERSE = "garden-room-recommendation-universe-v1.json"
EVIDENCE_REL = "atlas-tools/cluster1-cost-evidence.json"

# Fixed text of the evidence file (not figures). Proved by the byte-for-byte
# reproduction of the 11 October file.
SCHEMA = "plotnua.cluster1.cost-evidence"
BASE_GENERATED = "2026-10-11"
DISCLAIMER = ("PlotNua Atlas is not a census of the Irish garden-room market. These counts "
              "describe what Atlas holds, and nothing more. No figure here may be averaged "
              "across price bases.")
RELEVANCE = {"currency": "EUR", "priceSafeForMatching": True, "noPublishedIrishRoute": False,
             "numericPrice": True, "excludes": "availabilityStatus == Out of Stock"}
NOTES = [
    "The supply-only / DIY-kit segment is thinly represented in the euro set because the large "
    "DIY-kit sellers held in Atlas are GBP-priced or carry noPublishedIrishRoute: true. That is a "
    "coverage fact about Atlas, not a fact about the Irish market.",
    "No homeowner-visible copy may state a price for the 32-45 m2 Class 3A envelope: Atlas holds "
    "one product in it.",
]
# Floor-area envelopes (m2), in the 2026 planning classes.
ENVELOPES = (("lte30_class3", lambda a: a <= 30),
             ("between32and45_class3A", lambda a: 32 <= a <= 45),
             ("gt45", lambda a: a > 45))


def die(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(1)


def price_builder():
    argv, sys.argv = sys.argv, [sys.argv[0]]       # the builder reads its own flags at import
    try:
        spec = importlib.util.spec_from_file_location(
            "grp_builder_for_evidence", ROOT / "atlas-tools" / "build-garden-room-prices.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
    finally:
        sys.argv = argv
    return m


def git_show(rev, path):
    r = subprocess.run(["git", "show", "%s:%s" % (rev, path)], cwd=ROOT, capture_output=True)
    if r.returncode:
        die("git show %s:%s failed" % (rev[:12], path))
    return r.stdout


def universe_at_sha(want):
    """The universe snapshot whose bytes hash to `want`, from git history."""
    revs = subprocess.run(["git", "log", "--format=%H", "--", UNIVERSE], cwd=ROOT,
                          capture_output=True, text=True).stdout.split()
    for r in revs:
        b = subprocess.run(["git", "show", "%s:%s" % (r, UNIVERSE)], cwd=ROOT,
                           capture_output=True).stdout
        if hashlib.sha256(b).hexdigest() == want:
            return json.loads(b), r
    die("no revision of %s hashes to %s" % (UNIVERSE, want[:12]))


def register():
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    if reg.get("schema") != "plotnua.cost-evidence-corrections":
        die("the corrections register has the wrong schema")
    return reg


def apply_corrections(products, reg):
    """The snapshot's product list with every registered correction applied.
    Each listed product takes its record from the universe at the deployed
    commit (which must be the commit the register names, by sha256), or leaves
    the list when that universe no longer carries it. Order is preserved."""
    out = list(products)
    applied = []
    for c in reg.get("corrections") or []:
        raw = git_show(c["deployedCommit"], UNIVERSE)
        if hashlib.sha256(raw).hexdigest() != c["deployedUniverseSha256"]:
            die("correction %s: the universe at %s is not the one the register names"
                % (c["id"], c["deployedCommit"][:12]))
        anc = subprocess.run(["git", "merge-base", "--is-ancestor", c["deployedCommit"], "HEAD"],
                             cwd=ROOT).returncode
        if anc:
            die("correction %s: commit %s is not in this branch's history"
                % (c["id"], c["deployedCommit"][:12]))
        deployed = {p["id"]: p for p in json.loads(raw)["products"]}
        ids = [p["id"] for p in c["products"]]
        if len(set(ids)) != len(ids):
            die("correction %s lists a product twice" % c["id"])
        for entry in c["products"]:
            pid = entry["id"]
            idx = [i for i, p in enumerate(out) if p["id"] == pid]
            if len(idx) != 1:
                die("correction %s: %s is not in the snapshot exactly once" % (c["id"], pid))
            if pid in deployed:
                if entry.get("expect") != "replaced":
                    die("correction %s: %s is still published; the register expects %s"
                        % (c["id"], pid, entry.get("expect")))
                out[idx[0]] = deployed[pid]
            else:
                if entry.get("expect") != "removed":
                    die("correction %s: %s is no longer published; the register expects %s"
                        % (c["id"], pid, entry.get("expect")))
                del out[idx[0]]
        applied.append(c)
    return out, applied


def floor_area(p):
    return ((p.get("features") or {}).get("floorArea") or {}).get("number")


def summary(rows, with_vat=True):
    prices = [p["price"] for p in rows]
    d = {"n": len(rows), "organisations": len({p["organisation"] for p in rows}),
         "minEur": min(prices), "medianEur": statistics.median(prices), "maxEur": max(prices)}
    if with_vat:
        d.update({"vatIncluded": sum(p.get("vatStatus") == "Yes" for p in rows),
                  "vatExcluded": sum(p.get("vatStatus") == "No" for p in rows),
                  "vatUnknown": sum(p.get("vatStatus") not in ("Yes", "No") for p in rows),
                  "floorAreaKnown": sum(floor_area(p) is not None for p in rows)})
    return d


def evidence(products, snap, sha, b, applied):
    rel = [p for p in products if b.relevant(p)]
    seg_of = {}
    order = []
    for p in rel:
        s = b.segment(p)
        if s is None:
            die("a relevant product has no segment rule: %s" % p["id"])
        seg_of[p["id"]] = s
        if s not in order:
            order.append(s)
    area = [p for p in rel if floor_area(p) is not None]
    totals = {
        "gardenRoomRecords": len(products),
        "organisationsAll": len({p["organisation"] for p in products}),
        "relevant": len(rel),
        "relevantOrganisations": len({p["organisation"] for p in rel}),
        "priceBasisNotEstablished": sum(seg_of[p["id"]].startswith("UNKNOWN") for p in rel),
        "vatStatusUnknown": sum(p.get("vatStatus") not in ("Yes", "No") for p in rel),
        "floorAreaPublished": len(area),
        "floorAreaPublishedOrganisations": len({p["organisation"] for p in area}),
        "rangeFloorPrices": sum(bool(p.get("priceIsRangeFloor")) for p in rel),
        "quoteOnly": sum(bool((p.get("priceEvidence") or {}).get("quoteOnly")) for p in rel),
    }
    segments = {k: summary([p for p in rel if seg_of[p["id"]] == k]) for k in order}
    envelopes = {}
    for name, test in ENVELOPES:
        rows = [p for p in area if test(floor_area(p))]
        if rows:
            d = summary(rows, with_vat=False)
            envelopes[name] = {"n": d["n"], "organisations": d["organisations"], "minEur": d["minEur"],
                               "maxEur": d["maxEur"], "medianEur": d["medianEur"]}
    doc = {
        "schema": SCHEMA,
        "version": 1,
        "generated": applied[-1]["date"] if applied else BASE_GENERATED,
        "source": {"file": UNIVERSE, "generated": snap["generated"], "sha256": sha},
        "disclaimer": DISCLAIMER,
        "relevanceFilter": RELEVANCE,
        "totals": totals,
        "segments": segments,
        "classEnvelopes": envelopes,
        "homeownerVisibleFigures": {
            "relevantProducts": totals["relevant"],
            "priceBasisNotEstablished": totals["priceBasisNotEstablished"],
            "vatStatusUnknown": totals["vatStatusUnknown"],
            "floorAreaPublished": totals["floorAreaPublished"],
            "class3AProductsInAtlas": envelopes.get("between32and45_class3A", {}).get("n", 0),
        },
        "notes": NOTES,
    }
    if applied:
        doc["corrections"] = [{"id": c["id"], "date": c["date"], "deployedCommit": c["deployedCommit"],
                               "products": [p["id"] for p in c["products"]], "pageNote": c["pageNote"]}
                              for c in applied]
    # The file as first committed has no final newline; kept, so the bytes match.
    return json.dumps(doc, indent=2)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    if mode not in ("--prove-base", "--check", "--apply"):
        die("usage: --prove-base | --check | --apply")
    b = price_builder()
    reg = register()
    want = reg["baseSnapshot"]["sha256"]
    snap, rev = universe_at_sha(want)
    if snap.get("generated") != reg["baseSnapshot"]["generated"]:
        die("the base snapshot's stamp is not the one the register names")

    # 1 · fidelity: reproduce the evidence as first committed, byte for byte
    base_text = evidence(snap["products"], snap, want, b, [])
    first = git_show(reg["baseEvidence"]["revision"], EVIDENCE_REL).decode("utf-8")
    if base_text != first:
        import difflib
        print("".join(list(difflib.unified_diff(first.splitlines(True), base_text.splitlines(True),
                                                "committed 11 Oct", "regenerated"))[:60]))
        die("FIDELITY: the generator does not reproduce the evidence as first committed")
    print("FIDELITY OK — reproduced %s@%s byte for byte (%d bytes) from the snapshot %s (revision %s)"
          % (EVIDENCE_REL, reg["baseEvidence"]["revision"][:7], len(first), want[:12], rev[:7]))
    if mode == "--prove-base":
        return

    # 2 · corrections, then the same computation
    products, applied = apply_corrections(snap["products"], reg)
    text = evidence(products, snap, want, b, applied)
    for c in applied:
        print("  applied %s (%s): %s" % (c["id"], c["deployedCommit"][:7],
              ", ".join("%s %s" % (p["id"], p["expect"]) for p in c["products"])))
    current = EVIDENCE.read_text(encoding="utf-8")
    if mode == "--check":
        if current != text:
            die("CHECK: the committed evidence is not what the snapshot and the register produce")
        print("COST EVIDENCE · CHECK OK — committed evidence == snapshot + %d registered correction(s)"
              % len(applied))
        return
    EVIDENCE.write_text(text, encoding="utf-8")
    print("  wrote %s" % EVIDENCE_REL)


if __name__ == "__main__":
    main()
