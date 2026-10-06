/* EIGHT SIMULATIONS — CURRENT LIVE (four bands, no safety gate, operative
   artefact) vs NEWLY GENERATED CANDIDATE (five bands, safety gate, Power Sheds
   corrected). The candidate is NOT live. */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { SHADOW_BUDGET_BANDS, shadowBudgetFit, renderShadowPrice } from '../shadow-budget-bands.mjs';
const HERE = dirname(fileURLToPath(import.meta.url));
const LIVE = JSON.parse(readFileSync(join(HERE,'../../../garden-room-recommendation-universe-v1.json'))).products;
const CAND = JSON.parse(readFileSync(join(HERE,'candidate-universe-shadow.json'))).products;
const LIVE_BANDS = { 'under-10k':{lo:0,hi:10000}, '10k-20k':{lo:10000,hi:20000},
                     '20k-30k':{lo:20000,hi:30000}, '30k-plus':{lo:30000,hi:Infinity} };
const eur = p => p.price != null && (p.currency||'EUR')==='EUR';
const money = (v,c) => (c==='EUR'?'€':c+' ')+v.toLocaleString('en-IE');
const m = v => '€'+v.toLocaleString('en-IE');
const sup = xs => new Set(xs.map(p=>p.organisation)).size;
const pick = (b,w) => Object.keys(b).find(k => w>=b[k].lo && w<=b[k].hi);
console.log('CURRENT LIVE (operative artefact, 4 bands, no safety gate)  vs  CANDIDATE (5 bands, gated)');
for (const w of [8000,15000,25000,35000,45000,60000,80000,120000]) {
  const lb=pick(LIVE_BANDS,w), cb=pick(SHADOW_BUDGET_BANDS,w);
  const L=LIVE.filter(p=>eur(p)&&p.price>=LIVE_BANDS[lb].lo&&p.price<=LIVE_BANDS[lb].hi);
  const C=CAND.filter(p=>shadowBudgetFit(p,SHADOW_BUDGET_BANDS[cb])===2);
  const lmax=L.length?Math.max(...L.map(p=>p.price)):0, cmax=C.length?Math.max(...C.map(p=>p.price)):0;
  console.log('\n'+'='.repeat(78));
  console.log('  '+m(w)+' HOMEOWNER');
  console.log('    LIVE       '+lb.padEnd(10)+String(L.length).padStart(3)+' products / '+sup(L)+' suppliers   dearest '+m(lmax)+'   '+(lmax/w).toFixed(1)+'x');
  console.log('    CANDIDATE  '+cb.padEnd(10)+String(C.length).padStart(3)+' products / '+sup(C)+' suppliers   dearest '+m(cmax)+'   '+(cmax/w).toFixed(1)+'x');
  const lids=new Set(L.map(p=>p.productId)), cids=new Set(C.map(p=>p.productId));
  const gained=C.filter(p=>!lids.has(p.productId)), lost=L.filter(p=>!cids.has(p.productId));
  if (gained.length) console.log('    GAINED by the candidate: '+gained.map(p=>p.name.slice(0,30)+' '+money(p.price,p.currency)).join(' | '));
  console.log('    dropped: '+lost.length);
  if ([35000,45000,60000].includes(w)) {
    console.log('    --- CANDIDATE shows (dearest 6) ---');
    C.slice().sort((a,b)=>b.price-a.price).slice(0,6).forEach(p=>{
      const r=renderShadowPrice(p,money).split('\n');
      console.log('      '+r[0].padStart(12)+'  '+(r[1]||'').slice(0,40).padEnd(41)+p.organisation.slice(0,22));
    });
  }
}
