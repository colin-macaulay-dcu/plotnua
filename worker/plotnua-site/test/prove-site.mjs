// Proves the plotnua-site Worker against a build (node test/prove-site.mjs <dist-dir> <repo-root>).
// ASSETS is emulated from the build directory exactly as wrangler.toml configures it (exact file or 404).
import { readFileSync, statSync, readdirSync } from 'node:fs';
import { join, relative } from 'node:path';
import { handle } from '../src/index.js';

const [dist, root] = process.argv.slice(2);
// content types as Workers Static Assets sends them (observed on plotart.ie, 27 Nov 2026): no charset on text types
const CF_TYPE = { html: 'text/html', txt: 'text/plain', css: 'text/css', js: 'text/javascript', json: 'application/json', xml: 'application/xml' };
const ASSETS = { async fetch(req) { const p = decodeURIComponent(new URL(req.url).pathname);
  try { const f = join(dist, p); if (!f.startsWith(dist) || !statSync(f).isFile()) throw 0; return new Response(readFileSync(f), { status: 200, headers: CF_TYPE[f.split('.').pop()] ? { 'Content-Type': CF_TYPE[f.split('.').pop()] } : {} }); }
  catch { return new Response('nf', { status: 404 }); } } };
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; if (fail < 30) console.log('FAIL', m); } };
const env = (x = {}) => ({ ASSETS, INDEXING: 'index', PLOTART_ADDRESS: 'plotnua.ie', ...x });
const get = (u, e = env(), method = 'GET') => handle(new Request(u, { method, redirect: 'manual' }), e);
const walk = d => readdirSync(d, { withFileTypes: true }).flatMap(x => x.isDirectory() ? walk(join(d, x.name)) : [join(d, x.name)]);

// 1. every published file is served at its own path on plotnua.ie, byte-identical to the repository file
const files = walk(dist).map(f => relative(dist, f).split('\\').join('/')).filter(f => !f.startsWith('.') && f !== '_headers');
for (const rel of files) {
  const r = await get(`https://plotnua.ie/${encodeURI(rel)}`);
  ok(r.status === 200 && Buffer.from(await r.arrayBuffer()).equals(readFileSync(join(root, rel))), `200 + bytes /${rel} (${r.status})`);
  if (rel.endsWith('/index.html')) {
    const dir = rel.slice(0, -'index.html'.length);
    const n = await get(`https://plotnua.ie/${dir.slice(0, -1)}?q=1`);
    ok(n.status === 301 && n.headers.get('location') === `https://plotnua.ie/${dir}?q=1`, `slash redirect /${dir}`);
  }
}
ok((await get('https://plotnua.ie/')).status === 200, 'home');
ok((await get('https://plotnua.ie/discoveries')).status === 200, 'extensionless page (as GitHub Pages)');
ok((await get('https://plotnua.ie/no-such.html')).status === 404, '404');
// 2. private repository files are not public (they are not in the build at all)
for (const p of ['_config.yml', 'README.md', 'image-rights-records.json', 'image-rights-manifest.json', 'atlas-tools/plotart_shell.py',
                 'worker/plotart-studio/wrangler.toml', 'governance/', '.github/workflows/release-promote.yml', '.gitignore'])
  ok((await get(`https://plotnua.ie/${p}`)).status === 404, `private stays private: /${p}`);
// 3. hosts and indexing
const w = await get('https://www.plotnua.ie/discoveries.html?x=1');
ok(w.status === 301 && w.headers.get('location') === 'https://plotnua.ie/discoveries.html?x=1', 'www -> apex');
ok((await get('https://plotnua.ie/')).headers.get('x-robots-tag') === null, 'plotnua.ie indexable');
ok((await get('https://plotnua-site.colin-a41.workers.dev/')).headers.get('x-robots-tag') === 'noindex, nofollow', 'workers.dev noindex');
// Option B: workers.dev (and any non-live address) disallows all crawling; plotnua.ie serves its real robots.txt
{ const r = await get('https://plotnua-site.colin-a41.workers.dev/robots.txt'); ok(r.status === 200 && (await r.text()) === 'User-agent: *\nDisallow: /\n', 'workers.dev robots.txt disallows everything'); }
{ const r = await get('https://plotnua.ie/robots.txt'); ok(Buffer.from(await r.arrayBuffer()).equals(readFileSync(join(root, 'robots.txt'))), 'plotnua.ie robots.txt is the published file'); }
{ const t = readFileSync(join(root, 'worker/plotnua-site/wrangler.toml'), 'utf8');
  ok(/^run_worker_first = \["\/\*", "!\/assets\/\*"\]$/m.test(t), 'only /assets/* bypasses the Worker (pages, JSON and /plotart/* always go through it)'); }
// header parity with GitHub Pages (plotnua.ie today): cache-control and content types
for (const [path, type] of [['/', 'text/html; charset=utf-8'], ['/discoveries.html', 'text/html; charset=utf-8'], ['/robots.txt', 'text/plain; charset=utf-8'], ['/sitemap.xml', 'application/xml'], ['/CNAME', null]]) {
  const r = await get('https://plotnua.ie' + path);
  ok(r.headers.get('cache-control') === 'max-age=600', `cache-control as Pages ${path}`);
  if (type) ok(r.headers.get('content-type') === type, `content-type ${path}: ${r.headers.get('content-type')}`);
}
for (const h of ['x-content-type-options', 'referrer-policy', 'strict-transport-security']) ok((await get('https://plotnua.ie/')).headers.get(h) !== null, `security header ${h}`);
// 4. the PlotArt move: off until the cutover, then exact
ok((await get('https://plotnua.ie/plotart/gallery/')).status === 200, 'before cutover: /plotart/ served here');
const cut = env({ PLOTART_ADDRESS: 'plotart.ie' });
for (const [from, to] of [['/plotart', 'https://plotart.ie/'], ['/plotart/', 'https://plotart.ie/'],
  ['/plotart/gallery/?utm_source=x', 'https://plotart.ie/gallery/?utm_source=x'],
  ['/plotart/artists/clare-o-connor/navigating-the-labyrinth-series.html', 'https://plotart.ie/artists/clare-o-connor/navigating-the-labyrinth-series.html']]) {
  const r = await get('https://plotnua.ie' + from, cut);
  ok(r.status === 301 && r.headers.get('location') === to, `cutover: ${from} -> ${to} (${r.status} ${r.headers.get('location')})`);
}
for (const p of ['/', '/discoveries.html', '/plotart-x.html', '/plotartist/', '/plotart.html', '/assets/plotart/x'])
  ok((await get('https://plotnua.ie' + p, cut)).headers.get('location')?.includes('plotart.ie') !== true, `cutover leaves ${p} alone`);
console.log(`plotnua-site: ${pass} passed, ${fail} failed (${files.length} files)`);
process.exit(fail ? 1 : 0);
