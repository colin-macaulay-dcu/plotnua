#!/usr/bin/env bash
# PlotNua · show a website release to the founder BEFORE approval (Stage 1, founder decision 20 Nov 2026).
# Called by .github/workflows/release-promote.yml (job "preview") from a copy of the scripts taken from main.
#   bash release-preview.sh <40-char sha> <release branch>
# Writes, to the run summary: the commit, its branch, the main it builds on and every changed file. Writes the job
# output release=true only when the commit can actually be released (it contains the current main and adds something
# to it). It never pushes, tags or changes anything.
# Exit 0 = shown (release=true) or nothing to release (release=false); 1 = refused: the commit can never be released
# (bad id, not a release branch, the branch has moved, or main has moved past it), so no approval is requested.
set -euo pipefail
SHA="$1"; BRANCH="$2"
SUM="${GITHUB_STEP_SUMMARY:-/dev/null}"; OUT="${GITHUB_OUTPUT:-/dev/null}"
REPO_URL="${REPO_URL:-https://github.com/${GITHUB_REPOSITORY:-colin-macaulay-dcu/plotnua}}"
refuse() { echo "REFUSED: $*"; { echo "### Website release not offered for approval"; echo "- **refused:** $*"; echo "- production is unchanged"; } >> "$SUM"; echo "release=false" >> "$OUT"; exit 1; }
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || refuse "bad commit id"
[[ "$BRANCH" == release/auto/* ]] || refuse "not a release/auto/ branch"
git fetch -q origin main "$BRANCH"
MAIN=$(git rev-parse origin/main)
[ "$(git rev-parse "origin/$BRANCH")" = "$SHA" ] || refuse "$BRANCH has moved since its checks ran"
if git merge-base --is-ancestor "$SHA" "$MAIN"; then
  echo "nothing to release: main ${MAIN:0:7} already contains ${SHA:0:7}"
  { echo "### Nothing to release"; echo "- main \`${MAIN:0:7}\` already contains \`${SHA:0:7}\`: no approval is needed and nothing will change"; } >> "$SUM"
  echo "release=false" >> "$OUT"; exit 0
fi
git merge-base --is-ancestor "$MAIN" "$SHA" || refuse "${SHA:0:7} does not contain the current main ${MAIN:0:7} (main has moved on): request the release again from the current main"
# Routine Atlas statistics refresh (founder policy, 20 Nov 2026): released automatically by the separate promote-atlas
# job, ONLY if verify-atlas-refresh.sh (from main) says it is exactly that. Anything else, including any doubt, is
# offered to the founder for approval like every other release.
if [ -n "${ACTOR:-}" ] && ATLAS_WHY=$(bash "$(cd "$(dirname "$0")" && pwd)/verify-atlas-refresh.sh" "$SHA" "$BRANCH" "$ACTOR" "${EVENT:-}" 2>&1); then
  { echo "## Routine Atlas statistics refresh: released without approval (founder policy, 20 Nov 2026)"
    echo "- Commit [\`${SHA:0:7}\`]($REPO_URL/commit/$SHA) on \`$BRANCH\`, pushed by \`$ACTOR\`, on top of production \`${MAIN:0:7}\`"
    echo "- ${ATLAS_WHY}"
    echo "- Only index.html's six Atlas figures and atlas-stats.json change; the promote-atlas job checks this again before release."; } >> "$SUM"
  echo "release=false" >> "$OUT"; echo "atlas=true" >> "$OUT"
  echo "routine Atlas refresh: ${SHA:0:7} goes to promote-atlas (no approval)"; exit 0
fi
[ -z "${ACTOR:-}" ] || echo "not a routine Atlas refresh: ${ATLAS_WHY:-}"
N=$(git diff --name-only "$MAIN" "$SHA" | wc -l | tr -d ' ')
{
  echo "## Website release waiting for founder approval"
  echo ""
  echo "| | |"
  echo "|---|---|"
  echo "| Commit | [\`${SHA:0:7}\`]($REPO_URL/commit/$SHA) \`$SHA\` |"
  echo "| Title | $(git log -1 --format=%s "$SHA" | sed 's/|/\\|/g') |"
  echo "| Release branch | \`$BRANCH\` |"
  echo "| Builds on production (main) | \`${MAIN:0:7}\` |"
  echo "| Commits added | $(git rev-list --count "$MAIN..$SHA") |"
  echo "| Files changed | $N |"
  echo ""
  echo "Full comparison: $REPO_URL/compare/${MAIN:0:12}...${SHA:0:12}"
  echo ""
  echo "### Files changed"
  # shellcheck disable=SC2016  # literal backticks (Markdown code), nothing to expand
  git diff --stat=200 "$MAIN" "$SHA" | sed '$d' | sed 's/^ */- `/; s/ *|/` |/'
  echo ""
  echo "**Approve** on this run's *Review deployments* (environment \`website-production\`) to release exactly this commit."
  echo "**Reject** to stop it: main and the live site stay exactly as they are."
  echo "If production (main) changes before you approve, this release is refused, never merged over the newer work."
} >> "$SUM"
echo "release=true" >> "$OUT"
echo "offered for approval: ${SHA:0:7} on $BRANCH ($N file(s) changed against main ${MAIN:0:7})"
