/* PHASE 6B LOCK GUARD
   Turns the founder's four locked corrections into executable proofs. These are
   ADDITIONS to the 48. They never relax an existing guard. */
import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const CAND = process.argv[2] || 'phase5/candidate-universe-shadow.json';
const U = JSON.parse(readFileSync(CAND, 'utf8'));
const P = U.products;
let pass = 0, fail = 0;
const ok = (n, c, d = '') => { c ? (pass++, console.log(`  PASS  ${n}`)) : (fail++, console.log(`  FAIL  ${n} — ${d}`)); };

// The seven figures that were NOT verified and NOT written.
const REJECTED = [13299, 17969, 19049, 20049, 22099, 24179, 32499];
const orgOf = n => P.filter(p => (p.organisation || '').toLowerCase().includes(n));
const orgExact = n => P.filter(p => p.organisation === n);  // 5 suppliers contain 'Garden Rooms'
const eco = orgOf('ecohouse'), log = orgOf('loghouse'), gr = orgExact('Garden Rooms');

console.log('\nLOCK 1 · ECOHOUSE — the seven rejected prices must not reappear');
const anyRejected = P.filter(p => REJECTED.includes(p.price));
ok('L1.1 no product in the candidate carries any rejected figure', anyRejected.length === 0,
   anyRejected.map(p => `${p.name}=${p.price}`).join(', '));
ok('L1.2 Ecohouse products exist but none is priced', eco.length > 0 && eco.every(p => p.price == null),
   `${eco.length} products, priced: ${eco.filter(p => p.price != null).length}`);
// Any overlay / snapshot / fixture on disk that could reintroduce them.
const roots = ['phase5', '.'];
let reintro = [];
for (const r of roots) for (const f of (existsSync(r) ? readdirSync(r) : [])) {
  const p = join(r, f);
  if (!statSync(p).isFile() || !/\.(json|mjs|js|py)$/.test(f)) continue;
  if (f === 'prove-phase6b-locks.mjs') continue;  // this guard must name them to test for them
  const t = readFileSync(p, 'utf8');
  for (const v of REJECTED) if (new RegExp(`\\b${v}\\b`).test(t)) reintro.push(`${p}:${v}`);
}
ok('L1.3 no overlay, snapshot or fixture on disk contains a rejected figure',
   reintro.length === 0, reintro.join(', '));

console.log('\nLOCK 2 · ECOHOUSE / LOGHOUSE — distinct, no reseller claim');
ok('L2.1 both organisations present and distinct', eco.length > 0 && log.length > 0 &&
   new Set([...eco, ...log].map(p => p.organisation)).size === 2);
ok('L2.2 no product moved between the two organisations', eco.every(p => !log.includes(p)));
const prose = JSON.stringify(U).toLowerCase();
const banned = ['reseller margin', 'manufacturer→reseller', 'manufacturer->reseller',
                '12% dearer', 'approximately 12%', 'reseller of', 'white-label'];
const hits = banned.filter(b => prose.includes(b));
ok('L2.3 candidate asserts no reseller / margin relationship', hits.length === 0, hits.join(', '));
/* PHASE 6D REVISION OF L2.4.
   BEFORE: organisationCount === 65, a number pinned to the 477-product
   projection. The genuine universe has 64, so the figure was stale — but the
   LOCK's intent was "no organisation was merged", which a count cannot prove
   on its own. AFTER: that intent is asserted structurally. */
const orgNames = new Set(P.map(p => p.organisation).filter(Boolean));
ok('L2.4a Ecohouse and Loghouse are still two distinct organisations',
   new Set(eco.map(p => p.organisation)).size === 1 &&
   new Set(log.map(p => p.organisation)).size === 1 &&
   eco[0].organisation !== log[0].organisation,
   (eco[0]||{}).organisation + ' / ' + (log[0]||{}).organisation);
ok('L2.4b Garden Rooms organisation identity is intact (exact name, not merged away)',
   orgNames.has('Garden Rooms') && orgExact('Garden Rooms').length > 0);
ok('L2.4c the five similarly-named suppliers were NOT merged into one',
   [...orgNames].filter(n => /garden rooms/i.test(n)).length >= 5,
   String([...orgNames].filter(n => /garden rooms/i.test(n)).length));
ok('L2.4d organisationCount agrees with the distinct organisations actually present',
   U.organisationCount === orgNames.size,
   'declared ' + U.organisationCount + ' vs present ' + orgNames.size);

console.log('\nLOCK 3 · GRANULARITY — no new Products, no conflicting Verified records');
/* PHASE 6D REVISION OF L3.1.
   BEFORE: products === 477, pinned to the stale operative artefact. The real
   universe is 573 because Atlas grew, not because Phase 6A created products.
   AFTER: the intent -- Phase 6A created no Product records -- is asserted
   structurally and is not satisfiable by editing a constant. */
const ids = P.map(p => p.productId).filter(Boolean);
ok('L3.1a every product has a canonical productId', ids.length === P.length,
   ids.length + ' of ' + P.length);
ok('L3.1b no duplicate canonical product IDs', new Set(ids).size === ids.length,
   String(ids.length - new Set(ids).size) + ' duplicates');
ok('L3.1c product count equals unique canonical IDs', P.length === new Set(ids).size);
const grAll = orgExact('Garden Rooms');
ok('L3.1d Garden Rooms holds its RANGE products, not invented per-model products',
   grAll.length === 3 && grAll.filter(p => /Range$/.test(p.productName)).length === 2
   && !grAll.some(p => /CUBE (17|20|23|25)|ULTIMATE (20|23|25|27)/i.test(p.productName)),
   grAll.map(p => p.productName).join(' | '));
ok('L3.1e Shomera holds Range products, not per-model Shomera 12/14/18/21/23/25',
   !orgExact('Shomera').some(p => /Shomera (12|14|18|21|23|25)\b/.test(p.productName)));
ok('L3.1f the rejected Ecohouse pricing work created no product records',
   eco.every(p => p.price == null) && eco.length > 0,
   eco.length + ' Ecohouse products, ' + eco.filter(p => p.price != null).length + ' priced');
const ambNow = new Set(P.filter(p => p.priceEvidenceRef?.adjudication === 'ambiguous').map(p => p.name));
const BASE = 'phase5/candidate-universe-production.json';
const ambWas = new Set(JSON.parse(readFileSync(BASE, 'utf8')).products
  .filter(p => p.priceEvidenceRef?.adjudication === 'ambiguous').map(p => p.name));
const introduced = [...ambNow].filter(n => !ambWas.has(n));
ok(`L3.2 Phase 6A introduced no NEW ambiguity (${ambNow.size} pre-existing, unchanged)`,
   introduced.length === 0 && ambNow.size === ambWas.size, introduced.join(', '));
const grPriced = gr.filter(p => p.price != null);
ok('L3.3 Garden Rooms priced via Range products only, one record each',
   grPriced.length === 2 && grPriced.every(p => p.priceEvidenceRef.candidateCount === 1 &&
     /Range$/.test(p.name)), grPriced.map(p => `${p.name}:${p.priceEvidenceRef.candidateCount}`).join(', '));
ok('L3.4 ULTIMATE 27 is not a governed price (51000 / 57885 absent as numbers)',
   !P.some(p => [51000, 57885].includes(p.price)) &&
   !P.some(p => [51000, 57885].includes(p.priceTo)));

console.log('\nLOCK 4 · VAT — status only, no rate, no inference');
ok('L4.1 vatRate is null on every product', P.every(p => p.vatRate == null),
   String(P.filter(p => p.vatRate != null).length));
ok('L4.2 Garden Rooms priced ranges carry vatStatus = Yes',
   grPriced.every(p => p.vatStatus === 'Yes'), grPriced.map(p => p.vatStatus).join(','));
ok('L4.3 Shomera remains vatStatus Unknown — not inferred',
   orgOf('shomera').filter(p => p.price != null).every(p => p.vatStatus === 'Unknown'));
const vatVals = new Set(P.map(p => p.vatStatus).filter(Boolean));
ok('L4.4 vatStatus vocabulary closed to Yes / No / Unknown',
   [...vatVals].every(v => ['Yes', 'No', 'Unknown'].includes(v)), [...vatVals].join(','));

console.log('\n' + '='.repeat(78));
console.log(`${pass} of ${pass + fail} lock checks passed`);
console.log('='.repeat(78));
process.exit(fail ? 1 : 0);
