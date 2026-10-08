/* WORKER MUTATION PROOF · M27, M29, M30
 * ===========================================================================
 * prove-g3-mutations.mjs mutates the PAGE. These three mutations attack the
 * WORKER, because the code they target is in the Worker and nowhere else —
 * above all the absent-tenure refusal, which has no page equivalent at all
 * (decide() only runs once every question is answered, so inherited_tenure is
 * always own/rent/buying when the register panel exists).
 *
 * Each mutation patches a disposable copy of src/index.js, runs the real
 * prove-guards.mjs against that copy, and requires the named assertions to
 * FAIL. A mutation that fails to APPLY is reported as VACUOUS, never as a
 * pass: an unapplied mutation proves nothing, and that distinction is the one
 * that caught M7 going stale in the page harness today.
 *
 * M30 IS THE IMPORTANT ONE. Founder instruction, 8 October 2026: the
 * absent/unconfirmed-tenure divergence between FROZEN G1B §5 ("storable") and
 * the Worker ("refused") is PRESERVED, not solved, in this correction. M30
 * deletes that refusal and requires the suite to notice, so the divergence
 * cannot disappear quietly in some later pass.
 *
 *   node test/prove-worker-mutations.mjs
 * ========================================================================= */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WORKER_DIR = path.resolve(HERE, '..');
const SRC = fs.readFileSync(path.join(WORKER_DIR, 'src/index.js'), 'utf8');

/* Exact-occurrence substitution. Refuses rather than guessing, so a stale
   anchor shows up as VACUOUS instead of a silent no-op. */
function sub(text, from, to, expect = 1) {
  const n = text.split(from).length - 1;
  if (n !== expect) {
    throw new Error(`mutation did not apply: expected ${expect} occurrence(s) of ` +
                    JSON.stringify(from.slice(0, 72)) + `, found ${n}`);
  }
  return text.split(from).join(to);
}

const MUTATIONS = [
  ['M27 the buying divergence reinstated in the Worker',
   (s) => sub(s, "  if (tenure === 'rent') {", "  if (tenure !== 'own') {"),
   ['G34c', 'G34c2', 'T7b']],

  ['M29 the rent branch deleted entirely (permission no longer required)',
   (s) => sub(s,
     "  if (tenure === 'rent') {\n" +
     "    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');\n" +
     "    if (!note || note.length < 20) return REFUSED(cors, 'garden_note');\n" +
     "  }",
     "  if (false) {\n" +
     "    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');\n" +
     "    if (!note || note.length < 20) return REFUSED(cors, 'garden_note');\n" +
     "  }"),
   ['G34b', 'G35a']],

  ['M30 THE ABSENT-TENURE REFUSAL DELETED (the preserved divergence)',
   (s) => sub(s, "  if (!tenure) return REFUSED(cors, 'inherited_tenure');",
                 "  /* refusal removed */"),
   ['G35e', 'T9', 'T9b']]
];

let caught = 0, bad = 0;
const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'worker-mut-'));

/* Baseline: the suite must be green before any mutation, or a "failure" below
   proves nothing. Measured, not assumed — a baseline taken after the mutation
   was the exact fault that produced 13 false BLIND results in the G3 work. */
function runSuite(dir) {
  try {
    const out = execFileSync(process.execPath, ['test/prove-guards.mjs'],
      { cwd: dir, encoding: 'utf8', maxBuffer: 1 << 28 });
    return out;
  } catch (e) {
    return (e.stdout || '') + (e.stderr || '');
  }
}

function failedIds(out) {
  return [...out.matchAll(/\[FAIL\]\s+(\S+)/g)].map((m) => m[1]);
}

function freshCopy(src) {
  const dir = fs.mkdtempSync(path.join(tmpRoot, 'c-'));
  fs.mkdirSync(path.join(dir, 'src'), { recursive: true });
  fs.mkdirSync(path.join(dir, 'test'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'src/index.js'), src);
  for (const f of fs.readdirSync(path.join(WORKER_DIR, 'test'))) {
    fs.copyFileSync(path.join(WORKER_DIR, 'test', f), path.join(dir, 'test', f));
  }
  /* jsdom is resolved from the real worker dir; prove-guards does not need it,
     but the copy must still find node_modules if anything does. */
  try {
    fs.symlinkSync(path.join(WORKER_DIR, 'node_modules'),
                   path.join(dir, 'node_modules'), 'dir');
  } catch { /* fine: prove-guards has no runtime dependency */ }
  return dir;
}

console.log('\n  WORKER MUTATION PROOF · M27, M29, M30\n');

const baseOut = runSuite(freshCopy(SRC));
const baseFails = failedIds(baseOut);
if (baseFails.length) {
  console.log('  *** BASELINE NOT GREEN. Refusing to report mutation results,');
  console.log('      because a failure could not be attributed to a mutation.');
  console.log('      failing now: ' + baseFails.join(', '));
  fs.rmSync(tmpRoot, { recursive: true, force: true });
  process.exit(1);
}
console.log('  baseline: prove-guards.mjs green against the unmutated Worker  OK\n');

for (const [label, mutate, expected] of MUTATIONS) {
  let mutated;
  try { mutated = mutate(SRC); }
  catch (e) {
    bad++;
    console.log(`  [VACUOUS ] ${label}\n              ${e.message}`);
    continue;
  }
  const fails = failedIds(runSuite(freshCopy(mutated)));
  const missing = expected.filter((id) => !fails.includes(id));
  if (fails.length === 0) {
    bad++;
    console.log(`  [*** BLIND] ${label}\n              the suite stayed green`);
  } else if (missing.length) {
    bad++;
    console.log(`  [PARTIAL ] ${label}\n              expected ${expected.join('+')},` +
                ` missing ${missing.join(',')}; caught ${fails.join(',')}`);
  } else {
    caught++;
    const extra = fails.filter((id) => !expected.includes(id));
    console.log(`  [CAUGHT  ] ${label}\n              ${fails.length} failed: ` +
                expected.join('+') + (extra.length ? `  (also: ${extra.join(',')})` : ''));
  }
}

fs.rmSync(tmpRoot, { recursive: true, force: true });
console.log(`\n  ${caught} mutations caught, ${bad} blind, vacuous or partial\n`);
process.exit(bad ? 1 : 0);
