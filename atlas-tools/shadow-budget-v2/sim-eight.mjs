/* EIGHT HOMEOWNER SIMULATIONS — current four bands vs shadow five bands.
   Read-only. Uses the shadow universe, which is the 477-product operative
   universe plus the 13 contract fields and NO new Atlas evidence. */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { SHADOW_BUDGET_BANDS, shadowBudgetFit, renderShadowPrice } from './shadow-budget-bands.mjs';
const HERE = dirname(fileURLToPath(import.meta.url));
const P = JSON.parse(readFileSync(join(HERE,'shadow-recommendation-universe-v2.json'))).products;

/* the CURRENT live map, exactly as your-plot.html declares it */
const CURRENT = { 'under-10k':{lo:0,hi:10000}, '10k-20k':{lo:10000,hi:20000},
                  '20k-30k':{lo:20000,hi:30000}, '30k-plus':{lo:30000,hi:Infinity} };
const eur = p => p.price != null && (p.currency||'EUR')==='EUR';
/* CURRENT behaviour: no safety gate — a price is a price */
const curIn = (p,b) => eur(p) && p.price >= CURRENT[b].lo && p.price <= CURRENT[b].hi;
/* SHADOW behaviour: band membership AND the safety gate */
const shIn = (p,b) => shadowBudgetFit(p, SHADOW_BUDGET_BANDS[b]) === 2;
const pick = w => Object.keys(CURRENT).find(b => w>=CURRENT[b].lo && w<=CURRENT[b].hi);
const pickS = w => Object.keys(SHADOW_BUDGET_BANDS).find(b => { const x=SHADOW_BUDGET_BANDS[b]; return w>=x.lo && w<=x.hi; });
const m = v => '€'+v.toLocaleString('en-IE');
const money = (v,c) => (c==='EUR'?'€':c+' ')+v.toLocaleString('en-IE');
const sup = xs => new Set(xs.map(p=>p.organisation)).size;

for (const w of [8000,15000,25000,35000,45000,60000,80000,120000]) {
  const cb=pick(w), sb=pickS(w);
  const c=P.filter(p=>curIn(p,cb)), s=P.filter(p=>shIn(p,sb));
  const cmax=c.length?Math.max(...c.map(p=>p.price)):0, smax=s.length?Math.max(...s.map(p=>p.price)):0;
  console.log('\n'+'='.repeat(74));
  console.log('  HOMEOWNER WITH '+m(w));
  console.log('    CURRENT   band '+cb.padEnd(10)+'  '+String(c.length).padStart(3)+' products / '+sup(c)+' suppliers   dearest '+m(cmax)+'   overshoot '+(cmax/w).toFixed(1)+'x');
  console.log('    SHADOW    band '+sb.padEnd(10)+'  '+String(s.length).padStart(3)+' products / '+sup(s)+' suppliers   dearest '+m(smax)+'   overshoot '+(smax/w).toFixed(1)+'x');
  const dropped=c.filter(p=>!s.includes(p));
  const unsafe=c.filter(p=>p.priceSafeForMatching===false);
  console.log('    dropped by SHADOW: '+dropped.length+'   of which unsafe prices CURRENT counts as in budget: '+unsafe.length);
  if ([35000,45000,60000].includes(w)) {
    console.log('\n    --- CURRENT shows these (dearest 6), named ---');
    c.slice().sort((a,b)=>b.price-a.price).slice(0,6).forEach(p=>
      console.log('      '+m(p.price).padStart(9)+'  '+(p.priceSafeForMatching===false?'UNSAFE ':'       ')+p.organisation.slice(0,24).padEnd(25)+p.name.slice(0,34)));
    console.log('    --- SHADOW shows these (dearest 6), named ---');
    s.slice().sort((a,b)=>b.price-a.price).slice(0,6).forEach(p=>
      console.log('      '+renderShadowPrice(p,money).split('\n')[0].padStart(11)+'  '+renderShadowPrice(p,money).split('\n')[1].slice(0,38).padEnd(39)+'  '+p.organisation.slice(0,24).padEnd(25)+p.name.slice(0,34)));
    if(!s.length) console.log('      (none)');
  }
}
