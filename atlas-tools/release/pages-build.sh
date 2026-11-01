#!/usr/bin/env bash
# PlotNua · request the GitHub Pages build for the current main and wait until it has been built (automation v1).
# Pushes made with the workflow token do not start a Pages build by themselves (GitHub documentation), so the release
# and content workflows request one. Needs GH_TOKEN with pages: write.
set -euo pipefail
R="$GITHUB_REPOSITORY"
WANT=$(git ls-remote origin refs/heads/main | cut -f1)
curl -fsS -X POST -H "Authorization: Bearer $GH_TOKEN" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/$R/pages/builds" > /dev/null
for i in $(seq 1 60); do
  sleep 10
  J=$(curl -fsS -H "Authorization: Bearer $GH_TOKEN" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/$R/pages/builds/latest" || echo '{}')
  S=$(echo "$J" | python3 -c 'import json,sys; j=json.load(sys.stdin); print(j.get("status",""), j.get("commit",""))')
  set -- $S
  if [ "${2:-}" = "$WANT" ] && [ "$1" = "built" ]; then echo "Pages built ${WANT:0:7}"; exit 0; fi
  if [ "${2:-}" = "$WANT" ] && [ "$1" = "errored" ]; then echo "FAIL  the Pages build errored"; exit 1; fi
done
echo "WARNING  could not confirm the Pages build for ${WANT:0:7}; the live check that follows decides"; exit 0
