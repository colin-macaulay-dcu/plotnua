/* CERTIFICATION — automated output vs manually adjudicated truth.
   Fixtures reproduce the EXACT identifier strings observed first-party during
   the Issue 007 manual pilot. No supplier is re-browsed; the point is to test
   the engine's typing and verdicts against answers a human already settled. */
'use strict';
const T = require('./trust-sweep.js');

const P = (url, html, fetchState) => ({ url, html, fetchState: fetchState || 'READ' });
const F = [

/* 1 · Garden Rooms — Place ID in a Google reviews widget on its own homepage */
{ org: { organisationId: 'rechco59Sn6wp3Aiq', name: 'Garden Rooms', canonicalDomain: 'www.gardenrooms.ie' },
  pages: [P('https://www.gardenrooms.ie/',
    `<div class="rpi-badge" data-id="ChIJi8YJW2wSZ0gRVWL3QKDZZuc" data-provider="google"></div>
     <p>Beech Vista Garden Centre, Coldwinters, Finglas, Dublin 11, D11HC7V.</p>
     <a href="tel:+353 1 8642 888">01 8642 888</a>`)],
  expect: { verdict: 'CONFIRMED', placeId: 'ChIJi8YJW2wSZ0gRVWL3QKDZZuc' } },

/* 2 · Modern Garden Rooms — query_place_id link + a name-query embed beside it */
{ org: { organisationId: 'recZcfloN72CBES6I', name: 'Modern Garden Rooms', canonicalDomain: 'moderngardenrooms.ie' },
  pages: [P('https://moderngardenrooms.ie/contact/',
    `<a href="https://www.google.com/maps/search/?api=1&query=Modern%20Garden%20Rooms%20Ireland&query_place_id=ChIJh_woWH1LZ0gRFhvXEPyKrts">Map</a>
     <iframe src="https://www.google.com/maps?q=Modern%20Garden%20Rooms%20Ireland%2C%20190A%20Iveragh%20Road%2C%20Dublin%20D09%20RR2R&z=15&output=embed"></iframe>
     <a href="tel:+353876779191">call</a>`)],
  expect: { verdict: 'CONFIRMED', placeId: 'ChIJh_woWH1LZ0gRFhvXEPyKrts' } },

/* 3 · Shomera — a name-query embed ONLY. Must not confirm. */
{ org: { organisationId: 'recw124UIanKV5Ath', name: 'Shomera', canonicalDomain: 'www.shomera.ie' },
  pages: [P('https://www.shomera.ie/contact-us/',
    `<iframe src="https://maps.google.com/maps?q=Shomera&t=m&z=14&output=embed&iwloc=near"></iframe>
     <p>Dunshaughlin Business Park, Co. Meath, A85 XF65</p>
     <a href="tel:01 825 82 88">phone</a>`)],
  expect: { verdictNot: 'CONFIRMED', placeId: null, hasException: 'NON_BUSINESS_IDENTIFIER' } },

/* 4 · Ballyfree — three embeds, two of them other businesses entirely */
{ org: { organisationId: 'rec66sNzKArqeOU23', name: 'Ballyfree Garden Sheds', canonicalDomain: 'ballyfreegardensheds.ie' },
  pages: [P('https://ballyfreegardensheds.ie/contact/',
    `<iframe src="https://www.google.com/maps/embed?pb=!1m18!1s0x4867ba0c82046a43%3A0x7ee088e328d21feb!2sBallyfree%20Garden%20Sheds%20Sales%20and%20Factory%20Charvey%20Lane%2C%20Commons%2C%20Co.%20Wicklow!5e0"></iframe>
     <iframe src="https://www.google.com/maps/embed?pb=!1m18!1s0x4867096ac4b67b91%3A0x5590a133b81f7524!2sNaomh%20Olaf%20GAA%20Club!5e0"></iframe>
     <iframe src="https://www.google.com/maps/embed?pb=!1m18!1s0x4867785bb27940b7%3A0xce34dfc7c6543eff!2sThe%20Shed%20Company!5e0"></iframe>
     <p>W91 PH2A</p><a href="tel:040468847">x</a>`)],
  expect: { verdict: 'AMBIGUOUS', hasException: 'MULTIPLE_LISTINGS' } },

/* 5a/5b · Garden Office Solutions and Live in Garden Pods — one business, two
   Atlas organisations: same CID, same phone. Detected only in the second pass. */
{ org: { organisationId: 'rec0zLenIbn3nsvjh', name: 'Garden Office Solutions', canonicalDomain: 'gardenofficesolutions.ie' },
  pages: [P('https://gardenofficesolutions.ie/contact-us/',
    `<a href="https://www.google.com/maps/place/Garden+Office+Solutions/@53.28,-6.63,9z/data=!4m5!3m4!1s0x486779cfc310d863:0x816421bc8d4d698!8m2!3d53.2865366!4d-6.6355068">map</a>
     <p>Littlewrath Sallins W91K5WK</p><a href="tel:0838119134">x</a>`)],
  expect: { hasException: 'SHARED_IDENTIFIER' } },
{ org: { organisationId: 'reczankduIWGWwXKR', name: 'Live in Garden Pods', canonicalDomain: 'liveingardenpods.ie' },
  pages: [P('https://liveingardenpods.ie/contact-us/',
    `<a href="https://www.google.com/maps/place/Garden+Office+Solutions+%E2%80%93+Bespoke+Garden+Rooms/@53.28,-6.63,17z/data=!3m1!4b1!4m6!3m5!1s0x486779cfc310d863:0x816421bc8d4d698!8m2!3d53.2865366!4d-6.6355068">map</a>
     <a href="tel:0838119134">x</a>`)],
  expect: { hasException: 'SHARED_IDENTIFIER', alsoException: 'SHARED_PHONE' } },

/* 6 · Berko — the CID names a REGION, not a business */
{ org: { organisationId: 'rec7dG4sHJtzstIHo', name: 'Berko Pod Systems Ltd', canonicalDomain: 'berkopodsystems.com' },
  pages: [P('https://berkopodsystems.com/modular-home-builder-contact-details/',
    `<a href="https://www.google.com/maps/place/Northern+Ireland,+UK/@54.66,-8.12,8z/data=!3m1!4b1!4m6!3m5!1s0x485e10ca99a69975:0xf7e528ef6eb7e3d8!8m2!3d54.78!4d-6.49!2sNorthern+Ireland,+UK">map</a>
     <a href="tel:+447856507023">x</a>`)],
  expect: { verdictNot: 'CONFIRMED', placeId: null, hasType: 'CID_REGION' } },

/* 7 · Quick-Garden — My Maps custom maps are not business listings */
{ org: { organisationId: 'recLQOPHHfSrfs3xA', name: 'Quick-Garden', canonicalDomain: 'www.quick-garden.co.uk' },
  pages: [P('https://www.quick-garden.co.uk/contacts/',
    `<iframe src="https://www.google.com/maps/d/u/0/embed?mid=1_prVGSRXWOhS4s_Ph5culWlPq8GhVYU&ll=53.06,-2.41&z=6"></iframe>
     <iframe src="https://www.google.com/maps/d/u/0/embed?mid=1F7gtSMB7M5kKU-nKOozsfpN2oXT4LQE&ll=54.14,-1.85&z=6"></iframe>
     <a href="tel:+442038077585">x</a>`, 'NOT_FOUND_PAGE')],
  expect: { verdictNot: 'CONFIRMED', placeId: null, hasType: 'MYMAPS' } },

/* 8 · Berko again, in the PATH form Google now emits: no !2s, the place name
   lives in the URL path. Reading only !2s typed this as a business and let it
   reach CONFIRMED on phone + postcode. LOCKS DEFECT 1. */
{ org: { organisationId: 'recBerkoPathForm', name: 'Berko Pod Systems Ltd', canonicalDomain: 'berkopodsystems.com' },
  pages: [P('https://berkopodsystems.com/modular-home-builder-contact-details/',
    `<a href="https://www.google.com/maps/place/Northern+Ireland,+UK/@54.662171,-8.1238576,8z/data=!3m1!4b1!4m6!3m5!1s0x485e10ca99a69975:0xf7e528ef6eb7e3d8!8m2!3d54.7877149!4d-6.4923145!16zL20vMDViY2w">map</a>
     <a href="tel:+447856507023">x</a><p>BT47 4QH</p>`)],
  expect: { verdictNot: 'CONFIRMED', placeId: null, hasType: 'CID_REGION' } },

/* 9 · ONE listing, published in both URL forms — zeroed map cell and real map
   cell, same business half. Counting raw strings made this two listings and
   raised a false MULTIPLE_LISTINGS. LOCKS DEFECT 2. */
{ org: { organisationId: 'recCidFormEquiv', name: 'Cid Form Probe', canonicalDomain: 'cidformprobe.ie' },
  pages: [P('https://cidformprobe.ie/contact/',
    `<a href="https://www.google.com/maps/place/Cid+Form+Probe/@53.28,-6.63,9z/data=!4m5!3m4!1s0x0:0xabc123def4567890!8m2!3d53.2!4d-6.6">a</a>
     <a href="https://www.google.com/maps/place/Cid+Form+Probe/@53.28,-6.63,17z/data=!3m1!4b1!4m6!3m5!1s0x4867aaaaaaaaaaaa:0xabc123def4567890!8m2!3d53.2!4d-6.6">b</a>
     <p>W91K5WK</p><a href="tel:0871111111">x</a>`)],
  expect: { verdict: 'CONFIRMED', noException: 'MULTIPLE_LISTINGS' } },
];

/* --- run ----------------------------------------------------------------- */
const now = new Date('2026-09-07T00:00:00Z');
const records = T.collide(F.map(f => T.assess(f.org, f.pages, now)));
let pass = 0; const fails = [];
records.forEach((r, i) => {
  const e = F[i].expect, codes = r.exceptions.map(x => x.code), why = [];
  if (e.verdict && r.identity.verdict !== e.verdict) why.push(`verdict ${r.identity.verdict} != ${e.verdict}`);
  if (e.verdictNot && r.identity.verdict === e.verdictNot) why.push(`verdict wrongly ${e.verdictNot}`);
  if ('placeId' in e && r.identity.placeId !== e.placeId) why.push(`placeId ${r.identity.placeId} != ${e.placeId}`);
  if (e.hasException && !codes.includes(e.hasException)) why.push(`missing ${e.hasException} (got ${codes.join(',') || 'none'})`);
  if (e.alsoException && !codes.includes(e.alsoException)) why.push(`missing ${e.alsoException}`);
  if (e.noException && codes.includes(e.noException)) why.push(`unexpected ${e.noException}`);
  if (e.hasType && !r.identity.identifierTypes.includes(e.hasType)) why.push(`missing type ${e.hasType}`);
  if (why.length) { fails.push({ name: r.name, why }); console.log('  FAIL  ' + r.name + ' — ' + why.join('; ')); }
  else { pass++; console.log('  ok    ' + r.name + '  [' + r.identity.verdict + '] ' + (codes.join(',') || '-')); }
});

/* Governance invariants the engine must never breach. */
const inv = [];
if (records.some(r => r.reputation.enabled)) inv.push('reputation must stay disabled');
if (records.some(r => r.reputation.rating !== null || r.reputation.reviewCount !== null)) inv.push('no rating/count may be populated');
if (records.some(r => r.identity.placeId && !r.identity.placeIdRefreshDueAt)) inv.push('placeId without refresh target');
if (JSON.stringify(records).toLowerCase().includes('trustpilot')) inv.push('trustpilot must not appear');
inv.forEach(m => console.log('  FAIL  invariant: ' + m));

const q = T.queue(records);
console.log(`\n  certification ${pass}/${F.length} passed, invariants ${inv.length ? 'FAILED' : 'ok'}`);
console.log(`  exception queue: ${q.length} organisations -> ` +
  q.map(x => x.name + '(' + x.reasons.join('+') + ')').join(', '));

require('fs').writeFileSync(__dirname + '/out-evidence.json', JSON.stringify(records, null, 2));
require('fs').writeFileSync(__dirname + '/out-queue.json', JSON.stringify(q, null, 2));
process.exit(fails.length || inv.length ? 1 : 0);
