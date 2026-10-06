/* SHADOW ONLY — the proposed five-band architecture and the price-basis
   protection that must ship with it. Nothing here is loaded by your-plot.html.

   The live AS_BUDGET_BANDS is UNCHANGED and is not imported, so this file
   cannot alter it. The five-band map below is additive and stands alone. */

export const SHADOW_BUDGET_BANDS = {
  'under-10k': { lo: 0,     hi: 10000 },
  '10k-20k':   { lo: 10000, hi: 20000 },
  '20k-30k':   { lo: 20000, hi: 30000 },
  '30k-50k':   { lo: 30000, hi: 50000 },   // NEW
  '50k-plus':  { lo: 50000, hi: Infinity },// NEW — replaces 30k-plus
};
export const SHADOW_BUDGET_LABEL = {
  'under-10k': 'Under €10,000',
  '10k-20k':   '€10,000–€20,000',
  '20k-30k':   '€20,000–€30,000',
  '30k-50k':   '€30,000–€50,000',
  '50k-plus':  '€50,000+',
};
export const SHADOW_BUDGET_CURRENCY = 'EUR';

/* The retired key. Kept ONLY so a guard can assert it is gone from the live
   map's shadow successor; it is never offered to a homeowner. */
export const RETIRED_BAND_KEY = '30k-plus';

/* ── BUDGET FIT v2 ────────────────────────────────────────────────────────
   Four values, where the live function has three. The extra one is the whole
   point of the brief's section 5.

     2  a SAFE known price inside the stated band
     1  price unknown, OR a non-euro price, OR basis UNKNOWN — all "cannot say"
     0  a SAFE known price outside the stated band
    -1  a price that exists but must not earn a verdict at all

   -1 is NOT "out of budget". It means the figure is unsafe or self-
   contradicting, so neither 2 nor 0 can be claimed. Consumers must suppress
   the product's budget claim rather than rank it as a miss.

   UNKNOWN BASIS DOES NOT INVALIDATE THE NUMBER. A genuine published price
   whose commercial basis nobody has recorded still scores 2 or 0; it simply
   carries "Check what's included" beside it. That is the brief's distinction
   between (A) genuine price / basis unknown and (B) unsafe or conflicted
   evidence, and it is the single most load-bearing line in this file. */
export function shadowBudgetFit(product, band) {
  if (!band) return 1;
  const price = product ? product.price : null;
  if (typeof price !== 'number' || !isFinite(price) || price <= 0) return 1;
  if (product.currency !== SHADOW_BUDGET_CURRENCY) return 1;   // no authorised rate exists
  if (product.priceSafeForMatching === false) return -1;       // exists, cannot be trusted
  return (price >= band.lo && price <= band.hi) ? 2 : 0;
}

/* ── HOMEOWNER PRICE TREATMENT ───────────────────────────────────────────
   PRICE + exactly one evidence-earned line. The internal class never appears.
   An unmapped class falls to the honest line, not to silence. */
const BASIS_LINE = {
  ERECTED_WITH_SERVICES:     'Installed, with electrics',
  ERECTED_SERVICES_EXCLUDED: 'Installed. Electrics and plumbing extra',
  ERECTED_SERVICES_UNKNOWN:  'Delivered and assembled',
  DELIVERED_SHELL:           'Delivered. Installation extra',
  KIT_SELF_ASSEMBLY:         'Structure only. Assembly extra',
  EX_WORKS:                  'Collection from the maker',
  UNKNOWN:                   "Check what's included",
};
export const HOMEOWNER_BASIS_LINES = Object.freeze({ ...BASIS_LINE });

export function shadowPriceTreatment(product, money) {
  /* money() is the caller's existing formatter, so this function invents no
     currency symbol and no rounding of its own. */
  const price = product ? product.price : null;
  const has = typeof price === 'number' && isFinite(price) && price > 0;
  if (!has) return { figure: null, prefix: null, line: null, vat: null, suppressed: false };

  /* An unsafe figure is not shown as a price claim. Phase 2 found seven of
     these: third-party press figures, organisation-wide headlines, a German
     retail price for a product not sold in Ireland. */
  if (product.priceSafeForMatching === false) {
    return { figure: null, prefix: null, line: 'Price not confirmed', vat: null, suppressed: true };
  }

  const line = BASIS_LINE[product.priceBasisClass] || BASIS_LINE.UNKNOWN;

  /* VAT is qualified ONLY where Atlas states it. There is no inference, no
     default, and no rate unless a rate was published. */
  let vat = null;
  if (product.vatStatus === 'Yes') vat = product.vatRate ? ('includes VAT at ' + product.vatRate + '%') : 'includes VAT';
  else if (product.vatStatus === 'No') vat = 'excludes VAT';

  return {
    figure: money(price, product.currency),
    prefix: product.priceIsRangeFloor ? 'From' : null,
    line, vat, suppressed: false,
  };
}

export function renderShadowPrice(product, money) {
  const t = shadowPriceTreatment(product, money);
  if (!t.figure) return t.line || null;
  return [[t.prefix, t.figure].filter(Boolean).join(' '),
          [t.line, t.vat].filter(Boolean).join(' · ')].join('\n');
}
