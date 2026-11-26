#!/usr/bin/env bash
# PlotNua · garden-lead Worker checked from outside (Package N, Step C). Writes NOTHING: every request is refused at the
# release gate before its body is read (no preview key is ever sent).
#   bash outside-check.sh https://plotnua-garden-lead.colin-a41.workers.dev
set -euo pipefail
U="${1:?worker url}"; ok=0; bad=0
t() { local name="$1" want="$2" got="$3"; if [ "$got" = "$want" ]; then echo "PASS  $name ($got)"; ok=$((ok+1)); else echo "FAIL  $name (wanted $want, got $got)"; bad=$((bad+1)); fi; }
H=(-H "origin: https://plotnua.ie" -H "content-type: application/json" -H "sec-fetch-site: cross-site" -H "sec-fetch-mode: cors")
t "preflight from plotnua.ie is allowed" 204 "$(curl -s -o /dev/null -w '%{http_code}' -X OPTIONS "${H[@]}" "$U/v1/introduction")"
t "preflight from another origin is refused" 403 "$(curl -s -o /dev/null -w '%{http_code}' -X OPTIONS -H 'origin: https://example.com' "$U/v1/introduction")"
B=$(curl -s -X POST "${H[@]}" --data '{}' "$U/v1/introduction"); t "introductions closed: not_open" '{"ok":false,"state":"not_open"}' "$B"
B=$(curl -s -X POST "${H[@]}" --data '{}' "$U/v1/garden-lead/enquiry"); t "Yard Box Phase A route closed: not_open" '{"ok":false,"state":"not_open"}' "$B"
t "no read surface (GET refused)" 405 "$(curl -s -o /dev/null -w '%{http_code}' "${H[@]}" "$U/v1/introduction")"
echo "OUTSIDE CHECK · $ok passed, $bad failed"; [ "$bad" -eq 0 ]
