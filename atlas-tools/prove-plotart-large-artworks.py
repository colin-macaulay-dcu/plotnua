#!/usr/bin/env python3
"""PROVE · PlotArt large artworks, plotart/large-artworks/ (SEO buyer-intent Phase 2, 13 Nov 2026). Read-only.

    python3 atlas-tools/prove-plotart-large-artworks.py [--against MAIN_COMMIT]

B1  the page is exactly what build-plotart-artworks.py makes from the approved public exports (no stale region)
B2  the threshold: every published, AVAILABLE work whose published height or width is 100 cm or more appears exactly
    once, and no other work does; exactly 100 cm is in, 99.9 cm is out, depth never counts; reserved, sold,
    not-for-sale and withdrawn works never appear; an unapproved (draft) export is refused
B3  title, artist, medium (verbatim), dimensions, price and alt text match each export exactly
B4  every card links to its existing canonical artwork page and artist gallery; every image is an approved derivative
B5  structured data: CollectionPage + ItemList + BreadcrumbList (PlotArt > Artworks > Large artworks), numberOfItems =
    cards, item URLs = artwork canonicals, no Offer, price or availability claim
B6  head: approved title, one H1, description <= 160 characters, index/canonical exactly when its switch is on
B7  sitemap: exactly the generated region for the switches; the entry appears only while large_artworks_in_sitemap and
    large_artworks_indexable are both on
B8  synchronisation through the pipeline's own functions: a sale, a price change and a work re-measured below 100 cm
    all change the region, and the content-only boundary accepts exactly those regions and refuses tampering
B9  no style classification by PlotArt: the page adds no "abstract" (or other style) label of its own
B10 no service claims: the page says PlotArt doesn't take payment, deliver or install, and never offers delivery,
    installation, consultancy or purchasing services; it links to the art size calculator
B11 fairness: works alternate between artists while more than one artist still has works to show
B12 (--against MAIN) the All Available Artworks page, its stylesheet, every artist page and every other PlotArt page are
    byte-identical to main
"""
import copy, html, json, re, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import plotart_seo as SEO  # noqa: E402
import plotart_search_content as C  # noqa: E402
import plotart_gallery_pages as P  # noqa: E402

PATH = "large-artworks/index.html"
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, ("  [%s]" % str(detail)[:300]) if not ok and detail else ""))


cards = lambda doc: re.findall(r'<li class="pa-coll-work">(.*?)</li>', doc, re.S)
region = lambda doc: C.REGION.search(doc).group(0)
hrefs_of = lambda doc: [re.search(r'<h3 class="pa-coll-title"><a href="([^"]+)"', c).group(1) for c in cards(doc)]
url_of = lambda p, w: "../artists/%s/%s.html" % (p["artist"]["slug"], w["slug"])

packages = SEO.public_packages(ROOT)
page = (ROOT / "plotart" / PATH).read_text()
launch = SEO.switches()

# B1
build = subprocess.run([sys.executable, str(HERE / "build-plotart-artworks.py"), "--check"], capture_output=True, text=True)
check("B1 the page matches its reviewed source and the current public exports", build.returncode == 0, build.stdout + build.stderr)
check("B1 the collection region is current", C.update(page, PATH, packages) == page)

# B2
big = lambda w: max(w["h_cm"], w["w_cm"]) >= 100
want = [url_of(p, w) for p in packages for w in p["works"] if w["availability"] == "available" and big(w)]
small = [url_of(p, w) for p in packages for w in p["works"] if w["availability"] == "available" and not big(w)]
other = [url_of(p, w) for p in packages for w in p["works"] if w["availability"] != "available"]
hrefs = hrefs_of(page)
check("B2 every available work of 100 cm or more appears exactly once (%d works)" % len(want), sorted(hrefs) == sorted(want) and len(set(hrefs)) == len(hrefs), set(want) ^ set(hrefs))
check("B2 no available work under 100 cm appears (%d excluded)" % len(small), not set(hrefs) & set(small))
check("B2 no reserved, sold, not-for-sale or withdrawn work appears", not set(hrefs) & set(other))
sizes = {}
for p in packages:
    for w in p["works"]:
        sizes[url_of(p, w)] = max(w["h_cm"], w["w_cm"])
check("B2 every included work is 100 cm or more on its longest published side", all(sizes[h] >= 100 for h in hrefs), [(h, sizes[h]) for h in hrefs if sizes[h] < 100])


def one_off(change):
    t = copy.deepcopy(packages)
    w = next(w for p in t for w in p["works"] if w["availability"] == "available")
    p = next(p for p in t if w in p["works"])
    change(w)
    return url_of(p, w) in C.content(PATH, t)


check("B2 a work of exactly 100 cm is included", one_off(lambda w: w.update(h_cm=100, w_cm=40, d_cm=3)))
check("B2 a work of 99.9 cm is excluded", not one_off(lambda w: w.update(h_cm=99.9, w_cm=99.9, d_cm=3)))
check("B2 depth never counts (50 × 50 × 120 cm is excluded)", not one_off(lambda w: w.update(h_cm=50, w_cm=50, d_cm=120)))
check("B2 the width counts as well as the height (40 × 160 cm is included)", one_off(lambda w: w.update(h_cm=40, w_cm=160)))
for state in ("reserved", "sold", "not_for_sale", "withdrawn"):
    check("B2 a large work marked %s leaves the page" % state, not one_off(lambda w, s=state: w.update(h_cm=150, availability=s)))
t = copy.deepcopy(packages)
t[0]["publication"]["state"] = "draft"
try:
    C.content(PATH, t)
    check("B2 an unapproved (draft) export is refused", False)
except ValueError:
    check("B2 an unapproved (draft) export is refused", True)

# B3
by = dict(zip(hrefs, cards(page)))
mism = []
for p in packages:
    for w in p["works"]:
        c = by.get(url_of(p, w))
        if c is None:
            continue
        exp = [">%s</a></h3>" % html.escape(w["title"], quote=True), ">%s</a></p>" % html.escape(p["artist"]["display_name"], quote=True),
               '<p class="pa-coll-meta">%s<' % html.escape(w["medium"], quote=True), ">%s</span>" % html.escape(P.size_line(w)[0], quote=True),
               '<p class="pa-coll-price">%s</p>' % html.escape(P.price_line(w), quote=True), 'alt="%s"' % html.escape(P.main_image(w)["alt"], quote=True)]
        miss = [e for e in exp if e not in c]
        if miss:
            mism.append((w["slug"], miss))
check("B3 title, artist, medium (verbatim), size, price and alt text match each export", not mism, mism[:2])

# B4
base = ROOT / "plotart" / "large-artworks"
check("B4 every artwork link resolves to an existing artwork page", all((base / h).resolve().exists() for h in hrefs))
canon = [re.findall(r'<link rel="canonical" href="([^"]+)"', (base / h).resolve().read_text()) == [SEO.ORIGIN + h[3:]] for h in hrefs]
check("B4 each artwork page keeps its own single canonical", all(canon))
artist_links = set(re.findall(r'<p class="pa-coll-artist"><a href="([^"]+)"', page))
check("B4 every artist link resolves to a published gallery", all((base / a / "index.html").resolve().exists() for a in artist_links))
derivs = {"../artists/%s/img/%s" % (p["artist"]["slug"], d["file"]) for p in packages for w in p["works"] for i in w["images"] for d in i["derivatives"]}
srcs = set(re.findall(r'<img src="([^"]+)"', region(page))) | {x.split(" ")[0] for ss in re.findall(r'srcset="([^"]+)"', region(page)) for x in ss.split(", ")}
check("B4 every image is an approved derivative that exists (no new image)", srcs <= derivs and all((base / s).resolve().exists() for s in srcs), srcs - derivs)
other_links = [l for l in re.findall(r'href="(\.\./[^"#]+)"', page.split('<main', 1)[1].split('</main>')[0])]
check("B4 every other link in the page body resolves", all((base / (l + ("index.html" if l.endswith("/") else ""))).resolve().exists() for l in other_links),
      [l for l in other_links if not (base / (l + ("index.html" if l.endswith("/") else ""))).resolve().exists()])

# B5
data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', region(page), re.S).group(1))
g = {n["@type"]: n for n in data["@graph"]}
items = g["CollectionPage"]["mainEntity"]["itemListElement"]
check("B5 CollectionPage + ItemList + BreadcrumbList", set(g) == {"CollectionPage", "BreadcrumbList"} and g["CollectionPage"]["mainEntity"]["@type"] == "ItemList")
check("B5 numberOfItems equals the cards", g["CollectionPage"]["mainEntity"]["numberOfItems"] == len(hrefs) == len(items))
check("B5 item URLs are the artwork canonicals, in page order", [i["url"] for i in items] == [SEO.ORIGIN + h[3:] for h in hrefs])
check("B5 breadcrumb: PlotArt > Artworks > Large artworks, canonical URLs",
      [(i["name"], i["item"]) for i in g["BreadcrumbList"]["itemListElement"]] ==
      [("PlotArt", SEO.ORIGIN), ("Artworks", SEO.ORIGIN + "artworks/"), ("Large artworks", SEO.ORIGIN + "large-artworks/")])
check("B5 no Offer, price, availability or merchant claim", not re.search(r'"(?:Offer|price|priceCurrency|availability|offers|Product)"', json.dumps(data)))

# B6
head = page.split("</head>")[0]
check("B6 the approved title", "<title>Large Original Paintings &amp; Artworks for Sale in Ireland | PlotArt</title>" in head)
check("B6 exactly one H1, the approved heading", re.findall(r"<h1>(.*?)</h1>", page) == ["Large original artworks for sale in Ireland."])
check("B6 one meta description of at most 160 characters", len(re.findall(r'<meta name="description" content="([^"]{1,160})">', head)) == 1)
if SEO.indexable(PATH, launch):
    check("B6 switched indexable: index, follow and the exact canonical", head.count('<meta name="robots" content="index, follow">') == 1
          and re.findall(r'<link rel="canonical" href="([^"]+)"', head) == ["https://plotnua.ie/plotart/large-artworks/"])
else:
    check("B6 not switched: noindex, follow and no canonical", '<meta name="robots" content="noindex, follow">' in head and "canonical" not in head)
check("B6 the large page has its own switch (artworks' switch does not control it)",
      not SEO.indexable(PATH, dict(launch, large_artworks_indexable=False, artworks_indexable=True)) and SEO.indexable(PATH, dict(launch, large_artworks_indexable=True, artworks_indexable=False)))

# B7
sm = (ROOT / "sitemap.xml").read_text()
entry = "  <url><loc>https://plotnua.ie/plotart/large-artworks/</loc></url>\n"
listed = SEO.indexable(PATH, launch) and launch.get("large_artworks_in_sitemap") is True
check("B7 sitemap.xml is exactly the generated region for the current switches", SEO.update_sitemap(sm, packages, launch) == sm)
check("B7 the large page is listed %s" % ("once" if listed else "not yet (switch off)"), sm.count("plotart/large-artworks/") == (1 if listed else 0))
on = dict(launch, large_artworks_indexable=True, large_artworks_in_sitemap=True)
check("B7 switched on: exactly one added entry, nothing else changes",
      SEO.update_sitemap(sm, packages, on).replace(entry, "") == SEO.update_sitemap(sm, packages, dict(on, large_artworks_in_sitemap=False))
      and SEO.update_sitemap(sm, packages, on).count(entry) == 1)
check("B7 never listed while the page is not indexable", "large-artworks" not in SEO.update_sitemap(sm, packages, dict(on, large_artworks_indexable=False)))


# B8 (a temporary copy; changes only through the pipeline's own functions)
def git(cwd, *a):
    return subprocess.run(("git",) + a, cwd=cwd, capture_output=True, text=True)


tmp = tempfile.mkdtemp(prefix="pa-large-")
subprocess.run("git -C %s archive HEAD | tar -x -C %s" % (ROOT, tmp), shell=True, check=True)
for a in (("init", "-q"), ("add", "-A"), ("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")):
    git(tmp, *a)
dest = Path(tmp, "plotart", PATH)
outside = C.outside(dest.read_text())


def refresh(pkg):
    Path(tmp, "plotart/artists", pkg["artist"]["slug"], "gallery.json").write_text(json.dumps(pkg, indent=1, ensure_ascii=False, sort_keys=True))
    C.refresh(tmp, SEO.public_packages(tmp))
    return dest.read_text()


def boundary():
    git(tmp, "add", "-A")
    git(tmp, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "change")
    r = subprocess.run([sys.executable, str(Path(tmp, "atlas-tools/release/plotart-content-boundary.py")), "HEAD~1", "HEAD"], cwd=tmp, capture_output=True, text=True)
    return r.returncode == 0, r.stdout


work = copy.deepcopy(packages)
pk = next(p for p in work if sum(1 for w in p["works"] if w["availability"] == "available" and big(w) and w.get("price_eur")) >= 2)
w = next(w for w in pk["works"] if w["availability"] == "available" and big(w))
w["availability"] = "sold"
doc = refresh(pk)
check("B8 a sale removes the large work on the next publication", url_of(pk, w) not in region(doc) and C.outside(doc) == outside)
ok, out = boundary()
check("B8 ... and the content-only boundary accepts the regenerated regions", ok, out)
w2 = next(x for x in pk["works"] if x["availability"] == "available" and big(x) and x.get("price_eur"))
w2["price_eur"] += 300
doc = refresh(pk)
check("B8 a price change is reflected exactly", '<p class="pa-coll-price">%s</p>' % P.euro(w2["price_eur"]) in region(doc))
ok, out = boundary()
check("B8 ... and the boundary accepts it", ok, out)
w2["h_cm"], w2["w_cm"] = 60, 80
doc = refresh(pk)
check("B8 a work re-measured below 100 cm leaves the large page but stays in All Available Artworks",
      url_of(pk, w2) not in region(doc) and url_of(pk, w2) in Path(tmp, "plotart/artworks/index.html").read_text())
ok, out = boundary()
check("B8 ... and the boundary accepts it", ok, out)
doc = dest.read_text()
dest.write_text(doc.replace('<ol class="pa-coll-grid" aria-label="Available large artworks">',
                            '<ol class="pa-coll-grid" aria-label="Available large artworks"><li class="pa-coll-work"><a href="../artists/x/y.html">x</a></li>'))
ok, out = boundary()
check("B8 the boundary refuses a work injected into the region", not ok, out)
git(tmp, "reset", "-q", "--hard", "HEAD~1")
doc = dest.read_text()
dest.write_text(doc.replace("Large original artworks for sale in Ireland.", "Huge bargain paintings."))
ok, out = boundary()
check("B8 the boundary refuses an edited introduction (a code change)", not ok, out)
subprocess.run(["rm", "-rf", tmp])

# B9
no_alt = re.sub(r'alt="[^"]*"', "", region(page))
own_text = re.sub(r'<p class="pa-coll-meta">.*?</p>|<h3 class="pa-coll-title">.*?</h3>', "", no_alt, flags=re.S)
outside_text = re.sub(r"<[^>]+>", " ", C.outside(page))
check("B9 the page adds no style label of its own (abstract, figurative, landscape...)",
      not re.search(r"\b(abstract|figurative|landscape|portrait|expressionis\w*|minimalis\w*)\b", re.sub(r"<[^>]+>", " ", own_text) + " " + outside_text, re.I))

# B10
vis = re.sub(r"\s+", " ", html.unescape(re.sub(r"<script.*?</script>|<[^>]+>", " ", page.split("<main", 1)[1].split("</main>")[0], flags=re.S)))
check("B10 says PlotArt doesn't take payment, deliver or install artwork", "It doesn’t take payment, deliver or install artwork" in vis)
check("B10 no delivery, installation, consultancy or purchasing service is offered",
      not re.search(r"\b(?:we|PlotArt) (?:deliver|install|arrange|advise|curate|source|consult)|our (?:delivery|installation|consultan|advisory|curation)|free delivery|book a consultation|buy now|add to (?:cart|basket)", vis, re.I))
check("B10 links to the art size calculator", 'href="../art-size-calculator.html"' in page)

# B11
order = [h.split("/")[2] for h in hrefs]
left = {a: order.count(a) for a in set(order)}
fair = True
for i in range(len(order) - 1):
    left[order[i]] -= 1
    if order[i] == order[i + 1] and any(n > 0 for a, n in left.items() if a != order[i]):
        fair = False
check("B11 works alternate between artists", fair, order)

# B12
if "--against" in sys.argv:
    ref = sys.argv[sys.argv.index("--against") + 1]
    r = subprocess.run(["git", "diff", "--name-only", ref, "HEAD", "--", "plotart"], cwd=ROOT, capture_output=True, text=True)
    changed = [x for x in r.stdout.split() if x]
    check("B12 only plotart/large-artworks/index.html is new under plotart/; All Available Artworks, its stylesheet, artist pages "
          "and every other PlotArt page are byte-identical to %s" % ref, r.returncode == 0 and changed == ["plotart/large-artworks/index.html"], changed)
else:
    print("  ----  B12 not run (pass --against <main commit>)")

print("PLOTART LARGE ARTWORKS · %d checks, %d passed, %d failed" % (len(results), sum(results), len(results) - sum(results)))
sys.exit(0 if all(results) else 1)
