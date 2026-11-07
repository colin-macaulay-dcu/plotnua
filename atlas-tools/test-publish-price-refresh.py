#!/usr/bin/env python3
"""Negative tests for publish-price-refresh.py (Stage 3D-B2).

Each case plants one defect in a copy of the Atlas read-back (or the plan) and requires the
publisher to REFUSE before it writes anything. The unmodified read-back must pass the
pre-flight checks (it is run with --dry-run; the refusal cases stop before any build).

  python3 atlas-tools/test-publish-price-refresh.py --plan PLAN --snapshot READBACK
"""
import argparse, copy, json, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
TOOL = HERE / "publish-price-refresh.py"
RAYCO_ORG = 'Rayco Modular Homes'


def setf(snap, rid, field, value):
    for r in snap["pricing"]:
        if r["id"] == rid:
            r["fields"][field] = value
            return
    raise SystemExit("test setup: %s not in the read-back" % rid)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--snapshot", required=True)
    a = ap.parse_args()
    snap0 = json.loads(pathlib.Path(a.snapshot).read_text(encoding="utf-8"))
    plan0 = json.loads(pathlib.Path(a.plan).read_text(encoding="utf-8"))
    by = {i["productId"]: i for i in plan0["products"]}
    ilc = next(i for i in plan0["products"] if i["organisation"] == "Irish Log Cabins")
    corr = next(i for i in plan0["products"] if i["approvedPrice"] != i["publishedPrice"])
    std = next(i for i in plan0["products"] if i["organisation"] == "Hansa24 Group"
               and "approvedPriceType" not in i)
    sale = next(i for i in plan0["products"] if "approvedPriceType" in i)

    def s_price(s, p): setf(s, ilc["priceRecordIds"][0], "Base Price", ilc["approvedPrice"] + 100)
    def s_date(s, p): setf(s, ilc["priceRecordIds"][0], "Last Price Check", "2026-11-05")
    def s_promo(s, p): setf(s, corr["priceRecordIds"][0], "Base Price", corr["approvedPrice"] - 500)
    def s_old(s, p): setf(s, corr["priceRecordIds"][0], "Base Price", corr["publishedPrice"])
    def s_cur(s, p): setf(s, ilc["priceRecordIds"][0], "Currency", "GBP")
    def s_to(s, p): setf(s, corr["priceRecordIds"][0], "Price To", 99999)
    def s_status(s, p): setf(s, ilc["priceRecordIds"][0], "Status", "Partially Verified")
    def s_type(s, p): setf(s, std["priceRecordIds"][0], "Price Type", "Sale Price")
    def s_notype(s, p): setf(s, sale["priceRecordIds"][0], "Price Type", "Standard Price")
    def s_link(s, p): setf(s, ilc["priceRecordIds"][0], "Product", ["recAAAAAAAAAAAAAA"])
    def s_missing(s, p): s["pricing"] = [r for r in s["pricing"] if r["id"] != ilc["priceRecordIds"][0]]
    def p_unapproved(s, p):
        i = next(x for x in p["products"] if x["productId"] == ilc["productId"])
        i["approvedPrice"] = i["publishedPrice"] + 100
    def p_stale(s, p):
        i = next(x for x in p["products"] if x["productId"] == corr["productId"])
        i["publishedPrice"] = i["approvedPrice"]
    def p_hold(s, p):
        s["organisations"].append({"id": "recRaycoTestOrg01", "fields": {"Organisation Name": RAYCO_ORG}})
        p["products"].append({"productId": "recDIcUb7S6pP8JCx", "product": "Rayco", "organisation": RAYCO_ORG,
                              "priceRecordIds": ["rect2y3DTLysQfmdr"], "publishedPrice": 29500, "approvedPrice": 29500})

    cases = [
        ("unverified price change in Atlas (+EUR 100)", s_price, "does not match the approved refresh"),
        ("incorrect recheck date (2026-11-05)", s_date, "does not match the approved refresh"),
        ("promotional price replacing the regular price", s_promo, "does not match the approved refresh"),
        ("correction not applied in Atlas (old price kept)", s_old, "does not match the approved refresh"),
        ("unapproved currency drift (GBP)", s_cur, "does not match the approved refresh"),
        ("unapproved Price To drift", s_to, "does not match the approved refresh"),
        ("unapproved Status drift", s_status, "contradicts the published"),
        ("unapproved Price Type change", s_type, "does not match the approved refresh"),
        ("approved Sale Price not written in Atlas", s_notype, "does not match the approved refresh"),
        ("price record linked to another product", s_link, "does not match the approved refresh"),
        ("price record missing from the read-back", s_missing, "is not in the Atlas read"),
        ("plan approves a price the read-back does not carry", p_unapproved, "does not match the approved refresh"),
        ("plan's publishedPrice is not what is published", p_stale, "is not the published price"),
        ("refresh may not touch a presentation-held product", p_hold, "presentation hold"),
    ]
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="prf-test-"))
    fails = 0
    for name, mut, want in cases:
        s, p = copy.deepcopy(snap0), copy.deepcopy(plan0)
        mut(s, p)
        (tmp / "s.json").write_text(json.dumps(s), encoding="utf-8")
        (tmp / "p.json").write_text(json.dumps(p), encoding="utf-8")
        r = subprocess.run([sys.executable, str(TOOL), "--plan", str(tmp / "p.json"), "--snapshot",
                            str(tmp / "s.json"), "--dry-run"], capture_output=True, text=True, timeout=600)
        out = (r.stdout + r.stderr).strip().splitlines()
        last = next((l for l in out if l.startswith("REFUSED")), out[-1] if out else "")
        ok = r.returncode == 2 and last.startswith("REFUSED") and want in last
        fails += not ok
        print("%s  %-52s %s" % ("PASS" if ok else "FAIL", name, last[:150]))
    print("\n%d/%d refusal cases passed" % (len(cases) - fails, len(cases)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
