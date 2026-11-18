/* PlotArt · managed checkout pilot · public Worker ("plotart-checkout"). NOT DEPLOYED. TEST MODE ONLY. OFF BY DEFAULT.
   A separate public Worker bound to the Studio's D1 database (wrangler.checkout.toml). It serves only:
     GET  /q/<token>                the buyer's quote: seller, artwork, every charge, delivery and cover, purchase terms
     POST /q/<token>/pay            opens Stripe-hosted checkout on the ARTIST's account (server-side amounts only)
     GET  /q/<token>/return         what PlotArt has verified so far (a return from Stripe is never proof of payment)
     GET  /q/<token>/confirmation   the buyer's stored purchase confirmation (exact text kept by PlotArt), once the sale is complete
     GET  /terms/<doc>.html         the installed, fingerprinted buyer purchase terms
     GET  /v1/status                whether the pilot is installed and switched on (nothing else)
     POST /v1/stripe/webhook        signed Stripe events (Connect endpoint), idempotent
   The token in the link is the only key to a quote; it is stored hashed. No other order, artist address or note is ever
   reachable from here. Nothing on plotnua.ie links to this Worker. */
import * as C from './checkout.js';
import { PAYMENT_TERMS } from './payment-terms.js';

const SEC = { 'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; img-src 'self'; form-action 'self' https://checkout.stripe.com; frame-ancestors 'none'; base-uri 'none'",
  'X-Frame-Options': 'DENY', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex, nofollow' };
const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
const eur = c => c == null ? '—' : '€' + (c / 100).toLocaleString('en-IE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const PARTY = { artist: 'the artist (seller)', buyer: 'you (the buyer)', transporter: 'the transporter', plotart: 'PlotArt', not_applicable: 'not applicable' };
const page = (title, body, status = 200) => new Response(`<!DOCTYPE html><html lang="en-IE"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow"><title>${esc(title)} · PlotArt</title>
<style>body{margin:0;background:#141414;color:#ece9e4;font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}main{max-width:720px;margin:0 auto;padding:40px 22px 80px}h1{font-weight:500;font-size:28px;margin:.2em 0 .6em}h2{font-weight:500;font-size:18px;margin:2em 0 .5em;color:#fff}
.k{color:#9c9893;font-size:13px;letter-spacing:.06em;text-transform:uppercase}table{width:100%;border-collapse:collapse}td{padding:7px 0;border-bottom:1px solid #2a2a2a;vertical-align:top}td:last-child{text-align:right}
.tot td{font-weight:600;border-bottom:0;padding-top:12px}.note{background:#1d1d1d;border:1px solid #2c2c2c;padding:14px 16px;border-radius:6px;font-size:14px;color:#cfcac3}.test{background:#3a2f12;border-color:#6b5317;color:#f2dc9b}
button{background:#ece9e4;color:#141414;border:0;border-radius:4px;padding:13px 22px;font-size:16px;cursor:pointer}label{display:block;margin:18px 0}a{color:#ece9e4}dl{display:grid;grid-template-columns:minmax(150px,38%) 1fr;gap:6px 14px;font-size:14px}dt{color:#9c9893}dd{margin:0}</style></head>
<body><main><p class="k">PlotArt</p>${body}</main></body></html>`, { status, headers: { 'Content-Type': 'text/html; charset=utf-8', ...SEC } });
const TEST_BANNER = '<p class="note test"><strong>Test mode.</strong> This is a PlotArt payment pilot running in Stripe test mode. No real payment can be taken and no artwork is sold through this page.</p>';

function quoteHtml(q, token, error = null) {
  const d = q.delivery, a = q.artwork || {}, s = q.seller || {};
  const cover = `Transit insurance with ${esc(d.cover_provider)}, held by ${esc(PARTY[d.insured_party])}, up to ${eur(d.covered_value_cents)} (${esc(d.valuation_basis)})${d.excess_cents ? `, excess ${eur(d.excess_cents)}` : ''}. Period: ${esc(d.cover_period)}.${d.exclusions ? ` Exclusions: ${esc(d.exclusions)}.` : ''} Claims: ${esc(d.claims_contact)}. Confirmed for this shipment (ref. ${esc(d.cover_confirmation_ref)}).`;
  const payable = ['quoted', 'checkout_open', 'payment_failed'].includes(q.status) && !q.expired && !q.payments_paused;
  return `${TEST_BANNER}<h1>${esc(a.title || 'Original artwork')}</h1>
<p>Sold by <strong>${esc(s.name)}</strong>, the artist. ${esc(s.platform)}</p>
<p class="k">Quote ${esc(q.reference)} · valid until ${esc(new Date(q.quote_expires_at).toLocaleString('en-IE', { timeZone: 'Europe/Dublin', dateStyle: 'medium', timeStyle: 'short' }))} (Irish time)</p>
<h2>The seller</h2><dl>
<dt>Legal name</dt><dd>${esc(s.legal_name)}${s.trading_name ? ` trading as ${esc(s.trading_name)}` : ''}</dd><dt>Address</dt><dd>${esc(s.address)}</dd>
${s.returns_address && s.returns_address !== s.address ? `<dt>Returns and complaints</dt><dd>${esc(s.returns_address)}</dd>` : ''}<dt>Email</dt><dd>${esc(s.email)}</dd><dt>Telephone</dt><dd>${esc(s.phone)}</dd>
${s.vat_number ? `<dt>VAT number</dt><dd>${esc(s.vat_number)}</dd>` : ''}<dt>Seller’s declaration</dt><dd>${s.trader_status === 'trader' ? esc(C.BUYER_TRADER_SENTENCE) : 'The seller has not declared that they sell as a trader. This quote cannot be paid.'}</dd></dl>
<h2>What you pay</h2><table><tr><td>Original artwork${a.medium ? ` · ${esc(a.medium)}` : ''}${a.h_cm ? ` · ${esc(a.h_cm)} × ${esc(a.w_cm)}${a.d_cm ? ' × ' + esc(a.d_cm) : ''} cm` : ''}</td><td>${eur(q.artwork_cents)}</td></tr>
<tr><td>Packing, transport and cover as set out below</td><td>${eur(q.delivery_cents)}</td></tr><tr class="tot"><td>Total (EUR)</td><td>${eur(q.total_cents)}</td></tr></table>
<p class="note">You pay the artist through Stripe. PlotArt does not hold your payment; it is not escrow. The delivery charge pays for the delivery described below and is kept separate from the artwork price.</p>
<h2>Delivery and cover</h2><dl>
<dt>Collected from</dt><dd>${esc(d.collection_county)}</dd><dt>Delivered to</dt><dd>${esc(d.destination)}</dd><dt>Packed size</dt><dd>${esc(d.packed_cm)} cm</dd>
<dt>Framing / glazing</dt><dd>${esc(d.framing)} / ${esc(d.glazing)}</dd><dt>Condition</dt><dd>${esc(d.condition)}</dd>
<dt>Packed by</dt><dd>${esc(PARTY[d.packer])}</dd><dt>Transport contracted by</dt><dd>${esc(PARTY[d.transport_contracting_party])}${d.transporter_name ? ` (${esc(d.transporter_name)})` : ''}</dd>
<dt>Arranged by</dt><dd>${esc(PARTY[d.organiser])}</dd><dt>Installation</dt><dd>${esc(PARTY[d.installation])}</dd><dt>Import costs</dt><dd>${esc(PARTY[d.import_costs])}</dd>
<dt>Cover</dt><dd>${cover}</dd><dt>Delivery window</dt><dd>${esc(d.delivery_window)}</dd><dt>Tracking</dt><dd>${esc(d.tracking)}</dd>
<dt>On delivery</dt><dd>${d.signed_receipt ? 'Signed receipt' : 'No signed receipt'}${d.condition_photos ? '; condition photographs before dispatch and on arrival' : ''}</dd></dl>
<h2>Returns</h2><dl><dt>Method</dt><dd>${esc(d.return_method)}</dd><dt>Return address</dt><dd>${esc(d.return_address)}</dd><dt>Arranged by</dt><dd>${esc(PARTY[d.return_arranged_by])}</dd>
<dt>Cost if you cancel for a change of mind</dt><dd>${d.return_cost_basis === 'fixed' ? eur(d.return_cost_cents) : `Up to about ${eur(d.return_cost_cents)} (estimated maximum)`}. You bear this cost if you cancel for a change of mind. If the artwork is damaged, faulty or not as described, the seller bears it.</dd></dl>
<p class="note">Your rights as a buyer do not depend on any carrier or insurance claim being made or completed.</p>
${payable ? `<form method="post" action="/q/${esc(token)}/pay">${error ? `<p class="note">${esc(error)}</p>` : ''}
<label><input type="checkbox" name="accept_terms" value="${esc(q.terms && q.terms.doc_id)}" required> I have read the <a href="/terms/${esc(q.terms && q.terms.doc_id)}.html" target="_blank" rel="noopener">purchase terms (${esc(q.terms && q.terms.doc_id)})</a>, and I understand that I am buying from ${esc(s.name)}.</label>
<button type="submit">Continue to secure payment</button></form>` : `<p class="note">${q.payment_status === 'paid' ? 'Payment has been confirmed for this order.' : q.expired || q.status === 'expired' ? 'This quote has expired. Please contact hello@plotnua.ie.' : q.payments_paused && ['quoted', 'checkout_open', 'payment_failed'].includes(q.status) ? esc(C.BUYER_PAUSED) : 'This quote cannot be paid at the moment. Please contact hello@plotnua.ie.'}</p>`}
${(q.notices || []).length ? `<h2>Updates about your order</h2>${q.notices.map(n => `<div class="note"><strong>${esc(n.subject)}</strong> <span class="k">${esc(new Date(n.created_at).toLocaleString('en-IE', { timeZone: 'Europe/Dublin', dateStyle: 'medium', timeStyle: 'short' }))}</span><p style="white-space:pre-wrap">${esc(n.body)}</p></div>`).join('')}` : ''}
<p style="font-size:14px;color:#9c9893">Questions: <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a> · quote ${esc(q.reference)}</p>`;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url), p = url.pathname, m = req.method;
    try {
      if (p === '/v1/stripe/webhook') {
        if (m !== 'POST') return new Response(null, { status: 405 });
        if (!(await C.installed(env))) return new Response('{"ok":false}', { status: 503 });
        const raw = await req.text();
        if (raw.length > 512_000) return new Response('{"ok":false}', { status: 413 });
        const out = await C.webhook(env, raw, req.headers.get('Stripe-Signature'));
        return new Response(JSON.stringify(out.body), { status: out.status, headers: { 'Content-Type': 'application/json' } });
      }
      // switch state only (no counts, no identifiers): lets the deploy workflow verify from outside that the pilot is on or off
      if (p === '/v1/status' && m === 'GET') return new Response(JSON.stringify({ installed: await C.installed(env), pilot_enabled: C.switches(env).enabled, mode: 'test' }),
        { headers: { 'Content-Type': 'application/json', ...SEC } });
      let mm;
      if ((mm = p.match(/^\/terms\/(PA-BPT-[0-9A-Z-]{4,20})\.html$/)) && m === 'GET') {
        const t = await C.currentTerms(env, 'buyer_purchase_terms');
        if (!t || t.doc_id !== mm[1] || !PAYMENT_TERMS[mm[1]]) return page('Not found', '<h1>Not found</h1>', 404);
        return new Response(t.html, { headers: { 'Content-Type': 'text/html; charset=utf-8', ...SEC, 'X-Document-SHA256': t.html_sha256 } });
      }
      if ((mm = p.match(/^\/q\/([0-9a-z]{48})\/confirmation$/)) && m === 'GET') {
        if (!(await C.installed(env))) return page('Not available', '<h1>This page is not available.</h1>', 404);
        const c = await C.buyerConfirmation(env, mm[1]);
        if (!c) return page('Not found', '<h1>No confirmation is available for this quote.</h1>', 404);
        return new Response(c.body, { headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Content-Disposition': `inline; filename="plotart-confirmation.txt"`, 'X-Document-SHA256': c.sha256, ...SEC } });
      }
      if ((mm = p.match(/^\/q\/([0-9a-z]{48})(\/pay|\/return)?$/))) {
        if (!(await C.installed(env))) return page('Not available', '<h1>This page is not available.</h1>', 404);
        const token = mm[1];
        if (!mm[2] && m === 'GET') {
          if (!C.switches(env).enabled) return page('Not available', '<h1>Payments are not open.</h1><p>Please contact hello@plotnua.ie.</p>', 503);
          const q = await C.buyerQuote(env, token);
          return q ? page('Your quote', quoteHtml(q, token)) : page('Not found', '<h1>This quote is not available.</h1>', 404);
        }
        if (mm[2] === '/pay' && m === 'POST') {
          if (req.headers.get('Origin') !== env.CHECKOUT_ORIGIN) return page('Refused', '<h1>Refused</h1>', 403);
          const f = await req.formData();
          try {
            const r = await C.startCheckout(env, token, { accept_terms: String(f.get('accept_terms') || '') });
            return new Response(null, { status: 303, headers: { Location: r.url, ...SEC } });
          } catch (e) {
            const q = await C.buyerQuote(env, token);
            if (!q) return page('Not found', '<h1>This quote is not available.</h1>', 404);
            return page('Your quote', quoteHtml(q, token, e.message), e.status || 400);
          }
        }
        if (mm[2] === '/return' && m === 'GET') {
          const q = await C.buyerQuote(env, token);
          if (!q) return page('Not found', '<h1>This quote is not available.</h1>', 404);
          const paid = q.payment_status === 'paid';
          const msg = paid ? `<h1>Thank you</h1><p>Your payment for quote ${esc(q.reference)} has been confirmed. ${esc(q.seller && q.seller.name)} and PlotArt will be in touch about delivery.</p>${q.confirmation_ready ? `<p><a href="/q/${esc(token)}/confirmation">Your purchase confirmation</a>, with the purchase terms and the cancellation form. Please save or print it.</p>` : '<p>Your purchase confirmation is being prepared. Refresh this page shortly.</p>'}`
            : url.searchParams.get('result') === 'success' ? `<h1>We’re confirming your payment</h1><p>Stripe has returned you to PlotArt. Your payment is confirmed only once Stripe notifies us directly, usually within a minute. Refresh this page shortly; you will also receive Stripe’s receipt by email.</p>`
            : `<h1>Payment not completed</h1><p>No payment was taken. <a href="/q/${esc(token)}">Return to your quote</a>.</p>`;
          const upd = (q.notices || []).length ? `<h2>Updates about your order</h2>${q.notices.map(n => `<div class="note"><strong>${esc(n.subject)}</strong><p style="white-space:pre-wrap">${esc(n.body)}</p></div>`).join('')}` : '';
          return page('Payment', TEST_BANNER + msg + upd);
        }
      }
      return page('Not found', '<h1>Not found</h1>', 404);
    } catch (e) {
      if (e instanceof C.Bad) return page('Problem', `<h1>${esc(e.message)}</h1>`, e.status);
      console.error(e);
      return page('Problem', '<h1>Something went wrong.</h1><p>Please contact hello@plotnua.ie.</p>', 500);
    }
  },
  async scheduled(_e, env) { await C.sweep(env); },
};
