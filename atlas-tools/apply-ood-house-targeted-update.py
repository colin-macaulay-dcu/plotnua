#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED SPLICE — ÖÖD HOUSE TARGETED PUBLICATION UPDATE (14 OCTOBER 2026).

Founder brief "PlotNua — ÖÖD House targeted publication update": publish what
Keir Tetsmann (ÖÖD, UK and Irish clients) confirmed on 14 Oct 2026 for the
seven ÖÖD products --
    Republic of Ireland availability confirmed;
    transport from Estonia individually quoted;
    installation, foundations and utility connections arranged by the customer;
    technical drawings supplied by ÖÖD --
WITHOUT the full Atlas refresh, and without publishing any unrelated Atlas
change that has accumulated since the last refresh (7 Oct 2026).

HOW, AND WHY THIS SHAPE
  The real generator (.github/scripts/generate_garden_room_universe.py) is run
  OFFLINE against a committed ÖÖD-only Atlas snapshot
  (ood-house-atlas-snapshot-2026-10-14.json: the 7 products, their pricing,
  availability and 133 feature values, the 20 features they use, and the ÖÖD
  organisation, read 14 Oct 2026). Nothing is hand-written: every published
  value comes out of the same code the refresh uses. Its output for those
  seven products, their detail entries and the ÖÖD supplier entry is then
  spliced into the committed artefacts, and NOTHING ELSE moves.

  Every change is checked against an allow-list of the fields the brief
  touches. A price, a VAT state, a product URL, a name -- anything outside the
  list -- refuses the whole splice. Header counts are adjusted only by the
  seven products' own transitions, and the governed price digest is
  recomputed with the generator's own function.

  Imagery is NOT this script's job: apply_authorised_imagery.py remains the
  only writer of `imagery`/`imagerySet`, and existing blocks are carried over
  untouched. Run it after this.

WHAT CHANGES FOR ÖÖD, AND WHAT DOES NOT
  irishAvailability unknown -> confirmed (Confirmation State "Yes");
  the "Irish availability is not yet confirmed" caveat goes; tier
  WITH_CAVEAT -> HIGH_CONFIDENCE. The installation axis of the price basis
  moves from INCLUDED (read from the superseded "turnkey installation
  included" lead) to UNKNOWN, so nothing says installation is in the price.
  Price, VAT, currency, product URL and every other governed field are
  byte-identical.

  python3 atlas-tools/apply-ood-house-targeted-update.py           apply
  python3 atlas-tools/apply-ood-house-targeted-update.py --check   verify only
"""
import copy
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
GEN = ROOT / ".github" / "scripts" / "generate_garden_room_universe.py"
SNAP = ROOT / "atlas-tools" / "ood-house-atlas-snapshot-2026-10-14.json"
UNIVERSE = ROOT / "garden-room-recommendation-universe-v1.json"
INDEX = ROOT / "garden-room-detail-index-v1.json"
SUPPLIERS = ROOT / "garden-room-detail-suppliers-v1.json"
EVIDENCE = ROOT / "garden-room-detail-evidence-v1.json"
CHECK = "--check" in sys.argv

ORG = "rec2URqKyVwlhHSBw"
PRODUCTS = {
    "recGGCVFmV7lY1zkj": "ÖÖD Extended House",
    "recyc7vNON16NzYFD": "ÖÖD Glämping House",
    "recl9ITOz7WlqPPBn": "ÖÖD Glääzy House",
    "reczasgBzBbqP1lBg": "ÖÖD Mobile House",
    "reciFE98KRWuAhBwP": "ÖÖD Möön House",
    "recoQZlqmpfv3T5bz": "ÖÖD Signature House",
    "recPWKdUbLnAvXxmU": "ÖÖD The Big Monolith",
}

# The ONLY product paths the brief may move. Anything else refuses.
ALLOWED_PRODUCT_PATHS = {
    ".features.floorArea.records", ".features.installationModel.text",
    ".features.insulation.text", ".features.irishAvailability.confirmationState",
    ".features.irishAvailability.status", ".features.irishAvailability.text",
    ".features.warranty.text", ".insulation", ".irishAvailability",
    ".irishAvailabilityConfirmationState", ".priceBasisAxes.erection",
    ".priceBasisClass", ".priceBasisConfidence", ".priceEvidenceRef.basisLeadPhrase",
    ".qualification.caveats", ".qualification.confidenceTier",
    ".qualification.evidenceSignals.irishAvailability",
    ".qualification.evidenceSignals.irishAvailabilityBasis",
    ".qualification.reasons", ".qualification.status",
    ".qualificationCaveats", ".qualificationTier",
}
# Fields that must be byte-identical whatever the snapshot says.
FROZEN = ("name", "productId", "organisation", "price", "currency", "priceStatus",
          "priceType", "priceScope", "vatStatus", "vatRate", "priceIsRangeFloor",
          "priceSafeForMatching", "priceRecordIds", "productUrl", "imagery", "imagerySet")
DETAIL_CATEGORIES = {   # file stem -> key inside each product entry
    "alternatives": "alternatives", "bestfor": "bestFor",
    "considerations": "considerations",
    "planningconsiderations": "planningConsiderations",
    "strengths": "strengths", "typicalhomeowner": "typicalHomeowner",
}
ALLOWED_LOCALITY = {"installationModel", "irishPresence", "deliveryCoverage", "evidenceTier"}

# Phrases that would say installation is in the price. None may survive in an
# ÖÖD record after the splice. ÖÖD's own published general statement
# ("delivered fully assembled ... installable in one day") is KEPT in the
# installation record, labelled as recorded before the Irish confirmation and
# as not describing the Irish arrangement; it says nothing about price, and the
# record's lead -- the only part any surface classifies -- now says the work
# is customer-arranged.
INCLUDED_CLAIMS = ("installation included", "including installation",
                   "installation is included", "turnkey price", "supply and fit")
INSTALL_LEAD = "INSTALLATION CUSTOMER-ARRANGED IN IRELAND"


def die(m):
    print("REFUSED: " + m)
    sys.exit(2)


def diff(a, b, path, acc):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            diff(a.get(k, "<absent>"), b.get(k, "<absent>"), path + "." + k, acc)
    elif a != b:
        acc.append(path)


def load_gen():
    if str(GEN.parent) not in sys.path:
        sys.path.insert(0, str(GEN.parent))
    spec = importlib.util.spec_from_file_location("grgen", GEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def regenerate(tmp):
    r = subprocess.run([sys.executable, str(GEN), "--snapshot", str(SNAP),
                        "--out-dir", str(tmp), "--production-candidate"],
                       capture_output=True, text=True)
    if r.returncode:
        die("the generator refused the ÖÖD snapshot:\n" + r.stdout + r.stderr)
    return {p.name: json.loads(p.read_text(encoding="utf-8"))
            for p in pathlib.Path(tmp).glob("*.json")}


def dump2(d):
    return json.dumps(d, indent=2) + "\n"


def main():
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    if sorted(p["id"] for p in snap["products"]) != sorted(PRODUCTS):
        die("the snapshot does not hold exactly the seven ÖÖD products")
    if [o["id"] for o in snap["organisations"]] != [ORG]:
        die("the snapshot must hold the ÖÖD organisation and no other")

    with tempfile.TemporaryDirectory() as tmp:
        gen = regenerate(tmp)
    new_u = gen["garden-room-recommendation-universe-v1.json"]
    if sorted(p["productId"] for p in new_u["products"]) != sorted(PRODUCTS):
        die("the generator did not qualify exactly the seven ÖÖD products")

    out = {}

    # ---- the universe ------------------------------------------------------
    cur_raw = UNIVERSE.read_text(encoding="utf-8")
    cur = json.loads(cur_raw)
    base = copy.deepcopy(cur)
    by_id = {p["productId"]: p for p in new_u["products"]}
    swapped = 0
    for i, p in enumerate(cur["products"]):
        pid = p["productId"]
        if pid not in PRODUCTS:
            continue
        if p.get("name") != PRODUCTS[pid] or p.get("organisation") != "ÖÖD House":
            die("%s is not the ÖÖD product this splice expects" % pid)
        n = copy.deepcopy(by_id[pid])
        for k in ("imagery", "imagerySet"):     # owned by the imagery pass
            n.pop(k, None)
            if k in p:
                n[k] = p[k]
        acc = []
        diff(p, n, "", acc)
        stray = sorted(set(acc) - ALLOWED_PRODUCT_PATHS)
        if stray:
            die("%s would change outside the brief: %s" % (pid, ", ".join(stray)))
        for k in FROZEN:
            if p.get(k) != n.get(k):
                die("%s: frozen field %s would change" % (pid, k))
        if n["qualification"]["evidenceSignals"]["irishAvailability"] != "confirmed" \
                or n.get("irishAvailabilityConfirmationState") != "Yes":
            die("%s: Irish availability did not come out confirmed" % pid)
        if n["priceBasisAxes"].get("erection") == "INCLUDED":
            die("%s: the price basis still says installation is included" % pid)
        if not n["features"]["installationModel"]["text"].startswith(INSTALL_LEAD):
            die("%s: the installation lead is not the customer-arranged one" % pid)
        blob = json.dumps(n, ensure_ascii=False).lower()
        hit = [c for c in INCLUDED_CLAIMS if c in blob]
        if hit:
            die("%s: still carries an installation-included claim: %s" % (pid, hit))
        was = (p["qualification"]["evidenceSignals"]["irishAvailability"], p["qualificationTier"])
        now = (n["qualification"]["evidenceSignals"]["irishAvailability"], n["qualificationTier"])
        if was != ("unknown", "WITH_CAVEAT") and was != now:
            die("%s: unexpected starting state %r" % (pid, was))
        if was != now:
            cur["confirmedIrishAvailabilityCount"] += 1
            cur["unknownIrishAvailabilityCount"] -= 1
            cur["highConfidenceCount"] += 1
            cur["withCaveatCount"] -= 1
        cur["products"][i] = n
        swapped += 1
    if swapped != 7:
        die("found %d of the seven ÖÖD products in the universe" % swapped)
    others = [p for p in base["products"] if p["productId"] not in PRODUCTS]
    if others != [p for p in cur["products"] if p["productId"] not in PRODUCTS]:
        die("a non-ÖÖD product moved")
    g = load_gen()
    if g.governed_digest(base["products"]) != base["governedDigest"]:
        die("the committed governedDigest does not match the committed products")
    cur["governedDigest"] = g.governed_digest(cur["products"])
    hdr = {k for k in cur if k != "products" and cur[k] != base[k]}
    if not hdr <= {"confirmedIrishAvailabilityCount", "unknownIrishAvailabilityCount",
                   "highConfidenceCount", "withCaveatCount", "governedDigest"}:
        die("header fields outside the brief would change: %s" % sorted(hdr))
    out[UNIVERSE] = json.dumps(cur, indent=1, ensure_ascii=False) + "\n"

    # ---- detail partitions -------------------------------------------------
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    new_ev = gen["garden-room-detail-evidence-v1.json"]["products"]
    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    ev_old = EVIDENCE.read_text(encoding="utf-8")
    changes = []
    for stem, key in DETAIL_CATEGORIES.items():
        f = ROOT / ("garden-room-detail-%s-v1.json" % stem)
        old_text = f.read_text(encoding="utf-8")
        d = json.loads(old_text)
        nd = gen[f.name]["products"]
        for pid in PRODUCTS:
            if pid not in nd:
                continue
            if pid not in d["products"]:
                die("%s has no %s entry to update" % (pid, key))
            a, b = d["products"][pid][key], nd[pid][key]
            if a == b:
                continue
            if set(a) != set(b) or any(a[k] != b[k] for k in a if k != "text"):
                die("%s %s: only the text may change" % (pid, key))
            d["products"][pid][key] = b
            if ev["products"][pid].get(key) != a:
                die("%s %s: the evidence file disagrees with its partition" % (pid, key))
            ev["products"][pid][key] = new_ev[pid][key]
            changes.append((pid, key))
        text = dump2(d)
        if text != old_text:
            out[f] = text
    ev_text = dump2(ev)
    if ev_text != ev_old:
        out[EVIDENCE] = ev_text

    # ---- the ÖÖD supplier entry --------------------------------------------
    sup_old = SUPPLIERS.read_text(encoding="utf-8")
    sup = json.loads(sup_old)
    a = sup["products"][ORG]
    b = gen["garden-room-detail-suppliers-v1.json"]["products"][ORG]
    if set(a) != set(b) or set(a["locality"]) != set(b["locality"]):
        die("the ÖÖD supplier entry changed shape")
    moved = {k for k in a if k != "locality" and a[k] != b[k]}
    lmoved = {k for k in a["locality"] if a["locality"][k] != b["locality"][k]}
    if not moved <= {"lastReviewed"} or not lmoved <= ALLOWED_LOCALITY:
        die("supplier fields outside the brief would change: %s" % sorted(moved | lmoved))
    sup["products"][ORG] = b
    sup_text = dump2(sup)
    if sup_text != sup_old:
        out[SUPPLIERS] = sup_text

    # ---- the index: byte counts of the partitions that moved ---------------
    for part in index["partitions"]:
        f = ROOT / part["file"]
        if f in out:
            old = f.read_text(encoding="utf-8")
            part["rawBytes"] += len(out[f].encode("utf-8")) - len(old.encode("utf-8"))
    idx_text = dump2(index)
    if idx_text != INDEX.read_text(encoding="utf-8"):
        out[INDEX] = idx_text

    print("ÖÖD HOUSE TARGETED UPDATE")
    print("  universe: 7 products respliced; header %s" % ", ".join(sorted(hdr)))
    print("  detail entries updated: %d (%s)" % (len(changes), ", ".join(
        sorted({k for _, k in changes}))))
    print("  supplier entry: lastReviewed + %s" % ", ".join(sorted(lmoved)))
    stale = [f.name for f, t in out.items() if f.read_text(encoding="utf-8") != t]
    if CHECK:
        if stale:
            print("CHECK FAILED: not yet applied to " + ", ".join(stale))
            sys.exit(1)
        print("CHECK OK — the committed artefacts carry exactly the ÖÖD update")
        return
    for f, t in out.items():
        f.write_text(t, encoding="utf-8")
    print("APPLIED — " + (", ".join(stale) if stale else "nothing to change"))


if __name__ == "__main__":
    main()
