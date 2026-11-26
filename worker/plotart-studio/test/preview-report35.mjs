// Previews only (not a proof): Report 35 artist and founder screens — general delivery ("Delivering to buyers and
// hirers", unanswered), the location consent check, Opportunities (artwork kept, placement transport with the Art
// Services & Providers link, placement area with the general-delivery starting point) and the founder's separated
// filters. Fictional artists; local Worker.   node test/preview-report35.mjs DIR
import { createRequire } from 'node:module';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');
const OUT = process.argv[2];
const { mf, url, db } = await start({ port: 8957 });
const call = (m, p, email, body) => mf.dispatchFetch(url + p, { method: m, headers: { 'X-Studio': '1', 'Content-Type': 'application/json', 'Cf-Access-Jwt-Assertion': token(email) }, body: body ? JSON.stringify(body) : undefined }).then(r => r.json());
const S = 'asam@example.test', E = 'aeg@example.test', N = 'anew@example.test';
await seedPublished(db, { id: 'asam', slug: 'sample-artist', email: S, name: 'Sample Artist (fictional)', works: 1 });
await seedPublished(db, { id: 'aeg', slug: 'example-painter', email: E, name: 'Example Painter (fictional)', works: 1 });
await seedPublished(db, { id: 'anew', slug: 'new-artist', email: N, name: 'New Artist (fictional)', works: 1 });
await call('PUT', '/api/me/location', S, { country: 'IE', county: 'Galway', town: '', show_location: true, show_town: false });
await call('PUT', '/api/me/delivery', S, { scope: 'island', methods: ['courier'] });
await call('PUT', '/api/opportunities', S, { interests: ['living_gallery', 'exhibitions'], artwork_county: 'Galway', transport: ['deliver'], coverage: { mode: 'counties', counties: ['Galway', 'Mayo'] }, note: null });
await call('PUT', '/api/me/location', E, { country: 'IE', county: 'Cork', town: '', show_location: true, show_town: false });
await db.prepare("UPDATE artists SET county_public=0 WHERE id='aeg'").run();   // an older disagreement, for the confirmation note
await call('PUT', '/api/me/delivery', E, { scope: 'counties', counties: ['Cork', 'Kerry'], methods: ['personal'] });
await call('PUT', '/api/opportunities', E, { interests: ['venues'], artwork_county: 'Cork', transport: ['need_help'], coverage: null, note: null });
const b = await chromium.launch();
const hide = 'header, .st-top, .st-tabs { position: static !important; }';
for (const [n, w, h] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
  let ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(N) } });
  let pg = await ctx.newPage(); await pg.goto(url + '/#/profile', { waitUntil: 'networkidle' }); await pg.waitForTimeout(900); await pg.addStyleTag({ content: hide });
  await pg.locator('#del-card').screenshot({ path: `${OUT}/D01-artist-general-delivery-unanswered-${n}.png` });
  await ctx.close();
  ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(E) } });
  pg = await ctx.newPage(); await pg.goto(url + '/#/profile', { waitUntil: 'networkidle' }); await pg.waitForTimeout(900); await pg.addStyleTag({ content: hide });
  await pg.locator('#loc-card').screenshot({ path: `${OUT}/D02-artist-location-confirm-${n}.png` });
  await ctx.close();
  ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(S) } });
  pg = await ctx.newPage(); await pg.goto(url + '/#/opportunities', { waitUntil: 'networkidle' }); await pg.waitForTimeout(900); await pg.addStyleTag({ content: hide });
  await pg.locator('section.st-card', { has: pg.locator('#o-county') }).screenshot({ path: `${OUT}/D03-artist-artwork-kept-${n}.png` });
  await pg.locator('#o-tr-card').screenshot({ path: `${OUT}/D04-artist-placement-transport-${n}.png` });
  await pg.locator('#o-cov-card').screenshot({ path: `${OUT}/D05-artist-placement-area-starting-point-${n}.png` });
  await ctx.close();
  ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
  pg = await ctx.newPage(); await pg.goto(url + '/admin/opportunities', { waitUntil: 'networkidle' }); await pg.waitForSelector('#of-gen'); await pg.addStyleTag({ content: hide });
  await pg.locator('section.st-card', { has: pg.locator('#of-gen') }).screenshot({ path: `${OUT}/D06-founder-filters-${n}.png` });
  await pg.locator('#of-list > li', { hasText: 'Sample Artist' }).screenshot({ path: `${OUT}/D07-founder-row-three-answers-${n}.png` });
  await ctx.close();
}
await b.close(); await mf.dispose(); console.log('ok');
