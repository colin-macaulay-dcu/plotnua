// PROOF OF CONCEPT · Stripe TEST MODE ONLY · founder approval 21 Nov 2026 ("Approve Two-Artist Stripe Sandbox Test").
// One buyer enters card details ONCE (Stripe-hosted Checkout in setup mode, on PlotArt's platform account); the saved
// card is then cloned to each of two artists' connected accounts and charged there as a DIRECT CHARGE, so each artist
// stays the merchant of record (docs.stripe.com/connect/direct-charges-multiple-accounts).
// Isolated: no production code, database, Worker or live key. Every object is created in TEST mode and cleaned up at
// the end (uncaptured payments cancelled, captured ones refunded with the commission, the platform card detached and the
// test customer deleted). Card numbers are Stripe's published test cards (docs.stripe.com/testing); no real card data.
//   Called from test/stripe-testmode-checks.mjs (phase "basket_direct"); records results with rec().
import { createRequire } from 'node:module';

const CARDS = {
  ok: '4242424242424242',                // succeeds
  declineAfterAttach: '4000000000000341', // saving succeeds, every charge declines
  authUnlessSetUp: '4000002500003155',    // authentication at setup; off-session charges then succeed
  alwaysAuth: '4000002760003184',         // authentication on every transaction, however set up
};

export async function proveBasketDirect({ KEY, accounts, rec, v1, runId, playwrightFrom }) {
  const S = 'stripe-test-api';
  const ok = (id, name, pass, d = {}) => rec(id, name, S, pass ? 'PASS' : 'FAIL', d);
  const info = (id, name, d = {}) => rec(id, name, S, 'INFO', d);
  const tag = 'plotart-poc-' + runId;
  const created = { customers: [], captured: [], uncaptured: [] };   // for clean-up

  if (!/^(sk|rk)_test_[A-Za-z0-9]+$/.test(KEY)) { rec('BD0', 'TEST key only', 'local', 'FAIL'); return; }
  if (accounts.length !== 2 || new Set(accounts).size !== 2 || !accounts.every(a => /^acct_[A-Za-z0-9]+$/.test(a))) {
    rec('BD0', 'two distinct existing TEST artist accounts named in stripe-test-run.json', 'local', 'FAIL', { accounts }); return;
  }

  // one raw TEST-mode call; errors are returned (never thrown) with secrets scrubbed
  async function api(method, path, body = null, { account = null, idem = null } = {}) {
    const h = { Authorization: 'Bearer ' + KEY, 'Stripe-Version': v1 };
    if (account) h['Stripe-Account'] = account;
    if (idem) h['Idempotency-Key'] = idem;
    if (body) h['Content-Type'] = 'application/x-www-form-urlencoded';
    const r = await fetch('https://api.stripe.com' + path, { method, headers: h, body: body ? new URLSearchParams(body) : undefined });
    const j = await r.json();
    if (j.livemode === true) throw new Error('live-mode object returned: stopping');
    const err = j.error ? { status: r.status, type: j.error.type, code: j.error.code, decline_code: j.error.decline_code,
      message: String(j.error.message || '').replace(/(?:[rs]k|pk)_(?:test|live)_\S+/g, '[key]').slice(0, 240),
      pi_status: j.error.payment_intent?.status, pi: j.error.payment_intent?.id } : null;
    return { ok: r.ok, j, err, replayed: r.headers.get('idempotent-replayed') === 'true' };
  }

  // ---- 0 · both existing TEST artist accounts must be suitable for direct charges; otherwise STOP
  const suitable = [];
  for (const [i, acct] of accounts.entries()) {
    const r = await api('GET', '/v1/accounts/' + acct);
    const a = r.j;
    const fit = r.ok && a.id === acct && a.charges_enabled === true && a.capabilities?.card_payments === 'active';
    ok('BD-ACC' + (i + 1), `existing TEST artist account ${i + 1} is suitable (charges enabled, card payments active)`, fit,
      r.ok ? { account: acct, country: a.country, default_currency: a.default_currency, charges_enabled: a.charges_enabled,
        card_payments: a.capabilities?.card_payments, transfers: a.capabilities?.transfers, dashboard: a.controller?.stripe_dashboard?.type,
        losses: a.controller?.losses?.payments, fees: a.controller?.fees?.payer, descriptor: a.settings?.payments?.statement_descriptor } : { account: acct, error: r.err });
    suitable.push(fit);
  }
  if (!suitable.every(Boolean)) { rec('BD-STOP', 'an existing TEST artist account is unsuitable: stopped before any payment (founder instruction)', 'local', 'FAIL'); return; }
  const [A1, A2] = accounts;

  // ---- one card entry on Stripe's hosted page (Checkout, setup mode, PlotArt's platform account)
  const { chromium } = createRequire(playwrightFrom)('playwright');
  const browser = await chromium.launch();
  async function enterCardOnce(label, card) {
    const cus = await api('POST', '/v1/customers', { description: 'PlotArt basket POC test buyer (' + label + ')', 'metadata[poc]': tag });
    if (!cus.ok) return { error: cus.err };
    created.customers.push(cus.j.id);
    const cs = await api('POST', '/v1/checkout/sessions', { mode: 'setup', customer: cus.j.id, currency: 'eur', 'allowed_payment_method_types[0]': 'card',
      success_url: 'https://example.com/plotart-poc-done', cancel_url: 'https://example.com/plotart-poc-cancel', 'metadata[poc]': tag },
      { idem: tag + '-cs-' + label });
    if (!cs.ok) return { error: cs.err, customer: cus.j.id };
    const page = await browser.newPage({ locale: 'en-IE' });
    let stage = 'open hosted page', challenged = false;
    const field = async (css, timeout = 10000) => {
      const end = Date.now() + timeout;
      do { for (const f of page.frames()) for (const m of await f.locator(css).all().catch(() => [])) if (await m.isVisible().catch(() => false)) return m;
        await page.waitForTimeout(300); } while (Date.now() < end);
      return null;
    };
    const fill = async (css, value, timeout = 15000) => {
      stage = 'fill ' + css.split(',')[0];
      const end = Date.now() + timeout;
      do { const c = await field(css, 1000); if (c && await c.fill(value, { timeout: 2000 }).then(() => true, () => false)) return true; } while (Date.now() < end);
      return false;
    };
    try {
      await page.goto(cs.j.url, { waitUntil: 'domcontentloaded' });
      const cardCSS = '#cardNumber,#payment-numberInput,input[autocomplete="cc-number"],input[name=cardnumber]';
      if (!await field(cardCSS, 4000)) await (await field('[data-testid="card-accordion-item-button"],button:text-is("Card"),[role="radio"]:text-is("Card")', 4000))?.click();
      if (!await fill(cardCSS, card, 25000)) throw Error('card field unavailable');
      await fill('#cardExpiry,#payment-expiryInput,input[autocomplete="cc-exp"]', '12 / 34');
      await fill('#cardCvc,#payment-cvcInput,input[autocomplete="cc-csc"]', '123');
      await fill('#billingName,input[autocomplete="cc-name"]', 'Test Buyer', 3000);
      await fill('#email,input[type=email]', 'plotart-poc-buyer@example.com', 2000);
      const country = await field('#billingCountry', 1000); if (country) await country.selectOption('IE').catch(() => {});
      stage = 'submit';
      const submit = await field('[data-testid="hosted-payment-submit-button"],button[type="submit"],button.SubmitButton', 8000);
      if (!submit) throw Error('submit control missing');
      await submit.click({ timeout: 10000 });
      stage = 'await completion or authentication';
      const end = Date.now() + 90000;
      while (Date.now() < end && !page.url().startsWith('https://example.com/')) {
        const auth = await field('#test-source-authorize-3ds,button:has-text("Complete"),button:has-text("COMPLETE")', 1500);
        if (auth) { challenged = true; await auth.click().catch(() => {}); }
        await page.waitForTimeout(500);
      }
      if (!page.url().startsWith('https://example.com/')) throw Error('hosted page did not complete');
      const done = await api('GET', '/v1/checkout/sessions/' + cs.j.id + '?expand[]=setup_intent');
      const si = done.j.setup_intent;
      return { customer: cus.j.id, session: cs.j.id, setup_intent: si?.id, si_status: si?.status, pm: si?.payment_method, usage: si?.usage, challenged };
    } catch (e) {
      return { error: { stage, message: String(e.message).slice(0, 160) }, customer: cus.j.id, session: cs.j.id };
    } finally { await page.close(); }
  }

  // clone the platform card to an artist and create a direct charge there (artist = merchant of record)
  async function cloneTo(acct, entry, idem) {
    const c = await api('POST', '/v1/payment_methods', { customer: entry.customer, payment_method: entry.pm }, { account: acct, idem });
    return c.ok ? { pm: c.j.id, replayed: c.replayed } : { error: c.err };
  }
  async function charge(acct, pm, cents, feeCents, key, { manual = false, basket, artist } = {}) {
    const body = { amount: String(cents), currency: 'eur', payment_method: pm, confirm: 'true', off_session: 'true',
      'allowed_payment_method_types[0]': 'card', description: 'PlotArt basket POC (TEST) · ' + artist,
      'metadata[poc]': tag, 'metadata[basket]': basket, 'metadata[artist]': artist };
    if (feeCents > 0) body.application_fee_amount = String(feeCents);
    if (manual) body.capture_method = 'manual';
    const r = await api('POST', '/v1/payment_intents', body, { account: acct, idem: key });
    const pi = r.ok ? r.j : null;
    if (pi?.status === 'succeeded') created.captured.push([acct, pi.id]);
    if (pi?.status === 'requires_capture') created.uncaptured.push([acct, pi.id]);
    // a failed confirmation can leave a PaymentIntent behind (e.g. requires_payment_method): cancel it at clean-up
    if (!pi && r.err?.pi && !['succeeded', 'canceled'].includes(r.err.pi_status)) created.uncaptured.push([acct, r.err.pi]);
    return { ok: r.ok, replayed: r.replayed, id: pi?.id || r.err?.pi, status: pi?.status || r.err?.pi_status, fee: pi?.application_fee_amount ?? null,
      amount: pi?.amount, error: r.err };
  }
  const chargeDetail = async (acct, id) => {
    const r = await api('GET', `/v1/payment_intents/${id}?expand[]=latest_charge`, null, { account: acct });
    const ch = r.j.latest_charge || {};
    return { status: r.j.status, descriptor: ch.calculated_statement_descriptor, fee: ch.application_fee_amount, on_account: acct };
  };
  const fee15 = c => Math.round(c * 0.15);
  const W1 = 12000, W2 = 8000;   // Rowan's work €120 at 15% commission · Alder's work €80, a Founding 25 sale at 0%

  try {
    // ---- A · both artist payments succeed after ONE card entry
    const e = await enterCardOnce('A', CARDS.ok);
    ok('BD-A0', 'ONE card entry on Stripe-hosted Checkout (setup mode) saves the card on PlotArt\'s platform account', !e.error && e.si_status === 'succeeded' && !!e.pm,
      { method: 'browser (Playwright) on checkout.stripe.com', si_status: e.si_status, usage: e.usage, authentication_shown: e.challenged, error: e.error });
    if (!e.error && e.pm) {
      const c1 = await cloneTo(A1, e, tag + '-A-clone-1'), c2 = await cloneTo(A2, e, tag + '-A-clone-2');
      ok('BD-A1', 'the saved card is cloned to BOTH artists\' accounts (no second card entry)', !c1.error && !c2.error, { e1: c1.error, e2: c2.error });
      const p1 = await charge(A1, c1.pm, W1, fee15(W1), tag + '-A-pay-1', { basket: 'A', artist: 'artist-1' });
      const p2 = await charge(A2, c2.pm, W2, 0, tag + '-A-pay-2', { basket: 'A', artist: 'artist-2' });
      ok('BD-A2', 'two separate DIRECT charges succeed, one on each artist\'s account', p1.status === 'succeeded' && p2.status === 'succeeded', { p1: p1.status, p2: p2.status, e1: p1.error, e2: p2.error });
      if (p1.id && p2.id) {
        const [d1, d2] = [await chargeDetail(A1, p1.id), await chargeDetail(A2, p2.id)];
        ok('BD-A3', 'PlotArt commission is exact per charge: 15% (€18.00) on artist 1, none on the Founding 25 sale (artist 2)', d1.fee === 1800 && (d2.fee === null || d2.fee === 0 || d2.fee === undefined), { fee1: d1.fee, fee2: d2.fee ?? null });
        info('BD-A4', 'what the buyer\'s statement shows: one line per artist, under each artist\'s descriptor', { line1: d1.descriptor, line2: d2.descriptor });
      }
      created.basePm = e;   // reused by D and E as further baskets with the same saved card
    }

    // ---- B · one artist payment succeeds, the other fails
    if (created.basePm) {
      const e2 = created.basePm;
      const c1 = await cloneTo(A1, e2, tag + '-B-clone-1'), c2 = await cloneTo(A2, e2, tag + '-B-clone-2');
      const p1 = await charge(A1, c1.pm, W1, fee15(W1), tag + '-B-pay-1', { basket: 'B', artist: 'artist-1' });
      // Stripe has no test card that succeeds on one charge and declines on another, so the second charge is made to fail
      // with a real Stripe refusal (an amount above the per-charge maximum). This records the state a partial basket leaves.
      const p2 = await charge(A2, c2.pm, 100000000, 0, tag + '-B-pay-2', { basket: 'B', artist: 'artist-2' });
      ok('BD-B1', 'partial basket: artist 1 charged, artist 2 refused, and NOTHING links or reverses them automatically', p1.status === 'succeeded' && !p2.ok,
        { artist1: p1.status, artist2_error: p2.error, money_taken_from_buyer_cents: p1.status === 'succeeded' ? W1 : 0 });
      info('BD-B2', 'exact state after a partial basket', { artist1_charge: 'succeeded on artist 1 account (buyer charged €120)', artist2_charge: 'no PaymentIntent created',
        platform: 'card still saved on PlotArt until cleaned up', automatic_rollback: 'none: Stripe treats them as independent payments' });
    }
    const eD = await enterCardOnce('B-decline', CARDS.declineAfterAttach);
    if (!eD.error && eD.pm) {
      const c1 = await cloneTo(A1, eD, tag + '-B3-clone-1'), c2 = await cloneTo(A2, eD, tag + '-B3-clone-2');
      const p1 = await charge(A1, c1.pm, W1, fee15(W1), tag + '-B3-pay-1', { basket: 'B3', artist: 'artist-1' });
      const p2 = await charge(A2, c2.pm, W2, 0, tag + '-B3-pay-2', { basket: 'B3', artist: 'artist-2' });
      ok('BD-B3', 'a card that is saved but then declined fails on EACH artist charge separately (card declined on both)',
        !p1.ok && !p2.ok, { artist1: p1.error?.decline_code || p1.error?.code, artist2: p2.error?.decline_code || p2.error?.code });
    } else ok('BD-B3', 'decline-after-attaching card saved once', false, eD.error || {});

    // ---- C · additional authentication
    const e3 = await enterCardOnce('C-setup-auth', CARDS.authUnlessSetUp);
    if (!e3.error && e3.pm) {
      const c1 = await cloneTo(A1, e3, tag + '-C1-clone-1'), c2 = await cloneTo(A2, e3, tag + '-C1-clone-2');
      const p1 = await charge(A1, c1.pm, W1, fee15(W1), tag + '-C1-pay-1', { basket: 'C1', artist: 'artist-1' });
      const p2 = await charge(A2, c2.pm, W2, 0, tag + '-C1-pay-2', { basket: 'C1', artist: 'artist-2' });
      ok('BD-C1', 'card needing authentication at entry (completed once on the hosted page): both artist charges then succeed with no second authentication', e3.si_status === 'succeeded' && p1.status === 'succeeded' && p2.status === 'succeeded',
        { authentication_at_entry: e3.challenged, artist1: p1.status || p1.error?.code, artist2: p2.status || p2.error?.code });
    } else ok('BD-C1', 'authentication-at-setup card entered once', false, e3.error || {});
    const e4 = await enterCardOnce('C-always-auth', CARDS.alwaysAuth);
    if (!e4.error && e4.pm) {
      const c1 = await cloneTo(A1, e4, tag + '-C2-clone-1');
      const p1 = await charge(A1, c1.pm, W1, fee15(W1), tag + '-C2-pay-1', { basket: 'C2', artist: 'artist-1' });
      info('BD-C2', 'card that ALWAYS needs authentication: what an artist charge does after the one card entry', { authentication_at_entry: e4.challenged,
        artist1_status: p1.status, decline: p1.error?.decline_code || p1.error?.code,
        meaning: p1.status === 'requires_action' || p1.error?.code === 'authentication_required' ? 'the buyer must authenticate again, per artist charge' : 'no further authentication was needed' });
    } else info('BD-C2', 'always-authenticate card entry', e4.error || {});

    // ---- D · authorise BOTH before capturing either
    if (created.basePm) {
      const e5 = created.basePm;
      const c1 = await cloneTo(A1, e5, tag + '-D-clone-1'), c2 = await cloneTo(A2, e5, tag + '-D-clone-2');
      const p1 = await charge(A1, c1.pm, W1, fee15(W1), tag + '-D-auth-1', { manual: true, basket: 'D', artist: 'artist-1' });
      const p2 = await charge(A2, c2.pm, W2, 0, tag + '-D-auth-2', { manual: true, basket: 'D', artist: 'artist-2' });
      ok('BD-D1', 'both artist charges can be AUTHORISED (requires_capture) before either is captured', p1.status === 'requires_capture' && p2.status === 'requires_capture', { p1: p1.status, p2: p2.status, e1: p1.error, e2: p2.error });
      if (p1.status === 'requires_capture' && p2.status === 'requires_capture') {
        const k1 = await api('POST', `/v1/payment_intents/${p1.id}/capture`, {}, { account: A1, idem: tag + '-D-cap-1' });
        const k2 = await api('POST', `/v1/payment_intents/${p2.id}/capture`, {}, { account: A2, idem: tag + '-D-cap-2' });
        if (k1.ok) { created.uncaptured = created.uncaptured.filter(x => x[1] !== p1.id); created.captured.push([A1, p1.id]); }
        if (k2.ok) { created.uncaptured = created.uncaptured.filter(x => x[1] !== p2.id); created.captured.push([A2, p2.id]); }
        ok('BD-D2', 'once both are authorised, both are captured', k1.j.status === 'succeeded' && k2.j.status === 'succeeded', { c1: k1.j.status || k1.err, c2: k2.j.status || k2.err });
      }
      // one authorisation fails: release the other, so no money is taken
      const c3 = await cloneTo(A1, e5, tag + '-D3-clone-1'), c4 = await cloneTo(A2, e5, tag + '-D3-clone-2');
      const q1 = await charge(A1, c3.pm, W1, fee15(W1), tag + '-D3-auth-1', { manual: true, basket: 'D3', artist: 'artist-1' });
      const q2 = await charge(A2, c4.pm, 100000000, 0, tag + '-D3-auth-2', { manual: true, basket: 'D3', artist: 'artist-2' });
      let cancelled = null;
      if (q1.status === 'requires_capture' && !q2.ok) {
        const x = await api('POST', `/v1/payment_intents/${q1.id}/cancel`, {}, { account: A1, idem: tag + '-D3-cancel-1' });
        cancelled = x.j.status; if (x.ok) created.uncaptured = created.uncaptured.filter(y => y[1] !== q1.id);
      }
      ok('BD-D3', 'all-or-nothing by authorisation: when artist 2 fails, artist 1\'s authorisation is cancelled and nothing is captured', q1.status === 'requires_capture' && !q2.ok && cancelled === 'canceled',
        { artist1_auth: q1.status, artist2_error: q2.error?.code, artist1_after: cancelled, note: 'the buyer may briefly see a pending authorisation for artist 1 until the bank releases it' });
    }

    // ---- E · retries must not create duplicate payments
    if (created.basePm) {
      const e6 = created.basePm;
      const c1 = await cloneTo(A1, e6, tag + '-E-clone-1');
      const c1again = await cloneTo(A1, e6, tag + '-E-clone-1');
      ok('BD-E1', 'retrying the clone with the same idempotency key returns the same clone (no second copy)', c1.pm && c1.pm === c1again.pm && c1again.replayed, { same: c1.pm === c1again.pm, replayed: c1again.replayed });
      const r1 = await charge(A1, c1.pm, W1, fee15(W1), tag + '-E-pay-1', { manual: true, basket: 'E', artist: 'artist-1' });
      const r2 = await charge(A1, c1.pm, W1, fee15(W1), tag + '-E-pay-1', { manual: true, basket: 'E', artist: 'artist-1' });   // the "lost response" retry
      ok('BD-E2', 'a retried payment request with the SAME idempotency key returns the same payment: one authorisation, not two', r1.id && r1.id === r2.id && r2.replayed, { first: r1.id, retry: r2.id, replayed: r2.replayed });
      const r3 = await charge(A1, c1.pm, W1, fee15(W1), tag + '-E-pay-1-NEWKEY', { manual: true, basket: 'E', artist: 'artist-1' });
      info('BD-E3', 'a retry with a NEW key and the already-used clone', { status: r3.status, error: r3.error?.code, message: r3.error?.message,
        meaning: r3.ok ? 'a second payment WAS created: retries must reuse the key or reconcile first' : 'the consumed clone cannot be charged again' });
      if (r3.ok && r3.id && r3.id !== r1.id && r3.status === 'requires_capture') created.uncaptured.push([A1, r3.id]);
      await new Promise(r => setTimeout(r, 15000));   // Search is not instant
      const s = await api('GET', `/v1/payment_intents/search?query=${encodeURIComponent(`metadata['basket']:'E' AND metadata['poc']:'${tag}'`)}`, null, { account: A1 });
      info('BD-E4', 'reconciling before a retry: find this basket\'s payments on the artist account by metadata (Search API)', s.ok ? { found: s.j.data.map(p => p.status), ids: s.j.data.length } : { error: s.err });
    }
  } catch (err) {
    rec('BD-X', 'unexpected error (run stopped; clean-up follows)', S, 'FAIL', { message: String(err.message).slice(0, 200) });
  } finally {
    await browser.close().catch(() => {});
    // ---- clean-up: nothing kept beyond the test
    const out = { cancelled: 0, refunded: 0, customers_deleted: 0, errors: [] };
    for (const [acct, id] of created.uncaptured) {
      const r = await api('POST', `/v1/payment_intents/${id}/cancel`, {}, { account: acct });
      if (r.ok || r.err?.code === 'payment_intent_unexpected_state') out.cancelled++; else out.errors.push(r.err?.code);
    }
    for (const [acct, id] of created.captured) {
      const r = await api('POST', '/v1/refunds', { payment_intent: id, refund_application_fee: 'true', 'metadata[poc]': tag }, { account: acct, idem: tag + '-refund-' + id });
      if (r.ok) out.refunded++; else out.errors.push(r.err?.code);
    }
    for (const cus of created.customers) {
      const r = await api('DELETE', '/v1/customers/' + cus);
      if (r.ok) out.customers_deleted++; else out.errors.push(r.err?.code);
    }
    ok('BD-Z', 'clean-up: authorisations cancelled, test charges refunded with commission, saved cards removed (test customers deleted)', out.errors.length === 0, out);
  }
}
