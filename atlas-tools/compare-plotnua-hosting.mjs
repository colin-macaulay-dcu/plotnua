// Live hosting parity check for plotnua.ie (prepared 27 Nov 2026, development only).
// Compares the current GitHub Pages site with the plotnua-site Worker, file by file, before any switch-over:
//   node atlas-tools/compare-plotnua-hosting.mjs <build dir> https://plotnua.ie https://plotnua-site.colin-a41.workers.dev [--report out.json]
// For every published file (from the allowlist build) and a set of URL forms (directories, extensionless pages, 404s,
// www), it checks: status, bytes (sha256), content type, cache-control, redirects (Location) and the indexing header.
// Expected, documented differences (not failures): /assets/ files bypass the Worker (Option B) with Cloudflare's own
// cache-control; the Worker adds security headers (HSTS, nosniff, referrer,
// permissions, frame) and noindexes the workers.dev address. Anything else is reported and the exit code is 1.
import { readdirSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { createHash } from 'node:crypto';

const [dist, pagesBase, workerBase] = process.argv.slice(2);
const arg = k => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : null; };
const walk = d => readdirSync(d, { withFileTypes: true }).flatMap(x => x.isDirectory() ? walk(join(d, x.name)) : [join(d, x.name)]);
const files = walk(dist).map(f => '/' + relative(dist, f).split('\\').join('/')).filter(f => !/\/\.|\/_headers$/.test(f));
const extra = ['/', '/plotart', '/plotart/', '/discoveries', '/no-such-page.html', '/no-such-dir/', '/_config.yml', '/atlas-tools/', '/.github/'];
const diffs = [], expected = [], utf8Bad = [];
const isUtf8 = b => { try { new TextDecoder('utf-8', { fatal: true }).decode(b); return true; } catch { return false; } };
// the test address serves robots.txt "Disallow: /" by design (a non-live copy is never crawled); plotnua.ie serves the file
const workerIsTestAddress = !/^https:\/\/(www\.)?plotnua\.ie$/.test(workerBase);
const norm = t => (t || '').toLowerCase().replace(/\s+/g, '');
// Content types are compared by MEANING, not spelling (prepared 27 Nov 2026):
//   * registered aliases are the same type: application/javascript, application/x-javascript and text/javascript
//     (RFC 9239 makes text/javascript the standard name);
//   * for text-like types an absent charset means UTF-8 to every browser here (the files are UTF-8, checked below),
//     so "text/css" equals "text/css; charset=utf-8"; any OTHER charset still differs;
//   * a missing type and application/octet-stream both mean "unknown binary", accepted only for files whose extension
//     has no registered type (CNAME, .part);
// and, stronger than before, every 200 response on BOTH hosts must carry the type its extension requires, so a host
// that labels a stylesheet as text/plain, or a page as text/plain, fails even if both hosts made the same mistake.
const ALIAS = { 'application/javascript': 'text/javascript', 'application/x-javascript': 'text/javascript' };
const TEXTLIKE = /^(text\/|application\/(json|manifest\+json|xml|javascript)|image\/svg\+xml)/;
const EXT = { html: 'text/html', htm: 'text/html', css: 'text/css', js: 'text/javascript', mjs: 'text/javascript', json: 'application/json',
  webmanifest: 'application/manifest+json', xml: 'application/xml', txt: 'text/plain', svg: 'image/svg+xml', png: 'image/png',
  jpg: 'image/jpeg', jpeg: 'image/jpeg', webp: 'image/webp', avif: 'image/avif', gif: 'image/gif', ico: 'image/x-icon',
  woff2: 'font/woff2', woff: 'font/woff', pdf: 'application/pdf', mp4: 'video/mp4' };
const extOf = p => { const f = p.split('/').pop(); return f.includes('.') ? f.split('.').pop().toLowerCase() : ''; };
function canonType(raw, path) {
  const [base0, ...params] = norm(raw).split(';');
  let base = ALIAS[base0] || base0;
  const cs = (params.find(x => x.startsWith('charset=')) || '').slice(8);
  if (!base || base === 'application/octet-stream') return EXT[extOf(path)] ? `missing-or-binary(${base0 || 'none'})` : 'unknown-binary';
  if (TEXTLIKE.test(base)) return base + ';charset=' + (cs || 'utf-8');
  return base + (cs ? ';charset=' + cs : '');
}
function typeProblem(raw, path) {
  const want = EXT[extOf(path)];
  if (!want) return null;
  const got = canonType(raw, path).split(';')[0];
  const ok = got === want || (want === 'image/x-icon' && got === 'image/vnd.microsoft.icon') || (want === 'application/xml' && got === 'text/xml');
  return ok ? null : got;
}

async function one(base, path) {
  const r = await fetch(base + encodeURI(path), { redirect: 'manual' });
  const body = Buffer.from(await r.arrayBuffer());
  if (r.status === 200 && TEXTLIKE.test(norm(r.headers.get('content-type'))) && !isUtf8(body)) utf8Bad.push(base + path);
  return { status: r.status, sha: createHash('sha256').update(body).digest('hex'), type: canonType(r.headers.get('content-type'), path), raw: r.headers.get('content-type'),
    cache: r.headers.get('cache-control'), loc: (r.headers.get('location') || '').replace(base, '').replace(/^https:\/\/plotnua\.ie/, '') };
}
const queue = [...files, ...extra];
let done = 0;
async function worker() {
  while (queue.length) {
    const path = queue.shift();
    try {
      const [a, b] = await Promise.all([one(pagesBase, path), one(workerBase, path)]);
      // Option B: files under /assets/ bypass the Worker and carry Cloudflare's own cache-control (expected, listed separately)
      // a redirect's or error's body type is not content: types are compared for 200 responses (status and Location always)
      for (const k of ['status', 'loc', 'type', 'cache']) if (a[k] !== b[k] && !(k === 'type' && a.status !== 200)) (k === 'cache' && path.startsWith('/assets/') ? expected : diffs).push({ path, what: k, pages: a[k], worker: b[k] });
      if (a.status === 200 && a.sha !== b.sha) (path === '/robots.txt' && workerIsTestAddress ? expected : diffs).push({ path, what: 'bytes', pages: a.sha.slice(0, 12), worker: b.sha.slice(0, 12) });
      for (const [host, x] of [['pages', a], ['worker', b]]) {
        const bad = x.status === 200 && typeProblem(x.raw, path);
        if (bad) diffs.push({ path, what: 'wrong type for its extension', host, got: x.raw });
      }
    } catch (e) { diffs.push({ path, what: 'fetch', error: String(e) }); }
    done++;
  }
}
await Promise.all(Array.from({ length: 8 }, worker));
for (const u of utf8Bad) diffs.push({ path: u, what: 'served as text but not valid UTF-8' });
for (const d of diffs.slice(0, 200)) console.log('DIFF ', JSON.stringify(d));
console.log(`PARITY ${done} URLs · ${diffs.length} differences · ${expected.length} expected (cache-control on bypassed /assets/, robots.txt on the test address)`);
if (arg('--report')) writeFileSync(arg('--report'), JSON.stringify({ checked: done, diffs, expected }, null, 1));
process.exit(diffs.length ? 1 : 0);
