#!/usr/bin/env bash
# PROVE · refresh-stale-candidates.sh against a local bare repository and a stand-in `gh` (nothing touches GitHub).
#   bash atlas-tools/release/prove-release-freshness.sh
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
pass=0; fail=0; ok() { if eval "$2"; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
echo "PROVE · release candidate freshness"
git init -q --bare "$T/origin.git"; git clone -q "$T/origin.git" "$T/w" 2>/dev/null; cd "$T/w"
git config user.name t; git config user.email t@example.invalid; git checkout -q -b main
echo a > a.html; git add -A; git commit -qm base; git push -q origin HEAD:main 2>/dev/null
cand() { git checkout -q -b "$1" main; echo "$2" > "$3"; git add -A; git commit -qm "$1"; local s; s=$(git rev-parse HEAD); git push -q origin "$s:refs/heads/release/auto/$1-${s:0:7}" 2>/dev/null; echo "$s"; }
S=$(cand stale s stale.html); C=$(cand clash mine shared.html); L=$(cand busy-rf3 b busy.html); D=$(cand dup d dup.html)
git checkout -q main; echo theirs > shared.html; git add -A; git commit -qm "newer work on main"; git push -q origin HEAD:main 2>/dev/null; NEWMAIN=$(git rev-parse HEAD)
git checkout -q -b fresh main; echo f > fresh.html; git add -A; git commit -qm fresh; F=$(git rev-parse HEAD); git push -q origin "$F:refs/heads/release/auto/fresh-${F:0:7}" 2>/dev/null
# "dup" was already re-requested by hand on top of the new main
git checkout -q -b dup2 main; echo d > dup.html; git add -A; git commit -qm dup2; D2=$(git rev-parse HEAD); git push -q origin "$D2:refs/heads/release/auto/dup-${D2:0:7}" 2>/dev/null
mkdir -p "$T/bin"; cat > "$T/bin/gh" <<EOF
#!/usr/bin/env bash
echo "\$*" >> "$T/gh.log"
case "\$1 \$2" in
  "run list") printf '101\tRelease to production · release/auto/fresh-${F:0:7}\n102\tRelease to production · release/auto/stale-${S:0:7}\n103\tRelease to production · release/auto/clash-${C:0:7}\n104\tRelease to production · main\n105\tRelease to production · release/auto/busy-rf3-${L:0:7}\n106\tRelease to production · release/auto/dup-${D:0:7}\n' ;;
  "run cancel") echo cancelled ;;
  "label create") ;;
  "issue list") echo "" ;;
  "issue create"|"issue comment") echo "\$@" >> "$T/alerts.log" ;;
esac
EOF
chmod +x "$T/bin/gh"; touch "$T/alerts.log"
# as in GitHub Actions: the refresher pushes through push-release-branch.sh with an App token (here a dummy, to the local remote)
run() { PATH="$T/bin:$PATH" GITHUB_ACTIONS=true GITHUB_REPOSITORY=o/r GITHUB_OUTPUT="$T/ghout" RELEASE_PUSH_TOKEN=test-token RELEASE_PUSH_REMOTE="$T/origin.git" bash "$HERE/refresh-stale-candidates.sh" "$@"; }
run --cancel > "$T/out1" 2>&1; rc1=$?
STALE=$(sed -n 's/^stale=//p' "$T/ghout")
ok "cancel: completes" '[ $rc1 = 0 ]'
ok "cancel: a candidate that contains main is left alone" '! grep -q "run cancel 101" "$T/gh.log"'
ok "cancel: the waiting run of every stale candidate is cancelled (102, 103, 105, 106)" 'grep -q "run cancel 102" "$T/gh.log" && grep -q "run cancel 103" "$T/gh.log" && grep -q "run cancel 105" "$T/gh.log" && grep -q "run cancel 106" "$T/gh.log"'
ok "cancel: a run whose title names no release/auto/ branch is left alone" '! grep -q "run cancel 104" "$T/gh.log"'
ok "cancel: pushes nothing" '[ "$(git ls-remote "$T/origin.git" "refs/heads/release/auto/*" | wc -l)" = 6 ]'
run --refresh $STALE > "$T/out2" 2>&1; rc2=$?
ok "refresh: completes" '[ $rc2 = 0 ]'
NB=$(git ls-remote "$T/origin.git" 'refs/heads/release/auto/stale-rf1-*' | cut -f2); NS=$(git ls-remote "$T/origin.git" "$NB" | cut -f1)
ok "refresh: a stale candidate becomes a NEW branch (stale-rf1-<sha>) containing the new main and its own change" '[ -n "$NS" ] && git fetch -q origin "$NS" && git merge-base --is-ancestor "$NEWMAIN" "$NS" && git merge-base --is-ancestor "$S" "$NS" && [ "$NB" = "refs/heads/release/auto/stale-rf1-${NS:0:7}" ]'
ok "refresh: the original candidate branch and main are untouched (nothing forced)" '[ "$(git ls-remote "$T/origin.git" refs/heads/release/auto/stale-${S:0:7} | cut -f1)" = "$S" ] && [ "$(git ls-remote "$T/origin.git" refs/heads/main | cut -f1)" = "$NEWMAIN" ]'
ok "refresh: a conflicting candidate pushes nothing and asks for a manual rebase" '[ "$(git ls-remote "$T/origin.git" "refs/heads/release/auto/clash-*" | wc -l)" = 1 ] && grep -q "manual rebase needed" "$T/alerts.log"'
ok "refresh: no loop: a candidate already refreshed three times is not refreshed again" '[ "$(git ls-remote "$T/origin.git" "refs/heads/release/auto/busy-*" | wc -l)" = 1 ] && grep -q "refresh limit reached" "$T/alerts.log"'
ok "refresh: a topic already re-requested on top of main is not refreshed again" '[ "$(git ls-remote "$T/origin.git" "refs/heads/release/auto/dup-*" | wc -l)" = 2 ] && grep -q "already contains main; not refreshed" "$T/out2"'
ok "refresh: the refreshed candidate is reported (approval needed again)" 'grep -q "approval needed again" "$T/alerts.log"'
run --refresh "release/auto/stale-rf1-${NS:0:7}" > "$T/out3" 2>&1
ok "refresh: running again does nothing for a candidate that now contains main" 'grep -q "already contains main" "$T/out3" && [ "$(git ls-remote "$T/origin.git" "refs/heads/release/auto/stale-*" | wc -l)" = 2 ]'
echo "PROVE RELEASE FRESHNESS · $((pass+fail)) checks, $pass passed, $fail failed"; [ $fail = 0 ]
