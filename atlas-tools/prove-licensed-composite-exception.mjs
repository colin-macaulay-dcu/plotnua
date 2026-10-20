/**
 * PROVE THE LICENSED-PHOTOGRAPHY EXCEPTION IS NARROW · X1–X33 (+X12b, X12c, X12d)
 * ===========================================================
 * H2, 20 Oct 2026. The founder approved ONE exception to the provenance
 * guard's anti-laundering checks:
 *
 *   "a supplier name may sit beside the illustration ONLY as the required
 *    credit of a granted, modification-permitting photo record bound to
 *    that asset."
 *
 * An exception nobody has seen refuse is a hole. So every condition that
 * makes it narrow is broken here, one at a time, in a temporary tree, and the
 * named check must fail. The controls run first: the REAL staged L6
 * composite must pass, and so must the same composite once published with
 * its credit -- otherwise every refusal below would prove nothing.
 *
 *   VACUOUS       the guard passed anyway: it cannot see the defect
 *   BLIND         the guard could not run (exit 2): it measured nothing
 *   MISATTRIBUTED something failed, but not the check that should have
 *
 * all count as failures of THIS proof. NOTHING IN THE REPOSITORY IS
 * MUTATED; the real register, manifest and guard are hashed before and after.
 *
 *   node atlas-tools/prove-licensed-composite-exception.mjs
 *
 * Exit 0 = every case proved. Exit 1 = a case not proved. Exit 2 = the
 * instrument could not run.
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
const GATE = join(HERE, 'validate-image-rights.js');
const REGISTER = join(ROOT, 'image-provenance-records.json');
const RIGHTS = join(ROOT, 'image-rights-manifest.json');
const LICENCES = join(ROOT, 'image-adaptation-licences.json');
const sha = b => createHash('sha256').update(b).digest('hex');

for (const f of [GUARD, GATE, REGISTER, RIGHTS, LICENCES]) {
  if (!existsSync(f)) {
    console.log('\nINSTRUMENT UNAVAILABLE: ' + f + ' is missing. Nothing was measured.');
    process.exit(2);
  }
}
const before = [GUARD, GATE, REGISTER, RIGHTS, LICENCES].map(f => sha(readFileSync(f)));

const realReg = JSON.parse(readFileSync(REGISTER, 'utf8'));
const realRights = JSON.parse(readFileSync(RIGHTS, 'utf8'));
const realLicences = JSON.parse(readFileSync(LICENCES, 'utf8'));
const L6 = (realReg.staged_composites || []).find(s => s.composite_id === 'possibility-reveal-L6');
const TIMBERIN = realLicences.licences.find(r => r.atlas_permission_ref === 'L6-TIMBERIN-TWO-PHOTOS-20261019');
const OTHER = realRights.rows.find(r => r.organisation_code && r.atlas_permission_ref
                                         && r !== TIMBERIN && r.permitted_domain);
const anAsset = realReg.legacy_undeclared.find(e => /assets\/img\/.*\.jpg$/.test(e.asset)
                                                   && existsSync(join(ROOT, e.asset)));
if (!L6 || !TIMBERIN || !OTHER || !anAsset) {
  console.log('\nINSTRUMENT UNAVAILABLE: the staged L6 composite, the TimberIN grant, a '
              + 'second supplier row or a jpg asset is missing. Nothing was measured.');
  process.exit(2);
}
const CREDIT = TIMBERIN.required_credit;
const AI_LABEL = realReg.labels.AI_ILLUSTRATION;
const clone = o => JSON.parse(JSON.stringify(o));

/* A page carrying the published composite. The credit sits in the caption,
   as H3 would place it. */
function page({ credit = CREDIT, extra = '', asset = anAsset.asset } = {}) {
  return `<!doctype html><html><head><title>t</title></head><body>
<figure><img src="${asset}" width="100" height="100" alt="A garden.">
<figcaption>${AI_LABEL}. ${credit ? `<a href="https://www.timberin.com/">${credit}</a>` : ''}</figcaption></figure>
${extra}</body></html>`;
}

/* The staged composite, published: moved to records with a real asset. */
function publish(reg) {
  const s = reg.staged_composites.find(x => x.composite_id === L6.composite_id);
  reg.staged_composites = reg.staged_composites.filter(x => x !== s);
  const rec = clone(s);
  delete rec.status; delete rec.master;
  Object.assign(rec, { asset: anAsset.asset, sha256: anAsset.sha256,
                       permitted_surfaces: ['homepage'] });
  reg.legacy_undeclared = reg.legacy_undeclared.filter(e => e.asset !== anAsset.asset);
  reg.records.push(rec);
  return rec;
}

function tree({ regEdit = null, rightsEdit = null, published = false,
                pageOpts = {}, rawPage = null } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'pn-lpx-'));
  mkdirSync(join(dir, 'atlas-tools'), { recursive: true });
  mkdirSync(join(dir, dirname(anAsset.asset)), { recursive: true });
  const reg = clone(realReg);
  /* Only the one asset exists in this tree; the nine Reveal records and the
     rest of the backlog describe files that are not here, so they go. */
  reg.records = []; reg.derivatives = []; reg.derivative_holds = [];
  reg.legacy_undeclared = reg.legacy_undeclared.filter(e => e.asset === anAsset.asset);
  if (published) publish(reg);
  if (regEdit) regEdit(reg);
  writeFileSync(join(dir, 'image-provenance-records.json'), JSON.stringify(reg, null, 2));
  writeFileSync(join(dir, 'image-rights-manifest.json'), JSON.stringify(realRights, null, 2));
  const lic = clone(realLicences);
  if (rightsEdit) rightsEdit(lic.licences.find(r => r.atlas_permission_ref === TIMBERIN.atlas_permission_ref), lic);
  writeFileSync(join(dir, 'image-adaptation-licences.json'), JSON.stringify(lic, null, 2));
  copyFileSync(join(ROOT, anAsset.asset), join(dir, anAsset.asset));
  writeFileSync(join(dir, 'page.html'), rawPage !== null ? rawPage
    : published ? page(pageOpts)
    : `<!doctype html><html><head><title>t</title></head><body>
       <img src="${anAsset.asset}" alt="x"></body></html>`);
  copyFileSync(GATE, join(dir, 'atlas-tools', 'validate-image-rights.js'));
  copyFileSync(GUARD, join(dir, 'atlas-tools', 'validate-image-provenance.js'));
  return dir;
}
function run(dir) {
  try {
    return { code: 0, out: execFileSync('node',
      [join(dir, 'atlas-tools', 'validate-image-provenance.js'), '--root', dir],
      { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 }) };
  } catch (e) {
    return { code: e.status === undefined ? -1 : e.status,
             out: (e.stdout || '') + (e.stderr || '') };
  }
}
const failedIds = o => [...o.matchAll(/^ {2}FAIL {2}(P\d+)/gm)].map(m => m[1]);
const staged = r => r.staged_composites.find(x => x.composite_id === L6.composite_id);
const pub = r => r.records.find(x => x.composite_id === L6.composite_id);

console.log('\nPROOF · THE LICENSED-PHOTOGRAPHY EXCEPTION (P6 / P10 / P13)');
console.log('='.repeat(74));

let proved = 0, broken = 0;
/* ── CONTROLS ─────────────────────────────────────────────────────────── */
for (const [name, opts] of [['CONTROL-STAGED', {}],
                            ['CONTROL-PUBLISHED', { published: true }]]) {
  const r = run(tree(opts));
  if (r.code !== 0) {
    console.log(`  ${name} FAILED: the real composite does not pass clean:`);
    console.log('    ' + r.out.split('\n').filter(l => /FAIL|UNAVAILABLE/.test(l)).join('\n    '));
    console.log('  Every result after this would be meaningless. Stopping.');
    process.exit(1);
  }
  console.log(`  ${name.padEnd(18)} passes: the exception admits the real L6 composite`
              + (opts.published ? ' published with its credit' : ' as staged'));
}
console.log('-'.repeat(74));

const W = 'Withdrawn / Superseded';
const CASES = [
  /* ── the grant must be live, modification-permitting and bound ─────── */
  { id: 'X1', expect: ['P6', 'P13'], why: 'the TimberIN grant is withdrawn',
    opts: { rightsEdit: r => { r.permission_outcome = W; } } },
  { id: 'X2', expect: ['P6', 'P13'], why: 'the grant carries a withdrawal date',
    opts: { rightsEdit: r => { r.withdrawal_effective_at = '2026-10-21'; } } },
  { id: 'X3', expect: ['P6', 'P13'], why: 'the grant does not permit modification',
    opts: { rightsEdit: r => { r.modification_permitted = false; } } },
  { id: 'X4', expect: ['P6', 'P13'], why: '"modification_permitted" is merely truthy, not true',
    opts: { rightsEdit: r => { r.modification_permitted = 'yes'; } } },
  { id: 'X5', expect: ['P6', 'P13'], why: 'the grant has no required credit',
    opts: { rightsEdit: r => { delete r.required_credit; } } },
  { id: 'X6', expect: ['P6', 'P13'], why: 'a source photograph is not enumerated in the grant',
    opts: { rightsEdit: r => { r.approved_assets[1].sha256 = sha('another photo'); } } },
  { id: 'X7', expect: ['P6', 'P13'], why: 'a source is bound to a different composite',
    opts: { rightsEdit: r => { r.approved_assets[0].bound_composite = 'some-other-image'; } } },
  { id: 'X8', expect: ['P6', 'P13'], why: 'a source is granted for hot-linking, not adaptation',
    opts: { rightsEdit: r => { r.approved_assets[0].use = 'hotlink-unmodified'; } } },
  { id: 'X9', expect: ['P6', 'P13'], why: 'the rights_ref points at no grant',
    opts: { regEdit: r => { staged(r).licensed_photographic_elements[0].rights_ref.atlas_permission_ref = 'NOT-A-REF'; } } },
  { id: 'X10', expect: ['P6', 'P13'], why: 'the elements bind to two different grants',
    opts: { regEdit: r => { staged(r).licensed_photographic_elements[1].rights_ref = {
      organisation_code: OTHER.organisation_code, atlas_permission_ref: OTHER.atlas_permission_ref }; } } },
  { id: 'X11', expect: ['P6', 'P13'], why: 'two records claim the same composite_id',
    opts: { regEdit: r => { const t = clone(staged(r)); r.staged_composites.push(t); } } },
  { id: 'X12b', expect: ['P6', 'P13'], why: 'the licence has no evidence reference',
    opts: { rightsEdit: r => { delete r.evidence_ref; } } },
  { id: 'X12d', expect: ['P6', 'P13'], why: 'the evidence reference is free text, not a PN-EVID reference',
    opts: { rightsEdit: r => { r.evidence_ref = 'see the email from TimberIN'; } } },
  { id: 'X12c', expect: ['P6', 'P13'], why: 'the licence file holds no licence at all',
    opts: { rightsEdit: (r, lic) => { lic.licences = []; } } },
  { id: 'X12', expect: ['P6', 'P13'], why: 'licensed_photographic_elements is an empty list',
    opts: { regEdit: r => { staged(r).licensed_photographic_elements = []; } } },

  /* ── what the exception NEVER relaxes ──────────────────────────────── */
  { id: 'X13', expect: ['P6'], why: 'the prompt names the bound supplier, binding intact',
    opts: { regEdit: r => { staged(r).prompt += ' Make it look like a ' + TIMBERIN.organisation_name + ' tub.'; } } },
  { id: 'X14', expect: ['P6'], why: 'an extra reference input from another supplier’s domain',
    opts: { regEdit: r => { staged(r).reference_inputs.push('https://' + OTHER.permitted_domain + '/hero.jpg'); } } },
  { id: 'X15', expect: ['P6'], why: 'an extra, un-enumerated image from the bound supplier’s own domain',
    opts: { regEdit: r => { staged(r).reference_inputs.push('https://' + TIMBERIN.organisation_domain + '/gallery/tub-3.jpg'); } } },
  { id: 'X16', expect: ['P6'], why: 'depicts_named_organisation is set true',
    opts: { regEdit: r => { staged(r).depicts_named_organisation = true; } } },
  { id: 'X17', expect: ['P6'], why: 'the binding is removed but the record still depicts a named product',
    opts: { regEdit: r => { delete staged(r).licensed_photographic_elements;
                            staged(r).reference_inputs = []; } } },
  { id: 'X18', expect: ['P6'], why: 'the binding is removed but the supplier photographs are still inputs',
    opts: { regEdit: r => { delete staged(r).licensed_photographic_elements;
                            staged(r).depicts_named_product = false; } } },
  { id: 'X19', expect: ['P6'], why: 'an ORDINARY AI record lists a TimberIN photograph as an input',
    opts: { published: true, regEdit: r => {
      const p = pub(r); delete p.licensed_photographic_elements; delete p.composite_id;
      p.depicts_named_product = false;
      p.reference_inputs = ['sha256 ' + TIMBERIN.approved_assets[0].sha256]; },
      pageOpts: { credit: null } } },

  /* ── P13: the staged composite and the lock chain ──────────────────── */
  { id: 'X20', expect: ['P13'], why: 'the staged master is not the active master',
    opts: { regEdit: r => { staged(r).master.pixel_sha256 =
      /* the approved 19:43 image, built on the superseded L3 v2 */
      '0515825db8c968891923b6986c709f10da8fdf990ec32eef110287259a63e25e'; } } },
  { id: 'X21', expect: ['P13'], why: 'the registry is pointed back at the superseded L3 v2',
    opts: { regEdit: r => { const c = r.possibility_reveal_lock_chain;
      c.active_layers.L3 = { version: 'v2', sha256: c.superseded.L3_v2.sha256 }; } } },
  { id: 'X22', expect: ['P13'], why: 'the chain applies the superseded L3 v2 layer',
    opts: { regEdit: r => { const c = r.possibility_reveal_lock_chain;
      c.chain[1].layer_sha256 = c.superseded.L3_v2.sha256; } } },
  { id: 'X23', expect: ['P13'], why: 'the chain no longer ends at the active master',
    opts: { regEdit: r => { const c = r.possibility_reveal_lock_chain;
      c.chain[c.chain.length - 1].output_sha256 = sha('elsewhere'); } } },
  { id: 'X24', expect: ['P13'], why: 'the lock chain is missing',
    opts: { regEdit: r => { delete r.possibility_reveal_lock_chain; } } },
  { id: 'X25', expect: ['P13'], why: 'a staged composite names a published asset',
    opts: { regEdit: r => { staged(r).asset = anAsset.asset; } } },
  { id: 'X26', expect: ['P13'], why: 'a staged composite has no named human review',
    opts: { regEdit: r => { delete staged(r).human_review.reviewer; } } },

  /* ── P10: published, the name may appear ONLY as the exact credit ──── */
  { id: 'X27', expect: ['P10'], why: 'published without its required credit',
    opts: { published: true, pageOpts: { credit: null } } },
  { id: 'X28', expect: ['P10'], why: 'the supplier name appears outside the exact credit',
    opts: { published: true, pageOpts: { extra: `<p>${TIMBERIN.organisation_name} hot tubs from €4,000.</p>` } } },
  { id: 'X29', expect: ['P10'], why: 'the credit is reworded',
    opts: { published: true, pageOpts: { credit: 'Hot tub by ' + TIMBERIN.organisation_name } } },
  { id: 'X30', expect: ['P10'], why: 'ANOTHER supplier is named beside the composite',
    opts: { published: true, pageOpts: { extra: `<p>Also see ${OTHER.organisation_name}.</p>` } } },
  { id: 'X31', expect: ['P10', 'P6'], why: 'published, credit present, but the grant is withdrawn',
    opts: { published: true, rightsEdit: r => { r.permission_outcome = W; } } },
  { id: 'X32', expect: ['P10'], why: 'an UNBOUND AI image sits beside the credit (the exception does not travel)',
    opts: { published: true, regEdit: r => {
      const p = pub(r); delete p.licensed_photographic_elements; delete p.composite_id;
      p.depicts_named_product = false; p.reference_inputs = []; } } },
  { id: 'X33', expect: ['P11'], why: 'the staged record copies a rights field into the register',
    opts: { regEdit: r => { staged(r).required_credit = CREDIT; } } },
];

for (const c of CASES) {
  const r = run(tree(c.opts));
  if (r.code === 2 || /INSTRUMENT UNAVAILABLE/.test(r.out)) {
    console.log(`  BLIND         ${c.id.padEnd(4)} ${c.why}`); broken++; continue;
  }
  if (r.code === 0) {
    console.log(`  VACUOUS       ${c.id.padEnd(4)} ${c.why}`);
    console.log('                the guard PASSED against this defect'); broken++; continue;
  }
  const ids = failedIds(r.out);
  const missing = c.expect.filter(w => !ids.includes(w));
  if (missing.length) {
    console.log(`  MISATTRIBUTED ${c.id.padEnd(4)} ${c.why}`);
    console.log(`                expected ${c.expect.join('+')}; failed: ${ids.join(',') || '(none)'}`);
    broken++;
  } else {
    console.log(`  PROVED        ${c.id.padEnd(4)} ${c.why}  [${c.expect.join('+')}]`);
    proved++;
  }
}

const after = [GUARD, GATE, REGISTER, RIGHTS, LICENCES].map(f => sha(readFileSync(f)));
const untouched = before.every((h, i) => h === after[i]);
console.log('-'.repeat(74));
console.log(`  repository files hashed before and after: ${untouched ? 'UNCHANGED' : 'CHANGED'}`);
if (!untouched) broken++;
console.log(`${CASES.length} mutations, ${proved} proved, ${CASES.length - proved} not proved\n`);
process.exit(broken ? 1 : 0);
