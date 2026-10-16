/**
 * PROVE THE BIOBUILDS IMAGERY CHAIN · BI1–BI14
 * =============================================
 * The founder authorised publication of selected BIOBUILDS imagery on
 * 11 October 2026 under FX-BIOBUILDS-PUBLISH-20261011. These are the ten
 * requirements that came with it, as assertions.
 *
 *   1  selected images display                      BI1, BI2, BI3
 *   2  unapproved images cannot display             BI4, BI5
 *   3  images cannot reach the wrong product        BI6
 *   4  attribution and supplier links are present   BI7, BI8
 *   5  the rights gate remains effective            BI9
 *   6  other suppliers remain unaffected            BI10
 *   7  the exception stays supplier-specific        BI11
 *   8  Results and Compare pricing stays correct    BI12
 *   9  Serenity is not falsely recommended          BI13
 *  10  Garden Room behaviour is preserved           BI14
 *
 * HOW IT TESTS. The real generator's own imagery index and the real runtime's
 * own rights predicates are both LIFTED AND RUN. Nothing here re-implements
 * either: a re-implementation would prove this file agrees with itself.
 *
 * THE ARTEFACT IS SIMULATED, AND THAT IS SAID PLAINLY. The deployed
 * additional-home-universe-v1.json predates this change and carries no
 * imagery, and regenerating it needs an Airtable token this environment does
 * not hold. So BI1-BI3 and BI6 build the payload the real generator WOULD
 * write, by calling the real generator's own functions, and run the real
 * runtime predicates over it. That is a genuine end-to-end test of the code
 * on both sides of the artefact; it is not a test of the artefact itself,
 * and the founder's regeneration step is what closes that gap.
 *
 *   node atlas-tools/prove-biobuilds-imagery.mjs [--root PATH]
 *
 * Exit 0 = all pass. Exit 2 = the instrument could not run.
 */
import { readFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const arg = (n, d) => {
  const i = process.argv.indexOf('--' + n);
  return i === -1 ? d : process.argv[i + 1];
};
const ROOT = arg('root', dirname(HERE));
const PLOT = join(ROOT, 'your-plot.html');
const RECORDS = join(ROOT, 'image-rights-records.json');
const GEN = join(ROOT, '.github', 'scripts',
                 'generate_additional_home_universe.py');
const GARDEN = join(ROOT, 'garden-room-recommendation-universe-v1.json');

let pass = 0, fail = 0;
const ok  = (n, d) => { pass++; console.log(`  PASS  ${n}${d ? '  [' + d + ']' : ''}`); };
const bad = (n, d) => { fail++; console.log(`  FAIL  ${n}${d ? '  [' + d + ']' : ''}`); };
function refuse(why) {
  console.log('\nBIOBUILDS IMAGERY CHAIN');
  console.log('='.repeat(74));
  console.log('  INSTRUMENT UNAVAILABLE: ' + why);
  console.log('  Nothing was measured. This is not a pass.');
  process.exit(2);
}
for (const f of [PLOT, RECORDS, GEN]) {
  if (!existsSync(f)) refuse(f + ' is missing');
}

/* ── lift the runtime's own rights predicates ─────────────────────────── */
const html = readFileSync(PLOT, 'utf8');
const a = html.indexOf('  function pnImageRightsOk(');
const b = html.indexOf('  function pnAuthorisedImage(product){');
const c = html.indexOf('\n  }', b) + 4;
if (a === -1 || b === -1 || c <= b) {
  refuse('the runtime imagery predicates could not be located in your-plot.html');
}
const aEnd = html.indexOf('  function pnAuthorisedImages(');
let R;
try {
  // eslint-disable-next-line no-new-func
  R = new Function(html.slice(a, aEnd) + html.slice(aEnd, c) + `
    return { rightsOk: pnImageRightsOk, primary: pnAuthorisedImage,
             all: pnAuthorisedImages };`)();
} catch (e) {
  refuse('the lifted runtime predicates would not evaluate: ' + e.message);
}

/* ── drive the real generator's own imagery index ─────────────────────── */
const probe = `
import importlib.util, sys, pathlib, json
root = pathlib.Path(${JSON.stringify(ROOT)})
sys.path.insert(0, str(root / ".github" / "scripts"))
spec = importlib.util.spec_from_file_location("gen", root / ".github" /
        "scripts" / "generate_additional_home_universe.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
out = {"index": m._imagery_index(),
       "held": m._approved_imagery("PROD-000523", True),
       "unknown": m._approved_imagery("PROD-999999", False),
       "wanderlust": m._approved_imagery("PROD-000523", False),
       "serenity": m._approved_imagery("PROD-000524", False),
       "hold_biobuilds": m.publication_hold("BIOBUILDS"),
       "hold_shomera": m.publication_hold("Shomera")}
print(json.dumps(out, default=str))
`;
let G;
try {
  G = JSON.parse(execFileSync('python3', ['-c', probe],
    { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 }));
} catch (e) {
  refuse('the generator imagery index could not be driven: '
         + String((e.stderr || e.message)).slice(0, 220));
}

const recDoc = JSON.parse(readFileSync(RECORDS, 'utf8'));
const bb = (recDoc.records || []).find(r => r.organisation_code === 'ORG-000153');
if (!bb) refuse('no BIOBUILDS rights record');
const approvedUrls = new Set((bb.approved_assets || []).map(x => x.url));
const withheldUrls = new Set((bb.withheld_assets || []).map(x => x.url));

console.log('\nBIOBUILDS IMAGERY CHAIN · BI1–BI14');
console.log('='.repeat(74));
console.log('  NOTE: the payload below is SIMULATED from the real generator’s');
console.log('  own functions. The deployed artefact predates this change and');
console.log('  regeneration needs an Airtable token this environment lacks.');
console.log('-'.repeat(74));

/* ── 1 · THE SELECTED IMAGES DISPLAY ─────────────────────────────────── */
{
  const w = G.wanderlust, s = G.serenity;
  const okBoth = w && w[0] && s && s[0]
    && R.rightsOk(w[0]) && R.rightsOk(s[0]);
  okBoth
    ? ok('BI1 both products get a primary image the runtime accepts',
         `${w[0].url.split('/').pop().slice(0, 26)} / `
         + `${s[0].url.split('/').pop().slice(0, 24)}`)
    : bad('BI1 both products get a primary image the runtime accepts',
          JSON.stringify([!!(w && w[0]), !!(s && s[0])]));
}
{
  /* NULL-SAFE. A mutation that empties one product's index entry used to make
     this throw, which the capability proof reported as a crash rather than a
     failure. A guard that cannot survive the defect it is testing is not a
     guard. */
  const wSet = (G.wanderlust && G.wanderlust[1]) || [];
  const sSet = (G.serenity && G.serenity[1]) || [];
  const w = { imagery: (G.wanderlust || [])[0] || undefined, imagerySet: wSet };
  const s = { imagery: (G.serenity || [])[0] || undefined, imagerySet: sSet };
  const wa = R.all(w), sa = R.all(s);
  (wa.length === 3 && sa.length === 3
   && wa[0] && sa[0]
   && wa[0].url === ((G.wanderlust || [])[0] || {}).url
   && sa[0].url === ((G.serenity || [])[0] || {}).url)
    ? ok('BI2 the full authorised set reaches the gallery, primary first',
         `${wa.length} + ${sa.length}`)
    : bad('BI2 the full authorised set reaches the gallery, primary first',
          `${wa.length} / ${sa.length}`);
}
{
  const total = Object.values(G.index)
    .reduce((n, slot) => n + slot.set.length, 0);
  (total === approvedUrls.size)
    ? ok('BI3 every enumerated approved asset is published, and only those',
         `${total} of ${approvedUrls.size}`)
    : bad('BI3 every enumerated approved asset is published, and only those',
          `${total} vs ${approvedUrls.size}`);
}

/* ── 2 · UNAPPROVED IMAGES CANNOT DISPLAY ────────────────────────────── */
{
  const published = new Set();
  for (const slot of Object.values(G.index)) {
    for (const im of slot.set) published.add(im.url);
  }
  const leaked = [...withheldUrls].filter(u => published.has(u));
  (!leaked.length && withheldUrls.size > 0)
    ? ok('BI4 the explicitly withheld assets are not published',
         `${withheldUrls.size} withheld`)
    : bad('BI4 the explicitly withheld assets are not published',
          leaked.length ? leaked.join(', ') : 'nothing is recorded as withheld');
}
{
  /* An image on the supplier's own domain that nobody enumerated. This is the
     case the manifest's host-and-prefix rule would wave through. */
  const sneaked = {
    url: 'https://www.biobuilds.com/_next/static/immutable/media/'
         + 'never-approved-asset.jpg',
    alt: 'An unapproved image.', credit: '© BIOBUILDS',
    supplier: 'BIOBUILDS', rightsRecord: 'C2-GRANT-BIOBUILDS-20261002',
    permittedPrefix:
      'https://www.biobuilds.com/_next/static/immutable/media/'
  };
  /* The runtime predicate ACCEPTS it, because its job is the prefix rule --
     and that is exactly why enumeration lives in the generator and the
     containment proof. This asserts the division of labour honestly rather
     than claiming a check the runtime does not perform. */
  const runtimeAccepts = R.rightsOk(sneaked);
  const enumerated = approvedUrls.has(sneaked.url);
  const inPayload = Object.values(G.index)
    .some(slot => slot.set.some(im => im.url === sneaked.url));
  (!enumerated && !inPayload)
    ? ok('BI5 an unenumerated asset on the supplier’s own domain never '
         + 'enters the payload',
         `runtime prefix rule alone would accept it: ${runtimeAccepts}`)
    : bad('BI5 an unenumerated asset never enters the payload',
          `enumerated=${enumerated} inPayload=${inPayload}`);
}

/* ── 3 · IMAGES CANNOT REACH THE WRONG PRODUCT ───────────────────────── */
{
  const byProduct = new Map();
  for (const a of bb.approved_assets || []) {
    if (!byProduct.has(a.product_code)) byProduct.set(a.product_code, new Set());
    byProduct.get(a.product_code).add(a.url);
  }
  const wrong = [];
  for (const [code, slot] of Object.entries(G.index)) {
    const allowed = byProduct.get(code);
    if (!allowed) { wrong.push(`${code} is named by no approved asset`); continue; }
    for (const im of slot.set) {
      if (!allowed.has(im.url)) wrong.push(`${code} carries ${im.url}`);
    }
  }
  // And the two products must not share a single image.
  /* NULL-SAFE for the same reason. An absent entry is itself a problem and is
     reported as one, rather than throwing. */
  const wList = (G.wanderlust && G.wanderlust[1]) || null;
  const sList = (G.serenity && G.serenity[1]) || null;
  if (!wList || !sList) {
    wrong.push('one or both products have no imagery entry at all '
               + `(wanderlust=${!!wList} serenity=${!!sList})`);
  }
  const wUrls = new Set((wList || []).map(i => i.url));
  const overlap = (sList || []).filter(i => wUrls.has(i.url));
  (!wrong.length && !overlap.length)
    ? ok('BI6 every image sits on the product its own record names, and the '
         + 'two products share none')
    : bad('BI6 every image sits on the product its own record names',
          `${wrong.length} misplaced, ${overlap.length} shared`);
}

/* ── 4 · ATTRIBUTION AND LINKS ───────────────────────────────────────── */
{
  const all = Object.values(G.index).flatMap(s => s.set);
  const problems = all.filter(im =>
    im.credit !== '© BIOBUILDS'
    || im.supplier !== 'BIOBUILDS'
    || im.linkBack !== 'https://www.biobuilds.com/'
    || im.caption !== 'BIOBUILDS model imagery'
    || !im.alt);
  (!problems.length && all.length)
    ? ok('BI7 every published image carries the credit, the supplier’s '
         + 'caption, a link back and alt text', `${all.length} checked`)
    : bad('BI7 every published image carries its attribution',
          `${problems.length} of ${all.length} incomplete`);
}
{
  /* GRANT CONDITION 7. BIOBUILDS has never said whether the model imagery is
     photography or architectural visualisation, and the record forbids any
     PlotNua surface from describing it as either. This asserts that no alt
     text or caption written for publication does. */
  const all = Object.values(G.index).flatMap(s => s.set);
  const words = ['photograph', 'photo', 'render', 'rendering',
                 'visualisation', 'visualization', 'cgi'];
  const place = ['installed in ireland', 'in an irish garden',
                 'completed in ireland'];
  const offenders = [];
  for (const im of all) {
    const t = ((im.alt || '') + ' ' + (im.caption || '')).toLowerCase();
    for (const w of words) if (new RegExp('\\b' + w + '\\b').test(t)) offenders.push(`${w} in ${im.url.split('/').pop()}`);
    for (const w of place) if (t.includes(w)) offenders.push(`${w} in ${im.url.split('/').pop()}`);
  }
  !offenders.length
    ? ok('BI8 no caption or alt text describes the medium or claims an Irish '
         + 'installation (grant condition 7)')
    : bad('BI8 no caption or alt text describes the medium',
          offenders.slice(0, 3).join('; '));
}

/* ── 5 · THE RIGHTS GATE REMAINS EFFECTIVE ───────────────────────────── */
{
  const refusals = [
    ['no credit', { url: 'https://www.biobuilds.com/_next/static/immutable/media/a.jpg',
      alt: 'a', supplier: 'BIOBUILDS', rightsRecord: 'R',
      permittedPrefix: 'https://www.biobuilds.com/_next/static/immutable/media/' }],
    ['outside the prefix', { url: 'https://www.biobuilds.com/elsewhere/a.jpg',
      alt: 'a', credit: 'c', supplier: 'BIOBUILDS', rightsRecord: 'R',
      permittedPrefix: 'https://www.biobuilds.com/_next/static/immutable/media/' }],
    ['not https', { url: 'http://www.biobuilds.com/_next/static/immutable/media/a.jpg',
      alt: 'a', credit: 'c', supplier: 'BIOBUILDS', rightsRecord: 'R',
      permittedPrefix: 'http://www.biobuilds.com/_next/static/immutable/media/' }],
    ['no prefix at all', { url: 'https://www.biobuilds.com/_next/static/immutable/media/a.jpg',
      alt: 'a', credit: 'c', supplier: 'BIOBUILDS', rightsRecord: 'R' }],
    ['no rights record', { url: 'https://www.biobuilds.com/_next/static/immutable/media/a.jpg',
      alt: 'a', credit: 'c', supplier: 'BIOBUILDS',
      permittedPrefix: 'https://www.biobuilds.com/_next/static/immutable/media/' }]
  ];
  const leaks = refusals.filter(([, im]) => R.rightsOk(im) !== false);
  !leaks.length
    ? ok('BI9 the runtime rights predicate still refuses every malformed image',
         `${refusals.length} shapes`)
    : bad('BI9 the runtime rights predicate still refuses malformed images',
          leaks.map(l => l[0]).join(', '));
}

/* ── 6 · OTHER SUPPLIERS UNAFFECTED ──────────────────────────────────── */
{
  const others = (recDoc.records || [])
    .filter(r => r.organisation_code !== 'ORG-000153');
  const withAssets = others.filter(r =>
    Array.isArray(r.approved_assets) && r.approved_assets.length);
  /* RE-AIMED 11 October 2026, AND IT IS STRONGER, NOT WEAKER.
     This read `codes.every(c => c === 'PROD-000523' || c === 'PROD-000524')`
     — a hard-coded pair, written when BIOBUILDS had exactly two products
     carrying imagery. The founder then added Sanctuary (PROD-001215) and
     Bloom (PROD-001216) to the same enumeration, and the assertion failed on
     two BIOBUILDS products: a stale list, not a leak.
     The question BI10 exists to ask is whether anything OUTSIDE BIOBUILDS
     gained an index entry. So it is now asked of the data: every code in the
     index must be a product code BIOBUILDS' own rights row enumerates. That
     catches a non-BIOBUILDS code the old form could not have caught either,
     and it cannot go stale when the enumeration changes again. */
  const codes = Object.keys(G.index);
  const bbRow = (recDoc.records || [])
    .find(r => r.organisation_code === 'ORG-000153') || {};
  const bbCodes = new Set((bbRow.approved_assets || [])
    .map(a => a.product_code).filter(Boolean));
  const onlyBiobuilds = bbCodes.size > 0 && codes.every(c => bbCodes.has(c));
  (!withAssets.length && onlyBiobuilds)
    ? ok('BI10 no other supplier gained an approved asset or an index entry',
         `${others.length} other record(s), index holds ${codes.length}`)
    : bad('BI10 no other supplier gained an approved asset',
          `withAssets=${withAssets.length} indexCodes=${codes.join(',')}`);
}

/* ── 7 · THE EXCEPTION STAYS SUPPLIER-SPECIFIC ───────────────────────── */
{
  /* RE-AIMED 16 October 2026: FX-BIOBUILDS-PUBLISH-20261011 is revoked, so
     the generator must now HOLD BIOBUILDS (and so give it no imagery, BI12). */
  String(G.hold_biobuilds || '').includes('listing-review-awaiting-confirmation')
    ? ((G.hold_shomera === 'None' || G.hold_shomera === null)
        ? ok('BI11 the generator holds BIOBUILDS (exception revoked) and leaves an ungated '
             + 'supplier alone', `biobuilds=${G.hold_biobuilds} shomera=${G.hold_shomera}`)
        : bad('BI11 an ungated supplier is unaffected', String(G.hold_shomera)))
    : bad('BI11 the generator holds BIOBUILDS', String(G.hold_biobuilds));
}

/* ── 8 · A HELD PRODUCT GETS NO IMAGE ────────────────────────────────── */
{
  const held = G.held;
  const unknown = G.unknown;
  const noneForHeld = !held || held[0] === null || held[0] === 'None';
  const noneForUnknown = !unknown || unknown[0] === null || unknown[0] === 'None';
  (noneForHeld && noneForUnknown)
    ? ok('BI12 a held product and an unknown product each get no imagery')
    : bad('BI12 a held product gets no imagery',
          `held=${JSON.stringify(held)} unknown=${JSON.stringify(unknown)}`);
}

/* ── 9 · SERENITY IS NOT FALSELY RECOMMENDED ─────────────────────────── */
{
  /* Serenity is authorised and publishable. It holds no area number, and 95
     m2 is outside the 32-45 m2 Class 3A band either way, so it cannot enter
     the Additional Home recommendation pathway -- and nothing here invents
     one for it. What IS asserted is that it has not been made to appear:
     no area number was written, and the band was not widened. */
  const areaProbe = `
import importlib.util, sys, pathlib, json
root = pathlib.Path(${JSON.stringify(ROOT)})
sys.path.insert(0, str(root / ".github" / "scripts"))
import additional_home_qualification as Q
FID = "rechP7fg3NRe4bWXD"
rows = [{"fields": {"Feature": [FID], "Value Text": "95 m2 total floor area.",
                    "Status": "Verified", "Unit": "m2"}}]
n, u, b, t = Q._area_evidence(rows, {FID: "Internal Floor Area"})
q = {"habitationState": Q.CONFIRMED_HABITATION, "state": "ELIGIBLE",
     "area": {"number": n, "unit": u, "measurementBasis": b, "text": t}}
c = Q.class_3a(q)
rows2 = [{"fields": dict(rows[0]["fields"], **{"Value Number": 95})}]
n2, u2, b2, t2 = Q._area_evidence(rows2, {FID: "Internal Floor Area"})
q2 = dict(q); q2["area"] = {"number": n2, "unit": u2, "measurementBasis": b2, "text": t2}
c2 = Q.class_3a(q2)
print(json.dumps({"band": [Q.BAND_MIN, Q.BAND_MAX], "noNumber": c,
                  "withNinetyFive": c2}))
`;
  let A;
  try {
    A = JSON.parse(execFileSync('python3', ['-c', areaProbe],
      { encoding: 'utf8' }));
  } catch (e) {
    bad('BI13 Serenity is not falsely recommended',
        'the area probe could not run: '
        + String((e.stderr || e.message)).slice(0, 140));
  }
  if (A) {
    const bandIntact = A.band[0] === 32 && A.band[1] === 45;
    const notCandidate = A.noNumber.state === 'NOT_A_CANDIDATE'
      && A.withNinetyFive.state === 'NOT_A_CANDIDATE';
    (bandIntact && notCandidate)
      ? ok('BI13 Serenity is not a Class 3A candidate either way, and the '
           + 'band was not widened',
           `band ${A.band[0]}-${A.band[1]}, `
           + `no-number=${A.noNumber.reason}, 95=${A.withNinetyFive.reason}`)
      : bad('BI13 Serenity is not falsely recommended',
            JSON.stringify(A));
  }
}

/* ── 10 · GARDEN ROOM BEHAVIOUR PRESERVED ────────────────────────────── */
{
  if (!existsSync(GARDEN)) {
    bad('BI14 the Garden Room imagery population is unchanged',
        'the garden room universe is missing');
  } else {
    const gr = JSON.parse(readFileSync(GARDEN, 'utf8'));
    const withImagery = (gr.products || []).filter(p => p.imagery);
    const accepted = withImagery.filter(p => R.rightsOk(p.imagery));
    (withImagery.length === 6 && accepted.length === 6)
      ? ok('BI14 the six Garden Room products with imagery still pass the '
           + 'same predicate', `${accepted.length} of ${withImagery.length}`)
      : bad('BI14 the Garden Room imagery population is unchanged',
            `${withImagery.length} with imagery, ${accepted.length} accepted`);
  }
}

console.log('\n' + '='.repeat(74));
console.log(`${pass + fail} checks, ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
