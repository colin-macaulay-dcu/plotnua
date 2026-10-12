#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PlotNua — build-ah-visual-parity.py

THE FIVE CORRECTIONS, from looking at both rendered pages side by side in
the browser. Founder authorisation, 12 October 2026.

  C1  The review harness carries the assessment's figures and findings, so
      the preview shows the hero the real journey builds.
  C2  The homeowner's own 3D property view fills the hero's media column,
      where Garden Room puts the product photograph — with the shipped
      is-fieldonly treatment as the fallback when it cannot be shown.
  C3  The dead space under the hero.
  C4  THE ATLAS ASSESSMENT DOSSIER, in the same .aa-* grammar Garden Room
      uses, carrying the property's own governed assessment.
  C5  Card action buttons to the foot of the plate.

WHAT I SAW, AND WHY EACH ONE IS HERE. Garden Room renders a 2500px
photograph in its hero and then a full labelled evidence dossier —
Manufacturer, Turnkey installation included, Available in the Republic of
Ireland, dimensions, floor area, what Atlas holds, sources, still checking.
Additional Home rendered a headline, three paragraphs, a large gap and a
collapsed accordion. The premium weight of the Garden Room page is in that
dossier, not in its hero, and Additional Home had no equivalent at all.

C4 IS THE IMPORTANT ONE. It does NOT call aaRenderAssessment(): that
function is bound to a product, a supplier and their evidence, and inventing
a product to satisfy it is exactly the confusion this programme exists to
avoid. What is reused is the GRAMMAR — aaEl(), aaFig(), and the frozen
.aa-mast / .aa-head / .aa-rule / .aa-finds / .aa-find / .aa-fig / .aa-mkr
classes — so the property assessment reads in the same editorial spread as
the supplier assessment, from the property's own governed figures.

Usage:
  python3 atlas-tools/build-ah-visual-parity.py --check | (apply) | --revert
"""

import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "your-plot.html")
BAK = PAGE + ".bak-visualparity"
BASELINE_SHA16 = "40a117f7544d9497"


# ---------------------------------------------------------------------------
# C1 · THE REVIEW HARNESS CARRIES THE WHOLE ASSESSMENT
# ---------------------------------------------------------------------------

C1_FIND = "      if (vp) f.verdictParts = vp;\n      return f;\n"
C1_REPL = """      if (vp) f.verdictParts = vp;
      /* THE FIGURES AND FINDINGS, SO THE PREVIEW SHOWS THE REAL HERO.

         The fixture supplied the verdict strings but not the measurement
         figures or the confirmed findings, so the hero rendered its headline
         and its sentences and nothing else — and every visual review of this
         page has been of a hero missing half its content.

         These are fixture values in the fixture's own shape, in the same
         units and the same sentences the real assessment produces, and the
         banner above the page says so in as many words. The production path
         is untouched: renderResult() passes its own `c` and `why`. */
      f.verdictFacts = [
        { k: 'Potential area from your measurements', v: '38.4 m\\u00b2' },
        { k: 'The range these regulations allow',     v: '32\\u201345 m\\u00b2' },
        { k: 'Allowance left in the garden',          v: '45 m\\u00b2' }
      ];
      f.verdictKnown = [
        'Your measurements leave room for about 38.4 m\\u00b2, inside the '
          + '32\\u201345 m\\u00b2 range',
        'Nothing is built in the garden yet, so the full 45 m\\u00b2 allowance '
          + 'is available',
        'You told us the far end of the garden can be reached inside your own '
          + 'property',
        'No new entrance onto the road would be needed',
        'Water and drains would run off the existing house'
      ];
      f.verdictOpenCount = 2;
      f.verdictCalc = [
        { k: 'Garden area',                               v: '186 m\\u00b2' },
        { k: 'Buildings in the garden',                   v: 'none' },
        { k: 'Private open space the house keeps',        v: '\\u2212 60 m\\u00b2' },
        { k: 'Limited by',                                v: 'the open space rule' }
      ];
      f.verdictCheck = [
        'The tax treatment of a home like this. The Government has said it '
          + 'will be clarified; it is not settled yet.',
        'What \\u201coccupied in conjunction with the main house\\u201d means in '
          + 'practice. The regulations use the phrase and do not define it.'
      ];
      return f;
"""


# ---------------------------------------------------------------------------
# C2 · THE PROPERTY'S OWN 3D VIEW IN THE HERO MEDIA COLUMN
# ---------------------------------------------------------------------------

C2_FIND = """    const split = document.createElement('div');
    split.className = 'rh-split';
    const body = document.createElement('div');
    body.className = 'results-hero-body';
    const factsRow = pnVerdictFactsRow(fit && fit.verdictFacts);
"""
C2_REPL = """    const split = document.createElement('div');
    split.className = 'rh-split';

    /* THE HERO'S VISUAL IS THE HOMEOWNER'S OWN PROPERTY.

       Garden Room fills this column with the product's photograph. The
       Additional Home result is not a product, and a supplier's building
       must never stand in for someone's garden — so the column carries the
       one visual that genuinely IS the subject: the Cesium view of their
       property, which this page already builds for Sun & Light.

       NO SECOND 3D SYSTEM. #resultsMapViewport is MOVED, not cloned, and
       activateResultsMapViewport() is the same initialiser Sun & Light
       calls. The panel below keeps its season and time controls and drives
       the same viewport.

       THE FALLBACK IS THE SHIPPED ONE. If the viewport is absent, or the
       property was never geocoded, no media column is appended at all and
       the hero stays is-fieldonly — the exact treatment the product hero
       uses when Atlas holds no photograph it may publish. Nothing half-built
       is ever shown. */
    const pnVp = document.getElementById('resultsMapViewport');
    const pnLocated = !!(window.pnLastGeocode || document.getElementById('propConfirmPlace')
      && document.getElementById('propConfirmPlace').textContent.trim());
    if (pnVp && pnLocated) {
      const mediaCol = document.createElement('div');
      mediaCol.className = 'pn-media-col';
      const frame = document.createElement('div');
      frame.className = 'results-hero-media';
      frame.appendChild(pnVp);
      mediaCol.appendChild(frame);
      split.appendChild(mediaCol);
      wrap.classList.remove('is-fieldonly');
      try { if (typeof activateResultsMapViewport === 'function')
              activateResultsMapViewport(); } catch (e) {}
    }

    const body = document.createElement('div');
    body.className = 'results-hero-body';
    const factsRow = pnVerdictFactsRow(fit && fit.verdictFacts);
"""


# ---------------------------------------------------------------------------
# C3 + C5 · SPACING AND CARD ACTION ORDER
# ---------------------------------------------------------------------------

C35_FIND = """  #screen-match-results #matchPrimary[data-pn-verdict="1"]{
    margin-bottom:var(--pn-space-xl);
  }
"""
C35_REPL = """  #screen-match-results #matchPrimary[data-pn-verdict="1"]{
    margin-bottom:var(--pn-space-lg);
    padding-bottom:0;
  }
  /* C3 — THE DEAD SPACE. Measured in the browser: roughly 140px between the
     hero's last line and the property check, from the hero's own 40px
     bottom padding plus a 96px section gap sized for a ten-block product
     hero. The gap steps to 32px and the hero's bottom padding goes, because
     the onward link is already the hero's closing line. */
  #screen-match-results #matchPrimary[data-pn-verdict="1"] .hero-secondary{
    margin-top:22px;
  }
  /* C5 — THE ACTIONS BELONG AT THE FOOT OF THE PLATE.
     .match-card-actions carries no `order`, so it defaulted to 0 and sat
     ABOVE the maker, the name and the price — measured on the rendered
     page. Garden Room's own order runs maker(1), name(2), price(3),
     reason(4), explain(5), and the renderer appends the actions last. This
     gives them the number that matches where they are appended. */
  #screen-match-results #altResults .match-card-actions{ order:8; }
  #screen-match-results #altResults .results-gallery-body > :last-child{
    order:9;
  }
  /* THE 3D VIEW IN THE HERO, at the proportions the product photograph
     uses. No new values: the same 4/3 frame and the same column width the
     hero media already declares. */
  #screen-match-results #matchPrimary[data-pn-verdict="1"] .results-hero-media{
    aspect-ratio:4/3; border-radius:6px; overflow:hidden;
    background:var(--pn-hair);
  }
  #screen-match-results #matchPrimary[data-pn-verdict="1"]
    .results-hero-media #resultsMapViewport{
    width:100%; height:100%; min-height:0;
  }
"""


# ---------------------------------------------------------------------------
# C4 · THE ATLAS ASSESSMENT DOSSIER, FOR THE PROPERTY
# ---------------------------------------------------------------------------

C4_FIND = "  window.__PN_RENDER_RESIDENTIAL__ = function (results, fit) {\n"
C4_REPL = """  /* ================= THE PROPERTY'S ATLAS ASSESSMENT =====================

     THE SAME EDITORIAL SPREAD, A DIFFERENT SUBJECT.

     aaRenderAssessment() is NOT called: it is bound to a product, a
     supplier and their evidence, and inventing a product to satisfy it
     would be the HOME-as-Garden-Room confusion this branch exists to
     avoid. What is reused is the GRAMMAR — aaEl(), aaFig(), and the frozen
     .aa-mast / .aa-head / .aa-rule / .aa-finds / .aa-find / .aa-fig /
     .aa-mkr classes — so the property assessment reads as the same
     editorial spread, in the same section, at the same rhythm.

     Every figure and every finding comes from the assessment the page has
     already computed. Nothing is derived here, nothing is rounded again,
     and a datum the assessment did not produce is absent rather than
     estimated. */
  function pnRenderPropertyAssessment(fit){
    const sec  = document.getElementById('aboutSupplier');
    const host = document.getElementById('supplierRow');
    const t    = document.getElementById('supplierTitle');
    const foot = document.getElementById('supplierFoot');
    if (!sec || !host || !fit) return false;
    const facts = fit.verdictFacts || [];
    const known = fit.verdictKnown || [];
    const calc  = fit.verdictCalc  || [];
    const check = fit.verdictCheck || [];
    if (!facts.length && !known.length) return false;

    host.innerHTML = '';
    host.classList.add('aa');

    /* (1) MASTHEAD — the section's dateline, two-ended as Garden Room's is. */
    const mast = aaEl('div', 'aa-mast');
    const lead = aaEl('span', 'aa-mast-lead');
    try {
      const tpl = document.getElementById('pn-atlas-a-template');
      if (tpl && tpl.content) lead.appendChild(tpl.content.cloneNode(true));
    } catch (e) {}
    lead.appendChild(aaEl('span', 'aa-mast-l', 'Atlas assessment'));
    mast.appendChild(lead);
    const placeEl = document.getElementById('propConfirmPlace');
    mast.appendChild(aaEl('span', 'aa-mast-r',
      (placeEl && placeEl.textContent.trim()) || 'Your property'));
    host.appendChild(mast);

    /* (2) THE CONCLUSION AND ITS STANDFIRST. */
    const head = aaEl('div', 'aa-head');
    const hl = aaEl('div', 'aa-head-l');
    hl.appendChild(aaEl('p', 'aa-find-lab', 'Atlas assessed your property for'));
    hl.appendChild(aaEl('h4', 'aa-title', 'An additional home'));
    const hr = aaEl('div', 'aa-head-r');
    hr.appendChild(aaEl('p', 'aa-stand',
      'Against the published conditions for a home of 32\\u201345 m\\u00b2 in the '
      + 'garden of an existing house, using the measurements and answers you '
      + 'gave.'));
    head.appendChild(hl); head.appendChild(hr);
    host.appendChild(head);
    host.appendChild(aaEl('div', 'aa-rule'));

    /* (3) THE EVIDENCE MATRIX — the figures, at display size. */
    if (facts.length) {
      const finds = aaEl('div', 'aa-finds');
      facts.forEach(function (f, i) {
        const cell = aaEl('div', 'aa-find' + (i === 0 ? ' aa-find--lead' : ''));
        cell.setAttribute('data-level', 'key');
        cell.appendChild(aaEl('p', 'aa-find-lab', f.k));
        const v = aaFig('aa-fig' + (i === 0 ? ' aa-fig--big' : ''), f.v, 0);
        v.setAttribute('data-primary', '1');
        cell.appendChild(v);
        finds.appendChild(cell);
      });
      host.appendChild(finds);
    }

    /* (4) THE SUPPORTING ARITHMETIC, in the tighter spec grid. */
    if (calc.length) {
      const spec = aaEl('div', 'aa-finds');
      spec.setAttribute('data-group', 'spec');
      calc.forEach(function (c) {
        const cell = aaEl('div', 'aa-find');
        cell.setAttribute('data-level', 'spec');
        cell.appendChild(aaEl('p', 'aa-find-lab', c.k));
        cell.appendChild(aaFig('aa-fig', c.v, 0));
        spec.appendChild(cell);
      });
      host.appendChild(spec);
    }

    /* (5) WHAT ATLAS HOLDS — the maker band, carrying the findings. */
    if (known.length) {
      const band = aaEl('div', 'aa-mkr');
      band.appendChild(aaEl('p', 'aa-find-lab', 'What Atlas confirmed about your garden'));
      known.forEach(function (k) {
        band.appendChild(aaEl('p', 'aa-stand', '\\u2713  ' + k));
      });
      host.appendChild(band);
    }

    /* (6) STILL CHECKING — the open questions, named, never counted away. */
    if (check.length) {
      const band = aaEl('div', 'aa-mkr');
      band.appendChild(aaEl('p', 'aa-find-lab', 'Still checking'));
      check.forEach(function (c) {
        band.appendChild(aaEl('p', 'aa-stand', c));
      });
      host.appendChild(band);
    }

    if (t) { t.textContent = 'Atlas assessment of your property'; t.classList.add('aa-sr'); }
    if (foot) { foot.textContent = ''; foot.hidden = true; }
    sec.hidden = false;
    sec.setAttribute('data-pn-property-assessment', '1');
    return true;
  }

  window.__PN_RENDER_RESIDENTIAL__ = function (results, fit) {
"""

C4B_FIND = "      if (!pnVerdictShown) pnLensRailAfterOptions(false);\n"
C4B_REPL = """      if (!pnVerdictShown) pnLensRailAfterOptions(false);
      /* THE DOSSIER. Same section, same grammar, the property's own
         evidence. Rendered only where the verdict is the main result, so
         Garden Room's supplier assessment is never displaced. */
      if (pnVerdictShown) pnRenderPropertyAssessment(fit);
"""


EDITS = [
    ("C1  harness carries figures, findings, arithmetic", C1_FIND, C1_REPL),
    ("C2  the property's 3D view in the hero", C2_FIND, C2_REPL),
    ("C3+C5 spacing and card action order", C35_FIND, C35_REPL),
    ("C4a the property Atlas Assessment dossier", C4_FIND, C4_REPL),
    ("C4b render it when the verdict is the result", C4B_FIND, C4B_REPL),
]

INVARIANTS = [
    "aaRenderAssessment", "function aaEl(", "function aaFig(",
    "PN_PRODUCT_SECTIONS", "PN_DECISION_SECTIONS",
    "rankArtistStudioCandidates", "isPreferred: index === 0",
    "buildResultsHero", "buildResultsGalleryCard", "pnViewOptionButton",
    "pnAuthorisedImage(", "publicVisibility", "class3a",
    "originalRecommendation = {", "pnLensRailAfterOptions",
    "function activateResultsMapViewport", "resultsMapViewport",
    "function pnGoogleIdentity(product){",
]

FORBIDDEN_IN_NEW_CODE = [
    ".sort(", "score", "rank", "recommended",
    "rating", "reviews", "stars",
    "new Cesium", "Cesium.Viewer", "createElement('canvas')",
    "planning permission granted", "guaranteed",
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
        tmp = os.path.join(ROOT, ".pn-vp-syntax-%d.mjs" % i)
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
            raise SystemExit("no backup to revert from")
        orig = open(BAK, encoding="utf-8").read()
        open(PAGE, "w", encoding="utf-8").write(orig)
        print("reverted. sha256 %s" % sha16(orig))
        return

    src = open(PAGE, encoding="utf-8").read()
    base = sha16(src)
    if base != BASELINE_SHA16 and not os.path.exists(BAK):
        raise SystemExit("REFUSED: baseline is %s, expected %s."
                         % (base, BASELINE_SHA16))

    code = new_code_only()
    bad = [t for t in FORBIDDEN_IN_NEW_CODE if t.lower() in code.lower()]
    if bad:
        raise SystemExit("REFUSED: forbidden token(s): %s" % ", ".join(bad))

    before = {t: src.count(t) for t in INVARIANTS}
    before_style = style_bytes(src)
    out, report = apply_edits(src)
    after = {t: out.count(t) for t in INVARIANTS}
    lost = {k: (before[k], after[k]) for k in INVARIANTS if after[k] < before[k]}
    if lost:
        raise SystemExit("REFUSED: token reference lost: %s" % lost)

    added = out.count("\n") - src.count("\n")
    css_added = style_bytes(out) - before_style

    if mode == "--check":
        print("CHECK ONLY — nothing written.")
        print("  baseline          %s" % base)
        print("  anchors matched   %d of %d" % (len(report), len(EDITS)))
        print("  lines added       +%d" % added)
        print("  CSS added         +%d bytes, scoped to [data-pn-verdict]"
              % css_added)
        print("  invariants        %d checked, none lost" % len(INVARIANTS))
        print("  would become      %s" % sha16(out))
        for n in report:
            print("    %s" % n)
        return

    if not os.path.exists(BAK):
        open(BAK, "w", encoding="utf-8").write(src)
    open(PAGE, "w", encoding="utf-8").write(out)
    blocks = node_check(PAGE)
    print("applied.")
    print("  syntax            %d inline script block(s) parse" % blocks)
    print("  lines added       +%d" % added)
    print("  CSS added         +%d bytes" % css_added)
    print("  your-plot.html    %s -> %s" % (base, sha16(out)))
    print("  revert            python3 atlas-tools/build-ah-visual-parity.py --revert")


if __name__ == "__main__":
    main()
