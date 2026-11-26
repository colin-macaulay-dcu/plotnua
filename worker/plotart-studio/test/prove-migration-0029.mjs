// PROVE · PlotArt Studio · migration 0029 (unified gallery curation) on the production schema (everything up to 0028)
// with synthetic artists. Local Miniflare only.   node test/prove-migration-0029.mjs
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { seedPublished } from './seed.mjs';
import { statements } from './sql.mjs';
const require = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');

const HERE = new URL('..', import.meta.url).pathname;
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 500)}]` : ''}`); };
const FILE = HERE + 'migrations/0029_gallery_curation.sql', MIG = readFileSync(FILE, 'utf8');
console.log('PROVE · migration 0029 · SHA-256 ' + createHash('sha256').update(readFileSync(FILE)).digest('hex'));
// the production schema before 0029: production main's schema.sql (it carries 0028)
const BASE_REF = process.env.BASE_REF || 'origin/main';
const base = execFileSync('git', ['-C', HERE, 'show', `${BASE_REF}:worker/plotart-studio/schema.sql`], { encoding: 'utf8' });
check('M0 the baseline schema has 0028 and not 0029', /CREATE TABLE IF NOT EXISTS gallery_showcase/.test(base) && !/gallery_curation/.test(base));

const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'm29' } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
await run(base);
const T = '2026-11-20T10:00:00.000Z';
const A = ['leah', 'rasher', 'pigsy', 'dan', 'nessa', 'clare', 'anna', 'fintan', 'late1', 'late2', 'unplaced', 'spc1', 'spc2'];
for (const [i, a] of A.entries()) await seedPublished(db, { id: 'a' + a, slug: a, email: a + '@example.test', name: 'Artist ' + a, works: 2, number: i < 8 ? i + 1 : null });
// founding positions: 01 leah, 02 rasher, 03 pigsy, 04 reserved, 06 dan, 07 nessa, 08 clare, 09 anna, 12 fintan
for (const [p, a] of [[1, 'leah'], [2, 'rasher'], [3, 'pigsy'], [6, 'dan'], [7, 'nessa'], [8, 'clare'], [9, 'anna'], [12, 'fintan']])
  await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (?,?,0,NULL,?)').bind(p, 'a' + a, T).run();
await db.prepare("INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (4,NULL,1,'held',?)").bind(T).run();
// later order (26+): late2 before late1
for (const [p, a] of [[26, 'late2'], [27, 'late1']])
  await db.prepare("INSERT INTO gallery_order (gallery_id, position, artist_id, updated_at, updated_by) VALUES ('contemporary',?,?,?,'f@x.ie')").bind(p, 'a' + a, T).run();
// Spaces order and focus
for (const [p, a] of [[1, 'spc2'], [2, 'spc1']])
  await db.prepare("INSERT INTO gallery_order (gallery_id, position, artist_id, updated_at, updated_by) VALUES ('spaces',?,?,?,'f@x.ie')").bind(p, 'a' + a, T).run();
await db.prepare("INSERT INTO gallery_features (gallery_id, position, artist_id, artwork_id, updated_at, updated_by) VALUES ('spaces',1,'aspc1','waspc12',?,'f@x.ie')").bind(T).run();
// the founder's published showcase: leah, rasher, pigsy; a DIFFERENT draft: dan, rasher, leah
await db.prepare("DELETE FROM gallery_showcase").run();
for (const [st, p, a] of [['published', 1, 'leah'], ['published', 2, 'rasher'], ['published', 3, 'pigsy'], ['draft', 1, 'dan'], ['draft', 2, 'rasher'], ['draft', 3, 'leah']])
  await db.prepare("INSERT INTO gallery_showcase (gallery_id, stage, position, artist_id, artwork_id, updated_at, updated_by) VALUES ('contemporary',?,?,?,?,?,'f@x.ie')").bind(st, p, 'a' + a, `wa${a}1`, T).run();
// Artists in Focus: anna (her 2nd work) and fintan (his 2nd work), and dan
for (const [p, a] of [[1, 'anna'], [2, 'fintan'], [3, 'dan']])
  await db.prepare("INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (?, 'artist', ?, ?, ?)").bind(p, 'a' + a, `wa${a}2`, T).run();

const tables = async () => (await db.prepare("SELECT name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY name").all()).results;
const dump = async names => { const o = {}; for (const t of names) o[t] = (await db.prepare(`SELECT * FROM "${t}" ORDER BY rowid`).all()).results; return JSON.stringify(o); };
const t0 = await tables(), names = t0.filter(t => /^CREATE TABLE/.test(t.sql || '')).map(t => t.name), d0 = await dump(names);
await run(MIG);
const t1 = await tables();
const rows = async (g, st) => (await db.prepare('SELECT position, artist_id, artwork_id FROM gallery_curation WHERE gallery_id=? AND stage=? ORDER BY position').bind(g, st).all()).results;
check('M1 one new table and three refusal-only triggers; every existing table, row and value is unchanged',
  (await dump(names)) === d0 && JSON.stringify(t1.filter(t => !t.name.startsWith('gallery_curation'))) === JSON.stringify(t0)
  && t1.filter(t => t.name.startsWith('gallery_curation')).map(t => t.name).sort().join() === 'gallery_curation,gallery_curation_artist_insert,gallery_curation_artist_update,gallery_curation_once');
const pub = await rows('contemporary', 'published'), dr = await rows('contemporary', 'draft');
const fmt = r => r.map(x => `${x.position}:${x.artist_id.slice(1)}${x.artwork_id ? '=' + x.artwork_id : ''}`).join(',');
check('M2 published: today\'s order below the opening row (founding positions, then 26+), opening-row artists left out, numbered from 4',
  fmt(pub) === '4:dan=wadan2,5:nessa,6:clare,7:anna=waanna2,8:fintan=wafintan2,9:late2,10:late1', fmt(pub));
check('M3 draft: follows the draft opening row (dan, rasher, leah held there), so pigsy takes his founding place',
  fmt(dr) === '4:pigsy,5:nessa,6:clare,7:anna=waanna2,8:fintan=wafintan2,9:late2,10:late1', fmt(dr));
check('M4 Artists in Focus artworks are kept for those artists; everyone else starts with their first eligible artwork (NULL)',
  pub.filter(r => r.artwork_id).length === 3 && dr.filter(r => r.artwork_id).length === 2);
check('M5 an unplaced published artist is not added (the page appends them at the end, as today); reserved positions add nobody',
  ![...pub, ...dr].some(r => r.artist_id === 'aunplaced') && pub.length === 7);
const sp = await rows('spaces', 'published');
check('M6 Spaces: its own order and Artists in Focus artwork; Being has none', fmt(sp) === '4:spc2,5:spc1=waspc12' && (await rows('being', 'published')).length === 0, fmt(sp));
const before = await dump(['gallery_curation']);
let again = 'ok'; try { await run(MIG); } catch (e) { again = e.message; }
check('M7 safe to run again: a second run changes nothing and raises nothing', again === 'ok' && (await dump(['gallery_curation'])) === before && (await dump(names)) === d0, again);
const refuse = async sql => { try { await db.prepare(sql).run(); return false; } catch { return true; } };
check('M8 the database refuses another artist\'s artwork (insert and update), an opening-row artist, a repeated artist, position 3 and an unknown gallery or stage',
  await refuse("INSERT INTO gallery_curation VALUES ('contemporary','published',50,'aunplaced','waleah1','2026-11-26T00:00:00.000Z','f@x.ie')")
  && await refuse("UPDATE gallery_curation SET artwork_id='waleah1' WHERE artist_id='anessa' AND stage='published'")
  && await refuse("INSERT INTO gallery_curation VALUES ('contemporary','published',50,'aleah',NULL,'2026-11-26T00:00:00.000Z','f@x.ie')")
  && await refuse("INSERT INTO gallery_curation VALUES ('contemporary','published',50,'anessa',NULL,'2026-11-26T00:00:00.000Z','f@x.ie')")
  && await refuse("INSERT INTO gallery_curation VALUES ('contemporary','published',3,'aunplaced',NULL,'2026-11-26T00:00:00.000Z','f@x.ie')")
  && await refuse("INSERT INTO gallery_curation VALUES ('gallery','published',50,'aunplaced',NULL,'2026-11-26T00:00:00.000Z','f@x.ie')")
  && await refuse("INSERT INTO gallery_curation VALUES ('contemporary','live',50,'aunplaced',NULL,'2026-11-26T00:00:00.000Z','f@x.ie')")
  && !(await refuse("INSERT INTO gallery_curation VALUES ('contemporary','published',50,'aunplaced','waunplaced2','2026-11-26T00:00:00.000Z','f@x.ie')")));
await mf.dispose();
console.log(`\n${results.filter(Boolean).length}/${results.length} passed`);
process.exit(results.every(Boolean) ? 0 : 1);
