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

import { Bad } from './lib.js';
import { send } from './mailer.js';
export { Bad };
const now = () => new Date().toISOString();
const rid = (p = '', n = 12) => p + [...crypto.getRandomValues(new Uint8Array(n))].map(b => (b % 36).toString(36)).join('');
const all = async (env, sql, ...b) => (await env.DB.prepare(sql).bind(...b).all()).results;
const one = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).first();
const run = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).run();
const st = (env, sql, ...b) => env.DB.prepare(sql).bind(...b);
const J = s => (s ? JSON.parse(s) : null);
const sha256 = async s => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)))].map(b => b.toString(16).padStart(2, '0')).join('');
const plusDays = (iso, d) => new Date(Date.parse(iso) + d * 86400_000).toISOString();
const addMin = (iso, m) => new Date(Date.parse(iso) + m * 60_000).toISOString();

export const STATEMENT = doc => `I have read and accept the PlotArt Payment Pilot Addendum ${doc}. I understand that taking part is optional, that I remain the seller of my artwork, that payments are made to my own Stripe account, that Stripe deducts its processing fees from my Stripe balance, that PlotArt's commission (if any) applies only as my existing agreement provides and never to delivery charges, and that I can leave the pilot at any time.`;

/* Separate, explicit consent to the processing charge (founder decision 16 Nov 2026). On an order where PlotArt takes no
   commission (every Founding Enquiry, and Founding Artists without commission terms), Stripe's processing fees would be
   the only deduction and would fall on the artist. Direct payment, with no deduction at all, stays the artist's normal
   route; the pilot can be used for such an order only after this separate, withdrawable consent. It is never implied by
   joining the pilot, and never part of any agreement acceptance. */
export const PROCESSING_STATEMENT = `I agree that, on payment-pilot orders where PlotArt takes no commission, Stripe deducts its card processing fees from my Stripe balance (for example about 1.5% + €0.25 of the amount paid for a standard EEA card, more for premium, UK and international cards). I understand this is optional: I can always sell directly instead, with no deduction at all, and I can withdraw this consent at any time.`;

/* ---------------------------------------------------------------- deadlines (configurable; provisional until the founder approves them) */
const intEnv = (env, k, d) => { const n = Number(env[k]); return Number.isInteger(n) && n > 0 && n <= 365 ? n : d; };
/* Founder decisions on the two deadlines, recorded separately (18 Nov 2026). CHECKOUT_DEADLINES_APPROVED covered both at
   once and is left unset and no longer read: each deadline is approved only by its own entry here. */
export const DEADLINE_DECISIONS = {
  reimburse_days: { clause: 'PA-PAY 3.3', value: 7, unit: 'Irish calendar days', status: 'approved_for_sandbox_pilot', decided_by: 'founder', decided_at: '2026-11-18T09:30:00Z',
    scope: 'Sandbox pilot rule for the processing-fee reimbursement only. Artist terms remain draft and unissued.' },
  shortfall_days: { clause: 'PA-PAY 3.5', value: 30, unit: 'Irish calendar days', status: 'approved_for_sandbox_pilot', decided_by: 'founder', decided_at: '2026-11-18T09:40:00Z',
    scope: 'Sandbox pilot rule for bank-transfer payment of processing-fee and commission-return shortfalls: 30 Irish calendar days from the Irish date of the transaction record that first established the amount. Artist terms remain draft and unissued.' },
};
const approved = (k, v) => DEADLINE_DECISIONS[k].status === 'approved_for_sandbox_pilot' && DEADLINE_DECISIONS[k].value === v;
export function deadlines(env) {
  const reimburse_days = intEnv(env, 'CHECKOUT_REIMBURSE_DAYS', 7), shortfall_days = intEnv(env, 'CHECKOUT_SHORTFALL_DAYS', 30);
  const reimburse_provisional = !approved('reimburse_days', reimburse_days), shortfall_provisional = !approved('shortfall_days', shortfall_days);
  return { reimburse_days, shortfall_days, reimburse_provisional, shortfall_provisional,
    provisional: shortfall_provisional,   // the bank-transfer (shortfall) deadline; kept under this name for the owed queue
    reminder_days_before: intEnv(env, 'CHECKOUT_OWED_REMINDER_DAYS', 7), lost_dispute_commission_days: 30, decisions: DEADLINE_DECISIONS,
    note: `Processing reimbursement (PA-PAY 3.3): ${reimburse_days} Irish calendar days${reimburse_provisional ? ', provisional' : ', approved by the founder as the sandbox pilot rule on 18 Nov 2026'}. Bank-transfer shortfall (PA-PAY 3.5): ${shortfall_days} Irish calendar days${shortfall_provisional ? ', provisional' : ', approved by the founder as the sandbox pilot rule on 18 Nov 2026'}. Lost-dispute commission: the existing PA-GAA cl. 9.1 period (30 days).` };
}

/* ---------------------------------------------------------------- messages: test sink unless sending is configured AND approved
   Default: every message (buyer confirmations and notices, artist and founder notices) goes to checkout_mail_sink, which
   keeps only a fingerprint of the intended address. A sink entry is NOT an email delivery and is never reported as one.
   External sending uses the project's existing Resend integration (mailer.js) and happens only when ALL of these hold:
     CHECKOUT_MAIL = 'resend', CHECKOUT_MAIL_APPROVED = 'true', RESEND_API_KEY and CHECKOUT_MAIL_FROM are set, and
     while the pilot uses a Stripe TEST key the recipient is on CHECKOUT_MAIL_TEST_RECIPIENTS (the founder's own test
     inboxes). With a live key nothing is sent externally: live sending is not part of this pilot.
   'accepted_by_provider' means Resend accepted the message; it is not proof that it reached the inbox.
   CHECKOUT_MAIL = 'none' records that nothing was sent. */
export function mailMode(env) {
  const mode = env.CHECKOUT_MAIL || 'sink';
  const configured = mode === 'resend' && !!env.RESEND_API_KEY && !!env.CHECKOUT_MAIL_FROM;
  const approved = configured && env.CHECKOUT_MAIL_APPROVED === 'true';
  const testKey = /^(sk|rk)_test_/.test(env.STRIPE_SECRET_KEY || '');
  const allow = String(env.CHECKOUT_MAIL_TEST_RECIPIENTS || '').split(',').map(x => x.trim().toLowerCase()).filter(Boolean);
  return { mode, configured, approved, test_key: testKey, test_recipients: allow.length, external_sending: approved && testKey && allow.length > 0,
    summary: !configured ? (mode === 'none' ? 'Nothing is sent (CHECKOUT_MAIL = none).' : 'Test sink only: no email provider is configured for the pilot.')
      : !approved ? 'Resend is configured but sending is not approved (CHECKOUT_MAIL_APPROVED): test sink only.'
      : !testKey ? 'Live key detected: live sending is not part of this pilot; test sink only.'
      : `Sending only to ${allow.length} approved test address(es); everything else goes to the test sink.`, _allow: allow };
}
async function deliver(env, { orderId = null, kind, toRole, to, subject, body, idempotencyKey = null }) {
  const m = mailMode(env), addr = String(to || '').trim().toLowerCase();
  if (m.mode === 'none') return { channel: 'none', status: 'not_sent_no_provider', detail: 'no mail provider configured' };
  if (m.external_sending && m._allow.includes(addr)) {
    const r = await send({ ...env, MAILER: 'resend', MAIL_FROM: env.CHECKOUT_MAIL_FROM }, { to: addr, replyTo: 'hello@plotnua.ie', subject, text: body, idempotencyKey });
    return r.sent ? { channel: 'provider', status: 'accepted_by_provider', detail: 'accepted by Resend (not proof of inbox delivery)' } : { channel: 'provider', status: 'failed', detail: String(r.detail).slice(0, 200) };
  }
  if (env.CHECKOUT_MAIL_SINK_BROKEN === 'true' && env.ENVIRONMENT === 'local') throw new Error('test sink unavailable (local failure test)');
  await run(env, 'INSERT INTO checkout_mail_sink (at, order_id, kind, to_role, to_sha256, subject, body) VALUES (?,?,?,?,?,?,?)',
    now(), orderId, kind, toRole, await sha256(addr), subject, body);
  return { channel: 'test_sink', status: 'held_in_test_sink', detail: `test sink only, NOT delivered by email (${m.summary})` };
}

/* ---------------------------------------------------------------- seller information (artist-maintained; snapshotted into each quote) */
const SELLER_FIELDS = { legal_name: [2, 200, true], trading_name: [0, 200, false], address: [10, 400, true], returns_address: [0, 400, false],
  email: [5, 200, true], phone: [6, 40, true], vat_number: [0, 30, false] };
export const SELLER_DECLARATION = 'I confirm that this seller information is accurate and that buyers will be shown it on each quote, and I will keep it up to date.';
export async function sellerProfile(env, artistId) { return one(env, 'SELECT * FROM seller_profiles WHERE artist_id = ?', artistId); }
export async function saveSellerProfile(env, artist, b) {
  await requireInstalled(env);
  if (!(await membership(env, artist.id)).opted_in) throw new Bad('Join the payment pilot first', 409);
  const v = {};
  for (const [k, [min, max, req]] of Object.entries(SELLER_FIELDS)) {
    const x = String((b && b[k]) ?? '').trim();
    if (!x && !req) { v[k] = null; continue; }
    if (x.length < min || x.length > max) throw new Bad(`Seller information: ${k.replace(/_/g, ' ')} is required (${min}–${max} characters)`, 400);
    v[k] = x;
  }
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v.email)) throw new Bad('Seller information: give a valid email address', 400);
  if (!/^[+0-9 ()-]{6,40}$/.test(v.phone)) throw new Bad('Seller information: give a valid telephone number', 400);
  if (!['trader', 'not_trader'].includes(b && b.trader_status)) throw new Bad('Seller information: say whether you sell as a trader (in the course of your business, craft or profession)', 400);
  if (!b || b.confirm !== true) throw new Bad(SELLER_DECLARATION, 400);
  const t = now();
  await run(env, `INSERT INTO seller_profiles (artist_id, legal_name, trading_name, address, returns_address, email, phone, trader_status, vat_number, declared_at, declared_by, updated_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(artist_id) DO UPDATE SET legal_name = excluded.legal_name, trading_name = excluded.trading_name, address = excluded.address,
    returns_address = excluded.returns_address, email = excluded.email, phone = excluded.phone, trader_status = excluded.trader_status, vat_number = excluded.vat_number,
    declared_at = excluded.declared_at, declared_by = excluded.declared_by, updated_at = excluded.updated_at`,
    artist.id, v.legal_name, v.trading_name, v.address, v.returns_address, v.email, v.phone, b.trader_status, v.vat_number, t, artist.email, t);
  return { seller_profile: await sellerProfile(env, artist.id) };
}
/* F2 (open founder decision): by default only sellers who declare they sell as traders can be quoted, because buyers from a
   non-trader lose EU consumer rights. CHECKOUT_ALLOW_NON_TRADER_SELLERS = 'true' would allow them (PA-BPT 1.2 alternative). */
function sellerProblems(env, p) {
  if (!p) return ['the artist has not given their seller information (Payment pilot page)'];
  const out = Object.entries(SELLER_FIELDS).filter(([k, [, , req]]) => req && !p[k]).map(([k]) => k.replace(/_/g, ' '));
  if (p.trader_status === 'not_trader' && env.CHECKOUT_ALLOW_NON_TRADER_SELLERS !== 'true') out.push('the artist declared they do not sell as a trader, and the pilot currently quotes only sellers who do (founder decision F2)');
  return out;
}
const profileHash = p => sha256(JSON.stringify(['legal_name', 'trading_name', 'address', 'returns_address', 'email', 'phone', 'trader_status', 'vat_number'].map(k => p[k] ?? null)));
const looksLikeBankDetails = s => { const x = String(s || '').replace(/\s/g, ''); return /[A-Z]{2}\d{2}[A-Z0-9]{10,30}/i.test(x) && /\d{6,}/.test(x) || /\d{9,}/.test(x); };

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
    seller_profile: await sellerProfile(env, artist.id), seller_declaration: SELLER_DECLARATION, seller_problems: sellerProblems(env, await sellerProfile(env, artist.id)),
    processing_statement: PROCESSING_STATEMENT, direct_payment_note: 'Selling directly, with the buyer paying you, remains your normal route. The payment pilot is optional for every sale.',
    pending_refunds: (await pendingRefunds(env, artist.id)).map(r => ({ ...r, what_to_do: REFUND_FUNDING_STEPS })),
    orders: await withStatements(env, await all(env, 'SELECT * FROM checkout_orders WHERE artist_id = ? ORDER BY created_at DESC LIMIT 100', artist.id), 'artist') };
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
/* Fee Model B (founder decision, 17 Nov 2026): orders with no PlotArt commission — including every Founding Enquiry —
   stay on direct payment. They are not taken through the managed checkout in this implementation. */
function requireCommissionBearing(commissionBp) {
  if (!(commissionBp > 0)) throw new Bad('Orders with no PlotArt commission (including every Founding Enquiry) stay on direct payment between the artist and the buyer; they are not taken through the payment pilot.', 409);
}
function requireProcessingConsent(mem, commissionBp) {
  requireCommissionBearing(commissionBp);
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
  await run(env, 'DELETE FROM seller_profiles WHERE artist_id = ?', artist.id);   // each issued quote keeps its own copy
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
    paid_at: o.paid_at, created_at: o.created_at, updated_at: o.updated_at,
    processing_fees: 'Deducted by Stripe from the seller’s Stripe balance. On an order with PlotArt commission, PlotArt reimburses Stripe’s actual processing fee and the VAT on it from its commission (see statement).',
    processing: (({ stripe_fee, vat, cost, reimbursed_cents, status, excluded_fees, excluded_vat, descriptions } = J(o.processing) || {}) =>
      ({ stripe_fee, vat, cost, reimbursed_cents, status, excluded_fees, excluded_vat, descriptions }))(),
    dispute_fees: J(o.dispute_fees), quote_sha256: o.quote_sha256 };
  if (role === 'founder') Object.assign(v, { artist_id: o.artist_id, entitlement: J(o.entitlement), exclusion: o.exclusion, negotiation_note: o.negotiation_note,
    buyer_email: o.buyer_email, provider_account: o.provider_account, payment_intent: o.payment_intent, charge_id: o.charge_id, application_fee_id: o.application_fee_id });
  return v;
}
/* Order list with each paid order's statement (one ledger query for the whole list). */
async function owedForStatements(env, ids) {
  if (!ids.length) return {};
  const qs = ids.map(() => '?').join(','), by = {};
  const pays = await all(env, `SELECT p.owed_id, p.cents, p.method, p.reference, p.executed_on, r.returned_on FROM checkout_owed_payments p LEFT JOIN checkout_owed_payment_returns r ON r.payment_id = p.id
    WHERE p.order_id IN (${qs}) ORDER BY p.at, p.rowid`, ...ids);
  for (const w of await all(env, `SELECT id, order_id, kind, cents, settled_cents, due_at, due_basis_date FROM checkout_owed WHERE order_id IN (${qs})`, ...ids))
    (by[w.order_id] = by[w.order_id] || []).push({ ...w, payments: pays.filter(p => p.owed_id === w.id) });
  return by;
}
async function withStatements(env, rows, role) {
  const paid = rows.filter(o => o.payment_intent).map(o => o.id), by = {}, ow = {};
  if (paid.length) {
    const qs = paid.map(() => '?').join(',');
    for (const l of await all(env, `SELECT order_id, kind, amount_cents FROM order_ledger WHERE order_id IN (${qs})`, ...paid)) (by[l.order_id] = by[l.order_id] || []).push(l);
    Object.assign(ow, await owedForStatements(env, paid));
  }
  return rows.map(o => ({ ...orderView(o, role), statement: o.payment_intent ? statement(o, by[o.id] || [], ow[o.id] || []) : null }));
}
export async function orderDetail(env, o, role) {
  return { order: orderView(o, role), events: await all(env, 'SELECT at, actor, action, prior_status, new_status, detail FROM order_events WHERE order_id = ? ORDER BY id', o.id),
    ledger: await all(env, 'SELECT kind, amount_cents, provider_ref, at, note FROM order_ledger WHERE order_id = ? ORDER BY at, rowid', o.id),
    statement: statement(o, await all(env, 'SELECT kind, amount_cents FROM order_ledger WHERE order_id = ?', o.id), (await owedForStatements(env, [o.id]))[o.id] || []),
    owed: await owedRows(env, 'o.id = ?', o.id),
    messages: await all(env, 'SELECT id, kind, item_key, recipient_role, subject, sha256, created_at FROM order_messages WHERE order_id = ? ORDER BY created_at', o.id),
    mail: (({ summary, external_sending }) => ({ summary, external_sending }))(mailMode(env)),
    message_deliveries: await all(env, 'SELECT message_id, at, channel, status, detail FROM order_message_deliveries WHERE order_id = ? ORDER BY id', o.id),
    quote_snapshot: await quoteSnapshot(env, o),
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
    orders: await withStatements(env, await all(env, 'SELECT * FROM checkout_orders ORDER BY created_at DESC LIMIT 200'), 'founder'),
    unprocessed_events: await all(env, "SELECT event_id, type, status, attempts, detail, received_at FROM payment_events WHERE status IN ('deferred','failed','received') ORDER BY received_at LIMIT 50"),
    pending_refunds: await pendingRefunds(env), holds: await holdsView(env), refund_funding_steps: REFUND_FUNDING_STEPS,
    owed: await owedRows(env, 'w.settled_cents < w.cents'), owed_settled_recently: await owedRows(env, "w.settled_cents = w.cents AND w.arisen_at >= ?", plusDays(now(), -90)),
    reimbursements: await reimbursementsView(env, "(processing IS NULL OR json_extract(processing, '$.status') IN ('awaiting_fee','outstanding'))"),
    reimbursements_recent: await reimbursementsView(env, "json_extract(processing, '$.status') IN ('reimbursed','shortfall') AND updated_at >= ?", plusDays(now(), -30)),
    deadlines: deadlines(env), bank_details_process: BANK_DETAILS_PROCESS };
}

/* Founder desk: processing reimbursements (status, amount when known, due date, alerts, failures, evidence basis). */
export const REIMBURSEMENT_STATUS = {
  awaiting_fee: 'Waiting for Stripe to record the fee',
  outstanding: 'Fee known · reimbursement outstanding',
  reimbursed: 'Reimbursed · Stripe accepted the application-fee refund',
  shortfall: 'Reimbursed in part through Stripe · the rest is owed by bank transfer (Amounts owed)',
};
async function reimbursementsView(env, where, ...b) {
  const days = deadlines(env).reimburse_days, prov = deadlines(env).reimburse_provisional;
  const rows = await all(env, `SELECT id, reference, paid_at, processing FROM checkout_orders WHERE payment_intent IS NOT NULL AND commission_cents > 0 AND ${where} ORDER BY paid_at LIMIT 100`, ...b);
  const out = [];
  for (const o of rows) {
    const sa = await shortfallAmounts(env, o.id);
    const p = J(o.processing) || {}, status = p.status || 'awaiting_fee', conf = p.confirmed_at || o.paid_at || now();
    const s = reimbursementSchedule({ confirmed_at: conf, fee_recorded_at: p.fee_recorded_at, fee_time_known: p.fee_recorded_basis !== 'first_seen_by_pilot', reimbursed_at: p.completed_at || null, days });
    const amount = p.cost !== undefined ? Math.max(0, p.cost - (['awaiting_fee', 'outstanding'].includes(status) ? (p.reimbursed_cents || 0) : 0)) : null;
    const flags = [];
    if (p.confirmed_basis === 'stripe_charge_created') flags.push('Payment date taken from Stripe’s card charge time (fallback): no signed success event was recorded for this payment.');
    else if (p.confirmed_basis !== 'stripe_success_event_created') flags.push('Payment date taken from the pilot’s own record of the verified payment: Stripe’s confirmation time has not been read.');
    if (p.fee_recorded_basis === 'first_seen_by_pilot') flags.push(`FOR REVIEW: Stripe did not give the time it recorded the fee; the pilot can show only when it first saw it. The original date stays in force${s.extension_for_review ? ' although the pilot first saw the fee after it: whether the later date applies cannot be established' : ''}.`);
    if (p.delay_notice_at && !s.extended) flags.push('A delay notice was sent because Stripe showed no fee at the original date, but Stripe’s own record time is earlier: the original date stands. Check in the Stripe Dashboard and tell the artist if needed.');
    out.push({ order_id: o.id, reference: o.reference, status, status_label: REIMBURSEMENT_STATUS[status] || status,
      amount_cents: amount, amount_label: amount === null ? 'Not yet known: Stripe has not recorded the fee (nothing is estimated)'
        : status === 'shortfall' ? `${eur(p.cost)} in all: ${eur(sa.reimbursed)} reimbursed through Stripe; ${eur(sa.shortfallOutstanding)} still owed by bank transfer${sa.shortfallPaid ? ` (${eur(sa.shortfallPaid)} already paid)` : ''}` : eur(amount),
      reimbursed_through_stripe_cents: sa.reimbursed, owed_by_bank_transfer_cents: sa.shortfallOutstanding,
      payment_confirmed: s.confirmed_date, payment_confirmed_basis: p.confirmed_basis || 'pilot_verified_payment', day: s.day,
      fee_recorded: s.fee_recorded_date, fee_recorded_basis: p.fee_recorded_basis || null,
      original_due: s.original_due, extended: s.extended, extended_due: s.extended_due, due_date: s.due, due_provisional: prov,
      due_label: s.fee_time_unknown ? `Due by the end of ${longDate(s.original_due)} (Irish time)${prov ? ' · provisional' : ''} · Stripe gave no time for recording the fee: for review`
        : !s.extended ? `Due by the end of ${longDate(s.original_due)} (Irish time)${prov ? ' · provisional' : ''}`
        : s.extended_due ? `Extended: Stripe recorded the fee on ${longDate(s.fee_recorded_date)}. Due by the end of ${longDate(s.extended_due)} (Irish time)${prov ? ' · provisional' : ''}`
        : `Original date (${longDate(s.original_due)}) passed before Stripe recorded the fee. Due by the end of the ${days === 7 ? 'seventh' : days + 'th'} day after Stripe records it${prov ? ' · provisional' : ''}`,
      overdue: s.overdue && ['awaiting_fee', 'outstanding'].includes(status), completed_at: p.completed_at || null, completed_late: !!p.completed_late,
      alerts: p.alerts || {}, delay_notice_at: p.delay_notice_at || null,
      attempts: p.attempts || 0, last_error: p.last_error || null, last_attempt_at: p.last_attempt_at || null,
      failing: (p.attempts || 0) >= REIMB_FAIL_THRESHOLD && status === 'outstanding',
      fee_refund: p.fee_refund || null, flags,
      action: ['awaiting_fee', 'outstanding'].includes(status) ? 'Reconcile processing fee (re-reads Stripe, records any reimbursement Stripe already made, then retries; never pays twice)' : null });
  }
  return out;
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
async function notify(env, o, kind, text, { founderOnly = false, artistOnly = false, subject = null } = {}) {
  const artist = founderOnly ? null : await one(env, 'SELECT email, display_name FROM artists WHERE id = ?', o.artist_id);
  const to = [...(artist && artist.email ? [['artist', artist.email]] : []), ...(env.CHECKOUT_NOTIFY_EMAIL && !artistOnly ? [['founder', env.CHECKOUT_NOTIFY_EMAIL]] : [])];
  const out = [];
  for (const [role, addr] of to) {
    try { out.push((await deliver(env, { orderId: o.id, kind, toRole: role, to: addr, subject: subject || `PlotArt payment pilot · ${o.reference} · ${kind}`, body: text })).status); }
    catch (e) { out.push('error'); }
  }
  await event(env, o.id, 'system', 'notified_' + kind, o.status, o.status, { recipients: to.map(x => x[0]), result: out });
}
/* Re-check every pending refund with Stripe (sweep). */
export async function pollPendingRefunds(env) {
  let checked = 0, completed = 0, failed = 0, escalated = 0;
  for (const p of await pendingRefunds(env)) {
    const rr = await one(env, 'SELECT * FROM order_refunds WHERE id = ?', p.id), o = await getOrder(env, p.order_id);
    if (rr.provider_refund_id) {
      try {
        const re = await S.getRefund(env, { account: o.provider_account, id: rr.provider_refund_id }); checked++;
        if (re.status === 'succeeded') { await completeRefund(env, 'sweep', rr); completed++; continue; }   // a pending refund that has since succeeded: no Stripe success time (flagged for review)
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
  if (fee > 0) await feeRefund(env, founder, await getOrder(env, o.id), { fee, reason: 'commission share on an external repayment', refundId: row.id, providerRefund: ref,
    basis: { event: 'external_repayment_recorded', at: now(), source: 'pilot', review: 'Started from when the founder recorded the artist’s direct repayment of the buyer: check the date against the repayment evidence.' } });
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
const CONFIRM = ['available', 'location', 'condition', 'framing', 'dimensions', 'packing_and_handover', 'returns', 'seller_information'];
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
  const prof = await sellerProfile(env, artist.id), probs = sellerProblems(env, prof);
  if (probs.length) throw new Bad(`Before approving, complete your seller information: ${probs.join('; ')}`, 409);
  const conf = JSON.stringify({ ...Object.fromEntries(CONFIRM.map(k => [k, true])), seller_profile_sha256: await profileHash(prof), note: String(b.note || '').slice(0, 500) || null });
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
/* A quote is the only open quote for its work: PlotArt does not issue a second one while it can still be paid, so the
   buyer who holds it cannot lose the work to another pilot buyer (the artist separately agrees not to sell it elsewhere). */
async function requireNoOtherOpenQuote(env, o) {
  const other = await one(env, `SELECT reference FROM checkout_orders WHERE artwork_id = ? AND id <> ? AND status IN ('quoted','checkout_open','payment_failed') AND quote_expires_at > ?`, o.artwork_id, o.id, now());
  if (other) throw new Bad(`Another quote for this artwork (${other.reference}) is still open. Cancel it or let it expire first.`, 409);
}
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
  await requireNoOtherOpenQuote(env, o);
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
  const prof = await sellerProfile(env, artist.id), probs = sellerProblems(env, prof);
  if (probs.length) throw new Bad(`The quote cannot be issued without the seller information buyers must see: ${probs.join('; ')}`, 409);
  const approvedProfile = (J(o.artist_confirmations) || {}).seller_profile_sha256;
  if (approvedProfile !== await profileHash(prof)) throw new Bad('The artist’s seller information changed after they approved this quote. Send it to the artist to approve again.', 409);
  const d = J(o.delivery) || {};
  const ret = R.returnProblems(d);
  if (ret.length) throw new Bad(`The quote cannot be issued without the return arrangements: ${ret.join('; ')}`, 409);
  const seller = { name: artist.display_name, legal_name: prof.legal_name, trading_name: prof.trading_name, address: prof.address, returns_address: prof.returns_address || prof.address,
    email: prof.email, phone: prof.phone, trader_status: prof.trader_status, vat_number: prof.vat_number, role: 'Seller (the artist)', stripe_account_country: mem.account.country,
    platform: 'PlotArt (PlotNua, Colin Macaulay) introduces and coordinates this sale. PlotArt is not the seller.', contact: 'hello@plotnua.ie' };
  const token = rid('', 32) + rid('', 16);
  const expires = R.quoteExpiry(t, Number.isInteger(b.days) ? b.days : 3);
  const snapshot = JSON.stringify({ schema: 1, reference: o.reference, quote_version: o.quote_version, issued_at: t, expires_at: expires, currency: 'EUR', seller,
    artwork: J(o.artwork_snapshot), amounts: { artwork_cents: o.artwork_cents, delivery_cents: o.delivery_cents, total_cents: o.artwork_cents + o.delivery_cents },
    delivery: buyerDelivery(d), terms: { doc_id: bt.doc_id, html_sha256: bt.html_sha256 } });
  const snapSha = await sha256(snapshot);
  await run(env, 'INSERT INTO quote_snapshots (order_id, quote_version, snapshot, sha256, issued_at) VALUES (?,?,?,?,?)', o.id, o.quote_version, snapshot, snapSha, t);
  await move(env, o, 'quoted', founder, 'quote_issued', { quote_issued_at: t, quote_expires_at: expires, buyer_token_hash: await sha256(token), seller: JSON.stringify(seller), quote_sha256: snapSha,
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
/* What the buyer sees: the delivery, cover and return arrangements, never internal notes or confirmation references of who checked. */
function buyerDelivery(d) {
  return { collection_county: d.collection_county, destination: d.destination, packed_cm: d.packed_cm, framing: d.framing, glazing: d.glazing, condition: d.condition,
    organiser: d.organiser, packer: d.packer, transport_contracting_party: d.transport_contracting_party, transporter_name: d.transporter_name, installation: d.installation, import_costs: d.import_costs,
    cover_type: d.cover_type, cover_provider: d.cover_provider, insured_party: d.insured_party, cover_confirmation_ref: d.cover_confirmation_ref, covered_value_cents: d.covered_value_cents, valuation_basis: d.valuation_basis, excess_cents: d.excess_cents,
    exclusions: d.exclusions, cover_period: d.cover_period, claims_contact: d.claims_contact, delivery_window: d.delivery_window, tracking: d.tracking,
    signed_receipt: d.signed_receipt, condition_photos: d.condition_photos,
    return_method: d.return_method, return_address: d.return_address, return_cost_cents: d.return_cost_cents, return_cost_basis: d.return_cost_basis, return_arranged_by: d.return_arranged_by };
}
async function quoteSnapshot(env, o) {
  const r = await one(env, 'SELECT snapshot, sha256 FROM quote_snapshots WHERE order_id = ? AND quote_version = ?', o.id, o.quote_version);
  return r ? { ...JSON.parse(r.snapshot), sha256: r.sha256 } : null;
}
export async function buyerQuote(env, token) {
  const o = await byToken(env, token);
  if (!o) return null;
  const q = await quoteSnapshot(env, o);
  if (!q) return null;
  const bt = o.buyer_terms_doc_id ? await one(env, 'SELECT doc_id, title FROM payment_terms WHERE doc_id = ?', o.buyer_terms_doc_id) : null;
  const conf = await one(env, "SELECT sha256 FROM order_messages WHERE order_id = ? AND kind = 'buyer_confirmation' AND item_key = ''", o.id);
  const notices = await all(env, "SELECT kind, subject, body, created_at FROM order_messages WHERE order_id = ? AND kind <> 'buyer_confirmation' ORDER BY created_at", o.id);
  return { reference: o.reference, status: o.status, payment_status: o.payment_status, fulfilment_status: o.fulfilment_status,
    expired: !!o.quote_expires_at && o.quote_expires_at <= now(), quote_expires_at: o.quote_expires_at, seller: q.seller, artwork: q.artwork,
    currency: 'EUR', artwork_cents: q.amounts.artwork_cents, delivery_cents: q.amounts.delivery_cents, total_cents: q.amounts.total_cents,
    delivery: q.delivery, terms: bt, quote_sha256: q.sha256, confirmation_ready: !!conf, notices };
}
export async function buyerConfirmation(env, token) {
  const o = await byToken(env, token);
  if (!o) return null;
  return one(env, "SELECT subject, body, sha256, created_at FROM order_messages WHERE order_id = ? AND kind = 'buyer_confirmation' AND item_key = ''", o.id);
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
  if (!(o.commission_bp > 0)) throw new Bad('The seller cannot take payments through PlotArt for this order. Please contact hello@plotnua.ie.', 409);
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
      return { status: 'processed', order: o.id, detail: await recordPaid(env, o, obj, ev.id, ev.created) };
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
      if (obj.status === 'succeeded') { await completeRefund(env, 'provider', { ...mine, provider_refund_id: obj.id }, ev.created ? { event: `stripe_event:${ev.type}`, at: iso(ev.created), source: 'stripe' } : null); return { status: 'processed', order: o.id, detail: 'refund succeeded' }; }
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

/* Start of the reimbursement clock (PA-PAY 3.3(b)): the `created` time of the signed Stripe event that confirmed the
   successful payment (checkout.session.completed with payment_status 'paid', or checkout.session.async_payment_succeeded).
   Fallbacks, in order, when the payment was recorded without such an event (founder reconcile after an interruption):
   the succeeded card charge's `created` time (the pilot accepts card only, captured automatically, so the succeeded charge
   is created when the payment succeeds), then the pilot's own record of the verified payment (flagged). */
function startClock(o, eventId, eventCreated) {
  if (!(o.commission_cents > 0)) return o.processing || null;
  const p = J(o.processing) || {};
  if (p.confirmed_basis === 'stripe_success_event_created') return o.processing;
  return JSON.stringify(eventCreated && !String(eventId || '').startsWith('reconcile:')
    ? { ...p, status: p.status || 'awaiting_fee', confirmed_at: iso(eventCreated), confirmed_basis: 'stripe_success_event_created', confirmed_event: eventId }
    : { ...p, status: p.status || 'awaiting_fee' });
}
/* A verified completed payment. The sale, the order, the session, the reservation release, the Studio "sold" mark and
   the ledger are written in ONE transaction. If the original has already been sold (to another order), nothing is sold
   twice: the payment is booked and the order is flagged for a refund. */
async function recordPaid(env, o, s, eventId, eventCreated = null) {
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
      st(env, `UPDATE checkout_orders SET status = 'paid', payment_status = 'paid', payment_intent = ?, amount_received_cents = ?, paid_at = ?, processing = ?, needs_resolution = ?, updated_at = ? WHERE id = ?`,
        pi, s.amount_total, t, startClock(o, eventId, eventCreated), late ? 'late payment after the quote/checkout had expired: recorded as a sale (the work was still free); confirm with buyer and artist' : null, t, o.id),
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
  // the buyer's purchase confirmation (test sink in test mode); the sweep retries if this fails
  try { await prepareConfirmation(env, await getOrder(env, o.id)); } catch { /* the sweep retries */ }
  // Model B: reimburse Stripe's processing cost as soon as Stripe has recorded it (usually seconds later: the sweep retries)
  try { await reconcileProcessing(env, await getOrder(env, o.id)); } catch { /* the sweep retries */ }
  // events for this payment that arrived before this completion (e.g. a dispute) are applied now, not left waiting
  let replayed = 0; try { replayed = await replayDeferred(env, pi); } catch { /* the sweep retries */ }
  return (late ? 'paid (late)' : 'paid') + (replayed ? `; ${replayed} earlier event(s) replayed` : '');
}

async function refundTotals(env, orderId) {
  // a refund Stripe reversed (succeeded, then failed) is booked as a positive *_reversed line and no longer counts as repaid
  const r = await one(env, `SELECT COALESCE(SUM(CASE WHEN kind IN ('artwork_refund','artwork_refund_reversed') THEN -amount_cents END), 0) AS art, COALESCE(SUM(CASE WHEN kind IN ('delivery_refund','delivery_refund_reversed') THEN -amount_cents END), 0) AS del,
    COALESCE(SUM(CASE WHEN kind = 'commission_refund' THEN -amount_cents END), 0) AS fee, COALESCE(SUM(CASE WHEN kind = 'external_refund' THEN -amount_cents END), 0) AS ext FROM order_ledger WHERE order_id = ?`, orderId);
  // Model B: a commission refund that could not go back through Stripe (the application fee had already reimbursed processing)
  // is owed by PlotArt directly as a shortfall. It counts as settled commission here, so it is never owed (or paid) twice.
  r.fee_shortfall = (await one(env, "SELECT COALESCE(SUM(cents), 0) AS c FROM checkout_owed WHERE order_id = ? AND kind = 'commission_shortfall'", orderId)).c;
  r.fee += r.fee_shortfall;
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
      if (mine.status !== 'succeeded') await completeRefund(env, 'provider', { ...mine, provider_refund_id: r.id }, mine.status !== 'pending' && r.created ? { event: 'stripe_refund_created_succeeded', at: iso(r.created), source: 'stripe' } : null);
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

/* Stripe's dispute fees, from the dispute's own balance transactions (fee and the VAT on it; a negative fee is a fee
   Stripe returned). Booked once per balance transaction. If Stripe has not supplied them, the order says so. */
async function recordDisputeFees(env, o, d) {
  const full = x => Array.isArray(x) && x.every(b => b && typeof b === 'object') ? x : null;
  let bts = full(d.balance_transactions);
  if (!bts) { try { bts = full((await S.getDispute(env, { account: o.provider_account, id: d.id })).balance_transactions); } catch { bts = null; } }
  const cur = await getOrder(env, o.id), info = J(cur.dispute_fees) || {};
  if (!bts) info[d.id] = { ...(info[d.id] || {}), status: 'unavailable', checked_at: now() };
  else {
    const lines = [];
    let charged = 0, returned = 0;
    for (const bt of bts) {
      if (!bt.fee) continue;
      const vat = (bt.fee_details || []).filter(x => x.type === 'tax').reduce((a, x) => a + x.amount, 0);
      if (bt.fee > 0) { charged += bt.fee; lines.push(ledgerSt(env, o.id, 'dispute_fee', -bt.fee, bt.id, `Stripe dispute fee ${eur(bt.fee - vat)} + VAT ${eur(vat)} (dispute ${d.id}); charged to the seller, not reimbursed by PlotArt`)); }
      else { returned += -bt.fee; lines.push(ledgerSt(env, o.id, 'dispute_fee_returned', -bt.fee, bt.id, `Stripe returned a dispute fee (dispute ${d.id})`)); }
    }
    if (lines.length) await env.DB.batch(lines);
    info[d.id] = { status: 'recorded', balance_transactions: bts.length, checked_at: now() };
  }
  await run(env, 'UPDATE checkout_orders SET dispute_fees = ?, updated_at = ? WHERE id = ?', JSON.stringify(info), now(), o.id);
}
/* A dispute on an order whose retention date is already fixed: the records are held (reviewed hold) until it is resolved. */
async function holdForLateDispute(env, o, d) {
  if (!o.retain_until || await one(env, "SELECT 1 AS x FROM checkout_holds WHERE order_id = ? AND released_at IS NULL AND basis = 'dispute'", o.id)) return;
  const id = rid('h'), t = now(), rv = plusDays(t, 180).slice(0, 10), reason = `Automatic: Stripe dispute ${d.id} opened after this order's retention date was fixed. Keep until the dispute is resolved, then review.`;
  await env.DB.batch([st(env, 'INSERT INTO checkout_holds (id, order_id, basis, reason, placed_by, placed_at, review_by) VALUES (?,?,?,?,?,?,?)', id, o.id, 'dispute', reason, 'system', t, rv),
    st(env, "INSERT INTO checkout_hold_events (id, hold_id, order_id, kind, actor, at, note, review_by) VALUES (?,?,?, 'placed', ?,?,?,?)", rid('he'), id, o.id, 'system', t, reason, rv)]);
}
async function recordDispute(env, o, type, d) {
  if (type.startsWith('charge.dispute.')) { try { await recordDisputeFees(env, o, d); } catch { /* the sweep retries unavailable fees */ } }
  if (type === 'charge.dispute.created') await holdForLateDispute(env, o, d);
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
    const cur0 = await getOrder(env, o.id);
    await run(env, 'UPDATE checkout_orders SET dispute_status = ?, needs_resolution = ?, updated_at = ? WHERE id = ?', won ? 'won' : 'lost',
      won ? cur0.needs_resolution : [`dispute lost (${d.id}): return PlotArt’s commission under PA-GAA 9.1 within 30 days (founder desk: Amounts owed → Return commission)`, cur0.needs_resolution].filter(Boolean).join(' | '), now(), o.id);
    if (!won) {   // PA-GAA 9.1: treated as fully refunded; the commission still to be returned joins the queue with its deadline
      const tot = await refundTotals(env, o.id);
      await owe(env, cur0, { kind: 'lost_dispute_commission', key: `lost:${d.id}`, cents: Math.max(0, (cur0.commission_cents || 0) - tot.fee), reason: `Stripe closed dispute ${d.id} as lost` });
    }
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
    const w = await one(env, "SELECT * FROM checkout_owed WHERE order_id = ? AND kind = 'lost_dispute_commission' AND settled_cents < cents ORDER BY arisen_at LIMIT 1", o.id);
    const fee = w ? w.cents - w.settled_cents : Math.max(0, o.commission_cents - tot.fee);
    if (!fee) return { already: true, ...(await orderDetail(env, o, 'founder')) };
    return feeRefund(env, founder, o, { fee, reason, owed: w, basis: w ? { event: 'dispute_closed_lost', at: w.arisen_at, source: 'pilot', review: 'Started from when the pilot recorded Stripe closing the dispute as lost: check the closing date in the Stripe Dashboard.' } : null });
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
  if (re.status === 'succeeded') return completeRefund(env, founder, row, re.created ? { event: 'stripe_refund_created_succeeded', at: iso(re.created), source: 'stripe' } : null);
  if (['failed', 'canceled'].includes(re.status)) { await failRefund(env, row, re); return orderDetail(env, await getOrder(env, o.id), 'founder'); }
  // pending: for a card refund Stripe holds it when the artist's AVAILABLE Stripe balance cannot cover it (for example after
  // the payout), until the balance recovers; Stripe fails a pending refund after 45 days. Nothing is booked until it succeeds.
  await event(env, o.id, founder, 'refund_pending_at_provider', 'refund_pending', 'refund_pending', { refund: rr.id, provider_refund: re.id });
  await buyerRefundNotice(env, o, 'buyer_refund_pending', { id: rr.id, artwork_cents: art, delivery_cents: del });
  await notify(env, o, 'refund_pending', `A refund of EUR ${((art + del) / 100).toFixed(2)} on PlotArt order ${o.reference} is waiting because the seller's Stripe balance cannot cover it yet. Stripe cancels it after 45 days if it is still unfunded.\n\n${REFUND_FUNDING_STEPS.join('\n')}`);
  await run(env, 'UPDATE checkout_orders SET needs_resolution = ?, updated_at = ? WHERE id = ?',
    `refund ${re.id} is pending at Stripe (usually the artist's available Stripe balance is too low, e.g. after payout). Ask the artist to top up their Stripe balance; Stripe fails pending refunds after 45 days.`, now(), o.id);
  return orderDetail(env, await getOrder(env, o.id), 'founder');
}
/* A refund confirmed by Stripe: book it, return PlotArt's commission share (GAA 9) and settle the order. Idempotent: the
   ledger is unique per (kind, refund id) and the commission refund uses an idempotency key per refund request. */
async function completeRefund(env, actor, rr, basis = null) {
  const o = await getOrder(env, rr.order_id);
  await env.DB.batch([
    st(env, "UPDATE order_refunds SET status = 'succeeded', provider_refund_id = COALESCE(provider_refund_id, ?), updated_at = ? WHERE id = ?", rr.provider_refund_id, now(), rr.id),
    ...(rr.artwork_cents ? [ledgerSt(env, o.id, 'artwork_refund', -rr.artwork_cents, rr.provider_refund_id, rr.reason)] : []),
    ...(rr.delivery_cents ? [ledgerSt(env, o.id, 'delivery_refund', -rr.delivery_cents, rr.provider_refund_id, rr.reason)] : []),
  ]);
  if (o.needs_resolution && o.needs_resolution.includes(`refund ${rr.provider_refund_id} is pending`)) await run(env, 'UPDATE checkout_orders SET needs_resolution = NULL, updated_at = ? WHERE id = ?', now(), o.id);
  const cur = await one(env, 'SELECT fee_refund_id FROM order_refunds WHERE id = ?', rr.id);
  if (rr.commission_refund_cents > 0 && !cur.fee_refund_id) await feeRefund(env, actor, await getOrder(env, o.id), { fee: rr.commission_refund_cents, reason: rr.reason, refundId: rr.id, providerRefund: rr.provider_refund_id,
    basis: basis || { event: 'refund_success_seen_by_pilot', at: now(), source: 'pilot', review: 'Started from when the pilot found the buyer refund succeeded (Stripe gave no success time): check the refund in the Stripe Dashboard.' } });
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
  await buyerRefundNotice(env, await getOrder(env, rr.order_id), 'buyer_refund_failed', cur || rr, re.failure_reason || re.status);
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
  const owedDirect = ((await one(env, 'SELECT cents FROM checkout_owed WHERE order_id = ? AND item_key = ?', o.id, `commission:${rr.id}`)) || {}).cents || 0;
  const flag = `refund ${ref} of ${eur(rr.artwork_cents + rr.delivery_cents)} SUCCEEDED and then FAILED (${re.failure_reason || re.status}): Stripe returned the money to the artist's balance and the buyer has NOT been repaid. `
    + (feeBack ? `PlotArt had already settled ${eur(feeBack)} commission for it${owedDirect ? ` (${eur(feeBack - owedDirect)} through Stripe; ${eur(owedDirect)} owed by PlotArt directly because the application fee had reimbursed processing)` : ''}; that stays settled, so repaying this amount again returns no further commission. ` : '')
    + 'Repay the buyer by ONE route only: a new refund through the pilot, OR the artist repays directly and the founder records it with evidence.';
  const back = o.fulfilment_status === 'delivered' ? 'delivered' : o.fulfilment_status === 'dispatched' ? 'dispatched' : 'paid';
  const sets = { payment_status: repaid > 0 ? 'partially_refunded' : 'paid', needs_resolution: flag };
  if (['refunded', 'refund_pending'].includes(o.status) && R.canMove(o.status, back)) await move(env, o, back, 'provider', 'refund_reversed', sets, { refund: rr.id, provider_refund: ref, reason: re.failure_reason || re.status });
  else { await run(env, 'UPDATE checkout_orders SET payment_status = ?, needs_resolution = ?, updated_at = ? WHERE id = ?', sets.payment_status, flag, now(), o.id); await event(env, o.id, 'provider', 'refund_reversed', o.status, o.status, { refund: rr.id, provider_refund: ref }); }
  await run(env, "UPDATE artwork_sales SET released_at = NULL, released_reason = NULL WHERE order_id = ? AND released_reason = 'fully refunded'", o.id);   // the buyer still holds the sale
  await setOwedFlag(env, o.id);
  await buyerRefundNotice(env, await getOrder(env, o.id), 'buyer_refund_reversed', rr, re.failure_reason || re.status);
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
/* ---------------------------------------------------------------- Fee Model B: PlotArt absorbs Stripe's processing cost
   Founder decision (17 Nov 2026). On an order that carries PlotArt commission, the artist's combined deduction for PlotArt
   commission and Stripe payment processing must not exceed the commission. PlotArt therefore reimburses Stripe's ACTUAL
   processing fee and the VAT Stripe charges on it — on the whole payment, delivery included — by a partial refund of its
   own application fee, once Stripe has recorded the fee (it does so asynchronously). Commission stays calculated on the
   artwork only and is booked in full; the reimbursement is a separate ledger line, so commission records are unchanged.
   One pot: commission refunds owed under PA-GAA 9 and processing reimbursements are both paid from the application fee,
   so together they can never exceed it, and each is computed against what has already been returned (no double return).
   If what PlotArt owes the artist exceeds what is left of the application fee, the difference is a SHORTFALL: it cannot be
   paid through Stripe from this order, is flagged, and must be paid by PlotArt directly (e.g. bank transfer) and recorded.
   Not covered: Stripe's dispute fees, add-on fees (e.g. paid Radar plans, currency conversion) and any other charge. */
const NOT_PROCESSING = /radar|currency|conversion|billing|invoic|tax calculation|identity|instant payout/i;
export function processingFromBalance(bt) {
  const lines = (bt && bt.fee_details) || [];
  const fees = lines.filter(l => l.type === 'stripe_fee');
  const proc = fees.filter(l => !NOT_PROCESSING.test(l.description || '')).reduce((a, l) => a + l.amount, 0);
  const other = fees.filter(l => NOT_PROCESSING.test(l.description || '')).reduce((a, l) => a + l.amount, 0);
  const vatAll = lines.filter(l => l.type === 'tax').reduce((a, l) => a + l.amount, 0);
  const vat = other ? Math.round(vatAll * proc / (proc + other || 1)) : vatAll;   // VAT apportioned only if non-processing fees are present
  return { balance_transaction: bt.id, currency: bt.currency, stripe_fee: proc, vat, cost: proc + vat, excluded_fees: other, excluded_vat: vatAll - vat,
    descriptions: lines.map(l => `${l.type}: ${l.description || ''}`.slice(0, 80)) };
}
async function feePot(env, o) {
  const r = await one(env, `SELECT COALESCE(SUM(CASE WHEN kind = 'commission_refund' THEN -amount_cents END), 0) AS commission_refunded,
    COALESCE(SUM(CASE WHEN kind = 'processing_reimbursement' THEN amount_cents END), 0) AS reimbursed,
    COALESCE(SUM(CASE WHEN kind = 'processing_shortfall_paid' THEN amount_cents END), 0) AS shortfall_paid FROM order_ledger WHERE order_id = ?`, o.id);
  return { ...r, left: Math.max(0, (o.commission_cents || 0) - r.commission_refunded - r.reimbursed) };
}
const eur = c => `EUR ${(c / 100).toFixed(2)}`;
/* ---------------------------------------------------------------- amounts PlotArt owes artists (queue)
   processing_shortfall / commission_shortfall: Model B amounts that cannot be returned through Stripe from that order's
   application fee; PlotArt pays them directly. lost_dispute_commission: commission to return after a lost dispute
   (PA-GAA 9.1). Each item's amount, rule and due date are fixed when it arises; settlement is recorded payment by payment,
   never above the amount (database CHECK), and a payment reference can be recorded only once per item. */
const SHORTFALL_KINDS = ['processing_shortfall', 'commission_shortfall'];
/* PA-PAY 3.5 (sandbox rule approved by the founder 18 Nov 2026): a bank-transfer amount is due by the end of the 30th Irish
   calendar day after the Irish date of the transaction record that first established it (the next day is day one). The
   record used, its time and its Irish date are stored; a start that rests on the pilot's own record rather than Stripe's
   is flagged for founder review. The due date is fixed once: later reconciliation, retries, partial payments and returned
   transfers never move it, and items created before this rule keep the date they were given. */
export function shortfallDue(basisAt, days = 30) {
  const basis_date = dublinDate(basisAt), due_date = addDate(basis_date, days);
  return { basis_date, due_date, due_at: new Date(dublinDayEnd(due_date)).toISOString() };
}
const BASIS_LABEL = { stripe_fee_recorded: 'Stripe’s record of the processing fee', stripe_refund_created_succeeded: 'Stripe’s record of the buyer refund',
  refund_success_seen_by_pilot: 'the pilot’s record of the buyer refund succeeding', external_repayment_recorded: 'the founder’s record of the artist repaying the buyer directly',
  dispute_closed_lost: 'the pilot’s record of Stripe closing the dispute as lost', pilot_computed: 'the pilot’s own calculation' };
const basisLabel = e => BASIS_LABEL[e] || (String(e).startsWith('stripe_event:') ? 'Stripe’s event for the buyer refund' : e);
async function owe(env, o, { kind, key, cents, reason, basis = null }) {
  if (!(cents > 0)) return null;
  const d = deadlines(env), t = now(), lost = kind === 'lost_dispute_commission';
  let r;
  if (lost) {
    const days = d.lost_dispute_commission_days;
    r = await run(env, `INSERT INTO checkout_owed (id, order_id, kind, item_key, cents, reason, arisen_at, due_at, due_rule, due_provisional) VALUES (?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(order_id, item_key) DO NOTHING`, rid('ow'), o.id, kind, key, cents, String(reason).slice(0, 500), t, plusDays(t, days),
      `PA-GAA cl. 9.1: commission returned within ${days} days of notice (here, Stripe closing the dispute as lost)`, 0);
  } else {
    const b = basis && basis.at ? basis : { event: 'pilot_computed', at: t, source: 'pilot', review: 'No transaction record time was available: the start date is when the pilot worked out the amount.' };
    const days = d.shortfall_days, due = shortfallDue(b.at, days);
    const review = b.review || (b.source !== 'stripe' ? 'The start date rests on the pilot’s own record, not Stripe’s.' : null);
    const rule = `${d.shortfall_provisional ? 'PROVISIONAL: ' : ''}paid by bank transfer by the end of day ${days} (Irish time) counted from ${longDate(due.basis_date)}, the Irish date of ${basisLabel(b.event)} (day one is the next day; PA-PAY draft cl. 3.5)`;
    r = await run(env, `INSERT INTO checkout_owed (id, order_id, kind, item_key, cents, reason, arisen_at, due_at, due_rule, due_provisional, due_basis_event, due_basis_at, due_basis_date, due_basis_source, due_review)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(order_id, item_key) DO NOTHING`, rid('ow'), o.id, kind, key, cents, String(reason).slice(0, 500), t, due.due_at, rule,
      d.shortfall_provisional ? 1 : 0, b.event, b.at, due.basis_date, b.source === 'stripe' ? 'stripe' : 'pilot', review);
    if (r.meta.changes && review) await notify(env, o, 'owed_start_for_review', `FOR REVIEW: order ${o.reference} — PlotArt owes the artist ${eur(cents)} by bank transfer (${kind.replace(/_/g, ' ')}). The 30 days run from ${longDate(due.basis_date)} (${basisLabel(b.event)}), so it is due by the end of ${longDate(due.due_date)} (Irish time). ${review}`, { founderOnly: true });
  }
  if (r.meta.changes) await event(env, o.id, 'system', 'owed_recorded', o.status, o.status, { kind, key, cents, provisional: !lost && d.shortfall_provisional, basis });
  await setOwedFlag(env, o.id);
  return one(env, 'SELECT * FROM checkout_owed WHERE order_id = ? AND item_key = ?', o.id, key);
}
const addShortfall = (env, o, key, cents, why, basis = null) => owe(env, o, { kind: key.startsWith('commission:') ? 'commission_shortfall' : 'processing_shortfall', key, cents, reason: why, basis });
/* The order's flag always states the shortfall still owed (never hidden by other flags, never left after payment). */
async function setOwedFlag(env, id) {
  const o = await getOrder(env, id);
  const owed = (await one(env, `SELECT COALESCE(SUM(cents - settled_cents), 0) AS c, MIN(due_at) AS due FROM checkout_owed WHERE order_id = ? AND kind IN ('processing_shortfall','commission_shortfall') AND settled_cents < cents`, id));
  const rest = (o.needs_resolution || '').split(' | ').filter(x => x && !x.startsWith('PlotArt owes the artist')).join(' | ');
  const late = owed.c > 0 && Date.parse(owed.due) <= Date.now();
  const flag = owed.c > 0 ? `PlotArt owes the artist ${eur(owed.c)} that cannot be paid from this order's application fee (${late ? 'OVERDUE: was ' : ''}due by the end of ${longDate(dublinDate(Date.parse(owed.due) - 1))}, Irish time). ${late ? 'Follow up with the artist promptly (internal target: resolved within 5 working days of the deadline; the artist’s deadline still applies). ' : ''}PlotArt must pay it by bank transfer and record it with "Record shortfall paid" once the bank shows it executed.` : '';
  const nr = [flag, rest].filter(Boolean).join(' | ') || null;
  if (nr !== o.needs_resolution) await run(env, 'UPDATE checkout_orders SET needs_resolution = ?, updated_at = ? WHERE id = ?', nr, now(), id);
}
async function dropFlag(env, id, prefix) {
  const o = await getOrder(env, id);
  const nr = (o.needs_resolution || '').split(' | ').filter(x => x && !x.startsWith(prefix)).join(' | ') || null;
  if (nr !== o.needs_resolution) await run(env, 'UPDATE checkout_orders SET needs_resolution = ?, updated_at = ? WHERE id = ?', nr, now(), id);
}
async function settleOwed(env, w, { cents, method, reference, actor, executedOn = null }) {
  if (!(cents > 0)) return;
  await env.DB.batch([
    st(env, 'INSERT INTO checkout_owed_payments (id, owed_id, order_id, cents, method, reference, executed_on, recorded_by, at) VALUES (?,?,?,?,?,?,?,?,?)', rid('op'), w.id, w.order_id, cents, method, reference, executedOn, actor, now()),
    st(env, 'UPDATE checkout_owed SET settled_cents = settled_cents + ? WHERE id = ? AND settled_cents + ? <= cents', cents, w.id, cents)]);
}
async function owedRows(env, where, ...b) {
  const rows = await all(env, `SELECT w.*, o.reference, o.artist_id, a.display_name AS artist_name FROM checkout_owed w JOIN checkout_orders o ON o.id = w.order_id
    LEFT JOIN artists a ON a.id = o.artist_id WHERE ${where} ORDER BY w.due_at`, ...b);
  const t = Date.now();
  for (const w of rows) {
    w.outstanding_cents = w.cents - w.settled_cents;
    w.age_days = Math.floor((t - Date.parse(w.arisen_at)) / 86400_000);
    w.status = w.outstanding_cents <= 0 ? 'settled' : Date.parse(w.due_at) < t ? 'overdue' : 'open';
    w.due_date = w.due_basis_date ? dublinDate(Date.parse(w.due_at) - 1) : w.due_at.slice(0, 10);   // Irish date for the 3.5 rule; legacy items keep their stored date
    w.due_label = w.due_basis_date ? `by the end of ${longDate(w.due_date)} (Irish time)` : `${w.due_date} (date assigned before the 18 Nov 2026 rule)`;
    w.due_review = w.due_review || null;
    w.due_provisional = !!w.due_provisional;
    w.reminders = J(w.reminders) || [];
    w.payments = await all(env, `SELECT p.id, p.cents, p.method, p.reference, p.executed_on, p.recorded_by, p.at, r.returned_on, r.reason AS returned_reason, r.recorded_by AS return_recorded_by, r.at AS return_recorded_at
      FROM checkout_owed_payments p LEFT JOIN checkout_owed_payment_returns r ON r.payment_id = p.id WHERE p.owed_id = ? ORDER BY p.at, p.rowid`, w.id);
  }
  return rows;
}
/* Working days (Monday to Friday; Irish public holidays are not counted out) after an Irish date: the founder's internal
   target for resolving an overdue amount. It never changes the artist's deadline. */
export function workingDaysAfter(date, n) {
  let d = date, k = 0;
  while (k < n) { d = addDate(d, 1); const wd = new Date(d + 'T12:00:00Z').getUTCDay(); if (wd !== 0 && wd !== 6) k++; }
  return d;
}
/* Reminders (test sink only). Founder: once 7 days before the deadline, and once when it is overdue, with a prompt to follow
   up. Artist: one notice when a bank-transfer amount becomes overdue (shortfalls only; one per item). */
async function remindOwed(env) {
  const d = deadlines(env), t = Date.now();
  let sent = 0;
  for (const w of await all(env, 'SELECT * FROM checkout_owed WHERE settled_cents < cents')) {
    const due = Date.parse(w.due_at), stage = t >= due ? 'overdue' : due - t <= d.reminder_days_before * 86400_000 ? 'due_soon' : null;
    const done = J(w.reminders) || [];
    if (!stage || done.includes(stage)) continue;
    const o = await getOrder(env, w.order_id), out = w.cents - w.settled_cents, bank = SHORTFALL_KINDS.includes(w.kind);
    const dueDay = w.due_basis_date ? dublinDate(due - 1) : w.due_at.slice(0, 10), dueText = w.due_basis_date ? `the end of ${longDate(dueDay)} (Irish time)` : dueDay;
    const target = w.due_basis_date ? workingDaysAfter(dueDay, 5) : null;
    await notify(env, o, `owed_${stage}`, stage === 'overdue'
      ? `OVERDUE — follow up promptly: PlotArt owes the artist ${eur(out)} on order ${o.reference} (${w.kind.replace(/_/g, ' ')}). It was due by ${dueText}${w.due_provisional ? ' (provisional deadline)' : ''}. ${bank ? `Phone the artist on the number in their seller information, pay by bank transfer, and record the payment once the bank shows it executed. Internal resolution target: ${target ? longDate(target) : 'within 5 working days'} (5 working days after the deadline). The artist’s deadline still applies. ` : ''}Founder desk: Amounts owed. Never put bank details in email.`
      : `Due in 7 days or less: PlotArt owes the artist ${eur(out)} on order ${o.reference} (${w.kind.replace(/_/g, ' ')}), due by ${dueText}${w.due_provisional ? ' (provisional deadline)' : ''}. Founder desk: Amounts owed. Never put bank details in email; follow the bank details process.`, { founderOnly: true });
    if (stage === 'overdue' && bank) await notify(env, o, 'owed_overdue_artist', owedOverdueText(o, w, out, dueDay), { artistOnly: true, subject: `PlotArt payment pilot · ${o.reference} · amount owed to you is overdue` });
    await run(env, 'UPDATE checkout_owed SET reminders = ? WHERE id = ?', JSON.stringify([...done, stage]), w.id);
    if (stage === 'overdue') await setOwedFlag(env, o.id);
    sent++;
  }
  return sent;
}
export function owedOverdueText(o, w, out, dueDay) {
  return [`Order ${o.reference}`, '',
    `PlotArt owes you ${eur(out)} that could not be paid through Stripe (${w.kind === 'commission_shortfall' ? 'commission PlotArt must return to you' : 'part of Stripe’s processing fee and VAT that PlotArt reimburses'}). It was due by the end of ${longDate(dueDay)} (Irish time), and it has not yet been paid in full. We are sorry for the delay.`, '',
    `PlotArt will contact you to arrange the bank transfer. PlotArt will never ask for your bank details by email. Your statement shows the amount still owed.`, '',
    'This message comes from the PlotArt payment pilot (test mode).'].join('\n');
}
export function owedPaymentText(o, w, cents, executedOn, reference, stillOwed, dueDay) {
  return [`Order ${o.reference}`, '',
    `PlotArt sent you ${eur(cents)} by bank transfer on ${longDate(executedOn)} (PlotArt’s transfer reference: ${reference}). This is ${w.kind === 'commission_shortfall' ? 'commission PlotArt returns to you' : 'part of Stripe’s processing fee and VAT that PlotArt reimburses'} and could not be paid through Stripe.`, '',
    stillOwed > 0 ? `Still owed to you by PlotArt on this order: ${eur(stillOwed)}${dueDay ? `, due by the end of ${longDate(dueDay)} (Irish time)` : ''}.` : 'Nothing more is owed to you by bank transfer on this order.', '',
    'How long the transfer takes to appear in your account depends on your bank.', '',
    'This message comes from the PlotArt payment pilot (test mode).'].join('\n');
}
export const BANK_DETAILS_PROCESS = [
  'Bank details are never entered in PlotArt Studio, the payment pilot, its logs or its emails.',
  'Ask the artist, by phone on the number in their seller information or in person, for the account name and IBAN, and enter them directly into PlotArt’s bank as a new payee. Do not accept them by email, chat or a form in PlotArt.',
  'Use the bank’s payee name check (Verification of Payee) and do not pay if it reports a mismatch until the artist confirms by phone.',
  'If the artist later asks to change the account, confirm the change by calling the artist on the number already held; never act on an emailed change of bank details.',
  'Record the payment here with the bank’s transfer reference and date only (no IBAN, account number or sort code). The pilot refuses references that look like bank details.',
  'PlotArt’s bank keeps the details as a saved payee (delete it once no further payment to the artist is expected) and in its record of the transfer, which is part of PlotArt’s accounting records for six years and cannot be deleted. Never say PlotArt holds no bank details.',
];
async function ensureCharge(env, o) {
  if (o.charge_id && o.application_fee_id) return o;
  const p = await S.getPaymentIntent(env, { account: o.provider_account, id: o.payment_intent });
  const ch = p.latest_charge && typeof p.latest_charge === 'object' ? p.latest_charge : null;
  if (ch) await run(env, 'UPDATE checkout_orders SET charge_id = COALESCE(charge_id, ?), application_fee_id = COALESCE(application_fee_id, ?), updated_at = ? WHERE id = ?',
    ch.id, typeof ch.application_fee === 'string' ? ch.application_fee : ch.application_fee && ch.application_fee.id || null, now(), o.id);
  return getOrder(env, o.id);
}
/* ---------------------------------------------------------------- processing reimbursement: the seven-day rule (PA-PAY §3.3(b), PROVISIONAL)
   Dates are Irish calendar dates (Europe/Dublin). The day after the Dublin date of Stripe's payment confirmation is day 1;
   the reimbursement is due by the end of day 7 (CHECKOUT_REIMBURSE_DAYS). Only if Stripe has NOT recorded the fee by that
   original deadline does the period run instead to the end of the seventh day after the Dublin date on which Stripe recorded
   it. Evidence: payment confirmation = the charge's `created` time at Stripe; fee recorded = the `created` time of the
   charge's balance transaction at Stripe. Where Stripe's time cannot be read the pilot uses its own first record and says so.
   A failed reimbursement attempt, or a delay in the pilot checking Stripe, never starts a new period. */
const DUB = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Dublin', year: 'numeric', month: '2-digit', day: '2-digit' });
export const dublinDate = t => { const x = Object.fromEntries(DUB.formatToParts(new Date(typeof t === 'number' ? t : Date.parse(t))).map(p => [p.type, p.value])); return `${x.year}-${x.month}-${x.day}`; };
const addDate = (d, n) => new Date(Date.parse(d + 'T12:00:00Z') + n * 86400_000).toISOString().slice(0, 10);
const dateDiff = (a, b) => Math.round((Date.parse(b + 'T12:00:00Z') - Date.parse(a + 'T12:00:00Z')) / 86400_000);
/* The first instant after the Dublin calendar day d (Irish midnight, 00:00 IST = 23:00 UTC in summer, 00:00 GMT in winter). */
export function dublinDayEnd(d) {
  const next = addDate(d, 1);
  for (const h of [-1, 0]) { const t = Date.parse(next + 'T00:00:00Z') + h * 3600_000; if (dublinDate(t) === next) return t; }
  return Date.parse(next + 'T00:00:00Z');
}
export const longDate = d => new Date(d + 'T12:00:00Z').toLocaleDateString('en-IE', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
/* Pure: the schedule for one order, at time `at` (ms). Used by the pilot and by the tests with simulated dates. */
export function reimbursementSchedule({ confirmed_at, fee_recorded_at = null, fee_time_known = true, reimbursed_at = null, days = 7, at = Date.now() }) {
  const confirmed_date = dublinDate(confirmed_at), original_due = addDate(confirmed_date, days), originalEnd = dublinDayEnd(original_due);
  const done = reimbursed_at ? Date.parse(reimbursed_at) : null, ref = done ?? at;
  // Stripe gave no time for recording the fee: the original deadline stays in force and the case is for review
  const unknown = !!fee_recorded_at && !fee_time_known;
  const rec = fee_recorded_at && fee_time_known ? Date.parse(fee_recorded_at) : null;
  const extended = unknown ? false : rec !== null ? rec >= originalEnd : ref >= originalEnd;   // the fee was not recorded by the end of the original deadline
  const fee_recorded_date = rec !== null ? dublinDate(rec) : null;
  const extended_due = extended && fee_recorded_date ? addDate(fee_recorded_date, days) : null;
  const due = extended ? extended_due : original_due, dueEnd = due ? dublinDayEnd(due) : null;
  return { confirmed_date, day: dateDiff(confirmed_date, dublinDate(ref)), original_due, fee_recorded_date, extended, extended_due, due,
    fee_time_unknown: unknown, extension_for_review: unknown && Date.parse(fee_recorded_at) >= originalEnd,
    waiting_for_fee_date: extended && !extended_due, overdue: dueEnd !== null && ref >= dueEnd, completed_late: done !== null && dueEnd !== null && done >= dueEnd };
}
const REIMB_FAIL_FLAG = 'Processing reimbursement failing';
const REIMB_FAIL_THRESHOLD = 3;
const iso = s => new Date(s * 1000).toISOString();
async function shortfallAmounts(env, id) {
  const r = await one(env, `SELECT (SELECT COALESCE(SUM(cents - settled_cents), 0) FROM checkout_owed WHERE order_id = ?1 AND kind = 'processing_shortfall') AS outstanding,
    (SELECT COALESCE(SUM(amount_cents), 0) FROM order_ledger WHERE order_id = ?1 AND kind = 'processing_shortfall_paid') AS paid,
    (SELECT COALESCE(SUM(amount_cents), 0) FROM order_ledger WHERE order_id = ?1 AND kind = 'processing_reimbursement') AS reimbursed`, id);
  return { shortfallOutstanding: r.outstanding, shortfallPaid: r.paid, reimbursed: r.reimbursed };
}
async function saveProcessing(env, id, p) { await run(env, 'UPDATE checkout_orders SET processing = ?, updated_at = ? WHERE id = ?', JSON.stringify(p), now(), id); }
/* Records any processing reimbursement Stripe already made for this order but the pilot did not record (for example when
   Stripe accepted the refund but its answer was lost). Read from Stripe's own list of the fee's refunds; never creates one. */
async function adoptFeeRefunds(env, o) {
  const list = await S.listFeeRefunds(env, { fee: o.application_fee_id });
  let n = 0;
  for (const fr of (list && list.data) || []) {
    const md = fr.metadata || {};
    if (md.plotart_kind !== 'processing_reimbursement' || md.plotart_order !== o.id) continue;
    if (await one(env, "SELECT 1 AS x FROM order_ledger WHERE kind = 'processing_reimbursement' AND provider_ref = ?", fr.id)) continue;
    await env.DB.batch([ledgerSt(env, o.id, 'processing_reimbursement', fr.amount, fr.id, 'PlotArt reimburses Stripe’s processing fee and VAT on it (fee model B) · recorded from Stripe’s list of the fee’s refunds'),
      evSt(env, o.id, 'system', 'processing_reimbursement_adopted', o.status, o.status, { fee_refund: fr.id, amount: fr.amount, created: fr.created ? iso(fr.created) : null })]);
    n++;
  }
  return n;
}
/* Alerts (test sink only): founder at day 5 and at the deadline; one delay notice to the artist when the extension applies. */
async function reimbursementAlerts(env, o, p) {
  if (!['awaiting_fee', 'outstanding'].includes(p.status)) return p;
  const days = deadlines(env).reimburse_days, s = reimbursementSchedule({ confirmed_at: p.confirmed_at, fee_recorded_at: p.fee_recorded_at, fee_time_known: p.fee_recorded_basis !== 'first_seen_by_pilot', days });
  const al = { ...(p.alerts || {}) }, prov = deadlines(env).reimburse_provisional ? ' (provisional deadline)' : '';
  const amount = p.status === 'outstanding' ? eur(Math.max(0, p.cost - (p.reimbursed_cents || 0))) : 'not yet known (Stripe has not recorded the fee; nothing is estimated)';
  if (s.extended && !p.delay_notice_at) {
    await notify(env, o, 'reimbursement_delayed', delayNoticeText(o, s, days), { artistOnly: true, subject: `PlotArt payment pilot · ${o.reference} · processing fee reimbursement: Stripe has not yet recorded the fee` });
    await notify(env, o, 'reimbursement_extended', `Order ${o.reference}: the original reimbursement date (end of ${longDate(s.original_due)}) passed before Stripe recorded the processing fee. The extension applies: the reimbursement is now due by the end of the seventh day after the day Stripe records the fee${s.extended_due ? ` (${longDate(s.extended_due)})` : ''}${prov}. One delay notice has gone to the artist. Founder desk: Processing reimbursements.`, { founderOnly: true });
    p = { ...p, delay_notice_at: now() };
  }
  if (!s.extended && s.day >= 5 && !s.overdue && !al.day5) {
    await notify(env, o, 'reimbursement_day5', `Day ${s.day}: order ${o.reference} — processing reimbursement still outstanding. Status: ${p.status === 'outstanding' ? 'fee known, reimbursement outstanding' : 'waiting for Stripe to record the fee'}. Amount: ${amount}. Due by the end of ${longDate(s.due)} (Irish time)${prov}.${p.last_error ? ` Last attempt failed: ${p.last_error}` : ''} Founder desk: Processing reimbursements.`, { founderOnly: true });
    al.day5 = now();
  }
  const dk = s.extended ? 'extended_deadline' : 'deadline';
  if (s.overdue && !al[dk]) {
    await notify(env, o, 'reimbursement_' + dk, `OVERDUE: order ${o.reference} — the processing reimbursement was due by the end of ${longDate(s.due)} (Irish time)${prov} and is still outstanding. Status: ${p.status === 'outstanding' ? 'fee known, reimbursement outstanding' : 'waiting for Stripe to record the fee'}. Amount: ${amount}.${p.last_error ? ` Last attempt failed: ${p.last_error}` : ''} Founder desk: Processing reimbursements → Reconcile processing fee.`, { founderOnly: true });
    al[dk] = now();
  }
  return { ...p, alerts: al };
}
/* What the artist is told about the reimbursement (statement line, and the closing message after a delay notice).
   It states only what the pilot can show: that Stripe accepted PlotArt's refund of part of its application fee (Stripe's
   fee_refund object and its time). Where the application fee left on the order cannot cover it, the rest is owed by
   PlotArt directly under PA-PAY 3.5 and both amounts are shown. The artist's bank payout is a separate matter. */
export function transferLines(items) {
  const out = [];
  for (const w of items) for (const p of w.payments || []) if (p.method === 'bank_transfer')
    out.push(p.returned_on ? `${eur(p.cents)} sent by bank transfer on ${longDate(p.executed_on)} was returned by the bank on ${longDate(p.returned_on)} and is owed again.`
      : `${eur(p.cents)} sent by bank transfer on ${longDate(p.executed_on)}.`);
  return out;
}
const owedDueDay = w => w.due_basis_date ? dublinDate(Date.parse(w.due_at) - 1) : w.due_at.slice(0, 10);
export function reimbursementWording(p, { shortfallOutstanding = 0, reimbursed = null, items = [] } = {}) {
  if (!p || !p.status || p.status === 'awaiting_fee') return 'We have not yet been able to confirm the fee Stripe charged on this payment. Nothing is estimated: PlotArt reimburses it once Stripe has recorded it.';
  if (p.status === 'outstanding') return `Stripe charged a processing fee and VAT of ${eur(p.cost)} on this payment. PlotArt’s reimbursement of it is outstanding.`;
  const fr = p.fee_refund, when = fr && fr.accepted_at ? longDate(dublinDate(fr.accepted_at)) : null;
  const paid = reimbursed ?? (p.reimbursed_cents || 0), rest = Math.max(0, p.cost - paid);
  const out = [paid > 0
    ? `PlotArt reimbursed ${eur(paid)}${p.status === 'shortfall' ? ` of the ${eur(p.cost)} processing fee and VAT` : ''} through Stripe${fr ? `: Stripe accepted PlotArt’s refund of that amount of its application fee${when ? ` on ${when}` : ''} (Stripe reference ${fr.id})` : ''}. ${REIMBURSEMENT_CREDIT_WORDING}`
    : `Stripe charged a processing fee and VAT of ${eur(p.cost)} on this payment. None of it could be reimbursed through Stripe, because nothing was left of PlotArt’s application fee on this order.`];
  if (p.status === 'shortfall' && rest > 0) {
    const proc = items.filter(w => w.kind === 'processing_shortfall'), due = proc[0] && proc[0].due_basis_date ? owedDueDay(proc[0]) : null;
    out.push(`The remaining ${eur(rest)} could not be reimbursed through Stripe, because it is more than what was left of PlotArt’s application fee on this order. PlotArt pays it to you directly by bank transfer (clause 3.5)${due ? `, by the end of ${longDate(due)} (Irish time)` : ''}.`);
    out.push(...transferLines(proc));
    out.push(shortfallOutstanding > 0 ? `Still owed to you by PlotArt: ${eur(shortfallOutstanding)}. Your statement shows it under “Owed by PlotArt, not yet paid” until it is paid.` : 'Nothing is still owed.');
  }
  if (paid > 0) out.push('When the amount reimbursed through Stripe reaches your bank account depends on your Stripe payout schedule.');
  return out.join(' ');
}
/* Run 33 (18 Nov 2026, real sandbox): when Stripe accepted the application-fee refund it added the same amount to the
   artist's Stripe balance at the same second, as a balance transaction of type 'adjustment' on that payment's charge,
   status 'pending'. The pilot's runtime key cannot read the artist's balance (balance_read refused), so the pilot records
   Stripe's acceptance; the credit itself is seen in the artist's Stripe Dashboard. */
export const REIMBURSEMENT_CREDIT_WORDING = 'Stripe adds it to your Stripe balance as an adjustment on this payment; it shows as pending until Stripe makes it available.';
/* The one delay notice. It says only what PlotArt can establish: that it has not yet been able to confirm the fee. */
export function delayNoticeText(o, s, days = 7, today = dublinDate(Date.now())) {
  const n = days === 7 ? 'seven' : String(days), nth = days === 7 ? 'seventh' : days + 'th', ex = addDate(today, 1);
  return [`Order ${o.reference}`, '',
    `Stripe confirmed your buyer’s payment on ${longDate(s.confirmed_date)}. PlotArt reimburses Stripe’s processing fee, and the VAT Stripe charges on it, within ${n} calendar days of the payment: for this order, by the end of ${longDate(s.original_due)} (Irish time).`, '',
    `We have not yet been able to confirm the fee Stripe charged on this payment, so we do not yet know the exact amount. PlotArt does not estimate it.`, '',
    `If Stripe had not recorded the fee by the end of ${longDate(s.original_due)}, PlotArt will reimburse it at the latest by the end of the ${nth} calendar day after the day Stripe records it (Irish time). For example, if Stripe records it on ${longDate(ex)}, the latest date is ${longDate(addDate(ex, days))}. If Stripe’s records show that it had recorded the fee by ${longDate(s.original_due)}, that date still applies, and we will tell you.`, '',
    `We will write again with the amount and the date that applies when the reimbursement is made. Your payout from Stripe to your bank is separate and follows your usual Stripe payout schedule.`, '',
    `This message comes from the PlotArt payment pilot (test mode).`].join('\n');
}
/* The next (closing) notice after a delay notice: the amount, and the date that actually applied, corrected if Stripe's
   own record shows the fee was recorded in time, or stated as the original date (for review) if Stripe gave no time. */
export function closingNoticeText(o, p, s, wording) {
  const date = s.fee_time_unknown
    ? `Stripe did not give the time it recorded the fee, so we cannot establish that the later date applies. The date that applies is the original one: the end of ${longDate(s.original_due)} (Irish time). We are reviewing this order.`
    : s.extended
      ? `Stripe recorded the fee on ${longDate(s.fee_recorded_date)}, after the original date, so the latest date for this reimbursement was the end of ${longDate(s.extended_due)} (Irish time).`
      : `Correction to our earlier message: Stripe’s records show it recorded the fee on ${longDate(s.fee_recorded_date)}, by the original date. The date that applies is therefore the end of ${longDate(s.original_due)} (Irish time), not a later date.`;
  return [`Order ${o.reference}`, '', `We have now been able to confirm the fee Stripe charged on this payment.`, wording, '', date, '', 'This message comes from the PlotArt payment pilot (test mode).'].join('\n');
}
/* Reimburses Stripe's actual processing cost for a paid, commission-bearing order. Safe to call any number of times: the
   amount still due is worked out from the ledger, the idempotency key is fixed for that state, and after any failed attempt
   (or on the founder's "Reconcile processing fee") the pilot first reads Stripe's list of the fee's refunds and records any
   reimbursement Stripe already made, so a lost answer cannot lead to a second one. */
export async function reconcileProcessing(env, o, actor = 'system') {
  if (!o || !o.payment_intent || !(o.commission_cents > 0)) return { status: 'not_applicable' };
  o = await ensureCharge(env, o);
  const t = now();
  let p = J(o.processing) || {};
  if (!p.confirmed_at) p = { ...p, confirmed_at: o.paid_at || t, confirmed_basis: 'pilot_verified_payment' };
  let ch = null;
  if (o.charge_id && (p.confirmed_basis === 'pilot_verified_payment' || !p.balance_transaction)) {
    ch = await S.getCharge(env, { account: o.provider_account, id: o.charge_id, expandBalance: !p.balance_transaction });
    if (ch && ch.created) p = { ...p, charge_created_at: iso(ch.created) };
    // fallback only: a succeeded card charge (see startClock)
    if (ch && ch.created && p.confirmed_basis === 'pilot_verified_payment' && (ch.status === undefined || ch.status === 'succeeded'))
      p = { ...p, confirmed_at: iso(ch.created), confirmed_basis: 'stripe_charge_created' };
  }
  if (o.charge_id && o.application_fee_id && !p.balance_transaction) {
    const bt = ch && ch.balance_transaction && typeof ch.balance_transaction === 'object' ? ch.balance_transaction : null;
    if (bt) {
      const when = bt.created ? { fee_recorded_at: iso(bt.created), fee_recorded_basis: 'stripe_balance_transaction_created' } : { fee_recorded_at: t, fee_recorded_basis: 'first_seen_by_pilot' };
      p = { ...p, ...processingFromBalance(bt), recorded_at: t, ...when };
      await env.DB.batch([st(env, 'UPDATE checkout_orders SET processing = ?, updated_at = ? WHERE id = ?', JSON.stringify(p), t, o.id),
        ledgerSt(env, o.id, 'processing_fee', p.cost, p.balance_transaction, `Stripe processing fee ${eur(p.stripe_fee)} + VAT on it ${eur(p.vat)}, charged by Stripe to the seller's balance`)]);
      if (p.excluded_fees) await event(env, o.id, 'system', 'processing_excluded_fees', o.status, o.status, { excluded_fees: p.excluded_fees, excluded_vat: p.excluded_vat, descriptions: p.descriptions });
      if (!bt.created) {
        const s0 = reimbursementSchedule({ confirmed_at: p.confirmed_at, days: deadlines(env).reimburse_days });
        await notify(env, o, 'reimbursement_fee_time_unknown', `FOR REVIEW: order ${o.reference} — Stripe returned the processing fee without the time it recorded it. The pilot can show only when it first saw it (${t}). The original deadline stays in force (end of ${longDate(s0.original_due)}, Irish time); no extension is assumed. Check the payment in the Stripe Dashboard.`, { founderOnly: true });
      }
    }
  }
  if (!p.balance_transaction) {
    p = await reimbursementAlerts(env, o, { ...p, status: 'awaiting_fee' });
    await saveProcessing(env, o.id, p);
    return { status: 'awaiting_fee' };
  }
  if ((p.attempts || 0) > 0 || actor !== 'system') { try { await adoptFeeRefunds(env, o); } catch (e) { if ((p.attempts || 0) > 0) { p = { ...p, last_error: `could not read the fee’s refunds at Stripe: ${String(e.message).slice(0, 200)}`, last_attempt_at: t, status: 'outstanding' }; p = await reimbursementAlerts(env, o, p); await saveProcessing(env, o.id, p); return { status: 'outstanding', error: p.last_error }; } } }
  const pot = await feePot(env, o), due = Math.max(0, p.cost - pot.reimbursed);
  const pay = Math.min(due, pot.left);
  if (pay > 0) {
    let fr;
    try { fr = await S.refundFee(env, { fee: o.application_fee_id, amount: pay, idem: `plotart-proc-${o.id}-${p.cost}-${pot.reimbursed}`, metadata: { plotart_order: o.id, plotart_kind: 'processing_reimbursement' } }); }
    catch (e) {
      const attempts = (p.attempts || 0) + 1, reason = String(e.message || e).slice(0, 300);
      p = { ...p, attempts, last_error: reason, last_attempt_at: t, reimbursed_cents: pot.reimbursed, status: 'outstanding' };
      await event(env, o.id, actor, 'processing_reimbursement_failed', o.status, o.status, { attempt: attempts, amount: pay, error: reason });
      if (attempts >= REIMB_FAIL_THRESHOLD) {
        const cur = await getOrder(env, o.id), rest = (cur.needs_resolution || '').split(' | ').filter(x => x && !x.startsWith(REIMB_FAIL_FLAG)).join(' | ');
        const s = reimbursementSchedule({ confirmed_at: p.confirmed_at, fee_recorded_at: p.fee_recorded_at, fee_time_known: p.fee_recorded_basis !== 'first_seen_by_pilot', days: deadlines(env).reimburse_days });
        await run(env, 'UPDATE checkout_orders SET needs_resolution = ?, updated_at = ? WHERE id = ?', [`${REIMB_FAIL_FLAG} (${attempts} attempts): ${reason}. The due date is unchanged (${s.due ? 'end of ' + s.due : 'pending'}). Check the reason, then use "Reconcile processing fee": it re-reads Stripe, records any reimbursement Stripe already made, and retries without creating a second one.`, rest].filter(Boolean).join(' | '), now(), o.id);
      }
      p = await reimbursementAlerts(env, o, p);
      await saveProcessing(env, o.id, p);
      return { status: 'outstanding', error: reason, attempts };
    }
    await env.DB.batch([ledgerSt(env, o.id, 'processing_reimbursement', pay, fr.id, `PlotArt reimburses Stripe's processing fee and VAT on it (fee model B)`),
      evSt(env, o.id, actor, 'processing_reimbursed', o.status, o.status, { amount: pay, fee_refund: fr.id, cost: p.cost, stripe_created: fr.created ? iso(fr.created) : null, platform_balance_transaction: typeof fr.balance_transaction === 'string' ? fr.balance_transaction : fr.balance_transaction && fr.balance_transaction.id || null })]);
    p = { ...p, fee_refund: { id: fr.id, amount: fr.amount, accepted_at: fr.created ? iso(fr.created) : t, accepted_basis: fr.created ? 'stripe_fee_refund_created' : 'pilot_time_of_answer',
      platform_balance_transaction: typeof fr.balance_transaction === 'string' ? fr.balance_transaction : fr.balance_transaction && fr.balance_transaction.id || null } };
  }
  if (due - pay > 0) await addShortfall(env, o, 'processing', due - pay, `Stripe's processing cost ${eur(p.cost)} exceeds what is left of the commission`,
    { event: 'stripe_fee_recorded', at: p.fee_recorded_at || t, source: p.fee_recorded_basis === 'stripe_balance_transaction_created' ? 'stripe' : 'pilot',
      review: p.fee_recorded_basis === 'stripe_balance_transaction_created' ? (pot.commission_refunded > 0 ? 'Commission was returned on this order before the fee was reimbursed: check whether the amount owed was established later than Stripe’s fee record.' : null)
        : 'Stripe gave no time for recording the fee: the start date is when the pilot first saw it.' });
  const after = await feePot(env, o), cur = J((await getOrder(env, o.id)).processing) || {};
  const status = after.reimbursed >= p.cost ? 'reimbursed' : 'shortfall';
  p = { ...cur, ...p, reimbursed_cents: after.reimbursed, status, last_error: null };
  if (status !== 'awaiting_fee' && !p.completed_at) {
    p.completed_at = (p.fee_refund && p.fee_refund.accepted_at) || t;
    const s = reimbursementSchedule({ confirmed_at: p.confirmed_at, fee_recorded_at: p.fee_recorded_at, fee_time_known: p.fee_recorded_basis !== 'first_seen_by_pilot', reimbursed_at: p.completed_at, days: deadlines(env).reimburse_days });
    p.completed_late = s.completed_late;
  }
  if (p.delay_notice_at && !p.completion_notice_at) {   // closes the loop opened by the delay notice (test sink)
    const sc = reimbursementSchedule({ confirmed_at: p.confirmed_at, fee_recorded_at: p.fee_recorded_at, fee_time_known: p.fee_recorded_basis !== 'first_seen_by_pilot', reimbursed_at: p.completed_at, days: deadlines(env).reimburse_days });
    await notify(env, o, 'reimbursement_completed', closingNoticeText(o, p, sc, reimbursementWording(p, { ...(await shortfallAmounts(env, o.id)), items: (await owedForStatements(env, [o.id]))[o.id] || [] })),
      { artistOnly: true, subject: `PlotArt payment pilot · ${o.reference} · processing fee reimbursement` });
    p.completion_notice_at = now();
  }
  await saveProcessing(env, o.id, p);
  await dropFlag(env, o.id, REIMB_FAIL_FLAG);
  return { status, cost: p.cost, reimbursed: after.reimbursed };
}
/* The founder records a shortfall PlotArt paid the artist outside Stripe. */
/* The founder records a direct payment PlotArt made to the artist for this order's shortfalls (oldest first). The reference is
   the bank's transfer reference and date: anything that looks like bank details is refused, so none enters the records. */
export async function recordShortfallPaid(env, founder, id, b) {
  await requireInstalled(env);
  const o = await getOrder(env, id);
  if (!o) throw new Bad('Not found', 404);
  const open = await all(env, `SELECT * FROM checkout_owed WHERE order_id = ? AND kind IN ('processing_shortfall','commission_shortfall') AND settled_cents < cents ORDER BY due_at, arisen_at, rowid`, o.id);
  const owed = open.reduce((a, w) => a + w.cents - w.settled_cents, 0);
  const amt = Number(b && b.amount_cents), ref = String((b && (b.reference ?? b.evidence)) || '').trim(), ex = String((b && b.executed_on) || '').trim();
  if (!(owed > 0)) throw new Bad('PlotArt owes nothing outside Stripe on this order', 409);
  if (!Number.isInteger(amt) || amt <= 0 || amt > owed) throw new Bad(`Enter the amount paid, up to ${eur(owed)}`, 400);
  if (ref.length < 6 || ref.length > 200) throw new Bad('Give the bank’s transfer reference (6–200 characters)', 400);
  if (looksLikeBankDetails(ref)) throw new Bad('That looks like bank details. Record only the transfer reference: bank details are never stored here.', 400);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(ex) || dublinDate(Date.parse(ex + 'T12:00:00Z')) !== ex) throw new Bad('Give the date PlotArt’s bank shows the transfer as executed (YYYY-MM-DD)', 400);
  if (ex > dublinDate(Date.now())) throw new Bad('The execution date cannot be in the future: record the payment once the bank shows it executed', 400);
  if (o.paid_at && ex < dublinDate(o.paid_at)) throw new Bad('The execution date is before the buyer’s payment', 400);
  if (await one(env, 'SELECT 1 AS x FROM checkout_owed_payments WHERE order_id = ? AND reference = ?', o.id, ref)) throw new Bad('A payment with this reference is already recorded for this order', 409);
  let left = amt;
  for (const w of open) { const part = Math.min(left, w.cents - w.settled_cents); if (part > 0) { await settleOwed(env, w, { cents: part, method: 'bank_transfer', reference: ref, actor: founder, executedOn: ex }); left -= part; } if (!left) break; }
  await env.DB.batch([ledgerSt(env, o.id, 'processing_shortfall_paid', amt, rid('sp'), `sent by bank transfer, executed ${ex}, ref ${ref}`.slice(0, 200)),
    evSt(env, o.id, founder, 'shortfall_paid', o.status, o.status, { amount: amt, reference: ref.slice(0, 200), executed_on: ex })]);
  await setOwedFlag(env, o.id);
  const rest = await one(env, `SELECT COALESCE(SUM(cents - settled_cents), 0) AS c, MIN(CASE WHEN settled_cents < cents THEN due_at END) AS due FROM checkout_owed WHERE order_id = ? AND kind IN ('processing_shortfall','commission_shortfall')`, o.id);
  await notify(env, o, 'owed_payment_sent', owedPaymentText(o, open[0], amt, ex, ref, rest.c, rest.due ? dublinDate(Date.parse(rest.due) - 1) : null),
    { artistOnly: true, subject: `PlotArt payment pilot · ${o.reference} · ${eur(amt)} sent to you by bank transfer` });
  return orderDetail(env, await getOrder(env, o.id), 'founder');
}
/* A bank transfer that was returned (for example, rejected by the receiving bank): the outstanding amount is restored and the
   payment stays in the history, marked returned. The due date does not change. */
export async function recordShortfallReturned(env, founder, id, b) {
  await requireInstalled(env);
  const o = await getOrder(env, id);
  if (!o) throw new Bad('Not found', 404);
  const p = await one(env, "SELECT * FROM checkout_owed_payments WHERE id = ? AND order_id = ? AND method = 'bank_transfer'", String((b && b.payment_id) || ''), o.id);
  if (!p) throw new Bad('Choose a bank transfer recorded on this order', 404);
  if (await one(env, 'SELECT 1 AS x FROM checkout_owed_payment_returns WHERE payment_id = ?', p.id)) throw new Bad('This transfer is already recorded as returned', 409);
  const on = String((b && b.returned_on) || '').trim(), why = String((b && b.reason) || '').trim();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(on) || on > dublinDate(Date.now()) || on < p.executed_on) throw new Bad('Give the date the bank shows the transfer as returned (YYYY-MM-DD, not before it was executed)', 400);
  if (why.length < 5 || why.length > 300 || looksLikeBankDetails(why)) throw new Bad('Give the reason the bank gave (5–300 characters, no bank details)', 400);
  const rr = rid('or');
  await env.DB.batch([
    st(env, 'INSERT INTO checkout_owed_payment_returns (id, payment_id, owed_id, order_id, cents, returned_on, reason, recorded_by, at) VALUES (?,?,?,?,?,?,?,?,?)', rr, p.id, p.owed_id, o.id, p.cents, on, why, founder, now()),
    st(env, 'UPDATE checkout_owed SET settled_cents = settled_cents - ?, last_return_id = ? WHERE id = ?', p.cents, rr, p.owed_id),
    ledgerSt(env, o.id, 'processing_shortfall_paid', -p.cents, rr, `bank transfer ${p.reference} returned ${on}: ${why}`.slice(0, 200)),
    evSt(env, o.id, founder, 'shortfall_transfer_returned', o.status, o.status, { payment: p.id, amount: p.cents, returned_on: on, reason: why })]);
  await setOwedFlag(env, o.id);
  return orderDetail(env, await getOrder(env, o.id), 'founder');
}
/* The artist's statement for one order: every amount separated, nothing netted silently. All cents. "Paid" amounts are in
   net proceeds; amounts PlotArt owes but has not yet paid are shown separately and are NOT in net proceeds. */
export function statement(o, ledger, owed = []) {
  const sum = (...k) => ledger.filter(l => k.includes(l.kind)).reduce((a, l) => a + l.amount_cents, 0);
  const out = (...k) => owed.filter(w => k.includes(w.kind)).reduce((a, w) => a + w.cents - w.settled_cents, 0);
  const p = J(o.processing) || {}, df = J(o.dispute_fees) || {};
  const gross = o.amount_received_cents ?? (o.paid_at ? (o.artwork_cents || 0) + (o.delivery_cents || 0) : 0);
  if (!gross) return null;
  const commission = o.commission_cents || 0, commission_refunded = -sum('commission_refund');
  const processing_fee = p.stripe_fee || 0, processing_vat = p.vat || 0;
  const reimbursed = sum('processing_reimbursement'), shortfall_paid = sum('processing_shortfall_paid');
  const shortfall_owed = out('processing_shortfall', 'commission_shortfall'), commission_refund_owed = out('lost_dispute_commission');
  const refunded_to_buyer = -sum('artwork_refund', 'artwork_refund_reversed', 'delivery_refund', 'delivery_refund_reversed', 'external_refund');
  const disputes = sum('dispute', 'dispute_reinstated');
  const dispute_fees_charged = -sum('dispute_fee'), dispute_fees_returned = sum('dispute_fee_returned');
  const unavailable = Object.entries(df).filter(([, v]) => v && v.status === 'unavailable').map(([k]) => k);
  const other_fees = p.excluded_fees ? p.excluded_fees + (p.excluded_vat || 0) : 0;   // e.g. add-on fees on the same payment: charged by Stripe, not reimbursed
  const net = gross - commission + commission_refunded - processing_fee - processing_vat + reimbursed + shortfall_paid - refunded_to_buyer + disputes
    - dispute_fees_charged + dispute_fees_returned - other_fees;
  const notes = ['Stripe payout fees, if any, are charged by Stripe separately and are not included.'];
  if (unavailable.length) notes.push(`Stripe has not supplied the fee lines for dispute ${unavailable.join(', ')}: its dispute fees are NOT included above.`);
  if (shortfall_owed || commission_refund_owed) notes.push('Amounts PlotArt owes but has not yet paid are shown separately and are not included in net proceeds.');
  return { currency: o.currency || 'eur', gross_payment: gross, of_which_artwork: o.artwork_cents, of_which_delivery: o.delivery_cents || 0,
    plotart_commission: commission, commission_refunded, stripe_processing_fee: processing_fee, vat_on_processing_fee: processing_vat,
    processing_reimbursed_by_plotart: reimbursed, shortfall_paid_by_plotart: shortfall_paid, other_stripe_fees_not_reimbursed: other_fees,
    refunded_to_buyer, disputes_net: disputes, dispute_fees_charged_by_stripe: dispute_fees_charged, dispute_fees_returned_by_stripe: dispute_fees_returned,
    dispute_fees_status: o.dispute_status === 'none' ? 'no dispute' : unavailable.length ? 'unavailable from Stripe (not included)' : 'recorded from Stripe',
    net_proceeds: net,
    owed_by_plotart_not_yet_paid: { shortfall: shortfall_owed, commission_refund_after_lost_dispute: commission_refund_owed },
    shortfall_still_owed_by_plotart: shortfall_owed, commission_refund_owed: commission_refund_owed,
    net_proceeds_once_owed_amounts_are_paid: net + shortfall_owed + commission_refund_owed,
    processing_status: o.commission_cents > 0 ? (p.status || 'awaiting_fee') : 'not_applicable',
    processing_reimbursement: o.commission_cents > 0 ? reimbursementWording(p, { shortfallOutstanding: out('processing_shortfall'), reimbursed, items: owed }) : null,
    bank_transfers: owed.filter(w => SHORTFALL_KINDS.includes(w.kind)).map(w => ({ what: w.kind === 'commission_shortfall' ? 'Commission PlotArt returns to you' : 'Processing fee and VAT not covered through Stripe',
      amount_cents: w.cents, still_owed_cents: w.cents - w.settled_cents, due: w.due_basis_date ? `by the end of ${longDate(owedDueDay(w))} (Irish time)` : owedDueDay(w), lines: transferLines([w]) })),
    processing_reimbursed_through_stripe: reimbursed, processing_still_owed_by_bank_transfer: out('processing_shortfall'),
    not_included: notes.join(' ') };
}
async function feeRefund(env, founder, o, { fee, reason, refundId = null, providerRefund = null, owed = null, basis = null }) {
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
  // Model B: the processing reimbursement and commission refunds share the application fee. What cannot be returned
  // from it any more becomes a shortfall PlotArt pays directly (never silently left with the artist, never paid twice).
  const pot = await feePot(env, o), pay = Math.min(fee, pot.left), key = refundId || (owed && owed.item_key) || `commission-${fee}-${pot.commission_refunded}`;
  if (fee - pay > 0) await addShortfall(env, o, `commission:${key}`, fee - pay, `commission refund of ${eur(fee)} owed under the artist's agreement exceeds what is left of the application fee after the processing reimbursement`, basis);
  if (pay <= 0) {
    await env.DB.batch([...(refundId ? [st(env, "UPDATE order_refunds SET fee_refund_id = ?, updated_at = ? WHERE id = ?", `none:shortfall:${refundId}`, now(), refundId)] : []),
      evSt(env, o.id, founder, 'commission_refund_shortfall', o.status, o.status, { amount: fee, refund: providerRefund })]);
    if (owed) { await settleOwed(env, owed, { cents: fee, method: 'moved_to_direct_payment', reference: `commission:${key}`, actor: founder }); await dropFlag(env, o.id, 'dispute lost'); }
    return orderDetail(env, await getOrder(env, o.id), 'founder');
  }
  const idem = `plotart-feerefund-${refundId || o.id + '-commission-' + fee}-${pay}`;
  const fr = await S.refundFee(env, { fee: feeId, amount: pay, idem, metadata: { plotart_order: o.id, plotart_kind: 'commission_refund', reason: reason.slice(0, 200) } });
  await env.DB.batch([ledgerSt(env, o.id, 'commission_refund', -pay, fr.id, reason),
    ...(refundId ? [st(env, 'UPDATE order_refunds SET fee_refund_id = ?, updated_at = ? WHERE id = ?', fr.id, now(), refundId)] : []),
    evSt(env, o.id, founder, 'commission_refunded', o.status, o.status, { amount: pay, owed: fee, fee_refund: fr.id, refund: providerRefund })]);
  if (owed) {   // the lost-dispute queue item: settled by what went back through Stripe, plus any part moved to a direct payment (its own queue item)
    await settleOwed(env, owed, { cents: pay, method: 'stripe_application_fee_refund', reference: fr.id, actor: founder });
    if (fee - pay > 0) await settleOwed(env, owed, { cents: fee - pay, method: 'moved_to_direct_payment', reference: `commission:${key}`, actor: founder });
  }
  if (!refundId) await dropFlag(env, o.id, 'dispute lost');
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
    await setOwedFlag(env, id);   // settling the refund never hides money PlotArt still owes the artist
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
/* ---------------------------------------------------------------- the buyer's purchase confirmation
   Prepared once, when Stripe's verified completion has made the sale: the purchased artwork, the seller, the amounts, the
   delivery and return arrangements, the accepted terms (identifier, fingerprint and full text) and the cancellation
   information with the model cancellation form. The exact text and its fingerprint are kept; every delivery attempt is
   recorded. In test mode it goes only to the test sink; the buyer can also read it from their quote link. */
const money = c => `EUR ${(c / 100).toFixed(2)}`;
const PARTY_TXT = { artist: 'the artist (seller)', buyer: 'you (the buyer)', transporter: 'the transporter', plotart: 'PlotArt', not_applicable: 'not applicable' };
function termsText(html) {
  return String(html || '').replace(/<(script|style)[\s\S]*?<\/\1>/gi, '').replace(/<\/(p|h[1-6]|li|tr|div|section)>|<br\s*\/?>/gi, '\n').replace(/<li[^>]*>/gi, '  • ')
    .replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;|&rsquo;/g, '’')
    .split('\n').map(l => l.replace(/\s+/g, ' ').trim()).filter((l, i, a) => l || (a[i - 1] || '')).join('\n').trim();
}
export function confirmationText(q, o, terms, origin) {
  const s = q.seller, a = q.artwork || {}, d = q.delivery || {};
  const trader = s.trader_status === 'trader';
  const L = [];
  L.push('PURCHASE CONFIRMATION', 'TEST MODE: this is a PlotArt payment-pilot test. No real payment was taken and no artwork was sold.', '');
  L.push(`Order reference: ${o.reference}`, `Payment confirmed by Stripe: ${o.paid_at}`, `Quote version ${q.quote_version}, fingerprint ${o.quote_sha256}`, '');
  L.push('THE SELLER (your contract of sale is with the artist)', `${s.legal_name}${s.trading_name ? ` trading as ${s.trading_name}` : ''} (${s.name})`, `Address: ${s.address}`,
    ...(s.returns_address && s.returns_address !== s.address ? [`Returns and complaints: ${s.returns_address}`] : []), `Email: ${s.email}`, `Telephone: ${s.phone}`,
    ...(s.vat_number ? [`VAT number: ${s.vat_number}`] : []), `Sells as a trader: ${trader ? 'yes' : 'no'}`,
    `PlotArt (PlotNua, operated by Colin Macaulay, CRO business name no. 794392, hello@plotnua.ie) introduced you to the seller and provided the checkout. PlotArt is not the seller.`, '');
  L.push('THE ARTWORK', `${a.title || 'Original artwork'}${a.medium ? `, ${a.medium}` : ''}${a.h_cm ? `, ${a.h_cm} × ${a.w_cm}${a.d_cm ? ' × ' + a.d_cm : ''} cm` : ''}${a.year ? `, ${a.year}` : ''}. One original.`, '');
  L.push('WHAT YOU PAID', `Artwork: ${money(q.amounts.artwork_cents)}`, `Packing, transport and transit insurance: ${money(q.amounts.delivery_cents)}`, `Total paid by card through Stripe to the seller's own Stripe account: ${money(q.amounts.total_cents)}`, '');
  L.push('DELIVERY', `From ${d.collection_county} to ${d.destination}; delivery window: ${d.delivery_window}`, `Packed by ${PARTY_TXT[d.packer]}; transport contracted by ${PARTY_TXT[d.transport_contracting_party]}${d.transporter_name ? ` (${d.transporter_name})` : ''}; installation: ${PARTY_TXT[d.installation]}; import costs: ${PARTY_TXT[d.import_costs]}`,
    `Transit insurance: ${d.cover_provider}, held by ${PARTY_TXT[d.insured_party]}, up to ${money(d.covered_value_cents)}; period: ${d.cover_period}; claims: ${d.claims_contact} (ref. ${d.cover_confirmation_ref})`,
    `Tracking: ${d.tracking}. ${d.signed_receipt ? 'Signed receipt on delivery.' : ''}${d.condition_photos ? ' Condition photographs before dispatch and on arrival.' : ''}`, '');
  L.push('RETURNS', `Method: ${d.return_method}`, `Return address: ${d.return_address}`, `Arranged by: ${PARTY_TXT[d.return_arranged_by]}`,
    `Cost of returning the artwork if you cancel for a change of mind: ${d.return_cost_basis === 'fixed' ? money(d.return_cost_cents) : `up to about ${money(d.return_cost_cents)} (estimated maximum)`}. If the artwork is damaged, faulty or not as described, the seller bears the return cost.`, '');
  if (trader) L.push('YOUR RIGHT TO CANCEL', 'You may cancel this purchase without giving a reason within 14 days from the day you, or someone you name other than the carrier, receive the artwork. Tell the seller, or PlotArt on the seller\'s behalf (hello@plotnua.ie), clearly that you are cancelling; you may use the model form below. Return the artwork within 14 days of cancelling. The seller refunds everything you paid, including the delivery charge, within 14 days of being told, and may wait until the artwork is back or you show you have sent it. Full details are in the purchase terms below.', '');
  else L.push('YOUR RIGHT TO CANCEL', 'The seller has declared that they do not sell as a trader, so the statutory right to cancel does not apply to this purchase. See the purchase terms below.', '');
  L.push(`PURCHASE TERMS YOU ACCEPTED: ${terms.doc_id} (${terms.title})`, `Fingerprint (SHA-256): ${terms.html_sha256}`, `Online: ${origin}/terms/${terms.doc_id}.html`, '', termsText(terms.html), '');
  if (trader) L.push('MODEL CANCELLATION FORM', '(Complete and return this form only if you wish to cancel the contract.)', `To: ${s.legal_name}, ${s.returns_address || s.address}, ${s.email} — or to PlotArt on the seller's behalf, hello@plotnua.ie`,
    `I/We [*] hereby give notice that I/We [*] cancel my/our [*] contract of sale of the following goods [*]: ${a.title || 'original artwork'}, order reference ${o.reference}`,
    'Ordered on [*] / received on [*]', 'Name of consumer(s):', 'Address of consumer(s):', 'Signature of consumer(s) (only if this form is notified on paper):', 'Date:', '[*] Delete as appropriate.', '');
  L.push(`Questions: the seller (${s.email}, ${s.phone}) or PlotArt (hello@plotnua.ie), quoting ${o.reference}.`);
  return L.join('\n');
}
/* One stored message per order, kind and item (e.g. per refund): the text is fixed when prepared and never re-rendered. */
async function prepareMessage(env, o, { kind, key = '', subject, body }) {
  const id = rid('m');
  const r = await run(env, `INSERT INTO order_messages (id, order_id, kind, item_key, recipient_role, subject, body, sha256, created_at) VALUES (?,?,?,?, 'buyer', ?,?,?,?)
    ON CONFLICT(order_id, kind, item_key) DO NOTHING`, id, o.id, kind, key, subject, body, await sha256(body), now());
  const m = await one(env, 'SELECT * FROM order_messages WHERE order_id = ? AND kind = ? AND item_key = ?', o.id, kind, key);
  if (r.meta.changes) await deliverMessage(env, o, m);   // a duplicate request never sends again
  return m;
}
export const MAX_MESSAGE_ATTEMPTS = 6;
async function deliverMessage(env, o, m) {
  let r;
  try { r = await deliver(env, { orderId: o.id, kind: m.kind, toRole: 'buyer', to: o.buyer_email, subject: m.subject, body: m.body, idempotencyKey: `plotart-msg-${m.id}` }); }
  catch (e) { r = { channel: 'test_sink', status: 'failed', detail: String(e.message || e).slice(0, 200) }; }
  await run(env, 'INSERT INTO order_message_deliveries (message_id, order_id, at, channel, status, detail) VALUES (?,?,?,?,?,?)', m.id, o.id, now(), r.channel, r.status, r.detail);
  await event(env, o.id, 'system', `${m.kind}_${r.status}`, o.status, o.status, { message: m.id, sha256: m.sha256 });
  return r;
}
/* Retries: a message whose last attempt failed (or that was never attempted) is tried again with growing gaps
   (at the next sweep, then 5, 20, 45, 80 minutes), at most MAX_MESSAGE_ATTEMPTS times; then it is flagged for the founder. */
async function retryMessages(env) {
  let retried = 0;
  const rows = await all(env, `SELECT m.*, (SELECT COUNT(*) FROM order_message_deliveries d WHERE d.message_id = m.id) AS attempts,
      (SELECT status FROM order_message_deliveries d WHERE d.message_id = m.id ORDER BY d.id DESC LIMIT 1) AS last_status,
      (SELECT at FROM order_message_deliveries d WHERE d.message_id = m.id ORDER BY d.id DESC LIMIT 1) AS last_at
    FROM order_messages m WHERE NOT EXISTS (SELECT 1 FROM order_message_deliveries d WHERE d.message_id = m.id AND d.status <> 'failed') LIMIT 50`);
  for (const m of rows) {
    const o = await getOrder(env, m.order_id);
    if (!o) continue;
    if (m.attempts >= MAX_MESSAGE_ATTEMPTS) {
      if (!(o.needs_resolution || '').includes(`message ${m.id}`)) await run(env, 'UPDATE checkout_orders SET needs_resolution = ?, updated_at = ? WHERE id = ?',
        [o.needs_resolution, `message ${m.id} (${m.kind}) could not be delivered after ${m.attempts} attempts: check the mail set-up, then re-deliver`].filter(Boolean).join(' | '), now(), o.id);
      continue;
    }
    const gap = Number.isFinite(Number(env.CHECKOUT_MESSAGE_RETRY_MINUTES)) && env.CHECKOUT_MESSAGE_RETRY_MINUTES !== undefined ? Number(env.CHECKOUT_MESSAGE_RETRY_MINUTES) : 5;
    if (m.last_at && Date.now() - Date.parse(m.last_at) < gap * (m.attempts - 1) * (m.attempts - 1) * 60_000) continue;
    await deliverMessage(env, o, m); retried++;
  }
  return retried;
}
export async function prepareConfirmation(env, o) {
  const have = await one(env, "SELECT * FROM order_messages WHERE order_id = ? AND kind = 'buyer_confirmation' AND item_key = ''", o.id);
  if (have) return have;
  if (!(await one(env, 'SELECT 1 AS x FROM artwork_sales WHERE order_id = ?', o.id))) return null;   // only a completed sale is confirmed
  const q = await quoteSnapshot(env, o);
  const terms = o.buyer_terms_doc_id && await one(env, 'SELECT * FROM payment_terms WHERE doc_id = ?', o.buyer_terms_doc_id);
  const full = terms && PAYMENT_TERMS[terms.doc_id];
  if (!q || !terms || !full) { await event(env, o.id, 'system', 'confirmation_not_prepared', o.status, o.status, { reason: !q ? 'no quote snapshot' : 'terms text unavailable' }); return null; }
  const body = confirmationText(q, o, { ...terms, html: full.html }, env.CHECKOUT_ORIGIN || '');
  return prepareMessage(env, o, { kind: 'buyer_confirmation', subject: `Purchase confirmation · ${(q.artwork && q.artwork.title) || 'Original artwork'} · ${o.reference}`, body });
}
/* Buyer notices about refunds (PA-BPT 8.2–8.4): one per refund and kind, kept and delivered like the confirmation. */
async function buyerRefundNotice(env, o, kind, rr, extra = '') {
  const amount = money((rr.artwork_cents || 0) + (rr.delivery_cents || 0)), seller = (J(o.seller) || {});
  const contact = `Questions: ${seller.legal_name || seller.name || 'the seller'}${seller.email ? ` (${seller.email})` : ''} or PlotArt (hello@plotnua.ie), quoting ${o.reference}.`;
  const T = { buyer_refund_pending: [`Your refund for ${o.reference} is pending`, `Your refund of ${amount} for order ${o.reference} has been requested through Stripe and is pending. It has NOT been completed yet: you have not been repaid until Stripe completes it. The seller is arranging for it to be completed and must make sure you are repaid within your legal time limits. While it is pending, the seller will not repay you another way as well. We will tell you if anything changes.`],
    buyer_refund_failed: [`Your refund for ${o.reference} could not be completed`, `Stripe could not complete your refund of ${amount} for order ${o.reference}${extra ? ` (${extra})` : ''}. You have NOT been repaid. The seller will repay you once, either by a new refund through Stripe or directly, for example by bank transfer, and PlotArt will confirm it with you.`],
    buyer_refund_reversed: [`Your refund for ${o.reference} was reversed`, `A refund of ${amount} for order ${o.reference} that Stripe first confirmed was later reversed by Stripe${extra ? ` (${extra})` : ''}, for example because the card was closed. You have NOT been repaid. The seller will repay you once, either by a new refund through Stripe or directly, and PlotArt will confirm it with you.`] }[kind];
  const body = ['TEST MODE: this is a PlotArt payment-pilot test message. No real payment or refund took place.', '', T[1], '', contact].join('\n');
  try { return await prepareMessage(env, o, { kind, key: rr.id, subject: T[0], body }); } catch (e) { await event(env, o.id, 'system', `${kind}_not_prepared`, o.status, o.status, { error: String(e.message).slice(0, 200) }); return null; }
}
export async function resendConfirmation(env, founder, id, b = {}) {
  const o = await getOrder(env, id);
  if (!o) throw new Bad('Not found', 404);
  const m = b.message_id ? await one(env, 'SELECT * FROM order_messages WHERE id = ? AND order_id = ?', b.message_id, o.id)
    : await one(env, "SELECT * FROM order_messages WHERE order_id = ? AND kind = 'buyer_confirmation' AND item_key = ''", o.id) || await prepareConfirmation(env, o);
  if (!m) throw new Bad('No such message for this order', 409);
  if (await one(env, 'SELECT 1 AS x FROM order_message_deliveries WHERE message_id = ?', m.id)) {
    const r = await deliverMessage(env, o, m);   // the same stored text, never re-rendered
    if (r.status !== 'failed') await dropFlag(env, o.id, `message ${m.id}`);
  }
  return orderDetail(env, await getOrder(env, o.id), 'founder');
}

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
  let processing_reconciled = 0;
  for (const o of await all(env, `SELECT * FROM checkout_orders WHERE payment_intent IS NOT NULL AND commission_cents > 0
      AND (processing IS NULL OR json_extract(processing, '$.status') IN ('awaiting_fee','outstanding')) ORDER BY paid_at LIMIT 25`)) {
    try { const r = await reconcileProcessing(env, o); if (!['awaiting_fee', 'outstanding'].includes(r.status)) processing_reconciled++; } catch { /* next sweep */ }
  }
  let confirmations = 0;
  for (const o of await all(env, `SELECT o.* FROM checkout_orders o JOIN artwork_sales s ON s.order_id = o.id
      WHERE NOT EXISTS (SELECT 1 FROM order_messages m WHERE m.order_id = o.id AND m.kind = 'buyer_confirmation') LIMIT 25`)) {
    try { if (await prepareConfirmation(env, o)) confirmations++; } catch { /* next sweep */ }
  }
  let dispute_fees_rechecked = 0;
  for (const o of await all(env, `SELECT * FROM checkout_orders WHERE dispute_fees LIKE '%"unavailable"%' AND updated_at >= ? LIMIT 10`, plusDays(t, -30))) {
    for (const [did, v] of Object.entries(J(o.dispute_fees) || {})) if (v.status === 'unavailable') { try { await recordDisputeFees(env, o, { id: did }); dispute_fees_rechecked++; } catch { /* next sweep */ } }
  }
  let messages_retried = 0;
  try { messages_retried = await retryMessages(env); } catch { /* next sweep */ }
  let owed_reminders = 0;
  try { owed_reminders = await remindOwed(env); } catch { /* next sweep */ }
  let refunds_reversed = 0;
  try { refunds_reversed = await recheckSucceededRefunds(env); } catch { /* next sweep */ }
  let refunds = null;
  try { refunds = await pollPendingRefunds(env); } catch (e) { refunds = { error: String(e.message || e).slice(0, 120) }; }
  return { reservations_released: released.meta.changes, quotes_expired: expired, deferred_replayed, refunds_reversed, processing_reconciled, confirmations, messages_retried, dispute_fees_rechecked, owed_reminders, ...refunds, ...(await retention(env)) };
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
      AND dispute_status <> 'open' AND NOT EXISTS (SELECT 1 FROM checkout_owed w WHERE w.order_id = checkout_orders.id AND w.settled_cents < w.cents)
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
    // never while anything is unresolved: an open dispute (even one arriving after the date was fixed), an amount owed, a flag or a pending refund
    if (await one(env, `SELECT 1 AS x FROM checkout_orders c WHERE c.id = ? AND (c.dispute_status = 'open' OR c.needs_resolution IS NOT NULL
        OR EXISTS (SELECT 1 FROM checkout_owed w WHERE w.order_id = c.id AND w.settled_cents < w.cents)
        OR EXISTS (SELECT 1 FROM order_refunds r WHERE r.order_id = c.id AND r.status = 'pending'))`, o.id)) { held++; continue; }
    await env.DB.batch(['order_events', 'order_fulfilment_events', 'order_refunds', 'order_ledger', 'checkout_sessions', 'artwork_reservations', 'artwork_sales', 'payment_events', 'checkout_hold_events', 'checkout_holds',
      'quote_snapshots', 'order_message_deliveries', 'order_messages', 'checkout_mail_sink', 'checkout_owed_payment_returns', 'checkout_owed_payments', 'checkout_owed']
      .map(t => st(env, `DELETE FROM ${t} WHERE order_id = ?`, o.id)).concat([st(env, 'DELETE FROM checkout_orders WHERE id = ?', o.id)]));
    purged++;
  }
  // seller information is kept only while the artist is in the pilot (each quote keeps its own copy)
  await run(env, `DELETE FROM seller_profiles WHERE artist_id NOT IN (SELECT id FROM artists) OR artist_id NOT IN (SELECT e.artist_id FROM payment_pilot_events e
    WHERE e.kind = 'opted_in' AND e.at = (SELECT MAX(x.at) FROM payment_pilot_events x WHERE x.artist_id = e.artist_id AND x.kind IN ('opted_in', 'left')))`);
  await run(env, 'DELETE FROM checkout_mail_sink WHERE order_id IS NULL AND at <= ?', new Date(Date.parse(at) - RETAIN_UNLINKED_EVENT_DAYS * 86400_000).toISOString());
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
