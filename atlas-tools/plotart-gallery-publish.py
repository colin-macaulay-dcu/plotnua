#!/usr/bin/env python3
"""PLOTART CONTENT PIPELINE · Studio -> plotnua.ie (Phase 3, 29 Oct 2026). Runs on a checkout of main.
NOT ACTIVE: the GitHub workflow that runs it is switched off until the founder authorises activation.

    python3 atlas-tools/plotart-gallery-publish.py --studio URL --token PIPELINE_TOKEN [--push | --simulate]

For each queue item the founder has published (or, once authorised, an automatic availability/removal/order update):
  1. takes the approved export from PlotArt Studio and downloads the original photographs (SHA-256 checked);
  2. runs the Phase 1 ingest (checks, sRGB, metadata removed, never cropped) in a trial copy;
  3. refuses unless every publication safeguard passes;
  4. writes ONLY plotart/artists/<slug>/ (pages, images, gallery.json), the Virtual Gallery grid and the artist's
     ARTIST_SUPPLIED_ARTWORK provenance records; commits that on top of main;
     (the Virtual Gallery collection is the region between P.VG_BEGIN and P.VG_END: Direction C2, 5 Nov 2026)
  5. runs the content-only boundary (with --instant for automatic updates), the PlotArt launch guard L1-L14, the
     image provenance guard and the image-rights scan;
  6. --push: pushes an audit branch content/plotart-<artist>-v<n>-<commit> (one per attempt) and fast-forwards main (never forced; refused if main
     moved). --simulate (tests): stops before pushing. Any failure: the commit is dropped and the Studio is told why.
"""
import glob, hashlib, json, os, re, shutil, subprocess, sys, tempfile, urllib.error, urllib.request
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import plotart_gallery as G  # noqa: E402
import plotart_gallery_pages as P  # noqa: E402
import plotart_shell as S  # noqa: E402
import plotart_seo as SEO  # noqa: E402
import plotart_search_content as C  # noqa: E402

arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
STUDIO, TOKEN = arg("--studio"), arg("--token")
PUSH, SIMULATE = "--push" in sys.argv, "--simulate" in sys.argv
if not (STUDIO and TOKEN) or PUSH == SIMULATE:
    sys.exit(__doc__)
if SIMULATE and not re.match(r"^http://(127\.0\.0\.1|localhost):\d+/?$", STUDIO):
    sys.exit("REFUSED: --simulate is for local tests only (it reports success without pushing)")
CONFIG = json.load(open(os.path.join(HERE, "release", "plotart-gallery-config.json"), encoding="utf-8"))
ENDPOINT = CONFIG.get("enquiry_endpoint")
if ENDPOINT and not re.match(r"^https://[a-z0-9.-]+\.workers\.dev/v1/enquiry$|^http://(127\.0\.0\.1|localhost):\d{2,5}/v1/enquiry$", ENDPOINT):
    sys.exit("REFUSED: enquiry_endpoint must be the PlotArt enquiry relay route")
ART = os.path.join(ROOT, "plotart", "artists")
REC = os.path.join(ROOT, "image-provenance-records.json")
VG = os.path.join(ROOT, "plotart", "gallery", "index.html")


# Cloudflare Access sits in front of the Studio's address: the pipeline passes it with an Access service token
# (secrets STUDIO_ACCESS_CLIENT_ID / STUDIO_ACCESS_CLIENT_SECRET), then authenticates to the Studio with its bearer token.
# Cloudflare refuses Python's default User-Agent ("Python-urllib/…", error 1010) before Access or the Studio see the
# request, so the pipeline names itself (found on the first live run, 30 Oct 2026).
HEADERS = {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json",
           "User-Agent": "PlotArt-content-pipeline/1.0 (+https://plotnua.ie)"}
if os.environ.get("STUDIO_ACCESS_CLIENT_ID") and os.environ.get("STUDIO_ACCESS_CLIENT_SECRET"):
    HEADERS["CF-Access-Client-Id"] = os.environ["STUDIO_ACCESS_CLIENT_ID"]
    HEADERS["CF-Access-Client-Secret"] = os.environ["STUDIO_ACCESS_CLIENT_SECRET"]


def call(method, path, body=None, raw=False):
    req = urllib.request.Request(STUDIO.rstrip("/") + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as r:
        return (r.read(), dict(r.headers)) if raw else json.loads(r.read())


def git(*a, check=True):
    r = subprocess.run(("git",) + a, cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError("git %s: %s" % (" ".join(a), r.stderr.strip()))
    return r.stdout.strip()


def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def published():
    """Every published gallery package (plotart/artists/<slug>/gallery.json)."""
    out = []
    for p in sorted(glob.glob(os.path.join(ART, "*", "gallery.json"))):
        out.append(json.load(open(p, encoding="utf-8")))
    return out


def write_gallery(pkg, img_src):
    slug = pkg["artist"]["slug"]
    d = os.path.join(ART, slug)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, "img"))
    # a published gallery with no works on show and no portrait has no images at all (founder decision 1 Nov 2026)
    for f in (sorted(os.listdir(img_src)) if os.path.isdir(img_src) else []):
        shutil.copyfile(os.path.join(img_src, f), os.path.join(d, "img", f))
    for path, doc in P.gallery_pages(pkg, S.artist_page, enquiry_endpoint=ENDPOINT):
        open(os.path.join(ROOT, "plotart", path), "w", encoding="utf-8").write(doc)
    public = {k: pkg[k] for k in ("schema", "artist", "works", "publication", "provenance_sources")}
    json.dump(public, open(os.path.join(d, "gallery.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, sort_keys=True)


def layout():
    """The founder's gallery order from PlotArt Studio (Gallery order, 31 Oct 2026): positions 01-25 with the published
    or in-flight artist's gallery address, or reserved. Never a reservation note. A Studio without the Gallery order
    route (404) means the founder's order isn't available yet: the grid keeps its previous automatic order."""
    try:
        r = call("GET", "/api/pipeline/gallery-order")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    # "assigned" (optional, Direction C2): an artist holds the position but their gallery is not published here.
    # It is a bare true/false and never carries who; anything else is refused.
    allowed = {"position", "slug", "reserved", "assigned"}
    for e in r.get("positions", []):
        if set(e) - allowed:
            raise RuntimeError("the gallery order carries a field it must not: %s" % sorted(set(e) - allowed))
        if "assigned" in e and not isinstance(e["assigned"], bool):
            raise RuntimeError("the gallery order's 'assigned' flag must be true or false")
    return {"positions": r.get("positions", []), "extra": r.get("extra", [])}


def regrid(lay=None):
    pkgs = P.gallery_order(published())
    html = open(VG, encoding="utf-8").read()
    span = P.vg_region(html)
    if not span:
        raise RuntimeError("the Virtual Gallery collection region was not found")
    lay = layout() if lay is None else lay
    open(VG, "w", encoding="utf-8").write(html[:span[0]] + P.vg_collection(pkgs, layout=lay) + html[span[1]:])


def records(slug, new):
    r = json.load(open(REC, encoding="utf-8"))
    r["records"] = [x for x in r["records"] if not (x.get("class") == "ARTIST_SUPPLIED_ARTWORK" and x.get("artist_slug") == slug)] + new
    json.dump(r, open(REC, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open(REC, "a", encoding="utf-8").write("\n")


def release(topic):
    """Release the current HEAD through the checked route and wait for the real outcome (fix 5 Nov 2026, as the Idea
    Board and Borrowed Garden). A gate dispatched with the workflow's built-in token never starts "Release to production"
    (GitHub does not chain workflow_run from that token), so waiting for main to move never ended. Instead: start the
    gate (request-release.sh --no-wait), then promote-after-gate.sh waits for the gate to pass on this EXACT commit and
    runs promote.sh (fast-forward only, refused if main moved, live check, automatic rollback). The release scripts come
    from a copy of main's taken before anything was built (RELEASE_TOOLS), never from the commit being released.
    Returns (released, output)."""
    ok, o = run("bash atlas-tools/release/request-release.sh %s --no-wait" % topic)
    m = re.search(r" on (release/auto/[a-z0-9-]+)", o)
    if not ok or not m:
        return False, o
    tools = os.environ.get("RELEASE_TOOLS") or os.path.join(ROOT, "atlas-tools", "release")
    ok2, o2 = run('bash "%s/promote-after-gate.sh" %s %s' % (tools, git("rev-parse", "HEAD"), m.group(1)))
    return ok2, o + "\n" + o2


def guards(base, instant):
    checks = [
        ("content-only boundary", "python3 atlas-tools/release/plotart-content-boundary.py %s HEAD%s" % (base, " --instant" if instant else ""), "CONTENT BOUNDARY · OK"),
        ("PlotArt launch guard", "python3 atlas-tools/prove-plotart-launch.py . --switches atlas-tools/release/plotart-launch-switches.json "
                                 "--manifest atlas-tools/release/plotart-launch-manifest.json", "PLOTART LAUNCH · OK"),
        ("image provenance", "node atlas-tools/validate-image-provenance.js", " passed, 0 failed"),
        ("image rights", "node atlas-tools/validate-image-rights.js --scan-html . --permissions image-rights-manifest.json --max-age-days 30", None),
    ]
    for name, cmd, want in checks:
        ok, out = run(cmd)
        if not ok or (want and want not in out):
            return "%s refused: %s" % (name, out[-600:])
    return None


def one(q):
    ex = call("POST", "/api/pipeline/export/" + q["id"])
    g, slug = ex["gallery"], ex["gallery"]["artist"]["slug"]
    if not G.SLUG.match(slug):
        return "refused: invalid gallery address"
    tmp = tempfile.mkdtemp(prefix="pa-pub-")
    try:
        if q["kind"] == "remove":
            shutil.rmtree(os.path.join(ART, slug), ignore_errors=True)
            records(slug, [])
            regrid()
            return None
        exp = os.path.join(tmp, "export")
        os.makedirs(exp)
        names = {i["file"].split(".")[0]: i["file"] for w in g["works"] for i in w["images"]}
        if g["artist"].get("portrait"):
            names[g["artist"]["portrait"]["file"].split(".")[0]] = g["artist"]["portrait"]["file"]
        for iid in ex["images"]:
            body, headers = call("GET", "/api/pipeline/image/%s/%s" % (q["id"], iid), raw=True)
            if hashlib.sha256(body).hexdigest() != headers.get("X-Sha256"):
                return "refused: image %s changed in transit" % iid
            open(os.path.join(exp, names[iid]), "wb").write(body)
        json.dump(g, open(os.path.join(exp, "gallery.json"), "w"), indent=1, ensure_ascii=False)
        trial = os.path.join(tmp, "packages")                 # other galleries, for duplicate detection
        for other in published():
            if other["artist"]["slug"] != slug:
                os.makedirs(os.path.join(trial, other["artist"]["slug"]))
                json.dump(other, open(os.path.join(trial, other["artist"]["slug"], "package.json"), "w"))
        r = subprocess.run([sys.executable, os.path.join(HERE, "plotart-gallery-ingest.py"), exp, trial], capture_output=True, text=True)
        if r.returncode:
            return "refused: " + r.stdout.strip()[-400:]
        pkg = json.load(open(os.path.join(trial, slug, "package.json"), encoding="utf-8"))
        blocks = G.publication_blocks(pkg)
        if blocks:
            return "refused: " + "; ".join(blocks)
        write_gallery(pkg, os.path.join(trial, slug, "img"))
        records(slug, pkg["provenance"])
        regrid()
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    if git("status", "--porcelain"):
        sys.exit("REFUSED: the checkout is not clean")
    items = call("GET", "/api/pipeline/queue")["items"]
    failed = 0
    for q in items:
        if PUSH:          # build each update on the latest main, so another release moving main can't make it unpromotable
            git("fetch", "-q", "origin", "main")
            git("reset", "-q", "--hard", "origin/main")
        base = git("rev-parse", "HEAD")
        try:
            why = one(q)
            if why is None:
                sm = Path(ROOT) / "sitemap.xml"
                sm.write_text(SEO.update_sitemap(sm.read_text(), published(), SEO.switches()))
                C.refresh(ROOT, published())
        except Exception as e:                       # noqa: BLE001 - any failure refuses this item, never a half-publish
            why = "refused: %s: %s" % (type(e).__name__, e)
        if why is None:
            git("add", "-A", "plotart/artists", "plotart/gallery/index.html", "image-provenance-records.json", "sitemap.xml", *["plotart/" + p for p in SEO.GUIDE_PATHS])
            git("-c", "user.name=PlotArt content pipeline", "-c", "user.email=hello@plotnua.ie", "commit", "-q", "-m",
                "PlotArt content: %s · version %d · %s (Studio queue %s)" % (q["artist_id"], q["version"], q["kind"], q["id"]))
            why = guards(base, q["kind"] == "instant")
        if why is None and PUSH:
            # one saved copy per attempt (fix 5 Nov 2026): a retry of the same version is a new commit, so it gets its own
            # branch instead of colliding with an earlier attempt's copy (which is kept, never overwritten or forced)
            branch = "content/plotart-%s-v%d-%s" % (q["artist_id"], q["version"], git("rev-parse", "--short=12", "HEAD"))
            ok1, o1 = run("git push origin HEAD:refs/heads/%s" % branch)
            ok2, o2 = release("plotart-%s-v%d" % (q["artist_id"], q["version"])) if ok1 else (False, "")   # main only moves after the gate passes
            if not (ok1 and ok2):
                why = "not released (gate, main moved, live check or permission): " + (o1 + " " + o2)[-300:]
        if why:
            failed += 1
            subprocess.run(["git", "reset", "-q", "--hard", base], cwd=ROOT)
            subprocess.run(["git", "clean", "-qfd", "plotart/artists"], cwd=ROOT)
            call("POST", "/api/pipeline/result/" + q["id"], {"status": "failed", "detail": why[:1900]})
            print("PLOTART CONTENT · %s v%d · FAILED · %s" % (q["artist_id"], q["version"], why[:300]))
        else:
            sha = git("rev-parse", "HEAD")
            call("POST", "/api/pipeline/result/" + q["id"], {"status": "published", "detail": "commit %s%s" % (sha[:12], " (simulated)" if SIMULATE else "")})
            print("PLOTART CONTENT · %s v%d · %s · %s" % (q["artist_id"], q["version"], q["kind"], "published " + sha[:12] if PUSH else "verified (simulated) " + sha[:12]))
    failed += order_sync()
    if not items:
        print("PLOTART CONTENT · nothing to publish")
    return 1 if failed else 0


def order_sync():
    """Gallery order (31 Oct 2026): after the queue, rebuild the Virtual Gallery grid from the founder's order. If only
    the grid changed (a move, reservation or release), commit it as a content-only update, run every guard and push
    exactly as for a gallery. Nothing changes when the order is unchanged."""
    if git("status", "--porcelain"):
        return 0
    if PUSH:
        git("fetch", "-q", "origin", "main")
        git("reset", "-q", "--hard", "origin/main")
    base = git("rev-parse", "HEAD")
    try:
        lay = layout()
        if lay is None:
            return 0
        regrid(lay)
    except Exception as e:                           # noqa: BLE001
        subprocess.run(["git", "checkout", "-q", "--", "plotart/gallery/index.html"], cwd=ROOT)
        print("PLOTART CONTENT · gallery order · FAILED · %s" % e)
        return 1
    if not git("status", "--porcelain"):
        return 0
    git("add", "plotart/gallery/index.html")
    git("-c", "user.name=PlotArt content pipeline", "-c", "user.email=hello@plotnua.ie", "commit", "-q", "-m",
        "PlotArt content: Virtual Gallery order (founder's Gallery order in PlotArt Studio)")
    why = guards(base, False)
    if why is None and PUSH:
        ok1, o1 = run("git push origin HEAD:refs/heads/content/plotart-gallery-order-%s" % git("rev-parse", "--short", "HEAD"))
        ok2, o2 = release("plotart-gallery-order") if ok1 else (False, "")
        if not (ok1 and ok2):
            why = "not released (gate, main moved, live check or permission): " + (o1 + " " + o2)[-300:]
    sha = git("rev-parse", "HEAD")
    if why:
        subprocess.run(["git", "reset", "-q", "--hard", base], cwd=ROOT)
    try:
        call("POST", "/api/pipeline/gallery-order/result", {"status": "failed" if why else "published",
             "detail": (why or "commit %s%s" % (sha[:12], " (simulated)" if SIMULATE else ""))[:1900]})
    except Exception:                                # noqa: BLE001 - the record is best-effort; the commit stands or was dropped
        pass
    print("PLOTART CONTENT · gallery order · %s" % ("FAILED · " + why[:300] if why else ("published " if PUSH else "verified (simulated) ") + sha[:12]))
    return 1 if why else 0


if __name__ == "__main__":
    sys.exit(main())
