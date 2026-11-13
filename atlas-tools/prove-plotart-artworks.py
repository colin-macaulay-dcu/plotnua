#!/usr/bin/env python3
"""PROVE · the PlotArt artwork collection, plotart/artworks/ (SEO buyer-intent Phase 1, 13 Nov 2026). Read-only.

    python3 atlas-tools/prove-plotart-artworks.py [--against MAIN_COMMIT]

A1  the page is exactly what build-plotart-artworks.py makes from the approved public exports (no stale region)
A2  every published, AVAILABLE work appears exactly once; reserved, sold, not-for-sale and withdrawn works never do;
    an unapproved (draft) export is refused outright
A3  title, artist, medium (artist-supplied, verbatim), dimensions, price and image alt text match the export exactly
A4  every card links to its existing canonical artwork page and artist gallery; every image is an approved derivative
A5  structured data: CollectionPage + ItemList + BreadcrumbList, parses, numberOfItems = cards, item URLs = the
    artwork pages' own canonicals, and no Offer, price or availability claim
A6  head: title, one H1, index/follow + canonical exactly when its switch is on (noindex and no canonical otherwise)
A7  sitemap: unchanged while artworks_in_sitemap is off; exactly one entry, the canonical URL, when it is on
A8  synchronisation through the content pipeline's own functions: a sale, a withdrawal, a price change and a new
    gallery each change the region accordingly and nothing outside it
A9  the content-only boundary accepts exactly the regenerated region and refuses an edited intro, an injected work
    and a price that differs from the export
A10 fairness: works alternate between artists (no artist twice in a row while another still has works to show)
A11 no artist gallery, artwork page or Artists' Gallery page differs from main
"""
import copy, html, json, os, re, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import plotart_seo as SEO  # noqa: E402
import plotart_search_content as C  # noqa: E402
import plotart_gallery_pages as P  # noqa: E402

PATH = "artworks/index.html"
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, ("  [%s]" % str(detail)[:300]) if not ok and detail else ""))


def cards(doc):
    return re.findall(r'<li class="pa-coll-work">(.*?)</li>', doc, re.S)


def region(doc):
    return C.REGION.search(doc).group(0)


def ld(doc):
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', region(doc), re.S)
    return json.loads(m.group(1))


packages = SEO.public_packages(ROOT)
page = (ROOT / "plotart" / PATH).read_text()
launch = SEO.switches()

# A1
build = subprocess.run([sys.executable, str(HERE / "build-plotart-artworks.py"), "--check"], capture_output=True, text=True)
check("A1 the page matches its reviewed source and the current public exports", build.returncode == 0, build.stdout + build.stderr)
check("A1 the collection region is current (C.update is a no-op)", C.update(page, PATH, packages) == page)

# A2
available = [(p, w) for p in packages for w in p["works"] if w["availability"] == "available"]
hidden = [(p, w) for p in packages for w in p["works"] if w["availability"] != "available"]
found = cards(page)
hrefs = [re.search(r'<h3 class="pa-coll-title"><a href="([^"]+)"', c).group(1) for c in found]
want = ["../artists/%s/%s.html" % (p["artist"]["slug"], w["slug"]) for p, w in available]
check("A2 every available work appears exactly once (%d works)" % len(want), sorted(hrefs) == sorted(want) and len(set(hrefs)) == len(hrefs),
      set(want) ^ set(hrefs))
check("A2 no reserved, sold, not-for-sale or withdrawn work appears", not any("../artists/%s/%s.html" % (p["artist"]["slug"], w["slug"]) in hrefs for p, w in hidden))
for state in ("reserved", "sold", "not_for_sale", "withdrawn", "draft"):
    t = copy.deepcopy(packages)
    t[0]["works"][0]["availability"] = state
    gone = "../artists/%s/%s.html" % (t[0]["artist"]["slug"], t[0]["works"][0]["slug"])
    check("A2 a work marked %s leaves the collection" % state, gone not in C.content(PATH, t) and len(cards(C.content(PATH, t))) == len(want) - 1)
t = copy.deepcopy(packages)
t[0]["publication"]["state"] = "draft"
try:
    C.content(PATH, t)
    check("A2 an unapproved (draft) export is refused", False)
except ValueError:
    check("A2 an unapproved (draft) export is refused", True)

# A3
by_href = dict(zip(hrefs, found))
mism = []
for p, w in available:
    c = by_href.get("../artists/%s/%s.html" % (p["artist"]["slug"], w["slug"]), "")
    im = P.main_image(w)
    exp = [">%s</a></h3>" % html.escape(w["title"], quote=True), ">%s</a></p>" % html.escape(p["artist"]["display_name"], quote=True),
           '<p class="pa-coll-meta">%s<' % html.escape(w["medium"], quote=True), ">%s</span>" % html.escape(P.size_line(w)[0], quote=True),
           '<p class="pa-coll-price">%s</p>' % html.escape(P.price_line(w), quote=True), 'alt="%s"' % html.escape(im["alt"], quote=True)]
    miss = [e for e in exp if e not in c]
    if miss:
        mism.append((w["slug"], miss))
check("A3 title, artist, medium (verbatim), size, price and alt text match each export", not mism, mism[:3])
check("A3 prices shown are the exports' prices or 'Price on request' (no other amount)",
      sorted(re.findall(r'<p class="pa-coll-price">([^<]+)</p>', page)) == sorted(P.price_line(w) for _, w in available))

# A4
missing = [h for h in hrefs if not (ROOT / "plotart/artworks" / h).resolve().exists()]
check("A4 every card's link resolves to an existing artwork page", not missing, missing[:3])
canon_ok = []
for h in hrefs:
    target = (ROOT / "plotart/artworks" / h).resolve()
    m = re.findall(r'<link rel="canonical" href="([^"]+)"', target.read_text())
    canon_ok.append(m == [SEO.canonical(str(target.relative_to(ROOT / "plotart")))])
check("A4 each linked artwork page carries its own single canonical (the collection never competes with it)", all(canon_ok))
artist_links = set(re.findall(r'<p class="pa-coll-artist"><a href="([^"]+)"', page))
check("A4 every artist link resolves to a published gallery", all((ROOT / "plotart/artworks" / a / "index.html").resolve().exists() for a in artist_links))
derivs = {"../artists/%s/img/%s" % (p["artist"]["slug"], d["file"]) for p, w in available for i in w["images"] for d in i["derivatives"]}
srcs = set(re.findall(r'<img src="([^"]+)"', region(page))) | {s.split(" ")[0] for ss in re.findall(r'srcset="([^"]+)"', region(page)) for s in ss.split(", ")}
check("A4 every image is an approved derivative of the work's own export (no new or external image)", srcs <= derivs and all((ROOT / "plotart/artworks" / s).resolve().exists() for s in srcs), srcs - derivs)

# A5
try:
    data = ld(page)
    graph = {n["@type"]: n for n in data["@graph"]}
    items = graph["CollectionPage"]["mainEntity"]["itemListElement"]
    check("A5 structured data parses as CollectionPage + ItemList + BreadcrumbList", set(graph) == {"CollectionPage", "BreadcrumbList"} and graph["CollectionPage"]["mainEntity"]["@type"] == "ItemList")
    check("A5 numberOfItems equals the cards shown", graph["CollectionPage"]["mainEntity"]["numberOfItems"] == len(found) == len(items))
    check("A5 item URLs are the artwork pages' canonicals, in page order",
          [i["url"] for i in items] == [SEO.ORIGIN + h[3:] for h in hrefs] and [i["position"] for i in items] == list(range(1, len(items) + 1)))
    check("A5 the page URL is its own canonical", graph["CollectionPage"]["url"] == SEO.canonical(PATH))
    blob = json.dumps(data)
    check("A5 no Offer, price, availability or merchant claim in structured data", not re.search(r'"(?:Offer|price|priceCurrency|availability|offers|Product)"', blob))
except Exception as e:  # noqa: BLE001
    check("A5 structured data", False, e)

# A6
head = page.split("</head>")[0]
check("A6 the approved title", "<title>Original Irish Art for Sale | Buy Art from Irish Artists | PlotArt</title>" in head)
check("A6 exactly one H1, the approved heading", re.findall(r"<h1>(.*?)</h1>", page) == ["Discover original Irish art for sale."])
check("A6 one meta description of at most 160 characters", len(re.findall(r'<meta name="description" content="([^"]{1,160})">', head)) == 1)
if SEO.indexable(PATH, launch):
    check("A6 switched indexable: index, follow and the exact canonical", head.count('<meta name="robots" content="index, follow">') == 1
          and re.findall(r'<link rel="canonical" href="([^"]+)"', head) == ["https://plotnua.ie/plotart/artworks/"])
else:
    check("A6 not switched: noindex, follow and no canonical", '<meta name="robots" content="noindex, follow">' in head and "canonical" not in head)
off = dict(launch, artworks_indexable=False)
check("A6 with the switch off the page is noindex (indexable() honours artworks_indexable)", not SEO.indexable(PATH, off))

# A7
sm = (ROOT / "sitemap.xml").read_text()
on = dict(launch, artworks_indexable=True, artworks_in_sitemap=True)
check("A7 sitemap byte-identical while artworks_in_sitemap is off", SEO.update_sitemap(sm, packages, dict(launch, artworks_in_sitemap=False)) == sm)
added = SEO.update_sitemap(sm, packages, on)
check("A7 switched on: exactly one entry, the canonical collection URL", added.count("<loc>https://plotnua.ie/plotart/artworks/</loc>") == 1
      and len(added.splitlines()) == len(sm.splitlines()) + (0 if launch.get("artworks_in_sitemap") else 1))
check("A7 never listed while the page itself is not indexable", "plotart/artworks/" not in SEO.update_sitemap(sm, packages, dict(on, artworks_indexable=False)))


# A8 / A9: a temporary copy of the repository, changed only through the pipeline's own functions
def git(cwd, *a):
    return subprocess.run(("git",) + a, cwd=cwd, capture_output=True, text=True)


tmp = tempfile.mkdtemp(prefix="pa-artworks-")
subprocess.run("git -C %s archive HEAD | tar -x -C %s" % (ROOT, tmp), shell=True, check=True)
for a in (("init", "-q"), ("add", "-A"), ("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")):
    git(tmp, *a)
dest = Path(tmp) / "plotart" / PATH
base_doc = dest.read_text()
outside = C.outside(base_doc)


def pipeline_refresh(pkgs):
    for p in pkgs:
        Path(tmp, "plotart/artists", p["artist"]["slug"], "gallery.json").write_text(json.dumps(p, indent=1, ensure_ascii=False, sort_keys=True))
    C.refresh(tmp, SEO.public_packages(tmp))
    return dest.read_text()


def boundary():
    git(tmp, "add", "-A")
    git(tmp, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "change")
    r = subprocess.run([sys.executable, str(Path(tmp) / "atlas-tools/release/plotart-content-boundary.py"), "HEAD~1", "HEAD"], cwd=tmp, capture_output=True, text=True)
    return r.returncode == 0, r.stdout


work = copy.deepcopy(packages)
sold = work[0]["works"][0]
sold["availability"] = "sold"
doc = pipeline_refresh([work[0]])
check("A8 a sale removes the work from the collection on the next publication", "/%s.html" % sold["slug"] not in region(doc) and C.outside(doc) == outside)
ok, out = boundary()
check("A9 the content-only boundary accepts that regenerated region", ok, out)

rep = next(w for w in work[1]["works"] if w["availability"] == "available" and w.get("price_eur"))
rep["price_eur"] += 250
doc = pipeline_refresh([work[1]])
check("A8 a price change is reflected exactly", '<p class="pa-coll-price">%s</p>' % P.euro(rep["price_eur"]) in region(doc))
ok, out = boundary()
check("A9 ... and the boundary accepts it", ok, out)

gone = work[2]
gone_slug = gone["artist"]["slug"]
subprocess.run(["rm", "-rf", str(Path(tmp, "plotart/artists", gone_slug))])
C.refresh(tmp, SEO.public_packages(tmp))
doc = dest.read_text()
check("A8 a removed gallery's works all leave the collection", "../artists/%s/" % gone_slug not in region(doc))
git(tmp, "add", "-A"); git(tmp, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "remove")

doc = dest.read_text()
dest.write_text(doc.replace("Discover original Irish art for sale.", "Discover cheap Irish art for sale."))
ok, out = boundary()
check("A9 the boundary refuses an edited introduction (a code change)", not ok, out)
git(tmp, "reset", "-q", "--hard", "HEAD~1")

doc = dest.read_text()
fake = '<li class="pa-coll-work"><a class="pa-coll-art" href="../artists/x/y.html"><img src="../artists/x/img/y-600.webp" alt=""></a></li>'
dest.write_text(doc.replace('<ol class="pa-coll-grid" aria-label="Available artworks">', '<ol class="pa-coll-grid" aria-label="Available artworks">' + fake))
ok, out = boundary()
check("A9 the boundary refuses a work injected into the region", not ok, out)
git(tmp, "reset", "-q", "--hard", "HEAD~1")

doc = dest.read_text()
first = re.search(r'<p class="pa-coll-price">(€[\d,]+)</p>', doc).group(1)
dest.write_text(doc.replace('<p class="pa-coll-price">%s</p>' % first, '<p class="pa-coll-price">€1</p>', 1))
ok, out = boundary()
check("A9 the boundary refuses a price that differs from the export", not ok, out)
subprocess.run(["rm", "-rf", tmp])

# A10
order = [h.split("/")[2] for h in hrefs]
remaining = {a: order.count(a) for a in set(order)}
fair = True
for i in range(len(order) - 1):
    remaining[order[i]] -= 1
    if order[i] == order[i + 1] and any(n > 0 for a, n in remaining.items() if a != order[i]):
        fair = False
check("A10 works alternate between artists (no artist twice in a row while another still has works)", fair, order)

# A11 (development review only: needs the main commit to compare with, so it runs only when given one)
if "--against" in sys.argv:
    ref = sys.argv[sys.argv.index("--against") + 1]
    r = subprocess.run(["git", "diff", "--name-only", ref, "HEAD", "--", "plotart/artists", "plotart/gallery", "plotart/index.html"],
                       cwd=ROOT, capture_output=True, text=True)
    check("A11 no artist gallery, artwork page, Artists' Gallery or PlotArt homepage file differs from %s" % ref,
          r.returncode == 0 and r.stdout.strip() == "", r.stdout + r.stderr)
else:
    print("  ----  A11 not run (pass --against <main commit> to compare the galleries with main)")

print("PLOTART ARTWORKS · %d checks, %d passed, %d failed" % (len(results), sum(results), len(results) - sum(results)))
sys.exit(0 if all(results) else 1)
