#!/usr/bin/env bash
# Proof of the founder approval checkpoint for website releases (Stage 1, founder decision 20 Nov 2026).
#   release-preview.sh       shows the commit and changed files, offers a release only when it can be released
#   verify-founder-approval.sh  refuses unless website-production requires the founder AND this run carries his approval
# A throw-away local "origin" stands in for GitHub and a stub stands in for the GitHub API.
# Never touches GitHub, Pages or production.        bash atlas-tools/release/prove-founder-approval.sh
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; PV="$HERE/release-preview.sh"; VF="$HERE/verify-founder-approval.sh"
T=$(mktemp -d); cd "$T"; fails=0
ok() { if eval "$2"; then echo "  PASS  $1"; else echo "  FAIL  $1"; fails=$((fails+1)); fi; }
git init -q --bare origin.git; git clone -q origin.git w 2>/dev/null; cd w
git config user.name t; git config user.email t@t; git checkout -q -b main
echo a > a.html; git add -A; git commit -qm base; git push -q origin main
git checkout -q -b release/auto/topic-x; echo b > b.html; echo c >> a.html; git add -A; git commit -qm "Release title"; git push -q origin release/auto/topic-x
S=$(git rev-parse HEAD)
pv() { GITHUB_STEP_SUMMARY="$T/sum" GITHUB_OUTPUT="$T/out" bash "$PV" "$@" > "$T/log" 2>&1; }
: > "$T/sum"; : > "$T/out"; pv "$S" release/auto/topic-x; rc=$?
ok "preview: a releasable commit is offered for approval (release=true)" '[ $rc = 0 ] && grep -qx release=true "$T/out"'
ok "preview: the summary shows the full commit, its title, main and every changed file" 'grep -q "$S" "$T/sum" && grep -q "Release title" "$T/sum" && grep -q "a.html" "$T/sum" && grep -q "b.html" "$T/sum" && grep -q "| Files changed | 2 |" "$T/sum"'
ok "preview: it says rejecting changes nothing and a moved main is refused" 'grep -q "Reject" "$T/sum" && grep -q "never merged over the newer work" "$T/sum"'
ok "preview: nothing was pushed or changed on main" '[ "$(git ls-remote origin refs/heads/main | cut -f1)" = "$(git rev-parse main)" ]'
: > "$T/out"; pv "${S:0:7}" release/auto/topic-x; rc=$?
ok "preview: a bad commit id is refused, no approval requested" '[ $rc = 1 ] && grep -qx release=false "$T/out"'
: > "$T/out"; pv "$S" feature/x; rc=$?
ok "preview: a branch outside release/auto/ is refused" '[ $rc = 1 ] && grep -qx release=false "$T/out"'
# branch moved after its checks
git checkout -q -b release/auto/moved; echo m > m.html; git add -A; git commit -qm m; M1=$(git rev-parse HEAD); git push -q origin release/auto/moved; echo n > n.html; git add -A; git commit -qm n; git push -q origin release/auto/moved
: > "$T/out"; pv "$M1" release/auto/moved; rc=$?
ok "preview: a release branch that moved since its checks is refused" '[ $rc = 1 ] && grep -qx release=false "$T/out" && grep -q "has moved" "$T/log"'
# main already contains the commit (e.g. an automatic rollback already released in its own run)
git checkout -q main; git merge -q --ff-only "$S"; git push -q origin main
: > "$T/out"; : > "$T/sum"; pv "$S" release/auto/topic-x; rc=$?
ok "preview: nothing to release when main already contains the commit (no approval requested)" '[ $rc = 0 ] && grep -qx release=false "$T/out" && grep -q "Nothing to release" "$T/sum"'
# main moved past a waiting release (newer work)
git checkout -q -b release/auto/stale "$S~1"; echo s > s.html; git add -A; git commit -qm stale; ST=$(git rev-parse HEAD); git push -q origin release/auto/stale
: > "$T/out"; pv "$ST" release/auto/stale; rc=$?
ok "preview: a release that no longer contains the current main is refused, no approval requested" '[ $rc = 1 ] && grep -qx release=false "$T/out" && grep -q "does not contain the current main" "$T/log"'

# --- verify-founder-approval.sh against a stub GitHub API ---
cat > "$T/gh" <<'EOS'
#!/bin/bash
case "$2" in
  */environments/*) [ -f "$MOCK/env" ] && cat "$MOCK/env" || exit 1 ;;
  */approvals) [ -f "$MOCK/app" ] && cat "$MOCK/app" || exit 1 ;;
  *) exit 1 ;;
esac
EOS
cat > "$T/pub" <<'EOS'
#!/bin/bash
[ -f "$MOCK/pubenv" ] && cat "$MOCK/pubenv" || exit 1
EOS
U() { printf '{"type":"User","reviewer":{"login":"%s"}}' "$1"; }
ENV_OK="{\"name\":\"website-production\",\"protection_rules\":[{\"type\":\"branch_policy\"},{\"type\":\"required_reviewers\",\"prevent_self_review\":false,\"reviewers\":[$(U colin-macaulay-dcu)]}]}"
APP_OK='[{"state":"approved","comment":"","user":{"login":"colin-macaulay-dcu"},"environments":[{"name":"website-production"}]}]'
vf() { # $1 env json or -, $2 approvals json or -, $3 public env json or -, $4 run id
  rm -rf "$T/m"; mkdir "$T/m"; [ "$1" = - ] || printf '%s' "$1" > "$T/m/env"; [ "$2" = - ] || printf '%s' "$2" > "$T/m/app"; [ "$3" = - ] || printf '%s' "$3" > "$T/m/pubenv"
  MOCK="$T/m" GH_CMD="bash $T/gh" PUBLIC_API="bash $T/pub x" GITHUB_STEP_SUMMARY="$T/vsum" bash "$VF" "${4:-123}" > "$T/vlog" 2>&1; }
vf "$ENV_OK" "$APP_OK" -; rc=$?; ok "verify: environment requires the founder and he approved this run -> allowed" '[ $rc = 0 ]'
vf - "$APP_OK" "$ENV_OK"; rc=$?; ok "verify: environment read through the public API when the job token cannot -> allowed" '[ $rc = 0 ]'
vf - "$APP_OK" -; rc=$?; ok "verify: environment unreadable -> refused" '[ $rc = 1 ]'
vf '{"name":"website-production","protection_rules":[]}' "$APP_OK" -; rc=$?; ok "verify: environment exists without protection (auto-created) -> refused" '[ $rc = 1 ]'
vf "{\"protection_rules\":[{\"type\":\"required_reviewers\",\"reviewers\":[$(U someone-else)]}]}" "$APP_OK" -; rc=$?; ok "verify: environment requires someone else -> refused" '[ $rc = 1 ]'
vf '{"protection_rules":[{"type":"required_reviewers","reviewers":[{"type":"Team","reviewer":{"login":"colin-macaulay-dcu"}}]}]}' "$APP_OK" -; rc=$?; ok "verify: a team reviewer is not the founder -> refused" '[ $rc = 1 ]'
vf "$ENV_OK" '[]' -; rc=$?; ok "verify: no approval on this run -> refused" '[ $rc = 1 ]'
vf "$ENV_OK" '[{"state":"rejected","user":{"login":"colin-macaulay-dcu"},"environments":[{"name":"website-production"}]}]' -; rc=$?; ok "verify: the founder rejected -> refused" '[ $rc = 1 ]'
vf "$ENV_OK" '[{"state":"approved","user":{"login":"someone-else"},"environments":[{"name":"website-production"}]}]' -; rc=$?; ok "verify: approved by someone else -> refused" '[ $rc = 1 ]'
vf "$ENV_OK" '[{"state":"approved","user":{"login":"colin-macaulay-dcu"},"environments":[{"name":"studio-production."}]}]' -; rc=$?; ok "verify: an approval for another environment (Studio) does not count -> refused" '[ $rc = 1 ]'
vf "$ENV_OK" - -; rc=$?; ok "verify: approvals unreadable -> refused" '[ $rc = 1 ]'
vf "$ENV_OK" 'not json' -; rc=$?; ok "verify: malformed approvals -> refused" '[ $rc = 1 ]'
vf "$ENV_OK" "$APP_OK" - "12a"; rc=$?; ok "verify: a bad run id -> refused" '[ $rc = 1 ]'
ok "verify: a refusal says production is unchanged" 'grep -q "unchanged" "$T/vsum"'
echo; echo "FOUNDER APPROVAL PROOF · $([ $fails = 0 ] && echo OK || echo FAIL) · $fails failed"; rm -rf "$T"; exit $fails
