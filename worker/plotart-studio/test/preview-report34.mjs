// Previews only (not a proof): Report 34 founder and artist screens — invitation with gallery choice (Gallery Artist only),
// Remove from Contemporary, TEST badges, and the artist's gallery invitation. Fictional artists; local Worker, synthetic data.
//   node test/preview-report34.mjs DIR
import { createRequire } from 'node:module';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');
const OUT = process.argv[2];
const TEST = 'atestacct';
const { mf, url, db } = await start({ port: 8895, env: { TEST_ARTIST_IDS: TEST } });
const call = (m, p, email, body) => mf.dispatchFetch(url + p, { method: m, headers: { 'X-Studio': '1', 'Content-Type': 'application/json', 'Cf-Access-Jwt-Assertion': token(email) }, body: body ? JSON.stringify(body) : undefined }).then(r => r.json());
await seedPublished(db, { id: 'asam', slug: 'sample-artist', email: 'asam@example.test', name: 'Sample Artist (fictional)', works: 2, number: 1 });
await seedPublished(db, { id: 'aeg', slug: 'example-painter', email: 'aeg@example.test', name: 'Example Painter (fictional)', works: 2, number: 2 });
await seedPublished(db, { id: TEST, slug: 'test-account', email: 'test@example.test', name: 'Internal Test Account', works: 1 });
await call('POST', '/api/admin/artists/' + TEST + '/test-programme', FOUNDER);
await call('POST', '/api/admin/galleries/spaces/members', FOUNDER, { artist_id: 'aeg', source: 'founder_curation' });
const b = await chromium.launch();
for (const [n, w, h] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
  let ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
  let pg = await ctx.newPage();
  await pg.goto(url + '/admin', { waitUntil: 'networkidle' }); await pg.waitForSelector('#inv'); await pg.waitForTimeout(400);
  await pg.addStyleTag({ content: 'header, .st-top, .st-tabs { position: static !important; }' });
  await pg.locator('section.st-card', { has: pg.locator('#inv') }).screenshot({ path: `${OUT}/R01-founder-invite-gallery-choice-${n}.png` });
  const tbl = pg.locator('section.st-card', { has: pg.locator('text=Internal Test Account') }).first();
  if (await tbl.count()) await tbl.screenshot({ path: `${OUT}/R02-founder-overview-test-badge-${n}.png` });
  await pg.goto(url + '/admin/galleries', { waitUntil: 'networkidle' }); await pg.waitForTimeout(900);
  await pg.addStyleTag({ content: 'header, .st-top, .st-tabs { position: static !important; }' });   // element shots: no sticky header over them
  await pg.locator('.st-gm-tabs button[data-g="contemporary"]').click(); await pg.waitForTimeout(600);
  const rm = pg.locator('button[data-m="withdraw"]', { hasText: 'Remove from Contemporary' }).first();
  const cont = pg.locator('.st-gm-list', { has: rm }).first();
  if (await cont.count()) { await cont.scrollIntoViewIfNeeded(); await cont.screenshot({ path: `${OUT}/R03-founder-galleries-remove-from-contemporary-${n}.png` }); }
  if (await rm.count()) {
    pg.once('dialog', d => d.dismiss());
    const shot = cont;
    await rm.click().catch(() => {}); await pg.waitForTimeout(400);
    const conf = pg.locator('[role="dialog"], .st-confirm, .st-modal').first();
    if (await conf.count() && await conf.isVisible()) await conf.screenshot({ path: `${OUT}/R04-founder-remove-confirm-${n}.png` });
    else await shot.screenshot({ path: `${OUT}/R04-founder-remove-confirm-${n}.png` });
  }
  await ctx.close();
  ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token('aeg@example.test') } });
  pg = await ctx.newPage(); await pg.goto(url + '/', { waitUntil: 'networkidle' }); await pg.waitForTimeout(900);
  const yg = pg.locator('#yg-card');
  if (await yg.count() && await yg.isVisible()) await yg.screenshot({ path: `${OUT}/R05-artist-spaces-invitation-${n}.png` });
  await ctx.close();
}
await b.close(); await mf.dispose(); console.log('ok');
