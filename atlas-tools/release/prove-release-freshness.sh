#!/usr/bin/env bash
# PROVE · refresh-stale-candidates.sh against a local bare repository and a stand-in `gh` (nothing touches GitHub).
#   bash atlas-tools/release/prove-release-freshness.sh
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
pass=0; fail=0; ok() { if eval "$2"; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
echo "PROVE · release candidate freshness"
git init -q --bare "$T/origin.git"; git clone -q "$T/origin.git" "$T/w" 2>/dev/null; cd "$T/w"
git config user.name t; git config user.email t@example.invalid; git checkout -q -b main
echo a > a.html; git add -A; git commit -qm base; git push -q origin HEAD:main
# three candidates waiting: fresh, stale-but-mergeable, stale-and-conflicting
git checkout -q -b c1 main; echo f > fresh.html; git add -A; git commit -qm fresh; F=$(git rev-parse HEAD); git push -q origin "$F:refs/heads/release/auto/fresh-${F:0:7}"
git checkout -q -b c2 main; echo s > stale.html; git add -A; git commit -qm stale; S=$(git rev-parse HEAD); git push -q origin "$S:refs/heads/release/auto/stale-${S:0:7}"
git checkout -q -b c3 main; echo mine > shared.html; git add -A; git commit -qm conflict; C=$(git rev-parse HEAD); git push -q origin "$C:refs/heads/release/auto/clash-${C:0:7}"
# main moves (another release / merged pull request)
git checkout -q main; git pull -q origin main; echo theirs > shared.html; git add -A; git commit -qm "newer work on main"; git push -q origin HEAD:main; NEWMAIN=$(git rev-parse HEAD)
git checkout -q c1; git -c user.name=t -c user.email=t@x merge -q --no-edit main; F=$(git rev-parse HEAD); git push -q origin "$F:refs/heads/release/auto/fresh-x"   # a fresh one
# stand-in gh: lists three waiting runs; records cancels and ops alerts
mkdir -p "$T/bin"; cat > "$T/bin/gh" <<EOF
#!/usr/bin/env bash
echo "\$*" >> "$T/gh.log"
case "\$1 \$2" in
  "run list") printf '101\tRelease to production · release/auto/fresh-x\n102\tRelease to production · release/auto/stale-${S:0:7}\n103\tRelease to production · release/auto/clash-${C:0:7}\n104\tRelease to production · main\n' ;;
  "run cancel") echo cancelled ;;
  "label create") ;;
  "issue list") echo "" ;;
  "issue create"|"issue comment") echo "\$@" >> "$T/alerts.log" ;;
esac
EOF
chmod +x "$T/bin/gh"
PATH="$T/bin:$PATH" GITHUB_REPOSITORY=o/r bash "$HERE/refresh-stale-candidates.sh" > "$T/out" 2>&1; rc=$?
ok "the script completes" '[ $rc = 0 ]'
ok "a candidate that contains main is left alone (its run is not cancelled)" '! grep -q "run cancel 101" "$T/gh.log" && grep -q "run 101: .* still contains main" "$T/out"'
ok "the waiting run of a stale candidate is cancelled" 'grep -q "run cancel 102" "$T/gh.log"'
NB=$(git ls-remote "$T/origin.git" 'refs/heads/release/auto/stale-*' | cut -f2 | grep -v "stale-${S:0:7}" | head -1); NS=$(git ls-remote "$T/origin.git" "$NB" | cut -f1)
ok "it is refreshed as a NEW release/auto/ branch that contains the new main and the candidate change" '[ -n "$NS" ] && git fetch -q origin "$NS" && git merge-base --is-ancestor "$NEWMAIN" "$NS" && git merge-base --is-ancestor "$S" "$NS" && [ "$NB" = "refs/heads/release/auto/stale-${NS:0:7}" ]'
ok "the original candidate branch is untouched" '[ "$(git ls-remote "$T/origin.git" refs/heads/release/auto/stale-${S:0:7} | cut -f1)" = "$S" ]'
ok "main is untouched (newer work kept, nothing forced)" '[ "$(git ls-remote "$T/origin.git" refs/heads/main | cut -f1)" = "$NEWMAIN" ]'
ok "a conflicting candidate is cancelled, nothing is pushed for it, and an ops alert asks for a manual rebase" 'grep -q "run cancel 103" "$T/gh.log" && [ "$(git ls-remote "$T/origin.git" "refs/heads/release/auto/clash-*" | wc -l)" = 1 ] && grep -q "manual rebase needed" "$T/alerts.log"'
ok "the refresh is reported (approval needed again)" 'grep -q "approval needed again" "$T/alerts.log"'
ok "a run whose title names no release/auto/ branch is left alone" '! grep -q "run cancel 104" "$T/gh.log"'
echo "PROVE RELEASE FRESHNESS · $((pass+fail)) checks, $pass passed, $fail failed"; [ $fail = 0 ]
