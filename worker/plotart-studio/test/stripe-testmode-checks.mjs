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
  const h = { Authorization: `Bearer ${KEY}`, 'Stripe-Version': S.V1_API_VERSION };
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
  // Reuse an account an earlier run created (named in stripe-test-run.json) instead of creating a new one each run.
  let REUSE = '';
  try { REUSE = String(JSON.parse(readFileSync(HERE + 'test/stripe-test-run.json', 'utf8')).reuse_account || ''); } catch {}
  if (REUSE && !/^acct_[A-Za-z0-9]+$/.test(REUSE)) { rec('P0', 'reuse_account in stripe-test-run.json is an account id', 'local', 'FAIL', { reuse_account: REUSE }); REUSE = ''; }
  let acctId = null;
  if (REUSE) {
    rec('P1', 'account creation: not repeated — reusing the test account created and verified in an earlier run', 'stripe-test-api', 'SKIP', { reuse_account: REUSE });
    acctId = REUSE;
  } else {
    try {
      const acct = await S.createAccount(env, { email: `pilot-test+${RUN}@plotnua.invalid`, country: 'IE', artistId: 'harness-' + RUN });
      const r = (acct.defaults && acct.defaults.responsibilities) || {};
      rec('P1', 'account creation: Stripe accepts the pilot’s Accounts v2 configuration (artist pays fees, Stripe carries losses, Stripe-collected requirements, full Dashboard)', 'stripe-test-api',
        acct.object === 'v2.core.account' && S.accountConfigProblems(acct).length === 0 && r.requirements_collector === 'stripe' ? 'PASS' : 'FAIL',
        { account: acct.id, object: acct.object, dashboard: acct.dashboard, responsibilities: r, problems: S.accountConfigProblems(acct), livemode: acct.livemode, api_version: S.V2_API_VERSION });
      rec('P1b', 'merchant capabilities and requirements as returned', 'stripe-test-api', 'INFO',
        { card_payments: acct.configuration && acct.configuration.merchant && acct.configuration.merchant.capabilities && acct.configuration.merchant.capabilities.card_payments });
      acctId = acct.id;
    } catch (e) { rec('P1', 'account creation (Accounts v2)', 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }
  }
  if (acctId) {
    try {
      const again = await S.getAccountV2(env, acctId);
      rec('P1c', 'configuration read back (v2): fees_collector, losses_collector and requirements_collector are stripe; dashboard is full', 'stripe-test-api', S.accountConfigProblems(again).length === 0 ? 'PASS' : 'FAIL',
        { account: acctId, dashboard: again.dashboard, responsibilities: again.defaults && again.defaults.responsibilities, card_payments: again.configuration && again.configuration.merchant && again.configuration.merchant.capabilities && again.configuration.merchant.capabilities.card_payments });
    } catch (e) { rec('P1c', 'configuration read back (v2)', 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }
    try {
      const v1 = await S.getAccount(env, acctId);
      rec('P1d', 'the v1 view of the same account (used for charge status and account.updated) is readable', 'stripe-test-api', v1.id === acctId && typeof v1.charges_enabled === 'boolean' ? 'PASS' : 'FAIL',
        { charges_enabled: v1.charges_enabled, payouts_enabled: v1.payouts_enabled, details_submitted: v1.details_submitted, controller: v1.controller, country: v1.country });
      if (REUSE) {
        const req = v1.requirements || {};
        rec('P1e', 'onboarding status (reused account): details submitted, charges enabled, nothing currently or past due', 'stripe-test-api',
          v1.details_submitted && v1.charges_enabled && !(req.currently_due || []).length && !(req.past_due || []).length ? 'PASS' : 'FAIL',
          { details_submitted: v1.details_submitted, charges_enabled: v1.charges_enabled, payouts_enabled: v1.payouts_enabled, currently_due: req.currently_due, past_due: req.past_due, eventually_due: req.eventually_due, disabled_reason: req.disabled_reason });
      }
    } catch (e) { rec('P1d', 'v1 view of the account', 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }
    try {
      const link = await S.accountLink(env, { account: acctId, refreshUrl: 'https://plotart-checkout-test.invalid/refresh', returnUrl: 'https://plotart-checkout-test.invalid/return' });
      const host = new URL(link.url).host;
      rec('P2', 'onboarding link: Stripe-hosted Account Link v2 is created', 'stripe-test-api', /(^|\.)stripe\.com$/.test(host) ? 'PASS' : 'FAIL',
        { host, expires_at: link.expires_at, use_case: link.use_case && link.use_case.type, configurations_chosen_by_stripe: link.use_case && link.use_case.account_onboarding && link.use_case.account_onboarding.configurations });
      writeFileSync(OUT + 'onboarding-link.txt', `Test account ${acctId}\nComplete Stripe's TEST onboarding (test data only) at:\n${link.url}\nThe link is single-use and expires at ${link.expires_at}.\nThen set the GitHub variable CHECKOUT_TEST_CONNECTED_ACCOUNT=${acctId} in the checkout-test environment.\n`);
    } catch (e) { rec('P2', 'onboarding link (Account Links v2)', 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }
  }

  if (!ACCOUNT) {
    rec('P3', 'payments, refunds and disputes on an onboarded test account', 'stripe-test-api', 'SKIP', { reason: 'CHECKOUT_TEST_ACCOUNT not set yet: complete the onboarding link from P2 once, then set the variable' });
  } else {
    console.log('— provider: onboarded test account ' + ACCOUNT);
    const a = (await stripe('GET', `/v1/accounts/${ACCOUNT}`)).j;
    let a2 = null; try { a2 = await S.getAccountV2(env, ACCOUNT); } catch (e) { a2 = { error: e.message }; }
    rec('P3', 'the onboarded test account can take charges and has the pilot configuration', 'stripe-test-api',
      a.charges_enabled && a.details_submitted && a2 && !a2.error && S.accountConfigProblems(a2).length === 0 ? 'PASS' : 'FAIL',
      { charges_enabled: a.charges_enabled, payouts_enabled: a.payouts_enabled, details_submitted: a.details_submitted, dashboard: a2 && a2.dashboard, responsibilities: a2 && a2.defaults && a2.defaults.responsibilities, problems: a2 && !a2.error ? S.accountConfigProblems(a2) : a2, country: a.country, default_currency: a.default_currency });
    // Checkout Session exactly as the pilot creates it, then expired as a revision would
    try {
      const order = { id: 'o' + RUN, reference: 'PA-O-TEST-' + RUN.toUpperCase(), quote_version: 1 };
      const expiresAt = new Date(Date.now() + 31 * 60_000).toISOString();
      const s = await S.createSession(env, { account: ACCOUNT, idem: `harness-${RUN}-s1`, order, title: 'Harness test artwork by Test Artist', artworkCents: 100000, deliveryCents: 7500, feeCents: 15000, expiresAt,
        buyerEmail: `buyer+${RUN}@plotnua.invalid`, successUrl: 'https://plotart-checkout-test.invalid/ok', cancelUrl: 'https://plotart-checkout-test.invalid/cancel', statement: 'PlotArt harness test' });
      rec('P4', 'Checkout Session on the artist’s account: €1,075 total, EUR, hosted on checkout.stripe.com, expiry as requested', 'stripe-test-api',
        s.amount_total === 107500 && s.currency === 'eur' && /checkout\.stripe\.com/.test(s.url) && Math.abs(s.expires_at - Math.floor(Date.parse(expiresAt) / 1000)) <= 1
          && !(s.adaptive_pricing && s.adaptive_pricing.enabled) ? 'PASS' : 'FAIL',
        { session: s.id, adaptive_pricing: s.adaptive_pricing, amount_total: s.amount_total, currency: s.currency, status: s.status, expires_at: s.expires_at });
      const again = await S.createSession(env, { account: ACCOUNT, idem: `harness-${RUN}-s1`, order, title: 'Harness test artwork by Test Artist', artworkCents: 100000, deliveryCents: 7500, feeCents: 15000, expiresAt,
        buyerEmail: `buyer+${RUN}@plotnua.invalid`, successUrl: 'https://plotart-checkout-test.invalid/ok', cancelUrl: 'https://plotart-checkout-test.invalid/cancel', statement: 'PlotArt harness test' });
      rec('P4b', 'the same idempotency key returns the same session (a retried request cannot open a second checkout)', 'stripe-test-api', again.id === s.id ? 'PASS' : 'FAIL', { first: s.id, second: again.id });
      const ex = await S.expireSession(env, { account: ACCOUNT, id: s.id });
      rec('P5', 'an open session can be expired (quote revision / cancellation)', 'stripe-test-api', ex.status === 'expired' ? 'PASS' : 'FAIL', { status: ex.status });
    } catch (e) { rec('P4', 'Checkout Session creation and expiry', 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }

    // a direct charge with the same parameters Checkout uses (payment_intent_data), paid with a test payment method
    async function charge(amount, fee, pm, tag) {
      const r = await stripe('POST', '/v1/payment_intents', { amount, currency: 'eur', payment_method: pm, confirm: 'true', allowed_payment_method_types: ['card'],
        ...(fee ? { application_fee_amount: fee } : {}), metadata: { plotart_order: 'harness-' + tag, run: RUN }, expand: ['latest_charge.balance_transaction'] }, ACCOUNT, `harness-${RUN}-${tag}`);
      if (!r.ok) throw Object.assign(new Error(r.j.error && r.j.error.message), { code: r.j.error && r.j.error.code });
      // Stripe creates the application fee and the balance transaction of a direct charge ASYNCHRONOUSLY: right after the
      // payment both can still be null. Wait for them (as the pilot does at refund time) and record how long it took.
      const pi = r.j; const t0 = Date.now();
      let ch = pi.latest_charge;
      for (let i = 0; i < 20 && ch && ch.status === 'succeeded' && (!ch.balance_transaction || (fee && !ch.application_fee)); i++) {
        await sleep(1500);
        ch = (await stripe('GET', `/v1/charges/${ch.id}?expand[]=balance_transaction`, null, ACCOUNT)).j;
      }
      pi.latest_charge = ch; pi._async = { fee_present_at_creation: !!(r.j.latest_charge && r.j.latest_charge.application_fee), waited_ms: Date.now() - t0 };
      return pi;
    }
    const pctFor = { standard: 1.5 };
    try {
      const pi = await charge(107500, 15000, 'pm_card_bypassPending', 'full');
      const ch = pi.latest_charge, bt = ch.balance_transaction;
      rec('P6', 'a direct charge of €1,075 with a €150 application fee succeeds on the artist’s account', 'stripe-test-api',
        pi.status === 'succeeded' && ch.application_fee_amount === 15000 ? 'PASS' : 'FAIL', { payment_intent: pi.id, charge: ch.id, application_fee: ch.application_fee, status: pi.status, async: pi._async });
      rec('P6b', 'the application fee and balance transaction appear asynchronously after the payment (Stripe default for direct charges)', 'stripe-test-api',
        ch.application_fee && ch.balance_transaction ? 'PASS' : 'FAIL', { application_fee: ch.application_fee, balance_transaction: !!ch.balance_transaction, ...pi._async });
      rec('P7', 'Stripe’s actual fee on €1,075 with the US test card (non-EEA pricing; charged to the artist’s balance)', 'stripe-test-api', 'INFO',
        { stripe_fee_cents: bt && bt.fee, fee_details: bt && bt.fee_details, net_cents: bt && bt.net, card_country: ch.payment_method_details && ch.payment_method_details.card && ch.payment_method_details.card.country, expected_standard_eea_cents: expectedFee(107500, pctFor.standard) });
      // the same sale paid with an Irish (EEA) test card: the fee most PlotArt buyers would attract
      try {
        const ie = await charge(107500, 15000, 'pm_card_ie', 'fee-ie'), ich = ie.latest_charge, ibt = ich.balance_transaction;
        const part = t => ((ibt && ibt.fee_details) || []).filter(d => d.type === t).reduce((a, d) => a + d.amount, 0);
        rec('P7b', 'Stripe’s actual fee with an IRISH test card on the same €1,075 sale, split into processing fee, VAT on the fee and PlotArt commission', 'stripe-test-api', ibt ? 'INFO' : 'FAIL',
          { card_country: ich.payment_method_details && ich.payment_method_details.card && ich.payment_method_details.card.country, stripe_fee_cents: part('stripe_fee'), vat_on_fee_cents: part('tax'), application_fee_cents: part('application_fee'), net_to_artist_cents: ibt && ibt.net, available_on: ibt && ibt.available_on });
        await S.refund(env, { account: ACCOUNT, paymentIntent: ie.id, amount: 107500, idem: `harness-${RUN}-rf-fee-ie`, metadata: { plotart_refund: 'harness-fee-ie' } }).catch(() => {});
      } catch (e) { rec('P7b', 'Irish card fee measurement', 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }
      const rf = await S.refund(env, { account: ACCOUNT, paymentIntent: pi.id, amount: 107500, idem: `harness-${RUN}-rf-full`, metadata: { plotart_refund: 'harness-full' } });
      rec('P8', 'full refund on the artist’s account, application fee NOT refunded automatically', 'stripe-test-api', rf.status === 'succeeded' ? 'PASS' : 'FAIL', { refund: rf.id, status: rf.status });
      const feeAfterRefund = (await stripe('GET', `/v1/application_fees/${ch.application_fee}`)).j;
      rec('P8b', 'after the buyer refund, the application fee is still un-refunded until PlotArt refunds it', 'stripe-test-api', feeAfterRefund.amount_refunded === 0 ? 'PASS' : 'FAIL', { fee: ch.application_fee, amount_refunded: feeAfterRefund.amount_refunded, error: feeAfterRefund.error && feeAfterRefund.error.message });
      const fr1 = await S.refundFee(env, { fee: ch.application_fee, amount: 15000, idem: `harness-${RUN}-fr-full`, metadata: { plotart_order: 'harness-full' } });
      const fr1b = await S.refundFee(env, { fee: ch.application_fee, amount: 15000, idem: `harness-${RUN}-fr-full`, metadata: { plotart_order: 'harness-full' } });
      const feeObj = (await stripe('GET', `/v1/application_fees/${ch.application_fee}`)).j;
      rec('P9', 'PlotArt refunds the full €150 commission; repeating the request with the same key refunds nothing more', 'stripe-test-api',
        fr1.id === fr1b.id && feeObj.amount_refunded === 15000 && feeObj.refunded === true ? 'PASS' : 'FAIL', { fee_refund: fr1.id, repeat: fr1b.id, amount_refunded: feeObj.amount_refunded });
    } catch (e) { rec('P9', 'direct charge, full refund and commission refund', 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }

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
      const sum = b => Object.fromEntries(['available', 'pending'].map(k => [k, ((b[k] || []).find(x => x.currency === 'eur') || { amount: 0 }).amount]));
      const before = sum((await stripe('GET', '/v1/balance', null, ACCOUNT)).j);
      const rf = await S.refund(env, { account: ACCOUNT, paymentIntent: pi.id, amount, idem: `harness-${RUN}-rf-unfunded`, metadata: { plotart_refund: 'harness-unfunded' } });
      let cur = rf; for (let i = 0; i < 6 && cur.status === 'pending'; i++) { await sleep(5000); cur = await S.getRefund(env, { account: ACCOUNT, id: rf.id }); }
      const after = sum((await stripe('GET', '/v1/balance', null, ACCOUNT)).j);
      rec('P11', 'a card refund larger than the AVAILABLE balance: what Stripe does (pending vs. funded from the pending balance)', 'stripe-test-api',
        rf.status === 'pending' ? 'PASS' : 'INFO', { available_before_cents: avail, balance_before: before, balance_after: after, refund_cents: amount, status_at_creation: rf.status, status_after_30s: cur.status, refund: rf.id,
          note: rf.status === 'pending' ? 'held pending; the pilot books nothing until it succeeds' : 'Stripe completed it at once, funding it from the incoming (pending) balance; a refund larger than available + pending is not covered by this check' });
      rec('P11b', 'S.getRefund reads the refund state the sweep relies on', 'stripe-test-api', cur && cur.id === rf.id ? 'PASS' : 'FAIL', { status: cur.status });
    } catch (e) { rec('P11', 'refund that cannot be funded from the available balance', 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }

    try {
      const pi = await charge(1000, 0, 'pm_card_refundFail', 'refundfail');
      const rf = await S.refund(env, { account: ACCOUNT, paymentIntent: pi.id, amount: 1000, idem: `harness-${RUN}-rf-fail`, metadata: { plotart_refund: 'harness-fail' } });
      const t0 = Date.now(); let cur = rf; for (let i = 0; i < 36 && cur.status !== 'failed'; i++) { await sleep(5000); cur = await S.getRefund(env, { account: ACCOUNT, id: rf.id }); }
      rec('P12', 'a refund that fails asynchronously reaches status "failed" with a reason (waits up to 3 minutes)', 'stripe-test-api', cur.status === 'failed' ? 'PASS' : 'FAIL', { status_at_creation: rf.status, status: cur.status, failure_reason: cur.failure_reason, waited_s: Math.round((Date.now() - t0) / 1000) });
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
        const closed = (await stripe('GET', `/v1/disputes/${d.id}?expand[]=balance_transactions`, null, ACCOUNT)).j;
        rec('P14-' + want, `dispute closes as ${want} with Stripe’s test evidence`, 'stripe-test-api', st === want ? 'PASS' : 'FAIL', { status: st });
        // every balance movement on the dispute after closing: received fee, countered fee (submitting evidence counters it) and any reinstatement
        const bts = (closed.balance_transactions || []).map(b => ({ type: b.type, reporting_category: b.reporting_category, amount: b.amount, fee: b.fee, fee_details: (b.fee_details || []).map(f => ({ type: f.type, description: f.description, amount: f.amount })) }));
        rec('P15-' + want, `dispute fees actually charged and returned once the dispute closed as ${want} (sandbox measurement, not live pricing)`, 'stripe-test-api', 'INFO',
          { balance_transactions: bts, net_effect_cents: bts.reduce((a, b) => a + b.amount - b.fee, 0) });
      } catch (e) { rec('P13-' + want, `dispute (${want})`, 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }
    }
  }
}

if (PHASES.includes('unfunded')) {
  // A SECOND test connected account, used only here, so the shared account used by every other check is never drained.
  // Same key, same permissions. Fully unfunded = a refund larger than the account's available + incoming balance.
  console.log('— unfunded refund on a dedicated second test account');
  let UA = '';
  try { UA = String(JSON.parse(readFileSync(HERE + 'test/stripe-test-run.json', 'utf8')).unfunded_account || ''); } catch {}
  const bal = async a => { const b = (await stripe('GET', '/v1/balance', null, a)).j; const g = k => ((b[k] || []).find(x => x.currency === 'eur') || { amount: 0 }).amount; return { available: g('available'), pending: g('pending') }; };
  const link = async a => {
    const l = await S.accountLink(env, { account: a, refreshUrl: 'https://plotart-checkout-test.invalid/refresh', returnUrl: 'https://plotart-checkout-test.invalid/return' });
    writeFileSync(OUT + 'onboarding-link-unfunded.txt', `SECOND test account ${a} (unfunded-refund test only)\nComplete Stripe's TEST onboarding (test data only) at:\n${l.url}\nSingle-use; expires at ${l.expires_at}.\n`);
    return l;
  };
  try {
    if (!UA) {
      const a = await S.createAccount(env, { email: `pilot-unfunded+${RUN}@plotnua.invalid`, country: 'IE', artistId: 'unfunded-test-' + RUN });
      rec('U1', 'second test account created with the pilot configuration (artist pays fees, Stripe carries losses, full Dashboard)', 'stripe-test-api',
        S.accountConfigProblems(a).length === 0 ? 'PASS' : 'FAIL', { account: a.id, dashboard: a.dashboard, responsibilities: a.defaults && a.defaults.responsibilities, livemode: a.livemode });
      const l = await link(a.id);
      rec('U2', 'onboarding link for the second account', 'stripe-test-api', /stripe\.com$/.test(new URL(l.url).host) ? 'PASS' : 'FAIL', { account: a.id, expires_at: l.expires_at });
    } else {
      const v1 = await S.getAccount(env, UA), v2 = await S.getAccountV2(env, UA);
      const ready = v1.charges_enabled && v1.details_submitted && !((v1.requirements || {}).currently_due || []).length;
      rec('U3', 'second account: pilot configuration and onboarding complete', 'stripe-test-api', ready && !S.accountConfigProblems(v2).length ? 'PASS' : 'FAIL',
        { account: UA, charges_enabled: v1.charges_enabled, details_submitted: v1.details_submitted, currently_due: (v1.requirements || {}).currently_due, problems: S.accountConfigProblems(v2) });
      if (!ready) { const l = await link(UA); rec('U3b', 'a fresh onboarding link was written (onboarding not complete)', 'stripe-test-api', 'INFO', { expires_at: l.expires_at }); }
      else {
        const b0 = await bal(UA);
        rec('U4', 'balance on the second account before the test', 'stripe-test-api', 'INFO', b0);
        // a €100 sale with PlotArt's €15 commission: after commission, Stripe's fee and VAT the account holds less than €100
        const pi = (await stripe('POST', '/v1/payment_intents', { amount: 10000, currency: 'eur', payment_method: 'pm_card_visa', confirm: 'true', allowed_payment_method_types: ['card'],
          application_fee_amount: 1500, metadata: { plotart_order: 'harness-unfunded', run: RUN } }, UA, `harness-${RUN}-unf-pi`)).j;
        let ch = pi.latest_charge && (await stripe('GET', `/v1/charges/${typeof pi.latest_charge === 'string' ? pi.latest_charge : pi.latest_charge.id}?expand[]=balance_transaction`, null, UA)).j;
        for (let i = 0; i < 20 && ch && !ch.balance_transaction; i++) { await sleep(1500); ch = (await stripe('GET', `/v1/charges/${ch.id}?expand[]=balance_transaction`, null, UA)).j; }
        const b1 = await bal(UA);
        rec('U5', 'after a €100 sale with €15 commission the account holds less than the sale amount', 'stripe-test-api', pi.status === 'succeeded' && b1.available + b1.pending - (b0.available + b0.pending) < 10000 ? 'PASS' : 'FAIL',
          { payment_intent: pi.id, status: pi.status, net_cents: ch && ch.balance_transaction && ch.balance_transaction.net, balance_after_sale: b1 });
        // full refund of the €100 to the buyer, commission NOT refunded (as the pilot does): larger than everything the account holds
        const shortfall = 10000 - (b1.available + b1.pending);
        const rf = (await stripe('POST', '/v1/refunds', { payment_intent: pi.id, amount: 10000, refund_application_fee: 'false', metadata: { plotart_refund: 'harness-unfunded' } }, UA, `harness-${RUN}-unf-rf`)).j;
        const t0 = Date.now(); let cur = rf; const seen = [rf.status];
        for (let i = 0; i < 24 && !['failed', 'canceled'].includes(cur.status) && (cur.status === 'pending' || i < 6); i++) { await sleep(5000); cur = (await stripe('GET', `/v1/refunds/${rf.id}`, null, UA)).j; if (seen.at(-1) !== cur.status) seen.push(cur.status); }
        const b2 = await bal(UA);
        rec('U6', 'FULLY UNFUNDED refund: €100 refund when the account holds less than €100 in total (available + incoming) — what Stripe does', 'stripe-test-api', rf.id ? 'INFO' : 'FAIL',
          { refund: rf.id, error: rf.error && rf.error.message, shortfall_cents: shortfall, status_at_creation: rf.status, pending_reason: rf.pending_reason, statuses_seen: seen, final_status: cur.status, final_pending_reason: cur.pending_reason, failure_reason: cur.failure_reason, waited_s: Math.round((Date.now() - t0) / 1000), balance_before_refund: b1, balance_after_refund: b2 });
        // a second refund attempt while the balance is already short: the most a buyer could be owed again in practice
        const pi2 = (await stripe('POST', '/v1/payment_intents', { amount: 2000, currency: 'eur', payment_method: 'pm_card_visa', confirm: 'true', allowed_payment_method_types: ['card'],
          application_fee_amount: 300, metadata: { plotart_order: 'harness-unfunded-2', run: RUN } }, UA, `harness-${RUN}-unf-pi2`)).j;
        const b3 = await bal(UA);
        const rf2 = (await stripe('POST', '/v1/refunds', { payment_intent: pi2.id, amount: 2000, refund_application_fee: 'false', metadata: { plotart_refund: 'harness-unfunded-2' } }, UA, `harness-${RUN}-unf-rf2`)).j;
        let cur2 = rf2; for (let i = 0; i < 12 && cur2.status === 'pending'; i++) { await sleep(5000); cur2 = (await stripe('GET', `/v1/refunds/${rf2.id}`, null, UA)).j; }
        rec('U7', 'a further refund while the balance is already short or negative', 'stripe-test-api', rf2.id ? 'INFO' : 'FAIL',
          { refund: rf2.id, error: rf2.error && rf2.error.message, balance_before_refund: b3, status_at_creation: rf2.status, pending_reason: rf2.pending_reason, final_status: cur2.status, balance_after_refund: await bal(UA) });
      }
    }
  } catch (e) { rec('U9', 'unfunded refund test', 'stripe-test-api', 'FAIL', { error: e.message, code: e.code }); }
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
