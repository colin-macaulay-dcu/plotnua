#!/usr/bin/env python3
"""PHASE 6C — the governed price contract, proved offline.

Every function under test is pure: it takes governed evidence and returns the
contract. No Atlas, no network. The guards must be able to FAIL -- the last
block reintroduces the exact defects this phase exists to prevent and proves
each one is caught.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import generate_garden_room_universe as G

P = F = 0
def ok(name, cond, detail=""):
    global P, F
    if cond: P += 1; print("    ok   %s" % name)
    else:    F += 1; print("    FAIL %s  %s" % (name, detail))

def rec(**kw):
    """A fake Airtable record whose cell() lookups return kw."""
    return {"id": kw.pop("id", "recTEST"), "fields": dict(kw)}

print("\n--- A · the closed lead-phrase vocabulary ---")
ok("the vocabulary has exactly the 8 measured tokens", len(G.INSTALL_LEAD_ERECTION) == 8,
   str(len(G.INSTALL_LEAD_ERECTION)))
ok("TURNKEY INSTALLATION INCLUDED -> INCLUDED",
   G.INSTALL_LEAD_ERECTION["TURNKEY INSTALLATION INCLUDED"] == "INCLUDED")
ok("DIY KIT ONLY -> EXCLUDED", G.INSTALL_LEAD_ERECTION["DIY KIT ONLY"] == "EXCLUDED")
ok("DIY OR INSTALLED -> UNKNOWN (both offered; the price is not attributed)",
   G.INSTALL_LEAD_ERECTION["DIY OR INSTALLED"] == "UNKNOWN")
ok("the em-dash variant still yields the base token",
   G.install_lead_phrase("TURNKEY INSTALLATION INCLUDED — FOUNDATIONS BY OTHERS")
   == "TURNKEY INSTALLATION INCLUDED")
ok("a full stop terminates the token",
   G.install_lead_phrase("DIY KIT ONLY. Self-assembly kit; no installation offered.")
   == "DIY KIT ONLY")
ok("an unrecognised phrase is NOT silently classified",
   G.install_lead_phrase("SOMETHING NOBODY MEASURED") not in G.INSTALL_LEAD_ERECTION)
ok("empty/None text yields no token", G.install_lead_phrase(None) is None
   and G.install_lead_phrase("") is None)
ok("no supplier marketing word is a rule on its own",
   not any(k in G.INSTALL_LEAD_ERECTION for k in ("TURNKEY", "PREMIUM", "LUXURY", "ALL-IN")))

print("\n--- B · the Phase 4 taxonomy is a pure function of the axes ---")
cases = [
  ({"erection":"EXCLUDED","delivery":"EXCLUDED","siteWorks":"UNKNOWN"},  "EX_WORKS"),
  ({"erection":"INCLUDED","delivery":"UNKNOWN","siteWorks":"INCLUDED"},  "ERECTED_WITH_SERVICES"),
  ({"erection":"INCLUDED","delivery":"UNKNOWN","siteWorks":"EXCLUDED"},  "ERECTED_SERVICES_EXCLUDED"),
  ({"erection":"INCLUDED","delivery":"UNKNOWN","siteWorks":"UNKNOWN"},   "ERECTED_SERVICES_UNKNOWN"),
  ({"erection":"EXCLUDED","delivery":"INCLUDED","siteWorks":"UNKNOWN"},  "DELIVERED_SHELL"),
  ({"erection":"EXCLUDED","delivery":"UNKNOWN","siteWorks":"UNKNOWN"},   "KIT_SELF_ASSEMBLY"),
  ({"erection":"UNKNOWN","delivery":"UNKNOWN","siteWorks":"UNKNOWN"},    "UNKNOWN"),
]
for ax, want in cases:
    ok("%s/%s/%s -> %s" % (ax["erection"][:3], ax["siteWorks"][:3], ax["delivery"][:3], want),
       G.derive_basis_class(ax) == want, G.derive_basis_class(ax))
ok("the derivation is deterministic", all(G.derive_basis_class(a) == G.derive_basis_class(a)
                                          for a, _ in cases))

print("\n--- C · UNKNOWN basis fails closed but does NOT invalidate a real price ---")
r = rec(**{"Base Price": 12000, "Currency": "EUR", "Status": "Verified"})
g = G.price_governance(r, "adjudicated", [r], [r], {})
ok("no installation evidence -> basis UNKNOWN", g["priceBasisClass"] == "UNKNOWN")
ok("confidence says why: NO_BASIS_STATED", g["priceBasisConfidence"] == "NO_BASIS_STATED")
ok("the price SURVIVES an unknown basis", g["priceSafeForMatching"] is True)

print("\n--- D · price safety is derived from governed evidence ---")
r2 = rec(**{"Base Price": 9000, "Currency": "EUR", "Status": "Draft"})
ok("a Draft price is NOT safe for matching",
   G.price_governance(r2, "adjudicated", [r2], [r2], {})["priceSafeForMatching"] is False)
amb = G.price_governance(None, "ambiguous", [r, r2], [r, r2], {})
ok("an ambiguous product is not safe", amb["priceSafeForMatching"] is False)
ok("ambiguity is reported as CONFLICTED", amb["priceBasisConfidence"] == "CONFLICTED")
ok("an ambiguous product still reports its candidate records",
   amb["priceEvidenceRef"]["candidateCount"] == 2)
nop = G.price_governance(None, "missing", [], [], {})
ok("NO PRICE is reported as NO_PRICE, never as an unsafe price",
   nop["priceBasisConfidence"] == "NO_PRICE" and nop["priceSafeForMatching"] is False)

print("\n--- E · range floor, VAT, provenance ---")
rf = rec(**{"Base Price": 27090, "Price To": 36420, "Currency": "EUR", "Status": "Verified",
            "Price Includes VAT": "Yes"})
g = G.price_governance(rf, "adjudicated", [rf], [rf], {})
ok("a published ceiling above the floor renders From", g["priceIsRangeFloor"] is True)
ok("VAT Yes is carried", g["vatStatus"] == "Yes")
sf = rec(**{"Base Price": 36500, "Currency": "EUR", "Status": "Verified",
            "Price Type": "Starting From"})
ok("Starting From alone is a range floor",
   G.price_governance(sf, "adjudicated", [sf], [sf], {})["priceIsRangeFloor"] is True)
flat = rec(**{"Base Price": 9995, "Currency": "EUR", "Status": "Verified"})
ok("a flat price is NOT a range floor",
   G.price_governance(flat, "adjudicated", [flat], [flat], {})["priceIsRangeFloor"] is False)
for raw, want in (("Unknown","Unknown"), (None,"Unknown"), ("No","No"),
                  ("Excluding VAT","No"), ("13.5%","Unknown")):
    rv = rec(**{"Base Price": 100, "Currency": "EUR", "Status": "Verified",
                "Price Includes VAT": raw})
    ok("VAT %r -> %s (never inferred)" % (raw, want),
       G.price_governance(rv, "adjudicated", [rv], [rv], {})["vatStatus"] == want)
ok("vatRate is ALWAYS null — no rate is manufactured from Notes",
   all(G.price_governance(x, "adjudicated", [x], [x], {})["vatRate"] is None
       for x in (r, r2, rf, sf, flat)))

print("\n--- F · no curator prose may reach the contract ---")
pr = rec(**{"Base Price": 100, "Currency": "EUR", "Status": "Verified",
            "Known Exclusions": "SECRET CURATOR PROSE ABOUT DELIVERY",
            "Notes": "MORE SECRET PROSE"})
blob = repr(G.price_governance(pr, "adjudicated", [pr], [pr],
            {"installationModel": {"text": "DIY KIT ONLY. Long curator sentence that must not leak."}}))
ok("Known Exclusions does not reach the contract", "SECRET CURATOR PROSE" not in blob)
ok("Notes does not reach the contract", "MORE SECRET PROSE" not in blob)
ok("the installation prose does not reach the contract", "Long curator sentence" not in blob)
ok("only the governed lead token is carried",
   G.price_governance(pr, "adjudicated", [pr], [pr],
     {"installationModel": {"text": "DIY KIT ONLY. Long curator sentence."}}
   )["priceEvidenceRef"]["basisLeadPhrase"] == "DIY KIT ONLY")

print("\n--- G · priceRecordIds is plural and provenance survives ---")
a = rec(id="recA", **{"Base Price": 100, "Currency": "EUR", "Status": "Verified"})
b = rec(id="recB", **{"Base Price": 100, "Currency": "EUR", "Status": "Verified"})
g = G.price_governance(a, "adjudicated", [a, b], [a, b], {})
ok("priceRecordIds carries every candidate", g["priceRecordIds"] == ["recA", "recB"])
ok("priceRecordIdsAvailable counts the rows Atlas holds", g["priceRecordIdsAvailable"] == 2)
ok("the adjudication state survives", g["priceEvidenceRef"]["adjudication"] == "adjudicated")

print("\n--- H · governedDigest detects post-generation mutation ---")
base = [{"productId": "p1", "price": 100, "currency": "EUR", "priceStatus": "Verified",
         "priceSafeForMatching": True, "priceRecordIds": ["r1"]},
        {"productId": "p2", "price": 200, "currency": "EUR", "priceStatus": "Verified",
         "priceSafeForMatching": True, "priceRecordIds": ["r2"]}]
d0 = G.governed_digest(base)
ok("the digest is stable across runs", d0 == G.governed_digest(base))
ok("the digest ignores product ORDER", d0 == G.governed_digest(list(reversed(base))))
mut = [dict(base[0], price=101), base[1]]
ok("changing a governed price CHANGES the digest", G.governed_digest(mut) != d0)
mut2 = [dict(base[0], priceSafeForMatching=False), base[1]]
ok("flipping priceSafeForMatching CHANGES the digest", G.governed_digest(mut2) != d0)
mut3 = [dict(base[0], qualificationCaveats=["anything"]), base[1]]
ok("a NON-governed field does not change the digest", G.governed_digest(mut3) == d0)

print("\n--- I · GUARD CAPABILITY: reintroduce each defect, prove it is caught ---")
saved = dict(G.INSTALL_LEAD_ERECTION)
G.INSTALL_LEAD_ERECTION["TURNKEY"] = "INCLUDED"          # marketing word as a rule
ok("REINTRODUCED a marketing token: the vocabulary guard would now fail",
   any(k in G.INSTALL_LEAD_ERECTION for k in ("TURNKEY", "PREMIUM")) and len(G.INSTALL_LEAD_ERECTION) != 8)
G.INSTALL_LEAD_ERECTION.clear(); G.INSTALL_LEAD_ERECTION.update(saved)
ok("vocabulary restored to the measured 8", len(G.INSTALL_LEAD_ERECTION) == 8)
savedvat = dict(G.VAT_MAP)
G.VAT_MAP["13.5%"] = "Yes"                                # inferring VAT from a rate
rv = rec(**{"Base Price": 100, "Currency": "EUR", "Status": "Verified", "Price Includes VAT": "13.5%"})
ok("REINTRODUCED VAT inference: the VAT guard would now fail",
   G.price_governance(rv, "adjudicated", [rv], [rv], {})["vatStatus"] == "Yes")
G.VAT_MAP.clear(); G.VAT_MAP.update(savedvat)
ok("VAT non-inference restored",
   G.price_governance(rv, "adjudicated", [rv], [rv], {})["vatStatus"] == "Unknown")

print("\n" + "=" * 78)
print("  %d passed, %d failed" % (P, F))
print("=" * 78)
sys.exit(1 if F else 0)
