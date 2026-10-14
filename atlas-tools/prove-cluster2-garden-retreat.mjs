#!/usr/bin/env node
/**
 * PROVE CLUSTER 2 · GARDEN RETREAT
 * ================================
 * Claim guards for discovery-garden-retreat.html after the approved Cluster 2
 * build. Every guard reads the real page. No guard sits behind a
 * data-dependent early return: a region that cannot be located is reported as
 * UNREACHABLE and counted a FAILURE, never a silent pass.
 *
 *   node atlas-tools/prove-cluster2-garden-retreat.mjs [--page P] [--sitemap S]
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const arg = (f, d) => { const i = process.argv.indexOf(f); return i > -1 ? process.argv[i + 1] : d; };
const PAGE = arg('--page', join(ROOT, 'discovery-garden-retreat.html'));
const SITEMAP = arg('--sitemap', join(ROOT, 'sitemap.xml'));

const src = readFileSync(PAGE, 'utf8');
const sitemap = readFileSync(SITEMAP, 'utf8');

let pass = 0, fail = 0;
const ok = (id, m) => { pass++; console.log(`  PASS  ${id}  ${m}`); };
const bad = (id, m) => { fail++; console.log(`  FAIL  ${id}  ${m}`); };

function visible(html) {
  return html
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ').replace(/&mdash;/g, '—').replace(/&ndash;/g, '–')
    .replace(/&ldquo;|&rdquo;/g, '"').replace(/&rsquo;|&#39;/g, "'")
    .replace(/&sup2;/g, '²').replace(/&amp;/g, '&')
    .replace(/&euro;/g, '€').replace(/&pound;/g, '£').replace(/&middot;/g, '·')
    .replace(/&uacute;/g, 'ú').replace(/&oacute;/g, 'ó').replace(/&aacute;/g, 'á')
    .replace(/\s+/g, ' ');
}
const VIS = visible(src);

function slice(id, from, to) {
  const a = src.indexOf(from);
  const b = a < 0 ? -1 : src.indexOf(to, a + from.length);
  if (a < 0 || b < 0) { bad(id, `UNREACHABLE: region not found (${a}, ${b}) — guard could not run`); return null; }
  return src.slice(a, b);
}

console.log('\nCLUSTER 2 CLAIM GUARDS\n');

// --- L1 · the hot tub position is an interpretation, never a determination --
{
  const forbidden = [
    /a (freestanding )?hot tub (is|does) not (development|need|require)/i,
    /you do not need planning permission for a hot tub/i,
    /hot tubs are exempt/i,
    /no permission is (needed|required) for a (hot tub|cold plunge)/i,
  ];
  const hit = forbidden.map(r => VIS.match(r)).find(Boolean);
  if (hit) bad('L1', `categorical hot-tub claim: "${hit[0]}"`);
  else if (!VIS.includes('It is not a decision by your council, and only a council or'))
    bad('L1', 'the "not a decision by your council" disclaimer is missing');
  else if (!VIS.includes('It appears to fall outside the rules altogether'))
    bad('L1', 'the hedged "appears to" formulation for the free-standing tub is missing');
  else ok('L1', 'hot tub stated as a reading of the definitions, not a determination');
}

// --- L2 · the four categories are each present and each reasoned -----------
{
  const need = {
    'sauna cabin': 'A sauna cabin. You build it, so the rules apply',
    'hot tub on a patio': 'A hot tub on an existing patio.',
    'sunken tub': 'A sunken or in-ground tub.',
    'cold plunge': 'A cold plunge tub you stand on the ground.',
    'dig/deck flip': 'Build a deck or a shelter around it',
    'services flip': 'the connection can need permission even when the tub itself does not',
  };
  const miss = Object.entries(need).filter(([, s]) => !VIS.includes(s)).map(([k]) => k);
  miss.length ? bad('L2', `missing category or qualifier: ${miss.join(', ')}`)
              : ok('L2', 'four categories plus both flip conditions present');
}

// --- L3 · no categorical "a sauna IS a Class 3 structure" ------------------
{
  const forbidden = /a sauna (cabin )?is a Class ?3 structure|saunas are Class ?3|is classified as a Class ?3/i;
  const m = VIS.match(forbidden);
  if (m) bad('L3', `categorical Class 3 classification: "${m[0]}"`);
  else if (!VIS.includes('A sauna is not named anywhere in it'))
    bad('L3', 'the "a sauna is not named anywhere in it" qualifier is missing');
  else {
    // Scoped to the planning block. The phrase also appears in the
    // unresolved-questions list at the foot of the page, which satisfied a
    // page-wide test even with the basis removed. Found by C-L3b.
    const a = src.indexOf('<h3>Planning</h3>'), b = src.indexOf('<div class="practical-group">', a);
    if (a < 0 || b < 0) bad('L3', 'UNREACHABLE: planning block not found');
    else if (!visible(src.slice(a, b)).includes('other similar structure'))
      bad('L3', 'the "other similar structure" basis is missing from the planning block');
    else ok('L3', 'sauna classification stated as a reading of "other similar structure"');
  }
}

// --- L4 · the two thresholds, accurate and conditional ---------------------
{
  const errs = [];
  if (!/30\s*m²/.test(VIS)) errs.push('30 m² planning ceiling absent');
  if (!/25\s*m²[^.]{0,60}open garden/.test(VIS)) errs.push('25 m² open garden absent');
  if (!VIS.includes('Building Regulations are a separate rule with a separate number, and it is 25'))
    errs.push('the two rules are not separated');
  if (!VIS.includes('only if it is also standing on its own'))
    errs.push('the Building Regulations exemption is stated unconditionally');
  if (!VIS.includes('rather than for a business')) errs.push('the not-a-business condition is absent');
  if (!VIS.includes('for personal use at home')) errs.push('the personal-use condition is absent');
  // Scoped to the planning block. Product footprints elsewhere on the page
  // (1.2 m² Timbertrove plunge, 7.6 m² Hansa24 Lisette sauna) are
  // supplier-sourced and pre-existing; this guard owns the statutory figures.
  const plan = src.indexOf('<h3>Planning</h3>');
  const planEnd = src.indexOf('<div class="practical-group">', plan);
  if (plan < 0 || planEnd < 0) errs.push('UNREACHABLE: planning block not found');
  else {
    const pv = visible(src.slice(plan, planEnd));
    const rogue = [...new Set([...pv.matchAll(/(\d+(?:\.\d+)?)\s*m²/g)].map(m => m[1]))]
      .filter(n => !['25', '30', '7.3'].includes(n));
    if (rogue.length) errs.push(`unverified area figure(s) in the planning block: ${rogue.join(', ')}`);
  }
  errs.length ? bad('L4', errs.join('; ')) : ok('L4', '30 m² and 25 m² present, separated and conditional');
}

// --- L5 · the precedent is recorded and not overstated ---------------------
{
  const d = slice('L5', 'The one Irish case we found', '</div>\n    </div>') || slice('L5b', 'The one Irish case we found', '<div class="practical-group">');
  if (d) {
    const v = visible(d);
    const errs = [];
    // Layer B carries the gist; Layer A (the evidence drawer) carries the full
    // citation. Both are checked, each where it belongs.
    for (const t of ['ABP-322192-25', 'July 2025', '7.3 m²', 'Sandycove', 'three years'])
      if (!v.includes(t)) errs.push(`body missing ${t}`);
    const ev = visible(slice('L5-ev', 'The one case', '</details>') || '');
    for (const t of ['ABP-322192-25', '7 July 2025', 'Dún Laoghaire-Rathdown', 'D25A/0034/WEB'])
      if (!ev.includes(t)) errs.push(`evidence drawer missing ${t}`);
    if (!v.includes('not a Section 5 declaration'))
      errs.push('the case is not disclaimed as a non-s.5');
    if (!v.includes('we are not going to read that silence as a yes'))
      errs.push('absence of precedent is not disclaimed');
    // Founder correction, 11 Oct 2026: do not claim commercial use ALONE
    // triggered the requirement. The application was a package.
    if (!v.includes('we are not saying the paying customers alone are what made permission necessary'))
      errs.push('the commercial-use-alone disclaimer is missing');
    if (!v.includes('the fencing, the kiosk, the shelter'))
      errs.push('the associated structures and site works are not named');
    const over = /(because it was a business|commercial use alone (triggered|required|is what))/i;
    if (over.test(v)) errs.push(`requirement attributed to commercial use alone: "${v.match(over)[0]}"`);
    errs.length ? bad('L5', errs.join('; ')) : ok('L5', 'ABP-322192-25 recorded with authority, date, facts, outcome and limits');
  }
}

// --- L6 · electricity: verified only ---------------------------------------
{
  const errs = [];
  // The retired sentence carried penalty figures PlotNua never verified at
  // primary source. "three years" alone is NOT the test: it also appears,
  // legitimately, in the verified ABP-322192-25 three-year permission.
  if (/penalties up to/i.test(VIS) || /€\s*50,000/.test(VIS) || /50,000 and three years/i.test(VIS))
    errs.push('the unverified penalty figures are back on the page');
  for (const t of ['Registered Electrical Contractor', 'Completion Certificate', 'I.S. 10101'])
    if (!VIS.includes(t)) errs.push(`missing verified term: ${t}`);
  // Layer B says the plain thing; Layer A keeps the regulatory gap on record.
  // Founder correction, 11 Oct 2026.
  if (!VIS.includes('The exact electrical requirements depend on your installation'))
    errs.push('the plain-English electrical sentence is missing');
  if (!VIS.includes('A registered electrical contractor can advise you and carry out the work safely'))
    errs.push('the "ask a registered contractor" direction is missing');
  const ev = visible(slice('L6-ev', '<h3>Electricity</h3>', '</details>') || '');
  if (!ev.includes('Neither body\u2019s published material sets out exactly which jobs fall inside it')
      && !ev.includes("Neither body's published material sets out exactly which jobs fall inside it"))
    errs.push('the restricted/controlled boundary gap is no longer recorded in the evidence layer');
  if (!ev.includes('restricted electrical works') || !ev.includes('controlled electrical works'))
    errs.push('the two regulators\u2019 terms are not both recorded in the evidence layer');
  errs.length ? bad('L6', errs.join('; ')) : ok('L6', 'CRU-verified electrical guidance only; boundary disclaimed');
}

// --- R1 · the four running-cost quantities are kept apart ------------------
{
  const d = slice('R1', 'What it costs to run', '<h3>Insurance</h3>');
  if (d) {
    const v = visible(d);
    const need = {
      'consumption (kW x hours)': 'uses 9 units of electricity',
      'what you pay per unit': 'what you pay per unit',
      'own bill, not an average': 'the figure on your own bill, not an average',
      'illustrative session cost': 'that hour comes to',
      'standing charges kept separate': 'standing charges belong to your house, not to your sauna',
      'cycling stated': 'how long it runs and how much it cycles',
      'no invented percentage': 'We are not going to put a percentage on that and pretend it is precise',
    };
    const miss = Object.entries(need).filter(([, s]) => !v.includes(s)).map(([k]) => k);
    miss.length ? bad('R1', `running-cost quantity not kept apart: ${miss.join(', ')}`)
                : ok('R1', 'all four quantities separated; cycling stated; no invented duty cycle');
  }
}

// --- R2 · the rate is labelled illustrative, never a national price --------
{
  const d = slice('R2', 'What it costs to run', '<h3>Insurance</h3>');
  if (d) {
    const v = visible(d);
    const errs = [];
    // Founder correction, 11 Oct 2026: the figure must be described as one hour
    // of CONTINUOUS operation at an ILLUSTRATIVE rate.
    if (!v.includes('one hour of continuous 9 kW operation at an illustrative rate'))
      errs.push('the continuous-operation / illustrative-rate description is missing');
    if (!v.includes('not a forecast of your bill'))
      errs.push('the "not a forecast of your bill" caveat is missing');
    if (!v.includes('At an illustrative 35c a unit'))
      errs.push('the rate is not labelled illustrative where it is used');
    const claims = /(the|a) (current|average|national|typical) (Irish )?(electricity )?(unit )?rate is/i;
    if (claims.test(v)) errs.push(`a national price is claimed: "${v.match(claims)[0]}"`);
    if (/all-in|40\.42/.test(v) && !/belong to your household/.test(v))
      errs.push('an all-in price is used without the household caveat');
    errs.length ? bad('R2', errs.join('; ')) : ok('R2', 'rate labelled illustrative; no national price claimed');
  }
}

// --- R3 · the arithmetic on the page is correct ----------------------------
{
  const d = slice('R3', 'What it costs to run', '<h3>Insurance</h3>');
  if (d) {
    const v = visible(d);
    const m = v.match(/(\d+)\s*kW heater running flat out for an hour uses (\d+)\s*units/);
    // \d+\.\d{2} exactly, not [\d.]+ — the loose class swallowed the
    // sentence's full stop and produced NaN. Found by the first guard run.
    const n = v.match(/At an illustrative (\d+)c a unit, that hour comes to €(\d+\.\d{2})/);
    if (!m || !n) bad('R3', `UNREACHABLE: could not parse the worked example (${!!m}, ${!!n})`);
    else {
      const kw = +m[1], kwh = +m[2], rate = +n[1], eur = +n[2], kwh2 = kwh;
      const expect = Math.round(kwh2 * rate) / 100;
      (kw === kwh && Math.abs(expect - eur) < 0.005)
        ? ok('R3', `${kw} kW × 1 h × ${rate}c = €${eur.toFixed(2)} — arithmetic checks out`)
        : bad('R3', `arithmetic wrong: ${kwh2} kWh × ${rate}c = €${expect.toFixed(2)}, page says €${eur.toFixed(2)}`);
    }
  }
}

// --- P1 · no market-wide price comparison, no Atlas wellness claim ---------
{
  const forbidden = [
    /(average|typical|median) (cost|price)[^.]{0,40}(sauna|hot tub|cold plunge)/i,
    /saunas in Ireland (cost|range)/i,
    /PlotNua (holds|has) \d+ (sauna|wellness)/i,
  ];
  const hit = forbidden.map(r => VIS.match(r)).find(Boolean);
  hit ? bad('P1', `market-wide price claim: "${hit[0]}"`)
      : ok('P1', 'no market-wide price comparison and no Atlas wellness claim');
}

// --- E1 · no recommendation-engine route -----------------------------------
{
  const m = src.match(/your-plot\.html\?discovery=[a-z-]+/);
  m ? bad('E1', `a recommendation-engine route was added: ${m[0]} — Cluster 2 forbids it`)
    : ok('E1', 'no ?discovery= route; the page does not imply wellness matching');
}

// --- S1 · schema honesty ----------------------------------------------------
{
  const m = src.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/);
  if (!m) bad('S1', 'UNREACHABLE: no JSON-LD block found');
  else {
    let data = null;
    try { data = JSON.parse(m[1]); } catch (e) { bad('S1', `JSON-LD does not parse: ${e.message}`); }
    if (data) {
      const types = (data['@graph'] || []).map(n => n['@type']).sort();
      const expect = ['BreadcrumbList', 'Organization', 'WebPage', 'WebSite'];
      const banned = /"@type"\s*:\s*"(FAQPage|Question|Answer|Product|Offer|AggregateOffer|Review|AggregateRating)"/;
      if (banned.test(m[1])) bad('S1', `banned schema type: ${m[1].match(banned)[1]}`);
      else if (JSON.stringify(types) !== JSON.stringify(expect)) bad('S1', `graph is [${types}], expected [${expect}]`);
      else ok('S1', `JSON-LD parses; graph = ${types.join(', ')}; no FAQPage/Product/Offer`);
    }
  }
}

// --- S2 · dateModified and sitemap lastmod agree ---------------------------
{
  const dm = (src.match(/"dateModified":\s*"([0-9-]+)"/) || [])[1];
  const lm = (sitemap.match(/discovery-garden-retreat\.html<\/loc>\s*<lastmod>([0-9-]+)<\/lastmod>/) || [])[1];
  if (!dm || !lm) bad('S2', `UNREACHABLE: dateModified=${dm} lastmod=${lm}`);
  else if (dm !== lm) bad('S2', `dateModified ${dm} != sitemap lastmod ${lm}`);
  else ok('S2', `dateModified = sitemap lastmod = ${dm}`);
}

// --- J1 · Discovery identity and supplier honesty preserved ----------------
{
  const toks = {
    'H1': '<h1>Garden Retreat</h1>',
    'title': '<title>Garden Saunas, Hot Tubs &amp; Cold Plunges in Ireland | PlotNua</title>',
    'canonical': '<link rel="canonical" href="https://plotnua.ie/discovery-garden-retreat.html">',
    'no-commercial-relationship note': 'PlotNua has no commercial relationship with any supplier named on this page',
    // 14 Oct 2026 (final publication consistency corrections): MyCabin, held
    // from the directory, left the comparison; the sauna example is now
    // Hansa24's Lisette on summerhouse24.ie. GR10 refuses a held maker's name.
    'Summerhouse24 (Hansa24)': 'summerhouse24.ie', 'Gardenhouse24': 'gardenhouse24.ie', 'Timbertrove': 'timbertrove.com',
  };
  const miss = Object.entries(toks).filter(([, t]) => !src.includes(t)).map(([k]) => k);
  miss.length ? bad('J1', `lost: ${miss.join(', ')}`)
              : ok('J1', 'H1, title, canonical, supplier set and the no-relationship note intact');
}

// --- J2 · the unresolved questions survive ---------------------------------
{
  const need = [
    'only a Section 5 declaration settles that for your garden',
    "Whether a sauna's heater changes anything about the",
    'Whether a council counts a free-standing tub towards the 30',
    "Exactly which electrical jobs need a registered contractor's certificate",
  ];
  const miss = need.filter(s => !VIS.includes(s));
  miss.length ? bad('J2', `unresolved item(s) dropped: ${miss.length} of ${need.length}`)
              : ok('J2', 'all four carried-forward unresolved questions present');
}

// --- J3 · Cluster 1 is cited, not retold -----------------------------------
{
  // Scoped to the planning block. The page also carries a Living in the
  // Garden card in the related-Discoveries navigation, which satisfied a
  // page-wide test even with the in-context citation removed. Found by C-J3.
  const a = src.indexOf('<h3>Planning</h3>'), b = src.indexOf('<div class="practical-group">', a);
  if (a < 0 || b < 0) bad('J3', 'UNREACHABLE: planning block not found');
  else src.slice(a, b).includes('href="discovery-living-in-the-garden.html"')
    ? ok('J3', 'Cluster 1 cited in context as the parent for the full conditions')
    : bad('J3', 'the in-context citation to Living in the Garden is missing from the planning block');
}

console.log(`\n${pass + fail} checks, ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
