#!/usr/bin/env python3
"""Founder approval, 11 Nov 2026: six price-presentation holds (Garden Office Solutions x4,
Outdoor Living Nova 21.5m, Lugarde PSML2), figure withheld.

Independent of the generator and the builders, this proof reads the published files and
compares them with the production commit the release was built on (BASE):
  A1  exactly six new holds, each with its approved label and qualification, figure withheld;
  A2  each of the six stays published and discoverable (universe record, Search record by name,
      Maker Explorer row), keeps its historical price in the universe, and is held:
      priceState held, not safe for matching, no expiry;
  A3  none of the six carries a price in Search, and no Explorer row shows a figure;
  A4  supplier price ranges for the three suppliers equal the min/max of their other
      matching-safe euro prices (none left -> no range);
  A5  every other universe record and every other Search record is byte-identical to BASE,
      except the Garden Room Prices guide record (its meta description moves with the guide);
  A6  Search keeps the same number of records as BASE.

  python3 atlas-tools/prove-garden-room-availability-holds.py [--faults] [--base REV]
--faults plants four errors and requires each to be refused.
"""
import copy, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "95133784"   # production main when the release was built (prod/20261111-185757-9513378)
for i, a in enumerate(sys.argv):
    if a == "--base" and i + 1 < len(sys.argv):
        BASE = sys.argv[i + 1]
G = ("Not currently taking orders", "Garden Office Solutions says it is currently unable to take new orders. "
     "Its last published price is not shown or compared while it is not taking orders.")
N = ("Out of stock", "The retailer lists this product as temporarily out of stock. "
     "Its last listed price is not shown or compared until it is back in stock.")
L = ("Price requires verification", "The previously recorded price could not be verified against a current "
     "product page. A current quotation should be requested from the supplier.")
SIX = {"recKHXaApIugjOKti": G, "recUs4gexxlfkaiUj": G, "reciolethPMEn50gQ": G, "recUnUAWq0TWkNO5C": G,
       "recBVDyal8VGGVEZM": N, "reczxM0lggLXTBCdU": L}
ORGS = {"Garden Office Solutions": "sup-garden-office-solutions", "Lugarde": "sup-lugarde",
        "Outdoor Living (ModPod)": "sup-outdoor-living-modpod"}
GUIDE_RECORD = "poss-garden-room-prices-ireland"
UNI, IDX, HOLDS, LITG = ("garden-room-recommendation-universe-v1.json", "search-index-v1.json",
                         "atlas-tools/price-presentation-holds.json", "discovery-living-in-the-garden.html")


def git(path):
    return subprocess.run(["git", "show", "%s:%s" % (BASE, path)], cwd=ROOT, capture_output=True, check=True).stdout.decode()


def explorer(src):
    rows = {}
    for m in re.finditer(r'<script type="application/json" class="pn-mx-config"[^>]*>(.*?)</script>', src, re.S):
        def walk(x):
            if isinstance(x, list):
                if x and isinstance(x[0], str) and x[0] in SIX:
                    rows[x[0]] = x
                else:
                    for y in x:
                        walk(y)
            elif isinstance(x, dict):
                for y in x.values():
                    walk(y)
        walk(json.loads(m.group(1)))
    return rows


def state():
    rd = lambda p: (ROOT / p).read_text(encoding="utf-8")
    return {"uni": json.loads(rd(UNI)), "idx": json.loads(rd(IDX)), "holds": json.loads(rd(HOLDS)), "litg": rd(LITG),
            "b_uni": json.loads(git(UNI)), "b_idx": json.loads(git(IDX)), "b_holds": json.loads(git(HOLDS))}


def check(S):
    bad = []
    U = {p["id"]: p for p in S["uni"]["products"]}
    bU = {p["id"]: p for p in S["b_uni"]["products"]}
    R = {r["id"]: r for r in S["idx"]["records"]}
    bR = {r["id"]: r for r in S["b_idx"]["records"]}
    old = {h["productId"] for h in S["b_holds"]["holds"]}
    new = [h for h in S["holds"]["holds"] if h["productId"] not in old]
    # A1
    if sorted(h["productId"] for h in new) != sorted(SIX):
        bad.append("A1 new holds are %s, not exactly the six" % sorted(h["productId"] for h in new))
    for h in new:
        want = SIX.get(h["productId"])
        if want and (h.get("label"), h.get("qualification"), h.get("figure")) != (want[0], want[1], "withheld"):
            bad.append("A1 %s hold wording or figure is not the approved one" % h["productId"])
    # A2, A3
    ex = explorer(S["litg"])
    for pid, (lab, q) in SIX.items():
        p = U.get(pid)
        if not p:
            bad.append("A2 %s is not published" % pid); continue
        hold = (p.get("priceEvidence") or {}).get("presentationHold") or {}
        if p.get("priceState") != "held" or p.get("priceSafeForMatching") is not False or p.get("priceFreshUntil") \
                or hold.get("figure") != "withheld" or hold.get("label") != lab:
            bad.append("A2 %s is not held with its figure withheld" % pid)
        if p.get("price") != bU[pid].get("price"):
            bad.append("A2 %s historical price changed" % pid)
        r = R.get("prod-" + pid)
        if not r or r.get("name") != p["name"]:
            bad.append("A2 %s is not discoverable by name in Search" % pid)
        elif any(k in r for k in ("price", "fu", "priceBasis")):
            bad.append("A3 %s carries a price in Search" % pid)
        row = ex.get(pid)
        if not row or not str(row[-1]).startswith(lab + ".") or re.search(r"[\d€£$]", str(row[-1])):
            bad.append("A3 %s Explorer row does not show its label without a figure" % pid)
    # A4
    for org, rid in ORGS.items():
        ps = [p["price"] for p in U.values() if p.get("organisation") == org and p.get("priceSafeForMatching") is True
              and p.get("currency") == "EUR" and isinstance(p.get("price"), (int, float))]
        want = [min(ps), max(ps)] if ps else None
        if (R.get(rid) or {}).get("priceRange") != want:
            bad.append("A4 %s range %r is not its matching-safe euro prices %r" % (org, (R.get(rid) or {}).get("priceRange"), want))
    # A5, A6
    for pid, p in U.items():
        if pid not in SIX and p != bU.get(pid):
            bad.append("A5 universe record %s changed" % pid)
    if set(U) != set(bU):
        bad.append("A5 universe record set changed")
    for rid, r in R.items():
        if rid in {"prod-" + x for x in SIX} or rid in ORGS.values() or rid == GUIDE_RECORD:
            continue
        if r != bR.get(rid):
            bad.append("A5 Search record %s changed" % rid)
    if len(R) != len(bR) or set(R) != set(bR):
        bad.append("A6 Search holds %d records, BASE %d" % (len(R), len(bR)))
    return bad


def main():
    S = state()
    bad = check(S)
    for b in bad:
        print("FAIL", b)
    if "--faults" in sys.argv:
        faults = []
        f = copy.deepcopy(S); [r for r in f["idx"]["records"] if r["id"] == "prod-recKHXaApIugjOKti"][0]["price"] = 19950
        faults.append(("a held price back in Search", f))
        f = copy.deepcopy(S); [p for p in f["uni"]["products"] if p["id"] == "reczxM0lggLXTBCdU"][0]["priceSafeForMatching"] = True
        faults.append(("Lugarde entering matching", f))
        f = copy.deepcopy(S); [h for h in f["holds"]["holds"] if h["productId"] == "recBVDyal8VGGVEZM"][0]["label"] = "Sold out"
        faults.append(("unapproved label", f))
        f = copy.deepcopy(S); [p for p in f["uni"]["products"] if p["id"] == "recyMjzPUzBOvXD7Q"][0]["priceSafeForMatching"] = False
        faults.append(("an unrelated product (Nova 17.8m) changed", f))
        caught = 0
        for name, fs in faults:
            r = check(fs)
            print("  %s  planted %-42s -> %s" % ("REFUSED" if r else "MISSED ", name, r[0] if r else "-"))
            caught += bool(r)
        if caught != len(faults):
            bad.append("faults %d/%d" % (caught, len(faults)))
    print("AVAILABILITY HOLDS · %s" % ("OK — six held, figures withheld, nothing else changed" if not bad else "REFUSED — %d problem(s)" % len(bad)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
