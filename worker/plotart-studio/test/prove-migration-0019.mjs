// PROVE · migration 0019 (revision 3) on databases built from schema.sql (which holds the single-artist pilot tables of
// 0017), with realistic records. Local only: throwaway Miniflare D1s; nothing is applied to any real database.
//   node test/prove-migration-0019.mjs
// Sections: M additivity and repository policy · B backfill of claims · R the engine's plan recorded end to end (incl. N1)
// · S strict status machine (N2) · C one original across both checkouts, using checkout.js's OWN statements and functions
// (H1, M1) · N reverseRefund under a basket conflict (N4) · K concurrency · F money: caps, liability per cause (N3),
// lifecycles, immutability · T terms and commission-free gate in the database (N6) · W the review's reproductions and lows
// · L linked purchases across both checkouts (M2) · Z rollback.
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { statements, rollbackOf } from './sql.mjs';
import { seedPublished } from './seed.mjs';
import * as B from '../src/basket-rules.js';
import * as CO from '../src/checkout.js';

const { Miniflare } = createRequire('/tmp/claude-0/studio-tools/package.json')('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
process.on('uncaughtException', e => { console.log(`  FAIL  uncaught: ${e.message}`); console.log('MIGRATION 0019 · FAILED'); process.exit(1); });
process.on('unhandledRejection', e => { console.log(`  FAIL  unhandled: ${e && e.message}`); console.log('MIGRATION 0019 · FAILED'); process.exit(1); });
const HERE = new URL('..', import.meta.url).pathname, ROOT = new URL('../../..', import.meta.url).pathname;
const MIG_PATH = HERE + 'migrations/0019_basket_checkout.sql';
const MIG = readFileSync(MIG_PATH, 'utf8'), SCHEMA = readFileSync(HERE + 'schema.sql', 'utf8');
const mfs = [];
async function freshDb(withMig = true) {
  const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'm19-' + Date.now() + Math.random() } });
  mfs.push(mf);
  const db = await mf.getD1Database('DB');
  for (const s of statements(SCHEMA)) await db.prepare(s).run();
  if (withMig) for (const s of statements(MIG)) await db.prepare(s).run();
  return db;
}
const mk = db => {
  const q = (sql, ...a) => db.prepare(sql).bind(...a);
  const tryRun = async (sql, ...a) => { try { await q(sql, ...a).run(); return true; } catch (e) { return e.message; } };
  return { db, q, run: (sql, ...a) => q(sql, ...a).run(), accepted: tryRun,
    refused: async (sql, args = [], re = null) => { const r = await tryRun(sql, ...args); return r === true ? false : (re ? re.test(r) || r : true); },
    batch: async sts => { try { await db.batch(sts.map(([s, ...a]) => q(s, ...a))); return true; } catch (e) { return e.message; } } };
};
const t = new Date().toISOString(), future = '2099-01-01T00:00:00.000Z', past = '2026-01-01T00:00:00.000Z', H = 'a'.repeat(64);
const DEC = { processing_fee_bearer: 'plotart', transfer_timing: 'on_payment', dispute_loss_bearer: 'plotart', dispute_fee_bearer: 'plotart', basket_introduction: 'logged_enquiry_only' };
const ev = (aid, wid, ref) => JSON.stringify({ rule: 'x', binding: { artist_id: aid, artwork_id: wid, enquiry_ref: ref, enquiry_log_id: 'e' } });
const WHY = 'refund failed after succeeding: card closed';
const DEC_ARTISTS = { ...DEC, dispute_loss_bearer: 'artists_by_line', dispute_fee_bearer: 'artists_by_line' };

/* A basket built in SQL, as the basket path would: a draft with its lines, one shipment per artist and allocations, then
   opened (reconciled). lines: [{ line, artist, work, cents, bp }] */
async function basket(D, id, lines, { open = true, terms = ['PA-BASKET-TEST-02', 'PA-BASKET-BPT-TEST-02'], decisions = DEC, buyer = 'buyer@example.test', release = 'on_payment', shipCharge = 0 } = {}) {
  const com = l => Math.floor(l.cents * (l.bp ?? 1500) / 10000);
  const artists = [...new Set(lines.map(l => l.artist))];
  const total = lines.reduce((a, l) => a + l.cents, 0) + shipCharge * artists.length, comm = lines.reduce((a, l) => a + com(l), 0);
  await D.run(`INSERT INTO basket_orders (id, reference, status, buyer_email, livemode, total_cents, commission_cents, plan_version, plan_sha256, decisions, artist_terms_doc, buyer_terms_doc, transfer_group, created_by, created_at, updated_at)
    VALUES (?,?,'draft',?,0,?,?,'v',?,?,?,?,?,'system',?,?)`, id, 'PA-B-' + id, buyer, total, comm, H, JSON.stringify(decisions), terms[0], terms[1], 'plotart-basket-' + id, t, t);
  for (const a of artists) {
    await D.run(`INSERT INTO basket_shipments (basket_id, shipment_id, artist_id, method, delivery_cents, insurance_cents, cover) VALUES (?,?,?,?,?,0,?)`, id, 's-' + a, a, shipCharge ? 'delivery' : 'collection', shipCharge, shipCharge ? '{"cover_type":"transit_insurance"}' : null);
    const ls = lines.filter(l => l.artist === a), g = ls.reduce((x, l) => x + l.cents, 0) + shipCharge, c = ls.reduce((x, l) => x + com(l), 0);
    await D.run(`INSERT INTO basket_artist_allocations (basket_id, artist_id, account_id, gross_cents, commission_cents, delivery_cents, insurance_cents, transfer_before_fees_cents, release, updated_at)
      VALUES (?,?,?,?,?,?,0,?,?,?)`, id, a, 'acct_' + a, g, c, shipCharge, g - c, release, t);
  }
  for (const l of lines) await ensureWork(D, l.work, l.artist);
  for (const l of lines) await D.run(`INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis, entitlement_evidence, enquiry_ref)
    VALUES (?,?,?,?,?,?,?,?,'gallery_artist_agreement',?,?)`, id, l.line, l.artist, l.work, 's-' + l.artist, l.cents, l.bp ?? 1500, com(l), ev(l.artist, l.work, 'PA-E-' + id + l.line), 'PA-E-' + id + l.line);
  if (open) await D.run(`UPDATE basket_orders SET status = 'checkout_open', reconciled_at = ? WHERE id = ?`, t, id);
}
/* every artwork a test names exists, as in production (an artist row and an available artwork) */
async function ensureWork(D, work, artist = 'a1') {
  await D.run("INSERT OR IGNORE INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES (?,?,?,?,0,'active',?,?)", artist, artist, artist + '@example.test', artist, t, t);
  await D.run("INSERT OR IGNORE INTO artworks (id, artist_id, slug, title, year, medium, h_cm, w_cm, price_eur, availability, description, ord, ai_involvement, archived, created_at, updated_at) VALUES (?,?,?,?,2026,'painting',50,40,100,'available','d',1,'none',0,?,?)", work, artist, work, work, t, t);
}
const MARK_RESERVED = ["UPDATE artworks SET availability = 'reserved', updated_at = ? WHERE id = ? AND availability IN ('available','reserved')"];
/* the basket path's hold: stale claim cleared, the artwork marked reserved (rollback safety, H-1), claim taken, reservation
   written, in ONE batch (one transaction) */
const basketHold = async (D, id, work, until = future) => { await ensureWork(D, work); return D.batch([
  [CO.CLAIM_SQL.dropStale, work],
  [MARK_RESERVED[0], t, work],
  ["INSERT INTO artwork_claims (artwork_id, holder_kind, holder_id, kind, expires_at, claimed_at) VALUES (?, 'basket', ?, 'hold', ?, ?)", work, id, until, t],
  ['INSERT INTO basket_artwork_reservations (artwork_id, basket_id, expires_at, created_at) VALUES (?,?,?,?)', work, id, until, t]]); };
const pay = (D, id) => D.run(`UPDATE basket_orders SET status = 'paid', payment_status = 'paid', checkout_session_id = ?, payment_intent_id = ?, charge_id = ?, paid_at = ?, updated_at = ? WHERE id = ?`, 'cs_test_' + id, 'pi_' + id, 'ch_' + id, t, t, id);
/* the basket path's sale: its hold claim becomes the sale claim, asserted, the sale recorded, the reservation released, in ONE batch */
const basketSell = (D, id, work) => D.batch([
  ["UPDATE artworks SET availability = 'sold', updated_at = ? WHERE id = ? AND availability IN ('available','reserved')", t, work],
  ["UPDATE artwork_claims SET kind = 'sale', expires_at = NULL WHERE artwork_id = ? AND holder_kind = 'basket' AND holder_id = ? AND kind = 'hold'", work, id],
  ["INSERT INTO artwork_claim_assertions (artwork_id, holder_kind, holder_id, kind, purpose, at) VALUES (?, 'basket', ?, 'sale', 'paid', ?)", work, id, t],
  ['INSERT INTO basket_artwork_sales (basket_id, artwork_id, sold_at) VALUES (?,?,?)', id, work, t],
  ['DELETE FROM basket_artwork_reservations WHERE artwork_id = ? AND basket_id = ?', work, id]]);
async function settle(D, id, fee = 100) {
  await D.run(`UPDATE basket_orders SET fee_cents = ?, fee_vat_cents = 0, settled_at = ? WHERE id = ?`, fee, t, id);
  await D.run(`UPDATE basket_artist_allocations SET processing_share_cents = 0, transfer_due_cents = transfer_before_fees_cents WHERE basket_id = ?`, id);
}
const release = (D, id, artist) => D.accepted(`UPDATE basket_artist_allocations SET release_ready_at = ? WHERE basket_id = ? AND artist_id = ?`, t, id, artist);
const trIns = (D, { id, basket: b, artist, attempt = 1, amount, kind = 'allocation', cause = '-', dest = 'acct_' + artist, charge = 'ch_' + b, live = 0, reason = undefined, by = undefined }) =>
  D.accepted(`INSERT INTO basket_transfers (id, basket_id, artist_id, kind, cause_key, attempt, destination, idempotency_key, source_charge_id, amount_cents, livemode, status, reason, requested_by, created_at, updated_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,'requested',?,?,?,?)`, id, b, artist, kind, cause, attempt, dest, B.keys.transfer({ basket_id: b, artist_id: artist, kind, cause_key: cause, attempt }), charge, amount, live,
    reason !== undefined ? reason : (kind === 'allocation' ? null : WHY), by !== undefined ? by : (kind === 'allocation' ? null : 'founder'), t, t);
const trMade = (D, id) => D.run(`UPDATE basket_transfers SET status = 'created', stripe_transfer_id = ? WHERE id = ?`, 'tr_' + id, id);
const rfIns = (D, { id, basket: b, amount, comm = 0, live = 0 }) => D.accepted(`INSERT INTO basket_refunds (id, basket_id, idempotency_key, amount_cents, commission_returned_cents, status, reason, requested_by, livemode, created_at, updated_at)
  VALUES (?,?,?,?,?,'requested','buyer cancelled','founder',?,?,?)`, id, b, B.keys.refund({ basket_id: b, refund_id: id }), amount, comm, live, t, t);
const partIns = (D, { refund, kind = 'line', ref, artist, amount, comm = 0 }) => D.accepted(`INSERT INTO basket_refund_parts (refund_id, kind, ref, artist_id, amount_cents, commission_returned_cents, artist_debit_cents) VALUES (?,?,?,?,?,?,?)`,
  refund, kind, ref, artist, amount, comm, amount - comm);
const rvIns = (D, { id, transfer, cause_kind = 'refund', cause, attempt = 1, amount }) => D.accepted(`INSERT INTO basket_transfer_reversals (id, transfer_id, cause_kind, cause_id, attempt, idempotency_key, amount_cents, status, created_at, updated_at)
  VALUES (?,?,?,?,?,?,?,'requested',?,?)`, id, transfer, cause_kind, cause, attempt, B.keys.reversal({ transfer_id: transfer, cause_kind, cause_id: cause, attempt }), amount, t, t);
const adj = (D, { id, basket: b, artist, kind, cause_kind = 'refund', cause, amount, reason = WHY }) => D.accepted(`INSERT INTO basket_allocation_adjustments (id, basket_id, artist_id, kind, cause_kind, cause_id, amount_cents, reason, recorded_by, at)
  VALUES (?,?,?,?,?,?,?,?,'founder',?)`, id, b, artist, kind, cause_kind, cause, amount, reason, t);
const order = (D, id, work, status = 'checkout_open', qexp = null, extra = {}) => D.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, quote_expires_at, buyer_email, artwork_cents, delivery_cents, payment_status, created_by, created_at, updated_at)
  VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)`, id, 'PA-O-' + id, extra.artist || 'a1', work, 'PA-E-1', status, qexp, extra.email || 'other@example.test', extra.cents ?? null, extra.cents == null ? null : 0, extra.payment || 'none', 'founder', t, t);
/* the single-artist checkout's hold and sale, built from checkout.js's OWN exported statements, as startCheckout and recordPaid run them */
const singleHold = (env, o, until = future) => env.DB.batch([...CO.claimHoldSts(env, o, until, t), env.DB.prepare(CO.RESERVE_SQL).bind(o.artwork_id, o.id, 1, until, t, o.artwork_id)])
  .then(rs => rs[rs.length - 1].meta.changes === 1 ? 'held' : 'not held', e => e.message);
const singleSale = (env, o) => env.DB.batch([...CO.claimSaleSts(env, o, t, 'paid'), env.DB.prepare(CO.SALE_SQL).bind(o.id, o.artwork_id, t)]).then(() => 'sold', e => e.message);
const handled = msg => /UNIQUE/.test(String(msg));   // how checkout.js startCheckout and recordPaid classify a refused hold or sale

/* ---------------------------------------------------------------- M · additivity and repository policy */
console.log('PROVE · migration 0019 (revision 3) on the current schema with existing records');
const NEW = ['basket_terms', 'basket_orders', 'basket_shipments', 'basket_lines', 'basket_artist_allocations', 'basket_disputes', 'basket_dispute_allocations', 'basket_refunds',
  'basket_refund_parts', 'basket_transfers', 'basket_transfer_reversals', 'basket_allocation_adjustments', 'checkout_capabilities', 'artwork_claims', 'artwork_claim_assertions',
  'basket_artwork_reservations', 'basket_artwork_sales', 'basket_payment_events', 'basket_events'];
{
  const db = await freshDb(false), D = mk(db);
  await seedPublished(db, { id: 'arowan', slug: 'rowan-test', email: 'rowan@example.test', name: 'Rowan Test', works: 3, number: 1 });
  await order(D, 'osold', 'warowan3', 'paid'); await order(D, 'oheld', 'warowan2', 'checkout_open', future); await order(D, 'oold', 'warowan1', 'expired', past);
  await D.run('INSERT INTO artwork_sales (order_id, artwork_id, sold_at) VALUES (?,?,?)', 'osold', 'warowan3', t);
  await D.run('INSERT INTO artwork_reservations (artwork_id, order_id, quote_version, expires_at, created_at) VALUES (?,?,?,?,?)', 'warowan2', 'oheld', 1, future, t);
  await D.run('INSERT INTO artwork_reservations (artwork_id, order_id, quote_version, expires_at, created_at) VALUES (?,?,?,?,?)', 'warowan1', 'oold', 1, past, t);
  const objects = async () => (await db.prepare("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
  const dump = async names => { const o = {}; for (const tb of names) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
  const beforeObjects = await objects(), beforeTables = beforeObjects.filter(o => o.type === 'table').map(o => o.name), before = await dump(beforeTables);
  check('M0 the base has the single-artist pilot tables and none of the new ones', beforeTables.includes('checkout_orders') && !NEW.some(n => beforeTables.includes(n)));
  for (const s of statements(MIG)) await db.prepare(s).run();
  const after = await objects();
  const created = after.filter(o => o.type === 'table').map(o => o.name).filter(n => !beforeTables.includes(n) && n !== 'sqlite_sequence').sort();
  check('M1 the migration creates exactly the nineteen new tables', JSON.stringify(created) === JSON.stringify([...NEW].sort()), created.join(','));
  check('M2 every existing table, index and trigger definition is unchanged', beforeObjects.every(o => after.some(a => a.type === o.type && a.name === o.name && a.sql === o.sql)));
  check('M3 every existing row is unchanged', JSON.stringify(await dump(beforeTables)) === JSON.stringify(before));
  const newObjs = after.filter(o => !beforeObjects.some(b => b.type === o.type && b.name === o.name));
  check('M4 [policy] EVERY new index and trigger is on a table this migration creates (no trigger on an existing table)', newObjs.filter(o => o.type !== 'table').every(o => NEW.includes(o.tbl_name)),
    newObjs.filter(o => o.type !== 'table' && !NEW.includes(o.tbl_name)).map(o => o.name).join(','));
  check('M5 every new trigger is a refusal-only BEFORE trigger whose body is exactly SELECT RAISE(ABORT, …)', newObjs.filter(o => o.type === 'trigger')
    .every(o => /BEFORE (INSERT|UPDATE|DELETE)/.test(o.sql) && /BEGIN\s+SELECT\s+RAISE\(ABORT, '(?:[^']|'')*'\);\s*END$/.test(o.sql.trim())));
  check('M6 no foreign key from the new tables to artists, artworks or the single-artist tables', !newObjs.some(o => o.sql && /REFERENCES (artists|artworks|checkout_orders|artwork_sales|artwork_reservations)\b/.test(o.sql)));
  let again = true; try { for (const s of statements(MIG)) await db.prepare(s).run(); } catch { again = false; }
  check('M7 running it twice is harmless (seed and backfill are INSERT OR IGNORE)', again && JSON.stringify(await objects()) === JSON.stringify(after));
  const claims = (await db.prepare('SELECT artwork_id, holder_id, kind FROM artwork_claims ORDER BY artwork_id').all()).results;
  check('B1 backfill: the existing single-artist sale and LIVE hold now hold claims; the expired hold does not', JSON.stringify(claims) === JSON.stringify([{ artwork_id: 'warowan2', holder_id: 'oheld', kind: 'hold' }, { artwork_id: 'warowan3', holder_id: 'osold', kind: 'sale' }]), JSON.stringify(claims));
  check('B2 the migration does not record the claims-aware checkout (only checkout.js does)', (await db.prepare('SELECT COUNT(*) n FROM checkout_capabilities').first()).n === 0);
  let out = ''; try { out = execFileSync('python3', [ROOT + 'atlas-tools/release/studio/migration-check.py', MIG_PATH, createHash('sha256').update(readFileSync(MIG_PATH)).digest('hex'), NEW.join(','),
    'Nineteen new tables for the multi-artist basket and shared artwork claims; seeds TEST basket terms; backfills claims for existing single-artist holds and sales. No existing table changes.'], { encoding: 'utf8' }); } catch (e) { out = String(e.stdout || '') + String(e.message); }
  check('M8 [policy] the repository\'s migration-check.py ACCEPTS 0019 (class: needs the founder\'s approval, as every trigger does)', /MIGRATION CHECK OK/.test(out) && /MIGRATION CLASS: destructive/.test(out) && !/REFUSED/.test(out), out.split('\n').filter(l => /REFUSED|CLASS/.test(l)).join(' '));
}

/* ---------------------------------------------------------------- R · end to end */
console.log('— R end to end: hold, sale, settlement, transfer, refund, reversal within liability, failed refund, recredit');
{
  const D = mk(await freshDb()), env = { DB: D.db };
  await CO.markClaimsAware(env);   // the claims-aware single-artist checkout records itself
  await basket(D, 'b1', [{ line: 'l1', artist: 'arowan', work: 'w1', cents: 145000 }, { line: 'l2', artist: 'aalder', work: 'w2', cents: 210000, bp: 0 }], { open: false });
  check('R1 a basket (15% and a 0% line under terms permitting it) leaves draft only by being reconciled', await D.refused(`UPDATE basket_orders SET status = 'checkout_open' WHERE id = 'b1'`, [], /CHECK/) === true
    && await D.accepted(`UPDATE basket_orders SET status = 'checkout_open', reconciled_at = ? WHERE id = 'b1'`, t) === true);
  check('R2 the basket holds both originals (claim + reservation, one transaction each)', await basketHold(D, 'b1', 'w1') === true && await basketHold(D, 'b1', 'w2') === true);
  await pay(D, 'b1');
  check('R3 paid: each hold claim becomes the sale claim and the sale is recorded', await basketSell(D, 'b1', 'w1') === true && await basketSell(D, 'b1', 'w2') === true
    && (await D.q("SELECT COUNT(*) n FROM artwork_claims WHERE holder_id = 'b1' AND kind = 'sale'").first()).n === 2);
  await settle(D, 'b1');
  check('R4 an allocation released on payment, and transferred once', await release(D, 'b1', 'arowan') === true && (await trIns(D, { id: 'tr1', basket: 'b1', artist: 'arowan', amount: 145000 - 21750 })) === true);
  await trMade(D, 'tr1');
  await rfIns(D, { id: 'rf1', basket: 'b1', amount: 50000, comm: 7500 }); await partIns(D, { refund: 'rf1', ref: 'l1', artist: 'arowan', amount: 50000, comm: 7500 });
  await D.run("UPDATE basket_refunds SET status = 'succeeded', stripe_refund_id = 're_1' WHERE id = 'rf1'");
  check('R5 [N3] the reversal for that refund is accepted up to Rowan\'s debit (€425)…', (await rvIns(D, { id: 'v1', transfer: 'tr1', cause: 'rf1', amount: 42500 })) === true);
  await D.run("UPDATE basket_transfer_reversals SET status = 'created', stripe_reversal_id = 'trr_1' WHERE id = 'v1'");
  check('R6 [N3] …and not a cent more for the same refund', (await rvIns(D, { id: 'v1b', transfer: 'tr1', cause: 'rf1', attempt: 2, amount: 1 })) !== true);
  await D.run("UPDATE basket_refunds SET status = 'failed', failure = 'card closed' WHERE id = 'rf1'");
  check('R7 [L4] the refund fails after succeeding: the reversal is re-credited (recredit tied to that refund, with a reason)', (await trIns(D, { id: 'rc1', basket: 'b1', artist: 'arowan', kind: 'recredit', cause: 'rf1', amount: 42500 })) === true);
  check('R8 a recredit without a written reason is refused', (await trIns(D, { id: 'rc2', basket: 'b1', artist: 'arowan', kind: 'recredit', cause: 'rf1', attempt: 2, amount: 1, reason: 'short' })) !== true);
}
console.log('— R/N1 a reduction made before payout, restored after its refund failed, is paid exactly once by a restoration [N1]');
{
  const D = mk(await freshDb()), env = { DB: D.db };
  await CO.markClaimsAware(env);
  await basket(D, 'b2', [{ line: 'l1', artist: 'arowan', work: 'w1', cents: 100000 }]);
  await basketHold(D, 'b2', 'w1'); await pay(D, 'b2'); await basketSell(D, 'b2', 'w1'); await settle(D, 'b2');
  await rfIns(D, { id: 'r2', basket: 'b2', amount: 30000, comm: 4500 }); await partIns(D, { refund: 'r2', ref: 'l1', artist: 'arowan', amount: 30000, comm: 4500 });
  check('N1a a reduction (€255, Rowan\'s debit for that refund) is recorded with a written reason before payout', (await adj(D, { id: 'j1', basket: 'b2', artist: 'arowan', kind: 'pending_reduction', cause: 'r2', amount: 25500 })) === true);
  check('N1b an adjustment without a written reason is refused', (await adj(D, { id: 'j0', basket: 'b2', artist: 'arowan', kind: 'shortfall', cause: 'r2', amount: 1, reason: 'x' })) !== true);
  await release(D, 'b2', 'arowan');
  check('N1c the allocation is paid net of the reduction (€850 − €255 = €595)', (await trIns(D, { id: 't1', basket: 'b2', artist: 'arowan', amount: 59500 })) === true);
  await trMade(D, 't1');
  await D.run("UPDATE basket_refunds SET status = 'pending', stripe_refund_id = 're_2' WHERE id = 'r2'"); await D.run("UPDATE basket_refunds SET status = 'failed' WHERE id = 'r2'");
  check('N1d the refund fails: the reduction is restored (allowed only because it failed), with a reason', (await adj(D, { id: 'j2', basket: 'b2', artist: 'arowan', kind: 'pending_restored', cause: 'r2', amount: 25500 })) === true);
  check('N1e [N1] a second ALLOCATION transfer is still refused (one allocation per artist)', (await trIns(D, { id: 't2', basket: 'b2', artist: 'arowan', attempt: 2, amount: 25500 })) !== true);
  check('N1f [N1] a RESTORATION of exactly the restored €255, tied to that refund, is accepted', (await trIns(D, { id: 'rs1', basket: 'b2', artist: 'arowan', kind: 'restoration', cause: 'r2', amount: 25500 })) === true);
  await trMade(D, 'rs1');
  check('N1g [N1] a second restoration (any amount) is refused', (await trIns(D, { id: 'rs2', basket: 'b2', artist: 'arowan', kind: 'restoration', cause: 'r2', attempt: 2, amount: 1 })) !== true);
  const net = (await D.q("SELECT SUM(amount_cents) s FROM basket_transfers WHERE basket_id = 'b2' AND status = 'created'").first()).s;
  check('N1h [N1] the artist received exactly the €850 due, in total — underpaid never, overpaid never', net === 85000, net);
  await rfIns(D, { id: 'r3', basket: 'b2', amount: 1000, comm: 150 }); await partIns(D, { refund: 'r3', ref: 'l1', artist: 'arowan', amount: 1000, comm: 150 });
  check('N1i a restoration for a refund that has NOT failed is refused', (await trIns(D, { id: 'rs3', basket: 'b2', artist: 'arowan', kind: 'restoration', cause: 'r3', amount: 1 })) !== true);
  check('N1j a restoration without a written reason is refused', (await trIns(D, { id: 'rs4', basket: 'b2', artist: 'arowan', kind: 'restoration', cause: 'r2', attempt: 3, amount: 1, reason: '' })) !== true);
}
{
  // isolation of the restoration cap: the first restoration FAILED (so nothing is in flight) and a reversal for another
  // refund lowered the net paid, so neither the one-in-flight rule nor the net cap refuses an over-restoration
  const D = mk(await freshDb()); await CO.markClaimsAware({ DB: D.db });
  await basket(D, 'b3', [{ line: 'l1', artist: 'arowan', work: 'w1', cents: 100000 }]);
  await basketHold(D, 'b3', 'w1'); await pay(D, 'b3'); await basketSell(D, 'b3', 'w1'); await settle(D, 'b3');
  await rfIns(D, { id: 'r2', basket: 'b3', amount: 30000, comm: 4500 }); await partIns(D, { refund: 'r2', ref: 'l1', artist: 'arowan', amount: 30000, comm: 4500 });
  await adj(D, { id: 'j1', basket: 'b3', artist: 'arowan', kind: 'pending_reduction', cause: 'r2', amount: 25500 });
  await release(D, 'b3', 'arowan'); await trIns(D, { id: 't1', basket: 'b3', artist: 'arowan', amount: 59500 }); await trMade(D, 't1');
  await D.run("UPDATE basket_refunds SET status = 'failed' WHERE id = 'r2'");
  await adj(D, { id: 'j2', basket: 'b3', artist: 'arowan', kind: 'pending_restored', cause: 'r2', amount: 25500 });
  await trIns(D, { id: 'rs1', basket: 'b3', artist: 'arowan', kind: 'restoration', cause: 'r2', amount: 25500 });
  await D.run("UPDATE basket_transfers SET status = 'failed', failure = 'platform balance' WHERE id = 'rs1'");
  await rfIns(D, { id: 'r4', basket: 'b3', amount: 1000, comm: 150 }); await partIns(D, { refund: 'r4', ref: 'l1', artist: 'arowan', amount: 1000, comm: 150 });
  await rvIns(D, { id: 'v4', transfer: 't1', cause: 'r4', amount: 850 }); await D.run("UPDATE basket_transfer_reversals SET status = 'created', stripe_reversal_id = 'trr_4' WHERE id = 'v4'");
  const over = await trIns(D, { id: 'rs2', basket: 'b3', artist: 'arowan', kind: 'restoration', cause: 'r2', attempt: 2, amount: 25501 });
  check('N1k [N1] isolation: a retried restoration above what was restored is refused by the restoration cap itself', over !== true && /repays only a reduction restored/.test(over), over);
  check('N1l [N1] …and the exact restored amount is accepted on retry (new attempt, new key)', (await trIns(D, { id: 'rs3', basket: 'b3', artist: 'arowan', kind: 'restoration', cause: 'r2', attempt: 3, amount: 25500 })) === true);
}

/* ---------------------------------------------------------------- S · strict status machine (N2) */
console.log('— S strict basket status machine: no paid inserts, no reopening, no skipped reconciliation [N2]');
{
  const D = mk(await freshDb());
  check('S1 [N2] a basket cannot be created as paid', await D.refused(`INSERT INTO basket_orders (id, reference, status, payment_status, total_cents, commission_cents, plan_version, plan_sha256, decisions, artist_terms_doc, buyer_terms_doc, transfer_group, charge_id, created_by, created_at, updated_at) VALUES ('bp','PA-B-p','paid','paid',100,0,'v',?,?,'PA-BASKET-TEST-02','PA-BASKET-BPT-TEST-02','plotart-basket-bp','ch_x','s',?,?)`, [H, JSON.stringify(DEC), t, t], /only as an unpaid draft/) === true);
  await basket(D, 'bc', [{ line: 'l', artist: 'a1', work: 'w1', cents: 10000 }], { open: false });
  await D.run(`INSERT INTO basket_artist_allocations (basket_id, artist_id, account_id, gross_cents, commission_cents, delivery_cents, insurance_cents, transfer_before_fees_cents, release, updated_at) VALUES ('bc','a9','acct_a9',5000,0,0,0,5000,'on_payment',?)`, t);
  check('S2 an unreconciled draft (an extra €50 allocation) cannot open checkout', await D.refused(`UPDATE basket_orders SET status = 'checkout_open', reconciled_at = ? WHERE id = 'bc'`, [t], /does not reconcile/) === true);
  check('S3 draft → cancelled is allowed…', await D.accepted(`UPDATE basket_orders SET status = 'cancelled' WHERE id = 'bc'`) === true);
  check('S4 [N2] …but a cancelled basket never reopens (the review\'s bypass)', await D.refused(`UPDATE basket_orders SET status = 'checkout_open', reconciled_at = ? WHERE id = 'bc'`, [t], /not allowed|reconciled once/) === true);
  check('S5 [N2] …nor becomes paid, having never been reconciled or opened', await D.refused(`UPDATE basket_orders SET status = 'paid', payment_status = 'paid', charge_id = 'ch_bc' WHERE id = 'bc'`, [], /not allowed|CHECK/) === true);
  await basket(D, 'bo', [{ line: 'l', artist: 'a1', work: 'w2', cents: 10000 }]);
  await D.run(`UPDATE basket_orders SET checkout_session_id = 'cs_test_bo', status = 'cancelled' WHERE id = 'bo'`);
  check('S6 a basket cancelled AFTER its checkout opened may still record a late payment (money received is never lost)', await D.accepted(`UPDATE basket_orders SET status = 'paid', payment_status = 'paid', charge_id = 'ch_bo', paid_at = ? WHERE id = 'bo'`, t) === true);
  check('S7 [N2] payment status never moves backwards (paid → none, the review\'s D1)', await D.refused(`UPDATE basket_orders SET payment_status = 'none' WHERE id = 'bo'`, [], /not allowed/) === true);
  check('S8 [N2] paid → refunded → paid only when a refund actually failed', await D.accepted(`UPDATE basket_orders SET status = 'refunded', payment_status = 'refunded' WHERE id = 'bo'`) === true
    && await D.refused(`UPDATE basket_orders SET status = 'paid' WHERE id = 'bo'`, [], /only when a refund failed/) === true);
  check('S9 [N2] a closed basket is final', await D.accepted(`UPDATE basket_orders SET status = 'closed' WHERE id = 'bo'`) === true && await D.refused(`UPDATE basket_orders SET status = 'paid' WHERE id = 'bo'`, [], /not allowed/) === true);
  check('S10 [N2] reconciliation is written once', await D.refused(`UPDATE basket_orders SET reconciled_at = ? WHERE id = 'bo'`, [future], /reconciled once/) === true);
  check('S11 [N2] the dispute status never goes back to none', await D.accepted(`UPDATE basket_orders SET dispute_status = 'open' WHERE id = 'bo'`) === true && await D.refused(`UPDATE basket_orders SET dispute_status = 'none' WHERE id = 'bo'`, [], /not allowed/) === true);
  check('S12 [Low/D2] the buyer\'s email is fixed once checkout opens', await D.refused(`UPDATE basket_orders SET buyer_email = 'other@example.test' WHERE id = 'bo'`, [], /fixed once checkout opens/) === true);
}

/* ---------------------------------------------------------------- C · one original across both checkouts (H1, M1) */
console.log('— C one original across both checkouts: checkout.js\'s OWN statements and functions against basket claims');
{
  const D = mk(await freshDb()), env = { DB: D.db };
  await basket(D, 'b1', [{ line: 'h', artist: 'a1', work: 'wh', cents: 10000 }, { line: 's', artist: 'a1', work: 'ws', cents: 10000 }, { line: 'q', artist: 'a1', work: 'wq', cents: 10000 }]);
  check('C1 [deploy gate] no basket can claim anything before the claims-aware single-artist checkout has recorded itself', await basketHold(D, 'b1', 'wh') !== true);
  check('C2 checkout.js markClaimsAware() records the claims-aware checkout', (await CO.markClaimsAware(env)) === true && (await D.q('SELECT COUNT(*) n FROM checkout_capabilities').first()).n === 1);
  check('C3 a basket can now hold its own line', await basketHold(D, 'b1', 'wh') === true);
  await order(D, 'o1', 'wh'); const o1 = { id: 'o1', artwork_id: 'wh' };
  const r1 = await singleHold(env, o1);
  check('C4 [H1] the single checkout cannot hold a work a basket holds; the error is the kind checkout.js turns into "someone else is completing a purchase"', r1 !== 'held' && handled(r1), r1);
  check('C5 [H1] …and nothing was half-written (no reservation; the claim is still the basket\'s)', (await D.q("SELECT COUNT(*) n FROM artwork_reservations WHERE artwork_id = 'wh'").first()).n === 0 && (await D.q("SELECT holder_kind FROM artwork_claims WHERE artwork_id = 'wh'").first()).holder_kind === 'basket');
  const r2 = await singleSale(env, o1);
  check('C6 [H1] a late single-artist payment for a basket-held work is refused as a sale (checkout.js then flags it for refund)', r2 !== 'sold' && handled(r2), r2);
  await basketHold(D, 'b1', 'ws'); await pay(D, 'b1'); await basketSell(D, 'b1', 'ws');
  await order(D, 'o2', 'ws'); const o2 = { id: 'o2', artwork_id: 'ws' };
  check('C7 [H1] the single checkout can neither hold nor sell a work a basket has SOLD', handled(await singleHold(env, o2)) && handled(await singleSale(env, o2)));
  await order(D, 'o3', 'wfree'); const o3 = { id: 'o3', artwork_id: 'wfree' };
  check('C8 a free work is held normally by the single checkout (claim + reservation + audit assertion)', await singleHold(env, o3) === 'held'
    && (await D.q("SELECT holder_kind FROM artwork_claims WHERE artwork_id = 'wfree'").first()).holder_kind === 'single'
    && (await D.q("SELECT COUNT(*) n FROM artwork_claim_assertions WHERE artwork_id = 'wfree' AND holder_id = 'o3'").first()).n === 1);
  check('C9 re-opening its own checkout extends its own claim (no conflict with itself)', await singleHold(env, o3, '2099-06-01T00:00:00.000Z') === 'held');
  await basket(D, 'b2', [{ line: 'f', artist: 'a1', work: 'wfree', cents: 10000 }]);
  check('C10 [H1] a basket cannot claim a work the single checkout holds', await basketHold(D, 'b2', 'wfree') !== true);
  check('C11 the single checkout sells its held work: its hold claim becomes the sale claim', await singleSale(env, o3) === 'sold' && (await D.q("SELECT kind FROM artwork_claims WHERE artwork_id = 'wfree'").first()).kind === 'sale');
  check('C12 [H1] a sale claim cannot be released while the sale is active', await D.refused("DELETE FROM artwork_claims WHERE artwork_id = 'wfree'", [], /released only after the sale/) === true);
  await order(D, 'oq', 'wq', 'quoted', future);
  await basket(D, 'b4', [{ line: 'q', artist: 'a1', work: 'wq', cents: 10000 }]);   // an OPEN basket: only the quote can refuse it
  const c13 = await basketHold(D, 'b4', 'wq');
  check('C13 [M1] a basket cannot claim a work with an OPEN single-artist quote (refused for that reason)', c13 !== true && /quoted through the single-artist checkout/.test(c13), c13);
  // isolation: a single-artist sale written by pre-claims code has no claim; only the claims guard can see it
  await order(D, 'oorph', 'worph', 'paid'); await D.run("INSERT INTO artwork_sales (order_id, artwork_id, sold_at) VALUES ('oorph','worph',?)", t);
  await basket(D, 'b5', [{ line: 'o', artist: 'a1', work: 'worph', cents: 10000 }]);
  await ensureWork(D, 'worph'); await D.run(MARK_RESERVED[0], t, 'worph');
  const corph = await D.accepted("INSERT INTO artwork_claims (artwork_id, holder_kind, holder_id, kind, expires_at, claimed_at) VALUES ('worph','basket','b5','hold',?,?)", future, t);
  check('C13b [H1] a single-artist sale with NO claim (written before the claims-aware checkout) still blocks a basket claim', corph !== true && /sold, held or quoted through the single-artist/.test(corph), corph);
  // isolation: a basket claim without its reservation row; only the assertion stops the single checkout's no-op upsert
  await basket(D, 'b6', [{ line: 'n', artist: 'a1', work: 'wnr', cents: 10000 }]);
  await D.run(MARK_RESERVED[0], t, 'wnr');
  await D.run("INSERT INTO artwork_claims (artwork_id, holder_kind, holder_id, kind, expires_at, claimed_at) VALUES ('wnr','basket','b6','hold',?,?)", future, t);
  await order(D, 'onr', 'wnr');
  const cnr = await singleHold(env, { id: 'onr', artwork_id: 'wnr' });
  check('C13c [H1] the claim assertion alone stops the single checkout when a basket holds only the claim', cnr !== 'held' && /claimed through the other checkout|claimed by another holder/.test(cnr) && handled(cnr)
    && (await D.q("SELECT COUNT(*) n FROM artwork_reservations WHERE artwork_id = 'wnr'").first()).n === 0, cnr);
  await order(D, 'ox', 'wx', 'quoted', past);
  await basket(D, 'b3', [{ line: 'x', artist: 'a1', work: 'wx', cents: 10000 }]);
  check('C14 an EXPIRED single-artist quote no longer blocks a basket', await basketHold(D, 'b3', 'wx') === true);
  check('C15 [H1] a live basket hold\'s claim cannot be deleted while the hold exists', await D.refused("DELETE FROM artwork_claims WHERE artwork_id = 'wx'", [], /released only after the hold|checkout that is still open/) === true);
  check('C16 [H1] a claim never changes holder (no taking over by UPDATE)', await D.refused("UPDATE artwork_claims SET holder_kind = 'single', holder_id = 'o1' WHERE artwork_id = 'wx'", [], /never changes holder/) === true);
  check('C17 [L3] a basket cannot claim an artwork that is not one of its lines', await basketHold(D, 'b3', 'w-unrelated') !== true);
  const quoteBlock = await CO.markClaimsAware(env).then(() => D.q("SELECT 1 x FROM artwork_claims WHERE artwork_id = 'wh' AND holder_kind = 'basket' AND (kind = 'sale' OR julianday(expires_at) > julianday('now'))").first());
  check('C18 [Low] quoting a basket-held work meets the friendly 409 check in workAvailable (same query), not a raw database error', !!quoteBlock && /basket', 409\)/.test(readFileSync(HERE + 'src/checkout.js', 'utf8').replace(/\s+/g, ' ').match(/That artwork is held or sold through a PlotArt basket[^;]*/)?.[0] || ''));
  // expiry and takeover
  const E = mk(await freshDb()), envE = { DB: E.db }; await CO.markClaimsAware(envE);
  await basket(E, 'e1', [{ line: 'a', artist: 'a1', work: 'we', cents: 10000 }]); await basket(E, 'e2', [{ line: 'b', artist: 'a1', work: 'we', cents: 10000 }]);
  await E.run(MARK_RESERVED[0], t, 'we');
  await E.run("INSERT INTO artwork_claims (artwork_id, holder_kind, holder_id, kind, expires_at, claimed_at) VALUES ('we','basket','e1','hold',?,?)", past, t);
  check('C19 [H1] an EXPIRED basket hold cannot become a sale (no sale after an expired hold)', /lapsed hold no longer payable cannot become a sale/.test(String(await E.batch([["UPDATE artworks SET availability = 'sold' WHERE id = 'we'"], ["UPDATE artwork_claims SET kind = 'sale', expires_at = NULL WHERE artwork_id = 'we'"]]))));
  check('C20 another basket takes over an EXPIRED claim (the stale claim removed in the same transaction)', await basketHold(E, 'e2', 'we') === true && (await E.q("SELECT holder_id FROM artwork_claims WHERE artwork_id = 'we'").first()).holder_id === 'e2');
  check('C21 [H1] …but not an unexpired one', await basketHold(E, 'e1', 'we') !== true);
  await E.run("UPDATE basket_orders SET status = 'paid', payment_status = 'paid', checkout_session_id = 'cs_test_e1', charge_id = 'ch_e1', paid_at = ? WHERE id = 'e1'", t);
  check('C22 [H1] a basket sale needs its OWN sale claim (e1 is paid, but e2 holds the claim)', await E.refused("INSERT INTO basket_artwork_sales (basket_id, artwork_id, sold_at) VALUES ('e1','we',?)", [t], /own sale claim/) === true);
  check('C23 [H1] a basket hold row cannot outlast its claim, or move to another artwork', await E.refused("UPDATE basket_artwork_reservations SET expires_at = '2199-01-01T00:00:00.000Z' WHERE artwork_id = 'we'", [], /not beyond it/) === true
    && await E.refused("UPDATE basket_artwork_reservations SET artwork_id = 'wz' WHERE artwork_id = 'we'", [], /never moves|own live claim/) === true);
  // reinstating a basket sale after a failed refund
  const G = mk(await freshDb()), envG = { DB: G.db }; await CO.markClaimsAware(envG);
  await basket(G, 'g1', [{ line: 'a', artist: 'a1', work: 'wg', cents: 10000 }]); await basketHold(G, 'g1', 'wg'); await pay(G, 'g1'); await basketSell(G, 'g1', 'wg');
  await G.run("UPDATE basket_artwork_sales SET released_at = ?, released_reason = 'fully refunded' WHERE basket_id = 'g1'", t);
  await G.run("DELETE FROM artwork_claims WHERE artwork_id = 'wg'");
  await order(G, 'og', 'wg'); await singleHold(envG, { id: 'og', artwork_id: 'wg' });
  check('C24 [H1] a refunded basket sale cannot be reinstated while the single checkout holds the work', await G.refused("UPDATE basket_artwork_sales SET released_at = NULL, released_reason = NULL WHERE basket_id = 'g1'", [], /claimed elsewhere/) === true);
  check('C25 [H1] …and the basket cannot re-claim it either', await G.batch([["INSERT INTO artwork_claims (artwork_id, holder_kind, holder_id, kind, expires_at, claimed_at) VALUES ('wg','basket','g1','sale',NULL,?)", t]]) !== true);
  check('C26 exactly ONE active holder of that original across every table', (await G.q(`SELECT (SELECT COUNT(*) FROM artwork_claims WHERE artwork_id='wg') + (SELECT COUNT(*) FROM basket_artwork_sales WHERE artwork_id='wg' AND released_at IS NULL) + (SELECT COUNT(*) FROM artwork_sales WHERE artwork_id='wg' AND released_at IS NULL) AS n`).first()).n === 1);
}

console.log('— C/real the REAL checkout.js functions startCheckout and recordPaid use, against a basket hold [H1]');
{
  const D = mk(await freshDb()), env = { DB: D.db, ENVIRONMENT: 'local' }; await CO.markClaimsAware(env);
  await D.run("INSERT OR IGNORE INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('a1','a1','a1@example.test','A1',0,'active',?,?)", t, t);
  for (const w of ['wr', 'wf']) await D.run("INSERT OR IGNORE INTO artworks (id, artist_id, slug, title, year, medium, h_cm, w_cm, price_eur, availability, description, ord, ai_involvement, archived, created_at, updated_at) VALUES (?,'a1',?,?,2026,'painting',50,40,100,'available','d',1,'none',0,?,?)", w, w, w, t, t);
  // the basket holds 'wr' FIRST (a basket cannot claim a work with an open single-artist quote: C13); the single orders come after
  await basket(D, 'b1', [{ line: 'l', artist: 'a1', work: 'wr', cents: 10000 }]);
  check('C26b the basket holds wr', await basketHold(D, 'b1', 'wr') === true);
  for (const [id, w] of [['or', 'wr'], ['of', 'wf']]) await D.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, payment_status, quote_version, artwork_cents, delivery_cents, commission_cents, commission_bp, commission_basis, buyer_email, quote_expires_at, created_by, created_at, updated_at)
    VALUES (?,?,'a1',?,'PA-E-1','checkout_open','open',1,10000,0,1500,1500,'gallery_artist_agreement','b@example.test',?,'f',?,?)`, id, 'PA-O-' + id, w, future, t, t);
  const get = id => D.q('SELECT * FROM checkout_orders WHERE id = ?', id).first();
  check('C27 [H1] reserveOriginal (what startCheckout calls) refuses a basket-held work, writing nothing', (await CO.reserveOriginal(env, await get('or'), future, t)) === false
    && (await D.q("SELECT COUNT(*) n FROM artwork_reservations WHERE artwork_id = 'wr'").first()).n === 0);
  check('C28 reserveOriginal holds a free work with its claim', (await CO.reserveOriginal(env, await get('of'), future, t)) === true
    && (await D.q("SELECT holder_id, kind FROM artwork_claims WHERE artwork_id = 'wf'").first()).holder_id === 'of');
  const s = id => ({ id: 'cs_test_' + id, amount_total: 10000, currency: 'eur', payment_intent: 'pi_' + id });
  const paidR = await CO.recordPaid(env, await get('or'), s('or'), 'evt_or');
  check('C29 [H1] recordPaid for a basket-held work does NOT sell it: the payment is booked and the order flagged for refund', /^flagged: .*PlotArt basket.*refund or resolve with the buyer/.test(paidR)
    && (await D.q("SELECT COUNT(*) n FROM artwork_sales WHERE order_id = 'or'").first()).n === 0 && (await get('or')).status === 'refund_pending', paidR);
  const paidF = await CO.recordPaid(env, await get('of'), s('of'), 'evt_of');
  check('C30 recordPaid for its own held work sells it, converting its claim to the sale claim', (await D.q("SELECT COUNT(*) n FROM artwork_sales WHERE order_id = 'of' AND released_at IS NULL").first()).n === 1
    && (await D.q("SELECT kind FROM artwork_claims WHERE artwork_id = 'wf'").first()).kind === 'sale', paidF);
}

/* ---------------------------------------------------------------- N · reverseRefund under a basket conflict (N4) */
console.log('— N the single checkout\'s reverseRefund when a basket has taken the original meanwhile [N4]');
async function refundedOrder(D) {
  await D.run("INSERT OR IGNORE INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('a1','a1','a1@example.test','A1',0,'active',?,?)", t, t);
  await D.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, payment_status, artwork_cents, delivery_cents, amount_received_cents, commission_cents, buyer_email, created_by, created_at, updated_at)
    VALUES ('o1','PA-O-1','a1','w1','PA-E-1','refunded','refunded',10000,0,10000,1500,'b@example.test','f',?,?)`, t, t);
  await D.run("INSERT INTO artwork_sales (order_id, artwork_id, sold_at, released_at, released_reason) VALUES ('o1','w1',?,?,'fully refunded')", t, t);
  await D.run("INSERT INTO order_refunds (id, order_id, artwork_cents, delivery_cents, commission_refund_cents, reason, status, provider_refund_id, requested_by, created_at, updated_at) VALUES ('rr1','o1',10000,0,0,'buyer cancelled','succeeded','re_1','f',?,?)", t, t);
}
{
  const D = mk(await freshDb()), env = { DB: D.db, ENVIRONMENT: 'local', CHECKOUT_NOTIFY_EMAIL: 'founder@plotnua.ie' };
  await CO.markClaimsAware(env); await refundedOrder(D);
  const ledgerBefore = (await D.q("SELECT COUNT(*) n FROM order_ledger WHERE order_id = 'o1'").first()).n;
  await basket(D, 'b1', [{ line: 'l', artist: 'a1', work: 'w1', cents: 10000 }]); await basketHold(D, 'b1', 'w1');
  let threw = null; try { await CO.reverseRefund(env, await D.q("SELECT * FROM order_refunds WHERE id = 'rr1'").first(), { id: 're_1', status: 'failed', failure_reason: 'expired_or_canceled_card' }); } catch (e) { threw = e.message; }
  const o = await D.q("SELECT status, payment_status, needs_resolution FROM checkout_orders WHERE id = 'o1'").first();
  check('N1 [N4] reverseRefund completes; it no longer aborts part-way', threw === null, threw);
  check('N2 [N4] the payment history is kept: the refund is recorded as failed and its reversal is booked in the ledger', (await D.q("SELECT status FROM order_refunds WHERE id = 'rr1'").first()).status === 'failed'
    && (await D.q("SELECT COUNT(*) n FROM order_ledger WHERE order_id = 'o1'").first()).n > ledgerBefore && o.payment_status === 'paid');
  check('N3 [N4] the original is NOT reinstated over the basket\'s hold (the sale stays released; the basket keeps its claim)', (await D.q("SELECT released_at FROM artwork_sales WHERE order_id = 'o1'").first()).released_at !== null
    && (await D.q("SELECT holder_kind FROM artwork_claims WHERE artwork_id = 'w1'").first()).holder_kind === 'basket');
  check('N4 [N4] never silent: the order says the sale was not reinstated and the buyer is owed repayment', /sale not reinstated/.test(o.needs_resolution) && /buyer has NOT been repaid/.test(o.needs_resolution), o.needs_resolution);
  check('N5 [N4] …recorded as an order event', (await D.q("SELECT COUNT(*) n FROM order_events WHERE order_id = 'o1' AND action = 'sale_reinstatement_refused'").first()).n === 1);
  check('N6 [N4] …the buyer notice is stored', (await D.q("SELECT COUNT(*) n FROM order_messages WHERE order_id = 'o1' AND kind = 'buyer_refund_reversed'").first()).n === 1);
  check('N7 [N4] …and the founder alert says the sale could NOT be reinstated', (await D.q("SELECT COUNT(*) n FROM checkout_mail_sink WHERE order_id = 'o1' AND kind = 'refund_reversed' AND body LIKE '%could NOT be reinstated%'").first()).n >= 1);
  const F = mk(await freshDb()), envF = { DB: F.db, ENVIRONMENT: 'local', CHECKOUT_NOTIFY_EMAIL: 'founder@plotnua.ie' };
  await CO.markClaimsAware(envF); await refundedOrder(F);
  await CO.reverseRefund(envF, await F.q("SELECT * FROM order_refunds WHERE id = 'rr1'").first(), { id: 're_1', status: 'failed', failure_reason: 'expired_or_canceled_card' });
  check('N8 with no basket involved the sale IS reinstated as before, now holding its claim', (await F.q("SELECT released_at FROM artwork_sales WHERE order_id = 'o1'").first()).released_at === null
    && (await F.q("SELECT holder_id FROM artwork_claims WHERE artwork_id = 'w1'").first()).holder_id === 'o1' && !/not reinstated/.test((await F.q("SELECT needs_resolution n FROM checkout_orders").first()).n || ''));
  const P = mk(await freshDb(false)), envP = { DB: P.db, ENVIRONMENT: 'local', CHECKOUT_NOTIFY_EMAIL: 'founder@plotnua.ie' };
  await refundedOrder(P);
  await CO.reverseRefund(envP, await P.q("SELECT * FROM order_refunds WHERE id = 'rr1'").first(), { id: 're_1', status: 'failed', failure_reason: 'expired_or_canceled_card' });
  check('N9 without migration 0019, reverseRefund behaves exactly as before (sale reinstated, no claim tables touched)', (await P.q("SELECT released_at FROM artwork_sales WHERE order_id = 'o1'").first()).released_at === null);
}

/* ---------------------------------------------------------------- K · concurrency */
console.log('— K concurrent transactions on the same original or the same money (D1 serialises writes; exactly one wins)');
{
  const D = mk(await freshDb()), env = { DB: D.db }; await CO.markClaimsAware(env);
  await basket(D, 'b1', [{ line: 'a', artist: 'a1', work: 'wk', cents: 10000 }, { line: 'm', artist: 'a1', work: 'wm', cents: 10000 }]);
  await basket(D, 'b2', [{ line: 'b', artist: 'a1', work: 'wk', cents: 10000 }]);
  const won = rs => rs.filter(r => r === true || r === 'held').length;
  const k1 = await Promise.all([basketHold(D, 'b1', 'wk'), basketHold(D, 'b2', 'wk')]);
  check('K1 two baskets claiming the same work at once: exactly one', won(k1) === 1 && (await D.q("SELECT COUNT(*) n FROM basket_artwork_reservations WHERE artwork_id='wk'").first()).n === 1, JSON.stringify(k1));
  await order(D, 'om', 'wm');
  const k2 = await Promise.all([basketHold(D, 'b1', 'wm'), singleHold(env, { id: 'om', artwork_id: 'wm' })]);
  const holds = (await D.q(`SELECT (SELECT COUNT(*) FROM basket_artwork_reservations WHERE artwork_id='wm') + (SELECT COUNT(*) FROM artwork_reservations WHERE artwork_id='wm') AS n`).first()).n;
  check('K2 a basket and the single checkout claiming the same work at once: exactly one hold across both', won(k2) === 1 && holds === 1, JSON.stringify(k2));
  await order(D, 'p1', 'wp'); await order(D, 'p2', 'wp');
  const k3 = await Promise.all([singleHold(env, { id: 'p1', artwork_id: 'wp' }), singleHold(env, { id: 'p2', artwork_id: 'wp' })]);
  check('K3 two single-artist orders on the same work at once (with claims): exactly one', won(k3) === 1, JSON.stringify(k3));
  await pay(D, 'b1'); await settle(D, 'b1'); await release(D, 'b1', 'a1');
  const k4 = await Promise.all([1, 2].map(n => trIns(D, { id: 'kt' + n, basket: 'b1', artist: 'a1', attempt: n, amount: 17000 })));
  check('K4 two transfers to the same artist at once: exactly one', won(k4) === 1);
  const k5 = await Promise.all([1, 2].map(n => rfIns(D, { id: 'kr' + n, basket: 'b1', amount: 15000 })));
  check('K5 two refunds that together exceed the payment, at once: exactly one', won(k5) === 1);
}

/* ---------------------------------------------------------------- F · money */
console.log('— F transfers, reversals, refunds, disputes, adjustments: caps, liability per cause [N3], lifecycles, immutability');
{
  const D = mk(await freshDb()), env = { DB: D.db }; await CO.markClaimsAware(env);
  await basket(D, 'b1', [{ line: 'r', artist: 'rowan', work: 'w1', cents: 100000 }, { line: 'a', artist: 'alder', work: 'w2', cents: 100000 }], { decisions: DEC_ARTISTS });
  check('F1 no transfer before payment and settlement', (await trIns(D, { id: 'pre', basket: 'b1', artist: 'rowan', amount: 1 })) !== true);
  await pay(D, 'b1'); await settle(D, 'b1');
  check('F2 [Low/D3] release on payment is accepted once paid; a release time cannot be rewritten', await release(D, 'b1', 'rowan') === true && await D.refused(`UPDATE basket_artist_allocations SET release_ready_at = ? WHERE basket_id = 'b1' AND artist_id = 'rowan'`, [future], /written once/) === true);
  await release(D, 'b1', 'alder');
  check('F3 a transfer above what is due is refused', (await trIns(D, { id: 'big', basket: 'b1', artist: 'rowan', amount: 85001 })) !== true);
  check('F4 [H2] transfers to a wrong destination, from a wrong charge, or in live mode are refused', (await trIns(D, { id: 'd1', basket: 'b1', artist: 'rowan', amount: 1, dest: 'acct_evil' })) !== true
    && (await trIns(D, { id: 'd2', basket: 'b1', artist: 'rowan', amount: 1, charge: 'ch_other' })) !== true && (await trIns(D, { id: 'd3', basket: 'b1', artist: 'rowan', amount: 1, live: 1 })) !== true);
  await trIns(D, { id: 'tr', basket: 'b1', artist: 'rowan', amount: 85000 }); await trMade(D, 'tr');
  await trIns(D, { id: 'ta', basket: 'b1', artist: 'alder', amount: 85000 }); await trMade(D, 'ta');
  check('F5 [H2] a second full transfer to the same artist (new attempt and key) is refused', (await trIns(D, { id: 'tr2', basket: 'b1', artist: 'rowan', attempt: 2, amount: 85000 })) !== true);
  await rfIns(D, { id: 'rs', basket: 'b1', amount: 50, comm: 7 }); await partIns(D, { refund: 'rs', ref: 'r', artist: 'rowan', amount: 50, comm: 7 });
  check('F6 [N3] a 50-cent refund on Rowan\'s line cannot reverse €850 of Rowan\'s transfer (the review\'s A2: Rowan owes 43 cents for it)', (await rvIns(D, { id: 'v1', transfer: 'tr', cause: 'rs', amount: 85000 })) !== true);
  check('F7 [N3] …nor anything from Alder, who has no part in that refund (the review\'s A3)', (await rvIns(D, { id: 'v2', transfer: 'ta', cause: 'rs', amount: 1 })) !== true);
  check('F7b [H-4] no reversal while the refund has not SUCCEEDED (a cancelled refund would leave the artist out of pocket)', (await rvIns(D, { id: 'v0', transfer: 'tr', cause: 'rs', amount: 43 })) !== true);
  await D.run("UPDATE basket_refunds SET status = 'succeeded', stripe_refund_id = 're_rs' WHERE id = 'rs'");
  check('F8 [N3] Rowan\'s exact 43 cents is accepted once the refund succeeded', (await rvIns(D, { id: 'v3', transfer: 'tr', cause: 'rs', amount: 43 })) === true);
  check('F9 [N3] a reduction or shortfall for the same refund beyond Rowan\'s 43 cents is refused', (await adj(D, { id: 'j1', basket: 'b1', artist: 'rowan', kind: 'shortfall', cause: 'rs', amount: 1 })) !== true);
  await D.run(`INSERT INTO basket_disputes (id, basket_id, stripe_dispute_id, amount_cents, fee_cents, status, livemode, opened_at) VALUES ('d1','b1','du_1',20000,2000,'open',0,?)`, t);
  check('F10 [M4] no transfer and no refund while a dispute is open', (await trIns(D, { id: 'dsp', basket: 'b1', artist: 'rowan', kind: 'recredit', cause: 'rs', amount: 1 })) !== true && (await rfIns(D, { id: 'rdsp', basket: 'b1', amount: 1 })) !== true);
  await D.run(`UPDATE basket_disputes SET status = 'lost', closed_at = ?, attribution = '{"lines":[{"line_id":"r","artwork_cents":20000}]}' WHERE id = 'd1'`, t);
  check('F11 [N3] a dispute reversal before any per-artist share is recorded is refused', (await rvIns(D, { id: 'dv0', transfer: 'tr', cause_kind: 'dispute', cause: 'd1', amount: 1 })) !== true);
  check('F12 [N3] the per-artist share is recorded within the dispute\'s amount and fee', await D.accepted(`INSERT INTO basket_dispute_allocations (dispute_id, artist_id, loss_cents, fee_cents, recorded_by, recorded_at) VALUES ('d1','rowan',17000,2000,'founder',?)`, t) === true
    && await D.refused(`INSERT INTO basket_dispute_allocations (dispute_id, artist_id, loss_cents, fee_cents, recorded_by, recorded_at) VALUES ('d1','alder',3001,0,'founder',?)`, [t], /within the dispute|no more of a lost dispute/) === true);
  check('F13 [N3] Rowan\'s reversal for that dispute is capped at that share (€190)', (await rvIns(D, { id: 'dv1', transfer: 'tr', cause_kind: 'dispute', cause: 'd1', amount: 19001 })) !== true && (await rvIns(D, { id: 'dv2', transfer: 'tr', cause_kind: 'dispute', cause: 'd1', amount: 19000 })) === true);
  check('F14 [N3] Alder (no share of that dispute) cannot be reversed for it', (await rvIns(D, { id: 'dv3', transfer: 'ta', cause_kind: 'dispute', cause: 'd1', amount: 1 })) !== true);
  check('F15 a reversal is never deleted, and moves only requested → created or failed', await D.refused("DELETE FROM basket_transfer_reversals", [], /never deleted/) === true
    && await D.accepted("UPDATE basket_transfer_reversals SET status = 'failed' WHERE id = 'dv2'") === true && await D.refused("UPDATE basket_transfer_reversals SET status = 'created', stripe_reversal_id = 'trr_x' WHERE id = 'dv2'", [], /moves once/) === true);
  check('F16 [L4] after a failed reversal the shortfall is recorded against the SAME dispute, within Rowan\'s share', (await adj(D, { id: 'j2', basket: 'b1', artist: 'rowan', kind: 'shortfall', cause_kind: 'dispute', cause: 'd1', amount: 19000, reason: 'reversal failed: artist Stripe balance' })) === true
    && (await adj(D, { id: 'j3', basket: 'b1', artist: 'alder', kind: 'shortfall', cause_kind: 'dispute', cause: 'd1', amount: 1 })) !== true);
  check('F17 transfers are never deleted', await D.refused("DELETE FROM basket_transfers", [], /never deleted/) === true);
  await basket(D, 'b2', [{ line: 'l', artist: 'rowan', work: 'w9', cents: 100000 }]); await pay(D, 'b2'); await settle(D, 'b2');
  check('F18 a refund with a non-deterministic key is refused', await D.refused(`INSERT INTO basket_refunds (id, basket_id, idempotency_key, amount_cents, commission_returned_cents, status, reason, requested_by, livemode, created_at, updated_at) VALUES ('rk','b2','k',1,0,'requested','r','f',0,?,?)`, [t, t], /CHECK/) === true);
  await rfIns(D, { id: 'r1', basket: 'b2', amount: 60000, comm: 9000 });
  check('F19 a refund is sent only when its parts add up', await D.refused("UPDATE basket_refunds SET status = 'pending' WHERE id = 'r1'", [], /parts add up/) === true);
  check('F20 a line part above the line, above its commission, or for the wrong artist is refused', (await partIns(D, { refund: 'r1', ref: 'l', artist: 'rowan', amount: 100001 })) !== true
    && (await partIns(D, { refund: 'r1', ref: 'l', artist: 'rowan', amount: 60000, comm: 15001 })) !== true && (await partIns(D, { refund: 'r1', ref: 'l', artist: 'alder', amount: 60000, comm: 9000 })) !== true);
  await partIns(D, { refund: 'r1', ref: 'l', artist: 'rowan', amount: 60000, comm: 9000 });
  check('F21 [L4] a PENDING refund counts: a new refund beyond what remains is refused', await D.accepted("UPDATE basket_refunds SET status = 'pending', stripe_refund_id = 're_p' WHERE id = 'r1'") === true
    && (await rfIns(D, { id: 'r2', basket: 'b2', amount: 40001 })) !== true);
  check('F22 a refund\'s status never moves backwards and its amount never changes', await D.refused("UPDATE basket_refunds SET status = 'requested' WHERE id = 'r1'", [], /moves forward/) === true
    && await D.refused("UPDATE basket_refunds SET amount_cents = 1 WHERE id = 'r1'", [], /never change/) === true);
}

/* ---------------------------------------------------------------- T · terms and commission-free gate in the database (N6) */
console.log('— T approved basket terms and commission-free eligibility, enforced by the database [N6]');
{
  const D = mk(await freshDb());
  const ins = (id, docs, live = 0, decisions = DEC) => D.refused(`INSERT INTO basket_orders (id, reference, status, livemode, total_cents, commission_cents, plan_version, plan_sha256, decisions, artist_terms_doc, buyer_terms_doc, transfer_group, created_by, created_at, updated_at)
    VALUES (?,?,'draft',?,100,0,'v',?,?,?,?,?,'s',?,?)`, [id, 'PA-B-' + id, live, H, JSON.stringify(decisions), docs[0], docs[1], 'plotart-basket-' + id, t, t]);
  check('T1 [N6] a LIVE basket under made-up terms is refused (the review\'s E1: no live terms exist)', await ins('l1', ['ANYTHING', 'ANYTHING-BPT'], 1) === true);
  check('T2 [N6] the issued single-artist texts are refused, in any spelling (the review\'s E2)', await ins('l2', ['PA-PAY-2026-11', 'PA-BPT-2026-11']) === true && await ins('l3', ['pa-pay-2026-11', 'pa-bpt-2026-11']) === true);
  check('T3 [N6] TEST terms on a live basket are refused', await ins('l4', ['PA-BASKET-TEST-02', 'PA-BASKET-BPT-TEST-02'], 1) === true);
  check('T4 [N6] decisions the terms do not permit are refused (TEST-03 permits only on_payment); permitted ones accepted', await ins('l5', ['PA-BASKET-TEST-03', 'PA-BASKET-BPT-TEST-03'], 0, { ...DEC, transfer_timing: 'after_delivery' }) === true
    && await ins('l6', ['PA-BASKET-TEST-03', 'PA-BASKET-BPT-TEST-03']) === false);
  check('T5 [N6] basket terms cannot be added or changed at run time (only by a reviewed migration)', await D.refused(`INSERT INTO basket_terms (doc_id, buyer_terms_doc, livemode, commission_free_lines, permits, note) VALUES ('PA-BASKET-2099-01','PA-BASKET-BPT-2099-01',1,1,'{}','x')`, [], /reviewed migration/) === true
    && await D.refused(`UPDATE basket_terms SET commission_free_lines = 1 WHERE doc_id = 'PA-BASKET-TEST-01'`, [], /never change/) === true);
  await basket(D, 'f1', [{ line: 'g', artist: 'a1', work: 'w1', cents: 10000 }], { open: false, terms: ['PA-BASKET-TEST-01', 'PA-BASKET-BPT-TEST-01'] });
  check('T6 [N6][H3] a commission-free (Founding) line is refused under terms that do not permit it', await D.refused(`INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis, entitlement_evidence, enquiry_ref) VALUES ('f1','z','a1','w2','s-a1',10000,0,0,'founding_enquiry',?,'PA-E-z')`, [ev('a1', 'w2', 'PA-E-z')], /stay on direct payment/) === true);
  await basket(D, 'f2', [{ line: 'g', artist: 'a1', work: 'w3', cents: 10000 }], { open: false, decisions: { ...DEC, processing_fee_bearer: 'artists_pro_rata' } });
  check('T7 [N6] artists bear fees + a commission-free line without RECORDED consent is refused by the database; with it, accepted', await D.refused(`INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis, entitlement_evidence, enquiry_ref) VALUES ('f2','z','a1','w4','s-a1',10000,0,0,'founding_enquiry',?,'PA-E-z2')`, [ev('a1', 'w4', 'PA-E-z2')], /recorded consent/) === true
    && await D.accepted(`INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis, entitlement_evidence, enquiry_ref, processing_consent, processing_consent_at) VALUES ('f2','z','a1','w4','s-a1',10000,0,0,'founding_enquiry',?,'PA-E-z2',1,?)`, ev('a1', 'w4', 'PA-E-z2'), t) === true);
}

/* ---------------------------------------------------------------- W · remaining reproductions and lows */
console.log('— W the second review\'s remaining reproductions and low findings');
{
  const D = mk(await freshDb()); await CO.markClaimsAware({ DB: D.db });
  await basket(D, 'h1', [{ line: 'l', artist: 'a1', work: 'w1', cents: 10000 }]); await pay(D, 'h1');
  await D.run(`INSERT INTO basket_disputes (id, basket_id, stripe_dispute_id, amount_cents, status, livemode, opened_at) VALUES ('d1','h1','du_h1',10000,'open',0,?)`, t);
  check('W1 [Low/H1–H3] a second OPEN dispute beyond the total is refused (both could otherwise be lost)', await D.refused(`INSERT INTO basket_disputes (id, basket_id, stripe_dispute_id, amount_cents, status, livemode, opened_at) VALUES ('d2','h1','du_h2',10000,'open',0,?)`, [t], /exceeds what remains/) === true);
  await basket(D, 'h2', [{ line: 'l', artist: 'a1', work: 'w2', cents: 10000 }], { release: 'after_delivery', shipCharge: 500 });
  await pay(D, 'h2'); await settle(D, 'h2');
  check('W2 [Low/D3] release after delivery is refused until the shipment is recorded as delivered', await release(D, 'h2', 'a1') !== true);
  await D.run(`UPDATE basket_shipments SET fulfilment_status = 'delivered', fulfilled_at = ? WHERE basket_id = 'h2'`, t);
  check('W3 …and accepted once it is (never dated before the delivery)', await D.refused(`UPDATE basket_artist_allocations SET release_ready_at = ? WHERE basket_id = 'h2'`, [past], /not met/) === true && await release(D, 'h2', 'a1') === true);
  check('W4 fulfilment only moves forward; its time is written once', await D.refused(`UPDATE basket_shipments SET fulfilment_status = 'dispatched' WHERE basket_id = 'h2'`, [], /only moves forward/) === true
    && await D.refused(`UPDATE basket_shipments SET fulfilled_at = ? WHERE basket_id = 'h2'`, [future], /never change/) === true);
  check('W5 [M5] shipment charges, the settled fee and lines never change once recorded', await D.refused(`UPDATE basket_shipments SET delivery_cents = 1 WHERE basket_id = 'h2'`, [], /never change/) === true
    && await D.refused(`UPDATE basket_orders SET fee_cents = 1 WHERE id = 'h2'`, [], /recorded once/) === true && await D.refused(`UPDATE basket_lines SET title = 'x' WHERE basket_id = 'h2'`, [], /never changes/) === true);
  check('W6 lines cannot be added once the basket left draft', await D.refused(`INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis, entitlement_evidence, enquiry_ref) VALUES ('h2','late','a1','wl','s-a1',1000,1500,150,'g',?,'PA-E-late')`, [ev('a1', 'wl', 'PA-E-late')], /only while the basket is a draft/) === true);
  await basket(D, 'h3', [{ line: 'l', artist: 'a1', work: 'w5', cents: 10000 }], { open: false });
  check('W7 [M3] a line whose entitlement evidence is bound to another artwork is refused', await D.refused(`INSERT INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis, entitlement_evidence, enquiry_ref) VALUES ('h3','m','a1','wA','s-a1',1000,1500,150,'g',?,'PA-E-h3m')`, [ev('a1', 'wB', 'PA-E-h3m')], /CHECK/) === true);
  check('W8 a basket that left draft cannot be deleted', await D.refused(`DELETE FROM basket_orders WHERE id = 'h2'`, [], /kept with its records/) === true);
}

/* ---------------------------------------------------------------- L · linked purchases across both checkouts (M2) */
console.log('— L the EUR 10,000 linked-purchase check sees both checkouts');
{
  const withBaskets = await freshDb(), Lw = mk(withBaskets);
  await basket(Lw, 'bl', [{ line: 'l', artist: 'a1', work: 'w1', cents: 900000 }], { buyer: 'collector@example.test' });
  await pay(Lw, 'bl');
  const o = { id: 'o-new', buyer_email: 'Collector@Example.test', artwork_cents: 150000, delivery_cents: 0 };
  const lc = await CO.linkedCheck({ DB: withBaskets }, o);
  check('L1 [M2] checkout.js linkedCheck counts a paid basket: €9,000 basket + €1,500 single order is refused', lc.ok === false && lc.linked.includes('PA-B-bl') && lc.total_cents === 1050000, JSON.stringify(lc));
  const lc0 = await CO.linkedCheck({ DB: await freshDb(false) }, o);
  check('L2 without migration 0019 linkedCheck behaves exactly as before (no basket table, no error)', lc0.ok === true && lc0.total_cents === 150000 && lc0.linked.length === 0);
  await order(Lw, 'os', 'wz', 'paid', null, { email: 'collector@example.test', cents: 90000, payment: 'paid' });
  const bl = await B.basketLinkedCheck({ DB: withBaskets }, { buyer_email: 'collector@example.test', total_cents: 10000, exclude_basket_id: 'none' });   // €9,000 + €900 + €100 = exactly €10,000
  check('L3 [M2] basketLinkedCheck counts single-artist orders and baskets together: reaching exactly €10,000 is refused', bl.linked.includes('PA-O-os') && bl.linked.includes('PA-B-bl') && bl.total_cents === 1000000 && bl.ok === false, JSON.stringify(bl));
}

/* ---------------------------------------------------------------- Z · rollback */
console.log('— Z rollback');
{
  const base = await freshDb(false);
  const baseObjs = (await base.prepare("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE '_cf_%' AND name <> 'sqlite_sequence' ORDER BY type, name").all()).results;
  for (const s of statements(MIG)) await base.prepare(s).run();
  const rb = rollbackOf(MIG);
  check('Z1 the rollback names all nineteen tables', NEW.every(n => rb.includes(`DROP TABLE IF EXISTS ${n};`)));
  for (const s of statements(rb)) await base.prepare(s).run();
  const back = (await base.prepare("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE '_cf_%' AND name <> 'sqlite_sequence' ORDER BY type, name").all()).results;
  check('Z2 applying then rolling back (before any data) restores exactly the starting schema', JSON.stringify(back) === JSON.stringify(baseObjs));
  const Rb = mk(base);
  await order(Rb, 'o', 'w', 'paid');
  check('Z3 after rollback the single-artist checkout works normally and runs without claims', await Rb.accepted(CO.SALE_SQL, 'o', 'w', t) === true && (await CO.markClaimsAware({ DB: base })) === false);
}

/* ================================================================ third review (revision 4): reproductions for every finding */
const seedOrder = (D, id, work, status = 'checkout_open', qexp = future) => D.run(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, payment_status, quote_version, artwork_cents, delivery_cents, commission_cents, commission_bp, commission_basis, buyer_email, quote_expires_at, created_by, created_at, updated_at)
  VALUES (?,?,'a1',?,'PA-E-1',?,'open',1,10000,0,1500,1500,'gallery_artist_agreement','b@example.test',?,'f',?,?)`, id, 'PA-O-' + id, work, status, qexp, t, t);
const session = (D, order, status = 'open', exp = future) => D.run(`INSERT INTO checkout_sessions (id, order_id, quote_version, amount_total, application_fee_cents, status, expires_at, created_at, updated_at) VALUES (?,?,1,10000,1500,?,?,?,?)`, 'cs_test_' + order, order, status, exp, t, t);
const getO = (D, id) => D.q('SELECT * FROM checkout_orders WHERE id = ?', id).first();
const paidSession = id => ({ id: 'cs_test_' + id, amount_total: 10000, currency: 'eur', payment_intent: 'pi_' + id });
const lapse = (D, order) => D.batch([['UPDATE artwork_reservations SET expires_at = ? WHERE order_id = ?', past, order], ["UPDATE artwork_claims SET expires_at = ? WHERE holder_kind = 'single' AND holder_id = ?", past, order]]);

console.log('— H2 a lost dispute is carried only as the founder decided, and never beyond the artist\'s attributed share [H-2]');
{
  const D = mk(await freshDb()); await CO.markClaimsAware({ DB: D.db });
  const open = (b, id, amt, fee = 0) => D.run(`INSERT INTO basket_disputes (id, basket_id, stripe_dispute_id, amount_cents, fee_cents, status, livemode, opened_at) VALUES (?,?,?,?,?,'open',0,?)`, id, b, 'du_' + id, amt, fee, t);
  const lose = (id, att) => D.accepted(`UPDATE basket_disputes SET status = 'lost', closed_at = ?, attribution = ? WHERE id = ?`, t, att === null ? null : JSON.stringify(att), id);
  const share = (d, a, loss, fee = 0) => D.accepted(`INSERT INTO basket_dispute_allocations (dispute_id, artist_id, loss_cents, fee_cents, recorded_by, recorded_at) VALUES (?,?,?,?,'founder',?)`, d, a, loss, fee, t);
  await basket(D, 'p1', [{ line: 'r', artist: 'rowan', work: 'wp1', cents: 100000 }, { line: 'a', artist: 'alder', work: 'wp2', cents: 100000 }]);   // DEC: PlotArt carries loss and fee
  await pay(D, 'p1'); await settle(D, 'p1'); await open('p1', 'pd', 20000, 1500);
  check('H2a [H-2] a lost dispute with NO attribution is refused, whoever carries it', (await lose('pd', null)) !== true);
  check('H2b [H-2] an attribution that does not add up to the disputed amount, or names another basket\'s line, is refused', (await lose('pd', { lines: [{ line_id: 'r', artwork_cents: 19999 }] })) !== true
    && (await lose('pd', { lines: [{ line_id: 'zz', artwork_cents: 20000 }] })) !== true);
  check('H2c a correct attribution is accepted', (await lose('pd', { lines: [{ line_id: 'r', artwork_cents: 20000 }] })) === true);
  const loss = await share('pd', 'rowan', 1);
  check('H2d [H-2] the founder decided PlotArt carries the LOSS: an artist loss share of even 1 cent is refused', loss !== true && /on PlotArt, not the artist/.test(loss), loss);
  const fee = await share('pd', 'rowan', 0, 1);
  check('H2e [H-2] …and PlotArt carries the FEE: an artist fee share is refused', fee !== true && /on PlotArt, not the artist/.test(fee), fee);
  await basket(D, 'p2', [{ line: 'r', artist: 'rowan', work: 'wp3', cents: 100000 }, { line: 'a', artist: 'alder', work: 'wp4', cents: 100000 }], { decisions: { ...DEC, dispute_loss_bearer: 'artists_by_line' } });
  await pay(D, 'p2'); await settle(D, 'p2'); await open('p2', 'pm', 20000, 1500); await lose('pm', { lines: [{ line_id: 'r', artwork_cents: 20000 }] });
  check('H2f [H-2] mixed decision (artists the loss, PlotArt the fee): Rowan\'s loss is accepted but a fee share is refused', (await share('pm', 'rowan', 0, 1)) !== true && (await share('pm', 'rowan', 17000)) === true);
  await basket(D, 'p3', [{ line: 'r', artist: 'rowan', work: 'wp5', cents: 100000 }, { line: 'a', artist: 'alder', work: 'wp6', cents: 100000 }], { decisions: DEC_ARTISTS });
  await pay(D, 'p3'); await settle(D, 'p3'); await open('p3', 'pa', 30000, 1500);
  await lose('pa', { lines: [{ line_id: 'r', artwork_cents: 20000 }, { line_id: 'a', artwork_cents: 10000 }] });
  // the review's case: the old cap was only "within the dispute's amount and fee", so Alder could carry €300 of a dispute €100 of which was his
  const over = await share('pa', 'alder', 10001);
  check('H2g [H-2] an artist is never given more of the loss than the lines of theirs it was attributed to (Alder: €100, not €100.01)', over !== true && /no more of a lost dispute/.test(over), over);
  check('H2h [H-2] …while exactly their attributed share is accepted', (await share('pa', 'alder', 10000, 500)) === true && (await share('pa', 'rowan', 20000, 1000)) === true);
  await open('p3', 'pz', 1000); await lose('pz', { lines: [{ line_id: 'r', artwork_cents: 1000 }] });
  check('H2i [H-2] an artist with no attributed line of a lost dispute carries none of its fee either', (await share('pz', 'alder', 0, 1)) !== true);
}

console.log('— H3 a line or shipment is never recovered twice, through a dispute and a refund [H-3]');
{
  const D = mk(await freshDb()); await CO.markClaimsAware({ DB: D.db });
  await basket(D, 'q1', [{ line: 'r', artist: 'rowan', work: 'wq1', cents: 100000 }, { line: 'a', artist: 'alder', work: 'wq2', cents: 100000 }], { decisions: DEC_ARTISTS, shipCharge: 2000 });
  await pay(D, 'q1'); await settle(D, 'q1');
  await rfIns(D, { id: 'qr1', basket: 'q1', amount: 30000, comm: 4500 }); await partIns(D, { refund: 'qr1', ref: 'r', artist: 'rowan', amount: 30000, comm: 4500 });
  await D.run("UPDATE basket_refunds SET status = 'succeeded', stripe_refund_id = 're_q1' WHERE id = 'qr1'");
  await D.run(`INSERT INTO basket_disputes (id, basket_id, stripe_dispute_id, amount_cents, status, livemode, opened_at) VALUES ('qd1','q1','du_q1',80000,'open',0,?)`, t);
  const twice = await D.accepted(`UPDATE basket_disputes SET status = 'lost', closed_at = ?, attribution = '{"lines":[{"line_id":"r","artwork_cents":80000}]}' WHERE id = 'qd1'`, t);
  check('H3a [H-3] a dispute cannot recover €800 of Rowan\'s line when €300 of it was already refunded (only €700 remains)', twice !== true && /beyond what is left after refunds/.test(twice), twice);
  check('H3b …it can be attributed to what remains (€700 of the line and €100 of another)', await D.accepted(`UPDATE basket_disputes SET status = 'lost', closed_at = ?, attribution = '{"lines":[{"line_id":"r","artwork_cents":70000},{"line_id":"a","artwork_cents":10000}]}' WHERE id = 'qd1'`, t) === true);
  await rfIns(D, { id: 'qr2', basket: 'q1', amount: 1000 });
  const again = await partIns(D, { refund: 'qr2', ref: 'r', artist: 'rowan', amount: 1000, comm: 0 });
  check('H3c [H-3] the review\'s case: the same line can no longer be REFUNDED after a lost dispute recovered the rest of it', again !== true && /after refunds and lost disputes/.test(again), again);
  check('H3d …while the other line\'s remaining €900 can still be refunded', (await partIns(D, { refund: 'qr2', ref: 'a', artist: 'alder', amount: 1000, comm: 150 })) === true);
  await D.run(`INSERT INTO basket_disputes (id, basket_id, stripe_dispute_id, amount_cents, status, livemode, opened_at) VALUES ('qd2','q1','du_q2',1000,'open',0,?)`, t);
  check('H3e [H-3] a second lost dispute on a line that is already fully recovered is refused', await D.refused(`UPDATE basket_disputes SET status = 'lost', closed_at = ?, attribution = '{"lines":[{"line_id":"r","artwork_cents":1000}]}' WHERE id = 'qd2'`, [t], /beyond what is left/) === true);
  await D.run("UPDATE basket_disputes SET status = 'won', closed_at = ? WHERE id = 'qd2'", t);
  await D.run(`INSERT INTO basket_disputes (id, basket_id, stripe_dispute_id, amount_cents, status, livemode, opened_at) VALUES ('qd3','q1','du_q3',2000,'open',0,?)`, t);
  await D.run("UPDATE basket_disputes SET status = 'lost', closed_at = ?, attribution = '{\"shipments\":[{\"shipment_id\":\"s-rowan\",\"cents\":2000}]}' WHERE id = 'qd3'", t);
  await rfIns(D, { id: 'qr3', basket: 'q1', amount: 1 });
  check('H3f [H-3] shipments the same way: Rowan\'s €20 shipment, recovered by a lost dispute, cannot then be refunded', (await partIns(D, { refund: 'qr3', kind: 'shipment', ref: 's-rowan', artist: 'rowan', amount: 1 })) !== true);
}

console.log('— H4 a CANCELLED refund is undone like a failed one; reversals wait until a refund has succeeded [H-4]');
{
  const D = mk(await freshDb()); await CO.markClaimsAware({ DB: D.db });
  await basket(D, 'c1', [{ line: 'l', artist: 'rowan', work: 'wc1', cents: 100000 }]); await pay(D, 'c1'); await settle(D, 'c1');
  await rfIns(D, { id: 'cr', basket: 'c1', amount: 100000, comm: 15000 }); await partIns(D, { refund: 'cr', ref: 'l', artist: 'rowan', amount: 100000, comm: 15000 });
  check('H4a a reduction is recorded against the requested refund before payout', (await adj(D, { id: 'cj1', basket: 'c1', artist: 'rowan', kind: 'pending_reduction', cause: 'cr', amount: 85000 })) === true);
  await D.run("UPDATE basket_orders SET status = 'refunded', payment_status = 'refunded' WHERE id = 'c1'");
  await D.run("UPDATE basket_refunds SET status = 'pending', stripe_refund_id = 're_c1' WHERE id = 'cr'");
  check('H4b [H-4] no reversal while the refund is only PENDING (Stripe may still cancel it)', (await rvIns(D, { id: 'cv', transfer: 'none', cause: 'cr', amount: 1 })) !== true);
  await D.run("UPDATE basket_refunds SET status = 'canceled' WHERE id = 'cr'");
  check('H4c [H-4] the refund is CANCELLED: the reduction can be restored (before, only a FAILED refund allowed it — the trapped reduction)', (await adj(D, { id: 'cj2', basket: 'c1', artist: 'rowan', kind: 'pending_restored', cause: 'cr', amount: 85000 })) === true);
  check('H4d [H-4] …and the basket returns to paid (before, only after a FAILED refund)', await D.accepted("UPDATE basket_orders SET status = 'paid', payment_status = 'paid' WHERE id = 'c1'") === true);
  await release(D, 'c1', 'rowan');
  check('H4e [H-4] the artist is then paid in full (€850), once', (await trIns(D, { id: 'ct', basket: 'c1', artist: 'rowan', amount: 85000 })) === true && (await trIns(D, { id: 'ct2', basket: 'c1', artist: 'rowan', attempt: 2, amount: 1 })) !== true);
  // a refund cancelled after the allocation was paid: the restored reduction is repaid by a restoration tied to it
  await basket(D, 'c2', [{ line: 'l', artist: 'rowan', work: 'wc2', cents: 100000 }]); await pay(D, 'c2'); await settle(D, 'c2');
  await rfIns(D, { id: 'cr2', basket: 'c2', amount: 40000, comm: 6000 }); await partIns(D, { refund: 'cr2', ref: 'l', artist: 'rowan', amount: 40000, comm: 6000 });
  await adj(D, { id: 'ck1', basket: 'c2', artist: 'rowan', kind: 'pending_reduction', cause: 'cr2', amount: 34000 });
  await release(D, 'c2', 'rowan'); await trIns(D, { id: 'cu', basket: 'c2', artist: 'rowan', amount: 51000 }); await trMade(D, 'cu');
  await D.run("UPDATE basket_refunds SET status = 'canceled' WHERE id = 'cr2'");
  await adj(D, { id: 'ck2', basket: 'c2', artist: 'rowan', kind: 'pending_restored', cause: 'cr2', amount: 34000 });
  check('H4f [H-4] a restoration repays exactly the €340 restored for the cancelled refund, and no more', (await trIns(D, { id: 'cs1', basket: 'c2', artist: 'rowan', kind: 'restoration', cause: 'cr2', amount: 34001 })) !== true
    && (await trIns(D, { id: 'cs2', basket: 'c2', artist: 'rowan', kind: 'restoration', cause: 'cr2', amount: 34000 })) === true);
  await trMade(D, 'cs2');
  check('H4g the artist received exactly the €850 due in total', (await D.q("SELECT SUM(amount_cents) s FROM basket_transfers WHERE basket_id = 'c2' AND status = 'created'").first()).s === 85000);
  check('H4h a recredit for a cancelled refund repays only what was reversed for it (nothing was: refused)', (await trIns(D, { id: 'cq', basket: 'c2', artist: 'rowan', kind: 'recredit', cause: 'cr2', amount: 1 })) !== true);
}

console.log('— M1 INSERT OR REPLACE / upsert cannot overwrite or silently delete a protected row [M-1]');
{
  const D = mk(await freshDb()), env = { DB: D.db }; await CO.markClaimsAware(env);
  await basket(D, 'r1', [{ line: 'l', artist: 'rowan', work: 'wr1', cents: 100000 }]); await basketHold(D, 'r1', 'wr1'); await pay(D, 'r1'); await basketSell(D, 'r1', 'wr1'); await settle(D, 'r1');
  await release(D, 'r1', 'rowan'); await trIns(D, { id: 'rt', basket: 'r1', artist: 'rowan', amount: 85000 }); await trMade(D, 'rt');
  await rfIns(D, { id: 'rr', basket: 'r1', amount: 1000, comm: 150 });
  const count = async (tb, where = '1') => (await D.q(`SELECT COUNT(*) n FROM ${tb} WHERE ${where}`).first()).n;
  const attacks = [
    ['basket_transfers (same id, larger amount)', `INSERT OR REPLACE INTO basket_transfers (id, basket_id, artist_id, kind, cause_key, attempt, destination, idempotency_key, source_charge_id, amount_cents, livemode, status, created_at, updated_at) VALUES ('rt','r1','rowan','allocation','-',1,'acct_rowan','${B.keys.transfer({ basket_id: 'r1', artist_id: 'rowan', kind: 'allocation', cause_key: '-', attempt: 1 })}','ch_r1',85000,0,'requested',?,?)`, [t, t], 'basket_transfers', "id = 'rt' AND status = 'created'"],
    ['basket_refunds (same id)', `INSERT OR REPLACE INTO basket_refunds (id, basket_id, idempotency_key, amount_cents, commission_returned_cents, status, reason, requested_by, livemode, created_at, updated_at) VALUES ('rr','r1','${B.keys.refund({ basket_id: 'r1', refund_id: 'rr' })}',1,0,'requested','x','f',0,?,?)`, [t, t], 'basket_refunds', "id = 'rr' AND amount_cents = 1000"],
    ['basket_orders (same id, back to draft)', `INSERT OR REPLACE INTO basket_orders (id, reference, status, total_cents, commission_cents, plan_version, plan_sha256, decisions, artist_terms_doc, buyer_terms_doc, transfer_group, created_by, created_at, updated_at) VALUES ('r1','PA-B-r1','draft',1,0,'v',?,?,'PA-BASKET-TEST-02','PA-BASKET-BPT-TEST-02','plotart-basket-r1','x',?,?)`, [H, JSON.stringify(DEC), t, t], 'basket_orders', "id = 'r1' AND status = 'paid'"],
    ['basket_terms (broaden TEST-03 permits)', `INSERT OR REPLACE INTO basket_terms (doc_id, buyer_terms_doc, livemode, commission_free_lines, permits, note) SELECT doc_id, buyer_terms_doc, livemode, 1, permits, note FROM basket_terms WHERE doc_id = 'PA-BASKET-TEST-03'`, [], 'basket_terms', "doc_id = 'PA-BASKET-TEST-03' AND commission_free_lines = 0"],
    ['artwork_claims (another basket over a sold work)', `INSERT OR REPLACE INTO artwork_claims (artwork_id, holder_kind, holder_id, kind, expires_at, claimed_at) VALUES ('wr1','basket','other','hold',?,?)`, [future, t], 'artwork_claims', "artwork_id = 'wr1' AND holder_id = 'r1' AND kind = 'sale'"],
    ['artwork_claims (the holder turns its sale back into a hold)', `INSERT OR REPLACE INTO artwork_claims (artwork_id, holder_kind, holder_id, kind, expires_at, claimed_at) VALUES ('wr1','basket','r1','hold',?,?)`, [future, t], 'artwork_claims', "artwork_id = 'wr1' AND kind = 'sale'"],
    ['basket_artwork_sales (re-sell over an active sale)', `INSERT OR REPLACE INTO basket_artwork_sales (basket_id, artwork_id, sold_at) VALUES ('r1','wr1',?)`, [future], 'basket_artwork_sales', "basket_id = 'r1' AND sold_at = '" + t + "'"],
    ['basket_artist_allocations (same artist, larger due)', `INSERT OR REPLACE INTO basket_artist_allocations (basket_id, artist_id, account_id, gross_cents, commission_cents, delivery_cents, insurance_cents, transfer_before_fees_cents, release, updated_at) VALUES ('r1','rowan','acct_rowan',999999,0,0,0,999999,'on_payment',?)`, [t], 'basket_artist_allocations', "basket_id = 'r1' AND gross_cents = 100000"],
    ['basket_lines (same line, price changed)', `INSERT OR REPLACE INTO basket_lines (basket_id, line_id, artist_id, artwork_id, shipment_id, artwork_cents, commission_bp, commission_cents, commission_basis, entitlement_evidence, enquiry_ref) VALUES ('r1','l','rowan','wr1','s-rowan',1,0,0,'gallery_artist_agreement',?,'PA-E-r1l')`, [ev('rowan', 'wr1', 'PA-E-r1l')], 'basket_lines', "basket_id = 'r1' AND artwork_cents = 100000"],
    ['checkout_capabilities (version changed)', `INSERT OR REPLACE INTO checkout_capabilities (name, version, at) VALUES ('single_checkout_claims', 2, ?)`, [t], 'checkout_capabilities', 'version = 1'],
    ['basket_transfers (upsert changing the amount)', `INSERT INTO basket_transfers (id, basket_id, artist_id, kind, cause_key, attempt, destination, idempotency_key, source_charge_id, amount_cents, livemode, status, created_at, updated_at) VALUES ('rt','r1','rowan','allocation','-',1,'acct_rowan','k','ch_r1',1,0,'requested',?,?) ON CONFLICT(id) DO UPDATE SET amount_cents = 1`, [t, t], 'basket_transfers', "id = 'rt' AND amount_cents = 85000"],
  ];
  let n = 0;
  for (const [what, sql, args, tb, keep] of attacks) {
    const before = await count(tb), r = await D.accepted(sql, ...args);
    check(`M1.${++n} [M-1] REPLACE attack refused and nothing changed: ${what}`, r !== true && await count(tb) === before && await count(tb, keep) === 1, r);
  }
  const deletes = ['basket_transfers', 'basket_refunds', 'basket_orders', 'basket_lines', 'basket_artist_allocations', 'basket_artwork_sales', 'basket_terms', 'artwork_claims', 'basket_transfer_reversals', 'basket_disputes', 'basket_dispute_allocations', 'basket_allocation_adjustments', 'basket_refund_parts', 'basket_events', 'artwork_claim_assertions'];
  const kept = [];
  for (const tb of deletes) { const before = await count(tb); const r = await D.accepted(`DELETE FROM ${tb}`); if (before > 0 && (r === true || await count(tb) !== before)) kept.push(tb); }
  check('M1.d [M-1] DELETE attacks: no protected row of any financial, terms, claim or audit table can be deleted', kept.length === 0, kept.join(','));
  check('M1.e the identical seed of the TEST terms still re-runs harmlessly (INSERT OR IGNORE)', await D.accepted(`INSERT OR IGNORE INTO basket_terms (doc_id, buyer_terms_doc, livemode, commission_free_lines, permits, note) SELECT doc_id, buyer_terms_doc, livemode, commission_free_lines, permits, note FROM basket_terms WHERE doc_id = 'PA-BASKET-TEST-01'`) === true);
}

console.log('— M2 payment priority: a valid hold wins; an expired one never overrides a later valid one; no late payment double-sells [M-2]');
{
  const D = mk(await freshDb()), env = { DB: D.db, ENVIRONMENT: 'local' }; await CO.markClaimsAware(env);
  for (const w of ['wm1', 'wm2', 'wm3', 'wm4']) await ensureWork(D, w);
  // 1 · the hold lapsed but the buyer's checkout is still OPEN (they may have paid; Stripe's notification is late)
  await seedOrder(D, 'm1', 'wm1'); await CO.reserveOriginal(env, await getO(D, 'm1'), future, t); await session(D, 'm1'); await lapse(D, 'm1');
  await basket(D, 'mb1', [{ line: 'l', artist: 'a1', work: 'wm1', cents: 10000 }]);
  const take = await basketHold(D, 'mb1', 'wm1');
  check('M2a [M-2] a basket cannot take a lapsed hold whose checkout is still open (refused as "busy", like any held work)', take !== true && handled(take), take);
  await seedOrder(D, 'm1b', 'wm1');
  check('M2b [M-2] …nor can another single-artist order', (await CO.reserveOriginal(env, await getO(D, 'm1b'), future, t)) === false);
  check('M2c [M-2] the claim cannot be deleted from under the open checkout by anyone but its holder', await D.refused("DELETE FROM artwork_claims WHERE artwork_id = 'wm1'", [], /still open/) === true);
  await CO.sweep(env);
  check('M2d [M-2] the sweep keeps that hold while its checkout is open (it used to release it at the session\'s expiry time)', (await D.q("SELECT COUNT(*) n FROM artwork_reservations WHERE order_id = 'm1'").first()).n === 1
    && (await D.q("SELECT holder_id FROM artwork_claims WHERE artwork_id = 'wm1'").first()).holder_id === 'm1');
  const r1 = await CO.recordPaid(env, await getO(D, 'm1'), paidSession('m1'), 'evt_m1');
  check('M2e [M-2] the DELAYED webhook arrives: the buyer who paid in time gets the original (one sale, no refund)', (await D.q("SELECT COUNT(*) n FROM artwork_sales WHERE order_id = 'm1' AND released_at IS NULL").first()).n === 1
    && (await getO(D, 'm1')).status === 'paid', r1);
  // 2 · the checkout is over (Stripe said expired) and a basket has since taken the work: a late payment is refunded, never a second sale
  await seedOrder(D, 'm2', 'wm2', 'checkout_open', past); await CO.reserveOriginal(env, await getO(D, 'm2'), future, t); await session(D, 'm2'); await lapse(D, 'm2');
  await D.batch([["UPDATE checkout_sessions SET status = 'expired' WHERE order_id = 'm2'"], ['DELETE FROM artwork_reservations WHERE order_id = ?', 'm2'], [CO.CLAIM_SQL.releaseHold, 'm2']]);   // the expiry webhook (releaseHold)
  await basket(D, 'mb2', [{ line: 'l', artist: 'a1', work: 'wm2', cents: 10000 }]);
  check('M2f [M-2] once the checkout is over, a later valid basket hold takes the work (an expired hold does not override it)', await basketHold(D, 'mb2', 'wm2') === true);
  const r2 = await CO.recordPaid(env, await getO(D, 'm2'), paidSession('m2'), 'evt_m2');
  const o2 = await getO(D, 'm2');
  check('M2g [M-2] the late payment does NOT sell the work twice: no single-artist sale, the basket keeps its claim', (await D.q("SELECT COUNT(*) n FROM artwork_sales WHERE artwork_id = 'wm2'").first()).n === 0
    && (await D.q("SELECT holder_id FROM artwork_claims WHERE artwork_id = 'wm2'").first()).holder_id === 'mb2', r2);
  check('M2h [M-2] controlled refund: the order is refund_pending, the payment is booked, and the reason is ACCURATE (lapsed hold, now with a basket)', o2.status === 'refund_pending' && o2.payment_status === 'paid'
    && /after the hold had lapsed/.test(o2.needs_resolution) && /PlotArt basket/.test(o2.needs_resolution) && /refund or resolve/.test(o2.needs_resolution), o2.needs_resolution);
  // 3 · a lapsed hold with NO open checkout gives way at once
  await seedOrder(D, 'm3', 'wm3', 'checkout_open', past); await CO.reserveOriginal(env, await getO(D, 'm3'), future, t); await lapse(D, 'm3');
  await basket(D, 'mb3', [{ line: 'l', artist: 'a1', work: 'wm3', cents: 10000 }]);
  check('M2i a lapsed hold with no open checkout is taken over (stale claim and nothing payable)', await basketHold(D, 'mb3', 'wm3') === true);
  // 4 · the same priority for a hold written by the PRE-0019 checkout (a reservation without a claim)
  await seedOrder(D, 'm4', 'wm4'); await D.run('INSERT INTO artwork_reservations (artwork_id, order_id, quote_version, expires_at, created_at) VALUES (?,?,1,?,?)', 'wm4', 'm4', past, t); await session(D, 'm4');
  await D.run("UPDATE checkout_orders SET quote_expires_at = ? WHERE id = 'm4'", past);
  await basket(D, 'mb4', [{ line: 'l', artist: 'a1', work: 'wm4', cents: 10000 }]);
  check('M2j [M-2] a lapsed reservation of the OLD checkout whose session is open also keeps priority over a basket', await basketHold(D, 'mb4', 'wm4') !== true);
  // concurrency: the delayed webhook and a basket hold race on the same lapsed, still-open hold: exactly one outcome, never two sales
  const E = mk(await freshDb()), envE = { DB: E.db, ENVIRONMENT: 'local' }; await CO.markClaimsAware(envE); await ensureWork(E, 'wc');
  await seedOrder(E, 'mc', 'wc'); await CO.reserveOriginal(envE, await getO(E, 'mc'), future, t); await session(E, 'mc'); await lapse(E, 'mc');
  await basket(E, 'mbc', [{ line: 'l', artist: 'a1', work: 'wc', cents: 10000 }]);
  await Promise.all([CO.recordPaid(envE, await getO(E, 'mc'), paidSession('mc'), 'evt_mc').catch(e => e.message), basketHold(E, 'mbc', 'wc')]);
  const sales = (await E.q("SELECT (SELECT COUNT(*) FROM artwork_sales WHERE artwork_id = 'wc' AND released_at IS NULL) + (SELECT COUNT(*) FROM basket_artwork_sales WHERE artwork_id = 'wc' AND released_at IS NULL) + (SELECT COUNT(*) FROM basket_artwork_reservations WHERE artwork_id = 'wc') n").first()).n;
  check('M2k [M-2] concurrent delayed webhook and basket hold: exactly one holder or sale, and it is the buyer who paid', sales === 1 && (await E.q("SELECT COUNT(*) n FROM artwork_sales WHERE order_id = 'mc'").first()).n === 1);
}

console.log('— M3 interrupted operations: no stale claim survives a crash, an abandoned hold, or retention [M-3]');
{
  const D = mk(await freshDb()), env = { DB: D.db, ENVIRONMENT: 'local' }; await CO.markClaimsAware(env);
  for (const w of ['wx1', 'wx2', 'wx3']) await ensureWork(D, w);
  // the crash the review found: the sale released, then the process died before the claim was released (the old two-step)
  await seedOrder(D, 'x1', 'wx1'); await CO.reserveOriginal(env, await getO(D, 'x1'), future, t); await session(D, 'x1');
  await CO.recordPaid(env, await getO(D, 'x1'), paidSession('x1'), 'evt_x1');
  await D.run("UPDATE artwork_sales SET released_at = ?, released_reason = 'fully refunded' WHERE order_id = 'x1'", t);   // ← crash here
  await basket(D, 'xb', [{ line: 'l', artist: 'a1', work: 'wx1', cents: 10000 }]);
  check('M3a [M-3] reproduction: after the crash the orphaned sale claim blocks the work', await basketHold(D, 'xb', 'wx1') !== true);
  await CO.sweep(env);
  check('M3b [M-3] recovery: the sweep removes a sale claim whose sale is no longer active', (await D.q("SELECT COUNT(*) n FROM artwork_claims WHERE artwork_id = 'wx1'").first()).n === 0);
  check('M3c [M-3] recovery never permits a duplicate sale: an ACTIVE sale\'s claim is never swept', await (async () => {
    await seedOrder(D, 'x2', 'wx2'); await CO.reserveOriginal(env, await getO(D, 'x2'), future, t); await session(D, 'x2'); await CO.recordPaid(env, await getO(D, 'x2'), paidSession('x2'), 'evt_x2');
    await CO.sweep(env); return (await D.q("SELECT kind FROM artwork_claims WHERE artwork_id = 'wx2'").first())?.kind === 'sale'; })());
  const src = readFileSync(HERE + 'src/checkout.js', 'utf8');
  check('M3d [M-3] the fix: settleAfterRefund releases the sale and its claim in ONE batch (one transaction)', /env\.DB\.batch\(\[st\(env, "UPDATE artwork_sales SET released_at = \?, released_reason = 'fully refunded'[^\]]*CLAIM_SQL\.releaseSale/.test(src.replace(/\s+/g, ' ')));
  // retention: a closed order's records are purged after their period; its claim must go in the same batch
  await seedOrder(D, 'x3', 'wx3'); await CO.reserveOriginal(env, await getO(D, 'x3'), future, t); await session(D, 'x3'); await CO.recordPaid(env, await getO(D, 'x3'), paidSession('x3'), 'evt_x3');
  await D.run("UPDATE checkout_orders SET status = 'closed', updated_at = ?, retain_until = ? WHERE id = 'x3'", past, past);   // its retention period has ended
  const ret = await CO.retention(env);
  check('M3e [M-3] retention purges the order AND its claim together (no orphaned claim left behind)', ret.orders_deleted >= 1 && !(await getO(D, 'x3')) && (await D.q("SELECT COUNT(*) n FROM artwork_claims WHERE holder_id = 'x3'").first()).n === 0, JSON.stringify(ret));
  check('M3f …and the work stays unsellable by a basket, because the purge never resets the Studio "sold" mark', await (async () => { await basket(D, 'xb3', [{ line: 'l', artist: 'a1', work: 'wx3', cents: 10000 }]); return (await basketHold(D, 'xb3', 'wx3')) !== true; })());
  // an interrupted basket hold: the claim was never committed without its reservation (one transaction), so nothing to recover
  await basket(D, 'xb4', [{ line: 'l', artist: 'a1', work: 'wx4', cents: 10000 }]); await ensureWork(D, 'wx4');
  const half = await D.batch([[CO.CLAIM_SQL.dropStale, 'wx4'], [MARK_RESERVED[0], t, 'wx4'], ["INSERT INTO artwork_claims (artwork_id, holder_kind, holder_id, kind, expires_at, claimed_at) VALUES ('wx4','basket','xb4','hold',?,?)", future, t], ['SELECT RAISE(ABORT, \'simulated crash\')']]);
  check('M3g [M-3] a basket hold interrupted mid-transaction leaves nothing behind (no claim, no reservation, Studio mark unchanged)', half !== true && (await D.q("SELECT COUNT(*) n FROM artwork_claims WHERE artwork_id = 'wx4'").first()).n === 0
    && (await D.q("SELECT availability a FROM artworks WHERE id = 'wx4'").first()).a === 'available');
}

console.log('— O rollback and mixed versions: the PRE-PR checkout.js (git 4e66e39) against basket holds and sales [H-1]');
{
  const { mkdtempSync, writeFileSync, rmSync } = await import('node:fs'); const { tmpdir } = await import('node:os');
  const dir = mkdtempSync(tmpdir() + '/plotart-old-'); execFileSync('sh', ['-c', `git -C '${ROOT}' archive 4e66e39 worker/plotart-studio/src | tar -x -C '${dir}'`]);
  const oldPath = dir + '/worker/plotart-studio/src/checkout.js';
  writeFileSync(oldPath, readFileSync(oldPath, 'utf8') + '\nexport { workAvailable as __workAvailable, recordPaid as __recordPaid };\n');   // test-only access, in a throwaway copy
  const OLD = await import(oldPath);
  check('O0 the old code really is the pre-PR checkout (it knows nothing about claims)', !/artwork_claims/.test(readFileSync(oldPath, 'utf8')));
  const D = mk(await freshDb()), env = { DB: D.db, ENVIRONMENT: 'local' };
  await CO.markClaimsAware(env);   // the new checkout ran once (marker written), then the Worker was ROLLED BACK to the old code
  for (const w of ['wo1', 'wo2']) await ensureWork(D, w);
  await basket(D, 'ob1', [{ line: 'l', artist: 'a1', work: 'wo1', cents: 10000 }]); await basketHold(D, 'ob1', 'wo1');
  await basket(D, 'ob2', [{ line: 'l', artist: 'a1', work: 'wo2', cents: 10000 }]); await basketHold(D, 'ob2', 'wo2'); await pay(D, 'ob2'); await basketSell(D, 'ob2', 'wo2');
  const quote = w => OLD.__workAvailable(env, 'a1', w).then(() => 'available', e => e.message);
  check('O1 [H-1] the OLD checkout refuses to quote or open checkout for a basket-HELD original', /marked reserved/.test(await quote('wo1')));
  check('O2 [H-1] …and for a basket-SOLD original', /marked sold/.test(await quote('wo2')));
  // an order the old code had quoted BEFORE the basket existed, paid late after the basket took the work
  for (const [id, w] of [['oo1', 'wo1'], ['oo2', 'wo2']]) { await seedOrder(D, id, w); await session(D, id, 'expired'); }
  const p1 = await OLD.__recordPaid(env, await getO(D, 'oo1'), paidSession('oo1'), 'evt_oo1'), p2 = await OLD.__recordPaid(env, await getO(D, 'oo2'), paidSession('oo2'), 'evt_oo2');
  check('O3 [H-1] a payment recorded by the OLD code for a basket-held or basket-sold original is flagged for refund, NOT sold twice', /^flagged/.test(p1) && /^flagged/.test(p2)
    && (await D.q("SELECT COUNT(*) n FROM artwork_sales WHERE artwork_id IN ('wo1','wo2')").first()).n === 0, p1 + ' | ' + p2);
  // full rollback of the DATABASE too: the basket tables are gone, but the Studio marks they wrote remain
  for (const s of statements(rollbackOf(MIG))) await D.db.prepare(s).run();
  check('O4 [H-1] after the migration is rolled back as well, the old code still cannot sell either original (recovery: the founder resolves them by hand)', /marked reserved/.test(await quote('wo1')) && /marked sold/.test(await quote('wo2')));
  // the residual case, stated rather than hidden: if an artist marks a basket-held work "available" again while the OLD code runs, the old code can sell it
  const R = mk(await freshDb()), envR = { DB: R.db, ENVIRONMENT: 'local' }; await CO.markClaimsAware(envR);
  await seedPublished(R.db, { id: 'arowan', slug: 'rowan-test', email: 'rowan@example.test', name: 'Rowan Test', works: 1, number: 1 });   // a PUBLISHED available work
  await basket(R, 'rb', [{ line: 'l', artist: 'arowan', work: 'warowan1', cents: 10000 }]); await basketHold(R, 'rb', 'warowan1');
  const o5held = await OLD.__workAvailable(envR, 'arowan', 'warowan1').then(() => true, e => e.message);
  await R.run("UPDATE artworks SET availability = 'available' WHERE id = 'warowan1'");   // what the Studio availability control allows today
  const o5old = await OLD.__workAvailable(envR, 'arowan', 'warowan1').then(() => true, e => e.message), o5new = await CO.reserveOriginal(envR, { id: 'x', artwork_id: 'warowan1', quote_version: 1 }, future, t).catch(e => e.message);
  check('O5 [H-1 residual, documented] an artist re-marking a basket-held work "available" re-opens it to the OLD code (not to the new code)', /marked reserved/.test(o5held) && o5old === true && o5new === false, `held: ${o5held} old: ${o5old} new: ${o5new}`);
  const U = mk(await freshDb()); await CO.markClaimsAware({ DB: U.db }); await ensureWork(U, 'wu');
  await basket(U, 'ub', [{ line: 'l', artist: 'a1', work: 'wu', cents: 10000 }]);
  const unmarked = await U.batch([["INSERT INTO artwork_claims (artwork_id, holder_kind, holder_id, kind, expires_at, claimed_at) VALUES ('wu','basket','ub','hold',?,?)", future, t], ['INSERT INTO basket_artwork_reservations (artwork_id, basket_id, expires_at, created_at) VALUES (?,?,?,?)', 'wu', 'ub', future, t]]);
  check('O6 [H-1] the gate is mandatory: a basket hold that does not mark the artwork reserved in the same transaction is refused', unmarked !== true && /rollback safety/.test(unmarked), unmarked);
  await U.batch([[MARK_RESERVED[0], t, 'wu'], ["INSERT INTO artwork_claims (artwork_id, holder_kind, holder_id, kind, expires_at, claimed_at) VALUES ('wu','basket','ub','hold',?,?)", future, t], ['INSERT INTO basket_artwork_reservations (artwork_id, basket_id, expires_at, created_at) VALUES (?,?,?,?)', 'wu', 'ub', future, t]]);
  await pay(U, 'ub');
  const unsold = await U.batch([["UPDATE artwork_claims SET kind = 'sale', expires_at = NULL WHERE artwork_id = 'wu'"], ["INSERT INTO artwork_claim_assertions (artwork_id, holder_kind, holder_id, kind, purpose, at) VALUES ('wu','basket','ub','sale','paid',?)", t], ['INSERT INTO basket_artwork_sales (basket_id, artwork_id, sold_at) VALUES (?,?,?)', 'ub', 'wu', t]]);
  check('O7 [H-1] …and a basket sale that does not mark the artwork sold is refused', unsold !== true && /rollback safety/.test(unsold), unsold);
  rmSync(dir, { recursive: true, force: true });
}

for (const mf of mfs) await mf.dispose();
const failed = results.filter(x => !x).length;
console.log(`MIGRATION 0019 · ${results.length} checks, ${results.length - failed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
