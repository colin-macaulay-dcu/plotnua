#!/usr/bin/env python3
"""PlotNua — prove-snapshot-configuration.py

Proves the acquisition contract requests the named price Configuration, and
that snapshot_atlas.configuration_problems() REFUSES a snapshot in which a
multi-priced Additional Home product carries no configuration labels.

It imports THE SHIPPED FUNCTION. It does not re-implement the rule, because a
proof that tests a paste of a rule proves only that the paste works.

It also drives additional_home_qualification._price_state() on the real
BIOBUILDS rows, with and without the field, to show what the omission costs:
a VERIFIED_NUMERIC_PRICE becomes PRICE_AMBIGUOUS_MULTI_ROW and the product is
published with no price at all.

No network. No token. Nothing written.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / ".github" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import snapshot_atlas as snap                      # noqa: E402
import additional_home_qualification as q          # noqa: E402

PASS, FAIL = [], []


def check(name, condition, detail=""):
    (PASS if condition else FAIL).append((name, detail))
    print(f"  {'PASS' if condition else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail}")


# ── the real governed prose, as it stands in Atlas on 11 October 2026 ───────
KE_EXTERIOR = (
    "Irish price INCLUDING 23% VAT. Transport to Ireland and assembly on "
    "prepared ground screws are included. Foundations, utility connections "
    "and site works are quoted per project. Kitchen furniture and appliances "
    "are NOT included. Source: biobuilds.com/ie/wanderlust and "
    "biobuilds.com/ie/turnkey, read 11 October 2026.")
KE_TURNKEY = (
    "Irish price INCLUDING 23% VAT. Turnkey is finished inside and out, "
    "including interior finishes and bathroom fixtures. Transport to Ireland "
    "and assembly on prepared ground screws are included. Foundations, "
    "utility connections and site works are quoted per project. Kitchen "
    "furniture and appliances are NOT included. Source: "
    "biobuilds.com/ie/turnkey, read 11 October 2026.")

PRODUCT = {"id": "recIBexeX8au55mVn",
           "fields": {"Product Name": "BIOBUILDS Wanderlust",
                      "Product Category": "Additional Home"}}


def price_row(rid, amount, configuration, exclusions):
    f = {"Product": [PRODUCT["id"]], "Base Price": amount, "Currency": "EUR",
         "Price Type": "Standard Price", "Price Includes VAT": "Yes",
         "Status": "Verified", "Evidence Scope": "Product-Specific",
         "Known Exclusions": exclusions}
    if configuration:
        f["Configuration"] = configuration
    return {"id": rid, "fields": f}


LABELLED = [price_row("recA", 105000, "Exterior Finished", KE_EXTERIOR),
            price_row("recB", 163000, "Turnkey", KE_TURNKEY)]
UNLABELLED = [price_row("recA", 105000, None, KE_EXTERIOR),
              price_row("recB", 163000, None, KE_TURNKEY)]
SINGLE = [price_row("recA", 105000, None, KE_EXTERIOR)]


print("\n  SNAPSHOT CONFIGURATION FIELD — PROOF")
print("  " + "-" * 70)

# ── S1: the acquisition contract asks for the field ─────────────────────────
check("S1  the snapshot requests the Configuration field",
      "Configuration" in snap.PRICING_FIELDS,
      f"{len(snap.PRICING_FIELDS)} pricing fields requested")

# ── S2: and does NOT make it blanket-required, which would fail a snapshot
#        for an absence that is usually correct ───────────────────────────────
check("S2  Configuration is not a blanket required field",
      "Configuration" not in snap.REQUIRED_PRICING_FIELDS,
      f"required: {snap.REQUIRED_PRICING_FIELDS}")

# ── S3: the shipped check accepts labelled rows ─────────────────────────────
accepted = snap.configuration_problems([PRODUCT], LABELLED)
check("S3  two LABELLED prices are accepted",
      accepted == [], f"problems: {accepted}")

# ── S4: and refuses unlabelled ones. THE CHECK MUST BE ABLE TO FAIL. ───────
refused = snap.configuration_problems([PRODUCT], UNLABELLED)
check("S4  two UNLABELLED prices are refused",
      len(refused) == 1 and "no Configuration" in refused[0],
      refused[0] if refused else "nothing was refused")

# ── S5: a single unlabelled price is NOT refused. There is no ambiguity in
#        one price, and most of the universe is exactly that. ───────────────
single = snap.configuration_problems([PRODUCT], SINGLE)
check("S5  one unlabelled price is left alone",
      single == [], f"problems: {single}")

# ── S6: a non-Additional-Home product is out of scope ──────────────────────
other = {"id": "recOTHER", "fields": {"Product Name": "A Garden Room",
                                      "Product Category": "Garden Room"}}
rows = [dict(r, fields=dict(r["fields"], Product=[other["id"]]))
        for r in UNLABELLED]
check("S6  a product outside Additional Home is not policed by this check",
      snap.configuration_problems([PRODUCT], rows) == [],
      "the Garden Room price contract is unchanged")

# ── S7 / S8: what the omission actually costs, through the real reader ─────
st_ok, amt_ok, _, _, extra_ok = q._price_state(LABELLED)
st_no, amt_no, _, _, extra_no = q._price_state(UNLABELLED)

check("S7  WITH the field, both configurations are published",
      st_ok == "VERIFIED_NUMERIC_PRICE"
      and len(extra_ok.get("configurations") or []) == 2
      and extra_ok.get("basis") == "INCLUDES_VAT",
      " · ".join(f"€{int(c['amount']):,} {c['label']}"
                 for c in extra_ok.get("configurations") or [])
      + f" · {extra_ok.get('basis')}")

check("S8  WITHOUT it, the product is published with NO price",
      st_no == "PRICE_AMBIGUOUS_MULTI_ROW" and amt_no is None,
      f"state={st_no} amount={amt_no} — this is what the check prevents")

# ── S9: the commercial terms the founder requires survive the intersection ─
terms = extra_ok.get("commercialTerms") or []
wanted = ["TRANSPORT_AND_ASSEMBLY_INCLUDED",
          "FOUNDATIONS_UTILITIES_SITEWORKS_QUOTED_SEPARATELY",
          "KITCHEN_FURNITURE_AND_APPLIANCES_EXCLUDED"]
check("S9  the three shared commercial terms reach the product level",
      terms == wanted, " · ".join(terms) or "none")

print("  " + "-" * 70)
print(f"  {len(PASS) + len(FAIL)} checks, {len(PASS)} passed, {len(FAIL)} failed\n")
sys.exit(1 if FAIL else 0)
