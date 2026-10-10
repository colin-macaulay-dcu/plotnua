/* GARDEN ROOM LEAD WORKER · GUARD-CAPABILITY PROOF
 * ===========================================================================
 * prove-lead-worker.mjs asserts behaviour. This asserts THAT PROOF CAN FAIL.
 *
 * Each case copies the Worker and its proof to a disposable tree, breaks
 * exactly one thing, re-runs the proof against the copy, and requires the
 * SPECIFIC cases owning that defect to be the ones that fail.
 *
 * Counted as FAILURES, not successes:
 *   VACUOUS        the mutation did not change the file, so nothing was tested
 *   BLIND          the mutation was real and the proof still passed everything
 *   MISATTRIBUTED  the proof failed, but not on the cases that own the defect
 *
 * Every mutation here is a real way this could regress, and three of them
 * (M1, M4, M7) are the ones that would quietly expose a homeowner's details or
 * claim a lead that does not exist.
 *
 *     node test/prove-lead-mutations.mjs
 * ========================================================================= */

import { mkdtempSync, rmSync, mkdirSync, copyFileSync, readFileSync, writeFileSync }
  from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC = join(HERE, '..', 'src', 'index.js');
const PROOF = join(HERE, 'prove-lead-worker.mjs');

function disposable() {
  const t = mkdtempSync(join(tmpdir(), 'glead-'));
  mkdirSync(join(t, 'src')); mkdirSync(join(t, 'test'));
  copyFileSync(SRC, join(t, 'src', 'index.js'));
  copyFileSync(PROOF, join(t, 'test', 'prove-lead-worker.mjs'));
  writeFileSync(join(t, 'package.json'), '{"type":"module"}');
  return t;
}

function patch(tree, find, replace, count = 1) {
  const p = join(tree, 'src', 'index.js');
  const t = readFileSync(p, 'utf8');
  const n = t.split(find).length - 1;
  if (n !== count) throw new Error('anchor found ' + n + ' times, expected ' + count);
  const out = t.replace(find, replace);
  if (out === t) throw new Error('replacement produced no change');
  writeFileSync(p, out);
}

/* --------------------------------------------------------------- the cases */
const CASES = [
  ['M1', 'release gate removed entirely', ['L01', 'L02', 'L03'], (t) =>
    patch(t, '    if (!releaseOpen(env, request)) return NOT_OPEN(cors);',
             '    /* gate removed */')],

  ['M2', 'releaseOpen always true', ['L01', 'L02', 'L03'], (t) =>
    patch(t, 'function releaseOpen(env, request) {',
             'function releaseOpen(env, request) { return true;')],

  ['M3', 'preview key length floor dropped', ['L03'], (t) =>
    patch(t, '  if (typeof key !== \'string\' || key.length < 16) return false;',
             '  if (typeof key !== \'string\') return false;')],

  ['M4', 'allow-list made permissive: unknown supplier falls back to the first', ['L06'], (t) =>
    patch(t, '  const supplier = orgId ? SUPPLIERS[orgId] : null;',
             '  const supplier = (orgId ? SUPPLIERS[orgId] : null) || Object.values(SUPPLIERS)[0];')],

  ['M5', 'allow-list made permissive: unknown product falls back to the first', ['L07', 'L09'], (t) =>
    patch(t, '  const product = productId ? supplier.products[productId] : null;',
             '  const product = (productId ? supplier.products[productId] : null) || Object.values(supplier.products)[0];')],

  ['M6', 'consent sentence no longer compared', ['L17'], (t) =>
    patch(t, '  if (!sameString(canonicalHash, sentHash)) return REFUSED(cors, \'consent_text\');',
             '  /* consent comparison removed */')],

  ['M7', 'consent tick no longer required', ['L16'], (t) =>
    patch(t, '  if (body.consent !== true) return REFUSED(cors, \'consent\');',
             '  /* consent tick removed */')],

  ['M8', 'success claimed without a persisted record id', ['L22'], (t) =>
    patch(t, '  if (!recId) return UNAVAILABLE(cors, \'atnorec\');',
             '  /* record id no longer required */')],

  ['M9', 'typecast:false dropped', ['L29'], (t) =>
    patch(t, '            { records: [{ fields }], typecast: false });',
             '            { records: [{ fields }], typecast: true });')],

  ['M10', 'a CRM field creeps into the row', ['L32'], (t) =>
    patch(t, '    status: SUBMIT_STATUS\n  };',
             '    status: SUBMIT_STATUS,\n    lead_score: 7\n  };')],

  ['M11', 'Phase A test marker removed', ['L33'], (t) =>
    patch(t, '    fields.message = \'[PLOTNUA PHASE A TEST LEAD — NOT A HOMEOWNER]\\n\\n\' + message;',
             '    fields.message = message;')],

  ['M12', 'a GET handler appears', ['L35'], (t) =>
    patch(t, '    if (request.method !== \'POST\') {',
             '    if (request.method === \'GET\') return json(200, { ok: true }, cors);\n    if (request.method !== \'POST\') {')],

  ['M13', 'origin check dropped', ['L37'], (t) =>
    patch(t, '    if (!cors) return json(403, { ok: false, state: \'refused\' }, null);',
             '    /* origin check removed */')],

  ['M14', 'honeypot no longer checked', ['L15'], (t) =>
    patch(t, '  if (cleanText(body.gotcha, 200)) return REFUSED(cors, \'gotcha\');',
             '  /* honeypot removed */')],

  ['M15', 'lead_id taken from the caller instead of minted', ['L43'], (t) =>
    patch(t, '  const leadId = mintLeadId(now);',
             '  const leadId = (typeof body.lead_id === \'string\' && body.lead_id) || mintLeadId(now);')],

  ['M16', 'a second supplier added to the allow-list', ['L06'], (t) =>
    patch(t, 'const SUPPLIERS = {\n  \'ORG-000157\': {',
             'const SUPPLIERS = {\n  \'ORG-000195\': { name: \'TRIQBRIQ AG\', atlasRecord: \'x\', consentText: \'x\', products: {} },\n  \'ORG-000157\': {')],

  ['M17', 'rate limit removed', ['L39'], (t) =>
    patch(t, '    if (tooMany(\'post\', Date.now(), 20, 60_000)) return SLOW_DOWN(cors);',
             '    /* rate limit removed */')],

  ['M18', 'fetch-metadata check dropped', ['L38'], (t) =>
    patch(t, '    if (!fetchMetadataOk(request)) return REFUSED(cors);',
             '    /* fetch metadata check removed */')]
];

/* -------------------------------------------------------------------- run */
function failedIds(out) {
  return new Set([...out.matchAll(/^\s*\[FAIL\]\s+(L\d+)/gm)].map(m => m[1]));
}

console.log('\n  GARDEN ROOM LEAD WORKER · GUARD-CAPABILITY PROOF');
console.log('  ' + CASES.length + ' mutations\n');

/* CONTROL. The unmutated proof must pass, or every verdict below is noise. */
{
  const t = disposable();
  let out = '', code = 0;
  try { out = execFileSync(process.execPath, [join(t, 'test', 'prove-lead-worker.mjs')],
                           { encoding: 'utf8' }); }
  catch (e) { out = (e.stdout || '') + (e.stderr || ''); code = 1; }
  rmSync(t, { recursive: true, force: true });
  if (code !== 0) { console.log(out); console.log('\n  CONTROL FAILED — the unmutated proof does not pass.\n'); process.exit(1); }
  console.log('  control  unmutated proof passes  OK\n');
}

let caught = 0, blind = 0, vacuous = 0, wrong = 0;
for (const [id, label, owners, mutate] of CASES) {
  const t = disposable();
  let verdict, detail;
  try {
    const before = readFileSync(join(t, 'src', 'index.js'), 'utf8');
    try { mutate(t); } catch (e) { throw new Error('VACUOUS:' + e.message); }
    const after = readFileSync(join(t, 'src', 'index.js'), 'utf8');
    if (before === after) throw new Error('VACUOUS:file unchanged');

    let out = '', code = 0;
    try { out = execFileSync(process.execPath, [join(t, 'test', 'prove-lead-worker.mjs')],
                             { encoding: 'utf8' }); }
    catch (e) { out = (e.stdout || '') + (e.stderr || ''); code = 1; }

    const got = failedIds(out);
    if (code === 0 || got.size === 0) { verdict = 'BLIND'; detail = 'mutation real, proof passed'; }
    else if (!owners.some(o => got.has(o))) {
      verdict = 'MISATTRIBUTED'; detail = 'expected ' + owners.join('/') + ', got ' + [...got].join(',');
    } else {
      verdict = 'CAUGHT'; detail = 'failed ' + [...got].join(',') + ' (owns ' + owners.join('/') + ')';
    }
  } catch (e) {
    if (String(e.message).startsWith('VACUOUS:')) { verdict = 'VACUOUS'; detail = e.message.slice(8); }
    else { verdict = 'MISATTRIBUTED'; detail = e.message; }
  } finally {
    rmSync(t, { recursive: true, force: true });
  }

  if (verdict === 'CAUGHT') caught++;
  else if (verdict === 'BLIND') blind++;
  else if (verdict === 'VACUOUS') vacuous++;
  else wrong++;

  console.log('  ' + id.padEnd(4) + ' ' + verdict.padEnd(14) + ' ' + label);
  console.log('       ' + detail);
}

console.log('\n  ' + caught + '/' + CASES.length + ' caught by the cases that own them.');
console.log('  blind          ' + blind);
console.log('  vacuous        ' + vacuous);
console.log('  misattributed  ' + wrong + '\n');
process.exit(caught === CASES.length ? 0 : 1);
