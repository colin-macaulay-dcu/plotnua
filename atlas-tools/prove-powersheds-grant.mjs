#!/usr/bin/env node
/* PROOF: THE POWER SHEDS GRANT IS WHAT MAKES THE IMAGE PUBLISHABLE
 * ===========================================================================
 * The gate now ALLOWs the Power Sheds photograph. That is only worth anything
 * if the grant is what is doing the work. So each way the grant could stop
 * being live is applied to a COPY of the real manifest, and the real page is
 * re-scanned. If the image still passes, the grant was decorative.
 *
 * NOTHING IS WRITTEN to the repository. Every mutation happens in a temporary
 * manifest; the committed one is never touched.
 *
 * TRIQBRIQ MUST STAY ALLOWED THROUGHOUT. A change that quietly takes another
 * supplier's live grant down with it is a regression, not a proof.
 *
 * Run: node atlas-tools/prove-powersheds-grant.mjs
 */
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..');
const GATE = join(HERE, 'validate-image-rights.js');
const MANIFEST = join(REPO, 'image-rights-manifest.json');
const PS = 'recZyvRt8pDg5spUU';
const TRIQ = 'recztK0C8LeTavhVJ';

const base = JSON.parse(readFileSync(MANIFEST, 'utf8'));
const tmp = mkdtempSync(join(tmpdir(), 'pn-rights-'));

function run(manifest) {
  const p = join(tmp, 'm.json');
  writeFileSync(p, JSON.stringify(manifest));
  let out;
  try {
    out = execFileSync('node', [GATE, '--scan-html', REPO, '--permissions', p,
      '--max-age-days', '3650'], { encoding: 'utf8' });
  } catch (e) { out = (e.stdout || '') + (e.stderr || ''); }
  const line = out.split('\n').find(l => l.includes('powersheds-preview.html')) || '';
  const triq = out.split('\n').filter(l => l.includes('triq-cube-preview.html'));
  return {
    ps: line.trim().startsWith('ALLOW') ? 'ALLOW' : (line.trim().startsWith('REFUSE') ? 'REFUSE' : '(absent)'),
    why: line.replace(/^\s*(ALLOW|REFUSE)\s+\S+\s*/, '').trim(),
    triqAllowed: triq.length > 0 && triq.every(l => l.trim().startsWith('ALLOW'))
  };
}

const clone = () => JSON.parse(JSON.stringify(base));
const row = (m, org) => m.rows.find(r => r.organisation_record === org);

const cases = [
  ['the grant as recorded', m => m],

  ['the grant is WITHDRAWN',
   m => { const r = row(m, PS); r.permission_outcome = 'Withdrawn / Superseded';
          r.withdrawal_effective_at = '2026-10-15'; return m; }],

  ['the outcome falls back to UNKNOWN',
   m => { row(m, PS).permission_outcome = 'Unknown — Awaiting Reply'; return m; }],

  ['the whole Power Sheds record is REMOVED',
   m => { m.rows = m.rows.filter(r => r.organisation_record !== PS); return m; }],

  ['the required credit is changed, so the page no longer carries it',
   m => { row(m, PS).required_credit = 'Photo courtesy of Power Sheds'; return m; }],

  ['the scoped delivery host is DROPPED, leaving only powersheds.com',
   m => { delete row(m, PS).permitted_delivery_hosts; return m; }],

  ['the delivery host loses its path prefix, i.e. claims the whole CDN',
   m => { row(m, PS).permitted_delivery_hosts = [{ host: 'cdn.shopify.com' }]; return m; }],

  ['the prefix points at a DIFFERENT Shopify store',
   m => { row(m, PS).permitted_delivery_hosts[0].path_prefix = '/s/files/1/9999/9999/'; return m; }]
];

console.log('PROOF — the Power Sheds grant is load-bearing');
console.log('='.repeat(74));
let ok = true;
let first = true;
for (const [what, mutate] of cases) {
  const r = run(mutate(clone()));
  const expect = first ? 'ALLOW' : 'REFUSE';
  const pass = r.ps === expect && r.triqAllowed;
  if (!pass) ok = false;
  console.log('  ' + (pass ? 'ok  ' : 'FAIL') + '  ' + r.ps.padEnd(7) + what);
  if (r.why) console.log('          ' + r.why.slice(0, 96));
  if (!r.triqAllowed) console.log('          FAIL: TRIQBRIQ stopped being allowed');
  first = false;
}
console.log('-'.repeat(74));
console.log(ok
  ? 'PROOF COMPLETE — every way of invalidating the grant refuses the image,\n'
    + 'and TRIQBRIQ stayed allowed throughout.'
  : 'PROOF INCOMPLETE — see FAIL above');
process.exit(ok ? 0 : 1);
