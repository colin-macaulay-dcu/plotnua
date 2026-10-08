#!/usr/bin/env python3
"""
PRE-G5 · PAGE TENURE ALIGNMENT — G1B §5 IS AUTHORITATIVE
===============================================================================
Founder decision D-G5-1 = OPTION 1, 8 October 2026, executing step 5 of the
approved PRE-G5 CORRECTION PLAN. The frozen G1B contract is authoritative and
the shipped page was stricter than it. THREE logic changes, all in the g3-js
region, all removing one condition:

  A1  intPaintTenure()   tenure === 'rent' || tenure === 'buying'
                      -> tenure === 'rent'
  A2  intPayload()       answers.tenure && answers.tenure !== 'own'
                      -> answers.tenure === 'rent'
  A3  intLocalProblem()  answers.tenure && answers.tenure !== 'own'
                      -> answers.tenure === 'rent'

so that a `buying` homeowner meets the owner's form: no permission tick, no
required statement, note marked Optional — which is what G1B §5 already says.

THE 2708/2734 COLLISION. A2 and A3 are the IDENTICAL string
`if (answers.tenure && answers.tenure !== 'own') {`. Anchoring on that line
alone matches twice. Each anchor below is widened by its following line so each
occurs exactly once, and guard 2 asserts that rather than trusting it.

WHAT THIS DOES NOT TOUCH. No markup: `#bgIntCond`, the checkbox, the label, the
hint and the note field stay exactly as authored — only the JS that shows or
hides them changes. No CSS. No engine. No questions. No result logic. No
Save/My Plot. No consent wording. No field labels. No footer. No switch. `own`
and `rent` behaviour are byte-identical in effect, and guard 10 proves the
`rent` branch body survives intact and in order.

A DELIBERATE NON-CHANGE, recorded so the next reader does not "tidy" it: inside
the now rent-only block, `var who = (tenure === 'rent') ? ... : 'the current
owner';` keeps its dead else arm. Collapsing it is not one of the four approved
changes, it would alter a string-literal set that guard 11 pins, and leaving it
costs nothing.

GUARD DISCIPLINE. Textual assertions run on comment-stripped text where the
assertion is about executable code, because this builder rewrites a comment and
several guards reason about words that also appear in comments. Asserting
mention rather than assertion is the recorded DISC-025 failure class.

    python3 build-g1b-tenure-alignment.py --check   # guards only, writes nothing
    python3 build-g1b-tenure-alignment.py           # apply
"""

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "disc025-borrowed-garden-check.html"

BASE_SHA = "bd08ce67d004a8b24be00bc50e75a31bcf18693dd5e9dfb6974267917e327c19"

# ------------------------------------------------------------ the three sites
A1_OLD = """  /* The tenure rule, rendered. The wording is the homeowner's own statement,
     never a document: PlotNua asks for neither and stores neither. */
  function intPaintTenure() {
    var cond = $('bgIntCond');
    var tenure = answers.tenure;
    if (tenure === 'rent' || tenure === 'buying') {"""

A1_NEW = """  /* The tenure rule, rendered. The wording is the homeowner's own statement,
     never a document: PlotNua asks for neither and stores neither.
     G1B §5, as frozen: `rent` is the ONLY tenure that needs somebody else's
     agreement before PlotNua could ever introduce anyone, so `rent` is the only
     tenure that shows this block. `buying` is storable with no permission and
     no statement, and meets the same form an owner meets. It remains
     non-promotable, which is a G7 decision and not a form control.
     Aligned 8 October 2026 under founder decision D-G5-1 = option 1: this
     condition previously also matched `buying`, which asked a `buying`
     homeowner for permission the frozen contract does not require. */
  function intPaintTenure() {
    var cond = $('bgIntCond');
    var tenure = answers.tenure;
    if (tenure === 'rent') {"""

# Widened by the following line: the bare condition occurs twice in the file.
A2_OLD = """    if (answers.tenure && answers.tenure !== 'own') {
      body.permission_confirmed = $('bgIntPerm').checked === true;"""
A2_NEW = """    if (answers.tenure === 'rent') {
      body.permission_confirmed = $('bgIntPerm').checked === true;"""

A3_OLD = """    if (answers.tenure && answers.tenure !== 'own') {
      if (!$('bgIntPerm').checked) return 'permission_confirmed';"""
A3_NEW = """    if (answers.tenure === 'rent') {
      if (!$('bgIntPerm').checked) return 'permission_confirmed';"""

SITES = [("A1 intPaintTenure", A1_OLD, A1_NEW),
         ("A2 intPayload", A2_OLD, A2_NEW),
         ("A3 intLocalProblem", A3_OLD, A3_NEW)]

# Regions that must be byte-identical afterwards. g3-js is the ONLY one that
# may change.
FROZEN = [
    ("engine",  "/* PLOTNUA-DISC025-ENGINE-BEGIN */",
                "/* PLOTNUA-DISC025-ENGINE-END */"),
    ("save",    "/* PLOTNUA-JOURNEY-SAVE-BEGIN */",
                "/* PLOTNUA-JOURNEY-SAVE-END */"),
    ("g3-html", "<!-- PLOTNUA-G3-HTML-BEGIN",
                "<!-- PLOTNUA-G3-HTML-END -->"),
    ("g3-css",  "/* ---- G3 · EXPRESSION OF INTEREST",
                "PLOTNUA-G3-CSS-END */"),
]
G3_JS = ("g3-js", "/* PLOTNUA-G3-INTEREST-BEGIN", "/* PLOTNUA-G3-INTEREST-END */")

EXPECTED_FROZEN = {
    "engine":  "72c0f466ab4aa198",
    "save":    "df88b6e3bef36c4b",
    "g3-html": "829ff4f63724506c",
    "g3-css":  "b7e873413ceb6dc7",
}

# THE ONE DENIAL THIS BUILDER MUST GUARD ITSELF. It is built by JS inside
# g3-js, the only region allowed to change, and the equivalent denial in the
# Worker is what prove-guards.mjs G36b caught when the Worker pass rewrapped it.
#
# The other two homeowner-visible denials are deliberately NOT listed here:
#   - "Joining the register is not a match and does not guarantee one" is in
#     g3-html, pinned byte-identical by guard 7.
#   - "It isn't a match or an introduction" is the PS-1 footer, outside g3-js,
#     pinned byte-identical by guard 9.
# Asserting them here would be redundant, and the first version of this list
# got them WRONG: it used a typographic apostrophe where the source carries
# `&rsquo;`, so the assertion could never have matched and refused a correct
# patch. A guard that cannot pass is as useless as one that cannot fail.
DENIALS = [
    "We do not ask for a deed, a lease, or ",
]


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def region(t, b, e):
    if b not in t or e not in t:
        die("region marker missing: %r / %r" % (b, e))
    return t[t.index(b):t.index(e) + len(e)]


def strip_comments(js):
    """Remove /* ... */ and // ... so guards test executable text only."""
    js = re.sub(r"/\*.*?\*/", " ", js, flags=re.S)
    js = re.sub(r"(?m)//.*$", " ", js)
    return js


def main():
    check = "--check" in sys.argv
    src = TARGET.read_text(encoding="utf-8")
    before = hashlib.sha256(src.encode("utf-8")).hexdigest()

    print("  TARGET  %s" % TARGET.name)
    print("  BEFORE  %d bytes  sha256 %s" % (len(src.encode("utf-8")), before))
    print()

    # ---- guard 1 · base identity
    if before != BASE_SHA:
        die("the target is not the frozen deployed page %s... — refusing to "
            "patch an unexpected file" % BASE_SHA[:16])
    print("  G1  base is the frozen deployed page                        OK")

    # ---- guard 3 · not re-runnable over its own output
    for frag in ("if (tenure === 'rent') {", "if (answers.tenure === 'rent') {"):
        if frag in src:
            die("%r is already present; this builder is not re-runnable over "
                "its own output" % frag)
    print("  G3  not re-runnable over its own output                     OK")

    # ---- guard 2a · THE PRECONDITION, checked BEFORE the anchors. The bare
    # condition really is ambiguous, so the widening below is doing work rather
    # than decorating. Ordered first because any sabotage of a bare occurrence
    # also breaks a widened anchor: if the per-site loop ran first it would
    # always fire instead, and this guard could never be shown capable.
    bare = "    if (answers.tenure && answers.tenure !== 'own') {"
    if src.count(bare) != 2:
        die("expected the bare condition twice (the 2708/2734 collision this "
            "builder widens around); it is not genuinely ambiguous \u2014 found %d"
            % src.count(bare))
    print("  G2a the bare condition is genuinely ambiguous (x2)          OK")

    # ---- guard 2 · each WIDENED anchor occurs exactly once
    for label, old, _new in SITES:
        n = src.count(old)
        print("  G2  %-18s anchor occurrences = %d (must be 1)   %s"
              % (label, n, "OK" if n == 1 else "*** FAIL"))
        if n != 1:
            die("%s anchor occurs %d times, expected exactly 1 — widen it"
                % (label, n))

    # ---- guard 4 · the switch is not touched
    if "var INTEREST_PUBLIC = false;" not in src:
        die("INTEREST_PUBLIC = false is not present before the patch")

    out = src
    for _label, old, new in SITES:
        out = out.replace(old, new, 1)

    if "var INTEREST_PUBLIC = false;" not in out:
        die("INTEREST_PUBLIC = false did not survive the patch")
    print("  G4  INTEREST_PUBLIC = false survives                        OK")

    # ---- guards 5-8 · four frozen regions byte-identical
    for name, b, e in FROZEN:
        a = hashlib.sha256(region(src, b, e).encode()).hexdigest()
        z = hashlib.sha256(region(out, b, e).encode()).hexdigest()
        ok = a == z and z.startswith(EXPECTED_FROZEN[name])
        print("  G%-2s %-8s %s  %s"
              % (5 + [n for n, _, _ in FROZEN].index(name), name,
                 "IDENTICAL" if a == z else "*** CHANGED", z[:16]))
        if a != z:
            die("frozen region %s changed" % name)
        if not z.startswith(EXPECTED_FROZEN[name]):
            die("frozen region %s is %s..., expected %s... — the base is not "
                "the artefact this builder was written against"
                % (name, z[:16], EXPECTED_FROZEN[name]))

    # ---- guard 9 · everything OUTSIDE g3-js is byte-identical
    _, gb, ge = G3_JS
    pre_a, post_a = src[:src.index(gb)], src[src.index(ge) + len(ge):]
    pre_z, post_z = out[:out.index(gb)], out[out.index(ge) + len(ge):]
    if pre_a != pre_z or post_a != post_z:
        die("something outside the g3-js region changed — the correction has "
            "overreached")
    print("  G9  everything outside g3-js is byte-identical              OK")

    js_a = strip_comments(region(src, gb, ge))
    js_z = strip_comments(region(out, gb, ge))

    # ---- guard 10 · the rent branch bodies survive, intact and in order
    rent_body = ["$('bgIntPermLab').textContent =",
                 "body.permission_confirmed = $('bgIntPerm').checked === true;",
                 "if (!$('bgIntPerm').checked) return 'permission_confirmed';",
                 "if ($('bgIntNote').value.trim().length < 20) return 'garden_note';"]
    for frag in rent_body:
        if js_z.count(frag) != 1:
            die("rent-path statement %r is not present exactly once after the "
                "patch" % frag[:52])
    if not (js_z.index(rent_body[2]) < js_z.index(rent_body[3])):
        die("the rent refusals are out of order after the patch")
    print("  G10 rent branch bodies intact and in order                  OK")

    # ---- guard 13 · the denials survive, each unbroken on one line
    for d in DENIALS:
        if out.count(d) != 1:
            die("the denial %r must appear exactly once, unbroken on one line "
                "(found %d)" % (d[:44], out.count(d)))
    print("  G13 homeowner-visible denials survive, one line each        OK")

    # ---- guard 14 · no promotion / introduction logic in executable code
    for word in ("introduc", "promot", "eligib", "matchable"):
        if re.search(word, js_z, re.I):
            die("executable g3-js now mentions %r — promotion is a G7 decision "
                "and must not be built here" % word)
    print("  G14 no promotion/introduction logic in executable g3-js     OK")

    # ---- guard 12 · NOTHING IS ADDED, and exactly the two expected
    # (ordered AFTER G13/G14: a sabotage that breaks the denial or adds
    # promotion logic also perturbs the literal set, so the literal guard
    # would mask both and report them blind.)
    # comparison literals are dropped.
    # Set-equality was the first version of this guard and it fired correctly:
    # inside g3-js, `'buying'` occurs ONLY in the condition A1 removes, and
    # `'own'` ONLY in the two conditions A2/A3 remove. The vocabulary copies
    # live in the ENGINE region, which guard 5 pins byte-identical. So the two
    # removals are the correction itself, not a side effect — and naming them
    # exactly is a stronger claim than "unchanged" would have been.
    lits = lambda t: set(re.findall(r"'[^'\n]*'|\"[^\"\n]*\"", t))
    a, z = lits(js_a), lits(js_z)
    added, removed = z - a, a - z
    if added:
        die("new executable string literals appeared: %s \u2014 this correction "
            "introduces no copy" % sorted(added))
    if removed != {"'buying'", "'own'"}:
        die("expected exactly {'buying', 'own'} to be dropped from g3-js; got %s"
            % sorted(removed))
    print("  G12 no literal added; exactly 'buying' + 'own' dropped      OK")
    # And they must be GONE from executable g3-js, not merely rarer: after this
    # correction no g3-js code path compares tenure to either value.
    for lit in ("'buying'", "'own'"):
        if lit in js_z:
            die("%s still appears in executable g3-js after the patch" % lit)
    print("  G12b neither literal survives in executable g3-js           OK")

    # ---- guard 11 · THE CATCH-ALL, deliberately LAST. G12-G14 above name
    # what went wrong; this one catches anything they did not think of.
    # An earlier draft ran it here BEFORE them, which masked all four and
    # reported them blind though they worked — the same ordering mistake the
    # Worker builder made. Specific diagnosis before generic.
    # MOST SPECIFIC FIRST. The first version of this normaliser put the short
    # `tenure === 'rent'` rule before the long `answers.tenure === 'rent'`, so
    # it ate the substring and left `answers.@@T1@@` against `@@T2@@` — the
    # guard fired on its own normalisation rather than on the code. A guard
    # that can lie in this direction can also lie in the other, so the order
    # is pinned by length, not by site number.
    norm = lambda t: (t.replace("tenure === 'rent' || tenure === 'buying'", "@@T1@@")
                       .replace("answers.tenure && answers.tenure !== 'own'", "@@T2@@")
                       .replace("answers.tenure === 'rent'", "@@T2@@")
                       .replace("tenure === 'rent'", "@@T1@@"))
    if norm(js_a) != norm(js_z):
        die("executable code changed somewhere other than the three conditions")
    print("  G11 executable text differs ONLY in those conditions        OK")


    if check:
        print("\n  --check: every guard passed. Nothing written.")
        return

    TARGET.write_text(out, encoding="utf-8")
    after = hashlib.sha256(out.encode("utf-8")).hexdigest()
    print()
    print("  g3-js   %s -> %s"
          % (hashlib.sha256(region(src, gb, ge).encode()).hexdigest()[:16],
             hashlib.sha256(region(out, gb, ge).encode()).hexdigest()[:16]))
    print("  AFTER   %d bytes  sha256 %s" % (len(out.encode("utf-8")), after))
    print("  DELTA   %+d bytes" % (len(out.encode("utf-8")) - len(src.encode("utf-8"))))
    print()
    print("  THREE LOGIC CHANGES, all in g3-js:")
    print("    intPaintTenure   'rent' || 'buying'      -> 'rent'")
    print("    intPayload       tenure && !== 'own'     -> tenure === 'rent'")
    print("    intLocalProblem  tenure && !== 'own'     -> tenure === 'rent'")


if __name__ == "__main__":
    main()
