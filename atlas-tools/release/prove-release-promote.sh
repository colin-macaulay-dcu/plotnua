#!/usr/bin/env bash
# Proof of promote.sh (automation v1): controlled success and failure tests against a throw-away local "origin".
# Never touches GitHub, Pages or production.     bash atlas-tools/release/prove-release-promote.sh
set -uo pipefail
P="$(cd "$(dirname "$0")" && pwd)/promote.sh"
T=$(mktemp -d); cd "$T"; fails=0
ok() { if eval "$2"; then echo "  PASS  $1"; else echo "  FAIL  $1"; fails=$((fails+1)); fi; }
git init -q --bare origin.git
git clone -q origin.git w 2>/dev/null; cd w; git config protocol.version 0
git config user.name t; git config user.email t@t; git checkout -q -b main
echo "v1" > index.html; git add -A; git commit -qm base; git push -q origin main
export PAGES_CMD=true GITHUB_STEP_SUMMARY=/dev/null
rel() { git checkout -q -B "release/auto/$1" origin/main; echo "$2" > index.html; git commit -qam "$1"; git push -q -f origin "release/auto/$1"; git rev-parse HEAD; }
# 1 success
S=$(rel one v2); HEALTH_CMD=true bash "$P" "$S" release/auto/one >/dev/null; rc=$?
ok "a green release fast-forwards main" '[ $rc = 0 ] && [ "$(git ls-remote origin refs/heads/main | cut -f1)" = "$S" ]'
ok "it is tagged prod/…" 'git ls-remote --tags origin | grep -q "prod/.*-${S:0:7}"'
# 2 live check fails -> automatic revert
git fetch -q origin; B=$(git rev-parse origin/main); S=$(rel two BROKEN)
printf '#!/bin/bash\n[ "$1" != "%s" ]\n' "$S" > "$T/h2"; chmod +x "$T/h2"
HEALTH_CMD="$T/h2" bash "$P" "$S" release/auto/two >/dev/null 2>&1; rc=$?
git fetch -q origin; M=$(git rev-parse origin/main)
ok "a failed live check exits 2 (alert)" '[ $rc = 2 ]'
ok "main is rolled back to identical content by a new revert commit (no reset)" '[ "$M" != "$S" ] && git merge-base --is-ancestor "$S" "$M" && [ -z "$(git diff "$B" "$M")" ]'
ok "the revert's own live check passed (the health command saw the revert commit)" '[ "$(git log -1 --format=%s "$M")" != two ]'
# 3 main moved since the branch was cut -> refused, nothing changes
git checkout -q -B release/auto/three "$B"; echo v3 > index.html; git commit -qam three; git push -q -f origin release/auto/three; S=$(git rev-parse HEAD)
HEALTH_CMD=true bash "$P" "$S" release/auto/three >/dev/null; rc=$?
ok "a release that does not contain the current main is refused" '[ $rc = 1 ] && [ "$(git ls-remote origin refs/heads/main | cut -f1)" = "$M" ]'
# 4 branch moved after its checks ran -> refused
S=$(rel four v4); echo v5 > index.html; git commit -qam later; git push -q origin release/auto/four
HEALTH_CMD=true bash "$P" "$S" release/auto/four >/dev/null; rc=$?
ok "a branch that moved after its checks is refused" '[ $rc = 1 ] && [ "$(git ls-remote origin refs/heads/main | cut -f1)" = "$M" ]'
# 5 not a release/auto branch
HEALTH_CMD=true bash "$P" "$S" feature/x >/dev/null; rc=$?
ok "only release/auto/* branches can be promoted" '[ $rc = 1 ]'
# 6 rollback refused if main moved again after the release
S=$(rel six v6)
cat > "$T/h6" <<EOS
#!/bin/bash
cd "$T" && rm -rf o && git clone -q -b main origin.git o 2>/dev/null && cd o && git config user.name o && git config user.email o@o && echo z > z && git add -A && git commit -qm other && git push -q origin HEAD:main
exit 1
EOS
chmod +x "$T/h6"; HEALTH_CMD="$T/h6" bash "$P" "$S" release/auto/six > /dev/null 2>&1; rc=$?
git fetch -q origin
ok "no automatic revert if someone else moved main meanwhile (alert instead)" '[ $rc = 2 ] && [ "$(git log -1 --format=%s origin/main)" = other ]'
ok "promote.sh never forces a push" '! grep -qE "push[^#]*(-f|--force)" "$P"'
echo; echo "RELEASE PROMOTE PROOF · $([ $fails = 0 ] && echo OK || echo FAIL) · $fails failed"; rm -rf "$T"; exit $fails
