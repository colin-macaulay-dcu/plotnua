#!/usr/bin/env python3
"""PlotNua — build-snapshot-configuration-field.py

A BOUNDED BUILDER. It makes one change to .github/scripts/snapshot_atlas.py:
the acquisition contract requests the Configuration field, and refuses a
snapshot in which a multi-priced Additional Home product lacks it.

THE DEFECT, MEASURED 11 October 2026.
  additional_home_qualification._configuration_of() reads a pricing field
  called "Configuration". PRICING_FIELDS in snapshot_atlas.py never asked
  for it, because that list predates the named-configuration price contract.

  Airtable returns only the fields you request. So a fresh snapshot carries
  no Configuration, _configuration_of() returns None for every row, and two
  numeric rows with no configuration produce PRICE_AMBIGUOUS_MULTI_ROW — a
  HELD state. Measured against the real functions and the live Atlas rows:

    with Configuration     VERIFIED_NUMERIC_PRICE, EUR 105,000 / 163,000,
                           both labelled, basis INCLUDES_VAT, three terms
    without it             PRICE_AMBIGUOUS_MULTI_ROW, amount None

  The held state is honest — it says Atlas cannot choose between two prices.
  It is also wrong: Atlas CAN choose, because the rows are labelled. The
  wrongness is in the acquisition, not the reasoning.

WHY A TARGETED REFUSAL RATHER THAN A REQUIRED FIELD.
  Adding "Configuration" to REQUIRED_PRICING_FIELDS would fail the snapshot
  whenever NO record carries it. Today only BIOBUILDS does, so archiving two
  rows would break an unrelated snapshot for no reason. The check added here
  fires on the condition that actually matters: a product with more than one
  numeric price and no configuration to tell them apart.

IDEMPOTENT. Run twice and the second run reports nothing to do.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / ".github" / "scripts" / "snapshot_atlas.py"

# ── ANCHOR 1: the field list ────────────────────────────────────────────────
A1_OLD = '''    "Product", "Base Price", "Price From", "Price To", "Currency",
    "Price Type", "Price Includes VAT", "Status", "Primary Price",
    "Evidence Scope", "Known Exclusions", "Last Price Check", "Sources",
]'''
A1_NEW = '''    "Product", "Base Price", "Price From", "Price To", "Currency",
    "Price Type", "Price Includes VAT", "Status", "Primary Price",
    "Evidence Scope", "Known Exclusions", "Last Price Check", "Sources",
    # THE NAMED CONFIGURATION. additional_home_qualification reads this field
    # to tell an Exterior Finished price from a Turnkey one. Airtable returns
    # only the fields requested, so omitting it here does not produce a
    # missing label — it produces PRICE_AMBIGUOUS_MULTI_ROW and a product
    # with no published price at all. Added 11 October 2026, after that was
    # measured against the live BIOBUILDS rows.
    "Configuration",
]'''

# ── ANCHOR 2: the check, as an importable module-level function ─────────────
# Module level, not inline in main(), so a proof can drive THE SHIPPED
# FUNCTION rather than a copy of its logic. A proof that tests a paste of the
# rule proves only that the paste works.
A2_OLD = '''def coverage(rows, field):'''
A2_NEW = '''def configuration_problems(ah, pricing):
    """Additional Home products whose multiple numeric prices are unlabelled.

    NOT a blanket required field. "Configuration" is populated on only a
    handful of rows today, so requiring it everywhere would fail a snapshot
    for an absence that is usually correct. This fires on the condition that
    actually breaks publication: a product with MORE THAN ONE numeric price
    and nothing to tell those prices apart. additional_home_qualification
    then returns PRICE_AMBIGUOUS_MULTI_ROW -- an honest held state, and a
    product with no published price at all. Better caught here, loudly, than
    discovered as a blank price on Results."""
    ah_ids = {p["id"] for p in ah}
    numeric_by_product = {}
    for r in pricing:
        f = r.get("fields", {})
        linked = [x.get("id") if isinstance(x, dict) else x
                  for x in (f.get("Product") or [])]
        if not any(isinstance(f.get(k), (int, float))
                   for k in ("Base Price", "Price From", "Price To")):
            continue
        for pid in linked:
            if pid in ah_ids:
                numeric_by_product.setdefault(pid, []).append(r)

    out = []
    for pid, rows in sorted(numeric_by_product.items()):
        if len(rows) < 2:
            continue
        unlabelled = [r.get("id") for r in rows
                      if not txt(cell(r, "Configuration"))]
        if unlabelled:
            name = next((txt(cell(p, "Product Name")) for p in ah
                         if p["id"] == pid), pid)
            out.append(
                f"{name} carries {len(rows)} numeric pricing rows and "
                f"{len(unlabelled)} of them have no Configuration. Atlas "
                "cannot say which price to show, so the product would be "
                "published with no price at all. Rows: "
                + ", ".join(str(u) for u in unlabelled))
    return out


def coverage(rows, field):'''

# ── ANCHOR 3: call it where the other usability checks run ─────────────────
A3_OLD = '''    if problems:
        for p in problems:
            print(f"::error::{p}", file=sys.stderr)'''
A3_NEW = '''    problems.extend(configuration_problems(ah, raw["pricing"]))

    if problems:
        for p in problems:
            print(f"::error::{p}", file=sys.stderr)'''


def die(msg: str) -> None:
    print(f"REFUSING: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report what would change and write nothing")
    ap.add_argument("--revert", action="store_true",
                    help="restore the .bak sidecar and verify byte identity")
    args = ap.parse_args()

    if not TARGET.exists():
        die(f"{TARGET} does not exist.")
    src = TARGET.read_text(encoding="utf-8")
    bak = TARGET.with_suffix(TARGET.suffix + ".bak-config-field")

    if args.revert:
        if not bak.exists():
            die(f"no sidecar at {bak}.")
        shutil.copyfile(bak, TARGET)
        print(f"reverted. sha256 {hashlib.sha256(TARGET.read_bytes()).hexdigest()[:16]}")
        return

    if '"Configuration",' in src and "configuration_problems" in src:
        print("already applied — nothing to do.")
        return

    # Exactly-once anchors. A source that has drifted is a source this builder
    # does not understand, and it stops rather than guessing.
    for name, anchor in (("field list", A1_OLD),
                         ("coverage helper", A2_OLD),
                         ("usability checks", A3_OLD)):
        n = src.count(anchor)
        if n != 1:
            die(f"the {name} anchor appears {n} times, expected exactly 1. "
                "snapshot_atlas.py has changed; re-read it before editing.")

    out = (src.replace(A1_OLD, A1_NEW)
              .replace(A2_OLD, A2_NEW)
              .replace(A3_OLD, A3_NEW))

    # The builder must not touch the token handling, and must leave the file
    # importable.
    if out.count("AIRTABLE_TOKEN") != src.count("AIRTABLE_TOKEN"):
        die("the token handling changed. Refusing.")
    if "cell(" not in out or "txt(" not in out:
        die("cell/txt are not available in this module. Refusing.")
    import ast
    try:
        ast.parse(out)
    except SyntaxError as e:
        die(f"the result does not parse: {e}")

    added = len(out.splitlines()) - len(src.splitlines())
    if args.check:
        print(f"--check: would add {added} lines "
              f"(+1 requested field, +1 refusal) and remove 0.")
        return

    if not bak.exists():
        shutil.copyfile(TARGET, bak)
    TARGET.write_text(out, encoding="utf-8")

    # Reverse-replacement byte identity: undo the edit and confirm we land
    # exactly on what was there before.
    back = (out.replace(A1_NEW, A1_OLD)
               .replace(A2_NEW, A2_OLD)
               .replace(A3_NEW, A3_OLD))
    if back != src:
        die("the edit is not reversible byte for byte. Reverting.")
    print(f"applied: +{added} lines, 0 removed.")
    print(f"  sidecar {bak.name}")
    print(f"  sha256  {hashlib.sha256(TARGET.read_bytes()).hexdigest()[:16]}")


if __name__ == "__main__":
    main()
