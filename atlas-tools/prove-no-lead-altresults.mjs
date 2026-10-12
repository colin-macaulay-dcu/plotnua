#!/usr/bin/env node
/* PlotNua — prove-no-lead-altresults.mjs
 *
 * OPTION B. Founder decision, 11 October 2026: Additional Home presents its
 * qualifying products through the ESTABLISHED Garden Room components, with no
 * separate residential Results architecture.
 *
 * B1–B22. Every function under test is LIFTED FROM THE SHIPPED PAGE by
 * brace-matching and evaluated as source, so this suite cannot pass against a
 * page that no longer contains them. The DOM is jsdom. Only leaf helpers that
 * reach the network, the rights manifest or the price contract are supplied,
 * and each is supplied so BOTH of its branches can be driven — an authorised
 * image and no image, a lead and no lead.
 *
 * This suite REPLACES prove-no-lead-equality.mjs, whose surface
 * (#ahCandidateSet / #ahCandidateGrid and its own card and detail panel) the
 * founder retired as duplication. The retired suite is preserved at
 * governance/retired/prove-no-lead-equality.mjs.retired.
 *
 * Reads your-plot.html and the committed artefact. Writes nothing. No network.
 */
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { JSDOM } from 'jsdom';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const PAGE = readFileSync(join(ROOT, 'your-plot.html'), 'utf8');
const UNIVERSE = JSON.parse(
  readFileSync(join(ROOT, 'additional-home-universe-v1.json'), 'utf8'));

let pass = 0, fail = 0;
const check = (name, ok, detail = '') => {
  (ok ? pass++ : fail++);
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}`);
  if (detail) console.log(`        ${detail}`);
};

/* `bodyAfter` exists because buildResultsGalleryCard destructures its
   parameters: brace-matching from the first `{` after the name would return
   the parameter object, not the body. */
function lift(marker, name, bodyAfter) {
  const i = PAGE.indexOf(marker);
  if (i === -1) throw new Error(`cannot find ${name} in your-plot.html`);
  const open = bodyAfter
    ? PAGE.indexOf('{', PAGE.indexOf(bodyAfter, i) + bodyAfter.length - 1)
    : PAGE.indexOf('{', i);
  let depth = 0, j = open;
  for (; j < PAGE.length; j++) {
    if (PAGE[j] === '{') depth++;
    else if (PAGE[j] === '}') { depth--; if (depth === 0) break; }
  }
  return PAGE.slice(i, j + 1);
}

console.log('\n  OPTION B — ADDITIONAL HOME THROUGH THE GARDEN ROOM COMPONENTS');
console.log('  ' + '-'.repeat(68));

/* ── the DOM the shipped renderer expects, and nothing more ─────────────── */
const dom = new JSDOM(`<!doctype html><html><body>
  <div id="screen-match-results">
    <div class="results-hero" id="matchPrimary"></div>
    <div class="results-gallery-heading" id="altResultsHeading" hidden>Other options worth considering</div>
    <p class="alt-rail-note" id="altResultsNote" hidden></p>
    <div class="results-gallery alt-results" id="altResults" hidden></div>
  </div></body></html>`);
const { document } = dom.window;
global.document = document;
global.window = dom.window;

const host = document.getElementById('altResults');
const head = document.getElementById('altResultsHeading');
const note = document.getElementById('altResultsNote');

/* ── the real rows, built from the committed artefact ───────────────────── */
const PLACEHOLDER = 'data:image/svg+xml;PLACEHOLDER';
const CODES = ['PROD-000425', 'PROD-000437', 'PROD-000457', 'PROD-000523'];

const rowsFor = (preferredIndex = -1) => UNIVERSE.products
  .filter(p => (p.class3a || {}).state === 'CANDIDATE')
  .map((p, i) => ({
    role: 'residential',
    product: {
      id: p.id, productCode: p.productCode, name: p.productName,
      organisation: p.organisation, price: p.price, imagery: p.imagery,
      imagerySet: p.imagerySet, area: p.area, productUrl: p.productUrl
    },
    ctx: {
      discoveryContext: 'residential', intendedUse: 'residential',
      isPreferred: i === preferredIndex,
      leadReason: 'Atlas has confirmed this is a habitable building in the '
                  + 'Class 3A floor-area band.',
      residentialTradeOff: p.productCode === 'PROD-000437'
        ? 'Its floor area sits at the very top of the range.' : null,
      residentialKnown: ['Verified internal floor area'],
      residentialOpen: ['Site access'],
      decisionProfile: null, scoreTrace: null
    }
  }));

/* ── leaf helpers, both branches drivable ───────────────────────────────── */
const detailOpened = [];
const deps = {
  attachImageFallback(img) { img.dataset.pnFallbackWired = '1'; },
  PN_IMAGE_FALLBACK_SRC: PLACEHOLDER,
  /* THE GOVERNED READER, honestly modelled: an image only where the artefact
     actually carries one with a credit. Wanderlust has one; the other three
     candidates have none, which is the real population today. */
  pnAuthorisedImage(product) {
    const im = product && product.imagery;
    return (im && im.url && im.credit) ? im : null;
  },
  pnAttachImageCredit(wrap, im) {
    const p = document.createElement('p');
    p.className = 'pn-image-credit';
    p.textContent = im.credit + (im.linkBack ? ' · ' + im.linkBack : '');
    wrap.appendChild(p);
  },
  pnPriceDisplay(product) {
    const a = product && product.price && product.price.amount;
    return a == null ? '' : '€' + Math.round(a).toLocaleString('en-IE');
  },
  pnPriceView(product) {
    const a = product && product.price && product.price.amount;
    return { known: a != null };
  },
  pnSupplierOrgType() { return null; },
  irishRouteNoteText() { return null; },
  buildMatchReasons() { return []; },
  buildAlternativeRationale() { return ''; },
  /* A real element pair: the card appends both, and a null would be a
     different card from the shipped one. */
  buildSaveActions() {
    const a = document.createElement('div');
    a.className = 'match-card-actions';
    const l = document.createElement('a');
    l.className = 'open-myplot-link';
    return { actions: a, openMyPlotLink: l };
  },
  raCompareControl() { return null; },
  /* The real Map: the card registers each product's context for Option
     Detail, and B18 reads it back. */
  productDetailContext: new Map(),
  AS_BUDGET_LABEL: {},
  /* openProductDetail is the EXISTING navigation. Recorded, not faked away:
     B16 proves the control actually calls it with the right product. */
  openProductDetail(id, from) { detailOpened.push(id); },
  hasValidArea: null,            // lifted below
  /* renderAltResults' own leaves. */
  bydByoNode() { return null; },
  pnHomeownerCounty() { return null; },
  raLocalResolve() { return null; },
  altResultsCtx(row) { return row.ctx; },
  altReasonForDisplay() { return 'cheaper than the recommendation'; },
  altTradeOffForDisplay() { return ''; },
  altTradeOffRepeatsPrice() { return false; },
  altPricedPreference(c, p, picks) { return picks; },
  selectReasonedAlternatives(c) {
    return c.map(r => Object.assign({}, r, { __alt: {
      dimension: 'garden-room', reason: '', tradeOff: '', primaryName: '' } }));
  },
  decisionProfile: null
};
delete deps.hasValidArea;

/* ── the count vocabulary, lifted intact ────────────────────────────────── */
const CW_AT = PAGE.indexOf('const PN_AH_COUNT_WORDS');
if (CW_AT === -1) throw new Error('PN_AH_COUNT_WORDS is not in your-plot.html');
const CW_SRC = PAGE.slice(CW_AT, PAGE.indexOf(';', CW_AT) + 1);
check('B1  the governed count words are present and lifted intact',
  /'four'/.test(CW_SRC) && /'ten'\]/.test(CW_SRC),
  CW_SRC.replace(/\s+/g, ' ').slice(0, 96));

/* ── lift the shipped builders ──────────────────────────────────────────── */
const SRC = [
  lift('function hasValidArea(value){', 'hasValidArea'),
  lift('function pnViewOptionButton(product){', 'pnViewOptionButton'),
  lift('function buildResultsGalleryCard(', 'buildResultsGalleryCard',
       '}, primaryResult)'),
  lift('function renderAltResults(primaryResult, alternativeResults){',
       'renderAltResults')
].join('\n\n');

const harness = new Function(
  ...Object.keys(deps), 'els',
  `${CW_SRC}
   let pnResultUse = 'garden-room';
   ${SRC}
   return {
     setUse(u){ pnResultUse = u; },
     render: renderAltResults,
     card: buildResultsGalleryCard
   };`
)(...Object.values(deps), { matchPrimary: document.getElementById('matchPrimary') });

const codesOf = () => [].slice.call(host.children)
  .filter(c => c.classList.contains('results-gallery-card'))
  .map(c => {
    const n = c.querySelector('.results-gallery-name');
    const name = n ? n.textContent : '';
    const m = UNIVERSE.products.find(p => p.productName === name);
    return m ? m.productCode : '?';
  });

/* ═══ THE NO-LEAD RENDER ════════════════════════════════════════════════ */
harness.setUse('residential');
const rows = rowsFor(-1);
const n = harness.render(null, rows);

check('B2  the grid renders without a primary, residential no-lead',
  n === rows.length && host.hidden === false,
  `${rows.length} qualifying rows, ${n} cards rendered, host.hidden=${host.hidden}`);

check('B3  all four candidates are on the surface — none lost',
  codesOf().length === 4, codesOf().join(', '));

check('B4  catalogue order preserved exactly — no sort introduced',
  codesOf().join(',') === CODES.join(','), codesOf().join(', '));

const gridHtml = host.innerHTML;
check('B5  no card carries a preferred, recommended or best marker',
  !/recommend|preferred|best match|our pick|start here|winner|top choice/i
    .test(gridHtml) && rows.every(r => r.ctx.isPreferred === false),
  'scanned the rendered markup for every preference word');

check('B6  the heading is the founder-approved string, with the real count',
  head.textContent === '4 possibilities worth exploring' && head.hidden === false,
  JSON.stringify(head.textContent));

check('B7  the explanation is the founder-approved sentence, verbatim',
  note.textContent === 'Atlas has identified four buildings that meet the '
    + 'current assessment criteria. None has been established as a better '
    + 'match for your property.',
  JSON.stringify(note.textContent));

check('B8  neither string is stated relative to a primary',
  !/alternative/i.test(note.textContent)
  && !/other options/i.test(head.textContent),
  'nothing on this surface claims to be second to anything');

/* ── imagery: the Garden Room behaviour, unchanged ──────────────────────── */
const cards = [].slice.call(host.children)
  .filter(c => c.classList.contains('results-gallery-card'));
const wanderlust = cards[3];
const wImg = wanderlust.querySelector('.results-gallery-media img');
const wCredit = wanderlust.querySelector('.pn-image-credit');

check('B9  the one authorised image renders from its governed url',
  !!wImg && /biobuilds\.com/.test(wImg.getAttribute('src'))
  && !wImg.classList.contains('pn-image-fallback'),
  wImg ? wImg.getAttribute('src').slice(0, 72) : 'no img');

check('B10 it carries the credit and the required link-back',
  !!wCredit && /BIOBUILDS/.test(wCredit.textContent)
  && /biobuilds\.com/.test(wCredit.textContent),
  wCredit ? wCredit.textContent.slice(0, 80) : 'no credit node');

const imageless = [cards[0], cards[1], cards[2]];
check('B11 the three candidates with no grant fall to the branded placeholder',
  imageless.every(c => {
    const i = c.querySelector('.results-gallery-media img');
    return i && i.classList.contains('pn-image-fallback')
             && i.getAttribute('src') === PLACEHOLDER;
  }), 'PROD-000425, PROD-000437, PROD-000457');

check('B12 none of them carries a credit it has no grant for',
  imageless.every(c => !c.querySelector('.pn-image-credit')),
  'attribution appears only where a grant exists');

/* THE PLACEHOLDER TREATMENT IS THE SHIPPED ONE. Option B adds no CSS; the
   collapse rule already existed on this surface and is why it does not. */
check('B13 the shipped collapse rule owns the empty frame, scoped to #altResults',
  /#screen-match-results #altResults \.results-gallery-media:has\(img\.pn-image-fallback\)\{\s*display:none;/
    .test(PAGE),
  'no new placeholder treatment was introduced');

check('B14 no .pn-no-lead CSS scope exists anywhere in the page',
  !PAGE.includes('pn-no-lead'),
  'the retired 17-rule scope is gone, not renamed');

check('B15 the retired duplicate surface is absent from the page',
  !/ahCandidateSet|ahCandidateGrid|ahRenderDetail|ahSelectCandidate|ahCandidateCard/
    .test(PAGE),
  'no second grid, no second card builder, no inline detail panel');

/* ── the route to Option Detail ─────────────────────────────────────────── */
const viewButtons = cards.map(c => c.querySelector('.pn-view-option'));
check('B16 every card offers the existing View option control',
  viewButtons.every(b => b && b.textContent.trim() === 'View option →'),
  `${viewButtons.filter(Boolean).length} of ${cards.length} cards`);

viewButtons[3].dispatchEvent(new dom.window.Event('click'));
const wId = UNIVERSE.products.find(p => p.productCode === 'PROD-000523').id;
check('B17 it calls the existing openProductDetail() with that product',
  detailOpened.length === 1 && detailOpened[0] === wId,
  `openProductDetail(${detailOpened[0]})`);

check('B18 every candidate is registered for Option Detail',
  CODES.every(code => {
    const p = UNIVERSE.products.find(x => x.productCode === code);
    return deps.productDetailContext.has(p.id);
  }), `${deps.productDetailContext.size} products registered`);

/* ═══ THE GENUINE-LEAD RENDER — GARDEN ROOM MUST BE UNTOUCHED ═══════════ */
harness.setUse('garden-room');
const gr = rowsFor(0);
const grPrimary = gr[0];
const grAlts = gr.slice(1);
const grN = harness.render(grPrimary, grAlts);

check('B19 with a primary the surface returns to the shipped heading',
  head.textContent === 'Other options worth considering',
  JSON.stringify(head.textContent));

check('B20 and to the shipped relative note',
  note.textContent === 'Three alternatives Atlas found in the same search.',
  JSON.stringify(note.textContent));

check('B21 no card offers View option when a primary exists',
  grN === 3 && [].slice.call(host.children)
    .filter(c => c.classList.contains('results-gallery-card'))
    .every(c => !c.querySelector('.pn-view-option')),
  'the Y1 placement decision still stands wherever a hero carries the journey');

/* ── source assertions: the invariants Option B must not have moved ─────── */
const S = {
  lead: /const pnNoLead = pnResidential && !\(pnFirstRow && pnFirstRow\.ctx/
          .test(PAGE),
  primary: /const primaryResult = pnNoLead \? null : pnFirstRow;/.test(PAGE),
  rows: /const pnProductRows = pnNoLead \? results : alternativeResults;/.test(PAGE),
  origRec: /if \(!originalRecommendation && primaryResult && primaryResult\.product\)/
             .test(PAGE),
  heroGate: /if \(primaryResult\) \{\s*\n\s*\/\/ SCENE 1\s*\n\s*els\.matchPrimary\.appendChild\(buildResultsHero\(primaryResult\)\);/
              .test(PAGE),
  gardenRoom: /isPreferred: index === 0/.test(PAGE),
  noSort: !/pnProductRows\s*\.sort\(|pnCandidateRows\s*\.sort\(/.test(PAGE)
};

check('B22 the lead is derived from ctx.isPreferred, never assumed',
  S.lead && S.primary, 'pnNoLead + primaryResult = pnNoLead ? null : pnFirstRow');

check('B23 the whole qualifying set reaches both existing surfaces',
  S.rows, 'pnProductRows = pnNoLead ? results : alternativeResults');

check('B24 originalRecommendation is still unwritable without a primary',
  S.origRec, 'a homeowner selection can never become an Atlas recommendation');

check('B25 the hero is still the only thing #matchPrimary ever receives',
  S.heroGate, 'and it is still gated on a primary existing');

check('B26 Garden Room still takes its lead from its own ranking',
  S.gardenRoom, 'isPreferred: index === 0 — untouched');

check('B27 no sort was introduced on either path',
  S.noSort, 'catalogue order is the artefact\'s order, not a ranking');

/* ── the real artefact really is in the no-lead state ───────────────────── */
const realCandidates = UNIVERSE.products
  .filter(p => (p.class3a || {}).state === 'CANDIDATE');
const caveatFree = realCandidates.filter(
  p => !((p.class3a || {}).caveats || []).length);
check('B28 the live artefact genuinely names no lead',
  realCandidates.length === 4 && caveatFree.length !== 1,
  `${realCandidates.length} candidates, ${caveatFree.length} caveat-free — `
  + 'a lead is named only when exactly one is');

console.log('  ' + '-'.repeat(68));
console.log(`  ${pass + fail} checks, ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
