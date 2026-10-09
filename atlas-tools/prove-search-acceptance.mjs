/* PLOTNUA SEARCH · ACCEPTANCE + HOSTILE LEAK SUITE
 * ===========================================================================
 * Drives the SHIPPED matcher in ../search.js against the SHIPPED index in
 * ../search-index-v1.json. Not a copy of either: a test that exercises a
 * reimplementation proves the reimplementation.
 *
 * PART A   the eight representative queries, against the exact acceptance
 *          behaviour in governance/SEARCH-V1-CONTRACT.md §11
 * PART B   the hostile leak suite. Knowing the exact hidden name must NOT make
 *          Search reveal it. Run against the FULL set of private previews on
 *          disk, not a sample, so adding a preview later cannot quietly escape
 *          the test.
 * PART C   privacy statics: the runtime must contain no persistence, no
 *          analytics and no term-bearing network call
 *
 *   node atlas-tools/prove-search-acceptance.mjs
 * ========================================================================= */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const require = createRequire(import.meta.url);

const S = require(path.join(ROOT, 'search.js'));
const INDEX = JSON.parse(fs.readFileSync(path.join(ROOT, 'search-index-v1.json'), 'utf8'));
const RAW = fs.readFileSync(path.join(ROOT, 'search-index-v1.json'), 'utf8');
const RUNTIME = fs.readFileSync(path.join(ROOT, 'search.js'), 'utf8');

let pass = 0, fail = 0;
const check = (name, cond, detail) => {
  if (cond) { pass++; console.log(`  [PASS] ${name}`); }
  else { fail++; console.log(`  [FAIL] ${name}\n         ${detail ?? ''}`); }
};

const q = (s) => S.search(INDEX, s);

/* ORGANISATION IDENTITY. Comparing supplier names naively produced three false
   leak reports on the first run, and all three were this mistake:
     "Yard Box" (preview title) vs "Yardbox" (universe)
     "Quinn Offsite" (pool) vs "Quinn Offsite Ltd" (universe)
   Both pairs are ONE organisation under a naming variant, and in both cases the
   record Search returned came from the published universe, not from a preview.
   Spaces, punctuation and corporate suffixes are stripped for identity only —
   never for display. */
const ident = (s) => S.normalise(s)
  .replace(/\b(ltd|limited|ireland|ie|uk|co|company|group|studios?)\b/g, '')
  .replace(/[^a-z0-9]/g, '');

/* LEAK SCANNER. A result object echoes res.query back, so scanning the whole
   object flags the homeowner's OWN typing as a leak: searching for
   "auroom-wellness-preview.html" put that string in the result because the user
   typed it, not because Search revealed it. Only RECORDS can leak. */
const route = (rec) => {
  if (!rec) { return ''; }
  if (rec.route) { return rec.route; }
  if (rec.type === 'product' && INDEX.routes && INDEX.routes.product) {
    return INDEX.routes.product.replace('{id}', String(rec.id).slice(5));
  }
  return '';
};
const recordsBlob = (r) => JSON.stringify({
  possibility: r.groups.possibility, supplier: r.groups.supplier,
  product: r.groups.product, journey: r.groups.journey
});
const names = (rs) => rs.map((r) => r.name || r.title);

console.log('\n  PLOTNUA SEARCH · ACCEPTANCE + HOSTILE LEAK SUITE');
console.log(`  index: ${INDEX.counts.possibility} possibilities, ` +
            `${INDEX.counts.product} products, ${INDEX.counts.supplier} suppliers, ` +
            `${INDEX.counts.journey} journeys`);
console.log(`  universe: ${INDEX.sourceUniverseSha256.slice(0, 16)}…\n`);

/* ====================================================== PART A · ACCEPTANCE */
console.log('  PART A · THE EIGHT REPRESENTATIVE QUERIES\n');

/* --- A1 Powersheds: 1 supplier + 3 products, the founder's original gap ---- */
{
  const r = q('Powersheds');
  check('A1a Powersheds returns exactly 1 supplier', r.counts.supplier === 1,
    JSON.stringify(names(r.groups.supplier)));
  check('A1b Powersheds returns exactly 3 products', r.counts.product === 3,
    JSON.stringify(names(r.groups.product)));
  const prices = r.groups.product.map((p) => p.price).sort((a, b) => a - b);
  check('A1c the three prices are 6129 / 6959 / 9199',
    JSON.stringify(prices) === JSON.stringify([6129, 6959, 9199]), JSON.stringify(prices));
  check('A1d all three are WITH_CAVEAT',
    r.groups.product.every((p) => p.tier === 'WITH_CAVEAT'),
    JSON.stringify(r.groups.product.map((p) => p.tier)));
  check('A1e the supplier is named Powersheds, not "Power Sheds"',
    r.groups.supplier[0].name === 'Powersheds', r.groups.supplier[0].name);
}

/* --- A2 garden office: grouped, never flat -------------------------------- */
{
  const r = q('garden office');
  check('A2a garden office finds a large product set (>100)', r.counts.product > 100,
    String(r.counts.product));
  check('A2b products are GROUPED by supplier, not flat',
    r.productsBySupplier.length > 1 &&
    r.productsBySupplier.every((g) => g.shown.length <= 3),
    `${r.productsBySupplier.length} groups`);
  check('A2c every group exposes a total count',
    r.productsBySupplier.every((g) => typeof g.total === 'number' && g.total >= g.shown.length));
  check('A2d hidden remainders are counted, not dropped',
    r.productsBySupplier.reduce((n, g) => n + g.shown.length + g.hidden, 0) === r.counts.product);
  check('A2e possibilities are present and listed first', r.counts.possibility >= 1,
    String(r.counts.possibility));
  check('A2f "garden office" needs NO synonym — it matches productType natively',
    r.mappedByTopic.length === 0, JSON.stringify(r.mappedByTopic));
}

/* --- A3 price intent ------------------------------------------------------- */
{
  const r = q('garden room under €20,000');
  check('A3a the price cap parses to 20000', r.priceCap === 20000, String(r.priceCap));
  check('A3a2 the capped result is NOT empty (so A3b/A3c cannot pass vacuously)',
    r.counts.product > 50, String(r.counts.product));
  check('A3b every product returned is priced and under the cap',
    r.groups.product.every((p) => typeof p.price === 'number' && p.price <= 20000));
  check('A3c unpriced products are excluded, not shown as free',
    r.groups.product.every((p) => p.price > 0));
  /* Variant forms must parse to the same cap, or the fix is only skin deep. */
  check('A3e variant price forms all parse to 20000',
    [ 'garden room under 20000', 'garden room under \u20ac20,000',
      'garden room up to \u20ac20k', 'garden room below 20,000' ]
      .every((s) => q(s).priceCap === 20000),
    JSON.stringify([ 'garden room under 20000', 'garden room under \u20ac20,000',
      'garden room up to \u20ac20k', 'garden room below 20,000' ]
      .map((s) => q(s).priceCap)));
  const capless = q('garden room');
  check('A3d the cap genuinely restricts the set',
    r.counts.product < capless.counts.product,
    `${r.counts.product} with cap vs ${capless.counts.product} without`);
}

/* --- A4 solar battery: zero products, the right Discovery ----------------- */
{
  const r = q('solar battery');
  check('A4a solar battery returns ZERO products', r.counts.product === 0,
    JSON.stringify(names(r.groups.product)));
  check('A4b solar battery returns ZERO suppliers', r.counts.supplier === 0);
  check('A4c it returns The House as a Power Station via the governed map',
    names(r.groups.possibility).includes('The House as a Power Station'),
    JSON.stringify(names(r.groups.possibility)));
  check('A4d the answer came from the topic map, not prose luck',
    r.mappedByTopic.length === 1, JSON.stringify(r.mappedByTopic));
  const r2 = q('solar');
  check('A4e bare "solar" maps the same way',
    names(r2.groups.possibility).includes('The House as a Power Station'));
}

/* --- A5 artist: the productType hit, and no retired Discovery ------------- */
{
  const r = q('artist');
  check('A5a artist returns exactly 1 product', r.counts.product === 1,
    JSON.stringify(names(r.groups.product)));
  check('A5b and it is Hutsmith Type III Cabin',
    r.groups.product[0] && r.groups.product[0].name === 'Hutsmith Type III Cabin',
    r.groups.product[0] && r.groups.product[0].name);
  check('A5c matched on productType "Artist Studio / Writer\'s Retreat Cabin"',
    /Artist Studio/i.test(r.groups.product[0].productType),
    r.groups.product[0].productType);
  check('A5d art possibilities are returned too', r.counts.possibility >= 2,
    JSON.stringify(names(r.groups.possibility)));
  check('A5e the RETIRED Artist Studio Discovery is NOT returned',
    !names(r.groups.possibility).some((n) => /^artist studio$/i.test(String(n).trim())) &&
    !JSON.stringify(r).includes('discovery-artist-studio'),
    JSON.stringify(names(r.groups.possibility)));
}

/* --- A6 spare garden: the map corrects a measured wrong answer ------------ */
{
  const r = q('spare garden');
  check('A6a spare garden returns The Borrowed Garden',
    names(r.groups.possibility).includes('The Borrowed Garden'),
    JSON.stringify(names(r.groups.possibility)));
  check('A6b it does NOT return Open Your Home to Art',
    !names(r.groups.possibility).includes('Open Your Home to Art'));
  check('A6c it does NOT return about.html',
    !JSON.stringify(r).includes('about.html'));
  check('A6d exactly one possibility is offered', r.counts.possibility === 1,
    String(r.counts.possibility));
}

/* --- A7 parking: a NARROWING map ------------------------------------------ */
{
  const r = q('parking');
  const n = names(r.groups.possibility);
  check('A7a parking returns Hidden Cars', n.includes('Hidden Cars'), JSON.stringify(n));
  check('A7b parking returns Driveway Income', n.includes('Driveway Income'));
  check('A7c it does NOT return The Hidden Bins', !n.includes('The Hidden Bins'));
  check('A7d it does NOT return Your Home On Screen', !n.includes('Your Home On Screen'));
  check('A7e exactly two possibilities — the map narrowed 7 to 2',
    r.counts.possibility === 2, String(r.counts.possibility));
}

/* --- A8 sauna: HONEST EMPTY ---------------------------------------------- */
{
  const r = q('sauna');
  check('A8a sauna returns Garden Retreat',
    names(r.groups.possibility).includes('Garden Retreat'),
    JSON.stringify(names(r.groups.possibility)));
  check('A8b sauna returns ZERO products', r.counts.product === 0,
    JSON.stringify(names(r.groups.product)));
  check('A8c sauna returns ZERO suppliers', r.counts.supplier === 0,
    JSON.stringify(names(r.groups.supplier)));
  check('A8d the possibility-only flag is set', r.possibilityOnly === true);
  check('A8e Auroom Wellness is nowhere in the answer',
    !JSON.stringify(r).toLowerCase().includes('auroom'));
  check('A8f the 4 incidental features mentions did not leak: no MyCabin, ' +
        'Iglucraft or Koto product',
    !names(r.groups.product).length, JSON.stringify(names(r.groups.product)));
}

/* ============================= PART A2 · SEARCH -> PRODUCT ROUTING ========
 * The founder's exact acceptance cases. The previous build found the right
 * product and then sent the homeowner to the Eircode landing screen; these
 * assert the find is not thrown away. */
console.log('\n  PART A2 · SEARCH \u2192 PRODUCT ROUTING (founder acceptance cases)\n');

const PAGE = fs.readFileSync(path.join(ROOT, 'your-plot.html'), 'utf8');

{
  const r = q('Powersheds');

  /* CASE 1 — the SUPPLIER expands inside Search and never navigates. */
  const sup = r.groups.supplier[0];
  check('P1a the Powersheds supplier record carries NO route, so it cannot ' +
        'restart the Eircode journey', !sup.route, JSON.stringify(sup.route));
  check('P1b expansion yields exactly its 3 governed products',
    (sup.__products || []).length === 3,
    String((sup.__products || []).length));
  check('P1c the expansion control is a labelled button, not a link',
    /<button[^>]*class="pns-expand"[^>]*aria-expanded="false"/.test(S.renderResults(r)));
  check('P1d the supplier NAME is rendered as text, not an anchor',
    /<p class="pns-sup-name">Powersheds<\/p>/.test(S.renderResults(r)));
  check('P1e the control states the count it will deliver',
    /View 3 products/.test(S.renderResults(r)));

  /* CASES 2-4 — each PRODUCT deep-links to its own exact record. */
  const want = [
    ['12x12 Apex Classic Log Cabin', 6129],
    ['14x14 Apex Classic Log Cabin', 6959],
    ['16x12 Apex Log Cabin', 9199],
  ];
  want.forEach(function (pair, n) {
    const name = pair[0], price = pair[1];
    const prod = r.groups.product.find((x) => x.name === name);
    check(`P${2 + n}a "${name}" is returned`, !!prod);
    if (!prod) { return; }
    check(`P${2 + n}b its price is \u20ac${price.toLocaleString('en-IE')}`,
      prod.price === price, String(prod.price));
    const url = route(prod);
    check(`P${2 + n}c it deep-links to your-plot.html?product=<its own id>`,
      url === 'your-plot.html?product=' + prod.id.slice(5), url);
    check(`P${2 + n}d the link is NOT the bare page (the shipped defect)`,
      url !== 'your-plot.html' && url.indexOf('?product=rec') > 0, url);
  });

  /* The rendered markup must actually carry those hrefs. */
  const html = S.renderResults(r);
  check('P5a the rendered Search markup contains three distinct product deep links',
    new Set((html.match(/your-plot\.html\?product=rec[A-Za-z0-9]+/g) || [])).size === 3,
    JSON.stringify([...new Set((html.match(/your-plot\.html\?product=rec[A-Za-z0-9]+/g) || []))]));
  check('P5b no rendered href is the bare your-plot.html',
    !/href="your-plot\.html"/.test(html));
}

/* CASE 5 — a hand-made link for a non-publishable product FAILS CLOSED. */
{
  check('P6a the deep-link block shape-checks the id before any lookup',
    /\^rec\[A-Za-z0-9\]\{14,17\}\$/.test(PAGE));
  check('P6b it resolves ONLY through the existing governed pool',
    /getActiveAtlasPool\(\) \|\| \[\]/.test(PAGE));
  check('P6c openProductDetail already fails closed on an unknown id',
    /const product = getActiveAtlasPool\(\)\.find\(p => p\.id === productId\);\s*\n\s*if \(!product\) return;/
      .test(PAGE));
  check('P6d it refuses to combine with the ?review= fixture',
    /if \(reviewModeParam !== null\) \{ return; \}/.test(PAGE));
  check('P6e it never calls enterResultsReviewMode',
    !/pnSearchProductDeepLink[\s\S]{0,2000}enterResultsReviewMode/.test(PAGE));
  /* Only indexed products can ever be linked: Search composes from the index. */
  const ids = new Set(INDEX.records.filter((x) => x.type === 'product')
    .map((x) => x.id.slice(5)));
  check('P6f Search can only generate links for products in the governed index',
    ids.size === INDEX.counts.product, `${ids.size} vs ${INDEX.counts.product}`);
}

/* CASE 6 — VIEWING IS NOT SAVING, and no property context is manufactured. */
{
  const blk = PAGE.slice(PAGE.indexOf('pnSearchProductDeepLink'),
                         PAGE.indexOf('THE TEST ROUTE'));
  const forbidden = ['localStorage', 'sessionStorage', 'matchState',
                     'decisionProfile', 'eircode', 'Eircode', 'county',
                     'buildDecisionProfile', 'saveTo', 'myPlot'];
  const found = forbidden.filter((f) => blk.indexOf(f) !== -1);
  check('P7a the deep-link block writes no state and fabricates no property',
    found.length === 0, JSON.stringify(found));
  check('P7b it calls exactly one existing function: openProductDetail',
    (blk.match(/openProductDetail\(/g) || []).length === 1);
  check('P7c it makes no network call of its own',
    !/fetch\(|XMLHttpRequest/.test(blk));
}

/* CASE 7 — BACK, without persisting the search term anywhere. */
{
  const stripJs = RUNTIME.replace(/\/\*[\s\S]*?\*\//g, ' ')
                         .replace(/(?<![:\w])\/\/.*$/gm, ' ');
  /* P8a RE-SPECIFIED, for exactly the reason C5 was. It used to ban the
     History API outright, and that ban is what produced the founder's
     real-browser failure: with no history entry, Back from Product Detail went
     to the homepage. History STATE is now the approved mechanism. The
     invariant that actually protects the homeowner is unchanged and is what is
     asserted here: the term never enters a URL. */
  check('P8a the term is never written to the URL by Search',
    ![...stripJs.matchAll(/(?:push|replace)State\([^)]*\)/g)]
      .some((x) => x[0].split(',').length > 2) &&
    !/location\s*\.\s*(href|search|hash)\s*=/.test(stripJs) &&
    !/\?q=/.test(stripJs));
  check('P8b the product link carries only the governed id, never the query',
    !/product=.*\+.*query|q=/.test(stripJs));
}

/* ========== PART A3 · THE VISIBLE TRANSITION AND THE RETURN CONTEXT =======
 * WHY THESE EXIST. The 93-assertion suite proved the eventual DESTINATION and
 * never the visible TRANSITION or the return context, so it passed while two
 * real defects shipped: the Eircode screen flashed before Product Detail, and
 * Product Detail said "Back to Results" to a homeowner who had come from
 * Search. Both were found by a human in a real browser. These assertions
 * encode what that human saw. */
console.log('\n  PART A3 · VISIBLE TRANSITION + RETURN CONTEXT\n');

{
  /* 1 · the landing screen is never made visible before Product Detail */
  check('T1a a pre-paint boot gate exists, and it is a CLASSIC script',
    /<script>\s*\(function \(\) \{[\s\S]{0,400}classList\.add\('pn-deeplink'\)/.test(PAGE));
  check('T1b the gate runs before #screen-entry appears in the document',
    PAGE.indexOf("classList.add('pn-deeplink')") < PAGE.indexOf('id="screen-entry"'));
  check('T1c CSS hides #screen-entry under the gate class, with !important ' +
        'so nothing can out-specify it',
    /html\.pn-deeplink #screen-entry\{[^}]*visibility:hidden !important/.test(PAGE));
  check('T1d the gate suppresses the transition too, so there is no fade-out ' +
        'of a screen the homeowner should never have seen',
    /html\.pn-deeplink #screen-entry\{[^}]*transition:none !important/.test(PAGE));
  check('T1e #screen-entry still ships WITHOUT is-hidden — the gate is the only ' +
        'thing suppressing it, so ordinary boots are untouched',
    /<section id="screen-entry" class="screen">/.test(PAGE));

  /* 2 · Product Detail is the first meaningful screen */
  const blk = PAGE.slice(PAGE.indexOf('pnSearchProductDeepLink'),
                         PAGE.indexOf('THE TEST ROUTE'));
  check('T2a Product Detail is opened BEFORE the hold is released',
    blk.indexOf('openProductDetail(wanted') < blk.indexOf('releaseHold();\n        return;'));
  check('T2b the hold element is inert and hidden from assistive tech',
    /<div id="pnDeepLinkHold" aria-hidden="true">/.test(PAGE));
  /* The first version of this assertion was sloppy: its regex could run past
     the element and match the stylesheet, so it reported a failure the markup
     did not have. It now extracts the element and checks its actual text. */
  check('T2c the hold carries no journey copy — it is the absence of a screen',
    (PAGE.match(/<div id="pnDeepLinkHold"[^>]*>([\s\S]*?)<\/div>/) || [,''])[1]
      .replace(/<[^>]+>/g, '').trim() === '');

  /* 3 · failure releases the hold, so it fails closed to entry and never hangs */
  check('T3a the bounded window releases the hold on failure',
    /if \(\+\+tries > 60\) \{ releaseHold\(\); return; \}/.test(blk));
  check('T3b releaseHold is called on exactly the success and failure paths',
    (PAGE.match(/releaseHold\(\)/g) || []).length === 3);
  check('T3c a malformed id never sets the gate in the first place',
    /\/\^rec\[A-Za-z0-9\]\{14,17\}\$\/\.test\(id\)/.test(PAGE));

  /* 4 + 5 · the label is context-aware, and Atlas origin is unchanged */
  check('T4a a Search-origin Product Detail says "Back to Search"',
    /\(pnProductOrigin === 'search'\) \? '\\u2190 Back to Search'/.test(PAGE));
  check('T5a an Atlas-Results origin still says "Back to Results"',
    /: '\\u2190 Back to Results'/.test(PAGE));
  check('T5b a My Plot origin still says "Back to My Plot"',
    /\? '\\u2190 Back to My Plot'/.test(PAGE));
  check('T5c the origin defaults to null, so every existing route is unchanged',
    /let pnProductOrigin = null;/.test(PAGE));
  check('T5d the origin is cleared on close, so a later Atlas open cannot ' +
        'inherit it', /pnProductOrigin = null;\s*\n\s*if \(history\.length/.test(PAGE));

  /* 6 · Back returns to Search, not to the property/Results area */
  check('T6a Search-origin Back uses browser history, restoring the live Search',
    /if \(history\.length > 1\) \{ history\.back\(\); \}/.test(PAGE));
  check('T6b with no Search behind it, it falls back to search.html',
    /else \{ location\.href = 'search\.html'; \}/.test(PAGE));
  check('T6c Search-origin Back does NOT call productDetailReturn.close(), ' +
        'which is what led into the Results area',
    /pnProductOrigin === 'search'\)[\s\S]{0,300}return;\s*\n\s*\}\s*\n\s*productDetailReturn\.close\(\)/
      .test(PAGE));

  /* 7 · no raw search term anywhere, including the new parameter */
  const stripJs = RUNTIME.replace(/\/\*[\s\S]*?\*\//g, ' ')
                         .replace(/(?<![:\w])\/\/.*$/gm, ' ');
  check('T7a the only thing appended to a product link is from=search',
    /\+ '&from=search'/.test(stripJs) && !/query|qnorm|input\.value/.test(
      stripJs.slice(stripJs.indexOf('function productRoute'),
                    stripJs.indexOf('function productRoute') + 600)));
  check('T7b from=search carries no homeowner text',
    !/from=search['"]?\s*\+/.test(stripJs));
  check('T7c the page never stores the term either',
    !/(localStorage|sessionStorage|indexedDB|dataLayer)/.test(
      PAGE.slice(PAGE.indexOf('pnSearchProductDeepLink'),
                 PAGE.indexOf('THE TEST ROUTE'))));

  /* 8 · no property / Atlas / My Plot state mutation */
  const forbidden = ['matchState', 'decisionProfile', 'eircode', 'Eircode',
                     'county', 'buildDecisionProfile', 'localStorage'];
  check('T8a the deep-link block mutates no property or Atlas state',
    forbidden.filter((f) => blk.indexOf(f) !== -1).length === 0,
    JSON.stringify(forbidden.filter((f) => blk.indexOf(f) !== -1)));
  check('T8b the boot gate mutates nothing but one class name',
    (PAGE.slice(PAGE.indexOf('<script>\n  (function () {'),
                PAGE.indexOf('</script>\n<div id="pnDeepLinkHold"'))
      .match(/document\./g) || []).length === 1);
}

/* ============ PART A4 · THE RETURN PATH, AFTER THE REAL-BROWSER FAILURE ===
 * Homepage -> pill -> "Powersheds" -> product -> Back landed on the HOMEPAGE.
 * Root cause: the overlay opened with preventDefault() and pushed NO history
 * entry, so Back went to the entry before the product navigation — index.html.
 * These assertions encode the fix and the contract it has to stay inside. */
console.log('\n  PART A4 · RETURN PATH (history state, no URL, no storage)\n');

{
  const stripJs = RUNTIME.replace(/\/\*[\s\S]*?\*\//g, ' ')
                         .replace(/(?<![:\w])\/\/.*$/gm, ' ');

  /* 1 · the label */
  check('H1 a Search-origin Product Detail says "Back to Search"',
    /\(pnProductOrigin === 'search'\) \? '\\u2190 Back to Search'/.test(PAGE));

  /* 2 · Search occupies a history entry, so Back cannot skip past it */
  check('H2a opening the overlay pushes a history entry',
    /writeSnapshot\(false\);/.test(stripJs) &&
    stripJs.indexOf('writeSnapshot(false)') > stripJs.indexOf('function openPanel'));
  check('H2b the product click writes the snapshot into THAT entry first',
    /closest\('a\.pns-title'\)[\s\S]{0,260}writeSnapshot\(true\);/.test(stripJs));
  check('H2c the click does NOT preventDefault, so the link still works with ' +
        'JavaScript off', !/a\.pns-title[\s\S]{0,260}preventDefault/.test(stripJs));
  check('H2d both return paths are handled: popstate AND history.state at boot',
    /addEventListener\('popstate'/.test(stripJs) &&
    /history\.state && history\.state\[SEARCH_STATE_KEY\]/.test(stripJs));

  /* 3 + 4 · the query and the results come back */
  check('H3 the restored snapshot puts the query back in the field',
    /if \(e\.input\) \{ e\.input\.value = snap\.q \|\| ''; \}/.test(stripJs));
  check('H4a the results are RECOMPUTED, not restored from the entry',
    /loadIndex\(\)\.then\(function \(\) \{\s*run\(\);/.test(stripJs));
  check('H4b the snapshot carries no results, so a restored Search can never ' +
        'show a stale answer',
    !/results\s*:/.test(stripJs.slice(stripJs.indexOf('function uiSnapshot'),
                                       stripJs.indexOf('function writeSnapshot'))));
  check('H4c the supplier expansion is restored too',
    /snap\.expanded \|\| \[\]\)\.forEach/.test(stripJs));

  /* 5 · never in a URL */
  check('H5a no state call passes a url argument',
    ![...stripJs.matchAll(/(?:push|replace)State\([^)]*\)/g)]
      .some((m) => m[0].split(',').length > 2));
  check('H5b no ?q= anywhere, in runtime or stub', !/\?q=/.test(stripJs));
  check('H5c the only link parameter is the governed id plus from=search',
    /\+ '&from=search'/.test(stripJs));

  /* 6 + 7 · never persisted, never transmitted */
  ['localStorage', 'sessionStorage', 'indexedDB', 'document.cookie',
   'dataLayer', 'sendBeacon', 'XMLHttpRequest'].forEach(function (api) {
    check('H6 the term never reaches ' + api, stripJs.indexOf(api) === -1);
  });
  check('H7 exactly one fetch, and it carries no term',
    (stripJs.match(/fetch\(/g) || []).length === 1 && /fetch\(INDEX_URL/.test(stripJs));

  /* 8 + 9 · the existing routes are untouched */
  check('H8 Atlas Results origin still says "Back to Results"',
    /: '\\u2190 Back to Results'/.test(PAGE));
  check('H9 My Plot origin still says "Back to My Plot"',
    /\? '\\u2190 Back to My Plot'/.test(PAGE));
  check('H9b origin defaults to null, so neither route can be affected',
    /let pnProductOrigin = null;/.test(PAGE));

  /* 10 · a direct deep link with no Search behind it falls back honestly */
  check('H10a with no Search history it goes to search.html, not nowhere',
    /else \{ location\.href = 'search\.html'; \}/.test(PAGE));
  check('H10b the fallback carries no query', !/search\.html\?/.test(PAGE));

  /* 11 · the Eircode flash stays fixed */
  check('H11a the pre-paint boot gate is still in place',
    /classList\.add\('pn-deeplink'\)/.test(PAGE) &&
    PAGE.indexOf("classList.add('pn-deeplink')") < PAGE.indexOf('id="screen-entry"'));
  check('H11b Product Detail still opens before the hold releases',
    PAGE.indexOf('openProductDetail(wanted') <
    PAGE.indexOf('releaseHold();\n        return;'));

  /* 12 · THE APPROVED PILL IS BYTE-IDENTICAL, IN BOTH VARIANTS.
     The first version of this assertion froze only index.html's markup and then
     reported discoveries.html and search.html as "deviating" — they are not.
     There are exactly TWO variants, differing ONLY by data-pns-nofade="true",
     which the rail builder sets per page after MEASURING whether that page's
     .brand-mark has the .in fade mechanism (discoveries.html does not). Freezing
     one variant and calling the other a deviation would have been a test that
     cried wolf at its own design, so both are pinned and the count of each is
     asserted. */
  const VARIANTS = {
    '033652069264d4c4a89f330c90fcc1a2eecc43d8f3070a35ff73151865ab988b': 'faded',
    'ca57050a4872e231': 'nofade'
  };
  const seen = { faded: 0, nofade: 0, other: [] };
  fs.readdirSync(ROOT).filter((f) => f.endsWith('.html')).forEach(function (f) {
    const src = fs.readFileSync(path.join(ROOT, f), 'utf8');
    const mk = src.match(/<a class="pns-pill"[\s\S]*?<\/a>/);
    if (!mk) { return; }
    const h = crypto.createHash('sha256').update(mk[0]).digest('hex');
    if (h === '033652069264d4c4a89f330c90fcc1a2eecc43d8f3070a35ff73151865ab988b') { seen.faded++; }
    else if (h.indexOf('ca57050a4872e231') === 0) { seen.nofade++; }
    else { seen.other.push(f + ':' + h.slice(0, 16)); }
  });
  check('H12a every pill on every page is one of the two approved variants',
    seen.other.length === 0, JSON.stringify(seen.other));
  /* H12b IS A SCOPE CENSUS, AND IT FIRED — CORRECTLY — ON 9 OCTOBER 2026.
     Job 1 (P0 journey exits) added the Search entry to 404.html, which had been
     the one reachable page on the site with no route to Search. It was never
     in build-search-rail.py's scope because that builder derives its page list
     from sitemap.xml, and the 404 is deliberately not in the sitemap.

     The pill itself did NOT change: H12a already proves the 404's pill hashes
     to the approved faded variant byte for byte, because the region was copied
     from index.html rather than authored (see atlas-tools/build-404-search.py,
     guard F3). So Search V1's markup, CSS, JS and behaviour are untouched; the
     only thing that changed is how many surfaces carry it, by one, under
     founder authorisation.

     The count is therefore RAISED DELIBERATELY and stays exact, naming the
     extra surface, so the census can still never drift silently. */
  check('H12b 20 faded + 2 nofade = 21 public surfaces + the 404',
    seen.faded === 20 && seen.nofade === 2,
    `faded=${seen.faded} nofade=${seen.nofade}`);
  check('H12b2 the 20th faded surface is 404.html specifically',
    (function () {
      const src = fs.readFileSync(path.join(ROOT, '404.html'), 'utf8');
      const mk = src.match(/<a class="pns-pill"[\s\S]*?<\/a>/);
      return !!mk && crypto.createHash('sha256').update(mk[0]).digest('hex')
        === '033652069264d4c4a89f330c90fcc1a2eecc43d8f3070a35ff73151865ab988b';
    }()));
  check('H12c the two variants differ ONLY by the measured nofade flag',
    (function () {
      const a = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8')
        .match(/<a class="pns-pill"[\s\S]*?<\/a>/)[0];
      const b = fs.readFileSync(path.join(ROOT, 'discoveries.html'), 'utf8')
        .match(/<a class="pns-pill"[\s\S]*?<\/a>/)[0];
      return b.replace(' data-pns-nofade="true"', '') === a;
    }()));
}

/* ================================================ PART B · HOSTILE LEAK */
console.log('\n  PART B · HOSTILE LEAK SUITE — knowing the name must not reveal it\n');

const previews = fs.readdirSync(ROOT).filter((f) => f.endsWith('-preview.html'));
check(`B0 the full preview set is on disk to test against (${previews.length})`,
  previews.length >= 100, String(previews.length));

/* H1 every private-preview organisation name, from the page's own title ----- */
{
  let leaked = [];
  for (const f of previews) {
    const t = fs.readFileSync(path.join(ROOT, f), 'utf8');
    const m = t.match(/<title>(.*?)<\/title>/s);
    if (!m) { continue; }
    const org = m[1].replace(/&mdash;/g, '—').split('for ').pop().trim();
    if (!org || org.length < 4) { continue; }
    const r = q(org);
    const total = r.counts.possibility + r.counts.supplier +
                  r.counts.product + r.counts.journey;
    /* An org that is ALSO legitimately in the universe (Powersheds) may answer —
       from the universe, never from the preview. What must never appear is the
       preview route. */
    if (recordsBlob(r).includes('-preview.html')) { leaked.push(org + ' (route)'); }
    const inUniverse = INDEX.records.some(
      (x) => x.type === 'supplier' && ident(x.name) === ident(org));
    if (total > 0 && !inUniverse && r.counts.supplier > 0) {
      leaked.push(org + ' (supplier record)');
    }
  }
  check(`H1 all ${previews.length} private-preview organisation names leak nothing`,
    leaked.length === 0, JSON.stringify(leaked.slice(0, 8)));
}

/* H2 retired Discovery concepts ------------------------------------------- */
{
  const retired = ['Artist Studio', 'Garden Power', 'Potential Asset',
                   'Room to Grow', 'Start Something', 'An Extra Room'];
  const bad = retired.filter((t) => {
    const r = q(t);
    const s = recordsBlob(r);
    return /discovery-(artist-studio|garden-power|potential-asset|room-to-grow|start-something|an-extra-room)/.test(s)
           || s.toLowerCase().includes('"moved');
  });
  check('H2 no retired Discovery or "Moved" stub is reachable', bad.length === 0,
    JSON.stringify(bad));
}

/* H3 the orphan that has real content ------------------------------------- */
{
  const r = q('LOOK AGAIN');
  const r2 = q('look again hidden cars');
  check('H3 campaign-look-again.html (noindex WITH real content) is unreachable',
    !recordsBlob(r).includes('campaign-look-again') &&
    !recordsBlob(r2).includes('campaign-look-again'));
}

/* H4 recognition-pool-only organisations ---------------------------------- */
{
  /* DERIVED, NOT HARD-CODED. The first version used a hand-written list taken
     from a naive exact set-difference, which wrongly included "Quinn Offsite" —
     the universe publishes it as "Quinn Offsite Ltd". A hard-coded list also
     goes stale silently. This computes the genuinely pool-only set on every
     run, under the same identity rule. */
  const pool = JSON.parse(fs.readFileSync(path.join(ROOT, 'atlas-recognition-pool.json'), 'utf8'));
  const universeIdents = new Set(INDEX.records
    .filter((r) => r.type === 'supplier').map((r) => ident(r.name)));
  const poolOnly = [...new Set(pool
    .map((x) => x && x.organisation).filter(Boolean)
    .filter((o) => !universeIdents.has(ident(o))))];
  console.log(`         (derived pool-only organisations: ${poolOnly.length} — ` +
              `${JSON.stringify(poolOnly)})`);
  const leaked = poolOnly.filter((o) => {
    const r = q(o);
    return r.counts.supplier > 0 || r.counts.product > 0;
  });
  check(`H4 all ${poolOnly.length} recognition-pool-only organisations return nothing`,
    leaked.length === 0, JSON.stringify(leaked));
  const inIndex = poolOnly.filter((o) => RAW.includes(o));
  check('H4b the pool is not a publication source: none appears in the index',
    inIndex.length === 0, JSON.stringify(inIndex));
}

/* H5 literal filenames and paths ------------------------------------------ */
{
  const probes = ['auroom-wellness-preview.html', 'powersheds-preview.html',
                  'supplier-preview-system/template-provider-led.html',
                  'your-plot.html', 'disc025-borrowed-garden-check.html',
                  '-preview.html', 'thanks.html', 'image-permission.html'];
  const leaked = [];
  for (const p of probes) {
    const r = q(p);
    if (recordsBlob(r).includes('-preview.html')) { leaked.push(p); }
  }
  check('H5 searching for preview filenames and paths reveals no preview',
    leaked.length === 0, JSON.stringify(leaked));
  check('H5b the index file itself contains no preview string anywhere',
    !RAW.includes('-preview.html') && !RAW.includes('supplier-preview-system'));
}

/* ===================================================== PART C · PRIVACY */
console.log('\n  PART C · SEARCH TERMS ARE LOCAL AND EPHEMERAL\n');

const strip = RUNTIME.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(?<![:\w])\/\/.*$/gm, ' ');

check('C1 no localStorage in the runtime', !/localStorage/.test(strip));
check('C2 no sessionStorage in the runtime', !/sessionStorage/.test(strip));
check('C3 no IndexedDB in the runtime', !/indexedDB/i.test(strip));
check('C4 no document.cookie write', !/document\s*\.\s*cookie/.test(strip));
/* C5 CHANGED DELIBERATELY, NOT WEAKENED. The blanket ban on the History API
   was what made the founder's Back land on the homepage: the overlay created no
   entry, so there was nothing to go back to. Founder-approved after that
   failure: the term may live in this document's own history STATE. What is
   still forbidden — and is what actually matters — is writing it into a URL,
   so C5 now asserts that no state call passes a url argument. */
check('C5 history state is used, but NO state call ever writes a URL',
  /pushState\(snap, ''\)/.test(strip) && /replaceState\(snap, ''\)/.test(strip) &&
  ![...strip.matchAll(/(?:push|replace)State\([^)]*\)/g)]
    .some((m) => m[0].split(',').length > 2));
check('C5b the address bar is never assigned in the runtime',
  !/location\s*\.\s*(href|search|hash)\s*=/.test(strip));
check('C6 no dataLayer push', !/dataLayer/.test(strip));
check('C7 no gtag / ga / analytics call', !/\b(gtag|ga)\s*\(/.test(strip));
check('C8 no sendBeacon', !/sendBeacon/.test(strip));
check('C9 no XMLHttpRequest', !/XMLHttpRequest/.test(strip));
check('C10 exactly one fetch, and it is the index',
  (strip.match(/fetch\s*\(/g) || []).length === 1 && /fetch\(INDEX_URL/.test(strip));
check('C11 the index fetch carries no query string or term',
  !/INDEX_URL\s*\+/.test(strip) && !/\?q=/.test(strip));
check('C12 location is never written', !/location\s*\.\s*(href|search|hash)\s*=/.test(strip));
check('C13 the runtime renders no product or supplier image',
  !/<img/i.test(strip) && !/\.src\s*=/.test(strip) && !/backgroundImage/.test(strip));

console.log(`\n  ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
