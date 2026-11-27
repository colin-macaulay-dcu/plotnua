#!/usr/bin/env bash
# PlotNua · refresh release candidates that went stale while waiting for the founder (27 Nov 2026).
#
# Why: "Release to production" fast-forwards main only to a candidate that contains the current main (promote.sh). If
# anything else reaches main while a candidate waits for approval (another release, a merged pull request), the approval
# is wasted: the founder approves, then promote refuses (run 46038279459, 27 Nov 2026). This script runs on every push to
# main (release-freshness.yml) and, for each "Release to production" run that is WAITING for approval:
#   - candidate still contains main → nothing to do;
#   - candidate is stale → the waiting run is cancelled (so it can't be approved in vain), main is merged into the
#     candidate (a normal merge commit: nothing is forced and main's newer work is kept, never overwritten), and the result
#     is pushed as a NEW release/auto/ branch. That push starts the Image rights gate on the new commit, and only if it
#     passes does a new "Release to production" run ask the founder again. Approval is never carried over.
#   - the merge conflicts → nothing is pushed; an ops alert asks for a manual rebase.
# Each case is reported in an ops-alert issue (GitHub e-mails the founder). The script never touches main.
#   bash refresh-stale-candidates.sh            (needs GH_TOKEN: actions write + issues write; RELEASE_PUSH_TOKEN in Actions)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="${GITHUB_REPOSITORY:?}"
git fetch -q origin main
MAIN=$(git rev-parse origin/main)
RUNS=$(gh run list -R "$REPO" -w release-promote.yml --status waiting --limit 20 --json databaseId,displayTitle \
  --jq '.[] | "\(.databaseId)\t\(.displayTitle)"' || true)
[ -n "$RUNS" ] || { echo "no release is waiting for approval"; exit 0; }
alert() { bash "$HERE/ops-alert.sh" "$1" "$2" || echo "ops alert not sent: $1"; }
while IFS=$'\t' read -r RUN TITLE; do
  BR="${TITLE##* · }"
  [[ "$BR" =~ ^release/auto/[A-Za-z0-9._/-]+$ && "$BR" != *..* ]] || { echo "run $RUN: candidate branch not named in its title; left alone"; continue; }
  HEAD=$(git ls-remote origin "refs/heads/$BR" | cut -f1)
  [ -n "$HEAD" ] || { echo "run $RUN: $BR no longer exists; left alone"; continue; }
  git fetch -q origin "$HEAD"
  if git merge-base --is-ancestor "$MAIN" "$HEAD"; then echo "run $RUN: ${HEAD:0:7} on $BR still contains main ${MAIN:0:7}"; continue; fi
  echo "run $RUN: ${HEAD:0:7} on $BR is stale (main is now ${MAIN:0:7}); cancelling the waiting approval"
  gh run cancel "$RUN" -R "$REPO" || echo "run $RUN could not be cancelled (it may have just finished)"
  WT=$(mktemp -d); git worktree add -q --detach "$WT" "$HEAD"
  if git -C "$WT" -c user.name="PlotNua Release" -c user.email="release@plotnua.ie" merge -q --no-edit -m "Merge main ${MAIN:0:7} into ${BR#release/auto/} (automatic refresh of a stale release candidate)" "$MAIN" 2>/dev/null; then
    NEW=$(git -C "$WT" rev-parse HEAD)
    TOPIC="${BR#release/auto/}"; TOPIC="${TOPIC%-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]}"
    NBR="release/auto/${TOPIC}-${NEW:0:7}"
    if bash "$HERE/push-release-branch.sh" "$NEW" "$NBR"; then
      alert "Release candidate refreshed: approval needed again" "Main moved to ${MAIN:0:7} while ${HEAD:0:7} ($BR) waited for approval, so that approval run ($RUN) was cancelled before it could be approved in vain. Main was merged into it (nothing forced; main's newer work kept) and pushed as ${NEW:0:7} on $NBR. The Image rights gate now runs on it; if it passes, a new Release to production run will ask for approval."
    else
      alert "Release candidate stale: refresh not pushed" "Main moved to ${MAIN:0:7} while ${HEAD:0:7} ($BR) waited; its approval run $RUN was cancelled. The refreshed commit could not be pushed: rebase and request the release again."
    fi
  else
    git -C "$WT" merge --abort 2>/dev/null || true
    alert "Release candidate stale: manual rebase needed" "Main moved to ${MAIN:0:7} while ${HEAD:0:7} ($BR) waited for approval; its approval run $RUN was cancelled. Merging main into it conflicts, so nothing was pushed: rebase it and request the release again."
  fi
  git worktree remove --force "$WT"
done <<< "$RUNS"
