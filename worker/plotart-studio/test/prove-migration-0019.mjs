// PROVE · migration 0019 (multi-artist basket records) on a database built from schema.sql, which already holds the
// single-artist pilot tables (0017), with realistic records including a single-artist sale and an open hold.
// New tables only; nothing existing changes; idempotent; documented rollback restores the exact starting state; the
// tables accept exactly what src/basket-rules.js produces and refuse what it would never produce. Local only: a throwaway
// Miniflare D1. Nothing is applied to any real database.
//   node test/prove-migration-0019.mjs
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
const HERE = new URL('..', import.meta.url).pathname;
const MIG = readFileSync(HERE + 'migrations/0019_basket_checkout.sql', 'utf8');
const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig19-' + Date.now() } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
const q = (sql, ...a) => db.prepare(sql).bind(...a);
const refused = async (sql, args, re) => { try { await q(sql, ...args).run(); return false; } catch (e) { return re ? re.test(e.message) : true; } };

await run(readFileSync(HERE + 'schema.sql', 'utf8'));
console.log('PROVE · migration 0019 (multi-artist basket records) on the current schema with existing records');
const t = '2026-11-21T10:00:00.000Z', future = '2099-01-01T00:00:00.000Z', past = '2026-01-01T00:00:00.000Z';
await seedPublished(db, { id: 'arowan', slug: 'rowan-test', email: 'rowan@example.test', name: 'Rowan Test', works: 3, number: 1 });
await seedPublished(db, { id: 'aalder', slug: 'alder-test', email: 'alder@example.test', name: 'Alder Test', works: 3, number: 2 });
// a single-artist pilot order that has SOLD warowan3, and another holding warowan2 (unexpired) and one with an expired hold
const order = (id, ref, work) => q(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, created_by, created_at, updated_at)
  VALUES (?,?,?,?,?,?,?,?,?)`, id, ref, 'arowan', work, 'PA-E-1', 'paid', 'founder', t, t).run();
await order('o-sold', 'PA-O-SOLD', 'warowan3'); await order('o-held', 'PA-O-HELD', 'warowan2'); await order('o-old', 'PA-O-OLD', 'waalder3');
await q('INSERT INTO artwork_sales (order_id, artwork_id, sold_at) VALUES (?,?,?)', 'o-sold', 'warowan3', t).run();
await q('INSERT INTO artwork_reservations (artwork_id, order_id, quote_version, expires_at, created_at) VALUES (?,?,?,?,?)', 'warowan2', 'o-held', 1, future, t).run();
await q('INSERT INTO artwork_reservations (artwork_id, order_id, quote_version, expires_at, created_at) VALUES (?,?,?,?,?)', 'waalder3', 'o-old', 1, past, t).run();

const objects = async () => (await db.prepare("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
const dump = async names => { const o = {}; for (const tb of names) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
const beforeObjects = await objects(), beforeTables = beforeObjects.filter(o => o.type === 'table').map(o => o.name), before = await dump(beforeTables);
check('M0 the base has the single-artist pilot tables and no basket tables', beforeTables.includes('checkout_orders') && !beforeTables.some(n => n.startsWith('basket_')));

await run(MIG);
const after = await objects();
const NEW = ['basket_orders', 'basket_shipments', 'basket_lines', 'basket_artist_allocations', 'basket_transfers', 'basket_refunds', 'basket_refund_parts',
  'basket_disputes', 'basket_transfer_reversals', 'basket_artwork_reservations', 'basket_artwork_sales', 'basket_payment_events', 'basket_events'];
const created = after.filter(o => o.type === 'table').map(o => o.name).filter(n => !beforeTables.includes(n)).sort();
check('M1 the migration creates exactly the thirteen basket tables', JSON.stringify(created) === JSON.stringify([...NEW, 'sqlite_sequence'].filter(n => created.includes(n)).sort()) && NEW.every(n => created.includes(n)), created.join(','));
check('M2 every existing table, index and trigger definition is unchanged', beforeObjects.every(o => after.some(a => a.type === o.type && a.name === o.name && a.sql === o.sql)));
check('M3 every existing row is unchanged', JSON.stringify(await dump(beforeTables)) === JSON.stringify(before));
const newObjs = after.filter(o => !beforeObjects.some(b => b.type === o.type && b.name === o.name));
check('M4 every new index and trigger is on a new table', newObjs.filter(o => o.type !== 'table').every(o => NEW.includes(o.tbl_name)), newObjs.filter(o => o.type !== 'table' && !NEW.includes(o.tbl_name)).map(o => o.name).join(','));
check('M5 every new trigger is a refusal-only BEFORE trigger (reads other tables, writes none)', newObjs.filter(o => o.type === 'trigger')
  .every(o => /BEFORE (INSERT|UPDATE|DELETE)/.test(o.sql) && /SELECT RAISE\(ABORT/.test(o.sql) && !/\b(INSERT INTO|UPDATE \w+ SET|DELETE FROM)\b/.test(o.sql.replace(/BEFORE (INSERT|UPDATE|DELETE) ON/, ''))));
check('M6 no foreign key from the new tables to artists or artworks (participation deletion is never blocked)', !newObjs.some(o => o.sql && /REFERENCES (artists|artworks)\b/.test(o.sql)));
check('M7 no foreign key from the new tables to the single-artist pilot tables (they are only read by guards)', !newObjs.some(o => o.sql && /REFERENCES (checkout_orders|artwork_sales|artwork_reservations)\b/.test(o.sql)));
let again = true; try { await run(MIG); } catch { again = false; }
check('M8 running it twice is harmless', again && JSON.stringify(await objects()) === JSON.stringify(after));

/* ---------------------------------------------------------------- the engine's plan, recorded */
console.log('— R the tables record exactly what basket-rules.js produces');
const DEC = { processing_fee_bearer: 'artists_pro_rata', transfer_timing: 'after_delivery', dispute_loss_bearer: 'artists_by_line', dispute_fee_bearer: 'plotart', basket_introduction: 'logged_enquiry_only' };
const COVER = v => ({ cover_type: 'transit_insurance', covered_value_cents: v, insured_party: 'transporter' });
const plan = B.plan({
  lines: [
    { line_id: 'l1', artist_id: 'arowan', artwork_id: 'warowan1', shipment_id: 's1', artwork_cents: 145000, entitlement: { ok: true, bp: 1500, basis: 'gallery_artist_agreement', evidence: { doc_id: 'PA-GAA-2026-11' } } },
    { line_id: 'l2', artist_id: 'aalder', artwork_id: 'waalder1', shipment_id: 's2', artwork_cents: 210000, entitlement: { ok: true, bp: 0, basis: 'founding_enquiry' }, processing_consent: true },
  ],
  shipments: [
    { shipment_id: 's1', artist_id: 'arowan', method: 'delivery', delivery_cents: 3500, insurance_cents: 1200, cover: COVER(145000) },
    { shipment_id: 's2', artist_id: 'aalder', method: 'collection', delivery_cents: 0, insurance_cents: 0 },
  ] }, DEC);
const sha = createHash('sha256').update(JSON.stringify(plan)).digest('hex');
const ins = (sql, ...a) => q(sql, ...a).run();
await ins(`INSERT INTO basket_orders (id, reference, status, buyer_email, livemode, total_cents, commission_cents, plan_version, plan_sha256, decisions, transfer_group, created_by, created_at, updated_at)
  VALUES ('b1','PA-B-0001','draft','buyer@example.test',0,?,?,?,?,?,'plotart-basket-b1','system',?,?)`, plan.total_cents, plan.commission_cents, plan.version, sha, JSON.stringify(plan.decisions), t, t);
for (const s of plan.shipments) await ins(`INSERT INTO basket_shipments (basket_id, shipment_id, artist_id, method, delivery_cents, insurance_cents, cover) VALUES ('b1',?,?,?,?,?,?)`,
  s.shipment_id, s.artist_id, s.method, s.delivery_cents, s.insurance_cents, s.cover ? JSON.stringify(s.cover) : null);
for (const l of plan.lines) await ins(`INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis, entitlement_evidence, enquiry_ref, processing_consent)
  VALUES ('b1',?,?,?,?,?,?,?,?,?,?,?)`, l.line_id, l.artist_id, l.artwork_id, l.shipment_id, l.artwork_cents, l.commission_bp, l.commission_cents, l.commission_basis,
  l.entitlement_evidence ? JSON.stringify(l.entitlement_evidence) : null, 'PA-E-' + l.line_id, l.processing_consent ? 1 : 0);
for (const a of plan.artists) await ins(`INSERT INTO basket_artist_allocations (basket_id, artist_id, account_id, gross_cents, commission_cents, delivery_cents, insurance_cents, transfer_before_fees_cents, release, updated_at)
  VALUES ('b1',?,?,?,?,?,?,?,?,?)`, a.artist_id, 'acct_' + a.artist_id, a.gross_cents, a.commission_cents, a.delivery_cents, a.insurance_cents, a.transfer_before_fees_cents, a.release, t);
check('R1 a plan (two artists, 15% and Founding 0%, delivered and collected) is accepted as recorded', (await q("SELECT COUNT(*) AS n FROM basket_lines WHERE basket_id = 'b1'").first()).n === 2);
const st = B.settle(plan, { fee_cents: 5600, fee_vat_cents: 1288 });
await ins(`UPDATE basket_orders SET status = 'paid', payment_status = 'paid', checkout_session_id = 'cs_test_1', payment_intent_id = 'pi_1', charge_id = 'ch_1', fee_cents = 5600, fee_vat_cents = 1288, paid_at = ?, settled_at = ?, updated_at = ? WHERE id = 'b1'`, t, t, t);
for (const a of st.artists) await ins(`UPDATE basket_artist_allocations SET processing_share_cents = ?, transfer_due_cents = ?, status = 'held', updated_at = ? WHERE basket_id = 'b1' AND artist_id = ?`, a.processing_share_cents, a.transfer_cents, t, a.artist_id);
check('R2 settlement (artists bear the fee) is accepted: each due transfer = before-fees − processing share', (await q("SELECT COUNT(*) AS n FROM basket_artist_allocations WHERE transfer_due_cents = transfer_before_fees_cents - processing_share_cents").first()).n === 2);
const rw = st.artists.find(a => a.artist_id === 'arowan');
await ins(`INSERT INTO basket_transfers (id, basket_id, artist_id, destination, idempotency_key, stripe_transfer_id, source_charge_id, amount_cents, livemode, status, created_at, updated_at)
  VALUES ('tr-row1','b1','arowan','acct_arowan','basket-b1-arowan','tr_1','ch_1',?,0,'created',?,?)`, rw.transfer_cents, t, t);
await ins(`UPDATE basket_artist_allocations SET transferred_cents = ?, status = 'transferred' WHERE basket_id = 'b1' AND artist_id = 'arowan'`, rw.transfer_cents);
check('R3 a transfer of the settled amount is recorded', true);
const rf = B.refund(plan, { artists: { arowan: { transfer_due_cents: rw.transfer_cents, transferred_cents: rw.transfer_cents } } }, { lines: [{ line_id: 'l1', artwork_cents: 50000 }] });
await ins(`INSERT INTO basket_refunds (id, basket_id, idempotency_key, stripe_refund_id, amount_cents, commission_returned_cents, status, reason, requested_by, livemode, created_at, updated_at)
  VALUES ('rf1','b1','basket-b1-rf1','re_1',?,?,'succeeded','agreed partial refund','founder',0,?,?)`, rf.buyer_refund_cents, rf.commission_returned_cents, t, t);
for (const l of rf.lines) await ins(`INSERT INTO basket_refund_parts (refund_id, kind, ref, artist_id, amount_cents, commission_returned_cents, artist_debit_cents) VALUES ('rf1','line',?,?,?,?,?)`,
  l.line_id, l.artist_id, l.artwork_refund_cents, l.commission_returned_cents, l.artist_debit_cents);
await ins(`INSERT INTO basket_transfer_reversals (id, transfer_id, cause_kind, cause_id, idempotency_key, stripe_reversal_id, amount_cents, status, created_at, updated_at)
  VALUES ('rv1','tr-row1','refund','rf1','basket-b1-rf1-arowan','trr_1',?,'created',?,?)`, rf.artists[0].reverse_cents, t, t);
await ins(`UPDATE basket_transfers SET amount_reversed_cents = ? WHERE id = 'tr-row1'`, rf.artists[0].reverse_cents);
await ins(`UPDATE basket_lines SET artwork_refunded_cents = ?, commission_returned_cents = ? WHERE basket_id = 'b1' AND line_id = 'l1'`, 50000, rf.commission_returned_cents);
await ins(`UPDATE basket_artist_allocations SET reversed_cents = ?, status = 'partially_reversed' WHERE basket_id = 'b1' AND artist_id = 'arowan'`, rf.artists[0].reverse_cents);
check('R4 a partial refund, its per-line parts (commission returned) and the transfer reversal are recorded', (await q("SELECT SUM(amount_cents) AS a FROM basket_refund_parts WHERE refund_id='rf1'").first()).a === rf.buyer_refund_cents);
await ins(`INSERT INTO basket_disputes (id, basket_id, stripe_dispute_id, amount_cents, fee_cents, status, livemode, opened_at) VALUES ('d1','b1','du_1',?,2000,'open',0,?)`, 10000, t);
check('R5 an open dispute is recorded', true);
await ins(`INSERT INTO basket_artwork_reservations (artwork_id, basket_id, expires_at, created_at) VALUES ('warowan1','b1',?,?)`, future, t);
await ins(`INSERT INTO basket_artwork_sales (basket_id, artwork_id, sold_at) VALUES ('b1','warowan1',?)`, t);
check('R6 a basket reservation and sale of a work free on both paths are accepted', true);
check('R7 a work whose single-artist hold has EXPIRED can be reserved by a basket', await q(`INSERT INTO basket_artwork_reservations (artwork_id, basket_id, expires_at, created_at) VALUES ('waalder3','b1',?,?)`, future, t).run().then(() => true, () => false));
await ins(`INSERT INTO basket_payment_events (event_id, type, livemode, basket_id, created, status, received_at) VALUES ('evt_1','checkout.session.completed',0,'b1',1,'processed',?)`, t);
await ins(`INSERT INTO basket_events (basket_id, actor, kind, from_status, to_status, detail, at) VALUES ('b1','system','paid','draft','paid','{}',?)`, t);

await ins(`INSERT INTO basket_orders (id, reference, status, total_cents, commission_cents, plan_version, plan_sha256, decisions, transfer_group, created_by, created_at, updated_at)
  VALUES ('b2','PA-B-0002','draft',100,0,'v',?,'{}','plotart-basket-b2','system',?,?)`, 'b'.repeat(64), t, t);
console.log('— C the tables refuse what the rules never produce');
const C = [
  ['C1 the same original sold through the single-artist pilot cannot be reserved by a basket', `INSERT INTO basket_artwork_reservations (artwork_id, basket_id, expires_at, created_at) VALUES ('warowan3','b1','${future}','${t}')`, /single-artist/],
  ['C2 a work held (unexpired) by the single-artist pilot cannot be reserved by a basket', `INSERT INTO basket_artwork_reservations (artwork_id, basket_id, expires_at, created_at) VALUES ('warowan2','b1','${future}','${t}')`, /single-artist/],
  ['C3 a work sold through the single-artist pilot cannot be recorded as a basket sale', `INSERT INTO basket_artwork_sales (basket_id, artwork_id, sold_at) VALUES ('b1','warowan3','${t}')`, /single-artist/],
  ['C4 a commission that is not floor(price × rate) is refused', `INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis) VALUES ('b1','lx','arowan','wx','s1',333,1500,50,'gallery_artist_agreement')`, /CHECK/],
  ['C5 a rate above 15% is refused', `INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis) VALUES ('b1','lx','arowan','wx','s1',1000,1600,160,'x')`, /CHECK/],
  ['C6 the same artwork twice in one basket is refused', `INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis) VALUES ('b1','lx','arowan','warowan1','s1',1000,0,0,'x')`, /UNIQUE/],
  ['C7 a line in another artist\'s shipment is refused (foreign key)', `INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis) VALUES ('b1','lx','aalder','wy','s1',1000,0,0,'x')`, /FOREIGN KEY/],
  ['C8 a delivery shipment without cover is refused', `INSERT INTO basket_shipments (basket_id, shipment_id, artist_id, method, delivery_cents, insurance_cents) VALUES ('b1','s9','arowan','delivery',100,0)`, /CHECK/],
  ['C9 a basket total of EUR 10,000 or more is refused', `INSERT INTO basket_orders (id, reference, status, total_cents, commission_cents, plan_version, plan_sha256, decisions, transfer_group, created_by, created_at, updated_at) VALUES ('b9','PA-B-9','draft',1000000,0,'v','${'a'.repeat(64)}','{}','plotart-basket-b9','s','${t}','${t}')`, /CHECK/],
  ['C10 an allocation that does not balance (gross ≠ commission + transfer) is refused', `INSERT INTO basket_artist_allocations (basket_id, artist_id, account_id, gross_cents, commission_cents, delivery_cents, insurance_cents, transfer_before_fees_cents, release, updated_at) VALUES ('b1','ax','acct_x',1000,150,0,0,851,'on_payment','${t}')`, /CHECK/],
  ['C11 transferring more than is due is refused', `UPDATE basket_artist_allocations SET transferred_cents = transfer_due_cents + 1 WHERE basket_id = 'b1' AND artist_id = 'arowan'`, /CHECK/],
  ['C12 reversing more than was transferred is refused', `UPDATE basket_transfers SET amount_reversed_cents = amount_cents + 1 WHERE id = 'tr-row1'`, /CHECK/],
  ['C13 a refund part that does not balance (amount ≠ debit + commission) is refused', `INSERT INTO basket_refund_parts (refund_id, kind, ref, artist_id, amount_cents, commission_returned_cents, artist_debit_cents) VALUES ('rf1','shipment','s1','arowan',100,0,99)`, /CHECK/],
  ['C14 commission returned on a delivery refund is refused', `INSERT INTO basket_refund_parts (refund_id, kind, ref, artist_id, amount_cents, commission_returned_cents, artist_debit_cents) VALUES ('rf1','shipment','s1','arowan',100,15,85)`, /CHECK/],
  ['C15 refund parts are append-only', `UPDATE basket_refund_parts SET artist_debit_cents = 0`, /append-only/],
  ['C16 a basket\'s money cannot change after it is recorded', `UPDATE basket_orders SET total_cents = total_cents + 1 WHERE id = 'b1'`, /never change/],
  ['C17 a basket\'s decisions cannot change after it is recorded', `UPDATE basket_orders SET decisions = '{"processing_fee_bearer":"plotart"}' WHERE id = 'b1'`, /never change/],
  ['C18 a line\'s price and commission cannot change', `UPDATE basket_lines SET commission_cents = 0 WHERE line_id = 'l1'`, /never change/],
  ['C19 a transfer\'s amount cannot change', `UPDATE basket_transfers SET amount_cents = 1 WHERE id = 'tr-row1'`, /never change/],
  ['C20 a duplicate transfer idempotency key is refused', `INSERT INTO basket_transfers (id, basket_id, artist_id, destination, idempotency_key, source_charge_id, amount_cents, livemode, status, created_at, updated_at) VALUES ('tr2','b1','arowan','acct_arowan','basket-b1-arowan','ch_1',1,0,'requested','${t}','${t}')`, /UNIQUE/],
  ['C21 a second active basket sale of the same work (by another basket) is refused', `INSERT INTO basket_artwork_sales (basket_id, artwork_id, sold_at) VALUES ('b2','warowan1','${t}')`, /UNIQUE/],
  ['C22 a basket sale cannot be deleted', `DELETE FROM basket_artwork_sales`, /kept with their basket/],
  ['C23 the audit trail is append-only', `UPDATE basket_events SET kind = 'x'`, /append-only/],
  ['C24 a non-Stripe checkout session id is refused', `UPDATE basket_orders SET checkout_session_id = 'sess_1' WHERE id = 'b1'`, /CHECK/],
  ['C25 settled without the fee recorded is refused', `INSERT INTO basket_orders (id, reference, status, total_cents, commission_cents, plan_version, plan_sha256, decisions, transfer_group, settled_at, created_by, created_at, updated_at) VALUES ('b8','PA-B-8','paid',100,0,'v','${'a'.repeat(64)}','{}','plotart-basket-b8','${t}','s','${t}','${t}')`, /CHECK/],
];
for (const [n, sql, re] of C) check(n, await refused(sql, [], re));
check('C26 the single-artist pilot\'s own rows are untouched by all of this', JSON.stringify((await dump(['checkout_orders', 'artwork_sales', 'artwork_reservations']))) === JSON.stringify({ checkout_orders: before.checkout_orders, artwork_sales: before.artwork_sales, artwork_reservations: before.artwork_reservations }));

console.log('— B rollback');
const fresh = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig19-rb-' + Date.now() } });
const db2 = await fresh.getD1Database('DB');
for (const s of statements(readFileSync(HERE + 'schema.sql', 'utf8'))) await db2.prepare(s).run();
const base2 = (await db2.prepare("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
for (const s of statements(MIG)) await db2.prepare(s).run();
const rb = rollbackOf(MIG);
check('B1 the rollback names all thirteen tables', NEW.every(n => rb.includes(`DROP TABLE IF EXISTS ${n};`)));
for (const s of statements(rb)) await db2.prepare(s).run();
const back = (await db2.prepare("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE '_cf_%' ORDER BY type, name").all()).results.filter(o => o.name !== 'sqlite_sequence');
check('B2 applying then rolling back (before any data) restores exactly the starting schema', JSON.stringify(back) === JSON.stringify(base2.filter(o => o.name !== 'sqlite_sequence')));
await fresh.dispose(); await mf.dispose();

const failed = results.filter(x => !x).length;
console.log(`MIGRATION 0019 · ${results.length} checks, ${results.length - failed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
