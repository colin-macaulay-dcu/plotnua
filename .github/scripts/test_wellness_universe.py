#!/usr/bin/env python3
"""Tests for generate_wellness_universe.py and the published wellness universe.

  W1  an organisation with no rights record is HELD by the gate, never public
  W2  Atlas BLOCKED (recorded contradiction) holds a product on evidence
  W3  no product URL or no source excludes; missing price/availability holds
  W4  the firewall: Description, Notes and Standards prose never reach the file
  W5  the committed artefact: exactly 29 public OGNYX products, the 12 recorded
      contradictions held, gate declared, header counts reconcile
  W6  no OGNYX record carries a VAT, delivery, installation, health or
      lead-time statement; a price whose VAT is unknown says so
Run: python3 .github/scripts/test_wellness_universe.py
"""
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
GEN = HERE / "generate_wellness_universe.py"
ART = ROOT / "wellness-universe-v1.json"
fails = 0


def check(name, cond, detail=""):
    global fails
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, "" if cond else "  [%s]" % detail))
    fails += 0 if cond else 1


def prod(pid, org, **kw):
    f = {"Product Name": kw.get("name", "P " + pid), "Product Category": "Wellness / Sauna",
         "Organisation": [org], "Product URL": "https://example.invalid/" + pid,
         "Sources": ["recSRC0000000001"], "Description": "SECRET-DESCRIPTION",
         "Notes": "SECRET-NOTES"}
    f.update(kw.get("fields", {}))
    for k in kw.get("drop", []):
        f.pop(k, None)
    return {"id": pid, "fields": f}


def run(products, orgs):
    snap = {"source": "test", "products": products, "organisations": orgs,
            "pricing": [{"id": "recPR" + p["id"][5:], "fields": {"Product": [p["id"]], "Base Price": 1000,
                         "Currency": "EUR", "Status": "Verified", "Price Includes VAT": "Unknown"}}
                        for p in products if p["id"] != "recNOPRICE000001"],
            "availability": [{"id": "recAV" + p["id"][5:], "fields": {"Product": [p["id"]],
                              "Availability": "Available to Order"}} for p in products]}
    d = tempfile.mkdtemp()
    sp, op = pathlib.Path(d) / "s.json", pathlib.Path(d) / "u.json"
    sp.write_text(json.dumps(snap))
    r = subprocess.run([sys.executable, str(GEN), "--snapshot", str(sp), "--out", str(op)],
                       capture_output=True, text=True)
    if r.returncode:
        return None, r.stdout + r.stderr
    return json.loads(op.read_text()), op.read_text()


ORGS = [{"id": "recORGOGNYX00001", "fields": {"Organisation Name": "OGNYX"}},
        {"id": "recORGNEWCO00001", "fields": {"Organisation Name": "Brand New Saunas Ltd"}}]
P = [prod("recOKPRODUCT0001", "recORGOGNYX00001"),
     prod("recNEWCOPRODUCT1", "recORGNEWCO00001"),
     prod("recBLOCKED000001", "recORGOGNYX00001", fields={"Standards": "BLOCKED - contradiction SECRET-STD"}),
     prod("recNOURL00000001", "recORGOGNYX00001", drop=["Product URL"]),
     prod("recNOPRICE000001", "recORGOGNYX00001")]
u, text = run(P, ORGS)
if u is None:
    check("generator runs on a synthetic snapshot", False, text[:200]); sys.exit(1)
by = {r["id"]: r for r in u["products"]}
check("W1 an unrecorded organisation is held by the gate",
      by["recNEWCOPRODUCT1"]["publicVisibility"] == "HOLD"
      and by["recNEWCOPRODUCT1"]["holdReason"] == "publication-record-missing")
check("W1 and is not counted public", u["eligibleCount"] == 1, u["eligibleCount"])
check("W2 a recorded contradiction holds on evidence",
      by["recBLOCKED000001"]["qualification"]["state"] == "HELD")
check("W3 no product URL excludes", by["recNOURL00000001"]["qualification"]["state"] == "EXCLUDED")
check("W3 no price holds", by["recNOPRICE000001"]["qualification"]["state"] == "HELD")
check("W4 no Description, Notes or Standards prose leaks",
      not any(s in text for s in ("SECRET-DESCRIPTION", "SECRET-NOTES", "SECRET-STD")))

A = json.loads(ART.read_text(encoding="utf-8"))
pub = [r for r in A["products"] if r["qualification"]["state"] == "ELIGIBLE"
       and r["publicVisibility"] == "PUBLISHABLE"]
HELD = {"recursLY4Q1bFn4rh", "recX7IRnkD0PNDUhp", "recPEyrQcz5iHzaSM", "recB4sNoD3z8XpYgL",
        "rec3DxmwdTEumUwJ8", "recisLeRIkpgRCEFu", "recBgWBAcQwWLb9oT", "recJuwIn7bBk5mDQL",
        "recGyqJHsZTHoORPS", "recHEBSdisGB9AnmT", "recRPkVJdIB1mifpa", "recqZvNgpcTOUOe9D"}
check("W5 the artefact declares the publication gate", bool(A.get("publicationGate")))
check("W5 29 public products, all OGNYX", len(pub) == 29 and {r["organisation"] for r in pub} == {"OGNYX"},
      len(pub))
check("W5 header eligibleCount reconciles", A["eligibleCount"] == len(pub))
check("W5 exactly the 12 recorded contradictions are held",
      {r["id"] for r in A["products"] if r["qualification"]["state"] == "HELD"} == HELD)
check("W5 no held product is public", not (HELD & {r["id"] for r in pub}))
blob = json.dumps([{k: v for k, v in r.items() if k != "price"} for r in A["products"]]).lower()
check("W6 no VAT, delivery, installation, health or lead-time statement",
      not any(w in blob for w in ("vat", "delivery", "install", "health", "lead time", "therapeutic")))
check("W6 every unknown-VAT price says so",
      all("does not state whether it includes VAT" in r["price"]["basis"] for r in pub))
print("RESULT: %s" % ("PASS" if not fails else "%d FAILURE(S)" % fails))
sys.exit(1 if fails else 0)
