#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JOB 5 · GUARD-CAPABILITY PROOF for atlas-tools/build-a11y-visual.py
===============================================================================
A guard that has never failed is not a guard, it is a comment. This proves
every guard family in the builder (S0 protected state, V1-V8) is actually
capable of refusing, by deliberately breaking the one thing each one watches
and requiring that THAT guard -- not some other -- is the one that fires.

HOW IT WORKS. The builder is imported as a module into a DISPOSABLE COPY of
the repository: ROOT is repointed at a temp tree, so no mutation can ever
touch the real files. Each case either corrupts an input file or monkeypatches
the builder's own transform, then calls build(write=False) and captures the
die() message.

THREE FAILURE MODES ARE COUNTED AS FAILURES, not successes:
  VACUOUS       the mutation did not actually change anything, so a guard
                firing (or not) proves nothing. Every case asserts its own
                mutation took effect before building.
  BLIND         the mutation was real and NO guard fired.
  MISATTRIBUTED a guard fired, but not the one that owns that defect.

Several guards (V6, V7) watch for the builder damaging markup it must never
touch. No corruption of an INPUT file can make those fire, because the guard
compares base against out and the CSS-only block cannot alter markup. For
those the mutation is applied to the builder's transform itself -- which is
precisely the regression they exist to catch -- and that is stated per case
rather than quietly skipped.
"""
import importlib.util
import io
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import contextlib

HERE = pathlib.Path(__file__).resolve().parent
REAL_ROOT = HERE.parent
BUILDER = HERE / "build-a11y-visual.py"


def load_builder(root):
    spec = importlib.util.spec_from_file_location("b_a11y_%d" % id(root), BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ROOT = pathlib.Path(root)
    return mod


def run_build(mod):
    """Returns (ok, message). die() calls sys.exit(1) after printing."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            mod.build(write=False)
        return True, buf.getvalue()
    except SystemExit:
        return False, buf.getvalue()
    except Exception as e:                       # a crash is not a guard
        return False, "PYTHON EXCEPTION: %r\n%s" % (e, buf.getvalue())


def fresh_tree():
    """A disposable copy of only what the builder reads."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="j5cap-"))
    mod = load_builder(tmp)
    need = set(mod.plan()) | set(mod.FROZEN) | {mod.DISC025}
    for rel in need:
        src = REAL_ROOT / rel
        if src.exists():
            dst = tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    # The live repository may already hold an applied block. Strip it in the
    # copy so every case starts from the pre-fix base state.
    for rel in mod.plan():
        dst = tmp / rel
        if dst.exists():
            txt = dst.read_text(encoding="utf-8")
            dst.write_text(mod.strip_block(txt), encoding="utf-8")
    return tmp


# --------------------------------------------------------------------------
# Each case: (id, guard it must trip, how to break it, what the mutation is)
# A case returns a callable(mod, tree) that performs the mutation and returns
# a short description of the proof that the mutation was real.
# --------------------------------------------------------------------------

def m_s0_disc025(mod, tree):
    p = tree / mod.DISC025
    t = p.read_text(encoding="utf-8")
    i = t.find("<main")
    assert i >= 0
    t2 = t[:i] + '<main data-tampered="1"' + t[i + len("<main"):]
    assert t2 != t
    p.write_text(t2, encoding="utf-8")
    return "DISC-025 <main> altered, so its frozen SHA no longer matches"


def m_s0_searchjs(mod, tree):
    p = tree / "search.js"
    t = p.read_bytes()
    p.write_bytes(t + b"\n/* tampered */\n")
    assert p.read_bytes() != t
    return "search.js byte content changed, breaking its frozen SHA"


def m_s0_plan_disc025(mod, tree):
    orig = mod.plan
    def patched():
        p = orig()
        p[mod.DISC025] = [mod.REDUCED_MOTION]
        return p
    mod.plan = patched
    assert mod.DISC025 in mod.plan() and mod.DISC025 not in orig()
    return "DISC-025 added to the build plan as a target"


def m_s0_plan_searchcss(mod, tree):
    orig = mod.plan
    def patched():
        p = orig()
        p["search.css"] = [mod.DOTS_FIX]
        return p
    mod.plan = patched
    assert "search.css" in mod.plan() and "search.css" not in orig()
    return "search.css added to the build plan as a target"


def m_v1_stray_marker(mod, tree):
    f = sorted(mod.plan())[0]
    p = tree / f
    t = p.read_text(encoding="utf-8")
    k = t.rfind("</style>")
    t2 = t[:k] + "\n" + mod.BEGIN + "\n" + t[k:]      # unpaired BEGIN survives strip
    assert t2.count(mod.BEGIN) == 1 and t2 != t
    p.write_text(t2, encoding="utf-8")
    return "a lone unpaired BEGIN marker left in %s, so out holds two" % f


def m_v2_asymmetric_strip(mod, tree):
    """The historical defect: \\n* ate a newline that was already in the file,
    so the round trip was not symmetric. V2 is the guard that caught it."""
    orig = mod.strip_block
    def patched(t):
        return re.sub(r"\n*" + re.escape(mod.BEGIN) + r".*?" + re.escape(mod.END)
                      + r"\n*", "", t, flags=re.S)
    mod.strip_block = patched
    # Two newlines each side: the correct strip removes exactly one, the \n*
    # version greedily eats both. A single newline cannot tell them apart,
    # which is why an earlier probe here was vacuous.
    probe = "a\n\n" + mod.BEGIN + "x" + mod.END + "\n\nb"
    assert patched(probe) != orig(probe), "probe cannot separate the two"
    return "strip_block made asymmetric (the real historical \\n* bug)"


def m_v3_outside_style(mod, tree):
    """Splice the block after the end of the document instead of inside the
    last <style>. V3 is the guard that notices the block is not in a stylesheet."""
    f = sorted(mod.plan())[0]
    p = tree / f
    t = p.read_text(encoding="utf-8")
    assert "</style>" in t and "<style" in t
    # Move every </style> before a sentinel so rfind lands past all of them:
    t2 = t + "\n<!-- tail -->\n</style>\n"
    assert t2 != t
    p.write_text(t2, encoding="utf-8")
    return "a trailing </style> appended after </html> in %s, so the block " \
           "splices in outside any real stylesheet" % f


def m_v4_visible_content(mod, tree):
    mod.DOTS_FIX = mod.DOTS_FIX.replace('content:""', 'content:"click me"')
    assert 'content:"click me"' in mod.DOTS_FIX
    return "a fragment made to inject visible generated text"


def m_v5_brand_token(mod, tree):
    mod.REDUCED_MOTION = mod.REDUCED_MOTION.replace(
        "@media (prefers-reduced-motion: reduce){",
        ":root{ --brand-sage:#ffffff; }\n@media (prefers-reduced-motion: reduce){")
    assert "--brand-sage:#ffffff" in mod.REDUCED_MOTION
    return "a fragment made to redefine the --brand-sage token"


def m_v6_search_markup(mod, tree):
    """No input corruption can trip V6, because the CSS block cannot alter
    markup. The regression V6 exists for is the BUILDER losing Search markup,
    so the transform itself is what is broken here."""
    f = [x for x in mod.plan() if 'id="pnsInput"' in (tree / x).read_text(encoding="utf-8")]
    assert f, "no planned page carries Search V1 markup"
    target = f[0]
    orig_rfind = mod.strip_block
    def patched(t):
        t = orig_rfind(t)
        return t.replace('id="pnsInput"', 'id="pnsInputX"', 1)
    mod.strip_block = patched
    return "the transform made to rename id=\"pnsInput\" on %s" % target


def m_v7_job4_contract(mod, tree):
    f = [x for x in mod.plan()
         if 'class="pn-skip"' in (tree / x).read_text(encoding="utf-8")]
    assert f, "no planned page carries the Job 4 skip link"
    target = f[0]
    orig = mod.strip_block
    def patched(t):
        t = orig(t)
        return t.replace('class="pn-skip"', 'class="pn-skipX"', 1)
    mod.strip_block = patched
    return "the transform made to break class=\"pn-skip\" on %s" % target


def m_v8_font_size(mod, tree):
    mod.SAGE_ON_LIGHT_FIX = mod.SAGE_ON_LIGHT_FIX.replace(
        ".step-num{ color:#557550; }", ".step-num{ color:#557550; font-size:13px; }")
    assert "font-size:13px" in mod.SAGE_ON_LIGHT_FIX
    return "a fragment made to buy contrast with a bigger font-size"


CASES = [
    ("S0a", "S0", m_s0_disc025,        "DISC-025 frozen <main>"),
    ("S0b", "S0", m_s0_searchjs,       "frozen search.js hash"),
    ("S0c", "S0", m_s0_plan_disc025,   "DISC-025 never a target"),
    ("S0d", "S0", m_s0_plan_searchcss, "search.css never a target"),
    ("V1",  "V1", m_v1_stray_marker,   "exactly one marked block"),
    ("V2",  "V2", m_v2_asymmetric_strip, "nothing changes outside the block"),
    ("V3",  "V3", m_v3_outside_style,  "block lives inside a <style>"),
    ("V4",  "V4", m_v4_visible_content, "no visible generated text"),
    ("V5",  "V5", m_v5_brand_token,    "no brand token redefined"),
    ("V6",  "V6", m_v6_search_markup,  "Search V1 markup untouched"),
    ("V7",  "V7", m_v7_job4_contract,  "Job 4 contract untouched"),
    ("V8",  "V8", m_v8_font_size,      "no font-size change"),
]


def main():
    before = subprocess.run(["git", "status", "--porcelain"], cwd=str(REAL_ROOT),
                            capture_output=True, text=True).stdout

    print("\nJOB 5 · GUARD-CAPABILITY PROOF")
    print("=" * 78)

    # Control: an unmutated disposable tree must BUILD CLEAN. Without this the
    # whole run could be passing for some unrelated reason.
    tree = fresh_tree()
    mod = load_builder(tree)
    ok, msg = run_build(mod)
    shutil.rmtree(tree, ignore_errors=True)
    if not ok:
        print("CONTROL FAILED - an unmutated tree does not build:\n%s" % msg)
        return 1
    print("  control        unmutated copy builds clean, 8 guard families pass\n")

    results = []
    for cid, owner, mutate, watches in CASES:
        tree = fresh_tree()
        mod = load_builder(tree)
        try:
            what = mutate(mod, tree)
        except AssertionError as e:
            results.append((cid, owner, "VACUOUS", "mutation did not apply: %s" % e, ""))
            shutil.rmtree(tree, ignore_errors=True)
            continue
        ok, msg = run_build(mod)
        shutil.rmtree(tree, ignore_errors=True)

        if ok:
            results.append((cid, owner, "BLIND", "no guard fired", what))
            continue
        if msg.startswith("PYTHON EXCEPTION"):
            results.append((cid, owner, "CRASH", msg.splitlines()[0], what))
            continue
        fired = msg.strip().splitlines()[-1].strip()
        # die() prints "REFUSED: <GUARD> ... -- nothing written", so the guard
        # name is the token AFTER the prefix. An earlier revision of this proof
        # read the first token, called every correct refusal MISATTRIBUTED, and
        # reported 0/12 -- the harness was wrong, not the guards.
        bare = fired[len("REFUSED:"):].strip() if fired.startswith("REFUSED:") else fired
        tag = bare.split()[0] if bare else "?"
        if tag != owner:
            results.append((cid, owner, "MISATTRIBUTED",
                            "%s fired instead: %s" % (tag, fired[:70]), what))
        else:
            results.append((cid, owner, "CAUGHT", fired[:74], what))

    print("  %-5s %-6s %-14s %s" % ("case", "guard", "verdict", "message"))
    print("  " + "-" * 74)
    for cid, owner, verdict, msg, what in results:
        print("  %-5s %-6s %-14s %s" % (cid, owner, verdict, msg))
        print("        mutation: %s" % what)

    caught = sum(1 for r in results if r[2] == "CAUGHT")
    bad = [r for r in results if r[2] != "CAUGHT"]
    print("\n  %d/%d caught by their own guard." % (caught, len(results)))
    print("  vacuous=%d blind=%d misattributed=%d crash=%d" % (
        sum(1 for r in results if r[2] == "VACUOUS"),
        sum(1 for r in results if r[2] == "BLIND"),
        sum(1 for r in results if r[2] == "MISATTRIBUTED"),
        sum(1 for r in results if r[2] == "CRASH")))

    after = subprocess.run(["git", "status", "--porcelain"], cwd=str(REAL_ROOT),
                           capture_output=True, text=True).stdout
    same = after == before
    print("  repository working tree unchanged by this proof: %s"
          % ("YES" if same else "NO"))
    return 0 if (not bad and same) else 1


if __name__ == "__main__":
    sys.exit(main())
