/**
 * GUARD-CAPABILITY PROOF — THE PROVENANCE CHECKS CAN ACTUALLY FAIL
 * ================================================================
 * P1–P11 currently run against a register with ZERO declared records, so
 * several of them have nothing real to assert yet and say so in their own
 * output. That is exactly the condition in which a guard quietly rots: it
 * reads as green, nobody notices it is inert, and by the time the first
 * record arrives the check has been broken for months.
 *
 * So every check is driven here against a SYNTHETIC register holding the
 * records that do not exist yet. Each case breaks one thing and requires the
 * named check to fail.
 *
 *   VACUOUS       the suite passed anyway — the check cannot see the defect
 *   BLIND         the suite errored or refused — it measured nothing
 *   MISATTRIBUTED something failed, but not the check that should have
 *
 * all count as failures of the PROOF. The control runs first.
 *
 * NOTHING IN THE REPOSITORY IS MUTATED. Each case gets a temporary tree with
 * copies of the register, the pages it needs, the rights manifest and the
 * asset files.
 *
 *   node atlas-tools/prove-image-provenance-capability.mjs
 *
 * Exit 0 = every check proved capable.
 */
import { readFileSync, writeFileSync, mkdtempSync, mkdirSync, copyFileSync,
         existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const GUARD = join(HERE, 'validate-image-provenance.js');
const REGISTER = join(ROOT, 'image-provenance-records.json');
const RIGHTS = join(ROOT, 'image-rights-manifest.json');
const GATE = join(HERE, 'validate-image-rights.js');
const LICENCES = join(ROOT, 'image-adaptation-licences.json');

for (const f of [GUARD, REGISTER, RIGHTS, GATE]) {
  if (!existsSync(f)) {
    console.log('\nINSTRUMENT UNAVAILABLE: ' + f + ' is missing. Nothing was '
                + 'measured.');
    process.exit(2);
  }
}

let proved = 0, broken = 0;
const log = s => console.log(s);
const sha = b => createHash('sha256').update(b).digest('hex');

/* One real asset and one real supplier, so the synthetic records describe
   things that actually exist. */
const realReg = JSON.parse(readFileSync(REGISTER, 'utf8'));
const anAsset = realReg.legacy_undeclared.find(e => /assets\/img\/.*\.jpg$/.test(e.asset));
if (!anAsset) {
  console.log('\nINSTRUMENT UNAVAILABLE: no jpg asset in the backlog to build '
              + 'synthetic records around.');
  process.exit(2);
}
const rightsDoc = JSON.parse(readFileSync(RIGHTS, 'utf8'));
const rightsRows = Array.isArray(rightsDoc) ? rightsDoc
  : Object.values(rightsDoc).find(v => Array.isArray(v) && v[0]
                                       && typeof v[0] === 'object');
const supplier = rightsRows.find(r => r.organisation_code
                                      && r.atlas_permission_ref);
if (!supplier) {
  console.log('\nINSTRUMENT UNAVAILABLE: no rights row with both an '
              + 'organisation_code and a permission ref.');
  process.exit(2);
}

/* ── the synthetic records P1–P11 need in order to have work to do ────── */
const AI_LABEL = realReg.labels.AI_ILLUSTRATION;
function syntheticRegister() {
  const reg = JSON.parse(JSON.stringify(realReg));
  reg.legacy_undeclared = reg.legacy_undeclared.filter(e => e.asset !== anAsset.asset);
  reg.records = [
    {
      asset: anAsset.asset,
      sha256: anAsset.sha256,
      class: 'AI_ILLUSTRATION',
      label: AI_LABEL,
      generated: { tool: 'An image model', date: '2026-10-03' },
      prompt: 'An Irish suburban back garden in soft afternoon light, with a '
              + 'generic timber garden building and planting. No branding.',
      reference_inputs: [],
      depicts_named_product: false,
      depicts_named_organisation: false,
      human_review: {
        reviewer: 'Colin MacAulay', date: '2026-10-03',
        attests: 'Checked against the supplier imagery PlotNua holds. '
                 + 'Reproduces no supplier photograph and resembles no '
                 + 'identifiable product design.'
      },
      permitted_surfaces: ['discovery']
    }
  ];
  return reg;
}

/* The page that references the synthetic AI asset, carrying its label so the
   control passes P8. */
function pageFor(assetPath, { label = AI_LABEL, supplierName = null } = {}) {
  return `<!doctype html><html><head><title>t</title></head><body>
<figure>
  <img src="${assetPath}" width="100" height="100" alt="A garden.">
  <figcaption>${label}</figcaption>
</figure>
${supplierName ? `<p>Supplied by ${supplierName}.</p>` : ''}
</body></html>`;
}

/* ── DERIVATIVE FIXTURES (P12, SEO Phase 1b, 16 Oct 2026) ─────────────
   One real derivative and its real source, copied into the case tree, on a
   page that carries the AI figure (so P8/P9 stay satisfied) AND the
   <picture> with the source <img> as its fallback. */
const realDeriv = (realReg.derivatives || [])[0] || null;
function derivPage({ withSource = true, extra = '' } = {}) {
  const d = realDeriv;
  return `<!doctype html><html><head><title>t</title></head><body>
<figure><img src="${anAsset.asset}" width="100" height="100" alt="A garden.">
<figcaption>${AI_LABEL}</figcaption></figure>
<picture><source type="image/webp" srcset="${d.asset} ${d.pixels[0]}w">
${withSource ? `<img src="${d.derived_from.asset}" alt="Hero.">` : ''}</picture>
${extra}</body></html>`;
}
function derivOpts({ regEdit = null, withSource = true, bytes = null } = {}) {
  const d = realDeriv;
  return {
    regEdit, rawPage: derivPage({ withSource }),
    extraFiles: {
      [d.asset]: bytes || readFileSync(join(ROOT, d.asset)),
      [d.derived_from.asset]: readFileSync(join(ROOT, d.derived_from.asset)),
    },
  };
}
const dEdit = (fn) => (r) => fn(r.derivatives.find(x => x.asset === realDeriv.asset), r);
const srcEntry = (r) => [...r.records, ...r.legacy_undeclared]
  .find(e => e.asset === realDeriv.derived_from.asset);

function tree({ regEdit = null, pageOpts = {}, gateEdit = null,
                omitRights = false, regRaw = null, rawPage = null,
                extraFiles = null } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'pn-prov-'));
  mkdirSync(join(dir, 'atlas-tools'), { recursive: true });
  mkdirSync(join(dir, 'assets', 'img'), { recursive: true });

  const reg = syntheticRegister();
  if (regEdit) regEdit(reg);
  writeFileSync(join(dir, 'image-provenance-records.json'),
                regRaw !== null ? regRaw : JSON.stringify(reg, null, 2));

  // Only the one asset the synthetic records describe, so the tree is small
  // and P1 has a bounded set to check.
  const src = join(ROOT, anAsset.asset);
  if (existsSync(src)) copyFileSync(src, join(dir, anAsset.asset));
  writeFileSync(join(dir, 'page.html'),
                rawPage !== null ? rawPage : pageFor(anAsset.asset, pageOpts));
  /* Extra files let a case plant an image through a mechanism that lives
     outside the main page -- a web manifest, or a page in a subdirectory,
     neither of which the first version of the guard ever looked at. */
  if (extraFiles) {
    for (const [rel, content] of Object.entries(extraFiles)) {
      const full = join(dir, rel);
      mkdirSync(dirname(full), { recursive: true });
      writeFileSync(full, content);
    }
  }

  if (!omitRights) copyFileSync(RIGHTS, join(dir, 'image-rights-manifest.json'));
  /* H2, 20 Oct 2026: the real register now carries a staged composite bound
     to an adaptation licence. The licence travels with the register, or the
     control would (correctly) fail for a missing binding. */
  if (existsSync(LICENCES)) copyFileSync(LICENCES, join(dir, 'image-adaptation-licences.json'));
  let gate = readFileSync(GATE, 'utf8');
  if (gateEdit) gate = gateEdit(gate);
  writeFileSync(join(dir, 'atlas-tools', 'validate-image-rights.js'), gate);
  copyFileSync(GUARD, join(dir, 'atlas-tools', 'validate-image-provenance.js'));
  return dir;
}

function run(dir) {
  try {
    return { code: 0, out: execFileSync('node',
      [join(dir, 'atlas-tools', 'validate-image-provenance.js'),
       '--root', dir], { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 }) };
  } catch (e) {
    return { code: e.status === undefined ? -1 : e.status,
             out: (e.stdout || '') + (e.stderr || '') };
  }
}
const failedIds = o =>
  [...o.matchAll(/^ {2}FAIL {2}(P\d+)/gm)].map(m => m[1]);

console.log('\nGUARD-CAPABILITY PROOF · IMAGE PROVENANCE');
console.log('='.repeat(74));

/* ── CONTROL ─────────────────────────────────────────────────────────── */
{
  const r = run(tree());
  if (r.code !== 0) {
    log('  CONTROL FAILED — the synthetic register does not pass clean:');
    log('    ' + r.out.split('\n').filter(l => /FAIL|UNAVAILABLE/.test(l))
                   .slice(0, 6).join('\n    '));
    log('  Every result after this would be meaningless. Stopping.');
    process.exit(1);
  }
  const live = (r.out.match(/the check is live/g) || []).length;
  log('  CONTROL  the synthetic register passes, with real records for every '
      + 'check');
  log(`           (${live} check(s) still reported as having nothing to test)`);
  log('-'.repeat(74));
}

const CASES = [
  { id: 'C-P1', expect: ['P1'],
    why: 'a NEW undeclared image appears on a published page',
    opts: { regEdit: r => {
      /* The ratchet. The asset is dropped from BOTH the records and the
         backlog, which is what a newly added file looks like. */
      r.records = []; r.legacy_undeclared = []; } } },

  { id: 'C-P2', expect: ['P2'],
    why: 'a declared asset’s bytes no longer match its recorded hash',
    opts: { regEdit: r => { r.records[0].sha256 = sha(Buffer.from('other')); } } },

  { id: 'C-P3', expect: ['P3'],
    why: 'a record carries an unrecognised class',
    opts: { regEdit: r => { r.records[0].class = 'PROBABLY_FINE'; } } },

  { id: 'C-P3b', expect: ['P3'],
    why: 'NO_IMAGE is used as an asset class rather than a slot state',
    opts: { regEdit: r => { r.records[0].class = 'NO_IMAGE'; } } },

  { id: 'C-P4', expect: ['P4'],
    why: 'a SUPPLIER_IMAGE points at a grant that does not exist',
    opts: { regEdit: r => {
      r.records[0] = { asset: anAsset.asset, sha256: anAsset.sha256,
        class: 'SUPPLIER_IMAGE',
        rights_ref: { organisation_code: 'ORG-000000',
                      atlas_permission_ref: 'NOT-A-REAL-REF' } }; },
      pageOpts: { label: 'Supplier photograph' } } },

  { id: 'C-P5', expect: ['P5'],
    why: 'an AI illustration has no prompt recorded',
    opts: { regEdit: r => { delete r.records[0].prompt; } } },

  { id: 'C-P5b', expect: ['P5'],
    why: 'reference_inputs is absent rather than an explicit empty list',
    opts: { regEdit: r => { delete r.records[0].reference_inputs; } } },

  { id: 'C-P5c', expect: ['P5'],
    why: 'the human review has no named reviewer',
    opts: { regEdit: r => { delete r.records[0].human_review.reviewer; } } },

  { id: 'C-P6', expect: ['P6'],
    why: 'the prompt names a real supplier',
    opts: { regEdit: r => {
      r.records[0].prompt = 'A garden building in the style of '
        + supplier.organisation_name + ', photographic.'; } } },

  { id: 'C-P6b', expect: ['P6'],
    why: 'a reference input comes from a supplier’s own domain',
    opts: { regEdit: r => {
      r.records[0].reference_inputs =
        ['https://' + supplier.permitted_domain + '/product/hero.jpg']; } } },

  { id: 'C-P6c', expect: ['P6'],
    why: 'the record admits it depicts a named product',
    opts: { regEdit: r => { r.records[0].depicts_named_product = true; } } },

  { id: 'C-P7', expect: ['P7'],
    why: 'an AI illustration is permitted onto a supplier product card',
    opts: { regEdit: r => { r.records[0].permitted_surfaces = ['product-card']; } } },

  { id: 'C-P7b', expect: ['P7'],
    why: 'product-card is added to the guard’s own permitted vocabulary',
    opts: { regEdit: r => { r.records[0].permitted_surfaces = ['product-card']; } },
    guardEdit: s => s.replace(
      "const PERMITTED_SURFACES = ['discovery', 'library-card', 'homepage',",
      "const PERMITTED_SURFACES = ['product-card', 'discovery', 'library-card', 'homepage',") },

  { id: 'C-P8', expect: ['P8'],
    why: 'the published caption loses the AI label',
    opts: { pageOpts: { label: 'A garden' } } },

  { id: 'C-P9', expect: ['P9'],
    why: 'a declared record describes an asset no page references',
    opts: { regEdit: r => { r.records[0].asset = 'assets/img/not-referenced.jpg'; } } },

  { id: 'C-P10', expect: ['P10'],
    why: 'an AI illustration is captioned beside a named supplier',
    opts: { pageOpts: { supplierName: supplier.organisation_name } } },

  { id: 'C-P11', expect: ['P11'],
    why: 'the rights gate starts reading the provenance register',
    opts: { gateEdit: s => s.replace(
      'const FIRST_PARTY = new Set(',
      "const PROVENANCE = 'image-provenance-records.json';\n"
      + 'const FIRST_PARTY = new Set(') } },

  { id: 'C-P11b', expect: ['P11'],
    why: 'a provenance record claims a permission of its own',
    opts: { regEdit: r => {
      r.records[0].permission_outcome = 'Granted — Founder Confirmed';
      r.records[0].permitted_domain = 'example.com'; } } },

  /* ── THE NEWLY CLOSED LOADERS ──────────────────────────────────────────
     A coverage audit on 11 October 2026 found four mechanisms IN ACTUAL USE
     that the guard had never scanned, and several more that nothing uses
     yet. Widening a guard without proving the new coverage bites just moves
     the trust somewhere less visible, so each case below plants an
     UNDECLARED image through one mechanism and requires P1 to refuse.

     The declared asset is kept off these pages entirely, so the only thing
     P1 can be reacting to is the planted one. */
  { id: 'C-LOAD-icon', expect: ['P1'],
    why: 'undeclared image via <link rel="icon">  (122 real uses)',
    opts: { rawPage: '<!doctype html><html><head><title>t</title>'
      + '<link rel="icon" href="/undeclared-favicon.png">'
      + '</head><body></body></html>' } },

  { id: 'C-LOAD-appletouch', expect: ['P1'],
    why: 'undeclared image via <link rel="apple-touch-icon">',
    opts: { rawPage: '<!doctype html><html><head><title>t</title>'
      + '<link rel="apple-touch-icon" href="/undeclared-touch.png">'
      + '</head><body></body></html>' } },

  { id: 'C-LOAD-twitter', expect: ['P1'],
    why: 'undeclared image via twitter:image on our own origin  (23 real uses)',
    opts: { rawPage: '<!doctype html><html><head><title>t</title>'
      + '<meta name="twitter:image" '
      + 'content="https://plotnua.ie/assets/og/undeclared-card.png">'
      + '</head><body></body></html>' } },

  { id: 'C-LOAD-manifest', expect: ['P1'],
    why: 'undeclared image via the web manifest, which is not HTML at all',
    opts: { rawPage: '<!doctype html><html><head><title>t</title></head>'
      + '<body></body></html>',
      extraFiles: { 'site.webmanifest': JSON.stringify(
        { name: 'x', icons: [{ src: '/undeclared-chrome-192.png' }] }) } } },

  { id: 'C-LOAD-subdir', expect: ['P1'],
    why: 'undeclared image on a page below the root  (12 real pages)',
    opts: { rawPage: '<!doctype html><html><head><title>t</title></head>'
      + '<body></body></html>',
      extraFiles: { 'preview-system/template.html':
        '<!doctype html><html><head><title>t</title></head><body>'
        + '<img src="assets/img/undeclared-in-subdir.png" alt="x">'
        + '</body></html>' } } },

  { id: 'C-LOAD-css', expect: ['P1'],
    why: 'undeclared image via a CSS background url()',
    opts: { rawPage: '<!doctype html><html><head><title>t</title>'
      + '<style>.hero{background-image:url("/undeclared-bg.jpg")}</style>'
      + '</head><body></body></html>' } },

  { id: 'C-LOAD-imgsrcset', expect: ['P1'],
    why: 'undeclared image via <img srcset>  (pre-emptive)',
    opts: { rawPage: '<!doctype html><html><head><title>t</title></head><body>'
      + '<img srcset="/undeclared-1x.png 1x, /undeclared-2x.png 2x" alt="x">'
      + '</body></html>' } },

  { id: 'C-LOAD-poster', expect: ['P1'],
    why: 'undeclared image via <video poster>  (pre-emptive)',
    opts: { rawPage: '<!doctype html><html><head><title>t</title></head><body>'
      + '<video poster="/undeclared-poster.jpg"></video></body></html>' } },

  { id: 'C-LOAD-imageset', expect: ['P1'],
    why: 'undeclared image via CSS image-set()  (pre-emptive)',
    opts: { rawPage: '<!doctype html><html><head><title>t</title>'
      + '<style>.h{background:image-set("/undeclared-set.webp" 1x)}</style>'
      + '</head><body></body></html>' } },

  { id: 'C-LOAD-jssrc', expect: ['P1'],
    why: 'undeclared image via a JavaScript .src assignment',
    opts: { rawPage: '<!doctype html><html><head><title>t</title></head><body>'
      + '<scr' + 'ipt>el.src = "/undeclared-js.png";</scr' + 'ipt>'
      + '</body></html>' } },

  { id: 'C-LOAD-svgimage', expect: ['P1'],
    why: 'undeclared image via SVG <image href>  (pre-emptive)',
    opts: { rawPage: '<!doctype html><html><head><title>t</title></head><body>'
      + '<svg><image href="/undeclared-svg-image.png"/></svg>'
      + '</body></html>' } },

  { id: 'C-LOAD-datasrc', expect: ['P1'],
    why: 'undeclared image via a data-src lazy attribute  (pre-emptive)',
    opts: { rawPage: '<!doctype html><html><head><title>t</title></head><body>'
      + '<img data-src="/undeclared-lazy.png" alt="x"></body></html>' } },

  /* P12 · HASH-BOUND DERIVATIVES. The control must PASS; every narrowing
     condition must be seen by P12 (or by P1, for the ratchet itself). */
  { id: 'C-P12-control', mustPassOpts: () => derivOpts(), expect: ['(accepts)'],
    why: 'a recorded WebP derivative shown with its source as fallback is accepted' },
  { id: 'C-P12-ratchet', expect: ['P1'],
    why: 'a WebP that is NOT recorded as a derivative is a new undeclared image',
    optsFn: () => derivOpts({ regEdit: r => { r.derivatives = []; } }) },
  { id: 'C-P12-stale', expect: ['P12'],
    why: 'the source changed after the derivative was made',
    optsFn: () => derivOpts({ regEdit: dEdit(d => { d.derived_from.sha256 = sha(Buffer.from('old')); }) }) },
  { id: 'C-P12-crop', expect: ['P12'],
    why: 'the derivative does not keep the source aspect ratio (a crop)',
    optsFn: () => derivOpts({ regEdit: r => { srcEntry(r).pixels = [1000, 1000]; } }) },
  { id: 'C-P12-upscale', expect: ['P12'],
    why: 'the derivative is wider than its source (an upscale)',
    optsFn: () => derivOpts({ regEdit: r => {
      const s = srcEntry(r); s.pixels = [Math.round(s.pixels[0] / 4), Math.round(s.pixels[1] / 4)]; } }) },
  { id: 'C-P12-nofallback', expect: ['P12'],
    why: 'the derivative appears on a page without its source',
    optsFn: () => derivOpts({ withSource: false }) },
  { id: 'C-P12-bytes', expect: ['P12'],
    why: 'the derivative bytes no longer match its hash',
    optsFn: () => derivOpts({ bytes: Buffer.concat([readFileSync(join(ROOT, realDeriv.asset)), Buffer.from('x')]) }) },
  { id: 'C-P12-declares', expect: ['P12'],
    why: 'a derivative tries to declare a class of its own',
    optsFn: () => derivOpts({ regEdit: dEdit(d => { d.class = 'AI_ILLUSTRATION'; }) }) },
  { id: 'C-P12-method', expect: ['P12'],
    why: 'a derivative made by a method outside the closed vocabulary',
    optsFn: () => derivOpts({ regEdit: dEdit(d => { d.method = 'retouch'; }) }) },
  { id: 'C-P12-hold', expect: ['P12'],
    why: 'a derivative of a source that is on provenance hold',
    optsFn: () => derivOpts({ regEdit: r => {
      r.derivative_holds = [{ source: realDeriv.derived_from.asset, reason: 'test' }]; } }) },
  { id: 'C-P12-credclaim', expect: ['P12'],
    why: 'a derivative claims to carry a signed credential',
    optsFn: () => derivOpts({ regEdit: dEdit(d => {
      d.content_credentials = { derivative_embeds_c2pa: true }; }) }) },
  { id: 'C-P12-chain', expect: ['P12'],
    why: 'a derivative of a derivative',
    optsFn: () => derivOpts({ regEdit: r => {
      const other = r.derivatives.find(x => x.asset !== realDeriv.asset);
      const d = r.derivatives.find(x => x.asset === realDeriv.asset);
      d.derived_from = { asset: other.asset, sha256: other.sha256 }; } }) },

  /* THE CONTROL FOR THE WIDENING. A DECLARED image arriving through one of
     the newly covered mechanisms must still PASS. A guard that refuses
     everything is not a guard either, and this is the case that catches an
     over-broad regex. */
  { id: 'C-LOAD-control', mustPass: true, expect: ['(accepts)'],
    why: 'a DECLARED image via <link rel="icon"> is accepted, not refused' },

  /* And the instrument itself must refuse rather than pass when it cannot
     establish the facts. */
  { id: 'C-REFUSE', expect: ['REFUSE'],
    why: 'the register is missing entirely',
    opts: { regRaw: '' }, wantRefusal: true },

  { id: 'C-REFUSE2', expect: ['REFUSE'],
    why: 'the register is not valid JSON',
    opts: { regRaw: '{ not json' }, wantRefusal: true }
];

for (const c of CASES) {
  let dir;
  if ((c.optsFn || c.mustPassOpts) && !realDeriv) {
    log(`  BLIND         ${c.id}  ${c.why}`);
    log('                the register holds no derivative to build the case on');
    broken++;
    continue;
  }
  try {
    dir = tree(c.mustPassOpts ? c.mustPassOpts() : c.optsFn ? c.optsFn() : (c.opts || {}));
    if (c.guardEdit) {
      const p = join(dir, 'atlas-tools', 'validate-image-provenance.js');
      const before = readFileSync(p, 'utf8');
      const after = c.guardEdit(before);
      if (after === before) {
        log(`  BLIND         ${c.id}  ${c.why}`);
        log('                the guard mutation changed nothing — its '
            + 'target has moved');
        broken++;
        continue;
      }
      writeFileSync(p, after);
    }
  } catch (e) {
    log(`  BLIND         ${c.id}  ${c.why}`);
    log('                the tree could not be built: ' + e.message);
    broken++;
    continue;
  }
  const r = run(dir);

  if (c.mustPassOpts) {
    r.code === 0
      ? (log(`  PROVED        ${c.id}  ${c.why}`),
         log('                the guard ACCEPTED it \u2014 the exemption is usable'), proved++)
      : (log(`  VACUOUS       ${c.id}  ${c.why}`),
         log('                the guard refused a valid derivative (exit ' + r.code + ')'),
         log('                ' + r.out.split('\n').filter(l => /FAIL|UNAVAILABLE/.test(l)).join('\n                ')),
         broken++);
    continue;
  }

  if (c.mustPass) {
    /* CORRECTED. The first version referenced the DECLARED AI_ILLUSTRATION
       through the icon mechanism, and the guard refused -- correctly, because
       P8 requires a declared AI illustration to carry its visible label and a
       bare <link rel="icon"> carries no caption. The guard was right and the
       control was wrong.
       It now references an ENUMERATED LEGACY asset, which is the ordinary
       case for 110 of 110 assets today: accounted for, so P1 accepts it, and
       unlabelled, which is exactly what an undeclared asset should be. */
    const legacyAsset = realReg.legacy_undeclared
      .find(e => e.asset !== anAsset.asset && /\.(png|ico)$/i.test(e.asset));
    if (!legacyAsset) {
      log(`  BLIND         ${c.id}  ${c.why}`);
      log('                no second legacy asset to build the control on');
      broken++;
      continue;
    }
    /* BOTH assets on the page. The synthetic register declares the AI
       illustration, so P8 wants its label and P9 wants it referenced -- a
       page carrying only the legacy icon trips P9, which is the guard being
       right about a different thing. The control therefore satisfies the
       declared record properly AND adds the legacy asset through the newly
       covered icon mechanism. Only the widening is under test. */
    const dir2 = tree({ rawPage:
      '<!doctype html><html><head><title>t</title>'
      + '<link rel="icon" href="/' + legacyAsset.asset + '">'
      + '</head><body><figure>'
      + '<img src="' + anAsset.asset + '" width="10" height="10" alt="A garden.">'
      + '<figcaption>' + AI_LABEL + '</figcaption>'
      + '</figure></body></html>' });
    /* And the legacy asset's BYTES, or P2 refuses it as missing on disk --
       which it was, and which is P2 doing its job rather than the widening
       being wrong. */
    const legacySrc = join(ROOT, legacyAsset.asset);
    if (existsSync(legacySrc)) {
      mkdirSync(dirname(join(dir2, legacyAsset.asset)), { recursive: true });
      copyFileSync(legacySrc, join(dir2, legacyAsset.asset));
    }
    const rr = run(dir2);
    rr.code === 0
      ? (log(`  PROVED        ${c.id}  ${c.why}`),
         log('                the guard ACCEPTED it \u2014 the widening is not '
             + 'over-broad'), proved++)
      : (log(`  VACUOUS       ${c.id}  ${c.why}`),
         log('                the guard refused a DECLARED image (exit '
             + rr.code + '); the widening is over-broad'),
         log('                ' + rr.out.split('\n')
               .filter(l => /FAIL|UNAVAILABLE/.test(l)).join('\n                ')),
         broken++);
    continue;
  }

  if (c.wantRefusal) {
    (r.code === 2 && /INSTRUMENT UNAVAILABLE/.test(r.out))
      ? (log(`  PROVED        ${c.id}  ${c.why}`),
         log('                the guard REFUSED (exit 2) rather than passing'),
         proved++)
      : (log(`  VACUOUS       ${c.id}  ${c.why}`),
         log(`                exit ${r.code}; a guard that passes when it `
             + 'cannot read its own register is not a guard'),
         broken++);
    continue;
  }

  if (r.code === 2 || /INSTRUMENT UNAVAILABLE/.test(r.out)) {
    log(`  BLIND         ${c.id}  ${c.why}`);
    log('                the guard refused: '
        + r.out.split('\n').filter(Boolean).slice(-2).join(' / ').slice(0, 130));
    broken++;
    continue;
  }
  if (r.code === 0) {
    log(`  VACUOUS       ${c.id}  ${c.why}`);
    log('                the guard PASSED against this defect. It cannot see '
        + 'it.');
    broken++;
    continue;
  }
  const ids = failedIds(r.out);
  const hit = c.expect.filter(w => ids.includes(w));
  if (!hit.length) {
    log(`  MISATTRIBUTED ${c.id}  ${c.why}`);
    log(`                expected ${c.expect.join('/')}; what failed was `
        + `${ids.join(',') || '(nothing named)'}`);
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
