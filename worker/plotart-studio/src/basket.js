/* PlotArt · multi-artist basket on the managed checkout (development 21 Nov 2026). NOT DEPLOYED. TEST MODE ONLY.
   OFF BY DEFAULT (BASKET_ENABLED and the pilot switch must both be on; live mode also needs approved basket texts).

   ONE checkout architecture. Every artwork in a basket is an ordinary checkout_orders row (checkout.js), with its own
   reference, seller snapshot, commission entitlement, delivery, ledger, refunds, disputes and confirmation; it is paid
   by a DIRECT CHARGE on its artist's own Stripe account (the artist is the seller and merchant of record; PlotArt's
   commission is the application fee). This module only coordinates the payments of several such orders:

     1 · the buyer's basket is priced from the database (never from the browser), every artwork is checked as available
         and reserved in ONE database transaction, and the orders are created;
     2 · the buyer enters their card ONCE, on Stripe-hosted Checkout in setup mode on PlotArt's account;
     3 · for each order the card is cloned to the artist's account and the charge is AUTHORISED (manual capture);
     4 · if any authorisation is declined, every authorisation already made is CANCELLED and the artworks are released;
         if a bank asks for extra authentication, the buyer completes it for that artist's payment within a deadline;
     5 · only when EVERY line is authorised are they captured; each captured charge is recorded through the existing
         recordPaid (sale, ledger, sold mark, confirmation, fee reimbursement). The basket is "paid" only when every line
         is captured and recorded.
   Coordination is resumable: driven by the buyer's return, signed webhooks and the scheduled sweep, one coordinator at a
   time (a lease), and every Stripe call has an idempotency key, so a retry never charges twice.
   Proven against Stripe TEST mode in the isolated POC (run 44930999959, 21 PASS / 0 FAIL). */
import * as C from './checkout.js';
import * as R from './checkout-rules.js';
import * as S from './stripe.js';
import { foundingAt } from './founding.js';
import { basketDoc, ARTIST_STATEMENT, BASKET_DECISIONS, PROCESSING_CONSENT_STATEMENT, SELLER_DISCLOSURE_STATEMENT } from './basket-terms.js';
import { Bad } from './lib.js';

export const MAX_LINES = 10;
export const SETUP_MINUTES = 31;          // Stripe's minimum hosted-page lifetime is 30 minutes
export const HOLD_GRACE_MINUTES = 15;     // reservations outlive the page while its completion event arrives
export const LEASE_SECONDS = 60;
export const MAX_ATTEMPTS = 3;            // transient Stripe errors per line before the basket is cancelled
const ACTIVE = ['open', 'authorising', 'action_required', 'capturing'];
const ENDED = ['paid', 'failed', 'expired', 'cancelled', 'needs_resolution'];

const now = () => new Date().toISOString();
const addMin = (iso, m) => new Date(Date.parse(iso) + m * 60_000).toISOString();
const rid = (p = '', n = 12) => p + [...crypto.getRandomValues(new Uint8Array(n))].map(b => (b % 36).toString(36)).join('');
const sha256 = async s => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)))].map(b => b.toString(16).padStart(2, '0')).join('');
const all = async (env, sql, ...b) => (await env.DB.prepare(sql).bind(...b).all()).results;
const one = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).first();
const run = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).run();
const st = (env, sql, ...b) => env.DB.prepare(sql).bind(...b);
const J = s => (s ? JSON.parse(s) : null);
const live = env => { const m = S.stripeMode(env); return !!(m.ok && m.live); };

/* ---------------------------------------------------------------- switches and texts */
export async function installed(env) { try { await env.DB.prepare('SELECT 1 FROM checkout_baskets LIMIT 1').all(); return await C.installed(env); } catch { return false; } }
export function enabled(env) { return C.switches(env).enabled && env.BASKET_ENABLED === 'true'; }
async function requireOpen(env) {
  if (!(await installed(env))) throw new Bad('Online purchase is not available', 404);
  if (!enabled(env)) throw new Bad('Online purchase is not open at the moment. Please enquire about the work instead.', 503);
  if (!env.CHECKOUT_ORIGIN) throw new Bad('Online purchase is not configured', 503);
  if ((await C.pauseState(env)).paused) throw new Bad(C.BUYER_PAUSED, 409);
}
export async function currentDoc(env, kind) {
  const d = await one(env, 'SELECT * FROM basket_terms WHERE kind = ? AND effective_at <= ? ORDER BY effective_at DESC LIMIT 1', kind, now());
  if (!d) return null;
  const t = await basketDoc(d.doc_id, live(env));
  return t && t.html_sha256 === d.html_sha256 && t.kind === kind ? { ...d, html: t.html } : null;
}
export function commissionFreePolicy(env) {
  if (live(env)) return BASKET_DECISIONS.commission_free_lines_live;
  return env.BASKET_COMMISSION_FREE === 'with_processing_consent' ? 'with_processing_consent' : BASKET_DECISIONS.commission_free_lines_test_default;
}

/* ---------------------------------------------------------------- artist: basket opt-in and delivery offers */
export async function artistMembership(env, artistId) {
  const ev = await one(env, 'SELECT * FROM basket_artist_events WHERE artist_id = ? ORDER BY at DESC, rowid DESC LIMIT 1', artistId);
  const doc = await currentDoc(env, 'artist_basket_addendum');
  const m = { opted_in: !!ev && ev.kind === 'opted_in', doc_id: ev && ev.kind === 'opted_in' ? ev.doc_id : null, current: !!doc && !!ev && ev.kind === 'opted_in' && ev.doc_id === doc.doc_id, at: ev ? ev.at : null };
  /* the separate consents (migration 0020). A consent counts only in the Stripe mode it was given in; the processing consent
     only for the basket addendum the artist currently has accepted; the disclosure only for the seller information it saw. */
  const lm = live(env) ? 1 : 0, last = async topic => consentsInstalled(env).then(ok => ok ? one(env, 'SELECT * FROM basket_consents WHERE artist_id = ? AND topic = ? AND livemode = ? ORDER BY at DESC, rowid DESC LIMIT 1', artistId, topic, lm) : null);
  const pc = await last('processing_fees'), sd = await last('seller_disclosure');
  const prof = await C.sellerProfile(env, artistId), profSha = prof ? await sellerHash(prof) : null;
  m.processing_consent = { given: !!pc && pc.kind === 'given', id: pc && pc.kind === 'given' ? pc.id : null, doc_id: pc && pc.kind === 'given' ? pc.doc_id : null, at: pc ? pc.at : null,
    valid: !!pc && pc.kind === 'given' && m.current && pc.doc_id === m.doc_id };
  m.seller_disclosure = { given: !!sd && sd.kind === 'given', id: sd && sd.kind === 'given' ? sd.id : null, at: sd ? sd.at : null,
    valid: !!sd && sd.kind === 'given' && !!profSha && sd.subject_sha256 === profSha, changed_since: !!sd && sd.kind === 'given' && sd.subject_sha256 !== profSha };
  return m;
}
async function consentsInstalled(env) { try { await env.DB.prepare('SELECT 1 FROM basket_consents LIMIT 1').all(); return true; } catch { return false; } }
/* exactly what the buyer is shown before payment; any change needs the artist to confirm again */
const SELLER_KEYS = ['legal_name', 'trading_name', 'address', 'returns_address', 'email', 'phone', 'vat_number'];
const sellerHash = p => sha256(JSON.stringify(SELLER_KEYS.map(k => p[k] ?? null)));

/* the artist's separate consents: give and withdraw (append-only records) */
async function consentInsert(env, artist, topic, kind, extra = {}) {
  if (!(await consentsInstalled(env))) throw new Bad('Basket consents are not installed (migration 0020)', 409);
  const statement = extra.statement || null;
  await run(env, `INSERT INTO basket_consents (id, artist_id, topic, kind, doc_id, doc_sha256, subject_sha256, statement, statement_sha256, account_email, livemode, at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`,
    rid('bc'), artist.id, topic, kind, extra.doc_id || null, extra.doc_sha256 || null, extra.subject_sha256 || null, statement, statement ? await sha256(statement) : null, artist.email, live(env) ? 1 : 0, now());
}
export async function artistProcessingConsent(env, artist, b) {
  const m = await artistMembership(env, artist.id), doc = await currentDoc(env, 'artist_basket_addendum');
  if (!m.current || !doc) throw new Bad('Accept the current basket addendum first', 409);
  const statement = PROCESSING_CONSENT_STATEMENT(doc.doc_id);
  if (!b || b.accept !== true || b.statement !== statement) throw new Bad('Tick the box beside the statement shown to give this separate consent', 400);
  if (m.processing_consent.valid) return { already: true, membership: m };
  await consentInsert(env, artist, 'processing_fees', 'given', { doc_id: doc.doc_id, doc_sha256: doc.html_sha256, statement });
  return { membership: await artistMembership(env, artist.id) };
}
export async function artistWithdrawProcessingConsent(env, artist) {
  const m = await artistMembership(env, artist.id);
  if (!m.processing_consent.given) return { membership: m };
  await consentInsert(env, artist, 'processing_fees', 'withdrawn');
  return { membership: await artistMembership(env, artist.id), note: 'Your commission-free artworks are no longer offered in the basket. Baskets already being paid are completed.' };
}
export async function artistSellerDisclosure(env, artist, b) {
  const m = await artistMembership(env, artist.id);
  if (!m.opted_in) throw new Bad('Accept the basket addendum first', 409);
  const prof = await C.sellerProfile(env, artist.id);
  if (!prof || C.sellerProblems(env, prof).length) throw new Bad('Complete your seller information first', 409);
  if (!b || b.accept !== true || b.statement !== SELLER_DISCLOSURE_STATEMENT || b.subject_sha256 !== await sellerHash(prof)) throw new Bad('Tick the box to confirm the seller information shown', 400);
  if (m.seller_disclosure.valid) return { already: true, membership: m };
  await consentInsert(env, artist, 'seller_disclosure', 'given', { subject_sha256: await sellerHash(prof), statement: SELLER_DISCLOSURE_STATEMENT });
  return { membership: await artistMembership(env, artist.id) };
}
export async function artistWithdrawSellerDisclosure(env, artist) {
  const m = await artistMembership(env, artist.id);
  if (!m.seller_disclosure.given) return { membership: m };
  await consentInsert(env, artist, 'seller_disclosure', 'withdrawn');
  return { membership: await artistMembership(env, artist.id), note: 'Your artworks are no longer offered in the basket. Baskets already being paid are completed.' };
}
/* what the buyer sees in "Seller and returns information": the legally required seller details only (VAT only if registered) */
const sellerInfo = p => Object.fromEntries(Object.entries({ legal_name: p.legal_name, trading_name: p.trading_name, address: p.address,
  returns_address: p.returns_address && p.returns_address !== p.address ? p.returns_address : null, email: p.email, phone: p.phone, vat_number: p.vat_number, trader: p.trader_status === 'trader' }).filter(([, v]) => v));
const PARTY = { buyer: 'you', artist: 'the artist', transporter: 'the transporter' };
const returnsInfo = d => ({ method: d.return_method, address: d.return_address, arranged_by: PARTY[d.return_arranged_by] || d.return_arranged_by,
  cost_cents: d.return_cost_cents, cost_basis: d.return_cost_basis });
export async function artistView(env, artist) {
  if (!(await installed(env))) return { installed: false };
  const doc = await currentDoc(env, 'artist_basket_addendum');
  const works = await all(env, `SELECT w.id, w.title, w.price_eur, w.price_on_request, w.availability, o.delivery_cents, o.version, o.approved_at, o.withdrawn_at, o.delivery
    FROM artworks w LEFT JOIN artwork_delivery_offers o ON o.artwork_id = w.id WHERE w.artist_id = ? AND w.archived = 0 ORDER BY w.ord`, artist.id);
  return { installed: true, enabled: enabled(env), addendum: doc ? { doc_id: doc.doc_id, title: doc.title, html_sha256: doc.html_sha256, statement: ARTIST_STATEMENT(doc.doc_id) } : null,
    membership: await artistMembership(env, artist.id), pilot: await C.membership(env, artist.id), commission_free_policy: commissionFreePolicy(env),
    processing_statement: doc ? PROCESSING_CONSENT_STATEMENT(doc.doc_id) : null, disclosure_statement: SELLER_DISCLOSURE_STATEMENT,
    seller_info: await C.sellerProfile(env, artist.id).then(async p => p ? { shown: sellerInfo(p), subject_sha256: await sellerHash(p) } : null),
    founding: !!artist.founding, delivery_fields: R.DELIVERY_FIELDS, parties: R.PARTIES,
    works: await Promise.all(works.map(async ({ delivery, ...w }) => ({ ...w, offer: w.approved_at && !w.withdrawn_at
      ? { delivery_cents: w.delivery_cents, version: w.version, approved_at: w.approved_at, delivery: J(delivery), review: artistReviewView(await offerReview(env, { artwork_id: w.id, version: w.version, delivery_cents: w.delivery_cents, delivery })) } : null }))) };
}
export async function artistOptIn(env, artist, b) {
  if (!(await installed(env))) throw new Bad('Baskets are not installed (migration 0019)', 409);
  const doc = await currentDoc(env, 'artist_basket_addendum');
  if (!doc) throw new Bad('The basket addendum has not been issued yet', 409);
  if (!b || b.accept !== true || b.doc_id !== doc.doc_id || b.html_sha256 !== doc.html_sha256) throw new Bad('Tick the box to accept the basket addendum shown', 400);
  if (!(await C.membership(env, artist.id)).opted_in) throw new Bad('Join the payment pilot first', 409);
  const m = await artistMembership(env, artist.id);
  if (m.current) return { already: true, membership: m };
  await run(env, `INSERT INTO basket_artist_events (id, artist_id, kind, doc_id, doc_sha256, account_email, statement, at) VALUES (?,?, 'opted_in', ?,?,?,?,?)`,
    rid('be'), artist.id, doc.doc_id, doc.html_sha256, artist.email, ARTIST_STATEMENT(doc.doc_id), now());
  return { membership: await artistMembership(env, artist.id) };
}
export async function artistLeave(env, artist) {
  const m = await artistMembership(env, artist.id);
  if (!m.opted_in) return { membership: m };
  await run(env, `INSERT INTO basket_artist_events (id, artist_id, kind, account_email, at) VALUES (?,?, 'left', ?, ?)`, rid('be'), artist.id, artist.email, now());
  return { membership: await artistMembership(env, artist.id), note: 'Baskets already paid or being paid continue; your works are no longer offered for online purchase.' };
}
/* The artist's standing delivery offer for one artwork: every field of a quoted delivery, approved by the artist, for
   delivery anywhere in the Republic of Ireland (the buyer's address is completed on each order). */
export async function setDeliveryOffer(env, artist, artworkId, b) {
  if (!(await installed(env))) throw new Bad('Baskets are not installed (migration 0019)', 409);
  const w = await one(env, 'SELECT * FROM artworks WHERE id = ? AND artist_id = ?', artworkId, artist.id);
  if (!w || w.archived) throw new Bad('That artwork is not yours', 404);
  if (!b || b.confirm !== true) throw new Bad('Confirm that you will deliver this artwork as described, anywhere in the Republic of Ireland, for this price', 400);
  const cents = b.delivery_cents;
  if (!Number.isInteger(cents) || cents < 0 || cents > R.MAX_DELIVERY_CENTS) throw new Bad(`Give the delivery charge in whole euro cents (0 to ${R.MAX_DELIVERY_CENTS})`, 400);
  const islands = !!(b.delivery && b.delivery.offshore_islands === true);
  const d = R.cleanDelivery({ ...b.delivery, offshore_islands: islands, destination_country: 'IE', destination: islands
    ? 'Anywhere in the Republic of Ireland, including offshore islands (the buyer’s address is given at checkout)'
    : 'Anywhere on the mainland of the Republic of Ireland; offshore islands by enquiry (the buyer’s address is given at checkout)' });
  R.checkDeadlines(d);
  if (w.price_eur) R.checkCover(d, w.price_eur * 100);
  const ret = R.returnProblems(d);
  if (ret.length) throw new Bad(`Give the return arrangements: ${ret.join('; ')}`, 400);
  const t = now(), cur = await one(env, 'SELECT version FROM artwork_delivery_offers WHERE artwork_id = ?', w.id);
  await run(env, `INSERT INTO artwork_delivery_offers (artwork_id, artist_id, region, delivery_cents, delivery, version, approved_by, approved_at, withdrawn_at, created_at, updated_at)
    VALUES (?,?, 'IE', ?,?, 1, ?,?, NULL, ?,?) ON CONFLICT(artwork_id) DO UPDATE SET delivery_cents = excluded.delivery_cents, delivery = excluded.delivery,
    version = artwork_delivery_offers.version + 1, approved_by = excluded.approved_by, approved_at = excluded.approved_at, withdrawn_at = NULL, updated_at = excluded.updated_at`,
    w.id, artist.id, cents, JSON.stringify(d), 'artist:' + artist.email, t, t, t);
  const version = (cur ? cur.version : 0) + 1;
  await offerEvent(env, { artwork_id: w.id, artist_id: artist.id, kind: 'saved', version, sha: await offerSha({ artwork_id: w.id, version, delivery_cents: cents, delivery: d }), actor: 'artist:' + artist.email });
  // a new version is never approved: the founder reviews it before the artwork can be bought online (delivery safety, 22 Nov 2026)
  return { artwork_id: w.id, delivery_cents: cents, version, review: 'awaiting_founder_review' };
}
export async function withdrawDeliveryOffer(env, artist, artworkId) {
  const r = await run(env, 'UPDATE artwork_delivery_offers SET withdrawn_at = ?, updated_at = ? WHERE artwork_id = ? AND artist_id = ? AND withdrawn_at IS NULL', now(), now(), artworkId, artist.id);
  if (r.meta.changes) { const o = await one(env, 'SELECT version FROM artwork_delivery_offers WHERE artwork_id = ?', artworkId); await offerEvent(env, { artwork_id: artworkId, artist_id: artist.id, kind: 'withdrawn', version: o.version, sha: null, actor: 'artist:' + artist.email }); }
  return { withdrawn: !!r.meta.changes };
}

/* ---------------------------------------------------------------- delivery safety (22 Nov 2026): founder review of each delivery offer
   An artwork is offered in the basket only while the founder's LATEST review of its delivery offer approves the CURRENT version
   and the exact content (a fingerprint of the charge and every delivery field). Any change the artist saves is a new version,
   so an earlier approval stops counting until the founder reviews again. Reviews are append-only (migration 0022); without
   that migration nothing is approved and every artwork stays enquiry-only. */
export const DELIVERY_SCOPE = 'Online purchase delivers to addresses in the Republic of Ireland only. Offshore islands only where an artwork’s delivery offer includes them. For delivery anywhere else, please enquire about the artwork.';
export const REVIEW_STATEMENT = 'I have reviewed this exact delivery offer. The delivery charge, transit insurance, dispatch and delivery deadlines and return arrangements are complete and realistic for this artwork, and it may be bought online on these terms.';
const canon = v => Array.isArray(v) ? `[${v.map(canon).join(',')}]` : v && typeof v === 'object' ? `{${Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + canon(v[k])).join(',')}}` : JSON.stringify(v ?? null);
export async function offerSha(o) {
  const d = typeof o.delivery === 'string' ? JSON.parse(o.delivery) : o.delivery;
  return sha256(canon({ artwork_id: o.artwork_id, version: o.version, delivery_cents: o.delivery_cents, delivery: d }));
}
async function reviewsInstalled(env) { try { await env.DB.prepare('SELECT 1 FROM delivery_offer_reviews LIMIT 1').all(); return true; } catch { return false; } }
export async function offerReview(env, o) {
  let r = null;
  try { r = await one(env, 'SELECT * FROM delivery_offer_reviews WHERE artwork_id = ? ORDER BY reviewed_at DESC, rowid DESC LIMIT 1', o.artwork_id); }
  catch { return { approved: false, state: 'not_installed' }; }
  if (!r || o.withdrawn_at) return { approved: false, state: 'awaiting_review' };
  const current = r.offer_version === o.version && r.offer_sha256 === await offerSha(o);
  if (!current) return { approved: false, state: 'awaiting_review', previous: { decision: r.decision, version: r.offer_version, at: r.reviewed_at } };
  if (r.decision === 'returned') return { approved: false, state: 'returned', note: r.note, at: r.reviewed_at, by: r.reviewed_by, id: r.id };
  if (live(env) && !r.livemode) return { approved: false, state: 'awaiting_review' };   // a test-mode review never opens live purchase
  return { approved: true, state: 'approved', at: r.reviewed_at, by: r.reviewed_by, id: r.id, note: r.note };
}
const artistReviewView = r => ({ state: r.state, at: r.at || null, note: r.state === 'returned' ? r.note : null,
  text: r.state === 'approved' ? 'Reviewed and approved by PlotArt' : r.state === 'returned' ? 'Returned by PlotArt: change the offer and save it again' : 'Waiting for PlotArt to review it' });
async function offerEvent(env, { artwork_id, artist_id, kind, version, sha, actor }) {
  try { await run(env, 'INSERT INTO delivery_offer_events (id, artwork_id, artist_id, kind, offer_version, offer_sha256, actor, at) VALUES (?,?,?,?,?,?,?,?)', rid('de'), artwork_id, artist_id, kind, version, sha, actor, now()); }
  catch { /* migration 0022 not applied: the offer itself still records who approved it and when */ }
}
/* Founder: every current delivery offer with its review state; those waiting first. */
export async function adminOffers(env) {
  if (!(await installed(env))) return { installed: false, offers: [] };
  const ok = await reviewsInstalled(env);
  const rows = await all(env, `SELECT o.*, w.title, w.price_eur, w.availability, a.display_name FROM artwork_delivery_offers o JOIN artworks w ON w.id = o.artwork_id
    JOIN artists a ON a.id = o.artist_id WHERE o.withdrawn_at IS NULL AND w.archived = 0 ORDER BY o.updated_at DESC`);
  const offers = [];
  for (const o of rows) {
    const d = J(o.delivery) || {}, rv = await offerReview(env, o), problems = [];
    try { R.checkCover(d, (o.price_eur || 0) * 100); } catch (e) { problems.push(e.message); }
    problems.push(...R.returnProblems(d).map(x => 'missing: ' + x));
    if (R.deliveryDeadlines(d).basis !== 'agreed') problems.push('no dispatch and delivery deadlines (the artist must save the offer again)');
    if (!o.price_eur) problems.push('the artwork has no price');
    offers.push({ artwork_id: o.artwork_id, title: o.title, artist: o.display_name, artist_id: o.artist_id, price_eur: o.price_eur, availability: o.availability,
      version: o.version, sha256: await offerSha(o), delivery_cents: o.delivery_cents, delivery: d, saved_by: o.approved_by, saved_at: o.approved_at, review: rv, problems,
      history: ok ? await all(env, `SELECT 'review' AS type, decision AS what, offer_version AS version, reviewed_by AS who, reviewed_at AS at, note FROM delivery_offer_reviews WHERE artwork_id = ?
        UNION ALL SELECT 'artist', kind, offer_version, actor, at, NULL FROM delivery_offer_events WHERE artwork_id = ? ORDER BY at DESC LIMIT 12`, o.artwork_id, o.artwork_id) : [] });
  }
  offers.sort((x, y) => (x.review.approved - y.review.approved) || 0);
  return { installed: true, reviews_installed: ok, statement: REVIEW_STATEMENT, waiting: offers.filter(x => x.review.state === 'awaiting_review').length, offers };
}
/* Founder: approve or return ONE exact offer version (the version and fingerprint the founder was shown). */
export async function reviewOffer(env, founder, artworkId, b) {
  if (!(await installed(env)) || !(await reviewsInstalled(env))) throw new Bad('Delivery offer reviews are not installed (migration 0022)', 409);
  const o = await one(env, 'SELECT o.*, w.price_eur FROM artwork_delivery_offers o JOIN artworks w ON w.id = o.artwork_id WHERE o.artwork_id = ? AND o.withdrawn_at IS NULL', artworkId);
  if (!o) throw new Bad('No current delivery offer for that artwork', 404);
  const decision = b && b.decision;
  if (!['approved', 'returned'].includes(decision)) throw new Bad('Choose approve or return', 400);
  if (b.version !== o.version || b.sha256 !== await offerSha(o)) throw new Bad('The artist changed this delivery offer since you opened it. Reload and review the current version.', 409);
  const note = String(b.note || '').trim();
  if (note.length > 600) throw new Bad('Note: up to 600 characters', 400);
  if (decision === 'returned' && note.length < 3) throw new Bad('Say what the artist should change', 400);
  if (decision === 'approved') {
    if (b.confirm !== true || b.statement !== REVIEW_STATEMENT) throw new Bad('Tick the box to confirm your review', 400);
    const d = J(o.delivery) || {};
    if (!o.price_eur) throw new Bad('The artwork has no price: it cannot be bought online', 409);
    R.checkCover(d, o.price_eur * 100);
    const ret = R.returnProblems(d); if (ret.length) throw new Bad(`Return arrangements missing: ${ret.join('; ')}`, 409);
    if (R.deliveryDeadlines(d).basis !== 'agreed') throw new Bad('This offer has no dispatch and delivery deadlines: return it to the artist', 409);
  }
  const id = rid('dr');
  await run(env, `INSERT INTO delivery_offer_reviews (id, artwork_id, artist_id, offer_version, offer_sha256, decision, note, reviewed_by, reviewed_at, livemode) VALUES (?,?,?,?,?,?,?,?,?,?)`,
    id, o.artwork_id, o.artist_id, o.version, b.sha256, decision, note || null, 'founder:' + founder, now(), live(env) ? 1 : 0);
  return { id, artwork_id: o.artwork_id, version: o.version, decision, ...(await adminOffers(env)) };
}

/* ---------------------------------------------------------------- eligibility: one artwork, from the records only */
const PUBLIC_REASON = {
  unavailable: 'This artwork is no longer available.',
  busy: 'Someone else is completing a purchase of this artwork right now. Please try again later.',
  enquire: 'This artwork can’t be bought online. Please enquire about it instead.',
  price: 'The price of this artwork is being updated. Please try again later.',
};
async function lineFor(env, artworkId, at) {
  const no = (code, why) => ({ ok: false, code, reason: PUBLIC_REASON[code], why });
  const w = await one(env, 'SELECT * FROM artworks WHERE id = ?', artworkId);
  if (!w || w.archived) return no('unavailable', 'unknown or archived');
  const artist = await one(env, 'SELECT * FROM artists WHERE id = ?', w.artist_id);
  if (!artist || artist.account_status !== 'active') return no('unavailable', 'artist not active');
  const pw = await C.publishedWork(env, artist.id, w.id);
  if (!pw || pw.availability !== 'available' || w.availability !== 'available') return no('unavailable', 'not published as available');
  if (await one(env, 'SELECT 1 AS x FROM artwork_sales WHERE artwork_id = ? AND released_at IS NULL', w.id)) return no('unavailable', 'sold');
  if (w.price_on_request || !Number.isInteger(w.price_eur) || w.price_eur <= 0) return no('enquire', 'price on request');
  if (pw.price_eur !== w.price_eur) return no('price', 'published price differs from the Studio');
  const artworkCents = w.price_eur * 100;
  if (artworkCents > R.MAX_ARTWORK_CENTS) return no('enquire', 'above the pilot price limit');
  if (await one(env, 'SELECT 1 AS x FROM artwork_reservations WHERE artwork_id = ? AND expires_at > ?', w.id, at)) return no('busy', 'reserved');
  if (await one(env, `SELECT 1 AS x FROM checkout_orders WHERE artwork_id = ? AND status IN ('quoted','checkout_open','payment_failed') AND quote_expires_at > ?`, w.id, at)) return no('busy', 'an issued quote is open');
  const mem = await C.membership(env, artist.id), bm = await artistMembership(env, artist.id);
  const add = await C.currentTerms(env, 'artist_payment_addendum');
  if (!mem.ready || !add || mem.addendum !== add.doc_id || !bm.current) return no('enquire', 'artist not ready for online purchase');
  // completed Stripe onboarding in THIS mode (mem.ready checks the mode, charges and details): payouts too
  if (!mem.account || !mem.account.payouts_enabled) return no('enquire', 'Stripe onboarding incomplete (payouts)');
  const prof = await C.sellerProfile(env, artist.id);
  if (C.sellerProblems(env, prof).length) return no('enquire', 'seller information incomplete');
  if (!bm.seller_disclosure.valid) return no('enquire', bm.seller_disclosure.changed_since ? 'seller information changed since the artist confirmed it may be shown' : 'artist has not confirmed seller information may be shown before payment');
  const offer = await one(env, 'SELECT * FROM artwork_delivery_offers WHERE artwork_id = ? AND withdrawn_at IS NULL', w.id);
  if (!offer) return no('enquire', 'no delivery offer');
  const delivery = J(offer.delivery);
  try { R.checkCover(delivery, artworkCents); } catch { return no('enquire', 'delivery cover below the price'); }
  if (R.returnProblems(delivery).length) return no('enquire', 'return arrangements missing');
  if (R.deliveryDeadlines(delivery).basis !== 'agreed') return no('enquire', 'delivery offer has no dispatch and delivery deadlines');
  const review = await offerReview(env, offer);
  if (!review.approved) return no('enquire', review.state === 'returned' ? 'delivery offer returned by the founder' : 'delivery offer awaiting founder approval');
  const f = foundingAt(artist, at);
  const intro = { reference: null, route: 'online_basket', introduced_at: at, founding: f.founding, founding_year_end: f.year_end };
  const e = await R.entitlementForIntro(env, { artist, intro, at });
  if (!e.ok) return no('enquire', e.reason);
  if (e.bp === 0 && commissionFreePolicy(env) !== 'with_processing_consent') return no('enquire', 'commission-free: direct payment (policy)');
  if (e.bp === 0 && !bm.processing_consent.valid) return no('enquire', 'commission-free: no valid processing-fee consent');
  const money = R.amounts({ artwork_cents: artworkCents, delivery_cents: offer.delivery_cents, commission_bp: e.bp });
  return { ok: true, artist, work: w, pw, prof, mem, bm, offer, delivery, review, entitlement: e, money };
}
const artworkUrl = (env, artist, w) => env.STAGING_GALLERY === 'true' && ['staging', 'test', 'local'].includes(env.ENVIRONMENT) ? `${env.STAGING_GALLERY_URL || '/gallery'}/${w.id}` : `${env.GALLERY_ORIGIN || 'https://plotnua.ie'}/plotart/artists/${artist.slug}/${w.slug}.html`;
const deliverySummary = d => ({ islands: d.offshore_islands === true, dispatch_days: d.dispatch_days, delivery_days: d.delivery_days, window: d.delivery_window, transporter: d.transporter_name, tracking: d.tracking, cover: `${d.cover_provider}, up to €${(d.covered_value_cents / 100).toFixed(2)}`,
  from: d.collection_county, returns: d.return_cost_basis === 'fixed' ? `Return cost if you change your mind: €${(d.return_cost_cents / 100).toFixed(2)}` : `Return cost if you change your mind: up to about €${(d.return_cost_cents / 100).toFixed(2)}` });

/* What the basket page shows for each artwork: live availability, the seller, price and delivery (nothing internal). */
export async function preview(env, ids) {
  if (!(await installed(env))) return { open: false, items: [] };
  const at = now(), list = [...new Set((ids || []).map(String).filter(x => /^[A-Za-z0-9_-]{1,64}$/.test(x)))].slice(0, MAX_LINES);
  const items = [];
  for (const id of list) {
    const l = await lineFor(env, id, at);
    if (!l.ok) {
      const w = await one(env, 'SELECT a.display_name, w.title FROM artworks w JOIN artists a ON a.id = w.artist_id WHERE w.id = ?', id);
      items.push({ id, ok: false, reason: l.reason, title: w ? w.title : null, artist: w ? w.display_name : null }); continue;
    }
    items.push({ id, ok: true, title: l.work.title, year: l.work.year, medium: l.work.medium, size: l.work.h_cm ? `${l.work.h_cm} × ${l.work.w_cm}${l.work.d_cm ? ' × ' + l.work.d_cm : ''} cm` : null,
      artist: l.artist.display_name, artist_id: l.artist.id, founding_artist: !!l.artist.founding, seller: l.prof.legal_name, seller_info: sellerInfo(l.prof), returns: returnsInfo(l.delivery), url: artworkUrl(env, l.artist, l.work),
      price_cents: l.money.artwork_cents, delivery_cents: l.money.delivery_cents, total_cents: l.money.total_cents, delivery: deliverySummary(l.delivery) });
  }
  const ok = items.filter(i => i.ok);
  const terms = await currentDoc(env, 'buyer_basket_terms');
  return { open: enabled(env) && !(await C.pauseState(env)).paused && !!terms, test_mode: !live(env), items, max_lines: MAX_LINES, delivery_scope: DELIVERY_SCOPE,
    totals: { artworks_cents: ok.reduce((a, i) => a + i.price_cents, 0), delivery_cents: ok.reduce((a, i) => a + i.delivery_cents, 0), total_cents: ok.reduce((a, i) => a + i.total_cents, 0) },
    terms: terms ? { doc_id: terms.doc_id, title: terms.title } : null };
}

/* ---------------------------------------------------------------- buyer: open a basket (atomic) and the hosted card page */
const COUNTIES = ['Carlow', 'Cavan', 'Clare', 'Cork', 'Donegal', 'Dublin', 'Galway', 'Kerry', 'Kildare', 'Kilkenny', 'Laois', 'Leitrim', 'Limerick', 'Longford', 'Louth', 'Mayo',
  'Meath', 'Monaghan', 'Offaly', 'Roscommon', 'Sligo', 'Tipperary', 'Waterford', 'Westmeath', 'Wexford', 'Wicklow'];
export { COUNTIES };
function cleanBuyer(b) {
  const s = (k, max, req = true) => { const v = String((b && b[k]) || '').trim(); if (req && !v) throw new Bad(`Please give your ${k.replace(/_/g, ' ')}`, 400); if (v.length > max) throw new Bad(`Your ${k.replace(/_/g, ' ')} is too long`, 400); return v || null; };
  const email = s('email', 254);
  if (!/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}$/.test(email)) throw new Bad('Please check your email address', 400);
  const county = s('county', 40);
  if (!COUNTIES.includes(county)) throw new Bad('Delivery is to the Republic of Ireland only: choose your county', 400);
  const eircode = s('eircode', 8, false);
  if (eircode && !/^[AC-FHKNPRTV-Y][0-9]{2}W? ?[0-9AC-FHKNPRTV-Y]{4}$/i.test(eircode)) throw new Bad('Please check your Eircode', 400);
  const phone = s('phone', 30);
  if (!/^[+0-9 ()-]{7,30}$/.test(phone)) throw new Bad('Please give a telephone number for the delivery', 400);
  const isl = String((b && b.island) || '');
  if (!['yes', 'no'].includes(isl)) throw new Bad('Please say whether the delivery address is on an offshore island', 400);
  const address = { line1: s('address_line1', 120), line2: s('address_line2', 120, false), town: s('town', 80), county, eircode: eircode ? eircode.toUpperCase() : null, phone };
  const named = R.islandMatch([address.line1, address.line2, address.town].filter(Boolean).join(' '));
  return { email, name: s('name', 120), address: { ...address, island: isl === 'yes' || !!named }, island: { declared: isl === 'yes', named } };
}
const addressLine = a => [a.line1, a.line2, a.town, 'Co. ' + a.county, a.eircode, 'Ireland'].filter(Boolean).join(', ');

export async function openBasket(env, b) {
  await requireOpen(env);
  const terms = await currentDoc(env, 'buyer_basket_terms');
  if (!terms) throw new Bad('Online purchase is not open at the moment. Please enquire about the work instead.', 503);
  if (!b || b.accept_terms !== terms.doc_id) throw new Bad('Please read and accept the purchase terms', 400);
  const ids = [...new Set((Array.isArray(b.artworks) ? b.artworks : []).map(String))];
  if (!ids.length) throw new Bad('Your basket is empty', 400);
  if (ids.length > MAX_LINES || !ids.every(x => /^[A-Za-z0-9_-]{1,64}$/.test(x))) throw new Bad(`A basket holds up to ${MAX_LINES} artworks`, 400);
  const buyer = cleanBuyer(b), t = now();
  const lines = [];
  for (const id of ids) {
    const l = await lineFor(env, id, t);
    if (!l.ok) { const e = new Bad(l.reason, 409); e.artwork = id; throw e; }
    lines.push(l);
  }
  // offshore islands (delivery safety, 22 Nov 2026): only artworks whose founder-approved offer covers islands can go there
  if (buyer.address.island) {
    const not = lines.find(l => l.delivery.offshore_islands !== true);
    if (not) { const e = new Bad(`${not.work.title} can’t be delivered to an offshore island through online purchase. Please remove it and enquire about it instead.`, 409); e.artwork = not.work.id; e.code = 'island'; throw e; }
  }
  // the client's view of the price must match the server's (a price that changed while the page was open is shown again)
  if (Number.isInteger(b.expected_total_cents) && b.expected_total_cents !== lines.reduce((a, l) => a + l.money.total_cents, 0))
    throw new Bad('A price in your basket has changed. Please review your basket before paying.', 409);
  const total = lines.reduce((a, l) => a + l.money.total_cents, 0);
  // linked-purchase safeguard, as for single quotes (operational only; not an AML assessment)
  const since = new Date(Date.now() - R.LINKED_WINDOW_DAYS * 86400_000).toISOString();
  const prior = await one(env, `SELECT COALESCE(SUM(artwork_cents + COALESCE(delivery_cents, 0)), 0) AS c FROM checkout_orders
    WHERE lower(buyer_email) = lower(?) AND created_at >= ? AND artwork_cents IS NOT NULL AND (payment_status <> 'none' AND payment_status <> 'failed' OR status IN ('quoted','checkout_open'))`, buyer.email, since);
  if (prior.c + total >= R.LINKED_THRESHOLD_CENTS) throw new Bad('This purchase can’t be completed online. Please contact hello@plotnua.ie.', 409);

  const id = rid('b'), token = rid('', 32) + rid('', 16), reference = `PA-B-${t.slice(2, 10).replace(/-/g, '')}-${rid('', 6).toUpperCase()}`;
  const expires = addMin(t, SETUP_MINUTES), hold = addMin(expires, HOLD_GRACE_MINUTES), lm = live(env) ? 1 : 0;
  const basket = { id, reference, line_count: lines.length, total_cents: total };
  const add = await C.currentTerms(env, 'artist_payment_addendum');
  const stmts = [
    // reservations that have lapsed (and are not held by an open single-artwork checkout) give way; a live one makes the INSERT below fail
    ...lines.map(l => st(env, `DELETE FROM artwork_reservations WHERE artwork_id = ? AND expires_at < ? AND order_id NOT IN (SELECT order_id FROM checkout_sessions WHERE status = 'open' AND expires_at >= ?)`, l.work.id, t, t)),
    st(env, `INSERT INTO checkout_baskets (id, reference, status, buyer_email, buyer_name, delivery_address, buyer_token_hash, terms_doc_id, terms_accepted_at, total_cents, line_count, expires_at, livemode, created_at, updated_at)
      VALUES (?,?, 'open', ?,?,?,?,?,?,?,?,?,?,?,?)`, id, reference, buyer.email, buyer.name, JSON.stringify(buyer.address), await sha256(token), terms.doc_id, t, total, lines.length, expires, lm, t, t),
    st(env, 'INSERT INTO basket_events (basket_id, at, actor, action, next, detail) VALUES (?,?,?,?,?,?)', id, t, 'buyer', 'opened', 'open', JSON.stringify({ lines: lines.length, total_cents: total, terms: terms.doc_id })),
  ];
  const orders = [];
  for (const [i, l] of lines.entries()) {
    const oid = rid('o'), oref = `PA-O-${t.slice(2, 10).replace(/-/g, '')}-${rid('', 6).toUpperCase()}`;
    const seller = { name: l.artist.display_name, legal_name: l.prof.legal_name, trading_name: l.prof.trading_name, address: l.prof.address, returns_address: l.prof.returns_address || l.prof.address,
      email: l.prof.email, phone: l.prof.phone, trader_status: l.prof.trader_status, vat_number: l.prof.vat_number, role: 'Seller (the artist)', stripe_account_country: l.mem.account.country,
      platform: 'PlotArt (PlotNua, Colin Macaulay) introduces and coordinates this sale. PlotArt is not the seller.', contact: 'hello@plotnua.ie' };
    const delivery = { ...l.delivery, destination_country: 'IE', destination: addressLine(buyer.address) + (buyer.address.island ? ' (offshore island)' : '') };
    const art = { title: l.work.title, year: l.work.year, medium: l.work.medium, materials: l.work.materials, h_cm: l.work.h_cm, w_cm: l.work.w_cm, d_cm: l.work.d_cm, listed_price_eur: l.work.price_eur };
    const snapshot = JSON.stringify({ schema: 1, reference: oref, basket: reference, quote_version: 1, issued_at: t, expires_at: hold, currency: 'EUR', seller, artwork: art,
      amounts: { artwork_cents: l.money.artwork_cents, delivery_cents: l.money.delivery_cents, total_cents: l.money.total_cents }, delivery: C.buyerDelivery(delivery), terms: { doc_id: terms.doc_id, html_sha256: terms.html_sha256 } });
    const snapSha = await sha256(snapshot);
    orders.push({ id: oid, reference: oref, line: l });
    stmts.push(
      st(env, `INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, payment_status, buyer_email, livemode, artwork_snapshot, artwork_cents, delivery_cents,
          commission_bp, commission_cents, commission_basis, entitlement, delivery, seller, quote_version, artist_approved_version, artist_approved_at, artist_confirmations, quote_issued_at,
          quote_expires_at, quote_sha256, addendum_doc_id, buyer_terms_doc_id, buyer_terms_accepted_at, provider_account, created_by, created_at, updated_at)
        VALUES (?,?,?,?,?, 'checkout_open', 'open', ?,?,?,?,?,?,?,?,?,?,?, 1, 1, ?,?,?,?,?,?,?,?,?, 'buyer:basket', ?,?)`,
        oid, oref, l.artist.id, l.work.id, reference, buyer.email, lm, JSON.stringify(art), l.money.artwork_cents, l.money.delivery_cents, l.entitlement.bp, l.money.commission_cents,
        l.entitlement.basis, JSON.stringify(l.entitlement.evidence), JSON.stringify(delivery), JSON.stringify(seller), l.offer.approved_at,
        JSON.stringify({ basis: 'standing_delivery_offer', offer_version: l.offer.version, approved_by: l.offer.approved_by, founder_review: l.review.id, founder_reviewed_by: l.review.by, basket_addendum: l.bm.doc_id,
          seller_disclosure_consent: l.bm.seller_disclosure.id, processing_fee_consent: l.entitlement.bp === 0 ? l.bm.processing_consent.id : null }),
        t, hold, snapSha, add ? add.doc_id : null, terms.doc_id, t, l.mem.account.id, t, t),
      st(env, 'INSERT INTO quote_snapshots (order_id, quote_version, snapshot, sha256, issued_at) VALUES (?,?,?,?,?)', oid, 1, snapshot, snapSha, t),
      // the reservation: the PRIMARY KEY on artwork_id makes a second concurrent purchase fail, and the whole batch with it
      st(env, 'INSERT INTO artwork_reservations (artwork_id, order_id, quote_version, expires_at, created_at) VALUES (?,?,?,?,?)', l.work.id, oid, 1, hold, t),
      st(env, `INSERT INTO basket_lines (order_id, basket_id, line_no, artist_id, account, amount_cents, fee_cents, state, updated_at) VALUES (?,?,?,?,?,?,?, 'pending', ?)`,
        oid, id, i + 1, l.artist.id, l.mem.account.id, l.money.total_cents, l.money.commission_cents, t),
      C.evSt(env, oid, 'buyer', 'basket_order_created', null, 'checkout_open', { basket: reference, line: i + 1, commission_basis: l.entitlement.basis, offer_version: l.offer.version }),
    );
  }
  try { await env.DB.batch(stmts); }
  catch (e) { if (/UNIQUE|constraint/i.test(String(e.message))) throw new Bad(PUBLIC_REASON.busy, 409); throw e; }

  // the buyer's card is entered once, on Stripe's page, on PlotArt's account
  try {
    const cus = await S.createCustomer(env, { idem: `plotart-basket-${id}-customer`, email: buyer.email, name: buyer.name, basket });
    await run(env, 'UPDATE checkout_baskets SET platform_customer = ?, updated_at = ? WHERE id = ?', cus.id, now(), id);
    const s = await S.createSetupSession(env, { idem: `plotart-basket-${id}-setup`, customer: cus.id, basket, expiresAt: expires,
      successUrl: `${env.CHECKOUT_ORIGIN}/b/${token}/return`, cancelUrl: `${env.CHECKOUT_ORIGIN}/b/${token}?cancelled=1` });
    await run(env, 'UPDATE checkout_baskets SET setup_session = ?, updated_at = ? WHERE id = ?', s.id, now(), id);
    await event(env, id, 'buyer', 'card_page_opened', 'open', 'open', { session: s.id });
    return { url: s.url, token, reference };
  } catch (e) {
    const bk = await basketRow(env, id);
    await endBasket(env, bk, 'cancelled', 'system', 'The card page could not be opened: ' + String(e.message || e).slice(0, 200));
    throw new Bad('Secure payment could not be opened. Nothing has been charged. Please try again in a moment.', 502);
  }
}

/* ---------------------------------------------------------------- the coordinator */
const basketRow = (env, id) => one(env, 'SELECT * FROM checkout_baskets WHERE id = ?', id);
const linesOf = (env, id) => all(env, 'SELECT * FROM basket_lines WHERE basket_id = ? ORDER BY line_no', id);
async function event(env, basketId, actor, action, prior, next, detail) {
  await run(env, 'INSERT INTO basket_events (basket_id, at, actor, action, prior, next, detail) VALUES (?,?,?,?,?,?,?)', basketId, now(), actor, action, prior || null, next || null, detail ? JSON.stringify(detail).slice(0, 4000) : null);
}
async function setStatus(env, b, to, actor, action, sets = {}, detail = null) {
  const keys = Object.keys(sets);
  const r = await run(env, `UPDATE checkout_baskets SET status = ?, ${keys.map(k => `${k} = ?, `).join('')}updated_at = ? WHERE id = ? AND status = ?`, to, ...keys.map(k => sets[k]), now(), b.id, b.status);
  if (!r.meta.changes) return null;
  await event(env, b.id, actor, action, b.status, to, detail);
  return { ...b, ...sets, status: to };
}
const setLine = (env, l, sets) => { const keys = Object.keys(sets); return run(env, `UPDATE basket_lines SET ${keys.map(k => `${k} = ?, `).join('')}updated_at = ? WHERE order_id = ?`, ...keys.map(k => sets[k]), now(), l.order_id); };
const extendHolds = (env, b, until) => [
  st(env, 'UPDATE artwork_reservations SET expires_at = ? WHERE order_id IN (SELECT order_id FROM basket_lines WHERE basket_id = ?) AND expires_at < ?', until, b.id, until),
  st(env, `UPDATE checkout_orders SET quote_expires_at = ?, updated_at = ? WHERE id IN (SELECT order_id FROM basket_lines WHERE basket_id = ?) AND status = 'checkout_open'`, until, now(), b.id),
];

/* Run the basket forward as far as Stripe allows. Safe to call at any time and any number of times. */
export async function coordinate(env, basketId, actor = 'system') {
  const t = now();
  const got = await run(env, `UPDATE checkout_baskets SET lease_until = ?, attempts = attempts + 1 WHERE id = ? AND (lease_until IS NULL OR lease_until < ?) AND status IN ('open','authorising','action_required','capturing')`,
    new Date(Date.now() + LEASE_SECONDS * 1000).toISOString(), basketId, t);
  if (!got.meta.changes) return basketRow(env, basketId);   // ended, or another coordinator holds it
  try {
    let b = await basketRow(env, basketId);
    if (b.status === 'open') b = await afterCardPage(env, b, actor);
    if (b && b.status === 'authorising') b = await authoriseAll(env, b, actor);
    if (b && b.status === 'action_required') b = await checkActions(env, b, actor);
    if (b && b.status === 'capturing') b = await captureAll(env, b, actor);
    return b;
  } finally {
    await run(env, 'UPDATE checkout_baskets SET lease_until = NULL WHERE id = ?', basketId);
  }
}

async function afterCardPage(env, b, actor) {
  if (!b.setup_session) return b.expires_at < now() ? endBasket(env, b, 'expired', actor, 'The card page was never opened') : b;
  const s = await S.getPlatformSession(env, { id: b.setup_session });
  const si = s.setup_intent && typeof s.setup_intent === 'object' ? s.setup_intent : null;
  if (s.status === 'complete' && si && si.status === 'succeeded' && si.payment_method) {
    const pm = typeof si.payment_method === 'string' ? si.payment_method : si.payment_method.id;
    const until = addMin(now(), BASKET_DECISIONS.action_minutes + HOLD_GRACE_MINUTES);
    await env.DB.batch(extendHolds(env, b, until));
    return setStatus(env, b, 'authorising', actor, 'card_saved', { setup_intent: si.id, payment_method: pm }, { setup_intent: si.id, hold_until: until });
  }
  if (s.status === 'expired' || (s.status === 'open' && Date.parse(b.expires_at) + 60_000 < Date.now())) {
    if (s.status === 'open') await S.expirePlatformSession(env, { id: s.id }).catch(() => null);
    const again = await S.getPlatformSession(env, { id: b.setup_session });
    if (again.status === 'complete') return afterCardPage(env, b, actor);   // completed at the last second
    return endBasket(env, b, 'expired', actor, 'The card was not entered before the secure page expired');
  }
  return b;   // the buyer is still on Stripe's page
}

async function authoriseAll(env, b, actor) {
  const lines = await linesOf(env, b.id);
  for (const l of lines) {
    if (!['pending', 'error'].includes(l.state)) continue;
    const o = await C.getOrder(env, l.order_id);
    try {
      let clone = l.clone_pm;
      if (!clone) {
        clone = (await S.clonePaymentMethod(env, { account: l.account, idem: `plotart-basket-${b.id}-${o.id}-clone`, customer: b.platform_customer, paymentMethod: b.payment_method })).id;
        await setLine(env, l, { clone_pm: clone });
      }
      const seller = J(o.seller) || {};
      const r = await S.authoriseOutcome(env, { account: l.account, idem: `plotart-basket-${b.id}-${o.id}-auth`, amountCents: l.amount_cents, feeCents: l.fee_cents, paymentMethod: clone,
        order: o, basket: b, statement: `${o.reference} · sold by ${seller.name} · basket ${b.reference} · introduced by PlotArt` });
      const pi = r.ok ? r.pi : r.pi;
      if (pi && pi.id) await env.DB.batch([
        st(env, 'UPDATE basket_lines SET payment_intent = COALESCE(payment_intent, ?), updated_at = ? WHERE order_id = ?', pi.id, now(), l.order_id),
        st(env, 'UPDATE checkout_orders SET payment_intent = COALESCE(payment_intent, ?), updated_at = ? WHERE id = ?', pi.id, now(), o.id)]);
      if (r.ok && r.pi.status === 'requires_capture') {
        if (r.pi.amount !== l.amount_cents || (r.pi.application_fee_amount || 0) !== l.fee_cents) { await setLine(env, l, { state: 'error', last_error: 'authorised amount or fee differs from the order' }); return fail(env, b, actor, 'An authorised amount did not match the order'); }
        await setLine(env, l, { state: 'authorised', last_error: null }); continue;
      }
      if ((r.ok && r.pi.status === 'requires_action') || (!r.ok && (r.code === 'authentication_required' || r.decline_code === 'authentication_required'))) {
        await setLine(env, l, { state: 'action_required', decline_code: 'authentication_required', last_error: null }); continue;
      }
      if (!r.ok && r.retryable) {
        await setLine(env, l, { state: 'error', attempts: l.attempts + 1, last_error: String(r.error.message).slice(0, 300) });
        if (l.attempts + 1 >= MAX_ATTEMPTS) return fail(env, b, actor, `A payment to ${seller.name} could not be made`);
        return b;   // resumed by the next call (buyer, webhook or sweep)
      }
      if (r.ok && r.pi.status === 'succeeded') { await setLine(env, l, { state: 'captured' }); continue; }   // not expected with manual capture; recorded at capture
      // declined (or any other refusal): nothing in this basket is bought
      await setLine(env, l, { state: 'declined', decline_code: r.decline_code || r.code || (r.ok ? r.pi.status : null), last_error: r.ok ? `status ${r.pi.status}` : String(r.error.message).slice(0, 300) });
      return fail(env, b, actor, `Your card was declined for the payment to ${seller.name}`, { order: o.reference, code: r.code, decline_code: r.decline_code });
    } catch (e) {
      await setLine(env, l, { state: 'error', attempts: l.attempts + 1, last_error: String(e.message || e).slice(0, 300) });
      if (l.attempts + 1 >= MAX_ATTEMPTS) return fail(env, b, actor, 'A payment could not be made');
      return b;
    }
  }
  const after = await linesOf(env, b.id);
  if (after.some(l => l.state === 'action_required')) {
    const deadline = addMin(now(), BASKET_DECISIONS.action_minutes), until = addMin(deadline, HOLD_GRACE_MINUTES);
    await env.DB.batch(extendHolds(env, b, until));
    return setStatus(env, b, 'action_required', actor, 'authentication_needed', { action_deadline: deadline }, { lines: after.filter(l => l.state === 'action_required').map(l => l.line_no) });
  }
  if (after.every(l => ['authorised', 'captured'].includes(l.state))) return setStatus(env, b, 'capturing', actor, 'all_authorised', {}, { lines: after.length });
  return b;
}

async function checkActions(env, b, actor) {
  for (const l of await linesOf(env, b.id)) {
    if (l.state !== 'action_required' || !l.payment_intent) continue;
    const pi = await S.getPaymentIntent(env, { account: l.account, id: l.payment_intent });
    if (pi.status === 'requires_capture') {
      if (pi.amount !== l.amount_cents || (pi.application_fee_amount || 0) !== l.fee_cents) return fail(env, b, actor, 'An authorised amount did not match the order');
      await setLine(env, l, { state: 'authorised', decline_code: null });
    } else if (pi.status === 'canceled' || (pi.status === 'requires_payment_method' && pi.last_payment_error && pi.last_payment_error.code !== 'authentication_required')) {
      await setLine(env, l, { state: 'declined', decline_code: (pi.last_payment_error && (pi.last_payment_error.decline_code || pi.last_payment_error.code)) || pi.status });
      const seller = J((await C.getOrder(env, l.order_id)).seller) || {};
      return fail(env, b, actor, `The payment to ${seller.name} was not authorised`);
    }
  }
  const lines = await linesOf(env, b.id);
  if (lines.every(l => l.state === 'authorised')) return setStatus(env, b, 'capturing', actor, 'all_authorised', { action_deadline: null }, { after: 'authentication' });
  if (b.action_deadline && b.action_deadline < now()) return fail(env, b, actor, 'The extra bank check was not completed in time');
  return b;
}

async function captureAll(env, b, actor) {
  const lines = await linesOf(env, b.id);
  if (!lines.every(l => ['authorised', 'captured'].includes(l.state))) return fail(env, b, actor, 'Not every payment was authorised');
  // every original must still be this basket's (a reservation that lapsed and was taken by another buyer stops the basket)
  for (const l of lines.filter(x => x.state === 'authorised')) {
    const o = await C.getOrder(env, l.order_id);
    const res = await one(env, 'SELECT order_id FROM artwork_reservations WHERE artwork_id = ?', o.artwork_id);
    const sold = await one(env, 'SELECT order_id FROM artwork_sales WHERE artwork_id = ? AND released_at IS NULL', o.artwork_id);
    if ((res && res.order_id !== o.id) || (sold && sold.order_id !== o.id)) return fail(env, b, actor, `${(J(o.artwork_snapshot) || {}).title || 'An artwork'} is no longer available`);
    if (!res) await run(env, 'INSERT INTO artwork_reservations (artwork_id, order_id, quote_version, expires_at, created_at) VALUES (?,?,?,?,?) ON CONFLICT(artwork_id) DO NOTHING', o.artwork_id, o.id, 1, addMin(now(), 30), now());
  }
  for (const l of lines.filter(x => x.state === 'authorised')) {
    try {
      const pi = await S.capture(env, { account: l.account, idem: `plotart-basket-${b.id}-${l.order_id}-capture`, id: l.payment_intent });
      if (pi.status !== 'succeeded') throw new S.StripeError(`capture left the payment ${pi.status}`, 409);
      await setLine(env, l, { state: 'captured', last_error: null });
    } catch (e) {
      const retry = e instanceof S.StripeError && e.status >= 500;
      await setLine(env, l, { attempts: l.attempts + 1, last_error: String(e.message || e).slice(0, 300) });
      if (retry && l.attempts + 1 < MAX_ATTEMPTS) return b;   // resumed by the next call
      // an authorised payment that cannot be captured (e.g. the authorisation lapsed): stop, release what is not captured,
      // and hand the basket to the founder. Payments already captured are recorded and flagged for refund below.
      return resolve(env, b, actor, `The payment for line ${l.line_no} could not be captured: ${String(e.message || e).slice(0, 160)}`);
    }
  }
  // every line captured: record each sale through the single-artwork path (sale, ledger, sold mark, confirmation)
  const outcomes = await recordCaptured(env, b);
  if (outcomes.some(x => !/^paid/.test(x.result) && x.result !== 'already recorded')) return resolve(env, b, actor, 'A captured payment could not complete its sale', { outcomes });
  const done = await setStatus(env, b, 'paid', actor, 'paid', { action_deadline: null }, { outcomes });
  await releaseCard(env, done || b);
  return done || b;
}
async function recordCaptured(env, b) {
  const out = [];
  for (const l of (await linesOf(env, b.id)).filter(x => x.state === 'captured')) {
    const o = await C.getOrder(env, l.order_id);
    const pi = await S.getPaymentIntent(env, { account: l.account, id: l.payment_intent });
    const result = await C.recordPaid(env, o, { id: null, basket: b.reference, amount_total: pi.amount_received, currency: pi.currency, payment_intent: pi.id, application_fee_cents: pi.application_fee_amount || 0 },
      `basket:${b.id}:${l.order_id}`, Math.floor(Date.now() / 1000));
    out.push({ order: o.reference, result });
  }
  return out;
}

/* A basket that cannot be paid: cancel every authorisation, release every artwork, end the orders. Nothing is bought. */
async function fail(env, b, actor, reason, detail = null) {
  return endBasket(env, b, 'failed', actor, reason, detail);
}
async function endBasket(env, b, to, actor, reason, detail = null) {
  const lines = await linesOf(env, b.id);
  let uncancelled = 0;
  for (const l of lines) {
    if (l.payment_intent && ['authorised', 'action_required', 'error', 'pending'].includes(l.state)) {
      try { await S.cancelIntent(env, { account: l.account, idem: `plotart-basket-${b.id}-${l.order_id}-cancel`, id: l.payment_intent }); await setLine(env, l, { state: 'cancelled' }); }
      catch (e) {
        // an intent that is already cancelled or never authorised has nothing to release
        const pi = await S.getPaymentIntent(env, { account: l.account, id: l.payment_intent }).catch(() => null);
        if (pi && ['canceled', 'requires_payment_method'].includes(pi.status)) await setLine(env, l, { state: 'cancelled' });
        else { uncancelled++; await setLine(env, l, { last_error: 'cancel failed: ' + String(e.message || e).slice(0, 200) }); }
      }
    } else if (['pending', 'error'].includes(l.state)) await setLine(env, l, { state: 'cancelled' });
  }
  if (b.setup_session && b.status === 'open') await S.expirePlatformSession(env, { id: b.setup_session }).catch(() => null);
  const t = now(), stmts = [st(env, 'DELETE FROM artwork_reservations WHERE order_id IN (SELECT order_id FROM basket_lines WHERE basket_id = ?)', b.id)];
  for (const l of lines) {
    const o = await C.getOrder(env, l.order_id);
    if (o && R.PRE_PAYMENT.includes(o.status) && o.payment_status !== 'paid') {
      stmts.push(st(env, `UPDATE checkout_orders SET status = 'cancelled', payment_status = ?, updated_at = ? WHERE id = ? AND status = ?`, l.payment_intent ? 'failed' : 'none', t, o.id, o.status),
        C.evSt(env, o.id, actor, 'basket_' + to, o.status, 'cancelled', { basket: b.reference, reason }));
    }
  }
  await env.DB.batch(stmts);
  const done = await setStatus(env, b, to, actor, to, { action_deadline: null, resolution: uncancelled ? `${reason} · ${uncancelled} authorisation(s) still to cancel (retried by the sweep)` : reason }, { reason, ...(detail || {}) });
  await releaseCard(env, done || b);
  return done || await basketRow(env, b.id);
}
/* Captured money exists but the basket cannot complete as a whole: authorisations not captured are cancelled and the
   founder resolves the rest (normally a full refund of each captured line through the order's own refund action). */
async function resolve(env, b, actor, reason, detail = null) {
  for (const l of await linesOf(env, b.id)) {
    if (l.state === 'authorised' && l.payment_intent) {
      try { await S.cancelIntent(env, { account: l.account, idem: `plotart-basket-${b.id}-${l.order_id}-cancel`, id: l.payment_intent }); await setLine(env, l, { state: 'cancelled' }); }
      catch (e) { await setLine(env, l, { last_error: 'cancel failed: ' + String(e.message || e).slice(0, 200) }); }
    }
  }
  const lines = await linesOf(env, b.id);
  const outcomes = await recordCaptured(env, b);   // money received is always booked; recordPaid flags a sale it cannot complete
  for (const l of lines.filter(x => x.state === 'captured'))
    await run(env, 'UPDATE checkout_orders SET needs_resolution = ?, updated_at = ? WHERE id = ?', `Basket ${b.reference} could not complete as a whole: ${reason}. Refund this payment in full (Refund → whole order) unless the buyer agrees in writing to keep this artwork alone.`, now(), l.order_id);
  for (const l of lines.filter(x => x.state !== 'captured')) {
    const o = await C.getOrder(env, l.order_id);
    if (o && R.PRE_PAYMENT.includes(o.status)) await env.DB.batch([st(env, `UPDATE checkout_orders SET status = 'cancelled', updated_at = ? WHERE id = ? AND status = ?`, now(), o.id, o.status),
      st(env, 'DELETE FROM artwork_reservations WHERE order_id = ?', o.id), C.evSt(env, o.id, actor, 'basket_needs_resolution', o.status, 'cancelled', { basket: b.reference, reason })]);
  }
  const done = await setStatus(env, b, 'needs_resolution', actor, 'needs_resolution', { action_deadline: null, resolution: reason }, { reason, outcomes, ...(detail || {}) });
  await releaseCard(env, done || b);
  return done || b;
}
/* The buyer's saved card is kept only while the basket needs it: deleting the platform Customer detaches it. */
async function releaseCard(env, b) {
  if (!b || b.card_released_at || !b.platform_customer) return;
  try { await S.deleteCustomer(env, { id: b.platform_customer }); await run(env, 'UPDATE checkout_baskets SET card_released_at = ?, updated_at = ? WHERE id = ?', now(), now(), b.id); await event(env, b.id, 'system', 'card_released', b.status, b.status, null); }
  catch { /* retried by the sweep */ }
}

/* ---------------------------------------------------------------- events, buyer actions, sweep */
export const isBasketEvent = (ev, obj) => !!(obj && obj.metadata && obj.metadata.plotart_basket && (String(ev.type).startsWith('checkout.session.') || String(ev.type).startsWith('payment_intent.')));
export async function onEvent(env, ev, obj) {
  const b = await basketRow(env, obj.metadata.plotart_basket);
  if (!b) return { status: 'ignored', detail: 'unknown basket' };
  if (String(ev.type).startsWith('checkout.session.')) {
    if (ev.account) throw new Error('a basket card page is on PlotArt’s account, not a connected account');
    if (obj.id !== b.setup_session) return { status: 'ignored', detail: 'not this basket’s current card page' };
  } else {
    const l = await one(env, 'SELECT * FROM basket_lines WHERE basket_id = ? AND (payment_intent = ? OR order_id = ?)', b.id, obj.id, obj.metadata.plotart_order || '');
    if (!l) return { status: 'ignored', detail: 'not a line of this basket' };
    if (ev.account !== l.account) throw new Error('event account does not match the basket line');
  }
  const after = await coordinate(env, b.id, 'provider');
  return { status: 'processed', detail: `basket ${b.reference}: ${after ? after.status : 'unknown'}` };
}
async function byToken(env, token) {
  if (!/^[0-9a-z]{48}$/.test(String(token || ''))) return null;
  return one(env, 'SELECT * FROM checkout_baskets WHERE buyer_token_hash = ?', await sha256(token));
}
export async function buyerContinue(env, token) {
  const b = await byToken(env, token);
  if (!b) return null;
  if (ACTIVE.includes(b.status)) await coordinate(env, b.id, 'buyer');
  return buyerView(env, token);
}
const BUYER_STATUS = {
  open: 'Waiting for your card details.',
  authorising: 'Confirming your payment…',
  action_required: 'Your bank needs you to confirm your payment.',
  capturing: 'Completing your order…',
  paid: 'Order confirmed',
  failed: 'Your payment could not be completed. Nothing was charged, and any amount held by your bank has been released.',
  expired: 'The secure payment page expired before your card details were entered. Nothing was charged.',
  cancelled: 'Your order was cancelled. Nothing was charged.',
  needs_resolution: 'We’re sorting out a problem with your order and will contact you. You will not be charged for anything you do not receive.',
};
/* What a failed order tells the buyer: the reason in plain words, never internal payment detail. */
const buyerReason = r => /declined|not authorised/i.test(r || '') ? 'Your card was declined.' : /bank check|confirm/i.test(r || '') ? 'The payment was not confirmed with your bank in time.'
  : /no longer available/i.test(r || '') ? 'An artwork in your order is no longer available.' : null;
const LINE_STATUS = { pending: 'Not yet charged', authorised: 'Authorised (not yet taken)', action_required: 'Needs your confirmation', captured: 'Paid',
  declined: 'Declined', cancelled: 'Cancelled: nothing taken', error: 'Retrying' };
export async function buyerView(env, token) {
  const b = await byToken(env, token);
  if (!b) return null;
  const lines = [];
  for (const l of await linesOf(env, b.id)) {
    const o = await C.getOrder(env, l.order_id), art = J(o.artwork_snapshot) || {}, seller = J(o.seller) || {};
    const conf = await one(env, "SELECT 1 AS x FROM order_messages WHERE order_id = ? AND kind = 'buyer_confirmation' AND item_key = ''", o.id);
    lines.push({ line: l.line_no, order: o.reference, title: art.title, artist: seller.name, seller: seller.legal_name, artwork_cents: o.artwork_cents, delivery_cents: o.delivery_cents,
      total_cents: o.artwork_cents + o.delivery_cents, state: l.state, state_text: LINE_STATUS[l.state], action: l.state === 'action_required' && b.status === 'action_required', confirmation: !!conf,
      delivery_window: (J(o.delivery) || {}).delivery_window });
  }
  return { reference: b.reference, status: b.status, status_text: BUYER_STATUS[b.status], paid: b.status === 'paid', ended: ENDED.includes(b.status),
    total_cents: b.total_cents, lines, action_deadline: b.action_deadline, expires_at: b.expires_at, test_mode: !b.livemode, resolution: b.status === 'failed' ? buyerReason(b.resolution) : null,
    delivery_to: addressLine(J(b.delivery_address) || {}) };
}
/* The extra bank check for one artist's payment, in the buyer's browser (Stripe.js on the artist's account). */
export async function actionFor(env, token, orderRef) {
  const b = await byToken(env, token);
  if (!b || b.status !== 'action_required') return null;
  const l = await one(env, `SELECT l.* FROM basket_lines l JOIN checkout_orders o ON o.id = l.order_id WHERE l.basket_id = ? AND o.reference = ? AND l.state = 'action_required'`, b.id, String(orderRef || ''));
  if (!l || !l.payment_intent) return null;
  const pi = await S.getPaymentIntent(env, { account: l.account, id: l.payment_intent });
  const pk = String(env.STRIPE_PUBLISHABLE_KEY || '');
  if (!(live(env) ? /^pk_live_/ : /^pk_test_/).test(pk)) throw new Bad('Extra authentication is not configured. Please contact hello@plotnua.ie.', 503);
  const o = await C.getOrder(env, l.order_id);
  return { publishable_key: pk, account: l.account, client_secret: pi.client_secret, payment_method: l.clone_pm || (pi.last_payment_error && pi.last_payment_error.payment_method && pi.last_payment_error.payment_method.id) || null,
    order: o.reference, artist: (J(o.seller) || {}).name, title: (J(o.artwork_snapshot) || {}).title || null, amount_cents: l.amount_cents, deadline: b.action_deadline };
}
export async function confirmationFor(env, token, orderRef) {
  const b = await byToken(env, token);
  if (!b) return null;
  const o = await one(env, `SELECT o.* FROM checkout_orders o JOIN basket_lines l ON l.order_id = o.id WHERE l.basket_id = ? AND o.reference = ?`, b.id, String(orderRef || ''));
  return o ? one(env, "SELECT subject, body, sha256, created_at FROM order_messages WHERE order_id = ? AND kind = 'buyer_confirmation' AND item_key = ''", o.id) : null;
}
export async function buyerCancel(env, token) {
  const b = await byToken(env, token);
  if (!b) return null;
  if (['open', 'action_required'].includes(b.status)) await endBasket(env, b, 'cancelled', 'buyer', 'Cancelled by the buyer');
  return buyerView(env, token);
}

export async function sweep(env) {
  if (!(await installed(env))) return null;
  const t = now(), out = { coordinated: 0, cancels_retried: 0, cards_released: 0 };
  const due = await all(env, `SELECT id FROM checkout_baskets WHERE (status = 'open' AND expires_at < ?) OR (status IN ('authorising','capturing') AND updated_at < ?)
    OR (status = 'action_required') ORDER BY updated_at LIMIT 25`, t, new Date(Date.now() - 60_000).toISOString());
  for (const r of due) { try { await coordinate(env, r.id, 'scheduler'); out.coordinated++; } catch { /* next sweep */ } }
  for (const l of await all(env, `SELECT l.*, b.id AS bid FROM basket_lines l JOIN checkout_baskets b ON b.id = l.basket_id
      WHERE b.status IN ('failed','expired','cancelled','needs_resolution') AND l.state IN ('authorised','action_required') AND l.payment_intent IS NOT NULL LIMIT 25`)) {
    try { await S.cancelIntent(env, { account: l.account, idem: `plotart-basket-${l.bid}-${l.order_id}-cancel`, id: l.payment_intent }); await setLine(env, l, { state: 'cancelled' }); out.cancels_retried++; } catch { /* next sweep */ }
  }
  for (const b of await all(env, `SELECT * FROM checkout_baskets WHERE status IN ('paid','failed','expired','cancelled','needs_resolution') AND platform_customer IS NOT NULL AND card_released_at IS NULL LIMIT 25`)) {
    await releaseCard(env, b); out.cards_released++;
  }
  return out;
}

/* ---------------------------------------------------------------- founder desk */
export async function adminList(env) {
  if (!(await installed(env))) return { installed: false, baskets: [] };
  const rows = await all(env, 'SELECT id, reference, status, buyer_email, total_cents, line_count, resolution, created_at, updated_at FROM checkout_baskets ORDER BY created_at DESC LIMIT 100');
  return { installed: true, enabled: enabled(env), commission_free_policy: commissionFreePolicy(env), decisions: BASKET_DECISIONS, baskets: rows };
}
export async function adminDetail(env, id) {
  const b = await basketRow(env, id);
  if (!b) throw new Bad('Not found', 404);
  const lines = [];
  for (const l of await linesOf(env, id)) { const o = await C.getOrder(env, l.order_id); lines.push({ ...l, order: { id: o.id, reference: o.reference, status: o.status, payment_status: o.payment_status, needs_resolution: o.needs_resolution, commission_basis: o.commission_basis } }); }
  return { basket: { ...b, buyer_token_hash: undefined, delivery_address: J(b.delivery_address) }, lines, events: await all(env, 'SELECT * FROM basket_events WHERE basket_id = ? ORDER BY id', id) };
}
/* Why each artwork can or cannot be bought online right now (internal reasons, founder only). */
export async function adminEligibility(env, ids) {
  const at = now(), out = [];
  for (const id of [...new Set((ids || []).map(String))].slice(0, 50)) { const l = await lineFor(env, id, at); out.push({ id, ok: l.ok, why: l.ok ? null : l.why, commission_basis: l.ok ? l.entitlement.basis : null, total_cents: l.ok ? l.money.total_cents : null }); }
  return { items: out, commission_free_policy: commissionFreePolicy(env) };
}
/* Online sales readiness: ONE definition, used by the founder's Basket readiness tab and by the artist's own Studio card
   and payment-page steps (22 Nov 2026), so both always see the same answer. Records only; nothing is changed here. The
   steps follow the order of the artist's payment page. "online" counts the artist's available artworks that the basket
   would accept right now, with the same check the public basket and the gallery button use (lineFor); an artist with a
   step still to do cannot sell any, so only a ready artist's works are checked one by one. */
const ARTIST_REASON = {
  'artist not ready': 'online sales set-up not finished', 'price on request': 'price on request (add a price to sell online)',
  'above the pilot price limit': 'above the online price limit', 'no delivery offer': 'no delivery offer yet',
  'delivery cover below the price': 'transit insurance below the price', 'return arrangements missing': 'return arrangements missing from the delivery offer',
  'commission-free: no valid processing-fee consent': 'commission-free work: needs the optional processing-fee consent',
  'commission-free: direct payment (policy)': 'commission-free work: enquiry and direct sale only', 'sold': 'sold',
  'reserved': 'reserved for a buyer just now', 'published price differs from the Studio': 'new price not yet published',
  'not published as available': 'not yet published as available',
  'delivery offer awaiting founder approval': 'delivery offer waiting for PlotArt to review it',
  'delivery offer returned by the founder': 'delivery offer returned by PlotArt: see the note and save it again',
  'delivery offer has no dispatch and delivery deadlines': 'delivery offer needs dispatch and delivery deadlines (save it again)',
};
export async function artistReadiness(env, a) {
  const bm = await artistMembership(env, a.id), mem = await C.membership(env, a.id), prof = await C.sellerProfile(env, a.id);
  const pay = await C.currentTerms(env, 'artist_payment_addendum');
  const offerRows = await all(env, 'SELECT * FROM artwork_delivery_offers WHERE artist_id = ? AND withdrawn_at IS NULL', a.id), offers = offerRows.length;
  let offers_approved = 0; for (const o of offerRows) if ((await offerReview(env, o)).approved) offers_approved++;
  const stripe = !mem.account ? 'not connected' : mem.ready && mem.account.payouts_enabled ? 'onboarded' : 'onboarding incomplete';
  const steps = [
    { key: 'join', label: 'Join online sales (payment addendum)', founder: 'payment pilot', done: !!(mem.opted_in && pay && mem.addendum === pay.doc_id) },
    { key: 'seller', label: 'Add your seller information', founder: 'seller information', done: !!(prof && !C.sellerProblems(env, prof).length) },
    { key: 'stripe', label: 'Connect Stripe and complete its checks', founder: 'Stripe onboarding', done: stripe === 'onboarded' },
    { key: 'basket', label: 'Accept the basket addendum', founder: 'basket addendum', done: !!bm.current },
    { key: 'disclosure', label: 'Confirm what buyers see about you as the seller', founder: 'seller-information confirmation', done: !!bm.seller_disclosure.valid },
    { key: 'delivery', label: 'Set a delivery offer for each artwork', founder: 'delivery offers', done: offers > 0 },
  ];
  const missing = steps.filter(x => !x.done).map(x => x.founder);
  const avail = await all(env, `SELECT id FROM artworks WHERE artist_id = ? AND archived = 0 AND availability = 'available' ORDER BY ord`, a.id);
  const online = { available: avail.length, purchasable: 0, not_purchasable: {} };
  if (!missing.length) for (const w of avail) {
    const l = await lineFor(env, w.id, now());
    if (l.ok) online.purchasable++; else online.not_purchasable[l.why] = (online.not_purchasable[l.why] || 0) + 1;
  } else if (avail.length) online.not_purchasable['artist not ready'] = avail.length;
  const artist_reasons = {};
  for (const [k, n] of Object.entries(online.not_purchasable)) { const t = ARTIST_REASON[k] || 'not available online just now'; artist_reasons[t] = (artist_reasons[t] || 0) + n; }
  return { id: a.id, display_name: a.display_name, founding: !!a.founding, stripe, delivery_offers: offers, delivery_offers_approved: offers_approved, basket_addendum: bm.doc_id, basket_current: bm.current, online,
    seller_disclosure: bm.seller_disclosure, processing_consent: bm.processing_consent, missing, steps: steps.map(({ founder, ...x }) => x), artist_reasons,
    commission_free_works: !a.founding ? 'none expected' : bm.processing_consent.valid ? 'offered (artist bears Stripe fees, 0% commission)' : 'direct payment only (no valid consent)' };
}
/* Founder: every artist's basket readiness. */
export async function adminArtists(env) {
  if (!(await installed(env))) return { installed: false, artists: [] };
  const artists = await all(env, `SELECT id, display_name, founding, account_status FROM artists WHERE account_status = 'active' ORDER BY display_name`);
  const out = [];
  for (const a of artists) out.push(await artistReadiness(env, a));
  return { installed: true, consents_installed: await consentsInstalled(env), commission_free_policy: commissionFreePolicy(env), artists: out };
}
/* Artist: their own readiness (Studio home card, payment-page steps). Nothing internal: founder labels and internal
   reasons are left out. Not installed: { installed: false } and the Studio shows no card. */
export async function artistReadinessView(env, artist) {
  if (!(await installed(env)) || !(await C.installed(env))) return { installed: false };
  const r = await artistReadiness(env, artist);
  const done = r.steps.filter(x => x.done).length, next = r.steps.find(x => !x.done) || null;
  const sw = C.switches(env);
  return { installed: true, enabled: !!sw.enabled, live: !!sw.live, steps: r.steps, done, total: r.steps.length, next: next && next.key,
    ready: !next, founding: r.founding, processing_consent: !!r.processing_consent.valid,
    online: { available: r.online.available, purchasable: r.online.purchasable, reasons: r.artist_reasons }, started: r.steps.some(x => x.done) };
}
export async function adminReconcile(env, founder, id) { await coordinate(env, id, founder); return adminDetail(env, id); }
export async function adminCancel(env, founder, id, b) {
  const bk = await basketRow(env, id);
  if (!bk) throw new Bad('Not found', 404);
  if (!['open', 'authorising', 'action_required'].includes(bk.status)) throw new Bad('Only a basket that has not started capturing can be cancelled; refund captured orders instead', 409);
  await endBasket(env, bk, 'cancelled', founder, String((b && b.reason) || 'Cancelled by PlotArt').slice(0, 200));
  return adminDetail(env, id);
}
