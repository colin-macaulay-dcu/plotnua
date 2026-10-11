/**
 * PROVE THE PRICE PRESENTATION IS UNCHANGED FOR EVERY EXISTING PRODUCT
 * ====================================================================
 * The founder's seventh requirement — "Preserve the existing comparison
 * experience for products with only one price" — asserted against the whole
 * universe rather than against a handful of invented shapes.
 *
 * HOW. The price contract is lifted TWICE: once from the BASELINE
 * your-plot.html (git HEAD by default) and once from the working tree. Every
 * product in both real artefacts is then run through both, and the four
 * homeowner-visible outputs are compared character for character:
 *
 *     display · tail · figure · kind
 *
 * plus the budget comparability flag, which decides whether a product can be
 * ranked against the homeowner's band at all.
 *
 * Any product whose price presentation moved is listed by name. A product
 * SHOULD only move if it carries named configurations — and today none in
 * either artefact does, because the artefacts predate the schema. So the
 * expected result is zero differences across 573 + 46 products, and that is
 * exactly what makes this worth running: it is the assertion that a change
 * built for two suppliers did not quietly touch 619 products.
 *
 *   node atlas-tools/prove-price-presentation-unchanged.mjs
 *        [--baseline PATH] [--plot PATH]
 *
 * Exit 0 = no product moved. Exit 1 = at least one did.
 * Exit 2 = the instrument could not run: no baseline, or a slice that would
 *          not evaluate. NOT a pass.
 */
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const arg = (n, d) => {
  const i = process.argv.indexOf('--' + n);
  return i === -1 ? d : process.argv[i + 1];
};
const PLOT = arg('plot', join(ROOT, 'your-plot.html'));
const BASELINE = arg('baseline', null);

function refuse(why) {
  console.log('\nPRICE PRESENTATION EQUIVALENCE');
  console.log('='.repeat(74));
  console.log('  INSTRUMENT UNAVAILABLE: ' + why);
  console.log('  Nothing was measured. This is not a pass.');
  process.exit(2);
}

/* ── The two versions of the page ────────────────────────────────────── */
let current, baseline, baselineFrom;
try {
  current = readFileSync(PLOT, 'utf8');
} catch (e) { refuse('the working tree page could not be read: ' + e.message); }

if (BASELINE) {
  try {
    baseline = readFileSync(BASELINE, 'utf8');
    baselineFrom = BASELINE;
  } catch (e) { refuse('the baseline could not be read: ' + e.message); }
} else {
  // git HEAD is the honest baseline: what is committed, not what happens to
  // be lying in a .bak sidecar that an earlier run may have left behind.
  try {
    baseline = execFileSync('git', ['show', 'HEAD:your-plot.html'],
                            { cwd: ROOT, encoding: 'utf8',
                              maxBuffer: 64 * 1024 * 1024 });
    baselineFrom = 'git HEAD:your-plot.html';
  } catch (e) {
    refuse('no --baseline was given and git HEAD:your-plot.html could not be '
           + 'read (' + String(e.message).slice(0, 120) + ')');
  }
}

/* ── Lift one contract ───────────────────────────────────────────────── */
const START = '  const PN_PRICE_SYMBOL =';
const END = '  const pb046 = { originalResults:';
const PRELUDE = `
  const PB046_NO_PRICE = 'Price not published';
  const PB046_AMBIGUOUS_PRICE = 'Price not confirmed';
  const PB046_QUOTE_PRICE = 'Priced on enquiry';
  const AS_BUDGET_CURRENCY = 'EUR';
  const window = {};
`;
function lift(html, label) {
  const a = html.indexOf(START), b = html.indexOf(END);
  if (a === -1 || b === -1 || b <= a) {
    refuse('the price contract could not be located in ' + label);
  }
  try {
    // eslint-disable-next-line no-new-func
    return new Function(PRELUDE + html.slice(a, b) + `
      return { view: pnPriceView, delta: pnPriceDelta,
               budget: pnPriceComparableToBudget };
    `)();
  } catch (e) {
    refuse('the contract lifted from ' + label + ' would not evaluate: '
           + e.message);
  }
}
const B = lift(baseline, baselineFrom);
const C = lift(current, PLOT);

/* ── Every product in both real artefacts ────────────────────────────── */
function productsOf(name) {
  let doc;
  try { doc = JSON.parse(readFileSync(join(ROOT, name), 'utf8')); }
  catch (e) { refuse(name + ' could not be read: ' + e.message); }
  const list = doc.products || (Array.isArray(doc) ? doc : null);
  if (!Array.isArray(list)) refuse(name + ' holds no product list');
  return list;
}
const garden = productsOf('garden-room-recommendation-universe-v1.json');
const homes = productsOf('additional-home-universe-v1.json');

/* The Additional Home artefact holds the GOVERNED record, whose price is an
   object. The runtime converts it with pnAdditionalHomeView() before any of
   this contract sees it, so the same conversion is applied here — the fields
   this contract actually reads, and nothing else. Re-implementing the whole
   bridge would be testing a copy; these four fields are the contract's entire
   input surface. */
function asRuntime(p) {
  const pr = p.price && typeof p.price === 'object' ? p.price : null;
  const verified = pr && pr.state === 'VERIFIED_NUMERIC_PRICE'
                      && typeof pr.amount === 'number';
  return {
    productName: p.productName || p.name || p.id,
    currency: (pr && pr.currency) || p.currency || null,
    price: verified ? pr.amount : null,
    priceEvidence: pr ? {
      priceType: pr.priceType || null,
      currency: pr.currency || null,
      base: verified ? pr.amount : null,
      from: null, to: null,
      quoteOnly: pr.state === 'EVIDENCED_POA_QUOTE',
      configurations: verified && Array.isArray(pr.configurations)
        ? pr.configurations : null,
      basis: verified ? (pr.basis || null) : null,
      commercialTerms: verified && Array.isArray(pr.commercialTerms)
        ? pr.commercialTerms : null
    } : null
  };
}

const rows = [
  ...garden.map(p => ({ pool: 'garden room', p })),
  ...homes.map(p => ({ pool: 'additional home', p: asRuntime(p) }))
];

console.log('\nPRICE PRESENTATION EQUIVALENCE');
console.log('='.repeat(74));
console.log(`  baseline  ${baselineFrom}`);
console.log(`  current   ${PLOT}`);
console.log(`  products  ${garden.length} garden rooms + ${homes.length} `
            + `additional homes = ${rows.length}`);

const moved = [];
for (const { pool, p } of rows) {
  const before = B.view(p), after = C.view(p);
  const diffs = [];
  for (const k of ['display', 'tail', 'figure', 'kind', 'known']) {
    if (String(before[k]) !== String(after[k])) {
      diffs.push(`${k}: ${JSON.stringify(before[k])} → ${JSON.stringify(after[k])}`);
    }
  }
  if (B.budget(p) !== C.budget(p)) diffs.push('budget comparability changed');
  if (diffs.length) {
    moved.push(`${pool} · ${p.productName || p.id} · ${diffs.join('; ')}`);
  }
}

/* The delta is the other half of the presentation: a product's comparison
   experience is not preserved if the same pair of products now refuses to
   compare. Every product is paired against the first priced product in its
   own pool, which is enough to catch a blanket refusal. */
function firstPriced(list) {
  for (const p of list) if (typeof p.price === 'number' && p.price > 0) return p;
  return null;
}
const refGarden = firstPriced(garden);
const refHome = firstPriced(homes.map(asRuntime));
let deltaMoved = 0;
const deltaExamples = [];
for (const { pool, p } of rows) {
  const ref = pool === 'garden room' ? refGarden : refHome;
  if (!ref) continue;
  const b = B.delta(p, ref), c = C.delta(p, ref);
  const same = (b === null && c === null) ||
               (b && c && b.diff === c.diff && b.currency === c.currency);
  if (!same) {
    deltaMoved++;
    if (deltaExamples.length < 8) {
      deltaExamples.push(`${pool} · ${p.productName || p.id} · `
        + `${JSON.stringify(b)} → ${JSON.stringify(c)}`);
    }
  }
}

console.log('-'.repeat(74));
if (!moved.length) {
  console.log(`  PASS  every one of the ${rows.length} products renders its price `
              + 'exactly as before');
} else {
  console.log(`  FAIL  ${moved.length} product(s) changed how their price reads:`);
  moved.slice(0, 20).forEach(m => console.log('        ' + m));
  if (moved.length > 20) console.log(`        ... and ${moved.length - 20} more`);
}
if (!deltaMoved) {
  console.log(`  PASS  every one of the ${rows.length} price comparisons against `
              + 'its pool reference is unchanged');
} else {
  console.log(`  FAIL  ${deltaMoved} price comparison(s) changed:`);
  deltaExamples.forEach(m => console.log('        ' + m));
}
console.log('');
process.exit((moved.length || deltaMoved) ? 1 : 0);
