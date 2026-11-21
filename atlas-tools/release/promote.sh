#!/usr/bin/env bash
# PlotNua · promote a checked release commit to main, verify it live, and roll back automatically (automation v1).
# Called by .github/workflows/release-promote.yml from a copy of the scripts taken from main (never from the release).
#   bash promote.sh <40-char sha> <release branch>
# Env (overridable for the local proof): HEALTH_CMD (gets the expected commit as its last argument), PAGES_CMD.
# Env (GitHub Actions): RELEASE_PUSH_TOKEN, the 1-hour "PlotNua Release" App token minted by the calling job from the
# release-automation environment (main only); main and the prod/ tag are pushed with it. RELEASE_PUSH_REMOTE (proof only).
# Exit 0 = released and verified (or nothing to do); 1 = refused (nothing changed) ; 2 = released, failed, rolled back.
set -euo pipefail
SHA="$1"; BRANCH="$2"
HERE="$(cd "$(dirname "$0")" && pwd)"
HEALTH_CMD="${HEALTH_CMD:-python3 $HERE/site-health.py --expect-commit}"
PAGES_CMD="${PAGES_CMD:-bash $HERE/pages-build.sh}"
# A revert is a new commit: it gets no exemption from main's required checks. It is pushed to its own release branch by
# push-release-branch.sh (the "PlotNua Release" App token in GitHub Actions), so its gate starts on that PUSH, and it is
# then promoted like any other release (Stage 1, 10 Nov 2026: nothing is dispatched any more).
PUSH_CMD="${PUSH_CMD:-bash $HERE/push-release-branch.sh}"
SUM="${GITHUB_STEP_SUMMARY:-/dev/null}"
refuse() { echo "REFUSED: $*"; echo "- **refused:** $*" >> "$SUM"; exit 1; }
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || refuse "bad commit id"
[[ "$BRANCH" == release/auto/* ]] || refuse "not a release/auto/ branch"
# Stage 2 (founder approval to prepare, 21 Nov 2026): main and its prod/ tag are pushed as the "PlotNua Release" GitHub
# App, never with the workflow's built-in GITHUB_TOKEN, so that main's "Restrict updates" ruleset can admit the App
# alone. In GitHub Actions a missing App token is a refusal before anything happens; nothing is pushed.
if [ "${GITHUB_ACTIONS:-}" = "true" ] && [ -z "${RELEASE_PUSH_TOKEN:-}" ]; then
  refuse "no RELEASE_PUSH_TOKEN (the PlotNua Release App token) in GitHub Actions: main and production tags are only pushed as the App"
fi
# release_push <refspec>...: ONE atomic push. GitHub applies every ref or none, so main never moves without its prod/
# tag and the tag never exists without main. In Actions it authenticates with the App token only (the empty extraheader
# first clears the built-in token that actions/checkout stored, as push-release-branch.sh does); elsewhere (the local
# proof) it is an ordinary push. Never forces, never prints the token.
release_push() {
  local out rc remote auth
  if [ -n "${RELEASE_PUSH_TOKEN:-}" ]; then
    remote="${RELEASE_PUSH_REMOTE:-https://github.com/${GITHUB_REPOSITORY:?}.git}"
    auth=$(printf 'x-access-token:%s' "$RELEASE_PUSH_TOKEN" | base64 | tr -d '\n')
    set +e
    out=$(git -c http.https://github.com/.extraheader= -c "http.https://github.com/.extraheader=AUTHORIZATION: basic $auth" \
        push -q --atomic "$remote" "$@" 2>&1); rc=$?
    set -e
    out="${out//"$RELEASE_PUSH_TOKEN"/***}"; out="${out//"$auth"/***}"
  else
    set +e; out=$(git push -q --atomic origin "$@" 2>&1); rc=$?; set -e
  fi
  [ -z "$out" ] || printf '%s\n' "$out"
  return "$rc"
}
git fetch -q origin main "$BRANCH"
BEFORE=$(git rev-parse origin/main)
[ "$(git rev-parse "origin/$BRANCH")" = "$SHA" ] || refuse "$BRANCH has moved since its checks ran"
if [ "$BEFORE" = "$SHA" ]; then echo "nothing to release: main is already ${SHA:0:7}"; exit 0; fi
git merge-base --is-ancestor "$BEFORE" "$SHA" || refuse "${SHA:0:7} does not contain the current main ${BEFORE:0:7}"
{ echo "### Release ${SHA:0:7} from \`$BRANCH\`"; echo "- main before: \`$BEFORE\`"; echo "- files changed:"; git diff --name-only "$BEFORE" "$SHA" | sed 's/^/  - `/; s/$/`/'; } >> "$SUM"
T="prod/$(date -u +%Y%m%d-%H%M%S)-${SHA:0:7}"; git tag "$T" "$SHA"
# fast-forward only (no force); main's rulesets still require the gate on $SHA and refuse a non-fast-forward
if release_push "$SHA:refs/heads/main" "refs/tags/$T"; then
  echo "- released and tagged \`$T\` (pushed as the PlotNua Release App)" >> "$SUM"
else
  # The push reported a failure. Re-read main before deciding: if GitHub did apply it (an error after the update, e.g. a
  # dropped connection), the release is live and MUST still get its live check and, if needed, its rollback below.
  if ! git fetch -q origin main 2>/dev/null; then
    # main cannot be re-read, so whether the release is live is unknown: never claim "nothing was released"
    echo "FOUNDER ATTENTION: the push of ${SHA:0:7} reported an error and main could not be re-read; check main and the live site"
    echo "- **the push reported an error and main could not be re-read: whether ${SHA:0:7} is live is unknown. FOUNDER ATTENTION: check main and the live site.**" >> "$SUM"
    exit 2
  fi
  if [ "$(git rev-parse origin/main 2>/dev/null)" != "$SHA" ]; then
    git tag -d "$T" > /dev/null 2>&1 || true
    refuse "the push of main and its production tag was rejected (main moved, a ruleset refused it, or the App token was not accepted): nothing was released"
  fi
  echo "- **the push reported an error but main is now \`${SHA:0:7}\`: continuing to the live check**" >> "$SUM"
fi
$PAGES_CMD || true
if $HEALTH_CMD "$SHA"; then echo "- live check passed" >> "$SUM"; echo "RELEASED ${SHA:0:7}"; exit 0; fi
# --- automatic rollback: a revert commit on top (never a reset), released through the same checked route ---
echo "live check FAILED"
if [[ "$BRANCH" == release/auto/rollback-* ]]; then echo "- **a rollback release failed its live check: no further automatic action**" >> "$SUM"; exit 2; fi
git fetch -q origin main
[ "$(git rev-parse origin/main)" = "$SHA" ] || { echo "- **live check failed and main moved after the release: NOT reverted automatically**" >> "$SUM"; exit 2; }
# A release that changed workflow files cannot be reverted automatically: the release App has no Workflows permission
# (by design), so GitHub would refuse the revert's push. Those releases come through the founder route and are rolled
# back by the founder's rollback-<name>.sh.
WF=$(git diff --name-only "$BEFORE" "$SHA" -- .github/workflows | tr '\n' ' ')
if [ -n "$WF" ]; then
  echo "FOUNDER ROLLBACK REQUIRED: ${SHA:0:7} changed workflow files ($WF)"
  { echo "- **live check failed and this release changed workflow files (\`$WF\`): automatic rollback is not possible.**"
    echo "  **FOUNDER ROLLBACK REQUIRED** (\`rollback-<name>.sh\`, or a revert of ${BEFORE:0:7}..${SHA:0:7} through the release route)."; } >> "$SUM"
  printf 'founder_rollback_required=%s\n' "${SHA}" >> "${PROMOTE_OUT:-${GITHUB_OUTPUT:-/dev/null}}"
  exit 2
fi
git -c user.name="PlotNua release automation" -c user.email="hello@plotnua.ie" checkout -q -B plotnua-rollback "$SHA"
git -c user.name="PlotNua release automation" -c user.email="hello@plotnua.ie" revert --no-edit "$BEFORE..$SHA" > /dev/null
[ -z "$(git diff "$BEFORE" HEAD --stat)" ] || { echo "- **revert does not restore ${BEFORE:0:7} exactly: NOT pushed**" >> "$SUM"; exit 2; }
# The rollback branch keeps the released branch's topic, so "Release to production" can leave the rollbacks of
# self-promoting publishers (plotart, garden, ideas) to their own promote step, exactly like their releases.
RB="release/auto/rollback-${BRANCH#release/auto/}"
$PUSH_CMD "$(git rev-parse HEAD)" "$RB" || { echo "- **the revert could not be pushed to \`$RB\`: FOUNDER ROLLBACK REQUIRED**" >> "$SUM"; exit 2; }
# record the revert for the caller: promote-after-gate.sh waits for this exact commit's push-started gate and promotes
# it (in "Release to production" a second run started by that gate then finds nothing left to release).
printf 'rollback_branch=%s\nrollback_sha=%s\n' "$RB" "$(git rev-parse HEAD)" >> "${PROMOTE_OUT:-${GITHUB_OUTPUT:-/dev/null}}"
echo "- **automatic rollback requested**: \`$RB\` (content identical to \`${BEFORE:0:7}\`) goes through the gate and is released by the next run" >> "$SUM"
exit 2
