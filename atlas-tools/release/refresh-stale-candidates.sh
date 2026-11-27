#!/usr/bin/env bash
# PlotNua · refresh release candidates that went stale while waiting for the founder (27 Nov 2026).
#
# Why: "Release to production" fast-forwards main only to a candidate that contains the current main (promote.sh). If
# anything else reaches main while a candidate waits for approval (another release, a merged pull request), the approval
# is wasted: the founder approves, then promote refuses (run 46038279459, 27 Nov 2026). On every push to main
# (release-freshness.yml) this runs in two separate jobs, so no job holds both powers:
#
#   --cancel   (job "stale": actions: write, NO App key) For each "Release to production" run WAITING for approval whose
#              candidate no longer contains main: cancel it, so it can't be approved in vain. Writes the stale candidate
#              branches to $GITHUB_OUTPUT (stale=...). It never pushes and never dispatches anything.
#   --refresh BRANCH...  (job "refresh": the PlotNua Release App, contents only, NO actions: write) For each stale
#              candidate: merge main into it (an ordinary merge commit: nothing forced; main and the old branch are never
#              changed) and push the result as a NEW release/auto/ branch. That push starts the Image rights gate on the
#              new commit; only if it passes does a new "Release to production" run ask the founder again. An approval
#              is never carried over.
#
# No loops: a candidate is refreshed at most MAX_REFRESH times (generation -rf1, -rf2, ... in its branch name); after
# that, or on a merge conflict, or when a newer candidate for the same topic already contains main, nothing is pushed and
# an ops alert explains why. This script only runs on pushes to main and never pushes main, so its own pushes can't
# start it again.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="${GITHUB_REPOSITORY:?}"; MAX_REFRESH="${MAX_REFRESH:-3}"
MODE="${1:-}"; shift || true
git fetch -q origin main
MAIN=$(git rev-parse origin/main)
alert() { bash "$HERE/ops-alert.sh" "$1" "$2" || echo "ops alert not sent: $1"; }
valid() { [[ "$1" =~ ^release/auto/[A-Za-z0-9._/-]+$ && "$1" != *..* ]]; }
stem() { local t="${1#release/auto/}"; echo "${t%-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]}"; }
topic_of() { local t; t=$(stem "$1"); echo "${t%-rf[0-9]*}"; }
gen_of() { local t; t=$(stem "$1"); if [[ "$t" =~ -rf([0-9]+)$ ]]; then echo "${BASH_REMATCH[1]}"; else echo 0; fi; }

case "$MODE" in
--cancel)
  RUNS=$(gh run list -R "$REPO" -w release-promote.yml --status waiting --limit 20 --json databaseId,displayTitle \
    --jq '.[] | "\(.databaseId)\t\(.displayTitle)"' || true)
  STALE=()
  while IFS=$'\t' read -r RUN TITLE; do
    [ -n "${RUN:-}" ] || continue
    BR="${TITLE##* · }"
    valid "$BR" || { echo "run $RUN: candidate branch not named in its title; left alone"; continue; }
    HEAD=$(git ls-remote origin "refs/heads/$BR" | cut -f1)
    [ -n "$HEAD" ] || { echo "run $RUN: $BR no longer exists; left alone"; continue; }
    git fetch -q origin "$HEAD"
    if git merge-base --is-ancestor "$MAIN" "$HEAD"; then echo "run $RUN: ${HEAD:0:7} on $BR still contains main ${MAIN:0:7}"; continue; fi
    echo "run $RUN: ${HEAD:0:7} on $BR is stale (main is now ${MAIN:0:7}); cancelling its waiting approval"
    gh run cancel "$RUN" -R "$REPO" || echo "run $RUN could not be cancelled (it may have just finished)"
    STALE+=("$BR")
  done <<< "$RUNS"
  echo "stale=${STALE[*]:-}" >> "${GITHUB_OUTPUT:-/dev/null}"
  echo "stale candidates: ${STALE[*]:-none}" ;;
--refresh)
  for BR in "$@"; do
    valid "$BR" || { echo "skipping $BR: not a release/auto/ branch"; continue; }
    HEAD=$(git ls-remote origin "refs/heads/$BR" | cut -f1); [ -n "$HEAD" ] || continue
    git fetch -q origin "$HEAD"
    if git merge-base --is-ancestor "$MAIN" "$HEAD"; then echo "$BR already contains main"; continue; fi
    TOPIC=$(topic_of "$BR"); GEN=$(gen_of "$BR")
    # a newer candidate for the same topic that already contains main (e.g. re-requested by hand): nothing to do
    NEWER=""
    while read -r SHA REF; do
      [ -n "${SHA:-}" ] || continue
      [ "$(topic_of "${REF#refs/heads/}")" = "$TOPIC" ] || continue
      if git fetch -q origin "$SHA" && git merge-base --is-ancestor "$MAIN" "$SHA"; then NEWER="${REF#refs/heads/}"; fi
    done < <(git ls-remote origin "refs/heads/release/auto/${TOPIC}-*")
    if [ -n "$NEWER" ]; then echo "$BR: $NEWER already contains main; not refreshed"; continue; fi
    if [ "$GEN" -ge "$MAX_REFRESH" ]; then
      alert "Release candidate stale: refresh limit reached" "${HEAD:0:7} ($BR) went stale again after $GEN automatic refreshes, so it was not refreshed again (this stops a busy main from looping). Its waiting approval was cancelled. Request the release again when main is quiet."
      continue
    fi
    WT=$(mktemp -d); git worktree add -q --detach "$WT" "$HEAD"
    if git -C "$WT" -c user.name="PlotNua Release" -c user.email="release@plotnua.ie" merge -q --no-edit \
        -m "Merge main ${MAIN:0:7} into ${TOPIC} (automatic refresh $((GEN + 1)) of a stale release candidate)" "$MAIN" 2>/dev/null; then
      NEW=$(git -C "$WT" rev-parse HEAD); NBR="release/auto/${TOPIC}-rf$((GEN + 1))-${NEW:0:7}"
      if bash "$HERE/push-release-branch.sh" "$NEW" "$NBR"; then
        alert "Release candidate refreshed: approval needed again" "Main moved to ${MAIN:0:7} while ${HEAD:0:7} ($BR) waited for approval, so that approval was cancelled before it could be approved in vain. Main was merged into it (nothing forced; main's newer work kept) and pushed as ${NEW:0:7} on $NBR. The Image rights gate now runs on it; if it passes, a new Release to production run will ask for approval."
      else
        alert "Release candidate stale: refresh not pushed" "Main moved to ${MAIN:0:7} while ${HEAD:0:7} ($BR) waited; its approval was cancelled. The refreshed commit could not be pushed (for example because main changed workflow files, which the release App may not push): rebase it and request the release again."
      fi
    else
      git -C "$WT" merge --abort 2>/dev/null || true
      alert "Release candidate stale: manual rebase needed" "Main moved to ${MAIN:0:7} while ${HEAD:0:7} ($BR) waited for approval; its approval was cancelled. Merging main into it conflicts, so nothing was pushed: rebase it and request the release again."
    fi
    git worktree remove --force "$WT"
  done ;;
*) echo "usage: refresh-stale-candidates.sh --cancel | --refresh BRANCH..."; exit 2 ;;
esac
