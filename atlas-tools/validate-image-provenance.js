#!/usr/bin/env node
/**
 * THE IMAGE PROVENANCE GUARD · P1–P11
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

console.log('\nIMAGE PROVENANCE GUARD · P1–P11');
console.log('='.repeat(74));
console.log(`  pages scanned        ${pages}`);
console.log(`  local images on them ${found.size}`);
console.log(`  declared records     ${records.length}`);
console.log(`  legacy undeclared    ${legacy.length}`);
console.log('-'.repeat(74));

/* ── P1 · every local image on a published page is accounted for ──────── */
{
  /* THE RATCHET, AND THE WHOLE POINT OF THIS FILE. An image in neither the
     records nor the enumerated backlog is a NEW undeclared image, and it is
     refused. */
  const unaccounted = [...found.keys()]
    .filter(a => !byAsset.has(a) && !legacySet.has(a));
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
  const ai = records.filter(r => r.class === 'AI_ILLUSTRATION');
  const orgs = new Set();
  if (existsSync(RIGHTS)) {
    try {
      const d = JSON.parse(readFileSync(RIGHTS, 'utf8'));
      const rows = Array.isArray(d) ? d
        : (Object.values(d).find(v => Array.isArray(v) && v[0]
                                      && typeof v[0] === 'object') || []);
      for (const r of rows) {
        if (r.organisation_name) orgs.add(String(r.organisation_name).toLowerCase());
        if (r.permitted_domain) orgs.add(String(r.permitted_domain).toLowerCase());
      }
    } catch { /* orgs stays empty; reported below */ }
  }
  const problems = [];
  for (const r of ai) {
    const prompt = String(r.prompt || '').toLowerCase();
    for (const o of orgs) {
      if (o.length > 3 && prompt.includes(o)) {
        problems.push(`${r.asset}: prompt names ${o}`);
      }
    }
    for (const src of (r.reference_inputs || [])) {
      const s = String(src).toLowerCase();
      for (const o of orgs) {
        if (o.includes('.') && s.includes(o)) {
          problems.push(`${r.asset}: reference input from ${o}`);
        }
      }
    }
    if (r.depicts_named_product !== false) problems.push(`${r.asset}: depicts_named_product not false`);
    if (r.depicts_named_organisation !== false) problems.push(`${r.asset}: depicts_named_organisation not false`);
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
    for (const r of ai) {
      for (const page of (found.get(r.asset) || [])) {
        const html = readFileSync(join(ROOT, page), 'utf8');
        /* The same <figure>, caption or card as a supplier's name. Scoped to
           a window around the asset reference rather than the whole page, so
           a supplier mentioned elsewhere on a long page is not a violation. */
        const i = html.indexOf(r.asset);
        if (i === -1) continue;
        const win = html.slice(Math.max(0, i - 1200), i + 1200);
        for (const o of orgNames) {
          if (o.length > 3 && win.includes(o)) {
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
