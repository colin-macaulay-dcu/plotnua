// PROVE · artist location and delivery coverage in the Studio (Phase C): the artist's two answers, the founder's overview,
// and the Studio before migration 0025. Synthetic artists only; local Miniflare D1. Nothing here touches Cloudflare.
//   node test/prove-location-studio.mjs
import { execFileSync } from 'node:child_process';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';

const HERE = new URL('..', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const mkcall = (mf, url) => async (method, path, email, body) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json' };
  if (email) h['Cf-Access-Jwt-Assertion'] = token(email);
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ }
  return { s: r.status, j, t };
};
console.log('PROVE · artist location and delivery coverage in the Studio (Phase C)');

/* ---- before migration 0025 (production today): nothing changes ---- */
{
  const before = execFileSync('git', ['-C', HERE, 'show', 'dac259f5:worker/plotart-studio/schema.sql'], { encoding: 'utf8' });
  const { mf, url, db } = await start({ port: 8891, schemaSql: before });
  const call = mkcall(mf, url);
  await seedPublished(db, { id: 'azed', slug: 'zed-test', email: 'zed@example.test', name: 'Zed Test', works: 1, number: 2 });
  const me = await call('GET', '/api/me', 'zed@example.test'), g = await call('GET', '/api/me/location', 'zed@example.test');
  const put = await call('PUT', '/api/me/location', 'zed@example.test', { country: 'IE', county: 'Cork' });
  const old = await call('PUT', '/api/me/profile', 'zed@example.test', { county: 'Kerry', county_public: true });
  const fo = await call('GET', '/api/admin/locations', FOUNDER);
  check('S0 before migration 0025: no location cards, saving is refused politely, the existing county field works exactly as today, the founder list is empty',
    me.j.location_available === false && g.j.installed === false && put.s === 503 && old.s === 200
    && (await db.prepare("SELECT county, county_public FROM artists WHERE id='azed'").first()).county === 'Kerry' && fo.s === 200 && fo.j.installed === false);
  await mf.dispose();
}

/* ---- with migration 0025 ---- */
const { mf, url, db } = await start({ port: 8892 });
const call = mkcall(mf, url);
await seedPublished(db, { id: 'akay', slug: 'kay-test', email: 'kay@example.test', name: 'Kay Test', works: 1, number: 1 });
await seedPublished(db, { id: 'acor', slug: 'cor-test', email: 'cor@example.test', name: 'Cor Test', works: 1, number: 2 });
await seedPublished(db, { id: 'apar', slug: 'par-test', email: 'par@example.test', name: 'Par Test', works: 1, number: 3 });
await db.prepare("UPDATE artists SET county='Kerry', county_public=0 WHERE id='akay'").run();
const g0 = await call('GET', '/api/me/location', 'kay@example.test');
check('S1 the Studio offers both cards; an existing artist starts from their current profile county, with nothing saved until they choose',
  g0.s === 200 && g0.j.installed && g0.j.location === null && g0.j.profile_county === 'Kerry' && g0.j.counties.length === 32 && g0.j.countries.length > 240
  && (await db.prepare('SELECT COUNT(*) n FROM artist_locations').first()).n === 0);
const k1 = await call('PUT', '/api/me/location', 'kay@example.test', { country: 'IE', county: 'Kerry', town: 'Dingle', show_location: true, show_town: true });
const kay = await db.prepare("SELECT county, county_public FROM artists WHERE id='akay'").first();
check('S2 confirming a location stores it and keeps the existing profile county in step (so today’s publishing is unchanged)',
  k1.s === 200 && k1.j.location.county === 'Kerry' && k1.j.location.town === 'Dingle' && kay.county === 'Kerry' && kay.county_public === 1);
const bad = await call('PUT', '/api/me/location', 'kay@example.test', { country: 'IE', county: 'Kerry', town: '4 Strand Street' });
check('S3 an address is refused with a plain message and nothing changes', bad.s === 400 && /never your address/.test(bad.j.error)
  && (await db.prepare("SELECT town FROM artist_locations WHERE artist_id='akay'").first()).town === 'Dingle');
await call('PUT', '/api/me/location', 'par@example.test', { country: 'FR', town: 'Paris', show_location: true });
const par = await db.prepare("SELECT county, county_public FROM artists WHERE id='apar'").first();
check('S4 an artist based abroad: country only, and the profile county is cleared (never a wrong Irish county)', par.county === null && par.county_public === 0);
await call('PUT', '/api/me/location', 'cor@example.test', { country: 'IE', county: 'Cork', show_location: true });
const d1 = await call('PUT', '/api/me/delivery', 'cor@example.test', { scope: 'counties', counties: ['Kerry', 'Limerick'], show_delivery: true });
const corLoc = await db.prepare("SELECT * FROM artist_locations WHERE artist_id='acor'").first();
check('S5 delivery coverage is saved on its own and never changes where the artist is based', d1.s === 200 && d1.j.delivery.counties === '["Kerry","Limerick"]' && corLoc.county === 'Cork');
const d2 = await call('PUT', '/api/me/delivery', 'cor@example.test', { scope: 'country' });
const d3 = await call('PUT', '/api/me/delivery', 'par@example.test', { scope: 'island', show_delivery: true });
check('S6 "anywhere in my own country" is refused for an artist on the island; an artist in Paris may cover the whole island', d2.s === 400 && d3.s === 200 && d3.j.delivery.scope === 'island');
const f1 = await call('GET', '/api/admin/locations?county=Kerry', FOUNDER);
const rel = Object.fromEntries(f1.j.artists.map(a => [a.slug, a.relation]));
check('S7 the founder’s overview filtered by Kerry: the Kerry artist is "based"; Cork (Kerry chosen) and Paris (whole island) are "delivers"',
  f1.s === 200 && rel['kay-test'] === 'based' && rel['cor-test'] === 'delivers' && rel['par-test'] === 'delivers', JSON.stringify(rel));
const all = await call('GET', '/api/admin/locations', FOUNDER);
const kayRow = all.j.artists.find(a => a.slug === 'kay-test'), corRow = all.j.artists.find(a => a.slug === 'cor-test');
check('S8 the overview shows each artist’s place and coverage as plain lines', kayRow.place === 'Dingle, Co. Kerry, Ireland' && corRow.delivery === 'Delivers to Co. Kerry, Co. Limerick' && corRow.delivery_public === true);
const art = await call('GET', '/api/admin/locations', 'kay@example.test'), unk = await call('GET', '/api/admin/locations?county=Atlantis', FOUNDER);
check('S9 only the founder can see the overview; an unknown county is refused', art.s === 403 && unk.s === 400);
const au = (await db.prepare("SELECT action, detail FROM audit WHERE action IN ('location','delivery') ORDER BY id").all()).results;
check('S10 every save is in the audit log, without the town itself (only whether one was given)', au.length >= 5 && au.every(r => !/Dingle|Paris/.test(r.detail || '')), JSON.stringify(au).slice(0, 300));
/* ---- the public profile: the confirmed public location, never an address ---- */
await db.prepare("UPDATE artists SET practice='Painter' WHERE id IN ('akay','acor')").run();
const pv = await call('GET', '/preview/', 'kay@example.test');
const meta = (pv.t.match(/<p class="pa-ag-meta">([^<]*)<\/p>/) || [])[1];
check('P1 the gallery page shows the confirmed public location under the name: "Painter · Dingle, Co. Kerry, Ireland"', meta === 'Painter · Dingle, Co. Kerry, Ireland', meta);
await call('PUT', '/api/me/location', 'cor@example.test', { country: 'IE', county: 'Cork', show_location: false });
const pv2 = await call('GET', '/preview/', 'cor@example.test');
check('P2 when the artist does not show their location, no place appears at all (and coverage is never on the profile)',
  ((pv2.t.match(/<p class="pa-ag-meta">([^<]*)<\/p>/) || [])[1]) === 'Painter' && !/Limerick|Delivers/.test(pv2.t));
const py = (code, input) => execFileSync('python3', ['-c', `import sys, json; sys.path.insert(0, ${JSON.stringify(HERE + '../../atlas-tools')}); ${code}`], { input: JSON.stringify(input), encoding: 'utf8' });
const base = JSON.parse(execFileSync('cat', [HERE + '../../plotart/artists/leah-hewson/gallery.json'], { encoding: 'utf8' })).artist;
const pv3 = JSON.parse(py('import plotart_gallery as G\nd=json.load(sys.stdin)\nout=[]\nfor a in d:\n    try:\n        G.validate_export({"schema": G.SCHEMA, "artist": dict({"slug": "sample-artist", "display_name": "Sample Artist", "founding": False, "practice": "Painter", "medium": "painting", "county": None, "county_public": False, "statement": None, "bio": "A synthetic biography used only to check the export rules, long enough to be valid.", "website": None, "instagram": None, "portrait": None}, **{k: v for k, v in a.items() if k in ("location", "exhibitions")}), "works": []}); out.append("ok")\n    except Exception as e: out.append(type(e).__name__+":"+str(e)[:50])\nprint(json.dumps(out))',
  [{ ...base, location: { country: 'IE', county: 'Kerry', town: 'Dingle', line: 'Dingle, Co. Kerry, Ireland' } }, { ...base, location: { country: 'IE', county: 'Kerry', line: '4 Strand St, Dingle' } },
   { ...base, location: { country: 'IE', county: 'Kerry', line: 'Co. Kerry, Ireland', scope: 'island' } }]));
check('P3 the publisher accepts only the public view: an address-like line or any extra field (e.g. delivery) is refused',
  !/location/.test(pv3[0]) && !/not a plotnua/.test(pv3[0]) && /^Refused:location/.test(pv3[1]) && /^Refused:location/.test(pv3[2]), JSON.stringify(pv3));
const n = s => { const m = s.match(/^(\d{4})_/); return m && m[1]; };
const files = execFileSync('ls', [HERE + 'migrations'], { encoding: 'utf8' }).split('\n').filter(f => /^\d{4}_.*\.sql$/.test(f) && !f.endsWith('_rollback.sql'));
const nums = files.map(n), dup = nums.filter((x, i) => nums.indexOf(x) !== i);
check('N1 every migration number is used once (0024 Spaces, 0025 location and delivery, 0026 Exhibitions & Achievements)',
  !dup.length && ['0024_spaces_identifier.sql', '0025_artist_locations.sql', '0026_artist_exhibitions.sql'].every(f => files.includes(f)) && !files.some(f => /achievements/.test(f)), JSON.stringify(dup));
await mf.dispose();

const fail = results.filter(x => !x).length;
console.log(`\nLOCATION AND DELIVERY · STUDIO · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
