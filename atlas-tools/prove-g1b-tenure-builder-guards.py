#!/usr/bin/env python3
"""
GUARD-CAPABILITY PROOF · build-g1b-tenure-alignment.py
===============================================================================
A guard that has never been seen to fail is not a proven guard. This driver
builds a disposable copy of the repository layout, breaks ONE thing per case,
runs the builder in --check mode against the copy, and asserts the builder
REFUSES with the expected guard.

Two kinds of sabotage, each labelled in the output:

  INPUT    the page handed to the builder is corrupted. Proves the guard
           catches a bad target.
  BUILDER  the builder's own A*_NEW constants are corrupted. Proves the guard
           catches a builder that would do the wrong thing — the failure mode
           that actually ships bad code.

The pre-correction page is read FROM GIT, not from disk, so this proof stays
runnable after the correction has landed. Read from disk it would be a one-shot
script: guard 3 (not re-runnable) would fire for every case.

Nothing here touches the real page, the real Worker, Airtable or any switch.

    python3 prove-g1b-tenure-builder-guards.py
"""

import hashlib
import importlib.util
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILDER = ROOT / "atlas-tools" / "build-g1b-tenure-alignment.py"
BUILDER_SRC = BUILDER.read_text(encoding="utf-8")

BASE_REF = "057bb81:disc025-borrowed-garden-check.html"
BASE_SHA = "bd08ce67d004a8b24be00bc50e75a31bcf18693dd5e9dfb6974267917e327c19"

try:
    SRC = subprocess.run(["git", "show", BASE_REF], cwd=ROOT, check=True,
                         capture_output=True, text=True).stdout
except Exception as e:                                        # noqa: BLE001
    raise SystemExit("cannot read the pre-correction page from git (%s): %s"
                     % (BASE_REF, e))
assert hashlib.sha256(SRC.encode("utf-8")).hexdigest() == BASE_SHA, \
    "the committed base page is not bd08ce67..."

_spec = importlib.util.spec_from_file_location("_b", BUILDER)
_b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_b)

A1_NEW_RE = re.compile(r'(?s)^A1_NEW = """.*?"""', re.M)
A2_NEW_RE = re.compile(r'(?s)^A2_NEW = """.*?"""', re.M)
A3_NEW_RE = re.compile(r'(?s)^A3_NEW = """.*?"""', re.M)

passed = failed = 0


def sub_a1(body):
    return lambda b: A1_NEW_RE.sub('A1_NEW = """' + body + '"""', b)


def run_case(label, kind, guard, page_mut=None, builder_mut=None,
             refresh_base=True):
    global passed, failed
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="g1bguard-"))
    try:
        (tmp / "atlas-tools").mkdir()
        page = page_mut(SRC) if page_mut else SRC
        (tmp / "disc025-borrowed-garden-check.html").write_text(page,
                                                                encoding="utf-8")
        b = builder_mut(BUILDER_SRC) if builder_mut else BUILDER_SRC
        if refresh_base:
            # So the case under test fires, not the base-hash guard, which has
            # its own case (C1).
            b = re.sub(r'BASE_SHA = "[0-9a-f]{64}"',
                       'BASE_SHA = "%s"' % hashlib.sha256(
                           page.encode("utf-8")).hexdigest(), b)
        (tmp / "atlas-tools" / "b.py").write_text(b, encoding="utf-8")

        r = subprocess.run([sys.executable, str(tmp / "atlas-tools" / "b.py"),
                            "--check"], capture_output=True, text=True)
        out = r.stdout + r.stderr
        ok = r.returncode == 1 and "REFUSED:" in out and guard in out
        if ok:
            passed += 1
            why = out.split("REFUSED:")[1].strip().split("\n")[0]
            print("  [CAPABLE ] %-46s %-8s %s" % (label, kind, why[:68]))
        else:
            failed += 1
            print("  [*** BLIND] %-46s %-8s rc=%s" % (label, kind, r.returncode))
            print("              expected a refusal naming %r" % guard)
            print("              got: %s" % out.strip().replace("\n", " | ")[-300:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


print("\n  GUARD-CAPABILITY PROOF · build-g1b-tenure-alignment.py\n")

# ---------------------------------------------------------------- INPUT cases
run_case("C1  G1 base hash: target is not the frozen page", "INPUT",
         "not the frozen deployed page",
         page_mut=lambda s: s.replace("</body>", "<!-- x --></body>", 1),
         refresh_base=False)

run_case("C2  G2 A1 anchor absent", "INPUT",
         "anchor occurs 0 times",
         page_mut=lambda s: s.replace(_b.A1_OLD, _b.A1_OLD.replace(
             "var cond = $('bgIntCond');", "var cond = $('bgIntCond'); /* x */"), 1))

# Aimed at A1, not A2. Duplicating A2's or A3's widened anchor also duplicates
# the bare condition inside it, so G2a (the precondition, which now runs first)
# fires instead and the anchor-count guard is never reached. A1's anchor does
# not contain the bare condition, so it isolates cleanly.
run_case("C3  G2 A1 widened anchor duplicated", "INPUT",
         "anchor occurs 2 times",
         page_mut=lambda s: s.replace(_b.A1_OLD, _b.A1_OLD + "\n" + _b.A1_OLD, 1))

run_case("C4  G2a the 2708/2734 collision is gone", "INPUT",
         "not genuinely ambiguous",
         page_mut=lambda s: s.replace(
             "    if (answers.tenure && answers.tenure !== 'own') {\n"
             "      body.permission_confirmed",
             "    if (answers.tenure && answers.tenure !== 'OWN') {\n"
             "      body.permission_confirmed", 1))

run_case("C5  G3 re-run: aligned condition already present", "INPUT",
         "not re-runnable",
         page_mut=lambda s: s.replace("  function intPaintTenure() {",
                                      "  /* x */ if (tenure === 'rent') {}\n"
                                      "  function intPaintTenure() {", 1))

run_case("C6  G4 INTEREST_PUBLIC is not false in the base", "INPUT",
         "INTEREST_PUBLIC = false is not present",
         page_mut=lambda s: s.replace("var INTEREST_PUBLIC = false;",
                                      "var INTEREST_PUBLIC = true;", 1))

# -------------------------------------------------------------- BUILDER cases
run_case("C7  G5 engine region touched", "BUILDER",
         "frozen region engine changed",
         builder_mut=lambda b: b.replace(
             '    for _label, old, new in SITES:\n        out = out.replace(old, new, 1)',
             '    for _label, old, new in SITES:\n        out = out.replace(old, new, 1)\n'
             '    out = out.replace("{ id: \'tenure\',", "{ id: \'tenure\' ,", 1)'))

run_case("C8  G7 g3-html region touched", "BUILDER",
         "frozen region g3-html changed",
         builder_mut=lambda b: b.replace(
             '    for _label, old, new in SITES:\n        out = out.replace(old, new, 1)',
             '    for _label, old, new in SITES:\n        out = out.replace(old, new, 1)\n'
             '    out = out.replace(\'<input type="checkbox" id="bgIntPerm">\', '
             '\'<input type="checkbox" id="bgIntPerm" hidden>\', 1)'))

run_case("C9  G9 something outside g3-js changed (footer)", "BUILDER",
         "outside the g3-js region changed",
         builder_mut=lambda b: b.replace(
             '    for _label, old, new in SITES:\n        out = out.replace(old, new, 1)',
             '    for _label, old, new in SITES:\n        out = out.replace(old, new, 1)\n'
             '    out = out.replace("PlotNua does the homework.", '
             '"PlotNua does the homework!", 1)'))

run_case("C10 G10 the rent permission refusal is dropped", "BUILDER",
         "not present exactly once after",
         builder_mut=lambda b: A3_NEW_RE.sub(
             'A3_NEW = """    if (answers.tenure === \'rent\') {\n'
             "      if (false) return 'permission_confirmed';" '"""', b))

run_case("C11 G11 an extra statement smuggled into A1", "BUILDER",
         "somewhere other than the three conditions",
         builder_mut=sub_a1("""  function intPaintTenure() {
    var cond = $('bgIntCond');
    var tenure = answers.tenure;
    var extra = 1;
    if (tenure === 'rent') {"""))

run_case("C12 G12 a new homeowner-visible literal added", "BUILDER",
         "new executable string literals appeared",
         builder_mut=sub_a1("""  function intPaintTenure() {
    var cond = $('bgIntCond');
    var tenure = answers.tenure;
    var hint = 'Someone nearby may be looking for growing space';
    if (tenure === 'rent') {"""))

run_case("C13 G12 'buying' left behind in a condition", "BUILDER",
         "exactly {'buying', 'own'} to be dropped",
         builder_mut=sub_a1("""  function intPaintTenure() {
    var cond = $('bgIntCond');
    var tenure = answers.tenure;
    if (tenure === 'rent' || tenure === 'buying') {"""))

run_case("C14 G13 the landlord denial broken by rewrapping", "BUILDER",
         "unbroken on one line",
         builder_mut=lambda b: b.replace(
             '    out = src',
             '    out = src.replace("We do not ask for a deed, a lease, or ",\n'
             '                      "We do not ask for a deed, a lease,\\n or ", 1)')
         if '    out = src' in b else b)

run_case("C15 G14 promotion logic added", "BUILDER",
         "promotion is a G7 decision",
         builder_mut=sub_a1("""  function intPaintTenure() {
    var cond = $('bgIntCond');
    var tenure = answers.tenure;
    var introducible = tenure !== 'rent';
    if (tenure === 'rent') {"""))

print()
print("  %d guards proven capable, %d blind" % (passed, failed))
print()
print("  ORDERING NOTE. G11 ('executable text differs ONLY in those")
print("  conditions') is the catch-all and runs AFTER the specific guards")
print("  G12-G14, deliberately, so a precise diagnosis wins over a generic one")
print("  and each specific guard is independently fireable rather than masked.")
sys.exit(1 if failed else 0)
