#!/usr/bin/env python3
"""PlotNua · publish a founder-approved PRICE-PRESENTATION HOLD, and nothing else.

Why this exists (Stage 3C, 6 Nov 2026): a hold is a register decision
(atlas-tools/price-presentation-holds.json), not an Atlas change. Re-generating the
held product's record from a fresh Atlas read with publish-targeted-update.py would
also publish any Atlas edits made since the 7 Oct snapshot, which no founder decision
has approved. This tool applies the generator's OWN hold function
(apply_price_presentation_hold) to the published record, recomputes the universe
header's governed digest, and then runs the targeted-update tool's downstream steps
(search re-freeze, explorer/search rebuild, boundary check, validation gates)
unchanged.

Refuses unless, for every target product:
  * it is in the published universe and the register holds it;
  * the only fields that change in its record are priceSafeForMatching,
    priceBasisConfidence and priceEvidence.presentationHold;
  * no other product record changes, and in the header only governedDigest.

  python3 atlas-tools/publish-presentation-hold.py --product recX [--product ...] \
      [--dry-run | --apply] [--report FILE]
"""
from __future__ import annotations

import argparse, copy, datetime as _dt, importlib.util, json, pathlib, shutil, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("tu", HERE / "publish-targeted-update.py")
tu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tu)

# 11 Nov 2026: R-MATCH (Stage 3D-D2) derives priceState/priceFreshUntil from the hold; the
# generator's own finalise_price_state() sets them exactly as a full regeneration would.
ALLOWED = {"priceSafeForMatching", "priceBasisConfidence", "priceEvidence", "priceState", "priceFreshUntil"}


def main(argv=None):
    ap = argparse.ArgumentParser()
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
    root = tu.git_root(pathlib.Path(a.root).resolve() if a.root else tu.SELF_ROOT)
    if tu.sh(["git", "status", "--porcelain", "--untracked-files=no"], root, check=True).stdout.strip():
        tu.refuse("the working tree has uncommitted changes")
    head_sha = tu.sh(["git", "rev-parse", "HEAD"], root, check=True).stdout.strip()
    g = tu.load_module(root / tu.GARDEN_GEN, "grgen_hold")
    holds = g.price_presentation_holds()
    targets = list(dict.fromkeys(a.product))
    raw = (root / tu.GARDEN).read_text(encoding="utf-8")
    uni = json.loads(raw)
    if tu.dump1(uni) != raw:
        tu.refuse("the published universe is not in its canonical form")
    by_id = {p["productId"]: p for p in uni["products"]}
    before = copy.deepcopy(uni)
    rows, org_names = [], set()
    for pid in targets:
        p = by_id.get(pid) or tu.refuse("%s is not in the published universe" % pid)
        if pid not in holds:
            tu.refuse("%s is not in the price-presentation hold register" % pid)
        if (p.get("priceEvidence") or {}).get("presentationHold"):
            tu.refuse("%s already carries a presentation hold" % pid)
        old = copy.deepcopy(p)
        g.apply_price_presentation_hold(p, pid)
        g.finalise_price_state(p)
        changed = {k for k in set(old) | set(p) if old.get(k) != p.get(k)}
        if not changed or changed - ALLOWED:
            tu.refuse("%s: the hold would change %s" % (pid, sorted(changed - ALLOWED) or "nothing"))
        pe0 = dict(old.get("priceEvidence") or {}); pe1 = dict(p.get("priceEvidence") or {})
        pe1.pop("presentationHold", None)
        if pe0 != pe1:
            tu.refuse("%s: priceEvidence would change beyond presentationHold" % pid)
        org_names.add(p["organisation"])
        rows.append((pid, p["productName"], p["organisation"], old.get("priceSafeForMatching"),
                     old.get("priceBasisConfidence"), p.get("priceBasisConfidence")))
    uni["governedDigest"] = g.governed_digest(uni["products"])
    others = [k for k in set(before) | set(uni) if k not in ("products", "governedDigest")
              and before.get(k) != uni.get(k)]
    if others:
        tu.refuse("the universe header would change beyond governedDigest: %s" % others)
    b_by = {p["productId"]: p for p in before["products"]}
    stray = [p["productId"] for p in uni["products"]
             if p["productId"] not in targets and p != b_by.get(p["productId"])]
    if stray or len(before["products"]) != len(uni["products"]):
        tu.refuse("records other than the targets would change: %s" % stray[:5])
    new = tu.dump1(uni)

    rep = {"org_id": None}
    wt = pathlib.Path(tempfile.mkdtemp(prefix="pph-wt-")) / "wt"
    tu.sh(["git", "worktree", "add", "--detach", str(wt), "HEAD"], root, check=True)
    try:
        (wt / tu.GARDEN).write_text(new, encoding="utf-8")
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
        report_name = "%s/%s-presentation-hold.md" % (tu.REPORT_DIR, stamp)
        tu.refreeze_search(wt, report_name, rep)
        tu.run_builders(wt, rep)
        moved = tu.boundary(root, wt, set(targets), org_names, rep)
        results = tu.validate(root, wt, moved, rep)
        L = ["# Price-presentation hold", "",
             "- Tool: atlas-tools/publish-presentation-hold.py (hold-only; downstream steps "
             "from publish-targeted-update.py)",
             "- Built on commit `%s`" % head_sha[:12],
             "- Register: atlas-tools/price-presentation-holds.json",
             "- Mode: %s" % ("APPLY" if a.apply else "DRY RUN"), "",
             "## Products (only priceSafeForMatching, priceBasisConfidence and "
             "priceEvidence.presentationHold move)", "",
             "| Product | Organisation | Safe for matching | Basis confidence |", "|---|---|---|---|"]
        L += ["| `%s` %s | %s | %s → False | %s → %s |" % (pid, n, o, s0, c0, c1)
              for pid, n, o, s0, c0, c1 in rows]
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
