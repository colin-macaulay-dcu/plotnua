#!/usr/bin/env bash
# Prints the error block of a failed Wrangler run, sanitised: ANSI colours stripped, long token-like strings, bearer
# values and anything after "token"/"secret"/"key" separators redacted. Never fails; falls back to a fixed message.
# Usage: wrangler-error.sh <wrangler.log>
f="${1:-}"
[ -s "$f" ] || { echo "  (Wrangler wrote no log)"; exit 0; }
out=$(sed -E 's/\x1B\[[0-9;]*[A-Za-z]//g' "$f" 2>/dev/null \
  | awk '/✘|\[ERROR\]/ {p=1} p && n<16 {print; n++} p && /^[[:space:]]*$/ {b++} b>=2 {exit}' 2>/dev/null \
  | sed -E 's/(Bearer|bearer)[[:space:]]+[^[:space:]]+/\1 [redacted]/g; s/((token|secret|key)[^[:alnum:]]{1,3})[^[:space:]]+/\1[redacted]/Ig; s/[A-Za-z0-9_-]{32,}/[redacted]/g' 2>/dev/null)
[ -n "$out" ] || out="(no error block found in the Wrangler log)"
printf '%s\n' "$out" | sed 's/^/  | /'
exit 0
