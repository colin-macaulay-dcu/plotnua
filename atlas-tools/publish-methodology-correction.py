#!/usr/bin/env python3
"""PlotNua · publish a founder-approved PRICING METHODOLOGY CORRECTION, and nothing else.

Stage 3D-C2 (founder approval 7 Nov 2026). Publishes, from a scoped Atlas read-back and a
plan file in atlas-tools/methodology-plans/, exactly four kinds of change to published
garden-room records, then runs the targeted-update tool's own downstream steps (search
re-freeze, explorer/search rebuild, boundary check, validation gates) unchanged:

  installation  the product's Installation Model feature value (A1 Adman, Ö1 ÖÖD, L1 Live in
                Garden Pods updated; K1 kits and M1 Modular House created), and the price-basis
                fields the generator derives from it (basisLeadPhrase, basisSource, erection
                axis, basis class, basis confidence), computed by the generator's own functions;
  vat           Price Includes VAT -> Yes for a price resting on a supplier's current terms of
                sale, with priceEvidence.vatBasis = "supplier-terms" (atlas-tools/vat-terms-
                evidence.json must hold a current accepted entry naming the product);
  priceType     an approved Price Type correction (and the range-floor flag it implies);
  price         an approved price correction (base, Price To, check date, range-floor flag).

Refuses unless, for every product in the plan:
  * the published record exists, carries no price-presentation hold, and its organisation is
    the plan's;
  * every Atlas record named reads exactly what the plan says (installation text read back;
    price records' price, Price To, Price Type, VAT, currency, status and check date);
  * the recomputed derivation reproduces EVERY published garden-room record that the plan
    does not touch (a fidelity proof over the whole universe, so the derivation cannot drift
    from the generator's);
  * afterwards only the allowed paths for that product's approved change kinds differ, no
    other record differs, and in the header only governedDigest moves.

  python3 atlas-tools/publish-methodology-correction.py --plan atlas-tools/methodology-plans/X.json \
      --snapshot read.json [--dry-run | --apply] [--report FILE]
"""
from __future__ import annotations

import argparse, copy, datetime as _dt, hashlib, importlib.util, json, pathlib, re, shutil, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("tu", HERE / "publish-targeted-update.py")
tu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tu)

VAT_REGISTER = "atlas-tools/vat-terms-evidence.json"
BASIS_PATHS = {"features.installationModel", "priceEvidenceRef.basisLeadPhrase", "priceEvidenceRef.basisSource",
               "priceBasisAxes.erection", "priceBasisClass", "priceBasisConfidence"}
ALLOWED = {
    "installation": BASIS_PATHS,
    "vat": {"vatStatus", "priceEvidence.includesVat", "priceEvidence.vatBasis"},
    "priceType": {"priceType", "priceEvidence.priceType", "priceEvidenceRef.priceType", "priceIsRangeFloor"},
    "price": {"price", "priceEvidence.base", "priceEvidence.to", "priceEvidenceRef.lastPriceCheck",
              "priceIsRangeFloor"},
}
SAFE_STATUSES = {"Verified", "Partially Verified"}
VAT_MAP = {"yes": "Yes", "no": "No", "excluding vat": "No"}


def norm(v):
    return re.sub(r"\s+", " ", v).strip() if isinstance(v, str) else v


def num(v):
    return None if v is None else float(v)


def paths(a, b, pre=""):
    out = set()
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            p = pre + ("." if pre else "") + k
            if pre == "features" or p == "features.installationModel":
                if a.get(k) != b.get(k):
                    out.add("features." + k if pre == "features" else p)
                continue
            out |= paths(a.get(k), b.get(k), p)
    elif a != b:
        out.add(pre)
    return out


def derive_basis(g, p, text):
    """The generator's price_governance(), restricted to the fields an installation record
    drives, evaluated on a published record. Proven against the whole universe before use."""
    lead = g.install_lead_phrase(text)
    if lead is None:
        erection, conf = "UNKNOWN", "NO_BASIS_STATED"
    elif lead in g.INSTALL_LEAD_ERECTION:
        erection = g.INSTALL_LEAD_ERECTION[lead]
        conf = "EXPLICIT" if erection != "UNKNOWN" else "NOT_CONFIRMED"
    else:
        erection, conf = "UNKNOWN", "NOT_CONFIRMED"
    ref = p.get("priceEvidenceRef") or {}
    adj = ref.get("adjudication")
    price = p.get("price") if (isinstance(p.get("price"), (int, float)) and p.get("price") > 0) else None
    if adj == "ambiguous":
        conf = "CONFLICTED"
    elif price is None:
        conf = "NO_PRICE"
    safe = bool(price is not None and p.get("currency") and adj == "adjudicated" and p.get("priceStatus") in SAFE_STATUSES)
    if price is not None and not safe and adj != "ambiguous":
        conf = "UNSAFE" if conf in ("EXPLICIT", "NO_BASIS_STATED", "NOT_CONFIRMED") else conf
    if (p.get("priceEvidence") or {}).get("presentationHold") and conf in ("EXPLICIT", "NO_BASIS_STATED", "NOT_CONFIRMED"):
        conf = "UNSAFE"
    axes = dict(p.get("priceBasisAxes") or {}, erection=erection)
    return {"erection": erection, "conf": conf, "class": g.derive_basis_class(axes),
            "basisSource": "installationModel.leadPhrase" if lead else None,
            "basisLeadPhrase": lead if lead in g.INSTALL_LEAD_ERECTION else None}


def apply_basis(g, p, text):
    d = derive_basis(g, p, text)
    p["priceBasisAxes"]["erection"] = d["erection"]
    p["priceBasisClass"] = d["class"]
    p["priceBasisConfidence"] = d["conf"]
    p["priceEvidenceRef"]["basisSource"] = d["basisSource"]
    p["priceEvidenceRef"]["basisLeadPhrase"] = d["basisLeadPhrase"]


def range_floor(p):
    price = p.get("price") if (isinstance(p.get("price"), (int, float)) and p.get("price") > 0) else None
    to = (p.get("priceEvidence") or {}).get("to")
    ptype = p.get("priceType")
    return bool(price is not None and isinstance(to, (int, float)) and not isinstance(to, bool) and to > price) or \
        bool(price is not None and ptype and ptype.strip().lower() == "starting from")


def feature_object(g, r):
    """The generator's carry of one Feature Value (generate_garden_room_universe.py, D2)."""
    f = r["fields"]
    one = {"text": g.homeowner_text(f.get("Value Text")), "number": f.get("Value Number"),
           "unit": f.get("Unit"), "evidenceScope": f.get("Evidence Scope")}
    if f.get("Confirmation State"):
        one["confirmationState"] = f["Confirmation State"]
    if f.get("Status"):
        one["status"] = f["Status"]
    return one


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--snapshot", required=True)
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
    g = tu.load_module(root / tu.GARDEN_GEN, "grgen_methodology")
    plan_path = pathlib.Path(a.plan)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    date = plan["date"]
    today = _dt.date.fromisoformat(date)
    snap_b = pathlib.Path(a.snapshot).read_bytes()
    snap_sha = tu.sha(snap_b)
    snap = json.loads(snap_b)
    pricing = {r["id"]: r for r in snap["pricing"]}
    feats = {r["id"]: r for r in snap["featureValues"]}
    raw = (root / tu.GARDEN).read_text(encoding="utf-8")
    uni = json.loads(raw)
    if tu.dump1(uni) != raw:
        tu.refuse("the published universe is not in its canonical form")
    if g.governed_digest(uni["products"]) != uni["governedDigest"]:
        tu.refuse("the committed governedDigest does not match the committed products")
    before = copy.deepcopy(uni)
    by_id = {p["productId"]: p for p in uni["products"]}

    kinds = {}
    for k in ("installation", "vat", "priceType", "price"):
        for it in plan.get(k) or []:
            kinds.setdefault(it["productId"], set()).add(k)
    targets = set(kinds)

    # ---- fidelity: the derivation reproduces every record the plan does not touch
    for p in uni["products"]:
        if p["productId"] in targets:
            continue
        text = ((p.get("features") or {}).get("installationModel") or {}).get("text")
        d = derive_basis(g, p, text)
        got = (d["erection"], d["conf"], d["class"], d["basisSource"], d["basisLeadPhrase"], range_floor(p))
        want = ((p.get("priceBasisAxes") or {}).get("erection"), p.get("priceBasisConfidence"), p.get("priceBasisClass"),
                (p.get("priceEvidenceRef") or {}).get("basisSource"), (p.get("priceEvidenceRef") or {}).get("basisLeadPhrase"),
                p.get("priceIsRangeFloor"))
        if got != want:
            tu.refuse("FIDELITY: the derivation does not reproduce published record %s: %s != %s"
                      % (p["productId"], got, want))

    reg = json.loads((root / VAT_REGISTER).read_text(encoding="utf-8"))
    accepted = {}
    for e in reg["suppliers"]:
        if e["status"] != "accepted":
            continue
        if (today - _dt.date.fromisoformat(e["checked"])).days > 90:
            tu.refuse("the VAT terms register entry for %s is out of date" % e["organisation"])
        accepted[e["organisation"]] = {x["productId"]: x for x in e["productPagesChecked"]}

    rows, org_names = [], set()
    for pid in sorted(targets):
        p = by_id.get(pid) or tu.refuse("%s is not in the published universe" % pid)
        if (p.get("priceEvidence") or {}).get("presentationHold"):
            tu.refuse("%s carries a price-presentation hold; this publication may not touch it" % pid)
        old = copy.deepcopy(p)
        notes = []
        for it in [x for x in plan.get("installation") or [] if x["productId"] == pid]:
            if p["organisation"] != it["organisation"]:
                tu.refuse("%s: organisation %s is not the plan's %s" % (pid, p["organisation"], it["organisation"]))
            if len(it["featureValueIds"]) != 1:
                tu.refuse("%s: exactly one Installation Model record is required" % pid)
            r = feats.get(it["featureValueIds"][0]) or tu.refuse("%s: feature value %s is not in the Atlas read" % (pid, it["featureValueIds"][0]))
            f = r["fields"]
            if f.get("Product") != [pid] or f.get("Feature") != ["rec9qV0dfO5jgZ6KP"]:
                tu.refuse("%s: %s is not this product's Installation Model" % (pid, r["id"]))
            cur = (p.get("features") or {}).get("installationModel")
            if cur and "records" in cur:
                tu.refuse("%s: the published record carries more than one Installation Model" % pid)
            if it["change"] in ("K1", "M1") and cur:
                tu.refuse("%s: a created Installation Model where one is already published" % pid)
            if it["change"] in ("A1", "Ö1", "L1") and not cur:
                tu.refuse("%s: an updated Installation Model that is not published" % pid)
            one = feature_object(g, r)
            if cur:
                if {k: v for k, v in one.items() if k != "text"} != {k: v for k, v in cur.items() if k != "text"}:
                    tu.refuse("%s: the Installation Model's scope or status drifted in Atlas" % pid)
            p.setdefault("features", {})["installationModel"] = one
            apply_basis(g, p, one["text"])
            notes.append("%s %s" % (it["change"], g.install_lead_phrase(one["text"])))
        for it in [x for x in plan.get("vat") or [] if x["productId"] == pid]:
            ok = accepted.get(it["organisation"]) or tu.refuse("%s: no accepted VAT terms entry for %s" % (pid, it["organisation"]))
            if pid not in ok or sorted(ok[pid]["priceRecordIds"]) != sorted(it["priceRecordIds"]) or ok[pid]["contraryVatWording"]:
                tu.refuse("%s: the VAT terms register does not name this product's price records" % pid)
            if sorted(p["priceEvidenceRef"]["recordIds"]) != sorted(it["priceRecordIds"]):
                tu.refuse("%s: plan price records are not the published ones" % pid)
            for rid in it["priceRecordIds"]:
                pr = pricing.get(rid) or tu.refuse("%s: price record %s is not in the Atlas read" % (pid, rid))
                if norm(tu.fv(pr, "Price Includes VAT")) != "Yes" or num(tu.fv(pr, "Base Price")) != num(p["price"]):
                    tu.refuse("%s: Atlas price record %s does not read VAT Yes at the published price" % (pid, rid))
            p["vatStatus"] = "Yes"
            p["priceEvidence"]["includesVat"] = "Yes"
            p["priceEvidence"]["vatBasis"] = it["basis"]
            notes.append("VAT Yes (supplier terms)")
        for it in [x for x in plan.get("priceType") or [] if x["productId"] == pid]:
            pr = pricing.get(it["priceRecordId"]) or tu.refuse("%s: price record missing" % pid)
            if p["priceEvidenceRef"]["recordIds"] != [it["priceRecordId"]] or p["priceType"] != it["from"] \
                    or norm(tu.fv(pr, "Price Type")) != it["to"] or num(tu.fv(pr, "Base Price")) != num(p["price"]):
                tu.refuse("%s: the Price Type correction does not match Atlas or the published record" % pid)
            p["priceType"] = p["priceEvidence"]["priceType"] = p["priceEvidenceRef"]["priceType"] = it["to"]
            p["priceIsRangeFloor"] = range_floor(p)
            notes.append("Price Type %s -> %s" % (it["from"], it["to"]))
        for it in [x for x in plan.get("price") or [] if x["productId"] == pid]:
            pr = pricing.get(it["priceRecordId"]) or tu.refuse("%s: price record missing" % pid)
            pe = p["priceEvidence"]
            if p["priceEvidenceRef"]["recordIds"] != [it["priceRecordId"]] or num(p["price"]) != num(it["publishedPrice"]) \
                    or num(pe.get("to")) != num(it["publishedTo"]):
                tu.refuse("%s: the published price is not the plan's" % pid)
            checks = [("Base Price", num(tu.fv(pr, "Base Price")) == num(it["approvedPrice"])),
                      ("Price To", num(tu.fv(pr, "Price To")) == num(it["approvedTo"])),
                      ("Last Price Check", tu.fv(pr, "Last Price Check") == it["checked"]),
                      ("Price Type", norm(tu.fv(pr, "Price Type")) == p["priceType"]),
                      ("VAT", norm(tu.fv(pr, "Price Includes VAT")) == pe.get("includesVat")),
                      ("Currency", tu.fv(pr, "Currency") == p["currency"]),
                      ("Status", norm(tu.fv(pr, "Status")) == p["priceStatus"])]
            bad = [n for n, ok in checks if not ok]
            if bad:
                tu.refuse("%s: Atlas record %s does not match the approved correction: %s" % (pid, it["priceRecordId"], bad))
            newp = int(it["approvedPrice"])
            p["price"] = newp
            pe["base"] = newp
            pe["to"] = int(it["approvedTo"])
            p["priceEvidenceRef"]["lastPriceCheck"] = it["checked"]
            p["priceIsRangeFloor"] = range_floor(p)
            notes.append("price %s -> %s, to %s -> %s" % (it["publishedPrice"], it["approvedPrice"], it["publishedTo"], it["approvedTo"]))
        allowed = set().union(*(ALLOWED[k] for k in kinds[pid]))
        moved = paths(old, p)
        if not moved or moved - allowed:
            tu.refuse("%s: the correction would change %s" % (pid, sorted(moved - allowed) or "nothing"))
        org_names.add(p["organisation"])
        rows.append((pid, p["productName"], p["organisation"], sorted(kinds[pid]), "; ".join(notes)))
    uni["governedDigest"] = g.governed_digest(uni["products"])
    others = [k for k in set(before) | set(uni) if k not in ("products", "governedDigest") and before.get(k) != uni.get(k)]
    if others:
        tu.refuse("the universe header would change beyond governedDigest: %s" % others)
    b_by = {p["productId"]: p for p in before["products"]}
    stray = [p["productId"] for p in uni["products"] if p["productId"] not in targets and p != b_by.get(p["productId"])]
    if stray or len(before["products"]) != len(uni["products"]):
        tu.refuse("records other than the plan's products would change: %s" % stray[:5])
    new = tu.dump1(uni)

    rep = {"org_id": None}
    wt = pathlib.Path(tempfile.mkdtemp(prefix="pmc-wt-")) / "wt"
    tu.sh(["git", "worktree", "add", "--detach", str(wt), "HEAD"], root, check=True)
    try:
        (wt / tu.GARDEN).write_text(new, encoding="utf-8")
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
        report_name = "%s/%s-methodology-correction.md" % (tu.REPORT_DIR, stamp)
        tu.refreeze_search(wt, report_name, rep)
        tu.run_builders(wt, rep)
        moved_files = tu.boundary(root, wt, targets, org_names, rep)
        results = tu.validate(root, wt, moved_files, rep)
        L = ["# Pricing methodology correction — %s (%s)" % (plan["id"], date), "",
             "- Tool: atlas-tools/publish-methodology-correction.py (installation classification, supplier-terms VAT, "
             "approved Price Types and approved prices only; downstream steps from publish-targeted-update.py)",
             "- Plan: `%s`" % plan_path.as_posix().split("/atlas-tools/")[-1],
             "- Built on commit `%s`" % head_sha[:12],
             "- Mode: %s" % ("APPLY" if a.apply else "DRY RUN"), "",
             "- Atlas read `%s` sha256 `%s`" % (pathlib.Path(a.snapshot).name, snap_sha),
             "- Fidelity: the basis derivation reproduced all %d published records outside the plan"
             % (len(uni["products"]) - len(targets)), "",
             "Approval: " + plan["approved"], "",
             "## Products (%d)" % len(rows), "",
             "| Product | Organisation | Changes |", "|---|---|---|"]
        for pid, n, o, ks, nt in rows:
            L.append("| `%s` %s | %s | %s |" % (pid, n, o, nt))
        L += ["", "Header: governedDigest `%s…` → `%s…`" % (before["governedDigest"][:16], uni["governedDigest"][:16])]
        if rep.get("search_pin"):
            L += ["", "Search universe pin re-frozen `%s…` → `%s…`" % (rep["search_pin"][0][:16], rep["search_pin"][1][:16])]
        L += ["", "## Validation", ""] + ["- %s %s%s" % (v, n, (" — " + d) if d else "") for n, v, d in results]
        L += ["", "## Files that change", ""] + ["- " + f for f in moved_files]
        text = "\n".join(L) + "\n"
        print(text)
        if a.report:
            pathlib.Path(a.report).write_text(text, encoding="utf-8")
        if any(v == "FAIL" for _, v, _ in results):
            tu.refuse("validation failed")
        if not a.apply:
            print("DRY RUN — nothing written.")
            return 0
        for f in moved_files:
            shutil.copy2(wt / f, root / f)
        (root / report_name).write_text(text, encoding="utf-8")
        print("APPLIED — %d file(s) + report %s. Nothing committed." % (len(moved_files), report_name))
        return 0
    finally:
        tu.sh(["git", "worktree", "remove", "--force", str(wt)], root)
        shutil.rmtree(wt.parent, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
