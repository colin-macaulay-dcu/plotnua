#!/usr/bin/env python3
"""PlotNua — build-property-claim-excision.py

A BOUNDED BUILDER. One rule, added at the transformation layer, plus the
promotion of one regex to a single shared definition.

THE DEFECT, MEASURED 11 October 2026.

    2 public-disclosure firewall violation(s). Nothing written.
      .products[129].description
      .products[136].description

Both carry, inside the Airtable DESCRIPTION field:

    SITING: "If your site is long and narrow, this residential log cabin is
    the perfect solution! ..."

The firewall's "property assertion" pattern matches `your site is`. It was
RIGHT to. Published in PlotNua's own description field, that sentence reads as
PlotNua telling a homeowner a cabin suits their site — and the same Atlas
record says, two paragraphs later, that "property-specific eligibility remains
a Property Check matter". The firewall caught a genuine overclaim, not a false
positive.

WHY IT REACHED THE PUBLIC FIELD. homeowner_text() drops a sentence only when
it OPENS with a phrase in INTERNAL_LEAD_PHRASES. "SITING:" is not in that
closed list, so the sentence survived into `.description`, where the firewall
then refused the whole artefact.

THE FIX IS AT THE TRANSFORMATION LAYER, which is where the rule belongs:
PlotNua must never publish a second-person property claim, whoever wrote it —
supplier marketing or curator prose. The offending SENTENCE is excised; the
rest of the description survives. Nothing is invented, nothing is substituted,
and the full research text is untouched in Airtable.

ONE DEFINITION, NOT TWO. The pattern moves to atlas_common as
PROPERTY_CLAIM_RE and the generator's firewall entry references it. A detector
and its remover that each carry their own copy of a regex will drift, and the
day they drift is the day the remover stops removing what the detector still
catches.

THE FIREWALL IS NOT TOUCHED, not relaxed, and not bypassed. It still scans the
artefact and still fails closed. This fix means it has nothing to find — and if
it ever does again, it still stops the build.

BLAST RADIUS, MEASURED BEFORE WRITING: across the whole 22 September snapshot
(701 products, every category), ZERO published descriptions contain a
second-person property claim. This rule changes nothing that existed before
the 28 September MyCabin intake.

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
COMMON = ROOT / ".github" / "scripts" / "atlas_common.py"
GEN = ROOT / ".github" / "scripts" / "generate_additional_home_universe.py"

# ── atlas_common: excise the claim CLAUSE, before the sentence split ───────
#
# Placed beside the existing DO NOT RANK rule, which is this function's own
# precedent for "remove the clause, keep the evidence either side of it", and
# it must run BEFORE the sentence loop. The reason is measured, not stylistic:
# the splitter's lookbehind is (?<=[.!?]), so a sentence ending in `."` is NOT
# a split point. A first attempt dropped whole SEGMENTS instead, and on the
# real MyCabin text that merged
#     RESIDENTIAL CONFIGURATION - PUBLISHED: "...open-plan living room and
#     kitchen area..."   +   SITING: "If your site is long and narrow..."
# into a single segment and deleted both — destroying genuine homeowner
# evidence in order to remove a claim standing next to it. T4 caught it.
A_OLD = '''    s = re.sub(r"\\bflagged as an integrity issue\\b", "flagged", s,
               flags=re.IGNORECASE)'''

A_NEW = '''    s = re.sub(r"\\bflagged as an integrity issue\\b", "flagged", s,
               flags=re.IGNORECASE)
    # A SECOND-PERSON PROPERTY CLAIM IS NEVER PUBLISHED, WHOEVER WROTE IT.
    #
    # Measured 11 October 2026: two MyCabin records carried, inside the
    # Description field, the supplier's own line
    #     SITING: "If your site is long and narrow, this residential log
    #     cabin is the perfect solution! ..."
    # No lead phrase matched, because "SITING:" is not an internal label, and
    # the public-disclosure firewall then refused the whole artefact on
    # `your site is`. It was right to: in PlotNua's own description field that
    # sentence reads as PlotNua telling a homeowner their site suits the
    # building — and the same record says, two paragraphs later, that
    # property-specific eligibility remains a Property Check matter.
    #
    # Deliberately about the CLAIM, not the label. Relabelling it, or a
    # supplier writing the same thing with no label at all, does not get it
    # published.
    #
    # CLAUSE-LEVEL, like the DO NOT RANK rule above, and placed here for a
    # measured reason rather than a stylistic one: the sentence splitter below
    # uses (?<=[.!?]), so a sentence ending in `."` is NOT a split point. A
    # first attempt dropped whole SEGMENTS after the split, and on the real
    # MyCabin text that merged the RESIDENTIAL CONFIGURATION sentence with the
    # SITING one and deleted both — throwing away genuine homeowner evidence
    # to remove a claim standing next to it. Only the sentence carrying the
    # claim goes; the evidence either side of it stays, and the full text
    # remains in Airtable for the next researcher.
    s = re.sub(r"(?:^|(?<=[.!?]))\\s*[^.!?]*?(?:" + PROPERTY_CLAIM_RE.pattern
               + r")[^.!?]*[.!?]", " ", s, flags=re.IGNORECASE)'''

# The pattern itself, placed with the other module-level export rules.
B_OLD = '''INTERNAL_LEAD_PHRASES = ('''
B_NEW = '''# SECOND-PERSON PROPERTY CLAIMS. One definition, used by BOTH the remover in
# homeowner_text() below and the public-disclosure firewall in the generators.
# Two copies of this regex would drift, and the day they drift is the day the
# remover stops removing what the detector still catches.
PROPERTY_CLAIM_RE = re.compile(
    r"\\b(you (?:can|may) build|your (?:property|site|garden) (?:is|qualifies)"
    r"|exempt(?:ion)? applies|planning permission (?:is )?(?:granted|not required))\\b",
    re.I)

INTERNAL_LEAD_PHRASES = ('''

# ── generator: the firewall references the shared pattern ──────────────────
C_OLD = '''    ("property assertion", re.compile(
        r"\\b(you (?:can|may) build|your (?:property|site|garden) (?:is|qualifies)"
        r"|exempt(?:ion)? applies|planning permission (?:is )?(?:granted|not required))\\b", re.I)),'''
C_NEW = '''    # THE SAME OBJECT the remover in homeowner_text() uses, imported rather
    # than copied, so the detector and the remover cannot drift apart.
    ("property assertion", PROPERTY_CLAIM_RE),'''

D_OLD = '''from atlas_common import cell, txt, homeowner_text, fail'''
D_NEW = '''from atlas_common import (cell, txt, homeowner_text, fail,
                           PROPERTY_CLAIM_RE)'''


def die(msg: str) -> None:
    print(f"REFUSING: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--revert", action="store_true")
    args = ap.parse_args()

    for p in (COMMON, GEN):
        if not p.exists():
            die(f"{p} does not exist.")
    csrc, gsrc = COMMON.read_text(encoding="utf-8"), GEN.read_text(encoding="utf-8")
    cbak = COMMON.with_suffix(COMMON.suffix + ".bak-propclaim")
    gbak = GEN.with_suffix(GEN.suffix + ".bak-propclaim")

    if args.revert:
        if not (cbak.exists() and gbak.exists()):
            die("a sidecar is missing; refusing a partial revert.")
        shutil.copyfile(cbak, COMMON)
        shutil.copyfile(gbak, GEN)
        print("reverted both files.")
        return

    if "PROPERTY_CLAIM_RE" in csrc:
        print("already applied — nothing to do.")
        return

    for label, src, anchor in (("atlas_common sentence loop", csrc, A_OLD),
                               ("atlas_common lead phrases", csrc, B_OLD),
                               ("generator firewall entry", gsrc, C_OLD),
                               ("generator import", gsrc, D_OLD)):
        n = src.count(anchor)
        if n != 1:
            die(f"the {label} anchor appears {n} times, expected exactly 1. "
                "The source has changed; re-read it before editing.")

    cout = csrc.replace(B_OLD, B_NEW).replace(A_OLD, A_NEW)
    gout = gsrc.replace(D_OLD, D_NEW).replace(C_OLD, C_NEW)

    # THE FIREWALL MUST STILL HAVE ALL SEVEN RULES, and every other guard in
    # the generator must be bit-for-bit untouched.
    if gout.count('("') < gsrc.count('("') - 0:
        pass  # counted explicitly below instead
    for name, token, where in (
        ("the firewall list", "FIREWALL = [", gout),
        ("the firewall scan", "public-disclosure firewall violation", gout),
        ("the provenance key set", "PROVENANCE_KEYS", gout),
        ("the publication gate", "publicVisibility", gout),
        ("the imagery gate", "_approved_imagery", gout),
        ("the record-id rule", "raw record id", gout),
        ("the rule-name rule", "internal rule name", gout),
        ("the directive rule", "governance directive", gout),
    ):
        if where.count(token) != gsrc.count(token):
            die(f"{name} changed ({token}). Refusing.")
    if gout.count("habitation basis rule name") != 1:
        die("the firewall rule set changed shape. Refusing.")

    for name, out in (("atlas_common.py", cout), ("the generator", gout)):
        try:
            ast.parse(out)
        except SyntaxError as e:
            die(f"{name} does not parse: {e}")

    if args.check:
        print(f"--check: atlas_common +{len(cout.splitlines()) - len(csrc.splitlines())} "
              f"lines, generator {len(gout.splitlines()) - len(gsrc.splitlines()):+d} lines.")
        return

    if not cbak.exists():
        shutil.copyfile(COMMON, cbak)
    if not gbak.exists():
        shutil.copyfile(GEN, gbak)
    COMMON.write_text(cout, encoding="utf-8")
    GEN.write_text(gout, encoding="utf-8")

    back_c = cout.replace(A_NEW, A_OLD).replace(B_NEW, B_OLD)
    back_g = gout.replace(C_NEW, C_OLD).replace(D_NEW, D_OLD)
    if back_c != csrc or back_g != gsrc:
        die("the edit is not reversible byte for byte.")

    print("applied.")
    for p in (COMMON, GEN):
        print(f"  {p.name:46} sha256 {hashlib.sha256(p.read_bytes()).hexdigest()[:16]}")


if __name__ == "__main__":
    main()
