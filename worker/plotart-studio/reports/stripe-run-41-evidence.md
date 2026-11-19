# Run 41 · read-only platform balance check · evidence

- Actions run: https://github.com/colin-macaulay-dcu/plotnua/actions/runs/44395389677; approved by the founder; conclusion: failure.
- B0, PlotArt's own balance (GET /v1/balance, harness key rk_test_…vukQ): **FAIL, HTTP 403 `more_permissions_required` (balance_read)**, the same as run 40.
- Read only; nothing was created at Stripe.
- The founder reported granting Balance → Read ("In your account") at 20:51. The key the job used (ending vukQ, account acct_1UbJNrHx1O88AXec) still lacks it at 20:52. To check: which key was edited, and whether it was saved.
