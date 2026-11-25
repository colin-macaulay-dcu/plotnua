// Previews only (not a proof): the Track C visual review pack for one synthetic artist. Local Miniflare D1; nothing
// touches Cloudflare or a real artist.   node test/preview-review-pack.mjs OUT_DIR
//   STUDIO-artist-location-delivery-*  the artist's two location cards (Profile)
//   STUDIO-artist-exhibitions-*        the approved Exhibitions & Achievements editor with its live preview (Profile)
//   STUDIO-dashboard-*                 the artist dashboard, unchanged (the CSS safeguard)
//   PUBLIC-gallery-location-ea-*       the artist's gallery page: location under the name, and the E&A section
import { createRequire } from 'node:module';
import { start, token } from './local.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');
const OUT = process.argv[2];
if (!OUT) { console.error('usage: node test/preview-review-pack.mjs OUT_DIR'); process.exit(2); }
const { mf, url, db } = await start({ port: 8899 });
await seedPublished(db, { id: 'asam', slug: 'sample-artist', email: 'sample@example.test', name: 'Sample Artist', works: 2, number: 1 });
const T = '2026-11-25T10:00:00.000Z';
await db.prepare("UPDATE artists SET county='Sligo', county_public=1, practice='Painter', exhibitions=? WHERE id='asam'").bind(
  '## Solo exhibitions\n- 2025 · Tidelines, The Example Gallery, Dublin\n- 2023 · Salt and Stone, Harbour Arts Centre, Cork\n\n## Group exhibitions\n- 2024 · New Irish Painting, Example Arts Centre, Galway\n\n## Awards\n- 2024 · Shortlisted, Example Painting Prize').run();
await db.prepare("INSERT INTO artist_locations (artist_id, country, county, town, show_location, show_town, confirmed_at, confirmed_by, updated_at) VALUES ('asam','IE','Sligo','Strandhill',1,1,?,'artist',?)").bind(T, T).run();
await db.prepare("INSERT INTO artist_delivery (artist_id, scope, counties, show_delivery, confirmed_at, confirmed_by, updated_at) VALUES ('asam','counties','[\"Leitrim\",\"Mayo\",\"Roscommon\"]',1,?,'artist',?)").bind(T, T).run();
const b = await chromium.launch(); const errs = [];
for (const [n, w, h] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token('sample@example.test'), 'X-Studio': '1' } });
  const pg = await ctx.newPage(); pg.on('pageerror', e => errs.push(e.message));
  await pg.goto(url + '/#/', { waitUntil: 'networkidle' }); await pg.waitForTimeout(900);
  await pg.screenshot({ path: `${OUT}/STUDIO-dashboard-${n}.png`, fullPage: true });
  await pg.goto(url + '/#/profile', { waitUntil: 'networkidle' }); await pg.waitForTimeout(1200);
  // screenshots only: pin the sticky header and save bar so they do not cover the cards
  await pg.addStyleTag({ content: '.st-top,.st-savebar,.st-saved,.st-sticky{position:static!important}' });
  const lc = await pg.$('#loc-card'), dc = await pg.$('#del-card'), cv = await pg.$('.st-cv');
  await lc.scrollIntoViewIfNeeded(); await lc.screenshot({ path: `${OUT}/STUDIO-artist-location-${n}.png` });
  await dc.scrollIntoViewIfNeeded(); await dc.screenshot({ path: `${OUT}/STUDIO-artist-delivery-${n}.png` });
  if (cv) { await cv.scrollIntoViewIfNeeded(); await cv.screenshot({ path: `${OUT}/STUDIO-artist-exhibitions-${n}.png` }); } else errs.push('no E&A editor');
  await pg.goto(url + '/preview/', { waitUntil: 'networkidle' }); await pg.waitForTimeout(900);
  const meta = await pg.$eval('.pa-ag-meta', e => e.textContent).catch(() => null);
  const head = await pg.$('.pa-ag-meta'); if (head) { await pg.evaluate(() => scrollTo(0, 0)); await pg.screenshot({ path: `${OUT}/PUBLIC-gallery-location-${n}.png` }); }
  const ea = await pg.$('#exhibitions'); if (ea) { await ea.scrollIntoViewIfNeeded(); await ea.screenshot({ path: `${OUT}/PUBLIC-gallery-exhibitions-${n}.png` }); } else errs.push('no E&A section');
  console.log(n, 'meta:', meta, '| delivery on public page:', /Leitrim|Delivers/.test(await pg.content()));
  await ctx.close();
}
await b.close(); await mf.dispose(); console.log(errs.length ? 'ERRORS ' + errs.join(' | ') : 'ok');
