#!/usr/bin/env bash
# PlotArt · managed checkout · switch live checkout OFF and VERIFY it (20 Nov 2026, PR #38 review 2).
#   bash checkout-live-off.sh <worker dir> <OFF wrangler config file, relative to the worker dir>
# Used by the production OFF path of plotart-checkout-deploy.yml (every production run without enable_live_pilot) and by
# the recovery of checkout-live-enable.sh. Needs ORIGIN (the production checkout origin) and Cloudflare credentials.
#   1 deploy plotart-checkout with the given OFF configuration (pilot off; refused if the file is not OFF)
#   2 remove the Studio's Stripe key (without it the Studio's code refuses every Stripe call)
#   3 read the Studio's secret list: it MUST be readable and MUST NOT contain STRIPE_SECRET_KEY
#   4 check from outside that the checkout Worker reports the pilot OFF
# Prints "OFF VERIFIED" and exits 0 only if all four are confirmed. Otherwise prints "OFF NOT VERIFIED" with what could not
# be confirmed and the manual steps, and exits 1. It never reports success without that evidence.
# WRANGLER and OUTSIDE_CHECK can be overridden (tests only); the default outside check is resolved from this script's own
# directory BEFORE changing directory, so it works however the script is invoked.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || exit 2
W="${WRANGLER:-npx --yes wrangler@4.150.0}"
OUTSIDE="${OUTSIDE_CHECK:-bash $HERE/checkout-outside-check.sh}"
cd "$1" || { echo "OFF NOT VERIFIED: worker directory $1 not found"; exit 1; }
OFF="$2"
ok=1
if [ -f "$OFF" ] && grep -q '^CHECKOUT_PILOT_ENABLED = "false"' "$OFF" && ! grep -q '^CHECKOUT_LIVE' "$OFF"; then
  $W deploy --config "$OFF" > /dev/null 2>&1 && echo "  off: plotart-checkout deployed with the pilot OFF" || { echo "  off: FAILED to deploy the OFF configuration"; ok=0; }
else
  echo "  off: $OFF is missing or not an OFF configuration; nothing deployed"; ok=0
fi
printf 'y\n' | $W secret delete STRIPE_SECRET_KEY --name plotart-studio > /dev/null 2>&1 && echo "  off: the Studio's Stripe key removed" || echo "  off: the Studio's Stripe key was not removed (absent, or the removal failed; checked next)"
printf 'y\n' | $W secret delete STRIPE_BASKET_KEY --name plotart-studio > /dev/null 2>&1 && echo "  off: the Studio's basket key removed" || true
if L=$($W secret list --name plotart-studio 2> /dev/null) && N=$(printf '%s' "$L" | python3 -c 'import json,sys; print(" ".join(x["name"] for x in json.load(sys.stdin)))' 2> /dev/null); then
  if [[ " $N " == *" STRIPE_SECRET_KEY "* || " $N " == *" STRIPE_BASKET_KEY "* ]]; then echo "  off: the Studio STILL holds a Stripe key"; ok=0; else echo "  off: confirmed: the Studio holds no Stripe key"; fi
else
  echo "  off: the Studio's secret list could not be read, so the key's removal is NOT confirmed"; ok=0
fi
sleep "${OFF_WAIT:-10}"
$OUTSIDE "${ORIGIN:-}" off > /dev/null 2>&1 && echo "  off: checked from outside: pilot OFF" || { echo "  off: the outside check did NOT confirm the pilot OFF"; ok=0; }
if [ $ok = 1 ]; then echo "OFF VERIFIED: live checkout is off (no live payment possible)"; exit 0; fi
echo "OFF NOT VERIFIED: switch the pilot off manually (deploy $OFF for plotart-checkout) and remove plotart-studio's STRIPE_SECRET_KEY; then check $ORIGIN/v1/status."
exit 1
