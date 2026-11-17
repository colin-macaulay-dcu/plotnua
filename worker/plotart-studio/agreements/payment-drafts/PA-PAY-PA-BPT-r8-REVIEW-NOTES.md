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

## 4. Fully unfunded refund: real Stripe result (run 28, 17 Nov 2026, sandbox)

Account `acct_1Uct3vHx1OnYJa8H`, onboarded by the founder with test data (U3 PASS: charges enabled, nothing due, pilot configuration).

| Step | Balance (available / pending) | Stripe result |
|---|---|---|
| Before | €0.00 / €0.00 | — |
| €100 sale (€15 application fee) | €0.00 / €80.82 | Payment succeeded; net €80.82 after commission, Stripe's fee and VAT |
| €100 refund (€19.18 more than the account held) | €0.00 / **−€19.18** | Refund **succeeded immediately** (`succeeded`; never pending in 31 seconds) |
| A further €20 refund while already negative | €0.00 / **−€23.26** | Also **succeeded immediately** |

**Conclusion.** In this case Stripe did not hold the refund as pending. It completed it and let the artist's balance go negative. Because the account is configured with Stripe as losses collector, Stripe recovers the negative balance from the artist, not from PlotArt.

**Pilot handling.** A succeeded refund is booked as usual: refund lines, commission refund (capped by Model B), and settlement. The buyer is repaid, so no buyer notice is needed.

**Gap.** The pilot does not alert anyone that the artist's balance is now negative (optional O5 in the r5 notes). It would need `balance_read` for connected accounts on the Studio key only.

**Drafts.** PA-PAY 7.5 is updated: the bracket is removed, (a) states that refunds can complete into a negative balance, and (b) keeps the pending case. Pending refunds were not observed in this run but remain possible under Stripe's terms.
