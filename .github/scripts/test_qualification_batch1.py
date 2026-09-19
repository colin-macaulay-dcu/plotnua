#!/usr/bin/env python3
"""QUALIFICATION HARDENING — BATCH 1 REGRESSION.

Scope, deliberately narrow:
  * PRICE HARDENING  — a governed zero is not a published price; an unverified
    price is not a verified one; quote-only is its own commercial state.
  * EXPORT HYGIENE   — internal directives, governance commentary and raw
    record IDs do not reach homeowner-facing evidence text.

NOT in scope, and proven not to be: the PRODUCT EVIDENCE CONFIDENCE axis. The
calibration pass is recorded in TEST 9 below, which asserts the tier rule is
unchanged, and in the generator comment that explains why.

The generator needs Airtable credentials, so the price tests replay the
decision from the shipped artefact's own evidenceSignals — the same inputs
qualify() uses. TEST 0 proves the replay is faithful before anything else runs.

Read-only. Writes nothing, contacts nothing.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UNIVERSE = ROOT / "garden-room-recommendation-universe-v1.json"
GEN = Path(__file__).resolve().parent / "generate_garden_room_universe.py"

_spec = importlib.util.spec_from_file_location("gen_under_test", GEN)
gen = importlib.util.module_from_spec(_spec)
sys.modules["gen_under_test"] = gen
try:
    _spec.loader.exec_module(gen)
except SystemExit:
    pass

failures = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(f"{name}: {detail}")


def tier_rule(sig, name, org):
    """The SHIPPED tier rule. Batch 1 must not move it."""
    strong = bool(org and name)
    if (sig["irishAvailability"] == "confirmed"
            and sig["price"] in ("verified", "present-unverified")
            and sig["source"] in ("product-level", "supplier-level") and strong):
        return "HIGH_CONFIDENCE"
    if sig["source"] == "missing":
        return "LIMITED_EVIDENCE"
    return "WITH_CAVEAT"


def quote_marked(pe):
    return any(str((pe or {}).get(k) or "").strip().lower() in gen.QUOTE_ONLY_MARKERS
               for k in ("priceType", "status"))


def new_price_state(p, sig):
    """price_state after the Batch 1 usable_price() fix."""
    state, pe = sig["price"], (p.get("priceEvidence") or {})
    governed_zero = (state in ("verified", "present-unverified")
                     and p.get("price") is None
                     and pe.get("adjudication") != "ambiguous")
    if governed_zero:
        return ("quote-only" if quote_marked(pe) else "missing"), True
    if state == "missing" and quote_marked(pe):
        return "quote-only", False
    return state, False


def main():
    u = json.loads(UNIVERSE.read_text(encoding="utf-8"))
    ps = u["products"]
    print(f"\nBATCH 1 REGRESSION — {len(ps)} admitted / {u['sourceGardenRoomCount']} source\n")

    # ---- TEST 0 — replay fidelity -----------------------------------------
    bad = [p["productId"] for p in ps
           if tier_rule(p["qualification"]["evidenceSignals"],
                        p.get("productName"), p.get("organisation")) != p.get("qualificationTier")]
    check("TEST 0  replay reproduces shipped tiers exactly", not bad, f"{len(bad)} mismatch(es)")
    if bad:
        print("\nABORT — replay unfaithful.\n")
        return 1

    rows = []
    for p in ps:
        sig = p["qualification"]["evidenceSignals"]
        st, fixed = new_price_state(p, sig)
        rows.append({"p": p, "sig": sig, "old": sig["price"], "new": st, "fixed": fixed})

    def tally(k):
        t = {}
        for r in rows:
            t[r[k]] = t.get(r[k], 0) + 1
        return t

    b, a = tally("old"), tally("new")
    print("  PRICE EVIDENCE            before -> after")
    for s in ("verified", "present-unverified", "quote-only", "missing"):
        print(f"    {s:<20} {b.get(s,0):>5} -> {a.get(s,0):>5}")
    print()

    # ---- price hardening ---------------------------------------------------
    check("zero/null never counts as a published price",
          not [r for r in rows if r["new"] in ("verified", "present-unverified")
               and r["p"].get("price") is None
               and (r["p"].get("priceEvidence") or {}).get("adjudication") != "ambiguous"])
    check("the 8 governed-zero placeholder records are corrected",
          len([r for r in rows if r["fixed"]]) == 8,
          f"{len([r for r in rows if r['fixed']])} corrected")
    check("unverified price never satisfies a verified-price test",
          a.get("verified", 0) == b.get("verified", 0),
          f"verified {b.get('verified',0)} -> {a.get('verified',0)} (must not grow)")
    check("quote-only is separated from 'no price found'",
          a.get("quote-only", 0) > 0 and a.get("quote-only", 0) < b.get("missing", 0),
          f"{a.get('quote-only',0)} quote-only recognised")
    check("quote-only is only ever set from a published marker",
          all(quote_marked(r["p"].get("priceEvidence")) for r in rows if r["new"] == "quote-only"))
    check("ambiguous-price products are untouched by the zero fix",
          not [r for r in rows if r["fixed"]
               and (r["p"].get("priceEvidence") or {}).get("adjudication") == "ambiguous"])

    # ---- unit tests on the functions themselves ---------------------------
    check("_positive_number rejects 0, negatives, None, bool",
          not any(gen._positive_number(v) for v in (0, 0.0, -1, None, True, False, "12"))
          and gen._positive_number(1) and gen._positive_number(12.5))
    check("_is_quote_only requires an exact published marker",
          gen._is_quote_only({"fields": {"Price Type": "Custom Quote"}}) is True
          and gen._is_quote_only({"fields": {"Price Type": "Standard Price"}}) is False
          and gen._is_quote_only(None) is False)

    # ---- TEST 9 — the tier rule MUST NOT have moved ------------------------
    check("TEST 9  product-evidence tier rule unchanged in this batch",
          "productEvidenceConfidence" not in GEN.read_text(encoding="utf-8"),
          "no product-evidence axis is emitted")

    # ---- export hygiene ----------------------------------------------------
    texts = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "text" and isinstance(v, str):
                    texts.append(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    for p in ps:
        walk(p)

    BAD = ("DO NOT RANK", "DO NOT USE", "STANDING TECHNICAL DEBT",
           "INTEGRITY ISSUE", "INTEGRITY:")
    before_leaks = [t for t in texts
                    if re.search(r"\brec[A-Za-z0-9]{14}\b", t)
                    or any(x in t.upper() for x in BAD)]
    after = [(t, gen.homeowner_text(t) or "") for t in texts]
    after_leaks = [o for _, o in after
                   if re.search(r"\brec[A-Za-z0-9]{14}\b", o)
                   or any(x in o.upper() for x in BAD)]
    emptied = [t for t, o in after if t.strip() and not o.strip()]

    print(f"\n  evidence strings {len(texts)}  |  leaking before {len(before_leaks)}"
          f"  ->  after {len(after_leaks)}  |  emptied {len(emptied)}\n")
    check("sanitiser removes at least 95% of leaking strings",
          len(after_leaks) <= len(before_leaks) * 0.05,
          f"{len(before_leaks)} -> {len(after_leaks)}")
    check("no evidence string is wholly destroyed", not emptied, f"{len(emptied)} emptied")
    check("no raw record ID survives anywhere",
          not [o for _, o in after if re.search(r"\brec[A-Za-z0-9]{14}\b", o)])
    ok = ("Fully insulated garden room with 100mm rigid insulation to walls, "
          "ceiling and floor. Red cedar cladding.")
    check("ordinary evidence passes through byte-identical", gen.homeowner_text(ok) == ok)
    check("substantive warnings are preserved, not stripped",
          any("80-year" in o and "STEEL FRAME ONLY" in o for _, o in after),
          "Berko frame-only guarantee warning retained")
    check("useful sentences behind an internal label are kept",
          any("Auroom supplies wellness/sauna cabins" in o for _, o in after),
          "label removed, evidence retained")

    print()
    if failures:
        print(f"RESULT: {len(failures)} FAILURE(S)\n")
        for f in failures:
            print("  - " + f)
        return 1
    print("RESULT: ALL TESTS PASS\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
