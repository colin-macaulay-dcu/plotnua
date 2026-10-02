/* BIOBUILDS CONTAINMENT PROOF.
   ---------------------------------------------------------------------------
   WHY THIS EXISTS.

   image-rights-manifest.json scopes a grant by HOST and PATH PREFIX. It has no
   notion of a page. So the moment a biobuilds.com row exists, the publish-time
   gate would happily pass a biobuilds.com image on ANY page in this repository.

   BIOBUILDS did not grant that. They granted "use selected images from our
   website, with credit and a link back", and attached a condition: "Please
   send us the listing before it goes live, so we can check it." The grant
   therefore supports exactly one page today -- the private, noindexed review
   preview -- and nothing else.

   This file is the difference between the manifest row and the grant. It makes
   the row NARROWER than the gate would enforce on its own. Removing it widens
   permission without anybody deciding to.

   WHAT IT CHECKS, and each check is a way the hold could quietly fail:

     C1  Every biobuilds.com image in the deployed tree is on the one
         authorised page. A second page carrying them is publication.
     C2  That page still carries all five robots directives. A preview that
         loses noindex is a published page with extra steps.
     C3  That page still carries the credit and the link back, which are
         conditions of the grant, not decoration.
     C4  No sitemap lists it. A sitemap entry is an invitation to index.
     C5  The rights record still says 'Granted with Conditions' and still
         carries the pre-live-review condition. An outcome quietly upgraded to
         plain 'Granted' would read as clearance to publish.
     C6  The runtime product payload carries no biobuilds.com image block.
         That block is written only for Atlas assets marked Approved, and it
         is what puts a supplier into the Results pool. This is the check that
         proves the manifest row did not reach the public journey.

   Exit 0 = contained. Exit 1 = a containment breach. Exit 2 = the proof could
   not establish the facts, which is also a failure: a proof that passes when
   it is confused is not a proof.

   Run: node atlas-tools/prove-biobuilds-containment.mjs                     */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

/* fileURLToPath, not url.pathname: a repository path containing a space
   arrives percent-encoded otherwise and the proof cannot find the tree. */
const ROOT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)), '..');
const PAGE = 'biobuilds-preview.html';
const HOST = 'biobuilds.com';
const CREDIT = '© BIOBUILDS';
const ROBOTS = ['noindex', 'nofollow', 'noarchive', 'nosnippet', 'noimageindex'];

let failed = 0;
let confused = 0;

function ok(what) { console.log('  PASS   ' + what); }
function bad(what, detail) {
  console.log('  FAIL   ' + what);
  if (detail) console.log('         ' + detail);
  failed++;
}
function cannot(what, detail) {
  console.log('  ERROR  ' + what);
  if (detail) console.log('         ' + detail);
  confused++;
}

console.log('BIOBUILDS CONTAINMENT PROOF');
console.log('='.repeat(76));

/* ---- walk every published page, exactly as the rights gate does ---------- */
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

/* C1 . the imagery lives on one page and no other ------------------------- */
const carriers = new Map();
for (const f of htmlFiles) {
  /* Comments are not published, so they are not a breach either. The gate
     strips them; this must strip them too or it will refuse a note about
     BIOBUILDS that no homeowner can see. */
  const html = fs.readFileSync(f, 'utf8').replace(/<!--[\s\S]*?-->/g, ' ');
  const urls = new Set();
  for (const m of html.matchAll(/<img\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
  for (const m of html.matchAll(/<source\b[^>]*?\bsrcset\s*=\s*["']([^"']+)["']/gi)) {
    m[1].split(',').forEach(p => urls.add(p.trim().split(/\s+/)[0]));
  }
  for (const m of html.matchAll(/url\(\s*["']?(https?:\/\/[^"')]+)["']?\s*\)/gi)) urls.add(m[1]);
  for (const m of html.matchAll(/<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)["']/gi)) urls.add(m[1]);
  const hits = [...urls].filter(u => {
    try { return new URL(u).hostname.toLowerCase().replace(/^www\./, '') === HOST; }
    catch { return false; }
  });
  if (hits.length) carriers.set(path.relative(ROOT, f), hits.length);
}

const wrong = [...carriers.keys()].filter(p => p !== PAGE);
if (wrong.length) {
  bad('BIOBUILDS imagery appears only on ' + PAGE,
      'it also appears on: ' + wrong.join(', ') + '. BIOBUILDS asked to see '
      + 'the listing before it goes live; another page carrying their imagery '
      + 'is publication, whatever that page is called.');
} else if (!carriers.has(PAGE)) {
  ok('no BIOBUILDS imagery is deployed anywhere (the held slot)');
} else {
  ok('BIOBUILDS imagery appears on ' + PAGE + ' and nowhere else ('
     + carriers.get(PAGE) + ' references)');
}

/* C2, C3 . the preview is still private, still credited -------------------- */
const pagePath = path.join(ROOT, PAGE);
if (!fs.existsSync(pagePath)) {
  cannot(PAGE + ' is not in the tree', 'the proof cannot check the hold on a '
    + 'page that is not there.');
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

  if (carriers.has(PAGE)) {
    if (src.split(CREDIT).length - 1 < 2) {
      bad("the credit '" + CREDIT + "' is present at least twice",
          'the credit is a condition of the grant, not decoration.');
    } else {
      ok("the credit '" + CREDIT + "' is present "
         + (src.split(CREDIT).length - 1) + ' times');
    }
    if (!src.includes('href="https://www.' + HOST + '/')) {
      bad('the preview links back to https://www.' + HOST + '/',
          'the link back is the other condition of the grant.');
    } else {
      ok('the preview links back to https://www.' + HOST + '/');
    }
  }
}

/* C4 . no sitemap invites anyone in --------------------------------------- */
let sitemaps = 0;
for (const f of fs.readdirSync(ROOT)) {
  if (!/sitemap.*\.xml$/i.test(f)) continue;
  sitemaps++;
  if (fs.readFileSync(path.join(ROOT, f), 'utf8').toLowerCase().includes('biobuilds')) {
    bad('no sitemap lists the BIOBUILDS preview', f + ' lists it.');
  }
}
if (sitemaps === 0) cannot('no sitemap was found to check');
else if (!failed) ok('no sitemap lists the BIOBUILDS preview (' + sitemaps + ' checked)');

/* C5 . the rights record still says what the supplier actually said ------- */
const recPath = path.join(ROOT, 'image-rights-records.json');
try {
  const doc = JSON.parse(fs.readFileSync(recPath, 'utf8'));
  const row = (doc.records || []).find(r => r.permitted_domain === HOST);
  if (!row) {
    if (carriers.has(PAGE)) {
      bad('a BIOBUILDS rights record exists',
          'the preview carries their imagery but no record governs it.');
    } else {
      ok('no BIOBUILDS rights record and no deployed imagery (consistent)');
    }
  } else if (row.permission_outcome !== 'Granted with Conditions — Founder Confirmed') {
    bad('the BIOBUILDS outcome is still conditional',
        'it reads ' + JSON.stringify(row.permission_outcome) + '. BIOBUILDS '
        + 'asked to review before go-live; an unconditional outcome loses that.');
  } else {
    const conds = (row.conditions || []).join(' ').toLowerCase();
    if (!conds.includes('before it goes live')) {
      bad('the pre-live review condition is still recorded',
          'it has gone from the conditions list.');
    } else {
      ok('the record is conditional and still carries the pre-live review');
    }
  }
} catch (e) {
  cannot('image-rights-records.json could not be read', String(e.message));
}

/* C6 . the public Results path is untouched -------------------------------- */
/* The runtime payload is what decides the Results pool. An image block there
   for BIOBUILDS would mean an Atlas asset reached 'Approved' -- which is the
   one thing that would put them in front of homeowners. */
const payloads = [];
(function find(d, depth) {
  if (depth > 3) return;
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    if (e.name.startsWith('.') || e.name === 'node_modules') continue;
    const full = path.join(d, e.name);
    if (e.isDirectory()) find(full, depth + 1);
    /* EVERY atlas-*.json, not a hand-listed few. An earlier draft of this
       matched only atlas-stats.json, which carries no imagery at all, so C6
       passed without ever looking at the Results pool. A containment check
       that cannot see the pool it is protecting is worse than none. */
    else if (/^atlas-.*\.json$/i.test(e.name)) payloads.push(full);
  }
})(ROOT, 0);

if (!payloads.length) {
  cannot('no runtime Atlas payload was found',
         'C6 cannot confirm BIOBUILDS is absent from the Results pool.');
} else {
  const leaky = payloads.filter(p =>
    fs.readFileSync(p, 'utf8').toLowerCase().includes(HOST));
  if (leaky.length) {
    bad('no runtime payload carries a BIOBUILDS image',
        leaky.map(p => path.relative(ROOT, p)).join(', ') + '. That means an '
        + 'Atlas asset reached Approved and BIOBUILDS can reach Results.');
  } else {
    ok('no runtime payload carries a BIOBUILDS image (' + payloads.length
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
console.log('CONTAINED — the BIOBUILDS grant reaches the private review '
  + 'preview and nothing else.');
process.exit(0);
