#!/usr/bin/env bash
# PlotArt · managed checkout pilot · LIVE credentials check (20 Nov 2026). Refuses anything but Stripe LIVE credentials, and
# refuses the TEST values, before they are written to a production Worker. Reads the values from the environment and prints
# only PASS/FAIL (never a value). Used only by the production live-enablement path of plotart-checkout-deploy.yml.
set -uo pipefail
bad=0
for v in LIVE_STUDIO_KEY LIVE_RUNTIME_KEY; do
  [[ "${!v:-}" =~ ^(sk|rk)_live_[A-Za-z0-9]+$ ]] && echo "  PASS  $v is a Stripe LIVE key" || { echo "  FAIL  $v missing or not a Stripe LIVE key (sk_live_/rk_live_)"; bad=1; }
done
[[ "${LIVE_WEBHOOK_SECRET:-}" =~ ^whsec_[A-Za-z0-9]+$ ]] && echo "  PASS  live webhook signing secret present" || { echo "  FAIL  live webhook signing secret missing or malformed"; bad=1; }
[[ "${LIVE_RESEND_KEY:-}" =~ ^re_[A-Za-z0-9_]+$ ]] && echo "  PASS  email key present" || { echo "  FAIL  email key (Resend) missing or malformed"; bad=1; }
# multi-artist basket (22 Nov 2026): its own LIVE restricted key (Customers, PaymentMethods, Checkout Sessions, PaymentIntents
# write) and the PlotArt-account webhook secret, checked only when the basket is being enabled
if [ "${ENABLE_LIVE_BASKET:-false}" = true ]; then
  [[ "${LIVE_BASKET_KEY:-}" =~ ^(sk|rk)_live_[A-Za-z0-9]+$ ]] && echo "  PASS  basket key is a Stripe LIVE key" || { echo "  FAIL  LIVE_BASKET_KEY missing or not a Stripe LIVE key"; bad=1; }
  [[ "${LIVE_PLATFORM_WEBHOOK_SECRET:-}" =~ ^whsec_[A-Za-z0-9]+$ ]] && echo "  PASS  basket (PlotArt-account) webhook secret present" || { echo "  FAIL  basket webhook secret missing or malformed"; bad=1; }
  if [ -n "${TEST_STRIPE_KEY:-}" ] && [ "${LIVE_BASKET_KEY:-}" = "${TEST_STRIPE_KEY:-}" ]; then echo "  FAIL  LIVE_BASKET_KEY equals a TEST credential"; bad=1; fi
fi
# the live values must never be the TEST values (a test credential can never reach production)
for pair in "LIVE_RUNTIME_KEY:TEST_STRIPE_KEY" "LIVE_STUDIO_KEY:TEST_STRIPE_KEY" "LIVE_WEBHOOK_SECRET:TEST_WEBHOOK_SECRET"; do
  a="${pair%%:*}"; b="${pair##*:}"
  if [ -n "${!b:-}" ] && [ "${!a:-}" = "${!b:-}" ]; then echo "  FAIL  $a equals a TEST credential"; bad=1; fi
done
exit $bad
