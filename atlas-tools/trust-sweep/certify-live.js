/* CERTIFICATION — v1.1 ADAPTER, LIVE-ACQUIRED DOM.
   Same known-answer set as certify.js, but the pages come from a real browser
   DOM projection captured by the acquisition adapter — not hand-written
   fixtures. This is what proves the adapter, not just the classifier: the
   Garden Rooms Place ID lives in a data-id attribute that a plain HTML fetch
   strips, and it has to survive acquisition to be found here.
   Captures are the projection defined in acquire.js CAPTURE_SNIPPET. */
'use strict';
const A = require('./acquire.js');
const C = require('./captures-live.json');

const orgs = [
  { org: { organisationId: 'rechco59Sn6wp3Aiq', name: 'Garden Rooms', canonicalDomain: 'www.gardenrooms.ie' },
    expect: { verdict: 'CONFIRMED', placeId: 'ChIJi8YJW2wSZ0gRVWL3QKDZZuc' } },
  { org: { organisationId: 'recZcfloN72CBES6I', name: 'Modern Garden Rooms', canonicalDomain: 'moderngardenrooms.ie' },
    expect: { verdict: 'CONFIRMED', placeId: 'ChIJh_woWH1LZ0gRFhvXEPyKrts' } },
  { org: { organisationId: 'recw124UIanKV5Ath', name: 'Shomera', canonicalDomain: 'www.shomera.ie' },
    expect: { verdictNot: 'CONFIRMED', placeId: null, hasException: 'NON_BUSINESS_IDENTIFIER' } },
  { org: { organisationId: 'rec66sNzKArqeOU23', name: 'Ballyfree Garden Sheds', canonicalDomain: 'ballyfreegardensheds.ie' },
    expect: { verdict: 'AMBIGUOUS', hasException: 'MULTIPLE_LISTINGS' } },
  { org: { organisationId: 'rec0zLenIbn3nsvjh', name: 'Garden Office Solutions', canonicalDomain: 'gardenofficesolutions.ie' },
    expect: { hasException: 'SHARED_PHONE' } },
  { org: { organisationId: 'reczankduIWGWwXKR', name: 'Live in Garden Pods', canonicalDomain: 'liveingardenpods.ie' },
    expect: { hasException: 'SHARED_PHONE' } },
  { org: { organisationId: 'rec7dG4sHJtzstIHo', name: 'Berko Pod Systems Ltd', canonicalDomain: 'berkopodsystems.com' },
    expect: { verdictNot: 'CONFIRMED', placeId: null, hasType: 'CID_REGION' } },
  { org: { organisationId: 'recLQOPHHfSrfs3xA', name: 'Quick-Garden', canonicalDomain: 'www.quick-garden.co.uk' },
    expect: { verdictNot: 'CONFIRMED', placeId: null, hasType: 'MYMAPS', hasException: 'PAGE_NOT_FOUND' } },
];

const input = orgs.map(o => ({ org: o.org, captures: C[o.org.organisationId] || [] }));
const { records, queue } = A.sweep(input, new Date('2026-09-07T00:00:00Z'));

let pass = 0; const fails = [];
records.forEach((r, i) => {
  const e = orgs[i].expect, codes = r.exceptions.map(x => x.code), why = [];
  if (e.verdict && r.identity.verdict !== e.verdict) why.push(`verdict ${r.identity.verdict} != ${e.verdict}`);
  if (e.verdictNot && r.identity.verdict === e.verdictNot) why.push(`wrongly ${e.verdictNot}`);
  if ('placeId' in e && r.identity.placeId !== e.placeId) why.push(`placeId ${r.identity.placeId} != ${e.placeId}`);
  if (e.hasException && !codes.includes(e.hasException)) why.push(`missing ${e.hasException} (got ${codes.join(',') || 'none'})`);
  if (e.hasType && !r.identity.identifierTypes.includes(e.hasType)) why.push(`missing type ${e.hasType}`);
  if (why.length) { fails.push(r.name); console.log('  FAIL  ' + r.name + ' — ' + why.join('; ')); }
  else { pass++; console.log('  ok    ' + r.name + '  [' + r.identity.verdict + '] ' + (codes.join(',') || '-')); }
});

/* fetch-state fidelity: BLOCKED and NOT_FOUND_PAGE must stay distinct */
const states = [].concat(...records.map(r => r.fetchStates));
const distinct = states.includes('NOT_FOUND_PAGE') && !records.some(r =>
  r.fetchStates.includes('NOT_FOUND_PAGE') && r.identity.verdict === 'BLOCKED');
console.log(distinct ? '  ok    NOT_FOUND_PAGE never became BLOCKED'
                     : '  FAIL  fetch states collapsed');


/* GUARD TEST — a truncated capture must never read as clean absence. */
{
  const t = A.assessCaptured(
    { organisationId: 'recTRUNCTEST', name: 'Truncation Probe', canonicalDomain: 'example.ie' },
    [{ url: 'https://example.ie/contact/', title: 'Contact', text: 'x'.repeat(500),
       truncatedFields: 2,
       projection: '<a href="https://www.google.com/maps/place/Probe/@53.1,-6.1,17z/data=!4m6!3m5!1s0x0" ></a>'.repeat(6) }],
    new Date('2026-09-07T00:00:00Z'));
  const codes = t.exceptions.map(x => x.code);
  const ok = codes.includes('TRUNCATED_ACQUISITION') && t.identity.verdict !== 'UNRESOLVED';
  console.log(ok ? '  ok    truncation guard: marked and queued, not read as absence'
                 : '  FAIL  truncation guard (' + t.identity.verdict + ' / ' + codes.join(',') + ')');
  if (!ok) process.exitCode = 1;
}

const inv = [];
if (records.some(r => r.reputation.enabled)) inv.push('reputation enabled');
if (records.some(r => r.reputation.rating !== null || r.reputation.reviewCount !== null)) inv.push('rating/count populated');
if (records.some(r => r.identity.placeId && !r.identity.placeIdRefreshDueAt)) inv.push('placeId without refresh target');
inv.forEach(m => console.log('  FAIL  invariant: ' + m));

console.log(`\n  live certification ${pass}/${orgs.length} passed` +
            `  | fetch-state fidelity ${distinct ? 'ok' : 'FAILED'}` +
            `  | invariants ${inv.length ? 'FAILED' : 'ok'}`);
console.log('  exception queue: ' + queue.length + ' -> ' +
  queue.map(q => q.name + '(' + q.reasons.join('+') + ')').join(', '));

require('fs').writeFileSync(__dirname + '/out-evidence-live.json', JSON.stringify(records, null, 2));
require('fs').writeFileSync(__dirname + '/out-queue-live.json', JSON.stringify(queue, null, 2));
process.exit(fails.length || inv.length || !distinct ? 1 : 0);
