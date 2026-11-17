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
    async function payInBrowser(url, card, tag) {
      if (!browser) { const req = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json'); browser = await req('playwright').chromium.launch(); }
      const page = await browser.newPage({ locale: 'en-IE', timezoneId: 'Europe/Dublin', viewport: { width: 1280, height: 1000 } });
      try {
        await page.goto(url, { waitUntil: 'networkidle', timeout: 60_000 }).catch(() => page.waitForLoadState('domcontentloaded'));
        // Checkout may show payment methods as an accordion; open the card option if it is collapsed
        for (const sel of ['[data-testid="card-accordion-item-button"]', '#payment-method-accordion-item-title-card', 'button:has-text("Card")', '[aria-label="Pay with card"]'])
          if (await page.locator(sel).count()) { await page.locator(sel).first().click().catch(() => {}); break; }
        // the card number field, on the page or inside a payment frame
        const find = async (sels) => { for (const f of [page.mainFrame(), ...page.frames()]) for (const sl of sels) { const l = f.locator(sl); if (await l.count().catch(() => 0)) return l.first(); } return null; };
        let num = null; for (let i = 0; i < 30 && !num; i++) { num = await find(['#cardNumber', 'input[name="cardnumber"]', 'input[name="cardNumber"]', 'input[autocomplete="cc-number"]']); if (!num) await page.waitForTimeout(1000); }
        if (!num) throw new Error('card number field not found');
        await num.fill(card);
        const exp = await find(['#cardExpiry', 'input[name="exp-date"]', 'input[autocomplete="cc-exp"]']); if (exp) await exp.fill('12 / 34');
        const cvc = await find(['#cardCvc', 'input[name="cvc"]', 'input[autocomplete="cc-csc"]']); if (cvc) await cvc.fill('123');
        const name = await find(['#billingName', 'input[autocomplete="cc-name"]']); if (name) await name.fill('E2E Test Buyer');
        if (await page.locator('#billingCountry').count()) await page.locator('#billingCountry').selectOption('IE').catch(() => {});
        const pc = await find(['#billingPostalCode', 'input[autocomplete="postal-code"]']); if (pc) await pc.fill('D02 X285').catch(() => {});
        // the Pay button (Playwright locators reach into Checkout's shadow DOM; plain querySelector does not)
        let pay = null;
        for (const l of [page.getByTestId('hosted-payment-submit-button'), page.locator('.SubmitButton'), page.getByRole('button', { name: /^(pay|complete)/i }), page.locator('button[type="submit"]')])
          if (await l.count().catch(() => 0)) { pay = l.first(); break; }
        if (!pay) throw new Error('Pay button not found');
        await page.screenshot({ path: `${HERE}stripe-test-evidence/checkout-${tag}-filled.png`, fullPage: true }).catch(() => {});
        await pay.click({ timeout: 30_000 });
        await page.waitForURL(/plotart-checkout-test\.invalid/, { timeout: 60_000 }).catch(() => {});
      } catch (e) {
        // diagnostics for the evidence artifact: a screenshot and the visible form controls (no secrets on a test Checkout page)
        try { await page.screenshot({ path: `${HERE}stripe-test-evidence/checkout-${tag}.png`, fullPage: true }); } catch {}
        try { const ctl = await page.evaluate(() => [...document.querySelectorAll('input,button,select,iframe')].slice(0, 60).map(x => [x.tagName, x.id, x.name, x.getAttribute('autocomplete'), x.getAttribute('data-testid'), (x.innerText || '').slice(0, 40), x.src ? new URL(x.src).host : ''].join('|')));
          writeFileSync(`${HERE}stripe-test-evidence/checkout-${tag}-controls.txt`, ctl.join('\n') + '\nframes: ' + page.frames().map(f => f.url().slice(0, 80)).join(' , ') + '\n'); } catch {}
        throw e;
      } finally { await page.close(); }
    }

    // 1 · payment, verified only by Stripe's signed event
    const o1 = await quote('wagal1', 'PA-E-261116-E2E001');
    rec('E2', 'the pilot opens real hosted checkout on the artist’s account for the approved quote', SRC, o1.status === 303 && /checkout\.stripe\.com/.test(o1.url || '') ? 'PASS' : 'FAIL', { status: o1.status, host: o1.url && new URL(o1.url).host });
    try { await payInBrowser(o1.url, '4242424242424242', 'pay'); } catch (e) { rec('E3a', 'buyer pays on Stripe Checkout (headless browser)', SRC, 'FAIL', { error: String(e.message).slice(0, 300) }); }
    const paid = await waitFor(async () => { const o = await order(o1.id); return o.payment_status === 'paid' ? o : null; });
    const evs = await q("SELECT event_id, type, status FROM payment_events WHERE order_id = ?", o1.id);
    rec('E3', 'a REAL signed checkout.session.completed marks the order paid (and the work sold)', SRC, paid && evs.some(e => e.type === 'checkout.session.completed' && e.status === 'processed')
      && (await db.prepare("SELECT availability FROM artworks WHERE id='wagal1'").first()).availability === 'sold' ? 'PASS' : 'FAIL', { payment_status: paid && paid.payment_status, events: evs });
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
    try { await payInBrowser(o3.url, '4000000000000259', 'dispute'); } catch (e) { rec('E7a', 'buyer pays with the dispute test card', SRC, 'FAIL', { error: String(e.message).slice(0, 300) }); }
    const disputed = await waitFor(async () => (await order(o3.id)).dispute_status === 'open', 150_000);
    rec('E7', 'a REAL charge.dispute.created (arriving after or before the payment event) marks the order disputed', SRC, disputed ? 'PASS' : 'FAIL',
      { status: (await order(o3.id)).status, dispute_status: (await order(o3.id)).dispute_status, events: await q("SELECT type, status FROM payment_events WHERE object_id LIKE 'dp_%' OR order_id = ?", o3.id) });
    const bad = await q("SELECT type, status, detail FROM payment_events WHERE status IN ('failed')");
    rec('E8', 'no real event failed processing', SRC, bad.length ? 'FAIL' : 'PASS', { failed: bad, total: (await q('SELECT COUNT(*) AS n FROM payment_events'))[0].n });
  } catch (e) { rec('E9', 'end-to-end run', SRC, 'FAIL', { error: String(e.stack || e.message).slice(0, 500) }); }
  finally { if (browser) await browser.close(); await S.mf.dispose(); }
}
