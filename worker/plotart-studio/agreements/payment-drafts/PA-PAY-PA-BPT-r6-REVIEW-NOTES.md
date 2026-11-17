# PA-PAY / PA-BPT r6 — internal review notes (17 November 2026)

**Internal. Not customer-facing. Neither draft is issued, accepted or installed.** These notes replace the r5 notes for anything they cover. The r5 notes stay in this folder as history.

## 1. What changed from r5 to r6

| # | Area | PA-PAY r6 | PA-BPT r6 |
|---|---|---|---|
| 1 | Fee model (founder decision, 17 Nov 2026: Model B) | Cl. 3.3: PlotArt reimburses Stripe's **actual** processing fee and the VAT Stripe charges on it, on the whole payment including delivery. It is paid by a partial application-fee refund once Stripe records the fee. The combined deduction for commission and processing is no more than the commission. The Alternative A/B brackets are removed. | No change (buyer-facing amounts are unchanged). |
| 2 | Scope of the reimbursement | Cl. 3.4: processing fee and its VAT only. It does not cover dispute fees, optional-service, currency-conversion or payout fees, reverse-charge VAT the artist self-accounts, or a negative balance. | — |
| 3 | Shortfall | Cl. 3.5: if what PlotArt owes is more than what is left of the application fee, PlotArt pays the difference directly by bank transfer within [30] days and records it. Examples 3 and 4 show when this happens. | — |
| 4 | Examples | Cl. 3.7 is rewritten for Model B: completed sale; partial refund; full refund (with shortfall); small artwork with large delivery on an international card (shortfall at payment). Other cards, and accounts outside Ireland, are covered in a note. | — |
| 5 | Statements | Cl. 3.8 lists the lines in the artist's statement. Cl. 3.2 keeps commission recorded at its full amount, with the reimbursement as a separate line, and brackets an invoice where the law requires one. | — |
| 6 | Commission-free orders | Cl. 1.3(a) and 0.2(a): orders with no PlotArt commission, including every Founding Enquiry, are not taken through the pilot. Old cl. 3.6 (separate processing consent) and 10.2(b) are removed. | — |
| 7 | Reservation (r5 inconsistency) | Cl. 4.3: only one open quote per work at a time, as the code now enforces. The artist must not sell elsewhere while a quote is open. The checkout-period block is unchanged. The r5 text "first confirmed payment wins among several open quotes" is removed. | S.4.1–4.2 match: no second quote is issued, the quote is not a guarantee, and the checkout block is described. |
| 8 | Pending refund vs direct repayment (r5 inconsistency) | Cl. 7.5 keeps the rule against direct repayment while a refund is pending, adds why (double repayment), and keeps the artist responsible for the legal time limit. | S.8.2 no longer tells the buyer the seller repays directly while a refund is "delayed". Direct repayment is only for a failed or reversed refund (s.8.3). |
| 9 | Retention (r5 inconsistency) | Cl. 8.1 now matches the code. Paid orders are kept to 31 December of the sixth year after the order is **settled**; the date is fixed then. Later disputes or claims are covered by a legal hold. Opt-in records are kept for six years after leaving, or as long as any order is kept. Enquiry messages are separate. | S.9.1 uses the same rule and wording (settled, holds reviewed every 12 months, enquiry separate). |
| 10 | Refund and commission interaction | Cl. 7.4: the reimbursement is not reversed on refund. Cl. 7.7: the reimbursement already returned is taken into account, and the excess is paid directly under cl. 3.5. Cl. 7.8: dispute fees are not reimbursed, and the reimbursement is not reversed by a dispute. | — |

## 2. Conflicts and their status

| # | r5 conflict | Status in r6 |
|---|---|---|
| C1 | Stripe's fee vs PA-GAA 5.2 (artist pays at most 15% in total) | **Addressed by Model B**: the artist's combined deduction never exceeds the commission. The reimbursement is reliable only if shortfalls are paid (cl. 3.5); see N-B2. |
| C2 | Stripe's fee on Founding Enquiry orders vs PA-FAA 3.4 | **Removed**: commission-free orders are refused by the pilot (code `requireCommissionBearing`) and excluded by cl. 1.3(a). |
| C3 | PA-FAA 3.5 card and bank details | Unchanged. Pending the privacy probe. |
| C4 | Commission by application fee vs PA-GAA cl. 8 invoice | Unchanged. Cl. 3.2 now brackets an invoice where the law requires one. |
| C5 | Lost-dispute commission return | Unchanged (founder action, flagged). |
| C6 | Commission owed again after a reversed refund that ends without repayment | Unchanged. Under Model B, any shortfall paid for that refund also stays paid. |
| C7 | PA-FAA 5.5 enquiry deletion vs order retention | **Clarified** in PA-PAY 8.1 and PA-BPT 9.1 (separate records). The periods still need the accountant's confirmation. |
| C8 | Insurance | Unchanged. |
| C9 | Processing consent not tied to a version | **Moot**: consent is no longer used, because zero-commission orders are refused. The consent code remains but cannot enable an order. |

New points:

| # | Point |
|---|---|
| C10 | **Retention start depends on flags.** The retention date is set only when no flag is open (`needs_resolution IS NULL`) and no refund is pending. An unpaid shortfall therefore delays it, which is intended. A dispute arriving after the date is fixed does not move it; PA-PAY 8.1 relies on a legal hold. Today, placing that hold is a manual founder step (see gap N-B4). |
| C11 | **The reimbursement uses PlotArt's application fee.** In Stripe's records the reimbursement is an application-fee refund, the same mechanism as a commission refund. Pilot records keep them apart (ledger kinds `processing_reimbursement` vs `commission_refund`, and Stripe metadata `plotart_kind`). How the accountant books it (a reduction of commission income or a separate cost) is a tax question (section 6). |

## 3. Founder decisions

**Settled by the 17 November decision**
- F1: Model B, including VAT, on the whole payment including delivery.
- F4: commission-free orders are not offered through the pilot.
- F3 (partly): a second open quote per work is now prevented, rather than holding the work for the whole quote.

**Still open**

| # | Decision |
|---|---|
| F2 | Pilot limited to sellers who declare they are traders (PA-BPT 1.2). |
| F5 | Who responds to disputes. |
| F6 | Commission return after lost disputes, and C6. |
| F7 | Retention periods (accountant). |
| F8 | Transit insurance and return insurance. |
| F9 | Buyer receipt route. |
| F10 | Mail provider and monitoring owner. |
| F11 | **Deadline for paying a shortfall** (cl. 3.5 brackets [30] days), and the bank details route for paying the artist directly. PlotArt does not hold artists' bank details (PA-FAA 3.5), so one must be agreed, for example asking the artist at the time. |
| F12 | **Deadline for the reimbursement itself** (cl. 3.3(b) brackets [7] days). The code normally reimburses within minutes and retries every 15 minutes. |
| F13 | Whether to state that add-on fees are excluded (cl. 3.4(b)). The code excludes fee lines whose Stripe description names Radar, currency conversion, billing, invoicing, tax calculation, identity or instant payouts. Wording and list to confirm against what Stripe actually shows in live mode. |

## 4. Implementation: what Model B does (code)

- `processingFromBalance(bt)` takes the charge's balance transaction. It sums the `stripe_fee` lines, excluding the add-on descriptions above, and the `tax` lines. Tax is apportioned only if add-on fees are present.
- `reconcileProcessing` runs at payment completion (best effort), on every 15-minute sweep, and from the founder route `POST /api/admin/checkout/orders/:id/processing`. It:
  - books the ledger line `processing_fee` once, keyed to the balance transaction;
  - pays `min(owed, what is left of the application fee)` as a partial application-fee refund. The idempotency key includes the cost and the amount already reimbursed, so a retry can never pay twice;
  - books `processing_reimbursement`, keyed to the fee-refund id;
  - flags any excess as a shortfall;
  - if Stripe has not yet recorded the fee, sets status `awaiting_fee` and estimates nothing.
- `feeRefund` (commission refunds under PA-GAA 9) is capped at what is left of the application fee. The excess becomes a commission shortfall. `refundTotals` counts commission shortfalls as settled, so a later refund or direct repayment never asks for the same commission again.
- Shortfalls are kept in the order's `processing` JSON (per item, idempotent) and raise a `needs_resolution` flag that full-refund settlement no longer clears. `POST …/shortfallpaid` records a direct payment: once, never more than owed, with evidence; it books `processing_shortfall_paid`. A reversed refund keeps the shortfall flag and states exactly how the commission was settled.
- `statement()` appears on each order (artist and founder, list and detail) and in the Studio UI table. It shows the lines in PA-PAY 3.8.
- Commission-free orders are refused at artist approval, issue and checkout. Only one open quote per work is allowed (`requireNoOtherOpenQuote`).
- **Not absorbed:** disputes are booked as before, and no reimbursement is made for dispute fees.

## 5. Gaps (Model B)

**Necessary before live use**

| # | Gap |
|---|---|
| N-B1 | **Statement shows no dispute fees.** Stripe's dispute fee is not read into the pilot ledger, so the statement's net proceeds exclude it and say so. Reading the dispute's balance transactions would close this. |
| N-B2 | **Shortfalls rely on a person.** The code flags and records them; it does not pay them. A monitoring routine and deadline are needed (F11). No escalation timer exists for shortfalls; the pending-refund escalation is separate. |
| N-B3 | **Live fee lines.** The add-on exclusion pattern (F13) and VAT `tax` lines are verified in the sandbox only. Recheck the first live balance transactions. |
| N-B4 | **Hold after settlement.** A dispute or claim after the retention date is fixed needs a manual legal hold (C10). Consider placing a hold automatically when a dispute opens on a settled order. |
| N-B5 | The r5 gaps N1–N8 remain, except N4, which is moot. |

**Optional**
- An escalation for a reimbursement still `awaiting_fee` after a day.
- A downloadable statement (PDF or CSV) for the artist's records.
- Removing the dormant processing-consent code and UI once the founder confirms commission-free orders will never use the pilot.

## 6. Professional review points added by Model B

1. **Tax:** VAT treatment of PlotArt reimbursing VAT that Stripe charged the artist. The artist may also reclaim that VAT if VAT-registered, which would recover it twice across the two parties. Decide whether to reimburse VAT only to artists who cannot reclaim it, or accept the cost. The founder decision currently says "including VAT".
2. **Tax:** whether the reimbursement is a reduction of PlotArt's commission consideration, which affects VAT on commission, or a separate payment.
3. **Legal:** cl. 3.5 commits PlotArt to pay shortfalls directly. Confirm the wording and deadline, and whether cl. 0.2(b) "never more than that commission" needs "subject to clause 3.5" to stay true if a payment is late.
4. **Legal:** consistency of cl. 1.3(a) with any Founding Artist expectation that the pilot would be available to them. No issued text promised it.

## 7. Evidence

- Stripe sandbox, Irish card, €1,075 (run 14): `stripe_fee` €16.38 and `tax` €3.77 were separate lines.
- Local mocked proof: 157/157, including MB1–MB10, T6a and T6a2. The mock uses the same line structure and refuses application-fee refunds above the remaining fee, as Stripe does.
- Real Stripe results for run 19: see `reports/plotart-checkout-model-b-2026-11-17.md`.
