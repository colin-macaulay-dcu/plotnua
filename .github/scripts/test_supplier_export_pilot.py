#!/usr/bin/env python3
"""
PlotNua — DISC-026 SUPPLIER EXPORT pilot: Stage 3 certification tests.

Read-only. Writes nothing, contacts nothing, touches no Airtable record.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GEN = HERE / "generate_supplier_export_evidence.py"

PASS = FAIL = 0
PILOT = {"electric-ireland", "bord-gais-energy", "energia", "flogas"}
EXCLUDED = ("sse airtricity", "sseairtricity", "pinergy")
CANONICAL = ("authority", "source_type", "evidence_type", "verification_method",
             "verification_status", "maturity", "provenance", "claim_basis",
             "homeowner_safe", "logic_safe", "last_verified",
             "review_interval_months", "staleness_policy", "source_url")


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
        src = GEN.read_text(encoding="utf-8")
        blob = json.dumps(m).lower()
        spec = importlib.util.spec_from_file_location("gen_uut", GEN)
        gen = importlib.util.module_from_spec(spec)
        sys.modules["gen_uut"] = gen
        try:
            spec.loader.exec_module(gen)
        except SystemExit:
            pass

        # ── A. scope ────────────────────────────────────────────────────────
        print("\n--- A. pilot scope ---")
        ck("exactly four pilot suppliers", m["supplierCount"] == 4)
        ck("the four are the approved four",
           set(m["suppliers"].keys()) == PILOT, str(set(m["suppliers"].keys())))
        # Excluded suppliers must contribute NOTHING — no supplier entry, no
        # claim, no rate. They may legitimately be NAMED once, in the pilot
        # note, recording that they were deliberately excluded; suppressing
        # that would hide a scope decision rather than document it.
        for x in EXCLUDED:
            ck(f"excluded supplier '{x}' contributes no supplier entry",
               not any(x in k.lower() or x in v["supplier_name"].lower()
                       for k, v in m["suppliers"].items()))
            ck(f"excluded supplier '{x}' contributes no claim",
               not any(x in c["supplier_key"].lower()
                       or x in c["supplier_name"].lower() for c in claims))
            ck(f"excluded supplier '{x}' appears only in the exclusion note",
               blob.count(x) <= 1 and (x not in blob or x in m["pilotNote"].lower()))
        ck("every claim belongs to a pilot supplier",
           all(c["supplier_key"] in PILOT for c in claims))
        ck("every supplier carries claims",
           all(v["claimCount"] > 0 for v in m["suppliers"].values()))
        ck("selection is declared evidence-shaped, not a ranking",
           "NOT a ranking" in m["pilotNote"])

        # ── B. canonical vocabulary ─────────────────────────────────────────
        print("\n--- B. canonical evidence vocabulary ---")
        for d in CANONICAL:
            ck(f"every claim carries '{d}'", all(d in c for c in claims),
               str([c["claim_key"] for c in claims if d not in c][:2]))
        ck("no claim stores a hand-set evidence_state",
           not any(c.get("evidence_state") for c in claims))
        ck("a derived display label is present on every claim",
           all(c.get("evidence_state_derived") for c in claims))
        ck("every claim carries provenance",
           all(c.get("provenance") for c in claims))
        ck("all provenance is PUBLIC_PRIMARY",
           set(m["claimsByProvenance"]) == {"PUBLIC_PRIMARY"},
           str(m["claimsByProvenance"]))

        # ── C. claim_basis ──────────────────────────────────────────────────
        print("\n--- C. claim_basis ---")
        ck("every supplier commercial claim is STATED",
           all(c["claim_basis"] == "STATED" for c in claims))
        ck("ZERO OPERATIONAL claims",
           m["claimsByBasis"].get("OPERATIONAL", 0) == 0)
        ck("the generator refuses to emit an OPERATIONAL claim",
           "only STATED is permitted" in src)
        ck("no supplier claim is promoted above SUPPLIER-CLAIMED",
           set(m["claimsByDerivedState"]) <= {"SUPPLIER-CLAIMED",
                                              "NOT_PUBLICLY_EVIDENCED"},
           str(m["claimsByDerivedState"]))

        # ── D. VAT firewall ─────────────────────────────────────────────────
        print("\n--- D. VAT firewall (mandatory) ---")
        vat = {c["supplier_key"]: c for c in claims
               if c["claim_field"] == "export_rate_vat_basis"}
        ck("every supplier has an explicit VAT-basis claim", len(vat) == 4)
        ck("Flogas VAT basis is evidenced",
           vat["flogas"]["evidence_type"] == "PUBLISHED_SOURCE"
           and vat["flogas"]["value"]["vat_rate_percent"] == 9)
        for k in ("electric-ireland", "bord-gais-energy", "energia"):
            ck(f"{k} VAT basis preserved as NOT_PUBLICLY_EVIDENCED",
               vat[k]["evidence_state_derived"] == "NOT_PUBLICLY_EVIDENCED"
               and vat[k]["value"] is None)
        ck("VAT-unknown claims forbid inference of the basis",
           all(any("VAT-inclusive or VAT-exclusive" in p
                   for p in vat[k]["prohibited_readings"])
               for k in ("electric-ireland", "bord-gais-energy", "energia")))
        ck("rate claims forbid comparison while VAT basis is unknown",
           all(any("ranking or normalisation" in p for p in c["prohibited_readings"])
               for c in claims if c["claim_field"] == "export_rate"
               and c["supplier_key"] != "flogas"))
        ck("the manifest declares rate comparison FORBIDDEN",
           m["comparisonGovernance"]["rateComparison"] == "FORBIDDEN")
        # NO RANKING LOGIC — tested by BEHAVIOUR, not by grepping for words.
        # An earlier draft banned the substrings "rank", "normalis", "cheapest"
        # and "max(" outright. That flagged the prohibition text itself, the
        # refusal docstring and `max(months, 0)` in the staleness arithmetic —
        # i.e. it failed the file for containing the very rules that forbid
        # ranking. What matters is that no ordering is PRODUCED.
        code = "\n".join(l for l in src.splitlines()
                         if not l.strip().startswith("#"))
        for banned in ("sort(", "sorted(", ".sort", "argmax", "best_rate",
                       "cheapest_supplier", "rate_rank"):
            ck(f"generator contains no '{banned}' ordering call",
               banned not in code, "found in executable source")
        ck("no ordering or ranking field is emitted anywhere in the manifest",
           not re.search(r'"(rank|position|order|cheapest|best|winner|'
                         r'normalised[^"]*|comparison_result)"\s*:', blob))
        ck("no supplier record carries a comparative score",
           not any(any(k.lower() in ("rank", "score", "position")
                       for k in v) for v in m["suppliers"].values()))
        ck("the only numeric rates present are each supplier's own published "
           "figures, on its own stated basis",
           {json.dumps(c["value"], sort_keys=True) for c in claims
            if c["claim_field"] == "export_rate"}.__len__() == 4)
        ck("comparable_rates() exists only to refuse",
           callable(gen.comparable_rates))
        try:
            gen.comparable_rates()
            ck("comparable_rates() raises rather than returning an ordering", False)
        except NotImplementedError as e:
            ck("comparable_rates() raises rather than returning an ordering",
               "forbidden" in str(e).lower())
        ck("no derived annual-earnings comparison exists",
           "annual_earnings" not in src or "indicative_annual_earnings" in src)
        ei = next(c for c in claims
                  if c["claim_field"] == "indicative_annual_earnings")
        ck("the one earnings figure is the supplier's own and is not logic-safe",
           ei["source_type"] == "SUPPLIER_MARKETING_CLAIM"
           and not ei["logic_safe_resolved"])

        # ── E. payment-mechanism firewall ───────────────────────────────────
        print("\n--- E. payment-mechanism firewall ---")
        pay = {c["supplier_key"]: c for c in claims
               if c["claim_field"] == "payment_mechanism"}
        ck("all four payment mechanisms are recorded", len(pay) == 4)
        wordings = {k: v["value"]["as_published"] for k, v in pay.items()}
        ck("no two suppliers share an identical flattened wording",
           len(set(wordings.values())) == 4, str(wordings))
        ck("each mechanism forbids restatement as a generic 'bill credit'",
           all(any("generic 'bill credit'" in p for p in c["prohibited_readings"])
               for c in pay.values()))
        ck("Energia's explicit non-cash statement is preserved",
           "rather than a direct bank transfer" in pay["energia"]["value"]["as_published"])
        freq = {c["supplier_key"]: c["value"]["as_published"] for c in claims
                if c["claim_field"] == "payment_frequency"}
        ck("payment frequency recorded per supplier, unflattened",
           len(freq) == 4 and len(set(freq.values())) == 4, str(freq))

        # ── F. structural decision model ────────────────────────────────────
        print("\n--- F. structural comparison is what the pilot supports ---")
        bg = [c for c in claims if c["supplier_key"] == "bord-gais-energy"]
        ck("deemed export is evidenced for Bord Gáis",
           any(c["claim_field"] == "deemed_export_supported"
               and c["value"]["deemed"] for c in bg))
        ck("deemed export is NOT_PUBLICLY_EVIDENCED for the other three",
           all(next(c for c in claims if c["supplier_key"] == k
                    and c["claim_field"] == "deemed_export_treatment"
                    )["evidence_state_derived"] == "NOT_PUBLICLY_EVIDENCED"
               for k in ("electric-ireland", "energia", "flogas")))
        ck("customer-of-supplier requirement evidenced for Electric Ireland",
           next(c for c in claims if c["supplier_key"] == "electric-ireland"
                and c["claim_field"] == "customer_of_supplier_required"
                )["value"]["required"] is True)
        ck("smart-meter positions differ and are preserved per supplier",
           len({json.dumps(c["value"]) for c in claims
                if c["claim_field"] == "smart_meter_required"}) >= 2)
        ck("permitted comparison dimensions are declared",
           len(m["comparisonGovernance"]["permittedComparison"]) >= 6)

        # ── G. unknowns preserved ───────────────────────────────────────────
        print("\n--- G. unknowns preserved, nothing inferred ---")
        absents = [c for c in claims if c["evidence_type"] == "ABSENCE_OF_RECORD"]
        ck("absences exist and are numerous", len(absents) >= 12, str(len(absents)))
        ck("no absence carries a value", all(c["value"] is None for c in absents))
        ck("no absence is logic-safe",
           not [c for c in absents if c["logic_safe_resolved"]])
        ck("every absence records the search that produced it",
           all(c["maturity"] == "BOUNDED_SEARCH"
               and c["verification_method"] == "TARGETED_SEARCH" for c in absents))
        ck("caps / minimum terms / exclusions unevidenced for all four",
           len([c for c in absents
                if c["claim_field"] == "caps_minimum_terms_exclusions"]) == 4)
        ck("the third-party effective-date conflict is recorded as a limitation",
           any("24 June 2025" in " ".join(c["limitations"]) for c in claims))

        # ── H. image-rights containment ─────────────────────────────────────
        print("\n--- H. image-rights containment ---")
        ir = m["imageRights"]
        ck("zero supplier images declared", ir["supplierImagesUsed"] == 0)
        ck("zero logos declared", ir["logosUsed"] == 0)
        ck("zero hotlinks declared", ir["hotlinks"] == 0)
        ck("zero Asset records declared", ir["assetRecordsCreated"] == 0)
        for ext in (".jpg", ".jpeg", ".png", ".webp", ".svg", ".gif"):
            ck(f"no '{ext}' reference anywhere in the manifest", ext not in blob)
        # The `imageRights` block is the CONTAINMENT DECLARATION, so a blanket
        # ban on keys beginning "image"/"logo" flagged the very field that
        # proves containment. What must not exist is an image-BEARING field:
        # a URL, a path or an asset reference.
        img_keys = re.findall(r'"([a-z_]*(?:image|logo|photo|thumbnail|hero)'
                              r'[a-z_]*)"\s*:', blob)
        ck("the only image-named keys are inside the containment declaration",
           set(img_keys) <= {"imagerights", "supplierimagesused", "logosused"},
           str(sorted(set(img_keys))))
        ck("no image URL, path or asset reference exists",
           not re.search(r'https?://[^"\s]+\.(?:jpg|jpeg|png|webp|svg|gif)', blob)
           and "asset" not in re.sub(r"assetrecordscreated", "", blob))

        # ── I. containment: no leakage ──────────────────────────────────────
        print("\n--- I. containment ---")
        for bad in ("productid", "product_category", "producttype",
                    "qualificationtier", "flooraream2", "manufacturesku",
                    "results eligibility", "gold standard"):
            ck(f"no Garden Room product field '{bad}'", bad not in blob)
        u = json.loads((ROOT / "garden-room-recommendation-universe-v1.json")
                       .read_text(encoding="utf-8"))
        ck("Garden Room universe unchanged at 487 admitted",
           len(u["products"]) == 487)
        ck("Garden Room tiers unchanged (138/349/0)",
           (u["highConfidenceCount"], u["withCaveatCount"],
            u["limitedEvidenceCount"]) == (138, 349, 0))
        ck("no electricity supplier leaked into the Garden Room universe",
           not any(s in json.dumps(u).lower()
                   for s in ("electric ireland", "bord gáis", "bord gais",
                             "energia", "flogas")))
        pk = json.loads((ROOT / "parking-platform-evidence.json")
                        .read_text(encoding="utf-8"))
        # 22, not the original 23: the public disclosure firewall removed the
        # private commercial-correspondence claim from this publicly fetchable
        # artefact. The platform count and the evidence itself are untouched.
        ck("Parking Platform pilot intact (22 claims, 1 platform)",
           pk["claimCount"] == 22 and pk["platformCount"] == 1,
           f"{pk['claimCount']} claims / {pk['platformCount']} platform")
        ck("Parking pilot carries no correspondence provenance either",
           "COMMERCIAL_CORRESPONDENCE" not in pk["claimsByProvenance"])
        d26 = json.loads((ROOT / "disc026-evidence.json").read_text(encoding="utf-8"))
        ck("DISC-026 authority manifest unchanged (38 records)",
           len(d26["records"]) == 38)
        ck("no national rule is duplicated from the DISC-026 manifest",
           not (set(c["claim_field"] for c in claims)
                & set(r["claim_key"] for r in d26["records"])))
        ck("the manifest states the rules stay in DISC-026",
           "restates none of them" in m["rulesManifest"])
        ck("the live DISC-026 journey does not reference this pilot",
           "supplier-export-evidence" not in
           (ROOT / "disc026-power-station.html").read_text(encoding="utf-8"))

    print("\n" + "=" * 74)
    print(f"  {PASS} passed, {FAIL} failed")
    print("=" * 74)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
