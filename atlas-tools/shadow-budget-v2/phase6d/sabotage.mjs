/* PHASE 6D · SABOTAGE PROOF
   Each revised protection is broken once, on a COPY of the genuine candidate,
   and the break must be caught. A guard that cannot fail is a comment. */
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const SRC = 'phase6d/candidate-universe-573.json';
const base = JSON.parse(readFileSync(SRC, 'utf8'));
const tmp = mkdtempSync(join(tmpdir(), 'p6d-'));
let caught = 0, missed = 0;

function run(suite, file) {
  try { execSync(`node ${suite} ${file}`, { stdio: 'pipe', encoding: 'utf8' }); return 0; }
  catch (e) { return 1; }                       // non-zero exit = at least one FAIL
}
function sabotage(label, suite, mutate) {
  const u = JSON.parse(JSON.stringify(base));
  mutate(u);
  const f = join(tmp, 'mutant.json');
  writeFileSync(f, JSON.stringify(u));
  const failed = run(suite, f);
  if (failed) { caught++; console.log('  CAUGHT   ' + label); }
  else        { missed++; console.log('  MISSED   ' + label + '   <-- the guard did not fire'); }
}
const S1 = 'prove-shadow-budget.mjs', S3 = 'phase5/prove-phase6b-locks.mjs';

console.log('\nSABOTAGE · revised G9 — governed token / fail-closed');
sabotage('G9: a product claims a basis class with NO governed token', S1,
  u => { const p = u.products.find(x => x.priceBasisClass !== 'UNKNOWN');
         p.priceEvidenceRef.basisLeadPhrase = null; });
sabotage('G9: the governed token maps to the WRONG axis', S1,
  u => { const p = u.products.find(x => x.priceEvidenceRef.basisLeadPhrase === 'TURNKEY INSTALLATION INCLUDED');
         p.priceBasisAxes.erection = 'EXCLUDED'; });
sabotage('G9: unmatched prose does NOT fail closed', S1,
  u => { const p = u.products.find(x => !x.priceEvidenceRef.basisLeadPhrase);
         p.priceBasisClass = 'ERECTED_WITH_SERVICES'; });

console.log('\nSABOTAGE · revised G10 — provenance and the deprecated alias');
sabotage('G10: a product loses its governed priceEvidenceRef', S1,
  u => { delete u.products[0].priceEvidenceRef; });
sabotage('G10: priceEvidenceRef loses a required key', S1,
  u => { delete u.products[0].priceEvidenceRef.adjudication; });
sabotage('G10: sourceKind is no longer airtable-live', S1,
  u => { u.sourceKind = 'offline-snapshot'; delete u.provenance; delete u.shadow; });
sabotage('G10: governedDigest is truncated', S1,
  u => { u.governedDigest = 'deadbeef'; delete u.provenance; delete u.shadow; });
sabotage('G10: the candidate cites the retired curated axes file', S1,
  u => { u.basisAxesFile = 'price-basis-axes-v1.json'; });
sabotage('G10: priceStatus is removed (canonical field gone)', S1,
  u => { u.products.forEach(p => { delete p.priceStatus; }); });
sabotage('G10: a status value leaks into the basis vocabulary', S1,
  u => { u.products[0].priceBasis = 'KIT_SELF_ASSEMBLY'; });

console.log('\nSABOTAGE · revised L2.4 — organisation identity');
sabotage('L2.4: Ecohouse and Loghouse merged into one organisation', S3,
  u => { u.products.forEach(p => { if (/loghouse/i.test(p.organisation)) p.organisation = 'Ecohouse Building Systems'; }); });
sabotage('L2.4: Garden Rooms identity renamed away', S3,
  u => { u.products.forEach(p => { if (p.organisation === 'Garden Rooms') p.organisation = 'Garden Rooms Ltd'; }); });
sabotage('L2.4: organisationCount disagrees with the organisations present', S3,
  u => { u.organisationCount = 99; });

console.log('\nSABOTAGE · revised L3.1 — product identity');
sabotage('L3.1: a duplicate canonical product ID appears', S3,
  u => { u.products[1].productId = u.products[0].productId; });
sabotage('L3.1: a product loses its canonical ID', S3,
  u => { delete u.products[0].productId; });
sabotage('L3.1: invented per-model Garden Rooms products appear', S3,
  u => { const g = u.products.find(p => p.organisation === 'Garden Rooms');
         u.products.push({ ...g, productId: 'recINVENTED1', productName: 'CUBE 17' }); });
sabotage('L3.1: Ecohouse acquires a price (rejected work reintroduced)', S3,
  u => { const e = u.products.find(p => /ecohouse/i.test(p.organisation)); e.price = 13299; });

rmSync(tmp, { recursive: true, force: true });
console.log('\n' + '='.repeat(78));
console.log(`  ${caught} sabotages CAUGHT, ${missed} MISSED`);
console.log('='.repeat(78));
process.exit(missed ? 1 : 0);
