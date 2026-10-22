#!/usr/bin/env node
/**
 * THE IMAGE PROVENANCE GUARD · P1–P14
 * ====================================
 * Closes the blind spot at atlas-tools/validate-image-rights.js:395:
 *
 *     if (!/^https?:\/\//i.test(u)) continue;   // relative = PlotNua's own
 *
 * That assumption was sound when it was written -- everything local was
 * PlotNua's own artwork. It means the rights gate examines 40 externally
 * hosted supplier images and skips 85 locally hosted ones entirely. The
 * moment an AI illustration lands as a local file the assumption becomes
 * "relative = unexamined", and a laundered supplier photograph saved to
 * assets/img/ would pass silently. This guard is what makes a local image
 * declared rather than merely unexamined.
 *
 * IT IS NOT A RIGHTS GATE, AND MUST NEVER BECOME ONE. P11 asserts that:
 * nothing here can produce a permission, a provenance record can never
 * authorise supplier imagery, and the two files are read for two different
 * questions. The rights gate keeps its own job; this one keeps its own.
 *
 * IT FAILS CLOSED. Exit 1 = a violation. Exit 2 = the facts could not be
 * established, which is also a failure: a guard that passes when it is
 * confused is not a guard.
 *
 *   node atlas-tools/validate-image-provenance.js [--root PATH]
 *
 * The legacy backlog count is printed on every run and in the CI summary.
 */
import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const arg = (n, d) => {
  const i = process.argv.indexOf('--' + n);
  return i === -1 ? d : process.argv[i + 1];
};
const ROOT = arg('root', dirname(HERE));
const REGISTER = join(ROOT, 'image-provenance-records.json');
const RIGHTS = join(ROOT, 'image-rights-manifest.json');
/* H2, 20 Oct 2026: permission to ADAPT a supplier photograph into a composite.
   Read only for the licensed-photography exception (P6, P10, P13) and to add
   the licensed organisations to the names P6 and P10 protect. */
const LICENCES = join(ROOT, 'image-adaptation-licences.json');

let pass = 0, fail = 0;
const ok  = (n, d) => { pass++; console.log(`  PASS  ${n}${d ? '  [' + d + ']' : ''}`); };
const bad = (n, d) => { fail++; console.log(`  FAIL  ${n}${d ? '  [' + d + ']' : ''}`); };

function refuse(why) {
  console.log('\nIMAGE PROVENANCE GUARD');
  console.log('='.repeat(74));
  console.log('  INSTRUMENT UNAVAILABLE: ' + why);
  console.log('  Nothing was established. A guard that passes when it cannot');
  console.log('  establish the facts is not a guard.');
  process.exit(2);
}

/* ── the register ─────────────────────────────────────────────────────── */
if (!existsSync(REGISTER)) {
  refuse('image-provenance-records.json is missing. Every locally hosted '
         + 'image would be unexamined.');
}
let reg;
try { reg = JSON.parse(readFileSync(REGISTER, 'utf8')); }
catch (e) { refuse('the provenance register is not valid JSON: ' + e.message); }

const records = Array.isArray(reg.records) ? reg.records : null;
const legacy = Array.isArray(reg.legacy_undeclared) ? reg.legacy_undeclared : null;
if (!records || !legacy) {
  refuse('the register has no records array and/or no legacy_undeclared array');
}

const ASSET_CLASSES = ['SUPPLIER_IMAGE', 'AI_ILLUSTRATION'];
/* product-card is DELIBERATELY ABSENT. The founder's rule becomes a
   vocabulary restriction rather than a convention somebody has to remember:
   enabling it is a schema change with its own approval, not an oversight
   away. */
const PERMITTED_SURFACES = ['discovery', 'library-card', 'homepage',
                            'about', 'journey', 'preview'];
const IMG_EXT = /\.(jpe?g|png|webp|avif|gif|svg|ico)$/i;
/* PlotNua's own origins. An absolute self-reference is still one of our
   images and still needs declaring: twitter:image points at
   https://plotnua.ie/assets/og/... on 23 pages, which a "skip anything
   absolute" rule would have missed entirely. */
const SELF_ORIGINS = [/^https?:\/\/(www\.)?plotnua\.ie\//i];
/* Not part of the published site. */
const SKIP_DIRS = new Set(['.git', 'node_modules', 'outputs', '.github',
                           '__pycache__', 'atlas-tools']);

/* ── every local image a published page can show ──────────────────────────
   WIDENED 11 October 2026 after a coverage audit, and four of the gaps were
   real and in use:

     <link rel="icon|apple-touch-icon" href>   122 references, never scanned
     <meta twitter:image>                       23 references, never scanned
     site.webmanifest icons                      2 images, not HTML at all
     pages below the root                       12 files, never walked

   The first version walked only readdirSync(ROOT) for *.html and read four
   attribute shapes. The rights gate next to it walks recursively, so the two
   disagreed about what "published" means -- which is itself a defect.

   The remaining mechanisms below are covered PRE-EMPTIVELY: <img srcset>,
   imagesrcset, image-set(), <video poster>, <input type=image>, <object
   data>, xlink:href, SVG <image href>, msapplication-TileImage and
   JavaScript .src assignments to literal paths. None is in use today. That
   is exactly why they are covered -- the ratchet exists for the image
   somebody adds next month, and a mechanism nobody uses yet is the one most
   likely to slip in unexamined. */
function publishedLocalImages() {
  const found = new Map();      // asset path -> Set(pages)
  let pages = 0;

  const sources = [];
  (function walk(dir, rel) {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      if (SKIP_DIRS.has(e.name) || e.name.startsWith('.')) continue;
      const full = join(dir, e.name);
      const r = rel ? rel + '/' + e.name : e.name;
      if (e.isDirectory()) walk(full, r);
      else if (/\.(html|webmanifest)$/i.test(e.name)) sources.push([full, r]);
    }
  })(ROOT, '');

  for (const [full, rel] of sources) {
    let body;
    try { body = readFileSync(full, 'utf8'); } catch { continue; }
    pages++;
    body = body.replace(/<!--[\s\S]*?-->/g, ' ');   // comments are not published
    const urls = new Set();
    const addSet = v => v.split(',')
      .forEach(part => urls.add(part.trim().split(/\s+/)[0]));

    /* ---- in use today ---- */
    for (const m of body.matchAll(/<img\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<source\b[^>]*?\bsrcset\s*=\s*["']([^"']+)["']/gi)) addSet(m[1]);
    for (const m of body.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<meta[^>]+(?:property|name)=["'](?:og:image|twitter:image|msapplication-TileImage)["'][^>]+content=["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<link\b[^>]*\brel=["'][^"']*icon[^"']*["'][^>]*\bhref\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<link\b[^>]*\bhref\s*=\s*["']([^"']+)["'][^>]*\brel=["'][^"']*icon[^"']*["']/gi)) urls.add(m[1]);
    // the web manifest's icon list
    for (const m of body.matchAll(/"src"\s*:\s*"([^"]+)"/gi)) urls.add(m[1]);
    // JS assigning a literal path
    for (const m of body.matchAll(/\.src\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);

    /* ---- covered pre-emptively, not in use today ---- */
    for (const m of body.matchAll(/<img\b[^>]*?\bsrcset\s*=\s*["']([^"']+)["']/gi)) addSet(m[1]);
    for (const m of body.matchAll(/\bimagesrcset\s*=\s*["']([^"']+)["']/gi)) addSet(m[1]);
    for (const m of body.matchAll(/image-set\(\s*["']?([^"')]+)["']?/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<video\b[^>]*?\bposter\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<input\b[^>]*?\btype=["']image["'][^>]*?\bsrc\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<object\b[^>]*?\bdata\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<embed\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/(?:xlink:)?href\s*=\s*["']([^"']+\.(?:jpe?g|png|webp|avif|gif|svg|ico))["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/\bdata-(?:src|bg|image|background)\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);

    for (let u of urls) {
      if (!u) continue;
      if (u.startsWith('data:')) continue;             // inline, nothing to declare
      const self = SELF_ORIGINS.find(re => re.test(u));
      if (self) u = u.replace(self, '');               // our own origin, our own image
      else if (/^(https?:)?\/\//i.test(u)) continue;    // somebody else's: the rights gate's job
      u = u.split('?')[0].split('#')[0].replace(/^\.?\//, '');
      if (!u || !IMG_EXT.test(u)) continue;
      if (!found.has(u)) found.set(u, new Set());
      found.get(u).add(rel);
    }
  }
  return { found, pages };
}
const { found, pages } = publishedLocalImages();
if (!pages) refuse('no published HTML page was found under ' + ROOT);

const byAsset = new Map();
for (const r of records) if (r && r.asset) byAsset.set(r.asset, r);
const legacySet = new Map();
for (const e of legacy) if (e && e.asset) legacySet.set(e.asset, e);
/* HASH-BOUND DERIVATIVES (SEO Phase 1b, 16 Oct 2026). A re-encoding of one
   enumerated source file. It is accounted for ONLY through its source, is
   checked by P12, and is never counted in -- or added to -- the backlog. */
if (reg.derivatives !== undefined && !Array.isArray(reg.derivatives)) {
  refuse('the register has a derivatives field that is not an array');
}
const derivatives = Array.isArray(reg.derivatives) ? reg.derivatives : [];
const derivSet = new Map();
for (const d of derivatives) if (d && d.asset) derivSet.set(d.asset, d);

/* STAGED COMPOSITES (H2, 20 Oct 2026). A locked composite whose provenance is
   recorded BEFORE it is published. It names no asset path, so it can never
   satisfy P1 for a file on a page: publishing it means moving it to records
   with an asset, where every P-check applies. Checked by P6 and P13. */
if (reg.staged_composites !== undefined && !Array.isArray(reg.staged_composites)) {
  refuse('the register has a staged_composites field that is not an array');
}
const staged = Array.isArray(reg.staged_composites) ? reg.staged_composites : [];

/* BRAND VECTOR DERIVATIVES (22 Oct 2026, founder-approved Atlas symbol C).
   A pure vector redrawn from brand artwork the register already holds, bound
   to each source's exact sha256. Like a derivative it inherits its sources'
   provenance state, declares nothing and is not counted in the backlog.
   Checked by P14. */
if (reg.brand_vector_derivatives !== undefined && !Array.isArray(reg.brand_vector_derivatives)) {
  refuse('the register has a brand_vector_derivatives field that is not an array');
}
const brandVectors = Array.isArray(reg.brand_vector_derivatives) ? reg.brand_vector_derivatives : [];
const brandSet = new Map();
for (const v of brandVectors) if (v && v.asset) brandSet.set(v.asset, v);

/* ── THE LICENSED-PHOTOGRAPHY EXCEPTION TO P6 AND P10 ──────────────────────
   Founder decision, H2, 20 Oct 2026 (approved in principle at the L6 audit):
   "a supplier name may sit beside the illustration ONLY as the required credit
   of a granted, modification-permitting photo record bound to that asset."

   P6 and P10 exist to stop an AI image passing as a real supplier's product.
   A composite that really does contain a supplier's photographed product,
   used with written permission to adapt it, is the one case where naming the
   supplier is the honest thing to do -- as a credit, and as nothing else.

   The exception is DERIVED, never claimed. A record qualifies only if every
   licensed_photographic_elements entry resolves to exactly one licence in
   image-adaptation-licences.json, ALL of them granted by the SAME organisation
   (22 Oct 2026: one composite may carry more than one written grant from one
   supplier -- TimberIN's hot-tub grant of 20 Oct and its sauna grant of 22 Oct --
   and every one of those licences is held to every rule below; a composite
   can never mix organisations) (NOT the rights manifest: a record there is
   a hot-link host grant and a supplier listing record, and this is neither),
   and each such licence:
     a. is a live grant in the gate's own vocabulary, not withdrawn;
     b. says modification_permitted === true and carries a required credit;
     c. points back at Atlas by its outreach ref and a PN-EVID evidence_ref;
     d. enumerates the element's source photograph BY SHA-256, with
        use 'adapted-into-composite' and bound_composite equal to this
        record's composite_id;
   and the composite_id is claimed by exactly one record or staged composite.
   The provenance register holds only the POINTER (organisation_code +
   atlas_permission_ref, as P4 does). It grants nothing: P11 still holds.

   What it relaxes, and only for the bound organisation:
     P6  a reference input that IS one of the bound source photographs (its
         url, or a string carrying its sha256); depicts_named_product may be
         true, because it truthfully is.
     P10 the organisation's name beside the asset, but only inside the exact
         required credit of EVERY bound licence -- and each of those credits
         must then be present.
   What it never relaxes: a prompt naming any supplier; any other
   organisation; any other reference input; depicts_named_organisation. */
const LIVE_GRANTS = ['Granted — Founder Confirmed',
                     'Granted with Conditions — Founder Confirmed',
                     'Granted — Supplier Confirmed (one-click)'];
let licenceRows = [];
if (existsSync(LICENCES)) {
  try {
    const d = JSON.parse(readFileSync(LICENCES, 'utf8'));
    if (!Array.isArray(d.licences)) refuse('image-adaptation-licences.json has no licences array');
    licenceRows = d.licences;
  } catch (e) { refuse('image-adaptation-licences.json is not valid JSON: ' + e.message); }
}
let rightsRows = null;
function readRightsRows() {
  if (rightsRows !== null) return rightsRows;
  rightsRows = [];
  if (existsSync(RIGHTS)) {
    try {
      const d = JSON.parse(readFileSync(RIGHTS, 'utf8'));
      rightsRows = Array.isArray(d) ? d
        : (Object.values(d).find(v => Array.isArray(v) && v[0]
                                      && typeof v[0] === 'object') || []);
    } catch { rightsRows = []; }
  }
  return rightsRows;
}
const compositeClaims = new Map();
for (const r of [...records, ...staged]) {
  if (r && r.composite_id) compositeClaims.set(r.composite_id,
    (compositeClaims.get(r.composite_id) || 0) + 1);
}
/* -> { ok:true, row, rows, credits, sources:[{url, sha256}] } or { ok:false, why }
   row = the first bound licence; rows = every bound licence (same organisation). */
function licensedBinding(r) {
  const els = r && r.licensed_photographic_elements;
  if (els === undefined) return { ok: false, none: true, why: 'no licensed elements' };
  if (!Array.isArray(els) || !els.length) return { ok: false, why: 'licensed_photographic_elements is not a non-empty list' };
  if (!r.composite_id) return { ok: false, why: 'no composite_id to bind to' };
  if (compositeClaims.get(r.composite_id) !== 1) return { ok: false, why: `composite_id ${r.composite_id} is claimed ${compositeClaims.get(r.composite_id)} times` };
  const rows = licenceRows;
  let row = null;
  const rowsBound = [];
  const sources = [];
  for (const e of els) {
    const x = (e && e.rights_ref) || {};
    const hits = rows.filter(w => w.organisation_code && w.organisation_code === x.organisation_code
                                  && w.atlas_permission_ref === x.atlas_permission_ref);
    if (hits.length !== 1) return { ok: false, why: `rights_ref ${x.organisation_code}/${x.atlas_permission_ref} resolves to ${hits.length} licences` };
    if (row && hits[0].organisation_code !== row.organisation_code) return { ok: false, why: 'elements bind to licences of more than one organisation' };
    row = row || hits[0];
    const lic = hits[0];
    if (!rowsBound.includes(lic)) rowsBound.push(lic);
    const a = (lic.approved_assets || []).filter(s => s && s.sha256 && s.sha256 === e.source_sha256);
    if (a.length !== 1) return { ok: false, why: `source ${String(e.source_sha256).slice(0, 12)} is not enumerated once in the grant` };
    if (a[0].use !== 'adapted-into-composite') return { ok: false, why: `source ${a[0].id} is not granted for adaptation` };
    if (a[0].bound_composite !== r.composite_id) return { ok: false, why: `source ${a[0].id} is bound to ${a[0].bound_composite}, not ${r.composite_id}` };
    sources.push({ url: a[0].url, sha256: a[0].sha256 });
  }
  for (const lic of rowsBound) {
    const ref = lic.atlas_permission_ref;
    if (!LIVE_GRANTS.includes(lic.permission_outcome) || lic.withdrawal_effective_at) {
      return { ok: false, why: `the grant ${ref} is not live (${lic.permission_outcome}${lic.withdrawal_effective_at ? ', withdrawn' : ''})` };
    }
    if (lic.modification_permitted !== true) return { ok: false, why: `the grant ${ref} does not permit modification` };
    if (!lic.required_credit || !lic.organisation_name) return { ok: false, why: `the grant ${ref} carries no required credit` };
    if (lic.organisation_name !== row.organisation_name) return { ok: false, why: 'the bound licences name different organisations' };
    /* The licence file is PUBLIC (H2 founder review, 20 Oct 2026): it points
       back at Atlas by its outreach ref and a non-sensitive evidence_ref, never
       by correspondence identifiers. Both are still required. */
    if (!lic.atlas_permission_ref || !/^PN-EVID-[A-Z0-9-]+$/.test(String(lic.evidence_ref || ''))) {
      return { ok: false, why: `the grant ${ref} does not point back at Atlas and its evidence reference` };
    }
  }
  return { ok: true, row, rows: rowsBound, credits: rowsBound.map(l => String(l.required_credit)), sources };
}

console.log('\nIMAGE PROVENANCE GUARD · P1–P14');
console.log('='.repeat(74));
console.log(`  pages scanned        ${pages}`);
console.log(`  local images on them ${found.size}`);
console.log(`  declared records     ${records.length}`);
console.log(`  legacy undeclared    ${legacy.length}`);
console.log(`  derivatives          ${derivatives.length}  (not counted in the backlog)`);
console.log(`  staged composites    ${staged.length}  (locked, not published)`);
console.log(`  brand vectors        ${brandVectors.length}  (not counted in the backlog)`);
console.log('-'.repeat(74));

/* ── P1 · every local image on a published page is accounted for ──────── */
{
  /* THE RATCHET, AND THE WHOLE POINT OF THIS FILE. An image in neither the
     records nor the enumerated backlog is a NEW undeclared image, and it is
     refused. */
  const unaccounted = [...found.keys()]
    .filter(a => !byAsset.has(a) && !legacySet.has(a) && !derivSet.has(a) && !brandSet.has(a));
  unaccounted.length
    ? bad('P1 every local image on a published page is declared or enumerated',
          `${unaccounted.length} unaccounted: ${unaccounted.slice(0, 5).join(', ')}`)
    : ok('P1 every local image on a published page is declared or enumerated',
         `${found.size} checked`);
}

/* ── P2 · the hash binds the record to the bytes ──────────────────────── */
{
  /* A content-hash filename does not prevent a swap -- nothing recomputes
     it. Without this, a different image under a declared filename is
     invisible. */
  const wrong = [];
  for (const e of [...records, ...legacy]) {
    const p = join(ROOT, e.asset || '');
    if (!e.asset || !existsSync(p)) {
      if (e.asset && found.has(e.asset)) wrong.push(`${e.asset} (missing on disk)`);
      continue;
    }
    const h = createHash('sha256').update(readFileSync(p)).digest('hex');
    if (h !== e.sha256) wrong.push(`${e.asset} (${String(e.sha256).slice(0, 12)} != ${h.slice(0, 12)})`);
  }
  wrong.length
    ? bad('P2 every record’s sha256 matches the file on disk',
          `${wrong.length}: ${wrong.slice(0, 3).join('; ')}`)
    : ok('P2 every record’s sha256 matches the file on disk',
         `${records.length + legacy.length} hashed`);
}

/* ── P3 · the class vocabulary is closed ──────────────────────────────── */
{
  const badClass = records.filter(r => !ASSET_CLASSES.includes(r.class));
  const noImageAsClass = records.filter(r => r.class === 'NO_IMAGE');
  (!badClass.length && !noImageAsClass.length)
    ? ok('P3 every record carries a recognised asset class, and NO_IMAGE is '
         + 'not one of them')
    : bad('P3 every record carries a recognised asset class',
          `unrecognised=${badClass.length} NO_IMAGE-as-class=${noImageAsClass.length}`);
}

/* ── P4 · a SUPPLIER_IMAGE resolves to a live grant ───────────────────── */
{
  /* Routed through the EXISTING rights manifest's own vocabulary. This guard
     does not invent a second rights rule; it checks that the pointer lands
     on a row the rights gate already recognises. */
  const sup = records.filter(r => r.class === 'SUPPLIER_IMAGE');
  if (!sup.length) {
    ok('P4 a SUPPLIER_IMAGE row resolves to a live grant',
       'no SUPPLIER_IMAGE rows yet; the check is live and has nothing to test');
  } else if (!existsSync(RIGHTS)) {
    bad('P4 a SUPPLIER_IMAGE row resolves to a live grant',
        'the rights manifest is missing, so the pointer cannot be resolved');
  } else {
    let rows = [];
    try {
      const d = JSON.parse(readFileSync(RIGHTS, 'utf8'));
      rows = Array.isArray(d) ? d
        : (Object.values(d).find(v => Array.isArray(v) && v[0]
                                      && typeof v[0] === 'object') || []);
    } catch { /* handled below */ }
    const codes = new Set(rows.map(r => r.organisation_code).filter(Boolean));
    const refs = new Set(rows.map(r => r.atlas_permission_ref).filter(Boolean));
    const broken = sup.filter(r => {
      const x = r.rights_ref || {};
      return !(codes.has(x.organisation_code) && refs.has(x.atlas_permission_ref));
    });
    broken.length
      ? bad('P4 a SUPPLIER_IMAGE row resolves to a live grant',
            `${broken.length} unresolved`)
      : ok('P4 a SUPPLIER_IMAGE row resolves to a live grant', `${sup.length} checked`);
  }
}

/* ── P5 · an AI_ILLUSTRATION is fully declared ────────────────────────── */
{
  const ai = records.filter(r => r.class === 'AI_ILLUSTRATION');
  const problems = [];
  for (const r of ai) {
    const g = r.generated || {};
    if (!g.tool) problems.push(`${r.asset}: no tool`);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(g.date || ''))) problems.push(`${r.asset}: no date`);
    if (!r.prompt || !String(r.prompt).trim()) problems.push(`${r.asset}: no prompt`);
    /* An ABSENT reference_inputs is indistinguishable from an unanswered
       question. An empty array is an assertion that nothing was fed in. */
    if (!Array.isArray(r.reference_inputs)) problems.push(`${r.asset}: reference_inputs absent, not []`);
    const hr = r.human_review || {};
    if (!hr.reviewer || !hr.date || !hr.attests) problems.push(`${r.asset}: no named human review`);
  }
  (ai.length && !problems.length) ? ok('P5 every AI_ILLUSTRATION is fully declared', `${ai.length} checked`)
    : problems.length ? bad('P5 every AI_ILLUSTRATION is fully declared',
                            `${problems.length}: ${problems.slice(0, 3).join('; ')}`)
    : ok('P5 every AI_ILLUSTRATION is fully declared',
         'no AI_ILLUSTRATION rows yet; the check is live and has nothing to test');
}

/* ── P6 · anti-laundering ─────────────────────────────────────────────── */
{
  /* THE ONE ANTI-LAUNDERING CONTROL THAT CAN BE MECHANISED, and it is worth
     being precise about what it buys. It cannot look at two pictures and
     judge resemblance -- no check here can. What it does is make INTENT
     reviewable: a prompt naming a supplier, an organisation or a product is
     refused, and reference_inputs turns "did you feed it their photograph?"
     from an unanswerable question into a recorded assertion a named person
     signed. The resemblance judgement stays human, and P5 requires that the
     human attestation exists. It cannot require that it is true. */
  /* Staged composites are held to the same rule as published records. */
  const ai = [...records, ...staged].filter(r => r.class === 'AI_ILLUSTRATION');
  const orgs = new Set();
  /* An enumerated supplier photograph, by url or sha256, is a supplier
     reference input wherever it is hosted (H2: TimberIN's photographs live on
     woodenhottubsale.co.uk, which is not its permitted_domain). */
  const supplierPhotos = [];
  for (const r of [...readRightsRows(), ...licenceRows]) {
    if (r.organisation_name) orgs.add(String(r.organisation_name).toLowerCase());
    if (r.permitted_domain) orgs.add(String(r.permitted_domain).toLowerCase());
    if (r.organisation_domain) orgs.add(String(r.organisation_domain).toLowerCase());
    for (const a of (Array.isArray(r.approved_assets) ? r.approved_assets : [])) {
      if (a && a.url) supplierPhotos.push(String(a.url).toLowerCase());
      if (a && a.sha256) supplierPhotos.push(String(a.sha256).toLowerCase());
    }
  }
  const problems = [];
  for (const r of ai) {
    const id = r.asset || r.composite_id;
    const b = licensedBinding(r);
    if (!b.ok && !b.none) problems.push(`${id}: licensed-photography binding fails: ${b.why}`);
    const boundOrg = b.ok ? new Set([String(b.row.organisation_name).toLowerCase(),
                                     String(b.row.organisation_domain || '').toLowerCase()]) : new Set();
    const boundSrc = b.ok ? b.sources.flatMap(s => [String(s.url || '').toLowerCase(),
                                                    String(s.sha256).toLowerCase()]).filter(Boolean) : [];
    const prompt = String(r.prompt || '').toLowerCase();
    for (const o of orgs) {
      if (o.length > 3 && prompt.includes(o)) {
        problems.push(`${id}: prompt names ${o}`);          // never excepted
      }
    }
    for (const src of (r.reference_inputs || [])) {
      const s = String(src).toLowerCase();
      /* Excepted ONLY if the input is itself one of the bound photographs. */
      const isBound = boundSrc.some(x => s === x || (x.length === 64 && s.includes(x)));
      for (const o of orgs) {
        if (o.includes('.') && s.includes(o) && !(isBound && boundOrg.has(o))) {
          problems.push(`${id}: reference input from ${o}`);
        }
      }
      if (!isBound && supplierPhotos.some(x => s.includes(x))) {
        problems.push(`${id}: reference input is an enumerated supplier photograph`);
      }
    }
    if (r.depicts_named_product !== false && !(b.ok && r.depicts_named_product === true)) {
      problems.push(`${id}: depicts_named_product not false`);
    }
    if (r.depicts_named_organisation !== false) problems.push(`${id}: depicts_named_organisation not false`);
  }
  const note = orgs.size
    ? `${orgs.size} organisation names and domains checked`
    : 'NO organisation list could be read, so prompts were not checked';
  if (!orgs.size && ai.length) {
    bad('P6 no AI prompt or reference input names a supplier', note);
  } else {
    problems.length
      ? bad('P6 no AI prompt or reference input names a supplier',
            `${problems.length}: ${problems.slice(0, 3).join('; ')}`)
      : ok('P6 no AI prompt or reference input names a supplier', note);
  }
}

/* ── P7 · AI illustrations never reach a product card ─────────────────── */
{
  const ai = records.filter(r => r.class === 'AI_ILLUSTRATION');
  const problems = [];
  for (const r of ai) {
    const s = r.permitted_surfaces;
    if (!Array.isArray(s) || !s.length) { problems.push(`${r.asset}: no permitted_surfaces`); continue; }
    for (const surface of s) {
      if (!PERMITTED_SURFACES.includes(surface)) {
        problems.push(`${r.asset}: ${surface} is not a permitted surface`);
      }
    }
  }
  const cardIsAvailable = PERMITTED_SURFACES.includes('product-card');
  (!problems.length && !cardIsAvailable)
    ? ok('P7 product-card is not an available surface, and every AI surface '
         + 'is recognised', `${PERMITTED_SURFACES.length} surfaces`)
    : bad('P7 product-card is not an available surface',
          `cardAvailable=${cardIsAvailable} problems=${problems.length}`);
}

/* H3 (20 Oct 2026): the labels of a LICENSED PHOTOGRAPHIC COMPOSITE. Such an
   image is not only AI-generated, so the generic AI label would understate it.
   Its record carries a visible caption and an accessible disclosure, and they
   qualify only if, against the licence the record is bound to:
     - the caption contains the required credit of EVERY bound licence exactly
       and says it is an illustration;
     - the disclosure says "AI-generated", says photography, names the
       licensed organisation, and is no longer than 200 characters.
   Returns { ok, caption, disclosure } or { ok:false, why }. */
function compositeLabels(r, b) {
  const cap = String(r.visible_caption || ''), dis = String(r.accessible_disclosure || '');
  if (!cap || !dis) return { ok: false, why: 'no visible_caption and accessible_disclosure' };
  for (const c of b.credits) if (!cap.includes(c)) return { ok: false, why: `the caption does not carry the exact credit "${c}"` };
  if (!/illustrat/i.test(cap)) return { ok: false, why: 'the caption does not say it is an illustration' };
  if (!dis.includes('AI-generated') || !/photograph/i.test(dis) || !dis.includes(String(b.row.organisation_name))) {
    return { ok: false, why: 'the disclosure does not say AI-generated, photography and whose' };
  }
  if (dis.length > 200) return { ok: false, why: 'the disclosure is longer than 200 characters' };
  return { ok: true, caption: cap, disclosure: dis };
}
const pageText = html => html.replace(/<!--[\s\S]*?-->/g, ' ').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ');

/* ── P8 · a declared AI illustration carries its visible label ────────── */
{
  /* The founder held the page captions back until records exist. So this
     check is LIVE and currently has nothing to assert -- and it says so,
     rather than passing quietly as though it had verified something. */
  const ai = records.filter(r => r.class === 'AI_ILLUSTRATION');
  const expected = (reg.labels || {}).AI_ILLUSTRATION;
  if (!expected) {
    bad('P8 a declared AI illustration carries its approved label',
        'the register declares no AI_ILLUSTRATION label');
  } else if (!ai.length) {
    ok('P8 a declared AI illustration carries its approved label',
       'no AI_ILLUSTRATION rows yet, so no caption is due; the check is live');
  } else {
    const missing = [];
    for (const r of ai) {
      const onPages = found.get(r.asset);
      if (!onPages) continue;              // declared but not published: fine
      /* H3: a licensed photographic composite carries its own two labels
         instead; the generic AI label alone is not enough for it. */
      const b = licensedBinding(r);
      if (!b.none) {
        if (!b.ok) { missing.push(`${r.asset}: licensed binding fails (${b.why})`); continue; }
        const lab = compositeLabels(r, b);
        if (!lab.ok) { missing.push(`${r.asset}: ${lab.why}`); continue; }
        for (const page of onPages) {
          const text = pageText(readFileSync(join(ROOT, page), 'utf8'));
          if (!text.includes(lab.caption)) missing.push(`${r.asset} on ${page}: visible caption missing`);
          if (!text.includes(lab.disclosure)) missing.push(`${r.asset} on ${page}: accessible disclosure missing`);
        }
        continue;
      }
      for (const page of onPages) {
        const html = readFileSync(join(ROOT, page), 'utf8');
        if (!html.includes(expected)) missing.push(`${r.asset} on ${page}`);
      }
    }
    missing.length
      ? bad('P8 a declared AI illustration carries its approved label',
            `${missing.length}: ${missing.slice(0, 3).join('; ')}`)
      : ok('P8 a declared AI illustration carries its approved label',
           `${ai.length} checked`);
  }
}

/* ── P9 · no record for an asset no page references ───────────────────── */
{
  /* A withdrawn image's record should go with it, or the register slowly
     fills with claims about files nobody can see. Legacy entries are exempt:
     the backlog is a census of what is ON DISK, and 28 of the 85 are
     referenced by no page -- which is a real finding, reported below, and
     not a reason to drop them from the ratchet. */
  const stale = records.filter(r => !found.has(r.asset));
  stale.length
    ? bad('P9 no declared record describes an unreferenced asset',
          `${stale.length}: ${stale.slice(0, 3).map(r => r.asset).join(', ')}`)
    : ok('P9 no declared record describes an unreferenced asset');
}

/* ── P10 · no AI illustration shares a surface with a supplier name ───── */
{
  const ai = records.filter(r => r.class === 'AI_ILLUSTRATION');
  if (!ai.length) {
    ok('P10 no AI illustration is presented as a named supplier’s product',
       'no AI_ILLUSTRATION rows yet; the check is live');
  } else {
    const problems = [];
    let orgNames = [];
    if (existsSync(RIGHTS)) {
      try {
        const d = JSON.parse(readFileSync(RIGHTS, 'utf8'));
        const rows = Array.isArray(d) ? d
          : (Object.values(d).find(v => Array.isArray(v) && v[0]
                                        && typeof v[0] === 'object') || []);
        orgNames = rows.map(r => r.organisation_name).filter(Boolean);
      } catch { /* empty */ }
    }
    for (const l of licenceRows) if (l.organisation_name) orgNames.push(l.organisation_name);
    for (const r of ai) {
      for (const page of (found.get(r.asset) || [])) {
        const html = readFileSync(join(ROOT, page), 'utf8');
        /* The same <figure>, caption or card as a supplier's name. Scoped to
           a window around the asset reference rather than the whole page, so
           a supplier mentioned elsewhere on a long page is not a violation. */
        const i = html.indexOf(r.asset);
        if (i === -1) continue;
        const win = html.slice(Math.max(0, i - 1200), i + 1200);
        /* The licensed-photography exception: the bound organisation's name
           may appear ONLY inside its exact required credit, and that credit
           must then be there. Every other organisation is refused as before. */
        const b = licensedBinding(r);
        if (!b.ok && !b.none) problems.push(`${r.asset}: licensed-photography binding fails: ${b.why}`);
        const credits = b.ok ? b.credits : [];
        for (const credit of credits) if (!win.includes(credit)) {
          problems.push(`${r.asset} on ${page} lacks its required credit "${credit}"`);
        }
        /* ...and inside its approved accessible disclosure, which P8 holds to
           its own rules (H3). */
        const lab = b.ok ? compositeLabels(r, b) : { ok: false };
        for (const o of orgNames) {
          if (o.length <= 3) continue;
          let seen = win;
          if (credits.length && o === b.row.organisation_name) {
            for (const credit of credits) seen = seen.split(credit).join(' ');
            if (lab.ok) seen = seen.split(lab.disclosure).join(' ');
          }
          if (seen.includes(o)) {
            problems.push(`${r.asset} on ${page} sits beside ${o}`);
          }
        }
      }
    }
    problems.length
      ? bad('P10 no AI illustration is presented as a named supplier’s product',
            `${problems.length}: ${problems.slice(0, 3).join('; ')}`)
      : ok('P10 no AI illustration is presented as a named supplier’s product');
  }
}

/* ── P11 · provenance NEVER grants a permission ───────────────────────── */
{
  /* "AI generation is not proof of rights" is otherwise a sentence in a
     document. Asserted at SOURCE, three ways:
       a. the rights gate does not read this register at all;
       b. this register carries no rights field it could be mistaken for;
       c. no record claims a permission of its own. */
  const gatePath = join(HERE, 'validate-image-rights.js');
  let gateClean = true, gateRead = false;
  if (existsSync(gatePath)) {
    gateRead = true;
    const gate = readFileSync(gatePath, 'utf8');
    gateClean = !/image-provenance/.test(gate);
  }
  const blob = JSON.stringify(reg);
  const leaked = ['permission_outcome', 'permitted_domain', 'required_credit',
                  'permitted_delivery_hosts', 'permission_date']
    .filter(k => blob.includes(k));
  const claiming = records.filter(r =>
    r.permission_outcome || r.permitted_domain || r.required_credit);
  if (!gateRead) {
    bad('P11 (source) a provenance record can never grant a permission',
        'validate-image-rights.js could not be read, so the separation was '
        + 'not established');
  } else {
    (gateClean && !leaked.length && !claiming.length)
      ? ok('P11 (source) a provenance record can never grant a permission',
           'the rights gate does not read this register; it carries no rights '
           + 'field')
      : bad('P11 (source) a provenance record can never grant a permission',
            `gateReadsRegister=${!gateClean} leakedFields=${leaked.join(',')} `
            + `claimingRecords=${claiming.length}`);
  }
}

/* ── P12 · a derivative is bound to its source and never outgrows it ──── */
{
  /* Added 16 Oct 2026 (SEO Phase 1b, founder-approved). The only way a new
     local file may avoid the ratchet is as a verified re-encoding of a file
     the register already holds. Every condition below is what makes that
     exemption narrow:
       a. it is not also a record or a backlog entry, and appears once;
       b. its source is in the register with the SAME sha256 it was made from
          (a changed source makes the derivative stale);
       c. its source is not itself a derivative (no chains);
       d. it is WebP and its method is from a closed vocabulary;
       e. no crop and no upscale: same aspect ratio, never wider than the
          source -- read from the file's own header, not trusted from JSON;
       f. its bytes match its recorded hash;
       g. every page that shows it also carries its source (the fallback),
          so a derivative can never reach a surface its source is not on;
       h. it declares nothing: no class, status, label or permitted surface;
       i. its source is not on provenance hold (derivative_holds), and it never
          claims an embedded signed credential (re-encoding removes C2PA). */
  const METHODS = ['webp-reencode', 'webp-resize'];
  const problems = [];
  /* Provenance holds (17 Oct 2026): a held source may not have a derivative. */
  if (reg.derivative_holds !== undefined && !Array.isArray(reg.derivative_holds)) {
    problems.push('derivative_holds is not an array');
  }
  const held = new Set((Array.isArray(reg.derivative_holds) ? reg.derivative_holds : [])
    .map(h => h && h.source).filter(Boolean));
  for (const d of derivatives) {
    if (d && d.derived_from && held.has(d.derived_from.asset))
      problems.push(`${d.asset}: its source ${d.derived_from.asset} is on provenance hold`);
    if (d && d.content_credentials && d.content_credentials.derivative_embeds_c2pa !== false)
      problems.push(`${d.asset}: claims or carries an embedded credential`);
  }
  const seen = new Set();
  const webpSize = (buf) => {
    if (buf.length < 30 || buf.toString('ascii', 0, 4) !== 'RIFF'
        || buf.toString('ascii', 8, 12) !== 'WEBP') return null;
    const kind = buf.toString('ascii', 12, 16);
    if (kind === 'VP8 ') return [buf.readUInt16LE(26) & 0x3fff, buf.readUInt16LE(28) & 0x3fff];
    if (kind === 'VP8L') {
      const b = buf.readUInt32LE(21);
      return [(b & 0x3fff) + 1, ((b >> 14) & 0x3fff) + 1];
    }
    if (kind === 'VP8X') return [buf.readUIntLE(24, 3) + 1, buf.readUIntLE(27, 3) + 1];
    return null;
  };
  for (const d of derivatives) {
    const a = d && d.asset;
    if (!a) { problems.push('an entry has no asset'); continue; }
    if (seen.has(a)) problems.push(`${a} listed twice`);
    seen.add(a);
    if (byAsset.has(a) || legacySet.has(a)) problems.push(`${a} is also a record/backlog entry`);
    const from = d.derived_from || {};
    const srcEntry = byAsset.get(from.asset) || legacySet.get(from.asset);
    if (!srcEntry) problems.push(`${a}: source ${from.asset} is not in the register`);
    else if (srcEntry.sha256 !== from.sha256) problems.push(`${a}: source ${from.asset} has changed since derivation`);
    if (derivSet.has(from.asset)) problems.push(`${a}: derived from another derivative`);
    if (!/\.webp$/i.test(a) || !METHODS.includes(d.method)) problems.push(`${a}: not a WebP re-encoding (${d.method})`);
    for (const k of ['class', 'status', 'label', 'permitted_surfaces'])
      if (k in d) problems.push(`${a}: declares "${k}"`);
    const full = join(ROOT, a);
    if (!existsSync(full)) {
      if (found.has(a)) problems.push(`${a}: on a page but missing on disk`);
    } else {
      const buf = readFileSync(full);
      if (createHash('sha256').update(buf).digest('hex') !== d.sha256) problems.push(`${a}: bytes do not match its hash`);
      const wh = webpSize(buf);
      const sp = srcEntry && srcEntry.pixels;
      if (!wh) problems.push(`${a}: not a readable WebP file`);
      else if (Array.isArray(sp) && sp[0] && sp[1]) {
        if (wh[0] > sp[0]) problems.push(`${a}: wider than its source (upscaled)`);
        if (Math.abs(wh[0] / wh[1] - sp[0] / sp[1]) > 0.005) problems.push(`${a}: aspect ratio differs from its source (cropped)`);
      } else problems.push(`${a}: source pixels unknown, crop/upscale cannot be ruled out`);
    }
    for (const page of (found.get(a) || [])) {
      if (!(found.get(from.asset) || new Set()).has(page))
        problems.push(`${a} is on ${page} without its source ${from.asset}`);
    }
  }
  problems.length
    ? bad('P12 every derivative is hash-bound to an unchanged source and never outgrows it',
          `${problems.length}: ${problems.slice(0, 3).join('; ')}`)
    : ok('P12 every derivative is hash-bound to an unchanged source and never outgrows it',
         derivatives.length ? `${derivatives.length} checked` : 'no derivatives yet; the check is live');
}

/* The active L3 (H5C4, 22 Oct 2026; was "must be v2.1c"). Every superseded L3
   layer (L3_v2, L3_v2.1c, ...) is refused as the active L3 and as a chain step;
   the active L3 must be named by hash, and the version it replaced must record
   replaced_by === the active version, so a supersession is always explicit.
   L3_v2 must stay recorded (the original pavilion is never forgotten). */
function supersededL3(chain) {
  return Object.entries((chain && chain.superseded) || {})
    .filter(([k, v]) => /^L3_v[0-9.]+[a-z]?$/.test(k) && v && /^[0-9a-f]{64}$/.test(String(v.sha256 || '')))
    .map(([k, v]) => ({ key: k, sha256: v.sha256, replaced_by: v.replaced_by }));
}
function l3ChainProblems(chain) {
  const out = [];
  const L3 = ((chain && chain.active_layers) || {}).L3 || {};
  const sup = supersededL3(chain);
  if (!L3.version || !/^[0-9a-f]{64}$/.test(String(L3.sha256 || ''))) out.push('the lock chain does not name the active L3 by version and hash');
  if (!sup.some(x => x.key === 'L3_v2')) out.push('the superseded L3 v2 is not recorded');
  if (sup.some(x => x.sha256 === L3.sha256)) out.push('a superseded L3 is the active L3');
  if (!sup.some(x => x.replaced_by === L3.version)) out.push(`no superseded L3 records replaced_by ${L3.version}`);
  const steps = Array.isArray(chain && chain.chain) ? chain.chain : [];
  if (!steps.some(c => c.layer_sha256 === L3.sha256)) out.push('the chain does not apply the active L3 layer');
  if (steps.some(c => sup.some(x => x.sha256 === c.layer_sha256))) out.push('the chain applies a superseded L3 layer');
  return out;
}

/* ── P14 · a brand vector is bound to brand sources and is pure vector ── */
{
  /* Added 22 Oct 2026 (founder-approved Atlas symbol C: the approved ribbon
     artwork redrawn as a clean vector with the official P). The risk this
     exemption must not open: a new image escaping the ratchet, or a raster
     or photograph laundered into the brand folder. So:
       a. it is not also a record, backlog entry or derivative, and appears once;
       b. it lives in assets/brand/ and is an SVG;
       c. it names one or more sources, each in the register (record or
          backlog) with the SAME sha256, each in assets/brand/, none a
          derivative or brand vector itself (no chains);
       d. its bytes match its recorded hash;
       e. it is pure vector: no embedded or linked image, no script, no
          foreignObject, no external reference of any kind;
       f. it declares nothing: no class, status, label or permitted surface;
       g. its method is from a closed vocabulary and it records the founder
          approval it was made under;
       h. if it is on disk, a published page shows it (no orphan exemption). */
  const METHODS = ['vector-trace-and-compose'];
  const problems = [];
  const seen = new Set();
  for (const v of brandVectors) {
    const a = v && v.asset;
    if (!a) { problems.push('an entry has no asset'); continue; }
    if (seen.has(a)) problems.push(`${a} listed twice`);
    seen.add(a);
    if (byAsset.has(a) || legacySet.has(a) || derivSet.has(a)) problems.push(`${a} is also a record/backlog/derivative entry`);
    if (!/^assets\/brand\/[^/]+\.svg$/i.test(a)) problems.push(`${a}: not an SVG in assets/brand/`);
    const srcs = Array.isArray(v.derived_from) ? v.derived_from : [];
    if (!srcs.length) problems.push(`${a}: names no source`);
    for (const f of srcs) {
      const e = f && (byAsset.get(f.asset) || legacySet.get(f.asset));
      if (!e) problems.push(`${a}: source ${f && f.asset} is not in the register`);
      else if (e.sha256 !== f.sha256) problems.push(`${a}: source ${f.asset} has changed since derivation`);
      if (f && !/^assets\/brand\//.test(f.asset || '')) problems.push(`${a}: source ${f && f.asset} is not brand artwork`);
      if (f && (derivSet.has(f.asset) || brandSet.has(f.asset))) problems.push(`${a}: derived from another derivative`);
    }
    if (!METHODS.includes(v.method)) problems.push(`${a}: method outside the closed vocabulary (${v.method})`);
    if (!v.founder_approval || !v.founder_approval.date || !v.founder_approval.decision)
      problems.push(`${a}: records no founder approval`);
    for (const k of ['class', 'status', 'label', 'permitted_surfaces'])
      if (k in v) problems.push(`${a}: declares "${k}"`);
    const full = join(ROOT, a);
    if (!existsSync(full)) {
      if (found.has(a)) problems.push(`${a}: on a page but missing on disk`);
    } else {
      const buf = readFileSync(full);
      if (createHash('sha256').update(buf).digest('hex') !== v.sha256) problems.push(`${a}: bytes do not match its hash`);
      const t = buf.toString('utf8');
      if (/<image\b|<script\b|<foreignObject\b|<use\b[^>]*href|url\(|@import|(?:xlink:)?href\s*=/i.test(t))
        problems.push(`${a}: is not pure vector (embeds or links something)`);
      if (!found.has(a)) problems.push(`${a}: no published page shows it`);
    }
  }
  problems.length
    ? bad('P14 every brand vector is bound to unchanged brand sources and is pure vector',
          problems.slice(0, 4).join('; '))
    : ok('P14 every brand vector is bound to unchanged brand sources and is pure vector',
         brandVectors.length ? `${brandVectors.length} checked` : 'none recorded; the check is live');
}

/* ── P13 · a staged composite is declared, bound, unpublished, and on the
         authoritative lock chain ─────────────────────────────────────── */
{
  /* Added H2, 20 Oct 2026. A staged composite is a locked image recorded
     before publication. Conditions:
       a. fully declared as P5 requires of a published AI_ILLUSTRATION;
       b. names no asset path, so nothing on a page can be accounted for by
          it (publishing it means moving it to records, under every check);
       c. its composite_id is unique and not also a published record's;
       d. any licensed photographic elements bind (licensedBinding);
       e. its master is the ACTIVE master of possibility_reveal_lock_chain,
          the chain names the active L3 by hash (H5C4 since 22 Oct 2026), no
          superseded L3 version is the active one or a chain step, and the
          supersession is recorded (l3ChainProblems). The pixels themselves are verified offline by
          atlas-tools/verify-possibility-reveal-locks.py against the lock
          repository, which holds the images this tree must not carry. */
  const problems = [];
  const chain = reg.possibility_reveal_lock_chain;
  const ids = new Set();
  for (const s of staged) {
    const id = (s && s.composite_id) || '(no composite_id)';
    if (!s || !s.composite_id) problems.push('a staged composite has no composite_id');
    if (ids.has(id)) problems.push(`${id} staged twice`);
    ids.add(id);
    if (s && 'asset' in s) problems.push(`${id}: names an asset; a published image belongs in records`);
    if (records.some(r => r.composite_id === id)) problems.push(`${id}: is also a published record`);
    if (!ASSET_CLASSES.includes(s && s.class)) problems.push(`${id}: unrecognised class`);
    const g = (s && s.generated) || {};
    if (!g.tool || !/^\d{4}-\d{2}-\d{2}$/.test(String(g.date || ''))) problems.push(`${id}: generation not declared`);
    if (!s || !String(s.prompt || '').trim()) problems.push(`${id}: no prompt`);
    if (!s || !Array.isArray(s.reference_inputs)) problems.push(`${id}: reference_inputs absent, not []`);
    const hr = (s && s.human_review) || {};
    if (!hr.reviewer || !hr.date || !hr.attests) problems.push(`${id}: no named human review`);
    const b = licensedBinding(s);
    if (!b.ok && !b.none) problems.push(`${id}: ${b.why}`);
    const m = (s && s.master) || {};
    if (!chain || typeof chain !== 'object') { problems.push(`${id}: no possibility_reveal_lock_chain to check against`); continue; }
    const am = chain.active_master || {};
    if (!/^[0-9a-f]{64}$/.test(String(am.pixel_sha256 || ''))) problems.push('the lock chain has no active master pixel hash');
    if (m.pixel_sha256 !== am.pixel_sha256) problems.push(`${id}: master ${String(m.pixel_sha256).slice(0, 12)} is not the active master ${String(am.pixel_sha256).slice(0, 12)}`);
    for (const p of l3ChainProblems(chain)) problems.push(p);
    const steps = Array.isArray(chain.chain) ? chain.chain : [];
    const last = steps[steps.length - 1] || {};
    if (last.output_sha256 !== am.sha256) problems.push('the chain does not end at the active master');
  }
  /* H3 (20 Oct 2026): PUBLISHED Reveal layers stay on the lock chain too.
       f. a record with reveal_layer names the layer's LOCKED file by hash: the
          chain's active layer for L3 / L5 / L6 (L3 must be the active, explicitly superseding L3, never a
          superseded v2), or the locked layer carried in the base for L4;
       g. a published composite (composite_id) names the ACTIVE master. */
  if (chain && typeof chain === 'object') {
    const act = chain.active_layers || {}, inBase = chain.locked_layers_in_base || {};
    const supL3 = supersededL3(chain).map(x => x.sha256);
    for (const r of records) {
      const rl = r.reveal_layer;
      if (rl) {
        const want = (act[rl.id] || {}).sha256 || (inBase[rl.id] || {}).sha256;
        if (!want) problems.push(`${r.asset}: ${rl.id} is not a layer of the lock chain`);
        else if (rl.layer_sha256 !== want) problems.push(`${r.asset}: ${rl.id} is not the locked layer`);
        if (rl.id === 'L3' && (l3ChainProblems(chain).length || supL3.includes(rl.layer_sha256))) problems.push(`${r.asset}: L3 is not the active, explicitly superseding L3`);
      }
      if (r.composite_id) {
        const m = r.master || {};
        if (m.pixel_sha256 !== (chain.active_master || {}).pixel_sha256) problems.push(`${r.asset}: composite master is not the active master`);
      }
    }
  } else if (records.some(r => r.reveal_layer || r.composite_id)) {
    problems.push('published Reveal layers but no possibility_reveal_lock_chain');
  }
  problems.length
    ? bad('P13 every Reveal layer and composite, staged or published, is on the active lock chain',
          `${problems.length}: ${problems.slice(0, 3).join('; ')}`)
    : ok('P13 every Reveal layer and composite, staged or published, is on the active lock chain',
         `${staged.length} staged, ${records.filter(r => r.reveal_layer).length} published Reveal layer(s) on the chain`);
}

/* ── the backlog, visible on every run ────────────────────────────────── */
const unreferenced = legacy.filter(e => !(e.referenced_by || []).length);
console.log('-'.repeat(74));
console.log(`  LEGACY UNDECLARED: ${legacy.length} asset(s) awaiting a `
            + 'provenance declaration.');
console.log('  A legacy entry is NOT a declaration, NOT verified, and NOT '
            + 'authorised');
console.log('  supplier imagery. The count only goes down.');
if (unreferenced.length) {
  console.log(`  Of those, ${unreferenced.length} are referenced by no `
              + 'published page.');
}
if (process.env.GITHUB_STEP_SUMMARY) {
  try {
    const { appendFileSync } = await import('node:fs');
    appendFileSync(process.env.GITHUB_STEP_SUMMARY,
      `\n### Image provenance\n\n`
      + `- declared records: **${records.length}**\n`
      + `- legacy undeclared: **${legacy.length}**\n`
      + `- local images on published pages: **${found.size}**\n`
      + `\nA legacy entry is not a declaration and not an authorisation.\n`);
  } catch { /* the summary is a convenience, never the gate */ }
}

console.log('\n' + '='.repeat(74));
console.log(`${pass + fail} checks, ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
