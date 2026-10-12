#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PlotNua — build-no-lead-altresults.py

OPTION B. Founder decision, 11 October 2026.

WHAT THIS DOES, AND WHAT IT DELIBERATELY DOES NOT DO.

The Additional Home candidate set is a GOVERNED EVIDENCE FILTER returned in
catalogue order. It is not a ranking, so `results[0]` is the lowest Product
Code and nothing more. The shipped renderer gave that row the hero, which
asserted a recommendation Atlas had not made.

The retired no-lead-equality build answered this by adding a SECOND product
surface (#ahCandidateSet / #ahCandidateGrid, 17 CSS rules, its own card
builder and its own inline detail panel). Every one of those duplicated
something #altResults already had. The founder stopped it as drift.

Option B instead REUSES the established Garden Room components:

  the grid        #altResults, already repeat(auto-fit, minmax(300px,1fr))
                  with height:100% — already an equal-weight surface
  the card        buildResultsGalleryCard(), already governed for imagery,
                  rights, credit, link-back and price
  the placeholder #altResults .results-gallery-media:has(img.pn-image-fallback)
                  { display:none } — the SHIPPED treatment, unchanged, which
                  is why this builder adds no CSS at all
  the detail      pnViewOptionButton() -> openProductDetail(), both already
                  defined, and `#altResults .pn-view-option` CSS already in
                  the sheet. Y1 retired the CALL from the card because the
                  hero's Next steps block carried the journey. With no hero
                  there is no Next steps block, so the call comes back —
                  residential no-lead only.

NO NEW COMPONENT IS CREATED. NO CSS IS ADDED. Nine anchors, each matched
exactly once, all inside the residential path or behind a residential test.

THE GUARDS. This refuses to run if it would:
  * change any Garden Room invariant token count
  * introduce a sort, a score or a preference marker
  * add a CSS rule (the file's <style> byte length must not grow)
  * add a new element id
  * write originalRecommendation without a primary
  * leave any anchor matched other than exactly once

Usage:
  python3 atlas-tools/build-no-lead-altresults.py --check
  python3 atlas-tools/build-no-lead-altresults.py
  python3 atlas-tools/build-no-lead-altresults.py --revert
"""

import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "your-plot.html")
BAK = PAGE + ".bak-altresults"

BASELINE_SHA16 = "fd13a9359332d897"


# ---------------------------------------------------------------------------
# THE NINE EDITS
# ---------------------------------------------------------------------------

E1_FIND = "    const [primaryResult, ...alternativeResults] = results;\n"
E1_REPL = """    /* THE LEAD IS DERIVED, NOT ASSUMED — OPTION B, 11 October 2026.

       Additional Home runs a governed evidence filter, not a ranking, so
       `results[0]` is the lowest Product Code. The residential candidate
       split has already decided whether a lead can be named at all and
       recorded that verdict per row as ctx.isPreferred; this reads that one
       datum and nothing else. Nothing is scored, nothing is re-ordered, no
       supplier is favoured.

       Garden Room sets isPreferred from its OWN ranking (index === 0), so
       pnNoLead is false on every Garden Room render and every line below
       behaves exactly as it has always behaved. */
    const [pnFirstRow, ...alternativeResults] = results;
    const pnNoLead = pnResidential && !(pnFirstRow && pnFirstRow.ctx
                                        && pnFirstRow.ctx.isPreferred);
    const primaryResult = pnNoLead ? null : pnFirstRow;
    /* ONE PRODUCT SURFACE. With no lead there is no row 0 being held back
       for a hero, so the existing alternatives grid and the existing lens
       rail both receive the whole qualifying set — otherwise the first
       candidate would be lost to a distinction that no longer exists.
       Garden Room passes the tail, exactly as before. */
    const pnProductRows = pnNoLead ? results : alternativeResults;
    /* The hero container collapses rather than holding an empty plate's
       bottom margin. Residential only, so Garden Room never touches the
       attribute. */
    if (pnResidential && els.matchPrimary) els.matchPrimary.hidden = !!pnNoLead;
"""

E2_FIND = ("    const reasoned = pnResidential\n"
           "      ? (alternativeResults || []).map(function (r) {\n")
E2_REPL = ("    const reasoned = pnResidential\n"
           "      ? (pnProductRows || []).map(function (r) {\n")

E3_FIND = "    const lensCount = renderLensRail(primaryResult, alternativeResults, twistIdea);\n"
E3_REPL = "    const lensCount = renderLensRail(primaryResult, pnProductRows, twistIdea);\n"

E4_FIND = ("    renderAltResults(primaryResult, alternativeResults);\n\n"
           "    /* PAINT NOW, REPAINT ONCE")
E4_REPL = ("    renderAltResults(primaryResult, pnProductRows);\n\n"
           "    /* PAINT NOW, REPAINT ONCE")

E5_FIND = "        const settledCount = renderLensRail(primaryResult, alternativeResults, twistIdea);\n"
E5_REPL = "        const settledCount = renderLensRail(primaryResult, pnProductRows, twistIdea);\n"

E6_FIND = "        renderAltResults(primaryResult, alternativeResults);\n"
E6_REPL = "        renderAltResults(primaryResult, pnProductRows);\n"

E7_FIND = "    const picks = !(primary && candidates.length) ? []\n"
E7_REPL = """    /* OPTION B — THE GRID MAY RENDER WITHOUT A PRIMARY, RESIDENTIAL ONLY.

       This gate existed because every sentence on this surface was stated
       relative to the recommendation above it. In residential no-lead there
       is no recommendation and the rows carry their own governed sentences
       already (see the residential branch below), so the gate is the only
       thing standing between four qualifying buildings and the surface
       built to show them equally.

       Garden Room cannot reach pnNoLeadHere: pnResultUse is 'garden-room'
       there, and a Garden Room render always has a primary in any case. */
    const pnNoLeadHere = (pnResultUse === 'residential') && !primary;
    const picks = !((primary || pnNoLeadHere) && candidates.length) ? []
"""

E8_FIND = ("       are all unchanged. */\n\n"
           "    const { actions, openMyPlotLink } = buildSaveActions(product);\n")
E8_REPL = """       are all unchanged. */

    const { actions, openMyPlotLink } = buildSaveActions(product);
    /* THE ROUTE TO OPTION DETAIL, RESIDENTIAL NO-LEAD ONLY.

       pnViewOptionButton() and `#altResults .pn-view-option` have both been
       in this file since JC-2. Y1 retired the CALL from this card — not the
       control — on one stated ground: "The Next steps block below the hero
       carries the journey now." In residential no-lead there is no hero and
       #matchNextStep is hidden, so that ground does not hold and the card
       would otherwise offer Save as its only action.

       `primaryResult` is this builder's own second parameter, so the test
       needs no new state. Garden Room always passes a primary, and so does
       a genuine residential lead, which is why neither can reach this. */
    if (pnResultUse === 'residential' && !primaryResult) {
      actions.insertBefore(pnViewOptionButton(product), actions.firstChild);
    }
"""

E9_FIND = """    const n = host.children.length;
    if (n && bydByoNode()) host.appendChild(bydByoNode());
    host.hidden = n === 0;
    if (head) head.hidden = n === 0;
    if (note) {
      /* P1 — say the number that is on the page. `n` is measured above,
         before the bring-your-own block is attached, so it is exactly the
         count of alternatives and nothing else. */
      const word = ['No', 'One', 'Two', 'Three'][n] || String(n);
      note.textContent = word + ' alternative' + (n === 1 ? '' : 's')
        + ' Atlas found in the same search.';
      note.hidden = n === 0;
    }
"""

E9_REPL = """    const n = host.children.length;
    if (n && bydByoNode()) host.appendChild(bydByoNode());
    host.hidden = n === 0;
    if (head) head.hidden = n === 0;
    /* THE TWO APPROVED STRINGS — OPTION B, 11 October 2026.

       "Other options worth considering" and "N alternatives Atlas found in
       the same search" are both stated RELATIVE TO A PRIMARY. Neither can
       honestly be said when Atlas has named no lead, so in that state the
       two founder-approved strings of 11 October are used instead. They are
       set here rather than in new markup, and the lead case re-asserts the
       shipped heading, so nothing persists from one render to the next.

       The heading carries the figure and the explanation carries the word,
       which is exactly how the two approved sentences were written. */
    if (head) head.textContent = pnNoLeadHere
      ? (String(n) + ' possibilities worth exploring')
      : 'Other options worth considering';
    if (pnNoLeadHere) {
      if (note) {
        const w = PN_AH_COUNT_WORDS[n] || String(n);
        note.textContent = 'Atlas has identified ' + w
          + (n === 1 ? ' building that meets' : ' buildings that meet')
          + ' the current assessment criteria. None has been established as '
          + 'a better match for your property.';
        note.hidden = n === 0;
      }
    } else if (note) {
      /* P1 — say the number that is on the page. `n` is measured above,
         before the bring-your-own block is attached, so it is exactly the
         count of alternatives and nothing else. */
      const word = ['No', 'One', 'Two', 'Three'][n] || String(n);
      note.textContent = word + ' alternative' + (n === 1 ? '' : 's')
        + ' Atlas found in the same search.';
      note.hidden = n === 0;
    }
"""

# The count words. A governed list read by index — not arithmetic, not a
# formatter. Placed immediately above renderAltResults so the only function
# that reads it is the only function that can see it.
E10_FIND = "  function renderAltResults(primaryResult, alternativeResults){\n"
E10_REPL = """  /* The count words, so the approved explanation reads as a sentence rather
     than a figure. A fixed list, read by index. */
  const PN_AH_COUNT_WORDS = ['no', 'one', 'two', 'three', 'four', 'five',
    'six', 'seven', 'eight', 'nine', 'ten'];

  function renderAltResults(primaryResult, alternativeResults){
"""

EDITS = [
    ("E1  derive the lead at the destructure", E1_FIND, E1_REPL),
    ("E2  reasoned reads the whole set", E2_FIND, E2_REPL),
    ("E3  lens rail first paint", E3_FIND, E3_REPL),
    ("E4  altResults first paint", E4_FIND, E4_REPL),
    ("E5  lens rail repaint", E5_FIND, E5_REPL),
    ("E6  altResults repaint", E6_FIND, E6_REPL),
    ("E7  permit the grid without a primary", E7_FIND, E7_REPL),
    ("E8  the Option Detail route", E8_FIND, E8_REPL),
    ("E9  the two approved strings", E9_FIND, E9_REPL),
    ("E10 the count words", E10_FIND, E10_REPL),
]


# ---------------------------------------------------------------------------
# INVARIANTS — Garden Room, governance and evidence tokens whose COUNT must
# not move. A count change means this builder reached something it has no
# business touching.
# ---------------------------------------------------------------------------

INVARIANTS = [
    # the ranking engine and its evidence
    "rankArtistStudioCandidates",
    "selectReasonedAlternatives",
    "scoreTrace",
    "decisionProfile",
    "isPreferred: index === 0",
    # publication, qualification and rights
    "publicVisibility",
    "pnAuthorisedImage(",
    "pnAttachImageCredit",
    "PN_IMAGE_FALLBACK_SRC",
    "pn-image-fallback",
    "attachImageFallback",
    "class3a",
    "qualification",
    "pnCandidateSplit",
    "pnResidentialCandidateList",
    # price presentation
    "__PN_PRICE_VIEW__",
    "pnPriceView",
    # the property assessment, which this build must not touch at all
    "hmrPropertyFit",
    "hmrFitVerdict",
    "dhWhy",
    "dhCalc",
    "dhCheck",
    "dhNextList",
    "PN_DECISION_SECTIONS",
    "PN_PRODUCT_SECTIONS",
    # the hero, the card and the detail screen
    "buildResultsHero",
    "buildResultsGalleryCard",
    "openProductDetail",
    "productDetailContext",
    # the thing that must never be written without a primary
    "originalRecommendation = {",
]

# Tokens that must not appear ANYWHERE in the diff this builder introduces.
FORBIDDEN_IN_NEW_TEXT = [
    ".sort(",
    "score",
    "rank",
    "recommended",
    "best match",
    "preferred candidate",
    "ahCandidate",
    "pn-no-lead",
    "createElement('section')",
]


def sha16(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def style_bytes(src):
    """Total length of every <style> block. Must not change: no CSS added."""
    return sum(len(m) for m in re.findall(r"<style[^>]*>(.*?)</style>", src, re.S))


def element_ids(src):
    return set(re.findall(r'\bid="([A-Za-z0-9_-]+)"', src))


def counts(src):
    return {t: src.count(t) for t in INVARIANTS}


def apply_edits(src):
    out = src
    report = []
    for name, find, repl in EDITS:
        hits = out.count(find)
        if hits != 1:
            raise SystemExit(
                "REFUSED: anchor %s matched %d times, expected exactly 1.\n"
                "The file is not the baseline this builder was written against."
                % (name, hits))
        out = out.replace(find, repl, 1)
        report.append(name)
    return out, report


def check_new_text():
    """Every forbidden token, measured against the replacement text only."""
    blob = "\n".join(r for _, _, r in EDITS)
    # Strip comments before scanning, so the explanatory prose above may
    # name what the code must not do.
    code = re.sub(r"/\*.*?\*/", "", blob, flags=re.S)
    code = "\n".join(l for l in code.splitlines()
                     if not l.strip().startswith("//"))
    bad = [t for t in FORBIDDEN_IN_NEW_TEXT if t.lower() in code.lower()]
    if bad:
        raise SystemExit("REFUSED: forbidden token(s) in new CODE: "
                         + ", ".join(bad))


def node_check(path):
    """Per-<script> syntax check, the convention this repo already uses."""
    src = open(path, encoding="utf-8").read()
    blocks = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", src, re.S)
    ok = 0
    for i, b in enumerate(blocks):
        if not b.strip():
            continue
        tmp = os.path.join(ROOT, ".pn-syntax-%d.mjs" % i)
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
    if base != BASELINE_SHA16 and mode != "--force":
        print("NOTE: baseline is %s, expected %s" % (base, BASELINE_SHA16))
        if not os.path.exists(BAK):
            raise SystemExit(
                "REFUSED: your-plot.html is not the baseline this builder was "
                "written against and no backup exists. Revert first.")

    check_new_text()

    before_counts = counts(src)
    before_style = style_bytes(src)
    before_ids = element_ids(src)

    out, report = apply_edits(src)

    after_counts = counts(out)
    moved = {k: (before_counts[k], after_counts[k])
             for k in INVARIANTS if before_counts[k] != after_counts[k]}
    if moved:
        raise SystemExit("REFUSED: invariant token count moved: %s" % moved)

    after_style = style_bytes(out)
    if after_style != before_style:
        raise SystemExit(
            "REFUSED: <style> length changed by %d bytes. Option B adds NO "
            "CSS — the shipped #altResults rules are the whole presentation."
            % (after_style - before_style))

    new_ids = element_ids(out) - before_ids
    if new_ids:
        raise SystemExit("REFUSED: new element id(s) introduced: %s"
                         % sorted(new_ids))

    # The retired surface must not come back.
    for t in ("ahCandidateSet", "ahCandidateGrid", "ahRenderDetail",
              "ahSelectCandidate", "ahCandidateCard"):
        if t in out:
            raise SystemExit("REFUSED: retired duplicate surface present: %s" % t)

    added = out.count("\n") - src.count("\n")

    if mode == "--check":
        print("CHECK ONLY — nothing written.")
        print("  baseline            %s" % base)
        print("  anchors matched     %d of %d, each exactly once"
              % (len(report), len(EDITS)))
        print("  lines added         +%d" % added)
        print("  <style> bytes       %d -> %d (unchanged: no CSS added)"
              % (before_style, after_style))
        print("  new element ids     none")
        print("  invariant tokens    %d checked, none moved" % len(INVARIANTS))
        print("  retired surface     absent")
        print("  would become        %s" % sha16(out))
        for name in report:
            print("    %s" % name)
        return

    if not os.path.exists(BAK):
        open(BAK, "w", encoding="utf-8").write(src)

    open(PAGE, "w", encoding="utf-8").write(out)

    # byte-identity reverse check
    back = open(BAK, encoding="utf-8").read()
    if sha16(back) != BASELINE_SHA16 and sha16(back) != base:
        raise SystemExit("REFUSED: sidecar does not hold the pre-edit bytes")

    blocks = node_check(PAGE)
    print("applied.")
    print("  syntax              %d inline script block(s) parse" % blocks)
    print("  lines added         +%d" % added)
    print("  <style> bytes       unchanged (%d)" % after_style)
    print("  your-plot.html      %s -> %s" % (base, sha16(out)))
    print("  revert              python3 atlas-tools/build-no-lead-altresults.py --revert")


if __name__ == "__main__":
    main()
