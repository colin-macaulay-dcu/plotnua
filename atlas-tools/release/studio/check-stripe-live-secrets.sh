#!/usr/bin/env bash
# PlotArt · managed checkout pilot · LIVE credentials check (20 Nov 2026). Refuses anything but Stripe LIVE credentials, and
# refuses the TEST values, before they are written to a production Worker. Reads the values from the environment and prints
# only PASS/FAIL (never a value). Used only by the production live-enablement path of plotart-checkout-deploy.yml.
set -uo pipefail
bad=0
# Values pasted into GitHub can carry a trailing newline or spaces: trim them (never printed) before checking and using.
_trim() { local s="$1"; s="${s#"${s%%[![:space:]]*}"}"; s="${s%"${s##*[![:space:]]}"}"; printf '%s' "$s"; }
for _v in LIVE_STUDIO_KEY LIVE_RUNTIME_KEY LIVE_WEBHOOK_SECRET LIVE_RESEND_KEY LIVE_BASKET_KEY LIVE_PLATFORM_WEBHOOK_SECRET; do
  [ -n "${!_v:-}" ] && printf -v "$_v" '%s' "$(_trim "${!_v}")"
done
# why a Stripe key was refused, by its kind only (a key's prefix is not secret; nothing else of it is printed)
_why() { case "$1" in "") echo "is missing (empty)";; sk_test_*|rk_test_*) echo "is a TEST key";; pk_*) echo "is a publishable key, not a secret or restricted key";;
  whsec_*) echo "is a webhook signing secret, not an API key";; sk_live_*|rk_live_*) echo "starts correctly but contains characters other than letters and digits (for example quotes or a space)";;
  *) echo "does not start with sk_live_ or rk_live_";; esac; }
for v in LIVE_STUDIO_KEY LIVE_RUNTIME_KEY; do
  [[ "${!v:-}" =~ ^(sk|rk)_live_[A-Za-z0-9]+$ ]] && echo "  PASS  $v is a Stripe LIVE key" || { echo "  FAIL  $v is not a Stripe LIVE key (sk_live_/rk_live_): it $(_why "${!v:-}")"; bad=1; }
done
[[ "${LIVE_WEBHOOK_SECRET:-}" =~ ^whsec_[A-Za-z0-9]+$ ]] && echo "  PASS  live webhook signing secret present" || { echo "  FAIL  live webhook signing secret missing or malformed"; bad=1; }
[[ "${LIVE_RESEND_KEY:-}" =~ ^re_[A-Za-z0-9_]+$ ]] && echo "  PASS  email key present" || { echo "  FAIL  email key (Resend) missing or malformed"; bad=1; }
# multi-artist basket (22 Nov 2026): its own LIVE restricted key (Customers, PaymentMethods, Checkout Sessions, PaymentIntents
# write) and the PlotArt-account webhook secret, checked only when the basket is being enabled
if [ "${ENABLE_LIVE_BASKET:-false}" = true ]; then
  [[ "${LIVE_BASKET_KEY:-}" =~ ^(sk|rk)_live_[A-Za-z0-9]+$ ]] && echo "  PASS  basket key is a Stripe LIVE key" || { echo "  FAIL  LIVE_BASKET_KEY is not a Stripe LIVE key: it $(_why "${LIVE_BASKET_KEY:-}")"; bad=1; }
  [[ "${LIVE_PLATFORM_WEBHOOK_SECRET:-}" =~ ^whsec_[A-Za-z0-9]+$ ]] && echo "  PASS  basket (PlotArt-account) webhook secret present" || { echo "  FAIL  basket webhook secret missing or malformed"; bad=1; }
  if [ -n "${TEST_STRIPE_KEY:-}" ] && [ "${LIVE_BASKET_KEY:-}" = "${TEST_STRIPE_KEY:-}" ]; then echo "  FAIL  LIVE_BASKET_KEY equals a TEST credential"; bad=1; fi
fi
# the live values must never be the TEST values (a test credential can never reach production)
for pair in "LIVE_RUNTIME_KEY:TEST_STRIPE_KEY" "LIVE_STUDIO_KEY:TEST_STRIPE_KEY" "LIVE_WEBHOOK_SECRET:TEST_WEBHOOK_SECRET"; do
  a="${pair%%:*}"; b="${pair##*:}"
  if [ -n "${!b:-}" ] && [ "${!a:-}" = "${!b:-}" ]; then echo "  FAIL  $a equals a TEST credential"; bad=1; fi
done
exit $bad
