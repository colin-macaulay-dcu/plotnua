#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PlotNua — build-verdict-hero.py

RESTORE THE RESIDENTIAL PROPERTY-VERDICT HERO.
Founder authorisation, 11 October 2026. Applies ON TOP of Option B.

WHAT THIS RECOVERS, AND FROM WHERE.

PlotNua shipped a residential property-verdict hero until commit fdfa3f8
("Launch: complete flagship Home result journey", 9 September 2026), where
renderHomeVerdictHero(C) mounted the governed COPY[state] triple into
<div class="results-hero" id="hmrHero"> using the shared premium hero
classes. That renderer was removed when the residential journey was folded
into the one Garden Room renderer; the 15-line comment explaining WHY the
verdict reuses the hero presentation but never calls buildResultsHero()
survived as an orphan above pnResidentialResults(). This restores the
renderer the comment describes.

IT IS NOT A PASTE. The historical tree was

    .results-hero-inner.is-fieldonly > .results-hero-body > name/editorial

and the hero has since gained .rh-identity and .rh-split, with the name
moved OUT of .results-hero-body into the identity band. Pasting the 2026
function verbatim would put the name back inside the body's two-column grid,
where the rules at lines 4463-4466 would catch it in column 1. So the
verdict follows the CURRENT hero tree:

    .results-hero-inner.is-fieldonly
    |- .rh-identity          > h2.results-hero-name        COPY[s][0]
    `- .rh-split
       `- .results-hero-body > p.results-hero-editorial    COPY[s][1]
                             > p.hm-calm                   COPY[s][2]

Five classes, all already in the stylesheet with live rules. NO CSS IS
ADDED: `is-fieldonly` exists precisely for a hero with no photograph and is
set by buildResultsHero() today whenever a product has no imageUrl.

ZERO RESULTS, WITHOUT TOUCHING PN_PRODUCT_SECTIONS. The founder required
proof of necessity before reclassifying the shared #matchPrimary container.
It is NOT necessary: the zero path hides the product sections and the
verdict render runs AFTER that branch, so setting host.hidden = false there
is sufficient. PN_PRODUCT_SECTIONS, PN_DECISION_SECTIONS and the
disjointness assertion are all left exactly as shipped, and this builder
refuses if any of their counts move.

THE LENS RAIL MOVE IS SYMMETRIC. Moving three sibling nodes is a permanent
DOM mutation, so a Garden Room search later in the same session would
inherit it. pnLensRailAfterOptions(after) therefore RESTORES the shipped
order whenever `after` is false, and the single call site passes
(pnResidential && pnNoLead) — so Garden Room and a genuine residential lead
both put the rail back where it ships.

THE GENUINE-LEAD CASE IS DELIBERATELY UNTOUCHED. Where the governed split
names exactly one caveat-free candidate, that product is not "arbitrarily
selected" and buildResultsHero() still carries its price, supplier, Save
and next step. The verdict hero is gated on the no-lead state, which is
every state the live artefact can reach today (four caveat-free candidates)
plus the zero-product state. Flagged for the founder, not assumed.

Usage:
  python3 atlas-tools/build-verdict-hero.py --check
  python3 atlas-tools/build-verdict-hero.py
  python3 atlas-tools/build-verdict-hero.py --revert
"""

import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "your-plot.html")
BAK = PAGE + ".bak-verdicthero"

BASELINE_SHA16 = "ea8f5229808d157c"      # Option B applied


# ---------------------------------------------------------------------------
# THE FIVE EDITS
# ---------------------------------------------------------------------------

# V1 · carry the governed triple through, alongside the sentence it already
#      builds. One key. The concatenated `verdict` is NOT removed: it stays
#      as the fallback and as the property-check lede if the hero cannot
#      render.
V1_FIND = "        verdict: C[0] + ' — ' + C[1] + '. ' + C[2],\n"
V1_REPL = """        verdict: C[0] + ' — ' + C[1] + '. ' + C[2],
        /* THE SAME THREE GOVERNED STRINGS, UNCONCATENATED. The verdict hero
           sets them as three elements; the sentence above stays as the
           fallback and is suppressed, not deleted, when the hero renders.
           Nothing new is computed: this is COPY[d.st] by reference. */
        verdictParts: C,
"""

# V2 · the renderer + the symmetric rail mover, declared immediately above
#      the residential bridge so both are in scope with `els`.
V2_FIND = "  window.__PN_RENDER_RESIDENTIAL__ = function (results, fit) {\n"
V2_REPL = """  /* THE PROPERTY VERDICT, IN THE POSITION THE RECOMMENDATION OCCUPIES.

     Recovered from renderHomeVerdictHero() (removed at fdfa3f8) and
     re-tracked onto the CURRENT hero tree: .rh-identity carries the name,
     .rh-split carries the body. The product hero builder is NOT called — it
     is bound to a {role, product, ctx} triple and reaches the price view,
     the Save actions, the Irish route note and the governed gallery, none
     of which a property verdict has. What is reused is the PRESENTATION:
     the tinted field, its depth layers, the display-size name and the
     editorial line.

     `is-fieldonly` is the shipped no-photograph hero variant, which the
     product hero sets for itself whenever a product has no imageUrl. Every
     class below is already in the stylesheet. No CSS is added.

     The three strings are COPY[state], unchanged and in their existing
     order: the verdict, the homeowner-first sentence, the explanation. */
  function pnRenderVerdictHero(parts){
    const host = els.matchPrimary;
    if (!host || !parts || !parts.length || !parts[0]) return false;
    host.innerHTML = '';
    const wrap = document.createElement('div');
    wrap.className = 'results-hero-inner is-fieldonly';
    const identity = document.createElement('div');
    identity.className = 'rh-identity';
    const name = document.createElement('h2');
    name.className = 'results-hero-name';
    name.textContent = parts[0];
    identity.appendChild(name);
    const split = document.createElement('div');
    split.className = 'rh-split';
    const body = document.createElement('div');
    body.className = 'results-hero-body';
    if (parts[1]) {
      const ed = document.createElement('p');
      ed.className = 'results-hero-editorial';
      ed.textContent = parts[1];
      body.appendChild(ed);
    }
    if (parts[2]) {
      const detail = document.createElement('p');
      detail.className = 'hm-calm';
      detail.textContent = parts[2];
      body.appendChild(detail);
    }
    split.appendChild(body);
    wrap.appendChild(identity);
    wrap.appendChild(split);
    host.appendChild(wrap);
    /* THE ZERO-RESULT ANSWER, WITHOUT RECLASSIFYING THE CONTAINER.
       The zero path hides every product section, #matchPrimary among them,
       and this render runs after it. One assignment is therefore the whole
       of it: the two shared section lists and the assertion that keeps them
       disjoint are untouched, so a Garden Room render with an empty set
       behaves exactly as it ships. */
    host.hidden = false;
    host.setAttribute('data-pn-verdict', '1');
    return true;
  }

  /* THE LENSES FOLLOW THE OPTIONS — AND GO BACK WHEN THEY SHOULD NOT.

     Three existing sibling nodes, moved. No lens resolver, no lens copy, no
     CSS, no new element. Because a DOM move persists for the life of the
     page, this is SYMMETRIC: called with `after` false it restores the
     shipped order, so a Garden Room search later in the same session, and a
     genuine residential lead, both read exactly as they ship. Called twice
     in the same direction it mutates nothing. */
  function pnLensRailAfterOptions(after){
    const opts = document.getElementById('altResults');
    const optsHead = document.getElementById('altResultsHeading');
    if (!opts || !opts.parentNode || !optsHead) return false;
    const parent = opts.parentNode;
    if (optsHead.parentNode !== parent) return false;
    const ref = after ? opts.nextSibling : optsHead;
    ['matchAlternativesHeading', 'altRailNote', 'altRailWrap']
      .forEach(function (id) {
        const n = document.getElementById(id);
        if (n && n.parentNode === parent) parent.insertBefore(n, ref);
      });
    return true;
  }

  window.__PN_RENDER_RESIDENTIAL__ = function (results, fit) {
"""

# V3 · the one call site for the rail order, inside renderMatchResults where
#      pnNoLead is already known. Covers both journeys and both directions.
V3_FIND = "    const pnProductRows = pnNoLead ? results : alternativeResults;\n"
V3_REPL = """    const pnProductRows = pnNoLead ? results : alternativeResults;
    /* READING ORDER. With the property verdict as the main result the lens
       rail belongs after the buildings it asks questions about; with a
       recommendation above it, it belongs where it ships. One call, both
       directions, so neither journey can inherit the other's order. */
    try { pnLensRailAfterOptions(pnResidential && pnNoLead); } catch (e) {}
"""

# V4 · render the verdict, suppress the duplicate. Placed AFTER the
#      results/zero branch so it survives the zero path's section sweep and
#      is never wiped by renderMatchResults' own `innerHTML = ''`.
V4_FIND = """    showScreen(els.matchResultsScreen);
    window.scrollTo({ top: 0, behavior: 'auto' });
  };
"""
V4_REPL = """    /* THE MAIN RESULT IS THE PROPERTY, NOT A SUPPLIER PRODUCT.

       Order matters twice over. renderMatchResults() clears #matchPrimary
       on entry, and the zero branch above hides it, so the verdict is
       rendered HERE, after both, or it would be erased by one of them.

       Gated on the governed no-lead state. Where the split names exactly
       one caveat-free candidate that product is not arbitrary, and the
       shipped hero keeps its price, supplier, Save and next step. */
    try {
      const pnHasLead = !!(results && results.length && results[0]
                           && results[0].ctx && results[0].ctx.isPreferred);
      const pnVerdictShown = !pnHasLead
        && pnRenderVerdictHero(fit && fit.verdictParts);
      /* NO DUPLICATE VERDICT. #hmrFitVerdict carries the same three strings
         concatenated. It is HIDDEN, not emptied: the text stays in the DOM
         for diagnosis and the property check reads correctly again the
         moment the hero does not render. */
      const pnFitV = document.getElementById('hmrFitVerdict');
      if (pnFitV) pnFitV.hidden = !!pnVerdictShown;
      if (!pnVerdictShown) pnLensRailAfterOptions(false);
    } catch (e) { /* the concatenated verdict below stands on its own */ }
    showScreen(els.matchResultsScreen);
    window.scrollTo({ top: 0, behavior: 'auto' });
  };
"""

EDITS = [
    ("V1  carry COPY[state] through unconcatenated", V1_FIND, V1_REPL),
    ("V2  the verdict hero and the symmetric rail mover", V2_FIND, V2_REPL),
    ("V3  one call site for the rail order", V3_FIND, V3_REPL),
    ("V4  render the verdict, suppress the duplicate", V4_FIND, V4_REPL),
]


# ---------------------------------------------------------------------------
# INVARIANTS
# ---------------------------------------------------------------------------

INVARIANTS = [
    # the founder's explicit no-go: the shared section classification
    "PN_PRODUCT_SECTIONS",
    "PN_DECISION_SECTIONS",
    "DECISION and PRODUCT section sets overlap",
    # Garden Room's ranking and its hero
    "rankArtistStudioCandidates",
    "selectReasonedAlternatives",
    "scoreTrace",
    "isPreferred: index === 0",
    "buildResultsHero",
    # Option B's surface, which must survive untouched
    "buildResultsGalleryCard",
    "pnViewOptionButton",
    "openProductDetail",
    "productDetailContext",
    "pnNoLeadHere",
    "PN_AH_COUNT_WORDS",
    "possibilities worth exploring",
    # publication, qualification, rights, price
    "publicVisibility",
    "pnAuthorisedImage(",
    "pnAttachImageCredit",
    "PN_IMAGE_FALLBACK_SRC",
    "pn-image-fallback",
    "class3a",
    "qualification",
    "__PN_PRICE_VIEW__",
    # the property evidence, which must stay exactly where it is
    "hmrPropertyFit",
    "dhWhy",
    "dhCalc",
    "dhCheck",
    "dhNextList",
    "hmrMatchState",
    # the thing that must never be written without a primary
    "originalRecommendation = {",
    # the governed copy itself
    "Worth exploring",
    "A few things need checking",
    "Space looks like the limit",
    # the lens resolvers
    "raLocalResolve",
    "raEuropeanPick",
    "renderLensRail",
]

FORBIDDEN_IN_NEW_CODE = [
    ".sort(",
    "score",
    "rank",
    "recommended",
    "best match",
    "ahCandidate",
    "pn-no-lead",
    "createElement('section')",
    "PN_DECISION_SECTIONS",
    "innerHTML = '<",
]

# Classes the verdict hero is allowed to use. Every one must ALREADY have a
# rule in the stylesheet before this builder runs.
REQUIRED_CLASSES = [
    "results-hero-inner",
    "is-fieldonly",
    "rh-identity",
    "rh-split",
    "results-hero-body",
    "results-hero-name",
    "results-hero-editorial",
    "hm-calm",
]


def sha16(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def style_bytes(src):
    return sum(len(m) for m in re.findall(r"<style[^>]*>(.*?)</style>", src, re.S))


def element_ids(src):
    return set(re.findall(r'\bid="([A-Za-z0-9_-]+)"', src))


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
            raise SystemExit(
                "REFUSED: anchor %s matched %d times, expected exactly 1.\n"
                "The file is not the baseline this builder was written against."
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
        tmp = os.path.join(ROOT, ".pn-vh-syntax-%d.mjs" % i)
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
        print("reverted to Option B. your-plot.html sha256 %s" % sha16(orig))
        return

    src = open(PAGE, encoding="utf-8").read()
    base = sha16(src)
    if base != BASELINE_SHA16 and not os.path.exists(BAK):
        raise SystemExit(
            "REFUSED: baseline is %s, expected %s (Option B applied). "
            "Revert first." % (base, BASELINE_SHA16))

    # The classes must exist BEFORE, or the hero would need new CSS.
    missing = [c for c in REQUIRED_CLASSES if ("." + c) not in src]
    if missing:
        raise SystemExit("REFUSED: these classes have no existing rule, so the "
                         "hero cannot be built without new CSS: %s" % missing)

    code = new_code_only()
    bad = [t for t in FORBIDDEN_IN_NEW_CODE if t.lower() in code.lower()]
    if bad:
        raise SystemExit("REFUSED: forbidden token(s) in new CODE: %s"
                         % ", ".join(bad))

    # The hero must not use a class outside the approved list.
    used = set(re.findall(r"className = '([^']+)'", code))
    allowed = set()
    for grp in used:
        for c in grp.split():
            allowed.add(c)
    stray = sorted(c for c in allowed if c not in REQUIRED_CLASSES)
    if stray:
        raise SystemExit("REFUSED: the verdict hero uses unapproved class(es): "
                         "%s" % stray)

    before = {t: src.count(t) for t in INVARIANTS}
    before_style, before_ids = style_bytes(src), element_ids(src)

    out, report = apply_edits(src)

    after = {t: out.count(t) for t in INVARIANTS}
    moved = {k: (before[k], after[k]) for k in INVARIANTS if before[k] != after[k]}
    if moved:
        raise SystemExit("REFUSED: invariant token count moved: %s" % moved)

    if style_bytes(out) != before_style:
        raise SystemExit(
            "REFUSED: <style> length changed by %d bytes. The verdict hero is "
            "built from classes that already have rules."
            % (style_bytes(out) - before_style))

    new_ids = element_ids(out) - before_ids
    if new_ids:
        raise SystemExit("REFUSED: new element id(s): %s" % sorted(new_ids))

    for t in ("ahCandidateSet", "ahCandidateGrid", "ahRenderDetail", "hmrHero"):
        if t in out:
            raise SystemExit("REFUSED: retired surface reintroduced: %s" % t)

    added = out.count("\n") - src.count("\n")

    if mode == "--check":
        print("CHECK ONLY — nothing written.")
        print("  baseline              %s" % base)
        print("  anchors matched       %d of %d, each exactly once"
              % (len(report), len(EDITS)))
        print("  lines added           +%d" % added)
        print("  <style> bytes         %d -> %d (unchanged: no CSS added)"
              % (before_style, style_bytes(out)))
        print("  new element ids       none")
        print("  hero classes          %d, all pre-existing" % len(REQUIRED_CLASSES))
        print("  invariant tokens      %d checked, none moved" % len(INVARIANTS))
        print("  section sets          PN_PRODUCT_SECTIONS / "
              "PN_DECISION_SECTIONS untouched")
        print("  would become          %s" % sha16(out))
        for n in report:
            print("    %s" % n)
        return

    if not os.path.exists(BAK):
        open(BAK, "w", encoding="utf-8").write(src)
    open(PAGE, "w", encoding="utf-8").write(out)

    blocks = node_check(PAGE)
    print("applied.")
    print("  syntax                %d inline script block(s) parse" % blocks)
    print("  lines added           +%d" % added)
    print("  <style> bytes         unchanged (%d)" % style_bytes(out))
    print("  your-plot.html        %s -> %s" % (base, sha16(out)))
    print("  revert                python3 atlas-tools/build-verdict-hero.py --revert")


if __name__ == "__main__":
    main()
