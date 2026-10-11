/**
 * GUARD-CAPABILITY PROOF — THE FOUNDER-EXCEPTION GUARDS CAN ACTUALLY FAIL
 * =======================================================================
 * This mechanism lets a founder publish a supplier before one of the gate's
 * conditions is met. Guards around something like that have to be shown to
 * bite, not asserted to. Each case below breaks ONE thing in a DISPOSABLE
 * copy and requires the named check to fail.
 *
 *   VACUOUS       the suite passed anyway — the guard cannot see the defect
 *   BLIND         the suite errored or refused — it measured nothing
 *   MISATTRIBUTED something failed, but not the check that should have
 *
 * all count as failures of the PROOF. The control runs first, unmutated; if
 * it does not pass, every later result is meaningless and the proof stops.
 *
 * NOTHING IN THE REPOSITORY IS MUTATED. Each case gets its own temporary
 * tree holding copies of the gate module, the suite and the records.
 *
 *   node atlas-tools/prove-founder-exception-capability.mjs
 *
 * Exit 0 = every guard proved capable.
 */
import { readFileSync, writeFileSync, mkdtempSync, mkdirSync, copyFileSync,
         existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const GATE = join(HERE, 'publication-gate.mjs');
const BAK = join(HERE, 'publication-gate.mjs.bak');
const SUITE = join(HERE, 'prove-founder-exception.mjs');
const RECORDS = join(ROOT, 'image-rights-records.json');

for (const f of [GATE, BAK, SUITE, RECORDS]) {
  if (!existsSync(f)) {
    console.log('\nINSTRUMENT UNAVAILABLE: ' + f + ' is missing. The proof '
                + 'measured nothing.');
    process.exit(2);
  }
}
const gateSrc = readFileSync(GATE, 'utf8');
const recSrc = readFileSync(RECORDS, 'utf8');

let proved = 0, broken = 0;
const log = s => console.log(s);

function run(treeRoot) {
  const args = [join(treeRoot, 'atlas-tools', 'prove-founder-exception.mjs'),
                '--records', join(treeRoot, 'image-rights-records.json')];
  try {
    return { code: 0, out: execFileSync('node', args,
      { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 }) };
  } catch (e) {
    return { code: e.status === undefined ? -1 : e.status,
             out: (e.stdout || '') + (e.stderr || '') };
  }
}
const failedIds = o =>
  [...o.matchAll(/^ {2}FAIL {2}(FX\d+[a-z]?)/gm)].map(m => m[1]);

/* A disposable tree. gateEdit and recordEdit are functions; either may be
   null to leave that file as it is. */
function tree(gateEdit, recordEdit) {
  const dir = mkdtempSync(join(tmpdir(), 'pn-fx-'));
  mkdirSync(join(dir, 'atlas-tools'), { recursive: true });
  let gate = gateSrc;
  if (gateEdit) {
    const next = gateEdit(gate);
    if (next === gate) return { error: 'the gate mutation changed nothing' };
    gate = next;
  }
  let rec = recSrc;
  if (recordEdit) {
    const parsed = JSON.parse(rec);
    const list = Array.isArray(parsed) ? parsed
      : Object.values(parsed).find(v => Array.isArray(v) && v[0]
                                        && typeof v[0] === 'object');
    recordEdit(list, parsed);
    rec = JSON.stringify(parsed, null, 2) + '\n';
    if (rec === recSrc) return { error: 'the record mutation changed nothing' };
  }
  writeFileSync(join(dir, 'atlas-tools', 'publication-gate.mjs'), gate);
  writeFileSync(join(dir, 'image-rights-records.json'), rec);
  copyFileSync(SUITE, join(dir, 'atlas-tools', 'prove-founder-exception.mjs'));
  // FX15 lifts the pre-change derivation from the .bak sidecar, so the tree
  // needs it too or that check goes BLIND rather than measuring.
  copyFileSync(BAK, join(dir, 'atlas-tools', 'publication-gate.mjs.bak'));
  return { root: dir };
}
const bb = list => list.find(r => r.organisation_code === 'ORG-000153');
const swap = (find, replace) => src => {
  if (!src.includes(find)) return src;
  return src.replace(find, replace);
};

console.log('\nGUARD-CAPABILITY PROOF · FOUNDER EXCEPTION');
console.log('='.repeat(74));

/* ── CONTROL ─────────────────────────────────────────────────────────── */
{
  const t = tree(null, null);
  if (t.error) {
    log('  CONTROL BLIND — ' + t.error);
    process.exit(1);
  }
  const r = run(t.root);
  if (r.code !== 0) {
    log('  CONTROL FAILED — the unmutated suite does not pass in a '
        + 'disposable tree:');
    log('    ' + r.out.split('\n').filter(l => /FAIL|UNAVAILABLE/.test(l))
                   .slice(0, 4).join('\n    '));
    log('  Every result after this would be meaningless. Stopping.');
    process.exit(1);
  }
  log('  CONTROL  the unmutated suite passes in a disposable tree — the '
      + 'instrument works');
  log('-'.repeat(74));
}

const CASES = [
  /* ── the bright line ───────────────────────────────────────────────── */
  { id: 'C-FX10', expect: ['FX10', 'FX11'],
    why: 'no-permission is removed from NEVER_WAIVABLE',
    gate: swap('  "no-permission",\n  "permission-conditional-unresolved"',
               '  "permission-conditional-unresolved"') },

  /* RE-AIMED. The first version of this case removed the loop's re-check and
     the suite passed: the VALIDATOR had already rejected the exception, so
     the loop never saw a forbidden reason. That is defence in depth working
     as intended, and no behavioural test can separate the layers -- FX17 now
     asserts the second layer structurally and says so. What IS testable is
     BOTH layers going at once, which is the state a careless refactor
     actually produces. */
  { id: 'C-FX11', expect: ['FX11'],
    why: 'the bright line is dismantled at all THREE layers at once',
    /* RE-AIMED TWICE, and the second attempt taught me something. Removing
       the loop's re-check did nothing (the validator caught it). Removing the
       validator's NEVER_WAIVABLE branch did nothing either -- because
       'no-permission' is also absent from the WAIVABLE_HOLD_REASONS
       allowlist, so the next branch rejected it anyway. The bright line is
       held by THREE independent layers, not two, and the allowlist is the
       one actually doing the work. Only taking all three down publishes an
       unpermitted supplier, and FX11 has to catch that. */
    gate: src => src
      .replace('if (accepted.includes(reason) && !NEVER_WAIVABLE.includes(reason))',
               'if (accepted.includes(reason))')
      .replace('      if (NEVER_WAIVABLE.includes(r)) {', '      if (false) {')
      .replace('export const WAIVABLE_HOLD_REASONS = [',
               'export const WAIVABLE_HOLD_REASONS = [\n  "no-permission",'
               + '\n  "permission-declined",'
               + '\n  "permission-conditional-unresolved",'
               + '\n  "permission-state-missing",') },

  { id: 'C-FX17', expect: ['FX17'],
    why: 'the waiver loop alone stops re-checking NEVER_WAIVABLE',
    gate: swap('if (accepted.includes(reason) && !NEVER_WAIVABLE.includes(reason))',
               'if (accepted.includes(reason))') },

  /* ── fail-closed on a malformed decision ──────────────────────────── */
  { id: 'C-FX12', expect: ['FX12'],
    why: 'a malformed exception is honoured anyway',
    gate: swap('const exUsable = ex && founderExceptionProblems(record).length === 0;',
               'const exUsable = !!ex;') },

  { id: 'C-FX12b', expect: ['FX12'],
    why: 'the exception stops having to say the supplier did not confirm',
    gate: swap('  if (ex.supplier_confirmation_received !== false) {',
               '  if (false) {') },

  /* ── an exception must waive only what it names ───────────────────── */
  { id: 'C-FX13', expect: ['FX13'],
    why: 'a well-formed exception waives every condition, not the named ones',
    gate: swap('const accepted = exUsable ? ex.waives.slice() : [];',
               'const accepted = exUsable ? WAIVABLE_HOLD_REASONS.slice() : [];') },

  /* RE-AIMED at the validator. Every real condition is in one of the two
     lists, so the derivation can never be shown an unrecognised reason that
     is also the live hold; the first version of this case was therefore
     VACUOUS against the derivation and is now checked where it bites. */
  { id: 'C-FX16', expect: ['FX16'],
    why: 'the validator stops rejecting an unrecognised hold reason',
    gate: swap('      } else if (!WAIVABLE_HOLD_REASONS.includes(r)) {',
               '      } else if (false) {') },

  /* ── equivalence for everyone else ────────────────────────────────── */
  /* RE-AIMED. The first version swapped DECLINED and NONE, which are mutually
     exclusive -- a semantic no-op, so the suite rightly passed and the proof
     called it VACUOUS. Moving the ASSETS condition above the REVIEW condition
     is a real reordering: a record that is both AWAITING_CONFIRMATION and
     REFERENCE_ONLY then reports the wrong reason. */
  { id: 'C-FX15', expect: ['FX15'],
    why: 'the assets condition is moved above the review condition',
    gate: src => {
      const review = '    [rev === "AWAITING_CONFIRMATION", "listing-review-awaiting-confirmation"],';
      const assets = '    [!!assets && assets !== "APPROVED", "assets-not-approved"]';
      if (!src.includes(review) || !src.includes(assets)) return src;
      return src.replace(assets, '')
                .replace(review,
                  '    [!!assets && assets !== "APPROVED", "assets-not-approved"],\n'
                  + review); } },

  { id: 'C-FX15b', expect: ['FX15'],
    why: 'the assets condition is quietly dropped for everyone',
    gate: swap('    [!!assets && assets !== "APPROVED", "assets-not-approved"]',
               '    [false, "assets-not-approved"]') },

  /* ── the integrity check against a fabricated confirmation ────────── */
  /* TWO BRANCHES, TWO CASES. The first version forged a record tripping both,
     so removing either left the suite passing on the other -- VACUOUS. FX9
     and FX9b now isolate them, and so do these. */
  { id: 'C-FX9', expect: ['FX9'],
    why: 'the refusal of a forged CONFIRMED review state is removed',
    gate: swap('    if (ex.supplier_confirmation_received === false &&\n        review.state === "CONFIRMED") {',
               '    if (false) {') },

  { id: 'C-FX9b', expect: ['FX9b'],
    why: 'the refusal of an invented confirmed_at is removed',
    gate: swap('    if (ex.supplier_confirmation_received === false && review.confirmed_at) {',
               '    if (false) {') },

  /* ── the record itself ────────────────────────────────────────────── */
  { id: 'C-FX7', expect: ['FX7'],
    why: 'the listing review is "completed" to CONFIRMED',
    record: list => { bb(list).listing_review.state = 'CONFIRMED'; } },

  { id: 'C-FX7b', expect: ['FX7'],
    why: 'a confirmed_at timestamp is invented',
    record: list => {
      bb(list).listing_review.confirmed_at = '2026-10-12T09:00:00Z'; } },

  { id: 'C-FX8', expect: ['FX8'],
    why: 'the exception claims the supplier DID confirm',
    record: list => {
      bb(list).founder_exception.supplier_confirmation_received = true; } },

  { id: 'C-FX2', expect: ['FX2'],
    why: 'the supplier’s pre-live-review sentence is dropped from the evidence',
    record: list => {
      const r = bb(list);
      r.evidence = r.evidence.replace(
        'Please send us the listing before it goes live, so we can check it.',
        ''); } },

  { id: 'C-FX3', expect: ['FX3'],
    why: 'the credit condition is removed',
    record: list => {
      const r = bb(list);
      r.conditions = r.conditions.filter(c => !/credit/i.test(c)); } },

  { id: 'C-FX6', expect: ['FX6'],
    why: 'the written record stops carrying what was waived',
    record: list => { delete bb(list).waived_conditions; } },

  { id: 'C-FX14', expect: ['FX14'],
    why: 'a second supplier quietly gains the same exception',
    record: list => {
      const other = list.find(r => r.organisation_code
                                   && r.organisation_code !== 'ORG-000153');
      other.permission = { state: 'GRANTED', date: '2026-01-01' };
      other.listing_review = { state: 'AWAITING_CONFIRMATION',
                               confirmed_at: null };
      other.founder_exception = {
        authorised_by: 'Colin MacAulay', decision_date: '2026-10-11',
        waives: ['listing-review-awaiting-confirmation'],
        supplier_confirmation_received: false,
        basis: 'Copied from the BIOBUILDS decision without its own decision.'
      }; } },

  { id: 'C-FX4', expect: ['FX4', 'FX5'],
    why: 'the exception loses the name of the person who authorised it',
    record: list => { delete bb(list).founder_exception.authorised_by; } },

  { id: 'C-FX1', expect: ['FX1'],
    why: 'the original grant date is altered',
    record: list => { bb(list).permission.date = '2026-10-11'; } }
];

for (const c of CASES) {
  const t = tree(c.gate || null, c.record || null);
  if (t.error) {
    log(`  BLIND         ${c.id}  ${c.why}`);
    log(`                ${t.error} — the mutation target has moved`);
    broken++;
    continue;
  }
  const r = run(t.root);
  if (/INSTRUMENT UNAVAILABLE/.test(r.out) || r.code === 2) {
    log(`  BLIND         ${c.id}  ${c.why}`);
    log('                the suite refused: '
        + r.out.split('\n').filter(Boolean).slice(-2).join(' / ').slice(0, 140));
    broken++;
    continue;
  }
  if (r.code === 0) {
    log(`  VACUOUS       ${c.id}  ${c.why}`);
    log('                the suite PASSED against this defect. The guard '
        + 'cannot see it.');
    broken++;
    continue;
  }
  const ids = failedIds(r.out);
  const hit = c.expect.filter(w => ids.includes(w));
  if (!hit.length) {
    log(`  MISATTRIBUTED ${c.id}  ${c.why}`);
    log(`                expected ${c.expect.join('/')} to fail; what failed `
        + `was ${ids.join(',') || '(nothing named)'}`);
    broken++;
  } else {
    log(`  PROVED        ${c.id}  ${c.why}`);
    log(`                ${hit.join(', ')} failed, as required`);
    proved++;
  }
}

console.log('-'.repeat(74));
console.log(`${CASES.length} mutations, ${proved} proved capable, `
            + `${broken} not proved\n`);
process.exit(broken ? 1 : 0);
