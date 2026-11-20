#!/usr/bin/env bash
# PlotArt · managed checkout pilot · outside check (development 16 Nov 2026). Checks a deployed checkout Worker from the
# internet WITHOUT creating anything: an unknown quote token, an unsigned webhook and an unknown path. Never sends a secret.
#   bash checkout-outside-check.sh <base url> off   pilot switched off (production, or test before it is switched on)
#   bash checkout-outside-check.sh <base url> on    test environment with the pilot switched on
#   bash checkout-outside-check.sh <base url> live  production with live checkout enabled (status must report mode "live")
set -uo pipefail
U="${1%/}"; MODE="${2:-off}"; bad=0
[[ "$U" =~ ^https://[a-z0-9.-]+$ ]] || { [ "${CHECK_ALLOW_LOCAL:-}" = 1 ] && [[ "$U" =~ ^http://127\.0\.0\.1:[0-9]+$ ]]; } || { echo "FAIL  not a checkout address"; exit 1; }
T=$(mktemp)
req() { curl -s -o "$T" -D "$T.h" -w "%{http_code}" "$@"; }
chk() { if [[ " $3 " == *" $2 "* ]]; then echo "  PASS  $1 ($2)"; else echo "  FAIL  $1: got $2, expected $3"; bad=1; fi; }
TOKEN=$(printf 'a%.0s' $(seq 1 48))
S=$(curl -s "$U/v1/status")
if [ "$MODE" = live ]; then echo "$S" | grep -q '"mode":"live"' && echo "  PASS  status reports LIVE mode" || { echo "  FAIL  status does not report live mode: $S"; bad=1; }; MODE=on; fi
if [ "$MODE" = on ]; then echo "$S" | grep -q '"pilot_enabled":true' && echo "  PASS  status reports the pilot ON" || { echo "  FAIL  status: $S"; bad=1; }
else echo "$S" | grep -q '"pilot_enabled":false' && echo "  PASS  status reports the pilot OFF" || { echo "  FAIL  status: $S"; bad=1; }; fi
if [ "$MODE" = on ]; then chk "an unknown quote reaches nothing" "$(req "$U/q/$TOKEN")" 404
else chk "buyer pages are closed while the pilot is off (503; 404 before migration 0016)" "$(req "$U/q/$TOKEN")" "503 404"; fi
grep -qi '^x-robots-tag: noindex' "$T.h" && echo "  PASS  pages are noindex" || { echo "  FAIL  noindex header missing"; bad=1; }
if [ "$MODE" = on ]; then W=400; else W="400 503"; fi
chk "an unsigned webhook is refused (503 before migration 0016)" "$(req -X POST -H 'Content-Type: application/json' -d '{"id":"evt_x","livemode":false}' "$U/v1/stripe/webhook")" "$W"
chk "a webhook GET is refused" "$(req "$U/v1/stripe/webhook")" 405
chk "anything else is not found" "$(req "$U/anything")" 404
rm -f "$T" "$T.h"
[ $bad = 0 ] && echo "CHECKOUT OUTSIDE CHECK OK ($MODE)" || { echo "CHECKOUT OUTSIDE CHECK FAILED ($MODE)"; exit 1; }
