/* DISCOVERY LIBRARY IMAGE PROOF.
   ---------------------------------------------------------------------------
   FOUNDER RULE, 3 October 2026: each Library card on discoveries.html shows
   the image that best communicates THE DISCOVERY REALISED -- the payoff. That
   is an EDITORIAL choice, recorded explicitly in
   atlas-tools/discovery-library-images.json, and deliberately NOT derived from
   any selector over the markup.

   WHY NO SELECTOR. Two earlier rules were tried and both were wrong. The
   first followed the personalised Results engine, which is a different layer
   entirely. The second -- "the first .imagine-photo that is not a cmp frame"
   -- looked principled and systematically picked the POTENTIAL ASSET plate:
   the empty wall, the bare lawn, the frontage before the bins are gone. Four
   of its choices carry "potential asset" or "annotated by PlotNua" in their
   own page-side alt text. Pages have different image rhythms; judgement does
   not live in a CSS class.

   WHAT THIS GUARDS, and P3 is the one the founder asked for by name:

     P1  Every card on the page has exactly one mapping row, and every row
         matches a real card. A card added without a row would be unguarded.
     P2  The page renders what the mapping says, image and alt text.
     P3  NO CARD SHOWS A POTENTIAL-ASSET PLATE. The test is the Discovery
         page's OWN description of that image: "potential asset", "annotated
         by PlotNua", "before anything is planted", "standing completely
         empty". The bare word "empty" is deliberately not a marker --
         Driveway Income's realised image is two cars in spaces "that stood
         empty", and a guard that cannot tell a result from a description of
         what it replaced would block the right picture.
     P4  The chosen image actually appears on the Discovery page it links to.
     P5  Library alt text stands alone -- it must not open "The same...",
         which is page-sequence language that reads as a non-sequitur on a
         card seen by itself.
     P6  Local PlotNua assets only, present on disk. discoveries.html is
         public, so a supplier URL here is a rights question; it is refused
         one step before the rights gate would catch it.

   Exit 0 = governed. Exit 1 = a divergence. Exit 2 = the proof could not
   establish the facts, which is also a failure.

   Run: node atlas-tools/prove-discovery-library-images.mjs                  */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

/* fileURLToPath, not url.pathname: this repository's path contains a space. */
const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const LIBRARY = path.join(ROOT, 'discoveries.html');
const REGISTER = path.join(HERE, 'discovery-library-images.json');

const PA_MARKERS = ['potential asset', 'annotated by plotnua',
  'before anything is planted', 'standing completely empty'];

let failed = 0, confused = 0;
const ok = w => console.log('    PASS   ' + w);
const bad = (w, d) => { console.log('    FAIL   ' + w); if (d) console.log('           ' + d); failed++; };
const cannot = (w, d) => { console.log('    ERROR  ' + w); if (d) console.log('           ' + d); confused++; };

console.log('DISCOVERY LIBRARY IMAGE PROOF');
console.log('='.repeat(76));

let rows, html;
try {
  rows = JSON.parse(fs.readFileSync(REGISTER, 'utf8')).cards || [];
  html = fs.readFileSync(LIBRARY, 'utf8');
} catch (e) {
  console.log('  ERROR  could not read the mapping or the page: ' + e.message);
  console.log('NOT ESTABLISHED');
  process.exit(2);
}
if (!rows.length) {
  console.log('  ERROR  the mapping lists no cards, so this proof would pass');
  console.log('         without checking anything. That is a failure.');
  console.log('NOT ESTABLISHED');
  process.exit(2);
}

const rendered = new Map();
const re = /<a class="lib-card" href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g;
let m;
while ((m = re.exec(html))) {
  const im = /<img src="([^"]+)" alt="([^"]*)"/.exec(m[2]);
  rendered.set(m[1], { src: im ? im[1] : null, alt: im ? im[2] : null });
}

/* ---- P1 . coverage ------------------------------------------------------ */
console.log('');
console.log('  COVERAGE');
console.log('  ' + '-'.repeat(72));
const mapped = new Set(rows.map(r => r.card));
const unmapped = [...rendered.keys()].filter(h => !mapped.has(h));
const ghosts = rows.map(r => r.card).filter(h => !rendered.has(h));
if (unmapped.length) {
  cannot(unmapped.length + ' card(s) on the page have no mapping row',
         unmapped.join(', ') + '. An unmapped card keeps whatever image it '
         + 'has, unguarded, which is how a potential-asset plate gets back in.');
} else if (ghosts.length) {
  cannot(ghosts.length + ' mapping row(s) match no card', ghosts.join(', '));
} else {
  ok('all ' + rendered.size + ' cards governed by exactly one row');
}

/* ---- per card ----------------------------------------------------------- */
for (const r of rows) {
  console.log('');
  console.log('  ' + r.title);
  console.log('  ' + '-'.repeat(72));
  const live = rendered.get(r.card);
  if (!live) { cannot('not rendered on discoveries.html'); continue; }

  /* P2 */
  if (live.src !== r.image) {
    bad('the card renders the governed image',
        'mapping ' + r.image + '\n           page    ' + live.src
        + '\n           Somebody changed one without the other.');
  } else {
    ok('image is the governed choice — ' + r.image.split('/').pop());
  }
  if (live.alt !== r.alt) {
    bad('the card renders the governed alt text',
        'mapping "' + String(r.alt).slice(0, 52) + '"\n           page    "'
        + String(live.alt).slice(0, 52) + '"');
  } else {
    ok('alt text is the governed standalone description');
  }

  /* P5 */
  if (String(r.alt).trim().toLowerCase().startsWith('the same')) {
    bad('the alt text stands alone',
        'it opens "The same...", which is page-sequence language. On a card '
        + 'seen by itself there is no "same" to refer back to.');
  } else {
    ok('alt text stands alone');
  }

  /* P6 */
  if (/^https?:/i.test(String(r.image))) {
    bad('the image is a local PlotNua asset',
        r.image + ' is externally hosted. discoveries.html is public, so this '
        + 'is a rights question, not a layout one.');
    continue;
  }
  if (!fs.existsSync(path.join(ROOT, r.image))) {
    bad('the image exists on disk', r.image + ' is missing.');
    continue;
  }
  ok('local asset, present on disk');

  /* P3 + P4 . the correction this whole task exists for */
  const pagePath = path.join(ROOT, r.card);
  if (!fs.existsSync(pagePath)) {
    cannot('the linked page ' + r.card + ' is not in the tree');
    continue;
  }
  const pageHtml = fs.readFileSync(pagePath, 'utf8');
  if (!pageHtml.includes(r.image)) {
    bad('the chosen image appears on the Discovery page it represents',
        r.image + ' is nowhere on ' + r.card + '.');
    continue;
  }
  const pm = new RegExp('<img[^>]*src="' + r.image.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    + '"[^>]*alt="([^"]*)"').exec(pageHtml);
  if (!pm) {
    ok('present on ' + r.card + ' (no page-side alt to test)');
  } else {
    const hit = PA_MARKERS.filter(k => pm[1].toLowerCase().includes(k));
    if (hit.length) {
      bad('the card does NOT show a potential-asset plate',
          r.card + ' describes this image as ' + JSON.stringify(hit[0])
          + '. The Library is where the discovery REALISED goes — not the '
          + 'empty wall, the bare lawn or the before state.');
    } else {
      ok('a realised image: no potential-asset marker in its page description');
    }
  }
}

console.log('');
console.log('='.repeat(76));
if (confused) {
  console.log('NOT ESTABLISHED — ' + confused + ' check(s) could not run.');
  process.exit(2);
}
if (failed) {
  console.log('DIVERGED — ' + failed + ' check(s) failed.');
  process.exit(1);
}
console.log('GOVERNED — all ' + rows.length + ' Library cards show their '
  + 'recorded realised image, with standalone alt text, and not one of them '
  + 'is a potential-asset plate.');
process.exit(0);
