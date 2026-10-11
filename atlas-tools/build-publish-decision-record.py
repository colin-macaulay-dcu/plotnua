#!/usr/bin/env python3
"""
BOUNDED BUILDER — RECORD THE FOUNDER'S DECISION TO PUBLISH BIOBUILDS
====================================================================
Five anchored edits to atlas-tools/build-publication-gate-records.py, so the
ONE writer of the gate fields also carries the founder's exception.

WHY NOT A SECOND BUILDER. The obvious move was a new one-shot script beside
build-biobuilds-review-grant.py and build-ognyx-grant.py. It would have been
quicker and it would have been wrong: build-publication-gate-records.py is
idempotent and would be re-run, and on its next run it would recompute
public_visibility from inputs that knew nothing about the exception and quietly
put BIOBUILDS back on HOLD. Two writers of one field is two answers.

WHAT IS PRESERVED EXACTLY.

  * permission            GRANTED, 2 October 2026, ref C2-GRANT-BIOBUILDS-20261002
  * listing_review.state  AWAITING_CONFIRMATION -- UNCHANGED
  * confirmed_at          null -- UNCHANGED
  * the evidence quote    Mateus's words, verbatim, untouched
  * asset_approval_state  REFERENCE_ONLY -- UNCHANGED, because the 34 governed
                          assets genuinely are Reference Only in Atlas and no
                          decision changed that

Mateus has not confirmed the corrected preview. After this builder runs, the
record still says so, in the same words, and says separately that the founder
decided to proceed anyway. Anyone reading the file afterwards can tell exactly
what happened and who decided it.

    python3 atlas-tools/build-publish-decision-record.py [--check] [--revert]

Exit 0 = applied, or already correct.
"""
import difflib
import pathlib
import re
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "build-publication-gate-records.py"
BAK = SRC.with_suffix(".py.bak")

CHECK = "--check" in sys.argv
REVERT = "--revert" in sys.argv
SENTINEL = "FOUNDER_EXCEPTION"


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


# ── 1 · the decision itself, as data ──────────────────────────────────────
A1_OLD = '''

def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)
'''

A1_NEW = '''
# ── THE FOUNDER'S DECISION, AS DATA ───────────────────────────────────────
#
# BIOBUILDS granted permission on 2 October 2026 to feature its products and
# to use selected imagery with credit and a link back. In the same message it
# asked to see the listing first. That check has not come back.
#
# The founder has decided to publish without it and to own that decision.
# This is the record of that, and it is deliberately NOT a change to the
# review state: Mateus has not confirmed, the record still says he has not
# confirmed, and `supplier_confirmation_received: False` says it a second time
# in the place a future reader is most likely to look.
FOUNDER_EXCEPTION = {
    "authorised_by": "Colin MacAulay",
    "role": "Founder",
    "decision_date": "2026-10-11",
    "decision_ref": "FX-BIOBUILDS-PUBLISH-20261011",
    "supplier_confirmation_received": False,
    "waives": [
        "listing-review-awaiting-confirmation",
        "assets-not-approved",
    ],
    "basis": (
        "BIOBUILDS granted written permission on 2 October 2026 to feature "
        "its products and to use selected imagery with credit and a link "
        "back (C2-GRANT-BIOBUILDS-20261002). The supplier then asked for "
        "factual corrections on 11 October 2026; those corrections are "
        "implemented in Atlas and in the private preview. The founder has "
        "decided to publish the corrected listing without waiting for the "
        "supplier's confirmation of the revised preview, and accepts "
        "responsibility for proceeding before that confirmation is received."
    ),
    "scope": (
        "Authorises PUBLICATION OF THE PRODUCT LISTING in public Results, "
        "Compare and search. Does NOT authorise publication of BIOBUILDS "
        "imagery on any public page: the imagery grant remains scoped by "
        "this record's own conditions to the private noindexed review "
        "preview, the public Additional Home payload carries no image block, "
        "and prove-biobuilds-containment.mjs continues to enforce it."
    ),
    "withdrawal": (
        "BIOBUILDS may request change or removal at any time and PlotNua "
        "complies, exactly as the original grant provides. If the supplier "
        "objects to the published listing, remove this exception and the "
        "gate returns the product to HOLD with no other change."
    ),
}


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)
'''

# ── 2 · the Python mirror of the derivation ──────────────────────────────
A2_OLD = '''def derive(permission, review, asset_state):
    """Mirror of derivePublicVisibility() in atlas-tools/publication-gate.mjs.

    Two implementations of one rule is exactly the duplication that creates a
    second answer, so the two are pinned together by G4 below: the guard runs
    the JS derivation over the written file and refuses if it disagrees."""
    perm, rev = permission.get("state"), review.get("state")
    if perm == "DECLINED":
        return "HOLD", "permission-declined"
    if perm == "NONE":
        return "HOLD", "no-permission"
    if perm == "CONDITIONAL":
        return "HOLD", "permission-conditional-unresolved"
    if perm != "GRANTED":
        return "HOLD", "permission-state-missing"
    if rev == "AWAITING_CONFIRMATION":
        return "HOLD", "listing-review-awaiting-confirmation"
    if rev == "CHANGES_REQUESTED":
        return "HOLD", "listing-review-changes-requested"
    if rev not in ("NOT_REQUIRED", "CONFIRMED"):
        return "HOLD", "listing-review-state-missing"
    if asset_state and asset_state != "APPROVED":
        return "HOLD", "assets-not-approved"
    return "PUBLISHABLE", None'''

A2_NEW = '''# The four reasons no decision can waive. Kept in step with NEVER_WAIVABLE in
# atlas-tools/publication-gate.mjs, and G5 below refuses to run if the two
# lists ever diverge -- a mirror that drifts is worse than no mirror.
NEVER_WAIVABLE = (
    "permission-declined",
    "no-permission",
    "permission-conditional-unresolved",
    "permission-state-missing",
)


def derive(permission, review, asset_state, exception=None):
    """Mirror of derivePublicVisibility() in atlas-tools/publication-gate.mjs.

    Returns (visibility, hold_reason, waived).

    Two implementations of one rule is exactly the duplication that creates a
    second answer, so the two are pinned together by G4 below: the guard runs
    the JS derivation over the written file and refuses if it disagrees."""
    perm, rev = permission.get("state"), review.get("state")
    conditions = [
        (perm not in ("GRANTED", "CONDITIONAL", "DECLINED", "NONE"),
         "permission-state-missing"),
        (rev not in ("NOT_REQUIRED", "AWAITING_CONFIRMATION", "CONFIRMED",
                     "CHANGES_REQUESTED"), "listing-review-state-missing"),
        (perm == "DECLINED", "permission-declined"),
        (perm == "NONE", "no-permission"),
        (perm == "CONDITIONAL", "permission-conditional-unresolved"),
        (rev == "AWAITING_CONFIRMATION", "listing-review-awaiting-confirmation"),
        (rev == "CHANGES_REQUESTED", "listing-review-changes-requested"),
        (bool(asset_state) and asset_state != "APPROVED", "assets-not-approved"),
    ]
    accepted = list((exception or {}).get("waives") or ())
    waived = []
    for unsatisfied, reason in conditions:
        if not unsatisfied:
            continue
        if reason in accepted and reason not in NEVER_WAIVABLE:
            waived.append(reason)
            continue
        return "HOLD", reason, waived
    return "PUBLISHABLE", None, waived'''

# ── 3 · the call site and G1 ─────────────────────────────────────────────
A3_OLD = '''    asset_state = "REFERENCE_ONLY"
    visibility, hold_reason = derive(PERMISSION, LISTING_REVIEW, asset_state)

    # G1 · THE BUILDER REFUSES TO WRITE A PUBLISHABLE STATE.
    # This builder exists to record a hold. If the derivation ever came out
    # PUBLISHABLE here it would mean the inputs above had been edited, and
    # publishing a supplier must never be a side effect of running a recording
    # tool. Promotion is a separate, deliberate act.
    if visibility != "HOLD":
        die("the derivation produced %r, not HOLD. This builder records a "
            "hold and must never be the thing that publishes a supplier. "
            "Nothing written." % visibility)'''

A3_NEW = '''    asset_state = "REFERENCE_ONLY"
    visibility, hold_reason, waived = derive(
        PERMISSION, LISTING_REVIEW, asset_state, FOUNDER_EXCEPTION)

    # G1 · A PUBLISHABLE STATE MUST BE FULLY ACCOUNTED FOR.
    #
    # This guard used to refuse PUBLISHABLE outright, because until 11 October
    # 2026 this builder only ever recorded a hold and publishing a supplier
    # must never be a side effect of running a recording tool.
    #
    # It is now the writer of a founder-authorised publication, so an outright
    # refusal would be wrong. What it refuses instead is an UNEXPLAINED
    # publication: PUBLISHABLE is permitted only when every condition that
    # would otherwise have held the supplier was explicitly named in the
    # founder's decision. A supplier cannot become publishable here because an
    # input was quietly edited -- only because a decision says so, in writing,
    # naming what it accepts.
    if visibility == "PUBLISHABLE":
        if not waived:
            die("the derivation produced PUBLISHABLE with nothing waived, "
                "which means the recorded inputs no longer describe a held "
                "supplier. Publishing must not be a side effect of running "
                "this tool. Nothing written.")
        unexplained = [w for w in waived
                       if w not in (FOUNDER_EXCEPTION.get("waives") or ())]
        if unexplained:
            die("these conditions were waived without being named in the "
                "founder's decision: %s. Nothing written." % unexplained)
        for w in waived:
            if w in NEVER_WAIVABLE:
                die("the derivation waived %r, which no decision may waive. "
                    "Nothing written." % w)

    # G1b · AND THE DECISION MUST NOT CLAIM A CONFIRMATION.
    # The one thing the founder explicitly forbade: do not record Mateus as
    # having confirmed the corrected preview.
    if FOUNDER_EXCEPTION.get("supplier_confirmation_received") is not False:
        die("the founder exception does not state that the supplier's "
            "confirmation is OUTSTANDING. An exception records proceeding "
            "WITHOUT confirmation. Nothing written.")
    if LISTING_REVIEW.get("state") == "CONFIRMED" or LISTING_REVIEW.get("confirmed_at"):
        die("the listing review would record a confirmation the supplier has "
            "not given. Nothing written.")'''

# ── 4 · what gets written onto the row ───────────────────────────────────
A4_OLD = '''        before = json.dumps(row, sort_keys=True)
        row["permission"] = PERMISSION
        row["listing_review"] = LISTING_REVIEW
        row["asset_approval_state"] = asset_state
        row["public_visibility"] = visibility
        row["hold_reason"] = hold_reason
        after = json.dumps(row, sort_keys=True)'''

A4_NEW = '''        before = json.dumps(row, sort_keys=True)
        row["permission"] = PERMISSION
        row["listing_review"] = LISTING_REVIEW
        row["asset_approval_state"] = asset_state
        row["founder_exception"] = FOUNDER_EXCEPTION
        row["public_visibility"] = visibility
        row["hold_reason"] = hold_reason
        # The conditions that were unsatisfied and accepted. Written down so a
        # reader of this file never has to infer WHY a supplier with an
        # outstanding review is publishable, and so no surface can mistake a
        # waived condition for a satisfied one.
        row["waived_conditions"] = waived
        after = json.dumps(row, sort_keys=True)'''

# ── 5 · the cross-check and the closing report ───────────────────────────
A5_OLD = '''        js = json.loads(out.stdout.strip())
        if js.get("visibility") != visibility or js.get("holdReason") != hold_reason:
            die("the Python and JS derivations DISAGREE (%s/%s vs %s/%s). "
                "One rule, not two." % (visibility, hold_reason,
                                        js.get("visibility"), js.get("holdReason")))
        print("  ok    G4  the JS derivation agrees: %s / %s"
              % (js.get("visibility"), js.get("holdReason")))
    except (OSError, ValueError) as e:
        die("cross-check could not run: %s" % e)

    print("-" * 74)
    print("Recorded on %d file(s): %s" % (len(changed), ", ".join(changed) or "none"))
    print("No Airtable write. No public visibility change. BIOBUILDS stays "
          "on HOLD.")'''

A5_NEW = '''        js = json.loads(out.stdout.strip())
        if js.get("visibility") != visibility or js.get("holdReason") != hold_reason:
            die("the Python and JS derivations DISAGREE (%s/%s vs %s/%s). "
                "One rule, not two." % (visibility, hold_reason,
                                        js.get("visibility"), js.get("holdReason")))
        if sorted(js.get("waived") or []) != sorted(waived):
            die("the two derivations disagree about what was WAIVED (%s vs "
                "%s). One rule, not two." % (waived, js.get("waived")))
        print("  ok    G4  the JS derivation agrees: %s / %s / waived %s"
              % (js.get("visibility"), js.get("holdReason"),
                 js.get("waived")))

        # G5 · THE TWO FORBIDDEN LISTS MUST NOT DRIFT. The Python mirror above
        # carries its own copy of NEVER_WAIVABLE; if the JS one ever gained a
        # reason this did not, a decision could waive it here and be refused
        # there, or worse, the other way round.
        probe2 = ("import {NEVER_WAIVABLE} from '%s';"
                  "console.log(JSON.stringify(NEVER_WAIVABLE));"
                  % (HERE / "publication-gate.mjs").as_uri())
        out2 = subprocess.run(["node", "--input-type=module", "-e", probe2],
                              capture_output=True, text=True, timeout=60)
        if out2.returncode != 0:
            die("NEVER_WAIVABLE could not be read from the JS gate: %s"
                % (out2.stderr or "").strip()[:200])
        if sorted(json.loads(out2.stdout.strip())) != sorted(NEVER_WAIVABLE):
            die("the Python and JS NEVER_WAIVABLE lists have drifted apart. "
                "Nothing written.")
        print("  ok    G5  both NEVER_WAIVABLE lists agree (%d reasons)"
              % len(NEVER_WAIVABLE))
    except (OSError, ValueError) as e:
        die("cross-check could not run: %s" % e)

    print("-" * 74)
    print("Recorded on %d file(s): %s" % (len(changed), ", ".join(changed) or "none"))
    print("No Airtable write.")
    print("BIOBUILDS is PUBLISHABLE on a founder-authorised exception "
          "(%s, %s)." % (FOUNDER_EXCEPTION["decision_ref"],
                         FOUNDER_EXCEPTION["decision_date"]))
    print("The supplier's confirmation of the corrected preview remains "
          "OUTSTANDING and the record says so.")
    print("Imagery stays scoped to the private review preview.")'''


EDITS = [("the module preamble", A1_OLD, A1_NEW),
         ("the Python derivation mirror", A2_OLD, A2_NEW),
         ("the call site and G1", A3_OLD, A3_NEW),
         ("the row write", A4_OLD, A4_NEW),
         ("the cross-check and report", A5_OLD, A5_NEW)]


def main():
    if not SRC.exists():
        die("build-publication-gate-records.py is not where this builder "
            "expects it.")
    src = SRC.read_text(encoding="utf-8")

    if REVERT:
        if not BAK.exists():
            die("there is no .bak sidecar to revert to.")
        shutil.copyfile(BAK, SRC)
        print("REVERTED build-publication-gate-records.py from its .bak.")
        return

    already = SENTINEL in src
    if already:
        out = src
    else:
        for name, old, _ in EDITS:
            n = src.count(old)
            if n != 1:
                die("%s was found %d times, not once. The gate-records "
                    "builder has moved. Nothing written." % (name, n))
        out = src
        for _, old, new in EDITS:
            out = out.replace(old, new, 1)
        back = out
        for _, old, new in reversed(EDITS):
            back = back.replace(new, old, 1)
        if back != src:
            die("reversing the five replacements did not reproduce the "
                "original file. Nothing written.")

    # G1 · THE REVIEW STATE IS NOT TOUCHED. The founder's rule 3, asserted on
    # the builder's own source: AWAITING_CONFIRMATION stays, confirmed_at
    # stays null, and no literal "CONFIRMED" is written into LISTING_REVIEW.
    lr = out[out.find("LISTING_REVIEW = {"):]
    lr = lr[:lr.find("\n}") + 2]
    if '"state": "AWAITING_CONFIRMATION"' not in lr:
        die("LISTING_REVIEW no longer records AWAITING_CONFIRMATION. "
            "Nothing written.")
    if '"confirmed_at": None' not in lr:
        die("LISTING_REVIEW no longer records confirmed_at as None. "
            "Nothing written.")

    # G2 · THE SUPPLIER'S WORDS SURVIVE. The evidence quote is the thing a
    # future reader needs most and the thing an edit is most likely to lose.
    # The note is wrapped across source lines, so it is unwrapped before the
    # comparison: the assertion is about the sentence, not about where the
    # line breaks happen to fall.
    flat = re.sub(r'"\s*\n\s*"', "", out)
    if ("condition being exercised, not a permission withheld" not in flat):
        die("the listing-review note that distinguishes a condition being "
            "exercised from a permission withheld has gone. Nothing written.")

    # G3 · THE DECISION NAMES A PERSON AND A DATE. An unattributed exception
    # is not a decision, it is a shrug.
    fx = out[out.find("FOUNDER_EXCEPTION = {"):]
    fx = fx[:fx.find("\n}") + 2]
    for need in ('"authorised_by"', '"decision_date"', '"decision_ref"',
                 '"supplier_confirmation_received": False', '"basis"',
                 '"scope"', '"withdrawal"'):
        if need not in fx:
            die("the founder exception is missing %s. Nothing written." % need)

    # G4 · IT WAIVES ONLY WHAT IT NAMES, and names nothing from the
    # permission class.
    for forbidden in ("permission-declined", "no-permission",
                      "permission-conditional-unresolved",
                      "permission-state-missing"):
        if ('"%s"' % forbidden) in fx:
            die("the founder exception names %r, which no decision may "
                "waive. Nothing written." % forbidden)

    # G5 · IMAGERY IS EXCLUDED IN WRITING. The grant has two halves and this
    # decision exercises one of them.
    if "Does NOT authorise publication of BIOBUILDS" not in fx:
        die("the exception does not exclude imagery from its scope. "
            "Nothing written.")

    # G6 · AND THE WITHDRAWAL ROUTE SURVIVES. A supplier who objects must be
    # one edit from being unpublished again.
    if "remove this exception and the" not in fx:
        die("the exception does not record how to undo it. Nothing written.")

    print("\nFOUNDER PUBLISH DECISION · BIOBUILDS")
    print("=" * 74)
    if already:
        print("  ok    the decision is already recorded; nothing to do")
    else:
        print("  ok    G0  all five anchors matched once; nothing else moved")
    print("  ok    G1  listing_review stays AWAITING_CONFIRMATION, "
          "confirmed_at null")
    print("  ok    G2  the supplier's own correspondence note survives")
    print("  ok    G3  the decision names a person, a date and a reference")
    print("  ok    G4  it waives nothing from the permission class")
    print("  ok    G5  imagery is excluded from its scope in writing")
    print("  ok    G6  the withdrawal route is recorded")

    if CHECK:
        print("-" * 74)
        print("CHECK ONLY. Nothing written.")
        if not already:
            print("\n".join(difflib.unified_diff(
                src.splitlines(), out.splitlines(),
                "build-publication-gate-records.py",
                "build-publication-gate-records.py (proposed)",
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
    print("Now run it:  python3 atlas-tools/build-publication-gate-records.py")


if __name__ == "__main__":
    main()
