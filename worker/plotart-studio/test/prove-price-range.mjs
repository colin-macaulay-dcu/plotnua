// PROVE · price range (prepared 23 Nov 2026; NOT switched on in production). Run three times, by PR_MODE:
//   pilot (default settings: EUR 9,999.99 per artwork, EUR 10,000 linked-purchase safeguard; production today)
//   open  (PRICE_RANGE=open; the EUR 10,000 safeguard kept)   ·   open-noaml (PRICE_RANGE=open, AML_LINKED_LIMIT_CENTS=none)
// Setup is the basket suite's (same mock Stripe, synthetic artists and TEST texts: no real payment, no real artist).
//   PR_MODE=open node test/prove-price-range.mjs
// (original header of the shared setup follows)
// PROVE · multi-artist basket on the managed checkout (migration 0019; src/basket.js, src/basket-public.js).
// Local only: Miniflare D1 with the CURRENT schema plus the PROPOSED migration 0019 applied on top, the real Studio Worker
// and the real public checkout Worker, a stateful MOCK Stripe API (every outbound call is intercepted; nothing reaches
// Stripe), synthetic artists, and SYNTHETIC texts. Webhooks are signed here with a test secret exactly as Stripe signs them.
//   node test/prove-basket.mjs
import { cpSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { createHash, createHmac } from 'node:crypto';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { statements } from './sql.mjs';

const HERE = new URL('..', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(typeof d === 'string' ? d : JSON.stringify(d)).slice(0, 700)}]` : ''}`); };
const sha = b => createHash('sha256').update(b).digest('hex');
const ago = days => new Date(Date.now() - days * 86400_000).toISOString();

const FIX = 'test/.price-fixture/';
const MODE = process.env.PR_MODE || 'pilot';
const EXTRA = { pilot: {}, open: { PRICE_RANGE: 'open' }, 'open-noaml': { PRICE_RANGE: 'open', AML_LINKED_LIMIT_CENTS: 'none' } }[MODE];
if (!EXTRA) throw new Error('PR_MODE must be pilot, open or open-noaml');
rmSync(HERE + FIX, { recursive: true, force: true });
cpSync(HERE + 'src', HERE + FIX + 'src', { recursive: true });
const ADD = '<!DOCTYPE html><title>TEST ONLY · synthetic payment addendum</title><p>Synthetic.</p>';
const BPT = '<!DOCTYPE html><title>TEST ONLY · synthetic buyer terms</title><p>Synthetic.</p>';
const TERMS = { 'PA-PAY-TEST-01': { title: 'Payment Pilot Addendum (TEST)', kind: 'artist_payment_addendum', html: ADD, html_sha256: sha(ADD) },
  'PA-BPT-TEST-01': { title: 'Buyer Purchase Terms (TEST)', kind: 'buyer_purchase_terms', html: BPT, html_sha256: sha(BPT) } };
writeFileSync(HERE + FIX + 'src/payment-terms.js', `export const PAYMENT_TERMS = ${JSON.stringify(TERMS)};\n`);
const { basketDoc, LIVE_BASKET_DOCS } = await import(HERE + 'src/basket-terms.js');
const BBT = await basketDoc('PA-BBT-TEST-01', false), BAA = await basketDoc('PA-BAA-TEST-01', false);

/* ---------------------------------------------------------------- mock Stripe: platform (no Stripe-Account) and connected accounts */
const WHSEC = 'whsec_test_' + 'x'.repeat(24), WHSEC_P = 'whsec_test_platform_' + 'y'.repeat(20);
import { M, stripe, enterCard } from './mock-stripe-basket.mjs';
const sign = (raw, t = Math.floor(Date.now() / 1000), secret = WHSEC) => `t=${t},v1=${createHmac('sha256', secret).update(`${t}.${raw}`).digest('hex')}`;
let EV = 0;
const evt = (type, object, account = null) => ({ id: `evt_test_b${++EV}`, object: 'event', type, livemode: false, created: Math.floor(Date.now() / 1000), ...(account ? { account } : {}), data: { object } });

let S, BR = null;
try {
console.log(`PROVE · price range · mode ${MODE}`);
const ORIGIN = 'https://checkout.local';
const ENVV = { CHECKOUT_MESSAGE_RETRY_MINUTES: '0', CHECKOUT_PILOT_ENABLED: 'true', BASKET_ENABLED: 'true', BASKET_COMMISSION_FREE: 'with_processing_consent', STRIPE_SECRET_KEY: 'sk_test_mockkey123', STRIPE_BASKET_KEY: 'rk_test_basketkey456',
  STRIPE_PUBLISHABLE_KEY: 'pk_test_mockpublishable', STRIPE_WEBHOOK_SECRET: WHSEC, STRIPE_WEBHOOK_SECRET_PLATFORM: WHSEC_P, STRIPE_API_BASE: 'https://stripe.mock', CHECKOUT_ORIGIN: ORIGIN, GALLERY_ORIGIN: 'https://plotnua.ie', ...EXTRA };
S = await start({ port: 8875, env: ENVV, script: FIX + 'src/index.js', checkout: { script: FIX + 'src/checkout-public.js', env: ENVV }, outbound: stripe });
const { db } = S, CW = S.checkoutWorker;
const mig = readFileSync(HERE + 'migrations/0019_multi_artist_basket.sql', 'utf8');
let migErr = null; for (const s of statements(mig)) { try { await db.prepare(s).run(); } catch (e) { migErr = e.message; } }
check('M1 proposed migration 0019 applies cleanly on top of the current schema (0017 included)', !migErr, migErr);
let again = null; for (const s of statements(mig)) { try { await db.prepare(s).run(); } catch (e) { again = e.message; } }
check('M2 migration 0019 is re-runnable (IF NOT EXISTS throughout)', !again, again);
const tablesBefore = (await db.prepare("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").all()).results.map(r => r.name);
check('M3 migration 0019 is additive: only new basket tables', ['basket_terms', 'basket_artist_events', 'artwork_delivery_offers', 'checkout_baskets', 'basket_lines', 'basket_events'].every(t => tablesBefore.includes(t)));
const mig20 = readFileSync(HERE + 'migrations/0020_basket_consents.sql', 'utf8');
let m20 = null; for (let k = 0; k < 2; k++) for (const s of statements(mig20)) { try { await db.prepare(s).run(); } catch (e) { m20 = m20 || e.message; } }
const tablesAfter20 = (await db.prepare("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").all()).results.map(r => r.name);
check('M4 migration 0020 applies, is re-runnable and adds exactly one new table (basket_consents)', !m20 && tablesAfter20.filter(t => !tablesBefore.includes(t)).join() === 'basket_consents', { m20, added: tablesAfter20.filter(t => !tablesBefore.includes(t)) });
const mig22 = readFileSync(HERE + 'migrations/0022_delivery_safety.sql', 'utf8');
let m22 = null; for (let k = 0; k < 2; k++) for (const s of statements(mig22)) { try { await db.prepare(s).run(); } catch (e) { m22 = m22 || e.message; } }
const tablesAfter22 = (await db.prepare("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").all()).results.map(r => r.name);
check('M5 migration 0022 (delivery safety) applies, is re-runnable and adds only its three new tables', !m22 && tablesAfter22.filter(t => !tablesAfter20.includes(t)).sort().join() === 'delivery_offer_events,delivery_offer_reviews,order_overdue_alerts', { m22, added: tablesAfter22.filter(t => !tablesAfter20.includes(t)) });

const call = async (method, path, email, body) => { const r = await S.mf.dispatchFetch(S.url + path, { method, headers: { ...(email ? { 'Cf-Access-Jwt-Assertion': token(email) } : {}), 'X-Studio': '1', 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j, t }; };
/* delivery safety: the founder approves every current offer that has no problems (as on the Review desk) */
const approveOffers = async (only = null) => { const j = (await call('GET', '/api/admin/checkout/baskets/offers', FOUNDER)).j; let n = 0;
  for (const o of j.offers) if ((!only || only.includes(o.artwork_id)) && !o.review.approved && !o.problems.length) {
    const r = await call('POST', `/api/admin/checkout/baskets/offers/${o.artwork_id}/review`, FOUNDER, { decision: 'approved', version: o.version, sha256: o.sha256, confirm: true, statement: j.statement }); if (r.s === 200) n++; }
  return n; };
const pub = async (method, path, { json = null, form = null, origin = ORIGIN, headers = {}, raw = null } = {}) => { const r = await CW.fetch(ORIGIN + path, { method, redirect: 'manual',
  headers: { ...(json || form ? { 'Content-Type': json ? 'application/json' : 'application/x-www-form-urlencoded', Origin: origin } : {}), ...headers }, body: json ? JSON.stringify(json) : form ? new URLSearchParams(form).toString() : raw ?? undefined });
  const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, t, j, loc: r.headers.get('Location'), h: r.headers }; };
const hook = async (e, secret = WHSEC) => { const body = JSON.stringify(e); const r = await pub('POST', '/v1/stripe/webhook', { raw: body, headers: { 'Stripe-Signature': sign(body, undefined, secret), 'Content-Type': 'application/json' } }); return { s: r.s, j: r.j }; };
const q = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results;
const one = (sql, ...b) => db.prepare(sql).bind(...b).first();
/* Optional staging preview: BASKET_SCREENSHOTS=<dir> renders the real pages (served by the checkout Worker above) in Chromium,
   with SYNTHETIC artwork images (abstract gradients made here; no real artwork) standing in for the gallery's image files. */
const SHOTS = process.env.BASKET_SCREENSHOTS || null;
const ART = {};
async function shot(name, path, { width = 1280, height = 900, basket = null, full = true } = {}) {
  if (!SHOTS) return;
  const { createRequire } = await import('node:module');
  const pw = createRequire(process.env.PLAYWRIGHT_FROM || '/tmp/claude-0/studio-tools/package.json')('playwright');
  if (!BR) {
    BR = await pw.chromium.launch();
    const p0 = await BR.newPage({ viewport: { width: 600, height: 600 } });
    const G = { g1: 'radial-gradient(circle at 30% 35%,#d9a066,#7a3e2a 45%,#20262b 80%)', g2: 'linear-gradient(160deg,#2f4f5f,#9fb8ad 40%,#e9e2cf 55%,#c26d3a)', g3: 'conic-gradient(from 40deg at 60% 40%,#1c2833,#6c8a9b,#e4d5b7,#8c4a2f,#1c2833)', g4: 'radial-gradient(ellipse at 70% 60%,#f1e3c6,#b5893f 35%,#3a3a2e 75%)' };
    for (const [k, g] of Object.entries(G)) { await p0.setContent(`<body style="margin:0"><div style="width:600px;height:${k === 'g2' ? 760 : 600}px;background:${g}"></div></body>`); await p0.setViewportSize({ width: 600, height: k === 'g2' ? 760 : 600 }); ART[k] = await p0.screenshot(); }
    await p0.close();
  }
  const ctx = await BR.newContext({ viewport: { width, height }, deviceScaleFactor: 2 });
  await ctx.route('**/*', async route => {
    const u = new URL(route.request().url());
    if (u.origin === ORIGIN) { const req = route.request(); const r = await CW.fetch(req.url(), { method: req.method(), headers: { ...req.headers(), Origin: ORIGIN }, body: req.postData() || undefined, redirect: 'manual' });
      return route.fulfill({ status: r.status, headers: Object.fromEntries(r.headers), body: Buffer.from(await r.arrayBuffer()) }); }
    if (u.hostname === 'plotnua.ie') { const k = (u.pathname.match(/(g\d)\.png$/) || [])[1]; return k ? route.fulfill({ status: 200, contentType: 'image/png', body: ART[k] }) : route.fulfill({ status: 404, body: '' }); }
    if (/fonts\.(googleapis|gstatic)\.com$/.test(u.hostname)) return route.continue().catch(() => route.abort());
    return route.abort();
  });
  const page = await ctx.newPage();
  if (basket) { await page.goto(ORIGIN + '/basket?seed=1'); await page.evaluate(b => localStorage.setItem('pa-basket-v1', JSON.stringify(b)), basket); }
  await page.goto(ORIGIN + path, { waitUntil: 'networkidle' }).catch(() => {});
  await page.waitForTimeout(700);
  await page.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: full });
  await ctx.close();
}

// ---- synthetic world: a Gallery Artist on 15%, a Founding Artist (0%), an artist not in baskets
const GAL = 'gal@example.test', FND = 'fnd@example.test', NOB = 'nob@example.test';
await seedPublished(db, { id: 'agal', slug: 'gale', email: GAL, name: 'Gale Gallery', works: 4, publishedAt: ago(30) });
await seedPublished(db, { id: 'afnd', slug: 'fia', email: FND, name: 'Fia Founding', works: 3, number: 3, publishedAt: ago(100) });
await seedPublished(db, { id: 'anob', slug: 'nob', email: NOB, name: 'Nóra NoBasket', works: 1, publishedAt: ago(30) });
await db.prepare("UPDATE artists SET founding = 0 WHERE id IN ('agal','anob')").run();
const FAKE = 'a'.repeat(64);
await db.prepare("INSERT INTO gallery_agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at) VALUES ('PA-GAA-2026-11','gallery_artist_agreement','t','fixed',?,?,'2018-01-01T00:00:00Z',?)").bind(FAKE, FAKE, ago(0)).run();
for (const a of ['agal', 'anob']) {
  await db.prepare(`INSERT INTO gallery_agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, method, statement, created_at) VALUES (?,?,?,'PA-GAA-2026-11',?,?,?,?, 'x','studio_checkbox','test',?)`).bind('gaa' + a, 'ev' + a, a, FAKE, FAKE, ago(20), a + '@example.test', ago(20)).run();
  await db.prepare("INSERT INTO artist_terms (artist_id, track, commission_bp, set_by, created_at, updated_at) VALUES (?,'gallery_artist',1500,?,?,?)").bind(a, FOUNDER, ago(20), ago(20)).run();
}
for (const [id, t] of Object.entries(TERMS)) await db.prepare('INSERT INTO payment_terms (doc_id, kind, title, html_sha256, effective_at, created_at) VALUES (?,?,?,?,?,?)').bind(id, t.kind, t.title, t.html_sha256, '2018-01-01T00:00:00Z', ago(0)).run();
for (const d of [BBT, BAA]) await db.prepare('INSERT INTO basket_terms (doc_id, kind, title, html_sha256, effective_at, created_at) VALUES (?,?,?,?,?,?)').bind(d.doc_id, d.kind, d.title, d.html_sha256, '2018-01-01T00:00:00Z', ago(0)).run();
// prices: Gale's works EUR 1,200 and 800; Fia's EUR 450; one Gale work price on request
await db.prepare("UPDATE artworks SET price_eur = 1200 WHERE id = 'wagal1'").run(); await db.prepare("UPDATE artworks SET price_eur = 800 WHERE id = 'wagal2'").run();
await db.prepare("UPDATE artworks SET price_eur = 450 WHERE artist_id = 'afnd'").run(); await db.prepare("UPDATE artworks SET price_on_request = 1, price_eur = NULL WHERE id = 'wagal4'").run();
for (const a of ['agal', 'afnd']) {   // the published snapshot carries the same prices
  const v = await one('SELECT snapshot FROM versions WHERE artist_id = ?', a); const snap = JSON.parse(v.snapshot);
  for (const w of snap.works) { const r = await one('SELECT price_eur, price_on_request FROM artworks WHERE id = ?', w.id); w.price_eur = r.price_eur; w.price_on_request = r.price_on_request; }
  await db.prepare('UPDATE versions SET snapshot = ? WHERE artist_id = ?').bind(JSON.stringify(snap), a).run();
}
const SELLER = n => ({ legal_name: n, trading_name: null, address: '1 Studio Lane, Dublin 8, Ireland', returns_address: null, email: 'seller@example.test', phone: '+353 1 555 0100', trader_status: 'trader', vat_number: null, confirm: true });
for (const [e, n] of [[GAL, 'Gale Gallery'], [FND, 'Fia Founding'], [NOB, 'Nora NoBasket']]) {
  await call('POST', '/api/checkout/opt-in', e, { accept: true, doc_id: 'PA-PAY-TEST-01', html_sha256: sha(ADD) });
  await call('POST', '/api/checkout/onboarding', e, { country: 'IE' });
  await call('PUT', '/api/checkout/seller-profile', e, SELLER(n));
}
for (const a of ['agal', 'afnd', 'anob']) await call('POST', `/api/admin/checkout/accounts/${a}/refresh`, FOUNDER, {});
const ACC = Object.fromEntries((await q('SELECT artist_id, account_id FROM payment_accounts')).map(r => [r.artist_id, r.account_id]));
const prof = await call('GET', '/api/checkout', GAL);
check('S1 artists are in the existing payment pilot with ready Stripe accounts and seller information', prof.j.membership.ready === true && prof.j.seller_problems.length === 0 && Object.keys(ACC).length === 3, { sp: prof.j.seller_problems, acc: ACC });


// ---------------------------------------------------------------- the price range
console.log('— representative purchases at EUR 4,500, EUR 14,000 and EUR 30,000 (Gale Gallery, Gallery Artist, 15%)');
const PRICES = { wagal1: 4500, wagal2: 14000, wagal3: 30000 };
const DELIV = { wagal1: 8000, wagal2: 25000, wagal3: 60000 };
for (const [id, p] of Object.entries(PRICES)) await db.prepare('UPDATE artworks SET price_eur = ?, price_on_request = 0, availability = ? WHERE id = ?').bind(p, 'available', id).run();
{ const v = await one("SELECT snapshot FROM versions WHERE artist_id = 'agal'"), snap = JSON.parse(v.snapshot);
  for (const w of snap.works) if (PRICES[w.id]) { w.price_eur = PRICES[w.id]; w.price_on_request = 0; w.availability = 'available'; }
  await db.prepare("UPDATE versions SET snapshot = ? WHERE artist_id = 'agal'").bind(JSON.stringify(snap)).run(); }
await call('POST', '/api/checkout/basket/opt-in', GAL, { accept: true, doc_id: BAA.doc_id, html_sha256: BAA.html_sha256 });
{ const v = (await call('GET', '/api/checkout/basket', GAL)).j; await call('POST', '/api/checkout/basket/seller-disclosure', GAL, { accept: true, statement: v.disclosure_statement, subject_sha256: v.seller_info.subject_sha256 }); }
const DEL = (cover) => ({ dispatch_days: 5, delivery_days: 10, collection_county: 'Dublin', unpacked_cm: '160 × 120 × 4', packed_cm: '175 × 135 × 15', weight_kg: 18, medium: 'Oil on linen', framing: 'Unframed', glazing: 'None',
  condition: 'Excellent', access_notes: null, organiser: 'artist', packer: 'artist', transport_booker: 'artist', transport_contracting_party: 'artist', transport_payer: 'artist',
  transporter_name: 'Synthetic Fine Art Shipping', installation: 'not_applicable', import_costs: 'not_applicable', cover_type: 'transit_insurance', cover_provider: 'Synthetic Fine Art Underwriting (SIMULATED)', covered_value_cents: cover,
  insured_party: 'transporter', cover_confirmation_ref: 'SIM-FA-0001', cover_confirmed_by: 'Synthetic Fine Art Underwriting', cover_confirmed_on: '2026-11-23', valuation_basis: 'Sale price', excess_cents: 0, exclusions: null,
  cover_period: 'Collection to signed delivery', claims_contact: 'claims@example.test', delivery_window: '5–8 working days', tracking: 'Tracked, signature on delivery', signed_receipt: true, condition_photos: true,
  return_method: 'Same shipper, insured', return_address: '1 Studio Lane, Dublin 8', return_cost_cents: 20000, return_cost_basis: 'estimated_maximum', return_arranged_by: 'buyer',
  shipment_confirmation_ref: 'SFAS-2026', shipment_confirmed_by: 'Synthetic Fine Art Shipping', shipment_confirmed_on: '2026-11-23' });
// insurance must cover at least the artwork price, at every price
let r = await call('PUT', '/api/checkout/basket/offers/wagal3', GAL, { confirm: true, delivery_cents: DELIV.wagal3, delivery: DEL(2_000_000) });
check('R1 a delivery offer whose transit insurance is below the artwork price is refused (EUR 20,000 cover on a EUR 30,000 work)', r.s === 409 && /cover at least/.test(r.j.error), r.j);
for (const id of Object.keys(PRICES)) await call('PUT', `/api/checkout/basket/offers/${id}`, GAL, { confirm: true, delivery_cents: DELIV[id], delivery: DEL(PRICES[id] * 100 + 100000) });
const items = async ids => (await pub('GET', '/api/basket/items?ids=' + ids.join(','))).j.items;
let it = await items(Object.keys(PRICES));
check('R2 before PlotArt approves the delivery offers, none of the three can be bought online (at any price)', it.every(x => !x.ok), it.map(x => x.reason));
await approveOffers(Object.keys(PRICES));
it = await items(Object.keys(PRICES));
const ok = Object.fromEntries(it.map(x => [x.id, x.ok]));
const EXPECT = { pilot: { wagal1: true, wagal2: false, wagal3: false }, open: { wagal1: true, wagal2: false, wagal3: false }, 'open-noaml': { wagal1: true, wagal2: true, wagal3: true } }[MODE];
check(`R3 after approval, which works the basket offers in mode ${MODE}: ${JSON.stringify(EXPECT)}`, JSON.stringify(ok) === JSON.stringify(EXPECT), it);
const why = async id => (await call('GET', `/api/admin/checkout/baskets/eligibility?ids=${id}`, FOUNDER)).j.items[0].why;
if (MODE === 'pilot') check('R4 pilot (production today): above EUR 9,999.99 the reason is the current online price range (no "pilot price limit" wording)', (await why('wagal2')) === 'above the current online price range' && (await why('wagal3')) === 'above the current online price range');
if (MODE === 'open') check('R4 open range with the EUR 10,000 safeguard kept: the EUR 14,000 and EUR 30,000 works are refused by the safeguard, not by a price ceiling', (await why('wagal2')) === 'total at or above the online purchase limit' && (await why('wagal3')) === 'total at or above the online purchase limit');
// the artist and founder wording: no "pilot price limit"
const rd = (await call('GET', '/api/checkout/basket/readiness', GAL)).j, fa = (await call('GET', '/api/admin/checkout/baskets/artists', FOUNDER)).j.artists.find(a => a.id === 'agal');
check('R5 neither the artist nor the founder is told about a "pilot price limit"', !/pilot price limit/i.test(JSON.stringify([rd, fa])), [rd.online, fa.online]);
// migration 0023 (the database part of the price range): applied as ONE transaction, as the protected workflow applies it
const APPLY_0023 = process.env.PR_NO_0023 !== '1';
let MIGRATED = false;
async function migrate() {
  if (!APPLY_0023 || MIGRATED) return; MIGRATED = true;
  const before = { orders: await q('SELECT * FROM checkout_orders ORDER BY id'), master: await q("SELECT type, name, tbl_name FROM sqlite_master WHERE tbl_name = 'checkout_orders' ORDER BY type, name") };
  const allBefore = await q("SELECT type, name, sql FROM sqlite_master WHERE type IN ('trigger','index') AND sql IS NOT NULL ORDER BY name");
  const sql = readFileSync(HERE + 'migrations/0023_price_range.sql', 'utf8');
  let err = null; try { await db.batch(statements(sql).map(x => db.prepare(x))); } catch (e) { err = e.message; }
  const after = { orders: await q('SELECT * FROM checkout_orders ORDER BY id'), master: await q("SELECT type, name, tbl_name FROM sqlite_master WHERE tbl_name = 'checkout_orders' ORDER BY type, name") };
  const ddl = (await one("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'checkout_orders'")).sql;
  const fk = await q('PRAGMA foreign_key_check');
  const allAfter = await q("SELECT type, name, sql FROM sqlite_master WHERE type IN ('trigger','index') AND sql IS NOT NULL ORDER BY name");
  check('MG2b every trigger and index in the database is back with identical SQL (including the nine that protect other records)', !err && JSON.stringify(allBefore) === JSON.stringify(allAfter), { n: [allBefore.length, allAfter.length] });
  check('MG1 migration 0023 applies as one transaction; every order row is carried over unchanged (all 48 columns)', !err && before.orders.length > 0 && JSON.stringify(before.orders) === JSON.stringify(after.orders), { err, n: before.orders.length });
  check('MG2 only the artwork price check changes (to Stripe’s EUR 999,999.99); the three indexes and both triggers are back', /BETWEEN 100 AND 99999999\)/.test(ddl) && !/BETWEEN 100 AND 999999\)/.test(ddl)
    && JSON.stringify(before.master.map(x => x.type + ':' + x.name).filter(x => !x.startsWith('table'))) === JSON.stringify(after.master.map(x => x.type + ':' + x.name).filter(x => !x.startsWith('table'))) && !/checkout_orders_0023/.test(ddl), { ddl: ddl.slice(0, 120), before: before.master, after: after.master });
  check('MG3 every reference to checkout_orders still holds (no foreign-key problem anywhere)', fk.length === 0, fk);
  const o = after.orders.find(x => x.status === 'paid'), nev = (await one('SELECT COUNT(*) AS n FROM order_events WHERE order_id = ?', o.id)).n;
  let del = null; try { await db.prepare('DELETE FROM checkout_orders WHERE id = ?').bind(o.id).run(); } catch (e) { del = e.message; }
  let ev = null; try { await db.prepare('DELETE FROM order_events WHERE order_id = ?').bind(o.id).run(); } catch (e) { ev = e.message; }
  let ret = null; try { await db.prepare("UPDATE checkout_orders SET retain_until = '2099-12-31' WHERE id = ? AND retain_until IS NOT NULL").bind(o.id).run(); await db.prepare("UPDATE checkout_orders SET retain_until = '2000-01-01' WHERE id = ?").bind(o.id).run(); } catch (e) { ret = e.message; }
  check('MG4 the record-keeping rules still apply after the rebuild (on the paid order): it cannot be deleted, its history cannot be deleted, a fixed retention date cannot move',
    /kept until its retention period/.test(del || '') && nev > 0 && /never|kept|removed|retention/i.test(ev || '') && (o.retain_until ? /fixed once set/.test(ret || '') : true), { del, ev, nev, ret, retain: o.retain_until });
  const rowsNow = await q('SELECT * FROM checkout_orders ORDER BY id');
  let rerun = null; try { await db.batch(statements(sql).map(x => db.prepare(x))); } catch (e) { rerun = e.message; }
  check('MG5 running it a second time is harmless: every row, trigger and index is unchanged', !rerun && JSON.stringify(await q('SELECT * FROM checkout_orders ORDER BY id')) === JSON.stringify(rowsNow)
    && JSON.stringify(await q("SELECT type, name, sql FROM sqlite_master WHERE type IN ('trigger','index') AND sql IS NOT NULL ORDER BY name")) === JSON.stringify(allAfter), rerun);
}
// full checkout of each buyable work, by separate buyers (so linked purchases do not add up), through the mock Stripe API
const BUY = (id, n) => ({ artworks: [id], accept_terms: 'PA-BBT-TEST-01', name: `Buyer ${n}`, email: `buyer${n}@example.test`, address_line1: '7 Harbour Road', address_line2: '', town: 'Kinsale', county: 'Cork', eircode: 'P17 XY12', phone: '+353 21 555 0199', island: 'no' });
let n = 0;
for (const [id, eur] of Object.entries(PRICES)) {
  n++;
  const total = eur * 100 + DELIV[id], commission = Math.floor(eur * 100 * 1500 / 10000);
  const cB = M.calls.length;
  if (id === 'wagal2') await migrate();   // after the first sale exists, so its order is carried through the rebuild
  r = await pub('POST', '/basket/checkout', { json: { ...BUY(id, n), expected_total_cents: total } });
  if (!EXPECT[id]) { check(`R6 EUR ${eur.toLocaleString('en-IE')}: refused before any card page or payment (${MODE})`, r.s === 409 && !M.calls.slice(cB).some(c => c.path === '/v1/checkout/sessions'), r.j); continue; }
  const sess = Object.values(M.sessions).at(-1), bid = (await one('SELECT id FROM checkout_baskets WHERE lower(buyer_email) = lower(?)', `buyer${n}@example.test`) || {}).id;
  enterCard(sess.id, {}); await hook(evt('checkout.session.completed', M.sessions[sess.id]), WHSEC_P);
  const B = await one('SELECT * FROM checkout_baskets WHERE id = ?', bid);
  const O = await one('SELECT o.* FROM checkout_orders o JOIN basket_lines l ON l.order_id = o.id WHERE l.basket_id = ?', B.id);
  const auth = M.calls.slice(cB).find(c => c.path === '/v1/payment_intents' && c.method === 'POST');
  const led = await q('SELECT kind, amount_cents FROM order_ledger WHERE order_id = ?', O.id), L = k => (led.find(x => x.kind === k) || {}).amount_cents;
  console.log(`     EUR ${eur.toLocaleString('en-IE')}: total ${(total / 100).toFixed(2)} · charge ${auth && auth.f.amount} · application fee ${auth && auth.f.application_fee_amount} · artist artwork ${L('artist_artwork')} · status ${O.status}`);
  check(`R6 EUR ${eur.toLocaleString('en-IE')} + EUR ${(DELIV[id] / 100).toFixed(2)} delivery: one direct charge of the full total on the artist's account, 15% commission on the artwork only as the application fee, booked in the ledger, paid`,
    B.status === 'paid' && O.status === 'paid' && O.artwork_cents === eur * 100 && auth && Number(auth.f.amount) === total && Number(auth.f.application_fee_amount) === commission && auth.acct === ACC.agal
    && L('charge') === total && L('commission') === commission && L('artist_artwork') === eur * 100 - commission, { B: B.status, O: O.status, f: auth && auth.f, led });
}
// managed-checkout quote (single artwork from an enquiry) at the same prices
console.log('— managed-checkout quote from an enquiry at the same prices');
if (!Object.values(EXPECT).slice(1).some(Boolean)) await migrate();   // modes where no large sale ran: migrate before the quotes
for (const [eur, ref] of [[4500, 'PA-E-261123-QQ4500'], [14000, 'PA-E-261123-QQ1400'], [30000, 'PA-E-261123-QQ3000']]) {
  await db.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at) VALUES (?,?,?,?, 'relay', ?,?,?, 'relay', ?)`).bind('el' + eur, ref, 'agal', 'wagal4', ago(1), 0, null, ago(1)).run();
  const c = await call('POST', '/api/admin/checkout/orders', FOUNDER, { artist_id: 'agal', artwork_id: 'wagal4', enquiry_ref: ref, buyer_email: `q${eur}@example.test` });
  const u = c.s === 200 && await call('PUT', `/api/admin/checkout/orders/${c.j.order.id}`, FOUNDER, { artwork_cents: eur * 100, delivery_cents: 20000, delivery: { ...DEL(eur * 100 + 100000), destination: '3 Quay Street, Galway', destination_country: 'IE' } });
  const s2 = u && u.s === 200 && await call('POST', `/api/admin/checkout/orders/${c.j.order.id}/send`, FOUNDER, {});
  const expectOk = MODE === 'open-noaml' || eur < 10000, rangeOk = MODE !== 'pilot' || eur < 10000;
  const o = c.s === 200 && await one('SELECT artwork_cents, delivery_cents, commission_cents FROM checkout_orders WHERE id = ?', c.j.order.id);
  check(`R7 quote EUR ${eur.toLocaleString('en-IE')} (${MODE}): ${rangeOk ? 'the price is accepted' : 'the price is refused by the current range'}${rangeOk ? (expectOk ? ', and the quote goes to the artist with 15% commission on the artwork only' : ', and the linked-purchase safeguard stops it at the artist/issue step') : ''}`,
    c.s === 200 && (rangeOk ? u.s === 200 : (u.s === 400 || u.s === 409) && /between EUR 1.00 and EUR 9999.99/.test(u.j.error))
    && (!rangeOk || !expectOk || (s2.s === 200 && o.commission_cents === eur * 100 * 15 / 100)), { c: c.s, u: u && [u.s, u.j && u.j.error], s2: s2 && [s2.s, s2.j && s2.j.error], o });
}
// the payment limit itself: Stripe's largest single card payment
const { amounts, STRIPE_MAX_AMOUNT_CENTS } = await import(HERE + FIX + 'src/checkout-rules.js');
let big = null; try { amounts({ artwork_cents: STRIPE_MAX_AMOUNT_CENTS, delivery_cents: 1000, commission_bp: 1500, max_artwork_cents: STRIPE_MAX_AMOUNT_CENTS }); } catch (e) { big = e.message; }
check('R8 even with an open range, a total above Stripe’s largest single payment (EUR 999,999.99) is refused', /largest single card payment/.test(big || ''), big);

console.log(`\nPRICE RANGE (${MODE}) · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
process.exitCode = results.every(Boolean) ? 0 : 1;
} finally {
  if (S) await S.mf.dispose();
  rmSync(HERE + FIX, { recursive: true, force: true });
}
