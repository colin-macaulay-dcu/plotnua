#!/usr/bin/env python3
"""Proof for plotnua-deploy-authority.py (A5 governance, 28 Nov 2026). Uses real commits of this repository (needs full
history) with recorded, then deliberately altered, records of how main moved. Offline except for git.
    python3 atlas-tools/release/prove-plotnua-deploy-authority.py"""
import importlib.util, json, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("auth", Path(__file__).with_name("plotnua-deploy-authority.py"))
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
def sha(r): return A.git("rev-parse", r).stdout.strip()
def upd(before, after, actor, kind="push"): return {"ref": "refs/heads/main", "before": sha(before), "after": sha(after), "actor": {"login": actor}, "activity_type": kind}
BOT, FOUNDER = "plotnua-release[bot]", "colin-macaulay-dcu"
P = []
def check(name, got, want):
    P.append(got == want); print(("PASS " if got == want else "FAIL ") + f"{name}: {got}" + ("" if got == want else f" (expected {want})"))
studio = upd("789e5544d7", "af8a884cbf", BOT)                       # genuine Studio publication, 26 Nov
release = upd("77c6d341", "f82d9a13", BOT)                            # release-promote, approved by the founder 28 Nov
merge = upd("4c75fc09", "9feb5c7b", FOUNDER, "pr_merge")              # a PR merge (code), no GitHub approval
docs = upd("f82d9a13", "f54f7b5c", FOUNDER, "pr_merge")               # PR #83: a document only
wf = upd(sys.argv[1] + "~1", sys.argv[1], BOT) if len(sys.argv) > 1 else None   # PR #74 (workflow change) as if the App pushed it
appr = [{"sha": sha("f82d9a13"), "run": 46136546374}]
check("1 Studio publication by the Release App", A.classify(studio, set())[0], "routine")
check("2 founder-approved release", A.classify(release, {a["sha"] for a in appr})[0], "approved")
check("3 the same release without the founder's approval", A.classify(release, set())[0], "material")
check("4 PR merge of code", A.classify(merge, set())[0], "material")
check("5 PR merge that changes nothing plotnua.ie serves", A.classify(docs, set())[0], "routine")
if wf: check("6 workflow change, even pushed as the Release App", A.classify(wf, set())[0], "material")
check("7 old-token push (github-actions[bot])", A.classify(upd("789e5544d7", "af8a884cbf", "github-actions[bot]"), set())[0], "material")
check("8 malformed record", A.classify({"before": "x", "after": "y", "actor": {"login": BOT}}, set())[0], "material")
chain = [release, docs]
check("9 chain approved + unpublished", A.decide(sha("77c6d341"), sha("f54f7b5c"), chain, appr)[1], "approved")
check("10 chain with a gap in the record", A.decide(sha("77c6d341"), sha("f54f7b5c"), [docs], appr)[1], "material")
check("11 HEAD does not contain LIVE", A.decide(sha("f54f7b5c"), sha("77c6d341"), chain, appr)[1], "material")
check("12 chain with one unapproved code merge", A.decide(sha("4c75fc09"), sha("9feb5c7b"), [merge], appr)[1], "material")
check("13 HEAD already live", A.decide(sha("f54f7b5c"), sha("f54f7b5c"), [], [])[1], "routine")
# 14: a deployment status forged through the API (no run of an approval workflow, or no founder review) never counts
calls = {"deps": [{"id": 1, "sha": sha("9feb5c7b")}, {"id": 2, "sha": sha("9feb5c7b")}],
         "st1": [{"state": "success", "log_url": "", "environment_url": ""}],
         "st2": [{"state": "success", "log_url": "https://github.com/x/y/actions/runs/7/job/1", "environment_url": ""}],
         "run7": {"path": ".github/workflows/other.yml", "head_branch": "main"}}
def fake(path):
    if "/deployments?" in path: return calls["deps"] if path.endswith("&page=1") else []
    if "/deployments/1/" in path: return calls["st1"]
    if "/deployments/2/" in path: return calls["st2"]
    if path.endswith("/runs/7"): return calls["run7"]
    if path.endswith("/runs/7/approvals"): return [{"state": "approved", "user": {"login": FOUNDER}, "environments": [{"name": "website-production"}]}]
    raise RuntimeError(path)
A.api = fake
check("14 forged deployment statuses are not approvals", A.fetch_approved(), [])
calls["run7"] = {"path": ".github/workflows/release-promote.yml", "head_branch": "main"}
check("15 a real approval run with the founder's review counts", [a["sha"] for a in A.fetch_approved()], [sha("9feb5c7b")])
print(f"PLOTNUA DEPLOY AUTHORITY · {sum(P)} passed, {len(P) - sum(P)} failed")
sys.exit(0 if all(P) else 1)
