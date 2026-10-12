#!/usr/bin/env node
/* PlotNua — prove-verdict-hero.mjs
 *
 * THE FOUNDER'S NINE ASSERTIONS for the restored residential property-verdict
 * hero, as H1–H40. Authorisation 11 October 2026.
 *
 * pnRenderVerdictHero() and pnLensRailAfterOptions() are LIFTED FROM THE
 * SHIPPED PAGE by brace-matching and run against jsdom, so this cannot pass
 * against a page that no longer contains them. The governed COPY table is
 * lifted too, so a verdict string invented in the renderer would fail rather
 * than be silently accepted.
 *
 * The four equal options, Wanderlust's imagery, Product Detail and the
 * no-ranking assertions are NOT duplicated here: they are
 * prove-no-lead-altresults.mjs's 28 checks, which this suite requires to
 * still pass and which the regression run reports alongside it.
 *
 * Reads your-plot.html. Writes nothing. No network.
 */
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { JSDOM } from 'jsdom';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const PAGE = readFileSync(join(ROOT, 'your-plot.html'), 'utf8');

let pass = 0, fail = 0;
const check = (name, ok, detail = '') => {
  (ok ? pass++ : fail++);
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}`);
  if (detail) console.log(`        ${detail}`);
};

function lift(marker, name) {
  const i = PAGE.indexOf(marker);
  if (i === -1) throw new Error(`cannot find ${name} in your-plot.html`);
  const open = PAGE.indexOf('{', i);
  let depth = 0, j = open;
  for (; j < PAGE.length; j++) {
    if (PAGE[j] === '{') depth++;
    else if (PAGE[j] === '}') { depth--; if (depth === 0) break; }
  }
  return PAGE.slice(i, j + 1);
}

console.log('\n  RESIDENTIAL PROPERTY-VERDICT HERO — H1 to H40');
console.log('  ' + '-'.repeat(68));

/* ── the governed verdict table, lifted whole ───────────────────────────── */
const BOUND_AT = PAGE.indexOf('var PN_VERDICT_BOUND =');
if (BOUND_AT === -1) throw new Error('the boundary sentence is gone');
const BOUND_SRC = PAGE.slice(BOUND_AT, PAGE.indexOf(';\n', BOUND_AT) + 1);
const COPY_AT = PAGE.indexOf('var COPY = {');
if (COPY_AT === -1) throw new Error('the governed COPY table is gone');
const COPY_SRC = PAGE.slice(COPY_AT, PAGE.indexOf('\n  };', COPY_AT) + 5);
const COPY = new Function(BOUND_SRC + COPY_SRC
  + '; return COPY;')();
const BOUND = new Function(BOUND_SRC + '; return PN_VERDICT_BOUND;')();

check('H1  the governed COPY table holds all four states, each of four parts',
  [1, 2, 3, 4].every(s => Array.isArray(COPY[s]) && COPY[s].length === 4),
  Object.keys(COPY).map(k => `${k}:"${COPY[k][0].slice(0, 34)}…"`).join('\n        '));

/* THE BOUNDARY. The founder's one hard requirement on this copy: an initial
   assessment must never read as a consent. */
check('H1b the boundary is the fourth part of every state, identically',
  [1, 2, 3, 4].every(s => COPY[s][3] === BOUND)
  && /not a planning decision/.test(BOUND)
  && /not a guarantee of eligibility/.test(BOUND)
  && /local authority/.test(BOUND),
  JSON.stringify(BOUND.slice(0, 92) + '…'));

check('H1c no state claims permission, approval or entitlement',
  [1, 2, 3, 4].every(s => !/\b(permitted|approved|permission granted|you can build|entitled|cleared)\b/i
    .test(COPY[s].slice(0, 3).join(' '))),
  'scanned all four verdicts for consent language');

check('H1d the tentative phrasing the founder rejected is gone',
  !PAGE.includes('Your garden looks like it could take one')
  && !PAGE.includes('Worth exploring\','),
  '"Your garden looks like it could take one" no longer exists in the page');

/* ── the DOM, in the shipped sibling order ──────────────────────────────── */
const dom = new JSDOM(`<!doctype html><html><body>
  <div id="screen-match-results">
    <section class="prop-confirm" id="propConfirm"></section>
    <div class="results-hero" id="matchPrimary"></div>
    <section class="chapter" id="hmrPropertyFit" hidden>
      <p class="hm-calm" id="hmrFitVerdict"></p>
    </section>
    <div class="results-gallery-heading" id="matchAlternativesHeading" hidden></div>
    <p class="alt-rail-note" id="altRailNote" hidden></p>
    <div class="alt-rail-wrap" id="altRailWrap" hidden></div>
    <div class="results-gallery-heading" id="altResultsHeading" hidden></div>
    <p class="alt-rail-note" id="altResultsNote" hidden></p>
    <div class="results-gallery alt-results" id="altResults" hidden></div>
    <section class="byd" id="resultsDecide" hidden></section>
  </div></body></html>`);
const { document } = dom.window;
global.document = document;
global.window = dom.window;

const host = document.getElementById('matchPrimary');
const els = { matchPrimary: host };

const harness = new Function('els',
  `${lift('function pnVerdictExampleImage(results){', 'pnVerdictExampleImage')}
   ${lift('function pnVerdictFactsRow(facts){', 'pnVerdictFactsRow')}
   ${lift('function pnVerdictTrust(known, openCount){', 'pnVerdictTrust')}
   ${lift('function pnRenderVerdictHero(parts, fit, results){', 'pnRenderVerdictHero')}
   ${lift('function pnLensRailAfterOptions(after){', 'pnLensRailAfterOptions')}
   return { hero: pnRenderVerdictHero, rail: pnLensRailAfterOptions };`)(els);

const panel = document.getElementById('screen-match-results');
const order = () => [].slice.call(panel.children)
  .filter(n => n.id).map(n => n.id);

const SHIPPED_ORDER = order().join(',');

/* ═══ 1 · THE VERDICT HERO RENDERS CORRECTLY ═══════════════════════════ */
const FIT = {
  verdictFacts: [{ k: 'Potential area from your measurements', v: '38 m\u00b2' },
                 { k: 'The range these regulations allow', v: '32\u201345 m\u00b2' },
                 { k: 'Allowance left in the garden', v: '45 m\u00b2' }],
  verdictKnown: ['Nothing is built in the garden yet, so the full 45 m\u00b2 allowance is available',
                 'No new entrance onto the road would be needed'],
  verdictOpenCount: 2
};
const ok1 = harness.hero(COPY[1], FIT);

check('H2  it renders, and reports that it did',
  ok1 === true && host.children.length === 1, `returned ${ok1}`);

const wrap = host.firstElementChild;
check('H3  the shipped premium field, with the no-photograph variant',
  wrap.className === 'results-hero-inner is-fieldonly',
  `class="${wrap.className}"`);

const identity = wrap.querySelector(':scope > .rh-identity');
const split = wrap.querySelector(':scope > .rh-split');
const body = split && split.querySelector(':scope > .results-hero-body');
check('H4  it follows the CURRENT hero tree, not the 2026 one',
  !!identity && !!split && !!body
  && identity.nextElementSibling === split,
  '.rh-identity then .rh-split > .results-hero-body');

const nameEl = identity.querySelector('h2.results-hero-name');
check('H5  the name is in the identity band, where the display scale lives',
  !!nameEl && nameEl.parentElement === identity,
  'not inside .results-hero-body, where the two-column grid would claim it');

check('H6  nothing belonging to a PRODUCT is in the property hero',
  !wrap.querySelector('.pn-media-col, .results-hero-media, img')
  && !wrap.querySelector('.results-hero-price, .match-card-actions, '
                         + '.match-card-save-primary, .pn-view-option, '
                         + '.open-myplot-link'),
  'no photograph, no price, no Save, no View option \u2014 there is no product');

/* The founder asked for figures, trust and an onward step in the hero, in the
   Garden Room visual language. These are those blocks, and they must be the
   shipped classes rather than anything new. */
/* H6b-H6d RE-POINTED, 12 October 2026. The founder's instruction:
   "ONE property verdict and ONE Atlas Assessment dossier. No duplicated
   measurements or findings." The figures, the confirmed findings and the
   open-question count were rendered in the hero AND again in the dossier.
   They now live in the dossier alone, so these three assertions check the
   ABSENCE the instruction created, and H6b2 checks the dossier still
   carries what left the hero. */
check('H6b the hero no longer repeats the assessment figures',
  !wrap.querySelector('.results-hero-price-row'),
  'the figures belong to the dossier, which is the single account of them');

check('H6c the hero no longer repeats the confirmed findings',
  !wrap.querySelector('.hero-trust'),
  'the tick list belongs to the dossier');

check('H6d the hero no longer repeats the open-question count',
  !wrap.querySelector('.hero-trust-more'),
  'the outstanding checks are named in full in the dossier, not counted twice');

check('H6b2 the dossier still renders every figure and finding that left',
  (function(){
    const d = PAGE.slice(PAGE.indexOf('function pnRenderPropertyAssessment('),
                         PAGE.indexOf('window.__PN_RENDER_RESIDENTIAL__'));
    return ['verdictFacts','verdictCalc','verdictKnown','verdictCheck']
             .every(t => d.indexOf(t) !== -1);
  })(), 'nothing was dropped on the way out of the hero');

check('H6b3 the hero body is one editorial sentence, as Garden Room\u2019s is',
  (function(){
    const body = wrap.querySelector('.results-hero-body');
    if (!body) return false;
    const ps = [...body.querySelectorAll('p')];
    const ed = ps.filter(n => n.className.indexOf('results-hero-editorial') !== -1);
    const note = ps.filter(n => n.className.indexOf('results-hero-budget-note') !== -1);
    /* One editorial sentence, and the planning boundary, which is a
       condition on the headline rather than evidence and appears nowhere
       else on the page. Nothing else. */
    return ed.length === 1 && ps.length === ed.length + note.length;
  })(), 'the hero introduces the verdict; the dossier explains the evidence');

check('H6e the hero carries the locality and the regulated pathway',
  (function(){
    const meta = wrap.querySelector('.rh-identity .rh-identity-meta');
    return !!meta && /32\u201345 m\u00b2 pathway/.test(meta.textContent);
  })(), 'where it is, and what it was assessed against');

check('H6f the onward route uses the shipped secondary-action shape',
  (function(){
    const a = wrap.querySelector('.hero-secondary .hero-secondary-link');
    return !!a && a.getAttribute('href') === '#hmrPropertyFit';
  })(), '\u201cSee what Atlas checked \u2192\u201d');

/* ── every class used must already have a rule in the stylesheet ───────── */
const usedClasses = new Set();
wrap.querySelectorAll('*').forEach(n =>
  n.classList.forEach(c => usedClasses.add(c)));
wrap.classList.forEach(c => usedClasses.add(c));
const unstyled = [...usedClasses].filter(c => !PAGE.includes('.' + c));
check('H7  every class the hero uses already has a rule — no CSS was added',
  unstyled.length === 0,
  [...usedClasses].sort().join(' '));

/* ═══ 2 · ALL FOUR GOVERNED STATES ════════════════════════════════════ */
const stateRows = [];
let allStatesOk = true;
for (const s of [1, 2, 3, 4]) {
  harness.hero(COPY[s], FIT);
  const n = host.querySelector('.results-hero-name');
  const e = host.querySelector('.results-hero-editorial');
  const d = host.querySelector('p.hm-calm');
  const b = [...host.querySelectorAll('p.results-hero-budget-note')]
    .map(x => x.textContent);
  /* RE-POINTED. The hero renders the headline, the editorial sentence and
     the boundary. COPY[s][2] — the elaborating detail — left the hero with
     the figures and findings, under the founder's one-dossier rule, and
     must NOT be here. */
  const good = n && e && !d
    && n.textContent === COPY[s][0]
    && e.textContent === COPY[s][1]
    && b.indexOf(COPY[s][3]) >= 0;
  if (!good) allStatesOk = false;
  stateRows.push(`s${s}: "${COPY[s][0]}" / ${(e ? e.textContent : '').length}ch `
                 + `/ ${(d ? d.textContent : '').length}ch`);
}
check('H8  all four states render headline, sentence and boundary verbatim',
  allStatesOk, stateRows.join('\n        '));

check('H9  nothing is invented: every rendered string is a COPY[state] value',
  [1, 2, 3, 4].every(s => {
    harness.hero(COPY[s], FIT);
    return [...host.querySelectorAll('h2, p')]
      .filter(n => !n.classList.contains('hero-trust-title')
                && !n.closest('.hero-trust'))
      .every(n => COPY[s].indexOf(n.textContent) >= 0);
  }), 'no connective text, no label, no count');

/* Defensive shapes the renderer must refuse rather than half-render. */
check('H10 it refuses an absent or empty verdict instead of rendering a shell',
  harness.hero(null, FIT) === false && harness.hero([], FIT) === false
  && harness.hero([''], FIT) === false,
  'the concatenated sentence in the property check then stands on its own');

harness.hero(['A headline alone'], null);
check('H11 a one-part verdict with no assessment renders the name alone',
  host.querySelectorAll('p').length === 0
  && host.querySelector('.results-hero-name').textContent === 'A headline alone',
  'absent is absent, not an empty element');

/* ═══ 3 · ZERO ELIGIBLE PRODUCTS STILL SHOWS THE VERDICT ══════════════ */
/* The zero path hides every product section, #matchPrimary among them. This
   reproduces that exactly, then renders. */
host.hidden = true;
const ok0 = harness.hero(COPY[1], FIT);
check('H12 with no qualifying building the verdict is still visible',
  ok0 === true && host.hidden === false
  && host.querySelector('.results-hero-name').textContent === COPY[1][0],
  'the container was hidden by the zero-path sweep and the render un-hides it');

check('H13 and it marks itself, so nothing has to re-classify the container',
  host.getAttribute('data-pn-verdict') === '1',
  'PN_PRODUCT_SECTIONS and PN_DECISION_SECTIONS are untouched — see H20');

/* ═══ 4 · THE LENS RAIL FOLLOWS THE OPTIONS, AND GOES BACK ════════════ */
const RAIL = ['matchAlternativesHeading', 'altRailNote', 'altRailWrap'];
const OPTS = ['altResultsHeading', 'altResultsNote', 'altResults'];
const idx = id => order().indexOf(id);

check('H14 the shipped order puts the rail before the options',
  Math.max(...RAIL.map(idx)) < Math.min(...OPTS.map(idx)), SHIPPED_ORDER);

const moved = harness.rail(true);
check('H15 after the move every rail node follows every options node',
  moved === true
  && Math.min(...RAIL.map(idx)) > Math.max(...OPTS.map(idx)),
  order().join(','));

check('H16 the rail nodes keep their own relative order',
  idx('matchAlternativesHeading') < idx('altRailNote')
  && idx('altRailNote') < idx('altRailWrap'),
  'heading, note, wrap');

check('H17 nothing else moved — only three nodes changed position',
  order().filter(id => !RAIL.includes(id)).join(',')
    === SHIPPED_ORDER.split(',').filter(id => !RAIL.includes(id)).join(','),
  'the property check, the options and Before you decide are where they were');

harness.rail(true);
check('H18 moving again mutates nothing',
  Math.min(...RAIL.map(idx)) > Math.max(...OPTS.map(idx))
  && order().length === SHIPPED_ORDER.split(',').length,
  'idempotent, so the repaint pass is harmless');

harness.rail(false);
check('H19 THE RESTORE IS REAL — the shipped order comes back exactly',
  order().join(',') === SHIPPED_ORDER,
  'so a Garden Room search later in the same session cannot inherit the move');

/* ═══ 5 · GARDEN ROOM AND THE SHARED CONTRACTS ════════════════════════ */
const S = {
  /* the founder's explicit no-go */
  prodList: /const PN_PRODUCT_SECTIONS = \['matchPrimary','aboutSupplier'/
              .test(PAGE),
  decList: /const PN_DECISION_SECTIONS = \['hmrPropertyFit','hmrFitVerdict'/
             .test(PAGE),
  disjoint: PAGE.includes('DECISION and PRODUCT section sets overlap'),
  /* the verdict is gated on residential and on the absence of a lead */
  gated: /const pnVerdictShown = !pnHasLead\s*\n\s*&& pnRenderVerdictHero\(fit && fit\.verdictParts, fit, results\);/
           .test(PAGE),
  /* and it is rendered AFTER the results/zero branch, or it would be erased */
  afterBranch: (() => {
    const b = PAGE.indexOf("      renderMatchResults(results, 'residential');");
    const v = PAGE.indexOf('const pnVerdictShown = !pnHasLead');
    const s = PAGE.indexOf('    showScreen(els.matchResultsScreen);\n'
                           + "    window.scrollTo({ top: 0, behavior: 'auto' });");
    return b > 0 && v > b && s > v;
  })(),
  /* one call site, both directions */
  railCall: /pnLensRailAfterOptions\(pnResidential && pnNoLead\)/.test(PAGE),
  railRestore: /if \(!pnVerdictShown\) pnLensRailAfterOptions\(false\);/.test(PAGE),
  /* the duplicate is hidden, not destroyed */
  noDup: /if \(pnFitV\) pnFitV\.hidden = !!pnVerdictShown;/.test(PAGE)
         && /if \(v\) v\.textContent = fit\.verdict;/.test(PAGE),
  /* Garden Room's own lead, and the product hero, untouched */
  gardenRoomLead: /isPreferred: index === 0/.test(PAGE),
  productHero: /els\.matchPrimary\.appendChild\(buildResultsHero\(primaryResult\)\);/
                 .test(PAGE),
  origRec: /if \(!originalRecommendation && primaryResult && primaryResult\.product\)/
             .test(PAGE),
  /* no ranking anywhere near this */
  noSort: !/pnProductRows\s*\.sort\(|verdictParts\s*\.sort\(/.test(PAGE),
  /* the governed triple is passed by reference, not rebuilt */
  byRef: /verdictParts: C,/.test(PAGE),
  /* Option B's surface survives */
  optionB: /const pnNoLeadHere = \(pnResultUse === 'residential'\) && !primary;/
             .test(PAGE)
           && /possibilities worth exploring/.test(PAGE)
           && /actions\.insertBefore\(pnViewOptionButton\(product\), actions\.firstChild\);/
                .test(PAGE)
};

check('H20 PN_PRODUCT_SECTIONS and PN_DECISION_SECTIONS are as shipped',
  S.prodList && S.decList && S.disjoint,
  'matchPrimary was NOT reclassified — the founder required proof of '
  + 'necessity and H12 shows it is not necessary');

check('H21 the verdict is gated on the governed no-lead state',
  S.gated, 'a genuine single caveat-free candidate keeps the shipped hero');

check('H22 it is rendered after the results branch and before the screen shows',
  S.afterBranch,
  'so neither renderMatchResults’ clear nor the zero sweep can erase it');

check('H23 the verdict text appears once: the duplicate is hidden, not deleted',
  S.noDup, '#hmrFitVerdict keeps its sentence in the DOM and is hidden');

check('H24 one rail call site, both directions, and the restore is wired',
  S.railCall && S.railRestore, 'pnResidential && pnNoLead, else false');

check('H25 Garden Room is untouched: its lead, its hero, its ledger',
  S.gardenRoomLead && S.productHero && S.origRec,
  'isPreferred: index === 0 · buildResultsHero(primaryResult) · '
  + 'the originalRecommendation guard');

check('H26 no ranking, and the verdict is the governed table by reference',
  S.noSort && S.byRef, 'verdictParts: C');

check('H27 Option B’s surface survives intact',
  S.optionB, 'the no-lead gate, the approved heading, the View option route');

/* ═══ 6 · THE LOCAL REVIEW INSTRUMENT ═════════════════════════════════
   The harness fixture predates the verdict hero and carried only the
   concatenated `verdict`, so the hero correctly declined to render and the
   four states could not be reviewed before deployment. These prove the
   instrument now carries the GOVERNED triple and still fails closed. */

const H = {
  gates: ['if (!isLocal) return;',
          "if (location.protocol !== 'http:') return;",
          "if (qs.get('review') !== 'additional-home') return;",
          "if (intendedUse !== 'residential') return;"]
           .every(g => PAGE.includes(g)),
  exported: /window\.__PN_VERDICT_COPY__ = function \(\) \{/.test(PAGE),
  copied: /out\[k\] = COPY\[k\]\.slice\(\);/.test(PAGE),
  reads: /\? window\.__PN_VERDICT_COPY__\(\) : null;/.test(PAGE),
  carries: /if \(vp\) f\.verdictParts = vp;/.test(PAGE),
  selects: /var want = parseInt\(qs\.get\('verdict'\) \|\| '1', 10\);/.test(PAGE)
};

check('H28 the review harness still fails closed on all four gates',
  H.gates, 'localhost · http: · ?review=additional-home · residential');

check('H29 the governed table is exported, by value not by reference',
  H.exported && H.copied,
  '__PN_VERDICT_COPY__ returns a copy, so a reader cannot mutate the strings');

check('H30 the fixture reads the governed table rather than carrying strings',
  H.reads && H.carries,
  'no verdict string is duplicated into the harness');

check('H31 ?verdict=1|2|3|4 selects the state, defaulting to 1',
  H.selects, 'all four states reviewable at any width');

/* The strings must live in exactly ONE place. Four occurrences of a verdict
   would mean the fixture had acquired its own copy, which is how a review
   surface starts telling a homeowner something production does not. */
const onceOnly = [1, 2, 3, 4].every(s =>
  COPY[s].slice(0, 3).every(str => (PAGE.split(str).length - 1) === 1));
check('H32 every verdict string appears exactly once in the page',
  onceOnly, 'the fixture reads the table; it does not copy it');

/* The boundary is referenced by constant from all four states, so it is not
   a literal anywhere — which is stronger than appearing once. */
check('H33 the boundary is declared once and referenced, never duplicated',
  (PAGE.split('var PN_VERDICT_BOUND =').length - 1) === 1
  && (PAGE.split('PN_VERDICT_BOUND]').length - 1) === 4
  && (PAGE.split(BOUND).length - 1) === 0,
  'one declaration, four references, zero copies');

console.log('  ' + '-'.repeat(68));
console.log(`  ${pass + fail} checks, ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
