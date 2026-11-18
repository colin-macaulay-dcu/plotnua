# PA-PAY / PA-BPT draft r9 · review notes (18 November 2026)

Internal notes for founder and professional review; not customer-facing. r8 notes (`PA-PAY-PA-BPT-r8-REVIEW-NOTES.md`) still apply except as changed here.

## Changes in r9
- PA-PAY 3.3(b)–(e): seven calendar days (Irish dates, day after payment = day one), extension only where Stripe had not recorded the fee by the original deadline, completion defined as Stripe's acceptance of the application-fee refund, bank payout kept separate. "Normally within minutes" removed (no time-of-day promise).
- PA-BPT: unchanged.

## Founder decision status (recorded separately, 18 November 2026)
- **PA-PAY 3.3, processing-fee reimbursement: seven Irish calendar days — APPROVED by the founder at 09:30 on 18 November 2026 as the sandbox pilot rule.** Scope: the sandbox pilot only. It does not issue the terms, which remain an unissued draft, and does not approve live use. The brackets around "seventh" in 3.3(b) and (c) are removed for that reason only. Recorded in code as `DEADLINE_DECISIONS.reimburse_days` (`src/checkout.js`).
- **PA-PAY 3.5, bank-transfer shortfall: 30 Irish calendar days — APPROVED by the founder at 09:40 on 18 November 2026 as the sandbox pilot rule**, for both processing-fee and commission-return shortfalls. Start: the Irish date of the transaction record that first established the amount owed by bank transfer; day one is the next day; due by the end of day 30 (Europe/Dublin). Scope: sandbox only; terms remain an unissued draft. Recorded as `DEADLINE_DECISIONS.shortfall_days`. Evidence: `reports/plotart-shortfall-30-day-results-2026-11-18.md`.
- **Founder follow-up (internal, not in the terms):** the founder owns follow-up; internal target to resolve an overdue amount is 5 working days after the deadline; the artist's deadline still applies.
- `CHECKOUT_DEADLINES_APPROVED` approved both deadlines at once. It is left unset and is no longer read; each deadline is now approved only by its own entry.
- Pre-live (open): what Stripe does with an application-fee refund when PlotArt's platform balance cannot cover it.

## Evidence
- Results, desk wording, delay notice and gaps: `reports/plotart-seven-day-reimbursement-2026-11-18.md`.
- Real sandbox: run 33 (Actions 44259652058; concluded failure because of the E21c matcher only; evidence in `reports/stripe-run-33-evidence.md`) and run 34 (Actions 44264008409; success; E21c, E21e, E21f passed; `reports/stripe-run-34-evidence.md`).
- Local simulated: `reports/seven-day-local-simulated-evidence-2026-11-18.json`.

## For review
- Insufficient platform balance for an application-fee refund: Stripe's documentation does not say what happens; untested.
- The pilot cannot itself verify the artist-side credit (runtime key has no Balance Read on connected accounts).

## Founder decision F2 — traders only (18 November 2026, 10:00)
- **Option A adopted for the sandbox pilot.** PlotArt-managed checkout is limited to artists who confirm they sell as traders. The requirement applies only when an artist chooses managed checkout; gallery access, enquiries, direct sales and the Founding 25 arrangements are unaffected. There is no switch to allow other sellers (`CHECKOUT_ALLOW_NON_TRADER_SELLERS` removed).
- Drafts: PA-PAY new 2.3 (later clauses renumbered 2.4–2.6) and PA-BPT 1.2 (single option). Both carry a bracket for professional review before live use (definition of trader, reliance on the declaration, Consumer Rights Act 2022 s.107).
- Studio: a neutral three-way choice ("I sell as a trader" / "I do not sell as a trader" / "I'm not sure"), with what each means for checkout and a note that an unsure artist need not complete the form and can keep selling directly.
- Evidence: `reports/plotart-traders-only-and-returned-transfer-2026-11-18.md`; run 35 (E22).

## §3.5 returned-transfer notice (18 November 2026)
- One correction notice to the artist per returned transfer, naming the returned payment, the amount still owed and the unchanged due date. Test sink only.
