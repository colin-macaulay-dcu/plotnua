// TEST ONLY · a private local preview of the Art for Hire page (Stage 3B-4). The preview site is served from a temporary
// folder at https://plotnua.test/ INSIDE the test browser only (Playwright request routing; nothing listens publicly), and
// the enquiry relay runs in Miniflare with synthetic data. Nothing here touches the real site, Cloudflare or any record.
import { execFileSync } from 'node:child_process';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { start } from './local.mjs';
import { seedPublished } from './seed.mjs';

const HERE = new URL('..', import.meta.url).pathname;
export const SITE = 'https://plotnua.test', RELAY = 'https://relay.test';
export const { chromium, devices } = createRequire('/tmp/claude-0/studio-tools/package.json')('playwright');
const sha = b => createHash('sha256').update(b).digest('hex');
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.webp': 'image/webp', '.png': 'image/png', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.json': 'application/json', '.woff2': 'font/woff2' };

export function buildPreview(dir, { fixture = false, form = false } = {}) {
  return execFileSync('python3', [HERE + 'test/make-hire-preview.py', dir, '--api', RELAY, ...(fixture ? ['--fixture'] : []), ...(form ? ['--form'] : [])], { encoding: 'utf8' });
}

/* The relay with synthetic fixture rows that match the preview's fixture works (or none). */
export async function relay({ port, listing = true, enquiries = false, fixture = true }) {
  const S = await start({ port, enquiry: { ORIGIN: SITE, HIRE_TERMS_ENABLED: listing ? 'true' : 'false', HIRE_ENQUIRIES_ENABLED: enquiries ? 'true' : 'false' } });
  if (!fixture) return S;
  const TXT = '<p>Synthetic test text.</p>', PDF = '%PDF test';
  await S.db.prepare("INSERT INTO hire_terms VALUES ('PA-AFH-2026-11', 'TEST', ?, ?, '2018-01-01T00:00:00Z', '2026-11-10')").bind(sha(TXT), sha(PDF)).run();
  for (const [id, slug, name] of [['fixa', 'fixture-artist-a', 'Fixture Artist A'], ['fixb', 'fixture-artist-b', 'Fixture Artist B'], ['fixc', 'fixture-artist-c', 'Fixture Artist C']]) {
    await seedPublished(S.db, { id, slug, email: `${slug}@artist.example.test`, name, works: 2 });
    await S.db.prepare(`INSERT INTO hire_terms_acceptances (id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, statement, method, created_at)
      VALUES (?, ?, 'PA-AFH-2026-11', ?, ?, '2026-11-09T10:00:00Z', ?, ?, 'test', 'studio_checkbox', '2026-11-09T10:00:00Z')`).bind('ha' + id, id, sha(TXT), sha(PDF), `${slug}@artist.example.test`, name).run();
    for (const i of [1, 2]) {
      const ap = { availability: 'now', available_from: null, county: 'Dublin', screen_use: 'none', photo_use: 'none', framing: 'framed', glazed: 0, weight_band: '5_15kg', collection: 'ask', deliver_km: null };
      await S.db.prepare(`INSERT INTO artwork_hire (artwork_id, artist_id, offered, availability, county, screen_use, photo_use, framing, glazed, weight_band, collection, handling_note, review_state, approved_public, approved_at, approved_by, updated_at, created_at)
        VALUES (?, ?, 1, 'now', 'Dublin', 'none', 'none', 'framed', 0, '5_15kg', 'ask', 'PRIVATE handling note', 'approved', ?, '2026-11-09', 'founder', '2026-11-09', '2026-11-09')`).bind(`w${id}${i}`, id, JSON.stringify(ap)).run();
    }
  }
  return S;
}

/* A browser page on the preview. mode.fail: 'abort' | '503' | 'stale' | 'slow' simulates a broken live check. */
export async function open(browser, dir, S, { url = '/plotart/art-for-hire/', viewport = { width: 1440, height: 1000 }, device = null, js = true, fail = null, scale = 1 } = {}) {
  const ctx = await browser.newContext({ ...(device ? devices[device] : { viewport, deviceScaleFactor: scale }), javaScriptEnabled: js });
  const page = await ctx.newPage();
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  await page.route(SITE + '/**', async rt => {
    let p = decodeURIComponent(new URL(rt.request().url()).pathname);
    let f = path.join(dir, p);
    if (existsSync(f) && statSync(f).isDirectory()) f = path.join(f, 'index.html');
    if (!existsSync(f)) return rt.fulfill({ status: 404, body: 'not found' });
    return rt.fulfill({ body: readFileSync(f), headers: { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' } });
  });
  await page.route(/fonts\.(googleapis|gstatic)\.com/, rt => rt.abort());
  await page.route(RELAY + '/**', async rt => {
    const q = rt.request(), f = page._hireFail ?? fail;
    if (f === 'abort') return rt.abort();
    if (f === '503') return rt.fulfill({ status: 503, body: '{"ok":false}', headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': SITE } });
    if (f === 'slow') return new Promise(() => {});                       // never answers: the script's timeout applies
    const r = await S.mf.dispatchFetch('http://enquiry.local' + new URL(q.url()).pathname, { method: q.method(), headers: { Origin: SITE, 'Content-Type': 'application/json' }, body: q.postData() || undefined });
    let body = await r.text();
    if (f === 'stale' && q.url().endsWith('hire-listed')) { const j = JSON.parse(body); j.valid_until = new Date(Date.now() - 1000).toISOString(); body = JSON.stringify(j); }
    return rt.fulfill({ status: r.status, body, headers: Object.fromEntries(r.headers) });
  });
  await page.goto(SITE + url);
  await page.waitForTimeout(900);
  return { ctx, page, errors };
}
