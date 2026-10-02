/* PREVIEW-ONLY CONTAINMENT PROOF.
   ---------------------------------------------------------------------------
   WHAT THIS IS FOR.

   Some suppliers reply to PlotNua's outreach by asking to SEE the preview
   rather than by saying yes. The outreach offers both. Choosing PREVIEW is
   not a grant, so Atlas keeps their Permission Outcome at "Unknown --
   Awaiting Reply", and UNKNOWN is not GRANTED.

   That makes their previews a stricter case than a conditional grant like
   BIOBUILDS. There is no manifest row to scope, because there is no grant to
   record. What has to be proved instead is ABSENCE: that a page exists on the
   production domain carrying the supplier's published FACTS and NONE of their
   imagery, and that nothing about it has leaked into the public journey.

   WHY ONE FILE AND A REGISTER. This began as a per-supplier script. The
   second supplier was about to get a near-identical copy, and the third would
   have guaranteed that a fix made in one was forgotten in the others. The
   checks live here; atlas-tools/preview-only-suppliers.json is the only thing
   that changes when a supplier is added. A proof that is cheaper to extend
   than to copy is one that actually gets extended.

   PER SUPPLIER, each check being a way the hold could quietly fail:

     C1  No image from their site or their CDN prefix appears on ANY deployed
         page, including their own preview. Not "only on the preview" -- NONE,
         anywhere, because nothing was granted.
     C2  Their preview carries all five robots directives.
     C3  Their preview links back to their site and credits them for the
         published facts it uses.
     C4  No sitemap lists it.
     C5  No rights record exists for them. If one ever appears, its outcome
         must not be a live grant -- that would be PREVIEW written up as
         GRANTED.
     C6  No runtime Atlas payload reaches their imagery or their site.
     C7  Their preview makes none of the claims their own site does not
         support. The forbidden list is per supplier on purpose: insulation
         is unevidenced for one of these suppliers and evidenced three times
         over for another, and a shared list would either lie or gag.

   Exit 0 = contained. Exit 1 = a containment breach. Exit 2 = the proof could
   not establish the facts, which is also a failure: a proof that passes when
   it is confused is not a proof.

   Run: node atlas-tools/prove-preview-only-containment.mjs                  */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

/* fileURLToPath, not url.pathname: this repository's path contains a space
   and arrives percent-encoded otherwise. */
const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const REGISTER = path.join(HERE, 'preview-only-suppliers.json');
const ROBOTS = ['noindex', 'nofollow', 'noarchive', 'nosnippet', 'noimageindex'];

let failed = 0;
let confused = 0;
const ok = w => console.log('    PASS   ' + w);
const bad = (w, d) => { console.log('    FAIL   ' + w); if (d) console.log('           ' + d); failed++; };
const cannot = (w, d) => { console.log('    ERROR  ' + w); if (d) console.log('           ' + d); confused++; };

console.log('PREVIEW-ONLY CONTAINMENT PROOF');
console.log('='.repeat(76));

/* ---- the register ------------------------------------------------------- */
let suppliers;
try {
  const doc = JSON.parse(fs.readFileSync(REGISTER, 'utf8'));
  suppliers = doc.suppliers || [];
} catch (e) {
  console.log('  ERROR  the preview-only register could not be read: ' + e.message);
  console.log('CONTAINMENT NOT ESTABLISHED');
  process.exit(2);
}
if (!suppliers.length) {
  /* An empty register is not a pass. It is indistinguishable from a register
     that was emptied, and this proof would then protect nothing while
     printing success. */
  console.log('  ERROR  the register lists no suppliers, so this proof would');
  console.log('         pass without checking anything. That is a failure.');
  console.log('CONTAINMENT NOT ESTABLISHED');
  process.exit(2);
}

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

/* Every external image reference on every page, once. Comments are stripped
   because they are not published -- a note explaining the rights position
   must not itself read as a violation. */
const pageImages = new Map();
for (const f of htmlFiles) {
  const html = fs.readFileSync(f, 'utf8').replace(/<!--[\s\S]*?-->/g, ' ');
  const urls = new Set();
  for (const m of html.matchAll(/<img\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
  for (const m of html.matchAll(/<source\b[^>]*?\bsrcset\s*=\s*["']([^"']+)["']/gi)) {
    m[1].split(',').forEach(p => urls.add(p.trim().split(/\s+/)[0]));
  }
  for (const m of html.matchAll(/url\(\s*["']?(https?:\/\/[^"')]+)["']?\s*\)/gi)) urls.add(m[1]);
  for (const m of html.matchAll(/<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)["']/gi)) urls.add(m[1]);
  pageImages.set(path.relative(ROOT, f), [...urls]);
}

/* ---- the runtime payloads, found once ---------------------------------- */
const payloads = [];
(function find(d, depth) {
  if (depth > 3) return;
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    if (e.name.startsWith('.') || e.name === 'node_modules') continue;
    const full = path.join(d, e.name);
    if (e.isDirectory()) find(full, depth + 1);
    /* EVERY atlas-*.json, not a hand-picked few: a check that cannot see the
       Results pool it is protecting is worse than none. */
    else if (/^atlas-.*\.json$/i.test(e.name)) payloads.push(full);
  }
})(ROOT, 0);
if (!payloads.length) cannot('no runtime Atlas payload was found; C6 cannot run');

const sitemaps = fs.readdirSync(ROOT).filter(f => /sitemap.*\.xml$/i.test(f));
if (!sitemaps.length) cannot('no sitemap was found; C4 cannot run');

let records = null;
try {
  records = JSON.parse(fs.readFileSync(path.join(ROOT, 'image-rights-records.json'), 'utf8')).records || [];
} catch (e) {
  cannot('image-rights-records.json could not be read; C5 cannot run', e.message);
}

/* ---- per supplier ------------------------------------------------------ */
for (const s of suppliers) {
  console.log('');
  console.log('  ' + s.name + '  — preview-only, nothing granted');
  console.log('  ' + '-'.repeat(72));

  const mine = u => {
    let p;
    try { p = new URL(u); } catch { return false; }
    const host = p.hostname.toLowerCase().replace(/^www\./, '');
    if (host === s.site_host) return true;
    return (s.image_hosts || []).some(h =>
      host === String(h.host).toLowerCase().replace(/^www\./, '')
      && (!h.path_prefix || p.pathname.startsWith(h.path_prefix)));
  };

  /* C1 . no imagery anywhere */
  const carriers = [];
  for (const [page, urls] of pageImages) {
    for (const u of urls) if (mine(u)) carriers.push(page + ' → ' + u.slice(0, 64));
  }
  if (carriers.length) {
    bad('no ' + s.name + ' imagery appears on any deployed page',
        carriers.join('; ') + '. They replied PREVIEW, not YES. UNKNOWN is '
        + 'not GRANTED, and the rights gate would refuse these.');
  } else {
    const scoped = (s.image_hosts || []).map(h => h.host + (h.path_prefix || '')).join(', ');
    ok('no imagery on any of ' + pageImages.size + ' deployed pages ('
       + s.site_host + (scoped ? ' and ' + scoped : '') + ' checked)');
  }

  /* C2, C3, C7 . the preview itself */
  const pagePath = path.join(ROOT, s.page);
  if (!fs.existsSync(pagePath)) {
    cannot(s.page + ' is not in the tree',
           'the proof cannot check a hold on a page that is not there.');
  } else {
    const src = fs.readFileSync(pagePath, 'utf8');
    const missing = ROBOTS.filter(d => !src.includes(d));
    if (missing.length) {
      bad('the preview carries all five robots directives',
          'missing: ' + missing.join(', ') + '. A preview without these is a '
          + 'published page.');
    } else {
      ok('noindex, nofollow, noarchive, nosnippet, noimageindex');
    }

    if (!src.includes('href="https://www.' + s.site_host + '/')
        && !src.includes('href="https://' + s.site_host + '/')) {
      bad('the preview links back to ' + s.site_host,
          'every figure on the page is their published information, so the '
          + 'page must link to where it came from. A mention in prose is not '
          + 'a link.');
    } else {
      ok('links back to ' + s.site_host);
    }

    if (!src.includes(s.credit)) {
      bad('the preview credits ' + s.credit + ' for the published facts it uses');
    } else {
      ok('credits ' + s.credit);
    }

    const visible = src
      .replace(/<!--[\s\S]*?-->/g, ' ')
      .replace(/<style\b[\s\S]*?<\/style>/gi, ' ')
      .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
      .replace(/\s+/g, ' ')
      .toLowerCase();
    const claimed = (s.forbidden_claims || []).filter(c => visible.includes(c));
    if (claimed.length) {
      bad('the preview makes no claim their evidence does not support',
          'found: ' + claimed.join(', '));
    } else {
      ok('none of the ' + (s.forbidden_claims || []).length
         + ' claims their site does not support');
    }
  }

  /* C4 . no sitemap invites anyone in */
  const slug = s.page.replace(/\.html$/, '');
  const listed = sitemaps.filter(f =>
    fs.readFileSync(path.join(ROOT, f), 'utf8').toLowerCase().includes(slug));
  if (listed.length) bad('no sitemap lists the preview', listed.join(', ') + ' does.');
  else if (sitemaps.length) ok('absent from all ' + sitemaps.length + ' sitemap(s)');

  /* C5 . no grant was written that was never given */
  if (records) {
    const row = records.find(r =>
      String(r.permitted_domain || '').toLowerCase().includes(s.site_host)
      || String(r.organisation_name || '').toLowerCase() === s.name.toLowerCase());
    if (!row) {
      ok('no rights record exists, which is correct: nothing was granted');
    } else if (/^Granted/i.test(String(row.permission_outcome || ''))) {
      bad('no live grant is recorded for ' + s.name,
          'the record reads ' + JSON.stringify(row.permission_outcome)
          + '. They replied PREVIEW, not YES. A live-grant outcome here is '
          + 'PREVIEW converted into GRANTED.');
    } else {
      ok('a record exists but its outcome is not a live grant ('
         + row.permission_outcome + ')');
    }
  }

  /* C6 . the public Results path is untouched */
  if (payloads.length) {
    const needles = [s.site_host.toLowerCase()]
      .concat((s.image_hosts || []).map(h => String(h.path_prefix || '').toLowerCase()).filter(Boolean));
    const leaky = payloads.filter(p => {
      const t = fs.readFileSync(p, 'utf8').toLowerCase();
      return needles.some(n => t.includes(n));
    });
    if (leaky.length) {
      bad('no runtime payload reaches ' + s.name,
          leaky.map(p => path.relative(ROOT, p)).join(', '));
    } else {
      ok('absent from all ' + payloads.length
         + ' runtime payloads; the Results pool cannot reach them');
    }
  }
}

console.log('');
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
console.log('CONTAINED — ' + suppliers.length + ' preview-only supplier(s) carry '
  + 'their published facts, none of their imagery, and nothing has reached '
  + 'the public journey.');
process.exit(0);
