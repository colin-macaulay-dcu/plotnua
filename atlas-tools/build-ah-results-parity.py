#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PlotNua — build-ah-results-parity.py

ADDITIONAL HOME RESULTS: VISUAL PARITY WITH GARDEN ROOM.
Founder authorisation, 12 October 2026. Applies on top of the verdict hero.

TEN EDITS, ALL PRESENTATION. Nothing here touches eligibility,
ranking, image permissions, Airtable or search.

  P1  The governed verdict copy, rewritten to professional homeowner
      language, with the planning boundary stated as its own sentence.
  P2  The assessment's own figures carried through to the hero.
  P3  The hero built to Garden Room density: identity band, figures row,
      editorial line, hero-trust evidence list, boundary note, onward link.
  P4  Supplier identity joined, so the SHARED trust layer reaches Additional
      Home products: locality, organisation type, last reviewed, Google
      identity where Atlas holds a verified Place ID, and the Local Option.
  P5  Sun & Light reinstated on the residential path.
  P6  The alternatives grid stops stretching cards to the tallest in the row.
  P7  The orphan price separator fixed.
  P8  The card's reason line at sentence weight, not label weight.
  P9  The hero's trailing space scoped to the verdict state.
  P10 The hero reads the governed imagery reader, not the dead imageUrl
      field, so an authorised photograph reaches the hero on BOTH journeys.

WHAT IS REUSED, NOT INVENTED. Every class is already in the stylesheet:
.rh-identity, .rh-identity-meta, .rh-split, .results-hero-body,
.results-hero-name, .results-hero-price-row, .results-hero-area,
.results-hero-editorial, .results-hero-budget-note, .hero-trust,
.hero-trust-title, .hero-trust-list, .hero-tick, .hero-trust-more,
.hero-secondary, .hero-secondary-link. .hero-trust and its five companions
have carried 36 declarations since the first commit of this file and have
NEVER been built by any renderer; P3 is their first consumer.

THE ONE JOIN (P4). pnSupplierOrgId() reads product.organisationEvidence[0].id.
The Additional Home view deliberately omits that key, so every supplier
signal was dark for these four products. This resolves the id at runtime by
EXACT organisation-name match against the suppliers detail partition Atlas
already publishes. No fuzzy matching, no alias table, no fallback: an
unmatched name yields null and every surface takes its existing no-evidence
path. BIOBUILDS is not in that partition today, so its card shows what Atlas
holds for it and nothing more.

GOOGLE REVIEWS. The shipped identity mechanism and is NOT
touched. It renders only for state === 'verified' with a Place ID. Measured
today: 2 of 61 organisations qualify, and none of the four Additional Home
suppliers is one of them. So nothing Google-shaped appears for them, which
is correct — and the moment Atlas records a verified Place ID it will,
through the same code path as Garden Room.

Usage:
  python3 atlas-tools/build-ah-results-parity.py --check
  python3 atlas-tools/build-ah-results-parity.py
  python3 atlas-tools/build-ah-results-parity.py --revert
"""

import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "your-plot.html")
BAK = PAGE + ".bak-ahparity"
BASELINE_SHA16 = "48ad38918d55cac6"


# ---------------------------------------------------------------------------
# P1 · THE GOVERNED VERDICT COPY
#
# Four states, each: [headline, the homeowner-first sentence, the
# explanation, THE BOUNDARY]. The fourth string is new and is the same on
# every state, because the boundary does not vary with the verdict: an
# initial assessment is never a consent.
# ---------------------------------------------------------------------------

P1_FIND = ("  var COPY = {\n"
           "    1:['Worth exploring','Your garden looks like it could take one',\n")
P1_REPL = """  /* THE GOVERNED VERDICT. Founder decision, 12 October 2026: professional
     homeowner language in place of the tentative phrasing, and the planning
     boundary stated outright rather than implied.

     FOUR STRINGS PER STATE:
       [0] the headline, at display scale in the hero
       [1] the homeowner-first sentence, as the editorial line
       [2] the explanation, unchanged in substance from the governed original
       [3] THE BOUNDARY — what this assessment is not. Identical on every
           state, because an initial assessment is never a consent, whatever
           the verdict. It is rendered as its own note so it can never be
           read as part of the finding above it.

     WHAT THESE MAY NOT SAY, and do not: that permission exists, that
     eligibility is settled, that any authority has decided anything, or
     that PlotNua has applied for or obtained anything. */
  var COPY = {
    1:['Your property meets the initial criteria for an additional home',
       'Atlas has checked your measurements against every condition these regulations set, and found nothing that rules your garden out.',
"""

# The remaining three states, replaced wholesale so the table is one object.
P1B_FIND = """    2:['A few things need checking','Nothing is ruled out',
       'The space itself works. What is not settled yet is listed below — none of it counts against you, and each one has a straightforward way to resolve it.'],
    3:['Space looks like the limit','The garden is what decides it here',
       'Once the house keeps the open space it has to keep, what is left is smaller than the minimum size these regulations allow. That is a fact about the garden, not about permission.'],
    4:['A key condition doesn’t fit','Something outside the measurements',
       'One of the conditions these regulations set is not met, and it is not about size. Whatever the garden measures, that condition would need to change first.']
  };
"""
P1B_REPL = """    2:['Your property meets the initial criteria, with points to confirm',
       'The space itself works. A small number of things are not settled yet, and each has a straightforward way to resolve it.',
       'The space itself works. What is not settled yet is listed below — none of it counts against you, and each one has a straightforward way to resolve it.',
       PN_VERDICT_BOUND],
    3:['Your garden is below the minimum size these regulations allow',
       'Once the house keeps the open space it must keep, what is left is smaller than the minimum. That is a measurement, not a refusal.',
       'Once the house keeps the open space it has to keep, what is left is smaller than the minimum size these regulations allow. That is a fact about the garden, not about permission.',
       PN_VERDICT_BOUND],
    4:['One condition these regulations set is not met',
       'It is not about size. Whatever the garden measures, this condition would need to change first.',
       'One of the conditions these regulations set is not met, and it is not about size. Whatever the garden measures, that condition would need to change first.',
       PN_VERDICT_BOUND]
  };
"""

# State 1's third string closes the array that P1_REPL opened; the boundary
# constant is declared above the table.
P1C_FIND = ("       'On what you told us there is room for a home inside the "
            "32–45 m² range these regulations set, with enough garden still "
            "left for the house, and none of the other conditions is in the "
            "way.'],\n")
P1C_REPL = ("       'On what you told us there is room for a home inside the "
            "32–45 m² range these regulations set, with enough garden still "
            "left for the house, and none of the other conditions is in the "
            "way.',\n       PN_VERDICT_BOUND],\n")

P1D_FIND = "  var ASK = {\n"
P1D_REPL = """  /* THE BOUNDARY, SAID ONCE. An initial assessment against published
     conditions is not a planning decision, and nobody has applied for one.
     This sentence is the same in all four states by design. */
  var PN_VERDICT_BOUND = 'This is Atlas\\u2019s assessment against the published '
    + 'conditions \\u2014 not a planning decision, and not a guarantee of '
    + 'eligibility. Your local authority is the only body that can settle that.';

  var ASK = {
"""


# ---------------------------------------------------------------------------
# P2 · THE ASSESSMENT'S FIGURES, CARRIED THROUGH
# ---------------------------------------------------------------------------

P2_FIND = "        verdictParts: C,\n"
P2_REPL = """        verdictParts: C,
        /* THE FIGURES THE HERO SHOWS, from the SAME `c` object that builds
           the calculation disclosure below. Nothing is recomputed and
           nothing is rounded differently: a figure absent from `c` is
           absent here rather than estimated. */
        verdictFacts: (function(){
          var f = [];
          if (c.measured) f.push({ k: 'Potential area from your measurements',
                                   v: c.maxArea + ' m\\u00b2' });
          f.push({ k: 'The range these regulations allow',
                   v: R.MIN + '\\u2013' + R.MAX + ' m\\u00b2' });
          if (c.measured) f.push({ k: 'Allowance left in the garden',
                                   v: c.allowance + ' m\\u00b2' });
          return f;
        })(),
        /* THE CONFIRMED FINDINGS, for the hero's evidence list. Only the
           affirmative ones: the open questions keep their own place in the
           property check, where they are not competing with a verdict. */
        verdictKnown: why.filter(function(w){ return w[0] === 'hm-yes'; })
                         .map(function(w){ return w[2]; }),
        verdictOpenCount: why.filter(function(w){ return w[0] !== 'hm-yes'; }).length,
"""


# ---------------------------------------------------------------------------
# P3 · THE HERO, BUILT TO GARDEN ROOM DENSITY
# ---------------------------------------------------------------------------

P3_FIND = "  function pnRenderVerdictHero(parts){\n"
P3_REPL = """  /* THE PROPERTY ASSESSMENT AS THE CENTREPIECE.

     Garden Room's hero is substantial because it is FULL, not because it
     carries a photograph — measured: imageUrl is set on 0 of 573 products,
     so that hero has never rendered one. Its weight comes from ten content
     blocks across the identity band and the body.

     This gives the property assessment the same density from the same
     classes, using only figures and findings the assessment already
     computed:

       .rh-identity        the verdict headline, then the locality and the
                           regulated range as the meta row
       .results-hero-price-row   the figures, in the shipped spec-row shape
       .results-hero-editorial   the homeowner-first sentence
       .hero-trust               the confirmed findings as a tick list, with
                           the open-question count as its own link down to
                           the full check. First consumer of these classes.
       .results-hero-budget-note the planning boundary
       .hero-secondary           the onward route

     Every class already has rules. The only new CSS in this build is P9's
     spacing scope. */
  function pnVerdictFactsRow(facts){
    if (!facts || !facts.length) return null;
    const row = document.createElement('div');
    row.className = 'results-hero-price-row';
    facts.forEach(function (f) {
      const s = document.createElement('span');
      s.className = 'results-hero-area';
      s.textContent = f.k + ' \\u2014 ' + f.v;
      row.appendChild(s);
    });
    return row;
  }

  function pnVerdictTrust(known, openCount){
    if (!known || !known.length) return null;
    const box = document.createElement('div');
    box.className = 'hero-trust';
    const title = document.createElement('p');
    title.className = 'hero-trust-title';
    title.textContent = 'What Atlas has confirmed';
    box.appendChild(title);
    const list = document.createElement('ul');
    list.className = 'hero-trust-list';
    known.forEach(function (text) {
      const li = document.createElement('li');
      const tick = document.createElement('span');
      tick.className = 'hero-tick';
      tick.setAttribute('aria-hidden', 'true');
      tick.textContent = '\\u2713';
      const t = document.createElement('span');
      t.textContent = text;
      li.appendChild(tick); li.appendChild(t);
      list.appendChild(li);
    });
    box.appendChild(list);
    /* THE OPEN QUESTIONS ARE COUNTED, NOT HIDDEN, and the count is the real
       one. The link goes to the check that lists them in full. */
    if (openCount > 0) {
      const more = document.createElement('a');
      more.className = 'hero-trust-more';
      more.href = '#hmrPropertyFit';
      more.textContent = openCount + (openCount === 1
        ? ' thing still to confirm' : ' things still to confirm');
      box.appendChild(more);
    }
    return box;
  }

  function pnRenderVerdictHero(parts, fit){
"""

P3B_FIND = """    const split = document.createElement('div');
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
"""
P3B_REPL = """    /* THE META ROW. Garden Room carries maker and price here; the property
       carries where it is and which pathway was assessed. Both come from
       what the journey already established. */
    const meta = document.createElement('div');
    meta.className = 'rh-identity-meta';
    const place = document.createElement('span');
    place.className = 'results-hero-org';
    const placeEl = document.getElementById('propConfirmPlace');
    place.textContent = (placeEl && placeEl.textContent.trim())
      ? placeEl.textContent.trim() : 'Your property';
    meta.appendChild(place);
    const sep = document.createElement('span');
    sep.className = 'rh-identity-sep';
    sep.setAttribute('aria-hidden', 'true');
    sep.textContent = '\\u00b7';
    meta.appendChild(sep);
    const band = document.createElement('span');
    band.className = 'results-hero-org';
    band.textContent = 'Assessed against the 32\\u201345 m\\u00b2 pathway';
    meta.appendChild(band);
    identity.appendChild(meta);

    const split = document.createElement('div');
    split.className = 'rh-split';
    const body = document.createElement('div');
    body.className = 'results-hero-body';
    const factsRow = pnVerdictFactsRow(fit && fit.verdictFacts);
    if (factsRow) body.appendChild(factsRow);
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
    const trust = pnVerdictTrust(fit && fit.verdictKnown,
                                 (fit && fit.verdictOpenCount) || 0);
    if (trust) body.appendChild(trust);
    /* THE BOUNDARY. Its own note, in the shipped note class, so it reads as
       a condition on the finding and never as part of it. */
    if (parts[3]) {
      const bound = document.createElement('p');
      bound.className = 'results-hero-budget-note';
      bound.textContent = parts[3];
      body.appendChild(bound);
    }
    /* THE ONWARD ROUTE, in the shipped secondary-action shape. */
    const secondary = document.createElement('div');
    secondary.className = 'hero-secondary';
    const go = document.createElement('a');
    go.className = 'hero-secondary-link';
    go.href = '#hmrPropertyFit';
    go.textContent = 'See what Atlas checked \\u2192';
    secondary.appendChild(go);
    body.appendChild(secondary);
"""

P3C_FIND = ("      const pnVerdictShown = !pnHasLead\n"
            "        && pnRenderVerdictHero(fit && fit.verdictParts);\n")
P3C_REPL = ("      const pnVerdictShown = !pnHasLead\n"
            "        && pnRenderVerdictHero(fit && fit.verdictParts, fit);\n")


# ---------------------------------------------------------------------------
# P4 · THE SUPPLIER JOIN — the shared trust layer reaches these products
# ---------------------------------------------------------------------------

P4_FIND = ("      additionalHome: p,\n      class3a: p.class3a\n    };\n"
           "    return v;\n")
P4_REPL = """      additionalHome: p,
      class3a: p.class3a,
      /* THE SUPPLIER JOIN. pnSupplierOrgId() reads
         product.organisationEvidence[0].id, and every shared supplier
         surface reads it from there: locality, organisation type, last
         reviewed, the Local Option lens, and pnGoogleIdentity().

         Resolved by EXACT organisation-name match against the suppliers
         detail partition Atlas already publishes. No fuzzy match, no alias
         table, no fallback — an unmatched name yields an absent key and
         every surface takes its existing no-evidence path, which is the
         truthful one. Nothing about the product, its price, its imagery or
         its eligibility is affected either way. */
      organisationEvidence: (function(){
        var id = (typeof pnSupplierOrgIdByName === 'function')
          ? pnSupplierOrgIdByName(p.organisation) : null;
        return id ? [{ id: id, name: p.organisation }] : undefined;
      })()
    };
    return v;
"""

P4B_FIND = "  function pnSupplierOrgId(product){\n"
P4B_REPL = """  /* THE NAME → ORGANISATION-ID RESOLVER.

     The suppliers detail partition is keyed by Airtable record id and each
     record carries its own `name`. Additional Home records carry the
     organisation NAME and no id, so this is the join, and it is deliberately
     strict: exact string match after trimming, first match wins, null
     otherwise. A near-miss must resolve to nothing rather than to the wrong
     supplier's evidence.

     Memoised per partition load, because the AH view is built once per
     candidate on every render. */
  let pnOrgIdByNameCache = null;
  function pnSupplierOrgIdByName(name){
    const want = (typeof name === 'string') ? name.trim() : '';
    if (!want) return null;
    const store = pnDetailParts['suppliers'];
    if (!store) return null;
    if (!pnOrgIdByNameCache || pnOrgIdByNameCache.store !== store) {
      const map = Object.create(null);
      Object.keys(store).forEach(function (id) {
        const rec = store[id];
        const n = rec && typeof rec.name === 'string' ? rec.name.trim() : '';
        if (n && !(n in map)) map[n] = id;
      });
      pnOrgIdByNameCache = { store: store, map: map };
    }
    return pnOrgIdByNameCache.map[want] || null;
  }

  function pnSupplierOrgId(product){
"""


# ---------------------------------------------------------------------------
# P5 · SUN & LIGHT ON THE RESIDENTIAL PATH
# ---------------------------------------------------------------------------

P5_FIND = ("      if (els.resultsSunlightCentrepiece) "
           "els.resultsSunlightCentrepiece.hidden = true;\n"
           "      if (els.resultsReassurance) els.resultsReassurance.hidden = true;\n"
           "    }\n")
P5_REPL = """      if (els.resultsSunlightCentrepiece) els.resultsSunlightCentrepiece.hidden = true;
      if (els.resultsReassurance) els.resultsReassurance.hidden = true;
    }

    /* EXPLORE YOUR PROPERTY IN 3D — A PROPERTY FEATURE, SO IT STAYS.
       Founder decision, 12 October 2026. Measured before reinstating:
       activateResultsSunlightCentrepiece() does not read its argument at all
       — the one line that read chain.inferred is commented out under
       ISSUE 007. What it renders is the homeowner's own geocoded property,
       the sun position calculated for that location, and the season and time
       controls. There is no product datum in it, so withholding it when no
       building has been preferred was withholding a property feature over a
       product distinction.

       Scene 4's reassurance list stays suppressed: buildPrimaryWorthChecking()
       IS product-specific, and the property's own open questions are already
       in the check above. */
    if (pnResidential && !primaryResult && els.resultsSunlightCentrepiece) {
      try {
        activateResultsSunlightCentrepiece(null);
        els.resultsSunlightCentrepiece.hidden = false;
      } catch (e) { /* the panel stays hidden rather than half-built */ }
    }
"""


# ---------------------------------------------------------------------------
# P6 · NATURAL CARD HEIGHTS
# ---------------------------------------------------------------------------

P6_FIND = """  #screen-match-results #altResults{
    grid-template-columns:repeat(auto-fit, minmax(300px, 1fr));
    gap:clamp(20px,2.2vw,28px);
    align-items:stretch;
  }
"""
P6_REPL = """  #screen-match-results #altResults{
    grid-template-columns:repeat(auto-fit, minmax(300px, 1fr));
    gap:clamp(20px,2.2vw,28px);
    align-items:stretch;
  }
  /* NATURAL HEIGHTS WHERE THE SET IS MIXED.

     MEASURED: the panel is 910px, so auto-fit against a 300px minimum gives
     two 441px columns. A 4/3 media well is then 331px tall. `align-items:
     stretch` plus `height:100%` stretched every card in a row to the tallest
     — so a card whose media well is collapsed by the governed no-image rule
     was padded to the height of a card carrying a photograph, and
     `:last-child{margin-top:auto}` put that gap in the middle of the plate.

     Only the stretch is withdrawn, and only in the residential no-lead
     state. The plate, the hairline, the radius, the 4/3 well, the type scale
     and the governed collapse are all untouched; the feet still align within
     a card because the body is still a column with margin-top:auto on its
     last child. Garden Room cannot reach this: #matchPrimary carries
     data-pn-verdict only when the property verdict is the main result. */
  #screen-match-results #matchPrimary[data-pn-verdict="1"] ~ #altResults{
    align-items:start;
  }
  #screen-match-results #matchPrimary[data-pn-verdict="1"] ~ #altResults > *{
    height:auto;
  }
  /* The hero's trailing space was sized for a ten-block product hero. The
     verdict hero is substantial but shorter, so the gap steps down one place
     on the existing scale. No new value. */
  #screen-match-results #matchPrimary[data-pn-verdict="1"]{
    margin-bottom:var(--pn-space-xl);
  }
"""


# ---------------------------------------------------------------------------
# P7 · THE ORPHAN SEPARATOR
# ---------------------------------------------------------------------------

P7_FIND = ("    priceRow.textContent = pnPriceDisplay(product) // BATCH 2 PIECE 1\n"
           "      + (hasValidArea(product.floorAreaM2) ? ' · ' + "
           "product.floorAreaM2 + 'm²' : '')\n"
           "      + (build ? ' · ' + build : '');\n")
P7_REPL = """    /* JOINED, NOT CONCATENATED. The separator was unconditional, so a
       product with no published price rendered "· 33m²" — a leading
       separator with nothing before it. Measured on Van XL, which publishes
       no price. The parts are unchanged; only the join is. */
    priceRow.textContent = [
      pnPriceDisplay(product),
      hasValidArea(product.floorAreaM2) ? (product.floorAreaM2 + 'm\\u00b2') : '',
      build
    ].filter(function (s) { return s; }).join(' \\u00b7 ');
"""


# ---------------------------------------------------------------------------
# P8 · THE REASON LINE AT SENTENCE WEIGHT
# ---------------------------------------------------------------------------

P8_FIND = """  #screen-match-results #altResults .results-gallery-role{
    order:4; margin:0 0 6px; font-size:12px; font-weight:600;
    letter-spacing:.01em; color:var(--pn-stone);
  }
"""
P8_REPL = """  #screen-match-results #altResults .results-gallery-role{
    order:4; margin:0 0 6px; font-size:12px; font-weight:600;
    letter-spacing:.01em; color:var(--pn-stone);
  }
  /* A SENTENCE, SET AS ONE. This slot was written for a short cue — "A
     different maker — Outdoor Living (ModPod)" — and 12px semibold stone
     is right for that. The residential rows carry a full governed sentence,
     which at label weight reads as filler. Same text, same order, same
     colour family, set at the body size it actually is. Residential only. */
  #screen-match-results #matchPrimary[data-pn-verdict="1"] ~ #altResults
    .results-gallery-role{
    font-size:13.5px; font-weight:400; line-height:1.5;
    letter-spacing:normal; color:var(--pn-body); margin:0 0 12px;
  }
"""


# ---------------------------------------------------------------------------
# P10 · THE HERO READS THE GOVERNED IMAGERY READER
# ---------------------------------------------------------------------------

P10_FIND = ("       imageUrl renders it exactly as before. */\n"
            "    if (product.imageUrl) {\n"
            "      mediaCol.appendChild(imgWrap);\n")
P10_REPL = """       imageUrl renders it exactly as before. */
    /* THE GOVERNED READER, NOT THE DEAD FIELD.

       MEASURED: imageUrl is set on 0 of 573 Garden Room products and 0 of
       37 in the legacy pool, so this branch has never once fired and the
       hero has never rendered a photograph. Six Garden Room products DO
       carry an authorised imagery block, and the gallery card finds them
       through the governed reader — the same one checked three lines
       above — the same governed reader. The hero and the card disagreed about what "has a photograph"
       means; they now agree.

       Nothing about rights changes: the governed reader is the gate, and it
       already refuses an asset missing its url, credit, supplier, rights
       record or permitted prefix. A product with no authorised asset takes
       the is-fieldonly path exactly as before. */
    if (pnImg || product.imageUrl) {
      mediaCol.appendChild(imgWrap);
"""


EDITS = [
    ("P1a  verdict copy: state 1 headline and sentence", P1_FIND, P1_REPL),
    ("P1b  verdict copy: states 2, 3 and 4", P1B_FIND, P1B_REPL),
    ("P1c  state 1 carries the boundary", P1C_FIND, P1C_REPL),
    ("P1d  the boundary sentence, declared once", P1D_FIND, P1D_REPL),
    ("P2   the assessment's figures and findings", P2_FIND, P2_REPL),
    ("P3a  the hero's figure row and evidence list", P3_FIND, P3_REPL),
    ("P3b  the hero body, built to density", P3B_FIND, P3B_REPL),
    ("P3c  pass the fit through to the hero", P3C_FIND, P3C_REPL),
    ("P4a  the supplier join on the view", P4_FIND, P4_REPL),
    ("P4b  the name to organisation-id resolver", P4B_FIND, P4B_REPL),
    ("P5   Sun & Light on the residential path", P5_FIND, P5_REPL),
    ("P6   natural card heights and hero spacing", P6_FIND, P6_REPL),
    ("P7   the orphan price separator", P7_FIND, P7_REPL),
    ("P8   the reason line at sentence weight", P8_FIND, P8_REPL),
    ("P10  the hero reads the governed imagery", P10_FIND, P10_REPL),
]


INVARIANTS = [
    # eligibility, rights, price, search — all untouchable
    "publicVisibility", "class3a", "qualification",
    "pnAuthorisedImage(", "pnAttachImageCredit", "PN_IMAGE_FALLBACK_SRC",
    "pn-image-fallback", "attachImageFallback",
    "__PN_PRICE_VIEW__", "pnPriceView",
    "pnCandidateSplit", "pnResidentialCandidateList",
    # Garden Room's ranking and its lead
    "rankArtistStudioCandidates", "selectReasonedAlternatives",
    "scoreTrace", "isPreferred: index === 0",
    # the shared section lists
    "PN_PRODUCT_SECTIONS", "PN_DECISION_SECTIONS",
    "DECISION and PRODUCT section sets overlap",
    # the property assessment
    "hmrFitVerdict", "dhWhy", "dhCalc", "dhCheck",
    "dhNextList", "hmrMatchState",
    # Option B's surface
    "buildResultsGalleryCard", "pnViewOptionButton", "openProductDetail",
    "productDetailContext", "pnNoLeadHere", "PN_AH_COUNT_WORDS",
    "possibilities worth exploring",
    # the verdict hero's own wiring
    "pnLensRailAfterOptions",
    # the Google mechanism, which must not be reimplemented
    "function pnGoogleIdentity(product){",
    "if (g.state !== 'verified') return null;",
    # the guard that must survive
    "originalRecommendation = {",
]

# No ranking, no scoring, no invented reputation, no second trust system.
FORBIDDEN_IN_NEW_CODE = [
    ".sort(", "score", "rank",
    "recommended", "best match", "preferred candidate",
    "rating", "reviews", "stars", "testimonial", "endorse",
    "ahCandidate", "pn-no-lead",
    "createElement('section')",
    "planning permission granted", "approved by", "guaranteed",
]

# Tokens that may GAIN references but must never lose one: this build adds
# links to the property check and scopes new CSS to the verdict attribute.
FLOOR = ["hmrPropertyFit", "data-pn-verdict", "pnAuthorisedImage(",
         "qualification"]

# Classes the new hero markup may use. Each must already have a rule.
REQUIRED_CLASSES = [
    "results-hero-inner", "is-fieldonly", "rh-identity", "rh-identity-meta",
    "rh-identity-sep", "rh-split", "results-hero-body", "results-hero-name",
    "results-hero-org", "results-hero-price-row", "results-hero-area",
    "results-hero-editorial", "results-hero-budget-note", "hm-calm",
    "hero-trust", "hero-trust-title", "hero-trust-list", "hero-tick",
    "hero-trust-more", "hero-secondary", "hero-secondary-link",
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
        tmp = os.path.join(ROOT, ".pn-ap-syntax-%d.mjs" % i)
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

    missing = [c for c in REQUIRED_CLASSES if ("." + c) not in src]
    if missing:
        raise SystemExit("REFUSED: these classes have no existing rule: %s"
                         % missing)

    code = new_code_only()
    bad = [t for t in FORBIDDEN_IN_NEW_CODE if t.lower() in code.lower()]
    if bad:
        raise SystemExit("REFUSED: forbidden token(s) in new CODE: %s"
                         % ", ".join(bad))

    before = {t: src.count(t) for t in INVARIANTS}
    before_style, before_ids = style_bytes(src), element_ids(src)

    out, report = apply_edits(src)

    after = {t: out.count(t) for t in INVARIANTS}
    moved = {k: (before[k], after[k]) for k in INVARIANTS if before[k] != after[k]}
    if moved:
        raise SystemExit("REFUSED: invariant token count moved: %s" % moved)

    lost = {k: (src.count(k), out.count(k)) for k in FLOOR
            if out.count(k) < src.count(k)}
    if lost:
        raise SystemExit("REFUSED: floor token lost a reference: %s" % lost)

    new_ids = element_ids(out) - before_ids
    if new_ids:
        raise SystemExit("REFUSED: new element id(s): %s" % sorted(new_ids))

    css_added = style_bytes(out) - before_style
    # P6 and P8 are the only CSS in this build, and they are scoped to the
    # verdict state. A larger delta means something unscoped got in.
    # Only ADDED selector lines are examined: each REPL reproduces the
    # original rule it follows, and a preserved line is not a new one.
    def added_lines(find, repl):
        keep = set(find.splitlines())
        return [l for l in repl.splitlines() if l not in keep]
    css_new = added_lines(P6_FIND, P6_REPL) + added_lines(P8_FIND, P8_REPL)
    unscoped = [l for l in css_new
                if l.strip().startswith("#screen-match-results")
                and "data-pn-verdict" not in l]
    if unscoped:
        raise SystemExit("REFUSED: unscoped CSS selector(s): %s" % unscoped)

    for t in ("ahCandidateSet", "ahCandidateGrid", "hmrHero"):
        if t in out:
            raise SystemExit("REFUSED: retired surface reintroduced: %s" % t)

    added = out.count("\n") - src.count("\n")

    if mode == "--check":
        print("CHECK ONLY — nothing written.")
        print("  baseline            %s" % base)
        print("  anchors matched     %d of %d, each exactly once"
              % (len(report), len(EDITS)))
        print("  lines added         +%d" % added)
        print("  CSS added           +%d bytes, all scoped to "
              "[data-pn-verdict]" % css_added)
        print("  new element ids     none")
        print("  hero classes        %d, all pre-existing" % len(REQUIRED_CLASSES))
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
    print("  CSS added           +%d bytes, scoped" % css_added)
    print("  your-plot.html      %s -> %s" % (base, sha16(out)))
    print("  revert              python3 atlas-tools/"
          "build-ah-results-parity.py --revert")


if __name__ == "__main__":
    main()
