// PROVE · multi-artist basket allocation rules (src/basket-rules.js, Phase 1). Local only, offline: no Stripe, no network,
// no Worker. Sections D–X are pure. Section E runs the EXISTING entitlement rule (checkout-rules.entitlement) unchanged
// against a throwaway Miniflare D1 built from schema.sql, then feeds its results into the basket plan.
//   node test/prove-basket-rules.mjs            (section E is skipped, and reported as skipped, if Miniflare is absent)
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import * as B from '../src/basket-rules.js';
import * as R from '../src/checkout-rules.js';
import { statements } from './sql.mjs';

const results = []; let skipped = 0;
// an exception escaping a section (for example an engine invariant refusing an unbalanced result) is a failure, reported
process.on('uncaughtException', e => { console.log(`  FAIL  uncaught: ${e.message}`); console.log(`BASKET RULES · stopped after ${results.length} checks: FAILED`); process.exit(1); });
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d !== '' ? `  [${String(d).slice(0, 500)}]` : ''}`); };
const refuses = (fn, re) => { try { fn(); return false; } catch (e) { return e instanceof R.RuleError && (!re || re.test(e.message)) ? true : `${e.constructor.name}: ${e.message}`; } };
const ok = r => r === true;
const sum = xs => xs.reduce((a, b) => a + b, 0);

// deterministic pseudo-random numbers for the property checks (no Math.random: a failure must be reproducible)
let seed = 20261121; const rnd = n => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed % n; };

const DEC = { processing_fee_bearer: 'plotart', transfer_timing: 'on_payment', dispute_loss_bearer: 'plotart', dispute_fee_bearer: 'plotart', basket_introduction: 'logged_enquiry_only' };
const dec = over => ({ ...DEC, ...over });
const COVER = v => ({ cover_type: 'transit_insurance', covered_value_cents: v, insured_party: 'transporter' });
const GAL = { ok: true, bp: 1500, basis: 'gallery_artist_agreement', evidence: { rule: 'PA-GAA cl. 5' } };
const FOUND = { ok: true, bp: 0, basis: 'founding_enquiry', evidence: { rule: 'PA-FAA cl. 5' } };
const line = (line_id, artist_id, artwork_id, shipment_id, artwork_cents, entitlement = GAL, extra = {}) => ({ line_id, artist_id, artwork_id, shipment_id, artwork_cents, entitlement, ...extra });
const ship = (shipment_id, artist_id, delivery_cents, insurance_cents, cover = COVER(999999), method = 'delivery') => ({ shipment_id, artist_id, method, delivery_cents, insurance_cents, cover });
// The standard fixture: Rowan (Gallery Artist, 15%) ships two works together; Alder (Founding Enquiry, 0%) is collected.
const BASKET = () => ({
  lines: [line('l1', 'rowan', 'w1', 's1', 145000), line('l2', 'rowan', 'w2', 's1', 125000), line('l3', 'alder', 'w3', 's2', 210000, FOUND)],
  shipments: [ship('s1', 'rowan', 2500, 1000, COVER(270000)), { shipment_id: 's2', artist_id: 'alder', method: 'collection', delivery_cents: 0, insurance_cents: 0 }],
});
// Smaller fixture, below the EUR 10,000 pilot ceiling, for refund and dispute arithmetic
const SMALL = () => ({
  lines: [line('l1', 'rowan', 'w1', 's1', 100000), line('l2', 'alder', 'w2', 's2', 50000, FOUND)],
  shipments: [ship('s1', 'rowan', 5000, 2500, COVER(100000)), ship('s2', 'alder', 3000, 0, COVER(50000))],
});

console.log('PROVE · multi-artist basket allocation rules (offline)');

/* ---------------------------------------------------------------- D · founder decisions are explicit inputs */
console.log('— D founder decisions: required, no defaults');
for (const k of Object.keys(B.DECISIONS)) { const d = dec(); delete d[k]; check(`D1 missing decision ${k} is refused`, ok(refuses(() => B.decisions(d), new RegExp(`Founder decision required: ${k}`)))); }
check('D2 an unknown value is refused', ok(refuses(() => B.decisions(dec({ processing_fee_bearer: 'split_evenly' })), /must be one of/)));
check('D3 an unknown decision key is refused', ok(refuses(() => B.decisions({ ...DEC, payout_delay_days: 14 }), /Unknown founder decision/)));
check('D4 no decisions at all is refused (plan() has no defaults)', ok(refuses(() => B.plan(BASKET()), /Founder decisions are required/)));
check('D5 a valid set is returned frozen and unchanged', (() => { const d = B.decisions(DEC); return Object.isFrozen(d) && JSON.stringify(d) === JSON.stringify(DEC); })());
check('D6 commission eligibility has only the existing rule (logged introduction)', JSON.stringify(Object.keys(B.DECISIONS.basket_introduction)) === '["logged_enquiry_only"]');

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
    const p = B.apportion(total, w);
    const W = sum(w);
    if (sum(p) !== total || p.some((x, i) => !Number.isInteger(x) || x < Math.floor(total * w[i] / W) || x > Math.floor(total * w[i] / W) + 1)) bad = { total, w, p };
  }
  check('A7 3,000 random splits: exact sum, every part is the floor or floor+1 of its exact share', !bad, JSON.stringify(bad));
}

/* ---------------------------------------------------------------- N · normal purchases and validation */
console.log('— N normal purchases: per-artwork commission, per-shipment delivery, net proceeds');
const p1 = B.plan(BASKET(), DEC);
const rowan = p1.artists.find(a => a.artist_id === 'rowan'), alder = p1.artists.find(a => a.artist_id === 'alder');
check('N1 one total for the whole basket (artworks + every shipment charge)', p1.total_cents === 145000 + 125000 + 210000 + 2500 + 1000, p1.total_cents);
check('N2 commission is 15% of each Gallery artwork only: 21,750 + 18,750', rowan.commission_cents === 21750 + 18750 && p1.commission_cents === 40500, rowan.commission_cents);
check('N3 the Founding Enquiry line carries 0% commission', alder.commission_cents === 0 && p1.lines.find(l => l.line_id === 'l3').commission_basis === 'founding_enquiry');
check('N4 delivery and insurance go to the shipping artist and carry no commission', rowan.delivery_cents === 2500 && rowan.insurance_cents === 1000 && rowan.gross_cents === 273500 && rowan.transfer_before_fees_cents === 273500 - 40500);
check('N5 the collected artist is allocated their artwork in full', alder.gross_cents === 210000 && alder.transfer_before_fees_cents === 210000);
check('N6 the plan balances: total = commission + every artist transfer', p1.total_cents === p1.commission_cents + sum(p1.artists.map(a => a.transfer_before_fees_cents)));
check('N7 checkout items sum to the total, artist by artist, delivery and insurance itemised', sum(p1.items.map(i => i.amount_cents)) === p1.total_cents
  && JSON.stringify(p1.items.map(i => i.kind + ':' + i.ref)) === JSON.stringify(['artwork:l3', 'artwork:l1', 'artwork:l2', 'delivery:s1', 'insurance:s1']));
check('N8 artists are in a stable order (by id) and carry the transfer-timing decision', JSON.stringify(p1.artists.map(a => a.artist_id)) === '["alder","rowan"]' && p1.artists.every(a => a.release === 'on_payment'));
check('N9 the plan is deeply frozen and snapshots the decisions', Object.isFrozen(p1) && Object.isFrozen(p1.artists[0]) && Object.isFrozen(p1.lines[0]) && p1.decisions.processing_fee_bearer === 'plotart');
check('N10 the entitlement evidence is kept on each line', p1.lines.find(l => l.line_id === 'l1').entitlement_evidence.rule === 'PA-GAA cl. 5');
{
  // commission is floored PER ARTWORK (in the artist's favour), not on the artist's total
  const p = B.plan({ lines: [line('a', 'x', 'w1', 's', 333), line('b', 'x', 'w2', 's', 333)], shipments: [ship('s', 'x', 0, 0, COVER(666))] }, DEC);
  check('N11 rounding: two €3.33 works at 15% → 49 + 49 cents (not 99 on the €6.66 total)', p.commission_cents === 98 && p.artists[0].transfer_before_fees_cents === 666 - 98);
}
{
  const vari = { ok: true, bp: 1000, basis: 'gallery_artist_agreement', evidence: { rate_bp: 1000, variation_agreed_on: '2026-11-01' } };
  const fa = { ok: true, bp: 0, basis: 'founding_artist_no_commission_terms' };
  const p = B.plan({ lines: [line('a', 'x', 'w1', 'sx', 100000), line('b', 'y', 'w2', 'sy', 100000, vari), line('c', 'z', 'w3', 'sz', 100000, fa)],
    shipments: [ship('sx', 'x', 1000, 0), ship('sy', 'y', 2000, 0), ship('sz', 'z', 3000, 0)] }, DEC);
  check('N12 mixed rates in one basket: 15%, a 10% written variation, and a Founding Artist without terms (0%)',
    JSON.stringify(p.artists.map(a => [a.artist_id, a.commission_cents, a.transfer_before_fees_cents])) === JSON.stringify([['x', 15000, 86000], ['y', 10000, 92000], ['z', 0, 103000]]));
}
{
  const p = B.plan({ lines: [line('a', 'x', 'w1', 's1', 40000), line('b', 'x', 'w2', 's2', 30000)],
    shipments: [ship('s1', 'x', 4000, 500, COVER(40000)), { shipment_id: 's2', artist_id: 'x', method: 'collection', delivery_cents: 0, insurance_cents: 0 }] }, DEC);
  check('N13 one artist, two shipments (one delivered, one collected)', p.artists.length === 1 && p.artists[0].shipment_ids.length === 2 && p.artists[0].gross_cents === 74500);
}
{
  const p = B.plan({ lines: [line('a', 'x', 'w1', 's1', 40000, FOUND), line('b', 'y', 'w2', 's2', 30000, FOUND)], shipments: [ship('s1', 'x', 0, 0), ship('s2', 'y', 0, 0)] }, DEC);
  check('N14 a basket of commission-free sales only: no commission, every artist allocated in full', p.commission_cents === 0 && p.artists.every(a => a.transfer_before_fees_cents === a.gross_cents));
}
console.log('— N validation: everything a basket must not contain');
const mut = f => { const b = BASKET(); f(b); return () => B.plan(b, DEC); };
const V = [
  ['an unresolved entitlement blocks with its own reason', mut(b => { b.lines[0].entitlement = { ok: false, reason: 'Commission entitlement unknown: no accepted terms' }; }), /Commission entitlement unknown/],
  ['a missing entitlement blocks', mut(b => { delete b.lines[0].entitlement; }), /entitlement is required/],
  ['an entitlement without a basis is refused', mut(b => { b.lines[0].entitlement = { ok: true, bp: 1500 }; }), /basis/],
  ['a rate above 15% is refused', mut(b => { b.lines[0].entitlement = { ...GAL, bp: 1600 }; }), /Commission rate/],
  ['a fractional rate is refused', mut(b => { b.lines[0].entitlement = { ...GAL, bp: 1500.5 }; }), /Commission rate/],
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
  ['a delivery without insurance cover is refused', mut(b => { b.shipments[0].cover = null; }), /transit insurance/],
  ['cover below the artworks it carries is refused', mut(b => { b.shipments[0].cover = COVER(269999); }), /at least the artwork price/],
  ['cover held by PlotArt is refused (existing rule)', mut(b => { b.shipments[0].cover = { ...COVER(270000), insured_party: 'plotart' }; }), /Name who holds/],
  ['delivery + insurance above the pilot ceiling is refused', mut(b => { b.shipments[0].delivery_cents = R.MAX_DELIVERY_CENTS; }), /pilot ceiling/],
  ['an unknown shipment method is refused', mut(b => { b.shipments[0].method = 'drone'; }), /delivery or collection/],
  ['a malformed id is refused', mut(b => { b.lines[0].artist_id = 'rowan; DROP TABLE'; }), /letters, digits/],
  ['an empty basket is refused', () => B.plan({ lines: [], shipments: [] }, DEC), /at least one artwork/],
  ['a basket of EUR 10,000 or more is refused (existing pilot AML scope)', () => B.plan({ lines: [line('a', 'x', 'w1', 's', 999999), line('b', 'x', 'w2', 's', 1)], shipments: [ship('s', 'x', 0, 0)] }, DEC), /between EUR 1.00|EUR 10,000/],
  ['more than the technical maximum of lines is refused', () => B.plan({ lines: Array.from({ length: B.MAX_BASKET_LINES + 1 }, (_, i) => line('l' + i, 'x', 'w' + i, 's', 100)), shipments: [ship('s', 'x', 0, 0)] }, DEC), /at most/],
];
for (const [n, f, re] of V) { const r = refuses(f, re); check('N15 ' + n, ok(r), r); }
{
  const b = { lines: [line('a', 'x', 'w1', 's', 900000), line('b', 'x', 'w2', 's', 99999)], shipments: [ship('s', 'x', 1, 0)] };
  check('N16 the €10,000 ceiling is on the whole basket, delivery included (€9,999.99 + €0.01 is refused)', ok(refuses(() => B.plan(b, DEC), /EUR 10,000/)));
}
console.log('— N processing consent (existing rule) when artists bear processing fees');
const pr = dec({ processing_fee_bearer: 'artists_pro_rata' });
check('N17 artists bear fees + a commission-free line without consent: refused', ok(refuses(() => B.plan(BASKET(), pr), /separately consent/)));
check('N18 with the artist\'s separate consent on that line: accepted', (() => { const b = BASKET(); b.lines[2].processing_consent = true; return B.plan(b, pr).total_cents === p1.total_cents; })());
check('N19 PlotArt bears fees: no consent needed on commission-free lines', B.plan(BASKET(), DEC).total_cents > 0);
check('N20 a consent flag that is not yes/no is refused', ok(refuses(mut(b => { b.lines[2].processing_consent = 'yes'; }), /yes or no/)));

/* ---------------------------------------------------------------- S · settlement with Stripe's actual fee */
console.log('— S settlement: the actual processing fee, per decision');
{
  const s = B.settle(p1, { fee_cents: 7500, fee_vat_cents: 1725 });
  check('S1 PlotArt bears the fee: no artist share; artists receive the plan in full', s.artists.every(a => a.processing_share_cents === 0 && a.transfer_cents === a.transfer_before_fees_cents));
  check('S2 PlotArt net = commission − fee − VAT', s.platform_net_cents === 40500 - 9225 && s.platform_shortfall_cents === 0);
  check('S3 settlement balances: total = transfers + PlotArt net + fee', p1.total_cents === s.transfers_cents + s.platform_net_cents + s.fee_total_cents);
}
{
  const p = B.plan({ lines: [line('a', 'x', 'w1', 's', 50000, FOUND)], shipments: [ship('s', 'x', 0, 0)] }, DEC);
  const s = B.settle(p, { fee_cents: 1000, fee_vat_cents: 230 });
  check('S4 PlotArt bears the fee on a commission-free basket: the shortfall is reported, not hidden', s.platform_net_cents === -1230 && s.platform_shortfall_cents === 1230);
}
{
  const b = BASKET(); b.lines[2].processing_consent = true;
  const p = B.plan(b, pr), s = B.settle(p, { fee_cents: 7500, fee_vat_cents: 1725 });
  const expect = B.apportion(9225, p.artists.map(a => a.gross_cents));
  check('S5 artists bear the fee: shares are proportional to gross and sum exactly to fee + VAT', sum(s.artists.map(a => a.processing_share_cents)) === 9225 && JSON.stringify(s.artists.map(a => a.processing_share_cents)) === JSON.stringify(expect));
  check('S6 artists bear the fee: PlotArt keeps its full commission', s.platform_net_cents === p.commission_cents);
  check('S7 artists bear the fee: settlement balances', p.total_cents === s.transfers_cents + s.platform_net_cents + s.fee_total_cents);
  check('S8 a fee so large that a share exceeds an allocation is a FAILED allocation, never clipped', ok(refuses(() => B.settle(p, { fee_cents: p.total_cents, fee_vat_cents: 0 }), /Allocation failed/)));
}
check('S9 a fractional fee is refused', ok(refuses(() => B.settle(p1, { fee_cents: 10.5, fee_vat_cents: 0 }))));
check('S10 a hand-built (unfrozen) plan is refused', ok(refuses(() => B.settle(JSON.parse(JSON.stringify(p1)), { fee_cents: 0, fee_vat_cents: 0 }), /plan\(\) is required/)));

/* ---------------------------------------------------------------- property: random baskets */
{
  let bad = null;
  for (let t = 0; t < 400 && !bad; t++) {
    const nArt = 1 + rnd(4), lines = [], shipments = [];
    for (let a = 0; a < nArt; a++) {
      const nShip = 1 + rnd(2);
      for (let s = 0; s < nShip; s++) shipments.push({ shipment_id: `s${a}_${s}`, artist_id: `a${a}`, method: 'delivery', delivery_cents: rnd(5000), insurance_cents: rnd(800), cover: COVER(999999) });
      for (let k = 0; k < 1 + rnd(2); k++) {
        const bp = [0, 1500, 1000, 1250][rnd(4)];
        lines.push({ line_id: `l${lines.length}`, artist_id: `a${a}`, artwork_id: `w${lines.length}`, shipment_id: `s${a}_${rnd(nShip)}`, artwork_cents: 100 + rnd(80000),
          entitlement: { ok: true, bp, basis: bp ? 'gallery_artist_agreement' : 'founding_enquiry' }, processing_consent: true });
      }
    }
    // keep only shipments that carry something
    const used = new Set(lines.map(l => l.shipment_id)); const sh = shipments.filter(s => used.has(s.shipment_id));
    const bearer = rnd(2) ? 'plotart' : 'artists_pro_rata';
    try {
      const p = B.plan({ lines, shipments: sh }, dec({ processing_fee_bearer: bearer }));
      const fee = rnd(Math.floor(p.total_cents / 20) + 1), vat = Math.floor(fee * 23 / 100);
      const s = B.settle(p, { fee_cents: fee, fee_vat_cents: vat });
      const lineSum = sum(p.lines.map(l => l.commission_cents)), expectLine = p.lines.every(l => l.commission_cents === Math.floor(l.artwork_cents * l.commission_bp / 10000));
      if (p.total_cents !== p.commission_cents + sum(p.artists.map(a => a.transfer_before_fees_cents)) || lineSum !== p.commission_cents || !expectLine
        || p.total_cents !== s.transfers_cents + s.platform_net_cents + s.fee_total_cents || s.artists.some(a => a.transfer_cents < 0)) bad = { t, bearer };
    } catch (e) { if (!/EUR 10,000/.test(e.message)) bad = { t, error: e.message }; }
  }
  check('S11 400 random baskets: per-artwork floor commission, plan and settlement balance to the cent, no negative transfer', !bad, JSON.stringify(bad));
}

/* ---------------------------------------------------------------- F · refunds */
console.log('— F refunds: commission returned per PA-GAA 9.2, recovery from artists');
const sp = B.plan(SMALL(), DEC), ss = B.settle(sp, { fee_cents: 2500, fee_vat_cents: 575 });
const settled = (over = {}) => ({ artists: Object.fromEntries(ss.artists.map(a => [a.artist_id, { transfer_due_cents: a.transfer_cents, transferred_cents: a.transfer_cents, reversed_cents: 0, pending_reduced_cents: 0, ...(over[a.artist_id] || {}) }])) });
{
  const r = B.refund(sp, settled(), { lines: [{ line_id: 'l1', artwork_cents: 50000 }] });
  check('F1 €500 refunded on a €1,000 work at 15%: €75 commission returned, artist debited €425 (PA-PAY example 2)', r.commission_returned_cents === 7500 && r.lines[0].artist_debit_cents === 42500 && r.buyer_refund_cents === 50000);
  check('F2 the artist debit is recovered by reversing the transfer already made', r.artists[0].reverse_cents === 42500 && r.artists[0].reduce_pending_cents === 0 && r.shortfall_cents === 0);
  check('F3 the refund balances: buyer refund = artist debits + commission returned', r.buyer_refund_cents === sum(r.artists.map(a => a.debit_cents)) + r.commission_returned_cents);
}
{
  const r = B.refund(sp, settled(), { lines: [{ line_id: 'l1', artwork_cents: 100000 }], shipments: [{ shipment_id: 's1', cents: 7500 }] });
  check('F4 full refund of a work and its shipment: full commission returned, delivery + insurance debited in full', r.commission_returned_cents === 15000 && r.artists[0].debit_cents === 85000 + 7500 && r.buyer_refund_cents === 107500);
}
{
  const r = B.refund(sp, settled(), { lines: [{ line_id: 'l2', artwork_cents: 50000 }] });
  check('F5 a Founding (0%) line: nothing to return, the artist is debited the refund', r.commission_returned_cents === 0 && r.artists[0].debit_cents === 50000);
}
{
  // successive partial refunds on an awkward price: commission returned always matches PA-GAA 9.2 on the cumulative total
  const p = B.plan({ lines: [line('a', 'x', 'w1', 's', 999)], shipments: [ship('s', 'x', 0, 0, COVER(999))] }, DEC), s = B.settle(p, { fee_cents: 0, fee_vat_cents: 0 });
  let st = { lines: { a: { artwork_refunded_cents: 0, commission_returned_cents: 0 } }, artists: { x: { transfer_due_cents: s.artists[0].transfer_cents, transferred_cents: s.artists[0].transfer_cents, reversed_cents: 0 } } };
  const got = [];
  for (const amt of [333, 333, 333]) {
    const r = B.refund(p, st, { lines: [{ line_id: 'a', artwork_cents: amt }] });
    got.push(r.commission_returned_cents);
    st = { lines: { a: { artwork_refunded_cents: st.lines.a.artwork_refunded_cents + amt, commission_returned_cents: st.lines.a.commission_returned_cents + r.commission_returned_cents } },
      artists: { x: { ...st.artists.x, reversed_cents: st.artists.x.reversed_cents + r.artists[0].reverse_cents } } };
  }
  const kept = k => Math.floor(149 * k / 999);
  check('F6 rounding: three €3.33 refunds of a €9.99 work at 15% return 149 − kept(666), …, the whole 149 in total',
    p.commission_cents === 149 && JSON.stringify(got) === JSON.stringify([149 - kept(666), kept(666) - kept(333), kept(333)]) && sum(got) === 149, JSON.stringify(got));
  check('F7 after the last refund the whole transfer has been reversed', st.artists.x.reversed_cents === 999 - 149);
}
{
  const late = settled({ rowan: { transferred_cents: 0 } });
  const r = B.refund(sp, late, { lines: [{ line_id: 'l1', artwork_cents: 20000 }] });
  check('F8 transfer not yet made (held until delivery): the debit reduces the pending transfer, nothing is reversed', r.artists[0].reduce_pending_cents === 17000 && r.artists[0].reverse_cents === 0);
  const part = settled({ rowan: { transferred_cents: 0, pending_reduced_cents: 80000 } });
  const r2 = B.refund(sp, part, { lines: [{ line_id: 'l1', artwork_cents: 20000 }] });
  check('F9 pending first, then a SHORTFALL when neither pending nor transferred money covers it', r2.artists[0].reduce_pending_cents === ss.artists.find(a => a.artist_id === 'rowan').transfer_cents - 80000 && r2.shortfall_cents === 17000 - r2.artists[0].reduce_pending_cents);
}
{
  const b = SMALL(); b.lines[1].processing_consent = true;
  const p = B.plan(b, pr), s = B.settle(p, { fee_cents: 2500, fee_vat_cents: 575 });
  const st = { artists: Object.fromEntries(s.artists.map(a => [a.artist_id, { transfer_due_cents: a.transfer_cents, transferred_cents: a.transfer_cents }])) };
  const r = B.refund(p, st, { lines: [{ line_id: 'l1', artwork_cents: 100000 }], shipments: [{ shipment_id: 's1', cents: 7500 }] });
  const share = s.artists.find(a => a.artist_id === 'rowan').processing_share_cents;
  check('F10 FAILED ALLOCATION surfaced: artists bore the fee, full refund → shortfall equals that artist\'s fee share', r.shortfall_cents === share && share > 0, `${r.shortfall_cents} vs ${share}`);
}
const RF = [
  ['a refund above the artwork amount', { lines: [{ line_id: 'l1', artwork_cents: 100001 }] }, /exceeds/],
  ['a refund above the shipment charges', { shipments: [{ shipment_id: 's1', cents: 7501 }] }, /exceeds/],
  ['a zero refund', { lines: [{ line_id: 'l1', artwork_cents: 0 }] }, /more than zero/],
  ['an unknown line', { lines: [{ line_id: 'zz', artwork_cents: 1 }] }, /Unknown line/],
  ['the same line twice', { lines: [{ line_id: 'l1', artwork_cents: 1 }, { line_id: 'l1', artwork_cents: 1 }] }, /named twice/],
  ['an empty request', {}, /Name what/],
];
for (const [n, req, re] of RF) check('F11 refused: ' + n, ok(refuses(() => B.refund(sp, settled(), req), re)));
check('F12 refused: a refund beyond what is left after earlier refunds', ok(refuses(() => B.refund(sp, { ...settled(), lines: { l1: { artwork_refunded_cents: 90000, commission_returned_cents: 13500 } } }, { lines: [{ line_id: 'l1', artwork_cents: 10001 }] }), /exceeds/)));
check('F13 refused: a refund before the payment is settled', ok(refuses(() => B.refund(sp, {}, { lines: [{ line_id: 'l1', artwork_cents: 100 }] }), /settle the payment first/)));
check('F14 refused: an inconsistent transfer record (reversed more than transferred)', ok(refuses(() => B.refund(sp, settled({ rowan: { reversed_cents: 999999 } }), { lines: [{ line_id: 'l1', artwork_cents: 100 }] }), /inconsistent/)));
{
  let bad = null;
  for (let t = 0; t < 500 && !bad; t++) {
    const before = rnd(100001), now = 1 + rnd(100000 - Math.min(before, 99999));
    if (before + now > 100000) continue;
    const cb = Math.max(0, 15000 - Math.floor(15000 * (100000 - before) / 100000));
    try {
      const r = B.refund(sp, { ...settled(), lines: { l1: { artwork_refunded_cents: before, commission_returned_cents: cb } } }, { lines: [{ line_id: 'l1', artwork_cents: now }] });
      const keptAfter = Math.floor(15000 * (100000 - before - now) / 100000);
      if (r.buyer_refund_cents !== sum(r.artists.map(a => a.debit_cents)) + r.commission_returned_cents || cb + r.commission_returned_cents !== 15000 - keptAfter
        || r.artists.some(a => a.debit_cents !== a.reduce_pending_cents + a.reverse_cents + a.shortfall_cents)) bad = { before, now };
    } catch (e) { bad = { before, now, e: e.message }; }
  }
  check('F15 500 random partial refunds: balanced, commission kept always floor(C × kept / A), debits fully accounted', !bad, JSON.stringify(bad));
}

/* ---------------------------------------------------------------- X · disputes */
console.log('— X disputes: debited from PlotArt; recovery only as the founder decides');
{
  const o = B.dispute(sp, settled(), { outcome: 'open', amount_cents: sp.total_cents, fee_cents: 2000 });
  const w = B.dispute(sp, settled(), { outcome: 'won', amount_cents: sp.total_cents, fee_cents: 2000 });
  check('X1 an open or won dispute moves nothing between PlotArt and artists', o.artists.length === 0 && w.artists.length === 0 && o.platform_cost_cents === 0);
}
{
  const x = B.dispute(sp, settled(), { outcome: 'lost', amount_cents: sp.total_cents, fee_cents: 2000 });
  check('X2 lost, PlotArt bears loss and fee: no artist is debited; PlotArt\'s cost = amount + fee', x.artists.every(a => a.debit_cents === 0) && x.platform_cost_cents === sp.total_cents + 2000);
}
const XD = dec({ dispute_loss_bearer: 'artists_by_line', dispute_fee_bearer: 'artists_by_line' });
{
  const p = B.plan(SMALL(), XD), s = B.settle(p, { fee_cents: 2500, fee_vat_cents: 575 });
  const st = { artists: Object.fromEntries(s.artists.map(a => [a.artist_id, { transfer_due_cents: a.transfer_cents, transferred_cents: a.transfer_cents }])) };
  const x = B.dispute(p, st, { outcome: 'lost', amount_cents: 100000, fee_cents: 2000, attribution: { lines: [{ line_id: 'l1', artwork_cents: 100000 }] } });
  const r = x.artists.find(a => a.artist_id === 'rowan');
  check('X3 lost, attributed to Rowan\'s work: commission returned (PA-GAA 9.1), Rowan recovers €850 + the €20 fee', x.commission_returned_cents === 15000 && r.loss_cents === 85000 && r.dispute_fee_cents === 2000 && r.debit_cents === 87000);
  check('X4 PlotArt\'s cost is only the commission it returned', x.platform_cost_cents === 15000);
  check('X5 the dispute balances: amount + fee = artist recoveries + PlotArt\'s cost', 100000 + 2000 === sum(x.artists.map(a => a.debit_cents)) + x.platform_cost_cents);
  check('X6 the other artist is not touched', !x.artists.some(a => a.artist_id === 'alder'));
  const y = B.dispute(p, st, { outcome: 'lost', amount_cents: p.total_cents, fee_cents: 2001 });
  check('X7 lost without an attribution: spread over every line and shipment in proportion to what is unrefunded', sum(y.lines.map(l => l.artwork_refund_cents)) + sum(y.shipments.map(s => s.refund_cents)) === p.total_cents
    && sum(y.artists.map(a => a.dispute_fee_cents)) === 2001 && p.total_cents + 2001 === sum(y.artists.map(a => a.debit_cents)) + y.platform_cost_cents);
  const after = B.dispute(p, { ...st, lines: { l1: { artwork_refunded_cents: 100000, commission_returned_cents: 15000 } } }, { outcome: 'lost', amount_cents: 50000, fee_cents: 0 });
  check('X8 a dispute after a full refund of one work is attributed only to what is still unrefunded', !after.lines.some(l => l.line_id === 'l1'));
  check('X9 refused: an attribution that does not add up to the disputed amount', ok(refuses(() => B.dispute(p, st, { outcome: 'lost', amount_cents: 100000, attribution: { lines: [{ line_id: 'l1', artwork_cents: 99999 }] } }), /add up/)));
  check('X10 refused: a disputed amount above what remains unrefunded', ok(refuses(() => B.dispute(p, st, { outcome: 'lost', amount_cents: p.total_cents + 1 }), /no more than/)));
  check('X11 refused: an unknown outcome', ok(refuses(() => B.dispute(p, st, { outcome: 'maybe', amount_cents: 1 }), /open, won or lost/)));
}
{
  const p = B.plan(SMALL(), dec({ dispute_loss_bearer: 'artists_by_line', dispute_fee_bearer: 'plotart' })), s = B.settle(p, { fee_cents: 0, fee_vat_cents: 0 });
  const st = { artists: Object.fromEntries(s.artists.map(a => [a.artist_id, { transfer_due_cents: a.transfer_cents, transferred_cents: a.transfer_cents }])) };
  const x = B.dispute(p, st, { outcome: 'lost', amount_cents: 50000, fee_cents: 2000, attribution: { lines: [{ line_id: 'l2', artwork_cents: 50000 }] } });
  check('X12 mixed decision: artists carry the loss, PlotArt the fee', x.artists[0].dispute_fee_cents === 0 && x.artists[0].loss_cents === 50000 && x.platform_cost_cents === 2000);
}

/* ---------------------------------------------------------------- E · existing entitlement rule, unchanged */
console.log('— E entitlements: the EXISTING rule resolves each line (Miniflare D1 from schema.sql)');
let Miniflare = null;
for (const f of ['/tmp/claude-0/studio-tools/package.json', process.cwd() + '/package.json']) { try { ({ Miniflare } = createRequire(f)('miniflare')); break; } catch { /* next */ } }
if (!Miniflare) { console.log('  SKIP  section E: Miniflare not installed (npm i miniflare@3 in /tmp/claude-0/studio-tools)'); skipped++; }
else {
  const HERE = new URL('..', import.meta.url).pathname;
  const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'basket-rules-' + Date.now() } });
  const db = await mf.getD1Database('DB');
  for (const st of statements(readFileSync(HERE + 'schema.sql', 'utf8'))) await db.prepare(st).run();
  const t0 = '2026-11-01T10:00:00.000Z', t1 = '2026-11-10T10:00:00.000Z', at = '2026-11-21T10:00:00.000Z', H = 'a'.repeat(64);
  const artist = async (id, founding) => db.prepare('INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)')
    .bind(id, id, id + '@example.test', id, founding, 'active', t0, t0).run();
  await artist('fia', 1); await artist('gal', 0); await artist('var', 0); await artist('fnt', 1); await artist('unk', 0);
  await db.prepare("INSERT INTO gallery_agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at) VALUES ('PA-GAA-2026-11','gallery_artist_agreement','GAA','fixed',?,?,?,?)").bind(H, H, t0, t0).run();
  for (const [aid, bp, v] of [['gal', 1500, null], ['var', 1000, '2026-11-01']]) {
    await db.prepare("INSERT INTO artist_terms (artist_id, track, commission_bp, variation_agreed_on, set_by, created_at, updated_at) VALUES (?, 'gallery_artist', ?, ?, 'founder', ?, ?)").bind(aid, bp, v, t0, t0).run();
    await db.prepare("INSERT INTO gallery_agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, method, statement, created_at) VALUES (?,?,?,'PA-GAA-2026-11',?,?,?,?,?,'studio_checkbox','I accept',?)")
      .bind('acc-' + aid, 'ev-' + aid, aid, H, H, t0, aid + '@example.test', aid, t0).run();
  }
  const enq = (ref, aid, founding) => db.prepare("INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at, late_entry) VALUES (?,?,?,NULL,'relay',?,?,?,'relay',?,0)")
    .bind('e-' + ref, ref, aid, t1, founding, founding ? '2027-11-04' : null, t1).run();
  await enq('PA-E-1', 'fia', 1); await enq('PA-E-2', 'gal', 0); await enq('PA-E-3', 'var', 0); await enq('PA-E-4', 'fnt', 0); await enq('PA-E-5', 'unk', 0);
  const env = { DB: db };
  const row = async id => db.prepare('SELECT * FROM artists WHERE id = ?').bind(id).first();
  const reqs = [
    { line_id: 'l1', artist: await row('fia'), enquiry_ref: 'PA-E-1' },
    { line_id: 'l2', artist: await row('gal'), enquiry_ref: 'PA-E-2' },
    { line_id: 'l3', artist: await row('var'), enquiry_ref: 'PA-E-3' },
    { line_id: 'l4', artist: await row('fnt'), enquiry_ref: 'PA-E-4' },
    { line_id: 'l5', artist: await row('unk'), enquiry_ref: 'PA-E-5' },
    { line_id: 'l6', artist: await row('gal'), enquiry_ref: '' },
    { line_id: 'l7', artist: await row('gal'), enquiry_ref: 'PA-E-NOPE' },
  ];
  const e = await B.lineEntitlements(env, reqs, DEC, { at });
  check('E1 Founding 25 artist, Founding Enquiry → 0%, basis founding_enquiry', e.l1.ok && e.l1.bp === 0 && e.l1.basis === 'founding_enquiry');
  check('E2 Gallery Artist with the agreement accepted before the introduction → 15%', e.l2.ok && e.l2.bp === 1500 && e.l2.basis === 'gallery_artist_agreement');
  check('E3 Gallery Artist with a written 10% variation → 10%', e.l3.ok && e.l3.bp === 1000);
  check('E4 Founding Artist, non-founding enquiry, no commission terms → 0% (never inferred)', e.l4.ok && e.l4.bp === 0 && e.l4.basis === 'founding_artist_no_commission_terms');
  check('E5 non-founding artist without accepted terms → blocked (entitlement unknown)', e.l5.ok === false && /entitlement unknown/.test(e.l5.reason));
  check('E6 a line naming no introduction → blocked by basket_introduction = logged_enquiry_only', e.l6.ok === false && /basket_introduction/.test(e.l6.reason));
  check('E7 an introduction that is not logged → blocked (existing rule)', e.l7.ok === false && /No PlotArt introduction is logged/.test(e.l7.reason));
  const lines = ['l1', 'l2', 'l3', 'l4'].map((lid, i) => line(lid, reqs[i].artist.id, 'w' + i, 's' + i, 100000, e[lid]));
  const shipments = lines.map((l, i) => ship('s' + i, l.artist_id, 1000, 0, COVER(100000)));
  const p = B.plan({ lines, shipments }, DEC);
  check('E8 the resolved entitlements drive the plan: 0 + 15,000 + 10,000 + 0 commission', JSON.stringify(p.lines.map(l => l.commission_cents)) === JSON.stringify([0, 15000, 10000, 0]) && p.commission_cents === 25000);
  check('E9 a basket including a blocked line is refused with that line\'s reason', ok(refuses(() => B.plan({ lines: [...lines, line('l5', 'unk', 'w9', 's9', 1000, e.l5)], shipments: [...shipments, ship('s9', 'unk', 0, 0, COVER(1000))] }, DEC), /entitlement unknown/)));
  check('E10 no quote time → refused', await B.lineEntitlements(env, reqs, DEC, {}).then(() => false, err => err instanceof R.RuleError));
  await mf.dispose();
}

const failed = results.filter(x => !x).length;
console.log(`BASKET RULES · ${results.length} checks, ${results.length - failed} passed, ${failed} failed${skipped ? `, ${skipped} section skipped` : ''}`);
process.exit(failed ? 1 : 0);
