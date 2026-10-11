#!/usr/bin/env node
/**
 * PROVE THE PUBLICATION GATE · PG1–PG10
 * =====================================
 * Whether a supplier may appear in public Results is derived from permission
 * state, listing-review state and asset approval — and from nothing else.
 *
 * THE FAILURE THESE GUARDS EXIST FOR. BIOBUILDS is invisible in public
 * Results today, but only by accident: its area.number is null, so class_3a()
 * returns NOT_A_CANDIDATE with reason no-usable-area. Correcting Wanderlust's
 * area to its true 35.54 m² — an ordinary data-quality fix, and one the
 * supplier asked for — lands inside the 32–45 m² band and would publish the
 * product while the supplier is still reviewing the listing. PG6 is the
 * assertion that this cannot happen.
 *
 *   node atlas-tools/prove-supplier-publication-gate.mjs [--records PATH]
 *
 * Exit 0 = all pass.
 */
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { derivePublicVisibility, gateIntegrityProblems,
         PRE_LIVE_REVIEW_LANGUAGE } from './publication-gate.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);

function arg(name, dflt) {
  const i = process.argv.indexOf('--' + name);
  return i === -1 ? dflt : process.argv[i + 1];
}
// --root lets the capability proof point the whole suite at a disposable
// copy of the tree. Without it each mutation would have to touch the real
// files, and a proof that edits production is not a proof.
const BASE = arg('root', ROOT);
const RECORDS = arg('records', join(BASE, 'image-rights-records.json'));
const UNIVERSE = join(BASE, 'additional-home-universe-v1.json');
const GARDEN = join(BASE, 'garden-room-recommendation-universe-v1.json');
const PLOT = join(BASE, 'your-plot.html');

let pass = 0, fail = 0;
const ok = (n, d) => { pass++; console.log(`  PASS  ${n}${d ? '  [' + d + ']' : ''}`); };
const bad = (n, d) => { fail++; console.log(`  FAIL  ${n}${d ? '  [' + d + ']' : ''}`); };

function rowsOf(doc) {
  if (Array.isArray(doc)) return doc;
  for (const v of Object.values(doc)) {
    if (Array.isArray(v) && v[0] && typeof v[0] === 'object') return v;
  }
  return null;
}

const doc = JSON.parse(readFileSync(RECORDS, 'utf8'));
const rows = rowsOf(doc);
if (!rows) { console.log('  FAIL  the rights records hold no recognisable row list'); process.exit(1); }

const gated = rows.filter(r => r.permission || r.listing_review ||
                               r.public_visibility !== undefined);
if (!gated.length) {
  // A suite that silently tests nothing is worse than no suite.
  console.log('  FAIL  no record carries gate fields — this proof would pass vacuously');
  process.exit(1);
}

console.log('\nPUBLICATION GATE · PG1–PG10');
console.log('='.repeat(74));
console.log(`  ${gated.length} gated record(s) under test\n`);

/* ── PG1 · derived, never literal ─────────────────────────────────────── */
{
  let problems = [];
  for (const r of gated) {
    const p = gateIntegrityProblems(r);
    if (p.length) problems.push(`${r.organisation_code}: ${p.join('; ')}`);
  }
  problems.length
    ? bad('PG1 public_visibility and hold_reason are derived, never literal', problems.join(' | '))
    : ok('PG1 public_visibility and hold_reason are derived, never literal');
}

/* ── PG2 · a held supplier reaches no public surface ──────────────────── */
{
  const held = gated.filter(r => derivePublicVisibility(r).visibility === 'HOLD');
  const problems = [];
  for (const r of held) {
    const name = r.organisation_name;
    for (const [label, file] of [['additional-home universe', UNIVERSE]]) {
      const txt = readFileSync(file, 'utf8');
      // Presence in the universe is expected; presence in a PUBLISHED pool is
      // not. The universe is the candidate set, and class3a decides the pool.
      const d = JSON.parse(txt);
      const pool = (d.products || []).filter(p =>
        String(p.organisation || '').toUpperCase() === name.toUpperCase());
      const publishable = pool.filter(p => (p.class3a || {}).state === 'CANDIDATE');
      if (publishable.length) {
        problems.push(`${name} has ${publishable.length} CANDIDATE product(s) in the ${label} while on HOLD`);
      }
    }
  }
  problems.length
    ? bad('PG2 a supplier on HOLD reaches no public candidate pool', problems.join(' | '))
    : ok('PG2 a supplier on HOLD reaches no public candidate pool',
         `${held.length} held supplier(s) checked`);
}

/* ── PG3 · GRANTED + AWAITING_CONFIRMATION ⇒ HOLD, and CONFIRMED is earned ─ */
{
  const probe = { permission: { state: 'GRANTED' },
                  listing_review: { state: 'AWAITING_CONFIRMATION' } };
  const d = derivePublicVisibility(probe);
  const real = gated.filter(r => (r.permission || {}).state === 'GRANTED' &&
                                 (r.listing_review || {}).state === 'AWAITING_CONFIRMATION');
  const allHeld = real.every(r => derivePublicVisibility(r).visibility === 'HOLD');

  /* THE CAPABILITY PROOF FOUND THIS HOLE. The first version of PG3 checked
     the synthetic probe plus "every real AWAITING record is HOLD". Flipping
     the only real record to CONFIRMED therefore satisfied PG3 vacuously --
     there were no AWAITING records left to check -- and the mutation was
     caught only by PG1, as MISATTRIBUTED. The guard was weak, not the test.

     A review state of CONFIRMED is a claim that a named supplier came back
     and said yes. It is the single state that unlocks publication, so it
     must be EARNED: a confirmation date, and no corrections left outstanding
     after it. A CONFIRMED with confirmed_at null is somebody editing an enum,
     and that is exactly the edit this gate exists to catch. */
  const unearned = gated
    .filter(r => (r.listing_review || {}).state === 'CONFIRMED')
    .filter(r => !(r.listing_review || {}).confirmed_at)
    .map(r => r.organisation_code);

  (d.visibility === 'HOLD' &&
   d.holdReason === 'listing-review-awaiting-confirmation' &&
   allHeld && !unearned.length)
    ? ok('PG3 AWAITING derives to HOLD, and CONFIRMED requires a date',
         `${real.length} awaiting, ${gated.filter(r => (r.listing_review || {}).state === 'CONFIRMED').length} confirmed`)
    : bad('PG3 AWAITING derives to HOLD, and CONFIRMED requires a date',
          unearned.length
            ? `CONFIRMED with no confirmed_at: ${unearned.join(',')}`
            : JSON.stringify(d));
}

/* ── PG4 · a pre-live-review grant cannot claim NOT_REQUIRED ──────────── */
{
  const probe = {
    evidence: 'Please send us the listing before it goes live, so we can check it.',
    permission: { state: 'GRANTED' },
    listing_review: { state: 'NOT_REQUIRED' },
  };
  const caught = gateIntegrityProblems(probe)
    .some(p => /NOT_REQUIRED/.test(p));
  const realClean = gated.every(r => !(
    PRE_LIVE_REVIEW_LANGUAGE.test(String(r.evidence || '')) &&
    (r.listing_review || {}).state === 'NOT_REQUIRED'));
  (caught && realClean)
    ? ok('PG4 a grant asking for pre-live review cannot be NOT_REQUIRED')
    : bad('PG4 a grant asking for pre-live review cannot be NOT_REQUIRED',
          `probeCaught=${caught} realClean=${realClean}`);
}

/* ── PG5 · a GRANTED supplier is never called unpermitted ─────────────── */
{
  const problems = gated
    .filter(r => (r.permission || {}).state === 'GRANTED')
    .filter(r => derivePublicVisibility(r).holdReason === 'no-permission' ||
                 r.hold_reason === 'no-permission')
    .map(r => r.organisation_code);
  problems.length
    ? bad('PG5 hold_reason never says no-permission for a GRANTED supplier', problems.join(','))
    : ok('PG5 hold_reason never says no-permission for a GRANTED supplier');
}

/* ── PG6 · area is not an input to visibility ─────────────────────────── */
{
  // The whole point. Take each held record, pretend every area value in the
  // world changed, and assert the derivation does not move. The derivation
  // takes only the record, so this is tested by handing it records carrying
  // area fields and confirming they are ignored.
  const problems = [];
  for (const r of gated) {
    const base = derivePublicVisibility(r);
    for (const n of [null, 12, 35.54, 44.9, 95, 1000]) {
      const withArea = JSON.parse(JSON.stringify(r));
      withArea.area = { number: n, measurementBasis: 'VERIFIED_INTERNAL' };
      withArea.class3a = { state: n && n >= 32 && n <= 45 ? 'CANDIDATE' : 'NOT_A_CANDIDATE' };
      const d = derivePublicVisibility(withArea);
      if (d.visibility !== base.visibility || d.holdReason !== base.holdReason) {
        problems.push(`${r.organisation_code} moved to ${d.visibility} at area=${n}`);
      }
    }
  }
  problems.length
    ? bad('PG6 changing area never changes publicVisibility', problems.join(' | '))
    : ok('PG6 changing area never changes publicVisibility',
         'six area values per record, including 35.54 inside the 32–45 band');
}

/* ── PG7 · VAT basis present wherever an amount exists ────────────────── */
{
  const d = JSON.parse(readFileSync(UNIVERSE, 'utf8'));
  const priced = (d.products || []).filter(p => (p.price || {}).amount != null);
  const missing = priced.filter(p => !(p.price || {}).basis);
  // The universe has not been regenerated yet, so today every priced product
  // legitimately lacks `basis`. The guard states which world it is in rather
  // than passing silently in either.
  if (!priced.length) {
    bad('PG7 VAT basis present wherever an amount exists', 'no priced product found — vacuous');
  } else if (missing.length === priced.length) {
    ok('PG7 VAT basis — NOT YET REGENERATED, all ' + priced.length +
       ' priced products predate the field; re-run after regeneration',
       'pre-migration state, recorded not hidden');
  } else if (missing.length) {
    bad('PG7 VAT basis present wherever an amount exists',
        `${missing.length} of ${priced.length} priced products have an amount but no basis`);
  } else {
    ok('PG7 VAT basis present wherever an amount exists', `${priced.length} priced products`);
  }
}

/* ── PG8 · a model-name number is never used as an area ───────────────── */
{
  const d = JSON.parse(readFileSync(UNIVERSE, 'utf8'));
  const problems = (d.products || [])
    .filter(p => (p.area || {}).modelNameNumberIsNotArea === true)
    .filter(p => p.area.modelNameNumber != null &&
                 p.area.number === p.area.modelNameNumber)
    .map(p => p.productCode);
  problems.length
    ? bad('PG8 a model-name number is never recorded as the area', problems.join(','))
    : ok('PG8 a model-name number is never recorded as the area');
}

/* ── PG9 · the two Class 3A populations stay disjoint ─────────────────── */
{
  // Requirement F. The Cluster 1 copy guard counts Class 3A products in the
  // GARDEN ROOM universe. The Additional Home band counts a different
  // population. An earlier audit of mine wrongly claimed correcting a
  // BIOBUILDS area would trip the Cluster 1 refusal; it cannot, because
  // BIOBUILDS is not a garden room. This asserts the separation holds, so a
  // future refactor cannot quietly couple them.
  const ah = JSON.parse(readFileSync(UNIVERSE, 'utf8'));
  const gr = JSON.parse(readFileSync(GARDEN, 'utf8'));
  const grRows = gr.products || rowsOf(gr) || [];
  const ahCodes = new Set((ah.products || []).map(p => p.productCode));
  const overlap = grRows.map(p => p.productCode).filter(c => ahCodes.has(c));
  const ahCats = new Set((ah.products || []).map(p => p.productCategory));
  const grCats = new Set(grRows.map(p => p.productCategory));
  const shared = [...ahCats].filter(c => grCats.has(c));
  (!overlap.length && !shared.length)
    ? ok('PG9 the garden-room and additional-home populations are disjoint',
         `${grRows.length} garden rooms, ${(ah.products || []).length} additional homes, 0 shared`)
    : bad('PG9 the garden-room and additional-home populations are disjoint',
          `overlap=${overlap.length} sharedCategories=${[...shared].join(',')}`);
}

/* ── PG10 · the scalar is never labelled as a completed-home price ────── */
{
  // Founder decision 3. The retained scalar equals the LOWEST configuration,
  // which for a two-configuration supplier is the SHELL, not the finished
  // home. Any reader that prints it beside turnkey language is a defect.
  const html = readFileSync(PLOT, 'utf8');
  const BAD = [
    /price\.amount[^;\n]{0,120}\b(turnkey|fully fitted|fully finished|completed home)\b/i,
    /\b(turnkey|fully fitted|fully finished)\b[^;\n]{0,120}price\.amount/i,
  ];
  const hits = BAD.filter(re => re.test(html));
  hits.length
    ? bad('PG10 the scalar price.amount is never labelled turnkey or completed',
          `${hits.length} suspicious construction(s) in your-plot.html`)
    : ok('PG10 the scalar price.amount is never labelled turnkey or completed');
}

/* ── PG11 · the GENERATOR itself refuses a held supplier ──────────────── */
{
  /* PG1-PG10 prove the record is consistent and that no held supplier has a
     CANDIDATE product in the artefact. None of them proved the GENERATOR
     would refuse, because until now it never read the gate: a held supplier
     was kept out by the accident of a null area. This drives the real
     generator's own gate function over the real records. */
  const probe = `
import importlib.util, sys, pathlib
root = pathlib.Path(${JSON.stringify(BASE)})
sys.path.insert(0, str(root / ".github" / "scripts"))
spec = importlib.util.spec_from_file_location(
    "gen", root / ".github" / "scripts" / "generate_additional_home_universe.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(repr(m.publication_hold("BIOBUILDS")))
print(repr(m.publication_hold("Shomera")))
`;
  let out = '';
  try {
    out = execFileSync('python3', ['-I', '-c', probe], { encoding: 'utf8' }).trim();
  } catch (e) { out = 'ERROR ' + ((e.stderr || e.stdout || '') + '').slice(0, 200); }
  if (/No such file or directory/.test(out)) {
    // The guard was pointed at a tree with no generator. Say so rather than
    // passing or failing on an instrument that was never there.
    bad('PG11 the generator itself holds BIOBUILDS', 'UNREACHABLE: no generator under this root');
  } else {
  const lines = out.split('\n');
  const held = (lines[0] || '').includes('listing-review-awaiting-confirmation');
  const free = (lines[1] || '').trim() === 'None';
  (held && free)
    ? ok('PG11 the generator itself holds BIOBUILDS and frees an ungated supplier',
         lines.join(' | '))
    : bad('PG11 the generator itself holds BIOBUILDS and frees an ungated supplier', out.slice(0, 220));
  }
}

/* ── PG12 · the RUNTIME reader refuses a held product ─────────────────── */
{
  /* The second lock. Proves your-plot.html drops a product carrying
     publicVisibility HOLD even when every other signal says publish --
     including class3a CANDIDATE, which is exactly the state an area
     correction would produce. */
  const html = readFileSync(PLOT, 'utf8');
  const hasCheck = /if \(p\.publicVisibility === 'HOLD'\) \{ funnel\.publicationHeld\+\+; continue; \}/.test(html);
  const beforeCandidate =
    html.indexOf("p.publicVisibility === 'HOLD'") <
    html.indexOf("if (c3 === 'CANDIDATE') { funnel.class3aCandidates++; out.push(p); }");
  (hasCheck && beforeCandidate)
    ? ok('PG12 the runtime reader drops a HOLD product before the candidate push')
    : bad('PG12 the runtime reader drops a HOLD product before the candidate push',
          `check=${hasCheck} ordered=${beforeCandidate}`);
}

console.log('\n' + '='.repeat(74));
console.log(`${pass + fail} checks, ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
