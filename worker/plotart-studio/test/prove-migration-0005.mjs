// PROVE · migration 0005 (agreement records and the enquiry log) on a database built with the CURRENT PRODUCTION schema
// and realistic rows: an existing published artist with the earlier licence label (Leah-shaped), an invited artist
// (Nick-shaped), relay enquiries, Idea Board and noticeboard rows. Local only; nothing here touches Cloudflare.
//   node test/prove-migration-0005.mjs /path/to/schema-of-main.sql
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { statements } from './sql.mjs';
import { foundingYear } from '../src/founding.js';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
if (!process.argv[2]) { console.log('usage: node test/prove-migration-0005.mjs SCHEMA_OF_MAIN.sql'); process.exit(2); }
const HERE = new URL('..', import.meta.url).pathname;
const FILE = HERE + 'migrations/0005_agreements_and_enquiry_log.sql';
const MIG = readFileSync(FILE, 'utf8'), FP = JSON.parse(readFileSync(HERE + 'agreements/issued/fingerprints.json', 'utf8')).documents;
const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig5-test' } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
await run(readFileSync(process.argv[2], 'utf8'));

console.log('PROVE · migration 0005 on the production schema');
const t = '2026-10-30T10:00:00.000Z', pub = '2026-11-05T17:05:00.000Z';
await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, founding_number, account_status, licence_version, licence_accepted_at, first_published_at, created_at, updated_at)
  VALUES ('aleah','leah-like','leah@example.test','Leah Like',1,1,'active','PA-GPIL-2026-10-29','2026-11-05T16:40:12.345Z',?,?,?)`).bind(pub, t, pub).run();
await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('anick','nick-like','nick@example.test','Nick Like',1,'invited',?,?)`).bind(t, t).run();
for (let i = 1; i <= 11; i++) await db.prepare("INSERT INTO artworks (id, artist_id, slug, title, ord, created_at, updated_at) VALUES (?, 'aleah', ?, ?, ?, ?, ?)").bind(`w${i}`, `work-${i}`, `Work ${i}`, i, t, t).run();
await db.prepare(`INSERT INTO enquiries (id, reference, artist_id, artwork_id, artwork_title, buyer_name, buyer_email, message, notice_version, created_at, status, sent_at, delete_after)
  VALUES ('e1','PA-E-261105-0A1B2C','aleah','w3','Work 3','Bea Buyer','bea@example.test','Is this still available?','PA-ENQ-2026-10-29','2026-11-05T18:00:00.000Z','sent','2026-11-05T18:00:01.000Z','2028-11-04T18:00:00.000Z')`).run();
await db.prepare(`INSERT INTO enquiries (id, reference, artist_id, artwork_id, artwork_title, buyer_name, buyer_email, message, notice_version, created_at, status, delete_after)
  VALUES ('e2','PA-E-261105-3D4E5F','aleah',NULL,NULL,'Cal Buyer','cal@example.test','A general question.','PA-ENQ-2026-10-29','2026-11-05T21:00:00.000Z','received','2028-11-04T21:00:00.000Z')`).run();
await db.prepare("INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?, 'founder@example.test', 'founder', 'test', 'aleah', '{}')").bind(t).run();
try { await db.prepare("INSERT INTO ideas (id, ref, text, status, created_at) VALUES ('i1','PN-I-1','A synthetic test idea for the board','received',?)").bind(t).run(); } catch { /* table shape differs: not needed */ }

const objects = async () => (await db.prepare("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
const tables = async () => (await objects()).filter(o => o.type === 'table').map(o => o.name);
const dump = async names => { const o = {}; for (const tb of names) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
const beforeObjects = await objects(), beforeTables = await tables(), before = await dump(beforeTables);
const startedAt = new Date(Date.now() - 1000).toISOString();
await run(MIG);
const after = await dump(beforeTables);
check('M1 every existing table and row is byte-for-byte unchanged (artists, artworks, enquiries, audit, …)', JSON.stringify(after) === JSON.stringify(before));
const newTables = (await tables()).filter(x => !beforeTables.includes(x)).sort();
check('M2 it creates exactly four new tables', JSON.stringify(newTables) === JSON.stringify(['agreement_acceptances', 'agreement_documents', 'enquiry_log', 'record_retention']), newTables.join(','));
const docs = (await db.prepare('SELECT * FROM agreement_documents ORDER BY doc_id').all()).results;
check('M3 three documents: the two new texts with the exact fingerprints of the files Studio serves, effective from the moment it runs; the earlier licence as label only',
  docs.length === 3 && ['PA-FAA-2026-11', 'PA-GPIL-2026-11'].every(id => { const d = docs.find(x => x.doc_id === id); return d.text_status === 'fixed' && d.html_sha256 === FP[id].html_sha256 && d.pdf_sha256 === FP[id].pdf_sha256 && d.effective_at >= startedAt.slice(0, 19); })
  && docs.find(x => x.doc_id === 'PA-GPIL-2026-10-29').text_status === 'label_only' && docs.find(x => x.doc_id === 'PA-GPIL-2026-10-29').html_sha256 === null, JSON.stringify(docs));
const acc = (await db.prepare('SELECT * FROM agreement_acceptances').all()).results;
check('M4 exactly one acceptance is carried over (the existing licence acceptance), copied exactly: version and time as recorded, label only, no text, no fingerprint, no email, no legal name',
  acc.length === 1 && acc[0].artist_id === 'aleah' && acc[0].doc_id === 'PA-GPIL-2026-10-29' && acc[0].accepted_at === '2026-11-05T16:40:12.345Z' && acc[0].method === 'migrated_from_artists_table'
  && acc[0].doc_sha256 === null && acc[0].pdf_sha256 === null && acc[0].account_email === null && acc[0].legal_name === null && acc[0].display_name === 'Leah Like', JSON.stringify(acc));
check('F  the migration cannot create an agreement acceptance retrospectively: no row for PA-FAA-2026-11 or PA-GPIL-2026-11 exists for anyone, and the invited artist has none',
  !acc.some(a => a.doc_id !== 'PA-GPIL-2026-10-29') && !acc.some(a => a.artist_id === 'anick'));
const tries = [];
for (const [why, sql] of [
  ['migrated row naming the agreement', "INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, accepted_at, display_name, method, statement, created_at) VALUES ('x','x','anick','PA-FAA-2026-11','2026-11-01T00:00:00Z','Nick Like','migrated_from_artists_table','s','2026-11-06T00:00:00Z')"],
  ['migrated row naming the new licence', "INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, accepted_at, display_name, method, statement, created_at) VALUES ('x','x','aleah','PA-GPIL-2026-11','2026-11-01T00:00:00Z','Leah Like','migrated_from_artists_table','s','2026-11-06T00:00:00Z')"],
  ['Studio row dated before the text took effect', `INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, method, statement, created_at) VALUES ('x','x','aleah','PA-FAA-2026-11','${FP['PA-FAA-2026-11'].html_sha256}','${FP['PA-FAA-2026-11'].pdf_sha256}','2026-11-01T00:00:00Z','leah@example.test','Leah Like','studio_checkbox','s','2026-11-01T00:00:00Z')`],
  ['Studio row without a fingerprint', "INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, accepted_at, account_email, display_name, method, statement, created_at) VALUES ('x','x','aleah','PA-FAA-2026-11','2030-01-01T00:00:00Z','leah@example.test','Leah Like','studio_checkbox','s','2030-01-01T00:00:00Z')"],
  ['editing the carried-over row', "UPDATE agreement_acceptances SET accepted_at='2026-11-06T00:00:00Z'"],
  ['deleting the carried-over row', 'DELETE FROM agreement_acceptances'],
]) { try { await db.prepare(sql).run(); tries.push(why + ': RAN'); } catch { tries.push('refused'); } }
check('F2 … and the database itself refuses: a migrated row for any new text, a Studio row dated before the text took effect or without a fingerprint, editing or deleting the record',
  tries.every(x => x === 'refused'), tries.join(' | '));
const log = (await db.prepare('SELECT * FROM enquiry_log ORDER BY introduced_at').all()).results;
check('M5 the enquiry log gets one row per relay enquiry already held (same reference, artwork, time), Founding, with NO buyer details copied',
  log.length === 2 && log[0].reference === 'PA-E-261105-0A1B2C' && log[0].artwork_id === 'w3' && log[0].introduced_at === '2026-11-05T18:00:00.000Z' && log.every(l => l.route === 'relay' && l.founding === 1)
  && !/Bea|bea@|Cal|cal@|available|general question/i.test(JSON.stringify(log)), JSON.stringify(log));
check('M6 the founding-year end it records for the existing artist equals the Studio’s exact Irish-date rule', log[0].founding_year_end === foundingYear(pub).end && log[0].founding_year_end === '2027-11-04', log[0].founding_year_end);
const sch = readFileSync(HERE + 'schema.sql', 'utf8');
const ddl = MIG.split('-- @@DDL-BEGIN')[1].split('\n').slice(1).join('\n').split('-- @@DDL-END')[0].trim();
const ins = MIG.split('-- 5 · The documents.')[1].split('\n').slice(1).join('\n').split('\n\n-- 6 ·')[0].trim();
check('M7 schema.sql (new installs and local tests) carries the same tables, triggers and document rows, word for word', sch.includes(ddl) && sch.includes(ins));
let again = 'ran'; const n0 = JSON.stringify(await dump(await tables()));
try { await run(MIG); } catch (e) { again = 'refused: ' + e.message.slice(0, 60); }
check('M8 running it a second time stops at the first document row and changes nothing', again.startsWith('refused') && JSON.stringify(await dump(await tables())) === n0, again);
const eff = (await db.prepare("SELECT effective_at FROM agreement_documents WHERE doc_id='PA-FAA-2026-11'").first()).effective_at;
let same = 'refused';
try { await db.prepare(`INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, method, statement, created_at) VALUES ('s1','s1','aleah','PA-FAA-2026-11',?,?,?,'leah@example.test','Leah Like','studio_checkbox','s',?)`)
  .bind(FP['PA-FAA-2026-11'].html_sha256, FP['PA-FAA-2026-11'].pdf_sha256, eff.slice(0, 19) + '.500Z', eff.slice(0, 19) + '.500Z').run(); same = 'accepted'; } catch (e) { same = 'refused: ' + e.message.slice(0, 80); }
check('M12 an acceptance in the same second the texts were installed (with milliseconds) is accepted: times are compared as times, not as text', same === 'accepted', same);
const rollback = MIG.split('-- Rollback')[1].split('\n').slice(1).map(l => l.replace(/^--\s*/, '')).join('\n');
await run(rollback);
const ro = await objects();
check('M9 the rollback (before any real acceptance) returns the database exactly to its previous state', JSON.stringify(ro) === JSON.stringify(beforeObjects) && JSON.stringify(await dump(beforeTables)) === JSON.stringify(before));
const sha = createHash('sha256').update(readFileSync(FILE)).digest('hex');
let chk; try { chk = execFileSync('python3', [HERE + '../../atlas-tools/release/studio/migration-check.py', FILE, sha, 'agreement_documents,agreement_acceptances,enquiry_log,record_retention',
  'Creates four new tables with refusal-only guards; carries over existing licence acceptances and relay enquiry references.'], { encoding: 'utf8' }); } catch (e) { chk = String(e.stdout || e.message); }
check('M10 the migration approval check accepts it with exactly these four tables declared, and classes it as needing the founder’s approval (not automatic)', /MIGRATION CHECK OK/.test(chk) && /MIGRATION CLASS: destructive/.test(chk), chk.split('\n').filter(l => /REFUSED|CLASS|OK/.test(l)).join(' '));
let chk2; try { chk2 = execFileSync('python3', [HERE + '../../atlas-tools/release/studio/migration-check.py', FILE, sha, 'agreement_documents,agreement_acceptances,enquiry_log', 'Declaring one table fewer than the file writes to must be refused.'], { encoding: 'utf8' }); } catch (e) { chk2 = String(e.stdout || e.message); }
check('M11 … and refuses it if any table it writes to is not declared', /REFUSED/.test(chk2));
console.log(`\nMIGRATION 0005 · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
console.log(`file SHA-256 ${sha}`);
await mf.dispose(); process.exit(results.every(Boolean) ? 0 : 1);
