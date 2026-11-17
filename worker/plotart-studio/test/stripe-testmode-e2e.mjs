// END-TO-END · the pilot's own Workers (Miniflare, local D1) against the REAL Stripe test API, with REAL signed webhook
// deliveries forwarded by `stripe listen --forward-connect-to http://127.0.0.1:<port>/v1/stripe/webhook`, and the buyer
// paying on Stripe's hosted Checkout in headless Chromium (Playwright). Called by stripe-testmode-checks.mjs (phase e2e).
// Results are labelled source "stripe-test-api+pilot": Stripe's real responses and events, processed by the pilot's code.
import { readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
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
  const S = await start({ port, env: ENVV, checkout: { env: ENVV } });
  const { db } = S, CW = S.checkoutWorker;
  const q = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results;
  const call = async (method, path, email, body) => { const r = await S.mf.dispatchFetch(S.url + path, { method, headers: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
    const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* */ } return { s: r.status, j }; };
  const order = id => db.prepare('SELECT * FROM checkout_orders WHERE id = ?').bind(id).first();
  const waitFor = async (fn, ms = 90_000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { const v = await fn(); if (v) return v; await sleep(2000); } return null; };
  let browser = null;
  try {
    const GAL = `gal+${RUN}@plotnua.invalid`, ago = d => new Date(Date.now() - d * 86400_000).toISOString(), FAKE = 'a'.repeat(64);
    await seedPublished(db, { id: 'agal', slug: 'gal', email: GAL, name: 'E2E Test Gallery Artist', works: 3, publishedAt: ago(30) });
    await db.prepare("UPDATE artists SET founding = 0 WHERE id = 'agal'").run();
    await db.prepare("INSERT INTO gallery_agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at) VALUES ('PA-GAA-2026-11','gallery_artist_agreement','t','fixed',?,?,'2018-01-01T00:00:00Z',?)").bind(FAKE, FAKE, ago(0)).run();
    await db.prepare(`INSERT INTO gallery_agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, method, statement, created_at) VALUES ('gaa1','ev1','agal','PA-GAA-2026-11',?,?,?,?, 'E2E','studio_checkbox','test',?)`).bind(FAKE, FAKE, ago(20), GAL, ago(20)).run();
    await db.prepare("INSERT INTO artist_terms (artist_id, track, commission_bp, set_by, created_at, updated_at) VALUES ('agal','gallery_artist',1500,?,?,?)").bind(FOUNDER, ago(20), ago(20)).run();
    for (const [id, ref] of [['l1', 'PA-E-261116-E2E001'], ['l2', 'PA-E-261116-E2E002'], ['l3', 'PA-E-261116-E2E003']])
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
      condition_photos: true, return_route: 'Same courier', shipment_confirmation_ref: 'SIM-1', shipment_confirmed_by: 'SIMULATED', shipment_confirmed_on: new Date().toISOString().slice(0, 10),
      cover_confirmation_ref: 'SIM-COVER-1', cover_confirmed_by: 'SIMULATED', cover_confirmed_on: new Date().toISOString().slice(0, 10) };
    const ALL = { available: true, location: true, condition: true, framing: true, dimensions: true, packing_and_handover: true };
    async function quote(work, ref, artwork = 100000, delivery = 7500) {
      const c = await call('POST', '/api/admin/checkout/orders', FOUNDER, { artist_id: 'agal', artwork_id: work, enquiry_ref: ref, buyer_email: `buyer+${RUN}@plotnua.invalid` });
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
    const redact = t => String(t || '').replace(/^(\s*- (?:textbox|combobox|spinbutton|searchbox)[^:\n]*):.*$/gm, '$1: [redacted]').replace(/[\w.+-]+@[\w-]+\.[\w.]+/g, '[email]');
    async function snapshot(page, tag, stage) {
      const out = { stage, url: safeUrl(page.url()), title: await page.title().catch(() => ''), frames: [] };
      for (const f of page.frames()) {
        let aria = ''; try { aria = await f.locator('body').ariaSnapshot({ timeout: 5000 }); } catch (e) { aria = 'unavailable: ' + String(e.message).split('\n')[0]; }
        out.frames.push({ url: safeUrl(f.url()), aria: redact(aria).slice(0, 6000) });
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
        const ctry = await anyFrame(page, f => f.locator('#billingCountry, select[autocomplete="country"]'), 2_000); if (ctry) await ctry.selectOption('IE').catch(() => {});
        await fillIf(f => f.getByRole('textbox', { name: /postal|eircode|zip/i }).or(f.locator('#billingPostalCode, input[autocomplete="postal-code"]')), 'D02 X285', 2_000);
        step('card details entered (values not recorded)');
        const pay = await anyFrame(page, f => f.getByTestId('hosted-payment-submit-button').or(f.getByRole('button', { name: /^(pay|complete|buy)\b/i })).or(f.locator('.SubmitButton')), 30_000);
        if (!pay) throw new Error('Pay button not visible in the page or any frame');
        step('pay button visible: ' + ((await pay.getAttribute('data-testid').catch(() => null)) || (await pay.innerText().catch(() => '')).slice(0, 30)));
        await pay.click();
        await page.waitForURL(/plotart-checkout-test\.invalid/, { timeout: 90_000 }); step('returned to success_url');
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
    const o1 = await quote('wagal1', 'PA-E-261116-E2E001');
    rec('E2', 'the pilot opens real hosted checkout on the artist’s account for the approved quote', SRC, o1.status === 303 && /checkout\.stripe\.com/.test(o1.url || '') ? 'PASS' : 'FAIL', { status: o1.status, host: o1.url && new URL(o1.url).host });
    let paidOk = false;
    try { const r = await payInBrowser(o1.url, '4242424242424242', 'pay'); paidOk = true; rec('E3a', 'buyer pays on the real hosted Stripe Checkout page (headless browser) and returns to the success page', SRC, 'PASS', { final_url: r.diag.finalUrl, steps: r.diag.steps }); }
    catch (e) { rec('E3a', 'buyer pays on the real hosted Stripe Checkout page (headless browser)', SRC, 'FAIL', { error: String(e.message).split('\n')[0].slice(0, 300), final_url: e.diag && e.diag.finalUrl, steps: e.diag && e.diag.steps, page_errors: e.diag && e.diag.pageErrors, http_errors: e.diag && e.diag.httpErrors.slice(0, 10) }); }
    const paid = await waitFor(async () => { const o = await order(o1.id); return o.payment_status === 'paid' ? o : null; }, paidOk ? 90_000 : 20_000);
    const evs = await q("SELECT event_id, type, status FROM payment_events WHERE order_id = ?", o1.id);
    const e3ok = paid && evs.some(e => e.type === 'checkout.session.completed' && e.status === 'processed') && (await db.prepare("SELECT availability FROM artworks WHERE id='wagal1'").first()).availability === 'sold';
    rec('E3', 'a REAL signed checkout.session.completed marks the order paid (and the work sold)', SRC, e3ok ? 'PASS' : paidOk ? 'FAIL' : 'SKIP',
      { ...(paidOk || e3ok ? {} : { blocked_by: 'E3a — no payment was made, so no completion event could arrive; webhook handling NOT exercised' }), payment_status: paid && paid.payment_status, events: evs });
    if (paid) {
      const pi = (await stripe('GET', `/v1/payment_intents/${paid.payment_intent}?expand[]=latest_charge.balance_transaction`, null, ACCOUNT)).j;
      let ch = pi.latest_charge;   // the fee and balance transaction are created asynchronously: wait for them
      for (let i = 0; i < 20 && ch && (!ch.application_fee || !ch.balance_transaction); i++) { await sleep(1500); ch = (await stripe('GET', `/v1/charges/${ch.id}?expand[]=balance_transaction`, null, ACCOUNT)).j; }
      const led = await q('SELECT kind, amount_cents FROM order_ledger WHERE order_id = ? ORDER BY kind', o1.id);
      rec('E4', 'Stripe’s charge matches the pilot ledger: €1,075 charged, €150 application fee, delivery outside commission', SRC,
        ch.amount === 107500 && ch.application_fee_amount === 15000 && led.find(l => l.kind === 'commission').amount_cents === 15000 && led.find(l => l.kind === 'delivery_allocation').amount_cents === 7500 ? 'PASS' : 'FAIL',
        { charge: ch.id, amount: ch.amount, application_fee_amount: ch.application_fee_amount, stripe_fee: ch.balance_transaction && ch.balance_transaction.fee, ledger: led });
      // 2 · partial refund through the pilot, confirmed by Stripe's events
      const r = await call('POST', `/api/admin/checkout/orders/${o1.id}/refund`, FOUNDER, { artwork_cents: 10000, delivery_cents: 0, reason: 'E2E partial refund test' });
      const rr = await waitFor(async () => { const x = await db.prepare("SELECT * FROM order_refunds WHERE order_id = ?").bind(o1.id).first(); return x && x.status !== 'pending' ? x : null; }, 120_000);
      const feeObj = (await stripe('GET', `/v1/application_fees/${ch.application_fee}`)).j;
      rec('E5', 'partial refund €100 of the artwork: completed (directly or via webhook/sweep) and €15 commission returned', SRC,
        rr && rr.status === 'succeeded' && feeObj.amount_refunded === 1500 ? 'PASS' : (rr ? 'FAIL' : 'INFO'), { http: r.s, refund_status: rr ? rr.status : 'still pending after 120s', fee_amount_refunded: feeObj.amount_refunded, flag: (await order(o1.id)).needs_resolution });
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
    try { const r = await payInBrowser(o3.url, '4000000000000259', 'dispute'); dispPaid = true; rec('E7a', 'buyer pays with the dispute test card on the real hosted Checkout page', SRC, 'PASS', { final_url: r.diag.finalUrl }); }
    catch (e) { rec('E7a', 'buyer pays with the dispute test card on the real hosted Checkout page', SRC, 'FAIL', { error: String(e.message).split('\n')[0].slice(0, 300), final_url: e.diag && e.diag.finalUrl, steps: e.diag && e.diag.steps, page_errors: e.diag && e.diag.pageErrors }); }
    const disputed = dispPaid ? await waitFor(async () => (await order(o3.id)).dispute_status === 'open', 150_000) : null;
    rec('E7', 'a REAL charge.dispute.created (arriving after or before the payment event) marks the order disputed', SRC, disputed ? 'PASS' : dispPaid ? 'FAIL' : 'SKIP',
      { ...(dispPaid ? {} : { blocked_by: 'E7a — no payment was made, so no dispute could open; webhook handling NOT exercised' }), status: (await order(o3.id)).status, dispute_status: (await order(o3.id)).dispute_status, events: await q("SELECT type, status FROM payment_events WHERE object_id LIKE 'dp_%' OR order_id = ?", o3.id) });
    // E8 only counts if the events this run depends on actually arrived and were processed
    const all = await q('SELECT type, status FROM payment_events');
    const bad = all.filter(e => e.status === 'failed');
    const expected = ['checkout.session.completed', 'checkout.session.expired', 'charge.dispute.created'];
    const missing = expected.filter(t => !all.some(e => e.type === t && e.status === 'processed'));
    rec('E8', 'every expected real signed event (payment completed, session expired, dispute created) arrived and processed, and none failed', SRC,
      bad.length ? 'FAIL' : missing.length ? 'SKIP' : 'PASS', { failed: bad, missing_expected: missing, received: all.map(e => `${e.type}:${e.status}`), ...(missing.length && !bad.length ? { note: 'not a success: expected events never arrived' } : {}) });
  } catch (e) { rec('E9', 'end-to-end run', SRC, 'FAIL', { error: String(e.stack || e.message).slice(0, 500) }); }
  finally { if (browser) await browser.close(); await S.mf.dispose(); }
}
