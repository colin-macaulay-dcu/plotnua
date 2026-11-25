// Previews only (not a proof): the artist's location and delivery cards, and the founder's "Where artists are based"
// overview, for clearly fictional artists. Local Worker, synthetic data.   node test/preview-phase-c-location.mjs DIR
import { createRequire } from 'node:module';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');
const OUT = process.argv[2];
const { mf, url, db } = await start({ port: 8894 });
const call = (m, p, email, body) => mf.dispatchFetch(url + p, { method: m, headers: { 'X-Studio': '1', 'Content-Type': 'application/json', 'Cf-Access-Jwt-Assertion': token(email) }, body: body ? JSON.stringify(body) : undefined }).then(r => r.json());
const P = [['asam', 'sample-artist', 'Sample Artist (fictional)', { country: 'IE', county: 'Sligo', town: 'Strandhill', show_location: true, show_town: true }, { scope: 'counties', counties: ['Leitrim', 'Mayo', 'Roscommon'], show_delivery: true }],
  ['aeg', 'example-painter', 'Example Painter (fictional)', { country: 'IE', county: 'Mayo', town: '', show_location: true, show_town: false }, { scope: 'republic', counties: [], show_delivery: false }],
  ['ademo', 'demo-sculptor', 'Demo Sculptor (fictional)', { country: 'GB', county: 'Down', town: '', show_location: false, show_town: false }, { scope: 'island', counties: [], show_delivery: true }],
  ['aabr', 'abroad-example', 'Abroad Example (fictional)', { country: 'FR', county: null, town: 'Lyon', show_location: true, show_town: true }, { scope: 'counties', counties: ['Dublin', 'Mayo'], show_delivery: true }]];
for (const [id, slug, name, loc, del] of P) {
  await seedPublished(db, { id, slug, email: `${id}@example.test`, name, works: 1 });
  await call('PUT', '/api/me/location', `${id}@example.test`, loc); await call('PUT', '/api/me/delivery', `${id}@example.test`, del);
}
const b = await chromium.launch();
for (const [n, w, h] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
  let ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
  let pg = await ctx.newPage();
  await pg.goto(url + '/admin/opportunities', { waitUntil: 'networkidle' }); await pg.waitForSelector('.st-loc-ov h3');
  await pg.selectOption('#lo-c', 'Mayo'); await pg.waitForTimeout(500);
  await pg.locator('.st-loc-ov').screenshot({ path: `${OUT}/L01-founder-where-artists-are-mayo-${n}.png` });
  await ctx.close();
  ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token('asam@example.test') } });
  pg = await ctx.newPage(); await pg.goto(url + '/#/profile', { waitUntil: 'networkidle' }); await pg.waitForTimeout(900);
  await pg.locator('#loc-card').screenshot({ path: `${OUT}/L02-artist-based-${n}.png` });
  await pg.locator('#del-card').screenshot({ path: `${OUT}/L03-artist-delivery-${n}.png` });
  if (n === 'desktop') { const ex = pg.locator('.st-cv'); if (await ex.count()) { await ex.scrollIntoViewIfNeeded(); await ex.screenshot({ path: `${OUT}/X01-artist-exhibitions-unchanged-${n}.png` }); } }
  await ctx.close();
}
await b.close(); await mf.dispose(); console.log('ok');
