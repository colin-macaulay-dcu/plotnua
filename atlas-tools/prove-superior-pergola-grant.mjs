#!/usr/bin/env node
/* PROOF: THE SUPERIOR PERGOLA GRANT IS WHAT MAKES THE IMAGES PUBLISHABLE
 * ===========================================================================
 * The gate ALLOWs five Superior Pergola photographs. That is only worth
 * anything if the grant is what is doing the work. So each way the grant could
 * stop being live is applied to a COPY of the real manifest, and the real page
 * is re-scanned. If an image still passes, the grant was decorative.
 *
 * THE CASE THAT MATTERS MOST HERE is the shared CDN. b3819663.assetcdn.net is
 * not Superior Pergola's own domain: it is a delivery host that serves other
 * customers too. The grant is scoped to /2.0/3819663/, their account
 * namespace. If the gate would pass an image from that host OUTSIDE that
 * prefix, PlotNua would be publishing some other business's photograph on the
 * strength of Superior Pergola's permission. Cases 6-8 exist for that.
 *
 * ALL FIVE IMAGES ARE CHECKED, not the first one. A proof that watched a
 * single image would pass a manifest change that quietly authorised four
 * others.
 *
 * NOTHING IS WRITTEN to the repository. Every mutation happens in a temporary
 * manifest; the committed one is never touched.
 *
 * POWER SHEDS, YARD BOX AND TRIQBRIQ MUST STAY ALLOWED THROUGHOUT. A change
 * that quietly takes another supplier's live grant down with it is a
 * regression, not a proof.
 *
 * Run: node atlas-tools/prove-superior-pergola-grant.mjs
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

const SP = 'recEitQxMaz9SyDzX';
const PAGE = 'superior-pergola-platform-preview.html';
const OTHERS = ['powersheds-preview.html', 'yardbox-preview.html',
                'triq-cube-preview.html'];

const base = JSON.parse(readFileSync(MANIFEST, 'utf8'));
const tmp = mkdtempSync(join(tmpdir(), 'pn-sp-rights-'));

function run(manifest) {
  const p = join(tmp, 'm.json');
  writeFileSync(p, JSON.stringify(manifest));
  let out;
  try {
    out = execFileSync('node', [GATE, '--scan-html', REPO, '--permissions', p,
      '--max-age-days', '3650'], { encoding: 'utf8' });
  } catch (e) { out = (e.stdout || '') + (e.stderr || ''); }

  const lines = out.split('\n').map(l => l.trim());
  const mine = lines.filter(l => l.includes(PAGE));
  const others = lines.filter(l => OTHERS.some(o => l.includes(o)));

  let verdict;
  if (mine.length === 0) verdict = '(absent)';
  else if (mine.every(l => l.startsWith('ALLOW'))) verdict = 'ALLOW';
  else if (mine.every(l => l.startsWith('REFUSE'))) verdict = 'REFUSE';
  else verdict = 'MIXED';

  return {
    verdict,
    count: mine.length,
    why: (mine[0] || '').replace(/^(ALLOW|REFUSE)\s+\S+\s*/, '').trim(),
    othersAllowed: others.length > 0 && others.every(l => l.startsWith('ALLOW'))
  };
}

const clone = () => JSON.parse(JSON.stringify(base));
const row = (m) => m.rows.find(r => r.organisation_record === SP);

const cases = [
  ['the grant as recorded', m => m, 'ALLOW'],

  ['the grant is WITHDRAWN',
   m => { const r = row(m); r.permission_outcome = 'Withdrawn / Superseded';
          r.withdrawal_effective_at = '2026-10-15'; return m; }, 'REFUSE'],

  ['the outcome falls back to UNKNOWN',
   m => { row(m).permission_outcome = 'Unknown — Awaiting Reply'; return m; },
   'REFUSE'],

  ['the whole Superior Pergola record is REMOVED',
   m => { m.rows = m.rows.filter(r => r.organisation_record !== SP); return m; },
   'REFUSE'],

  ['the required credit is changed, so the page no longer carries it',
   m => { row(m).required_credit = 'Photo courtesy of Superior Pergola';
          return m; }, 'REFUSE'],

  // THE SHARED-CDN CASES.
  ['the scoped delivery host is DROPPED, leaving only superiorpergola.ie',
   m => { delete row(m).permitted_delivery_hosts; return m; }, 'REFUSE'],

  ['the delivery host loses its path prefix, i.e. claims the WHOLE CDN',
   m => { row(m).permitted_delivery_hosts = [{ host: 'b3819663.assetcdn.net' }];
          return m; }, 'REFUSE'],

  ['the prefix points at a DIFFERENT assetcdn account',
   m => { row(m).permitted_delivery_hosts[0].path_prefix = '/2.0/9999999/';
          return m; }, 'REFUSE']
];

console.log('PROOF — the Superior Pergola grant is load-bearing');
console.log('='.repeat(74));
let ok = true;
for (const [what, mutate, expect] of cases) {
  const r = run(mutate(clone()));
  const pass = r.verdict === expect && r.othersAllowed
               && (expect !== 'ALLOW' || r.count === 5);
  if (!pass) ok = false;
  console.log('  ' + (pass ? 'ok  ' : 'FAIL') + '  '
              + (r.verdict + '(' + r.count + ')').padEnd(11) + what);
  if (r.why) console.log('          ' + r.why.slice(0, 92));
  if (!r.othersAllowed) {
    console.log('          FAIL: another supplier stopped being allowed');
  }
  if (expect === 'ALLOW' && r.count !== 5) {
    console.log('          FAIL: expected all 5 authorised images, saw '
                + r.count);
  }
}
console.log('-'.repeat(74));
console.log(ok
  ? 'PROOF COMPLETE — every way of invalidating the grant refuses all five\n'
    + 'images, no other supplier\'s grant was disturbed, and an image from the\n'
    + 'same CDN outside Superior Pergola\'s own account namespace is refused.'
  : 'PROOF INCOMPLETE — see FAIL above');
process.exit(ok ? 0 : 1);
