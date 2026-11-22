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

const FIX = 'test/.basket-fixture/';
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
console.log('PROVE · multi-artist basket (direct charge per artwork, authorise all before capture)');
const ORIGIN = 'https://checkout.local';
const ENVV = { CHECKOUT_MESSAGE_RETRY_MINUTES: '0', CHECKOUT_PILOT_ENABLED: 'true', BASKET_ENABLED: 'true', BASKET_COMMISSION_FREE: 'with_processing_consent', STRIPE_SECRET_KEY: 'sk_test_mockkey123', STRIPE_BASKET_KEY: 'rk_test_basketkey456',
  STRIPE_PUBLISHABLE_KEY: 'pk_test_mockpublishable', STRIPE_WEBHOOK_SECRET: WHSEC, STRIPE_WEBHOOK_SECRET_PLATFORM: WHSEC_P, STRIPE_API_BASE: 'https://stripe.mock', CHECKOUT_ORIGIN: ORIGIN, GALLERY_ORIGIN: 'https://plotnua.ie' };
S = await start({ port: 8873, env: ENVV, script: FIX + 'src/index.js', checkout: { script: FIX + 'src/checkout-public.js', env: ENVV }, outbound: stripe });
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

console.log('— artist: basket opt-in and standing delivery offers');
let r = await call('GET', '/api/checkout/basket', GAL);
check('A1 the artist sees the basket addendum (separate from the single-artwork addendum) and is not enrolled by default', r.j.addendum && r.j.addendum.doc_id === 'PA-BAA-TEST-01' && !r.j.membership.opted_in, r.j);
r = await call('POST', '/api/checkout/basket/opt-in', GAL, { accept: true, doc_id: 'PA-BAA-TEST-01', html_sha256: 'b'.repeat(64) });
check('A2 a different text fingerprint is refused', r.s === 400);
for (const e of [GAL, FND]) r = await call('POST', '/api/checkout/basket/opt-in', e, { accept: true, doc_id: BAA.doc_id, html_sha256: BAA.html_sha256 });
check('A3 artists opt in to baskets themselves (append-only record with the statement and fingerprint)', r.s === 200 && (await q("SELECT * FROM basket_artist_events WHERE kind='opted_in'")).length === 2
  && !!(await db.prepare("UPDATE basket_artist_events SET kind='left'").run().catch(e => e)).message);
const DELIVERY = { dispatch_days: 5, delivery_days: 10, collection_county: 'Dublin', unpacked_cm: '60 × 50 × 3', packed_cm: '75 × 65 × 12', weight_kg: 6, medium: 'Oil on board', framing: 'Framed, oak', glazing: 'None',
  condition: 'Excellent', access_notes: null, organiser: 'artist', packer: 'artist', transport_booker: 'artist', transport_contracting_party: 'artist', transport_payer: 'artist',
  transporter_name: 'Synthetic Art Couriers', installation: 'not_applicable', import_costs: 'not_applicable', cover_type: 'transit_insurance', cover_provider: 'Synthetic Underwriting (SIMULATED)', covered_value_cents: 150000,
  insured_party: 'transporter', cover_confirmation_ref: 'SIM-COVER-0001', cover_confirmed_by: 'Synthetic Underwriting', cover_confirmed_on: '2026-11-16', valuation_basis: 'Sale price', excess_cents: 0, exclusions: null,
  cover_period: 'Collection to signed delivery', claims_contact: 'claims@example.test', delivery_window: '5–8 working days', tracking: 'Tracked, signature on delivery', signed_receipt: true, condition_photos: true,
  return_method: 'Same courier, insured', return_address: '1 Studio Lane, Dublin 8', return_cost_cents: 6000, return_cost_basis: 'estimated_maximum', return_arranged_by: 'buyer',
  shipment_confirmation_ref: 'SAC-RATE-2026', shipment_confirmed_by: 'Synthetic Art Couriers', shipment_confirmed_on: '2026-11-16' };
r = await call('PUT', '/api/checkout/basket/offers/wagal1', GAL, { delivery_cents: 4500, delivery: DELIVERY });
check('A4 a delivery offer needs the artist’s explicit confirmation', r.s === 400);
r = await call('PUT', '/api/checkout/basket/offers/wagal1', GAL, { confirm: true, delivery_cents: 4500, delivery: { ...DELIVERY, covered_value_cents: 50000 } });
check('A5 transit insurance must cover at least the artwork price (pilot rule reused)', r.s === 409 && /cover at least/.test(r.j.error), r.j);
r = await call('PUT', '/api/checkout/basket/offers/wafnd1', GAL, { confirm: true, delivery_cents: 4500, delivery: DELIVERY });
check('A6 an artist can never set an offer on another artist’s work', r.s === 404);
for (const [e, w, c] of [[GAL, 'wagal1', 4500], [GAL, 'wagal2', 4500], [GAL, 'wagal3', 4500], [FND, 'wafnd1', 3000], [FND, 'wafnd2', 3000], [FND, 'wafnd3', 3000]]) r = await call('PUT', `/api/checkout/basket/offers/${w}`, e, { confirm: true, delivery_cents: c, delivery: DELIVERY });
const approvedFirst = await approveOffers();
check('A7 standing delivery offers recorded per artwork, approved by the artist (destination completed per order)', r.s === 200 && (await q('SELECT * FROM artwork_delivery_offers')).length === 6
  && JSON.parse((await one("SELECT delivery FROM artwork_delivery_offers WHERE artwork_id='wagal1'")).delivery).destination.includes('Republic of Ireland'));
// seller information shown BEFORE payment needs the artist's own confirmation (bound to that information)
r = await call('GET', '/api/admin/checkout/baskets/eligibility?ids=wagal1', FOUNDER);
check('D1 without the artist’s confirmation that their seller information may be shown before payment, the work is not offered', !r.j.items[0].ok && /seller information may be shown/.test(r.j.items[0].why), r.j.items);
let BV = (await call('GET', '/api/checkout/basket', GAL)).j;
check('D2 the artist sees exactly the seller details buyers will see (no VAT line when not registered) and the statement', BV.seller_info.shown.address === '1 Studio Lane, Dublin 8, Ireland' && !('vat_number' in BV.seller_info.shown) && /address at which I am established/.test(BV.disclosure_statement), BV.seller_info);
r = await call('POST', '/api/checkout/basket/seller-disclosure', GAL, { accept: true, statement: BV.disclosure_statement, subject_sha256: 'c'.repeat(64) });
check('D3 a confirmation of different seller information is refused', r.s === 400);
for (const e of [GAL, FND]) { const v = (await call('GET', '/api/checkout/basket', e)).j; r = await call('POST', '/api/checkout/basket/seller-disclosure', e, { accept: true, statement: v.disclosure_statement, subject_sha256: v.seller_info.subject_sha256 }); }
const sd = await one("SELECT * FROM basket_consents WHERE artist_id = 'agal' AND topic = 'seller_disclosure'");
check('D4 the confirmation is recorded: artist, account, statement and its fingerprint, the information fingerprint, Stripe mode, time; append-only',
  r.s === 200 && sd && sd.kind === 'given' && sd.account_email === GAL && sd.statement_sha256.length === 64 && sd.subject_sha256 === BV.seller_info.subject_sha256 && sd.livemode === 0
  && !!(await db.prepare("UPDATE basket_consents SET kind = 'withdrawn'").run().catch(e => e)).message, sd);
await call('PUT', '/api/checkout/seller-profile', GAL, { ...SELLER('Gale Gallery'), phone: '+353 1 555 0199' });
r = await call('GET', '/api/admin/checkout/baskets/eligibility?ids=wagal1', FOUNDER);
check('D5 changing the seller information withdraws the work until the artist confirms again', !r.j.items[0].ok && /changed since/.test(r.j.items[0].why), r.j.items);
await call('PUT', '/api/checkout/seller-profile', GAL, SELLER('Gale Gallery'));
r = await call('GET', '/api/admin/checkout/baskets/eligibility?ids=wagal1,wafnd1,wagal4,wanob1', FOUNDER);
const el0 = Object.fromEntries(r.j.items.map(i => [i.id, i]));
check('A8 founder eligibility view: Gallery Artist work ready; Founding work refused without the separate processing consent (fee Model B); price-on-request and non-basket artists refused',
  el0.wagal1.ok && el0.wagal1.commission_basis === 'gallery_artist_agreement' && !el0.wafnd1.ok && /no valid processing-fee consent/.test(el0.wafnd1.why) && /price on request/.test(el0.wagal4.why) && /not ready/.test(el0.wanob1.why), r.j.items);
const PSTAT = (await call('GET', '/api/checkout', FND)).j.processing_statement;
r = await call('POST', '/api/checkout/processing-consent', FND, { accept: true, statement: PSTAT });
r = await call('GET', '/api/admin/checkout/baskets/eligibility?ids=wafnd1', FOUNDER);
const BT = await import(HERE + 'src/basket-terms.js');
check('C0 founder decision applied: in LIVE mode commission-free works are offered only with the separate processing consent (TEST default stays direct payment)', BT.BASKET_DECISIONS.commission_free_lines_live === 'with_processing_consent' && BT.BASKET_DECISIONS.commission_free_lines_test_default === 'direct_payment_only');
check('C1 the older single-quote pilot consent does not count for the basket (no document version)', !r.j.items[0].ok && /processing-fee consent/.test(r.j.items[0].why), r.j.items);
const FV = (await call('GET', '/api/checkout/basket', FND)).j, BST = FV.processing_statement;
check('C2 the Founding Artist sees the consent: 0% commission, actual Stripe fees, refunds and disputes, withdrawal, no effect on gallery or enquiries',
  FV.founding && /0% commission/.test(BST) && /agreed commission-free period/.test(BST) && /actual card processing fee/.test(BST) && /refund a buyer, Stripe does not return/.test(BST) && /dispute fees/.test(BST)
  && /withdraw this consent at any time/.test(BST) && /does not affect my gallery listing, enquiries, direct sales/.test(BST) && BST.includes(BAA.doc_id), BST);
r = await call('POST', '/api/checkout/basket/processing-consent', FND, { accept: true, statement: BST.replace('0%', '5%') });
check('C3 a consent to any other wording is refused', r.s === 400);
r = await call('POST', '/api/checkout/basket/processing-consent', GAL, { accept: false, statement: BST });
check('C4 consent needs the explicit tick', r.s === 400);
r = await call('POST', '/api/checkout/basket/processing-consent', FND, { accept: true, statement: BST });
const pc = await one("SELECT * FROM basket_consents WHERE artist_id = 'afnd' AND topic = 'processing_fees'");
check('C5 the consent is recorded: artist, account, accepted document version and fingerprint, statement fingerprint, Stripe mode, time',
  r.s === 200 && pc.kind === 'given' && pc.doc_id === BAA.doc_id && pc.doc_sha256 === BAA.html_sha256 && pc.account_email === FND && pc.statement === BST && pc.livemode === 0 && r.j.membership.processing_consent.valid, pc);
check('C6 the database refuses a consent naming a document that is not an installed basket addendum', !!(await db.prepare("INSERT INTO basket_consents (id, artist_id, topic, kind, doc_id, doc_sha256, statement, statement_sha256, account_email, livemode, at) VALUES ('bcx','afnd','processing_fees','given','PA-BBT-TEST-01',?, 'x', ?, 'x', 0, ?)").bind('d'.repeat(64), 'e'.repeat(64), new Date().toISOString()).run().catch(e => e)).message);
r = await call('POST', '/api/checkout/basket/processing-consent/withdraw', FND, {});
const r2 = await call('GET', '/api/admin/checkout/baskets/eligibility?ids=wafnd1', FOUNDER);
check('C7 withdrawing the consent takes commission-free works out of the basket at once (recorded as a new row)', r.s === 200 && !r.j.membership.processing_consent.valid && !r2.j.items[0].ok
  && (await q("SELECT kind FROM basket_consents WHERE artist_id = 'afnd' AND topic = 'processing_fees' ORDER BY at, rowid")).map(x => x.kind).join() === 'given,withdrawn');
r = await call('POST', '/api/checkout/basket/processing-consent', FND, { accept: true, statement: BST });
r = await call('GET', '/api/admin/checkout/baskets/artists', FOUNDER);
const ra = Object.fromEntries(r.j.artists.map(a => [a.id, a]));
check('C8 founder readiness view: consent, document version, seller-information confirmation and what is missing, per artist',
  ra.afnd.processing_consent.valid && ra.afnd.processing_consent.doc_id === BAA.doc_id && ra.afnd.seller_disclosure.valid && !ra.afnd.missing.length && ra.agal.processing_consent && !ra.agal.missing.length
  && ra.anob.missing.includes('basket addendum') && /0% commission/.test(ra.afnd.commission_free_works), r.j.artists);
check('C8a founder readiness: each artist’s available artworks and how many can be bought online now (a not-ready artist: none, “artist not ready”)',
  ra.anob.online && ra.anob.online.purchasable === 0 && (ra.anob.online.available === 0 || ra.anob.online.not_purchasable['artist not ready'] === ra.anob.online.available)
  && ra.agal.online.purchasable + Object.values(ra.agal.online.not_purchasable).reduce((n, x) => n + x, 0) === ra.agal.online.available && ra.agal.online.purchasable > 0, Object.values(ra).map(a => [a.id, a.online]));
r = await call('GET', '/api/admin/checkout/baskets/eligibility?ids=wafnd1', FOUNDER);
check('A9 with the Founding Artist’s own processing consent (and the TEST policy switch), their work is offered at 0% commission (Founding 25 entitlement kept)', r.j.items[0].ok && r.j.items[0].commission_basis === 'founding_enquiry', r.j.items);

console.log('— buyer: the basket page and live preview');
r = await pub('GET', '/basket');
check('B1 the basket page is served with a strict policy (nonce scripts only, no third-party scripts, no framing)', r.s === 200 && /<h1 class="bh">Your Basket<\/h1>/.test(r.t) && !/Original works|one secure checkout|Summary<\/h2>|secure payment page/.test(r.t) && (r.t.match(/<h1/g) || []).length === 1 && />Buy now<\/button>/.test(r.t) && /select <strong>Save<\/strong> there to complete your purchase/.test(r.t) && /script-src 'nonce-[0-9a-f]{32}'(;| )/.test(r.h.get('Content-Security-Policy'))
  && !/js\.stripe\.com/.test(r.h.get('Content-Security-Policy')) && r.h.get('X-Frame-Options') === 'DENY' && /Test mode/.test(r.t), r.h.get('Content-Security-Policy'));
const bp = r.t;
const BP = await import(HERE + FIX + 'src/basket-public.js');
const live = await BP.page({ ENVIRONMENT: 'production', CHECKOUT_LIVE: 'true', STRIPE_SECRET_KEY: 'sk_live_notused', STAGING_GALLERY: 'true', CHECKOUT_ORIGIN: 'https://x' }, 'Your basket', '<h1>Your Basket</h1>').text();
const stagingNote = await BP.page({ ENVIRONMENT: 'test', STRIPE_SECRET_KEY: 'sk_test_x', STAGING_GALLERY: 'true', CHECKOUT_ORIGIN: 'https://x' }, 'Your basket', '<h1>Your Basket</h1>').text();
check('B1c the TEST/staging notice appears only in Stripe TEST mode, never in live production', !/Test mode|Private staging|staging/i.test(live) && /Private staging/.test(stagingNote));
check('B1b the basket page carries no payment-arrangement detail (separate payments, paid directly, Stripe processing, number of transactions)', !/separate (card )?payments?|paid directly|directly to the artist|each artist(’|')s payment|Stripe emails|transactions?\\b/i.test(bp.replace(/<footer>[\s\S]*<\/footer>/, '').replace(/<p class="note test">[\s\S]*?<\/p>/, '')) && /Each artwork is sold by its artist/.test(bp));
check('B1a the page carries PlotArt’s identity (Instrument Serif, Hanken Grotesk, anthracite) and is responsive', /Instrument\+Serif/.test(r.t) && /Hanken\+Grotesk/.test(r.t) && /#27282A/.test(r.t) && /@media \(max-width:560px\)/.test(r.t) && /name="viewport"/.test(r.t));
r = await pub('GET', '/api/basket/items?ids=wagal1,wafnd1,wagal4,wanob1,nonexistent');
const it = Object.fromEntries(r.j.items.map(i => [i.id, i]));
check('B2 live preview: price, seller and delivery for eligible works, from the records', it.wagal1.ok && it.wagal1.price_cents === 120000 && it.wagal1.delivery_cents === 4500 && it.wagal1.artist === 'Gale Gallery' && /5–8 working days/.test(it.wagal1.delivery.window)
  && it.wafnd1.ok && it.wafnd1.price_cents === 45000 && r.j.open === true && r.j.terms.doc_id === 'PA-BBT-TEST-01', r.j);
check('B2a before payment, each work carries its seller’s legally required details (VAT only if registered) and its return arrangements',
  it.wagal1.seller_info.legal_name === 'Gale Gallery' && it.wagal1.seller_info.address && it.wagal1.seller_info.email && it.wagal1.seller_info.phone && it.wagal1.seller_info.trader === true && !('vat_number' in it.wagal1.seller_info)
  && it.wagal1.returns.method && it.wagal1.returns.address && it.wagal1.returns.arranged_by === 'you' && !('seller_info' in it.wagal4), it.wagal1);
check('B3 ineligible works are refused with a buyer-friendly reason and never priced (price on request; artist not in baskets; unknown)', !it.wagal4.ok && /enquire/i.test(it.wagal4.reason) && !it.wanob1.ok && !it.nonexistent.ok
  && !('price_cents' in it.wagal4) && !/Model B|commission|opted/i.test(JSON.stringify(r.j.items.filter(i => !i.ok))), r.j.items);
check('B4 the gallery (plotnua.ie) may read eligibility cross-origin; nothing else is exposed', r.h.get('Access-Control-Allow-Origin') === 'https://plotnua.ie');

console.log('— buyer: open a basket (two artists, one card entry)');
const BUYER = { name: 'Bríd Buyer', email: 'brid@example.test', address_line1: '7 Harbour Road', address_line2: '', town: 'Kinsale', county: 'Cork', eircode: 'P17 XY12', phone: '+353 21 555 0199', island: 'no' };
const basketReq = (artworks, extra = {}) => ({ artworks, accept_terms: 'PA-BBT-TEST-01', ...BUYER, ...extra });
const SEEDB = [{ id: 'wagal1', img: 'https://plotnua.ie/plotart/artists/gale/img/g1.png' }, { id: 'wafnd1', img: 'https://plotnua.ie/plotart/artists/fia/img/g2.png' }, { id: 'wagal2', img: 'https://plotnua.ie/plotart/artists/gale/img/g3.png' }];
await shot('1-basket-desktop', '/basket', { basket: SEEDB });
await shot('2-basket-mobile', '/basket', { basket: SEEDB, width: 390, height: 844 });
r = await pub('POST', '/basket/checkout', { json: basketReq(['wagal1', 'wafnd1']), origin: 'https://evil.example' });
check('B5 another origin cannot open a basket', r.s === 403);
r = await pub('POST', '/basket/checkout', { json: basketReq(['wagal1', 'wafnd1'], { accept_terms: '' }) });
check('B6 the purchase terms must be accepted', r.s === 400 && /terms/.test(r.j.error));
r = await pub('POST', '/basket/checkout', { json: basketReq(['wagal1', 'wafnd1'], { county: 'Antrim' }) });
check('B7 delivery is to the Republic of Ireland only (county checked)', r.s === 400 && /Republic of Ireland/.test(r.j.error));
r = await pub('POST', '/basket/checkout', { json: basketReq(['wagal1', 'wafnd1'], { expected_total_cents: 1 }) });
check('B8 a total that differs from the server’s price is refused (the browser never sets an amount)', r.s === 409 && /changed/.test(r.j.error) && !(await q('SELECT * FROM checkout_baskets')).length);
r = await pub('POST', '/basket/checkout', { json: basketReq(['wagal1', 'wafnd1', 'wagal4']) });
check('B9 a basket with an ineligible work is refused as a whole, naming the work', r.s === 409 && r.j.artwork === 'wagal4' && !(await q('SELECT * FROM checkout_orders')).length);
const callsBefore = M.calls.length;
r = await pub('POST', '/basket/checkout', { json: basketReq(['wagal1', 'wafnd1'], { expected_total_cents: 120000 + 4500 + 45000 + 3000 }) });
const B1 = await one('SELECT * FROM checkout_baskets ORDER BY created_at DESC LIMIT 1');
const sess1 = Object.values(M.sessions).at(-1);
const L1 = await q('SELECT * FROM basket_lines WHERE basket_id = ? ORDER BY line_no', B1.id);
const O1 = await q('SELECT o.* FROM checkout_orders o JOIN basket_lines l ON l.order_id = o.id WHERE l.basket_id = ? ORDER BY l.line_no', B1.id);
check('B10 the buyer is sent to Stripe’s hosted card page (setup mode, on PlotArt’s own account, card only, no amount on it)', r.s === 200 && r.j.url === sess1.url && sess1._f.mode === 'setup'
  && !M.calls.slice(callsBefore).find(c => c.path === '/v1/checkout/sessions').acct && sess1._f['allowed_payment_method_types[0]'] === 'card' && !('amount' in sess1._f) && sess1._f.customer, r.j);
check('B10a the card page’s confirm button carries the order wording with the basket total (obligation to pay)', /^Selecting Save completes your purchase: you order the artworks in your basket and agree to pay €[0-9,]+\.[0-9]{2} in total\. Your card is saved only to take these payments\.$/.test(sess1._f['custom_text[submit][message]'] || '')
  && sess1._f['custom_text[submit][message]'].includes((B1.total_cents / 100).toLocaleString('en-IE', { minimumFractionDigits: 2 })), sess1._f['custom_text[submit][message]']);
check('B11 one ordinary order per artwork, priced from the records: 15% on the Gallery Artist’s work, 0% (Founding 25) on the Founding Artist’s', O1.length === 2
  && O1[0].artwork_cents === 120000 && O1[0].delivery_cents === 4500 && O1[0].commission_bp === 1500 && O1[0].commission_cents === 18000 && O1[0].commission_basis === 'gallery_artist_agreement'
  && O1[1].artwork_cents === 45000 && O1[1].commission_cents === 0 && O1[1].commission_basis === 'founding_enquiry' && O1.every(o => o.status === 'checkout_open' && o.enquiry_ref === B1.reference), O1);
check('B12 commission is never charged on delivery; the line amount is artwork + delivery and the fee is the commission only', L1[0].amount_cents === 124500 && L1[0].fee_cents === 18000 && L1[1].amount_cents === 48000 && L1[1].fee_cents === 0, L1);
check('B13 every artwork is reserved in the same transaction; each order keeps the seller, delivery to the buyer’s address and a fingerprinted snapshot', (await q('SELECT * FROM artwork_reservations WHERE order_id IN (?,?)', O1[0].id, O1[1].id)).length === 2
  && JSON.parse(O1[0].delivery).destination.includes('Kinsale') && JSON.parse(O1[0].seller).name === 'Gale Gallery' && (await q('SELECT * FROM quote_snapshots WHERE order_id IN (?,?)', O1[0].id, O1[1].id)).length === 2);
check('B14 the buyer link is stored only as a hash; the basket and its history are recorded', B1.buyer_token_hash.length === 64 && B1.status === 'open' && (await q('SELECT * FROM basket_events WHERE basket_id = ?', B1.id)).length >= 2);
r = await pub('POST', '/basket/checkout', { json: basketReq(['wagal2', 'wafnd1'], { email: 'other@example.test' }) });
check('B15 a second buyer cannot buy a work that is in someone’s open basket (nothing of theirs is created)', r.s === 409 && /someone else/i.test(r.j.error) && (await q("SELECT * FROM checkout_orders WHERE buyer_email = 'other@example.test'")).length === 0, r.j);
r = await pub('GET', '/api/basket/items?ids=wafnd1');
check('B16 the preview shows a reserved work as being bought by someone else', r.j.items[0].ok === false && /someone else/i.test(r.j.items[0].reason));

console.log('— paying: authorise every artist’s payment, then capture');
const token1 = new URL(sess1._f.success_url).pathname.split('/')[2];
r = await pub('GET', `/b/${token1}`);
check('P1 before the card is entered the status page says so; a return from Stripe is never proof of payment', r.s === 200 && /Waiting for your card details/.test(r.t));
await shot('3-waiting', `/b/${token1}`);
enterCard(sess1.id, {});
const cBefore = M.calls.length;
r = await hook(evt('checkout.session.completed', M.sessions[sess1.id]), 'whsec_test_wrong_' + 'z'.repeat(20));
check('P1a an event signed with an unknown secret is refused before anything is read', r.s === 400 && (await one('SELECT status FROM checkout_baskets WHERE id = ?', B1.id)).status === 'open');
r = await hook(evt('checkout.session.completed', M.sessions[sess1.id]), WHSEC_P);
const B1p = await one('SELECT * FROM checkout_baskets WHERE id = ?', B1.id);
const newCalls = M.calls.slice(cBefore);
const clones = newCalls.filter(c => c.path === '/v1/payment_methods'), auths = newCalls.filter(c => c.path === '/v1/payment_intents' && c.method === 'POST'), caps = newCalls.filter(c => /\/capture$/.test(c.path));
check('P2 an event signed by PlotArt’s own-account endpoint (its own secret) completes the card page; the coordinator runs', r.s === 200 && B1p.status === 'paid', { r, status: B1p.status, res: B1p.resolution });
check('P3 the saved card is cloned to EACH artist’s own account (no second card entry)', clones.length === 2 && clones[0].acct === ACC.agal && clones[1].acct === ACC.afnd && clones.every(c => c.f.customer === B1p.platform_customer));
check('P4 each artist’s payment is a DIRECT charge on their own account, authorised first (manual capture, off-session, card only)', auths.length === 2 && auths.every(c => c.f.capture_method === 'manual' && c.f.off_session === 'true' && c.f.confirm === 'true' && c.f['allowed_payment_method_types[0]'] === 'card')
  && auths[0].acct === ACC.agal && auths[1].acct === ACC.afnd);
check('P5 PlotArt’s commission is the application fee: EUR 180 on the Gallery Artist’s charge, none on the Founding Artist’s', auths[0].f.application_fee_amount === '18000' && !('application_fee_amount' in auths[1].f) && auths[0].f.amount === '124500' && auths[1].f.amount === '48000');
const firstCap = newCalls.findIndex(c => /\/capture$/.test(c.path)), lastAuth = newCalls.map(c => c.path === '/v1/payment_intents' && c.method === 'POST').lastIndexOf(true);
check('P6 nothing is captured until EVERY artist’s payment is authorised', caps.length === 2 && firstCap > lastAuth);
check('P7 every Stripe call that moves money carries an idempotency key derived from the basket and the order', [...clones, ...auths, ...caps].every(c => c.idem && c.idem.includes(B1.id)));
const O1p = await q('SELECT o.* FROM checkout_orders o JOIN basket_lines l ON l.order_id = o.id WHERE l.basket_id = ? ORDER BY l.line_no', B1.id);
check('P8 each captured charge completes its own order through the single-artwork path: paid, sold, reservation released', O1p.every(o => o.status === 'paid' && o.payment_status === 'paid' && o.payment_intent)
  && (await q('SELECT * FROM artwork_sales WHERE order_id IN (?,?)', O1[0].id, O1[1].id)).length === 2 && !(await q('SELECT * FROM artwork_reservations WHERE order_id IN (?,?)', O1[0].id, O1[1].id)).length
  && (await one("SELECT availability FROM artworks WHERE id='wagal1'")).availability === 'sold', O1p.map(o => [o.status, o.needs_resolution]));
const led = await q('SELECT order_id, kind, amount_cents FROM order_ledger WHERE order_id IN (?,?) ORDER BY order_id, kind', O1[0].id, O1[1].id);
const L = (o, k) => (led.find(x => x.order_id === o && x.kind === k) || {}).amount_cents;
check('P9 the ledger books each payment exactly: charge, commission (15% of the artwork only) and the artist’s allocations', L(O1[0].id, 'charge') === 124500 && L(O1[0].id, 'commission') === 18000 && L(O1[0].id, 'artist_artwork') === 102000 && L(O1[0].id, 'delivery_allocation') === 4500
  && L(O1[1].id, 'charge') === 48000 && L(O1[1].id, 'commission') === undefined && L(O1[1].id, 'artist_artwork') === 45000, led);
check('P10 the buyer gets one purchase confirmation per artwork, naming the artist as seller and the basket', (await q("SELECT * FROM order_messages WHERE kind='buyer_confirmation' AND order_id IN (?,?)", O1[0].id, O1[1].id)).length === 2
  && /Part of basket PA-B-/.test((await one("SELECT body FROM order_messages WHERE kind='buyer_confirmation' AND order_id = ?", O1[1].id)).body) && /TEST ONLY · Basket purchase terms/.test((await one("SELECT body FROM order_messages WHERE kind='buyer_confirmation' AND order_id = ?", O1[1].id)).body));
check('P11 the buyer’s saved card is not kept: the platform Customer is deleted once the basket ends', M.customers[B1p.platform_customer].deleted === true && !!B1p.card_released_at);
r = await pub('GET', `/b/${token1}`);
await shot('4-paid', `/b/${token1}`, { width: 1280 }); await shot('4b-paid-mobile', `/b/${token1}`, { width: 390, height: 844 });
check('P12 the confirmation: “Thank you for your purchase”, “Order confirmed”, the agreed message; titles, artists (once each), prices, delivery and total; one simple confirmation link per artwork; no payment-arrangement detail',
  /Thank you for your purchase/.test(r.t) && /Order confirmed/.test(r.t) && /Your order has been successfully placed\./.test(r.t) && /Your artwork will be prepared for delivery to your nominated address\. You’ll receive confirmation of your purchase, and we’ll be in touch with any delivery updates\./.test(r.t)
  && (r.t.match(/View confirmation/g) || []).length === 2 && /by Gale Gallery/.test(r.t) && !/Gale Gallery \(/.test(r.t) && /€1,245\.00/.test(r.t) && /€1,725\.00/.test(r.t) && /delivered in 5–8 working days/.test(r.t)
  && !/separate (card )?payments?|paid directly|directly to the artist|each artist(’|')s payment|Stripe emails|transactions?\\b/i.test(r.t.replace(/<footer>[\s\S]*<\/footer>/, '')), r.t.slice(0, 400));
r = await pub('GET', `/b/${token1}/confirmation/${O1p[0].reference}`);
check('P13 the confirmation for one artwork is reachable only through this basket’s link', r.s === 200 && /PURCHASE CONFIRMATION/.test(r.t) && (await pub('GET', `/b/${'z'.repeat(48)}/confirmation/${O1p[0].reference}`)).s === 404);
const cAfter = M.calls.length;
r = await hook(evt('checkout.session.completed', M.sessions[sess1.id]));
await hook(evt('payment_intent.amount_capturable_updated', M.pis[O1p[0].payment_intent] && { id: O1p[0].payment_intent, object: 'payment_intent', metadata: { plotart_basket: B1.id, plotart_order: O1[0].id } }, ACC.agal));
check('P14 repeated or late events change nothing: no second authorisation or capture', M.calls.slice(cAfter).filter(c => c.method === 'POST').length === 0 && (await one('SELECT status FROM checkout_baskets WHERE id = ?', B1.id)).status === 'paid');
r = await hook(evt('payment_intent.amount_capturable_updated', { id: O1p[0].payment_intent, object: 'payment_intent', metadata: { plotart_basket: B1.id, plotart_order: O1[0].id } }, ACC.afnd));
check('P15 an event naming the wrong artist account is refused (not applied)', r.s === 500);

console.log('— one artist’s payment is declined: nothing is bought');
r = await pub('POST', '/basket/checkout', { json: basketReq(['wagal2', 'wafnd2'], { email: 'dee@example.test' }) });
const B2 = await one("SELECT * FROM checkout_baskets WHERE buyer_email = 'dee@example.test'"), s2 = Object.values(M.sessions).at(-1);
enterCard(s2.id, { [ACC.afnd]: 'decline' });
await hook(evt('checkout.session.completed', M.sessions[s2.id]));
const B2p = await one('SELECT * FROM checkout_baskets WHERE id = ?', B2.id), L2 = await q('SELECT * FROM basket_lines WHERE basket_id = ? ORDER BY line_no', B2.id);
const O2 = await q('SELECT o.* FROM checkout_orders o JOIN basket_lines l ON l.order_id = o.id WHERE l.basket_id = ? ORDER BY l.line_no', B2.id);
check('D1 the second artist’s card decline fails the basket', B2p.status === 'failed' && L2[1].state === 'declined' && L2[1].decline_code === 'generic_decline', { B2p, L2 });
check('D2 the first artist’s authorisation is CANCELLED: nothing is captured, nothing taken', L2[0].state === 'cancelled' && M.pis[L2[0].payment_intent].status === 'canceled' && !M.calls.some(c => c.path === `/v1/payment_intents/${L2[0].payment_intent}/capture`));
check('D3 both orders end unpaid, the artworks are released and stay available, the card is not kept', O2.every(o => o.status === 'cancelled' && o.payment_status !== 'paid') && !(await q('SELECT * FROM artwork_reservations WHERE order_id IN (?,?)', O2[0].id, O2[1].id)).length
  && !(await q('SELECT * FROM artwork_sales WHERE order_id IN (?,?)', O2[0].id, O2[1].id)).length && (await one("SELECT availability FROM artworks WHERE id='wagal2'")).availability === 'available' && M.customers[B2p.platform_customer].deleted);
r = await pub('GET', `/b/${new URL(s2._f.success_url).pathname.split('/')[2]}`);
await shot('6-declined', `/b/${new URL(s2._f.success_url).pathname.split('/')[2]}`);
check('D4 the buyer is told plainly: payment not completed, card declined, nothing charged (no artist or payment detail)', /Payment not completed/.test(r.t) && /Your card was declined\./.test(r.t) && /Nothing was charged/.test(r.t) && !/Fia Founding/.test(r.t.split('<section>')[0]), r.t.slice(0, 600));
check('D5 no ledger entry exists for a failed basket', !(await q('SELECT * FROM order_ledger WHERE order_id IN (?,?)', O2[0].id, O2[1].id)).length);

console.log('— extra bank authentication for one artist’s payment');
r = await pub('POST', '/basket/checkout', { json: basketReq(['wagal2', 'wafnd2'], { email: 'ena@example.test' }) });
const B3 = await one("SELECT * FROM checkout_baskets WHERE buyer_email = 'ena@example.test'"), s3 = Object.values(M.sessions).at(-1), token3 = new URL(s3._f.success_url).pathname.split('/')[2];
enterCard(s3.id, { [ACC.afnd]: 'auth' });
r = await pub('GET', `/b/${token3}/return`);
let B3p = await one('SELECT * FROM checkout_baskets WHERE id = ?', B3.id); const L3 = await q('SELECT * FROM basket_lines WHERE basket_id = ? ORDER BY line_no', B3.id);
check('X1 the buyer’s return from Stripe runs the coordinator (no need to wait for the webhook)', r.s === 303 && r.loc === `/b/${token3}`);
check('X2 a bank asking for authentication pauses the basket: the other artist stays authorised, nothing is captured', B3p.status === 'action_required' && L3[0].state === 'authorised' && L3[1].state === 'action_required'
  && !M.calls.some(c => c.path.endsWith('/capture') && [L3[0].payment_intent, L3[1].payment_intent].some(p => c.path.includes(p))) && !!B3p.action_deadline);
r = await pub('GET', `/b/${token3}`);
const ref3 = (await one('SELECT reference FROM checkout_orders WHERE id = ?', L3[1].order_id)).reference;
await shot('5-bank-check', `/b/${token3}`);
check('X3 the status page asks the buyer to confirm their payment, with a deadline (no per-artist payment wording)', /Confirm your payment/.test(r.t) && /Confirm payment</.test(r.t) && /otherwise your order is cancelled and nothing is charged/.test(r.t) && !/separate (card )?payments?|paid directly|directly to the artist|each artist(’|')s payment|Stripe emails|transactions?\\b/i.test(r.t.replace(/<footer>[\s\S]*<\/footer>/, '')), r.t.slice(0, 500));
r = await pub('GET', `/b/${token3}/authenticate/${ref3}`);
check('X4 the confirmation page runs Stripe.js on THAT artist’s account with the payment’s own secret; only then is Stripe.js allowed', r.s === 200 && r.t.includes(`stripeAccount:"${ACC.afnd}"`) && r.t.includes('pk_test_mockpublishable') && r.t.includes(M.pis[L3[1].payment_intent].client_secret)
  && /script-src 'nonce-[0-9a-f]+' https:\/\/js\.stripe\.com/.test(r.h.get('Content-Security-Policy')), r.t.slice(0, 300));
M.pis[L3[1].payment_intent].status = 'requires_capture';   // the buyer completes their bank's check in the browser (Stripe.js)
r = await pub('POST', `/b/${token3}/continue`, { form: {} });
B3p = await one('SELECT * FROM checkout_baskets WHERE id = ?', B3.id);
check('X5 once confirmed, every payment is captured and the basket is paid', r.s === 303 && B3p.status === 'paid' && (await q("SELECT * FROM basket_lines WHERE basket_id = ? AND state = 'captured'", B3.id)).length === 2, B3p);

console.log('— authentication not completed in time: everything is cancelled');
r = await pub('POST', '/basket/checkout', { json: basketReq(['wagal3', 'wafnd3'], { email: 'fin@example.test' }) });
const B4 = await one("SELECT * FROM checkout_baskets WHERE buyer_email = 'fin@example.test'"), s4 = Object.values(M.sessions).at(-1);
enterCard(s4.id, { [ACC.afnd]: 'auth' });
await hook(evt('checkout.session.completed', M.sessions[s4.id]));
await db.prepare('UPDATE checkout_baskets SET action_deadline = ? WHERE id = ?').bind(ago(0.01), B4.id).run();
await CW.scheduled({ scheduledTime: Date.now(), cron: '*/5 * * * *' });
const B4p = await one('SELECT * FROM checkout_baskets WHERE id = ?', B4.id), L4 = await q('SELECT * FROM basket_lines WHERE basket_id = ? ORDER BY line_no', B4.id);
check('T1 the scheduled sweep cancels every authorisation when the deadline passes; nothing is bought', B4p.status === 'failed' && L4.every(l => l.state === 'cancelled') && L4.every(l => M.pis[l.payment_intent].status === 'canceled')
  && (await one("SELECT availability FROM artworks WHERE id='wagal3'")).availability === 'available', { B4p, L4 });

console.log('— the buyer never enters a card: the page expires');
await db.prepare("DELETE FROM artwork_reservations").run();
r = await pub('POST', '/basket/checkout', { json: basketReq(['wagal3'], { email: 'gus@example.test' }) });
const B5 = await one("SELECT * FROM checkout_baskets WHERE buyer_email = 'gus@example.test'"), s5 = Object.values(M.sessions).at(-1);
M.sessions[s5.id].status = 'expired';
await db.prepare('UPDATE checkout_baskets SET expires_at = ? WHERE id = ?').bind(ago(0.01), B5.id).run();
await CW.scheduled({ scheduledTime: Date.now(), cron: '*/5 * * * *' });
const B5p = await one('SELECT * FROM checkout_baskets WHERE id = ?', B5.id);
check('E1 an unused card page expires the basket, releases the artwork and charges nothing', B5p.status === 'expired' && !(await q('SELECT * FROM artwork_reservations WHERE artwork_id = ?', 'wagal3')).length
  && !Object.values(M.pis).some(p => p.metadata.plotart_basket === B5.id), B5p);

console.log('— a temporary Stripe error while authorising: retried safely');
r = await pub('POST', '/basket/checkout', { json: basketReq(['wagal3', 'wafnd3'], { email: 'hal@example.test' }) });
const B6 = await one("SELECT * FROM checkout_baskets WHERE buyer_email = 'hal@example.test'"), s6 = Object.values(M.sessions).at(-1);
enterCard(s6.id, {}); M.fail500 = 1;
await hook(evt('checkout.session.completed', M.sessions[s6.id]));
let B6p = await one('SELECT * FROM checkout_baskets WHERE id = ?', B6.id);
const st6 = B6p.status;
await db.prepare('UPDATE checkout_baskets SET updated_at = ? WHERE id = ?').bind(ago(0.01), B6.id).run();
await CW.scheduled({ scheduledTime: Date.now(), cron: '*/5 * * * *' });
B6p = await one('SELECT * FROM checkout_baskets WHERE id = ?', B6.id);
const pis6 = Object.values(M.pis).filter(p => p.metadata.plotart_basket === B6.id);
check('R1 a transient error leaves the basket authorising; the sweep resumes it and it completes', st6 === 'authorising' && B6p.status === 'paid', { st6, B6p });
check('R2 the retry made exactly one charge per artwork (same idempotency keys; never charged twice)', pis6.length === 2 && pis6.every(p => p.status === 'succeeded'));

console.log('— refunds and commission reversal on a basket order (existing order refund path)');
r = await call('POST', `/api/admin/checkout/orders/${O1[0].id}/refund`, FOUNDER, { artwork_cents: 120000, delivery_cents: 4500, reason: 'Buyer cancelled within 14 days' });
const rf = M.refunds.at(-1);
const ledR = await q("SELECT kind, amount_cents FROM order_ledger WHERE order_id = ? AND kind IN ('artwork_refund','delivery_refund','commission_refund')", O1[0].id);
check('F1 a basket order is refunded on its artist’s account through the existing refund action (one artist only)', r.s === 200 && rf && rf._acct === ACC.agal && rf.amount === 124500 && rf._f.refund_application_fee === 'false', { r: r.j, rf });
const owedF = await q("SELECT kind, cents FROM checkout_owed WHERE order_id = ?", O1[0].id);
const viaStripe = -(ledR.find(x => x.kind === 'commission_refund') || {}).amount_cents || 0, owedC = owedF.filter(x => x.kind === 'commission_shortfall').reduce((a, x) => a + x.cents, 0);
check('F2 PlotArt returns its exact commission on the refunded artwork (EUR 180 in total: through Stripe, plus any part already used to reimburse Stripe’s fee owed by bank transfer, fee Model B), and only on that order',
  viaStripe + owedC === 18000 && viaStripe > 0 && !(await q("SELECT * FROM order_ledger WHERE order_id = ? AND kind LIKE '%refund%'", O1[1].id)).length, { ledR, owedF });

console.log('— founder desk and switches');
r = await call('GET', '/api/admin/checkout/baskets', FOUNDER);
check('G1 the founder sees every basket with its status', r.s === 200 && r.j.baskets.length >= 6 && r.j.baskets.some(b => b.status === 'failed') && r.j.decisions.charge_granularity === 'per_artwork');
r = await call('GET', `/api/admin/checkout/baskets/${B2.id}`, FOUNDER);
check('G2 basket detail: lines, orders and the append-only history (no buyer token)', r.s === 200 && r.j.lines.length === 2 && r.j.events.length >= 3 && !('buyer_token_hash' in r.j.basket && r.j.basket.buyer_token_hash) && !!(await db.prepare('UPDATE basket_events SET action = 1').run().catch(e => e)).message);
r = await call('GET', '/api/admin/checkout/baskets', GAL);
check('G3 an artist cannot reach the founder’s basket desk', r.s === 403 || r.s === 401);
const FPI = JSON.parse(readFileSync(HERE + 'agreements/basket-issued/fingerprints.json', 'utf8')).documents;
const LB = await basketDoc('PA-BBT-2026-11', true), LA = await basketDoc('PA-BAA-2026-11', true);
check('G4 live mode: only the two ISSUED texts exist, fingerprints match the issued files, no TEST placeholder is live and no live text is offered in TEST mode',
  Object.keys(LIVE_BASKET_DOCS).sort().join() === 'PA-BAA-2026-11,PA-BBT-2026-11' && LB.html_sha256 === FPI['PA-BBT-2026-11'].html_sha256 && LA.html_sha256 === FPI['PA-BAA-2026-11'].html_sha256
  && (await basketDoc('PA-BBT-TEST-01', true)) === null && (await basketDoc('PA-BBT-2026-11', false)) === null && !/DRAFT|TEST ONLY/.test(LB.html + LA.html));
const esc = t => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const mig21 = readFileSync(HERE + 'migrations/0021_basket_terms_issue.sql', 'utf8');
check('G4a the issued addendum carries, word for word, the processing-fee consent and seller-information statements the Studio records; migration 0021 installs exactly the issued fingerprints',
  BT.PROCESSING_CONSENT_STATEMENT('PA-BAA-2026-11').split('\n').every(l => LA.html.includes(esc(l))) && LA.html.includes(esc(BT.SELLER_DISCLOSURE_STATEMENT))
  && mig21.includes(FPI['PA-BBT-2026-11'].html_sha256) && mig21.includes(FPI['PA-BAA-2026-11'].html_sha256) && (mig21.match(/\('PA-B/g) || []).length === 2);
check('G5 only TEST keys were presented to the provider', M.calls.every(c => ['Bearer sk_test_mockkey123', 'Bearer rk_test_basketkey456'].includes(c.auth)));
const basketPaths = c => (c.path === '/v1/customers' || /^\/v1\/customers\/cus_/.test(c.path) && c.method === 'DELETE' || c.path === '/v1/checkout/sessions' || c.path === '/v1/payment_methods'
  || (c.path === '/v1/payment_intents' && c.method === 'POST') || /\/(capture|cancel)$/.test(c.path));
check('G7 the basket’s own calls use the separate basket key; refunds, reads and everything else keep the main key',
  M.calls.filter(basketPaths).length > 10 && M.calls.filter(basketPaths).every(c => c.auth === 'Bearer rk_test_basketkey456')
  && M.calls.filter(c => c.path === '/v1/refunds' && c.method === 'POST').every(c => c.auth === 'Bearer sk_test_mockkey123') && M.calls.some(c => c.path === '/v1/refunds'));
const SS = await import(HERE + 'src/stripe.js');
const mism = await (async () => SS.createCustomer({ STRIPE_SECRET_KEY: 'sk_test_x1', STRIPE_BASKET_KEY: 'rk_live_x2', STRIPE_API_BASE: 'https://stripe.mock', ENVIRONMENT: 'local' }, { idem: 'x', email: 'a@b.c', name: 'x', basket: { id: 'b', reference: 'PA-B-x' } }))().then(() => 'called', e => e.code);
check('G8 a basket key of the other mode (live with test) is refused before any request', mism === 'not_configured', mism);
r = await pub('GET', `/b/${'q'.repeat(48)}`);
check('G6 an unknown basket link reveals nothing', r.s === 404 && !/PA-B-/.test(r.t));

console.log('— in a real browser: the artist’s and founder’s basket controls, and the buyer’s seller and returns information');
{
  const { createRequire } = await import('node:module');
  let pw = null; try { pw = createRequire(process.env.PLAYWRIGHT_FROM || '/tmp/claude-0/studio-tools/package.json')('playwright'); } catch { pw = null; }
  check('U0 a real browser is available for the screen checks', !!pw);
  if (pw) {
    BR = BR || await pw.chromium.launch();
    const UISHOT = process.env.BASKET_UI_SHOTS || null;
    // artist (Founding): consent, seller information and delivery offers on the Studio page
    const ac = await BR.newContext({ viewport: { width: 1200, height: 900 } }), ap = await ac.newPage();
    await ap.setExtraHTTPHeaders({ 'Cf-Access-Jwt-Assertion': token(FND) }); await ap.goto(S.url + '/checkout-pilot', { waitUntil: 'load' });
    await ap.waitForSelector('#basket', { timeout: 20000 });
    let txt = await ap.textContent('#basket');
    check('U1 artist page: the basket section shows the seller information buyers will see, its confirmation, and the Founding processing-fee consent as given',
      /Seller information shown to buyers before payment/.test(txt) && /1 Studio Lane, Dublin 8/.test(txt) && /Confirmed on/.test(txt) && /You agreed on .* 0% PlotArt commission/.test(txt) && !/VAT number/.test(txt), txt.slice(0, 800));
    await ap.click('button[data-a2="withdraw-basket-processing"]'); await ap.waitForSelector('form[data-f="basket-processing"]', { timeout: 10000 });
    txt = await ap.textContent('#basket');
    check('U2 artist withdraws the consent on screen; the full statement and an unticked box are then offered again', /0% commission/.test(txt) && /dispute fees/.test(txt) && !(await ap.isChecked('form[data-f="basket-processing"] input[name="accept"]'))
      && (await one("SELECT kind FROM basket_consents WHERE artist_id = 'afnd' AND topic = 'processing_fees' ORDER BY at DESC, rowid DESC LIMIT 1")).kind === 'withdrawn');
    await ap.check('form[data-f="basket-processing"] input[name="accept"]'); await ap.click('form[data-f="basket-processing"] button'); await ap.waitForSelector('button[data-a2="withdraw-basket-processing"]', { timeout: 10000 });
    check('U3 artist gives the consent again by ticking the box: recorded against the current addendum', (await one("SELECT * FROM basket_consents WHERE artist_id = 'afnd' AND topic = 'processing_fees' ORDER BY at DESC, rowid DESC LIMIT 1")).doc_id === BAA.doc_id);
    const before = await one("SELECT delivery_cents, version FROM artwork_delivery_offers WHERE artwork_id = 'wafnd3'");
    const li = ap.locator('li[data-id="wafnd3"]'); await li.locator('summary').click();
    await li.locator('input[name="charge"]').fill('35.00'); await li.locator('input[name="confirm"]').check(); await li.locator('button[type="submit"]').click();
    await ap.waitForFunction(() => /€35\.00/.test(document.querySelector('li[data-id="wafnd3"]')?.textContent || ''), null, { timeout: 10000 }).catch(() => {});
    const after = await one("SELECT delivery_cents, version FROM artwork_delivery_offers WHERE artwork_id = 'wafnd3'");
    check('U4 artist changes a delivery offer on screen (the form is prefilled with the current offer): a new version at the new charge', after.delivery_cents === 3500 && after.version === before.version + 1, { before, after });
    if (UISHOT) await ap.screenshot({ path: `${UISHOT}/artist-basket.png`, fullPage: true });
    await ac.close();
    // founder: readiness per artist
    const fc = await BR.newContext({ viewport: { width: 1280, height: 900 } }), fp = await fc.newPage();
    await fp.setExtraHTTPHeaders({ 'Cf-Access-Jwt-Assertion': token(FOUNDER) }); await fp.goto(S.url + '/admin/checkout', { waitUntil: 'load' });
    await fp.waitForSelector('#basket-readiness', { timeout: 20000 }); txt = await fp.textContent('#basket-readiness');
    check('U5 founder page: basket readiness per artist (consent and its document version, seller information confirmation, what is missing)', /Fia Founding \(Founding\)/.test(txt) && /given .*PA-BAA-TEST-01/.test(txt) && /confirmed /.test(txt) && /basket addendum/.test(txt), txt.slice(0, 600));
    if (UISHOT) await fp.locator('#basket-readiness').screenshot({ path: `${UISHOT}/founder-readiness.png` });
    // the Review desk's Basket readiness tab: the same section, inside the Review desk header and tabs (22 Nov 2026)
    await fp.goto(S.url + '/admin/baskets', { waitUntil: 'load' }); await fp.waitForSelector('#basket-readiness', { timeout: 20000 });
    const tabs = await fp.$$eval('.st-tabs a', as => as.map(a => [a.textContent, a.getAttribute('aria-current')]));
    txt = await fp.textContent('#basket-readiness');
    check('U5a Review desk "Basket readiness" tab: every Review desk tab kept, this one current; the same readiness table with online purchase per artist; one dashboard (no second copy)',
      tabs.length === 11 && tabs[0][0] === 'Review desk' && tabs[10][0] === 'Basket readiness' && tabs[10][1] === 'page' && tabs.filter(t => t[1]).length === 1
      && /Fia Founding \(Founding\)/.test(txt) && /Online purchase/.test(txt) && /of \d+ available artworks can be bought online/.test(txt) && (await fp.$$('#basket-readiness')).length === 1
      && /Open the Payment pilot page/.test(await fp.textContent('#app')), { tabs, txt: txt.slice(0, 600) });
    if (UISHOT) { await fp.screenshot({ path: `${UISHOT}/review-desk-basket-tab.png`, fullPage: true }); await fp.setViewportSize({ width: 390, height: 844 }); await fp.screenshot({ path: `${UISHOT}/review-desk-basket-tab-phone.png`, fullPage: true }); await fp.setViewportSize({ width: 1280, height: 900 }); }
    // Review desk tabs wrap from tablet width up: every tab fully inside the bar, no sideways scrolling; phones keep one scrolling row
    const fit = [];
    for (const w of [1920, 1440, 1280, 1024, 768, 480]) {
      await fp.setViewportSize({ width: w, height: 900 }); await fp.goto(S.url + '/admin/baskets', { waitUntil: 'load' }); await fp.waitForSelector('#basket-readiness', { timeout: 20000 });
      fit.push(await fp.evaluate(w => { const n = document.querySelector('.st-tabs'), r = n.getBoundingClientRect(), as = [...n.querySelectorAll('a')];
        const rows = new Set(as.map(a => Math.round(a.getBoundingClientRect().top))).size;
        return { w, inside: as.every(a => { const b = a.getBoundingClientRect(); return b.left >= r.left - 0.5 && b.right <= r.right + 0.5; }), scroll: n.scrollWidth > n.clientWidth + 1,
          page: document.documentElement.scrollWidth > innerWidth + 1, rows, font: getComputedStyle(as[0]).fontSize }; }, w));
      if (UISHOT && [1280, 768].includes(w)) await fp.screenshot({ path: `${UISHOT}/review-desk-tabs-${w}.png`, clip: { x: 0, y: 0, width: w, height: 260 } });
    }
    await fp.setViewportSize({ width: 390, height: 844 }); await fp.goto(S.url + '/admin', { waitUntil: 'load' });
    const ph = await fp.evaluate(() => { const n = document.querySelector('.st-tabs'); return { scroll: n.scrollWidth > n.clientWidth + 1, wrap: getComputedStyle(n).flexWrap, page: document.documentElement.scrollWidth > innerWidth + 1 }; });
    const st = await fp.goto(S.url + '/admin', { waitUntil: 'load' }).then(() => fp.evaluate(() => getComputedStyle(document.querySelector('.st-tabs a')).fontSize));
    check('U5c Review desk tabs: from 480 to 1920 px every tab (incl. Basket readiness) is fully visible, wrapping to a second row when needed, no sideways scrolling, same 14px labels; phones keep the one scrolling row',
      fit.every(f => f.inside && !f.scroll && !f.page && f.font === '14px') && fit.find(f => f.w === 768).rows >= 2 && ph.wrap === 'nowrap' && ph.scroll && !ph.page && st === '13.5px', { fit, ph, st });
    await fp.setViewportSize({ width: 1280, height: 900 });
    const dk = await fp.goto(S.url + '/admin', { waitUntil: 'load' }).then(() => fp.$$eval('.st-tabs a', as => as.map(a => [a.textContent, a.getAttribute('href')])));
    check('U5b the Review desk itself shows the Basket readiness tab, after Opportunities', dk.length === 11 && dk[9][0] === 'Opportunities' && dk[10][0] === 'Basket readiness' && dk[10][1] === '/admin/baskets', dk);
    await fc.close();
    // buyer: a discreet, collapsed "Seller and returns information" per artist, desktop and phone
    // every earlier work has been sold by now: three fresh synthetic works (one Gallery, two Founding), published, with offers
    for (const [src, id] of [['wagal1', 'wagal9'], ['wafnd1', 'wafnd8'], ['wafnd1', 'wafnd9']]) {
      await db.prepare(`INSERT INTO artworks (id, artist_id, slug, title, year, medium, materials, h_cm, w_cm, d_cm, price_eur, price_on_request, availability, description, ord, ai_involvement, ai_note, archived, created_at, updated_at)
        SELECT ?, artist_id, ?, title || ' II', year, medium, materials, h_cm, w_cm, d_cm, price_eur, 0, 'available', description, ord + 50, ai_involvement, ai_note, 0, created_at, updated_at FROM artworks WHERE id = ?`).bind(id, id, src).run();
      const w = await one('SELECT * FROM artworks WHERE id = ?', id), v = await one('SELECT version, snapshot FROM versions WHERE artist_id = ? ORDER BY version DESC LIMIT 1', w.artist_id), snap = JSON.parse(v.snapshot);
      snap.works.push({ ...snap.works.find(x => x.id === src), id, slug: id, title: w.title, availability: 'available' });
      await db.prepare('UPDATE versions SET snapshot = ? WHERE artist_id = ? AND version = ?').bind(JSON.stringify(snap), w.artist_id, v.version).run();
      await call('PUT', `/api/checkout/basket/offers/${id}`, w.artist_id === 'agal' ? GAL : FND, { confirm: true, delivery_cents: 3000, delivery: DELIVERY });
    }
    await approveOffers(['wagal9', 'wafnd8', 'wafnd9']);
    const avail = (await call('GET', '/api/admin/checkout/baskets/eligibility?ids=wagal9,wafnd8,wafnd9', FOUNDER)).j.items.filter(i => i.ok).map(i => i.id);
    const pick = avail;
    for (const [vw, vh, name] of [[1280, 900, 'desktop'], [390, 844, 'phone']]) {
      const bc = await BR.newContext({ viewport: { width: vw, height: vh } });
      await bc.route('**/*', async route => { const u = new URL(route.request().url()); if (u.origin !== ORIGIN) return route.fulfill({ status: 404, body: '' });
        const req = route.request(); const rr = await CW.fetch(req.url(), { method: req.method(), headers: { ...req.headers(), Origin: ORIGIN }, body: req.postData() || undefined, redirect: 'manual' });
        return route.fulfill({ status: rr.status, headers: Object.fromEntries(rr.headers), body: Buffer.from(await rr.arrayBuffer()) }); });
      const bp2 = await bc.newPage();
      await bp2.goto(ORIGIN + '/basket'); await bp2.evaluate(b => localStorage.setItem('pa-basket-v1', JSON.stringify(b)), pick.map(id => ({ id, img: null })));
      await bp2.goto(ORIGIN + '/basket', { waitUntil: 'load' }); await bp2.waitForSelector('details.sri', { timeout: 15000 });
      const n = await bp2.locator('details.sri').count(), open0 = await bp2.locator('details.sri[open]').count(), sum = await bp2.locator('details.sri summary').allTextContents();
      await bp2.locator('details.sri summary').first().click();
      const body = await bp2.locator('details.sri').first().textContent(), wide = await bp2.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      const vat = await bp2.locator('details.sri dt', { hasText: 'VAT number' }).count();
      const btnTxt = (await bp2.locator('#pay').textContent()).trim(), tot = (await bp2.locator('#t-tot').textContent()).trim();
      check(`U7 buyer basket (${name}): the button reads “Buy now · <total> total” and the next step (Stripe’s Save completes the purchase) is stated`, btnTxt === `Buy now · ${tot} total` && /select Save there to complete your purchase/.test(await bp2.locator('.nx').textContent()), { btnTxt, tot });
      check(`U6 buyer basket (${name}): one collapsed “Seller and returns information” per artist (${pick.length} works, 2 artists), with seller, address, email, telephone and returns; no VAT line when not registered; no sideways scroll`,
        pick.length === 3 && n === 2 && open0 === 0 && sum.every(t => /^Seller and returns information · /.test(t)) && /Seller/.test(body) && /Address/.test(body) && /Email/.test(body) && /Telephone/.test(body) && /Same courier, insured/.test(body) && vat === 0 && !wide,
        { n, open0, sum, body: body.slice(0, 400), wide, pick });
      if (UISHOT) await bp2.screenshot({ path: `${UISHOT}/basket-${name}.png`, fullPage: true });
      await bc.close();
    }
  }
}

console.log('— artist: Online sales in the Studio (card, tab, steps; 22 Nov 2026)');
{
  // a Gallery Artist who completed the original gallery set-up and has not started online sales
  const NEW = 'new@example.test';
  await seedPublished(db, { id: 'anew', slug: 'nia', email: NEW, name: 'Nia New', works: 2, publishedAt: ago(10) });
  await db.prepare("UPDATE artists SET founding = 0 WHERE id = 'anew'").run();
  const statusBefore = (await call('GET', '/api/me', NEW)).j;
  const rn = (await call('GET', '/api/checkout/basket/readiness', NEW)).j, rg = (await call('GET', '/api/checkout/basket/readiness', GAL)).j, rb = (await call('GET', '/api/checkout/basket/readiness', NOB)).j;
  const fa = Object.fromEntries((await call('GET', '/api/admin/checkout/baskets/artists', FOUNDER)).j.artists.map(a => [a.id, a]));
  const same = (r, f) => r.steps.filter(x => !x.done).length === f.missing.length && r.online.available === f.online.available && r.online.purchasable === f.online.purchasable && r.ready === !f.missing.length;
  check('OS1 artist readiness: six steps in page order, next step, artworks online; an artist who has not started has nothing done and nothing on sale',
    rn.installed && rn.steps.map(x => x.key).join() === 'join,seller,stripe,basket,disclosure,delivery' && rn.done === 0 && !rn.started && rn.next === 'join' && rn.online.purchasable === 0 && rn.online.available === 2
    && rn.online.reasons['online sales set-up not finished'] === 2 && rg.ready && rg.done === 6, { rn, rg });
  check('OS2 the artist and the founder see the same answer (one readiness check): steps left = founder’s “missing”, same artworks online, for every artist',
    same(rn, fa.anew) && same(rg, fa.agal) && same(rb, fa.anob), { rn: rn.steps, fan: fa.anew.missing, rb: rb.steps, fab: fa.anob.missing });
  check('OS3 nothing internal reaches the artist: no founder labels, no internal reasons, no other artist',
    !JSON.stringify(rg).includes('founder') && !/artist not ready|no valid processing-fee consent|policy\)/.test(JSON.stringify([rn, rg, rb])) && !JSON.stringify(rn).includes('agal'));
  const statusAfter = (await call('GET', '/api/me', NEW)).j;
  check('OS4 the gallery checklist and publication state are untouched by online sales (an enquiry-only gallery stays complete and live)',
    JSON.stringify(statusBefore.status.checklist) === JSON.stringify(statusAfter.status.checklist) && statusAfter.status.state === statusBefore.status.state && statusAfter.status.state === 'live'
    && !JSON.stringify(statusAfter.status.checklist).toLowerCase().includes('stripe'), { b: statusBefore.status, a: statusAfter.status.state });
  if (BR) {
    const UISHOT = process.env.BASKET_UI_SHOTS || null;
    const page = async (email, w = 1200) => { const c = await BR.newContext({ viewport: { width: w, height: 900 } }), pg = await c.newPage(); await pg.setExtraHTTPHeaders({ 'Cf-Access-Jwt-Assertion': token(email) }); return [c, pg]; };
    // Studio home: the card after the gallery checklist, for not started / in progress / set up
    const homes = {};
    for (const [k, e] of [['new', NEW], ['nob', NOB], ['gal', GAL]]) {
      const [c, pg] = await page(e); await pg.goto(S.url + '/', { waitUntil: 'load' });
      await pg.waitForSelector('#os-card:not([hidden])', { timeout: 20000 }).catch(() => {});
      homes[k] = await pg.evaluate(() => { const card = document.querySelector('#os-card'), ck = document.querySelector('#ck-h');
        return { text: card && !card.hidden ? card.textContent.replace(/\s+/g, ' ').trim() : null, after: !!(ck && card && (ck.compareDocumentPosition(card) & Node.DOCUMENT_POSITION_FOLLOWING)),
          tabs: [...document.querySelectorAll('.st-tabs a')].map(a => a.textContent), btn: card && card.querySelector('.st-actions a')?.getAttribute('href') }; });
      if (UISHOT) await pg.locator('#os-card').screenshot({ path: `${UISHOT}/studio-card-${k}.png` }).catch(() => {});
      if (UISHOT && k === 'new') await pg.screenshot({ path: `${UISHOT}/studio-home-new.png`, fullPage: true });
      await c.close();
    }
    check('OS5 Studio home: an optional “Online sales” card after the gallery checklist; not started → “Set up online sales”, in progress → steps done and the next step, set up → artworks online',
      homes.new.after && /Online sales\s*Optional/.test(homes.new.text) && /Set up online sales/.test(homes.new.text) && /work exactly as now/.test(homes.new.text)
      && /\d of 6 steps done/.test(homes.nob.text) && /Next: /.test(homes.nob.text) && /Continue set-up/.test(homes.nob.text)
      && /Online sales are set up/.test(homes.gal.text) && /can be bought online/.test(homes.gal.text) && /Manage online sales/.test(homes.gal.text) && homes.gal.btn === '/checkout-pilot', homes);
    check('OS6 Studio tabs: “Online sales” after Enquiries; every earlier tab kept', homes.new.tabs.join('|') === 'Gallery|Works|Profile|Opportunities|Enquiries|Online sales|Agreement|Preview ↗', homes.new.tabs);
    // the Online sales page: Studio tabs, the steps, the artworks line
    const pages = {};
    for (const [k, e, w] of [['new', NEW, 1200], ['gal', GAL, 1200], ['new-phone', NEW, 390]]) {
      const [c, pg] = await page(e, w); await pg.goto(S.url + '/checkout-pilot', { waitUntil: 'load' }); await pg.waitForSelector('.st-os-steps', { timeout: 20000 });
      pages[k] = await pg.evaluate(() => ({ tabs: [...document.querySelectorAll('.st-tabs a')].map(a => [a.textContent, a.getAttribute('href'), a.getAttribute('aria-current')]),
        steps: [...document.querySelectorAll('.st-os-list li')].map(li => li.className + ':' + li.querySelector('.st-os-s').textContent),
        text: document.querySelector('.st-os-steps').textContent.replace(/\s+/g, ' '), h1: document.querySelector('h1').textContent, wide: document.documentElement.scrollWidth > innerWidth + 1 }));
      if (UISHOT) await pg.screenshot({ path: `${UISHOT}/online-sales-${k}.png`, fullPage: true });
      if (k === 'new') { await pg.click('a[data-step="join"]'); await pg.waitForFunction(() => { const t = document.querySelector('#pay-join').getBoundingClientRect(); return t.top >= 0 && t.top < innerHeight / 2; }, null, { timeout: 5000 }).catch(() => {}); pages.jump = await pg.evaluate(() => { const t = document.querySelector('#pay-join').getBoundingClientRect(); return t.top < innerHeight && t.bottom > 0; }); }
      await c.close();
    }
    check('OS7 Online sales page: the Studio tabs with “Online sales” current (others lead back to the Studio); the heading says it is optional',
      pages.new.tabs.length === 8 && pages.new.tabs.find(t => t[0] === 'Online sales')[2] === 'page' && pages.new.tabs.find(t => t[0] === 'Works')[1] === '/#/works' && pages.new.h1 === 'Online sales', pages.new.tabs);
    check('OS8 “Your steps”: six steps, the first marked Next for a new artist, all Done when set up; each jumps to its section',
      pages.new.steps.length === 6 && pages.new.steps[0] === 'next:Next' && pages.new.steps.slice(1).every(x => x === ':To do') && pages.gal.steps.every(x => x === 'done:Done') && pages.jump, pages);
    check('OS9 artwork eligibility on the page: how many available artworks can be bought online and why not, in plain words',
      /0 of 2 available artworks can be bought online/.test(pages.new.text) && /2 online sales set-up not finished/.test(pages.new.text) && /stay on enquiry/.test(pages.new.text)
      && /of \d available artworks can be bought online/.test(pages.gal.text) && /price on request \(add a price to sell online\)/.test(pages.gal.text) && !pages['new-phone'].wide, { n: pages.new.text, g: pages.gal.text });
    const [fc, fp] = await page(FOUNDER, 1280); await fp.goto(S.url + '/admin/checkout', { waitUntil: 'load' }); await fp.waitForSelector('#basket-readiness', { timeout: 20000 });
    const fh = await fp.evaluate(() => ({ h1: document.querySelector('h1').textContent, tabs: [...document.querySelectorAll('.st-tabs a')].map(a => a.textContent) }));
    check('OS10 the founder’s Payment pilot page is unchanged (its own heading and navigation)', /^Payment pilot/.test(fh.h1) && fh.tabs.join() === 'Studio', fh);
    await fc.close();
  }
}

/* ================================================================ delivery safety (22 Nov 2026) */
console.log('— delivery safety: founder review of delivery offers, deadlines, islands, Ireland-only, overdue alerts');
{
  const fresh = async (src, id) => {
    await db.prepare(`INSERT INTO artworks (id, artist_id, slug, title, year, medium, materials, h_cm, w_cm, d_cm, price_eur, price_on_request, availability, description, ord, ai_involvement, ai_note, archived, created_at, updated_at)
      SELECT ?, artist_id, ?, title || ' DS', year, medium, materials, h_cm, w_cm, d_cm, price_eur, 0, 'available', description, ord + 80, ai_involvement, ai_note, 0, created_at, updated_at FROM artworks WHERE id = ?`).bind(id, id, src).run();
    const w = await one('SELECT * FROM artworks WHERE id = ?', id), v = await one('SELECT version, snapshot FROM versions WHERE artist_id = ? ORDER BY version DESC LIMIT 1', w.artist_id), snap = JSON.parse(v.snapshot);
    snap.works.push({ ...snap.works.find(x => x.id === src), id, slug: id, title: w.title, availability: 'available' });
    await db.prepare('UPDATE versions SET snapshot = ? WHERE artist_id = ? AND version = ?').bind(JSON.stringify(snap), w.artist_id, v.version).run();
    return w;
  };
  const elig = async id => (await call('GET', '/api/admin/checkout/baskets/eligibility?ids=' + id, FOUNDER)).j.items[0];
  const offers = async () => (await call('GET', '/api/admin/checkout/baskets/offers', FOUNDER)).j;
  const offerOf = async id => (await offers()).offers.find(o => o.artwork_id === id);
  const review = (id, body, who = FOUNDER) => call('POST', `/api/admin/checkout/baskets/offers/${id}/review`, who, body);
  check('DS1 the founder approved the first offers through the Review desk API; each approval is an audit row naming the founder, the exact version and fingerprint',
    approvedFirst === 6 && (await q('SELECT * FROM delivery_offer_reviews')).filter(r => r.decision === 'approved' && /^founder:/.test(r.reviewed_by) && r.offer_sha256.length === 64).length >= 6, approvedFirst);

  await fresh('wagal1', 'wds1'); await fresh('wagal1', 'wds2'); await fresh('wafnd1', 'wds3');
  r = await call('PUT', '/api/checkout/basket/offers/wds1', GAL, { confirm: true, delivery_cents: 4500, delivery: { ...DELIVERY, dispatch_days: undefined, delivery_days: undefined } });
  check('DS2 a delivery offer without dispatch and delivery deadlines is refused when saved', r.s === 409 && /dispatch deadline/.test(r.j.error), r.j);
  r = await call('PUT', '/api/checkout/basket/offers/wds1', GAL, { confirm: true, delivery_cents: 4500, delivery: { ...DELIVERY, dispatch_days: 9, delivery_days: 5 } });
  check('DS2a the delivery deadline cannot be earlier than dispatch', r.s === 409 && /no earlier than dispatch/.test(r.j.error), r.j);
  r = await call('PUT', '/api/checkout/basket/offers/wds1', GAL, { confirm: true, delivery_cents: 4500, delivery: DELIVERY });
  const e1 = await elig('wds1');
  check('DS3 a saved offer leaves the artwork enquiry-only until the founder approves it', r.s === 200 && r.j.review === 'awaiting_founder_review' && !e1.ok && e1.why === 'delivery offer awaiting founder approval', { r: r.j, e1 });
  const o1 = await offerOf('wds1');
  r = await review('wds1', { decision: 'approved', version: o1.version, sha256: o1.sha256, confirm: true, statement: (await offers()).statement }, GAL);
  check('DS4 an artist cannot approve their own offer (founder-only route: 403)', r.s === 403, r.s);
  r = await review('wds1', { decision: 'approved', version: o1.version, sha256: o1.sha256 });
  check('DS5 approval needs the founder’s explicit confirmation of the review statement', r.s === 400 && /Tick the box/.test(r.j.error), r.j);
  r = await review('wds1', { decision: 'approved', version: o1.version, sha256: 'f'.repeat(64), confirm: true, statement: (await offers()).statement });
  check('DS6 approving a version or content other than the current one is refused (stale review page)', r.s === 409 && /changed this delivery offer/.test(r.j.error), r.j);
  r = await review('wds1', { decision: 'approved', version: o1.version, sha256: o1.sha256, confirm: true, statement: (await offers()).statement });
  const e2 = await elig('wds1');
  check('DS7 after the founder approves the exact version the artwork can be bought online', r.s === 200 && e2.ok, { r: r.j && r.j.error, e2 });
  r = await call('PUT', '/api/checkout/basket/offers/wds1', GAL, { confirm: true, delivery_cents: 4600, delivery: DELIVERY });
  const e3 = await elig('wds1'), o3 = await offerOf('wds1');
  check('DS8 any change by the artist (here the charge) is a new version: the earlier approval no longer counts and the artwork is enquiry-only again',
    !e3.ok && e3.why === 'delivery offer awaiting founder approval' && o3.review.state === 'awaiting_review' && o3.review.previous && o3.review.previous.decision === 'approved', { e3, rv: o3.review });
  r = await call('PUT', '/api/checkout/basket/offers/wds1', GAL, { confirm: true, delivery_cents: 4600, delivery: { ...DELIVERY, cover_provider: 'Other Underwriting (SIMULATED)' } });
  r = await review('wds1', { decision: 'approved', version: o3.version, sha256: o3.sha256, confirm: true, statement: (await offers()).statement });
  check('DS9 an approval prepared for an earlier version cannot be applied after a further change (insurance details changed)', r.s === 409 && !(await elig('wds1')).ok, r.j);
  const o4 = await offerOf('wds1');
  r = await review('wds1', { decision: 'returned', version: o4.version, sha256: o4.sha256, note: 'x' });
  check('DS10 returning an offer needs a note for the artist', r.s === 400, r.j);
  r = await review('wds1', { decision: 'returned', version: o4.version, sha256: o4.sha256, note: 'Please confirm the insurer covers wall-hung works in transit.' });
  const av = (await call('GET', '/api/checkout/basket', GAL)).j.works.find(w => w.id === 'wds1');
  check('DS11 a returned offer stays enquiry-only and the artist sees PlotArt’s note', r.s === 200 && (await elig('wds1')).why === 'delivery offer returned by the founder'
    && av.offer.review.state === 'returned' && /wall-hung/.test(av.offer.review.note), av.offer);
  let trig = null; try { await db.prepare("UPDATE delivery_offer_reviews SET decision = 'approved'").run(); } catch (e) { trig = e.message; }
  let trig2 = null; try { await db.prepare('DELETE FROM delivery_offer_reviews').run(); } catch (e) { trig2 = e.message; }
  let trig3 = null; try { await db.prepare("INSERT INTO delivery_offer_reviews (id, artwork_id, artist_id, offer_version, offer_sha256, decision, reviewed_by, reviewed_at) VALUES ('drx','wds1','agal',1,'x','approved','founder:x','2026-11-22')").run(); } catch (e) { trig3 = e.message; }
  check('DS12 the review record is append-only and cannot approve a version that is not current (database triggers)', /never change/.test(trig) && /never removed/.test(trig2) && /not the current version/.test(trig3), { trig, trig2, trig3 });
  const ev = await q("SELECT kind, offer_version FROM delivery_offer_events WHERE artwork_id = 'wds1' ORDER BY at");
  r = await call('DELETE', '/api/checkout/basket/offers/wds1', GAL);
  check('DS13 the artist’s saves and withdrawals are recorded with the version', ev.length === 3 && ev.every(x => x.kind === 'saved') && (await q("SELECT kind FROM delivery_offer_events WHERE artwork_id = 'wds1' AND kind = 'withdrawn'")).length === 1, ev);

  // islands
  await call('PUT', '/api/checkout/basket/offers/wds2', GAL, { confirm: true, delivery_cents: 4500, delivery: DELIVERY });
  await call('PUT', '/api/checkout/basket/offers/wds3', FND, { confirm: true, delivery_cents: 9000, delivery: { ...DELIVERY, offshore_islands: true } });
  await approveOffers(['wds2', 'wds3']);
  const items = (await pub('GET', '/api/basket/items?ids=wds2,wds3')).j;
  check('DS14 the basket items say, per artwork, whether offshore islands are covered, and carry the Ireland-only delivery scope',
    items.items.find(i => i.id === 'wds2').delivery.islands === false && items.items.find(i => i.id === 'wds3').delivery.islands === true && /Republic of Ireland only/.test(items.delivery_scope), items);
  const ISL = { address_line1: 'Teach na Trá', town: 'Inis Oírr', county: 'Galway', eircode: '' };
  r = await pub('POST', '/basket/checkout', { json: basketReq(['wds2', 'wds3'], { island: 'yes' }) });
  check('DS15 a buyer who says the address is on an offshore island cannot buy an artwork whose offer does not cover islands: directed to enquire', r.s === 409 && /offshore island/.test(r.j.error) && /enquire/.test(r.j.error), r.j);
  r = await pub('POST', '/basket/checkout', { json: basketReq(['wds2'], { ...ISL, island: 'no' }) });
  check('DS16 an address naming an offshore island (Inis Oírr) is treated as an island even if the box says no', r.s === 409 && /offshore island/.test(r.j.error), r.j);
  r = await pub('POST', '/basket/checkout', { json: basketReq(['wds2'], { island: undefined }) });
  check('DS17 the buyer must answer the island question', r.s === 400 && /offshore island/.test(r.j.error), r.j);
  r = await pub('POST', '/basket/checkout', { json: basketReq(['wds3'], { ...ISL, island: 'yes' }) });
  const ib = r.j && r.j.url ? await one("SELECT * FROM checkout_baskets ORDER BY created_at DESC, rowid DESC LIMIT 1") : null;
  const io = ib ? await one('SELECT delivery FROM checkout_orders WHERE enquiry_ref = ?', ib.reference) : null;
  check('DS18 an artwork whose founder-approved offer includes islands can be bought for an island address (recorded on the order)', r.s === 200 && !!r.j.url && /offshore island/.test(JSON.parse(io.delivery).destination) && JSON.parse(io.delivery).destination_country === 'IE', r.j);
  if (ib) { const tk = new URL(r.j.url).pathname; await db.prepare("UPDATE checkout_baskets SET status = status WHERE id = ?").bind(ib.id).run(); }

  // Ireland-only shown before checkout
  const bp = await pub('GET', '/basket');
  const iScope = bp.t.indexOf('Republic of Ireland only'), iForm = bp.t.indexOf('id="buy"');
  check('DS19 the basket page states Ireland-only delivery before the buyer starts checkout (above the items and address form), and the county field says Republic of Ireland',
    iScope > 0 && iScope < iForm && /County \(Republic of Ireland\)/.test(bp.t) && /offshore island/.test(bp.t), { iScope, iForm });
  const gp = readFileSync(HERE + '../../atlas-tools/plotart_gallery_pages.py', 'utf8');
  check('DS20 the artwork-page basket note (gallery generator) says online purchase delivers in the Republic of Ireland only', /Online purchase delivers in the Republic of Ireland only; for delivery elsewhere, please enquire/.test(gp));

  // nothing purchasable without every approval
  const allIds = (await q("SELECT id FROM artworks WHERE archived = 0")).map(x => x.id);
  let bad = [];
  for (let k = 0; k < allIds.length; k += 40) {
    const its = (await call('GET', '/api/admin/checkout/baskets/eligibility?ids=' + allIds.slice(k, k + 40).join(','), FOUNDER)).j.items.filter(i => i.ok);
    for (const it of its) {
      const o = await one('SELECT * FROM artwork_delivery_offers WHERE artwork_id = ?', it.id), rv = await one('SELECT * FROM delivery_offer_reviews WHERE artwork_id = ? ORDER BY reviewed_at DESC, rowid DESC LIMIT 1', it.id);
      if (!o || o.withdrawn_at || !rv || rv.decision !== 'approved' || rv.offer_version !== o.version) bad.push(it.id);
    }
  }
  const okCount = (await Promise.all(allIds.map(elig))).filter(i => i.ok).length;
  check('DS21 every artwork that can be bought online has a current, founder-approved delivery offer for its exact current version (all artworks checked)', !bad.length && okCount > 0, { bad, okCount });

  // overdue dispatch and delivery
  const po = await one("SELECT * FROM checkout_orders WHERE status = 'paid' AND COALESCE(fulfilment_status,'none') = 'none' ORDER BY paid_at LIMIT 1");
  const dd = JSON.parse(po.delivery);
  await db.prepare('UPDATE checkout_orders SET paid_at = ? WHERE id = ?').bind(ago(dd.delivery_days + 3), po.id).run();
  const sinkBefore = (await q("SELECT id FROM checkout_mail_sink WHERE to_role = 'founder' AND kind IN ('dispatch_overdue','delivery_overdue')")).length;
  await CW.scheduled({ scheduledTime: Date.now(), cron: '*/15 * * * *' });
  const al = await q("SELECT * FROM checkout_mail_sink WHERE to_role = 'founder' AND kind IN ('dispatch_overdue','delivery_overdue') AND order_id = ?", po.id);
  const art = JSON.parse(po.artwork_snapshot), sel = JSON.parse(po.seller);
  check('DS22 the scheduled sweep alerts the founder when a paid order passes its agreed dispatch and delivery dates: artwork, artist, order reference and overdue status',
    sinkBefore === 0 && al.length === 2 && al.every(a => a.body.includes(po.reference) && a.body.includes(art.title) && a.body.includes(sel.name) && /Overdue: \d+ day/.test(a.body) && /agreed/.test(a.body)), al.map(a => a.body.slice(0, 300)));
  await CW.scheduled({ scheduledTime: Date.now(), cron: '*/15 * * * *' }); await CW.scheduled({ scheduledTime: Date.now(), cron: '*/15 * * * *' });
  check('DS23 no duplicate alerts: later sweeps send nothing more for the same order (one row per order and kind)',
    (await q("SELECT id FROM checkout_mail_sink WHERE to_role = 'founder' AND kind IN ('dispatch_overdue','delivery_overdue') AND order_id = ?", po.id)).length === 2
    && (await q('SELECT * FROM order_overdue_alerts WHERE order_id = ?', po.id)).length === 2);
  const fa = (await call('GET', '/api/admin/checkout', FOUNDER)).j.founder_alerts.items.filter(x => x.order_id === po.id && /overdue/.test(x.kind));
  check('DS24 the alerts appear in the founder’s alerts panel with the reason, the due date and OVERDUE', fa.length === 2 && fa.every(x => x.state === 'open' && /OVERDUE/.test(x.due_label)) && fa.some(x => /not dispatched/.test(x.reason)), fa);
  const po2 = await one("SELECT * FROM checkout_orders WHERE status = 'paid' AND COALESCE(fulfilment_status,'none') = 'none' AND id <> ? ORDER BY paid_at LIMIT 1", po.id);
  await db.prepare('UPDATE checkout_orders SET paid_at = ? WHERE id = ?').bind(ago(1), po2.id).run();
  await CW.scheduled({ scheduledTime: Date.now(), cron: '*/15 * * * *' });
  check('DS25 an order still within its dates raises no alert', !(await q('SELECT * FROM order_overdue_alerts WHERE order_id = ?', po2.id)).length);
  const C2 = await import(HERE + FIX + 'src/checkout.js');
  const st = C2.overdueState({ status: 'paid', fulfilment_status: 'dispatched', paid_at: ago(12), delivery: JSON.stringify({ dispatch_days: 5, delivery_days: 10 }) });
  const st2 = C2.overdueState({ status: 'paid', fulfilment_status: 'none', paid_at: ago(16), delivery: JSON.stringify({}) });
  const st3 = C2.overdueState({ status: 'refunded', fulfilment_status: 'none', paid_at: ago(60), delivery: JSON.stringify({ dispatch_days: 5, delivery_days: 10 }) });
  check('DS26 deadline rules: a dispatched order is only delivery-overdue; an order with no agreed days uses the labelled defaults (14/30); refunded orders are not monitored',
    !st.dispatch.overdue && st.delivery.overdue && st2.basis === 'default' && st2.dispatch.overdue && !st2.delivery.overdue && !st3.dispatch.overdue && !st3.delivery.overdue, { st, st2, st3 });
  if (SHOTS) {   // review screenshots (BASKET_SCREENSHOTS=dir): the buyer basket with the Ireland-only notice, and the founder's review section
    await fresh('wagal1', 'wds4'); await call('PUT', '/api/checkout/basket/offers/wds4', GAL, { confirm: true, delivery_cents: 4500, delivery: DELIVERY }); await approveOffers(['wds4']);
    await shot('ds-basket-desktop', '/basket', { basket: [{ id: 'wds4', img: 'https://plotnua.ie/plotart/artists/gale/img/g1.png' }] });
    await shot('ds-basket-phone', '/basket', { basket: [{ id: 'wds4', img: 'https://plotnua.ie/plotart/artists/gale/img/g1.png' }], width: 390, height: 844 });
    await call('PUT', '/api/checkout/basket/offers/wds2', GAL, { confirm: true, delivery_cents: 4800, delivery: DELIVERY });   // one offer waiting for review
    for (const [w, n] of [[1280, 'desktop'], [390, 'phone']]) {
      const c = await BR.newContext({ viewport: { width: w, height: 900 }, deviceScaleFactor: 2 }), pg = await c.newPage(); await pg.setExtraHTTPHeaders({ 'Cf-Access-Jwt-Assertion': token(FOUNDER) });
      await pg.goto(S.url + '/admin/baskets', { waitUntil: 'load' }); await pg.waitForSelector('#offer-reviews', { timeout: 20000 });
      await pg.evaluate(() => { const d = document.querySelector('#offer-reviews article details.st-step'); if (d) d.open = true; });
      await (await pg.$('#offer-reviews')).screenshot({ path: `${SHOTS}/ds-founder-review-${n}.png` }); await c.close();
    }
  }
}

console.log(`\nMULTI-ARTIST BASKET · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
process.exitCode = results.every(Boolean) ? 0 : 1;
} finally {
  if (BR) await BR.close().catch(() => {});
  if (S) await S.mf.dispose();
  rmSync(HERE + FIX, { recursive: true, force: true });
}
