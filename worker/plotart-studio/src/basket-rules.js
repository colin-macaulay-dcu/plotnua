/* PlotArt · multi-artist basket · allocation rules (Phase 1, 21 Nov 2026). NOT WIRED IN. NO STRIPE CALLS. NO DATABASE WRITES.

   One buyer payment for artworks from several artists, taken on PlotArt's platform account and paid on to each artist by
   a Stripe transfer ("separate charges and transfers"). This module is the ONE definition of how that payment is split.
   It is pure: every function takes plain objects and returns plain, frozen objects. It never calls Stripe, never reads or
   writes the database (except lineEntitlements, which only READS through the existing entitlement rule), and is not
   imported by any Worker yet. The single-artist direct-charge pilot (checkout.js, checkout-rules.js) is unchanged.

   Reused from checkout-rules.js, not re-implemented:
     · amounts()            per-artwork commission (floor, in the artist's favour), the price limits, integer cents
     · commissionRefund()   PA-GAA cl. 9.2: commission kept after a partial refund is proportional to the artwork kept
     · entitlement()        Founding Enquiry 0% permanently; Founding Artist 0% without accepted commission terms;
                            Gallery Artist at their artist_terms rate; anything unknown blocks (PA-FAA 5–6, PA-GAA 5)
     · checkCover()         confirmed transit insurance covering at least the artworks shipped
     · LINKED_THRESHOLD_CENTS, MAX_DELIVERY_CENTS, RuleError

   Founder decisions that are NOT settled are explicit inputs (DECISIONS). There are no defaults: a missing or unknown
   decision is refused, so nothing here can quietly choose who bears processing fees, when artists are paid, who carries a
   lost dispute, or how a basket purchase counts as a PlotArt introduction.

   Money is integer euro cents throughout. Every split of an amount across artists or lines uses apportion() (largest
   remainder, deterministic order), so parts always sum exactly to the whole. Every result is checked against its own
   conservation invariant before it is returned; a plan that does not balance throws instead of being returned. */
import * as R from './checkout-rules.js';

export const BASKET_PILOT_ID = 'plotart-basket-1';
export const PLAN_VERSION = 'basket-plan-1';
/* A technical bound on one basket (size of the Checkout Session and of the records), not a commercial policy. */
export const MAX_BASKET_LINES = 20;
const ID = /^[A-Za-z0-9_-]{1,64}$/;

/* ---------------------------------------------------------------- founder decisions (inputs, never defaults) */
export const DECISIONS = Object.freeze({
  // Who bears Stripe's processing fee (and the VAT Stripe charges on it) on the basket payment. Stripe deducts it from
  // PlotArt's platform balance in this model, and does not return it when a payment is refunded.
  processing_fee_bearer: Object.freeze({
    plotart: 'PlotArt bears the fee; artists receive their allocation without any processing deduction',
    artists_pro_rata: 'Each artist bears a share of the actual fee in proportion to their gross allocation (commission-free lines need the artist\'s separate processing consent)',
  }),
  // When each artist's transfer may be made. The engine records it on the plan; it does not schedule anything.
  transfer_timing: Object.freeze({
    on_payment: 'Transfer once Stripe confirms the payment',
    after_delivery: 'Transfer once the artist\'s shipment is recorded as delivered (or collected)',
    after_cancellation_window: 'Transfer once the buyer\'s cancellation period for that shipment has ended',
  }),
  // Who carries the disputed amount when a dispute is lost.
  dispute_loss_bearer: Object.freeze({
    plotart: 'PlotArt carries the lost amount; no artist transfer is reversed',
    artists_by_line: 'The lost amount is attributed to the disputed lines and recovered from those artists like a refund (PlotArt returns the commission on it, PA-GAA 9.1)',
  }),
  // Who carries Stripe's dispute fee when a dispute is lost.
  dispute_fee_bearer: Object.freeze({
    plotart: 'PlotArt carries the dispute fee',
    artists_by_line: 'The dispute fee is shared by the artists the lost amount is attributed to, in proportion to it',
  }),
  // How a basket line establishes the PlotArt introduction that the commission rules depend on. Only the existing rule
  // is implemented: the line must name an introduction already logged in enquiry_log. Any other basis (for example
  // treating a basket purchase itself as an introduction) needs a founder decision and agreement changes first.
  basket_introduction: Object.freeze({
    logged_enquiry_only: 'Every line names a PlotArt introduction already logged for that artist; otherwise the line is blocked',
  }),
});

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

/* ---------------------------------------------------------------- helpers */
const isCents = v => Number.isSafeInteger(v) && v >= 0;
function cents(v, what) { if (!isCents(v)) throw new R.RuleError(`Give the ${what} in whole euro cents`); return v; }
function id(v, what) { if (typeof v !== 'string' || !ID.test(v)) throw new R.RuleError(`${what} must be 1–64 letters, digits, - or _`); return v; }
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

/* ---------------------------------------------------------------- basket validation */
/* A basket is { lines, shipments }.
     line:     { line_id, artist_id, artwork_id, shipment_id, artwork_cents, entitlement, processing_consent?, title? }
               entitlement is exactly what checkout-rules.entitlement() returns for that artist and introduction:
               { ok: true, bp, basis, evidence } — or { ok: false, reason }, which blocks the basket.
     shipment: { shipment_id, artist_id, method: 'delivery' | 'collection', delivery_cents, insurance_cents, cover? }
               Each shipment belongs to ONE artist (each artist fulfils their own part). delivery_cents is packing and
               transport; insurance_cents is the itemised transit-cover charge. Neither ever carries commission. A
               'delivery' shipment needs cover that passes checkout-rules.checkCover() for the artworks it carries. */
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
    ships.set(sid, { shipment_id: sid, artist_id: id(s.artist_id, 'Artist id'), method: s.method, delivery_cents: d, insurance_cents: ins,
      cover: s.cover ? { cover_type: s.cover.cover_type, covered_value_cents: s.cover.covered_value_cents, insured_party: s.cover.insured_party } : null });
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
    const e = l.entitlement;
    if (!e || typeof e !== 'object') throw new R.RuleError(`Line ${lid}: commission entitlement is required (checkout-rules.entitlement)`);
    if (e.ok !== true) throw new R.RuleError(`Line ${lid}: ${e.reason || 'commission entitlement unknown'}`);
    if (typeof e.basis !== 'string' || !e.basis) throw new R.RuleError(`Line ${lid}: the entitlement must state its basis`);
    if (l.processing_consent !== undefined && typeof l.processing_consent !== 'boolean') throw new R.RuleError(`Line ${lid}: processing consent must be yes or no`);
    // amounts() checks the price range and the commission rate (0–15%) and computes commission on the artwork only
    const m = R.amounts({ artwork_cents: l.artwork_cents, delivery_cents: 0, commission_bp: e.bp });
    out.push({ line_id: lid, artist_id: aid, artwork_id: wid, shipment_id: s.shipment_id, title: typeof l.title === 'string' ? l.title.slice(0, 250) : null,
      artwork_cents: m.artwork_cents, commission_bp: m.commission_bp, commission_cents: m.commission_cents, artist_artwork_cents: m.artist_artwork_cents,
      commission_basis: e.basis, entitlement_evidence: e.evidence ?? null, processing_consent: l.processing_consent === true });
  }

  for (const s of ships.values()) {
    const carried = out.filter(l => l.shipment_id === s.shipment_id);
    if (!carried.length) throw new R.RuleError(`Shipment ${s.shipment_id} carries no artwork`);
    if (s.method === 'delivery') {
      try { R.checkCover(s.cover, sum(carried, l => l.artwork_cents)); }
      catch (e) { throw new R.RuleError(`Shipment ${s.shipment_id}: ${e.message}`); }
    }
  }
  const total = sum(out, l => l.artwork_cents) + sum([...ships.values()], s => s.delivery_cents + s.insurance_cents);
  // Existing pilot rule (checkout.js linkedCheck): purchases reaching EUR 10,000 are outside the pilot until PlotArt's
  // anti-money-laundering position is settled. A basket is one purchase; linked orders elsewhere are the caller's check.
  if (total >= R.LINKED_THRESHOLD_CENTS) throw new R.RuleError(`This basket reaches EUR ${(total / 100).toFixed(2)} (EUR 10,000 or more), which is outside the pilot`);
  return { lines: out, shipments: [...ships.values()] };
}

/* ---------------------------------------------------------------- the payment plan */
/* What the buyer pays and how it is allocated, before Stripe's processing fee (known only once Stripe records it; see
   settle()). Per artist: gross = their artworks + their shipments' charges; commission = the sum of their per-artwork
   commissions; transfer before fees = gross − commission. Invariant: total = commission + Σ transfers before fees. */
export function plan(basketInput, decisionsInput) {
  const d = decisions(decisionsInput);
  const b = cleanBasket(basketInput);
  if (d.processing_fee_bearer === 'artists_pro_rata') {
    // Existing pilot rule (MANAGED-CHECKOUT-PILOT.md "Founding Artists keep direct payment; the processing charge needs
    // separate consent"): on a commission-free sale a processing deduction needs the artist's separate, explicit consent.
    const missing = b.lines.find(l => l.commission_bp === 0 && !l.processing_consent);
    if (missing) throw new R.RuleError(`Line ${missing.line_id} is commission-free: the artist must separately consent to bearing processing fees`);
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
  // Checkout line items, in a stable order: each artist's artworks, then that artist's shipments. Their sum is the total
  // the hosted checkout must charge; the caller compares Stripe's amount_total with total_cents before accepting it.
  const items = [];
  for (const a of artists) {
    for (const l of b.lines.filter(x => x.artist_id === a.artist_id)) items.push({ kind: 'artwork', ref: l.line_id, artist_id: a.artist_id, amount_cents: l.artwork_cents });
    for (const s of b.shipments.filter(x => x.artist_id === a.artist_id)) {
      if (s.delivery_cents) items.push({ kind: 'delivery', ref: s.shipment_id, artist_id: a.artist_id, amount_cents: s.delivery_cents });
      if (s.insurance_cents) items.push({ kind: 'insurance', ref: s.shipment_id, artist_id: a.artist_id, amount_cents: s.insurance_cents });
    }
  }
  invariant(sum(items, i => i.amount_cents) === total, 'checkout items do not sum to the total');
  return freeze({ version: PLAN_VERSION, pilot: BASKET_PILOT_ID, currency: R.CURRENCY, decisions: d, lines: b.lines, shipments: b.shipments,
    artists, items, total_cents: total, commission_cents: commission });
}

/* ---------------------------------------------------------------- settlement: the actual processing fee */
/* Once Stripe records the payment's balance transaction: fee_cents and fee_vat_cents are Stripe's actual figures.
   Returns each artist's transfer amount and PlotArt's net. Invariant: total = Σ transfers + PlotArt net + fee + VAT.
   A share that would make an artist's transfer negative is refused (failed allocation), never clipped. */
export function settle(p, { fee_cents, fee_vat_cents }) {
  assertPlan(p);
  const fee = cents(fee_cents, 'processing fee') + cents(fee_vat_cents, 'VAT on the processing fee');
  let shares;
  if (p.decisions.processing_fee_bearer === 'plotart') shares = p.artists.map(() => 0);
  else shares = apportion(fee, p.artists.map(a => a.gross_cents));
  const artists = p.artists.map((a, i) => {
    const t = a.transfer_before_fees_cents - shares[i];
    if (t < 0) throw new R.RuleError(`Allocation failed: the processing share for ${a.artist_id} exceeds their allocation`);
    return { artist_id: a.artist_id, transfer_before_fees_cents: a.transfer_before_fees_cents, processing_share_cents: shares[i], transfer_cents: t, release: a.release };
  });
  const transfers = sum(artists, a => a.transfer_cents);
  const platformNet = p.total_cents - transfers - fee;   // may be negative when PlotArt bears a fee larger than its commission
  invariant(p.total_cents === transfers + platformNet + fee, 'settlement does not balance');
  return freeze({ fee_cents, fee_vat_cents, fee_total_cents: fee, artists, transfers_cents: transfers, platform_net_cents: platformNet,
    platform_shortfall_cents: Math.max(0, -platformNet) });
}

/* ---------------------------------------------------------------- refunds */
/* state (all optional; amounts so far, in cents):
     { lines:     { [line_id]: { artwork_refunded_cents, commission_returned_cents } },
       shipments: { [shipment_id]: { refunded_cents } },
       artists:   { [artist_id]: { transfer_due_cents, transferred_cents, reversed_cents, pending_reduced_cents } } }
   transfer_due_cents is the settled transfer (settle().artists[].transfer_cents); before settlement it is unknown and the
   refund is refused for that artist. request: { lines: [{ line_id, artwork_cents }], shipments: [{ shipment_id, cents }] }.

   Per artwork line, PlotArt returns the commission PA-GAA 9.2 requires (checkout-rules.commissionRefund), so the artist is
   debited the refunded amount less that commission. Delivery and insurance refunds are debited in full (never commission).
   Each artist's debit is taken first from any transfer not yet made, then by reversing transfers already made; anything
   still uncovered is a SHORTFALL that Stripe cannot recover (for example an artist who bore a processing share, or whose
   transfers were already reversed) and must be resolved outside Stripe. Stripe's processing fee is never returned on a
   refund, so refunds never change who bore it.
   Invariant: buyer refund = Σ artist debits + commission returned. */
export function refund(p, state = {}, request = {}) {
  assertPlan(p);
  const reqLines = request.lines || [], reqShips = request.shipments || [];
  if (!Array.isArray(reqLines) || !Array.isArray(reqShips) || (!reqLines.length && !reqShips.length)) throw new R.RuleError('Name what is being refunded');
  const S = state || {};
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
  const artists = recover(p, S, [...lines, ...shipments]);
  const buyer = sum(lines, l => l.artwork_refund_cents) + sum(shipments, s => s.refund_cents);
  const commission = sum(lines, l => l.commission_returned_cents);
  invariant(buyer === sum(artists, a => a.debit_cents) + commission, 'the refund does not balance');
  return freeze({ buyer_refund_cents: buyer, commission_returned_cents: commission, lines, shipments, artists,
    shortfall_cents: sum(artists, a => a.shortfall_cents) });
}

/* Each affected artist's debit: reduce the transfer not yet made, then reverse transfers made, then shortfall. */
function recover(p, S, parts) {
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

/* ---------------------------------------------------------------- disputes */
/* A dispute is raised on the whole basket payment, which Stripe debits from PlotArt's platform balance.
     outcome 'open' or 'won': nothing moves between PlotArt and artists (a won dispute is returned to PlotArt by Stripe).
     outcome 'lost': the lost amount is attributed to lines and shipments, either explicitly (attribution) or, without
     one, in proportion to what remains unrefunded on each. Then, by the founder's decisions:
       dispute_loss_bearer = plotart          PlotArt carries the amount; no artist is debited.
       dispute_loss_bearer = artists_by_line  treated as a refund of the attributed parts (commission returned, PA-GAA 9.1
                                              and 9.2), recovered from those artists through refund().
       dispute_fee_bearer  = plotart          PlotArt carries Stripe's dispute fee.
       dispute_fee_bearer  = artists_by_line  the fee is shared by the artists the lost amount is attributed to, in
                                              proportion to it; it is added to their recovery (it can only be a shortfall
                                              or a pending reduction/reversal like any other debit).
   Invariant (lost): amount + fee = Σ artist recoveries + PlotArt's cost. */
export function dispute(p, state = {}, { outcome, amount_cents, fee_cents = 0, attribution = null } = {}) {
  assertPlan(p);
  if (!['open', 'won', 'lost'].includes(outcome)) throw new R.RuleError('Dispute outcome must be open, won or lost');
  const amount = cents(amount_cents, 'disputed amount'), fee = cents(fee_cents, 'dispute fee');
  const S = state || {};
  const remainingLines = p.lines.map(l => ({ line_id: l.line_id, artist_id: l.artist_id,
    left: l.artwork_cents - cents(((S.lines || {})[l.line_id] || {}).artwork_refunded_cents ?? 0, 'artwork refunded so far') }));
  const remainingShips = p.shipments.map(s => ({ shipment_id: s.shipment_id, artist_id: s.artist_id,
    left: s.delivery_cents + s.insurance_cents - cents(((S.shipments || {})[s.shipment_id] || {}).refunded_cents ?? 0, 'shipment refunded so far') }));
  const refundable = sum(remainingLines, x => x.left) + sum(remainingShips, x => x.left);
  if (amount === 0 || amount > refundable) throw new R.RuleError('The disputed amount must be more than zero and no more than what remains unrefunded');
  if (outcome !== 'lost') return freeze({ outcome, amount_cents: amount, fee_cents: fee, artists: [], platform_cost_cents: 0, attribution: null, recovery: null });

  let att;
  if (attribution) {
    att = { lines: (attribution.lines || []).map(x => ({ line_id: x.line_id, artwork_cents: x.artwork_cents })),
      shipments: (attribution.shipments || []).map(x => ({ shipment_id: x.shipment_id, cents: x.cents })) };
    const total = sum(att.lines, x => cents(x.artwork_cents, 'attributed amount')) + sum(att.shipments, x => cents(x.cents, 'attributed amount'));
    if (total !== amount) throw new R.RuleError('The attribution must add up to the disputed amount');
  } else {
    const parts = [...remainingLines.map(x => ({ k: 'l', id: x.line_id, w: x.left })), ...remainingShips.map(x => ({ k: 's', id: x.shipment_id, w: x.left }))];
    const split = apportion(amount, parts.map(x => x.w));
    att = { lines: [], shipments: [] };
    parts.forEach((x, i) => { if (!split[i]) return; if (x.k === 'l') att.lines.push({ line_id: x.id, artwork_cents: split[i] }); else att.shipments.push({ shipment_id: x.id, cents: split[i] }); });
  }

  const d = p.decisions;
  // the refund calculation is used for attribution checks and per-artist amounts even when PlotArt carries the loss
  const asRefund = refund(p, S, att);
  const perArtist = asRefund.artists.map(a => a.artist_id);
  const attributed = perArtist.map(aid => sum(asRefund.lines.filter(l => l.artist_id === aid), l => l.artwork_refund_cents) + sum(asRefund.shipments.filter(s => s.artist_id === aid), s => s.refund_cents));
  const feeShares = d.dispute_fee_bearer === 'artists_by_line' ? apportion(fee, attributed) : perArtist.map(() => 0);
  const lossDebits = d.dispute_loss_bearer === 'artists_by_line' ? asRefund.artists.map(a => a.debit_cents) : perArtist.map(() => 0);
  const parts = perArtist.map((aid, i) => ({ artist_id: aid, artist_debit_cents: lossDebits[i] + feeShares[i] }));
  const artists = recover(p, S, parts).map((a, i) => ({ ...a, loss_cents: lossDebits[i], dispute_fee_cents: feeShares[i] }));
  const recovered = sum(artists, a => a.debit_cents);
  const platformCost = amount + fee - recovered;
  invariant(platformCost >= 0, 'artists would be charged more than the dispute cost');
  return freeze({ outcome, amount_cents: amount, fee_cents: fee, attribution: att, artists, platform_cost_cents: platformCost,
    commission_returned_cents: d.dispute_loss_bearer === 'artists_by_line' ? asRefund.commission_returned_cents : 0,
    lines: asRefund.lines, shipments: asRefund.shipments, shortfall_cents: sum(artists, a => a.shortfall_cents) });
}

/* ---------------------------------------------------------------- entitlements (read-only, existing rule) */
/* Resolve each line's commission entitlement with the EXISTING rule (checkout-rules.entitlement), one line at a time.
   requests: [{ line_id, artist, enquiry_ref, exclusion?, negotiation_note? }] where `artist` is the artists row.
   Only basket_introduction = logged_enquiry_only is implemented: a line without a logged introduction is blocked. The
   result per line is passed unchanged as that line's `entitlement` to plan(). */
export async function lineEntitlements(env, requests, decisionsInput, { at, resolve = R.entitlement } = {}) {
  const d = decisions(decisionsInput);
  if (typeof at !== 'string' || !Number.isFinite(Date.parse(at))) throw new R.RuleError('The time of the basket quote is required');
  const out = {};
  for (const q of requests) {
    const lid = id(q.line_id, 'Line id');
    if (d.basket_introduction === 'logged_enquiry_only' && !(typeof q.enquiry_ref === 'string' && q.enquiry_ref.trim())) {
      out[lid] = { ok: false, reason: 'No PlotArt introduction is named for this line. A basket line needs a logged introduction (founder decision basket_introduction).' };
      continue;
    }
    out[lid] = await resolve(env, { artist: q.artist, enquiryRef: q.enquiry_ref.trim(), at, exclusion: q.exclusion ?? null, negotiationNote: q.negotiation_note ?? null });
  }
  return out;
}

function assertPlan(p) {
  if (!p || p.version !== PLAN_VERSION || !Object.isFrozen(p)) throw new R.RuleError('A basket plan from plan() is required');
}
