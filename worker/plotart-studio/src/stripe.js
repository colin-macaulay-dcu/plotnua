/* PlotArt · managed checkout pilot · Stripe Connect adapter (development 16 Nov 2026). NOT DEPLOYED. TEST MODE ONLY.

   Configuration chosen (see MANAGED-CHECKOUT-PILOT.md "Implementation"):
     · Each opted-in artist has their OWN Stripe account, created with the Accounts v2 API (POST /v2/core/accounts —
       Stripe no longer accepts POST /v1/accounts from new Connect platforms unless a compatibility setting is switched
       on). Configuration: dashboard = full (the artist's own full Stripe Dashboard), defaults.responsibilities.
       fees_collector = stripe (Stripe charges its processing fees to the ARTIST), losses_collector = stripe (Stripe —
       not PlotArt — carries unrecoverable negative balances); Stripe then collects requirements itself (read-only
       requirements_collector = stripe). These are the v2 equivalents of the v1 controller properties fees.payer =
       account, losses.payments = stripe, requirement_collection = stripe, stripe_dashboard.type = full. Stripe does
       not allow them to be changed once the merchant configuration is added, and the pilot re-checks them on every
       refresh. Onboarding uses Account Links v2. Everything else (status reads, Checkout, PaymentIntents, refunds,
       application fees, account.updated events) stays on v1, which Stripe documents as working with v2 accounts.
     · Every payment is a DIRECT CHARGE on the artist's account (Stripe-Account header), via Stripe-hosted Checkout. The
       artist is the merchant of record; PlotArt's commission is an application_fee_amount on the artwork only.
     · Refunds and disputes are debited from the artist's Stripe balance by Stripe. PlotArt refunds its application fee
       separately, by the exact amount the agreement requires (never Stripe's proportional default, which would include
       delivery).
   Secrets: STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET are Worker secrets (wrangler secret put), never in Git or in a
   browser. A LIVE key is refused in code: changing that needs a code change and the founder's explicit approval. */
export class StripeError extends Error { constructor(m, status = 502, code = null) { super(m); this.status = status; this.code = code; } }

export function testKey(env) {
  const k = String(env.STRIPE_SECRET_KEY || '');
  if (!k) return { ok: false, reason: 'STRIPE_SECRET_KEY is not set' };
  if (!/^(sk|rk)_test_[A-Za-z0-9]+$/.test(k)) return { ok: false, reason: 'Only a Stripe TEST key is accepted by the pilot' };
  return { ok: true };
}

/* Stripe's form encoding, including nested objects and arrays (a[b][0][c]=v). */
export function form(obj, prefix = '', out = []) {
  for (const [k, v] of Object.entries(obj)) {
    if (v === undefined || v === null) continue;
    const key = prefix ? `${prefix}[${k}]` : k;
    if (Array.isArray(v)) v.forEach((x, i) => (typeof x === 'object' ? form(x, `${key}[${i}]`, out) : out.push(`${encodeURIComponent(`${key}[${i}]`)}=${encodeURIComponent(x)}`)));
    else if (typeof v === 'object') form(v, key, out);
    else out.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(v))}`);
  }
  return out.join('&');
}

/* API v2 requests are JSON and must name an API version. Pinned here (override with STRIPE_V2_API_VERSION) and sent on
   /v2 requests only, so v1 calls keep the platform account's pinned version. */
export const V2_API_VERSION = '2026-10-28.endive';
/* v1 requests are pinned too (override with STRIPE_API_VERSION), so the pilot does not change behaviour when a Stripe
   account's default version differs. Endive (2026-09-30) removed payment_method_types from Checkout Sessions and
   PaymentIntents; the pilot uses allowed_payment_method_types instead. */
export const V1_API_VERSION = '2026-10-28.endive';

async function call(env, method, path, { body = null, account = null, idem = null, query = '' } = {}) {
  const k = testKey(env);
  if (!k.ok) throw new StripeError(k.reason, 503, 'not_configured');
  const base = env.STRIPE_API_BASE || 'https://api.stripe.com';
  if (env.STRIPE_API_BASE && env.ENVIRONMENT !== 'local') throw new StripeError('STRIPE_API_BASE is for local tests only', 500);
  const v2 = path.startsWith('/v2/');
  const headers = { Authorization: `Bearer ${env.STRIPE_SECRET_KEY}` };
  if (v2) headers['Stripe-Version'] = env.STRIPE_V2_API_VERSION || V2_API_VERSION;
  else headers['Stripe-Version'] = env.STRIPE_API_VERSION || V1_API_VERSION;
  if (account) headers['Stripe-Account'] = account;
  if (idem) headers['Idempotency-Key'] = idem;
  if (body) headers['Content-Type'] = v2 ? 'application/json' : 'application/x-www-form-urlencoded';
  const r = await fetch(`${base}${path}${query}`, { method, headers, body: body ? (v2 ? JSON.stringify(body) : form(body)) : undefined });
  const t = await r.text();
  let j; try { j = JSON.parse(t); } catch { throw new StripeError('Payment provider returned an unreadable response'); }
  if (!r.ok) throw new StripeError((j.error && j.error.message) || 'Payment provider error', r.status >= 500 ? 502 : 409, j.error && j.error.code);
  if (j.livemode === true) throw new StripeError('A live-mode object was returned to the test-mode pilot', 500, 'livemode');
  return j;
}

/* The configuration every pilot account must have. Checked on the object Stripe returns, not assumed. */
export function accountConfigProblems(a) {
  const r = (a && a.defaults && a.defaults.responsibilities) || {};
  const p = [];
  if (r.fees_collector !== 'stripe') p.push(`fees_collector is ${r.fees_collector} (must be stripe: the artist pays Stripe's fees)`);
  if (r.losses_collector !== 'stripe') p.push(`losses_collector is ${r.losses_collector} (must be stripe: Stripe carries negative balances)`);
  if (r.requirements_collector && r.requirements_collector !== 'stripe') p.push(`requirements_collector is ${r.requirements_collector} (must be stripe)`);
  if (a && a.dashboard !== 'full') p.push(`dashboard is ${a && a.dashboard} (must be full)`);
  return p;
}
const V2_INCLUDE = ['configuration.merchant', 'defaults', 'identity', 'requirements'];

export const createAccount = (env, { email, country, artistId }) => call(env, 'POST', '/v2/core/accounts', { idem: `plotart-acct-v2-${artistId}`, body: {
  contact_email: email,
  dashboard: 'full',
  identity: { country: String(country).toLowerCase() },
  defaults: { responsibilities: { fees_collector: 'stripe', losses_collector: 'stripe' } },
  configuration: { merchant: { capabilities: { card_payments: { requested: true } } } },
  metadata: { plotart_artist: artistId, plotart_pilot: 'managed-checkout-1' },
  include: V2_INCLUDE } });
/* No `configurations` field: API 2026-09-30.endive removed it from Account Links v2 (Stripe now works out which of the
   account's configurations need onboarding — here the merchant configuration set at creation). Sending it is rejected
   as "Unknown field". */
export const accountLink = (env, { account, refreshUrl, returnUrl }) => call(env, 'POST', '/v2/core/account_links', { body: {
  account, use_case: { type: 'account_onboarding', account_onboarding: { refresh_url: refreshUrl, return_url: returnUrl } } } });
/* v2 view: configuration (responsibilities, dashboard, merchant capability status). */
export const getAccountV2 = (env, account) => call(env, 'GET', `/v2/core/accounts/${encodeURIComponent(account)}`, { query: '?' + V2_INCLUDE.map((x, i) => `include[${i}]=${encodeURIComponent(x)}`).join('&') });
/* v1 view of the same account: charges_enabled / payouts_enabled / details_submitted / requirements — the same shape the
   account.updated webhook delivers, so one mapping serves both. */
export const getAccount = (env, account) => call(env, 'GET', `/v1/accounts/${encodeURIComponent(account)}`);

export const createSession = (env, { account, idem, order, title, artworkCents, deliveryCents, feeCents, expiresAt, buyerEmail, successUrl, cancelUrl, statement }) =>
  call(env, 'POST', '/v1/checkout/sessions', { account, idem, body: {
    mode: 'payment', currency: 'eur', allowed_payment_method_types: ['card'], customer_email: buyerEmail || undefined,
    // The quote is in euro. Adaptive Pricing would show and charge a converted local-currency price (seen in run 11: US$
    // prices and a currency chooser for a buyer outside the euro area), so the buyer would not pay the quoted figure.
    adaptive_pricing: { enabled: false },
    client_reference_id: order.id, expires_at: Math.floor(Date.parse(expiresAt) / 1000),
    success_url: successUrl, cancel_url: cancelUrl,
    line_items: [
      { quantity: 1, price_data: { currency: 'eur', unit_amount: artworkCents, product_data: { name: title.slice(0, 250), description: 'Original artwork' } } },
      ...(deliveryCents > 0 ? [{ quantity: 1, price_data: { currency: 'eur', unit_amount: deliveryCents, product_data: { name: 'Packing, transport and cover as quoted' } } }] : []),
    ],
    payment_intent_data: { application_fee_amount: feeCents > 0 ? feeCents : undefined, description: statement,
      metadata: { plotart_order: order.id, plotart_reference: order.reference, quote_version: order.quote_version } },
    metadata: { plotart_order: order.id, plotart_reference: order.reference, quote_version: order.quote_version } } });
export const expireSession = (env, { account, id }) => call(env, 'POST', `/v1/checkout/sessions/${encodeURIComponent(id)}/expire`, { account });
export const getSession = (env, { account, id }) => call(env, 'GET', `/v1/checkout/sessions/${encodeURIComponent(id)}`, { account });
export const getPaymentIntent = (env, { account, id }) => call(env, 'GET', `/v1/payment_intents/${encodeURIComponent(id)}`, { account, query: '?expand[]=latest_charge' });
export const refund = (env, { account, paymentIntent, amount, idem, metadata }) =>
  call(env, 'POST', '/v1/refunds', { account, idem, body: { payment_intent: paymentIntent, amount, refund_application_fee: 'false', metadata } });
export const getDispute = (env, { account, id }) => call(env, 'GET', `/v1/disputes/${encodeURIComponent(id)}`, { account });
export const getCharge = (env, { account, id }) => call(env, 'GET', `/v1/charges/${encodeURIComponent(id)}`, { account });
export const getRefund = (env, { account, id }) => call(env, 'GET', `/v1/refunds/${encodeURIComponent(id)}`, { account });
export const refundFee = (env, { fee, amount, idem, metadata }) => call(env, 'POST', `/v1/application_fees/${encodeURIComponent(fee)}/refunds`, { idem, body: { amount, metadata } });

/* Webhook signature (Stripe-Signature: t=..., v1=...). HMAC-SHA256 over `${t}.${rawBody}` with the endpoint secret;
   constant-time comparison; 5-minute tolerance. Anything else is refused before the body is parsed. */
export async function verifySignature(env, header, raw, nowSec = Math.floor(Date.now() / 1000)) {
  const secret = String(env.STRIPE_WEBHOOK_SECRET || '');
  if (!secret.startsWith('whsec_')) return { ok: false, reason: 'webhook secret not configured' };
  const parts = Object.create(null);
  for (const kv of String(header || '').split(',')) { const i = kv.indexOf('='); if (i > 0) (parts[kv.slice(0, i).trim()] ||= []).push(kv.slice(i + 1).trim()); }
  const t = Number((parts.t || [])[0]);
  if (!Number.isInteger(t) || !(parts.v1 || []).length) return { ok: false, reason: 'malformed signature' };
  if (Math.abs(nowSec - t) > 300) return { ok: false, reason: 'signature outside tolerance' };
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const mac = new Uint8Array(await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(`${t}.${raw}`)));
  const hex = [...mac].map(b => b.toString(16).padStart(2, '0')).join('');
  const eq = (a, b) => { if (a.length !== b.length) return false; let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i); return d === 0; };
  return parts.v1.some(v => eq(v, hex)) ? { ok: true, t } : { ok: false, reason: 'signature mismatch' };
}
