// PROVE · migration 0011 (Open for Commissions) on a database built with the CURRENT PRODUCTION schema (main, which carries
// 0010) holding realistic records: Founding Artists, gallery positions, published versions, an enquiry and its log entry,
// agreement acceptances, Opportunities answers. Local only (Miniflare D1).
//   node test/prove-migration-0011.mjs /path/to/schema-of-main.sql
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { statements } from './sql.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
if (!process.argv[2]) { console.log('usage: node test/prove-migration-0011.mjs SCHEMA_OF_MAIN.sql'); process.exit(2); }
const HERE = new URL('..', import.meta.url).pathname;
const MIG = readFileSync(HERE + 'migrations/0011_open_for_commissions.sql', 'utf8');
const SCHEMA_NEW = readFileSync(HERE + 'schema.sql', 'utf8');
const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig11-test' } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
const refused = async (sql, ...b) => { try { await db.prepare(sql).bind(...b).run(); return false; } catch { return true; } };
await run(readFileSync(process.argv[2], 'utf8'));

console.log('PROVE · migration 0011 (Open for Commissions) on the production schema with existing records');
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
const cols = async () => (await db.prepare("SELECT name FROM pragma_table_info('artists')").all()).results.map(r => r.name);
const beforeObjects = await objects(), beforeTables = await tables(), before = await dump(beforeTables), beforeCols = await cols();
check('M0 the base is the production schema (0010 present, no open_for_commissions) with real-shaped records',
  !beforeCols.includes('open_for_commissions') && before.artists.length === 3 && before.versions.length === 2 && before.enquiry_log.length === 1 && before.artist_opportunities.length === 1);
await run(MIG);
const afterObjects = await objects(), afterTables = await tables(), after = await dump(afterTables);
const others = beforeTables.filter(x => x !== 'artists');
check('M1 every other table and row is byte-for-byte unchanged (versions, positions, enquiries, enquiry log, agreements, Opportunities …)',
  JSON.stringify(others.map(x => after[x])) === JSON.stringify(others.map(x => before[x])) && JSON.stringify(afterTables) === JSON.stringify(beforeTables));
check('M2 every other table, index and trigger definition is unchanged', JSON.stringify(afterObjects.filter(o => o.name !== 'artists')) === JSON.stringify(beforeObjects.filter(o => o.name !== 'artists')));
check('M3 it adds exactly one column to artists and keeps every existing column', JSON.stringify(await cols()) === JSON.stringify([...beforeCols, 'open_for_commissions']));
const keep = r => { const { open_for_commissions, ...rest } = r; return rest; };
check('M4 every artist row keeps every original value (Founding status and numbers included), and every artist starts OFF',
  JSON.stringify(after.artists.map(keep)) === JSON.stringify(before.artists) && after.artists.every(r => r.open_for_commissions === 0));
check('C1 only 0 or 1 is accepted', await refused("UPDATE artists SET open_for_commissions = 2 WHERE id = 'aleah'") && await refused("UPDATE artists SET open_for_commissions = NULL WHERE id = 'aleah'")
  && !(await refused("UPDATE artists SET open_for_commissions = 1 WHERE id = 'aleah'")));
let ok = true; try { await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, created_at, updated_at) VALUES ('anew','new-test','new@example.test','New',0,?,?)`).bind(t, t).run(); } catch (e) { ok = e.message; }
check('C2 the Studio currently live keeps creating artists (its INSERT names no new column; the new artist starts OFF)', ok === true && (await db.prepare("SELECT open_for_commissions o FROM artists WHERE id='anew'").first()).o === 0, ok);
let again = true; try { await run(MIG); } catch { again = false; }
check('R1 running it a second time is refused by the database and changes nothing', !again && JSON.stringify(await cols()) === JSON.stringify([...beforeCols, 'open_for_commissions']));
const block = s => s.slice(s.indexOf('\n', s.indexOf('-- @@DDL-BEGIN')) + 1, s.indexOf('-- @@DDL-END')).trim();
check('R2 schema.sql carries the migration verbatim for new installs and local tests', SCHEMA_NEW.includes(block(MIG)));
for (const l of MIG.split('\n').filter(l => /^--\s+ALTER TABLE .* DROP COLUMN/.test(l))) await db.prepare(l.replace(/^--\s*/, '')).run();
check('R3 the documented rollback removes exactly the new column; every other value is still in place',
  JSON.stringify(await cols()) === JSON.stringify(beforeCols) && JSON.stringify((await dump(['artists'])).artists.filter(r => r.id !== 'anew')) === JSON.stringify(before.artists));
await mf.dispose();
const fail = results.filter(x => !x).length;
console.log(`\nMIGRATION 0011 · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
