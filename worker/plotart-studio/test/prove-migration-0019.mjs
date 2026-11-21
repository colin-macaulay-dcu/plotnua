// PROVE · migration 0019 (multi-artist basket records, revised after review) on a database built from schema.sql, which
// already holds the single-artist pilot tables (0017), with realistic records. Local only: throwaway Miniflare D1s.
// Nothing is applied to any real database.
//   node test/prove-migration-0019.mjs
// Sections: M additivity · R the engine's plan recorded end to end · C every database defect the independent review
// reproduced (now refused) · X cross-checkout, using the single-artist checkout's OWN statements from checkout.js ·
// K concurrency · F financial integrity · L linked purchases (checkout.js linkedCheck with and without 0019) · B rollback.
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { statements, rollbackOf } from './sql.mjs';
import { seedPublished } from './seed.mjs';
import * as B from '../src/basket-rules.js';

const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
process.on('uncaughtException', e => { console.log(`  FAIL  uncaught: ${e.message}`); console.log('MIGRATION 0019 · FAILED'); process.exit(1); });
process.on('unhandledRejection', e => { console.log(`  FAIL  unhandled: ${e && e.message}`); console.log('MIGRATION 0019 · FAILED'); process.exit(1); });
const HERE = new URL('..', import.meta.url).pathname;
const MIG = readFileSync(HERE + 'migrations/0019_basket_checkout.sql', 'utf8');
const SCHEMA = readFileSync(HERE + 'schema.sql', 'utf8');
const CHECKOUT_SRC = readFileSync(HERE + 'src/checkout.js', 'utf8');
const mfs = [];
async function freshDb(name, withMig = true) {
  const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: name + '-' + Date.now() + Math.random() } });
  mfs.push(mf);
  const db = await mf.getD1Database('DB');
  for (const s of statements(SCHEMA)) await db.prepare(s).run();
  if (withMig) for (const s of statements(MIG)) await db.prepare(s).run();
  return db;
}
const mk = db => {
  const q = (sql, ...a) => db.prepare(sql).bind(...a);
  return {
    q, run: (sql, ...a) => q(sql, ...a).run(),
    refused: async (sql, args = [], re = null) => { try { await q(sql, ...args).run(); return false; } catch (e) { return re ? re.test(e.message) || e.message : true; } },
    accepted: async (sql, ...a) => { try { await q(sql, ...a).run(); return true; } catch (e) { return e.message; } },
  };
};
const t = '2026-11-21T10:00:00.000Z', future = '2099-01-01T00:00:00.000Z', past = '2026-01-01T00:00:00.000Z', H = 'a'.repeat(64);
const DECS = JSON.stringify({ processing_fee_bearer: 'plotart', transfer_timing: 'on_payment', dispute_loss_bearer: 'plotart', dispute_fee_bearer: 'plotart', basket_introduction: 'logged_enquiry_only' });
const ev = (aid, wid, ref) => JSON.stringify({ rule: 'x', binding: { artist_id: aid, artwork_id: wid, enquiry_ref: ref, enquiry_log_id: 'e' } });

/* A basket built straight in SQL (draft → lines/shipments/allocations → checkout_open), for the constraint sections. */
async function basketSql(D, id, lines, { status = 'checkout_open', livemode = 0, buyer = 'buyer@example.test' } = {}) {
  // lines: [{ line, artist, work, cents, bp }]; one collection shipment per artist, no charges
  const total = lines.reduce((a, l) => a + l.cents, 0), comm = lines.reduce((a, l) => a + Math.floor(l.cents * (l.bp ?? 1500) / 10000), 0);
  const docs = livemode ? ['PA-BASKET-2099-01', 'PA-BASKET-BPT-2099-01'] : ['PA-BASKET-TEST-02', 'PA-BASKET-BPT-TEST-02'];
  await D.run(`INSERT INTO basket_orders (id, reference, status, buyer_email, livemode, total_cents, commission_cents, plan_version, plan_sha256, decisions, artist_terms_doc, buyer_terms_doc, transfer_group, created_by, created_at, updated_at)
    VALUES (?,?,'draft',?,?,?,?,'v',?,?,?,?,?,'system',?,?)`, id, 'PA-B-' + id, buyer, livemode, total, comm, H, DECS, docs[0], docs[1], 'plotart-basket-' + id, t, t);
  for (const a of [...new Set(lines.map(l => l.artist))]) {
    await D.run(`INSERT INTO basket_shipments (basket_id, shipment_id, artist_id, method, delivery_cents, insurance_cents) VALUES (?,?,?,'collection',0,0)`, id, 's-' + a, a);
    const ls = lines.filter(l => l.artist === a), g = ls.reduce((x, l) => x + l.cents, 0), c = ls.reduce((x, l) => x + Math.floor(l.cents * (l.bp ?? 1500) / 10000), 0);
    await D.run(`INSERT INTO basket_artist_allocations (basket_id, artist_id, account_id, gross_cents, commission_cents, delivery_cents, insurance_cents, transfer_before_fees_cents, release, release_ready_at, updated_at)
      VALUES (?,?,?,?,?,0,0,?,'on_payment',?,?)`, id, a, 'acct_' + a, g, c, g - c, past, t);
  }
  for (const l of lines) await D.run(`INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis, entitlement_evidence, enquiry_ref)
    VALUES (?,?,?,?,?,?,?,?,'gallery_artist_agreement',?,?)`, id, l.line, l.artist, l.work, 's-' + l.artist, l.cents, l.bp ?? 1500, Math.floor(l.cents * (l.bp ?? 1500) / 10000), ev(l.artist, l.work, 'PA-E-' + l.line), 'PA-E-' + l.line);
  if (status !== 'draft') await D.run(`UPDATE basket_orders SET status = ? WHERE id = ?`, status, id);
}
/* paid and settled (PlotArt bears the fee), allocations settled */
async function paySettle(D, id, { charge = 'ch_' + id, fee = 100 } = {}) {
  await D.run(`UPDATE basket_orders SET status = 'paid', payment_status = 'paid', checkout_session_id = ?, payment_intent_id = ?, charge_id = ?, paid_at = ?, updated_at = ? WHERE id = ?`, 'cs_test_' + id, 'pi_' + id, charge, t, t, id);
  await D.run(`UPDATE basket_orders SET fee_cents = ?, fee_vat_cents = 0, settled_at = ? WHERE id = ?`, fee, t, id);
  await D.run(`UPDATE basket_artist_allocations SET processing_share_cents = 0, transfer_due_cents = transfer_before_fees_cents WHERE basket_id = ?`, id);
}
const trIns = (D, { id, basket, artist, attempt = 1, amount, kind = 'allocation', cause = '-', dest = 'acct_' + artist, charge = 'ch_' + basket, live = 0 }) =>
  D.accepted(`INSERT INTO basket_transfers (id, basket_id, artist_id, kind, cause_key, attempt, destination, idempotency_key, source_charge_id, amount_cents, livemode, status, created_at, updated_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,'requested',?,?)`, id, basket, artist, kind, cause, attempt, dest, B.keys.transfer({ basket_id: basket, artist_id: artist, kind, cause_key: cause, attempt }), charge, amount, live, t, t);
const trMade = (D, id) => D.run(`UPDATE basket_transfers SET status = 'created', stripe_transfer_id = ? WHERE id = ?`, 'tr_' + id, id);
const rfIns = (D, { id, basket, amount, comm = 0, live = 0 }) => D.accepted(`INSERT INTO basket_refunds (id, basket_id, idempotency_key, amount_cents, commission_returned_cents, status, reason, requested_by, livemode, created_at, updated_at)
  VALUES (?,?,?,?,?,'requested','r','founder',?,?,?)`, id, basket, B.keys.refund({ basket_id: basket, refund_id: id }), amount, comm, live, t, t);
const partIns = (D, { refund, kind = 'line', ref, artist, amount, comm = 0 }) => D.accepted(`INSERT INTO basket_refund_parts (refund_id, kind, ref, artist_id, amount_cents, commission_returned_cents, artist_debit_cents) VALUES (?,?,?,?,?,?,?)`,
  refund, kind, ref, artist, amount, comm, amount - comm);
const rvIns = (D, { id, transfer, cause_kind = 'refund', cause, attempt = 1, amount }) => D.accepted(`INSERT INTO basket_transfer_reversals (id, transfer_id, cause_kind, cause_id, attempt, idempotency_key, amount_cents, status, created_at, updated_at)
  VALUES (?,?,?,?,?,?,?,'requested',?,?)`, id, transfer, cause_kind, cause, attempt, B.keys.reversal({ transfer_id: transfer, cause_kind, cause_id: cause, attempt }), amount, t, t);

/* ---------------------------------------------------------------- M · additivity */
console.log('PROVE · migration 0019 (multi-artist basket records, revised) on the current schema with existing records');
const db = await freshDb('mig19', false), D = mk(db);
await seedPublished(db, { id: 'arowan', slug: 'rowan-test', email: 'rowan@example.test', name: 'Rowan Test', works: 3, number: 1 });
await seedPublished(db, { id: 'aalder', slug: 'alder-test', email: 'alder@example.test', name: 'Alder Test', works: 3, number: 2 });
const order = (id, work, status = 'paid', qexp = null, email = 'other@example.test') => D.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, quote_expires_at, buyer_email, created_by, created_at, updated_at)
  VALUES (?,?,?,?,?,?,?,?,?,?,?)`, id, 'PA-O-' + id, 'arowan', work, 'PA-E-1', status, qexp, email, 'founder', t, t);
await order('osold', 'warowan3'); await order('oheld', 'warowan2', 'checkout_open', future); await order('oold', 'waalder3', 'expired', past);
await D.run('INSERT INTO artwork_sales (order_id, artwork_id, sold_at) VALUES (?,?,?)', 'osold', 'warowan3', t);
await D.run('INSERT INTO artwork_reservations (artwork_id, order_id, quote_version, expires_at, created_at) VALUES (?,?,?,?,?)', 'warowan2', 'oheld', 1, future, t);
await D.run('INSERT INTO artwork_reservations (artwork_id, order_id, quote_version, expires_at, created_at) VALUES (?,?,?,?,?)', 'waalder3', 'oold', 1, past, t);
const objects = async () => (await db.prepare("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
const dump = async names => { const o = {}; for (const tb of names) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
const beforeObjects = await objects(), beforeTables = beforeObjects.filter(o => o.type === 'table').map(o => o.name), before = await dump(beforeTables);
check('M0 the base has the single-artist pilot tables and no basket tables', beforeTables.includes('checkout_orders') && !beforeTables.some(n => n.startsWith('basket_')));
for (const s of statements(MIG)) await db.prepare(s).run();
const after = await objects();
const NEW = ['basket_orders', 'basket_shipments', 'basket_lines', 'basket_artist_allocations', 'basket_disputes', 'basket_refunds', 'basket_refund_parts', 'basket_transfers',
  'basket_transfer_reversals', 'basket_allocation_adjustments', 'basket_artwork_reservations', 'basket_artwork_sales', 'basket_payment_events', 'basket_events'];
const EXISTING_GUARDS = { single_hold_not_basket_insert: 'artwork_reservations', single_hold_not_basket_update: 'artwork_reservations', single_sale_not_basket_insert: 'artwork_sales',
  single_sale_reinstate_not_basket: 'artwork_sales', single_quote_not_basket: 'checkout_orders' };
const created = after.filter(o => o.type === 'table').map(o => o.name).filter(n => !beforeTables.includes(n) && n !== 'sqlite_sequence').sort();
check('M1 the migration creates exactly the fourteen basket tables', JSON.stringify(created) === JSON.stringify([...NEW].sort()), created.join(','));
check('M2 every existing table, index and trigger definition is unchanged', beforeObjects.every(o => after.some(a => a.type === o.type && a.name === o.name && a.sql === o.sql)));
check('M3 every existing row is unchanged', JSON.stringify(await dump(beforeTables)) === JSON.stringify(before));
const newObjs = after.filter(o => !beforeObjects.some(b => b.type === o.type && b.name === o.name));
const onExisting = newObjs.filter(o => o.type !== 'table' && !NEW.includes(o.tbl_name));
check('M4 new indexes and triggers are on new tables, except EXACTLY the five declared cross-checkout guards',
  JSON.stringify(onExisting.map(o => [o.name, o.tbl_name]).sort()) === JSON.stringify(Object.entries(EXISTING_GUARDS).sort()) && onExisting.every(o => o.type === 'trigger'), onExisting.map(o => o.name).join(','));
const isRefusalOnly = o => /BEFORE (INSERT|UPDATE|DELETE)/.test(o.sql) && /SELECT RAISE\(ABORT/.test(o.sql) && !/\b(INSERT INTO|UPDATE \w+ SET|DELETE FROM)\b/.test(o.sql.replace(/BEFORE (INSERT|UPDATE|DELETE)( OF \w+)? ON/, ''));
check('M5 every new trigger is a refusal-only BEFORE trigger (reads tables, writes none)', newObjs.filter(o => o.type === 'trigger').every(isRefusalOnly));
check('M6 the guards on existing tables refuse with a "UNIQUE constraint failed" message (handled cleanly by checkout.js)', onExisting.every(o => /RAISE\(ABORT, 'UNIQUE constraint failed:/.test(o.sql)));
check('M7 no foreign key from the new tables to artists, artworks or the single-artist pilot tables', !newObjs.some(o => o.sql && /REFERENCES (artists|artworks|checkout_orders|artwork_sales|artwork_reservations)\b/.test(o.sql)));
let again = true; try { for (const s of statements(MIG)) await db.prepare(s).run(); } catch { again = false; }
check('M8 running it twice is harmless', again && JSON.stringify(await objects()) === JSON.stringify(after));

/* ---------------------------------------------------------------- R · the engine's plan, recorded end to end */
console.log('— R the tables record exactly what basket-rules.js produces');
const DEC = JSON.parse(DECS);
const COVER = v => ({ cover_type: 'transit_insurance', covered_value_cents: v, insured_party: 'transporter' });
const recs = {
  artist: async aid => ({ id: aid }), artwork: async wid => ({ id: wid, artist_id: wid.startsWith('warowan') ? 'arowan' : 'aalder' }),
  enquiry: async ref => ({ PA_E_r: { id: 'er', artist_id: 'arowan', artwork_id: 'warowan1' }, PA_E_a: { id: 'ea', artist_id: 'aalder', artwork_id: 'waalder1' } })[ref.replace(/-/g, '_')] || null,
  consent: async () => ({ given: false, at: null }) };
const ents = await B.lineEntitlements({ ENVIRONMENT: 'test' }, [{ line_id: 'l1', artist_id: 'arowan', artwork_id: 'warowan1', enquiry_ref: 'PA-E-r' }, { line_id: 'l2', artist_id: 'aalder', artwork_id: 'waalder1', enquiry_ref: 'PA-E-a' }], DEC,
  { at: t, records: recs, resolve: async (env, { enquiryRef }) => (enquiryRef === 'PA-E-r' ? { ok: true, bp: 1500, basis: 'gallery_artist_agreement', evidence: { doc_id: 'PA-GAA-2026-11' } } : { ok: true, bp: 0, basis: 'founding_enquiry', evidence: {} }) });
const plan = B.plan({ lines: [{ line_id: 'l1', artist_id: 'arowan', artwork_id: 'warowan1', shipment_id: 's1', artwork_cents: 145000, entitlement: ents.l1 },
  { line_id: 'l2', artist_id: 'aalder', artwork_id: 'waalder1', shipment_id: 's2', artwork_cents: 210000, entitlement: ents.l2 }],
  shipments: [{ shipment_id: 's1', artist_id: 'arowan', method: 'delivery', delivery_cents: 3500, insurance_cents: 1200, cover: COVER(145000) }, { shipment_id: 's2', artist_id: 'aalder', method: 'collection', delivery_cents: 0, insurance_cents: 0 }] },
  DEC, { livemode: false, artist_terms_doc: 'PA-BASKET-TEST-02', buyer_terms_doc: 'PA-BASKET-BPT-TEST-02' });
await D.run(`INSERT INTO basket_orders (id, reference, status, buyer_email, livemode, total_cents, commission_cents, plan_version, plan_sha256, decisions, artist_terms_doc, buyer_terms_doc, transfer_group, created_by, created_at, updated_at)
  VALUES ('b1','PA-B-0001','draft','buyer@example.test',0,?,?,?,?,?,?,?,'plotart-basket-b1','system',?,?)`, plan.total_cents, plan.commission_cents, plan.version, createHash('sha256').update(JSON.stringify(plan)).digest('hex'),
  JSON.stringify(plan.decisions), plan.terms.artist_terms_doc, plan.terms.buyer_terms_doc, t, t);
for (const s of plan.shipments) await D.run(`INSERT INTO basket_shipments (basket_id, shipment_id, artist_id, method, delivery_cents, insurance_cents, cover) VALUES ('b1',?,?,?,?,?,?)`,
  s.shipment_id, s.artist_id, s.method, s.delivery_cents, s.insurance_cents, s.cover ? JSON.stringify(s.cover) : null);
for (const l of plan.lines) await D.run(`INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis, entitlement_evidence, enquiry_ref, processing_consent, processing_consent_at)
  VALUES ('b1',?,?,?,?,?,?,?,?,?,?,?,?)`, l.line_id, l.artist_id, l.artwork_id, l.shipment_id, l.artwork_cents, l.commission_bp, l.commission_cents, l.commission_basis, JSON.stringify(l.entitlement_evidence), l.enquiry_ref, l.processing_consent ? 1 : 0, l.processing_consent_at);
check('R0 checkout cannot open before allocations are recorded (the basket does not reconcile)', await D.refused(`UPDATE basket_orders SET status = 'checkout_open' WHERE id = 'b1'`, [], /does not reconcile/));
for (const a of plan.artists) await D.run(`INSERT INTO basket_artist_allocations (basket_id, artist_id, account_id, gross_cents, commission_cents, delivery_cents, insurance_cents, transfer_before_fees_cents, release, updated_at)
  VALUES ('b1',?,?,?,?,?,?,?,?,?)`, a.artist_id, 'acct_' + a.artist_id, a.gross_cents, a.commission_cents, a.delivery_cents, a.insurance_cents, a.transfer_before_fees_cents, a.release, t);
check('R1 a reconciled plan (two artists, 15% and Founding 0% under terms permitting it) can leave draft', await D.accepted(`UPDATE basket_orders SET status = 'checkout_open' WHERE id = 'b1'`));
await D.run(`INSERT INTO basket_artwork_reservations (artwork_id, basket_id, expires_at, created_at) VALUES ('warowan1','b1',?,?)`, future, t);
await D.run(`INSERT INTO basket_artwork_reservations (artwork_id, basket_id, expires_at, created_at) VALUES ('waalder1','b1',?,?)`, future, t);
await D.run(`UPDATE basket_orders SET status = 'paid', payment_status = 'paid', checkout_session_id = 'cs_test_b1', payment_intent_id = 'pi_b1', charge_id = 'ch_b1', paid_at = ? WHERE id = 'b1'`, t);
for (const w of ['warowan1', 'waalder1']) await D.run(`INSERT INTO basket_artwork_sales (basket_id, artwork_id, sold_at) VALUES ('b1',?,?)`, w, t);
check('R2 the paid basket holds both originals as active basket sales', (await D.q(`SELECT COUNT(*) n FROM basket_artwork_sales WHERE basket_id='b1' AND released_at IS NULL`).first()).n === 2);
const st = B.settle(plan, { fee_cents: 5600, fee_vat_cents: 1288 });
await D.run(`UPDATE basket_orders SET fee_cents = 5600, fee_vat_cents = 1288, settled_at = ? WHERE id = 'b1'`, t);
for (const a of st.artists) await D.run(`UPDATE basket_artist_allocations SET processing_share_cents = ?, transfer_due_cents = ?, release_ready_at = ?, status = 'ready' WHERE basket_id = 'b1' AND artist_id = ?`, a.processing_share_cents, a.transfer_cents, past, a.artist_id);
check('R3 settlement is recorded once: each due transfer = before-fees − processing share', (await D.q(`SELECT COUNT(*) n FROM basket_artist_allocations WHERE basket_id='b1' AND transfer_due_cents = transfer_before_fees_cents - processing_share_cents`).first()).n === 2);
const tp = B.transferPlan(plan, st, { artists: { arowan: { release_ready_at: past }, aalder: { release_ready_at: past } } }, { basket_id: 'b1', now: t });
for (const a of tp) { check(`R4 transfer to ${a.artist_id}, with the engine's key, is accepted`, (await trIns(D, { id: 'tr-' + a.artist_id, basket: 'b1', artist: a.artist_id, amount: a.amount_cents })) === true); await trMade(D, 'tr-' + a.artist_id); }
const rw = st.artists.find(a => a.artist_id === 'arowan');
const rf = B.refund(plan, { artists: { arowan: { transfer_due_cents: rw.transfer_cents, transferred_cents: rw.transfer_cents } } }, { lines: [{ line_id: 'l1', artwork_cents: 50000 }] });
check('R5 a partial refund is requested with its per-line part (commission returned per PA-GAA 9.2)', (await rfIns(D, { id: 'rf1', basket: 'b1', amount: rf.buyer_refund_cents, comm: rf.commission_returned_cents })) === true
  && (await partIns(D, { refund: 'rf1', ref: 'l1', artist: 'arowan', amount: rf.lines[0].artwork_refund_cents, comm: rf.lines[0].commission_returned_cents })) === true);
check('R6 the refund can be sent once its parts add up, and succeed', await D.accepted(`UPDATE basket_refunds SET status = 'pending', stripe_refund_id = 're_1' WHERE id = 'rf1'`) === true && await D.accepted(`UPDATE basket_refunds SET status = 'succeeded' WHERE id = 'rf1'`) === true);
check('R7 the matching transfer reversal is accepted', (await rvIns(D, { id: 'rv1', transfer: 'tr-arowan', cause: 'rf1', amount: rf.artists[0].reverse_cents })) === true && await D.accepted(`UPDATE basket_transfer_reversals SET status = 'created', stripe_reversal_id = 'trr_1' WHERE id = 'rv1'`) === true);
check('R8 [L4] the refund later FAILS: the status may move succeeded → failed', await D.accepted(`UPDATE basket_refunds SET status = 'failed', failure = 'card closed' WHERE id = 'rf1'`) === true);
const un = B.refundFailed(plan, rf);
check('R9 [L4] …and the artist is re-credited exactly what was reversed for it (recredit transfer tied to the refund)', (await trIns(D, { id: 'rc1', basket: 'b1', artist: 'arowan', kind: 'recredit', cause: 'rf1', amount: un.artists[0].recredit_cents })) === true);
check('R10 [L4] a second recredit for the same failed refund is refused', (await trIns(D, { id: 'rc2', basket: 'b1', artist: 'arowan', kind: 'recredit', cause: 'rf1', attempt: 2, amount: 1 })) !== true);
await D.run(`INSERT INTO basket_disputes (id, basket_id, stripe_dispute_id, amount_cents, fee_cents, status, livemode, opened_at) VALUES ('d1','b1','du_1',10000,2000,'open',0,?)`, t);
check('R11 an open dispute is recorded and may close as lost once', await D.accepted(`UPDATE basket_disputes SET status = 'lost', closed_at = ?, attribution = '{}' WHERE id = 'd1'`, t) === true
  && await D.refused(`UPDATE basket_disputes SET status = 'won' WHERE id = 'd1'`, [], /only moves from open/) === true);

/* ---------------------------------------------------------------- C · every reproduced defect, now refused */
console.log('— C the independent review\'s reproductions (each was ACCEPTED before; each is refused now)');
{
  const D2 = mk(await freshDb('c'));
  const ord = (id, work, status, qexp) => D2.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, quote_expires_at, created_by, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)`,
    id, 'PA-O-' + id, 'a1', work, 'PA-E-1', status, qexp, 'founder', t, t);
  await basketSql(D2, 'b1', [{ line: 'q', artist: 'a1', work: 'wq', cents: 10000 }, { line: 'r', artist: 'a1', work: 'wr', cents: 10000 }, { line: 'x', artist: 'a1', work: 'wx', cents: 10000 }, { line: 'u', artist: 'a1', work: 'wu', cents: 10000 }]);
  await basketSql(D2, 'b2', [{ line: 'q2', artist: 'a1', work: 'wq2', cents: 10000 }, { line: 'r2', artist: 'a1', work: 'wr', cents: 10000 }]);
  await ord('oq', 'wq', 'quoted', future);
  check('C1 [M1] a basket hold on a work with an OPEN single-artist quote', await D2.refused(`INSERT INTO basket_artwork_reservations VALUES ('wq','b1',?,?)`, [future, t], /single-artist/) === true);
  await ord('or', 'wr', 'checkout_open', future);
  await D2.run(`INSERT INTO basket_artwork_reservations VALUES ('wr','b1',?,?)`, past, t).catch(() => {});
  // the basket hold must exist for the update case: create it before the single hold, then the single checkout takes the work
  const D3 = mk(await freshDb('c3'));
  await basketSql(D3, 'b1', [{ line: 'r', artist: 'a1', work: 'wr', cents: 10000 }, { line: 'q', artist: 'a1', work: 'wq', cents: 10000 }]);
  await D3.run(`INSERT INTO basket_artwork_reservations VALUES ('wr','b1',?,?)`, past, t);
  await D3.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, quote_expires_at, created_by, created_at, updated_at) VALUES ('or','PA-O-or','a1','wr','PA-E-1','checkout_open',?,'f',?,?)`, future, t, t);
  await D3.run(`INSERT INTO artwork_reservations VALUES ('wr','or',1,?,?)`, future, t);
  check('C2 [H1] an expired basket hold renewed by UPDATE while the single checkout holds the work', await D3.refused(`UPDATE basket_artwork_reservations SET expires_at = ? WHERE artwork_id = 'wr'`, [future], /single-artist/) === true);
  await D3.run(`INSERT INTO basket_artwork_reservations VALUES ('wq','b1',?,?)`, future, t);
  check('C3 [H1] a basket hold moved onto another artwork by UPDATE', await D3.refused(`UPDATE basket_artwork_reservations SET artwork_id = 'wq2' WHERE artwork_id = 'wq'`) === true);
  check('C4 [H1] a basket SALE of a work the single checkout currently holds', await D3.refused(`INSERT INTO basket_artwork_sales VALUES ('b1','wr',?,NULL,NULL)`, [t], /single-artist|own unexpired hold/) === true);
  // reinstatement while a single sale is active
  const D4 = mk(await freshDb('c4'));
  await basketSql(D4, 'b1', [{ line: 'x', artist: 'a1', work: 'wx', cents: 10000 }]);
  await D4.run(`INSERT INTO basket_artwork_reservations VALUES ('wx','b1',?,?)`, future, t);
  await D4.run(`INSERT INTO basket_artwork_sales VALUES ('b1','wx',?,NULL,NULL)`, t);
  await D4.run(`DELETE FROM basket_artwork_reservations WHERE artwork_id = 'wx'`);
  await D4.run(`UPDATE basket_artwork_sales SET released_at = ?, released_reason = 'fully refunded' WHERE artwork_id = 'wx'`, t);
  await D4.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, created_by, created_at, updated_at) VALUES ('os','PA-O-os','a1','wx','PA-E-1','paid','f',?,?)`, t, t);
  await D4.run(`INSERT INTO artwork_sales (order_id, artwork_id, sold_at) VALUES ('os','wx',?)`, t);
  check('C5 [H1] a released basket sale reinstated while a single-artist sale is active', await D4.refused(`UPDATE basket_artwork_sales SET released_at = NULL, released_reason = NULL WHERE artwork_id = 'wx'`, [], /cannot be reinstated/) === true);
  check('C6 [H1] …so there is still exactly ONE active sale of that original across both tables',
    (await D4.q(`SELECT (SELECT COUNT(*) FROM artwork_sales WHERE artwork_id='wx' AND released_at IS NULL) + (SELECT COUNT(*) FROM basket_artwork_sales WHERE artwork_id='wx' AND released_at IS NULL) AS n`).first()).n === 1);
  // reverse direction: single sale of a basket-sold work
  const D5 = mk(await freshDb('c5'));
  await basketSql(D5, 'b1', [{ line: 'y', artist: 'a1', work: 'wy', cents: 10000 }]);
  await D5.run(`INSERT INTO basket_artwork_reservations VALUES ('wy','b1',?,?)`, future, t);
  await D5.run(`INSERT INTO basket_artwork_sales VALUES ('b1','wy',?,NULL,NULL)`, t);
  await D5.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, created_by, created_at, updated_at) VALUES ('oy','PA-O-oy','a1','wy','PA-E-1','checkout_open','f',?,?)`, t, t);
  check('C7 [H1] a single-artist sale of a work already sold by a basket (reverse direction)', await D5.refused(`INSERT INTO artwork_sales (order_id, artwork_id, sold_at) VALUES ('oy','wy',?)`, [t], /UNIQUE constraint failed: this artwork is held or sold through a basket/) === true);
  check('C8 [L3] a basket hold on an artwork that is not one of its lines', await D2.refused(`INSERT INTO basket_artwork_reservations VALUES ('w-unrelated','b2',?,?)`, [future, t], /one of its lines/) === true);
  // money (H2, M5)
  const D6 = mk(await freshDb('c6'));
  await basketSql(D6, 'b1', [{ line: 'l', artist: 'a1', work: 'w1', cents: 100000 }]);
  await paySettle(D6, 'b1');
  check('C14 [H2] a transfer whose key does not follow the deterministic format', await D6.refused(`INSERT INTO basket_transfers (id, basket_id, artist_id, kind, attempt, destination, idempotency_key, source_charge_id, amount_cents, livemode, status, created_at, updated_at) VALUES ('t6','b1','a1','allocation',6,'acct_a1','random-key','ch_b1',1,0,'requested',?,?)`, [t, t], /CHECK/) === true);
  check('C9 [H2] first full transfer accepted', (await trIns(D6, { id: 't1', basket: 'b1', artist: 'a1', amount: 85000 })) === true); await trMade(D6, 't1');
  check('C10 [H2] a SECOND full transfer to the same artist under a different attempt/key', (await trIns(D6, { id: 't2', basket: 'b1', artist: 'a1', attempt: 2, amount: 85000 })) !== true);
  check('C11 [H2] a transfer to a different destination account', (await trIns(D6, { id: 't3', basket: 'b1', artist: 'a1', attempt: 3, amount: 1, dest: 'acct_evil' })) !== true);
  check('C12 [H2] a transfer from a different source charge', (await trIns(D6, { id: 't4', basket: 'b1', artist: 'a1', attempt: 4, amount: 1, charge: 'ch_other' })) !== true);
  check('C13 [H2] a LIVE transfer for a test basket', (await trIns(D6, { id: 't5', basket: 'b1', artist: 'a1', attempt: 5, amount: 1, live: 1 })) !== true);
  await rfIns(D6, { id: 'r1', basket: 'b1', amount: 100000, comm: 15000 }); await partIns(D6, { refund: 'r1', ref: 'l', artist: 'a1', amount: 100000, comm: 15000 });
  check('C15 [H2] first full reversal accepted', (await rvIns(D6, { id: 'v1', transfer: 't1', cause: 'r1', amount: 85000 })) === true);
  check('C16 [H2] a SECOND full reversal of the same transfer (another attempt for the same refund)', (await rvIns(D6, { id: 'v2', transfer: 't1', cause: 'r1', attempt: 2, amount: 85000 })) !== true);
  check('C17 [H2] a refund of 5× the basket total', (await rfIns(D6, { id: 'r9', basket: 'b1', amount: 500000 })) !== true);
  check('C18 [M5] a shipment charge edited after recording', await D6.refused(`UPDATE basket_shipments SET delivery_cents = 150000 WHERE basket_id='b1'`, [], /never change/) === true);
  check('C19 [M5] the settled fee rewritten', await D6.refused(`UPDATE basket_orders SET fee_cents = 1 WHERE id='b1'`, [], /recorded once/) === true);
  check('C20 [M5] the settlement time rewritten', await D6.refused(`UPDATE basket_orders SET settled_at = ? WHERE id='b1'`, [future], /recorded once/) === true);
  const lineCols = (await D6.q(`SELECT name FROM pragma_table_info('basket_lines')`).all()).results.map(r => r.name);
  check('C21 [M5] a line changed after recording is refused, and lines carry no mutable refund counters (refunded amounts derive from refund parts)',
    await D6.refused(`UPDATE basket_lines SET title = 'x' WHERE basket_id='b1'`, [], /never changes/) === true && !lineCols.includes('artwork_refunded_cents') && !lineCols.includes('commission_returned_cents'), lineCols.join(','));
  check('C22 [M5] a basket whose total does not equal its lines + shipments cannot leave draft', await (async () => {
    await D6.run(`INSERT INTO basket_orders (id, reference, status, total_cents, commission_cents, plan_version, plan_sha256, decisions, artist_terms_doc, buyer_terms_doc, transfer_group, created_by, created_at, updated_at) VALUES ('bz','PA-B-z','draft',5000,0,'v',?,'{}','PA-BASKET-TEST-02','PA-BASKET-BPT-TEST-02','plotart-basket-bz','s',?,?)`, H, t, t);
    await D6.run(`INSERT INTO basket_shipments (basket_id, shipment_id, artist_id, method, delivery_cents, insurance_cents) VALUES ('bz','s','a1','collection',0,0)`);
    await D6.run(`INSERT INTO basket_artist_allocations (basket_id, artist_id, account_id, gross_cents, commission_cents, delivery_cents, insurance_cents, transfer_before_fees_cents, release, updated_at) VALUES ('bz','a1','acct_a1',5000,0,0,0,5000,'on_payment',?)`, t);
    await D6.run(`INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis, entitlement_evidence, enquiry_ref) VALUES ('bz','l','a1','wz','s',4000,0,0,'founding_enquiry',?,'PA-E-z')`, ev('a1', 'wz', 'PA-E-z'));
    return D6.refused(`UPDATE basket_orders SET status = 'checkout_open' WHERE id = 'bz'`, [], /does not reconcile/);
  })() === true);
}

/* ---------------------------------------------------------------- X · cross-checkout with checkout.js's own statements */
console.log('— X the single-artist checkout\'s OWN statements (extracted verbatim from checkout.js) against basket holds and sales');
{
  const upsert = CHECKOUT_SRC.match(/run\(env, `(INSERT INTO artwork_reservations[\s\S]*?excluded\.created_at)`/)[1];
  const saleSql = "INSERT INTO artwork_sales (order_id, artwork_id, sold_at) VALUES (?,?,?)";
  const reinstateSql = "UPDATE artwork_sales SET released_at = NULL, released_reason = NULL WHERE order_id = ? AND released_reason = 'fully refunded'";
  check('X0 the statements under test are present in checkout.js exactly as run here', CHECKOUT_SRC.includes(saleSql) && CHECKOUT_SRC.includes(reinstateSql) && /ON CONFLICT\(artwork_id\) DO UPDATE/.test(upsert));
  const handled = msg => /UNIQUE/.test(String(msg));   // how checkout.js startCheckout and recordPaid classify the error
  const X = mk(await freshDb('x'));
  await basketSql(X, 'b1', [{ line: 'h', artist: 'a1', work: 'wh', cents: 10000 }, { line: 's', artist: 'a1', work: 'ws', cents: 10000 }]);
  await X.run(`INSERT INTO basket_artwork_reservations VALUES ('wh','b1',?,?)`, future, t);
  await X.run(`INSERT INTO basket_artwork_reservations VALUES ('ws','b1',?,?)`, future, t);
  await X.run(`INSERT INTO basket_artwork_sales VALUES ('b1','ws',?,NULL,NULL)`, t);
  for (const [id, w] of [['o1', 'wh'], ['o2', 'ws'], ['o3', 'wfree']]) await X.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, quote_expires_at, created_by, created_at, updated_at) VALUES (?,?,?,?,'PA-E-1','checkout_open',?,'f',?,?)`, id, 'PA-O-' + id, 'a1', w, future, t, t);
  const tryUpsert = async (w, o) => { try { await X.q(upsert, w, o, 1, future, t, w).run(); return 'ok'; } catch (e) { return e.message; } };
  const r1 = await tryUpsert('wh', 'o1');
  check('X1 [H1] the single checkout cannot hold a work a basket holds — and the error is the kind checkout.js turns into "someone else is completing a purchase"', r1 !== 'ok' && handled(r1), r1);
  const r2 = await tryUpsert('ws', 'o2');
  check('X2 [H1] …nor a work a basket has sold', r2 !== 'ok' && handled(r2), r2);
  check('X3 a free work is still held normally (existing behaviour unchanged)', (await tryUpsert('wfree', 'o3')) === 'ok');
  let r3; try { await X.q(saleSql, 'o1', 'wh', t).run(); r3 = 'ok'; } catch (e) { r3 = e.message; }
  check('X4 [H1] a late single-artist payment for a basket-held work is refused as a sale — checkout.js then flags it for refund', r3 !== 'ok' && handled(r3), r3);
  await X.run(`UPDATE checkout_orders SET status = 'paid' WHERE id = 'o3'`);
  await X.run(`INSERT INTO artwork_sales (order_id, artwork_id, sold_at, released_at, released_reason) VALUES ('o3','wfree',?,?, 'fully refunded')`, t, t);
  await X.run(`DELETE FROM artwork_reservations WHERE artwork_id = 'wfree'`);
  await X.run(`INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis, entitlement_evidence, enquiry_ref) SELECT 'b9','f','a1','wfree','s-a1',10000,1500,1500,'g',?,'PA-E-f' WHERE 0`, ev('a1', 'wfree', 'PA-E-f'));
  await basketSql(X, 'b9', [{ line: 'f', artist: 'a1', work: 'wfree', cents: 10000 }]);
  await X.run(`INSERT INTO basket_artwork_reservations VALUES ('wfree','b9',?,?)`, future, t);
  let r4; try { await X.q(reinstateSql, 'o3').run(); r4 = 'ok'; } catch (e) { r4 = e.message; }
  check('X5 [H1] the single checkout\'s refund-failure reinstatement is refused while a basket holds the work (refund-reversal path, checkout.js:1423)', r4 !== 'ok' && handled(r4), r4);
  await X.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, created_by, created_at, updated_at) VALUES ('o5','PA-O-o5','a1','wh','PA-E-1','awaiting_artist','f',?,?)`, t, t);
  check('X6 [M1] no new single-artist quote for a work a basket holds', await X.refused(`UPDATE checkout_orders SET status = 'quoted' WHERE id = 'o5'`, [], /UNIQUE constraint failed: this artwork is held or sold through a basket; no quote/) === true);
  // expiry
  const E = mk(await freshDb('e'));
  await basketSql(E, 'b1', [{ line: 'a', artist: 'a1', work: 'we', cents: 10000 }]);
  await basketSql(E, 'b2', [{ line: 'b', artist: 'a1', work: 'we', cents: 10000 }]);
  await E.run(`INSERT INTO basket_artwork_reservations VALUES ('we','b1',?,?)`, past, t);
  check('X7 [H1] a sale following an EXPIRED basket hold is refused', await E.refused(`INSERT INTO basket_artwork_sales VALUES ('b1','we',?,NULL,NULL)`, [t], /own unexpired hold/) === true);
  check('X8 another basket may take over an EXPIRED hold', await E.accepted(`UPDATE basket_artwork_reservations SET basket_id = 'b2', expires_at = ? WHERE artwork_id = 'we'`, future) === true);
  check('X9 …but not an UNEXPIRED one', await E.refused(`UPDATE basket_artwork_reservations SET basket_id = 'b1' WHERE artwork_id = 'we'`, [], /taken over only after it expires/) === true);
  check('X10 a basket sale with a hold belonging to ANOTHER basket is refused', await E.refused(`INSERT INTO basket_artwork_sales VALUES ('b1','we',?,NULL,NULL)`, [t], /own unexpired hold/) === true);
  await E.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, quote_expires_at, created_by, created_at, updated_at) VALUES ('ox','PA-O-ox','a1','wq','PA-E-1','quoted',?,'f',?,?)`, past, t, t);
  await basketSql(E, 'b3', [{ line: 'c', artist: 'a1', work: 'wq', cents: 10000 }]);
  check('X11 an EXPIRED single-artist quote no longer blocks a basket hold', await E.accepted(`INSERT INTO basket_artwork_reservations VALUES ('wq','b3',?,?)`, future, t) === true);
}

/* ---------------------------------------------------------------- K · concurrency */
console.log('— K concurrent writes on the same original or the same money (D1 serialises writes; exactly one wins)');
{
  const K = mk(await freshDb('k'));
  await basketSql(K, 'b1', [{ line: 'a', artist: 'a1', work: 'wk', cents: 10000 }, { line: 'm', artist: 'a1', work: 'wm', cents: 10000 }]);
  await basketSql(K, 'b2', [{ line: 'b', artist: 'a1', work: 'wk', cents: 10000 }]);
  const outcomes = rs => rs.map(r => (r.status === 'fulfilled' ? 'ok' : 'refused'));
  const hold2 = await Promise.allSettled([K.q(`INSERT INTO basket_artwork_reservations VALUES ('wk','b1',?,?)`, future, t).run(), K.q(`INSERT INTO basket_artwork_reservations VALUES ('wk','b2',?,?)`, future, t).run()]);
  check('K1 two baskets reserving the same work at once: exactly one hold', outcomes(hold2).filter(x => x === 'ok').length === 1 && (await K.q(`SELECT COUNT(*) n FROM basket_artwork_reservations WHERE artwork_id='wk'`).first()).n === 1);
  await K.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, created_by, created_at, updated_at) VALUES ('ok1','PA-O-ok1','a1','wm','PA-E-1','checkout_open','f',?,?)`, t, t);
  const mixed = await Promise.allSettled([K.q(`INSERT INTO basket_artwork_reservations VALUES ('wm','b1',?,?)`, future, t).run(), K.q(`INSERT INTO artwork_reservations VALUES ('wm','ok1',1,?,?)`, future, t).run()]);
  const holds = (await K.q(`SELECT (SELECT COUNT(*) FROM basket_artwork_reservations WHERE artwork_id='wm') + (SELECT COUNT(*) FROM artwork_reservations WHERE artwork_id='wm') AS n`).first()).n;
  check('K2 a basket and the single checkout reserving the same work at once: exactly one hold across both', outcomes(mixed).filter(x => x === 'ok').length === 1 && holds === 1, JSON.stringify(outcomes(mixed)));
  await paySettle(K, 'b1');
  const tr2 = await Promise.allSettled([1, 2].map(n => K.q(`INSERT INTO basket_transfers (id, basket_id, artist_id, kind, cause_key, attempt, destination, idempotency_key, source_charge_id, amount_cents, livemode, status, created_at, updated_at)
    VALUES (?,?,?,'allocation','-',?,'acct_a1',?,'ch_b1',17000,0,'requested',?,?)`, 'kt' + n, 'b1', 'a1', n, B.keys.transfer({ basket_id: 'b1', artist_id: 'a1', attempt: n }), t, t).run()));
  check('K3 two transfers to the same artist at once (different attempts): exactly one', outcomes(tr2).filter(x => x === 'ok').length === 1);
  const rf2 = await Promise.allSettled([1, 2].map(n => K.q(`INSERT INTO basket_refunds (id, basket_id, idempotency_key, amount_cents, commission_returned_cents, status, reason, requested_by, livemode, created_at, updated_at)
    VALUES (?,?,?,15000,0,'requested','r','f',0,?,?)`, 'kr' + n, 'b1', B.keys.refund({ basket_id: 'b1', refund_id: 'kr' + n }), t, t).run()));
  check('K4 two refunds that together exceed the payment, at once: exactly one', outcomes(rf2).filter(x => x === 'ok').length === 1);
}

/* ---------------------------------------------------------------- F · financial integrity */
console.log('— F transfers, reversals, refunds, disputes, adjustments: caps, holds, lifecycles, immutability');
{
  const F = mk(await freshDb('f'));
  await basketSql(F, 'b1', [{ line: 'l', artist: 'a1', work: 'w1', cents: 100000 }, { line: 'm', artist: 'a2', work: 'w2', cents: 50000, bp: 0 }]);
  check('F1 no transfer before payment and settlement', (await trIns(F, { id: 'pre', basket: 'b1', artist: 'a1', amount: 1 })) !== true);
  await paySettle(F, 'b1');
  check('F2 the settlement cannot be written again', await F.refused(`UPDATE basket_artist_allocations SET transfer_due_cents = 1, processing_share_cents = 84999 WHERE artist_id = 'a1'`, [], /written once/) === true);
  check('F3 a transfer above what is due is refused', (await trIns(F, { id: 'big', basket: 'b1', artist: 'a1', amount: 85001 })) !== true);
  await F.run(`UPDATE basket_artist_allocations SET release_ready_at = ? WHERE artist_id = 'a2'`, future);
  check('F4 a transfer before the allocation is released is refused', (await trIns(F, { id: 'early', basket: 'b1', artist: 'a2', amount: 50000 })) !== true);
  await F.run(`INSERT INTO basket_disputes (id, basket_id, stripe_dispute_id, amount_cents, status, livemode, opened_at) VALUES ('d1','b1','du_f1',1000,'open',0,?)`, t);
  check('F5 [M4] no transfer while a dispute is open', (await trIns(F, { id: 'dsp', basket: 'b1', artist: 'a1', amount: 1000 })) !== true);
  check('F6 no refund while a dispute is open', (await rfIns(F, { id: 'rdsp', basket: 'b1', amount: 1000 })) !== true);
  await F.run(`UPDATE basket_disputes SET status = 'won', closed_at = ? WHERE id = 'd1'`, t);
  check('F7 [L4] a failed transfer can be retried with the next attempt (new key) — and only then', (await trIns(F, { id: 'a1t1', basket: 'b1', artist: 'a1', amount: 85000 })) === true
    && await F.accepted(`UPDATE basket_transfers SET status = 'failed', failure = 'insufficient platform balance' WHERE id = 'a1t1'`) === true
    && (await trIns(F, { id: 'a1t1b', basket: 'b1', artist: 'a1', attempt: 1, amount: 85000 })) !== true
    && (await trIns(F, { id: 'a1t2', basket: 'b1', artist: 'a1', attempt: 2, amount: 85000 })) === true);
  check('F8 a failed transfer cannot be revived', await F.refused(`UPDATE basket_transfers SET status = 'created', stripe_transfer_id = 'tr_x' WHERE id = 'a1t1'`, [], /requested moves once/) === true);
  await trMade(F, 'a1t2');
  check('F9 a made transfer\'s amount, destination and key never change', await F.refused(`UPDATE basket_transfers SET amount_cents = 1 WHERE id = 'a1t2'`, [], /never change/) === true);
  check('F10 transfers are never deleted', await F.refused(`DELETE FROM basket_transfers WHERE id = 'a1t2'`, [], /never deleted/) === true);
  check('F11 a reversal on a FAILED transfer is refused', (await rvIns(F, { id: 'vbad', transfer: 'a1t1', cause: 'x', amount: 1 })) !== true);
  check('F12 a reversal without an active refund or lost dispute is refused', (await rvIns(F, { id: 'vnocause', transfer: 'a1t2', cause: 'nope', amount: 1 })) !== true);
  // refund lifecycle
  check('F13 a refund with a non-deterministic key is refused', await F.refused(`INSERT INTO basket_refunds (id, basket_id, idempotency_key, amount_cents, commission_returned_cents, status, reason, requested_by, livemode, created_at, updated_at) VALUES ('rk','b1','k',1,0,'requested','r','f',0,?,?)`, [t, t], /CHECK/) === true);
  check('F14 a refund in the wrong mode is refused', (await rfIns(F, { id: 'rlive', basket: 'b1', amount: 1, live: 1 })) !== true);
  await rfIns(F, { id: 'r1', basket: 'b1', amount: 60000, comm: 7500 });
  check('F15 a refund cannot be sent before its parts add up', await F.refused(`UPDATE basket_refunds SET status = 'pending' WHERE id = 'r1'`, [], /parts add up/) === true);
  check('F16 a line part above the line\'s price is refused', (await partIns(F, { refund: 'r1', ref: 'l', artist: 'a1', amount: 100001, comm: 0 })) !== true);
  check('F17 a line part above the line\'s commission is refused', (await partIns(F, { refund: 'r1', ref: 'l', artist: 'a1', amount: 60000, comm: 15001 })) !== true);
  check('F18 a part naming the wrong artist for the line is refused', (await partIns(F, { refund: 'r1', ref: 'l', artist: 'a2', amount: 50000, comm: 7500 })) !== true);
  check('F19 a commission return on a delivery part is refused', (await partIns(F, { refund: 'r1', kind: 'shipment', ref: 's-a1', artist: 'a1', amount: 1, comm: 1 })) !== true);
  await partIns(F, { refund: 'r1', ref: 'l', artist: 'a1', amount: 50000, comm: 7500 }); await partIns(F, { refund: 'r1', ref: 'm', artist: 'a2', amount: 10000, comm: 0 });
  check('F20 complete parts: the refund may be sent and go PENDING', await F.accepted(`UPDATE basket_refunds SET status = 'pending', stripe_refund_id = 're_f1' WHERE id = 'r1'`) === true);
  check('F21 [L4] parts cannot be added after the refund is sent', (await partIns(F, { refund: 'r1', ref: 'm', artist: 'a2', amount: 1 })) !== true);
  await rfIns(F, { id: 'r2', basket: 'b1', amount: 50001 });
  check('F22 [L4] a PENDING refund counts: a new line part beyond what remains of that line is refused', (await partIns(F, { refund: 'r2', ref: 'l', artist: 'a1', amount: 50001 })) !== true);
  check('F23 a refund\'s status never moves backwards, and its amount never changes', await F.refused(`UPDATE basket_refunds SET status = 'requested' WHERE id = 'r1'`, [], /moves forward/) === true
    && await F.refused(`UPDATE basket_refunds SET amount_cents = 1 WHERE id = 'r1'`, [], /never change/) === true);
  check('F24 refund parts and refunds are never deleted', await F.refused(`DELETE FROM basket_refund_parts`, [], /append-only/) === true && await F.refused(`DELETE FROM basket_refunds`, [], /never deleted/) === true);
  check('F25 a reversal above the transfer is refused', (await rvIns(F, { id: 'vbig', transfer: 'a1t2', cause: 'r1', amount: 85001 })) !== true);
  check('F26 the reversal for the refund is accepted; a second one for the same refund is refused while the first is in flight',
    (await rvIns(F, { id: 'v1', transfer: 'a1t2', cause: 'r1', amount: 42500 })) === true && (await rvIns(F, { id: 'v1b', transfer: 'a1t2', cause: 'r1', attempt: 2, amount: 42500 })) !== true);
  check('F27 [L4] a FAILED reversal may be retried with the next attempt', await F.accepted(`UPDATE basket_transfer_reversals SET status = 'failed', failure = 'artist balance' WHERE id = 'v1'`) === true
    && (await rvIns(F, { id: 'v2', transfer: 'a1t2', cause: 'r1', attempt: 2, amount: 42500 })) === true);
  check('F28 a recredit is refused while the refund has NOT failed', (await trIns(F, { id: 'rc', basket: 'b1', artist: 'a1', kind: 'recredit', cause: 'r1', amount: 1 })) !== true);
  // adjustments
  const adj = (id, kind, cause, amt, artist = 'a2') => F.accepted(`INSERT INTO basket_allocation_adjustments (id, basket_id, artist_id, kind, cause_kind, cause_id, amount_cents, at) VALUES (?,?,?,?,?,?,?,?)`, id, 'b1', artist, kind, 'refund', cause, amt, t);
  check('F29 a reduction of a transfer not yet made, within it, is accepted', (await adj('j1', 'pending_reduction', 'r1', 10000)) === true);
  check('F30 a reduction beyond what is not yet transferred is refused', (await adj('j2', 'pending_reduction', 'r2', 40001)) !== true);
  check('F31 the same reduction twice (same cause) is refused', (await adj('j3', 'pending_reduction', 'r1', 1)) !== true);
  check('F32 the transfer cap counts reductions: the artist cannot then be sent the full amount', await (async () => {
    await F.run(`UPDATE basket_artist_allocations SET release_ready_at = ? WHERE artist_id = 'a2'`, past).catch(() => {});
    return (await trIns(F, { id: 'a2full', basket: 'b1', artist: 'a2', amount: 50000 })) !== true && (await trIns(F, { id: 'a2rest', basket: 'b1', artist: 'a2', attempt: 2, amount: 40000 })) === true;
  })());
  check('F33 [L4] a restoration only up to the recorded reduction', (await adj('j4', 'pending_restored', 'r1', 10001)) !== true && (await adj('j5', 'pending_restored', 'r1', 10000)) === true);
  check('F34 a shortfall can be cleared only up to what was recorded', (await adj('j6', 'shortfall', 'r1', 500, 'a1')) === true && (await adj('j7', 'shortfall_cleared', 'r1', 501, 'a1')) !== true);
  check('F35 adjustments are append-only', await F.refused(`UPDATE basket_allocation_adjustments SET amount_cents = 1`, [], /append-only/) === true && await F.refused(`DELETE FROM basket_allocation_adjustments`, [], /append-only/) === true);
  // disputes and refunds share one cap (a clean basket: paid 100,000)
  await basketSql(F, 'bd', [{ line: 'd', artist: 'a1', work: 'wd', cents: 100000 }]); await paySettle(F, 'bd');
  await rfIns(F, { id: 'rd1', basket: 'bd', amount: 30000 });
  check('F36a a dispute above what remains after an active refund is refused (100,000 − 30,000)', await F.refused(`INSERT INTO basket_disputes (id, basket_id, stripe_dispute_id, amount_cents, status, livemode, opened_at) VALUES ('dx','bd','du_fx',70001,'open',0,?)`, [t], /exceeds what remains/) === true);
  await F.run(`INSERT INTO basket_disputes (id, basket_id, stripe_dispute_id, amount_cents, status, livemode, opened_at) VALUES ('d2','bd','du_f2',50000,'open',0,?)`, t);
  await F.run(`UPDATE basket_disputes SET status = 'lost', closed_at = ? WHERE id = 'd2'`, t);
  check('F36b a lost dispute reduces what can still be refunded: 30,000 refunded + 50,000 lost → 20,001 refused, 20,000 accepted',
    (await rfIns(F, { id: 'rd2', basket: 'bd', amount: 20001 })) !== true && (await rfIns(F, { id: 'rd3', basket: 'bd', amount: 20000 })) === true);
  check('F37 disputes are never deleted, and amounts never change', await F.refused(`DELETE FROM basket_disputes`, [], /never deleted/) === true && await F.refused(`UPDATE basket_disputes SET amount_cents = 1 WHERE id = 'd2'`, [], /only moves/) === true);
  check('F38 a dispute larger than the basket cannot be recorded', await F.refused(`INSERT INTO basket_disputes (id, basket_id, stripe_dispute_id, amount_cents, status, livemode, opened_at) VALUES ('d3','b1','du_f3',150001,'open',0,?)`, [t], /no more than its total|exceeds what remains/) === true);
  // terms and modes
  check('F39 [H3] a basket under the issued single-artist terms is refused by the database too', await F.refused(`INSERT INTO basket_orders (id, reference, status, total_cents, commission_cents, plan_version, plan_sha256, decisions, artist_terms_doc, buyer_terms_doc, transfer_group, created_by, created_at, updated_at) VALUES ('bt','PA-B-t','draft',100,0,'v',?,'{}','PA-PAY-2026-11','PA-BPT-2026-11','plotart-basket-bt','s',?,?)`, [H, t, t], /CHECK/) === true);
  check('F40 [H3] TEST placeholder terms on a LIVE basket are refused', await F.refused(`INSERT INTO basket_orders (id, reference, status, livemode, total_cents, commission_cents, plan_version, plan_sha256, decisions, artist_terms_doc, buyer_terms_doc, transfer_group, created_by, created_at, updated_at) VALUES ('bl','PA-B-l','draft',1,100,0,'v',?,'{}','PA-BASKET-TEST-02','PA-BASKET-BPT-TEST-02','plotart-basket-bl','s',?,?)`, [H, t, t], /CHECK/) === true);
  check('F41 a live checkout session on a test basket is refused', await F.refused(`UPDATE basket_orders SET checkout_session_id = 'cs_live_x' WHERE id = 'b1'`, [], /CHECK|written once/) === true);
  check('F42 lines cannot be added once the basket has left draft', await F.refused(`INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis, entitlement_evidence, enquiry_ref) VALUES ('b1','late','a1','wl','s-a1',1000,1500,150,'g',?,'PA-E-late')`, [ev('a1', 'wl', 'PA-E-late')], /only while the basket is a draft/) === true);
  check('F43 [M3] a line whose entitlement evidence is bound to another artwork is refused', await (async () => {
    await F.run(`INSERT INTO basket_orders (id, reference, status, total_cents, commission_cents, plan_version, plan_sha256, decisions, artist_terms_doc, buyer_terms_doc, transfer_group, created_by, created_at, updated_at) VALUES ('be','PA-B-e','draft',100,0,'v',?,'{}','PA-BASKET-TEST-02','PA-BASKET-BPT-TEST-02','plotart-basket-be','s',?,?)`, H, t, t);
    await F.run(`INSERT INTO basket_shipments (basket_id, shipment_id, artist_id, method, delivery_cents, insurance_cents) VALUES ('be','s','a1','collection',0,0)`);
    return F.refused(`INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis, entitlement_evidence, enquiry_ref) VALUES ('be','l','a1','wA','s',1000,0,0,'founding_enquiry',?,'PA-E-1')`, [ev('a1', 'wB', 'PA-E-1')], /CHECK/);
  })() === true);
  check('F44 a basket that left draft cannot be deleted', await F.refused(`DELETE FROM basket_orders WHERE id = 'b1'`, [], /kept with its records/) === true);
}

/* ---------------------------------------------------------------- L · linked purchases across both checkouts (M2) */
console.log('— L the EUR 10,000 linked-purchase check sees both checkouts');
{
  const { linkedCheck } = await import('../src/checkout.js');
  const withBaskets = await freshDb('l'), Lw = mk(withBaskets);
  await basketSql(Lw, 'bl', [{ line: 'l', artist: 'a1', work: 'w1', cents: 900000 }], { buyer: 'collector@example.test' });
  await Lw.run(`UPDATE basket_orders SET payment_status = 'paid', status = 'paid' WHERE id = 'bl'`);
  const o = { id: 'o-new', buyer_email: 'Collector@Example.test', artwork_cents: 150000, delivery_cents: 0 };
  const lc = await linkedCheck({ DB: withBaskets }, o);
  check('L1 [M2] checkout.js linkedCheck counts a paid basket: €9,000 basket + €1,500 single order is refused', lc.ok === false && lc.linked.includes('PA-B-bl') && lc.total_cents === 1050000, JSON.stringify(lc));
  const without = await freshDb('l0', false);
  const lc0 = await linkedCheck({ DB: without }, o);
  check('L2 without migration 0019 linkedCheck behaves exactly as before (no basket table, no error)', lc0.ok === true && lc0.total_cents === 150000 && lc0.linked.length === 0);
  await Lw.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, buyer_email, artwork_cents, delivery_cents, payment_status, created_by, created_at, updated_at) VALUES ('os','PA-O-os','a1','wz','PA-E-1','paid','collector@example.test',90000,1000,'paid','f',?,?)`, new Date().toISOString(), new Date().toISOString());
  await Lw.run(`UPDATE basket_orders SET created_at = ? WHERE id = 'bl'`, new Date().toISOString()).catch(() => {});
  const bl = await B.basketLinkedCheck({ DB: withBaskets }, { buyer_email: 'collector@example.test', total_cents: 5000, exclude_basket_id: 'none' });
  check('L3 [M2] basketLinkedCheck counts single-artist orders and baskets together', bl.linked.includes('PA-O-os') && bl.ok === (bl.total_cents < 1000000), JSON.stringify(bl));
}

/* ---------------------------------------------------------------- B · rollback */
console.log('— B rollback');
{
  const base = await freshDb('rb', false);
  const baseObjs = (await base.prepare("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE '_cf_%' AND name <> 'sqlite_sequence' ORDER BY type, name").all()).results;
  for (const s of statements(MIG)) await base.prepare(s).run();
  const rb = rollbackOf(MIG);
  check('B1 the rollback names all fourteen tables and the five triggers on existing tables', NEW.every(n => rb.includes(`DROP TABLE IF EXISTS ${n};`)) && Object.keys(EXISTING_GUARDS).every(n => rb.includes(`DROP TRIGGER IF EXISTS ${n};`)));
  for (const s of statements(rb)) await base.prepare(s).run();
  const back = (await base.prepare("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE '_cf_%' AND name <> 'sqlite_sequence' ORDER BY type, name").all()).results;
  check('B2 applying then rolling back (before any data) restores exactly the starting schema', JSON.stringify(back) === JSON.stringify(baseObjs));
  const Rb = mk(base);
  await Rb.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, created_by, created_at, updated_at) VALUES ('o','PA-O-o','a','w','PA-E-1','paid','f',?,?)`, t, t);
  check('B3 after rollback the single-artist tables work normally (no dangling trigger reads a dropped basket table)', await Rb.accepted(`INSERT INTO artwork_sales (order_id, artwork_id, sold_at) VALUES ('o','w',?)`, t) === true);
}

for (const mf of mfs) await mf.dispose();
const failed = results.filter(x => !x).length;
console.log(`MIGRATION 0019 · ${results.length} checks, ${results.length - failed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
