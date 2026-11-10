#!/usr/bin/env python3
"""PlotNua · publish a founder-approved VERIFIED PRICE REFRESH, and nothing else.

Stage 3D-B2 (founder approval 6 Nov 2026). publish-price-recheck-dates.py moves only a
check date and refuses a record with two linked price records. A verified refresh also
carries a small number of approved price corrections (a supplier's regular price moved)
and approved Price Type corrections, and some products carry two Atlas price records for
the same figure. This tool publishes exactly that, from a scoped Atlas read-back, against
a plan file in atlas-tools/price-refresh-plans/, and then runs the targeted-update tool's
own downstream steps (search re-freeze, explorer/search rebuild, boundary check,
validation gates) unchanged.

Refuses unless, for every product in the plan:
  * the published record exists and its organisation is in the Atlas read;
  * EVERY Atlas pricing record in priceEvidenceRef.recordIds is in the read, links the
    product, reads Last Price Check == --date and a governed figure (Base Price, else Price
    From: the generator's rule) == approvedPrice, with Base Price equal to the published
    base unless the plan moves the price, and its
    Currency, Status, Price From, Price To and Evidence Scope equal the published record
    (unapproved Atlas drift is refused, not published);
  * Price Type reads approvedPriceType where the plan gives one, otherwise the published
    Price Type (no unapproved Price Type change);
  * a price moves only where the plan's approvedPrice differs from publishedPrice, and
    publishedPrice equals the price published today;
  * priceFreshUntil follows the new check date by the generator's R-MATCH rule, and price
    eligibility may not change;
  * afterwards only the allowed keys differ in each target, no other record differs, and
    in the header only governedDigest moves.

  python3 atlas-tools/publish-price-refresh.py --plan atlas-tools/price-refresh-plans/X.json \
      --snapshot read.json [--snapshot ...] [--dry-run | --apply] [--report FILE]
"""
from __future__ import annotations

import argparse, copy, datetime as _dt, importlib.util, json, pathlib, re, shutil, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("tu", HERE / "publish-targeted-update.py")
tu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tu)

ALLOWED_PATHS = {"priceEvidenceRef.lastPriceCheck", "price", "priceEvidence.base",
                 "priceType", "priceEvidence.priceType", "priceEvidenceRef.priceType",
                 "priceFreshUntil"}


def norm(v):
    return re.sub(r"\s+", " ", v).strip() if isinstance(v, str) else v


def num(v):
    return None if v is None else float(v)


def paths(a, b, pre=""):
    out = set()
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            out |= paths(a.get(k), b.get(k), pre + ("." if pre else "") + k)
    elif a != b:
        out.add(pre)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--snapshot", action="append", required=True)
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
    g = tu.load_module(root / tu.GARDEN_GEN, "grgen_refresh")
    plan_path = pathlib.Path(a.plan)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    date = plan["date"]
    _dt.date.fromisoformat(date)
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
    if g.governed_digest(uni["products"]) != uni["governedDigest"]:
        tu.refuse("the committed governedDigest does not match the committed products")
    before = copy.deepcopy(uni)
    by_id = {p["productId"]: p for p in uni["products"]}
    items = plan["products"]
    targets = [i["productId"] for i in items]
    if len(set(targets)) != len(targets):
        tu.refuse("the plan lists a product twice")
    rows, org_names = [], set()
    for it in items:
        pid = it["productId"]
        p = by_id.get(pid) or tu.refuse("%s is not in the published universe" % pid)
        if p["organisation"] not in orgs.values():
            tu.refuse("%s: organisation %s is not in the Atlas read" % (pid, p["organisation"]))
        if num(it["publishedPrice"]) != num(p["price"]):
            tu.refuse("%s: plan publishedPrice %s is not the published price %s"
                      % (pid, it["publishedPrice"], p["price"]))
        if (p.get("priceEvidence") or {}).get("presentationHold"):
            tu.refuse("%s carries a price-presentation hold; a refresh may not touch it" % pid)
        ref = p["priceEvidenceRef"]
        if sorted(ref["recordIds"]) != sorted(it["priceRecordIds"]):
            tu.refuse("%s: plan price records %s are not the published %s"
                      % (pid, it["priceRecordIds"], ref["recordIds"]))
        pe = p["priceEvidence"]
        want_type = it.get("approvedPriceType") or p["priceType"]
        full_match = 0
        for rid in ref["recordIds"]:
            r = pricing.get(rid) or tu.refuse("%s: price record %s is not in the Atlas read" % (pid, rid))
            # Every linked record: same product, checked on the date, at the approved price,
            # in the published currency and Price Type.
            checks = [
                ("Product", pid in tu.link_ids(r, "Product"), tu.link_ids(r, "Product")),
                ("Last Price Check", tu.fv(r, "Last Price Check") == date, tu.fv(r, "Last Price Check")),
                # The governed figure is the generator's own rule (Base Price first, then
                # Price From; generate_garden_room_universe.py). A record that carries its
                # figure in Price From with Base Price blank (published base null) is read
                # the same way the universe was built; Base Price itself must still equal
                # the published base, so no field may drift (Loghouse refresh, 10 Nov 2026).
                ("Price", num(tu.fv(r, "Base Price") if tu.fv(r, "Base Price") is not None
                              else tu.fv(r, "Price From")) == num(it["approvedPrice"]),
                 (tu.fv(r, "Base Price"), tu.fv(r, "Price From"))),
                ("Base Price", num(tu.fv(r, "Base Price")) == (num(it["approvedPrice"])
                               if num(it["approvedPrice"]) != num(p["price"]) else num(pe.get("base"))),
                 tu.fv(r, "Base Price")),
                ("Currency", tu.fv(r, "Currency") == p["currency"], tu.fv(r, "Currency")),
                ("Price Type", norm(tu.fv(r, "Price Type")) == want_type, tu.fv(r, "Price Type")),
                ("Price From", num(tu.fv(r, "Price From")) == num(pe.get("from")), tu.fv(r, "Price From")),
                ("Price To", num(tu.fv(r, "Price To")) == num(pe.get("to")), tu.fv(r, "Price To")),
            ]
            bad = [(n, v) for n, ok, v in checks if not ok]
            if bad:
                tu.refuse("%s (%s) record %s does not match the approved refresh: %s"
                          % (pid, p["productName"], rid, bad))
            # The adjudicated record the published evidence came from must also carry the
            # published Status, Evidence Scope and VAT position (an older duplicate record may
            # leave them blank; it may not contradict them).
            ok_status = norm(tu.fv(r, "Status")) == p["priceStatus"]
            ok_scope = norm(tu.fv(r, "Evidence Scope")) == p["priceScope"]
            ok_vat = norm(tu.fv(r, "Price Includes VAT")) == pe.get("includesVat")
            if ok_status and ok_scope and ok_vat:
                full_match += 1
            for n, val, pub in (("Status", tu.fv(r, "Status"), p["priceStatus"]),
                                ("Evidence Scope", tu.fv(r, "Evidence Scope"), p["priceScope"])):
                if val not in (None, "") and norm(val) != pub:
                    tu.refuse("%s record %s: %s %r contradicts the published %r" % (pid, rid, n, val, pub))
        if not full_match:
            tu.refuse("%s (%s): no linked price record carries the published Status, Evidence "
                      "Scope and VAT position" % (pid, p["productName"]))
        old = copy.deepcopy(p)
        if ref["lastPriceCheck"] >= date:
            tu.refuse("%s: published check date %s is not older than %s" % (pid, ref["lastPriceCheck"], date))
        ref["lastPriceCheck"] = date
        if num(it["approvedPrice"]) != num(p["price"]):
            newp = int(it["approvedPrice"]) if float(it["approvedPrice"]).is_integer() else it["approvedPrice"]
            p["price"] = newp
            pe["base"] = newp
        if it.get("approvedPriceType") and it["approvedPriceType"] != p["priceType"]:
            p["priceType"] = pe["priceType"] = ref["priceType"] = it["approvedPriceType"]
        # R-MATCH freshness (validator rule of 7 Nov 2026): a new check date moves
        # priceFreshUntil by the generator's own rule. Eligibility itself may not change.
        safe, until = g.r_match(p["price"], p["currency"], ref["adjudication"], p["priceStatus"],
                                p["priceType"], p["priceScope"], date)
        if safe != p["priceSafeForMatching"]:
            tu.refuse("%s: the refresh would change price eligibility (%s -> %s)"
                      % (pid, p["priceSafeForMatching"], safe))
        if p.get("priceFreshUntil") is not None:
            p["priceFreshUntil"] = until
        moved = paths(old, p)
        if not moved or moved - ALLOWED_PATHS:
            tu.refuse("%s: the refresh would change %s" % (pid, sorted(moved - ALLOWED_PATHS)))
        org_names.add(p["organisation"])
        rows.append((pid, p["productName"], p["organisation"], old["price"], p["price"],
                     old["priceType"], p["priceType"], old["priceEvidenceRef"]["lastPriceCheck"],
                     ", ".join(ref["recordIds"])))
    uni["governedDigest"] = g.governed_digest(uni["products"])
    others = [k for k in set(before) | set(uni) if k not in ("products", "governedDigest")
              and before.get(k) != uni.get(k)]
    if others:
        tu.refuse("the universe header would change beyond governedDigest: %s" % others)
    b_by = {p["productId"]: p for p in before["products"]}
    stray = [p["productId"] for p in uni["products"]
             if p["productId"] not in targets and p != b_by.get(p["productId"])]
    if stray or len(before["products"]) != len(uni["products"]):
        tu.refuse("records other than the plan's products would change: %s" % stray[:5])
    new = tu.dump1(uni)

    rep = {"org_id": None}
    wt = pathlib.Path(tempfile.mkdtemp(prefix="prf-wt-")) / "wt"
    tu.sh(["git", "worktree", "add", "--detach", str(wt), "HEAD"], root, check=True)
    try:
        (wt / tu.GARDEN).write_text(new, encoding="utf-8")
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
        report_name = "%s/%s-price-refresh.md" % (tu.REPORT_DIR, stamp)
        tu.refreeze_search(wt, report_name, rep)
        tu.run_builders(wt, rep)
        moved = tu.boundary(root, wt, set(targets), org_names, rep)
        results = tu.validate(root, wt, moved, rep)
        fm = lambda v: "€" + format(v, ",")
        L = ["# Verified price refresh — %s (%s)" % (plan["id"], date), "",
             "- Tool: atlas-tools/publish-price-refresh.py (dates, approved prices and approved "
             "Price Types only; downstream steps from publish-targeted-update.py)",
             "- Plan: `%s`" % plan_path.as_posix().split("/atlas-tools/")[-1],
             "- Built on commit `%s`" % head_sha[:12],
             "- Mode: %s" % ("APPLY" if a.apply else "DRY RUN"), ""]
        L += ["- Atlas read `%s` sha256 `%s`" % (pathlib.Path(s).name, h) for s, h in snap_shas]
        L += ["", "Approval: " + plan["approved"], "",
              "## Products (%d)" % len(rows), "",
              "| Product | Organisation | Price | Price Type | Check date | Atlas price record(s) |",
              "|---|---|---|---|---|---|"]
        for pid, n, o, p0, p1, t0, t1, d0, rid in rows:
            L.append("| `%s` %s | %s | %s | %s | %s → %s | `%s` |" % (
                pid, n, o, fm(p0) if p0 == p1 else "%s → **%s**" % (fm(p0), fm(p1)),
                t0 if t0 == t1 else "%s → **%s**" % (t0, t1), d0, date, rid))
        L += ["", "Header: governedDigest `%s…` → `%s…`" % (before["governedDigest"][:16],
                                                        uni["governedDigest"][:16])]
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
