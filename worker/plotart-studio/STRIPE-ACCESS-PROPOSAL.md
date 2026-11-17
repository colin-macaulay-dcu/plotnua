# PlotArt payment pilot: narrower Stripe access (proposal, 17 November 2026)

**Status: proposal. Nothing has been changed.** Today a single restricted TEST key (`CHECKOUT_TEST_STRIPE_SECRET_KEY`) is used by both pilot Workers and by the test runner. Run 20's access check showed that this key can read artist identity details (date of birth, address, identity-number fields) and bank branch details, which the public checkout never needs.

Permission names are Stripe's restricted-key permissions, from https://docs.stripe.com/keys/permissions-reference. Permissions marked "(Direct)" cannot be used with the `Stripe-Account` header; application fees are platform objects, so the pilot calls them directly anyway.

## 1. What each part of the pilot actually calls

| Caller | Calls (from `src/stripe.js` and its callers) | Permission needed |
|---|---|---|
| **Public checkout Worker** (internet-facing: buyer pages, webhooks, 15-minute sweep, processing reimbursement at payment) | create, read and expire Checkout Sessions (on the artist's account) | `checkout_session_write` |
| | read PaymentIntent | `payment_intent_read` |
| | read Charge with its balance transaction (Model B fee lines) | `charge_read` (plus `balance_read` **if** Stripe refuses the expansion without it; run 22 will show) |
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

| Key | Used by | Permissions | Effect |
|---|---|---|---|
| **A. Runtime key** (new) | the public checkout Worker only | Checkout Sessions: **Write**; PaymentIntents: **Read**; Charges (and refunds): **Read**; Application fees: **Write**; Disputes: **Read**; everything else **None** (no Accounts v1 or v2, no Balance unless run 22 shows it is needed) | The internet-facing Worker can no longer read any artist identity or bank detail. If its key leaked, it could not create payments, pay out, or read artist accounts. |
| **B. Studio key** | the Studio Worker | today's runtime permissions **minus** the test-runner extras | Founder-only (Cloudflare Access). Still needs account reads for onboarding status; those can also expose identity details, because Stripe's account read permissions offer nothing narrower. |
| **C. Test-runner key** | GitHub Actions only | today's key, unchanged | Never deployed to any Worker. |

**Not possible today.** Onboarding-status reads cannot be narrowed further. `v2_account_read` returns identity details when they are requested, and `connected_account_read` returns individual and bank summaries. Stripe's permission list has nothing finer for these endpoints. What the pilot can do is never request or store them: it already does not request `identity`.

**Optional later narrowing (code change, not made).** The Studio could take charge and payout status from Accounts v2 alone and drop `connected_account_read`. That needs the v2 merchant status fields confirmed in the sandbox first.

## 3. Verification

The test runner already supports key A. When the secret `CHECKOUT_TEST_STRIPE_RUNTIME_KEY` exists, the end-to-end test gives it to the public checkout Worker only, and adds:
- **E17a:** records which key that Worker used;
- **E17b:** checks that the runtime key is refused the artist's v1 account, its bank accounts, and the v2 account with identity. Only the HTTP status codes are recorded.

Every existing end-to-end check then runs with key A on the public side:
- E2/E3: hosted Checkout and the completion;
- E13: the reimbursement at payment;
- E14/E16: dispute fees;
- E6: expiry;
- the sweep's reimbursement and refund polling.

If any of these fails with a permission error, the report names the missing permission. Key B is not tested separately: the Studio side keeps the current key in the test run.

## 4. Steps for you (sandbox only)

Your current key is not changed by these steps. Do them one at a time.

1. In the Stripe Dashboard, open the **sandbox** you use for the pilot. Go to **Developers → API keys → Create restricted key**, and choose to build it yourself.
2. Name it **"PlotArt checkout runtime (test)"**.
3. Set **Checkout Sessions = Write**, **PaymentIntents = Read**, **Charges = Read**, **Application Fees = Write**, **Disputes = Read**. Leave every other resource **None**; in particular, Accounts, Accounts v2, Balance, Customers and Payouts.
4. If the form shows a separate **Connect** column, allow the same permissions for connected accounts. The pilot creates Checkout Sessions on the artist's account.
5. Create the key and copy it. **Do not paste it into chat.**
6. In GitHub, go to **colin-macaulay-dcu/plotnua → Settings → Environments → checkout-test → Add secret**. Name it `CHECKOUT_TEST_STRIPE_RUNTIME_KEY` and paste the key as its value.
7. Tell me it is done. I will then request a run, which waits for your approval as usual, and report E17 and the e2e results.

For live use, the same split would be created as separate live keys and stored as Cloudflare secrets of the two Workers, with your approval. That is not part of this pilot.
