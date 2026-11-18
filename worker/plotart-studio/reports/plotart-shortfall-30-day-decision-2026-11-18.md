# PlotArt payment pilot · next decision: PA-PAY §3.5, the 30-day bank-transfer period

18 November 2026 · branch `plotart/managed-checkout-pilot` (PR #20) · sandbox only · **for the founder's decision**

**Status: provisional.**
- Recorded as `DEADLINE_DECISIONS.shortfall_days` (status `provisional`). Nothing in this paper is approved, and its recommendations are not your approval.
- The §3.3 seven-day rule was approved separately for the sandbox (18 Nov, 09:30).
- Email stays in the test sink, and the artist terms remain an unissued draft.

## 1. What §3.5 covers

A **shortfall** is the part of what PlotArt owes the artist that cannot go back through Stripe, because it is more than what is left of PlotArt's application fee on that order. It arises in two ways:
- **Processing shortfall:** Stripe's fee plus VAT is more than the commission left on the order.
- **Commission shortfall:** commission to be returned after a buyer refund, when the fee has already been used.

PlotArt pays a shortfall by bank transfer, outside Stripe. Draft §3.5 says: "within [30] days of it arising [provisional period, awaiting founder approval]".

## 2. Worked example: the existing €6.83 shortfall (local check SD14 and SD16)

**The order:**
- €100.00 artwork with 15% commission = **€15.00** application fee.
- Stripe's processing fee and VAT come to **€21.83**.
- PlotArt reimburses **€15.00** through Stripe, which is all of the fee.
- The remaining **€6.83** becomes a processing shortfall owed by bank transfer.

For dates, take a payment Stripe confirms at **10:00:00 on Tuesday 1 December 2026** (Irish time = UTC in winter). As in every real sandbox run, Stripe records the fee at once, and the pilot reimburses through Stripe at **10:00:05**.

### 2a. When the 30 days start, as built now

- **Start:** the moment the pilot works out that the fee cannot cover the reimbursement, which is when it makes the €15.00 reimbursement. That moment is **10:00:05 on 1 December**.
  - This is not the payment time.
  - If Stripe recorded the fee late (say on 10 December), the shortfall would arise on 10 December.
- **Due:** exactly 30 × 24 hours later, at **10:00:05 on Thursday 31 December 2026**.
  - The founder desk shows "Due 2026-12-31 (provisional)".
  - The item counts as overdue from 10:00:05 that day, not from the end of the day.
  - The local run recorded the same pattern: arose 18 Nov 09:31:36.549Z, due 18 Dec 09:31:36.549Z, rule "PROVISIONAL, awaiting founder approval: paid directly within 30 days of arising (PA-PAY draft cl. 3.5)".
- **The due date is fixed when the item arises.** Approving or changing the period later affects only new items.

### 2b. The alternative, consistent with §3.3

Count **30 Irish calendar days**:
- the day after the shortfall arises is day one;
- the payment is due by the **end of day 30**, Irish time.

For this example that is **the end of Thursday 31 December 2026**: the same date, but the end of the day rather than 10:00:05. In summer, near midnight, the two methods can give different dates. This would be a small code change, made only if you choose it.

### 2c. What the artist sees after a partial bank payment

PlotArt pays **€3.00** by transfer and records it. The artist's statement line (exact text from SD16) reads:

> PlotArt reimbursed EUR 15.00 of the EUR 21.83 processing fee and VAT through Stripe: Stripe accepted PlotArt's refund of that amount of its application fee on ‹date› (Stripe reference fr_…). Stripe adds it to your Stripe balance as an adjustment on this payment; it shows as pending until Stripe makes it available. The remaining EUR 6.83 could not be reimbursed through Stripe, because it is more than what was left of PlotArt's application fee on this order. PlotArt pays it to you directly by bank transfer (clause 3.5). Paid to you by bank transfer so far: EUR 3.00. Still owed to you by PlotArt: EUR 3.83. Your statement shows it under "Owed by PlotArt, not yet paid" until it is paid. When the amount reimbursed through Stripe reaches your bank account depends on your Stripe payout schedule.

The statement figures:
- `processing_still_owed_by_bank_transfer` = 383 cents;
- "Owed by PlotArt, not yet paid" = €3.83, kept outside net proceeds.

The founder desk (Amounts owed) shows:
- owed €6.83, paid €3.00, **outstanding €3.83**;
- due 2026-12-31 (provisional);
- the payment with its reference.

After the remaining €3.83 is recorded, the statement reads "Paid to you by bank transfer so far: EUR 6.83. Nothing is still owed." and the order's flag clears.

**The artist is not sent a message when a bank payment is recorded.** The statement in Studio is the only record they see. See decision 5.

## 3. What lets you mark the balance paid

**As built:** the founder enters two things in **Record shortfall paid**:
- the amount paid (up to the amount outstanding);
- the bank's **transfer reference and date**, as text of 10–200 characters.

The pilot then:
- refuses anything that looks like bank details;
- refuses a reference already recorded on that order;
- stores who recorded it and when;
- applies the amount to the oldest item first.

It **does not check the bank**. It also keeps the transfer date only inside that text, so it cannot tell whether a payment was made on time.

**Recommended evidence standard (for your decision):** mark an amount paid only when PlotArt's bank shows the transfer as **executed**, not merely scheduled. The bank's confirmation should show:
- the amount;
- the execution date;
- PlotArt's payment reference (for example the order reference);
- the payee name, with a clean Verification of Payee result (PILOT-SHORTFALL-PAYMENTS.md §2).

Keep that confirmation in PlotArt's bank and accounting records, not in the pilot. Record in the pilot only the bank's reference and the execution date.

**Optional small change:** a separate "date executed" field, so the desk can show "paid on time" or "paid late" automatically.

## 4. Who follows up if it is unpaid at the deadline

**PlotArt (the founder) follows up.** It is PlotArt's debt to the artist; the artist is never asked to chase it.

As built:
- **Before the deadline:** one founder reminder 7 days before (from 10:00:05 on 24 December in the example).
- **At the deadline:** one overdue reminder.
- **Desk:** the item is marked overdue.
- **Order:** it keeps the flag "PlotArt owes the artist … PlotArt must pay it directly … and record it with 'Record shortfall paid'", and cannot be closed while it is set.

Reminders go to the founder only, in the test sink. **The artist receives nothing automatic at the deadline.**

**Proposed procedure (for your decision):**
1. On the overdue reminder, the founder phones the artist on the number in their seller information. Bank details are never collected by email (PILOT-SHORTFALL-PAYMENTS.md §2).
2. The founder pays within 5 working days.
3. The founder sends the artist a short notice giving the amount, the reason for the delay and the payment date.

## 5. Decisions for you

1. **Period:** 30 days, or another number.
2. **Start:** when the shortfall arises (as built, normally the moment of the Stripe reimbursement), or the Irish date of Stripe's payment confirmation, as in §3.3.
3. **Counting:** 30 × 24 hours from the moment it arises (as built), or 30 Irish calendar days to the end of day 30 (consistent with §3.3; small code change).
4. **Evidence:** the standard in section 3, and whether to add the "date executed" field.
5. **Artist notices** (test sink): whether the artist gets a message when a bank payment is recorded and/or when an amount becomes overdue, or relies on the statement.
6. **Follow-up:** the procedure in section 4.

## 6. Evidence for this paper

- **Local suite:** 219/219 checks, mock Stripe.
  - **SD14:** the €15.00/€6.83 split; the owed row due 30 days later, provisional.
  - **SD16:** a €3.00 partial payment, the refusal of a bank-detail reference and a duplicate reference, then the full payment.
  - **OQ checks:** the reminder and overdue logic.
- **Real Stripe:** no sandbox run has produced a real shortfall. Every real sale had enough application fee left.
- **Code:** `owe()`, `recordShortfallPaid()`, `remindOwed()` and `reimbursementWording()` in `src/checkout.js`.

## Pre-live list (unchanged)

- **Insufficient platform funds.** What Stripe does with an application-fee refund when PlotArt's platform balance cannot cover it. This affects both §3.3 and §3.5.
