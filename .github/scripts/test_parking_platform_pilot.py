#!/usr/bin/env python3
"""
PlotNua — PARKING PLATFORM CONTROLLED PILOT: certification tests.

Proves the governance correction of 2026-09-22 (canonical evidence model +
claim_basis) and re-proves the six original pilot questions. Read-only:
writes nothing, contacts nothing, touches no Airtable record.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GEN = HERE / "generate_parking_platform_evidence.py"

# The generator is imported so the PROVENANCE MODEL can be unit-tested
# directly. The private correspondence INSTANCE was removed from the public
# artefact by the disclosure firewall, so the model can no longer be tested
# through the emitted JSON — it must be tested at the function.
_spec = importlib.util.spec_from_file_location("parking_gen_uut", GEN)
gen = importlib.util.module_from_spec(_spec)
sys.modules["parking_gen_uut"] = gen
try:
    _spec.loader.exec_module(gen)
except SystemExit:
    pass

PASS = FAIL = 0

CANONICAL_DIMENSIONS = ("authority", "source_type", "evidence_type",
                        "verification_method", "verification_status",
                        "maturity", "provenance", "claim_basis",
                        "homeowner_safe", "logic_safe",
                        "last_verified", "valid_from", "review_interval_months",
                        "staleness_policy")


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
        out = Path(td) / "m.json"
        r = subprocess.run([sys.executable, str(GEN), "--out", str(out),
                            "--as-of", "2026-09-22"], capture_output=True, text=True)
        ck("the generator runs", r.returncode == 0, r.stderr[-300:])
        if r.returncode:
            return 1
        m = json.loads(out.read_text(encoding="utf-8"))
        claims = m["claims"]
        k = {c["claim_key"]: c for c in claims}
        src = GEN.read_text(encoding="utf-8")

        # ── A. canonical vocabulary restored ────────────────────────────────
        print("\n--- A. canonical evidence model ---")
        for d in CANONICAL_DIMENSIONS:
            ck(f"every claim carries '{d}'", all(d in c for c in claims),
               str([c["claim_key"] for c in claims if d not in c][:2]))
        ck("schema version reflects the correction",
           m["schema"].endswith(".v2"), m["schema"])
        ck("the canonical model is declared in the artefact",
           "decomposition" in m["canonicalModel"])

        # ── B. evidence_state is derived, not stored ────────────────────────
        print("\n--- B. evidence_state is derived, never the stored truth ---")
        ck("no claim stores a hand-set 'evidence_state'",
           not any("evidence_state" in c and c.get("evidence_state") is not None
                   for c in claims))
        ck("the derived label is present on every claim",
           all(c.get("evidence_state_derived") for c in claims))
        ck("the artefact says the label is derived",
           "DISPLAY LABEL" in m["canonicalModel"])
        # derivation must be a pure function of the dimensions
        ck("an operative instrument derives VERIFIED",
           k["cancellation_terms"]["evidence_state_derived"] == "VERIFIED"
           and k["cancellation_terms"]["source_type"] == "CONTRACT_TERM")
        ck("a marketing claim derives SUPPLIER-CLAIMED",
           k["ireland_service_coverage"]["evidence_state_derived"] == "SUPPLIER-CLAIMED"
           and k["ireland_service_coverage"]["source_type"] == "MARKETING_CLAIM")
        ck("an absence derives NOT_PUBLICLY_EVIDENCED",
           k["host_fee_rate"]["evidence_state_derived"] == "NOT_PUBLICLY_EVIDENCED"
           and k["host_fee_rate"]["evidence_type"] == "ABSENCE_OF_RECORD")
        ck("an untested question derives UNKNOWN",
           k["eircode_onboarding_accepted"]["evidence_state_derived"] == "UNKNOWN")
        ck("conflicting sources derive CONTRADICTED",
           k["company_number_inconsistency"]["evidence_state_derived"] == "CONTRADICTED")
        # The private instance was removed from this PUBLIC artefact by the
        # disclosure firewall, so the derivation is unit-tested against the
        # function directly. The model must still work, or a supplier-supplied
        # fact could not be added later without being mistaken for one PlotNua
        # verified independently.
        ck("correspondence still derives SUPPLIER-CLAIMED (model unit-test)",
           gen.derive_state({"evidence_type": "CORRESPONDENCE",
                             "provenance": "COMMERCIAL_CORRESPONDENCE",
                             "source_type": "OUTREACH_RECORD"})
           == "SUPPLIER-CLAIMED")
        ck("a future SUPPLIER_PROVIDED fact derives SUPPLIER-CLAIMED, not VERIFIED",
           gen.derive_state({"evidence_type": "PUBLISHED_SOURCE",
                             "provenance": "SUPPLIER_PROVIDED",
                             "source_type": "MARKETING_CLAIM"})
           == "SUPPLIER-CLAIMED")

        # ── C. claim_basis ──────────────────────────────────────────────────
        print("\n--- C. claim_basis: STATED vs OPERATIONAL ---")
        ck("every claim declares a basis", all(c["claim_basis"] for c in claims))
        ck("EVERY claim is STATED — none is OPERATIONAL",
           all(c["claim_basis"] == "STATED" for c in claims),
           str([c["claim_key"] for c in claims if c["claim_basis"] != "STATED"]))
        ck("no OPERATIONAL claim exists without operational evidence",
           m["claimsByBasis"].get("OPERATIONAL", 0) == 0)
        ck("STATED is explicitly NOT defined as weaker",
           "not a weaker grade" in src.lower())
        stated_logic_safe = [c for c in claims
                             if c["claim_basis"] == "STATED" and c["logic_safe_resolved"]]
        ck("STATED claims from operative instruments ARE logic-safe",
           len(stated_logic_safe) >= 8, f"{len(stated_logic_safe)} logic-safe")
        ck("contractual terms specifically are logic-safe",
           k["governing_law"]["logic_safe_resolved"]
           and k["host_fee_model"]["logic_safe_resolved"]
           and k["cancellation_terms"]["logic_safe_resolved"])

        # ── D. uncertainty and contradictions preserved ─────────────────────
        print("\n--- D. preservation of unknowns and contradictions ---")
        required = {
            "host_fee_rate": "NOT_PUBLICLY_EVIDENCED",
            "host_protection_insurance_roi": "NOT_PUBLICLY_EVIDENCED",
            "eircode_onboarding_accepted": "UNKNOWN",
            "referral_affiliate_route": "NOT_PUBLICLY_EVIDENCED",
            "space_property_requirements": "NOT_PUBLICLY_EVIDENCED",
            "space_verification_requirements": "NOT_PUBLICLY_EVIDENCED",
            "company_number_inconsistency": "CONTRADICTED",
        }
        for key, expect in required.items():
            ck(f"{key} preserved as {expect}",
               k[key]["evidence_state_derived"] == expect,
               k[key]["evidence_state_derived"])
        opens = [c for c in claims if c["evidence_state_derived"]
                 in ("UNKNOWN", "NOT_PUBLICLY_EVIDENCED", "CONTRADICTED")]
        # THE INVARIANT DIFFERS BY KIND, AND CONFLATING THEM WAS A TEST BUG.
        # An UNKNOWN or an absence must hold NO value — nothing is known, so
        # any value would be invention. A CONTRADICTED claim is the opposite
        # case: its value IS the conflicting observations, and blanking it
        # would delete the very contradiction the record exists to preserve.
        # What a contradiction must never do is assert a winner.
        nothing_known = [c for c in opens
                         if c["evidence_state_derived"] != "CONTRADICTED"]
        ck("no UNKNOWN or absent claim carries a fabricated value",
           all(c["value"] is None for c in nothing_known),
           str([c["claim_key"] for c in nothing_known if c["value"] is not None]))
        contradictions = [c for c in opens
                          if c["evidence_state_derived"] == "CONTRADICTED"]
        ck("a contradiction records BOTH conflicting observations",
           all(isinstance(c["value"], dict) and len(c["value"]) >= 2
               for c in contradictions))
        ck("a contradiction asserts no resolution",
           all(c["maturity"] == "UNRESOLVED_CONFLICT" and not c["logic_safe_resolved"]
               for c in contradictions))
        ck("no open claim is logic-safe",
           not [c for c in opens if c["logic_safe_resolved"]],
           str([c["claim_key"] for c in opens if c["logic_safe_resolved"]]))
        ck("the UK insurance clause remains forbidden from being read across",
           any("United Kingdom" in p for p in
               k["host_protection_insurance_roi"]["prohibited_readings"]))
        ck("no host fee rate or percentage is recorded",
           k["host_fee_rate"]["value"] is None)
        ck("absences record the search that produced them",
           all(c["maturity"] == "BOUNDED_SEARCH" and
               c["verification_method"] == "TARGETED_SEARCH"
               for c in claims if c["evidence_type"] == "ABSENCE_OF_RECORD"))

        # ── E. completion governance ────────────────────────────────────────
        print("\n--- E. platform completion governance ---")
        cm, comp = m["completionModel"], m["completion"]
        ck("the seven dimensions are recorded",
           cm["dimensions"] == ["Identity", "Route", "Jurisdiction",
                                "Commercial Terms", "Protection", "Exit",
                                "Currency"])
        ck("an evidenced negative may satisfy a dimension",
           "EVIDENCED NEGATIVE may satisfy" in cm["rule"])
        ck("UNKNOWN does not satisfy a dimension",
           "UNKNOWN does not satisfy" in cm["rule"])
        ck("completion is defined as a judgement, not a score",
           "NOT a mechanical" in cm["explicitly_not"])
        ck("YourParkingSpace completion is UNRESOLVED",
           comp["status"] == "UNRESOLVED")
        ck("the two material unknowns are named as the reason",
           set(comp["dimensionsOpen"]) == {"Commercial Terms", "Protection"})
        ck("completion is not expressed as a count",
           "score" not in comp["status"].lower() and "/7" not in json.dumps(comp))

        # ── F. supplier-provided evidence can arrive later ──────────────────
        print("\n--- F. public disclosure firewall + provenance model intact ---")
        # THIS ARTEFACT IS PUBLICLY FETCHABLE from the site root. Labelling a
        # claim COMMERCIAL_CORRESPONDENCE stops it reaching a HOMEOWNER; it
        # does nothing to stop the FILE being fetched. Private relationship
        # material must therefore be absent entirely, not merely flagged.
        ck("NO claim carries COMMERCIAL_CORRESPONDENCE provenance",
           not [c for c in claims
                if c["provenance"] == "COMMERCIAL_CORRESPONDENCE"])
        ck("NO claim cites a private outreach record as its source",
           not [c for c in claims if c["source_type"] == "OUTREACH_RECORD"])
        ck("NO claim is verified by correspondence",
           not [c for c in claims if c["verification_method"] == "CORRESPONDENCE"])
        ck("every published claim is PUBLIC_PRIMARY",
           {c["provenance"] for c in claims} == {"PUBLIC_PRIMARY"},
           str(m["claimsByProvenance"]))
        ck("every published claim cites a checkable source",
           all(c["source_url"] for c in claims))
        # ...while the MODEL survives, so a fact supplied later can still be
        # classified without being mistaken for independent verification.
        ck("SUPPLIER_PROVIDED remains a defined provenance",
           "SUPPLIER_PROVIDED" in gen.PROVENANCE)
        ck("COMMERCIAL_CORRESPONDENCE remains a defined provenance",
           "COMMERCIAL_CORRESPONDENCE" in gen.PROVENANCE)
        ck("correspondence would still be barred from driving logic",
           not gen.resolve(dt.date(2026, 9, 22),
                           {"last_verified": "2026-09-22",
                            "review_interval_months": 3, "logic_safe": True,
                            "homeowner_safe": True,
                            "evidence_type": "CORRESPONDENCE",
                            "provenance": "COMMERCIAL_CORRESPONDENCE",
                            "source_type": "OUTREACH_RECORD"}
                           )["logic_safe_resolved"])

        # ── G. staleness still works, identity still stable ─────────────────
        print("\n--- G. expiry without disturbing identity ---")
        out2 = Path(td) / "future.json"
        subprocess.run([sys.executable, str(GEN), "--out", str(out2),
                        "--as-of", "2027-06-22"], capture_output=True, text=True)
        f = {c["claim_key"]: c for c in json.loads(out2.read_text("utf-8"))["claims"]}
        ck("time-sensitive terms go STALE",
           f["host_onboarding_page_available"]["verification_status"] == "STALE")
        ck("a stale claim loses both safety flags",
           not f["host_onboarding_page_available"]["homeowner_safe_resolved"]
           and not f["host_onboarding_page_available"]["logic_safe_resolved"])
        ck("a stale claim keeps its evidence and is not deleted",
           f["host_onboarding_page_available"]["source_url"]
           and f["host_onboarding_page_available"]["evidence_type"] == "PUBLISHED_SOURCE")
        ck("ORGANISATION IDENTITY is untouched by expiry",
           f["platform_legal_identity"]["value"] == k["platform_legal_identity"]["value"])

        # ── H. containment ──────────────────────────────────────────────────
        print("\n--- H. containment: Garden Room architecture untouched ---")
        blob = json.dumps(m).lower()
        for bad in ("productid", "product_category", "producttype",
                    "qualificationtier", "flooraream2", "manufacturesku"):
            ck(f"no Garden Room product field '{bad}'", bad not in blob)
        u = json.loads((ROOT / "garden-room-recommendation-universe-v1.json")
                       .read_text(encoding="utf-8"))
        ck("Garden Room universe still holds 487 admitted products",
           len(u["products"]) == 487)
        ck("Garden Room tiers unchanged (138/349/0)",
           (u["highConfidenceCount"], u["withCaveatCount"],
            u["limitedEvidenceCount"]) == (138, 349, 0))
        ck("no parking platform leaked into the Garden Room universe",
           "yourparkingspace" not in json.dumps(u).lower())
        ck("the pilot is not referenced by the runtime",
           "parking-platform-evidence" not in
           (ROOT / "your-plot.html").read_text(encoding="utf-8"))
        ck("only ONE platform is represented", m["platformCount"] == 1)

    print("\n" + "=" * 74)
    print(f"  {PASS} passed, {FAIL} failed")
    print("=" * 74)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
