# Run 39 · founder-only sandbox email test · evidence

- Actions run: https://github.com/colin-macaulay-dcu/plotnua/actions/runs/44388837509 (commit 6955d9c, branch plotart/managed-checkout-pilot)
- Requested 18 Nov 2026 20:14; approved by the founder; conclusion: success.
- Summary line: STRIPE TEST MODE · PASS 8 · FAIL 0 · SKIP 0 · INFO 1 · INCONCLUSIVE 0

| Check | Result |
|---|---|
| L1 adapter refuses a live key | PASS |
| L2 Stripe TEST key configured | PASS |
| M0 prerequisites present (values not printed; recipient recorded by fingerprint) | PASS |
| M1 Resend ACCEPTANCE: exactly two requests (one urgent alert, one manual digest), both HTTP 200 with an email id, both subjects "SANDBOX TEST", approved sender, reply-to hello@plotnua.ie | PASS |
| M2 artist and buyer messages held in the test sink; no request to any other address | PASS |
| M3 repeated checks and the digest produced no additional sends | PASS |
| M4 founder desk records "Emailed to you: accepted by Resend" with simulated amount and due date | PASS |
| M5 inbox RECEIPT of both messages | INFO: awaiting founder confirmation |
| M6 sending switched off at the end; no deployed configuration changed | PASS |

Resend acceptance (M1) is not inbox receipt. Receipt (M5) is confirmed only by the founder.
Nothing merged or deployed; live email remains off.
