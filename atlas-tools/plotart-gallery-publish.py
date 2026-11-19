#!/usr/bin/env python3
"""PLOTART CONTENT PIPELINE · Studio -> plotnua.ie (Phase 3, 29 Oct 2026). Runs on a checkout of main.
NOT ACTIVE: the GitHub workflow that runs it is switched off until the founder authorises activation.

    python3 atlas-tools/plotart-gallery-publish.py --studio URL --token PIPELINE_TOKEN [--push | --simulate]

For each queue item the founder has published (or, once authorised, an automatic availability/removal/order update):
  1. takes the approved export from PlotArt Studio and downloads the original photographs (SHA-256 checked);
  2. runs the Phase 1 ingest (checks, sRGB, metadata removed, never cropped) in a trial copy;
  3. refuses unless every publication safeguard passes;
  4. writes ONLY plotart/artists/<slug>/ (pages, images, gallery.json), the Virtual Gallery grid, the artist opportunity
     lists (the generated region of four pages, plotart_opportunities) and the artist's ARTIST_SUPPLIED_ARTWORK provenance
     records; commits that on top of main;
     (the Virtual Gallery collection is the region between P.VG_BEGIN and P.VG_END: Direction C2, 5 Nov 2026)
  5. runs the content-only boundary (with --instant for automatic updates), the PlotArt launch guard L1-L14, the
     image provenance guard and the image-rights scan;
  6. --push: pushes an audit branch content/plotart-<artist>-v<n>-<commit> (one per attempt) and fast-forwards main (never forced; refused if main
     moved). --simulate (tests): stops before pushing. Any failure: the commit is dropped and the Studio is told why.
"""
import glob, hashlib, http.client, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.request
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import plotart_gallery as G  # noqa: E402
import plotart_gallery_pages as P  # noqa: E402
import plotart_shell as S  # noqa: E402
import plotart_seo as SEO  # noqa: E402
import plotart_search_content as C  # noqa: E402
import plotart_opportunities as OPP  # noqa: E402  (artist opportunity lists, 16 Nov 2026)
import plotart_featured as FEAT  # noqa: E402  (Featured Artists in the Artists' Gallery, 17 Nov 2026; was the homepage)

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
# Art for Hire (Stage 3B-6): artist pages carry the fourth gallery tab only once the founder has switched the hire page on;
# until then the shell writes them byte-for-byte as before. The hire page itself is never written by this pipeline.
S.HIRE_NAV = json.load(open(os.path.join(HERE, "release", "plotart-launch-switches.json"), encoding="utf-8")).get("art_for_hire_page") is True
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
    if not check and a[:2] == ("merge-base", "--is-ancestor"):
        return "" if r.returncode == 0 else "no"
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


def regrid(lay=None, selection=None):
    """Rebuild the Artists' Gallery from the published galleries: Featured Artists first (the founder's selection, or the
    page's current one), then Explore More Artists, which leaves out whoever is featured (17 Nov 2026), so an artist who
    is featured, unfeatured, withdrawn or newly published is always shown exactly once."""
    pkgs = P.gallery_order(published())
    FEAT.refresh(ROOT, pkgs, selection)
    html = open(VG, encoding="utf-8").read()
    span = P.vg_region(html)
    if not span:
        raise RuntimeError("the Virtual Gallery collection region was not found")
    lay = layout() if lay is None else lay
    shown = [x["artist"] for x in FEAT.selection_in(html)]
    open(VG, "w", encoding="utf-8").write(html[:span[0]] + P.vg_collection(pkgs, layout=lay, featured=shown) + html[span[1]:])


def records(slug, new):
    r = json.load(open(REC, encoding="utf-8"))
    r["records"] = [x for x in r["records"] if not (x.get("class") == "ARTIST_SUPPLIED_ARTWORK" and x.get("artist_slug") == slug)] + new
    json.dump(r, open(REC, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open(REC, "a", encoding="utf-8").write("\n")


def release(topic):
    """Release the current HEAD through the checked route and wait for the real outcome. request-release.sh --no-wait
    pushes release/auto/plotart-... with the release App token, so the gate starts on that push (Stage 1, 10 Nov 2026);
    then promote-after-gate.sh waits for the gate to pass on this EXACT commit and runs promote.sh (fast-forward only,
    refused if main moved, live check, automatic rollback). "Release to production" leaves these branches to this
    publisher. The release scripts come from a copy of main's taken before anything was built (RELEASE_TOOLS), never
    from the commit being released.
    Returns (released, output)."""
    ok, o = run("bash atlas-tools/release/request-release.sh %s --no-wait" % topic)
    m = re.search(r" on (release/auto/[a-z0-9-]+)", o)
    if not ok or not m:
        return False, o
    tools = os.environ.get("RELEASE_TOOLS") or os.path.join(ROOT, "atlas-tools", "release")
    ok2, o2 = run('bash "%s/promote-after-gate.sh" %s %s' % (tools, git("rev-parse", "HEAD"), m.group(1)))
    return ok2, o + "\n" + o2


# MAIN ADVANCING DURING PUBLICATION (19 Nov 2026: Nick Munier's first publication was built on df2337a; while its gate ran,
# PR #29 moved main to 1757f90, so promote.sh refused "2c56987 does not contain the current main 1757f90"). That refusal
# is promote.sh's ancestry guard and it is NOT changed or bypassed here: main still only ever fast-forwards, and only to a
# commit whose own push-started gate passed. What changes is what happens next. When, and only when, the refusal was
# caused by main having moved FORWARD past the commit this update was built on, the update is rebuilt from the Studio's
# approved export on top of the new main (so every change that reached main meanwhile is kept exactly as it is), every
# guard runs again against that new base, and the new commit goes through its own saved copy, gate and promotion. At most
# REBUILDS attempts in one run; any other refusal (gate, guards, live check, permission) stays final, exactly as before.
REBUILDS = 3
MAIN_MOVED = re.compile(r"does not contain the current main")


def main_advanced(output, base):
    """True only if the release was refused by the ancestry guard AND origin/main has really moved forward from `base`
    (never on a rewritten or diverged main: that is refused and left for the founder)."""
    if not MAIN_MOVED.search(output or ""):
        return False
    git("fetch", "-q", "origin", "main")
    now = git("rev-parse", "origin/main")
    return now != base and git("merge-base", "--is-ancestor", base, now, check=False) == ""


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
            return G.refusal(name, out)
    return None



def fetch_image(qid, iid, tries=3):
    """One photograph from the Studio export. A download cut off part-way (18 Nov 2026: Carmel Marrinan's first
    publication failed with "IncompleteRead(71654 bytes read, 1366688 more expected)") is fetched again, up to three
    times in all, a few seconds apart. Nothing is relaxed: every copy must still match the Studio's SHA-256 fingerprint,
    and a third failure refuses the publication exactly as before."""
    for n in range(1, tries + 1):
        try:
            return call("GET", "/api/pipeline/image/%s/%s" % (qid, iid), raw=True)
        except (http.client.IncompleteRead, ConnectionError, TimeoutError) as e:
            if n == tries:
                raise
            print("image %s: download interrupted (%s); trying again (%d of %d)" % (iid, type(e).__name__, n + 1, tries), flush=True)
            time.sleep(5 * n)


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
            body, headers = fetch_image(q["id"], iid)
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
        for n in range(1, REBUILDS + 1):
            bad, moved = publish_item(q, final=(n == REBUILDS))
            if not (bad and moved) or n == REBUILDS:
                failed += bad
                break
            print("PLOTART CONTENT · %s v%d · main moved during the release: rebuilding on the new main (attempt %d of %d)"
                  % (q["artist_id"], q["version"], n + 1, REBUILDS), flush=True)
    failed += with_rebuilds("gallery order", order_sync)
    failed += with_rebuilds("featured artists", featured_sync)
    if not items:
        print("PLOTART CONTENT · nothing to publish")
    return 1 if failed else 0


def with_rebuilds(label, once):
    """The gallery order and Featured Artists updates, with the same bounded rebuild when main moved during the release."""
    for n in range(1, REBUILDS + 1):
        bad, moved = once(final=(n == REBUILDS))
        if not (bad and moved) or n == REBUILDS:
            return bad
        print("PLOTART CONTENT · %s · main moved during the release: rebuilding on the new main (attempt %d of %d)" % (label, n + 1, REBUILDS), flush=True)
    return 0


def publish_item(q, final=True):
    """One queue item, built on the latest main. Returns (1 if not published else 0, main_moved). When main moved and this
    is not the final attempt, nothing is reported to the Studio yet: the item stays 'exporting' and is rebuilt."""
    moved = False
    if PUSH:              # build each update on the latest main, so another release moving main can't make it unpromotable
        git("fetch", "-q", "origin", "main")
        git("reset", "-q", "--hard", "origin/main")
    base = git("rev-parse", "HEAD")
    try:
        why = one(q)
        if why is None:
            sm = Path(ROOT) / "sitemap.xml"
            sm.write_text(SEO.update_sitemap(sm.read_text(), published(), SEO.switches()))
            C.refresh(ROOT, published())
            OPP.refresh(ROOT, published())     # the opportunity lists: only published artists, only what they chose to show
            FEAT.refresh(ROOT, published())    # Featured Artists: the founder's current choice, published work only
    except Exception as e:                       # noqa: BLE001 - any failure refuses this item, never a half-publish
        why = "refused: %s: %s" % (type(e).__name__, e)
    if why is None:
        git("add", "-A", "plotart/artists", "plotart/gallery/index.html", "image-provenance-records.json", "sitemap.xml", *["plotart/" + p for p in SEO.GENERATED_PATHS],
            *["plotart/" + p for p in OPP.PAGES if os.path.exists(os.path.join(ROOT, "plotart", p))])
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
            moved = ok1 and main_advanced(o2, base)
    if why:
        subprocess.run(["git", "reset", "-q", "--hard", base], cwd=ROOT)
        subprocess.run(["git", "clean", "-qfd", "plotart/artists"], cwd=ROOT)
        if moved and not final:
            return 1, True
        call("POST", "/api/pipeline/result/" + q["id"], {"status": "failed", "detail": why[:1900]})
        print("PLOTART CONTENT · %s v%d · FAILED · %s" % (q["artist_id"], q["version"], why[:300]))
        return 1, moved
    sha = git("rev-parse", "HEAD")
    call("POST", "/api/pipeline/result/" + q["id"], {"status": "published", "detail": "commit %s%s" % (sha[:12], " (simulated)" if SIMULATE else "")})
    print("PLOTART CONTENT · %s v%d · %s · %s" % (q["artist_id"], q["version"], q["kind"], "published " + sha[:12] if PUSH else "verified (simulated) " + sha[:12]))
    return 0, False


def order_sync(final=True):
    """Gallery order (31 Oct 2026): after the queue, rebuild the Virtual Gallery grid from the founder's order. If only
    the grid changed (a move, reservation or release), commit it as a content-only update, run every guard and push
    exactly as for a gallery. Nothing changes when the order is unchanged."""
    moved = False
    if git("status", "--porcelain"):
        return 0, False
    if PUSH:
        git("fetch", "-q", "origin", "main")
        git("reset", "-q", "--hard", "origin/main")
    base = git("rev-parse", "HEAD")
    try:
        lay = layout()
        if lay is None:
            return 0, False
        regrid(lay)
    except Exception as e:                           # noqa: BLE001
        subprocess.run(["git", "checkout", "-q", "--", "plotart/gallery/index.html"], cwd=ROOT)
        print("PLOTART CONTENT · gallery order · FAILED · %s" % e)
        return 1, False
    if not git("status", "--porcelain"):
        return 0, False
    git("add", "plotart/gallery/index.html")
    git("-c", "user.name=PlotArt content pipeline", "-c", "user.email=hello@plotnua.ie", "commit", "-q", "-m",
        "PlotArt content: Virtual Gallery order (founder's Gallery order in PlotArt Studio)")
    why = guards(base, False)
    if why is None and PUSH:
        ok1, o1 = run("git push origin HEAD:refs/heads/content/plotart-gallery-order-%s" % git("rev-parse", "--short", "HEAD"))
        ok2, o2 = release("plotart-gallery-order") if ok1 else (False, "")
        if not (ok1 and ok2):
            why = "not released (gate, main moved, live check or permission): " + (o1 + " " + o2)[-300:]
            moved = ok1 and main_advanced(o2, base)
    sha = git("rev-parse", "HEAD")
    if why:
        subprocess.run(["git", "reset", "-q", "--hard", base], cwd=ROOT)
        if moved and not final:
            return 1, True
    try:
        call("POST", "/api/pipeline/gallery-order/result", {"status": "failed" if why else "published",
             "detail": (why or "commit %s%s" % (sha[:12], " (simulated)" if SIMULATE else ""))[:1900]})
    except Exception:                                # noqa: BLE001 - the record is best-effort; the commit stands or was dropped
        pass
    print("PLOTART CONTENT · gallery order · %s" % ("FAILED · " + why[:300] if why else ("published " if PUSH else "verified (simulated) ") + sha[:12]))
    return (1, moved) if why else (0, False)


def featured_selection():
    """The founder's Featured Artists selection from PlotArt Studio (Review Desk "Featured Artists"; migration 0016's
    table, unchanged): gallery addresses and artwork ids only. A Studio without the route (404), or without the table
    yet, means nothing to change."""
    try:
        r = call("GET", "/api/pipeline/featured-artists")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    if not r.get("installed"):
        return None
    return FEAT.check_selection(r.get("items", []))


def featured_sync(final=True):
    """Featured Artists (17 Nov 2026; moved from the homepage): after the queue and the gallery order, re-render the
    Featured Artists region of the Artists' Gallery from the founder's selection and the published galleries. Only that
    region can change (content boundary, launch guard L20); the complete collection below is not touched. It is
    committed, guarded and released exactly like the gallery order. Nothing happens when nothing changed."""
    page = "plotart/" + FEAT.PAGE
    moved = False
    if git("status", "--porcelain"):
        return 0, False
    if PUSH:
        git("fetch", "-q", "origin", "main")
        git("reset", "-q", "--hard", "origin/main")
    base = git("rev-parse", "HEAD")
    try:
        sel = featured_selection()
        if sel is None:
            return 0, False
        before = open(os.path.join(ROOT, page), encoding="utf-8").read()
        lay = layout()
        if lay is None:                    # no Gallery order from the Studio: the page cannot be rebuilt safely
            return 0, False
        regrid(lay, sel)                   # Featured Artists, then Explore More Artists without them (17 Nov 2026)
        after = open(os.path.join(ROOT, page), encoding="utf-8").read()
        # only the two generated regions may change: nothing else on the page, and never the twenty-five positions
        blank = lambda d: FEAT.outside(d[:P.vg_region(d)[0]] + P.VG_BEGIN + P.VG_END + d[P.vg_region(d)[1]:])
        idx = lambda d: re.findall(r'<li class="pa-vgc-pos is-[a-z]+">.*?</li>', d[slice(*P.vg_region(d))])
        if P.vg_region(before) is None or blank(before) != blank(after) or idx(before) != idx(after):
            raise ValueError("the Featured Artists update would change the page outside its two regions or the positions")
    except Exception as e:                           # noqa: BLE001
        subprocess.run(["git", "checkout", "-q", "--", page], cwd=ROOT)
        print("PLOTART CONTENT · featured artists · FAILED · %s" % e)
        return 1, False
    if not git("status", "--porcelain"):
        return 0, False
    git("add", page)
    git("-c", "user.name=PlotArt content pipeline", "-c", "user.email=hello@plotnua.ie", "commit", "-q", "-m",
        "PlotArt content: Featured Artists (founder's selection in PlotArt Studio)")
    why = guards(base, False)
    if why is None and PUSH:
        ok1, o1 = run("git push origin HEAD:refs/heads/content/plotart-featured-%s" % git("rev-parse", "--short", "HEAD"))
        ok2, o2 = release("plotart-featured") if ok1 else (False, "")
        if not (ok1 and ok2):
            why = "not released (gate, main moved, live check or permission): " + (o1 + " " + o2)[-300:]
            moved = ok1 and main_advanced(o2, base)
    sha = git("rev-parse", "HEAD")
    if why:
        subprocess.run(["git", "reset", "-q", "--hard", base], cwd=ROOT)
        if moved and not final:
            return 1, True
    print("PLOTART CONTENT · featured artists · %s" % ("FAILED · " + why[:300] if why else ("published " if PUSH else "verified (simulated) ") + sha[:12]))
    return (1, moved) if why else (0, False)


if __name__ == "__main__":
    sys.exit(main())
