# PlotArt managed checkout pilot

Date: 16 November 2026
Status: Proposed pilot specification. No executable checkout, policy amendment, provider configuration or deployment is included.
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
