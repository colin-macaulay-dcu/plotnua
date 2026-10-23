#!/usr/bin/env python3
"""PLOTNUA RELEASE · read the Image Rights Gate result for ONE exact commit.

Founder decision 23 Oct 2026: the gate runs by itself when a release/* branch is
pushed, and the release scripts read its result; nobody opens GitHub Actions or
vouches for a green tick by hand any more.

  python3 atlas-tools/release/gate-result.py --sha <40-hex> --branch release/<name> [--wait SECONDS]

Exit codes (the release scripts act on these and on nothing else):
  0  PASSED   the newest gate run for exactly this commit on exactly this branch
              completed with conclusion "success"
  2  FAILED   the newest such run completed with any other conclusion (failure,
              cancelled, timed_out, ...): a later red run outranks an earlier green one
  3  PENDING  a run exists but has not finished (after --wait, if given)
  4  NO RUN   no gate run exists for this commit on this branch (after --wait)
  5  UNREADABLE  GitHub could not be read: refuse, never assume

What it will never do:
  * accept a run on any other commit: the match is on the full 40-character SHA,
    so an old green run can never approve a new release
  * accept a run of any other workflow, or on any other branch
  * start, re-run or cancel anything (it only reads)

How it reads: the repository is public, so GitHub's REST API answers without a
token. If that is refused (e.g. the repository is made private) it uses the gh CLI
when gh is installed and logged in; otherwise it exits 5.
Testing: PN_GATE_FIXTURE=<file.json> replaces GitHub with a recorded response
(see atlas-tools/release/prove-gate-result.py).
"""
import json, os, re, shutil, subprocess, sys, time, urllib.error, urllib.request

REPO = "colin-macaulay-dcu/plotnua"
WORKFLOW = "image-rights-gate.yml"
PATH = ".github/workflows/" + WORKFLOW
EVENTS = {"push", "workflow_dispatch"}


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def fetch(sha, branch):
    fx = os.environ.get("PN_GATE_FIXTURE")
    if fx:
        with open(fx, encoding="utf-8") as f:
            data = json.load(f)
        if data == "UNREADABLE":
            raise OSError("fixture: unreadable")
        return data
    q = "repos/%s/actions/workflows/%s/runs?head_sha=%s&branch=%s&per_page=100" % (
        REPO, WORKFLOW, sha, urllib.request.quote(branch, safe=""))
    try:
        req = urllib.request.Request("https://api.github.com/" + q,
                                     headers={"Accept": "application/vnd.github+json", "User-Agent": "plotnua-release"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 404) and shutil.which("gh"):
            out = subprocess.run(["gh", "api", q], capture_output=True, text=True, timeout=60)
            if out.returncode == 0:
                return json.loads(out.stdout)
        raise OSError("GitHub API HTTP %d" % e.code)


def verdict(data, sha, branch):
    runs = [r for r in data.get("workflow_runs", [])
            if r.get("head_sha") == sha and r.get("head_branch") == branch
            and r.get("path") == PATH and r.get("event") in EVENTS]
    if not runs:
        return 4, None
    newest = max(runs, key=lambda r: (r.get("created_at", ""), r.get("id", 0)))
    if newest.get("status") != "completed":
        return 3, newest
    return (0 if newest.get("conclusion") == "success" else 2), newest


def main():
    sha, branch = arg("--sha", ""), arg("--branch", "")
    wait = int(arg("--wait", "0"))
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        print("GATE · REFUSED: --sha must be the full 40-character commit"); return 5
    if not branch.startswith("release/"):
        print("GATE · REFUSED: --branch must be a release/* branch"); return 5
    deadline = time.time() + wait
    while True:
        try:
            code, run = verdict(fetch(sha, branch), sha, branch)
        except (OSError, ValueError) as e:
            print("GATE · UNREADABLE: %s -- refuse, do not assume" % e); return 5
        if code in (0, 2) or time.time() >= deadline:
            break
        print("GATE · %s for %s on %s, checking again in 20 s"
              % ("running" if code == 3 else "no run yet", sha[:7], branch), flush=True)
        time.sleep(min(20, max(1, deadline - time.time())))
    label = {0: "PASSED", 2: "FAILED", 3: "PENDING", 4: "NO RUN"}[code]
    if run:
        print("GATE · %s · run %s · %s · event %s · commit %s · branch %s · %s"
              % (label, run.get("id"), run.get("conclusion") or run.get("status"), run.get("event"),
                 sha[:7], branch, run.get("html_url", "")))
    else:
        print("GATE · NO RUN · no Image Rights Gate run for commit %s on %s" % (sha[:7], branch))
    return code


if __name__ == "__main__":
    sys.exit(main())
