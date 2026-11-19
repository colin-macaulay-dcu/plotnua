# PA-PAY / PA-BPT r8: internal review notes (17 November 2026)

**Internal. Not customer-facing. Neither draft is issued, accepted or installed.** These notes add to the r5–r7 notes.

## 1. Changes from r7 to r8

| # | Draft | Change | Behaviour it rests on |
|---|---|---|---|
| 1 | PA-PAY 7.5, 7.6; PA-BPT 8.4 | Buyers are now told about pending, failed and reversed refunds. In test mode the notices appear on the buyer's quote page; email is bracketed until sending is approved. | `buyerRefundNotice`: one stored notice per refund and kind; test sink; retries; founder re-delivery. Local checks BN1–BN6; e2e E18 added. |
| 2 | PA-PAY 3.5, new 9.8 | Bank details are now described as they are actually processed: asked for by phone, entered only in PlotArt's business online banking, never entered in Studio, the pilot, logs or emails. The bank keeps them as a saved payee (PlotArt deletes it when no longer needed) and in its transfer records, which are kept as accounting records for six years and cannot be deleted. | `PILOT-SHORTFALL-PAYMENTS.md` step 8; the pilot rejects payment references that look like bank details (local check OQ2). |
| 3 | New: `PRIVACY-NOTICE-PILOT-SECTION-DRAFT.md` | One draft privacy-notice section covering: purposes, data kept, data viewable through Stripe but not kept, bank details, recipients (Resend in brackets), retention, rights. | Run 20 V1–V5; PA-PAY 9 |

## 2. Reconciliation check (implementation ↔ procedure ↔ PA-PAY ↔ PA-BPT ↔ privacy draft)

| Topic | Code | Procedure | PA-PAY | PA-BPT | Privacy draft | Consistent? |
|---|---|---|---|---|---|---|
| Seller information required, frozen per quote | yes | — | 2.2 | 1.1 | yes | ✓ |
| Trader-only default (F2 open) | `CHECKOUT_ALLOW_NON_TRADER_SELLERS` unset | — | 2.2 bracket | 1.2 note | — | ✓ |
| Returns: structured and required | yes | — | 7.2 | 6.3 | — | ✓ |
| One open quote per work | yes | — | 4.3 | 4.1–4.2 | — | ✓ |
| Confirmation kept; opened from the quote link; email pending | yes | — | — | 3.3 | Resend row bracketed | ✓ |
| Refund notices to buyers | yes | — | 7.5–7.6 | 8.2–8.4 | — | ✓ |
| Pending refund means not completed; no direct repayment while pending | yes (flag text, notice) | — | 7.5 | 8.2 | — | ✓ |
| Model B reimbursement; shortfall paid directly | yes | §1 | 3.3–3.5 | — | — | ✓ |
| Deadlines provisional | yes (`CHECKOUT_DEADLINES_APPROVED`) | §4 | 3.3(b), 3.5 brackets | — | — | ✓ |
| Lost-dispute commission within 30 days (PA-GAA 9.1) | yes | §1 | 7.7(c) | — | — | ✓ |
| Dispute fees shown, not reimbursed; unavailable fees labelled | yes | — | 3.4, 3.8, 7.8 | — | — | ✓ |
| Bank details only at the bank | yes (references checked) | §2 | 3.5, 9.8 | — | yes | ✓ (corrected in r8) |
| Retention: settled + 6 years; never while a dispute is open; automatic hold for a late dispute | yes | §3 | 8.1 | 9.1 | yes | ✓ |
| Viewable through Stripe but not kept | probe | — | 9.3 | 9.2(c) | yes | ✓ (update if F14 narrows access) |
| Commission-free orders stay direct | yes | — | 1.3(a), 0.2(a) | — | — | ✓ |

**Durable medium.** No inconsistency was found, but one point remains open: whether a confirmation reached only through the quote link counts as a "durable medium" before email exists. This is a legal-review point, and email sending would remove it.

## 3. Still open

These are listed in the consolidated report's decision table: F2, F5–F15, email approval, and the runtime key.

## 4. Fully unfunded refund: real Stripe result (run 28, 17 Nov 2026, sandbox): CLOSED AS PASSED

Account `acct_1Uct3vHx1OnYJa8H`, onboarded by the founder with test data (U3 PASS: charges enabled, nothing due, pilot configuration).

| Step | Available | Pending | Stripe refund status | Source |
|---|---|---|---|---|
| Before | €0.00 | €0.00 | — | U4 (observed) |
| €100 sale (€15 application fee) | €0.00 | €80.82 | — | U5 (observed): net €80.82 after commission, Stripe's fee and VAT |
| €100 refund (€19.18 more than the account held) | €0.00 | **−€19.18** | **succeeded** at creation; still succeeded after 31 s | U6 (observed) |
| €20 sale (€3 application fee) | — | — | — | **Inferred net €15.92** (= €20.00 − €3.00 commission − €1.08 Stripe fee and VAT). U7's "balance before refund" (−€19.18) was read immediately after this sale, before Stripe had recorded its balance transaction. |
| €20 refund | €0.00 | **−€23.26** | **succeeded** at creation | U7 (observed) |
| Reconciliation | | −€19.18 + €15.92 − €20.00 = **−€23.26** | | The €15.92 is inferred; the next run reads the actual balance transactions (U8) to confirm it line by line. |

**"Succeeded" is not "credited".**
- Stripe's status "succeeded" means the refund was sent. Stripe states that the refund has been successfully initiated, but this doesn't guarantee that it has landed on the customer's side ([Stripe: Understanding refund statuses](https://support.stripe.com/questions/understanding-refund-statuses)).
- Stripe states that the customer sees the credit approximately 5–10 business days later, depending on their bank ([Stripe: Refund and cancel payments](https://docs.stripe.com/docs/refunds)).
- In test mode no card is credited. The test shows Stripe's status and balances only.

**Who carries a negative balance (documented, not observed).**
- The pilot's accounts use `losses_collector = stripe`. Stripe's documentation says that with this setting, Stripe is liable for the connected account's negative balances, while the platform remains liable for negative balances on its own platform account ([Stripe: Connected account configuration](https://edge-docs.stripe.com/connect/accounts-v2/connected-account-configuration)).
- Stripe also says it assumes losses from **unrecoverable** negative balances on such accounts ([Stripe: Managed Risk](https://docs.stripe.com/connect/risk-management/connected-accounts-with-managed-risk)).
- Stripe documents that while an account's balance is negative, Stripe does not send payouts to the account's bank until the balance is positive again ([Stripe: Connect account balances](https://docs.stripe.com/connect/account-balances?locale=en-GB)).
- Stripe attempts to debit the account's external bank account if `debit_negative_balances` is set to true ([Stripe: Connect disputes](https://docs.stripe.com/connect/disputes.md)). **Not checked for the pilot accounts.**
- **For review before issue:**
  - what the artist owes Stripe, and how Stripe recovers it, under the Stripe Connected Account Agreement;
  - whether `debit_negative_balances` applies to these accounts.

  PA-PAY 7.5 marks both points for review rather than stating them.

**Pilot handling.**
- A succeeded refund is booked as usual: refund lines, then the commission refund. Under Model B the commission refund is capped by what is left of the application fee, and any remainder is owed directly (cl. 3.5).
- The negative balance changes none of PlotArt's obligations to the artist under cl. 3.3–3.5 and 7.7. PA-PAY 7.5 now says so.
- No buyer notice is needed for a succeeded refund.

**Deferred (founder, 22:15).** An alert for a negative artist balance.
