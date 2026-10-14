#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REGRESSION TESTS — atlas-tools/publish-targeted-update.py

Every scenario runs the real tool, with the real generators, post-passes,
builders and validators, in a throwaway clone. Nothing here touches this
repository's working tree or Atlas, and nothing is pushed.

  R1   reproduces the ÖÖD House seven-product update (7cf158d) EXACTLY, from
       the pre-update commit 23bad4c, the committed ÖÖD snapshot and the 28
       Atlas Asset records
  T1   single supplier, organisation-wide, Atlas unchanged -> nothing to publish
  T2   single product + price change (garden) -> one record, search, explorer
  T3   multiple products (two ÖÖD feature changes)
  T4   removal / hold (recorded contradiction) -> counts, detail, search, explorer
  T5   image permission: asset no longer Approved; medium not recorded;
       grant withdrawn in the rights records
  T6   supplier objection: preview-request register (garden) and the
       public-information register (wellness)
  T7   wellness price change -> wellness record, search
  T8   category change Garden Rooms -> Wellness / Sauna (cross-Discovery)
  T9   cross-Discovery organisation and combination products
  T10  unrelated Atlas changes in the read, and unrelated published changes
  T11  unsafe publication refused: new products, Additional Home, dirty tree
  T12  explicit local commit: exact files, author, trailers, no push

  python3 atlas-tools/test-publish-targeted-update.py [--only T4,T5]
"""
import copy
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = "atlas-tools/publish-targeted-update.py"
OVERLAY = [TOOL, ".github/scripts/apply_authorised_imagery.py",
           ".github/scripts/generate_wellness_universe.py", "atlas-tools/approved-image-assets-v1.json",
           "atlas-tools/build-maker-explorer.py"]
OOD = "rec2URqKyVwlhHSBw"
OOD_SNAP = ROOT / "atlas-tools" / "ood-house-atlas-snapshot-2026-10-14.json"
SIGNATURE, MOBILE, MONOLITH = "recoQZlqmpfv3T5bz", "reczasgBzBbqP1lBg", "recPWKdUbLnAvXxmU"
GARDEN = "garden-room-recommendation-universe-v1.json"
WELLNESS = "wellness-universe-v1.json"
SEARCH = "search-index-v1.json"
ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None

FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("ok  " if ok else "FAIL", name, ("  — " + detail) if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


def git(repo, *a, check_=True):
    r = subprocess.run(["git"] + list(a), cwd=repo, capture_output=True, text=True)
    if check_ and r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr))
    return r.stdout


class Clone:
    def __init__(self, rev, overlay=OVERLAY):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="tu-test-"))
        self.p = self.tmp / "repo"
        subprocess.run(["git", "clone", "-q", "--shared", "--no-checkout", str(ROOT), str(self.p)], check=True)
        git(self.p, "checkout", "-q", rev)
        for f in overlay:
            (self.p / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / f, self.p / f)
        self.commit("overlay: the code under test")
        self.base = git(self.p, "rev-parse", "HEAD").strip()

    def commit(self, msg):
        git(self.p, "add", "-A")
        git(self.p, "-c", "user.name=test", "-c", "user.email=t@t", "commit", "-q",
            "--allow-empty", "-m", msg)

    def reset(self):
        git(self.p, "reset", "-q", "--hard", self.base)
        git(self.p, "clean", "-qfdx")
        last = self.p / ".git" / "targeted-update-last.json"
        if last.exists():
            last.unlink()

    def run(self, *args, snap=None):
        cmd = [sys.executable, str(self.p / TOOL)] + list(args)
        if snap is not None:
            sp = self.tmp / "snap.json"
            sp.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
            cmd += ["--snapshot", str(sp)]
        r = subprocess.run(cmd, cwd=self.p, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def j(self, f):
        return json.loads((self.p / f).read_text(encoding="utf-8"))

    def head(self, f):
        return json.loads(git(self.p, "show", "%s:%s" % (self.base, f)))

    def changed(self):
        return sorted(l[3:] for l in git(self.p, "status", "--porcelain", "--untracked-files=all").splitlines() if l.strip())

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


def ood_snapshot(with_assets=True):
    s = json.loads(OOD_SNAP.read_text(encoding="utf-8"))
    if with_assets:
        s["assets"] = json.loads((ROOT / "atlas-tools" / "approved-image-assets-v1.json")
                                 .read_text(encoding="utf-8"))["records"]
    return s


def scope_to(s, ids):
    s = copy.deepcopy(s)
    s["products"] = [p for p in s["products"] if p["id"] in ids]
    for t in ("pricing", "availability", "featureValues"):
        s[t] = [r for r in s[t] if set(r["fields"].get("Product") or []) <= set(ids)]
    if "assets" in s:
        s["assets"] = [a for a in s["assets"]
                       if {x["id"] for x in a["fields"]["Products"]} <= set(ids)]
    return s


def prod(s, pid):
    return next(p for p in s["products"] if p["id"] == pid)


def rec(doc, pid):
    for p in doc["products"]:
        if p.get("productId", p.get("id")) == pid:
            return p
    return None


def others_identical(a, b, skip):
    k = lambda p: p.get("productId", p.get("id"))
    A = {k(p): json.dumps(p, sort_keys=True) for p in a["products"] if k(p) not in skip}
    B = {k(p): json.dumps(p, sort_keys=True) for p in b["products"] if k(p) not in skip}
    return A == B


def search_rec(doc, rid):
    return next((r for r in doc["records"] if r["id"] == rid), None)


def explorer_cfg(clone, page):
    t = (clone.p / page).read_text(encoding="utf-8")
    m = re.search(r'id="mx-data">(.*?)</script>', t, re.S)
    return json.loads(m.group(1))


def wellness_snapshot(clone, org):
    """Atlas rows that make the wellness generator re-derive exactly the
    published records of one organisation (proved by T7's no-op first step)."""
    u = clone.j(WELLNESS)
    links = clone.j("atlas-tools/maker-product-links-v1.json")["links"]
    reg = clone.j("atlas-tools/public-information-listings.json")
    oid = next((r["organisation_record"] for r in reg["organisations"] if r["name"] == org),
               "recSYNTHORG" + "%06d" % (abs(hash(org)) % 10 ** 6))
    s = {"source": "synthetic: re-derived from the published wellness records of %s" % org,
         "products": [], "pricing": [], "availability": [], "organisations": [
             {"id": oid, "fields": {"Organisation Name": org}}], "featureValues": [], "features": []}
    for i, r in enumerate(x for x in u["products"] if x["organisation"] == org):
        url = r["productUrl"] or (links.get(r["id"]) or {}).get("url") or "https://synthetic.invalid/" + r["id"]
        f = {"Product Name": r["productName"], "Product Category": "Wellness / Sauna",
             "Organisation": [oid], "Product URL": url, "Sources": ["recSYNTHSOURCE01"]}
        if r["productCode"]:
            f["Product Code"] = r["productCode"]
        if r["productType"]:
            f["Product Type"] = r["productType"]
        if "recorded-contradiction" in r["qualification"]["heldReasons"]:
            f["Standards"] = "BLOCKED — recorded contradiction"
        s["products"].append({"id": r["id"], "fields": f})
        pr = r["price"]
        if pr["state"] == "VERIFIED_NUMERIC_PRICE":
            vat = "Yes" if pr["basis"].endswith("including VAT.") else \
                "No" if pr["basis"].endswith("excluding VAT.") else "Unknown"
            s["pricing"].append({"id": "recSYNTHPRICE%03d" % i, "fields": {
                "Product": [r["id"]], "Status": "Verified", "Base Price": pr["amount"], "Currency": "EUR",
                "Price Type": pr["type"], "Price Includes VAT": vat,
                "Evidence Scope": "Range-Level" if "for the range" in pr["basis"] else "Product-Specific"}})
    return s, oid


def ids_of(s):
    return [p["id"] for p in s["products"]]


# ============================================================== scenarios
def R1():
    print("\nR1  ÖÖD seven-product update reproduced exactly from 23bad4c")
    c = Clone("23bad4c", overlay=[TOOL, ".github/scripts/apply_authorised_imagery.py"])
    try:
        rc, out = c.run("--organisation", OOD, "--apply", snap=ood_snapshot())
        check("R1 tool applies", rc == 0, out[-800:])
        same = []
        for f in [GARDEN, "discovery-living-in-the-garden.html", "discovery-garden-retreat.html", WELLNESS] + \
                ["garden-room-detail-%s-v1.json" % k for k in (
                    "alternatives", "bestfor", "considerations", "planningconsiderations", "strengths",
                    "typicalhomeowner", "sources", "suppliers", "evidence", "index")]:
            want = git(c.p, "show", "7cf158d:" + f)
            got = (c.p / f).read_text(encoding="utf-8")
            if want != got:
                same.append(f)
        check("R1 universe, 10 detail files, explorer pages byte-identical to 7cf158d", not same, str(same))
        a = json.loads(git(c.p, "show", "7cf158d:" + SEARCH))
        b = c.j(SEARCH)
        for k in ("generated", "sourceCommit"):
            a.pop(k), b.pop(k)
        check("R1 search index identical to 7cf158d (except generated, sourceCommit)", a == b)
        pin = lambda t: re.search(r'BASE_UNIVERSE_SHA = "(\w+)"', t).group(1)
        check("R1 search pin re-frozen to 7cf158d's value",
              pin(git(c.p, "show", "7cf158d:atlas-tools/build-search-index.py")) ==
              pin((c.p / "atlas-tools/build-search-index.py").read_text(encoding="utf-8")))
        check("R1 census pin flagged for review, not hidden", "REVIEW prove-atlas-a" in out)
    finally:
        c.close()


def T1(c):
    print("\nT1  single supplier, organisation-wide, Atlas unchanged")
    rc, out = c.run("--organisation", OOD, "--dry-run", snap=ood_snapshot())
    check("T1 nothing to publish", rc == 0 and "NOTHING TO PUBLISH" in out, out[-600:])
    check("T1 dry run wrote nothing", c.changed() == [])


def T2(c):
    print("\nT2  single product, price change")
    s = scope_to(ood_snapshot(), [SIGNATURE])
    pr = next(r for r in s["pricing"] if SIGNATURE in r["fields"]["Product"])
    old_price = pr["fields"]["Base Price"]
    pr["fields"]["Base Price"] = old_price + 500
    rc, out = c.run("--organisation", OOD, "--product", SIGNATURE, "--dry-run", snap=s)
    check("T2 dry run succeeds and reports the price", rc == 0 and str(old_price + 500) in out, out[-900:])
    check("T2 dry run modifies no published file", c.changed() == [])
    rc, out = c.run("--organisation", OOD, "--product", SIGNATURE, "--apply", snap=s)
    check("T2 apply succeeds, validators pass", rc == 0 and "FAIL " not in out, out[-900:])
    u0, u1 = c.head(GARDEN), c.j(GARDEN)
    check("T2 the product carries the new price", rec(u1, SIGNATURE)["price"] == old_price + 500)
    check("T2 every other garden record byte-identical", others_identical(u0, u1, {SIGNATURE}))
    check("T2 imagery kept on the changed product (8 images)",
          len(rec(u1, SIGNATURE).get("imagerySet") or []) == len(rec(u0, SIGNATURE).get("imagerySet") or []) > 0)
    s1 = search_rec(c.j(SEARCH), "prod-" + SIGNATURE)
    check("T2 search product record updated", s1 and s1.get("price") == old_price + 500)
    check("T2 governed digest moved", u0["governedDigest"] != u1["governedDigest"])
    ch = c.changed()
    check("T2 report written beside the change",
          any(f.startswith("atlas-tools/targeted-updates/") for f in ch))
    check("T2 Garden Retreat untouched", WELLNESS not in ch and "discovery-garden-retreat.html" not in ch)
    c.reset()


def T3(c):
    print("\nT3  multiple products")
    s = scope_to(ood_snapshot(), [SIGNATURE, MOBILE])
    wid = next(f["id"] for f in s["features"] if f["fields"]["Feature Name"] == "Warranty")
    n = 0
    for r in s["featureValues"]:
        if wid in r["fields"].get("Feature", []):
            r["fields"]["Value Text"] = "WARRANTY 5 YEARS ON THE STRUCTURE — SUPPLIER-CONFIRMED (test)."
            n += 1
    rc, out = c.run("--organisation", OOD, "--product", SIGNATURE, "--product", MOBILE, "--apply", snap=s)
    check("T3 apply succeeds", rc == 0, out[-900:])
    u0, u1 = c.head(GARDEN), c.j(GARDEN)
    moved = [p["productId"] for p in u1["products"]
             if json.dumps(p, sort_keys=True) != json.dumps(rec(u0, p["productId"]), sort_keys=True)]
    check("T3 exactly the two named products changed", sorted(moved) == sorted([SIGNATURE, MOBILE]), str(moved))
    check("T3 warranty text published", "5 YEARS" in (rec(u1, MOBILE)["features"].get("warranty") or {}).get("text", ""))
    c.reset()


def T4(c):
    print("\nT4  removal / hold (recorded contradiction)")
    s = scope_to(ood_snapshot(), [MONOLITH])
    prod(s, MONOLITH)["fields"]["Verification Status"] = "Contradicted"
    rc, out = c.run("--organisation", OOD, "--product", MONOLITH, "--apply", snap=s)
    check("T4 apply succeeds", rc == 0, out[-900:])
    u0, u1 = c.head(GARDEN), c.j(GARDEN)
    check("T4 product removed from the universe", rec(u1, MONOLITH) is None)
    check("T4 eligible -1, excluded +1, source unchanged",
          (u1["eligibleCount"], u1["excludedCount"], u1["sourceGardenRoomCount"]) ==
          (u0["eligibleCount"] - 1, u0["excludedCount"] + 1, u0["sourceGardenRoomCount"]))
    check("T4 header still adds up", u1["sourceGardenRoomCount"] == u1["eligibleCount"] + u1["excludedCount"])
    check("T4 every other record byte-identical", others_identical(u0, u1, {MONOLITH}))
    ev = c.j("garden-room-detail-evidence-v1.json")
    check("T4 detail entries removed", MONOLITH not in ev["products"])
    sr = c.j(SEARCH)
    check("T4 search record removed", search_rec(sr, "prod-" + MONOLITH) is None)
    sup = next(r for r in sr["records"] if r["type"] == "supplier" and r["name"] == "ÖÖD House")
    check("T4 search supplier count 7 -> 6", sup["productCount"] == 6)
    cfg = explorer_cfg(c, "discovery-living-in-the-garden.html")
    check("T4 explorer garden-room figure moved by one",
          cfg["tabs"][0]["figures"]["products"] == len(u1["products"]))
    check("T4 report says REMOVED / HELD", "REMOVED / HELD" in out)
    c.reset()


def T5(c):
    print("\nT5  image permission changes")
    s = ood_snapshot()
    target_asset = "recQNpx3vprHXsh0p"                 # Signature House photograph 1
    a = next(x for x in s["assets"] if x["id"] == target_asset)
    a["fields"]["Publication Status"] = "Pending Review"
    b = next(x for x in s["assets"] if x["id"] == "recV5xOE7fjYvOUMD")   # Monolith photograph 1
    b["fields"]["Notes"] = "ÖÖD-supplied file. Required credit: ÖÖD House."  # medium not recorded
    rc, out = c.run("--organisation", OOD, "--apply", snap=s)
    check("T5 apply succeeds", rc == 0, out[-900:])
    u0, u1 = c.head(GARDEN), c.j(GARDEN)
    urls = lambda p: [i["url"] for i in (p.get("imagerySet") or ([p["imagery"]] if p.get("imagery") else []))]
    check("T5 the asset no longer Approved is gone",
          a["fields"]["Source URL"] not in urls(rec(u1, SIGNATURE)) and
          len(urls(rec(u1, SIGNATURE))) == len(urls(rec(u0, SIGNATURE))) - 1)
    check("T5 an asset whose medium is not recorded is refused",
          b["fields"]["Source URL"] not in urls(rec(u1, MONOLITH)) and "medium" in out)
    sig = rec(u1, SIGNATURE)
    check("T5 credit and link-back preserved on the remaining images",
          all(i["credit"].startswith("ÖÖD House") and i.get("linkBack") for i in sig["imagerySet"]))
    check("T5 photographer attribution preserved",
          any("· Photo: Valmarifoto" in i["credit"] for i in sig["imagerySet"]))
    check("T5 every non-ÖÖD record byte-identical",
          others_identical(u0, u1, {p["productId"] for p in u1["products"] if p["organisation"] == "ÖÖD House"}))
    c.reset()

    # the grant itself is withdrawn in the rights records (a founder act, committed first)
    recs = c.j("image-rights-records.json")
    for r in recs["records"]:
        if r.get("organisation_name") == "ÖÖD House":
            r["withdrawal_effective_at"] = "2026-10-14"
    (c.p / "image-rights-records.json").write_text(json.dumps(recs, indent=2, ensure_ascii=False) + "\n",
                                                   encoding="utf-8")
    subprocess.run([sys.executable, ".github/scripts/generate_image_rights_manifest.py"], cwd=c.p,
                   capture_output=True)
    c.commit("founder: ÖÖD grant withdrawn (test)")
    rc, out = c.run("--organisation", OOD, "--apply", snap=ood_snapshot())
    check("T5 withdrawal applies", rc == 0, out[-900:])
    u1 = c.j(GARDEN)
    check("T5 withdrawn grant: no ÖÖD imagery at all",
          not any(p.get("imagery") for p in u1["products"] if p["organisation"] == "ÖÖD House"))
    check("T5 withdrawn grant: other suppliers' imagery untouched",
          sum(1 for p in u1["products"] if p.get("imagery")) == 6)
    c.reset()


def T6(c):
    print("\nT6  supplier objections")
    reg = c.j("atlas-tools/preview-only-suppliers.json")
    reg["suppliers"].append({"name": "ÖÖD House", "imagery_mode": "none", "legal_name": "test",
                             "asked": "test objection"})
    (c.p / "atlas-tools/preview-only-suppliers.json").write_text(
        json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    c.commit("founder: ÖÖD asked for a preview first (test)")
    rc, out = c.run("--organisation", OOD, "--apply", snap=ood_snapshot())
    u0, u1 = c.head(GARDEN), c.j(GARDEN)
    check("T6 garden objection: apply succeeds", rc == 0, out[-1200:])
    check("T6 garden objection: no ÖÖD product published",
          not any(p["organisation"] == "ÖÖD House" for p in u1["products"]))
    check("T6 garden objection: blocker F +7, eligible -7",
          u1["exclusionSummaryByReason"].get("F") == u0["exclusionSummaryByReason"].get("F", 0) + 7
          and u1["eligibleCount"] == u0["eligibleCount"] - 7)
    check("T6 garden objection: organisation count -1", u1["organisationCount"] == u0["organisationCount"] - 1)
    sr = c.j(SEARCH)
    check("T6 garden objection: no ÖÖD supplier in search",
          not any(r["type"] == "supplier" and r["name"] == "ÖÖD House" for r in sr["records"]))
    c.reset()

    s, oid = wellness_snapshot(c, "Polaris Sauna")
    reg = c.j("atlas-tools/public-information-listings.json")
    row = next(r for r in reg["organisations"] if r["name"] == "Polaris Sauna")
    reg["organisations"].remove(row)
    reg["not_listed"].append({"name": "Polaris Sauna", "why": "objected (test)"})
    (c.p / "atlas-tools/public-information-listings.json").write_text(
        json.dumps(reg, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    c.commit("founder: Polaris objected (test)")
    rc, out = c.run("--organisation", oid, "--apply", snap=s)
    check("T6 wellness objection: apply succeeds", rc == 0, out[-1200:])
    w0, w1 = c.head(WELLNESS), c.j(WELLNESS)
    pol = [p for p in w1["products"] if p["organisation"] == "Polaris Sauna"]
    check("T6 wellness objection: all 20 Polaris records held",
          len(pol) == 20 and all(p["publicVisibility"] == "HOLD" for p in pol))
    check("T6 wellness objection: public count 120 -> 100", w1["eligibleCount"] == w0["eligibleCount"] - 20)
    check("T6 wellness objection: Polaris gone from Garden Retreat explorer",
          "Polaris" not in json.dumps(explorer_cfg(c, "discovery-garden-retreat.html")))
    check("T6 wellness objection: census pin surfaced (fails at base too: the register change itself moves it)",
          "PRE-EXISTING test_wellness_universe" in out or "REVIEW test_wellness_universe" in out,
          out[out.find("## Validation"):][:1500])
    c.reset()


def T7(c):
    print("\nT7  wellness price change")
    s, oid = wellness_snapshot(c, "Polaris Sauna")
    rc, out = c.run("--organisation", oid, "--dry-run", snap=s)
    check("T7 the re-derived Polaris read is a no-op (fixture fidelity)",
          rc == 0 and "NOTHING TO PUBLISH" in out, out[-900:])
    pid = s["products"][0]["id"]
    pr = next(r for r in s["pricing"] if pid in r["fields"]["Product"])
    new_price = pr["fields"]["Base Price"] + 111
    pr["fields"]["Base Price"] = new_price
    rc, out = c.run("--organisation", oid, "--apply", snap=s)
    check("T7 apply succeeds", rc == 0 and "FAIL " not in out, out[-900:])
    w0, w1 = c.head(WELLNESS), c.j(WELLNESS)
    check("T7 the wellness record carries the new price", rec(w1, pid)["price"]["amount"] == new_price)
    check("T7 every other wellness record byte-identical", others_identical(w0, w1, {pid}))
    check("T7 header re-derived, counts unchanged", w1["eligibleCount"] == w0["eligibleCount"])
    check("T7 provenance appended to snapshotScope", "targeted update" in w1["snapshotScope"])
    sr = search_rec(c.j(SEARCH), "prod-" + pid)
    check("T7 search updated", sr and sr.get("price") == new_price)
    check("T7 garden universe untouched", GARDEN not in c.changed())
    c.reset()


def T8(c):
    print("\nT8  category change (Garden Rooms -> Wellness / Sauna)")
    s = scope_to(ood_snapshot(), [MOBILE])
    prod(s, MOBILE)["fields"]["Product Category"] = "Wellness / Sauna"
    prod(s, MOBILE)["fields"]["Sources"] = ["recSYNTHSOURCE01"]
    rc, out = c.run("--organisation", OOD, "--product", MOBILE, "--apply", snap=s)
    check("T8 apply succeeds", rc == 0, out[-1200:])
    u0, u1 = c.head(GARDEN), c.j(GARDEN)
    w0, w1 = c.head(WELLNESS), c.j(WELLNESS)
    check("T8 garden: removed, source -1, eligible -1",
          rec(u1, MOBILE) is None and u1["sourceGardenRoomCount"] == u0["sourceGardenRoomCount"] - 1
          and u1["eligibleCount"] == u0["eligibleCount"] - 1)
    r = rec(w1, MOBILE)
    check("T8 wellness: record added, source +1", r is not None and
          w1["sourceCategoryCount"] == w0["sourceCategoryCount"] + 1)
    check("T8 wellness: the gate decides, not the tool (%s)" % (r and r["publicVisibility"]),
          r is not None and r["publicVisibility"] in ("HOLD", "PUBLISHABLE"))
    c.reset()


def T9(c):
    print("\nT9  cross-Discovery organisation and combination products")
    s, oid = wellness_snapshot(c, "TimberIN")
    combo = next(p["id"] for p in c.j(WELLNESS)["products"]
                 if p["organisation"] == "TimberIN" and "combination" in p["kinds"]
                 and p["publicVisibility"] == "PUBLISHABLE")
    s1 = scope_to(s, [combo])
    pr = next(r for r in s1["pricing"] if combo in r["fields"]["Product"])
    pr["fields"]["Base Price"] += 7
    rc, out = c.run("--organisation", oid, "--product", combo, "--apply", snap=s1)
    check("T9 combination product: apply succeeds", rc == 0, out[-900:])
    cfg = json.dumps(explorer_cfg(c, "discovery-garden-retreat.html"), ensure_ascii=False)
    check("T9 combination product listed under both tabs, once each", cfg.count(combo) == 2, str(cfg.count(combo)))
    c.reset()

    ps, pid_org = wellness_snapshot(c, "Pineca Ireland")
    rc, out = c.run("--organisation", pid_org, "--dry-run", snap=ps)
    check("T9 Pineca organisation-wide with only its wellness products is refused "
          "(its garden rooms are published too)", rc == 2 and "missing from the Atlas read" in out, out[-500:])
    one = ps["products"][0]["id"]
    rc, out = c.run("--organisation", pid_org, "--product", one, "--dry-run", snap=scope_to(ps, [one]))
    check("T9 Pineca, one named wellness product: allowed", rc == 0, out[-500:])
    c.reset()


def T10(c):
    print("\nT10 unrelated Atlas changes present")
    s = ood_snapshot()
    s["products"].append({"id": "recUNRELATED00001", "fields": {"Product Name": "Somebody else's room",
                          "Organisation": ["recOTHERORG000001"], "Product Category": "Garden Rooms"}})
    rc, out = c.run("--organisation", OOD, "--dry-run", snap=s)
    check("T10 another organisation's product in the read is refused", rc == 2 and "outside the approved scope" in out)
    s = ood_snapshot()
    s["organisations"].append({"id": "recOTHERORG000001", "fields": {"Organisation Name": "Other"}})
    rc, out = c.run("--organisation", OOD, "--dry-run", snap=s)
    check("T10 another organisation record in the read is refused", rc == 2)
    s = scope_to(ood_snapshot(), [SIGNATURE])
    s["pricing"].append({"id": "recSTRAYPRICE0001", "fields": {"Product": [MOBILE], "Base Price": 1}})
    rc, out = c.run("--organisation", OOD, "--product", SIGNATURE, "--dry-run", snap=s)
    check("T10 a price row for an out-of-scope product is refused", rc == 2 and "outside the approved scope" in out)
    rc, out = c.run("--organisation", OOD, "--product", SIGNATURE, "--dry-run", snap=ood_snapshot())
    check("T10 a read wider than --product is refused", rc == 2 and "does not match --product" in out)
    # an unrelated, already-committed change that would move another supplier's output
    f = c.p / ".github/scripts/apply_authorised_imagery.py"
    f.write_text(f.read_text(encoding="utf-8").replace(
        '"The Yard Box Whistler, a compact garden room"', '"The Yard Box Whistler (edited)"'), encoding="utf-8")
    c.commit("unrelated change to another supplier (test)")
    rc, out = c.run("--organisation", OOD, "--dry-run", snap=ood_snapshot())
    check("T10 an unrelated published change is refused by the boundary check",
          rc == 2 and "outside the scope would change" in out, out[-500:])
    c.reset()


def T11(c):
    print("\nT11 unsafe publication refused")
    base = scope_to(ood_snapshot(False), [SIGNATURE])
    new = copy.deepcopy(base)
    nid = "recTESTNEWPROD001"
    p = prod(new, SIGNATURE)
    p["id"], p["fields"]["Product Name"] = nid, "ÖÖD Test House"
    p["createdTime"] = "2026-10-14T20:00:00.000Z"
    for t in ("pricing", "availability", "featureValues"):
        for i, r in enumerate(new[t]):
            r["id"] = "recTN%s%03d" % (t[:6].upper(), i)
            r["fields"]["Product"] = [nid]
    full = ood_snapshot(False)
    for t in ("products", "pricing", "availability", "featureValues"):
        full[t] += copy.deepcopy(new[t])
    rc, out = c.run("--organisation", OOD, "--dry-run", snap=full)
    check("T11 an organisation-wide read never publishes a NEW product unasked",
          rc == 0 and "NOTHING TO PUBLISH" in out and "new to Living in the Garden" in out, out[-400:])
    new_old = copy.deepcopy(new)
    prod(new_old, nid)["createdTime"] = "2026-09-01T00:00:00.000Z"
    rc, out = c.run("--organisation", OOD, "--product", nid, "--dry-run", snap=new_old)
    check("T11 a named new product that predates the last refresh is refused",
          rc == 2 and "predates the last refresh" in out, out[-400:])
    rc, out = c.run("--organisation", OOD, "--product", nid, "--apply", snap=new)
    u0, u1 = c.head(GARDEN), c.j(GARDEN)
    check("T11 a named new product created after the refresh publishes, header exact",
          rc == 0 and rec(u1, nid) is not None
          and u1["sourceGardenRoomCount"] == u0["sourceGardenRoomCount"] + 1
          and u1["eligibleCount"] == u0["eligibleCount"] + 1, out[-600:])
    check("T11 the new product carries no imagery (no asset is linked to it)", not rec(u1, nid).get("imagery"))
    c.reset()
    ah = c.j("additional-home-universe-v1.json")["products"][0]
    s = {"products": [{"id": ah["id"], "fields": {"Product Name": ah["productName"], "Organisation": ["recAHORG000000001"],
                                                   "Product Category": "Additional Home"}}],
         "pricing": [], "availability": [], "featureValues": [], "features": [],
         "organisations": [{"id": "recAHORG000000001", "fields": {"Organisation Name": ah["organisation"]}}]}
    rc, out = c.run("--organisation", "recAHORG000000001", "--product", ah["id"], "--dry-run", snap=s)
    check("T11 an Additional Home product is refused (its own mechanism)",
          rc == 2 and "additional-home-universe-v1.json" in out, out[-400:])
    (c.p / GARDEN).write_text((c.p / GARDEN).read_text(encoding="utf-8") + " ", encoding="utf-8")
    rc, out = c.run("--organisation", OOD, "--dry-run", snap=ood_snapshot())
    check("T11 a dirty working tree is refused", rc == 2 and "uncommitted changes" in out)
    c.reset()


def T12(c):
    print("\nT12 explicit local commit")
    s = scope_to(ood_snapshot(), [SIGNATURE])
    next(r for r in s["pricing"] if SIGNATURE in r["fields"]["Product"])["fields"]["Base Price"] += 1
    rc, out = c.run("--organisation", OOD, "--product", SIGNATURE, "--apply", snap=s)
    check("T12 apply succeeds", rc == 0, out[-600:])
    applied = c.changed()
    (c.p / "README-test.txt").write_text("stray", encoding="utf-8")
    rc, out = c.run("--commit")
    check("T12 commit refuses an unrelated file in the tree", rc == 2 and "differs from what --apply wrote" in out)
    (c.p / "README-test.txt").unlink()
    rc, out = c.run("--commit")
    check("T12 commit succeeds", rc == 0 and "COMMITTED" in out and "Not pushed" in out, out[-600:])
    files = sorted(git(c.p, "show", "--name-only", "--format=", "HEAD").split())
    check("T12 the commit holds exactly the applied files", files == applied, "%s vs %s" % (files, applied))
    msg = git(c.p, "log", "-1", "--format=%an <%ae>%n%B")
    check("T12 author and trailers", msg.startswith("Colin MacAulay <kolin.macaulay@gmail.com>")
          and "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" in msg
          and "Claude-Session: https://claude.ai/code/session_" in msg)
    check("T12 nothing pushed (no remote touched)", "push" not in out.lower() or "not pushed" in out.lower())
    c.reset()


def main():
    tests = [("R1", R1)]
    head_tests = [("T1", T1), ("T2", T2), ("T3", T3), ("T4", T4), ("T5", T5), ("T6", T6),
                  ("T7", T7), ("T8", T8), ("T9", T9), ("T10", T10), ("T11", T11), ("T12", T12)]
    for name, fn in tests:
        if not ONLY or name in ONLY:
            fn()
    todo = [(n, f) for n, f in head_tests if not ONLY or n in ONLY]
    if todo:
        c = Clone("HEAD")
        try:
            for name, fn in todo:
                fn(c)
        finally:
            c.close()
    print("\n%s — %d failure(s)" % ("ALL PASS" if not FAILS else "FAILURES", len(FAILS)))
    for f in FAILS:
        print("   ", f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
