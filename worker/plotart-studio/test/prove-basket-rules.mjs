// PROVE · multi-artist basket allocation rules (src/basket-rules.js, Phase 1, revised after review). Local only, offline:
// no Stripe, no network, no Worker. Pure sections use lineEntitlements() with stub records (the only way to obtain an
// entitlement plan() accepts). Section E runs the EXISTING entitlement rule unchanged against a throwaway Miniflare D1
// built from schema.sql, reading the artist, artwork, introduction and recorded consent from the database.
//   node test/prove-basket-rules.mjs
// Review regressions (PR #43 independent review) are marked [P1]…[P7], [M3], [M4], [L1], [L2], [L4], [H3].
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import * as B from '../src/basket-rules.js';
import * as R from '../src/checkout-rules.js';
import { statements } from './sql.mjs';

const results = []; let skipped = 0;
process.on('uncaughtException', e => { console.log(`  FAIL  uncaught: ${e.message}`); console.log(`BASKET RULES · stopped after ${results.length} checks: FAILED`); process.exit(1); });
process.on('unhandledRejection', e => { console.log(`  FAIL  unhandled: ${e && e.message}`); console.log(`BASKET RULES · stopped after ${results.length} checks: FAILED`); process.exit(1); });
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d !== '' ? `  [${String(d).slice(0, 500)}]` : ''}`); };
const refuses = (fn, re) => { try { fn(); return false; } catch (e) { return e instanceof R.RuleError && (!re || re.test(e.message)) ? true : `${e.constructor.name}: ${e.message}`; } };
const refusesAsync = async (fn, re) => { try { await fn(); return false; } catch (e) { return e instanceof R.RuleError && (!re || re.test(e.message)) ? true : `${e.constructor.name}: ${e.message}`; } };
const ok = r => r === true;
const sum = xs => xs.reduce((a, b) => a + b, 0);
let seed = 20261121; const rnd = n => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed % n; };

const T = '2026-11-21T10:00:00.000Z';
const DEC = { processing_fee_bearer: 'plotart', transfer_timing: 'on_payment', dispute_loss_bearer: 'plotart', dispute_fee_bearer: 'plotart', basket_introduction: 'logged_enquiry_only' };
const dec = over => ({ ...DEC, ...over });
const TERMS1 = { livemode: false, artist_terms_doc: 'PA-BASKET-TEST-01', buyer_terms_doc: 'PA-BASKET-BPT-TEST-01' };   // commission-free NOT permitted
const TERMS2 = { livemode: false, artist_terms_doc: 'PA-BASKET-TEST-02', buyer_terms_doc: 'PA-BASKET-BPT-TEST-02' };   // commission-free permitted
const COVER = v => ({ cover_type: 'transit_insurance', covered_value_cents: v, insured_party: 'transporter' });
const GAL = { ok: true, bp: 1500, basis: 'gallery_artist_agreement', evidence: { rule: 'PA-GAA cl. 5' } };
const FOUND = { ok: true, bp: 0, basis: 'founding_enquiry', evidence: { rule: 'PA-FAA cl. 5' } };

/* Sealed lines: the entitlement for each spec comes out of lineEntitlements(), with stub records that agree with the spec
   (artist owns the artwork; the introduction is logged for that artist and artwork). `e` is what the existing rule would
   return; `consent` is the artist's RECORDED processing consent. */
async function sealed(specs, decs = DEC) {
  const ref = s => 'PA-E-' + s.line_id;
  const records = {
    artist: async aid => (specs.some(s => s.artist_id === aid) ? { id: aid, founding: 0 } : null),
    artwork: async wid => { const s = specs.find(x => x.artwork_id === wid); return s ? { id: wid, artist_id: s.artist_id } : null; },
    enquiry: async r => { const s = specs.find(x => ref(x) === r); return s ? { id: 'e-' + s.line_id, artist_id: s.artist_id, artwork_id: s.artwork_id } : null; },
    consent: async aid => (specs.some(s => s.artist_id === aid && s.consent) ? { given: true, at: T } : { given: false, at: null }),
  };
  const resolve = async (env, { enquiryRef }) => specs.find(s => ref(s) === enquiryRef).e;
  const ents = await B.lineEntitlements({ ENVIRONMENT: 'test' }, specs.map(s => ({ line_id: s.line_id, artist_id: s.artist_id, artwork_id: s.artwork_id, enquiry_ref: ref(s) })), decs, { at: T, records, resolve });
  return specs.map(s => ({ line_id: s.line_id, artist_id: s.artist_id, artwork_id: s.artwork_id, shipment_id: s.shipment_id, artwork_cents: s.artwork_cents, entitlement: ents[s.line_id] }));
}
const L = (line_id, artist_id, artwork_id, shipment_id, artwork_cents, e = GAL, extra = {}) => ({ line_id, artist_id, artwork_id, shipment_id, artwork_cents, e, ...extra });
const ship = (shipment_id, artist_id, delivery_cents, insurance_cents, cover = COVER(999999), method = 'delivery') => ({ shipment_id, artist_id, method, delivery_cents, insurance_cents, cover });
const collect = (shipment_id, artist_id) => ({ shipment_id, artist_id, method: 'collection', delivery_cents: 0, insurance_cents: 0 });
// Rowan (Gallery Artist, 15%) ships two works together; Alder (Founding Enquiry, 0%) is collected.
const BASKET = async (consent = false) => ({ lines: await sealed([L('l1', 'rowan', 'w1', 's1', 145000), L('l2', 'rowan', 'w2', 's1', 125000), L('l3', 'alder', 'w3', 's2', 210000, FOUND, { consent })]),
  shipments: [ship('s1', 'rowan', 2500, 1000, COVER(270000)), collect('s2', 'alder')] });
const SMALL = async (consent = false) => ({ lines: await sealed([L('l1', 'rowan', 'w1', 's1', 100000), L('l2', 'alder', 'w2', 's2', 50000, FOUND, { consent })]),
  shipments: [ship('s1', 'rowan', 5000, 2500, COVER(100000)), ship('s2', 'alder', 3000, 0, COVER(50000))] });

console.log('PROVE · multi-artist basket allocation rules (offline)');

/* ---------------------------------------------------------------- D · founder decisions are explicit inputs */
console.log('— D founder decisions: required, no defaults');
for (const k of Object.keys(B.DECISIONS)) { const d = dec(); delete d[k]; check(`D1 missing decision ${k} is refused`, ok(refuses(() => B.decisions(d), new RegExp(`Founder decision required: ${k}`)))); }
check('D2 an unknown value is refused', ok(refuses(() => B.decisions(dec({ processing_fee_bearer: 'split_evenly' })), /must be one of/)));
check('D3 an unknown decision key is refused', ok(refuses(() => B.decisions({ ...DEC, payout_delay_days: 14 }), /Unknown founder decision/)));
check('D4 no decisions at all is refused (plan() has no defaults)', ok(refuses(() => B.plan({ lines: [], shipments: [] }, undefined, TERMS1), /Founder decisions are required/)));
check('D5 a valid set is returned frozen and unchanged', (() => { const d = B.decisions(DEC); return Object.isFrozen(d) && JSON.stringify(d) === JSON.stringify(DEC); })());
check('D6 commission eligibility has only the existing rule (logged introduction)', JSON.stringify(Object.keys(B.DECISIONS.basket_introduction)) === '["logged_enquiry_only"]');

/* ---------------------------------------------------------------- T · basket terms: the approval gate [H3] */
console.log('— T basket terms: approval gate (no live terms exist; issued single-artist terms excluded)');
const b0 = await SMALL();
check('T1 [H3] no terms → refused', ok(refuses(() => B.plan(b0, DEC), /Basket terms are required/)));
check('T2 [H3] the issued single-artist terms are refused for a basket (PA-PAY 1.3 excludes multi-artwork orders)', ok(refuses(() => B.plan(b0, DEC, { livemode: true, artist_terms_doc: 'PA-PAY-2026-11', buyer_terms_doc: 'PA-BPT-2026-11' }), /exclude multi-artwork/)));
check('T3 [H3] live mode: no approved live basket terms exist, so every live basket is refused', Object.keys(B.LIVE_BASKET_TERMS).length === 0 && Object.isFrozen(B.LIVE_BASKET_TERMS)
  && ok(refuses(() => B.plan(b0, DEC, { livemode: true, artist_terms_doc: 'PA-BASKET-2027-01', buyer_terms_doc: 'PA-BASKET-BPT-2027-01' }), /No approved live basket terms/)));
check('T4 [H3] TEST placeholder terms are never accepted in live mode', ok(refuses(() => B.plan(b0, DEC, { ...TERMS2, livemode: true }), /No approved live basket terms|never valid in live/)));
check('T5 a buyer text that does not belong with the artist text is refused', ok(refuses(() => B.plan(b0, DEC, { ...TERMS2, buyer_terms_doc: 'PA-BASKET-BPT-TEST-01' }), /do not belong/)));
check('T6 the mode must be stated', ok(refuses(() => B.plan(b0, DEC, { artist_terms_doc: 'PA-BASKET-TEST-02', buyer_terms_doc: 'PA-BASKET-BPT-TEST-02' }), /state the Stripe mode/)));
check('T7 [H3] a Founding 25 (0%) line under terms that do not permit commission-free sales → refused', ok(refuses(() => B.plan(b0, DEC, TERMS1), /Commission-free sales stay on direct payment/)));
check('T8 [H3] the same basket under terms that expressly permit commission-free lines → planned (support preserved behind the gate)', B.plan(b0, DEC, TERMS2).commission_cents === 15000);
const TERMS3 = { livemode: false, artist_terms_doc: 'PA-BASKET-TEST-03', buyer_terms_doc: 'PA-BASKET-BPT-TEST-03' };
const g0 = { lines: await sealed([L('g1', 'rowan', 'w1', 's1', 100000)]), shipments: [ship('s1', 'rowan', 0, 0, COVER(100000))] };
check('T9 terms that permit only some decisions refuse the others', ok(refuses(() => B.plan(g0, dec({ transfer_timing: 'after_delivery' }), TERMS3), /do not permit transfer_timing = after_delivery/)));
check('T9b …and accept the decisions they permit', B.plan(g0, DEC, TERMS3).total_cents === 100000);
check('T9c unknown TEST terms are refused', ok(refuses(() => B.plan(g0, DEC, { livemode: false, artist_terms_doc: 'PA-BASKET-TEST-99', buyer_terms_doc: 'PA-BASKET-BPT-TEST-99' }), /Unknown TEST basket terms/)));
check('T10 the plan records the terms it was made under', B.plan(b0, DEC, TERMS2).terms.artist_terms_doc === 'PA-BASKET-TEST-02');

/* ---------------------------------------------------------------- A · apportion */
console.log('— A apportion: exact integer splits');
check('A1 parts sum exactly to the whole', JSON.stringify(B.apportion(100, [1, 1, 1])) === '[34,33,33]');
check('A2 ties go to the earlier position (deterministic)', JSON.stringify(B.apportion(1, [5, 5])) === '[1,0]');
check('A3 a zero weight gets nothing', JSON.stringify(B.apportion(10, [0, 3, 7])) === '[0,3,7]');
check('A4 zero total over zero weights is all zeros', JSON.stringify(B.apportion(0, [0, 0])) === '[0,0]');
check('A5 a positive total over zero weights is refused', ok(refuses(() => B.apportion(5, [0, 0]))));
check('A6 fractions, negatives and floats are refused', [() => B.apportion(1.5, [1]), () => B.apportion(5, [-1, 2]), () => B.apportion(5, [0.5]), () => B.apportion(5, [])].every(f => ok(refuses(f))));
{
  let bad = null;
  for (let t = 0; t < 3000 && !bad; t++) {
    const n = 1 + rnd(8), w = Array.from({ length: n }, () => rnd(5) === 0 ? 0 : rnd(1_000_000)), total = rnd(2_000_000);
    if (sum(w) === 0) continue;
    const p = B.apportion(total, w), W = sum(w);
    if (sum(p) !== total || p.some((x, i) => !Number.isInteger(x) || x < Math.floor(total * w[i] / W) || x > Math.floor(total * w[i] / W) + 1)) bad = { total, w, p };
  }
  check('A7 3,000 random splits: exact sum, every part is the floor or floor+1 of its exact share', !bad, JSON.stringify(bad));
}

/* ---------------------------------------------------------------- N · normal purchases and validation */
console.log('— N normal purchases: per-artwork commission, per-shipment delivery, net proceeds');
const p1 = B.plan(await BASKET(), DEC, TERMS2);
const rowan = p1.artists.find(a => a.artist_id === 'rowan'), alder = p1.artists.find(a => a.artist_id === 'alder');
check('N1 one total for the whole basket (artworks + every shipment charge)', p1.total_cents === 145000 + 125000 + 210000 + 2500 + 1000, p1.total_cents);
check('N2 commission is 15% of each Gallery artwork only: 21,750 + 18,750', rowan.commission_cents === 21750 + 18750 && p1.commission_cents === 40500, rowan.commission_cents);
check('N3 the Founding Enquiry line carries 0% commission (terms permitting commission-free lines)', alder.commission_cents === 0 && p1.lines.find(l => l.line_id === 'l3').commission_basis === 'founding_enquiry');
check('N4 delivery and insurance go to the shipping artist and carry no commission', rowan.delivery_cents === 2500 && rowan.insurance_cents === 1000 && rowan.gross_cents === 273500 && rowan.transfer_before_fees_cents === 273500 - 40500);
check('N5 the collected artist is allocated their artwork in full', alder.gross_cents === 210000 && alder.transfer_before_fees_cents === 210000);
check('N6 the plan balances: total = commission + every artist transfer', p1.total_cents === p1.commission_cents + sum(p1.artists.map(a => a.transfer_before_fees_cents)));
check('N7 checkout items sum to the total, artist by artist, delivery and insurance itemised', sum(p1.items.map(i => i.amount_cents)) === p1.total_cents
  && JSON.stringify(p1.items.map(i => i.kind + ':' + i.ref)) === JSON.stringify(['artwork:l3', 'artwork:l1', 'artwork:l2', 'delivery:s1', 'insurance:s1']));
check('N8 artists are in a stable order (by id) and carry the transfer-timing decision', JSON.stringify(p1.artists.map(a => a.artist_id)) === '["alder","rowan"]' && p1.artists.every(a => a.release === 'on_payment'));
check('N9 the plan is deeply frozen and snapshots the decisions', Object.isFrozen(p1) && Object.isFrozen(p1.artists[0]) && Object.isFrozen(p1.lines[0]) && p1.decisions.processing_fee_bearer === 'plotart');
check('N10 [M3] the entitlement evidence is kept on each line, with its binding to artist, artwork and introduction', (() => { const l = p1.lines.find(x => x.line_id === 'l1'); return l.entitlement_evidence.rule === 'PA-GAA cl. 5' && l.entitlement_evidence.binding.artist_id === 'rowan' && l.entitlement_evidence.binding.artwork_id === 'w1' && l.enquiry_ref === 'PA-E-l1'; })());
{
  const p = B.plan({ lines: await sealed([L('a', 'x', 'w1', 's', 333), L('b', 'x', 'w2', 's', 333)]), shipments: [ship('s', 'x', 0, 0, COVER(666))] }, DEC, TERMS1);
  check('N11 rounding: two €3.33 works at 15% → 49 + 49 cents (not 99 on the €6.66 total)', p.commission_cents === 98 && p.artists[0].transfer_before_fees_cents === 666 - 98);
}
{
  const vari = { ok: true, bp: 1000, basis: 'gallery_artist_agreement', evidence: { rate_bp: 1000, variation_agreed_on: '2026-11-01' } };
  const fa = { ok: true, bp: 0, basis: 'founding_artist_no_commission_terms' };
  const p = B.plan({ lines: await sealed([L('a', 'x', 'w1', 'sx', 100000), L('b', 'y', 'w2', 'sy', 100000, vari), L('c', 'z', 'w3', 'sz', 100000, fa)]),
    shipments: [ship('sx', 'x', 1000, 0), ship('sy', 'y', 2000, 0), ship('sz', 'z', 3000, 0)] }, DEC, TERMS2);
  check('N12 mixed rates in one basket: 15%, a 10% written variation, and a Founding Artist without terms (0%)',
    JSON.stringify(p.artists.map(a => [a.artist_id, a.commission_cents, a.transfer_before_fees_cents])) === JSON.stringify([['x', 15000, 86000], ['y', 10000, 92000], ['z', 0, 103000]]));
}
{
  const p = B.plan({ lines: await sealed([L('a', 'x', 'w1', 's1', 40000), L('b', 'x', 'w2', 's2', 30000)]), shipments: [ship('s1', 'x', 4000, 500, COVER(40000)), collect('s2', 'x')] }, DEC, TERMS1);
  check('N13 one artist, two shipments (one delivered, one collected)', p.artists.length === 1 && p.artists[0].shipment_ids.length === 2 && p.artists[0].gross_cents === 74500);
}
{
  const p = B.plan({ lines: await sealed([L('a', 'x', 'w1', 's1', 40000, FOUND), L('b', 'y', 'w2', 's2', 30000, FOUND)]), shipments: [ship('s1', 'x', 0, 0), ship('s2', 'y', 0, 0)] }, DEC, TERMS2);
  check('N14 a basket of commission-free sales only (terms permitting): no commission, every artist allocated in full', p.commission_cents === 0 && p.artists.every(a => a.transfer_before_fees_cents === a.gross_cents));
}
console.log('— N validation: everything a basket must not contain');
const base = await BASKET();
const mut = f => { const b = { lines: base.lines.map(l => ({ ...l })), shipments: base.shipments.map(s => ({ ...s })) }; f(b); return () => B.plan(b, DEC, TERMS2); };
const one = async e => (await sealed([L('l1', 'rowan', 'w1', 's1', 145000, e)]))[0];
const V = [];
const blockedE = await one({ ok: false, reason: 'Commission entitlement unknown: no accepted terms' });
const noBasisE = await one({ ok: true, bp: 1500 });
const highE = await one({ ...GAL, bp: 1600 });
const fracE = await one({ ...GAL, bp: 1500.5 });
V.push(
  ['an unresolved entitlement blocks with its own reason', mut(b => { b.lines[0] = blockedE; }), /Commission entitlement unknown/],
  ['a missing entitlement blocks', mut(b => { delete b.lines[0].entitlement; }), /entitlement is required/],
  ['an entitlement without a basis is refused', mut(b => { b.lines[0] = noBasisE; }), /basis/],
  ['a rate above 15% is refused', mut(b => { b.lines[0] = highE; }), /Commission rate/],
  ['a fractional rate is refused', mut(b => { b.lines[0] = fracE; }), /Commission rate/],
  ['a price in fractions of a cent is refused', mut(b => { b.lines[0].artwork_cents = 1450.5; }), /whole euro cents/],
  ['a price given as a string is refused', mut(b => { b.lines[0].artwork_cents = '145000'; }), /whole euro cents/],
  ['a price below €1.00 is refused', mut(b => { b.lines[0].artwork_cents = 99; }), /between EUR 1.00/],
  ['a price above the per-artwork pilot limit is refused', mut(b => { b.lines[0].artwork_cents = R.MAX_ARTWORK_CENTS + 1; }), /between EUR 1.00/],
  ['a negative delivery charge is refused', mut(b => { b.shipments[0].delivery_cents = -1; }), /whole euro cents/],
  ['the same original twice is refused', mut(b => { b.lines[1].artwork_id = 'w1'; }), /sold only once/],
  ['a duplicate line id is refused', mut(b => { b.lines[1].line_id = 'l1'; }), /Duplicate basket line/],
  ['a duplicate shipment id is refused', mut(b => { b.shipments[1].shipment_id = 's1'; }), /Duplicate shipment/],
  ['a line in another artist\'s shipment is refused', mut(b => { b.lines[2].shipment_id = 's1'; }), /belongs to another artist/],
  ['an unknown shipment is refused', mut(b => { b.lines[0].shipment_id = 'nope'; }), /unknown shipment/],
  ['an empty shipment is refused', mut(b => { b.shipments.push(ship('s9', 'rowan', 0, 0)); }), /carries no artwork/],
  ['a delivery without insurance cover is refused', mut(b => { b.shipments[0].cover = null; }), /transit insurance|needs recorded cover/],
  ['cover below the artworks it carries is refused', mut(b => { b.shipments[0].cover = COVER(269999); }), /at least the artwork price/],
  ['cover held by PlotArt is refused (existing rule)', mut(b => { b.shipments[0].cover = { ...COVER(270000), insured_party: 'plotart' }; }), /Name who holds/],
  ['delivery + insurance above the pilot ceiling is refused', mut(b => { b.shipments[0].delivery_cents = R.MAX_DELIVERY_CENTS; }), /pilot ceiling/],
  ['an unknown shipment method is refused', mut(b => { b.shipments[0].method = 'drone'; }), /delivery or collection/],
  ['a malformed id is refused', mut(b => { b.lines[0].artist_id = 'rowan; DROP TABLE'; }), /letters, digits/],
  ['an empty basket is refused', () => B.plan({ lines: [], shipments: [] }, DEC, TERMS2), /at least one artwork/],
  ['[L1] a collection shipment with a delivery charge is refused', mut(b => { b.shipments[1].delivery_cents = 150000; }), /collection has no delivery charge/],
  ['[L1] an insurance charge without recorded cover is refused', mut(b => { b.shipments[1].insurance_cents = 50000; }), /needs recorded cover/],
);
for (const [n, f, re] of V) { const r = refuses(f, re); check('N15 ' + n, ok(r), r); }
{
  const b = { lines: await sealed([L('a', 'x', 'w1', 's', 999999), L('b', 'x', 'w2', 's', 1000)]), shipments: [ship('s', 'x', 0, 0, COVER(2_000_000))] };
  check('N16 a basket of EUR 10,000 or more is refused (existing pilot AML scope)', ok(refuses(() => B.plan(b, DEC, TERMS1), /EUR 10,000/)));
  const b2 = { lines: await sealed([L('a', 'x', 'w1', 's', 900000), L('b', 'x', 'w2', 's', 99999)]), shipments: [ship('s', 'x', 1, 0, COVER(2_000_000))] };
  check('N17 the €10,000 ceiling is on the whole basket, delivery included (€9,999.99 + €0.01 is refused)', ok(refuses(() => B.plan(b2, DEC, TERMS1), /EUR 10,000/)));
  const many = { lines: await sealed(Array.from({ length: B.MAX_BASKET_LINES + 1 }, (_, i) => L('l' + i, 'x', 'w' + i, 's', 100))), shipments: [ship('s', 'x', 0, 0)] };
  check('N18 more than the technical maximum of lines is refused', ok(refuses(() => B.plan(many, DEC, TERMS1), /at most/)));
}
{
  const b = { lines: await sealed([L('a', 'x', 'w1', 's', 40000)]), shipments: [{ shipment_id: 's', artist_id: 'x', method: 'collection', delivery_cents: 0, insurance_cents: 500, cover: COVER(40000) }] };
  check('N19 [L1] a collection with an insurance charge AND recorded cover is accepted', B.plan(b, DEC, TERMS1).total_cents === 40500);
}

/* ---------------------------------------------------------------- M · entitlements bound to records; consent recorded [M3] */
console.log('— M entitlements bound to artist, artwork and introduction; consent only as recorded');
{
  const gal = await sealed([L('g', 'gallery', 'wg', 'sg', 500000, GAL)]);
  const fnd = await sealed([L('f', 'founder', 'wf', 'sf', 50000, FOUND)]);
  const hijack = { lines: [{ ...gal[0], entitlement: fnd[0].entitlement }], shipments: [ship('sg', 'gallery', 0, 0)] };
  check('M1 [P1] a Founding 0% entitlement attached to a Gallery Artist\'s line is refused', ok(refuses(() => B.plan(hijack, DEC, TERMS2), /another artist or artwork/)));
  const sameArtist = await sealed([L('a', 'x', 'w1', 's', 10000, FOUND), L('b', 'x', 'w2', 's', 10000, GAL)]);
  const swapped = { lines: [{ ...sameArtist[1], entitlement: sameArtist[0].entitlement }], shipments: [ship('s', 'x', 0, 0)] };
  check('M2 [P1] an entitlement for another artwork of the SAME artist is refused', ok(refuses(() => B.plan(swapped, DEC, TERMS2), /another artist or artwork/)));
  const forged = { lines: [{ ...gal[0], entitlement: { ok: true, bp: 0, basis: 'founding_enquiry', binding: { artist_id: 'gallery', artwork_id: 'wg' } } }], shipments: [ship('sg', 'gallery', 0, 0)] };
  check('M3 a hand-made entitlement (even with a matching binding) is refused', ok(refuses(() => B.plan(forged, DEC, TERMS2), /not produced by lineEntitlements/)));
  const withFlag = { lines: [{ ...gal[0], processing_consent: true }], shipments: [ship('sg', 'gallery', 0, 0)] };
  check('M4 [P7] caller-supplied processing consent is refused outright', ok(refuses(() => B.plan(withFlag, DEC, TERMS2), /recorded consent, never from the request/)));
  const pr = dec({ processing_fee_bearer: 'artists_pro_rata' });
  const noConsent = await SMALL(false);
  check('M5 artists bear fees + a commission-free line WITHOUT recorded consent → refused', ok(refuses(() => B.plan(noConsent, pr, TERMS2), /not recorded consent/)));
  const pc = B.plan(await SMALL(true), pr, TERMS2);
  check('M6 the same with the artist\'s RECORDED consent → planned, and the consent time is kept on the line', pc.lines.find(l => l.line_id === 'l2').processing_consent_at === T);
  check('M7 PlotArt bears fees: no consent needed on commission-free lines', B.plan(noConsent, DEC, TERMS2).total_cents > 0);
}
{
  const rec = (over = {}) => ({
    artist: async aid => (aid === 'gone' ? null : { id: aid }),
    artwork: async wid => ({ w1: { id: 'w1', artist_id: 'x' }, w2: { id: 'w2', artist_id: 'x' }, wy: { id: 'wy', artist_id: 'y' } })[wid] || null,
    enquiry: async ref => ({ E1: { id: 'e1', artist_id: 'x', artwork_id: 'w1' }, ENULL: { id: 'en', artist_id: 'x', artwork_id: null }, EY: { id: 'ey', artist_id: 'y', artwork_id: 'wy' } })[ref] || null,
    consent: async () => ({ given: false, at: null }), ...over });
  const resolve = async () => GAL;
  const run = (reqs, opts = {}) => B.lineEntitlements(opts.env || { ENVIRONMENT: 'test' }, reqs, DEC, { at: T, records: rec(opts.rec), resolve });
  const e = await run([
    { line_id: 'a', artist_id: 'gone', artwork_id: 'w1', enquiry_ref: 'E1' },
    { line_id: 'b', artist_id: 'x', artwork_id: 'wy', enquiry_ref: 'E1' },
    { line_id: 'c', artist_id: 'x', artwork_id: 'w2', enquiry_ref: 'E1' },
    { line_id: 'd', artist_id: 'x', artwork_id: 'w2', enquiry_ref: 'ENULL' },
    { line_id: 'f', artist_id: 'x', artwork_id: 'w2', enquiry_ref: 'EY' },
    { line_id: 'g', artist_id: 'x', artwork_id: 'w2', enquiry_ref: '' },
    { line_id: 'h', artist_id: 'x', artwork_id: 'w1', enquiry_ref: 'E1' },
    { line_id: 'i', artist_id: 'x', artwork_id: 'w1', enquiry_ref: 'E1' },
  ]);
  check('M8 an unknown artist is blocked', e.a.ok === false && /Unknown artist/.test(e.a.reason));
  check('M9 an artwork that is not the artist\'s is blocked', e.b.ok === false && /not this artist/.test(e.b.reason));
  check('M10 [M3] an introduction for ANOTHER artwork cannot set this artwork\'s commission', e.c.ok === false && /for another artwork/.test(e.c.reason));
  check('M11 [M3] an introduction not tied to any artwork cannot set commission (founder decision)', e.d.ok === false && /not tied to an artwork/.test(e.d.reason));
  check('M12 another artist\'s introduction is blocked', e.f.ok === false && /No PlotArt introduction is logged/.test(e.f.reason));
  check('M13 no introduction named is blocked (basket_introduction)', e.g.ok === false && /basket_introduction/.test(e.g.reason));
  check('M14 a matching introduction resolves through the existing rule, bound to artist, artwork and introduction', e.h.ok === true && e.h.bp === 1500 && e.h.binding.enquiry_log_id === 'e1' && e.h.evidence.binding.artwork_id === 'w1');
  check('M15 [M3] one introduction cannot serve two lines', e.i.ok === false && /already used/.test(e.i.reason));
  check('M16 records cannot be supplied in production (they are read from the database)', ok(await refusesAsync(() => run([{ line_id: 'h', artist_id: 'x', artwork_id: 'w1', enquiry_ref: 'E1' }], { env: { ENVIRONMENT: 'production' } }), /cannot be supplied in production/)));
  const w = await run([{ line_id: 'h', artist_id: 'x', artwork_id: 'w1', enquiry_ref: 'E1' }], { rec: { consent: async () => ({ given: false, at: null }) } });
  check('M17 withdrawn or absent consent is carried as not given', w.h.processing_consent === false && w.h.processing_consent_at === null);
}

/* ---------------------------------------------------------------- S · settlement with Stripe's actual fee */
console.log('— S settlement: the actual processing fee, per decision');
{
  const s = B.settle(p1, { fee_cents: 7500, fee_vat_cents: 1725 });
  check('S1 PlotArt bears the fee: no artist share; artists receive the plan in full', s.artists.every(a => a.processing_share_cents === 0 && a.transfer_cents === a.transfer_before_fees_cents));
  check('S2 PlotArt net = commission − fee − VAT', s.platform_net_cents === 40500 - 9225 && s.platform_shortfall_cents === 0);
  check('S3 settlement balances: total = transfers + PlotArt net + fee', p1.total_cents === s.transfers_cents + s.platform_net_cents + s.fee_total_cents);
}
{
  const p = B.plan({ lines: await sealed([L('a', 'x', 'w1', 's', 50000, FOUND)]), shipments: [ship('s', 'x', 0, 0)] }, DEC, TERMS2);
  const s = B.settle(p, { fee_cents: 1000, fee_vat_cents: 230 });
  check('S4 PlotArt bears the fee on a commission-free basket: the shortfall is reported, not hidden', s.platform_net_cents === -1230 && s.platform_shortfall_cents === 1230);
}
const pr = dec({ processing_fee_bearer: 'artists_pro_rata' });
{
  const p = B.plan(await BASKET(true), pr, TERMS2), s = B.settle(p, { fee_cents: 7500, fee_vat_cents: 1725 });
  const expect = B.apportion(9225, p.artists.map(a => a.gross_cents));
  check('S5 artists bear the fee: shares are proportional to gross and sum exactly to fee + VAT', sum(s.artists.map(a => a.processing_share_cents)) === 9225 && JSON.stringify(s.artists.map(a => a.processing_share_cents)) === JSON.stringify(expect));
  check('S6 artists bear the fee: PlotArt keeps its full commission', s.platform_net_cents === p.commission_cents);
  check('S7 artists bear the fee: settlement balances', p.total_cents === s.transfers_cents + s.platform_net_cents + s.fee_total_cents);
  check('S8 a fee so large that a share exceeds an allocation is a FAILED allocation, never clipped', ok(refuses(() => B.settle(p, { fee_cents: p.total_cents, fee_vat_cents: 0 }), /Allocation failed/)));
}
check('S9 a fractional fee is refused', ok(refuses(() => B.settle(p1, { fee_cents: 10.5, fee_vat_cents: 0 }))));
check('S10 a hand-built (unfrozen) plan is refused', ok(refuses(() => B.settle(JSON.parse(JSON.stringify(p1)), { fee_cents: 0, fee_vat_cents: 0 }), /plan\(\) is required/)));
{
  let bad = null;
  for (let t = 0; t < 300 && !bad; t++) {
    const nArt = 1 + rnd(4), specs = [], shipments = [];
    for (let a = 0; a < nArt; a++) {
      const nShip = 1 + rnd(2);
      for (let s = 0; s < nShip; s++) shipments.push({ shipment_id: `s${a}_${s}`, artist_id: `a${a}`, method: 'delivery', delivery_cents: rnd(5000), insurance_cents: rnd(800), cover: COVER(999999) });
      for (let k = 0; k < 1 + rnd(2); k++) {
        const bp = [0, 1500, 1000, 1250][rnd(4)];
        specs.push(L(`l${specs.length}`, `a${a}`, `w${specs.length}`, `s${a}_${rnd(nShip)}`, 100 + rnd(80000), { ok: true, bp, basis: bp ? 'gallery_artist_agreement' : 'founding_enquiry' }, { consent: true }));
      }
    }
    const used = new Set(specs.map(l => l.shipment_id)); const sh = shipments.filter(s => used.has(s.shipment_id));
    const bearer = rnd(2) ? 'plotart' : 'artists_pro_rata';
    try {
      const p = B.plan({ lines: await sealed(specs), shipments: sh }, dec({ processing_fee_bearer: bearer }), TERMS2);
      const fee = rnd(Math.floor(p.total_cents / 20) + 1), vat = Math.floor(fee * 23 / 100);
      const s = B.settle(p, { fee_cents: fee, fee_vat_cents: vat });
      const expectLine = p.lines.every(l => l.commission_cents === Math.floor(l.artwork_cents * l.commission_bp / 10000));
      if (p.total_cents !== p.commission_cents + sum(p.artists.map(a => a.transfer_before_fees_cents)) || sum(p.lines.map(l => l.commission_cents)) !== p.commission_cents || !expectLine
        || p.total_cents !== s.transfers_cents + s.platform_net_cents + s.fee_total_cents || s.artists.some(a => a.transfer_cents < 0)) bad = { t, bearer };
    } catch (e) { if (!/EUR 10,000/.test(e.message)) bad = { t, error: e.message }; }
  }
  check('S11 300 random baskets: per-artwork floor commission, plan and settlement balance to the cent, no negative transfer', !bad, JSON.stringify(bad));
}

/* ---------------------------------------------------------------- P · what to transfer now [M4, L4] */
console.log('— P transfers: hold during disputes and before release; one in flight; failed attempts retried with a new key');
{
  const sp = B.plan(await SMALL(), DEC, TERMS2), ss = B.settle(sp, { fee_cents: 2500, fee_vat_cents: 575 });
  const ready = { artists: { rowan: { release_ready_at: T }, alder: { release_ready_at: T } } };
  const now = '2026-11-22T00:00:00.000Z';
  const tp = B.transferPlan(sp, ss, ready, { basket_id: 'b1', now });
  check('P1 released artists are transferred their settled amount, attempt 1, with the database key format',
    tp.every(a => a.action === 'transfer' && a.attempt === 1) && tp.find(a => a.artist_id === 'rowan').idempotency_key === 'plotart-basket-tr:b1:rowan:allocation:-:1'
    && tp.find(a => a.artist_id === 'rowan').amount_cents === ss.artists.find(a => a.artist_id === 'rowan').transfer_cents);
  check('P2 [M4] an open dispute holds EVERY artist\'s transfer', B.transferPlan(sp, ss, ready, { basket_id: 'b1', now, open_dispute: true }).every(a => a.action === 'hold'));
  check('P3 not yet released (delivery or cancellation window pending) → hold', B.transferPlan(sp, ss, { artists: { rowan: {}, alder: { release_ready_at: '2026-12-01T00:00:00.000Z' } } }, { basket_id: 'b1', now }).every(a => a.action === 'hold'));
  const retry = B.transferPlan(sp, ss, { artists: { rowan: { release_ready_at: T, attempts: 1, in_flight_or_made_cents: 0 }, alder: { release_ready_at: T } } }, { basket_id: 'b1', now });
  check('P4 [L4] after a FAILED transfer the next attempt uses a new idempotency key', retry.find(a => a.artist_id === 'rowan').attempt === 2 && /:2$/.test(retry.find(a => a.artist_id === 'rowan').idempotency_key));
  const due = ss.artists.find(a => a.artist_id === 'rowan').transfer_cents;
  const inflight = B.transferPlan(sp, ss, { artists: { rowan: { release_ready_at: T, attempts: 1, in_flight_or_made_cents: 1000 }, alder: { release_ready_at: T } } }, { basket_id: 'b1', now });
  check('P5 [H2] a transfer already in flight or made is never sent again', inflight.find(a => a.artist_id === 'rowan').action === 'wait');
  check('P6 fully transferred → done', B.transferPlan(sp, ss, { artists: { rowan: { release_ready_at: T, attempts: 1, in_flight_or_made_cents: due }, alder: {} } }, { basket_id: 'b1', now }).find(a => a.artist_id === 'rowan').action === 'done');
  const reduced = B.transferPlan(sp, ss, { artists: { rowan: { release_ready_at: T, pending_reduced_cents: 10000 }, alder: { release_ready_at: T } } }, { basket_id: 'b1', now });
  check('P7 reductions applied before payout lower the transfer', reduced.find(a => a.artist_id === 'rowan').amount_cents === due - 10000);
  check('P8 [H2] more already sent than is due is a failed allocation', ok(refuses(() => B.transferPlan(sp, ss, { artists: { rowan: { in_flight_or_made_cents: due + 1 } } }, { basket_id: 'b1', now }), /more than is due/)));
}

/* ---------------------------------------------------------------- F · refunds */
console.log('— F refunds: commission returned per PA-GAA 9.2, recovery from artists, failures unwound');
const sp = B.plan(await SMALL(), DEC, TERMS2), ss = B.settle(sp, { fee_cents: 2500, fee_vat_cents: 575 });
const settled = (over = {}) => ({ artists: Object.fromEntries(ss.artists.map(a => [a.artist_id, { transfer_due_cents: a.transfer_cents, transferred_cents: a.transfer_cents, reversed_cents: 0, pending_reduced_cents: 0, ...(over[a.artist_id] || {}) }])) });
{
  const r = B.refund(sp, settled(), { lines: [{ line_id: 'l1', artwork_cents: 50000 }] });
  check('F1 €500 refunded on a €1,000 work at 15%: €75 commission returned, artist debited €425 (PA-PAY example 2)', r.commission_returned_cents === 7500 && r.lines[0].artist_debit_cents === 42500 && r.buyer_refund_cents === 50000);
  check('F2 the artist debit is recovered by reversing the transfer already made', r.artists[0].reverse_cents === 42500 && r.artists[0].reduce_pending_cents === 0 && r.shortfall_cents === 0);
  check('F3 the refund balances: buyer refund = artist debits + commission returned', r.buyer_refund_cents === sum(r.artists.map(a => a.debit_cents)) + r.commission_returned_cents);
  const u = B.refundFailed(sp, r);
  check('F4 [L4] that refund FAILS (even after succeeding): the reversal is re-credited and PlotArt reclaims its €75', u.artists[0].recredit_cents === 42500 && u.commission_reclaimed_cents === 7500);
}
{
  const r = B.refund(sp, settled(), { lines: [{ line_id: 'l1', artwork_cents: 100000 }], shipments: [{ shipment_id: 's1', cents: 7500 }] });
  check('F5 full refund of a work and its shipment: full commission returned, delivery + insurance debited in full', r.commission_returned_cents === 15000 && r.artists[0].debit_cents === 85000 + 7500 && r.buyer_refund_cents === 107500);
}
{
  const r = B.refund(sp, settled(), { lines: [{ line_id: 'l2', artwork_cents: 50000 }] });
  check('F6 a Founding (0%) line: nothing to return, the artist is debited the refund', r.commission_returned_cents === 0 && r.artists[0].debit_cents === 50000);
}
{
  const p = B.plan({ lines: await sealed([L('a', 'x', 'w1', 's', 999)]), shipments: [ship('s', 'x', 0, 0, COVER(999))] }, DEC, TERMS1), s = B.settle(p, { fee_cents: 0, fee_vat_cents: 0 });
  let st = { lines: { a: { artwork_refunded_cents: 0, commission_returned_cents: 0 } }, artists: { x: { transfer_due_cents: s.artists[0].transfer_cents, transferred_cents: s.artists[0].transfer_cents, reversed_cents: 0 } } };
  const got = [];
  for (const amt of [333, 333, 333]) {
    const r = B.refund(p, st, { lines: [{ line_id: 'a', artwork_cents: amt }] });
    got.push(r.commission_returned_cents);
    st = { lines: { a: { artwork_refunded_cents: st.lines.a.artwork_refunded_cents + amt, commission_returned_cents: st.lines.a.commission_returned_cents + r.commission_returned_cents } },
      artists: { x: { ...st.artists.x, reversed_cents: st.artists.x.reversed_cents + r.artists[0].reverse_cents } } };
  }
  const kept = k => Math.floor(149 * k / 999);
  check('F7 rounding: three €3.33 refunds of a €9.99 work at 15% return 149 − kept(666), …, the whole 149 in total',
    p.commission_cents === 149 && JSON.stringify(got) === JSON.stringify([149 - kept(666), kept(666) - kept(333), kept(333)]) && sum(got) === 149, JSON.stringify(got));
  check('F8 after the last refund the whole transfer has been reversed', st.artists.x.reversed_cents === 999 - 149);
}
{
  const late = settled({ rowan: { transferred_cents: 0 } });
  const r = B.refund(sp, late, { lines: [{ line_id: 'l1', artwork_cents: 20000 }] });
  check('F9 transfer not yet made (held until delivery): the debit reduces the pending transfer, nothing is reversed', r.artists[0].reduce_pending_cents === 17000 && r.artists[0].reverse_cents === 0);
  const part = settled({ rowan: { transferred_cents: 0, pending_reduced_cents: 80000 } });
  const r2 = B.refund(sp, part, { lines: [{ line_id: 'l1', artwork_cents: 20000 }] });
  check('F10 pending first, then a SHORTFALL when neither pending nor transferred money covers it', r2.artists[0].reduce_pending_cents === ss.artists.find(a => a.artist_id === 'rowan').transfer_cents - 80000 && r2.shortfall_cents === 17000 - r2.artists[0].reduce_pending_cents);
  const u = B.refundFailed(sp, r2);
  check('F11 [L4] a failed refund restores reductions and clears shortfalls exactly', u.artists[0].restore_pending_cents === r2.artists[0].reduce_pending_cents && u.artists[0].shortfall_cleared_cents === r2.shortfall_cents);
}
{
  const p = B.plan(await SMALL(true), pr, TERMS2), s = B.settle(p, { fee_cents: 2500, fee_vat_cents: 575 });
  const st = { artists: Object.fromEntries(s.artists.map(a => [a.artist_id, { transfer_due_cents: a.transfer_cents, transferred_cents: a.transfer_cents }])) };
  const r = B.refund(p, st, { lines: [{ line_id: 'l1', artwork_cents: 100000 }], shipments: [{ shipment_id: 's1', cents: 7500 }] });
  const share = s.artists.find(a => a.artist_id === 'rowan').processing_share_cents;
  check('F12 [P6] FAILED ALLOCATION surfaced: artists bore the fee, full refund → shortfall equals that artist\'s fee share', r.shortfall_cents === share && share > 0, `${r.shortfall_cents} vs ${share}`);
}
const RF = [
  ['a refund above the artwork amount', { lines: [{ line_id: 'l1', artwork_cents: 100001 }] }, /exceeds/],
  ['a refund above the shipment charges', { shipments: [{ shipment_id: 's1', cents: 7501 }] }, /exceeds/],
  ['a zero refund', { lines: [{ line_id: 'l1', artwork_cents: 0 }] }, /more than zero/],
  ['an unknown line', { lines: [{ line_id: 'zz', artwork_cents: 1 }] }, /Unknown line/],
  ['the same line twice', { lines: [{ line_id: 'l1', artwork_cents: 1 }, { line_id: 'l1', artwork_cents: 1 }] }, /named twice/],
  ['an empty request', {}, /Name what/],
];
for (const [n, req, re] of RF) check('F13 refused: ' + n, ok(refuses(() => B.refund(sp, settled(), req), re)));
check('F14 refused: a refund beyond what is left after earlier (including PENDING) refunds', ok(refuses(() => B.refund(sp, { ...settled(), lines: { l1: { artwork_refunded_cents: 90000, commission_returned_cents: 13500 } } }, { lines: [{ line_id: 'l1', artwork_cents: 10001 }] }), /exceeds/)));
check('F15 refused: a refund before the payment is settled', ok(refuses(() => B.refund(sp, {}, { lines: [{ line_id: 'l1', artwork_cents: 100 }] }), /settle the payment first/)));
check('F16 refused: an inconsistent transfer record (reversed more than transferred)', ok(refuses(() => B.refund(sp, settled({ rowan: { reversed_cents: 999999 } }), { lines: [{ line_id: 'l1', artwork_cents: 100 }] }), /inconsistent/)));
{
  const rv = B.reversalFailed({ transfer_id: 'tr1', cause_kind: 'refund', cause_id: 'rf1', attempt: 1, amount_cents: 42500 }, { retry: true });
  const sf = B.reversalFailed({ transfer_id: 'tr1', cause_kind: 'refund', cause_id: 'rf1', attempt: 2, amount_cents: 42500 }, { retry: false });
  check('F17 [L4] a failed reversal is retried with a new key (database format)…', rv.action === 'retry' && rv.idempotency_key === 'plotart-basket-trr:tr1:refund:rf1:2');
  check('F18 [L4] …or becomes a shortfall to recover outside Stripe; the choice is never implicit', sf.action === 'shortfall' && sf.amount_cents === 42500 && ok(refuses(() => B.reversalFailed({ transfer_id: 'tr1', cause_kind: 'refund', cause_id: 'rf1', attempt: 1, amount_cents: 1 }, {}), /retry the reversal or record a shortfall/)));
}
{
  let bad = null;
  for (let t = 0; t < 500 && !bad; t++) {
    const before = rnd(100001), now = 1 + rnd(100000 - Math.min(before, 99999));
    if (before + now > 100000) continue;
    const cb = Math.max(0, 15000 - Math.floor(15000 * (100000 - before) / 100000));
    try {
      const r = B.refund(sp, { ...settled(), lines: { l1: { artwork_refunded_cents: before, commission_returned_cents: cb } } }, { lines: [{ line_id: 'l1', artwork_cents: now }] });
      const keptAfter = Math.floor(15000 * (100000 - before - now) / 100000);
      const u = B.refundFailed(sp, r);
      if (r.buyer_refund_cents !== sum(r.artists.map(a => a.debit_cents)) + r.commission_returned_cents || cb + r.commission_returned_cents !== 15000 - keptAfter
        || r.artists.some(a => a.debit_cents !== a.reduce_pending_cents + a.reverse_cents + a.shortfall_cents)
        || r.buyer_refund_cents !== sum(u.artists.map(a => a.restore_pending_cents + a.recredit_cents + a.shortfall_cleared_cents)) + u.commission_reclaimed_cents) bad = { before, now };
    } catch (e) { bad = { before, now, e: e.message }; }
  }
  check('F19 500 random partial refunds: balanced, commission kept = floor(C × kept / A), debits fully accounted, failure unwinds exactly', !bad, JSON.stringify(bad));
}

/* ---------------------------------------------------------------- X · disputes */
console.log('— X disputes: holds while open; explicit attribution when artists carry any part');
{
  const o = B.dispute(sp, settled(), { outcome: 'open', amount_cents: sp.total_cents, fee_cents: 2000 });
  const w = B.dispute(sp, settled(), { outcome: 'won', amount_cents: sp.total_cents, fee_cents: 2000 });
  check('X1 [P4][M4] an open dispute holds every artist\'s transfers; nothing moves', JSON.stringify(o.hold_transfers) === '["alder","rowan"]' && o.artists.length === 0 && o.platform_cost_cents === 0);
  check('X2 a won dispute releases the hold; nothing moves', w.hold_transfers.length === 0 && w.artists.length === 0);
  const x = B.dispute(sp, settled(), { outcome: 'lost', amount_cents: sp.total_cents, fee_cents: 2000 });
  check('X3 lost, PlotArt bears loss and fee: no artist is debited; PlotArt\'s cost = amount + fee', x.artists.length === 0 && x.platform_cost_cents === sp.total_cents + 2000);
  const early = B.dispute(sp, {}, { outcome: 'lost', amount_cents: 1000, fee_cents: 2000 });
  check('X4 [L2][P5] lost and PlotArt-borne BEFORE settlement: no longer throws', early.platform_cost_cents === 3000);
}
const XD = dec({ dispute_loss_bearer: 'artists_by_line', dispute_fee_bearer: 'artists_by_line' });
{
  const p = B.plan(await SMALL(), XD, TERMS2), s = B.settle(p, { fee_cents: 2500, fee_vat_cents: 575 });
  const st = { artists: Object.fromEntries(s.artists.map(a => [a.artist_id, { transfer_due_cents: a.transfer_cents, transferred_cents: a.transfer_cents }])) };
  const x = B.dispute(p, st, { outcome: 'lost', amount_cents: 100000, fee_cents: 2000, attribution: { lines: [{ line_id: 'l1', artwork_cents: 100000 }] } });
  const r = x.artists.find(a => a.artist_id === 'rowan');
  check('X5 lost, attributed to Rowan\'s work: commission returned (PA-GAA 9.1), Rowan recovers €850 + the €20 fee', x.commission_returned_cents === 15000 && r.loss_cents === 85000 && r.dispute_fee_cents === 2000 && r.debit_cents === 87000);
  check('X6 PlotArt\'s cost is only the commission it returned', x.platform_cost_cents === 15000);
  check('X7 the dispute balances: amount + fee = artist recoveries + PlotArt\'s cost', 100000 + 2000 === sum(x.artists.map(a => a.debit_cents)) + x.platform_cost_cents);
  check('X8 [P3] the other artist is not touched', !x.artists.some(a => a.artist_id === 'alder'));
  check('X9 [P3][M4] lost and carried by artists WITHOUT an explicit attribution → refused (no spreading over uninvolved artists)', ok(refuses(() => B.dispute(p, st, { outcome: 'lost', amount_cents: p.total_cents, fee_cents: 2001 }), /explicit attribution/)));
  check('X10 refused: an attribution that does not add up to the disputed amount', ok(refuses(() => B.dispute(p, st, { outcome: 'lost', amount_cents: 100000, attribution: { lines: [{ line_id: 'l1', artwork_cents: 99999 }] } }), /add up/)));
  check('X11 refused: a disputed amount above what remains unrefunded', ok(refuses(() => B.dispute(p, st, { outcome: 'lost', amount_cents: p.total_cents + 1 }), /no more than/)));
  check('X12 refused: an unknown outcome', ok(refuses(() => B.dispute(p, st, { outcome: 'maybe', amount_cents: 1 }), /open, won or lost/)));
  check('X13 refused: attribution to a line already fully refunded', ok(refuses(() => B.dispute(p, { ...st, lines: { l1: { artwork_refunded_cents: 100000, commission_returned_cents: 15000 } } },
    { outcome: 'lost', amount_cents: 1000, attribution: { lines: [{ line_id: 'l1', artwork_cents: 1000 }] } }), /exceeds/)));
}
{
  const p = B.plan(await SMALL(), dec({ dispute_loss_bearer: 'artists_by_line', dispute_fee_bearer: 'plotart' }), TERMS2), s = B.settle(p, { fee_cents: 0, fee_vat_cents: 0 });
  const st = { artists: Object.fromEntries(s.artists.map(a => [a.artist_id, { transfer_due_cents: a.transfer_cents, transferred_cents: a.transfer_cents }])) };
  const x = B.dispute(p, st, { outcome: 'lost', amount_cents: 50000, fee_cents: 2000, attribution: { lines: [{ line_id: 'l2', artwork_cents: 50000 }] } });
  check('X14 mixed decision: artists carry the loss, PlotArt the fee', x.artists[0].dispute_fee_cents === 0 && x.artists[0].loss_cents === 50000 && x.platform_cost_cents === 2000);
}

/* ---------------------------------------------------------------- E · existing entitlement rule, real database */
console.log('— E entitlements: the EXISTING rule, artist/artwork/introduction and RECORDED consent read from a real D1 (schema.sql)');
let Miniflare = null;
for (const f of ['/tmp/claude-0/studio-tools/package.json', process.cwd() + '/package.json']) { try { ({ Miniflare } = createRequire(f)('miniflare')); break; } catch { /* next */ } }
if (!Miniflare) { console.log('  SKIP  section E: Miniflare not installed (npm i miniflare@3 in /tmp/claude-0/studio-tools)'); skipped++; }
else {
  const HERE = new URL('..', import.meta.url).pathname;
  const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'basket-rules-' + Date.now() } });
  const db = await mf.getD1Database('DB');
  for (const st of statements(readFileSync(HERE + 'schema.sql', 'utf8'))) await db.prepare(st).run();
  const t0 = '2026-11-01T10:00:00.000Z', t1 = '2026-11-10T10:00:00.000Z', H = 'a'.repeat(64);
  const artist = (aid, founding) => db.prepare('INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)').bind(aid, aid, aid + '@example.test', aid, founding, 'active', t0, t0).run();
  const work = (wid, aid) => db.prepare("INSERT INTO artworks (id, artist_id, slug, title, year, medium, h_cm, w_cm, price_eur, availability, description, ord, ai_involvement, archived, created_at, updated_at) VALUES (?,?,?,?,2026,'painting',50,40,1000,'available','d',1,'none',0,?,?)").bind(wid, aid, wid, wid, t0, t0).run();
  for (const [aid, f] of [['fia', 1], ['gal', 0], ['var', 0], ['fnt', 1], ['unk', 0]]) { await artist(aid, f); await work('w-' + aid, aid); }
  await work('w-gal2', 'gal');
  await db.prepare("INSERT INTO gallery_agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at) VALUES ('PA-GAA-2026-11','gallery_artist_agreement','GAA','fixed',?,?,?,?)").bind(H, H, t0, t0).run();
  for (const [aid, bp, v] of [['gal', 1500, null], ['var', 1000, '2026-11-01']]) {
    await db.prepare("INSERT INTO artist_terms (artist_id, track, commission_bp, variation_agreed_on, set_by, created_at, updated_at) VALUES (?, 'gallery_artist', ?, ?, 'founder', ?, ?)").bind(aid, bp, v, t0, t0).run();
    await db.prepare("INSERT INTO gallery_agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, method, statement, created_at) VALUES (?,?,?,'PA-GAA-2026-11',?,?,?,?,?,'studio_checkbox','I accept',?)")
      .bind('acc-' + aid, 'ev-' + aid, aid, H, H, t0, aid + '@example.test', aid, t0).run();
  }
  const enq = (ref, aid, wid, founding) => db.prepare("INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at, late_entry) VALUES (?,?,?,?,'relay',?,?,?,'relay',?,0)")
    .bind('e-' + ref, ref, aid, wid, t1, founding, founding ? '2027-11-04' : null, t1).run();
  await enq('PA-E-1', 'fia', 'w-fia', 1); await enq('PA-E-2', 'gal', 'w-gal', 0); await enq('PA-E-3', 'var', 'w-var', 0); await enq('PA-E-4', 'fnt', 'w-fnt', 0); await enq('PA-E-5', 'unk', 'w-unk', 0);
  await enq('PA-E-6', 'gal', null, 0);
  const consent = (aid, kind, at) => db.prepare("INSERT INTO payment_pilot_events (id, artist_id, kind, account_email, display_name, statement, at) VALUES (?,?,?,?,?,?,?)").bind('pe-' + aid + kind, aid, kind, aid + '@example.test', aid, kind === 'processing_consent' ? 'statement' : null, at).run();
  await consent('fia', 'processing_consent', t1); await consent('fnt', 'processing_consent', t0); await consent('fnt', 'processing_consent_withdrawn', t1);
  const env = { DB: db, ENVIRONMENT: 'test' };
  const reqs = [
    { line_id: 'l1', artist_id: 'fia', artwork_id: 'w-fia', enquiry_ref: 'PA-E-1' },
    { line_id: 'l2', artist_id: 'gal', artwork_id: 'w-gal', enquiry_ref: 'PA-E-2' },
    { line_id: 'l3', artist_id: 'var', artwork_id: 'w-var', enquiry_ref: 'PA-E-3' },
    { line_id: 'l4', artist_id: 'fnt', artwork_id: 'w-fnt', enquiry_ref: 'PA-E-4' },
    { line_id: 'l5', artist_id: 'unk', artwork_id: 'w-unk', enquiry_ref: 'PA-E-5' },
    { line_id: 'l6', artist_id: 'gal', artwork_id: 'w-gal2', enquiry_ref: '' },
    { line_id: 'l7', artist_id: 'gal', artwork_id: 'w-gal2', enquiry_ref: 'PA-E-NOPE' },
    { line_id: 'l8', artist_id: 'gal', artwork_id: 'w-gal2', enquiry_ref: 'PA-E-6' },
    { line_id: 'l9', artist_id: 'fia', artwork_id: 'w-gal2', enquiry_ref: 'PA-E-1' },
  ];
  const e = await B.lineEntitlements(env, reqs, DEC, { at: T });
  check('E1 Founding 25 artist, Founding Enquiry for this artwork → 0%, basis founding_enquiry', e.l1.ok && e.l1.bp === 0 && e.l1.basis === 'founding_enquiry');
  check('E2 Gallery Artist with the agreement accepted before the introduction → 15%', e.l2.ok && e.l2.bp === 1500 && e.l2.basis === 'gallery_artist_agreement');
  check('E3 Gallery Artist with a written 10% variation → 10%', e.l3.ok && e.l3.bp === 1000);
  check('E4 Founding Artist, non-founding enquiry, no commission terms → 0% (never inferred)', e.l4.ok && e.l4.bp === 0 && e.l4.basis === 'founding_artist_no_commission_terms');
  check('E5 non-founding artist without accepted terms → blocked (entitlement unknown)', e.l5.ok === false && /entitlement unknown/.test(e.l5.reason));
  check('E6 a line naming no introduction → blocked by basket_introduction = logged_enquiry_only', e.l6.ok === false && /basket_introduction/.test(e.l6.reason));
  check('E7 an introduction that is not logged → blocked', e.l7.ok === false && /No PlotArt introduction is logged/.test(e.l7.reason));
  check('E8 [M3] a logged introduction with no artwork → blocked for a basket line (founder decision)', e.l8.ok === false && /not tied to an artwork/.test(e.l8.reason));
  check('E9 [M3] an artwork that is not the named artist\'s → blocked', e.l9.ok === false && /not this artist/.test(e.l9.reason));
  check('E10 [M3] consent is read from payment_pilot_events: given (fia), withdrawn after giving (fnt), never given (gal)',
    e.l1.processing_consent === true && e.l1.processing_consent_at === t1 && e.l4.processing_consent === false && e.l2.processing_consent === false);
  const lines = ['l1', 'l2', 'l3', 'l4'].map((lid, i) => ({ line_id: lid, artist_id: reqs[i].artist_id, artwork_id: reqs[i].artwork_id, shipment_id: 's' + i, artwork_cents: 100000, entitlement: e[lid] }));
  const shipments = lines.map((l, i) => ship('s' + i, l.artist_id, 1000, 0, COVER(100000)));
  const p = B.plan({ lines, shipments }, DEC, TERMS2);
  check('E11 the resolved entitlements drive the plan: 0 + 15,000 + 10,000 + 0 commission', JSON.stringify(p.lines.map(l => l.commission_cents)) === JSON.stringify([0, 15000, 10000, 0]) && p.commission_cents === 25000);
  check('E12 [H3] the same real Founding lines are refused under terms that do not permit commission-free sales', ok(refuses(() => B.plan({ lines, shipments }, DEC, TERMS1), /Commission-free sales stay on direct payment/)));
  check('E13 a basket including a blocked line is refused with that line\'s reason', ok(refuses(() => B.plan({ lines: [...lines, { line_id: 'l5', artist_id: 'unk', artwork_id: 'w-unk', shipment_id: 's9', artwork_cents: 1000, entitlement: e.l5 }], shipments: [...shipments, ship('s9', 'unk', 0, 0, COVER(1000))] }, DEC, TERMS2), /entitlement unknown/)));
  check('E14 no quote time → refused', ok(await refusesAsync(() => B.lineEntitlements(env, reqs, DEC, {}), /time of the basket quote/)));
  await mf.dispose();
}

const failed = results.filter(x => !x).length;
console.log(`BASKET RULES · ${results.length} checks, ${results.length - failed} passed, ${failed} failed${skipped ? `, ${skipped} section skipped` : ''}`);
process.exit(failed ? 1 : 0);
