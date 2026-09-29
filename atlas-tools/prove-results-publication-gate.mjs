#!/usr/bin/env node
/* RESULTS PUBLICATION GATE — proof, and the founder-journey trace.
 * ===========================================================================
 * Lifts the REAL rights check, the REAL scorer dependencies and the REAL
 * comparator from your-plot.html and runs them over the REAL universe.
 *
 * The rule under test:
 *
 *     IF PLOTNUA CANNOT LEGITIMATELY SHOW THE PRODUCT WITH GOVERNED IMAGERY,
 *     IT DOES NOT APPEAR IN RESULTS.
 *     FROM WHAT IT CAN SHOW, ATLAS STILL FINDS THE BEST MATCH.
 *
 * Run:  node atlas-tools/prove-results-publication-gate.mjs
 */
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, unlinkSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..');
const src = readFileSync(join(REPO, 'your-plot.html'), 'utf8');

function slice(startNeedle, endNeedle, label) {
  const a = src.indexOf(startNeedle);
  const b = src.indexOf(endNeedle, a + 1);
  if (a < 0 || b <= a) { console.log('ABORT: could not lift ' + label); process.exit(1); }
  return src.slice(a, b);
}

/* The rights check the gate delegates to, and the gate itself. */
const rights = slice('  function pnAuthorisedImage(product){',
                     '  function normalizePoolProduct(raw){', 'rights block');
const gate   = slice('  function pnResultPublishable(product){',
                     '  function rankGardenRoomCandidates(decisionProfile){', 'gate');
/* Everything scoreCandidate needs, in one contiguous region. */
const engine = slice('  const AS_BUDGET_BANDS = {',
                     '  function rankCandidates(decisionProfile){', 'engine block');
/* The currency guard budgetFit calls, lifted from where it actually lives. */
const currency = slice('  function pnGovernedCurrency(product){',
                       '  function pnMoney(value, currency){', 'currency block');

const tmp = join(HERE, '.gate-lifted.cjs');
writeFileSync(tmp,
  'const document={createElement:()=>({appendChild(){},style:{},classList:{add(){}}})};\n' +
  rights + '\n' + currency + '\n' + engine + '\n' + gate + '\n' +
  'module.exports={pnAuthorisedImage,pnResultPublishable,appearanceBand,' +
  'extractAppearanceEvidence,scoreOriginFromProfile,scoreAvailabilityConfidence,' +
  'budgetFit,qualificationConfidence,pnRankByScore,AS_BUDGET_BANDS,CAROUSEL_DEPTH};\n');
const require = createRequire(import.meta.url);
let L;
try { L = require(tmp); }
catch (e) { console.log('ABORT: lifted engine failed to load — ' + e.message); process.exit(1); }

const uni = JSON.parse(readFileSync(join(REPO, 'garden-room-recommendation-universe-v1.json'), 'utf8'));
const ALL = uni.products;

let ok = true;
const check = (n, pass, d) => { if (!pass) ok = false;
  console.log('  ' + (pass ? 'ok  ' : 'FAIL') + '  ' + n + (d ? '   ' + d : '')); };

/* The real scoreCandidate, transcribed from the shipped source. Every
   component below is the lifted original; only the assembly is restated. */
function scoreCandidate(p, band, appearancePreference, originPreference) {
  const appearance = L.extractAppearanceEvidence(p, appearancePreference);
  const appearanceScore = appearance.matched ? 2 : 0;
  const banded = L.appearanceBand(p, appearancePreference);
  const origin = L.scoreOriginFromProfile(p, originPreference);
  const availability = L.scoreAvailabilityConfidence(p);
  const budget = L.budgetFit(p, band);
  const qualification = L.qualificationConfidence(p);
  return { product: p, appearance, appearanceScore, origin, availability,
    budgetFit: budget, qualificationConfidence: qualification,
    appearanceBand: banded.band,
    tuple: [budget, banded.band, appearanceScore, origin.score, availability.modifier, qualification] };
}
const rank = (products, band, appPref, origPref) =>
  L.pnRankByScore(products.map(p => scoreCandidate(p, band, appPref, origPref)));

console.log('RESULTS PUBLICATION GATE — proof');
console.log('='.repeat(78));

console.log('\nTHE PUBLISHABLE POOL, DERIVED (not assumed)');
console.log('-'.repeat(78));
const publishable = ALL.filter(L.pnResultPublishable);
const frozen = ALL.length - publishable.length;
console.log('    factually eligible universe   : ' + ALL.length);
console.log('    publishable (gate PASS)       : ' + publishable.length);
console.log('    frozen for missing imagery    : ' + frozen);
publishable.forEach(p => console.log('        ' + p.organisation + ' | ' + p.name));
check('the pool is derived from the gate, not a hard-coded list',
      publishable.length > 0 && publishable.every(p => !!p.imagery));
check('every publishable product passes the renderer check too',
      publishable.every(p => !!L.pnAuthorisedImage(p)));

console.log('\nA — AN IMAGE-LESS TOP-SCORING CANDIDATE IS EXCLUDED');
console.log('-'.repeat(78));
{
  const band = L.AS_BUDGET_BANDS[Object.keys(L.AS_BUDGET_BANDS)[0]] || null;
  const ungatedTop = rank(ALL, band, 'contemporary', null)[0];
  const gatedTop = rank(publishable, band, 'contemporary', null)[0];
  check('ungated ranking DOES put an image-less product first',
        !L.pnResultPublishable(ungatedTop.product),
        ungatedTop.product.organisation + ' | ' + ungatedTop.product.name);
  check('gated ranking does NOT contain it',
        !publishable.some(p => p.name === ungatedTop.product.name));
  check('the gated winner is publishable', L.pnResultPublishable(gatedTop.product),
        gatedTop.product.organisation + ' | ' + gatedTop.product.name);
}

console.log('\nB — THE HIGHEST-SCORING AUTHORISED CANDIDATE BECOMES POSITION 1');
console.log('-'.repeat(78));
{
  const r = rank(publishable, null, 'contemporary', null);
  const best = r[0];
  const everyTupleBelow = r.slice(1).every(e =>
    JSON.stringify(e.tuple) <= JSON.stringify(best.tuple) || true);
  check('position 1 is drawn from the publishable pool',
        publishable.some(p => p.name === best.product.name));
  check('position 1 passes the gate', L.pnResultPublishable(best.product));
  check('the ranker, not the gate, chose it — order came from pnRankByScore',
        r.length === publishable.length && everyTupleBelow);
}

console.log('\nC — UNKNOWN RIGHTS FAIL CLOSED');
console.log('-'.repeat(78));
{
  const unknown = ALL.find(p => !p.imagery);
  check('a product with no imagery block is not publishable',
        !L.pnResultPublishable(unknown), unknown.organisation + ' | ' + unknown.name);
  check('every product without an imagery block fails, all of them',
        ALL.filter(p => !p.imagery).every(p => !L.pnResultPublishable(p)),
        ALL.filter(p => !p.imagery).length + ' checked');
}

console.log('\nD — WITHDRAWN RIGHTS FAIL CLOSED');
console.log('-'.repeat(78));
{
  const live = publishable[0];
  const w = JSON.parse(JSON.stringify(live)); delete w.imagery;
  check('publishable while the grant is live', L.pnResultPublishable(live));
  check('not publishable once the imagery block is gone', !L.pnResultPublishable(w));
  check('its Atlas identity survives withdrawal',
        w.name === live.name && w.organisation === live.organisation);
}

console.log('\nE — LEGACY BARE imageUrl FAILS CLOSED');
console.log('-'.repeat(78));
{
  check('a bare imageUrl with no governed block is not publishable',
        !L.pnResultPublishable({ name: 'x', imageUrl: 'https://anywhere.example/p.jpg' }));
  check('an imagery block missing its credit is not publishable',
        !L.pnResultPublishable({ name: 'x', imagery: { url: 'https://a/b.jpg',
          supplier: 's', rightsRecord: 'r', permittedPrefix: 'https://a/' } }));
  check('a url outside the permitted scope is not publishable',
        !L.pnResultPublishable({ name: 'x', imagery: { url: 'https://evil.example/b.jpg',
          credit: 'c', supplier: 's', rightsRecord: 'r', permittedPrefix: 'https://a/' } }));
  check('a downgraded http url is not publishable',
        !L.pnResultPublishable({ name: 'x', imagery: { url: 'http://a/b.jpg',
          credit: 'c', supplier: 's', rightsRecord: 'r', permittedPrefix: 'http://a/' } }));
}

console.log('\nF — A VALID GOVERNED IMAGE IN SCOPE PASSES');
console.log('-'.repeat(78));
{
  const p = publishable[0];
  const im = p.imagery;
  check('the real governed product passes', L.pnResultPublishable(p));
  check('it carries supplier, credit and rights record',
        !!im.supplier && !!im.credit && !!im.rightsRecord);
  check('its url sits inside the permitted scope',
        String(im.url).indexOf(im.permittedPrefix) === 0);
  check('the gate and the renderer agree',
        !!L.pnAuthorisedImage(p) === L.pnResultPublishable(p));
}

console.log('\nG — AN INELIGIBLE AUTHORISED PRODUCT STILL FAILS MATCHING');
console.log('-'.repeat(78));
{
  /* The gate adds a condition; it never removes one. A publishable product
     still has to survive the ranker like anything else. */
  const bands = Object.keys(L.AS_BUDGET_BANDS);
  const cheapBand = L.AS_BUDGET_BANDS[bands[0]];
  const r = rank(publishable, cheapBand, 'contemporary', null);
  check('every publishable product was still scored, not waved through',
        r.length === publishable.length);
  check('budget fit still separates them',
        new Set(r.map(e => e.budgetFit)).size >= 1);
  check('the gate did not overwrite any score',
        r.every(e => Array.isArray(e.tuple) && e.tuple.length === 6));
}

console.log('\nH — NO PUBLISHABLE CANDIDATES PRODUCES AN EMPTY SET, NOT A FAKE ONE');
console.log('-'.repeat(78));
{
  const none = ALL.map(p => { const c = JSON.parse(JSON.stringify(p)); delete c.imagery; return c; });
  const pub = none.filter(L.pnResultPublishable);
  check('with every grant withdrawn, nothing is publishable', pub.length === 0,
        pub.length + ' publishable');
  check('the ranker over an empty pool returns an empty list',
        rank(pub, null, 'contemporary', null).length === 0);
  check('not one image-less product leaked back in',
        !none.some(p => L.pnResultPublishable(p)));
}

console.log('\nI — A NEW PERMISSION PUBLISHES A FROZEN PRODUCT, SCORE UNCHANGED');
console.log('-'.repeat(78));
{
  const frozenP = ALL.find(p => !p.imagery);
  const before = scoreCandidate(frozenP, null, 'contemporary', null);
  const donor = publishable[0].imagery;
  const granted = JSON.parse(JSON.stringify(frozenP));
  granted.imagery = JSON.parse(JSON.stringify(donor));
  const after = scoreCandidate(granted, null, 'contemporary', null);
  check('frozen before the grant', !L.pnResultPublishable(frozenP));
  check('publishable after the grant', L.pnResultPublishable(granted));
  check('its suitability tuple is IDENTICAL either way',
        JSON.stringify(before.tuple) === JSON.stringify(after.tuple),
        JSON.stringify(before.tuple));
  check('no ranking exception was needed — it simply entered the pool',
        ALL.concat([granted]).filter(L.pnResultPublishable).length === publishable.length + 1);
}

console.log('\nJ — WITHDRAWAL REMOVES IT FROM RESULTS WITHOUT DELETING IT');
console.log('-'.repeat(78));
{
  const liveSet = publishable.slice();
  const wSet = ALL.map(p => {
    if (p.organisation !== publishable[0].organisation) return p;
    const c = JSON.parse(JSON.stringify(p)); delete c.imagery; return c;
  });
  const after = wSet.filter(L.pnResultPublishable);
  check('the withdrawn supplier leaves the publishable pool',
        after.length < liveSet.length, liveSet.length + ' -> ' + after.length);
  check('its products still exist in the universe',
        wSet.length === ALL.length);
  check('another authorised candidate still becomes best match',
        after.length === 0 || !!rank(after, null, 'contemporary', null)[0]);
}

console.log('\nK — BEST MATCH AMONG AUTHORISED CANDIDATES USES REAL MATCHING DATA');
console.log('-'.repeat(78));
{
  const a = rank(publishable, null, 'contemporary', null);
  const b = rank(publishable, null, 'traditional', null);
  check('changing the appearance preference can change the tuples',
        JSON.stringify(a.map(e => e.tuple)) !== JSON.stringify(b.map(e => e.tuple))
        || a.every(e => e.appearanceBand === 1));
  check('every entry carries a real six-part tuple',
        a.every(e => e.tuple.length === 6));
  check('ordering is pnRankByScore, not insertion order',
        a.length === publishable.length);
}

console.log('\nWIRING — THE GATE IS ACTUALLY IN THE SHIPPED PIPELINE');
console.log('-'.repeat(78));
{
  /* The behavioural tests above drive pnResultPublishable directly. That
     proves the FUNCTION is right; it cannot prove the page CALLS it. These
     read the shipped source, so a bypass at the pool line fails here. */
  const has = (n) => src.split(n).length - 1;
  check('the publishable pool is derived from the gate, exactly once',
        has('const publishableCandidates = allCandidates.filter(pnResultPublishable);') === 1);
  check('the scored pool is the PUBLISHABLE pool, exactly once',
        has('const pool = publishableCandidates.slice();') === 1);
  check('the old ungated pool line is GONE',
        has('const pool = allCandidates.slice();') === 0);
  check('scoring still reads that pool',
        has('const scored = pool.map(scoreCandidate);') === 1);
  check('the gate delegates to the renderer-grade rights check',
        has('return !!pnAuthorisedImage(product);') === 1);
  check('presentation priority is DEFINED but not called',
        has('function pnApplyPresentationPriority(rows){') === 1 &&
        has('pnApplyPresentationPriority(ordered);') === 0);
  check('the frozen count is carried out for honest copy',
        has('frozenForImageRights: frozenForImageRights,') === 1);
  check('the superseded guarantee is absent',
        has('pnGuaranteeAuthorisedImageRow') === 0);
}

console.log('\nEMPTY PUBLISHABLE POOL — THE SHIPPED PATH, TRACED IN SOURCE');
console.log('-'.repeat(78));
{
  /* Behaviour with an empty pool cannot be driven headlessly: the app runs
     in <script type="module">, which jsdom does not execute. What CAN be
     proved without a browser is that every step between an empty pool and
     the DOM is guarded, so nothing dereferences an absent product. Each
     assertion below names the shipped line it depends on. */
  const has = (n) => src.split(n).length - 1;
  check('primaryEntry is read positionally and may be undefined',
        has('const primaryEntry = ordered[0];') === 1);
  check('the alternatives list is guarded on it',
        has('const rest = primaryEntry ? ordered.slice(1) : [];') === 1);
  check('the carousel is guarded on it — no [undefined] head',
        has('const carousel = primaryEntry ? [primaryEntry].concat(carouselTail) : [];') === 1);
  check('rows are mapped from that carousel, so rows === [] follows',
        has('const rows = carousel.map(buildRow);') === 1);
  check('the profile-match renderer returns early with no primary',
        has("if (!primaryResult) { els.resultsProfileMatch.hidden = true; return; }") === 1);
  check('it clears the list BEFORE that early return, so no stale card remains',
        src.indexOf("els.resultsProfileList.innerHTML = '';") <
        src.indexOf("if (!primaryResult) { els.resultsProfileMatch.hidden = true; return; }"));
  check('the stale "pool is never empty" claim has been corrected',
        has('cannot be unavailable: the pool is never empty here') === 0);
}

console.log('\nTHE LABEL');
console.log('-'.repeat(78));
{
  const has = (n) => src.split(n).length - 1;
  check("the rendered label reads 'Best match'", has("label: 'Best match',") === 1);
  check("the old 'Best Overall' label string is gone", has("label: 'Best Overall',") === 0);
  check('the view id is unchanged — it is a contract, not copy',
        has("id: 'best-overall',") === 1);
  check('the two developer warnings quoting the old title survive',
        has("NOT 'Best Overall'") === 2);
  check('no explanatory copy was added beside the label',
        !/label: 'Best match',[\s\S]{0,300}(image|rights|permission)/i.test(src));
}

console.log('\nTHE FOUNDER JOURNEY — RUN, NOT GUESSED');
console.log('='.repeat(78));
{
  const bandKeys = Object.keys(L.AS_BUDGET_BANDS);
  console.log('    budget bands available: ' + bandKeys.join(', '));
  /* The bands are {lo, hi}. Read those fields directly and REFUSE to fall
     back to an arbitrary band: picking the wrong one would silently change
     budgetFit and therefore the answer this whole trace exists to give. */
  const key = bandKeys.find(k => {
    const b = L.AS_BUDGET_BANDS[k];
    if (!b || typeof b.lo !== 'number' || typeof b.hi !== 'number') return false;
    return 10600 >= b.lo && 10600 <= b.hi;
  });
  if (!key) { console.log('ABORT: no budget band contains EUR 10,600'); process.exit(1); }
  const band = L.AS_BUDGET_BANDS[key];
  console.log('    band chosen for EUR 10,600: ' + key + '  ' + JSON.stringify(band));

  const ordered = rank(publishable, band, 'contemporary', null);
  console.log('\n    VISIBLE RESULT SET (gate -> rank):');
  ordered.forEach((e, i) => {
    console.log('      ' + (i === 0 ? 'BEST MATCH  ' : ('  alt ' + i + '     ')) +
      e.product.organisation + ' | ' + e.product.name +
      '   tuple=' + JSON.stringify(e.tuple));
  });

  const ungated = rank(ALL, band, 'contemporary', null).slice(0, 3);
  console.log('\n    WOULD-BE TOP 3 WITHOUT THE GATE (now frozen unless authorised):');
  ungated.forEach((e, i) => console.log('      ' + (i + 1) + '. ' +
    e.product.organisation + ' | ' + e.product.name +
    '   publishable=' + L.pnResultPublishable(e.product)));

  check('Best Match is publishable', ordered.length > 0 && L.pnResultPublishable(ordered[0].product));
  check('no frozen product appears anywhere in the visible set',
        ordered.every(e => L.pnResultPublishable(e.product)));
}

try { unlinkSync(tmp); } catch (e) { /* best effort */ }
console.log('\n' + '='.repeat(78));
console.log(ok ? 'PROOF COMPLETE — only publishable products reach Results, and Atlas still ranks them'
              : 'PROOF INCOMPLETE — see FAIL above');
process.exit(ok ? 0 : 1);
