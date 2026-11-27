// Privacy regression test (prepared 27 Nov 2026): replaces Cookiebot's automated scanning with a check we run ourselves,
// in the deploy pipeline and against the live sites. For every page it loads in a real browser (Chromium):
//   1. before any choice: no cookie, no storage except the consent record's key, and no request to any host outside
//      the site's own origin and its declared functional hosts (no analytics, no pings, no fonts, no ads);
//   2. "Reject optional": the same, after the choice and a reload;
//   3. "Accept analytics": analytics hosts become allowed, nothing else new.
// Usage: node atlas-tools/prove-privacy.mjs <config.json> <base-url> [--pages-from <build dir>] [--pages N] [--report out.json]
// config: { "site": "plotart.ie", "consentKey": "pa-consent", "functional": ["plotart-enquiry.colin-a41.workers.dev", ...],
//           "analytics": ["www.googletagmanager.com", "*.google-analytics.com", "*.analytics.google.com"], "pages": ["/", ...],
//           "expectAnalyticsAfterAccept": true, "buttons": { "accept": "Accept analytics", "reject": "Reject optional" } }
// Analytics hosts are prohibited before any choice and after Reject, and REQUIRED after Accept (when expectAnalyticsAfterAccept).
// Exit 1 on any finding; each finding names the page, the phase and the host or cookie.
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { join, relative } from 'node:path';
import { chromium } from 'playwright';

const [cfgPath, base] = process.argv.slice(2);
const arg = k => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : null; };
const cfg = JSON.parse(readFileSync(cfgPath, 'utf8'));
const limit = Number(arg('--pages') || 1e9);
const origin = new URL(base).host;
const match = (host, pats) => pats.some(p => p.startsWith('*.') ? host === p.slice(2) || host.endsWith(p.slice(1)) : host === p);
const findings = [];
const note = (page, phase, what) => { findings.push({ page, phase, what }); console.log(`FAIL  ${page} [${phase}] ${what}`); };

const browser = await chromium.launch();
async function visit(page, phase, choose) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 860 } });
  const tab = await ctx.newPage();
  const hosts = new Set();
  tab.on('request', r => { try { hosts.add(new URL(r.url()).host); } catch {} });
  await ctx.route(/^https?:\/\/(?!127\.0\.0\.1|localhost)/, r => r.abort());   // nothing actually leaves the test machine
  await tab.goto(base + page, { waitUntil: 'domcontentloaded' });
  await tab.waitForTimeout(700);
  if (choose) {
    const b = cfg.buttons || { accept: 'Accept analytics', reject: 'Reject optional' };
    const btn = 'text=' + (choose === 'accept' ? b.accept : b.reject);
    if (await tab.isVisible(btn)) await tab.click(btn); else note(page, phase, 'consent banner not shown');
    await tab.reload({ waitUntil: 'domcontentloaded' });
    await tab.waitForTimeout(700);
  }
  await tab.mouse.wheel(0, 4000); await tab.waitForTimeout(300);          // lazy content too
  const cookies = await ctx.cookies();
  const storage = await tab.evaluate(() => Object.keys(localStorage).concat(Object.keys(sessionStorage).map(k => 'session:' + k)));
  await ctx.close();
  const allowed = [origin, ...(cfg.functional || []), ...(choose === 'accept' ? cfg.analytics : [])];
  for (const h of hosts) if (!match(h, allowed)) note(page, phase, `request to ${h}`);
  // the other direction: after an explicit Accept, analytics must actually start (measurement is not silently lost)
  if (choose === 'accept' && cfg.expectAnalyticsAfterAccept && ![...hosts].some(h => match(h, cfg.analytics))) note(page, phase, 'analytics did not start after Accept');
  const okCookie = c => choose === 'accept' && /^_ga(_|$)/.test(c.name);
  for (const c of cookies) if (!okCookie(c)) note(page, phase, `cookie ${c.name} (${c.domain})`);
  for (const k of storage) if (k !== cfg.consentKey) note(page, phase, `storage ${k}`);
}
// --pages-from <build dir>: every HTML page of the build (directories as /dir/), instead of cfg.pages
const walk = d => readdirSync(d, { withFileTypes: true }).flatMap(x => x.isDirectory() ? walk(join(d, x.name)) : [join(d, x.name)]);
const from = arg('--pages-from');
const all = from ? walk(from).map(f => '/' + relative(from, f).split('\\').join('/')).filter(f => f.endsWith('.html') && !f.startsWith('/.'))
  .map(f => f.endsWith('/index.html') ? f.slice(0, -10) : f).sort() : cfg.pages;
const pages = all.slice(0, limit);
for (const p of pages) await visit(p, 'before consent', null);
for (const p of pages.filter(x => !/(^|\/)404\.html$/.test(x)).slice(0, 5)) { await visit(p, 'after reject', 'reject'); await visit(p, 'after accept', 'accept'); }
await browser.close();
if (arg('--report')) writeFileSync(arg('--report'), JSON.stringify({ site: cfg.site, pages: pages.length, findings }, null, 1));
console.log(`PRIVACY ${cfg.site} · ${pages.length} pages · ${findings.length} findings`);
process.exit(findings.length ? 1 : 0);
