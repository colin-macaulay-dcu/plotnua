/* PACKAGE N · INTRODUCTION REQUESTS · GUARD-CAPABILITY PROOF
 * Breaks exactly one thing in a disposable copy of src/introduction.js, re-runs
 * prove-introduction.mjs against it, and requires the cases that own the defect
 * to be the ones that fail. VACUOUS, BLIND and MISATTRIBUTED count as failures.
 *     node test/prove-introduction-mutations.mjs                               */
import { mkdtempSync, rmSync, mkdirSync, copyFileSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const CASES = [
  ['N1', 'introduction gate always open', ['I04', 'I05', 'I06'],
    ["export function introOpen(env, request) {", "export function introOpen(env, request) { return true;"]],
  ['N2', 'allow-list check dropped: any named supplier accepted', ['I18'],
    ["!Object.prototype.hasOwnProperty.call(INTRO_SUPPLIERS, s)) return REFUSED('supplier');", "false) return REFUSED('supplier');"],
    ["supplierName = INTRO_SUPPLIERS[s].name;", "supplierName = (INTRO_SUPPLIERS[s] || { name: s }).name;"]],
  ['N3', "founder email leaks the homeowner's email", ['I39'],
    ["      'Timeframe: ' + timeframeLabel,", "      'Timeframe: ' + timeframeLabel + ' ' + (globalThis.__e || ''),"],
    ["  if (notifyEnabled(env)) {", "  globalThis.__e = email;\n  if (notifyEnabled(env)) {"]],
  ['N4', 'status ceiling raised to FORWARDED', ['I10'],
    ["export const INTRO_STATUS = 'RECEIVED';", "export const INTRO_STATUS = 'FORWARDED';"]],
  ['N5', 'retention date dropped', ['I11', 'I12'],
    ["    delete_after: deleteAfter(now),\n", ""]],
  ['N6', 'timing check removed', ['I22', 'I23'],
    ["  if (typeof b.elapsed_ms !== 'number' || !(b.elapsed_ms >= MIN_FILL_MS)) return REFUSED('timing');", "  /* timing removed */"]],
  ['N7', 'typecast enabled', ['I10'],
    ["records: [{ fields }], typecast: false", "records: [{ fields }], typecast: true"]],
  ['N8', 'success claimed without a persisted row', ['I34'],
    ["  if (!recId) return UNAVAILABLE();", "  /* row check removed */"]],
  ['N9', 'closed payload opened to a phone field', ['I19'],
    ["const ALLOWED = ['name',", "const ALLOWED = ['phone', 'name',"]],
  ['N10', 'consent sentence no longer compared', ['I25', 'I26', 'I44', 'I45'],
    ["  if (!sameString(canonicalHash, sentHash)) return REFUSED('consent_text');", "  /* compare removed */"]],
  ['N11', 'consent tick no longer required', ['I24'],
    ["  if (b.consent !== true) return REFUSED('consent');", "  /* tick removed */"]],
  ['N12', 'founder email sent before the row is stored', ['I33'],
    ["  let recId = null;\n", "  let recId = null;\n  if (notifyEnabled(env)) { try { await sendFounderNotice(env, founderNotice('x', kind, supplierName, county, TIMEFRAMES[timeframe])); } catch {} }\n"]],
  ['N13', 'notify switch ignored', ['I35'],
    ["  return env.INTRO_NOTIFY_ENABLED === 'true' && !!env.RESEND_API_KEY &&", "  return !!env.RESEND_API_KEY &&"]],
  ['N15', 'retention trusts the Airtable formula: no expiry re-check', ['I48'],
    ["const expired = typeof f.delete_after === 'string' && f.delete_after < today;", "const expired = true;"]],
  ['N16', 'retention ignores retain_reason', ['I48'],
    ["const retained = typeof f.retain_reason === 'string' && f.retain_reason.trim() !== '';", "const retained = false;"]],
  ['N17', 'retention deletes in batches larger than Airtable allows', ['I51'],
    ["for (let i = 0; i < due.length; i += 10) {", "for (let i = 0; i < due.length; i += 100) {"],
    ["for (const id of due.slice(i, i + 10)) q.append('records[]', id);", "for (const id of due.slice(i, i + 100)) q.append('records[]', id);"]],
  ['N18', 'retention runs with every switch off', ['I47'],
    ["  return (env.INTRO_RETENTION_ENABLED === 'true' || env.INTRO_WRITES_ENABLED === 'true') &&", "  return true &&"]],
  ['N19', 'retention stops after the first page', ['I51'],
    ["    if (!j.offset) break;", "    break;"]],
  ['N14', 'honeypot ignored', ['I21'],
    ["  if (cleanText(b.gotcha, 200)) return REFUSED('gotcha');", "  /* honeypot removed */"]]
];
const failedIds = out => new Set([...out.matchAll(/^\s+FAIL\s+(I\d+)/gm)].map(m => m[1]));
let caught = 0, bad = 0;
for (const [id, label, owners, ...edits] of CASES) {
  const t = mkdtempSync(join(tmpdir(), 'pn-intro-mut-'));
  let verdict, detail = '';
  try {
    mkdirSync(join(t, 'src')); mkdirSync(join(t, 'test'));
    for (const f of ['index.js', 'introduction.js']) copyFileSync(join(ROOT, 'src', f), join(t, 'src', f));
    copyFileSync(join(ROOT, 'wrangler.toml'), join(t, 'wrangler.toml'));
    copyFileSync(join(ROOT, 'airtable-introduction-requests.json'), join(t, 'airtable-introduction-requests.json'));
    copyFileSync(join(HERE, 'prove-introduction.mjs'), join(t, 'test', 'prove-introduction.mjs'));
    writeFileSync(join(t, 'package.json'), '{"type":"module"}');
    const p = join(t, 'src', 'introduction.js'); let s = readFileSync(p, 'utf8');
    for (const [a, b] of edits) { if (s.split(a).length !== 2) throw new Error('VACUOUS:anchor not unique/found: ' + a.slice(0, 50)); s = s.replace(a, b); }
    writeFileSync(p, s);
    let out = '', code = 0;
    try { out = execFileSync(process.execPath, [join(t, 'test', 'prove-introduction.mjs')], { encoding: 'utf8' }); }
    catch (e) { out = (e.stdout || '') + (e.stderr || ''); code = 1; }
    const got = failedIds(out);
    if (code === 0 || got.size === 0) { verdict = 'BLIND'; detail = out.split('\n').slice(-3).join(' '); }
    else if (!owners.some(o => got.has(o))) { verdict = 'MISATTRIBUTED'; detail = 'expected ' + owners + ', got ' + [...got]; }
    else { verdict = 'CAUGHT'; detail = 'failed ' + [...got].join(','); }
  } catch (e) { verdict = String(e.message).startsWith('VACUOUS:') ? 'VACUOUS' : 'MISATTRIBUTED'; detail = e.message; }
  finally { rmSync(t, { recursive: true, force: true }); }
  verdict === 'CAUGHT' ? caught++ : bad++;
  console.log(`  ${id.padEnd(4)} ${verdict.padEnd(14)} ${label}\n       ${detail}`);
}
console.log(`\nINTRODUCTION MUTATIONS · ${caught}/${CASES.length} caught by the cases that own them; ${bad} blind, vacuous or misattributed`);
process.exit(bad ? 1 : 0);
