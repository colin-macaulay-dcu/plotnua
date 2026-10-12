#!/usr/bin/env node
/* PlotNua — prove-lens-null-primary.mjs
 *
 * THE PRE-IMPLEMENTATION VERIFICATION the founder required before the no-lead
 * equality build may start:
 *
 *   "Verify that lens resolvers safely handle a null primaryResult. Resolve
 *    any issue without assigning an arbitrary replacement lead."
 *
 * WHY THIS CANNOT BE SETTLED BY READING. renderLensRail() takes primaryResult
 * and derives `const primary = primaryResult && primaryResult.product`, which
 * is null-safe on its own line. What matters is what every resolver BELOW it
 * then does with a null product, and three of them take it as an argument.
 * Reading says they look safe; this runs them.
 *
 * The functions are LIFTED FROM THE SHIPPED PAGE by brace-matching, so the
 * proof cannot pass against a page that no longer contains them.
 *
 * Reads your-plot.html and the committed artefact. Writes nothing. No network.
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

console.log('\n  LENS RESOLVERS UNDER A NULL PRIMARY');
console.log('  ' + '-'.repeat(68));

/* ── the real candidate rows, shaped as the rail receives them ──────────── */
const candidates = UNIVERSE.products
  .filter(p => (p.class3a || {}).state === 'CANDIDATE')
  .map(p => ({ product: {
    id: p.id, productCode: p.productCode, name: p.productName,
    organisation: p.organisation, price: p.price,
    manufactureCountry: null, installationModel: null
  }}));

check('S1  four real candidate rows assembled from the artefact',
  candidates.length === 4, candidates.map(r => r.product.productCode).join(', '));

/* ── R1 · raLocalResolve, the only lens doing real work on residential ──── */
const localSrc = lift('function raLocalResolve(rows, county, primaryProduct){',
                      'raLocalResolve');
const pickedSrc = lift('function raLocalPickLocated(', 'raLocalPickLocated');

/* pnSupplierBasedInCounty is the frozen premises adjudication. Both arms are
   driven: a county nobody is based in, and one where a candidate is. */
let basedIn = () => false;
const raLocalPickLocated = new Function(
  'pnSupplierBasedInCounty',
  pickedSrc + '; return raLocalPickLocated;')((p, c) => basedIn(p, c));
const raLocalResolve = new Function(
  'pnSupplierBasedInCounty', 'raLocalPickLocated',
  localSrc + '; return raLocalResolve;')((p, c) => basedIn(p, c), raLocalPickLocated);

let threw = null, res;
try { res = raLocalResolve(candidates, 'Wicklow', null); }
catch (e) { threw = e; }
check('R1  raLocalResolve(rows, county, NULL) does not throw',
  !threw, threw ? String(threw) : 'returned ' + JSON.stringify(res));

check('R2  with no supplier based in the county it resolves to nothing',
  res === null, 'the lens then renders its own state card, not a product');

/* Now a county where one candidate IS based — the lens must still answer, and
   must NOT reach the how:"primary" arm, because there is no primary to be. */
basedIn = (prod, county) =>
  county === 'Wicklow' && prod && prod.productCode === 'PROD-000457';
threw = null;
try { res = raLocalResolve(candidates, 'Wicklow', null); }
catch (e) { threw = e; }
check('R3  it still resolves a located option with a null primary',
  !threw && res && res.how === 'located'
  && res.product.productCode === 'PROD-000457',
  threw ? String(threw)
        : `how=${res && res.how}, product=${res && res.product.productCode}`);

check('R4  the how:"primary" arm is UNREACHABLE with a null primary',
  res.how !== 'primary',
  'so "Your recommendation is based in your county" can never be said when '
  + 'Atlas has not made a recommendation');

/* ── R5 · raEuropeanPick, called with `primary && primary.id` ───────────── */
const euroSrc = lift('function raEuropeanPick(rows, excludeId){', 'raEuropeanPick');
const raEuropeanPick = new Function(
  'raCountryOf', 'NON_IRISH_EUROPEAN_COUNTRIES',
  euroSrc + '; return raEuropeanPick;')(
  p => (p && p.manufactureCountry) || null, ['Sweden', 'Estonia', 'Finland']);

threw = null; let euro;
try { euro = raEuropeanPick(candidates, undefined); } catch (e) { threw = e; }
check('R5  raEuropeanPick(rows, UNDEFINED excludeId) does not throw',
  !threw, threw ? String(threw) : 'returned ' + (euro ? euro.productCode : 'null'));

/* excludeId undefined must not accidentally exclude a row: no product id is
   undefined, so every row stays eligible for the lens. */
const withEuro = candidates.map((r, i) => i === 1
  ? { product: Object.assign({}, r.product, { manufactureCountry: 'Sweden' }) }
  : r);
check('R6  an undefined excludeId excludes NOTHING',
  raEuropeanPick(withEuro, undefined) &&
  raEuropeanPick(withEuro, undefined).productCode === 'PROD-000437',
  'the row that would have been dropped as "the primary" is still offered');

/* ── R7 · the residential early returns read no primary at all ─────────── */
const railSrc = lift('function renderLensRail(primaryResult, alternativeResults, twistIdea){',
                     'renderLensRail');
const euroResidential = railSrc.slice(
  railSrc.indexOf("lens.id === 'european' && pnResultUse === 'residential'"));
check('R7  the residential European branch returns before reading `primary`',
  /raStateCard\(lens, 'not-yet'[\s\S]{0,400}?return;/.test(euroResidential)
  && !/isEuro\(primary\)/.test(euroResidential.slice(0, 400)),
  'the state card is built from the lens, not from a product');

const wildResidential = railSrc.slice(
  railSrc.indexOf("lens.id === 'wildcard' && pnResultUse === 'residential'"));
check('R8  the residential wildcard branch does the same',
  /raStateCard\(lens, 'not-yet'[\s\S]{0,400}?return;/.test(wildResidential),
  'no primary is read on the residential path');

/* ── R9 · raCompareControl already refuses without a primary ────────────── */
const cmpSrc = lift('function raCompareControl(lens, product){', 'raCompareControl');
check('R9  raCompareControl returns null when there is no compare primary',
  /if \(!resultsComparePrimary \|\| !resultsComparePrimary\.id\) return null;/
    .test(cmpSrc),
  'so no card offers "Compare with the recommendation" when none exists');

/* ── R10 · RE-POINTED, 12 October 2026 ──────────────────────────────────
   The finding was that renderResultsDecide(null) hid "Before you decide"
   unconditionally, which made the section product-specific. The founder
   then required the Additional Home result to carry the same closing
   experience, so the property result now RENDERS it and marks it as its
   own. The null branch must therefore still hide the section — except
   where that marker says the property result owns it. Both halves are
   asserted: a Garden Room render with no product still hides it. */
const RRD = lift('function renderResultsDecide(product){', 'renderResultsDecide');
check('R10 renderResultsDecide(null) still hides a section it owns',
  /sec\.hidden = true; els\.bydPoints\.innerHTML = ''; return 0;/.test(RRD)
  && /if \(!product\) \{/.test(RRD),
  'the product-less call clears the section exactly as before');

check('R10b unless the property result rendered it',
  /getAttribute\('data-pn-residential-decide'\) === '1'\) return 0;/.test(RRD),
  'the Additional Home closing experience is not erased a moment after it '
  + 'is built; Garden Room never sets the marker, so it is unaffected');


console.log('  ' + '-'.repeat(68));
console.log(`  ${pass + fail} checks, ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
