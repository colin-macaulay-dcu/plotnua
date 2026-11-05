#!/usr/bin/env bash
# PlotNua · promote a release whose gate was started from inside a workflow (fix 5 Nov 2026).
# A gate dispatched with a workflow's built-in GitHub token never triggers "Release to production" (GitHub does not
# chain workflow_run from that token). This waits for the Image rights gate to pass on the EXACT commit, then runs
# promote.sh (fast-forward only, refused if main moved, live check, automatic rollback). If promote.sh reverts a failed
# release, the revert (release/auto/rollback-*) is released the same way: its own gate must pass on its exact commit.
# A failing rollback release is never reverted again (promote.sh). Main's ruleset still requires the gate.
#   bash promote-after-gate.sh <40-char sha> <release/auto/... branch>
# Several gate runs can exist for one commit (a push run cancelled by the dispatched one): any successful run on the exact
# commit counts as passed; while any is still running it waits; only when all finished without success is it refused.
# Env (overridable for the local proof): GATE_STATUS_CMD <branch> <sha> prints "<status>\t<conclusion>";
# GATE_POLL (seconds, default 15), GATE_TRIES (default 120 = 30 min). Exit: promote.sh's code (0 released, 1 refused,
# 2 released then rolled back or failed).
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
POLL="${GATE_POLL:-15}"; TRIES="${GATE_TRIES:-120}"
status() {
  if [ -n "${GATE_STATUS_CMD:-}" ]; then $GATE_STATUS_CMD "$1" "$2"; return; fi
  gh run list -R "${GITHUB_REPOSITORY:?}" -w image-rights-gate.yml --branch "$1" -L 5 --json headSha,status,conclusion \
    -q "[.[] | select(.headSha == \"$2\")] | if any(.status == \"completed\" and .conclusion == \"success\") then \"completed\tsuccess\" elif any(.status != \"completed\") or length == 0 then \"waiting\t\" else \"completed\t\" + (map(.conclusion) | join(\",\")) end" 2>/dev/null || true
}
wait_gate() {   # <sha> <branch>
  [[ "$1" =~ ^[0-9a-f]{40}$ ]] && [[ "$2" == release/auto/* ]] || { echo "REFUSED: unexpected release request"; return 1; }
  for i in $(seq 1 "$TRIES"); do
    case "$(status "$2" "$1")" in
      completed$'\t'success) echo "gate passed on ${1:0:7} ($2)"; return 0 ;;
      completed*) echo "REFUSED: the gate did not pass on ${1:0:7} ($2): nothing released"; return 1 ;;
    esac
    sleep "$POLL"
  done
  echo "REFUSED: the gate on ${1:0:7} did not finish in time"; return 1
}
release() {     # <sha> <branch>: wait for its gate, then promote; prints rollback_* lines to $OUT
  wait_gate "$1" "$2" || return 1
  PROMOTE_OUT="$OUT" bash "$HERE/promote.sh" "$1" "$2"
}
OUT=$(mktemp)
release "$1" "$2"; rc=$?
if [ "$rc" = 2 ]; then
  RB=$(sed -n 's/^rollback_branch=//p' "$OUT" | tail -1); RS=$(sed -n 's/^rollback_sha=//p' "$OUT" | tail -1)
  if [ -n "$RB" ] && [ -n "$RS" ]; then
    [[ "$RB" == release/auto/rollback-* ]] || { echo "REFUSED: unexpected rollback branch"; exit 2; }
    echo "releasing the automatic rollback ${RS:0:7} ($RB)"
    : > "$OUT"; release "$RS" "$RB" && echo "ROLLBACK RELEASED ${RS:0:7}" || echo "ROLLBACK NOT RELEASED: see the summary"
  fi
  [ -n "${GITHUB_OUTPUT:-}" ] && [ -n "${RB:-}" ] && printf 'rollback_branch=%s\nrollback_sha=%s\n' "$RB" "$RS" >> "$GITHUB_OUTPUT"
fi
rm -f "$OUT"; exit "$rc"
