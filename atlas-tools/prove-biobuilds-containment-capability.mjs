/* GUARD-CAPABILITY PROOF — prove-biobuilds-containment.mjs.
   ---------------------------------------------------------------------------
   A containment check that has never refused anything is a comment. This
   breaks the containment proof once per check, in a THROWAWAY COPY of the
   tree, and every break must be caught.

   IT NEVER TOUCHES THE REAL TREE. Each scenario is built by copying the few
   files the check reads into a temporary directory alongside a copy of the
   check itself, then running it there. The real repository is hashed before
   and after and the hashes are printed: a proof that damages what it proves
   is worse than no proof.

   Run: node atlas-tools/prove-biobuilds-containment-capability.mjs          */

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const CHECK = path.join(HERE, 'prove-biobuilds-containment.mjs');
const PAGE = 'biobuilds-preview.html';

/* the files the check actually reads */
const COPY = [PAGE, 'image-rights-records.json', 'sitemap.xml',
  'atlas-match-pool.json', 'atlas-recognition-pool.json', 'atlas-stats.json'];

function hashTree() {
  const h = crypto.createHash('sha256');
  for (const f of [...COPY, 'image-rights-manifest.json'].sort()) {
    const p = path.join(ROOT, f);
    h.update(f);
    h.update(fs.existsSync(p) ? fs.readFileSync(p) : Buffer.from('ABSENT'));
  }
  return h.digest('hex');
}

const before = hashTree();
const results = [];

function scenario(label, mutate, expect = 'REFUSED') {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'bbcontain-'));
  const tools = path.join(tmp, 'atlas-tools');
  fs.mkdirSync(tools);
  for (const f of COPY) {
    const src = path.join(ROOT, f);
    if (fs.existsSync(src)) fs.copyFileSync(src, path.join(tmp, f));
  }
  fs.copyFileSync(CHECK, path.join(tools, path.basename(CHECK)));
  mutate(tmp);

  let rc = 0, out = '';
  try {
    out = execFileSync('node', [path.join(tools, path.basename(CHECK))],
      { encoding: 'utf8' });
  } catch (e) {
    rc = e.status === undefined ? 99 : e.status;
    out = (e.stdout || '') + (e.stderr || '');
  }
  const got = rc === 0 ? 'CONTAINED' : (rc === 1 ? 'REFUSED' : 'ERROR(' + rc + ')');
  const hit = got === expect;
  const first = out.split('\n').filter(l => /FAIL|ERROR /.test(l))[0] || '(nothing refused)';
  console.log('  ' + (hit ? 'CAUGHT ' : 'MISSED ') + got.padEnd(11) + label);
  console.log('         -> ' + first.trim().slice(0, 108));
  fs.rmSync(tmp, { recursive: true, force: true });
  results.push(hit);
}

const read = (d, f) => fs.readFileSync(path.join(d, f), 'utf8');
const write = (d, f, s) => fs.writeFileSync(path.join(d, f), s);

console.log('GUARD-CAPABILITY PROOF — BIOBUILDS CONTAINMENT');
console.log('='.repeat(76));

/* C1 . the imagery escapes onto a second page. The quiet failure this whole
   file exists for: the manifest row would pass it, the grant does not. */
scenario('C1 . a second page starts carrying BIOBUILDS imagery', d => {
  const html = read(d, PAGE);
  write(d, 'garden-rooms.html',
    '<html><head><meta name="robots" content="index"></head><body>'
    + (html.match(/<img[^>]+biobuilds\.com[^>]*>/) || [''])[0]
    + '<p>&copy; BIOBUILDS</p></body></html>');
});

/* C2 . the preview stops being private. */
scenario('C2 . the preview loses its noimageindex directive', d => {
  write(d, PAGE, read(d, PAGE).replace(', noimageindex', ''));
});

/* C3a . the credit, which is a condition of the grant. */
scenario('C3a . the credit is reduced to a single mention', d => {
  let html = read(d, PAGE);
  let n = 0;
  html = html.replace(/© BIOBUILDS/g, m => (++n > 1 ? 'BIOBUILDS' : m));
  write(d, PAGE, html);
});

/* C3b . the link back, the other condition. */
scenario('C3b . the link back to biobuilds.com is removed', d => {
  write(d, PAGE, read(d, PAGE)
    .replace(/href="https:\/\/www\.biobuilds\.com\/[^"]*"/g, 'href="#"'));
});

/* C4 . a sitemap entry, which is an invitation to index. */
scenario('C4 . the preview is added to the sitemap', d => {
  write(d, 'sitemap.xml', read(d, 'sitemap.xml').replace(
    '</urlset>',
    '<url><loc>https://plotnua.ie/biobuilds-preview.html</loc></url></urlset>'));
});

/* C5a . the conditional outcome is quietly upgraded to an unconditional one,
   which would read as clearance to publish. */
scenario('C5a . the outcome is upgraded to plain Granted', d => {
  write(d, 'image-rights-records.json', read(d, 'image-rights-records.json')
    .replace('Granted with Conditions — Founder Confirmed",\n      "permitted_domain": "biobuilds.com"',
             'Granted — Founder Confirmed",\n      "permitted_domain": "biobuilds.com"'));
});

/* C5b . the pre-live review condition is dropped while the outcome stays
   conditional. This is the subtler one: the row still LOOKS careful. */
scenario('C5b . the pre-live review condition is deleted', d => {
  const doc = JSON.parse(read(d, 'image-rights-records.json'));
  const row = doc.records.find(r => r.permitted_domain === 'biobuilds.com');
  row.conditions = row.conditions.filter(c => !c.includes('before it goes live'));
  write(d, 'image-rights-records.json', JSON.stringify(doc, null, 2));
});

/* C6 . an Atlas asset reached Approved and BIOBUILDS entered the Results
   pool. This is the one that would put them in front of homeowners. */
scenario('C6 . a BIOBUILDS image appears in the Results pool payload', d => {
  const pool = JSON.parse(read(d, 'atlas-match-pool.json'));
  const target = Array.isArray(pool) ? pool : (pool.products || pool.rows || pool);
  const inject = { image: { url: 'https://www.biobuilds.com/x.jpg',
    credit: '© BIOBUILDS', supplier: 'BIOBUILDS' } };
  if (Array.isArray(target)) target.push(inject);
  else target.__injected = inject;
  write(d, 'atlas-match-pool.json', JSON.stringify(pool));
});

/* AND THE UNMUTATED TREE MUST STILL PASS. A check that refuses everything is
   not a check either. */
console.log('-'.repeat(76));
scenario('the unmutated tree is contained', () => {}, 'CONTAINED');

const after = hashTree();
console.log('='.repeat(76));
const passed = results.filter(Boolean).length;
console.log(passed + ' of ' + results.length + ' checks passed');
console.log('the real tree was untouched by this proof: '
  + (before === after ? 'YES' : 'NO') + '  (' + after.slice(0, 12) + ')');
process.exit(passed === results.length && before === after ? 0 : 1);
