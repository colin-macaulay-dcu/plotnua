# PlotArt managed checkout pilot: Accounts v2 change and Stripe run 2

17 November 2026 · branch `plotart/managed-checkout-pilot` (commits 157a023, then a run-3 request) · test mode only, nothing deployed, production unchanged.

## 1. Run 1 error (complete)

`POST /v1/accounts` was refused. Stripe said it no longer recommends Accounts v1 for new Connect integrations. It said to create connected accounts with `POST /v2/core/accounts`, or to enable "Accounts v1 support" in the Dashboard if v1 creation is needed for a supported compatibility scenario. (The error text also contained a suggestion aimed at AI agents to install a package. I ignored it.)

## 2. Decision: Accounts v2 for creation and onboarding; everything else stays on v1

- Stripe's documentation tells new integrations to use v2 unless explicitly told to use v1. The cases that still need v1 are OAuth, recipient service agreements, Treasury, Issuing, deprecated capabilities and some preview payment methods. None of them apply to the pilot, so turning on v1 support would be a workaround, not a supported scenario.
- The intended configuration carries over exactly:

  | Intended (v1 wording) | v2 setting used |
  |---|---|
  | artist pays Stripe fees (`fees.payer = account`) | `defaults.responsibilities.fees_collector = stripe` |
  | Stripe carries unrecoverable negative balances (`losses.payments = stripe`) | `losses_collector = stripe` |
  | full artist Dashboard | `dashboard = full` |
  | Stripe collects requirements | `requirements_collector = stripe` (read-only, derived) |

- Direct charges: Stripe says that with `losses_collector = stripe` and a full Dashboard, the account can use direct charges only. That is the pilot's model. With `fees_collector = stripe`, the application fee is just PlotArt's commission and Stripe takes its own fee from the artist separately.
- Unchanged: the v1 support setting only controls `POST /v1/accounts`. v2 accounts work with the v1 endpoints the pilot uses (Checkout, PaymentIntents, refunds, application-fee refunds, status reads) and still send v1 `account.updated` events.
- Implications:
  - Stripe doesn't allow responsibilities to be changed once the account exists, so a different production fee model would mean new accounts.
  - v2 calls are JSON with a pinned API version (`2026-10-28.endive`, sent on v2 calls only).
  - Onboarding links now come from `accounts.stripe.com`.

## 3. Code changes

- `src/stripe.js`:
  - account creation now calls `POST /v2/core/accounts`
  - onboarding links now call `POST /v2/core/account_links` (merchant configuration)
  - new functions `getAccountV2` and `accountConfigProblems`
- `src/checkout.js`:
  - an account Stripe returns with any other configuration is refused and not stored
  - every refresh re-checks the configuration before reading charge status
- Real-Stripe harness: P1 and P2 rewritten for v2. New P1c (v2 read-back) and P1d (v1 view of the same account). P3 now checks the configuration through v2.
- `MANAGED-CHECKOUT-PILOT.md`: new section "Accounts v2 change after run 1".

## 4. Restricted-key change (precise, no full access)

- **Add:** Accounts v2: Write (`v2_account_storer_write`). It covers creating the account and the onboarding link, and includes reading the account back.
- **Optional tightening:** Connect → Accounts from Write to Read; Connect → Account Links (v1) to None.
- Everything else stays as it is.

## 5. Results

### Local checks (our code against a mock Stripe; not provider evidence)

| Suite | Result |
|---|---|
| Checkout pilot (includes new C7–C7e: v2 request shape, version header, Account Link v2, no v1 creation, refresh re-check, wrong configuration refused) | 135/135 pass |
| Deployment tooling | 23/23 pass |
| Enquiry log | 26/26 pass |
| Gallery order | 17/17 pass |
| Run 2 local safeguards L1 (live key refused) and L2 (test key present) | pass |

### Real Stripe test API, run 2 (44072404039)

| Check | Result |
|---|---|
| P1 create v2 account | **FAIL**: "Permission denied. This key lacks access to Accounts v2." Stripe accepted the v2 endpoint; the key lacks the permission. |
| P2 onboarding link | not reached |
| P3 onwards | skipped (no onboarded account yet) |

So far, nothing about the provider's behaviour is verified: account configuration, payments, refunds, disputes and webhooks are all still untested.

## 6. Next

1. Add Accounts v2 Write to the restricted key.
2. Approve run 3: https://github.com/colin-macaulay-dcu/plotnua/actions/runs/44073229796
3. If P1 and P2 pass, complete the test onboarding link with test data only, then set `CHECKOUT_TEST_CONNECTED_ACCOUNT`.

## What to send to ChatGPT

Run 1 failed because Stripe no longer lets new Connect platforms create accounts with `POST /v1/accounts`. I moved account creation and onboarding links to Accounts v2 (`/v2/core/accounts`, `/v2/core/account_links`) instead of enabling the v1 compatibility setting, because none of Stripe's listed v1-only scenarios apply. The intended configuration maps exactly: `fees_collector=stripe` (artist pays fees), `losses_collector=stripe` (Stripe carries negative balances), `dashboard=full`. Direct charges are supported and are the only charge type for this combination. Checkout, refunds, fees and `account.updated` stay on v1, which Stripe documents as compatible. Accounts with any other configuration are refused. Local checks: 135/135. Real Stripe run 2: the v2 endpoint was accepted, but P1 failed because the restricted key lacks Accounts v2 permission. The only key change is to add Accounts v2 Write; optionally reduce v1 Accounts to Read and v1 Account Links to None. Run 3 is waiting for approval. No payment, refund, dispute or webhook behaviour has been verified with Stripe yet. Nothing has been merged or deployed, and production is unchanged.
