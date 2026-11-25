// Previews only (not a proof): the Studio's location and delivery cards for a synthetic artist.
import { createRequire } from 'node:module';
import { start, token } from './local.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');
const OUT = '/home/user/plotart-review/phase-c/shots';
const { mf, url, db } = await start({ port: 8893 });
await seedPublished(db, { id: 'asam', slug: 'sample-artist', email: 'sample@example.test', name: 'Sample Artist', works: 1, number: 1 });
await db.prepare("UPDATE artists SET county='Sligo' WHERE id='asam'").run();
const b = await chromium.launch();
for (const [n, w, h] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token('sample@example.test'), 'X-Studio': '1' } });
  const pg = await ctx.newPage();
  await pg.goto(url + '/#/profile', { waitUntil: 'networkidle' }).catch(() => {}); await pg.waitForTimeout(900);
  await pg.fill('#loc-town', 'Strandhill'); await pg.check('#loc-show');
  await pg.check('input[name="del-scope"][value="counties"]'); await pg.waitForTimeout(200);
  for (const c of ['Leitrim', 'Mayo', 'Roscommon']) await pg.check(`input[name="del-county"][value="${c}"]`);
  const lc = await pg.$('#loc-card'), dc = await pg.$('#del-card');
  await lc.scrollIntoViewIfNeeded(); await lc.screenshot({ path: `${OUT}/LOC-studio-based-${n}.png` });
  await dc.scrollIntoViewIfNeeded(); await dc.screenshot({ path: `${OUT}/LOC-studio-delivery-${n}.png` });
  await ctx.close();
}
await b.close(); await mf.dispose(); console.log('ok');
