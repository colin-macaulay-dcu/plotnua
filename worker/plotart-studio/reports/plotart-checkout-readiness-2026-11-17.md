# PlotArt managed checkout pilot: consolidated readiness report

17 November 2026 · branch `plotart/managed-checkout-pilot` (PR #20) · **Stripe test mode only** · nothing merged or deployed · production unchanged · live payments off · no terms issued.

Latest run: **run 18**, [Actions run 44137541556](https://github.com/colin-macaulay-dcu/plotnua/actions/runs/44137541556).

- **39 passed, 0 failed.**
- **1 skipped on purpose:** account creation reused the account created and checked in run 3.
- **5 measurements recorded.**

Test connected account: `acct_1UclJXHx1Olx8cdw`. It was created with Stripe's current account type (Accounts v2) and Colin onboarded it with test data.

---

## A. Completed tests

### A1. Checked against Stripe's test API (run 18)

**Account set-up**

| Area | Checks | Result |
|---|---|---|
| Account configuration | P1c, P1d, P3 | PASS. The artist pays Stripe's fees, Stripe carries any unrecoverable negative balance and collects the identity requirements, and the artist has the full Stripe Dashboard. Card payments are active. |
| Onboarding complete | P1e, P2 | PASS. Details submitted, charges and payouts enabled, nothing outstanding. The Stripe-hosted onboarding link works. |

**Payments**

| Area | Checks | Result |
|---|---|---|
| Checkout Sessions | P4, P4b, P5 | PASS. Prices are in euro with Adaptive Pricing off, so buyers can't be shown converted prices. A repeated request returns the same session, and a session can be expired. |
| Payment with commission | P6, P6b | PASS. A €1,075 direct charge with a €150 application fee. Stripe creates the fee record a few seconds after the payment. |

**Refunds**

| Area | Checks | Result |
|---|---|---|
| Full and partial refunds | P8, P10 | PASS |
| Refunds of PlotArt's commission | P8b, P9, P10 | PASS. The commission is not refunded automatically with the buyer's refund. PlotArt's own commission refund is made once only, even if the request repeats. Partial refunds return a proportional share. |
| A refund that succeeds and then fails | P12 | PASS. Stripe changed the refund to failed (`expired_or_canceled_card`). |
| A refund larger than the available balance | P11, P11b | PASS (measured). Stripe completed it at once from incoming payments rather than holding it. See gap G1. |

**Disputes**

| Area | Checks | Result |
|---|---|---|
| Disputes, lost and won | P13, P14 | PASS. Each dispute closed with the expected outcome. |

### A2. End to end: a real browser paying on Stripe's hosted Checkout, with genuine Stripe-signed events (run 18)

**Payment and refund**

| Check | Result |
|---|---|
| E1, E2: account ready; buyer sent to hosted Checkout | PASS |
| E3a, E3, E3c: payment completes and updates the right order | PASS. The completion event marked the order paid and the artwork sold. Stripe's session and payment match that order; no other order was touched. |
| E4: Stripe's charge matches the pilot's ledger | PASS. €1,075 charged; €150 commission; €75 delivery outside commission. |
| E5: partial refund through the pilot | PASS. €100 refunded; €15 commission returned. |

**Abandoned checkout**

| Check | Result |
|---|---|
| E6: checkout expires | PASS. A real "checkout expired" event released the reservation. |

**Disputes**

| Check | Result |
|---|---|
| E7a, E7, E7c: dispute opens | PASS. The dispute was applied to the right order, including when the dispute event arrived before the payment event. |
| **E10: dispute closed as won** | **PASS.** A genuine signed "dispute closed" event (`evt_1UcqIBHx1Olx8cdwX14Gebtx`) returned the order to paid. The ledger shows −€50 then +€50 reinstated. |
| **E11: dispute closed as lost** | **PASS.** A genuine signed "dispute closed" event (`evt_1UcqITHx1Olx8cdwNR19jAxE`) marked the order refunded and flagged PlotArt's commission for return (founder action). |

**A refund that succeeds and later fails** (uses Stripe's test card for refunds that fail later)

| Check | Result |
|---|---|
| **E12a: refund first succeeds** | **PASS.** The €420 refund succeeded; the pilot recorded it and returned PlotArt's full €60 commission once. |
| **E12b: Stripe later fails it** | **PASS.** Real signed `refund.updated` and `refund.failed` events reconciled the order: back to paid; the ledger keeps the refund and adds reversal lines of +€400 and +€20; the flag says the buyer has not been repaid and the €60 commission stays with the artist. |
| **E12c: no double repayment** | **PASS.** The artist's direct repayment was recorded once, with no second commission refund (Stripe still shows €60 refunded). A further Stripe refund was refused, and no new refund was created on Stripe. |

**All events**

| Check | Result |
|---|---|
| E8: every expected event arrived and was processed | PASS. 16 real events were processed (payments, refunds, refund failure, dispute opened, updated and closed), and none failed. |

### A3. Local checks (simulated Stripe; not evidence from Stripe)

| Suite | Result |
|---|---|
| Checkout pilot | 145/145. Includes 8 checks of the refund-reversal handling, early-arriving events handled with no redelivery, and Adaptive Pricing off. |
| Migration 0016, run on the pre-change schema | 9/9 |
| Deployment tooling | 23/23 |
| Enquiry log | 26/26 |
| Gallery order | 17/17 |
| L1, L2: live key refused; test key present | PASS |

### A4. Fees measured in the sandbox, compared with published live pricing

**Balance-transaction breakdown on a €1,075 sale (sandbox):**

| Line | Irish test card (P7b) | US test card (P7) |
|---|---|---|
| Stripe processing fee | €16.38 | €34.11 |
| VAT on that fee | €3.77 | €7.85 |
| PlotArt application fee | €150.00 | €150.00 |
| Net to artist | **€904.85** | €883.04 |

**Dispute fees after closing (P15, sandbox):**

| Outcome | What happened | Net cost to the artist |
|---|---|---|
| Lost | −€50 disputed amount, plus a €20 "dispute fee" and €4.60 VAT | −€74.60 |
| Won | The same debit, then the €50 was reinstated. The €20 and its VAT were not returned. | −€24.60 |

**What is sandbox observation and what is published live pricing:**

- **Standard EEA card fee.** The sandbox fee matches Stripe's published 1.5% + €0.25 exactly.
- **International card fee.** The sandbox fee (€34.11) is below Stripe's published 3.25% + €0.25 (€35.19). Sandbox fees are not live pricing.
- **VAT on fees.** Stripe documents that VAT applies to all Stripe fees for Irish-based accounts, added on top of the fees. For accounts elsewhere in Europe, Stripe states it charges no VAT on its fees; the account holder may need to self-assess under the reverse charge. Whether VAT is a real cost depends on the artist's own VAT position.
- **Dispute fees.** Stripe publishes two fees for EEA accounts:
  - a €20 **dispute received fee**, not returned even if the dispute is won;
  - a €20 **dispute countered fee** when evidence is submitted, returned if the dispute is won.

  The sandbox charged only the received fee, although the test did submit evidence. The countered fee has therefore not been observed in test mode, and it should be assumed in live use.

---

## B. Unresolved technical gaps

| # | Gap | Status and reason |
|---|---|---|
| G1 | A refund larger than the artist's available and incoming balance combined ("fully unfunded") | **Unverified.** It can't be produced within the authorised sandbox permissions. The test key deliberately has no payout permission. The only alternative, refunding every earlier test charge on the shared test account, would corrupt the account the other checks rely on. Verified so far: Stripe completed refunds above the available balance at once, funding them from incoming payments, and once took the pending balance negative (−€73.83). Draft PA-PAY 7.3 marks this case as unverified. **To close it:** a second test account, onboarded by Colin with test data, drained by refunds or a manual sandbox payout. |
| G2 | Live pricing and live VAT | Not testable in the sandbox. Re-check Stripe's Irish pricing and VAT pages when the terms are issued. |
| G3 | Premium EEA and UK card fees | Not measured. The examples use Stripe's published rates. |
| G4 | Behaviour when live Stripe redelivers events | Not exercised; the test tool never redelivers. The pilot no longer depends on redelivery: early events are replayed by the pilot and the sweep, and repeated deliveries are ignored. Locally tested. |
| G5 | The dispute countered fee | Not charged in the sandbox (A4). Confirm on the first live dispute, or with Stripe. |
| G6 | Sweep backstops (deferred-event replay; recheck of refunds succeeded in the last 14 days) | Tested locally only. With the real webhooks, the events path was enough in run 18. |
| G7 | Production deployment, production migration, live keys, real artists | Out of scope by instruction. Nothing done. |

---

## C. Colin's commercial decisions (not technical; nothing adopted)

| # | Decision | Notes |
|---|---|---|
| D1 | Who bears Stripe's processing fees, including on the delivery portion | Model A (the artist pays Stripe's fee on top of commission) was used for technical testing only. The alternative assessed was making 15% the artist's total deduction, with PlotArt absorbing Stripe's fee. With VAT, Stripe's fee is about 1.9% on a standard EEA card for an Irish account, and far more on non-EEA cards. |
| D2 | Whether PlotArt issues any receipt to buyers | Open, as in the draft. |
| D3 | Retention periods | Confirm with the accountant. |
| D4 | Who responds to disputes | Artists only, in their own Stripe Dashboard (current draft cl. 7.5), or may PlotArt submit evidence for them? Responding triggers the €20 countered fee, which is returned only if the dispute is won. |
| D5 | Returning commission after a lost dispute | The pilot currently flags it for a founder action ("Refund commission only"). Should it be automatic? |
| D6 | Approving the r4 draft wording | PA-PAY r4: separate processing-fee and conditional VAT lines; split dispute fees; observed low-balance refund behaviour; new cl. 7.3A on reversed refunds. PA-BPT r4: reversed refunds. **Drafts only; not issued.** |
| D7 | Professional advice still outstanding | Marketplace and consumer responsibilities, VAT on commission, DAC7, anti-money-laundering position (from the earlier reviews). |
| D8 | Whether to set up a second sandbox account to close G1 | Optional. It needs Colin to onboard a second test account. |

---

## D. Changes made in this round (on the branch only)

**Pilot code**

- A refund that succeeds and later fails is now reconciled: append-only reversal lines in the ledger; the order returns to paid with an accurate flag; commission is not returned twice; the buyer can be repaid by one route only. The sweep re-reads recently succeeded refunds as a backstop.
- Events that arrive before their payment completion are replayed by the pilot.
- Adaptive Pricing is off.
- Accounts v2 and the current API parameters are used, with API versions pinned.

**Tests**

- End-to-end checks E10 and E11 (dispute closed, won and lost) and E12a–c (refund reversal), plus E3c and E7c (event matched to the right order).
- P15 records dispute fees after closing.
- Browser diagnostics with payment details masked.
- E8 counts only when the expected events actually arrived.

**Draft documents**

- PA-PAY and PA-BPT r4. Decision list updated with D4 and D5.

---

## What to send to ChatGPT

The PlotArt managed-checkout pilot (Stripe Connect, test mode only) now passes the full Stripe test-mode suite: run 18, 39 passed, 0 failed, 1 deliberate skip. Nothing has been merged or deployed, production is unchanged, live payments are off, and no terms have been issued.

**Verified with the real Stripe test API:**

- Accounts v2 configuration: the artist pays fees, Stripe carries losses, and the artist has the full Dashboard.
- Checkout in euro with Adaptive Pricing off.
- A €1,075 payment with a €150 application fee.
- Refunds and commission refunds, each made once only.
- A refund that fails asynchronously.
- Disputes won and lost.

**Verified end to end, with a real hosted Checkout payment and genuine signed events:**

- The payment marked the correct order paid, cross-checked against Stripe.
- Partial refund through the pilot.
- An abandoned checkout released the reservation.
- A dispute opened, including when its event arrived before the payment event.
- **A dispute closed as won** returned the order to paid and reinstated €50.
- **A dispute closed as lost** marked the order refunded and flagged the commission for return.
- **A refund that succeeded and later failed** was reconciled. The order went back to paid, with reversal lines in the ledger and the buyer flagged as not repaid. The €60 commission already returned was not returned again. The direct repayment was recorded once, and a further Stripe refund was refused, with none created.

**Fees, sandbox compared with live:**

- Irish card: €16.38 + €3.77 VAT; matches the published 1.5% + €0.25.
- US card: €34.11; below the published 3.25% + €0.25, so not live pricing.
- VAT on Stripe fees applies for Irish-based accounts. For other European accounts it may be self-assessed. Whether it is a real cost depends on the artist.
- Disputes: the sandbox charged €20 + €4.60 VAT, which was not returned when the dispute was won. Stripe also publishes a €20 countered fee, returned on a win, which the sandbox did not charge.

**Gaps:**

- The fully unfunded refund is unverified; it needs payout permission or a second test account.
- Live pricing and VAT.
- Premium and UK card fees.
- Live redelivery behaviour.
- The countered fee.

**Founder decisions:**

- D1: who bears Stripe's fees.
- D2: buyer receipts.
- D3: retention periods.
- D4: who responds to disputes.
- D5: whether commission is returned automatically after a lost dispute.
- D6: approval of the r4 draft wording.
- D7: professional advice still outstanding.
- D8: whether to set up a second sandbox account.
