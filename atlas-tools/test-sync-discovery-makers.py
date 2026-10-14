#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for atlas-tools/sync-discovery-makers.py (founder brief, 14 Oct 2026,
section 10). Every test runs in a THROWAWAY CLONE of this repository; the
working tree is never touched. Universes are changed the way their generators
would change them: records edited, headers re-derived by the generator's own
summarise(), so the explorer's G1 count guard still has to hold.

  python3 atlas-tools/test-sync-discovery-makers.py
"""
import copy
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
NEW_FILES = ("atlas-tools/sync-discovery-makers.py", "atlas-tools/discovery-maker-snapshot-v1.json",
             "atlas-tools/test-sync-discovery-makers.py")
RESULTS = []


def check(label, ok, detail=""):
    RESULTS.append((label, bool(ok)))
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label, ("  · " + detail) if detail and not ok else ""))


def sh(args, cwd, ok=(0,)):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True)
    return r


class Clone:
    def __init__(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="sync-test-"))
        self.root = self.tmp / "repo"
        subprocess.run(["git", "clone", "-q", "--local", str(ROOT), str(self.root)], check=True)
        for f in NEW_FILES:                                   # uncommitted work under test
            if (ROOT / f).exists():
                shutil.copy2(ROOT / f, self.root / f)
        subprocess.run(["git", "-C", str(self.root), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t",
                        "commit", "-qm", "test base", "--allow-empty"], check=True)

    def tool(self, *args):
        return sh([sys.executable, "atlas-tools/sync-discovery-makers.py", *args], self.root)

    def j(self, rel):
        return json.loads((self.root / rel).read_text(encoding="utf-8"))

    def w(self, rel, data):
        (self.root / rel).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def text(self, rel):
        return (self.root / rel).read_text(encoding="utf-8")

    def module(self):
        spec = importlib.util.spec_from_file_location("sync_%d" % id(self), self.root / NEW_FILES[0])
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def wellness(self, edit):
        """Edit the wellness universe's records, then re-derive its header with
        the generator's own summarise()."""
        U = self.j("wellness-universe-v1.json")
        edit(U["products"])
        sys.path.insert(0, str(self.root / ".github" / "scripts"))
        spec = importlib.util.spec_from_file_location("gw_%d" % id(U), self.root / ".github/scripts/generate_wellness_universe.py")
        g = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(g)
        sys.path.pop(0)
        U.update(g.summarise(U["products"], U["snapshotSha256"], U["snapshotScope"], U["sourceCategoryCount"]))
        self.w("wellness-universe-v1.json", U)

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


def public_sauna(rows):
    """A published sauna from a maker with no rights record and no link: the
    plainest shape a new eligible product takes."""
    for q in rows:
        if (q["qualification"]["state"] == "ELIGIBLE" and q["publicVisibility"] == "PUBLISHABLE"
                and q.get("kinds") == ["sauna"]):
            return q
    raise SystemExit("no public sauna to model a fixture on")


NEW_ID, NEW_ORG = "recTESTSAUNA00001", "Test Sauna Makers Ltd"


def add_new_maker(rows, kinds=("sauna",), pid=NEW_ID, org=NEW_ORG):
    q = copy.deepcopy(public_sauna(rows))
    q.update({"id": pid, "organisation": org, "productName": "Test Barrel Sauna 2m", "kinds": list(kinds),
              "productCode": "TEST-%s" % pid[-5:], "productUrl": None, "listingBasis": "SUPPLIER_PERMISSION"})
    rows.append(q)


def main():
    print("DISCOVERY MAKER SYNCHRONISATION — TESTS (throwaway clones)")
    # ── 0 · baseline, determinism, idempotence ─────────────────────────────
    c = Clone()
    try:
        r = c.tool("--check")
        check("T0  the committed site is IN SYNC with its snapshot", r.returncode == 0 and "IN SYNC" in r.stdout,
              r.stdout[-300:])
        m = c.module()
        a, b = m.dump(m.state()[0]), m.dump(m.state()[0])
        check("T12 regeneration is deterministic (state serialised twice is byte-identical)", a == b)
        check("T12b the state equals the committed snapshot", a == c.text(NEW_FILES[1]))
        r1, r2 = c.tool("--report"), c.tool("--report")
        check("T12c two reports are identical", r1.stdout == r2.stdout)
        before = sh(["git", "status", "--porcelain"], c.root).stdout
        r = c.tool("--apply", "--all")
        after = sh(["git", "status", "--porcelain"], c.root).stdout
        check("T13 a repeated run with no Atlas change writes nothing (full apply)",
              r.returncode == 0 and "written: nothing" in r.stdout and before == after == "", r.stdout[-400:])
    finally:
        c.close()

    # ── 1 · a newly eligible maker, counts, search, links, unrelated pages ──
    c = Clone()
    try:
        garden_before = c.text("discovery-living-in-the-garden.html")
        snap_before = c.j(NEW_FILES[1])
        c.wellness(lambda rows: add_new_maker(rows))
        r = c.tool("--report")
        rep = r.stdout
        check("T1  report: the new maker appears for Garden Retreat only",
              "poss-garden-retreat · %s" % NEW_ORG in rep and "poss-living-in-the-garden · %s" % NEW_ORG not in rep, rep[:600])
        check("T2  report: the product is placed in the Saunas tab only",
              "%s · %s · Test Barrel Sauna 2m → poss-garden-retreat#saunas\n" % (NEW_ID, NEW_ORG) in rep)
        check("T2b report: awaiting regeneration (page and Search), not a failure",
              r.returncode == 0 and "Awaiting regeneration" in rep and "S3 discovery-garden-retreat.html" in rep)
        r = c.tool("--check")
        check("T2c --check fails while the change is unpublished", r.returncode == 1)
        r = c.tool("--apply", "--discovery", "poss-garden-retreat")
        check("T1b targeted apply succeeds", r.returncode == 0, r.stdout[-800:])
        page = c.text("discovery-garden-retreat.html")
        check("T1c the Garden Retreat explorer now lists the new maker and product",
              NEW_ORG in page and NEW_ID in page)
        s = c.j(NEW_FILES[1])
        D = s["discoveries"]["poss-garden-retreat"]
        O = snap_before["discoveries"]["poss-garden-retreat"]
        check("T7  counts update: products +1, makers +1, saunas tab +1, other tabs unchanged",
              D["products"] == O["products"] + 1 and D["makers"] == O["makers"] + 1
              and D["tabs"]["saunas"]["products"] == O["tabs"]["saunas"]["products"] + 1
              and D["tabs"]["hotTubs"] == O["tabs"]["hotTubs"] and D["tabs"]["coldPlunges"] == O["tabs"]["coldPlunges"])
        search = {x["id"]: x for x in c.j("search-index-v1.json")["records"]}
        check("T8  Search lists the new product, routed to the explorer that lists it",
              search.get("prod-" + NEW_ID, {}).get("route") == "discovery-garden-retreat.html#p-" + NEW_ID)
        check("T9  product links resolve after the rebuild (S7 passes)", c.tool("--check").returncode == 0)
        check("T11 Living in the Garden is byte-identical; its snapshot entry is unchanged",
              c.text("discovery-living-in-the-garden.html") == garden_before
              and s["discoveries"]["poss-living-in-the-garden"] == snap_before["discoveries"]["poss-living-in-the-garden"])
        r = c.tool("--apply", "--discovery", "poss-garden-retreat")
        check("T13b repeating the targeted apply writes nothing", "written: nothing" in r.stdout, r.stdout[-300:])
        # S7 negative: Search routing a product to a page that does not list it
        S = c.j("search-index-v1.json")
        for x in S["records"]:
            if x["id"] == "prod-" + NEW_ID:
                x["route"] = "discovery-garden-retreat.html#p-recAAAAAAAAAAAAAA"
        c.w("search-index-v1.json", S)
        r = c.tool("--check")
        check("T9b a broken product route is caught (S7)", r.returncode == 2 and "S7" in r.stdout)
    finally:
        c.close()

    # ── 2 · one product in two Discoveries, one canonical record ───────────
    c = Clone()
    try:
        m = c.module()
        cfg = copy.deepcopy(m.ME.PAGES["discovery-garden-retreat.html"])
        m.ME.PAGES["discovery-test-second.html"] = cfg
        m.REGISTRY.append({"id": "poss-test-second", "route": "discovery-test-second.html", "explorer": "maker",
                           "categories": ["Wellness / Sauna"], "search": False})
        st = m.state()[0]
        pid = next(p for p, v in st["products"].items() if v["source"] == "wellness-universe-v1")
        text = m.dump(st)
        check("T3  a product appears in two Discoveries as ONE canonical record",
              any(i.startswith("poss-test-second#") for i in st["products"][pid]["in"])
              and any(i.startswith("poss-garden-retreat#") for i in st["products"][pid]["in"])
              and text.count('"%s": {' % pid) == 1)
        check("T3b the second Discovery's counts equal the first's (no duplication)",
              st["discoveries"]["poss-test-second"]["products"] == st["discoveries"]["poss-garden-retreat"]["products"])
    finally:
        c.close()

    # ── 3 · held, objection, removal ──────────────────────────────────────
    c = Clone()
    try:
        snap_was = c.j(NEW_FILES[1])
        U = c.j("wellness-universe-v1.json")
        victim = public_sauna(U["products"])["id"]
        objector = [q for q in U["products"] if q["qualification"]["state"] == "ELIGIBLE"
                    and q["publicVisibility"] == "PUBLISHABLE" and q["id"] != victim][0]["id"]

        def hold(rows):
            for q in rows:
                if q["id"] == victim:
                    q["qualification"] = dict(q["qualification"], state="HELD", heldReasons=["recorded-contradiction"])
                if q["id"] == objector:      # what the gate emits when a rights record records an objection
                    q["publicVisibility"], q["holdReason"] = "HOLD", "supplier-objection"
        c.wellness(hold)
        rep = c.tool("--report").stdout
        check("T4  report: the held product is listed as newly held", "Newly held products: " in rep and victim in rep
              and rep.split("Newly held products:")[1].split("\n")[0].strip() != "0")
        r = c.tool("--apply", "--discovery", "poss-garden-retreat")
        page, search, snap = c.text("discovery-garden-retreat.html"), c.text("search-index-v1.json"), c.j(NEW_FILES[1])
        check("T4b a held product never appears publicly (page, Search, snapshot)",
              r.returncode == 0 and victim not in page and victim not in search and victim not in snap["products"],
              r.stdout[-500:])
        check("T5  a supplier objection blocks publication (page, Search, snapshot)",
              objector not in page and objector not in search and objector not in snap["products"])
        check("T10 removing eligibility removes the product from the next snapshot",
              victim in snap_was["products"] and victim not in snap["products"])
        # The public-information register refuses a row that records an objection.
        reg = c.j("atlas-tools/public-information-listings.json")
        reg["organisations"][0]["objection"] = "objection recorded 14 Oct 2026"
        c.w("atlas-tools/public-information-listings.json", reg)
        probe = ("import sys; sys.path.insert(0, '.github/scripts'); import generate_wellness_universe as g; "
                 "g.public_information_register()")
        r = sh([sys.executable, "-c", probe], c.root)
        check("T5b the register cannot list a maker that has objected (generator refuses)",
              r.returncode != 0 and "malformed" in (r.stdout + r.stderr))
    finally:
        c.close()

    # ── 4 · unauthorised imagery stays excluded ───────────────────────────
    c = Clone()
    try:
        R = c.j("image-rights-records.json")
        snap = c.j(NEW_FILES[1])
        shown = {v["maker"] for v in snap["products"].values() if v["images"]}
        row = next(x for x in R["records"] if x.get("approved_assets") and x["organisation_name"] in shown)
        org = row["organisation_name"]
        had = [p for p, v in snap["products"].items() if v["maker"] == org and v["images"]]
        row["permission"]["scope"] = [s for s in row["permission"]["scope"] if s != "imagery"]
        c.w("image-rights-records.json", R)
        rep = c.tool("--report").stdout
        check("T6  report: withdrawing the imagery scope is an image-rights change",
              bool(had) and "Image-rights changes: %d" % len(had) in rep, rep[:300])
        r = c.tool("--apply", "--discovery", "poss-garden-retreat")
        page = c.text("discovery-garden-retreat.html")
        srcs = [i for p in had for i in snap["products"][p]["images"]]
        check("T6b no image outside the grant reaches the page",
              r.returncode == 0 and srcs and not any(s in page for s in srcs),
              r.stdout[-400:])
    finally:
        c.close()

    # ── 5 · boundaries: targeted refusal, category integrity ──────────────
    c = Clone()
    try:
        c.wellness(lambda rows: add_new_maker(rows))
        A = c.j("additional-home-universe-v1.json")
        q = next(x for x in A["products"] if x["qualification"]["state"] == "ELIGIBLE")
        q["productName"] = q["productName"] + " (renamed in Atlas)"
        c.w("additional-home-universe-v1.json", A)
        r = c.tool("--apply", "--discovery", "poss-garden-retreat")
        check("T14 a targeted apply refuses when another Discovery has pending changes",
              r.returncode == 2 and "other Discoveries have pending changes (poss-living-in-the-garden)" in r.stdout,
              r.stdout[-300:])
        check("T14b … and writes nothing", sh(["git", "status", "--porcelain"], c.root).stdout.split()
              == ["M", "additional-home-universe-v1.json", "M", "wellness-universe-v1.json"])
    finally:
        c.close()
    c = Clone()
    try:
        def miscategorise(rows):
            rows[0]["productCategory"] = "Garden Rooms"
        c.wellness(miscategorise)
        r = c.tool("--apply", "--discovery", "poss-garden-retreat")
        check("T15 a record outside its universe's Atlas category is held for review, not published",
              r.returncode == 2 and "S2 wellness-universe-v1" in r.stdout)
    finally:
        c.close()

    n, ok = len(RESULTS), sum(1 for _, o in RESULTS if o)
    print("\n%d/%d passed — %s" % (ok, n, "PROVEN" if ok == n else "NOT PROVEN"))
    sys.exit(0 if ok == n else 1)


if __name__ == "__main__":
    main()
