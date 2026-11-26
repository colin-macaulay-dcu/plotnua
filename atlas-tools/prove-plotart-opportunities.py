#!/usr/bin/env python3
"""PROVE · artist opportunity lists on the website (founder approval 16 Nov 2026).

  python3 atlas-tools/prove-plotart-opportunities.py [--exports DIR] [--shots DIR]

O1  the pipeline accepts open_to only as known keys in the fixed order, never online_only, repeats or an empty list
O2  the ingest carries open_to and "Open for commissions" from a real Studio export into the published package
O3  every PUBLISHED gallery renders byte-for-byte as main renders it today (nobody has chosen to show anything yet);
    with open_to the gallery page gains exactly one "Open to" line linking to each list, and nothing else changes
O4  the lists: only approved packages; by surname; Commissions also from the existing switch; withdrawing, keeping private
    or unpublishing removes an artist; programme pages show nothing until someone is listed; no private answer appears
O5  the content boundary accepts a gallery release that changes a list only as the published packages produce it, and
    refuses any other change to those pages (outside the region, an invented artist, the hire works catalogue)
O6  in a browser: the four pages and an artist page at 1440 and 390 px, no overflow, links resolve (--shots saves previews)
--exports: export-shown.json / export-none.json from worker/plotart-studio/test/prove-opportunities-public.mjs --export-dir
"""
import copy, glob, html, importlib.util, json, os, re, shutil, subprocess, sys, tempfile, threading, functools, http.server

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import plotart_gallery as G            # noqa: E402
import plotart_gallery_pages as P      # noqa: E402
import plotart_opportunities as OPP    # noqa: E402
import plotart_featured as FEAT    # noqa: E402
import plotart_shell as S              # noqa: E402

ARGS = sys.argv[1:]
EXPORTS = ARGS[ARGS.index("--exports") + 1] if "--exports" in ARGS else None
SHOTS = ARGS[ARGS.index("--shots") + 1] if "--shots" in ARGS else None
ENDPOINT = json.load(open(os.path.join(HERE, "release", "plotart-gallery-config.json")))["enquiry_endpoint"]
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, ("  [%s]" % str(detail)[:500]) if not ok and detail else ""))


def run(cmd, cwd=ROOT):
    r = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def main_module():
    src = subprocess.run(["git", "show", "origin/main:atlas-tools/plotart_gallery_pages.py"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    d = tempfile.mkdtemp(prefix="pa-opp-main-")
    path = os.path.join(d, "plotart_gallery_pages_main.py")
    open(path, "w").write(src)
    spec = importlib.util.spec_from_file_location("plotart_gallery_pages_main", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def pages(mod, pkg, endpoint):
    ws = mod.shown(pkg)
    out = {"index": mod.artist_body(pkg, enquiry_endpoint=endpoint)}
    for i, w in enumerate(ws):
        out[w["slug"]] = mod.artwork_body(pkg, w, ws[i - 1] if i else None, ws[i + 1] if i + 1 < len(ws) else None, enquiry_endpoint=endpoint)
    return out


def sample(slug, name, practice, open_to=None, ofc=False, state="approved"):
    """A synthetic published package with no works and no portrait (no images): previews never borrow anyone's art."""
    a = {"slug": slug, "display_name": name, "founding": False, "practice": practice, "medium": "painting", "statement": None,
         "bio": "%s is a sample artist used only in this private preview. No real artist is described." % name, "website": None, "instagram": None,
         "county": None, "portrait": None}
    if open_to:
        a["open_to"] = [k for k in OPP.KEYS if k in open_to]
    if ofc:
        a["open_for_commissions"] = True
    return {"schema": "plotnua.plotart.package.v1", "artist": a, "works": [], "provenance_sources": [],
            "publication": {"state": state, "version": "v2", "approved_by": "founder", "approved_at": "2026-11-16T10:00:00Z", "licence_version": "PA-GPIL-2026-11",
                            "licence_accepted_at": "2026-11-10T10:00:00Z", "permission_ref": "PA-PERM-sample", "test_note": "sample"}}


print("PROVE · artist opportunity lists (website)")
print("— O1 the pipeline")
if EXPORTS:
    shown, none = (json.load(open(os.path.join(EXPORTS, f))) for f in ("export-shown.json", "export-none.json"))
    def ok(g):
        try:
            G.validate_export(g)
            return True
        except G.Refused as e:
            return str(e)
    check("O1a the Studio's real exports pass: shown (all seven, in order) and none (no key)",
          ok(shown) is True and ok(none) is True and shown["artist"]["open_to"] == list(OPP.KEYS) and "open_to" not in none["artist"], [ok(shown), ok(none)])
    refused = []
    for v in ([], ["online_only"], ["talks", "exhibitions"], ["talks", "talks"], ["county"], "talks", None, [1]):
        g = copy.deepcopy(shown)
        g["artist"]["open_to"] = v
        refused.append(ok(g) is not True)
    check("O1b refused: empty, online_only, wrong order, repeats, unknown keys, a string, null, a number", all(refused), refused)
    priv = json.dumps(shown)
    check("O1c the export carries nothing private from the Opportunities answers", not re.search(r"Cork|courier|anywhere|practical|care_condition|transport|coverage", priv))
else:
    check("O1 (skipped: run with --exports)", True)

print("— O2 the ingest carries both public switches into the package")
if EXPORTS:
    try:
        from PIL import Image
        import random
        exp, trial = tempfile.mkdtemp(prefix="pa-opp-exp-"), tempfile.mkdtemp(prefix="pa-opp-trial-")
        g = copy.deepcopy(shown)
        g["artist"]["open_for_commissions"] = True
        json.dump(g, open(os.path.join(exp, "gallery.json"), "w"))
        files = [i["file"] for w in g["works"] for i in w["images"]] + ([g["artist"]["portrait"]["file"]] if g["artist"].get("portrait") else [])
        for n, f in enumerate(files):
            random.seed(n)
            im = Image.new("RGB", (64, 48))
            im.putdata([(random.randrange(256), random.randrange(256), random.randrange(256)) for _ in range(64 * 48)])
            im.resize((3000, 2250), Image.NEAREST).save(os.path.join(exp, f), quality=90)
        code, out = run([sys.executable, os.path.join(HERE, "plotart-gallery-ingest.py"), exp, trial])
        pk = json.load(open(os.path.join(trial, g["artist"]["slug"], "package.json"))) if code == 0 else {}
        check("O2 a real export through the ingest: the package carries open_to (all seven) and open_for_commissions (the 13 Nov fix)",
              code == 0 and pk["artist"].get("open_to") == list(OPP.KEYS) and pk["artist"].get("open_for_commissions") is True, out[-400:])
        shutil.rmtree(exp, ignore_errors=True); shutil.rmtree(trial, ignore_errors=True)
    except ImportError:
        check("O2 (skipped: Pillow not available)", True)
else:
    check("O2 (skipped: run with --exports)", True)

print("— O3 every published gallery renders exactly as today")
M = main_module()
pkgs = sorted(glob.glob(os.path.join(ROOT, "plotart", "artists", "*", "gallery.json")))
same, diffs = 0, []
for f in pkgs:
    pkg = json.load(open(f))
    for ep in (None, ENDPOINT):
        a, b = pages(M, pkg, ep), pages(P, pkg, ep)
        for k in a:
            # Sprint 1 (founder approval 26 Nov 2026) moved an artwork page's button block (one line, class pa-aw-cta)
            # directly under the price and reworded its notes; everything else on the page must still match main exactly
            if k != "index":
                a[k], b[k] = (re.sub(r'(?m)^ *<div class="pa-aw-cta">.*\n', "", x) if x is not None else x for x in (a[k], b.get(k)))
                # SEO and analytics package (founder approval 26 Nov 2026, section 2.5): one added line, the two links
                # (size calculator, available artworks); nothing else may differ
                b[k] = b[k].replace("      " + P.MORE_LINKS + "\n", "", 1) if b.get(k) is not None else b.get(k)
            if a[k] == b.get(k) or (k == "index" and OPP.open_to(pkg)):   # 17 Nov 2026: pills change the gallery page of an artist who shows something
                same += 1
            else:
                diffs.append("%s/%s" % (pkg["artist"]["slug"], k))
published = [json.load(open(f)) for f in pkgs]
shown_now = [p for p in published if OPP.open_to(p)]
lines_ok = all((not p["artist"].get("open_to") or OPP.check_open_to(p["artist"]["open_to"])) and OPP.artist_line(p) in open(os.path.join(ROOT, "plotart", "artists", p["artist"]["slug"], "index.html"), encoding="utf-8").read()
               for p in shown_now)
check("O3a all %d published galleries: %d gallery and artwork pages byte-identical to main's renderer; the %d artists showing opportunities carry a valid open_to and exactly its \"Open to\" line"
      % (len(pkgs), same, len(shown_now)), len(pkgs) >= 5 and not diffs and lines_ok, diffs[:5])
base = json.load(open(os.path.join(ROOT, "plotart", "artists", "leah-hewson", "gallery.json")))
# A stable fixture (17 Nov 2026): a real published gallery, with the two settings this test turns on removed, so it is
# always "an artist who shows no opportunities and is not open for commissions", whatever that artist later chooses in
# PlotArt Studio. The live gallery is never touched.
base["artist"].pop("open_to", None)
base["artist"]["open_for_commissions"] = False
withp = copy.deepcopy(base)
withp["artist"]["open_to"] = ["exhibitions", "living_gallery", "commissions"]
A, B = pages(P, base, ENDPOINT), pages(P, withp, ENDPOINT)
line = ('<div class="pa-ag-opps"><p class="pa-ag-opps-h" id="agOppsH">Open to</p><ul class="pa-ag-pills" aria-labelledby="agOppsH">'
        '<li><a class="pa-ag-pill" href="../../opportunities/#exhibitions" data-pa-track="artist_opportunity_link">Exhibitions</a></li>'
        '<li><a class="pa-ag-pill" href="../../living-gallery.html#open-artists" data-pa-track="artist_opportunity_link">Living Gallery</a></li></ul></div>')
check("O3b with open_to the gallery page gains exactly one row of \"Open to\" pills, each linking to its list; Commissions chosen without \"Open for commissions\" is never shown", B["index"].count(line) == 1 and "Commissions" not in B["index"], B["index"][:0])
check("O3c removing the pills gives back exactly today's page; artwork pages are unchanged", B["index"].replace(line, "") == A["index"] and all(A[k] == B[k] for k in A if k != "index") and len(A) > 1)
both = copy.deepcopy(withp)
both["artist"]["open_for_commissions"] = True
bi = pages(P, both, ENDPOINT)["index"]
check("O3d with \"Open for commissions\" on, the Commissions pill appears once and the commission section once (never twice)", bi.count('href="../../commissions/" data-pa-track="artist_opportunity_link"') == 1 and bi.count(">Open for commissions</h2>") == 1 and "Living Gallery</a>" in bi)

print("— O4 the lists")
aoife = sample("aoife-sample", "Aoife Sample", "Painter", ["exhibitions", "living_gallery", "talks"])
brian = sample("brian-example", "Brian Example", "Ceramicist", ["art_for_hire", "venues"], ofc=True)
cara = sample("cara-preview", "Cara Preview", "Printmaker", ["living_gallery", "mobile_gallery", "commissions"])
dan = sample("dan-private", "Dan Private", "Sculptor")                            # kept private, or never chose
pk4 = [cara, dan, brian, aoife]
lg = [p["artist"]["slug"] for p in OPP.listed(pk4, "living_gallery")]
cm = [p["artist"]["slug"] for p in OPP.listed(pk4, "commissions")]
check("O4a Living Gallery lists exactly the artists who chose it, by surname (Preview before Sample)", lg == ["cara-preview", "aoife-sample"], lg)
check("O4b Commissions lists ONLY artists whose explicit \"Open for commissions\" switch is on (Brian), never one who only chose it (Cara)", cm == ["brian-example"], cm)
check("O4c an artist who shows nothing is in no list", all(dan not in OPP.listed(pk4, k) for k in OPP.KEYS))
try:
    OPP.listed(pk4 + [sample("eve-draft", "Eve Draft", "Painter", ["talks"], state="draft")], "talks")
    unappr = False
except OPP.Refused:
    unappr = True
check("O4d a package that is not approved is refused outright (never listed)", unappr)
cw = copy.deepcopy(cara); cw["artist"]["open_to"] = ["mobile_gallery"]
check("O4e withdrawing interest removes the artist from that list; unpublishing (no package) removes them from every list",
      "cara-preview" not in [p["artist"]["slug"] for p in OPP.listed([cw, aoife], "living_gallery")]
      and all("cara-preview" not in [p["artist"]["slug"] for p in OPP.listed([aoife, brian], k)] for k in OPP.KEYS))
site = tempfile.mkdtemp(prefix="pa-opp-site-")
shutil.copytree(os.path.join(ROOT, "plotart"), os.path.join(site, "plotart"))
for d in ("assets",):
    if os.path.isdir(os.path.join(ROOT, d)):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(site, d))
for fn in ("index.html", "privacy.html"):
    shutil.copyfile(os.path.join(ROOT, fn), os.path.join(site, fn))
before = {p: open(os.path.join(site, "plotart", p), encoding="utf-8").read() for p in OPP.PAGES}
def _cards_ok(doc, path):
    """Art for Hire (22 Nov 2026): the same listed artists as an artwork-led mini gallery. Every card: one link to the
    artist's gallery, the MAIN image of one of their own published works at a published size (never the portrait), with
    that image's approved alt text, lazy-loaded, and the file present; up to GALLERY_FIRST shown, the rest one click away."""
    base = "../" * path.count("/")
    cards = re.findall(r'<li><a class="pa-afg-card" href="([^"]+)" data-pa-track="opportunity_artist">(.*?)</a></li>', doc, re.S)
    key = "living_gallery" if path == "living-gallery.html" else "art_for_hire"
    want = OPP.listed(published, key)
    if len(cards) != len(want) or doc.count('class="pa-afg-grid"') != (1 if len(want) <= OPP.GALLERY_FIRST else 2):
        return False
    by = {p["artist"]["slug"]: p for p in published}
    for href, inner in cards:
        m = re.fullmatch(re.escape(base) + r"artists/([a-z0-9-]+)/", href)
        pk = m and by.get(m.group(1))
        img = re.search(r'<img src="([^"]+)" srcset="[^"]+" sizes="[^"]+" width="\d+" height="\d+" alt="([^"]+)" loading="lazy" decoding="async">', inner)
        if not pk or key not in OPP.open_to(pk) or not img or "portrait" in img.group(1):
            return False
        files = {base + "artists/%s/img/%s" % (pk["artist"]["slug"], d["file"]): i.get("alt")
                 for w in pk["works"] for i in w.get("images", []) if i.get("role") == "main" for d in i.get("derivatives", [])}
        if img.group(1) not in files or html.unescape(img.group(2)) != (files[img.group(1)] or "").strip() \
                or not os.path.isfile(os.path.join(ROOT, "plotart", os.path.normpath(os.path.join(os.path.dirname(path), img.group(1))))):
            return False
    return True
def _thumbs_ok(doc, path):
    if path in OPP.GALLERY_PAGES:
        return _cards_ok(doc, path)
    """Every listed row: a listed artist (open_to carries the key), linked as one row to their gallery, with an 80x80
    lazy-loaded thumbnail that is the smallest published derivative of a MAIN image of one of their own published works
    (never the portrait), with that image's approved alt text, and the file present."""
    base = "../" * path.count("/")
    rows = re.findall(r'<li><a class="pa-opp-row" href="([^"]+)" data-pa-track="opportunity_artist">(.*?)</a></li>', doc, re.S)
    if not rows:
        return False
    by = {p["artist"]["slug"]: p for p in published}
    for href, inner in rows:
        m = re.fullmatch(re.escape(base) + r"artists/([a-z0-9-]+)/(#commission)?", href)
        if m and m.group(2) and (path != OPP.COMMISSIONS or by.get(m.group(1), {}).get("artist", {}).get("open_for_commissions") is not True):
            return False   # only the Commissions page, and only for an artist whose Open for commissions is on, links to the commission enquiry
        pk = m and by.get(m.group(1))
        img = re.search(r'<img class="pa-opp-thumb" src="([^"]+)" alt="([^"]+)" width="80" height="80" loading="lazy" decoding="async">', inner)
        if not pk or not img or not OPP.open_to(pk) or "portrait" in img.group(1):
            return False
        mains = {base + "artists/%s/img/%s" % (pk["artist"]["slug"], min(i["derivatives"], key=lambda d: d["long_edge"])["file"]): i.get("alt")
                 for w in pk["works"] for i in w.get("images", []) if i.get("role") == "main" and i.get("derivatives")}
        if img.group(1) not in mains or html.unescape(img.group(2)) != (mains[img.group(1)] or "").strip() \
                or not os.path.isfile(os.path.join(ROOT, "plotart", os.path.normpath(os.path.join(os.path.dirname(path), img.group(1))))):
            return False
    return True
_ch = FEAT.choices(ROOT)   # the representative artworks the gallery page publishes (curated once, 26 Nov 2026)
live_ok = all(OPP.REGION.search(before[p]).group(0) == (OPP.BEGIN + ("\n" + OPP.content(p, published, _ch) + "\n" if OPP.content(p, published, _ch) else "") + OPP.END)
              for p in OPP.PAGES)
listed_keys = sum(1 for k in OPP.KEYS if OPP.listed(published, k))
check("O4f today: the four pages carry exactly the lists the published galleries produce (%d artists showing); every row is one link to the gallery with an approved artwork thumbnail (80x80, lazy, approved alt, never the portrait); unlisted kinds say so"
      % len(shown_now), live_ok and all(_thumbs_ok(before[p], p) for p in OPP.PAGES if OPP.content(p, published))
      and before[OPP.HUB].count("No artists are listed here yet.") == len(OPP.KEYS) - listed_keys)
for p in pk4:
    d = os.path.join(site, "plotart", "artists", p["artist"]["slug"])
    os.makedirs(d, exist_ok=True)
    json.dump(p, open(os.path.join(d, "gallery.json"), "w"), indent=1, sort_keys=True)
    for path, doc in P.gallery_pages(p, functools.partial(S.artist_page, hire_nav=True), enquiry_endpoint=ENDPOINT):
        open(os.path.join(site, "plotart", path), "w", encoding="utf-8").write(doc)
allp = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(site, "plotart", "artists", "*", "gallery.json")))]
OPP.refresh(site, allp)
after = {p: open(os.path.join(site, "plotart", p), encoding="utf-8").read() for p in OPP.PAGES}
check("O4g refreshing changes the four pages ONLY inside their region", all(OPP.outside(after[p]) == OPP.outside(before[p]) for p in OPP.PAGES))
regions = " ".join(OPP.REGION.search(after[p]).group(0) for p in OPP.PAGES)
check("O4h the regions name only published artists, link to their galleries, and contain nothing private",
      "Dan Private" not in regions and all('href="%sartists/%s/"' % ("../" * p.count("/"), s) in after[p]
          for p, s in (("living-gallery.html", "aoife-sample"), ("art-for-hire/index.html", "brian-example"), ("mobile-gallery/index.html", "cara-preview"), (OPP.HUB, "brian-example")))
      and not re.search(r"(?i)county|transport|courier|insurance box|@|practical note", re.sub(r"<[^>]+>", " ", regions)))
vis = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", regions)))
check("O4i the wording is interest, never participation or a booking", "Being listed is not a booking, and nothing is confirmed until it’s agreed." in vis
      and not re.search(r"(?i)participating artists|confirmed artists|book now|available now|partner", vis))
hire = after["art-for-hire/index.html"]
check("O4j Art for Hire (22 Nov 2026): the artists' mini gallery sits straight after the hero, apart from the works catalogue, which is unchanged; its introduction is the founder's wording and availability is agreed with the artist",
      hire.index("</section>") < hire.index(OPP.BEGIN) < hire.index("<!-- pa-hire-catalogue:begin -->") and "afh3-hero" in hire[:hire.index(OPP.BEGIN)]
      and OPP.HIRE_SAID in html.unescape(hire) and "Availability, rental terms and arrangements are agreed directly with the artist." in html.unescape(hire) and
      re.search(r"<!-- pa-hire-catalogue:begin -->.*?<!-- pa-hire-catalogue:end -->", hire, re.S).group(0) == re.search(r"<!-- pa-hire-catalogue:begin -->.*?<!-- pa-hire-catalogue:end -->", before["art-for-hire/index.html"], re.S).group(0))

print("— O5 the content-only boundary")
wt = tempfile.mkdtemp(prefix="pa-opp-wt-")
shutil.rmtree(wt)
run(["git", "worktree", "add", "-q", "--detach", wt, "HEAD"])
gitc = lambda *a: run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid"] + list(a), cwd=wt)
bnd = lambda b, r, *x: run([sys.executable, os.path.join(wt, "atlas-tools", "release", "plotart-content-boundary.py"), b, r] + list(x), cwd=wt)
try:
    base_sha = run(["git", "rev-parse", "HEAD"], cwd=wt)[1].strip()
    leah = json.load(open(os.path.join(wt, "plotart", "artists", "leah-hewson", "gallery.json")))
    leah["artist"]["open_to"] = ["exhibitions", "living_gallery"]
    json.dump(leah, open(os.path.join(wt, "plotart", "artists", "leah-hewson", "gallery.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, sort_keys=True)
    S.HIRE_NAV = True
    # only the gallery page gains the line: insert it exactly where the renderer puts it (the published page also carries
    # SEO regions the pipeline adds, so the page is edited, not regenerated)
    ip = os.path.join(wt, "plotart", "artists", "leah-hewson", "index.html")
    pg = open(ip, encoding="utf-8").read()
    anchor = re.search(r'<p class="pa-ag-meta">[^<]*</p>', pg)
    pg = pg[:anchor.end()] + OPP.artist_line(leah) + pg[anchor.end():]
    open(ip, "w", encoding="utf-8").write(pg)
    OPP.refresh(wt, [json.load(open(f)) for f in sorted(glob.glob(os.path.join(wt, "plotart", "artists", "*", "gallery.json")))])
    gitc("add", "-A", "plotart"); gitc("commit", "-q", "-m", "test: Leah shows two opportunities (instant)")
    c1, o1 = bnd(base_sha, "HEAD", "--instant")
    changed = run(["git", "diff", "--name-only", base_sha, "HEAD"], cwd=wt)[1].split()
    check("O5a an instant release (an artist starts showing opportunities) passes the content boundary: gallery page + the lists only",
          c1 == 0 and "CONTENT BOUNDARY · OK" in o1 and set(changed) <= {"plotart/artists/leah-hewson/index.html", "plotart/artists/leah-hewson/gallery.json"} | {"plotart/" + p for p in OPP.PAGES}
          and "plotart/living-gallery.html" in changed, o1[-400:] + str(changed))
    good = run(["git", "rev-parse", "HEAD"], cwd=wt)[1].strip()
    lgp = os.path.join(wt, "plotart", "living-gallery.html")
    doc = open(lgp, encoding="utf-8").read()
    assert '<p class="pa-eyebrow">For artists</p>' in doc
    open(lgp, "w", encoding="utf-8").write(doc.replace('<p class="pa-eyebrow">For artists</p>', '<p class="pa-eyebrow">For all artists</p>', 1))
    gitc("commit", "-qam", "tamper outside")
    c2, o2 = bnd(base_sha, "HEAD")
    gitc("reset", "-q", "--hard", good)
    _list = '<ul class="pa-afg-grid">' if '<ul class="pa-afg-grid">' in doc else '<ul class="pa-opp-list">'   # the Living Gallery shows its list as a gallery (22 Nov 2026)
    assert _list in doc
    open(lgp, "w", encoding="utf-8").write(doc.replace(_list, _list + '<li><a href="artists/invented/">Invented Artist</a></li>', 1))
    gitc("commit", "-qam", "tamper inside")
    c3, o3 = bnd(base_sha, "HEAD")
    gitc("reset", "-q", "--hard", good)
    hp = os.path.join(wt, "plotart", "art-for-hire", "index.html")
    hd = open(hp, encoding="utf-8").read()
    open(hp, "w", encoding="utf-8").write(hd.replace("<!-- pa-hire-catalogue:end -->", "<li class=\"pa-hire-card\" data-hire-work=\"wx\">x</li><!-- pa-hire-catalogue:end -->", 1))
    gitc("commit", "-qam", "tamper hire catalogue")
    c4, o4 = bnd(base_sha, "HEAD")
    check("O5b refused: a change outside the region, an invented artist inside it, and any change to the hire works catalogue",
          c2 == 1 and "differs from the exact opportunity lists" in o2 and c3 == 1 and "differs from the exact opportunity lists" in o3 and c4 == 1, (o2[-200:], o3[-200:], o4[-200:]))
    gitc("reset", "-q", "--hard", good)
    open(hp, "w", encoding="utf-8").write(hd.replace("<!-- pa-hire-catalogue:end -->", "<li class=\"pa-hire-card\" data-hire-work=\"wx\">x</li><!-- pa-hire-catalogue:end -->", 1))
    gitc("commit", "-qam", "hire catalogue change alone")
    c5, o5 = bnd(good, "HEAD", "--hire")
    check("O5c the Art for Hire catalogue keeps its own narrower boundary (a catalogue-only change passes --hire, untouched lists)", c5 == 0, o5[-300:])
finally:
    run(["git", "worktree", "remove", "--force", wt])

print("— O6 in a browser")
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
if sync_playwright is None:
    check("O6 (skipped: Playwright not available)", True)
else:
    for src in ("assets",):
        pass
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=site)
    http.server.SimpleHTTPRequestHandler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d/plotart/" % srv.server_address[1]
    targets = [("opportunities", OPP.HUB.replace("index.html", ""), None), ("living-gallery", "living-gallery.html", "#open-artists"),
               ("art-for-hire", "art-for-hire/", "#open-artists"), ("mobile-gallery", "mobile-gallery/", "#open-artists"),
               ("artist-page", "artists/aoife-sample/", ".pa-ag-hero, .pa-ag-id")]
    probs = []
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for w, h in ((1440, 900), (390, 844)):
            for name, path, sel in targets:
                pg = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=2 if SHOTS else 1)
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                r = pg.goto(url + path, wait_until="load")
                pg.wait_for_timeout(250)
                over = pg.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
                links = pg.eval_on_selector_all(".pa-opp-list a, .pa-ag-open a", "els => els.map(e => e.href)")
                for l in links:
                    rr = pg.request.get(l.split("#")[0])
                    if rr.status != 200:
                        probs.append("%s %s → %d" % (name, l, rr.status))
                if r.status != 200 or over or errs:
                    probs.append("%s %dpx: status %s overflow %s errors %s" % (name, w, r.status, over, errs))
                if SHOTS:
                    os.makedirs(SHOTS, exist_ok=True)
                    if sel and sel.startswith("#"):
                        pg.locator(sel).screenshot(path=os.path.join(SHOTS, "%s-list-%d.png" % (name, w)))
                    elif sel:
                        pg.locator("main").screenshot(path=os.path.join(SHOTS, "%s-%d.png" % (name, w)), clip=None) if False else \
                            pg.screenshot(path=os.path.join(SHOTS, "%s-top-%d.png" % (name, w)))
                    else:
                        pg.screenshot(path=os.path.join(SHOTS, "%s-%d.png" % (name, w)), full_page=True)
                pg.close()
        br.close()
    srv.shutdown()
    check("O6 the four pages and an artist page at 1440 and 390 px: load, no sideways scrolling, no script errors, every list link resolves", not probs, probs[:6])
shutil.rmtree(site, ignore_errors=True)

print("\nPLOTART OPPORTUNITY LISTS · %d checks, %d passed, %d failed" % (len(results), sum(results), len(results) - sum(results)))
sys.exit(0 if all(results) else 1)
