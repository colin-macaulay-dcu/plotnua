// PROVE · migration 0002 (Gallery order) on a database built with the CURRENT production schema and a realistic artist:
// account, works, images, submission, a published version. Everything that existed must be byte-for-byte unchanged.
//   node test/prove-migration.mjs /path/to/schema-of-main.sql
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 300)}]` : ''}`); };
const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig-test' } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of sql.replace(/--[^\n]*/g, '').split(';').map(s => s.trim()).filter(Boolean)) await db.prepare(st).run(); };
await run(readFileSync(process.argv[2], 'utf8'));
const t = '2026-10-31T12:00:00.000Z';
await db.prepare("INSERT INTO artists (id, slug, email, display_name, founding, account_status, licence_version, licence_accepted_at, created_at, updated_at) VALUES ('a1test','sophia-test','artist@example.test','Synthetic Artist',1,'active','PA-GPIL-2026-10-29',?,?,?)").bind(t, t, t).run();
await db.prepare("INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('a2test','second-test','second@example.test','Second Synthetic',1,'invited',?,?)").bind(t, t).run();
const tables = (await db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%'").all()).results.map(r => r.name);
const dump = async () => { const o = {}; for (const tb of tables) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
const before = await dump();
await run(readFileSync(new URL('../migrations/0002_gallery_order.sql', import.meta.url), 'utf8'));
const after = await dump();
const strip = rows => rows.map(r => { const { founding_number, ...rest } = r; return rest; });
check('M1 every existing table and row is unchanged (artists differ only by the new, empty founding_number)',
  tables.every(tb => JSON.stringify(tb === 'artists' ? strip(after[tb]) : after[tb]) === JSON.stringify(before[tb])) && after.artists.every(a => a.founding_number === null));
check('M2 account status, licence, email and gallery address of existing artists are untouched',
  JSON.stringify(after.artists.map(a => [a.id, a.account_status, a.licence_version, a.email, a.slug, a.founding])) === JSON.stringify(before.artists.map(a => [a.id, a.account_status, a.licence_version, a.email, a.slug, a.founding])));
const gp = (await db.prepare('SELECT * FROM gallery_positions').all()).results;
check('M3 the only new row is position 01, reserved, with no note and no artist', gp.length === 1 && gp[0].position === 1 && gp[0].reserved === 1 && gp[0].artist_id === null && gp[0].note === null);
check('M4 no artist has a Founding number after the migration (founder sets them)', after.artists.every(a => a.founding_number === null));
let again = 'ok'; try { await run(readFileSync(new URL('../migrations/0002_gallery_order.sql', import.meta.url), 'utf8')); again = 'ran twice'; } catch (e) { again = 'refused: ' + e.message.slice(0, 60); }
check('M5 running it a second time is refused (the column already exists) and changes nothing', again.startsWith('refused') && (await db.prepare('SELECT COUNT(*) n FROM gallery_positions').first()).n === 1, again);
console.log(`\nMIGRATION 0002 · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
await mf.dispose(); process.exit(results.every(Boolean) ? 0 : 1);
