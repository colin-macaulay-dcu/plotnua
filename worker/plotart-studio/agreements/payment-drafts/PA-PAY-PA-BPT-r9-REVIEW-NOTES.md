# PA-PAY / PA-BPT draft r9 · review notes (18 November 2026)

Internal notes for founder and professional review; not customer-facing. r8 notes (`PA-PAY-PA-BPT-r8-REVIEW-NOTES.md`) still apply except as changed here.

## Changes in r9
- PA-PAY 3.3(b)–(e): seven calendar days (Irish dates, day after payment = day one), extension only where Stripe had not recorded the fee by the original deadline, completion defined as Stripe's acceptance of the application-fee refund, bank payout kept separate. "Normally within minutes" removed (no time-of-day promise).
- PA-BPT: unchanged.

## Founder decision status (recorded separately, 18 November 2026)
- **PA-PAY 3.3, processing-fee reimbursement: seven Irish calendar days — APPROVED by the founder at 09:30 on 18 November 2026 as the sandbox pilot rule.** Scope: the sandbox pilot only. It does not issue the terms, which remain an unissued draft, and does not approve live use. The brackets around "seventh" in 3.3(b) and (c) are removed for that reason only. Recorded in code as `DEADLINE_DECISIONS.reimburse_days` (`src/checkout.js`).
- **PA-PAY 3.5, bank-transfer shortfall: 30 days — still PROVISIONAL.** Separate decision, next for the founder (`reports/plotart-shortfall-30-day-decision-2026-11-18.md`). Recorded as `DEADLINE_DECISIONS.shortfall_days`, status provisional.
- `CHECKOUT_DEADLINES_APPROVED` approved both deadlines at once. It is left unset and is no longer read; each deadline is now approved only by its own entry.
- Pre-live (open): what Stripe does with an application-fee refund when PlotArt's platform balance cannot cover it.

## Evidence
- Results, desk wording, delay notice and gaps: `reports/plotart-seven-day-reimbursement-2026-11-18.md`.
- Real sandbox: run 33 (Actions 44259652058; concluded failure because of the E21c matcher only; evidence in `reports/stripe-run-33-evidence.md`) and run 34 (Actions 44264008409; success; E21c, E21e, E21f passed; `reports/stripe-run-34-evidence.md`).
- Local simulated: `reports/seven-day-local-simulated-evidence-2026-11-18.json`.

## For review
- Insufficient platform balance for an application-fee refund: Stripe's documentation does not say what happens; untested.
- The pilot cannot itself verify the artist-side credit (runtime key has no Balance Read on connected accounts).
