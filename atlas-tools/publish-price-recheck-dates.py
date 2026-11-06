#!/usr/bin/env python3
"""PlotNua · publish founder-approved base-price RECHECK DATES, and nothing else.

Why this exists (6 Nov 2026): publish-targeted-update.py regenerates a product's whole
universe record from a fresh Atlas read. For Garden Office Solutions, Adman Steel Sheds
and Live in Garden Pods that regeneration would ALSO publish feature changes made in
Atlas since the 7 Oct snapshot (floor area, insulation, warranty, price-record order),
which no founder decision has approved. A recheck batch may move only the date a price
was last checked. This tool does exactly that, from a scoped Atlas read, and then runs
the targeted-update tool's own downstream steps (search re-freeze, explorer/search
rebuild, boundary check, validation gates) unchanged.

Refuses unless, for every target product:
  * the published record exists and its organisation is in the Atlas read;
  * the record's ADJUDICATED price record (priceEvidenceRef.recordIds) includes an Atlas
    pricing record whose Last Price Check equals --date, whose Base Price equals the
    published price, and whose Status equals the published price status;
  * nothing but `priceEvidenceRef.lastPriceCheck` differs in the record afterwards, and
    no other record in any file differs at all (boundary() + an exact line diff).

  python3 atlas-tools/publish-price-recheck-dates.py --date 2026-11-06 \
      --snapshot a.json [--snapshot b.json ...] --product recX [--product ...] \
      [--dry-run | --apply] [--report FILE]
"""
from __future__ import annotations

import argparse, datetime as _dt, difflib, importlib.util, json, pathlib, shutil, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("tu", HERE / "publish-targeted-update.py")
tu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tu)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--snapshot", action="append", required=True)
    ap.add_argument("--product", action="append", required=True)
    ap.add_argument("--root")
    ap.add_argument("--report")
    m = ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--dry-run", action="store_true")
    m.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    try:
        return run(a)
    except tu.Refused as e:
        print("REFUSED: %s" % e)
        return 2


def run(a):
    _dt.date.fromisoformat(a.date)
    root = tu.git_root(pathlib.Path(a.root).resolve() if a.root else tu.SELF_ROOT)
    if tu.sh(["git", "status", "--porcelain", "--untracked-files=no"], root, check=True).stdout.strip():
        tu.refuse("the working tree has uncommitted changes")
    head_sha = tu.sh(["git", "rev-parse", "HEAD"], root, check=True).stdout.strip()
    targets = list(dict.fromkeys(a.product))
    pricing, orgs, snap_shas = {}, {}, []
    for s in a.snapshot:
        b = pathlib.Path(s).read_bytes()
        snap_shas.append((s, tu.sha(b)))
        d = json.loads(b)
        for o in d["organisations"]:
            orgs[o["id"]] = tu.fv(o, "Organisation Name")
        for r in d["pricing"]:
            pricing[r["id"]] = r
    raw = (root / tu.GARDEN).read_text(encoding="utf-8")
    uni = json.loads(raw)
    if tu.dump1(uni) != raw:
        tu.refuse("the published universe is not in its canonical form")
    by_id = {p["productId"]: p for p in uni["products"]}
    rows, org_names = [], set()
    for pid in targets:
        p = by_id.get(pid) or tu.refuse("%s is not in the published universe" % pid)
        if p["organisation"] not in orgs.values():
            tu.refuse("%s: organisation %s is not in the Atlas read" % (pid, p["organisation"]))
        org_names.add(p["organisation"])
        ref = p["priceEvidenceRef"]
        ok = [r for i in ref["recordIds"] if (r := pricing.get(i))
              and tu.fv(r, "Last Price Check") == a.date
              and tu.fv(r, "Base Price") == p["price"]
              and (tu.fv(r, "Status") or "").strip() == p["priceStatus"]
              and pid in tu.link_ids(r, "Product")]
        if len(ok) != 1:
            tu.refuse("%s (%s): expected exactly one adjudicated Atlas price record checked on %s "
                      "at the published price %s; found %d" % (pid, p["productName"], a.date,
                                                               p["price"], len(ok)))
        old = ref["lastPriceCheck"]
        if old >= a.date:
            tu.refuse("%s: published check date %s is not older than %s" % (pid, old, a.date))
        ref["lastPriceCheck"] = a.date
        rows.append((pid, p["productName"], p["organisation"], p["price"], old, ok[0]["id"]))
    new = tu.dump1(uni)
    diff = [l for l in difflib.unified_diff(raw.splitlines(), new.splitlines(), lineterm="", n=0)
            if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    if len(diff) != 2 * len(targets) or any('"lastPriceCheck": ' not in l for l in diff):
        tu.refuse("the universe edit is not date-only:\n" + "\n".join(diff[:10]))

    rep = {"org_id": None}
    wt = pathlib.Path(tempfile.mkdtemp(prefix="prd-wt-")) / "wt"
    tu.sh(["git", "worktree", "add", "--detach", str(wt), "HEAD"], root, check=True)
    try:
        (wt / tu.GARDEN).write_text(new, encoding="utf-8")
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
        report_name = "%s/%s-price-recheck-dates.md" % (tu.REPORT_DIR, stamp)
        tu.refreeze_search(wt, report_name, rep)
        tu.run_builders(wt, rep)
        moved = tu.boundary(root, wt, set(targets), org_names, rep)
        results = tu.validate(root, wt, moved, rep)
        L = ["# Price recheck dates — %s" % a.date, "",
             "- Tool: atlas-tools/publish-price-recheck-dates.py (date-only; downstream steps "
             "from publish-targeted-update.py)",
             "- Built on commit `%s`" % head_sha[:12],
             "- Mode: %s" % ("APPLY" if a.apply else "DRY RUN"), ""]
        L += ["- Atlas read `%s` sha256 `%s`" % (pathlib.Path(s).name, h) for s, h in snap_shas]
        L += ["", "## Products (only `priceEvidenceRef.lastPriceCheck` moves)", "",
              "| Product | Organisation | Published price | Check date | Atlas price record |",
              "|---|---|---|---|---|"]
        L += ["| `%s` %s | %s | €%s | %s → %s | `%s` |" % (pid, n, o, format(pr, ","), old, a.date, rid)
              for pid, n, o, pr, old, rid in rows]
        if rep.get("search_pin"):
            L += ["", "Search universe pin re-frozen `%s…` → `%s…`" % (rep["search_pin"][0][:16],
                                                                 rep["search_pin"][1][:16])]
        L += ["", "## Validation", ""] + ["- %s %s%s" % (v, n, (" — " + d) if d else "")
                                         for n, v, d in results]
        L += ["", "## Files that change", ""] + ["- " + f for f in moved]
        text = "\n".join(L) + "\n"
        print(text)
        if a.report:
            pathlib.Path(a.report).write_text(text, encoding="utf-8")
        if any(v == "FAIL" for _, v, _ in results):
            tu.refuse("validation failed")
        if not a.apply:
            print("DRY RUN — nothing written.")
            return 0
        for f in moved:
            shutil.copy2(wt / f, root / f)
        (root / report_name).write_text(text, encoding="utf-8")
        print("APPLIED — %d file(s) + report %s. Nothing committed." % (len(moved), report_name))
        return 0
    finally:
        tu.sh(["git", "worktree", "remove", "--force", str(wt)], root)
        shutil.rmtree(wt.parent, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
