// Previews only (not a proof): the Gallery Showcase panel (Galleries tab), its preview, a vacancy and the Review desk
// notice. Fictional artists; local Worker with migration 0028.   node test/preview-showcase.mjs DIR
import { createRequire } from 'node:module';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');
const OUT = process.argv[2];
const { mf, url, db } = await start({ port: 8985 });
const call = (m, p, email, body) => mf.dispatchFetch(url + p, { method: m, headers: { 'X-Studio': '1', 'Content-Type': 'application/json', 'Cf-Access-Jwt-Assertion': token(email) }, body: body ? JSON.stringify(body) : undefined }).then(r => r.json());
for (const [id, n] of [['asam', 'Sample Artist (fictional)'], ['aeg', 'Example Painter (fictional)'], ['ademo', 'Demo Printmaker (fictional)']]) await seedPublished(db, { id, slug: id.slice(1) + '-artist', email: id + '@example.test', name: n, works: 3 });
// plainly synthetic colour panels as the preview images (screenshots only)
{ const { readFileSync } = await import('node:fs'); const bucket = await mf.getR2Bucket('IMAGES'); let k = 0;
  for (const r of (await db.prepare('SELECT id, preview_key, r2_key FROM images ORDER BY id').all()).results) { const b0 = readFileSync(`/tmp/scimg/${k++ % 9}.jpg`), buf = b0.buffer.slice(b0.byteOffset, b0.byteOffset + b0.length); await bucket.put(r.preview_key, buf); await bucket.put(r.r2_key, buf); } }
await call('PUT', '/api/admin/showcase/contemporary', FOUNDER, { items: [{ position: 1, artist_id: 'asam', artwork_id: 'wasam2' }, { position: 2, artist_id: 'aeg', artwork_id: 'waeg1' }, { position: 3, artist_id: 'ademo', artwork_id: 'wademo3' }] });
await call('POST', '/api/admin/showcase/contemporary/publish', FOUNDER);
// the right-hand work is then sold in a routine publication
const lv = await db.prepare("SELECT version, snapshot FROM versions WHERE artist_id='ademo' ORDER BY version DESC").first();
const s = JSON.parse(lv.snapshot); s.works.find(w => w.id === 'wademo3').availability = 'sold';
await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES ('ademo', ?, ?, 'preview', ?)").bind(lv.version + 1, JSON.stringify(s), new Date().toISOString()).run();
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qdemo2','ademo',?,'instant','published',?,?)").bind(lv.version + 1, new Date().toISOString(), new Date().toISOString()).run();
const b = await chromium.launch();
const hide = 'header, .st-top, .st-tabs { position: static !important; }';
for (const [n, w, h] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
  const pg = await ctx.newPage();
  await pg.goto(url + '/admin', { waitUntil: 'networkidle' }); await pg.waitForTimeout(600); await pg.addStyleTag({ content: hide });
  await pg.locator('.st-sc-alert').first().screenshot({ path: `${OUT}/G01-review-desk-vacancy-notice-${n}.png` });
  await pg.goto(url + '/admin/galleries', { waitUntil: 'networkidle' }); await pg.waitForTimeout(700); await pg.addStyleTag({ content: hide });
  await pg.locator('.st-gm-tabs button[data-g="contemporary"]').click(); await pg.waitForTimeout(400);
  await pg.locator('.st-sc').screenshot({ path: `${OUT}/G02-galleries-showcase-vacant-${n}.png` });
  await pg.selectOption('[data-sc-a="2"]', 'asam'); await pg.waitForTimeout(150); await pg.selectOption('[data-sc-w="2"]', 'wasam3'); await pg.waitForTimeout(150);
  await pg.click('[data-sc="swap"][data-i="2"][data-j="1"]'); await pg.waitForTimeout(150);
  await pg.locator('.st-sc').screenshot({ path: `${OUT}/G03-galleries-showcase-new-choice-preview-${n}.png` });
  await pg.locator('.st-gm-tabs button[data-g="spaces"]').click().catch(() => {}); await pg.waitForTimeout(400);
  pg.once('dialog', d => d.accept());
  await pg.locator('.st-gm-tabs button[data-g="spaces"]').click().catch(() => {}); await pg.waitForTimeout(500);
  if (await pg.locator('.st-sc').count()) await pg.locator('.st-sc').screenshot({ path: `${OUT}/G04-spaces-showcase-in-preparation-${n}.png` });
  await ctx.close();
}
await b.close(); await mf.dispose(); console.log('ok');
