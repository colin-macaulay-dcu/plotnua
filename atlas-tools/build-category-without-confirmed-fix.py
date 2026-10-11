#!/usr/bin/env python3
"""PlotNua — build-category-without-confirmed-fix.py

A BOUNDED BUILDER. One change, to one statistic, in
.github/scripts/generate_additional_home_universe.py.

THE DEFECT, MEASURED 11 October 2026.

    TypeError: '<' not supported between instances of 'NoneType' and 'NoneType'
    generate_additional_home_universe.py:475  "categoryWithoutConfirmed"

Line 403 writes the product code as `txt(cell(p, "Product Code")) or None`, so
an uncoded product arrives in `emitted` as None. Line 475 feeds those values
straight to `sorted()`. One None would have sorted fine -- a one-element sort
compares nothing -- so this needed TWO uncoded products to surface, and two is
what the fresh snapshot had:

    recFek9ErsnKt6uKN   Yardbox Aspect Modular Homes
    recPermX1OwzI2o1Y   Yardbox Bothán

Both created 2026-09-29, both Additional Home, both with NO Product Code and
NO Habitation Classification -- so both land in the not-confirmed set that
this statistic lists. `Product Code` is requested by the snapshot but is NOT
in REQUIRED_PRODUCT_FIELDS, so an uncoded product is a legal snapshot.

THE ASYMMETRY IS THE REAL DEFECT. The sibling statistic three lines below,
`confirmedWithoutCategory`, reads `txt(cell(p, "Product Code"))` directly and
gets `''` -- always sortable, never a crash. The same quantity was read two
different ways in adjacent lines. Only one of them could fail, and it did.

It is the ONLY instance of its class: every other sorted() in the generator
either sorts a closed token set, filters on truthiness, or sorts the raw
txt() string. Audited, not assumed.

THE CONTRACT. `categoryWithoutConfirmed` is a governance reconciliation
statistic -- Additional Home products whose habitation is not confirmed, so a
curator can go and assess them. It is paired with `confirmedWithoutCategory`,
the opposite gap. Nothing in the repository consumes either; both are read by
people. So the contract is: a stable, sorted, legible list of identifiers.

THE FIX honours three constraints at once:

  * no uncoded product is DROPPED. Silence is what let two of them sit
    unnoticed since 29 September.
  * no code is INVENTED, and no placeholder stands in for one.
  * the raw Airtable record id is NOT used. It would be the obvious
    identifier, and it is forbidden here: this key is not in PROVENANCE_KEYS,
    so the public-disclosure firewall's "raw record id" pattern would catch it
    and fail the generator -- correctly.

So the coded products stay a clean sorted list of codes, which is what the key
name promises, and the uncoded ones are named in their own key by PRODUCT
NAME: governed data, already published on every record in the artefact, always
a string because `Product Name` is a required field read through txt().

IDEMPOTENT. Run twice and the second run reports nothing to do.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / ".github" / "scripts" / "generate_additional_home_universe.py"

OLD = '''        "categoryWithoutConfirmed": sorted(
            r["productCode"] for r in emitted
            if r["habitation"]["state"] != CONFIRMED_HABITATION),'''

NEW = '''        # PRODUCT CODE IS NOT GUARANTEED, AND THIS STATISTIC USED TO ASSUME IT
        # WAS. "Product Code" is requested by the snapshot but is not in
        # REQUIRED_PRODUCT_FIELDS, and the record above writes it as
        # `txt(...) or None`. Two uncoded Additional Home products therefore
        # made sorted() compare None with None, and the generator died on its
        # last statistic after all the real work was done. Measured 11 October
        # 2026 against the two Yardbox records created on 29 September.
        #
        # The sibling statistic immediately below reads txt() directly and
        # gets '' -- always sortable. The same quantity was read two ways in
        # adjacent lines, and only one of them could fail.
        #
        # An uncoded product is neither dropped nor given an invented code.
        # The coded ones remain a sorted list of codes, which is what this key
        # name promises; the uncoded ones are named in their own key, by
        # PRODUCT NAME. Not by record id: this key is not one of the declared
        # provenance keys below, so the firewall's raw-record-id pattern would
        # catch one here, and it would be right to.
        "categoryWithoutConfirmed": sorted(
            r["productCode"] for r in emitted
            if r["habitation"]["state"] != CONFIRMED_HABITATION
            and r["productCode"]),
        # THE GAP, STATED RATHER THAN INFERRED. Empty on a clean snapshot.
        # Non-empty means: these products are in the Additional Home category,
        # their habitation is not confirmed, and they carry no Product Code,
        # so they cannot be referred to by code in any downstream conversation.
        "categoryWithoutConfirmedUncoded": sorted(
            r["productName"] for r in emitted
            if r["habitation"]["state"] != CONFIRMED_HABITATION
            and not r["productCode"]),'''


def die(msg: str) -> None:
    print(f"REFUSING: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report what would change and write nothing")
    ap.add_argument("--revert", action="store_true",
                    help="restore the sidecar and verify byte identity")
    args = ap.parse_args()

    if not TARGET.exists():
        die(f"{TARGET} does not exist.")
    src = TARGET.read_text(encoding="utf-8")
    bak = TARGET.with_suffix(TARGET.suffix + ".bak-cwc")

    if args.revert:
        if not bak.exists():
            die(f"no sidecar at {bak}.")
        shutil.copyfile(bak, TARGET)
        print(f"reverted. sha256 {hashlib.sha256(TARGET.read_bytes()).hexdigest()[:16]}")
        return

    if "categoryWithoutConfirmedUncoded" in src:
        print("already applied — nothing to do.")
        return

    n = src.count(OLD)
    if n != 1:
        die(f"the anchor appears {n} times, expected exactly 1. The generator "
            "has changed; re-read line 474 before editing.")

    out = src.replace(OLD, NEW)

    # The builder touches ONE statistic. Everything that makes this generator
    # safe must be bit-for-bit untouched.
    for name, token in (
        ("the firewall", "PROVENANCE_KEYS"),
        ("the firewall scan", "public-disclosure firewall violation"),
        ("the publication gate", "publicVisibility"),
        ("the imagery gate", "_approved_imagery"),
        ("the hold derivation", "publication_hold"),
        ("the sibling statistic", "confirmedWithoutCategory"),
        ("the Class 3A assessment", "class3a"),
    ):
        if out.count(token) != src.count(token):
            die(f"{name} changed ({token}). Refusing.")

    try:
        ast.parse(out)
    except SyntaxError as e:
        die(f"the result does not parse: {e}")

    added = len(out.splitlines()) - len(src.splitlines())
    if args.check:
        print(f"--check: would add {added} lines, remove 0, and touch exactly "
              "one statistic.")
        return

    if not bak.exists():
        shutil.copyfile(TARGET, bak)
    TARGET.write_text(out, encoding="utf-8")

    if out.replace(NEW, OLD) != src:
        die("the edit is not reversible byte for byte.")
    print(f"applied: +{added} lines, 0 removed.")
    print(f"  sidecar {bak.name}")
    print(f"  sha256  {hashlib.sha256(TARGET.read_bytes()).hexdigest()[:16]}")


if __name__ == "__main__":
    main()
