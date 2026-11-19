// FOUNDER EMAIL · one approved SANDBOX test send (phase founder_email; approved by the founder 18 Nov 2026, 11:30).
// The pilot's Workers run in Miniflare inside the GitHub job with sandbox sending switched on for THIS PROCESS ONLY:
//   CHECKOUT_MAIL=resend, CHECKOUT_MAIL_APPROVED=true, CHECKOUT_MAIL_SANDBOX_TEST=true, CHECKOUT_MAIL_FROM = the approved sender,
//   CHECKOUT_MAIL_TEST_RECIPIENTS = CHECKOUT_NOTIFY_EMAIL = the founder's single inbox (GitHub variable), RESEND_API_KEY (secret).
// Synthetic orders only. Exactly two emails to the founder inbox: one urgent alert and one manually triggered digest.
// Artist and buyer messages use .invalid addresses that are NOT on the allowed list. Sending is switched off at the end
// (the test instance is disposed in `finally`, success or failure); nothing about it persists anywhere.
// The recipient address is never written to the evidence: only a short fingerprint.
import { createHash } from 'node:crypto';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';

const SRC = 'resend-sandbox+pilot';
const fp = s => createHash('sha256').update(String(s).trim().toLowerCase()).digest('hex').slice(0, 12);

export async function founderEmail({ rec, KEY, RUN }) {
  const KEYR = process.env.RESEND_API_KEY || '', TO = String(process.env.CHECKOUT_TEST_FOUNDER_EMAIL || '').trim().toLowerCase();
  const FROM = 'PlotArt payment pilot <studio@plotnua.ie>';
  if (!/^re_[A-Za-z0-9_]+$/.test(KEYR) || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(TO) || /\.invalid$/.test(TO)) {
    rec('M0', 'prerequisites: secret RESEND_API_KEY and variable CHECKOUT_TEST_FOUNDER_EMAIL in the checkout-test environment', 'local', 'FAIL',
      { resend_key_present: !!KEYR, resend_key_format_ok: /^re_/.test(KEYR), recipient_present: !!TO, note: 'nothing was sent' });
    return;
  }
  rec('M0', 'prerequisites present (values never printed); recipient fingerprint recorded instead of the address', 'local', 'PASS', { recipient_fingerprint: fp(TO), sender: FROM });
  const MAIL = { CHECKOUT_MAIL: 'resend', CHECKOUT_MAIL_APPROVED: 'true', CHECKOUT_MAIL_SANDBOX_TEST: 'true', RESEND_API_KEY: KEYR, CHECKOUT_MAIL_FROM: FROM,
    CHECKOUT_MAIL_TEST_RECIPIENTS: TO, CHECKOUT_NOTIFY_EMAIL: TO, CHECKOUT_MESSAGE_RETRY_MINUTES: '0' };
  const ENVV = { ...MAIL, CHECKOUT_PILOT_ENABLED: 'true', STRIPE_SECRET_KEY: KEY, STRIPE_WEBHOOK_SECRET: 'whsec_test_' + 'x'.repeat(24), STRIPE_API_BASE: 'https://stripe.invalid', CHECKOUT_ORIGIN: 'https://plotart-checkout-test.invalid' };
  // every outbound request from the Workers: Resend requests recorded (recipient fingerprint, status, Resend id), then passed on
  const SENT = [];
  const outbound = async req => {
    const u = new URL(req.url);
    if (u.hostname !== 'api.resend.com') return new Response('{"error":"no other outbound in this test"}', { status: 599 });
    const raw = await req.text(), b = JSON.parse(raw);
    const item = { to: (b.to || []).map(fp), subject: b.subject, from: b.from, reply_to: b.reply_to, idempotency: req.headers.get('Idempotency-Key') ? 'set' : 'missing' };
    SENT.push(item);
    const r = await fetch(req.url, { method: 'POST', headers: Object.fromEntries(req.headers), body: raw });
    const t = await r.text(); item.http = r.status; try { const j = JSON.parse(t); item.resend_id = j.id || null; item.resend_error = j.message || j.name || null; } catch { item.resend_error = t.slice(0, 200); }
    return new Response(t, { status: r.status, headers: { 'Content-Type': 'application/json' } });
  };
  let S = null;
  try {
    S = await start({ port: 8897, env: ENVV, checkout: { script: 'src/checkout-public.js', env: ENVV }, outbound });
    const db = S.db, q = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results;
    const api = async (method, path, body) => { const r = await S.mf.dispatchFetch(S.url + path, { method, headers: { 'Cf-Access-Jwt-Assertion': token(FOUNDER), 'X-Studio': '1', 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined }); return { s: r.status, j: await r.json().catch(() => null) }; };
    const ARTIST = `artist+${RUN}@plotnua.invalid`, BUYER = `buyer+${RUN}@plotnua.invalid`;
    await seedPublished(db, { id: 'amt', slug: 'mt', email: ARTIST, name: 'SANDBOX Test Artist', works: 1, publishedAt: new Date(Date.now() - 30 * 86400_000).toISOString() });
    const t = new Date().toISOString(), due = new Date(Date.now() - 86400_000).toISOString();
    await db.prepare(`INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, payment_status, artwork_cents, delivery_cents, commission_bp, commission_cents, buyer_email, created_by, created_at, updated_at)
      VALUES ('omt1', 'PA-O-261118-SBX001', 'amt', 'wamt1', 'PA-E-261101-AAAAAA', 'paid', 'paid', 10000, 0, 1500, 1500, ?, 'sandbox-test', ?, ?)`).bind(BUYER, t, t).run();
    await db.prepare(`INSERT INTO checkout_owed (id, order_id, kind, item_key, cents, reason, arisen_at, due_at, due_rule, due_provisional, due_basis_event, due_basis_at, due_basis_date, due_basis_source)
      VALUES ('wmt1', 'omt1', 'processing_shortfall', 'processing', 683, 'SANDBOX TEST: simulated shortfall', ?, ?, 'SANDBOX TEST', 0, 'stripe_fee_recorded', ?, ?, 'stripe')`).bind(due, due, due, due.slice(0, 10)).run();
    await db.prepare(`INSERT INTO order_messages (id, order_id, kind, item_key, recipient_role, subject, body, sha256, created_at) VALUES ('mmt1', 'omt1', 'buyer_refund_pending', 'sbx', 'buyer', 'SANDBOX TEST buyer message', 'SANDBOX TEST: simulated buyer notice.', ?, ?)`)
      .bind(createHash('sha256').update('SANDBOX TEST: simulated buyer notice.').digest('hex'), t).run();
    const CW = S.checkoutWorker, sweep = () => CW.scheduled({ cron: '*/15 * * * *' });
    // urgent alert: the overdue amount (three checks in a row)
    await sweep(); await sweep(); await sweep();
    const afterSweeps = SENT.length;
    // the digest, triggered once by hand
    const dg = await api('POST', '/api/admin/checkout/digest/send');
    // repeated checks afterwards
    await sweep(); await sweep();
    const toFounder = SENT.filter(x => x.to.length === 1 && x.to[0] === fp(TO)), toOthers = SENT.filter(x => !(x.to.length === 1 && x.to[0] === fp(TO)));
    const urgent = toFounder.find(x => /URGENT/.test(x.subject)), digest = toFounder.find(x => /daily digest/.test(x.subject));
    rec('M1', 'Resend ACCEPTANCE (not inbox receipt): exactly two requests to the approved inbox — one urgent alert after three checks, one manually triggered digest — both accepted by Resend (HTTP 200 with an email id), both subjects marked “SANDBOX TEST”, from the approved sender with reply-to hello@plotnua.ie', SRC,
      toFounder.length === 2 && urgent && digest && afterSweeps === 1 && toFounder.every(x => x.http === 200 && x.resend_id && /^SANDBOX TEST · /.test(x.subject) && x.from === FROM && (x.reply_to || [])[0] === 'hello@plotnua.ie' && x.idempotency === 'set') && dg.s === 200 ? 'PASS' : 'FAIL',
      { requests_to_founder: toFounder.map(x => ({ subject: x.subject, http: x.http, resend_id: x.resend_id, error: x.resend_error })), digest_api: dg.j, requests_after_three_checks: afterSweeps });
    const artistSink = await q("SELECT kind, delivery FROM checkout_mail_sink WHERE order_id = 'omt1' AND to_role = 'artist'");
    const buyerDel = await q("SELECT status, channel FROM order_message_deliveries WHERE message_id = 'mmt1'");
    rec('M2', 'artist and buyer messages stay in the test inbox: the artist’s overdue notice and a buyer message are held in the test inbox and no Resend request was made for any address other than the approved inbox', SRC,
      !toOthers.length && artistSink.length >= 1 && artistSink.every(x => x.delivery === 'held_in_test_sink') && buyerDel.length >= 1 && buyerDel.every(x => x.status === 'held_in_test_sink') ? 'PASS' : 'FAIL',
      { resend_requests_to_other_addresses: toOthers.length, artist: artistSink, buyer: buyerDel });
    rec('M3', 'repeated checks produce no additional sends: after the first send, two more checks and the digest left the founder at exactly two emails', SRC,
      toFounder.length === 2 && SENT.length === 2 ? 'PASS' : 'FAIL', { total_resend_requests: SENT.length });
    const fa = (await api('GET', '/api/admin/checkout')).j.founder_alerts;
    const aU = fa.items.find(x => x.kind === 'owed_overdue' && x.order_id === 'omt1'), aD = fa.items.find(x => x.kind === 'founder_digest');
    rec('M4', 'the founder desk records the outcome of both emails (“Emailed to you: accepted by Resend …”), with the urgent alert’s simulated amount and due date', SRC,
      aU && aU.delivery_status === 'accepted_by_provider' && aD && aD.delivery_status === 'accepted_by_provider' && aU.amount_label === 'EUR 6.83 still owed to the artist' ? 'PASS' : 'FAIL',
      { urgent: aU && { delivery: aU.delivery, amount: aU.amount_label, due: aU.due_label }, digest: aD && { delivery: aD.delivery } });
    rec('M5', 'inbox RECEIPT of both messages', 'founder', 'INFO', { to_be_confirmed_by: 'the founder', expect: ['SANDBOX TEST · PlotArt payment pilot · URGENT · PA-O-261118-SBX001 · Amount owed to the artist is overdue', 'SANDBOX TEST · PlotArt payment pilot · daily digest · …'] });
  } catch (e) {
    rec('M9', 'founder email test run', SRC, 'FAIL', { error: String(e.message).slice(0, 300), resend_requests_so_far: SENT.length });
  } finally {
    if (S) await S.mf.dispose().catch(() => {});
    rec('M6', 'sandbox sending switched off at the end of the run (success or failure): the test Workers are stopped; the mail settings existed only in this process; no deployed configuration was changed', 'local', S ? 'PASS' : 'INFO',
      { instance_disposed: !!S, resend_requests_total: SENT.length });
  }
}
