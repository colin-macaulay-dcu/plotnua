#!/usr/bin/env python3
"""PROVE · the D1 test workflow's clean-up steps fail closed (founder safeguards, 24 Nov 2026). Offline.

Runs the REAL shell of two steps of .github/workflows/plotart-galleries-cloudflare-test.yml ("Databases left by earlier
runs …" and "Delete the temporary database … (fail-closed)") with stand-in `npx` (wrangler) and `gh` commands on PATH, so
every Cloudflare and GitHub answer can be scripted: a failed delete, a failed or unreadable list, a database still there,
a run still in progress, an unreadable run status. Nothing contacts Cloudflare or GitHub.
    python3 worker/plotart-studio/test/prove-cf-cleanup-steps.py"""
import json, os, re, stat, subprocess, sys, tempfile
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WF = yaml.safe_load(open(os.path.join(ROOT, ".github/workflows/plotart-galleries-cloudflare-test.yml"), encoding="utf-8"))
STEPS = {s.get("name", ""): s for s in WF["jobs"]["d1-test"]["steps"]}
LEFT = next(s for n, s in STEPS.items() if n.startswith("Databases left by earlier runs"))
CLEAN = next(s for n, s in STEPS.items() if n.startswith("Delete the temporary database"))
NPX = r'''#!/usr/bin/env bash
# stand-in for `npx --yes wrangler@… d1 …`: answers come from $STUB (one file per list call, in order)
shift 2; cmd="$1 $2"
if [ "$cmd" = "d1 list" ]; then
  n=$(cat "$STUB/n" 2>/dev/null || echo 0); n=$((n+1)); echo $n > "$STUB/n"
  f="$STUB/list$n"; [ -f "$f" ] || f="$STUB/list"
  if [ "$(cat "$f")" = "FAIL" ]; then echo "✘ [ERROR] Authentication error [code: 10000]" >&2; exit 1; fi
  cat "$f"; exit 0
fi
if [ "$cmd" = "d1 delete" ]; then echo "$3" >> "$STUB/deleted"; [ "$(cat "$STUB/delete" 2>/dev/null)" = "FAIL" ] && { echo "✘ [ERROR] A request to the Cloudflare API failed. [code: 7500]" >&2; exit 1; }; exit 0; fi
exit 3
'''
GH = r'''#!/usr/bin/env bash
id="${2##*/}"; f="$STUB/gh-$id"; [ -f "$f" ] || exit 1; cat "$f"
'''
results = []


def run(step, lists, delete="ok", gh=None, env_extra=None):
    d = tempfile.mkdtemp(prefix="cfc-")
    stub, binp = os.path.join(d, "stub"), os.path.join(d, "bin")
    os.makedirs(stub); os.makedirs(binp)
    for name, body in (("npx", NPX), ("gh", GH)):
        p = os.path.join(binp, name); open(p, "w").write(body); os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
    for i, l in enumerate(lists, 1):
        open(os.path.join(stub, "list%d" % i), "w").write(l if isinstance(l, str) else json.dumps(l))
    open(os.path.join(stub, "list"), "w").write(lists[-1] if isinstance(lists[-1], str) else json.dumps(lists[-1]))
    open(os.path.join(stub, "delete"), "w").write("FAIL" if delete == "fail" else "ok")
    for rid, st in (gh or {}).items():
        open(os.path.join(stub, "gh-%s" % rid), "w").write(json.dumps(st))
    script = step["run"].replace("${{ github.run_id }}", "100").replace("${{ github.run_attempt }}", "1").replace("sleep 10", "sleep 0")
    env = {**os.environ, "PATH": binp + ":" + os.environ["PATH"], "STUB": stub, "RUNNER_TEMP": d, "GITHUB_STEP_SUMMARY": os.path.join(d, "summary"),
           "DB_NAME": "plotart-gallery-phaseb-test-100-1", "C": "worker/plotart-studio/test/cf-test-cleanup.mjs", "GITHUB_REPOSITORY": "o/r", **(env_extra or {})}
    p = subprocess.run(["bash", "-c", script], cwd=ROOT, env=env, capture_output=True, text=True)
    deleted = open(os.path.join(stub, "deleted")).read().split() if os.path.exists(os.path.join(stub, "deleted")) else []
    summary = open(env["GITHUB_STEP_SUMMARY"]).read() if os.path.exists(env["GITHUB_STEP_SUMMARY"]) else ""
    return p.returncode, p.stdout + p.stderr, deleted, summary


def check(name, ok, detail=""):
    results.append(ok); print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  [" + detail[-300:].replace("\n", " | ") + "]"))


OURS = {"name": "plotart-gallery-phaseb-test-100-1", "uuid": "11111111-1111-1111-1111-111111111111"}
PROD = {"name": "plotart-studio", "uuid": "22222222-2222-2222-2222-222222222222"}
TEST = {"name": "plotart-checkout-test", "uuid": "33333333-3333-3333-3333-333333333333"}
print("PROVE · the D1 test workflow's clean-up steps fail closed")
# ---- the run's own clean-up ----
c, o, dl, sm = run(CLEAN, [[PROD]], env_extra={"DBID": OURS["uuid"]})
check("C1 deleted, then a readable list without it → success, reported as confirmed gone", c == 0 and "deleted and confirmed gone" in o and dl == [OURS["name"]], o)
c, o, dl, sm = run(CLEAN, [[PROD, OURS]], delete="fail", env_extra={"DBID": OURS["uuid"]})
check("C2 delete failed and the database is still listed → visible FAIL (never success)", c == 1 and "STILL EXISTS" in o and "FAIL" in sm, o)
c, o, dl, sm = run(CLEAN, [[PROD, OURS]], env_extra={"DBID": OURS["uuid"]})
check("C3 delete reported success but the database is still listed → visible FAIL", c == 1 and "STILL EXISTS" in o, o)
c, o, dl, sm = run(CLEAN, ["FAIL"], env_extra={"DBID": OURS["uuid"]})
check("C4 delete succeeded but the list call failed → FAIL: clean-up could not be verified", c == 1 and "could NOT be verified" in o and "could not be verified" in sm, o)
c, o, dl, sm = run(CLEAN, [json.dumps({"success": False, "errors": [{"code": 10000}]})], env_extra={"DBID": OURS["uuid"]})
check("C5 the list answered with an error object instead of a list → FAIL: not verified", c == 1 and "could NOT be verified" in o, o)
c, o, dl, sm = run(CLEAN, ["[{\"name\":"], env_extra={"DBID": OURS["uuid"]})
check("C6 the list was cut off (malformed) → FAIL: not verified", c == 1 and "could NOT be verified" in o, o)
c, o, dl, sm = run(CLEAN, [[PROD, {"name": "renamed", "uuid": OURS["uuid"]}]], env_extra={"DBID": OURS["uuid"]})
check("C7 the database's id is still present under another name → visible FAIL", c == 1 and "STILL EXISTS" in o, o)
c, o, dl, sm = run(CLEAN, [[PROD, OURS], [PROD]], env_extra={"DBID": OURS["uuid"]})
check("C8 listed once more just after the delete, gone on the next read → success (no false failure)", c == 0 and "confirmed gone" in o, o)
c, o, dl, sm = run(CLEAN, [[PROD]], delete="fail", env_extra={"DBID": ""})
check("C9 the create step stopped before recording an id; nothing of that name exists → success stated as 'not present'", c == 0 and "not present" in o, o)
check("C10 the clean-up only ever deletes this run's own name", all(n == OURS["name"] for n in dl))
# ---- leftovers of earlier runs ----
L = lambda n: {"name": "plotart-gallery-phaseb-test-%s" % n, "uuid": "u-%s" % n}
c, o, dl, sm = run(LEFT, ["FAIL"])
check("L1 the list cannot be read → FAIL before anything is created; nothing deleted", c == 1 and "could not be read" in o and dl == [], o)
c, o, dl, sm = run(LEFT, [[PROD, TEST, L("90-1"), L("91-1")], [PROD, TEST, L("91-1")]], gh={"90": {"status": "completed", "run_attempt": 1}, "91": {"status": "in_progress", "run_attempt": 1}})
check("L2 a finished run's leftover is deleted and confirmed gone; an active run's database is left and reported for manual review",
      c == 0 and dl == ["plotart-gallery-phaseb-test-90-1"] and "Left for manual review: plotart-gallery-phaseb-test-91-1" in o and "manual review" in sm, o)
c, o, dl, sm = run(LEFT, [[PROD, L("92-1")]], gh={})
check("L3 a run whose status cannot be read → its database is NOT deleted; reported for manual review", c == 0 and dl == [] and "status of its run could not be read" in o, o)
c, o, dl, sm = run(LEFT, [[PROD, L("93-1")]], delete="fail", gh={"93": {"status": "completed", "run_attempt": 1}})
check("L4 a finished run's leftover that cannot be deleted → FAIL before anything is created", c == 1 and "could not delete the leftover" in o, o)
c, o, dl, sm = run(LEFT, [[PROD, L("94-1")], [PROD, L("94-1")]], gh={"94": {"status": "completed", "run_attempt": 1}})
check("L5 a leftover whose deletion cannot be confirmed → FAIL before anything is created", c == 1 and "could not confirm" in o, o)
c, o, dl, sm = run(LEFT, [[PROD, L("95-1")], "FAIL"], gh={"95": {"status": "completed", "run_attempt": 1}})
check("L6 the confirming list fails after a leftover is deleted → FAIL (inconclusive is not success)", c == 1 and "could not confirm" in o, o)
c, o, dl, sm = run(LEFT, [[PROD, TEST, {"name": "plotart-gallery-phaseb-test-7", "uuid": "x"}, {"name": "something-else", "uuid": "y"}]])
check("L7 production, the checkout test database and other names are never deleted or reported", c == 0 and dl == [] and "Left for manual review" not in o, o)
c, o, dl, sm = run(LEFT, [[PROD, L("96-1")], [PROD]], gh={"96": {"status": "waiting", "run_attempt": 2}})
check("L8 an earlier attempt of a run now waiting on a later attempt → that attempt is over: deleted and confirmed", c == 0 and dl == ["plotart-gallery-phaseb-test-96-1"], o)
fail = results.count(False)
print("\nD1 TEST CLEAN-UP STEPS (fail-closed) · %d checks, %d passed, %d failed" % (len(results), len(results) - fail, fail))
sys.exit(1 if fail else 0)
