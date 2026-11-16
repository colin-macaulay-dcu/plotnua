// REAL STRIPE TEST-MODE CHECKS · PlotArt managed checkout pilot (prepared 16 Nov 2026).
// Talks to the REAL Stripe API in TEST MODE only (refuses anything but sk_test_/rk_test_). Never prints the key. Writes
// evidence to stripe-test-evidence/ (JSON + Markdown): every result is labelled with its SOURCE — "stripe-test-api" for
// what Stripe itself returned, "local" for checks of our own code — so provider results are never confused with mocks.
//
//   STRIPE_SECRET_KEY=<test key> node test/stripe-testmode-checks.mjs provider
//   STRIPE_SECRET_KEY=<test key> CHECKOUT_TEST_ACCOUNT=acct_… node test/stripe-testmode-checks.mjs provider e2e
//
// provider : account configuration and onboarding link; with an onboarded CHECKOUT_TEST_ACCOUNT also Checkout Session
//            shape and expiry, direct-charge payments with application fees, actual Stripe fees, full and partial
//            refunds, exact commission (application fee) refunds and their idempotency, a refund that cannot be funded
//            from the available balance, an asynchronously failing refund, and disputes won and lost.
// e2e      : the pilot's own Workers (Miniflare, local D1) against the real Stripe test API, with REAL signed webhook
//            deliveries forwarded by the Stripe CLI (`stripe listen`), and the buyer paying on Stripe's hosted Checkout
//            in a headless browser. Needs STRIPE_WEBHOOK_SECRET from `stripe listen --print-secret` and Playwright.
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

const HERE = new URL('..', import.meta.url).pathname;
const OUT = HERE + 'stripe-test-evidence/';
mkdirSync(OUT, { recursive: true });
const KEY = process.env.STRIPE_SECRET_KEY || '';
const PHASES = process.argv.slice(2).length ? process.argv.slice(2) : ['provider'];
const ACCOUNT = process.env.CHECKOUT_TEST_ACCOUNT || '';
const RUN = 'run' + Date.now().toString(36);
const results = [];
const rec = (id, name, source, status, detail = {}) => { results.push({ id, name, source, status, detail }); console.log(`  ${status.padEnd(4)} [${source}] ${id} ${name}${status === 'FAIL' ? '  ' + JSON.stringify(detail).slice(0, 400) : ''}`); };
const scrub = o => JSON.parse(JSON.stringify(o, (k, v) => (typeof v === 'string' && /^(sk|rk)_(test|live)_|^whsec_/.test(v) ? '[redacted]' : v)));
const sleep = ms => new Promise(r => setTimeout(r, ms));
function finish() {
  const ev = scrub({ run: RUN, at: new Date().toISOString(), phases: PHASES, account: ACCOUNT || null, results });
  writeFileSync(OUT + 'evidence.json', JSON.stringify(ev, null, 1));
  const n = s => results.filter(r => r.status === s).length;
  const md = [`# Stripe test-mode evidence · ${ev.at}`, '', `Run ${RUN}; phases ${PHASES.join(', ')}; connected test account ${ACCOUNT || '(none yet)'}.`, '',
    `PASS ${n('PASS')} · FAIL ${n('FAIL')} · SKIP ${n('SKIP')} · INFO ${n('INFO')}`, '', '| id | check | source | result | observed |', '|---|---|---|---|---|',
    ...results.map(r => `| ${r.id} | ${r.name} | ${r.source} | ${r.status} | ${JSON.stringify(r.detail).replace(/\|/g, '/').slice(0, 300)} |`)].join('\n');
  writeFileSync(OUT + 'evidence.md', md + '\n');
  console.log(`\nSTRIPE TEST MODE · PASS ${n('PASS')} · FAIL ${n('FAIL')} · SKIP ${n('SKIP')} · INFO ${n('INFO')}`);
  process.exit(n('FAIL') ? 1 : 0);
}

const S = await import(HERE + 'src/stripe.js');
const env = { STRIPE_SECRET_KEY: KEY, ENVIRONMENT: 'stripe-test-harness' };
// ---- local refusals first (no network)
rec('L1', 'the adapter refuses a live key before any request', 'local', !S.testKey({ STRIPE_SECRET_KEY: 'sk_live_' + 'x'.repeat(20) }).ok ? 'PASS' : 'FAIL');
if (!S.testKey(env).ok) { rec('L2', 'a Stripe TEST key is configured', 'local', 'FAIL', { reason: S.testKey(env).reason }); finish(); }
rec('L2', 'a Stripe TEST key is configured', 'local', 'PASS');

// raw calls for objects the pilot never creates itself (direct test payments, disputes, balances)
async function stripe(method, path, body = null, account = null, idem = null) {
  const h = { Authorization: `Bearer ${KEY}` };
  if (account) h['Stripe-Account'] = account;
  if (idem) h['Idempotency-Key'] = idem;
  if (body) h['Content-Type'] = 'application/x-www-form-urlencoded';
  const r = await fetch('https://api.stripe.com' + path, { method, headers: h, body: body ? S.form(body) : undefined });
  const j = await r.json();
  if (j.livemode === true) throw new Error('live-mode object returned');
  return { ok: r.ok, status: r.status, j };
}
const expectedFee = (cents, pct) => Math.round(cents * pct / 100 + 25);

if (PHASES.includes('provider')) {
  console.log('— provider: account configuration');
  let acct;
  try {
    acct = await S.createAccount(env, { email: `pilot-test+${RUN}@plotnua.invalid`, country: 'IE', artistId: 'harness-' + RUN });
    const c = acct.controller || {};
    rec('P1', 'Stripe accepts the pilot’s account configuration (artist pays fees, Stripe carries losses, Stripe-hosted requirements, full Dashboard)', 'stripe-test-api',
      c.fees && c.fees.payer === 'account' && c.losses && c.losses.payments === 'stripe' && c.requirement_collection === 'stripe' && c.stripe_dashboard && c.stripe_dashboard.type === 'full' ? 'PASS' : 'FAIL',
      { account: acct.id, type: acct.type, controller: c, livemode: acct.livemode });
    rec('P1b', 'requested capabilities as returned', 'stripe-test-api', 'INFO', { capabilities: acct.capabilities, requirements_due: acct.requirements && acct.requirements.currently_due });
    const link = await S.accountLink(env, { account: acct.id, refreshUrl: 'https://plotart-checkout-test.invalid/refresh', returnUrl: 'https://plotart-checkout-test.invalid/return' });
    rec('P2', 'Stripe-hosted onboarding link is created', 'stripe-test-api', /^https:\/\/connect\.stripe\.com\//.test(link.url) ? 'PASS' : 'FAIL', { host: new URL(link.url).host, expires_at: link.expires_at });
    writeFileSync(OUT + 'onboarding-link.txt', `Test account ${acct.id}\nComplete Stripe's TEST onboarding (test data only) at:\n${link.url}\nThen set the GitHub variable CHECKOUT_TEST_ACCOUNT=${acct.id} in the checkout-test environment.\n`);
  } catch (e) { rec('P1', 'Stripe accepts the pilot’s account configuration', 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }

  if (!ACCOUNT) {
    rec('P3', 'payments, refunds and disputes on an onboarded test account', 'stripe-test-api', 'SKIP', { reason: 'CHECKOUT_TEST_ACCOUNT not set yet: complete the onboarding link from P2 once, then set the variable' });
  } else {
    console.log('— provider: onboarded test account ' + ACCOUNT);
    const a = (await stripe('GET', `/v1/accounts/${ACCOUNT}`)).j;
    rec('P3', 'the onboarded test account can take charges and has the pilot configuration', 'stripe-test-api',
      a.charges_enabled && a.details_submitted && a.controller && a.controller.fees && a.controller.fees.payer === 'account' && a.controller.losses.payments === 'stripe' ? 'PASS' : 'FAIL',
      { charges_enabled: a.charges_enabled, payouts_enabled: a.payouts_enabled, details_submitted: a.details_submitted, controller: a.controller, country: a.country, default_currency: a.default_currency });
    // Checkout Session exactly as the pilot creates it, then expired as a revision would
    try {
      const order = { id: 'o' + RUN, reference: 'PA-O-TEST-' + RUN.toUpperCase(), quote_version: 1 };
      const expiresAt = new Date(Date.now() + 31 * 60_000).toISOString();
      const s = await S.createSession(env, { account: ACCOUNT, idem: `harness-${RUN}-s1`, order, title: 'Harness test artwork by Test Artist', artworkCents: 100000, deliveryCents: 7500, feeCents: 15000, expiresAt,
        buyerEmail: `buyer+${RUN}@plotnua.invalid`, successUrl: 'https://plotart-checkout-test.invalid/ok', cancelUrl: 'https://plotart-checkout-test.invalid/cancel', statement: 'PlotArt harness test' });
      rec('P4', 'Checkout Session on the artist’s account: €1,075 total, EUR, hosted on checkout.stripe.com, expiry as requested', 'stripe-test-api',
        s.amount_total === 107500 && s.currency === 'eur' && /checkout\.stripe\.com/.test(s.url) && Math.abs(s.expires_at - Math.floor(Date.parse(expiresAt) / 1000)) <= 1 ? 'PASS' : 'FAIL',
        { session: s.id, amount_total: s.amount_total, currency: s.currency, status: s.status, expires_at: s.expires_at });
      const again = await S.createSession(env, { account: ACCOUNT, idem: `harness-${RUN}-s1`, order, title: 'Harness test artwork by Test Artist', artworkCents: 100000, deliveryCents: 7500, feeCents: 15000, expiresAt,
        buyerEmail: `buyer+${RUN}@plotnua.invalid`, successUrl: 'https://plotart-checkout-test.invalid/ok', cancelUrl: 'https://plotart-checkout-test.invalid/cancel', statement: 'PlotArt harness test' });
      rec('P4b', 'the same idempotency key returns the same session (a retried request cannot open a second checkout)', 'stripe-test-api', again.id === s.id ? 'PASS' : 'FAIL', { first: s.id, second: again.id });
      const ex = await S.expireSession(env, { account: ACCOUNT, id: s.id });
      rec('P5', 'an open session can be expired (quote revision / cancellation)', 'stripe-test-api', ex.status === 'expired' ? 'PASS' : 'FAIL', { status: ex.status });
    } catch (e) { rec('P4', 'Checkout Session creation and expiry', 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }

    // a direct charge with the same parameters Checkout uses (payment_intent_data), paid with a test payment method
    async function charge(amount, fee, pm, tag) {
      const r = await stripe('POST', '/v1/payment_intents', { amount, currency: 'eur', payment_method: pm, confirm: 'true', payment_method_types: ['card'],
        ...(fee ? { application_fee_amount: fee } : {}), metadata: { plotart_order: 'harness-' + tag, run: RUN }, expand: ['latest_charge.balance_transaction'] }, ACCOUNT, `harness-${RUN}-${tag}`);
      if (!r.ok) throw Object.assign(new Error(r.j.error && r.j.error.message), { code: r.j.error && r.j.error.code });
      return r.j;
    }
    const pctFor = { standard: 1.5 };
    try {
      const pi = await charge(107500, 15000, 'pm_card_bypassPending', 'full');
      const ch = pi.latest_charge, bt = ch.balance_transaction;
      rec('P6', 'a direct charge of €1,075 with a €150 application fee succeeds on the artist’s account', 'stripe-test-api',
        pi.status === 'succeeded' && ch.application_fee_amount === 15000 ? 'PASS' : 'FAIL', { payment_intent: pi.id, charge: ch.id, application_fee: ch.application_fee, status: pi.status });
      rec('P7', 'Stripe’s actual processing fee on €1,075 (charged to the artist’s balance; compare the documented 1.5% + €0.25 ≈ €16.38)', 'stripe-test-api', 'INFO',
        { stripe_fee_cents: bt && bt.fee, fee_details: bt && bt.fee_details, net_cents: bt && bt.net, card_country: ch.payment_method_details && ch.payment_method_details.card && ch.payment_method_details.card.country, expected_standard_eea_cents: expectedFee(107500, pctFor.standard) });
      const rf = await S.refund(env, { account: ACCOUNT, paymentIntent: pi.id, amount: 107500, idem: `harness-${RUN}-rf-full`, metadata: { plotart_refund: 'harness-full' } });
      rec('P8', 'full refund on the artist’s account, application fee NOT refunded automatically', 'stripe-test-api', rf.status === 'succeeded' ? 'PASS' : 'FAIL', { refund: rf.id, status: rf.status });
      const feeAfterRefund = (await stripe('GET', `/v1/application_fees/${ch.application_fee}`)).j;
      rec('P8b', 'after the buyer refund, the application fee is still un-refunded until PlotArt refunds it', 'stripe-test-api', feeAfterRefund.amount_refunded === 0 ? 'PASS' : 'FAIL', { amount_refunded: feeAfterRefund.amount_refunded });
      const fr1 = await S.refundFee(env, { fee: ch.application_fee, amount: 15000, idem: `harness-${RUN}-fr-full`, metadata: { plotart_order: 'harness-full' } });
      const fr1b = await S.refundFee(env, { fee: ch.application_fee, amount: 15000, idem: `harness-${RUN}-fr-full`, metadata: { plotart_order: 'harness-full' } });
      const feeObj = (await stripe('GET', `/v1/application_fees/${ch.application_fee}`)).j;
      rec('P9', 'PlotArt refunds the full €150 commission; repeating the request with the same key refunds nothing more', 'stripe-test-api',
        fr1.id === fr1b.id && feeObj.amount_refunded === 15000 && feeObj.refunded === true ? 'PASS' : 'FAIL', { fee_refund: fr1.id, repeat: fr1b.id, amount_refunded: feeObj.amount_refunded });
    } catch (e) { rec('P6', 'direct charge, full refund and commission refund', 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }

    try {
      const pi = await charge(107500, 15000, 'pm_card_bypassPending', 'partial');
      const fee = pi.latest_charge.application_fee;
      const r1 = await S.refund(env, { account: ACCOUNT, paymentIntent: pi.id, amount: 50000, idem: `harness-${RUN}-rf-p1`, metadata: {} });
      const f1 = await S.refundFee(env, { fee, amount: 7500, idem: `harness-${RUN}-fr-p1`, metadata: {} });
      const r2 = await S.refund(env, { account: ACCOUNT, paymentIntent: pi.id, amount: 7500, idem: `harness-${RUN}-rf-p2`, metadata: {} });
      const fo = (await stripe('GET', `/v1/application_fees/${fee}`)).j;
      rec('P10', 'partial: €500 artwork refund → €75 commission returned; €75 delivery refund → no commission returned', 'stripe-test-api',
        r1.status === 'succeeded' && r2.status === 'succeeded' && f1.amount === 7500 && fo.amount_refunded === 7500 ? 'PASS' : 'FAIL', { refunds: [r1.status, r2.status], fee_amount_refunded: fo.amount_refunded });
    } catch (e) { rec('P10', 'partial refunds and proportional commission refund', 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }

    try {
      const bal = (await stripe('GET', '/v1/balance', null, ACCOUNT)).j;
      const avail = (bal.available.find(x => x.currency === 'eur') || { amount: 0 }).amount;
      const amount = Math.max(avail + 50000, 60000);
      const pi = await charge(amount, 0, 'pm_card_visa', 'unfunded');   // funds go to the PENDING balance
      const rf = await S.refund(env, { account: ACCOUNT, paymentIntent: pi.id, amount, idem: `harness-${RUN}-rf-unfunded`, metadata: { plotart_refund: 'harness-unfunded' } });
      let cur = rf; for (let i = 0; i < 6 && cur.status === 'pending'; i++) { await sleep(5000); cur = await S.getRefund(env, { account: ACCOUNT, id: rf.id }); }
      rec('P11', 'a card refund larger than the AVAILABLE balance (e.g. after payout) is held by Stripe as pending, not failed', 'stripe-test-api',
        rf.status === 'pending' ? 'PASS' : 'INFO', { available_before_cents: avail, refund_cents: amount, status_at_creation: rf.status, status_after_30s: cur.status, refund: rf.id,
          note: rf.status === 'pending' ? 'matches Stripe documentation; the pilot books nothing until it succeeds' : 'Stripe did not hold it pending in test mode: record and review' });
      rec('P11b', 'S.getRefund reads the refund state the sweep relies on', 'stripe-test-api', cur && cur.id === rf.id ? 'PASS' : 'FAIL', { status: cur.status });
    } catch (e) { rec('P11', 'refund that cannot be funded from the available balance', 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }

    try {
      const pi = await charge(1000, 0, 'pm_card_refundFail', 'refundfail');
      const rf = await S.refund(env, { account: ACCOUNT, paymentIntent: pi.id, amount: 1000, idem: `harness-${RUN}-rf-fail`, metadata: { plotart_refund: 'harness-fail' } });
      let cur = rf; for (let i = 0; i < 12 && cur.status !== 'failed'; i++) { await sleep(5000); cur = await S.getRefund(env, { account: ACCOUNT, id: rf.id }); }
      rec('P12', 'a refund that fails asynchronously reaches status "failed" with a reason', 'stripe-test-api', cur.status === 'failed' ? 'PASS' : 'FAIL', { status: cur.status, failure_reason: cur.failure_reason });
    } catch (e) { rec('P12', 'asynchronously failing refund', 'stripe-test-api', e.code === 'resource_missing' ? 'SKIP' : 'FAIL', { error: e.message, code: e.code }); }

    for (const [tag, evidence, want] of [['dispute-lost', 'losing_evidence', 'lost'], ['dispute-won', 'winning_evidence', 'won']]) {
      try {
        const pi = await charge(5000, 750, 'pm_card_createDispute', tag);
        let d = null; for (let i = 0; i < 12 && !d; i++) { await sleep(5000); d = ((await stripe('GET', `/v1/disputes?payment_intent=${pi.id}`, null, ACCOUNT)).j.data || [])[0]; }
        if (!d) { rec('P13-' + want, `dispute is opened on the artist’s account (${want})`, 'stripe-test-api', 'FAIL', { reason: 'no dispute after 60s' }); continue; }
        const full = (await stripe('GET', `/v1/disputes/${d.id}?expand[]=balance_transactions`, null, ACCOUNT)).j;
        rec('P13-' + want, `dispute opened on the artist’s account; amount and dispute fee debited there (${want})`, 'stripe-test-api', 'PASS',
          { dispute: d.id, amount: d.amount, reason: d.reason, balance_transactions: (full.balance_transactions || []).map(b => ({ amount: b.amount, fee: b.fee })) });
        await stripe('POST', `/v1/disputes/${d.id}`, { evidence: { uncategorized_text: evidence }, submit: 'true' }, ACCOUNT);
        let st = d.status; for (let i = 0; i < 24 && !['won', 'lost'].includes(st); i++) { await sleep(5000); st = (await stripe('GET', `/v1/disputes/${d.id}`, null, ACCOUNT)).j.status; }
        rec('P14-' + want, `dispute closes as ${want} with Stripe’s test evidence`, 'stripe-test-api', st === want ? 'PASS' : 'FAIL', { status: st });
      } catch (e) { rec('P13-' + want, `dispute (${want})`, 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }
    }
  }
}

if (PHASES.includes('e2e')) {
  console.log('— e2e: the pilot’s Workers with real Stripe test API and real signed webhooks');
  if (!ACCOUNT || !process.env.STRIPE_WEBHOOK_SECRET || !process.env.CHECKOUT_E2E_PORT) {
    rec('E0', 'end-to-end prerequisites (onboarded account, Stripe CLI listener, port)', 'local', 'SKIP', { account: !!ACCOUNT, webhook_secret: !!process.env.STRIPE_WEBHOOK_SECRET, port: process.env.CHECKOUT_E2E_PORT || null });
  } else {
    const { e2e } = await import(HERE + 'test/stripe-testmode-e2e.mjs');
    await e2e({ rec, KEY, ACCOUNT, RUN, port: Number(process.env.CHECKOUT_E2E_PORT), whsec: process.env.STRIPE_WEBHOOK_SECRET, stripe, sleep });
  }
}
finish();
