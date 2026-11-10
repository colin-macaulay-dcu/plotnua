#!/usr/bin/env python3
"""PLOTNUA IDEA BOARD PIPELINE · PlotArt Studio -> plotnua.ie (Phase 1, 1 Nov 2026). Runs on a checkout of main.
NOT ACTIVE: its GitHub workflow runs only when the repository variable IDEAS_PUBLISH_ENABLED is "true", which the
founder sets only after separately authorising the Idea Board launch.

    python3 atlas-tools/plotnua-ideas-publish.py --studio URL --token PIPELINE_TOKEN [--push | --simulate]

  1. takes the ideas the founder has approved from the Studio (/api/pipeline/ideas: public fields only: the approved
     wording, area, county only where the person chose to show it, month and year, and any "Now a Discovery" link);
  2. writes them to atlas-tools/idea-board/approved-ideas.json and rebuilds ideas.html and the Library's Idea Board
     card (atlas-tools/build-idea-board.py, which checks every idea again);
  3. does nothing when nothing changed;
  4. commits, then refuses unless ONLY those three files changed, the Library outside the marked card block is
     byte-identical, and the Idea Board proof passes;
  5. --push: pushes an audit branch content/ideas-<sha> and fast-forwards main (never forced; refused if main moved).
     --simulate (local tests only): stops before pushing. Any failure: the commit is dropped.
"""
import json, os, re, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
STUDIO, TOKEN = arg("--studio"), arg("--token")
PUSH, SIMULATE = "--push" in sys.argv, "--simulate" in sys.argv
if not (STUDIO and TOKEN) or PUSH == SIMULATE:
    sys.exit(__doc__)
if SIMULATE and not re.match(r"^http://(127\.0\.0\.1|localhost):\d+/?$", STUDIO):
    sys.exit("REFUSED: --simulate is for local tests only (it reports success without pushing)")
SNAP = os.path.join(HERE, "idea-board", "approved-ideas.json")
ALLOWED = {"atlas-tools/idea-board/approved-ideas.json", "ideas.html", "discoveries.html"}
CARD = re.compile(r"[ \t]*<!-- PLOTNUA IDEA BOARD CARD · BEGIN.*?<!-- PLOTNUA IDEA BOARD CARD · END -->\n", re.S)
CSS = re.compile(r"/\* PLOTNUA IDEA BOARD CARD v1 · BEGIN.*?/\* PLOTNUA IDEA BOARD CARD v1 · END \*/\n\n", re.S)
# The Idea Board proof, and every governed layer that reads the Library or the page.
GUARDS = ["python3 atlas-tools/prove-idea-board.py", "python3 atlas-tools/build-library-card-labels.py --check",
          "python3 atlas-tools/build-library-card-webp.py --check", "python3 atlas-tools/build-discovery-library-images.py --check",
          "python3 atlas-tools/build-identity-stage1.py --check", "python3 atlas-tools/prove-global-header.py"]
FIELDS = {"text", "area", "county", "month", "became_discovery"}

# The same Cloudflare Access service token and User-Agent the PlotArt pipeline uses (see plotart-gallery-publish.py).
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


def boundary(base):
    """Only the snapshot, the board page and the Library's marked card block may change."""
    changed = set(git("diff", "--name-only", base, "HEAD").splitlines())
    if changed - ALLOWED:
        return "files outside the Idea Board changed: %s" % sorted(changed - ALLOWED)
    old = subprocess.run(["git", "show", "%s:discoveries.html" % base], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    new = open(os.path.join(ROOT, "discoveries.html"), encoding="utf-8").read()
    strip = lambda t: CSS.sub("", CARD.sub("", t))
    teaser = re.compile(r'[ \t]*<div class="lib-card lib-next">.*?</div>\n', re.S)
    if teaser.sub("", strip(old)) != teaser.sub("", strip(new)):
        return "the Discovery Library changed outside the Idea Board card"
    return None


def main():
    if git("status", "--porcelain"):
        sys.exit("REFUSED: the checkout is not clean")
    req = urllib.request.Request(STUDIO.rstrip("/") + "/api/pipeline/ideas", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        ideas = json.loads(r.read())["ideas"]
    for i in ideas:
        if set(i) - FIELDS:
            print("IDEA BOARD · FAILED · the Studio sent fields that are not public: %s" % sorted(set(i) - FIELDS)); return 1
        for k in [k for k, v in i.items() if v is None]:
            del i[k]
    cur = json.load(open(SNAP, encoding="utf-8"))
    if cur.get("ideas") == ideas and run("python3 atlas-tools/build-idea-board.py --check")[0]:
        print("IDEA BOARD · nothing to publish (%d approved ideas, unchanged)" % len(ideas)); return 0
    base = git("rev-parse", "HEAD")
    cur["ideas"] = ideas
    with open(SNAP, "w", encoding="utf-8") as f:
        json.dump(cur, f, ensure_ascii=False, indent=2); f.write("\n")
    ok, out = run("python3 atlas-tools/build-idea-board.py")
    why = None if ok else "builder refused: " + out[-400:]
    if why is None:
        git("add", "--", *sorted(ALLOWED))
        git("-c", "user.name=PlotNua content pipeline", "-c", "user.email=hello@plotnua.ie", "commit", "-q", "-m",
            "Idea Board content: %d approved ideas (founder's approvals in PlotArt Studio)" % len(ideas))
        why = boundary(base)
    for guard in GUARDS:
        if why is None:
            ok, out = run(guard)
            why = None if ok else "%s refused: %s" % (guard, out[-400:])
    if why is None and PUSH:
        sha = git("rev-parse", "--short", "HEAD")
        ok1, o1 = run("git push origin HEAD:refs/heads/content/ideas-%s" % sha)
        # main only moves after the gate passes. request-release.sh pushes release/auto/... with the release App token,
        # so the gate starts on that push; --no-wait because the workflow's own promote job promotes it.
        ok2, o2 = run("bash atlas-tools/release/request-release.sh ideas --no-wait")
        if not (ok1 and ok2):
            why = "push refused (main moved or no permission): " + (o1 + " " + o2)[-300:]
        else:
            full = git("rev-parse", "HEAD")
            branch = "release/auto/ideas-%s" % full[:7]
            print("RELEASE_REQUESTED %s %s" % (branch, full))
            gho = os.environ.get("GITHUB_OUTPUT")
            if gho:
                with open(gho, "a", encoding="utf-8") as f:
                    f.write("branch=%s\nsha=%s\n" % (branch, full))
    if why:
        subprocess.run(["git", "reset", "-q", "--hard", base], cwd=ROOT)
        print("IDEA BOARD · FAILED · %s" % why[:500]); return 1
    print("IDEA BOARD · %d approved ideas · %s %s" % (len(ideas), "release requested" if PUSH else "verified (simulated)", git("rev-parse", "--short", "HEAD")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
