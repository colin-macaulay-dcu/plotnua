#!/usr/bin/env bash
# PlotArt · enquiry relay outside check (F2, 6 Nov 2026). Checks the live relay from the internet, the way plotnua.ie uses
# it, WITHOUT ever creating an enquiry: every POST has a blank name, which every version of the relay refuses (400) before
# it reads or writes the database or sends any email. An open relay answers "Please check your name."; a closed one 503.
#   bash relay-outside-check.sh <base url> new        after an F2 deploy: open, both notice versions, garden route off
#   bash relay-outside-check.sh <base url> previous   after a rollback: open, today's notice version accepted
set -uo pipefail
U="${1%/}"; MODE="${2:-new}"; E="$U/v1/enquiry"; bad=0
[[ "$U" =~ ^https?://[a-z0-9.:-]+$ ]] || { echo "FAIL  not a relay address"; exit 1; }
req() { curl -s -o "$T" -w "%{http_code}" "$@"; }
T=$(mktemp)
chk() { if [ "$2" = "$3" ] && { [ -z "${4:-}" ] || grep -q "$4" "$T"; }; then echo "  PASS  $1 ($2)"; else echo "  FAIL  $1: got $2 $(head -c 100 "$T"), expected $3 ${4:-}"; bad=1; fi; }
chk "GET is refused" "$(req "$E")" 405
chk "another website is refused" "$(req -X POST -H 'Origin: https://evil.example' -H 'Content-Type: application/json' -d '{}' "$E")" 403
chk "plotnua.ie may send enquiries (CORS pre-check)" "$(curl -s -o "$T" -D - -w "%{http_code}" -X OPTIONS -H 'Origin: https://plotnua.ie' -H 'Access-Control-Request-Method: POST' "$E" | tail -1)" 204
O=$(curl -s -D - -o /dev/null -X OPTIONS -H 'Origin: https://plotnua.ie' -H 'Access-Control-Request-Method: POST' "$E" | tr -d '\r' | grep -i '^access-control-allow-origin:' | awk '{print $2}')
[ "$O" = "https://plotnua.ie" ] && echo "  PASS  CORS allows https://plotnua.ie only" || { echo "  FAIL  CORS allow-origin is '$O'"; bad=1; }
P() { req -X POST -H 'Origin: https://plotnua.ie' -H 'Content-Type: application/json' -d "{\"notice\":\"$1\",\"name\":\"\"}" "$E"; }
chk "OPEN, and notice PA-ENQ-2026-10-29 accepted (blank name refused, nothing stored)" "$(P PA-ENQ-2026-10-29)" 400 "Please check your name"
if [ "$MODE" = new ]; then
  chk "notice PA-ENQ-2026-11 accepted (blank name refused, nothing stored)" "$(P PA-ENQ-2026-11)" 400 "Please check your name"
  chk "Borrowed Garden route present and OFF" "$(req -X POST -H 'Origin: https://plotnua.ie' -H 'Content-Type: application/json' -d '{}' "$U/v1/garden-enquiry")" 503
fi
rm -f "$T"
[ $bad = 0 ] && echo "RELAY OUTSIDE CHECK OK ($MODE)" || { echo "RELAY OUTSIDE CHECK FAILED ($MODE)"; exit 1; }
