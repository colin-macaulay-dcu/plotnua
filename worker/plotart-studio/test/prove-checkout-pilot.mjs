// PROVE · managed checkout pilot (migration 0016; MANAGED-CHECKOUT-PILOT.md "Required verification before activation").
// Local only: Miniflare D1, the real Studio Worker and the real public checkout Worker, a MOCK Stripe API (every outbound
// call is intercepted; nothing reaches Stripe), synthetic artists, and SYNTHETIC addendum/buyer-terms texts (the real
// texts are not issued). Webhooks are signed here with a test secret exactly as Stripe signs them.
//   node test/prove-checkout-pilot.mjs
import { cpSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { createHash, createHmac } from 'node:crypto';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';

const HERE = new URL('..', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(typeof d === 'string' ? d : JSON.stringify(d)).slice(0, 600)}]` : ''}`); };
const sha = b => createHash('sha256').update(b).digest('hex');
const ago = days => new Date(Date.now() - days * 86400_000).toISOString();

/* A test copy of the Workers carrying SYNTHETIC pilot texts (as prove-hire.mjs does for PA-AFH). */
const FIX = 'test/.checkout-fixture/';
rmSync(HERE + FIX, { recursive: true, force: true });
cpSync(HERE + 'src', HERE + FIX + 'src', { recursive: true });
const ADD = '<!DOCTYPE html><title>TEST ONLY · synthetic payment addendum</title><p>Synthetic text for local tests. Not a PlotArt document.</p>';
const BPT = '<!DOCTYPE html><title>TEST ONLY · synthetic buyer terms</title><p>Synthetic text for local tests. Not a PlotArt document.</p>';
const TERMS = { 'PA-PAY-TEST-01': { title: 'Payment Pilot Addendum (TEST)', kind: 'artist_payment_addendum', html: ADD, html_sha256: sha(ADD) },
  'PA-BPT-TEST-01': { title: 'Buyer Purchase Terms (TEST)', kind: 'buyer_purchase_terms', html: BPT, html_sha256: sha(BPT) } };
writeFileSync(HERE + FIX + 'src/payment-terms.js', `export const PAYMENT_TERMS = ${JSON.stringify(TERMS)};\n`);

/* ---------------------------------------------------------------- mock Stripe (test mode objects only) */
const WHSEC = 'whsec_test_' + 'x'.repeat(24);
const M = { accounts: {}, v2accounts: {}, nextAccountResponsibilities: null, sessions: {}, pis: {}, refunds: [], feeRefunds: [], calls: [], idem: {}, n: 0, failNextExpire: false, nextRefundStatus: null };
const nid = p => `${p}_test_${(++M.n).toString(36).padStart(6, '0')}`;
const flat = body => Object.fromEntries(new URLSearchParams(body || ''));
const ok = o => new Response(JSON.stringify(o), { status: 200, headers: { 'Content-Type': 'application/json' } });
const err = (m, s = 400) => new Response(JSON.stringify({ error: { message: m } }), { status: s, headers: { 'Content-Type': 'application/json' } });
async function stripe(req) {
  const u = new URL(req.url);
  if (u.hostname !== 'stripe.mock') return err('unexpected outbound host ' + u.hostname, 599);
  const body = req.method === 'POST' ? await req.text() : '';
  const v2 = u.pathname.startsWith('/v2/');
  let jb = null; if (v2 && body) { try { jb = JSON.parse(body); } catch { return err('v2 expects JSON', 400); } }
  const f = v2 ? {} : flat(body), acct = req.headers.get('Stripe-Account'), idem = req.headers.get('Idempotency-Key');
  M.calls.push({ method: req.method, path: u.pathname, f, jb, acct, idem, auth: req.headers.get('Authorization'), version: req.headers.get('Stripe-Version'), ctype: req.headers.get('Content-Type'), query: u.search });
  if (v2 && !req.headers.get('Stripe-Version')) return err('v2 requests must include Stripe-Version', 400);
  if (idem && M.idem[idem]) return ok(M.idem[idem]);
  const remember = o => { if (idem) M.idem[idem] = o; return ok(o); };
  let mm;
  // As real Stripe now does for new Connect platforms: v1 account creation is refused (the v1 support setting is off).
  if (u.pathname === '/v1/accounts' && req.method === 'POST') return err('Stripe no longer recommends Accounts v1 for new Connect integrations.', 400);
  if (u.pathname === '/v2/core/accounts' && req.method === 'POST') {
    const id = nid('acct').replace('_test', '');
    const resp = M.nextAccountResponsibilities || jb.defaults.responsibilities; M.nextAccountResponsibilities = null;
    const v2a = { id, object: 'v2.core.account', livemode: false, contact_email: jb.contact_email, dashboard: jb.dashboard, identity: { country: String(jb.identity.country).toUpperCase() },
      defaults: { responsibilities: { ...resp, requirements_collector: 'stripe' } }, configuration: { merchant: { capabilities: { card_payments: { status: 'restricted', status_details: [] } } } },
      requirements: { entries: [{ description: 'individual.verification.document' }] }, metadata: jb.metadata };
    M.v2accounts[id] = v2a;
    M.accounts[id] = { id, object: 'account', livemode: false, charges_enabled: false, payouts_enabled: false, details_submitted: false, country: v2a.identity.country, email: jb.contact_email, requirements: { currently_due: ['individual.verification.document'] } };
    return remember(v2a);
  }
  if (u.pathname === '/v2/core/account_links' && req.method === 'POST' && jb.use_case && jb.use_case.account_onboarding && 'configurations' in jb.use_case.account_onboarding)
    return new Response(JSON.stringify({ error: { type: 'invalid_request_error', code: 'invalid_fields', message: "Some fields in the request were invalid: 'use_case.account_onboarding.configurations: Unknown field.'" } }), { status: 400, headers: { 'Content-Type': 'application/json' } });   // as Stripe answers on 2026-09-30.endive and later
  if (u.pathname === '/v2/core/account_links' && req.method === 'POST') return ok({ object: 'v2.core.account_link', account: jb.account, url: `https://accounts.stripe.test/r/${jb.account}`, use_case: jb.use_case, livemode: false });
  if ((mm = u.pathname.match(/^\/v2\/core\/accounts\/(acct_[\w]+)$/)) && req.method === 'GET') return M.v2accounts[mm[1]] ? ok(M.v2accounts[mm[1]]) : err('no such account', 404);
  if ((mm = u.pathname.match(/^\/v1\/accounts\/(acct_[\w]+)$/))) return M.accounts[mm[1]] ? ok(M.accounts[mm[1]]) : err('no such account', 404);
  if (u.pathname === '/v1/checkout/sessions' && req.method === 'POST' && Object.keys(f).some(k => k.startsWith('payment_method_types'))) return err('Received unknown parameter: payment_method_types', 400);
  if (u.pathname === '/v1/checkout/sessions' && req.method === 'POST') {
    if (!acct) return err('direct charge expected');
    const items = [0, 1].filter(i => f[`line_items[${i}][price_data][unit_amount]`]).map(i => Number(f[`line_items[${i}][price_data][unit_amount]`]));
    const s = { id: nid('cs'), object: 'checkout.session', livemode: false, url: `https://checkout.stripe.test/c/${M.n}`, status: 'open', payment_status: 'unpaid', currency: f.currency,
      amount_total: items.reduce((a, b) => a + b, 0), expires_at: Number(f.expires_at), metadata: { plotart_order: f['metadata[plotart_order]'], quote_version: f['metadata[quote_version]'] },
      _fee: f['payment_intent_data[application_fee_amount]'] === undefined ? null : Number(f['payment_intent_data[application_fee_amount]']), _acct: acct, _items: items, _f: f, payment_intent: null };
    M.sessions[s.id] = s; return remember(s);
  }
  if ((mm = u.pathname.match(/^\/v1\/checkout\/sessions\/(cs_test_\w+)\/expire$/))) {
    const s = M.sessions[mm[1]]; if (!s) return err('no such session', 404);
    if (M.failNextExpire) { M.failNextExpire = false; return err('temporary', 500); }
    if (s.status !== 'open') return err('session is not open'); s.status = 'expired'; return ok(s);
  }
  if ((mm = u.pathname.match(/^\/v1\/checkout\/sessions\/(cs_test_\w+)$/))) return M.sessions[mm[1]] ? ok(M.sessions[mm[1]]) : err('no such session', 404);
  if ((mm = u.pathname.match(/^\/v1\/payment_intents\/(pi_test_\w+)$/))) { const p = M.pis[mm[1]]; return p ? ok({ ...p, latest_charge: { id: p.charge, application_fee: p.fee } }) : err('no such pi', 404); }
  if ((mm = u.pathname.match(/^\/v1\/refunds\/(re_test_\w+)$/)) && req.method === 'GET') { const r = M.refunds.find(x => x.id === mm[1]); return r ? ok(r) : err('no such refund', 404); }
  if (u.pathname === '/v1/refunds') { const st = M.nextRefundStatus || 'succeeded'; M.nextRefundStatus = null;
    const r = { id: nid('re'), object: 'refund', status: st, amount: Number(f.amount), payment_intent: f.payment_intent, livemode: false, metadata: { plotart_refund: f['metadata[plotart_refund]'], plotart_order: f['metadata[plotart_order]'] }, _f: f, _acct: acct }; M.refunds.push(r); return remember(r); }
  if ((mm = u.pathname.match(/^\/v1\/application_fees\/(fee_test_\w+)\/refunds$/))) { const r = { id: nid('fr'), object: 'fee_refund', amount: Number(f.amount), fee: mm[1], livemode: false }; M.feeRefunds.push(r); return remember(r); }
  return err('mock: unhandled ' + req.method + ' ' + u.pathname, 404);
}
/* The buyer pays at Stripe (mock): the session completes, a payment intent, charge and application fee exist. */
function pay(sid) {
  const s = M.sessions[sid]; s.status = 'complete'; s.payment_status = 'paid';
  const pi = nid('pi'); s.payment_intent = pi;
  M.pis[pi] = { id: pi, object: 'payment_intent', livemode: false, amount: s.amount_total, charge: nid('ch'), fee: s._fee ? nid('fee') : null, metadata: s.metadata };
  return s;
}
const sign = (raw, t = Math.floor(Date.now() / 1000), secret = WHSEC) => `t=${t},v1=${createHmac('sha256', secret).update(`${t}.${raw}`).digest('hex')}`;
let EV = 0;
const evt = (type, object, account, extra = {}) => ({ id: `evt_test_${++EV}`, object: 'event', type, livemode: false, created: Math.floor(Date.now() / 1000), account, data: { object }, ...extra });

let S;
try {
console.log('PROVE · managed checkout pilot');
const ORIGIN = 'https://checkout.local';
const ENVV = { CHECKOUT_NOTIFY_EMAIL: 'founder-notify@plotnua.invalid', PARTICIPATION_DELETION: 'on', CHECKOUT_PILOT_ENABLED: 'true', STRIPE_SECRET_KEY: 'sk_test_mockkey123', STRIPE_WEBHOOK_SECRET: WHSEC, STRIPE_API_BASE: 'https://stripe.mock', CHECKOUT_ORIGIN: ORIGIN };
S = await start({ port: 8871, env: ENVV, script: FIX + 'src/index.js', checkout: { script: FIX + 'src/checkout-public.js', env: ENVV }, outbound: stripe });
const { db } = S, CW = S.checkoutWorker;
const call = async (method, path, email, body) => { const r = await S.mf.dispatchFetch(S.url + path, { method, headers: { ...(email ? { 'Cf-Access-Jwt-Assertion': token(email) } : {}), 'X-Studio': '1', 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j, t }; };
const pub = async (method, path, { form = null, origin = ORIGIN, headers = {}, raw = null } = {}) => { const r = await CW.fetch(ORIGIN + path, { method, redirect: 'manual',
  headers: { ...(form ? { 'Content-Type': 'application/x-www-form-urlencoded', Origin: origin } : {}), ...headers }, body: form ? new URLSearchParams(form).toString() : raw ?? undefined });
  return { s: r.status, t: await r.text(), loc: r.headers.get('Location'), h: r.headers }; };
const hook = async (e, { sig = null, raw = null } = {}) => { const body = raw ?? JSON.stringify(e); const r = await pub('POST', '/v1/stripe/webhook', { raw: body, headers: { 'Stripe-Signature': sig ?? sign(body), 'Content-Type': 'application/json' } }); let j = null; try { j = JSON.parse(r.t); } catch { /* */ } return { s: r.s, j }; };
const order = async id => db.prepare('SELECT * FROM checkout_orders WHERE id = ?').bind(id).first();
const q = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results;

// ---- synthetic world
const GAL = 'gal@example.test', FND = 'fnd@example.test', OLD = 'old@example.test', UNK = 'unk@example.test', NOP = 'nop@example.test';
await seedPublished(db, { id: 'agal', slug: 'gal', email: GAL, name: 'Gale Gallery', works: 7, publishedAt: ago(30) });
await seedPublished(db, { id: 'afnd', slug: 'fnd', email: FND, name: 'Fia Founding', works: 2, number: 3, publishedAt: ago(500) });
await seedPublished(db, { id: 'aold', slug: 'old', email: OLD, name: 'Oisin Older', works: 3, number: 4, publishedAt: ago(500) });
await seedPublished(db, { id: 'aunk', slug: 'unk', email: UNK, name: 'Una Unknown', works: 2, publishedAt: ago(30) });
await seedPublished(db, { id: 'anop', slug: 'nop', email: NOP, name: 'Nuala NotIn', works: 1, publishedAt: ago(30) });
await db.prepare("UPDATE artists SET founding = 0 WHERE id IN ('agal','aunk','anop')").run();
await db.prepare("INSERT INTO gallery_positions (position, artist_id, reserved, updated_at) VALUES (1, 'afnd', 0, ?), (2, NULL, 1, ?)").bind(ago(1), ago(1)).run();
// Gale holds the Gallery Artist Agreement (synthetic fingerprints) and the standard 15%
const FAKE = 'a'.repeat(64);
await db.prepare("INSERT INTO agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at) VALUES ('PA-GPIL-2026-11','licence','t','fixed',?,?,'2018-01-01T00:00:00Z',?)").bind(FAKE, FAKE, ago(0)).run().catch(() => {});
await db.prepare("INSERT INTO gallery_agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at) VALUES ('PA-GAA-2026-11','gallery_artist_agreement','t','fixed',?,?,'2018-01-01T00:00:00Z',?)").bind(FAKE, FAKE, ago(0)).run();
await db.prepare(`INSERT INTO gallery_agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, method, statement, created_at) VALUES ('gaa1','ev1','agal','PA-GAA-2026-11',?,?,?,?, 'Gale Gallery','studio_checkbox','test',?)`).bind(FAKE, FAKE, ago(20), GAL, ago(20)).run();
await db.prepare("INSERT INTO artist_terms (artist_id, track, commission_bp, set_by, created_at, updated_at) VALUES ('agal','gallery_artist',1500,?,?,?)").bind(FOUNDER, ago(20), ago(20)).run();
// the enquiry log: introductions as the relay records them (founding fixed at introduction)
const LOG = [['l1', 'PA-E-261101-AAAAAA', 'agal', 10, 0], ['l2', 'PA-E-261102-BBBBBB', 'agal', 9, 0], ['l3', 'PA-E-251101-CCCCCC', 'afnd', 400, 1],
  ['l4', 'PA-E-261103-DDDDDD', 'aold', 5, 0], ['l5', 'PA-E-261104-EEEEEE', 'aunk', 5, 0], ['l6', 'PA-E-261105-FFFFFF', 'agal', 8, 0], ['l7', 'PA-E-261106-GGGGGG', 'agal', 7, 0], ['l8', 'PA-E-261107-HHHHHH', 'anop', 3, 0]];
for (const [id, ref, a, d, f] of LOG) await db.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at) VALUES (?,?,?,?, 'relay', ?,?,?, 'relay', ?)`)
  .bind(id, ref, a, null, ago(d), f, null, ago(d)).run();
// pilot texts installed (as an approved migration would install the issued texts)
for (const [id, t] of Object.entries(TERMS)) await db.prepare('INSERT INTO payment_terms (doc_id, kind, title, html_sha256, effective_at, created_at) VALUES (?,?,?,?,?,?)').bind(id, t.kind, t.title, t.html_sha256, '2018-01-01T00:00:00Z', ago(0)).run();

const snapshotOf = async () => JSON.stringify({ v: await q('SELECT * FROM versions ORDER BY artist_id, version'), pq: await q('SELECT * FROM publish_queue ORDER BY id'),
  gp: await q('SELECT * FROM gallery_positions ORDER BY position'), ar: await q('SELECT * FROM artists ORDER BY id'), aa: await q('SELECT * FROM agreement_acceptances ORDER BY id'),
  gaa: await q('SELECT * FROM gallery_agreement_acceptances ORDER BY id'), at: await q('SELECT * FROM artist_terms ORDER BY artist_id'), el: await q('SELECT * FROM enquiry_log ORDER BY id'),
  en: await q('SELECT * FROM enquiries ORDER BY id'), works: await q('SELECT id, artist_id, slug, title, price_eur, ord, archived, description FROM artworks ORDER BY id') });
const BEFORE = await snapshotOf();

console.log('— opt-in and onboarding (test 4: consent and onboarding gate)');
let r = await call('POST', '/api/admin/checkout/orders', FOUNDER, { artist_id: 'agal', artwork_id: 'wagal1', enquiry_ref: 'PA-E-261101-AAAAAA', buyer_email: 'buyer@example.test' });
check('C1 no order for an artist who has not opted in', r.s === 409 && /opted in/.test(r.j.error), r.j);
r = await call('GET', '/api/checkout', GAL);
check('C2 the artist sees the addendum and its acceptance statement, not enrolled by default', r.j.addendum && r.j.addendum.doc_id === 'PA-PAY-TEST-01' && !r.j.membership.opted_in, r.j);
r = await call('POST', '/api/checkout/opt-in', GAL, { accept: false, doc_id: 'PA-PAY-TEST-01', html_sha256: sha(ADD) });
check('C3 opting in needs the explicit tick', r.s === 400);
r = await call('POST', '/api/checkout/opt-in', GAL, { accept: true, doc_id: 'PA-PAY-TEST-01', html_sha256: 'b'.repeat(64) });
check('C4 a different text fingerprint is refused', r.s === 400);
for (const e of [GAL, FND, OLD, UNK]) { r = await call('POST', '/api/checkout/opt-in', e, { accept: true, doc_id: 'PA-PAY-TEST-01', html_sha256: sha(ADD) }); }
check('C5 artists opt in themselves (append-only record with statement, version and fingerprint)', (await q("SELECT * FROM payment_pilot_events WHERE kind='opted_in'")).length === 4
  && (await q("SELECT * FROM payment_pilot_events WHERE artist_id='agal'"))[0].doc_sha256 === sha(ADD));
check('C6 opt-in records cannot be edited or deleted', !!(await db.prepare("UPDATE payment_pilot_events SET kind='left'").run().catch(e => e)).message && !!(await db.prepare('DELETE FROM payment_pilot_events').run().catch(e => e)).message);
r = await call('POST', '/api/checkout/onboarding', GAL, { country: 'IE' });
const ACCT = (await db.prepare("SELECT account_id FROM payment_accounts WHERE artist_id='agal'").first()).account_id;
const accCall = M.calls.find(c => c.path === '/v2/core/accounts');
const linkCall = M.calls.find(c => c.path === '/v2/core/account_links');
check('C7 Stripe-hosted onboarding (Accounts v2): the artist’s own account, artist pays fees, Stripe carries losses, full Dashboard',
  r.s === 200 && /accounts\.stripe\.test/.test(r.j.url) && accCall && accCall.jb.defaults.responsibilities.fees_collector === 'stripe' && accCall.jb.defaults.responsibilities.losses_collector === 'stripe'
  && accCall.jb.dashboard === 'full' && accCall.jb.configuration.merchant.capabilities.card_payments.requested === true && accCall.ctype === 'application/json' && /^\d{4}-\d{2}-\d{2}\.\w+$/.test(accCall.version || ''), accCall);
check('C7a onboarding link is an Account Link v2 in the endive shape (no configurations field); no v1 account creation is attempted',
  linkCall && linkCall.jb.use_case.type === 'account_onboarding' && !('configurations' in linkCall.jb.use_case.account_onboarding) && linkCall.jb.use_case.account_onboarding.return_url && linkCall.jb.use_case.account_onboarding.refresh_url && !M.calls.some(c => c.path === '/v1/accounts' && c.method === 'POST'), linkCall);
check('C7b every request names its API version (v2 and v1 both pinned, independent of the account default)', M.calls.every(c => /^\d{4}-\d{2}-\d{2}\.\w+$/.test(c.version || '')));
check('C8 only a TEST secret key was presented to the provider', M.calls.every(c => c.auth === 'Bearer sk_test_mockkey123'));
for (const [aid, e] of [['afnd', FND], ['aold', OLD], ['aunk', UNK]]) await call('POST', '/api/checkout/onboarding', e, { country: 'IE' });
r = await call('POST', '/api/admin/checkout/accounts/agal/refresh', FOUNDER, {});
const refreshCalls = M.calls.slice(-2).map(c => c.method + ' ' + c.path);
check('C7c a refresh re-reads the configuration (v2) and the charge status (v1) from Stripe', r.s === 200 && refreshCalls[0] === `GET /v2/core/accounts/${ACCT}` && refreshCalls[1] === `GET /v1/accounts/${ACCT}`
  && /include%5B0%5D|include\[0\]/.test(M.calls.at(-2).query), { status: r.s, refreshCalls });
M.v2accounts[ACCT].defaults.responsibilities.losses_collector = 'application';
r = await call('POST', '/api/admin/checkout/accounts/agal/refresh', FOUNDER, {});
check('C7d an account Stripe reports with a different configuration is refused on refresh', r.s === 409 && /losses_collector/.test(JSON.stringify(r.j)), r);
M.v2accounts[ACCT].defaults.responsibilities.losses_collector = 'stripe';
// a new account that Stripe returns with the platform liable for losses is never stored
const AUNK_ACCT = (await db.prepare("SELECT account_id FROM payment_accounts WHERE artist_id='aunk'").first()).account_id;
await db.prepare("DELETE FROM payment_accounts WHERE artist_id='aunk'").run();
for (const k of Object.keys(M.idem)) if (k.startsWith('plotart-acct-v2-aunk')) delete M.idem[k];
M.nextAccountResponsibilities = { fees_collector: 'application', losses_collector: 'application' };
r = await call('POST', '/api/checkout/onboarding', UNK, { country: 'IE' });
check('C7e a newly created account with the wrong configuration is refused and not recorded', r.s === 502 && !(await db.prepare("SELECT 1 FROM payment_accounts WHERE artist_id='aunk'").first()), r);
await db.prepare("INSERT INTO payment_accounts (artist_id, account_id, country, created_at, updated_at) VALUES ('aunk', ?, 'IE', ?, ?)").bind(AUNK_ACCT, new Date().toISOString(), new Date().toISOString()).run();

console.log('— commission entitlement (tests 1–4)');
const DELIVERY = { collection_county: 'Dublin', destination: 'Cork, Ireland', unpacked_cm: '60 × 50 × 3', packed_cm: '75 × 65 × 12', weight_kg: 6, medium: 'Oil on board', framing: 'Framed, oak', glazing: 'None',
  condition: 'Excellent; small studio mark on reverse', access_notes: null, organiser: 'artist', packer: 'artist', transport_booker: 'artist', transport_contracting_party: 'artist', transport_payer: 'artist',
  transporter_name: 'Synthetic Art Couriers', installation: 'not_applicable', import_costs: 'not_applicable', cover_type: 'transit_insurance', cover_provider: 'Synthetic Underwriting (SIMULATED test cover)', covered_value_cents: 100000,
  insured_party: 'transporter', cover_confirmation_ref: 'SIM-COVER-0001', cover_confirmed_by: 'Synthetic Underwriting', cover_confirmed_on: '2026-11-16',
  valuation_basis: 'Agreed sale price', excess_cents: 5000, exclusions: 'Inherent vice', cover_period: 'Collection to signed delivery', claims_contact: 'claims@example.test', delivery_window: '5–8 working days',
  tracking: 'Tracked, signature on delivery', signed_receipt: true, condition_photos: true, return_route: 'Same courier; return cost quoted on request', shipment_confirmation_ref: 'SAC-Q-1001', shipment_confirmed_by: 'Synthetic Art Couriers', shipment_confirmed_on: '2026-11-16' };
async function makeOrder(artist_id, artwork_id, enquiry_ref, artwork_cents = 100000, delivery_cents = 7500, buyer = 'buyer@example.test', delivery = DELIVERY) {
  const c = await call('POST', '/api/admin/checkout/orders', FOUNDER, { artist_id, artwork_id, enquiry_ref, buyer_email: buyer });
  if (c.s !== 200) return c;
  const id = c.j.order.id;
  const u = await call('PUT', `/api/admin/checkout/orders/${id}`, FOUNDER, { artwork_cents, delivery_cents, delivery });
  return u.s === 200 ? { s: 200, id } : u;
}
const o1 = await makeOrder('agal', 'wagal1', 'PA-E-261101-AAAAAA');
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/send`, FOUNDER, {});
check('T1 non-founding artist with accepted terms: 15% of the artwork only (EUR 1,000 → EUR 150), delivery excluded',
  r.s === 200 && r.j.order.commission_bp === 1500 && r.j.order.commission_cents === 15000 && r.j.order.total_cents === 107500 && r.j.order.artist_artwork_cents === 85000 && r.j.order.commission_basis === 'gallery_artist_agreement', r.j);
const of = await makeOrder('afnd', 'wafnd1', 'PA-E-251101-CCCCCC');
r = await call('POST', `/api/admin/checkout/orders/${of.id}/send`, FOUNDER, {});
check('T2 an enquiry from the founding year, completed 400 days later: 0% commission, permanently', r.s === 200 && r.j.order.commission_cents === 0 && r.j.order.commission_basis === 'founding_enquiry', r.j);
const oo = await makeOrder('aold', 'waold1', 'PA-E-261103-DDDDDD');
r = await call('POST', `/api/admin/checkout/orders/${oo.id}/send`, FOUNDER, {});
check('T3 a Founding Artist after the founding year with no accepted commission terms: 15% is NEVER inferred (0%)', r.s === 200 && r.j.order.commission_bp === 0 && r.j.order.commission_basis === 'founding_artist_no_commission_terms', r.j);
console.log('— separate consent to the processing charge on commission-free orders (Founding Artists keep direct payment)');
let rpc = await call('GET', '/api/checkout', FND);
check('PC0 a Founding Artist is told direct payment stays their normal route, and is not asked to consent by joining', /normal route/.test(rpc.j.direct_payment_note) && rpc.j.membership.processing_consent === false);
rpc = await call('POST', `/api/checkout/orders/${of.id}/approve`, FND, { quote_version: (await order(of.id)).quote_version, confirm: { available: true, location: true, condition: true, framing: true, dimensions: true, packing_and_handover: true } });
check('PC1 a commission-free order cannot be approved without the separate processing-charge consent', rpc.s === 409 && /separate consent/.test(rpc.j.error), rpc.j);
rpc = await call('POST', '/api/checkout/processing-consent', FND, { accept: true, statement: 'something else' });
check('PC2 the consent must be to the exact statement shown', rpc.s === 400);
const PSTAT = (await call('GET', '/api/checkout', FND)).j.processing_statement;
for (const e of [FND, OLD]) rpc = await call('POST', '/api/checkout/processing-consent', e, { accept: true, statement: PSTAT });
check('PC3 consent is recorded separately from the addendum acceptance, with its statement', rpc.s === 200 && rpc.j.membership.processing_consent === true
  && (await q("SELECT * FROM payment_pilot_events WHERE kind='processing_consent'")).length === 2 && (await q("SELECT * FROM payment_pilot_events WHERE kind='processing_consent' AND doc_id IS NOT NULL")).length === 0);
const ALLC = { available: true, location: true, condition: true, framing: true, dimensions: true, packing_and_handover: true };
rpc = await call('POST', `/api/checkout/orders/${of.id}/approve`, FND, { quote_version: (await order(of.id)).quote_version, confirm: ALLC });
check('PC4 with consent the commission-free order can be approved', rpc.s === 200, rpc.j);
rpc = await call('POST', '/api/checkout/processing-consent/withdraw', FND, {});
check('PC5 withdrawing consent cancels the artist’s unpaid commission-free quotes', rpc.s === 200 && rpc.j.cancelled.includes((await order(of.id)).reference) && (await order(of.id)).status === 'cancelled' && !rpc.j.membership.processing_consent);
check('PC6 a Gallery Artist on 15% is never asked for this consent', !(await q("SELECT * FROM payment_pilot_events WHERE artist_id='agal' AND kind LIKE 'processing%'")).length);
const ou = await makeOrder('aunk', 'waunk1', 'PA-E-261104-EEEEEE');
r = await call('POST', `/api/admin/checkout/orders/${ou.id}/send`, FOUNDER, {});
check('T4a a non-founding artist without accepted commission terms: entitlement unknown, blocked', r.s === 409 && /unknown/i.test(r.j.error), r.j);
r = await call('POST', '/api/admin/checkout/orders', FOUNDER, { artist_id: 'agal', artwork_id: 'wagal1', enquiry_ref: 'PA-E-999999-ZZZZZZ', buyer_email: 'b@example.test' });
check('T4b no logged introduction for the reference: blocked', r.s === 409 && /logged/.test(r.j.error), r.j);

console.log('— transit insurance required (initial pilot)');
r = await call('PUT', `/api/admin/checkout/orders/${o1.id}`, FOUNDER, { delivery: { ...DELIVERY, cover_type: 'carrier_limited_liability' } });
check('V1 carrier’s limited liability is refused as cover', r.s === 409 && /cover type/.test(r.j.error), r.j);
r = await call('PUT', `/api/admin/checkout/orders/${o1.id}`, FOUNDER, { delivery: { ...DELIVERY, cover_type: 'none', covered_value_cents: 0 } });
check('V2 no cover is refused', r.s === 409, r.j);
const { cover_confirmation_ref: _cr, ...noRef } = DELIVERY;
r = await call('PUT', `/api/admin/checkout/orders/${o1.id}`, FOUNDER, { delivery: noRef });
check('V3 cover without a shipment-specific confirmation reference is refused', r.s === 409 && /confirmation ref/.test(r.j.error), r.j);
const ov = await makeOrder('agal', 'wagal7', 'PA-E-261101-AAAAAA', 120000, 7500, 'v@example.test');
r = await call('POST', `/api/admin/checkout/orders/${ov.id}/send`, FOUNDER, {});
check('V4 cover below the artwork price is refused before the artist is asked', r.s === 409 && /at least the artwork price/.test(r.j.error), r.j);
await call('POST', `/api/admin/checkout/orders/${ov.id}/cancel`, FOUNDER, { reason: 'test' });
check('V5 the earlier valid quote is untouched by refused edits', (await order(o1.id)).status === 'awaiting_artist' && JSON.parse((await order(o1.id)).delivery).cover_type === 'transit_insurance');

console.log('— artist approval and quote');
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/issue`, FOUNDER, { days: 3, linked_check_confirmed: true });
check('T4c the quote cannot be issued before the artist approves it', r.s === 409 && /approved/.test(r.j.error), r.j);
r = await call('POST', `/api/checkout/orders/${o1.id}/approve`, FND, { quote_version: 2, confirm: {} });
check('T12a an artist cannot see or approve another artist’s order', r.s === 404);
r = await call('GET', `/api/checkout/orders/${o1.id}`, FND);
check('T12b an artist cannot read another artist’s order', r.s === 404);
r = await call('GET', '/api/admin/checkout', GAL);
check('T12c the founder desk is refused to artists', r.s === 403);
const v1 = (await order(o1.id)).quote_version;
r = await call('POST', `/api/checkout/orders/${o1.id}/approve`, GAL, { quote_version: v1, confirm: { available: true, location: true } });
check('A1 approval needs every shipment confirmation (availability, location, condition, framing, dimensions, packing)', r.s === 400 && /condition/.test(r.j.error), r.j);
const ALL = { available: true, location: true, condition: true, framing: true, dimensions: true, packing_and_handover: true };
r = await call('POST', `/api/checkout/orders/${o1.id}/approve`, GAL, { quote_version: v1 - 1, confirm: ALL });
check('A2 approving a stale quote version is refused', r.s === 409);
r = await call('POST', `/api/checkout/orders/${o1.id}/approve`, GAL, { quote_version: v1, confirm: ALL });
check('A3 the artist approves the exact quote version', r.s === 200 && r.j.order.artist_approved_version === v1, r.j);
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/issue`, FOUNDER, { days: 3, linked_check_confirmed: true });
check('T4d an artist whose Stripe onboarding is incomplete cannot be quoted', r.s === 409 && /onboarding/.test(r.j.error), r.j);
// Stripe tells us (signed account.updated) that onboarding is complete
for (const a of Object.values(M.accounts)) { a.charges_enabled = true; a.payouts_enabled = true; a.details_submitted = true; a.requirements = { currently_due: [] }; }
for (const a of Object.values(M.accounts)) await hook(evt('account.updated', a, a.id));
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/issue`, FOUNDER, { days: 3 });
check('K1 a quote needs the founder’s linked-purchases confirmation', r.s === 400 && /linked/.test(r.j.error), r.j);
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/issue`, FOUNDER, { days: 3, linked_check_confirmed: true });
const LINK1 = r.j && r.j.buyer_link, T1 = LINK1 && LINK1.split('/q/')[1];
check('Q1 quote issued with a one-time buyer link (token stored hashed only)', r.s === 200 && /^https:\/\/checkout\.local\/q\/[0-9a-z]{48}$/.test(LINK1)
  && (await order(o1.id)).buyer_token_hash === sha(T1) && !JSON.stringify(await order(o1.id)).includes(T1), r.j);
check('Q2 the seller snapshot names the artist as seller and PlotArt as introducer', /Seller \(the artist\)/.test(r.j.order.seller.role) && /not the seller/.test(r.j.order.seller.platform));

console.log('— buyer page and hosted checkout (test 13)');
let pg = await pub('GET', `/q/${T1}`);
check('B1 the buyer sees seller, artwork, delivery, cover and total before paying', pg.s === 200 && pg.t.includes('Gale Gallery') && pg.t.includes('€1,000.00') && pg.t.includes('€75.00') && pg.t.includes('€1,075.00')
  && pg.t.includes('Synthetic Underwriting') && pg.t.includes('not escrow') && pg.t.includes('Test mode') && !pg.t.includes(GAL), pg.t.slice(0, 300));
check('B2 the buyer page never shows the commission or the artist’s address', !/15%|150\.00|commission/i.test(pg.t) && !pg.t.includes(GAL), (pg.t.match(/.{60}(15%|150\.00|commission).{60}/i) || [])[0]);
check('B3 another token reaches nothing', (await pub('GET', '/q/' + 'z'.repeat(48))).s === 404);
pg = await pub('POST', `/q/${T1}/pay`, { form: {} });
check('B4 paying needs the purchase terms accepted', pg.s === 400 && /purchase terms/.test(pg.t));
pg = await pub('POST', `/q/${T1}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' }, origin: 'https://evil.example' });
check('B5 a cross-site form post is refused', pg.s === 403);
pg = await pub('POST', `/q/${T1}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01', artwork_cents: '1', commission: '0' } });
const sess1 = Object.values(M.sessions).at(-1);
check('B6 hosted checkout opens on the ARTIST’s account (direct charge) with server-side amounts only', pg.s === 303 && pg.loc === sess1.url && sess1._acct === ACCT
  && sess1._items.join() === '100000,7500' && sess1._fee === 15000 && sess1.amount_total === 107500 && sess1._f.currency === 'eur', sess1);
check('B7 the session lasts at least 30 minutes and the work is reserved with an explicit expiry beyond it', (() => { const res = 0; return true; })()
  && sess1.expires_at * 1000 - Date.now() >= 29.5 * 60_000 && (await db.prepare('SELECT * FROM artwork_reservations WHERE artwork_id = ?').bind('wagal1').first()).expires_at > new Date(sess1.expires_at * 1000).toISOString());
pg = await pub('POST', `/q/${T1}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } });
check('B8 a double click reopens the SAME checkout, not a second one', pg.s === 303 && pg.loc === sess1.url && (await q('SELECT * FROM checkout_sessions WHERE order_id = ?', o1.id)).length === 1);
pg = await pub('GET', `/q/${T1}/return?result=success`);
check('T14a returning from Stripe is never proof of payment: still unpaid, work not sold', /confirming/.test(pg.t) && (await order(o1.id)).payment_status === 'open'
  && (await db.prepare("SELECT availability FROM artworks WHERE id='wagal1'").first()).availability === 'available');

console.log('— verified events (test 7)');
pay(sess1.id);
const done1 = evt('checkout.session.completed', M.sessions[sess1.id], ACCT);
let h = await hook(done1, { sig: sign(JSON.stringify(done1), Math.floor(Date.now() / 1000), 'whsec_wrongsecret0000000000') });
check('T7a a forged event (wrong secret) is refused and changes nothing', h.s === 400 && (await order(o1.id)).payment_status === 'open' && !(await q('SELECT * FROM payment_events WHERE event_id = ?', done1.id)).length);
h = await hook(done1, { sig: sign(JSON.stringify(done1), Math.floor(Date.now() / 1000) - 3600) });
check('T7b a replayed event outside the 5-minute tolerance is refused', h.s === 400);
h = await hook(done1, { raw: JSON.stringify({ ...done1, data: { object: { ...done1.data.object, amount_total: 1 } } }), sig: sign(JSON.stringify(done1)) });
check('T7c a tampered body fails its signature', h.s === 400);
h = await hook(done1);
let O1 = await order(o1.id);
check('T7d a signed completion marks the order paid and the work sold, atomically', h.s === 200 && O1.status === 'paid' && O1.payment_status === 'paid' && O1.amount_received_cents === 107500
  && (await db.prepare("SELECT availability FROM artworks WHERE id='wagal1'").first()).availability === 'sold' && (await q("SELECT * FROM artwork_sales WHERE artwork_id='wagal1'")).length === 1
  && !(await q("SELECT * FROM artwork_reservations WHERE artwork_id='wagal1'")).length, { h, O1 });
const L1 = await q('SELECT kind, amount_cents FROM order_ledger WHERE order_id = ? ORDER BY kind', o1.id);
check('T7e the ledger books charge 1,075, commission 150, artist artwork 850, delivery allocation 75',
  JSON.stringify(L1) === JSON.stringify([{ kind: 'artist_artwork', amount_cents: 85000 }, { kind: 'charge', amount_cents: 107500 }, { kind: 'commission', amount_cents: 15000 }, { kind: 'delivery_allocation', amount_cents: 7500 }]), L1);
h = await hook(done1);
check('T7f the same event delivered again is recognised and not re-applied', h.s === 200 && h.j.duplicate && (await q('SELECT * FROM order_ledger WHERE order_id = ?', o1.id)).length === 4);
const dup2 = { ...done1, id: `evt_test_${++EV}` };   // a different event id carrying the same completion (provider retry semantics differ)
h = await hook(dup2);
check('T7g a second event for the same payment books nothing twice', h.s === 200 && (await q('SELECT * FROM order_ledger WHERE order_id = ?', o1.id)).length === 4 && (await q("SELECT * FROM artwork_sales WHERE artwork_id='wagal1'")).length === 1);
h = await hook(evt('checkout.session.expired', { ...M.sessions[sess1.id], status: 'expired' }, ACCT));
check('T7h an expiry arriving after the completion (out of order) is ignored', h.s === 200 && (await order(o1.id)).status === 'paid');
h = await hook(evt('checkout.session.completed', { ...M.sessions[sess1.id] }, ACCT, { livemode: true }));
check('T15a a live-mode event is refused by the test-mode pilot', h.s === 400);
pg = await pub('GET', `/q/${T1}/return?result=success`);
check('B9 the return page reports payment only once the verified event has arrived', /has been confirmed/.test(pg.t));
pg = await pub('POST', `/q/${T1}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } });
check('B10 a paid quote cannot be paid again', pg.s === 409);

console.log('— linked purchases (EUR 10,000 is not avoided by splitting)');
const ok1 = await makeOrder('agal', 'wagal5', 'PA-E-261102-BBBBBB', 600000, 0, 'big@example.test', { ...DELIVERY, covered_value_cents: 600000 });
const ok2 = await makeOrder('agal', 'wagal6', 'PA-E-261105-FFFFFF', 450000, 0, 'BIG@Example.test', { ...DELIVERY, covered_value_cents: 450000 });
for (const x of [ok1, ok2]) { await call('POST', `/api/admin/checkout/orders/${x.id}/send`, FOUNDER, {}); await call('POST', `/api/checkout/orders/${x.id}/approve`, GAL, { quote_version: (await order(x.id)).quote_version, confirm: ALL }); }
r = await call('POST', `/api/admin/checkout/orders/${ok1.id}/issue`, FOUNDER, { days: 2, linked_check_confirmed: true });
check('K2 a single EUR 6,000 order is quoted, with the linked-purchase check recorded', r.s === 200 && JSON.parse((await order(ok1.id)).linked_order_check).founder_confirmed_no_other_link === true && /not an AML assessment/i.test((await order(ok1.id)).linked_order_check), r.j);
const TK1 = r.j.buyer_link.split('/q/')[1];
r = await call('POST', `/api/admin/checkout/orders/${ok2.id}/issue`, FOUNDER, { days: 2, linked_check_confirmed: true });
check('K3 a second order by the same buyer (any letter case) taking the total to EUR 10,500 is refused', r.s === 409 && /10,000/.test(r.j.error) && /10500\.00/.test(r.j.error), r.j);
await call('POST', `/api/admin/checkout/orders/${ok1.id}/cancel`, FOUNDER, { reason: 'test' });
r = await call('POST', `/api/admin/checkout/orders/${ok2.id}/issue`, FOUNDER, { days: 2, linked_check_confirmed: true });
check('K4 an unpaid, cancelled order no longer counts', r.s === 200, r.j);
await call('POST', `/api/admin/checkout/orders/${ok2.id}/cancel`, FOUNDER, { reason: 'test' });
check('K5 the cancelled quote cannot be paid', (await pub('POST', `/q/${TK1}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } })).s === 409);

console.log('— two buyers, one original (test 6)');
const oa = await makeOrder('agal', 'wagal2', 'PA-E-261102-BBBBBB', 50000, 0, 'a@example.test'), ob = await makeOrder('agal', 'wagal2', 'PA-E-261105-FFFFFF', 50000, 0, 'b@example.test');
const prep = async id => { await call('POST', `/api/admin/checkout/orders/${id}/send`, FOUNDER, {}); await call('POST', `/api/checkout/orders/${id}/approve`, GAL, { quote_version: (await order(id)).quote_version, confirm: ALL });
  const x = await call('POST', `/api/admin/checkout/orders/${id}/issue`, FOUNDER, { days: 2, linked_check_confirmed: true }); return x.j.buyer_link.split('/q/')[1]; };
const TA = await prep(oa.id), TB = await prep(ob.id);
const [pa, pb] = await Promise.all([pub('POST', `/q/${TA}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } }), pub('POST', `/q/${TB}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } })]);
check('T6a two buyers at the same moment: exactly one checkout opens', [pa.s, pb.s].sort().join() === '303,409', [pa.s, pb.s]);
const [first, second, TF, TS] = pa.s === 303 ? [oa, ob, TA, TB] : [ob, oa, TB, TA];
const sA = (await q("SELECT * FROM checkout_sessions WHERE order_id = ? AND status='open'", first.id))[0];
h = await hook(evt('checkout.session.expired', { ...M.sessions[sA.id], status: 'expired' }, ACCT));
check('T8a an abandoned checkout releases the reservation and returns the quote to payable', (await order(first.id)).status === 'quoted' && !(await q("SELECT * FROM artwork_reservations WHERE artwork_id='wagal2'")).length);
pg = await pub('POST', `/q/${TS}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } });
const sB = (await q("SELECT * FROM checkout_sessions WHERE order_id = ? AND status='open'", second.id))[0];
check('T6b the other buyer can then open checkout', pg.s === 303 && !!sB);
pay(sB.id); await hook(evt('checkout.session.completed', M.sessions[sB.id], ACCT));
M.sessions[sA.id].status = 'open'; pay(sA.id);   // the first buyer's payment completes late, at the provider, after their session had expired here
h = await hook(evt('checkout.session.completed', M.sessions[sA.id], ACCT));
const FA = await order(first.id);
check('T6c a delayed payment for an already-sold original is never a second sale: flagged for refund', h.s === 200 && FA.status === 'refund_pending' && /already sold/.test(FA.needs_resolution)
  && (await q("SELECT * FROM artwork_sales WHERE artwork_id='wagal2' AND released_at IS NULL")).length === 1 && (await order(second.id)).status === 'paid', FA);
check('T6d the database itself refuses a second active sale of one original', /UNIQUE/.test((await db.prepare("INSERT INTO artwork_sales (order_id, artwork_id, sold_at) VALUES (?, 'wagal2', ?)").bind(first.id, ago(0)).run().catch(e => e)).message));
pg = await pub('POST', `/q/${TF}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } });
check('T6e and the sold work cannot be checked out again', pg.s === 409, [pg.s, pg.t.slice(-600)]);

console.log('— revised and expired quotes (test 5), failure (tests 8, 14)');
const oc = await makeOrder('agal', 'wagal3', 'PA-E-261106-GGGGGG', 80000, 5000, 'c@example.test');
const TC = await prep(oc.id);
await pub('POST', `/q/${TC}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } });
const sC = (await q("SELECT * FROM checkout_sessions WHERE order_id = ? AND status='open'", oc.id))[0];
r = await call('PUT', `/api/admin/checkout/orders/${oc.id}`, FOUNDER, { artwork_cents: 90000 });
const OC = await order(oc.id);
check('T5a revising a quote expires the open checkout at the provider first, releases the work and needs fresh artist approval',
  r.s === 200 && M.sessions[sC.id].status === 'expired' && (await db.prepare('SELECT status FROM checkout_sessions WHERE id = ?').bind(sC.id).first()).status === 'superseded'
  && OC.status === 'draft' && OC.artist_approved_version === null && OC.buyer_token_hash === null && !(await q("SELECT * FROM artwork_reservations WHERE artwork_id='wagal3'")).length, OC);
check('T5b the old buyer link no longer opens anything', (await pub('GET', `/q/${TC}`)).s === 404 && (await pub('POST', `/q/${TC}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } })).s === 404);
M.sessions[sC.id].status = 'open'; pay(sC.id);   // the stale amount is somehow paid at the provider anyway
h = await hook(evt('checkout.session.completed', M.sessions[sC.id], ACCT));
const OC2 = await order(oc.id);
check('T5c a payment of the stale amount never completes a sale: flagged, work not sold', OC2.status === 'refund_pending' && /amount|version/.test(OC2.needs_resolution)
  && (await db.prepare("SELECT availability FROM artworks WHERE id='wagal3'").first()).availability === 'available' && !(await q("SELECT * FROM artwork_sales WHERE artwork_id='wagal3'")).length, OC2);
const od = await makeOrder('agal', 'wagal4', 'PA-E-261106-GGGGGG', 60000, 0, 'd@example.test');
const TD = await prep(od.id);
await db.prepare('UPDATE checkout_orders SET quote_expires_at = ? WHERE id = ?').bind(ago(0.01), od.id).run();
pg = await pub('POST', `/q/${TD}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } });
check('T5d an expired quote cannot be paid', pg.s === 410 && (await order(od.id)).status === 'expired');
r = await call('PUT', `/api/admin/checkout/orders/${od.id}`, FOUNDER, { delivery_cents: 0 });
await call('POST', `/api/admin/checkout/orders/${od.id}/send`, FOUNDER, {});
await call('POST', `/api/checkout/orders/${od.id}/approve`, GAL, { quote_version: (await order(od.id)).quote_version, confirm: ALL });
const TD2 = (await call('POST', `/api/admin/checkout/orders/${od.id}/issue`, FOUNDER, { days: 1, linked_check_confirmed: true })).j.buyer_link.split('/q/')[1];
await pub('POST', `/q/${TD2}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } });
const sD = (await q("SELECT * FROM checkout_sessions WHERE order_id = ? AND status='open'", od.id))[0];
h = await hook(evt('checkout.session.async_payment_failed', { ...M.sessions[sD.id], payment_status: 'unpaid' }, ACCT));
const OD = await order(od.id);
check('T8b/T14b a declined payment releases the reservation and never marks the work sold', OD.status === 'payment_failed' && !(await q("SELECT * FROM artwork_reservations WHERE artwork_id='wagal4'")).length
  && (await db.prepare("SELECT availability FROM artworks WHERE id='wagal4'").first()).availability === 'available');
await db.prepare("UPDATE artworks SET availability = 'sold' WHERE id = 'wagal4'").run();   // the artist records an outside sale in Studio
pg = await pub('POST', `/q/${TD2}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } });
check('T14c a work the artist has marked sold elsewhere cannot be checked out', pg.s === 409 && /no longer available/.test(pg.t));
await db.prepare("UPDATE artworks SET availability = 'available' WHERE id = 'wagal4'").run();

console.log('— refunds (test 9), including a refund held at Stripe for want of balance');
let fees = M.feeRefunds.length;
M.nextRefundStatus = 'pending';   // as Stripe does when the artist's AVAILABLE balance cannot cover a card refund (e.g. after payout)
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/refund`, FOUNDER, { artwork_cents: 50000, delivery_cents: 0, reason: 'Agreed partial refund for a frame mark' });
const rf1 = M.refunds.at(-1);
check('T9a partial artwork refund: created on the artist’s account, application fee NOT refunded by Stripe’s proportional rule',
  r.s === 200 && rf1._acct === ACCT && rf1.amount === 50000 && rf1._f.refund_application_fee === 'false', rf1);
check('R1 a refund pending at Stripe books nothing and returns no commission yet, and is flagged',
  !(await q("SELECT * FROM order_ledger WHERE order_id = ? AND kind = 'artwork_refund'", o1.id)).length && M.feeRefunds.length === fees && /pending at Stripe/.test((await order(o1.id)).needs_resolution));
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/refund`, FOUNDER, { artwork_cents: 50001, delivery_cents: 0, reason: 'too much' });
check('R2 a pending refund counts against what can still be refunded', r.s === 409);
check('R1b the artist and the founder are told at once, with the funding steps', (await q("SELECT * FROM order_events WHERE order_id = ? AND action = 'notified_refund_pending'", o1.id)).length === 1
  && (await q("SELECT * FROM mail_capture WHERE subject LIKE '%refund_pending%' AND (to_addr = ? OR to_addr = 'founder-notify@plotnua.invalid')", GAL)).length === 2
  && (await q("SELECT body FROM mail_capture WHERE to_addr = ?", GAL))[0].body.includes('Add to balance'));
check('R1c the founder desk lists the pending refund with its days and Stripe’s 45-day date', (await call('GET', '/api/admin/checkout', FOUNDER)).j.pending_refunds.some(x => x.order_id === o1.id && x.days_pending === 0 && x.stripe_fails_it_by));
check('R1d the artist sees it with what to do', (await call('GET', '/api/checkout', GAL)).j.pending_refunds[0].what_to_do.length === 4);
h = await hook(evt('refund.updated', { ...rf1, status: 'succeeded' }, ACCT));
check('R3 when Stripe confirms the refund, it is booked and PlotArt returns exactly GAA 9.2 commission (€150 × €500 kept / €1,000 → €75)',
  h.s === 200 && M.feeRefunds.length === fees + 1 && M.feeRefunds.at(-1).amount === 7500 && (await q("SELECT * FROM order_ledger WHERE order_id = ? AND kind = 'artwork_refund'", o1.id)).length === 1 && !(await order(o1.id)).needs_resolution, h);
h = await hook(evt('refund.updated', { ...rf1, status: 'succeeded' }, ACCT));
check('R4 the same confirmation again returns nothing twice', M.feeRefunds.length === fees + 1 && (await q("SELECT * FROM order_ledger WHERE order_id = ? AND kind = 'commission_refund'", o1.id)).length === 1);
check('T9b order back to paid, partially refunded', (await order(o1.id)).status === 'paid' && (await order(o1.id)).payment_status === 'partially_refunded');
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/refund`, FOUNDER, { artwork_cents: 0, delivery_cents: 7500, reason: 'Delivery not used: buyer collected' });
check('T9c a delivery refund moves no commission', r.s === 200 && M.feeRefunds.length === fees + 1);
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/refund`, FOUNDER, { artwork_cents: 60000, delivery_cents: 0, reason: 'too much' });
check('T9d a refund above the amount still paid is refused', r.s === 409);
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/refund`, FOUNDER, { artwork_cents: 50000, delivery_cents: 0, reason: 'Returned in full' });
O1 = await order(o1.id);
const fin = await db.prepare(`SELECT SUM(CASE WHEN kind='commission' THEN amount_cents END) + SUM(CASE WHEN kind='commission_refund' THEN amount_cents ELSE 0 END) AS netfee,
  SUM(CASE WHEN kind IN ('charge','artwork_refund','delivery_refund') THEN amount_cents ELSE 0 END) AS netpaid FROM order_ledger WHERE order_id = ?`).bind(o1.id).first();
check('T9e full refund reconciles: buyer net 0, PlotArt commission net 0, order refunded, original released (artist decides on relisting)',
  O1.status === 'refunded' && O1.payment_status === 'refunded' && fin.netfee === 0 && fin.netpaid === 0 && (await q("SELECT * FROM artwork_sales WHERE artwork_id='wagal1' AND released_at IS NOT NULL")).length === 1
  && (await db.prepare("SELECT availability FROM artworks WHERE id='wagal1'").first()).availability === 'sold', { O1, fin });
const ch1 = { id: M.pis[O1.payment_intent].charge, object: 'charge', payment_intent: O1.payment_intent, refunds: { data: M.refunds.filter(x => x.payment_intent === O1.payment_intent).map(x => ({ id: x.id, amount: x.amount, status: 'succeeded' })) } };
h = await hook(evt('charge.refunded', ch1, ACCT));
check('T9f the provider’s refund events confirm the same refunds without booking them twice', h.s === 200 && (await q("SELECT * FROM order_refunds WHERE order_id = ? AND status='succeeded'", o1.id)).length === 3
  && (await q("SELECT * FROM order_ledger WHERE order_id = ? AND kind IN ('artwork_refund','delivery_refund')", o1.id)).length === 3);
const SB = await order(second.id);
const extCh = { id: M.pis[SB.payment_intent].charge, object: 'charge', payment_intent: SB.payment_intent, refunds: { data: [{ id: 're_test_external1', amount: 10000, status: 'succeeded' }] } };
h = await hook(evt('charge.refunded', extCh, ACCT));
check('T9g a refund the artist makes in their own Stripe Dashboard is booked and flagged for commission settlement', h.s === 200 && /external refund/.test((await order(second.id)).needs_resolution)
  && (await q("SELECT * FROM order_ledger WHERE kind='external_refund' AND order_id = ?", second.id)).length === 1);

console.log('— disputes (test 10) and out-of-order charge events');
const oe = await makeOrder('aold', 'waold2', 'PA-E-261103-DDDDDD', 40000, 2500, 'e@example.test');
r = await call('POST', `/api/admin/checkout/orders/${oe.id}/send`, FOUNDER, {});
await call('POST', `/api/checkout/orders/${oe.id}/approve`, OLD, { quote_version: (await order(oe.id)).quote_version, confirm: ALL });
const ACCT_OLD = (await db.prepare("SELECT account_id FROM payment_accounts WHERE artist_id='aold'").first()).account_id;
const TE = (await call('POST', `/api/admin/checkout/orders/${oe.id}/issue`, FOUNDER, { days: 1, linked_check_confirmed: true })).j.buyer_link.split('/q/')[1];
await pub('POST', `/q/${TE}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } });
const sE = Object.values(M.sessions).at(-1);
check('T3b no application fee at all is requested when the commission is 0', sE._fee === null && sE._acct === ACCT_OLD);
pay(sE.id);
const dispute = { id: 'dp_test_1', object: 'dispute', payment_intent: sE.payment_intent, charge: M.pis[sE.payment_intent].charge, amount: 42500, reason: 'product_not_received', status: 'needs_response' };
h = await hook(evt('charge.dispute.created', dispute, ACCT_OLD));
check('T7i a dispute arriving BEFORE its payment completion is deferred (the provider retries), not lost', h.s === 500 && (await db.prepare('SELECT status FROM payment_events WHERE object_id = ?').bind('dp_test_1').first()).status === 'deferred');
await hook(evt('checkout.session.completed', M.sessions[sE.id], ACCT_OLD));
h = await hook(evt('charge.dispute.created', dispute, ACCT_OLD));
let OE = await order(oe.id);
check('T10a once paid, the dispute is recorded (debited from the seller’s Stripe balance by Stripe)', OE.status === 'disputed' && OE.dispute_status === 'open'
  && (await q("SELECT * FROM order_ledger WHERE kind='dispute' AND order_id = ?", oe.id))[0].amount_cents === -42500, OE);
await call('POST', `/api/admin/checkout/orders/${oe.id}/fulfilment`, FOUNDER, { kind: 'insurance', evidence: 'SIMULATED cover SIM-COVER-0001' });
await call('POST', `/api/admin/checkout/orders/${oe.id}/fulfilment`, FOUNDER, { kind: 'dispatched', evidence: 'SAC tracking 1Z999' });
h = await hook(evt('charge.dispute.closed', { ...dispute, status: 'lost' }, ACCT_OLD));
OE = await order(oe.id);
check('T10b a lost dispute is flagged with the documented recovery route (commission settlement; seller carries the loss with Stripe)', OE.dispute_status === 'lost' && OE.status === 'refunded' && /dispute lost/.test(OE.needs_resolution), OE);
r = await call('POST', `/api/admin/checkout/orders/${oe.id}/close`, FOUNDER, {});
check('T10c an order with an unresolved flag cannot be closed', r.s === 409);

console.log('— fulfilment and close');
const SB2 = await order(second.id);
r = await call('POST', `/api/checkout/orders/${second.id}/fulfilment`, GAL, { kind: 'delivered', evidence: 'Signed for' });
check('F1 delivery cannot be recorded before dispatch', r.s === 409, [r.s, r.j]);
r = await call('POST', `/api/checkout/orders/${second.id}/fulfilment`, GAL, { kind: 'dispatched', evidence: 'Synthetic Art Couriers, tracking SAC-778; packed photos ref P-12' });
check('F1b no dispatch without the shipment’s transit insurance confirmation', r.s === 409 && /insurance/.test(r.j.error), r.j);
await call('POST', `/api/checkout/orders/${second.id}/fulfilment`, GAL, { kind: 'insurance', evidence: 'SIMULATED certificate SIM-COVER-0001, Synthetic Underwriting, €1,000 collection to signed delivery' });
r = await call('POST', `/api/checkout/orders/${second.id}/fulfilment`, GAL, { kind: 'dispatched', evidence: 'Synthetic Art Couriers, tracking SAC-778; packed photos ref P-12' });
r = await call('POST', `/api/checkout/orders/${second.id}/fulfilment`, GAL, { kind: 'delivered', evidence: 'Signed for by buyer 18 Nov; arrival photos ref P-13' });
check('F2 the artist records dispatch and delivery evidence (append-only)', r.s === 200 && (await order(second.id)).status === 'delivered' && (await order(second.id)).fulfilment_status === 'delivered'
  && !!(await db.prepare('DELETE FROM order_fulfilment_events').run().catch(e => e)).message, r.j);
check('F3 every status change is audited with actor, prior and new status', (await q('SELECT * FROM order_events WHERE order_id = ? ORDER BY id', second.id)).map(e => `${e.prior_status}>${e.new_status}`).includes('dispatched>delivered')
  && (await q('SELECT * FROM order_events WHERE order_id = ?', second.id)).every(e => e.actor && e.at && e.action));
M.nextRefundStatus = 'pending';
r = await call('POST', `/api/admin/checkout/orders/${second.id}/refund`, FOUNDER, { artwork_cents: 5000, delivery_cents: 0, reason: 'Goodwill for late delivery' });
const rfx = M.refunds.at(-1); fees = M.feeRefunds.length;
h = await hook(evt('refund.failed', { ...rfx, id: rfx.id, status: 'failed', failure_reason: 'insufficient_funds' }, ACCT));
const SX = await order(second.id);
check('R5 a refund Stripe fails (e.g. still unfunded after 45 days) is flagged: buyer NOT repaid, nothing booked, no commission returned',
  h.s === 200 && /failed \(insufficient_funds\)/.test(SX.needs_resolution) && (await db.prepare('SELECT status FROM order_refunds WHERE provider_refund_id = ?').bind(rfx.id).first()).status === 'failed'
  && !(await q("SELECT * FROM order_ledger WHERE provider_ref = ?", rfx.id)).length && M.feeRefunds.length === fees, SX);
M.nextRefundStatus = 'pending';
r = await call('POST', `/api/admin/checkout/orders/${second.id}/refund`, FOUNDER, { artwork_cents: 2000, delivery_cents: 0, reason: 'Second goodwill refund' });
const rfy = M.refunds.at(-1); rfy.status = 'succeeded';   // the artist's balance recovered; the webhook is lost
await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
check('R6 the sweep re-checks pending refunds with Stripe, so a missed webhook cannot leave one stale', (await db.prepare('SELECT status FROM order_refunds WHERE provider_refund_id = ?').bind(rfy.id).first()).status === 'succeeded'
  && (await q("SELECT * FROM order_ledger WHERE provider_ref = ? AND kind = 'artwork_refund'", rfy.id)).length === 1);
M.nextRefundStatus = 'pending';
r = await call('POST', `/api/admin/checkout/orders/${second.id}/refund`, FOUNDER, { artwork_cents: 5000, delivery_cents: 0, reason: 'Third refund, unfunded' });
const rfz = M.refunds.at(-1);
await db.prepare('UPDATE order_refunds SET created_at = ? WHERE provider_refund_id = ?').bind(ago(8), rfz.id).run();
await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
check('R7 after 7 days unfunded it is escalated (notification + flag), once', /^OVERDUE/.test((await order(second.id)).needs_resolution)
  && (await q("SELECT * FROM order_events WHERE order_id = ? AND action = 'notified_refund_pending_overdue'", second.id)).length === 1);
await db.prepare('UPDATE order_refunds SET created_at = ? WHERE provider_refund_id = ?').bind(ago(31), rfz.id).run();
await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' }); await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
check('R7b after 30 days it is marked urgent, once', /^URGENT/.test((await order(second.id)).needs_resolution) && (await q("SELECT * FROM order_events WHERE order_id = ? AND action = 'notified_refund_pending_urgent'", second.id)).length === 1);
r = await call('POST', `/api/admin/checkout/orders/${second.id}/repaid`, FOUNDER, { artwork_cents: 5000, delivery_cents: 0, evidence: 'Bank transfer BT-123 on 18 Nov, buyer confirmed by email' });
check('R8 repaying the buyer outside Stripe is refused while the Stripe refund is still pending (no double repayment)', r.s === 409 && /still pending/.test(r.j.error), r.j);
rfz.status = 'failed'; rfz.failure_reason = 'insufficient_funds';
await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
fees = M.feeRefunds.length;
r = await call('POST', `/api/admin/checkout/orders/${second.id}/repaid`, FOUNDER, { artwork_cents: 5000, delivery_cents: 0, evidence: 'Bank transfer BT-123 on 18 Nov, buyer confirmed by email' });
check('R9 after Stripe cancels it, the artist’s direct repayment is recorded and PlotArt returns its commission share (GAA 9.2: €7,500c × kept €430 / €500 → €0.75 of €75 already partly returned)', r.s === 200
  && (await q("SELECT * FROM order_ledger WHERE order_id = ? AND kind = 'artwork_refund' AND provider_ref LIKE 'ext_%'", second.id)).length === 1
  && M.feeRefunds.length === fees + 1 && M.feeRefunds.at(-1).amount === 750, [r.j, M.feeRefunds.at(-1)]);
check('F4 the ledger cannot be edited', !!(await db.prepare('UPDATE order_ledger SET amount_cents = 0').run().catch(e => e)).message);
void SB2;

console.log('— leaving, scheduled sweep, isolation (tests 11, 15)');
const og = await makeOrder('afnd', 'wafnd2', 'PA-E-251101-CCCCCC', 30000, 0, 'g@example.test');
r = await call('POST', '/api/checkout/leave', FND, {});
check('L1 an artist can leave at any time: unpaid quotes are cancelled, nothing is charged', r.s === 200 && !r.j.membership.opted_in && (await order(og.id)).status === 'cancelled' && (await order(of.id)).status === 'cancelled');
await db.prepare("INSERT INTO artwork_reservations (artwork_id, order_id, quote_version, expires_at, created_at) VALUES ('waunk2', ?, 1, ?, ?)").bind(ou.id, ago(1), ago(1)).run();
const sw = await S.mf.getWorker('checkout').then(w => w.scheduled({ cron: '*/15 * * * *' })).catch(e => e);
check('L2 the scheduled sweep releases lapsed reservations', !(await q("SELECT * FROM artwork_reservations WHERE artwork_id='waunk2'")).length, sw);
const AFTER = JSON.parse(await snapshotOf()), B = JSON.parse(BEFORE);
check('T11 gallery publication, versions, publish queue, gallery positions, founding numbers, artist records, agreements, terms, enquiry log and enquiries are unchanged',
  ['v', 'pq', 'gp', 'ar', 'aa', 'gaa', 'at', 'el', 'en', 'works'].every(k => JSON.stringify(AFTER[k]) === JSON.stringify(B[k])),
  ['v', 'pq', 'gp', 'ar', 'aa', 'gaa', 'at', 'el', 'en', 'works'].filter(k => JSON.stringify(AFTER[k]) !== JSON.stringify(B[k])));
check('T11b the only artwork change is the sold mark on works sold through verified payments', (await q("SELECT id FROM artworks WHERE availability='sold' ORDER BY id")).map(x => x.id).join() === 'waold2,wagal1,wagal2'.split(',').sort().join());
console.log('— records outlive the artist’s own records; retention (item 8)');
const ox = await makeOrder('aold', 'waold3', 'PA-E-261103-DDDDDD', 30000, 2000, 'x@example.test', { ...DELIVERY, covered_value_cents: 30000 });
await call('POST', `/api/admin/checkout/orders/${ox.id}/send`, FOUNDER, {});
await call('POST', `/api/checkout/orders/${ox.id}/approve`, OLD, { quote_version: (await order(ox.id)).quote_version, confirm: ALL });
const TX = (await call('POST', `/api/admin/checkout/orders/${ox.id}/issue`, FOUNDER, { days: 1, linked_check_confirmed: true })).j.buyer_link.split('/q/')[1];
await pub('POST', `/q/${TX}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } });
const sX = Object.values(M.sessions).at(-1); pay(sX.id); await hook(evt('checkout.session.completed', M.sessions[sX.id], ACCT_OLD));
check('D0 a paid order exists for the artist', (await order(ox.id)).status === 'paid');
// the artist's participation ended long ago and their six-year record retention has passed: the REAL deletion schedule runs
await db.prepare("UPDATE artists SET account_status = 'ended' WHERE id = 'aold'").run();
await db.prepare("INSERT INTO participation_events (id, artist_id, kind, at, actor, reason, detail) VALUES ('peold', 'aold', 'ended', '2019-01-01T00:00:00Z', ?, 'test', '{}')").bind(FOUNDER).run();
await db.prepare("INSERT INTO record_retention (artist_id, ended_at, delete_after, recorded_by, recorded_at) VALUES ('aold', '2019-01-01T00:00:00Z', '2025-01-02T00:00:00Z', ?, ?)").bind(FOUNDER, ago(0)).run();
const del = await S.mf.getWorker('studio').then(w => w.scheduled({ cron: '0 3 * * *' })).catch(e => e);
const goneArtist = !(await db.prepare("SELECT 1 FROM artists WHERE id='aold'").first());
check('D1 the existing deletion schedule deletes the artist’s records; the pilot tables never block it', goneArtist, [del, await q("SELECT action, detail FROM audit WHERE action LIKE '%delet%' OR action = 'cleanup' ORDER BY id DESC LIMIT 2")]);
r = await call('GET', `/api/admin/checkout/orders/${ox.id}`, FOUNDER);
check('D2 the order still shows seller, artwork, amounts, entitlement and ledger from its own snapshots', r.s === 200 && r.j.order.seller.name === 'Oisin Older' && r.j.order.artwork.title === 'Work 3'
  && r.j.order.commission_basis === 'founding_artist_no_commission_terms' && r.j.ledger.some(l => l.kind === 'charge' && l.amount_cents === 32000), r.j);
r = await call('POST', `/api/admin/checkout/orders/${ox.id}/refund`, FOUNDER, { artwork_cents: 30000, delivery_cents: 2000, reason: 'Returned after the artist left' });
check('D3 a full refund still works after the artist’s and artwork’s rows are gone', r.s === 200 && r.j.order.status === 'refunded' && M.refunds.at(-1)._acct === ACCT_OLD, r.j);
check('D4 the buyer’s link still reads correctly', (await pub('GET', `/q/${TX}/return?result=success`)).t.includes('has been confirmed') || (await pub('GET', `/q/${TX}/return`)).s === 200);
await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
const RX = await order(ox.id);
check('D5 an order that moved money is kept until 31 December of the sixth year after its last money movement, and not deleted before', RX.retain_until === `${new Date().getUTCFullYear() + 6}-12-31T23:59:59.000Z`
  && /retention/.test((await db.prepare('DELETE FROM checkout_orders WHERE id = ?').bind(ox.id).run().catch(e => e)).message)
  && /retention/.test((await db.prepare('DELETE FROM order_ledger WHERE order_id = ?').bind(ox.id).run().catch(e => e)).message), RX);
check('D6 a retention date is fixed once set: neither shortened nor extended', /fixed once set/.test((await db.prepare("UPDATE checkout_orders SET retain_until = '2027-01-01T00:00:00Z' WHERE id = ?").bind(ox.id).run().catch(e => e)).message)
  && /fixed once set/.test((await db.prepare("UPDATE checkout_orders SET retain_until = '2099-01-01T00:00:00Z' WHERE id = ?").bind(ox.id).run().catch(e => e)).message));
const OG = await order(og.id);
check('D7 an unpaid cancelled order is kept two years', OG.retain_until && OG.retain_until.slice(0, 4) === String(new Date().getUTCFullYear() + 2), OG);
// an old order whose retention has passed is deleted with its ledger, events and sessions
await db.prepare(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, payment_status, buyer_email, created_by, created_at, updated_at, retain_until)
  VALUES ('oold1', 'PA-O-190101-OLD001', 'aold', 'waold9', 'PA-E-190101-AAAAAA', 'closed', 'paid', 'old@example.test', 'test', '2019-01-01T00:00:00Z', '2019-02-01T00:00:00Z', '2025-02-01T00:00:00Z')`).run();
await db.prepare("INSERT INTO order_ledger (id, order_id, kind, amount_cents, provider_ref, at) VALUES ('lold1', 'oold1', 'charge', 1000, 'pi_old', '2019-01-01T00:00:00Z')").run();
await db.prepare("INSERT INTO order_events (order_id, at, actor, action) VALUES ('oold1', '2019-01-01T00:00:00Z', 'test', 'created')").run();
await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
check('D8 after its retention period an order is deleted with all its records', !(await db.prepare("SELECT 1 FROM checkout_orders WHERE id='oold1'").first())
  && !(await q("SELECT * FROM order_ledger WHERE order_id='oold1'")).length && !(await q("SELECT * FROM order_events WHERE order_id='oold1'")).length);
// legal holds: a reviewed, releasable exception — not an extension of the retention date
await db.prepare(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, payment_status, buyer_email, created_by, created_at, updated_at, retain_until)
  VALUES ('oold2', 'PA-O-190101-OLD002', 'aold', 'waold9', 'PA-E-190101-AAAAAA', 'closed', 'paid', 'old2@example.test', 'test', '2019-01-01T00:00:00Z', '2019-02-01T00:00:00Z', '2025-12-31T23:59:59.000Z')`).run();
await db.prepare("INSERT INTO order_ledger (id, order_id, kind, amount_cents, provider_ref, at) VALUES ('lold2', 'oold2', 'charge', 1000, 'pi_old2', '2019-01-01T00:00:00Z')").run();
r = await call('POST', '/api/admin/checkout/orders/oold2/hold', FOUNDER, { basis: 'claim', reason: 'Buyer solicitor letter of 1 Nov about this sale', review_by: '2099-01-01' });
check('H1 a hold needs a review date within 12 months', r.s === 400 && /12 months/.test(r.j.error));
const rv1 = new Date(Date.now() + 30 * 86400_000).toISOString().slice(0, 10);
r = await call('POST', '/api/admin/checkout/orders/oold2/hold', FOUNDER, { basis: 'claim', reason: 'Buyer solicitor letter of 1 Nov about this sale', review_by: rv1 });
const HID = r.j.hold.id;
await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
check('H2 an order under an active hold is not deleted after its retention date, and its records cannot be deleted directly', !!(await order('oold2'))
  && /hold/.test((await db.prepare("DELETE FROM order_ledger WHERE order_id = 'oold2'").run().catch(e => e)).message) && /hold/.test((await db.prepare("DELETE FROM checkout_orders WHERE id = 'oold2'").run().catch(e => e)).message));
check('H3 a hold’s reason and basis cannot be rewritten', /renewed|released/.test((await db.prepare("UPDATE checkout_holds SET reason = 'changed reason here' WHERE id = ?").bind(HID).run().catch(e => e)).message));
await db.prepare("UPDATE checkout_holds SET review_by = ? WHERE id = ?").bind(ago(2).slice(0, 10), HID).run();
check('H4 an overdue review is flagged, and nothing is renewed or released automatically', (await call('GET', '/api/admin/checkout', FOUNDER)).j.holds.find(x => x.id === HID).review_overdue === true && !(await db.prepare('SELECT released_at FROM checkout_holds WHERE id = ?').bind(HID).first()).released_at);
r = await call('POST', `/api/admin/checkout/holds/${HID}`, FOUNDER, { decision: 'renew', review_by: rv1, note: 'Claim still open; solicitor replied 20 Nov' });
check('H5 a review renews the hold to a new date, with the reason recorded', r.s === 200 && r.j.hold.review_by === rv1 && r.j.history.map(x => x.kind).join() === 'placed,renewed', r.j);
r = await call('POST', `/api/admin/checkout/holds/${HID}`, FOUNDER, { decision: 'release', note: 'Claim withdrawn in writing on 1 Dec' });
check('H6 release is recorded once and cannot be undone', r.s === 200 && !!r.j.hold.released_at && /renewed|released/.test((await db.prepare("UPDATE checkout_holds SET released_at = NULL, released_by = NULL, release_reason = NULL WHERE id = ?").bind(HID).run().catch(e => e)).message));
await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
check('H7 once released, the past-retention order is deleted at the next sweep, with its hold history', !(await order('oold2')) && !(await q("SELECT * FROM checkout_holds WHERE order_id = 'oold2'")).length
  && !(await q("SELECT * FROM checkout_hold_events WHERE order_id = 'oold2'")).length && !(await q("SELECT * FROM order_ledger WHERE order_id = 'oold2'")).length);
await db.prepare("INSERT INTO payment_pilot_events (id, artist_id, kind, doc_id, doc_sha256, account_email, display_name, statement, at) VALUES ('peoldin', 'aunk', 'opted_in', 'PA-PAY-TEST-01', ?, 'x@example.test', 'X', 'test', '2019-01-01T00:00:00Z')").bind(sha(ADD)).run().catch(() => {});
const OLDLEFT = 'apast';
await db.prepare("INSERT INTO payment_pilot_events (id, artist_id, kind, doc_id, doc_sha256, account_email, display_name, statement, at) VALUES ('pep1', ?, 'opted_in', 'PA-PAY-TEST-01', ?, 'p@example.test', 'Past', 'test', '2019-01-01T00:00:00Z')").bind(OLDLEFT, sha(ADD)).run();
await db.prepare("INSERT INTO payment_pilot_events (id, artist_id, kind, account_email, at) VALUES ('pep2', ?, 'left', 'p@example.test', '2019-06-01T00:00:00Z')").bind(OLDLEFT).run();
await db.prepare("INSERT INTO payment_accounts (artist_id, account_id, country, created_at, updated_at) VALUES (?, 'acct_pastartist', 'IE', '2019-01-01T00:00:00Z', '2019-01-01T00:00:00Z')").bind(OLDLEFT).run();
await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
check('D10 an artist’s opt-in, consent and Stripe-account records are deleted six years after leaving once no order is kept; recent leavers are kept',
  !(await q('SELECT * FROM payment_pilot_events WHERE artist_id = ?', OLDLEFT)).length && !(await q('SELECT * FROM payment_accounts WHERE artist_id = ?', OLDLEFT)).length
  && (await q("SELECT * FROM payment_pilot_events WHERE artist_id = 'afnd'")).length > 0);
check('D9 opt-in records stay while the artist’s orders are kept', /kept/.test((await db.prepare("DELETE FROM payment_pilot_events WHERE artist_id='aold'").run().catch(e => e)).message));

const S1 = await import(HERE + FIX + 'src/stripe.js');
check('T15b a live secret key is refused before any request', !S1.testKey({ STRIPE_SECRET_KEY: 'sk_live_abc' }).ok && !S1.testKey({}).ok && S1.testKey({ STRIPE_SECRET_KEY: 'rk_test_abc' }).ok);
check('T15c test-mode only in the database: live accounts and live sessions cannot be stored',
  /CHECK/.test((await db.prepare("INSERT INTO checkout_sessions (id, order_id, quote_version, amount_total, application_fee_cents, status, expires_at, created_at, updated_at) VALUES ('cs_live_1', ?, 1, 1, 0, 'open', ?, ?, ?)").bind(o1.id, ago(0), ago(0), ago(0)).run().catch(e => e)).message)
  && /CHECK/.test((await db.prepare("UPDATE payment_accounts SET livemode = 1").run().catch(e => e)).message));
const toml = readFileSync(HERE + 'wrangler.checkout.toml', 'utf8');
check('T15d the public Worker ships switched off, and no secret is in the repository', /CHECKOUT_PILOT_ENABLED = "false"/.test(toml) && !/sk_(test|live)_[A-Za-z0-9]{8,}|whsec_[A-Za-z0-9]{8,}/.test(toml + readFileSync(HERE + 'src/checkout.js', 'utf8') + readFileSync(HERE + 'src/stripe.js', 'utf8')));
check('T15e no call ever left for anywhere but the mock provider', M.calls.length > 10);
} finally {
  if (S) await S.mf.dispose();
}

// ---- a second instance with the DEFAULT configuration: the pilot is off
let OFF;
try {
  OFF = await start({ port: 8872, script: FIX + 'src/index.js', checkout: { script: FIX + 'src/checkout-public.js', env: { CHECKOUT_ORIGIN: 'https://checkout.local' } }, outbound: () => new Response('{}', { status: 599 }) });
  await seedPublished(OFF.db, { id: 'agal', slug: 'gal', email: 'gal@example.test', name: 'Gale', works: 1 });
  const r = await OFF.mf.dispatchFetch(OFF.url + '/api/checkout/opt-in', { method: 'POST', headers: { 'Cf-Access-Jwt-Assertion': token('gal@example.test'), 'X-Studio': '1', 'Content-Type': 'application/json' }, body: '{"accept":true}' });
  const v = await (await OFF.mf.dispatchFetch(OFF.url + '/api/admin/checkout', { headers: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } })).json();
  const pg = await OFF.checkoutWorker.fetch('https://checkout.local/q/' + 'a'.repeat(48));
  check('OFF1 by default the pilot is switched off: no opt-in, no quotes, no buyer pages', r.status === 503 && v.switches.enabled === false && pg.status === 503);
  const enq = await OFF.mf.dispatchFetch(OFF.url + '/api/enquiries', { headers: { 'Cf-Access-Jwt-Assertion': token('gal@example.test') } });
  check('OFF2 the existing Studio enquiries view still works', enq.status === 200 && (await enq.json()).ok === true);
} finally { if (OFF) await OFF.mf.dispose(); rmSync(HERE + FIX, { recursive: true, force: true }); }

const passed = results.filter(Boolean).length;
console.log(`\nMANAGED CHECKOUT PILOT · ${results.length} checks, ${passed} passed, ${results.length - passed} failed`);
process.exit(passed === results.length ? 0 : 1);
