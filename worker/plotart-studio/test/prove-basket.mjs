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
const WHSEC = 'whsec_test_' + 'x'.repeat(24);
const M = { accounts: {}, v2accounts: {}, customers: {}, sessions: {}, pms: {}, pis: {}, charges: {}, feeAmounts: {}, feeRefunds: [], refunds: [], calls: [], idem: {}, n: 0,
  fail500: 0, cardBehaviour: {} };
const nid = p => `${p}_test_${(++M.n).toString(36).padStart(6, '0')}`;
const flat = body => Object.fromEntries(new URLSearchParams(body || ''));
const ok = o => new Response(JSON.stringify(o), { status: 200, headers: { 'Content-Type': 'application/json' } });
const err = (m, s = 400, extra = {}) => new Response(JSON.stringify({ error: { message: m, ...extra } }), { status: s, headers: { 'Content-Type': 'application/json' } });
const piView = p => ({ ...p, latest_charge: p.charge ? { id: p.charge, application_fee: p.fee } : null, _acct: undefined });
async function stripe(req) {
  const u = new URL(req.url);
  if (u.hostname !== 'stripe.mock') return err('unexpected outbound host ' + u.hostname, 599);
  const body = req.method === 'POST' ? await req.text() : '';
  const v2 = u.pathname.startsWith('/v2/');
  const jb = v2 && body ? JSON.parse(body) : null, f = v2 ? {} : flat(body), acct = req.headers.get('Stripe-Account'), idem = req.headers.get('Idempotency-Key');
  M.calls.push({ method: req.method, path: u.pathname, f, acct, idem, auth: req.headers.get('Authorization'), query: u.search });
  if (idem && M.idem[acct + '|' + idem]) return new Response(M.idem[acct + '|' + idem].body, { status: M.idem[acct + '|' + idem].status, headers: { 'Content-Type': 'application/json' } });
  const remember = (o, status = 200) => { const r = JSON.stringify(o); if (idem) M.idem[acct + '|' + idem] = { body: r, status }; return new Response(r, { status, headers: { 'Content-Type': 'application/json' } }); };
  if (M.fail500 > 0 && req.method === 'POST' && u.pathname === '/v1/payment_intents') { M.fail500--; return err('SIMULATED: temporary Stripe error', 500); }   // nothing created, nothing remembered
  let mm;
  if (u.pathname === '/v2/core/accounts' && req.method === 'POST') {
    const id = nid('acct').replace('_test', '');
    const v2a = { id, object: 'v2.core.account', livemode: false, contact_email: jb.contact_email, dashboard: jb.dashboard, identity: { country: String(jb.identity.country).toUpperCase() },
      defaults: { responsibilities: { ...jb.defaults.responsibilities, requirements_collector: 'stripe' } }, configuration: { merchant: { capabilities: { card_payments: { status: 'active' } } } }, requirements: { entries: [] }, metadata: jb.metadata };
    M.v2accounts[id] = v2a;
    M.accounts[id] = { id, object: 'account', livemode: false, charges_enabled: true, payouts_enabled: true, details_submitted: true, country: v2a.identity.country, requirements: { currently_due: [] } };
    return remember(v2a);
  }
  if (u.pathname === '/v2/core/account_links' && req.method === 'POST') return ok({ object: 'v2.core.account_link', account: jb.account, url: `https://accounts.stripe.test/r/${jb.account}`, livemode: false });
  if ((mm = u.pathname.match(/^\/v2\/core\/accounts\/(acct_\w+)$/))) return M.v2accounts[mm[1]] ? ok(M.v2accounts[mm[1]]) : err('no such account', 404);
  if ((mm = u.pathname.match(/^\/v1\/accounts\/(acct_\w+)$/))) return M.accounts[mm[1]] ? ok(M.accounts[mm[1]]) : err('no such account', 404);
  // platform: customers and the setup-mode card page
  if (u.pathname === '/v1/customers' && req.method === 'POST') { if (acct) return err('customer expected on the platform'); const c = { id: nid('cus'), object: 'customer', livemode: false, email: f.email, metadata: { plotart_basket: f['metadata[plotart_basket]'] } }; M.customers[c.id] = c; return remember(c); }
  if ((mm = u.pathname.match(/^\/v1\/customers\/(cus_test_\w+)$/)) && req.method === 'DELETE') { if (!M.customers[mm[1]]) return err('no such customer', 404); M.customers[mm[1]].deleted = true; for (const pm of Object.values(M.pms)) if (pm.customer === mm[1] && !pm._acct) pm.customer = null; return ok({ id: mm[1], deleted: true }); }
  if (u.pathname === '/v1/checkout/sessions' && req.method === 'POST') {
    if (acct) return err('the basket card page belongs on the platform account');
    if (f.mode !== 'setup') return err('setup mode expected');
    if (Object.keys(f).some(k => k.startsWith('payment_method_types'))) return err('Received unknown parameter: payment_method_types');
    const s = { id: nid('cs'), object: 'checkout.session', mode: 'setup', livemode: false, url: `https://checkout.stripe.test/c/setup/${M.n}`, status: 'open', customer: f.customer,
      expires_at: Number(f.expires_at), metadata: { plotart_basket: f['metadata[plotart_basket]'], plotart_reference: f['metadata[plotart_reference]'] }, setup_intent: null, _f: f };
    M.sessions[s.id] = s; return remember(s);
  }
  if ((mm = u.pathname.match(/^\/v1\/checkout\/sessions\/(cs_test_\w+)\/expire$/))) { const s = M.sessions[mm[1]]; if (!s || s.status !== 'open') return err('session is not open'); s.status = 'expired'; return ok(s); }
  if ((mm = u.pathname.match(/^\/v1\/checkout\/sessions\/(cs_test_\w+)$/))) { const s = M.sessions[mm[1]]; if (!s) return err('no such session', 404);
    return ok({ ...s, setup_intent: s.setup_intent && u.search.includes('setup_intent') ? { id: s.setup_intent, object: 'setup_intent', status: 'succeeded', payment_method: s._pm, usage: 'off_session' } : s.setup_intent }); }
  // connected account: clone, authorise (manual capture), capture, cancel, read
  if (u.pathname === '/v1/payment_methods' && req.method === 'POST') {
    if (!acct) return err('clone expected on a connected account');
    const src = M.pms[f.payment_method]; if (!src || src.customer !== f.customer || src._acct) return err('No such PaymentMethod for that customer', 400, { code: 'resource_missing' });
    const pm = { id: nid('pm'), object: 'payment_method', livemode: false, _acct: acct, _from: src.id, customer: null }; M.pms[pm.id] = pm; return remember(pm);
  }
  if (u.pathname === '/v1/payment_intents' && req.method === 'POST') {
    if (!acct) return err('direct charge expected');
    const pm = M.pms[f.payment_method];
    if (!pm || pm._acct !== acct) return err('No such PaymentMethod', 400, { code: 'resource_missing' });
    if (pm._used) return err('The provided PaymentMethod was previously used', 400);
    if (Object.keys(f).some(k => k.startsWith('payment_method_types'))) return err('Received unknown parameter: payment_method_types');
    pm._used = true;
    const beh = (M.cardBehaviour[pm._from] || {})[acct] || 'ok';
    const p = { id: nid('pi'), object: 'payment_intent', livemode: false, amount: Number(f.amount), amount_received: 0, currency: f.currency, capture_method: f.capture_method,
      application_fee_amount: f.application_fee_amount ? Number(f.application_fee_amount) : null, payment_method: pm.id, metadata: Object.fromEntries(Object.entries(f).filter(([k]) => k.startsWith('metadata[')).map(([k, v]) => [k.slice(9, -1), v])),
      client_secret: 'pi_secret_' + M.n, charge: null, fee: null, _acct: acct, _f: f, status: 'requires_capture', last_payment_error: null };
    M.pis[p.id] = p;
    if (beh === 'decline') { p.status = 'requires_payment_method'; p.last_payment_error = { code: 'card_declined', decline_code: 'generic_decline' };
      return remember({ error: { type: 'card_error', code: 'card_declined', decline_code: 'generic_decline', message: 'Your card was declined.', payment_intent: { id: p.id, status: p.status, client_secret: p.client_secret } } }, 402); }
    if (beh === 'auth') { p.status = 'requires_payment_method'; p.last_payment_error = { code: 'authentication_required', decline_code: 'authentication_required', payment_method: { id: pm.id } };
      return remember({ error: { type: 'card_error', code: 'authentication_required', decline_code: 'authentication_required', message: 'This payment requires authentication.', payment_intent: { id: p.id, status: p.status, client_secret: p.client_secret, last_payment_error: { payment_method: { id: pm.id } } } } }, 402); }
    return remember(piView(p));
  }
  if ((mm = u.pathname.match(/^\/v1\/payment_intents\/(pi_test_\w+)\/capture$/))) {
    const p = M.pis[mm[1]]; if (!p || p._acct !== acct) return err('no such pi', 404);
    if (p.status !== 'requires_capture') return err(`This PaymentIntent could not be captured because it has a status of ${p.status}.`, 400, { code: 'payment_intent_unexpected_state' });
    p.status = 'succeeded'; p.amount_received = p.amount; p.charge = nid('ch'); p.fee = p.application_fee_amount ? nid('fee') : null;
    if (p.fee) M.feeAmounts[p.fee] = p.application_fee_amount;
    const sf = Math.round(p.amount * 0.015) + 25, vat = Math.round(sf * 0.23);
    M.charges[p.charge] = { id: p.charge, fee: p.fee, created: Math.floor(Date.now() / 1000), bt: { id: nid('txn'), object: 'balance_transaction', created: Math.floor(Date.now() / 1000), currency: 'eur', amount: p.amount,
      fee: sf + vat + (p.application_fee_amount || 0), fee_details: [{ type: 'stripe_fee', amount: sf }, { type: 'tax', amount: vat }, ...(p.application_fee_amount ? [{ type: 'application_fee', amount: p.application_fee_amount }] : [])] } };
    return remember(piView(p));
  }
  if ((mm = u.pathname.match(/^\/v1\/payment_intents\/(pi_test_\w+)\/cancel$/))) {
    const p = M.pis[mm[1]]; if (!p || p._acct !== acct) return err('no such pi', 404);
    if (['succeeded', 'canceled'].includes(p.status)) return err(`You cannot cancel this PaymentIntent because it has a status of ${p.status}.`, 400, { code: 'payment_intent_unexpected_state' });
    p.status = 'canceled'; return remember(piView(p));
  }
  if ((mm = u.pathname.match(/^\/v1\/payment_intents\/(pi_test_\w+)$/))) { const p = M.pis[mm[1]]; return p && p._acct === acct ? ok(piView(p)) : err('no such pi', 404); }
  if ((mm = u.pathname.match(/^\/v1\/charges\/(ch_test_\w+)$/))) { const c = M.charges[mm[1]]; if (!c) return err('no such charge', 404);
    return ok({ id: c.id, object: 'charge', created: c.created, application_fee: c.fee, balance_transaction: u.search.includes('balance_transaction') ? c.bt : c.bt.id }); }
  if ((mm = u.pathname.match(/^\/v1\/application_fees\/(fee_test_\w+)\/refunds$/))) {
    if (req.method === 'GET') return ok({ object: 'list', data: M.feeRefunds.filter(x => x.fee === mm[1]).slice().reverse(), has_more: false });
    const done = M.feeRefunds.filter(x => x.fee === mm[1]).reduce((a, x) => a + x.amount, 0);
    if (done + Number(f.amount) > M.feeAmounts[mm[1]]) return err('Refund amount is greater than unrefunded amount on fee', 400);
    const r = { id: nid('fr'), object: 'fee_refund', amount: Number(f.amount), fee: mm[1], livemode: false, created: Math.floor(Date.now() / 1000), balance_transaction: nid('txn'), metadata: { plotart_kind: f['metadata[plotart_kind]'] } };
    M.feeRefunds.push(r); return remember(r);
  }
  if (u.pathname === '/v1/refunds' && req.method === 'POST') {
    const r = { id: nid('re'), object: 'refund', status: 'succeeded', created: Math.floor(Date.now() / 1000), amount: Number(f.amount), payment_intent: f.payment_intent, livemode: false,
      metadata: { plotart_refund: f['metadata[plotart_refund]'], plotart_order: f['metadata[plotart_order]'] }, _f: f, _acct: acct };
    M.refunds.push(r); return remember(r);
  }
  if ((mm = u.pathname.match(/^\/v1\/refunds\/(re_test_\w+)$/))) { const r = M.refunds.find(x => x.id === mm[1]); return r ? ok(r) : err('no such refund', 404); }
  return err('mock: unhandled ' + req.method + ' ' + u.pathname, 404);
}
/* The buyer enters a card on Stripe's setup page (mock). behaviour: { [account]: 'ok' | 'decline' | 'auth' } */
function enterCard(sessionId, behaviour = {}) {
  const s = M.sessions[sessionId]; const pm = { id: nid('pm'), object: 'payment_method', livemode: false, customer: s.customer };
  M.pms[pm.id] = pm; M.cardBehaviour[pm.id] = behaviour; s.status = 'complete'; s.setup_intent = nid('seti'); s._pm = pm.id; return s;
}
const sign = (raw, t = Math.floor(Date.now() / 1000), secret = WHSEC) => `t=${t},v1=${createHmac('sha256', secret).update(`${t}.${raw}`).digest('hex')}`;
let EV = 0;
const evt = (type, object, account = null) => ({ id: `evt_test_b${++EV}`, object: 'event', type, livemode: false, created: Math.floor(Date.now() / 1000), ...(account ? { account } : {}), data: { object } });

let S, BR = null;
try {
console.log('PROVE · multi-artist basket (direct charge per artwork, authorise all before capture)');
const ORIGIN = 'https://checkout.local';
const ENVV = { CHECKOUT_MESSAGE_RETRY_MINUTES: '0', CHECKOUT_PILOT_ENABLED: 'true', BASKET_ENABLED: 'true', BASKET_COMMISSION_FREE: 'with_processing_consent', STRIPE_SECRET_KEY: 'sk_test_mockkey123',
  STRIPE_PUBLISHABLE_KEY: 'pk_test_mockpublishable', STRIPE_WEBHOOK_SECRET: WHSEC, STRIPE_API_BASE: 'https://stripe.mock', CHECKOUT_ORIGIN: ORIGIN, GALLERY_ORIGIN: 'https://plotnua.ie' };
S = await start({ port: 8873, env: ENVV, script: FIX + 'src/index.js', checkout: { script: FIX + 'src/checkout-public.js', env: ENVV }, outbound: stripe });
const { db } = S, CW = S.checkoutWorker;
const mig = readFileSync(HERE + 'migrations/0019_multi_artist_basket.sql', 'utf8');
let migErr = null; for (const s of statements(mig)) { try { await db.prepare(s).run(); } catch (e) { migErr = e.message; } }
check('M1 proposed migration 0019 applies cleanly on top of the current schema (0017 included)', !migErr, migErr);
let again = null; for (const s of statements(mig)) { try { await db.prepare(s).run(); } catch (e) { again = e.message; } }
check('M2 migration 0019 is re-runnable (IF NOT EXISTS throughout)', !again, again);
const tablesBefore = (await db.prepare("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").all()).results.map(r => r.name);
check('M3 migration 0019 is additive: only new basket tables', ['basket_terms', 'basket_artist_events', 'artwork_delivery_offers', 'checkout_baskets', 'basket_lines', 'basket_events'].every(t => tablesBefore.includes(t)));

const call = async (method, path, email, body) => { const r = await S.mf.dispatchFetch(S.url + path, { method, headers: { ...(email ? { 'Cf-Access-Jwt-Assertion': token(email) } : {}), 'X-Studio': '1', 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j, t }; };
const pub = async (method, path, { json = null, form = null, origin = ORIGIN, headers = {}, raw = null } = {}) => { const r = await CW.fetch(ORIGIN + path, { method, redirect: 'manual',
  headers: { ...(json || form ? { 'Content-Type': json ? 'application/json' : 'application/x-www-form-urlencoded', Origin: origin } : {}), ...headers }, body: json ? JSON.stringify(json) : form ? new URLSearchParams(form).toString() : raw ?? undefined });
  const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, t, j, loc: r.headers.get('Location'), h: r.headers }; };
const hook = async e => { const body = JSON.stringify(e); const r = await pub('POST', '/v1/stripe/webhook', { raw: body, headers: { 'Stripe-Signature': sign(body), 'Content-Type': 'application/json' } }); return { s: r.s, j: r.j }; };
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
const DELIVERY = { collection_county: 'Dublin', unpacked_cm: '60 × 50 × 3', packed_cm: '75 × 65 × 12', weight_kg: 6, medium: 'Oil on board', framing: 'Framed, oak', glazing: 'None',
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
check('A7 standing delivery offers recorded per artwork, approved by the artist (destination completed per order)', r.s === 200 && (await q('SELECT * FROM artwork_delivery_offers')).length === 6
  && JSON.parse((await one("SELECT delivery FROM artwork_delivery_offers WHERE artwork_id='wagal1'")).delivery).destination.includes('Republic of Ireland'));
r = await call('GET', '/api/admin/checkout/baskets/eligibility?ids=wagal1,wafnd1,wagal4,wanob1', FOUNDER);
const el0 = Object.fromEntries(r.j.items.map(i => [i.id, i]));
check('A8 founder eligibility view: Gallery Artist work ready; Founding work refused without the separate processing consent (fee Model B); price-on-request and non-basket artists refused',
  el0.wagal1.ok && el0.wagal1.commission_basis === 'gallery_artist_agreement' && !el0.wafnd1.ok && /Model B/.test(el0.wafnd1.why) && /price on request/.test(el0.wagal4.why) && /not ready/.test(el0.wanob1.why), r.j.items);
const PSTAT = (await call('GET', '/api/checkout', FND)).j.processing_statement;
r = await call('POST', '/api/checkout/processing-consent', FND, { accept: true, statement: PSTAT });
r = await call('GET', '/api/admin/checkout/baskets/eligibility?ids=wafnd1', FOUNDER);
check('A9 with the Founding Artist’s own processing consent (and the TEST policy switch), their work is offered at 0% commission (Founding 25 entitlement kept)', r.j.items[0].ok && r.j.items[0].commission_basis === 'founding_enquiry', r.j.items);

console.log('— buyer: the basket page and live preview');
r = await pub('GET', '/basket');
check('B1 the basket page is served with a strict policy (nonce scripts only, no third-party scripts, no framing)', r.s === 200 && /Original works, one checkout/.test(r.t) && /script-src 'nonce-[0-9a-f]{32}'(;| )/.test(r.h.get('Content-Security-Policy'))
  && !/js\.stripe\.com/.test(r.h.get('Content-Security-Policy')) && r.h.get('X-Frame-Options') === 'DENY' && /Test mode/.test(r.t), r.h.get('Content-Security-Policy'));
check('B1a the page carries PlotArt’s identity (Instrument Serif, Hanken Grotesk, anthracite) and is responsive', /Instrument\+Serif/.test(r.t) && /Hanken\+Grotesk/.test(r.t) && /#27282A/.test(r.t) && /@media \(max-width:560px\)/.test(r.t) && /name="viewport"/.test(r.t));
r = await pub('GET', '/api/basket/items?ids=wagal1,wafnd1,wagal4,wanob1,nonexistent');
const it = Object.fromEntries(r.j.items.map(i => [i.id, i]));
check('B2 live preview: price, seller and delivery for eligible works, from the records', it.wagal1.ok && it.wagal1.price_cents === 120000 && it.wagal1.delivery_cents === 4500 && it.wagal1.artist === 'Gale Gallery' && /5–8 working days/.test(it.wagal1.delivery.window)
  && it.wafnd1.ok && it.wafnd1.price_cents === 45000 && r.j.open === true && r.j.terms.doc_id === 'PA-BBT-TEST-01', r.j);
check('B3 ineligible works are refused with a buyer-friendly reason and never priced (price on request; artist not in baskets; unknown)', !it.wagal4.ok && /enquire/i.test(it.wagal4.reason) && !it.wanob1.ok && !it.nonexistent.ok
  && !('price_cents' in it.wagal4) && !/Model B|commission|opted/i.test(JSON.stringify(r.j.items.filter(i => !i.ok))), r.j.items);
check('B4 the gallery (plotnua.ie) may read eligibility cross-origin; nothing else is exposed', r.h.get('Access-Control-Allow-Origin') === 'https://plotnua.ie');

console.log('— buyer: open a basket (two artists, one card entry)');
const BUYER = { name: 'Bríd Buyer', email: 'brid@example.test', address_line1: '7 Harbour Road', address_line2: '', town: 'Kinsale', county: 'Cork', eircode: 'P17 XY12', phone: '+353 21 555 0199' };
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
check('P1 before the card is entered the status page says so; a return from Stripe is never proof of payment', r.s === 200 && /Waiting for your card/.test(r.t));
await shot('3-waiting', `/b/${token1}`);
enterCard(sess1.id, {});
const cBefore = M.calls.length;
r = await hook(evt('checkout.session.completed', { ...M.sessions[sess1.id], setup_intent: M.sessions[sess1.id].setup_intent }));
const B1p = await one('SELECT * FROM checkout_baskets WHERE id = ?', B1.id);
const newCalls = M.calls.slice(cBefore);
const clones = newCalls.filter(c => c.path === '/v1/payment_methods'), auths = newCalls.filter(c => c.path === '/v1/payment_intents' && c.method === 'POST'), caps = newCalls.filter(c => /\/capture$/.test(c.path));
check('P2 a signed platform event completes the card page; the coordinator runs', r.s === 200 && B1p.status === 'paid', { r, status: B1p.status, res: B1p.resolution });
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
check('P12 the status page says paid only now, per artist payment, with each confirmation', /Thank you/.test(r.t) && (r.t.match(/state captured/g) || []).length === 2 && (r.t.match(/Your purchase confirmation from/g) || []).length === 2, r.t.slice(0, 400));
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
check('D4 the buyer is told plainly that nothing was bought and any hold is released', /Not completed/.test(r.t) && /declined/.test(r.t), r.t.slice(0, 600));
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
check('X3 the status page asks the buyer to confirm that one artist’s payment, with a deadline', /Confirm the payment to Fia Founding/.test(r.t) && /otherwise every payment in this basket is cancelled/.test(r.t));
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
check('G4 live mode: no basket text is approved, so no live basket can be opened', Object.keys(LIVE_BASKET_DOCS).length === 0 && (await basketDoc('PA-BBT-TEST-01', true)) === null);
check('G5 only the TEST key was presented to the provider', M.calls.every(c => c.auth === 'Bearer sk_test_mockkey123'));
r = await pub('GET', `/b/${'q'.repeat(48)}`);
check('G6 an unknown basket link reveals nothing', r.s === 404 && !/PA-B-/.test(r.t));

console.log(`\nMULTI-ARTIST BASKET · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
process.exitCode = results.every(Boolean) ? 0 : 1;
} finally {
  if (BR) await BR.close().catch(() => {});
  if (S) await S.mf.dispose();
  rmSync(HERE + FIX, { recursive: true, force: true });
}
