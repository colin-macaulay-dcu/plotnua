#!/usr/bin/env python3
"""
PROVE NAMED PRICE CONFIGURATIONS AND THE VAT BASIS
==================================================
Direct unit tests against the real `_price_state()` in
.github/scripts/additional_home_qualification.py. No snapshot, no Airtable,
no network: synthetic rows in the exact shape the generator passes.

WHY THIS EXISTS. The old `_price_state()` returned on the FIRST pricing row
carrying a number. A supplier publishing two prices -- BIOBUILDS publishes
Exterior Finished and Turnkey for each model -- would have had one chosen by
row order and the other silently discarded, producing a figure that looked as
verified as any other. Every guard in the repository would have passed. The
tests below are the ones that would have caught it.

    python3 atlas-tools/prove-price-configurations.py

Exit 0 = all pass.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".github" / "scripts"))

try:
    from additional_home_qualification import _price_state
except ImportError as e:
    sys.exit("REFUSE: the qualification module is not importable (%s). This "
             "is an instrument failure, not a logic failure: do not record "
             "it as a pass." % e)


def row(amount=None, config=None, basis=None, rate=None,
        ptype="Published Price", currency="EUR", field="Base Price"):
    """One Airtable pricing row in the shape cell() expects."""
    f = {"Price Type": ptype, "Currency": currency}
    if amount is not None:
        f[field] = amount
    if config is not None:
        f["Configuration"] = config
    if basis is not None:
        f["Price Basis"] = basis
    if rate is not None:
        f["VAT Rate %"] = rate
    return {"fields": f}


RESULTS = []


def check(cid, desc, cond, detail=""):
    RESULTS.append((cid, bool(cond), desc, detail))


# ── C1 · the regression that motivated the change ──────────────────────────
# Two numeric rows, no Configuration. The OLD code returned €105,000 and threw
# €163,000 away. The new code must refuse.
st, amt, cur, pt, extra = _price_state([row(105000.0), row(163000.0)])
check("C1", "two unnamed numeric rows refuse rather than pick one",
      st == "PRICE_AMBIGUOUS_MULTI_ROW" and amt is None,
      "state=%s amount=%s" % (st, amt))
check("C1b", "the refusal says how many rows were in conflict",
      extra.get("ambiguousRowCount") == 2, str(extra))

# ── C2 · the supported two-configuration case ──────────────────────────────
wanderlust = [
    row(163000.0, "Turnkey", "Includes VAT", 23),
    row(105000.0, "Exterior Finished", "Includes VAT", 23),
]
st, amt, cur, pt, extra = _price_state(wanderlust)
cfg = extra.get("configurations") or []
check("C2", "two named configurations are both kept",
      st == "VERIFIED_NUMERIC_PRICE" and len(cfg) == 2, "%s %d" % (st, len(cfg)))
check("C2b", "configurations are ordered cheapest first",
      [c["amount"] for c in cfg] == [105000.0, 163000.0],
      str([c["amount"] for c in cfg]))
check("C2c", "labels and keys survive",
      [c["label"] for c in cfg] == ["Exterior Finished", "Turnkey"]
      and [c["key"] for c in cfg] == ["exterior-finished", "turnkey"],
      str([(c["key"], c["label"]) for c in cfg]))
check("C2d", "the retained scalar equals the LOWEST configuration",
      amt == 105000.0, "amount=%s" % amt)
check("C2e", "VAT basis and rate are carried",
      extra.get("basis") == "INCLUDES_VAT" and extra.get("vatRatePercent") == 23,
      str((extra.get("basis"), extra.get("vatRatePercent"))))

# Serenity, the second real pair, ordered the other way round in the input.
st, amt, _, _, extra = _price_state([
    row(191000.0, "Exterior Finished", "Includes VAT", 23),
    row(306000.0, "Turnkey", "Includes VAT", 23)])
check("C2f", "Serenity's pair behaves identically whatever the row order",
      amt == 191000.0
      and [c["amount"] for c in extra["configurations"]] == [191000.0, 306000.0],
      "amount=%s" % amt)

# ── C3 · every other supplier is untouched ─────────────────────────────────
st, amt, cur, pt, extra = _price_state([row(21490.0)])
check("C3", "a single unnamed numeric row still verifies, as today",
      st == "VERIFIED_NUMERIC_PRICE" and amt == 21490.0, "%s %s" % (st, amt))
check("C3b", "a single unnamed row emits NO configurations block",
      "configurations" not in extra, str(sorted(extra)))

st, amt, _, pt, _ = _price_state([row(ptype="Custom Quote")])
check("C4", "a quote-only row is still EVIDENCED_POA_QUOTE",
      st == "EVIDENCED_POA_QUOTE" and amt is None, st)

st, amt, _, _, _ = _price_state([])
check("C5", "no rows is still PRICE_NOT_PUBLISHED",
      st == "PRICE_NOT_PUBLISHED" and amt is None, st)

st, amt, _, _, _ = _price_state([row(ptype="Something Else")])
check("C6", "a row with neither number nor quote type stays not-published",
      st == "PRICE_NOT_PUBLISHED", st)

# ── C7 · VAT is never guessed ──────────────────────────────────────────────
st, amt, _, _, extra = _price_state([row(105000.0)])
check("C7", "a row with no Price Basis yields VAT_UNKNOWN, never a default",
      extra.get("basis") == "VAT_UNKNOWN", str(extra.get("basis")))

st, amt, _, _, extra = _price_state([
    row(105000.0, "Exterior Finished", "Includes VAT", 23),
    row(163000.0, "Turnkey", "Excludes VAT", 23)])
check("C7b", "rows that disagree about VAT are NOT averaged into one basis",
      extra.get("basis") == "VAT_UNKNOWN", str(extra.get("basis")))

st, amt, _, _, extra = _price_state([row(105000.0, "Exterior Finished",
                                         "Not stated")])
check("C7c", "'Not stated' maps to VAT_UNKNOWN, not to a silent inclusive",
      extra.get("basis") == "VAT_UNKNOWN", str(extra.get("basis")))

# ── C8 · the numeric fields other than Base Price still work ───────────────
st, amt, _, _, _ = _price_state([row(94900.0, field="Price From")])
check("C8", "Price From is still read as a numeric price", amt == 94900.0,
      str(amt))

# ── C9 · a zero or negative is not a price ─────────────────────────────────
st, amt, _, _, _ = _price_state([row(0)])
check("C9", "zero is not treated as a published price",
      st == "PRICE_NOT_PUBLISHED" and amt is None, st)

# ── C10 · one named row is representable without being ambiguous ───────────
st, amt, _, _, extra = _price_state([row(105000.0, "Exterior Finished",
                                         "Includes VAT", 23)])
check("C10", "a single NAMED configuration still carries its label",
      st == "VERIFIED_NUMERIC_PRICE" and amt == 105000.0
      and len(extra.get("configurations") or []) == 1,
      "%s %s" % (st, extra.get("configurations")))

# ── C11 · three rows, partially named, is still a refusal ──────────────────
st, amt, _, _, _ = _price_state([
    row(105000.0, "Exterior Finished"), row(163000.0), row(306000.0, "Turnkey")])
check("C11", "partially named numeric rows refuse; naming some is not enough",
      st == "PRICE_AMBIGUOUS_MULTI_ROW" and amt is None, st)


print("\nPRICE CONFIGURATIONS AND VAT BASIS")
print("=" * 74)
failed = 0
width = max(len(c) for c, _, _, _ in RESULTS)
for cid, ok, desc, detail in RESULTS:
    print("  %s  %-*s %s%s" % ("PASS" if ok else "FAIL", width, cid, desc,
                               ("  [%s]" % detail) if detail else ""))
    failed += 0 if ok else 1
print("\n%d checks, %d passed, %d failed\n" % (len(RESULTS),
                                               len(RESULTS) - failed, failed))
sys.exit(1 if failed else 0)
