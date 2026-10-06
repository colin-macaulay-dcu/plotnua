import { readFileSync } from 'node:fs';
import { SHADOW_BUDGET_BANDS, shadowBudgetFit } from '../shadow-budget-bands.mjs';
const P6 = JSON.parse(readFileSync('phase5/candidate-universe-shadow.json','utf8')).products;
const P5 = JSON.parse(readFileSync('phase5/candidate-universe-production.json','utf8')).products;
const med = a => { const s=[...a].sort((x,y)=>x-y), m=s.length>>1;
  return s.length%2 ? s[m] : Math.round((s[m-1]+s[m])/2); };
const eur = n => '€' + n.toLocaleString('en-IE');
const KEYS = ['under-10k','10k-20k','20k-30k','30k-50k','50k-plus'];
const LABEL = {'under-10k':'Under €10,000','10k-20k':'€10,000–€20,000','20k-30k':'€20,000–€30,000',
               '30k-50k':'€30,000–€50,000','50k-plus':'€50,000+'};
console.log('F · FIVE-BAND POPULATION (safe matching products only)\n');
console.log('  band                 prod  sup   cheapest     median      dearest');
for (const k of KEYS) {
  const b = SHADOW_BUDGET_BANDS[k];
  const inB = P6.filter(p => shadowBudgetFit(p, b) === 2);
  const pr = inB.map(p => p.price);
  console.log(`  ${LABEL[k].padEnd(20)} ${String(inB.length).padStart(4)} ${String(new Set(inB.map(p=>p.organisation)).size).padStart(4)}   ${eur(Math.min(...pr)).padEnd(11)} ${eur(med(pr)).padEnd(11)} ${eur(Math.max(...pr))}`);
}
const band5 = k => new Set(P5.filter(p => shadowBudgetFit(p, SHADOW_BUDGET_BANDS[k]) === 2).map(p=>p.productId));
const band6 = k => P6.filter(p => shadowBudgetFit(p, SHADOW_BUDGET_BANDS[k]) === 2);
console.log('\n  What Garden Rooms and corrected Shomera add to €30–50k (vs Phase 5):');
const was = band5('30k-50k');
for (const p of band6('30k-50k')) if (!was.has(p.productId))
  console.log(`    + ${p.organisation.padEnd(16)} ${p.name.padEnd(30)} ${eur(p.price)}  ${p.priceIsRangeFloor?'From':'    '}  VAT ${p.vatStatus||'—'}`);
const shom = band6('30k-50k').filter(p => p.organisation === 'Shomera');
console.log('    Shomera already in the band; its correction moves the floor:');
for (const p of shom) console.log(`      = ${p.name.padEnd(30)} ${eur(p.price)} (was ${eur(P5.find(x=>x.productId===p.productId).price)})`);
console.log('\n  What the Big Man withdrawal removes from €50k+:');
const w5 = band5('50k-plus'), w6 = new Set(band6('50k-plus').map(p=>p.productId));
const gone = [...w5].filter(id => !w6.has(id));
console.log(`    Phase 5 €50k+ = ${w5.size} products / Phase 6A = ${w6.size}. Removed: ${gone.length ? gone.join(', ') : 'NONE'}`);
const bm = P5.find(p => p.productId === 'rech2D1aCz41kZtc5');
console.log(`    Big Man in Phase 5 €50k+: ${w5.has('rech2D1aCz41kZtc5') ? 'YES' : 'NO'} — it was already suppressed (safe=${bm.priceSafeForMatching}, ${bm.priceBasisConfidence})`);
console.log('    So the withdrawal removes it from the UNGATED live four-band pool, not from the gated €50k+.');
