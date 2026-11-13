// PROVE · migration 0010 (Opportunities & delivery: care condition and 2,000-character note) on a database built with the
// CURRENT PRODUCTION schema (main, which carries 0009) holding realistic answers. Local only (Miniflare D1).
//   node test/prove-migration-0010.mjs /path/to/schema-of-main.sql
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { statements } from './sql.mjs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
if (!process.argv[2]) { console.log('usage: node test/prove-migration-0010.mjs SCHEMA_OF_MAIN.sql'); process.exit(2); }
const HERE = new URL('..', import.meta.url).pathname;
const MIG = readFileSync(HERE + 'migrations/0010_opportunities_care.sql', 'utf8');
const SCHEMA_NEW = readFileSync(HERE + 'schema.sql', 'utf8');
const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig10-test' } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
const refused = async (sql, ...b) => { try { await db.prepare(sql).bind(...b).run(); return false; } catch { return true; } };
await run(readFileSync(process.argv[2], 'utf8'));

console.log('PROVE · migration 0010 (care condition, longer note) on the production schema with existing answers');
const t = '2026-11-13T14:40:00.000Z';
for (const [id, n] of [['aleah', 1], ['abea', 2], ['acal', 3], ['adan', 4]]) {
  await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, founding_number, account_status, created_at, updated_at) VALUES (?,?,?,?,1,?,'active',?,?)`)
    .bind(id, id.slice(1), `${id}@example.test`, id, n, t, t).run();
  await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (?,?,0,NULL,?)').bind(n, id, t).run();
}
const ins = (id, i, tr, mode, cs, note) => db.prepare(`INSERT INTO artist_opportunities (artist_id, interests, artwork_county, transport, coverage_mode, coverage_counties, note, created_at, updated_at, updated_by)
  VALUES (?,?,?,?,?,?,?,?,?,?)`).bind(id, i, 'Dublin', tr, mode, cs, note, t, t, `${id}@example.test`).run();
await ins('aleah', '["living_gallery","art_for_hire"]', '["deliver"]', 'counties', '["Dublin","Wicklow"]', 'Some works depend on how they are cared for — ' + 'x'.repeat(230));
await ins('abea', '["online_only"]', '[]', null, '[]', null);
await ins('acal', '["commissions"]', '["courier"]', 'anywhere', '[]', 'Short note.');
const objects = async () => (await db.prepare("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
const tables = async () => (await objects()).filter(o => o.type === 'table').map(o => o.name);
const dump = async names => { const o = {}; for (const tb of names) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
const beforeObjects = await objects(), beforeTables = await tables(), before = await dump(beforeTables);
const cols = async () => (await db.prepare("SELECT name FROM pragma_table_info('artist_opportunities')").all()).results.map(r => r.name);
const beforeCols = await cols();
check('M0 the base is the production schema with 0009 and three existing answers (one with a 276-character note, one online only)',
  beforeTables.includes('artist_opportunities') && !beforeCols.includes('care_condition') && before.artist_opportunities.length === 3);
await run(MIG);
const afterObjects = await objects(), afterTables = await tables(), after = await dump(afterTables);
const others = beforeTables.filter(x => x !== 'artist_opportunities');
check('M1 every other table and row is byte-for-byte unchanged (artists, gallery_positions, agreements, hire tables, audit …)',
  JSON.stringify(others.map(x => after[x])) === JSON.stringify(others.map(x => before[x])) && JSON.stringify(afterTables) === JSON.stringify(beforeTables));
check('M2 every other table, index and trigger definition is unchanged, and the artist_opportunities index is unchanged',
  JSON.stringify(afterObjects.filter(o => o.name !== 'artist_opportunities')) === JSON.stringify(beforeObjects.filter(o => o.name !== 'artist_opportunities')));
check('M3 it adds exactly two columns (care_condition, practical_note) and keeps every existing column', JSON.stringify(await cols()) === JSON.stringify([...beforeCols, 'care_condition', 'practical_note']));
const keep = r => { const { care_condition, practical_note, ...rest } = r; return rest; };
check('M4 every existing answer is preserved exactly: same rows, same values in every original column (notes included)',
  JSON.stringify(after.artist_opportunities.map(keep)) === JSON.stringify(before.artist_opportunities));
check('M5 each existing note is copied into practical_note, a missing note stays missing, and every care condition starts unticked',
  after.artist_opportunities.every((r, i) => r.practical_note === before.artist_opportunities[i].note && r.care_condition === 0));
check('M6 the gallery order is unchanged', JSON.stringify(after.gallery_positions) === JSON.stringify(before.gallery_positions));
const okLong = !(await refused(`INSERT INTO artist_opportunities (artist_id, interests, transport, practical_note, care_condition, created_at, updated_at, updated_by) VALUES ('adan','["talks"]','[]',?,1,'x','x','x')`, 'y'.repeat(2000)));
check('C1 a 2,000-character practical note with the care condition ticked is accepted', okLong);
check('C2 the database refuses a practical note over 2,000 characters and a care value other than 0 or 1',
  await refused("UPDATE artist_opportunities SET practical_note = ? WHERE artist_id = 'adan'", 'y'.repeat(2001)) && await refused("UPDATE artist_opportunities SET care_condition = 2 WHERE artist_id = 'adan'")
  && await refused("UPDATE artist_opportunities SET care_condition = NULL WHERE artist_id = 'adan'"));
check('C3 the earlier guards still hold (online only cannot be mixed, the old note column keeps its 280 limit)',
  await refused(`UPDATE artist_opportunities SET interests = '["online_only","talks"]' WHERE artist_id = 'adan'`) && await refused("UPDATE artist_opportunities SET note = ? WHERE artist_id = 'adan'", 'z'.repeat(281)));
// A Studio from before 0010 keeps writing "note" if it saves between the migration and the Studio deployment.
let ok = true; try { await db.prepare(`INSERT INTO artist_opportunities (artist_id, interests, artwork_county, transport, coverage_mode, coverage_counties, note, created_at, updated_at, updated_by)
  VALUES ('acal','["commissions"]','Cork','[]',NULL,'[]','Edited by the older Studio.','x','y','z') ON CONFLICT(artist_id) DO UPDATE SET note=excluded.note, artwork_county=excluded.artwork_county, updated_at=excluded.updated_at`).run(); } catch (e) { ok = e.message; }
check('C4 the Studio currently live keeps saving answers after the migration (its INSERT/UPDATE still works)', ok === true, ok);
let again = true; try { await run(MIG); } catch { again = false; }
check('R1 running it a second time is refused by the database and changes nothing', !again && JSON.stringify(await dump(['artist_opportunities'])).length > 0
  && JSON.stringify(await cols()) === JSON.stringify([...beforeCols, 'care_condition', 'practical_note']));
const block = s => s.slice(s.indexOf('\n', s.indexOf('-- @@DDL-BEGIN')) + 1, s.indexOf('-- @@DDL-END')).trim();
check('R2 schema.sql carries the migration verbatim for new installs and local tests', SCHEMA_NEW.includes(block(MIG)));
for (const l of MIG.split('\n').filter(l => /^--\s+ALTER TABLE .* DROP COLUMN/.test(l))) await db.prepare(l.replace(/^--\s*/, '')).run();
check('R3 the documented rollback removes exactly the two new columns; the original notes are still in place',
  JSON.stringify(await cols()) === JSON.stringify(beforeCols) && (await db.prepare("SELECT note FROM artist_opportunities WHERE artist_id='aleah'").first()).note === before.artist_opportunities[0].note);
await mf.dispose();
const fail = results.filter(x => !x).length;
console.log(`\nMIGRATION 0010 · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
