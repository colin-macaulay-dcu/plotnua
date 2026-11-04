#!/usr/bin/env node
/* PROOF: SUPPLIER ATTRIBUTION (via=) SURVIVES TO THE HOMEOWNER'S ENQUIRY
 * ===========================================================================
 * Supplier showcases link into your-plot.html with ?via=<supplier-slug>. This
 * drives the real page in Chromium (served locally; every off-site request is
 * answered or refused here, nothing leaves the machine) and checks:
 *
 *   VA1  every via= link on every suppliers/*.html page is read as its slug
 *   VA2  the slug survives in-page navigation (history entries)
 *   VA3  Ask PlotNua: the Formspree POST carries via=<slug>
 *   VA4  the enquiry screen (test route): the POST body carries via
 *   VA5  without via=, both enquiries carry an empty via (no stale value)
 *   VA6  a via= that is not a plain slug (markup, an email address, spaces,
 *        uppercase tricks, 65+ chars) is dropped, never forwarded
 *   VA7  the slug is not written to cookies, localStorage or sessionStorage
 *   VA8  the lead Worker payload is unchanged (closed contract; no via field)
 *
 * Run: node atlas-tools/prove-supplier-attribution.mjs
 */
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');   // pre-installed locally; not a CI dependency
import http from 'node:http';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, extname, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.webp': 'image/webp', '.woff2': 'font/woff2' };
const srv = http.createServer((req, res) => {
  const f = join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!f.startsWith(ROOT) || !existsSync(f)) { res.writeHead(404); return res.end(); }
  try { const b = readFileSync(f); res.writeHead(200, { 'content-type': TYPES[extname(f)] || 'application/octet-stream' }); res.end(b); }
  catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${srv.address().port}`;

let fails = 0;
const check = (code, ok, what) => { console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${code}  ${what}`); if (!ok) fails++; };

const links = [];
for (const f of readdirSync(join(ROOT, 'suppliers')).filter(n => n.endsWith('.html'))) {
  const html = readFileSync(join(ROOT, 'suppliers', f), 'utf8');
  for (const m of html.matchAll(/href="\.\.\/(your-plot\.html\?[^"]*via=([a-z0-9-]+)[^"]*)"/g)) {
    links.push({ page: f, url: m[1].replace(/&amp;/g, '&'), slug: m[2] });
  }
}

const browser = await chromium.launch();
async function open(query) {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const posts = [];
  await page.route('**/*', route => {
    const u = route.request().url();
    if (u.startsWith(BASE)) return route.continue();
    if (u.includes('formspree.io')) { posts.push({ url: u, body: route.request().postData() || '' });
      return route.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' }); }
    if (u.includes('garden-lead')) { posts.push({ url: u, body: route.request().postData() || '' });
      return route.fulfill({ status: 500, body: '' }); }
    return route.abort();
  });
  await page.goto(`${BASE}/your-plot.html${query}`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.readyState !== 'loading');
  return { ctx, page, posts };
}
async function askPost(page, posts) {
  await page.evaluate(() => {
    const f = document.getElementById('askOwnForm'); f.hidden = false;
    document.getElementById('askOwnField').value = 'Attribution proof question';
    f.requestSubmit();
  });
  await page.waitForTimeout(400);
  return posts.find(p => p.url.includes('xrpgakqw'));
}
async function enquiryPost(page, posts) {
  await page.evaluate(() => {
    window.PLOTNUA_OPEN_TEST_ENQUIRY();
    document.getElementById('enqName').value = 'Proof';
    document.getElementById('enqEmail').value = 'proof@example.com';
    document.getElementById('enqLocation').value = 'Dublin';
    document.getElementById('enqConsent').checked = true;
    document.getElementById('enqSendBtn').click();
  });
  await page.waitForTimeout(500);
  return posts.find(p => p.url.includes('xjyvqepz'));
}
const viaOf = body => {
  if (!body) return null;
  if (body.trim().startsWith('{')) { try { return JSON.parse(body).via; } catch { return null; } }
  const m = body.match(/name="via"\r?\n\r?\n([^\r\n]*)/); return m ? m[1] : null;
};

console.log('SUPPLIER ATTRIBUTION (via=) PROOF\n' + '='.repeat(74));

/* VA1 */
let va1 = links.length > 0;
for (const l of links) {
  const { ctx, page } = await open('?' + l.url.split('?')[1]);
  const v = await page.evaluate(() => [window.PLOTNUA_VIA, document.getElementById('askOwnVia').value]);
  if (v[0] !== l.slug || v[1] !== l.slug) { va1 = false; console.log(`        ${l.page}: got ${JSON.stringify(v)} for ${l.slug}`); }
  await ctx.close();
}
check('VA1', va1, `${links.length} via= links on ${new Set(links.map(l => l.page)).size} showcase pages read as their slug`);

for (const slug of ['superior-pergola-ireland', 'gardenhouse24', 'the-mobile-pods']) {
  const { ctx, page, posts } = await open(`?discovery=garden-room&via=${slug}&enquiry=test`);
  await page.evaluate(() => { history.pushState({ pnScreen: 'x' }, ''); history.pushState({ pnScreen: 'y' }, ''); history.back(); });
  await page.waitForTimeout(150);
  const still = await page.evaluate(() => new URLSearchParams(location.search).get('via'));
  check('VA2', still === slug, `${slug}: survives in-page navigation`);
  const a = await askPost(page, posts);
  check('VA3', viaOf(a && a.body) === slug, `${slug}: Ask PlotNua POST carries via=${slug}`);
  const e = await enquiryPost(page, posts);
  check('VA4', viaOf(e && e.body) === slug, `${slug}: enquiry POST carries via=${slug}`);
  const stored = await page.evaluate(() => document.cookie + JSON.stringify(localStorage) + JSON.stringify(sessionStorage));
  check('VA7', !stored.includes(slug), `${slug}: not written to cookies or storage`);
  await ctx.close();
}

{
  const { ctx, page, posts } = await open('?discovery=garden-room&enquiry=test');
  const a = await askPost(page, posts), e = await enquiryPost(page, posts);
  check('VA5', viaOf(a && a.body) === '' && viaOf(e && e.body) === '', 'no via=: both enquiries carry an empty via');
  await ctx.close();
}

for (const bad of ['%3Cscript%3Ex%3C%2Fscript%3E', 'someone%40example.com', 'garden%20house', '-lead', 'a'.repeat(65), 'x_y', '']) {
  const { ctx, page } = await open(`?discovery=garden-room&via=${bad}`);
  const v = await page.evaluate(() => [window.PLOTNUA_VIA, document.getElementById('askOwnVia').value]);
  check('VA6', v[0] === '' && v[1] === '', `rejected: via=${decodeURIComponent(bad).slice(0, 30) || '(empty)'}`);
  await ctx.close();
}

const yp = readFileSync(join(ROOT, 'your-plot.html'), 'utf8');
const lead = (yp.match(/function leadPayload\(\)\{[\s\S]*?\n  \}/) || [''])[0];
check('VA8', lead.length > 0 && !/via/.test(lead), 'lead Worker payload unchanged (no via field)');

await browser.close(); srv.close();
console.log('-'.repeat(74));
console.log(fails ? `PROOF FAILED (${fails})` : 'PROOF COMPLETE');
process.exit(fails ? 1 : 0);
