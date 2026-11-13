// PROVE · migrations 0012 (Gallery Artist terms and agreement records) and 0013 (the approved PA-GAA text) on a database
// built with the CURRENT PRODUCTION schema (main, which carries 0010 and 0011) holding realistic records. Local only.
//   node test/prove-migration-0012-0013.mjs /path/to/schema-of-main.sql
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { statements } from './sql.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
if (!process.argv[2]) { console.log('usage: node test/prove-migration-0012-0013.mjs SCHEMA_OF_MAIN.sql'); process.exit(2); }
const HERE = new URL('..', import.meta.url).pathname;
const M12 = readFileSync(HERE + 'migrations/0012_gallery_artist_terms.sql', 'utf8');
const M13 = readFileSync(HERE + 'migrations/0013_gallery_artist_agreement_text.sql', 'utf8');
const SCHEMA_NEW = readFileSync(HERE + 'schema.sql', 'utf8');
const FP = JSON.parse(readFileSync(HERE + 'agreements/issued/fingerprints.json', 'utf8')).documents;
const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig12-test' } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
await run(readFileSync(process.argv[2], 'utf8'));

console.log('PROVE · migrations 0012 and 0013 on the production schema with existing records');
const t = '2026-11-13T19:00:00.000Z';
await seedPublished(db, { id: 'aleah', slug: 'leah-test', email: 'leah@example.test', name: 'Leah Test', works: 3, number: 1 });
await seedPublished(db, { id: 'anessa', slug: 'nessa-test', email: 'nessa@example.test', name: 'Nessa Test', works: 2, number: 2 });
await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (1, ?, 0, NULL, ?), (2, ?, 0, NULL, ?)').bind('aleah', t, 'anessa', t).run();
await db.prepare("UPDATE artists SET open_for_commissions = 1 WHERE id = 'aleah'").run();
await db.prepare(`INSERT INTO enquiries (id, reference, artist_id, artwork_id, artwork_title, buyer_name, buyer_email, message, notice_version, created_at, status, delete_after)
  VALUES ('e1','PA-E-261113-AAAAAA','aleah','waleah1','Work 1','Bea','bea@example.test','Is it available?','PA-ENQ-2026-10-29',?,'sent','2028-11-13T00:00:00Z')`).bind(t).run();
await db.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at, late_entry)
  VALUES ('l1','PA-E-261113-AAAAAA','aleah','waleah1','relay',?,1,'2027-11-04','relay',?,0)`).bind(t, t).run();
const ta = new Date(Date.now() + 1000).toISOString();   // after the texts' effective time (installed 'now' by the schema)
const fa = FP['PA-FAA-2026-11'], gp = FP['PA-GPIL-2026-11'];
await db.prepare(`INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, legal_name, method, statement, note, created_at)
  VALUES ('acc1','evt1','anessa','PA-FAA-2026-11',?,?,?,'nessa@example.test','Nessa Test',NULL,'studio_checkbox','I accept',NULL,?),
         ('acc2','evt1','anessa','PA-GPIL-2026-11',?,?,?,'nessa@example.test','Nessa Test',NULL,'studio_checkbox','I accept',NULL,?)`).bind(fa.html_sha256, fa.pdf_sha256, ta, ta, gp.html_sha256, gp.pdf_sha256, ta, ta).run();
const objects = async () => (await db.prepare("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
const tables = async () => (await objects()).filter(o => o.type === 'table').map(o => o.name);
const dump = async names => { const o = {}; for (const tb of names) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
const beforeObjects = await objects(), beforeTables = await tables(), before = await dump(beforeTables);
const NEW = ['artist_terms', 'gallery_agreement_acceptances', 'gallery_agreement_documents'];
check('M0 the base is the production schema (0010 and 0011 present, no Gallery Artist tables) with real-shaped records',
  beforeTables.includes('agreement_acceptances') && NEW.every(n => !beforeTables.includes(n)) && before.artists.length === 2 && before.artists.some(a => a.open_for_commissions === 1)
  && before.agreement_acceptances.length === 2 && before.enquiry_log.length === 1);
await run(M12);
const afterTables = await tables(), after = await dump(beforeTables);
check('M1 0012 adds exactly the three new tables', JSON.stringify(afterTables.filter(x => !beforeTables.includes(x)).sort()) === JSON.stringify(NEW));
check('M2 every existing table and row is byte-for-byte unchanged (artists, Founding numbers, positions, versions, enquiries, enquiry log, acceptances …)', JSON.stringify(after) === JSON.stringify(before));
check('M3 every existing table, index and trigger definition is unchanged', JSON.stringify((await objects()).filter(o => beforeObjects.some(b => b.type === o.type && b.name === o.name))) === JSON.stringify(beforeObjects));
const newDump = await dump(NEW);
check('M4 the new tables start empty: no artist is moved to the Gallery Artist programme, and no text is installed', NEW.every(n => newDump[n].length === 0));
const block = s => s.slice(s.indexOf('\n', s.indexOf('-- @@DDL-BEGIN')) + 1, s.indexOf('-- @@DDL-END')).trim();
check('M5 schema.sql carries 0012 verbatim for new installs and local tests', SCHEMA_NEW.includes(block(M12)));
let again = 'ran'; try { await run(M12); } catch (e) { again = 'refused'; }
check('M6 running 0012 a second time changes nothing (CREATE … IF NOT EXISTS)', JSON.stringify(await dump([...beforeTables, ...NEW])) === JSON.stringify({ ...before, ...newDump }), again);
const g = FP['PA-GAA-2026-11'];
check('M7 0013 installs exactly the issued PA-GAA fingerprints (html and pdf)', M13.includes(g.html_sha256) && M13.includes(g.pdf_sha256));
await run(M13);
const docs = (await dump(['gallery_agreement_documents'])).gallery_agreement_documents;
check('M8 after 0013 there is exactly one installed Gallery Artist text, fixed, with those fingerprints; nothing else changed',
  docs.length === 1 && docs[0].doc_id === 'PA-GAA-2026-11' && docs[0].text_status === 'fixed' && docs[0].html_sha256 === g.html_sha256
  && JSON.stringify(await dump(beforeTables)) === JSON.stringify(before));
let r13 = 'ran'; try { await run(M13); } catch { r13 = 'refused'; }
check('M9 running 0013 a second time is refused by the database (primary key)', r13 === 'refused' && (await dump(['gallery_agreement_documents'])).gallery_agreement_documents.length === 1);
let c = 'ran'; try { await db.prepare("INSERT INTO artist_terms (artist_id, track, commission_bp, set_by, created_at, updated_at) VALUES ('aleah','founding',1500,'x',?,?)").bind(t, t).run(); } catch { c = 'refused'; }
check('M10 the only track the terms table accepts is gallery_artist (Founding Artists never get a terms row)', c === 'refused');
const lines = M12.split('\n').filter(l => /^-- DROP TABLE/.test(l));
for (const l of lines) for (const st of l.replace(/^--\s*/, '').split(';').map(x => x.trim()).filter(Boolean)) await db.prepare(st).run();
check('M11 the documented rollback removes exactly the three new tables; every existing row is still in place',
  JSON.stringify(await tables()) === JSON.stringify(beforeTables) && JSON.stringify(await dump(beforeTables)) === JSON.stringify(before));
await mf.dispose();
const fail = results.filter(x => !x).length;
console.log(`\nMIGRATIONS 0012-0013 · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
