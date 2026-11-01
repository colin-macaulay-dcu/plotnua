#!/usr/bin/env bash
# PlotNua · ask for a commit to be released through the checked route (automation v1, no bypass of main's rules).
#   bash atlas-tools/release/request-release.sh <topic> [--no-wait]
# The current HEAD (committed on top of origin/main) is pushed to release/auto/<topic>-<sha7>; the Image rights gate is
# started on it (a workflow cannot start workflows by pushing, but it may dispatch one); "Release to production" then
# fast-forwards main ONLY if the gate passed on that exact commit, and verifies the live site. Waits (default 25 minutes)
# until main contains the commit. Needs GH_TOKEN with actions: write (GITHUB_TOKEN is enough).
# Exit 0 = released; 1 = not released (nothing changed on main).
set -euo pipefail
TOPIC="$1"; WAIT=1; [ "${2:-}" = "--no-wait" ] && WAIT=0
[[ "$TOPIC" =~ ^[a-z0-9][a-z0-9-]{1,60}$ ]] || { echo "REFUSED: bad topic"; exit 1; }
SHA=$(git rev-parse HEAD); BR="release/auto/$TOPIC-${SHA:0:7}"
git fetch -q origin main
git merge-base --is-ancestor origin/main "$SHA" || { echo "REFUSED: HEAD does not contain the current main"; exit 1; }
git push -q origin "HEAD:refs/heads/$BR"
gh workflow run image-rights-gate.yml --ref "$BR" -R "${GITHUB_REPOSITORY:?}"
echo "requested: ${SHA:0:7} on $BR (gate started; promotion follows only if it passes)"
[ "$WAIT" = 1 ] || exit 0
for i in $(seq 1 150); do
  sleep 10; git fetch -q origin main
  if git merge-base --is-ancestor "$SHA" origin/main; then echo "RELEASED ${SHA:0:7}"; exit 0; fi
done
echo "NOT RELEASED within 25 minutes: see the Image rights gate and Release to production runs for $BR"; exit 1
