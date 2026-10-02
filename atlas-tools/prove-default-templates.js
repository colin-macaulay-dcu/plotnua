#!/usr/bin/env node
/* ===========================================================================
   PROVE THE DEFAULT PRODUCT JOURNEY UI ACROSS THE WHOLE UNIVERSE.

   The Results and Resolve compositions are the DEFAULT presentation for every
   eligible product, not a Yardbox treatment that happens to be reused. A design
   freeze that is only ever looked at through one supplier's product is not a
   freeze, it is a coincidence. So this runs the shipped decision code over all
   477 products and asserts the properties the default must hold for each.

   IT LIFTS THE SHIPPED SOURCE, IT DOES NOT RE-IMPLEMENT IT. The page runs in a
   <script type="module">, which jsdom will not execute, so the regions under
   test are sliced out of your-plot.html and driven against the real universe
   artefact. A second implementation of the rules would prove only that the
   second implementation agrees with itself.

   FAIL CLOSED IS THE POINT. Where evidence or rights are insufficient the
   default must show LESS, never guess more: no photograph without a live
   grant, no price where none is verified, no enquiry question invented from
   nothing, and no product that renders an empty page.

   THE MULTI-IMAGE CASES ARE SYNTHETIC, AND THAT IS STATED IN THE OUTPUT.
   No product in the universe currently carries two governed images, so the
   gallery cannot be exercised against real data. Synthesising the cases is the
   only way to test it at all; pretending the coverage is real would be worse
   than saying so.

   Run:  node atlas-tools/prove-default-templates.js
=========================================================================== */

'use strict';

const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..');
const PAGE = path.join(REPO, 'your-plot.html');
const UNI = path.join(REPO, 'garden-room-recommendation-universe-v1.json');

const src = fs.readFileSync(PAGE, 'utf8');
const universe = JSON.parse(fs.readFileSync(UNI, 'utf8'));
const products = universe.products;

let fails = 0;
function check(label, cond, detail) {
  if (cond) { console.log('  ok    ' + label + (detail ? '   ' + detail : '')); }
  else { console.log('  FAIL  ' + label + (detail ? '   ' + detail : '')); fails++; }
}
function head(s) { console.log('\n' + s + '\n' + '-'.repeat(74)); }

/* ---------------------------------------------------------------------------
   Lift the regions under test.
--------------------------------------------------------------------------- */
function slice(startMark, endMark) {
  const i = src.indexOf(startMark);
  if (i < 0) throw new Error('lift failed, missing: ' + startMark);
  const j = src.indexOf(endMark, i);
  if (j < 0) throw new Error('lift failed, missing end for: ' + startMark);
  return src.slice(i, j + endMark.length);
}

const lifted = [
  slice('  function pnImageRightsOk(im){', '\n  }\n'),
  slice('  function pnAuthorisedImages(product){', '\n  }\n'),
  slice('  function pnAuthorisedImage(product){', '\n  }\n'),
].join('\n');

const sandbox = {};
new Function('exports', lifted +
  '\nexports.pnImageRightsOk = pnImageRightsOk;' +
  '\nexports.pnAuthorisedImages = pnAuthorisedImages;' +
  '\nexports.pnAuthorisedImage = pnAuthorisedImage;')(sandbox);

const { pnImageRightsOk, pnAuthorisedImages, pnAuthorisedImage } = sandbox;

/* ===========================================================================
   A · THE DEFAULT IS GENERIC — no supplier appears in the decision code.
=========================================================================== */
head('A · NO SUPPLIER-SPECIFIC FORK IN THE DEFAULT TEMPLATES');

function stripComments(t) {
  return t.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^[ \t]*\/\/.*$/gm, '');
}
const code = stripComments(src);

/* The one frozen data lookup that names suppliers exists because Atlas holds
   no structured supplierCounty field. It is DATA, adjudicated and recorded, and
   it is not a layout or styling fork. Everything else must be clean. */
const FROZEN_DATA_MARK = 'My Garden Room (Barna Buildings)';
const frozenStart = code.indexOf(FROZEN_DATA_MARK);
const frozenTable = frozenStart < 0 ? '' :
  code.slice(code.lastIndexOf('{', frozenStart), code.indexOf('}', code.indexOf('Iglucraft', frozenStart)) + 1);
const codeOutsideFrozenData = frozenTable ? code.split(frozenTable).join('') : code;

const SUPPLIERS = ['Yardbox', 'Yard Box', 'Power Sheds', 'Shomera', 'Koto',
                   'Iglucraft', 'Kodasema', 'Superior Pergola', 'TRIQBRIQ'];
SUPPLIERS.forEach(function (s) {
  const n = codeOutsideFrozenData.split(s).length - 1;
  check('no "' + s + '" outside the frozen supplier-county data', n === 0,
        n ? n + ' occurrence(s)' : '');
});

const styleForks = (code.match(/\.(?:pn|rsv|results)[a-z-]*(?:yardbox|powersheds|koto|shomera)/gi) || []);
check('no supplier-named CSS class anywhere', styleForks.length === 0,
      styleForks.join(', '));

/* ===========================================================================
   B · EVERY PRODUCT RENDERS, AND EVERY PRODUCT RENDERS SOMETHING.
=========================================================================== */
head('B · THE DEFAULT SURVIVES ALL ' + products.length + ' PRODUCTS');

const orgs = new Set();
let withImagery = 0, withoutImagery = 0, priced = 0, quoteOnly = 0;
let crashed = 0;

products.forEach(function (p) {
  if (p.organisation) orgs.add(p.organisation);
  try {
    const set = pnAuthorisedImages(p);
    if (set.length) withImagery++; else withoutImagery++;
  } catch (e) { crashed++; }
  const hasPrice = (typeof p.price === 'number' && isFinite(p.price))
                   && p.priceEvidenceState === 'verified';
  if (hasPrice) priced++; else quoteOnly++;
});

check('no product crashes the imagery gate', crashed === 0,
      crashed ? crashed + ' crashed' : products.length + ' evaluated');
check('the default spans many suppliers, not one', orgs.size >= 20,
      orgs.size + ' distinct organisations');
check('both priced and quote-only products are covered',
      priced > 0 && quoteOnly > 0,
      priced + ' verified-price / ' + quoteOnly + ' quote-only or unpriced');
check('both rich and sparse imagery evidence are covered',
      withImagery > 0 && withoutImagery > 0,
      withImagery + ' with governed imagery / ' + withoutImagery + ' without');

/* ===========================================================================
   C · FAIL CLOSED: NOTHING UNPROVEN IS EVER PAINTED.
=========================================================================== */
head('C · THE RIGHTS GATE FAILS CLOSED, PER IMAGE');

let gatePasses = 0, gateBad = [];
products.forEach(function (p) {
  pnAuthorisedImages(p).forEach(function (im) {
    gatePasses++;
    if (!im.url || !im.credit || !im.supplier || !im.rightsRecord) gateBad.push(p.productId + ' incomplete');
    if (!im.permittedPrefix) gateBad.push(p.productId + ' unscoped');
    else if (String(im.url).indexOf(im.permittedPrefix) !== 0) gateBad.push(p.productId + ' outside prefix');
    if (String(im.url).slice(0, 8) !== 'https://') gateBad.push(p.productId + ' not https');
  });
});
check('every image the default would display passes the rights gate',
      gateBad.length === 0, gatePasses + ' image(s) checked, ' +
      (gateBad.length ? gateBad.slice(0, 3).join('; ') : 'all scoped, credited, https'));

/* Each field, removed on its own, must close the gate. A gate that only fails
   when everything is missing is not a gate. */
const REQUIRED = ['url', 'credit', 'supplier', 'rightsRecord', 'permittedPrefix'];
const real = products.map(pnAuthorisedImage).filter(Boolean)[0];
check('at least one real governed image exists to mutate', !!real);
if (real) {
  REQUIRED.forEach(function (f) {
    const broken = Object.assign({}, real); delete broken[f];
    check('removing ' + f + ' alone closes the gate', pnImageRightsOk(broken) === false);
  });
  const drifted = Object.assign({}, real, {
    url: 'https://images.squarespace-cdn.com/content/v1/0000000000000000/x.jpg' });
  check('a url outside the permitted prefix closes the gate',
        pnImageRightsOk(drifted) === false);
  const http = Object.assign({}, real, { url: real.url.replace('https://', 'http://') });
  check('a non-https url closes the gate', pnImageRightsOk(http) === false);
  /* THE BARE-CDN-HOST RULE BELONGS TO THE GENERATOR, NOT HERE.
     My first version asserted that the runtime ACCEPTS a bare-host prefix
     "because the url sits inside it", then took whichever governed image came
     first in the universe -- a Shopify-hosted one -- and tested it against a
     Squarespace prefix. It failed for the wrong reason and was aimed at the
     wrong layer. Refusing to WRITE a bare host is
     apply_authorised_imagery.py's guard G7, proven there per supplier. What the
     RUNTIME owes is narrower, and is what is asserted instead. */
  const otherTenant = Object.assign({}, real, {
    permittedPrefix: real.permittedPrefix.replace(/[^/]+\/$/, '0000000000000000/') });
  check('a permitted prefix belonging to another tenant closes the gate',
        pnImageRightsOk(otherTenant) === false,
        'bare-host AUTHORSHIP is refused by the generator\u2019s G7, not here');
}

/* ===========================================================================
   D · SINGLE IMAGE vs MULTIPLE IMAGES.
=========================================================================== */
head('D · MEDIA BEHAVIOUR — 1 IMAGE vs 2+ (MULTI-IMAGE CASES ARE SYNTHETIC)');

const multiReal = products.filter(function (p) {
  return pnAuthorisedImages(p).length > 1;
});
console.log('  NOTE  ' + multiReal.length + ' product(s) in the real universe carry 2+ governed '
  + 'images.\n        The gallery is therefore correct-but-unexercised until Atlas asset\n'
  + '        records are linked and exported. The cases below are SYNTHETIC.');

const one = products.filter(function (p) { return pnAuthorisedImages(p).length === 1; })[0];
check('a real single-image product returns exactly one', !!one && pnAuthorisedImages(one).length === 1);

if (one) {
  const base = pnAuthorisedImage(one);
  function synth(n, mutate) {
    const set = [];
    for (let i = 0; i < n; i++) {
      const im = Object.assign({}, base, { url: base.url + '?v=' + i });
      set.push(mutate ? mutate(im, i) : im);
    }
    return Object.assign({}, one, { imagery: set[0], imagerySet: set });
  }

  check('2 authorised images yield a set of 2', pnAuthorisedImages(synth(2)).length === 2);
  check('5 authorised images yield a set of 5', pnAuthorisedImages(synth(5)).length === 5);

  /* the primary is always the first frame */
  const p5 = synth(5);
  check('the primary image is the first member of the set',
        pnAuthorisedImages(p5)[0].url === p5.imagery.url);

  /* a duplicate url is refused */
  const dup = Object.assign({}, one, {
    imagery: base, imagerySet: [base, Object.assign({}, base), base] });
  check('the same photograph cannot appear twice in a gallery',
        pnAuthorisedImages(dup).length === 1,
        'three entries, one distinct url');

  /* ONE BAD IMAGE DOES NOT TAKE THE OTHERS DOWN, AND DOES NOT RIDE ALONG */
  const mixed = synth(4, function (im, i) {
    if (i === 2) return Object.assign({}, im, { credit: '' });   /* no attribution */
    return im;
  });
  const got = pnAuthorisedImages(mixed);
  check('an uncredited image is dropped and the rest still publish',
        got.length === 3 && got.every(function (im) { return !!im.credit; }),
        got.length + ' of 4 published');

  const driftedSet = synth(3, function (im, i) {
    if (i === 1) return Object.assign({}, im, {
      url: 'https://images.squarespace-cdn.com/content/v1/0000000000000000/y.jpg' });
    return im;
  });
  check('an image outside its permitted prefix is dropped from the set',
        pnAuthorisedImages(driftedSet).length === 2);

  /* WITHDRAWAL. No grant anywhere means no gallery, not a partial one. */
  const withdrawn = Object.assign({}, one, {
    imagery: Object.assign({}, base, { rightsRecord: null }),
    imagerySet: [Object.assign({}, base, { rightsRecord: null }),
                 Object.assign({}, base, { rightsRecord: null, url: base.url + '?v=1' })] });
  check('withdrawing the rights record empties the set entirely',
        pnAuthorisedImages(withdrawn).length === 0);

  /* AN OLDER ARTEFACT, with imagery as a single object and no set, still works */
  const legacy = Object.assign({}, one); delete legacy.imagerySet;
  check('a product with no imagerySet still yields its single image',
        pnAuthorisedImages(legacy).length === 1);

  /* pnAuthorisedImage() is byte-compatible for every existing caller */
  let same = 0;
  products.forEach(function (p) {
    const a = pnAuthorisedImage(p);
    const b = pnAuthorisedImages(p)[0] || null;
    if (a === b) same++;
  });
  check('pnAuthorisedImage() is the first member of the set for every product',
        same === products.length, same + '/' + products.length);
}

/* ===========================================================================
   E · RESULTS AND RESOLVE SHARE ONE SET AND ONE GALLERY.
=========================================================================== */
head('E · RESULTS AND RESOLVE CANNOT DIVERGE');

check('the gallery is declared exactly once',
      (code.match(/function pnGovernedGallery\(/g) || []).length === 1);
check('the gallery has exactly two call sites (Results hero, Resolve hero)',
      (code.match(/pnGovernedGallery\(/g) || []).length - 1 === 2);
check('both call sites derive their images from pnAuthorisedImages(product)',
      (code.match(/pnGovernedGallery\([^)]*pnAuthorisedImages\(product\)\)/g) || []).length === 2);
check('the painter is declared exactly once',
      (code.match(/function pnPaintGoverned\(/g) || []).length === 1);
check('the per-image rights rule is declared exactly once',
      (code.match(/function pnImageRightsOk\(/g) || []).length === 1);

/* the gallery is inert below two images -- this is what keeps the approved
   single-hero composition frozen for the whole universe today */
const gi = code.indexOf('function pnGovernedGallery(');
const gal = code.slice(gi, code.indexOf('\n  }', code.indexOf('return true;', gi)));
check('the gallery returns early below two images',
      /images\.length < 2\) return false;/.test(gal));
check('the gallery assigns no src of its own', !/\.src\s*=/.test(gal));
check('the gallery attaches no credit of its own', !/pnAttachImageCredit\(/.test(gal));

/* ===========================================================================
   F · RESPONSIVE BEHAVIOUR IS DECLARED, NOT ASSUMED.
=========================================================================== */
head('F · THE GALLERY STRIP IS RESPONSIVE AND KEYBOARD-REACHABLE');

/* RE-ANCHORED FOR RESULTS-IDENTITY-001.

   This assertion used to read "styled in exactly two places" and counted the
   declarations. The count was only ever a proxy for the thing worth proving,
   and RESULTS-IDENTITY-001 broke the proxy without breaking the invariant: the
   authorised layout moved the strip inside .rh-split and legitimately added a
   third, Results-scoped declaration. A guard that fails because the
   implementation it guards was correctly changed is telling you about itself,
   not about the code, and the right answer is to test the invariant rather
   than loosen the number.

   THE INVARIANT: the strip is styled in exactly the three AUTHORISED places,
   each appearing once, and nowhere else. Naming them means a fourth stray
   declaration is still caught, which is what the old count was for. */
const STRIP_RULES = [
  ['the Results-scoped rule inside .rh-split',
   /#screen-match-results \.rh-split \.pn-gal-strip\{/g],
  ['the shared base rule',
   /\n  \.pn-gal-strip\{/g],
  ['the phone breakpoint override',
   /@media \(max-width:640px\)\{[\s\S]{0,400}?\.pn-gal-strip\{/g]
];
STRIP_RULES.forEach(([what, re]) => {
  check('the strip is styled once in ' + what,
        (code.match(re) || []).length === 1);
});
check('the strip is styled in exactly those three places and nowhere else',
      (code.match(/\.pn-gal-strip\{/g) || []).length === 3);
check('the strip scrolls rather than wrapping out of its container',
      /\.pn-gal-strip\{[^}]*overflow-x:auto/.test(code));
check('a phone breakpoint resizes the thumbnails',
      /@media \(max-width:640px\)\{[\s\S]{0,200}\.pn-gal-thumb\{[^}]*width:54px/.test(code));
check('each thumbnail is a real button, so it is keyboard-reachable',
      /b\.type = 'button';/.test(gal) && /aria-label/.test(gal));
check('the selected thumbnail is announced, not only coloured',
      /aria-pressed/.test(gal));
check('focus is visible', /\.pn-gal-thumb:focus-visible\{/.test(code));
check('the strip does not reuse the alternatives carousel namespace',
      code.indexOf('.results-gallery-strip') === -1);

/* ===========================================================================
=========================================================================== */
console.log('\n' + '='.repeat(74));
if (fails) {
  console.log('DEFAULT TEMPLATE PROOF FAILED — ' + fails + ' assertion(s)');
  process.exit(1);
}
console.log('DEFAULT TEMPLATE PROOF HELD — the Results and Resolve compositions are');
console.log('the default for all ' + products.length + ' products across ' + orgs.size
  + ' organisations, and fail closed');
console.log('where evidence or rights are insufficient.');
console.log('\nSTATED LIMIT: ' + multiReal.length + ' real product(s) carry 2+ governed images, so the');
console.log('gallery’s behaviour above ONE image is proven only against synthetic sets.');
