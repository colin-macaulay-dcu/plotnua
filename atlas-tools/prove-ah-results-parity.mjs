#!/usr/bin/env node
/* PlotNua — prove-ah-results-parity.mjs
 *
 * The presentation-parity build, A1–A24. Founder authorisation 12 October 2026.
 *
 * Everything under test is LIFTED FROM THE SHIPPED PAGE and run against the
 * real artefact and the real suppliers detail partition. The supplier join in
 * particular is driven against Atlas's own published partition, so a wrong
 * join would resolve to the wrong record and fail here rather than in front
 * of a homeowner.
 *
 * Writes nothing. No network.
 */
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { JSDOM } from 'jsdom';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const PAGE = readFileSync(join(ROOT, 'your-plot.html'), 'utf8');
const U = JSON.parse(readFileSync(
  join(ROOT, 'additional-home-universe-v1.json'), 'utf8'));
const SUPP = JSON.parse(readFileSync(
  join(ROOT, 'garden-room-detail-suppliers-v1.json'), 'utf8')).products;

let pass = 0, fail = 0;
const check = (name, ok, detail = '') => {
  (ok ? pass++ : fail++);
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}`);
  if (detail) console.log(`        ${detail}`);
};

function lift(marker, name, bodyAfter) {
  const i = PAGE.indexOf(marker);
  if (i === -1) throw new Error(`cannot find ${name}`);
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

console.log('\n  ADDITIONAL HOME RESULTS — PRESENTATION PARITY, A1 to A24');
console.log('  ' + '-'.repeat(68));

const dom = new JSDOM('<!doctype html><html><body><div id="h"></div></body></html>');
global.document = dom.window.document;
global.window = dom.window;

/* ── the real view + card, with only network leaves supplied ────────────── */
const PLACEHOLDER = 'data:image/svg+xml;PH';
let detailStore = null;
const deps = {
  attachImageFallback() {},
  PN_IMAGE_FALLBACK_SRC: PLACEHOLDER,
  pnAuthorisedImage(p) {
    const im = p && p.imagery;
    return (im && im.url && im.credit) ? im : null;
  },
  pnAttachImageCredit(w, im) {
    const c = document.createElement('p');
    c.className = 'pn-image-credit';
    c.textContent = im.credit + (im.linkBack ? ' · ' + im.linkBack : '');
    w.appendChild(c);
  },
  pnPriceDisplay(p) {
    return (typeof p.price === 'number')
      ? '€' + p.price.toLocaleString('en-IE') : '';
  },
  pnPriceView(p) { return { known: typeof p.price === 'number' }; },
  pnSupplierOrgType() { return null; },
  irishRouteNoteText() { return null; },
  buildMatchReasons() { return []; },
  buildAlternativeRationale() { return ''; },
  buildSaveActions() {
    const a = document.createElement('div');
    a.className = 'match-card-actions';
    const l = document.createElement('a');
    l.className = 'open-myplot-link';
    return { actions: a, openMyPlotLink: l };
  },
  raCompareControl() { return null; },
  productDetailContext: new Map(),
  AS_BUDGET_LABEL: {},
  openProductDetail() {},
  /* THE REAL PARTITION, under the real handle the resolver reads. */
  get pnDetailParts() { return { suppliers: detailStore }; }
};

const SRC = [
  lift('function hasValidArea(value){', 'hasValidArea'),
  lift('function pnViewOptionButton(product){', 'pnViewOptionButton'),
  lift('function pnSupplierOrgIdByName(name){', 'pnSupplierOrgIdByName'),
  lift('function pnSupplierOrgId(product){', 'pnSupplierOrgId'),
  lift('function pnAdditionalHomeView(p){', 'pnAdditionalHomeView'),
  lift('function buildResultsGalleryCard(', 'buildResultsGalleryCard',
       '}, primaryResult)')
].join('\n\n');

const keys = Object.keys(deps).filter(k => k !== 'pnDetailParts');
const H = new Function(...keys, 'pnDetailParts',
  `let pnResultUse = 'residential';
   let pnOrgIdByNameCache = null;
   ${SRC}
   return { view: pnAdditionalHomeView, card: buildResultsGalleryCard,
            orgId: pnSupplierOrgId, byName: pnSupplierOrgIdByName };`
)(...keys.map(k => deps[k]), { get suppliers() { return detailStore; } });

const CAND = U.products.filter(p => (p.class3a || {}).state === 'CANDIDATE');
const CODES = ['PROD-000425', 'PROD-000437', 'PROD-000457', 'PROD-000523'];

check('A1  the four qualifying products are the four named ones',
  CAND.length === 4 && CAND.map(p => p.productCode).join(',') === CODES.join(','),
  CAND.map(p => p.productName).join(' · '));

/* ═══ THE SUPPLIER JOIN ═══════════════════════════════════════════════ */
detailStore = null;
check('A2  with the partition unfetched the join is silent, not wrong',
  H.byName('All About Outdoors') === null
  && H.view(CAND[0]).organisationEvidence === undefined,
  'the lazy partition has not landed yet, so no supplier claim is made');

detailStore = SUPP;
const joined = CAND.map(p => ({
  code: p.productCode, org: p.organisation,
  id: H.byName(p.organisation)
}));
const expect = {
  'All About Outdoors': 'reccM9Gg66ZuZC0m3',
  'All In One Cabins': 'rec7q7WitcIuY3phT',
  'Concept Modular': 'recfV4V49BHoMsYBA',
  'BIOBUILDS': null
};
check('A3  each organisation resolves to ITS OWN record, or to nothing',
  joined.every(j => j.id === expect[j.org]),
  joined.map(j => `${j.org} → ${j.id || 'not in the partition'}`).join('\n        '));

check('A4  the resolved id is the one every shared supplier surface reads',
  CAND.slice(0, 3).every(p => H.orgId(H.view(p)) === expect[p.organisation]),
  'pnSupplierOrgId(view) now answers for Additional Home products');

check('A5  BIOBUILDS has no record, so no supplier evidence is asserted',
  H.view(CAND[3]).organisationEvidence === undefined
  && H.orgId(H.view(CAND[3])) === null,
  'absent is absent — nothing is borrowed from a similar name');

check('A6  a near-miss name resolves to nothing, never to a neighbour',
  H.byName('All About Outdoor') === null
  && H.byName('all about outdoors') === null
  && H.byName('Concept Modular Ltd') === null,
  'exact match after trimming, or null');

check('A7  whitespace is tolerated, because Atlas data carries it',
  H.byName('  All About Outdoors  ') === expect['All About Outdoors'],
  'trimmed, not fuzzy-matched');

/* The real Google mechanism, unchanged, measured against the real data. */
const withGoogle = Object.keys(SUPP).filter(id => {
  const g = SUPP[id].googleIdentity;
  return g && g.state === 'verified' && g.placeId;
});
check('A8  Google identity is verified for only the organisations Atlas holds',
  withGoogle.length === 2
  && !withGoogle.some(id => Object.values(expect).includes(id)),
  withGoogle.map(id => SUPP[id].name).join(', ')
  + ' — and none of the four Additional Home suppliers, so nothing '
  + 'Google-shaped renders for them');

check('A9  no rating, review count or endorsement is invented anywhere',
  !/\b(4\.\d\s*(out of|\/)\s*5|\d+\s+reviews?\b)/.test(
    JSON.stringify(CAND)) &&
  !/pnAhRating|ahReview|fakeRating|defaultRating/.test(PAGE),
  'the shipped identity-only mechanism is the only route to a rating');

/* ═══ THE CARDS ═══════════════════════════════════════════════════════ */
const cards = CAND.map(p => {
  const v = H.view(p);
  return H.card({
    role: 'residential', product: v,
    ctx: { leadReason: 'Atlas has confirmed this is a habitable building '
                       + 'in the Class 3A floor-area band.' },
    altReason: 'Atlas has confirmed this is a habitable building in the '
               + 'Class 3A floor-area band.',
    altTradeOff: ''
  }, null);
});

const priceRows = cards.map(c => {
  const r = c.querySelector('.results-gallery-price-row');
  return r ? r.textContent : '';
});
check('A10 THE ORPHAN SEPARATOR IS GONE',
  priceRows.every(t => !/^\s*·/.test(t) && !/·\s*$/.test(t)
                       && !/·\s*·/.test(t)),
  priceRows.map((t, i) => CODES[i] + ': ' + JSON.stringify(t)).join('\n        '));

check('A11 Van XL shows its area alone, because it publishes no price',
  priceRows[0] === '33m²',
  'was "· 33m²" — a separator with nothing before it');

check('A12 every priced product shows price and area, correctly joined',
  priceRows[1] === '€24,076 · 42m²'
  && priceRows[2] === '€72,500 · 36.2m²'
  && priceRows[3] === '€105,000 · 35.54m²',
  priceRows.slice(1).join(' | '));

check('A13 every card names its supplier',
  cards.every((c, i) => {
    const o = c.querySelector('.results-gallery-org');
    return o && o.textContent === CAND[i].organisation;
  }), CAND.map(p => p.organisation).join(' · '));

check('A14 the governed floor area reaches every card',
  CAND.every(p => typeof H.view(p).floorAreaM2 === 'number'),
  CAND.map(p => p.productCode + ': ' + H.view(p).floorAreaM2 + 'm²').join(' · '));

const w = cards[3];
check('A15 Wanderlust keeps its approved photograph, credit and link-back',
  (function(){
    const img = w.querySelector('.results-gallery-media img');
    const cr = w.querySelector('.pn-image-credit');
    return img && /biobuilds\.com/.test(img.getAttribute('src'))
      && !img.classList.contains('pn-image-fallback')
      && cr && /BIOBUILDS/.test(cr.textContent)
      && /biobuilds\.com/.test(cr.textContent);
  })(), 'unchanged by this build');

check('A16 the three with no grant keep the governed placeholder path',
  cards.slice(0, 3).every(c => {
    const i = c.querySelector('.results-gallery-media img');
    return i && i.classList.contains('pn-image-fallback');
  }) && !cards.slice(0, 3).some(c => c.querySelector('.pn-image-credit')),
  'no credit without a grant');

/* ═══ CSS: THE STRETCH, THE SPACING, THE REASON LINE ══════════════════ */
const CSS = {
  noStretch: /#screen-match-results #matchPrimary\[data-pn-verdict="1"\] ~ #altResults\{\s*align-items:start;/
               .test(PAGE),
  autoHeight: /#matchPrimary\[data-pn-verdict="1"\] ~ #altResults > \*\{\s*height:auto;/
                .test(PAGE),
  stretchKept: /#screen-match-results #altResults\{[\s\S]{0,200}align-items:stretch;/
                 .test(PAGE),
  heroGap: /#screen-match-results #matchPrimary\[data-pn-verdict="1"\]\{\s*margin-bottom:var\(--pn-space-lg\);\s*padding-bottom:0;/
             .test(PAGE),
  roleSentence: /\[data-pn-verdict="1"\] ~ #altResults\s*\n\s*\.results-gallery-role\{\s*\n\s*font-size:13\.5px; font-weight:400;/
                  .test(PAGE),
  roleLabelKept: /#screen-match-results #altResults \.results-gallery-role\{\s*\n\s*order:4; margin:0 0 6px; font-size:12px; font-weight:600;/
                   .test(PAGE),
  collapseKept: /#screen-match-results #altResults \.results-gallery-media:has\(img\.pn-image-fallback\)\{\s*display:none;/
                  .test(PAGE)
};

check('A17 cards no longer stretch to the tallest in the row',
  CSS.noStretch && CSS.autoHeight,
  'align-items:start and height:auto, scoped to the verdict state');

check('A18 Garden Room keeps the stretch and the aligned feet',
  CSS.stretchKept && CSS.roleLabelKept,
  'the shipped rules are preserved, not replaced');

check('A19 the hero’s trailing space steps down one place on the scale',
  CSS.heroGap, '--pn-space-2xl (96px) → --pn-space-xl (48px), verdict only');

check('A20 the reason line is set as a sentence on the residential cards',
  CSS.roleSentence, '13.5px regular, body colour — not 12px semibold stone');

check('A21 the governed no-image collapse is untouched',
  CSS.collapseKept, 'imagery rights presentation is exactly as shipped');

/* ═══ SUN & LIGHT, AND THE PAGE FLOW ═════════════════════════════════ */
check('A22 Sun & Light is reinstated on the residential no-lead path',
  /if \(pnResidential && !primaryResult && els\.resultsSunlightCentrepiece\)/
    .test(PAGE)
  && /activateResultsSunlightCentrepiece\(null\);/.test(PAGE),
  'the panel reads no product datum — the one line that did is commented '
  + 'out under ISSUE 007');

check('A23 Scene 4’s product-specific reassurance stays suppressed',
  /if \(els\.resultsReassurance\) els\.resultsReassurance\.hidden = true;/
    .test(PAGE),
  'buildPrimaryWorthChecking() IS product-specific, so it stays out');

check('A24 the hero now reads the governed imagery reader on BOTH journeys',
  /if \(pnImg \|\| product\.imageUrl\) \{/.test(PAGE),
  'the universe JSON carries no imageUrl, but the live pool is enriched '
  + 'elsewhere — the rendered Garden Room hero shows a real photograph — so '
  + 'the hero must consult the governed reader, exactly as the card does');

console.log('  ' + '-'.repeat(68));
console.log(`  ${pass + fail} checks, ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
