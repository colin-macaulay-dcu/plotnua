#!/usr/bin/env python3
"""Tests for generate_wellness_universe.py and the published wellness universe.

  W1  an organisation with no rights record is HELD by the gate, never public
  W2  Atlas BLOCKED (recorded contradiction) holds a product on evidence
  W3  no product URL or no source excludes; a missing verified price holds;
      missing availability does NOT hold (it is never emitted as a claim)
  W4  the firewall: Description, Notes and Standards prose never reach the file
  W5  the committed artefact: 35 public products from exactly OGNYX (29),
      Tanktribe (4) and Irish Sauna Company (2); the 12 recorded OGNYX
      contradictions held; gate declared; header counts reconcile
  W7  the legacy baseline is NOT honoured: an organisation it names (MyCabin.ie)
      with no rights record holds
  W8  every public record carries closed kind tokens; Price From is read when
      Base Price is absent
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
            "pricing": [{"id": "recPR" + p["id"][5:], "fields": dict(
                             {"Product": [p["id"]], "Currency": "EUR", "Status": "Verified",
                              "Price Type": "Starting From", "Price Includes VAT": "Unknown"},
                             **({"Price From": 700} if p["id"] == "recPRICEFROM0001" else {"Base Price": 1000}))}
                        for p in products if p["id"] != "recNOPRICE000001"],
            # Availability is deliberately absent: it must not decide anything.
            "availability": []}
    d = tempfile.mkdtemp()
    sp, op = pathlib.Path(d) / "s.json", pathlib.Path(d) / "u.json"
    sp.write_text(json.dumps(snap))
    r = subprocess.run([sys.executable, str(GEN), "--snapshot", str(sp), "--out", str(op)],
                       capture_output=True, text=True)
    if r.returncode:
        return None, r.stdout + r.stderr
    return json.loads(op.read_text()), op.read_text()


ORGS = [{"id": "recORGOGNYX00001", "fields": {"Organisation Name": "OGNYX"}},
        {"id": "recORGNEWCO00001", "fields": {"Organisation Name": "Brand New Saunas Ltd"}},
        {"id": "recORGMYCABIN001", "fields": {"Organisation Name": "MyCabin.ie"}}]
P = [prod("recOKPRODUCT0001", "recORGOGNYX00001", name="Outdoor Sauna for 4"),
     prod("recLEGACY0000001", "recORGMYCABIN001", name="Barrel Sauna"),
     prod("recPRICEFROM0001", "recORGOGNYX00001", name="Cold Plunge Tub"),
     prod("recNOKIND0000001", "recORGOGNYX00001", name="Garden Thing"),
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
check("W1 and is not counted public", u["eligibleCount"] == 2, u["eligibleCount"])
check("W3 missing availability does not hold", by["recOKPRODUCT0001"]["qualification"]["state"] == "ELIGIBLE")
check("W7 a legacy-baseline organisation with no rights record holds",
      by["recLEGACY0000001"]["holdReason"] == "publication-record-missing")
check("W8 Price From is read when Base Price is absent",
      by["recPRICEFROM0001"]["price"].get("amount") == 700)
check("W8 kinds come from the name when Atlas has no type",
      by["recOKPRODUCT0001"]["kinds"] == ["sauna"] and by["recPRICEFROM0001"]["kinds"] == ["cold-plunge"])
check("W8 an unclassifiable record holds",
      "kind-unclassified" in by["recNOKIND0000001"]["qualification"]["heldReasons"])
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
import collections
per = collections.Counter(r["organisation"] for r in pub)
check("W5 35 public products: OGNYX 29, Tanktribe 4, Irish Sauna Company 2",
      per == {"OGNYX": 29, "Tanktribe": 4, "Irish Sauna Company": 2}, dict(per))
check("W7 no organisation without its own PUBLISHABLE rights record is public",
      not ({r["organisation"] for r in pub} & {"MyCabin.ie", "Hansa24 Group", "Pineca Ireland",
           "Polaris Sauna", "TimberIN", "Sommarnöjen", "Auroom Wellness", "Cosy Cabins"}))
check("W8 every public record has closed kind tokens",
      all(r["kinds"] and set(r["kinds"]) <= {"sauna", "hot-tub", "cold-plunge", "combination"} for r in pub))
check("W5 header eligibleCount reconciles", A["eligibleCount"] == len(pub))
check("W5 the 12 recorded OGNYX contradictions are held",
      {r["id"] for r in A["products"] if r["qualification"]["state"] == "HELD"
       and r["organisation"] == "OGNYX"} == HELD)
check("W5 no held product is public", not (HELD & {r["id"] for r in pub}))
blob = json.dumps([{k: v for k, v in r.items() if k != "price"} for r in A["products"]]).lower()
check("W6 no VAT, delivery, installation, health or lead-time statement",
      not any(w in blob for w in ("vat", "delivery", "install", "health", "lead time", "therapeutic")))
check("W6 every price states its VAT position, saying so when the supplier does not",
      all(r["price"]["basis"].endswith((". The supplier does not state whether it includes VAT.",
                                        ", including VAT.", ", excluding VAT.")) for r in pub))
check("W6 Tanktribe's unknown-VAT prices say so",
      all("does not state whether it includes VAT" in r["price"]["basis"]
          for r in pub if r["organisation"] == "Tanktribe"))
check("W6 every public record has a verified EUR price",
      all(r["price"]["state"] == "VERIFIED_NUMERIC_PRICE" and r["price"]["currency"] == "EUR" for r in pub))
print("RESULT: %s" % ("PASS" if not fails else "%d FAILURE(S)" % fails))
sys.exit(1 if fails else 0)
