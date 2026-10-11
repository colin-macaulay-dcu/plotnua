#!/usr/bin/env python3
"""
BOUNDED BUILDER — TEACH THE GENERATOR'S OWN GATE ABOUT THE EXCEPTION
=====================================================================
One anchored rewrite of _gate_index() in
.github/scripts/generate_additional_home_universe.py.

THE DEFECT THIS FIXES, AND HOW IT WAS FOUND.

The founder authorised publishing BIOBUILDS. The rights record was written,
the JS derivation agreed, 18 assertions passed and 20 mutations proved
capable. Then driving the GENERATOR'S OWN gate function over the real records
returned:

    publication_hold('BIOBUILDS') -> 'listing-review-awaiting-confirmation'

The generator carries its own copy of the rule -- deliberately, so that a
held supplier cannot be published even if the runtime reader is bypassed --
and that copy knew nothing about founder exceptions. Regenerating on the
founder's Mac would therefore have stamped publicVisibility HOLD onto both
BIOBUILDS products, the runtime's second lock would have withheld them, and
the authorised publication would simply not have happened. Every guard would
have stayed green, because every guard was pointed at the other two layers.

THREE MIRRORS OF ONE RULE is the standing hazard here: this function, the
Python mirror in atlas-tools/build-publication-gate-records.py, and the
authoritative JS in atlas-tools/publication-gate.mjs. The third mirror was
the one nobody had taught. PG11 is re-aimed in the same change so the
generator's agreement is asserted from now on rather than assumed.

    python3 atlas-tools/build-generator-exception.py [--check] [--revert]

Exit 0 = applied, or already correct.
"""
import difflib
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / ".github" / "scripts" / "generate_additional_home_universe.py"
BAK = SRC.with_suffix(".py.bak")

CHECK = "--check" in sys.argv
REVERT = "--revert" in sys.argv
SENTINEL = "_founder_waives"


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


OLD = '''        if perm == "DECLINED":
            idx[name] = "permission-declined"
        elif perm == "NONE":
            idx[name] = "no-permission"
        elif perm == "CONDITIONAL":
            idx[name] = "permission-conditional-unresolved"
        elif perm != "GRANTED":
            idx[name] = "permission-state-missing"
        elif rev == "AWAITING_CONFIRMATION":
            idx[name] = "listing-review-awaiting-confirmation"
        elif rev == "CHANGES_REQUESTED":
            idx[name] = "listing-review-changes-requested"
        elif rev not in ("NOT_REQUIRED", "CONFIRMED"):
            idx[name] = "listing-review-state-missing"
        elif assets and assets != "APPROVED":
            idx[name] = "assets-not-approved"
    return idx'''

NEW = '''        # Conditions in the gate's fixed order; the first unsatisfied one
        # decides. Written as a list rather than a chain of elifs so the
        # founder-exception filter below can be applied uniformly instead of
        # being threaded through eight branches.
        conditions = [
            (perm not in ("GRANTED", "CONDITIONAL", "DECLINED", "NONE"),
             "permission-state-missing"),
            (rev not in ("NOT_REQUIRED", "AWAITING_CONFIRMATION", "CONFIRMED",
                         "CHANGES_REQUESTED"), "listing-review-state-missing"),
            (perm == "DECLINED", "permission-declined"),
            (perm == "NONE", "no-permission"),
            (perm == "CONDITIONAL", "permission-conditional-unresolved"),
            (rev == "AWAITING_CONFIRMATION",
             "listing-review-awaiting-confirmation"),
            (rev == "CHANGES_REQUESTED", "listing-review-changes-requested"),
            (bool(assets) and assets != "APPROVED", "assets-not-approved"),
        ]
        accepted = _founder_waives(r)
        for unsatisfied, reason in conditions:
            if not unsatisfied:
                continue
            if reason in accepted:
                continue
            idx[name] = reason
            break
    return idx'''

OLD2 = '''def _gate_index():'''

NEW2 = '''# The four reasons no decision may waive, kept in step with NEVER_WAIVABLE in
# atlas-tools/publication-gate.mjs. A founder can accept the risk of
# publishing early against a grant PlotNua HOLDS; a founder cannot conjure a
# grant that was never given. prove-supplier-publication-gate.mjs (PG11)
# refuses if this list and the JS one ever drift apart.
GATE_NEVER_WAIVABLE = (
    "permission-declined",
    "no-permission",
    "permission-conditional-unresolved",
    "permission-state-missing",
)

GATE_WAIVABLE = (
    "listing-review-awaiting-confirmation",
    "listing-review-changes-requested",
    "listing-review-state-missing",
    "assets-not-approved",
)


def _founder_waives(row):
    """The hold reasons a well-formed founder exception on this row accepts.

    THIRD MIRROR OF ONE RULE, and the one that was missed when the exception
    mechanism was built: the generator keeps its own copy of the gate so a
    held supplier cannot be published even if the runtime reader is bypassed,
    and that copy knew nothing about exceptions. Regenerating would have put
    an authorised supplier straight back on HOLD with every guard green.

    A malformed exception waives NOTHING -- it does not half-work and it does
    not fail open -- and the permission class can never be waived however the
    record is written."""
    ex = row.get("founder_exception")
    if not isinstance(ex, dict):
        return ()
    if not isinstance(ex.get("authorised_by"), str) or not ex["authorised_by"]:
        return ()
    date = str(ex.get("decision_date") or "")
    if len(date) != 10 or date[4] != "-" or date[7] != "-":
        return ()
    if ex.get("supplier_confirmation_received") is not False:
        return ()
    if len(str(ex.get("basis") or "").strip()) < 20:
        return ()
    waives = ex.get("waives")
    if not isinstance(waives, list) or not waives:
        return ()
    for w in waives:
        if w in GATE_NEVER_WAIVABLE or w not in GATE_WAIVABLE:
            # One bad entry invalidates the whole exception, exactly as
            # founderExceptionProblems() does in the JS gate.
            return ()
    return tuple(waives)


def _gate_index():'''


def main():
    if not SRC.exists():
        die("the Additional Home generator is not where this builder expects it.")
    src = SRC.read_text(encoding="utf-8")

    if REVERT:
        if not BAK.exists():
            die("there is no .bak sidecar to revert to.")
        shutil.copyfile(BAK, SRC)
        print("REVERTED generate_additional_home_universe.py from its .bak.")
        return

    already = SENTINEL in src
    if already:
        out = src
    else:
        for name, anchor in (("the condition chain", OLD),
                             ("the gate-index definition", OLD2)):
            n = src.count(anchor)
            if n != 1:
                die("%s was found %d times, not once. The generator has "
                    "moved. Nothing written." % (name, n))
        out = src.replace(OLD, NEW, 1).replace(OLD2, NEW2, 1)
        if out.replace(NEW2, OLD2, 1).replace(NEW, OLD, 1) != src:
            die("reversing the replacements did not reproduce the original "
                "file. Nothing written.")

    # G1 · THE PERMISSION CLASS IS UNWAIVABLE HERE TOO. Three mirrors, one
    # bright line; a mirror that allows what the others forbid is worse than
    # no mirror at all.
    blk = out[out.find("GATE_NEVER_WAIVABLE = ("):]
    blk = blk[:blk.find(")") + 1]
    for r in ("permission-declined", "no-permission",
              "permission-conditional-unresolved", "permission-state-missing"):
        if r not in blk:
            die("%r is missing from GATE_NEVER_WAIVABLE. Nothing written." % r)

    # G2 · AND IT IS CHECKED, not merely declared.
    if "if w in GATE_NEVER_WAIVABLE or w not in GATE_WAIVABLE:" not in out:
        die("_founder_waives does not reject a forbidden or unrecognised "
            "reason. Nothing written.")

    # G3 · A MALFORMED EXCEPTION WAIVES NOTHING. Five well-formedness tests,
    # each returning the empty tuple.
    fn = out[out.find("def _founder_waives"):]
    fn = fn[:fn.find("\ndef ", 1)]
    if fn.count("return ()") < 6:
        die("_founder_waives has fewer fail-closed returns than the JS "
            "validator has checks (%d). Nothing written." % fn.count("return ()"))

    # G4 · THE CONDITION VOCABULARY IS UNCHANGED. Eight reasons, same spelling
    # as the JS gate and as every hold_reason already recorded in the tree.
    for r in ("permission-state-missing", "listing-review-state-missing",
              "permission-declined", "no-permission",
              "permission-conditional-unresolved",
              "listing-review-awaiting-confirmation",
              "listing-review-changes-requested", "assets-not-approved"):
        if ('"%s"' % r) not in out:
            die("the hold reason %r has gone from the generator. Nothing "
                "written." % r)

    # G5 · THE GATE STILL NEVER READS A MEASUREMENT. The whole point of the
    # 11 October architecture: correcting an area must not publish anybody.
    gi = out[out.find("def _gate_index"):]
    gi = gi[:gi.find("\n_GATE = None")]
    for forbidden in ("area", "Value Number", "floor", "m²"):
        if forbidden in gi:
            die("the generator's gate index would read %r. The gate must "
                "never read a measurement. Nothing written." % forbidden)

    print("\nTHE GENERATOR'S GATE LEARNS THE EXCEPTION")
    print("=" * 74)
    if already:
        print("  ok    already in place; nothing to do")
    else:
        print("  ok    G0  both anchors matched once; nothing else moved")
    print("  ok    G1  the permission class is unwaivable in this mirror too")
    print("  ok    G2  a forbidden or unrecognised reason is rejected")
    print("  ok    G3  a malformed exception waives nothing (%d fail-closed "
          "returns)" % fn.count("return ()"))
    print("  ok    G4  all eight hold reasons keep their exact names")
    print("  ok    G5  the gate index still reads no measurement")

    if CHECK:
        print("-" * 74)
        print("CHECK ONLY. Nothing written.")
        if not already:
            print("\n".join(difflib.unified_diff(
                src.splitlines(), out.splitlines(),
                "generate_additional_home_universe.py",
                "generate_additional_home_universe.py (proposed)",
                lineterm="", n=1)))
        return
    if already:
        print("-" * 74)
        print("No change needed.")
        return

    if not BAK.exists():
        shutil.copyfile(SRC, BAK)
    SRC.write_text(out, encoding="utf-8")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (SRC.name, len(out.encode("utf-8"))))


if __name__ == "__main__":
    main()
