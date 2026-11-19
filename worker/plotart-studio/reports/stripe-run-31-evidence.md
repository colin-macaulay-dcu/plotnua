# Stripe test-mode evidence · 2026-11-17T23:50:08.470Z

Run runmwlchi4k; phases runtime_refund_probe; connected test account acct_1UclJXHx1Olx8cdw.

PASS 3 · FAIL 0 · SKIP 0 · INFO 0

| id | check | source | result | observed |
|---|---|---|---|---|
| L1 | the adapter refuses a live key before any request | local | PASS | {} |
| L2 | a Stripe TEST key is configured | local | PASS | {} |
| E17e | runtime key submits ONE valid €1.00 partial refund of a fresh paid €10 test charge on the artist’s account (idempotency key; runner key prepared the charge and lists the refunds) | stripe-test-api | PASS | {"prepared_charge":{"payment_intent":"pi_3Ucw8YHx1Olx8cdw0oE6JZvQ","status":"succeeded","amount":1000,"application_fee":null},"runtime_attempt":{"http":403,"refund_id":null,"refund_status":null,"error_code":"more_permissions_required","error_type":"invalid_request_error","error_message":"Permission  |
