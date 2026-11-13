// PROVE · migration 0009 (Opportunities & delivery) on a database built with the CURRENT PRODUCTION schema (main) and
// realistic rows. Local only (Miniflare D1); nothing here touches Cloudflare.
//   node test/prove-migration-0009.mjs /path/to/schema-of-main.sql
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { statements, rollbackOf } from './sql.mjs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
if (!process.argv[2]) { console.log('usage: node test/prove-migration-0009.mjs SCHEMA_OF_MAIN.sql'); process.exit(2); }
const HERE = new URL('..', import.meta.url).pathname;
const MIG = readFileSync(HERE + 'migrations/0009_artist_opportunities.sql', 'utf8');
const SCHEMA_NEW = readFileSync(HERE + 'schema.sql', 'utf8');
const NEW = ['artist_opportunities'];
const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig9-test' } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
const refused = async (sql, ...b) => { try { await db.prepare(sql).bind(...b).run(); return false; } catch { return true; } };
await run(readFileSync(process.argv[2], 'utf8'));

console.log('PROVE · migration 0009 (Opportunities & delivery) on the production schema');
const t = '2026-10-30T10:00:00.000Z', pub = '2026-11-05T17:05:00.000Z';
for (const [id, slug, name, n] of [['aleah', 'leah-like', 'Leah Like', 1], ['apigsy', 'pigsy-like', 'Pigsy Like', 2]]) {
  await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, founding_number, county, account_status, first_published_at, created_at, updated_at)
    VALUES (?,?,?,?,1,?,'Dublin','active',?,?,?)`).bind(id, slug, `${slug}@example.test`, name, n, pub, t, pub).run();
  await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (?,?,0,NULL,?)').bind(n, id, pub).run();
  await db.prepare("INSERT INTO artworks (id, artist_id, slug, title, ord, created_at, updated_at) VALUES (?,?,?,?,1,?,?)").bind(`${id}-w1`, id, 'work-1', 'Work 1', t, t).run();
}
await db.prepare("INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?, 'founder@example.test', 'founder', 'test', 'aleah', '{}')").bind(t).run();
const objects = async () => (await db.prepare("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
const tables = async () => (await objects()).filter(o => o.type === 'table').map(o => o.name);
const dump = async names => { const o = {}; for (const tb of names) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
const beforeObjects = await objects(), beforeTables = await tables(), before = await dump(beforeTables);
check('M0 the base is the production schema (hire reports installed, no opportunities table)', beforeTables.includes('hire_reports') && !beforeTables.includes('artist_opportunities'));
await run(MIG);
const afterObjects = await objects();
check('M1 every existing table and row is byte-for-byte unchanged (artists, artworks, gallery_positions, agreements, hire tables, audit …)', JSON.stringify(await dump(beforeTables)) === JSON.stringify(before));
check('M2 every existing table, index and trigger definition is unchanged', JSON.stringify(afterObjects.filter(o => !NEW.includes(o.tbl_name))) === JSON.stringify(beforeObjects));
const newTables = (await tables()).filter(x => !beforeTables.includes(x));
check('M3 it creates exactly one table, one index and no trigger', JSON.stringify(newTables) === JSON.stringify(NEW)
  && afterObjects.filter(o => o.tbl_name === 'artist_opportunities' && o.type === 'index' && o.sql).length === 1 && !afterObjects.some(o => o.type === 'trigger' && o.tbl_name === 'artist_opportunities'));
check('M4 it installs no rows (every artist starts as "not answered")', (await db.prepare('SELECT COUNT(*) AS n FROM artist_opportunities').first()).n === 0);
check('M5 the gallery order is unchanged', JSON.stringify((await db.prepare('SELECT position, artist_id FROM gallery_positions ORDER BY position').all()).results)
  === JSON.stringify([{ position: 1, artist_id: 'aleah' }, { position: 2, artist_id: 'apigsy' }]));
const ins = (id, o = {}) => db.prepare(`INSERT INTO artist_opportunities (artist_id, interests, artwork_county, transport, coverage_mode, coverage_counties, note, created_at, updated_at, updated_by)
  VALUES (?,?,?,?,?,?,?,?,?,?)`).bind(id, o.i ?? '["living_gallery"]', o.c === undefined ? 'Clare' : o.c, o.t ?? '["deliver"]', o.m === undefined ? 'counties' : o.m, o.k ?? '["Clare"]', o.n ?? null, t, t, 'x@example.test');
let ok = true; try { await ins('aleah').run(); } catch (e) { ok = e.message; }
check('C1 a valid answer is stored', ok === true, ok);
const bad = [];
for (const [why, o] of [['no interest', { i: '[]' }], ['not JSON', { i: 'living_gallery' }], ['online only with another interest', { i: '["online_only","talks"]', t: '[]', m: null, k: '[]' }],
  ['online only with transport', { i: '["online_only"]', m: null, k: '[]' }], ['online only with delivery coverage', { i: '["online_only"]', t: '[]', m: 'anywhere', k: '[]' }],
  ['an unknown coverage mode', { m: 'everywhere' }], ['"selected counties" without counties', { k: '[]' }], ['counties without "selected counties"', { m: 'anywhere' }],
  ['counties with no coverage mode', { m: null }], ['a note over 280 characters', { n: 'x'.repeat(281) }], ['an over-long county', { c: 'x'.repeat(30) }]]) {
  let r; try { await ins('apigsy', o).run(); await db.prepare("DELETE FROM artist_opportunities WHERE artist_id='apigsy'").run(); r = false; } catch { r = true; }
  bad.push([why, r]);
}
check('C2 the table itself refuses: ' + bad.map(b => b[0]).join('; '), bad.every(b => b[1]), JSON.stringify(bad));
check('C3 an answer for an artist who does not exist is refused', await refused("INSERT INTO artist_opportunities (artist_id, interests, created_at, updated_at, updated_by) VALUES ('anobody','[\"talks\"]','x','x','x')"));
// The six-year deletion (artist_opportunities before record_retention and the artist row) still succeeds.
await db.prepare("INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('aold','old','old@example.test','Old',1,'ended',?,?)").bind(t, t).run();
await ins('aold').run();
await db.prepare("INSERT INTO record_retention (artist_id, ended_at, delete_after, recorded_by, recorded_at) VALUES ('aold','2019-01-01T00:00:00Z','2025-01-02T00:00:00Z','founder','2019-01-01T00:00:00Z')").run();
ok = true; let why = '';
try {
  await db.batch([...['acceptance_corrections', 'agreement_acceptances', 'enquiry_log', 'enquiries', 'versions', 'publish_queue', 'gallery_positions', 'participation_events',
    'hire_report_records', 'hire_reports', 'hire_use_permissions', 'hire_participation_events', 'hire_terms_acceptances', 'artwork_hire', 'artist_opportunities', 'record_retention'].map(x => db.prepare(`DELETE FROM ${x} WHERE artist_id = 'aold'`)),
    db.prepare("DELETE FROM artists WHERE id = 'aold' AND account_status = 'ended'"), db.prepare("DELETE FROM audit WHERE artist_id = 'aold'")]);
} catch (e) { ok = false; why = e.message; }
check('D1 the existing six-year deletion of an ended artist still succeeds with an answer present', ok && !(await db.prepare("SELECT 1 FROM artist_opportunities WHERE artist_id='aold'").first()), why);
let again = true; try { await run(MIG); } catch { again = false; }
check('R1 running it a second time changes nothing and does not fail', again && JSON.stringify(await objects()) === JSON.stringify(afterObjects));
const block = s => s.slice(s.indexOf('\n', s.indexOf('-- @@DDL-BEGIN')) + 1, s.indexOf('-- @@DDL-END')).trim();
check('R2 schema.sql carries the migration\'s DDL verbatim for new installs and local tests', SCHEMA_NEW.includes(block(MIG)));
await run(rollbackOf(MIG));
check('R3 the documented rollback removes exactly the new table and leaves every existing object as it was', JSON.stringify(await objects()) === JSON.stringify(beforeObjects));
await mf.dispose();
const fail = results.filter(x => !x).length;
console.log(`\nMIGRATION 0009 · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
