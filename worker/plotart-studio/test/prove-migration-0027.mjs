// PROVE · migration 0027 (delivery and transport: artist_delivery.methods, artist_opportunities.placement_area) on a
// database built with the CURRENT PRODUCTION schema (origin/main, which carries 0026) holding realistic answers, plus:
// the live Studio (origin/main code) keeps working on the migrated database before the new Studio is deployed; the new
// Studio keeps working on an unmigrated database; and the new behaviour (methods, explicit inheritance, independent
// placement transport) on the migrated one. Synthetic artists only; local Miniflare. Nothing touches Cloudflare.
//   node test/prove-migration-0027.mjs
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createRequire } from 'node:module';
import { statements } from './sql.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');

const HERE = new URL('..', import.meta.url).pathname, ROOT = join(HERE, '../..');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const MIG_FILE = HERE + 'migrations/0027_delivery_transport.sql', MIG = readFileSync(MIG_FILE, 'utf8');
const SHA = createHash('sha256').update(readFileSync(MIG_FILE)).digest('hex');
const tmp = mkdtempSync(join(tmpdir(), 'pa-m27-')), MAIN = join(tmp, 'main'), PERSIST = join(tmp, 'd1');
execFileSync('git', ['-C', ROOT, 'worktree', 'add', '-q', '--detach', MAIN, 'origin/main']);
const mainHead = execFileSync('git', ['-C', MAIN, 'rev-parse', '--short', 'HEAD'], { encoding: 'utf8' }).trim();
const prodSchema = readFileSync(join(MAIN, 'worker/plotart-studio/schema.sql'), 'utf8');
console.log(`PROVE · migration 0027 · SHA-256 ${SHA} · production baseline ${mainHead}`);
const T = '2026-11-20T10:00:00.000Z';
const cleanup = () => { try { execFileSync('git', ['-C', ROOT, 'worktree', 'remove', '--force', MAIN]); } catch { /* */ } rmSync(tmp, { recursive: true, force: true }); };
try {
  /* ---- A · the migration on its own (production schema, realistic answers) ---- */
  const M = await import(join(MAIN, 'worker/plotart-studio/test/local.mjs'));
  let { mf, db, url } = await M.start({ port: 8861, persist: PERSIST, schemaSql: prodSchema });
  const seed = async (id, name, loc, del, opp) => {
    await seedPublished(db, { id, slug: id.slice(1) + '-test', email: id.slice(1) + '@example.test', name, works: 1 });
    if (loc) await db.prepare("INSERT INTO artist_locations (artist_id, country, county, town, show_location, show_town, confirmed_at, confirmed_by, updated_at) VALUES (?,?,?,NULL,?,0,?,'artist',?)").bind(id, loc[0], loc[1], loc[2] ? 1 : 0, T, T).run();
    if (del) await db.prepare("INSERT INTO artist_delivery (artist_id, scope, counties, show_delivery, confirmed_at, confirmed_by, updated_at) VALUES (?,?,?,?,?,'artist',?)").bind(id, del[0], JSON.stringify(del[1] || []), del[2] ? 1 : 0, T, T).run();
    if (opp) await db.prepare(`INSERT INTO artist_opportunities (artist_id, interests, artwork_county, transport, coverage_mode, coverage_counties, note, created_at, updated_at, updated_by, care_condition, practical_note, public_display)
      VALUES (?,?,?,?,?,?,NULL,?,?,?,?,?,?)`).bind(id, JSON.stringify(opp.i), opp.c || null, JSON.stringify(opp.t || []), opp.m || null, JSON.stringify(opp.k || []), T, T, id.slice(1) + '@example.test', opp.care ? 1 : 0, opp.note || null, opp.pub ?? null).run();
  };
  // answers as they exist in production: a legacy "none", areas of every kind, a "courier or art transporter" placement,
  // matching general and placement counties, a stored "show once available" tick, care and a private note
  await seed('acork', 'Cork Artist', ['IE', 'Cork', 1], ['counties', ['Cork', 'Kerry'], 1], { i: ['living_gallery'], c: 'Cork', t: ['courier'], m: 'counties', k: ['Cork', 'Kerry'], care: 1, note: 'PRIVATE-NOTE-CORK' });
  await seed('anone', 'None Artist', ['IE', 'Mayo', 0], ['none'], { i: ['exhibitions'], c: 'Mayo', t: ['need_help'] });
  await seed('aroi', 'Republic Artist', ['IE', 'Dublin', 1], ['republic'], { i: ['venues'], c: 'Dublin', t: ['deliver'], m: 'anywhere' });
  await seed('ani', 'Belfast Artist', ['GB', 'Antrim', 1], ['northern_ireland'], { i: ['exhibitions'], c: 'Antrim', t: ['deliver', 'courier'], m: 'ask' });
  await seed('aisl', 'Island Artist', ['IE', 'Sligo', 1], ['island'], null);
  await seed('afr', 'Paris Artist', ['FR', null, 1], ['country'], { i: ['exhibitions'], t: ['deliver'], m: 'counties', k: ['Dublin'] });
  await seed('aun', 'Unanswered Artist', null, null, null);
  const objects = async () => (await db.prepare("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY type, name").all()).results;
  const tables = async () => (await objects()).filter(o => o.type === 'table').map(o => o.name);
  const dump = async names => { const o = {}; for (const t of names) o[t] = (await db.prepare(`SELECT * FROM ${t} ORDER BY rowid`).all()).results; return o; };
  const strip = d => JSON.parse(JSON.stringify(d, (k, v) => (k === 'methods' || k === 'placement_area') ? undefined : v));
  const o0 = await objects(), t0 = await tables(), d0 = await dump(t0);
  const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
  await run(MIG);
  const o1 = await objects(), d1 = await dump(t0);
  check('M1 every existing table, row and value is unchanged; no table, index or trigger is added or removed',
    JSON.stringify(strip(d1)) === JSON.stringify(d0) && JSON.stringify(await tables()) === JSON.stringify(t0)
    && JSON.stringify(o1.filter(o => !['artist_delivery', 'artist_opportunities'].includes(o.name)).map(o => o.name)) === JSON.stringify(o0.filter(o => !['artist_delivery', 'artist_opportunities'].includes(o.name)).map(o => o.name))
    && JSON.stringify(o1.filter(o => !['artist_delivery', 'artist_opportunities'].includes(o.name))) === JSON.stringify(o0.filter(o => !['artist_delivery', 'artist_opportunities'].includes(o.name))));
  const cols = async t => (await db.prepare(`PRAGMA table_info(${t})`).all()).results.map(c => c.name);
  check('M2 exactly two columns are added (artist_delivery.methods, artist_opportunities.placement_area), and every existing row holds NULL in them',
    (await cols('artist_delivery')).at(-1) === 'methods' && (await cols('artist_opportunities')).at(-1) === 'placement_area'
    && d1.artist_delivery.every(r => r.methods === null) && d1.artist_opportunities.every(r => r.placement_area === null)
    && (await cols('artist_delivery')).length === Object.keys(d0.artist_delivery[0]).length + 1 && (await cols('artist_opportunities')).length === Object.keys(d0.artist_opportunities[0]).length + 1);
  let again = 'applied'; try { await run(MIG); } catch { again = 'refused'; }
  check('M3 running it a second time is refused by the database and changes nothing', again === 'refused' && JSON.stringify(await dump(t0)) === JSON.stringify(d1));
  const tryD = async (scope, counties, methods) => { try { await db.prepare('UPDATE artist_delivery SET scope=?, counties=?, show_delivery=0, methods=? WHERE artist_id=?').bind(scope, JSON.stringify(counties), methods, 'aisl').run(); return 'ok'; } catch { return 'refused'; } };
  const allowedArea = ['personal', 'courier', 'specialist', 'personal,courier', 'personal,specialist', 'courier,specialist', 'personal,courier,specialist'];
  const okArea = []; for (const m of allowedArea) okArea.push(await tryD('island', [], m));
  const bad = []; for (const m of ['courier,personal', 'personal,personal', 'bogus', '', 'collection', 'arrangement', '["courier"]', 'personal,courier,specialist,personal']) bad.push(await tryD('island', [], m));
  const none = [await tryD('none', [], 'collection'), await tryD('none', [], 'arrangement'), await tryD('none', [], 'courier'), await tryD('none', [], null)];
  check('M4 the database itself accepts only the permitted transport methods, once each, in the fixed order, and only with a delivery area',
    okArea.every(x => x === 'ok') && bad.every(x => x === 'refused') && none.join() === 'ok,ok,refused,ok', JSON.stringify({ okArea, bad, none }));
  const tryP = async v => { try { await db.prepare('UPDATE artist_opportunities SET placement_area=? WHERE artist_id=?').bind(v, 'acork').run(); return 'ok'; } catch { return 'refused'; } };
  check('M5 placement_area accepts only general, own or NULL', [await tryP('general'), await tryP('own'), await tryP(null), await tryP('same'), await tryP('')].join() === 'ok,ok,ok,refused,refused');
  await db.prepare("UPDATE artist_delivery SET scope='island', counties='[]', methods=NULL WHERE artist_id='aisl'").run();
  await mf.dispose();

  /* ---- C · compatibility: today's live Studio (origin/main) on the migrated database ---- */
  ({ mf, db, url } = await M.start({ port: 8862, persist: PERSIST, schemaSql: null }));
  const callM = async (method, path, email, body) => { const r = await mf.dispatchFetch(url + path, { method, headers: { 'X-Studio': '1', 'Content-Type': 'application/json', 'Cf-Access-Jwt-Assertion': M.token(email) }, body: body === undefined ? undefined : JSON.stringify(body) }); const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* */ } return { s: r.status, j, t }; };
  const c1 = await callM('PUT', '/api/me/delivery', 'cork@example.test', { scope: 'island', show_delivery: false });
  const c2 = await callM('PUT', '/api/opportunities', 'cork@example.test', { interests: ['living_gallery'], artwork_county: 'Cork', transport: ['courier'], coverage: { mode: 'counties', counties: ['Cork'] }, note: null, care_condition: true });
  const c3 = await callM('GET', '/api/admin/opportunities', M.FOUNDER), c4 = await callM('GET', '/api/admin/locations', M.FOUNDER);
  const cr = await db.prepare("SELECT d.methods, o.placement_area FROM artist_delivery d JOIN artist_opportunities o ON o.artist_id = d.artist_id WHERE d.artist_id='acork'").first();
  check('C1 the live Studio keeps working on the migrated database (delivery, Opportunities and both founder views) and never writes the new columns',
    c1.s === 200 && c2.s === 200 && c3.s === 200 && c4.s === 200 && cr.methods === null && cr.placement_area === null, JSON.stringify([c1.s, c2.s, c3.s, c4.s, cr]));
  // put Cork's answers back to the seeded production state for the next part (C1 changed them through the live Studio)
  await db.prepare(`UPDATE artist_delivery SET scope='counties', counties='["Cork","Kerry"]', show_delivery=1 WHERE artist_id='acork'`).run();
  await db.prepare(`UPDATE artist_opportunities SET coverage_mode='counties', coverage_counties='["Cork","Kerry"]' WHERE artist_id='acork'`).run();
  await mf.dispose();
  /* ---- N · the new Studio on an UNMIGRATED database: the new questions stay hidden, everything else works ---- */
  const B = await import(join(HERE, 'test/local.mjs'));
  let s0 = await B.start({ port: 8863, schemaSql: prodSchema });
  await seedPublished(s0.db, { id: 'aold', slug: 'old-test', email: 'old@example.test', name: 'Old Test', works: 1 });
  const callB = (S) => async (method, path, email, body) => { const r = await S.mf.dispatchFetch(S.url + path, { method, headers: { 'X-Studio': '1', 'Content-Type': 'application/json', 'Cf-Access-Jwt-Assertion': B.token(email) }, body: body === undefined ? undefined : JSON.stringify(body) }); const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* */ } return { s: r.status, j, t }; };
  let call = callB(s0);
  await call('PUT', '/api/me/location', 'old@example.test', { country: 'IE', county: 'Clare', town: '', show_location: false, show_town: false });
  const n1 = await call('PUT', '/api/me/delivery', 'old@example.test', { scope: 'counties', counties: ['Clare'] });
  const n2 = await call('PUT', '/api/me/delivery', 'old@example.test', { scope: 'counties', counties: ['Clare'], methods: ['courier'] });
  const n3 = await call('PUT', '/api/opportunities', 'old@example.test', { interests: ['exhibitions'], artwork_county: 'Clare', transport: ['specialist'], coverage: null, note: null });
  const n4 = await call('PUT', '/api/opportunities', 'old@example.test', { interests: ['exhibitions'], artwork_county: 'Clare', transport: ['courier'], coverage: null, placement_area: 'general', note: null });
  const n5 = (await call('GET', '/api/opportunities', 'old@example.test')).j;
  check('N1 the new Studio on a database without 0027: delivery saves as before; methods, specialist transport and placement_area are refused, and the form does not offer them',
    n1.s === 200 && n2.s === 400 && n3.s === 400 && n4.s === 400 && n5.options.v27 === false && !('specialist' in n5.options.transport), JSON.stringify([n1.s, n2.s, n3.s, n4.s]));
  await s0.mf.dispose();

  /* ---- I · the new Studio on the migrated database: methods, explicit inheritance, independent transport ---- */
  s0 = await B.start({ port: 8864, persist: PERSIST, schemaSql: null });
  call = callB(s0); db = s0.db;
  const adm = async () => (await call('GET', '/api/admin/opportunities', B.FOUNDER)).j;
  let v = await adm(); const it = id => v.items.find(i => i.id === id);
  check('I1 nothing is inferred from matching answers: an artist whose placement counties equal their general counties is not "Same as general" (placement_area stays NULL, shown as not yet confirmed)',
    it('acork').prefs.placement_area === null && it('acork').prefs.coverage_counties.join() === it('acork').general.counties.join() && it('acork').general.methods === null);
  check('I2 unanswered, legacy "none" (before the split) and every area keep their meaning; the founder sees the legacy answer as needing confirmation',
    it('aun').general === null && it('anone').general.scope === 'none' && it('anone').general.methods === null && /answered before/.test(it('anone').general.line)
    && it('aroi').general.counties.length === 26 && it('ani').general.counties.length === 6 && it('aisl').general.counties.length === 32 && it('afr').general.counties.length === 0 && /France/.test(it('afr').general.line));
  // D · general delivery: three different "no area" answers, and how a work travels
  const dl = async (email, body) => call('PUT', '/api/me/delivery', email, body);
  const d1x = await dl('none@example.test', { scope: 'none', methods: ['arrangement'] });
  const d2x = await dl('none@example.test', { scope: 'none', methods: ['courier'] });
  const d3x = await dl('none@example.test', { scope: 'none' });
  const d4x = await dl('isl@example.test', { scope: 'island', methods: ['specialist', 'personal', 'courier'] });
  const d5x = await dl('isl@example.test', { scope: 'island', methods: ['courier', 'courier'] });
  const d6x = await dl('isl@example.test', { scope: 'island', methods: ['van'] });
  const d7x = await dl('isl@example.test', { scope: 'island', methods: [] });
  check('D1 "No delivery", "By arrangement" and unanswered are three different answers; how the work travels is validated (permitted values, once each, stored in a fixed order)',
    d1x.s === 200 && d1x.j.delivery.methods === 'arrangement' && d2x.s === 400 && d3x.s === 400 && d4x.s === 200 && d4x.j.delivery.methods === 'personal,courier,specialist'
    && d5x.s === 400 && d6x.s === 400 && d7x.s === 400, JSON.stringify([d1x.s, d2x.s, d3x.s, d4x.s, d5x.s, d6x.s, d7x.s]));
  const pubTick = await dl('isl@example.test', { scope: 'island', methods: ['courier'], show_delivery: true });
  const corkShow0 = (await db.prepare("SELECT show_delivery FROM artist_delivery WHERE artist_id='acork'").first()).show_delivery;
  await dl('cork@example.test', { scope: 'counties', counties: ['Cork', 'Kerry'], methods: ['personal'] });
  const corkShow1 = (await db.prepare("SELECT show_delivery FROM artist_delivery WHERE artist_id='acork'").first()).show_delivery;
  await dl('cork@example.test', { scope: 'counties', counties: ['Cork', 'Kerry'], methods: ['personal'], show_delivery: false });
  const corkShow2 = (await db.prepare("SELECT show_delivery FROM artist_delivery WHERE artist_id='acork'").first()).show_delivery;
  check('D2 a public-delivery tick can no longer be given (only withdrawn); an earlier tick is kept as it is until the artist withdraws it',
    pubTick.s === 400 && corkShow0 === 1 && corkShow1 === 1 && corkShow2 === 0);
  // T · placement transport: standard courier and specialist art transport are separate; invalid, duplicate and clashing refused
  const op = (email, body) => call('PUT', '/api/opportunities', email, { interests: ['exhibitions'], artwork_county: null, note: null, ...body });
  const t1 = await op('isl@example.test', { transport: ['deliver', 'courier', 'specialist'], coverage: { mode: 'counties', counties: ['Sligo'] }, placement_area: 'own' });
  const t2 = await op('isl@example.test', { transport: ['specialist', 'specialist'], coverage: null, placement_area: 'own' });
  const t3 = await op('isl@example.test', { transport: ['specialist', 'need_help'], coverage: null, placement_area: 'own' });
  const t4 = await op('isl@example.test', { transport: ['lorry'], coverage: null, placement_area: 'own' });
  const t5 = await op('isl@example.test', { transport: ['depends', 'courier'], coverage: null, placement_area: 'own' });
  const tr = JSON.parse((await db.prepare("SELECT transport FROM artist_opportunities WHERE artist_id='aisl'").first()).transport);
  check('T1 placement transport: personal delivery, standard courier and specialist art transport are stored as separate answers; duplicates, unknown and clashing answers are refused',
    t1.s === 200 && tr.join() === 'deliver,courier,specialist' && [t2.s, t3.s, t4.s, t5.s].every(s => s === 400), JSON.stringify([t1.s, t2.s, t3.s, t4.s, t5.s, tr]));
  // the founder's example: courier anywhere on the island for sales; personal delivery in two counties for placements
  await dl('isl@example.test', { scope: 'island', methods: ['courier'] });
  await op('isl@example.test', { transport: ['deliver'], coverage: { mode: 'counties', counties: ['Leitrim', 'Sligo'] }, placement_area: 'own' });
  v = await adm();
  check('T2 the founder’s example: sales by standard courier anywhere on the island; placements delivered personally in Sligo and Leitrim only',
    it('aisl').general.how === 'By standard courier' && it('aisl').general.counties.length === 32 && it('aisl').prefs.transport.join() === 'deliver' && it('aisl').prefs.coverage_counties.join() === 'Leitrim,Sligo');
  // I · explicit inheritance: chosen, preserved underneath, restored, and followed for every geographical scope
  const g1 = await op('cork@example.test', { interests: ['living_gallery'], transport: ['courier'], placement_area: 'general' });
  const st1 = await db.prepare("SELECT coverage_mode, coverage_counties, placement_area FROM artist_opportunities WHERE artist_id='acork'").first();
  check('I3 choosing "Same as my general delivery" is recorded explicitly and keeps the artist’s own placement area untouched underneath',
    g1.s === 200 && st1.placement_area === 'general' && st1.coverage_mode === 'counties' && st1.coverage_counties === '["Cork","Kerry"]', JSON.stringify([g1.s, st1]));
  await dl('cork@example.test', { scope: 'republic', methods: ['personal'] });
  v = await adm();
  const corkOwn = await db.prepare("SELECT coverage_counties FROM artist_opportunities WHERE artist_id='acork'").first();
  check('I4 while inheriting, a Profile change applies to placements (now the Republic, 26 counties) and still never overwrites the own area',
    it('acork').prefs.placement_area === 'general' && it('acork').general.counties.length === 26 && corkOwn.coverage_counties === '["Cork","Kerry"]');
  const sv = (await call('GET', '/api/opportunities', 'cork@example.test')).j.saved;
  const g2 = await op('cork@example.test', { interests: ['living_gallery'], transport: ['courier'], placement_area: 'own', coverage: { mode: sv.coverage_mode, counties: sv.coverage_counties } });
  const st2 = await db.prepare("SELECT coverage_mode, coverage_counties, placement_area FROM artist_opportunities WHERE artist_id='acork'").first();
  check('I5 choosing "A different area" again restores the earlier own area exactly (Cork and Kerry)', g2.s === 200 && st2.placement_area === 'own' && st2.coverage_counties === '["Cork","Kerry"]');
  const noneG = await op('none@example.test', { transport: ['deliver'], placement_area: 'general' });
  const unG = await op('un@example.test', { transport: ['deliver'], placement_area: 'general' });
  const helpG = await op('isl@example.test', { transport: ['need_help'], placement_area: 'general' });
  const mixG = await op('isl@example.test', { transport: ['deliver'], placement_area: 'general', coverage: { mode: 'anywhere' } });
  check('I6 inheritance needs a general delivery area: refused with "By arrangement", with no answer, without a way to move the work, or together with a different area',
    [noneG.s, unG.s, helpG.s, mixG.s].every(s => s === 400), JSON.stringify([noneG.s, unG.s, helpG.s, mixG.s]));
  const scopes = [['roi@example.test', 'aroi', 26], ['ni@example.test', 'ani', 6], ['isl@example.test', 'aisl', 32], ['fr@example.test', 'afr', 0], ['cork@example.test', 'acork', 26]];
  for (const [e, id] of scopes) {
    const g = (await db.prepare('SELECT scope, counties FROM artist_delivery WHERE artist_id=?').bind(id).first());
    if (!(await db.prepare('SELECT methods FROM artist_delivery WHERE artist_id=?').bind(id).first()).methods) await dl(e, { scope: g.scope, counties: JSON.parse(g.counties), methods: ['courier'] });
    await op(e, { transport: ['deliver'], placement_area: 'general' });
  }
  v = await adm();
  check('I7 every geographical scope is followed exactly: Republic 26, Northern Ireland 6, whole island 32, an artist abroad (France) no Irish county but their own country',
    scopes.every(([, id, n]) => it(id).prefs.placement_area === 'general' && it(id).general.counties.length === n) && /France/.test(it('afr').general.line), JSON.stringify(scopes.map(([, id]) => [id, it(id).general && it(id).general.counties.length])));
  const frOwn = await db.prepare("SELECT coverage_mode, coverage_counties FROM artist_opportunities WHERE artist_id='afr'").first();
  check('I8 the overseas artist’s own placement area (Dublin) is kept underneath while they follow their general delivery', frOwn.coverage_mode === 'counties' && frOwn.coverage_counties === '["Dublin"]');
  // founder filters on the migrated data (browser)
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': B.token(B.FOUNDER) } });
  const pg = await ctx.newPage(); await pg.goto(s0.url + '/admin/opportunities', { waitUntil: 'networkidle' }); await pg.waitForSelector('#of-how');
  const names = async () => (await pg.locator('#of-list > li').allInnerTexts()).map(t => t.split('\n')[0].replace(/\s*·.*$/, '').trim()).filter(n => /Artist$/.test(n)).sort().join();
  await pg.selectOption('#of-reach', 'general'); const fGen = await names();
  await pg.selectOption('#of-reach', 'Kerry'); const fKerry = await names();
  await pg.selectOption('#of-reach', ''); await pg.selectOption('#of-gen', '_arrangement'); const fArr = await names();
  await pg.selectOption('#of-gen', ''); await pg.selectOption('#of-how', 'specialist'); const fSpec = await names();
  check('F1 founder filters on the migrated data: "same as their general delivery", placement counties through inheritance (Kerry: Republic followers), "by arrangement" and "how: specialist"',
    fGen === 'Belfast Artist,Cork Artist,Island Artist,Paris Artist,Republic Artist' && fKerry === 'Cork Artist,Island Artist,Republic Artist' && fArr === 'None Artist' && fSpec === '',
    JSON.stringify({ fGen, fKerry, fArr, fSpec }));
  await ctx.close();
  // artist UI: choosing "Same as" and back restores the own area on screen
  const actx = await b.newContext({ viewport: { width: 1200, height: 1000 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': B.token('fr@example.test') } });
  const ap = await actx.newPage(); await ap.goto(s0.url + '/#/opportunities', { waitUntil: 'networkidle' }); await ap.waitForTimeout(800);
  const genPressed = await ap.locator('[data-g="a"][data-k="general"]').getAttribute('aria-pressed');
  await ap.click('[data-g="a"][data-k="own"]'); await ap.waitForTimeout(150);
  const restored = await ap.locator('#o-own .st-opt--sm[aria-pressed="true"]').allInnerTexts();
  await ap.click('#o-save'); await ap.waitForTimeout(600);
  const frAfter = await db.prepare("SELECT placement_area, coverage_counties FROM artist_opportunities WHERE artist_id='afr'").first();
  check('F2 on screen: "Same as my general delivery" is shown as chosen; choosing "A different area" brings back Dublin; saving records it',
    genPressed === 'true' && restored.join() === 'Dublin' && frAfter.placement_area === 'own' && frAfter.coverage_counties === '["Dublin"]', JSON.stringify({ genPressed, restored, frAfter }));
  await actx.close(); await b.close();
  const priv = JSON.stringify((await call('GET', '/api/pipeline/hire-catalogue', null, undefined)).j) + JSON.stringify((await call('GET', '/api/admin/locations', 'cork@example.test')).j);
  check('P1 private answers stay private after the migration: the private note is never readable outside the founder’s view', !/PRIVATE-NOTE-CORK/.test(priv));
  await s0.mf.dispose();
} finally { cleanup(); }
console.log(`\n${results.filter(Boolean).length}/${results.length} passed`);
process.exit(results.every(Boolean) ? 0 : 1);
