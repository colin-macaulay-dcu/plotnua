#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JOB 6 · GUARD-CAPABILITY PROOF
===============================================================================
prove-job6-interaction.py asserts behaviour. This asserts THAT PROOF CAN FAIL.

Each case copies the repository to a disposable tree, breaks exactly one thing,
re-runs the runtime proof against the copy, and requires that the SPECIFIC
checks owning that defect are the ones that fail.

Counted as FAILURES, not successes:
  VACUOUS        the mutation did not change the file, so nothing was tested
  BLIND          the mutation was real and the proof still passed everything
  MISATTRIBUTED  the proof failed, but not on the checks that own the defect

Every mutation here corresponds to a real way this fix could regress, and two
of them (M2, M5) are mistakes that were actually made and caught during
implementation.

Usage:  python3 atlas-tools/prove-job6-capability.py            # all cases
        python3 atlas-tools/prove-job6-capability.py --only M1,M2
"""
import argparse
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
PROOF = "prove-job6-interaction.py"

# What the copy needs: the pages the sliced proof visits, plus the runtime.
NEED_FILES = ["search.js", "search.css", "search-index-v1.json", "search.html",
              "index.html", "your-plot.html"]
NEED_DIRS = ["assets"]


def disposable():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="j6cap-"))
    (tmp / "atlas-tools").mkdir()
    shutil.copy2(HERE / PROOF, tmp / "atlas-tools" / PROOF)
    for f in NEED_FILES:
        src = REPO / f
        if src.exists():
            shutil.copy2(src, tmp / f)
    for d in NEED_DIRS:
        src = REPO / d
        if src.exists():
            shutil.copytree(src, tmp / d, dirs_exist_ok=True)
    return tmp


def patch(tree, name, old, new, count=1):
    """Returns a one-line description, or raises if the mutation is vacuous."""
    p = tree / name
    t = p.read_text(encoding="utf-8")
    if t.count(old) != count:
        raise AssertionError("anchor found %d times, expected %d in %s"
                             % (t.count(old), count, name))
    p.write_text(t.replace(old, new), encoding="utf-8")
    assert p.read_text(encoding="utf-8") != t, "write produced no change"
    return "%s: %r -> %r" % (name, old[:46].replace("\n", " "),
                             new[:46].replace("\n", " "))


# --------------------------------------------------------------------------
# Mutations. Each returns (description, [check ids that must fail], slice args)
# --------------------------------------------------------------------------
SEARCH_SLICE = ["--pages", "index.html", "--widths", "1440", "--no-tail"]
MYPLOT_SLICE = ["--pages", "", "--widths", "1440"]


def m1(tree):
    d = patch(tree, "search.js",
              "    document.addEventListener('keydown', trapTab, true);",
              "    /* trap removed */")
    return d, ["J5", "J7"], SEARCH_SLICE


def m2(tree):
    """The mistake actually made first: offsetParent excludes position:fixed,
    so #pnsClose dropped out of the focusable set and Shift+Tab escaped."""
    d = patch(tree, "search.js",
              "      if (!el.getClientRects().length) { continue; }",
              "      if (el.offsetParent === null) { continue; }")
    return d, ["J7"], SEARCH_SLICE


def m3(tree):
    d = patch(tree, "search.js",
              "    document.documentElement.classList.add('pns-open');\n    inertBackground();",
              "    document.documentElement.classList.add('pns-open');")
    return d, ["J2"], SEARCH_SLICE


def m4(tree):
    d = patch(tree, "search.js",
              "    restoreBackground();\n    if (e.open) { e.open.setAttribute('aria-expanded', 'false'); e.open.focus(); }",
              "    if (e.open) { e.open.setAttribute('aria-expanded', 'false'); e.open.focus(); }")
    return d, ["J10", "J11"], SEARCH_SLICE


def m5(tree):
    """The ordering trap flagged in the diagnostic: focusing an inert element
    silently does nothing, so focus never returns to the pill."""
    d = patch(tree, "search.js",
              "    restoreBackground();\n    if (e.open) { e.open.setAttribute('aria-expanded', 'false'); e.open.focus(); }",
              "    if (e.open) { e.open.setAttribute('aria-expanded', 'false'); e.open.focus(); }\n    restoreBackground();")
    return d, ["J10"], SEARCH_SLICE


def m6(tree):
    d = patch(tree, "search.js",
              "        restoreBackground();\n        if (e.open) { e.open.setAttribute('aria-expanded', 'false'); }",
              "        if (e.open) { e.open.setAttribute('aria-expanded', 'false'); }")
    return d, ["J12"], SEARCH_SLICE


def m7(tree):
    """Snapshot the focusable set once instead of recomputing per keypress —
    the specific wrong approach the diagnostic rejected."""
    d = patch(tree, "search.js",
              "  function focusablesIn(root) {\n    var out = [];",
              "  var __snap = null;\n  function focusablesIn(root) {\n"
              "    if (__snap) { return __snap; }\n    var out = __snap = [];")
    return d, ["J9"], SEARCH_SLICE


def m8(tree):
    d = patch(tree, "your-plot.html",
              '<div class="season-tabs" role="group" aria-label="Season">',
              '<div class="season-tabs" role="tablist" aria-label="Season">')
    return d, ["J14", "J15"], MYPLOT_SLICE


def m9(tree):
    d = patch(tree, "your-plot.html",
              "      tab.setAttribute('aria-pressed', on ? 'true' : 'false');",
              "      /* aria-pressed no longer maintained */")
    return d, ["J18"], MYPLOT_SLICE


CASES = [
    ("M1", "Tab trap not bound at all", m1),
    ("M2", "offsetParent visibility test (drops fixed #pnsClose)", m2),
    ("M3", "background never made inert on open", m3),
    ("M4", "inert never restored by closePanel", m4),
    ("M5", "inert restored AFTER returning focus to the pill", m5),
    ("M6", "inert never restored on the popstate close route", m6),
    ("M7", "focusables snapshotted once instead of per keypress", m7),
    ("M8", "false season tablist reinstated", m8),
    ("M9", "aria-pressed no longer maintained on season change", m9),
]


def failed_ids(output):
    return set(re.findall(r"^\s+(J\d+)\s+FAIL", output, re.M))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--port", type=int, default=9701)
    a = ap.parse_args()
    wanted = [x.strip() for x in a.only.split(",") if x.strip()]
    cases = [c for c in CASES if not wanted or c[0] in wanted]

    before = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO),
                            capture_output=True, text=True).stdout

    print("\nJOB 6 · GUARD-CAPABILITY PROOF")
    print("=" * 78)
    rows = []
    port = a.port
    for cid, label, fn in cases:
        tree = disposable()
        try:
            try:
                desc, owners, slice_args = fn(tree)
            except AssertionError as e:
                rows.append((cid, label, "VACUOUS", str(e)))
                continue
            port += 1
            r = subprocess.run(
                [sys.executable, "atlas-tools/" + PROOF, "--port", str(port)]
                + slice_args,
                cwd=str(tree), capture_output=True, text=True)
            got = failed_ids(r.stdout)
            if not got:
                rows.append((cid, label, "BLIND", "mutation real, proof passed"))
            elif not (set(owners) & got):
                rows.append((cid, label, "MISATTRIBUTED",
                             "expected %s, got %s" % (owners, sorted(got))))
            else:
                rows.append((cid, label, "CAUGHT",
                             "failed %s (owns %s)" % (sorted(got), owners)))
        finally:
            shutil.rmtree(tree, ignore_errors=True)

    for cid, label, verdict, detail in rows:
        print("  %-4s %-14s %s" % (cid, verdict, label))
        print("        %s" % detail)

    caught = [r for r in rows if r[2] == "CAUGHT"]
    print("\n  %d/%d caught by the checks that own them." % (len(caught), len(rows)))
    for v in ("VACUOUS", "BLIND", "MISATTRIBUTED"):
        print("  %-14s %d" % (v.lower(), len([r for r in rows if r[2] == v])))

    after = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO),
                           capture_output=True, text=True).stdout
    same = after == before
    print("  repository working tree unchanged by this proof: %s"
          % ("YES" if same else "NO"))
    return 0 if (len(caught) == len(rows) and same) else 1


if __name__ == "__main__":
    sys.exit(main())
