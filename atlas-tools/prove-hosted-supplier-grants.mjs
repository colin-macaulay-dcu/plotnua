#!/usr/bin/env node
/**
 * PROOF · HOSTED SUPPLIER IMAGES NEED A LIVE GRANT THAT COVERS HOSTING (P4, P4b)
 * ===========================================================================
 * 11 Nov 2026. The rights gate never sees a local file, so a supplier image that
 * PlotNua hosts itself (the first: NOOK Prefab's six supplied images) is protected
 * only by the provenance guard. This drives the REAL guard
 * (atlas-tools/validate-image-provenance.js) against a temporary copy of the REAL
 * NOOK page, its 18 hosted files, their 18 SUPPLIER_IMAGE records and the REAL
 * rights manifest, then breaks one thing per case:
 *
 *   H0  control: today's records and grant                        -> accepted
 *   H1  grant withdrawn (outcome 'Withdrawn / Superseded')        -> P4 refuses
 *   H2  grant withdrawn (withdrawal_effective_at set, outcome live)-> P4 refuses
 *   H3  grant expired (permission_expires_on yesterday)           -> P4 refuses
 *   H4  grant expired (permission.expires_on yesterday)           -> P4 refuses
 *   H5  expiry tomorrow                                           -> accepted
 *   H6  malformed expiry date                                     -> P4 refuses
 *   H7  grant row missing from the manifest                       -> P4 refuses
 *   H8  rights_ref points at another supplier's live grant        -> P4 refuses
 *   H9  outcome not a grant ('Unknown — Awaiting Reply')          -> P4 refuses
 *   H10 grant not publishable (public_visibility HOLD)            -> P4 refuses
 *   H11 permission scope lacks 'hosting'                          -> P4 refuses
 *   H12 the same grant row appears twice                          -> P4 refuses
 *   H13 the photograph's record relabelled 'Visualisation'        -> P4b refuses
 *   H14 a visualisation shown on the page as 'Photograph'         -> P4b refuses
 *   H15 a record with no supplier_label                           -> P4b refuses
 *
 * Nothing in the repository is changed: every case gets its own temporary tree.
 *   node atlas-tools/prove-hosted-supplier-grants.mjs        Exit 0 = every case behaved.
 */
import { readFileSync, writeFileSync, mkdtempSync, mkdirSync, copyFileSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const PAGE = 'suppliers/nook-prefab.html';
const ORG = 'ORG-000209';

const realReg = JSON.parse(readFileSync(join(ROOT, 'image-provenance-records.json'), 'utf8'));
const realRights = JSON.parse(readFileSync(join(ROOT, 'image-rights-manifest.json'), 'utf8'));
const nookRecs = realReg.records.filter(r => r.class === 'SUPPLIER_IMAGE' && (r.rights_ref || {}).organisation_code === ORG);
const realPage = readFileSync(join(ROOT, PAGE), 'utf8');
if (nookRecs.length !== 18) { console.log(`INSTRUMENT UNAVAILABLE: expected NOOK's 18 hosted records, found ${nookRecs.length}`); process.exit(2); }
const otherLive = realRights.rows.find(w => w.organisation_code && w.organisation_code !== ORG && w.atlas_permission_ref
  && /^Granted/.test(w.permission_outcome || '') && !w.withdrawal_effective_at);
const day = n => new Date(Date.now() + n * 864e5).toISOString().slice(0, 10);

function tree({ rowEdit = null, rowsEdit = null, regEdit = null, pageEdit = null } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'pn-hosted-'));
  mkdirSync(join(dir, 'atlas-tools'), { recursive: true });
  const reg = JSON.parse(JSON.stringify(realReg));
  // Only NOOK's records and nothing else, so the tree is small and every other check stays satisfied.
  reg.records = JSON.parse(JSON.stringify(nookRecs));
  for (const k of ['legacy_undeclared', 'derivatives', 'derivative_holds', 'staged_composites', 'brand_vector_derivatives'])
    if (Array.isArray(reg[k])) reg[k] = [];
  if (regEdit) regEdit(reg);
  writeFileSync(join(dir, 'image-provenance-records.json'), JSON.stringify(reg, null, 2));
  const rights = JSON.parse(JSON.stringify(realRights));
  const row = rights.rows.find(w => w.organisation_code === ORG);
  if (rowEdit) rowEdit(row);
  if (rowsEdit) rowsEdit(rights);
  writeFileSync(join(dir, 'image-rights-manifest.json'), JSON.stringify(rights, null, 2));
  // The real page, without the site icon link (a brand file outside this proof).
  let page = realPage.replace(/<link rel="icon"[^>]*>\n?/, '');
  if (pageEdit) page = pageEdit(page);
  mkdirSync(join(dir, 'suppliers'), { recursive: true });
  writeFileSync(join(dir, PAGE), page);
  for (const r of nookRecs) {
    mkdirSync(join(dir, dirname(r.asset)), { recursive: true });
    copyFileSync(join(ROOT, r.asset), join(dir, r.asset));
  }
  copyFileSync(join(HERE, 'validate-image-provenance.js'), join(dir, 'atlas-tools', 'validate-image-provenance.js'));
  copyFileSync(join(HERE, 'validate-image-rights.js'), join(dir, 'atlas-tools', 'validate-image-rights.js'));
  return dir;
}
function run(dir) {
  try {
    return { code: 0, out: execFileSync('node', [join(dir, 'atlas-tools', 'validate-image-provenance.js'), '--root', dir],
      { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 }) };
  } catch (e) { return { code: e.status ?? -1, out: (e.stdout || '') + (e.stderr || '') }; }
  finally { rmSync(dir, { recursive: true, force: true }); }
}
const failed = out => [...out.matchAll(/^ {2}FAIL {2}(P\d+[a-z]?)/gm)].map(m => m[1]);

const CASES = [
  ['H0', 'control: today\'s NOOK records and grant', {}, []],
  ['H1', 'grant withdrawn (outcome)', { rowEdit: w => { w.permission_outcome = 'Withdrawn / Superseded'; } }, ['P4']],
  ['H2', 'grant withdrawn (withdrawal_effective_at)', { rowEdit: w => { w.withdrawal_effective_at = day(-1); } }, ['P4']],
  ['H3', 'grant expired (permission_expires_on)', { rowEdit: w => { w.permission_expires_on = day(-1); } }, ['P4']],
  ['H4', 'grant expired (permission.expires_on)', { rowEdit: w => { w.permission.expires_on = day(-1); } }, ['P4']],
  ['H5', 'expiry tomorrow is still valid', { rowEdit: w => { w.permission_expires_on = day(1); } }, []],
  ['H6', 'malformed expiry date', { rowEdit: w => { w.permission_expires_on = 'next spring'; } }, ['P4']],
  ['H7', 'grant row missing', { rowsEdit: m => { m.rows = m.rows.filter(w => w.organisation_code !== ORG); } }, ['P4']],
  ['H8', 'rights_ref points at another supplier\'s live grant', { regEdit: r => { r.records[0].rights_ref = {
      organisation_code: otherLive.organisation_code, atlas_permission_ref: otherLive.atlas_permission_ref }; } }, ['P4']],
  ['H9', 'outcome is not a grant', { rowEdit: w => { w.permission_outcome = 'Unknown — Awaiting Reply'; } }, ['P4']],
  ['H10', 'grant not publishable', { rowEdit: w => { w.public_visibility = 'HOLD'; } }, ['P4']],
  ['H11', 'permission scope lacks hosting', { rowEdit: w => { w.permission.scope = w.permission.scope.filter(s => s !== 'hosting'); } }, ['P4']],
  ['H12', 'the grant row appears twice', { rowsEdit: m => { m.rows.push(JSON.parse(JSON.stringify(m.rows.find(w => w.organisation_code === ORG)))); } }, ['P4']],
  ['H13', 'the photograph relabelled Visualisation in its record', { regEdit: r => {
      r.records.filter(x => x.supplier_label === 'Photograph').forEach(x => { x.supplier_label = 'Visualisation'; }); } }, ['P4b']],
  ['H14', 'a visualisation shown as a Photograph on the page', { pageEdit: p => p.replace('data-kind="Visualisation"', 'data-kind="Photograph"') }, ['P4b']],
  ['H15', 'a record with no supplier_label', { regEdit: r => { delete r.records[1].supplier_label; } }, ['P4b']],
];

console.log('\nPROOF · HOSTED SUPPLIER IMAGES NEED A LIVE GRANT THAT COVERS HOSTING');
console.log('='.repeat(74));
let bad = 0;
for (const [id, why, opts, expect] of CASES) {
  const r = run(tree(opts));
  const f = failed(r.out);
  const ok = expect.length
    ? r.code === 1 && expect.every(e => f.includes(e)) && f.every(x => expect.includes(x))
    : r.code === 0 && !f.length;
  if (!ok) bad++;
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${id.padEnd(4)} ${why}  -> ${expect.length ? 'refused by ' + expect.join(', ') : 'accepted'}`
    + (ok ? '' : `   [exit ${r.code}; failed: ${f.join(', ') || 'none'}]\n        ` + r.out.split('\n').filter(l => /FAIL|UNAVAILABLE/.test(l)).slice(0, 3).join('\n        ')));
}
console.log('-'.repeat(74));
console.log(bad ? `PROOF FAILED (${bad} of ${CASES.length})` : `PROOF COMPLETE (${CASES.length} cases)`);
process.exit(bad ? 1 : 0);
