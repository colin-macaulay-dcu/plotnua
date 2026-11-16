# PlotArt managed checkout pilot

Date: 16 November 2026
Status: Specification, plus a working TEST-MODE implementation (see "Implementation (16 November 2026)" at the end). Off by default. Not deployed, no migration applied, no artist enrolled, no live payments, no public terms changed.
Authorisation: Founder agreed to try the managed-purchase approach following competitor research.

## Purpose

Allow a buyer to discuss an original work with the artist, agree availability and delivery, and then pay through a secure hosted checkout. Deduct the applicable PlotArt commission through a marketplace payment provider. Keep the artist as the proposed seller, subject to confirmation that provider configuration, contracts and actual operation align.

This is an optional pilot for willing artists, not a compulsory migration. Existing direct enquiries and sales continue. No artist is enrolled without accepting a versioned payment addendum.

## Existing implementation reviewed

- Public gallery and artwork pages identify artists as sellers and say PlotArt does not take payment or deliver work.
- plotart/founding-25.html guarantees no membership, subscription or listing fees, no automatic change of terms, and permanent commission exemption for enquiries received during each artist's founding year.
- Studio resides in worker/plotart-studio, with migrations, agreement generation, UI and tests already present.
- Private acceptance records and the full issued agreements have not been reviewed for this specification.
- Repository code search returned no Stripe matches; this is not proof that no payment integration exists elsewhere.
- This session has no usable execution environment. No implementation or tests have been run.

## Proposed scope

One artist and one unique original artwork per order. EUR only initially. Founder-assisted quote followed by hosted checkout. No multi-artist basket, automatic discounts, credit, rental payments, gift cards or public instant-buy rollout.

1. Buyer enquires.
2. Artist confirms availability, location, condition, framing and dimensions.
3. A named organiser obtains packing/transport/cover/installation quotation.
4. Founder prepares a time-limited quote identifying the seller and showing all agreed charges.
5. Artist approves the quote; buyer sees the sale terms before paying.
6. A server-created hosted checkout accepts the exact approved amount.
7. A verified payment event confirms the order and marks the artwork sold.
8. Artist or specialist dispatches; delivery evidence is attached.
9. Payout occurs according to the accepted, provider-supported schedule.
10. PlotArt coordinates communications; seller and platform responsibilities remain explicit.

A successful payment return page is not evidence of payment. Only verified provider events may confirm it.

## Commission rules

All calculations use integer euro cents, server-side. Snapshot the rule and agreement version on the order.

- Founding-year enquiry exemption: 0%, permanently, even when completion is later.
- Founding artist outside that exemption: do not infer 15%; require accepted applicable terms.
- Later artist: proposed 15% only after acceptance of the corresponding agreement.
- Unknown entitlement or missing acceptance: block checkout creation pending resolution.
- No commission on separately itemised delivery in the proposed pilot.
- Platform-funded discounts are excluded.
- Quote revisions invalidate outstanding checkout sessions before a new one is issued.
- Refund accounting must include any required commission refund and transfer reversal.

The final agreement must settle whether 15% includes applicable VAT and payment processing. Until settled, no live quote may represent a guaranteed artist net amount.

Examples before processing fees/tax:
- EUR 1,000 artwork + EUR 75 delivery, 15% artwork commission: EUR 1,075 collected; EUR 150 platform commission; EUR 925 artist/delivery allocation.
- Same order with founding-year enquiry exemption: EUR 0 platform commission; processing allocation remains separately agreed.
Delivery allocation is not artist profit; it pays the transport obligation.

## Payment-provider assessment

Evaluate Stripe Connect with hosted onboarding and hosted checkout. Compare connected-account direct charges plus an application fee against platform destination charges. Obtain confirmation of eligibility for the art business, account countries, who pays fees, negative-balance liability, refund/dispute responsibilities and payout controls.

Do not implement ordinary platform payment collection followed by ad hoc bank transfers as a shortcut. Do not describe provider balances or delayed payouts as escrow.

Before choosing the configuration:
- Identify the legal seller and invoice issuer.
- Confirm whether the platform or artist receives payment in the provider's architecture.
- Confirm who is debited for processing, refunds and disputes.
- Confirm actual payout control; do not promise delivery-based delay unless supported.
- Specify reserves/recovery and artist repayment arrangements.
- Confirm fee refund behaviour.
- Keep test and live credentials, webhook endpoints and data separate.
- Store secrets using existing deployment secret facilities, never Git or browser code.

Processing costs must be presented before artist acceptance. Founding commission exemption must not silently turn into a mandatory processing deduction.

## Delivery and cover

Record actual collection location, unpacked and packed dimensions, weight, medium, framing/glazing, condition, access restrictions and destination.

Each quote identifies:
- Who packs, books, contracts with and pays the transporter.
- Packing, transport, cover, installation and applicable import-cost responsibilities.
- Covered value, valuation basis, excess, exclusions, coverage period and claims contact.
- Delivery window and tracking or scheduled-update arrangements.
- Signed receipt and condition photographs.
- Return route and cost information, especially where ordinary post is unsuitable.

For large, fragile or valuable originals, obtain a specialist quotation. Tracking alone is not full-value cover. Do not publish blanket insurance promises. Buyer remedies must not be made conditional on a completed carrier/insurance claim.

Candidate providers from research: Maurice Ward Art Handling, Irish Art Services and Mail Boxes Etc. No partnership, pricing or cover has been agreed.

## Proposed records

Use a distinct order subsystem after inspecting the current database conventions. Do not edit gallery publishing or founding position logic as part of this pilot.

Artists: opt-in status, accepted agreement version/time, provider account ID and readiness.
Orders: artist/work/enquiry references, entitlement evidence, currency, artwork/delivery/commission/processing amounts, seller identity snapshot, quote version/expiry, terms version, provider session/payment references.
Fulfilment: organiser, transporter, cover evidence, dispatch/delivery records.
Ledger: original charges, commission, transfers, refunds, reversals and adjustments.
Audit: actor, action, timestamp and prior/new status.
Webhook events: provider event ID with unique constraint and processing status.

Suggested statuses:
draft -> awaiting_artist -> quoted -> checkout_open -> paid -> dispatched -> delivered -> closed.
Additional explicit states: expired, cancelled, payment_failed, refund_pending, refunded, disputed.
Use separate payment, fulfilment and dispute fields where a single status would lose information.

Minimise personal data and restrict access to the relevant artist and founder. Keep identity documents within provider onboarding where possible.

## Reservation and payment integrity

- Reserve a work atomically before opening checkout, with an explicit expiry.
- Do not trust price, commission, artist or delivery amounts supplied by a browser.
- Prevent concurrent sessions/orders for the same unique work.
- Handle delayed successful payments after expiry without silently selling twice: flag for reconciliation and customer resolution.
- Make webhook processing idempotent and validate signatures.
- Record payment success durably before acknowledging the event.
- Do not trigger gallery publishing or artist payouts from an unverified browser redirect.
- Reconcile provider state after interruptions.
- Prevent unauthorised access to another buyer's checkout/order.
- Record external sale/unavailability before offering checkout.
- Payout delay does not eliminate later chargebacks.

## Agreement and policy work

Prepare a versioned opt-in artist payment addendum and buyer purchase terms for review, covering seller identity, payment authority, fees/tax, commission exemptions, settlement, refunds/disputes, delivery and data sharing.

Do not overwrite existing acceptances or silently change the public introducer model. Update public copy only when the actual pilot and accepted terms support it.

Obtain Irish professional advice on marketplace responsibilities, commission VAT treatment, DAC7 applicability and art trader/intermediary AML obligations for EUR 10,000 or linked transactions. Direct artist payment does not itself remove AML applicability. Provider KYC does not discharge all platform obligations.

## Required verification before activation

1. Non-founding accepted artist: correct 15% artwork commission; delivery excluded.
2. Founding-year enquiry completed later: zero commission.
3. Founding artist with no accepted later terms: 15% never inferred.
4. Missing consent, incomplete onboarding or unknown entitlement blocks checkout.
5. Expired/revised quote cannot accept a stale amount.
6. Two simultaneous buyers cannot purchase one original.
7. Forged, duplicate, delayed and out-of-order webhook events are handled correctly.
8. Payment failure/abandonment releases a reservation appropriately.
9. Full/partial refunds reconcile buyer payment, commission and artist transfer.
10. Dispute after payout has a documented recovery/support route.
11. Gallery publication, artist records, permissions and founding positions are unaffected.
12. Buyer cannot access another order; artist cannot access another artist's orders.
13. Shipping total and seller identity match quote, checkout and confirmation.
14. A declined or incomplete payment never marks a work sold.
15. Test mode cannot send live payouts or expose live purchasing.

## Activation dependencies

Working coding runtime; provider test configuration; agreement review; fee allocation decision; willing artist; actual artwork and shipping route; confirmed cover; test evidence.

Deliver the first implementation with payments disabled by default. Review the tested result and provider/legal setup before live activation.

## Primary references

- https://www.art4you.ie/sellers-information/
- https://www.art4you.ie/returns/
- https://www.art4you.ie/buy-irish-art-from-abroad/
- https://docs.stripe.com/connect/charges
- https://stripe.com/ie/connect/pricing
- https://stripe.com/ie/pricing
- https://www.ccpc.ie/information-for-businesses/selling-goods-and-services/selling-products
- https://www.revenue.ie/en/companies-and-charities/international-tax/aeoi/dac7/reporting.aspx
- https://www.amlcompliance.ie/art-trader-intermediary/

## Implementation (16 November 2026)

Everything below is on branch `plotart/managed-checkout-pilot` only. Nothing is merged, deployed, migrated, issued or enrolled.

### What was built

| Part | Files |
|---|---|
| Commission entitlement, amounts, statuses, delivery/cover validation (pure rules) | `src/checkout-rules.js` |
| Stripe Connect adapter (test keys only), webhook signature check | `src/stripe.js` |
| Orders, reservations, sales, sessions, verified events, ledger, refunds, disputes, fulfilment, sweep | `src/checkout.js` |
| Public buyer Worker `plotart-checkout`: quote page, hosted-checkout start, return page, terms, webhook | `src/checkout-public.js`, `wrangler.checkout.toml` |
| Studio routes: founder desk `/admin/checkout`, artist page `/checkout-pilot` (not linked from the Studio tabs) | `src/index.js`, `ui/checkout-pilot.js`, `build-assets.mjs` |
| Database: 12 new tables, refusal-only triggers on new tables only, no FKs into artists/artworks | `migrations/0016_managed_checkout_pilot.sql` (also appended to `schema.sql`) |
| Draft texts for review (not issued) | `agreements/payment-drafts/PA-PAY-2026-11-DRAFT.md`, `PA-BPT-2026-11-DRAFT.md` |
| Proofs | `test/prove-checkout-pilot.mjs` (81 checks), `test/prove-migration-0016.mjs` (9 checks) |

Switches: `CHECKOUT_PILOT_ENABLED` defaults to `"false"` in both `wrangler.toml` and `wrangler.checkout.toml`. Even when
on, the code refuses any key that is not `sk_test_`/`rk_test_`, any live-mode object returned by Stripe and any
live-mode event; the database refuses live accounts (`livemode = 0` CHECK) and any session id not beginning `cs_test_`.
Moving to live therefore needs a code change, not a setting.

### Provider configuration chosen

**Stripe Connect, direct charges on the artist's own Stripe account, Stripe-hosted onboarding and Stripe-hosted
Checkout, with PlotArt's commission taken as an `application_fee_amount`.** Each artist's account is created with
controller properties equivalent to a Standard account: `fees.payer = account`, `losses.payments = stripe`,
`requirement_collection = stripe`, `stripe_dashboard.type = full`.

Why this and not the alternatives:
- Direct charges make the connected account the business the buyer pays, debit refunds and disputes from that account,
  and let the platform take an optional application fee. That matches "the artist is the seller and collects payment"
  in PA-FAA cl. 3 and PA-GAA cl. 4, so the pilot does not silently change PlotArt into the seller.
- Destination charges and separate charges-and-transfers put the payment, Stripe's fees, refunds and chargebacks on
  PlotArt's own balance, and PlotArt would then be paying the artist out. The spec rules out "platform collection then
  transfers"; destination charges have the same economic effect and were rejected for the same reason.
- `losses.payments = stripe` means Stripe, not PlotArt, is liable for an artist's negative balance (after refunds or
  lost disputes) and recovers it from the artist under Stripe's own agreement.

### Decisions documented (founder confirmation marked ⚑)

| Question | Implemented position |
|---|---|
| Who pays processing fees? | ⚑ Stripe deducts its processing fees from the **artist's** Stripe balance (`fees.payer = account`), on every order including commission-free ones. Disclosed in the addendum before opt-in; never presented as PlotArt commission; quotes never show a guaranteed net. Alternative for Colin: PlotArt bears fees (`fees.payer = application`), which costs PlotArt money on 0% orders. |
| Does 15% include VAT? | Yes, as PA-GAA-2026-11 cl. 5.2 already says: the 15% includes any VAT applicable to the commission, on the Commission Base only. The application fee equals the full commission. Professional confirmation of the VAT treatment remains outstanding (as recorded on 13 Nov). |
| Commission rules | Founding Enquiry (fixed in `enquiry_log` at introduction) → 0% permanently, whenever completed. Founding Artist without separately accepted commission terms in effect at introduction → 0% (FAA cl. 5–6); **15% is never inferred**. Gallery Artist → the rate in `artist_terms` (≤15%) only with an accepted PA-GAA dated on/before the introduction and inside the 24-month attribution period. Anything else → **blocked**. Delivery never carries commission. Commission rounds down (in the artist's favour). The founder can only lower to 0 with a recorded GAA 5.7 exclusion, never raise. |
| Refunds | The artist, as seller, is responsible to the buyer. The founder can refund from the order (artwork and delivery amounts separately). Stripe debits the artist's balance. PlotArt refunds its application fee by the **exact** GAA 9.2 amount (full on full refund; Full Commission × kept ÷ due on partial; nothing for delivery refunds) using `refund_application_fee = false` plus an explicit fee refund — not Stripe's proportional default, which would wrongly include delivery. Refunds the artist makes in their own Stripe Dashboard arrive as events, are booked as `external_refund` and flagged for commission settlement. |
| Disputes | Debited from the artist's Stripe balance by Stripe; the artist responds in their Stripe Dashboard with PlotArt's order, quote, terms-acceptance and delivery records. A lost dispute flags the order and the founder's "commission only" refund returns PlotArt's fee (GAA 9). A dispute arriving before its payment completion is deferred (HTTP 500, Stripe retries), not lost. |
| When are artists paid? | On the artist's own Stripe payout schedule. PlotArt does not hold funds, does not delay payouts to delivery and does not describe anything as escrow. Chargebacks remain possible after payout. |
| Delivery and cover | Kept entirely separate from commission. Every quote must name packer, organiser, booker, contracting party, payer, installation and import-cost parties; the cover type actually arranged (transit insurance, carrier's limited liability, or **none** — shown as such); covered value, valuation basis, excess, exclusions, period and claims contact; delivery window, tracking, signed receipt, condition photographs, return route; and a **shipment-specific confirmation reference, who confirmed it and when**. The artist confirms each item before the buyer can pay. No blanket insurance promise exists anywhere. |
| Order ceiling | EUR 9,999.99 per artwork in the pilot (below the EUR 10,000 art-trader AML threshold). Linked transactions still need watching; professional advice outstanding. |

### How the requirements are met

1. One artist, one original per order: an order holds one `artwork_id`; `artwork_reservations` (PK artwork) and a
   partial unique index on `artwork_sales` (one active sale per artwork) enforce it in the database.
2. Availability and delivery agreed before checkout: draft → founder enters price, delivery and cover → artist confirms
   six shipment items and approves that exact quote version → founder issues a time-limited quote (1–7 days) → buyer
   accepts the terms → hosted checkout. Any revision expires the open Stripe session first, bumps the version, clears
   the approval and the buyer link.
3–5. Commission and Founding 25 protections: see the table above. No existing agreement, acceptance or term is changed;
   the pilot only reads `enquiry_log`, `artist_terms` and the acceptance tables.
6. Explicit opt-in: append-only `payment_pilot_events`; a trigger accepts an opt-in only against an installed addendum
   with the matching fingerprint. Leaving cancels unpaid quotes; paid orders complete.
7. Records: orders, expiring reservations, sessions, verified events (`payment_events`, unique by Stripe event id),
   append-only ledger, refunds, append-only fulfilment evidence, append-only order audit (actor, prior/new status).
8. No duplicate purchases; idempotent, order-independent events: unique event ids, `UNIQUE(kind, provider_ref)` on the
   ledger, the sale/reservation constraints, out-of-order handling (late expiry ignored, late completion of an already
   sold work flagged for refund, charge events before completion deferred). A Stripe redirect is never proof of payment.
9. Direct enquiries unchanged: `src/enquiry.js` is untouched; the Studio enquiries view is re-tested.
10. Off by default, test mode only (above).
11. No change to public pages, terms, acceptances, gallery order, publishing or permissions. The only existing row the
   pilot writes is the artwork's working-copy availability (`sold`) after a verified sale; it reaches the public site
   only through the normal Studio publishing path (nothing is dispatched).

### Test results (local, 16 November 2026)

- `node test/prove-checkout-pilot.mjs` — **81 / 81 passed**. Covers all 15 "Required verification" items against the
  real Studio and public Workers in Miniflare with a mock Stripe API: commission cases (15% / founding enquiry 0% /
  founding artist never inferred / unknown blocked), consent and onboarding gates, stale/expired/revised quotes, two
  simultaneous buyers, forged/tampered/replayed/duplicate/out-of-order/live-mode events, failure and abandonment,
  partial/delivery/full/external refunds with exact commission reversal, disputes (deferred, opened, lost, close
  blocked), cross-artist and cross-buyer access, gallery/publishing/positions/agreements/enquiry-log unchanged, test-mode
  refusal of live keys and objects, and a default-configuration instance proving the pilot is off.
- `node test/prove-migration-0016.mjs <schema-before.sql>` — **9 / 9 passed** (new tables only, existing objects and rows
  unchanged, refusal-only triggers on new tables, idempotent, rollback exact, artwork deletion unaffected).
- Existing regression suites: see the PR description for the run and the baseline comparison.

### Exact setup for a first test-mode transaction (each step needs Colin's approval)

1. **Stripe (Colin's login).** In the PlotNua Stripe account, stay in *test mode*; activate Connect for a platform;
   confirm with Stripe that original-art sales by Irish/NI individual artists are eligible; note the test secret key.
   (A restricted key `rk_test_` needs: Connect accounts + account links write, Checkout Sessions write, Refunds write,
   Application fee refunds write, PaymentIntents read.)
2. **Texts.** Approve PA-PAY and PA-BPT (drafts in `agreements/payment-drafts/`); issue each as HTML in
   `agreements/payment-issued/` with `fingerprints.json` (`{"documents": {"PA-PAY-2026-11": {"title", "kind":
   "artist_payment_addendum", "html_sha256"}, …}}`); run `node build-assets.mjs`; prepare migration 0017 inserting the two
   `payment_terms` rows with those fingerprints.
3. **Database.** Apply migrations 0016 and 0017 through the approved D1 migration workflow (both backups; exact SQL
   approved).
4. **Public Worker.** Create `plotart-checkout` from `wrangler.checkout.toml` (set the D1 `database_id` and
   `CHECKOUT_ORIGIN` to the Worker's own origin), then
   `npx wrangler secret put STRIPE_SECRET_KEY -c wrangler.checkout.toml` and the same for `STRIPE_WEBHOOK_SECRET`.
5. **Stripe webhook (test mode).** Add an endpoint for *events on connected accounts* at
   `<CHECKOUT_ORIGIN>/v1/stripe/webhook` with: `checkout.session.completed`, `checkout.session.async_payment_succeeded`,
   `checkout.session.async_payment_failed`, `checkout.session.expired`, `charge.refunded`, `charge.dispute.created`,
   `charge.dispute.updated`, `charge.dispute.closed`, `account.updated`. Its `whsec_…` secret is step 4's
   `STRIPE_WEBHOOK_SECRET`.
6. **Studio Worker.** `npx wrangler secret put STRIPE_SECRET_KEY` (same test key); set `CHECKOUT_ORIGIN` as in step 4;
   deploy. Then set `CHECKOUT_PILOT_ENABLED = "true"` on both Workers.
7. **Willing artist (their decision).** The artist opens `/checkout-pilot` in Studio, reads and accepts the addendum,
   completes Stripe test onboarding.
8. **First test order.** Founder at `/admin/checkout`: create from a logged enquiry → enter price, delivery and cover
   (with the transporter's quote reference) → send to artist → artist approves → issue quote → open the buyer link →
   pay with Stripe test card 4242 4242 4242 4242 → confirm the order shows *paid* only after the webhook → record
   dispatch/delivery → try a partial refund.

### Remaining before a real (live) pilot transaction

- Colin's decisions: D1 processing-fee bearer; approval of PA-PAY and PA-BPT texts; whether to proceed to live.
- Professional advice (spec "Agreement and policy work"): marketplace/consumer responsibilities, commission VAT
  treatment, DAC7, AML art-trader/intermediary obligations.
- Stripe: platform activation, eligibility confirmation for art sales, live keys (a code change is required to accept
  them, by design).
- Privacy notice update covering buyer checkout data and Stripe as a recipient (not drafted here).
- A willing artist, a real artwork and a confirmed transport and cover quotation for that shipment.
- Not built in this pilot: automatic emails (the founder sends the buyer link; Stripe sends receipts), PlotArt
  commission invoices (still manual under GAA 8), CSV export of the ledger.
