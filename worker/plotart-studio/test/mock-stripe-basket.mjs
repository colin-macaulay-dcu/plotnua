// Mock Stripe for the multi-artist basket tests: PlotArt's platform (no Stripe-Account header) and connected artist accounts.
// Stateful, test-mode objects only. Shared by prove-basket.mjs and prove-basket-e2e-offline.mjs.
export const M = { accounts: {}, v2accounts: {}, customers: {}, sessions: {}, pms: {}, pis: {}, charges: {}, feeAmounts: {}, feeRefunds: [], refunds: [], calls: [], idem: {}, n: 0,
  fail500: 0, cardBehaviour: {} };
const nid = p => `${p}_test_${(++M.n).toString(36).padStart(6, '0')}`;
const flat = body => Object.fromEntries(new URLSearchParams(body || ''));
const ok = o => new Response(JSON.stringify(o), { status: 200, headers: { 'Content-Type': 'application/json' } });
const err = (m, s = 400, extra = {}) => new Response(JSON.stringify({ error: { message: m, ...extra } }), { status: s, headers: { 'Content-Type': 'application/json' } });
const piView = p => ({ ...p, latest_charge: p.charge ? { id: p.charge, object: 'charge', application_fee: p.fee, amount_captured: p.amount_received,
  amount_refunded: M.refunds.filter(r => r.payment_intent === p.id && r.status === 'succeeded').reduce((a, r) => a + (Number.isFinite(r.amount) ? r.amount : p.amount_received), 0) } : null, _acct: undefined });
export async function stripe(req) {
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
  if ((mm = u.pathname.match(/^\/v1\/customers\/(cus_test_\w+)$/)) && req.method === 'GET') { const c = M.customers[mm[1]]; return c ? ok(c.deleted ? { id: c.id, deleted: true } : c) : err('no such customer', 404); }
  if ((mm = u.pathname.match(/^\/v1\/customers\/(cus_test_\w+)$/)) && req.method === 'DELETE') { if (!M.customers[mm[1]]) return err('no such customer', 404); M.customers[mm[1]].deleted = true; for (const pm of Object.values(M.pms)) if (pm.customer === mm[1] && !pm._acct) pm.customer = null; return ok({ id: mm[1], deleted: true }); }
  if (u.pathname === '/v1/checkout/sessions' && req.method === 'POST') {
    if (acct) return err('the basket card page belongs on the platform account');
    if (f.mode !== 'setup') return err('setup mode expected');
    if (Object.keys(f).some(k => k.startsWith('payment_method_types'))) return err('Received unknown parameter: payment_method_types');
    const sid = nid('cs');
    const s = { id: sid, object: 'checkout.session', mode: 'setup', livemode: false, url: `${M.hostedBase || 'https://checkout.stripe.test'}/c/setup/${sid}`, success_url: f.success_url, cancel_url: f.cancel_url, status: 'open', customer: f.customer,
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
export function enterCard(sessionId, behaviour = {}) {
  const s = M.sessions[sessionId]; const pm = { id: nid('pm'), object: 'payment_method', livemode: false, customer: s.customer };
  M.pms[pm.id] = pm; M.cardBehaviour[pm.id] = behaviour; s.status = 'complete'; s.setup_intent = nid('seti'); s._pm = pm.id; return s;
}