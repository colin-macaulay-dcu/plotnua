#!/usr/bin/env bash
# PlotNua · promote a checked release commit to main, verify it live, and roll back automatically (automation v1).
# Called by .github/workflows/release-promote.yml from a copy of the scripts taken from main (never from the release).
#   bash promote.sh <40-char sha> <release branch>
# Env (overridable for the local proof): HEALTH_CMD (gets the expected commit as its last argument), PAGES_CMD.
# Exit 0 = released and verified (or nothing to do); 1 = refused (nothing changed) ; 2 = released, failed, rolled back.
set -euo pipefail
SHA="$1"; BRANCH="$2"
HERE="$(cd "$(dirname "$0")" && pwd)"
HEALTH_CMD="${HEALTH_CMD:-python3 $HERE/site-health.py --expect-commit}"
PAGES_CMD="${PAGES_CMD:-bash $HERE/pages-build.sh}"
# A revert is a new commit: it gets no exemption from main's required checks. It is pushed to its own release branch and
# the gate is dispatched on it; this workflow then promotes it like any other release.
DISPATCH_CMD="${DISPATCH_CMD:-gh workflow run image-rights-gate.yml -R ${GITHUB_REPOSITORY:-} --ref}"
SUM="${GITHUB_STEP_SUMMARY:-/dev/null}"
refuse() { echo "REFUSED: $*"; echo "- **refused:** $*" >> "$SUM"; exit 1; }
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || refuse "bad commit id"
[[ "$BRANCH" == release/auto/* ]] || refuse "not a release/auto/ branch"
git fetch -q origin main "$BRANCH"
BEFORE=$(git rev-parse origin/main)
[ "$(git rev-parse "origin/$BRANCH")" = "$SHA" ] || refuse "$BRANCH has moved since its checks ran"
if [ "$BEFORE" = "$SHA" ]; then echo "nothing to release: main is already ${SHA:0:7}"; exit 0; fi
git merge-base --is-ancestor "$BEFORE" "$SHA" || refuse "${SHA:0:7} does not contain the current main ${BEFORE:0:7}"
{ echo "### Release ${SHA:0:7} from \`$BRANCH\`"; echo "- main before: \`$BEFORE\`"; echo "- files changed:"; git diff --name-only "$BEFORE" "$SHA" | sed 's/^/  - `/; s/$/`/'; } >> "$SUM"
git push origin "$SHA:refs/heads/main"                                  # fast-forward only: the ruleset forbids forcing
T="prod/$(date -u +%Y%m%d-%H%M%S)-${SHA:0:7}"; git tag "$T" "$SHA"; git push -q origin "refs/tags/$T"
echo "- released and tagged \`$T\`" >> "$SUM"
$PAGES_CMD || true
if $HEALTH_CMD "$SHA"; then echo "- live check passed" >> "$SUM"; echo "RELEASED ${SHA:0:7}"; exit 0; fi
# --- automatic rollback: a revert commit on top (never a reset), released through the same checked route ---
echo "live check FAILED"
if [[ "$BRANCH" == release/auto/rollback-* ]]; then echo "- **a rollback release failed its live check: no further automatic action**" >> "$SUM"; exit 2; fi
git fetch -q origin main
[ "$(git rev-parse origin/main)" = "$SHA" ] || { echo "- **live check failed and main moved after the release: NOT reverted automatically**" >> "$SUM"; exit 2; }
git -c user.name="PlotNua release automation" -c user.email="hello@plotnua.ie" checkout -q -B plotnua-rollback "$SHA"
git -c user.name="PlotNua release automation" -c user.email="hello@plotnua.ie" revert --no-edit "$BEFORE..$SHA" > /dev/null
[ -z "$(git diff "$BEFORE" HEAD --stat)" ] || { echo "- **revert does not restore ${BEFORE:0:7} exactly: NOT pushed**" >> "$SUM"; exit 2; }
RB="release/auto/rollback-${SHA:0:7}"
git push -q origin "HEAD:refs/heads/$RB"
$DISPATCH_CMD "$RB"
echo "- **automatic rollback requested**: \`$RB\` (content identical to \`${BEFORE:0:7}\`) goes through the gate and is released by the next run" >> "$SUM"
exit 2
