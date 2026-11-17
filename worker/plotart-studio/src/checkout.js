/* PlotArt · managed checkout pilot · core (development 16 Nov 2026). NOT DEPLOYED. TEST MODE ONLY. OFF BY DEFAULT.
   Shared by the Studio Worker (founder desk and artist panel, behind Cloudflare Access) and the public checkout Worker
   (buyer quote page, hosted-checkout start, provider webhook). It never writes versions, submissions, publish_queue,
   gallery_positions, founding numbers, agreement tables or the enquiry log. The only existing row it touches is the
   artwork's own availability in the Studio working copy, set to 'sold' when a VERIFIED payment completes a sale; that
   change is published, like any sold mark, only through the normal Studio publishing path (nothing is dispatched here).

   Order flow: founder creates a draft from a logged enquiry → founder enters price, delivery and cover → artist confirms
   availability, condition, framing, dimensions and packing, and approves that exact quote version → founder issues a
   time-limited quote (buyer link) → buyer reads the seller, charges and terms and opens hosted checkout (the work is
   reserved atomically) → only a signed provider event marks the order paid and the work sold → dispatch and delivery
   evidence → close. Refunds and disputes are booked in an append-only ledger. */
import * as R from './checkout-rules.js';
import * as S from './stripe.js';
import { PAYMENT_TERMS } from './payment-terms.js';
import { send } from './mailer.js';

import { Bad } from './lib.js';
export { Bad };
const now = () => new Date().toISOString();
const rid = (p = '', n = 12) => p + [...crypto.getRandomValues(new Uint8Array(n))].map(b => (b % 36).toString(36)).join('');
const all = async (env, sql, ...b) => (await env.DB.prepare(sql).bind(...b).all()).results;
const one = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).first();
const run = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).run();
const st = (env, sql, ...b) => env.DB.prepare(sql).bind(...b);
const J = s => (s ? JSON.parse(s) : null);
const sha256 = async s => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)))].map(b => b.toString(16).padStart(2, '0')).join('');
const addMin = (iso, m) => new Date(Date.parse(iso) + m * 60_000).toISOString();

export const STATEMENT = doc => `I have read and accept the PlotArt Payment Pilot Addendum ${doc}. I understand that taking part is optional, that I remain the seller of my artwork, that payments are made to my own Stripe account, that Stripe deducts its processing fees from my Stripe balance, that PlotArt's commission (if any) applies only as my existing agreement provides and never to delivery charges, and that I can leave the pilot at any time.`;

/* Separate, explicit consent to the processing charge (founder decision 16 Nov 2026). On an order where PlotArt takes no
   commission (every Founding Enquiry, and Founding Artists without commission terms), Stripe's processing fees would be
   the only deduction and would fall on the artist. Direct payment, with no deduction at all, stays the artist's normal
   route; the pilot can be used for such an order only after this separate, withdrawable consent. It is never implied by
   joining the pilot, and never part of any agreement acceptance. */
export const PROCESSING_STATEMENT = `I agree that, on payment-pilot orders where PlotArt takes no commission, Stripe deducts its card processing fees from my Stripe balance (for example about 1.5% + €0.25 of the amount paid for a standard EEA card, more for premium, UK and international cards). I understand this is optional: I can always sell directly instead, with no deduction at all, and I can withdraw this consent at any time.`;

/* ---------------------------------------------------------------- switches */
export async function installed(env) { try { await env.DB.prepare('SELECT 1 FROM checkout_orders LIMIT 1').all(); return true; } catch { return false; } }
export function switches(env) {
  const key = S.testKey(env);
  return { enabled: env.CHECKOUT_PILOT_ENABLED === 'true' && key.ok, flag: env.CHECKOUT_PILOT_ENABLED === 'true', test_key: key.ok, key_problem: key.ok ? null : key.reason,
    webhook_secret: String(env.STRIPE_WEBHOOK_SECRET || '').startsWith('whsec_'), checkout_origin: env.CHECKOUT_ORIGIN || null, mode: 'test' };
}
function requireOn(env) {
  const s = switches(env);
  if (!s.flag) throw new Bad('The payment pilot is switched off', 503);
  if (!s.test_key) throw new Bad(`The payment pilot is not configured: ${s.key_problem}`, 503);
  if (!env.CHECKOUT_ORIGIN) throw new Bad('The payment pilot is not configured: CHECKOUT_ORIGIN', 503);
}
async function requireInstalled(env) { if (!(await installed(env))) throw new Bad('The payment pilot is not installed (migration 0016)', 409); }

/* An installed text whose fingerprint matches the text bundled with the Worker. */
export async function currentTerms(env, kind) {
  const d = await one(env, 'SELECT * FROM payment_terms WHERE kind = ? AND effective_at <= ? ORDER BY effective_at DESC LIMIT 1', kind, now());
  const t = d && PAYMENT_TERMS[d.doc_id];
  return d && t && t.html_sha256 === d.html_sha256 ? { ...d, html: t.html } : null;
}

/* ---------------------------------------------------------------- audit and status moves */
async function event(env, orderId, actor, action, prior, next, detail) {
  await run(env, 'INSERT INTO order_events (order_id, at, actor, action, prior_status, new_status, detail) VALUES (?,?,?,?,?,?,?)',
    orderId, now(), actor, action, prior || null, next || null, detail ? JSON.stringify(detail).slice(0, 4000) : null);
}
const evSt = (env, orderId, actor, action, prior, next, detail) => st(env, 'INSERT INTO order_events (order_id, at, actor, action, prior_status, new_status, detail) VALUES (?,?,?,?,?,?,?)',
  orderId, now(), actor, action, prior || null, next || null, detail ? JSON.stringify(detail).slice(0, 4000) : null);
/* Optimistic: the row moves only if it is still in the status we read. */
async function move(env, order, to, actor, action, sets = {}, detail = null) {
  if (!R.canMove(order.status, to)) throw new Bad(`An order that is ${order.status.replace('_', ' ')} cannot become ${to.replace('_', ' ')}`, 409);
  const keys = Object.keys(sets);
  const r = await run(env, `UPDATE checkout_orders SET status = ?, ${keys.map(k => `${k} = ?, `).join('')}updated_at = ? WHERE id = ? AND status = ?`,
    to, ...keys.map(k => sets[k]), now(), order.id, order.status);
  if (!r.meta.changes) throw new Bad('This order changed meanwhile. Reload and try again.', 409);
  await event(env, order.id, actor, action, order.status, to, detail);
  return { ...order, ...sets, status: to };
}
export const getOrder = (env, id) => one(env, 'SELECT * FROM checkout_orders WHERE id = ?', id);

/* ---------------------------------------------------------------- artist pilot membership */
export async function membership(env, artistId) {
  const ev = await one(env, "SELECT * FROM payment_pilot_events WHERE artist_id = ? AND kind IN ('opted_in', 'left') ORDER BY at DESC, rowid DESC LIMIT 1", artistId);
  const pc = await one(env, "SELECT * FROM payment_pilot_events WHERE artist_id = ? AND kind IN ('processing_consent', 'processing_consent_withdrawn') ORDER BY at DESC, rowid DESC LIMIT 1", artistId);
  const acct = await one(env, 'SELECT * FROM payment_accounts WHERE artist_id = ?', artistId);
  const opted = !!ev && ev.kind === 'opted_in';
  const ready = !!acct && acct.charges_enabled === 1 && acct.details_submitted === 1;
  return { opted_in: opted, addendum: opted ? ev.doc_id : null, opted_in_at: opted ? ev.at : null,
    processing_consent: opted && !!pc && pc.kind === 'processing_consent', processing_consent_at: pc && pc.kind === 'processing_consent' ? pc.at : null, account: acct ? { id: acct.account_id, country: acct.country,
    charges_enabled: !!acct.charges_enabled, payouts_enabled: !!acct.payouts_enabled, details_submitted: !!acct.details_submitted,
    requirements_due: J(acct.requirements_due) || [], checked_at: acct.checked_at } : null, ready: opted && ready };
}

export async function artistView(env, artist) {
  if (!(await installed(env))) return { installed: false };
  const sw = switches(env), add = await currentTerms(env, 'artist_payment_addendum');
  return { installed: true, switches: { enabled: sw.enabled, mode: 'test' }, membership: await membership(env, artist.id),
    addendum: add ? { doc_id: add.doc_id, title: add.title, html_sha256: add.html_sha256, statement: STATEMENT(add.doc_id) } : null,
    processing_statement: PROCESSING_STATEMENT, direct_payment_note: 'Selling directly, with the buyer paying you, remains your normal route. The payment pilot is optional for every sale.',
    pending_refunds: (await pendingRefunds(env, artist.id)).map(r => ({ ...r, what_to_do: REFUND_FUNDING_STEPS })),
    orders: (await all(env, 'SELECT * FROM checkout_orders WHERE artist_id = ? ORDER BY created_at DESC LIMIT 100', artist.id)).map(o => orderView(o, 'artist')) };
}

export async function optIn(env, artist, body) {
  await requireInstalled(env); requireOn(env);
  const add = await currentTerms(env, 'artist_payment_addendum');
  if (!add) throw new Bad('The payment addendum has not been issued yet', 409);
  if (!body || body.accept !== true || body.doc_id !== add.doc_id || body.html_sha256 !== add.html_sha256) throw new Bad('Tick the box to accept the addendum shown', 400);
  if (artist.account_status !== 'active') throw new Bad('Only an active Studio account can join the pilot', 409);
  const m = await membership(env, artist.id);
  if (m.opted_in && m.addendum === add.doc_id) return { already: true, membership: m };
  await run(env, `INSERT INTO payment_pilot_events (id, artist_id, kind, doc_id, doc_sha256, account_email, display_name, statement, at) VALUES (?,?, 'opted_in', ?,?,?,?,?,?)`,
    rid('pe'), artist.id, add.doc_id, add.html_sha256, artist.email, artist.display_name, STATEMENT(add.doc_id), now());
  return { membership: await membership(env, artist.id) };
}

export async function processingConsent(env, artist, body) {
  await requireInstalled(env); requireOn(env);
  const m = await membership(env, artist.id);
  if (!m.opted_in) throw new Bad('Join the payment pilot first', 409);
  if (!body || body.accept !== true || body.statement !== PROCESSING_STATEMENT) throw new Bad('Tick the box beside the statement shown to give this separate consent', 400);
  if (m.processing_consent) return { already: true, membership: m };
  await run(env, `INSERT INTO payment_pilot_events (id, artist_id, kind, account_email, display_name, statement, at) VALUES (?,?, 'processing_consent', ?,?,?,?)`,
    rid('pe'), artist.id, artist.email, artist.display_name, PROCESSING_STATEMENT, now());
  return { membership: await membership(env, artist.id) };
}
/* Withdrawing stops any commission-free order from being paid through the pilot: unpaid ones are cancelled (paid ones finish). */
export async function withdrawProcessingConsent(env, artist) {
  await requireInstalled(env);
  const m = await membership(env, artist.id);
  if (!m.processing_consent) return { membership: m };
  const open = await all(env, `SELECT * FROM checkout_orders WHERE artist_id = ? AND commission_bp = 0 AND status IN ('awaiting_artist','quoted','checkout_open','payment_failed')`, artist.id);
  for (const o of open) await cancelOrder(env, o, 'artist:' + artist.email, 'Artist withdrew consent to the processing charge');
  await run(env, `INSERT INTO payment_pilot_events (id, artist_id, kind, account_email, display_name, at) VALUES (?,?, 'processing_consent_withdrawn', ?,?,?)`, rid('pe'), artist.id, artist.email, artist.display_name, now());
  return { membership: await membership(env, artist.id), cancelled: open.map(o => o.reference) };
}
function requireProcessingConsent(mem, commissionBp) {
  if (commissionBp === 0 && !mem.processing_consent)
    throw new Bad('PlotArt takes no commission on this order, so Stripe’s processing fees would be the artist’s only deduction. That needs the artist’s separate consent (Payment pilot page); otherwise the artist sells directly, with no deduction.', 409);
}

export async function leave(env, artist) {
  await requireInstalled(env);
  const m = await membership(env, artist.id);
  if (!m.opted_in) return { membership: m };
  const open = await all(env, `SELECT * FROM checkout_orders WHERE artist_id = ? AND status IN ('draft','awaiting_artist','quoted','checkout_open','payment_failed')`, artist.id);
  for (const o of open) await cancelOrder(env, o, 'artist:' + artist.email, 'Artist left the payment pilot');   // paid orders continue to completion
  await run(env, `INSERT INTO payment_pilot_events (id, artist_id, kind, account_email, at) VALUES (?,?, 'left', ?, ?)`, rid('pe'), artist.id, artist.email, now());
  return { membership: await membership(env, artist.id), cancelled: open.map(o => o.reference) };
}

/* Stripe-hosted onboarding: the artist's own account, then a one-time onboarding link. */
export async function onboarding(env, artist, origin, body = {}) {
  await requireInstalled(env); requireOn(env);
  const m = await membership(env, artist.id);
  if (!m.opted_in) throw new Bad('Join the payment pilot first', 409);
  let acct = await one(env, 'SELECT * FROM payment_accounts WHERE artist_id = ?', artist.id);
  if (!acct) {
    const country = (body.country || 'IE').toUpperCase();
    if (!['IE', 'GB'].includes(country)) throw new Bad('The pilot supports artists in Ireland and Northern Ireland', 400);
    const a = await S.createAccount(env, { email: artist.email, country, artistId: artist.id });
    const bad = S.accountConfigProblems(a);
    if (bad.length) throw new Bad('Stripe created the account with a configuration the pilot does not allow: ' + bad.join('; '), 502);
    await run(env, 'INSERT INTO payment_accounts (artist_id, account_id, country, created_at, updated_at) VALUES (?,?,?,?,?)', artist.id, a.id, country, now(), now());
    acct = await one(env, 'SELECT * FROM payment_accounts WHERE artist_id = ?', artist.id);
  }
  const link = await S.accountLink(env, { account: acct.account_id, refreshUrl: `${origin}/checkout-pilot?onboarding=refresh`, returnUrl: `${origin}/checkout-pilot?onboarding=return` });
  return { url: link.url, account: acct.account_id };
}
export async function applyAccount(env, a) {
  const due = [...new Set([...((a.requirements && a.requirements.currently_due) || []), ...((a.requirements && a.requirements.past_due) || [])])].slice(0, 40);
  await run(env, `UPDATE payment_accounts SET charges_enabled = ?, payouts_enabled = ?, details_submitted = ?, requirements_due = ?, checked_at = ?, updated_at = ? WHERE account_id = ?`,
    a.charges_enabled ? 1 : 0, a.payouts_enabled ? 1 : 0, a.details_submitted ? 1 : 0, JSON.stringify(due), now(), now(), a.id);
}
export async function refreshAccount(env, artistId) {
  await requireInstalled(env);
  const acct = await one(env, 'SELECT * FROM payment_accounts WHERE artist_id = ?', artistId);
  if (!acct) throw new Bad('No payment account yet', 404);
  const bad = S.accountConfigProblems(await S.getAccountV2(env, acct.account_id));
  if (bad.length) throw new Bad('This Stripe account does not have the pilot configuration: ' + bad.join('; '), 409);
  await applyAccount(env, await S.getAccount(env, acct.account_id));
  return { membership: await membership(env, artistId) };
}

/* ---------------------------------------------------------------- orders: what each party may see */
export function orderView(o, role) {
  const v = { id: o.id, reference: o.reference, status: o.status, payment_status: o.payment_status, fulfilment_status: o.fulfilment_status, dispute_status: o.dispute_status,
    needs_resolution: o.needs_resolution, artwork_id: o.artwork_id, enquiry_ref: o.enquiry_ref, currency: o.currency,
    artwork_cents: o.artwork_cents, delivery_cents: o.delivery_cents, total_cents: o.artwork_cents == null ? null : o.artwork_cents + (o.delivery_cents || 0),
    commission_bp: o.commission_bp, commission_cents: o.commission_cents, commission_basis: o.commission_basis,
    artist_artwork_cents: o.commission_cents == null ? null : o.artwork_cents - o.commission_cents,
    delivery: J(o.delivery), artwork: J(o.artwork_snapshot), seller: J(o.seller), quote_version: o.quote_version,
    artist_approved_version: o.artist_approved_version, artist_approved_at: o.artist_approved_at, quote_expires_at: o.quote_expires_at,
    paid_at: o.paid_at, created_at: o.created_at, updated_at: o.updated_at, processing_fees: 'Deducted by Stripe from the seller’s Stripe balance; not PlotArt commission; not included above.' };
  if (role === 'founder') Object.assign(v, { artist_id: o.artist_id, entitlement: J(o.entitlement), exclusion: o.exclusion, negotiation_note: o.negotiation_note,
    buyer_email: o.buyer_email, provider_account: o.provider_account, payment_intent: o.payment_intent, charge_id: o.charge_id, application_fee_id: o.application_fee_id });
  return v;
}
export async function orderDetail(env, o, role) {
  return { order: orderView(o, role), events: await all(env, 'SELECT at, actor, action, prior_status, new_status, detail FROM order_events WHERE order_id = ? ORDER BY id', o.id),
    ledger: await all(env, 'SELECT kind, amount_cents, provider_ref, at, note FROM order_ledger WHERE order_id = ? ORDER BY at, rowid', o.id),
    fulfilment: await all(env, 'SELECT kind, actor, at, evidence FROM order_fulfilment_events WHERE order_id = ? ORDER BY at, rowid', o.id),
    refunds: await all(env, 'SELECT id, artwork_cents, delivery_cents, commission_refund_cents, reason, status, error, created_at FROM order_refunds WHERE order_id = ? ORDER BY created_at', o.id),
    sessions: role === 'founder' ? await all(env, 'SELECT id, quote_version, amount_total, application_fee_cents, status, expires_at, created_at FROM checkout_sessions WHERE order_id = ? ORDER BY created_at', o.id) : undefined };
}
export async function adminView(env) {
  if (!(await installed(env))) return { installed: false, switches: switches(env) };
  const artists = await all(env, `SELECT a.id, a.display_name, a.slug, a.founding, p.account_id, p.charges_enabled, p.payouts_enabled, p.details_submitted
    FROM artists a JOIN (SELECT artist_id FROM payment_pilot_events GROUP BY artist_id) e ON e.artist_id = a.id LEFT JOIN payment_accounts p ON p.artist_id = a.id ORDER BY a.display_name`);
  for (const a of artists) a.membership = await membership(env, a.id);
  return { installed: true, switches: switches(env), addendum: await currentTerms(env, 'artist_payment_addendum').then(d => d && d.doc_id),
    buyer_terms: await currentTerms(env, 'buyer_purchase_terms').then(d => d && d.doc_id), artists,
    orders: (await all(env, 'SELECT * FROM checkout_orders ORDER BY created_at DESC LIMIT 200')).map(o => orderView(o, 'founder')),
    unprocessed_events: await all(env, "SELECT event_id, type, status, attempts, detail, received_at FROM payment_events WHERE status IN ('deferred','failed','received') ORDER BY received_at LIMIT 50"),
    pending_refunds: await pendingRefunds(env), holds: await holdsView(env), refund_funding_steps: REFUND_FUNDING_STEPS };
}

/* ---------------------------------------------------------------- refunds waiting for the artist's Stripe balance
   Stripe holds a card refund as pending while the artist's AVAILABLE Stripe balance cannot cover it (typically after a
   payout) and fails it after 45 days. PlotArt flags it at once, tells the artist and the founder, re-checks it with Stripe
   on every sweep (so a missed webhook cannot leave it stale), and escalates as the deadline approaches. */
export const REFUND_PENDING_DAYS = 45;
export const REFUND_FUNDING_STEPS = [
  'Stripe will complete the refund by itself as soon as your Stripe balance can cover it (for example from your next sale), and may debit the bank account linked to your Stripe account to bring a negative balance back up.',
  'To complete it now, add funds to your Stripe balance: Stripe Dashboard → Balances → Add to balance (bank transfer). The refund is released when the funds arrive.',
  'If the refund cannot be funded before Stripe’s 45-day limit, Stripe cancels it. You then repay the buyer directly (for example by bank transfer) and send PlotArt the confirmation, so the order can be settled. Do not repay the buyer outside Stripe while a Stripe refund is still pending: they could be repaid twice.',
  'PlotArt returns its share of commission only after the buyer has actually been repaid.',
];
async function pendingRefunds(env, artistId = null) {
  const rows = await all(env, `SELECT r.id, r.order_id, o.reference, o.artist_id, r.artwork_cents + r.delivery_cents AS amount_cents, r.provider_refund_id, r.created_at
    FROM order_refunds r JOIN checkout_orders o ON o.id = r.order_id WHERE r.status = 'pending' AND (? IS NULL OR o.artist_id = ?) ORDER BY r.created_at`, artistId, artistId);
  return rows.map(r => { const age = Math.floor((Date.now() - Date.parse(r.created_at)) / 86400_000);
    return { ...r, days_pending: age, stripe_fails_it_by: new Date(Date.parse(r.created_at) + REFUND_PENDING_DAYS * 86400_000).toISOString().slice(0, 10),
      urgency: age >= 30 ? 'urgent' : age >= 7 ? 'overdue' : 'new' }; });
}
async function notify(env, o, kind, text) {
  const artist = await one(env, 'SELECT email, display_name FROM artists WHERE id = ?', o.artist_id);
  const to = [artist && artist.email, env.CHECKOUT_NOTIFY_EMAIL].filter(Boolean);
  const out = [];
  for (const addr of to) {
    try { out.push((await send(env, { to: addr, subject: `PlotArt payment pilot · ${o.reference} · ${kind}`, text, idempotencyKey: `${o.id}-${kind}-${addr}` })).detail); }
    catch (e) { out.push('error'); }
  }
  await event(env, o.id, 'system', 'notified_' + kind, o.status, o.status, { recipients: to.length, result: out });
}
/* Re-check every pending refund with Stripe (sweep). */
export async function pollPendingRefunds(env) {
  let checked = 0, completed = 0, failed = 0, escalated = 0;
  for (const p of await pendingRefunds(env)) {
    const rr = await one(env, 'SELECT * FROM order_refunds WHERE id = ?', p.id), o = await getOrder(env, p.order_id);
    if (rr.provider_refund_id) {
      try {
        const re = await S.getRefund(env, { account: o.provider_account, id: rr.provider_refund_id }); checked++;
        if (re.status === 'succeeded') { await completeRefund(env, 'sweep', rr); completed++; continue; }
        if (['failed', 'canceled'].includes(re.status)) { await failRefund(env, rr, re); failed++; continue; }
      } catch { /* Stripe unreachable: try again next sweep */ }
    }
    for (const [days, level] of [[7, 'overdue'], [30, 'urgent']]) {
      if (p.days_pending >= days && !(await one(env, "SELECT 1 AS x FROM order_events WHERE order_id = ? AND action = ?", o.id, `notified_refund_pending_${level}`))) {
        await notify(env, o, `refund_pending_${level}`, `A refund of EUR ${(p.amount_cents / 100).toFixed(2)} on PlotArt order ${o.reference} has been waiting ${p.days_pending} days for the seller's Stripe balance. Stripe will cancel it on ${p.stripe_fails_it_by} if it is still unfunded.\n\n${REFUND_FUNDING_STEPS.join('\n')}`);
        await run(env, 'UPDATE checkout_orders SET needs_resolution = ?, updated_at = ? WHERE id = ?',
          `${level.toUpperCase()}: refund ${rr.provider_refund_id} pending ${p.days_pending} days; Stripe cancels it on ${p.stripe_fails_it_by}. Contact the artist about adding funds.`, now(), o.id);
        escalated++;
      }
    }
  }
  return { refunds_checked: checked, refunds_completed: completed, refunds_failed: failed, refunds_escalated: escalated };
}
/* After a Stripe refund has FAILED (or was never possible), the artist may repay the buyer directly. The founder records it
   with evidence; it is booked as an external repayment and PlotArt returns its commission share exactly as for a refund. */
export async function recordExternalRepayment(env, founder, id, b) {
  await requireInstalled(env);
  const o = await getOrder(env, id);
  if (!o || !o.payment_intent) throw new Bad('Not found', 404);
  if (await one(env, "SELECT 1 AS x FROM order_refunds WHERE order_id = ? AND status = 'pending'", o.id))
    throw new Bad('A Stripe refund is still pending on this order. Wait until it succeeds or fails, so the buyer is never repaid twice.', 409);
  const art = b.artwork_cents ?? 0, del = b.delivery_cents ?? 0, evidence = String(b.evidence || '').trim();
  if (!Number.isInteger(art) || !Number.isInteger(del) || art < 0 || del < 0 || art + del === 0) throw new Bad('Give the amounts in whole cents');
  if (evidence.length < 10) throw new Bad('Describe the evidence (bank transfer reference, date, and the buyer’s confirmation)');
  const tot = await refundTotals(env, o.id);
  if (tot.art + art > o.artwork_cents || tot.del + del > o.delivery_cents) throw new Bad('That is more than remains unrefunded', 409);
  const fee = R.commissionRefund({ artwork_cents: o.artwork_cents, commission_cents: o.commission_cents, artwork_refunded_before: tot.art, artwork_refund_now: art, commission_refunded_before: tot.fee });
  const ref = 'ext_' + rid('', 10);
  await env.DB.batch([
    st(env, `INSERT INTO order_refunds (id, order_id, artwork_cents, delivery_cents, commission_refund_cents, reason, status, provider_refund_id, requested_by, created_at, updated_at) VALUES (?,?,?,?,?,?, 'succeeded', ?, ?,?,?)`,
      rid('rf'), o.id, art, del, fee, ('Repaid by the artist outside Stripe: ' + evidence).slice(0, 500), ref, founder, now(), now()),
    ...(art ? [ledgerSt(env, o.id, 'artwork_refund', -art, ref, 'repaid by the artist outside Stripe')] : []),
    ...(del ? [ledgerSt(env, o.id, 'delivery_refund', -del, ref, 'repaid by the artist outside Stripe')] : []),
    st(env, "UPDATE checkout_orders SET needs_resolution = NULL, updated_at = ? WHERE id = ? AND (needs_resolution LIKE '%failed%' OR needs_resolution LIKE '%pending%')", now(), o.id),
    evSt(env, o.id, founder, 'external_repayment_recorded', o.status, o.status, { art, del, evidence: evidence.slice(0, 300) }),
  ]);
  const row = await one(env, 'SELECT * FROM order_refunds WHERE provider_refund_id = ?', ref);
  if (fee > 0) await feeRefund(env, founder, await getOrder(env, o.id), { fee, reason: 'commission share on an external repayment', refundId: row.id, providerRefund: ref });
  return settleAfterRefund(env, founder, o.id);
}

/* ---------------------------------------------------------------- founder: create and edit */
async function publishedWork(env, artistId, artworkId) {
  const q = await one(env, "SELECT version FROM publish_queue WHERE artist_id = ? AND status = 'published' ORDER BY version DESC LIMIT 1", artistId);
  if (!q) return null;
  const v = await one(env, 'SELECT snapshot FROM versions WHERE artist_id = ? AND version = ?', artistId, q.version);
  return v ? (JSON.parse(v.snapshot).works || []).find(w => w.id === artworkId) || null : null;
}
/* The work must be the artist's, published, available in the gallery AND in the Studio working copy (where the artist
   records an outside sale), not archived, and not already sold through the pilot. */
async function workAvailable(env, artistId, artworkId) {
  const w = await one(env, 'SELECT * FROM artworks WHERE id = ? AND artist_id = ?', artworkId, artistId);
  if (!w) throw new Bad('That artwork is not this artist’s', 404);
  if (w.archived) throw new Bad('That artwork is withdrawn', 409);
  if (w.availability !== 'available') throw new Bad(`That artwork is marked ${w.availability.replace(/_/g, ' ')} in the artist’s Studio`, 409);
  const pw = await publishedWork(env, artistId, artworkId);
  if (!pw || pw.availability !== 'available') throw new Bad('That artwork is not published as available', 409);
  if (await one(env, 'SELECT 1 AS x FROM artwork_sales WHERE artwork_id = ? AND released_at IS NULL', artworkId)) throw new Bad('That artwork has already been sold through the pilot', 409);
  return w;
}

export async function createOrder(env, founder, b) {
  await requireInstalled(env); requireOn(env);
  const artist = await one(env, 'SELECT * FROM artists WHERE id = ?', String(b.artist_id || ''));
  if (!artist || artist.account_status !== 'active') throw new Bad('Choose an active artist', 404);
  if (!(await membership(env, artist.id)).opted_in) throw new Bad('This artist has not opted in to the payment pilot', 409);
  const w = await workAvailable(env, artist.id, String(b.artwork_id || ''));
  const ref = String(b.enquiry_ref || '').trim();
  if (!/^PA-(E|EM|H)-[0-9A-Z-]{6,30}$/.test(ref)) throw new Bad('Give the enquiry reference (PA-E-… or PA-EM-…)', 400);
  if (ref.startsWith('PA-H-')) throw new Bad('Art for Hire enquiries are not part of the payment pilot', 409);
  if (!(await one(env, 'SELECT 1 AS x FROM enquiry_log WHERE reference = ? AND artist_id = ?', ref, artist.id))) throw new Bad('No PlotArt introduction is logged under that reference for this artist. Log the enquiry first.', 409);
  const email = String(b.buyer_email || '').trim();
  if (!/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}$/.test(email) || email.length > 254) throw new Bad('Give the buyer’s email address', 400);
  const id = rid('o'), t = now();
  const reference = `PA-O-${t.slice(2, 10).replace(/-/g, '')}-${rid('', 6).toUpperCase()}`;
  await run(env, `INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, buyer_email, artwork_snapshot, created_by, created_at, updated_at)
    VALUES (?,?,?,?,?, 'draft', ?,?,?,?,?)`, id, reference, artist.id, w.id, ref, email,
    JSON.stringify({ title: w.title, year: w.year, medium: w.medium, materials: w.materials, h_cm: w.h_cm, w_cm: w.w_cm, d_cm: w.d_cm, listed_price_eur: w.price_eur }), founder, t, t);
  await event(env, id, founder, 'created', null, 'draft', { enquiry_ref: ref });
  return orderDetail(env, await getOrder(env, id), 'founder');
}

/* Any change to price, delivery or commission evidence is a NEW quote version: an open checkout is expired at the
   provider first, the reservation is released and the artist must approve again. */
async function supersede(env, o, actor, why) {
  const open = await all(env, "SELECT * FROM checkout_sessions WHERE order_id = ? AND status = 'open'", o.id);
  for (const s of open) {
    try { await S.expireSession(env, { account: o.provider_account, id: s.id }); }
    catch (e) {
      const cur = await S.getSession(env, { account: o.provider_account, id: s.id }).catch(() => null);
      if (!cur || cur.status === 'complete') throw new Bad('The open checkout could not be closed (it may just have been paid). Reconcile the order first.', 409);
    }
    await run(env, "UPDATE checkout_sessions SET status = 'superseded', updated_at = ? WHERE id = ? AND status = 'open'", now(), s.id);
  }
  await run(env, 'DELETE FROM artwork_reservations WHERE order_id = ?', o.id);
  if (open.length) await event(env, o.id, actor, 'checkout_superseded', o.status, o.status, { sessions: open.map(s => s.id), why });
}
export async function updateOrder(env, founder, id, b) {
  await requireInstalled(env); requireOn(env);
  const o = await getOrder(env, id);
  if (!o) throw new Bad('Not found', 404);
  if (!R.PRE_PAYMENT.includes(o.status)) throw new Bad('A paid or closed order cannot be revised', 409);
  const sets = {};
  if (b.artwork_cents !== undefined) sets.artwork_cents = b.artwork_cents;
  if (b.delivery_cents !== undefined) sets.delivery_cents = b.delivery_cents;
  if (b.delivery !== undefined) sets.delivery = JSON.stringify(R.cleanDelivery(b.delivery));
  if (b.exclusion !== undefined) { if (b.exclusion !== null && !R.EXCLUSIONS[b.exclusion]) throw new Bad('Unknown exclusion'); sets.exclusion = b.exclusion; }
  if (b.negotiation_note !== undefined) sets.negotiation_note = b.negotiation_note ? String(b.negotiation_note).slice(0, 1000) : null;
  const merged = { ...o, ...sets };
  if (merged.artwork_cents != null) R.amounts({ artwork_cents: merged.artwork_cents, delivery_cents: merged.delivery_cents ?? 0, commission_bp: 0 });   // validates the figures
  if (!Object.keys(sets).length) throw new Bad('Nothing to change');
  await supersede(env, o, founder, 'quote revised');
  sets.quote_version = o.quote_version + 1;
  Object.assign(sets, { artist_approved_version: null, artist_approved_at: null, artist_confirmations: null, quote_issued_at: null, quote_expires_at: null,
    buyer_token_hash: null, commission_bp: null, commission_cents: null, commission_basis: null, entitlement: null });
  if (o.status === 'draft') {
    const keys = Object.keys(sets);
    const r = await run(env, `UPDATE checkout_orders SET ${keys.map(k => `${k} = ?`).join(', ')}, updated_at = ? WHERE id = ? AND status = 'draft' AND quote_version = ?`, ...keys.map(k => sets[k]), now(), o.id, o.quote_version);
    if (!r.meta.changes) throw new Bad('This order changed meanwhile. Reload and try again.', 409);
    await event(env, o.id, founder, 'revised', 'draft', 'draft', { quote_version: sets.quote_version });
  } else await move(env, o, 'draft', founder, 'revised', sets, { quote_version: sets.quote_version });
  return orderDetail(env, await getOrder(env, id), 'founder');
}

async function priced(env, o, at) {
  if (o.artwork_cents == null || o.delivery_cents == null || !o.delivery) throw new Bad('Enter the artwork price, the delivery charge and the delivery and cover details first', 409);
  R.checkCover(J(o.delivery), o.artwork_cents);
  const artist = await one(env, 'SELECT * FROM artists WHERE id = ?', o.artist_id);
  const e = await R.entitlement(env, { artist, enquiryRef: o.enquiry_ref, at, exclusion: o.exclusion, negotiationNote: o.negotiation_note });
  if (!e.ok) throw new Bad(e.reason, 409);
  return { artist, e, money: R.amounts({ artwork_cents: o.artwork_cents, delivery_cents: o.delivery_cents, commission_bp: e.bp }) };
}
export async function requestArtist(env, founder, id) {
  await requireInstalled(env); requireOn(env);
  const o = await getOrder(env, id);
  if (!o) throw new Bad('Not found', 404);
  await workAvailable(env, o.artist_id, o.artwork_id);
  const { e, money } = await priced(env, o, now());
  await move(env, o, 'awaiting_artist', founder, 'sent_to_artist', { commission_bp: e.bp, commission_cents: money.commission_cents, commission_basis: e.basis, entitlement: JSON.stringify(e.evidence) },
    { quote_version: o.quote_version, commission_bp: e.bp, basis: e.basis });
  return orderDetail(env, await getOrder(env, id), 'founder');
}

/* ---------------------------------------------------------------- artist: approve the exact quote */
const CONFIRM = ['available', 'location', 'condition', 'framing', 'dimensions', 'packing_and_handover'];
export async function approveQuote(env, artist, id, b) {
  await requireInstalled(env); requireOn(env);
  const o = await one(env, 'SELECT * FROM checkout_orders WHERE id = ? AND artist_id = ?', id, artist.id);   // never another artist's order
  if (!o) throw new Bad('Not found', 404);
  if (o.status !== 'awaiting_artist') throw new Bad('This quote is not waiting for your approval', 409);
  if (b.quote_version !== o.quote_version) throw new Bad('This quote has changed. Please review the new version.', 409);
  if (b.decision === 'decline') return orderDetail(env, await move(env, o, 'draft', 'artist:' + artist.email, 'artist_declined', {}, { note: String(b.note || '').slice(0, 500) }), 'artist');
  const c = b.confirm || {};
  const missing = CONFIRM.filter(k => c[k] !== true);
  if (missing.length) throw new Bad(`Please confirm: ${missing.join(', ').replace(/_/g, ' ')}`, 400);
  const memA = await membership(env, artist.id);
  if (!memA.opted_in) throw new Bad('You are no longer in the payment pilot', 409);
  requireProcessingConsent(memA, o.commission_bp);
  await workAvailable(env, artist.id, o.artwork_id);
  const conf = JSON.stringify({ ...Object.fromEntries(CONFIRM.map(k => [k, true])), note: String(b.note || '').slice(0, 500) || null });
  const r = await run(env, `UPDATE checkout_orders SET artist_approved_version = ?, artist_approved_at = ?, artist_confirmations = ?, updated_at = ? WHERE id = ? AND status = 'awaiting_artist' AND quote_version = ?`,
    o.quote_version, now(), conf, now(), o.id, o.quote_version);
  if (!r.meta.changes) throw new Bad('This quote changed meanwhile. Reload and try again.', 409);
  await event(env, o.id, 'artist:' + artist.email, 'artist_approved', 'awaiting_artist', 'awaiting_artist', { quote_version: o.quote_version });
  return orderDetail(env, await getOrder(env, id), 'artist');
}

/* ---------------------------------------------------------------- linked transactions (anti-money-laundering)
   The pilot's per-artwork scope limit does NOT settle any AML question: Irish law looks at the value of a transaction alone
   or together with transactions that are or appear to be linked. Until PlotArt has professional advice and, if required,
   the procedures of a designated person, the pilot refuses any quote that would take this buyer's apparently linked
   orders (same email address, any artist, last 12 months, every order that was paid, refunded or is quoted and payable) to EUR 10,000
   or more, and the founder must confirm before each quote that he knows of no other link (other addresses, household,
   business, agents, staged payments). This is a LIMITED OPERATIONAL SAFEGUARD: matching on email addresses cannot detect a
   buyer using other addresses or acting through others, 12 months is a pilot rule rather than a legal definition, and a
   pass is never confirmation of anti-money-laundering compliance or evidence that no obligation applies. */
export async function linkedCheck(env, o) {
  const since = new Date(Date.now() - R.LINKED_WINDOW_DAYS * 86400_000).toISOString();
  const rows = await all(env, `SELECT reference, artwork_cents + COALESCE(delivery_cents, 0) AS total FROM checkout_orders
    WHERE lower(buyer_email) = lower(?) AND id <> ? AND created_at >= ? AND artwork_cents IS NOT NULL
      AND (payment_status <> 'none' OR status IN ('quoted', 'checkout_open', 'payment_failed'))`, o.buyer_email, o.id, since);
  const others = rows.reduce((a, r) => a + r.total, 0), total = others + o.artwork_cents + (o.delivery_cents || 0);
  return { ok: total < R.LINKED_THRESHOLD_CENTS, total_cents: total, linked: rows.map(r => r.reference), window_days: R.LINKED_WINDOW_DAYS,
    reason: total < R.LINKED_THRESHOLD_CENTS ? null : `This buyer's apparently linked purchases reach EUR ${(total / 100).toFixed(2)} (EUR 10,000 or more). That is outside the pilot until PlotArt's anti-money-laundering position is settled by professional advice.` };
}

/* ---------------------------------------------------------------- founder: issue the buyer's quote */
export async function issueQuote(env, founder, id, b = {}) {
  await requireInstalled(env); requireOn(env);
  const o = await getOrder(env, id);
  if (!o) throw new Bad('Not found', 404);
  if (o.status !== 'awaiting_artist') throw new Bad('Send the quote to the artist first', 409);
  if (o.artist_approved_version !== o.quote_version) throw new Bad('The artist has not approved this version of the quote', 409);
  const mem = await membership(env, o.artist_id);
  if (!mem.opted_in) throw new Bad('The artist is no longer in the payment pilot', 409);
  if (!mem.ready) throw new Bad('The artist’s Stripe account is not ready to take payments (onboarding incomplete)', 409);
  requireProcessingConsent(mem, o.commission_bp);
  const add = await currentTerms(env, 'artist_payment_addendum'), bt = await currentTerms(env, 'buyer_purchase_terms');
  if (!bt) throw new Bad('The buyer purchase terms have not been issued yet', 409);
  if (!add || add.doc_id !== mem.addendum) throw new Bad('The artist’s accepted addendum is not the current one: ask them to review the current text', 409);
  await workAvailable(env, o.artist_id, o.artwork_id);
  const lc = await linkedCheck(env, o);
  if (!lc.ok) throw new Bad(lc.reason, 409);
  if (b.linked_check_confirmed !== true) throw new Bad('Confirm that, as far as you know, this purchase is not linked to other purchases by this buyer or anyone acting with them (other email addresses, household, business, agents, staged payments)', 400);
  const t = now();
  const { artist, e, money } = await priced(env, o, t);
  if (e.bp !== o.commission_bp || money.commission_cents !== o.commission_cents) {
    await move(env, o, 'draft', 'system', 'commission_changed', { artist_approved_version: null, artist_approved_at: null, artist_confirmations: null, commission_bp: null,
      commission_cents: null, commission_basis: null, entitlement: null, quote_version: o.quote_version + 1 }, { was: o.commission_bp, now: e.bp });
    throw new Bad('The commission entitlement changed since the artist approved. The quote was returned to draft.', 409);
  }
  const accept = await one(env, "SELECT legal_name FROM agreement_acceptances WHERE artist_id = ? AND legal_name IS NOT NULL ORDER BY accepted_at DESC LIMIT 1", artist.id);
  const seller = { name: artist.display_name, legal_name: accept ? accept.legal_name : null, role: 'Seller (the artist)', stripe_account_country: mem.account.country,
    platform: 'PlotArt (PlotNua, Colin Macaulay) introduces and coordinates this sale. PlotArt is not the seller.', contact: 'hello@plotnua.ie' };
  const token = rid('', 32) + rid('', 16);
  const expires = R.quoteExpiry(t, Number.isInteger(b.days) ? b.days : 3);
  await move(env, o, 'quoted', founder, 'quote_issued', { quote_issued_at: t, quote_expires_at: expires, buyer_token_hash: await sha256(token), seller: JSON.stringify(seller),
    addendum_doc_id: add.doc_id, buyer_terms_doc_id: bt.doc_id, provider_account: mem.account.id, entitlement: JSON.stringify(e.evidence),
    linked_order_check: JSON.stringify({ at: t, by: founder, founder_confirmed_no_other_link: true, ...lc, note: 'Operational safeguard only. Not an AML assessment and not evidence of AML compliance.' }) },
    { quote_version: o.quote_version, expires, total_cents: money.total_cents, commission_cents: money.commission_cents });
  return { ...(await orderDetail(env, await getOrder(env, id), 'founder')), buyer_link: `${env.CHECKOUT_ORIGIN}/q/${token}`,
    note: 'Send this link to the buyer yourself. It is shown once and is the only way to open this quote.' };
}

export async function cancelOrder(env, o, actor, reason) {
  if (!R.PRE_PAYMENT.includes(o.status)) throw new Bad('A paid order is not cancelled: refund it instead', 409);
  await supersede(env, o, actor, 'cancelled');
  return move(env, o, 'cancelled', actor, 'cancelled', {}, { reason: String(reason || '').slice(0, 300) });   // the buyer's link stays readable: it says the quote cannot be paid
}

/* ---------------------------------------------------------------- buyer: the quote and hosted checkout */
async function byToken(env, token) {
  if (!/^[0-9a-z]{48}$/.test(String(token || ''))) return null;
  return one(env, 'SELECT * FROM checkout_orders WHERE buyer_token_hash = ?', await sha256(token));
}
export async function buyerQuote(env, token) {
  const o = await byToken(env, token);
  if (!o) return null;
  const bt = o.buyer_terms_doc_id ? await one(env, 'SELECT doc_id, title FROM payment_terms WHERE doc_id = ?', o.buyer_terms_doc_id) : null;
  const d = J(o.delivery) || {};
  return { reference: o.reference, status: o.status, payment_status: o.payment_status, fulfilment_status: o.fulfilment_status,
    expired: !!o.quote_expires_at && o.quote_expires_at <= now(), quote_expires_at: o.quote_expires_at, seller: J(o.seller), artwork: J(o.artwork_snapshot),
    currency: 'EUR', artwork_cents: o.artwork_cents, delivery_cents: o.delivery_cents, total_cents: o.artwork_cents + o.delivery_cents,
    delivery: { collection_county: d.collection_county, destination: d.destination, packed_cm: d.packed_cm, framing: d.framing, glazing: d.glazing, condition: d.condition,
      organiser: d.organiser, packer: d.packer, transport_contracting_party: d.transport_contracting_party, transporter_name: d.transporter_name, installation: d.installation, import_costs: d.import_costs,
      cover_type: d.cover_type, cover_provider: d.cover_provider, insured_party: d.insured_party, cover_confirmation_ref: d.cover_confirmation_ref, covered_value_cents: d.covered_value_cents, valuation_basis: d.valuation_basis, excess_cents: d.excess_cents,
      exclusions: d.exclusions, cover_period: d.cover_period, claims_contact: d.claims_contact, delivery_window: d.delivery_window, tracking: d.tracking,
      signed_receipt: d.signed_receipt, condition_photos: d.condition_photos, return_route: d.return_route },
    terms: bt };
}

export async function startCheckout(env, token, b) {
  requireOn(env);
  const o = await byToken(env, token);
  if (!o) throw new Bad('This quote is not available', 404);
  if (!['quoted', 'checkout_open', 'payment_failed'].includes(o.status)) throw new Bad('This quote can no longer be paid', 409);
  const t = now();
  if (!o.quote_expires_at || o.quote_expires_at <= t) { await move(env, o, 'expired', 'buyer', 'quote_expired').catch(() => {}); throw new Bad('This quote has expired. Please contact hello@plotnua.ie.', 410); }
  if (o.artist_approved_version !== o.quote_version) throw new Bad('This quote is being revised', 409);
  if (!b || b.accept_terms !== o.buyer_terms_doc_id) throw new Bad('Please read and accept the purchase terms', 400);
  const mem = await membership(env, o.artist_id);
  if (!mem.ready || mem.account.id !== o.provider_account) throw new Bad('The seller cannot take payments at the moment. Please contact hello@plotnua.ie.', 409);
  const add = await currentTerms(env, 'artist_payment_addendum');
  if (!mem.opted_in || !add || add.doc_id !== o.addendum_doc_id) throw new Bad('The seller cannot take payments at the moment. Please contact hello@plotnua.ie.', 409);
  if (o.commission_bp === 0 && !mem.processing_consent) throw new Bad('The seller cannot take payments through PlotArt at the moment. Please contact hello@plotnua.ie.', 409);
  await workAvailable(env, o.artist_id, o.artwork_id).catch(() => { throw new Bad('Sorry, this artwork is no longer available.', 409); });
  if (!(await linkedCheck(env, o)).ok) throw new Bad('This purchase cannot be completed through the pilot. Please contact hello@plotnua.ie.', 409);
  // an open session for this quote version that still has time left is reused (a double click opens the same checkout)
  const open = await one(env, "SELECT * FROM checkout_sessions WHERE order_id = ? AND status = 'open'", o.id);
  if (open && open.quote_version === o.quote_version && addMin(t, 5) < open.expires_at) return { url: open.url, reused: true };
  if (open) await supersede(env, o, 'buyer', 'session replaced');
  // reserve the original atomically: free, expired, or already this order's; never while it is sold
  const sessionExpires = new Date(Math.min(Date.parse(addMin(t, R.SESSION_MINUTES + 1)), Date.parse(o.quote_expires_at) + 60_000)).toISOString();
  if (Date.parse(sessionExpires) - Date.parse(t) < 30 * 60_000 + 30_000) throw new Bad('This quote expires too soon to pay. Please contact hello@plotnua.ie.', 410);
  const holdUntil = addMin(sessionExpires, R.RESERVATION_GRACE_MINUTES);
  const r = await run(env, `INSERT INTO artwork_reservations (artwork_id, order_id, quote_version, expires_at, created_at)
    SELECT ?, ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM artwork_sales WHERE artwork_id = ? AND released_at IS NULL)
    ON CONFLICT(artwork_id) DO UPDATE SET order_id = excluded.order_id, quote_version = excluded.quote_version, expires_at = excluded.expires_at, created_at = excluded.created_at
    WHERE artwork_reservations.order_id = excluded.order_id OR artwork_reservations.expires_at < excluded.created_at`,
    o.artwork_id, o.id, o.quote_version, holdUntil, t, o.artwork_id).catch(e => { if (/UNIQUE/.test(String(e.message))) return { meta: { changes: 0 } }; throw e; });
  if (!r.meta.changes) throw new Bad('Someone else is completing a purchase of this artwork right now. Please try again later.', 409);
  const money = R.amounts({ artwork_cents: o.artwork_cents, delivery_cents: o.delivery_cents, commission_bp: o.commission_bp });
  if (money.commission_cents !== o.commission_cents) throw new Bad('Quote integrity check failed', 500);
  const n = (await one(env, 'SELECT COUNT(*) AS n FROM checkout_sessions WHERE order_id = ?', o.id)).n;
  let s;
  try {
    const art = J(o.artwork_snapshot) || {}, seller = J(o.seller) || {};
    s = await S.createSession(env, { account: o.provider_account, idem: `plotart-${o.id}-v${o.quote_version}-s${n + 1}`, order: o, title: `${art.title || 'Original artwork'} by ${seller.name}`,
      artworkCents: o.artwork_cents, deliveryCents: o.delivery_cents, feeCents: o.commission_cents, expiresAt: sessionExpires, buyerEmail: o.buyer_email,
      successUrl: `${env.CHECKOUT_ORIGIN}/q/${token}/return?result=success`, cancelUrl: `${env.CHECKOUT_ORIGIN}/q/${token}/return?result=cancel`,
      statement: `${o.reference} · sold by ${seller.name} · introduced by PlotArt` });
  } catch (e) {
    await run(env, 'DELETE FROM artwork_reservations WHERE order_id = ?', o.id);
    throw new Bad(e instanceof S.StripeError ? `Checkout could not be opened: ${e.message}` : 'Checkout could not be opened', e.status && e.status < 500 ? 409 : 502);
  }
  if (s.amount_total != null && s.amount_total !== money.total_cents) throw new Bad('Checkout amount mismatch', 500);
  await env.DB.batch([
    st(env, `INSERT INTO checkout_sessions (id, order_id, quote_version, amount_total, application_fee_cents, status, url, expires_at, created_at, updated_at) VALUES (?,?,?,?,?, 'open', ?,?,?,?)`,
      s.id, o.id, o.quote_version, money.total_cents, money.commission_cents, s.url, sessionExpires, t, t),
    st(env, `UPDATE checkout_orders SET status = 'checkout_open', payment_status = 'open', buyer_terms_accepted_at = ?, updated_at = ? WHERE id = ? AND status = ?`, t, t, o.id, o.status),
    evSt(env, o.id, 'buyer', 'checkout_opened', o.status, 'checkout_open', { session: s.id, quote_version: o.quote_version, terms: o.buyer_terms_doc_id, hold_until: holdUntil }),
  ]);
  return { url: s.url };
}

/* ---------------------------------------------------------------- verified provider events */
export async function webhook(env, raw, signature) {
  const v = await S.verifySignature(env, signature, raw);
  if (!v.ok) return { status: 400, body: { ok: false, error: 'invalid signature' } };
  let ev; try { ev = JSON.parse(raw); } catch { return { status: 400, body: { ok: false } }; }
  if (ev.livemode !== false) return { status: 400, body: { ok: false, error: 'live-mode events are refused by the test-mode pilot' } };
  if (!/^evt_/.test(String(ev.id || ''))) return { status: 400, body: { ok: false } };
  const prior = await one(env, 'SELECT * FROM payment_events WHERE event_id = ?', ev.id);
  if (prior && ['processed', 'ignored'].includes(prior.status)) return { status: 200, body: { ok: true, duplicate: true } };
  const obj = (ev.data && ev.data.object) || {};
  if (prior) await run(env, 'UPDATE payment_events SET attempts = attempts + 1, status = ? WHERE event_id = ?', 'received', ev.id);
  else {
    const ins = await run(env, `INSERT INTO payment_events (event_id, type, account, livemode, created, object_id, status, received_at) VALUES (?,?,?,0,?,?, 'received', ?) ON CONFLICT(event_id) DO NOTHING`,
      ev.id, String(ev.type), ev.account || null, Number(ev.created) || 0, obj.id || null, now());
    if (!ins.meta.changes) return { status: 503, body: { ok: false, error: 'being processed' } };   // a racing duplicate: let the provider retry
  }
  try {
    const out = await apply(env, ev, obj);
    await run(env, 'UPDATE payment_events SET status = ?, order_id = ?, detail = ?, processed_at = ? WHERE event_id = ?', out.status, out.order || null, out.detail || null, now(), ev.id);
    if (out.status === 'deferred') return { status: 500, body: { ok: false, deferred: true } };   // the provider retries later
    return { status: 200, body: { ok: true, result: out.status } };
  } catch (e) {
    await run(env, "UPDATE payment_events SET status = 'failed', detail = ? WHERE event_id = ?", String(e.message || e).slice(0, 500), ev.id);
    return { status: 500, body: { ok: false } };
  }
}

async function orderForSession(env, ev, s) {
  const row = await one(env, 'SELECT * FROM checkout_sessions WHERE id = ?', s.id);
  const id = row ? row.order_id : (s.metadata && s.metadata.plotart_order);
  const o = id ? await getOrder(env, id) : null;
  if (o && ev.account && o.provider_account !== ev.account) throw new Error('event account does not match the order');
  return { o, row };
}
async function orderForPI(env, ev, pi) {
  const o = pi ? await one(env, 'SELECT * FROM checkout_orders WHERE payment_intent = ?', pi) : null;
  if (o && ev.account && o.provider_account !== ev.account) throw new Error('event account does not match the order');
  return o;
}

async function apply(env, ev, obj) {
  switch (ev.type) {
    case 'account.updated': {
      const a = await one(env, 'SELECT artist_id FROM payment_accounts WHERE account_id = ?', obj.id);
      if (!a) return { status: 'ignored', detail: 'unknown account' };
      await applyAccount(env, obj);
      return { status: 'processed' };
    }
    case 'checkout.session.completed':
    case 'checkout.session.async_payment_succeeded': {
      const { o } = await orderForSession(env, ev, obj);
      if (!o) return { status: 'ignored', detail: 'no pilot order' };
      if (obj.payment_status !== 'paid') return { status: 'processed', order: o.id, detail: 'awaiting asynchronous payment' };
      return { status: 'processed', order: o.id, detail: await recordPaid(env, o, obj, ev.id) };
    }
    case 'checkout.session.async_payment_failed': {
      const { o } = await orderForSession(env, ev, obj);
      if (!o) return { status: 'ignored' };
      await run(env, "UPDATE checkout_sessions SET status = 'expired', updated_at = ? WHERE id = ? AND status = 'open'", now(), obj.id);
      if (o.payment_status === 'paid') return { status: 'ignored', order: o.id, detail: 'already paid' };
      await run(env, 'DELETE FROM artwork_reservations WHERE order_id = ?', o.id);
      if (R.canMove(o.status, 'payment_failed')) await move(env, o, 'payment_failed', 'provider', 'payment_failed', { payment_status: 'failed' }, { event: ev.id });
      return { status: 'processed', order: o.id };
    }
    case 'checkout.session.expired': {
      const { o, row } = await orderForSession(env, ev, obj);
      if (!o) return { status: 'ignored' };
      await run(env, "UPDATE checkout_sessions SET status = 'expired', updated_at = ? WHERE id = ? AND status = 'open'", now(), obj.id);
      if (o.payment_status === 'paid' || ['paid', 'dispatched', 'delivered', 'closed', 'refund_pending', 'refunded', 'disputed'].includes(o.status))
        return { status: 'ignored', order: o.id, detail: 'order already paid: an out-of-order expiry is ignored' };
      const current = await one(env, "SELECT 1 AS x FROM checkout_sessions WHERE order_id = ? AND status = 'open'", o.id);
      if (!current) await run(env, 'DELETE FROM artwork_reservations WHERE order_id = ?', o.id);   // released only if no newer checkout holds it
      if (o.status === 'checkout_open' && !current) {
        const back = o.quote_expires_at > now() ? 'quoted' : 'expired';
        await move(env, o, back, 'provider', 'checkout_expired', { payment_status: 'none' }, { session: obj.id, superseded: row && row.status === 'superseded' });
      }
      return { status: 'processed', order: o.id };
    }
    case 'charge.refunded': {
      const o = await orderForPI(env, ev, obj.payment_intent);
      if (!o) return obj.payment_intent && await knownPI(env, ev, obj) ? deferFor(obj.payment_intent) : { status: 'ignored' };
      return { status: 'processed', order: o.id, detail: await recordRefunds(env, o, obj) };
    }
    case 'refund.updated':
    case 'refund.failed':
    case 'charge.refund.updated': {
      let mine = await one(env, 'SELECT * FROM order_refunds WHERE provider_refund_id = ?', obj.id);
      if (!mine && obj.metadata && obj.metadata.plotart_refund) {   // the event can arrive before the refund id was stored
        mine = await one(env, 'SELECT * FROM order_refunds WHERE id = ?', obj.metadata.plotart_refund);
        if (mine) await run(env, 'UPDATE order_refunds SET provider_refund_id = COALESCE(provider_refund_id, ?), updated_at = ? WHERE id = ?', obj.id, now(), mine.id);
      }
      if (!mine) return { status: 'ignored', detail: 'not a PlotArt refund (artist refunds arrive as charge.refunded)' };
      const o = await getOrder(env, mine.order_id);
      if (ev.account && o.provider_account !== ev.account) throw new Error('event account does not match the order');
      if (obj.status === 'succeeded') { await completeRefund(env, 'provider', { ...mine, provider_refund_id: obj.id }); return { status: 'processed', order: o.id, detail: 'refund succeeded' }; }
      if (['failed', 'canceled'].includes(obj.status)) { await failRefund(env, mine, obj); return { status: 'processed', order: o.id, detail: 'refund failed' }; }
      return { status: 'processed', order: o.id, detail: 'refund still ' + obj.status };
    }
    case 'charge.dispute.created':
    case 'charge.dispute.updated':
    case 'charge.dispute.closed': {
      const o = await orderForPI(env, ev, obj.payment_intent);
      if (!o) return obj.payment_intent && await knownPI(env, ev, obj) ? deferFor(obj.payment_intent) : { status: 'ignored' };
      return { status: 'processed', order: o.id, detail: await recordDispute(env, o, ev.type, obj) };
    }
    default: return { status: 'ignored', detail: 'event type not used by the pilot' };
  }
}
/* A charge event can arrive BEFORE the checkout completion that links its payment to an order (out of order). If the
   payment belongs to one of our sessions' accounts, it is deferred rather than dropped, and the PaymentIntent is noted.
   It is then REPLAYED by the pilot itself as soon as the completion links that PaymentIntent to an order, and by the
   sweep as a backstop — not left to the provider's redelivery alone (run 15: a dispute created seconds after payment
   arrived before the completion; the Stripe CLI forwarder never redelivers, and live redelivery can take hours).
   Replay re-reads the CURRENT object from Stripe by id, so a stale payload is never applied. */
const deferFor = pi => ({ status: 'deferred', detail: `awaiting order for ${pi}` });
const REFETCH = { 'charge.dispute.': S.getDispute, 'charge.': S.getCharge, 'refund.': S.getRefund };
export async function replayDeferred(env, pi = null) {
  const rows = pi
    ? await all(env, "SELECT * FROM payment_events WHERE status = 'deferred' AND detail = ? ORDER BY created, received_at", `awaiting order for ${pi}`)
    : await all(env, "SELECT * FROM payment_events WHERE status = 'deferred' AND detail LIKE 'awaiting order for %' ORDER BY created, received_at LIMIT 50");
  let done = 0;
  for (const row of rows) {
    const pfx = Object.keys(REFETCH).find(k => row.type.startsWith(k));
    if (!pfx || !row.object_id || !row.account) continue;
    try {
      const obj = await REFETCH[pfx](env, { account: row.account, id: row.object_id });
      const out = await apply(env, { id: row.event_id, type: row.type, account: row.account }, obj);
      if (out.status === 'deferred') continue;   // still no order: left for a later replay or redelivery
      await run(env, "UPDATE payment_events SET status = ?, order_id = ?, detail = ?, attempts = attempts + 1, processed_at = ? WHERE event_id = ? AND status = 'deferred'",
        out.status, out.order || null, ('replayed after the payment was linked; ' + (out.detail || '')).slice(0, 500), now(), row.event_id);
      done++;
    } catch (e) { await run(env, "UPDATE payment_events SET attempts = attempts + 1 WHERE event_id = ?", row.event_id); }
  }
  return done;
}
async function knownPI(env, ev, obj) {
  if (obj.metadata && obj.metadata.plotart_order) return !!(await getOrder(env, obj.metadata.plotart_order));
  if (!ev.account || !(await one(env, 'SELECT 1 AS x FROM payment_accounts WHERE account_id = ?', ev.account))) return false;
  const p = await S.getPaymentIntent(env, { account: ev.account, id: obj.payment_intent }).catch(() => null);   // the artist's own non-PlotArt sales are ignored
  return !!(p && p.metadata && p.metadata.plotart_order && await getOrder(env, p.metadata.plotart_order));
}

const ledgerSt = (env, orderId, kind, cents, ref, note) => st(env, 'INSERT INTO order_ledger (id, order_id, kind, amount_cents, provider_ref, at, note) VALUES (?,?,?,?,?,?,?) ON CONFLICT(kind, provider_ref) DO NOTHING',
  rid('l'), orderId, kind, cents, ref, now(), note || null);

/* A verified completed payment. The sale, the order, the session, the reservation release, the Studio "sold" mark and
   the ledger are written in ONE transaction. If the original has already been sold (to another order), nothing is sold
   twice: the payment is booked and the order is flagged for a refund. */
async function recordPaid(env, o, s, eventId) {
  if (o.payment_status === 'paid' || ['paid', 'dispatched', 'delivered', 'closed', 'refunded', 'disputed'].includes(o.status)) return 'already recorded';
  const t = now(), pi = typeof s.payment_intent === 'string' ? s.payment_intent : s.payment_intent && s.payment_intent.id;
  const expected = o.artwork_cents + o.delivery_cents;
  const sessRow = await one(env, 'SELECT * FROM checkout_sessions WHERE id = ?', s.id);
  const problems = [];
  if (s.amount_total !== expected) problems.push(`amount ${s.amount_total} ≠ quoted ${expected}`);
  if (String(s.currency).toLowerCase() !== 'eur') problems.push('currency is not EUR');
  if (sessRow && sessRow.quote_version !== o.quote_version) problems.push(`paid quote version ${sessRow.quote_version} ≠ current ${o.quote_version}`);
  if (sessRow && sessRow.application_fee_cents !== o.commission_cents) problems.push('application fee differs from the order commission');
  const late = !['checkout_open', 'quoted', 'payment_failed'].includes(o.status) || (sessRow && sessRow.status !== 'open');
  // the payment and the commission the provider took are booked in every case (money was received)
  const books = [
    ledgerSt(env, o.id, 'charge', s.amount_total, pi, `checkout ${s.id}`),
    ...(sessRow && sessRow.application_fee_cents > 0 ? [ledgerSt(env, o.id, 'commission', sessRow.application_fee_cents, pi, o.commission_basis)] : []),
  ];
  const sold = await one(env, 'SELECT order_id FROM artwork_sales WHERE artwork_id = ? AND released_at IS NULL AND order_id <> ?', o.artwork_id, o.id);
  if (sold) problems.push(`this original was already sold through another order (${(await getOrder(env, sold.order_id)).reference})`);
  const work = await one(env, 'SELECT availability FROM artworks WHERE id = ?', o.artwork_id);
  if (!sold && work.availability !== 'available') problems.push(`artwork marked ${work.availability} in the Studio before payment`);
  const flag = async why => {
    await env.DB.batch([...books,
      st(env, `UPDATE checkout_orders SET status = 'refund_pending', payment_status = 'paid', payment_intent = ?, amount_received_cents = ?, paid_at = ?, needs_resolution = ?, updated_at = ? WHERE id = ?`, pi, s.amount_total, t, why, t, o.id),
      st(env, "UPDATE checkout_sessions SET status = 'complete', updated_at = ? WHERE id = ?", t, s.id),
      st(env, 'DELETE FROM artwork_reservations WHERE order_id = ?', o.id),
      evSt(env, o.id, 'provider', 'paid_needs_resolution', o.status, 'refund_pending', { event: eventId, why })]);
    return 'flagged: ' + why;
  };
  if (problems.length) return flag(problems.join('; ') + ' — refund or resolve with the buyer');
  try {
    await env.DB.batch([
      st(env, 'INSERT INTO artwork_sales (order_id, artwork_id, sold_at) VALUES (?,?,?)', o.id, o.artwork_id, t),
      ...books,
      ledgerSt(env, o.id, 'artist_artwork', o.artwork_cents - o.commission_cents, pi, 'artwork amount after commission, before Stripe fees'),
      ...(o.delivery_cents > 0 ? [ledgerSt(env, o.id, 'delivery_allocation', o.delivery_cents, pi, 'pays the quoted delivery obligation; not artist profit')] : []),
      st(env, `UPDATE checkout_orders SET status = 'paid', payment_status = 'paid', payment_intent = ?, amount_received_cents = ?, paid_at = ?, needs_resolution = ?, updated_at = ? WHERE id = ?`,
        pi, s.amount_total, t, late ? 'late payment after the quote/checkout had expired: recorded as a sale (the work was still free); confirm with buyer and artist' : null, t, o.id),
      st(env, "UPDATE checkout_sessions SET status = 'complete', updated_at = ? WHERE id = ?", t, s.id),
      st(env, 'DELETE FROM artwork_reservations WHERE order_id = ?', o.id),
      st(env, "UPDATE artworks SET availability = 'sold', updated_at = ? WHERE id = ? AND availability = 'available'", t, o.artwork_id),
      evSt(env, o.id, 'provider', late ? 'paid_late' : 'paid', o.status, 'paid', { event: eventId, payment_intent: pi, amount: s.amount_total }),
    ]);
  } catch (e) {
    if (/UNIQUE/.test(String(e.message))) return flag('paid, but this original was already sold through another order — refund the buyer');
    throw e;
  }
  // another order that had reserved or opened checkout on the same work can no longer buy it
  for (const other of await all(env, `SELECT * FROM checkout_orders WHERE artwork_id = ? AND id <> ? AND status IN ('quoted','checkout_open','payment_failed','awaiting_artist','draft')`, o.artwork_id, o.id)) {
    try { await cancelOrder(env, other, 'system', `Artwork sold through order ${o.reference}`); }
    catch { await run(env, 'UPDATE checkout_orders SET needs_resolution = ?, updated_at = ? WHERE id = ?', `artwork sold through ${o.reference}; this order's checkout could not be closed`, now(), other.id); }
  }
  // the application fee id (created asynchronously by the provider) is fetched when available; refunds fetch it again if not
  try {
    const p = await S.getPaymentIntent(env, { account: o.provider_account, id: pi });
    const ch = p.latest_charge && typeof p.latest_charge === 'object' ? p.latest_charge : null;
    if (ch) await run(env, 'UPDATE checkout_orders SET charge_id = COALESCE(charge_id, ?), application_fee_id = COALESCE(application_fee_id, ?), updated_at = ? WHERE id = ?',
      ch.id, typeof ch.application_fee === 'string' ? ch.application_fee : ch.application_fee && ch.application_fee.id || null, now(), o.id);
  } catch { /* fetched again at refund time */ }
  // events for this payment that arrived before this completion (e.g. a dispute) are applied now, not left waiting
  let replayed = 0; try { replayed = await replayDeferred(env, pi); } catch { /* the sweep retries */ }
  return (late ? 'paid (late)' : 'paid') + (replayed ? `; ${replayed} earlier event(s) replayed` : '');
}

async function refundTotals(env, orderId) {
  // a refund Stripe reversed (succeeded, then failed) is booked as a positive *_reversed line and no longer counts as repaid
  const r = await one(env, `SELECT COALESCE(SUM(CASE WHEN kind IN ('artwork_refund','artwork_refund_reversed') THEN -amount_cents END), 0) AS art, COALESCE(SUM(CASE WHEN kind IN ('delivery_refund','delivery_refund_reversed') THEN -amount_cents END), 0) AS del,
    COALESCE(SUM(CASE WHEN kind = 'commission_refund' THEN -amount_cents END), 0) AS fee, COALESCE(SUM(CASE WHEN kind = 'external_refund' THEN -amount_cents END), 0) AS ext FROM order_ledger WHERE order_id = ?`, orderId);
  return r;
}

/* Refunds confirmed by the provider. Refunds PlotArt asked for are matched to their request; a refund the artist made
   in their own Stripe Dashboard is booked as external and flagged so the commission can be settled under GAA 9. */
async function recordRefunds(env, o, ch) {
  const out = [];
  for (const r of ((ch.refunds && ch.refunds.data) || [])) {
    if (r.status !== 'succeeded') continue;
    const mine = await one(env, 'SELECT * FROM order_refunds WHERE provider_refund_id = ?', r.id)
      || (r.metadata && r.metadata.plotart_refund ? await one(env, 'SELECT * FROM order_refunds WHERE id = ? AND order_id = ?', r.metadata.plotart_refund, o.id) : null);
    if (mine) {
      if (mine.status !== 'succeeded') await completeRefund(env, 'provider', { ...mine, provider_refund_id: r.id });
      out.push(`${r.id} confirmed`);
      continue;
    } else {
      await env.DB.batch([ledgerSt(env, o.id, 'external_refund', -r.amount, r.id, 'refund made outside PlotArt (artist’s Stripe Dashboard): allocate and settle commission'),
        st(env, 'UPDATE checkout_orders SET needs_resolution = ?, updated_at = ? WHERE id = ?', `external refund ${r.id} of ${r.amount} cents: allocate artwork/delivery and settle commission (GAA 9)`, now(), o.id),
        evSt(env, o.id, 'provider', 'external_refund', o.status, o.status, { refund: r.id, amount: r.amount })]);
      out.push(`${r.id} external`);
    }
  }
  if (out.some(x => x.endsWith('external'))) {
    const fresh = await getOrder(env, o.id), tot = await refundTotals(env, o.id);
    const refunded = tot.art + tot.del + tot.ext;
    if (refunded >= fresh.amount_received_cents && fresh.status !== 'refunded' && R.canMove(fresh.status, 'refunded'))
      await move(env, fresh, 'refunded', 'provider', 'fully_refunded', { payment_status: 'refunded' });
    else if (refunded > 0 && fresh.payment_status === 'paid') await run(env, "UPDATE checkout_orders SET payment_status = 'partially_refunded', updated_at = ? WHERE id = ?", now(), o.id);
  }
  return out.join(', ') || 'no succeeded refunds';
}

async function recordDispute(env, o, type, d) {
  if (type === 'charge.dispute.created') {
    await env.DB.batch([ledgerSt(env, o.id, 'dispute', -d.amount, d.id, `dispute opened: ${d.reason || 'unspecified'} (debited from the seller’s Stripe balance by Stripe)`),
      st(env, "UPDATE checkout_orders SET dispute_status = 'open', updated_at = ? WHERE id = ?", now(), o.id)]);
    if (R.canMove(o.status, 'disputed')) await move(env, o, 'disputed', 'provider', 'dispute_opened', {}, { dispute: d.id, amount: d.amount });
    return 'dispute opened';
  }
  if (type === 'charge.dispute.closed') {
    const won = d.status === 'won';
    if (won) await run(env, 'INSERT INTO order_ledger (id, order_id, kind, amount_cents, provider_ref, at, note) VALUES (?,?,?,?,?,?,?) ON CONFLICT(kind, provider_ref) DO NOTHING',
      rid('l'), o.id, 'dispute_reinstated', d.amount, d.id, now(), 'dispute won: funds reinstated');
    await run(env, 'UPDATE checkout_orders SET dispute_status = ?, needs_resolution = ?, updated_at = ? WHERE id = ?', won ? 'won' : 'lost',
      won ? o.needs_resolution : `dispute lost (${d.id}): refund PlotArt’s commission under GAA 9 (founder action: Refund commission only)`, now(), o.id);
    const cur = await getOrder(env, o.id);
    if (cur.status === 'disputed') {
      const back = won ? (cur.fulfilment_status === 'delivered' ? 'delivered' : cur.fulfilment_status === 'dispatched' ? 'dispatched' : 'paid') : 'refunded';
      await move(env, cur, back, 'provider', won ? 'dispute_won' : 'dispute_lost', won ? {} : { payment_status: 'refunded' }, { dispute: d.id });
    }
    return won ? 'dispute won' : 'dispute lost';
  }
  return 'dispute updated';
}

/* ---------------------------------------------------------------- founder: refunds and reconciliation */
export async function refund(env, founder, id, b) {
  await requireInstalled(env); requireOn(env);
  const o = await getOrder(env, id);
  if (!o) throw new Bad('Not found', 404);
  if (!['paid', 'dispatched', 'delivered', 'refund_pending', 'disputed', 'refunded'].includes(o.status) || !o.payment_intent) throw new Bad('Only a paid order can be refunded', 409);
  const reason = String(b.reason || '').trim();
  if (reason.length < 3) throw new Bad('Give a reason for the refund');
  const tot = await refundTotals(env, o.id);
  if (b.commission_only) {   // after a lost dispute: the buyer was repaid by the dispute, PlotArt returns its commission
    if (o.dispute_status !== 'lost') throw new Bad('Commission-only refunds are for lost disputes', 409);
    const fee = Math.max(0, o.commission_cents - tot.fee);
    if (!fee) return { already: true, ...(await orderDetail(env, o, 'founder')) };
    return feeRefund(env, founder, o, { art: 0, del: 0, fee, reason });
  }
  const art = b.artwork_cents ?? 0, del = b.delivery_cents ?? 0;
  if (!Number.isInteger(art) || !Number.isInteger(del) || art < 0 || del < 0 || art + del === 0) throw new Bad('Give the refund amounts in whole cents');
  // refunds still waiting at Stripe count as already asked for, so two requests can never exceed what was paid
  const pend = await one(env, "SELECT COALESCE(SUM(artwork_cents), 0) AS art, COALESCE(SUM(delivery_cents), 0) AS del, COALESCE(SUM(commission_refund_cents), 0) AS fee FROM order_refunds WHERE order_id = ? AND status = 'pending'", o.id);
  if (tot.art + pend.art + art > o.artwork_cents) throw new Bad('That is more than the artwork amount still unrefunded', 409);
  if (tot.del + pend.del + del > o.delivery_cents) throw new Bad('That is more than the delivery amount still unrefunded', 409);
  const fee = R.commissionRefund({ artwork_cents: o.artwork_cents, commission_cents: o.commission_cents, artwork_refunded_before: tot.art + pend.art, artwork_refund_now: art, commission_refunded_before: tot.fee + pend.fee });
  const rr = { id: rid('rf'), t: now() };
  await run(env, `INSERT INTO order_refunds (id, order_id, artwork_cents, delivery_cents, commission_refund_cents, reason, status, requested_by, created_at, updated_at) VALUES (?,?,?,?,?,?, 'pending', ?,?,?)`,
    rr.id, o.id, art, del, fee, reason, founder, rr.t, rr.t);
  if (R.canMove(o.status, 'refund_pending') && o.status !== 'refund_pending') await move(env, o, 'refund_pending', founder, 'refund_requested', {}, { refund: rr.id, art, del, fee });
  let re;
  try {
    re = await S.refund(env, { account: o.provider_account, paymentIntent: o.payment_intent, amount: art + del, idem: `plotart-refund-${rr.id}`,
      metadata: { plotart_order: o.id, plotart_refund: rr.id, artwork_cents: art, delivery_cents: del } });
  } catch (e) {
    await run(env, "UPDATE order_refunds SET status = 'failed', error = ?, updated_at = ? WHERE id = ?", String(e.message).slice(0, 300), now(), rr.id);
    throw new Bad(`The refund was not made: ${e.message}`, 409);
  }
  await run(env, 'UPDATE order_refunds SET provider_refund_id = COALESCE(provider_refund_id, ?), updated_at = ? WHERE id = ?', re.id, now(), rr.id);
  const row = await one(env, 'SELECT * FROM order_refunds WHERE id = ?', rr.id);
  if (re.status === 'succeeded') return completeRefund(env, founder, row);
  if (['failed', 'canceled'].includes(re.status)) { await failRefund(env, row, re); return orderDetail(env, await getOrder(env, o.id), 'founder'); }
  // pending: for a card refund Stripe holds it when the artist's AVAILABLE Stripe balance cannot cover it (for example after
  // the payout), until the balance recovers; Stripe fails a pending refund after 45 days. Nothing is booked until it succeeds.
  await event(env, o.id, founder, 'refund_pending_at_provider', 'refund_pending', 'refund_pending', { refund: rr.id, provider_refund: re.id });
  await notify(env, o, 'refund_pending', `A refund of EUR ${((art + del) / 100).toFixed(2)} on PlotArt order ${o.reference} is waiting because the seller's Stripe balance cannot cover it yet. Stripe cancels it after 45 days if it is still unfunded.\n\n${REFUND_FUNDING_STEPS.join('\n')}`);
  await run(env, 'UPDATE checkout_orders SET needs_resolution = ?, updated_at = ? WHERE id = ?',
    `refund ${re.id} is pending at Stripe (usually the artist's available Stripe balance is too low, e.g. after payout). Ask the artist to top up their Stripe balance; Stripe fails pending refunds after 45 days.`, now(), o.id);
  return orderDetail(env, await getOrder(env, o.id), 'founder');
}
/* A refund confirmed by Stripe: book it, return PlotArt's commission share (GAA 9) and settle the order. Idempotent: the
   ledger is unique per (kind, refund id) and the commission refund uses an idempotency key per refund request. */
async function completeRefund(env, actor, rr) {
  const o = await getOrder(env, rr.order_id);
  await env.DB.batch([
    st(env, "UPDATE order_refunds SET status = 'succeeded', provider_refund_id = COALESCE(provider_refund_id, ?), updated_at = ? WHERE id = ?", rr.provider_refund_id, now(), rr.id),
    ...(rr.artwork_cents ? [ledgerSt(env, o.id, 'artwork_refund', -rr.artwork_cents, rr.provider_refund_id, rr.reason)] : []),
    ...(rr.delivery_cents ? [ledgerSt(env, o.id, 'delivery_refund', -rr.delivery_cents, rr.provider_refund_id, rr.reason)] : []),
  ]);
  if (o.needs_resolution && o.needs_resolution.includes(`refund ${rr.provider_refund_id} is pending`)) await run(env, 'UPDATE checkout_orders SET needs_resolution = NULL, updated_at = ? WHERE id = ?', now(), o.id);
  const cur = await one(env, 'SELECT fee_refund_id FROM order_refunds WHERE id = ?', rr.id);
  if (rr.commission_refund_cents > 0 && !cur.fee_refund_id) await feeRefund(env, actor, await getOrder(env, o.id), { fee: rr.commission_refund_cents, reason: rr.reason, refundId: rr.id, providerRefund: rr.provider_refund_id });
  return settleAfterRefund(env, actor, o.id);
}
async function failRefund(env, rr, re) {
  const cur = await one(env, 'SELECT * FROM order_refunds WHERE id = ?', rr.id);
  if (cur && cur.status === 'succeeded') return reverseRefund(env, cur, re);
  if (cur && cur.status === 'failed') return;   // already recorded
  await run(env, "UPDATE order_refunds SET status = 'failed', error = ?, updated_at = ? WHERE id = ? AND status <> 'succeeded'", String(re.failure_reason || re.status).slice(0, 200), now(), rr.id);
  await run(env, 'UPDATE checkout_orders SET needs_resolution = ?, updated_at = ? WHERE id = ?',
    `refund ${re.id} failed (${re.failure_reason || re.status}): the buyer has NOT been repaid; the artist, as seller, must repay them another way. No commission was returned.`, now(), rr.order_id);
  await event(env, rr.order_id, 'provider', 'refund_failed', null, null, { refund: rr.id, provider_refund: re.id, reason: re.failure_reason || re.status });
  await notify(env, await getOrder(env, rr.order_id), 'refund_failed', `Stripe could not complete a refund on PlotArt order ${(await getOrder(env, rr.order_id)).reference} (${re.failure_reason || re.status}). The buyer has NOT been repaid. The seller now repays the buyer directly and sends PlotArt the confirmation.`);
}
/* A refund that Stripe first reported SUCCEEDED and later FAILED (e.g. the card was closed): Stripe returns the money to
   the artist's balance and the buyer has NOT been repaid. Reconciliation, idempotent per refund:
     · the refund request becomes failed; the ledger keeps the original refund lines and adds positive *_reversed lines,
       so the amount counts as unrefunded again (nothing is deleted);
     · PlotArt's commission share returned for that refund is NOT taken back automatically (an application-fee refund
       cannot be undone through Stripe). Because it stays booked, a later refund or recorded repayment of the same amount
       returns no further commission;
     · the order goes back to its paid state with a flag naming the ONE route to repay the buyer: a new refund through the
       pilot, or the artist's direct repayment recorded with evidence. Whichever happens first uses up the amount, so the
       other is refused ("more than remains unrefunded"): the buyer cannot be repaid twice through the pilot. */
async function reverseRefund(env, rr, re) {
  const flip = await run(env, "UPDATE order_refunds SET status = 'failed', error = ?, updated_at = ? WHERE id = ? AND status = 'succeeded'",
    ('reversed by Stripe after succeeding: ' + (re.failure_reason || re.status)).slice(0, 200), now(), rr.id);
  if (!flip.meta.changes) return;   // another delivery already reversed it
  const o = await getOrder(env, rr.order_id), ref = rr.provider_refund_id || re.id;
  await env.DB.batch([
    ...(rr.artwork_cents ? [ledgerSt(env, o.id, 'artwork_refund_reversed', rr.artwork_cents, ref, `refund failed after succeeding (${re.failure_reason || re.status}): returned to the seller's Stripe balance`)] : []),
    ...(rr.delivery_cents ? [ledgerSt(env, o.id, 'delivery_refund_reversed', rr.delivery_cents, ref, `refund failed after succeeding (${re.failure_reason || re.status})`)] : []),
  ]);
  const tot = await refundTotals(env, o.id), repaid = tot.art + tot.del + tot.ext;
  const feeBack = rr.fee_refund_id ? rr.commission_refund_cents : 0;
  const eur = c => `EUR ${(c / 100).toFixed(2)}`;
  const flag = `refund ${ref} of ${eur(rr.artwork_cents + rr.delivery_cents)} SUCCEEDED and then FAILED (${re.failure_reason || re.status}): Stripe returned the money to the artist's balance and the buyer has NOT been repaid. `
    + (feeBack ? `PlotArt had already returned ${eur(feeBack)} commission for it; that stays returned, so repaying this amount again returns no further commission. ` : '')
    + 'Repay the buyer by ONE route only: a new refund through the pilot, OR the artist repays directly and the founder records it with evidence.';
  const back = o.fulfilment_status === 'delivered' ? 'delivered' : o.fulfilment_status === 'dispatched' ? 'dispatched' : 'paid';
  const sets = { payment_status: repaid > 0 ? 'partially_refunded' : 'paid', needs_resolution: flag };
  if (['refunded', 'refund_pending'].includes(o.status) && R.canMove(o.status, back)) await move(env, o, back, 'provider', 'refund_reversed', sets, { refund: rr.id, provider_refund: ref, reason: re.failure_reason || re.status });
  else { await run(env, 'UPDATE checkout_orders SET payment_status = ?, needs_resolution = ?, updated_at = ? WHERE id = ?', sets.payment_status, flag, now(), o.id); await event(env, o.id, 'provider', 'refund_reversed', o.status, o.status, { refund: rr.id, provider_refund: ref }); }
  await run(env, "UPDATE artwork_sales SET released_at = NULL, released_reason = NULL WHERE order_id = ? AND released_reason = 'fully refunded'", o.id);   // the buyer still holds the sale
  await notify(env, await getOrder(env, o.id), 'refund_reversed', `Stripe reversed a refund on PlotArt order ${o.reference} after first confirming it (${re.failure_reason || re.status}). The money is back in the seller's Stripe balance and the buyer has NOT been repaid. Repay the buyer by one route only: a new refund through PlotArt, or a direct repayment by the seller that PlotArt records with evidence.`);
}
/* Backstop for missed events: a refund can fail days after succeeding, so recently succeeded refunds are re-read. */
export const RECHECK_SUCCEEDED_REFUND_DAYS = 14;
async function recheckSucceededRefunds(env) {
  const since = new Date(Date.now() - RECHECK_SUCCEEDED_REFUND_DAYS * 864e5).toISOString();
  let reversed = 0;
  for (const rr of await all(env, "SELECT r.*, o.provider_account FROM order_refunds r JOIN checkout_orders o ON o.id = r.order_id WHERE r.status = 'succeeded' AND r.provider_refund_id LIKE 're_%' AND r.updated_at >= ? ORDER BY r.updated_at DESC LIMIT 25", since)) {
    try { const re = await S.getRefund(env, { account: rr.provider_account, id: rr.provider_refund_id }); if (['failed', 'canceled'].includes(re.status)) { await reverseRefund(env, rr, re); reversed++; } } catch { /* next sweep */ }
  }
  return reversed;
}
async function feeRefund(env, founder, o, { fee, reason, refundId = null, providerRefund = null }) {
  let feeId = o.application_fee_id;
  if (!feeId) {
    const p = await S.getPaymentIntent(env, { account: o.provider_account, id: o.payment_intent });
    const ch = p.latest_charge && typeof p.latest_charge === 'object' ? p.latest_charge : null;
    feeId = ch && (typeof ch.application_fee === 'string' ? ch.application_fee : ch.application_fee && ch.application_fee.id);
    if (feeId) await run(env, 'UPDATE checkout_orders SET application_fee_id = ?, charge_id = COALESCE(charge_id, ?), updated_at = ? WHERE id = ?', feeId, ch.id, now(), o.id);
  }
  if (!feeId) {
    await run(env, 'UPDATE checkout_orders SET needs_resolution = ?, updated_at = ? WHERE id = ?', `commission refund of ${fee} cents still due (application fee not yet available)`, now(), o.id);
    return orderDetail(env, await getOrder(env, o.id), 'founder');
  }
  const idem = `plotart-feerefund-${refundId || o.id + '-commission-' + fee}`;
  const fr = await S.refundFee(env, { fee: feeId, amount: fee, idem, metadata: { plotart_order: o.id, reason: reason.slice(0, 200) } });
  await env.DB.batch([ledgerSt(env, o.id, 'commission_refund', -fee, fr.id, reason),
    ...(refundId ? [st(env, 'UPDATE order_refunds SET fee_refund_id = ?, updated_at = ? WHERE id = ?', fr.id, now(), refundId)] : []),
    evSt(env, o.id, founder, 'commission_refunded', o.status, o.status, { amount: fee, fee_refund: fr.id, refund: providerRefund })]);
  if (!refundId) await run(env, "UPDATE checkout_orders SET needs_resolution = NULL, updated_at = ? WHERE id = ? AND needs_resolution LIKE 'dispute lost%'", now(), o.id);
  return orderDetail(env, await getOrder(env, o.id), 'founder');
}
async function settleAfterRefund(env, founder, id) {
  const o = await getOrder(env, id), tot = await refundTotals(env, id);
  if (await one(env, "SELECT 1 AS x FROM order_refunds WHERE order_id = ? AND status = 'pending'", id)) return orderDetail(env, o, 'founder');
  const full = tot.art + tot.del + tot.ext >= o.amount_received_cents;
  if (full) {
    if (R.canMove(o.status, 'refunded')) await move(env, o, 'refunded', founder, 'refunded', { payment_status: 'refunded', needs_resolution: null });
    // a fully refunded sale no longer holds the original; the artist decides when (and whether) to offer it again
    await run(env, "UPDATE artwork_sales SET released_at = ?, released_reason = 'fully refunded' WHERE order_id = ? AND released_at IS NULL", now(), id);
  } else {
    await run(env, "UPDATE checkout_orders SET payment_status = 'partially_refunded', updated_at = ? WHERE id = ?", now(), id);
    if (o.status === 'refund_pending') {
      const back = o.fulfilment_status === 'delivered' ? 'delivered' : o.fulfilment_status === 'dispatched' ? 'dispatched' : 'paid';
      await move(env, o, back, founder, 'partial_refund_done', {}, null);
    }
  }
  return orderDetail(env, await getOrder(env, id), 'founder');
}

/* After an interruption: ask the provider for the session's real state and apply it exactly as a verified event would. */
export async function reconcile(env, founder, id) {
  await requireInstalled(env); requireOn(env);
  const o = await getOrder(env, id);
  if (!o) throw new Bad('Not found', 404);
  const sessions = await all(env, "SELECT * FROM checkout_sessions WHERE order_id = ? ORDER BY created_at", o.id);
  const out = [];
  for (const s of sessions) {
    const cur = await S.getSession(env, { account: o.provider_account, id: s.id });
    const synthetic = { id: `reconcile:${s.id}`, account: o.provider_account };
    if (cur.status === 'complete' && cur.payment_status === 'paid') out.push(`${s.id}: ${await recordPaid(env, await getOrder(env, o.id), cur, synthetic.id)}`);
    else if (cur.status === 'expired') { await apply(env, { ...synthetic, type: 'checkout.session.expired' }, cur); out.push(`${s.id}: expired`); }
    else out.push(`${s.id}: ${cur.status}`);
  }
  await event(env, o.id, founder, 'reconciled', o.status, (await getOrder(env, o.id)).status, { result: out });
  return { result: out, ...(await orderDetail(env, await getOrder(env, id), 'founder')) };
}

/* ---------------------------------------------------------------- fulfilment */
export async function fulfilment(env, actor, role, o, b) {
  await requireInstalled(env);
  const kind = String(b.kind || ''), evidence = String(b.evidence || '').trim();
  if (!['insurance', 'dispatched', 'delivered', 'signed_receipt', 'condition_photos', 'tracking', 'note'].includes(kind)) throw new Bad('Choose what you are recording');
  if (evidence.length < 2 || evidence.length > 2000) throw new Bad('Describe the evidence (tracking number, receipt, photo reference) in up to 2,000 characters');
  if (!['paid', 'dispatched', 'delivered', 'disputed', 'refund_pending'].includes(o.status)) throw new Bad('Fulfilment is recorded only for a paid order', 409);
  if (kind === 'delivered' && o.fulfilment_status === 'none') throw new Bad('Record the dispatch first', 409);
  // initial pilot: no dispatch without evidence that the quoted transit insurance is in place for THIS shipment
  if (kind === 'dispatched' && !(await one(env, "SELECT 1 AS x FROM order_fulfilment_events WHERE order_id = ? AND kind = 'insurance'", o.id)))
    throw new Bad('Record the transit insurance confirmation for this shipment (policy or certificate reference, insurer, insured value) before dispatch', 409);
  await run(env, 'INSERT INTO order_fulfilment_events (id, order_id, kind, actor, at, evidence) VALUES (?,?,?,?,?,?)', rid('f'), o.id, kind, `${role}:${actor}`, now(), evidence);
  if (kind === 'dispatched' && o.fulfilment_status === 'none') {
    await run(env, "UPDATE checkout_orders SET fulfilment_status = 'dispatched', updated_at = ? WHERE id = ?", now(), o.id);
    if (o.status === 'paid') await move(env, o, 'dispatched', `${role}:${actor}`, 'dispatched');
  } else if (kind === 'delivered' && o.fulfilment_status !== 'delivered') {
    await run(env, "UPDATE checkout_orders SET fulfilment_status = 'delivered', updated_at = ? WHERE id = ?", now(), o.id);
    const cur = await getOrder(env, o.id);
    if (cur.status === 'dispatched') await move(env, cur, 'delivered', `${role}:${actor}`, 'delivered');
  } else await event(env, o.id, `${role}:${actor}`, 'fulfilment_' + kind, o.status, o.status, null);
  return orderDetail(env, await getOrder(env, o.id), role);
}
export async function closeOrder(env, founder, id) {
  const o = await getOrder(env, id);
  if (!o) throw new Bad('Not found', 404);
  if (o.needs_resolution) throw new Bad('Resolve the flagged issue first: ' + o.needs_resolution, 409);
  if (o.status === 'delivered' || o.status === 'refunded') return orderDetail(env, await move(env, o, 'closed', founder, 'closed'), 'founder');
  throw new Bad('Close an order once it is delivered or refunded', 409);
}

/* ---------------------------------------------------------------- scheduled clean-up */
export async function sweep(env) {
  if (!(await installed(env))) return null;
  const t = now();
  const released = await run(env, `DELETE FROM artwork_reservations WHERE expires_at < ? AND order_id NOT IN (SELECT order_id FROM checkout_sessions WHERE status = 'open' AND expires_at >= ?)`, t, t);
  let expired = 0;
  for (const o of await all(env, `SELECT * FROM checkout_orders WHERE status IN ('quoted','payment_failed') AND quote_expires_at <= ?`, t)) {
    try { await move(env, o, 'expired', 'scheduler', 'quote_expired'); expired++; } catch { /* moved meanwhile */ }
  }
  let deferred_replayed = 0;
  try { deferred_replayed = await replayDeferred(env); } catch { /* next sweep */ }
  let refunds_reversed = 0;
  try { refunds_reversed = await recheckSucceededRefunds(env); } catch { /* next sweep */ }
  let refunds = null;
  try { refunds = await pollPendingRefunds(env); } catch (e) { refunds = { error: String(e.message || e).slice(0, 120) }; }
  return { reservations_released: released.meta.changes, quotes_expired: expired, deferred_replayed, refunds_reversed, ...refunds, ...(await retention(env)) };
}

/* Retention (spec "Records and retention"). Each period has a stated basis and a fixed start; nothing is ever deleted
   while a legal hold is active, and holds — not retention dates — are how records are kept longer for a specific reason.
     · An order that moved money (paid, refunded, disputed): kept until 31 December of the SIXTH year after the year of its
       last money movement (payment, refund, commission refund, dispute). Basis: Irish tax record-keeping (records kept six
       years; PA-GAA cl. 18.3 makes the same commitment for commission records) and the six-year limitation period for
       contract claims. Starting from the end of the year covers both "six years from the transaction" and "six years after
       the end of the period" readings.
     · An order that never moved money (draft, cancelled, expired): two years after it ended, for questions and
       complaints about the quote — the same as PlotArt enquiry records (24 months, privacy notice).
     · Provider events linked to an order go with that order; events linked to no order: 90 days (operations only).
   The date is fixed once set: it cannot be shortened or extended. Deletion is done by the sweep, order by order, in one
   transaction, and only for orders with no open issue, no pending refund and no active hold. Database backups follow
   their own (shorter) rotation, so deleted rows leave the backups as they age out. */
export const RETAIN_PAID_YEARS = 6, RETAIN_UNPAID_YEARS = 2, RETAIN_UNLINKED_EVENT_DAYS = 90;
const plusYears = (iso, y) => { const d = new Date(iso); d.setUTCFullYear(d.getUTCFullYear() + y); return d.toISOString(); };
export function retentionDate({ moneyMoved, lastMoneyAt, endedAt }) {
  if (moneyMoved) return `${new Date(lastMoneyAt).getUTCFullYear() + RETAIN_PAID_YEARS}-12-31T23:59:59.000Z`;
  return plusYears(endedAt, RETAIN_UNPAID_YEARS);
}
export async function retention(env, at = now()) {
  let scheduled = 0, purged = 0, held = 0;
  for (const o of await all(env, `SELECT id, status, payment_status, updated_at FROM checkout_orders WHERE retain_until IS NULL AND needs_resolution IS NULL
      AND (status IN ('closed', 'refunded') OR (status IN ('cancelled', 'expired') AND payment_status = 'none'))
      AND NOT EXISTS (SELECT 1 FROM order_refunds r WHERE r.order_id = checkout_orders.id AND r.status = 'pending')`)) {
    const last = await one(env, 'SELECT MAX(at) AS at FROM order_ledger WHERE order_id = ?', o.id);
    const moneyMoved = !!(last && last.at);
    await run(env, 'UPDATE checkout_orders SET retain_until = ? WHERE id = ? AND retain_until IS NULL',
      retentionDate({ moneyMoved, lastMoneyAt: moneyMoved ? (last.at > o.updated_at ? last.at : o.updated_at) : null, endedAt: o.updated_at }), o.id);
    scheduled++;
  }
  for (const o of await all(env, 'SELECT id FROM checkout_orders WHERE retain_until IS NOT NULL AND retain_until <= ?', at)) {
    if (await one(env, 'SELECT 1 AS x FROM checkout_holds WHERE order_id = ? AND released_at IS NULL', o.id)) { held++; continue; }
    await env.DB.batch(['order_events', 'order_fulfilment_events', 'order_refunds', 'order_ledger', 'checkout_sessions', 'artwork_reservations', 'artwork_sales', 'payment_events', 'checkout_hold_events', 'checkout_holds']
      .map(t => st(env, `DELETE FROM ${t} WHERE order_id = ?`, o.id)).concat([st(env, 'DELETE FROM checkout_orders WHERE id = ?', o.id)]));
    purged++;
  }
  await run(env, 'DELETE FROM payment_events WHERE order_id IS NULL AND received_at <= ?', new Date(Date.parse(at) - RETAIN_UNLINKED_EVENT_DAYS * 86400_000).toISOString());
  // an artist's opt-in/consent records and Stripe account link: six years after they left the pilot, once none of their orders is kept
  let artists = 0;
  for (const a of await all(env, `SELECT e.artist_id FROM payment_pilot_events e WHERE e.kind = 'left' AND e.at <= ?
      AND e.at = (SELECT MAX(x.at) FROM payment_pilot_events x WHERE x.artist_id = e.artist_id AND x.kind IN ('opted_in', 'left'))
      AND NOT EXISTS (SELECT 1 FROM checkout_orders o WHERE o.artist_id = e.artist_id)`, plusYears(at, -RETAIN_PAID_YEARS))) {
    await env.DB.batch([st(env, 'DELETE FROM payment_pilot_events WHERE artist_id = ?', a.artist_id), st(env, 'DELETE FROM payment_accounts WHERE artist_id = ?', a.artist_id)]);
    artists++;
  }
  return { orders_scheduled_for_deletion: scheduled, orders_deleted: purged, deletion_held: held, artist_pilot_records_deleted: artists };
}

/* ---------------------------------------------------------------- legal holds
   A hold keeps one order's records past its retention date for a stated reason (dispute, claim, Revenue enquiry or
   investigation, litigation, a data-subject request being handled). Every hold has a review date no more than 12 months
   ahead. At review the founder either releases it (with a reason) or renews it to a new review date (with a reason);
   overdue reviews are flagged and nothing is renewed or released automatically. Once released, the ordinary retention
   date applies again, so records past it are deleted at the next sweep. Every placement, review and release is recorded. */
export const HOLD_BASES = ['dispute', 'claim', 'revenue_enquiry', 'investigation', 'litigation', 'data_subject_request', 'other'];
const MAX_REVIEW_DAYS = 366;
function reviewDate(v) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(v || ''))) throw new Bad('Give a review date (YYYY-MM-DD)');
  const t = Date.parse(v + 'T00:00:00Z');
  if (t <= Date.now() || t > Date.now() + MAX_REVIEW_DAYS * 86400_000) throw new Bad('A review date must be in the next 12 months');
  return v;
}
export async function placeHold(env, founder, orderId, b) {
  await requireInstalled(env);
  if (!(await getOrder(env, orderId))) throw new Bad('Not found', 404);
  if (!HOLD_BASES.includes(b.basis)) throw new Bad('Choose the basis for the hold');
  const reason = String(b.reason || '').trim();
  if (reason.length < 10 || reason.length > 1000) throw new Bad('Give the specific reason for the hold (10–1,000 characters)');
  const id = rid('h'), t = now(), rv = reviewDate(b.review_by);
  await env.DB.batch([
    st(env, 'INSERT INTO checkout_holds (id, order_id, basis, reason, placed_by, placed_at, review_by) VALUES (?,?,?,?,?,?,?)', id, orderId, b.basis, reason, founder, t, rv),
    st(env, "INSERT INTO checkout_hold_events (id, hold_id, order_id, kind, actor, at, note, review_by) VALUES (?,?,?, 'placed', ?,?,?,?)", rid('he'), id, orderId, founder, t, reason, rv)]);
  return { hold: await one(env, 'SELECT * FROM checkout_holds WHERE id = ?', id) };
}
export async function reviewHold(env, founder, holdId, b) {
  await requireInstalled(env);
  const h = await one(env, 'SELECT * FROM checkout_holds WHERE id = ? AND released_at IS NULL', holdId);
  if (!h) throw new Bad('No active hold', 404);
  const note = String(b.note || '').trim(), t = now();
  if (note.length < 10) throw new Bad('Record why (10 characters or more)');
  if (b.decision === 'release') {
    await env.DB.batch([st(env, 'UPDATE checkout_holds SET released_at = ?, released_by = ?, release_reason = ? WHERE id = ? AND released_at IS NULL', t, founder, note, holdId),
      st(env, "INSERT INTO checkout_hold_events (id, hold_id, order_id, kind, actor, at, note) VALUES (?,?,?, 'released', ?,?,?)", rid('he'), holdId, h.order_id, founder, t, note)]);
  } else if (b.decision === 'renew') {
    const rv = reviewDate(b.review_by);
    await env.DB.batch([st(env, 'UPDATE checkout_holds SET review_by = ? WHERE id = ? AND released_at IS NULL', rv, holdId),
      st(env, "INSERT INTO checkout_hold_events (id, hold_id, order_id, kind, actor, at, note, review_by) VALUES (?,?,?, 'renewed', ?,?,?,?)", rid('he'), holdId, h.order_id, founder, t, note, rv)]);
  } else throw new Bad('Choose release or renew');
  return { hold: await one(env, 'SELECT * FROM checkout_holds WHERE id = ?', holdId), history: await all(env, 'SELECT kind, actor, at, note, review_by FROM checkout_hold_events WHERE hold_id = ? ORDER BY at, rowid', holdId) };
}
async function holdsView(env) {
  const today = now().slice(0, 10);
  return (await all(env, `SELECT h.*, o.reference, o.retain_until FROM checkout_holds h JOIN checkout_orders o ON o.id = h.order_id WHERE h.released_at IS NULL ORDER BY h.review_by`))
    .map(h => ({ ...h, review_overdue: h.review_by < today, past_retention: !!h.retain_until && h.retain_until <= now() }));
}
