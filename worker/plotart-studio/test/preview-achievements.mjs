// Previews only (not a proof): a synthetic artist with an Exhibitions & Achievements section, in the local Studio.
import { createRequire } from 'node:module';
import { start, token } from './local.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');
const OUT = '/home/user/plotart-review/phase-c/shots';
const { mf, url, db } = await start({ port: 8881 });
await seedPublished(db, { id: 'asam', slug: 'sample-artist', email: 'sample@example.test', name: 'Sample Artist', works: 2, number: 1 });
const XA = `## Solo exhibitions
- 2025 Tide Lines, Sample Gallery, Galway
- 2022 Field Notes, Town Arts Centre, Westport

## Group exhibitions
- 2024 Annual Exhibition, Sample Academy, Dublin
- 2023 New Irish Painting, Harbour Gallery, Cork

## Awards
- 2024 Sample Painting Prize (shortlist)

## Collections
Work held in private collections in Ireland, the UK and the United States.

## Residencies
- 2021 Coastal Studio Residency, Co. Mayo`;
await db.prepare("UPDATE artists SET achievements=?, statement=?, bio=?, practice='Painter' WHERE id='asam'").bind(
  XA.replace(/\n\n## /g, '\n\n## ').trim(), 'Painting the light of the western seaboard.',
  'Sample Artist is a synthetic profile used only to preview the Exhibitions & Achievements section. The biography stays in About, the statement stays under the name, and the record of exhibitions and achievements has its own section.').run();
const b = await chromium.launch();
for (const [n, w, h] of [['desktop', 1440, 900], ['tablet', 834, 1112], ['mobile', 390, 844]]) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token('sample@example.test'), 'X-Studio': '1' } });
  const pg = await ctx.newPage();
  await pg.goto(url + '/preview/', { waitUntil: 'networkidle' }).catch(() => {});
  await pg.waitForTimeout(600);
  await pg.screenshot({ path: `${OUT}/XA-public-top-${n}.png` });
  const el = await pg.$('#exhibitions-achievements');
  if (el) { await el.scrollIntoViewIfNeeded(); await pg.waitForTimeout(300); await el.screenshot({ path: `${OUT}/XA-public-section-${n}.png` }); }
  if (n !== 'tablet') {
    await pg.goto(url + '/#/profile', { waitUntil: 'networkidle' }).catch(() => {});
    await pg.waitForTimeout(900);
    const f = await pg.$('#f-achievements');
    if (f) { const card = await f.evaluateHandle(e => e.closest('.st-card')); await card.scrollIntoViewIfNeeded(); await card.asElement().screenshot({ path: `${OUT}/XA-studio-field-${n}.png` }); }
    else console.log('no field on', n, (await pg.content()).slice(0, 300));
  }
  await ctx.close();
}
await b.close(); await mf.dispose(); console.log('ok');
