// PROVE · migration 0008 (Art for Hire hire reports) on a database built with the CURRENT PRODUCTION schema (main, which
// already carries 0007) and realistic rows. Local only (Miniflare D1); nothing here touches Cloudflare.
//   node test/prove-migration-0008.mjs /path/to/schema-of-main.sql
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { statements, rollbackOf } from './sql.mjs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
if (!process.argv[2]) { console.log('usage: node test/prove-migration-0008.mjs SCHEMA_OF_MAIN.sql'); process.exit(2); }
const HERE = new URL('..', import.meta.url).pathname;
const MIG = readFileSync(HERE + 'migrations/0008_hire_reports.sql', 'utf8');
const SCHEMA_NEW = readFileSync(HERE + 'schema.sql', 'utf8');
const NEW = ['hire_report_records', 'hire_reports'];
const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig8-test' } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
const refused = async (sql, ...b) => { try { await db.prepare(sql).bind(...b).run(); return false; } catch { return true; } };
await run(readFileSync(process.argv[2], 'utf8'));

console.log('PROVE · migration 0008 (hire reports) on the production schema');
const t = '2026-10-30T10:00:00.000Z', pub = '2026-11-05T17:05:00.000Z', now = new Date().toISOString();
for (const [id, slug, name, n] of [['aleah', 'leah-like', 'Leah Like', 1], ['apigsy', 'pigsy-like', 'Pigsy Like', 2]]) {
  await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, founding_number, account_status, first_published_at, created_at, updated_at)
    VALUES (?,?,?,?,1,?,'active',?,?,?)`).bind(id, slug, `${slug}@example.test`, name, n, pub, t, pub).run();
  await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (?,?,0,NULL,?)').bind(n, id, pub).run();
  await db.prepare("INSERT INTO artworks (id, artist_id, slug, title, ord, created_at, updated_at) VALUES (?,?,?,?,1,?,?)").bind(`${id}-w1`, id, 'work-1', 'Work 1', t, t).run();
}
await db.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at)
  VALUES ('l1','PA-H-261105-0A1B2C','aleah','aleah-w1','relay','2026-11-05T18:00:00.000Z',1,'2027-11-04','relay','2026-11-05T18:00:00.000Z')`).run();
await db.prepare("INSERT INTO hire_terms (doc_id, title, html_sha256, pdf_sha256, effective_at, created_at) VALUES ('PA-AFH-TEST','Test',?,?,'2026-11-10T00:00:00Z',?)").bind('a'.repeat(64), 'b'.repeat(64), now).run();
await db.prepare("INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?, 'founder@example.test', 'founder', 'test', 'aleah', '{}')").bind(t).run();

const objects = async () => (await db.prepare("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
const tables = async () => (await objects()).filter(o => o.type === 'table').map(o => o.name);
const dump = async names => { const o = {}; for (const tb of names) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
const beforeObjects = await objects(), beforeTables = await tables(), before = await dump(beforeTables);
check('M0 the base is the production schema with Art for Hire (0007) already installed and no hire reports', beforeTables.includes('hire_terms') && !beforeTables.includes('hire_reports'));
await run(MIG);
const afterObjects = await objects();
check('M1 every existing table and row is byte-for-byte unchanged (artists, artworks, gallery_positions, enquiry_log, hire_terms, audit …)', JSON.stringify(await dump(beforeTables)) === JSON.stringify(before));
check('M2 every existing table, index and trigger definition is unchanged', JSON.stringify(afterObjects.filter(o => !NEW.includes(o.tbl_name))) === JSON.stringify(beforeObjects));
const newTables = (await tables()).filter(x => !beforeTables.includes(x)).sort();
check('M3 it creates exactly the two approved tables', JSON.stringify(newTables) === JSON.stringify(NEW), newTables.join(','));
const trig = afterObjects.filter(o => o.type === 'trigger' && NEW.includes(o.tbl_name)).map(o => o.name).sort();
check('M4 three refusal-only guards: reports cannot be edited, reports and records cannot be deleted before retention ends',
  JSON.stringify(trig) === JSON.stringify(['hire_report_records_no_delete', 'hire_reports_no_delete', 'hire_reports_no_update']), trig.join(','));
let rows = 0; for (const tb of NEW) rows += (await db.prepare(`SELECT COUNT(*) AS n FROM ${tb}`).first()).n;
check('M5 it installs no rows', rows === 0);
const cols = [...(await db.prepare("SELECT name FROM pragma_table_info('hire_reports')").all()).results, ...(await db.prepare("SELECT name FROM pragma_table_info('hire_report_records')").all()).results].map(r => r.name);
check('M6 no hirer detail can be stored: no name, email, business, phone or message column', !cols.some(c => /name|email|business|phone|message|hirer|buyer/i.test(c)), cols.join(','));
check('M7 the gallery order is unchanged', JSON.stringify((await db.prepare('SELECT position, artist_id FROM gallery_positions ORDER BY position').all()).results)
  === JSON.stringify([{ position: 1, artist_id: 'aleah' }, { position: 2, artist_id: 'apigsy' }]));

const ins = (id, o = {}) => {
  const v = { artist: 'apigsy', ref: 'PA-H-261105-0A1B2C', works: '["apigsy-w1"]', agreed: '2026-11-10', before: 0, start: '2026-11-20', end: '2026-11-30', fee: 50000, more: 0, founding: 0, basis: 'commission', rate: 1000, comm: 5000, corrects: null, ...o };
  return db.prepare(`INSERT INTO hire_reports (id, artist_id, reference, artwork_ids, hire_start, hire_end, agreed_on, starts_before_introduction, net_fee_cents, more_to_pay, introduced_at, founding, basis, rate_bp, commission_cents, terms_doc, corrects, reported_at, reported_by)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'PA-AFH-TEST',?,?,'x@example.test')`).bind(id, v.artist, v.ref, v.works, v.start, v.end, v.agreed, v.before, v.fee, v.more, '2026-11-05T18:00:00.000Z', v.founding, v.basis, v.rate, v.comm, v.corrects, now);
};
let ok = true; try { await ins('hr1').run(); await db.prepare("INSERT INTO hire_report_records (report_id, artist_id, updated_at, updated_by) VALUES ('hr1','apigsy',?, 'system')").bind(now).run(); } catch { ok = false; }
const rec = await db.prepare("SELECT invoice_status, payment_status FROM hire_report_records WHERE report_id='hr1'").first();
check('C1 a valid report and its record are stored; the record starts "not invoiced" and "unpaid"', ok && rec.invoice_status === 'not_invoiced' && rec.payment_status === 'unpaid');
const bad = [];
for (const [why, o] of [['commission on a founding-year report', { basis: 'founding_year', founding: 1, comm: 100 }], ['founding-year basis without the founding flag', { basis: 'founding_year', comm: 0 }],
  ['a rate other than 10%', { rate: 1500 }], ['a negative fee', { fee: -1, comm: 0, basis: 'no_fee' }], ['end before start', { end: '2026-11-01' }], ['an empty work list', { works: '[]' }], ['not JSON', { works: 'w1' }],
  ['an impossible date format', { start: '20/11/2026' }], ['no agreed date', { agreed: null }], ['an agreed date in another format', { agreed: '10/11/2026' }], ['a flag other than 0 or 1', { before: 2 }], ['an unknown basis', { basis: 'discount', comm: 0 }], ['a correction of a report that does not exist', { corrects: 'nope' }]]) {
  let r; try { await ins('hrb' + bad.length, o).run(); r = false; } catch { r = true; } bad.push([why, r]);
}
check('C2 the table itself refuses: ' + bad.map(b => b[0]).join('; '), bad.every(b => b[1]), JSON.stringify(bad));
check('C3 the founder record refuses an unknown status, a malformed date, a long note, and a record for a report that does not exist',
  await refused("UPDATE hire_report_records SET invoice_status='sent' WHERE report_id='hr1'") && await refused("UPDATE hire_report_records SET paid_on='12/11/2026' WHERE report_id='hr1'")
  && await refused("UPDATE hire_report_records SET note=? WHERE report_id='hr1'", 'x'.repeat(281)) && await refused("INSERT INTO hire_report_records (report_id, artist_id, updated_at, updated_by) VALUES ('nope','apigsy',?, 'x')", now));
check('C4 a report cannot be edited or deleted, and its record cannot be deleted, while the artist is within retention',
  await refused("UPDATE hire_reports SET net_fee_cents=1 WHERE id='hr1'") && await refused("DELETE FROM hire_reports WHERE id='hr1'") && await refused("DELETE FROM hire_report_records WHERE report_id='hr1'"));
ok = true; try { await db.prepare("UPDATE hire_report_records SET invoice_status='invoiced', invoice_no='PN-1', invoiced_on='2026-11-12' WHERE report_id='hr1'").run(); } catch { ok = false; }
check('C5 the founder\'s record can be updated (invoice and payment status are kept by hand)', ok);

// The existing six-year deletion, in the order deleteRecords uses (hire report tables before record_retention)
await db.prepare("INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('aold','old','old@example.test','Old',1,'ended',?,?)").bind(t, t).run();
await ins('hrold', { artist: 'aold' }).run();
await db.prepare("INSERT INTO hire_report_records (report_id, artist_id, updated_at, updated_by) VALUES ('hrold','aold',?, 'system')").bind(now).run();
await db.prepare("INSERT INTO record_retention (artist_id, ended_at, delete_after, recorded_by, recorded_at) VALUES ('aold','2019-01-01T00:00:00Z','2025-01-02T00:00:00Z','founder','2019-01-01T00:00:00Z')").run();
ok = true; let why = '';
try {
  await db.batch([...['acceptance_corrections', 'agreement_acceptances', 'enquiry_log', 'enquiries', 'versions', 'publish_queue', 'gallery_positions', 'participation_events',
    'hire_report_records', 'hire_reports', 'hire_use_permissions', 'hire_participation_events', 'hire_terms_acceptances', 'artwork_hire', 'record_retention'].map(x => db.prepare(`DELETE FROM ${x} WHERE artist_id = 'aold'`)),
    db.prepare("DELETE FROM artists WHERE id = 'aold' AND account_status = 'ended'"), db.prepare("DELETE FROM audit WHERE artist_id = 'aold'")]);
} catch (e) { ok = false; why = e.message; }
check('D1 the existing six-year deletion of an ended artist succeeds with hire reports present (they go before record_retention)',
  ok && !(await db.prepare("SELECT 1 FROM artists WHERE id='aold'").first()) && !(await db.prepare("SELECT 1 FROM hire_reports WHERE artist_id='aold'").first()), why);

let again = true; try { await run(MIG); } catch { again = false; }
const objsNow = await objects();
check('R1 running it a second time changes nothing and does not fail', again && JSON.stringify(objsNow) === JSON.stringify(afterObjects));
const block = s => s.slice(s.indexOf('\n', s.indexOf('-- @@DDL-BEGIN')) + 1, s.indexOf('-- @@DDL-END')).trim();
check('R2 schema.sql carries the migration\'s DDL verbatim for new installs and local tests', SCHEMA_NEW.includes(block(MIG)));
await run(rollbackOf(MIG));
check('R3 the documented rollback removes exactly the two new tables and leaves every existing object as it was', JSON.stringify(await objects()) === JSON.stringify(beforeObjects));
await mf.dispose();
const fail = results.filter(x => !x).length;
console.log(`\nMIGRATION 0008 · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
