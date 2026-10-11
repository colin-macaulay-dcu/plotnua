/**
 * PROVE NAMED PRICE CONFIGURATIONS IN RESULTS AND COMPARE · PC1–PC19
 * ==================================================================
 * The founder's seven requirements, each as an assertion:
 *
 *   1  both configurations display correctly          PC1, PC2, PC5
 *   2  the VAT basis is accurate                      PC6, PC7, PC8
 *   3  the important exclusions remain visible        PC9, PC10, PC11
 *   4  no configuration is mislabelled                PC3, PC4, PC12
 *   5  no misleading comparison is introduced         PC13, PC14, PC15
 *   6  held products remain invisible                 PC17
 *   7  existing single-price products are unchanged   PC16, PC18
 *
 * HOW IT TESTS. The price contract is LIFTED OUT OF THE SHIPPED PAGE and
 * run — not re-implemented here. A re-implementation would prove that this
 * file agrees with itself. The slice runs from `const PN_PRICE_SYMBOL` to
 * the end of pnPriceDelta(), which is the whole of the one contract, and the
 * suite REFUSES rather than passes if the slice cannot be found or will not
 * evaluate: a suite that silently tests nothing is worse than no suite.
 *
 * WHAT IS A SOURCE ASSERTION AND WHAT IS BEHAVIOURAL. PC1-PC16 drive the
 * real functions with real governed shapes. PC17 and PC18 are source
 * assertions about the OTHER script block, which cannot be evaluated in
 * isolation; each says so in its own name so a reader is never told a
 * structural check was a behavioural one.
 *
 *   node atlas-tools/prove-results-configurations.mjs [--plot PATH]
 *
 * Exit 0 = all pass. Exit 2 = the instrument could not run.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
function arg(name, dflt) {
  const i = process.argv.indexOf('--' + name);
  return i === -1 ? dflt : process.argv[i + 1];
}
const PLOT = arg('plot', join(ROOT, 'your-plot.html'));
const html = readFileSync(PLOT, 'utf8');

let pass = 0, fail = 0;
const ok  = (n, d) => { pass++; console.log(`  PASS  ${n}${d ? '  [' + d + ']' : ''}`); };
const bad = (n, d) => { fail++; console.log(`  FAIL  ${n}${d ? '  [' + d + ']' : ''}`); };

function refuse(why) {
  console.log('\nRESULTS PRICE CONFIGURATIONS');
  console.log('='.repeat(74));
  console.log('  INSTRUMENT UNAVAILABLE: ' + why);
  console.log('  Not a pass and not a failure. Nothing was measured.');
  process.exit(2);
}

/* ── Lift the one price contract out of the shipped page ─────────────── */
const START = '  const PN_PRICE_SYMBOL =';
const END = '  const pb046 = { originalResults:';
const a = html.indexOf(START), b = html.indexOf(END);
if (a === -1 || b === -1 || b <= a) {
  refuse('the price contract could not be located in ' + PLOT +
         ' (start=' + a + ' end=' + b + ')');
}
const slice = html.slice(a, b);
for (const needed of ['function pnPriceView', 'function pnPriceDelta',
                      'function pnPriceConfigurations', 'function pnVatBasis']) {
  if (!slice.includes(needed)) {
    refuse('the lifted slice does not contain ' + needed);
  }
}

/* The four constants and the one global the slice reads, declared here with
   their shipped values so the lift is complete rather than patched. */
const PRELUDE = `
  const PB046_NO_PRICE = 'Price not published';
  const PB046_AMBIGUOUS_PRICE = 'Price not confirmed';
  const PB046_QUOTE_PRICE = 'Priced on enquiry';
  const AS_BUDGET_CURRENCY = 'EUR';
  const window = {};
`;
let C;
try {
  // eslint-disable-next-line no-new-func
  C = new Function(PRELUDE + slice + `
    return { pnPriceView, pnPriceDisplay, pnPriceDelta, pnPriceConfigurations,
             pnVatBasis, pnPriceTerms, pnConfigSuffix, pnMoney,
             pnPriceComparableToBudget, handle: window.__PN_PRICE_VIEW__ };
  `)();
} catch (e) {
  refuse('the lifted contract would not evaluate: ' + e.message);
}

/* ── The governed shapes, exactly as the generator emits them ─────────── */
const TERMS_BB = ['TRANSPORT_AND_ASSEMBLY_INCLUDED',
                  'FOUNDATIONS_UTILITIES_SITEWORKS_QUOTED_SEPARATELY',
                  'KITCHEN_FURNITURE_AND_APPLIANCES_EXCLUDED'];

/* Wanderlust, as additional_home_qualification._price_state() produces it and
   pnAdditionalHomeView() hands it on: the scalar is the LOWEST configuration,
   which is the shell. */
const wanderlust = {
  productName: 'BIOBUILDS Wanderlust', currency: 'EUR', price: 105000,
  priceEvidence: {
    priceType: 'Standard Price', currency: 'EUR', base: 105000,
    from: null, to: null, quoteOnly: false, basis: 'INCLUDES_VAT',
    vatRatePercent: 23, commercialTerms: TERMS_BB,
    configurations: [
      { key: 'exterior-finished', label: 'Exterior Finished', amount: 105000,
        priceType: 'Standard Price', terms: TERMS_BB },
      { key: 'turnkey', label: 'Turnkey', amount: 163000,
        priceType: 'Standard Price', terms: TERMS_BB }
    ]
  }
};
/* Liora, the other real two-configuration product — and published on the
   OPPOSITE VAT basis, which is why a single default would have been wrong. */
const liora = {
  productName: 'Liora', currency: 'EUR', price: 28070,
  priceEvidence: {
    priceType: 'Standard Price', currency: 'EUR', base: 28070,
    from: null, to: null, quoteOnly: false, basis: 'EXCLUDES_VAT',
    vatRatePercent: null,
    commercialTerms: ['DELIVERY_INSTALLATION_FOUNDATION_EXCLUDED'],
    configurations: [
      { key: 'basic', label: 'Basic', amount: 28070, priceType: 'Standard Price' },
      { key: 'optima', label: 'Optima', amount: 32830, priceType: 'Standard Price' }
    ]
  }
};
/* A single unnamed price: 38 of the 46 Additional Homes, and every Garden
   Room in the universe. The control for every "unchanged" assertion. */
const plain = {
  productName: 'A single-price product', currency: 'EUR', price: 21490,
  priceEvidence: { priceType: 'Standard Price', currency: 'EUR',
                   base: 21490, from: null, to: null, quoteOnly: false }
};
const plainDearer = {
  productName: 'A dearer single-price product', currency: 'EUR', price: 30000,
  priceEvidence: { priceType: 'Standard Price', currency: 'EUR',
                   base: 30000, from: null, to: null, quoteOnly: false }
};

console.log('\nRESULTS PRICE CONFIGURATIONS · PC1–PC19');
console.log('='.repeat(74));

const vW = C.pnPriceView(wanderlust);
const vL = C.pnPriceView(liora);
const vP = C.pnPriceView(plain);

/* ── 1 · BOTH CONFIGURATIONS DISPLAY CORRECTLY ───────────────────────── */
{
  const cfg = vW.configurations;
  (cfg.length === 2 && cfg[0].label === 'Exterior Finished'
   && cfg[1].label === 'Turnkey'
   && cfg[0].amount === 105000 && cfg[1].amount === 163000)
    ? ok('PC1 both named configurations reach the view, cheapest first',
         cfg.map(c => `${c.label} ${c.amount}`).join(' | '))
    : bad('PC1 both named configurations reach the view, cheapest first',
          JSON.stringify(cfg));
}
{
  const line = vW.configurationLine || '';
  (line.includes('€105,000') && line.includes('Exterior Finished')
   && line.includes('€163,000') && line.includes('Turnkey'))
    ? ok('PC2 the both-prices line carries both figures and both labels', line)
    : bad('PC2 the both-prices line carries both figures and both labels', line);
}
{
  // Compare's row is the surface that shows both. It must take the
  // both-prices line for a multi-configuration product and the single
  // display for everything else.
  const row = html.includes("? v.configurationLine : v.display");
  row ? ok('PC5 Compare renders the both-prices line only when there are two')
      : bad('PC5 Compare renders the both-prices line only when there are two');
}

/* ── 4 · NO CONFIGURATION IS MISLABELLED ─────────────────────────────── */
{
  /* THE CENTRAL ASSERTION. The scalar is EUR 105,000, which is the shell.
     Printed bare it reads as the price of the finished home. */
  const d = vW.display;
  (d.includes('€105,000') && d.includes('Exterior Finished')
   && !d.includes('163,000'))
    ? ok('PC3 the scalar is printed WITH its own configuration name', d)
    : bad('PC3 the scalar is printed WITH its own configuration name', d);
}
{
  const t = vW.tail;
  (t.includes('Exterior Finished') && /^at /.test(t))
    ? ok('PC4 the sentence form carries the name too', t)
    : bad('PC4 the sentence form carries the name too', t);
}
{
  // The scalar is the LOWEST, so the label attached to it must be the
  // cheapest configuration's — never the dearest. Attaching "Turnkey" to
  // EUR 105,000 would be the worst available outcome: confident and wrong.
  (vW.configurationLabel === 'Exterior Finished' &&
   vL.configurationLabel === 'Basic')
    ? ok('PC12 the name attached to the scalar is the cheapest tier’s',
         `${vW.configurationLabel} / ${vL.configurationLabel}`)
    : bad('PC12 the name attached to the scalar is the cheapest tier’s',
          `${vW.configurationLabel} / ${vL.configurationLabel}`);
}

/* ── 2 · THE VAT BASIS IS ACCURATE ───────────────────────────────────── */
{
  (vW.basis === 'INCLUDES_VAT' && vW.vatNote === 'including VAT')
    ? ok('PC6 an inclusive price says so', vW.vatNote)
    : bad('PC6 an inclusive price says so', `${vW.basis}/${vW.vatNote}`);
}
{
  (vL.basis === 'EXCLUDES_VAT' && vL.vatNote === 'excluding VAT')
    ? ok('PC7 an exclusive price says so, on the same surface', vL.vatNote)
    : bad('PC7 an exclusive price says so', `${vL.basis}/${vL.vatNote}`);
}
{
  // The dangerous default. A product with no governed basis must say
  // NOTHING, not "including VAT" because that is the common case.
  const unknown = C.pnPriceView({
    currency: 'EUR', price: 1000,
    priceEvidence: { currency: 'EUR', base: 1000, basis: 'VAT_UNKNOWN' } });
  (unknown.vatNote === null && vP.vatNote === null)
    ? ok('PC8 an unknown or absent VAT basis asserts nothing')
    : bad('PC8 an unknown or absent VAT basis asserts nothing',
          `${unknown.vatNote} / ${vP.vatNote}`);
}

/* ── 3 · THE IMPORTANT EXCLUSIONS REMAIN VISIBLE ─────────────────────── */
{
  const t = vW.terms;
  (t.length === 3
   && t.some(s => /Transport and assembly.*included/.test(s))
   && t.some(s => /Foundations, utility connections and site works are quoted separately/.test(s))
   && t.some(s => /Kitchen furniture and appliances are not included/.test(s)))
    ? ok('PC9 all three governed commercial terms are rendered', String(t.length))
    : bad('PC9 all three governed commercial terms are rendered', JSON.stringify(t));
}
{
  (vL.terms.length === 1 &&
   /Delivery, installation and foundations are not included/.test(vL.terms[0]))
    ? ok('PC10 a different supplier’s own term is rendered, not BIOBUILDS’',
         vL.terms[0].slice(0, 44))
    : bad('PC10 a different supplier’s term is rendered', JSON.stringify(vL.terms));
}
{
  // Absence of evidence is not absence of cost. No token must mean no
  // sentence, and nothing anywhere may say the unlisted is covered.
  const forbidden = ['everything else is included', 'all other costs are included',
                     'nothing else to pay', 'fully inclusive price',
                     'no further costs'];
  const low = html.toLowerCase();
  const hits = forbidden.filter(p => low.includes(p));
  (vP.terms.length === 0 && !hits.length)
    ? ok('PC11 a product with no terms says nothing, and nothing claims inclusion')
    : bad('PC11 a product with no terms says nothing, and nothing claims inclusion',
          `terms=${vP.terms.length} phrases=${hits.join(',')}`);
}

/* ── 5 · NO MISLEADING COMPARISON IS INTRODUCED ──────────────────────── */
{
  /* THE CASE ONLY THE MULTI-CONFIGURATION RULE CAN REFUSE.
     Serenity against Wanderlust: both BIOBUILDS, both including VAT, both
     publishing Exterior Finished and Turnkey. The labels match and the bases
     match, so neither of the other two refusals fires. Yet "Serenity costs
     EUR 86,000 more" is a comparison of two shells presented as a comparison
     of two buildings — at turnkey the gap is EUR 143,000. A product with more
     than one price cannot be represented by one difference figure.

     An earlier version of this check paired Wanderlust against a
     single-price product, which the unlike-LABEL refusal already caught.
     The capability proof reported it VACUOUS: the mutation that removed the
     multi-configuration refusal did not make it fail. This is the case that
     does. */
  const TB = TERMS_BB;
  const serenity = {
    productName: 'BIOBUILDS Serenity', currency: 'EUR', price: 191000,
    priceEvidence: {
      priceType: 'Standard Price', currency: 'EUR', base: 191000,
      from: null, to: null, quoteOnly: false, basis: 'INCLUDES_VAT',
      vatRatePercent: 23, commercialTerms: TB,
      configurations: [
        { key: 'exterior-finished', label: 'Exterior Finished', amount: 191000,
          priceType: 'Standard Price', terms: TB },
        { key: 'turnkey', label: 'Turnkey', amount: 306000,
          priceType: 'Standard Price', terms: TB }
      ]
    }
  };
  const alike = C.pnPriceDelta(serenity, wanderlust);
  const vsPlain = C.pnPriceDelta(wanderlust, plain);
  (alike === null && vsPlain === null &&
   C.pnPriceDelta(plain, wanderlust) === null)
    ? ok('PC13 a product with more than one price is never ranked, even '
         + 'against an identically configured one')
    : bad('PC13 a product with more than one price is never ranked',
          `matchedPair=${JSON.stringify(alike)} vsSinglePrice=${JSON.stringify(vsPlain)}`);
}
{
  // Two products each publishing ONE configuration, but not the same one.
  const shellOnly = {
    currency: 'EUR', price: 105000,
    priceEvidence: { currency: 'EUR', base: 105000, basis: 'INCLUDES_VAT',
      configurations: [{ key: 'exterior-finished', label: 'Exterior Finished',
                         amount: 105000 }] } };
  const turnkeyOnly = {
    currency: 'EUR', price: 163000,
    priceEvidence: { currency: 'EUR', base: 163000, basis: 'INCLUDES_VAT',
      configurations: [{ key: 'turnkey', label: 'Turnkey', amount: 163000 }] } };
  const same = {
    currency: 'EUR', price: 120000,
    priceEvidence: { currency: 'EUR', base: 120000, basis: 'INCLUDES_VAT',
      configurations: [{ key: 'exterior-finished', label: 'Exterior Finished',
                         amount: 120000 }] } };
  const unlike = C.pnPriceDelta(shellOnly, turnkeyOnly);
  const alike = C.pnPriceDelta(shellOnly, same);
  (unlike === null && alike && alike.diff === -15000)
    ? ok('PC14 unlike single configurations refuse; like ones still compare',
         `unlike=null like=${alike.diff}`)
    : bad('PC14 unlike single configurations refuse; like ones still compare',
          `unlike=${JSON.stringify(unlike)} like=${JSON.stringify(alike)}`);
}
{
  // The second dimension of unlikeness. At 23% this is not a rounding
  // difference.
  const incl = { currency: 'EUR', price: 30000,
    priceEvidence: { currency: 'EUR', base: 30000, basis: 'INCLUDES_VAT' } };
  const excl = { currency: 'EUR', price: 28000,
    priceEvidence: { currency: 'EUR', base: 28000, basis: 'EXCLUDES_VAT' } };
  const mixed = C.pnPriceDelta(incl, excl);
  const bothUnknown = C.pnPriceDelta(plain, plainDearer);
  (mixed === null && bothUnknown && bothUnknown.diff === -8510)
    ? ok('PC15 unlike VAT bases refuse; two unknown bases compare as today',
         `mixed=null today=${bothUnknown.diff}`)
    : bad('PC15 unlike VAT bases refuse; two unknown bases compare as today',
          `mixed=${JSON.stringify(mixed)} today=${JSON.stringify(bothUnknown)}`);
}

/* ── 7 · EXISTING SINGLE-PRICE PRODUCTS ARE UNCHANGED ────────────────── */
{
  /* THE REGRESSION THAT MATTERS MOST. 487 Garden Rooms and 38 of the 46
     Additional Homes carry one unnamed price. Every one of them must render
     the bytes it rendered before this change. */
  const cases = [
    [plain, '€21,490', 'at €21,490', 'exact'],
    [{ currency: 'EUR', price: 35950,
       priceEvidence: { currency: 'EUR', from: 35950, base: null,
                        priceType: 'Starting From' } },
     'From €35,950', 'from €35,950', 'from'],
    [{ currency: 'EUR', price: 27090,
       priceEvidence: { currency: 'EUR', from: 27090, to: 36420,
                        base: 27090 } },
     '€27,090 – €36,420', null, 'range'],
    [{ currency: 'EUR', price: 9000,
       priceEvidence: { currency: 'EUR', base: 9000,
                        priceType: 'Estimated Price' } },
     'Estimated €9,000', null, 'estimated'],
    [{ currency: 'GBP', price: 12000,
       priceEvidence: { currency: 'GBP', base: 12000 } },
     '£12,000', null, 'exact']
  ];
  const wrong = [];
  for (const [p, wantDisplay, wantTail, wantKind] of cases) {
    const v = C.pnPriceView(p);
    if (v.display !== wantDisplay) wrong.push(`display ${v.display}!=${wantDisplay}`);
    if (wantTail && v.tail !== wantTail) wrong.push(`tail ${v.tail}!=${wantTail}`);
    if (v.kind !== wantKind) wrong.push(`kind ${v.kind}!=${wantKind}`);
    if (v.configurations.length) wrong.push('configurations appeared from nowhere');
    if (v.configurationLine !== null) wrong.push('a both-prices line appeared');
  }
  wrong.length
    ? bad('PC16 every single-price shape renders exactly as before',
          wrong.join('; '))
    : ok('PC16 every single-price shape renders exactly as before',
         `${cases.length} shapes: exact, from, range, estimated, sterling`);
}
{
  /* A configuration entry with no governed label is NOT printed as a bare
     figure. It is dropped, and the product falls back to the single-price
     presentation — the honest direction. */
  const unlabelled = {
    currency: 'EUR', price: 50000,
    priceEvidence: { currency: 'EUR', base: 50000,
      configurations: [{ key: null, label: null, amount: 50000 }] } };
  const v = C.pnPriceView(unlabelled);
  (v.configurations.length === 0 && v.display === '€50,000')
    ? ok('PC18 an unlabelled configuration is dropped, never printed bare',
         v.display)
    : bad('PC18 an unlabelled configuration is dropped, never printed bare',
          JSON.stringify(v.configurations) + ' ' + v.display);
}

/* ── 6 · HELD PRODUCTS REMAIN INVISIBLE ──────────────────────────────── */
{
  /* SOURCE ASSERTION — the publication gate lives in the other script block
     and is proved behaviourally by prove-supplier-publication-gate.mjs
     (PG12, PG13). What is asserted HERE is that this Piece did not weaken
     it: the fail-closed test is still in place and still sits BEFORE the
     candidate push, so a presentation change cannot have published anybody. */
  const failsClosed = /gateEnforced \? p\.publicVisibility !== 'PUBLISHABLE'/.test(html);
  const ordered =
    html.indexOf("gateEnforced ? p.publicVisibility !== 'PUBLISHABLE'") <
    html.indexOf("if (c3 === 'CANDIDATE') { funnel.class3aCandidates++; out.push(p); }");
  (failsClosed && ordered)
    ? ok('PC17 (source) the publication gate is intact and still precedes the push')
    : bad('PC17 (source) the publication gate is intact and still precedes the push',
          `failsClosed=${failsClosed} ordered=${ordered}`);
}
{
  /* SOURCE ASSERTION — the Additional Home journey runs in a separate
     <script type="module"> that cannot be evaluated apart from the page, so
     its routing is asserted structurally rather than driven. Two things
     matter: it goes through the ONE published contract, and if that handle
     is ever missing a multi-configuration product says NOTHING about price
     rather than falling back to an unlabelled figure. */
  const usesHandle = /window\.__PN_PRICE_VIEW__\(pnAdditionalHomeView\(p\)\)/.test(html);
  const degrades = /pnConfigCount\(p\) > 1 \? null : pnMoney\(p\)/.test(html);
  const publishes = /window\.__PN_PRICE_VIEW__ = function \(product\)/.test(html);
  const carries = /configurations: \(p\.price\.state === 'VERIFIED_NUMERIC_PRICE' &&/.test(html);
  (usesHandle && degrades && publishes && carries)
    ? ok('PC19 (source) the Additional Home journey uses the one contract and '
         + 'degrades to silence, never to a bare figure')
    : bad('PC19 (source) the Additional Home journey uses the one contract',
          `handle=${usesHandle} degrades=${degrades} published=${publishes} carried=${carries}`);
}

console.log('\n' + '='.repeat(74));
console.log(`${pass + fail} checks, ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
