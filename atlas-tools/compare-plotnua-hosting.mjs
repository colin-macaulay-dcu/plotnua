// Live hosting parity check for plotnua.ie (prepared 27 Nov 2026, development only).
// Compares the current GitHub Pages site with the plotnua-site Worker, file by file, before any switch-over:
//   node atlas-tools/compare-plotnua-hosting.mjs <build dir> https://plotnua.ie https://plotnua-site.colin-a41.workers.dev [--report out.json]
// For every published file (from the allowlist build) and a set of URL forms (directories, extensionless pages, 404s,
// www), it checks: status, bytes (sha256), content type, cache-control, redirects (Location) and the indexing header.
// Expected, documented differences (not failures): the Worker adds security headers (HSTS, nosniff, referrer,
// permissions, frame) and noindexes the workers.dev address. Anything else is reported and the exit code is 1.
import { readdirSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { createHash } from 'node:crypto';

const [dist, pagesBase, workerBase] = process.argv.slice(2);
const arg = k => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : null; };
const walk = d => readdirSync(d, { withFileTypes: true }).flatMap(x => x.isDirectory() ? walk(join(d, x.name)) : [join(d, x.name)]);
const files = walk(dist).map(f => '/' + relative(dist, f).split('\\').join('/')).filter(f => !/\/\.|\/_headers$/.test(f));
const extra = ['/', '/plotart', '/plotart/', '/discoveries', '/no-such-page.html', '/no-such-dir/', '/_config.yml', '/atlas-tools/', '/.github/'];
const diffs = [];
const norm = t => (t || '').toLowerCase().replace(/\s+/g, '');

async function one(base, path) {
  const r = await fetch(base + encodeURI(path), { redirect: 'manual' });
  const body = Buffer.from(await r.arrayBuffer());
  return { status: r.status, sha: createHash('sha256').update(body).digest('hex'), type: norm(r.headers.get('content-type')),
    cache: r.headers.get('cache-control'), loc: (r.headers.get('location') || '').replace(base, '').replace(/^https:\/\/plotnua\.ie/, '') };
}
const queue = [...files, ...extra];
let done = 0;
async function worker() {
  while (queue.length) {
    const path = queue.shift();
    try {
      const [a, b] = await Promise.all([one(pagesBase, path), one(workerBase, path)]);
      for (const k of ['status', 'loc', 'type', 'cache']) if (a[k] !== b[k]) diffs.push({ path, what: k, pages: a[k], worker: b[k] });
      if (a.status === 200 && a.sha !== b.sha) diffs.push({ path, what: 'bytes', pages: a.sha.slice(0, 12), worker: b.sha.slice(0, 12) });
    } catch (e) { diffs.push({ path, what: 'fetch', error: String(e) }); }
    done++;
  }
}
await Promise.all(Array.from({ length: 8 }, worker));
for (const d of diffs.slice(0, 40)) console.log('DIFF ', JSON.stringify(d));
console.log(`PARITY ${done} URLs · ${diffs.length} differences`);
if (arg('--report')) writeFileSync(arg('--report'), JSON.stringify({ checked: done, diffs }, null, 1));
process.exit(diffs.length ? 1 : 0);
