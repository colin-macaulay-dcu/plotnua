// PROVE · migration 0024 (Spaces: the final gallery identifier) on a database built with the CURRENT PRODUCTION schema
// (404986e: everything up to 0023 revision 4, which production carries since 25 Nov 2026) holding realistic records:
// published artists, gallery positions, Featured Artists, terms, an enquiry and its log entry. Local only (Miniflare D1).
//   node test/prove-migration-0024.mjs
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { statements } from './sql.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire(new URL('../package.json', import.meta.url).pathname);
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const HERE = new URL('..', import.meta.url).pathname;
const MIG_FILE = HERE + 'migrations/0024_spaces_identifier.sql';
const MIG = readFileSync(MIG_FILE, 'utf8');
const M23 = readFileSync(HERE + 'migrations/0023_three_galleries.sql', 'utf8');
const SEVEN = ['gallery_settings', 'gallery_memberships', 'artwork_placements', 'gallery_order', 'gallery_features', 'image_use_requests', 'image_use_consents'];
const PROD = '404986e1f9d968bf293751363b2c4d6e8ef19bf0';   // production main: migration 0023 revision 4 applied in production (run 45578283948)
const prodSchema = execFileSync('git', ['-C', HERE, 'show', `${PROD}:worker/plotart-studio/schema.sql`], { encoding: 'utf8' });
const t = '2026-11-25T10:00:00.000Z';
let n = 0;
const fresh = async () => {
  const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: `mig24-${++n}` } });
  const db = await mf.getD1Database('DB');
  const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
  await run(prodSchema);
  return { mf, db, run };
};
const objects = async db => (await db.prepare("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
const tables = async db => (await objects(db)).filter(o => o.type === 'table').map(o => o.name);
const dump = async (db, names) => { const o = {}; for (const tb of names) o[tb] = (await db.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return o; };
const norm = s => String(s || '').replace(/IF NOT EXISTS /g, '').replace(/\s+/g, ' ').trim();
const tryInsert = async (db, g) => {   // Contemporary is always open (0023 CHECK), and an open gallery records who opened it
  const open = g === 'contemporary';
  try { await db.prepare("INSERT INTO gallery_settings (gallery_id, status, target_artists, target_works, opened_at, opened_by, updated_at, updated_by) VALUES (?, ?, 1, 1, ?, ?, ?, 'x')")
    .bind(g, open ? 'open' : 'in_preparation', open ? t : null, open ? 'x' : null, t).run(); }
  catch { return 'refused'; }
  await db.prepare('DELETE FROM gallery_settings WHERE gallery_id = ?').bind(g).run();
  return 'accepted';
};

console.log('PROVE · migration 0024 (Spaces) on the production schema with existing records');
const { mf, db, run } = await fresh();
await seedPublished(db, { id: 'aleah', slug: 'leah-test', email: 'leah@example.test', name: 'Leah Test', works: 3, number: 1 });
await seedPublished(db, { id: 'anessa', slug: 'nessa-test', email: 'nessa@example.test', name: 'Nessa Test', works: 2, number: 2 });
await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (1, ?, 0, NULL, ?), (2, ?, 0, NULL, ?), (3, NULL, 1, ?, ?)').bind('aleah', t, 'anessa', t, 'held', t).run();
await db.prepare('INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (1, ?, ?, ?, ?)').bind('artist', 'anessa', 'wanessa1', t).run();
await db.prepare(`INSERT INTO artist_terms (artist_id, track, commission_bp, variation_agreed_on, variation_note, set_by, created_at, updated_at) VALUES ('anessa','gallery_artist',1500,NULL,NULL,'founder@plotnua.invalid',?,?)`).bind(t, t).run();
await db.prepare(`INSERT INTO enquiries (id, reference, artist_id, artwork_id, artwork_title, buyer_name, buyer_email, message, notice_version, created_at, status, delete_after)
  VALUES ('e1','PA-E-261125-AAAAAA','aleah','waleah1','Work 1','Bea','bea@example.test','Is it available?','PA-ENQ-2026-10-29',?,'sent','2028-11-25T00:00:00Z')`).bind(t).run();
await db.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at, late_entry)
  VALUES ('l1','PA-E-261125-AAAAAA','aleah','waleah1','relay',?,1,'2027-11-04','relay',?,0)`).bind(t, t).run();
const beforeObjects = await objects(db), beforeTables = await tables(db);
const OTHER = beforeTables.filter(x => !SEVEN.includes(x));
const before = await dump(db, OTHER);
check('M0 the base is production today: the seven gallery tables exist (0023 revision 4, empty) and accept "environment", with real-shaped records',
  SEVEN.every(x => beforeTables.includes(x)) && Object.values(await dump(db, SEVEN)).every(r => r.length === 0) && (await tryInsert(db, 'environment')) === 'accepted'
  && before.artists.length === 2 && before.gallery_positions.length === 3 && before.homepage_features.length === 1 && before.enquiry_log.length === 1);

await run(MIG);
const afterObjects = await objects(db), afterTables = await tables(db);
check('M1 every other table and every row in it is byte-for-byte unchanged (artists, artworks, versions, positions, Featured Artists, terms, enquiries …)',
  JSON.stringify(await dump(db, OTHER)) === JSON.stringify(before));
check('M2 every other table, index and trigger definition is unchanged',
  JSON.stringify(afterObjects.filter(o => !SEVEN.includes(o.tbl_name))) === JSON.stringify(beforeObjects.filter(o => !SEVEN.includes(o.tbl_name))));
const want = beforeObjects.filter(o => SEVEN.includes(o.tbl_name)).map(o => ({ ...o, sql: norm(o.sql.replace(/'environment'/g, "'spaces'")) }));
const got = afterObjects.filter(o => SEVEN.includes(o.tbl_name)).map(o => ({ ...o, sql: norm(o.sql) }));
check('M3 the same seven tables and indexes, identical to 0023 revision 4 except that the identifier is now "spaces"',
  JSON.stringify(afterTables.slice().sort()) === JSON.stringify(beforeTables.slice().sort()) && JSON.stringify(got) === JSON.stringify(want) && !afterObjects.some(o => /'environment'/.test(o.sql || '')));
check('M4 the seven tables are empty: nothing is assigned to any gallery and no setting is written', Object.values(await dump(db, SEVEN)).every(r => r.length === 0));
const ids = { spaces: await tryInsert(db, 'spaces'), environment: await tryInsert(db, 'environment'), being: await tryInsert(db, 'being'), contemporary: await tryInsert(db, 'contemporary') };
check('M5 the database now accepts "spaces" (and still "contemporary" and "being") and refuses the retired "environment"',
  ids.spaces === 'accepted' && ids.environment === 'refused' && ids.being === 'accepted' && ids.contemporary === 'accepted', JSON.stringify(ids));
check('M6 it adds no trigger', afterObjects.filter(o => o.type === 'trigger').length === beforeObjects.filter(o => o.type === 'trigger').length);
let again = true; try { await run(MIG); } catch (e) { again = e.message; }
check('R1 running it a second time while the tables are empty is harmless and changes nothing', again === true && JSON.stringify(await objects(db)) === JSON.stringify(afterObjects));
await mf.dispose();

/* ---- the guard: with even one gallery row present it refuses, BEFORE anything is dropped ---- */
{
  const g = await fresh();
  await seedPublished(g.db, { id: 'aleah', slug: 'leah-test', email: 'leah@example.test', name: 'Leah Test', works: 1, number: 1 });
  await g.db.prepare(`INSERT INTO gallery_memberships (artist_id, gallery_id, state, source, application_ref, proposed_by, proposed_at, founder_approved_by, founder_approved_at, artist_accepted_at, updated_at)
    VALUES ('aleah','environment','founder_approved','founder_invitation',NULL,'founder@plotnua.invalid',?,'founder@plotnua.invalid',?,NULL,?)`).bind(t, t, t).run();
  const o0 = await objects(g.db), d0 = await dump(g.db, await tables(g.db));
  let err = ''; try { await g.run(MIG); } catch (e) { err = String(e.message || e); }
  check('G1 with one gallery row present the migration refuses at its first statement: nothing is dropped, every table and row is still there',
    /malformed JSON|JSON/i.test(err) && JSON.stringify(await objects(g.db)) === JSON.stringify(o0) && JSON.stringify(await dump(g.db, await tables(g.db))) === JSON.stringify(d0), err.slice(0, 200));
  await g.mf.dispose();
}

/* ---- new installs and the migration check ---- */
const block = s => s.slice(s.indexOf('\n', s.indexOf('-- @@DDL-BEGIN')) + 1, s.indexOf('-- @@DDL-END')).trim();
const SCHEMA = readFileSync(HERE + 'schema.sql', 'utf8');
check('R2 schema.sql carries the migration (its table definitions) for new installs and local tests, after the 0023 block', SCHEMA.includes(block(MIG)) && SCHEMA.indexOf(block(MIG)) > SCHEMA.indexOf(block(M23)));
{
  const mf2 = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'mig24-new' } });
  const db2 = await mf2.getD1Database('DB');
  for (const st of statements(SCHEMA)) await db2.prepare(st).run();
  const fresh7 = (await objects(db2)).filter(o => SEVEN.includes(o.tbl_name)).map(o => ({ ...o, sql: norm(o.sql) }));
  check('R3 a new install from schema.sql has exactly the same seven gallery tables as production after the migration', JSON.stringify(fresh7) === JSON.stringify(got));
  await mf2.dispose();
}
const sha = execFileSync('sha256sum', [MIG_FILE], { encoding: 'utf8' }).split(' ')[0];
const DESC = 'Recreates the seven empty three-gallery tables with the final identifier spaces in place of environment (refuses at its first statement if any of them holds a row); changes no other table or row.';
let cls = '';
try { cls = execFileSync('python3', [HERE + '../../atlas-tools/release/studio/migration-check.py', MIG_FILE, sha, SEVEN.join(','), DESC], { encoding: 'utf8' }); } catch (e) { cls = String(e.stdout || e); }
check('C1 the production migration check accepts it with the seven tables declared and classes it DESTRUCTIVE (so it waits for the founder’s Approve)',
  /MIGRATION CHECK OK/.test(cls) && /MIGRATION CLASS: destructive/.test(cls), cls.split('\n').filter(l => /REFUSED|CLASS/.test(l)).join(' '));
let narrow = '';
try { narrow = execFileSync('python3', [HERE + '../../atlas-tools/release/studio/migration-check.py', MIG_FILE, sha, 'gallery_settings', DESC], { encoding: 'utf8' }); } catch (e) { narrow = String(e.stdout || e); }
check('C2 the check refuses it if any table it writes is left undeclared', /REFUSED/.test(narrow));
console.log(`  (migration SHA-256 for the founder’s approval: ${sha})`);
const fail = results.filter(x => !x).length;
console.log(`\nMIGRATION 0024 · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
