// SANDBOX END-TO-END · multi-artist basket (src/basket.js) against the REAL Stripe TEST API. Called by
// stripe-testmode-checks.mjs (phase "basket_e2e") on the protected checkout-test runner. TEST MODE ONLY.
// The basket's own Workers run in Miniflare (local D1, current schema + proposed migration 0019) with the isolated POC
// TEST key (CHECKOUT_TEST_STRIPE_POC_KEY), the two existing TEST artist accounts, and the buyer entering a Stripe test card
// on Stripe's real hosted page (headless Chromium). The coordinator is driven by the buyer's return and the sweep (signed
// webhooks are proven locally in prove-basket.mjs). Every object is tagged with the run and cleaned up, then every payment
// tagged with the run on both accounts is re-read to verify it is refunded or cancelled. hCaptcha is never bypassed: if the
// hosted page asks for a challenge, browser steps stop and the result says so.
import { readFileSync, mkdirSync } from 'node:fs';
import { createRequire } from 'node:module';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { statements } from './sql.mjs';

const HERE = new URL('..', import.meta.url).pathname;
const SRC = 'stripe-test-api+basket';
const CARDS = { ok: '4242424242424242', declineAfterAttach: '4000000000000341', alwaysAuth: '4000002760003184' };

/* offline: a test harness may pass { apiBase, fetchImpl, outbound, origin } to run this exact phase against a mock Stripe; the
   defaults are the real Stripe TEST API, as on the protected runner. */
export async function basketE2E({ rec, KEY, accounts, runId, playwrightFrom, v1, port = 8893, offline = null }) {
  const ok = (id, name, pass, d = {}) => rec(id, name, SRC, pass ? 'PASS' : 'FAIL', d);
  const info = (id, name, d = {}) => rec(id, name, SRC, 'INFO', d);
  if (!/^(sk|rk)_test_[A-Za-z0-9]+$/.test(KEY) || accounts.length !== 2 || !accounts.every(a => /^acct_[A-Za-z0-9]+$/.test(a))) { rec('BE0', 'TEST key and two TEST artist accounts', 'local', 'FAIL'); return; }
  const built = readFileSync(HERE + 'src/payment-terms.js', 'utf8');
  if (!built.includes('PA-PAY-TEST-01')) { rec('BE0', 'the Workers were built with the TEST ONLY texts (CHECKOUT_TARGET=test)', 'local', 'FAIL'); return; }
  const tag = 'basket-' + runId, ORIGIN = 'https://plotart-basket-test.invalid';
  const api = async (method, path, body = null, account = null) => {
    const h = { Authorization: 'Bearer ' + KEY, 'Stripe-Version': v1 }; if (account) h['Stripe-Account'] = account; if (body) h['Content-Type'] = 'application/x-www-form-urlencoded';
    const r = await (offline ? offline.fetchImpl : fetch)((offline ? offline.apiBase : 'https://api.stripe.com') + path, { method, headers: h, body: body ? new URLSearchParams(body) : undefined });
    const j = await r.json(); if (j.livemode === true) throw new Error('live object returned: stopping');
    return { ok: r.ok, status: r.status, j, err: j.error ? { type: j.error.type, code: j.error.code ?? null, message: String(j.error.message || '').slice(0, 240) } : null };
  };
  const ENVV = { CHECKOUT_PILOT_ENABLED: 'true', BASKET_ENABLED: 'true', BASKET_COMMISSION_FREE: 'with_processing_consent', STRIPE_SECRET_KEY: KEY, STRIPE_WEBHOOK_SECRET: 'whsec_unused_in_this_phase',
    CHECKOUT_ORIGIN: ORIGIN, GALLERY_ORIGIN: 'https://plotnua.ie', CHECKOUT_MESSAGE_RETRY_MINUTES: '0', ...(offline ? { STRIPE_API_BASE: offline.apiBase } : {}) };
  const S = await start({ port, env: ENVV, checkout: { env: ENVV }, ...(offline ? { outbound: offline.outbound } : {}) });
  const { db } = S, CW = S.checkoutWorker;
  const created = { baskets: [] };
  let browser = null;
  try {
    for (const s of statements(readFileSync(HERE + 'migrations/0019_multi_artist_basket.sql', 'utf8'))) await db.prepare(s).run();
    const ago = d => new Date(Date.now() - d * 86400_000).toISOString();
    const call = async (method, path, email, body) => { const r = await S.mf.dispatchFetch(S.url + path, { method, headers: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
      const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* */ } return { s: r.status, j }; };
    const pub = async (method, path, json = null) => { const r = await CW.fetch(ORIGIN + path, { method, redirect: 'manual', headers: json ? { 'Content-Type': 'application/json', Origin: ORIGIN } : {}, body: json ? JSON.stringify(json) : undefined });
      const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* */ } return { s: r.status, t, j, loc: r.headers.get('Location') }; };
    const one = (sql, ...b) => db.prepare(sql).bind(...b).first();
    const q = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results;

    // ---- synthetic artists on the two existing TEST accounts: a Gallery Artist (15%) and a Founding Artist (0%)
    const GAL = 'gal@example.test', FND = 'fnd@example.test';
    await seedPublished(db, { id: 'agal', slug: 'gale', email: GAL, name: 'Gale Gallery (TEST)', works: 4, publishedAt: ago(30) });
    await seedPublished(db, { id: 'afnd', slug: 'fia', email: FND, name: 'Fia Founding (TEST)', works: 4, number: 3, publishedAt: ago(100) });
    await db.prepare("UPDATE artists SET founding = 0 WHERE id = 'agal'").run();
    const FAKE = 'a'.repeat(64);
    await db.prepare("INSERT INTO gallery_agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at) VALUES ('PA-GAA-2026-11','gallery_artist_agreement','t','fixed',?,?,'2018-01-01T00:00:00Z',?)").bind(FAKE, FAKE, ago(0)).run();
    await db.prepare(`INSERT INTO gallery_agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, method, statement, created_at) VALUES ('gaa1','ev1','agal','PA-GAA-2026-11',?,?,?,?, 'x','studio_checkbox','test',?)`).bind(FAKE, FAKE, ago(20), GAL, ago(20)).run();
    await db.prepare("INSERT INTO artist_terms (artist_id, track, commission_bp, set_by, created_at, updated_at) VALUES ('agal','gallery_artist',1500,?,?,?)").bind(FOUNDER, ago(20), ago(20)).run();
    await db.prepare("UPDATE artworks SET price_eur = 120 WHERE artist_id = 'agal'").run(); await db.prepare("UPDATE artworks SET price_eur = 80 WHERE artist_id = 'afnd'").run();
    for (const a of ['agal', 'afnd']) { const v = await one('SELECT snapshot FROM versions WHERE artist_id = ?', a); const snap = JSON.parse(v.snapshot); for (const w of snap.works) w.price_eur = a === 'agal' ? 120 : 80; await db.prepare('UPDATE versions SET snapshot = ? WHERE artist_id = ?').bind(JSON.stringify(snap), a).run(); }
    const terms = JSON.parse(readFileSync(HERE + 'agreements/payment-test/fingerprints.json', 'utf8')).documents;
    for (const [id, t] of Object.entries(terms)) await db.prepare('INSERT INTO payment_terms (doc_id, kind, title, html_sha256, effective_at, created_at) VALUES (?,?,?,?,?,?)').bind(id, t.kind, t.title, t.html_sha256, '2018-01-01T00:00:00Z', ago(0)).run();
    const { basketDoc } = await import(HERE + 'src/basket-terms.js');
    for (const id of ['PA-BBT-TEST-01', 'PA-BAA-TEST-01']) { const d = await basketDoc(id, false); await db.prepare('INSERT INTO basket_terms (doc_id, kind, title, html_sha256, effective_at, created_at) VALUES (?,?,?,?,?,?)').bind(id, d.kind, d.title, d.html_sha256, '2018-01-01T00:00:00Z', ago(0)).run(); }
    const ADD = Object.entries(terms).find(([, t]) => t.kind === 'artist_payment_addendum');
    const SELLER = n => ({ legal_name: n, address: '1 Studio Lane, Dublin 8, Ireland', email: 'seller@example.test', phone: '+353 1 555 0100', trader_status: 'trader', confirm: true });
    const DELIVERY = { collection_county: 'Dublin', unpacked_cm: '40 × 50 × 3', packed_cm: '55 × 65 × 10', weight_kg: 4, medium: 'Oil on board', framing: 'Unframed', glazing: 'None', condition: 'Excellent', access_notes: null,
      organiser: 'artist', packer: 'artist', transport_booker: 'artist', transport_contracting_party: 'artist', transport_payer: 'artist', transporter_name: 'Synthetic Art Couriers (TEST)', installation: 'not_applicable', import_costs: 'not_applicable',
      cover_type: 'transit_insurance', cover_provider: 'Synthetic Underwriting (SIMULATED)', covered_value_cents: 20000, insured_party: 'transporter', cover_confirmation_ref: 'SIM-COVER-T', cover_confirmed_by: 'Synthetic', cover_confirmed_on: '2026-11-21',
      valuation_basis: 'Sale price', excess_cents: 0, exclusions: null, cover_period: 'Collection to signed delivery', claims_contact: 'claims@example.test', delivery_window: '5–8 working days', tracking: 'Tracked', signed_receipt: true, condition_photos: true,
      return_method: 'Same courier', return_address: '1 Studio Lane, Dublin 8', return_cost_cents: 2000, return_cost_basis: 'estimated_maximum', return_arranged_by: 'buyer', shipment_confirmation_ref: 'SAC-T', shipment_confirmed_by: 'Synthetic', shipment_confirmed_on: '2026-11-21' };
    for (const [aid, e, n, acct] of [['agal', GAL, 'Gale Gallery', accounts[0]], ['afnd', FND, 'Fia Founding', accounts[1]]]) {
      await call('POST', '/api/checkout/opt-in', e, { accept: true, doc_id: ADD[0], html_sha256: ADD[1].html_sha256 });
      const a = await api('GET', '/v1/accounts/' + acct);
      ok(`BE-ACC-${aid}`, `existing TEST artist account for ${n} can take card payments (read from Stripe)`, a.ok && a.j.charges_enabled === true && a.j.capabilities?.card_payments === 'active', a.ok ? { country: a.j.country, charges_enabled: a.j.charges_enabled } : a.err);
      await db.prepare(`INSERT INTO payment_accounts (artist_id, account_id, country, livemode, charges_enabled, payouts_enabled, details_submitted, checked_at, created_at, updated_at) VALUES (?,?,?,0,?,?,?,?,?,?)`)
        .bind(aid, acct, a.j.country === 'GB' ? 'GB' : 'IE', a.j.charges_enabled ? 1 : 0, a.j.payouts_enabled ? 1 : 0, a.j.details_submitted ? 1 : 0, new Date().toISOString(), new Date().toISOString(), new Date().toISOString()).run();
      await call('PUT', '/api/checkout/seller-profile', e, SELLER(n));
      const bd = await basketDoc('PA-BAA-TEST-01', false);
      await call('POST', '/api/checkout/basket/opt-in', e, { accept: true, doc_id: bd.doc_id, html_sha256: bd.html_sha256 });
      for (let i = 1; i <= 4; i++) await call('PUT', `/api/checkout/basket/offers/w${aid}${i}`, e, { confirm: true, delivery_cents: 1000, delivery: DELIVERY });
    }
    const PST = (await call('GET', '/api/checkout', FND)).j.processing_statement;
    await call('POST', '/api/checkout/processing-consent', FND, { accept: true, statement: PST });
    const el = await call('GET', '/api/admin/checkout/baskets/eligibility?ids=wagal1,wafnd1', FOUNDER);
    ok('BE-1', 'both works can be bought online: 15% for the Gallery Artist, 0% Founding 25 entitlement for the Founding Artist', el.j && el.j.items.every(i => i.ok) && el.j.items[0].commission_basis === 'gallery_artist_agreement' && el.j.items[1].commission_basis === 'founding_enquiry', el.j);

    // ---- the hosted card page in a real browser (no bypass of anything Stripe shows)
    const { chromium } = createRequire(playwrightFrom)('playwright');
    browser = await chromium.launch();
    let captchaBlocked = false;
    /* The hosted card page, as in the proven POC routine (commit 9101fb3f, run 44930999959): the same field order and selectors,
       Link handled the same way (the phone is filled; Link is unticked only if Stripe rejects the phone), a pre-submit check,
       Stripe's own messages told apart from third-party frames (hCaptcha), messages after submit detected, and a full failure
       report with a screenshot. Completion is taken from Stripe (the Checkout Session's status, polled), not from the browser
       redirect alone. A visible hCaptcha challenge stops the browser steps: nothing is bypassed. */
    async function enterCard(url, card, label, sessionId) {
      if (captchaBlocked) return { stage: 'not attempted', error: 'hosted page asked for hCaptcha earlier in this run' };
      const page = await browser.newPage({ locale: 'en-IE' });
      const scrubText = s => String(s || '').replace(/(?:[rs]k|pk)_(?:test|live)_\S+|cs_(?:test|live)_\S+|seti_\S+|pm_\S+/g, '[redacted]').replace(/\s+/g, ' ').trim().slice(0, 200);
      const diag = { console_errors: [], page_errors: [], failed_requests: [] };
      page.on('console', m => { if (m.type() === 'error' && diag.console_errors.length < 10) diag.console_errors.push(scrubText(m.text())); });
      page.on('pageerror', err => { if (diag.page_errors.length < 10) diag.page_errors.push(scrubText(err.message)); });
      page.on('requestfailed', r => { if (diag.failed_requests.length < 10) { try { const u = new URL(r.url()); if (u.origin !== ORIGIN) diag.failed_requests.push(u.host + u.pathname.slice(0, 60) + ' ' + (r.failure()?.errorText || '')); } catch {} } });
      // the return address is this local test's own (not a real host): answer it in the browser so the redirect completes
      await page.route(ORIGIN + '/**', r => r.fulfill({ status: 200, contentType: 'text/html', body: '<p>returned</p>' }));
      const field = async (css, timeout = 10000) => { const end = Date.now() + timeout; do { for (const f of page.frames()) for (const m of await f.locator(css).all().catch(() => [])) if (await m.isVisible().catch(() => false)) return m; await page.waitForTimeout(300); } while (Date.now() < end); return null; };
      const firstOf = async (list, timeout = 10000) => { const end = Date.now() + timeout; do { for (const css of list) { const m = await field(css, 1); if (m) return m; } await page.waitForTimeout(300); } while (Date.now() < end); return null; };
      let stage = 'open';
      const fill = async (css, v, timeout = 15000, req = true) => { stage = 'fill ' + css.split(',')[0]; const end = Date.now() + timeout; do { const c = await field(css, 1000); if (c && await c.fill(v, { timeout: 2000 }).then(() => true, () => false)) return true; } while (Date.now() < end); if (req) throw Error('required field unavailable: ' + css.split(',')[0]); return false; };
      const host = f => { try { return new URL(f.url()).host; } catch { return ''; } };
      const isStripeHost = h => /(^|\.)stripe\.com$/.test(h) || h === '' || !!(offline && offline.hostedHosts && offline.hostedHosts.includes(h));   // offline: the local imitation page
      const isCaptchaHost = h => /(^|\.)hcaptcha\.com$/.test(h);
      const fieldIn = async (css, keep, timeout = 1500) => { const end = Date.now() + timeout; do { for (const f of page.frames()) if (keep(f)) for (const m of await f.locator(css).all().catch(() => [])) if (await m.isVisible().catch(() => false)) return m; await page.waitForTimeout(300); } while (Date.now() < end); return null; };
      const captchaChallengeVisible = async () => { for (const f of page.frames()) { if (!isCaptchaHost(host(f)) || !/challenge/i.test(f.url())) continue; const el = await f.frameElement().catch(() => null); if (el && await el.isVisible().catch(() => false)) return true; } return false; };
      const problems = async () => {
        const empty = [];
        for (const css of ['#payment-numberInput', '#payment-expiryInput', '#payment-cvcInput', '#payment-postalCodeInput', '#payment-linkMobilePhoneInput']) { const el = await field(css, 1); if (el && !(await el.inputValue().catch(() => ''))) empty.push(css.slice(1)); }
        const stripe = [], third = [];
        for (const f of page.frames()) {
          const h = host(f), texts = await f.locator('.FieldError:visible,[role="alert"]:visible,p[class*="Error"]:visible').evaluateAll(ns => ns.map(n => (n.innerText || '').trim()).filter(Boolean)).catch(() => []);
          for (const text of texts) (isStripeHost(h) ? stripe : third).push({ frame: h, text: scrubText(text) });
        }
        const dd = a => a.filter((m, i) => a.findIndex(x => x.frame === m.frame && x.text === m.text) === i).slice(0, 6);
        return { empty, stripe_messages: dd(stripe), third_party_messages: dd(third), messages: dd(stripe).map(m => m.text) };
      };
      const sessionStatus = async () => { const s = await api('GET', `/v1/checkout/sessions/${sessionId}`); return s.ok ? s.j.status : null; };
      let challenged = false;
      try {
        await page.goto(url, { waitUntil: 'domcontentloaded' });
        stage = 'complete hosted setup form';
        await fill('#linkAuthentication-emailInput,input[type=email]', `plotart-basket+${tag}-${label}@example.com`.toLowerCase(), 12000, false);
        const cardCSS = '#payment-numberInput,#cardNumber,input[autocomplete="cc-number"],input[name=cardnumber]';
        if (!await field(cardCSS, 3000)) await (await field('[data-testid="card-accordion-item-button"],button:text-is("Card"),[role="radio"]:text-is("Card")', 3000))?.click();
        await fill(cardCSS, card, 25000);
        await fill('#payment-expiryInput,#cardExpiry,input[autocomplete="cc-exp"]', '12 / 34');
        await fill('#payment-cvcInput,#cardCvc,input[autocomplete="cc-csc"]', '123');
        await fill('#payment-nameInput,#billingName,input[autocomplete="cc-name"]', 'Test Buyer', 3000, false);
        const FMT = { US: { postal: '10001', phone: '2015550123' }, GB: { postal: 'SW1A 1AA', phone: '7700900123' }, IE: { postal: 'D02 X285', phone: '851234567' }, CA: { postal: 'K1A 0B1', phone: '6135550123' } };
        const valueOf = async css => { const el = await field(css, 1500); return el ? String(await el.inputValue().catch(() => '')).toUpperCase() : ''; };
        const cc = await valueOf('#payment-countryInput,#billingCountry,select[autocomplete="country"]') || 'US';
        diag.billing_country = cc;
        if (await field('#payment-postalCodeInput,#billingPostalCode,input[autocomplete="postal-code"]', 1500)) await fill('#payment-postalCodeInput,#billingPostalCode,input[autocomplete="postal-code"]', (FMT[cc] || FMT.US).postal);
        if (await field('#payment-linkMobilePhoneInput', 1500)) { const pc = await valueOf('#payment-linkMobilePhoneCountryInput') || cc; diag.phone_country = pc; await fill('#payment-linkMobilePhoneInput', (FMT[pc] || FMT.US).phone); }
        await page.waitForTimeout(800);   // let Stripe validate the fields just filled
        const optInEl = await field('#payment-linkOptInInput', 500);
        diag.link_opt_in_checked = optInEl ? await optInEl.isChecked().catch(() => null) : 'absent';
        let pre = await problems();
        if (pre.messages.some(m => /phone/i.test(m))) {   // Link's phone is only needed because Link sign-up is ticked: untick it instead
          const optIn = await field('#payment-linkOptInInput', 1000);
          if (optIn && await optIn.isChecked().catch(() => false)) { await optIn.uncheck().catch(() => {}); diag.link_opt_in = 'unticked after phone rejected'; }
          await page.waitForTimeout(800); pre = await problems();
        }
        diag.pre_submit = pre;   // third-party warnings (e.g. hCaptcha) never stop the attempt by themselves
        if (pre.empty.length || pre.messages.length) { stage = 'pre-submit validation'; throw Error('form invalid before submit (Stripe field error or empty field)'); }
        stage = 'submit';
        const submit = await firstOf(['#payment-form-submit-button', '[data-testid="payment-form-submit-button"]', '[data-testid="hosted-payment-submit-button"]',
          'button[type="submit"]:text-matches("^(Pay|Save|Set up|Continue|Confirm)(\\s|$)","i")', 'button.SubmitButton'], 8000);
        if (!submit) throw Error('submit control missing');
        diag.submit_label = scrubText(await submit.innerText().catch(() => ''));
        await submit.click({ timeout: 10000 });
        stage = 'await completion or authentication';
        const end = Date.now() + 120000;
        let polled = 0, status = null;
        while (Date.now() < end) {
          if (page.url().startsWith(ORIGIN)) { diag.completed_by = 'redirect'; break; }
          if (Date.now() - polled > 3000) { polled = Date.now(); status = await sessionStatus(); if (status === 'complete') { diag.completed_by = 'stripe_session_status'; break; } }
          const auth = await fieldIn('#test-source-authorize-3ds,button:has-text("Complete"),button:has-text("COMPLETE")', f => !isCaptchaHost(host(f)), 1500);
          if (auth) { challenged = true; await auth.click().catch(() => {}); }
          if (await captchaChallengeVisible()) { diag.after_submit = await problems(); diag.verification = 'hcaptcha_challenge'; captchaBlocked = true; stage = 'additional verification required'; throw Error('Stripe requires additional verification (hCaptcha challenge): stopped, no bypass'); }
          const after = await problems();
          if (after.messages.length) { diag.after_submit = after; throw Error('Stripe rejected the form: ' + after.messages.join(' | ')); }
          await page.waitForTimeout(500);
        }
        if (!diag.completed_by) { diag.after_submit = await problems(); diag.session_status = await sessionStatus(); throw Error('hosted page did not complete'); }
        return { completed: true, challenged, return_url: page.url().startsWith(ORIGIN) ? page.url() : null, completed_by: diag.completed_by, link_opt_in_checked: diag.link_opt_in_checked };
      } catch (e) {
        const controls = [], errors = [];
        for (const f of page.frames()) {
          controls.push(...await f.locator('input:visible,select:visible,button:visible').evaluateAll(ns => ns.map(n => n.id ? 'id:' + n.id : n.getAttribute('data-testid') ? 'testid:' + n.getAttribute('data-testid') : n.getAttribute('autocomplete')).filter(Boolean)).catch(() => []));
          errors.push(...await f.locator('[role="alert"]:visible,.FieldError:visible,[class*="Error"]:visible,[aria-invalid="true"]:visible').evaluateAll(ns => ns.map(n => (n.innerText || n.getAttribute('aria-label') || n.id || '').trim()).filter(Boolean)).catch(() => []));
        }
        let screenshot = null;
        await page.waitForTimeout(1500).catch(() => {});
        try { mkdirSync(HERE + 'stripe-test-evidence/', { recursive: true }); screenshot = `basket-e2e-${label}.png`; await page.screenshot({ path: HERE + 'stripe-test-evidence/' + screenshot, fullPage: true }); } catch { screenshot = 'not captured'; }
        return { stage, error: scrubText(e.message), captcha: captchaBlocked, challenged, page_host: (() => { try { return new URL(page.url()).host; } catch { return null; } })(),
          validation_messages: [...new Set(errors.map(scrubText))].slice(0, 10), visible_controls: [...new Set(controls)].filter(s => /^[a-zA-Z][\w :.-]{0,64}$/.test(s)).slice(0, 40), screenshot, ...diag };
      } finally { await page.close().catch(() => {}); }
    }
    const BUYER = { name: 'Test Buyer', address_line1: '7 Harbour Road', town: 'Kinsale', county: 'Cork', eircode: 'P17 XY12', phone: '+353 21 555 0199' };
    async function openAndPay(ids, card, label) {
      const r = await pub('POST', '/basket/checkout', { artworks: ids, accept_terms: 'PA-BBT-TEST-01', email: `plotart-basket+${tag}-${label}@example.com`.toLowerCase(), ...BUYER });
      if (r.s !== 200) return { error: r.j };
      const b = await one('SELECT * FROM checkout_baskets ORDER BY created_at DESC LIMIT 1'); created.baskets.push(b.id);
      const s0 = await one('SELECT setup_session FROM checkout_baskets WHERE id = ?', b.id);
      const entry = await enterCard(r.j.url, card, label, s0.setup_session);
      const s = await one('SELECT setup_session FROM checkout_baskets WHERE id = ?', b.id);
      const sess = await api('GET', `/v1/checkout/sessions/${s.setup_session}`);
      // the buyer's return address: from the browser redirect, or (if Stripe completed but the redirect was not seen) from the session itself
      const returnPath = entry.return_url ? new URL(entry.return_url).pathname : entry.completed && sess.ok && sess.j.success_url ? new URL(sess.j.success_url).pathname : null;
      if (returnPath) await pub('GET', returnPath);   // the buyer's return: PlotArt checks with Stripe and runs the basket forward
      return { basket: await one('SELECT * FROM checkout_baskets WHERE id = ?', b.id), lines: await q('SELECT * FROM basket_lines WHERE basket_id = ? ORDER BY line_no', b.id), entry, session: { mode: sess.j.mode, status: sess.j.status, account_header: false }, returnPath };
    }

    // ---- A · one card entry, two artists, authorise both, capture both
    const A = await openAndPay(['wagal1', 'wafnd1'], CARDS.ok, 'a');
    ok('BE-A0', 'ONE card entry on Stripe’s hosted page (setup mode, PlotArt’s account) completes', !!A.entry && A.entry.completed && A.session.mode === 'setup' && A.session.status === 'complete', { entry: A.entry, session: A.session, error: A.error });
    if (A.basket) {
      const pis = await Promise.all(A.lines.map(l => l.payment_intent ? api('GET', `/v1/payment_intents/${l.payment_intent}?expand[]=latest_charge`, null, l.account) : null));
      ok('BE-A1', 'the basket is paid only after BOTH artists’ direct charges were authorised then captured on their own accounts', A.basket.status === 'paid' && pis.every(p => p && p.j.status === 'succeeded') && A.lines[0].account === accounts[0] && A.lines[1].account === accounts[1],
        { status: A.basket.status, resolution: A.basket.resolution, lines: A.lines.map(l => ({ state: l.state, err: l.last_error, code: l.decline_code })), pis: pis.map(p => p && { status: p.j.status, capture_method: p.j.capture_method }) });
      ok('BE-A2', 'commission on Stripe: EUR 18.00 application fee on the Gallery Artist’s charge, none on the Founding Artist’s; delivery never commissioned', pis[0] && pis[0].j.application_fee_amount === 1800 && pis[0].j.amount === 13000 && pis[1] && !pis[1].j.application_fee_amount && pis[1].j.amount === 9000,
        pis.map(p => p && { amount: p.j.amount, fee: p.j.application_fee_amount }));
      const ords = await q('SELECT o.status, o.payment_status, o.commission_cents FROM checkout_orders o JOIN basket_lines l ON l.order_id = o.id WHERE l.basket_id = ? ORDER BY l.line_no', A.basket.id);
      ok('BE-A3', 'each artwork’s order is recorded as paid and sold through the existing order path (ledger, sold mark, confirmation)', ords.every(o => o.status === 'paid' && o.payment_status === 'paid')
        && (await q("SELECT * FROM order_messages WHERE kind = 'buyer_confirmation' AND order_id IN (SELECT order_id FROM basket_lines WHERE basket_id = ?)", A.basket.id)).length === 2, ords);
      const cus = A.basket.platform_customer && await api('GET', '/v1/customers/' + A.basket.platform_customer);
      ok('BE-A4', 'the buyer’s saved card is not kept on PlotArt’s account after the basket (Customer deleted)', !!cus && (cus.j.deleted === true || cus.status === 404), cus && { deleted: cus.j.deleted, http: cus.status });
      const again = await pub('GET', A.returnPath || '/');
      const pis2 = await Promise.all(A.lines.map(l => api('GET', `/v1/payment_intents/search?query=${encodeURIComponent(`metadata['plotart_order']:'${l.order_id}'`)}`, null, l.account)));
      info('BE-A5', 'a second return from Stripe changes nothing (no second authorisation); Search API view', { http: again.s, found: pis2.map(p => p.ok ? p.j.data.length : p.err) });
    }

    // ---- B · a card that saves but is declined: nothing is captured, the works are released
    const B = await openAndPay(['wagal2', 'wafnd2'], CARDS.declineAfterAttach, 'b');
    if (B.entry && B.entry.completed) {
      ok('BE-B1', 'a declined artist charge fails the basket; no charge is captured and both works are released', B.basket.status === 'failed' && B.lines.some(l => l.state === 'declined') && !B.lines.some(l => l.state === 'captured')
        && (await q('SELECT * FROM artwork_reservations WHERE artwork_id IN (?,?)', 'wagal2', 'wafnd2')).length === 0, { status: B.basket.status, lines: B.lines.map(l => ({ state: l.state, code: l.decline_code })) });
    } else info('BE-B1', 'decline scenario not run (hosted page)', B.entry || B.error);

    // ---- C · a card that always needs authentication: the basket waits for the buyer, then cancels at the deadline
    const Cb = await openAndPay(['wagal3', 'wafnd3'], CARDS.alwaysAuth, 'c');
    if (Cb.entry && Cb.entry.completed) {
      info('BE-C1', 'card that always needs authentication: state after the one card entry', { status: Cb.basket.status, lines: Cb.lines.map(l => ({ state: l.state, code: l.decline_code })) });
      if (Cb.basket.status === 'action_required') {
        await db.prepare('UPDATE checkout_baskets SET action_deadline = ? WHERE id = ?').bind(new Date(Date.now() - 60_000).toISOString(), Cb.basket.id).run();
        await CW.scheduled({ scheduledTime: Date.now(), cron: '*/5 * * * *' });
        const after = await one('SELECT * FROM checkout_baskets WHERE id = ?', Cb.basket.id), ls = await q('SELECT * FROM basket_lines WHERE basket_id = ?', Cb.basket.id);
        const pis = await Promise.all(ls.filter(l => l.payment_intent).map(l => api('GET', `/v1/payment_intents/${l.payment_intent}`, null, l.account)));
        ok('BE-C2', 'when the extra check is not completed in time, every authorisation is cancelled at Stripe and nothing is bought', after.status === 'failed' && pis.every(p => ['canceled', 'requires_payment_method'].includes(p.j.status)), { status: after.status, pis: pis.map(p => p.j.status) });
      }
    } else info('BE-C1', 'authentication scenario not run (hosted page)', Cb.entry || Cb.error);

    // ---- D · refund one artwork of the paid basket through the existing founder refund (one artist only)
    if (A.basket && A.basket.status === 'paid') {
      const o = await one('SELECT o.* FROM checkout_orders o JOIN basket_lines l ON l.order_id = o.id WHERE l.basket_id = ? AND l.line_no = 1', A.basket.id);
      const r = await call('POST', `/api/admin/checkout/orders/${o.id}/refund`, FOUNDER, { artwork_cents: o.artwork_cents, delivery_cents: o.delivery_cents, reason: 'TEST: buyer cancelled' });
      const led = await q("SELECT kind, amount_cents FROM order_ledger WHERE order_id = ? AND kind IN ('artwork_refund','delivery_refund','commission_refund')", o.id);
      ok('BE-D1', 'one basket artwork refunded on its artist’s account through the existing refund action; the other artist’s payment is untouched', r.s === 200 && led.some(x => x.kind === 'artwork_refund'), { http: r.s, error: r.j && r.j.error, ledger: led });
    }
  } catch (e) {
    rec('BE-X', 'unexpected error (clean-up follows)', SRC, 'FAIL', { message: String(e.message).slice(0, 300) });
  } finally {
    if (browser) await browser.close().catch(() => {});
    // ---- clean-up and verification: every payment this run made, on both accounts, refunded or cancelled; customers deleted
    const out = { refunded: 0, cancelled: 0, errors: [] }, left = [];
    try {
      const lines = await (async () => (await S.db.prepare(`SELECT l.*, b.platform_customer FROM basket_lines l JOIN checkout_baskets b ON b.id = l.basket_id`).all()).results)();
      for (const l of lines.filter(x => x.payment_intent)) {
        const p = await api('GET', `/v1/payment_intents/${l.payment_intent}?expand[]=latest_charge`, null, l.account);
        if (!p.ok) { out.errors.push({ pi: l.payment_intent, read: p.err }); continue; }
        const ch = p.j.latest_charge && typeof p.j.latest_charge === 'object' ? p.j.latest_charge : null;
        if (['requires_capture', 'requires_payment_method', 'requires_action', 'requires_confirmation'].includes(p.j.status)) {
          const c = await api('POST', `/v1/payment_intents/${l.payment_intent}/cancel`, {}, l.account); if (c.ok) out.cancelled++; else out.errors.push({ pi: l.payment_intent, cancel: c.err });
        } else if (p.j.status === 'succeeded' && ch && ch.amount_refunded < ch.amount_captured) {
          const body = { payment_intent: l.payment_intent, 'metadata[plotart_test_cleanup]': tag }; if (p.j.application_fee_amount > 0) body.refund_application_fee = 'true';
          const r = await api('POST', '/v1/refunds', body, l.account); if (r.ok) out.refunded++; else out.errors.push({ pi: l.payment_intent, refund: r.err });
        }
      }
      for (const l of lines.filter(x => x.payment_intent)) {
        const p = await api('GET', `/v1/payment_intents/${l.payment_intent}?expand[]=latest_charge`, null, l.account);
        const ch = p.j.latest_charge && typeof p.j.latest_charge === 'object' ? p.j.latest_charge : null;
        const done = p.j.status === 'canceled' || (p.j.status === 'succeeded' && ch && ch.amount_refunded >= ch.amount_captured);
        if (!done) left.push({ account: l.account, pi: l.payment_intent, status: p.j.status });
      }
      for (const c of [...new Set(lines.map(l => l.platform_customer).filter(Boolean))]) { const r = await api('DELETE', '/v1/customers/' + c); if (!r.ok && r.status !== 404) out.errors.push({ customer: c, err: r.err }); }
      ok('BE-Z', 'clean-up: every payment from this run refunded or cancelled on both artist accounts; the buyer’s test customers deleted', out.errors.length === 0 && left.length === 0, { ...out, left, run_tag: tag });
    } catch (e) { rec('BE-Z', 'clean-up', SRC, 'FAIL', { message: String(e.message).slice(0, 300), ...out }); }
    await S.mf.dispose().catch(() => {});
  }
}
