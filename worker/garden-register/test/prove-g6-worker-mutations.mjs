/* G6 · R3 — WORKER MUTATION PROOF FOR THE DEPRECATED-FIELD SAFEGUARD
 * ===========================================================================
 * Each mutation patches a disposable copy of src/index.js, runs the real
 * prove-g6-deprecated-fields.mjs AND prove-guards.mjs against the copy, and
 * requires the OWNING assertions to fail. A mutation that does not apply is
 * VACUOUS, never a pass. The baseline must be green first. Same pattern as
 * prove-worker-mutations.mjs (M27/M29/M30), which is left as it was.
 *
 *   node test/prove-g6-worker-mutations.mjs
 * ========================================================================= */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WORKER_DIR = path.resolve(HERE, '..');
const SRC = fs.readFileSync(path.join(WORKER_DIR, 'src/index.js'), 'utf8');
const SUITES = ['test/prove-g6-deprecated-fields.mjs', 'test/prove-guards.mjs'];

function sub(text, from, to, expect = 1) {
  const n = text.split(from).length - 1;
  if (n !== expect) throw new Error(`mutation did not apply: expected ${expect} of ` +
    JSON.stringify(from.slice(0, 70)) + `, found ${n}`);
  return text.split(from).join(to);
}

const REFUSAL = "  const deprecated = deprecatedKeyIn(body);\n  if (deprecated) return REFUSED(cors, deprecated);\n";
const SWITCH = "  if (!writesEnabled(env)) return NOT_OPEN(cors);\n";

/* Apply fn to the GARDEN handler only. Several lines (the write switch, the
   privacy-version field) occur in both routes; the first run reported those
   mutations VACUOUS rather than guessing, which is the point of sub(). */
function inGarden(s, fn) {
  const h = s.indexOf('async function handleGarden(');
  const e = s.indexOf('async function handleGrower(');
  if (h < 0 || e < h) throw new Error('mutation did not apply: garden handler not found');
  return s.slice(0, h) + fn(s.slice(h, e)) + s.slice(e);
}

const MUTATIONS = [
  ['X1 the explicit refusal deleted',
   (s) => sub(s, REFUSAL, ''), ['D4', 'D5', 'D4b', 'D4c', 'D4d', 'D4e']],
  ['X2 the refusal moved behind the write switch (hidden as not_open)',
   (s) => inGarden(s, (g) => sub(sub(g, REFUSAL, ''), SWITCH, SWITCH + REFUSAL)), ['D4d']],
  ['X3 presence weakened to truthiness (empty and null slip through)',
   (s) => sub(s, '    if (Object.prototype.hasOwnProperty.call(body, k)) return k;',
                 '    if (body[k]) return k;'), ['D4', 'D5']],
  ['X4 one key dropped from the deprecated list',
   (s) => sub(s, "  'inherited_your_own_use', 'inherited_result_key'\n]);",
                 "  'inherited_your_own_use'\n]);"), ['D4', 'D5', 'D4g']],
  ['X5 a write path re-added behind the refusal (layer two removed)',
   (s) => sub(s, '  if (note) fields.garden_note = note;\n',
     '  if (note) fields.garden_note = note;\n' +
     '  if (body.inherited_result_key) fields.inherited_result_key = body.inherited_result_key;\n'),
   ['D8']],
  ['X6 required tenure no longer required',
   (s) => sub(s, "  if (!tenure) return REFUSED(cors, 'inherited_tenure');", '  /* removed */'),
   ['D3', 'G35e']],
  ['X7 the renter permission tick no longer required',
   (s) => sub(s, "    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');",
                 '    /* removed */'), ['D3', 'G34b']],
  ['X8 consent verification removed from the garden route',
   (s) => {
     const h = s.indexOf('async function handleGarden(');
     const e = s.indexOf('async function handleGrower(');
     const g = sub(s.slice(h, e),
       "  if (!sameString(consentHash, sentHash)) return REFUSED(cors, 'consent_text');",
       '  /* removed */');
     return s.slice(0, h) + g + s.slice(e);
   }, ['D6']],
  ['X9 the status ceiling raised',
   (s) => sub(s, "const SUBMIT_STATUS = 'interest_submitted';",
                 "const SUBMIT_STATUS = 'qualified_garden_opportunity';"), ['D7a', 'D7f', 'G5']],
  ['X10 the privacy version hard-coded instead of read from the environment',
   (s) => inGarden(s, (g) => sub(g, '    privacy_version: env.PRIVACY_VERSION,',
                 "    privacy_version: '2026-10-PHASE2-V2',")),
   ['D7c']]
];

function failedIds(out) {
  return [...out.matchAll(/\[FAIL\]\s+(\S+)/g)].map((m) => m[1]);
}
function runAll(dir) {
  let out = '';
  for (const s of SUITES) {
    try { out += execFileSync(process.execPath, [s], { cwd: dir, encoding: 'utf8', maxBuffer: 1 << 28 }); }
    catch (e) { out += (e.stdout || '') + (e.stderr || ''); }
  }
  return out;
}
const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'g6-worker-mut-'));
function freshCopy(src) {
  const dir = fs.mkdtempSync(path.join(tmpRoot, 'c-'));
  fs.mkdirSync(path.join(dir, 'src'), { recursive: true });
  fs.mkdirSync(path.join(dir, 'test'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'src/index.js'), src);
  for (const f of fs.readdirSync(path.join(WORKER_DIR, 'test'))) {
    fs.copyFileSync(path.join(WORKER_DIR, 'test', f), path.join(dir, 'test', f));
  }
  return dir;
}

let caught = 0, bad = 0;
try {
  console.log('\n  G6 R3 · WORKER MUTATION PROOF\n');
  const baseFails = failedIds(runAll(freshCopy(SRC)));
  if (baseFails.length) {
    console.log('  *** BASELINE NOT GREEN: ' + baseFails.join(', '));
    process.exitCode = 1;
  } else {
    console.log('  baseline: both suites green against the unmutated Worker  OK\n');
    for (const [label, mutate, expected] of MUTATIONS) {
      let m;
      try { m = mutate(SRC); } catch (e) { bad++; console.log(`  [VACUOUS ] ${label}\n              ${e.message}`); continue; }
      const fails = failedIds(runAll(freshCopy(m)));
      const missing = expected.filter((p) => !fails.some((f) => f === p));
      if (!fails.length) { bad++; console.log(`  [*** BLIND] ${label}`); }
      else if (missing.length) { bad++; console.log(`  [PARTIAL ] ${label}\n              missing ${missing.join(',')}; caught ${[...new Set(fails)].join(',')}`); }
      else { caught++; console.log(`  [CAUGHT  ] ${label}\n              ${fails.length} failed: ${expected.join('+')}`); }
    }
    console.log(`\n  ${caught} mutations caught, ${bad} blind, vacuous or partial\n`);
    process.exitCode = bad ? 1 : 0;
  }
} finally {
  fs.rmSync(tmpRoot, { recursive: true, force: true });
}
