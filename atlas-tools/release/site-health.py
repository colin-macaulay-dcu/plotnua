#!/usr/bin/env python3
"""PlotNua · site and service health check (automation v1, 1 Nov 2026). Read-only: it never writes, posts an idea or
uses a secret. Used after every automatic deployment and on a schedule (.github/workflows/site-health.yml).

    python3 atlas-tools/release/site-health.py [--expect-commit SHA] [--json out.json]

Checks:
  H1  key public pages answer 200 and carry their landmark text;
  H2  pages that must not exist yet answer 404 (read from atlas-tools/release/flags.json: ideas.html until launched);
  H3  the PlotArt Studio and its pipeline sit behind Cloudflare Access (an anonymous request is redirected to sign-in);
  H4  public Workers refuse what they must refuse (GET 405; another site's origin 403; the Idea Board intake answers
      503 while flags say it is closed);
  H5  with --expect-commit: the live site serves the files of that commit (byte comparison of the checked pages).
Exit 0 = healthy. Prints one line per check and a summary; --json writes the results for the workflow.
"""
import hashlib, json, pathlib, subprocess, sys, time, urllib.error, urllib.request

# The repository to read from: the current directory (the workflow's checkout), so the script can run from a trusted copy.
ROOT = pathlib.Path.cwd()
arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
_want = arg("--expect-commit")
if _want:   # the switches of the commit being verified (a release may e.g. publish a page that was absent)
    FLAGS = json.loads(subprocess.run(["git", "show", "%s:atlas-tools/release/flags.json" % _want], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
else:
    FLAGS = json.loads((ROOT / "atlas-tools" / "release" / "flags.json").read_text(encoding="utf-8"))
SITE = "https://plotnua.ie"
PAGES = {"": "PlotNua", "discoveries.html": "Discovery Library", "discovery-hidden-cars.html": "PlotNua",
         "discovery-underground-swimming-pool.html": "PlotNua", "ideas.html": "What Could Your Property Do?",
         "plotart/": "PlotArt", "privacy.html": "Privacy", "terms.html": "Terms", "contact.html": "PlotNua"}
STUDIO = "https://plotart-studio.colin-a41.workers.dev"
IDEAS = "https://plotnua-ideas.colin-a41.workers.dev/v1/ideas"
results = []


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def fetch(url, method="GET", headers=None, data=None, follow=True):
    url = url + (("&" if "?" in url else "?") + "h=%d" % time.time_ns() if method == "GET" else "")
    req = urllib.request.Request(url, method=method, data=data, headers={"User-Agent": "PlotNua-health/1.0 (+https://plotnua.ie)", **(headers or {})})
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    for attempt in range(3):
        try:
            with opener.open(req, timeout=30) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read(), dict(e.headers)
        except Exception:                                   # noqa: BLE001 - network blip: retry, then report
            time.sleep(5)
    return 0, b"", {}


def check(name, ok, detail=""):
    results.append({"check": name, "ok": bool(ok), "detail": detail})
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  · " + detail) if detail else ""))


for path, mark in PAGES.items():
    s, body, _ = fetch(SITE + "/" + path)
    check("H1 /%s answers 200 with its landmark" % path, s == 200 and mark.encode() in body, "HTTP %s" % s)
for path in FLAGS.get("must_not_exist", []):
    s, _, _ = fetch(SITE + "/" + path)
    check("H2 /%s is not public yet" % path, s == 404, "HTTP %s" % s)
for path in ("/admin/ideas", "/api/pipeline/ideas"):
    s, _, h = fetch(STUDIO + path, follow=False)
    check("H3 Studio %s requires the Cloudflare Access sign-in" % path, s in (302, 303) and "cloudflareaccess.com" in h.get("Location", h.get("location", "")), "HTTP %s" % s)
s, _, _ = fetch(IDEAS)
check("H4 Idea Board intake refuses GET", s == 405, "HTTP %s" % s)
s, _, _ = fetch(IDEAS, "POST", {"Origin": "https://evil.example", "Content-Type": "application/json"}, b"{}")
check("H4 Idea Board intake refuses another site", s == 403, "HTTP %s" % s)
if FLAGS.get("ideas_submissions_open"):
    # open: plotnua.ie's origin reaches validation (a too-short idea is refused with a reason; nothing is stored)
    s, body, _ = fetch(IDEAS, "POST", {"Origin": "https://plotnua.ie", "Content-Type": "application/json"}, b'{"idea":"x"}')
    check("H4 Idea Board intake is open to plotnua.ie and validates (nothing stored)", s == 400 and b"at least 8 characters" in body, "HTTP %s" % s)
else:
    s, _, _ = fetch(IDEAS, "POST", {"Origin": "https://plotnua.ie", "Content-Type": "application/json"}, b'{"idea":"health check"}')
    check("H4 Idea Board intake is closed (flags: submissions not open)", s == 503, "HTTP %s" % s)
want = arg("--expect-commit")
if want:
    tree = subprocess.run(["git", "ls-tree", "--name-only", want], cwd=ROOT, capture_output=True, text=True).stdout.split()
    discoveries = sorted(p for p in tree if p.startswith("discovery-") and p.endswith(".html"))
    for path in sorted(set([p for p in PAGES if p.endswith(".html")] + discoveries)):
        src = subprocess.run(["git", "show", "%s:%s" % (want, path)], cwd=ROOT, capture_output=True).stdout
        live = b""
        for attempt in range(12):                           # GitHub Pages can take a few minutes to publish
            s, live, _ = fetch(SITE + "/" + path)
            if live == src:
                break
            time.sleep(20)
        check("H5 /%s is the file from %s" % (path, want[:7]), live == src and bool(src),
              "live %s · commit %s" % (hashlib.sha256(live).hexdigest()[:12], hashlib.sha256(src).hexdigest()[:12]))
bad = [r for r in results if not r["ok"]]
print("\nSITE HEALTH · %s · %d checks, %d failed" % ("OK" if not bad else "FAIL", len(results), len(bad)))
if arg("--json"):
    pathlib.Path(arg("--json")).write_text(json.dumps({"ok": not bad, "results": results}, indent=2), encoding="utf-8")
sys.exit(1 if bad else 0)
