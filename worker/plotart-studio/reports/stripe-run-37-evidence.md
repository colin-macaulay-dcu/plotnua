# Stripe test-mode evidence · 2026-11-18T11:42:05.327Z

Run runmwm1x3zf; phases founder_email; connected test account acct_1UclJXHx1Olx8cdw.

PASS 2 · FAIL 1 · SKIP 0 · INFO 0 · INCONCLUSIVE 0

| id | check | source | result | observed |
|---|---|---|---|---|
| L1 | the adapter refuses a live key before any request | local | PASS | {} |
| L2 | a Stripe TEST key is configured | local | PASS | {} |
| M0 | prerequisites: secret RESEND_API_KEY and variable CHECKOUT_TEST_FOUNDER_EMAIL in the checkout-test environment | local | FAIL | {"resend_key_present":false,"resend_key_format_ok":false,"recipient_present":false,"note":"nothing was sent"} |
