// Previews only (not a proof): Report 36 screens on a database with migration 0027 — general delivery (where and how;
// "No delivery" / "By arrangement"; withdrawing an earlier public request), placements (Same as my general delivery /
// A different area / Ask me; standard courier vs specialist art transport), an artist confirming answers saved before
// 0027, the founder's filters, and the founder-only identifiers. Fictional artists; local Worker.
//   node test/preview-report36.mjs DIR
import { createRequire } from 'node:module';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');
const OUT = process.argv[2];
const { mf, url, db } = await start({ port: 8983, env: { TEST_ARTIST_IDS: 'atestacct' } });
const call = (m, p, email, body) => mf.dispatchFetch(url + p, { method: m, headers: { 'X-Studio': '1', 'Content-Type': 'application/json', 'Cf-Access-Jwt-Assertion': token(email) }, body: body ? JSON.stringify(body) : undefined }).then(r => r.json());
const S = 'asam@example.test', L = 'aleg@example.test';
await seedPublished(db, { id: 'asam', slug: 'sample-artist', email: S, name: 'Sample Artist (fictional)', works: 1 });
await seedPublished(db, { id: 'aleg', slug: 'earlier-artist', email: L, name: 'Earlier Answers (fictional)', works: 1 });
await seedPublished(db, { id: 'atestacct', slug: 'test-account', email: 'test@example.test', name: 'Internal Test Account', works: 1 });
await call('PUT', '/api/me/location', S, { country: 'IE', county: 'Sligo', town: '', show_location: true, show_town: false });
await call('PUT', '/api/me/delivery', S, { scope: 'island', methods: ['courier', 'specialist'] });
await call('PUT', '/api/opportunities', S, { interests: ['living_gallery', 'venues'], artwork_county: 'Sligo', transport: ['deliver'], coverage: { mode: 'counties', counties: ['Leitrim', 'Sligo'] }, placement_area: 'own', note: null });
// an artist who answered before 0027: legacy "none", a stored public tick, "courier or art transporter", own counties
await call('PUT', '/api/me/location', L, { country: 'IE', county: 'Cork', town: '', show_location: false, show_town: false });
const T = new Date().toISOString();
await db.prepare("INSERT INTO artist_delivery (artist_id, scope, counties, show_delivery, confirmed_at, confirmed_by, updated_at) VALUES ('aleg','counties','[\"Cork\",\"Kerry\"]',1,?,'artist',?)").bind(T, T).run();
await db.prepare(`INSERT INTO artist_opportunities (artist_id, interests, artwork_county, transport, coverage_mode, coverage_counties, note, created_at, updated_at, updated_by, care_condition, public_display)
  VALUES ('aleg','["exhibitions"]','Cork','["courier"]','counties','["Cork","Kerry"]',NULL,?,?,'aleg@example.test',0,0)`).bind(T, T).run();
const b = await chromium.launch();
const hide = 'header, .st-top, .st-tabs, .st-savebar, .st-opp-save { position: static !important; }';
for (const [n, w, h] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
  let ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(S) } });
  let pg = await ctx.newPage(); await pg.goto(url + '/#/profile', { waitUntil: 'networkidle' }); await pg.waitForTimeout(900); await pg.addStyleTag({ content: hide });
  await pg.locator('#del-card').screenshot({ path: `${OUT}/E01-artist-general-delivery-where-and-how-${n}.png` });
  await pg.goto(url + '/#/opportunities', { waitUntil: 'networkidle' }); await pg.waitForTimeout(900); await pg.addStyleTag({ content: hide });
  await pg.locator('#o-tr-card').screenshot({ path: `${OUT}/E02-artist-placement-transport-${n}.png` });
  await pg.locator('#o-cov-card').screenshot({ path: `${OUT}/E03-artist-placement-area-own-${n}.png` });
  await pg.click('[data-g="a"][data-k="general"]'); await pg.waitForTimeout(200);
  await pg.locator('#o-cov-card').screenshot({ path: `${OUT}/E04-artist-placement-same-as-general-${n}.png` });
  await ctx.close();
  ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(L) } });
  pg = await ctx.newPage(); await pg.goto(url + '/#/profile', { waitUntil: 'networkidle' }); await pg.waitForTimeout(900); await pg.addStyleTag({ content: hide });
  await pg.locator('#del-card').screenshot({ path: `${OUT}/E05-artist-earlier-answers-delivery-${n}.png` });
  await pg.goto(url + '/#/opportunities', { waitUntil: 'networkidle' }); await pg.waitForTimeout(900); await pg.addStyleTag({ content: hide });
  await pg.locator('#o-tr-card').screenshot({ path: `${OUT}/E06-artist-earlier-answers-transport-${n}.png` });
  await ctx.close();
  ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
  pg = await ctx.newPage(); await pg.goto(url + '/admin/opportunities', { waitUntil: 'networkidle' }); await pg.waitForSelector('#of-how'); await pg.addStyleTag({ content: hide });
  await pg.locator('section.st-card', { has: pg.locator('#of-how') }).screenshot({ path: `${OUT}/E07-founder-filters-${n}.png` });
  await pg.locator('#of-list > li', { hasText: 'Earlier Answers' }).screenshot({ path: `${OUT}/E08-founder-row-earlier-answers-${n}.png` });
  await pg.goto(url + '/admin', { waitUntil: 'networkidle' }); await pg.waitForTimeout(700); await pg.addStyleTag({ content: hide });
  const row = pg.locator('tr', { has: pg.locator('text=Internal Test Account') }).first();
  await row.locator('details.st-ids summary').click(); await pg.waitForTimeout(150);
  await row.locator('td').first().screenshot({ path: `${OUT}/E09-founder-identifiers-${n}.png` });
  await ctx.close();
}
await b.close(); await mf.dispose(); console.log('ok');
