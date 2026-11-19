# Stripe test-mode evidence · 2026-11-18T11:00:24.300Z

Run runmwm0f4i8; phases e2e; connected test account acct_1UclJXHx1Olx8cdw.

PASS 8 · FAIL 0 · SKIP 0 · INFO 1 · INCONCLUSIVE 0

| id | check | source | result | observed |
|---|---|---|---|---|
| L1 | the adapter refuses a live key before any request | local | PASS | {} |
| L2 | a Stripe TEST key is configured | local | PASS | {} |
| E17a | which key the public checkout Worker is configured with | local | INFO | {"public_worker_key":"separate restricted TEST key (CHECKOUT_TEST_STRIPE_RUNTIME_KEY)","worker_env_has_runner_key":false} |
| E17b | the runtime key is refused artist account, identity and bank data (HTTP status only recorded) | stripe-test-api | PASS | {"v1_account":403,"v1_external_accounts":403,"v2_account_identity":403} |
| E17c | the runtime key cannot create PaymentIntents directly, refund, read balances or payouts, or create accounts (incomplete or invalid requests; status and Stripe error recorded) | stripe-test-api | PASS | {"create_payment_intent_on_artist_account":{"status":403,"denied":true,"stripe_error":{"type":"invalid_request_error","code":"more_permissions_required","message":"Permission denied. The provided key 'rk_test_...rDIv' does not have the required permissions for this endpoint on account 'acct_1UclJXHx |
| E1 | the pilot reads the onboarded test account from Stripe and marks it ready | stripe-test-api+pilot | PASS | {"ok":true,"membership":{"opted_in":true,"addendum":"PA-PAY-TEST-01","opted_in_at":"2026-11-18T11:00:09.713Z","processing_consent":false,"processing_consent_at":null,"account":{"id":"acct_1UclJXHx1Olx8cdw","country":"IE","charges_enabled":true,"payouts_enabled":true,"details_submitted":true,"require |
| E23a | while paused, an existing buyer link for an unpaid quote cannot open a Stripe Checkout Session: the buyer sees “payments are temporarily paused”, no session is created at Stripe, and the quote’s expiry is unchanged | stripe-test-api+pilot | PASS | {"pause_http":200,"buyer_http":409,"buyer_sees":"Payments are temporarily paused. Your quote stays valid until the expiry time shown above; you can pay once payments resume. Questions: hello@plotnua.ie.","stripe_session_creates":0,"absence_open_sessions":[{"reference":"PA-O-261118-B1DDQD","expires_a |
| E23 | a real Checkout Session opened BEFORE the pause, paid DURING it: Stripe’s signed checkout.session.completed is processed once, the charge is booked once, the work is sold, and the processing reimbursement proceeds (one application-fee refund) while the pause stays on | stripe-test-api+pilot | PASS | {"session_opened_before_pause":{"id":"cs_test_a0UMpxCBKJTXGJfZH99B49M7ruic2PwwsD6QBjrqoDMKiLtrCAbpWmfqkE","expires_at":"2026-11-18T11:31:10.591Z"},"pause_since":"2026-11-18T11:00:10.967Z","completion_events":[{"type":"checkout.session.completed","status":"processed","created":"2026-11-18T11:00:19.00 |
| E17d | pause run: every Stripe API call made by the public checkout Worker used the runtime key | stripe-test-api+pilot | PASS | {"calls":9,"list":["POST /v1/checkout/sessions [connected] → 200 (runtime)","GET /v1/payment_intents/pi_… [connected] → 200 (runtime)","GET /v1/payment_intents/pi_… [connected] → 200 (runtime)","GET /v1/charges/ch_… [connected] → 200 (runtime)","GET /v1/payment_intents/pi_… [connected] → 200 (runtim |
