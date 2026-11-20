#!/usr/bin/env bash
# PlotNua · fail-closed check that a website release was approved by the founder (Stage 1, founder decision 20 Nov 2026).
# Called by .github/workflows/release-promote.yml (job "promote") from a copy of the scripts taken from main, after the
# "approval" job and BEFORE anything can reach main. It refuses unless BOTH hold:
#   1. the website-production environment requires the founder as a reviewer (so an environment created without
#      protection, deleted, or left unprotected can never wave a release through);
#   2. this exact run carries an "approved" review by the founder for website-production.
# If GitHub cannot be read, it refuses. It never pushes, tags or changes anything.
#   bash verify-founder-approval.sh <run id>
# Env: REPO (owner/name), FOUNDER (GitHub login), APPROVAL_ENV (environment name), GH_CMD (the gh command, overridable
# for the local proof), PUBLIC_API (the unauthenticated fallback for reading a public repository's environment).
set -uo pipefail
RUN="${1:-}"
REPO="${REPO:-${GITHUB_REPOSITORY:-colin-macaulay-dcu/plotnua}}"
FOUNDER="${FOUNDER:-colin-macaulay-dcu}"
ENVN="${APPROVAL_ENV:-website-production}"
GH_CMD="${GH_CMD:-gh}"
PUBLIC_API="${PUBLIC_API:-curl -fsS -H Accept:application/vnd.github+json https://api.github.com}"
SUM="${GITHUB_STEP_SUMMARY:-/dev/null}"
refuse() { echo "REFUSED: $*"; { echo "- **refused before release:** $*"; echo "- main and the live site are unchanged"; } >> "$SUM"; exit 1; }
[[ "$RUN" =~ ^[0-9]+$ ]] || refuse "bad run id"

ENV_RULE='
import json, sys
founder = sys.argv[1]
try:
    env = json.load(sys.stdin)
except ValueError:
    sys.exit(1)
ok = any(rule.get("type") == "required_reviewers" and any(
            r.get("type") == "User" and (r.get("reviewer") or {}).get("login") == founder for r in (rule.get("reviewers") or []))
         for rule in (env.get("protection_rules") or []) if isinstance(rule, dict)) if isinstance(env, dict) else False
sys.exit(0 if ok else 1)'
RUN_RULE='
import json, sys
founder, envn = sys.argv[1], sys.argv[2]
try:
    reviews = json.load(sys.stdin)
except ValueError:
    sys.exit(1)
ok = isinstance(reviews, list) and any(isinstance(r, dict) and r.get("state") == "approved"
         and (r.get("user") or {}).get("login") == founder
         and any(isinstance(e, dict) and e.get("name") == envn for e in (r.get("environments") or [])) for r in reviews)
sys.exit(0 if ok else 1)'

# 1 · the environment really requires the founder (read with the job token, else the public API; neither = refuse)
ENVJSON=$($GH_CMD api "repos/$REPO/environments/$ENVN" 2>/dev/null) || ENVJSON=$($PUBLIC_API/repos/$REPO/environments/$ENVN 2>/dev/null) || refuse "the $ENVN environment could not be read"
printf '%s' "$ENVJSON" | python3 -c "$ENV_RULE" "$FOUNDER" || refuse "the $ENVN environment does not require $FOUNDER as a reviewer"

# 2 · this run was approved by the founder for this environment
APPJSON=$($GH_CMD api "repos/$REPO/actions/runs/$RUN/approvals" 2>/dev/null) || refuse "the approvals of run $RUN could not be read"
printf '%s' "$APPJSON" | python3 -c "$RUN_RULE" "$FOUNDER" "$ENVN" || refuse "run $RUN has no approval by $FOUNDER for $ENVN"

echo "founder approval confirmed: run $RUN approved by $FOUNDER for $ENVN"
echo "- founder approval confirmed: approved by \`$FOUNDER\` for \`$ENVN\` on this run" >> "$SUM"
