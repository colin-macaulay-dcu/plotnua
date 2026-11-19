# PA-PAY / PA-BPT DRAFT r5: internal review notes

17 November 2026 · **internal only; not customer-facing** · both drafts unissued · existing agreements (PA-FAA, PA-GAA, PA-GPIL) unchanged.

Sources checked:
- the issued PA-FAA-2026-11 and PA-GAA-2026-11 (HTML in `agreements/issued/`);
- the pilot code on `plotart/managed-checkout-pilot` (`src/checkout.js`, `checkout-public.js`, `stripe.js`, `mailer.js`, migration 0016, `wrangler*.toml`);
- Stripe test runs 1–18;
- CCPC guidance and the Consumer Rights Act 2022 (s.106–107, s.115, Schedules 3–4);
- Stripe's receipts documentation.

---

## 1. Change table (r4 → r5)

| # | Review point | PA-PAY r5 | PA-BPT r5 |
|---|---|---|---|
| 1 | Fee model | The assertion that Stripe fees fall outside the "at least 85%" promise is removed. New cl. 0.2 says nothing reduces existing rights, Founding protections are restated, and the artist's agreement prevails on any conflict. Cl. 3.3 carries drafting Alternatives A and B. The example table shows who bears what under each, with fee and VAT lines kept separate. | — |
| 1a | "More favourable term applies" (old cl. 0) | Replaced. That rule would have made every pilot obligation that is less favourable to the artist (insurance, return information) unenforceable. New cl. 0.2–0.3 protects existing rights and adds pilot-only conditions by express acceptance. | — |
| 1b | Collecting commission | New cl. 3.2: on pilot orders, commission is collected as a Stripe application fee instead of by PA-GAA cl. 8 invoice. | — |
| 2 | Cancellation and returns | New cl. 7.2: return method, address and return-cost estimate are required on every quote. Cl. 7.3 covers refund timing, standard delivery, withholding the refund until the work is returned or proof of sending, and diminished value. Faulty work: the seller pays return costs. | New s.6 (change of mind): 14 days from receipt; how to cancel; returns within 14 days; buyer pays the stated return cost; refund of price and delivery within 14 days; withholding rule; handling. New s.7 (damaged, faulty or misdescribed): 30-day right to reject; seller pays return. New s.11: model cancellation form. |
| 3 | Damage reporting | — | s.5.2: the 48-hour report is a request, not a condition. Reporting later does not affect the buyer's rights. |
| 4 | Seller information | New cl. 2.2: the artist must provide legal name, address, email, phone, trader status and VAT number. Cl. 4.1 lists what the quote shows. Cl. 2.5: PlotArt may receive cancellations and complaints on the artist's behalf. | s.1.1–1.3: seller identity and contacts, the trader declaration with its consequence if the seller is not a trader, and how obligations are shared between seller and PlotArt (CRA 2022 s.107). |
| 5 | Reservations | Cl. 4.3 matches the code: a quote does not hold the work. The work is held only from checkout opening, for 31 + 15 minutes. If several quotes are open, the first confirmed payment wins. | s.4 says the same, with the times stated. |
| 6 | Privacy | "Never sees bank details" and "only email and country" are replaced by cl. 9.1–9.4: what is sent to Stripe, what is received and stored, what the artist sees, and that full card numbers never reach PlotArt or the artist. What PlotArt can view through its Stripe access is bracketed pending the access probe (section 4). | s.9 rewritten the same way. |
| 7 | Notifications and receipts | Removed: "tells the artist the same day", "PlotArt tells the artist and the buyer the same day", and the 7-day and 30-day reminder promises. Replaced with "when it becomes aware". | Removed "you will receive Stripe's receipt by email". s.3.2 reserves the durable-medium confirmation for completion before live payments. |
| 8 | Test versus live | New cl. 10: test acceptances, consents and accounts never become live ones. Live use needs acceptance of the issued live version, fresh consent under cl. 3.6, and live Stripe onboarding. Cl. 3.6 consent is tied to the addendum version. | — |
| 9 | Consistency | Cl. 7.7: commission returns are aligned with PA-GAA cl. 9, including the 30-day limit, with lost disputes and reversed refunds stated. Cl. 8 retention is unchanged. Insurance stays a pilot condition under cl. 0.3. Conflicts are flagged in section 2 below, not rewritten. | — |
| — | Housekeeping | Founder decisions, evidence notes and revision history moved out of the customer text into these notes. | Same. |

## 2. Conflicts with existing agreements or with the code (flagged, not resolved)

| # | Conflict | Where | What is needed |
|---|---|---|---|
| C1 | PA-GAA 5.2 says the artist "pays no more than 15% of the Commission Base in total". Under Alternative A, Stripe's processing fee is also deducted from the artist's balance on pilot orders. Whether a third-party processor's fee counts towards that promise is not settled. | PA-GAA 5.1–5.2; PA-PAY 3.3 | A legal view, or choose Alternative B. r5 no longer asserts that the fee falls outside the promise. |
| C2 | PA-FAA 3.4: during the founding year "PlotArt charges no sales commission and no other charge of any kind". In the pilot, Stripe's fee applies to Founding Enquiry orders. It is not a PlotArt charge, and the pilot needs separate consent with direct payment remaining the normal route (cl. 3.6). | PA-FAA 3.4; PA-PAY 3.6 | A legal view on whether this is consistent. Alternatively, do not offer the pilot for orders with no commission (decision F4). |
| C3 | PA-FAA 3.5: "PlotArt does not ask for payment-card or bank details for the gallery." The pilot does not ask either: Stripe onboarding is hosted by Stripe. What PlotArt's key can read is pending the probe (V1–V3). | PA-FAA 3.5 | Confirm with the probe and word the privacy notice to match. |
| C4 | PA-GAA cl. 8 collects commission by invoice within 30 days; pilot orders use an application fee. | PA-GAA 8; PA-PAY 3.2 | Acceptance of PA-PAY is express acceptance of this collection method for pilot orders. Confirm this does not count as a "change" under PA-GAA 20.2 needing a new GAA version. |
| C5 | Lost disputes: PA-GAA 9.1 covers sales "cancelled or fully refunded". A lost chargeback is not named. The pilot treats it as fully refunded, but only flags a founder action; returning commission is not automatic. | PA-GAA 9.1; code `recordDispute` | PA-PAY 7.7(c) commits to return within the PA-GAA 9 period. A reliable operational process (or automation) is needed so the 30-day limit is met. |
| C6 | Reversed refund where the buyer ultimately does not need repaying (for example, a claim withdrawn). PlotArt has returned commission on a sale that stands. PA-PAY 7.7 says commission is not returned twice, but does not say how PlotArt recovers commission it is again owed. | PA-PAY 7.6–7.7; PA-GAA 9 | Decide whether the commission is re-invoiced under PA-GAA cl. 8, or left. |
| C7 | Retention: PA-FAA 5.5 deletes buyer name, email and message 24 months after an enquiry. A pilot order keeps the buyer's email until 31 December of the sixth year after the last money movement. These are different records for different purposes. | PA-FAA 5.5; PA-PAY 8.1; PA-BPT 9.1 | The privacy notice must explain both (section 6). The retention periods still need confirming with the accountant (decision F7). |
| C8 | Insurance: PA-GAA 4.3 leaves shipping and insurance between the artist and the collector. The pilot requires confirmed transit cover for every shipment. | PA-GAA 4.3; PA-PAY 6.2 | Covered by express acceptance of a pilot-only condition (cl. 0.3). Confirm the commercial position (decision F8). |
| C9 | Processing consent is not tied to an addendum version in the code. A test-mode consent would carry over to a live version. | code `processingConsent`, `membership` | Necessary fix N4. |

## 3. Remaining founder decisions

| # | Decision |
|---|---|
| F1 | Fee model: Alternative A (artist bears Stripe's fee) or B (PlotArt absorbs it from commission on commission-bearing orders, with or without VAT, and including or excluding the delivery portion). |
| F2 | Whether the pilot is open only to artists who declare they sell as traders. Recommended: otherwise buyers lose EU consumer rights (PA-BPT 1.2). |
| F3 | Whether a quote should hold the work in PlotArt's systems for its whole validity (up to 7 days), rather than only during checkout. r5 describes current behaviour; a change would need code (optional O2). |
| F4 | Whether orders with no commission (Founding Enquiries) are offered through the pilot at all, given C2. |
| F5 | Who responds to disputes, given the €20 countered fee: the artist only, or PlotArt on the artist's behalf. |
| F6 | Returning commission after a lost dispute: automatic, or a founder action with a 30-day process (C5). Also how C6 is handled. |
| F7 | Retention periods (confirm with the accountant). |
| F8 | Transit insurance required for every pilot shipment (C8), and who arranges the return insurance. |
| F9 | Buyer receipt or invoice: rely on the artist's Stripe receipt; have PlotArt pass `receipt_email`; or send PlotArt's own confirmation email (section 5). |
| F10 | The mail provider for buyer and artist notifications (currently none), and who monitors refund escalations. |

## 4. Implementation gaps

### Necessary before any live use (some also before realistic buyer testing)

| # | Gap | Evidence |
|---|---|---|
| N1 | **Seller information on the quote:** the seller snapshot has only the display name, an optional legal name, role, the Stripe account country, and PlotArt's contact address. It needs: geographical address, returns/complaints address, seller email, phone, trader declaration and VAT number. These require new artist profile fields, inclusion in the quote snapshot, and display. | `issueQuote` seller object; `checkout-public.js` quote HTML |
| N2 | **Return information on the quote:** only a free-text `return_route` exists. It needs: return method, return address, return-cost estimate (cents), and who arranges the return. The quote must not issue without them. | `buyerQuote` delivery fields |
| N3 | **Pre-contract and confirmation information:** the cancellation information and model form must be shown before payment (via the PA-BPT terms link: check that it is acceptable as "made available"). A **durable-medium confirmation** after payment is also needed, and there is none today: `MAILER = "none"` and no buyer emails exist in the code. | `mailer.js`; `wrangler*.toml` |
| N4 | **Processing consent tied to the addendum version:** record the `doc_id` in the consent event, and require it to match the current addendum (C9). Test and live acceptances are already separated by `doc_id` for the addendum itself. | `processingConsent`, `membership`, `requireProcessingConsent` |
| N5 | **Notifications:** no mailer is configured. Artist and founder emails exist only for refund pending, failed and reversed, and never for payment confirmed, dispute opened or lost, or cancellation received. Nothing is ever sent to buyers. Either configure the mailer and add these, or document Studio-based monitoring with a named owner and frequency. The drafts now promise nothing automatic. | `notify()` call sites |
| N6 | **Commission return after a lost dispute** within the PA-GAA 30-day limit: an alert or queue in Studio, or automation (C5). | `recordDispute` |
| N7 | **Unfunded-refund behaviour:** run the second-account test and finalise PA-PAY 7.5. | Prepared; awaiting Colin's onboarding |
| N8 | **Privacy access probe:** run V1–V5 and finalise PA-PAY 9.2 and PA-BPT 9.2(c), and the privacy notice. | Prepared (`privacy` phase) |

### Optional improvements

| # | Improvement |
|---|---|
| O1 | Pass `payment_intent_data.receipt_email` so Stripe sends a receipt in live mode even if the artist's "Successful payments" setting is off (Stripe documents this for direct charges). Decision F9. |
| O2 | Hold the work for the whole quote validity, or prevent a second open quote for the same work (decision F3). |
| O3 | Online cancellation form with an automatic acknowledgement on a durable medium (CRA s.115(3)–(4)). |
| O4 | Automate commission return on lost disputes (F6). |
| O5 | Studio alert for a negative artist Stripe balance after a refund (read Balance, which is already permitted). |
| O6 | Implement Alternative B mechanics if chosen: partial application-fee refund after the balance transaction, using existing permissions. |

Already changed in this round: the pilot no longer requests `identity` when reading the artist's v2 account (data minimisation; local checks 145/145).

## 5. Notifications and receipts: what works today

| Item | Actually works? | Dependency or manual responsibility |
|---|---|---|
| Stripe payment receipt to the buyer | **Not in test mode** (Stripe sends none). In live mode, only if the **artist's** Stripe "Successful payments" setting is on, because for direct charges receipts use the connected account's settings. The pilot passes `customer_email`, not `receipt_email`. | The artist's Stripe settings, or O1 |
| Stripe refund receipt | Live mode only, if the artist's "Refunds" email setting is on | The artist's Stripe settings |
| PlotArt confirmation to the buyer | None | N3 |
| PlotArt emails to the artist or founder | Code exists for refund pending, failed and reversed only; **sends nothing** (`MAILER = "none"`) | N5 / F10 |
| Studio status for the artist | Yes: order status, paid, refunds and flags are visible in Studio | The artist checks Studio |
| Refund escalation at 7 and 30 days | Records the event and flag; the email part sends nothing | The founder monitors Studio flags |
| Buyer return page | Shows "confirmed" only after Stripe's signed event | — |

## 6. Privacy notice changes needed (plotnua.ie/privacy.html)

1. **New processing purpose:** the managed-checkout pilot, covering buyers and artists. Lawful bases: contract (buyer and artist); legal obligation (tax records); legitimate interests (fraud prevention, linked-purchase limit).
2. **Buyer data:** the email received with the quote; the order record; ledger and event identifiers; retention until 31 December of the sixth year after the last money movement, or two years if never paid; legal holds.
3. **Recipients:**
   - Stripe, as an independent controller for payment processing (link to Stripe's privacy policy);
   - the artist-seller, who sees the payment details on their Stripe account;
   - Cloudflare, as hosting processor;
   - any mail provider, once one is configured.
4. **What PlotArt can access through Stripe without storing it:** wording per the probe results (V1–V5).
5. **Artist data for the pilot:** Studio email and country sent to Stripe; account status and requirement names received; opt-in and consent records kept for six years after leaving the pilot.
6. **The difference from enquiry retention:** enquiry data is deleted after 24 months under PA-FAA 5.5; pilot order records are kept longer.
7. **International transfers:** Stripe and Cloudflare, if applicable.
8. **The test-mode statement:** removed when live.

## 7. Points needing professional legal or tax review

**Legal (consumer and contract)**

1. Whether PlotArt is an "online marketplace" provider under CRA 2022 s.107 and the Consumer Protection Act 2007 s.46 as amended, and whether PA-BPT 1.3 satisfies the duty to say how obligations are shared.
2. Whether presenting the cancellation information and model form through the linked PA-BPT terms meets CRA s.106. Also the form and timing of the durable-medium confirmation.
3. The return-cost estimate approach for artworks that cannot normally be returned by post, and the diminished-value wording.
4. Allowing sellers who are not traders (F2), and the consequences if it is allowed.
5. C1 and C2: whether Stripe's fees on pilot orders are consistent with PA-GAA 5.2 and PA-FAA 3.4.
6. C4: whether the change in commission collection needs a GAA version change under cl. 20.2.
7. C6: whether commission is owed again where a reversed refund ends with no repayment due.
8. PlotArt receiving cancellations and complaints as the seller's agent (PA-PAY 2.5).

**Tax**

9. VAT on PlotArt's commission when it is collected as an application fee. Also invoicing obligations if PlotArt is VAT-registered (PA-GAA 5.2 says the invoice shows VAT).
10. VAT on Stripe fees under Alternative B: if PlotArt absorbs them, who reclaims what.
11. DAC7 reporting for platform operators.

**Regulatory**

12. Anti-money-laundering position for art sales, including the €10,000 threshold scope.
13. Privacy: controller and processor roles for Stripe and the artist; the privacy notice text in section 6.

## 8. Evidence and sources

- **CCPC guidance:**
  - the cancellation period for online purchases is 14 days from receipt, with a further 14 days to return;
  - the refund is due within 14 days of being told of the cancellation, subject to receiving the goods back;
  - for faulty goods there is a 30-day short-term right to terminate, and the business pays the return cost.
- **CRA 2022:**
  - s.106: the model cancellation form must be given before the contract binds;
  - Schedule 3(n): the cost of returning goods that cannot normally be returned by post must be stated;
  - s.107: online marketplace information, including trader status and how obligations are shared;
  - s.115: how a consumer may cancel.
- **Stripe receipts:**
  - live mode only;
  - for direct charges, the connected account's Customer emails settings apply;
  - `receipt_email` causes Stripe to send a receipt even if the setting is off.
- **Code:**
  - reservation is created in `startCheckout` for the session length (31 min, `SESSION_MINUTES` + 1) plus `RESERVATION_GRACE_MINUTES` = 15;
  - quotes last 1–7 days (`MAX_QUOTE_DAYS`, default 3);
  - several open quotes per work are possible;
  - `notify()` goes only to the artist and `CHECKOUT_NOTIFY_EMAIL`;
  - `MAILER = "none"` in the Studio and enquiry Workers; the checkout Worker has no mailer setting.
