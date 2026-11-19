# Founder decision paper · Insufficient platform funds for an application-fee refund

18 November 2026 · PlotArt managed-checkout pilot (Stripe Connect TEST mode) · internal review note, not customer-facing

## The question
Under §3.3 PlotArt reimburses the artist's Stripe processing fee by refunding part of its application fee. Stripe takes that refund from **PlotArt's platform balance**. If the balance cannot cover it, we do not know what Stripe does with an application-fee refund specifically. It might refuse the request, leave it pending, or take the platform balance negative. This is the last open item on the pre-live list for the reimbursement rules.

## What is known
- **Stripe documentation, ordinary refunds:** refunds use the available balance. If that is not enough, Stripe holds the refund as pending until the balance recovers. Where applicable, it may debit the bank account to cover a negative balance.
- **Stripe documentation, platforms:** Stripe recommends a platform **minimum balance** so that automatic payouts do not empty the account needed for refunds.
- **Not documented:** the application-fee-refund case. Every real sandbox run so far (33–36) had enough balance, so there is no evidence of what happens.
- **Pilot behaviour already built and tested locally:**
  - A failed fee refund is recorded as an attempt. After 3 failures the order is flagged "Processing reimbursement failing" on the founder desk, with the reason. The artist's due date is not changed.
  - "Reconcile processing fee" re-reads Stripe, so a pending or late-accepted refund is adopted, not duplicated.
  - Anything still unpaid after the seven-day deadline becomes a §3.5 amount owed by bank transfer, with its own 30-day deadline.
- **Not handled:** a refund Stripe reports as *pending* instead of failed. Today the pilot would treat it as accepted when Stripe returns the object. Whether Stripe ever returns a pending fee refund is the part we need to find out.

## Options
| | Option | What it involves | Trade-off |
|---|---|---|---|
| **1** | **Sandbox test first (recommended)** | One approved TEST-mode run. Empty the platform's test available balance with a test payout, try one €-cents fee refund, and record exactly what Stripe returns (error, pending status or negative balance). Then adapt the pilot's handling to that result and re-test. | Real evidence before any live decision. Touches only the test platform balance. Needs one approval link. |
| 2 | Operational control only | Before live, set a Stripe minimum balance on the platform and keep the existing failure flag and §3.5 fallback. No test. | Quick, but the pending case stays unknown. Relies on a setting that a large refund could still exceed. |
| 3 | Ask Stripe support | Written question to Stripe support. Their answer is recorded as review evidence. | Authoritative if answered, but slow and may be generic. Can run alongside option 1. |

**Recommendation:** option 1 now, plus option 3 in parallel. Treat the minimum balance (option 2) as a pre-live configuration item whatever the test shows. Choosing the amount is a live-money decision, so it stays with you at that point.

## If option 1 is approved
- The test runs on the existing test platform and reuse account only. It draws on no real money, and production stays untouched.
- After the run, the test balance is topped back up with test funds so later sandbox runs are not affected.
- The run is reported separately from mocked tests, the same way as runs 33–39.
- Insufficient platform funds stays on the pre-live list until you accept the evidence.
