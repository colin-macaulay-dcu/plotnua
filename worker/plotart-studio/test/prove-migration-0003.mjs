// PROVE · migration 0003 (PlotNua Idea Board) on a database built with the CURRENT production schema and realistic rows.
// Everything that existed must be byte-for-byte unchanged; the rollback must return the database to exactly that state.
//   node test/prove-migration-0003.mjs /path/to/schema-of-main.sql
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { statements } from './sql.mjs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 300)}]` : ''}`); };
const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig3-test' } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
const file = f => readFileSync(new URL('../migrations/' + f, import.meta.url), 'utf8');
await run(readFileSync(process.argv[2], 'utf8'));
const t = '2026-10-31T12:00:00.000Z';
await db.prepare("INSERT INTO artists (id, slug, email, display_name, founding, account_status, licence_version, licence_accepted_at, created_at, updated_at) VALUES ('a1test','synthetic-one','artist@example.test','Synthetic Artist',1,'active','PA-GPIL-2026-10-29',?,?,?)").bind(t, t, t).run();
await db.prepare("INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('a2test','synthetic-two','second@example.test','Second Synthetic',1,'invited',?,?)").bind(t, t).run();
await db.prepare("INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?, 'founder@example.test', 'founder', 'test', 'a1test', '{}')").bind(t).run();
const objects = async () => (await db.prepare("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
const tables = async () => (await objects()).filter(o => o.type === 'table').map(o => o.name);
const dump = async names => { const o = {}; for (const tb of names) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
const beforeObjects = await objects(), beforeTables = await tables(), before = await dump(beforeTables);

await run(file('0003_ideas.sql'));
const afterTables = await tables(), after = await dump(beforeTables);
check('M1 every existing table and row is byte-for-byte unchanged', JSON.stringify(after) === JSON.stringify(before));
check('M2 exactly two new tables (ideas, idea_intake_days) and one new index; no existing object altered',
  JSON.stringify(afterTables.filter(x => !beforeTables.includes(x)).sort()) === '["idea_intake_days","ideas"]' &&
  JSON.stringify((await objects()).filter(o => !beforeObjects.some(b => b.name === o.name)).map(o => o.type + ':' + o.name)) === '["index:ideas_status_published","table:idea_intake_days","table:ideas"]' &&
  JSON.stringify((await objects()).filter(o => beforeObjects.some(b => b.name === o.name))) === JSON.stringify(beforeObjects));
check('M3 the new tables are empty', (await db.prepare('SELECT COUNT(*) n FROM ideas').first()).n === 0 && (await db.prepare('SELECT COUNT(*) n FROM idea_intake_days').first()).n === 0);
const cols = (await db.prepare('PRAGMA table_info(ideas)').all()).results.map(c => c.name);
check('M4 the ideas table has no column for a name, e-mail, telephone or IP address', !cols.some(c => /name|mail|phone|tel|ip|addr/.test(c)), cols.join(','));
const ins = (o) => db.prepare('INSERT INTO ideas (id, ref, text, area, county, show_county, status, became_discovery, created_at) VALUES (?,?,?,?,?,?,?,?,?)')
  .bind(o.id || 'i1', o.ref || 'PN-I-261101-AAAA', o.text ?? 'A valid idea text', o.area ?? null, o.county ?? null, o.show_county ?? 0, o.status || 'received', o.became_discovery ?? null, t).run();
const refused = async o => { try { await ins(o); await db.prepare("DELETE FROM ideas").run(); return false; } catch { return true; } };
const r = [await refused({ text: 'short' }), await refused({ text: 'x'.repeat(161) }), await refused({ area: 'Kitchen' }), await refused({ status: 'published' }),
  await refused({ show_county: 1 }), await refused({ became_discovery: 'https://example.test/x.html' }), await refused({ became_discovery: 'ideas.html' })];
check('M5 the database itself refuses invalid ideas (too short, too long, unknown area, unknown status, county shown without a county, a link that is not a Discovery page)', r.every(Boolean), JSON.stringify(r));
await ins({}); await ins({ id: 'i2', ref: 'PN-I-261101-BBBB', became_discovery: 'discovery-hidden-cars.html', status: 'approved' });
check('M6 valid ideas are accepted', (await db.prepare('SELECT COUNT(*) n FROM ideas').first()).n === 2);
let again = 'ok'; try { await run(file('0003_ideas.sql')); again = 'ran twice'; } catch (e) { again = 'refused: ' + e.message.slice(0, 60); }
check('M7 running the migration a second time is refused and changes nothing', again.startsWith('refused') && (await db.prepare('SELECT COUNT(*) n FROM ideas').first()).n === 2, again);

await run(file('0003_ideas_rollback.sql'));
check('M8 rollback: the database returns exactly to its previous objects and rows', JSON.stringify(await objects()) === JSON.stringify(beforeObjects) &&
  JSON.stringify(await dump(beforeTables)) === JSON.stringify(before));
await run(file('0003_ideas.sql'));
check('M9 after a rollback the migration can be applied again cleanly', (await tables()).includes('ideas') && JSON.stringify(await dump(beforeTables)) === JSON.stringify(before));
console.log(`\nMIGRATION 0003 · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
await mf.dispose(); process.exit(results.every(Boolean) ? 0 : 1);
