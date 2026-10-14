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
         founderExceptionProblems, deriveOrganisationVisibility,
         NEVER_WAIVABLE, NO_RECORD_HOLD,
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
const LEGACY = join(BASE, 'atlas-tools', 'publication-gate-legacy-baseline.json');
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

console.log('\nPUBLICATION GATE · PG1–PG15');
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

/* ── PG2 · a held supplier is never PUBLISHABLE in the artefact ───────── */
{
  /* CORRECTED 11 October 2026. PG2 used to assert that a held supplier had
     no CANDIDATE product. That baked in the wrong architecture: it was only
     true because the generator was overwriting class_3a, i.e. telling a lie
     about the building in order to hide it. Class 3A is a TECHNICAL finding
     about the structure and must stay true whatever the commercial state.

     What must actually hold is this: a held supplier's products may be
     Class 3A candidates on their merits, and must still never be marked
     publishable. */
  const d = JSON.parse(readFileSync(UNIVERSE, 'utf8'));
  const gated = (d.publicationGate && d.publicationGate.heldOrganisations) || [];
  const problems = [];
  for (const r of rows.filter(x => derivePublicVisibility(x).visibility === 'HOLD')) {
    const name = String(r.organisation_name || '').toUpperCase();
    const mine = (d.products || []).filter(p =>
      String(p.organisation || '').toUpperCase() === name);
    const leaked = mine.filter(p => p.publicVisibility === 'PUBLISHABLE');
    if (leaked.length) {
      problems.push(`${name}: ${leaked.length} product(s) marked PUBLISHABLE while on HOLD`);
    }
    if (d.publicationGate && mine.length && !gated.includes(r.organisation_name)) {
      problems.push(`${name} is on HOLD but absent from publicationGate.heldOrganisations`);
    }
  }
  problems.length
    ? bad('PG2 a supplier on HOLD is never marked PUBLISHABLE', problems.join(' | '))
    : ok('PG2 a supplier on HOLD is never marked PUBLISHABLE',
         d.publicationGate ? 'gate-aware artefact' : 'pre-gate artefact, nothing marked either way');
}

/* ── PG2b · the hold NEVER rewrites the technical assessment ──────────── */
{
  /* The founder's correction, asserted directly: a publication hold must not
     show up as a Class 3A reason. If it ever does again, the commercial
     state has leaked back into the evidence. */
  const d = JSON.parse(readFileSync(UNIVERSE, 'utf8'));
  const leaked = (d.products || []).filter(p =>
    ((p.class3a || {}).reason === 'publication-hold') ||
    (((p.class3a || {}).caveats) || []).includes('publication-hold'));
  const src = readFileSync(join(BASE, '.github', 'scripts',
                                'generate_additional_home_universe.py'), 'utf8');
  const overwrites = /c3\s*=\s*\{[^}]*publication-hold/.test(src);
  (!leaked.length && !overwrites)
    ? ok('PG2b a publication hold never appears as a Class 3A finding')
    : bad('PG2b a publication hold never appears as a Class 3A finding',
          `products=${leaked.length} generatorOverwrites=${overwrites}`);
}

/* ── PG3 · GRANTED + AWAITING_CONFIRMATION ⇒ HOLD, and CONFIRMED is earned ─ */
{
  // scope: a FEATURING grant, so the review is what holds it (since 14 Oct
  // 2026 a grant without "feature" in scope holds earlier, on its scope).
  const probe = { permission: { state: 'GRANTED', scope: ['feature'] },
                  listing_review: { state: 'AWAITING_CONFIRMATION' } };
  const d = derivePublicVisibility(probe);
  const real = gated.filter(r => (r.permission || {}).state === 'GRANTED' &&
                                 (r.listing_review || {}).state === 'AWAITING_CONFIRMATION');
  /* AMENDED 11 October 2026, when the founder authorised publishing
     BIOBUILDS before its review came back.

     PG3's point is that an OUTSTANDING REVIEW HOLDS A SUPPLIER. That is
     unchanged, and the synthetic probe above -- which carries no exception --
     still has to derive HOLD, which is the core of this guard.

     What is now allowed is the one thing that was always meant to be
     possible: a named founder decision, recorded on that supplier's own
     record, that explicitly accepts this exact condition. The exclusion is
     deliberately narrow -- the exception must be WELL-FORMED and must name
     listing-review-awaiting-confirmation by hand. A record that is simply
     publishable with an outstanding review and no such decision still fails
     here, and prove-founder-exception.mjs (FX14) separately asserts that no
     other supplier has acquired one. */
  const excepted = r => {
    const ex = r.founder_exception;
    return !!ex && founderExceptionProblems(r).length === 0 &&
           (ex.waives || []).includes('listing-review-awaiting-confirmation');
  };
  const unexplained = real.filter(r =>
    derivePublicVisibility(r).visibility !== 'HOLD' && !excepted(r));
  const allHeld = !unexplained.length;

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
    ? ok('PG3 AWAITING derives to HOLD unless a founder decision says '
         + 'otherwise, and CONFIRMED requires a date',
         `${real.length} awaiting (${real.filter(excepted).length} by founder `
         + `decision), ${gated.filter(r => (r.listing_review || {}).state === 'CONFIRMED').length} confirmed`)
    : bad('PG3 AWAITING derives to HOLD, and CONFIRMED requires a date',
          unearned.length
            ? `CONFIRMED with no confirmed_at: ${unearned.join(',')}`
            : unexplained.length
              ? `publishable with an outstanding review and no founder `
                + `decision: ${unexplained.map(r => r.organisation_code).join(',')}`
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
  // THE MIGRATION BRANCH IS GONE, RETIRED 11 October 2026.
  //
  // This guard used to PASS when EVERY priced product lacked `basis`, on the
  // grounds that the universe had not been regenerated yet and a uniform
  // absence was the honest pre-migration state. That was true while it was
  // true. The founder regenerated on 11 October and all 125 priced products
  // now carry a basis, so the branch became unreachable in normal operation
  // and dangerous in abnormal operation: a generator regression that stripped
  // the field from every priced product would have been reported as "ok, not
  // yet regenerated" — the guard excusing precisely what it exists to forbid.
  //
  // Uniform absence now fails like any other absence. With no special case
  // left, one missing basis and all missing bases are the same code path,
  // which is why C-PG7 can prove both by removing one.
  if (!priced.length) {
    bad('PG7 VAT basis present wherever an amount exists', 'no priced product found — vacuous');
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
print(repr(m.publication_hold("Shomera")) + " " + repr(m.publication_hold("Kodasema")))
print(repr(m.GATE_NEVER_WAIVABLE))
import json, copy, pathlib as P
rec = json.loads((root / "image-rights-records.json").read_text())
rows = rec["records"] if isinstance(rec, dict) else rec
d = copy.deepcopy(rec)
tgt = [r for r in (d["records"] if isinstance(d, dict) else d)
       if r.get("organisation_code") == "ORG-000153"][0]
tgt.pop("founder_exception", None)
P.Path("/tmp/pg11-no-exception.json").write_text(json.dumps(d))
m.RIGHTS = P.Path("/tmp/pg11-no-exception.json"); m._GATE = None
print(repr(m.publication_hold("BIOBUILDS")))
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
  /* RE-AIMED 11 October 2026, with the founder's decision to publish.
     PG11 used to assert that the generator HOLDS BIOBUILDS. That was the
     correct intent until the decision was taken, and it is now the wrong
     one -- so this is re-aimed rather than relaxed, and it now asserts four
     things instead of two.

     IT EXISTS BECAUSE OF A REAL NEAR-MISS. The exception was built, the
     record written, the JS derivation agreed, eighteen assertions passed and
     twenty mutations proved capable -- and the GENERATOR'S own copy of the
     rule still returned 'listing-review-awaiting-confirmation'. Regenerating
     would have stamped HOLD onto both products and the authorised
     publication would silently not have happened, with every guard green,
     because every guard was pointed at the other two mirrors. This now
     checks the third one, both ways round. */
  const lines = out.split('\n');
  const freedByDecision = (lines[0] || '').trim() === 'None';
  /* RE-AIMED 14 October 2026 (fail-closed correction). This line used to
     assert that an organisation with NO rights record is free -- the
     fail-open, written down as a requirement. It now asserts the opposite:
     an unrecorded organisation holds, and only a name in the legacy
     baseline (already public before the correction) is preserved. */
  const ungatedFree = (lines[1] || '').trim() === `'${NO_RECORD_HOLD}' None`;
  const forbidden = (lines[2] || '');
  const mirrorsAgree = NEVER_WAIVABLE.every(r => forbidden.includes(r));
  // And WITHOUT the decision the same generator must hold it again, which is
  // what proves the exception is doing the work rather than the gate having
  // been loosened.
  const heldWithoutIt =
    (lines[3] || '').includes('listing-review-awaiting-confirmation');
  (freedByDecision && ungatedFree && mirrorsAgree && heldWithoutIt)
    ? ok('PG11 the generator frees BIOBUILDS on the founder decision, holds '
         + 'it again without one, and shares the unwaivable list',
         `biobuilds=${lines[0]} ungated=${lines[1]} without=${(lines[3] || '').slice(0, 42)}`)
    : bad('PG11 the generator agrees with the decision and with the JS gate',
          `freed=${freedByDecision} ungated=${ungatedFree} `
          + `mirrors=${mirrorsAgree} heldWithout=${heldWithoutIt} :: `
          + out.slice(0, 200));
  }
}

/* ── PG12 · the RUNTIME reader refuses a held product ─────────────────── */
{
  /* The second lock. Proves your-plot.html drops a product carrying
     publicVisibility HOLD even when every other signal says publish --
     including class3a CANDIDATE, which is exactly the state an area
     correction would produce. */
  const html = readFileSync(PLOT, 'utf8');
  const hasCheck = /gateEnforced \? p\.publicVisibility !== 'PUBLISHABLE'/.test(html)
    && /: p\.publicVisibility === 'HOLD'/.test(html);
  const beforeCandidate =
    html.indexOf("gateEnforced ? p.publicVisibility !== 'PUBLISHABLE'") <
    html.indexOf("if (c3 === 'CANDIDATE') { funnel.class3aCandidates++; out.push(p); }");
  (hasCheck && beforeCandidate)
    ? ok('PG12 the runtime reader drops a HOLD product before the candidate push')
    : bad('PG12 the runtime reader drops a HOLD product before the candidate push',
          `check=${hasCheck} ordered=${beforeCandidate}`);
}

/* ── PG13 · the reader fails CLOSED on a gate-aware artefact ──────────── */
{
  /* The dangerous case is not HOLD, which is loud. It is a product whose
     publicVisibility has gone missing -- a truncated file, a hand edit, a
     half-finished merge. On an artefact that declares the gate, anything
     that is not exactly PUBLISHABLE must be withheld. */
  const html = readFileSync(PLOT, 'utf8');
  const declares = /publicationGate: data\.publicationGate \|\| null/.test(html);
  const failsClosed = /gateEnforced \? p\.publicVisibility !== 'PUBLISHABLE'/.test(html);
  const derivesFlag = /var gateEnforced = !!\(meta && meta\.publicationGate\);/.test(html);
  (declares && failsClosed && derivesFlag)
    ? ok('PG13 a missing publicVisibility is withheld, not shown, once the gate is declared')
    : bad('PG13 a missing publicVisibility is withheld, not shown',
          `meta=${declares} failsClosed=${failsClosed} flag=${derivesFlag}`);
}

/* ── PG14 · FAIL-CLOSED REGRESSION · missing evidence never publishes ───── */
{
  /* 14 October 2026. The record derivation was always fail-closed; the hole
     was in how a generator found the record. Each case below is a way
     ABSENT or INCOMPLETE evidence used to come out PUBLISHABLE, run through
     BOTH the JS gate and the generator's own copy, which must agree. */
  const legacy = JSON.parse(readFileSync(LEGACY, 'utf8')).organisations.map(o => o.organisation);
  const G = (scope, rev, extra) => Object.assign({ organisation_name: 'PROBE',
    permission: { state: 'GRANTED', scope }, listing_review: { state: rev } }, extra || {});
  const FX = { authorised_by: 'Probe', decision_date: '2026-10-14',
    supplier_confirmation_received: false, basis: 'a probe decision, long enough to pass',
    waives: ['permission-scope-excludes-listing'] };
  const cases = [
    // [label, records, name, expected holdReason (null = PUBLISHABLE)]
    ['a record with neither state', [{ organisation_name: 'PROBE' }], 'PROBE', 'permission-state-missing'],
    ['a record with permission but no review state', [{ organisation_name: 'PROBE', permission: { state: 'GRANTED', scope: ['feature'] } }], 'PROBE', 'listing-review-state-missing'],
    ['an unknown permission state', [G(['feature'], 'CONFIRMED', { permission: { state: 'MAYBE', scope: ['feature'] } })], 'PROBE', 'permission-state-missing'],
    ['GRANTED with no scope', [G(undefined, 'CONFIRMED')], 'PROBE', 'permission-scope-excludes-listing'],
    ['GRANTED for preview imagery only, review CONFIRMED', [G(['imagery-preview-only'], 'CONFIRMED')], 'PROBE', 'permission-scope-excludes-listing'],
    ['a founder exception cannot waive the scope', [G(['imagery'], 'CONFIRMED', { founder_exception: FX })], 'PROBE', 'permission-scope-excludes-listing'],
    ['no rights record at all', [], 'NEWCO', NO_RECORD_HOLD],
    ['an empty organisation name', [], '', NO_RECORD_HOLD],
    ['two records answer to one name', [G(['feature'], 'CONFIRMED'), G(['feature'], 'CONFIRMED', { organisation_name: 'Probe' })], 'PROBE', 'permission-state-missing'],
    ['a spacing variant still finds its record', [{ organisation_name: 'Yard Box' }], 'Yardbox', 'permission-state-missing'],
    ['a legacy org that gains a record is governed by the record', [{ organisation_name: legacy[0] }], legacy[0], 'permission-state-missing'],
    ['CONTROL a complete, confirmed, featured grant publishes', [G(['feature'], 'CONFIRMED', { listing_review: { state: 'CONFIRMED', confirmed_at: '2026-10-14' } })], 'PROBE', null],
    ['CONTROL a legacy-baseline org with no record is preserved', [], legacy[0], null],
  ];
  const probe = `
import importlib.util, sys, json, pathlib, tempfile
root = pathlib.Path(${JSON.stringify(BASE)})
sys.path.insert(0, str(root / ".github" / "scripts"))
spec = importlib.util.spec_from_file_location("gen", root / ".github" / "scripts" / "generate_additional_home_universe.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
cases = json.loads(sys.stdin.read())
out = []
for recs, name in cases:
    p = pathlib.Path(tempfile.mkstemp(suffix=".json")[1]); p.write_text(json.dumps({"records": recs}))
    m.RIGHTS = p; m._GATE = None; m._LEGACY = None
    out.append(m.publication_hold(name))
# an unreadable baseline refuses to generate
m.RIGHTS = root / "image-rights-records.json"; m._GATE = None; m._LEGACY = None
m.LEGACY = pathlib.Path("/nonexistent/baseline.json")
try:
    m.publication_hold("Kodasema"); out.append("NO-REFUSAL")
except SystemExit:
    out.append("REFUSED")
print(json.dumps(out))
`;
  let py = null;
  try {
    // stderr is captured: the baseline-refusal case is SUPPOSED to print an error.
    py = JSON.parse(execFileSync('python3', ['-I', '-c', probe], { encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
      input: JSON.stringify(cases.map(c => [c[1], c[2]])) }).trim().split('\n').pop());
  } catch (e) { py = null; }
  const problems = [];
  cases.forEach(([label, recs, name, want], i) => {
    const js = deriveOrganisationVisibility(name, recs, legacy).holdReason;
    if (js !== want) problems.push(`JS ${label}: ${js}`);
    if (!py || py[i] !== want) problems.push(`generator ${label}: ${py ? py[i] : 'unavailable'}`);
  });
  if (!py || py[cases.length] !== 'REFUSED') problems.push('generator ran without its legacy baseline');
  problems.length
    ? bad('PG14 missing, unknown or incomplete evidence never derives PUBLISHABLE', problems.join(' | '))
    : ok('PG14 missing, unknown or incomplete evidence never derives PUBLISHABLE',
         `${cases.length} cases, JS and generator agree; no baseline -> refuses`);
}

/* ── PG15 · the correction changes nothing that is live ───────────────── */
{
  /* Every product public today (PUBLISHABLE and ELIGIBLE in the committed
     artefact) must still derive PUBLISHABLE under the corrected generator,
     every real record must derive the same in JS and in the generator, and
     the legacy baseline may only shrink and may never shadow a record. */
  const d = JSON.parse(readFileSync(UNIVERSE, 'utf8'));
  const legacyDoc = JSON.parse(readFileSync(LEGACY, 'utf8'));
  const legacy = legacyDoc.organisations.map(o => o.organisation);
  const FROZEN = ['All About Outdoors', 'All In One Cabins', 'Concept Modular',
    'Granny Flats Dublin', 'Hansa24 Group', 'Kodasema', 'Koto', 'Modular House', 'MyCabin.ie'];
  const live = [...new Set((d.products || []).filter(p => p.publicVisibility === 'PUBLISHABLE' &&
    ((p.qualification || {}).state === 'ELIGIBLE')).map(p => p.organisation))];
  const names = [...new Set([...live, ...rows.map(r => r.organisation_name)])];
  const probe = `
import importlib.util, sys, json, pathlib
root = pathlib.Path(${JSON.stringify(BASE)})
sys.path.insert(0, str(root / ".github" / "scripts"))
spec = importlib.util.spec_from_file_location("gen", root / ".github" / "scripts" / "generate_additional_home_universe.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(json.dumps({n: m.publication_hold(n) for n in json.loads(sys.stdin.read())}))
`;
  let py = {};
  try { py = JSON.parse(execFileSync('python3', ['-I', '-c', probe], { encoding: 'utf8',
          input: JSON.stringify(names) }).trim().split('\n').pop()); } catch (e) { py = null; }
  const problems = [];
  if (!py) problems.push('generator unavailable');
  for (const o of live) {
    const js = deriveOrganisationVisibility(o, rows, legacy);
    if (js.visibility !== 'PUBLISHABLE') problems.push(`live ${o} now ${js.holdReason} (JS)`);
    if (py && py[o] !== null) problems.push(`live ${o} now ${py[o]} (generator)`);
  }
  for (const r of rows) {
    const js = deriveOrganisationVisibility(r.organisation_name, rows, legacy).holdReason;
    if (py && py[r.organisation_name] !== js) problems.push(`${r.organisation_name}: JS ${js} vs generator ${py[r.organisation_name]}`);
  }
  for (const n of legacy) {
    if (!FROZEN.includes(n)) problems.push(`baseline grew: ${n}`);
    if (deriveOrganisationVisibility(n, rows, []).matched) problems.push(`baseline shadows a record: ${n}`);
  }
  /* RE-AIMED 14 October 2026 (founder decision: PROCEED on OGNYX's own words).
     This used to assert OGNYX was HELD on a preview-only scope. It now asserts
     the publication is EARNED: a featuring grant, a confirmed review with a
     date, exactly four enumerated assets, and no founder exception doing the
     work evidence must do. */
  const og = rows.find(r => r.organisation_name === 'OGNYX');
  const ogd = og && derivePublicVisibility(og);
  const sc = ((og || {}).permission || {}).scope || [];
  if (!og || ogd.visibility !== 'PUBLISHABLE' || og.founder_exception ||
      !sc.includes('feature') || !sc.includes('imagery') ||
      (og.listing_review || {}).state !== 'CONFIRMED' || !(og.listing_review || {}).confirmed_at ||
      (og.approved_assets || []).length !== 4) {
    problems.push('OGNYX is not published on evidence alone: ' + JSON.stringify(ogd));
  }
  problems.length
    ? bad('PG15 nothing live changes, JS and generator agree on every record, OGNYX earned', problems.join(' | '))
    : ok('PG15 nothing live changes, JS and generator agree on every record, OGNYX earned',
         `${live.length} live organisations still publishable (${legacy.length} by legacy baseline), `
         + `${rows.length} records agree`);
}

console.log('\n' + '='.repeat(74));
console.log(`${pass + fail} checks, ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
