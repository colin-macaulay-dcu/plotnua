#!/usr/bin/env python3
"""Stage 3D-B3 (founder approval 7 Nov 2026): Pineca PREMIUM S price-presentation hold.

Independent of the generator, the search builder and the explorer builder, this proof reads
the published files and confirms:
  P1  PREMIUM S stays discoverable (universe, search record by name, explorer row);
  P2  the historical EUR 8,678 appears on no public presentation surface (search record,
      explorer row, any published page), and the hold withholds the figure;
  P3  the product is excluded from budget matching;
  P4  it is excluded from euro price filters (the search record carries no price);
  P5  the Pineca supplier price range is exactly its other euro price-safe prices;
  P6  every other Pineca product is byte-identical in the universe and the search index
      to the Stage 3D-B2 production baseline;
  P7  the NOOK, ECC and Rayco holds and their published records are unchanged;
  P8  the Stage 3D-B1 search currency guards still pass (build-search-index.py --check);
  P9  the Garden Room Prices guide and its evidence still check, and the Stage 3D-B2
      evidence exclusion is intact.

  python3 atlas-tools/prove-pineca-premium-s-hold.py [--faults] [--base REV]
--faults plants the unsupported price back in each place and requires a refusal.
"""
import copy, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PID = "recej5DFaBD76ODlv"
FIG_RE = re.compile(r"8,678|8678|8 678")
BASE = "651a154"
for i, a in enumerate(sys.argv):
    if a == "--base" and i + 1 < len(sys.argv):
        BASE = sys.argv[i + 1]
PAGES = ["discovery-living-in-the-garden.html", "discovery-garden-retreat.html", "your-plot.html",
         "search.html", "garden-room-prices-ireland.html"]
PROTECTED_HOLDS = ("recDIcUb7S6pP8JCx",)          # Rayco; NOOK and ECC found by organisation


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def base(path):
    return json.loads(subprocess.run(["git", "show", "%s:%s" % (BASE, path)], cwd=ROOT,
                                     capture_output=True, check=True).stdout)


def explorer_rows(src):
    """Every explorer data row (JSON arrays inside the pn-mx-config blocks) naming PID."""
    rows = []
    for m in re.finditer(r'<script type="application/json" class="pn-mx-config"[^>]*>(.*?)</script>', src, re.S):
        def walk(x):
            if isinstance(x, list):
                if x and x[0] == PID:
                    rows.append(x)
                else:
                    for y in x:
                        walk(y)
            elif isinstance(x, dict):
                for y in x.values():
                    walk(y)
        walk(json.loads(m.group(1)))
    return rows


def gather():
    d = {"uni": load("garden-room-recommendation-universe-v1.json"),
         "search": load("search-index-v1.json"),
         "holds": load("atlas-tools/price-presentation-holds.json"),
         "reg": load("atlas-tools/cost-evidence-corrections.json"),
         "pages": {p: (ROOT / p).read_text(encoding="utf-8") for p in PAGES if (ROOT / p).exists()}}
    return d


def check(d):
    bad = []
    prods = {p["productId"]: p for p in d["uni"]["products"]}
    p = prods.get(PID)
    srec = {r["id"]: r for r in d["search"]["records"]}
    s = srec.get("prod-" + PID)
    hold = next((h for h in d["holds"]["holds"] if h["productId"] == PID), None)
    # P1
    if not p:
        bad.append("P1 PREMIUM S is not in the published universe")
    if not s or "PREMIUM S" not in s.get("title", "") + s.get("name", ""):
        bad.append("P1 no search record finds PREMIUM S by name")
    ex = [r for src in d["pages"].values() for r in explorer_rows(src)]
    if not ex:
        bad.append("P1 PREMIUM S has no Maker Explorer row")
    # P2
    if not hold or hold.get("figure") != "withheld" or hold.get("label") != "Price on request":
        bad.append("P2 the register does not withhold the figure under 'Price on request'")
    if p:
        ph = (p.get("priceEvidence") or {}).get("presentationHold") or {}
        if ph.get("figure") != "withheld" or ph.get("label") != "Price on request":
            bad.append("P2 the published record does not carry the withheld hold")
        if p.get("price") != 8678:
            bad.append("P2 the historical price was altered or removed from the record (it must be kept, withheld)")
        if p["priceEvidenceRef"]["lastPriceCheck"] != "2026-09-23" or p.get("priceStatus") != "Verified":
            bad.append("P2 Last Price Check or verification status was changed")
    if s and FIG_RE.search(json.dumps(s)):
        bad.append("P2 the search record carries 8,678")
    for r in ex:
        if FIG_RE.search(json.dumps(r, ensure_ascii=False)) or "Price on request" not in json.dumps(r, ensure_ascii=False):
            bad.append("P2 an explorer row shows 8,678 or lacks 'Price on request'")
    for name, src in d["pages"].items():
        if FIG_RE.search(src):
            bad.append("P2 %s contains 8,678" % name)
    # P3
    if p and (p.get("priceSafeForMatching") is not False or
              ((p.get("priceEvidence") or {}).get("presentationHold") or {}).get("matching") != "excluded"):
        bad.append("P3 PREMIUM S is not excluded from budget matching")
    # P4
    if s and ("price" in s or "priceBasis" in s):
        bad.append("P4 the search record carries a price, so euro filters can match it")
    # P5
    sup = srec.get("sup-pineca-ireland") or {}
    # every Pineca product price search publishes (all corpora); PREMIUM S must not be among them
    euro = [r["price"] for r in d["search"]["records"] if r.get("type") == "product"
            and r.get("organisation") == "Pineca Ireland" and "price" in r and r["id"] != "prod-" + PID]
    if sup.get("priceRange") != [min(euro), max(euro)]:
        bad.append("P5 the Pineca supplier range %s is not its other published prices %s" % (sup.get("priceRange"), [min(euro), max(euro)]))
    if 8678 in (sup.get("priceRange") or []):
        bad.append("P5 the Pineca supplier range uses 8,678")
    # P6 / P7
    bu, bs = d["base_uni"], d["base_search"]
    bprod = {x["productId"]: x for x in bu["products"]}
    bsrec = {r["id"]: r for r in bs["records"]}
    keep = [k for k, x in bprod.items() if x["organisation"] == "Pineca Ireland" and k != PID]
    keep += [k for k, x in bprod.items() if "NOOK" in x["organisation"] or x["organisation"] == "East Coast Carpentry"]
    keep += list(PROTECTED_HOLDS)
    for k in keep:
        if prods.get(k) != bprod.get(k):
            bad.append("P6/P7 published record %s changed" % k)
        if srec.get("prod-" + k) != bsrec.get("prod-" + k):
            bad.append("P6/P7 search record prod-%s changed" % k)
    bh = {h["productId"]: h for h in d["base_holds"]["holds"]}
    for k, h in bh.items():
        if next((x for x in d["holds"]["holds"] if x["productId"] == k), None) != h:
            bad.append("P7 hold %s changed" % k)
    # P9 (register part)
    ent = next((c for c in d["reg"]["corrections"] if c["id"] == "pineca-premium-s-unverifiable-2026-11-06"), None)
    if not ent or ent["products"][0].get("expect") != "evidenceExcluded" or ent["products"][0]["id"] != PID:
        bad.append("P9 the Stage 3D-B2 evidence exclusion is not intact")
    return bad


def tools():
    out = []
    for cmd, name in ((["python3", "atlas-tools/build-search-index.py", "--check"], "P8 search index --check (G7, G7b, G7c)"),
                      (["python3", "atlas-tools/build-garden-room-prices.py", "--check"], "P9 Garden Room Prices --check"),
                      (["python3", "atlas-tools/build-cluster1-cost-evidence.py", "--check"], "P9 cost evidence --check")):
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if r.returncode:
            out.append("%s failed: %s" % (name, (r.stdout + r.stderr).strip().splitlines()[-1:]))
    return out


def main():
    d = gather()
    d["base_uni"] = base("garden-room-recommendation-universe-v1.json")
    d["base_search"] = base("search-index-v1.json")
    d["base_holds"] = base("atlas-tools/price-presentation-holds.json")
    if "--faults" in sys.argv:
        if check(d):
            print("FAULTS · the real files must pass first"); return 1
        def f_search(x):
            r = next(r for r in x["search"]["records"] if r["id"] == "prod-" + PID); r["price"] = 8678
        def f_safe(x):
            next(p for p in x["uni"]["products"] if p["productId"] == PID)["priceSafeForMatching"] = True
        def f_hold(x):
            next(p for p in x["uni"]["products"] if p["productId"] == PID)["priceEvidence"].pop("presentationHold")
        def f_reg(x):
            x["holds"]["holds"] = [h for h in x["holds"]["holds"] if h["productId"] != PID]
        def f_fig(x):
            next(h for h in x["holds"]["holds"] if h["productId"] == PID)["figure"] = "shown"
        def f_page(x):
            k = "discovery-living-in-the-garden.html"
            x["pages"][k] = x["pages"][k].replace("Price on request. Pineca", "€8,678 incl. VAT. Pineca", 1)
        def f_range(x):
            r = next(r for r in x["search"]["records"] if r["id"] == "sup-pineca-ireland"); r["priceRange"] = [4018, 8678]
        def f_other(x):
            p = next(p for p in x["uni"]["products"] if p["productId"] == "recE1sTxnHbf6CDKI"); p["price"] = 12509
        def f_rayco(x):
            next(h for h in x["holds"]["holds"] if h["productId"] == "recDIcUb7S6pP8JCx")["figure"] = "shown"
        def f_starting(x):
            p = next(p for p in x["uni"]["products"] if p["productId"] == PID); p["priceType"] = "Starting From"; p["price"] = 8000
        def f_excl(x):
            x["reg"]["corrections"] = [c for c in x["reg"]["corrections"] if c["id"] != "pineca-premium-s-unverifiable-2026-11-06"]
        def f_gone(x):
            x["search"]["records"] = [r for r in x["search"]["records"] if r["id"] != "prod-" + PID]
        cases = [("price restored in the search record (euro filters)", f_search),
                 ("price made safe for budget matching", f_safe),
                 ("hold dropped from the published record", f_hold),
                 ("hold dropped from the register", f_reg),
                 ("figure shown instead of withheld", f_fig),
                 ("EUR 8,678 restored on the Maker Explorer", f_page),
                 ("supplier range built from 8,678", f_range),
                 ("another Pineca price disturbed", f_other),
                 ("Rayco hold weakened", f_rayco),
                 ("replacement starting-from price invented", f_starting),
                 ("Stage 3D-B2 evidence exclusion removed", f_excl),
                 ("product made undiscoverable in search", f_gone)]
        miss = 0
        for name, fn in cases:
            x = copy.deepcopy(d); fn(x); got = check(x)
            print("%s  %-52s %s" % ("CAUGHT" if got else "MISSED", name, (got or [""])[0][:110]))
            miss += not got
        print("PREMIUM S HOLD FAULTS · %d/%d caught" % (len(cases) - miss, len(cases)))
        return 1 if miss else 0
    bad = check(d) + tools()
    for b in bad:
        print("FAIL " + b)
    print("PREMIUM S HOLD · %s" % ("OK — P1-P9 pass" if not bad else "REFUSED — %d problem(s)" % len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
