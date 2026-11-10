// PROVE · migration 0007 (Art for Hire) on a database built with the CURRENT PRODUCTION schema (main) and realistic rows:
// two published Founding Artists (Leah-shaped at 01, PIGSY-shaped at 02), artworks, versions, gallery positions, agreement
// acceptances, relay enquiries and the enquiry log. Local only (Miniflare D1); nothing here touches Cloudflare.
//   node test/prove-migration-0007.mjs /path/to/schema-of-main.sql
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { statements, rollbackOf } from './sql.mjs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
if (!process.argv[2]) { console.log('usage: node test/prove-migration-0007.mjs SCHEMA_OF_MAIN.sql'); process.exit(2); }
const HERE = new URL('..', import.meta.url).pathname;
const MIG = readFileSync(HERE + 'migrations/0007_art_for_hire.sql', 'utf8');
const SCHEMA_NEW = readFileSync(HERE + 'schema.sql', 'utf8');
const NEW = ['artwork_hire', 'hire_enquiries', 'hire_participation_events', 'hire_terms', 'hire_terms_acceptances', 'hire_use_permissions'];
const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig6-test' } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
const refused = async (sql, ...b) => { try { await db.prepare(sql).bind(...b).run(); return false; } catch { return true; } };
await run(readFileSync(process.argv[2], 'utf8'));

console.log('PROVE · migration 0007 (Art for Hire) on the production schema');
const t = '2026-10-30T10:00:00.000Z', pub = '2026-11-05T17:05:00.000Z';
for (const [id, slug, name, n] of [['aleah', 'leah-like', 'Leah Like', 1], ['apigsy', 'pigsy-like', 'Pigsy Like', 2]]) {
  await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, founding_number, account_status, first_published_at, created_at, updated_at)
    VALUES (?,?,?,?,1,?,'active',?,?,?)`).bind(id, slug, `${slug}@example.test`, name, n, pub, t, pub).run();
  await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (?,?,0,NULL,?)').bind(n, id, pub).run();
  for (let i = 1; i <= 4; i++) await db.prepare("INSERT INTO artworks (id, artist_id, slug, title, ord, created_at, updated_at) VALUES (?,?,?,?,?,?,?)").bind(`${id}-w${i}`, id, `work-${i}`, `Work ${i}`, i, t, t).run();
  await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES (?,1,?,'s1',?)").bind(id, JSON.stringify({ works: [{ id: `${id}-w1` }] }), pub).run();
}
await db.prepare("INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (3, NULL, 1, 'private note', ?)").bind(t).run();
await db.prepare(`INSERT INTO enquiries (id, reference, artist_id, artwork_id, artwork_title, buyer_name, buyer_email, message, notice_version, created_at, status, sent_at, delete_after)
  VALUES ('e1','PA-E-261105-0A1B2C','aleah','aleah-w1','Work 1','Bea Buyer','bea@example.test','Is this still available?','PA-ENQ-2026-11','2026-11-05T18:00:00.000Z','sent','2026-11-05T18:00:01.000Z','2028-11-04T18:00:00.000Z')`).run();
await db.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at)
  VALUES ('l1','PA-E-261105-0A1B2C','aleah','aleah-w1','relay','2026-11-05T18:00:00.000Z',1,'2027-11-04','relay','2026-11-05T18:00:00.000Z')`).run();
await db.prepare("INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?, 'founder@example.test', 'founder', 'test', 'aleah', '{}')").bind(t).run();

const objects = async () => (await db.prepare("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
const tables = async () => (await objects()).filter(o => o.type === 'table').map(o => o.name);
const dump = async names => { const o = {}; for (const tb of names) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
const beforeObjects = await objects(), beforeTables = await tables(), before = await dump(beforeTables);
await run(MIG);
const afterObjects = await objects();
check('M1 every existing table and row is byte-for-byte unchanged (artists, artworks, versions, gallery_positions, agreement_documents, agreement_acceptances, enquiries, enquiry_log, audit …)',
  JSON.stringify(await dump(beforeTables)) === JSON.stringify(before));
check('M2 every existing table, index and trigger definition is unchanged (none altered, dropped or added to an existing table)',
  JSON.stringify(afterObjects.filter(o => !NEW.includes(o.tbl_name))) === JSON.stringify(beforeObjects));
const newTables = (await tables()).filter(x => !beforeTables.includes(x)).sort();
check('M3 it creates exactly the six approved tables', JSON.stringify(newTables) === JSON.stringify(NEW), newTables.join(','));
const newTriggers = afterObjects.filter(o => o.type === 'trigger' && NEW.includes(o.tbl_name)).map(o => o.name).sort();
check('M4 nine refusal-only guards, all on the four append-only tables (none on artwork_hire or hire_enquiries)',
  newTriggers.length === 9 && afterObjects.filter(o => o.type === 'trigger' && ['artwork_hire', 'hire_enquiries'].includes(o.tbl_name)).length === 0, newTriggers.join(','));
let rows = 0; for (const tb of NEW) rows += (await db.prepare(`SELECT COUNT(*) AS n FROM ${tb}`).first()).n;
check('M5 it installs no rows: no hire document, acceptance, offer, permission or enquiry exists after it runs', rows === 0);
const cols = (await db.prepare("SELECT name FROM pragma_table_info('artwork_hire')").all()).results.map(r => r.name);
check('M6 artwork_hire has no price, fee or value column (founder decisions 2 and 3)', !cols.some(c => /price|fee|value|amount|cost/i.test(c)), cols.join(','));
check('M7 the gallery order is unchanged: 01 Leah-shaped, 02 Pigsy-shaped, 03 reserved', JSON.stringify((await db.prepare('SELECT position, artist_id, reserved FROM gallery_positions ORDER BY position').all()).results)
  === JSON.stringify([{ position: 1, artist_id: 'aleah', reserved: 0 }, { position: 2, artist_id: 'apigsy', reserved: 0 }, { position: 3, artist_id: null, reserved: 1 }]));

// Acceptance guard: no acceptance is possible until a hire_terms text is installed (none is installed by this migration).
const H = 'a'.repeat(64), P = 'b'.repeat(64), now = new Date().toISOString();
const acc = (id, artist, doc, h, p, at) => db.prepare(`INSERT INTO hire_terms_acceptances (id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, statement, method, created_at)
  VALUES (?,?,?,?,?,?,'x@example.test','X','I accept','studio_checkbox',?)`).bind(id, artist, doc, h, p, at, at);
check('A1 with no hire_terms text installed, an acceptance is refused', await (async () => { try { await acc('h0', 'aleah', 'PA-AFH-TEST', H, P, now).run(); return false; } catch { return true; } })());
await db.prepare("INSERT INTO hire_terms (doc_id, title, html_sha256, pdf_sha256, effective_at, created_at) VALUES ('PA-AFH-TEST','Test terms',?,?, '2026-11-10T00:00:00Z', ?)").bind(H, P, now).run();
let ok = true; try { await acc('h1', 'aleah', 'PA-AFH-TEST', H, P, now).run(); } catch (e) { ok = false; }
check('A2 a correct acceptance (installed text, exact fingerprints, after it took effect, known artist) is recorded', ok);
const r = [];
for (const [id, a, h, p, at] of [['h2', 'aleah', 'c'.repeat(64), P, now], ['h3', 'aleah', H, P, '2026-11-01T00:00:00Z'], ['h4', 'nobody', H, P, now]]) {
  try { await acc(id, a, 'PA-AFH-TEST', h, p, at).run(); r.push(false); } catch { r.push(true); }
}
check('A3 refused: wrong fingerprint, dated before the text took effect, unknown artist', r.every(Boolean), JSON.stringify(r));
check('A4 append-only: a hire acceptance cannot be edited or deleted; a hire_terms text cannot be edited or removed',
  await refused("UPDATE hire_terms_acceptances SET display_name='Y' WHERE id='h1'") && await refused("DELETE FROM hire_terms_acceptances WHERE id='h1'")
  && await refused("UPDATE hire_terms SET title='Z'") && await refused("DELETE FROM hire_terms"));
await db.prepare("INSERT INTO hire_participation_events (id, artist_id, kind, at, actor, created_at) VALUES ('pe1','aleah','left',?, 'x@example.test', ?)").bind(now, now).run();
await db.prepare(`INSERT INTO hire_use_permissions (id, artist_id, use_kind, purpose, recipients, artwork_ids, answer, answered_at, method, recorded_by, created_at)
  VALUES ('up1','aleah','lookbook','Private lookbook for stagers','Three Dublin stagers','["aleah-w1"]','yes',?, 'email_logged_by_founder','founder@example.test',?)`).bind(now, now).run();
check('A5 append-only: leave/rejoin events and lookbook permissions cannot be edited or deleted while the artist is within retention',
  await refused("UPDATE hire_participation_events SET kind='rejoined'") && await refused("DELETE FROM hire_participation_events")
  && await refused("UPDATE hire_use_permissions SET answer='no'") && await refused("DELETE FROM hire_use_permissions"));

// artwork_hire: defaults and constraints
await db.prepare("INSERT INTO artwork_hire (artwork_id, artist_id, updated_at, created_at) VALUES ('aleah-w1','aleah',?,?)").bind(now, now).run();
const d = await db.prepare("SELECT offered, availability, screen_use, photo_use, collection, review_state FROM artwork_hire WHERE artwork_id='aleah-w1'").first();
check('H1 a new hire row defaults to OFF, no screen or photo use, "ask" collection, draft (nothing is offered by default)',
  d.offered === 0 && d.screen_use === 'none' && d.photo_use === 'none' && d.collection === 'ask' && d.review_state === 'draft', JSON.stringify(d));
check('H2 constraints refuse: approved without an approved snapshot; "from" without a date; delivery radius without delivery; an unknown artwork',
  await refused("UPDATE artwork_hire SET review_state='approved' WHERE artwork_id='aleah-w1'")
  && await refused("UPDATE artwork_hire SET availability='from' WHERE artwork_id='aleah-w1'")
  && await refused("UPDATE artwork_hire SET deliver_km=20 WHERE artwork_id='aleah-w1'")
  && await refused("INSERT INTO artwork_hire (artwork_id, artist_id, updated_at, created_at) VALUES ('no-such-work','aleah',?,?)", now, now));

// The Studio's EXISTING deletions keep working with hire rows present (no blocked foreign key)
await db.prepare("INSERT INTO artworks (id, artist_id, slug, title, ord, created_at, updated_at) VALUES ('aleah-draft','aleah','draft','Draft',9,?,?)").bind(t, t).run();
await db.prepare("INSERT INTO artwork_hire (artwork_id, artist_id, updated_at, created_at) VALUES ('aleah-draft','aleah',?,?)").bind(now, now).run();
ok = true; try { await db.prepare("DELETE FROM artworks WHERE id='aleah-draft' AND artist_id='aleah'").run(); } catch { ok = false; }
check('D1 deleting a draft artwork (existing Studio action) still works and removes its hire details with it',
  ok && !(await db.prepare("SELECT 1 FROM artwork_hire WHERE artwork_id='aleah-draft'").first()));
await db.prepare(`INSERT INTO enquiries (id, reference, artist_id, artwork_id, artwork_title, buyer_name, buyer_email, message, notice_version, created_at, status, delete_after)
  VALUES ('eh','PA-H-261110-ABCDEF','aleah','aleah-w1','Work 1','Hana Hirer','hana@example.test','Hire for a shoot','PA-ENQ-HIRE-TEST','2024-01-01T00:00:00.000Z','sent','2026-01-01T00:00:00.000Z')`).run();
await db.prepare("INSERT INTO hire_enquiries (enquiry_id, business, role, project_type, intended_use, delete_after, created_at) VALUES ('eh','Studio Co','Set decorator','film_tv','filming','2026-01-01T00:00:00.000Z',?)").bind(now).run();
ok = true; try { await db.prepare('DELETE FROM enquiries WHERE delete_after < ?').bind(now).run(); } catch { ok = false; }
check('D2 the existing 24-month enquiry deletion still works and removes the hire details with the enquiry',
  ok && !(await db.prepare("SELECT 1 FROM hire_enquiries WHERE enquiry_id='eh'").first()) && !!(await db.prepare("SELECT 1 FROM enquiries WHERE id='e1'").first()));
// Six-year deletion of an artist whose retention has ended, exactly as the existing deleteRecords batch runs it
await db.prepare("INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('aold','old','old@example.test','Old',1,'ended',?,?)").bind(t, t).run();
await db.prepare("INSERT INTO artworks (id, artist_id, slug, title, ord, created_at, updated_at) VALUES ('aold-w1','aold','w','W',1,?,?)").bind(t, t).run();
await db.prepare("INSERT INTO artwork_hire (artwork_id, artist_id, updated_at, created_at) VALUES ('aold-w1','aold',?,?)").bind(t, t).run();
await db.prepare("INSERT INTO hire_terms_acceptances (id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, statement, method, created_at) VALUES ('hold','aold','PA-AFH-TEST',?,?,?, 'o@example.test','Old','I accept','studio_checkbox',?)").bind(H, P, now, now).run();
await db.prepare("INSERT INTO record_retention (artist_id, ended_at, delete_after, recorded_by, recorded_at) VALUES ('aold','2019-01-01T00:00:00Z','2025-01-02T00:00:00Z','founder','2019-01-01T00:00:00Z')").run();
ok = true; let why = '';
try {
  await db.batch([db.prepare("DELETE FROM artworks WHERE artist_id = 'aold'"),
    ...['acceptance_corrections', 'agreement_acceptances', 'enquiry_log', 'enquiries', 'versions', 'publish_queue', 'gallery_positions', 'participation_events', 'record_retention'].map(x => db.prepare(`DELETE FROM ${x} WHERE artist_id = 'aold'`)),
    db.prepare("DELETE FROM artists WHERE id = 'aold' AND account_status = 'ended'"), db.prepare("DELETE FROM audit WHERE artist_id = 'aold'")]);
} catch (e) { ok = false; why = e.message; }
check('D3 the existing six-year deletion of an ended artist still succeeds with hire rows present (hire records are left for the Stage 3B-2 job, never blocking it)', ok && !(await db.prepare("SELECT 1 FROM artists WHERE id='aold'").first()), why);
const ret2 = await db.prepare("INSERT INTO record_retention (artist_id, ended_at, delete_after, recorded_by, recorded_at) VALUES ('apigsy','2019-01-01T00:00:00Z','2025-01-02T00:00:00Z','founder','2019-01-01T00:00:00Z')").run();
await db.prepare("INSERT INTO hire_use_permissions (id, artist_id, use_kind, purpose, recipients, artwork_ids, answer, answered_at, method, recorded_by, created_at) VALUES ('up2','apigsy','press','A press feature','One magazine','[]','no',?, 'studio','founder@example.test',?)").bind(now, now).run();
ok = true; try { await db.prepare("DELETE FROM hire_use_permissions WHERE artist_id='apigsy'").run(); } catch { ok = false; }
check('D4 once an artist\'s retention period has ended, their append-only hire records can be deleted (and only then)', ok && await refused("DELETE FROM hire_use_permissions WHERE artist_id='aleah'"));
await db.prepare("DELETE FROM record_retention WHERE artist_id='apigsy'").run();

// Idempotent, mirrored in schema.sql, and reversible
let again = true; try { await run(MIG); } catch { again = false; }
check('R1 running it a second time changes nothing and does not fail (IF NOT EXISTS throughout; no rows installed)', again && JSON.stringify((await objects())) === JSON.stringify(afterObjects));
const block = s => s.slice(s.indexOf('\n', s.indexOf('-- @@DDL-BEGIN')) + 1, s.indexOf('-- @@DDL-END') > -1 ? s.indexOf('-- @@DDL-END') : undefined).trim();
check('R2 schema.sql carries the migration\'s DDL verbatim for new installs and local tests', SCHEMA_NEW.includes(block(MIG)));
await run(rollbackOf(MIG));
check('R3 the documented rollback removes exactly the six new tables and leaves every existing object as it was', JSON.stringify(await objects()) === JSON.stringify(beforeObjects));

const fail = results.filter(x => !x).length;
console.log(`\nMIGRATION 0007 · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
