# PlotArt payment pilot: narrower Stripe access (proposal, 17 November 2026)

**Status: proposal. Nothing has been changed.** Today a single restricted TEST key (`CHECKOUT_TEST_STRIPE_SECRET_KEY`) is used by both pilot Workers and by the test runner. Run 20's access check showed that this key can read artist identity details (date of birth, address, identity-number fields) and bank branch details, which the public checkout never needs.

Permission names are Stripe's restricted-key permissions, from https://docs.stripe.com/keys/permissions-reference. Permissions marked "(Direct)" cannot be used with the `Stripe-Account` header; application fees are platform objects, so the pilot calls them directly anyway.

## 1. What each part of the pilot actually calls

| Caller | Calls (from `src/stripe.js` and its callers) | Permission needed |
|---|---|---|
| **Public checkout Worker** (internet-facing: buyer pages, webhooks, 15-minute sweep, processing reimbursement at payment) | create, read and expire Checkout Sessions (on the artist's account) | `checkout_session_write` |
| | read PaymentIntent | `payment_intent_read` |
| | read Charge with its balance transaction (Model B fee lines) | `charge_read` (plus `balance_read` **if** Stripe refuses the expansion without it; the verification run will show) |
| | read Refund (sweep) | `charge_read` |
| | partial application-fee refund (reimbursement) | `application_fee_write` (Direct) |
| | read Dispute (fee lines) | `dispute_read` |
| | **artist accounts (v1 or v2)** | **none**: `account.updated` is handled from the signed event itself |
| **Studio Worker** (behind Cloudflare Access: onboarding, founder actions) | create Accounts v2 account and Account Link | `v2_account_storer_write` (Dashboard: the Accounts v2 write and merchant configuration permissions already granted) |
| | read Accounts v2 (configuration, requirements) and the v1 account (charge and payout status) | `v2_account_read`, `connected_account_read` (Direct) |
| | refunds | `charge_write` |
| | commission refunds, lost-dispute commission | `application_fee_write` |
| | expire Checkout Sessions when a quote is revised or cancelled; read PaymentIntents and Disputes | `checkout_session_write`, `payment_intent_read`, `dispute_read` |
| **Test runner** (GitHub Actions only) | everything above, plus: test payments, submitting dispute evidence, balance reads, listing fee refunds, and the privacy probe | additionally `payment_intent_write`, `dispute_write`, `balance_read`, `application_fee_read` (and read access to connected accounts for the probe) |

## 2. Proposal

| Key | Used by | Effect |
|---|---|---|
| **A. Runtime key** (new; exact permissions in §2.1) | the public checkout Worker only | The internet-facing Worker cannot read artist accounts, identity or bank details. It **can** create Checkout Sessions on artist accounts, so it can start payment flows that buyers complete. |
| **B. Studio key** | the Studio Worker | Today's runtime permissions minus the test-runner extras. Founder-only (Cloudflare Access). Still needs account reads for onboarding status, and these can expose identity details: Stripe offers no narrower permission for those endpoints. |
| **C. Test-runner key** | GitHub Actions only | Today's key, unchanged. Never deployed to any Worker. |

### 2.1 Key A: exact permissions (proposed)

Set each permission separately. "In your account" means the platform account (PlotNua). "In connected accounts" means calls made on an artist's account with the `Stripe-Account` header.

| Resource (Dashboard) | In your account | In connected accounts | What the Worker uses it for |
|---|---|---|---|
| Checkout Sessions | None | **Write** | Create, read and expire the buyer's Checkout Session on the artist's account (`checkout_session_write`) |
| PaymentIntents | None | **Read** | Read the payment after the signed completion (`payment_intent_read`) |
| Charges (includes refunds) | None | **Read** | Read the charge and its balance transaction (Model B fee lines); read refund status in the sweep (`charge_read`) |
| Disputes | None | **Read** | Read a dispute's fee lines (`dispute_read`) |
| Application Fees | **Write** | None | Partial application-fee refund for the processing reimbursement. Application fees are platform objects; Stripe marks this permission "(Direct)" (`application_fee_write`) |
| Balance | None | None | Not needed. **Fallback:** if the verification run shows that reading the charge's balance transaction is refused, set "In connected accounts" to Read, and nothing else |
| All other resources, including Accounts, Accounts v2, Account Links, Payouts, Transfers, Customers, Payment Methods, Webhook Endpoints | None | None | — |

What key A **can** do: create Checkout Sessions on artist accounts (start payments that a buyer completes on Stripe's page); read those payments, charges, refunds and disputes; and refund part of PlotArt's own application fees.

What key A **cannot** do (proposed): create PaymentIntents or charges directly, create refunds to buyers, read balances or payouts, create or read artist accounts, or read identity or bank details.

**Not possible today.** Onboarding-status reads (key B) cannot be narrowed further. `v2_account_read` returns identity details when they are requested, and `connected_account_read` returns individual and bank summaries; Stripe's permission list has nothing finer for these endpoints. The pilot never requests or stores those details.

**Optional later narrowing (code change, not made).** The Studio could take charge and payout status from Accounts v2 alone and drop `connected_account_read`. That needs the v2 merchant status fields confirmed in the sandbox first.

## 3. Proposed versus verified (what the next run checks)

Nothing in §2.1 is verified yet. The next run gives key A to the public checkout Worker only; the Studio Worker and the harness keep the existing key.

| Permission or restriction | Checked by | What counts as verified |
|---|---|---|
| Key A is the one the public Worker uses | **E17a** | Records "separate restricted TEST key" |
| Accounts / Accounts v2 = None (identity and bank data refused) | **E17b** | v1 account, v1 bank accounts and v2 account with identity all return 401/403 |
| No direct PaymentIntents, refunds, balance, payouts or account creation | **E17c** | Deliberately invalid requests all return 401/403 |
| Checkout Sessions: Write, in connected accounts | **E2, E3** | The public Worker opens real hosted Checkout and the payment completes |
| PaymentIntents: Read, in connected accounts | **E3, E13** | The completion is recorded; the charge is found from the PaymentIntent |
| Charges: Read, in connected accounts | **E13** | The public Worker reads the balance transaction and records the actual fee and VAT. If this fails with a permission error, Balance: Read (connected accounts) is the named fallback |
| Application Fees: Write, in your account | **E13, E13b** | The reimbursement is made by the public Worker at payment, once |
| Disputes: Read, in connected accounts | E14 and E16 **only partly** | The public Worker reads a dispute through the API only if Stripe's event lacks the fee lines; usually it does not need to. **Not verified** unless the run shows the API path was used |
| Sweep refund polling (Charges: Read) | E5 | **Not verified** if the refund completes by webhook before the sweep polls |
| Expiring a session from the public Worker (Checkout Sessions: Write) | — | **Not verified**: E6 expires the session with the harness key |
| Studio key B | — | Not tested (the Studio keeps the existing key) |

## 4. Steps for you (sandbox only)

Your current key is not changed by these steps. Do them one at a time.

1. In the Stripe Dashboard, open the **sandbox** you use for the pilot. Go to **Developers → API keys → Create restricted key**, and choose to build it yourself.
2. Name it **"PlotArt checkout runtime (test)"**.
3. Set each permission exactly as in the §2.1 table, both "In your account" and "In connected accounts". Leave everything else None.
4. Create the key and copy it. **Do not paste it into chat.**
5. In GitHub, go to **colin-macaulay-dcu/plotnua → Settings → Environments → checkout-test → Add secret**. Name it `CHECKOUT_TEST_STRIPE_RUNTIME_KEY` and paste the key as its value.
6. Tell me it is saved. I will queue the run (phases `e2e` and `unfunded_ledger`), send you the approval link, and report each check, including any skipped.

For live use, the same split would be created as separate live keys and stored as Cloudflare secrets of the two Workers, with your approval. That is not part of this pilot.


## 5. Results: run 30 (17 Nov 2026, sandbox, Actions 44196705014)

**Run 29** did not exercise the key's checkout permissions. A bug in the harness's call observer stopped checkout with a 502 before any request reached Stripe; it was fixed for run 30. Run 29 still confirmed E17b (403 ×3).

| Check | Result | Evidence |
|---|---|---|
| E17a: key in the public Worker | **Verified** | Separate restricted TEST key; the runner key is absent from the Worker's settings |
| E17d: no fallback to the runner key | **Verified** | All 30 Stripe calls from the public Worker carried the runtime key; 0 permission errors |
| Checkout Sessions: Write, connected | **Verified** | `POST /v1/checkout/sessions` [connected] 200 ×5; E2/E3 PASS |
| PaymentIntents: Read, connected | **Verified** | `GET /v1/payment_intents/…` [connected] 200 ×13 |
| Charges: Read, connected (incl. balance transaction) | **Verified** | `GET /v1/charges/…` [connected] 200 ×4; E13 read the actual €34.11 + €7.85. **Balance: Read is not needed.** |
| Refund status reads (Charges: Read, connected) | **Verified** | `GET /v1/refunds/…` [connected] 200 ×4 |
| Application Fees: Write, platform | **Verified** | `POST /v1/application_fees/…/refunds` [platform] 200 ×4; E13/E13b reimbursed €41.96 once |
| Disputes: Read, connected | **Not exercised** | No dispute read was needed: Stripe's events carried the fee lines. Dispute fees were still recorded (E14, E16) |
| Expire a session from the public Worker | **Not exercised** | — |
| Refused: v1 account, bank accounts, v2 identity | **Verified** | 403 ×3 (E17b) |
| Refused: create PaymentIntent | **Verified** | 403 `more_permissions_required` ("Enabling Payment Intents Write…") |
| Refused: read balance | **Verified** | 403 `more_permissions_required` ("Enabling Balance Read…") |
| Refused: list payouts | **Verified** | 403 `more_permissions_required` ("Enabling Payouts Read…") |
| Refused: create v2 account | **Verified** | 403 forbidden ("This key lacks access to Accounts v2") |
| **Refused: create refund** | **NOT verified: E17c FAIL** | `POST /v1/refunds` [connected] with no parameters → **400** `invalid_request_error` "One of the following params should be provided for this request: payment_intent or charge." The other endpoints returned 403 before validating their (equally invalid) parameters. This suggests the key **is permitted** to create refunds on connected accounts, but it does not prove it. **Next step (founder):** check the key's Refunds or Charges setting under "In connected accounts". No change has been made. |
| Studio key B | Not tested | — |
