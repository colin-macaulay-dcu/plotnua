# PlotArt payment pilot · seven-day reimbursement, round 2 — wording and evidence

18 November 2026 · branch `plotart/managed-checkout-pilot` (PR #20) · Stripe TEST mode only

This round follows `plotart-seven-day-reimbursement-2026-11-18.md`.

**Status: the founder approved seven Irish calendar days as the sandbox pilot rule for PA-PAY §3.3 on 18 November 2026, 09:30.** This approval covers the sandbox rule only; the artist terms remain an unissued draft.
- The 30-day shortfall period (clause 3.5) remains a separate provisional proposal.
- Email stays in the test sink.
- Nothing has been merged, deployed or issued, and no migration has been applied.

Local results come from mock Stripe; dates and failures marked SIMULATED are simulated. Real Stripe results are reported separately (section 5).

---

## 1. Clause 3.3 linked to clause 3.5 (PA-PAY draft r9)

Clause 3.3(d) now reads:

> (d) PlotArt makes the reimbursement by refunding that amount of its application fee through Stripe. The reimbursement is made when Stripe accepts that refund. Stripe then adds the amount to the artist's Stripe balance, where it appears as an adjustment on that payment. The reimbursement can come only from what is left of PlotArt's application fee on that order. If that is less than the amount due, PlotArt reimburses what is left through Stripe and pays the rest to the artist directly by bank transfer under clause 3.5. The artist's statement shows the amount reimbursed through Stripe, with the date Stripe accepted the refund and Stripe's reference for it, and any amount PlotArt still owes by bank transfer until it is paid. When the money reimbursed through Stripe reaches the artist's bank account depends on the artist's Stripe payout schedule, which this clause does not govern;

Two other changes to the clause:
- **3.3(b)** now starts the period from "the day Stripe confirmed that the payment succeeded" (see section 3).
- **3.3(c)** ends: "Where Stripe's records do not show the day on which it recorded the amounts, the date in (b) applies;"

Clause 3.5 is unchanged: "[30] days … [provisional period, awaiting founder approval]". It is the next decision (`plotart-shortfall-30-day-decision-2026-11-18.md`).

**Artist's statement line for a partial reimbursement** (generated, check SD14):

> PlotArt reimbursed EUR 15.00 of the EUR 21.83 processing fee and VAT through Stripe: Stripe accepted PlotArt's refund of that amount of its application fee on Wednesday 18 November 2026 (Stripe reference fr_…). Stripe adds it to your Stripe balance as an adjustment on this payment; it shows as pending until Stripe makes it available. The remaining EUR 6.83 could not be reimbursed through Stripe, because it is more than what was left of PlotArt's application fee on this order. PlotArt pays it to you directly by bank transfer (clause 3.5). Still owed to you by PlotArt: EUR 6.83. Your statement shows it under "Owed by PlotArt, not yet paid" until it is paid. When the amount reimbursed through Stripe reaches your bank account depends on your Stripe payout schedule.

What else the statement and desk show:
- **Once part of the remainder is paid by bank transfer**, the line adds "Paid to you by bank transfer so far: EUR …". When nothing remains, it says "Nothing is still owed."
- **The statement's figures** also carry `processing_reimbursed_through_stripe` and `processing_still_owed_by_bank_transfer`.
- **Founder desk, amount column:** "EUR 21.83 in all: EUR 15.00 reimbursed through Stripe; EUR 6.83 still owed by bank transfer".
- **Founder desk, status:** "Reimbursed in part through Stripe · the rest is owed by bank transfer (Amounts owed)".

**Evidence:** SD14 (mock). €100 artwork, €15 commission; Stripe fee and VAT €21.83:
- €15.00 was refunded from the application fee at Stripe.
- One owed row for €6.83 was created, with a provisional due date.
- The desk and the statement both show both amounts.

## 2. Delay notice: what PlotArt can establish

**Delay notice** (one per order, artist, test sink):

> Order ‹reference›
>
> Stripe confirmed your buyer's payment on ‹date›. PlotArt reimburses Stripe's processing fee, and the VAT Stripe charges on it, within seven calendar days of the payment: for this order, by the end of ‹original date› (Irish time).
>
> We have not yet been able to confirm the fee Stripe charged on this payment, so we do not yet know the exact amount. PlotArt does not estimate it.
>
> If Stripe had not recorded the fee by the end of ‹original date›, PlotArt will reimburse it at the latest by the end of the seventh calendar day after the day Stripe records it (Irish time). For example, if Stripe records it on ‹tomorrow›, the latest date is ‹tomorrow + 7›. If Stripe's records show that it had recorded the fee by ‹original date›, that date still applies, and we will tell you.
>
> We will write again with the amount and the date that applies when the reimbursement is made. Your payout from Stripe to your bank is separate and follows your usual Stripe payout schedule.
>
> This message comes from the PlotArt payment pilot (test mode).

**Next notice** (one closing message; it opens "We have now been able to confirm the fee Stripe charged on this payment." and gives the reimbursement line above). It ends with one of three sentences:
- **Stripe recorded the fee late (extension applies):** "Stripe recorded the fee on ‹date›, after the original date, so the latest date for this reimbursement was the end of ‹date + 7› (Irish time)."
- **Later evidence shows Stripe recorded it on time:** "Correction to our earlier message: Stripe's records show it recorded the fee on Monday 16 November 2026, by the original date. The date that applies is therefore the end of Tuesday 17 November 2026 (Irish time), not a later date."
- **Fee time unknown:** "Stripe did not give the time it recorded the fee, so we cannot establish that the later date applies. The date that applies is the original one: the end of Sunday 15 November 2026 (Irish time). We are reviewing this order."

**Fee time unknown — founder side:**
- The desk keeps the original date as the due date: "Due by the end of ‹original› (Irish time) · provisional · Stripe gave no time for recording the fee: for review".
- Flag: "FOR REVIEW: Stripe did not give the time it recorded the fee; the pilot can show only when it first saw it. The original date stays in force although the pilot first saw the fee after it: whether the later date applies cannot be established."
- One founder alert: "FOR REVIEW: order ‹ref› — Stripe returned the processing fee without the time it recorded it … The original deadline stays in force … no extension is assumed."

**Evidence** (local, SIMULATED dates):

| Check | What it proves |
|---|---|
| SD8, SD8b | One delay notice per order in the test sink, never repeated |
| SD12 | The notice contains "We have not yet been able to confirm the fee Stripe charged on this payment" and no longer says "Stripe has not yet recorded" |
| SD9b, SD9d | Stripe's own time shows the fee was recorded in time: the original date is kept; one closing notice carries the correction |
| SD13 | Fee time unknown: the original date stays visible and in force; flagged FOR REVIEW; one founder alert; one delay notice; the closing notice gives the original date and says the order is under review |

## 3. Which timestamp starts the clock

**What run 33 did:** it used `charge.created`.
- The pilot accepts **card only** (`allowed_payment_method_types: ['card']`), with automatic capture. A card charge is therefore created at the successful authorisation, and run 33's charge was `succeeded` at its `created` time.
- That is a reasonable proxy, but it is not the confirmation event itself.
- A charge could in principle fall on a different Irish date from Stripe's confirmation. I have not confirmed the timing for every card flow, for example a 3-D Secure challenge.

**Changed to:** the `created` time of the **signed Stripe event that confirmed the successful payment**:
- `checkout.session.completed` with `payment_status = 'paid'`, or
- `checkout.session.async_payment_succeeded`.

The pilot already treats those events as proof of payment.

**Documented fallbacks**, used only when the payment was recorded without such an event (the founder's "reconcile after interruption" path):
1. the succeeded card charge's `created` time (flagged on the desk as a fallback);
2. the pilot's own record of the verified payment (flagged).

The charge time is always stored as evidence (`charge_created_at`).

**Evidence:**
- **SD15** (local, SIMULATED times, real webhook path): the card charge is created at 23:59:58 on 15 November and Stripe's signed success event at 00:00:03 on 16 November (Irish winter time = UTC). The clock starts on 16 November, so the reimbursement is due by the end of 23 November. The charge time is kept.
- **MB8b:** the normal paid order now shows basis `stripe_success_event_created`.
- **SD4:** the fallback path (no event) shows basis `stripe_charge_created` and is flagged.
- **E21e (run 34, real): PASS.** Signed `checkout.session.completed` created 09:13:58Z; the pilot's clock started there. The charge was created 09:13:56Z (2 s earlier), succeeded, card, captured. Both fall on 18 November 2026 in Ireland. See section 5.

## 4. Artist-side credit check (E21c corrected)

**Match rule** (harness key, read-only): a connected-account balance transaction whose source is the payment's charge, other than the charge itself, with the fee refund's amount and currency.
- **PASS:** exactly one such entry, and no other entry on the charge.
- **FAIL:** nothing on the charge after a minute of re-reading.
- **INCONCLUSIVE:** anything else, such as several entries or a near match. INCONCLUSIVE is now counted separately in the evidence summary.

**What run 34 checks:**
- **E21c:** a fresh €200 payment.
- **E21f:** run 33's €8.06 reimbursement, re-read from the sandbox.
- **E21e:** the real timestamps (section 3).

The runtime key keeps its five permissions. The harness only reads.

## 5. Real sandbox results

- **Run 33** (reported earlier): Stripe accepted the application-fee refund `fr_1Ud3cFHx1Olx8cdwLON6LFjc` (€8.06). The artist's balance showed an `adjustment` of +€8.06 (806 cents), pending, on the charge, in the same second. The pilot cannot read the artist's balance with the runtime key.
- **Run 34:** [44264008409](https://github.com/colin-macaulay-dcu/plotnua/actions/runs/44264008409), approved in `checkout-test` by `colin-macaulay-dcu`, **conclusion: success**. Timing from the run record (all UTC, which is Irish time in November): run created 08:05:25; job started 09:12:51; evidence written 09:14:05.631; job completed 09:14:10. GitHub's approval record gives no time, so the approval is known only to have been at or before 09:12:51, when the job started. The 09:23 previously shown here was the time of your message reporting the approval, not the approval itself, and has been removed. All Stripe times below (09:13:56–09:14:02) fall between the job start and the evidence time, so they are consistent with the run record. Every check passed, and no check was inconclusive.

| Check | Result | Amounts and timestamps (real Stripe) |
|---|---|---|
| E21c (fresh €200 payment) | **PASS** | **Fee refund:** `fr_1Ud4wIHx1Olx8cdw8oZs3KKh`, €8.06 (806 cents), EUR, accepted 09:14:02Z.<br>**Exactly one match on the artist's balance:** `txn_1Ud4wIHx1Olx8cdwgqiFJwEy`, type `adjustment`, +€8.06 (806 cents), EUR, net €8.06, fee €0, status `pending`, source = charge `ch_3Ud4wCHx1Olx8cdw0xU9NhZl`, created 09:14:02Z (0 s after the fee refund), available on 25 Nov 2026. Stripe's description: "Application fee refund for ch_…". Reporting category `fee`.<br>No other entries on the charge. |
| E21e (clock start) | **PASS** | **Signed `checkout.session.completed`:** created 09:13:58Z. The pilot's clock started here (basis `stripe_success_event_created`).<br>**Charge:** created 09:13:56Z, 2 s earlier; status `succeeded`, card, captured.<br>**Irish dates:** both 18 Nov 2026.<br>**Fee:** recorded 09:13:56Z; reimbursed 09:14:02Z, not late. |
| E21f (run 33's reimbursement re-read) | **PASS** | **Fee refund:** `fr_1Ud3cFHx1Olx8cdwLON6LFjc`, €8.06 (806 cents), EUR, accepted 07:49:15Z.<br>**Exactly one match:** `txn_1Ud3cFHx1Olx8cdwX9Y2UYbR`, `adjustment` +€8.06 (806 cents), EUR, `pending`, source = charge `ch_3Ud3c9Hx1Olx8cdw0Ah0fyIj`, created 07:49:15Z (0 s after), available on 25 Nov 2026. |

**Unchanged in run 34:**
- E21a/E21b PASS: Stripe fee €6.55 + VAT €1.51 = €8.06 reimbursed through the runtime key; the application fee shows `amount_refunded` €8.06 of €30.00 (806 of 3000 cents).
- E21d PASS: the runtime key can read the fee's refunds, but not the artist's balance (`balance_read` refused).
- E17d PASS: all 9 Worker calls used the runtime key.

## 6. Tests

| Suite | Result |
|---|---|
| Local pilot suite | 218/218 |
| Migration 0016 | 9/9 |

New or changed local checks: SD9d, SD12 (new sentence), SD13, SD14, SD15, MB8b. T11b now also expects the work sold through SD15's signed payment.

## 7. Open questions

1. **Insufficient platform funds — specific pre-live question.** What does Stripe do with an application-fee refund when PlotArt's platform balance cannot cover it? The options are refused, pending, or allowed to make the balance negative. Stripe's documentation does not say, and the sandbox platform has always had funds.
   - Before going live, either get Stripe's written answer, or test it in the sandbox with an emptied platform balance.
   - Also decide how much of a balance to keep, since the application fees from the same payments are themselves pending at first.
2. **The pilot cannot verify the artist's credit itself:** the runtime key has no Balance Read on connected accounts. This is unchanged and is your decision.
3. **The extension path has only simulated evidence:** every real payment so far had its fee recorded in the same second.
4. **3-D Secure:** whether a 3-D Secure card payment's charge and success event can fall on different dates is not established with real Stripe. The pilot no longer depends on it.
