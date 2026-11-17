# Stripe test-mode evidence · 2026-11-17T23:07:19.059Z

Run runmwlaxvvg; phases e2e, unfunded_ledger; connected test account acct_1UclJXHx1Olx8cdw.

PASS 5 · FAIL 7 · SKIP 8 · INFO 2

| id | check | source | result | observed |
|---|---|---|---|---|
| L1 | the adapter refuses a live key before any request | local | PASS | {} |
| L2 | a Stripe TEST key is configured | local | PASS | {} |
| U8 | second account: balance transactions in order, with running net (reconciles the U5–U7 balances) | stripe-test-api | INFO | {"http":200,"transactions":[{"id":"txn_3UcuZyHx1OnYJa8H0AIuOziB","type":"charge","reporting_category":"charge","amount":10000,"fee":1918,"net":8082,"status":"pending","created":"2026-11-17T22:10:18.000Z","available_on":"2026-11-24","source_prefix":"ch_","running_net":8082},{"id":"txn_3UcuZyHx1OnYJa8 |
| E17a | which key the public checkout Worker is configured with | local | INFO | {"public_worker_key":"separate restricted TEST key (CHECKOUT_TEST_STRIPE_RUNTIME_KEY)","worker_env_has_runner_key":false} |
| E17b | the runtime key is refused artist account, identity and bank data (HTTP status only recorded) | stripe-test-api | PASS | {"v1_account":403,"v1_external_accounts":403,"v2_account_identity":403} |
| E17c | the runtime key cannot create PaymentIntents directly, refund, read balances or payouts, or create accounts (deliberately invalid requests; HTTP status only) | stripe-test-api | FAIL | {"create_payment_intent_on_artist_account":403,"create_refund_on_artist_account":404,"read_artist_balance":403,"list_artist_payouts":403,"create_v2_account":415} |
| E1 | the pilot reads the onboarded test account from Stripe and marks it ready | stripe-test-api+pilot | PASS | {"ok":true,"membership":{"opted_in":true,"addendum":"PA-PAY-TEST-01","opted_in_at":"2026-11-17T23:06:56.682Z","processing_consent":false,"processing_consent_at":null,"account":{"id":"acct_1UclJXHx1Olx8cdw","country":"IE","charges_enabled":true,"payouts_enabled":true,"details_submitted":true,"require |
| E2 | the pilot opens real hosted checkout on the artist’s account for the approved quote | stripe-test-api+pilot | FAIL | {"status":502,"host":null} |
| E3a | buyer pays on the real hosted Stripe Checkout page (headless browser) | stripe-test-api+pilot | FAIL | {"error":"page.goto: url: expected string, got object","final_url":"nullblank","steps":["23:06:58 ERROR page.goto: url: expected string, got object"],"page_errors":[],"http_errors":[]} |
| E3 | a REAL signed checkout.session.completed marks the order paid (and the work sold) | stripe-test-api+pilot | SKIP | {"blocked_by":"E3a — no payment was made, so no completion event could arrive; webhook handling NOT exercised","payment_status":null,"events":[]} |
| E3c | the completion event is for this order’s own Checkout Session (matching client_reference_id, paid on Stripe) and was applied to no other order | stripe-test-api+pilot | SKIP | {"events":[],"stray":[]} |
| E6 | a REAL checkout.session.expired event releases the reservation and returns the quote to payable | stripe-test-api+pilot | PASS | {"status":"quoted"} |
| E7a | buyer pays with the dispute test card on the real hosted Checkout page | stripe-test-api+pilot | FAIL | {"error":"page.goto: url: expected string, got object","final_url":"nullblank","steps":["23:07:18 ERROR page.goto: url: expected string, got object"],"page_errors":[]} |
| E7 | a REAL charge.dispute.created (arriving after or before the payment event) marks the order disputed | stripe-test-api+pilot | SKIP | {"blocked_by":"E7a — no payment was made, so no dispute could open; webhook handling NOT exercised","status":"quoted","dispute_status":"none","events":[]} |
| E7c | the dispute event was applied to the order whose PaymentIntent Stripe disputed, and to no other order | stripe-test-api+pilot | SKIP | {"events":[],"payment_intent_matches":false,"other_orders":[]} |
| E10 | dispute closed as won through the pilot | stripe-test-api+pilot | SKIP | {"blocked_by":"E7 — no open dispute"} |
| E11a | buyer pays with the dispute test card (lost case) | stripe-test-api+pilot | FAIL | {"error":"page.goto: url: expected string, got object"} |
| E11 | dispute closed as lost through the pilot | stripe-test-api+pilot | SKIP | {"blocked_by":"E11a"} |
| E12a | buyer pays with the refund-fails test card | stripe-test-api+pilot | FAIL | {"error":"page.goto: url: expected string, got object"} |
| E12b | refund reversal reconciliation | stripe-test-api+pilot | SKIP | {"blocked_by":"E12a — payment not completed"} |
| E17d | every Stripe API call made by the public checkout Worker used the runtime key (no fallback to the runner key); endpoints and statuses listed; permission errors shown with Stripe’s message | stripe-test-api+pilot | FAIL | {"calls":0,"by_key":{},"endpoints":[],"permission_errors":[]} |
| E8 | every expected real signed event (payment completed, session expired, dispute created, dispute closed) arrived and processed, and none failed | stripe-test-api+pilot | SKIP | {"failed":[],"missing_expected":["checkout.session.completed","checkout.session.expired","charge.dispute.created","charge.dispute.closed"],"received":[],"note":"not a success: expected events never arrived"} |
