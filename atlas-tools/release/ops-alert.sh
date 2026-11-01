#!/usr/bin/env bash
# PlotNua · operations alert (automation v1). Opens one GitHub issue labelled "ops-alert" per title, or comments on it
# if it is already open, so a repeating failure does not create a flood. GitHub e-mails the repository owner.
#   bash atlas-tools/release/ops-alert.sh "<title>" "<body>"     (needs GH_TOKEN with issues: write)
set -euo pipefail
TITLE="$1"; BODY="$2"
gh label create ops-alert --color B60205 --description "Automatic operations alert" -R "$GITHUB_REPOSITORY" 2>/dev/null || true
N=$(gh issue list -R "$GITHUB_REPOSITORY" --label ops-alert --state open --search "in:title \"$TITLE\"" --json number --jq '.[0].number // empty')
if [ -n "$N" ]; then gh issue comment "$N" -R "$GITHUB_REPOSITORY" --body "$BODY"; else gh issue create -R "$GITHUB_REPOSITORY" --label ops-alert --title "$TITLE" --body "$BODY"; fi
