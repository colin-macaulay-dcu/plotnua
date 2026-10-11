#!/usr/bin/env node
/**
 * PROVE PUBLICATION-GATE GUARD CAPABILITY
 * =======================================
 * Every guard in prove-publication-gate.mjs demonstrated capable of failing.
 * One deliberate mutation per guard, each in its own disposable copy of the
 * tree, control run first.
 *
 * A guard that passes against its own mutation is a FAILURE of this proof, as
 * are BLIND (nothing caught), VACUOUS (the owner went unreachable) and
 * MISATTRIBUTED (caught only by some other guard).
 *
 *   node atlas-tools/prove-publication-gate-capability.mjs
 */
import { readFileSync, writeFileSync, mkdtempSync, copyFileSync, rmSync }
  from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const GUARD = join(HERE, 'prove-publication-gate.mjs');

const FILES = ['image-rights-records.json', 'additional-home-universe-v1.json',
               'garden-room-recommendation-universe-v1.json', 'your-plot.html'];

const ORG = 'ORG-000153';

/* Each case mutates one disposable tree. `fn` receives a tiny helper API. */
const CASES = [
  ['C-PG1', 'PG1', 'a hand-set public_visibility contradicts the derivation',
    t => t.record(r => { r.public_visibility = 'PUBLISHABLE'; })],

  ['C-PG2', 'PG2', 'the held supplier gains a CANDIDATE product in the pool',
    t => t.universe(d => {
      const p = d.products.find(x => /BIOBUILDS/i.test(x.organisation || ''));
      p.area = { number: 35.54, unit: 'm²', measurementBasis: 'VERIFIED_INTERNAL' };
      p.class3a = { state: 'CANDIDATE', reason: null, caveats: [] };
    })],

  ['C-PG3', 'PG3', 'the review state is quietly flipped to CONFIRMED',
    t => t.record(r => {
      r.listing_review.state = 'CONFIRMED';
      r.public_visibility = 'HOLD';          // left stale on purpose
      r.hold_reason = 'listing-review-awaiting-confirmation';
    })],

  ['C-PG4', 'PG4', 'a pre-live-review grant is marked NOT_REQUIRED',
    t => t.record(r => {
      r.listing_review.state = 'NOT_REQUIRED';
      r.public_visibility = 'HOLD';
      r.hold_reason = 'assets-not-approved';
    })],

  ['C-PG5', 'PG5', 'a GRANTED supplier is labelled no-permission',
    t => t.record(r => { r.hold_reason = 'no-permission'; })],

  ['C-PG6', 'PG6', 'the derivation is made to read area',
    t => t.gateModule(s => s.replace(
      'const assets = record && record.asset_approval_state;',
      'const assets = record && record.asset_approval_state;\n' +
      '  if (record && record.area && record.area.number >= 32 && ' +
      'record.area.number <= 45) return { visibility: "PUBLISHABLE", holdReason: null };'))],

  ['C-PG7', 'PG7', 'one priced product gains a basis and the rest do not',
    t => t.universe(d => {
      const p = d.products.find(x => (x.price || {}).amount != null);
      p.price.basis = 'INCLUDES_VAT';
    })],

  ['C-PG8', 'PG8', 'a model-name number is recorded as the area',
    t => t.universe(d => {
      const p = d.products.find(x => /BIOBUILDS Wanderlust/i.test(x.productName || ''));
      p.area = { number: 48, unit: 'm²', measurementBasis: 'VERIFIED_INTERNAL',
                 modelNameNumber: 48, modelNameNumberIsNotArea: true };
    })],

  ['C-PG9', 'PG9', 'a garden room is given the Additional Home category',
    t => t.garden(d => {
      const rows = d.products || Object.values(d).find(v => Array.isArray(v));
      rows[0].productCategory = 'Additional Home';
    })],

  ['C-PG10', 'PG10', 'the scalar is printed beside turnkey language',
    t => t.plot(s => s.replace('<body',
      '<script>/* var label = price.amount + " turnkey"; */</script><body'))],
];

function run(root) {
  try {
    return { code: 0, out: execFileSync('node', [GUARD, '--root', root],
                                        { encoding: 'utf8' }) };
  } catch (e) {
    return { code: e.status ?? 1, out: (e.stdout || '') + (e.stderr || '') };
  }
}
const failedIds = o => [...o.matchAll(/^ {2}FAIL {2}(PG\d+)/gm)].map(m => m[1]);

console.log('\nGUARD-CAPABILITY PROOF · PUBLICATION GATE\n');

const before = createHash('sha256')
  .update(FILES.map(f => readFileSync(join(ROOT, f))).join('')).digest('hex');

const control = run(ROOT);
if (control.code !== 0) {
  console.log('CONTROL FAILED — the unmutated tree does not pass. Nothing below is meaningful.');
  console.log(control.out);
  process.exit(1);
}
console.log(`  CONTROL  unmutated tree: ${(control.out.match(/(\d+) passed/) || [])[1]} passed, 0 failed\n`);

let good = 0, bad = 0;
for (const [id, owner, desc, mutate] of CASES) {
  const dir = mkdtempSync(join(tmpdir(), 'pgcap-'));
  for (const f of FILES) copyFileSync(join(ROOT, f), join(dir, f));
  // The gate module is imported by the guard, so a case that mutates it needs
  // its own copy beside a copy of the guard.
  copyFileSync(join(HERE, 'publication-gate.mjs'), join(dir, 'publication-gate.mjs'));

  let guardPath = GUARD;
  const t = {
    record(fn) {
      const p = join(dir, 'image-rights-records.json');
      const d = JSON.parse(readFileSync(p, 'utf8'));
      const rows = Array.isArray(d) ? d
        : Object.values(d).find(v => Array.isArray(v) && v[0] && typeof v[0] === 'object');
      fn(rows.find(r => r.organisation_code === ORG));
      writeFileSync(p, JSON.stringify(d, null, 2));
    },
    universe(fn) {
      const p = join(dir, 'additional-home-universe-v1.json');
      const d = JSON.parse(readFileSync(p, 'utf8')); fn(d);
      writeFileSync(p, JSON.stringify(d, null, 2));
    },
    garden(fn) {
      const p = join(dir, 'garden-room-recommendation-universe-v1.json');
      const d = JSON.parse(readFileSync(p, 'utf8')); fn(d);
      writeFileSync(p, JSON.stringify(d, null, 2));
    },
    plot(fn) {
      const p = join(dir, 'your-plot.html');
      writeFileSync(p, fn(readFileSync(p, 'utf8')));
    },
    gateModule(fn) {
      const gp = join(dir, 'publication-gate.mjs');
      writeFileSync(gp, fn(readFileSync(gp, 'utf8')));
      // Run a copy of the guard FROM the disposable dir so its relative
      // import picks up the mutated module.
      const g = join(dir, 'prove-publication-gate.mjs');
      writeFileSync(g, readFileSync(GUARD, 'utf8'));
      guardPath = g;
    },
  };

  mutate(t);

  let r;
  try {
    r = guardPath === GUARD ? run(dir) : (() => {
      try {
        return { code: 0, out: execFileSync('node', [guardPath, '--root', dir],
                                            { encoding: 'utf8' }) };
      } catch (e) { return { code: e.status ?? 1, out: (e.stdout || '') + (e.stderr || '') }; }
    })();
  } finally { /* keep going */ }

  const fails = failedIds(r.out);
  const collateral = fails.filter(f => f !== owner);
  const ownerLine = new RegExp(`^ {2}(PASS|FAIL) {2}${owner}\\b`, 'm').test(r.out);

  if (!ownerLine) {
    console.log(`  VACUOUS ${id}  ${owner} never ran  — ${desc}`); bad++;
  } else if (!fails.length) {
    console.log(`  BLIND   ${id}  NOT CAUGHT (owner ${owner}) — ${desc}`); bad++;
  } else if (!fails.includes(owner)) {
    console.log(`  MISATTR ${id}  ${owner} passed; caught by ${fails.join(',')} — ${desc}`); bad++;
  } else {
    console.log(`  CAUGHT  ${id}  by ${owner}${collateral.length ? '  (also ' + collateral.join(',') + ')' : ''} — ${desc}`);
    good++;
  }
  rmSync(dir, { recursive: true, force: true });
}

const after = createHash('sha256')
  .update(FILES.map(f => readFileSync(join(ROOT, f))).join('')).digest('hex');

console.log(`\n${CASES.length} mutations: ${good} caught by the guard that owns them, ${bad} not.`);
console.log(`the real tree was untouched by this proof: ${before === after ? 'YES' : 'NO'}  (${after.slice(0, 12)})\n`);
process.exit(bad || before !== after ? 1 : 0);
