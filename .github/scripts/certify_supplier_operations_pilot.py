#!/usr/bin/env python3
"""ISSUE 007 — SUPPLIER OPERATIONS EVIDENCE · 3-SUPPLIER PILOT CERTIFICATION.

Runs without Airtable. It simulates exactly the merge the generator performs —
same keys, same order, same guard — over the SHIPPED supplier partition, then
proves that the merged artefact is accepted by the validator and that nothing
in the eligibility path can see the new fields.

Nothing is written to any published artefact. This is a test, not a build.
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

import validate_garden_room_detail_evidence as V          # noqa: E402
import generate_garden_room_universe as G                 # noqa: E402

PILOT = sorted(G.SUPPLIER_OPS_EVIDENCE.keys())
fails = []


def check(ok, label, detail=""):
    print(("  ok    " if ok else "  FAIL  ") + label + (("  " + detail) if detail else ""))
    if not ok:
        fails.append(label)


# ---- the merge, exactly as the generator does it ---------------------------
partition = json.loads((ROOT / "garden-room-detail-suppliers-v1.json").read_text())
before = json.dumps(partition, sort_keys=True)
merged = json.loads(before if False else json.dumps(partition))   # deep copy
for oid, rec in merged["products"].items():
    ops = G.SUPPLIER_OPS_EVIDENCE.get(oid)
    if not ops:
        continue
    for k in G.SUPPLIER_OPS_KEYS:
        v = ops.get(k)
        if isinstance(v, str) and v.strip():
            rec["locality"][k] = v.strip()

print("\n=== A · CONTRACT ===")
check(len(G.SUPPLIER_OPS_KEYS) == 9, "nine typed fields in the generator contract")
touched = [o for o in merged["products"]
           if any(k in merged["products"][o]["locality"] for k in G.SUPPLIER_OPS_KEYS)]
check(sorted(touched) == sorted(PILOT), "exactly the certified organisations carry typed evidence",
      str(len(touched)) + " of " + str(len(merged["products"])))
check(all(json.dumps(partition["products"][o]["locality"].get("installationModel"))
          == json.dumps(merged["products"][o]["locality"].get("installationModel"))
          for o in merged["products"]), "existing Atlas prose preserved verbatim, all 61")

print("\n=== B · VALIDATOR ===")
errs = []
V.validate_supplier(merged, errs)
check(not errs, "merged partition passes the supplier contract", "; ".join(errs[:3]))

# The gate must actually bite. Each mutation must be REFUSED, and the refusal
# must name the rule under test — "it errored" is not a pass.
def refuses(mutate, needle, label):
    doc = json.loads(json.dumps(merged))
    mutate(doc["products"])
    e = []
    V.validate_supplier(doc, e)
    hit = [x for x in e if needle in x]
    check(bool(hit), label, (hit[0] if hit else "NOT REFUSED — " + "; ".join(e[:2]) or "no error"))

refuses(lambda p: p["recw124UIanKV5Ath"]["locality"].pop("installationSourceUrl"),
        "CONFIRMED without installationSourceUrl", "CONFIRMED installation without a source is refused")
refuses(lambda p: p["recw124UIanKV5Ath"]["locality"].pop("installationCheckedAt"),
        "CONFIRMED without installationCheckedAt", "CONFIRMED installation without a date is refused")
refuses(lambda p: p["reclA5R4kPCCwc8Pc"]["locality"].pop("deliverySourceUrl"),
        "CONFIRMED without deliverySourceUrl", "CONFIRMED delivery without a source is refused")
refuses(lambda p: p["rec0E8ongSL0hZnZR"]["locality"].__setitem__("roiDelivery", "EXCLUDED"),
        "claims 'EXCLUDED'", "EXCLUDED without confirmed, sourced delivery is refused")
refuses(lambda p: p["rec0E8ongSL0hZnZR"]["locality"].__setitem__("roiInstallCoverage", "NONE"),
        "claims 'NONE'", "NONE without confirmed, sourced delivery is refused")
refuses(lambda p: p["recw124UIanKV5Ath"]["locality"].__setitem__("roiInstallCoverage", "REGIONAL"),
        "claims 'REGIONAL'", "REGIONAL without confirmed, sourced delivery is refused")
refuses(lambda p: p["recw124UIanKV5Ath"]["locality"].__setitem__("installationType", "INSTALLS"),
        "not in the closed vocabulary", "a value outside the vocabulary is refused")
refuses(lambda p: p["recw124UIanKV5Ath"]["locality"].__setitem__("installationSourceUrl", "shomera.ie"),
        "not an https page URL", "a bare domain is not a page URL")
refuses(lambda p: p["recw124UIanKV5Ath"]["locality"].__setitem__("deliveryConfirmed", "true"),
        "FROZEN eligibility key", "the frozen eligibility key is still refused inside locality")

# UNKNOWN must cost nothing. This is the UNKNOWN != FALSE proof.
doc = json.loads(json.dumps(merged))
for k in ("installationSourceUrl", "installationCheckedAt"):
    doc["products"]["rec0E8ongSL0hZnZR"]["locality"].pop(k, None)
doc["products"]["rec0E8ongSL0hZnZR"]["locality"]["installationStatus"] = "UNKNOWN"
doc["products"]["rec0E8ongSL0hZnZR"]["locality"]["installationType"] = "UNKNOWN"
e = []
V.validate_supplier(doc, e)
check(not e, "UNKNOWN asserts nothing and needs no source", "; ".join(e[:2]))

print("\n=== C · SAFETY ===")
uni = json.loads((ROOT / "garden-room-recommendation-universe-v1.json").read_text())
check(len(uni["products"]) == 487, "eligible product count remains 487", str(len(uni["products"])))
check(uni["eligibleCount"] == 487 and "suppliers" not in uni,
      "universe export untouched and still carries no suppliers{}")

page = (ROOT / "your-plot.html").read_text()
# Every consumer of the eligibility channel reads `.irish`. The new keys are
# searched for by name across the whole production file: absent means no
# consumer exists, which is the requirement.
for k in G.SUPPLIER_OPS_KEYS:
    check(k not in page, "no production consumer reads " + k)
check("atlasSupplierEvidence[org].irish" in page.replace("\n", "").replace(" ", "")
      or "atlasSupplierEvidence && atlasSupplierEvidence[org]" in page,
      "marketEligibility still reads the .irish channel")
check(page.count("let atlasSupplierEvidence = {};") == 1,
      "atlasSupplierEvidence still initialises empty and is untouched")
frozen = ("excludedProductIds", "excludedRanges", "excludesIreland",
          "deliveryConfirmed", "installationConfirmed")
merged_keys = {k for o in merged["products"].values() for k in o["locality"]}
check(not (set(frozen) & merged_keys), "no frozen eligibility key appears in locality")

print("\n=== D · CERTIFIED RECORDS ===")
for oid in PILOT:
    loc = merged["products"][oid]["locality"]
    print("  " + merged["products"][oid]["name"])
    for k in G.SUPPLIER_OPS_KEYS:
        if k in loc:
            print("      " + k.ljust(22) + loc[k])

print("\n  pilot certification " + ("FAILED — " + "; ".join(fails) if fails else "PASSED"))
sys.exit(1 if fails else 0)
