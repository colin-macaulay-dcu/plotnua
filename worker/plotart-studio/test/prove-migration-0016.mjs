// PROVE · migration 0016 (managed checkout pilot) on a database built with the schema BEFORE this change (the branch base),
// holding realistic records. New tables only; nothing existing changes; idempotent; documented rollback. Local only.
//   node test/prove-migration-0016.mjs /path/to/schema-before.sql
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { statements, rollbackOf } from './sql.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
if (!process.argv[2]) { console.log('usage: node test/prove-migration-0016.mjs SCHEMA_BEFORE.sql'); process.exit(2); }
const HERE = new URL('..', import.meta.url).pathname;
const MIG = readFileSync(HERE + 'migrations/0016_managed_checkout_pilot.sql', 'utf8');
const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig16-test' } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
await run(readFileSync(process.argv[2], 'utf8'));
console.log('PROVE · migration 0016 (managed checkout pilot) on the pre-change schema with existing records');
const t = '2026-11-16T19:00:00.000Z';
await seedPublished(db, { id: 'aleah', slug: 'leah-test', email: 'leah@example.test', name: 'Leah Test', works: 3, number: 1 });
await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (1, ?, 0, NULL, ?)').bind('aleah', t).run();
await db.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at, late_entry)
  VALUES ('l1','PA-E-261113-AAAAAA','aleah','waleah1','relay',?,1,'2027-11-04','relay',?,0)`).bind(t, t).run();
const objects = async () => (await db.prepare("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
const dump = async names => { const o = {}; for (const tb of names) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
const beforeObjects = await objects(), beforeTables = beforeObjects.filter(o => o.type === 'table').map(o => o.name), before = await dump(beforeTables);
check('M0 the base has no pilot tables', !beforeTables.includes('checkout_orders'));
await run(MIG);
const after = await objects();
const NEW = ['payment_terms', 'payment_pilot_events', 'payment_accounts', 'checkout_orders', 'artwork_reservations', 'artwork_sales', 'checkout_sessions', 'payment_events', 'order_ledger', 'order_refunds', 'order_fulfilment_events', 'order_events', 'checkout_holds', 'checkout_hold_events',
  'seller_profiles', 'quote_snapshots', 'order_messages', 'order_message_deliveries', 'checkout_mail_sink', 'checkout_owed', 'checkout_owed_payments', 'checkout_owed_payment_returns', 'checkout_founder_alert_reads', 'checkout_pause_events'];
check('M1 the migration creates exactly the twenty-four pilot tables', JSON.stringify(after.filter(o => o.type === 'table').map(o => o.name).filter(n => !beforeTables.includes(n)).sort()) === JSON.stringify([...NEW].sort()));
check('M2 every existing table, index and trigger definition is unchanged', beforeObjects.every(o => after.some(a => a.type === o.type && a.name === o.name && a.sql === o.sql)));
check('M3 every existing row is unchanged', JSON.stringify(await dump(beforeTables)) === JSON.stringify(before));
check('M4 every new trigger is a refusal-only BEFORE trigger on a new table', after.filter(o => o.type === 'trigger' && !beforeObjects.some(b => b.name === o.name))
  .every(o => NEW.includes(o.tbl_name) && /BEFORE (INSERT|UPDATE|DELETE)/.test(o.sql) && /SELECT RAISE\(ABORT/.test(o.sql) && !/\b(INSERT INTO|UPDATE \w+ SET|DELETE FROM)\b/.test(o.sql.replace(/BEFORE (INSERT|UPDATE|DELETE) ON/, ''))));
check('M5 no foreign key from the new tables to artists or artworks (participation deletion is never blocked)', !after.filter(o => NEW.includes(o.tbl_name) && o.sql).some(o => /REFERENCES (artists|artworks)/.test(o.sql)));
let again = true; try { await run(MIG); } catch { again = false; }
check('M6 running it twice is harmless', again);
await db.prepare("DELETE FROM artworks WHERE id = 'waleah3'").run().catch(() => {});
check('M7 existing deletion of an artwork still works with the pilot installed', !(await db.prepare("SELECT 1 FROM artworks WHERE id='waleah3'").first()));
await run(rollbackOf(MIG));
check('M8 the documented rollback removes exactly the pilot tables', JSON.stringify((await objects()).filter(o => o.type === 'table').map(o => o.name).sort()) === JSON.stringify([...beforeTables].sort()));
await mf.dispose();
const passed = results.filter(Boolean).length;
console.log(`\nMIGRATION 0016 · ${results.length} checks, ${passed} passed, ${results.length - passed} failed`);
process.exit(passed === results.length ? 0 : 1);
