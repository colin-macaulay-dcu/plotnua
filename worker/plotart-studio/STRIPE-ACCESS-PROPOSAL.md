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

## 3. Proposed versus verified

Nothing in §2.1 is verified yet. The test runner gives key A to the public checkout Worker only, once the secret `CHECKOUT_TEST_STRIPE_RUNTIME_KEY` exists.

| Restriction or capability | How it is verified | Status |
|---|---|---|
| Key A is used by the public Worker (and the Studio and harness keep the main key) | E17a records which key was used | proposed (not yet run) |
| Refused: v1 artist account, artist bank accounts, v2 account with identity | E17b: HTTP 401/403 required; status codes only recorded | proposed (not yet run) |
| Refused: creating a PaymentIntent directly, creating a refund, reading the artist's balance or payouts, creating an account | E17c: each request is deliberately invalid (zero amount, unknown object), so nothing can happen even if a permission were wrongly granted; 401/403 required | proposed (not yet run) |
| Everything the public Worker needs still works: Checkout creation, completion, expiry, reimbursement at payment, sweep refund polling, dispute fees | the existing e2e checks E2, E3, E6, E13, E14, E16 and E18, run with key A on the public side | proposed (not yet run) |
| Studio key B | not tested separately (the Studio keeps the current key in tests) | proposal only |
| Anything not listed above | not tested | not verified |

## 4. Steps for you (sandbox only)

Your current key is not changed by these steps. Do them one at a time.

1. In the Stripe Dashboard, open the **sandbox** you use for the pilot. Go to **Developers → API keys → Create restricted key**, and choose to build it yourself.
2. Name it **"PlotArt checkout runtime (test)"**.
3. Set each permission exactly as in the §2.1 table, both "In your account" and "In connected accounts". Leave everything else None.
4. Create the key and copy it. **Do not paste it into chat.**
5. In GitHub, go to **colin-macaulay-dcu/plotnua → Settings → Environments → checkout-test → Add secret**. Name it `CHECKOUT_TEST_STRIPE_RUNTIME_KEY` and paste the key as its value.
6. Tell me it is done. I will request a run, which waits for your approval as usual, and report E17a–c and the e2e results, keeping proposed and verified apart.

For live use, the same split would be created as separate live keys and stored as Cloudflare secrets of the two Workers, with your approval. That is not part of this pilot.
