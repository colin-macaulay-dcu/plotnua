# PlotArt: Delivery Safety Improvements (implementation report)

**Date:** 22 November 2026
**Branch:** `plotart/delivery-safety`, based on `main` at `305e0af`
**Status:** for review only. Nothing has been merged, migrated or deployed, and no production setting has changed.

**Starting point:** the read-only Checkout Delivery Safety Audit of 22 November 2026. It found that live checkout and the basket are on in production, and that 0 of 108 artworks can be bought.

## Summary

| # | Brief item | Done | Where |
|---|---|---|---|
| 1 | Founder approves every delivery offer; a material change voids the approval; on the Review Desk | Yes | `src/basket.js` (`offerReview`, `adminOffers`, `reviewOffer`, check in `lineFor`); `src/index.js` routes; `ui/checkout-pilot.js` (Review desk → Basket readiness → "Delivery offers to review") |
| 2 | Overdue dispatch and delivery alerts: no duplicates, full details, testable | Yes | `src/checkout.js` (`overdueState`, `overdueCheck`, called by `sweep` every 15 min); `order_overdue_alerts` table |
| 3 | Ireland-only delivery shown before checkout | Yes | `src/basket-public.js` (notice above the basket and form; county label); `atlas-tools/plotart_gallery_pages.py` (artwork-page basket note) |
| 4 | Offshore islands by enquiry unless the approved offer covers them | Yes | `src/checkout-rules.js` (`OFFSHORE_ISLANDS`, `islandMatch`); `src/basket.js` (`cleanBuyer`, `openBasket`); basket page question |
| 5 | Existing price, insurance, return terms, basket, Stripe direct charges, refunds and enquiry routes preserved | Yes | No change to `stripe.js`, refunds, commission or terms; the existing proofs all pass |
| 6 | Founder-only routes, audit records, nothing buyable without every approval | Yes | Founder gate on `/api/admin/*` plus the `X-Studio` header; append-only tables enforced by triggers; proof DS21 |
| 7 | No international payment through the single-artwork quote route | Yes | `src/checkout-rules.js` (`QUOTE_DESTINATIONS = ['IE']`, `checkQuoteDestination`); applied in `updateOrder`, `priced` (send and issue) and `startCheckout` |
| 8 | Tests, report, migrations; nothing activated | Yes | `migrations/0022_delivery_safety.sql`; `test/prove-basket.mjs` (+27 checks); `test/prove-checkout-pilot.mjs` (+5 checks) |

## How each item works

### 1. Founder approval of delivery offers

**When an offer can be sold**
- The artwork is offered in the basket only while the founder's latest review approves the offer's current version and its fingerprint.
- The fingerprint is a SHA-256 of the canonical form of: artwork, version, delivery charge, and every delivery field. The fields include the charge, insurance, deadlines, returns and islands.

**What voids an approval**
- Every save by the artist creates a new version, and a new version is never approved.
- A withdrawal also voids the approval.
- So any change, material or not, sends the work back to enquiry-only until the founder reviews it again. Because an identical re-save also needs a fresh review, the rule is stricter than "material change".
- Approval is also refused if the founder's page is out of date. The request must carry the version and fingerprint the founder was shown; otherwise it gets a 409.

**What approval checks again**
- the artwork has a price;
- the insurance cover is at least the price;
- the return arrangements are complete;
- the dispatch and delivery deadlines are present.

The founder must also tick an explicit review statement.

**Returning an offer**
- Returning an offer needs a note, which the artist sees in Studio.
- Returning works even for an offer that is already approved, which withdraws that approval.

**Audit records**
- `delivery_offer_reviews` is append-only (no update or delete). A trigger refuses a review of anything except the current, unwithdrawn version.
- `delivery_offer_events` records every save and withdrawal by the artist.

**Safe by default**
- If migration 0022 is missing, nothing is approved and every artwork stays enquiry-only.
- A review made in test mode never opens live purchase.

**Founder screen:** Review desk → Basket readiness. Waiting and returned offers are shown in full, with the charge, deadlines, islands, insurance, cover confirmation and returns, any problems flagged, and an Approve or Return action. Approved offers are collapsed under "Approved offers (n)". The readiness table now shows "x of y approved".

**Artist screen:** each offer shows "Waiting for PlotArt to review it", "Reviewed and approved by PlotArt", or "Returned by PlotArt", with the note. The offer form now asks for two required deadlines, "Dispatch within" and "Delivered within", in days after payment. Islands are an optional yes/no, defaulting to no.

### 2. Overdue dispatch and delivery alerts

**Deadlines**
- Each deadline is the agreed number of Irish calendar days from the Irish date of payment, ending at the end of that Irish day.
- Basket offers must now include `dispatch_days` and `delivery_days`: dispatch 1–60 days, and delivery no earlier than dispatch and at most 90 days.
- Older quote orders with no agreed days use labelled defaults of 14 and 30 days.

**Which orders are watched:** orders with status paid, dispatched, refund pending or disputed that are not yet delivered.
- Recording dispatch stops the dispatch alert.
- Recording delivery stops both.
- Refunded and closed orders are not watched.

**Duplicate prevention:** the `order_overdue_alerts` table has the key (order, kind). The key is claimed with `INSERT OR IGNORE` before the alert is sent, so overlapping sweeps cannot both send it.

**What an alert contains**
- the order reference and basket reference;
- the artwork title and artist;
- the payment date and due date;
- days overdue, order status and fulfilment status;
- the delivery window shown to the buyer;
- whether the deadline was agreed or a default;
- the next step under PA-BBT 6.2 and PA-BAA 8.3.

**How alerts reach the founder**
- Alerts use the existing founder-alert path, so they appear in the alerts panel with an OVERDUE flag. They are emailed where checkout mail is approved.
- If no founder address is set, the alert is still kept in the panel and marked "EMAIL FAILED".

**Schedule:** checks run on the existing checkout Worker cron (every 15 minutes), with nothing new to deploy for scheduling.

**Testability**
- `overdueCheck(env, at)` and `overdueState(order, at)` take the time as a parameter.
- The proof drives the real `scheduled()` handler.

### 3. Ireland-only delivery shown before checkout

**Basket page:** a notice above the items and the address form reads: "Online purchase delivers to addresses in the Republic of Ireland only. Offshore islands only where an artwork's delivery offer includes them. For delivery anywhere else, please enquire about the artwork."
- Each artwork shows "Delivery in the Republic of Ireland (mainland; offshore islands by enquiry)" or "…including offshore islands".
- The county field is labelled "County (Republic of Ireland)".
- `/api/basket/items` returns `delivery_scope`.

**Artwork pages:** the generator's basket note adds: "Online purchase delivers in the Republic of Ireland only; for delivery elsewhere, please enquire."
- This takes effect at the next gallery publish after merge.
- The 110 committed artwork pages are not rebuilt in this branch.

### 4. Offshore islands

**The buyer's answer**
- The buyer must answer "Is this address on an offshore island (not connected to the mainland by road)?"
- The address is also checked against a list of island names (Aran Islands, Tory, Arranmore, Inishbofin, Clare Island, Cape Clear, Sherkin, Bere and others). Accents are ignored, and Achill and Valentia, which have road connections, are treated as mainland.
- A match counts as an island even if the box says "no".

**What happens next**
- An island address is accepted only if every artwork's approved offer includes islands.
- Otherwise the buyer is told to remove that artwork and enquire about it.
- This is checked both on the page and on the server. The island marker is saved on the order's delivery address.

### 7. Single-artwork quote route

- Quotes now need a `destination_country`.
- Only `IE` can be priced, sent, issued or paid until the founder approves an international delivery policy.
- A quote issued before this change has no country, so its payment link is refused before any reservation or Stripe session is made. No such live quote is known: the route already refuses commission-free orders, which covers every Founding sale.
- The founder's quote template now includes `destination_country: 'IE'` and example deadlines.

## Migration 0022 (new tables only)

- **File:** `migrations/0022_delivery_safety.sql`
- **SHA-256:** `85ccf0162566d41c049851ec737b28952701cc9ee2c8d1a2b680f8f3bc0d52af`
- **Contents:** three new tables (`delivery_offer_events`, `delivery_offer_reviews`, `order_overdue_alerts`) and their triggers. Nothing existing is altered.
- **Re-runnable:** it uses `IF NOT EXISTS` throughout.
- **Migration-check class:** the triggers put it in the "destructive" class, so back up the database first.
- **Release safety:** `render-checkout-config.py` now refuses to enable the live basket unless 0022 is in the release. The test-environment workflow applies 0022 before the seed.

## Test results (local; Miniflare with the mock Stripe API)

| Proof | Before | After |
|---|---|---|
| `test/prove-basket.mjs` | 114/114 | **142/142**: M5 plus DS1–DS26, covering approval, version and fingerprint invalidation, founder-only, audit triggers, deadlines, islands, Ireland-only notice, every-artwork check, overdue alerts and no duplicates |
| `test/prove-checkout-pilot.mjs` | 282/282 | **287/287**: IN1–IN5, covering GB, US and FR quotes refused, country required, and an issued quote without a country cannot be paid |
| `prove-checkout-deploy`, `prove-live-enable`, `prove-live-gate`, `prove-payment-terms-ready`, `prove-migration-0017-launch` | pass | pass (24, 47, 58, 30, 27) |
| `atlas-tools/prove-plotart-basket-button.py` | 4/4 | 4/4 |
| `prove-basket-staging`, `prove-basket-test-seed`, `prove-basket-e2e-offline` | already failing in this environment | identical results before and after; these failures pre-date this work and are environment-related |

**Seed fingerprint:** the staging seed writes test-only founder reviews. I checked that the seed's fingerprint equals the Worker's.

**Not run here:** `stripe-testmode-basket-e2e.mjs`, which needs real Stripe test keys in CI. It has been updated: migration 0022, founder approval of offers, deadlines, and the buyer's island answer.

## What happens on deployment (when approved)

1. Merge to `main`.
2. Back up the production database, then apply migration 0022 through `migration-check.py`.
3. Deploy the checkout and Studio Workers through the existing protected workflows.

Until the founder approves an offer, no artwork becomes buyable. That is the same as today, since 0 of 108 are buyable now.

## Not changed (by design)

- Commission rules, PA-BAA, PA-BBT and PA-PAY texts.
- Stripe Connect direct charges, authorise-then-capture, refunds and disputes.
- Enquiry and direct-sale routes.
- Artist data.

**Terms wording:** the deadlines and the island limit are consistent with PA-BBT 2.3 and 6.2 and PA-BAA 5 and 8. The terms could mention the island limit explicitly at their next revision; this needs your decision.

## Open decisions for the founder

1. Approve this branch for merge and the 0022 migration.
2. Islands: confirm the default (excluded unless the offer includes them) and the list of island names.
3. Deadlines: the limits are calendar days (dispatch up to 60, delivery up to 90). The defaults for older quotes are 14 and 30 days.
4. International: the quote policy stays Ireland-only until a policy is approved, which needs the legal and tax advice listed in the audit.
