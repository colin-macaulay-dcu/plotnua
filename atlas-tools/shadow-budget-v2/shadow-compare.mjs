/* SHADOW COMPARISON — live logic vs proposed logic, over the same 477 products.
   Read-only. Writes nothing. */
import { readFileSync } from 'node:fs';
import { SHADOW_BUDGET_BANDS, SHADOW_BUDGET_LABEL, shadowBudgetFit } from './shadow-budget-bands.mjs';

const U = JSON.parse(readFileSync(new URL('./shadow-recommendation-universe-v2.json', import.meta.url)));
const P = U.products;

/* The LIVE definitions, transcribed exactly from your-plot.html line 15658 and
   budgetFit() at ~16526. Not imported, because the live file must not be a
   dependency of a shadow tool; transcribed so a drift guard can compare them. */
const LIVE_BANDS = {
  'under-10k': { lo: 0, hi: 10000 }, '10k-20k': { lo: 10000, hi: 20000 },
  '20k-30k': { lo: 20000, hi: 30000 }, '30k-plus': { lo: 30000, hi: Infinity },
};
const LIVE_LABEL = { 'under-10k':'Under €10,000','10k-20k':'€10,000–€20,000',
  '20k-30k':'€20,000–€30,000','30k-plus':'€30,000+' };
function liveBudgetFit(product, band){
  if (!band) return 1;
  const price = product ? product.price : null;
  if (typeof price !== 'number' || !isFinite(price)) return 1;
  if (product.currency !== 'EUR') return 1;
  return (price >= band.lo && price <= band.hi) ? 2 : 0;
}

const eur = P.filter(x => typeof x.price === 'number' && x.price > 0 && x.currency === 'EUR');
const orgs = s => new Set(s.map(x => x.organisation)).size;
const f = n => n.toLocaleString('en-IE');

console.log('I · SHADOW COMPARISON');
console.log('='.repeat(78));
console.log('source            %s  generated %s  dryRun %s', U.builtFrom.file, U.builtFrom.generated, U.builtFrom.dryRun);
console.log('recommendation population   %d products, %d organisations', P.length, orgs(P));
console.log('  usable EUR price          %d products, %d organisations', eur.length, orgs(eur));
console.log('  usable GBP price          %d  (scored 1 by BOTH architectures)', P.filter(x=>x.currency==='GBP'&&x.price>0).length);
console.log('  no usable price           %d', P.length - P.filter(x=>typeof x.price==='number'&&x.price>0).length);

console.log('\nOLD BANDS (live)                      products  suppliers');
for (const [k,b] of Object.entries(LIVE_BANDS)) {
  const m = eur.filter(x => liveBudgetFit(x,b) === 2);
  console.log('  ' + LIVE_LABEL[k].padEnd(22) + String(m.length).padStart(8) + String(orgs(m)).padStart(10));
}
console.log('\nNEW BANDS (proposed)                  products  suppliers   unsafe suppressed');
for (const [k,b] of Object.entries(SHADOW_BUDGET_BANDS)) {
  const m = eur.filter(x => shadowBudgetFit(x,b) === 2);
  const sup = eur.filter(x => shadowBudgetFit(x,b) === -1 && x.price >= b.lo && x.price <= b.hi);
  console.log('  ' + SHADOW_BUDGET_LABEL[k].padEnd(22) + String(m.length).padStart(8) + String(orgs(m)).padStart(10) + String(sup.length).padStart(12));
}

const unsafe = eur.filter(x => x.priceSafeForMatching === false);
console.log('\nunsafe/conflicted EUR prices removed from strong matching: %d', unsafe.length);
for (const x of unsafe) console.log('   €' + f(x.price).padEnd(9) + ' ' + x.name.slice(0,46).padEnd(47) + x.priceBasisConfidence);

const rf = eur.filter(x=>x.priceIsRangeFloor).length;
console.log('\nrange-floor products (render with "From"): ' + rf + ' of ' + eur.length + ' priced EUR (' + Math.round(100*rf/eur.length) + '%)');
console.log('   KNOWN GAP: Phase 2 identified 69 range-floor cases by reading the prose.');
console.log('   6 Loghouse/Shomera products publish a RANGE but record a single Base Price,');
console.log('   so no structured field makes them derivable. Fix belongs in Airtable (populate');
console.log('   Price To), not in a heuristic here. Recorded, not guessed.');

console.log('\nbasis-class counts (all %d products)', P.length);
const cc = {}; for (const x of P) cc[x.priceBasisClass] = (cc[x.priceBasisClass]||0)+1;
for (const k of Object.keys(cc).sort((a,b)=>cc[b]-cc[a])) console.log('   ' + k.padEnd(28) + String(cc[k]).padStart(5));
console.log('   UNKNOWN basis among priced EUR:  %d of %d', eur.filter(x=>x.priceBasisClass==='UNKNOWN').length, eur.length);

console.log('\nVAT states among priced EUR');
const vv = {}; for (const x of eur) vv[String(x.vatStatus)] = (vv[String(x.vatStatus)]||0)+1;
for (const k of Object.keys(vv).sort((a,b)=>vv[b]-vv[a])) console.log('   ' + k.padEnd(12) + String(vv[k]).padStart(5));
console.log('   products carrying a published VAT RATE: %d', eur.filter(x=>x.vatRate).length);

/* verdict changes: for every (product, old band) pair, what the homeowner's
   equivalent new band would now say. */
/* CORRECTED 6 Oct 2026. The first version of this loop chose the new band by
   the PRODUCT's own price (price < 50000 ? '30k-50k' : '50k-plus'). That picks
   a band guaranteed to contain the product, so it could never produce a
   2 -> 0 — it measured "does this product keep a verdict somewhere", not
   "what does a given homeowner now see". It under-reported the change set as
   48 with zero 2 -> 0, which is the split's whole purpose. The comparison must
   be driven by the HOMEOWNER's selection: each old band a homeowner could pick
   is compared against each new band they could pick in its place. */
const SUCCESSORS = { 'under-10k':['under-10k'], '10k-20k':['10k-20k'],
                     '20k-30k':['20k-30k'], '30k-plus':['30k-50k','50k-plus'] };
let changed = [];
for (const x of eur) {
  for (const [ok, ob] of Object.entries(LIVE_BANDS)) {
    const o = liveBudgetFit(x, ob);
    for (const nk of SUCCESSORS[ok]) {
      const n = shadowBudgetFit(x, SHADOW_BUDGET_BANDS[nk]);
      if (o !== n) changed.push({ x, ok, nk, o, n });
    }
  }
}
console.log('\nrecommendation verdicts that change: %d (product × band pairs)', changed.length);
const by = {}; for (const c of changed) { const k = `${c.o} -> ${c.n}`; by[k] = (by[k]||0)+1; }
for (const k of Object.keys(by).sort()) console.log('   ' + k.padEnd(12) + String(by[k]).padStart(5));

console.log('\n' + '='.repeat(78));
console.log('J · EIGHT HOMEOWNER BUDGET SIMULATIONS');
const WALLET = [8000,15000,25000,35000,45000,60000,80000,120000];
const pick = (bands,wallet) => Object.entries(bands).find(([k,b]) => wallet >= b.lo && wallet <= b.hi);
for (const w of WALLET) {
  const [ok,ob] = pick(LIVE_BANDS,w), [nk,nb] = pick(SHADOW_BUDGET_BANDS,w);
  const om = eur.filter(x=>liveBudgetFit(x,ob)===2), nm = eur.filter(x=>shadowBudgetFit(x,nb)===2);
  const lost = om.filter(x=>!nm.includes(x)), gained = nm.filter(x=>!om.includes(x));
  const hi = a => a.length ? f(Math.max(...a.map(x=>x.price))) : '-';
  console.log('\n  €%s homeowner', f(w));
  console.log('    LIVE      ' + LIVE_LABEL[ok].padEnd(18) + String(om.length).padStart(3) + ' products / ' + String(orgs(om)).padStart(2) + ' suppliers   dearest in-budget €' + hi(om));
  console.log('    PROPOSED  ' + SHADOW_BUDGET_LABEL[nk].padEnd(18) + String(nm.length).padStart(3) + ' products / ' + String(orgs(nm)).padStart(2) + ' suppliers   dearest in-budget €' + hi(nm));
  if (lost.length)   console.log('      no longer claimed in budget: %d  (up to €%s)', lost.length, hi(lost));
  if (gained.length) console.log('      newly claimed in budget:     %d', gained.length);
  const sup = om.filter(x=>x.priceSafeForMatching===false);
  if (sup.length) console.log('      unsafe prices the live journey counts as in budget: %d  (%s)',
    sup.length, sup.map(x=>'€'+f(x.price)).join(', '));
}
