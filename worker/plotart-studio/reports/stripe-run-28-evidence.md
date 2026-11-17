# Stripe test-mode evidence · 2026-11-17T22:10:57.633Z

Run runmwl8x4th; phases unfunded; connected test account acct_1UclJXHx1Olx8cdw.

PASS 4 · FAIL 0 · SKIP 0 · INFO 3

| id | check | source | result | observed |
|---|---|---|---|---|
| L1 | the adapter refuses a live key before any request | local | PASS | {} |
| L2 | a Stripe TEST key is configured | local | PASS | {} |
| U3 | second account: pilot configuration and onboarding complete | stripe-test-api | PASS | {"account":"acct_1Uct3vHx1OnYJa8H","charges_enabled":true,"details_submitted":true,"currently_due":[],"problems":[]} |
| U4 | balance on the second account before the test | stripe-test-api | INFO | {"available":0,"pending":0} |
| U5 | after a €100 sale with €15 commission the account holds less than the sale amount | stripe-test-api | PASS | {"payment_intent":"pi_3UcuZyHx1OnYJa8H0npuCBrm","status":"succeeded","net_cents":8082,"balance_after_sale":{"available":0,"pending":8082}} |
| U6 | FULLY UNFUNDED refund: €100 refund when the account holds less than €100 in total (available + incoming) — what Stripe does | stripe-test-api | INFO | {"refund":"re_3UcuZyHx1OnYJa8H0m26qGlu","shortfall_cents":1918,"status_at_creation":"succeeded","statuses_seen":["succeeded"],"final_status":"succeeded","waited_s":31,"balance_before_refund":{"available":0,"pending":8082},"balance_after_refund":{"available":0,"pending":-1918}} |
| U7 | a further refund while the balance is already short or negative | stripe-test-api | INFO | {"refund":"re_3UcuaZHx1OnYJa8H0MalwIwm","balance_before_refund":{"available":0,"pending":-1918},"status_at_creation":"succeeded","final_status":"succeeded","balance_after_refund":{"available":0,"pending":-2326}} |
