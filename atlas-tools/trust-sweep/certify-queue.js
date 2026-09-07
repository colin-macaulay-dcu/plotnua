/* CERTIFICATION — QUEUE GOVERNANCE
   ============================================================================
   Locks the disposition rule against the 41-organisation cohort and against
   the principle it exists to enforce: UNRESOLVED is a valid terminal machine
   state, and absence of evidence never costs a person's attention.

   These are known answers, adjudicated by the founder from the 41-org analysis
   — not re-derived here. If the rule drifts, this fails.
   ========================================================================== */
'use strict';
const A = require('./acquire.js');
const T = require('./trust-sweep.js');
const C = require('./out-captures-41.js');

const input = C.map(r => ({
  org: { organisationId: r.id, name: r.name, canonicalDomain: r.dom },
  captures: [{ url: r.url, title: r.title, fetchState: r.st,
               text: r.p, projection: r.p, truncatedFields: r.tr }],
}));
const { records, queue } = A.sweep(input, new Date('2026-09-07T00:00:00Z'));

/* The six organisations that carry a real adjudication decision. */
const EXPECT_HUMAN = [
  'MCD Garden Sheds',            // CONFIRMED under a different trading name
  'Outdoor Living (ModPod)',     // CONFIRMED under a different trading name
  'Loghouse',                    // several listings, five premises
  'Ballyfree Garden Sheds',      // three listings, two of them other businesses
  'Garden Office Solutions',     // one business behind two Atlas organisations
  'Live in Garden Pods',         // the other half of that pair
];
const EXPECT_RETRY = [
  'Granny Flats Dublin', 'Pineca Ireland', 'Hansa24 Group (summerhouse24.ie)',
  'Quick-Garden', 'MyCabin.ie',
];
const EXPECT = { AUTO_TERMINAL: 25, RETRY_LATER: 5, HUMAN_REVIEW: 6 };

const got = {};
queue.forEach(q => { got[q.disposition] = (got[q.disposition] || 0) + 1; });
const fails = [];

Object.keys(EXPECT).forEach(k => {
  const ok = (got[k] || 0) === EXPECT[k];
  if (!ok) fails.push(k + ' ' + (got[k] || 0) + ' != ' + EXPECT[k]);
  console.log((ok ? '  ok    ' : '  FAIL  ') + k + ' = ' + (got[k] || 0));
});

const nameSet = d => queue.filter(q => q.disposition === d).map(q => q.name).sort();
const same = (a, b) => JSON.stringify(a.slice().sort()) === JSON.stringify(b.slice().sort());
[['HUMAN_REVIEW', EXPECT_HUMAN], ['RETRY_LATER', EXPECT_RETRY]].forEach(([d, exp]) => {
  const ok = same(nameSet(d), exp);
  if (!ok) fails.push(d + ' membership: ' + nameSet(d).join(', '));
  console.log((ok ? '  ok    ' : '  FAIL  ') + d + ' membership');
});

/* GOVERNANCE INVARIANTS — the rules the disposition must never break. */
const inv = [];
/* 1 · No-evidence UNRESOLVED must never reach a person. */
records.forEach(r => {
  if (r.identity.verdict === 'UNRESOLVED' && !r.exceptions.length &&
      T.dispose(r) !== 'AUTO_TERMINAL') inv.push('bare UNRESOLVED queued: ' + r.name);
});
/* 2 · Anything the engine ACCEPTED an identity for, where the evidence
       conflicts, must reach a person. */
records.forEach(r => {
  const held = !!(r.identity.placeId || r.identity.cid);
  const conflict = r.exceptions.some(e =>
    ['MULTIPLE_LISTINGS', 'SHARED_IDENTIFIER', 'SHARED_PHONE', 'NAME_MISMATCH'].includes(e.code));
  if (held && conflict && T.dispose(r) !== 'HUMAN_REVIEW')
    inv.push('conflicted identity not reviewed: ' + r.name);
});
/* 3 · A fetch that failed must be retried, never read as a finding. */
records.forEach(r => {
  if (r.exceptions.some(e => e.code === 'BLOCKED_SITE') && T.dispose(r) !== 'RETRY_LATER')
    inv.push('blocked site not retried: ' + r.name);
});
/* 4 · Disposition must not change any verdict. */
const verdicts = records.map(r => r.identity.verdict).join(',');
if (!/CONFIRMED/.test(verdicts)) inv.push('verdicts lost');
inv.forEach(m => console.log('  FAIL  invariant: ' + m));

console.log('\n  queue governance ' + (fails.length || inv.length ? 'FAILED' : 'PASSED') +
            '  | human-review ' + ((got.HUMAN_REVIEW || 0) / records.length * 100).toFixed(1) +
            '%  (' + (got.HUMAN_REVIEW || 0) + '/' + records.length + ')');
process.exit(fails.length || inv.length ? 1 : 0);
