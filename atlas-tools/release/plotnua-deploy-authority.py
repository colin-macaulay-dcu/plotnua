#!/usr/bin/env python3
"""PLOTNUA PRODUCTION DEPLOY AUTHORITY (hosting migration A5, prepared 28 Nov 2026; founder governance 28 Nov 2026)

    python3 atlas-tools/release/plotnua-deploy-authority.py LIVE HEAD --fetch            (in the workflow: reads GitHub)
    python3 atlas-tools/release/plotnua-deploy-authority.py LIVE HEAD --updates U.json --approved A.json   (offline proof)

Decides whether the plotnua-site Worker may deploy HEAD to plotnua.ie WITHOUT a fresh founder approval.

LIVE is the commit the production Worker serves now (the last successful production run of plotnua-site-deploy.yml,
or the A4-verified baseline). HEAD is the commit to deploy. updates.json is GitHub's record of every update of
refs/heads/main (the repository activity API: before, after, actor, activity_type). A.json lists the commits the
founder approved: a website-production deployment with a "success" status whose run (log_url) is a run of
release-promote.yml or plotnua-site-deploy.yml on main AND carries the founder's own "approved" review for
website-production (GitHub's run approvals API). The approved commit is the one the approval job names (environment_url
.../commit/<sha>); a deployment created by hand through the API has no such run and does not count.

The founder's rule (28 Nov 2026): routine artist publications stay automatic; website design, commercial logic,
agreements, migrations, hosting, security, privacy and deployment-workflow changes keep his explicit approval.
Every update of main between LIVE and HEAD must therefore be ONE of:

  approved  the founder pressed Approve for exactly that commit: website-production in release-promote.yml, or
            plotnua-site-production in plotnua-site-deploy.yml (that workflow's own approval job);
  routine   pushed by the PlotNua Release App ("plotnua-release[bot]": its key lives only in a main-only environment,
            so no person or Claude session can push as it) AND content-only by an existing boundary:
              - PlotArt gallery or hire publication: plotart-content-boundary.py BEFORE AFTER [--hire] says OK;
              - Garden noticeboard: only atlas-tools/garden-board/approved-listings.json, borrowed-garden-board.html;
              - Idea Board: only atlas-tools/idea-board/approved-ideas.json, ideas.html, discoveries.html;
              - Atlas statistics refresh: only atlas-stats.json and index.html, index.html differing in digits only.

Anything else (a pull-request merge, a person's push, any file outside those boundaries, a .github/ change, a gap in
the record between LIVE and HEAD, HEAD not reachable from LIVE, an unreadable record) is MATERIAL: the deploy waits
for the founder's approval in plotnua-site-production. Fail closed: every doubt is "material".

Output (stdout, last line): DECISION=routine | DECISION=approved | DECISION=material, preceded by one line per update.
Exit 0 always for a decision; 2 for usage errors (treated as material by the workflow).
"""
import fnmatch, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = "plotnua-release[bot]"
GARDEN = {"atlas-tools/garden-board/approved-listings.json", "borrowed-garden-board.html"}
IDEAS = {"atlas-tools/idea-board/approved-ideas.json", "ideas.html", "discoveries.html"}
ATLAS = {"atlas-stats.json", "index.html"}
SHA = re.compile(r"^[0-9a-f]{40}$")
FOUNDER = os.environ.get("FOUNDER", "colin-macaulay-dcu")
REPO = os.environ.get("GITHUB_REPOSITORY", "colin-macaulay-dcu/plotnua")
# What decides what plotnua.ie serves besides the published files themselves: always material when changed.
SITE_CODE = ("worker/plotnua-site/", "atlas-tools/plotnua_site_build.py", "atlas-tools/release/flags.json", "_config.yml",
             ".github/")
# Where the founder approves: website releases in release-promote.yml (website-production); material plotnua.ie deploys
# in this workflow's own approval job (plotnua-site-production). Each environment counts only from its own workflow.
APPROVAL_SOURCES = {"website-production": ".github/workflows/release-promote.yml",
                    "plotnua-site-production": ".github/workflows/plotnua-site-deploy.yml"}


def api(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"GitHub API {path.split('?')[0]} unreadable")
    return json.loads(r.stdout)


def fetch_updates():
    return api(f"repos/{REPO}/activity?ref=refs/heads/main&per_page=100&time_period=quarter")


def fetch_approved():
    """Commits the founder approved, proven by the approving run's own review record."""
    out, runs = [], {}
    for env, workflow in APPROVAL_SOURCES.items():
        for page in (1, 2):
            for d in api(f"repos/{REPO}/deployments?environment={env}&per_page=100&page={page}"):
                for st in api(f"repos/{REPO}/deployments/{d['id']}/statuses?per_page=100"):
                    if st.get("state") != "success":
                        continue
                    m = re.search(r"/actions/runs/(\d+)/", st.get("log_url") or "")
                    if not m:
                        continue
                    key = (env, m.group(1))
                    if key not in runs:
                        r = api(f"repos/{REPO}/actions/runs/{m.group(1)}")
                        ok = r.get("path") == workflow and r.get("head_branch") == "main"
                        if ok:
                            ok = any(a.get("state") == "approved" and (a.get("user") or {}).get("login") == FOUNDER
                                     and any(e.get("name") == env for e in a.get("environments", []))
                                     for a in api(f"repos/{REPO}/actions/runs/{m.group(1)}/approvals"))
                        runs[key] = ok
                    if not runs[key]:
                        continue
                    u = re.search(r"/commit/([0-9a-f]{40})$", st.get("environment_url") or "")
                    a = {"sha": u.group(1) if u else d["sha"], "run": int(m.group(1)), "environment": env}
                    if a not in out:
                        out.append(a)
    return out


def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)


def changed(before, after):
    r = git("diff", "--name-status", "--no-renames", before, after)
    if r.returncode:
        return None
    out = {}
    for line in r.stdout.splitlines():
        st, _, path = line.partition("\t")
        out[path] = st
    return out


def boundary(before, after, *flags):
    """The PlotArt content-only boundary exactly as the publisher ran it: the boundary and the generators it compares
    against are taken from the published commit itself (a later redesign of a page must not turn an old, correctly
    bounded publication into a "material" change, nor the reverse)."""
    import tempfile, shutil
    tmp = tempfile.mkdtemp(prefix="pn-authority-")
    try:
        if git("worktree", "add", "--detach", "-q", tmp, after).returncode:
            return False
        r = subprocess.run([sys.executable, "atlas-tools/release/plotart-content-boundary.py", before, after, *flags],
                           capture_output=True, text=True, cwd=tmp)
        return r.returncode == 0 and "CONTENT BOUNDARY" in r.stdout and "OK" in r.stdout
    finally:
        git("worktree", "remove", "--force", tmp)
        shutil.rmtree(tmp, ignore_errors=True)


def digits_only(before, after, path):
    a, b = git("show", f"{before}:{path}"), git("show", f"{after}:{path}")
    if a.returncode or b.returncode:
        return False
    return re.sub(r"\d", "0", a.stdout) == re.sub(r"\d", "0", b.stdout)


def published(path, ref):
    """Could this path be served on plotnua.ie? Only files matching the fail-closed publication allowlist can be."""
    r = git("show", f"{ref}:worker/plotnua-site/publish-allowlist.txt")
    lines = [l.strip() for l in r.stdout.splitlines() if l.strip() and not l.startswith("#")] if not r.returncode else ["*"]
    return any(fnmatch.fnmatch(path, pat) for pat in lines)


def unpublished_only(before, after, files):
    return all(not p.startswith(SITE_CODE) and not published(p, before) and not published(p, after) for p in files)


def classify(u, approved):
    before, after, actor = u.get("before", ""), u.get("after", ""), (u.get("actor") or {}).get("login", "")
    if not (SHA.match(before) and SHA.match(after)):
        return "material", "malformed record"
    if after in approved:
        return "approved", "founder approved this exact commit in website-production"
    files = changed(before, after)
    if files is None:
        return "material", "commits not available"
    if not files:
        return "routine", "no file changes"
    if unpublished_only(before, after, files):
        return "routine", "changes nothing plotnua.ie serves (no published file, no site code)"
    if actor != APP:
        return "material", f"{u.get('activity_type', '?')} by {actor or 'unknown'} without founder approval"
    if any(p.startswith(".github/") for p in files):
        return "material", "workflow change"
    paths = set(files)
    if paths <= GARDEN and all(s == "M" for s in files.values()):
        return "routine", "Garden noticeboard publication"
    if paths <= IDEAS and all(s == "M" for s in files.values()):
        return "routine", "Idea Board publication"
    if paths <= ATLAS and all(s == "M" for s in files.values()) and all(digits_only(before, after, p) for p in paths):
        return "routine", "Atlas statistics refresh"
    # the PlotArt boundary itself refuses every path outside its own list (gallery pages, records, sitemap regions)
    if boundary(before, after) or boundary(before, after, "--hire"):
        return "routine", "PlotArt content-only publication"
    return "material", "outside every content-only boundary: " + ", ".join(sorted(paths)[:5])


def decide(live, head, updates, approvals):
    approved = {a["sha"] for a in approvals if SHA.match(a.get("sha", ""))}
    lines = []
    if not (SHA.match(live) and SHA.match(head)):
        return lines + ["bad LIVE or HEAD"], "material"
    if live == head:
        return lines + ["HEAD is already live"], "routine"
    if git("merge-base", "--is-ancestor", live, head).returncode:
        return lines + ["HEAD does not contain the live commit (history moved or LIVE unknown)"], "material"
    # walk back from HEAD through the recorded updates of main until LIVE
    by_after = {}
    for u in updates:
        if u.get("ref") in (None, "refs/heads/main") and SHA.match(u.get("after", "")):
            by_after.setdefault(u["after"], u)
    chain, cur, seen = [], head, set()
    while cur != live:
        u = by_after.get(cur)
        if u is None or cur in seen:
            return lines + [f"no record of how main reached {cur[:12]}: gap in the activity record"], "material"
        seen.add(cur)
        chain.append(u)
        cur = u["before"]
        if git("merge-base", "--is-ancestor", live, cur).returncode and cur != live:
            return lines + [f"update before {cur[:12]} is not after the live commit"], "material"
    decision = "routine"
    for u in reversed(chain):
        kind, why = classify(u, approved)
        lines.append(f"{u['after'][:12]}  {kind:8}  {why}")
        if kind == "material":
            decision = "material"
        elif kind == "approved" and decision == "routine":
            decision = "approved"
    return lines, decision


def main(argv):
    if len(argv) < 4 or not ("--fetch" in argv or "--updates" in argv):
        print(__doc__); print("DECISION=material"); return 2
    live, head = argv[1], argv[2]
    try:
        if "--fetch" in argv:
            updates, approvals = fetch_updates(), fetch_approved()
        else:
            updates = json.loads(Path(argv[argv.index("--updates") + 1]).read_text())
            approvals = json.loads(Path(argv[argv.index("--approved") + 1]).read_text()) if "--approved" in argv else []
    except Exception as e:  # unreadable record: fail closed
        print(f"record unreadable ({e})"); print("DECISION=material"); return 0
    lines, decision = decide(live, head, updates, approvals)
    for l in lines:
        print(l)
    print(f"DECISION={decision}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
