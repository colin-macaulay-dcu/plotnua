// STAGE 3D-D2 — R-MATCH at the time of use, in the real page code (node:vm).
//   node atlas-tools/rmatch-runtime.mjs <your-plot.html> <search.js> <universe.json> <index.json> <YYYY-MM-DD>
// Lifts Your Plot's pnPriceToday / pnPriceIsCurrent / pnPriceStateOf / pnPriceView /
// pnOrderTiedGroup / bydTrueCostPoint and the real search.js, freezes the clock at
// noon Europe/Dublin on the given day, and prints a JSON report. Planted-fault runs
// pass mutated copies of the same files.
import fs from 'node:fs'; import vm from 'node:vm'; import { createRequire } from 'node:module';
const [yp, sj, un, ix, day] = process.argv.slice(2, 7);
const T = new Date(day + 'T12:00:00Z').getTime();
class FixedDate extends Date { constructor(...a) { a.length ? super(...a) : super(T); } static now() { return T; } }
const page = fs.readFileSync(yp, 'utf8');
const slice = (a, z) => { const i = page.indexOf(a), j = page.indexOf(z, i); if (i < 0 || j < 0) throw new Error('slice ' + a); return page.slice(i, j); };
const fn = (name) => { const i = page.indexOf('function ' + name + '('); if (i < 0) throw new Error('fn ' + name);
  let d = 0, j = page.indexOf('{', i); for (; j < page.length; j++) { if (page[j] === '{') d++; else if (page[j] === '}') { d--; if (!d) break; } }
  return page.slice(i, j + 1); };
const code = 'const AS_BUDGET_CURRENCY = "EUR";\n' + slice('const PB046_NO_PRICE', 'function pnPriceDelta') + '\n' +
  slice('function pnVatPosition', '/* ISSUE 005 PIECE D4b') + '\n' + slice('const BYD_INSTALL_CLASS', '/* ---- SELECTION') + '\n' +
  fn('pnOrderTiedGroup') + '\n' + fn('budgetFit') + '\n' +
  ';globalThis.__x = { pnPriceToday, pnPriceIsCurrent, pnPriceStateOf, pnPriceView, pnOrderTiedGroup, budgetFit, note: bydTrueCostPoint };';
const ctx = { window: {}, Date: FixedDate, Intl, console }; vm.createContext(ctx); vm.runInContext(code, ctx);
const X = ctx.__x;
const U = JSON.parse(fs.readFileSync(un, 'utf8')).products;
const out = { today: X.pnPriceToday(), yp: {}, order: null, search: {} };
for (const p of U) {
  const v = X.pnPriceView(p); let n = null; try { const c = X.note(p); n = c ? c.body : null; } catch (e) { n = 'ERR ' + e.message; }
  out.yp[p.id] = { state: X.pnPriceStateOf(p), current: X.pnPriceIsCurrent(p), kind: v.kind, display: v.display, figure: v.figure, note: n };
}
// A tied group: what orders it, and what does not. Pool-shaped products as normalisation makes them.
const pool = (p) => ({ id: p.id, price: (X.pnPriceIsCurrent(p) && !(p.priceEvidence || {}).presentationHold) ? p.price : undefined,
  priceFreshUntil: p.priceFreshUntil, priceState: X.pnPriceStateOf(p), priceEvidence: p.priceEvidence, currency: p.currency });
const want = JSON.parse(process.env.RM_GROUP || '[]');
if (want.length) {
  const group = want.map(id => ({ product: pool(U.find(p => p.id === id)) }));
  out.order = X.pnOrderTiedGroup(group).map(e => e.product.id);
  out.raworder = X.pnOrderTiedGroup(want.map(id => ({ product: U.find(p => p.id === id) }))).map(e => e.product.id);
  out.budget = Object.fromEntries(want.map(id => { const p = U.find(q => q.id === id); return [id, X.budgetFit(Object.assign({}, p), { lo: 0, hi: Infinity })]; }));
}
// Search: the real runtime module under the frozen clock.
const sctx = { module: { exports: {} }, Date: FixedDate, Intl, console, self: undefined };
sctx.exports = sctx.module.exports; vm.createContext(sctx);
vm.runInContext(fs.readFileSync(sj, 'utf8'), sctx);
const S = sctx.module.exports; const idx = JSON.parse(fs.readFileSync(ix, 'utf8'));
out.search.today = S.pnsToday();
out.search.products = Object.fromEntries(idx.records.filter(r => r.type === 'product').map(r => [r.id, { price: S.pnsPrice(r), unverified: S.pnsUnverified(r) }]));
out.search.suppliers = Object.fromEntries(idx.records.filter(r => r.type === 'supplier').map(r => [r.name, S.pnsRange(r)]));
for (const q of (JSON.parse(process.env.RM_QUERIES || '[]'))) {
  const res = S.search(idx, q);
  out.search['q:' + q] = { products: ((res.groups || {}).product || []).map(p => p.id),
                           suppliers: ((res.groups || {}).supplier || []).map(s => s.name) };
}
process.stdout.write(JSON.stringify(out));
