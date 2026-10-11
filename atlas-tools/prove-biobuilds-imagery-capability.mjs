/**
 * GUARD-CAPABILITY PROOF — THE IMAGERY GUARDS CAN ACTUALLY FAIL
 * ==============================================================
 * Publishing a supplier's imagery is the kind of change where a guard that
 * has never been seen to refuse is worse than no guard at all: everyone
 * assumes it is watching. Each case below breaks ONE thing in a DISPOSABLE
 * tree and requires the named check to fail.
 *
 *   VACUOUS       the suite passed anyway
 *   BLIND         the suite errored or refused
 *   MISATTRIBUTED something failed, but not the right check
 *
 * all count as failures of the PROOF. The control runs first.
 *
 * NOTHING IN THE REPOSITORY IS MUTATED, and the tree is hashed before and
 * after to prove it.
 *
 *   node atlas-tools/prove-biobuilds-imagery-capability.mjs
 *
 * Exit 0 = every guard proved capable.
 */
import { readFileSync, writeFileSync, mkdtempSync, mkdirSync, copyFileSync,
         existsSync, cpSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const SUITE = join(HERE, 'prove-biobuilds-imagery.mjs');
const CONTAIN = join(HERE, 'prove-biobuilds-containment.mjs');
const RECORDS = join(ROOT, 'image-rights-records.json');
const PLOT = join(ROOT, 'your-plot.html');
const GARDEN = join(ROOT, 'garden-room-recommendation-universe-v1.json');
const PREVIEW = join(ROOT, 'biobuilds-preview.html');

for (const f of [SUITE, CONTAIN, RECORDS, PLOT, GARDEN]) {
  if (!existsSync(f)) {
    console.log('\nINSTRUMENT UNAVAILABLE: ' + f + ' is missing.');
    process.exit(2);
  }
}
const sha = f => createHash('sha256').update(readFileSync(f)).digest('hex');
const before = {
  records: sha(RECORDS), plot: sha(PLOT), suite: sha(SUITE),
  contain: sha(CONTAIN),
  gen: sha(join(ROOT, '.github', 'scripts',
                'generate_additional_home_universe.py'))
};

let proved = 0, broken = 0;
const log = s => console.log(s);

/* A disposable tree holding everything both suites read. */
function tree({ recordEdit = null, genEdit = null, plotEdit = null,
                gardenEdit = null, extraPage = null } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'pn-img-'));
  mkdirSync(join(dir, 'atlas-tools'), { recursive: true });
  mkdirSync(join(dir, '.github', 'scripts'), { recursive: true });
  cpSync(join(ROOT, '.github', 'scripts'), join(dir, '.github', 'scripts'),
         { recursive: true });
  for (const f of ['prove-biobuilds-imagery.mjs',
                   'prove-biobuilds-containment.mjs']) {
    copyFileSync(join(HERE, f), join(dir, 'atlas-tools', f));
  }

  const rec = JSON.parse(readFileSync(RECORDS, 'utf8'));
  const bb = rec.records.find(r => r.organisation_code === 'ORG-000153');
  if (recordEdit) recordEdit(bb, rec);
  writeFileSync(join(dir, 'image-provenance-placeholder'), '');
  writeFileSync(join(dir, 'image-rights-records.json'),
                JSON.stringify(rec, null, 2));

  let plot = readFileSync(PLOT, 'utf8');
  if (plotEdit) plot = plotEdit(plot);
  writeFileSync(join(dir, 'your-plot.html'), plot);

  if (genEdit) {
    const p = join(dir, '.github', 'scripts',
                   'generate_additional_home_universe.py');
    writeFileSync(p, genEdit(readFileSync(p, 'utf8')));
  }

  let garden = JSON.parse(readFileSync(GARDEN, 'utf8'));
  if (gardenEdit) gardenEdit(garden);
  writeFileSync(join(dir, 'garden-room-recommendation-universe-v1.json'),
                JSON.stringify(garden));

  // The containment proof needs the preview, a sitemap and a payload set.
  if (existsSync(PREVIEW)) copyFileSync(PREVIEW, join(dir, 'biobuilds-preview.html'));
  writeFileSync(join(dir, 'sitemap.xml'),
                '<?xml version="1.0"?><urlset></urlset>');
  if (extraPage) writeFileSync(join(dir, extraPage.name), extraPage.html);
  return dir;
}

function run(which, dir) {
  const f = which === 'imagery' ? 'prove-biobuilds-imagery.mjs'
                                : 'prove-biobuilds-containment.mjs';
  const args = which === 'imagery'
    ? [join(dir, 'atlas-tools', f), '--root', dir]
    : [join(dir, 'atlas-tools', f)];
  try {
    return { code: 0, out: execFileSync('node', args,
      { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024, cwd: dir }) };
  } catch (e) {
    return { code: e.status === undefined ? -1 : e.status,
             out: (e.stdout || '') + (e.stderr || '') };
  }
}
const failedIds = o =>
  [...o.matchAll(/^ {2}FAIL {2}(BI\d+)/gm)].map(m => m[1]);

console.log('\nGUARD-CAPABILITY PROOF · BIOBUILDS IMAGERY');
console.log('='.repeat(74));

/* ── CONTROL ─────────────────────────────────────────────────────────── */
{
  const dir = tree();
  const r = run('imagery', dir);
  if (r.code !== 0) {
    log('  CONTROL FAILED — the suite does not pass in a disposable tree:');
    log('    ' + r.out.split('\n').filter(l => /FAIL|UNAVAILABLE/.test(l))
                   .slice(0, 5).join('\n    '));
    process.exit(1);
  }
  log('  CONTROL  the imagery suite passes in a disposable tree');
  log('-'.repeat(74));
}

const CASES = [
  { id: 'C-BI1', suite: 'imagery', expect: ['BI1', 'BI2', 'BI3'],
    why: 'the approved asset list is emptied',
    opts: { recordEdit: bb => { bb.approved_assets = []; } } },

  { id: 'C-BI3', suite: 'imagery', expect: ['BI3'],
    why: 'an approved asset is dropped from the index by the generator',
    opts: { genEdit: s => s.replace(
      '            slot["set"].append(im)',
      '            if a.get("primary"):\n                slot["set"].append(im)') } },

  { id: 'C-BI4', suite: 'imagery', expect: ['BI4'],
    why: 'a withheld asset is quietly moved into the approved list',
    opts: { recordEdit: bb => {
      const w = bb.withheld_assets[0];
      bb.approved_assets.push({ url: w.url, product_code: 'PROD-000523',
        product_name: 'BIOBUILDS Wanderlust', role: 'interior',
        primary: false, alt: 'A wall build-up detail.' }); } } },

  /* RE-AIMED. Reassigning a Serenity image to Wanderlust empties Serenity's
     index entry, so BI2 and BI6 both see it. Both are named: the defect is
     genuinely caught, and pretending only one check owns it would be a
     fiction. The suite was also made null-safe, because this mutation used to
     make BI6 throw instead of fail. */
  { id: 'C-BI6', suite: 'imagery', expect: ['BI6', 'BI2'],
    why: 'a Serenity image is assigned to Wanderlust',
    opts: { recordEdit: bb => {
      const s = bb.approved_assets.find(a => a.product_code === 'PROD-000524');
      s.product_code = 'PROD-000523'; } } },

  /* RE-AIMED, and what it taught is worth recording. Deleting the credit or
     the alt text does NOT reach BI7: the generator's own index refuses to
     emit an asset missing either, so the asset vanishes and BI1/BI3 catch it
     instead. That is the system failing closed one layer earlier than the
     test expected, which is the right behaviour -- so these two now assert
     the layer that actually fires. */
  { id: 'C-BI7', suite: 'imagery', expect: ['BI1', 'BI3'],
    why: 'the required credit is removed (the generator refuses the asset)',
    opts: { recordEdit: bb => { delete bb.required_credit; } } },

  { id: 'C-BI7b', suite: 'imagery', expect: ['BI3'],
    why: 'an approved asset loses its alt text (the generator skips it)',
    opts: { recordEdit: bb => { delete bb.approved_assets[0].alt; } } },

  /* And a DIRECT test of BI7: the asset stays indexed, but the generator
     stops attaching the supplier's caption. Nothing upstream refuses it, so
     BI7 is the only check that can see it. */
  { id: 'C-BI7c', suite: 'imagery', expect: ['BI7'],
    why: 'the generator stops attaching the supplier\u2019s caption',
    opts: { genEdit: s => s.replace(
      '                "caption": "BIOBUILDS model imagery" if org == "BIOBUILDS"\n'
      + '                           else None,',
      '                "caption": None,') } },

  { id: 'C-BI8', suite: 'imagery', expect: ['BI8'],
    why: 'alt text starts calling the imagery a photograph',
    opts: { recordEdit: bb => {
      bb.approved_assets[0].alt =
        'A photograph of the Wanderlust 48 installed in Ireland.'; } } },

  { id: 'C-BI9', suite: 'imagery', expect: ['BI9'],
    why: 'the runtime stops requiring a permitted prefix',
    opts: { plotEdit: s => s.replace(
      '    if (!im.permittedPrefix) return false;\n'
      + '    if (String(im.url).indexOf(im.permittedPrefix) !== 0) return false;',
      '    if (false) return false;') } },

  { id: 'C-BI10', suite: 'imagery', expect: ['BI10'],
    why: 'another supplier quietly gains an approved asset',
    opts: { recordEdit: (bb, rec) => {
      const other = rec.records.find(r => r.organisation_code
        && r.organisation_code !== 'ORG-000153' && r.permitted_domain);
      other.approved_assets = [{
        url: 'https://' + other.permitted_domain + '/img/a.jpg',
        product_code: 'PROD-000001', product_name: 'Something',
        role: 'exterior', primary: true, alt: 'A building.' }]; } } },

  { id: 'C-BI12', suite: 'imagery', expect: ['BI12'],
    why: 'the generator stops withholding imagery from a held product',
    opts: { genEdit: s => s.replace(
      '    if held:\n        return (None, None)',
      '    if False:\n        return (None, None)') } },

  { id: 'C-BI14', suite: 'imagery', expect: ['BI14'],
    why: 'a Garden Room product loses its authorised image',
    opts: { gardenEdit: d => {
      const p = (d.products || []).find(x => x.imagery);
      if (p) delete p.imagery.credit; } } },

  /* ── and the containment proof, which is the per-asset enforcement ── */
  { id: 'C-CONTAIN', suite: 'containment', expect: ['CONTAIN'],
    why: 'a WITHHELD asset appears on a public page',
    opts: { extraPage: { name: 'public-page.html', html:
      '<!doctype html><html><head><title>t</title></head><body>'
      + '<img src="https://www.biobuilds.com/_next/static/immutable/media/'
      + 'wall-section-3.0.26fqr4wmqyq13.jpg" alt="x">'
      + '</body></html>' } } },

  { id: 'C-CONTAIN2', suite: 'containment', expect: ['CONTAIN'],
    why: 'an unenumerated BIOBUILDS asset appears on a public page',
    opts: { extraPage: { name: 'public-page.html', html:
      '<!doctype html><html><head><title>t</title></head><body>'
      + '<img src="https://www.biobuilds.com/_next/static/immutable/media/'
      + 'never-approved.jpg" alt="x">'
      + '</body></html>' } } },

  { id: 'C-CONTAIN3', suite: 'containment', expect: ['CONTAIN'],
    why: 'the approved asset list becomes unreadable',
    opts: { recordEdit: (bb, rec) => { rec.records = 'not a list'; } } }
];

for (const c of CASES) {
  let dir;
  try { dir = tree(c.opts || {}); }
  catch (e) {
    log(`  BLIND         ${c.id}  ${c.why}`);
    log('                the tree could not be built: ' + e.message);
    broken++; continue;
  }
  const r = run(c.suite, dir);

  if (c.suite === 'containment') {
    /* The containment proof names its checks in prose, not ids, so a
       non-zero exit plus a FAIL or ERROR line is the signal. */
    const refused = r.code !== 0 && /FAIL|ERROR/.test(r.out);
    refused
      ? (log(`  PROVED        ${c.id}  ${c.why}`),
         log(`                containment refused (exit ${r.code})`), proved++)
      : (log(`  VACUOUS       ${c.id}  ${c.why}`),
         log(`                containment PASSED (exit ${r.code}). It cannot `
             + 'see this.'), broken++);
    continue;
  }

  if (r.code === 2 || /INSTRUMENT UNAVAILABLE/.test(r.out)) {
    log(`  BLIND         ${c.id}  ${c.why}`);
    log('                the suite refused: '
        + r.out.split('\n').filter(Boolean).slice(-2).join(' / ').slice(0, 130));
    broken++; continue;
  }
  if (r.code === 0) {
    log(`  VACUOUS       ${c.id}  ${c.why}`);
    log('                the suite PASSED against this defect.');
    broken++; continue;
  }
  const ids = failedIds(r.out);
  const hit = c.expect.filter(w => ids.includes(w));
  if (!hit.length) {
    log(`  MISATTRIBUTED ${c.id}  ${c.why}`);
    log(`                expected ${c.expect.join('/')}; failed was `
        + `${ids.join(',') || '(nothing named)'}`);
    broken++;
  } else {
    log(`  PROVED        ${c.id}  ${c.why}`);
    log(`                ${hit.join(', ')} failed, as required`);
    proved++;
  }
}

/* ── the real tree must be untouched ─────────────────────────────────── */
const after = {
  records: sha(RECORDS), plot: sha(PLOT), suite: sha(SUITE),
  contain: sha(CONTAIN),
  gen: sha(join(ROOT, '.github', 'scripts',
                'generate_additional_home_universe.py'))
};
const moved = Object.keys(before).filter(k => before[k] !== after[k]);

console.log('-'.repeat(74));
console.log(`${CASES.length} mutations, ${proved} proved capable, `
            + `${broken} not proved`);
console.log('the real tree was untouched by this proof: '
            + (moved.length ? 'NO — ' + moved.join(', ') : 'YES')
            + '  (' + before.records.slice(0, 12) + ')');
process.exit((broken || moved.length) ? 1 : 0);
