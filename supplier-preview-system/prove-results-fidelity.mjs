/* PROVE RESULTS FIDELITY — Supplier Preview System v2 (27 Oct 2026).

   A supplier preview's demonstration must match production Your Plot Results,
   not merely resemble it. This proof loads the REAL your-plot.html, puts the
   preview's own hero markup into production's #matchPrimary, and compares the
   computed style of every hero element with the same element on the preview.

   Usage (from the repository root):
     node supplier-preview-system/prove-results-fidelity.mjs <preview.html> [more.html ...]

   It serves the repository root and the preview's folder itself, on two free
   local ports. Exit 0 = identical at 1440 px (widths may differ at 768/390,
   because the preview frame is narrower than a full window); exit 1 = a real
   difference, printed. Needs Playwright (preinstalled in the build sandbox). */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
let chromium;
for (const p of ['playwright', '/home/claude/.npm-global/lib/node_modules/playwright/index.mjs']) {
  try { ({ chromium } = await import(p)); break; } catch (e) { /* next */ }
}
if (!chromium) { console.log('ERROR  Playwright not available'); process.exit(2); }

const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2' };
function serve(dir) {
  return new Promise(res => {
    const s = http.createServer((q, r) => {
      const f = path.join(dir, decodeURIComponent(q.url.split('?')[0]));
      if (!f.startsWith(dir) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); }
      r.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' });
      fs.createReadStream(f).pipe(r);
    }).listen(0, '127.0.0.1', () => res(s));
  });
}

const SEL = ['.results-hero-inner', '.rh-identity', '.results-hero-name', '.results-hero-org',
  '.results-hero-price', '.rh-identity-sep', '.results-hero-media', '.results-hero-body',
  '.results-hero-area', '.prop-confirm', '.prop-confirm-place', '.results-hero-editorial',
  '.results-hero-budget-note', '.match-card-save-primary', '.match-card-open-myplot-link',
  '.hero-secondary', '.hero-secondary-link', '.pn-mark-heart'];
const PROPS = ['color', 'backgroundColor', 'fontFamily', 'fontSize', 'fontWeight', 'fontStyle',
  'lineHeight', 'letterSpacing', 'textTransform', 'borderTopLeftRadius', 'borderTopWidth',
  'borderTopColor', 'borderBottomColor', 'paddingTop', 'paddingLeft', 'boxShadow', 'width',
  'display', 'flexDirection', 'gap'];
function grab({ SEL, PROPS }) {
  const o = {}; const root = document.getElementById('matchPrimary');
  for (const s of SEL) { const e = root.querySelector(s); if (!e) { o[s] = null; continue; }
    const c = getComputedStyle(e); o[s] = {}; for (const p of PROPS) o[s][p] = c[p]; }
  return o;
}

const files = process.argv.slice(2);
if (!files.length) { console.log('usage: prove-results-fidelity.mjs <preview.html> ...'); process.exit(2); }
const repo = await serve(ROOT);
const browser = await chromium.launch();
let fail = 0;
for (const f of files) {
  const abs = path.resolve(f);
  const page = await serve(path.dirname(abs));
  const html = fs.readFileSync(abs, 'utf8');
  const m = html.match(/<div class="results-hero" id="matchPrimary">\n([\s\S]*?)\n      <\/div><\/div><\/section><\/div>/);
  if (!m) { console.log('ERROR  ' + f + ': no production Results chain found'); fail++; continue; }
  console.log('RESULTS FIDELITY · ' + path.basename(f));
  for (const w of [1440, 768, 390]) {
    const p = await browser.newPage({ viewport: { width: w, height: 900 } });
    await p.goto(`http://127.0.0.1:${page.address().port}/${path.basename(abs)}`, { waitUntil: 'networkidle' });
    const prev = await p.evaluate(grab, { SEL, PROPS });
    const q = await browser.newPage({ viewport: { width: w, height: 900 } });
    await q.goto(`http://127.0.0.1:${repo.address().port}/your-plot.html`, { waitUntil: 'domcontentloaded' });
    await q.waitForTimeout(4000);
    await q.evaluate(h => { document.getElementById('screen-match-results').classList.remove('is-hidden');
      document.getElementById('matchPrimary').innerHTML = h; }, m[1]);
    await q.waitForTimeout(600);
    const prod = await q.evaluate(grab, { SEL, PROPS });
    let n = 0; const diffs = [];
    for (const s of SEL) {
      if (!prev[s] || !prod[s]) { if (prev[s] || prod[s]) diffs.push([s, 'missing']); continue; }
      for (const k of PROPS) { n++; if (prev[s][k] !== prod[s][k]) diffs.push([s, k, prev[s][k], prod[s][k]]); }
    }
    const real = diffs.filter(d => !(d[1] === 'width' && w < 1440));
    console.log(`  ${w}px  ${n} values compared · ${real.length ? real.length + ' DIFFERENT' : 'identical'}`
      + (diffs.length - real.length ? ` (${diffs.length - real.length} widths differ: narrower frame)` : ''));
    for (const d of real) console.log('         ' + JSON.stringify(d));
    if (real.length) fail++;
    await p.close(); await q.close();
  }
  page.close();
}
await browser.close(); repo.close();
console.log(fail ? 'FIDELITY NOT ESTABLISHED' : 'FIDELITY OK — the demonstration matches production Your Plot Results');
process.exit(fail ? 1 : 0);
