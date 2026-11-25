// Previews only (not a proof): the Art for Hire filters with REAL public data only (each artist's real public county; no
// delivery coverage, because none is public yet). Built into a temporary copy of the site; nothing is published.
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, existsSync, readFileSync, cpSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, extname } from 'node:path';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');
const HERE = new URL('..', import.meta.url).pathname, ROOT = join(HERE, '../..'), OUT = process.argv[2];
const tmp = mkdtempSync(join(tmpdir(), 'pa-afhp-'));
for (const d of ['plotart', 'assets']) cpSync(join(ROOT, d), join(tmp, d), { recursive: true });
const ids = [['carolyn-walsh', 'wh4ve2xmvb1'], ['lena-fawaz', 'waczo72tchw'], ['ciaran-mccoy', 'w1yt3pkcsxk'], ['olivia-jones', 'w4xytln2tm7'], ['paul-kerr', 'w7qm51rtg2y']];
const cat = { items: ids.map(([s, id]) => ({ artwork_id: id, artist_id: 'a-' + s, artist_slug: s, work_slug: 'x', hire: { availability: 'now', available_from: null, price: 'Price on request' } })) };
writeFileSync(join(tmp, 'c.json'), JSON.stringify(cat));
execFileSync('python3', ['-c', `import sys, json, importlib.util as u; sys.path.insert(0, ${JSON.stringify(join(ROOT, 'atlas-tools'))}); s = u.spec_from_file_location('h', ${JSON.stringify(join(ROOT, 'atlas-tools/plotart-hire-page.py'))}); m = u.module_from_spec(s); s.loader.exec_module(m); m.build(${JSON.stringify(tmp)}, json.load(open(${JSON.stringify(join(tmp, 'c.json'))})), 'https://relay.example')`]);
const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript', '.svg': 'image/svg+xml', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg' };
const b = await chromium.launch();
for (const [n, w, h] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, isMobile: n === 'mobile', hasTouch: n === 'mobile' });
  await ctx.route('https://plotnua.local/**', r => { let p = new URL(r.request().url()).pathname; if (p.endsWith('/')) p += 'index.html'; const f = join(tmp, decodeURIComponent(p)); existsSync(f) ? r.fulfill({ body: readFileSync(f), contentType: types[extname(f)] || 'application/octet-stream' }) : r.fulfill({ status: 404, body: '' }); });
  await ctx.route('https://relay.example/v1/hire-listed', r => r.fulfill({ contentType: 'application/json', body: JSON.stringify({ ok: true, open: true, enquiries: false, valid_until: new Date(Date.now() + 600000).toISOString(), items: ids.map(([, id]) => ({ id, availability: 'now' })) }) }));
  const pg = await ctx.newPage(); await pg.goto('https://plotnua.local/plotart/art-for-hire/', { waitUntil: 'networkidle' }); await pg.waitForTimeout(500);
  await pg.selectOption('[data-hire-f="county"]', 'Dublin'); await pg.waitForTimeout(200);
  await pg.evaluate(() => document.querySelectorAll('#afh3-works img').forEach(i => { i.loading = 'eager'; }));
  const sec = await pg.$('#afh3-works'); await sec.scrollIntoViewIfNeeded();
  await pg.waitForFunction(() => [...document.querySelectorAll('#afh3-works [data-hire-work]:not([hidden]) img')].every(i => i.complete && i.naturalWidth > 0), null, { timeout: 15000 }).catch(() => {});
  await pg.waitForTimeout(400);
  if (n === 'desktop') await sec.screenshot({ path: `${OUT}/AFH-filter-dublin-desktop.png` });
  else { const f = await pg.$('[data-hire-filter]'); await pg.evaluate(e => window.scrollTo(0, e.getBoundingClientRect().top + scrollY - 110), f); await pg.waitForTimeout(300); await pg.screenshot({ path: `${OUT}/AFH-filter-dublin-mobile.png` }); }
  await ctx.close();
}
await b.close(); console.log('ok');
