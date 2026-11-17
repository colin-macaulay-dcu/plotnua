# PlotArt managed checkout — fee model B: implementation and Stripe test results (17 November 2026)

**Test mode only.** Branch `plotart/managed-checkout-pilot` (PR #20), commits `075b2de` (code) and `842432e` (drafts).

Not done, and not to be done without approval: merge, deployment, production migration, issued terms or live payments. Migration 0016 is still unapplied everywhere. No key permissions were changed.

## 1. What was implemented

| Requirement | Implementation |
|---|---|
| Combined deduction ≤ commission on commission-bearing orders | PlotArt reimburses Stripe's **actual** processing fee + the VAT Stripe charged on it, on the whole payment including delivery. The reimbursement is a partial application-fee refund (approach B2), made after Stripe records the fee. |
| Actual amounts, not estimates | Amounts are read from the charge's balance transaction (`fee_details`: `stripe_fee`, `tax`). Until Stripe records them, the order shows `awaiting_fee` and nothing is paid. |
| No duplicate reimbursements | The ledger is unique per Stripe object. The idempotency key includes the cost and the amount already reimbursed. Payment completion, the 15-minute sweep and the founder "Reconcile processing fee" button can all run repeatedly. |
| Commission on artwork only | Unchanged. Commission is booked in full; the reimbursement is a separate ledger line. |
| Refunds account for reimbursements already made | Commission refunds and the reimbursement share one pot (the application fee). Each is capped at what is left. Any excess becomes a **shortfall**. Commission shortfalls count as settled, so nothing is returned twice, including after a reversed refund or a direct repayment. |
| Shortfall | Flagged on the order and shown on the statement as "still owed by PlotArt". The required funding is a **direct payment by PlotArt** (for example a bank transfer); Stripe cannot pay it from that order. The founder records it once ("Record shortfall paid…"); overpaying or recording twice is refused. Nothing pays it automatically. |
| Statements | Every order view (artist and founder) and the Studio UI show: gross, of which artwork and delivery, commission, commission refunded, Stripe processing fee, VAT on it, reimbursement, shortfall paid or owed, other Stripe fees not reimbursed, refunds, disputes and net proceeds. |
| Founding Artist protections; commission-free orders | Orders with no commission (including every Founding Enquiry) are refused at artist approval, issue and checkout, and stay on direct payment. The commission entitlement rules are untouched. |
| Disputes and other charges | **Not absorbed.** Dispute fees, add-on fees (flagged as excluded) and payout fees remain the seller's. |
| r5 inconsistencies | **Reservation:** one open quote per work is now enforced in code, and both drafts are aligned. **Pending refund:** PA-BPT 8.2 no longer suggests direct repayment while a refund is pending. **Retention:** both drafts state the code's actual rule. |

## 2. Actual Stripe test results — run 19 (GitHub Actions 44161463466, test mode)

Totals: 46 PASS (24 Stripe API, 22 Stripe + pilot end to end), 5 INFO, 1 SKIP (account creation reused), **0 FAIL**, plus 2 local preflight PASS. Every signed webhook event processed; none failed (E8).

**Model B checks, against Stripe**

| Check | Result | Real Stripe amounts |
|---|---|---|
| P16a — fee read from the balance transaction (Irish card, €1,075) | PASS | `stripe_fee` €16.38 and `tax` €3.77, computed cost **€20.15** |
| P16b — partial application-fee refund of exactly that; same key repeated | PASS | One fee refund of €20.15; the repeat returned the same id |
| P16c — Stripe refuses a refund above what is left of the fee | PASS | "greater than unrefunded amount on fee (€129.85)" |
| P16d — full buyer refund: only the remainder goes back through Stripe | PASS | €129.85 returned; fee fully refunded (€150); **€20.15 shortfall** owed outside Stripe |

**Model B checks, end to end** (real hosted Checkout, real signed events, pilot code)

| Check | Result | Real Stripe amounts |
|---|---|---|
| E13 — reimbursement after a real Checkout payment (€1,075, US test card) | PASS | `stripe_fee` €34.11 and `tax` €7.85; one reimbursement of **€41.96** |
| E13b — reconcile again (founder button and sweep) | PASS | Still one fee refund |
| E5 — partial artwork refund of €100 | PASS | €15 commission returned; fee refunded in total €56.96 (€41.96 + €15) |
| E13c — statement | PASS | Gross €1,075; commission €150; commission refunded €15; fee €34.11; VAT €7.85; reimbursed €41.96; refunded €100; **net €840.00** (= €1,075 − €100 − €150 + €15) |
| E14 — dispute (won) | PASS | Only the €2.25 processing reimbursement was paid. Stripe's dispute fees of **€24.60** (incl. VAT) were not reimbursed, and the statement says so. |
| E12a — full refund (€420, refund-fail card) | PASS | €43.42 commission returned through Stripe, **€16.58 shortfall flagged** (processing €13.48 + VAT €3.10) |
| E12b — Stripe then fails the refund (signed events) | PASS | Order back to paid; the flag states how the €60 commission was settled (€43.42 + €16.58 owed directly) |
| E12c — artist's direct repayment | PASS | No second commission refund; a further Stripe refund was refused |
| E12d — shortfall after the reversal | PASS | Still €16.58 (not doubled); recorded once (a second record was refused); statement net €0.00 |

**Unchanged checks that still pass:** onboarding, Checkout, payments, partial and full refunds, the asynchronous refund failure, disputes won and lost (API and signed events), deferred-event handling, expiry.

## 3. Local mocked results (kept separate from Stripe)

| Suite | Result |
|---|---|
| `prove-checkout-pilot` | 157/157. New: MB1–MB10, covering reimbursement, idempotency, statement, partial and full refund capping, the shortfall flag, recording the shortfall, `awaiting_fee`, add-on exclusion, and disputes not absorbed. Also new: T6a (one open quote per work) and T6a2 (simultaneous checkout on one quote). |
| `prove-migration-0016` | 9/9 |
| `prove-checkout-deploy` | 23/23 |
| `prove-enquiry-log` | 26/26 |
| `prove-gallery-order` | 17/17 |
| `prove-leaving` | 27/27 |

`prove-studio` needs the external gallery-tools folder and was not run; it is unrelated to the pilot.

## 4. Drafts (unissued)

- **PA-PAY r6:** Model B (cl. 3.3–3.8), with four worked examples: sale, partial refund, full refund with shortfall, and a shortfall at payment. Also: commission-free orders excluded (1.3), reservation (4.3), pending refund (7.5), commission and reimbursement interaction (7.7), dispute fees not absorbed (7.8), retention (8.1).
- **PA-BPT r6:** reservation (4.1–4.2), pending vs failed refunds (8.2–8.4), retention (9.1).
- **Review notes r6:** change table, conflict status (C1 and C2 resolved by the decision; C9 moot), new decisions F11–F13, gaps and professional-review points.

## 5. Remaining gaps

1. **Shortfalls rely on PlotArt paying by hand.** The code flags and records them; it pays nothing. A deadline (draft brackets [30] days), a route for the artist's bank details and a monitoring owner are needed. There is no escalation timer for shortfalls yet.
2. **VAT double recovery.** A VAT-registered Irish artist may reclaim the Stripe-fee VAT that PlotArt also reimburses. This is a tax-review point; the decision as given is "including VAT".
3. **Dispute fees** are not read into the pilot ledger. The statement says they are excluded, and the artist sees them in Stripe.
4. **Add-on fee exclusion** (Radar, currency conversion and similar) is proven only in the mock. The sandbox showed no such lines. Recheck on the first live balance transactions.
5. **Late disputes.** A dispute after an order's retention date is fixed needs a manual legal hold.
6. **Still open from earlier rounds:**
   - the fully unfunded refund case (second-account phase prepared; waiting for "ready" to send the onboarding link);
   - the privacy probe;
   - live pricing and VAT;
   - the countered dispute fee;
   - seller and return information on the quote;
   - buyer confirmation emails (no mailer);
   - lost-dispute commission return process.
7. Dormant processing-consent code remains. It can no longer enable an order and can be removed once confirmed.
