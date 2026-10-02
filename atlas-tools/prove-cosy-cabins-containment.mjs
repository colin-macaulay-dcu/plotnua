/* COSY CABINS CONTAINMENT PROOF.
   ---------------------------------------------------------------------------
   WHY THIS EXISTS.

   Cosy Cabins granted NOTHING. Bruno was offered two replies -- "YES" for
   permission to feature the company and use selected website imagery, or
   "PREVIEW" to see the page first -- and he chose PREVIEW. Atlas therefore
   holds Permission Outcome "Unknown -- Awaiting Reply", and UNKNOWN is not
   GRANTED.

   That makes this preview a stricter case than BIOBUILDS, which did grant
   with conditions. There is no manifest row to scope, because there is no
   grant to record. What has to be proved instead is ABSENCE: that a preview
   page exists on the production domain carrying this supplier's published
   facts and NONE of their imagery, and that nothing about it has leaked into
   the public journey.

   WHAT IT CHECKS, and each one is a way the hold could quietly fail:

     C1  No cosycabins.ie or Cosy Cabins Wix-prefix image appears on ANY
         deployed page, including the preview itself. Not "only on the
         preview" -- NONE, anywhere, because nothing was granted.
     C2  The preview carries all five robots directives.
     C3  The preview links back to the supplier's site and credits them for
         the published facts it uses.
     C4  No sitemap lists it.
     C5  No Cosy Cabins row exists in image-rights-records.json. A row would
         mean somebody had written a grant that was never given. If a row
         ever does appear, its outcome must not be a live grant.
     C6  No runtime Atlas payload carries Cosy Cabins imagery or reaches
         their products through the publication path.
     C7  The page makes none of the claims their own site contradicts:
         insulation as standard, planning status, lead times, warranties or
         nationwide coverage.

   Exit 0 = contained. Exit 1 = a containment breach. Exit 2 = the proof
   could not establish the facts, which is also a failure: a proof that
   passes when it is confused is not a proof.

   Run: node atlas-tools/prove-cosy-cabins-containment.mjs                  */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

/* fileURLToPath, not url.pathname: this repository's path contains a space
   and arrives percent-encoded otherwise. */
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PAGE = 'cosy-cabins-preview.html';
const SITE_HOST = 'cosycabins.ie';
/* Their own Wix media account prefix. The site serves its images from the
   shared static.wixstatic.com host, exactly as Garden Room Ireland does, so
   the account prefix is what identifies them -- not the host. */
const WIX_PREFIX = '/media/9ba815_';
const CREDIT = '© Cosy Cabins Limited';
const ROBOTS = ['noindex', 'nofollow', 'noarchive', 'nosnippet', 'noimageindex'];
const FORBIDDEN_CLAIMS = [
  'fully insulated', 'insulated garden room', 'u-value',
  'planning exempt', 'no planning permission',
  'lead time', 'warranty', 'nationwide', 'across ireland'
];

let failed = 0;
let confused = 0;
const ok = w => console.log('  PASS   ' + w);
const bad = (w, d) => { console.log('  FAIL   ' + w); if (d) console.log('         ' + d); failed++; };
const cannot = (w, d) => { console.log('  ERROR  ' + w); if (d) console.log('         ' + d); confused++; };

console.log('COSY CABINS CONTAINMENT PROOF');
console.log('='.repeat(76));

/* ---- walk every published page, exactly as the rights gate does --------- */
const htmlFiles = [];
(function walk(d) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    if (e.name.startsWith('.') || e.name === 'node_modules') continue;
    const full = path.join(d, e.name);
    if (e.isDirectory()) walk(full);
    else if (e.name.endsWith('.html')) htmlFiles.push(full);
  }
})(ROOT);
if (!htmlFiles.length) cannot('no .html files were found; the proof cannot run');

/* C1 . no imagery anywhere, on any page --------------------------------- */
const carriers = [];
for (const f of htmlFiles) {
  /* Comments are not published, so they are not a breach either. The gate
     strips them; this must too, or a note explaining the rights position
     would itself read as a violation. */
  const html = fs.readFileSync(f, 'utf8').replace(/<!--[\s\S]*?-->/g, ' ');
  const urls = new Set();
  for (const m of html.matchAll(/<img\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
  for (const m of html.matchAll(/<source\b[^>]*?\bsrcset\s*=\s*["']([^"']+)["']/gi)) {
    m[1].split(',').forEach(p => urls.add(p.trim().split(/\s+/)[0]));
  }
  for (const m of html.matchAll(/url\(\s*["']?(https?:\/\/[^"')]+)["']?\s*\)/gi)) urls.add(m[1]);
  for (const m of html.matchAll(/<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)["']/gi)) urls.add(m[1]);
  for (const u of urls) {
    let parsed;
    try { parsed = new URL(u); } catch { continue; }
    const host = parsed.hostname.toLowerCase().replace(/^www\./, '');
    const isTheirs = host === SITE_HOST
      || (host === 'static.wixstatic.com' && parsed.pathname.startsWith(WIX_PREFIX));
    if (isTheirs) carriers.push(path.relative(ROOT, f) + ' → ' + u.slice(0, 70));
  }
}
if (carriers.length) {
  bad('no Cosy Cabins imagery appears on any deployed page',
      carriers.join('; ') + '. Cosy Cabins replied PREVIEW, not YES. '
      + 'UNKNOWN is not GRANTED, and the rights gate would refuse these.');
} else {
  ok('no Cosy Cabins imagery appears on any deployed page (' + htmlFiles.length
     + ' pages scanned, cosycabins.ie and static.wixstatic.com'
     + WIX_PREFIX + ' both checked)');
}

/* C2, C3, C7 . the preview itself ---------------------------------------- */
const pagePath = path.join(ROOT, PAGE);
if (!fs.existsSync(pagePath)) {
  cannot(PAGE + ' is not in the tree',
         'the proof cannot check a hold on a page that is not there.');
} else {
  const src = fs.readFileSync(pagePath, 'utf8');
  const missing = ROBOTS.filter(d => !src.includes(d));
  if (missing.length) {
    bad('the preview carries all five robots directives',
        'missing: ' + missing.join(', ') + '. A preview without these is a '
        + 'published page.');
  } else {
    ok('the preview carries noindex, nofollow, noarchive, nosnippet, noimageindex');
  }

  if (!src.includes('href="https://www.' + SITE_HOST + '/')) {
    bad('the preview links back to ' + SITE_HOST,
        'every figure on the page is their published information and the '
        + 'page must link to where it came from.');
  } else {
    ok('the preview links back to ' + SITE_HOST);
  }

  if (!src.includes(CREDIT)) {
    bad('the preview credits ' + CREDIT + ' for the published facts it uses');
  } else {
    ok('the preview credits ' + CREDIT);
  }

  const visible = src
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<style\b[\s\S]*?<\/style>/gi, ' ')
    .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
    .toLowerCase();
  const claimed = FORBIDDEN_CLAIMS.filter(c => visible.includes(c));
  if (claimed.length) {
    bad('the preview makes no claim the evidence does not support',
        'found: ' + claimed.join(', ') + '. Cosy Cabins’ own site '
        + 'contradicts itself on insulation, installation and nationwide '
        + 'delivery; PlotNua does not resolve that by picking a side.');
  } else {
    ok('the preview makes no insulation, planning, lead-time, warranty or '
       + 'nationwide claim');
  }
}

/* C4 . no sitemap invites anyone in ------------------------------------- */
let sitemaps = 0, listed = false;
for (const f of fs.readdirSync(ROOT)) {
  if (!/sitemap.*\.xml$/i.test(f)) continue;
  sitemaps++;
  const s = fs.readFileSync(path.join(ROOT, f), 'utf8').toLowerCase();
  if (s.includes('cosy-cabins') || s.includes('cosycabins')) {
    bad('no sitemap lists the Cosy Cabins preview', f + ' lists it.');
    listed = true;
  }
}
if (sitemaps === 0) cannot('no sitemap was found to check');
else if (!listed) ok('no sitemap lists the Cosy Cabins preview (' + sitemaps + ' checked)');

/* C5 . no grant was written that was never given ------------------------ */
try {
  const doc = JSON.parse(fs.readFileSync(path.join(ROOT, 'image-rights-records.json'), 'utf8'));
  const row = (doc.records || []).find(r =>
    String(r.permitted_domain || '').toLowerCase().includes(SITE_HOST)
    || String(r.organisation_name || '').toLowerCase().includes('cosy cabins'));
  if (!row) {
    ok('no Cosy Cabins rights record exists, which is correct: nothing was granted');
  } else if (/^Granted/i.test(String(row.permission_outcome || ''))) {
    bad('no live grant is recorded for Cosy Cabins',
        'the record reads ' + JSON.stringify(row.permission_outcome)
        + '. Bruno replied PREVIEW, not YES. A live-grant outcome here is '
        + 'PREVIEW converted into GRANTED.');
  } else {
    ok('a Cosy Cabins record exists but its outcome is not a live grant ('
       + row.permission_outcome + ')');
  }
} catch (e) {
  cannot('image-rights-records.json could not be read', String(e.message));
}

/* C6 . the public Results path is untouched ----------------------------- */
const payloads = [];
(function find(d, depth) {
  if (depth > 3) return;
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    if (e.name.startsWith('.') || e.name === 'node_modules') continue;
    const full = path.join(d, e.name);
    if (e.isDirectory()) find(full, depth + 1);
    /* EVERY atlas-*.json, not a hand-picked few: a check that cannot see
       the Results pool it is protecting is worse than none. */
    else if (/^atlas-.*\.json$/i.test(e.name)) payloads.push(full);
  }
})(ROOT, 0);

if (!payloads.length) {
  cannot('no runtime Atlas payload was found',
         'C6 cannot confirm Cosy Cabins is absent from the Results pool.');
} else {
  const leaky = payloads.filter(p => {
    const s = fs.readFileSync(p, 'utf8').toLowerCase();
    return s.includes(SITE_HOST) || s.includes(WIX_PREFIX.toLowerCase());
  });
  if (leaky.length) {
    bad('no runtime payload carries Cosy Cabins imagery or source links',
        leaky.map(p => path.relative(ROOT, p)).join(', '));
  } else {
    ok('no runtime payload carries Cosy Cabins imagery (' + payloads.length
       + ' checked); the Results pool cannot reach them');
  }
}

console.log('='.repeat(76));
if (confused) {
  console.log('CONTAINMENT NOT ESTABLISHED — ' + confused
    + ' check(s) could not run. That is a failure, not a pass.');
  process.exit(2);
}
if (failed) {
  console.log('CONTAINMENT BREACHED — ' + failed + ' check(s) failed.');
  process.exit(1);
}
console.log('CONTAINED — the Cosy Cabins preview carries their published '
  + 'facts, none of their imagery, and nothing has reached the public journey.');
process.exit(0);
