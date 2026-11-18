// END-TO-END · the pilot's own Workers (Miniflare, local D1) against the REAL Stripe test API, with REAL signed webhook
// deliveries forwarded by `stripe listen --forward-connect-to http://127.0.0.1:<port>/v1/stripe/webhook`, and the buyer
// paying on Stripe's hosted Checkout in headless Chromium (Playwright). Called by stripe-testmode-checks.mjs (phase e2e).
// Results are labelled source "stripe-test-api+pilot": Stripe's real responses and events, processed by the pilot's code.
import { readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { createHmac } from 'node:crypto';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';

const HERE = new URL('..', import.meta.url).pathname;
const SRC = 'stripe-test-api+pilot';

export async function e2e({ rec, KEY, ACCOUNT, RUN, port, whsec, stripe, sleep }) {
  const ORIGIN = 'https://plotart-checkout-test.invalid';
  const ENVV = { CHECKOUT_PILOT_ENABLED: 'true', STRIPE_SECRET_KEY: KEY, STRIPE_WEBHOOK_SECRET: whsec, CHECKOUT_ORIGIN: ORIGIN };
  const terms = JSON.parse(readFileSync(HERE + 'agreements/payment-test/fingerprints.json', 'utf8')).documents;
  const built = readFileSync(HERE + 'src/payment-terms.js', 'utf8');
  if (!built.includes('PA-PAY-TEST-01')) { rec('E0', 'the Workers were built with the TEST ONLY texts (CHECKOUT_TARGET=test)', 'local', 'FAIL'); return; }
  // Runtime key test: if a narrower restricted TEST key is supplied, the PUBLIC checkout Worker (checkout, webhooks, sweep,
  // reimbursements) uses it, while the Studio Worker (onboarding, refunds, founder actions) and this harness keep the main key.
  const RUNTIME = process.env.STRIPE_RUNTIME_KEY || '';
  const runtimeOk = /^rk_test_[A-Za-z0-9]+$/.test(RUNTIME);
  const ENVC = runtimeOk ? { ...ENVV, STRIPE_SECRET_KEY: RUNTIME } : ENVV;
  // Every outbound request from the public checkout Worker is observed: which key it carried (never the key itself), the
  // endpoint and the HTTP status; Stripe's error message is kept for any permission failure.
  const CW_CALLS = [];
  const keyName = auth => { const k = String(auth || '').replace(/^Bearer\s+/, ''); return !k ? 'none' : k === RUNTIME ? 'runtime' : k === KEY ? 'RUNNER (fallback!)' : 'other'; };
  const cwOutbound = async req => {
    const u = new URL(req.url), item = { method: req.method, path: u.pathname.replace(/(acct|cs|pi|ch|fee|re|dp|txn|py|po)_(test_)?[A-Za-z0-9]+/g, '$1_…'), host: u.host, key: u.host === 'api.stripe.com' ? keyName(req.headers.get('Authorization')) : 'n/a', connected: !!req.headers.get('Stripe-Account') };
    CW_CALLS.push(item);   // recorded before the call, so a failed call is still visible
    let res;
    try {   // re-issue with Node's own fetch (Miniflare's Request object is not passed through as is)
      res = await fetch(req.url, { method: req.method, headers: Object.fromEntries(req.headers), body: ['GET', 'HEAD'].includes(req.method) ? undefined : await req.arrayBuffer(), redirect: 'manual' });
    } catch (e) { item.status = 'network_error'; item.error = String(e.message).slice(0, 200); throw e; }
    const buf = await res.arrayBuffer();
    item.status = res.status;
    if (u.host === 'api.stripe.com' && res.status >= 400) { try { const j = JSON.parse(new TextDecoder().decode(buf)); item.stripe_error = j.error && { type: j.error.type, code: j.error.code, message: String(j.error.message || '').slice(0, 300) }; } catch { /* */ } }
    return new Response(buf, { status: res.status, headers: res.headers });
  };
  const S = await start({ port, env: ENVV, checkout: { env: ENVC, outbound: cwOutbound } });
  rec('E17a', 'which key the public checkout Worker is configured with', 'local', 'INFO', { public_worker_key: runtimeOk ? 'separate restricted TEST key (CHECKOUT_TEST_STRIPE_RUNTIME_KEY)' : RUNTIME ? 'runtime secret present but not an rk_test_ key: NOT used' : 'same key as the harness (no runtime key supplied)',
    worker_env_has_runner_key: Object.values(ENVC).includes(KEY) && runtimeOk });
  if (runtimeOk) {   // the runtime key must NOT be able to read artist identity or bank details
    const h = { Authorization: `Bearer ${RUNTIME}`, 'Stripe-Version': '2026-10-28.endive' };
    const st = async u => (await fetch('https://api.stripe.com' + u, { headers: h })).status;
    const probes = { v1_account: await st(`/v1/accounts/${ACCOUNT}`), v1_external_accounts: await st(`/v1/accounts/${ACCOUNT}/external_accounts?limit=1`), v2_account_identity: await st(`/v2/core/accounts/${ACCOUNT}?include[0]=identity`) };
    rec('E17b', 'the runtime key is refused artist account, identity and bank data (HTTP status only recorded)', 'stripe-test-api', Object.values(probes).every(x => x === 401 || x === 403) ? 'PASS' : 'FAIL', probes);
    // E17c · actions the runtime key should NOT be able to take. Each request is deliberately invalid (zero amount, unknown
    // object), so even if a permission were wrongly granted nothing could happen: Stripe would answer 400/404 instead of 401/403.
    // each probe is deliberately incomplete or invalid, so nothing can be created even if a permission were wrongly granted;
    // Stripe's error type, code and message are recorded so a 400/404 (permission granted) is distinguishable from 401/403
    const probe = async (method, u, { form = null, json = null, acct = null } = {}) => {
      const r = await fetch('https://api.stripe.com' + u, { method, headers: { ...h, ...(acct ? { 'Stripe-Account': acct } : {}), ...(form ? { 'Content-Type': 'application/x-www-form-urlencoded' } : {}), ...(json ? { 'Content-Type': 'application/json' } : {}) },
        body: form ? new URLSearchParams(form) : json ? JSON.stringify(json) : undefined });
      let e = null; try { const j = await r.json(); e = j.error && { type: j.error.type, code: j.error.code || null, message: String(j.error.message || '').slice(0, 200) }; } catch { /* */ }
      return { status: r.status, denied: r.status === 401 || r.status === 403, stripe_error: e };
    };
    const denied = {
      create_payment_intent_on_artist_account: await probe('POST', '/v1/payment_intents', { form: { amount: '0', currency: 'eur' }, acct: ACCOUNT }),
      create_refund_on_artist_account: await probe('POST', '/v1/refunds', { form: {}, acct: ACCOUNT }),   // no parameters: 400 if permitted, 403 if not
      read_artist_balance: await probe('GET', '/v1/balance', { acct: ACCOUNT }),
      list_artist_payouts: await probe('GET', '/v1/payouts?limit=1', { acct: ACCOUNT }),
      create_v2_account: await probe('POST', '/v2/core/accounts', { json: {} }) };
    rec('E17c', 'the runtime key cannot create PaymentIntents directly, refund, read balances or payouts, or create accounts (incomplete or invalid requests; status and Stripe error recorded)', 'stripe-test-api',
      Object.entries(denied).every(([k, x]) => x.denied || k === 'create_refund_on_artist_account') ? 'PASS' : 'FAIL',
      { ...denied, note: 'create_refund_on_artist_account is informational here: with no parameters Stripe validates them before checking permissions (400). The refund restriction is verified by E17e (run 31) with a valid refund request.' });
  } else rec('E17b', 'narrower runtime key not supplied: access separation not verified', 'local', 'SKIP', { needed: 'secret CHECKOUT_TEST_STRIPE_RUNTIME_KEY in the checkout-test environment' });
  const { db } = S, CW = S.checkoutWorker;
  const q = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results;
  const call = async (method, path, email, body) => { const r = await S.mf.dispatchFetch(S.url + path, { method, headers: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
    const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* */ } return { s: r.status, j }; };
  const order = id => db.prepare('SELECT * FROM checkout_orders WHERE id = ?').bind(id).first();
  const waitFor = async (fn, ms = 90_000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { const v = await fn(); if (v) return v; await sleep(2000); } return null; };
  // fee model B: wait until the pilot has reimbursed the processing fee (at payment, or by the 15-minute sweep, run here directly)
  const reimbursedFor = async id => waitFor(async () => { await CW.scheduled({ cron: '*/15 * * * *' }).catch(() => {}); const o = await order(id); const P = o && o.processing && JSON.parse(o.processing); return P && P.status && P.status !== 'awaiting_fee' ? P : null; }, 120_000);
  const sumType = (bt, t) => ((bt && bt.fee_details) || []).filter(d => d.type === t).reduce((a, d) => a + d.amount, 0);
  const feeRefundsOf = async fee => ((await stripe('GET', `/v1/application_fees/${fee}/refunds?limit=20`)).j.data || []);
  let browser = null;
  try {
    const GAL = `gal+${RUN}@plotnua.invalid`, ago = d => new Date(Date.now() - d * 86400_000).toISOString(), FAKE = 'a'.repeat(64);
    await seedPublished(db, { id: 'agal', slug: 'gal', email: GAL, name: 'E2E Test Gallery Artist', works: 5, publishedAt: ago(30) });
    await db.prepare("UPDATE artists SET founding = 0 WHERE id = 'agal'").run();
    await db.prepare("INSERT INTO gallery_agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at) VALUES ('PA-GAA-2026-11','gallery_artist_agreement','t','fixed',?,?,'2018-01-01T00:00:00Z',?)").bind(FAKE, FAKE, ago(0)).run();
    await db.prepare(`INSERT INTO gallery_agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, method, statement, created_at) VALUES ('gaa1','ev1','agal','PA-GAA-2026-11',?,?,?,?, 'E2E','studio_checkbox','test',?)`).bind(FAKE, FAKE, ago(20), GAL, ago(20)).run();
    await db.prepare("INSERT INTO artist_terms (artist_id, track, commission_bp, set_by, created_at, updated_at) VALUES ('agal','gallery_artist',1500,?,?,?)").bind(FOUNDER, ago(20), ago(20)).run();
    for (const [id, ref] of [['l1', 'PA-E-261116-E2E001'], ['l2', 'PA-E-261116-E2E002'], ['l3', 'PA-E-261116-E2E003'], ['l4', 'PA-E-261116-E2E004'], ['l5', 'PA-E-261116-E2E005']])
      await db.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, route, introduced_at, founding, logged_by, logged_at) VALUES (?,?, 'agal', 'relay', ?, 0, 'relay', ?)`).bind(id, ref, ago(5), ago(5)).run();
    for (const [id, t] of Object.entries(terms)) await db.prepare('INSERT INTO payment_terms (doc_id, kind, title, html_sha256, effective_at, created_at) VALUES (?,?,?,?,?,?)').bind(id, t.kind, t.title, t.html_sha256, '2018-01-01T00:00:00Z', ago(0)).run();
    const add = (await call('GET', '/api/checkout', GAL)).j.addendum;
    await call('POST', '/api/checkout/opt-in', GAL, { accept: true, doc_id: add.doc_id, html_sha256: add.html_sha256 });
    await db.prepare("INSERT INTO payment_accounts (artist_id, account_id, country, created_at, updated_at) VALUES ('agal', ?, 'IE', ?, ?)").bind(ACCOUNT, ago(0), ago(0)).run();
    const rf = await call('POST', '/api/admin/checkout/accounts/agal/refresh', FOUNDER, {});
    rec('E1', 'the pilot reads the onboarded test account from Stripe and marks it ready', SRC, rf.s === 200 && rf.j.membership.ready ? 'PASS' : 'FAIL', rf.j);

    const DELIVERY = { collection_county: 'Dublin', destination: 'Cork, Ireland', unpacked_cm: '60 × 50 × 3', packed_cm: '75 × 65 × 12', weight_kg: 6, medium: 'Oil on board', framing: 'Framed', glazing: 'None',
      condition: 'Excellent', access_notes: null, organiser: 'artist', packer: 'artist', transport_booker: 'artist', transport_contracting_party: 'artist', transport_payer: 'artist', transporter_name: 'SIMULATED courier',
      installation: 'not_applicable', import_costs: 'not_applicable', cover_type: 'transit_insurance', cover_provider: 'SIMULATED test cover', covered_value_cents: 100000, valuation_basis: 'Agreed price', insured_party: 'transporter',
      excess_cents: null, exclusions: null, cover_period: 'Collection to signed delivery', claims_contact: 'claims@example.invalid', delivery_window: '5–8 working days', tracking: 'Tracked', signed_receipt: true,
      condition_photos: true, return_method: 'SIMULATED courier collection', return_address: 'SIMULATED studio address, Dublin', return_cost_cents: 9500, return_cost_basis: 'estimated_maximum', return_arranged_by: 'buyer', shipment_confirmation_ref: 'SIM-1', shipment_confirmed_by: 'SIMULATED', shipment_confirmed_on: new Date().toISOString().slice(0, 10),
      cover_confirmation_ref: 'SIM-COVER-1', cover_confirmed_by: 'SIMULATED', cover_confirmed_on: new Date().toISOString().slice(0, 10) };
    const ALL = { available: true, location: true, condition: true, framing: true, dimensions: true, packing_and_handover: true, returns: true, seller_information: true };
    const sp = await call('PUT', '/api/checkout/seller-profile', GAL, { legal_name: 'E2E Test Seller (SIMULATED)', address: 'SIMULATED address, Dublin, Ireland', email: 'seller@plotnua.invalid', phone: '+353 1 000 0000', trader_status: 'trader', confirm: true });
    if (sp.s !== 200) throw new Error('test setup: seller information not saved ' + JSON.stringify(sp.j).slice(0, 200));
    async function quote(work, ref, artwork = 100000, delivery = 7500) {
      const c = await call('POST', '/api/admin/checkout/orders', FOUNDER, { artist_id: 'agal', artwork_id: work, enquiry_ref: ref, buyer_email: `buyer+${RUN}@plotnua.invalid` });
      if (c.s !== 200 || !c.j.order) throw new Error(`test setup: order for ${work} / ${ref} not created (${c.s} ${JSON.stringify(c.j).slice(0, 200)})`);
      const id = c.j.order.id;
      await call('PUT', `/api/admin/checkout/orders/${id}`, FOUNDER, { artwork_cents: artwork, delivery_cents: delivery, delivery: { ...DELIVERY, covered_value_cents: artwork } });
      await call('POST', `/api/admin/checkout/orders/${id}/send`, FOUNDER, {});
      await call('POST', `/api/checkout/orders/${id}/approve`, GAL, { quote_version: (await order(id)).quote_version, confirm: ALL });
      const iss = await call('POST', `/api/admin/checkout/orders/${id}/issue`, FOUNDER, { days: 1, linked_check_confirmed: true });
      const tok = iss.j.buyer_link.split('/q/')[1];
      const r = await CW.fetch(`http://checkout.local/q/${tok}/pay`, { method: 'POST', redirect: 'manual', headers: { 'Content-Type': 'application/x-www-form-urlencoded', Origin: ORIGIN }, body: 'accept_terms=PA-BPT-TEST-01' });
      return { id, tok, status: r.status, url: r.headers.get('Location') };
    }
    // Pays on the REAL hosted Checkout page. Diagnostics never include payment details: input values are masked in
    // screenshots and redacted from accessibility snapshots; URLs are reduced to origin + path (no query, no fragment).
    const DIAG = (tag, name) => `${HERE}stripe-test-evidence/checkout-${tag}-${name}`;
    const safeUrl = u => { try { const x = new URL(u); return x.origin + x.pathname.replace(/cs_(test|live)_[A-Za-z0-9]+/, 'cs_…'); } catch { return String(u).slice(0, 60); } };
    const redact = t => String(t || '').replace(/^\s*- option .*\n?/gm, '').replace(/^(\s*- (?:textbox|combobox|spinbutton|searchbox)[^:\n]*):.*$/gm, '$1: [redacted]').replace(/[\w.+-]+@[\w-]+\.[\w.]+/g, '[email]');
    async function snapshot(page, tag, stage) {
      const out = { stage, url: safeUrl(page.url()), title: await page.title().catch(() => ''), frames: [] };
      for (const f of page.frames()) {
        let aria = ''; try { aria = await f.locator('body').ariaSnapshot({ timeout: 5000 }); } catch (e) { aria = 'unavailable: ' + String(e.message).split('\n')[0]; }
        out.frames.push({ url: safeUrl(f.url()), aria: redact(aria).slice(0, 8000) });
      }
      const masks = page.frames().map(f => f.locator('input'));
      await page.screenshot({ path: DIAG(tag, stage + '.png'), fullPage: true, mask: masks }).catch(() => {});
      return out;
    }
    // first VISIBLE match in the page or any of its frames (role lookups do not cross iframes; CSS does cross open shadow roots)
    async function anyFrame(page, build, timeout = 30_000) {
      const t0 = Date.now();
      do {
        for (const f of page.frames()) { const l = build(f).first(); if (await l.isVisible().catch(() => false)) return l; }
        await page.waitForTimeout(500);
      } while (Date.now() - t0 < timeout);
      return null;
    }
    async function payInBrowser(url, card, tag) {
      if (!browser) { const req = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json'); browser = await req('playwright').chromium.launch(); }
      const page = await browser.newPage({ locale: 'en-IE', timezoneId: 'Europe/Dublin', viewport: { width: 1280, height: 1000 } });
      const diag = { pageErrors: [], consoleErrors: [], failedRequests: [], httpErrors: [], snapshots: [], steps: [] };
      page.on('pageerror', e => diag.pageErrors.push(String(e.message).slice(0, 300)));
      page.on('console', m => { if (m.type() === 'error') diag.consoleErrors.push(redact(m.text()).slice(0, 300)); });
      page.on('requestfailed', r => diag.failedRequests.push(`${r.method()} ${safeUrl(r.url())} ${r.failure() && r.failure().errorText}`));
      page.on('response', r => { if (r.status() >= 400) diag.httpErrors.push(`${r.status()} ${r.request().method()} ${safeUrl(r.url())}`); });
      const step = s => diag.steps.push(`${new Date().toISOString().slice(11, 19)} ${s}`);
      // The pilot's success_url/cancel_url use the test origin ${ORIGIN}, which deliberately does not resolve. Serve it in
      // this browser from the locally running pilot checkout Worker, so Stripe's redirect lands on the pilot's REAL return
      // page (run 14: both payments succeeded but the redirect failed with ERR_NAME_NOT_RESOLVED).
      await page.route(ORIGIN + '/**', async rt => {
        const u = new URL(rt.request().url());
        const r = await CW.fetch(`http://checkout.local${u.pathname}${u.search}`, { method: rt.request().method() });
        diag.returnPage = { path: u.pathname.replace(/\/q\/[^/]+/, '/q/…'), result: u.searchParams.get('result'), status: r.status };
        await rt.fulfill({ status: r.status, headers: { 'content-type': r.headers.get('content-type') || 'text/html' }, body: await r.text() });
      });
      try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60_000 }); step('loaded ' + safeUrl(page.url()));
        // wait for the hosted page to show its card form, or a collapsed card option, before doing anything
        const cardBoxIn = f => f.getByRole('textbox', { name: /card number/i }).or(f.locator('#cardNumber, input[autocomplete="cc-number"], input[name="cardnumber"]'));
        const cardOptIn = f => f.getByTestId('card-accordion-item-button').or(f.getByRole('button', { name: /^card$/i })).or(f.getByRole('radio', { name: /^card$/i }));
        let box = await anyFrame(page, cardBoxIn, 20_000);
        diag.snapshots.push(await snapshot(page, tag, 'loaded'));
        if (!box) { const opt = await anyFrame(page, cardOptIn, 5_000); if (opt) { await opt.click(); step('opened the card option'); box = await anyFrame(page, cardBoxIn, 30_000); } }
        if (!box) throw new Error('card number field not visible in the page or any frame');
        step('card form visible'); await box.fill(card);
        const fillIf = async (build, v, t = 5_000) => { const l = await anyFrame(page, build, t); if (l) await l.fill(v).catch(() => {}); return !!l; };
        await fillIf(f => f.getByRole('textbox', { name: /expir|mm \/ yy/i }).or(f.locator('#cardExpiry, input[autocomplete="cc-exp"]')), '12 / 34');
        await fillIf(f => f.getByRole('textbox', { name: /cvc|security code/i }).or(f.locator('#cardCvc, input[autocomplete="cc-csc"]')), '123');
        await fillIf(f => f.getByRole('textbox', { name: /name on card|cardholder/i }).or(f.locator('#billingName, input[autocomplete="cc-name"]')), 'E2E Test Buyer', 2_000);
        const ctry = await anyFrame(page, f => f.getByRole('combobox', { name: /^country/i }).or(f.locator('#billingCountry, select[autocomplete="country"]')), 3_000);
        if (ctry) { await ctry.selectOption('IE').catch(() => ctry.selectOption({ label: 'Ireland' })).catch(() => {}); step('billing country: ' + (await ctry.inputValue().catch(() => '?'))); }
        await fillIf(f => f.getByRole('textbox', { name: /postal|eircode|zip/i }).or(f.locator('#billingPostalCode, input[autocomplete="postal-code"]')), 'D02 X285', 2_000);
        step('card details entered (values not recorded)');
        // the main Pay button only: an exact "Pay" / "Pay €…" name. Run 13 matched "Pay securely with Link" (Stripe's Link
        // wallet), which opened a Link window instead of paying.
        const pay = await anyFrame(page, f => f.getByTestId('hosted-payment-submit-button').or(f.getByRole('button', { name: /^pay(\s+€\s?[\d.,]+)?$/i })).or(f.locator('button.SubmitButton')), 30_000);
        if (!pay) throw new Error('Pay button not visible in the page or any frame');
        step('pay button visible: ' + ((await pay.getAttribute('data-testid').catch(() => null)) || (await pay.innerText().catch(() => '')).slice(0, 30)));
        await pay.click();
        const back = page.waitForURL(/plotart-checkout-test\.invalid/, { timeout: 90_000 }).then(() => 'returned');
        const linkWin = page.getByText(/complete your payment in the open link window/i).waitFor({ state: 'visible', timeout: 90_000 }).then(() => 'link');
        const how = await Promise.race([back, linkWin]).catch(e => { throw e; });
        if (how === 'link') throw new Error('a Link wallet window opened instead of the card payment');
        step(`returned to the pilot's return page (result=${diag.returnPage && diag.returnPage.result}, HTTP ${diag.returnPage && diag.returnPage.status})`);
        if (!diag.returnPage || diag.returnPage.result !== 'success') throw new Error('Checkout did not return with result=success');
        return { ok: true, diag };
      } catch (e) {
        step('ERROR ' + String(e.message).split('\n')[0].slice(0, 200));
        diag.snapshots.push(await snapshot(page, tag, 'failed').catch(() => ({ stage: 'failed', error: 'snapshot unavailable' })));
        diag.finalUrl = safeUrl(page.url());
        throw Object.assign(e, { diag });
      } finally {
        diag.finalUrl = diag.finalUrl || safeUrl(page.url());
        writeFileSync(DIAG(tag, 'diagnostics.json'), JSON.stringify(diag, null, 2));
        await page.close();
      }
    }

    // 1 · payment, verified only by Stripe's signed event
    // ---- coverage-only run (request file: "coverage_only": true): the two runtime-key paths not yet exercised
    let COVERAGE = false; try { COVERAGE = JSON.parse(readFileSync(HERE + 'test/stripe-test-run.json', 'utf8')).coverage_only === true; } catch { /* */ }
    if (COVERAGE) {
      const callsFrom = i => CW_CALLS.slice(i).filter(c => c.host === 'api.stripe.com');
      const summary = cs => ({ calls: cs.length, by_key: cs.reduce((a, c) => (a[c.key] = (a[c.key] || 0) + 1, a), {}), list: cs.map(c => `${c.method} ${c.path}${c.connected ? ' [connected]' : ' [platform]'} → ${c.status}${c.stripe_error ? ' ' + c.stripe_error.code : ''}`) });
      // E19 · part 1: open a checkout through the Worker; Stripe will expire it at its expires_at (the Worker's normal path)
      const i19 = CW_CALLS.length;
      const ox = await quote('wagal1', 'PA-E-261116-E2E001');
      const sx = (await q("SELECT id, expires_at FROM checkout_sessions WHERE order_id = ? AND status = 'open'", ox.id))[0];
      const resvAtOpen = (await q("SELECT expires_at FROM artwork_reservations WHERE artwork_id = 'wagal1'"))[0];
      // E20 · a REAL sandbox dispute, then the fee-read fallback
      const od = await quote('wagal3', 'PA-E-261116-E2E003', 5000, 0);
      let dPaid = false; try { await payInBrowser(od.url, '4000000000000259', 'coverage-dispute'); dPaid = true; } catch (e) { rec('E20a', 'buyer pays with the dispute test card', SRC, 'FAIL', { error: String(e.message).split('\n')[0].slice(0, 300) }); }
      const opened = dPaid ? await waitFor(async () => (await order(od.id)).dispute_status === 'open', 180_000) : null;
      if (opened) {
        const O = await order(od.id);
        const d = (await stripe('GET', `/v1/disputes?payment_intent=${encodeURIComponent(O.payment_intent)}&limit=1`, null, ACCOUNT)).j.data[0];   // runner key: the real dispute
        const before = (JSON.parse(O.dispute_fees || '{}')[d.id] || {}).checked_at || null;
        const { balance_transactions: _omit, ...withoutFees } = d;   // SIMULATED INPUT: the same real dispute, with its fee lines removed
        const ev = { id: `evt_coverage_${RUN}`, object: 'event', type: 'charge.dispute.updated', livemode: false, created: Math.floor(Date.now() / 1000), account: ACCOUNT, api_version: '2026-10-28.endive', data: { object: withoutFees } };
        const raw = JSON.stringify(ev), t = Math.floor(Date.now() / 1000), sig = `t=${t},v1=${createHmac('sha256', whsec).update(`${t}.${raw}`).digest('hex')}`;
        const i20 = CW_CALLS.length;
        const wh = await CW.fetch('http://checkout.local/v1/stripe/webhook', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Stripe-Signature': sig }, body: raw });
        const whBody = await wh.text();
        const reads = callsFrom(i20).filter(c => c.method === 'GET' && /^\/v1\/disputes\//.test(c.path));
        const O2 = await order(od.id), info = JSON.parse(O2.dispute_fees || '{}')[d.id] || {};
        const fees = await q("SELECT amount_cents, provider_ref FROM order_ledger WHERE order_id = ? AND kind = 'dispute_fee'", od.id);
        rec('E20', 'dispute-fee fallback: an event WITHOUT fee lines (simulated input, signed locally) makes the Worker read the REAL dispute from Stripe with the runtime key; fees recorded from Stripe’s response', SRC,
          wh.status === 200 && reads.length >= 1 && reads.every(c => c.key === 'runtime' && c.status === 200 && c.connected) && info.status === 'recorded' && info.checked_at !== before && fees.length >= 1 ? 'PASS' : 'FAIL',
          { simulated: 'event envelope signed locally with the run’s webhook secret; data.object = the real dispute object fetched from Stripe with balance_transactions REMOVED',
            from_stripe: 'the Worker’s GET of the dispute (status and key below) and the fee lines it booked', webhook_http: wh.status, webhook_response: whBody.slice(0, 200),
            dispute_reads: reads.map(c => ({ path: c.path, key: c.key, status: c.status, connected: c.connected })), dispute_fees_status: info, dispute_fee_lines: fees, calls: summary(callsFrom(i20)) });
      } else rec('E20', 'dispute-fee fallback', SRC, 'SKIP', { blocked_by: dPaid ? 'the sandbox dispute did not open within 3 minutes' : 'E20a payment failed' });
      // E19 · part 2: wait for Stripe's own expiry of the open session (expires_at), the signed event, and the Worker's release
      if (sx) {
        const until = Date.parse(sx.expires_at) + 25 * 60_000;
        let st = null, released = false;
        while (Date.now() < until) {
          st = (await stripe('GET', `/v1/checkout/sessions/${sx.id}`, null, ACCOUNT)).j.status;   // runner key: Stripe's view
          released = (await order(ox.id)).status === 'quoted' && !(await q("SELECT 1 FROM artwork_reservations WHERE artwork_id = 'wagal1'")).length;
          if (st === 'expired' && released) break;
          await sleep(30_000);
        }
        const evs = await q("SELECT type, status FROM payment_events WHERE type = 'checkout.session.expired' AND object_id = ?", sx.id);
        const cs = callsFrom(i19).filter(c => /checkout\/sessions/.test(c.path));
        rec('E19', 'normal expiry path: Stripe expires the open session at its expires_at; the signed checkout.session.expired event reaches the Worker, which releases the reservation and returns the quote to payable', SRC,
          st === 'expired' && released && evs.some(e => e.status === 'processed') ? 'PASS' : 'FAIL',
          { session_expires_at: sx.expires_at, reservation_at_open: resvAtOpen, stripe_session_status: st, worker_released: released, expired_event: evs,
            worker_checkout_session_calls: cs.map(c => `${c.method} ${c.path} → ${c.status} (${c.key})`),
            note: 'The public Worker never calls Stripe’s expire endpoint in normal operation: expiry is done by Stripe at expires_at, or by the Studio Worker (existing key) when a quote is revised or cancelled.' });
      } else rec('E19', 'normal expiry path', SRC, 'FAIL', { reason: 'no open session was created' });
      const all = callsFrom(0);
      rec('E17d', 'coverage run: every Stripe API call made by the public checkout Worker used the runtime key', 'stripe-test-api+pilot',
        !runtimeOk ? 'SKIP' : all.length && all.every(c => c.key === 'runtime') && !all.some(c => c.status === 401 || c.status === 403) ? 'PASS' : 'FAIL', summary(all));
      return;
    }
    // ---- reimbursement-evidence run (request file: "reimbursement_evidence": true): what Stripe returns when it accepts a
    // processing reimbursement (an application-fee refund) and whether the credit to the artist's Stripe balance can be seen
    let EVID = false; try { EVID = JSON.parse(readFileSync(HERE + 'test/stripe-test-run.json', 'utf8')).reimbursement_evidence === true; } catch { /* */ }
    if (EVID) {
      const callsFrom = i => CW_CALLS.slice(i).filter(c => c.host === 'api.stripe.com');
      const rkGet = async (path, account = null) => {   // read-only probe with the runtime key (the key itself is never printed)
        const h = { Authorization: `Bearer ${RUNTIME}`, 'Stripe-Version': '2026-10-28.endive' }; if (account) h['Stripe-Account'] = account;
        const r = await fetch('https://api.stripe.com' + path, { headers: h }); const j = await r.json().catch(() => ({}));
        return { status: r.status, error: j.error ? { type: j.error.type, code: j.error.code, message: String(j.error.message || '').slice(0, 300) } : null, j };
      };
      const ov = await quote('wagal2', 'PA-E-261116-E2E002', 20000, 0);
      let paid = false; try { await payInBrowser(ov.url, '4242424242424242', 'evidence'); paid = true; } catch (e) { rec('E21a', 'buyer pays €200 on the real hosted Checkout page', SRC, 'FAIL', { error: String(e.message).split('\n')[0].slice(0, 300) }); }
      const O = paid ? await waitFor(async () => { const o = await order(ov.id); return o.payment_status === 'paid' ? o : null; }, 90_000) : null;
      if (!O) { rec('E21', 'reimbursement evidence', SRC, 'SKIP', { blocked_by: paid ? 'the signed completion did not arrive within 90 s' : 'E21a payment failed' }); return; }
      const P = await reimbursedFor(ov.id), O2 = await order(ov.id);
      const fee = O2.application_fee_id;
      const ch = (await stripe('GET', `/v1/charges/${O2.charge_id}?expand[]=balance_transaction`, null, ACCOUNT)).j;
      rec('E21a', 'a real €200 sandbox payment (15% commission = €30 application fee); the Worker reads Stripe’s actual processing fee and VAT and reimburses it through an application-fee refund, on the runtime key', SRC,
        P && P.status === 'reimbursed' && P.cost === sumType(ch.balance_transaction, 'stripe_fee') + sumType(ch.balance_transaction, 'tax') ? 'PASS' : 'FAIL',
        { pilot_processing: P, charge_created: ch.created && new Date(ch.created * 1000).toISOString(), balance_transaction_created: ch.balance_transaction && ch.balance_transaction.created && new Date(ch.balance_transaction.created * 1000).toISOString(),
          fee_lines: ch.balance_transaction && ch.balance_transaction.fee_details, worker_calls: callsFrom(0).map(c => `${c.method} ${c.path}${c.connected ? ' [connected]' : ''} → ${c.status} (${c.key})`) });
      // what Stripe returned when it accepted the refund (as the pilot stored it) and the same object read back from Stripe
      const frs = await feeRefundsOf(fee), fr = frs.find(x => x.metadata && x.metadata.plotart_kind === 'processing_reimbursement') || null;
      const feeObj = (await stripe('GET', `/v1/application_fees/${fee}`)).j;
      const pbt = fr && typeof fr.balance_transaction === 'string' ? (await stripe('GET', `/v1/balance_transactions/${fr.balance_transaction}`)).j : null;
      rec('E21b', 'Stripe’s acceptance of the application-fee refund: a fee_refund object (id, amount, created time, platform balance transaction) and the application fee’s amount_refunded', SRC,
        fr && fr.object === 'fee_refund' && fr.amount === P.cost && fr.created && feeObj.amount_refunded === P.cost && P.fee_refund && P.fee_refund.id === fr.id ? 'PASS' : 'FAIL',
        { fee_refund: fr && { id: fr.id, object: fr.object, amount: fr.amount, currency: fr.currency, created: fr.created && new Date(fr.created * 1000).toISOString(), fee: fr.fee, balance_transaction: fr.balance_transaction, metadata: fr.metadata },
          stored_by_pilot: P && P.fee_refund, application_fee: { amount: feeObj.amount, amount_refunded: feeObj.amount_refunded, refunded: feeObj.refunded, account: feeObj.account },
          platform_balance_transaction: pbt && { id: pbt.id, type: pbt.type, amount: pbt.amount, net: pbt.net, status: pbt.status, created: pbt.created && new Date(pbt.created * 1000).toISOString(), available_on: pbt.available_on && new Date(pbt.available_on * 1000).toISOString(), source: pbt.source, reporting_category: pbt.reporting_category } });
      // the artist's side: a balance transaction on the connected account for that fee refund (runner key: the harness, not the Worker)
      const findCredit = async () => {
        const bySource = fr ? await stripe('GET', `/v1/balance_transactions?source=${encodeURIComponent(fr.id)}&limit=5`, null, ACCOUNT) : null;
        const recent = await stripe('GET', '/v1/balance_transactions?limit=25', null, ACCOUNT);
        // run 33 showed the artist-side credit is an 'adjustment' whose source is the payment's CHARGE (not the fee refund),
        // created in the same second as the fee refund, for the same amount
        const hit = ((recent.j.data) || []).filter(b => fr && (b.source === fr.id || (b.type === 'adjustment' && b.source === O2.charge_id && b.amount === fr.amount && Math.abs(b.created - fr.created) <= 60)));
        return { bySource, recent, hit };
      };
      let cr = await findCredit(); for (let i = 0; i < 10 && !cr.hit.length && !((cr.bySource && cr.bySource.j.data) || []).length; i++) { await sleep(3000); cr = await findCredit(); }
      const credit = cr.hit[0] || ((cr.bySource && cr.bySource.j.data) || [])[0] || null;
      const typesNear = ((cr.recent.j.data) || []).slice(0, 12).map(b => ({ type: b.type, amount: b.amount, status: b.status, source: typeof b.source === 'string' ? b.source.replace(/^(\w+?)_.*/, '$1_…') : null, created: new Date(b.created * 1000).toISOString() }));
      rec('E21c', 'the artist’s side: a balance transaction on the connected account crediting the reimbursed amount (read with the harness key)', SRC,
        credit && credit.amount === P.cost ? 'PASS' : credit ? 'INFO' : 'FAIL',
        { credit: credit && { id: credit.id, type: credit.type, amount: credit.amount, net: credit.net, fee: credit.fee, status: credit.status, created: new Date(credit.created * 1000).toISOString(), available_on: credit.available_on && new Date(credit.available_on * 1000).toISOString(), source: credit.source, description: credit.description, reporting_category: credit.reporting_category },
          by_source_query: cr.bySource && { status: cr.bySource.status, count: ((cr.bySource.j.data) || []).length, error: cr.bySource.j.error && cr.bySource.j.error.message }, recent_connected_types: typesNear });
      // what the pilot itself can read on the runtime key (read-only probes)
      const p1 = await rkGet(`/v1/application_fees/${fee}/refunds?limit=5`), p2 = await rkGet('/v1/balance_transactions?limit=1', ACCOUNT), p3 = await rkGet('/v1/balance', ACCOUNT);
      rec('E21d', 'runtime key, read-only: the Worker CAN read the fee’s refunds (Stripe’s acceptance) but CANNOT read the artist’s balance or balance transactions with the five adopted permissions', SRC,
        p1.status === 200 && p2.status >= 400 && p3.status >= 400 ? 'PASS' : 'INFO',
        { fee_refunds: { status: p1.status, count: ((p1.j && p1.j.data) || []).length, error: p1.error }, connected_balance_transactions: { status: p2.status, error: p2.error }, connected_balance: { status: p3.status, error: p3.error } });
      const all = callsFrom(0);
      rec('E17d', 'evidence run: every Stripe API call made by the public checkout Worker used the runtime key', SRC,
        !runtimeOk ? 'SKIP' : all.length && all.every(c => c.key === 'runtime') && !all.some(c => c.status === 401 || c.status === 403) ? 'PASS' : 'FAIL',
        { calls: all.length, list: all.map(c => `${c.method} ${c.path}${c.connected ? ' [connected]' : ''} → ${c.status}${c.stripe_error ? ' ' + c.stripe_error.code : ''} (${c.key})`) });
      return;
    }
    const o1 = await quote('wagal1', 'PA-E-261116-E2E001');
    rec('E2', 'the pilot opens real hosted checkout on the artist’s account for the approved quote', SRC, o1.status === 303 && /checkout\.stripe\.com/.test(o1.url || '') ? 'PASS' : 'FAIL', { status: o1.status, host: o1.url && new URL(o1.url).host });
    let paidOk = false;
    try { const r = await payInBrowser(o1.url, '4242424242424242', 'pay'); paidOk = true; rec('E3a', 'buyer pays on the real hosted Stripe Checkout page (headless browser) and Stripe returns them to the pilot with result=success', SRC, 'PASS', { final_url: r.diag.finalUrl, return_page: r.diag.returnPage, steps: r.diag.steps }); }
    catch (e) { rec('E3a', 'buyer pays on the real hosted Stripe Checkout page (headless browser)', SRC, 'FAIL', { error: String(e.message).split('\n')[0].slice(0, 300), final_url: e.diag && e.diag.finalUrl, steps: e.diag && e.diag.steps, page_errors: e.diag && e.diag.pageErrors, http_errors: e.diag && e.diag.httpErrors.slice(0, 10) }); }
    const paid = await waitFor(async () => { const o = await order(o1.id); return o.payment_status === 'paid' ? o : null; }, paidOk ? 90_000 : 20_000);
    const evs = await q("SELECT event_id, type, status FROM payment_events WHERE order_id = ?", o1.id);
    const e3ok = paid && evs.some(e => e.type === 'checkout.session.completed' && e.status === 'processed') && (await db.prepare("SELECT availability FROM artworks WHERE id='wagal1'").first()).availability === 'sold';
    rec('E3', 'a REAL signed checkout.session.completed marks the order paid (and the work sold)', SRC, e3ok ? 'PASS' : paidOk ? 'FAIL' : 'SKIP',
      { ...(paidOk || e3ok ? {} : { blocked_by: 'E3a — no payment was made, so no completion event could arrive; webhook handling NOT exercised' }), payment_status: paid && paid.payment_status, events: evs });
    { // E3c · the signed completion event belongs to THIS order's own Checkout Session, and no other order was touched
      const own = await q(`SELECT pe.event_id, pe.object_id FROM payment_events pe JOIN checkout_sessions cs ON cs.id = pe.object_id
        WHERE pe.type = 'checkout.session.completed' AND pe.status = 'processed' AND pe.order_id = ? AND cs.order_id = ?`, o1.id, o1.id);
      const stray = await q(`SELECT event_id, order_id FROM payment_events WHERE type = 'checkout.session.completed' AND object_id IN (SELECT id FROM checkout_sessions WHERE order_id = ?) AND (order_id IS NULL OR order_id <> ?)`, o1.id, o1.id);
      const sess1 = own[0] && (await stripe('GET', `/v1/checkout/sessions/${own[0].object_id}`, null, ACCOUNT)).j;
      rec('E3c', 'the completion event is for this order’s own Checkout Session (matching client_reference_id, paid on Stripe) and was applied to no other order', SRC,
        own.length === 1 && !stray.length && sess1 && sess1.client_reference_id === o1.id && sess1.payment_status === 'paid' && sess1.payment_intent === (paid && paid.payment_intent) ? 'PASS' : paidOk ? 'FAIL' : 'SKIP',
        { events: own.map(e => e.event_id), stray, stripe_session: sess1 && { client_reference_id_matches: sess1.client_reference_id === o1.id, payment_status: sess1.payment_status, payment_intent_matches: sess1.payment_intent === (paid && paid.payment_intent) } });
    }
    if (paid) {   // E15 · the buyer's confirmation after a REAL verified payment: prepared once, exact text kept, test sink only
      const m = await db.prepare("SELECT * FROM order_messages WHERE order_id = ? AND kind = 'buyer_confirmation'").bind(o1.id).first();
      const dl = m ? await q('SELECT channel, status FROM order_message_deliveries WHERE message_id = ?', m.id) : [];
      const sink = await q("SELECT to_role, to_sha256 FROM checkout_mail_sink WHERE order_id = ? AND kind = 'buyer_confirmation'", o1.id);
      const web = await CW.fetch(`http://checkout.local/q/${o1.tok}/confirmation`);
      const wt = await web.text();
      rec('E15', 'after the REAL signed completion, the buyer confirmation is prepared once with seller, amounts, delivery, returns, accepted terms and cancellation form; held in the test sink only; the buyer link serves the identical text', SRC,
        m && /MODEL CANCELLATION FORM/.test(m.body) && m.body.includes('E2E Test Seller') && m.body.includes('EUR 1075.00') && m.body.includes('PA-BPT-TEST-01') && dl.length === 1 && dl[0].status === 'held_in_test_sink'
        && sink.length === 1 && sink[0].to_role === 'buyer' && !JSON.stringify(sink).includes('@') && web.status === 200 && wt === m.body ? 'PASS' : 'FAIL',
        { prepared: !!m, sha256: m && m.sha256, chars: m && m.body.length, deliveries: dl, sink_rows: sink.length, buyer_link_http: web.status, identical: m ? wt === m.body : false });
    }
    if (paid) {
      const pi = (await stripe('GET', `/v1/payment_intents/${paid.payment_intent}?expand[]=latest_charge.balance_transaction`, null, ACCOUNT)).j;
      let ch = pi.latest_charge;   // the fee and balance transaction are created asynchronously: wait for them
      for (let i = 0; i < 20 && ch && (!ch.application_fee || !ch.balance_transaction); i++) { await sleep(1500); ch = (await stripe('GET', `/v1/charges/${ch.id}?expand[]=balance_transaction`, null, ACCOUNT)).j; }
      const led = await q('SELECT kind, amount_cents FROM order_ledger WHERE order_id = ? ORDER BY kind', o1.id);
      rec('E4', 'Stripe’s charge matches the pilot ledger: €1,075 charged, €150 application fee, delivery outside commission', SRC,
        ch.amount === 107500 && ch.application_fee_amount === 15000 && led.find(l => l.kind === 'commission').amount_cents === 15000 && led.find(l => l.kind === 'delivery_allocation').amount_cents === 7500 ? 'PASS' : 'FAIL',
        { charge: ch.id, amount: ch.amount, application_fee_amount: ch.application_fee_amount, stripe_fee: ch.balance_transaction && ch.balance_transaction.fee, ledger: led });
      // MODEL B · the actual processing fee + its VAT, reimbursed once from the application fee
      const P1 = await reimbursedFor(o1.id), bt1 = ch.balance_transaction;
      const frs1 = await feeRefundsOf(ch.application_fee);
      rec('E13', 'model B: after payment the pilot reads Stripe’s ACTUAL processing fee and VAT on it for the whole €1,075 and reimburses exactly that by a partial application-fee refund', SRC,
        P1 && P1.status === 'reimbursed' && P1.stripe_fee === sumType(bt1, 'stripe_fee') && P1.vat === sumType(bt1, 'tax') && frs1.length === 1 && frs1[0].amount === P1.cost ? 'PASS' : 'FAIL',
        { stripe_fee_details: bt1 && bt1.fee_details, pilot: P1, fee_refunds: frs1.map(f => ({ id: f.id, amount: f.amount, kind: f.metadata && f.metadata.plotart_kind })) });
      await call('POST', `/api/admin/checkout/orders/${o1.id}/processing`, FOUNDER, {}); await CW.scheduled({ cron: '*/15 * * * *' }).catch(() => {});
      const frs1b = await feeRefundsOf(ch.application_fee);
      rec('E13b', 'model B: reconciling again (founder button and sweep) creates no second reimbursement on Stripe', SRC, frs1b.length === frs1.length ? 'PASS' : 'FAIL', { before: frs1.length, after: frs1b.length });
      // 2 · partial refund through the pilot, confirmed by Stripe's events
      const r = await call('POST', `/api/admin/checkout/orders/${o1.id}/refund`, FOUNDER, { artwork_cents: 10000, delivery_cents: 0, reason: 'E2E partial refund test' });
      const rr = await waitFor(async () => { const x = await db.prepare("SELECT * FROM order_refunds WHERE order_id = ?").bind(o1.id).first(); return x && x.status !== 'pending' ? x : null; }, 120_000);
      const feeObj = (await stripe('GET', `/v1/application_fees/${ch.application_fee}`)).j;
      rec('E5', 'partial refund €100 of the artwork: completed (directly or via webhook/sweep) and €15 commission returned', SRC,
        rr && rr.status === 'succeeded' && P1 && feeObj.amount_refunded === 1500 + P1.cost ? 'PASS' : (rr ? 'FAIL' : 'INFO'), { http: r.s, refund_status: rr ? rr.status : 'still pending after 120s', fee_amount_refunded: feeObj.amount_refunded, of_which_processing: P1 && P1.cost, flag: (await order(o1.id)).needs_resolution });
      const st1 = (await call('GET', `/api/checkout/orders/${o1.id}`, GAL)).j.statement;
      rec('E13c', 'model B statement (real amounts): gross, delivery, commission, processing fee, VAT, reimbursement, refund and net shown separately', SRC,
        st1 && P1 && st1.gross_payment === 107500 && st1.of_which_delivery === 7500 && st1.plotart_commission === 15000 && st1.commission_refunded === 1500 && st1.stripe_processing_fee === P1.stripe_fee
        && st1.vat_on_processing_fee === P1.vat && st1.processing_reimbursed_by_plotart === P1.cost && st1.refunded_to_buyer === 10000 && st1.net_proceeds === 107500 - 15000 + 1500 - 10000 ? 'PASS' : 'FAIL', st1);
    }
    // 3 · abandonment: expiry delivered as a real event releases the work
    const o2 = await quote('wagal2', 'PA-E-261116-E2E002', 50000, 0);
    const sess = (await q("SELECT id FROM checkout_sessions WHERE order_id = ? AND status = 'open'", o2.id))[0];
    if (sess) await stripe('POST', `/v1/checkout/sessions/${sess.id}/expire`, {}, ACCOUNT);
    const released = await waitFor(async () => (await order(o2.id)).status === 'quoted' && !(await q("SELECT 1 FROM artwork_reservations WHERE artwork_id='wagal2'")).length);
    rec('E6', 'a REAL checkout.session.expired event releases the reservation and returns the quote to payable', SRC, released ? 'PASS' : 'FAIL', { status: (await order(o2.id)).status });
    // 4 · dispute delivered as a real event
    const o3 = await quote('wagal3', 'PA-E-261116-E2E003', 5000, 0);
    let dispPaid = false;
    try { const r = await payInBrowser(o3.url, '4000000000000259', 'dispute'); dispPaid = true; rec('E7a', 'buyer pays with the dispute test card on the real hosted Checkout page and returns with result=success', SRC, 'PASS', { final_url: r.diag.finalUrl, return_page: r.diag.returnPage }); }
    catch (e) { rec('E7a', 'buyer pays with the dispute test card on the real hosted Checkout page', SRC, 'FAIL', { error: String(e.message).split('\n')[0].slice(0, 300), final_url: e.diag && e.diag.finalUrl, steps: e.diag && e.diag.steps, page_errors: e.diag && e.diag.pageErrors }); }
    const disputed = dispPaid ? await waitFor(async () => (await order(o3.id)).dispute_status === 'open', 150_000) : null;
    rec('E7', 'a REAL charge.dispute.created (arriving after or before the payment event) marks the order disputed', SRC, disputed ? 'PASS' : dispPaid ? 'FAIL' : 'SKIP',
      { ...(dispPaid ? {} : { blocked_by: 'E7a — no payment was made, so no dispute could open; webhook handling NOT exercised' }), status: (await order(o3.id)).status, dispute_status: (await order(o3.id)).dispute_status, events: await q("SELECT type, status FROM payment_events WHERE object_id LIKE 'dp_%' OR order_id = ?", o3.id) });
    { // E7c · the dispute event was applied to the order whose payment Stripe says was disputed
      const o = await order(o3.id);
      const dEv = await q("SELECT event_id, object_id FROM payment_events WHERE type = 'charge.dispute.created' AND status = 'processed' AND order_id = ?", o3.id);
      const dsp = dEv[0] && (await stripe('GET', `/v1/disputes/${dEv[0].object_id}`, null, ACCOUNT)).j;
      const others = await q("SELECT order_id FROM payment_events WHERE type = 'charge.dispute.created' AND (order_id IS NULL OR order_id <> ?)", o3.id);
      rec('E7c', 'the dispute event was applied to the order whose PaymentIntent Stripe disputed, and to no other order', SRC,
        dEv.length === 1 && dsp && dsp.payment_intent === o.payment_intent && !others.length ? 'PASS' : dispPaid ? 'FAIL' : 'SKIP',
        { events: dEv.map(e => e.event_id), payment_intent_matches: !!dsp && dsp.payment_intent === o.payment_intent, dispute_amount: dsp && dsp.amount, dispute_reason: dsp && dsp.reason, other_orders: others });
    }
    // 5 · dispute CLOSED through the pilot by genuine signed charge.dispute.closed events: won (o3) and lost (o4)
    const closeDispute = async (o, evidence) => {
      const d = (await stripe('GET', `/v1/disputes?payment_intent=${encodeURIComponent(o.payment_intent)}&limit=1`, null, ACCOUNT)).j.data[0];
      if (!d) return null;
      await stripe('POST', `/v1/disputes/${d.id}`, { evidence: { uncategorized_text: evidence }, submit: 'true' }, ACCOUNT);
      return d.id;
    };
    if (disputed) {
      const dId = await closeDispute(await order(o3.id), 'winning_evidence');
      const won = await waitFor(async () => (await order(o3.id)).dispute_status === 'won', 240_000);
      const O = await order(o3.id), L = await q("SELECT kind, amount_cents FROM order_ledger WHERE order_id = ? AND kind IN ('dispute','dispute_reinstated')", o3.id);
      const ev = await q("SELECT event_id FROM payment_events WHERE type = 'charge.dispute.closed' AND status = 'processed' AND order_id = ? AND object_id = ?", o3.id, dId);
      rec('E10', 'a REAL signed charge.dispute.closed (won) returns the order to paid and reinstates the disputed amount in the ledger', SRC,
        won && O.status === 'paid' && L.some(l => l.kind === 'dispute_reinstated' && l.amount_cents === 5000) && ev.length === 1 ? 'PASS' : 'FAIL',
        { dispute: dId, status: O.status, dispute_status: O.dispute_status, ledger: L, closed_events: ev.map(e => e.event_id), flag: O.needs_resolution });
    } else rec('E10', 'dispute closed as won through the pilot', SRC, 'SKIP', { blocked_by: 'E7 — no open dispute' });
    if (disputed) {   // MODEL B · disputes are NOT absorbed: only the processing fee was reimbursed; Stripe's dispute fee stays with the seller
      const O3 = await order(o3.id), P3 = await reimbursedFor(o3.id);
      const c3 = (await stripe('GET', `/v1/payment_intents/${O3.payment_intent}?expand[]=latest_charge`, null, ACCOUNT)).j.latest_charge;
      const frs3 = c3 && c3.application_fee ? await feeRefundsOf(c3.application_fee) : [];
      const d3 = (await stripe('GET', `/v1/disputes?payment_intent=${encodeURIComponent(O3.payment_intent)}&limit=1&expand[]=data.balance_transactions`, null, ACCOUNT)).j.data[0];
      const dfee = d3 ? d3.balance_transactions.reduce((a, b) => a + b.fee, 0) : null;
      const st3 = (await call('GET', `/api/checkout/orders/${o3.id}`, GAL)).j.statement;
      rec('E14', 'model B with a dispute: the only reimbursement is the processing fee + VAT; Stripe’s ACTUAL dispute fees (and any it returned) are in the ledger and statement, not reimbursed', SRC,
        P3 && P3.status === 'reimbursed' && frs3.length === 1 && frs3[0].amount === P3.cost && st3 && dfee !== null
        && st3.dispute_fees_charged_by_stripe - st3.dispute_fees_returned_by_stripe === dfee && st3.dispute_fees_status === 'recorded from Stripe' ? 'PASS' : 'FAIL',
        { processing: P3 && { stripe_fee: P3.stripe_fee, vat: P3.vat, cost: P3.cost }, fee_refunds: frs3.map(f => f.amount), dispute_fees_charged_by_stripe_cents: dfee, statement: st3 });
    }
    const o4 = await quote('wagal4', 'PA-E-261116-E2E004', 5000, 0);
    let lostPaid = false;
    try { await payInBrowser(o4.url, '4000000000000259', 'dispute-lost'); lostPaid = true; } catch (e) { rec('E11a', 'buyer pays with the dispute test card (lost case)', SRC, 'FAIL', { error: String(e.message).split('\n')[0].slice(0, 300) }); }
    const opened4 = lostPaid ? await waitFor(async () => (await order(o4.id)).dispute_status === 'open', 150_000) : null;
    if (opened4) {
      const dId = await closeDispute(await order(o4.id), 'losing_evidence');
      const lost = await waitFor(async () => (await order(o4.id)).dispute_status === 'lost', 240_000);
      const O = await order(o4.id);
      const ev = await q("SELECT event_id FROM payment_events WHERE type = 'charge.dispute.closed' AND status = 'processed' AND order_id = ? AND object_id = ?", o4.id, dId);
      rec('E11', 'a REAL signed charge.dispute.closed (lost) marks the order refunded and flags PlotArt’s commission for return (GAA 9)', SRC,
        lost && O.status === 'refunded' && /dispute lost/.test(O.needs_resolution || '') && ev.length === 1 ? 'PASS' : 'FAIL',
        { dispute: dId, status: O.status, dispute_status: O.dispute_status, closed_events: ev.map(e => e.event_id), flag: O.needs_resolution });
      // E16 · the commission to return after the lost dispute: queued with the PA-GAA 9.1 deadline, then returned through REAL Stripe
      await reimbursedFor(o4.id);
      const LW = await db.prepare("SELECT * FROM checkout_owed WHERE order_id = ? AND kind = 'lost_dispute_commission'").bind(o4.id).first();
      const O4 = await order(o4.id), P4 = JSON.parse(O4.processing || '{}');
      const c4 = (await stripe('GET', `/v1/payment_intents/${O4.payment_intent}?expand[]=latest_charge`, null, ACCOUNT)).j.latest_charge;
      const ret = await call('POST', `/api/admin/checkout/orders/${o4.id}/refund`, FOUNDER, { commission_only: true, reason: 'E2E: dispute lost, commission returned under PA-GAA 9.1' });
      const f4 = (await stripe('GET', `/v1/application_fees/${c4.application_fee}`)).j, LW2 = LW && await db.prepare('SELECT * FROM checkout_owed WHERE id = ?').bind(LW.id).first();
      const SH4 = await db.prepare("SELECT * FROM checkout_owed WHERE order_id = ? AND kind = 'commission_shortfall'").bind(o4.id).first(), st4 = (await call('GET', `/api/checkout/orders/${o4.id}`, GAL)).j.statement;
      rec('E16', 'lost dispute: the €7.50 commission is queued (due 30 days, PA-GAA 9.1) and returned — what is left of the fee through REAL Stripe, the processing already reimbursed as a direct-payment item; dispute fees recorded', SRC,
        LW && LW.cents === 750 && !LW.due_provisional && ret.s === 200 && LW2.settled_cents === 750 && f4.amount_refunded === 750 && SH4 && SH4.cents === P4.cost && st4.dispute_fees_status === 'recorded from Stripe' ? 'PASS' : 'FAIL',
        { owed: LW && { cents: LW.cents, due_rule: LW.due_rule }, return_http: ret.s, fee_amount_refunded: f4.amount_refunded, processing_reimbursed: P4.cost, direct_payment_item: SH4 && SH4.cents, settled: LW2 && LW2.settled_cents,
          statement: st4 && { dispute_fees_charged: st4.dispute_fees_charged_by_stripe, returned: st4.dispute_fees_returned_by_stripe, net: st4.net_proceeds, owed: st4.owed_by_plotart_not_yet_paid } });
    } else rec('E11', 'dispute closed as lost through the pilot', SRC, lostPaid ? 'FAIL' : 'SKIP', lostPaid ? { reason: 'the dispute never opened on the order' } : { blocked_by: 'E11a' });

    // 6 · a refund that SUCCEEDS and later FAILS (Stripe test card 4000 0000 0000 5126), reconciled from REAL signed events
    const o5 = await quote('wagal5', 'PA-E-261116-E2E005', 40000, 2000);
    let rfPaid = false;
    try { await payInBrowser(o5.url, '4000000000005126', 'refund-fail'); rfPaid = true; } catch (e) { rec('E12a', 'buyer pays with the refund-fails test card', SRC, 'FAIL', { error: String(e.message).split('\n')[0].slice(0, 300) }); }
    const paid5 = rfPaid ? await waitFor(async () => { const o = await order(o5.id); return o.payment_status === 'paid' ? o : null; }) : null;
    if (paid5) {
      await reimbursedFor(o5.id);   // model B: the processing reimbursement happens first, as it would in practice
      const r = await call('POST', `/api/admin/checkout/orders/${o5.id}/refund`, FOUNDER, { artwork_cents: 40000, delivery_cents: 2000, reason: 'E2E refund that Stripe later fails' });
      const rr = await db.prepare('SELECT * FROM order_refunds WHERE order_id = ?').bind(o5.id).first();
      let ch = (await stripe('GET', `/v1/payment_intents/${paid5.payment_intent}?expand[]=latest_charge`, null, ACCOUNT)).j.latest_charge;
      for (let i = 0; i < 20 && ch && !ch.application_fee; i++) { await sleep(1500); ch = (await stripe('GET', `/v1/charges/${ch.id}`, null, ACCOUNT)).j; }
      const fee1 = (await stripe('GET', `/v1/application_fees/${ch.application_fee}`)).j;
      const P5 = JSON.parse((await order(o5.id)).processing || '{}'); P5.shortfall_cents = (await db.prepare('SELECT COALESCE(SUM(cents), 0) AS c FROM checkout_owed WHERE order_id = ?').bind(o5.id).first()).c;
      rec('E12a', 'the full refund first SUCCEEDS on Stripe; the €60 commission is settled once: (€60 − processing already reimbursed) back through Stripe, the processing amount flagged as a shortfall PlotArt pays directly', SRC,
        r.s === 200 && rr && rr.status === 'succeeded' && fee1.amount_refunded === 6000 && (await order(o5.id)).status === 'refunded' && P5.cost > 0 && P5.shortfall_cents === P5.cost
        && /PlotArt owes the artist/.test((await order(o5.id)).needs_resolution || '') ? 'PASS' : 'FAIL',
        { http: r.s, refund_status: rr && rr.status, fee_amount_refunded: fee1.amount_refunded, processing: P5.cost, shortfall: P5.shortfall_cents, order_status: (await order(o5.id)).status, flag: (await order(o5.id)).needs_resolution });
      const reversed = await waitFor(async () => (await db.prepare('SELECT status FROM order_refunds WHERE id = ?').bind(rr.id).first()).status === 'failed', 300_000);
      const O = await order(o5.id), re = (await stripe('GET', `/v1/refunds/${rr.provider_refund_id}`, null, ACCOUNT)).j;
      const L = await q("SELECT kind, amount_cents FROM order_ledger WHERE order_id = ? AND kind LIKE '%refund%' ORDER BY kind", o5.id);
      const evs = await q("SELECT type, status FROM payment_events WHERE order_id = ? AND type IN ('refund.updated','refund.failed','charge.refund.updated')", o5.id);
      rec('E12b', 'Stripe later FAILS it and a REAL signed refund event reconciles the order: back to paid, reversal lines booked, buyer flagged as NOT repaid', SRC,
        reversed && re.status === 'failed' && O.status === 'paid' && L.some(l => l.kind === 'artwork_refund_reversed' && l.amount_cents === 40000) && /SUCCEEDED and then FAILED/.test(O.needs_resolution || '') ? 'PASS' : 'FAIL',
        { stripe_refund_status: re.status, failure_reason: re.failure_reason, order_status: O.status, payment_status: O.payment_status, ledger: L, events: evs, flag: O.needs_resolution });
      if (reversed) {   // E18 · the buyer's notice for a REAL reversed refund: kept once, test sink only, shown on the quote page
        const bm = await q("SELECT id, body FROM order_messages WHERE order_id = ? AND kind = 'buyer_refund_reversed'", o5.id);
        const bd = bm[0] ? await q('SELECT channel, status, detail FROM order_message_deliveries WHERE message_id = ?', bm[0].id) : [];
        const qp = await (await CW.fetch(`http://checkout.local/q/${o5.tok}`)).text();
        rec('E18', 'after the REAL refund reversal the buyer gets one notice that they have NOT been repaid: kept, held in the test sink (not emailed), shown on their quote page', SRC,
          bm.length === 1 && /NOT been repaid/.test(bm[0].body) && bd.length === 1 && bd[0].status === 'held_in_test_sink' && qp.includes('was reversed') ? 'PASS' : 'FAIL',
          { notices: bm.length, deliveries: bd, shown_on_quote_page: qp.includes('was reversed') });
        const before = (await stripe('GET', `/v1/refunds?payment_intent=${paid5.payment_intent}&limit=10`, null, ACCOUNT)).j.data.length;
        const rep = await call('POST', `/api/admin/checkout/orders/${o5.id}/repaid`, FOUNDER, { artwork_cents: 40000, delivery_cents: 2000, evidence: 'E2E: artist repaid the buyer by bank transfer BT-E2E-1, buyer confirmed' });
        const again = await call('POST', `/api/admin/checkout/orders/${o5.id}/refund`, FOUNDER, { artwork_cents: 40000, delivery_cents: 2000, reason: 'E2E duplicate repayment attempt' });
        const after = (await stripe('GET', `/v1/refunds?payment_intent=${paid5.payment_intent}&limit=10`, null, ACCOUNT)).j.data.length;
        const fee2 = (await stripe('GET', `/v1/application_fees/${ch.application_fee}`)).j;
        rec('E12c', 'the artist’s direct repayment is recorded once with NO second commission refund; a further Stripe refund is refused and none is created', SRC,
          rep.s === 200 && again.s === 409 && after === before && fee2.amount_refunded === 6000 && (await order(o5.id)).status === 'refunded' ? 'PASS' : 'FAIL',
          { repaid_http: rep.s, second_refund_http: again.s, stripe_refunds_before: before, stripe_refunds_after: after, fee_amount_refunded: fee2.amount_refunded });
        const P5b = JSON.parse((await order(o5.id)).processing || '{}'); P5b.shortfall_cents = (await db.prepare('SELECT COALESCE(SUM(cents - settled_cents), 0) AS c FROM checkout_owed WHERE order_id = ?').bind(o5.id).first()).c;
        const sp = await call('POST', `/api/admin/checkout/orders/${o5.id}/shortfallpaid`, FOUNDER, { amount_cents: P5b.shortfall_cents, reference: 'E2E bank transfer BT-SF-E2E on 17 Nov' });
        const sp2 = await call('POST', `/api/admin/checkout/orders/${o5.id}/shortfallpaid`, FOUNDER, { amount_cents: 1, reference: 'E2E second attempt BT-SF-E2E-2' });
        const fee3 = (await stripe('GET', `/v1/application_fees/${ch.application_fee}`)).j, st5 = (await call('GET', `/api/checkout/orders/${o5.id}`, GAL)).j.statement;
        rec('E12d', 'model B after the reversal: the shortfall is still owed once (not doubled); PlotArt records paying it directly; a second record is refused; nothing more moves on Stripe', SRC,
          P5b.shortfall_cents === P5.cost && sp.s === 200 && sp2.s === 409 && fee3.amount_refunded === 6000 && st5.shortfall_still_owed_by_plotart === 0 && st5.shortfall_paid_by_plotart === P5.cost ? 'PASS' : 'FAIL',
          { shortfall: P5b.shortfall_cents, record_http: sp.s, second_http: sp2.s, fee_amount_refunded: fee3.amount_refunded, statement: st5 });
      } else rec('E12c', 'no double repayment after the reversal', SRC, 'SKIP', { blocked_by: 'E12b' });
    } else rec('E12b', 'refund reversal reconciliation', SRC, 'SKIP', { blocked_by: 'E12a — payment not completed' });

    // E17d · every Stripe call the public Worker made, by key: proves no fallback to the runner key
    { const st = CW_CALLS.filter(c => c.host === 'api.stripe.com');
      const byKey = st.reduce((a, c) => (a[c.key] = (a[c.key] || 0) + 1, a), {});
      const endpoints = Object.values(st.reduce((a, c) => { const k = `${c.method} ${c.path}${c.connected ? ' [connected]' : ' [platform]'}`; (a[k] = a[k] || { endpoint: k, calls: 0, statuses: {} }).calls++; a[k].statuses[c.status] = (a[k].statuses[c.status] || 0) + 1; return a; }, {}));
      const permissionErrors = st.filter(c => c.status === 401 || c.status === 403).map(c => ({ endpoint: `${c.method} ${c.path}`, connected: c.connected, status: c.status, stripe_error: c.stripe_error }));
      rec('E17d', 'every Stripe API call made by the public checkout Worker used the runtime key (no fallback to the runner key); endpoints and statuses listed; permission errors shown with Stripe’s message', 'stripe-test-api+pilot',
        !runtimeOk ? 'SKIP' : st.length > 0 && st.every(c => c.key === 'runtime') && !permissionErrors.length ? 'PASS' : 'FAIL', { calls: st.length, by_key: byKey, endpoints, permission_errors: permissionErrors }); }
    // E8 only counts if the events this run depends on actually arrived and were processed
    const all = await q('SELECT type, status FROM payment_events');
    const bad = all.filter(e => e.status === 'failed');
    const expected = ['checkout.session.completed', 'checkout.session.expired', 'charge.dispute.created', 'charge.dispute.closed'];
    const missing = expected.filter(t => !all.some(e => e.type === t && e.status === 'processed'));
    rec('E8', 'every expected real signed event (payment completed, session expired, dispute created, dispute closed) arrived and processed, and none failed', SRC,
      bad.length ? 'FAIL' : missing.length ? 'SKIP' : 'PASS', { failed: bad, missing_expected: missing, received: all.map(e => `${e.type}:${e.status}`), ...(missing.length && !bad.length ? { note: 'not a success: expected events never arrived' } : {}) });
  } catch (e) { rec('E9', 'end-to-end run', SRC, 'FAIL', { error: String(e.stack || e.message).slice(0, 500) }); }
  finally { if (browser) await browser.close(); await S.mf.dispose(); }
}
