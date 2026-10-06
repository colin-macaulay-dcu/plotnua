/* G12 — GENERATED ARTEFACT INTEGRITY, plus the promotion gate.
   Every rule is broken once and the break must be caught. Read-only with
   respect to Atlas, the live page and the operative universe. */
import { readFileSync, writeFileSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const HERE = dirname(fileURLToPath(import.meta.url));
const CAND = join(HERE, 'candidate-universe-shadow.json');
const GEN  = join(HERE, 'build-candidate-universe.py');
const results = [];
function t(label, fn) {
  let ok=false, note='';
  try { const r=fn(); ok = r===true; note = r===true?'':String(r); }
  catch(e){ ok=false; note='threw: '+e.message; }
  results.push(ok);
  console.log('  '+(ok?'PASS   ':'FAIL   ')+label+(note?'\n           -> '+note:''));
}
function sab(label, fn) {
  let caught=false, note='';
  try { const r=fn(); caught = r===true; note = r===true?'':String(r); }
  catch(e){ caught=false; note='threw: '+e.message; }
  results.push(caught);
  console.log('  '+(caught?'CAUGHT ':'MISSED ')+label+(note?'\n           -> '+note:''));
}

const U = JSON.parse(readFileSync(CAND));
const GOVERNED = U.governedFields;

/* The digest is recomputed by the GENERATOR's own canonical implementation via
   --verify. A second implementation in another language drifted on JSON key
   order and float/serialisation details, which would have made the proof depend
   on an accident rather than on the data. One implementation, invoked twice. */
function verify(file){
  try { return { ok:true,  out: execFileSync('python3',[GEN,'--verify',file],{encoding:'utf8'}) }; }
  catch(e){ return { ok:false, out: ((e.stdout||'')+(e.stderr||'')) }; }
}
function mutantFile(mutate){
  const m = JSON.parse(readFileSync(CAND)); mutate(m);
  const f = join(HERE,'__mutant__.json'); writeFileSync(f, JSON.stringify(m)); return f;
}

console.log('G12 — GENERATED ARTEFACT INTEGRITY + PROMOTION GATE');
console.log('='.repeat(78));

t('G12 . the candidate declares a governed digest and a governed field list', () =>
  (typeof U.governedDigest === 'string' && U.governedDigest.length === 64
   && Array.isArray(GOVERNED) && GOVERNED.length === 13)
   ? true : 'the candidate carries no usable integrity declaration');

t('G12 . the declared digest matches a recomputation from the artefact itself', () => {
  const r = verify(CAND);
  return r.ok && /INTEGRITY OK/.test(r.out) ? true : r.out.trim().slice(0,140);
});

sab('G12 SABOTAGE . a governed field changed after generation is detected', () => {
  const f = mutantFile(m => {
    const i = m.products.findIndex(p => p.priceSafeForMatching === false);
    m.products[i].priceSafeForMatching = true;           // the exact class of edit that matters
  });
  const r = verify(f); rmSync(f,{force:true});
  return (!r.ok && /INTEGRITY FAIL/.test(r.out)) ? true : 'the mutation went undetected';
});

sab('G12 SABOTAGE . the Power Sheds mutation class is detected if reintroduced', () => {
  const f = mutantFile(m => {
    const i = m.products.findIndex(p => p.productId === 'recLcmGihJ0mrfdwV');
    /* exactly what 7f49c0e did: flip adjudication, keep the number */
    m.products[i].priceEvidenceRef.adjudication = 'ambiguous';
    m.products[i].priceEvidenceRef.candidateCount = 2;
  });
  const r = verify(f); rmSync(f,{force:true});
  return (!r.ok && /INTEGRITY FAIL/.test(r.out)) ? true : 'reintroducing the 29 Sep mutation went undetected';
});

t('G12 . the digest is scoped to governed fields, not the whole file', () => {
  const f = mutantFile(m => {
    m.products[0].glazing = 'CHANGED BY AN UNRELATED PIECE OF WORK';
    m.generated = '1999-01-01T00:00:00Z';
  });
  const r = verify(f); rmSync(f,{force:true});
  return (r.ok && /INTEGRITY OK/.test(r.out))
    ? true : 'ungoverned churn broke the digest, so the proof would be brittle';
});

t('G12 . no ambiguous row in the candidate retains a number', () => {
  const bad = U.products.filter(p => (p.priceEvidenceRef||{}).adjudication === 'ambiguous'
                                     && p.price !== null && p.price !== undefined);
  return bad.length === 0 ? true : bad.length + ' ambiguous rows still hold a figure: '
    + bad.map(p=>p.name).slice(0,3).join(', ');
});

t('G12 . the three Power Sheds rows are adjudicated, euro, single-candidate', () => {
  const ids = ['recLcmGihJ0mrfdwV','recYM6hUVXceIrmmv','recrmlUXvX9TbgTj7'];
  const rows = U.products.filter(p => ids.includes(p.productId));
  if (rows.length !== 3) return 'expected 3 Power Sheds rows, saw ' + rows.length;
  const bad = rows.filter(p => p.currency !== 'EUR'
      || (p.priceEvidenceRef||{}).adjudication !== 'adjudicated'
      || (p.priceEvidenceRef||{}).candidateCount !== 1
      || !(p.priceRecordIds||[]).length);
  return bad.length === 0 ? true : bad.length + ' Power Sheds rows are not correctly resolved';
});

/* ── PROMOTION GATE ───────────────────────────────────────────────────── */
console.log('\n  promotion gate (a mutant generator; nothing is promoted)');
function gate(label, from, to, mode, expectRefusal) {
  const src = readFileSync(GEN,'utf8');
  if (!src.includes(from)) { results.push(false); console.log('  FAIL   '+label+'\n           -> anchor absent'); return; }
  const f = join(HERE,'__gate_sabotage__.py');
  writeFileSync(f, src.replace(from,to));
  let refused=false, out='';
  try { out = execFileSync('python3',[f,'--mode',mode,'--out',join(HERE,'__gate_out__.json')],{encoding:'utf8',cwd:HERE}); }
  catch(e){ refused=true; out=((e.stdout||'')+(e.stderr||'')); }
  rmSync(f,{force:true}); rmSync(join(HERE,'__gate_out__.json'),{force:true});
  const sawRefusal = /PROMOTION REFUSED/.test(out);
  const ok = expectRefusal ? (refused && sawRefusal) : (!refused);
  results.push(ok);
  console.log('  '+(ok?(expectRefusal?'CAUGHT ':'PASS   '):'MISSED ')+label
    + '\n           -> '+(out.split('\n').find(l=>l.trim())||'').slice(0,100));
}
gate('G12 GATE . production REFUSES when a validation check fails',
     '"product_count_preserved":      len(products)==len(base["products"]),',
     '"product_count_preserved":      False,', 'production', true);
gate('G12 GATE . shadow still BUILDS when validation fails (so it can be inspected)',
     '"product_count_preserved":      len(products)==len(base["products"]),',
     '"product_count_preserved":      False,', 'shadow', false);
gate('G12 GATE . production REFUSES if an ambiguous row regains a price',
     '"no_ambiguous_row_retains_price": all(',
     '"no_ambiguous_row_retains_price": False and all(', 'production', true);

console.log('\n'+'='.repeat(78));
const pass = results.filter(Boolean).length;
console.log(pass+' of '+results.length+' checks passed');
process.exit(pass===results.length?0:1);
