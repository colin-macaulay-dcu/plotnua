#!/usr/bin/env node
/**
 * PROVE CLUSTER 1 · GARDEN AUTHORITY
 * ==================================
 * Claim guards for discovery-living-in-the-garden.html after the approved
 * Cluster 1 build. Eighteen named guards, each owning one mutation.
 *
 * Every guard reads the real page and the frozen evidence artefact. No guard
 * sits behind a data-dependent early return: the page slices used below are
 * asserted non-empty first, so a guard that cannot reach its subject is a
 * FAILURE, not a silent pass. (The M01 lesson, 10 October 2026.)
 *
 *   node atlas-tools/prove-cluster1-garden-authority.mjs [--page <path>]
 *
 * Exit 0 = all pass. Exit 1 = at least one failure.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const argPage = process.argv.indexOf('--page');
const PAGE = argPage > -1 ? process.argv[argPage + 1] : join(ROOT, 'discovery-living-in-the-garden.html');
const argMap = process.argv.indexOf('--sitemap');
const SITEMAP = argMap > -1 ? process.argv[argMap + 1] : join(ROOT, 'sitemap.xml');

const src = readFileSync(PAGE, 'utf8');
const sitemap = readFileSync(SITEMAP, 'utf8');
const EV = JSON.parse(readFileSync(join(HERE, 'cluster1-cost-evidence.json'), 'utf8'));
const FIG = EV.homeownerVisibleFigures;

let pass = 0, fail = 0;
const ok = (id, msg) => { pass++; console.log(`  PASS  ${id}  ${msg}`); };
const bad = (id, msg) => { fail++; console.log(`  FAIL  ${id}  ${msg}`); };

/** Strip <style>, <script> (except ld+json, handled separately) and comments,
 *  so guards see only what a homeowner sees. */
function visible(html) {
  return html
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<script\b(?![^>]*ld\+json)[\s\S]*?<\/script>/gi, ' ')
    .replace(/<script[^>]*ld\+json[\s\S]*?<\/script>/gi, ' ')
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ').replace(/&mdash;/g, '—').replace(/&ndash;/g, '–')
    .replace(/&ldquo;|&rdquo;/g, '"').replace(/&rsquo;/g, "'")
    .replace(/&sup2;/g, '²').replace(/&amp;/g, '&')
    // currency entities decoded, or P1 would be blind to a price written as
    // &euro; rather than the literal glyph. Found by C-P1a, 11 October 2026.
    .replace(/&euro;/g, '€').replace(/&pound;/g, '£').replace(/&#8364;|&#x20AC;/gi, '€')
    .replace(/\s+/g, ' ');
}
const VIS = visible(src);

/** Slice a region of the raw source between two markers. Asserts non-empty. */
function slice(id, from, to) {
  const a = src.indexOf(from);
  const b = a < 0 ? -1 : src.indexOf(to, a + from.length);
  if (a < 0 || b < 0) { bad(id, `UNREACHABLE: cannot locate region (${a}, ${b}) — guard could not run`); return null; }
  return src.slice(a, b);
}

// ---------------------------------------------------------------------------
console.log('\nCLUSTER 1 CLAIM GUARDS\n');

// --- L1 · planning limits ---------------------------------------------------
{
  // Statutory limits, plus two derived figures the page already carried:
  //   13  = 45 - 32, the pre-existing "how much shed rules you out" arithmetic
  //   50  = the BER threshold for a standalone building
  // 2/12/20/40/45 are Class 1 figures; 300 is Third Schedule Class 5.
  const ALLOWED = new Set(['2', '12', '13', '20', '25', '30', '32', '40', '45', '50', '300']);
  const found = [...VIS.matchAll(/(\d+(?:\.\d+)?)\s*(?:m²|square metres)/g)].map(m => m[1]);
  if (!found.length) bad('L1', 'UNREACHABLE: no square-metre figures found on the page at all');
  else {
    const rogue = [...new Set(found)].filter(n => !ALLOWED.has(n));
    rogue.length ? bad('L1', `disallowed area figure(s) on the page: ${rogue.join(', ')}`)
                 : ok('L1', `${found.length} area figures, all inside the verified set {${[...new Set(found)].sort((a,b)=>a-b).join(', ')}}`);
  }
}

// --- L2 · the 25 m² Building Regulations distinction, stated conditionally ---
{
  const need = [
    'Thirty square metres is the planning ceiling for a garden room',
    'separate threshold, and it is still 25',
    'but only if it also meets the rest of the conditions attached to it',
    'not for human habitation and not for a trade or business',
  ];
  const missing = need.filter(s => !VIS.includes(s));
  // the categorical form the founder forbade
  const forbidden = /outside the Building Regulations altogether|automatically exempt from (the )?Building Regulations|under 25\s*m²[^.]{0,40}(is|are) exempt/i;
  if (missing.length) bad('L2', `missing required clause(s): ${missing.map(s => `"${s.slice(0, 40)}…"`).join('; ')}`);
  else if (forbidden.test(VIS)) bad('L2', 'page states the 25 m² exemption categorically — the conditions must be carried');
  else ok('L2', '30 m² planning / 25 m² Building Regulations distinction present, and conditional');
}

// --- L3 · measurement honesty -----------------------------------------------
{
  const asserts = /(total area|floor area)[^.]{0,60}\b(is|means|shall be)\b[^.]{0,30}\b(internal|external|measured)/i;
  const asserts2 = /(total area|floor area) is (defined|measured)/i;
  if (!VIS.includes('they say "total area", which is defined nowhere'))
    bad('L3', 'the page no longer states that "total area" is undefined');
  else if (asserts.test(VIS) || asserts2.test(VIS))
    bad('L3', `page asserts a measurement method: ${(VIS.match(asserts) || VIS.match(asserts2))[0]}`);
  else ok('L3', 'ambiguity stated as ambiguity; no measurement method asserted');
}

// --- L4 · "habitable" never attributed to the regulations -------------------
{
  const m = VIS.match(/(regulations?|exemption|statute|Class 3A)[^.]{0,80}habitable|habitable[^.]{0,60}(regulations?|exemption|statute|Class 3A)/i);
  m ? bad('L4', `"habitable" attributed to the regulations: "${m[0].slice(0, 90)}"`)
    : ok('L4', 'the word "habitable" is not attributed to the regulations');
}

// --- L5 · dates --------------------------------------------------------------
{
  const ALLOWED = new Set(['16 July 2026', '27 July 2026', '31 December 2030', '1 October 1964']);
  // 14 Oct 2026: the price section names the research snapshot its figures
  // come from. That date is not typed here: it is traced to the evidence
  // file's own source stamp, so only THAT date is allowed.
  if (typeof EV !== 'undefined' && EV && EV.source && EV.source.generated) {
    const d = new Date(EV.source.generated.slice(0, 10) + 'T00:00:00Z');
    ALLOWED.add(`${d.getUTCDate()} ${d.toLocaleString('en-GB', { month: 'long', timeZone: 'UTC' })} ${d.getUTCFullYear()}`);
  }
  const found = [...VIS.matchAll(/\b\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}\b/g)].map(m => m[0]);
  if (!found.length) bad('L5', 'UNREACHABLE: no full dates on the page — the signing date should be here');
  else {
    const rogue = [...new Set(found)].filter(d => !ALLOWED.has(d));
    if (rogue.length) bad('L5', `unverified date(s) published: ${rogue.join(', ')}`);
    else if (!VIS.includes('16 July 2026')) bad('L5', 'the verified signing date 16 July 2026 is absent');
    else ok('L5', `dates on the page: ${[...new Set(found)].join(' · ')}`);
  }
}

// --- L6 · the curated unresolved questions stay framed as unresolved --------
{
  const d = slice('L6', 'What the regulations do not say', '</details>');
  if (d) {
    const need = {
      'semi-detached / terraced conflict': 'Those are\n          not the same thing, and the regulations do not reconcile them',
      'measurement': 'Undefined, and that is the honest answer',
      'toilet / incidental use': 'where a WC sits against that test is not settled in the text',
      'seven-year rule': 'It is a limit on the\n          council, not a route for you',
    };
    const missing = Object.entries(need).filter(([, s]) => !d.includes(s)).map(([k]) => k);
    missing.length ? bad('L6', `unresolved item(s) no longer framed as unresolved: ${missing.join(', ')}`)
                   : ok('L6', 'all four curated unresolved items present and framed as unresolved');
  }
}

// --- L7 · the seven-year rule is not presented as authorisation -------------
{
  const d = slice('L7', 'seven-year rule', '</details>');
  if (d) {
    const v = visible(d);
    const claims = /seven years[^.]{0,80}\b(lawful|authorised|authorized|exempt|legal|permitted)\b(?!,)/i;
    if (!v.includes('It does not make the building lawful'))
      bad('L7', 'the page no longer says the seven-year rule does not make the building lawful');
    else if (claims.test(v.replace('It does not make the building lawful', '')))
      bad('L7', 'the seven-year rule is presented as conferring lawfulness');
    else ok('L7', 'seven-year rule presented as an enforcement limit, not authorisation');
  }
}

// --- L8 · the two declarations are not conflated ----------------------------
{
  const ps = slice('L8-ps', 'Protected structures and conservation areas', '</details>');
  const s5 = slice('L8-s5', 'Settling it in writing: the Section 5 declaration', '</details>');
  if (ps && s5) {
    const pv = visible(ps), sv = visible(s5);
    const errs = [];
    if (!/twelve weeks/i.test(pv)) errs.push('protected-structure drawer lost the twelve-week clock');
    if (/prescribed fee/i.test(pv) && !/Section 5/i.test(pv)) errs.push('a prescribed fee attached to the s.57 declaration');
    if (!/four weeks/i.test(sv)) errs.push('Section 5 drawer lost the four-week clock');
    if (!/prescribed fee/i.test(sv)) errs.push('Section 5 drawer lost the prescribed fee');
    if (/twelve weeks/i.test(sv)) errs.push('the twelve-week clock has leaked into the Section 5 drawer');
    errs.length ? bad('L8', errs.join('; ')) : ok('L8', 's.5 (fee, 4 weeks) and s.57 (12 weeks) kept distinct');
  }
}

// --- L9 · protected structures stated conditionally -------------------------
{
  const d = slice('L9', 'Protected structures and conservation areas', '</details>');
  if (d) {
    const v = visible(d);
    if (/protection\s+extends to the land in its curtilage/i.test(v))
      bad('L9', 'the unconditional curtilage claim is back on the page');
    else if (!v.includes("only where the council's Record of Protected Structures says so"))
      bad('L9', 'the conditional qualifier on the attendant-grounds extension is missing');
    else ok('L9', 'attendant-grounds protection stated as conditional on the Record');
  }
}

// --- the price section ------------------------------------------------------
/* The price section ends where the next section begins. Since 13 October 2026
   that is the Maker Explorer (marker 6c, atlas-tools/build-maker-explorer.py),
   whose own figures are traced to the published universes by that builder's
   guard G1; before it existed, the next section was 7. Ending the slice at the
   section boundary keeps P1-P4 exactly as strict over the price section and
   does not let the explorer's counts be misread as price-section figures. */
const PRICE_END = src.indexOf('<!-- 6c · ') > -1 ? '<!-- 6c · ' : '<!-- 7 · THE EVIDENCE LAYER';
const PRICE = slice('P0', 'Garden room prices are hard to compare.', PRICE_END);
if (PRICE) {
  // Founder correction, 11 October 2026. The superseded heading must not come
  // back through a hand edit or a regeneration from a stale builder.
  if (VIS.includes('Why the prices you are quoted will not compare'))
    bad('P0', 'the retired pricing heading is back on the page');
  else ok('P0', `price section located under the approved heading, ${PRICE.length} chars`);
}

// --- P1 · no cross-basis arithmetic ----------------------------------------
if (PRICE) {
  const v = visible(PRICE);
  const errs = [];
  if (/[€£$]|\bEUR\b/.test(v)) errs.push('a currency figure appears in the price section');
  // belt and braces: the raw region, in case a new entity form is introduced
  if (/&euro;|&pound;|&#8364;|&#x20AC;/i.test(PRICE)) errs.push('a currency entity appears in the price section');
  const words = v.match(/\b(average|averages|averaged|typical|typically|median|mean)\b/gi);
  if (words) errs.push(`aggregate language: ${[...new Set(words.map(w => w.toLowerCase()))].join(', ')}`);
  errs.length ? bad('P1', errs.join('; ')) : ok('P1', 'no price figure and no aggregate language in the price section');
}

// --- P2 · every count traced to the artefact -------------------------------
if (PRICE) {
  const v = visible(PRICE);
  const want = {
    relevantProducts: FIG.relevantProducts,
    priceBasisNotEstablished: FIG.priceBasisNotEstablished,
    vatStatusUnknown: FIG.vatStatusUnknown,
    floorAreaPublished: FIG.floorAreaPublished,
    gardenRoomRecords: EV.totals.gardenRoomRecords,
    relevantOrganisations: EV.totals.relevantOrganisations,
  };
  const missing = Object.entries(want).filter(([, n]) => !new RegExp(`\\b${n}\\b`).test(v)).map(([k, n]) => `${k}=${n}`);
  // and no untraced integer >= 10 other than the allowed set
  const allowed = new Set([...Object.values(want).map(String), '25', '30', '32', '45',
    // the snapshot date's day and year, traced to the evidence stamp (14 Oct 2026)
    ...EV.source.generated.slice(0, 10).split('-').map(x => String(Number(x)))]);
  const rogue = [...new Set([...v.matchAll(/\b(\d{2,})\b/g)].map(m => m[1]))].filter(n => !allowed.has(n));
  if (missing.length) bad('P2', `artefact figure(s) absent from the page: ${missing.join(', ')}`);
  else if (rogue.length) bad('P2', `untraced figure(s) in the price section: ${rogue.join(', ')}`);
  else ok('P2', `all six artefact figures present (${Object.values(want).join('/')}), no untraced figures`);
}

// --- P3 · no Class 3A price, no census claim -------------------------------
if (PRICE) {
  const v = visible(PRICE);
  const errs = [];
  if (!v.includes('we are certainly not going to tell you what a garden home costs'))
    errs.push('the explicit garden-home price refusal is missing');
  if (/\b(all|every|complete|entire)\b[^.]{0,30}\b(Irish )?(garden[- ]room )?market\b/i.test(v))
    errs.push('the page implies Atlas is a complete census of the market');
  if (EV.homeownerVisibleFigures.class3AProductsInAtlas > 2)
    errs.push('Atlas now holds enough Class 3A products that this copy needs re-approval');
  errs.length ? bad('P3', errs.join('; ')) : ok('P3', 'no Class 3A price, no census claim');
}

// --- P4 · the three questions survive --------------------------------------
if (PRICE) {
  const v = visible(PRICE);
  const q = ['Is erection included?', 'Are foundations included?', 'Is VAT included?'];
  const missing = q.filter(s => !v.includes(s));
  missing.length ? bad('P4', `homeowner test question(s) missing: ${missing.join(' ')}`)
                 : ok('P4', 'all three comparison questions present');
}

// --- S1 · schema honesty ----------------------------------------------------
{
  const m = src.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/);
  if (!m) bad('S1', 'UNREACHABLE: no JSON-LD block found');
  else {
    let data;
    try { data = JSON.parse(m[1]); } catch (e) { data = null; bad('S1', `JSON-LD does not parse: ${e.message}`); }
    if (data) {
      const types = (data['@graph'] || []).map(n => n['@type']).sort();
      const expect = ['BreadcrumbList', 'Organization', 'WebPage', 'WebSite'];
      const banned = /"@type"\s*:\s*"(FAQPage|Question|Answer|Product|Offer|AggregateOffer|Review|AggregateRating)"/;
      if (banned.test(m[1])) bad('S1', `banned schema type present: ${m[1].match(banned)[1]}`);
      else if (JSON.stringify(types) !== JSON.stringify(expect)) bad('S1', `schema graph is [${types}], expected [${expect}]`);
      else ok('S1', `JSON-LD parses; graph = ${types.join(', ')}; no FAQPage/Product/Offer`);
    }
  }
}

// --- S2 · dateModified and sitemap lastmod agree ----------------------------
{
  const dm = (src.match(/"dateModified":\s*"([0-9-]+)"/) || [])[1];
  const lm = (sitemap.match(/discovery-living-in-the-garden\.html<\/loc><lastmod>([0-9-]+)<\/lastmod>/) || [])[1];
  if (!dm || !lm) bad('S2', `UNREACHABLE: dateModified=${dm} lastmod=${lm}`);
  else if (dm !== lm) bad('S2', `dateModified ${dm} != sitemap lastmod ${lm}`);
  else ok('S2', `dateModified = sitemap lastmod = ${dm}`);
}

// --- J1 · journey preservation ----------------------------------------------
{
  const toks = {
    "measurement event": "garden_discovery_assessment_click",
    "your-plot guard": "!destination.pathname.endsWith('/your-plot.html')",
    "two routes": "route !== 'garden-room' && route !== 'residential'",
    "H1": 'What Could You Build in Your Garden?',
    "title": '<title>Garden Rooms &amp; Garden Homes in Ireland: 2026 Planning Rules | PlotNua</title>',
    "canonical": '<link rel="canonical" href="https://plotnua.ie/discovery-living-in-the-garden.html">',
  };
  const errs = Object.entries(toks).filter(([, t]) => src.split(t).length - 1 < 1).map(([k]) => k);
  errs.length ? bad('J1', `journey/identity token(s) lost: ${errs.join(', ')}`)
              : ok('J1', 'both assessment routes, the measurement event, H1, title and canonical intact');
}

// --- J2 · the garden-room Commencement Notice claim stays omitted (option A)
{
  const forbidden = /A garden room files nothing|garden room[^.]{0,80}no (commencement notice|Commencement Notice)|no Commencement Notice[^.]{0,60}garden room/i;
  const m = VIS.match(forbidden);
  if (m) bad('J2', `the omitted garden-room Commencement Notice claim has reappeared: "${m[0].slice(0, 80)}"`);
  else if (!VIS.includes('For a garden home, it does not mean nothing to file'))
    bad('J2', 'the scope correction on the two notices is missing');
  else if (!VIS.includes('A Commencement Notice with Additional Documentation'))
    bad('J2', 'the verified garden-home Building Control chain has been lost');
  else ok('J2', 'garden-room CN claim omitted; verified garden-home chain intact');
}

// ---------------------------------------------------------------------------
console.log(`\n${pass + fail} checks, ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
