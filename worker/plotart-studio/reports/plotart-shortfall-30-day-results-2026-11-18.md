# PlotArt payment pilot · §3.5 bank-transfer shortfalls — sandbox rule implemented

18 November 2026 · branch `plotart/managed-checkout-pilot` (PR #20) · sandbox only

**Decision recorded:** the founder approved 30 Irish calendar days as the sandbox rule for PA-PAY §3.5 at 09:40 on 18 November 2026. It covers both processing-fee and commission-return shortfalls, and is recorded as `DEADLINE_DECISIONS.shortfall_days`.
- The artist terms remain an unissued draft.
- Live email stays off; every notice goes to the test sink.
- Insufficient platform funds stays on the pre-live list.

**Source of every result here:** local tests with mock Stripe; dates and failures are SIMULATED. **No real Stripe sandbox run has produced a shortfall.** Every real sandbox sale has had enough application fee left, so there is no actual Stripe evidence for this rule yet.

## 1. What was built

| Item | Behaviour | Local check |
|---|---|---|
| **Start** | The Irish date of the transaction record that first established the amount owed by bank transfer (details below). The next day is day one; payment is due by the end of day 30 in Europe/Dublin. | SD16, OQ1, SD21, LD4 |
| **Stored** | The record used (`due_basis_event`), its time, its Irish date, whether it is Stripe's record or the pilot's, and any review note. | SD16 |
| **Uncertain start** | If the start rests on the pilot's record rather than Stripe's, the item is marked **For review** and the founder gets one alert (test sink). | LD4 |
| **Deadline fixed** | Late reconciliation, retries, partial payments and returned transfers keep the original date. The database refuses to change a due date or start record. | SD16, SD19 |
| **Existing items** | Items created before this rule keep their stored due dates. | OQ5 |
| **Bank execution date** | A payment can be recorded only with the date the bank shows the transfer executed. The pilot refuses a missing date, a future date, or a date before the buyer's payment. It stores the amount, reference, execution date, who recorded it and when. The bank confirmation and payee details stay in the bank and accounting records. | SD17, OQ6 |
| **Returned transfer** | Founder action **Transfer returned…** (date and bank's reason). The outstanding amount is restored, the payment stays in the history marked returned, and the due date is unchanged. A transfer can be returned only once. The database blocks any other reduction of a paid amount. | SD19 |
| **Follow-up** | One founder reminder 7 days before the deadline. When overdue: one founder prompt to follow up promptly, with an **internal** target of 5 working days after the deadline (stated as not changing the artist's deadline); the order is flagged OVERDUE. | SD23, OQ5 |
| **Artist notices** | One per executed payment, and one when a balance becomes overdue. All go to the test sink. | SD17, SD18, SD20, SD23 |

**Which record starts the clock:**

| How the shortfall arises | Record used | Source |
|---|---|---|
| Processing fee | Stripe's record of the fee (`bt.created`) | Stripe |
| Commission return on a buyer refund | Stripe's refund record or refund event | Stripe |
| Commission moved to bank transfer after a lost dispute | The pilot's record of Stripe closing the dispute as lost | Pilot (flagged for review) |
| Commission on a direct repayment | The founder's record of the artist repaying the buyer | Pilot (flagged for review) |
| A pending refund found succeeded by the sweep | The pilot's record of finding it | Pilot (flagged for review) |

## 2. The €6.83 example (order G: €100 artwork, €15 commission, Stripe fee + VAT €21.83) — SIMULATED

| Step | Result |
|---|---|
| Stripe records the fee; €15.00 reimbursed through Stripe; €6.83 owed by bank transfer | Start = Irish date of Stripe's fee record (17 Nov). Due by the end of **Thursday 17 December 2026**. Event `stripe_fee_recorded`, source Stripe, no review needed. Founder reconcile and sweep afterwards: still one item, same date (SD16). |
| Founder records €3.00 with no date, or a future date | Refused (SD17) |
| €3.00 executed (`SIM-TRF-0001`) | Desk: paid €3.00, outstanding €3.83, with the execution date, reference, recorder and time. One artist notice (SD17). |
| Same reference entered again | Refused (409); no second notice (SD17) |
| €3.83 executed (`SIM-TRF-0002`) | Nothing owed; order flag cleared; second artist notice (SD18) |
| €3.83 transfer returned by the bank | €3.83 owed again; due date unchanged; history keeps both transfers, one marked returned; order flagged again; a second return is refused; a direct database reduction is refused (SD19) |
| €3.83 re-sent (`SIM-TRF-0003`) | Nothing owed. Three executed transfers, one returned. Three artist payment notices in total (SD20). |

## 3. Both reasons a shortfall can arise

- **Processing fee:** the €6.83 above (SD14, SD16).
- **Commission return:** order J, same €100/€15 shape. A €50 buyer refund owes a €7.50 commission share, but the fee was already used up. So €7.50 is owed by bank transfer, due 30 Irish days from the Irish date of Stripe's refund record (SD21). The statement lists it separately as "Commission PlotArt returns to you".
- **Earlier local checks:**
  - MB6/OQ1: a full refund leaves €20.15 commission to return by bank transfer. Start: Stripe's refund record.
  - LD2/LD4: a lost dispute moves €8.15 to bank transfer. Start: the pilot's record of the dispute closing, flagged for review.

## 4. Across the Irish clock change — SIMULATED

| Case | Result |
|---|---|
| **Autumn (SD22)** | Stripe recorded the fee at 23:30 UTC on 15 October 2026 = 00:30 on **16 October** in Dublin (Irish summer time). A UTC-date rule would start from 15 October.<br>Day 30 is **Sunday 15 November 2026**. It is due by its end, 00:00 UTC on 16 November, Irish winter time after the 25 October change. |
| **Spring (pure calculation)** | Start 10 March 2027 → due by the end of Friday 9 April 2027 = 23:00 UTC (Irish summer time). |
| **Overdue (SD23)** | Order K is now past its deadline. One founder prompt; the order is flagged OVERDUE; one artist overdue notice; repeat sweeps send nothing more. |

## 5. Artist-facing wording (generated in the test sink and on the statement)

**Statement line after the €3.00 partial payment:**

> … The remaining EUR 6.83 could not be reimbursed through Stripe, because it is more than what was left of PlotArt's application fee on this order. PlotArt pays it to you directly by bank transfer (clause 3.5), by the end of Thursday 17 December 2026 (Irish time). EUR 3.00 sent by bank transfer on Wednesday 18 November 2026. Still owed to you by PlotArt: EUR 3.83. Your statement shows it under "Owed by PlotArt, not yet paid" until it is paid. …

**After a returned transfer:**

> … EUR 3.00 sent by bank transfer on Wednesday 18 November 2026. EUR 3.83 sent by bank transfer on Wednesday 18 November 2026 was returned by the bank on Wednesday 18 November 2026 and is owed again. Still owed to you by PlotArt: EUR 3.83. …

**Notice for each executed payment:**

> Order ‹reference›
>
> PlotArt sent you EUR 3.00 by bank transfer on Wednesday 18 November 2026 (PlotArt's transfer reference: SIM-TRF-0001). This is part of Stripe's processing fee and VAT that PlotArt reimburses and could not be paid through Stripe.
>
> Still owed to you by PlotArt on this order: EUR 3.83, due by the end of Thursday 17 December 2026 (Irish time).
>
> How long the transfer takes to appear in your account depends on your bank.
>
> This message comes from the PlotArt payment pilot (test mode).

For the final payment, the "Still owed" line reads "Nothing more is owed to you by bank transfer on this order." For a commission shortfall, the description reads "commission PlotArt returns to you".

**Overdue notice:**

> Order ‹reference›
>
> PlotArt owes you EUR 6.83 that could not be paid through Stripe (part of Stripe's processing fee and VAT that PlotArt reimburses). It was due by the end of Sunday 15 November 2026 (Irish time), and it has not yet been paid in full. We are sorry for the delay.
>
> PlotArt will contact you to arrange the bank transfer. PlotArt will never ask for your bank details by email. Your statement shows the amount still owed.
>
> This message comes from the PlotArt payment pilot (test mode).

**Founder prompt when overdue (internal):**

> OVERDUE — follow up promptly: PlotArt owes the artist EUR 6.83 on order ‹ref› (processing shortfall). It was due by the end of Sunday 15 November 2026 (Irish time). Phone the artist on the number in their seller information, pay by bank transfer, and record the payment once the bank shows it executed. Internal resolution target: Friday 20 November 2026 (5 working days after the deadline). The artist's deadline still applies. …

Working days count Monday to Friday; Irish public holidays are not excluded.

## 6. Clause §3.5 (draft r9, still unissued)

> … PlotArt pays the difference to the artist directly, by bank transfer, no later than the end of the thirtieth calendar day after the day on which the payment records first show the amount (for example, Stripe's record of the processing fee, or of the buyer's refund). Days are counted by the date in Ireland, and the next day is day one. A later check of the records, a failed or partial payment, or a transfer that is returned does not change that date. PlotArt tells the artist each time it sends a transfer, with the amount, the date its bank executed it and any amount still owed, and tells the artist if any amount is not paid by the date. …
>
> … The artist's statement shows each amount sent by bank transfer and the date its bank executed it, any transfer that was returned, and any amount PlotArt still owes.

The 5-working-day follow-up target is internal. It is in the review notes and the internal procedure (PILOT-SHORTFALL-PAYMENTS.md §5), not in the terms.

## 7. Tests

| Suite | Result |
|---|---|
| Local pilot suite | 227/227 |
| Migration 0016 | 9/9 (now 22 pilot tables, including `checkout_owed_payment_returns`) |
| Deployment tooling | 23/23 |

New or changed local checks: SD16–SD23, LD4, OQ1, OQ5, OQ6. A sandbox rerun wasn't needed: this changes no Stripe calls.

## 8. Open points

1. **No artist notice when a transfer is returned.** The statement changes, and the overdue notice follows if the deadline passes, but no message goes when the return is recorded. A notice can be added if wanted.
2. **Lost-dispute and direct-repayment start dates are always flagged for review**, because the pilot records them rather than Stripe giving the time.
3. **Insufficient platform funds** (pre-live): unchanged.
