#!/usr/bin/env python3
"""PLOTNUA · THE BORROWED GARDEN NOTICEBOARD PIPELINE · PlotArt Studio -> plotnua.ie (release candidate, 4 Nov 2026).
Runs on a checkout of main. NOT ACTIVE: its GitHub workflow runs only when the repository variable
GARDEN_PUBLISH_ENABLED (or flags.json garden_publish_enabled) is "true", which the founder sets at the noticeboard launch.

    python3 atlas-tools/plotnua-garden-publish.py --studio URL --token PIPELINE_TOKEN [--push | --simulate]

  1. takes the listings the founder has approved and that have not expired from the Studio (/api/pipeline/garden:
     public fields only: reference, side, county, general area, type of space, availability, approved wording, an
     approved photograph if any, date posted and expiry). Rejected, removed and expired listings are never in it;
  2. writes them to atlas-tools/garden-board/approved-listings.json and rebuilds borrowed-garden-board.html
     (atlas-tools/build-garden-board.py, which checks every listing again);
  3. does nothing when nothing changed;
  4. commits, then refuses unless ONLY those two files changed and the page and site guards pass;
  5. --push: pushes an audit branch content/garden-<sha> and releases through the gate (automation v1).
     --simulate (local tests only, a local Studio): stops before pushing. Any failure: the commit is dropped.
Demonstration listings exist only in local test databases: --simulate refuses any Studio that is not on this machine,
and --push refuses one that is.
"""
import json, os, re, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
STUDIO, TOKEN = arg("--studio"), arg("--token")
PUSH, SIMULATE = "--push" in sys.argv, "--simulate" in sys.argv
if not (STUDIO and TOKEN) or PUSH == SIMULATE:
    sys.exit(__doc__)
LOCAL = re.match(r"^http://(127\.0\.0\.1|localhost):\d+/?$", STUDIO)
if SIMULATE and not LOCAL:
    sys.exit("REFUSED: --simulate is for local tests only (it reports success without pushing)")
if PUSH and LOCAL:
    sys.exit("REFUSED: a local Studio holds demonstration listings only; it is never published")
SNAP = os.path.join(HERE, "garden-board", "approved-listings.json")
PAGE = "borrowed-garden-board.html"
ALLOWED = {"atlas-tools/garden-board/approved-listings.json", PAGE}
GUARDS = ["python3 atlas-tools/build-garden-board.py --check", "python3 atlas-tools/build-identity-stage1.py --check",
          "python3 atlas-tools/prove-global-header.py"]
FIELDS = {"ref", "kind", "county", "area", "space_type", "availability", "text", "photo", "posted", "expires"}
HEADERS = {"Authorization": "Bearer " + TOKEN, "User-Agent": "PlotArt-content-pipeline/1.0 (+https://plotnua.ie)"}
if os.environ.get("STUDIO_ACCESS_CLIENT_ID") and os.environ.get("STUDIO_ACCESS_CLIENT_SECRET"):
    HEADERS["CF-Access-Client-Id"] = os.environ["STUDIO_ACCESS_CLIENT_ID"]
    HEADERS["CF-Access-Client-Secret"] = os.environ["STUDIO_ACCESS_CLIENT_SECRET"]


def git(*a, check=True):
    r = subprocess.run(("git",) + a, cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError("git %s: %s" % (" ".join(a), r.stderr.strip()))
    return r.stdout.strip()


def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def main():
    if git("status", "--porcelain"):
        sys.exit("REFUSED: the checkout is not clean")
    req = urllib.request.Request(STUDIO.rstrip("/") + "/api/pipeline/garden", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        listings = json.loads(r.read())["listings"]
    for l in listings:
        if set(l) - FIELDS:
            print("GARDEN NOTICEBOARD · FAILED · the Studio sent fields that are not public: %s" % sorted(set(l) - FIELDS)); return 1
        if l.get("photo") is None:
            l.pop("photo", None)
    cur = json.load(open(SNAP, encoding="utf-8"))
    if cur.get("listings") == listings and run("python3 atlas-tools/build-garden-board.py --check")[0]:
        print("GARDEN NOTICEBOARD · nothing to publish (%d listings, unchanged)" % len(listings)); return 0
    base = git("rev-parse", "HEAD")
    cur["listings"] = listings
    with open(SNAP, "w", encoding="utf-8") as f:
        json.dump(cur, f, ensure_ascii=False, indent=2); f.write("\n")
    ok, out = run("python3 atlas-tools/build-garden-board.py")
    why = None if ok else "builder refused: " + out[-400:]
    if why is None:
        git("add", "--", *sorted(ALLOWED))
        git("-c", "user.name=PlotNua content pipeline", "-c", "user.email=hello@plotnua.ie", "commit", "-q", "-m",
            "Borrowed Garden noticeboard content: %d listings (founder's approvals in PlotArt Studio)" % len(listings))
        changed = set(git("diff", "--name-only", base, "HEAD").splitlines())
        if changed - ALLOWED:
            why = "files outside the noticeboard changed: %s" % sorted(changed - ALLOWED)
    for guard in GUARDS:
        if why is None:
            ok, out = run(guard)
            why = None if ok else "%s refused: %s" % (guard, out[-400:])
    if why is None and PUSH:
        sha = git("rev-parse", "--short", "HEAD")
        ok1, o1 = run("git push origin HEAD:refs/heads/content/garden-%s" % sha)
        ok2, o2 = run("bash atlas-tools/release/request-release.sh garden")  # automation v1: main only moves after the gate passes
        if not (ok1 and ok2):
            why = "push refused (main moved or no permission): " + (o1 + " " + o2)[-300:]
    if why:
        subprocess.run(["git", "reset", "-q", "--hard", base], cwd=ROOT)
        print("GARDEN NOTICEBOARD · FAILED · %s" % why[:500]); return 1
    print("GARDEN NOTICEBOARD · %d listings · %s %s" % (len(listings), "published" if PUSH else "verified (simulated)", git("rev-parse", "--short", "HEAD")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
