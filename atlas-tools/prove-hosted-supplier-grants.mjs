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
 *   H16 grant lacks 'label-visualisations' (11 Nov 2026)          -> P4 refuses the
 *       15 visualisation copies only; the photograph's 3 stay accepted
 *
 * C · ONE GRANT RULE (11 Nov 2026). A table of grant states is applied twice:
 * to NOOK's hosted copies through the real guard, and to an externally hosted
 * NOOK image through the real rights gate command (--assets). Both must reach
 * the same verdict for every state. S1 also checks the guard keeps no copy of
 * the live-grant vocabulary of its own.
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
  ['H16', 'grant does not cover visualisations (no label-visualisations)', { rowEdit: w => {
      w.permission.conditions = w.permission.conditions.filter(c => c !== 'label-visualisations'); } }, ['P4'], /^ {2}FAIL {2}P4 .*\b15 refused/m],
];

console.log('\nPROOF · HOSTED SUPPLIER IMAGES NEED A LIVE GRANT THAT COVERS HOSTING');
console.log('='.repeat(74));
let bad = 0;
for (const [id, why, opts, expect, mustSay] of CASES) {
  const r = run(tree(opts));
  const f = failed(r.out);
  const ok = (expect.length
    ? r.code === 1 && expect.every(e => f.includes(e)) && f.every(x => expect.includes(x))
    : r.code === 0 && !f.length) && (!mustSay || mustSay.test(r.out));
  if (!ok) bad++;
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${id.padEnd(4)} ${why}  -> ${expect.length ? 'refused by ' + expect.join(', ') : 'accepted'}`
    + (ok ? '' : `   [exit ${r.code}; failed: ${f.join(', ') || 'none'}]\n        ` + r.out.split('\n').filter(l => /FAIL|UNAVAILABLE/.test(l)).slice(0, 3).join('\n        ')));
}

/* C · ONE GRANT RULE. The same grant row, the same verdict, hosted or not. */
console.log('-'.repeat(74));
console.log('C · one grant rule: hosted copies (guard P4) and an externally hosted image (gate) agree');
const GATE = join(HERE, 'validate-image-rights.js');
function gateVerdict(rowEdit) {
  const dir = mkdtempSync(join(tmpdir(), 'pn-hosted-gate-'));
  try {
    const rights = JSON.parse(JSON.stringify(realRights));
    const row = rights.rows.find(w => w.organisation_code === ORG);
    rowEdit(row);
    writeFileSync(join(dir, 'perms.json'), JSON.stringify(rights));
    writeFileSync(join(dir, 'assets.json'), JSON.stringify([{ asset_name: 'nook-hotlinked.jpg',
      organisation_record: row.organisation_record, rights_status: 'Supplier Provided', publication_status: 'Published',
      source_url: 'https://' + row.permitted_domain + '/x.jpg', required_credit: row.required_credit }]));
    execFileSync('node', [GATE, '--assets', join(dir, 'assets.json'), '--permissions', join(dir, 'perms.json')],
      { encoding: 'utf8', stdio: 'pipe' });
    return 'live';
  } catch (e) { return e.status === 1 || e.status === 2 ? 'refused' : 'error ' + e.status; }
  finally { rmSync(dir, { recursive: true, force: true }); }
}
const STATES = [
  ['C1', 'valid, no expiry', w => {}, 'live'],
  ['C2', 'expires tomorrow (permission_expires_on)', w => { w.permission_expires_on = day(1); }, 'live'],
  ['C3', 'expires today', w => { w.permission_expires_on = day(0); }, 'refused'],
  ['C4', 'expired yesterday (permission.expires_on)', w => { w.permission.expires_on = day(-1); }, 'refused'],
  ['C5', 'malformed expiry', w => { w.permission_expires_on = '11/12/2027'; }, 'refused'],
  ['C6', 'impossible expiry (30 February)', w => { w.permission_expires_on = '2027-02-30'; }, 'refused'],
  ['C7', 'withdrawn (outcome)', w => { w.permission_outcome = 'Withdrawn / Superseded'; }, 'refused'],
  ['C8', 'withdrawn (date only)', w => { w.withdrawal_effective_at = day(-1); }, 'refused'],
  ['C9', 'not a grant (Unknown — Awaiting Reply)', w => { w.permission_outcome = 'Unknown — Awaiting Reply'; }, 'refused'],
  ['C10', 'unrecognised outcome', w => { w.permission_outcome = 'Granted, probably'; }, 'refused'],
];
for (const [id, why, edit, want] of STATES) {
  const hosted = run(tree({ rowEdit: edit }));
  const h = hosted.code === 0 ? 'live' : failed(hosted.out).includes('P4') ? 'refused' : 'error ' + hosted.code;
  const g = gateVerdict(edit);
  const ok = h === want && g === want;
  if (!ok) bad++;
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${id.padEnd(4)} ${why}  -> hosted ${h}, externally hosted ${g}` + (ok ? '' : `  [want ${want}]`));
}
/* S1 · the guard keeps no live-grant vocabulary of its own. */
{
  const guard = readFileSync(join(HERE, 'validate-image-provenance.js'), 'utf8');
  const own = ['Granted — Founder Confirmed', 'Granted with Conditions — Founder Confirmed', 'Granted — Supplier Confirmed (one-click)']
    .filter(s => guard.includes("'" + s + "'") || guard.includes('"' + s + '"'));
  const uses = /RIGHTS_GATE\.grantStatus\(/.test(guard);
  const ok = !own.length && uses;
  if (!ok) bad++;
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  S1   the guard holds no copy of the live-grant list and calls the gate's grantStatus`
    + (ok ? '' : `  [own copies: ${own.length}; calls grantStatus: ${uses}]`));
}
const total = CASES.length + STATES.length + 1;
console.log('-'.repeat(74));
console.log(bad ? `PROOF FAILED (${bad} of ${total})` : `PROOF COMPLETE (${total} cases)`);
process.exit(bad ? 1 : 0);
