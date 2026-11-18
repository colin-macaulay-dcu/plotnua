# PA-PAY / PA-BPT draft r9 · review notes (18 November 2026)

Internal notes for founder and professional review; not customer-facing. r8 notes (`PA-PAY-PA-BPT-r8-REVIEW-NOTES.md`) still apply except as changed here.

## Changes in r9
- PA-PAY 3.3(b)–(e): seven calendar days (Irish dates, day after payment = day one), extension only where Stripe had not recorded the fee by the original deadline, completion defined as Stripe's acceptance of the application-fee refund, bank payout kept separate. "Normally within minutes" removed (no time-of-day promise).
- PA-BPT: unchanged.

## Founder decision status
- Seven days: proposed sandbox rule, **provisional pending the founder's review of the results**.
- 30-day shortfall period (3.5): separate decision, unchanged, provisional.

## Evidence
- Results, desk wording, delay notice and gaps: `reports/plotart-seven-day-reimbursement-2026-11-18.md`.
- Real sandbox: run 33 (Actions 44259652058; concluded failure because of the E21c matcher only; evidence in `reports/stripe-run-33-evidence.md`).
- Local simulated: `reports/seven-day-local-simulated-evidence-2026-11-18.json`.

## For review
- Insufficient platform balance for an application-fee refund: Stripe's documentation does not say what happens; untested.
- The pilot cannot itself verify the artist-side credit (runtime key has no Balance Read on connected accounts).
