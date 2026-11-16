// PROVE · migration 0015 (Opportunities shown publicly) on a database built with the CURRENT PRODUCTION schema (main, which
// carries 0009-0014) holding realistic records: Founding Artists, gallery positions, published versions, an enquiry and its log entry,
// agreement acceptances, Opportunities answers. Local only (Miniflare D1).
//   node test/prove-migration-0015.mjs /path/to/schema-of-main.sql
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { statements } from './sql.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
if (!process.argv[2]) { console.log('usage: node test/prove-migration-0015.mjs SCHEMA_OF_MAIN.sql'); process.exit(2); }
const HERE = new URL('..', import.meta.url).pathname;
const MIG = readFileSync(HERE + 'migrations/0015_opportunities_public.sql', 'utf8');
const SCHEMA_NEW = readFileSync(HERE + 'schema.sql', 'utf8');
const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig15-test' } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
const refused = async (sql, ...b) => { try { await db.prepare(sql).bind(...b).run(); return false; } catch { return true; } };
await run(readFileSync(process.argv[2], 'utf8'));

console.log('PROVE · migration 0015 (Opportunities shown publicly) on the production schema with existing records');
const t = '2026-11-13T19:00:00.000Z';
await seedPublished(db, { id: 'aleah', slug: 'leah-test', email: 'leah@example.test', name: 'Leah Test', works: 3, number: 1 });
await seedPublished(db, { id: 'anessa', slug: 'nessa-test', email: 'nessa@example.test', name: 'Nessa Test', works: 2, number: 2 });
await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (1, ?, 0, NULL, ?), (2, ?, 0, NULL, ?)').bind('aleah', t, 'anessa', t).run();
await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('ainv','inv-test','inv@example.test','Invited Test',0,'invited',?,?)`).bind(t, t).run();
await db.prepare(`INSERT INTO enquiries (id, reference, artist_id, artwork_id, artwork_title, buyer_name, buyer_email, message, notice_version, created_at, status, delete_after)
  VALUES ('e1','PA-E-261113-AAAAAA','aleah','waleah1','Work 1','Bea','bea@example.test','Is it available?','PA-ENQ-2026-10-29',?,'sent','2028-11-13T00:00:00Z')`).bind(t).run();
await db.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at, late_entry)
  VALUES ('l1','PA-E-261113-AAAAAA','aleah','waleah1','relay',?,1,'2027-11-04','relay',?,0)`).bind(t, t).run();
await db.prepare(`INSERT INTO artist_opportunities (artist_id, interests, artwork_county, transport, coverage_mode, coverage_counties, practical_note, care_condition, created_at, updated_at, updated_by)
  VALUES ('aleah','["commissions"]','Dublin','["courier"]','anywhere','[]','Large canvases.',1,?,?,'leah@example.test')`).bind(t, t).run();
const objects = async () => (await db.prepare("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
const tables = async () => (await objects()).filter(o => o.type === 'table').map(o => o.name);
const dump = async names => { const o = {}; for (const tb of names) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
const cols = async () => (await db.prepare("SELECT name FROM pragma_table_info('artist_opportunities')").all()).results.map(r => r.name);
const beforeObjects = await objects(), beforeTables = await tables(), before = await dump(beforeTables), beforeCols = await cols();
check('M0 the base is the production schema (0010 present, no public_display) with real-shaped records',
  !beforeCols.includes('public_display') && beforeCols.includes('care_condition') && before.artists.length === 3 && before.versions.length === 2 && before.artist_opportunities.length === 1);
await run(MIG);
const afterObjects = await objects(), afterTables = await tables(), after = await dump(afterTables);
const others = beforeTables.filter(x => x !== 'artist_opportunities');
check('M1 every other table and row is byte-for-byte unchanged (artists incl. open_for_commissions, versions, positions, enquiries, agreements …)',
  JSON.stringify(others.map(x => after[x])) === JSON.stringify(others.map(x => before[x])) && JSON.stringify(afterTables) === JSON.stringify(beforeTables));
check('M2 every other table, index and trigger definition is unchanged', JSON.stringify(afterObjects.filter(o => o.tbl_name !== 'artist_opportunities')) === JSON.stringify(beforeObjects.filter(o => o.tbl_name !== 'artist_opportunities')));
const NEWC = ['public_display', 'public_decided_at', 'public_notice'];
check('M3 it adds exactly three columns to artist_opportunities and keeps every existing column', JSON.stringify(await cols()) === JSON.stringify([...beforeCols, ...NEWC]));
const keep = r => { const o = { ...r }; for (const c of NEWC) delete o[c]; return o; };
check('M4 every existing answer keeps every original value, and every one starts NOT DECIDED (NULL): nothing becomes public',
  JSON.stringify(after.artist_opportunities.map(keep)) === JSON.stringify(before.artist_opportunities) && after.artist_opportunities.every(r => r.public_display === null && r.public_decided_at === null && r.public_notice === null));
check('C1 public_display accepts only NULL, 0 or 1', await refused("UPDATE artist_opportunities SET public_display = 2 WHERE artist_id = 'aleah'")
  && !(await refused("UPDATE artist_opportunities SET public_display = 1 WHERE artist_id = 'aleah'")) && !(await refused("UPDATE artist_opportunities SET public_display = NULL WHERE artist_id = 'aleah'")));
let ok = true; try { await db.prepare(`INSERT INTO artist_opportunities (artist_id, interests, created_at, updated_at, updated_by) VALUES ('anessa','["talks"]',?,?,'nessa@example.test')`).bind(t, t).run(); } catch (e) { ok = e.message; }
check('C2 the Studio currently live keeps saving answers (its INSERT names no new column; the new answer starts not decided)', ok === true && (await db.prepare("SELECT public_display p FROM artist_opportunities WHERE artist_id='anessa'").first()).p === null, ok);
let again = true; try { await run(MIG); } catch { again = false; }
check('R1 running it a second time is refused by the database and changes nothing', !again && JSON.stringify(await cols()) === JSON.stringify([...beforeCols, ...NEWC]));
const block = s => s.slice(s.indexOf('\n', s.indexOf('-- @@DDL-BEGIN')) + 1, s.indexOf('-- @@DDL-END')).trim();
check('R2 schema.sql carries the migration verbatim for new installs and local tests', SCHEMA_NEW.includes(block(MIG)));
for (const l of MIG.split('\n').filter(l => /^--\s+ALTER TABLE .* DROP COLUMN/.test(l))) await db.prepare(l.replace(/^--\s*/, '')).run();
check('R3 the documented rollback removes exactly the new columns; every earlier answer is still in place',
  JSON.stringify(await cols()) === JSON.stringify(beforeCols) && JSON.stringify((await dump(['artist_opportunities'])).artist_opportunities.filter(r => r.artist_id !== 'anessa')) === JSON.stringify(before.artist_opportunities));
await mf.dispose();
const fail = results.filter(x => !x).length;
console.log(`\nMIGRATION 0015 · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
