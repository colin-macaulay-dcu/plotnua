/* PlotArt · multi-artist basket · allocation rules (Phase 1, revised after review 21 Nov 2026). NOT WIRED IN. NO STRIPE CALLS.
   NO DATABASE WRITES (lineEntitlements and basketLinkedCheck only READ).

   One buyer payment for artworks from several artists, taken on PlotArt's platform account and paid on to each artist by
   a Stripe transfer ("separate charges and transfers"). This module is the ONE definition of how that payment is split.
   The single-artist direct-charge pilot (checkout.js, checkout-rules.js) is unchanged and does not use this module.

   Reused from checkout-rules.js, not re-implemented:
     · amounts()            per-artwork commission (floor, in the artist's favour), price limits, integer cents
     · commissionRefund()   PA-GAA cl. 9.2: commission kept after a partial refund is proportional to the artwork kept
     · entitlement()        Founding Enquiry 0% permanently; Founding Artist 0% without accepted commission terms;
                            Gallery Artist at their artist_terms rate; anything unknown blocks (PA-FAA 5–6, PA-GAA 5)
     · checkCover()         confirmed transit insurance covering at least the artworks shipped
     · LINKED_THRESHOLD_CENTS, LINKED_WINDOW_DAYS, MAX_DELIVERY_CENTS, RuleError

   Gates (review of PR #43, findings H3 and M3):
     · TERMS. The issued single-artist texts (PA-PAY-2026-11, PA-BPT-2026-11) exclude multi-artwork orders (PA-PAY 1.3),
       so a basket needs its own approved terms. LIVE_BASKET_TERMS is EMPTY: no live basket is possible until the founder
       approves new terms AND they are added here in a reviewed change. In test mode only labelled placeholders are
       accepted. Terms also say which founder decisions they permit and whether commission-free lines (Founding 25) are
       allowed; nothing here invents or approves commercial terms.
     · ENTITLEMENTS are produced only by lineEntitlements(), which reads the artist, the artwork, the logged introduction and
       the recorded processing consent from the database, binds the result to that artist, artwork and introduction, and
       seals it. plan() accepts only sealed entitlements whose binding matches the line, and refuses caller-supplied consent.

   Founder decisions that are NOT settled are explicit inputs (DECISIONS). There are no defaults.
   Money is integer euro cents throughout; apportion() splits amounts exactly; every result checks its own conservation
   invariant and throws instead of returning an unbalanced result. */
import * as R from './checkout-rules.js';

export const BASKET_PILOT_ID = 'plotart-basket-1';
export const PLAN_VERSION = 'basket-plan-2';
/* A technical bound on one basket (size of the Checkout Session and of the records), not a commercial policy. */
export const MAX_BASKET_LINES = 20;
const ID = /^[A-Za-z0-9_-]{1,64}$/;

/* ---------------------------------------------------------------- founder decisions (inputs, never defaults) */
export const DECISIONS = Object.freeze({
  processing_fee_bearer: Object.freeze({
    plotart: 'PlotArt bears Stripe\'s processing fee (and VAT on it); artists receive their allocation without a processing deduction',
    artists_pro_rata: 'Each artist bears a share of the actual fee in proportion to their gross allocation (commission-free lines need the artist\'s recorded processing consent)',
  }),
  transfer_timing: Object.freeze({
    on_payment: 'Transfer once Stripe confirms the payment',
    after_delivery: 'Transfer once the artist\'s shipment is recorded as delivered (or collected)',
    after_cancellation_window: 'Transfer once the buyer\'s cancellation period for that shipment has ended',
  }),
  dispute_loss_bearer: Object.freeze({
    plotart: 'PlotArt carries the lost amount; no artist transfer is reversed',
    artists_by_line: 'The lost amount, explicitly attributed to lines, is recovered from those artists like a refund (PlotArt returns the commission on it, PA-GAA 9.1)',
  }),
  dispute_fee_bearer: Object.freeze({
    plotart: 'PlotArt carries the dispute fee',
    artists_by_line: 'The dispute fee is shared by the artists the lost amount is explicitly attributed to, in proportion to it',
  }),
  basket_introduction: Object.freeze({
    logged_enquiry_only: 'Every line names a PlotArt introduction already logged for that artist and that artwork; otherwise the line is blocked',
  }),
});
const ALL_PERMITTED = Object.freeze(Object.fromEntries(Object.entries(DECISIONS).map(([k, v]) => [k, Object.freeze(Object.keys(v))])));

export function decisions(input) {
  if (!input || typeof input !== 'object') throw new R.RuleError('Founder decisions are required for a basket (see DECISIONS)');
  const out = {};
  for (const [k, options] of Object.entries(DECISIONS)) {
    const v = input[k];
    if (v === undefined || v === null || v === '') throw new R.RuleError(`Founder decision required: ${k} (one of ${Object.keys(options).join(', ')})`);
    if (!Object.hasOwn(options, v)) throw new R.RuleError(`Founder decision ${k} must be one of ${Object.keys(options).join(', ')}`);
    out[k] = v;
  }
  const extra = Object.keys(input).filter(k => !Object.hasOwn(DECISIONS, k));
  if (extra.length) throw new R.RuleError('Unknown founder decision: ' + extra[0]);
  return Object.freeze(out);
}

/* ---------------------------------------------------------------- basket terms (approval gate) */
/* LIVE basket terms: NONE. A live basket is impossible until the founder approves new artist and buyer terms for baskets
   and they are added here, with what they permit, in a reviewed change. Do not add an entry without that approval. */
export const LIVE_BASKET_TERMS = Object.freeze({});
/* TEST placeholders (synthetic, labelled TEST, never valid in live mode), mirroring PA-PAY-TEST-01 / PA-BPT-TEST-01. -02 lets
   tests exercise commission-free lines; it is not a statement that any real terms will permit them. */
export const TEST_BASKET_TERMS = Object.freeze({
  'PA-BASKET-TEST-01': Object.freeze({ buyer_terms_doc: 'PA-BASKET-BPT-TEST-01', commission_free_lines: false, permits: ALL_PERMITTED }),
  'PA-BASKET-TEST-02': Object.freeze({ buyer_terms_doc: 'PA-BASKET-BPT-TEST-02', commission_free_lines: true, permits: ALL_PERMITTED }),
  // terms that permit only some decision values, to prove plan() enforces what terms permit
  'PA-BASKET-TEST-03': Object.freeze({ buyer_terms_doc: 'PA-BASKET-BPT-TEST-03', commission_free_lines: false, permits: Object.freeze({
    processing_fee_bearer: Object.freeze(['plotart']), transfer_timing: Object.freeze(['on_payment']), dispute_loss_bearer: Object.freeze(['plotart']),
    dispute_fee_bearer: Object.freeze(['plotart']), basket_introduction: Object.freeze(['logged_enquiry_only']) }) }),
});
const SINGLE_ARTIST_TEXTS = ['PA-PAY-2026-11', 'PA-BPT-2026-11'];

export function basketTerms(input, registries = { live: LIVE_BASKET_TERMS, test: TEST_BASKET_TERMS }) {
  if (!input || typeof input !== 'object') throw new R.RuleError('Basket terms are required (artist and buyer terms approved for baskets)');
  const { livemode, artist_terms_doc: a, buyer_terms_doc: b } = input;
  if (livemode !== true && livemode !== false) throw new R.RuleError('Basket terms must state the Stripe mode (livemode true or false)');
  if (SINGLE_ARTIST_TEXTS.includes(a) || SINGLE_ARTIST_TEXTS.includes(b))
    throw new R.RuleError('The issued single-artist terms (PA-PAY-2026-11 / PA-BPT-2026-11) exclude multi-artwork orders; a basket needs its own approved terms');
  const reg = livemode ? registries.live : registries.test;
  const t = reg && Object.hasOwn(reg, a) ? reg[a] : null;
  if (!t) throw new R.RuleError(livemode ? 'No approved live basket terms: live baskets need new artist and buyer terms approved by the founder'
    : 'Unknown TEST basket terms (use a labelled TEST placeholder)');
  if (!livemode && !/-TEST-/.test(a)) throw new R.RuleError('Test mode accepts only labelled TEST placeholder terms');
  if (livemode && (/-TEST-/.test(a) || /-TEST-/.test(b))) throw new R.RuleError('TEST placeholder terms are never valid in live mode');
  if (t.buyer_terms_doc !== b) throw new R.RuleError('The buyer terms do not belong with these artist terms');
  return Object.freeze({ livemode, artist_terms_doc: a, buyer_terms_doc: b, commission_free_lines: t.commission_free_lines === true, permits: t.permits });
}

/* ---------------------------------------------------------------- idempotency keys (the database CHECKs the same format) */
export const keys = Object.freeze({
  transfer: ({ basket_id, artist_id, kind = 'allocation', cause_key = '-', attempt }) => `plotart-basket-tr:${basket_id}:${artist_id}:${kind}:${cause_key}:${attempt}`,
  reversal: ({ transfer_id, cause_kind, cause_id, attempt }) => `plotart-basket-trr:${transfer_id}:${cause_kind}:${cause_id}:${attempt}`,
  refund: ({ basket_id, refund_id }) => `plotart-basket-re:${basket_id}:${refund_id}`,
});

/* ---------------------------------------------------------------- helpers */
const isCents = v => Number.isSafeInteger(v) && v >= 0;
function cents(v, what) { if (!isCents(v)) throw new R.RuleError(`Give the ${what} in whole euro cents`); return v; }
function id(v, what) { if (typeof v !== 'string' || !ID.test(v)) throw new R.RuleError(`${what} must be 1–64 letters, digits, - or _`); return v; }
function posInt(v, what) { if (!Number.isSafeInteger(v) || v < 1) throw new R.RuleError(`${what} must be a whole number of at least 1`); return v; }
const sum = (xs, f = x => x) => xs.reduce((a, x) => a + f(x), 0);
const byId = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
function freeze(o) { if (o && typeof o === 'object' && !Object.isFrozen(o)) { Object.freeze(o); for (const v of Object.values(o)) freeze(v); } return o; }
function invariant(ok, what) { if (!ok) throw new R.RuleError(`Allocation failed: ${what}`); }

/* Split `total` cents across `weights` (non-negative integers) so the parts are integers that sum exactly to `total`.
   Largest remainder; ties go to the earlier position, so the caller's (sorted) order makes the result deterministic. */
export function apportion(total, weights) {
  cents(total, 'amount to split');
  if (!Array.isArray(weights) || !weights.length || !weights.every(isCents)) throw new R.RuleError('Weights must be whole, non-negative numbers');
  const W = sum(weights);
  if (W === 0) { if (total === 0) return weights.map(() => 0); throw new R.RuleError('Cannot split an amount across zero weights'); }
  const base = weights.map(w => Math.floor((total * w) / W));
  if (!base.every(Number.isSafeInteger)) throw new R.RuleError('Amount too large to split safely');
  let left = total - sum(base);
  const order = weights.map((w, i) => ({ i, r: (total * w) % W })).sort((a, b) => b.r - a.r || a.i - b.i);
  for (const { i } of order) { if (!left) break; base[i]++; left--; }
  return base;
}

/* ---------------------------------------------------------------- entitlements: read, bind, seal */
const SEALED = new WeakSet();
const isSealed = e => !!e && typeof e === 'object' && SEALED.has(e);

/* The records lineEntitlements reads. Production passes nothing and these read the database; offline tests may supply
   their own (refused when ENVIRONMENT is "production"). */
function dbRecords(env) {
  const one = (sql, ...a) => env.DB.prepare(sql).bind(...a).first();
  return {
    artist: aid => one('SELECT * FROM artists WHERE id = ?', aid),
    artwork: wid => one('SELECT id, artist_id FROM artworks WHERE id = ?', wid),
    // the latest statement about this introduction: a correcting row, if any (as checkout-rules.entitlement reads it)
    enquiry: ref => one('SELECT * FROM enquiry_log WHERE reference = ? OR corrects IN (SELECT id FROM enquiry_log WHERE reference = ?) ORDER BY logged_at DESC, rowid DESC LIMIT 1', ref, ref),
    consent: async aid => {
      const r = await one("SELECT kind, at FROM payment_pilot_events WHERE artist_id = ? AND kind IN ('processing_consent', 'processing_consent_withdrawn') ORDER BY at DESC, rowid DESC LIMIT 1", aid);
      return r && r.kind === 'processing_consent' ? { given: true, at: r.at } : { given: false, at: null };
    },
  };
}

/* Resolve each line's commission entitlement with the EXISTING rule, after checking the records it must bind to.
   requests: [{ line_id, artist_id, artwork_id, enquiry_ref, exclusion?, negotiation_note? }]
   A line is blocked (ok: false) when the artist or artwork is unknown, the artwork is not the artist's, no introduction is
   named, the introduction is not logged for this artist, or it is not tied to THIS artwork (an introduction recorded
   without an artwork, or for another artwork, cannot carry Founding or any other commission terms to this one: deciding
   otherwise is a founder decision). Each result is sealed and carries its binding and the RECORDED processing consent. */
export async function lineEntitlements(env, requests, decisionsInput, { at, records = null, resolve = R.entitlement } = {}) {
  const d = decisions(decisionsInput);
  if (typeof at !== 'string' || !Number.isFinite(Date.parse(at))) throw new R.RuleError('The time of the basket quote is required');
  if (records && env && env.ENVIRONMENT === 'production') throw new R.RuleError('Records cannot be supplied in production: they are read from the database');
  const rec = records || dbRecords(env);
  if (!Array.isArray(requests) || !requests.length) throw new R.RuleError('Name the basket lines to resolve');
  const out = {}, seenRefs = new Set();
  for (const q of requests) {
    const lid = id(q?.line_id, 'Line id'), aid = id(q.artist_id, 'Artist id'), wid = id(q.artwork_id, 'Artwork id');
    if (Object.hasOwn(out, lid)) throw new R.RuleError('Duplicate basket line ' + lid);
    const ref = typeof q.enquiry_ref === 'string' ? q.enquiry_ref.trim() : '';
    const binding = { artist_id: aid, artwork_id: wid, enquiry_ref: ref || null, enquiry_log_id: null };
    const block = reason => (out[lid] = seal({ ok: false, reason, binding, processing_consent: false, processing_consent_at: null }));
    const artist = await rec.artist(aid);
    if (!artist) { block('Unknown artist'); continue; }
    const work = await rec.artwork(wid);
    if (!work || work.artist_id !== aid) { block('This artwork is not this artist\'s'); continue; }
    if (d.basket_introduction === 'logged_enquiry_only' && !ref) { block('No PlotArt introduction is named for this line. A basket line needs a logged introduction (founder decision basket_introduction).'); continue; }
    if (seenRefs.has(ref)) { block('This introduction is already used by another line of the basket'); continue; }
    const log = await rec.enquiry(ref);
    if (!log || log.artist_id !== aid) { block(`No PlotArt introduction is logged for ${ref} and this artist.`); continue; }
    if (log.artwork_id !== wid) { block(`Introduction ${ref} is ${log.artwork_id ? 'for another artwork' : 'not tied to an artwork'}: it cannot set the commission for this one (founder decision)`); continue; }
    seenRefs.add(ref);
    binding.enquiry_log_id = log.id;
    const e = await resolve(env, { artist, enquiryRef: ref, at, exclusion: q.exclusion ?? null, negotiationNote: q.negotiation_note ?? null });
    const c = await rec.consent(aid);
    out[lid] = seal(e && e.ok === true
      ? { ok: true, bp: e.bp, basis: e.basis, evidence: { ...(e.evidence || {}), binding: { ...binding } }, binding, processing_consent: c.given === true, processing_consent_at: c.given ? c.at : null }
      : { ok: false, reason: (e && e.reason) || 'Commission entitlement unknown', binding, processing_consent: false, processing_consent_at: null });
  }
  return Object.freeze(out);
}
function seal(o) { freeze(o); SEALED.add(o); return o; }

/* ---------------------------------------------------------------- basket validation */
/* A basket is { lines, shipments }.
     line:     { line_id, artist_id, artwork_id, shipment_id, artwork_cents, entitlement, title? }
               entitlement is the sealed result lineEntitlements() gave for this line. Consent is never supplied here.
     shipment: { shipment_id, artist_id, method: 'delivery' | 'collection', delivery_cents, insurance_cents, cover? }
               Each shipment belongs to ONE artist. A 'delivery' shipment needs cover passing checkCover(); a collection has
               no delivery charge; any insurance charge needs recorded cover. Neither charge ever carries commission. */
export function cleanBasket(basket) {
  if (!basket || typeof basket !== 'object') throw new R.RuleError('A basket is required');
  const { lines, shipments } = basket;
  if (!Array.isArray(lines) || !lines.length) throw new R.RuleError('A basket needs at least one artwork');
  if (lines.length > MAX_BASKET_LINES) throw new R.RuleError(`A basket holds at most ${MAX_BASKET_LINES} artworks`);
  if (!Array.isArray(shipments) || !shipments.length) throw new R.RuleError('A basket needs at least one shipment');

  const ships = new Map();
  for (const s of shipments) {
    if (!s || typeof s !== 'object') throw new R.RuleError('Each shipment must be an object');
    const sid = id(s.shipment_id, 'Shipment id');
    if (ships.has(sid)) throw new R.RuleError('Duplicate shipment ' + sid);
    if (!['delivery', 'collection'].includes(s.method)) throw new R.RuleError(`Shipment ${sid}: method must be delivery or collection`);
    const d = cents(s.delivery_cents, `delivery charge for ${sid}`), ins = cents(s.insurance_cents, `insurance charge for ${sid}`);
    if (d + ins > R.MAX_DELIVERY_CENTS) throw new R.RuleError(`Shipment ${sid}: the delivery and insurance charges are above the pilot ceiling`);
    if (s.method === 'collection' && d > 0) throw new R.RuleError(`Shipment ${sid}: a collection has no delivery charge`);
    const cover = s.cover ? { cover_type: s.cover.cover_type, covered_value_cents: s.cover.covered_value_cents, insured_party: s.cover.insured_party } : null;
    if (ins > 0 && !cover) throw new R.RuleError(`Shipment ${sid}: an insurance charge needs recorded cover`);
    ships.set(sid, { shipment_id: sid, artist_id: id(s.artist_id, 'Artist id'), method: s.method, delivery_cents: d, insurance_cents: ins, cover });
  }

  const seenLine = new Set(), seenWork = new Set(), out = [];
  for (const l of lines) {
    if (!l || typeof l !== 'object') throw new R.RuleError('Each basket line must be an object');
    const lid = id(l.line_id, 'Line id');
    if (seenLine.has(lid)) throw new R.RuleError('Duplicate basket line ' + lid);
    seenLine.add(lid);
    const wid = id(l.artwork_id, 'Artwork id');
    if (seenWork.has(wid)) throw new R.RuleError(`Artwork ${wid} appears twice: each original can be sold only once`);
    seenWork.add(wid);
    const aid = id(l.artist_id, 'Artist id');
    const s = ships.get(l.shipment_id);
    if (!s) throw new R.RuleError(`Line ${lid}: unknown shipment ${l.shipment_id}`);
    if (s.artist_id !== aid) throw new R.RuleError(`Line ${lid}: shipment ${s.shipment_id} belongs to another artist (each artist ships their own works)`);
    if (Object.hasOwn(l, 'processing_consent')) throw new R.RuleError(`Line ${lid}: processing consent comes only from the artist's recorded consent, never from the request`);
    const e = l.entitlement;
    if (!e || typeof e !== 'object') throw new R.RuleError(`Line ${lid}: commission entitlement is required (from lineEntitlements)`);
    if (!isSealed(e)) throw new R.RuleError(`Line ${lid}: the entitlement was not produced by lineEntitlements from the records`);
    if (!e.binding || e.binding.artist_id !== aid || e.binding.artwork_id !== wid) throw new R.RuleError(`Line ${lid}: the entitlement belongs to another artist or artwork`);
    if (e.ok !== true) throw new R.RuleError(`Line ${lid}: ${e.reason || 'commission entitlement unknown'}`);
    if (typeof e.basis !== 'string' || !e.basis) throw new R.RuleError(`Line ${lid}: the entitlement must state its basis`);
    const m = R.amounts({ artwork_cents: l.artwork_cents, delivery_cents: 0, commission_bp: e.bp });
    out.push({ line_id: lid, artist_id: aid, artwork_id: wid, shipment_id: s.shipment_id, title: typeof l.title === 'string' ? l.title.slice(0, 250) : null,
      artwork_cents: m.artwork_cents, commission_bp: m.commission_bp, commission_cents: m.commission_cents, artist_artwork_cents: m.artist_artwork_cents,
      commission_basis: e.basis, entitlement_evidence: e.evidence ?? null, enquiry_ref: e.binding.enquiry_ref,
      processing_consent: e.processing_consent === true, processing_consent_at: e.processing_consent_at || null });
  }

  for (const s of ships.values()) {
    const carried = out.filter(l => l.shipment_id === s.shipment_id);
    if (!carried.length) throw new R.RuleError(`Shipment ${s.shipment_id} carries no artwork`);
    if (s.method === 'delivery' || s.cover) {
      try { R.checkCover(s.cover, sum(carried, l => l.artwork_cents)); }
      catch (e) { throw new R.RuleError(`Shipment ${s.shipment_id}: ${e.message}`); }
    }
  }
  const total = sum(out, l => l.artwork_cents) + sum([...ships.values()], s => s.delivery_cents + s.insurance_cents);
  if (total >= R.LINKED_THRESHOLD_CENTS) throw new R.RuleError(`This basket reaches EUR ${(total / 100).toFixed(2)} (EUR 10,000 or more), which is outside the pilot`);
  return { lines: out, shipments: [...ships.values()] };
}

/* ---------------------------------------------------------------- the payment plan */
/* What the buyer pays and how it is allocated, before Stripe's processing fee (see settle()). Per artist: gross = their
   artworks + their shipments' charges; commission = Σ per-artwork commissions; transfer before fees = gross − commission.
   Invariant: total = commission + Σ transfers before fees. */
export function plan(basketInput, decisionsInput, termsInput) {
  const d = decisions(decisionsInput);
  const terms = basketTerms(termsInput);
  for (const [k, v] of Object.entries(d))
    if (!(terms.permits[k] || []).includes(v)) throw new R.RuleError(`The basket terms ${terms.artist_terms_doc} do not permit ${k} = ${v}`);
  const b = cleanBasket(basketInput);
  const free = b.lines.find(l => l.commission_bp === 0);
  if (free && !terms.commission_free_lines)
    throw new R.RuleError(`Line ${free.line_id} is commission-free (${free.commission_basis}). Commission-free sales stay on direct payment under the current terms; basket terms that expressly permit them must be approved first`);
  if (d.processing_fee_bearer === 'artists_pro_rata') {
    // Existing pilot rule: on a commission-free sale a processing deduction needs the artist's separate, RECORDED consent.
    const missing = b.lines.find(l => l.commission_bp === 0 && !l.processing_consent);
    if (missing) throw new R.RuleError(`Line ${missing.line_id} is commission-free: the artist has not recorded consent to bearing processing fees`);
  }
  const artistIds = [...new Set(b.lines.map(l => l.artist_id))].sort(byId);
  const artists = artistIds.map(a => {
    const ls = b.lines.filter(l => l.artist_id === a), ss = b.shipments.filter(s => s.artist_id === a);
    const artwork = sum(ls, l => l.artwork_cents), commission = sum(ls, l => l.commission_cents);
    const delivery = sum(ss, s => s.delivery_cents), insurance = sum(ss, s => s.insurance_cents);
    const gross = artwork + delivery + insurance;
    return { artist_id: a, line_ids: ls.map(l => l.line_id), shipment_ids: ss.map(s => s.shipment_id), artwork_cents: artwork,
      commission_cents: commission, delivery_cents: delivery, insurance_cents: insurance, gross_cents: gross,
      transfer_before_fees_cents: gross - commission, release: d.transfer_timing };
  });
  const total = sum(artists, a => a.gross_cents), commission = sum(artists, a => a.commission_cents);
  invariant(total === commission + sum(artists, a => a.transfer_before_fees_cents), 'the plan does not balance');
  invariant(artists.every(a => a.transfer_before_fees_cents >= 0), 'an artist allocation is negative');
  const items = [];
  for (const a of artists) {
    for (const l of b.lines.filter(x => x.artist_id === a.artist_id)) items.push({ kind: 'artwork', ref: l.line_id, artist_id: a.artist_id, amount_cents: l.artwork_cents });
    for (const s of b.shipments.filter(x => x.artist_id === a.artist_id)) {
      if (s.delivery_cents) items.push({ kind: 'delivery', ref: s.shipment_id, artist_id: a.artist_id, amount_cents: s.delivery_cents });
      if (s.insurance_cents) items.push({ kind: 'insurance', ref: s.shipment_id, artist_id: a.artist_id, amount_cents: s.insurance_cents });
    }
  }
  invariant(sum(items, i => i.amount_cents) === total, 'checkout items do not sum to the total');
  return freeze({ version: PLAN_VERSION, pilot: BASKET_PILOT_ID, currency: R.CURRENCY, decisions: d,
    terms: { livemode: terms.livemode, artist_terms_doc: terms.artist_terms_doc, buyer_terms_doc: terms.buyer_terms_doc },
    lines: b.lines, shipments: b.shipments, artists, items, total_cents: total, commission_cents: commission });
}

/* ---------------------------------------------------------------- settlement: the actual processing fee */
/* Invariant: total = Σ transfers + PlotArt net + fee + VAT. A share that would make a transfer negative is refused. */
export function settle(p, { fee_cents, fee_vat_cents }) {
  assertPlan(p);
  const fee = cents(fee_cents, 'processing fee') + cents(fee_vat_cents, 'VAT on the processing fee');
  const shares = p.decisions.processing_fee_bearer === 'plotart' ? p.artists.map(() => 0) : apportion(fee, p.artists.map(a => a.gross_cents));
  const artists = p.artists.map((a, i) => {
    const t = a.transfer_before_fees_cents - shares[i];
    if (t < 0) throw new R.RuleError(`Allocation failed: the processing share for ${a.artist_id} exceeds their allocation`);
    return { artist_id: a.artist_id, transfer_before_fees_cents: a.transfer_before_fees_cents, processing_share_cents: shares[i], transfer_cents: t, release: a.release };
  });
  const transfers = sum(artists, a => a.transfer_cents);
  const platformNet = p.total_cents - transfers - fee;
  invariant(p.total_cents === transfers + platformNet + fee, 'settlement does not balance');
  return freeze({ fee_cents, fee_vat_cents, fee_total_cents: fee, artists, transfers_cents: transfers, platform_net_cents: platformNet,
    platform_shortfall_cents: Math.max(0, -platformNet) });
}

/* ---------------------------------------------------------------- transfers: what to send now */
/* For each artist: transfer the remainder now, hold it, or nothing (done). Never two in flight; a failed attempt is retried
   with the next attempt number (a new idempotency key), a requested or made one never again.
   state.artists[artist_id] = { release_ready_at, attempts, in_flight_or_made_cents, pending_reduced_cents }
     attempts                 allocation transfers recorded so far (any status)
     in_flight_or_made_cents  allocation transfers requested or created (not failed)
   opts: { basket_id, now, open_dispute }   An open dispute holds every transfer (review M4). */
export function transferPlan(p, settlement, state = {}, { basket_id, now, open_dispute = false } = {}) {
  assertPlan(p);
  if (!settlement || !Array.isArray(settlement.artists) || settlement.artists.length !== p.artists.length) throw new R.RuleError('The settlement of this plan is required');
  id(basket_id, 'Basket id');
  if (typeof now !== 'string' || !Number.isFinite(Date.parse(now))) throw new R.RuleError('The current time is required');
  return freeze(settlement.artists.map(a => {
    const st = (state.artists || {})[a.artist_id] || {};
    const made = cents(st.in_flight_or_made_cents ?? 0, 'transferred so far'), reduced = cents(st.pending_reduced_cents ?? 0, 'reductions');
    const attempts = cents(st.attempts ?? 0, 'attempts');
    const left = a.transfer_cents - made - reduced;
    if (left < 0) throw new R.RuleError(`Allocation failed: ${a.artist_id} has been sent more than is due`);
    if (left === 0) return { artist_id: a.artist_id, action: 'done', amount_cents: 0 };
    if (made > 0) return { artist_id: a.artist_id, action: 'wait', amount_cents: 0, reason: 'a transfer for this artist is already in flight or made' };
    if (open_dispute) return { artist_id: a.artist_id, action: 'hold', amount_cents: left, reason: 'a dispute on this basket is open' };
    if (!st.release_ready_at || Date.parse(st.release_ready_at) > Date.parse(now)) return { artist_id: a.artist_id, action: 'hold', amount_cents: left, reason: `not released (${a.release})` };
    const attempt = attempts + 1;
    return { artist_id: a.artist_id, action: 'transfer', amount_cents: left, attempt, idempotency_key: keys.transfer({ basket_id, artist_id: a.artist_id, attempt }) };
  }));
}

/* ---------------------------------------------------------------- refunds */
/* state (amounts so far, in cents; derived from the records):
     { lines: { [line_id]: { artwork_refunded_cents, commission_returned_cents } }, shipments: { [shipment_id]: { refunded_cents } },
       artists: { [artist_id]: { transfer_due_cents, transferred_cents, reversed_cents, pending_reduced_cents } } }
   "refunded so far" counts ACTIVE refunds (requested, pending, requires_action, succeeded): a pending refund is not money
   free to refund again. request: { lines: [{ line_id, artwork_cents }], shipments: [{ shipment_id, cents }] }.
   Commission returned per PA-GAA 9.2; each artist's debit comes from the transfer not yet made, then by reversal, then is a
   SHORTFALL that Stripe cannot recover. Invariant: buyer refund = Σ artist debits + commission returned. */
export function refund(p, state = {}, request = {}) {
  assertPlan(p);
  const reqLines = request.lines || [], reqShips = request.shipments || [];
  if (!Array.isArray(reqLines) || !Array.isArray(reqShips) || (!reqLines.length && !reqShips.length)) throw new R.RuleError('Name what is being refunded');
  const S = state || {};
  const parts = refundParts(p, S, reqLines, reqShips);
  const artists = recover(S, [...parts.lines, ...parts.shipments]);
  const buyer = sum(parts.lines, l => l.artwork_refund_cents) + sum(parts.shipments, s => s.refund_cents);
  const commission = sum(parts.lines, l => l.commission_returned_cents);
  invariant(buyer === sum(artists, a => a.debit_cents) + commission, 'the refund does not balance');
  return freeze({ buyer_refund_cents: buyer, commission_returned_cents: commission, lines: parts.lines, shipments: parts.shipments, artists,
    shortfall_cents: sum(artists, a => a.shortfall_cents) });
}
function refundParts(p, S, reqLines, reqShips) {
  const seen = new Set();
  const lines = reqLines.map(r => {
    const l = p.lines.find(x => x.line_id === r?.line_id);
    if (!l) throw new R.RuleError('Unknown line ' + r?.line_id);
    if (seen.has('l:' + l.line_id)) throw new R.RuleError('Line named twice: ' + l.line_id);
    seen.add('l:' + l.line_id);
    const amt = cents(r.artwork_cents, `refund for ${l.line_id}`);
    if (amt === 0) throw new R.RuleError(`Refund for ${l.line_id} must be more than zero`);
    const st = (S.lines || {})[l.line_id] || {};
    const before = cents(st.artwork_refunded_cents ?? 0, 'artwork refunded so far'), commBefore = cents(st.commission_returned_cents ?? 0, 'commission returned so far');
    if (before + amt > l.artwork_cents) throw new R.RuleError(`Refund for ${l.line_id} exceeds the artwork amount paid`);
    const ret = R.commissionRefund({ artwork_cents: l.artwork_cents, commission_cents: l.commission_cents, artwork_refunded_before: before,
      artwork_refund_now: amt, commission_refunded_before: commBefore });
    return { line_id: l.line_id, artist_id: l.artist_id, artwork_refund_cents: amt, commission_returned_cents: ret, artist_debit_cents: amt - ret };
  });
  const shipments = reqShips.map(r => {
    const s = p.shipments.find(x => x.shipment_id === r?.shipment_id);
    if (!s) throw new R.RuleError('Unknown shipment ' + r?.shipment_id);
    if (seen.has('s:' + s.shipment_id)) throw new R.RuleError('Shipment named twice: ' + s.shipment_id);
    seen.add('s:' + s.shipment_id);
    const amt = cents(r.cents, `refund for ${s.shipment_id}`);
    if (amt === 0) throw new R.RuleError(`Refund for ${s.shipment_id} must be more than zero`);
    const before = cents(((S.shipments || {})[s.shipment_id] || {}).refunded_cents ?? 0, 'shipment refunded so far');
    if (before + amt > s.delivery_cents + s.insurance_cents) throw new R.RuleError(`Refund for ${s.shipment_id} exceeds its delivery and insurance charges`);
    return { shipment_id: s.shipment_id, artist_id: s.artist_id, refund_cents: amt, artist_debit_cents: amt };
  });
  return { lines, shipments };
}

/* Each affected artist's debit: reduce the transfer not yet made, then reverse transfers made, then shortfall. */
function recover(S, parts) {
  const ids = [...new Set(parts.map(x => x.artist_id))].sort(byId);
  return ids.map(aid => {
    const debit = sum(parts.filter(x => x.artist_id === aid), x => x.artist_debit_cents);
    const st = (S.artists || {})[aid];
    if (!st || st.transfer_due_cents === undefined) throw new R.RuleError(`Artist ${aid}: the settled transfer is not known yet (settle the payment first)`);
    const due = cents(st.transfer_due_cents, 'transfer due'), made = cents(st.transferred_cents ?? 0, 'transferred'),
      reversed = cents(st.reversed_cents ?? 0, 'reversed'), reduced = cents(st.pending_reduced_cents ?? 0, 'pending reductions');
    if (made > due || reversed > made || made + reduced > due) throw new R.RuleError(`Artist ${aid}: the transfer record is inconsistent`);
    const pending = due - made - reduced, reversible = made - reversed;
    const fromPending = Math.min(debit, pending), fromReversal = Math.min(debit - fromPending, reversible);
    return { artist_id: aid, debit_cents: debit, reduce_pending_cents: fromPending, reverse_cents: fromReversal,
      shortfall_cents: debit - fromPending - fromReversal };
  });
}

/* A refund that Stripe reports as failed (including one that first succeeded). The buyer was not repaid, so every movement
   made for it is undone: reductions restored, reversed amounts re-credited to the artist (a 'recredit' transfer tied to the
   refund), shortfalls cleared, and the commission PlotArt returned is kept by PlotArt again.
   Invariant: buyer refund = Σ (restored + recredited + shortfall cleared) + commission reclaimed. */
export function refundFailed(p, refundResult) {
  assertPlan(p);
  if (!refundResult || !Array.isArray(refundResult.artists) || !Number.isSafeInteger(refundResult.buyer_refund_cents)) throw new R.RuleError('The refund calculation (refund()) is required');
  const artists = refundResult.artists.map(a => ({ artist_id: a.artist_id, restore_pending_cents: a.reduce_pending_cents, recredit_cents: a.reverse_cents, shortfall_cleared_cents: a.shortfall_cents }));
  invariant(refundResult.buyer_refund_cents === sum(artists, a => a.restore_pending_cents + a.recredit_cents + a.shortfall_cleared_cents) + refundResult.commission_returned_cents,
    'the failed refund does not unwind exactly');
  return freeze({ commission_reclaimed_cents: refundResult.commission_returned_cents, artists });
}

/* A transfer reversal Stripe refused (for example the artist's Stripe balance cannot cover it). Either retry with the next
   attempt (a new idempotency key), or record the amount as a shortfall to recover outside Stripe. Never both. */
export function reversalFailed({ transfer_id, cause_kind, cause_id, attempt, amount_cents }, { retry }) {
  id(transfer_id, 'Transfer id'); id(cause_id, 'Cause id'); posInt(attempt, 'Attempt'); cents(amount_cents, 'reversal amount');
  if (!['refund', 'dispute'].includes(cause_kind)) throw new R.RuleError('A reversal is for a refund or a dispute');
  if (retry !== true && retry !== false) throw new R.RuleError('Say whether to retry the reversal or record a shortfall');
  return freeze(retry
    ? { action: 'retry', attempt: attempt + 1, idempotency_key: keys.reversal({ transfer_id, cause_kind, cause_id, attempt: attempt + 1 }), amount_cents }
    : { action: 'shortfall', amount_cents, cause_kind: 'reversal', cause_id: transfer_id + ':' + cause_kind + ':' + cause_id });
}

/* ---------------------------------------------------------------- disputes */
/* A dispute is raised on the whole basket payment, which Stripe debits from PlotArt's platform balance.
     open:  nothing moves, and EVERY artist's untransferred allocation is held until it closes (review M4).
     won:   nothing moves; the hold ends.
     lost:  PlotArt carries the amount and fee unless the founder decided otherwise. When any part is carried by artists,
            an explicit attribution to lines/shipments is REQUIRED (no default spreading across uninvolved artists), and
            the attributed amount is treated as a refund of those parts (commission returned, PA-GAA 9.1 and 9.2).
   Invariant (lost): amount + fee = Σ artist recoveries + PlotArt's cost. */
export function dispute(p, state = {}, { outcome, amount_cents, fee_cents = 0, attribution = null } = {}) {
  assertPlan(p);
  if (!['open', 'won', 'lost'].includes(outcome)) throw new R.RuleError('Dispute outcome must be open, won or lost');
  const amount = cents(amount_cents, 'disputed amount'), fee = cents(fee_cents, 'dispute fee');
  const S = state || {};
  const refundable = sum(p.lines, l => l.artwork_cents - cents(((S.lines || {})[l.line_id] || {}).artwork_refunded_cents ?? 0, 'artwork refunded so far'))
    + sum(p.shipments, s => s.delivery_cents + s.insurance_cents - cents(((S.shipments || {})[s.shipment_id] || {}).refunded_cents ?? 0, 'shipment refunded so far'));
  if (amount === 0 || amount > refundable) throw new R.RuleError('The disputed amount must be more than zero and no more than what remains unrefunded');
  const allArtists = p.artists.map(a => a.artist_id);
  if (outcome === 'open') return freeze({ outcome, amount_cents: amount, fee_cents: fee, hold_transfers: allArtists, artists: [], platform_cost_cents: 0, attribution: null });
  if (outcome === 'won') return freeze({ outcome, amount_cents: amount, fee_cents: fee, hold_transfers: [], artists: [], platform_cost_cents: 0, attribution: null });

  const d = p.decisions, artistsBear = d.dispute_loss_bearer === 'artists_by_line' || d.dispute_fee_bearer === 'artists_by_line';
  if (artistsBear && !attribution) throw new R.RuleError('A lost dispute carried by artists needs an explicit attribution to the disputed lines or shipments');
  let att = null;
  if (attribution) {
    att = { lines: (attribution.lines || []).map(x => ({ line_id: x.line_id, artwork_cents: x.artwork_cents })),
      shipments: (attribution.shipments || []).map(x => ({ shipment_id: x.shipment_id, cents: x.cents })) };
    const total = sum(att.lines, x => cents(x.artwork_cents, 'attributed amount')) + sum(att.shipments, x => cents(x.cents, 'attributed amount'));
    if (total !== amount) throw new R.RuleError('The attribution must add up to the disputed amount');
    refundParts(p, S, att.lines, att.shipments);   // each part must be within what remains on that line or shipment
  }
  if (!artistsBear) return freeze({ outcome, amount_cents: amount, fee_cents: fee, hold_transfers: [], attribution: att, artists: [],
    platform_cost_cents: amount + fee, commission_returned_cents: 0, lines: [], shipments: [], shortfall_cents: 0 });

  const parts = refundParts(p, S, att.lines, att.shipments);
  const perArtist = [...new Set([...parts.lines, ...parts.shipments].map(x => x.artist_id))].sort(byId);
  const attributed = perArtist.map(aid => sum(parts.lines.filter(l => l.artist_id === aid), l => l.artwork_refund_cents) + sum(parts.shipments.filter(s => s.artist_id === aid), s => s.refund_cents));
  const lossDebits = perArtist.map(aid => d.dispute_loss_bearer === 'artists_by_line'
    ? sum([...parts.lines, ...parts.shipments].filter(x => x.artist_id === aid), x => x.artist_debit_cents) : 0);
  const feeShares = d.dispute_fee_bearer === 'artists_by_line' ? apportion(fee, attributed) : perArtist.map(() => 0);
  const debits = perArtist.map((aid, i) => ({ artist_id: aid, artist_debit_cents: lossDebits[i] + feeShares[i] }));
  const artists = recover(S, debits).map((a, i) => ({ ...a, loss_cents: lossDebits[i], dispute_fee_cents: feeShares[i] }));
  const commission = d.dispute_loss_bearer === 'artists_by_line' ? sum(parts.lines, l => l.commission_returned_cents) : 0;
  const platformCost = amount + fee - sum(artists, a => a.debit_cents);
  invariant(platformCost >= 0, 'artists would be charged more than the dispute cost');
  return freeze({ outcome, amount_cents: amount, fee_cents: fee, hold_transfers: [], attribution: att, artists, platform_cost_cents: platformCost,
    commission_returned_cents: commission, lines: parts.lines, shipments: parts.shipments, shortfall_cents: sum(artists, a => a.shortfall_cents) });
}

/* ---------------------------------------------------------------- linked purchases across BOTH checkouts (review M2) */
/* The pilot refuses a purchase when this buyer's apparently linked purchases reach EUR 10,000. This counts single-artist
   orders (as checkout.js linkedCheck does) AND baskets, over the same window, read-only. */
export async function basketLinkedCheck(env, { buyer_email, total_cents, exclude_basket_id = null, now = new Date().toISOString() }) {
  if (typeof buyer_email !== 'string' || !buyer_email.includes('@')) throw new R.RuleError('The buyer\'s email address is required');
  cents(total_cents, 'basket total');
  const since = new Date(Date.parse(now) - R.LINKED_WINDOW_DAYS * 86400_000).toISOString();
  const q = async (sql, ...a) => (await env.DB.prepare(sql).bind(...a).all()).results;
  const single = await q(`SELECT reference, artwork_cents + COALESCE(delivery_cents, 0) AS total FROM checkout_orders
    WHERE lower(buyer_email) = lower(?) AND created_at >= ? AND artwork_cents IS NOT NULL
      AND (payment_status <> 'none' OR status IN ('quoted', 'checkout_open', 'payment_failed'))`, buyer_email, since);
  const baskets = await q(`SELECT reference, total_cents AS total FROM basket_orders
    WHERE lower(buyer_email) = lower(?) AND created_at >= ? AND id IS NOT ? AND (payment_status <> 'none' OR status IN ('checkout_open', 'payment_failed'))`, buyer_email, since, exclude_basket_id);
  const total = sum([...single, ...baskets], r => r.total) + total_cents;
  return freeze({ ok: total < R.LINKED_THRESHOLD_CENTS, total_cents: total, linked: [...single, ...baskets].map(r => r.reference), window_days: R.LINKED_WINDOW_DAYS,
    reason: total < R.LINKED_THRESHOLD_CENTS ? null : `This buyer's apparently linked purchases reach EUR ${(total / 100).toFixed(2)} (EUR 10,000 or more), which is outside the pilot.` });
}

function assertPlan(p) {
  if (!p || p.version !== PLAN_VERSION || !Object.isFrozen(p)) throw new R.RuleError('A basket plan from plan() is required');
}
