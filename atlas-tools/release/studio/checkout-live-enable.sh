#!/usr/bin/env bash
# PlotArt · managed checkout · LIVE enablement, fail-closed (20 Nov 2026, review of PR #38).
#   bash checkout-live-enable.sh <worker dir>
# Run only by the live path of plotart-checkout-deploy.yml, after the founder's Approve on the studio-production. environment
# and after check-stripe-live-secrets.sh has passed. Needs, from the environment (values never printed):
#   LIVE_RUNTIME_KEY LIVE_WEBHOOK_SECRET LIVE_RESEND_KEY LIVE_STUDIO_KEY   the LIVE credentials
#   ORIGIN                                                                 the production checkout origin
#   and in <worker dir>: wrangler.checkout.production.off.toml (pilot OFF) and wrangler.checkout.production.toml (LIVE).
# Order. Live checkout is switched on LAST, by one deploy, only after every credential is written and verified:
#   1 deploy plotart-checkout with the pilot explicitly OFF (any earlier version, live or not, is replaced by OFF)
#   2 write the checkout Worker's three secrets and the Studio's live key (all written fresh on every run: none is stale)
#   3 verify that every required secret is present on both Workers
#   4 deploy the LIVE configuration (the only step that enables live checkout)
#   5 check from outside that the Worker reports live mode
# Any failure, at any step, runs the RECOVERY and the run fails: the checkout Worker is redeployed OFF, the Studio's live
# Stripe key is deleted (without it the Studio's code refuses every Stripe call), and the Worker is checked from outside as
# OFF. If the recovery itself cannot be verified the run says so plainly ("RECOVERY NOT VERIFIED") for manual action.
# WRANGLER and OUTSIDE_CHECK can be overridden (tests only).
set -uo pipefail
cd "$1" || exit 2
W="${WRANGLER:-npx --yes wrangler@4.150.0}"
OUTSIDE="${OUTSIDE_CHECK:-bash $(cd "$(dirname "$0")" && pwd)/checkout-outside-check.sh}"
OFF=wrangler.checkout.production.off.toml; ON=wrangler.checkout.production.toml
for f in "$OFF" "$ON"; do [ -f "$f" ] || { echo "FAIL  $f missing"; exit 1; }; done
grep -q '^CHECKOUT_PILOT_ENABLED = "false"' "$OFF" && ! grep -q '^CHECKOUT_LIVE' "$OFF" || { echo "FAIL  $OFF is not an OFF configuration"; exit 1; }
grep -q '^CHECKOUT_LIVE = "true"' "$ON" || { echo "FAIL  $ON is not the live configuration"; exit 1; }

recover() {
  echo "FAIL  $1: RECOVERY (switching live checkout off)"
  local ok=1
  $W deploy --config "$OFF" > /dev/null 2>&1 && echo "  recovery: plotart-checkout redeployed with the pilot OFF" || { echo "  recovery: FAILED to redeploy OFF"; ok=0; }
  printf 'y\n' | $W secret delete STRIPE_SECRET_KEY --name plotart-studio > /dev/null 2>&1 && echo "  recovery: the Studio's live Stripe key removed" || echo "  recovery: the Studio's live Stripe key was not present or could not be removed"
  if $W secret list --name plotart-studio 2> /dev/null | grep -q '"STRIPE_SECRET_KEY"'; then echo "  recovery: the Studio STILL holds a Stripe key"; ok=0; fi
  sleep "${RECOVERY_WAIT:-10}"
  $OUTSIDE "$ORIGIN" off > /dev/null 2>&1 && echo "  recovery: checked from outside: pilot OFF" || { echo "  recovery: the outside check did not confirm OFF"; ok=0; }
  if [ $ok = 1 ]; then echo "RECOVERED: live checkout is OFF (no live payment possible). Fix the cause and run again."
  else echo "RECOVERY NOT VERIFIED: switch the pilot off manually (deploy $OFF) and remove plotart-studio's STRIPE_SECRET_KEY."; fi
  exit 1
}
put() {   # put <secret name> <value> <wrangler target args...>
  local n="$1" v="$2"; shift 2
  [ -n "$v" ] || recover "$n is empty"
  printf '%s' "$v" | $W secret put "$n" "$@" > /dev/null 2>&1 || recover "writing $n failed"
}
names() { $W secret list "$@" 2> /dev/null | python3 -c 'import json,sys; print(" ".join(sorted(x["name"] for x in json.load(sys.stdin))))' 2> /dev/null; }

echo "STEP 1  deploy plotart-checkout with the pilot OFF"
$W deploy --config "$OFF" > /dev/null 2>&1 || recover "the OFF deployment"
echo "STEP 2  write the LIVE secrets (checkout Worker, then Studio)"
put STRIPE_SECRET_KEY     "${LIVE_RUNTIME_KEY:-}"    --config "$ON"
put STRIPE_WEBHOOK_SECRET "${LIVE_WEBHOOK_SECRET:-}" --config "$ON"
put RESEND_API_KEY        "${LIVE_RESEND_KEY:-}"     --config "$ON"
put STRIPE_SECRET_KEY     "${LIVE_STUDIO_KEY:-}"     --name plotart-studio
echo "STEP 3  verify every required secret is present"
C=$(names --config "$ON"); S=$(names --name plotart-studio)
for n in RESEND_API_KEY STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET; do [[ " $C " == *" $n "* ]] || recover "plotart-checkout is missing $n"; done
for n in RESEND_API_KEY STRIPE_SECRET_KEY; do [[ " $S " == *" $n "* ]] || recover "plotart-studio is missing $n"; done
echo "STEP 4  deploy the LIVE configuration (enables live checkout)"
$W deploy --config "$ON" > "${RUNNER_TEMP:-/tmp}/wrangler-live.log" 2>&1 || recover "the LIVE deployment"
grep -E "^Current Version ID" "${RUNNER_TEMP:-/tmp}/wrangler-live.log" || true
echo "STEP 5  check from outside: live mode"
sleep "${LIVE_WAIT:-10}"
$OUTSIDE "$ORIGIN" live || recover "the outside check of live mode"
echo "LIVE CHECKOUT ENABLED: every credential written and verified before the live deployment; outside check passed"
