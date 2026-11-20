#!/usr/bin/env bash
# PlotArt · managed checkout · LIVE enablement, fail-closed (20 Nov 2026, PR #38 reviews 1 and 2).
#   bash checkout-live-enable.sh <worker dir>
# Run only by the live path of plotart-checkout-deploy.yml, after the founder's Approve on the studio-production. environment
# and after check-stripe-live-secrets.sh has passed. Needs, from the environment (values never printed):
#   LIVE_RUNTIME_KEY LIVE_WEBHOOK_SECRET LIVE_RESEND_KEY LIVE_STUDIO_KEY   the LIVE credentials
#   ORIGIN                                                                 the production checkout origin
#   and in <worker dir>: wrangler.checkout.production.off.toml (pilot OFF) and wrangler.checkout.production.toml (LIVE).
# Order. Live checkout is switched on LAST, by one deploy, only after every credential is written and verified:
#   1 deploy plotart-checkout with the pilot explicitly OFF (any earlier version, live or not, is replaced by OFF)
#   2 write the checkout Worker's three secrets and the Studio's live key, all fresh on every run (none is stale)
#   3 verify that every required secret is present on both Workers
#   4 deploy the LIVE configuration (the only step that enables live checkout)
#   5 check from outside that the Worker reports live mode
# Secrets are written and listed by Worker NAME (--name), never through the LIVE config file. Wrangler 4.150.0's
# `secret put` (checked in its source, cli.js secretPutCommand) only PUTs {name, text} to .../workers/scripts/<name>/secrets:
# it uploads no code and no vars, so it cannot apply the LIVE configuration; Cloudflare adds the secret to a new version of
# the currently deployed one (step 1's OFF version) and refuses if the latest version is not the deployed one.
# Any failure, at any step after the start, runs checkout-live-off.sh: OFF redeployed, the Studio's live key removed and its
# absence confirmed from a readable secret list, OFF confirmed from outside. Success is reported only on that evidence;
# otherwise "OFF NOT VERIFIED" with manual steps. The run always fails after a recovery.
# WRANGLER and OUTSIDE_CHECK can be overridden (tests only). Paths are resolved before changing directory.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || exit 2
W="${WRANGLER:-npx --yes wrangler@4.150.0}"
OUTSIDE="${OUTSIDE_CHECK:-bash $HERE/checkout-outside-check.sh}"
WD="$(cd "$1" && pwd)" || { echo "FAIL  worker directory $1 not found"; exit 1; }
cd "$WD"
OFF=wrangler.checkout.production.off.toml; ON=wrangler.checkout.production.toml
for f in "$OFF" "$ON"; do [ -f "$f" ] || { echo "FAIL  $f missing (nothing changed)"; exit 1; }; done
grep -q '^CHECKOUT_PILOT_ENABLED = "false"' "$OFF" && ! grep -q '^CHECKOUT_LIVE' "$OFF" || { echo "FAIL  $OFF is not an OFF configuration (nothing changed)"; exit 1; }
grep -q '^CHECKOUT_LIVE = "true"' "$ON" && grep -q '^name = "plotart-checkout"' "$ON" || { echo "FAIL  $ON is not the live plotart-checkout configuration (nothing changed)"; exit 1; }

recover() {
  echo "FAIL  $1: RECOVERY (switching live checkout off)"
  bash "$HERE/checkout-live-off.sh" "$WD" "$OFF"
  echo "The live activation FAILED. Fix the cause and run again."
  exit 1
}
put() {   # put <secret name> <value> <worker name>
  [ -n "$2" ] || recover "$1 for $3 is empty"
  printf '%s' "$2" | $W secret put "$1" --name "$3" > /dev/null 2>&1 || recover "writing $1 to $3 failed"
}
names() { local l; l=$($W secret list --name "$1" 2> /dev/null) || return 1; printf '%s' "$l" | python3 -c 'import json,sys; print(" ".join(sorted(x["name"] for x in json.load(sys.stdin))))' 2> /dev/null; }

echo "STEP 1  deploy plotart-checkout with the pilot OFF"
$W deploy --config "$OFF" > /dev/null 2>&1 || recover "the OFF deployment"
echo "STEP 2  write the LIVE secrets (by Worker name; the LIVE config is not used)"
put STRIPE_SECRET_KEY     "${LIVE_RUNTIME_KEY:-}"    plotart-checkout
put STRIPE_WEBHOOK_SECRET "${LIVE_WEBHOOK_SECRET:-}" plotart-checkout
put RESEND_API_KEY        "${LIVE_RESEND_KEY:-}"     plotart-checkout
put STRIPE_SECRET_KEY     "${LIVE_STUDIO_KEY:-}"     plotart-studio
echo "STEP 3  verify every required secret is present"
C=$(names plotart-checkout) || recover "the secret list of plotart-checkout could not be read"
S=$(names plotart-studio) || recover "the secret list of plotart-studio could not be read"
for n in RESEND_API_KEY STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET; do [[ " $C " == *" $n "* ]] || recover "plotart-checkout is missing $n"; done
for n in RESEND_API_KEY STRIPE_SECRET_KEY; do [[ " $S " == *" $n "* ]] || recover "plotart-studio is missing $n"; done
echo "STEP 4  deploy the LIVE configuration (enables live checkout)"
$W deploy --config "$ON" > "${RUNNER_TEMP:-/tmp}/wrangler-live.log" 2>&1 || recover "the LIVE deployment"
grep -E "^Current Version ID" "${RUNNER_TEMP:-/tmp}/wrangler-live.log" || true
echo "STEP 5  check from outside: live mode"
sleep "${LIVE_WAIT:-10}"
$OUTSIDE "$ORIGIN" live || recover "the outside check of live mode"
echo "LIVE CHECKOUT ENABLED: every credential written and verified before the live deployment; outside check passed"
