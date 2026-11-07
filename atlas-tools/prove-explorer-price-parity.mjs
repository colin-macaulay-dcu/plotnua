#!/usr/bin/env node
/* PLOTNUA · DISC-008 Maker Explorer ↔ product page price parity (founder approval, 4 Nov 2026).

   Runs the product page's OWN price contract -- pnPriceView() and its helpers, lifted
   verbatim from your-plot.html at run time, never copied -- on every garden-room product,
   exactly as normalizePoolProduct() hands it over (price, currency, priceEvidence), and
   compares the result with that product's line in the Living in the Garden Maker Explorer.

     P1  every garden-room product in the universe is listed once, with a price label
     P2  a product the page prices shows the page's own figure, verbatim
     P3  quote-only on the page   -> "Price on enquiry"
         ambiguous / none / zero  -> "Price unavailable"  (never a figure)
     P4  wording: Verified EUR carries its VAT position; Verified GBP "· UK price";
         every other priced record reads "Indicative price: ..." (GBP/USD keep their
         region note); no figure is ever shown in a currency the record does not carry
     P5  fault test: each planted mismatch is caught
     P7  Stage 3D-D2 (R-MATCH): a price the page reads as not currently verified
         (Partially Verified, undated, range-level, expired) reads
         "Price not currently verified" in the explorer -- never a figure

   node atlas-tools/prove-explorer-price-parity.mjs */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const page = fs.readFileSync(path.join(ROOT, 'your-plot.html'), 'utf8');
const a = page.indexOf('const PB046_NO_PRICE');
const z = page.indexOf('function pnPriceDelta');
if (a < 0 || z < a) { console.log('PRICE PARITY · REFUSED — pnPriceView not found in your-plot.html'); process.exit(2); }
const ctx = { window: {} };
vm.createContext(ctx);
vm.runInContext(page.slice(a, z) + '\n;globalThis.__view = pnPriceView; globalThis.__gov = pnPriceGoverned; globalThis.__cur = pnPriceIsCurrent; globalThis.__st = pnPriceStateOf;', ctx);
const view = ctx.__view;

const U = JSON.parse(fs.readFileSync(path.join(ROOT, 'garden-room-recommendation-universe-v1.json'), 'utf8')).products;
const html = fs.readFileSync(path.join(ROOT, 'discovery-living-in-the-garden.html'), 'utf8');
const cfg = JSON.parse(html.match(/id="mx-data">([\s\S]*?)<\/script>/)[1]);

function rows(cfg) {
  const tab = cfg.tabs.find(t => t.key === 'gardenRooms');
  const out = new Map(); let dup = 0;
  for (const m of tab.makers) for (const p of m.p) { if (out.has(p[0])) dup++; out.set(p[0], p.length > 4 ? p[4] : ''); }
  return { out, dup };
}

function check(cfg) {
  const bad = [];
  const { out, dup } = rows(cfg);
  if (dup) bad.push('P1 duplicated products: ' + dup);
  if (out.size !== U.length) bad.push(`P1 listed ${out.size}, universe ${U.length}`);
  const tally = {};
  for (const r of U) {
    const line = out.get(r.id);
    if (line === undefined) { bad.push('P1 not listed: ' + r.id); continue; }
    if (!line) { bad.push('P1 no price label: ' + r.id); continue; }
    /* Mirrors normalizePoolProduct(): Stage 3D-D2 carries priceState and
       priceFreshUntil, and only an eligible, current price arrives as a number.
       A HELD price keeps its number here (as before) so P6 can rebuild the
       explorer's held line from the page's own figure. */
    const P0 = { priceState: r.priceState, priceFreshUntil: r.priceFreshUntil };
    const gov = ctx.__gov(P0);
    const P = { price: (typeof r.price === 'number' && isFinite(r.price) && r.price > 0
                        && (!gov || r.priceState === 'held' || ctx.__cur(P0))) ? r.price : undefined,
                currency: r.currency || undefined, priceEvidence: r.priceEvidence || undefined,
                priceFreshUntil: (typeof r.priceFreshUntil === 'string') ? r.priceFreshUntil : undefined,
                priceState: gov ? ctx.__st(P0) : undefined };
    const v = view(P);
    const e = r.priceEvidence || {};
    let k;
    // P6 (NOOK Stage 3A, 6 Nov 2026): a HELD price. The page shows the qualification and no
    // figure; the explorer shows the figure, "excluding VAT", then the same qualification.
    if (v.kind === 'held') {
      k = 'held';
      const q = (e.presentationHold || {}).qualification || '';
      const bare = view(Object.assign({}, P, { priceEvidence: Object.assign({}, e, { presentationHold: undefined }) }));
      if (!q || !v.display.includes(q.replace(/^Ex works\.\s*/, ''))) bad.push(`P6 ${r.id}: page held price without its qualification: "${v.display}"`);
      if (v.known || v.amount != null || /\d/.test(v.display)) bad.push(`P6 ${r.id}: page shows a figure for a held price: "${v.display}"`);
      const incl = (e.presentationHold || {}).vatBasis === 'included';
      // Stage 3C: a WITHHELD figure (Rayco) is shown nowhere; the explorer shows label + qualification.
      const withheld = (e.presentationHold || {}).figure === 'withheld';
      const want = withheld ? (e.presentationHold.label + '. ' + q) : bare.display + (incl ? '. ' : ' excluding VAT. ') + q;
      if ((!withheld && !bare.known) || line !== want) bad.push(`P6 ${r.id}: held price shown without its qualification: "${line}"`);
      if (withheld && /\d/.test(line)) bad.push(`P6 ${r.id}: a withheld figure is shown: "${line}"`);
      tally[k] = (tally[k] || 0) + 1; continue;
    }
    if (v.kind === 'unverified') { k = 'not currently verified'; if (line !== 'Price not currently verified') bad.push(`P7 ${r.id}: page not currently verified, explorer "${line}"`); }
    else if (v.kind === 'quote-only') { k = 'enquiry'; if (line !== 'Price on enquiry') bad.push(`P3 ${r.id}: page quote-only, explorer "${line}"`); }
    else if (!v.known) { k = 'unavailable'; if (line !== 'Price unavailable') bad.push(`P3 ${r.id}: page ${v.kind}, explorer "${line}"`); }
    else if (!['EUR', 'GBP', 'USD'].includes(v.currency)) { k = 'unavailable'; if (line !== 'Price unavailable') bad.push(`P4 ${r.id}: ${v.currency} figure shown`); }
    else {
      if (!line.includes(v.display)) bad.push(`P2 ${r.id}: page "${v.display}", explorer "${line}"`);
      const verified = e.status === 'Verified';
      if (verified && v.currency === 'EUR') {
        k = 'verified EUR';
        /* Stage 3D-C2: the exact VAT tail the record's own position calls for. A terms-based
           VAT-inclusive price (vatBasis "supplier-terms") reads "incl. VAT (supplier's terms)". */
        const vat = String(e.includesVat || '').trim().toLowerCase();
        const tail = vat === 'yes' ? (e.vatBasis === 'supplier-terms' ? ' incl. VAT (supplier\u2019s terms)' : ' incl. VAT')
                   : (vat === 'no' || vat === 'excluding vat') ? ' excl. VAT' : ' · VAT not stated';
        if (line !== v.display + tail)
          bad.push(`P4 ${r.id}: verified EUR without its exact VAT position: "${line}"`);
        if (e.vatBasis === 'supplier-terms') k = 'verified EUR (supplier terms)';
      } else if (verified && v.currency === 'GBP') {
        k = 'verified GBP';
        if (line !== v.display + ' · UK price') bad.push(`P4 ${r.id}: verified GBP wording: "${line}"`);
      } else {
        k = 'indicative';
        const note = v.currency === 'GBP' ? ' · UK price' : v.currency === 'USD' ? ' · US price' : '';
        if (line !== 'Indicative price: ' + v.display + note) bad.push(`P4 ${r.id}: indicative wording: "${line}"`);
      }
      for (const [sym, c] of [['€', 'EUR'], ['£', 'GBP'], ['$', 'USD']])
        if (line.includes(sym) && v.currency !== c) bad.push(`P4 ${r.id}: ${c} symbol on a ${v.currency} record`);
    }
    tally[k] = (tally[k] || 0) + 1;
  }
  return { bad, tally };
}

const real = check(cfg);
if (real.bad.length) {
  for (const b of real.bad.slice(0, 40)) console.log('FAIL ' + b);
  console.log(`PRICE PARITY · REFUSED — ${real.bad.length} problem(s)`); process.exit(2);
}

// P5 fault test: plant one mismatch of each kind in a copy of the configuration
const tab = () => JSON.parse(JSON.stringify(cfg));
const find = (c, pred) => { for (const m of c.tabs.find(t => t.key === 'gardenRooms').makers) for (const p of m.p) if (pred(p)) return p; };
const faults = [
  ['a verified price changed', c => { const p = find(c, p => (p[4] || '').includes('VAT not stated')); p[4] = p[4].replace('\u20ac', '\u20ac1'); }, 'P2'],
  ['a quote-only shown as unavailable', c => { find(c, p => p[4] === 'Price on enquiry')[4] = 'Price unavailable'; }, 'P3'],
  ['an ambiguous price shown as a figure', c => { find(c, p => p[4] === 'Price unavailable')[4] = '€9,999 · VAT not stated'; }, 'P3'],
  ['sterling shown as euro', c => { const p = find(c, p => (p[4] || '').endsWith('UK price')); p[4] = p[4].replace('£', '€'); }, 'P2'],
  /* Stage 3D-D2: no Partially Verified EUR figure is published any more, so the
     wording fault is planted the other way round -- a verified figure relabelled. */
  ['a verified price relabelled as indicative', c => { const p = find(c, p => /^(From )?\u20ac[\d,]+ /.test(p[4] || '')); p[4] = 'Indicative price: ' + p[4]; }, 'P4'],
  ['the VAT position dropped', c => { const p = find(c, p => (p[4] || '').endsWith(' · VAT not stated')); p[4] = p[4].replace(' · VAT not stated', ''); }, 'P4'],
  ['the supplier-terms VAT basis dropped', c => { const p = find(c, p => (p[4] || '').endsWith(' incl. VAT (supplier\u2019s terms)')); p[4] = p[4].replace(' (supplier\u2019s terms)', ''); }, 'P4'],
  ['a supplier-terms VAT basis claimed for a price-level position', c => { const p = find(c, p => /€[\d,]+ incl\. VAT$/.test(p[4] || '')); p[4] = p[4] + ' (supplier\u2019s terms)'; }, 'P4'],
  ['a regional held price shown without its qualification', c => { const p = find(c, p => (p[4] || '').includes('. Price includes VAT, delivery and installation in Dublin and Wicklow only.')); p[4] = p[4].split('. Price includes')[0] + ' incl. VAT'; }, 'P6'],
  ['a withheld figure shown in the explorer', c => { const p = find(c, p => (p[4] || '').startsWith('Price on request. Rayco does not publish')); p[4] = 'Indicative price: From \u20ac29,500'; }, 'P6'],
  ['a held price shown without its qualification', c => { const p = find(c, p => (p[4] || '').includes(' excluding VAT. Ex works.')); p[4] = p[4].split(' excluding VAT. ')[0] + ' excl. VAT'; }, 'P6'],
  ['an unverified price shown as a figure', c => { find(c, p => p[4] === 'Price not currently verified')[4] = 'Indicative price: \u20ac19,950'; }, 'P7'],
  ['a product delisted', c => { const ms = c.tabs.find(t => t.key === 'gardenRooms').makers; ms[0].p.shift(); }, 'P1'],
];
let caught = 0;
for (const [name, fn, code] of faults) {
  const c = tab(); fn(c);
  const hit = check(c).bad.some(b => b.startsWith(code));
  console.log(`  ${hit ? 'CAUGHT' : 'MISSED'}  ${name}`); caught += hit ? 1 : 0;
}
if (caught !== faults.length) { console.log(`PRICE PARITY · FAULTS MISSED — ${caught}/${faults.length}`); process.exit(2); }
console.log(`PRICE PARITY · OK — ${U.length} garden-room products match the product page (${Object.entries(real.tally).map(([k, v]) => v + ' ' + k).join(', ')}); faults ${caught}/${faults.length} caught`);
