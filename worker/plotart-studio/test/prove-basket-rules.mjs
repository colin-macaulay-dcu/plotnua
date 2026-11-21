// PROVE · multi-artist basket allocation rules (src/basket-rules.js, revision 3). Local only, offline: no Stripe, no
// network, no Worker. EVERY entitlement here comes from lineEntitlements() reading a throwaway Miniflare D1 built from
// schema.sql through the EXISTING entitlement rule (checkout-rules.entitlement), unchanged: nothing is injected (review N5).
//   node test/prove-basket-rules.mjs
// Review regressions are marked: first review [P1]…[P7] [H3] [M3] [M4] [L1] [L2] [L4]; second review [N1] [N3] [N5] [N6].
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import * as B from '../src/basket-rules.js';
import * as R from '../src/checkout-rules.js';
import { statements } from './sql.mjs';

const results = [];
process.on('uncaughtException', e => { console.log(`  FAIL  uncaught: ${e.message}`); console.log(`BASKET RULES · stopped after ${results.length} checks: FAILED`); process.exit(1); });
process.on('unhandledRejection', e => { console.log(`  FAIL  unhandled: ${e && e.message}`); console.log(`BASKET RULES · stopped after ${results.length} checks: FAILED`); process.exit(1); });
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d !== '' ? `  [${String(d).slice(0, 500)}]` : ''}`); };
const refuses = (fn, re) => { try { fn(); return false; } catch (e) { return e instanceof R.RuleError && (!re || re.test(e.message)) ? true : `${e.constructor.name}: ${e.message}`; } };
const refusesAsync = async (fn, re) => { try { await fn(); return false; } catch (e) { return e instanceof R.RuleError && (!re || re.test(e.message)) ? true : `${e.constructor.name}: ${e.message}`; } };
const ok = r => r === true;
const sum = xs => xs.reduce((a, b) => a + b, 0);
let seed = 20261121; const rnd = n => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed % n; };

const HERE = new URL('..', import.meta.url).pathname;
const { Miniflare } = createRequire('/tmp/claude-0/studio-tools/package.json')('miniflare');
const mfs = [];
async function freshDb(withMig = false) {
  const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'br-' + Date.now() + Math.random() } });
  mfs.push(mf);
  const db = await mf.getD1Database('DB');
  for (const s of statements(readFileSync(HERE + 'schema.sql', 'utf8'))) await db.prepare(s).run();
  if (withMig) for (const s of statements(readFileSync(HERE + 'migrations/0019_basket_checkout.sql', 'utf8'))) await db.prepare(s).run();
  return db;
}
const db = await freshDb();
const ENV = { DB: db, ENVIRONMENT: 'test' };

const T = '2026-11-21T10:00:00.000Z', t0 = '2026-11-01T10:00:00.000Z', t1 = '2026-11-10T10:00:00.000Z', H = 'a'.repeat(64);
const DEC = { processing_fee_bearer: 'plotart', transfer_timing: 'on_payment', dispute_loss_bearer: 'plotart', dispute_fee_bearer: 'plotart', basket_introduction: 'logged_enquiry_only' };
const dec = over => ({ ...DEC, ...over });
const TERMS1 = { livemode: false, artist_terms_doc: 'PA-BASKET-TEST-01', buyer_terms_doc: 'PA-BASKET-BPT-TEST-01' };   // commission-free NOT permitted
const TERMS2 = { livemode: false, artist_terms_doc: 'PA-BASKET-TEST-02', buyer_terms_doc: 'PA-BASKET-BPT-TEST-02' };   // commission-free permitted
const TERMS3 = { livemode: false, artist_terms_doc: 'PA-BASKET-TEST-03', buyer_terms_doc: 'PA-BASKET-BPT-TEST-03' };   // only some decisions
const COVER = v => ({ cover_type: 'transit_insurance', covered_value_cents: v, insured_party: 'transporter' });

/* ---------------------------------------------------------------- real records in the database
   An artist's PROFILE fixes what the existing rule will decide for them:
     gal   Gallery Artist, standard 15% (artist_terms 1500, PA-GAA accepted before the introduction)
     var10 Gallery Artist on a written 10% variation;  var125 the same at 12.5%
     fa    Founding Artist without commission terms (0%, never inferred)
     unk   Gallery track artist with no accepted terms (entitlement unknown: blocked)
   A line's introduction is logged for that artist and that artwork, either as a Founding Enquiry ('F', 0% permanently)
   or not ('G'). Consent, when asked for, is recorded in payment_pilot_events, as the Studio records it. */
await db.prepare("INSERT INTO gallery_agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at) VALUES ('PA-GAA-2026-11','gallery_artist_agreement','GAA','fixed',?,?,?,?)").bind(H, H, t0, t0).run();
const profiles = new Map();
async function ensureArtist(aid, profile) {
  if (profiles.has(aid)) { if (profiles.get(aid) !== profile) throw new Error(`fixture: ${aid} is ${profiles.get(aid)}, not ${profile}`); return; }
  profiles.set(aid, profile);
  await db.prepare('INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)')
    .bind(aid, aid.toLowerCase().replace(/_/g, '-'), aid + '@example.test', aid, profile === 'fa' ? 1 : 0, 'active', t0, t0).run();
  const bp = { gal: 1500, var10: 1000, var125: 1250 }[profile];
  if (bp) {
    await db.prepare("INSERT INTO artist_terms (artist_id, track, commission_bp, variation_agreed_on, set_by, created_at, updated_at) VALUES (?, 'gallery_artist', ?, ?, 'founder', ?, ?)").bind(aid, bp, bp === 1500 ? null : '2026-11-01', t0, t0).run();
    await db.prepare("INSERT INTO gallery_agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, method, statement, created_at) VALUES (?,?,?,'PA-GAA-2026-11',?,?,?,?,?,'studio_checkbox','I accept',?)")
      .bind('acc-' + aid, 'ev-' + aid, aid, H, H, t0, aid + '@example.test', aid, t0).run();
  }
}
const works = new Set();
async function ensureWork(wid, aid) {
  if (works.has(wid)) return; works.add(wid);
  await db.prepare("INSERT INTO artworks (id, artist_id, slug, title, year, medium, h_cm, w_cm, price_eur, availability, description, ord, ai_involvement, archived, created_at, updated_at) VALUES (?,?,?,?,2026,'painting',50,40,1000,'available','d',1,'none',0,?,?)")
    .bind(wid, aid, wid.toLowerCase().replace(/_/g, '-'), wid, t0, t0).run();
}
const enquiries = new Set();
async function ensureEnquiry(ref, aid, wid, founding) {
  if (enquiries.has(ref)) return; enquiries.add(ref);
  await db.prepare("INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at, late_entry) VALUES (?,?,?,?,'relay',?,?,?,'relay',?,0)")
    .bind('e-' + ref, ref, aid, wid, t1, founding ? 1 : 0, founding ? '2027-11-04' : null, t1).run();
}
const consents = new Set();
async function ensureConsent(aid) {
  if (consents.has(aid)) return; consents.add(aid);
  await db.prepare("INSERT INTO payment_pilot_events (id, artist_id, kind, account_email, display_name, statement, at) VALUES (?,?,'processing_consent',?,?,'statement',?)").bind('pe-' + aid, aid, aid + '@example.test', aid, t1).run();
}
/* L(line, artist, work, shipment, cents, { profile, founding, consent }): a line resolved from the records. The artwork id in
   the database is "<artist>_<work>", so an original belongs to exactly one artist. */
const L = (line_id, artist_id, work, shipment_id, artwork_cents, o = {}) => ({ line_id, artist_id, artwork_id: `${artist_id}_${work}`, shipment_id, artwork_cents,
  profile: o.profile || 'gal', founding: !!o.founding, consent: !!o.consent });
async function sealed(specs, decs = DEC) {
  for (const s of specs) {
    await ensureArtist(s.artist_id, s.profile); await ensureWork(s.artwork_id, s.artist_id);
    await ensureEnquiry(`PA-E-${s.artwork_id}-${s.founding ? 'F' : 'G'}`, s.artist_id, s.artwork_id, s.founding);
    if (s.consent) await ensureConsent(s.artist_id);
  }
  const ents = await B.lineEntitlements(ENV, specs.map(s => ({ line_id: s.line_id, artist_id: s.artist_id, artwork_id: s.artwork_id, enquiry_ref: `PA-E-${s.artwork_id}-${s.founding ? 'F' : 'G'}` })), decs, { at: T });
  return specs.map(s => ({ line_id: s.line_id, artist_id: s.artist_id, artwork_id: s.artwork_id, shipment_id: s.shipment_id, artwork_cents: s.artwork_cents, entitlement: ents[s.line_id] }));
}
const ship = (shipment_id, artist_id, delivery_cents, insurance_cents, cover = COVER(999999), method = 'delivery') => ({ shipment_id, artist_id, method, delivery_cents, insurance_cents, cover });
const collect = (shipment_id, artist_id) => ({ shipment_id, artist_id, method: 'collection', delivery_cents: 0, insurance_cents: 0 });
// Rowan (Gallery Artist, 15%) ships two works together; Alder's work comes from a Founding Enquiry (0%) and is collected.
// Alder never records processing consent; Aldc (same position) has recorded it.
const BASKET = async (consent = false) => { const a = consent ? 'aldc' : 'alder';
  return { lines: await sealed([L('l1', 'rowan', 'w1', 's1', 145000), L('l2', 'rowan', 'w2', 's1', 125000), L('l3', a, 'w3', 's2', 210000, { founding: true, consent })]),
    shipments: [ship('s1', 'rowan', 2500, 1000, COVER(270000)), collect('s2', a)] }; };
const SMALL = async (consent = false) => { const a = consent ? 'aldc' : 'alder';
  return { lines: await sealed([L('l1', 'rowan', 'w1', 's1', 100000), L('l2', a, 'w2', 's2', 50000, { founding: true, consent })]),
    shipments: [ship('s1', 'rowan', 5000, 2500, COVER(100000)), ship('s2', a, 3000, 0, COVER(50000))] }; };

console.log('PROVE · multi-artist basket allocation rules (offline; entitlements from a real D1, nothing injected)');

/* ---------------------------------------------------------------- D · founder decisions are explicit inputs */
console.log('— D founder decisions: required, no defaults');
for (const k of Object.keys(B.DECISIONS)) { const d = dec(); delete d[k]; check(`D1 missing decision ${k} is refused`, ok(refuses(() => B.decisions(d), new RegExp(`Founder decision required: ${k}`)))); }
check('D2 an unknown value is refused', ok(refuses(() => B.decisions(dec({ processing_fee_bearer: 'split_evenly' })), /must be one of/)));
check('D3 an unknown decision key is refused', ok(refuses(() => B.decisions({ ...DEC, payout_delay_days: 14 }), /Unknown founder decision/)));
check('D4 no decisions at all is refused (plan() has no defaults)', ok(refuses(() => B.plan({ lines: [], shipments: [] }, undefined, TERMS1), /Founder decisions are required/)));
check('D5 a valid set is returned frozen and unchanged', (() => { const d = B.decisions(DEC); return Object.isFrozen(d) && JSON.stringify(d) === JSON.stringify(DEC); })());
check('D6 commission eligibility has only the existing rule (logged introduction)', JSON.stringify(Object.keys(B.DECISIONS.basket_introduction)) === '["logged_enquiry_only"]');

/* ---------------------------------------------------------------- T · basket terms: the approval gate */
console.log('— T basket terms: approval gate (no live terms exist; issued single-artist terms excluded)');
const b0 = await SMALL();
check('T1 [H3] no terms → refused', ok(refuses(() => B.plan(b0, DEC), /Basket terms are required/)));
check('T2 [H3] the issued single-artist terms are refused for a basket (PA-PAY 1.3 excludes multi-artwork orders)', ok(refuses(() => B.plan(b0, DEC, { livemode: true, artist_terms_doc: 'PA-PAY-2026-11', buyer_terms_doc: 'PA-BPT-2026-11' }), /exclude multi-artwork/)));
check('T3 [H3] live mode: no approved live basket terms exist, so every live basket is refused', Object.keys(B.LIVE_BASKET_TERMS).length === 0 && Object.isFrozen(B.LIVE_BASKET_TERMS)
  && ok(refuses(() => B.plan(b0, DEC, { livemode: true, artist_terms_doc: 'PA-BASKET-2027-01', buyer_terms_doc: 'PA-BASKET-BPT-2027-01' }), /No approved live basket terms/)));
check('T4 [H3] TEST placeholder terms are never accepted in live mode', ok(refuses(() => B.plan(b0, DEC, { ...TERMS2, livemode: true }), /No approved live basket terms|never valid in live/)));
check('T5 a buyer text that does not belong with the artist text is refused', ok(refuses(() => B.plan(b0, DEC, { ...TERMS2, buyer_terms_doc: 'PA-BASKET-BPT-TEST-01' }), /do not belong/)));
check('T6 the mode must be stated', ok(refuses(() => B.plan(b0, DEC, { artist_terms_doc: 'PA-BASKET-TEST-02', buyer_terms_doc: 'PA-BASKET-BPT-TEST-02' }), /state the Stripe mode/)));
check('T7 [H3] a Founding (0%) line under terms that do not permit commission-free sales → refused', ok(refuses(() => B.plan(b0, DEC, TERMS1), /Commission-free sales stay on direct payment/)));
check('T8 [H3] the same basket under terms that expressly permit commission-free lines → planned (support preserved behind the gate)', B.plan(b0, DEC, TERMS2).commission_cents === 15000);
const g0 = { lines: await sealed([L('g1', 'rowan', 'w1', 's1', 100000)]), shipments: [ship('s1', 'rowan', 0, 0, COVER(100000))] };
check('T9 terms that permit only some decisions refuse the others', ok(refuses(() => B.plan(g0, dec({ transfer_timing: 'after_delivery' }), TERMS3), /do not permit transfer_timing = after_delivery/)));
check('T9b …and accept the decisions they permit', B.plan(g0, DEC, TERMS3).total_cents === 100000);
check('T9c unknown TEST terms are refused', ok(refuses(() => B.plan(g0, DEC, { livemode: false, artist_terms_doc: 'PA-BASKET-TEST-99', buyer_terms_doc: 'PA-BASKET-BPT-TEST-99' }), /Unknown TEST basket terms/)));
check('T10 the plan records the terms it was made under', B.plan(b0, DEC, TERMS2).terms.artist_terms_doc === 'PA-BASKET-TEST-02');
{
  const mdb = await freshDb(true);
  const rows = (await mdb.prepare('SELECT doc_id, buyer_terms_doc, livemode, commission_free_lines, permits FROM basket_terms ORDER BY doc_id').all()).results;
  const fromEngine = Object.entries(B.TEST_BASKET_TERMS).map(([doc, v]) => ({ doc_id: doc, buyer_terms_doc: v.buyer_terms_doc, livemode: 0, commission_free_lines: v.commission_free_lines ? 1 : 0,
    permits: JSON.stringify(Object.fromEntries(Object.keys(B.DECISIONS).map(k => [k, [...v.permits[k]]]))) }));
  const fromDb = rows.map(r => ({ ...r, permits: JSON.stringify(Object.fromEntries(Object.keys(B.DECISIONS).map(k => [k, JSON.parse(r.permits)[k]]))) }));
  check('T11 [N6] the engine\'s TEST terms are exactly the rows migration 0019 seeds into basket_terms (one gate, two layers); no live rows', JSON.stringify(fromDb) === JSON.stringify(fromEngine), JSON.stringify(fromDb));
}

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
check('N10 [M3] each line keeps the existing rule\'s evidence, bound to its artist, artwork and introduction', (() => { const l = p1.lines.find(x => x.line_id === 'l1');
  return l.entitlement_evidence.rule && /PA-GAA/.test(l.entitlement_evidence.rule) && l.entitlement_evidence.binding.artist_id === 'rowan' && l.entitlement_evidence.binding.artwork_id === 'rowan_w1' && l.enquiry_ref === 'PA-E-rowan_w1-G'; })());
{
  const p = B.plan({ lines: await sealed([L('a', 'xg', 'w1', 's', 333), L('b', 'xg', 'w2', 's', 333)]), shipments: [ship('s', 'xg', 0, 0, COVER(666))] }, DEC, TERMS1);
  check('N11 rounding: two €3.33 works at 15% → 49 + 49 cents (not 99 on the €6.66 total)', p.commission_cents === 98 && p.artists[0].transfer_before_fees_cents === 666 - 98);
}
{
  const p = B.plan({ lines: await sealed([L('a', 'xg', 'w3', 'sx', 100000), L('b', 'yv', 'w1', 'sy', 100000, { profile: 'var10' }), L('c', 'zf', 'w1', 'sz', 100000, { profile: 'fa' })]),
    shipments: [ship('sx', 'xg', 1000, 0), ship('sy', 'yv', 2000, 0), ship('sz', 'zf', 3000, 0)] }, DEC, TERMS2);
  check('N12 mixed rates from the records: 15%, a written 10% variation, and a Founding Artist without terms (0%, never inferred)',
    JSON.stringify(p.artists.map(a => [a.artist_id, a.commission_cents, a.transfer_before_fees_cents, p.lines.find(l => l.artist_id === a.artist_id).commission_basis]))
    === JSON.stringify([['xg', 15000, 86000, 'gallery_artist_agreement'], ['yv', 10000, 92000, 'gallery_artist_agreement'], ['zf', 0, 103000, 'founding_artist_no_commission_terms']]));
}
{
  const p = B.plan({ lines: await sealed([L('a', 'xg', 'w4', 's1', 40000), L('b', 'xg', 'w5', 's2', 30000)]), shipments: [ship('s1', 'xg', 4000, 500, COVER(40000)), collect('s2', 'xg')] }, DEC, TERMS1);
  check('N13 one artist, two shipments (one delivered, one collected)', p.artists.length === 1 && p.artists[0].shipment_ids.length === 2 && p.artists[0].gross_cents === 74500);
}
{
  const p = B.plan({ lines: await sealed([L('a', 'xg', 'w6', 's1', 40000, { founding: true }), L('b', 'yv', 'w2', 's2', 30000, { profile: 'var10', founding: true })]), shipments: [ship('s1', 'xg', 0, 0), ship('s2', 'yv', 0, 0)] }, DEC, TERMS2);
  check('N14 a basket of Founding Enquiries only (terms permitting): 0% even for artists whose own rate is 15% or 10%', p.commission_cents === 0 && p.artists.every(a => a.transfer_before_fees_cents === a.gross_cents));
}
console.log('— N validation: everything a basket must not contain');
const base = await BASKET();
const mut = f => { const b = { lines: base.lines.map(l => ({ ...l })), shipments: base.shipments.map(s => ({ ...s })) }; f(b); return () => B.plan(b, DEC, TERMS2); };
const V = [
  ['a missing entitlement blocks', mut(b => { delete b.lines[0].entitlement; }), /entitlement is required/],
  ['a price in fractions of a cent is refused', mut(b => { b.lines[0].artwork_cents = 1450.5; }), /whole euro cents/],
  ['a price given as a string is refused', mut(b => { b.lines[0].artwork_cents = '145000'; }), /whole euro cents/],
  ['a price below €1.00 is refused', mut(b => { b.lines[0].artwork_cents = 99; }), /between EUR 1.00/],
  ['a price above the per-artwork pilot limit is refused', mut(b => { b.lines[0].artwork_cents = R.MAX_ARTWORK_CENTS + 1; }), /between EUR 1.00/],
  ['a negative delivery charge is refused', mut(b => { b.shipments[0].delivery_cents = -1; }), /whole euro cents/],
  ['the same original twice is refused', mut(b => { b.lines[1].artwork_id = b.lines[0].artwork_id; }), /sold only once/],
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
];
for (const [n, f, re] of V) { const r = refuses(f, re); check('N15 ' + n, ok(r), r); }
{
  const unk = await sealed([L('u', 'unkn', 'w1', 'su', 10000, { profile: 'unk' })]);
  check('N15 an unresolved entitlement (no accepted terms on record) blocks with the existing rule\'s reason', ok(refuses(() => B.plan({ lines: unk, shipments: [ship('su', 'unkn', 0, 0)] }, DEC, TERMS2), /Commission entitlement unknown/)));
  check('N15 a rate above 15% cannot arise: the database refuses it in artist_terms, and amounts() refuses 1600 and 1500.5 bp',
    await db.prepare("INSERT INTO artist_terms (artist_id, track, commission_bp, variation_agreed_on, set_by, created_at, updated_at) VALUES ('unkn','gallery_artist',1600,'2026-11-01','f',?,?)").bind(t0, t0).run().then(() => false, () => true)
    && ok(refuses(() => R.amounts({ artwork_cents: 1000, delivery_cents: 0, commission_bp: 1600 }), /Commission rate/)) && ok(refuses(() => R.amounts({ artwork_cents: 1000, delivery_cents: 0, commission_bp: 1500.5 }), /Commission rate/)));
  check('N15 an entitlement object not produced from the records (whatever its contents) is refused', ok(refuses(mut(b => { b.lines[0].entitlement = { ok: true, bp: 1600, basis: 'x', binding: { artist_id: 'rowan', artwork_id: 'rowan_w1' } }; }), /not produced by lineEntitlements/)));
}
{
  const b = { lines: await sealed([L('a', 'xg', 'w7', 's', 999999), L('b', 'xg', 'w8', 's', 1000)]), shipments: [ship('s', 'xg', 0, 0, COVER(2_000_000))] };
  check('N16 a basket of EUR 10,000 or more is refused (existing pilot AML scope)', ok(refuses(() => B.plan(b, DEC, TERMS1), /EUR 10,000/)));
  const b2 = { lines: await sealed([L('a', 'xg', 'w9', 's', 900000), L('b', 'xg', 'w10', 's', 99999)]), shipments: [ship('s', 'xg', 1, 0, COVER(2_000_000))] };
  check('N17 the €10,000 ceiling is on the whole basket, delivery included (€9,999.99 + €0.01 is refused)', ok(refuses(() => B.plan(b2, DEC, TERMS1), /EUR 10,000/)));
  const many = { lines: await sealed(Array.from({ length: B.MAX_BASKET_LINES + 1 }, (_, i) => L('l' + i, 'xg', 'm' + i, 's', 100))), shipments: [ship('s', 'xg', 0, 0)] };
  check('N18 more than the technical maximum of lines is refused', ok(refuses(() => B.plan(many, DEC, TERMS1), /at most/)));
}
{
  const b = { lines: await sealed([L('a', 'xg', 'w11', 's', 40000)]), shipments: [{ shipment_id: 's', artist_id: 'xg', method: 'collection', delivery_cents: 0, insurance_cents: 500, cover: COVER(40000) }] };
  check('N19 [L1] a collection with an insurance charge AND recorded cover is accepted', B.plan(b, DEC, TERMS1).total_cents === 40500);
}

/* ---------------------------------------------------------------- M · entitlements bound to records; nothing injectable */
console.log('— M entitlements bound to artist, artwork and introduction; consent as recorded; no injection [M3][N5]');
{
  const gal = await sealed([L('g', 'galx', 'w1', 'sg', 500000)]);
  const fnd = await sealed([L('f', 'fndx', 'w1', 'sf', 50000, { founding: true })]);
  const hijack = { lines: [{ ...gal[0], entitlement: fnd[0].entitlement }], shipments: [ship('sg', 'galx', 0, 0)] };
  check('M1 [P1] a Founding 0% entitlement attached to a Gallery Artist\'s line is refused', ok(refuses(() => B.plan(hijack, DEC, TERMS2), /another artist or artwork/)));
  const same = await sealed([L('a', 'galx', 'w2', 's', 10000, { founding: true }), L('b', 'galx', 'w3', 's', 10000)]);
  const swapped = { lines: [{ ...same[1], entitlement: same[0].entitlement }], shipments: [ship('s', 'galx', 0, 0)] };
  check('M2 [P1] an entitlement for another artwork of the SAME artist is refused', ok(refuses(() => B.plan(swapped, DEC, TERMS2), /another artist or artwork/)));
  check('M3 a hand-made entitlement (even with a matching binding) is refused', ok(refuses(() => B.plan({ lines: [{ ...gal[0], entitlement: { ok: true, bp: 0, basis: 'founding_enquiry', binding: { artist_id: 'galx', artwork_id: 'galx_w1' } } }], shipments: [ship('sg', 'galx', 0, 0)] }, DEC, TERMS2), /not produced by lineEntitlements/)));
  check('M4 [P7] caller-supplied processing consent is refused outright', ok(refuses(() => B.plan({ lines: [{ ...gal[0], processing_consent: true }], shipments: [ship('sg', 'galx', 0, 0)] }, DEC, TERMS2), /recorded consent, never from the request/)));
  const pr = dec({ processing_fee_bearer: 'artists_pro_rata' });
  const noConsent = await SMALL(false);
  check('M5 artists bear fees + a commission-free line WITHOUT recorded consent → refused', ok(refuses(() => B.plan(noConsent, pr, TERMS2), /not recorded consent/)));
  const pc = B.plan(await SMALL(true), pr, TERMS2);
  check('M6 the same with the artist\'s RECORDED consent (payment_pilot_events) → planned, and the consent time is kept on the line', pc.lines.find(l => l.line_id === 'l2').processing_consent_at === t1);
  check('M7 PlotArt bears fees: no consent needed on commission-free lines', B.plan(noConsent, DEC, TERMS2).total_cents > 0);
}
{
  await ensureArtist('mx', 'gal'); await ensureArtist('my', 'gal');
  await ensureWork('mx_w1', 'mx'); await ensureWork('mx_w2', 'mx'); await ensureWork('my_w1', 'my');
  await ensureEnquiry('PA-E-M1', 'mx', 'mx_w1', false); await ensureEnquiry('PA-E-MNULL', 'mx', null, false); await ensureEnquiry('PA-E-MY', 'my', 'my_w1', false);
  const e = await B.lineEntitlements(ENV, [
    { line_id: 'a', artist_id: 'gone', artwork_id: 'mx_w1', enquiry_ref: 'PA-E-M1' },
    { line_id: 'b', artist_id: 'mx', artwork_id: 'my_w1', enquiry_ref: 'PA-E-M1' },
    { line_id: 'c', artist_id: 'mx', artwork_id: 'mx_w2', enquiry_ref: 'PA-E-M1' },
    { line_id: 'd', artist_id: 'mx', artwork_id: 'mx_w2', enquiry_ref: 'PA-E-MNULL' },
    { line_id: 'f', artist_id: 'mx', artwork_id: 'mx_w2', enquiry_ref: 'PA-E-MY' },
    { line_id: 'g', artist_id: 'mx', artwork_id: 'mx_w2', enquiry_ref: '' },
    { line_id: 'h', artist_id: 'mx', artwork_id: 'mx_w1', enquiry_ref: 'PA-E-M1' },
    { line_id: 'i', artist_id: 'mx', artwork_id: 'mx_w1', enquiry_ref: 'PA-E-M1' },
  ], DEC, { at: T });
  check('M8 an unknown artist is blocked', e.a.ok === false && /Unknown artist/.test(e.a.reason));
  check('M9 an artwork that is not the artist\'s is blocked', e.b.ok === false && /not this artist/.test(e.b.reason));
  check('M10 [M3] an introduction for ANOTHER artwork cannot set this artwork\'s commission', e.c.ok === false && /for another artwork/.test(e.c.reason));
  check('M11 [M3] an introduction not tied to any artwork cannot set commission (founder decision)', e.d.ok === false && /not tied to an artwork/.test(e.d.reason));
  check('M12 another artist\'s introduction is blocked', e.f.ok === false && /No PlotArt introduction is logged/.test(e.f.reason));
  check('M13 no introduction named is blocked (basket_introduction)', e.g.ok === false && /basket_introduction/.test(e.g.reason));
  check('M14 a matching introduction resolves through the existing rule, bound to artist, artwork and introduction', e.h.ok === true && e.h.bp === 1500 && e.h.binding.enquiry_log_id === 'e-PA-E-M1' && e.h.evidence.binding.artwork_id === 'mx_w1');
  check('M15 [M3] one introduction cannot serve two lines', e.i.ok === false && /already used/.test(e.i.reason));
  const req = [{ line_id: 'h', artist_id: 'mx', artwork_id: 'mx_w1', enquiry_ref: 'PA-E-M1' }];
  const fake = { artist: async () => ({ id: 'mx' }), artwork: async () => ({ id: 'mx_w1', artist_id: 'mx' }), enquiry: async () => ({ id: 'x', artist_id: 'mx', artwork_id: 'mx_w1' }), consent: async () => ({ given: true, at: T }) };
  check('M16 [N5] injected records are refused, in every environment (not only production)', ok(await refusesAsync(() => B.lineEntitlements({ DB: db }, req, DEC, { at: T, records: fake }), /takes no other inputs/))
    && ok(await refusesAsync(() => B.lineEntitlements({ DB: db, ENVIRONMENT: 'sandbox' }, req, DEC, { at: T, records: fake }), /takes no other inputs/)));
  check('M17 [N5] an injected entitlement resolver is refused, including in production', ok(await refusesAsync(() => B.lineEntitlements({ DB: db, ENVIRONMENT: 'production' }, req, DEC, { at: T, resolve: async () => ({ ok: true, bp: 1, basis: 'invented' }) }), /takes no other inputs/)));
  check('M18 [N5] without a database there is no entitlement at all', ok(await refusesAsync(() => B.lineEntitlements({}, req, DEC, { at: T }), /database is required/)));
  check('M19 no quote time → refused', ok(await refusesAsync(() => B.lineEntitlements(ENV, req, DEC, {}), /time of the basket quote/)));
  await db.prepare("INSERT INTO payment_pilot_events (id, artist_id, kind, account_email, display_name, statement, at) VALUES ('pe-w1','mx','processing_consent','mx@example.test','mx','s',?)").bind(t0).run();
  await db.prepare("INSERT INTO payment_pilot_events (id, artist_id, kind, account_email, display_name, statement, at) VALUES ('pe-w2','mx','processing_consent_withdrawn','mx@example.test','mx',NULL,?)").bind(t1).run();
  const w = await B.lineEntitlements(ENV, req, DEC, { at: T });
  check('M20 consent given and later WITHDRAWN is read as not given', w.h.processing_consent === false && w.h.processing_consent_at === null);
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
  const p = B.plan({ lines: await sealed([L('a', 'xg', 'w12', 's', 50000, { founding: true })]), shipments: [ship('s', 'xg', 0, 0)] }, DEC, TERMS2);
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
  // each artist has ONE rate on record; each line is a Founding Enquiry or not
  let bad = null;
  for (let t = 0; t < 120 && !bad; t++) {
    const nArt = 1 + rnd(4), specs = [], shipments = [];
    for (let a = 0; a < nArt; a++) {
      const aid = `p${t}a${a}`, profile = ['gal', 'var10', 'var125', 'fa'][rnd(4)], nShip = 1 + rnd(2);
      for (let s = 0; s < nShip; s++) shipments.push({ shipment_id: `s${a}_${s}`, artist_id: aid, method: 'delivery', delivery_cents: rnd(5000), insurance_cents: rnd(800), cover: COVER(999999) });
      for (let k = 0; k < 1 + rnd(2); k++) specs.push(L(`l${specs.length}`, aid, `w${specs.length}`, `s${a}_${rnd(nShip)}`, 100 + rnd(80000), { profile, founding: rnd(3) === 0, consent: true }));
    }
    const used = new Set(specs.map(l => l.shipment_id)); const sh = shipments.filter(s => used.has(s.shipment_id));
    const bearer = rnd(2) ? 'plotart' : 'artists_pro_rata';
    try {
      const p = B.plan({ lines: await sealed(specs), shipments: sh }, dec({ processing_fee_bearer: bearer }), TERMS2);
      const fee = rnd(Math.floor(p.total_cents / 20) + 1), vat = Math.floor(fee * 23 / 100);
      const s = B.settle(p, { fee_cents: fee, fee_vat_cents: vat });
      const rate = { gal: 1500, var10: 1000, var125: 1250, fa: 0 };
      const expectLine = p.lines.every((l, i) => { const sp = specs.find(x => x.line_id === l.line_id); const bp = sp.founding ? 0 : rate[sp.profile];
        return l.commission_bp === bp && l.commission_cents === Math.floor(l.artwork_cents * bp / 10000); });
      if (p.total_cents !== p.commission_cents + sum(p.artists.map(a => a.transfer_before_fees_cents)) || sum(p.lines.map(l => l.commission_cents)) !== p.commission_cents || !expectLine
        || p.total_cents !== s.transfers_cents + s.platform_net_cents + s.fee_total_cents || s.artists.some(a => a.transfer_cents < 0)) bad = { t, bearer };
    } catch (e) { if (!/EUR 10,000/.test(e.message)) bad = { t, error: e.message }; }
  }
  check('S11 120 random baskets from real records: the existing rule\'s rate per artist and per Founding Enquiry, floor commission, plan and settlement balance', !bad, JSON.stringify(bad));
}

/* ---------------------------------------------------------------- P · what to transfer now [M4, L4, N1] */
console.log('— P transfers: holds, one in flight, retries with new keys, restorations after a failed refund');
{
  const sp = B.plan(await SMALL(), DEC, TERMS2), ss = B.settle(sp, { fee_cents: 2500, fee_vat_cents: 575 });
  const ready = { artists: { rowan: { release_ready_at: T }, alder: { release_ready_at: T } } };
  const now = '2026-11-22T00:00:00.000Z', due = ss.artists.find(a => a.artist_id === 'rowan').transfer_cents;
  const tp = B.transferPlan(sp, ss, ready, { basket_id: 'b1', now });
  check('P1 released artists are transferred their settled amount, attempt 1, with the database key format',
    tp.every(a => a.action === 'transfer' && a.attempt === 1) && tp.find(a => a.artist_id === 'rowan').idempotency_key === 'plotart-basket-tr:b1:rowan:allocation:-:1' && tp.find(a => a.artist_id === 'rowan').amount_cents === due);
  check('P2 [M4] an open dispute holds EVERY artist\'s transfer', B.transferPlan(sp, ss, ready, { basket_id: 'b1', now, open_dispute: true }).every(a => a.action === 'hold'));
  check('P3 not yet released → hold', B.transferPlan(sp, ss, { artists: { rowan: {}, alder: { release_ready_at: '2026-12-01T00:00:00.000Z' } } }, { basket_id: 'b1', now }).every(a => a.action === 'hold'));
  const retry = B.transferPlan(sp, ss, { artists: { rowan: { release_ready_at: T, attempts: 1 }, alder: { release_ready_at: T } } }, { basket_id: 'b1', now });
  check('P4 [L4] after a FAILED transfer the next attempt uses a new idempotency key', retry.find(a => a.artist_id === 'rowan').attempt === 2 && /:2$/.test(retry.find(a => a.artist_id === 'rowan').idempotency_key));
  check('P5 [H2] an allocation transfer in flight is never sent again', B.transferPlan(sp, ss, { artists: { rowan: { release_ready_at: T, attempts: 1, allocation_in_flight_cents: due }, alder: {} } }, { basket_id: 'b1', now }).find(a => a.artist_id === 'rowan').action === 'wait');
  check('P6 fully transferred → done', B.transferPlan(sp, ss, { artists: { rowan: { release_ready_at: T, attempts: 1, allocation_made_cents: due }, alder: {} } }, { basket_id: 'b1', now }).find(a => a.artist_id === 'rowan').action === 'done');
  check('P7 reductions applied before payout lower the transfer', B.transferPlan(sp, ss, { artists: { rowan: { release_ready_at: T, pending_reduced_cents: 10000 }, alder: {} } }, { basket_id: 'b1', now }).find(a => a.artist_id === 'rowan').amount_cents === due - 10000);
  check('P8 [H2] more already sent than is due is a failed allocation', ok(refuses(() => B.transferPlan(sp, ss, { artists: { rowan: { allocation_made_cents: due + 1 } } }, { basket_id: 'b1', now }), /more than is due/)));
  // N1: a reduction of 25,500 for refund rf2; the allocation then paid due − 25,500; rf2 FAILS and the reduction is restored
  const restoredState = r => ({ artists: { rowan: { release_ready_at: T, attempts: 1, allocation_made_cents: due - 25500, pending_reduced_cents: 0, restorations: [{ cause_id: 'rf2', restored_cents: 25500, ...r }] }, alder: {} } });
  const rs = B.transferPlan(sp, ss, restoredState({}), { basket_id: 'b1', now }).find(a => a.artist_id === 'rowan');
  check('P9 [N1] after the allocation was paid, a restored reduction is paid by a RESTORATION tied to its refund (not a second allocation)',
    rs.action === 'restore' && rs.amount_cents === 25500 && rs.items.length === 1 && rs.items[0].kind === 'restoration' && rs.items[0].idempotency_key === 'plotart-basket-tr:b1:rowan:restoration:rf2:1', JSON.stringify(rs));
  check('P10 [N1] once the restoration is paid the artist is done; it is never paid twice', B.transferPlan(sp, ss, restoredState({ paid_cents: 25500, attempts: 1 }), { basket_id: 'b1', now }).find(a => a.artist_id === 'rowan').action === 'done');
  check('P11 [N1] a failed restoration is retried with a new key', B.transferPlan(sp, ss, restoredState({ paid_cents: 0, attempts: 1 }), { basket_id: 'b1', now }).find(a => a.artist_id === 'rowan').items[0].attempt === 2);
  check('P12 [N1] repaid more than restored is refused', ok(refuses(() => B.transferPlan(sp, ss, restoredState({ paid_cents: 25501 }), { basket_id: 'b1', now }), /more than was restored/)));
  check('P13 [N1] an unexplained remainder after payout is refused, not paid', ok(refuses(() => B.transferPlan(sp, ss, { artists: { rowan: { allocation_made_cents: due - 100 }, alder: {} } }, { basket_id: 'b1', now }), /not explained by restored reductions/)));
  check('P14 [N1] a restoration is held while a dispute is open', B.transferPlan(sp, ss, restoredState({}), { basket_id: 'b1', now, open_dispute: true }).find(a => a.artist_id === 'rowan').action === 'hold');
  check('P15 [N1] a reduction restored BEFORE payout simply raises the allocation (no separate payment)', B.transferPlan(sp, ss, { artists: { rowan: { release_ready_at: T, pending_reduced_cents: 0, restorations: [{ cause_id: 'rf2', restored_cents: 25500 }] }, alder: {} } }, { basket_id: 'b1', now }).find(a => a.artist_id === 'rowan').amount_cents === due);
}

/* ---------------------------------------------------------------- F · refunds */
console.log('— F refunds: commission returned per PA-GAA 9.2, recovery from artists, failures unwound with written reasons');
const sp = B.plan(await SMALL(), DEC, TERMS2), ss = B.settle(sp, { fee_cents: 2500, fee_vat_cents: 575 });
const settled = (over = {}) => ({ artists: Object.fromEntries(ss.artists.map(a => [a.artist_id, { transfer_due_cents: a.transfer_cents, transferred_cents: a.transfer_cents, reversed_cents: 0, pending_reduced_cents: 0, ...(over[a.artist_id] || {}) }])) });
const WHY = 'Stripe reported the refund failed: card closed';
{
  const r = B.refund(sp, settled(), { lines: [{ line_id: 'l1', artwork_cents: 50000 }] });
  check('F1 €500 refunded on a €1,000 work at 15%: €75 commission returned, artist debited €425 (PA-PAY example 2)', r.commission_returned_cents === 7500 && r.lines[0].artist_debit_cents === 42500 && r.buyer_refund_cents === 50000);
  check('F2 the artist debit is recovered by reversing the transfer already made', r.artists[0].reverse_cents === 42500 && r.artists[0].reduce_pending_cents === 0 && r.shortfall_cents === 0);
  check('F3 the refund balances: buyer refund = artist debits + commission returned', r.buyer_refund_cents === sum(r.artists.map(a => a.debit_cents)) + r.commission_returned_cents);
  const u = B.refundFailed(sp, r, { reason: WHY });
  check('F4 [L4] that refund FAILS (even after succeeding): the reversal is re-credited and PlotArt reclaims its €75; the reason is kept', u.artists[0].recredit_cents === 42500 && u.commission_reclaimed_cents === 7500 && u.reason === WHY);
  check('F4b [N1] unwinding a failed refund needs a written reason', ok(refuses(() => B.refundFailed(sp, r, {}), /written reason/)) && ok(refuses(() => B.refundFailed(sp, r, { reason: 'x' }), /written reason/)));
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
  const p = B.plan({ lines: await sealed([L('a', 'xg', 'w13', 's', 999)]), shipments: [ship('s', 'xg', 0, 0, COVER(999))] }, DEC, TERMS1), s = B.settle(p, { fee_cents: 0, fee_vat_cents: 0 });
  let st = { lines: { a: { artwork_refunded_cents: 0, commission_returned_cents: 0 } }, artists: { xg: { transfer_due_cents: s.artists[0].transfer_cents, transferred_cents: s.artists[0].transfer_cents, reversed_cents: 0 } } };
  const got = [];
  for (const amt of [333, 333, 333]) {
    const r = B.refund(p, st, { lines: [{ line_id: 'a', artwork_cents: amt }] });
    got.push(r.commission_returned_cents);
    st = { lines: { a: { artwork_refunded_cents: st.lines.a.artwork_refunded_cents + amt, commission_returned_cents: st.lines.a.commission_returned_cents + r.commission_returned_cents } },
      artists: { xg: { ...st.artists.xg, reversed_cents: st.artists.xg.reversed_cents + r.artists[0].reverse_cents } } };
  }
  const kept = k => Math.floor(149 * k / 999);
  check('F7 rounding: three €3.33 refunds of a €9.99 work at 15% return 149 − kept(666), …, the whole 149 in total',
    p.commission_cents === 149 && JSON.stringify(got) === JSON.stringify([149 - kept(666), kept(666) - kept(333), kept(333)]) && sum(got) === 149, JSON.stringify(got));
  check('F8 after the last refund the whole transfer has been reversed', st.artists.xg.reversed_cents === 999 - 149);
}
{
  const r = B.refund(sp, settled({ rowan: { transferred_cents: 0 } }), { lines: [{ line_id: 'l1', artwork_cents: 20000 }] });
  check('F9 transfer not yet made: the debit reduces the pending transfer, nothing is reversed', r.artists[0].reduce_pending_cents === 17000 && r.artists[0].reverse_cents === 0);
  const r2 = B.refund(sp, settled({ rowan: { transferred_cents: 0, pending_reduced_cents: 80000 } }), { lines: [{ line_id: 'l1', artwork_cents: 20000 }] });
  check('F10 pending first, then a SHORTFALL when neither pending nor transferred money covers it', r2.artists[0].reduce_pending_cents === ss.artists.find(a => a.artist_id === 'rowan').transfer_cents - 80000 && r2.shortfall_cents === 17000 - r2.artists[0].reduce_pending_cents);
  const u = B.refundFailed(sp, r2, { reason: WHY });
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
  const sf = B.reversalFailed({ transfer_id: 'tr1', cause_kind: 'refund', cause_id: 'rf1', attempt: 2, amount_cents: 42500 }, { retry: false, reason: 'artist Stripe balance cannot cover it' });
  check('F17 [L4] a failed reversal is retried with a new key (database format)…', rv.action === 'retry' && rv.idempotency_key === 'plotart-basket-trr:tr1:refund:rf1:2');
  check('F18 [L4][N3] …or becomes a shortfall that stays tied to its ORIGINAL refund (counted against that artist\'s liability), with a written reason',
    sf.action === 'shortfall' && sf.amount_cents === 42500 && sf.cause_kind === 'refund' && sf.cause_id === 'rf1' && /balance/.test(sf.reason));
  check('F18b the choice is never implicit, and a shortfall needs a reason', ok(refuses(() => B.reversalFailed({ transfer_id: 'tr1', cause_kind: 'refund', cause_id: 'rf1', attempt: 1, amount_cents: 1 }, {}), /retry the reversal or record a shortfall/))
    && ok(refuses(() => B.reversalFailed({ transfer_id: 'tr1', cause_kind: 'refund', cause_id: 'rf1', attempt: 1, amount_cents: 1 }, { retry: false }), /written reason/)));
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
      const u = B.refundFailed(sp, r, { reason: WHY });
      if (r.buyer_refund_cents !== sum(r.artists.map(a => a.debit_cents)) + r.commission_returned_cents || cb + r.commission_returned_cents !== 15000 - keptAfter
        || r.artists.some(a => a.debit_cents !== a.reduce_pending_cents + a.reverse_cents + a.shortfall_cents)
        || r.buyer_refund_cents !== sum(u.artists.map(a => a.restore_pending_cents + a.recredit_cents + a.shortfall_cleared_cents)) + u.commission_reclaimed_cents) bad = { before, now };
    } catch (e) { bad = { before, now, e: e.message }; }
  }
  check('F19 500 random partial refunds: balanced, commission kept = floor(C × kept / A), debits fully accounted, failure unwinds exactly', !bad, JSON.stringify(bad));
}

/* ---------------------------------------------------------------- X · disputes */
console.log('— X disputes: holds while open; explicit attribution when artists carry any part; per-artist liability rows');
{
  const o = B.dispute(sp, settled(), { outcome: 'open', amount_cents: sp.total_cents, fee_cents: 2000 });
  const w = B.dispute(sp, settled(), { outcome: 'won', amount_cents: sp.total_cents, fee_cents: 2000 });
  check('X1 [P4][M4] an open dispute holds every artist\'s transfers; nothing moves', JSON.stringify(o.hold_transfers) === '["alder","rowan"]' && o.artists.length === 0 && o.platform_cost_cents === 0);
  check('X2 a won dispute releases the hold; nothing moves', w.hold_transfers.length === 0 && w.artists.length === 0);
  const all = p => ({ lines: p.lines.map(l => ({ line_id: l.line_id, artwork_cents: l.artwork_cents })), shipments: p.shipments.filter(s => s.delivery_cents + s.insurance_cents > 0).map(s => ({ shipment_id: s.shipment_id, cents: s.delivery_cents + s.insurance_cents })) });
  const x = B.dispute(sp, settled(), { outcome: 'lost', amount_cents: sp.total_cents, fee_cents: 2000, attribution: all(sp) });
  check('X3 lost, PlotArt bears loss and fee: no artist is debited or liable; PlotArt\'s cost = amount + fee', x.artists.length === 0 && x.allocations.length === 0 && x.platform_cost_cents === sp.total_cents + 2000);
  check('X4 [L2] lost and PlotArt-borne BEFORE settlement: no longer throws', B.dispute(sp, {}, { outcome: 'lost', amount_cents: 1000, fee_cents: 2000, attribution: { lines: [{ line_id: 'l1', artwork_cents: 1000 }] } }).platform_cost_cents === 3000);
  check('X4b [H-2] EVERY lost dispute names what it was for, even one PlotArt carries (the database refuses one without)', ok(refuses(() => B.dispute(sp, settled(), { outcome: 'lost', amount_cents: 1000 }), /explicit attribution/)));
  const lostL1 = { ...settled(), lines: { l1: { artwork_disputed_cents: 100000 } } };
  check('X4c [H-3] a line already recovered through a lost dispute cannot be refunded again', ok(refuses(() => B.refund(sp, lostL1, { lines: [{ line_id: 'l1', artwork_cents: 1 }] }), /after refunds and lost disputes/)));
  check('X4d [H-3] …nor attributed to a second lost dispute', ok(refuses(() => B.dispute(sp, lostL1, { outcome: 'lost', amount_cents: 1, attribution: { lines: [{ line_id: 'l1', artwork_cents: 1 }] } }), /exceeds what remains/)));
  check('X4e [H-3] a partly disputed line can still be refunded for what remains, and no more', B.refund(sp, { ...settled(), lines: { l1: { artwork_disputed_cents: 60000 } } }, { lines: [{ line_id: 'l1', artwork_cents: 40000 }] }).lines[0].artwork_refund_cents === 40000
    && ok(refuses(() => B.refund(sp, { ...settled(), lines: { l1: { artwork_disputed_cents: 60000 } } }, { lines: [{ line_id: 'l1', artwork_cents: 40001 }] }), /exceeds/)));
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
  check('X8 [P3][N3] only the attributed artist carries anything; the database row of liability names only Rowan', !x.artists.some(a => a.artist_id === 'alder')
    && JSON.stringify(x.allocations) === JSON.stringify([{ artist_id: 'rowan', loss_cents: 85000, fee_cents: 2000 }]));
  check('X9 [P3][M4] lost and carried by artists WITHOUT an explicit attribution → refused', ok(refuses(() => B.dispute(p, st, { outcome: 'lost', amount_cents: p.total_cents, fee_cents: 2001 }), /explicit attribution/)));
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

/* ---------------------------------------------------------------- E · the existing rule, real records (founder cases) */
console.log('— E entitlements from the records: the Founding 25 and Gallery Artist cases end to end');
{
  await ensureArtist('fia', 'fa'); await ensureWork('fia_w', 'fia'); await ensureEnquiry('PA-E-FIA', 'fia', 'fia_w', true);
  await ensureArtist('fnt', 'fa'); await ensureWork('fnt_w', 'fnt'); await ensureEnquiry('PA-E-FNT', 'fnt', 'fnt_w', false);
  await ensureArtist('gal', 'gal'); await ensureWork('gal_w', 'gal'); await ensureEnquiry('PA-E-GAL', 'gal', 'gal_w', false);
  await ensureArtist('var', 'var10'); await ensureWork('var_w', 'var'); await ensureEnquiry('PA-E-VAR', 'var', 'var_w', false);
  const reqs = [['l1', 'fia', 'fia_w', 'PA-E-FIA'], ['l2', 'gal', 'gal_w', 'PA-E-GAL'], ['l3', 'var', 'var_w', 'PA-E-VAR'], ['l4', 'fnt', 'fnt_w', 'PA-E-FNT']]
    .map(([line_id, artist_id, artwork_id, enquiry_ref]) => ({ line_id, artist_id, artwork_id, enquiry_ref }));
  const e = await B.lineEntitlements(ENV, reqs, DEC, { at: T });
  check('E1 Founding 25 artist, Founding Enquiry for this artwork → 0%, basis founding_enquiry', e.l1.ok && e.l1.bp === 0 && e.l1.basis === 'founding_enquiry');
  check('E2 Gallery Artist with the agreement accepted before the introduction → 15%', e.l2.ok && e.l2.bp === 1500 && e.l2.basis === 'gallery_artist_agreement');
  check('E3 Gallery Artist with a written 10% variation → 10%', e.l3.ok && e.l3.bp === 1000);
  check('E4 Founding Artist, non-founding enquiry, no commission terms → 0% (never inferred)', e.l4.ok && e.l4.bp === 0 && e.l4.basis === 'founding_artist_no_commission_terms');
  const lines = ['l1', 'l2', 'l3', 'l4'].map((lid, i) => ({ line_id: lid, artist_id: reqs[i].artist_id, artwork_id: reqs[i].artwork_id, shipment_id: 's' + i, artwork_cents: 100000, entitlement: e[lid] }));
  const shipments = lines.map((l, i) => ship('s' + i, l.artist_id, 1000, 0, COVER(100000)));
  check('E5 the resolved entitlements drive the plan: 0 + 15,000 + 10,000 + 0 commission', B.plan({ lines, shipments }, DEC, TERMS2).commission_cents === 25000);
  check('E6 [H3] the same real Founding lines are refused under terms that do not permit commission-free sales (support kept, disabled)', ok(refuses(() => B.plan({ lines, shipments }, DEC, TERMS1), /Commission-free sales stay on direct payment/)));
}

for (const mf of mfs) await mf.dispose();
const failed = results.filter(x => !x).length;
console.log(`BASKET RULES · ${results.length} checks, ${results.length - failed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
