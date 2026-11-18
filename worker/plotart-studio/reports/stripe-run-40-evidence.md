# Run 40 · low-platform-balance reimbursement · evidence

- Actions run: https://github.com/colin-macaulay-dcu/plotnua/actions/runs/44394666891 (commit 336ce47); approved by the founder; conclusion: failure.
- Summary: PASS 5 · FAIL 1 · SKIP 1 · INFO 1 · INCONCLUSIVE 0

| Check | Result |
|---|---|
| L1, L2, E17b, E17c, E1 | PASS (live key refused; test key; runtime key restrictions unchanged; test account ready) |
| E24-0 platform EUR balance, read-only | **FAIL: HTTP 403 `more_permissions_required`.** The harness test key (rk_test_…vukQ) has no Balance Read on PlotArt's own account. |
| E24 low-balance reimbursement | SKIP: stopped at the read-only gate |

**Nothing was created at Stripe in the balance part of this run.** No €1.00 probe, no order, no payment, no fee refund and no payout. Nothing needs restoring.

Next: the harness needs Balance Read on PlotArt's own account (and, depending on the balance, a way to lower it). Founder decision required before any key change. See the chat for the options.
