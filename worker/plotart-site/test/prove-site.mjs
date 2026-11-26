// Proves the plotart-site Worker against a real build (node test/prove-site.mjs <dist-dir> <repo-root>).
// ASSETS is emulated from the build directory with the behaviour configured in wrangler.toml
// (html_handling "none", not_found_handling "none": exact file or 404).
import { readFileSync, statSync, readdirSync } from 'node:fs';
import { join, relative } from 'node:path';
import { handle } from '../src/index.js';

const [dist, root] = process.argv.slice(2);
const ASSETS = {
  async fetch(req) {
    const p = decodeURIComponent(new URL(req.url).pathname);
    try {
      const f = join(dist, p);
      if (!f.startsWith(dist) || !statSync(f).isFile()) throw 0;
      return new Response(readFileSync(f), { status: 200 });
    } catch { return new Response('nf', { status: 404 }); }
  },
};
const report = JSON.parse(readFileSync(join(dist, '.build-report.json'), 'utf8'));
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const get = (u, env = { ASSETS, INDEXING: 'noindex' }, method = 'GET') => handle(new Request(u, { method }), env);
const walk = d => readdirSync(d, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(join(d, e.name)) : [join(d, e.name)]);

// 1. every file of plotart/ is served at the same path on plotart.ie, byte-identical to the build
const src = join(root, 'plotart');
let pages = 0;
for (const f of walk(src)) {
  const rel = relative(src, f).split('\\').join('/');
  const r = await get(`https://plotart.ie/${rel}`);
  ok(r.status === 200, `200 /${rel} got ${r.status}`);
  const body = Buffer.from(await r.arrayBuffer());
  ok(body.equals(readFileSync(join(dist, rel))), `bytes /${rel}`);
  if (rel.endsWith('index.html')) {
    const dir = rel.slice(0, -'index.html'.length);
    const d = await get(`https://plotart.ie/${dir}`);
    ok(d.status === 200 && Buffer.from(await d.arrayBuffer()).equals(readFileSync(join(dist, rel))), `dir /${dir}`);
    if (dir) {
      const n = await get(`https://plotart.ie/${dir.slice(0, -1)}?q=1`);
      ok(n.status === 301 && n.headers.get('location') === `https://plotart.ie/${dir}?q=1`, `slash redirect /${dir}`);
    }
    pages++;
  } else if (rel.endsWith('.html')) pages++;
}
// 2. extensionless page (GitHub Pages serves about.html at /about)
const a = await get('https://plotart.ie/about');
ok(a.status === 200, '/about served');
// 3. not found
const nf = await get('https://plotart.ie/no-such-page.html');
ok(nf.status === 404 && (await nf.text()).includes('<html'), '404 page');
ok((await get('https://plotart.ie/%2e%2e/secret')).status === 404, 'traversal refused');
// 4. www and other hosts -> apex, path and query kept
const w = await get('https://www.plotart.ie/gallery/?utm_source=x');
ok(w.status === 301 && w.headers.get('location') === 'https://plotart.ie/gallery/?utm_source=x', 'www -> apex');
// 5. indexing switch
ok((await get('https://plotart.ie/')).headers.get('x-robots-tag') === 'noindex, nofollow', 'noindex while testing');
ok((await get('https://plotart.ie/', { ASSETS, INDEXING: 'index' })).headers.get('x-robots-tag') === null, 'indexable after cutover');
ok((await get('https://plotart.ie/')).headers.get('x-content-type-options') === 'nosniff', 'security headers');
const csp = (await get('https://plotart.ie/gallery/')).headers.get('content-security-policy') || '';
ok(/script-src 'self' 'unsafe-inline'(;|$)/.test(csp) && !/googletagmanager|cookiebot/.test(csp), 'CSP: scripts only from plotart.ie (no tracker can load)');
ok(report.tracking_or_consent_scripts.length === 0, 'build: no tracking or consent script on any page');
// 6. methods
ok((await get('https://plotart.ie/', undefined, 'POST')).status === 405, 'POST refused');
const h = await get('https://plotart.ie/', undefined, 'HEAD');
ok(h.status === 200 && (await h.text()) === '', 'HEAD');
// 7. build: no old address, sitemap and robots
const sm = readFileSync(join(dist, 'sitemap.xml'), 'utf8');
ok(!/plotnua\.ie\/plotart/.test(sm) && sm.includes('<loc>https://plotart.ie/</loc>'), 'sitemap re-addressed');
ok(report.missing_links.length === 0 && report.old_address_left_in.length === 0, 'build report clean');
console.log(`plotart-site: ${pass} passed, ${fail} failed (${pages} pages)`);
process.exit(fail ? 1 : 0);
