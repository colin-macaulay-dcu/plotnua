#!/usr/bin/env node
/* PlotNua — verify-biobuilds-publication.mjs
 *
 * THE POST-REGENERATION ACCEPTANCE CHECK for founder authorisation
 * FX-BIOBUILDS-PUBLISH-20261011, final deployment instruction 11 October 2026.
 *
 * WHY IT EXISTS. The founder's instruction 5 lists seven facts that must be
 * true of Wanderlust in the regenerated artefact, and instruction 6 one fact
 * about Serenity. Those are checkable by eye exactly once, by one person, on
 * one afternoon. This makes them checkable by instrument, every time, by
 * anyone — so a regeneration that quietly produces the wrong answer is caught
 * by a failing command rather than by a homeowner.
 *
 * IT READS THE REGENERATED ARTEFACT AND THE RIGHTS RECORD. It generates
 * nothing, writes nothing and contacts no network. It cannot create the
 * condition it checks for.
 *
 * EXIT CODES
 *   0  every check passed
 *   1  a check failed — do not deploy
 *   2  the facts could not be established (file missing, unreadable, or the
 *      artefact predates the gate). Treated as failure, never as a pass.
 *
 * --self-test runs each check against a deliberately broken copy of the
 * artefact IN MEMORY and proves the check fails. A check that cannot fail is
 * not a check. The real files are never written.
 */
import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');

/* --universe / --rights point the checks at a disposable copy, so the
 * capability proof can run against a fixture without the real artefact being
 * read, written or implicated. Absent, both resolve to the real files. */
function argPath(flag, fallback) {
  const i = process.argv.indexOf(flag);
  return (i !== -1 && process.argv[i + 1]) ? process.argv[i + 1] : fallback;
}
const UNIVERSE = argPath('--universe', join(ROOT, 'additional-home-universe-v1.json'));
const RIGHTS = argPath('--rights', join(ROOT, 'image-rights-records.json'));

const WANDERLUST = 'PROD-000523';
const SERENITY = 'PROD-000524';
const DECISION_DATE = '2026-10-11';   // FX-BIOBUILDS-PUBLISH-20261011

/* The founder's figures, written here so a drift in the artefact cannot
 * silently redefine what "correct" means. */
const EXPECTED = {
  [WANDERLUST]: {
    configurations: [
      { label: 'Exterior Finished', amount: 105000 },
      { label: 'Turnkey', amount: 163000 },
    ],
    area: { number: 35.54, unit: 'm²', measurementBasis: 'VERIFIED_INTERNAL' },
    class3a: 'CANDIDATE',
    images: 3,
  },
  [SERENITY]: {
    configurations: [
      { label: 'Exterior Finished', amount: 191000 },
      { label: 'Turnkey', amount: 306000 },
    ],
    class3a: 'NOT_A_CANDIDATE',
    class3aReason: 'no-usable-area',
    images: 3,
  },
};

/* Figures that were CORRECTED on 11 October. Their reappearance is the
 * signature of a stale snapshot, and the founder's instruction forbids
 * reinstating superseded pricing. */
const SUPERSEDED = [112700, 208500];

const CREDIT = '© BIOBUILDS';
const CAPTION = 'BIOBUILDS model imagery';
const LINK_BACK = 'https://www.biobuilds.com/';
/* Grant condition 7: the medium is not established, so no surface may call
 * these photographs, renders or visualisations. */
const MEDIUM_WORDS = /\b(photograph|photo|render(ing|ed)?|visualisation|visualization|cgi)\b/i;

let failed = 0, passed = 0;
const log = [];
function ok(name, detail) {
  passed++; log.push(['PASS', name, detail]);
}
function bad(name, detail) {
  failed++; log.push(['FAIL', name, detail]);
}
function die(msg) {
  console.error('\n  CANNOT ESTABLISH THE FACTS\n  ' + msg + '\n');
  process.exit(2);
}

/* ── load ────────────────────────────────────────────────────────────────── */
function load(path, what) {
  if (!existsSync(path)) die(`${what} is not at ${path}.`);
  try { return JSON.parse(readFileSync(path, 'utf8')); }
  catch (e) { die(`${what} is not readable JSON: ${e.message}`); }
}

function approvedIndex(rights) {
  const rows = Array.isArray(rights) ? rights
    : (Object.values(rights).find(v => Array.isArray(v) && v.length
       && typeof v[0] === 'object') || []);
  const bb = rows.filter(r => (r.organisation_name || '').trim() === 'BIOBUILDS');
  if (!bb.length) die('image-rights-records.json carries no BIOBUILDS record.');
  const approved = new Map(), withheld = new Set();
  for (const r of bb) {
    for (const a of (r.approved_assets || [])) {
      if (a.url) approved.set(a.url, a.product_code || null);
    }
    for (const a of (r.withheld_assets || [])) if (a.url) withheld.add(a.url);
  }
  if (!approved.size) die('no BIOBUILDS asset is enumerated in approved_assets.');
  return { approved, withheld };
}

/* ── the checks ──────────────────────────────────────────────────────────── */
function run(universe, rights) {
  failed = 0; passed = 0; log.length = 0;
  const { approved, withheld } = approvedIndex(rights);
  const products = Array.isArray(universe.products) ? universe.products : [];
  if (!products.length) die('the artefact carries no products array.');
  const byCode = new Map(products.map(p => [p.productCode, p]));

  /* V1 — the artefact was built by a gate-aware generator. Without this
   * declaration the runtime reader falls back to its older behaviour, so a
   * missing gate is not a detail. */
  universe.publicationGate && universe.publicationGate.version
    ? ok('V1  the artefact declares its publication gate',
         universe.publicationGate.version)
    : bad('V1  the artefact declares its publication gate',
          'publicationGate.version is absent — this artefact predates the gate');

  /* V2 — it was regenerated on or after the founder's decision. An artefact
   * older than the decision cannot carry the decision. */
  const gen = String(universe.generated || '');
  /^\d{4}-\d{2}-\d{2}/.test(gen)
    ? (gen.slice(0, 10) >= DECISION_DATE
        ? ok('V2  regenerated on or after the founder decision', gen)
        : bad('V2  regenerated on or after the founder decision',
              `generated ${gen}, decision ${DECISION_DATE} — this is a stale artefact`))
    : bad('V2  regenerated on or after the founder decision',
          `generated is ${gen || 'absent'} and cannot be read as a date`);

  /* V3 / V4 — both products present and publicly visible. */
  for (const [code, name] of [[WANDERLUST, 'Wanderlust'], [SERENITY, 'Serenity']]) {
    const p = byCode.get(code);
    if (!p) { bad(`V3  ${name} is in the artefact`, `${code} not found`); continue; }
    ok(`V3  ${name} is in the artefact`, `${code} · ${p.productName}`);
    (p.publicVisibility === 'PUBLISHABLE' && !p.holdReason)
      ? ok(`V4  ${name} is PUBLISHABLE`, 'holdReason null')
      : bad(`V4  ${name} is PUBLISHABLE`,
            `publicVisibility=${p.publicVisibility} holdReason=${p.holdReason}`);
  }

  const w = byCode.get(WANDERLUST);
  const s = byCode.get(SERENITY);

  /* V5 — Wanderlust's verified internal area, to the figure and the basis.
   * The basis is load-bearing: 35.54 with an unresolved basis is a different
   * claim from 35.54 measured internally. */
  if (w) {
    const a = w.area || {}, e = EXPECTED[WANDERLUST].area;
    (a.number === e.number && a.unit === e.unit
     && a.measurementBasis === e.measurementBasis)
      ? ok('V5  Wanderlust interior area is 35.54 m², verified internal',
           `${a.number} ${a.unit} · ${a.measurementBasis}`)
      : bad('V5  Wanderlust interior area is 35.54 m², verified internal',
            `got ${a.number} ${a.unit} · ${a.measurementBasis}`);
  }

  /* V6 — Class 3A for Wanderlust, and V7 — Serenity's ineligibility WITH its
   * reason. "Not a candidate" for the wrong reason would still be wrong. */
  if (w) {
    (w.class3a && w.class3a.state === EXPECTED[WANDERLUST].class3a)
      ? ok('V6  Wanderlust is a Class 3A CANDIDATE', w.class3a.state)
      : bad('V6  Wanderlust is a Class 3A CANDIDATE',
            `got ${w.class3a && w.class3a.state}`);
  }
  if (s) {
    const c = s.class3a || {};
    (c.state === EXPECTED[SERENITY].class3a
     && c.reason === EXPECTED[SERENITY].class3aReason)
      ? ok('V7  Serenity is NOT a Class 3A candidate, for want of a usable area',
           `${c.state} · ${c.reason}`)
      : bad('V7  Serenity is NOT a Class 3A candidate, for want of a usable area',
            `got ${c.state} · ${c.reason}`);
  }

  /* V8 — the two named configurations, each with its own label and amount. */
  for (const [code, name] of [[WANDERLUST, 'Wanderlust'], [SERENITY, 'Serenity']]) {
    const p = byCode.get(code);
    if (!p) continue;
    const got = ((p.price || {}).configurations || [])
      .map(c => ({ label: c.label, amount: c.amount }));
    const want = EXPECTED[code].configurations;
    const same = got.length === want.length && want.every(
      x => got.some(y => y.label === x.label && y.amount === x.amount));
    same
      ? ok(`V8  ${name} carries both named configurations`,
           got.map(c => `€${c.amount.toLocaleString('en-IE')} ${c.label}`).join(' · '))
      : bad(`V8  ${name} carries both named configurations`,
            `got ${JSON.stringify(got)}`);
  }

  /* V9 — VAT basis stated, and stated as inclusive. VAT_UNKNOWN rendered as
   * though it meant inclusive is the exact failure the field exists for. */
  for (const [code, name] of [[WANDERLUST, 'Wanderlust'], [SERENITY, 'Serenity']]) {
    const p = byCode.get(code);
    if (!p) continue;
    const basis = (p.price || {}).basis;
    basis === 'INCLUDES_VAT'
      ? ok(`V9  ${name} prices are stated VAT-inclusive`, basis)
      : bad(`V9  ${name} prices are stated VAT-inclusive`, `basis=${basis}`);
  }

  /* V10 — no superseded figure anywhere in either record. */
  for (const [code, name] of [[WANDERLUST, 'Wanderlust'], [SERENITY, 'Serenity']]) {
    const p = byCode.get(code);
    if (!p) continue;
    const blob = JSON.stringify(p);
    const hits = SUPERSEDED.filter(n => blob.includes(String(n)));
    hits.length === 0
      ? ok(`V10 ${name} carries no superseded price`, 'none of ' + SUPERSEDED.join(', '))
      : bad(`V10 ${name} carries no superseded price`,
            `superseded figure(s) present: ${hits.join(', ')}`);
  }

  /* V11 — Wanderlust receives its three approved images. */
  if (w) {
    const set = Array.isArray(w.imagerySet) ? w.imagerySet : [];
    const n = EXPECTED[WANDERLUST].images;
    (set.length === n && w.imagery && w.imagery.url)
      ? ok('V11 Wanderlust receives its three authorised images',
           `${set.length} in the set, primary ${w.imagery.url.split('/').pop()}`)
      : bad('V11 Wanderlust receives its three authorised images',
            `imagerySet=${set.length} primary=${!!(w.imagery && w.imagery.url)}`);
  }

  /* V12 — every published image is ENUMERATED for ITS OWN product. Being on
   * the supplier's domain is never what makes an image publishable. */
  {
    const problems = [];
    for (const p of products) {
      const ims = [].concat(p.imagery || [], p.imagerySet || []).filter(Boolean);
      for (const im of ims) {
        if (!approved.has(im.url)) {
          problems.push(`${p.productCode}: ${im.url} is not enumerated`);
        } else if (approved.get(im.url) !== p.productCode) {
          problems.push(`${p.productCode}: ${im.url} is approved for `
                        + `${approved.get(im.url)}`);
        }
      }
    }
    problems.length === 0
      ? ok('V12 every published image is enumerated for its own product',
           'checked every product in the artefact')
      : bad('V12 every published image is enumerated for its own product',
            problems.join(' | '));
  }

  /* V13 — the withheld assets reach no public surface. */
  {
    const blob = JSON.stringify(universe);
    const leaked = [...withheld].filter(u => blob.includes(u));
    leaked.length === 0
      ? ok('V13 no withheld asset appears in the artefact',
           `${withheld.size} withheld asset(s) absent`)
      : bad('V13 no withheld asset appears in the artefact', leaked.join(' | '));
  }

  /* V14 — attribution and link-back on every image, and NO claim about the
   * medium. Grant condition 7 is a condition of the permission, not a
   * stylistic preference. */
  {
    const problems = [];
    for (const p of products) {
      for (const im of [].concat(p.imagery || [], p.imagerySet || []).filter(Boolean)) {
        const tag = `${p.productCode}/${(im.url || '').split('/').pop()}`;
        if (im.credit !== CREDIT) problems.push(`${tag}: credit=${im.credit}`);
        if (im.supplier !== 'BIOBUILDS') problems.push(`${tag}: supplier=${im.supplier}`);
        if (im.linkBack !== LINK_BACK) problems.push(`${tag}: linkBack=${im.linkBack}`);
        if (im.caption !== CAPTION) problems.push(`${tag}: caption=${im.caption}`);
        if (!im.rightsRecord) problems.push(`${tag}: no rightsRecord`);
        if (!im.alt) problems.push(`${tag}: no alt text`);
        if (!String(im.url || '').startsWith('https://'))
          problems.push(`${tag}: not https`);
        if (!im.permittedPrefix || !String(im.url).startsWith(im.permittedPrefix))
          problems.push(`${tag}: url outside its permitted prefix`);
        for (const field of ['alt', 'caption']) {
          if (MEDIUM_WORDS.test(String(im[field] || '')))
            problems.push(`${tag}: ${field} names the medium`);
        }
      }
    }
    problems.length === 0
      ? ok('V14 every image carries credit, link-back and a medium-neutral caption',
           `${CREDIT} · ${CAPTION} · ${LINK_BACK}`)
      : bad('V14 every image carries credit, link-back and a medium-neutral caption',
            problems.join(' | '));
  }

  /* V15 — no HELD product anywhere carries imagery. The gate and the imagery
   * must not be able to disagree about whether a supplier is public. */
  {
    const held = products.filter(
      p => p.publicVisibility === 'HOLD'
        && ((p.imagery) || (p.imagerySet || []).length));
    held.length === 0
      ? ok('V15 no held product carries imagery',
           `${products.filter(p => p.publicVisibility === 'HOLD').length} held product(s)`)
      : bad('V15 no held product carries imagery',
            held.map(p => p.productCode).join(', '));
  }

  return { passed, failed, log: log.slice() };
}

/* ── the capability proof ────────────────────────────────────────────────── */
function selfTest(universe, rights) {
  const clone = () => JSON.parse(JSON.stringify(universe));
  const find = (u, code) => u.products.find(p => p.productCode === code);

  const mutations = [
    ['V1', 'remove the publication gate declaration',
      u => { delete u.publicationGate; }],
    ['V2', 'date the artefact before the founder decision',
      u => { u.generated = '2026-09-22T22:48:16Z'; }],
    ['V3', 'drop Wanderlust from the artefact',
      u => { u.products = u.products.filter(p => p.productCode !== WANDERLUST); }],
    ['V4', 'put Wanderlust back on HOLD',
      u => { const p = find(u, WANDERLUST); p.publicVisibility = 'HOLD';
             p.holdReason = 'listing-review-awaiting-confirmation'; }],
    ['V5', 'restore the unevidenced 48 m² area',
      u => { find(u, WANDERLUST).area = { number: 48, unit: 'm²',
             measurementBasis: 'UNRESOLVED', text: null }; }],
    ['V6', 'demote Wanderlust out of the Class 3A pathway',
      u => { find(u, WANDERLUST).class3a =
             { state: 'NOT_A_CANDIDATE', reason: 'no-usable-area', caveats: [] }; }],
    ['V7', 'promote Serenity into the Class 3A pathway',
      u => { find(u, SERENITY).class3a =
             { state: 'CANDIDATE', reason: null, caveats: [] }; }],
    ['V8', 'collapse the two configurations into one',
      u => { const p = find(u, WANDERLUST);
             p.price.configurations = [p.price.configurations[0]]; }],
    ['V9', 'lose the VAT basis',
      u => { find(u, WANDERLUST).price.basis = 'VAT_UNKNOWN'; }],
    ['V10', 'reinstate the superseded €112,700',
      u => { find(u, WANDERLUST).price.amount = 112700; }],
    ['V11', 'remove two of the three images',
      u => { const p = find(u, WANDERLUST); p.imagerySet = p.imagerySet.slice(0, 1); }],
    ['V12', 'publish an unenumerated image on the supplier domain',
      u => { const p = find(u, WANDERLUST);
             p.imagerySet = p.imagerySet.concat([{ ...p.imagerySet[0],
               url: 'https://www.biobuilds.com/_next/static/immutable/media/not-approved.jpg',
               permittedPrefix: 'https://www.biobuilds.com/_next/static/immutable/media/' }]); }],
    ['V12b', 'move an approved image onto the wrong product',
      u => { const w = find(u, WANDERLUST), s = find(u, SERENITY);
             if (s && w) s.imagerySet = s.imagerySet.concat([w.imagerySet[0]]); }],
    ['V13', 'publish a withheld construction detail',
      u => { const p = find(u, WANDERLUST);
             const { withheld } = approvedIndex(rights);
             p.imagerySet = p.imagerySet.concat([{ ...p.imagerySet[0],
               url: [...withheld][0] }]); }],
    ['V14', 'drop the supplier credit',
      u => { find(u, WANDERLUST).imagerySet[0].credit = null; }],
    ['V14b', 'describe the imagery as a photograph',
      u => { find(u, WANDERLUST).imagerySet[0].alt =
             'A photograph of the completed Wanderlust.'; }],
    ['V14c', 'break the link back to the supplier',
      u => { find(u, WANDERLUST).imagerySet[0].linkBack = null; }],
    ['V15', 'give a held product imagery',
      u => { const p = u.products.find(x => x.publicVisibility === 'HOLD');
             if (p) { p.imagery = find(u, WANDERLUST).imagery;
                      p.imagerySet = [find(u, WANDERLUST).imagery]; }
             else { u.products.push({ ...find(u, WANDERLUST),
                      productCode: 'PROD-SYNTH', publicVisibility: 'HOLD',
                      holdReason: 'listing-review-awaiting-confirmation' }); } }],
  ];

  console.log('\n  CAPABILITY PROOF — each mutation must make a check FAIL.');
  console.log('  ' + '-'.repeat(70));
  const control = run(universe, rights);
  if (control.failed !== 0) {
    console.error('\n  CONTROL FAILED: the artefact does not pass as it stands, so a '
      + 'mutation proving a failure would prove nothing. Fix the artefact first.\n');
    for (const [s, n, d] of control.log) if (s === 'FAIL') console.error(`    ${n} — ${d}`);
    process.exit(2);
  }
  console.log(`    CONTROL  ${control.passed} checks pass on the real artefact`);

  let proved = 0, notProved = 0;
  for (const [aimed, what, mutate] of mutations) {
    const u = clone();
    try { mutate(u); } catch (e) {
      console.log(`    SKIP     ${aimed.padEnd(5)} ${what} — could not apply: ${e.message}`);
      notProved++; continue;
    }
    if (JSON.stringify(u) === JSON.stringify(universe)) {
      console.log(`    VACUOUS  ${aimed.padEnd(5)} ${what} — the mutation changed nothing`);
      notProved++; continue;
    }
    const r = run(u, rights);
    const fired = r.log.filter(([s]) => s === 'FAIL').map(([, n]) => n.split(/\s+/)[0]);
    const base = aimed.replace(/[a-z]$/, '');
    if (r.failed === 0) {
      console.log(`    MISSED   ${aimed.padEnd(5)} ${what} — nothing failed`);
      notProved++;
    } else if (!fired.includes(base)) {
      console.log(`    MISATTR  ${aimed.padEnd(5)} ${what} — failed, but at `
                  + `${fired.join(',')} rather than ${base}`);
      notProved++;
    } else {
      console.log(`    PROVED   ${aimed.padEnd(5)} ${what}`);
      proved++;
    }
  }
  console.log('  ' + '-'.repeat(70));
  console.log(`  ${mutations.length} mutations, ${proved} proved capable, `
              + `${notProved} not proved\n`);
  return notProved === 0 ? 0 : 1;
}

/* ── main ────────────────────────────────────────────────────────────────── */
const universe = load(UNIVERSE, 'additional-home-universe-v1.json');
const rights = load(RIGHTS, 'image-rights-records.json');

if (process.argv.includes('--self-test')) {
  process.exit(selfTest(universe, rights));
}

const r = run(universe, rights);
console.log('\n  BIOBUILDS PUBLICATION — ACCEPTANCE CHECK');
console.log('  founder authorisation FX-BIOBUILDS-PUBLISH-20261011');
console.log('  ' + '-'.repeat(70));
for (const [state, name, detail] of r.log) {
  console.log(`  ${state === 'PASS' ? ' PASS ' : '*FAIL*'} ${name}`);
  if (detail) console.log(`         ${detail}`);
}
console.log('  ' + '-'.repeat(70));
console.log(`  ${r.passed + r.failed} checks, ${r.passed} passed, ${r.failed} failed\n`);
if (r.failed) {
  console.log('  DO NOT DEPLOY. The regenerated artefact does not carry the '
              + 'authorised facts.\n');
}
process.exit(r.failed ? 1 : 0);
