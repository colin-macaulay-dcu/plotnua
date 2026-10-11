#!/usr/bin/env node
/**
 * PROVE PUBLICATION-GATE GUARD CAPABILITY
 * =======================================
 * Every guard in prove-supplier-publication-gate.mjs demonstrated capable of failing.
 * One deliberate mutation per guard, each in its own disposable copy of the
 * tree, control run first.
 *
 * A guard that passes against its own mutation is a FAILURE of this proof, as
 * are BLIND (nothing caught), VACUOUS (the owner went unreachable) and
 * MISATTRIBUTED (caught only by some other guard).
 *
 *   node atlas-tools/prove-supplier-publication-gate-capability.mjs
 */
import { readFileSync, writeFileSync, mkdtempSync, copyFileSync, rmSync, mkdirSync }
  from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const GUARD = join(HERE, 'prove-supplier-publication-gate.mjs');

/* Every disposable tree gets a COMPLETE copy, including the generator and
   its two imports. PG11 drives the real generator, so a tree missing it
   makes PG11 fail for the wrong reason and show up as collateral on
   unrelated mutations. Copying everything every time costs nothing and
   keeps each case's result about the thing it mutated. */
const FILES = ['image-rights-records.json', 'additional-home-universe-v1.json',
               'garden-room-recommendation-universe-v1.json', 'your-plot.html',
               '.github/scripts/generate_additional_home_universe.py',
               '.github/scripts/additional_home_qualification.py',
               '.github/scripts/atlas_common.py'];

const ORG = 'ORG-000153';

/* Each case mutates one disposable tree. `fn` receives a tiny helper API. */
const CASES = [
  /* RE-AIMED 11 October 2026, when the founder authorised publication. This
     case used to hand-set PUBLISHABLE, which the derivation now produces by
     itself -- so the mutation became a no-op and the proof reported it BLIND.
     The defect PG1 owns is a hand-set value CONTRADICTING the derivation, and
     the contradiction now runs the other way. */
  ['C-PG1', 'PG1', 'a hand-set public_visibility contradicts the derivation',
    t => t.record(r => { r.public_visibility = 'HOLD';
                         r.hold_reason = 'listing-review-awaiting-confirmation'; })],

  /* RE-AIMED 11 October 2026. This case used to flip class3a to CANDIDATE.
     Under the corrected architecture that is no longer a defect -- a held
     supplier's product MAY be a Class 3A candidate on its technical merits,
     and saying so is the point. The defect worth catching is the product
     being marked PUBLISHABLE while its supplier is held. */
  /* RE-AIMED AGAIN, 11 October 2026. The founder's decision made BIOBUILDS
     genuinely publishable, so marking its product PUBLISHABLE stopped being a
     contradiction and the proof reported this BLIND. The defect still worth
     catching is a product published while its SUPPLIER'S OWN RECORD holds it,
     so the mutation now removes the founder decision and leaves the product
     published -- which is precisely the state a half-finished revert leaves
     behind. */
  ['C-PG2', 'PG2', 'a product stays published after the founder decision is removed',
    t => { t.record(r => { delete r.founder_exception; });
           t.universe(d => {
      d.publicationGate = { version: 'supplier-publication-gate-v1',
                            heldOrganisations: ['BIOBUILDS'] };
      const p = d.products.find(x => /BIOBUILDS/i.test(x.organisation || ''));
      p.area = { number: 35.54, unit: 'm²', measurementBasis: 'VERIFIED_INTERNAL' };
      p.class3a = { state: 'CANDIDATE', reason: null, caveats: [] };
      p.publicVisibility = 'PUBLISHABLE';
           }); }],

  ['C-PG2b', 'PG2b', 'the hold is written back into the Class 3A finding',
    t => t.universe(d => {
      const p = d.products.find(x => /BIOBUILDS/i.test(x.organisation || ''));
      p.class3a = { state: 'NOT_A_CANDIDATE', reason: 'publication-hold',
                    caveats: ['publication-hold'] };
    })],

  ['C-PG13', 'PG13', 'the fail-closed branch is softened to fail open',
    t => t.plot(s => s.replace(
      "gateEnforced ? p.publicVisibility !== 'PUBLISHABLE'",
      "false ? p.publicVisibility !== 'PUBLISHABLE'"))],

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

  /* RE-AIMED 11 October 2026. The injected branch used to return PUBLISHABLE,
     which is what BIOBUILDS now derives anyway, so varying the area changed
     nothing and the proof reported this BLIND. It now returns HOLD for an
     in-band area, so a measurement genuinely moves the visibility -- which is
     the one thing PG6 exists to forbid. */
  ['C-PG6', 'PG6', 'the derivation is made to read area',
    t => t.gateModule(s => s.replace(
      'const assets = record && record.asset_approval_state;',
      'const assets = record && record.asset_approval_state;\n' +
      '  if (record && record.area && record.area.number >= 32 && ' +
      'record.area.number <= 45) return { visibility: "HOLD", '
      + 'holdReason: "area-in-band", waived: [] };'))],

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

  /* RE-AIMED 11 October 2026. The generator's elif chain became a conditions
     list when it learned about founder exceptions, so this mutation stopped
     matching anything and the proof correctly reported it BLIND. Pointed at
     the new line: with the review condition dead, the generator stops holding
     a supplier whose review is outstanding, which PG11's
     "held again without a decision" arm is there to catch. */
  ['C-PG11', 'PG11', 'the generator gate is made to ignore the review state',
    t => t.generator(src => src.replace(
      '(rev == "AWAITING_CONFIRMATION",\n             "listing-review-awaiting-confirmation"),',
      '(False, "listing-review-awaiting-confirmation"),'))],

  ['C-PG12', 'PG12', 'the runtime visibility check is deleted entirely',
    t => t.plot(s => s.replace(
      /      if \(gateEnforced \? p\.publicVisibility !== 'PUBLISHABLE'\n[\s\S]*?\n      \}\n/,
      ''))],

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
/* The suffixed ids matter. (PG\d+) captured "PG2" out of "PG2b", so a real
   PG2b failure was reported as PG2 catching it and PG2b going blind. The
   guard was fine; the harness was reading its own output wrongly. */
const failedIds = o => [...o.matchAll(/^ {2}FAIL {2}(PG\d+[a-z]?)/gm)].map(m => m[1]);

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
  for (const f of FILES) {
    // FILES now includes a nested path, so the parent has to exist first.
    mkdirSync(dirname(join(dir, f)), { recursive: true });
    copyFileSync(join(ROOT, f), join(dir, f));
  }
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
    generator(fn) {
      // The tree already holds a full copy; mutate it in place.
      const gp = join(dir, '.github', 'scripts',
                      'generate_additional_home_universe.py');
      writeFileSync(gp, fn(readFileSync(gp, 'utf8')));
    },
    gateModule(fn) {
      const gp = join(dir, 'publication-gate.mjs');
      writeFileSync(gp, fn(readFileSync(gp, 'utf8')));
      // Run a copy of the guard FROM the disposable dir so its relative
      // import picks up the mutated module.
      const g = join(dir, 'prove-supplier-publication-gate.mjs');
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
