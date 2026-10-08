#!/usr/bin/env python3
"""
PRE-G5 · WORKER TENURE ALIGNMENT — G1B §5 IS AUTHORITATIVE
===============================================================================
Founder decision D-G5-1 = OPTION 1, 8 October 2026. The FROZEN G1B contract is
authoritative and the implementation was stricter than it. One logic change:

    OLD   if (tenure !== 'own')   { tick + >=20-char note required }
    NEW   if (tenure === 'rent')  { tick + >=20-char note required }

so that `buying` is storable with neither, as G1B §5 already specifies.

WHAT THIS DOES NOT TOUCH. `own` behaviour. `rent` behaviour — both inner
refusals survive byte-for-byte, in order. The absent-tenure refusal at
`if (!tenure) return REFUSED(cors, 'inherited_tenure');` — founder instruction
is explicit that the unreachable contract/code divergence is PRESERVED and not
solved here, so guard 9 asserts it is still present afterwards. No vocabulary,
no CORS rule, no Fetch Metadata check, no write path, no reply shape, no var in
wrangler.toml, and no switch.

NON-PROMOTION. `buying` remains non-promotable. Nothing in this Worker promotes
or introduces anybody — there is no such code path — so non-promotion needs no
code today. Guard 10 asserts that remains true: `status` is only ever
SUBMIT_STATUS, and no introduction/eligibility/promotion logic appears.

GUARD DISCIPLINE. Every textual assertion runs against comment-stripped source,
because this builder REWRITES the comment above the change and several guards
reason about words that also appear in that comment. Asserting mention rather
than assertion is the recorded failure mode this strips out.

    python3 build-worker-tenure-alignment.py --check   # guards only, writes nothing
    python3 build-worker-tenure-alignment.py           # apply
"""

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "worker" / "garden-register" / "src" / "index.js"

BASE_SHA = "4c5a47831ec85178f083f4535f1bbb732ee9c4542af43f28ef8b88105897a3ba"

# ---------------------------------------------------------------- the one site
OLD = """  /* G1B TENURE RULE. A non-owner needs the tick AND their own statement.
     PlotNua never asks for a deed, a lease, or a landlord's details: the
     homeowner's own sentence is the evidence, and it is evidence of what they
     said, not of the fact. Storage is still permitted — this refusal exists
     only because a submission with neither has nothing to review. */
  const permission_confirmed = body.permission_confirmed === true;
  if (tenure !== 'own') {
    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');
    if (!note || note.length < 20) return REFUSED(cors, 'garden_note');
  }"""

NEW = """  /* G1B §5 TENURE RULE, as frozen. `rent` may reach an introduction ONLY with
     explicit permission, so `rent` alone requires the tick AND the homeowner's
     own statement. `buying` is storable with neither, is never promoted, and
     `own` needs ordinary confirmation only.
     PlotNua never asks for a deed, a lease, or a landlord's details: the
     homeowner's own sentence is evidence of what they said, not of the fact.
     Non-promotion is enforced at G7, which is
     BLOCKED — it is not, and must not become, a form control.
     Aligned 8 October 2026 under founder decision D-G5-1 = option 1: this
     block previously read `tenure !== 'own'`, which refused a `buying`
     homeowner the frozen contract says is storable. */
  const permission_confirmed = body.permission_confirmed === true;
  if (tenure === 'rent') {
    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');
    if (!note || note.length < 20) return REFUSED(cors, 'garden_note');
  }"""

# The absent-tenure refusal that must SURVIVE untouched (founder instruction).
PRESERVED = "  if (!tenure) return REFUSED(cors, 'inherited_tenure');"


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def strip_comments(js):
    """Remove /* ... */ and // ... so guards test executable text only."""
    js = re.sub(r"/\*.*?\*/", " ", js, flags=re.S)
    js = re.sub(r"(?m)//.*$", " ", js)
    return js


def main():
    check = "--check" in sys.argv
    src = TARGET.read_text(encoding="utf-8")
    before = hashlib.sha256(src.encode("utf-8")).hexdigest()

    print("  TARGET  %s" % TARGET.relative_to(ROOT))
    print("  BEFORE  %d bytes  sha256 %s" % (len(src.encode("utf-8")), before))
    print()

    # ---- guard 1 · base identity
    if before != BASE_SHA:
        die("the target is not the frozen deployed Worker %s... — refusing to "
            "patch an unexpected file" % BASE_SHA[:16])
    print("  G1  base is the frozen deployed Worker                      OK")

    # ---- guard 3 · not re-runnable over its own output
    if "if (tenure === 'rent') {" in src:
        die("the aligned condition is already present; this builder is not "
            "re-runnable over its own output")
    print("  G3  not re-runnable over its own output                     OK")

    # ---- guard 2 · the anchor occurs exactly once
    n = src.count(OLD)
    print("  G2  anchor occurrences = %d (must be 1)                     %s"
          % (n, "OK" if n == 1 else "*** FAIL"))
    if n != 1:
        die("the tenure block occurs %d times, expected exactly 1" % n)

    # ---- guard 9 · the preserved divergence is present BEFORE
    if src.count(PRESERVED) != 1:
        die("the absent-tenure refusal is not present exactly once before the "
            "patch — refusing to proceed")
    print("  G9a preserved absent-tenure refusal present before          OK")

    out = src.replace(OLD, NEW, 1)

    # ---- guard 9b · and AFTER, unaltered
    if out.count(PRESERVED) != 1:
        die("the absent-tenure refusal did not survive the patch")
    print("  G9b preserved absent-tenure refusal survives                OK")

    exe_before, exe_after = strip_comments(src), strip_comments(out)

    # ---- guard 10 · the rent branch body is unchanged, in order
    rent_body = ["if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');",
                 "if (!note || note.length < 20) return REFUSED(cors, 'garden_note');"]
    pos = -1
    for frag in rent_body:
        if exe_after.count(frag) != 1:
            die("rent refusal %r is not present exactly once after the patch" % frag[:40])
        at = exe_after.index(frag)
        if at <= pos:
            die("the rent refusals are out of order after the patch")
        pos = at
    print("  G10 rent branch body unchanged and in order                 OK")

    # ---- guard 12 · no promotion / introduction / eligibility logic appears
    for word in ("introduc", "promot", "eligib", "matchable"):
        if re.search(word, exe_after, re.I):
            die("executable code now mentions %r — promotion is a G7 decision "
                "and must not be built here" % word)
    print("  G12 no promotion/introduction logic in executable code      OK")

    # ---- guard 13 · the RECORD's status is only ever SUBMIT_STATUS.
    # The lookbehind keeps `from_status` / `to_status` out: those are status-LOG
    # columns and `from_status: ''` is the correct "from nothing" value.
    statuses = set(re.findall(r"(?<![\w_])status:\s*([A-Za-z_'\"][\w'\"]*)", exe_after))
    if statuses - {"SUBMIT_STATUS"}:
        die("the record status is assigned something other than SUBMIT_STATUS: %s"
            % sorted(statuses))
    print("  G13 record status is only ever SUBMIT_STATUS                OK")

    # ---- guard 14 · no new string literal appears and none disappears.
    # The SET, not the multiset: the change moves one occurrence from 'own' to
    # 'rent' and both literals already exist elsewhere in the file, so counts
    # legitimately shift by one. A literal appearing or vanishing would not be
    # this correction.
    lits = lambda t: set(re.findall(r"'[^'\n]*'|\"[^\"\n]*\"", t))
    a, b = lits(exe_before), lits(exe_after)
    if a != b:
        die("the set of executable string literals changed: added %s removed %s"
            % (sorted(b - a), sorted(a - b)))
    print("  G14 executable string literal SET unchanged (no new copy)   OK")
    for lit, delta in (("'own'", -1), ("'rent'", +1)):
        d = exe_after.count(lit) - exe_before.count(lit)
        if d != delta:
            die("occurrences of %s moved by %+d, expected %+d" % (lit, d, delta))
    print("  G14b exactly one occurrence moved 'own' -> 'rent'           OK")

    # ---- guard 16 · THE LANDLORD DENIAL SURVIVES, AS A DENIAL, ON ONE LINE.
    # prove-guards.mjs G36b matches /never asks for a deed, a lease, or a
    # landlord/ against the raw source. The first run of this builder rewrote
    # the comment, dropped the comma after "lease" AND wrapped the phrase across
    # two lines, and G36b caught it. That guard was right and the builder was
    # wrong, so the builder now asserts it too rather than relying on a suite
    # downstream. The phrase must not wrap: a line break inside it defeats the
    # regex exactly as a missing comma does.
    DENIAL = "never asks for a deed, a lease, or a landlord"
    if out.count(DENIAL) != 1:
        die("the landlord denial must appear exactly once, unbroken on one "
            "line, as prove-guards.mjs G36b requires (found %d)"
            % out.count(DENIAL))
    print("  G16 landlord denial survives, one line, as a denial         OK")

    # ---- guard 15 · secret sweep. Every AIRTABLE_TOKEN occurrence must be
    # either inside a comment (documenting that it is a Cloudflare secret) or
    # an `env.` read. Anything else is a binding, a copy or a literal.
    # Comment spans are computed over the WHOLE file, not a fixed look-back
    # window. A 200-character window was the first version and it fired on the
    # file's own 30-line header comment, which also made the capability case
    # pass for the wrong reason.
    spans = [m.span() for m in re.finditer(r"/\*.*?\*/", out, flags=re.S)]
    spans += [m.span() for m in re.finditer(r"(?m)//.*$", out)]
    for m in re.finditer(r"AIRTABLE_TOKEN", out):
        in_comment = any(a <= m.start() < b for a, b in spans)
        env_read = out[max(0, m.start() - 4):m.start()] == "env."
        if not (in_comment or env_read):
            die("AIRTABLE_TOKEN at offset %d is neither inside a comment nor an "
                "env read" % m.start())
    print("  G15 secret sweep: token only in comments / env reads        OK")

    # ---- guard 11 · THE CATCH-ALL, deliberately LAST. The specific guards
    # above (G12-G15) name what went wrong; this one catches anything they
    # did not think of. Ordered last so a specific diagnosis wins over a
    # generic one, and so each specific guard is independently fireable
    # instead of being masked by this.
    if exe_before.replace("tenure !== 'own'", "@@T@@") != \
       exe_after.replace("tenure === 'rent'", "@@T@@"):
        die("executable code changed somewhere other than the tenure condition")
    print("  G11 executable text differs ONLY in that condition          OK")


    if check:
        print("\n  --check: every guard passed. Nothing written.")
        return

    TARGET.write_text(out, encoding="utf-8")
    after = hashlib.sha256(out.encode("utf-8")).hexdigest()
    print()
    print("  AFTER   %d bytes  sha256 %s" % (len(out.encode("utf-8")), after))
    print("  DELTA   %+d bytes" % (len(out.encode("utf-8")) - len(src.encode("utf-8"))))
    print()
    print("  ONE LOGIC CHANGE:  if (tenure !== 'own')  ->  if (tenure === 'rent')")


if __name__ == "__main__":
    main()
