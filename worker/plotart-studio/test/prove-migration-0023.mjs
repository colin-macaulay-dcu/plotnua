// PROVE · migration 0023 (three galleries) on a database built with the CURRENT PRODUCTION schema (main, which carries 0022)
// holding realistic records: published artists, gallery positions, Featured Artists, terms, an enquiry and its log entry.
// Local only (Miniflare D1).
//   node test/prove-migration-0023.mjs            (reads main's schema.sql with git)
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { statements } from './sql.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire(new URL('../package.json', import.meta.url).pathname);
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const HERE = new URL('..', import.meta.url).pathname;
const MIG_FILE = HERE + 'migrations/0023_three_galleries.sql';
const MIG = readFileSync(MIG_FILE, 'utf8');
const NEW = ['gallery_settings', 'gallery_memberships', 'artwork_placements', 'gallery_order', 'gallery_features', 'image_use_requests', 'image_use_consents'];
const mainSchema = execFileSync('git', ['-C', HERE, 'show', 'origin/main:worker/plotart-studio/schema.sql'], { encoding: 'utf8' });
const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig23-test' } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
await run(mainSchema);

console.log('PROVE · migration 0023 (three galleries) on the production schema with existing records');
const t = '2026-11-13T19:00:00.000Z';
await seedPublished(db, { id: 'aleah', slug: 'leah-test', email: 'leah@example.test', name: 'Leah Test', works: 3, number: 1 });
await seedPublished(db, { id: 'anessa', slug: 'nessa-test', email: 'nessa@example.test', name: 'Nessa Test', works: 2, number: 2 });
await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (1, ?, 0, NULL, ?), (2, ?, 0, NULL, ?), (3, NULL, 1, ?, ?)').bind('aleah', t, 'anessa', t, 'held', t).run();
await db.prepare('INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (1, ?, ?, ?, ?)').bind('artist', 'anessa', 'wanessa1', t).run();
await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('ainv','inv-test','inv@example.test','Invited Test',0,'invited',?,?)`).bind(t, t).run();
await db.prepare(`INSERT INTO artist_terms (artist_id, track, commission_bp, variation_agreed_on, variation_note, set_by, created_at, updated_at) VALUES ('ainv','gallery_artist',1500,NULL,NULL,'founder@plotnua.invalid',?,?)`).bind(t, t).run();
await db.prepare(`INSERT INTO enquiries (id, reference, artist_id, artwork_id, artwork_title, buyer_name, buyer_email, message, notice_version, created_at, status, delete_after)
  VALUES ('e1','PA-E-261113-AAAAAA','aleah','waleah1','Work 1','Bea','bea@example.test','Is it available?','PA-ENQ-2026-10-29',?,'sent','2028-11-13T00:00:00Z')`).bind(t).run();
await db.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at, late_entry)
  VALUES ('l1','PA-E-261113-AAAAAA','aleah','waleah1','relay',?,1,'2027-11-04','relay',?,0)`).bind(t, t).run();
const objects = async () => (await db.prepare("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
const tables = async () => (await objects()).filter(o => o.type === 'table').map(o => o.name);
const dump = async names => { const o = {}; for (const tb of names) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
const beforeObjects = await objects(), beforeTables = await tables(), before = await dump(beforeTables);
check('M0 the base is the production schema (0022 present, no gallery tables) with real-shaped records',
  !beforeTables.some(x => NEW.includes(x)) && beforeTables.includes('checkout_orders') && before.artists.length === 3 && before.gallery_positions.length === 3 && before.homepage_features.length === 1 && before.enquiry_log.length === 1);
await run(MIG);
const afterObjects = await objects(), afterTables = await tables(), after = await dump(beforeTables);
check('M1 every existing table and every row in it is byte-for-byte unchanged (artists, artworks, versions, positions, Featured Artists, terms, enquiries …)',
  JSON.stringify(after) === JSON.stringify(before));
check('M2 every existing table, index and trigger definition is unchanged', JSON.stringify(afterObjects.filter(o => !NEW.includes(o.tbl_name))) === JSON.stringify(beforeObjects));
check('M3 it adds exactly the seven new tables', JSON.stringify(afterTables.filter(x => !beforeTables.includes(x)).sort()) === JSON.stringify([...NEW].sort()));
check('M4 the new tables are empty: nothing is assigned to any gallery and no setting is written', (await dump(NEW)) && Object.values(await dump(NEW)).every(rows => rows.length === 0));
check('M5 it adds no trigger at all', afterObjects.filter(o => o.type === 'trigger').length === beforeObjects.filter(o => o.type === 'trigger').length);
let again = true; try { await run(MIG); } catch (e) { again = e.message; }
check('R1 running it a second time is harmless (IF NOT EXISTS) and changes nothing', again === true && JSON.stringify(await objects()) === JSON.stringify(afterObjects));
const block = s => s.slice(s.indexOf('\n', s.indexOf('-- @@DDL-BEGIN')) + 1, s.indexOf('-- @@DDL-END')).trim();
check('R2 schema.sql carries the migration verbatim for new installs and local tests', readFileSync(HERE + 'schema.sql', 'utf8').includes(block(MIG)));
for (const l of MIG.split('\n').filter(l => /^--\s+DROP TABLE /.test(l))) await db.prepare(l.replace(/^--\s*/, '')).run();
check('R3 the documented rollback removes exactly the seven new tables; every existing row and definition is still in place',
  JSON.stringify(await objects()) === JSON.stringify(beforeObjects) && JSON.stringify(await dump(beforeTables)) === JSON.stringify(before));
await mf.dispose();
const sha = execFileSync('sha256sum', [MIG_FILE], { encoding: 'utf8' }).split(' ')[0];
let cls = '';
try { cls = execFileSync('python3', [HERE + '../../atlas-tools/release/studio/migration-check.py', MIG_FILE, sha, NEW.join(','), 'Creates seven new, empty tables for the three-gallery data model and their indexes; changes no existing table or row.'], { encoding: 'utf8' }); } catch (e) { cls = String(e.stdout || e); }
check('C1 the production migration check accepts it and classes it ADDITIVE (new tables and indexes only)', /MIGRATION CHECK OK/.test(cls) && /MIGRATION CLASS: additive/.test(cls), cls.split('\n').filter(l => /REFUSED|CLASS/.test(l)).join(' '));
let narrow = '';
try { narrow = execFileSync('python3', [HERE + '../../atlas-tools/release/studio/migration-check.py', MIG_FILE, sha, 'gallery_settings', 'Creates seven new, empty tables for the three-gallery data model and their indexes.'], { encoding: 'utf8' }); } catch (e) { narrow = String(e.stdout || e); }
check('C2 the check refuses it if any table it writes is left undeclared (the guard still bites)', /REFUSED: the SQL writes to tables that are not declared/.test(narrow));
console.log(`  (migration SHA-256 for the founder’s approval: ${sha})`);
const fail = results.filter(x => !x).length;
console.log(`\nMIGRATION 0023 · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
