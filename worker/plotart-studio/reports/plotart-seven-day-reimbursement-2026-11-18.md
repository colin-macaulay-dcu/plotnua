# PlotArt payment pilot · seven-day processing reimbursement (PA-PAY §3.3(b)) — sandbox results

18 November 2026 · branch `plotart/managed-checkout-pilot` (PR #20) · Stripe TEST mode only

**Status: proposed sandbox rule, provisional until the founder reviews these results.** Nothing has been merged, deployed or issued, and no migration has been applied. Email stays in the test sink. The separate 30-day shortfall decision, issuing terms and production deployment remain outside this approval.

---

## 1. Revised clause (PA-PAY-2026-11 draft r9, §3.3)

> 3.3 **Stripe processing fees: PlotArt reimburses them.** Stripe charges a processing fee on each card payment, on the whole amount the buyer pays, including delivery. Stripe deducts it, and any VAT Stripe charges on it, from the balance of the artist's Stripe account. On every pilot order:
>
> (a) PlotArt reimburses the artist the actual processing fee Stripe charged on that payment, and the VAT Stripe charged on that fee, if any;
>
> (b) the amounts are those Stripe records for the payment, not estimates. PlotArt reimburses them once Stripe has recorded them, and no later than the end of the [seventh] calendar day after the day Stripe confirmed the payment [seven days: provisional, awaiting founder approval]. Days are counted by the date in Ireland, and the day after the payment is day one. For example, for a payment Stripe confirms on Tuesday 1 December 2026, the reimbursement is due by the end of Tuesday 8 December;
>
> (c) if Stripe has not recorded the amounts by the end of that [seventh] day, PlotArt tells the artist and reimburses them no later than the end of the [seventh] calendar day after the day Stripe records them, counted in the same way. In the example in (b), if Stripe recorded the fee on Thursday 10 December, the latest date would be Thursday 17 December. This later date applies only where Stripe had not recorded the amounts. It does not apply where PlotArt was late in checking Stripe or an attempt to make the reimbursement failed;
>
> (d) PlotArt makes the reimbursement by refunding that amount of its application fee through Stripe. The reimbursement is made when Stripe accepts that refund. Stripe then adds the amount to the artist's Stripe balance, where it appears as an adjustment on that payment. The artist's statement shows the amount, the date Stripe accepted the refund and Stripe's reference for it. When the money reaches the artist's bank account depends on the artist's Stripe payout schedule, which this clause does not govern;
>
> (e) as a result, the artist's combined deduction for PlotArt commission and Stripe's processing of the payment is no more than the commission.

Changes from r8:
- "normally within minutes of the payment" is removed. No time-of-day promise is made, so there is no "by 14:15" equivalent: a 15-minute check interval is not a delivery guarantee.
- The extension in (c) is new.
- (d) now states what the evidence shows.
- The old (c) and (d) become (d) and (e).
- No other clause cites 3.3(c) or 3.3(d).

## 2. Founder-desk wording (Payment pilot → Processing reimbursements)

The table shows one row per order still to be reimbursed. Orders reimbursed in the last 30 days are listed underneath with the same columns.

| Column | Wording |
|---|---|
| Status | **Waiting for Stripe to record the fee** · **Fee known · reimbursement outstanding** · **Reimbursed · Stripe accepted the application-fee refund** · **Reimbursed in part · the rest is in Amounts owed (bank transfer)**. **OVERDUE** is added once the due date has passed. |
| Amount | "Not yet known: Stripe has not recorded the fee (nothing is estimated)", or the exact amount, for example "EUR 21.83" |
| Paid (Irish date) | Irish date of Stripe's payment confirmation, plus "day N" |
| Due | "Due by the end of Tuesday 8 December 2026 (Irish time) · provisional" |
| | "Original date (Tuesday 8 December 2026) passed before Stripe recorded the fee. Due by the end of the seventh day after Stripe records it · provisional" |
| | "Extended: Stripe recorded the fee on Thursday 10 December 2026. Due by the end of Thursday 17 December 2026 (Irish time) · provisional" |
| Alerts and attempts | "Day-5 alert sent" · "Deadline alert sent" · "Delay notice sent to the artist (test sink)" · "4 failed attempt(s); last: ‹Stripe's message›. Due date unchanged." |
| Action | **Reconcile processing fee**: re-reads Stripe, records any reimbursement Stripe already made, then retries. It never pays twice. |

**Evidence flags**, shown in the same cell:
- "Payment date taken from the pilot's own record of the verified payment: Stripe's confirmation time has not been read."
- "Stripe did not give the time it recorded the fee: the pilot can show only when it first saw the record."
- "A delay notice was sent because Stripe showed no fee at the original date, but Stripe's own record time is earlier: the original date stands. Check in the Stripe Dashboard and tell the artist if needed."

**Order flag after 3 failed attempts:** "Processing reimbursement failing (N attempts): ‹Stripe's reason›. The due date is unchanged (end of ‹date›). Check the reason, then use "Reconcile processing fee": it re-reads Stripe, records any reimbursement Stripe already made, and retries without creating a second one." The order cannot be closed while this flag is set. The flag clears itself once the reimbursement is made.

**Founder alerts** (test sink, founder only):
- **Day 5:** "Day 5: order ‹ref› — processing reimbursement still outstanding. Status: … Amount: … Due by the end of ‹date› (Irish time) (provisional deadline)."
- **Deadline passed:** "OVERDUE: order ‹ref› — the processing reimbursement was due by the end of ‹date› … and is still outstanding."
- **Extension applied:** "the original reimbursement date … passed before Stripe recorded the processing fee. The extension applies … One delay notice has gone to the artist."

Each alert is sent once per order.

## 3. The artist's delay notice (as generated in the test sink)

Subject: *PlotArt payment pilot · ‹order› · processing fee reimbursement: Stripe has not yet recorded the fee*

> Order ‹order reference›
>
> Stripe confirmed your buyer's payment on Tuesday 1 December 2026. PlotArt reimburses Stripe's processing fee, and the VAT Stripe charges on it, within seven calendar days of the payment: for this order, by the end of Tuesday 8 December 2026 (Irish time).
>
> Stripe has not yet recorded the processing fee for this payment, so the exact amount is not yet known. PlotArt does not estimate it.
>
> PlotArt will reimburse the fee as soon as Stripe records it, and at the latest by the end of the seventh calendar day after the day Stripe records it (Irish time). For example, if Stripe records the fee on Thursday 10 December 2026, the latest date is Thursday 17 December 2026.
>
> We will tell you the amount when the reimbursement is made. Your payout from Stripe to your bank is separate and follows your usual Stripe payout schedule.
>
> This message comes from the PlotArt payment pilot (test mode).

Notes on the notice:
- Dates are shown here for the 1 December example. In the pilot the worked example always uses the day after the notice is sent, so it is never a past date.
- It is sent once per order.
- When Stripe records the fee and the reimbursement is made, one closing message follows, with the completion wording below.

**Completion wording** (artist statement line; also the closing message after a delay notice):

> PlotArt reimbursed EUR 8.06: Stripe accepted PlotArt's refund of that amount of its application fee on Wednesday 18 November 2026 (Stripe reference fr_…). Stripe adds it to your Stripe balance as an adjustment on this payment; it shows as pending until Stripe makes it available. When it reaches your bank account depends on your Stripe payout schedule.

## 4. Test results

### 4a. Real Stripe sandbox — run 33

- Actions run [44259652058](https://github.com/colin-macaulay-dcu/plotnua/actions/runs/44259652058), approved by the founder 07:48, 18 Nov.
- **Run conclusion: failure.** This is caused solely by E21c, whose matcher looked for the wrong link (see below). The evidence it collected answers the question.
- Account: `acct_1UclJXHx1Olx8cdw`. Payment: one €200 card payment on real hosted Checkout, 15% commission = €30 application fee.

| Check | Result | What Stripe returned |
|---|---|---|
| E21a | PASS | **Payment confirmation:** charge `created` 07:49:10Z. This is the pilot's basis: `stripe_charge_created`.<br>**Fee recorded:** balance transaction `created` 07:49:10Z. Basis: `stripe_balance_transaction_created`.<br>**Fee lines:** processing fee €6.55 + VAT €1.51 = €8.06.<br>**Reimbursement:** the public Worker reimbursed €8.06 on the runtime key at 07:49:15Z (5 s after payment). Status `reimbursed`, not late. |
| E21b | PASS | **What Stripe returns when it accepts the refund:** a `fee_refund` object, `fr_1Ud3cFHx1Olx8cdwLON6LFjc`, amount 806, currency eur, `created` 07:49:15Z, `fee` = the application fee, `balance_transaction` = a **platform** balance transaction, plus our metadata (`plotart_kind`, `plotart_order`).<br>**The application fee now shows** `amount_refunded` 806 of 3000, `refunded: false`.<br>**Stored by the pilot:** id, amount, Stripe's acceptance time and the platform balance transaction.<br>The harness's read-back of the platform balance transaction returned no fields; not established. |
| E21c | FAIL (matcher); **evidence found** | **Artist's balance (read with the harness key):** at 07:49:15Z, the same second as the fee refund, Stripe recorded a balance transaction of **type `adjustment`, amount +806, status `pending`, source = the payment's charge** (not the fee refund).<br>The check searched for `source = fr_…` and so missed it. The matcher is now corrected to type `adjustment`, the same charge, the same amount, created within 60 s. It has not been re-run. |
| E21d | PASS | **Runtime key, read-only:**<br>- It **can** list the fee's refunds (200). The pilot uses this to detect a refund whose answer was lost.<br>- It **cannot** read the artist's balance or balance transactions: 403 `more_permissions_required`, "Enabling Balance Read ('balance_read') permissions on this key would allow this request to continue." |
| E17d | PASS | All 9 Stripe calls by the public Worker used the runtime key; none fell back to another key. |
| E17b, E17c | PASS | Denials unchanged from runs 30–32. |

**What confirms reimbursement:**
- Stripe's `fee_refund` object, with its id, amount and `created`, together with `amount_refunded` on the application fee. The pilot records and can re-read both.
- The matching credit to the artist's Stripe balance exists: an `adjustment` on the payment, pending at first.
- **With the five adopted permissions, the pilot cannot verify the credit itself.** It can be seen in the artist's Stripe Dashboard, or by a key with Balance Read on connected accounts.

The completion wording therefore says what Stripe accepted and where the money appears. It makes no claim that the pilot checked the artist's balance.

### 4b. Local tests — Miniflare with mock Stripe (dates and failures SIMULATED)

The local suite runs **214/214 checks**. Other suites: migration 0016 9/9; deployment tooling 23/23.

The seven-day checks:

| Check | Label | What it proves |
|---|---|---|
| SD1 | SIMULATED dates | Payment confirmed Tue 1 Dec → day one is 2 Dec. Due by the end of Tue 8 Dec; 23:59 on 8 Dec is still in time. |
| SD2 | SIMULATED near midnight | 23:30 UTC on 1 July = 00:30 on 2 July in Dublin (Irish Summer Time). So the Irish date is 2 July, due by the end of 9 July (23:00 UTC); a UTC rule would give 8 July. In winter, 23:30 UTC on 1 Dec stays 1 Dec → due 8 Dec. |
| SD3 | SIMULATED | Fee not recorded by the end of 8 Dec → extension. Recorded on 10 Dec → latest date 17 Dec. |
| SD3b | SIMULATED late check | Stripe recorded the fee on 8 Dec; the pilot first checks on 10 Dec. No extension; due stays 8 Dec; overdue. |
| MB8b | mock | Desk: "Waiting for Stripe to record the fee", no amount, day 0, provisional due date, based on Stripe's charge time. |
| SD4 | SIMULATED day 5 | Desk shows "Fee known · reimbursement outstanding", EUR 21.83 and the due date. Day-5 founder alert, once. |
| SD5 | SIMULATED failures | 4 failures. Desk and flag show Stripe's reason and the manual action. Due date unchanged. One idempotency key throughout. No reimbursement created. |
| SD6 | SIMULATED day 8 | Deadline alert, once. OVERDUE. No extension (the fee was recorded in time); no delay notice. |
| SD7 | SIMULATED lost answer | Stripe made the refund but the answer was lost. The next pass reads Stripe's list and records it. Exactly one reimbursement; flag cleared; marked late. |
| SD8, SD8b | SIMULATED | Fee unrecorded past the original date. One artist delay notice and one founder note, never repeated. No estimate. |
| SD9 | SIMULATED | Stripe records the fee: reimbursed at the next sweep, once. Latest date = 7 Irish days after the day Stripe recorded it. |
| SD9b | SIMULATED | The notice went out, but Stripe's own record time is inside the original period. No extension claimed; the original date stands; marked late; the desk flags it. |
| SD9c | mock | One closing message after the delay notice, with the completion wording. The statement carries the same wording. |
| SD10 | SIMULATED late check | No new period for a late check; marked late against the original date. |
| SD11 | mock | Where Stripe's times are missing, both evidence flags are shown. |
| SD12 | mock | Notice content: dates, no estimate, the 7-day rule from Stripe's record with an example, payout separate, no "14:15". |

Simulated evidence (desk rows and notice) is in `reports/seven-day-local-simulated-evidence-2026-11-18.json`. Run 33's table is in `reports/stripe-run-33-evidence.md`.

## 5. Remaining gaps

1. **Insufficient platform funds — not known.**
   - Stripe's API reference says creating a fee refund returns the `fee_refund` object if it succeeded, and an error if the fee is already refunded or the id is invalid.
   - I found no Stripe documentation saying what happens when the **platform's** balance cannot cover an application-fee refund: whether it is refused, created as pending, or allowed to make the platform balance negative. Stripe documents the pending behaviour only for payment refunds on indirect charges.
   - The sandbox platform had funds in run 33, so this case has not been tested.
   - The pilot's handling is the same whatever the cause: a refusal is recorded with Stripe's message, retried on the original due date, flagged after 3 attempts and alerted at day 5 and at the deadline.
   - The founder should still check the platform balance before relying on the seven days. Application fees from the same payments are themselves pending at first, so early in the pilot the platform's available balance may be low.
   - A sandbox test of this case would need an empty platform balance; it has not been designed.
2. **Artist credit not verifiable by the pilot.**
   - The runtime key lacks Balance Read on connected accounts, so the pilot relies on Stripe's acceptance (fee_refund) and does not check the artist's balance.
   - Adding that permission is a decision for you; I have not proposed or made the change.
3. **E21c not re-run with the corrected matcher.** The credit was observed in the raw listing (+806 `adjustment`, pending, on the charge), but the check itself has not passed. Its `available_on` date was not captured.
4. **Platform balance transaction for the fee refund** could not be read back by the harness (empty result). This is not established.
5. **Fee recorded later than payment** was simulated only. In every real sandbox payment so far, Stripe recorded the fee in the same second as the charge, so the extension path has no real-Stripe evidence.
6. **Alerts and the delay notice go to the test sink only.** Email stays disabled.
7. **The seven days, and the 30-day shortfall period, remain provisional** (`CHECKOUT_DEADLINES_APPROVED` not set).
