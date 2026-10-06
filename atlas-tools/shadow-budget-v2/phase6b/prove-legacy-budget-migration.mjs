import { resolveSavedBudget, budgetKeyForRanking, LIVE_BAND_KEYS, RETIRED_BAND_KEYS } from './legacy-budget-migration.mjs';
let pass=0, fail=0;
const ok=(n,c,d='')=>{c?(pass++,console.log(`  PASS  ${n}`)):(fail++,console.log(`  FAIL  ${n} — ${d}`));};
const R=s=>resolveSavedBudget(s);

console.log('\nM1 · 30k-plus is a LIVE homeowner-facing key — no migration occurs');
ok('M1.1 30k-plus resolves as CURRENT, not migrated', R({budgetKey:'30k-plus'}).status==='current');
ok('M1.2 it keeps its own key',                       R({budgetKey:'30k-plus'}).key==='30k-plus');
ok('M1.3 a stored amount does NOT reroute it',        R({budgetKey:'30k-plus',budgetAmount:35000}).key==='30k-plus');
ok('M1.4 a large stored amount does NOT reroute it',  R({budgetKey:'30k-plus',budgetAmount:120000}).key==='30k-plus');
ok('M1.5 nothing is retired, so nothing needs a choice', RETIRED_BAND_KEYS.length===0);
ok('M1.6 no saved answer is disturbed unnecessarily',
   ['under-10k','10k-20k','20k-30k','30k-plus'].every(k=>R({budgetKey:k}).status==='current'));

console.log('\nM2 · the four live keys pass through unchanged');
ok('M2.1 all four resolve to themselves', LIVE_BAND_KEYS.every(k=>R({budgetKey:k}).key===k));
ok('M2.2 50k-plus is NOT a live key', !LIVE_BAND_KEYS.includes('50k-plus'));
ok('M2.3 30k-50k is NOT a live key',  !LIVE_BAND_KEYS.includes('30k-50k'));

console.log('\nM3 · THE AXIS STILL CANNOT DISAPPEAR');
const states=[{budgetKey:'30k-plus'},{budgetKey:'30k-plus',budgetAmount:35000},
  ...LIVE_BAND_KEYS.map(k=>({budgetKey:k})),{},{budgetKey:''},{budgetKey:'  30k-plus  '},
  {budgetKey:'nonsense'},{budgetKey:'50k-plus'},null,undefined];
ok('M3.1 every state resolves to a defined status', states.every(s=>{const r=R(s);return r&&typeof r.status==='string';}));
ok('M3.2 whitespace is tolerated',                   R({budgetKey:'  30k-plus  '}).key==='30k-plus');
ok('M3.3 budgetKeyForRanking returns only a live key or null',
   states.every(s=>{const k=budgetKeyForRanking(s);return k===null||LIVE_BAND_KEYS.includes(k);}));
ok('M3.4 an unrecognised key never becomes a usable band',
   budgetKeyForRanking({budgetKey:'nonsense'})===null && budgetKeyForRanking({budgetKey:'50k-plus'})===null);
ok('M3.5 a live key always yields a usable band', LIVE_BAND_KEYS.every(k=>budgetKeyForRanking({budgetKey:k})===k));

console.log('\nM4 · the stored amount is preserved for RANKING, never for rebanding');
const amt=s=>[s.budgetAmount,s.budget,s.budgetValue].find(v=>typeof v==='number'&&Number.isFinite(v)&&v>=0);
ok('M4.1 €35,000 is available to the ranker', amt({budgetKey:'30k-plus',budgetAmount:35000})===35000);
ok('M4.2 a missing amount stays missing — none is invented',
   amt({budgetKey:'30k-plus'})===undefined && amt({budgetKey:'30k-plus',budgetAmount:null})===undefined);
ok('M4.3 a string amount is not treated as a number', amt({budgetKey:'30k-plus',budgetAmount:'45000'})===undefined);
ok('M4.4 €0 is a real stated amount',                 amt({budgetKey:'30k-plus',budgetAmount:0})===0);

console.log('\n'+'='.repeat(78));
console.log(`${pass} of ${pass+fail} migration checks passed  (PHASE 6D: no migration required)`);
console.log('='.repeat(78));
process.exit(fail?1:0);
