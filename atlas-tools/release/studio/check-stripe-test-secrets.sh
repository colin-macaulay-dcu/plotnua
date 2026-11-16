#!/usr/bin/env bash
# PlotArt · managed checkout pilot · refuses anything but Stripe TEST credentials before they are written to a Worker.
# Reads STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET from the environment and prints only PASS/FAIL (never a value).
set -uo pipefail
bad=0
[[ "${STRIPE_SECRET_KEY:-}" =~ ^(sk|rk)_test_[A-Za-z0-9]+$ ]] && echo "  PASS  Stripe key is a TEST key" || { echo "  FAIL  Stripe key missing or not a TEST key (sk_test_/rk_test_)"; bad=1; }
[[ "${STRIPE_WEBHOOK_SECRET:-}" =~ ^whsec_[A-Za-z0-9]+$ ]] && echo "  PASS  webhook signing secret present" || { echo "  FAIL  webhook signing secret missing or malformed"; bad=1; }
exit $bad
