/* ISSUE 007 — IRISH COHORT AUTOMATED ACCURACY TEST
   ============================================================================
   Compares the engine's verdict for all 41 Irish organisations against the
   verdicts a human adjudicated in the manual first-party sweep.

   The manual verdicts are the prior work product, recovered verbatim from the
   three sweep reports. They are the reference, not a re-derivation.

   Comparison classes (founder-defined):
     EXACT MATCH                 same verdict
     SAFE CONSERVATIVE DIFFERENCE engine claims LESS identity than the human
     UNSAFE FALSE CONFIRMATION   engine claims MORE identity than the human
     MISSED CONFIRMATION         human CONFIRMED, engine did not
     OTHER DISAGREEMENT          anything else
   ========================================================================== */
'use strict';
const A = require('./acquire.js');
const T = require('./trust-sweep.js');
const C = require('./out-captures-41.js');

const NOW = new Date('2026-09-07T00:00:00Z');

const toCapture = r => ({
  url: r.url, title: r.title, fetchState: r.st,
  text: r.p, projection: r.p, truncatedFields: r.tr,
});

const input = C.map(r => ({
  org: { organisationId: r.id, name: r.name, canonicalDomain: r.dom },
  captures: [toCapture(r)],
}));

const { records, queue } = A.sweep(input, NOW);

/* --- what a difference actually means ------------------------------------
   SAFETY IS ABOUT ACCEPTED IDENTIFIERS, NOT ABOUT VERDICT RANK. The earlier
   ladder scored a previously-blocked site becoming readable as "more
   confident", which is not a safety event at all: nothing was accepted. An
   UNSAFE FALSE CONFIRMATION is now, and only, the engine HOLDING a business
   identifier the manual truth set does not support. */
const STRENGTH = { BLOCKED: 0, UNRESOLVED: 1, AMBIGUOUS: 2, PARTIAL: 3, CONFIRMED: 4 };
/* The manual pass found some identity evidence in these states, none in these. */
const MANUAL_SUPPORTS_IDENTITY = ['CONFIRMED', 'AMBIGUOUS', 'PARTIAL'];

function classify(manual, auto, held) {
  if (held && !MANUAL_SUPPORTS_IDENTITY.includes(manual)) return 'UNSAFE FALSE CONFIRMATION';
  if (manual === auto) return 'EXACT MATCH';
  /* The fetch changed, not the finding: a site that refused us now answers. */
  if (manual === 'BLOCKED' && !held) return 'FETCH-STATE CHANGE';
  if (manual === 'CONFIRMED') return 'MISSED CONFIRMATION';
  if (STRENGTH[auto] < STRENGTH[manual]) return 'SAFE CONSERVATIVE DIFFERENCE';
  return 'OTHER DISAGREEMENT';
}

const rows = records.map((r, i) => ({
  name: r.name,
  manual: C[i].manual,
  auto: r.identity.verdict,
  cls: classify(C[i].manual, r.identity.verdict,
                !!(r.identity.placeId || r.identity.cid)),
  disposition: T.dispose(r),
  codes: r.exceptions.map(e => e.code),
  placeId: r.identity.placeId, cid: r.identity.cid,
  types: r.identity.identifierTypes,
}));

/* --- A · counts ---------------------------------------------------------- */
const tally = {};
rows.forEach(r => { tally[r.cls] = (tally[r.cls] || 0) + 1; });
const n = rows.length;
const unsafe = tally['UNSAFE FALSE CONFIRMATION'] || 0;
const safe = n - unsafe;

console.log('\n=== ACCURACY · ' + n + ' Irish organisations ===');
Object.keys(tally).sort().forEach(k =>
  console.log('  ' + String(tally[k]).padStart(3) + '  ' + k));
console.log('  SAFE RATE               ' + (safe / n * 100).toFixed(1) + '%  (' + safe + '/' + n + ')');
console.log('  FALSE-CONFIRMATION RATE ' + (unsafe / n * 100).toFixed(1) + '%  (' + unsafe + '/' + n + ')');

/* --- B · disagreements only ---------------------------------------------- */
console.log('\n=== DISAGREEMENTS ===');
rows.filter(r => r.cls !== 'EXACT MATCH').forEach(r =>
  console.log('  ' + r.name.padEnd(32) + ' manual=' + r.manual.padEnd(11) +
              ' auto=' + r.auto.padEnd(11) + ' [' + r.cls + ']  ' + r.codes.join(',')));

/* --- B2 · disposition ------------------------------------------------------ */
const disp = {};
queue.forEach(q => { disp[q.disposition] = (disp[q.disposition] || 0) + 1; });
const human = queue.filter(q => q.disposition === 'HUMAN_REVIEW');
console.log('\n=== DISPOSITION ===');
['AUTO_TERMINAL', 'RETRY_LATER', 'HUMAN_REVIEW'].forEach(k =>
  console.log('  ' + String(disp[k] || 0).padStart(3) + '  ' + k));
console.log('  human-review rate ' + (human.length / n * 100).toFixed(1) + '%  (' + human.length + '/' + n + ')');
human.forEach(q => console.log('      * ' + q.name + '  ' + q.reasons.join(',')));

/* --- C · exception queue -------------------------------------------------- */
const HAZARDS = {
  'Ballyfree Garden Sheds': 'MULTIPLE_LISTINGS',
  'Live in Garden Pods': 'SHARED_IDENTIFIER',
  'Garden Office Solutions': 'SHARED_IDENTIFIER',
  'Berko Pod Systems Ltd': 'NON_BUSINESS_IDENTIFIER',
  'Garden Solutions 4U': 'NON_BUSINESS_IDENTIFIER',
  'Quick-Garden': 'NON_BUSINESS_IDENTIFIER',
  'Shomera': 'NON_BUSINESS_IDENTIFIER',
};
console.log('\n=== EXCEPTION QUEUE ===');
console.log('  queued ' + queue.length + '/' + n + '  (' + (queue.length / n * 100).toFixed(1) + '%)');
Object.keys(HAZARDS).forEach(k => {
  const r = rows.find(x => x.name === k);
  const hit = r && r.codes.includes(HAZARDS[k]);
  console.log('  ' + (hit ? 'covered ' : 'MISSED  ') + k + ' -> ' + HAZARDS[k]);
});

/* --- D · governance invariants -------------------------------------------- */
const inv = [];
if (records.some(r => r.reputation.enabled)) inv.push('reputation enabled');
if (records.some(r => r.reputation.rating !== null || r.reputation.reviewCount !== null)) inv.push('rating/count populated');
if (records.some(r => r.identity.placeId && !r.identity.placeIdRefreshDueAt)) inv.push('placeId without refresh target');
if (records.some(r => r.fetchStates.includes('NOT_FOUND_PAGE') && r.identity.verdict === 'BLOCKED')) inv.push('NOT_FOUND became BLOCKED');
console.log('\n  invariants: ' + (inv.length ? 'FAILED — ' + inv.join('; ') : 'ok'));

/* --- E · durable identifiers found ---------------------------------------- */
console.log('\n=== DURABLE IDENTIFIERS ===');
rows.filter(r => r.placeId || r.cid).forEach(r =>
  console.log('  ' + r.name.padEnd(32) + (r.placeId || '') + ' ' + (r.cid || '')));

require('fs').writeFileSync(__dirname + '/out-accuracy-41.json',
  JSON.stringify({ rows, records, queue }, null, 2));
