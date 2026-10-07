#!/usr/bin/env python3
"""
GUARD-CAPABILITY PROOF for build-g3-garden-interest.py
===============================================================================
A guard that has never been seen to fail is not a guard, it is a comment. This
harness imports the builder, deliberately breaks one precondition at a time,
and asserts the builder REFUSES. It never writes to the real target: every
case runs against a temporary copy, and the builder's TARGET is repointed.

Run:  python3 atlas-tools/prove-g3-builder-guards.py
"""

import importlib.util
import io
import pathlib
import shutil
import sys
import tempfile
from contextlib import redirect_stdout

HERE = pathlib.Path(__file__).resolve().parent
REAL = HERE.parent / "disc025-borrowed-garden-check.html"


def fresh():
    """A fresh import of the builder, so each case starts from clean state."""
    spec = importlib.util.spec_from_file_location(
        "g3b", HERE / "build-g3-garden-interest.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run(mod, argv):
    """Run the builder's main() and return (exit_code, output)."""
    old = sys.argv
    sys.argv = ["builder"] + argv
    buf = io.StringIO()
    code = 0
    try:
        with redirect_stdout(buf):
            mod.main()
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
    finally:
        sys.argv = old
    return code, buf.getvalue()


PASS = FAIL = 0


def expect_refusal(name, mutate, argv=None):
    """mutate(mod, tmpfile) breaks one thing. The builder must refuse.

    The baseline is snapshotted AFTER the mutation, not before: several cases
    deliberately edit the copy on disk, and the thing being proven is that the
    BUILDER wrote nothing, not that the harness wrote nothing.
    """
    global PASS, FAIL
    tmpdir = tempfile.mkdtemp(prefix="g3guard-")
    tmp = pathlib.Path(tmpdir) / REAL.name
    shutil.copy2(REAL, tmp)
    mod = fresh()
    mod.TARGET = tmp
    try:
        mutate(mod, tmp)
        before = tmp.read_bytes()
        code, out = run(mod, ["--check"] if argv is None else argv)
        refused = (code != 0) and ("REFUSED" in out)
        untouched = (tmp.read_bytes() == before)
        if refused and untouched:
            PASS += 1
            why = out.strip().splitlines()[-1]
            print("  [CAPABLE] %-44s %s" % (name, why))
        else:
            FAIL += 1
            print("  [BLIND  ] %-44s exit=%s refused=%s untouched=%s"
                  % (name, code, refused, untouched))
            if not refused:
                print("            %s" % out.strip().splitlines()[-1:])
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def expect_pass(name, mutate=None, argv=None):
    global PASS, FAIL
    tmpdir = tempfile.mkdtemp(prefix="g3guard-")
    tmp = pathlib.Path(tmpdir) / REAL.name
    shutil.copy2(REAL, tmp)
    mod = fresh()
    mod.TARGET = tmp
    try:
        if mutate:
            mutate(mod, tmp)
        code, out = run(mod, ["--check"] if argv is None else argv)
        if code == 0 and "REFUSED" not in out:
            PASS += 1
            print("  [CLEAN  ] %-44s accepted, as it should be" % name)
        else:
            FAIL += 1
            print("  [FALSE+ ] %-44s %s" % (name, out.strip().splitlines()[-1]))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


print("\n  G3 BUILDER · GUARD-CAPABILITY PROOF\n")

# --- the control: an unmodified copy must be accepted ----------------------
expect_pass("B0 control (nothing broken)")

# --- anchor guards ---------------------------------------------------------
def kill_anchor(which):
    def f(mod, tmp):
        anchor = dict((n, a) for n, a, _ in mod.INSERTS)[which]
        s = tmp.read_text(encoding="utf-8")
        tmp.write_text(s.replace(anchor, "/*ANCHOR REMOVED*/", 1),
                       encoding="utf-8")
    return f


def dup_anchor(which):
    def f(mod, tmp):
        anchor = dict((n, a) for n, a, _ in mod.INSERTS)[which]
        s = tmp.read_text(encoding="utf-8")
        tmp.write_text(s.replace(anchor, anchor + "\n" + anchor, 1),
                       encoding="utf-8")
    return f


for which in ("CSS", "HTML", "FUNNEL", "JS", "CALL"):
    expect_refusal("B1.%s anchor missing" % which, kill_anchor(which))
for which in ("CSS", "HTML", "FUNNEL", "JS", "CALL"):
    expect_refusal("B2.%s anchor duplicated" % which, dup_anchor(which))

# --- idempotence -----------------------------------------------------------
def already_built(mod, tmp):
    s = tmp.read_text(encoding="utf-8")
    tmp.write_text(s + "\n<!-- PLOTNUA-G3-HTML-BEGIN -->\n", encoding="utf-8")


expect_refusal("B3 G3 marker already present", already_built)

# --- frozen regions --------------------------------------------------------
def frozen_markers_gone(mod, tmp):
    s = tmp.read_text(encoding="utf-8")
    tmp.write_text(s.replace("/* PLOTNUA-DISC025-ENGINE-END */", "/* gone */"),
                   encoding="utf-8")


expect_refusal("B4 frozen engine marker missing", frozen_markers_gone)


def insert_into_engine(mod, tmp):
    """Point an insertion INSIDE the certified engine region. The frozen-region
    hash comparison must catch it. This runs a real write, so --check is not
    used; the builder must still leave the file untouched."""
    s = tmp.read_text(encoding="utf-8")
    victim = "/* PLOTNUA-DISC025-ENGINE-BEGIN */"
    mod.INSERTS = [("CSS", victim, victim + "\nvar sneaked = 1;")]
    assert s.count(victim) == 1


expect_refusal("B4b insertion lands inside the engine", insert_into_engine,
               argv=[])

# --- the consent sentence --------------------------------------------------
def consent_removed(mod, tmp):
    mod.JS = mod.JS.replace(mod.CONSENT, "something I made up")


expect_refusal("B5 consent sentence absent from the JS", consent_removed)


def consent_twice(mod, tmp):
    mod.JS = mod.JS + "\n/* " + mod.CONSENT + " */"


expect_refusal("B5b consent sentence appears twice", consent_twice)


def consent_typographic(mod, tmp):
    mod.CONSENT = mod.CONSENT.replace("'", "’")
    mod.JS = mod.JS.replace(
        "I'm over 18", "I’m over 18").replace(
        "I'd like", "I’d like")


expect_refusal("B6 consent has a typographic apostrophe", consent_typographic)

# --- Q2 independence (code, not mentions) ----------------------------------
def real_save_read(mod, tmp):
    mod.JS = mod.JS.replace(
        "    var sec = $('bgInterest');",
        "    var sec = $('bgInterest');\n"
        "    if (window.PlotNuaJourneySave.has('x')) return;")


expect_refusal("B7 code actually reads PlotNuaJourneySave", real_save_read)


def real_storage_read(mod, tmp):
    mod.JS = mod.JS.replace(
        "    var sec = $('bgInterest');",
        "    var sec = $('bgInterest');\n"
        "    try { localStorage.getItem('x'); } catch (e) {}")


expect_refusal("B7b code actually reads localStorage", real_storage_read)


def denial_removed(mod, tmp):
    mod.JS = mod.JS.replace(
        "Founder decision Q2. This module reads no", "Q2 whatever")


expect_refusal("B8 the Q2 independence denial is gone", denial_removed)

# THE ESSENTIAL NEGATIVE CONTROL. The guard above must NOT fire merely because
# the forbidden name appears in a comment — that was the original defect, and
# the certified contract records the class. This case proves the fix holds.
def mention_only(mod, tmp):
    mod.JS = mod.JS.replace(
        "  var INTEREST_PUBLIC = false;",
        "  /* It never calls PlotNuaJourneySave and never touches\n"
        "     localStorage or sessionStorage, nor does it read bgSave. */\n"
        "  var INTEREST_PUBLIC = false;")


expect_pass("B7c a DENIAL naming the forbidden symbols", mention_only)

# --- the G6 no-promise constraint ------------------------------------------
def promise_added(mod, tmp):
    mod.HTML = mod.HTML.replace(
        "          <button class=\"pc-cta\" type=\"button\" id=\"bgIntOpen\">",
        "        <p class=\"bg-int-p\">Join and we will match you with a "
        "grower.</p>\n"
        "          <button class=\"pc-cta\" type=\"button\" id=\"bgIntOpen\">")


expect_refusal("B9 copy promises a match", promise_added)


def offer_denial_removed(mod, tmp):
    mod.HTML = mod.HTML.replace("Joining the register is not a match",
                                "Joining the register is a good idea")


expect_refusal("B10 offer drops the no-guarantee statement",
               offer_denial_removed)


def confirm_denial_removed(mod, tmp):
    mod.JS = mod.JS.replace("This is a register, not a match",
                            "We are on it")


expect_refusal("B11 confirmation drops the not-a-match statement",
               confirm_denial_removed)

# --- the real build must still be clean after all of that ------------------
expect_pass("B12 control again (state not leaked between cases)")

print("\n  %d capable/clean, %d blind/false-positive\n" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
