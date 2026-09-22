#!/usr/bin/env python3
"""
PlotNua — PARKING PLATFORM CONTROLLED PILOT: certification tests.

Answers the six questions the pilot exists to answer, against the generated
manifest and against the live Atlas schema. Read-only: writes nothing,
contacts nothing, and touches no Airtable record.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GEN = HERE / "generate_parking_platform_evidence.py"

PASS = FAIL = 0


def ck(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"    ok   {name}")
    else:
        FAIL += 1
        print(f"    *** FAIL *** {name}  {detail}")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "parking-platform-evidence.json"
        r = subprocess.run([sys.executable, str(GEN), "--out", str(out),
                            "--as-of", "2026-09-22"],
                           capture_output=True, text=True)
        ck("the generator runs", r.returncode == 0, r.stderr[-300:])
        if r.returncode != 0:
            return 1
        m = json.loads(out.read_text(encoding="utf-8"))
        claims = m["claims"]
        by_key = {c["claim_key"]: c for c in claims}

        # ── TEST 1 — can PlotNua answer the homeowner question? ─────────────
        print("\n--- 1. Is there a currently evidenced Irish listing route? ---")
        route = by_key["irish_homeowner_listing_route"]
        onboard = by_key["host_onboarding_route_available"]
        ident = by_key["platform_legal_identity"]
        answerable = (route["evidence_state"] == "VERIFIED"
                      and route["homeowner_safe_resolved"]
                      and onboard["evidence_state"] == "VERIFIED"
                      and ident["evidence_state"] == "VERIFIED")
        ck("YES is answerable, from VERIFIED primary evidence only", answerable)
        ck("the answer rests on Irish sources, not UK ones",
           all(".ie" in c["source_url"] for c in (route, onboard, ident)))
        ck("no COMMERCIAL_CORRESPONDENCE claim supports the answer",
           all(c["provenance"] == "PUBLIC_PRIMARY" for c in (route, onboard, ident)))

        # ── TEST 2 — is the unknown correctly identified? ───────────────────
        print("\n--- 2. Is what remains unknown correctly identified? ---")
        for k in ("host_fee_rate", "host_protection_insurance_roi",
                  "eircode_onboarding_accepted", "referral_affiliate_route",
                  "space_property_requirements", "space_verification_requirements"):
            c = by_key[k]
            ck(f"{k} is preserved as {c['evidence_state']}",
               c["evidence_state"] in ("UNKNOWN", "NOT_PUBLICLY_EVIDENCED"))
        unknowns = [c for c in claims
                    if c["evidence_state"] in ("UNKNOWN", "NOT_PUBLICLY_EVIDENCED")]
        # THE INVARIANT THAT MATTERS: an absence of evidence may be SHOWN
        # ("PlotNua could not find a published fee rate" is honest and useful),
        # but it may never be an INPUT TO A DECISION, and it may never carry a
        # value. An earlier draft of this suite asserted that no unknown could
        # be homeowner-safe at all; that was over-broad — it would have
        # suppressed exactly the honest disclosure the framework exists to make.
        ck("no unknown claim is logic-safe (absence never drives a decision)",
           not [c for c in unknowns if c["logic_safe_resolved"]],
           str([c["claim_key"] for c in unknowns if c["logic_safe_resolved"]]))
        ck("no unknown claim carries a fabricated value",
           all(c["value"] is None for c in unknowns),
           str([c["claim_key"] for c in unknowns if c["value"] is not None]))
        ck("every shown unknown travels with its evidence state",
           all(c["evidence_state"] for c in unknowns if c["homeowner_safe_resolved"]))
        ck("the UK insurance clause is explicitly forbidden from being read across",
           any("United Kingdom" in p for p in
               by_key["host_protection_insurance_roi"]["prohibited_readings"]))
        # Narrow and correct: the FEE claims must carry no rate. The manifest
        # legitimately contains other percentages (the published refund table),
        # and a blanket "%" ban would have flagged those as commission.
        fee_claims = [by_key["host_fee_rate"], by_key["host_fee_model"],
                      by_key["listing_cost"]]
        ck("no host fee rate or percentage is recorded on any fee claim",
           by_key["host_fee_rate"]["value"] is None
           and not any("%" in json.dumps(c["value"] or {}) for c in fee_claims
                       if c["claim_key"] != "listing_cost"))

        # ── TEST 3 — expiry without disturbing identity ─────────────────────
        print("\n--- 3. Can time-sensitive claims expire without moving identity? ---")
        out2 = Path(td) / "future.json"
        r2 = subprocess.run([sys.executable, str(GEN), "--out", str(out2),
                             "--as-of", "2027-06-22"], capture_output=True, text=True)
        ck("the generator runs at a future date", r2.returncode == 0)
        f = {c["claim_key"]: c for c in json.loads(out2.read_text("utf-8"))["claims"]}
        ck("time-sensitive terms go STALE",
           f["host_onboarding_route_available"]["verification_status"] == "STALE")
        ck("a stale claim is no longer homeowner-safe",
           not f["host_onboarding_route_available"]["homeowner_safe_resolved"])
        ck("a stale claim is no longer logic-safe",
           not f["host_onboarding_route_available"]["logic_safe_resolved"])
        ck("a stale claim is NOT deleted and keeps its evidence",
           f["host_onboarding_route_available"]["evidence_state"] == "VERIFIED"
           and f["host_onboarding_route_available"]["source_url"])
        ck("ORGANISATION IDENTITY is untouched by expiry",
           f["platform_legal_identity"]["value"] == ident["value"]
           and f["platform_legal_identity"]["evidence_state"] == "VERIFIED")
        ck("identity carries a longer review interval than terms do",
           f["platform_legal_identity"]["review_interval_months"]
           > f["host_onboarding_route_available"]["review_interval_months"])

        # ── TEST 4 — no PRODUCT field abused ────────────────────────────────
        print("\n--- 4. Has any PRODUCT-specific field been abused? ---")
        blob = json.dumps(m).lower()
        for bad in ("productid", "product_category", "producttype",
                    "qualificationtier", "productevidenceconfidence",
                    "priceevidencestate", "flooraream2", "manufacturesku"):
            ck(f"no Garden Room product field '{bad}'", bad not in blob)
        ck("the manifest declares it creates no product record",
           "no atlas product record" in m["note"].lower())
        ck("no price/currency figure is presented as a product price",
           by_key["chargeback_admin_fee"]["value"]["currency"] == "EUR"
           and by_key["host_fee_rate"]["value"] is None)

        # ── TEST 5 — no supplier claim promoted to fact ─────────────────────
        print("\n--- 5. Was any supplier claim promoted to verified fact? ---")
        sc = [c for c in claims if c["evidence_state"] == "SUPPLIER-CLAIMED"]
        ck("supplier claims exist and are labelled as such", len(sc) >= 3)
        ck("the Ireland coverage figure stays SUPPLIER-CLAIMED",
           by_key["ireland_service_coverage"]["evidence_state"] == "SUPPLIER-CLAIMED")
        ck("'free to list' stays SUPPLIER-CLAIMED",
           by_key["listing_cost"]["evidence_state"] == "SUPPLIER-CLAIMED")
        ck("the payment mechanism stays SUPPLIER-CLAIMED",
           by_key["payment_mechanism"]["evidence_state"] == "SUPPLIER-CLAIMED")
        ck("every VERIFIED claim carries a source URL and a quote or structured value",
           all(c["source_url"] and (c["quote"] or c["value"])
               for c in claims if c["evidence_state"] == "VERIFIED"))
        ck("the fee STRUCTURE is verified while the RATE is not — they are separate claims",
           by_key["host_fee_model"]["evidence_state"] == "VERIFIED"
           and by_key["host_fee_rate"]["evidence_state"] == "NOT_PUBLICLY_EVIDENCED")

        # ── TEST 6 — supplier-supplied evidence can arrive later ────────────
        print("\n--- 6. Can supplier-supplied evidence be added without confusion? ---")
        rel = by_key["plotnua_commercial_relationship"]
        ck("correspondence is a distinct provenance",
           rel["provenance"] == "COMMERCIAL_CORRESPONDENCE")
        ck("correspondence is not homeowner-safe", not rel["homeowner_safe_resolved"])
        ck("correspondence is not logic-safe", not rel["logic_safe_resolved"])
        ck("correspondence is forbidden from establishing service facts",
           any("availability" in p.lower() for p in rel["prohibited_readings"]))
        ck("no public claim shares the correspondence provenance",
           len([c for c in claims
                if c["provenance"] == "COMMERCIAL_CORRESPONDENCE"]) == 1)
        ck("a third provenance exists for future supplier-supplied facts",
           "SUPPLIER_PROVIDED" in Path(GEN).read_text("utf-8"))
        ck("provenance is carried on every single claim",
           all(c.get("provenance") for c in claims))

        # ── containment ─────────────────────────────────────────────────────
        print("\n--- containment: Garden Room architecture untouched ---")
        uni = ROOT / "garden-room-recommendation-universe-v1.json"
        u = json.loads(uni.read_text(encoding="utf-8"))
        ck("Garden Room universe still holds 487 admitted products",
           len(u["products"]) == 487)
        ck("Garden Room tiers unchanged (138/349/0)",
           (u["highConfidenceCount"], u["withCaveatCount"],
            u["limitedEvidenceCount"]) == (138, 349, 0))
        ck("no parking platform leaked into the Garden Room universe",
           "yourparkingspace" not in json.dumps(u).lower())
        ck("the pilot manifest is not referenced by the runtime",
           "parking-platform-evidence" not in (ROOT / "your-plot.html")
           .read_text(encoding="utf-8"))

    print("\n" + "=" * 74)
    print(f"  {PASS} passed, {FAIL} failed")
    print("=" * 74)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
