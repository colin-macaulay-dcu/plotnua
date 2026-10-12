#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PlotNua — build-verdict-review-harness.py

INSTRUMENT ONLY. Local review harness, not Results behaviour.

WHY THIS EXISTS. The founder's validation list requires all four governed
verdict states checked at desktop and mobile widths. The local review
harness supplies a property-assessment FIXTURE whose shape predates the
verdict hero: it carries `verdict` (one concatenated sentence) and no
`verdictParts`. So the restored hero correctly declines to render in review
mode, and the four states cannot be seen before deployment.

That is precisely the fault the harness's own comment warns about:
"A harness that hides a shipped section is not a review instrument, it is a
second bug."

WHAT THIS CHANGES. Two things, both inside the already fail-closed local
block or beside the module's existing exports:

  1. the governed verdict table is exposed through the SAME named-export
     convention the module already uses for __PN_RESIDENTIAL_CANDIDATES__
     and __PN_RESIDENTIAL_RESULTS__. One line. It exposes a read-only copy
     of strings that are already homeowner-visible.

  2. the review fixture carries `verdictParts` READ FROM THAT TABLE, and
     ?verdict=1|2|3|4 selects which governed state to review. The fixture
     invents nothing: with the export unavailable it adds no key at all and
     the page behaves exactly as it does now.

WHAT THIS DOES NOT CHANGE. No Results logic, no renderer, no copy, no CSS,
no qualification, no rights. The harness block is already gated on
localhost + http: + ?review=additional-home + intendedUse === 'residential',
and on the live site the first gate fails and none of this runs.

Usage:
  python3 atlas-tools/build-verdict-review-harness.py --check
  python3 atlas-tools/build-verdict-review-harness.py
  python3 atlas-tools/build-verdict-review-harness.py --revert
"""

import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "your-plot.html")
BAK = PAGE + ".bak-verdictharness"

BASELINE_SHA16 = "ebabeedb54a71ee5"      # verdict hero applied


R1_FIND = ("  window.__PN_RESIDENTIAL_RESULTS__ = function () "
           "{ return pnResidentialResults(); };\n")
R1_REPL = """  window.__PN_RESIDENTIAL_RESULTS__ = function () { return pnResidentialResults(); };

  /* THE GOVERNED VERDICT TABLE, FOR THE LOCAL REVIEW HARNESS ONLY.

     Same named-export convention as the two above: one named destination,
     no element, no state, no way to reach anything else. It returns a COPY
     of COPY, so a reader cannot mutate the governed strings, and every
     string in it is already homeowner-visible on this screen.

     The production path does not read this. renderResult() passes
     COPY[d.st] directly. */
  window.__PN_VERDICT_COPY__ = function () {
    var out = {};
    Object.keys(COPY).forEach(function (k) { out[k] = COPY[k].slice(); });
    return out;
  };
"""


R2_FIND = """    function fixture(){
      return {
        verdict: 'Your garden can take a home — worth taking further. '
               + 'The conditions look workable.',
"""
R2_REPL = """    /* WHICH GOVERNED VERDICT STATE TO REVIEW. ?verdict=1|2|3|4, default 1.
       The strings come from the governed table itself through the module's
       named export — the fixture does not carry a copy of them, so it
       cannot drift from what a homeowner actually reads. With the export
       unavailable this returns null, the fixture adds no verdictParts key,
       and the page behaves exactly as it did before this harness change. */
    function reviewVerdictParts(){
      var want = parseInt(qs.get('verdict') || '1', 10);
      if (!(want >= 1 && want <= 4)) want = 1;
      var table = (typeof window.__PN_VERDICT_COPY__ === 'function')
        ? window.__PN_VERDICT_COPY__() : null;
      var parts = table && table[want];
      return (parts && parts.length) ? parts : null;
    }

    function fixture(){
      var vp = reviewVerdictParts();
      var f = {
        verdict: 'Your garden can take a home — worth taking further. '
               + 'The conditions look workable.',
"""


R3_FIND = """                + '<li>Establish services — water, drainage and power.</li>'
                + '<li>Run a Property Check before approaching anyone.</li>'
      };
    }
"""
R3_REPL = """                + '<li>Establish services — water, drainage and power.</li>'
                + '<li>Run a Property Check before approaching anyone.</li>'
      };
      /* THE REAL GOVERNED TRIPLE, so the verdict hero renders in review the
         way it renders in production. Absent when the table cannot be read,
         rather than filled with a stand-in: an invented verdict is the one
         thing this surface may never show. */
      if (vp) f.verdictParts = vp;
      return f;
    }
"""


R4_FIND = ("      b.textContent = 'LOCAL REVIEW MODE · state=' + state + ' · '\n")
R4_REPL = ("      b.textContent = 'LOCAL REVIEW MODE · state=' + state\n"
           "        + ' · verdict=' + (qs.get('verdict') || '1') + ' · '\n")


EDITS = [
    ("R1  export the governed verdict table", R1_FIND, R1_REPL),
    ("R2  the fixture reads the governed state", R2_FIND, R2_REPL),
    ("R3  and carries it as verdictParts", R3_FIND, R3_REPL),
    ("R4  the banner names the state under review", R4_FIND, R4_REPL),
]


# The harness must stay fail-closed, and the verdict strings must stay in
# exactly one place.
INVARIANTS = [
    "if (!isLocal) return;",
    "if (location.protocol !== 'http:') return;",
    "if (qs.get('review') !== 'additional-home') return;",
    "if (intendedUse !== 'residential') return;",
    "THE PROPERTY ASSESSMENT ABOVE IS A FIXTURE",
    # the governed copy, which must not be duplicated
    "Worth exploring",
    "A few things need checking",
    "Space looks like the limit",
    "Your garden looks like it could take one",
    # the hero and its wiring
    "pnRenderVerdictHero",
    "pnLensRailAfterOptions",
    "verdictParts: C,",
    # everything the harness may not touch
    "PN_PRODUCT_SECTIONS",
    "PN_DECISION_SECTIONS",
    "buildResultsGalleryCard",
    "pnAuthorisedImage(",
    "publicVisibility",
    "class3a",
    "isPreferred: index === 0",
    "originalRecommendation = {",
]

FORBIDDEN_IN_NEW_CODE = [
    ".sort(",
    "score",
    "rank",
    "Worth exploring",            # no governed string may be copied in
    "A few things need checking",
    "Space looks like the limit",
    "doesn’t fit",
]


def sha16(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def style_bytes(src):
    return sum(len(m) for m in re.findall(r"<style[^>]*>(.*?)</style>", src, re.S))


def new_code_only():
    blob = "\n".join(r for _, _, r in EDITS)
    code = re.sub(r"/\*.*?\*/", "", blob, flags=re.S)
    return "\n".join(l for l in code.splitlines()
                     if not l.strip().startswith("//"))


def apply_edits(src):
    out, report = src, []
    for name, find, repl in EDITS:
        hits = out.count(find)
        if hits != 1:
            raise SystemExit("REFUSED: anchor %s matched %d times, expected 1."
                             % (name, hits))
        out = out.replace(find, repl, 1)
        report.append(name)
    return out, report


def node_check(path):
    src = open(path, encoding="utf-8").read()
    blocks = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", src, re.S)
    ok = 0
    for i, b in enumerate(blocks):
        if not b.strip():
            continue
        tmp = os.path.join(ROOT, ".pn-rh-syntax-%d.mjs" % i)
        open(tmp, "w", encoding="utf-8").write(b)
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode != 0:
            raise SystemExit("REFUSED: inline script %d does not parse:\n%s"
                             % (i, r.stderr))
        ok += 1
    return ok


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"

    if mode == "--revert":
        if not os.path.exists(BAK):
            raise SystemExit("no %s to revert from" % os.path.basename(BAK))
        orig = open(BAK, encoding="utf-8").read()
        open(PAGE, "w", encoding="utf-8").write(orig)
        print("reverted. your-plot.html sha256 %s" % sha16(orig))
        return

    src = open(PAGE, encoding="utf-8").read()
    base = sha16(src)
    if base != BASELINE_SHA16 and not os.path.exists(BAK):
        raise SystemExit("REFUSED: baseline is %s, expected %s. Revert first."
                         % (base, BASELINE_SHA16))

    code = new_code_only()
    bad = [t for t in FORBIDDEN_IN_NEW_CODE if t.lower() in code.lower()]
    if bad:
        raise SystemExit("REFUSED: forbidden token(s) in new CODE: %s "
                         "(a governed verdict string must live in one place "
                         "only)" % ", ".join(bad))

    before = {t: src.count(t) for t in INVARIANTS}
    before_style = style_bytes(src)

    out, report = apply_edits(src)

    after = {t: out.count(t) for t in INVARIANTS}
    moved = {k: (before[k], after[k]) for k in INVARIANTS if before[k] != after[k]}
    if moved:
        raise SystemExit("REFUSED: invariant token count moved: %s" % moved)

    if style_bytes(out) != before_style:
        raise SystemExit("REFUSED: <style> length changed. This is an "
                         "instrument change and touches no presentation.")

    added = out.count("\n") - src.count("\n")

    if mode == "--check":
        print("CHECK ONLY — nothing written.")
        print("  baseline            %s" % base)
        print("  anchors matched     %d of %d, each exactly once"
              % (len(report), len(EDITS)))
        print("  lines added         +%d" % added)
        print("  <style> bytes       unchanged (%d)" % before_style)
        print("  harness gates       all four intact")
        print("  governed strings    not duplicated into the fixture")
        print("  invariant tokens    %d checked, none moved" % len(INVARIANTS))
        print("  would become        %s" % sha16(out))
        for n in report:
            print("    %s" % n)
        return

    if not os.path.exists(BAK):
        open(BAK, "w", encoding="utf-8").write(src)
    open(PAGE, "w", encoding="utf-8").write(out)
    blocks = node_check(PAGE)
    print("applied.")
    print("  syntax              %d inline script block(s) parse" % blocks)
    print("  lines added         +%d" % added)
    print("  your-plot.html      %s -> %s" % (base, sha16(out)))
    print("  review URLs         ?discovery=residential&review=additional-home"
          "&verdict=1|2|3|4")
    print("  revert              python3 atlas-tools/"
          "build-verdict-review-harness.py --revert")


if __name__ == "__main__":
    main()
