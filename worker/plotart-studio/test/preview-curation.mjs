// Previews only (not a proof): Galleries -> Curate (one list, opening row, artwork picker, page preview) and the Review
// desk notes. Fictional artists, plainly synthetic colour panels; local Worker with migration 0029.
//   node test/preview-curation.mjs DIR
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { statements } from './sql.mjs';
const require = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');
const OUT = process.argv[2], HERE = new URL('..', import.meta.url).pathname, T = '2026-11-20T10:00:00.000Z';
const { mf, url, db } = await start({ port: 8986 });
const names = ['Sample Artist', 'Example Painter', 'Demo Printmaker', 'Model Sculptor', 'Pattern Colourist', 'Fictional Abstractionist', 'Placeholder Photographer'];
for (const [i, n] of names.entries()) await seedPublished(db, { id: 'a' + i + 'x', slug: 'artist-' + i, email: i + '@example.test', name: n + ' (fictional)', works: 3, number: i + 1 });
{ const bucket = await mf.getR2Bucket('IMAGES'); let k = 0;
  for (const r of (await db.prepare('SELECT id, preview_key, r2_key FROM images ORDER BY id').all()).results) { const b0 = readFileSync(`/tmp/scimg/${k++ % 9}.jpg`), buf = b0.buffer.slice(b0.byteOffset, b0.byteOffset + b0.length); await bucket.put(r.preview_key, buf); await bucket.put(r.r2_key, buf); } }
for (const p of [1, 2, 3, 4, 5]) await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (?,?,0,NULL,?)').bind(p, 'a' + (p - 1) + 'x', T).run();
await db.prepare("INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (1,'artist','a4x','wa4x2',?)").bind(T).run();
await db.prepare('DELETE FROM gallery_showcase').run();
for (const st of ['draft', 'published']) for (const p of [1, 2, 3]) await db.prepare("INSERT INTO gallery_showcase VALUES ('contemporary',?,?,?,?,?,'f@x.ie')").bind(st, p, 'a' + (p - 1) + 'x', `wa${p - 1}x1`, T).run();
for (const st of statements(readFileSync(HERE + 'migrations/0029_gallery_curation.sql', 'utf8'))) await db.prepare(st).run();
const b = await chromium.launch();
const hide = 'header, .st-top, .st-tabs { position: static !important; }';
for (const [n, w, h] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
  const pg = await ctx.newPage(); pg.on('dialog', d => d.accept());
  await pg.goto(url + '/admin/galleries', { waitUntil: 'networkidle' }); await pg.waitForTimeout(700); await pg.addStyleTag({ content: hide });
  await pg.locator('.st-gm-tabs button[data-g="contemporary"]').click(); await pg.waitForTimeout(500);
  await pg.locator('.st-cu').screenshot({ path: `${OUT}/S1-curate-${n}.png` });
  await pg.selectOption('[data-cu-to="5"]', '0'); await pg.waitForTimeout(200);
  await pg.click('.st-cu-row[data-i="4"] .st-cu-ctl [data-cu="pick"]'); await pg.waitForTimeout(200);
  await pg.locator('.st-cu').screenshot({ path: `${OUT}/S2-curate-moved-and-picker-${n}.png` });
  await ctx.close();
}
await b.close(); await mf.dispose(); console.log('ok');
