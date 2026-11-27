// Local test server for a site Worker build (used by the privacy regression test in CI): node serve-site-local.mjs <worker index.js> <dist> <INDEXING> <ANALYTICS>
// ASSETS is emulated from the build directory, with content types as Workers Static Assets sends them (no charset; the
// Worker adds charset=utf-8 to text types itself). Unknown extensions get no content type, as on Cloudflare.
import http from 'node:http'; import { readFileSync, statSync } from 'node:fs'; import { join } from 'node:path';
const { handle } = await import(process.argv[2]); const dist = process.argv[3];
const T = { css: 'text/css', js: 'text/javascript', html: 'text/html', svg: 'image/svg+xml', png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg',
  webp: 'image/webp', avif: 'image/avif', gif: 'image/gif', ico: 'image/x-icon', woff2: 'font/woff2', woff: 'font/woff', pdf: 'application/pdf',
  mp4: 'video/mp4', json: 'application/json', webmanifest: 'application/manifest+json', xml: 'application/xml', txt: 'text/plain' };
const ASSETS = { async fetch(req) { const p = decodeURIComponent(new URL(req.url).pathname); try { const f = join(dist, p); if (!statSync(f).isFile()) throw 0;
  const name = f.split('/').pop(); const t = name.includes('.') ? T[name.split('.').pop().toLowerCase()] : undefined;
  return new Response(readFileSync(f), { headers: t ? { 'Content-Type': t } : {} }); } catch { return new Response('nf', { status: 404 }); } } };
http.createServer(async (q, s) => { const r = await handle(new Request('http://127.0.0.1:8799' + q.url, { method: q.method }), { ASSETS, INDEXING: process.argv[4], ANALYTICS: process.argv[5] || 'off' });
  s.writeHead(r.status, Object.fromEntries(r.headers)); s.end(Buffer.from(await r.arrayBuffer())); }).listen(8799);
