/* OGNYX IMAGERY CONTAINMENT PROOF — BY ENUMERATION, PER ASSET.
   ---------------------------------------------------------------------------
   WHY THIS EXISTS (14 October 2026).

   OGNYX graduated from the preview-only register to a publication grant: on
   13 October they agreed to PlotNua featuring OGNYX and using "the selected
   product images shown there" -- the FOUR images on the preview. The rights
   manifest scopes a grant by host, so on its own the ognyx.com row would pass
   ANY image from ognyx.com on ANY page. OGNYX granted four. This file is the
   difference between the manifest row and the grant.

   WHAT IT CHECKS
     I1  Every ognyx.com image referenced anywhere in the deployed tree (pages
         and JSON payloads) is one of the four in approved_assets.
     I2  Every page that shows one carries the credit "© OGNYX" and a working
         link back to ognyx.com -- conditions of the grant, not decoration.
     I3  A visualisation is never presented as a photograph: its alt text
         says "Visualisation" wherever it appears.
     I4  The record still says what was granted: scope feature + imagery,
         exactly four enumerated assets, credit required.
     I5  No OGNYX claim the evidence does not support reaches a published
         artefact: no health, VAT, delivery, installation, lead-time, stock,
         warranty or planning claim in the wellness universe's OGNYX records
         or in the search index's OGNYX records.

   Exit 0 = contained. 1 = breach. 2 = could not establish the facts.

   Run: node atlas-tools/prove-ognyx-imagery-containment.mjs                 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
let failed = 0, confused = 0;
const ok = m => console.log('    PASS   ' + m);
const bad = (m, d) => { failed++; console.log('    FAIL   ' + m + (d ? '\n           ' + d : '')); };
const cannot = (m, d) => { confused++; console.log('    ERROR  ' + m + (d ? '\n           ' + d : '')); };

const FORBIDDEN = ['health benefit', 'therapeutic', 'improves recovery',
  'inc. vat', 'including vat', 'vat included', 'free delivery',
  'delivery included', 'delivery is free', 'installation included',
  'we install', 'fully installed', 'warranty included', 'guaranteed',
  'in stock', 'next day', 'lead time of', 'planning exempt',
  'no planning permission'];

console.log('OGNYX IMAGERY CONTAINMENT PROOF');
console.log('='.repeat(76));

let row = null;
try {
  const recs = JSON.parse(fs.readFileSync(path.join(ROOT, 'image-rights-records.json'), 'utf8')).records;
  row = recs.find(r => r.organisation_name === 'OGNYX');
} catch (e) { cannot('image-rights-records.json could not be read', e.message); }
if (!row) cannot('no OGNYX rights record');

const assets = (row && row.approved_assets) || [];
const keyOf = u => { try { const p = new URL(u.replace(/&amp;/g, '&')); return p.hostname.replace(/^www\./, '') + p.pathname; } catch { return null; } };
const approved = new Map(assets.map(a => [keyOf(a.url), a]));

/* I4 the record */
{
  const sc = (row && row.permission && row.permission.scope) || [];
  if (assets.length !== 4 || approved.size !== 4) bad('I4 exactly four enumerated assets', 'found ' + assets.length);
  else if (!sc.includes('feature') || !sc.includes('imagery')) bad('I4 the grant covers featuring and imagery', JSON.stringify(sc));
  else if (!row || row.required_credit !== '© OGNYX') bad('I4 the credit is required');
  else if (assets.filter(a => a.kind === 'visualisation').length !== 2) bad('I4 two visualisations are declared as such');
  else ok('I4 scope feature + imagery, four enumerated assets, credit © OGNYX required');
}

/* the deployed tree */
const files = [];
(function walk(d) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    if (e.name.startsWith('.') || e.name === 'node_modules') continue;
    const full = path.join(d, e.name);
    if (e.isDirectory()) walk(full);
    else if (/\.(html|json)$/.test(e.name) && !/^image-rights-(records|manifest)\.json$/.test(e.name)) files.push(full);
  }
})(ROOT);
if (!files.length) cannot('no deployed files found');

const OG = /https?:\/\/(?:www\.)?ognyx\.com\/[^"'\s)<>\\]+?\.(?:png|jpe?g|webp|gif|avif)(?:\?[^"'\s)<>\\]*)?/gi;
let carriers = 0;
for (const f of files) {
  const rel = path.relative(ROOT, f);
  const raw = fs.readFileSync(f, 'utf8');
  const src = rel.endsWith('.html') ? raw.replace(/<!--[\s\S]*?-->/g, ' ') : raw;
  const urls = [...new Set(src.match(OG) || [])];
  if (!urls.length) continue;
  carriers++;
  /* I1 */
  const foreign = urls.filter(u => !approved.has(keyOf(u)));
  if (foreign.length) bad('I1 only enumerated OGNYX images on ' + rel, foreign.map(u => u.slice(0, 90)).join('; '));
  else ok('I1 ' + rel + ': ' + urls.length + ' OGNYX image reference(s), all enumerated');
  if (!rel.endsWith('.html')) continue;
  /* I2 */
  if (!/(©|&copy;|&#169;)\s*OGNYX/.test(src)) bad('I2 ' + rel + ' credits © OGNYX');
  else if (!/href="https:\/\/(www\.)?ognyx\.com\//.test(src)) bad('I2 ' + rel + ' links back to ognyx.com');
  else ok('I2 ' + rel + ' carries the credit and the link back');
  /* I3 */
  for (const m of src.matchAll(/<img\b[^>]*>/gi)) {
    const tag = m[0];
    const s = (tag.match(/\bsrc\s*=\s*["']([^"']+)/i) || [])[1];
    const a = s && approved.get(keyOf(s));
    if (!a || a.kind !== 'visualisation') continue;
    const alt = (tag.match(/\balt\s*=\s*["']([^"']*)/i) || [])[1] || '';
    if (!/^visualisation/i.test(alt)) bad('I3 ' + rel + ' labels the visualisation as one', alt.slice(0, 80));
  }
}
if (!carriers) ok('I1 no OGNYX image appears anywhere in the deployed tree');

/* I5 published OGNYX text */
{
  const hits = [];
  const scan = (label, text) => {
    const t = String(text).toLowerCase();
    for (const c of FORBIDDEN) if (t.includes(c)) hits.push(label + ': "' + c + '"');
  };
  const W = path.join(ROOT, 'wellness-universe-v1.json');
  if (fs.existsSync(W)) {
    const u = JSON.parse(fs.readFileSync(W, 'utf8'));
    for (const p of (u.products || [])) if (p.organisation === 'OGNYX') scan('wellness ' + p.id, JSON.stringify(p));
  }
  const S = path.join(ROOT, 'search-index-v1.json');
  if (fs.existsSync(S)) {
    const ix = JSON.parse(fs.readFileSync(S, 'utf8'));
    for (const r of (ix.records || [])) if (r.organisation === 'OGNYX' || r.name === 'OGNYX') scan('search ' + r.id, JSON.stringify(r));
  }
  hits.length ? bad('I5 no unsupported OGNYX claim is published', hits.slice(0, 6).join('; '))
              : ok('I5 no health, VAT, delivery, installation, lead-time, stock, warranty or planning claim in published OGNYX records');
}

console.log('='.repeat(76));
if (confused) { console.log('NOT ESTABLISHED — the proof could not establish the facts.'); process.exit(2); }
if (failed) { console.log('BREACH — ' + failed + ' check(s) failed.'); process.exit(1); }
console.log('CONTAINED — OGNYX imagery is exactly the four enumerated assets, credited and linked wherever it appears.');
