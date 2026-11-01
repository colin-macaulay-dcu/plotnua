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
# --- automatic rollback: a revert commit on top (never a reset), only if nothing else moved main meanwhile ---
echo "live check FAILED: rolling back"
git fetch -q origin main
[ "$(git rev-parse origin/main)" = "$SHA" ] || { echo "- **live check failed and main moved after the release: NOT reverted automatically**" >> "$SUM"; exit 2; }
git -c user.name="PlotNua release automation" -c user.email="hello@plotnua.ie" checkout -q -B plotnua-rollback "$SHA"
git -c user.name="PlotNua release automation" -c user.email="hello@plotnua.ie" revert --no-edit "$BEFORE..$SHA" > /dev/null
[ -z "$(git diff "$BEFORE" HEAD --stat)" ] || { echo "- **revert does not restore ${BEFORE:0:7} exactly: NOT pushed**" >> "$SUM"; exit 2; }
git push origin "HEAD:refs/heads/main"
R=$(git rev-parse HEAD)
$PAGES_CMD || true
if $HEALTH_CMD "$R"; then echo "- **rolled back automatically**: main is \`${R:0:7}\`, identical in content to \`${BEFORE:0:7}\`; live check passed" >> "$SUM"
else echo "- **rolled back automatically** to the content of \`${BEFORE:0:7}\`, but the live check still fails" >> "$SUM"; fi
exit 2
