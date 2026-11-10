#!/usr/bin/env bash
# PlotNua · push one commit to a release branch so that the Image rights gate starts on a PUSH event (Stage 1, 10 Nov 2026).
#   bash push-release-branch.sh <commit> <release/... branch>
# Why: a push made with a workflow's built-in GITHUB_TOKEN never starts another workflow, and a gate that is dispatched
# instead is never counted by main's required "gate" check (GitHub docs: only push / pull_request / deployment-triggered
# checks satisfy a ruleset) and never starts "Release to production". So:
#   - in GitHub Actions the branch is pushed with RELEASE_PUSH_TOKEN, a 1-hour token of the "PlotNua Release" GitHub App
#     (Contents only, this repository only, no Workflows permission), minted per job from the release-automation
#     environment (main only). Without that token in Actions this REFUSES: nothing is pushed, nothing is released.
#   - anywhere else (the founder's Mac, a Claude session) it is an ordinary push with the caller's own credentials,
#     which starts the gate by itself.
# Never forces, never touches main, never prints the token. Exit 0 = pushed; 1 = refused or failed.
# Env for the local proof: RELEASE_PUSH_REMOTE (default: https://github.com/$GITHUB_REPOSITORY.git when a token is used).
set -euo pipefail
SHA="$1"; BR="$2"
[[ "$BR" == release/* ]] || { echo "REFUSED: $BR is not a release/ branch"; exit 1; }
[[ "$BR" != *..* && "$BR" =~ ^[A-Za-z0-9/._-]+$ ]] || { echo "REFUSED: bad branch name"; exit 1; }
SHA=$(git rev-parse --verify "$SHA^{commit}")
if [ -n "${RELEASE_PUSH_TOKEN:-}" ]; then
  REMOTE="${RELEASE_PUSH_REMOTE:-https://github.com/${GITHUB_REPOSITORY:?}.git}"
  AUTH=$(printf 'x-access-token:%s' "$RELEASE_PUSH_TOKEN" | base64 | tr -d '\n')
  # An empty extraheader first clears the built-in token that actions/checkout stored, so only the App token is sent.
  set +e
  OUT=$(git -c http.https://github.com/.extraheader= -c "http.https://github.com/.extraheader=AUTHORIZATION: basic $AUTH" \
      push -q "$REMOTE" "$SHA:refs/heads/$BR" 2>&1); rc=$?
  set -e
  OUT="${OUT//$RELEASE_PUSH_TOKEN/***}"; OUT="${OUT//$AUTH/***}"; [ -z "$OUT" ] || printf '%s\n' "$OUT"
  [ "$rc" = 0 ] || { echo "REFUSED: push of $BR with the release App token failed"; exit 1; }
  echo "pushed ${SHA:0:7} to $BR as the PlotNua Release App (the gate starts on this push)"
elif [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  echo "REFUSED: no RELEASE_PUSH_TOKEN in GitHub Actions. A built-in-token push would never start the gate, so nothing was pushed."
  exit 1
else
  git push -q origin "$SHA:refs/heads/$BR"
  echo "pushed ${SHA:0:7} to $BR (the gate starts on this push)"
fi
