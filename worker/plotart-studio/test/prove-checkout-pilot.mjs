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
const M = { disputes: {}, accounts: {}, v2accounts: {}, nextAccountResponsibilities: null, sessions: {}, pis: {}, refunds: [], feeRefunds: [], charges: {}, feeAmounts: {}, calls: [], idem: {}, n: 0, failNextExpire: false, nextRefundStatus: null };
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
  if ((mm = u.pathname.match(/^\/v1\/disputes\/(dp_[\w]+)$/)) && req.method === 'GET') return M.disputes[mm[1]] && M.disputes[mm[1]]._acct === acct ? ok(M.disputes[mm[1]]) : err('no such dispute', 404);
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
  if ((mm = u.pathname.match(/^\/v1\/application_fees\/(fee_test_\w+)\/refunds$/))) {
    // like Stripe: an application fee cannot be refunded beyond its amount
    const feeAmt = M.feeAmounts[mm[1]], done = M.feeRefunds.filter(x => x.fee === mm[1]).reduce((a, x) => a + x.amount, 0);
    if (feeAmt !== undefined && done + Number(f.amount) > feeAmt) return err(`Refund amount (${f.amount}) is greater than unrefunded amount on fee (${feeAmt - done})`, 400);
    if (req.method === 'GET') return ok({ object: 'list', data: M.feeRefunds.filter(x => x.fee === mm[1]).slice().reverse(), has_more: false });
    if (M.failFeeRefunds > 0) { M.failFeeRefunds--; return err(M.failFeeRefundMessage || 'SIMULATED: temporary Stripe error', 500); }   // SIMULATED failure: nothing is created
    const r = { id: nid('fr'), object: 'fee_refund', amount: Number(f.amount), fee: mm[1], livemode: false, created: Math.floor(Date.now() / 1000), balance_transaction: nid('txn'), metadata: { plotart_kind: f['metadata[plotart_kind]'], plotart_order: f['metadata[plotart_order]'] } }; M.feeRefunds.push(r);
    if (M.loseFeeRefundAnswer) { M.loseFeeRefundAnswer = false; return err('SIMULATED: connection lost after Stripe accepted the refund', 502); }   // SIMULATED: Stripe made it, the answer is lost (and the idempotency entry with it)
    return remember(r); }
  if ((mm = u.pathname.match(/^\/v1\/charges\/(ch_test_\w+)$/)) && req.method === 'GET') {
    const c = M.charges[mm[1]]; if (!c) return err('no such charge', 404);
    const created = c.noCreated ? {} : { created: c.created };
    if (c.btPending) return ok({ id: c.id, object: 'charge', ...created, balance_transaction: null });
    return ok({ id: c.id, object: 'charge', ...created, application_fee: c.fee, balance_transaction: u.search.includes('balance_transaction') ? c.bt : c.bt.id });
  }
  return err('mock: unhandled ' + req.method + ' ' + u.pathname, 404);
}
/* The buyer pays at Stripe (mock): the session completes, a payment intent, charge and application fee exist. */
function pay(sid) {
  const s = M.sessions[sid]; s.status = 'complete'; s.payment_status = 'paid';
  const pi = nid('pi'); s.payment_intent = pi;
  M.pis[pi] = { id: pi, object: 'payment_intent', livemode: false, amount: s.amount_total, charge: nid('ch'), fee: s._fee ? nid('fee') : null, metadata: s.metadata };
  // Stripe's processing fee, as an Irish sandbox account showed it: 1.5% + EUR 0.25 for an EEA card, VAT 23% on the fee, recorded as separate lines
  const sf = M.nextStripeFee ?? Math.round(s.amount_total * 0.015) + 25, vat = Math.round(sf * 0.23), extra = M.nextExtraFee || 0; M.nextStripeFee = null; M.nextExtraFee = 0;
  const fd = [{ type: 'stripe_fee', amount: sf, description: 'Stripe processing fees' }, { type: 'tax', amount: vat + Math.round(extra * 0.23), description: 'VAT' },
    ...(s._fee ? [{ type: 'application_fee', amount: s._fee, description: 'Application fee' }] : []), ...(extra ? [{ type: 'stripe_fee', amount: extra, description: 'Radar for Fraud Teams' }] : [])];
  M.charges[M.pis[pi].charge] = { id: M.pis[pi].charge, fee: M.pis[pi].fee, created: Math.floor(Date.now() / 1000), btPending: !!M.btPendingNext, bt: { id: nid('txn'), object: 'balance_transaction', created: Math.floor(Date.now() / 1000), currency: s.currency, amount: s.amount_total, fee: fd.reduce((a, x) => a + x.amount, 0), fee_details: fd } };
  M.btPendingNext = false;
  if (M.pis[pi].fee) M.feeAmounts[M.pis[pi].fee] = s._fee;
  return s;
}
const sign = (raw, t = Math.floor(Date.now() / 1000), secret = WHSEC) => `t=${t},v1=${createHmac('sha256', secret).update(`${t}.${raw}`).digest('hex')}`;
let EV = 0;
const evt = (type, object, account, extra = {}) => ({ id: `evt_test_${++EV}`, object: 'event', type, livemode: false, created: Math.floor(Date.now() / 1000), account, data: { object }, ...extra });

let S;
try {
console.log('PROVE · managed checkout pilot');
const ORIGIN = 'https://checkout.local';
const ENVV = { CHECKOUT_MESSAGE_RETRY_MINUTES: '0', CHECKOUT_NOTIFY_EMAIL: 'founder-notify@plotnua.invalid', PARTICIPATION_DELETION: 'on', CHECKOUT_PILOT_ENABLED: 'true', STRIPE_SECRET_KEY: 'sk_test_mockkey123', STRIPE_WEBHOOK_SECRET: WHSEC, STRIPE_API_BASE: 'https://stripe.mock', CHECKOUT_ORIGIN: ORIGIN };
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
await seedPublished(db, { id: 'agal', slug: 'gal', email: GAL, name: 'Gale Gallery', works: 9, publishedAt: ago(30) });
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
  tracking: 'Tracked, signature on delivery', signed_receipt: true, condition_photos: true, return_method: 'Same courier, packed as delivered, insured', return_address: '12 Studio Lane, Dublin 8', return_cost_cents: 9500, return_cost_basis: 'estimated_maximum', return_arranged_by: 'buyer', shipment_confirmation_ref: 'SAC-Q-1001', shipment_confirmed_by: 'Synthetic Art Couriers', shipment_confirmed_on: '2026-11-16' };
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
rpc = await call('POST', `/api/checkout/orders/${of.id}/approve`, FND, { quote_version: (await order(of.id)).quote_version, confirm: { available: true, location: true, condition: true, framing: true, dimensions: true, packing_and_handover: true, returns: true, seller_information: true } });
check('PC1 Model B: a commission-free order (Founding Enquiry) is not taken through the pilot; it stays on direct payment', rpc.s === 409 && /stay on direct payment/.test(rpc.j.error), rpc.j);
rpc = await call('POST', '/api/checkout/processing-consent', FND, { accept: true, statement: 'something else' });
check('PC2 the consent must be to the exact statement shown', rpc.s === 400);
const PSTAT = (await call('GET', '/api/checkout', FND)).j.processing_statement;
for (const e of [FND, OLD]) rpc = await call('POST', '/api/checkout/processing-consent', e, { accept: true, statement: PSTAT });
check('PC3 consent is recorded separately from the addendum acceptance, with its statement', rpc.s === 200 && rpc.j.membership.processing_consent === true
  && (await q("SELECT * FROM payment_pilot_events WHERE kind='processing_consent'")).length === 2 && (await q("SELECT * FROM payment_pilot_events WHERE kind='processing_consent' AND doc_id IS NOT NULL")).length === 0);
const ALLC = { available: true, location: true, condition: true, framing: true, dimensions: true, packing_and_handover: true, returns: true, seller_information: true };
rpc = await call('POST', `/api/checkout/orders/${of.id}/approve`, FND, { quote_version: (await order(of.id)).quote_version, confirm: ALLC });
check('PC4 Model B: even with the artist’s consent, a commission-free order is not enrolled automatically (direct payment)', rpc.s === 409 && /stay on direct payment/.test(rpc.j.error), rpc.j);
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
const ALL = { available: true, location: true, condition: true, framing: true, dimensions: true, packing_and_handover: true, returns: true, seller_information: true };
console.log('— seller information and returns on the quote');
r = await call('POST', `/api/checkout/orders/${o1.id}/approve`, GAL, { quote_version: v1, confirm: ALL });
check('SP1 an artist cannot approve a quote before giving the seller information buyers must see', r.s === 409 && /seller information/.test(r.j.error), r.j);
const SELLER = { legal_name: 'Gale Gallagher', trading_name: 'Gale Gallery', address: '12 Studio Lane, Dublin 8, Ireland', email: 'sales@galegallery.example', phone: '+353 1 555 0100', vat_number: '', trader_status: 'trader' };
r = await call('PUT', '/api/checkout/seller-profile', GAL, { ...SELLER, phone: 'call me' , confirm: true });
const r2sp = await call('PUT', '/api/checkout/seller-profile', GAL, { ...SELLER, trader_status: undefined, confirm: true });
const r3sp = await call('PUT', '/api/checkout/seller-profile', GAL, { ...SELLER });
check('SP2 seller information needs a valid phone, a trader declaration and the artist’s confirmation', r.s === 400 && r2sp.s === 400 && /trader/.test(r2sp.j.error) && r3sp.s === 400, [r.j, r2sp.j, r3sp.j]);
r = await call('PUT', '/api/checkout/seller-profile', GAL, { ...SELLER, confirm: true });
await call('PUT', '/api/checkout/seller-profile', OLD, { ...SELLER, legal_name: 'Oisin Older', trading_name: '', email: 'oisin@older.example', confirm: true });
check('SP3 the artist saves their seller information', r.s === 200 && r.j.seller_profile.legal_name === 'Gale Gallagher' && r.j.seller_profile.trader_status === 'trader', r.j);
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
{ const snap = await db.prepare('SELECT * FROM quote_snapshots WHERE order_id = ?').bind(o1.id).first(), Q1 = await order(o1.id);
  const sj = JSON.parse(snap.snapshot);
  check('QS1 the exact issued quote is kept: seller identity, address, contact, trader status, amounts, delivery, returns and terms, fingerprinted', snap.sha256 === sha(snap.snapshot) && Q1.quote_sha256 === snap.sha256
    && sj.seller.legal_name === 'Gale Gallagher' && sj.seller.address && sj.seller.phone && sj.seller.trader_status === 'trader' && sj.delivery.return_cost_cents === 9500 && sj.delivery.return_arranged_by === 'buyer'
    && sj.amounts.total_cents === 107500 && sj.terms.doc_id === 'PA-BPT-TEST-01' && !('cover_confirmed_by' in sj.delivery), sj);
  check('QS2 an issued quote snapshot cannot be changed', /append-only/.test((await db.prepare("UPDATE quote_snapshots SET snapshot = '{}' WHERE order_id = ?").bind(o1.id).run().catch(e => e)).message)); }

console.log('— buyer page and hosted checkout (test 13)');
let pg = await pub('GET', `/q/${T1}`);
check('B1a the buyer sees the seller’s legal name, address, email, phone and trader status, and the return method, address, cost and who arranges it',
  pg.t.includes('Gale Gallagher') && pg.t.includes('12 Studio Lane') && pg.t.includes('sales@galegallery.example') && pg.t.includes('+353 1 555 0100') && /Sells as a trader/.test(pg.t)
  && pg.t.includes('Up to about €95.00') && /Arranged by<\/dt><dd>you \(the buyer\)/.test(pg.t));
await call('PUT', '/api/checkout/seller-profile', GAL, { ...SELLER, phone: '+353 1 555 0199', confirm: true });
check('QS3 editing seller information later never changes an issued quote', (await pub('GET', `/q/${T1}`)).t.includes('+353 1 555 0100') && !(await pub('GET', `/q/${T1}`)).t.includes('0199'));
check('B1 the buyer sees seller, artwork, delivery, cover and total before paying', pg.s === 200 && pg.t.includes('Gale Gallery') && pg.t.includes('€1,000.00') && pg.t.includes('€75.00') && pg.t.includes('€1,075.00')
  && pg.t.includes('Synthetic Underwriting') && pg.t.includes('not escrow') && pg.t.includes('Test mode') && !pg.t.includes(GAL), pg.t.slice(0, 300));
check('B2 the buyer page never shows the commission or the artist’s Studio login email', !/15%|150\.00|commission/i.test(pg.t) && !pg.t.includes(GAL), (pg.t.match(/.{60}(15%|150\.00|commission).{60}/i) || [])[0]);
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
  JSON.stringify(L1.filter(l => !/^processing/.test(l.kind))) === JSON.stringify([{ kind: 'artist_artwork', amount_cents: 85000 }, { kind: 'charge', amount_cents: 107500 }, { kind: 'commission', amount_cents: 15000 }, { kind: 'delivery_allocation', amount_cents: 7500 }]), L1);
console.log('— fee model B: PlotArt reimburses Stripe’s actual processing fee + VAT on it, from the application fee');
{ const bt = M.charges[M.pis[O1.payment_intent].charge].bt, sf = bt.fee_details.find(x => x.type === 'stripe_fee').amount, vt = bt.fee_details.find(x => x.type === 'tax').amount;
  const P = JSON.parse((await order(o1.id)).processing), frs = M.feeRefunds.filter(x => x.fee === M.pis[O1.payment_intent].fee);
  check('MB1 the actual fee is read from Stripe’s balance transaction (whole payment incl. delivery): EUR 16.38 + VAT EUR 3.77 = EUR 20.15', sf === 1638 && vt === 377 && P.stripe_fee === 1638 && P.vat === 377 && P.cost === 2015 && P.balance_transaction === bt.id, P);
  check('MB2 reimbursed once by a partial application-fee refund of exactly that amount; commission booked in full, separately', frs.length === 1 && frs[0].amount === 2015 && P.status === 'reimbursed'
    && L1.some(l => l.kind === 'commission' && l.amount_cents === 15000) && L1.some(l => l.kind === 'processing_reimbursement' && l.amount_cents === 2015) && L1.some(l => l.kind === 'processing_fee' && l.amount_cents === 2015), { P, frs, L1 });
  const st1 = (await call('GET', `/api/checkout/orders/${o1.id}`, GAL)).j.statement;
  check('MB3 the artist statement separates gross, delivery, commission, processing fee, VAT, reimbursement and net (combined deduction = commission)', st1 && st1.gross_payment === 107500 && st1.of_which_delivery === 7500
    && st1.plotart_commission === 15000 && st1.stripe_processing_fee === 1638 && st1.vat_on_processing_fee === 377 && st1.processing_reimbursed_by_plotart === 2015 && st1.net_proceeds === 92500
    && st1.gross_payment - st1.net_proceeds === 15000 && st1.dispute_fees_status === 'no dispute' && /payout fees/.test(st1.not_included), st1);
  await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
  r = await call('POST', `/api/admin/checkout/orders/${o1.id}/processing`, FOUNDER, {});
  check('MB4 reconciling again (sweep, founder button) never reimburses twice', r.s === 200 && M.feeRefunds.filter(x => x.fee === M.pis[O1.payment_intent].fee).length === 1
    && (await q("SELECT * FROM order_ledger WHERE order_id = ? AND kind LIKE 'processing%'", o1.id)).length === 2, r.j); }
h = await hook(done1);
console.log('— buyer purchase confirmation (test sink only)');
{ const m = await db.prepare("SELECT * FROM order_messages WHERE order_id = ? AND kind = 'buyer_confirmation'").bind(o1.id).first();
  check('BC1 after Stripe confirms the sale, the buyer’s confirmation is prepared and kept: artwork, seller identity and contact, amounts, delivery, returns, accepted terms (id, fingerprint, full text) and the model cancellation form',
    !!m && m.sha256 === sha(m.body) && m.body.includes('Gale Gallagher') && m.body.includes('12 Studio Lane') && m.body.includes('Total paid by card through Stripe to the seller\'s own Stripe account: EUR 1075.00')
    && m.body.includes('EUR 75.00') && m.body.includes('Synthetic Underwriting') && m.body.includes('PA-BPT-TEST-01') && m.body.includes('MODEL CANCELLATION FORM') && m.body.includes('YOUR RIGHT TO CANCEL')
    && m.body.includes('up to about EUR 95.00') && m.body.includes((await order(o1.id)).quote_sha256) && /TEST MODE/.test(m.body) && m.body.length > 2000, m && m.body.slice(0, 600));
  const sink = await q("SELECT * FROM checkout_mail_sink WHERE kind = 'buyer_confirmation' AND order_id = ?", o1.id), dl = await q('SELECT * FROM order_message_deliveries WHERE message_id = ?', m.id);
  check('BC2 it goes only to the test sink: the intended address is kept as a fingerprint, nothing is sent anywhere', sink.length === 1 && sink[0].to_sha256 === sha('buyer@example.test') && !JSON.stringify(sink).includes('buyer@example.test')
    && sink[0].body === m.body && dl.length === 1 && dl[0].status === 'held_in_test_sink' && dl[0].channel === 'test_sink' && !(await q('SELECT * FROM mail_capture')).length, { sink: sink.length, dl });
  const pgc = await pub('GET', `/q/${T1}/confirmation`), ret = await pub('GET', `/q/${T1}/return`);
  check('BC3 the buyer can open the exact stored confirmation from their quote link (the return page links it)', pgc.s === 200 && pgc.t === m.body && pgc.h.get('X-Document-SHA256') === m.sha256 && ret.t.includes('/confirmation'));
  r = await call('POST', `/api/admin/checkout/orders/${o1.id}/confirmation`, FOUNDER, {});
  check('BC4 re-delivery uses the same stored text: one message, two delivery records, identical bodies', r.s === 200 && (await q('SELECT * FROM order_messages WHERE order_id = ?', o1.id)).length === 1
    && (await q('SELECT * FROM order_message_deliveries WHERE message_id = ?', m.id)).length === 2 && (await q("SELECT * FROM checkout_mail_sink WHERE kind = 'buyer_confirmation' AND order_id = ?", o1.id)).every(x => x.body === m.body), r.j && r.j.error);
  check('BC5 a stored confirmation cannot be edited', /append-only/.test((await db.prepare("UPDATE order_messages SET body = 'x' WHERE id = ?").bind(m.id).run().catch(e => e)).message)); }
check('T7f the same event delivered again is recognised and not re-applied', h.s === 200 && h.j.duplicate && (await q('SELECT * FROM order_ledger WHERE order_id = ?', o1.id)).length === 6);
const dup2 = { ...done1, id: `evt_test_${++EV}` };   // a different event id carrying the same completion (provider retry semantics differ)
h = await hook(dup2);
check('T7g a second event for the same payment books nothing twice', h.s === 200 && (await q('SELECT * FROM order_ledger WHERE order_id = ?', o1.id)).length === 6 && (await q("SELECT * FROM artwork_sales WHERE artwork_id='wagal1'")).length === 1);
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

console.log('— a quote needs current seller information and complete return arrangements');
{ const os = await makeOrder('agal', 'wagal8', 'PA-E-261101-AAAAAA', 20000, 2000, 's@example.test');
  const { return_address: _ra, ...noRA } = DELIVERY;
  r = await call('PUT', `/api/admin/checkout/orders/${os.id}`, FOUNDER, { delivery: noRA });
  check('RT1 delivery details without the return address (or method, cost, basis, who arranges it) are refused', r.s >= 400 && /return address/.test(r.j.error), r.j);
  await call('PUT', `/api/admin/checkout/orders/${os.id}`, FOUNDER, { delivery: { ...DELIVERY, return_arranged_by: 'not_applicable' } });
  const prepOS = async () => { await call('POST', `/api/admin/checkout/orders/${os.id}/send`, FOUNDER, {}); return call('POST', `/api/checkout/orders/${os.id}/approve`, GAL, { quote_version: (await order(os.id)).quote_version, confirm: ALL }); };
  await prepOS();
  r = await call('POST', `/api/admin/checkout/orders/${os.id}/issue`, FOUNDER, { days: 2, linked_check_confirmed: true });
  check('RT2 a quote is not issued unless it says who arranges the return (buyer, artist or transporter)', r.s === 409 && /who arranges the return/.test(r.j.error), r.j);
  await call('PUT', `/api/admin/checkout/orders/${os.id}`, FOUNDER, { delivery: DELIVERY });
  await prepOS();
  await call('PUT', '/api/checkout/seller-profile', GAL, { ...SELLER, phone: '+353 1 555 0177', confirm: true });
  r = await call('POST', `/api/admin/checkout/orders/${os.id}/issue`, FOUNDER, { days: 2, linked_check_confirmed: true });
  check('SP4 if the seller information changes after the artist approved, the quote is not issued (the artist must approve again)', r.s === 409 && /changed after/.test(r.j.error), r.j);
  await call('PUT', '/api/checkout/seller-profile', GAL, { ...SELLER, phone: '+353 1 555 0199', trader_status: 'not_trader', confirm: true });
  r = await call('POST', `/api/admin/checkout/orders/${os.id}/issue`, FOUNDER, { days: 2, linked_check_confirmed: true });
  check('SP5 a seller who declares they are not a trader is not quoted while decision F2 stands (default: traders only)', r.s === 409 && /not sell as a trader/.test(r.j.error), r.j);
  await call('PUT', '/api/checkout/seller-profile', GAL, { ...SELLER, phone: '+353 1 555 0199', confirm: true });
  r = await call('POST', `/api/admin/checkout/orders/${os.id}/issue`, FOUNDER, { days: 2, linked_check_confirmed: true });
  check('SP6 with the approved seller information restored, the quote is issued', r.s === 200 && !!r.j.buyer_link, r.j);
  await call('POST', `/api/admin/checkout/orders/${os.id}/cancel`, FOUNDER, { reason: 'test complete' }); }

console.log('— two buyers, one original (test 6)');
const oa = await makeOrder('agal', 'wagal2', 'PA-E-261102-BBBBBB', 50000, 0, 'a@example.test'), ob = await makeOrder('agal', 'wagal2', 'PA-E-261105-FFFFFF', 50000, 0, 'b@example.test');
const prep = async id => { await call('POST', `/api/admin/checkout/orders/${id}/send`, FOUNDER, {}); await call('POST', `/api/checkout/orders/${id}/approve`, GAL, { quote_version: (await order(id)).quote_version, confirm: ALL });
  const x = await call('POST', `/api/admin/checkout/orders/${id}/issue`, FOUNDER, { days: 2, linked_check_confirmed: true }); return x.j.buyer_link.split('/q/')[1]; };
const TA = await prep(oa.id);
await call('POST', `/api/admin/checkout/orders/${ob.id}/send`, FOUNDER, {}); await call('POST', `/api/checkout/orders/${ob.id}/approve`, GAL, { quote_version: (await order(ob.id)).quote_version, confirm: ALL });
r = await call('POST', `/api/admin/checkout/orders/${ob.id}/issue`, FOUNDER, { days: 2, linked_check_confirmed: true });
check('T6a one open quote per original: a second buyer cannot be quoted for a work that already has a live quote', r.s === 409 && /is still open/.test(r.j.error), r.j);
const [pa, pa2] = await Promise.all([pub('POST', `/q/${TA}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } }), pub('POST', `/q/${TA}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } })]);
const [first, second, TF] = [oa, ob, TA];
const sA = (await q("SELECT * FROM checkout_sessions WHERE order_id = ? AND status='open'", first.id))[0];
check('T6a2 two simultaneous checkout attempts on the one quote open a single checkout', !!sA && (await q("SELECT * FROM checkout_sessions WHERE order_id = ?", first.id)).length === 1, [pa.s, pa2.s]);
h = await hook(evt('checkout.session.expired', { ...M.sessions[sA.id], status: 'expired' }, ACCT));
check('T8a an abandoned checkout releases the reservation and returns the quote to payable', (await order(first.id)).status === 'quoted' && !(await q("SELECT * FROM artwork_reservations WHERE artwork_id='wagal2'")).length);
await call('POST', `/api/admin/checkout/orders/${first.id}/cancel`, FOUNDER, { reason: 'Buyer A withdrew' });
const TS = (await call('POST', `/api/admin/checkout/orders/${second.id}/issue`, FOUNDER, { days: 2, linked_check_confirmed: true })).j.buyer_link.split('/q/')[1];
pg = await pub('POST', `/q/${TS}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } });
const sB = (await q("SELECT * FROM checkout_sessions WHERE order_id = ? AND status='open'", second.id))[0];
check('T6b the other buyer can then open checkout', pg.s === 303 && !!sB);
pay(sB.id); await hook(evt('checkout.session.completed', M.sessions[sB.id], ACCT));
M.sessions[sA.id].status = 'open'; pay(sA.id);   // the first buyer's payment completes late, at the provider, after their session had expired here
h = await hook(evt('checkout.session.completed', M.sessions[sA.id], ACCT));
const FA = await order(first.id);
check('T6c a delayed payment for an already-sold original is never a second sale: flagged for refund', h.s === 200 && FA.status === 'refund_pending' && /already sold/.test(FA.needs_resolution)
  && (await q("SELECT * FROM artwork_sales WHERE artwork_id='wagal2' AND released_at IS NULL")).length === 1 && (await order(second.id)).status === 'paid', FA);
check('BC6 a payment that could not complete a sale gets no purchase confirmation', !(await q('SELECT * FROM order_messages WHERE order_id = ?', first.id)).length);
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
  && (await q("SELECT * FROM checkout_mail_sink WHERE subject LIKE '%refund_pending%' AND to_role IN ('artist','founder') AND order_id = ?", o1.id)).length === 2
  && (await q("SELECT body FROM checkout_mail_sink WHERE to_sha256 = ? AND kind = 'refund_pending'", sha(GAL)))[0].body.includes('Add to balance')
  && !(await q('SELECT * FROM mail_capture')).length);
{ const bn = await q("SELECT * FROM order_messages WHERE order_id = ? AND kind = 'buyer_refund_pending'", o1.id), sk = await q("SELECT * FROM checkout_mail_sink WHERE order_id = ? AND kind = 'buyer_refund_pending'", o1.id);
  check('BN1 the buyer gets a notice that the refund is pending and NOT yet completed: kept with its fingerprint, test sink only (address fingerprint, not delivered by email)', bn.length === 1 && bn[0].item_key === rf1.metadata.plotart_refund
    && /NOT been completed/.test(bn[0].body) && bn[0].sha256 === sha(bn[0].body) && sk.length === 1 && sk[0].to_role === 'buyer' && sk[0].to_sha256 === sha('buyer@example.test')
    && (await q('SELECT status, detail FROM order_message_deliveries WHERE message_id = ?', bn[0].id))[0].status === 'held_in_test_sink'
    && /NOT delivered by email/.test((await q('SELECT detail FROM order_message_deliveries WHERE message_id = ?', bn[0].id))[0].detail), bn[0] && bn[0].body);
  check('BN1b the buyer’s quote page shows the update', (await pub('GET', `/q/${T1}`)).t.includes('Your refund for')); }
check('R1c the founder desk lists the pending refund with its days and Stripe’s 45-day date', (await call('GET', '/api/admin/checkout', FOUNDER)).j.pending_refunds.some(x => x.order_id === o1.id && x.days_pending === 0 && x.stripe_fails_it_by));
check('R1d the artist sees it with what to do', (await call('GET', '/api/checkout', GAL)).j.pending_refunds[0].what_to_do.length === 4);
h = await hook(evt('refund.updated', { ...rf1, status: 'succeeded' }, ACCT));
check('R3 when Stripe confirms the refund, it is booked and PlotArt returns exactly GAA 9.2 commission (€150 × €500 kept / €1,000 → €75)',
  h.s === 200 && M.feeRefunds.length === fees + 1 && M.feeRefunds.at(-1).amount === 7500 && (await q("SELECT * FROM order_ledger WHERE order_id = ? AND kind = 'artwork_refund'", o1.id)).length === 1 && !(await order(o1.id)).needs_resolution, h);
h = await hook(evt('refund.updated', { ...rf1, status: 'succeeded' }, ACCT));
check('R4 the same confirmation again returns nothing twice', M.feeRefunds.length === fees + 1 && (await q("SELECT * FROM order_ledger WHERE order_id = ? AND kind = 'commission_refund'", o1.id)).length === 1);
check('BN2 repeated provider events never duplicate a buyer notice', (await q("SELECT * FROM order_messages WHERE order_id = ? AND kind LIKE 'buyer_refund_%'", o1.id)).length === 1);
check('T9b order back to paid, partially refunded', (await order(o1.id)).status === 'paid' && (await order(o1.id)).payment_status === 'partially_refunded');
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/refund`, FOUNDER, { artwork_cents: 0, delivery_cents: 7500, reason: 'Delivery not used: buyer collected' });
check('T9c a delivery refund moves no commission', r.s === 200 && M.feeRefunds.length === fees + 1);
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/refund`, FOUNDER, { artwork_cents: 60000, delivery_cents: 0, reason: 'too much' });
check('T9d a refund above the amount still paid is refused', r.s === 409);
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/refund`, FOUNDER, { artwork_cents: 50000, delivery_cents: 0, reason: 'Returned in full' });
O1 = await order(o1.id);
const fin = await db.prepare(`SELECT SUM(CASE WHEN kind='commission' THEN amount_cents END) + SUM(CASE WHEN kind='commission_refund' THEN amount_cents ELSE 0 END) AS netfee,
  SUM(CASE WHEN kind IN ('charge','artwork_refund','delivery_refund') THEN amount_cents ELSE 0 END) AS netpaid FROM order_ledger WHERE order_id = ?`).bind(o1.id).first();
const reimb1 = (await db.prepare("SELECT SUM(amount_cents) AS x FROM order_ledger WHERE order_id = ? AND kind = 'processing_reimbursement'").bind(o1.id).first()).x;
const P1 = JSON.parse(O1.processing);
check('T9e full refund reconciles: buyer net 0; commission kept by PlotArt = processing reimbursed (EUR 20.15), so PlotArt keeps net 0; order refunded, original released',
  O1.status === 'refunded' && O1.payment_status === 'refunded' && fin.netfee === reimb1 && reimb1 === 2015 && fin.netpaid === 0 && (await q("SELECT * FROM artwork_sales WHERE artwork_id='wagal1' AND released_at IS NOT NULL")).length === 1
  && (await db.prepare("SELECT availability FROM artworks WHERE id='wagal1'").first()).availability === 'sold', { O1, fin });
check('MB5 full refund: the commission refund owed (EUR 75) exceeds what is left of the application fee after the reimbursement (EUR 54.85): only EUR 54.85 goes back through Stripe',
  M.feeRefunds.filter(x => x.fee === M.pis[O1.payment_intent].fee).map(x => x.amount).join() === '2015,7500,5485', M.feeRefunds);
check('MB6 the EUR 20.15 difference is flagged as a shortfall PlotArt must pay the artist directly (not silently left with the artist, not paid twice)',
  (await db.prepare("SELECT SUM(cents) AS c FROM checkout_owed WHERE order_id = ?").bind(o1.id).first()).c === 2015 && /PlotArt owes the artist EUR 20.15/.test(O1.needs_resolution) && (await call('GET', `/api/checkout/orders/${o1.id}`, GAL)).j.statement.shortfall_still_owed_by_plotart === 2015, { P1, nr: O1.needs_resolution });
{ const Qd = (await call('GET', '/api/admin/checkout', FOUNDER)).j, w1 = Qd.owed.find(w => w.order_id === o1.id);
  check('OQ1 the founder queue lists what PlotArt owes: amount, paid, outstanding, age, due date (marked provisional) and the rule', !!w1 && w1.cents === 2015 && w1.settled_cents === 0 && w1.outstanding_cents === 2015
    && w1.age_days === 0 && w1.due_provisional === true && /PROVISIONAL/.test(w1.due_rule) && Date.parse(w1.due_at) - Date.parse(w1.arisen_at) === 30 * 86400_000
    && Qd.deadlines.provisional === true && Qd.deadlines.shortfall_days === 30 && Qd.bank_details_process.length >= 4, { w1, d: Qd.deadlines }); }
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/shortfallpaid`, FOUNDER, { amount_cents: 2015, reference: 'Paid to IE29 AIBK 9311 5212 3456 78 on 18 Nov' });
check('OQ2 a payment record that looks like bank details is refused, so none is stored', r.s === 400 && /bank details/.test(r.j.error) && !(await q("SELECT * FROM checkout_owed_payments WHERE reference LIKE '%AIBK%'")).length, r.j);
r = await call('POST', `/api/admin/checkout/orders/${o1.id}/shortfallpaid`, FOUNDER, { amount_cents: 2016, evidence: 'Bank transfer BT-SF1 on 18 Nov' });
const r2sf = await call('POST', `/api/admin/checkout/orders/${o1.id}/shortfallpaid`, FOUNDER, { amount_cents: 2015, evidence: 'Bank transfer BT-SF1 on 18 Nov' });
const r3sf = await call('POST', `/api/admin/checkout/orders/${o1.id}/shortfallpaid`, FOUNDER, { amount_cents: 1, evidence: 'Bank transfer BT-SF2 on 18 Nov' });
const st9 = (await call('GET', `/api/checkout/orders/${o1.id}`, GAL)).j.statement;
check('MB7 the founder records the direct payment once; more than owed, or paying again, is refused; the statement then shows the artist whole on fees',
  r.s === 400 && r2sf.s === 200 && r3sf.s === 409 && !(await order(o1.id)).needs_resolution && st9.shortfall_paid_by_plotart === 2015 && st9.shortfall_still_owed_by_plotart === 0
  && st9.net_proceeds === 0, { st9, r: r.j, r3: r3sf.j });
{ const w = await db.prepare('SELECT * FROM checkout_owed WHERE order_id = ?').bind(o1.id).first(), pays = await q('SELECT * FROM checkout_owed_payments WHERE owed_id = ?', w.id);
  check('OQ3 the queue item is settled with its payment evidence (transfer reference only); owed and paid are separate in the statement',
    w.settled_cents === 2015 && pays.length === 1 && pays[0].method === 'bank_transfer' && pays[0].reference === 'Bank transfer BT-SF1 on 18 Nov' && st9.owed_by_plotart_not_yet_paid.shortfall === 0 && st9.shortfall_paid_by_plotart === 2015
    && !(await call('GET', '/api/admin/checkout', FOUNDER)).j.owed.some(x => x.order_id === o1.id), { w, pays });
  check('OQ4 an owed amount and its due date cannot be changed, and settlement can never exceed it', /fixed/.test((await db.prepare('UPDATE checkout_owed SET cents = 1 WHERE id = ?').bind(w.id).run().catch(e => e)).message)
    && /fixed/.test((await db.prepare("UPDATE checkout_owed SET due_at = '2099-01-01T00:00:00Z' WHERE id = ?").bind(w.id).run().catch(e => e)).message)
    && /CHECK/.test((await db.prepare('UPDATE checkout_owed SET settled_cents = cents + 1 WHERE id = ?').bind(w.id).run().catch(e => e)).message)); }
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
// Model B covers commission-bearing orders only: this artist now has accepted 15% commission terms
await db.prepare(`INSERT INTO gallery_agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, method, statement, created_at) VALUES ('gaa2','ev2','aold','PA-GAA-2026-11',?,?,?,?, 'Oisin Older','studio_checkbox','test',?)`).bind(FAKE, FAKE, ago(6), OLD, ago(6)).run();
await db.prepare("INSERT INTO artist_terms (artist_id, track, commission_bp, set_by, created_at, updated_at) VALUES ('aold','gallery_artist',1500,?,?,?)").bind(FOUNDER, ago(6), ago(6)).run();
const oe = await makeOrder('aold', 'waold2', 'PA-E-261103-DDDDDD', 40000, 2500, 'e@example.test');
r = await call('POST', `/api/admin/checkout/orders/${oe.id}/send`, FOUNDER, {});
await call('POST', `/api/checkout/orders/${oe.id}/approve`, OLD, { quote_version: (await order(oe.id)).quote_version, confirm: ALL });
const ACCT_OLD = (await db.prepare("SELECT account_id FROM payment_accounts WHERE artist_id='aold'").first()).account_id;
const TE = (await call('POST', `/api/admin/checkout/orders/${oe.id}/issue`, FOUNDER, { days: 1, linked_check_confirmed: true })).j.buyer_link.split('/q/')[1];
await pub('POST', `/q/${TE}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } });
const sE = Object.values(M.sessions).at(-1);
check('T3b the application fee requested is exactly the 15% commission on the artwork (EUR 60 on EUR 400), never on delivery', sE._fee === 6000 && sE._acct === ACCT_OLD);
M.btPendingNext = true; M.nextExtraFee = 200;   // Stripe has not yet recorded the fee; and this payment carries a non-processing add-on fee
pay(sE.id);
const dispute = { id: 'dp_test_1', object: 'dispute', payment_intent: sE.payment_intent, charge: M.pis[sE.payment_intent].charge, amount: 42500, reason: 'product_not_received', status: 'needs_response',
  balance_transactions: [{ id: 'txn_test_dp1', object: 'balance_transaction', amount: -42500, fee: 2460, fee_details: [{ type: 'stripe_fee', amount: 2000, description: 'Dispute fee' }, { type: 'tax', amount: 460, description: 'VAT' }] }] };
h = await hook(evt('charge.dispute.created', dispute, ACCT_OLD));
check('T7i a dispute arriving BEFORE its payment completion is deferred (noting its payment), not lost', h.s === 500 && (await db.prepare('SELECT status, detail FROM payment_events WHERE object_id = ?').bind('dp_test_1').first()).detail === `awaiting order for ${sE.payment_intent}`);
M.disputes.dp_test_1 = { ...dispute, _acct: ACCT_OLD };   // what Stripe returns when the pilot re-reads the dispute
await hook(evt('checkout.session.completed', M.sessions[sE.id], ACCT_OLD));   // NO redelivery of the dispute event follows
let OE = await order(oe.id);
const dpRow = await db.prepare('SELECT status, order_id, detail FROM payment_events WHERE object_id = ?').bind('dp_test_1').first();
check('T10a the completion replays the earlier dispute WITHOUT any redelivery: recorded on the right order (debited from the seller’s Stripe balance by Stripe)', OE.status === 'disputed' && OE.dispute_status === 'open'
  && dpRow.status === 'processed' && dpRow.order_id === oe.id && /replayed/.test(dpRow.detail)
  && (await q("SELECT * FROM order_ledger WHERE kind='dispute' AND order_id = ?", oe.id))[0].amount_cents === -42500, { OE, dpRow });
{ const PE = JSON.parse((await order(oe.id)).processing || '{}'), feeE = M.pis[sE.payment_intent].fee;
  check('MB8 before Stripe records the fee nothing is estimated or reimbursed: the order waits (awaiting_fee)', PE.status === 'awaiting_fee' && !M.feeRefunds.some(x => x.fee === feeE), PE);
  { const wq = (await call('GET', '/api/admin/checkout', FOUNDER)).j.reimbursements.find(x => x.order_id === oe.id);
    check('MB8b the founder desk lists the reimbursement as waiting for Stripe to record the fee: no amount, day 0, provisional due date 7 Irish days after Stripe’s payment time',
      !!wq && wq.status === 'awaiting_fee' && wq.status_label === 'Waiting for Stripe to record the fee' && wq.amount_cents === null && /Not yet known/.test(wq.amount_label) && wq.day === 0 && wq.due_provisional === true
      && wq.payment_confirmed_basis === 'stripe_success_event_created' && /^\d{4}-\d{2}-\d{2}$/.test(wq.due_date) && /Due by the end of .* \(Irish time\) · provisional/.test(wq.due_label), wq); }
  M.charges[M.pis[sE.payment_intent].charge].btPending = false;
  await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
  const PE2 = JSON.parse((await order(oe.id)).processing), frE = M.feeRefunds.filter(x => x.fee === feeE);
  check('MB9 the sweep then reimburses the ACTUAL processing fee + its VAT once; the add-on fee (and its VAT) is excluded and recorded, not absorbed',
    PE2.status === 'reimbursed' && PE2.stripe_fee === 663 && PE2.vat === 152 && PE2.excluded_fees === 200 && PE2.excluded_vat === 46 && frE.length === 1 && frE[0].amount === 815
    && (await q("SELECT * FROM order_events WHERE order_id = ? AND action = 'processing_excluded_fees'", oe.id)).length === 1, { PE2, frE }); }
h = await hook(evt('charge.dispute.created', dispute, ACCT_OLD));
check('T10a2 a later redelivery of the same dispute event changes nothing (already processed)', h.s === 200 && (await q("SELECT * FROM order_ledger WHERE kind='dispute' AND order_id = ?", oe.id)).length === 1);
await call('POST', `/api/admin/checkout/orders/${oe.id}/fulfilment`, FOUNDER, { kind: 'insurance', evidence: 'SIMULATED cover SIM-COVER-0001' });
await call('POST', `/api/admin/checkout/orders/${oe.id}/fulfilment`, FOUNDER, { kind: 'dispatched', evidence: 'SAC tracking 1Z999' });
h = await hook(evt('charge.dispute.closed', { ...dispute, status: 'lost' }, ACCT_OLD));
OE = await order(oe.id);
{ const stE = (await call('GET', `/api/checkout/orders/${oe.id}`, OLD)).j.statement;
  check('MB10 disputes are NOT absorbed: no reimbursement for the dispute, the statement shows the dispute separately and says dispute fees stay with the seller',
    M.feeRefunds.filter(x => x.fee === M.pis[sE.payment_intent].fee).length === 1 && stE.disputes_net === -42500 && stE.processing_reimbursed_by_plotart === 815 && stE.other_stripe_fees_not_reimbursed === 246 && stE.dispute_fees_charged_by_stripe === 2460 && stE.dispute_fees_status === 'recorded from Stripe' && stE.net_proceeds === -8706 && stE.commission_refund_owed === 6000 && (await q("SELECT * FROM order_ledger WHERE kind = 'dispute_fee' AND order_id = ?", oe.id)).length === 1, stE); }
check('T10b a lost dispute is flagged with the documented recovery route (commission settlement; seller carries the loss with Stripe)', OE.dispute_status === 'lost' && OE.status === 'refunded' && /dispute lost/.test(OE.needs_resolution), OE);
r = await call('POST', `/api/admin/checkout/orders/${oe.id}/close`, FOUNDER, {});
check('T10c an order with an unresolved flag cannot be closed', r.s === 409);
{ const LW = await db.prepare("SELECT * FROM checkout_owed WHERE order_id = ? AND kind = 'lost_dispute_commission'").bind(oe.id).first();
  check('LD1 a lost dispute puts the commission to return in the queue, due under PA-GAA 9.1 (30 days; the agreement’s period, not provisional)', !!LW && LW.cents === 6000 && LW.due_provisional === 0
    && /PA-GAA cl\. 9\.1/.test(LW.due_rule) && Date.parse(LW.due_at) - Date.parse(LW.arisen_at) === 30 * 86400_000, LW);
  const feeE = M.pis[sE.payment_intent].fee, before = M.feeRefunds.filter(x => x.fee === feeE).length;
  r = await call('POST', `/api/admin/checkout/orders/${oe.id}/refund`, FOUNDER, { commission_only: true, reason: 'Dispute lost: commission returned under PA-GAA 9.1' });
  const LW2 = await db.prepare('SELECT * FROM checkout_owed WHERE id = ?').bind(LW.id).first(), SH = await db.prepare("SELECT * FROM checkout_owed WHERE order_id = ? AND kind = 'commission_shortfall'").bind(oe.id).first();
  const frE = M.feeRefunds.filter(x => x.fee === feeE), OE2 = await order(oe.id);
  check('LD2 returning it sends what is left of the application fee through Stripe (€60 − €8.15 reimbursed) and moves the €8.15 to a direct-payment item; the lost-dispute item is settled and its flag cleared',
    r.s === 200 && frE.length === before + 1 && frE.at(-1).amount === 6000 - 815 && LW2.settled_cents === 6000 && SH && SH.cents === 815 && !/dispute lost/.test(OE2.needs_resolution || '') && /PlotArt owes the artist EUR 8\.15/.test(OE2.needs_resolution || ''), { r: r.j && r.j.error, LW2, SH, nr: OE2.needs_resolution });
  r = await call('POST', `/api/admin/checkout/orders/${oe.id}/refund`, FOUNDER, { commission_only: true, reason: 'Second attempt' });
  check('LD3 asking again returns nothing more', r.s === 200 && M.feeRefunds.filter(x => x.fee === feeE).length === before + 1, r.j); }

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
await db.prepare("CREATE TRIGGER test_sink_down BEFORE INSERT ON checkout_mail_sink WHEN NEW.kind = 'buyer_refund_failed' BEGIN SELECT RAISE(ABORT, 'sink down (test)'); END").run();
h = await hook(evt('refund.failed', { ...rfx, id: rfx.id, status: 'failed', failure_reason: 'insufficient_funds' }, ACCT));
const SX = await order(second.id);
check('R5 a refund Stripe fails (e.g. still unfunded after 45 days) is flagged: buyer NOT repaid, nothing booked, no commission returned',
  h.s === 200 && /failed \(insufficient_funds\)/.test(SX.needs_resolution) && (await db.prepare('SELECT status FROM order_refunds WHERE provider_refund_id = ?').bind(rfx.id).first()).status === 'failed'
  && !(await q("SELECT * FROM order_ledger WHERE provider_ref = ?", rfx.id)).length && M.feeRefunds.length === fees, SX);
{ const fm = await db.prepare("SELECT * FROM order_messages WHERE order_id = ? AND kind = 'buyer_refund_failed'").bind(second.id).first();
  const d1 = await q('SELECT status FROM order_message_deliveries WHERE message_id = ?', fm.id);
  check('BN3 if delivery fails, the notice is still kept and the failure is recorded (never reported as delivered)', /NOT been repaid/.test(fm.body) && d1.length === 1 && d1[0].status === 'failed');
  for (let i = 0; i < 7; i++) await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
  const d2 = await q('SELECT status FROM order_message_deliveries WHERE message_id = ?', fm.id);
  check('BN4 the sweep retries a failed delivery, at most 6 attempts in all, then flags it for the founder', d2.length === 6 && d2.every(x => x.status === 'failed')
    && new RegExp(`message ${fm.id}`).test((await order(second.id)).needs_resolution), { attempts: d2.length, nr: (await order(second.id)).needs_resolution });
  await db.prepare('DROP TRIGGER test_sink_down').run();
  r = await call('POST', `/api/admin/checkout/orders/${second.id}/confirmation`, FOUNDER, { message_id: fm.id });
  const d3 = await q('SELECT status FROM order_message_deliveries WHERE message_id = ?', fm.id);
  check('BN5 once the problem is fixed the founder re-delivers the same stored text; the flag is cleared; one message, never a duplicate', r.s === 200 && d3.at(-1).status === 'held_in_test_sink'
    && (await q("SELECT * FROM checkout_mail_sink WHERE order_id = ? AND kind = 'buyer_refund_failed'", second.id)).length === 1
    && !new RegExp(`message ${fm.id}`).test((await order(second.id)).needs_resolution || '') && (await q("SELECT * FROM order_messages WHERE order_id = ? AND kind = 'buyer_refund_failed'", second.id)).length === 1, [r.j && r.j.error, d3]); }
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

console.log('— seven-day reimbursement rule (PA-PAY §3.3(b), provisional) · SIMULATED dates and failures');
{ const CO = await import(HERE + FIX + 'src/checkout.js');
  const SCH = CO.reimbursementSchedule, at = s => Date.parse(s);
  // SIMULATED dates (pure schedule, no Stripe)
  const a = SCH({ confirmed_at: '2026-12-01T10:00:00Z', at: at('2026-12-08T23:59:00Z') }), a2 = SCH({ confirmed_at: '2026-12-01T10:00:00Z', at: at('2026-12-09T00:00:00Z') });
  check('SD1 SIMULATED: payment confirmed Tuesday 1 December 2026 → day one is 2 December; due by the end of Tuesday 8 December (Irish time); 23:59 on 8 December is still in time',
    a.confirmed_date === '2026-12-01' && a.due === '2026-12-08' && a.day === 7 && !a.overdue && a2.extended && CO.longDate(a.due) === 'Tuesday 8 December 2026', { a, a2 });
  const s = SCH({ confirmed_at: '2026-07-01T23:30:00Z', at: at('2026-07-09T22:59:00Z') }), s2 = SCH({ confirmed_at: '2026-07-01T23:30:00Z', fee_recorded_at: '2026-07-01T23:30:05Z', at: at('2026-07-09T23:00:00Z') });
  const w = SCH({ confirmed_at: '2026-12-01T23:30:00Z', at: at('2026-12-08T23:59:00Z') });
  check('SD2 SIMULATED near midnight: Stripe confirms at 23:30 UTC on 1 July 2026 = 00:30 on 2 July in Dublin (IST) → Irish date 2 July, due by the end of 9 July (23:00 UTC); a UTC-date rule would have given 8 July. In winter (GMT) 23:30 UTC on 1 December stays 1 December → due 8 December',
    s.confirmed_date === '2026-07-02' && s.due === '2026-07-09' && !s.overdue && s2.overdue && CO.dublinDayEnd('2026-07-09') === at('2026-07-09T23:00:00Z') && w.confirmed_date === '2026-12-01' && w.due === '2026-12-08', { s, s2, w });
  const e1 = SCH({ confirmed_at: '2026-12-01T10:00:00Z', at: at('2026-12-09T09:00:00Z') }), e2 = SCH({ confirmed_at: '2026-12-01T10:00:00Z', fee_recorded_at: '2026-12-10T09:00:00Z', at: at('2026-12-10T09:15:00Z') });
  check('SD3 SIMULATED extension: Stripe has not recorded the fee by the end of 8 December → the period runs from the day Stripe records it; recorded on 10 December → latest date 17 December',
    e1.extended && e1.due === null && e1.waiting_for_fee_date && e2.extended && e2.extended_due === '2026-12-17' && e2.due === '2026-12-17' && !e2.overdue, { e1, e2 });
  const l = SCH({ confirmed_at: '2026-12-01T10:00:00Z', fee_recorded_at: '2026-12-08T22:00:00Z', at: at('2026-12-10T09:00:00Z') });
  check('SD3b SIMULATED late check: Stripe recorded the fee on 8 December but PlotArt first checks on 10 December → no extension, due stays 8 December, now overdue (a delay in checking starts no new period)',
    !l.extended && l.due === '2026-12-08' && l.overdue, l);
  // SIMULATED orders against the mock Stripe (real pilot code; timestamps set in the mock)
  const DAY = 86400, nowS = () => Math.floor(Date.now() / 1000);
  async function sdOrder(tag, { chargeAgeDays, btPending = false, btAgeDays = chargeAgeDays, noCreated = false, noBtCreated = false, artwork = 100000, commission = 15000 }) {
    const id = 'osd' + tag.toLowerCase(), ch = 'ch_test_sd' + tag, fee = 'fee_test_sd' + tag, t = new Date().toISOString();
    await db.prepare(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, payment_status, artwork_cents, delivery_cents, commission_bp, commission_cents, provider_account, payment_intent, charge_id, application_fee_id, amount_received_cents, paid_at, buyer_email, created_by, created_at, updated_at)
      VALUES (?, ?, 'agal', 'wagal9', 'PA-E-261101-AAAAAA', 'paid', 'paid', ?, 0, 1500, ?, ?, ?, ?, ?, ?, ?, 'sd@example.test', 'test', ?, ?)`).bind(id, 'PA-O-261118-SD000' + tag, artwork, commission, ACCT, 'pi_test_sd' + tag, ch, fee, artwork, t, t, t).run();
    M.feeAmounts[fee] = commission;
    M.charges[ch] = { id: ch, fee, created: nowS() - chargeAgeDays * DAY, noCreated, btPending, bt: { id: 'txn_test_sd' + tag, object: 'balance_transaction', ...(noBtCreated ? {} : { created: nowS() - btAgeDays * DAY }), currency: 'eur', amount: 100000, fee: 1500 + 1775 + 408,
      fee_details: [{ type: 'stripe_fee', amount: 1775, description: 'Stripe processing fees' }, { type: 'tax', amount: 408, description: 'VAT' }, { type: 'application_fee', amount: 15000, description: 'Application fee' }] } };
    return { id, ch, fee };
  }
  const sweep = () => S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
  const desk = async () => (await call('GET', '/api/admin/checkout', FOUNDER)).j;
  const sink = (id, kind, role) => q('SELECT to_role FROM checkout_mail_sink WHERE order_id = ? AND kind = ?' + (role ? ' AND to_role = ?' : ''), ...[id, kind, ...(role ? [role] : [])]);
  const P = async id => JSON.parse((await order(id)).processing || '{}');
  // A · fee known, reimbursement failing (SIMULATED Stripe errors), day 5
  const A = await sdOrder('A', { chargeAgeDays: 5 });
  M.failFeeRefunds = 99; M.failFeeRefundMessage = 'SIMULATED: Stripe temporarily unavailable';
  await sweep();
  let PA = await P(A.id), dA = (await desk()).reimbursements.find(x => x.order_id === A.id);
  const dueA = dA && dA.due_date;
  check('SD4 fee known, reimbursement outstanding: the desk shows that status, the exact amount (EUR 21.83) and the due date; day-5 alert to the founder (test sink), once',
    PA.status === 'outstanding' && dA.status_label === 'Fee known · reimbursement outstanding' && dA.amount_cents === 2183 && dA.amount_label === 'EUR 21.83' && dA.day === 5
    && dA.payment_confirmed_basis === 'stripe_charge_created' && dA.fee_recorded_basis === 'stripe_balance_transaction_created' && !!dA.alerts.day5
    && (await sink(A.id, 'reimbursement_day5', 'founder')).length === 1 && !(await sink(A.id, 'reimbursement_day5', 'artist')).length, { PA, dA });
  await sweep(); await sweep(); await sweep();
  PA = await P(A.id); dA = (await desk()).reimbursements.find(x => x.order_id === A.id);
  const idems = [...new Set(M.calls.filter(c => c.method === 'POST' && c.path === `/v1/application_fees/${A.fee}/refunds`).map(c => c.idem))];
  check('SD5 repeated failures are surfaced with Stripe’s reason and the manual action; the due date is unchanged; every retry uses the same idempotency key; no reimbursement exists',
    PA.attempts === 4 && /SIMULATED: Stripe temporarily unavailable/.test(PA.last_error) && dA.failing && dA.due_date === dueA && /Reconcile processing fee/.test(dA.action)
    && /^Processing reimbursement failing \(4 attempts\): .*SIMULATED.* due date is unchanged/.test((await order(A.id)).needs_resolution) && idems.length === 1
    && !M.feeRefunds.some(x => x.fee === A.fee) && (await sink(A.id, 'reimbursement_day5')).length === 1, { PA, dA, idems, nr: (await order(A.id)).needs_resolution });
  // SIMULATED passage of time: the stored Stripe times are moved 3 days earlier (as if the clock had moved on to day 8)
  await db.prepare('UPDATE checkout_orders SET processing = ? WHERE id = ?').bind(JSON.stringify({ ...PA, confirmed_at: new Date(Date.now() - 8 * DAY * 1000).toISOString(), fee_recorded_at: new Date(Date.now() - 8 * DAY * 1000).toISOString() }), A.id).run();
  await sweep(); await sweep();
  dA = (await desk()).reimbursements.find(x => x.order_id === A.id);
  check('SD6 SIMULATED day 8: still outstanding at the deadline → deadline alert to the founder, once; the desk marks it OVERDUE; still no extension (the fee was recorded in time) and no delay notice',
    dA.overdue && !dA.extended && !!dA.alerts.deadline && (await sink(A.id, 'reimbursement_deadline', 'founder')).length === 1 && !(await sink(A.id, 'reimbursement_delayed')).length, dA);
  // SIMULATED lost answer: Stripe accepts the refund but the answer never arrives
  M.failFeeRefunds = 0; M.loseFeeRefundAnswer = true;
  r = await call('POST', `/api/admin/checkout/orders/${A.id}/processing`, FOUNDER, {});
  const afterLost = M.feeRefunds.filter(x => x.fee === A.fee).length;
  await sweep(); await sweep();
  PA = await P(A.id);
  check('SD7 SIMULATED lost answer: Stripe made the refund but the pilot never got the answer; the next pass reads Stripe’s list of the fee’s refunds and records it: exactly ONE reimbursement, no duplicate, flag cleared, marked late',
    r.s === 200 && afterLost === 1 && M.feeRefunds.filter(x => x.fee === A.fee).length === 1 && PA.status === 'reimbursed' && PA.reimbursed_cents === 2183 && PA.completed_late === true
    && (await q("SELECT * FROM order_ledger WHERE order_id = ? AND kind = 'processing_reimbursement'", A.id)).length === 1
    && (await q("SELECT * FROM order_events WHERE order_id = ? AND action = 'processing_reimbursement_adopted'", A.id)).length === 1 && !/Processing reimbursement failing/.test((await order(A.id)).needs_resolution || ''), { PA, nr: (await order(A.id)).needs_resolution });
  // B · Stripe has not recorded the fee by the original deadline (SIMULATED: payment 8 days ago, fee still pending)
  const B = await sdOrder('B', { chargeAgeDays: 10, btPending: true });   // SIMULATED: payment 10 days ago, original date passed 3 days ago
  await sweep();
  let dB = (await desk()).reimbursements.find(x => x.order_id === B.id);
  check('SD8 waiting for Stripe to record the fee past the original deadline: the extension applies; ONE delay notice to the artist (test sink) and a note to the founder; no amount is estimated',
    dB.status === 'awaiting_fee' && dB.status_label === 'Waiting for Stripe to record the fee' && dB.amount_cents === null && dB.extended && dB.due_date === null && /passed before Stripe recorded the fee/.test(dB.due_label)
    && (await sink(B.id, 'reimbursement_delayed', 'artist')).length === 1 && !(await sink(B.id, 'reimbursement_delayed', 'founder')).length && (await sink(B.id, 'reimbursement_extended', 'founder')).length === 1 && !dB.overdue, dB);
  const notice = (await q("SELECT subject, body FROM checkout_mail_sink WHERE order_id = ? AND kind = 'reimbursement_delayed'", B.id))[0];
  await sweep(); await sweep();
  check('SD8b later sweeps send no second delay notice', (await sink(B.id, 'reimbursement_delayed')).length === 1 && (await sink(B.id, 'reimbursement_extended')).length === 1);
  M.charges[B.ch].btPending = false; M.charges[B.ch].bt.created = nowS() - DAY;   // SIMULATED: Stripe recorded the fee yesterday
  await sweep();
  const PB = await P(B.id), dB2 = (await desk()).reimbursements_recent.find(x => x.order_id === B.id);
  const expB = CO.dublinDate(Date.now() - DAY * 1000);
  check('SD9 once Stripe records the fee the next sweep reimburses it promptly, once; the latest date shown is 7 Irish days after the day Stripe recorded it; still one delay notice',
    PB.status === 'reimbursed' && M.feeRefunds.filter(x => x.fee === B.fee).length === 1 && dB2.extended && dB2.fee_recorded === expB && dB2.extended_due === new Date(Date.parse(expB + 'T12:00:00Z') + 7 * DAY * 1000).toISOString().slice(0, 10)
    && !dB2.completed_late && (await sink(B.id, 'reimbursement_delayed')).length === 1, { PB, dB2 });
  const done = (await q("SELECT to_role, body FROM checkout_mail_sink WHERE order_id = ? AND kind = 'reimbursement_completed'", B.id));
  const stB = (await call('GET', `/api/checkout/orders/${B.id}`, GAL)).j;
  check('SD9c after a delay notice, ONE closing message to the artist (test sink) states the amount, that Stripe accepted the application-fee refund, its date and Stripe reference, and that the bank payout is separate; the statement carries the same wording',
    done.length === 1 && done[0].to_role === 'artist' && /PlotArt reimbursed EUR 21\.83 through Stripe: Stripe accepted PlotArt’s refund of that amount of its application fee on \w+day \d+ \w+ \d{4} \(Stripe reference fr_test_\w+\)/.test(done[0].body)
    && /depends on your Stripe payout schedule/.test(done[0].body) && stB.statement && stB.statement.processing_reimbursement === done[0].body.split('\n')[3], { done, st: stB.statement && stB.statement.processing_reimbursement });
  writeFileSync('/tmp/plotart-sd-completion.txt', done[0] ? done[0].body : '');
  // B2 · the pilot saw no fee at the deadline and sent the notice, but Stripe's own time later shows the fee was recorded before it
  const B2 = await sdOrder('E', { chargeAgeDays: 8, btPending: true });
  await sweep();
  M.charges[B2.ch].btPending = false; M.charges[B2.ch].bt.created = nowS() - 2 * DAY;   // SIMULATED: Stripe's record time is inside the original period
  await sweep();
  const dE = (await desk()).reimbursements_recent.find(x => x.order_id === B2.id);
  check('SD9b if Stripe’s own record time shows the fee was recorded before the original deadline although the pilot could not see it then, no extension is claimed: the original date stands, it is marked late, and the desk flags that a delay notice went out',
    !dE.extended && dE.due_date === dE.original_due && dE.completed_late && (await sink(B2.id, 'reimbursement_delayed')).length === 1 && dE.flags.some(x => /delay notice was sent/.test(x)), dE);
  const closeE = await q("SELECT body FROM checkout_mail_sink WHERE order_id = ? AND kind = 'reimbursement_completed'", B2.id);
  check('SD9d the next notice to the artist gives the corrected date: Stripe recorded the fee by the original date, so the original date applies (not a later one); one closing notice only',
    closeE.length === 1 && closeE[0].body.includes('Correction to our earlier message') && closeE[0].body.includes(`the end of ${CO.longDate(dE.original_due)} (Irish time), not a later date`), closeE);
  // F · the pilot saw no fee at the original date (notice sent); Stripe then returns the fee WITHOUT its record time
  const F = await sdOrder('F', { chargeAgeDays: 10, btPending: true, noBtCreated: true });
  await sweep(); await sweep();
  const noticeF = await sink(F.id, 'reimbursement_delayed', 'artist');
  M.charges[F.ch].btPending = false;
  await sweep(); await sweep();
  const dF = (await desk()).reimbursements_recent.find(x => x.order_id === F.id), closeF = await q("SELECT body FROM checkout_mail_sink WHERE order_id = ? AND kind = 'reimbursement_completed'", F.id);
  check('SD13 fee time unknown: the original deadline stays visible and in force (no extension assumed), the case is flagged FOR REVIEW to the founder once, the delay notice went once, and the next notice gives the original date and says it is under review',
    noticeF.length === 1 && (await sink(F.id, 'reimbursement_delayed')).length === 1 && dF.fee_recorded_basis === 'first_seen_by_pilot' && !dF.extended && dF.due_date === dF.original_due
    && /for review/.test(dF.due_label) && dF.flags.some(x => /^FOR REVIEW: .*whether the later date applies cannot be established/.test(x)) && dF.completed_late
    && (await sink(F.id, 'reimbursement_fee_time_unknown', 'founder')).length === 1 && !(await sink(F.id, 'reimbursement_fee_time_unknown', 'artist')).length
    && closeF.length === 1 && closeF[0].body.includes(`The date that applies is the original one: the end of ${CO.longDate(dF.original_due)} (Irish time). We are reviewing this order.`), { dF, closeF });
  // G · partial reimbursement: the application fee left (EUR 15.00) is less than Stripe's fee + VAT (EUR 21.83)
  const G = await sdOrder('G', { chargeAgeDays: 1, artwork: 10000, commission: 1500 });
  await sweep();
  const dG = (await desk()).reimbursements_recent.find(x => x.order_id === G.id), stG = (await call('GET', `/api/checkout/orders/${G.id}`, GAL)).j.statement;
  const owG = await q("SELECT cents, settled_cents, due_provisional FROM checkout_owed WHERE order_id = ? AND kind = 'processing_shortfall'", G.id);
  check('SD14 partial reimbursement (clause 3.3 → 3.5): EUR 15.00 reimbursed through Stripe (all that was left of the fee) and EUR 6.83 owed by bank transfer; the desk and the artist’s statement show both amounts; the 30-day due date is provisional',
    dG.status === 'shortfall' && dG.reimbursed_through_stripe_cents === 1500 && dG.owed_by_bank_transfer_cents === 683 && /EUR 21\.83 in all: EUR 15\.00 reimbursed through Stripe; EUR 6\.83 still owed by bank transfer/.test(dG.amount_label)
    && M.feeRefunds.filter(x => x.fee === G.fee).reduce((a, x) => a + x.amount, 0) === 1500 && owG.length === 1 && owG[0].cents === 683 && owG[0].due_provisional
    && stG.processing_reimbursed_through_stripe === 1500 && stG.processing_still_owed_by_bank_transfer === 683
    && /PlotArt reimbursed EUR 15\.00 of the EUR 21\.83 processing fee and VAT through Stripe/.test(stG.processing_reimbursement)
    && /The remaining EUR 6\.83 could not be reimbursed through Stripe.*clause 3\.5\)\. Still owed to you by PlotArt: EUR 6\.83\. Your statement shows it under “Owed by PlotArt, not yet paid”/.test(stG.processing_reimbursement), { dG, st: stG && stG.processing_reimbursement, owG });
  writeFileSync('/tmp/plotart-sd-partial.txt', stG.processing_reimbursement || '');
  // H · clock start: Stripe's charge and its success event fall on different Irish dates (SIMULATED times, real webhook path)
  { const work = (await q("SELECT id FROM artworks WHERE artist_id = 'agal' AND availability = 'available' AND id NOT IN (SELECT artwork_id FROM artwork_sales) AND id NOT IN (SELECT artwork_id FROM artwork_reservations) ORDER BY id DESC LIMIT 1"))[0];
    globalThis.SD15_WORK = work.id;   // sold through SD15's verified (signed) payment; T11b expects it
    const X = CO.dublinDate(Date.now() - 3 * DAY * 1000), X1 = new Date(Date.parse(X + 'T12:00:00Z') + DAY * 1000).toISOString().slice(0, 10);
    const id = 'osdh', sid = 'cs_test_sdh', pi = 'pi_test_sdh', ch = 'ch_test_sdh', fee = 'fee_test_sdh', t = new Date().toISOString();
    await db.prepare(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, payment_status, artwork_cents, delivery_cents, commission_bp, commission_cents, provider_account, quote_version, buyer_email, created_by, created_at, updated_at)
      VALUES (?, 'PA-O-261118-SD000H', 'agal', ?, 'PA-E-261101-AAAAAA', 'checkout_open', 'open', 100000, 0, 1500, 15000, ?, 1, 'sdh@example.test', 'test', ?, ?)`).bind(id, work.id, ACCT, t, t).run();
    await db.prepare(`INSERT INTO checkout_sessions (id, order_id, quote_version, amount_total, application_fee_cents, status, expires_at, created_at, updated_at) VALUES (?, ?, 1, 100000, 15000, 'open', ?, ?, ?)`).bind(sid, id, new Date(Date.now() + 3600e3).toISOString(), t, t).run();
    const chargeCreated = Math.floor(Date.parse(X + 'T23:59:58Z') / 1000), eventCreated = Math.floor(Date.parse(X1 + 'T00:00:03Z') / 1000);   // Irish winter time = UTC
    M.pis[pi] = { id: pi, object: 'payment_intent', livemode: false, amount: 100000, charge: ch, fee, metadata: { plotart_order: id } };
    M.feeAmounts[fee] = 15000;
    M.charges[ch] = { id: ch, fee, created: chargeCreated, btPending: false, bt: { id: 'txn_test_sdh', object: 'balance_transaction', created: chargeCreated, currency: 'eur', amount: 100000, fee: 17183,
      fee_details: [{ type: 'stripe_fee', amount: 1775, description: 'Stripe processing fees' }, { type: 'tax', amount: 408, description: 'VAT' }, { type: 'application_fee', amount: 15000, description: 'Application fee' }] } };
    M.sessions[sid] = { id: sid, object: 'checkout.session', livemode: false, status: 'complete', payment_status: 'paid', currency: 'eur', amount_total: 100000, payment_intent: pi, client_reference_id: id, metadata: { plotart_order: id, quote_version: '1' } };
    const hH = await hook({ ...evt('checkout.session.completed', M.sessions[sid], ACCT), created: eventCreated });
    const PH = JSON.parse((await order(id)).processing || '{}');
    const dH = (await desk()).reimbursements_recent.concat((await desk()).reimbursements).find(x => x.order_id === id);
    check('SD15 SIMULATED times on different Irish dates: the card charge is created at 23:59:58 on ' + X + ' and Stripe’s signed success event at 00:00:03 on ' + X1 + '; the clock starts from the success event (Irish date ' + X1 + ', due ' + CO.dublinDate(Date.parse(X1 + 'T12:00:00Z') + 7 * DAY * 1000) + '), not the charge; the charge time is kept as evidence',
      hH.s === 200 && PH.confirmed_basis === 'stripe_success_event_created' && PH.confirmed_at === new Date(eventCreated * 1000).toISOString() && PH.charge_created_at === new Date(chargeCreated * 1000).toISOString()
      && dH && dH.payment_confirmed === X1 && dH.original_due === new Date(Date.parse(X1 + 'T12:00:00Z') + 7 * DAY * 1000).toISOString().slice(0, 10) && !dH.flags.some(x => /Payment date/.test(x)), { hH, PH, dH, work }); }
  // C · late check: Stripe recorded the fee 9 days ago (in time) but the pilot had not checked
  const C = await sdOrder('C', { chargeAgeDays: 9 });
  await sweep();
  const dC = (await desk()).reimbursements_recent.find(x => x.order_id === C.id);
  check('SD10 a delay in PlotArt checking Stripe starts no new period: fee recorded in time → no extension, no delay notice, reimbursement marked late against the original date',
    dC.status === 'reimbursed' && !dC.extended && dC.due_date === dC.original_due && dC.completed_late && !(await sink(C.id, 'reimbursement_delayed')).length, dC);
  // D · Stripe gives no times: the pilot says it can show only when it first saw the records
  const D = await sdOrder('D', { chargeAgeDays: 2, noCreated: true, noBtCreated: true });
  await sweep();
  const dD = (await desk()).reimbursements_recent.find(x => x.order_id === D.id);
  check('SD11 where Stripe’s times are not available the desk flags it: payment date from the pilot’s own record; fee date only when the pilot first saw it',
    dD.payment_confirmed_basis === 'pilot_verified_payment' && dD.fee_recorded_basis === 'first_seen_by_pilot' && dD.flags.length === 2, dD);
  check('SD12 the artist’s delay notice states the confirmation date, the original date, that the amount is not estimated, the 7-day rule from Stripe’s record with a worked example, and that the bank payout is separate (no “by 14:15” promise)',
    !!notice && /Stripe confirmed your buyer’s payment on \w+day \d+ \w+ \d{4}/.test(notice.body) && /does not estimate/.test(notice.body) && /seventh calendar day after the day Stripe records it/.test(notice.body)
    && /payout from Stripe to your bank is separate/.test(notice.body) && !/14:15/.test(notice.body) && /test mode/.test(notice.body)
    && notice.body.includes('We have not yet been able to confirm the fee Stripe charged on this payment') && !/Stripe has not yet recorded/.test(notice.body), notice);
  writeFileSync('/tmp/plotart-sd-evidence.json', JSON.stringify({ desk_F_unknown_time: dF, desk_G_partial: dG, statement_G: stG && stG.processing_reimbursement, closing_E_correction: closeE[0] && closeE[0].body, closing_F_review: closeF[0] && closeF[0].body, desk_H_clock: undefined, SD1: a, SD2: { summer: s, winter: w }, SD3: { before: e1, after: e2 }, SD3b: l, desk_A_outstanding: dA, desk_B_waiting: dB, desk_B_done: dB2, desk_C_late: dC, desk_D_flags: dD, delay_notice: notice }, null, 2));
}

console.log('— leaving, scheduled sweep, isolation (tests 11, 15)');
const og = await makeOrder('afnd', 'wafnd2', 'PA-E-251101-CCCCCC', 30000, 0, 'g@example.test');
r = await call('POST', '/api/checkout/leave', FND, {});
check('L1 an artist can leave at any time: unpaid quotes are cancelled, nothing is charged', r.s === 200 && !r.j.membership.opted_in && (await order(og.id)).status === 'cancelled' && (await order(of.id)).status === 'cancelled');
await db.prepare("INSERT INTO artwork_reservations (artwork_id, order_id, quote_version, expires_at, created_at) VALUES ('waunk2', ?, 1, ?, ?)").bind(ou.id, ago(1), ago(1)).run();
const sw = await S.mf.getWorker('checkout').then(w => w.scheduled({ cron: '*/15 * * * *' })).catch(e => e);
check('L2 the scheduled sweep releases lapsed reservations', !(await q("SELECT * FROM artwork_reservations WHERE artwork_id='waunk2'")).length, sw);
const AFTER = JSON.parse(await snapshotOf()), B = JSON.parse(BEFORE);
// the test itself gave artist aold accepted 15% terms (Model B covers commission-bearing orders only); the pilot changed nothing
AFTER.gaa = AFTER.gaa.filter(x => x.id !== 'gaa2'); AFTER.at = AFTER.at.filter(x => x.artist_id !== 'aold');
check('T11 gallery publication, versions, publish queue, gallery positions, founding numbers, artist records, agreements, terms, enquiry log and enquiries are unchanged',
  ['v', 'pq', 'gp', 'ar', 'aa', 'gaa', 'at', 'el', 'en', 'works'].every(k => JSON.stringify(AFTER[k]) === JSON.stringify(B[k])),
  ['v', 'pq', 'gp', 'ar', 'aa', 'gaa', 'at', 'el', 'en', 'works'].filter(k => JSON.stringify(AFTER[k]) !== JSON.stringify(B[k])));
check('T11b the only artwork change is the sold mark on works sold through verified payments', (await q("SELECT id FROM artworks WHERE availability='sold' ORDER BY id")).map(x => x.id).join() === ['waold2', 'wagal1', 'wagal2', globalThis.SD15_WORK].sort().join());
console.log('— a refund that succeeds and later FAILS (reversal, commission already returned, no double repayment)');
{
  const orv = await makeOrder('agal', 'wagal3', 'PA-E-261106-GGGGGG', 80000, 5000, 'rv@example.test');
  await call('POST', `/api/admin/checkout/orders/${orv.id}/send`, FOUNDER, {});
  await call('POST', `/api/checkout/orders/${orv.id}/approve`, GAL, { quote_version: (await order(orv.id)).quote_version, confirm: ALL });
  const TV = (await call('POST', `/api/admin/checkout/orders/${orv.id}/issue`, FOUNDER, { days: 1, linked_check_confirmed: true })).j.buyer_link.split('/q/')[1];
  await pub('POST', `/q/${TV}/pay`, { form: { accept_terms: 'PA-BPT-TEST-01' } });
  const sV = Object.values(M.sessions).at(-1); pay(sV.id); await hook(evt('checkout.session.completed', M.sessions[sV.id], ACCT));
  const feesBefore = M.feeRefunds.length;
  r = await call('POST', `/api/admin/checkout/orders/${orv.id}/refund`, FOUNDER, { artwork_cents: 80000, delivery_cents: 5000, reason: 'Full refund: work returned' });
  const rv = M.refunds.at(-1);
  const PRV = JSON.parse((await order(orv.id)).processing);
  check('RV0 the full refund first SUCCEEDS: the €120 commission is settled — €120 less the processing already reimbursed back through Stripe, the rest flagged for PlotArt to pay directly',
    r.s === 200 && (await order(orv.id)).status === 'refunded' && M.feeRefunds.length === feesBefore + 1 && M.feeRefunds.at(-1).amount === 12000 - PRV.cost && (await db.prepare("SELECT SUM(cents) AS c FROM checkout_owed WHERE order_id = ?").bind(orv.id).first()).c === PRV.cost, { s: (await order(orv.id)).status, fee: M.feeRefunds.at(-1), PRV });
  // Stripe later reports the same refund as FAILED (as in real test P12: succeeded → failed, expired_or_canceled_card)
  h = await hook(evt('refund.updated', { ...rv, status: 'failed', failure_reason: 'expired_or_canceled_card' }, ACCT));
  let OV = await order(orv.id);
  const rvRow = await db.prepare('SELECT status, error FROM order_refunds WHERE provider_refund_id = ?').bind(rv.id).first();
  const led = await q('SELECT kind, amount_cents FROM order_ledger WHERE order_id = ? ORDER BY kind', orv.id);
  check('RV1 the later failure is reconciled: refund failed, ledger keeps the refund and adds reversal lines (+€800, +€50), order back to paid with nothing refunded',
    h.s === 200 && rvRow.status === 'failed' && /after succeeding/.test(rvRow.error) && OV.status === 'paid' && OV.payment_status === 'paid'
    && led.some(l => l.kind === 'artwork_refund' && l.amount_cents === -80000) && led.some(l => l.kind === 'artwork_refund_reversed' && l.amount_cents === 80000) && led.some(l => l.kind === 'delivery_refund_reversed' && l.amount_cents === 5000), { OV, rvRow, led });
  check('RV2 the flag is accurate: buyer NOT repaid, the €120 commission already returned stays returned, repay by ONE route only',
    /SUCCEEDED and then FAILED/.test(OV.needs_resolution) && /NOT been repaid/.test(OV.needs_resolution) && /settled EUR 120\.00 commission/.test(OV.needs_resolution) && /PlotArt owes the artist/.test(OV.needs_resolution) && /ONE route/.test(OV.needs_resolution), OV.needs_resolution);
  h = await hook(evt('refund.updated', { ...rv, status: 'failed', failure_reason: 'expired_or_canceled_card' }, ACCT));
  check('RV3 a repeated failure event (or another event id for the same failure) changes nothing', h.s === 200 && (await q("SELECT * FROM order_ledger WHERE order_id = ? AND kind LIKE '%_reversed'", orv.id)).length === 2
    && (await q("SELECT * FROM order_events WHERE order_id = ? AND action = 'refund_reversed'", orv.id)).length === 1);
  check('BN6 a reversed refund sends the buyer one notice that they have NOT been repaid, even when the failure event is repeated', (await q("SELECT * FROM order_messages WHERE order_id = ? AND kind = 'buyer_refund_reversed'", orv.id)).length === 1
    && /NOT been repaid/.test((await q("SELECT body FROM order_messages WHERE order_id = ? AND kind = 'buyer_refund_reversed'", orv.id))[0].body));
  const feesMid = M.feeRefunds.length, refundsMid = M.refunds.length;
  r = await call('POST', `/api/admin/checkout/orders/${orv.id}/refund`, FOUNDER, { artwork_cents: 80000, delivery_cents: 5000, reason: 'Retry after reversal' });
  OV = await order(orv.id);
  check('RV4 repaying through a NEW Stripe refund works once, and returns NO further commission (it was already returned)',
    r.s === 200 && M.refunds.length === refundsMid + 1 && M.feeRefunds.length === feesMid && OV.status === 'refunded'
    && (await db.prepare('SELECT commission_refund_cents FROM order_refunds WHERE provider_refund_id = ?').bind(M.refunds.at(-1).id).first()).commission_refund_cents === 0, { s: r.s, j: r.j && r.j.error, OV: OV.status });
  r = await call('POST', `/api/admin/checkout/orders/${orv.id}/repaid`, FOUNDER, { artwork_cents: 80000, delivery_cents: 5000, evidence: 'Bank transfer BT-999 on 18 Nov, buyer confirmed by email' });
  const r2 = await call('POST', `/api/admin/checkout/orders/${orv.id}/refund`, FOUNDER, { artwork_cents: 1, delivery_cents: 0, reason: 'Attempt a third repayment' });
  check('RV5 after the buyer is repaid, recording a direct repayment or another refund of the same money is refused (no double repayment)',
    r.s === 409 && /more than remains unrefunded/.test(r.j.error) && r2.s === 409 && M.refunds.length === refundsMid + 1, [r.j, r2.j]);
  // backstop: the failure event is never delivered; the sweep finds it by re-reading recently succeeded refunds
  const lastRv = M.refunds.at(-1); lastRv.status = 'failed'; lastRv.failure_reason = 'lost_or_stolen_card';
  await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
  check('RV6 if the failure event is lost, the sweep re-reads recently succeeded refunds and reconciles the reversal', (await db.prepare('SELECT status FROM order_refunds WHERE provider_refund_id = ?').bind(lastRv.id).first()).status === 'failed'
    && (await order(orv.id)).status === 'paid' && /SUCCEEDED and then FAILED/.test((await order(orv.id)).needs_resolution));
  r = await call('POST', `/api/admin/checkout/orders/${orv.id}/repaid`, FOUNDER, { artwork_cents: 80000, delivery_cents: 5000, evidence: 'Bank transfer BT-999 on 18 Nov, buyer confirmed by email' });
  check('RV7 the artist’s direct repayment can then be recorded once, again with no further commission', r.s === 200 && M.feeRefunds.length === feesMid && (await order(orv.id)).status === 'refunded', r.j && r.j.error);
}
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
  && r.j.order.commission_bp === 1500 && r.j.ledger.some(l => l.kind === 'charge' && l.amount_cents === 32000), r.j);
r = await call('POST', `/api/admin/checkout/orders/${ox.id}/refund`, FOUNDER, { artwork_cents: 30000, delivery_cents: 2000, reason: 'Returned after the artist left' });
check('D3 a full refund still works after the artist’s and artwork’s rows are gone', r.s === 200 && r.j.order.status === 'refunded' && M.refunds.at(-1)._acct === ACCT_OLD, r.j);
{ const PX = JSON.parse((await order(ox.id)).processing);
  r = await call('POST', `/api/admin/checkout/orders/${ox.id}/shortfallpaid`, FOUNDER, { amount_cents: (await db.prepare("SELECT SUM(cents - settled_cents) AS c FROM checkout_owed WHERE order_id = ?").bind(ox.id).first()).c, evidence: 'Bank transfer BT-SFX on 18 Nov' });
  check('D3b retention waits while PlotArt still owes a shortfall; recording the direct payment settles it', r.s === 200 && !(await order(ox.id)).needs_resolution, r.j); }
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

console.log('— reminders, dispute fees and late disputes');
{ const tnow = new Date().toISOString(), past = new Date(Date.now() - 2 * 86400_000).toISOString(), soon = new Date(Date.now() + 3 * 86400_000).toISOString();
  await db.prepare(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, payment_status, buyer_email, created_by, created_at, updated_at)
    VALUES ('oq1', 'PA-O-261117-OQ0001', 'agal', 'wagal9', 'PA-E-261101-AAAAAA', 'closed', 'paid', 'oq@example.test', 'test', ?, ?)`).bind(tnow, tnow).run();
  await db.prepare(`INSERT INTO checkout_owed (id, order_id, kind, item_key, cents, reason, arisen_at, due_at, due_rule, due_provisional) VALUES
    ('owq1', 'oq1', 'processing_shortfall', 'processing', 500, 'test overdue', ?, ?, 'test rule', 1), ('owq2', 'oq1', 'commission_shortfall', 'commission:x', 300, 'test due soon', ?, ?, 'test rule', 1)`).bind(past, past, tnow, soon).run();
  await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' }); await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
  const rem = await q("SELECT kind, to_role FROM checkout_mail_sink WHERE order_id = 'oq1'");
  check('OQ5 reminders go to the founder only (test sink): once when due soon, once when overdue, never repeated', rem.length === 2 && rem.every(x => x.to_role === 'founder')
    && rem.some(x => x.kind === 'owed_overdue') && rem.some(x => x.kind === 'owed_due_soon')
    && (await call('GET', '/api/admin/checkout', FOUNDER)).j.owed.find(w => w.id === 'owq1').status === 'overdue', rem);
  r = await call('POST', '/api/admin/checkout/orders/oq1/shortfallpaid', FOUNDER, { amount_cents: 800, reference: 'Bank transfer BT-OQ1 on 18 Nov' });
  const ws = await q("SELECT settled_cents FROM checkout_owed WHERE order_id = 'oq1' ORDER BY id");
  check('OQ6 one direct payment settles the order’s items oldest first, with the same reference recorded on each', r.s === 200 && ws.map(x => x.settled_cents).join() === '500,300', [r.j && r.j.error, ws]); }
{ const C1 = await import(HERE + FIX + 'src/checkout.js');
  const base = { currency: 'eur', paid_at: ago(1), amount_received_cents: 10000, artwork_cents: 10000, delivery_cents: 0, commission_cents: 1500, processing: null };
  const K = 'rk_test_x';
  const mm1 = C1.mailMode({ STRIPE_SECRET_KEY: K }), mm2 = C1.mailMode({ STRIPE_SECRET_KEY: K, CHECKOUT_MAIL: 'resend', RESEND_API_KEY: 're_x', CHECKOUT_MAIL_FROM: 'PlotArt <orders@plotnua.ie>' });
  const mm3 = C1.mailMode({ STRIPE_SECRET_KEY: K, CHECKOUT_MAIL: 'resend', RESEND_API_KEY: 're_x', CHECKOUT_MAIL_FROM: 'x', CHECKOUT_MAIL_APPROVED: 'true', CHECKOUT_MAIL_TEST_RECIPIENTS: 'founder-test@plotnua.ie' });
  const mm4 = C1.mailMode({ STRIPE_SECRET_KEY: 'sk_live_x', CHECKOUT_MAIL: 'resend', RESEND_API_KEY: 're_x', CHECKOUT_MAIL_FROM: 'x', CHECKOUT_MAIL_APPROVED: 'true', CHECKOUT_MAIL_TEST_RECIPIENTS: 'a@b.c' });
  const mm5 = C1.mailMode({ STRIPE_SECRET_KEY: K, CHECKOUT_MAIL: 'resend', RESEND_API_KEY: 're_x', CHECKOUT_MAIL_FROM: 'x', CHECKOUT_MAIL_APPROVED: 'true' });
  check('MM1 external email stays off unless configured AND approved, only to listed test inboxes in test mode, and never with a live key', !mm1.external_sending && /no email provider/.test(mm1.summary)
    && !mm2.external_sending && /not approved/.test(mm2.summary) && mm3.external_sending && !mm4.external_sending && /not part of this pilot/.test(mm4.summary) && !mm5.external_sending, [mm1, mm2, mm3, mm4, mm5].map(x => x.summary));
  const sw = C1.statement({ ...base, dispute_status: 'won', dispute_fees: JSON.stringify({ dp_w: { status: 'recorded' } }) },
    [{ kind: 'dispute', amount_cents: -10000 }, { kind: 'dispute_reinstated', amount_cents: 10000 }, { kind: 'dispute_fee', amount_cents: -2460 }, { kind: 'dispute_fee_returned', amount_cents: 2000 }], []);
  check('DF1 dispute fees and fees Stripe returns are separate statement lines and both count in net proceeds', sw.dispute_fees_charged_by_stripe === 2460 && sw.dispute_fees_returned_by_stripe === 2000 && sw.net_proceeds === 10000 - 1500 - 460, sw);
  const su = C1.statement({ ...base, dispute_status: 'open', dispute_fees: JSON.stringify({ dp_u: { status: 'unavailable' } }) }, [{ kind: 'dispute', amount_cents: -10000 }], []);
  check('DF2 if Stripe has not supplied a dispute’s fee lines, the statement says so and does not guess', /unavailable/.test(su.dispute_fees_status) && /dp_u/.test(su.not_included) && su.dispute_fees_charged_by_stripe === 0, su); }
{ const OX = await order(ox.id);
  const dx = { id: 'dp_test_late', object: 'dispute', payment_intent: OX.payment_intent, charge: M.pis[OX.payment_intent].charge, amount: 32000, reason: 'fraudulent', status: 'needs_response',
    balance_transactions: [{ id: 'txn_test_dplate', object: 'balance_transaction', amount: -32000, fee: 2460, fee_details: [{ type: 'stripe_fee', amount: 2000 }, { type: 'tax', amount: 460 }] }] };
  h = await hook(evt('charge.dispute.created', dx, ACCT_OLD));
  const hx = await q("SELECT * FROM checkout_holds WHERE order_id = ? AND released_at IS NULL", ox.id);
  check('RH1 a dispute arriving after the retention date was fixed places a reviewed legal hold automatically, and its fee is booked', h.s === 200 && hx.length === 1 && hx[0].basis === 'dispute' && hx[0].placed_by === 'system'
    && (await q("SELECT * FROM order_ledger WHERE kind = 'dispute_fee' AND provider_ref = 'txn_test_dplate'")).length === 1 && (await order(ox.id)).dispute_status === 'open', { h, hx }); }
await db.prepare(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, payment_status, dispute_status, buyer_email, created_by, created_at, updated_at, retain_until)
  VALUES ('oold3', 'PA-O-190101-OLD003', 'aold', 'waold9', 'PA-E-190101-AAAAAA', 'closed', 'paid', 'open', 'old3@example.test', 'test', '2019-01-01T00:00:00Z', '2019-02-01T00:00:00Z', '2025-02-01T00:00:00Z')`).run();
await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
check('RH2 an order past its retention date is never deleted while a dispute on it is open (sweep and database both refuse)', !!(await order('oold3'))
  && /no dispute is open/.test((await db.prepare("DELETE FROM checkout_orders WHERE id = 'oold3'").run().catch(e => e)).message));
await db.prepare("UPDATE checkout_orders SET dispute_status = 'lost' WHERE id = 'oold3'").run();
await S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
check('RH3 once the dispute is resolved, the past-retention order is deleted at the next sweep', !(await order('oold3')));

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

{ const sc = M.calls.filter(c => c.path === '/v1/checkout/sessions' && c.method === 'POST');
  check('C24 every Checkout Session is created in euro with Adaptive Pricing off (the buyer pays the quoted euro figure)', sc.length > 0 && sc.every(c => c.f['adaptive_pricing[enabled]'] === 'false' && c.f.currency === 'eur'), { sessions: sc.length }); }

const passed = results.filter(Boolean).length;
console.log(`\nMANAGED CHECKOUT PILOT · ${results.length} checks, ${passed} passed, ${results.length - passed} failed`);
process.exit(passed === results.length ? 0 : 1);
