#!/usr/bin/env node
/* ===========================================================================
   PROVE THE MANUAL-ADD RESOLVER — "Found something yourself?"

   THE TWO DEFECTS THIS EXISTS TO KEEP FIXED, as observed by the founder:

     https://www.yardbox.co.uk/models   created a product called "Models" and
                                        said Atlas had no record of it
     Bothán                             did not resolve at all, although Atlas
                                        holds a Yardbox Bothán

   IT LIFTS THE SHIPPED SOURCE, IT DOES NOT RE-IMPLEMENT IT. The resolver's own
   functions are sliced out of your-plot.html and driven against the real
   datasets. A second implementation would prove only that it agrees with
   itself.

   THE SEVEN CASES THE BRIEF NAMES ARE ALL HERE, plus a sweep asserting that
   every product either source already knows still resolves to ITSELF -- the
   regression that matters, because a resolver that finds new things by losing
   old ones has not been improved.

   WHY A FIXTURE. atlas-recognition-pool.json is a 27 August export of 516
   records; Atlas now holds 1,187 and the export contains no Yardbox record at
   all. The eight records in fixtures/manual-add-atlas-records.json were read
   verbatim from live Atlas so the Bothán and /models cases can be proved
   before the export is refreshed. Every such assertion is labelled FIXTURE in
   the output: this file does not let a fixture masquerade as live coverage.

   Run:  node atlas-tools/prove-manual-add-resolver.js
=========================================================================== */

'use strict';

const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..');
const PAGE = path.join(REPO, 'your-plot.html');
const POOL = path.join(REPO, 'atlas-recognition-pool.json');
const UNI = path.join(REPO, 'garden-room-recommendation-universe-v1.json');
const FIX = path.join(__dirname, 'fixtures', 'manual-add-atlas-records.json');

const src = fs.readFileSync(PAGE, 'utf8');
const shippedPool = JSON.parse(fs.readFileSync(POOL, 'utf8'));
const universe = JSON.parse(fs.readFileSync(UNI, 'utf8')).products;
const fixture = JSON.parse(fs.readFileSync(FIX, 'utf8')).records;

let fails = 0;
function check(label, cond, detail) {
  console.log((cond ? '  ok    ' : '  FAIL  ') + label + (detail ? '   ' + detail : ''));
  if (!cond) fails++;
}
function head(s) { console.log('\n' + s + '\n' + '-'.repeat(76)); }

/* ---------------------------------------------------------------------------
   Lift the resolver.
--------------------------------------------------------------------------- */
function slice(start, end) {
  const i = src.indexOf(start);
  if (i < 0) throw new Error('lift failed, missing: ' + start);
  const j = src.indexOf(end, i);
  if (j < 0) throw new Error('lift failed, no end for: ' + start);
  return src.slice(i, j + end.length);
}
function fn(sig) { return slice(sig, '\n  }\n'); }

function constant(re) {
  const m = src.match(re);
  if (!m) throw new Error('lift failed, missing constant: ' + re);
  return m[1];
}

const LIFTED = [
  'const BYO_PROSE_MARKERS = ' + constant(/const BYO_PROSE_MARKERS = (\/.*?\/i);/) + ';',
  'const BYO_PAIR_SEPARATORS = ' + constant(/const BYO_PAIR_SEPARATORS = (\[[^\]]*\]);/) + ';',
  constant(/(  const PN_COLLECTION_SLUGS = Object\.freeze\(\[[\s\S]*?\]\);)/),
  'let atlasRecognitionPool = [];',
  'let UNIVERSE = [];',
  'function getActiveAtlasPool(){ return UNIVERSE; }',
  fn('  function normalizeAtlasUrl(url){'),
  fn('  function normalizeAtlasName(name){'),
  fn('  function byoLooksLikeProse(text){'),
  fn('  function byoParseProductUrl(raw){'),
  fn('  function byoIdentityFromUrl(u){'),
  fn('  function byoSplitPair(text){'),
  fn('  function byoUniverseRecords(){'),
  fn('  function pnCollectionSlug(u){'),
  fn('  function pnHostOf(value){'),
  fn('  function pnCanonicalRecords(){'),
  fn('  function pnUniqueRows(rows){'),
  fn('  function pnAgreedSupplier(rows){'),
  fn('  function pnNameWithoutOrg(rn, ro){'),
  fn('  function pnContainsWholeName(haystack, needle){'),
  fn('  function pnResolveManualAdd(raw){'),
  fn('  function pnSpokenProductName(match){')
].join('\n');

const box = {};
new Function('exports', LIFTED +
  '\nexports.resolve = pnResolveManualAdd;' +
  '\nexports.spoken = pnSpokenProductName;' +
  '\nexports.slug = pnCollectionSlug;' +
  '\nexports.setSources = function(pool, uni){ atlasRecognitionPool = pool; UNIVERSE = uni; };'
)(box);

const uniRows = universe.map(function (p) {
  return Object.assign({}, p, { id: p.productId || p.id });
});

/* The live state: the shipped export plus the universe. */
box.setSources(shippedPool, uniRows);

/* ===========================================================================
   1 · THE COLLECTION-PAGE RULE IS GENERIC
=========================================================================== */
head('1 · A COLLECTION PAGE IS NEVER A PRODUCT (no supplier is named)');

const GENERIC = ['https://any-maker.example/models',
                 'https://any-maker.example/products',
                 'https://any-maker.example/shop',
                 'https://any-maker.example/collection',
                 'https://any-maker.example/garden-rooms',
                 'https://any-maker.example/cabins',
                 'https://any-maker.example/'];
GENERIC.forEach(function (u) {
  const r = box.resolve(u);
  const named = (r.outcome === 'unknown' && r.name) ? r.name : null;
  check('no product invented from ' + u.replace('https://any-maker.example', ''),
        !named, named ? 'invented "' + named + '"' : r.outcome);
});
check('a specific-looking slug IS still a usable identity for an unknown maker',
      box.resolve('https://any-maker.example/sunrise-studio-5m').outcome === 'unknown',
      'a generic word is the thing we refuse, not every slug');

/* ===========================================================================
   2 · NO REGRESSION — everything already known still resolves to itself
=========================================================================== */
head('2 · EVERY PRODUCT EITHER SOURCE KNOWS STILL RESOLVES TO ITSELF');

(function () {
  const seen = Object.create(null);
  const rows = [];
  shippedPool.forEach(function (r) {
    if (!seen[r.id]) { seen[r.id] = 1; rows.push({ id: r.id, name: r.name }); }
  });
  uniRows.forEach(function (p) {
    if (!seen[p.id]) { seen[p.id] = 1; rows.push({ id: p.id, name: p.name }); }
  });
  let same = 0, wrong = 0, lost = 0;
  const wrongEx = [];
  rows.forEach(function (r) {
    const res = box.resolve(r.name);
    if (res.outcome === 'product' && res.match.id === r.id) same++;
    else if (res.outcome === 'product') {
      wrong++;
      if (wrongEx.length < 3) wrongEx.push(r.name + ' -> ' + res.match.name);
    } else lost++;
  });
  check('no product resolves to a DIFFERENT product', wrong === 0,
        wrong ? wrongEx.join(' | ') : rows.length + ' names tested');
  check('every known product resolves to itself', same === rows.length,
        same + '/' + rows.length + (lost ? ('  ' + lost + ' unresolved') : ''));
})();

/* ===========================================================================
   3 · THE SEVEN CASES THE BRIEF NAMES
=========================================================================== */
head('3 · THE SEVEN CASES  (FIXTURE = proved against records read from live\n'
     + '    Atlas but not yet in the shipped export)');

/* The fixture joins the shipped export, exactly as the refreshed export will. */
box.setSources(shippedPool.concat(fixture), uniRows);

function resolved(input) {
  const r = box.resolve(input);
  return r.outcome === 'product' ? r.match.id : null;
}

/* a · a known Atlas product by exact URL */
check('FIXTURE  exact product URL resolves to that product',
      resolved('https://www.yardbox.co.uk/bothan') === 'recPermX1OwzI2o1Y');

/* b · a known product by product + supplier, in both orders, same id */
const b1 = resolved('Yardbox Bothán');
const b2 = resolved('Bothán Yardbox');
check('FIXTURE  "Yardbox Bothán" resolves', b1 === 'recPermX1OwzI2o1Y', b1 || 'unresolved');
check('FIXTURE  "Bothán Yardbox" resolves to the SAME product id',
      b2 === b1 && b1 !== null, b2 || 'unresolved');

/* c · a unique product name on its own */
check('FIXTURE  a unique product name alone resolves',
      resolved('Vancouver') === 'reckMDqp4tVjAjM7b');

/* d · a supplier collection URL */
(function () {
  const r = box.resolve('https://www.yardbox.co.uk/models');
  check('FIXTURE  a collection URL offers the models, it does not invent one',
        r.outcome === 'choose' && r.candidates.length === 3,
        r.outcome + (r.candidates ? ' / ' + r.candidates.length + ' candidates' : ''));
  check('FIXTURE  and it names the supplier it found',
        r.supplier === 'Yardbox', r.supplier || '(none)');
  check('FIXTURE  no candidate is called "Models"',
        (r.candidates || []).every(function (c) { return c.name !== 'Models'; }));
})();

/* e · an unknown external product URL */
(function () {
  const r = box.resolve('https://some-unknown-maker.example/the-oakfield-6m');
  check('an unknown external product is kept, labelled as unknown',
        r.outcome === 'unknown', r.outcome);
  check('and it carries the page it came from',
        !!r.url && !!r.host, r.host || '(no host)');
})();

/* f · an ambiguous product name */
(function () {
  const r = box.resolve('Bothán');
  check('FIXTURE  an ambiguous name asks which one, it does not pick',
        r.outcome === 'choose' && r.candidates.length === 4,
        r.outcome + ' / ' + ((r.candidates || []).length) + ' candidates across '
        + (new Set((r.candidates || []).map(function (c) { return c.organisation; }))).size
        + ' makers');
  check('FIXTURE  and it offers no supplier name it cannot stand over',
        r.supplier === '', 'candidates come from more than one maker');
})();

/* g · a product Atlas knows that is OUTSIDE the recommendation universe */
(function () {
  const inUniverse = uniRows.some(function (p) { return p.id === 'recFek9ErsnKt6uKN'; });
  const r = box.resolve('Yardbox Aspect Modular Homes');
  check('FIXTURE  the test product really is outside the recommendation set',
        !inUniverse);
  check('FIXTURE  Atlas still knows it — eligibility is not identity',
        r.outcome === 'product' && r.match.id === 'recFek9ErsnKt6uKN',
        r.outcome);
})();

/* ===========================================================================
   4 · THE ACKNOWLEDGEMENT SAYS THE RIGHT NAME
=========================================================================== */
head('4 · WHAT THE HOMEOWNER IS TOLD');

check('the spoken name drops a supplier prefix the sentence already carries',
      box.spoken({ name: 'Yardbox Bothán', organisation: 'Yardbox' }) === 'Bothán',
      '"Found it — Bothán by Yardbox", not "Yardbox Bothán by Yardbox"');
check('a name that does not start with its supplier is left alone',
      box.spoken({ name: 'The Vancouver', organisation: 'Yardbox' }) === 'The Vancouver');

/* THE MODULE SCRIPT ONLY, AND WITH EVERY KIND OF COMMENT REMOVED.
   My first version stripped JS comments from the WHOLE FILE and then searched
   for internal vocabulary. It matched inside an HTML <!-- --> comment, which
   is neither code nor anything a homeowner reads, and reported a leak that did
   not exist. The page is markup AND script, so a check about shipped strings
   has to say which of the two it means. */
const MODULE = (src.match(/<script type="module">([\s\S]*?)<\/script>/) || [])[1] || '';
const code = MODULE
  .replace(/\/\*[\s\S]*?\*\//g, '')
  .replace(/^[ \t]*\/\/.*$/gm, '');
check('the old "no verified record" claim is gone from the code',
      code.indexOf('Atlas has no verified record') === -1);
/* SCOPED TO THE SURFACE THIS FLOW OWNS, which is what the brief asks about.

   My first version searched EVERY string literal in the module and reported two
   leaks that were not leaks: 'garden-room-recommendation-universe-v1.json' is a
   filename in a fetch call, and 'EVIDENCE TIER' is a term inside
   PN_CONSIDER_WITHHOLD -- the filter whose whole job is to keep that vocabulary
   AWAY from homeowners. A check that cannot tell a suppression list from a leak
   is measuring the wrong thing. */
(function () {
  const a = code.indexOf('function pnSpokenProductName(');
  const b = code.indexOf('els.addYourOwnForm.addEventListener');
  const flow = code.slice(a, b);
  const spoken = (flow.match(/'[^'\\]{10,}'/g) || []);
  ['universe', 'canonical record', 'evidence tier', 'verification pipeline',
   'recognition pool', 'atlas record'].forEach(function (term) {
    const hit = spoken.filter(function (s) {
      return s.toLowerCase().indexOf(term) !== -1;
    })[0];
    check('nothing this flow says uses the term "' + term + '"', !hit, hit || '');
  });
  check('and the page still actively withholds that vocabulary elsewhere',
        code.indexOf('PN_CONSIDER_WITHHOLD') !== -1,
        'the suppression filter is intact');
})();

/* ===========================================================================
   5 · THE RESOLVER IS GENERIC
=========================================================================== */
head('5 · NO SUPPLIER IS NAMED IN THE RESOLVER');

(function () {
  const i = code.indexOf('function pnResolveManualAdd(');
  const body = code.slice(i, code.indexOf('function classifyExternalProductInput', i));
  ['Yardbox', 'Yard Box', 'Power Sheds', 'Shomera', 'Koto', 'Iglucraft',
   'INTUMODULAR', 'yardbox', 'intumodular'].forEach(function (s) {
    check('the resolver never names "' + s + '"', body.indexOf(s) === -1);
  });
  check('the collection-slug list names no supplier either',
        !/yardbox|shomera|powersheds|intumodular/i.test(
          constant(/(  const PN_COLLECTION_SLUGS = Object\.freeze\(\[[\s\S]*?\]\);)/)));
})();

/* ===========================================================================
   6 · THE SHIPPED EXPORT IS STALE, AND THAT IS STATED
=========================================================================== */
head('6 · WHAT THE SHIPPED EXPORT CANNOT DO YET');

box.setSources(shippedPool, uniRows);
(function () {
  const live = box.resolve('Bothán');
  console.log('  NOTE  against the SHIPPED export alone, "Bothán" -> '
    + live.outcome + '.');
  console.log('        atlas-recognition-pool.json holds ' + shippedPool.length
    + ' records from 27 August; Atlas held 1,187 when this was written.');
  console.log('        Run .github/scripts/generate_recognition_pool.py with a');
  console.log('        token to close that gap. The resolver is already correct;');
  console.log('        it cannot find what the file it searches does not carry.');
  check('the stale export does NOT cause a wrong product to be returned',
        live.outcome !== 'product',
        'failing closed is the correct behaviour for a gap in the data');
})();

console.log('\n' + '='.repeat(76));
if (fails) {
  console.log('MANUAL-ADD RESOLVER PROOF FAILED — ' + fails + ' assertion(s)');
  process.exit(1);
}
console.log('MANUAL-ADD RESOLVER PROOF HELD');
console.log('A collection page is never a product; an ambiguous name is a question,');
console.log('never a guess; and a product Atlas knows is known whether or not it is');
console.log('currently recommended.');
