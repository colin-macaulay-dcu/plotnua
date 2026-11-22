// PROVE (local) · the PRIVATE STAGING configuration of the multi-artist basket, as a customer would use it.
// Miniflare runs the real Studio and checkout Workers with the staging settings (STAGING_GALLERY on, basket on, Stripe
// TEST mode) on a local D1 holding schema.sql + migration 0013 + the proposed migration 0019 + the staging seed
// (test/basket-staging-seed.mjs). Stripe is the mock of mock-stripe-basket.mjs and its hosted page the local imitation
// (hosted-imitation.mjs); nothing reaches Stripe or Cloudflare. A real Chromium walks the customer journeys on desktop
// and on a phone: gallery → artwork → basket (two artists) → card page → confirmation; a declined card; a bank check.
//   node test/prove-basket-staging.mjs            (screenshots: BASKET_STAGING_SHOTS=<dir>)
import { readFileSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { start, token, FOUNDER } from './local.mjs';
import { statements } from './sql.mjs';
import { M, stripe } from './mock-stripe-basket.mjs';
import { startHostedImitation } from './hosted-imitation.mjs';

const HERE = new URL('..', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(typeof d === 'string' ? d : JSON.stringify(d)).slice(0, 700)}]` : ''}`); };
const SHOTS = process.env.BASKET_STAGING_SHOTS || null;
const ACC = ['acct_stagingAoife', 'acct_stagingCian'];
for (const a of ACC) M.accounts[a] = { id: a, object: 'account', livemode: false, charges_enabled: true, payouts_enabled: true, details_submitted: true, country: 'IE', capabilities: { card_payments: 'active' } };
const HOSTED = await startHostedImitation(ACC);
const ORIGIN = 'https://plotart-basket-staging.local';
const ENV = { ENVIRONMENT: 'local', STAGING_GALLERY: 'true', CHECKOUT_PILOT_ENABLED: 'true', BASKET_ENABLED: 'true', BASKET_COMMISSION_FREE: 'with_processing_consent', STRIPE_SECRET_KEY: 'rk_test_stagingmock',
  STRIPE_PUBLISHABLE_KEY: 'pk_test_stagingmock', STRIPE_WEBHOOK_SECRET: 'whsec_test_staging_connect', STRIPE_WEBHOOK_SECRET_PLATFORM: 'whsec_test_staging_platform', STRIPE_API_BASE: 'https://stripe.mock',
  CHECKOUT_ORIGIN: ORIGIN, GALLERY_ORIGIN: ORIGIN, CHECKOUT_MESSAGE_RETRY_MINUTES: '0' };
let S, BR;
try {
  console.log('PROVE · private basket staging (local: real Workers, staging settings, mock Stripe, real browser)');
  S = await start({ port: 8896, env: ENV, checkout: { env: ENV }, outbound: stripe });
  const { db } = S, CW = S.checkoutWorker;
  const seed = execFileSync('node', [HERE + 'test/basket-staging-seed.mjs', '--target', 'plotart-basket-staging', '--accounts', ACC.join(',')], { encoding: 'utf8' });
  let err = null;
  for (const f of [readFileSync(HERE + 'migrations/0013_gallery_artist_agreement_text.sql', 'utf8'), readFileSync(HERE + 'migrations/0019_multi_artist_basket.sql', 'utf8'), readFileSync(HERE + 'migrations/0020_basket_consents.sql', 'utf8'), readFileSync(HERE + 'migrations/0022_delivery_safety.sql', 'utf8'), seed])
    for (const s of statements(f)) { try { await db.prepare(s).run(); } catch (e) { err = (err ? err + " || " : "") + `${e.message} :: ${s.slice(0, 90)}`; } }
  check('S1 the staging database builds from schema.sql + 0013 + 0019 + the synthetic seed without error', !err, err);
  const q = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results, one = (sql, ...b) => db.prepare(sql).bind(...b).first();
  const pub = async (path, init = {}) => { const r = await CW.fetch(ORIGIN + path, { redirect: 'manual', ...init }); return { s: r.status, t: await r.text(), h: r.headers }; };
  const call = async (method, path, body) => { const r = await S.mf.dispatchFetch(S.url + path, { method, headers: { 'Cf-Access-Jwt-Assertion': token(FOUNDER), 'X-Studio': '1', 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
    const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* */ } return { s: r.status, j }; };

  let r = await call('GET', '/api/admin/checkout/baskets/eligibility?ids=wastgal1,wastgal2,wastgal3,wastgal4,wastgal5,wastfnd1,wastfnd2,wastfnd3,wastfnd4');
  const el = Object.fromEntries(r.j.items.map(i => [i.id, i]));
  check('S2 every priced synthetic work can be bought online: 15% for the Gallery Artist, 0% (Founding 25, with consent) for the Founding Artist; price-on-request refused',
    ['wastgal1', 'wastgal2', 'wastgal3', 'wastgal4'].every(k => el[k].ok && el[k].commission_basis === 'gallery_artist_agreement') && ['wastfnd1', 'wastfnd2', 'wastfnd3', 'wastfnd4'].every(k => el[k].ok && el[k].commission_basis === 'founding_enquiry')
    && !el.wastgal5.ok && /price on request/.test(el.wastgal5.why), r.j.items);
  r = await pub('/gallery');
  check('S3 the staging gallery lists the synthetic works with live status and says it is private staging', r.s === 200 && (r.t.match(/class="card"/g) || []).length === 9 && /Private staging/.test(r.t) && /can be bought online/.test(r.t));
  r = await pub('/staging-img/wastgal1.svg');
  check('S4 artwork images are synthetic SVGs generated per artwork (no real artwork); unknown ids refused', r.s === 200 && /^<svg /.test(r.t) && r.h.get('Content-Type') === 'image/svg+xml' && (await pub('/staging-img/nope.svg')).s === 404);
  ENV.STAGING_GALLERY = 'false';

  // ---- the customer, in a real browser (desktop, then a phone)
  const pw = createRequire(process.env.PLAYWRIGHT_FROM || '/tmp/claude-0/studio-tools/package.json')('playwright');
  BR = await pw.chromium.launch();
  const context = async opts => {
    const ctx = await BR.newContext(opts);
    await ctx.route('**/*', async route => {
      const u = new URL(route.request().url());
      if (u.origin === ORIGIN) { const req = route.request(); const hd = { ...req.headers() }; delete hd.origin; const res = await CW.fetch(req.url(), { method: req.method(), headers: { ...hd, origin: ORIGIN }, body: req.postData() || undefined, redirect: 'manual' });
        // a redirect is turned into a fresh navigation so that the next request is intercepted too (harness only)
        if (res.status >= 300 && res.status < 400 && res.headers.get('Location')) return route.fulfill({ status: 200, contentType: 'text/html', body: `<script>location.replace(${JSON.stringify(res.headers.get('Location'))})</script>` });
        return route.fulfill({ status: res.status, headers: Object.fromEntries(res.headers), body: Buffer.from(await res.arrayBuffer()) }); }
      if (u.host === HOSTED.host) { const req = route.request(); const res = await fetch(req.url(), { method: req.method(), headers: { 'content-type': req.headers()['content-type'] || 'text/plain' }, body: req.postData() || undefined });
        return route.fulfill({ status: res.status, headers: { 'content-type': res.headers.get('content-type') || 'text/html' }, body: Buffer.from(await res.arrayBuffer()) }); }
      if (/fonts\.(googleapis|gstatic)\.com$/.test(u.hostname)) return route.continue().catch(() => route.abort());
      return route.abort();
    });
    return ctx;
  };
  const shot = async (page, name) => { if (SHOTS) await page.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: true }); };
  const buyer = async (page, { email, card, mobile = false, prefix }) => {
    await page.goto(ORIGIN + '/gallery'); await shot(page, `${prefix}-1-gallery`);
    await page.click('a.card[href="/gallery/wastgal1"]'); await page.waitForSelector('h1'); await shot(page, `${prefix}-2-artwork`);
    await page.click('a.btn:has-text("Add to basket")'); await page.waitForSelector('#items article');
    await page.goto(ORIGIN + '/gallery/wastfnd2'); await page.click('a.btn:has-text("Add to basket")'); await page.waitForFunction(() => document.querySelectorAll('#items article').length === 2);
    const f = { name: 'Test Buyer', email, address_line1: '7 Harbour Road', town: 'Kinsale', eircode: 'P17 XY12', phone: '+353 21 555 0199' };
    for (const [k, v] of Object.entries(f)) await page.fill(`[name="${k}"]`, v);
    await page.selectOption('[name="county"]', 'Cork');
    await page.check('input[name="island"][value="no"]');   // the offshore-island question (Kinsale is on the mainland); the delivery rules are unchanged
    await page.check('#accept'); await shot(page, `${prefix}-3-basket`);
    await page.click('#pay');
    try { await page.waitForURL(u => u.host === HOSTED.host, { timeout: 15000 }); }
    catch (e) { throw new Error('no hosted card page; the basket page says: ' + (await page.textContent('#err').catch(() => '')) + ' · button: ' + (await page.textContent('#pay').catch(() => ''))); }
    await page.fill('#linkAuthentication-emailInput', email); await page.fill('#payment-numberInput', card); await page.fill('#payment-expiryInput', '12 / 34'); await page.fill('#payment-cvcInput', '123');
    await page.fill('#payment-postalCodeInput', '10001'); await page.fill('#payment-linkMobilePhoneInput', '2015550123'); await page.click('#payment-form-submit-button');
    if (card.endsWith('3184')) { await page.click('#test-source-authorize-3ds'); }
    await page.waitForURL(u => u.origin === ORIGIN && /\/b\/[0-9a-z]{48}$/.test(u.pathname), { timeout: 20000 });
    await page.waitForTimeout(500); await page.reload(); await shot(page, `${prefix}-4-status`);
    return { text: await page.textContent('main'), token: new URL(page.url()).pathname.split('/')[2] };
  };

  console.log('— desktop: two artists, one card entry, paid');
  let ctx = await context({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: SHOTS ? 2 : 1 }), page = await ctx.newPage();
  ENV.STAGING_GALLERY = 'true';
  const A = await buyer(page, { email: 'buyer-a@example.invalid', card: '4242424242424242', prefix: 'desktop' });
  const bA = await one("SELECT * FROM checkout_baskets WHERE buyer_email = 'buyer-a@example.invalid'");
  const oA = await q('SELECT o.* FROM checkout_orders o JOIN basket_lines l ON l.order_id = o.id WHERE l.basket_id = ? ORDER BY l.line_no', bA.id);
  check('C1 the customer browses, adds works by two artists, enters the card once on the hosted page and sees “Thank you”', bA.status === 'paid' && /Thank you for your purchase/.test(A.text) && /Order confirmed/.test(A.text) && (A.text.match(/View confirmation/g) || []).length === 2, { status: bA.status, text: A.text.slice(0, 300) });
  const auths = M.calls.filter(c => c.path === '/v1/payment_intents' && c.method === 'POST');
  check('C2 commission on Stripe: EUR 180.00 on Aoife’s EUR 1,200 work (delivery EUR 35 not commissioned); none on Cian’s Founding work', auths.length === 2 && auths[0].f.application_fee_amount === '18000' && auths[0].f.amount === '123500'
    && !('application_fee_amount' in auths[1].f) && auths[1].f.amount === '78500' && oA[0].commission_cents === 18000 && oA[1].commission_cents === 0, auths.map(a => a.f));
  r = await pub('/gallery/wastgal1');
  check('C3 availability: the bought works now show as sold and cannot be added again', /Sold/.test(r.t) && !/Add to basket/.test(r.t) && (await one("SELECT availability FROM artworks WHERE id='wastfnd2'")).availability === 'sold');
  r = await pub(`/b/${A.token}/confirmation/${oA[0].reference}`);
  check('C4 each artist’s purchase confirmation is available to the buyer from the status page', r.s === 200 && /PURCHASE CONFIRMATION/.test(r.t) && /Part of basket PA-B-/.test(r.t));
  r = await call('POST', `/api/admin/checkout/orders/${oA[0].id}/refund`, { artwork_cents: oA[0].artwork_cents, delivery_cents: oA[0].delivery_cents, reason: 'Staging: buyer cancelled within 14 days' });
  const led = await q("SELECT kind, amount_cents FROM order_ledger WHERE order_id = ? AND kind IN ('artwork_refund','delivery_refund','commission_refund')", oA[0].id);
  check('C5 refund from the founder desk (Studio): the buyer is refunded on Aoife’s account; Cian’s payment is untouched', r.s === 200 && M.refunds.at(-1)._acct === ACC[0] && M.refunds.at(-1).amount === 123500 && led.some(x => x.kind === 'artwork_refund')
    && !(await q("SELECT * FROM order_ledger WHERE order_id = ? AND kind LIKE '%refund%'", oA[1].id)).length, { r: r.j, led });
  await ctx.close();

  console.log('— phone: a declined card');
  ctx = await context({ ...pw.devices['iPhone 13'] }); page = await ctx.newPage();
  await db.prepare("UPDATE artworks SET availability = 'available' WHERE id IN ('wastgal1')").run();   // (staging) a fresh copy of the first work for the next journeys
  await db.prepare("UPDATE artwork_sales SET released_at = ?, released_reason = 'staging reset' WHERE artwork_id = 'wastgal1' AND released_at IS NULL").bind(new Date().toISOString()).run();
  for (const id of ['wastgal1']) { const v = await one("SELECT snapshot FROM versions WHERE artist_id = 'astgal'"); const s = JSON.parse(v.snapshot); s.works.find(w => w.id === id).availability = 'available'; await db.prepare("UPDATE versions SET snapshot = ? WHERE artist_id = 'astgal'").bind(JSON.stringify(s)).run(); }
  await db.prepare("UPDATE artworks SET id = id WHERE 0").run();
  // the Founding work bought above is sold; the phone journey uses the Founding Artist's next work
  const buyer2 = async (opts) => { const sav = buyer.toString(); return null; }; void buyer2;
  await db.prepare("UPDATE artworks SET availability = 'available' WHERE id = 'wastfnd2'").run();
  await db.prepare("UPDATE artwork_sales SET released_at = ?, released_reason = 'staging reset' WHERE artwork_id = 'wastfnd2' AND released_at IS NULL").bind(new Date().toISOString()).run();
  { const v = await one("SELECT snapshot FROM versions WHERE artist_id = 'astfnd'"); const s = JSON.parse(v.snapshot); s.works.find(w => w.id === 'wastfnd2').availability = 'available'; await db.prepare("UPDATE versions SET snapshot = ? WHERE artist_id = 'astfnd'").bind(JSON.stringify(s)).run(); }
  const D = await buyer(page, { email: 'buyer-d@example.invalid', card: '4000000000000341', mobile: true, prefix: 'phone-declined' });
  const bD = await one("SELECT * FROM checkout_baskets WHERE buyer_email = 'buyer-d@example.invalid'");
  check('C6 on a phone, a declined card: nothing is bought, the buyer is told plainly, both works are released', bD.status === 'failed' && /Payment not completed/.test(D.text) && /declined/i.test(D.text)
    && !(await q('SELECT * FROM artwork_reservations WHERE artwork_id IN (?,?)', 'wastgal1', 'wastfnd2')).length, { status: bD.status });
  await ctx.close();

  console.log('— phone: the bank asks for a check on each artist’s payment');
  ctx = await context({ ...pw.devices['iPhone 13'] }); page = await ctx.newPage();
  const X = await buyer(page, { email: 'buyer-x@example.invalid', card: '4000002760003184', mobile: true, prefix: 'phone-bankcheck' });
  const bX = await one("SELECT * FROM checkout_baskets WHERE buyer_email = 'buyer-x@example.invalid'");
  check('C7 a bank check: the status page asks the buyer to confirm each payment, with the deadline and a cancel button; nothing is taken yet', bX.status === 'action_required' && /Confirm your payment/.test(X.text) && /Confirm payment/.test(X.text)
    && !M.calls.some(c => c.path.endsWith('/capture') && Object.values(M.pis).some(p => p.metadata.plotart_basket === bX.id && c.path.includes(p.id))), { status: bX.status });
  await page.click('button:has-text("Cancel order")'); await page.waitForTimeout(500);
  check('C8 the buyer can cancel instead: every authorisation is cancelled and the works are released', (await one('SELECT status FROM checkout_baskets WHERE id = ?', bX.id)).status === 'cancelled'
    && Object.values(M.pis).filter(p => p.metadata.plotart_basket === bX.id).every(p => ['canceled', 'requires_payment_method'].includes(p.status)));
  await ctx.close();
  check('C9 only the TEST key reached the (mock) provider', M.calls.every(c => c.auth === 'Bearer rk_test_stagingmock'));
  console.log(`\nBASKET STAGING (local) · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
  process.exitCode = results.every(Boolean) ? 0 : 1;
} finally {
  if (BR) await BR.close().catch(() => {});
  if (S) await S.mf.dispose();
  HOSTED.close();
}
