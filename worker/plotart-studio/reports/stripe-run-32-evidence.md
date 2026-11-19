# Stripe test-mode evidence · 2026-11-18T00:34:58.096Z

Run runmwlcyrh9; phases e2e; connected test account acct_1UclJXHx1Olx8cdw.

PASS 7 · FAIL 1 · SKIP 0 · INFO 1

| id | check | source | result | observed |
|---|---|---|---|---|
| L1 | the adapter refuses a live key before any request | local | PASS | {} |
| L2 | a Stripe TEST key is configured | local | PASS | {} |
| E17a | which key the public checkout Worker is configured with | local | INFO | {"public_worker_key":"separate restricted TEST key (CHECKOUT_TEST_STRIPE_RUNTIME_KEY)","worker_env_has_runner_key":false} |
| E17b | the runtime key is refused artist account, identity and bank data (HTTP status only recorded) | stripe-test-api | PASS | {"v1_account":403,"v1_external_accounts":403,"v2_account_identity":403} |
| E17c | the runtime key cannot create PaymentIntents directly, refund, read balances or payouts, or create accounts (incomplete or invalid requests; status and Stripe error recorded) | stripe-test-api | FAIL | {"create_payment_intent_on_artist_account":{"status":403,"denied":true,"stripe_error":{"type":"invalid_request_error","code":"more_permissions_required","message":"Permission denied. The provided key 'rk_test_...rDIv' does not have the required permissions for this endpoint on account 'acct_1UclJXHx |
| E1 | the pilot reads the onboarded test account from Stripe and marks it ready | stripe-test-api+pilot | PASS | {"ok":true,"membership":{"opted_in":true,"addendum":"PA-PAY-TEST-01","opted_in_at":"2026-11-18T00:03:34.073Z","processing_consent":false,"processing_consent_at":null,"account":{"id":"acct_1UclJXHx1Olx8cdw","country":"IE","charges_enabled":true,"payouts_enabled":true,"details_submitted":true,"require |
| E20 | dispute-fee fallback: an event WITHOUT fee lines (simulated input, signed locally) makes the Worker read the REAL dispute from Stripe with the runtime key; fees recorded from Stripe’s response | stripe-test-api+pilot | PASS | {"simulated":"event envelope signed locally with the run’s webhook secret; data.object = the real dispute object fetched from Stripe with balance_transactions REMOVED","from_stripe":"the Worker’s GET of the dispute (status and key below) and the fee lines it booked","webhook_http":200,"webhook_respo |
| E19 | normal expiry path: Stripe expires the open session at its expires_at; the signed checkout.session.expired event reaches the Worker, which releases the reservation and returns the quote to payable | stripe-test-api+pilot | PASS | {"session_expires_at":"2026-11-18T00:34:34.868Z","reservation_at_open":{"expires_at":"2026-11-18T00:49:34.868Z"},"stripe_session_status":"expired","worker_released":true,"expired_event":[{"type":"checkout.session.expired","status":"processed"}],"worker_checkout_session_calls":["POST /v1/checkout/ses |
| E17d | coverage run: every Stripe API call made by the public checkout Worker used the runtime key | stripe-test-api+pilot | PASS | {"calls":7,"by_key":{"runtime":7},"list":["POST /v1/checkout/sessions [connected] → 200","POST /v1/checkout/sessions [connected] → 200","GET /v1/payment_intents/pi_… [connected] → 200","GET /v1/payment_intents/pi_… [connected] → 200","GET /v1/payment_intents/pi_… [connected] → 200","GET /v1/disputes |
