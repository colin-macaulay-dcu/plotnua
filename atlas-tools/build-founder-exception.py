#!/usr/bin/env python3
"""
BOUNDED BUILDER — THE FOUNDER-AUTHORISED PUBLICATION EXCEPTION
==============================================================
One anchored rewrite of derivePublicVisibility() in
atlas-tools/publication-gate.mjs, so a NAMED supplier can be published on a
NAMED founder decision without the general gate being weakened for anybody
else.

THE PROBLEM THIS SOLVES, PRECISELY.

BIOBUILDS granted written permission on 2 October 2026 to feature its products
and to use selected imagery with credit and a link back. In the same message
it asked to see the listing first. The founder has decided to publish before
that check comes back, and accepts responsibility for doing so.

There were only three ways to make the gate let that through:

  1. Set listing_review.state to CONFIRMED. REFUSED. Mateus has not
     confirmed, and writing that he did would be falsifying a supplier's
     words in PlotNua's own records. It would also survive this decision and
     mislead everyone who read the file afterwards.
  2. Relax the AWAITING_CONFIRMATION condition for everyone. REFUSED. That is
     the global weakening the founder forbade, and it would silently publish
     the next supplier who asks for a pre-live check.
  3. Record the decision as what it is: a documented, dated, named exception
     to a specific condition for a specific supplier. THIS.

So the condition is NOT removed and the review state is NOT altered. The
derivation still finds listing-review-awaiting-confirmation. It then finds an
exception that explicitly names that reason, and publishes anyway, carrying
the waiver in its own output so no surface can report the hold as satisfied
when it was waived.

WHAT CANNOT BE WAIVED, EVER.

A permission that was never given, was declined, or was withdrawn. Those four
hold reasons are in NEVER_WAIVABLE and no exception can touch them, because
the whole point of the gate is that PlotNua does not publish a supplier's
material without the supplier's permission. A founder decision can accept the
risk of publishing early against a grant PlotNua HOLDS. It cannot manufacture
a grant that does not exist. That line is what keeps this mechanism from
becoming a master key, and PG16 asserts it.

WHAT THIS DOES NOT AUTHORISE.

Imagery. The BIOBUILDS imagery grant is scoped by PlotNua's own rights record
to the private noindexed preview, and measured today the public Additional
Home payload carries no image block at all -- pnAdditionalHomeView() has no
imagery field and the generator emits none. So publication exercises the
'feature' half of the grant and not the 'imagery' half, the containment proof
continues to enforce that, and PG19 asserts the linkage rather than leaving it
to a sentence in a note.

    python3 atlas-tools/build-founder-exception.py [--check] [--revert]

Exit 0 = applied, or already correct.
"""
import difflib
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "publication-gate.mjs"
BAK = SRC.with_suffix(".mjs.bak")

CHECK = "--check" in sys.argv
REVERT = "--revert" in sys.argv
SENTINEL = "NEVER_WAIVABLE"


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


OLD = """/**
 * Derive public visibility. Returns { visibility, holdReason }.
 * holdReason is null when PUBLISHABLE, and otherwise names the FIRST
 * unsatisfied condition in a fixed order, so the reason is stable and
 * testable rather than dependent on evaluation order.
 */
export function derivePublicVisibility(record) {
  const permission = (record && record.permission) || {};
  const review = (record && record.listing_review) || {};
  const perm = permission.state;
  const rev = review.state;
  const assets = record && record.asset_approval_state;

  if (!PERMISSION_STATES.includes(perm)) {
    return { visibility: "HOLD", holdReason: "permission-state-missing" };
  }
  if (!REVIEW_STATES.includes(rev)) {
    return { visibility: "HOLD", holdReason: "listing-review-state-missing" };
  }

  if (perm === "DECLINED") {
    return { visibility: "HOLD", holdReason: "permission-declined" };
  }
  if (perm === "NONE") {
    return { visibility: "HOLD", holdReason: "no-permission" };
  }
  if (perm === "CONDITIONAL") {
    return { visibility: "HOLD", holdReason: "permission-conditional-unresolved" };
  }

  // perm === GRANTED from here.
  if (rev === "AWAITING_CONFIRMATION") {
    return { visibility: "HOLD",
             holdReason: "listing-review-awaiting-confirmation" };
  }
  if (rev === "CHANGES_REQUESTED") {
    return { visibility: "HOLD", holdReason: "listing-review-changes-requested" };
  }

  // The pre-existing Atlas gate, kept as a condition rather than replaced.
  if (assets && assets !== "APPROVED") {
    return { visibility: "HOLD", holdReason: "assets-not-approved" };
  }

  return { visibility: "PUBLISHABLE", holdReason: null };
}"""

NEW = '''/* ── THE FOUNDER-AUTHORISED EXCEPTION ──────────────────────────────────────
   A founder may decide to publish a supplier before one of the gate's
   conditions is satisfied, and own that decision. What a founder may NOT do
   is make the record say the condition was met.

   So an exception does not edit a condition, remove it, or relax it for
   anyone else. It sits on ONE supplier's record, names the EXACT hold reasons
   it accepts the risk of, and travels in the derivation's output so no
   surface can later report a waived hold as a satisfied one.

   THE LINE THAT CANNOT MOVE. A permission that was never given, was declined,
   or was withdrawn cannot be waived by anybody. The gate exists so PlotNua
   does not publish a supplier's material without the supplier's permission; a
   founder can accept the risk of publishing early against a grant PlotNua
   HOLDS, and cannot conjure a grant that was never made. Without this list
   the mechanism would be a master key. */
export const NEVER_WAIVABLE = [
  "permission-declined",
  "no-permission",
  "permission-conditional-unresolved",
  "permission-state-missing"
];

/* Everything else is waivable ON AN EXPLICIT, NAMED DECISION -- enumerated
   rather than derived as "whatever is not forbidden", so adding a new hold
   reason does not silently make it waivable. */
export const WAIVABLE_HOLD_REASONS = [
  "listing-review-awaiting-confirmation",
  "listing-review-changes-requested",
  "listing-review-state-missing",
  "assets-not-approved"
];

/**
 * Is this record's founder_exception usable? Returns an array of problems;
 * empty means usable. A malformed exception waives NOTHING -- it does not
 * half-work, and it does not fail open.
 */
export function founderExceptionProblems(record) {
  const ex = record && record.founder_exception;
  if (!ex) return ["no founder_exception on this record"];
  const out = [];
  if (!ex.authorised_by || typeof ex.authorised_by !== "string") {
    out.push("authorised_by must name the person who decided");
  }
  if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(String(ex.decision_date || ""))) {
    out.push("decision_date must be an ISO date");
  }
  if (!Array.isArray(ex.waives) || !ex.waives.length) {
    out.push("waives must list the exact hold reasons being accepted");
  } else {
    for (const r of ex.waives) {
      if (NEVER_WAIVABLE.includes(r)) {
        out.push(`${r} can never be waived by anyone`);
      } else if (!WAIVABLE_HOLD_REASONS.includes(r)) {
        out.push(`${r} is not a recognised waivable hold reason`);
      }
    }
  }
  /* The decision's whole character is that the supplier has NOT come back.
     Recording that explicitly, as a boolean on the exception itself, is what
     stops the file drifting into implying confirmation. It must be present
     and it must be false -- an exception is not the place to record a
     confirmation that arrived. */
  if (ex.supplier_confirmation_received !== false) {
    out.push("supplier_confirmation_received must be present and false: an "
             + "exception records proceeding WITHOUT confirmation");
  }
  if (!ex.basis || String(ex.basis).trim().length < 20) {
    out.push("basis must say why the decision was taken");
  }
  return out;
}

/**
 * Derive public visibility. Returns { visibility, holdReason, waived }.
 *
 * holdReason names the FIRST unsatisfied condition in a fixed order, so the
 * reason is stable and testable rather than dependent on evaluation order.
 * `waived` lists any conditions that were unsatisfied and explicitly accepted
 * by a well-formed founder exception; it is an empty array otherwise.
 *
 * The conditions below are the SAME conditions, in the SAME order, with the
 * SAME vocabulary as before the exception mechanism existed. A record with no
 * founder_exception derives exactly what it derived before, which
 * prove-founder-exception.mjs asserts over every real record and a synthetic
 * matrix rather than leaving it to inspection.
 */
export function derivePublicVisibility(record) {
  const permission = (record && record.permission) || {};
  const review = (record && record.listing_review) || {};
  const perm = permission.state;
  const rev = review.state;
  const assets = record && record.asset_approval_state;

  /* Every condition, in order. The first unsatisfied one decides, exactly as
     the chain of early returns did. */
  const conditions = [
    [!PERMISSION_STATES.includes(perm), "permission-state-missing"],
    [!REVIEW_STATES.includes(rev), "listing-review-state-missing"],
    [perm === "DECLINED", "permission-declined"],
    [perm === "NONE", "no-permission"],
    [perm === "CONDITIONAL", "permission-conditional-unresolved"],
    // perm === GRANTED from here.
    [rev === "AWAITING_CONFIRMATION", "listing-review-awaiting-confirmation"],
    [rev === "CHANGES_REQUESTED", "listing-review-changes-requested"],
    // The pre-existing Atlas gate, kept as a condition rather than replaced.
    [!!assets && assets !== "APPROVED", "assets-not-approved"]
  ];

  /* An exception is consulted ONLY if it is well-formed, and waives ONLY the
     reasons it names. A malformed one waives nothing. */
  const ex = record && record.founder_exception;
  const exUsable = ex && founderExceptionProblems(record).length === 0;
  const accepted = exUsable ? ex.waives.slice() : [];

  const waived = [];
  for (const [unsatisfied, reason] of conditions) {
    if (!unsatisfied) continue;
    if (accepted.includes(reason) && !NEVER_WAIVABLE.includes(reason)) {
      waived.push(reason);
      continue;
    }
    return { visibility: "HOLD", holdReason: reason, waived: waived };
  }

  return { visibility: "PUBLISHABLE", holdReason: null, waived: waived };
}'''

# The integrity checks need one addition: an exception must never coexist with
# a fabricated confirmation.
OLD2 = """  // PG5 · never call a granted supplier unpermitted.
  if (permission.state === "GRANTED" && derived.holdReason === "no-permission") {
    out.push("holdReason says no-permission for a supplier whose permission " +
             "state is GRANTED");
  }

  return out;
}"""

NEW2 = """  // PG5 · never call a granted supplier unpermitted.
  if (permission.state === "GRANTED" && derived.holdReason === "no-permission") {
    out.push("holdReason says no-permission for a supplier whose permission " +
             "state is GRANTED");
  }

  /* PG14 · AN EXCEPTION IS NOT A CONFIRMATION, AND MUST NEVER BECOME ONE.
     The failure mode this exists for: somebody tidies the record later,
     notices the supplier is published, and "completes" the review state to
     match. That would turn a founder's accepted risk into a supplier's
     endorsement, in writing, on PlotNua's own file. */
  const ex = record && record.founder_exception;
  if (ex) {
    const problems = founderExceptionProblems(record);
    if (problems.length) {
      out.push("founder_exception is malformed and therefore waives nothing: "
               + problems.join("; "));
    }
    if (ex.supplier_confirmation_received === false &&
        review.state === "CONFIRMED") {
      out.push("the record says the supplier has NOT confirmed and also sets "
               + "listing_review.state to CONFIRMED");
    }
    if (ex.supplier_confirmation_received === false && review.confirmed_at) {
      out.push("the record says the supplier has NOT confirmed and also "
               + "carries a confirmed_at timestamp");
    }
    /* An exception that waives nothing real is a note pretending to be a
       decision; it should be removed rather than left to rot. */
    if (!problems.length && !derived.waived.length) {
      out.push("founder_exception waives " + JSON.stringify(ex.waives) +
               " but no such condition is unsatisfied; the exception is "
               + "inert and should be removed");
    }
  }

  return out;
}"""


def main():
    if not SRC.exists():
        die("publication-gate.mjs is not where this builder expects it.")
    src = SRC.read_text(encoding="utf-8")

    if REVERT:
        if not BAK.exists():
            die("there is no .bak sidecar to revert to.")
        shutil.copyfile(BAK, SRC)
        print("REVERTED publication-gate.mjs from its .bak sidecar.")
        return

    already = SENTINEL in src
    if already:
        out = src
    else:
        for name, anchor in (("the derivation", OLD),
                             ("the integrity checks", OLD2)):
            n = src.count(anchor)
            if n != 1:
                die("%s was found %d times, not once. publication-gate.mjs "
                    "has moved. Nothing written." % (name, n))
        out = src.replace(OLD, NEW, 1).replace(OLD2, NEW2, 1)

        # G1 · NOTHING OUTSIDE THE TWO BLOCKS MOVED.
        if out.replace(NEW2, OLD2, 1).replace(NEW, OLD, 1) != src:
            die("reversing the replacements did not reproduce the original "
                "file. Nothing written.")

    # G2 · THE PERMISSION CLASS IS UNWAIVABLE, AND ENUMERATED.
    for r in ("permission-declined", "no-permission",
              "permission-conditional-unresolved", "permission-state-missing"):
        block = out[out.find("export const NEVER_WAIVABLE"):]
        block = block[:block.find("];") + 2]
        if r not in block:
            die("%r is not in NEVER_WAIVABLE. A founder decision must never "
                "be able to manufacture a permission. Nothing written." % r)

    # G3 · DEFENCE IN DEPTH. The loop checks the forbidden list at the point
    # of waiving as well as at validation time.
    #
    # HONEST ABOUT WHAT THIS BUYS: the second check is UNREACHABLE while the
    # validator works, and the capability proof demonstrated exactly that --
    # removing it changed no behaviour. It is not redundant belt-and-braces
    # against a reachable state; it is insurance against a future edit to the
    # validator, and FX17 asserts it structurally and labels itself (source)
    # for that reason. Keeping it is cheap; claiming it currently stops
    # anything would be false.
    if "accepted.includes(reason) && !NEVER_WAIVABLE.includes(reason)" not in out:
        die("the waiver loop does not re-check NEVER_WAIVABLE at the point of "
            "waiving. One check is not enough for this. Nothing written.")

    # G4 · A MALFORMED EXCEPTION WAIVES NOTHING. Fail closed, not half-open.
    if "founderExceptionProblems(record).length === 0" not in out:
        die("the derivation does not require a well-formed exception before "
            "honouring it. Nothing written.")

    # G5 · THE WAIVER IS REPORTED, NOT SWALLOWED. A surface that cannot tell a
    # waived hold from a satisfied condition will eventually claim the
    # supplier confirmed.
    if "waived: waived" not in out or "holdReason: null, waived" not in out:
        die("the derivation does not carry the waived list in its output. "
            "Nothing written.")

    # G6 · NO FABRICATED CONFIRMATION, asserted in the integrity checks.
    if ("listing_review.state to CONFIRMED" not in out
            or "carries a confirmed_at timestamp" not in out):
        die("the integrity checks do not refuse a record that claims both "
            "'not confirmed' and a confirmation. Nothing written.")

    # G7 · THE CONDITION VOCABULARY IS UNCHANGED. Eight conditions, the same
    # eight reason strings as before. A renamed reason would silently break
    # every guard and every recorded hold_reason in the tree.
    for r in ("permission-state-missing", "listing-review-state-missing",
              "permission-declined", "no-permission",
              "permission-conditional-unresolved",
              "listing-review-awaiting-confirmation",
              "listing-review-changes-requested", "assets-not-approved"):
        if ('"%s"' % r) not in out:
            die("the hold reason %r has gone from the derivation. The "
                "vocabulary must not change. Nothing written." % r)

    print("\nFOUNDER-AUTHORISED PUBLICATION EXCEPTION")
    print("=" * 74)
    if already:
        print("  ok    the mechanism is already in place; nothing to do")
    else:
        print("  ok    G1  both anchors matched once; nothing else moved")
    print("  ok    G2  the four permission reasons can never be waived")
    print("  ok    G3  the forbidden list is re-checked at the waiver itself")
    print("  ok    G4  a malformed exception waives nothing")
    print("  ok    G5  the waiver is carried in the derivation's output")
    print("  ok    G6  a fabricated confirmation is refused")
    print("  ok    G7  all eight hold reasons keep their exact names")

    if CHECK:
        print("-" * 74)
        print("CHECK ONLY. Nothing written.")
        if not already:
            print("\n".join(difflib.unified_diff(
                src.splitlines(), out.splitlines(), "publication-gate.mjs",
                "publication-gate.mjs (proposed)", lineterm="", n=1)))
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
