#!/usr/bin/env bash
# Proof of the checked release route (automation v1, revised 1 Nov 2026: no bypass of main's rules).
# A throw-away local "origin" stands in for GitHub. A pre-receive hook plays the role of the main ruleset's required
# status check: main may only move to a commit recorded in checks-passed (what the Image rights gate does on GitHub),
# never by force. The "gate" is simulated by DISPATCH_CMD, which records a branch's head as checked.
# Never touches GitHub, Pages or production.        bash atlas-tools/release/prove-release-promote.sh
set -uo pipefail
P="$(cd "$(dirname "$0")" && pwd)/promote.sh"
T=$(mktemp -d); cd "$T"; fails=0
ok() { if eval "$2"; then echo "  PASS  $1"; else echo "  FAIL  $1"; fails=$((fails+1)); fi; }
git init -q --bare origin.git; touch "$T/checks-passed"
cat > origin.git/hooks/pre-receive <<EOS
#!/bin/bash
while read old new ref; do
  [ "\$ref" = refs/heads/main ] || continue
  grep -qx "\$new" "$T/checks-passed" || { echo "ruleset: required check 'gate' has not passed on \${new:0:7}"; exit 1; }
  [ "\$old" = 0000000000000000000000000000000000000000 ] || git merge-base --is-ancestor "\$old" "\$new" || { echo "ruleset: non-fast-forward"; exit 1; }
done
EOS
chmod +x origin.git/hooks/pre-receive
git clone -q origin.git w 2>/dev/null; cd w; git config user.name t; git config user.email t@t; git checkout -q -b main
echo v1 > index.html; git add -A; git commit -qm base; git rev-parse HEAD >> "$T/checks-passed"; git push -q origin main
export PAGES_CMD=true GITHUB_STEP_SUMMARY=/dev/null
gate() { git -C "$T/w" fetch -q origin "$1" && git -C "$T/w" rev-parse "origin/$1" >> "$T/checks-passed"; }   # the gate passes
printf '#!/bin/bash\ngit -C "%s/w" fetch -q origin "$1" && git -C "%s/w" rev-parse "origin/$1" >> "%s/checks-passed"\n' "$T" "$T" "$T" > "$T/dispatch"; chmod +x "$T/dispatch"
export DISPATCH_CMD="$T/dispatch"
rel() { git checkout -q -B "release/auto/$1" origin/main; echo "$2" > index.html; git commit -qam "$1"; git push -q -f origin "release/auto/$1"; git rev-parse HEAD; }
main() { git ls-remote origin refs/heads/main | cut -f1; }
# 0 the ruleset itself
git checkout -q -B direct origin/main; echo unchecked > index.html; git commit -qam unchecked; U=$(git rev-parse HEAD)
git push -q origin "$U:refs/heads/main" 2>/dev/null; ok "a direct push of an unchecked commit to main is refused" '[ "$(main)" != "$U" ]'
# 1 success
S=$(rel one v2); gate release/auto/one; HEALTH_CMD=true bash "$P" "$S" release/auto/one >/dev/null 2>&1; rc=$?
ok "a release whose gate passed fast-forwards main" '[ $rc = 0 ] && [ "$(main)" = "$S" ]'
ok "it is tagged prod/..." 'git ls-remote --tags origin | grep -q "prod/.*-${S:0:7}"'
# 1b unchecked release
S=$(rel unchecked v2b); HEALTH_CMD=true bash "$P" "$S" release/auto/unchecked >/dev/null 2>&1; rc=$?
ok "promote cannot move main to a commit whose gate has not passed (no bypass)" '[ $rc != 0 ] && [ "$(main)" != "$S" ]'
# 2 live check fails -> revert released through the same checked route
git fetch -q origin; B=$(main); S=$(rel two BROKEN); gate release/auto/two
printf '#!/bin/bash\n[ "$1" != "%s" ]\n' "$S" > "$T/h2"; chmod +x "$T/h2"
HEALTH_CMD="$T/h2" bash "$P" "$S" release/auto/two >/dev/null 2>&1; rc=$?
ok "a failed live check exits 2 (alert) and leaves the bad release live only until the revert is released" '[ $rc = 2 ] && [ "$(main)" = "$S" ]'
git fetch -q origin; RB="release/auto/rollback-${S:0:7}"; R=$(git rev-parse "origin/$RB" 2>/dev/null || echo none)
ok "the revert is a new commit on its own release branch, with content identical to before" '[ "$R" != none ] && [ -z "$(git diff "$B" "$R")" ] && git merge-base --is-ancestor "$S" "$R"'
ok "the gate was dispatched on the revert (it is recorded as checked)" 'grep -qx "$R" "$T/checks-passed"'
HEALTH_CMD=true bash "$P" "$R" "$RB" >/dev/null 2>&1; rc=$?
ok "the revert is then released like any other commit: main back to the previous content" '[ $rc = 0 ] && [ "$(main)" = "$R" ] && [ -z "$(git diff "$B" "$(main)")" ]'
# 2b a failing rollback release does not loop
git fetch -q origin; S=$(rel three BROKEN2); gate release/auto/three
printf '#!/bin/bash\nexit 1\n' > "$T/hx"; chmod +x "$T/hx"
HEALTH_CMD="$T/hx" bash "$P" "$S" release/auto/three >/dev/null 2>&1
git fetch -q origin; RB="release/auto/rollback-${S:0:7}"; R=$(git rev-parse "origin/$RB")
HEALTH_CMD="$T/hx" bash "$P" "$R" "$RB" >/dev/null 2>&1; rc=$?
ok "a rollback that also fails its live check stops (alert, no revert of the revert)" '[ $rc = 2 ] && ! git ls-remote origin | grep -q "rollback-${R:0:7}"'
# 3 refusals
git fetch -q origin; M=$(main)
git checkout -q -B release/auto/old "$B"; echo old > index.html; git commit -qam old; git push -q -f origin release/auto/old; S=$(git rev-parse HEAD); gate release/auto/old
HEALTH_CMD=true bash "$P" "$S" release/auto/old >/dev/null 2>&1; rc=$?
ok "a release that does not contain the current main is refused" '[ $rc = 1 ] && [ "$(main)" = "$M" ]'
S=$(rel four v4); gate release/auto/four; echo v5 > index.html; git commit -qam later; git push -q origin release/auto/four
HEALTH_CMD=true bash "$P" "$S" release/auto/four >/dev/null 2>&1; rc=$?
ok "a branch that moved after its checks is refused" '[ $rc = 1 ] && [ "$(main)" = "$M" ]'
HEALTH_CMD=true bash "$P" "$S" feature/x >/dev/null 2>&1; rc=$?
ok "only release/auto/* branches can be promoted" '[ $rc = 1 ]'
ok "promote.sh never forces a push" '! grep -qE "push[^#]*(-f|--force)" "$P"'
echo; echo "RELEASE PROMOTE PROOF · $([ $fails = 0 ] && echo OK || echo FAIL) · $fails failed"; rm -rf "$T"; exit $fails
