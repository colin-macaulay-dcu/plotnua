// PROVE · artist location and delivery coverage (Phase C): the shared rules (src/location.js) and migration 0025 on a database
// built with the production schema as it will be after migration 0024 (dac259f). Local only (Miniflare D1).
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
const no = (f, re) => { try { f(); return false; } catch (e) { return re ? re.test(e.message) : true; } };
console.log('PROVE · artist location and delivery coverage (Phase C)');

/* ---- where the artist is based ---- */
const loc = b => ({ ...L.validateLocation(b), artist_id: 'a1', confirmed_by: 'artist', confirmed_at: 'x', updated_at: 'x' });
check('V1 Republic of Ireland: a county is required, from the 26; the country code is normalised',
  L.validateLocation({ country: 'ie', county: 'Sligo' }).country === 'IE' && no(() => L.validateLocation({ country: 'IE' }), /county/)
  && no(() => L.validateLocation({ country: 'IE', county: 'Antrim' })) && no(() => L.validateLocation({ country: 'IE', county: 'Atlantis' })));
check('V2 Northern Ireland: one of its six counties (or none); a Republic county is refused with a clear message',
  !!L.validateLocation({ country: 'GB', county: 'Antrim' }) && no(() => L.validateLocation({ country: 'GB', county: 'Dublin' }), /choose Ireland/));
check('V3 international artists: any ISO country, no county; an unknown country is refused',
  L.validateLocation({ country: 'PT', town: 'Lisbon' }).county === null && no(() => L.validateLocation({ country: 'PT', county: 'Cork' })) && no(() => L.validateLocation({ country: 'XX' })));
check('V4 all 32 counties (26 + 6), grouped by the four provinces',
  L.ROI_COUNTIES.length === 26 && L.NI_COUNTIES.length === 6 && Object.values(L.PROVINCES).flat().sort().join() === [...L.ROI_COUNTIES, ...L.NI_COUNTIES].sort().join());
check('V5 never a residential address: house numbers, Eircodes, postcodes and street words are refused; a town is accepted',
  ['12 Main Street', 'D02 X285', 'BT1 5GS', 'Apt 4', 'Harbour Road', '<b>x</b>'].every(t => no(() => L.validateLocation({ country: 'IE', county: 'Cork', town: t }), /never your address/))
  && L.validateLocation({ country: 'IE', county: 'Cork', town: 'Skibbereen' }).town === 'Skibbereen');
const lv = L.validateLocation({ country: 'IE', county: 'Cork', scope: 'island', counties: ['Dublin'], show_delivery: 1 });
check('V6 location is kept separate from delivery: the location record holds no delivery field, whatever is sent',
  JSON.stringify(Object.keys(lv).sort()) === JSON.stringify(['country', 'county', 'show_location', 'show_town', 'town']));
check('V7 nothing is public unless ticked; the town is public only with the location', L.validateLocation({ country: 'IE', county: 'Cork' }).show_location === 0
  && L.validateLocation({ country: 'IE', county: 'Cork', town: 'Cobh', show_town: true }).show_town === 0);

/* ---- where the artist can deliver ---- */
const cork = loc({ country: 'IE', county: 'Cork', show_location: 1 }), antrim = loc({ country: 'GB', county: 'Antrim', show_location: 1 }), paris = loc({ country: 'FR', town: 'Paris', show_location: 1 });
// Report 36: the Studio no longer accepts a "show" tick (only a withdrawal); a stored tick from before is simulated here.
// A future public-delivery consent is simulated with consent:true (no such record can exist today).
const NOTICE = 'PA-DELIVERY-PUBLIC-FUTURE';
const del = (b, l) => { const { show_delivery, consent, ...rest } = b; return { ...L.validateDelivery(rest, l), artist_id: 'a1', show_delivery: show_delivery && rest.scope !== 'none' ? 1 : 0, ...(consent ? { public_consent_notice: NOTICE } : {}) }; };
check('D1 coverage distinguishes the Republic (26), Northern Ireland (6) and the whole island (32)',
  L.covered(del({ scope: 'republic' }, cork)).length === 26 && L.covered(del({ scope: 'northern_ireland' }, cork)).join() === L.NI_COUNTIES.join()
  && L.covered(del({ scope: 'island' }, cork)).length === 32 && !L.covered(del({ scope: 'republic' }, cork)).includes('Antrim'));
check('D2 chosen counties: at least one, from the 32, stored once in a fixed order; the list is ignored for any other scope',
  del({ scope: 'counties', counties: ['Kerry', 'Cork', 'Kerry'] }, cork).counties === '["Cork","Kerry"]' && no(() => L.validateDelivery({ scope: 'counties' }, cork), /counties/)
  && del({ scope: 'island', counties: ['Kerry'] }, cork).counties === '[]' && no(() => L.validateDelivery({ scope: 'counties', counties: ['Paris'] }, cork)));
check('D3 "anywhere in my country" is for artists based outside Ireland; on the island the Republic / NI / island choices are used',
  del({ scope: 'country' }, paris).scope === 'country' && no(() => L.validateDelivery({ scope: 'country' }, cork), /Republic, Northern Ireland or the whole island/)
  && no(() => L.validateDelivery({ scope: 'country' }, antrim)));
check('D4 an artist based anywhere may cover any Irish county (Cork covering Dublin; Belfast covering the Republic; Paris covering the island)',
  L.covered(del({ scope: 'counties', counties: ['Dublin'] }, cork)).includes('Dublin') && L.covered(del({ scope: 'republic' }, antrim)).includes('Kerry')
  && L.covered(del({ scope: 'island' }, paris)).includes('Donegal'));

/* ---- what the public sees ---- */
check('P1 the place line: "Strandhill, Co. Sligo, Ireland", "Co. Antrim, Northern Ireland", "Lisbon, Portugal"',
  L.placeLine(loc({ country: 'IE', county: 'Sligo', town: 'Strandhill', show_location: 1, show_town: 1 })) === 'Strandhill, Co. Sligo, Ireland'
  && L.placeLine(antrim) === 'Co. Antrim, Northern Ireland' && L.placeLine(loc({ country: 'PT', town: 'Lisbon', show_location: 1, show_town: 1 })) === 'Lisbon, Portugal');
const priv = loc({ country: 'IE', county: 'Sligo', town: 'Strandhill', show_location: 1, show_town: 0 });
check('P2 the public location carries no private field and no town unless ticked; nothing when not shown',
  !('town' in L.publicLocation(priv)) && !/confirmed|artist_id|updated/.test(Object.keys(L.publicLocation(priv)).join()) && L.publicLocation({ ...priv, show_location: 0 }) === null);
const dIsland = del({ scope: 'island', show_delivery: 1, consent: true }, cork), dTickOnly = del({ scope: 'island', show_delivery: 1 }, cork);
check('P3 coverage is public only with the founder’s switch AND a fresh consent recorded under the notice in force: an earlier tick alone, or the switch alone, shows nothing; the lines name ROI, NI and all-island',
  L.publicDelivery(dIsland, cork) === null && L.publicDelivery({ ...dIsland, show_delivery: 0 }, cork, { deliveryPublic: true, consentNotice: NOTICE }) === null
  && L.publicDelivery(dTickOnly, cork, { deliveryPublic: true, consentNotice: NOTICE }) === null && L.publicDelivery(dIsland, cork, { deliveryPublic: true }) === null
  && L.publicDelivery(dIsland, cork, { deliveryPublic: true, consentNotice: 'AN-OLDER-NOTICE' }) === null
  && L.publicDelivery(dIsland, cork, { deliveryPublic: true, consentNotice: NOTICE }).line === 'Delivers anywhere on the island of Ireland'
  && L.deliveryLine(del({ scope: 'republic' }, cork), cork) === 'Delivers anywhere in the Republic of Ireland'
  && L.deliveryLine(del({ scope: 'northern_ireland' }, antrim), antrim) === 'Delivers anywhere in Northern Ireland'
  && L.deliveryLine(del({ scope: 'counties', counties: ['Kerry', 'Cork'] }, cork), cork) === 'Delivers to Co. Cork, Co. Kerry');

/* ---- Art for Hire: discover local artists without excluding anyone willing to supply the county ---- */
const pub = (l, d) => [L.publicLocation(l), L.publicDelivery(d, l, { deliveryPublic: true, consentNotice: NOTICE })];
const kerryArtist = pub(loc({ country: 'IE', county: 'Kerry', show_location: 1 }), del({ scope: 'none' }, null));
const corkToKerry = pub(cork, del({ scope: 'counties', counties: ['Kerry'], show_delivery: 1, consent: true }, cork));
const belfastROI = pub(antrim, del({ scope: 'republic', show_delivery: 1, consent: true }, antrim));
const parisIsland = pub(paris, del({ scope: 'island', show_delivery: 1, consent: true }, paris));
const corkHidden = pub(cork, del({ scope: 'island', show_delivery: 0 }, cork));
check('R1 filtering by Kerry: a Kerry-based artist is "based"; artists from Cork, Belfast and Paris who supply Kerry are "delivers"; none excluded',
  L.relation(...kerryArtist, 'Kerry') === 'based' && L.relation(...corkToKerry, 'Kerry') === 'delivers' && L.relation(...belfastROI, 'Kerry') === 'delivers'
  && L.relation(...parisIsland, 'Kerry') === 'delivers');
check('R2 "based" (home county) and "delivers" (coverage) stay distinct; private coverage never counts; ROI coverage does not reach NI',
  L.relation(...corkToKerry, 'Cork') === 'based' && L.relation(...corkHidden, 'Kerry') === null && L.relation(...belfastROI, 'Antrim') === 'based'
  && L.relation(...belfastROI, 'Down') === null && L.relation(...kerryArtist, 'Cork') === null);

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
const NEW = ['artist_delivery', 'artist_locations'];
const o0 = await objects(), t0 = await tables(), d0 = await dump(t0);
await run(MIG);
check('M1 every existing table, row and definition is unchanged (artists.county and county_public included)',
  JSON.stringify(await dump(t0)) === JSON.stringify(d0) && JSON.stringify((await objects()).filter(o => !NEW.includes(o.tbl_name))) === JSON.stringify(o0));
check('M2 it adds exactly two tables (location; delivery coverage), both empty: no existing artist is given a location or coverage',
  JSON.stringify((await tables()).filter(t => !t0.includes(t)).sort()) === JSON.stringify(NEW) && Object.values(await dump(NEW)).every(r => r.length === 0));
const env = { DB: db };
await L.saveLocation(env, 'aleah', L.validateLocation({ country: 'IE', county: 'Dublin', town: 'Howth', show_location: true }), 'artist').run();
await L.saveLocation(env, 'aleah', L.validateLocation({ country: 'IE', county: 'Dublin', show_location: true }), 'artist').run();
await L.saveDelivery(env, 'aleah', L.validateDelivery({ scope: 'counties', counties: ['Wicklow', 'Meath'] }, { country: 'IE', county: 'Dublin' }), 'artist').run();
const sl = await db.prepare("SELECT * FROM artist_locations WHERE artist_id='aleah'").first(), sd = await db.prepare("SELECT * FROM artist_delivery WHERE artist_id='aleah'").first();
check('M3 the Studio’s validated answers are stored in their own tables, one row per artist; a later answer replaces it',
  sl && sl.town === null && sd && sd.counties === '["Meath","Wicklow"]' && (await db.prepare('SELECT COUNT(*) n FROM artist_locations').first()).n === 1);
await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, created_at, updated_at) VALUES ('ab','b-test','b@example.test','B Test',0,'2026-11-25T10:00:00.000Z','2026-11-25T10:00:00.000Z')`).run();
const T = "'2026-11-25T10:00:00.000Z'";
const refuses = async (table, cols, vals) => {
  try { await db.prepare(`INSERT INTO ${table} (artist_id, ${cols}, confirmed_at, confirmed_by, updated_at) VALUES ('ab', ${vals}, ${T}, 'artist', ${T})`).run(); }
  catch { return true; }
  await db.prepare(`DELETE FROM ${table} WHERE artist_id='ab'`).run(); return false;   // accepted rows are removed: every attempt is tested on its own
};
const m4 = [await refuses('artist_locations', 'country, county', "'IE', NULL"), await refuses('artist_locations', 'country, county', "'GB', 'Cork'"),
  await refuses('artist_locations', 'country, county', "'FR', 'Cork'"), await refuses('artist_locations', 'country, county, town', "'IE', 'Cork', '12 Main St'"),
  await refuses('artist_locations', 'country, county', "'IE', 'Atlantis'"), !(await refuses('artist_locations', 'country, county', "'GB', 'Antrim'"))];
check('M4 the database refuses what the Studio refuses for location: Republic without a county, a Republic county under GB, a county abroad, a house number, an unknown county',
  m4.every(Boolean), JSON.stringify(m4));
const m5 = [await refuses('artist_delivery', 'scope, counties', "'counties', '[]'"), await refuses('artist_delivery', 'scope, counties', "'island', '[\"Cork\"]'"),
  await refuses('artist_delivery', 'scope', "'worldwide'"), await refuses('artist_delivery', 'scope, show_delivery', "'none', 1"),
  !(await refuses('artist_delivery', 'scope', "'northern_ireland'"))];
check('M5 the database refuses what the Studio refuses for coverage: "chosen counties" with none, counties with another scope, an unknown scope, publishing no coverage',
  m5.every(Boolean), JSON.stringify(m5));
await L.saveLocation(env, 'ab', L.validateLocation({ country: 'FR' }), 'artist').run();
await L.saveDelivery(env, 'ab', L.validateDelivery({ scope: 'island' }, { country: 'FR' }), 'artist').run();
await db.prepare("DELETE FROM artists WHERE id='ab'").run();
check('M6 deleting an artist (the Studio’s existing erasure) takes their location and coverage with it (ON DELETE CASCADE)',
  (await db.prepare("SELECT (SELECT COUNT(*) FROM artist_locations WHERE artist_id='ab') + (SELECT COUNT(*) FROM artist_delivery WHERE artist_id='ab') n").first()).n === 0);
let again = true; try { await run(MIG); } catch (e) { again = e.message; }
check('R1 running it a second time is harmless (IF NOT EXISTS)', again === true);
const block = s => s.slice(s.indexOf('\n', s.indexOf('-- @@DDL-BEGIN')) + 1, s.indexOf('-- @@DDL-END')).trim();
check('R2 schema.sql carries the migration verbatim for new installs and local tests', readFileSync(HERE + 'schema.sql', 'utf8').includes(block(MIG)));
await mf.dispose();
const sha = execFileSync('sha256sum', [MIG_FILE], { encoding: 'utf8' }).split(' ')[0];
let cls = '';
try { cls = execFileSync('python3', [HERE + '../../atlas-tools/release/studio/migration-check.py', MIG_FILE, sha, NEW.join(','), 'Creates two new, empty tables: artist location (country, county, town) and delivery coverage, and one index; changes no existing table or row.'], { encoding: 'utf8' }); } catch (e) { cls = String(e.stdout || e); }
check('C1 the production migration check accepts it and classes it ADDITIVE', /MIGRATION CHECK OK/.test(cls) && /MIGRATION CLASS: additive/.test(cls), cls.split('\n').filter(l => /REFUSED|CLASS/.test(l)).join(' '));
console.log(`  (migration SHA-256: ${sha})`);
const fail = results.filter(x => !x).length;
console.log(`\nARTIST LOCATION AND DELIVERY · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
