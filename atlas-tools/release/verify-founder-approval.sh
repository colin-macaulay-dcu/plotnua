#!/usr/bin/env bash
# PlotNua · fail-closed check that a website release was approved by the founder (Stage 1, founder decision 20 Nov 2026).
# Called by .github/workflows/release-promote.yml (job "promote") from a copy of the scripts taken from main, after the
# "approval" job and BEFORE anything can reach main. It refuses unless ALL of these hold:
#   1. the website-production environment exists and is configured as approved by the founder:
#      - a required_reviewers rule naming the founder's user account;
#      - administrators may NOT bypass its protection rules (can_admins_bypass: false);
#      - deployments restricted to selected branches (custom policies, not "protected branches"), with a branch_policy rule;
#   2. its deployment branch policies are exactly one rule: the branch "main";
#   3. this exact run carries an "approved" review by the founder for website-production.
# Every answer is read from GitHub (job token first; for a public repository, GitHub's unauthenticated API as the
# fallback). Anything unreadable, malformed, incomplete or unexpected is a refusal. It never pushes, tags or changes
# anything.
#   bash verify-founder-approval.sh <run id>
# Env: REPO (owner/name), FOUNDER (GitHub login), APPROVAL_ENV (environment name), GH_CMD (the gh command, overridable
# for the local proof), PUBLIC_API (the unauthenticated fallback, overridable for the local proof).
set -uo pipefail
RUN="${1:-}"
REPO="${REPO:-${GITHUB_REPOSITORY:-colin-macaulay-dcu/plotnua}}"
FOUNDER="${FOUNDER:-colin-macaulay-dcu}"
ENVN="${APPROVAL_ENV:-website-production}"
GH_CMD="${GH_CMD:-gh}"
PUBLIC_API="${PUBLIC_API:-curl -fsS --max-time 30 -H Accept:application/vnd.github+json https://api.github.com/}"
SUM="${GITHUB_STEP_SUMMARY:-/dev/null}"
refuse() { echo "REFUSED: $*"; { echo "- **refused before release:** $*"; echo "- main and the live site are unchanged"; } >> "$SUM"; exit 1; }
[[ "$RUN" =~ ^[1-9][0-9]{0,19}$ ]] || refuse "bad run id"
[[ "$REPO" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || refuse "bad repository name"
[[ "$ENVN" =~ ^[A-Za-z0-9_.-]+$ ]] || refuse "bad environment name"

# read <api path>: the JSON body, from the job token, else the public API; non-zero (and nothing) if neither answers
read_api() {
  local out
  if out=$($GH_CMD api "$1" 2>/dev/null) && [ -n "$out" ]; then printf '%s' "$out"; return 0; fi
  # shellcheck disable=SC2086  # PUBLIC_API is a command plus base URL: word splitting is intended
  if out=$($PUBLIC_API"$1" 2>/dev/null) && [ -n "$out" ]; then printf '%s' "$out"; return 0; fi
  return 1
}

ENV_RULE='
import json, sys
founder, envn = sys.argv[1], sys.argv[2]
try:
    env = json.load(sys.stdin)
except ValueError:
    print("environment answer is not JSON"); sys.exit(1)
if not isinstance(env, dict) or str(env.get("name", "")).lower() != envn.lower():
    print("environment answer is not the %s environment" % envn); sys.exit(1)
rules = env.get("protection_rules")
if not isinstance(rules, list):
    print("environment answer has no protection rules"); sys.exit(1)
reviewers = [r for rule in rules if isinstance(rule, dict) and rule.get("type") == "required_reviewers"
             for r in (rule.get("reviewers") or []) if isinstance(r, dict)]
if not any(r.get("type") == "User" and (r.get("reviewer") or {}).get("login") == founder for r in reviewers):
    print("required reviewers do not include %s" % founder); sys.exit(1)
if env.get("can_admins_bypass") is not False:
    print("administrators may bypass the protection rules (or GitHub did not say)"); sys.exit(1)
dbp = env.get("deployment_branch_policy")
if not (isinstance(dbp, dict) and dbp.get("custom_branch_policies") is True and dbp.get("protected_branches") is False):
    print("deployments are not restricted to selected branches"); sys.exit(1)
if not any(isinstance(rule, dict) and rule.get("type") == "branch_policy" for rule in rules):
    print("no branch_policy protection rule"); sys.exit(1)
sys.exit(0)'
BRANCH_RULE='
import json, sys
try:
    d = json.load(sys.stdin)
except ValueError:
    print("branch policies answer is not JSON"); sys.exit(1)
pols = d.get("branch_policies") if isinstance(d, dict) else None
if not isinstance(pols, list) or d.get("total_count") != len(pols):
    print("branch policies answer is incomplete"); sys.exit(1)
if len(pols) != 1 or not isinstance(pols[0], dict) or pols[0].get("name") != "main" or pols[0].get("type", "branch") != "branch":
    print("deployment branches are not exactly: main"); sys.exit(1)
sys.exit(0)'
RUN_RULE='
import json, sys
founder, envn = sys.argv[1], sys.argv[2]
try:
    reviews = json.load(sys.stdin)
except ValueError:
    print("approvals answer is not JSON"); sys.exit(1)
if not isinstance(reviews, list):
    print("approvals answer is not a list"); sys.exit(1)
ok = any(isinstance(r, dict) and r.get("state") == "approved"
         and isinstance(r.get("user"), dict) and r["user"].get("login") == founder
         and isinstance(r.get("environments"), list)
         and any(isinstance(e, dict) and str(e.get("name", "")).lower() == envn.lower() for e in r["environments"])
         for r in reviews)
if not ok:
    print("no approval by %s for %s" % (founder, envn)); sys.exit(1)
sys.exit(0)'

# 1 · the environment is configured as the founder approved
ENVJSON=$(read_api "repos/$REPO/environments/$ENVN") || refuse "the $ENVN environment could not be read"
WHY=$(printf '%s' "$ENVJSON" | python3 -c "$ENV_RULE" "$FOUNDER" "$ENVN") || refuse "$ENVN is not configured as approved: ${WHY:-unreadable}"

# 2 · deployments from main only
BRJSON=$(read_api "repos/$REPO/environments/$ENVN/deployment-branch-policies?per_page=100") || refuse "the $ENVN deployment branches could not be read"
WHY=$(printf '%s' "$BRJSON" | python3 -c "$BRANCH_RULE") || refuse "$ENVN deployment branches: ${WHY:-unreadable}"

# 3 · this run was approved by the founder for this environment
APPJSON=$(read_api "repos/$REPO/actions/runs/$RUN/approvals") || refuse "the approvals of run $RUN could not be read"
WHY=$(printf '%s' "$APPJSON" | python3 -c "$RUN_RULE" "$FOUNDER" "$ENVN") || refuse "run $RUN: ${WHY:-unreadable}"

echo "founder approval confirmed: run $RUN approved by $FOUNDER for $ENVN (reviewer required, no admin bypass, main only)"
echo "- founder approval confirmed: approved by \`$FOUNDER\` for \`$ENVN\` on this run (required reviewer, no administrator bypass, deployments from main only)" >> "$SUM"
