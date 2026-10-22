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
  W9  productUrl is emitted for public records only (https), never for held ones
  W6  no OGNYX record carries a VAT, delivery, installation, health or
      lead-time statement; a price whose VAT is unknown says so
  W10 the public-information basis (founder decision 14 Oct 2026): a listed
      maker with no rights record publishes text only; an unlisted one
      holds; a rights record always wins over the register; a product whose
      page is not VERIFIED holds; a register row claiming permission,
      imagery or an objection refuses the build
  W11 the committed artefact: 120 public from 7 makers (35 on supplier
      permission, 85 on the public-information basis); MyCabin, Cosy Cabins,
      Sommarnöjen and Auroom held; the five 14 Oct contradictions held;
      every public-information product has a VERIFIED page; TimberIN's
      combination buildings are one record each, under sauna AND hot tub
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

# W10 — the register, exercised in-process against synthetic rows.
import importlib.util
def gen_module(register_doc, links_doc):
    spec = importlib.util.spec_from_file_location("wgen", GEN)
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(HERE))
    spec.loader.exec_module(m)
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "r.json").write_text(json.dumps(register_doc)); (d / "l.json").write_text(json.dumps(links_doc))
    m.REGISTER, m.LINKS = d / "r.json", d / "l.json"
    return m
ROW = {"name": "Brand New Saunas Ltd", "basis": "PUBLIC_INFORMATION", "supplier_permission": False,
       "imagery": "none", "objection": "none recorded", "objection_check": "searched",
       "maker_identity": "Atlas organisation"}
DEC = {"decision": {"scope": "Wellness / Sauna"}}
m = gen_module(dict(DEC, organisations=[ROW]), {"links": {}})
check("W10 a listed maker with no rights record publishes on the public-information basis",
      m.wellness_hold("Brand New Saunas Ltd") == (None, "PUBLIC_INFORMATION"))
check("W10 an unlisted maker with no rights record still holds",
      m.wellness_hold("Somebody Else Ltd") == ("publication-record-missing", None))
m = gen_module(dict(DEC, organisations=[dict(ROW, name="OGNYX")]), {"links": {}})
check("W10 a rights record always wins over the register",
      m.wellness_hold("OGNYX")[1] == "SUPPLIER_PERMISSION")
m2 = gen_module(dict(DEC, organisations=[dict(ROW, name="Cosy Cabins")]), {"links": {}})
check("W10 listing one maker never lets an unlisted maker through",
      m2.wellness_hold("MyCabin.ie")[0] == "publication-record-missing")
for bad, label in ((dict(ROW, supplier_permission=True), "claims permission"),
                   (dict(ROW, imagery="selected"), "claims imagery"),
                   (dict(ROW, objection="asked not to be listed"), "records an objection")):
    mb = gen_module(dict(DEC, organisations=[bad]), {"links": {}})
    try:
        mb.public_information_register(); refused = False
    except SystemExit:
        refused = True
    check("W10 a register row that %s refuses the build" % label, refused)
m = gen_module(dict(DEC, organisations=[ROW]), {"links": {"recX": {"state": "VERIFIED", "url": "https://a.ie/x"}}})
check("W10 a product page counts only when VERIFIED at the record's own URL",
      m.page_verified("recX", "https://a.ie/x") and not m.page_verified("recX", "https://a.ie/y")
      and not m.page_verified("recY", "https://a.ie/x"))

A = json.loads(ART.read_text(encoding="utf-8"))
pub = [r for r in A["products"] if r["qualification"]["state"] == "ELIGIBLE"
       and r["publicVisibility"] == "PUBLISHABLE"]
HELD = {"recursLY4Q1bFn4rh", "recX7IRnkD0PNDUhp", "recPEyrQcz5iHzaSM", "recB4sNoD3z8XpYgL",
        "rec3DxmwdTEumUwJ8", "recisLeRIkpgRCEFu", "recBgWBAcQwWLb9oT", "recJuwIn7bBk5mDQL",
        "recGyqJHsZTHoORPS", "recHEBSdisGB9AnmT", "recRPkVJdIB1mifpa", "recqZvNgpcTOUOe9D"}
check("W5 the artefact declares the publication gate", bool(A.get("publicationGate")))
import collections
per = collections.Counter(r["organisation"] for r in pub)
check("W11 120 public products: OGNYX 29, Tanktribe 4, Irish Sauna Company 2, Pineca 34, "
      "Hansa24 25, Polaris 20, TimberIN 6",
      per == {"OGNYX": 29, "Tanktribe": 4, "Irish Sauna Company": 2, "Pineca Ireland": 34,
              "Hansa24 Group": 25, "Polaris Sauna": 20, "TimberIN": 6}, dict(per))
REG = json.loads((ROOT / "atlas-tools" / "public-information-listings.json").read_text(encoding="utf-8"))
listed = {o["name"] for o in REG["organisations"]}
rights = {r["organisation_name"] for r in json.loads((ROOT / "image-rights-records.json")
          .read_text(encoding="utf-8"))["records"]}
check("W7/W11 every public maker is either on its own rights record or on the register, never both",
      all((r["organisation"] in rights) != (r["organisation"] in listed) for r in pub)
      and not (listed & rights), sorted(listed & rights))
check("W11 basis matches: supplier permission for rights-record makers, public information otherwise",
      all(r["listingBasis"] == ("SUPPLIER_PERMISSION" if r["organisation"] in rights else "PUBLIC_INFORMATION")
          for r in pub) and A["listingBasisCounts"] == {"SUPPLIER_PERMISSION": 35, "PUBLIC_INFORMATION": 85})
check("W11 MyCabin, Cosy Cabins, Sommarnöjen and Auroom Wellness are not public",
      not ({r["organisation"] for r in pub} & {"MyCabin.ie", "Cosy Cabins", "Sommarnöjen", "Auroom Wellness"}))
BLOCKERS = {"rectXEcIBSgq92QFn", "recQT6LbDFnfrssoi", "recu1Y1kHvG90k7GL", "recZcGYcwzf2Fa1re",
            "recStbWNjbPyrxVIL"}
byid = {r["id"]: r for r in A["products"]}
check("W11 the five 14 Oct contradictions are held on evidence",
      all(byid[i]["qualification"]["state"] == "HELD"
          and "recorded-contradiction" in byid[i]["qualification"]["heldReasons"] for i in BLOCKERS))
LINKS = json.loads((ROOT / "atlas-tools" / "maker-product-links-v1.json").read_text(encoding="utf-8"))["links"]
check("W11 every public-information product has a VERIFIED page at its own URL",
      all(LINKS.get(r["id"], {}).get("state") == "VERIFIED" and LINKS[r["id"]]["url"] == r["productUrl"]
          for r in pub if r["listingBasis"] == "PUBLIC_INFORMATION"))
combo = [r for r in pub if "combination" in r["kinds"]]
check("W11 TimberIN's four combination buildings: one record each, under sauna and hot tub",
      len(combo) == 4 and all(r["organisation"] == "TimberIN" and {"sauna", "hot-tub"} <= set(r["kinds"])
                              for r in combo) and len({r["id"] for r in pub}) == len(pub))
check("W11 no record claims Irish availability",
      all(r["irish"] == {"state": "UNCONFIRMED"} for r in A["products"]))
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
REG = json.loads((ROOT / "atlas-tools" / "price-currency-corrections.json").read_text(encoding="utf-8"))
CORR = {c["id"]: c for c in REG["corrections"]}
check("W6 every public record has a verified EUR price, or the supplier's own published currency where the "
      "founder's currency register lists it (22 Oct 2026)",
      all(r["price"]["state"] == "VERIFIED_NUMERIC_PRICE" and r["price"]["currency"] ==
          (CORR[r["id"]]["publishedCurrency"] if r["id"] in CORR else "EUR") for r in pub))
check("W10 the currency register names exactly the six TimberIN records, and only GBP",
      len(CORR) == 6 and all(c["organisation"] == "TimberIN" and c["publishedCurrency"] == "GBP"
                             and c["atlasCurrency"] == "EUR" for c in CORR.values()))
check("W10 a register-listed price keeps the evidenced amount and type: nothing converted",
      all(r["price"]["amount"] == CORR[r["id"]]["amount"] and r["price"]["type"] == CORR[r["id"]]["priceType"]
          for r in A["products"] if r["id"] in CORR))
check("W10 a register-listed price keeps Atlas's VAT position (not stated): no VAT treatment assumed",
      all(r["price"]["basis"].endswith(", in pounds sterling as the supplier publishes it. "
                                       "The supplier does not state whether it includes VAT.")
          for r in A["products"] if r["id"] in CORR))
check("W10 no other record carries a non-EUR price",
      all(r["price"].get("currency") in (None, "EUR") for r in A["products"] if r["id"] not in CORR))
sys.path.insert(0, str(HERE))
import generate_wellness_universe as GW  # noqa: E402
FAKE = {"recFAKE000000001": {"id": "recFAKE000000001", "amount": 1000, "priceType": "Standard Price",
                              "atlasCurrency": "EUR", "publishedCurrency": "GBP"}}
row = lambda cur, amt=1000: [{"fields": {"Status": "Verified", "Base Price": amt, "Currency": cur,
                                         "Price Type": "Standard Price", "Price Includes VAT": "Unknown"}}]
pg = GW.price_of(row("EUR"), "recFAKE000000001", FAKE)
check("W10 generator: a listed EUR-recorded price comes out in the published currency, same amount, same VAT sentence",
      pg["currency"] == "GBP" and pg["amount"] == 1000 and pg["basis"] ==
      "Published price, in pounds sterling as the supplier publishes it. The supplier does not state whether it includes VAT.")
check("W10 generator: a GBP-recorded Atlas row for a listed record gives the same result (Atlas later corrected)",
      GW.price_of(row("GBP"), "recFAKE000000001", FAKE) == pg)
check("W10 generator: an unlisted GBP row is still refused",
      GW.price_of(row("GBP"), "recOTHER00000001", FAKE) == {"state": "PRICE_NOT_ESTABLISHED"})
check("W10 generator: an unlisted EUR row is unchanged",
      GW.price_of(row("EUR"), "recOTHER00000001", FAKE)["currency"] == "EUR")
try:
    GW.price_of(row("EUR", 1200), "recFAKE000000001", FAKE)
    moved = False
except SystemExit:
    moved = True
check("W10 generator: refuses when the Atlas amount no longer matches the evidenced amount", moved)
check("W9 a product URL is published only for public records, and only as https",
      all((r["productUrl"] is None) or (r in pub and r["productUrl"].startswith("https://"))
          for r in A["products"]) and all(r["productUrl"] for r in pub))
print("RESULT: %s" % ("PASS" if not fails else "%d FAILURE(S)" % fails))
sys.exit(1 if fails else 0)
