#!/usr/bin/env python3
"""PLOTNUA RELEASE · proof that gate-result.py approves exactly one thing.

Feeds recorded GitHub responses to atlas-tools/release/gate-result.py and requires
the right exit code for every case. Above all: a green run on ANY other commit,
branch or workflow must never read as approval. No network.
Usage: python3 atlas-tools/release/prove-gate-result.py
"""
import json, os, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHA = "d9db752c72f1b6b0dda4240e17f957e89074cad6"
OLD = "da78d1055d4f5dcb50b10c2239674fad14822bec"
BR = "release/example-2026-10-23"
PATH = ".github/workflows/image-rights-gate.yml"


def run(i, sha=SHA, br=BR, event="push", status="completed", conclusion="success", path=PATH, t="2026-10-23T13:00:00Z"):
    return {"id": i, "head_sha": sha, "head_branch": br, "event": event, "status": status,
            "conclusion": conclusion if status == "completed" else None, "path": path, "created_at": t,
            "html_url": "https://github.com/x/y/actions/runs/%d" % i}


CASES = [
    ("green run on exactly this commit and branch", [run(1)], 0),
    ("manual (dispatch) green run on exactly this commit", [run(1, event="workflow_dispatch")], 0),
    ("OLD green run on another commit only", [run(1, sha=OLD)], 4),
    ("green run on this commit but another branch (main)", [run(1, br="main")], 4),
    ("green run on this commit but another release branch", [run(1, br="release/other")], 4),
    ("green run of another workflow on this commit", [run(1, path=".github/workflows/atlas-stats.yml")], 4),
    ("green pull_request run on this commit", [run(1, event="pull_request")], 4),
    ("no runs at all", [], 4),
    ("newest run failed after an older green one", [run(1, t="2026-10-23T12:00:00Z"), run(2, conclusion="failure", t="2026-10-23T13:00:00Z")], 2),
    ("newest run green after an older failure", [run(1, conclusion="failure", t="2026-10-23T12:00:00Z"), run(2, t="2026-10-23T13:00:00Z")], 0),
    ("newest run cancelled", [run(1, t="2026-10-23T12:00:00Z"), run(2, conclusion="cancelled", t="2026-10-23T13:00:00Z")], 2),
    ("newest run timed out", [run(1, conclusion="timed_out")], 2),
    ("run still in progress", [run(1, status="in_progress")], 3),
    ("run queued, older green present", [run(1, t="2026-10-23T12:00:00Z"), run(2, status="queued", t="2026-10-23T13:00:00Z")], 3),
    ("old green on another commit + this commit failed", [run(1, sha=OLD), run(2, conclusion="failure")], 2),
    ("GitHub unreadable", "UNREADABLE", 5),
]
ARGS = [
    ("short commit hash refused", ["--sha", SHA[:7], "--branch", BR], 5),
    ("non-release branch refused", ["--sha", SHA, "--branch", "main"], 5),
]


def main():
    bad = 0
    with tempfile.TemporaryDirectory() as d:
        fx = Path(d) / "fx.json"
        tests = [(n, data, ["--sha", SHA, "--branch", BR], want) for n, data, want in CASES] + \
                [(n, {"workflow_runs": [run(1)]}, a, want) for n, a, want in ARGS]
        for name, data, a, want in tests:
            fx.write_text(json.dumps(data if isinstance(data, str) else ({"workflow_runs": data} if isinstance(data, list) else data)))
            r = subprocess.run([sys.executable, str(HERE / "gate-result.py")] + a, capture_output=True, text=True,
                               env={**os.environ, "PN_GATE_FIXTURE": str(fx)})
            ok = r.returncode == want
            bad += not ok
            print("%s  %-56s exit %d (want %d)" % ("ok    " if ok else "WRONG ", name, r.returncode, want))
    total = len(CASES) + len(ARGS)
    if bad:
        print("GATE-RESULT PROOF · FAILED — %d of %d cases wrong" % (bad, total)); return 2
    print("GATE-RESULT PROOF · OK — %d cases, only a green run on the exact commit and release branch approves" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
