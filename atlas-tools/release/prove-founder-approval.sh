#!/usr/bin/env bash
# shellcheck disable=SC2034,SC2016  # each check is a single-quoted string evaluated later by ok(): rc, NEWMAIN etc. are read there
# Proof of the founder approval checkpoint for website releases (Stage 1, founder decision 20 Nov 2026).
#   release-preview.sh       shows the commit and changed files, offers a release only when it can be released
#   verify-founder-approval.sh  refuses unless website-production requires the founder AND this run carries his approval
# A throw-away local "origin" stands in for GitHub and a stub stands in for the GitHub API.
# Never touches GitHub, Pages or production.        bash atlas-tools/release/prove-founder-approval.sh
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; PV="$HERE/release-preview.sh"; VF="$HERE/verify-founder-approval.sh"
T=$(mktemp -d); cd "$T" || exit 1; fails=0
ok() { if eval "$2"; then echo "  PASS  $1"; else echo "  FAIL  $1"; fails=$((fails+1)); fi; }
git init -q --bare origin.git; git clone -q origin.git w 2>/dev/null; cd w || exit 1
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

# --- main moves while a release waits for approval: the existing promote.sh must refuse, never overwrite ---
git checkout -q main; git checkout -q -b release/auto/waiting; echo w > w.html; git add -A; git commit -qm waiting; WS=$(git rev-parse HEAD); git push -q origin release/auto/waiting
: > "$T/out"; pv "$WS" release/auto/waiting; rc=$?
ok "wait: a release that contains main is offered for approval" '[ $rc = 0 ] && grep -qx release=true "$T/out"'
git checkout -q main; echo g > garden.html; git add -A; git commit -qm "publisher released while the founder was deciding"; git push -q origin main; NEWMAIN=$(git rev-parse HEAD)
PAGES_CMD=true HEALTH_CMD=true GITHUB_STEP_SUMMARY="$T/psum" bash "$HERE/promote.sh" "$WS" release/auto/waiting > "$T/plog" 2>&1; rc=$?
ok "wait: once main has moved, the approved release is refused by promote.sh and main keeps the newer work" '[ $rc = 1 ] && grep -q "does not contain the current main" "$T/plog" && [ "$(git ls-remote origin refs/heads/main | cut -f1)" = "$NEWMAIN" ]'
git checkout -q -b release/auto/old "$S"; git push -q origin release/auto/old 2>/dev/null
PAGES_CMD=true HEALTH_CMD=true GITHUB_STEP_SUMMARY="$T/psum" bash "$HERE/promote.sh" "$S" release/auto/old > "$T/plog" 2>&1; rc=$?
ok "wait: an approval for a commit main has already passed cannot move main backwards" '[ $rc = 1 ] && [ "$(git ls-remote origin refs/heads/main | cut -f1)" = "$NEWMAIN" ]'

# --- verify-founder-approval.sh against a stub GitHub API ---
cat > "$T/gh" <<'EOS'
#!/bin/bash
[ -f "$MOCK/ghdown" ] && exit 1
case "$2" in
  */deployment-branch-policies*) [ -f "$MOCK/br" ] && cat "$MOCK/br" || exit 1 ;;
  */environments/*) [ -f "$MOCK/env" ] && cat "$MOCK/env" || exit 1 ;;
  */approvals) [ -f "$MOCK/app" ] && cat "$MOCK/app" || exit 1 ;;
  *) exit 1 ;;
esac
EOS
cat > "$T/pub" <<'EOS'
#!/bin/bash
case "$1" in
  */deployment-branch-policies*) [ -f "$MOCK/br" ] && cat "$MOCK/br" || exit 22 ;;
  */environments/*) [ -f "$MOCK/env" ] && cat "$MOCK/env" || exit 22 ;;
  */approvals) [ -f "$MOCK/app" ] && cat "$MOCK/app" || exit 22 ;;
  *) exit 22 ;;
esac
EOS
U() { printf '{"type":"User","reviewer":{"login":"%s"}}' "$1"; }
BP=',{"type":"branch_policy"}'
envj() { # $1 reviewers json, $2 can_admins_bypass, $3 protected_branches, $4 custom, $5 extra rules
  printf '{"name":"website-production","can_admins_bypass":%s,"protection_rules":[{"type":"required_reviewers","prevent_self_review":false,"reviewers":[%s]}%s],"deployment_branch_policy":{"protected_branches":%s,"custom_branch_policies":%s}}' "$2" "$1" "${5-$BP}" "$3" "$4"; }
ENV_OK=$(envj "$(U colin-macaulay-dcu)" false false true)
BR_OK='{"total_count":1,"branch_policies":[{"id":1,"name":"main","type":"branch"}]}'
APP_OK='[{"state":"approved","comment":"","user":{"login":"colin-macaulay-dcu"},"environments":[{"name":"website-production"}]}]'
vf() { # $1 env, $2 branch policies, $3 approvals (- = unreadable), $4 run id, $5 "ghdown" to make the job token fail
  rm -rf "$T/m"; mkdir "$T/m"; [ "$1" = - ] || printf '%s' "$1" > "$T/m/env"; [ "$2" = - ] || printf '%s' "$2" > "$T/m/br"; [ "$3" = - ] || printf '%s' "$3" > "$T/m/app"; [ "${5:-}" = ghdown ] && touch "$T/m/ghdown"
  MOCK="$T/m" GH_CMD="bash $T/gh" PUBLIC_API="bash $T/pub " GITHUB_STEP_SUMMARY="$T/vsum" bash "$VF" "${4:-123}" > "$T/vlog" 2>&1; }
yes_() { vf "$@"; rc=$?; ok "verify ALLOWS: $LABEL" '[ $rc = 0 ]'; }
no_() { vf "$@"; rc=$?; ok "verify REFUSES: $LABEL" '[ $rc = 1 ] && grep -q REFUSED "$T/vlog"'; }
LABEL="environment as approved, founder approved this run"; yes_ "$ENV_OK" "$BR_OK" "$APP_OK"
LABEL="job token cannot read, GitHub's public API answers (public repository)"; yes_ "$ENV_OK" "$BR_OK" "$APP_OK" 123 ghdown
LABEL="neither the job token nor the public API can read the environment"; no_ - "$BR_OK" "$APP_OK" 123 ghdown
LABEL="environment missing (both reads fail)"; no_ - "$BR_OK" "$APP_OK"
LABEL="environment auto-created by GitHub with no protection rules"; no_ '{"name":"website-production","can_admins_bypass":true,"protection_rules":[],"deployment_branch_policy":null}' "$BR_OK" "$APP_OK"
LABEL="answer for a different environment"; no_ "$(envj "$(U colin-macaulay-dcu)" false false true | sed 's/website-production/release-automation/')" "$BR_OK" "$APP_OK"
LABEL="required reviewer is someone else"; no_ "$(envj "$(U someone-else)" false false true)" "$BR_OK" "$APP_OK"
LABEL="required reviewer is a team, not the founder's account"; no_ "$(envj '{"type":"Team","reviewer":{"login":"colin-macaulay-dcu"}}' false false true)" "$BR_OK" "$APP_OK"
LABEL="founder plus another user as reviewers"; no_ "$(envj "$(U colin-macaulay-dcu),$(U someone-else)" false false true)" "$BR_OK" "$APP_OK"
LABEL="founder plus a team as reviewers"; no_ "$(envj "$(U colin-macaulay-dcu),{\"type\":\"Team\",\"reviewer\":{\"slug\":\"t\"}}" false false true)" "$BR_OK" "$APP_OK"
LABEL="the founder listed twice"; no_ "$(envj "$(U colin-macaulay-dcu),$(U colin-macaulay-dcu)" false false true)" "$BR_OK" "$APP_OK"
LABEL="no reviewers listed in the rule"; no_ "$(envj "" false false true)" "$BR_OK" "$APP_OK"
LABEL="an unexpected reviewer entry (no type)"; no_ "$(envj '{"reviewer":{"login":"colin-macaulay-dcu"}}' false false true)" "$BR_OK" "$APP_OK"
LABEL="two required-reviewer rules"; no_ "$(envj "$(U colin-macaulay-dcu)" false false true ",{\"type\":\"branch_policy\"},{\"type\":\"required_reviewers\",\"reviewers\":[$(U someone-else)]}")" "$BR_OK" "$APP_OK"
LABEL="an extra wait-timer rule"; no_ "$(envj "$(U colin-macaulay-dcu)" false false true ',{"type":"branch_policy"},{"type":"wait_timer","wait_timer":5}')" "$BR_OK" "$APP_OK"
LABEL="an extra custom protection rule (third-party app)"; no_ "$(envj "$(U colin-macaulay-dcu)" false false true ',{"type":"branch_policy"},{"type":"custom","app":{"slug":"x"}}')" "$BR_OK" "$APP_OK"
LABEL="prevent self-review switched on (founder could not approve)"; no_ "$(envj "$(U colin-macaulay-dcu)" false false true | sed 's/"prevent_self_review":false/"prevent_self_review":true/')" "$BR_OK" "$APP_OK"
LABEL="GitHub does not say whether self-review is prevented"; no_ "$(envj "$(U colin-macaulay-dcu)" false false true | sed 's/"prevent_self_review":false,//')" "$BR_OK" "$APP_OK"
LABEL="a protection rule that is not an object"; no_ "$(envj "$(U colin-macaulay-dcu)" false false true ',{"type":"branch_policy"},"x"')" "$BR_OK" "$APP_OK"
LABEL="administrators may bypass the rules"; no_ "$(envj "$(U colin-macaulay-dcu)" true false true)" "$BR_OK" "$APP_OK"
LABEL="GitHub does not say whether administrators may bypass"; no_ "$(envj "$(U colin-macaulay-dcu)" null false true)" "$BR_OK" "$APP_OK"
LABEL="deployments allowed from all branches (no branch policy)"; no_ "$(printf '{"name":"website-production","can_admins_bypass":false,"protection_rules":[{"type":"required_reviewers","reviewers":[%s]}],"deployment_branch_policy":null}' "$(U colin-macaulay-dcu)")" "$BR_OK" "$APP_OK"
LABEL="deployments from protected branches instead of selected branches"; no_ "$(envj "$(U colin-macaulay-dcu)" false true false)" "$BR_OK" "$APP_OK"
LABEL="branch policy flags set but no branch_policy rule"; no_ "$(envj "$(U colin-macaulay-dcu)" false false true '')" "$BR_OK" "$APP_OK"
LABEL="branch policies unreadable"; no_ "$ENV_OK" - "$APP_OK"
LABEL="branch policy is a wildcard"; no_ "$ENV_OK" '{"total_count":1,"branch_policies":[{"name":"*","type":"branch"}]}' "$APP_OK"
LABEL="branch policies allow main AND another branch"; no_ "$ENV_OK" '{"total_count":2,"branch_policies":[{"name":"main","type":"branch"},{"name":"release/*","type":"branch"}]}' "$APP_OK"
LABEL="a tag named main instead of the branch"; no_ "$ENV_OK" '{"total_count":1,"branch_policies":[{"name":"main","type":"tag"}]}' "$APP_OK"
LABEL="branch policies answer incomplete (count disagrees)"; no_ "$ENV_OK" '{"total_count":3,"branch_policies":[{"name":"main","type":"branch"}]}' "$APP_OK"
LABEL="no branch policies at all"; no_ "$ENV_OK" '{"total_count":0,"branch_policies":[]}' "$APP_OK"
LABEL="no approval on this run"; no_ "$ENV_OK" "$BR_OK" '[]'
LABEL="the founder rejected"; no_ "$ENV_OK" "$BR_OK" '[{"state":"rejected","user":{"login":"colin-macaulay-dcu"},"environments":[{"name":"website-production"}]}]'
LABEL="approved by someone else"; no_ "$ENV_OK" "$BR_OK" '[{"state":"approved","user":{"login":"someone-else"},"environments":[{"name":"website-production"}]}]'
LABEL="an approval for the Studio environment does not count"; no_ "$ENV_OK" "$BR_OK" '[{"state":"approved","user":{"login":"colin-macaulay-dcu"},"environments":[{"name":"studio-production."}]}]'
LABEL="approval without its environment list"; no_ "$ENV_OK" "$BR_OK" '[{"state":"approved","user":{"login":"colin-macaulay-dcu"}}]'
LABEL="approvals unreadable"; no_ "$ENV_OK" "$BR_OK" -
LABEL="approvals answer is an error object, not a list"; no_ "$ENV_OK" "$BR_OK" '{"message":"Resource not accessible by integration"}'
LABEL="approvals answer malformed"; no_ "$ENV_OK" "$BR_OK" 'not json'
LABEL="environment answer is an error object"; no_ '{"message":"Not Found"}' "$BR_OK" "$APP_OK"
LABEL="a bad run id"; no_ "$ENV_OK" "$BR_OK" "$APP_OK" "12a"
LABEL="run id zero"; no_ "$ENV_OK" "$BR_OK" "$APP_OK" "0"
ok "verify: a refusal says production is unchanged and why" 'grep -q "unchanged" "$T/vsum" && grep -q "refused before release" "$T/vsum"'
# the real approval record of a Studio deploy (run 44737245394, read 20 Nov 2026), checked for the right environment only
REAL='[{"state":"approved","comment":"","environments":[{"id":1,"node_id":"x","name":"studio-production.","url":"u","html_url":"h","created_at":"c","updated_at":"u"}],"user":{"login":"colin-macaulay-dcu","id":1,"type":"User"}}]'
LABEL="GitHub's real approval record format, for the Studio, is not a website approval"; no_ "$ENV_OK" "$BR_OK" "$REAL"
LABEL="GitHub's real approval record format, for website-production, is accepted"; yes_ "$ENV_OK" "$BR_OK" "$(printf '%s' "$REAL" | sed 's/studio-production\./website-production/')"

# --- which jobs GitHub runs: release-promote.yml's real conditions, every outcome of preview and approval ---
python3 "$HERE/prove-approval-jobs.py" "$HERE/../../.github/workflows/release-promote.yml" > "$T/jl" 2>&1; rc=$?
cat "$T/jl" | sed 's/^/  /' | tail -4
ok "jobs: promote runs ONLY after a successful preview offering the release AND a successful (approved) approval job" '[ $rc = 0 ]'
echo; echo "FOUNDER APPROVAL PROOF · $([ $fails = 0 ] && echo OK || echo FAIL) · $fails failed"; rm -rf "$T"; exit $fails
