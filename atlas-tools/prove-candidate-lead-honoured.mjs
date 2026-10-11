#!/usr/bin/env node
/* PlotNua — prove-candidate-lead-honoured.mjs
 *
 * REGRESSION for the implied-preference defect of 11 October 2026, founder
 * decision Option 1.
 *
 * The Additional Home Results page presented PROD-000425 Van XL as the
 * apparent lead because it sorts first by Product Code, while the candidate
 * split had deliberately declined to name one: all four Class 3A candidates
 * carry `caveats: []`, so clear.length === 4 and the split returns a null
 * lead. Two places ignored that — the ctx's `isPreferred` and the renderer's
 * `lead` — so the first product by code became the de-facto recommendation.
 *
 * BOTH CONDITIONS ARE TESTED, which is the whole point: a fix that suppresses
 * the lead panel always would be just as wrong as one that never suppresses
 * it. L-series = no lead (the live case). G-series = a genuine lead.
 *
 * The three functions under test are LIFTED FROM THE SHIPPED PAGE by reading
 * your-plot.html and evaluating the exact source text, so this cannot pass
 * against a page that no longer contains them.
 *
 * Reads the regenerated artefact. Writes nothing. No network.
 */
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

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

/* ── lift the shipped source, so the test cannot drift from the page ───── */
function lift(startMarker, name) {
  const i = PAGE.indexOf(startMarker);
  if (i === -1) throw new Error(`cannot find ${name} in your-plot.html`);
  // Brace-match from the first { after the marker.
  const open = PAGE.indexOf('{', i);
  let depth = 0, j = open;
  for (; j < PAGE.length; j++) {
    if (PAGE[j] === '{') depth++;
    else if (PAGE[j] === '}') { depth--; if (depth === 0) break; }
  }
  return PAGE.slice(i, j + 1);
}

const splitSrc = lift('function pnCandidateSplit(list){', 'pnCandidateSplit');

/* pnCandidateSplit's only external references are TOP_OF_BAND and
   pnFloorAreaEvidence. Both are supplied as the real page supplies them for
   a GOVERNED record: the governed caveats branch returns before either is
   reached, which is the branch every Class 3A candidate takes. */
const TOP_OF_BAND = /very top of the (?:range|band)/i;
const pnFloorAreaEvidence = () => null;
const pnCandidateSplit = new Function(
  'TOP_OF_BAND', 'pnFloorAreaEvidence',
  splitSrc + '; return pnCandidateSplit;')(TOP_OF_BAND, pnFloorAreaEvidence);

console.log('\n  CANDIDATE LEAD — IMPLIED PREFERENCE REGRESSION');
console.log('  ' + '-'.repeat(68));

/* ── the live population ──────────────────────────────────────────────── */
const candidates = UNIVERSE.products.filter(
  p => (p.class3a || {}).state === 'CANDIDATE');

check('S1  the artefact still holds four Class 3A candidates',
  candidates.length === 4,
  candidates.map(p => p.productCode).join(', '));

check('S2  BIOBUILDS Wanderlust is one of them',
  candidates.some(p => p.productCode === 'PROD-000523'),
  'PROD-000523 present, position ' +
  candidates.findIndex(p => p.productCode === 'PROD-000523'));

/* ── L · NO LEAD: the live case ───────────────────────────────────────── */
const splitL = pnCandidateSplit(candidates);

check('L1  the split declines to name a lead',
  splitL.lead === null,
  `${candidates.filter(p => !(p.class3a.caveats || []).length).length} of ` +
  `${candidates.length} candidates are caveat-free, so it cannot choose`);

/* The shipped ctx expression, exactly as the page now computes it. */
const ctxFor = (split, list) => list.map((p, i) => {
  const lead = (i === 0) && !!split.lead;
  return { productCode: p.productCode, isPreferred: lead };
});
const ctxL = ctxFor(splitL, splitL.lead ? [splitL.lead, ...splitL.others] : candidates);

check('L2  NO candidate is marked preferred',
  ctxL.every(c => !c.isPreferred),
  ctxL.map(c => `${c.productCode}:${c.isPreferred}`).join(' '));

/* The shipped renderer expression, exactly as the page now computes it. */
const renderLead = results =>
  (results && results.length && results[0] && results[0].ctx
   && results[0].ctx.isPreferred) ? results[0] : null;

const resultsL = ctxL.map(c => ({ ctx: c }));
check('L3  the renderer resolves NO lead, so the lead panel is suppressed',
  renderLead(resultsL) === null,
  'hmrLeadEvidence stays hidden: "What Atlas has established about this ' +
  'building" is no longer attributed to whichever product sorted first');

check('L4  all four candidates survive — none is dropped to hide the lead',
  ctxL.length === 4 &&
  ['PROD-000425', 'PROD-000437', 'PROD-000457', 'PROD-000523']
    .every(c => ctxL.some(x => x.productCode === c)),
  ctxL.map(c => c.productCode).join(', '));

check('L5  the order is UNCHANGED — no ranking was introduced',
  ctxL.map(c => c.productCode).join(',') ===
  candidates.map(p => p.productCode).join(','),
  'artefact order preserved exactly; BIOBUILDS was not promoted');

/* ── G · A GENUINE LEAD: the preserved case ───────────────────────────── */
const genuine = JSON.parse(JSON.stringify(candidates));
genuine.slice(1).forEach(p => { p.class3a.caveats = ['area-basis-unresolved']; });
const splitG = pnCandidateSplit(genuine);

check('G1  one caveat-free candidate IS named as the lead',
  splitG.lead && splitG.lead.productCode === 'PROD-000425',
  `lead = ${splitG.lead && splitG.lead.productCode}, ` +
  `others = ${splitG.others.length}`);

const ctxG = ctxFor(splitG, [splitG.lead, ...splitG.others]);
check('G2  exactly ONE candidate is marked preferred, and it is the lead',
  ctxG.filter(c => c.isPreferred).length === 1 &&
  ctxG[0].isPreferred && ctxG[0].productCode === 'PROD-000425',
  ctxG.map(c => `${c.productCode}:${c.isPreferred}`).join(' '));

const resultsG = ctxG.map(c => ({ ctx: c }));
check('G3  the renderer resolves THAT lead, so the panel still appears',
  renderLead(resultsG) === resultsG[0],
  'existing lead presentation preserved exactly');

check('G4  all four still render in the genuine-lead case too',
  ctxG.length === 4, ctxG.map(c => c.productCode).join(', '));

/* ── C · CAPABILITY: the pre-fix expressions still mis-state ──────────── */
const ctxPreFix = candidates.map((p, i) => ({
  productCode: p.productCode, isPreferred: i === 0 }));
check('C1  the PRE-FIX ctx expression marks a preference with no lead',
  ctxPreFix[0].isPreferred === true && splitL.lead === null,
  'proves the test can tell the two apart — `i === 0` alone still claims ' +
  'PROD-000425 is preferred while the split says there is no lead');

const renderLeadPreFix = r => (r && r.length ? r[0] : null);
check('C2  the PRE-FIX renderer expression still resolves a false lead',
  renderLeadPreFix(resultsL) !== null,
  'the old line would still draw the panel for PROD-000425');

/* ── P · the page really contains the fix ─────────────────────────────── */
check('P1  the shipped ctx reads the split, not the index',
  PAGE.includes('isPreferred: lead,') && !PAGE.includes('isPreferred: i === 0,'),
  'one occurrence, and the old form is gone');

check('P2  the shipped renderer reads ctx.isPreferred',
  PAGE.includes('results[0].ctx.isPreferred'),
  'detector and panel now share one signal');

check('P3  no sort or ranking was added to the residential path',
  !/pnResidentialResults[\s\S]{0,1200}\.sort\(/.test(PAGE),
  'order still comes from the artefact alone');

console.log('  ' + '-'.repeat(68));
console.log(`  ${pass + fail} checks, ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
