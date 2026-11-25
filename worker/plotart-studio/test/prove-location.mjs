// PROVE · artist location (Phase C): the shared rules (src/location.js) and migration 0025 on a database built with the
// production schema as it will be after migration 0024 (dev/plotart-spaces). Local only (Miniflare D1).
//   node test/prove-location.mjs
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { statements } from './sql.mjs';
import { seedPublished } from './seed.mjs';
import * as L from '../src/location.js';
const require = createRequire(new URL('../package.json', import.meta.url).pathname);
const { Miniflare } = require('miniflare');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 300)}]` : ''}`); };
const HERE = new URL('..', import.meta.url).pathname;
const refused = (b, re) => { try { L.validate(b); return false; } catch (e) { return re ? re.test(e.message) : true; } };
console.log('PROVE · artist location (Phase C)');

/* ---- the rules ---- */
const sligo = L.validate({ country: 'ie', county: 'Sligo', town: 'Strandhill', show_location: true, show_town: true });
check('V1 based in Ireland: a county is required, from the 26; the country code is normalised', sligo.country === 'IE' && sligo.county === 'Sligo'
  && refused({ country: 'IE' }, /county/) && refused({ country: 'IE', county: 'Antrim' }) && refused({ country: 'IE', county: 'Atlantis' }));
check('V2 Northern Ireland: one of its six counties or none; a Republic county is refused with a clear message',
  !!L.validate({ country: 'GB', county: 'Antrim' }) && !!L.validate({ country: 'GB' }) && refused({ country: 'GB', county: 'Dublin' }, /choose Ireland/));
check('V3 international artists: any ISO country, no county; an unknown country is refused',
  L.validate({ country: 'PT', town: 'Lisbon' }).county === null && refused({ country: 'PT', county: 'Cork' }) && refused({ country: 'XX' }) && refused({}));
check('V4 all 32 counties are offered (26 + 6), grouped by the four provinces',
  L.ROI_COUNTIES.length === 26 && L.NI_COUNTIES.length === 6 && Object.values(L.PROVINCES).flat().sort().join() === [...L.ROI_COUNTIES, ...L.NI_COUNTIES].sort().join());
check('V5 a town or city only: house numbers, Eircodes, postcodes and street words are refused',
  ['12 Main Street', 'D02 X285', 'Apt 4', 'Harbour Road', '<b>x</b>'].every(t => refused({ country: 'IE', county: 'Cork', town: t }, /never your address/))
  && L.validate({ country: 'IE', county: 'Cork', town: 'Skibbereen' }).town === 'Skibbereen');
const del = L.validate({ country: 'IE', county: 'Sligo', delivers_local: true, local_counties: ['Leitrim', 'Sligo', 'Mayo', 'Leitrim'], delivers_nationwide: false });
check('V6 delivery areas are kept apart from the home county: the home county is implied, duplicates removed, list order fixed',
  del.local_counties === '["Leitrim","Mayo"]' && L.validate({ country: 'IE', county: 'Sligo', delivers_local: false, local_counties: ['Mayo'] }).local_counties === '[]'
  && refused({ country: 'FR', delivers_local: true }, /counties you can deliver/) && refused({ country: 'IE', county: 'Sligo', delivers_local: true, local_counties: ['Paris'] }));
check('V7 nothing is public unless ticked; the town is public only with the location', L.validate({ country: 'IE', county: 'Cork' }).show_location === 0
  && L.validate({ country: 'IE', county: 'Cork', town: 'Cobh', show_town: true }).show_town === 0);

/* ---- what the public sees ---- */
const row = (b) => ({ ...L.validate(b), confirmed_by: 'artist', confirmed_at: 'x', updated_at: 'x', artist_id: 'a1' });
check('P1 the place line: "Strandhill, Co. Sligo, Ireland", "Co. Antrim, Northern Ireland", "Lisbon, Portugal"',
  L.placeLine(row({ country: 'IE', county: 'Sligo', town: 'Strandhill', show_location: 1, show_town: 1 })) === 'Strandhill, Co. Sligo, Ireland'
  && L.placeLine(row({ country: 'GB', county: 'Antrim', show_location: 1 })) === 'Co. Antrim, Northern Ireland'
  && L.placeLine(row({ country: 'PT', town: 'Lisbon', show_location: 1, show_town: 1 })) === 'Lisbon, Portugal');
const priv = row({ country: 'IE', county: 'Sligo', town: 'Strandhill', show_location: 1, show_town: 0, delivers_local: 1, local_counties: ['Mayo'], show_delivery: 1 });
const pub = L.publicLocation(priv);
check('P2 the public view carries no private field and no town unless ticked; nothing at all when the location is not shown',
  pub && !('town' in pub) && !/confirmed|artist_id|updated/.test(JSON.stringify(Object.keys(pub))) && L.publicLocation({ ...priv, show_location: 0 }) === null);
check('P3 delivery is public only when the artist ticks it AND the founder has switched on public delivery (privacy notice)',
  !('delivery' in pub) && JSON.stringify(L.publicLocation(priv, { deliveryPublic: true }).delivery) === '{"nationwide":false,"area":"Ireland","counties":["Sligo","Mayo"]}'
  && !('delivery' in L.publicLocation({ ...priv, show_delivery: 0 }, { deliveryPublic: true })));
const nat = L.publicLocation(row({ country: 'GB', county: 'Down', show_location: 1, delivers_nationwide: 1, show_delivery: 1 }), { deliveryPublic: true });
check('R1 Art for Hire county filter: "based" (home county) is distinct from "delivers" (local counties or anywhere in Ireland)',
  L.relation(L.publicLocation(priv, { deliveryPublic: true }), 'Sligo') === 'based' && L.relation(L.publicLocation(priv, { deliveryPublic: true }), 'Mayo') === 'delivers'
  && L.relation(L.publicLocation(priv, { deliveryPublic: true }), 'Kerry') === null && L.relation(nat, 'Kerry') === 'delivers' && L.relation(pub, 'Mayo') === null);

/* ---- migration 0025 on the production schema after 0024 ---- */
const MIG_FILE = HERE + 'migrations/0025_artist_locations.sql', MIG = readFileSync(MIG_FILE, 'utf8');
const base = execFileSync('git', ['-C', HERE, 'show', 'dac259f5:worker/plotart-studio/schema.sql'], { encoding: 'utf8' });   // production after migration 0024
const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'loc-test' } });
const db = await mf.getD1Database('DB');
const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
await run(base);
await seedPublished(db, { id: 'aleah', slug: 'leah-test', email: 'leah@example.test', name: 'Leah Test', works: 2, number: 1 });
await db.prepare("UPDATE artists SET county='Dublin', county_public=1 WHERE id='aleah'").run();
const objects = async () => (await db.prepare("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
const tables = async () => (await objects()).filter(o => o.type === 'table').map(o => o.name);
const dump = async names => { const o = {}; for (const t of names) o[t] = (await db.prepare(`SELECT * FROM ${t} ORDER BY rowid`).all()).results; return o; };
const o0 = await objects(), t0 = await tables(), d0 = await dump(t0);
await run(MIG);
check('M1 every existing table, row and definition is unchanged (artists.county and county_public included)',
  JSON.stringify(await dump(t0)) === JSON.stringify(d0) && JSON.stringify((await objects()).filter(o => o.tbl_name !== 'artist_locations')) === JSON.stringify(o0));
check('M2 it adds exactly one table, artist_locations, empty: no existing artist is given a location automatically',
  JSON.stringify((await tables()).filter(t => !t0.includes(t))) === '["artist_locations"]' && (await dump(['artist_locations'])).artist_locations.length === 0);
const env = { DB: db };
await L.saveStatement(env, 'aleah', L.validate({ country: 'IE', county: 'Dublin', town: 'Howth', show_location: true }), 'artist').run();
await L.saveStatement(env, 'aleah', L.validate({ country: 'IE', county: 'Dublin', show_location: true, delivers_nationwide: true }), 'artist').run();
const saved = await db.prepare("SELECT * FROM artist_locations WHERE artist_id='aleah'").first();
check('M3 the Studio’s validated answer is stored, one row per artist; a later answer replaces it', saved && saved.town === null && saved.delivers_nationwide === 1
  && (await db.prepare('SELECT COUNT(*) n FROM artist_locations').first()).n === 1);
const dbRefuses = async (sql) => { try { await db.prepare(sql).run(); } catch { return true; } await db.prepare("DELETE FROM artist_locations WHERE artist_id='aleah2'").run(); return false; };   // accepted rows are removed, so every attempt is tested on its own
const ins = (c, k, t = 'NULL', extra = '') => `INSERT INTO artist_locations (artist_id, country, county, town, confirmed_at, confirmed_by, updated_at${extra ? ', ' + extra.split('=')[0] : ''}) VALUES ('aleah2', '${c}', ${k}, ${t}, '2026-11-25T10:00:00.000Z', 'artist', '2026-11-25T10:00:00.000Z'${extra ? ', ' + extra.split('=')[1] : ''})`;
await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, created_at, updated_at) VALUES ('aleah2','b-test','b@example.test','B Test',0,'2026-11-25T10:00:00.000Z','2026-11-25T10:00:00.000Z')`).run();
check('M4 the database itself refuses what the Studio refuses: Ireland without a county, a Republic county under GB, a county abroad, a town with digits, an unknown county',
  (await dbRefuses(ins('IE', 'NULL'))) && (await dbRefuses(ins('GB', "'Cork'"))) && (await dbRefuses(ins('FR', "'Cork'"))) && (await dbRefuses(ins('IE', "'Cork'", "'12 Main St'")))
  && (await dbRefuses(ins('IE', "'Atlantis'"))) && !(await dbRefuses(ins('GB', "'Antrim'"))));
await db.prepare("DELETE FROM artists WHERE id='aleah2'").run();
check('M5 deleting an artist (the Studio’s existing erasure) takes their location with it (ON DELETE CASCADE)',
  (await db.prepare("SELECT COUNT(*) n FROM artist_locations WHERE artist_id='aleah2'").first()).n === 0);
let again = true; try { await run(MIG); } catch (e) { again = e.message; }
check('R1 running it a second time is harmless (IF NOT EXISTS)', again === true);
const block = s => s.slice(s.indexOf('\n', s.indexOf('-- @@DDL-BEGIN')) + 1, s.indexOf('-- @@DDL-END')).trim();
check('R2 schema.sql carries the migration verbatim for new installs and local tests', readFileSync(HERE + 'schema.sql', 'utf8').includes(block(MIG)));
await mf.dispose();
const sha = execFileSync('sha256sum', [MIG_FILE], { encoding: 'utf8' }).split(' ')[0];
let cls = '';
try { cls = execFileSync('python3', [HERE + '../../atlas-tools/release/studio/migration-check.py', MIG_FILE, sha, 'artist_locations', 'Creates one new, empty table for artist location (country, county, town, delivery) and its index; changes no existing table or row.'], { encoding: 'utf8' }); } catch (e) { cls = String(e.stdout || e); }
check('C1 the production migration check accepts it and classes it ADDITIVE', /MIGRATION CHECK OK/.test(cls) && /MIGRATION CLASS: additive/.test(cls), cls.split('\n').filter(l => /REFUSED|CLASS/.test(l)).join(' '));
console.log(`  (migration SHA-256: ${sha})`);
const fail = results.filter(x => !x).length;
console.log(`\nARTIST LOCATION · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
