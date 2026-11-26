// PROVE · PlotArt Studio · Report 35 (26 Nov 2026): one public-location consent, no private county in the export,
// unanswered general delivery distinct from "No delivery", general delivery vs temporary placements kept independent
// (offered only as an editable starting point), founder filters that keep the three questions apart, and the link to
// PlotArt's Art Services & Providers. Synthetic artists only; local Worker. Nothing here touches Cloudflare.
//   node test/prove-report35.mjs
import { createRequire } from 'node:module';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
import * as L from '../src/lib.js';
const require = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
console.log('PROVE · PlotArt Studio · Report 35 (delivery, transport and location consent)');
const { mf, url, db } = await start({ port: 8851 });
const call = async (method, path, email, body) => {
  const r = await mf.dispatchFetch(url + path, { method, headers: { 'X-Studio': '1', 'Content-Type': 'application/json', 'Cf-Access-Jwt-Assertion': token(email) }, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ }
  return { s: r.status, j, t };
};
const A = 'ann@example.test', B = 'ben@example.test', C = 'cal@example.test', D = 'dee@example.test';
await seedPublished(db, { id: 'aann', slug: 'ann-test', email: A, name: 'Ann Test', works: 1 });
await seedPublished(db, { id: 'aben', slug: 'ben-test', email: B, name: 'Ben Test', works: 1 });
await seedPublished(db, { id: 'acal', slug: 'cal-test', email: C, name: 'Cal Test', works: 1 });
await seedPublished(db, { id: 'adee', slug: 'dee-test', email: D, name: 'Dee Test', works: 1 });
const art = id => db.prepare('SELECT county, county_public FROM artists WHERE id=?').bind(id).first();
const loc = id => db.prepare('SELECT * FROM artist_locations WHERE artist_id=?').bind(id).first();
const opp = id => db.prepare('SELECT * FROM artist_opportunities WHERE artist_id=?').bind(id).first();

/* E · the export never carries a county that isn't public */
const snapPub = { artist: { slug: 's', display_name: 'S', founding: false, practice: null, medium: null, county: 'Sligo', county_public: true, statement: null, bio: 'x'.repeat(40), website: null, instagram: null, portrait: null }, works: [] };
const snapPriv = { ...snapPub, artist: { ...snapPub.artist, county_public: false } };
const opts = { version: 1, approvedAt: '2026-11-26T10:00:00.000Z', licenceVersion: 'PA-GPIL-2026-10-29', licenceAcceptedAt: '2026-11-26T10:00:00.000Z', artistId: 'as' };
const ePub = L.exportGallery(snapPub, opts), ePriv = L.exportGallery(snapPriv, opts);
check('E1 a public county is exported as today', ePub.artist.county === 'Sligo' && ePub.artist.county_public === true && ePub.artist.bio === 'x'.repeat(40));
check('E2 a county that is not public never leaves the Studio (null in the export package)', ePriv.artist.county === null && ePriv.artist.county_public === false && !JSON.stringify(ePriv).includes('Sligo'));

/* C · one public-location consent */
await db.prepare("UPDATE artists SET county='Galway', county_public=1 WHERE id='aann'").run();   // an earlier, valid "Show my county"
let r = await call('GET', '/api/me/location', A);
check('C1 existing consent is preserved: an artist who chose "Show my county" before has it as their starting point, and nothing else is inferred',
  r.j.profile_county === 'Galway' && r.j.profile_county_public === true && r.j.location === null && r.j.consent_conflict === false, r.t);
await db.prepare("UPDATE artists SET county='Mayo', county_public=0 WHERE id='aben'").run();
r = await call('GET', '/api/me/location', B);
check('C2 a private county stays private: nothing is pre-ticked', r.j.profile_county_public === false);
// a conflict: the newer answer says show, the older says don't (written directly, as an older client could have)
await call('PUT', '/api/me/location', C, { country: 'IE', county: 'Kerry', town: '', show_location: true, show_town: false });
await db.prepare("UPDATE artists SET county_public=0 WHERE id='acal'").run();
r = await call('GET', '/api/me/location', C);
const prevC = await call('GET', '/preview/', C);
check('C3 where the two answers disagree, the more private one applies until the artist confirms: the preview shows no county, and the artist is asked',
  r.j.consent_conflict === true && !/Kerry/.test(prevC.t), JSON.stringify({ c: r.j.consent_conflict, has: /Kerry/.test(prevC.t) }));
await call('PUT', '/api/me/location', C, { country: 'IE', county: 'Kerry', town: '', show_location: true, show_town: false });
r = await call('GET', '/api/me/location', C);
const prevC2 = await call('GET', '/preview/', C);
check('C4 confirming in "Where you\'re based" sets both answers together; the county shows again', r.j.consent_conflict === false && (await art('acal')).county_public === 1 && /Kerry/.test(prevC2.t));
r = await call('PUT', '/api/me/profile', C, { county_public: false });
check('C5 the older "show my county" switch (still accepted from older pages) now changes both answers together, so they can never disagree again',
  r.s === 200 && (await art('acal')).county_public === 0 && (await loc('acal')).show_location === 0 && (await call('GET', '/api/me/location', C)).j.consent_conflict === false);
r = await call('PUT', '/api/me/profile', C, { county: 'Cork' });
check('C6 once a location is confirmed, the older route cannot move the county away from it', r.s === 409 && (await art('acal')).county === 'Kerry');
r = await call('PUT', '/api/me/profile', B, { county: 'Sligo', county_public: true });
check('C7 an artist who has not confirmed a location yet keeps the earlier behaviour (no change for them)', r.s === 200 && (await art('aben')).county === 'Sligo');

/* G · general delivery: unanswered is not "No delivery" */
r = await call('PUT', '/api/me/delivery', A, { counties: [] });
check('G1 saving general delivery without an answer is refused: no answer is never recorded as "No delivery"', r.s === 400 && !(await db.prepare("SELECT 1 FROM artist_delivery WHERE artist_id='aann'").first()), r.t);
r = await call('PUT', '/api/me/delivery', B, { scope: 'none' });
check('G2 "No delivery: collection or by arrangement" is an explicit, recorded answer', r.s === 200 && (await db.prepare("SELECT scope FROM artist_delivery WHERE artist_id='aben'").first()).scope === 'none');
await call('PUT', '/api/me/location', A, { country: 'IE', county: 'Galway', town: '', show_location: true, show_town: false });
r = await call('PUT', '/api/me/delivery', A, { scope: 'republic', show_delivery: false });
check('G3 every geographical option is kept (here: anywhere in the Republic)', r.s === 200 && r.j.delivery.scope === 'republic');

/* O · temporary placements: an editable starting point, never a link */
r = await call('GET', '/api/opportunities', A);
check('O1 Opportunities shows the artist’s general delivery for reference, with the Art Services & Providers link', r.j.general && /Republic of Ireland/.test(r.j.general.line) && r.j.general.counties.length === 26
  && r.j.services_url === 'https://plotnua.ie/plotart/services.html', r.t);
r = await call('GET', '/api/opportunities', D);
check('O2 with no general delivery answer, nothing is offered', r.j.general === null);
check('O3 viewing never copies anything: no placement answer exists until the artist saves', !(await opp('aann')));
// the artist saves placements independently: personal delivery in two counties only, while general delivery is the Republic
await call('PUT', '/api/opportunities', A, { interests: ['living_gallery'], artwork_county: 'Galway', transport: ['deliver'], coverage: { mode: 'counties', counties: ['Galway', 'Mayo'] }, note: null });
await call('PUT', '/api/me/delivery', A, { scope: 'island', show_delivery: false });
const oa = await opp('aann');
check('O4 a later change to general delivery never changes the placement answer (Republic → whole island; placements stay Galway and Mayo, personal delivery)',
  oa.coverage_mode === 'counties' && oa.coverage_counties === JSON.stringify(['Galway', 'Mayo']) && oa.transport === JSON.stringify(['deliver']));
await call('PUT', '/api/opportunities', A, { interests: ['living_gallery'], artwork_county: 'Galway', transport: ['deliver'], coverage: { mode: 'anywhere' }, note: null });
check('O5 and a placement change never changes general delivery', (await db.prepare("SELECT scope FROM artist_delivery WHERE artist_id='aann'").first()).scope === 'island');

/* F · founder: three questions kept apart; UI: the starting point */
await call('PUT', '/api/opportunities', B, { interests: ['exhibitions'], artwork_county: 'Mayo', transport: ['courier'], coverage: { mode: 'counties', counties: ['Cork'] }, note: null });
await call('PUT', '/api/me/location', D, { country: 'IE', county: 'Cork', town: '', show_location: false, show_town: false });
await call('PUT', '/api/me/delivery', D, { scope: 'counties', counties: ['Cork', 'Kerry'], show_delivery: false });
await call('PUT', '/api/opportunities', D, { interests: ['venues'], artwork_county: 'Cork', transport: ['need_help'], coverage: null, note: null });
const v = (await call('GET', '/api/admin/opportunities', FOUNDER)).j;
const it = id => v.items.find(i => i.id === id);
check('F1 the founder data carries general delivery separately from placement answers (and unanswered stays unanswered)',
  v.general_installed === true && /island of Ireland/.test(it('aann').general.line) && it('aben').general.scope === 'none' && it('acal').general === null && it('adee').general.counties.join() === 'Cork,Kerry');
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
const pg = await ctx.newPage();
await pg.goto(url + '/admin/opportunities', { waitUntil: 'networkidle' }); await pg.waitForSelector('#of-gen');
const names = async () => (await pg.locator('#of-list > li').allInnerTexts()).map(t => t.split('\n')[0].replace(/\s*·.*$/, '').trim()).filter(n => /Test$/.test(n)).sort().join();
await pg.selectOption('#of-gen', 'Cork'); const genCork = await names();
await pg.selectOption('#of-gen', ''); await pg.selectOption('#of-reach', 'Cork'); const plCork = await names();
await pg.selectOption('#of-reach', ''); await pg.selectOption('#of-tr', 'need_help'); const help = await names();
await pg.selectOption('#of-tr', ''); await pg.selectOption('#of-gen', '_none'); const none = await names();
await pg.selectOption('#of-gen', '_unanswered'); const unans = await names();
const annRow = await pg.locator('#of-list > li', { hasText: 'Ann Test' }).innerText().catch(() => '');
check('F2 "General delivery to Cork" (sales and hire) and "Placements: deliver & collect in Cork" give different, correct answers',
  genCork === 'Ann Test,Dee Test' && plCork === 'Ann Test,Ben Test', JSON.stringify({ genCork, plCork }));
check('F3 transport is its own filter (needs help arranging transport)', help === 'Dee Test', help);
check('F4 "No delivery" and "Not answered" are separate filters', none === 'Ben Test' && unans === 'Cal Test', JSON.stringify({ none, unans }));
await pg.selectOption('#of-gen', '');
const annRow2 = await pg.locator('#of-list > li', { hasText: 'Ann Test' }).innerText();
check('F5 each artist’s row labels the three answers separately', /Artwork kept in: Co. Galway/.test(annRow2) && /Placements, deliver & collect: Anywhere on the island/.test(annRow2)
  && /Placements, transport: Delivers/.test(annRow2) && /General delivery \(sales & hire\): Delivers anywhere on the island of Ireland/.test(annRow2), annRow2);
await ctx.close();
// artist UI: the starting point copies once, editable; nothing is saved until "Save preferences"
await call('PUT', '/api/me/delivery', A, { scope: 'counties', counties: ['Clare', 'Galway', 'Limerick'], show_delivery: false });
const actx = await b.newContext({ viewport: { width: 1200, height: 1000 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(A) } });
const ap = await actx.newPage();
await ap.goto(url + '/#/opportunities', { waitUntil: 'networkidle' }); await ap.waitForTimeout(800);
const covText = await ap.locator('#o-cov-card').innerText();
await ap.click('#o-from-gen'); await ap.waitForTimeout(200);
const pressed = await ap.locator('#o-cov-card .st-opt[aria-pressed="true"]').allInnerTexts();
const msgT = await ap.locator('#o-c-msg').innerText();
const before = await opp('aann');
check('F6 the artist sees their general delivery and can start from it; the copy is editable and nothing is saved by copying',
  /general delivery to buyers and hirers/i.test(covText) && pressed.sort().join() === 'Clare,Galway,Limerick' && /starting point/.test(msgT) && before.coverage_mode === 'anywhere', JSON.stringify({ pressed, msgT }));
await ap.click('#o-cov-card .st-opt[data-k="Limerick"]'); await ap.click('#o-save'); await ap.waitForTimeout(600);
const after = await opp('aann');
check('F7 after editing the copy and saving, placements hold the artist’s own choice (Clare, Galway); general delivery is unchanged',
  after.coverage_counties === JSON.stringify(['Clare', 'Galway']) && (await db.prepare("SELECT counties FROM artist_delivery WHERE artist_id='aann'").first()).counties === JSON.stringify(['Clare', 'Galway', 'Limerick']), after.coverage_counties);
const trText = await ap.locator('#o-tr-card').innerText();
const link = await ap.locator('#o-tr-card a').getAttribute('href');
check('F8 transport for placements is explained separately from sending a sold work, with a simple link to Art Services & Providers (no booking, quote or charge)',
  /separate from how you send a sold or hired work/.test(trText) && link === 'https://plotnua.ie/plotart/services.html' && !/book|quote|£|€/i.test(trText.replace(/Any arrangement or quote is between you and them\./, '')), trText);
const kept = await ap.locator('label[for="o-county"]').innerText(); const kh = await ap.locator('#o-county-h').innerText();
check('F9 artwork location is "where it is kept", private, and distinct from where the artist is based', /kept/.test(kept) && /Private/.test(kh) && /where you’re based/.test(kh));
await actx.close();
// artist UI: general delivery unanswered → nothing pre-selected
const dctx = await b.newContext({ viewport: { width: 1200, height: 1000 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(C) } });
const dp = await dctx.newPage(); await dp.goto(url + '/#/profile', { waitUntil: 'networkidle' }); await dp.waitForTimeout(900);
const checkedScope = await dp.locator('input[name="del-scope"]:checked').count();
const delText = await dp.locator('#del-card').innerText();
check('F10 the Profile shows general delivery as "Not answered yet" with nothing pre-selected', checkedScope === 0 && /Not answered yet/.test(delText) && /Delivering to buyers and hirers/.test(delText), delText);
await dctx.close(); await b.close();
await mf.dispose();
console.log(`\n${results.filter(Boolean).length}/${results.length} passed`);
process.exit(results.every(Boolean) ? 0 : 1);
