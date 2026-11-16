/* PlotArt · managed checkout pilot · Stripe Connect adapter (development 16 Nov 2026). NOT DEPLOYED. TEST MODE ONLY.

   Configuration chosen (see MANAGED-CHECKOUT-PILOT.md "Implementation"):
     · Each opted-in artist has their OWN Stripe account, created with controller properties equivalent to a Standard
       account: Stripe collects requirements (hosted onboarding), the artist has the full Stripe Dashboard, the ARTIST pays
       Stripe's processing fees (fees.payer = account) and Stripe — not PlotArt — carries negative-balance losses
       (losses.payments = stripe).
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

async function call(env, method, path, { body = null, account = null, idem = null, query = '' } = {}) {
  const k = testKey(env);
  if (!k.ok) throw new StripeError(k.reason, 503, 'not_configured');
  const base = env.STRIPE_API_BASE || 'https://api.stripe.com';
  if (env.STRIPE_API_BASE && env.ENVIRONMENT !== 'local') throw new StripeError('STRIPE_API_BASE is for local tests only', 500);
  const headers = { Authorization: `Bearer ${env.STRIPE_SECRET_KEY}` };
  if (env.STRIPE_API_VERSION) headers['Stripe-Version'] = env.STRIPE_API_VERSION;   // otherwise the platform account's pinned version
  if (account) headers['Stripe-Account'] = account;
  if (idem) headers['Idempotency-Key'] = idem;
  if (body) headers['Content-Type'] = 'application/x-www-form-urlencoded';
  const r = await fetch(`${base}${path}${query}`, { method, headers, body: body ? form(body) : undefined });
  const t = await r.text();
  let j; try { j = JSON.parse(t); } catch { throw new StripeError('Payment provider returned an unreadable response'); }
  if (!r.ok) throw new StripeError((j.error && j.error.message) || 'Payment provider error', r.status >= 500 ? 502 : 409, j.error && j.error.code);
  if (j.livemode === true) throw new StripeError('A live-mode object was returned to the test-mode pilot', 500, 'livemode');
  return j;
}

export const createAccount = (env, { email, country, artistId }) => call(env, 'POST', '/v1/accounts', { idem: `plotart-acct-${artistId}`, body: {
  country, email,
  controller: { fees: { payer: 'account' }, losses: { payments: 'stripe' }, requirement_collection: 'stripe', stripe_dashboard: { type: 'full' } },
  capabilities: { card_payments: { requested: true }, transfers: { requested: true } },
  metadata: { plotart_artist: artistId, plotart_pilot: 'managed-checkout-1' } } });
export const accountLink = (env, { account, refreshUrl, returnUrl }) => call(env, 'POST', '/v1/account_links', { body: { account, refresh_url: refreshUrl, return_url: returnUrl, type: 'account_onboarding' } });
export const getAccount = (env, account) => call(env, 'GET', `/v1/accounts/${encodeURIComponent(account)}`);

export const createSession = (env, { account, idem, order, title, artworkCents, deliveryCents, feeCents, expiresAt, buyerEmail, successUrl, cancelUrl, statement }) =>
  call(env, 'POST', '/v1/checkout/sessions', { account, idem, body: {
    mode: 'payment', currency: 'eur', payment_method_types: ['card'], customer_email: buyerEmail || undefined,
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
