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

In the initial pilot every real shipment needs confirmed transit insurance for that shipment (see Implementation).

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

## Implementation (16 November 2026, revision 2)

Everything below is on branch `plotart/managed-checkout-pilot` only. Nothing is merged, deployed, migrated, issued or
enrolled, and payments are not activated.

### Revision 3 (16 November 2026, founder review 2)

Production, agreements and live settings are unchanged. Nothing merged, deployed, migrated, issued or enrolled.

#### Fee model assessment — "15% is the artist's total deduction; PlotArt absorbs Stripe's fee" (assessed, NOT adopted)

Today (model A) the artist bears Stripe's processing fee on top of any commission. Model B makes an accepted commission
the artist's only deduction. Two ways Stripe could support it:

- **B1 — Stripe bills PlotArt for fees** (`controller.fees.payer = application`). PlotArt then "handles pricing" in
  Stripe's terms: Stripe's Connect pricing for that option adds per-active-account and per-payout charges (published
  for the US as $2 per monthly active account and 0.25% + 25¢ per payout; the EUR figures must be confirmed). It changes
  the account configuration already verified.
- **B2 — application-fee offset** (configuration unchanged). After each payment PlotArt reads Stripe's actual fee from
  the charge's balance transaction and refunds that amount of its application fee, so the artist's net is exactly the
  amount less the commission. No Connect platform fees. PlotArt's cost per order can never exceed its commission. The
  actual fee is available from the balance transaction (real-API check P7 records it).

Effect on PlotArt (per order, Gallery Artist at 15%, EUR 1,000 artwork + EUR 75 delivery, Stripe's published EEA rates):

| Card | Stripe fee | PlotArt keeps, model A | PlotArt keeps, model B | Margin reduction |
|---|---|---|---|---|
| Standard EEA (1.5% + €0.25) | €16.38 | €150.00 | €133.62 | 10.9% |
| Premium EEA (1.9% + €0.25) | €20.68 | €150.00 | €129.32 | 13.8% |
| UK (2.5% + €0.25) | €27.13 | €150.00 | €122.87 | 18.1% |
| International (3.25% + €0.25) | €35.19 | €150.00 | €114.81 | 23.5% |
| Small order: €300 + €40, standard card | €5.35 | €45.00 | €39.65 | 11.9% |

- If PlotArt is VAT-registered, the €150 includes €28.05 VAT, so net commission revenue is €121.95 under A. Under B2 the
  commission actually charged becomes €133.62 (€108.63 net of VAT); under B1 it stays €150 with the €16.38 as PlotArt's
  expense (€105.57 after the fee). VAT treatment needs the accountant.
- Fee on delivery: Stripe charges on the whole €1,075, so under B PlotArt also pays the fee on the delivery portion
  (about €1.13 of the €16.38 here).
- Refunds: Stripe keeps its fee when a payment is refunded. Under B1 PlotArt bears that loss; under B2 PlotArt returns
  its remaining commission and the lost fee falls back on the artist unless PlotArt pays it by a separate transfer. This
  needs a decision.
- Commission-free orders: there is no commission to offset, so under B PlotArt would have to pay the whole fee
  (€16.38 per standard €1,075 order) by transfer. That is why the separate consent below exists instead.
- Illustration: 20 Gallery Artist sales a year of €1,075, all standard cards: €3,000 commission under A against about
  €2,672 under B, so €328 less.
- Requirements if adopted: Colin's decision; new addendum wording (more favourable to artists, so PA-GAA is not
  changed); code for B2 (fee read after payment, offset refund, idempotent); a refund rule; real-API verification.
  Nothing is changed automatically.

#### Founding Artists keep direct payment; the processing charge needs separate consent

Direct payment (the buyer pays the artist; no deduction) stays every artist's normal route; the pilot is optional per
sale. On any commission-free order (all Founding Enquiries and Founding Artists without commission terms) Stripe's fee
would be the only deduction, so the pilot now requires a **separate, explicit, withdrawable consent** to that
processing charge (`PROCESSING_STATEMENT`). It is not part of opting in, it is recorded separately with its exact
statement, and the artist approval, quote and checkout all refuse such an order without it. Withdrawing cancels unpaid
commission-free quotes. Gallery Artists on 15% are never asked.

#### Funding a refund after payout

Under the pilot configuration the connected account is responsible for its own negative balance; Stripe debits the
account's bank account where it can and, as a last resort, Stripe (not PlotArt) carries an unrecoverable loss.

| When | What happens | Who acts |
|---|---|---|
| Day 0 | The refund comes back `pending` (the available balance is too low). The pilot books nothing and returns no commission. The order is flagged; the artist and the founder are emailed (where email is on) with the steps; it is listed on the founder desk with its days pending and Stripe's 45-day date, and on the artist's page. | system |
| Days 0–45 | The artist funds it: (a) Stripe completes it from new sales or by debiting the linked bank account; or (b) the artist adds funds (Stripe Dashboard → Balances → Add to balance, bank transfer), which releases the refund when the funds arrive. Each sweep re-checks the refund with Stripe, so a missed webhook cannot leave it stale. | artist / Stripe |
| Day 7 | Reminder to the artist and founder; flag "OVERDUE" (once). | system |
| Day 30 | Flag "URGENT" (once); the founder contacts the artist and keeps the buyer informed. | founder |
| Day 45 | Stripe cancels the refund (`refund.failed`). Order flagged: the buyer has NOT been repaid. | Stripe |
| After cancellation | The artist repays the buyer directly; the founder records it with evidence ("Record repayment outside Stripe"). PlotArt then returns its commission share (GAA 9.2). This is refused while a Stripe refund is still pending, so the buyer can never be repaid twice. | artist, founder |

PlotArt does not advance money to buyers. Doing so would be a separate founder decision.

#### Retention, start dates, deletion and legal holds

| Records | Kept until | Start | Why |
|---|---|---|---|
| An order that moved money (paid, refunded or disputed), with its ledger, refunds, sessions, provider events, fulfilment evidence and audit | 31 December of the 6th year after its last money movement | The year of the last payment, refund, commission refund or dispute movement, fixed when the order ends (closed or refunded, nothing outstanding) | Irish tax record-keeping keeps records for six years from the transaction (Revenue); PA-GAA cl. 18.3 already commits to six years for commission records; six-year limitation period for contract claims. Counting from year-end satisfies both the "from the transaction" and "after the period" readings. |
| An order that never moved money (draft, cancelled, expired) | 2 years after it ended | The day it was cancelled or expired | Questions and complaints about a quote; the same 24 months used for PlotArt enquiries in the privacy notice. Holds the buyer's email, so kept short. |
| Opt-in, consent and Stripe-account link records | 6 years after the artist left the pilot, once none of their orders is kept | The artist's last "left" event | Evidence of what the artist agreed, for the contract limitation period. |
| Provider events not linked to any order | 90 days | Receipt | Operations only. |

- **How deletion happens:** the checkout Worker's scheduled sweep (every 15 minutes) fixes `retain_until` when an order
  ends. Once the date passes, it deletes each order and every record belonging to it in one transaction. It skips any
  order with an open issue, a pending refund or an active hold.
- **Enforced in the database:** triggers refuse earlier deletion, and refuse any change to a retention date once set
  (it can be neither shortened nor extended).
- **Backups:** the database backups follow their own rotation, so deleted rows disappear from backups as those age out.
  The backup retention period should be stated in the privacy notice.
- **Legal holds** (instead of irreversible extension): the founder places a hold on an order with a basis (dispute,
  claim, Revenue enquiry, investigation, litigation, data-subject request, other), a specific reason and a review date
  no more than 12 months ahead.
  - At review he either renews it (new date and reason) or releases it (reason). Both are recorded in an append-only
    history.
  - Overdue reviews are flagged; nothing renews or releases automatically.
  - The hold never changes the retention date. While it is active nothing is deleted; once it is released, a
    past-retention order is deleted at the next sweep, together with its hold history.
  - This matches Revenue's position that records connected with a claim, appeal or investigation are kept until the
    matter is finalised.

#### Linked-order safeguard (wording corrected)

The EUR 9,999.99 per-artwork limit and the 12-month linked-order check (same email address, any artist) are **limited
operational safeguards**:
- email matching cannot detect other addresses, household members, businesses or agents;
- 12 months is a pilot rule, not a legal definition;
- passing the check is **never** confirmation of anti-money-laundering compliance, nor evidence that no obligation applies.

The stored record is named `linked_order_check` and says so. PlotArt's actual AML position awaits professional advice.

#### Real Stripe test-mode checks: how they run and what is still needed

- `test/stripe-testmode-checks.mjs` (provider phase) runs against the real Stripe **test** API:
  - account configuration and onboarding link;
  - Checkout Session shape, idempotency and expiry;
  - direct charges with application fees and Stripe's actual fee;
  - full and partial refunds, exact and idempotent commission refunds;
  - a refund larger than the available balance (pending);
  - a refund that fails asynchronously;
  - disputes, both won and lost.
- `test/stripe-testmode-e2e.mjs` (e2e phase) runs the pilot's own Workers against the real test API:
  - real **signed** webhook deliveries forwarded by the Stripe CLI;
  - the buyer paying on Stripe's hosted Checkout in headless Chromium;
  - covering payment, ledger against Stripe's charge, partial refund with commission return, expiry, and a dispute.
- `.github/workflows/plotart-checkout-stripe-test.yml` runs both in GitHub's runner using the **checkout-test**
  environment:
  - the Stripe test key stays in GitHub, never in chat or files;
  - each run waits for Colin's approval;
  - nothing is deployed; the evidence is uploaded with every result labelled `stripe-test-api` (Stripe's own response),
    `stripe-test-api+pilot` (Stripe's events processed by the pilot) or `local`.
- It runs from the pilot branch when `worker/plotart-studio/test/stripe-test-run.json` changes, so no merge is needed.

Colin's steps (his logins; never share keys in chat):
1. **Stripe Dashboard → switch to test mode (sandbox).** Open Connect and complete the platform setup for PlotNua in
   test mode, choosing that Stripe sets and collects processing fees from connected accounts. Then Developers → API keys:
   reveal the **test** secret key, or create a restricted test key with write access to Connect accounts, Account Links,
   Checkout Sessions, PaymentIntents, Refunds, Application fees and Disputes, and read access to Balance and Events.
2. **GitHub → plotnua → Settings → Environments → New environment `checkout-test`.**
   - Required reviewers: Colin.
   - Deployment branches: selected branches, add `plotart/managed-checkout-pilot`.
   - Add the environment secret `CHECKOUT_TEST_STRIPE_SECRET_KEY`: paste the test key there and only there.
3. Tell Claude "checkout-test is ready". Claude pushes the run request; Colin approves the waiting run (Actions → the run
   → Review deployments → Approve).
4. The first run creates a test connected account and puts its **test onboarding link** in the run summary.
   - Colin opens it and completes onboarding with Stripe's test data only (no real personal or bank details).
   - Then add the environment **variable** `CHECKOUT_TEST_CONNECTED_ACCOUNT` = the `acct_…` shown.
5. Claude requests the full run (provider + e2e) and reports the evidence.

### What was built

| Part | Files |
|---|---|
| Commission entitlement, amounts, statuses, delivery and insurance validation (pure rules) | `src/checkout-rules.js` |
| Stripe Connect adapter (test keys only), webhook signature check | `src/stripe.js` |
| Orders, reservations, sales, sessions, verified events, ledger, refunds (incl. pending/failed), disputes, fulfilment, linked-purchase check, retention | `src/checkout.js` |
| Public buyer Worker `plotart-checkout`: quote page, hosted-checkout start, return page, terms, status, webhook | `src/checkout-public.js`, `wrangler.checkout.toml` |
| Studio routes: founder desk `/admin/checkout`, artist page `/checkout-pilot` (not linked from the Studio tabs) | `src/index.js`, `ui/checkout-pilot.js`, `build-assets.mjs` |
| Database: 14 new tables (incl. legal holds), refusal-only triggers on new tables only, no foreign keys into artists/artworks | `migrations/0016_managed_checkout_pilot.sql` (also appended to `schema.sql`) |
| Draft texts for review (not issued) | `agreements/payment-drafts/PA-PAY-2026-11-DRAFT.md`, `PA-BPT-2026-11-DRAFT.md` (r2) |
| TEST ONLY placeholder texts (test environment only; refused in any other build) | `agreements/payment-test/` |
| Deployment workflow (prepared, never run) and its tools | `.github/workflows/plotart-checkout-deploy.yml`, `atlas-tools/release/studio/render-checkout-config.py`, `check-stripe-test-secrets.sh`, `checkout-outside-check.sh`, `test/checkout-test-env-seed.mjs` |
| Proofs | `test/prove-checkout-pilot.mjs` (130 checks), `test/prove-migration-0016.mjs` (9), `test/prove-checkout-deploy.mjs` (26) |
| Real Stripe test-mode harness and its GitHub runner (prepared; not yet run with a key) | `test/stripe-testmode-checks.mjs`, `test/stripe-testmode-e2e.mjs`, `.github/workflows/plotart-checkout-stripe-test.yml` |

`CHECKOUT_PILOT_ENABLED` defaults to `"false"` in `wrangler.toml` and `wrangler.checkout.toml` (`production.json` does not
set it). Even when on, the code refuses any key that is not `sk_test_`/`rk_test_`, any live-mode object returned by
Stripe and any live-mode event; the database refuses live accounts and any session id not beginning `cs_test_`.
Moving to live therefore needs a code change, not a setting.

### Stripe Connect configuration — checked against Stripe's documentation (16 Nov 2026)

**Chosen:** direct charges on each opted-in artist's own Stripe account; Stripe-hosted onboarding and Checkout;
PlotArt's commission as `application_fee_amount`; accounts created with `controller.fees.payer = account`,
`controller.losses.payments = stripe`, `controller.requirement_collection = stripe`, `controller.stripe_dashboard.type = full`.

What Stripe documents for this configuration:
- With direct charges the payment is made on the connected account, so refunds, disputes and other negative transactions
  affect the **connected account's** balance; transaction risk falls mainly on connected accounts rather than the platform
  (docs.stripe.com/connect/manage-risk; docs.stripe.com/connect/saas/tasks/refunds-disputes).
- `controller.losses.payments` decides who is ultimately responsible for a connected account's negative balance
  (docs.stripe.com/connect/account-balances). With `stripe`, Stripe assumes the risk of losses from **unrecoverable**
  negative balances (Stripe "Managed Risk" / negative balance liability). Stripe recommends assigning negative-balance
  responsibility to Stripe for direct-charge integrations; when the platform is responsible instead, Stripe holds a
  reserve on the platform's balance (docs.stripe.com/connect/integration-recommendations).
- With `losses.payments = stripe` and `fees.payer = account`, dispute fees are charged to the connected account and
  Stripe covers the loss if the amount cannot be debited (docs.stripe.com/disputes/connect). Accounts where the platform
  is not liable for negative balances handle their own disputes.
- Application fees are **not** refunded automatically with a refund; the platform must refund them explicitly or the
  connected account loses that amount (Connect refunds-and-disputes guide). Stripe adds no fee on the application fee.
- Stripe does not return its processing fees from the original charge when a payment is refunded
  (support.stripe.com, "Understanding fees for refunded payments").

Still unverified against the live API (only against documentation and a mock): that Stripe accepts this exact
controller combination for Irish and Northern Irish individual artists selling original art on PlotNua's platform
account, and the exact `account.updated` requirement fields during onboarding. Those are the first real test-mode checks.

### Refund after the artist has been paid out

Stripe uses the **available** balance for refunds. If it does not cover a card refund, Stripe holds the refund as
**pending** until the balance is sufficient (refunds for other payment methods fail); Stripe may debit the account's bank
account to recover a negative balance where applicable; and Stripe automatically fails a pending refund after 45 days.
If the cardholder disputes the charge while the refund is pending, the refund fails and a dispute is created
(docs.stripe.com/refunds; Stripe support "Fix your pending refund").

The pilot now handles this explicitly:
- a refund Stripe returns as `pending` books **nothing** and returns **no** commission; the order is flagged ("pending at
  Stripe … ask the artist to top up; fails after 45 days"); amounts still pending count against what can be refunded again;
- `refund.updated` / `charge.refund.updated` / `charge.refunded` with `succeeded` then books the refund and returns
  PlotArt's commission share once (idempotent);
- `refund.failed` (e.g. `insufficient_funds` after 45 days, or a cancelled card) marks it failed and flags the order:
  the buyer has **not** been repaid and the artist, as seller, must repay them another way. No commission is returned.

### Who carries what — kept separate

| Layer | Who | Basis |
|---|---|---|
| **Provider loss allocation** (between Stripe, PlotNua's platform account and the artist's account) | Refunds, disputes and dispute fees are debited from the artist's Stripe balance; an *unrecoverable* negative balance is Stripe's loss, which Stripe pursues against the artist under Stripe's own agreement. PlotArt's platform balance is not used. | Stripe configuration above |
| **Contract between artist and PlotArt** | The artist, as seller, repays buyers and bears Stripe fees (decision D1); PlotArt returns its commission per GAA 9 only once a refund succeeds. | PA-PAY draft cl. 3, 7; PA-GAA cl. 9 |
| **Consumer law towards the buyer** | The seller (artist) owes the buyer the statutory remedies, including cancellation refunds, whatever happens in Stripe. PlotArt, as the platform that introduced the sale and prepared the quote, remains responsible for its own information duties (seller identity, charges, terms) and for what its own terms promise; Stripe's loss allocation does not remove either party's obligations to the consumer. | PA-BPT draft cl. 6–7; professional advice outstanding |

### Artist deductions — worked examples

EUR 1,000 artwork + EUR 75 delivery and transit insurance = EUR 1,075 paid. Stripe fees from Stripe's published
standard EEA pricing (standard EEA cards 1.5% + €0.25; premium EEA 1.9% + €0.25; UK 2.5% + €0.25; international
3.25% + €0.25) — to be re-checked on Stripe's Irish pricing page before any text is issued.

| | Founding Artist, commission-free | Gallery Artist, 15% (VAT-inclusive) |
|---|---|---|
| Buyer pays | €1,075.00 | €1,075.00 |
| PlotArt commission (Stripe application fee), on the artwork only | €0.00 | €150.00 — if PlotArt is VAT-registered at 23%, €121.95 + €28.05 VAT inside the €150 |
| Stripe processing fee (separate; Stripe's, not PlotArt's), standard EEA card | €16.38 | €16.38 |
| Net into the artist's Stripe balance | €1,058.62 | €908.62 |
| Transport and insurance, paid on by the artist as quoted | €75.00 | €75.00 |
| Left for the artwork | €983.62 | €833.62 |
| Stripe fee with premium EEA / UK / international card | €20.68 / €27.13 / €35.19 | same |

Notes: Stripe's fee is on the whole €1,075, including the delivery portion; the 15% is not. A full refund returns PlotArt's
€150 but not Stripe's €16.38. A partial artwork refund of €500 returns €75 of commission (GAA 9.2). A lost dispute adds
Stripe's dispute fee (€20 on Stripe's EEA pricing pages at the time of writing). **Review point:** PA-GAA cl. 5.2 says
the artist keeps at least 85% of the Commission Base; that is true of PlotArt's commission, but with Stripe's fee the
artist's cash is below 85% (here €833.62 of €1,000). The addendum says so expressly (cl. 3.3) so it is accepted knowingly.

### Anti-money-laundering

The EUR 9,999.99 per-artwork limit is a **pilot scope limit only. It does not resolve or settle any AML obligation**,
and it will not be raised merely to enable live transactions. Irish law (Criminal Justice (Money Laundering and
Terrorist Financing) Act 2010, as amended) brings in persons trading in or acting as intermediaries in works of art where
the value of the transaction, **alone or with transactions that are or appear to be linked**, is at least EUR 10,000;
the Department of Justice's Anti-Money Laundering Compliance Unit supervises that sector. Whether PlotArt's role in a
managed checkout makes it such an intermediary is one of the open professional-advice questions.

What the pilot does about linked transactions — a limited operational safeguard, never confirmation of AML compliance (`linkedCheck`, enforced when a quote is issued and again when checkout
opens): it totals this order with the same buyer's other pilot orders (email address compared case-insensitively, any
artist, last 12 months, every order paid, refunded, or quoted and payable) and refuses at EUR 10,000 or more; and the
founder must confirm, for each quote, that he knows of no other link (other email addresses, household, business,
agents, staged payments). Both are recorded on the order (`linked_order_check`). Limits: it cannot see purchases outside the pilot
or connections the founder does not know of; it is a refusal rule, not an AML programme.

Higher-value works would be supported only after professional advice confirms PlotArt's position and, if it is within
scope, after PlotArt has what a designated person needs: registration/notification with the competent authority as
required, a written business risk assessment and policies, customer due diligence on buyers (and sellers where required)
including identity verification, beneficial-ownership, PEP and sanctions screening, record keeping, suspicious-transaction
reporting, and training. Stripe's own identity checks on artists do not discharge PlotArt's obligations. Technically that
would be a separate, switched-off "verified purchase" path (a due-diligence record that must be completed and approved
before a quote at or above the threshold can be issued); it is not built.

### Transit insurance (initial pilot)

Every real shipment must have **confirmed transit insurance for that shipment**: cover type `transit_insurance` only
(carrier's limited liability or no cover are refused), covered value at least the artwork price, insurer, who holds the
cover, valuation basis, period, claims contact and a cover confirmation reference (who confirmed it and when). The
quote cannot be sent to the artist without it, and **dispatch cannot be recorded until an `insurance` evidence entry
(policy or certificate reference for this shipment) is recorded**. Test fixtures use clearly labelled simulated cover
("SIMULATED test cover", `SIM-COVER-0001`).

### Records after an artist or artwork is deleted; retention

Order records do not depend on the artist's or artwork's rows: no foreign keys, and the order snapshots the seller,
the artwork as quoted, the amounts, the commission entitlement evidence, the linked-purchase check, and the Stripe
account, payment intent, charge and application fee ids. Tested with the **real** six-year deletion schedule: after the
artist's records and artworks are deleted, the founder still sees the full order and ledger, a full refund still works
on the artist's Stripe account, and the buyer's link still works.

Retention (implemented in the sweep; triggers enforce it): an order that moved money is kept with its ledger, refunds,
sessions, fulfilment and events for **6 years** after it ends (closed or refunded, nothing outstanding); an order that
never moved money for **2 years**; then everything for that order is deleted. A retention date is fixed once set (revision 3; longer retention only by a reviewed legal hold), nothing is deletable before it, and orders with an open issue or a pending refund are never scheduled. Opt-in
records are kept until six years after the artist leaves and none of their orders remain. (Superseded in detail by
revision 3: start dates, fixed retention dates and legal holds. D3: confirm periods with the accountant.)

### Test environment (prepared, not created)

Test and production share code only. Test uses its own Workers (`plotart-studio-test`, `plotart-checkout-test`), its own
D1 database `plotart-checkout-test`, its own R2 buckets, its own Cloudflare Access application, its own Cloudflare token
and Stripe TEST credentials, all in the GitHub environment `checkout-test`. Production (`studio-production.`) can only
deploy `plotart-checkout` with the pilot off and no Stripe secret. The renderer refuses the production database for test.

Exact setup (each step on Colin's approval; nothing here has been run):
1. **Stripe (Colin's login), test mode.** Activate Connect for the PlotNua platform account. Create a restricted test
   key (`rk_test_…`) with write access to Accounts, Account Links, Checkout Sessions, Refunds and Application Fees and read
   access to PaymentIntents (or use the `sk_test_…` key). Add a webhook endpoint listening to **events on connected
   accounts** at `https://plotart-checkout-test.<subdomain>.workers.dev/v1/stripe/webhook` with: `checkout.session.completed`,
   `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, `checkout.session.expired`,
   `charge.refunded`, `refund.updated`, `refund.failed`, `charge.dispute.created`, `charge.dispute.updated`,
   `charge.dispute.closed`, `account.updated`. Note its `whsec_…` secret.
2. **Cloudflare test resources** (EU):
   `npx wrangler d1 create plotart-checkout-test --location weur`
   `npx wrangler r2 bucket create plotart-studio-test-images --jurisdiction eu`
   `npx wrangler r2 bucket create plotart-studio-test-applications --jurisdiction eu`
   An Access application for `plotart-studio-test.<subdomain>.workers.dev` allowing Colin's own test addresses; a Cloudflare
   API token limited to those two Workers and the test database and buckets.
3. **Test database schema and synthetic data** (TEST database only):
   `npx wrangler d1 execute plotart-checkout-test --remote --file worker/plotart-studio/schema.sql`
   `npx wrangler d1 execute plotart-checkout-test --remote --file worker/plotart-studio/migrations/0013_gallery_artist_agreement_text.sql`
   `node worker/plotart-studio/test/checkout-test-env-seed.mjs --target plotart-checkout-test --founding <colin+f1@…> --gallery <colin+g1@…> > seed.sql`
   `npx wrangler d1 execute plotart-checkout-test --remote --file seed.sql`
4. **GitHub environment `checkout-test`** (required reviewer: Colin). Variables: `CHECKOUT_TEST_D1_DATABASE_ID`,
   `CHECKOUT_TEST_ACCESS_AUD`, `CHECKOUT_TEST_ACCESS_TEAM`, `CHECKOUT_TEST_ORIGIN`, `CLOUDFLARE_ACCOUNT_ID`. Secrets:
   `CHECKOUT_TEST_CF_TOKEN`, `CHECKOUT_TEST_STRIPE_SECRET_KEY`, `CHECKOUT_TEST_STRIPE_WEBHOOK_SECRET`,
   `CHECKOUT_TEST_FOUNDER_EMAILS`. (Values entered by Colin directly in GitHub; never in chat or files.)
5. **Merge to main** (Colin's approval) — the workflow only deploys commits on main.
6. Run **PlotArt checkout pilot deploy** with `target = test`, `dry_run = true`; then `dry_run = false`,
   `enable_test_pilot = true`. The workflow builds with the TEST ONLY texts, renders the test configs, refuses non-test
   Stripe credentials, deploys both test Workers, writes their secrets and checks them from outside (`/v1/status`).
7. Run the Stripe test-API checks below.

Production stays untouched by all of this. Production pilot activation additionally needs: migration 0016 (and 0017
for issued texts) through `studio-d1-migration.yml`, issued texts, a code change to accept live keys, and Colin's approval.

### What is tested, mocked or unverified

| Area | Status |
|---|---|
| Commission rules, Founding protections, consent gates, reservations, duplicate prevention, event idempotency and ordering, refunds incl. pending/failed, disputes, linked-purchase refusal, transit-insurance rules, access control, retention, records surviving the real deletion schedule | **Tested locally** against the real Workers and D1 (Miniflare); **Stripe mocked** (107 checks) |
| Migration 0016 on the pre-change schema | **Tested** (9 checks) |
| Deployment configs, guards, TEST ONLY build guard, seed, outside check | **Tested locally**; `wrangler deploy --dry-run` **builds all three configurations** (26 checks). Workflow never run in GitHub. |
| Stripe API behaviour (request shapes accepted, controller combination, onboarding requirements, event payloads, timing) | **Unverified** — mock only |
| Cloudflare deployment, Access, real webhook delivery, secrets | **Unverified** |
| Stripe fees, dispute fee amount | From Stripe's published pages via search; Irish pricing page not directly retrieved — re-check before issuing texts |
| Legal effect of texts, VAT, DAC7, AML position | **Not assessed** — professional advice outstanding |

### Stripe test-API checks still needed (test environment)

1. **Onboarding:** account created with the controller settings (read back `controller`); Account Link completes with
   Stripe's test data; `account.updated` arrives and sets `charges_enabled`/`details_submitted`; an incomplete account is
   refused a quote. Also a GB (Northern Ireland) account.
2. **Payment:** Checkout Session created on the connected account with the exact line items, `application_fee_amount`
   and `expires_at`; pay with `4242 4242 4242 4242`; `checkout.session.completed` delivered to the Connect endpoint with
   the right `account`; order paid only then; application fee visible on the platform; 0% order creates no fee.
3. **Webhook delivery:** signature verified with the real secret; Stripe retries after a deliberate 500 (deferred
   event); resend from the Dashboard is recognised as duplicate; events for the artist's own non-PlotArt payments ignored.
4. **Expiry and abandonment:** a session left to expire produces `checkout.session.expired` and releases the work.
5. **Full refund:** succeeded; ledger and application-fee refund (full commission) match; order refunded.
6. **Partial refund:** e.g. €500 of €1,000 artwork → fee refund €75; then a delivery-only refund → no fee refund.
7. **Refund with insufficient balance:** pay with a normal card (funds pending), refund immediately → expect `pending`;
   confirm nothing booked; top up or wait; confirm `refund.updated` succeeded → booked once. With `4000000000005126`
   (refund fails asynchronously) → `refund.failed` flags the order and returns no commission. Use `4000000000000077`
   where funds must be available immediately.
8. **Commission refunds:** application fee refunds created with the exact amounts and idempotency keys; repeated
   events do not double-refund.
9. **Disputes:** test dispute cards (e.g. `4000000000000259`) → `charge.dispute.created`; respond with Stripe's
   winning/losing test evidence → `charge.dispute.closed` won/lost; lost → founder "commission only" refund works; check
   the dispute fee lands on the connected account.
10. **Reconciliation:** interrupt a webhook (endpoint disabled), complete a payment, then "Reconcile with Stripe".
11. **Live refusal:** confirm a live key in the test Worker is refused before any request.

### Remaining before a real (live) pilot transaction

- Colin's decisions: D1 processing-fee bearer; D3 retention; approval of PA-PAY and PA-BPT; each setup step.
- The Stripe test-API checks above, in the separate test environment.
- Professional advice: marketplace and consumer responsibilities, commission VAT, DAC7, and PlotArt's AML position.
- Privacy notice update for buyer checkout data and Stripe as recipient.
- A willing artist, a real artwork, a transporter quote and **confirmed transit insurance** for that shipment.
- Production: migrations 0016/0017, issued texts, a deliberate code change to accept live keys, and explicit approval.
- Not built: automatic emails, PlotArt commission invoices (manual under GAA 8), ledger CSV export, AML "verified purchase" path.

#### Real-Stripe test stage: key permissions and how runs start (16 Nov 2026)

Model A (the artist bears Stripe's fees) is used **for technical testing only**. This is not approval of the production
fee model, the draft terms or the retention periods.

**Use a restricted test key in a dedicated Stripe sandbox.** Every other resource stays at *None*. The key needs:
- **Permissions column** (PlotNua's own platform account):
  - *Connect → Accounts*: Write (create the test connected account and read it).
  - *Connect → Account Links*: Write (the onboarding link).
  - *Connect → Application Fees*: Write (read fees and refund commission).
  - *Stripe CLI permissions*: Write, so that `stripe listen` can relay signed webhook events to the job.
- **Connect Permissions column** (calls made on the artist's test account):
  - Checkout Sessions: Write.
  - Payment Intents: Write (the harness makes test payments).
  - Charges and Refunds: Write.
  - Payment Disputes: Write (to submit Stripe's test evidence).
  - Payment Methods: Read.
  - Balance: Read.

If Stripe refuses a call, the run records Stripe's permission error and that check fails; nothing else is affected.
Specifically, if Stripe does not allow `stripe listen` with a restricted key, the signed-webhook checks are reported as
untested. The fallback is that sandbox's own secret test key, whose reach is limited to that sandbox.

**How runs start without merging.** GitHub only offers "Run workflow" (`workflow_dispatch`) for workflows on the default
branch, so the runner is started by a **push** to the pilot branch that changes `test/stripe-test-run.json`. That works
from the unmerged branch. Each run then waits for Colin's approval on `checkout-test`. The environment must exist before
the first run, because GitHub creates a missing environment automatically with no protection rules.
