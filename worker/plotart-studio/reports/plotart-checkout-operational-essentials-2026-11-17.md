# PlotArt managed checkout: operational essentials, implementation and test results (17 November 2026)

**Test mode only.** Branch `plotart/managed-checkout-pilot` (PR #20).

No merge, deployment, production migration, issued terms or live activation. Migration 0016 is still unapplied anywhere. The Stripe key's permissions are unchanged. Founding Artist protections and their direct-payment route are unchanged; commission-free orders are still refused by the pilot.

## 1. Completed and outstanding

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Seller identity, address, contact and trader status: entered by the artist, required before approval and issue, frozen per quote | **Done** | Local SP1–SP6, QS1–QS3; real E2–E3 used it |
| 1 | Structured return arrangements (method, address, fixed or maximum cost, who arranges) required before issue; shown to the buyer | **Done** | Local RT1–RT2, B1a |
| 1 | Exact approved quote snapshot (append-only, SHA-256) | **Done** | Local QS1–QS3 |
| 2 | Buyer confirmation: artwork, seller, amounts, delivery, returns, accepted terms (id, fingerprint, full text), cancellation form; exact copy and delivery record kept; test sink only | **Done** | Local BC1–BC6; **real E15** |
| 3 | Founder queue: amount, paid, outstanding, age, due date (provisional), rule, reminders, payment evidence; waiting reimbursements | **Done** | Local OQ1–OQ6, MB8b |
| 3 | Owed vs paid kept separate in statements and settlement; duplicate-payment protection | **Done** | Local OQ3–OQ4, MB7; real E12d |
| 3 | Secure process for bank details; nothing that looks like bank details accepted in records | **Done** (procedure: `PILOT-SHORTFALL-PAYMENTS.md`) | Local OQ2 |
| 4 | Actual dispute fees and their returns in ledger and net proceeds; unavailable fees labelled | **Done** | Local DF1–DF2, MB10; **real E14, E16** |
| 4 | Queue for commission owed after lost disputes (PA-GAA 9.1, 30 days) | **Done** | Local LD1–LD3; **real E16** |
| 5 | Sandbox access check (field names only) | **Done** | **Real V1–V5** |
| 5 | Draft privacy wording updated to actual access and storage | **Done** (drafts r7) | — |
| 5 | Later disputes prevent deletion while unresolved | **Done** (automatic hold, sweep guard, database trigger) | Local RH1–RH3 |
| 6 | Second sandbox account for the fully unfunded refund | **Prepared**: `acct_1Uct3vHx1OnYJa8H`, no link yet | **Real U1** |
| 6 | Unfunded refund test itself | **Outstanding**: needs your onboarding | — |
| 7 | Draft corrections (pending refunds, Example 2, reconciliation with behaviour, open decisions marked) | **Done** (r7) | — |
| — | Live email sending, buyer refund notices, deadline approval | **Outstanding** (founder decisions) | — |

## 2. Real Stripe results: run 20 (Actions 44167976954, test mode)

**Totals:** 49 PASS (25 Stripe API, 24 Stripe + pilot end to end), 11 INFO, 1 SKIP (account creation reused), **0 FAIL**, plus 2 local preflight PASS. All signed webhook events were processed (E8).

| Check | Result | Provider evidence |
|---|---|---|
| E15: buyer confirmation after a real signed payment | PASS | Prepared once (3,666 characters, SHA-256 `6ea76987…`). One delivery, held in the test sink. The buyer link served identical text. No email address appears in the sink. |
| E13/E13b/E5/E13c: fee model B with real amounts | PASS | `stripe_fee` €34.11 + `tax` €7.85 = €41.96 reimbursed once; statement net €840.00 |
| E14: dispute (won) | PASS | Stripe's dispute fee **€24.60** (incl. VAT) read from the dispute's balance transaction and booked. Not reimbursed and not returned on a win. Statement net €17.90 (€50.00 − €7.50 commission − €2.25 processing + €2.25 reimbursed − €24.60). |
| E16: dispute (lost) | PASS | €7.50 commission queued, due in 30 days (PA-GAA 9.1). Returned: €5.25 through Stripe, €2.25 (the processing already reimbursed) moved to a direct-payment item. The fee was fully refunded on Stripe. The €24.60 dispute fees are in the statement. |
| E12a–E12d: full refund, reversal, shortfall | PASS | €16.58 shortfall (due 17 Dec, provisional); recorded once; a second record was refused |
| P16a–P16d: reimbursement mechanics | PASS | €16.38 + €3.77 on an Irish card |
| U1: second sandbox account | PASS | Created with the pilot configuration; **no onboarding link generated** |

**Privacy access check (V1–V5).** Field names only; no values were recorded.

| Data subject | The key **can view** | The key **cannot view** |
|---|---|---|
| Artist | email, name, address, date of birth, business phone and URL, bank name and country, routing (branch) number, last 4 of the payout account; through v2, also identity documents and identity-number fields | full account number |
| Buyer | name, email, billing country, card brand, country, funding type, expiry, last 4, fingerprint, receipt URL | full card number |

PlotArt stores none of these beyond payment ids, amounts and statuses. The drafts now say so. Narrowing the key is for you to decide (F14); I have not changed it.

## 3. Local mocked results (kept separate from the Stripe results)

| Suite | Result |
|---|---|
| `prove-checkout-pilot` | **190/190** (new: SP1–SP6, QS1–QS3, B1a, RT1–RT2, BC1–BC6, OQ1–OQ6, MB8b, LD1–LD3, DF1–DF2, RH1–RH3) |
| `prove-migration-0016` | 9/9 (21 pilot tables; rollback updated) |
| `prove-checkout-deploy` | 23/23 |
| `prove-enquiry-log` | 26/26 |
| `prove-gallery-order` | 17/17 |
| `prove-leaving` | 27/27 |
| `prove-agreement` | 35/35 |

## 4. Inputs needed from you

1. **Unfunded-refund onboarding.** Tell me when you can spend about 5 minutes. I will then request a run that generates the short-lived link for the second account, and send it to you.
2. **Deadlines (F11/F12).** Approve 30 days for shortfalls and 7 days for reimbursements, or give other periods. They stay marked provisional until you do.
3. **F2.** Traders only (the current default), or allow sellers who are not traders.
4. **F14.** Whether to ask Stripe for narrower read access.
5. **F15.** Who checks the "amounts owed" queue, and how often.
6. Before live use only: an email provider for buyer confirmations and notices.
