# PlotArt multi-artist basket — production launch runbook (22 November 2026)

Branch `plotart/multi-artist-basket`. Nothing here has been run against production. Every step marked **founder** needs the
founder's action or approval; nothing merges, migrates production or takes a live payment before the final deployment approval.

## What is ready

- Code: basket (one direct charge per artwork, authorise all before capture), seller and returns information before payment
  (shown only after each artist confirms it, bound to the exact details), the Founding 25 processing-fee consent (0% PlotArt
  commission; artist bears Stripe's actual fees; separate, recorded, revocable), Studio screens for artists and the founder.
- Migrations: `0019_multi_artist_basket.sql`, `0020_basket_consents.sql` (new tables only; triggers ⇒ migration-check class
  "destructive": backup first). `0021_basket_terms_issue.sql` installs the issued texts.
- Texts: issued 21 Nov 2026 in `agreements/basket-issued/` (PA-BBT-2026-11, PA-BAA-2026-11); Privacy V18 in `atlas-tools/privacy_v18_layer.py`.
- Live safeguards: the production config refuses the basket unless live checkout is on, both texts are issued and bundled,
  0019–0021 are in the release, and a `pk_live_` key is set. Live enablement writes the basket key and platform webhook secret
  only when the basket is enabled, verifies them before the live deploy, and recovers to OFF on any failure.

## Route to launch (in order)

1. **Texts — DONE (21 Nov 2026).** Approved and issued: `agreements/basket-issued/` (PA-BBT-2026-11, PA-BAA-2026-11,
   fingerprints), bundled as LIVE_BASKET_DOCS; `migrations/0021_basket_terms_issue.sql` (SHA-256
   b791c838045508f08badebc59104ce99d717457cdd778948971eea3d12a68900). Privacy V18 (pilot + basket) prepared in
   `atlas-tools/privacy_v18_layer.py`; published at launch with `python3 atlas-tools/privacy_v18_layer.py --apply`.
2. **Founder, Stripe dashboard (live mode):**
   - Restricted key "PlotArt basket": write **Customers, Payment Methods, Checkout Sessions, PaymentIntents** (incl. on
     connected accounts). Store as GitHub secret `CHECKOUT_LIVE_STRIPE_BASKET_KEY` (environment `studio-production.`).
     The existing live keys are not changed.
   - Webhook endpoint on **your account**: `https://<checkout origin>/v1/stripe/webhook`, events
     `checkout.session.completed`, `checkout.session.expired`. Secret → `CHECKOUT_LIVE_STRIPE_PLATFORM_WEBHOOK_SECRET`.
   - Existing **connected accounts** endpoint: add `payment_intent.amount_capturable_updated`, `payment_intent.succeeded`,
     `payment_intent.payment_failed`, `payment_intent.canceled`, `payment_intent.requires_action`.
   - Variable `CHECKOUT_LIVE_PUBLISHABLE_KEY` = the live `pk_live_…`.
3. **Founder: final deployment approval**, then:
   - merge the branch to `main`;
   - production D1 backup, then migrations 0019, 0020, 0021 and 0022 (delivery safety; each through `migration-check.py` with its SHA-256);
   - publish privacy notice V18 (`privacy_v18_layer.py --apply`, then the site release);
   - run `plotart-checkout-deploy.yml` → production, `enable_live_pilot` + `enable_live_basket`, approve `studio-production.`.
4. **Artists (live, each themselves in Studio → Payment pilot page):** join the payment pilot (PA-PAY), complete Stripe live
   onboarding (charges **and payouts**), seller information, accept PA-BAA, confirm seller information may be shown,
   (Founding, optional) give the processing-fee consent. Those five steps set up the ACCOUNT. Then, per artwork (23 Nov 2026):
   a fixed delivery price with real transit insurance (bought online once the founder approves it), or delivery arranged
   personally (no online payment: buyers enquire, the artwork page says so; a managed-checkout quote can follow the enquiry).
   **Founder:** review each delivery offer on Review desk → Basket readiness → "Delivery offers to review"; nothing can be
   bought online until its exact current offer is approved (22 Nov 2026). The founder's
   "Basket readiness" table shows what each artist is missing. No synthetic or TEST artist exists in production.

## Genuinely open legal risks

See `agreements/basket-drafts/PA-BBT-PA-BAA-r2-REVIEW-NOTES.md` section C (order-button wording on Stripe's page; home
addresses of home-based artists; privacy V18 not yet published).
