// PROVE · founder-only email alerts (PROPOSAL, 18 Nov 2026). LOCAL ONLY: Miniflare, a MOCK Resend API (nothing is sent),
// synthetic data. Checks the mail settings matrix, that artist and buyer messages stay in the test inbox, that repeated
// checks send no duplicate alert, and that a failed delivery is visible in the founder desk.
//   node test/prove-founder-email.mjs
import { writeFileSync } from 'node:fs';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';

const HERE = new URL('..', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${JSON.stringify(d).slice(0, 600)}]` : ''}`); };
const FOUNDER_TO = 'founder-alerts@plotnua.invalid', ARTIST = 'artist@plotnua.invalid', BUYER = 'buyer@plotnua.invalid';
const R = { calls: [], fail: 0, ids: {} };
async function outbound(req) {
  const u = new URL(req.url);
  if (u.hostname === 'api.resend.com') {   // MOCK Resend: records the request; honours Idempotency-Key like Resend
    const body = JSON.parse(await req.text()), idem = req.headers.get('Idempotency-Key');
    R.calls.push({ to: body.to, from: body.from, reply_to: body.reply_to, subject: body.subject, idem });
    if (R.fail > 0) { R.fail--; return new Response(JSON.stringify({ message: 'SIMULATED: Resend unavailable' }), { status: 500 }); }
    if (idem && R.ids[idem]) return new Response(JSON.stringify({ id: R.ids[idem] }), { status: 200 });
    const id = 'em_' + R.calls.length; if (idem) R.ids[idem] = id;
    return new Response(JSON.stringify({ id }), { status: 200 });
  }
  return new Response(JSON.stringify({ error: { message: 'mock: no outbound expected to ' + u.hostname } }), { status: 599 });
}
const MAIL = { CHECKOUT_MAIL: 'resend', CHECKOUT_MAIL_APPROVED: 'true', RESEND_API_KEY: 're_test_mock', CHECKOUT_MAIL_FROM: 'PlotArt payment pilot <studio@plotnua.ie>',
  CHECKOUT_MAIL_TEST_RECIPIENTS: FOUNDER_TO, CHECKOUT_NOTIFY_EMAIL: FOUNDER_TO };
const ENVV = { ...MAIL, CHECKOUT_PILOT_ENABLED: 'true', STRIPE_SECRET_KEY: 'sk_test_mockkey123', STRIPE_WEBHOOK_SECRET: 'whsec_test_' + 'x'.repeat(24), STRIPE_API_BASE: 'https://stripe.mock', CHECKOUT_ORIGIN: 'https://checkout.local' };
let S;
try {
  console.log('PROVE · founder-only email alerts (mock Resend; nothing is sent)');
  S = await start({ port: 8873, env: ENVV, checkout: { script: 'src/checkout-public.js', env: ENVV }, outbound });
  const db = S.db, q = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results;
  const desk = async () => { const r = await S.mf.dispatchFetch(S.url + '/api/admin/checkout', { headers: { 'Cf-Access-Jwt-Assertion': token(FOUNDER), 'X-Studio': '1' } }); return (await r.json()).founder_alerts; };
  await seedPublished(db, { id: 'aem', slug: 'em', email: ARTIST, name: 'Email Test Artist', works: 3, publishedAt: new Date(Date.now() - 30 * 86400_000).toISOString() });
  const CO = await import(HERE + 'src/checkout.js');
  // 1 · the settings matrix, through the pilot's own deliver() (D1 local; Resend mocked through global fetch)
  const realFetch = globalThis.fetch; const NODE = [];
  globalThis.fetch = async (url, init) => { if (String(url).startsWith('https://api.resend.com')) { NODE.push({ to: JSON.parse(init.body).to[0], idem: init.headers['Idempotency-Key'] }); return new Response(JSON.stringify({ id: 'em_node' }), { status: 200 }); } return realFetch(url, init); };
  const base = { DB: db, STRIPE_SECRET_KEY: 'sk_test_mockkey123', ENVIRONMENT: 'local' };
  const d = (env, to, role) => CO.deliver(env, { orderId: null, kind: 'matrix_test', toRole: role, to, subject: 'matrix', body: 'matrix ' + role + ' ' + Object.keys(env).length, idempotencyKey: 'k-' + role });
  const m = {
    not_configured: (await d({ ...base }, FOUNDER_TO, 'founder')).status,
    configured_not_approved: (await d({ ...base, ...MAIL, CHECKOUT_MAIL_APPROVED: 'false' }, FOUNDER_TO, 'founder')).status,
    approved_live_key: (await d({ ...base, ...MAIL, STRIPE_SECRET_KEY: 'sk_live_' + 'x'.repeat(20) }, FOUNDER_TO, 'founder')).status,
    approved_founder: (await d({ ...base, ...MAIL }, FOUNDER_TO, 'founder')).status,
    approved_artist: (await d({ ...base, ...MAIL }, ARTIST, 'artist')).status,
    approved_buyer: (await d({ ...base, ...MAIL }, BUYER, 'buyer')).status,
  };
  globalThis.fetch = realFetch;
  check('E1 settings matrix: nothing is emailed unless Resend is configured, sending is approved and the Stripe key is a test key; even then only the one allow-listed founder address is emailed — artist and buyer messages stay in the test inbox',
    m.not_configured === 'held_in_test_sink' && m.configured_not_approved === 'held_in_test_sink' && m.approved_live_key === 'held_in_test_sink' && m.approved_founder === 'accepted_by_provider'
    && m.approved_artist === 'held_in_test_sink' && m.approved_buyer === 'held_in_test_sink' && NODE.length === 1 && NODE[0].to === FOUNDER_TO, { m, NODE });
  // 2 · a real alert path in the Worker: an amount owed to the artist becomes overdue (SIMULATED dates)
  const mkOrder = async (id, ref, cents, dueAgo) => {
    const t = new Date().toISOString();
    await db.prepare(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, payment_status, artwork_cents, delivery_cents, commission_bp, commission_cents, buyer_email, created_by, created_at, updated_at)
      VALUES (?, ?, 'aem', 'waem1', 'PA-E-261101-AAAAAA', 'paid', 'paid', 10000, 0, 1500, 1500, ?, 'test', ?, ?)`).bind(id, ref, BUYER, t, t).run();
    const due = new Date(Date.now() - dueAgo * 86400_000).toISOString();
    await db.prepare(`INSERT INTO checkout_owed (id, order_id, kind, item_key, cents, reason, arisen_at, due_at, due_rule, due_provisional, due_basis_event, due_basis_at, due_basis_date, due_basis_source)
      VALUES (?, ?, 'processing_shortfall', 'processing', ?, 'SIMULATED shortfall', ?, ?, 'test', 0, 'stripe_fee_recorded', ?, ?, 'stripe')`).bind('w' + id, id, cents, due, due, due, due.slice(0, 10)).run();
  };
  await mkOrder('oem1', 'PA-O-261118-EM0001', 683, 1);
  const sweep = () => S.checkoutWorker.scheduled({ cron: '*/15 * * * *' });
  await sweep(); await sweep(); await sweep();
  const toFounder = R.calls.filter(c => c.to[0] === FOUNDER_TO), toOthers = R.calls.filter(c => c.to[0] !== FOUNDER_TO);
  const artistSink = await q("SELECT kind, to_role, delivery FROM checkout_mail_sink WHERE order_id = 'oem1' AND to_role = 'artist'");
  const fa = await desk(), alert = fa.items.find(x => x.order_id === 'oem1' && x.kind === 'owed_overdue');
  check('E2 one overdue amount: exactly ONE email to the founder (from the proposed sender, reply-to hello@plotnua.ie) after three sweeps; the artist’s overdue notice stays in the test inbox; no email to any artist or buyer address',
    toFounder.length === 1 && toFounder[0].from === MAIL.CHECKOUT_MAIL_FROM && toFounder[0].reply_to[0] === 'hello@plotnua.ie'
    && !toOthers.length && artistSink.length === 1 && artistSink[0].delivery === 'held_in_test_sink', { toFounder, toOthers, artistSink });
  check('E3 the founder desk keeps the emailed alert and shows how the email went (“Emailed to you: accepted by Resend …”), with the amount outstanding and the Irish due date',
    alert && alert.delivery_status === 'accepted_by_provider' && /^Emailed to you: accepted by Resend/.test(alert.delivery) && alert.amount_label === 'EUR 6.83 still owed to the artist' && /OVERDUE/.test(alert.due_label), alert);
  const keys = toFounder.map(c => c.idem);
  check('E4 repeated checks send no duplicate: the alert carries one idempotency key derived from the order, kind, recipient and text, so a retried send of the same alert is not delivered twice by Resend',
    keys.length === 1 && /^plotart-[0-9a-f]{40}$/.test(keys[0]), keys);
  // 3 · a failed delivery (SIMULATED Resend error)
  R.fail = 1;
  await mkOrder('oem2', 'PA-O-261118-EM0002', 450, 1);
  await sweep();
  const fa2 = await desk(), failed = fa2.items.find(x => x.order_id === 'oem2' && x.kind === 'owed_overdue');
  check('E5 SIMULATED failed delivery: Resend refuses the alert; the founder desk shows it as unread with “EMAIL FAILED: …”, so it is not lost',
    failed && failed.delivery_status === 'failed' && /^EMAIL FAILED: mailer 500/.test(failed.delivery) && !failed.read && failed.state === 'open', failed);
  const digest = await CO.founderDigest({ ...ENVV, DB: db });
  writeFileSync('/tmp/plotart-founder-email-samples.json', JSON.stringify({ urgent: (await q("SELECT subject, body FROM checkout_mail_sink WHERE order_id = 'oem1' AND to_role = 'founder' AND kind = 'owed_overdue'"))[0], digest, resend_request: toFounder[0] }, null, 1));
  check('E6 the daily digest sample is generated from the desk (open items, amounts, Irish due dates, pause state) without bank or buyer contact details', !!digest && /daily digest/.test(digest.subject) && /PA-O-261118-EM0001/.test(digest.body) && !/@/.test(digest.body.replace('/admin/checkout', '')), digest);
} catch (e) { console.error(e); results.push(false); }
finally { if (S) await S.mf.dispose(); }
const failedN = results.filter(x => !x).length;
console.log(`\nFOUNDER EMAIL (mock Resend) · ${results.length} checks, ${results.length - failedN} passed, ${failedN} failed`);
process.exit(failedN ? 1 : 0);
