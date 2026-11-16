/* PlotArt · managed checkout pilot · rules (development 16 Nov 2026). NOT DEPLOYED. TEST MODE ONLY.
   The ONE definition of who owes what on a pilot order, shared by the Studio (founder desk, artist panel) and the public
   checkout Worker. No other imports beyond founding.js, so the public Worker stays small.

   Commission (MANAGED-CHECKOUT-PILOT.md "Commission rules"; PA-FAA-2026-11 cl. 5–6; PA-GAA-2026-11 cl. 5, 9):
     · A Founding Enquiry (enquiry_log.founding = 1, fixed when the enquiry was introduced) carries 0%, permanently,
       whenever the sale completes. No later agreement or setting can change that.
     · A Founding Artist owes commission ONLY under separately and expressly accepted commission-bearing terms that had
       taken effect before the enquiry was introduced (FAA 5, 6.4). Without them: 0%. 15% is never inferred.
     · A non-founding artist owes the rate in their artist_terms row, and only if they hold an accepted Gallery Artist
       Agreement dated on or before the introduction. Anything else is UNKNOWN and blocks checkout.
     · Commission is on the artwork only (Commission Base, GAA 5.6): never on separately itemised delivery, packing,
       cover or installation. No PlotArt-Funded Discounts in the pilot.
   All money is integer euro cents and is computed here, server-side. Nothing a browser sends is trusted. */
import { addDays } from './founding.js';
import { Bad } from './lib.js';

export const PILOT_ID = 'plotart-managed-checkout-pilot-1';
export const CURRENCY = 'eur';
export const MAX_ARTWORK_CENTS = 999_999;        // pilot ceiling: EUR 9,999.99 (stays below the EUR 10,000 AML art-trader threshold; see spec)
export const MAX_DELIVERY_CENTS = 200_000;
export const MAX_QUOTE_DAYS = 7;
export const SESSION_MINUTES = 30;               // Stripe's minimum hosted-checkout lifetime; the reservation follows it
export const RESERVATION_GRACE_MINUTES = 15;     // a payment completing at the last second is still reserved while its event arrives
export const ATTRIBUTION_MONTHS = 24;            // PA-GAA cl. 5.5

/* Statuses (spec "Suggested statuses"). Payment, fulfilment and dispute also have their own fields on the order. */
export const STATUSES = ['draft', 'awaiting_artist', 'quoted', 'checkout_open', 'paid', 'dispatched', 'delivered', 'closed',
  'expired', 'cancelled', 'payment_failed', 'refund_pending', 'refunded', 'disputed'];
export const MOVES = {
  draft: ['awaiting_artist', 'cancelled'],
  awaiting_artist: ['draft', 'quoted', 'cancelled'],
  quoted: ['checkout_open', 'expired', 'draft', 'cancelled'],
  checkout_open: ['quoted', 'paid', 'payment_failed', 'expired', 'draft', 'cancelled'],
  payment_failed: ['quoted', 'checkout_open', 'expired', 'draft', 'cancelled', 'paid'],
  expired: ['draft', 'cancelled', 'paid'],          // 'paid': a delayed success after expiry is recorded, never lost
  cancelled: ['paid'],                              // likewise; recorded and flagged for resolution
  paid: ['dispatched', 'refund_pending', 'refunded', 'disputed', 'closed'],
  dispatched: ['delivered', 'refund_pending', 'refunded', 'disputed'],
  delivered: ['closed', 'refund_pending', 'refunded', 'disputed'],
  refund_pending: ['refunded', 'paid', 'dispatched', 'delivered', 'disputed'],
  refunded: ['closed'],
  disputed: ['paid', 'dispatched', 'delivered', 'refunded', 'closed'],
  closed: [],
};
export const canMove = (from, to) => (MOVES[from] || []).includes(to);
export const PRE_PAYMENT = ['draft', 'awaiting_artist', 'quoted', 'checkout_open', 'payment_failed', 'expired'];

export const commissionCents = (artworkCents, bp) => Math.floor((artworkCents * bp) / 10000);   // rounds in the artist's favour

/* What the buyer pays and how it is allocated, before Stripe's processing fees (which Stripe deducts from the artist's
   own Stripe balance on a direct charge; they are not PlotArt commission and are never shown as a guaranteed net). */
export function amounts({ artwork_cents, delivery_cents, commission_bp }) {
  const a = int(artwork_cents, 'artwork price'), d = int(delivery_cents, 'delivery charge');
  if (a < 100 || a > MAX_ARTWORK_CENTS) throw new RuleError(`The artwork price must be between EUR 1.00 and EUR ${(MAX_ARTWORK_CENTS / 100).toFixed(2)} in the pilot`);
  if (d > MAX_DELIVERY_CENTS) throw new RuleError('The delivery charge is above the pilot ceiling');
  if (!Number.isInteger(commission_bp) || commission_bp < 0 || commission_bp > 1500) throw new RuleError('Commission rate out of range');
  const commission = commissionCents(a, commission_bp);
  return { currency: CURRENCY, artwork_cents: a, delivery_cents: d, total_cents: a + d, commission_bp, commission_cents: commission,
    artist_artwork_cents: a - commission, delivery_allocation_cents: d };
}

/* GAA cl. 9.2: after a partial refund the commission due is Full Commission × (artwork amount kept) / (artwork amount due).
   Returns how much application fee to refund now, given what has already been refunded. Delivery refunds never move
   commission (delivery was never part of the Commission Base). */
export function commissionRefund({ artwork_cents, commission_cents, artwork_refunded_before, artwork_refund_now, commission_refunded_before }) {
  const refunded = artwork_refunded_before + artwork_refund_now;
  if (refunded > artwork_cents) throw new RuleError('Refund exceeds the artwork amount paid');
  const kept = artwork_cents - refunded;
  const due = kept === 0 ? 0 : Math.floor((commission_cents * kept) / artwork_cents);
  return Math.max(0, commission_cents - due - commission_refunded_before);
}

export class RuleError extends Bad { constructor(m) { super(m, 409); } }
function int(v, what) { if (!Number.isInteger(v) || v < 0) throw new RuleError(`Give the ${what} in whole euro cents`); return v; }

/* GAA cl. 5.7 exclusions the founder may record (each makes the commission 0 and is kept on the order as evidence). The
   founder can only ever LOWER commission to 0 with a reason; nothing here can raise a rate. */
export const EXCLUSIONS = {
  prior_relationship: 'Collector bought from, commissioned, or was in documented contact with the artist before the introduction (GAA 5.7(a))',
  representing_gallery: 'Sale through a representing gallery or agent: handled outside the pilot (GAA 12.2)',
  independent_sale: 'Collector origin genuinely uncertain: treated as an independent sale',
  founder_waiver: 'Founder waived commission on this order in writing',
};

const monthsAfter = (ymd, n) => { const [y, m, d] = ymd.split('-').map(Number); const t = new Date(Date.UTC(y, m - 1 + n, d)); return t.toISOString().slice(0, 10); };

/* The commission entitlement for an order, from the records alone. Returns
     { ok: true, bp, basis, evidence }   or   { ok: false, reason }   (blocks checkout).
   `at` is the time the quote is issued; `exclusion` / `negotiation_note` are the founder's recorded decisions. */
export async function entitlement(env, { artist, enquiryRef, at, exclusion = null, negotiationNote = null }) {
  const rows = (await env.DB.prepare('SELECT * FROM enquiry_log WHERE artist_id = ? AND (reference = ? OR corrects IN (SELECT id FROM enquiry_log WHERE reference = ?)) ORDER BY logged_at DESC, rowid DESC')
    .bind(artist.id, enquiryRef, enquiryRef).all()).results;
  const log = rows[0];   // a correcting row, if any, is the latest statement about this introduction
  if (!log) return { ok: false, reason: `No PlotArt introduction is logged for ${enquiryRef} and this artist. Log the enquiry first (Review desk → Log enquiry).` };
  const intro = { reference: enquiryRef, log_id: log.id, introduced_at: log.introduced_at, founding: log.founding, founding_year_end: log.founding_year_end, route: log.route };
  if (log.founding === 1) return { ok: true, bp: 0, basis: 'founding_enquiry', evidence: { intro, rule: 'PA-FAA-2026-11 cl. 5: Founding Enquiry, commission-free permanently' } };
  if (exclusion) {
    if (!EXCLUSIONS[exclusion]) return { ok: false, reason: 'Unknown exclusion' };
    return { ok: true, bp: 0, basis: 'exclusion:' + exclusion, evidence: { intro, rule: EXCLUSIONS[exclusion] } };
  }
  let terms = null, acc = null;
  try {
    terms = await env.DB.prepare("SELECT * FROM artist_terms WHERE artist_id = ? AND track = 'gallery_artist'").bind(artist.id).first();
    acc = await env.DB.prepare("SELECT doc_id, accepted_at, id FROM gallery_agreement_acceptances WHERE artist_id = ? AND doc_id LIKE 'PA-GAA-%' ORDER BY accepted_at ASC LIMIT 1").bind(artist.id).first();
  } catch { /* migration 0012 not applied: no commission-bearing terms can exist */ }
  const accBeforeIntro = acc && Date.parse(acc.accepted_at) <= Date.parse(log.introduced_at);
  if (artist.founding) {
    // FAA 5 last paragraph: unless PlotArt can show the enquiry was introduced after accepted commission-bearing terms
    // took effect, it is treated as a Founding Enquiry. FAA 6.5: without acceptance the gallery continues without charges.
    if (!terms || !accBeforeIntro)
      return { ok: true, bp: 0, basis: terms ? 'founding_artist_introduced_before_commission_terms' : 'founding_artist_no_commission_terms',
        evidence: { intro, rule: 'PA-FAA-2026-11 cl. 5–6: no commission without expressly accepted commission terms in effect at introduction' } };
  } else if (!terms || !acc) {
    return { ok: false, reason: 'Commission entitlement unknown: this artist holds no accepted commission terms on record. Resolve before checkout.' };
  } else if (!accBeforeIntro) {
    return { ok: false, reason: 'The introduction is dated before the artist accepted the Gallery Artist Agreement. Resolve before checkout.' };
  }
  // A commission-bearing agreement applies: check the attribution period (GAA 5.5)
  const introDay = log.introduced_at.slice(0, 10), endDay = monthsAfter(introDay, ATTRIBUTION_MONTHS);
  if (at.slice(0, 10) > endDay && !negotiationNote)
    return { ok: false, reason: `This sale falls after the ${ATTRIBUTION_MONTHS}-month attribution period (ended ${endDay}). Record documented negotiations or an exclusion.` };
  return { ok: true, bp: terms.commission_bp, basis: 'gallery_artist_agreement', evidence: { intro, doc_id: acc.doc_id, accepted_at: acc.accepted_at,
    rate_bp: terms.commission_bp, variation_agreed_on: terms.variation_agreed_on || null, negotiation_note: negotiationNote || null,
    attribution_end: endDay, rule: `${acc.doc_id} cl. 5: ${(terms.commission_bp / 100).toFixed(2)}% of the Commission Base, including any VAT; delivery excluded` } };
}

/* Delivery and cover (spec "Delivery and cover"). Every field must be filled before the artist is asked to approve: the
   quote names who does and pays for each part, and what the cover actually is. No blanket insurance promise is possible:
   "none" is an allowed, explicit cover answer, and is shown to the buyer as such. */
export const PARTIES = ['artist', 'buyer', 'transporter', 'plotart', 'not_applicable'];
export const DELIVERY_FIELDS = {
  collection_county: 's', destination: 's', unpacked_cm: 's', packed_cm: 's', weight_kg: 'n', medium: 's', framing: 's', glazing: 's',
  condition: 's', access_notes: 's?',
  organiser: 'p', packer: 'p', transport_booker: 'p', transport_contracting_party: 'p', transport_payer: 'p', transporter_name: 's',
  installation: 'p', import_costs: 'p',
  cover_type: ['transit_insurance', 'carrier_limited_liability', 'none'], cover_provider: 's?', covered_value_cents: 'n', valuation_basis: 's?',
  excess_cents: 'n?', exclusions: 's?', cover_period: 's?', claims_contact: 's?',
  delivery_window: 's', tracking: 's', signed_receipt: 'b', condition_photos: 'b', return_route: 's',
  shipment_confirmation_ref: 's', shipment_confirmed_by: 's', shipment_confirmed_on: 'd',
};
export function cleanDelivery(o) {
  if (!o || typeof o !== 'object') throw new RuleError('Delivery details are required');
  const out = {};
  for (const [k, t] of Object.entries(DELIVERY_FIELDS)) {
    let v = o[k];
    const opt = typeof t === 'string' && t.endsWith('?');
    const ty = typeof t === 'string' ? t.replace('?', '') : t;
    if (v === undefined || v === null || v === '') { if (opt) { out[k] = null; continue; } throw new RuleError(`Delivery: ${k.replace(/_/g, ' ')} is required`); }
    if (Array.isArray(ty)) { if (!ty.includes(v)) throw new RuleError(`Delivery: choose a valid ${k.replace(/_/g, ' ')}`); }
    else if (ty === 's') { v = String(v).trim(); if (!v || v.length > 400) throw new RuleError(`Delivery: ${k.replace(/_/g, ' ')} must be 1–400 characters`); }
    else if (ty === 'n') { if (typeof v !== 'number' || !isFinite(v) || v < 0) throw new RuleError(`Delivery: ${k.replace(/_/g, ' ')} must be a number`); }
    else if (ty === 'b') { if (v !== true && v !== false) throw new RuleError(`Delivery: ${k.replace(/_/g, ' ')} must be yes or no`); }
    else if (ty === 'p') { if (!PARTIES.includes(v)) throw new RuleError(`Delivery: ${k.replace(/_/g, ' ')} must name a party`); }
    else if (ty === 'd') { if (!/^\d{4}-\d{2}-\d{2}$/.test(v)) throw new RuleError(`Delivery: ${k.replace(/_/g, ' ')} must be YYYY-MM-DD`); }
    out[k] = v;
  }
  if (out.cover_type !== 'none' && (!out.cover_provider || !out.claims_contact || !out.cover_period || !out.valuation_basis))
    throw new RuleError('Delivery: cover needs its provider, valuation basis, period and claims contact');
  if (out.cover_type === 'none' && out.covered_value_cents !== 0) throw new RuleError('Delivery: with no cover, the covered value must be 0');
  const extra = Object.keys(o).filter(k => !(k in DELIVERY_FIELDS));
  if (extra.length) throw new RuleError('Delivery: unknown field ' + extra[0]);
  return out;
}
export const quoteExpiry = (fromIso, days) => {
  if (!Number.isInteger(days) || days < 1 || days > MAX_QUOTE_DAYS) throw new RuleError(`A quote lasts 1–${MAX_QUOTE_DAYS} days`);
  return new Date(Date.parse(fromIso) + days * 86400_000).toISOString();
};
export { addDays };
