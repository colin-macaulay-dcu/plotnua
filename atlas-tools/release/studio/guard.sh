#!/usr/bin/env bash
# PlotArt Studio deployment guard (31 Oct 2026). Refuses anything except a full commit ID that is already on main
# (main only moves with the founder's explicit approval) and that contains the Studio release currently live.
#   bash atlas-tools/release/studio/guard.sh <40-char commit> [--allow-unchanged]
# Prints only commit IDs and file paths. Exit 0 = may proceed to the founder's approval step.
set -euo pipefail
COMMIT="${1:-}"; ALLOW_UNCHANGED="${2:-}"
W=worker/plotart-studio
BASELINE=60155036e246d026f06d6944cd17ac881ccd8728   # Studio release live since 31 Oct 2026 (Worker a2169449), until the first workflow deployment tags studio-live
fail() { echo "REFUSED: $*"; exit 1; }
[[ "$COMMIT" =~ ^[0-9a-f]{40}$ ]] || fail "give the full 40-character commit ID"
git cat-file -e "$COMMIT^{commit}" 2>/dev/null || fail "commit $COMMIT is not in this repository"
git fetch -q origin main
git merge-base --is-ancestor "$COMMIT" origin/main || fail "commit $COMMIT is not on main (main only moves with the founder's approval)"
LIVE=$(git rev-parse -q --verify "refs/tags/studio-live^{commit}" || true)
[ -n "$LIVE" ] || LIVE=$(git rev-parse -q --verify "$BASELINE^{commit}" || true)
[ -n "$LIVE" ] || fail "the record of the live Studio release is missing"
git merge-base --is-ancestor "$LIVE" "$COMMIT" || fail "commit $COMMIT does not contain the live Studio release ${LIVE:0:7} (this would roll back)"
CHANGED=$(git diff --name-only "$LIVE" "$COMMIT" -- "$W")
if [ -z "$CHANGED" ] && [ "$ALLOW_UNCHANGED" != "--allow-unchanged" ]; then fail "nothing in the Studio changes between the live release ${LIVE:0:7} and $COMMIT"; fi
# the committed bundle must be exactly what the committed sources build (no hand-edited or stale src/assets.js)
TMP=$(mktemp -d); git archive "$COMMIT" "$W" assets/brand plotart/assets | tar -x -C "$TMP"
( cd "$TMP/$W" && node build-assets.mjs >/dev/null )
git show "$COMMIT:$W/src/assets.js" | cmp -s - "$TMP/$W/src/assets.js" || fail "the committed src/assets.js does not match its sources"
rm -rf "$TMP"
{
  echo "### PlotArt Studio · release check"
  echo "- Commit to deploy: \`$COMMIT\` (on main)"
  echo "- Live Studio release: \`$LIVE\`"
  echo "- Studio files changed:"; [ -n "$CHANGED" ] && echo "$CHANGED" | sed 's/^/  - `/; s/$/`/' || echo "  - none"
} | tee -a "${GITHUB_STEP_SUMMARY:-/dev/null}"
echo "GUARD OK"
