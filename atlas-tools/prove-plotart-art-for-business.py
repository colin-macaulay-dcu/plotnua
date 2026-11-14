#!/usr/bin/env python3
"""PROVE · PlotArt art for business, plotart/art-for-business/ (SEO commercial Phase 3, 14 Nov 2026). Read-only.

    python3 atlas-tools/prove-plotart-art-for-business.py [--against MAIN_COMMIT]

F1  the page is exactly what build-plotart-artworks.py makes from the approved public exports (no stale region)
F2  the selection: the first eight works of the large collection's fair rotation -- published, AVAILABLE, 100 cm or
    more -- each once; fewer only when fewer exist; reserved, sold, not-for-sale and withdrawn works never appear; no
    artist appears twice before every artist with a large work has appeared once; a draft export is refused
F3  title, artist, medium (verbatim), dimensions, price and alt text match each export exactly
F4  every card links to its canonical artwork page and artist gallery; every image is an approved derivative whose
    width/height are that derivative's own pixels (proportions kept, nothing cropped)
F5  structured data: CollectionPage + ItemList + BreadcrumbList (PlotArt > Art for business); no Offer or price claim
F6  head: approved title, one H1, description <= 160 characters, index/canonical exactly when its own switch is on
F7  sitemap: listed only while art_for_business_in_sitemap and art_for_business_indexable are both on; one entry
F8  synchronisation through the pipeline's own functions: a sale replaces the work on the next publication and a price
    change is reflected; the content-only boundary accepts exactly those regions and refuses tampering
F9  no service claims: PlotArt is said not to take payment, source, deliver, install or advise; no consultancy,
    curation, procurement, delivery, installation, managed or corporate-programme offer; no tax or allowance wording
F10 existing enquiry routes only: no form, basket, shortlist or multi-artist enquiry on the page
F11 useful, not duplicated or stuffed: at most 8 works (fewer than the large collection), substantive practical copy,
    no repeated sentence, limited repetition of the target phrases
F12 navigation unchanged: the header is the shared PlotArt header, and no page links here except this page and the
    three discreet contextual links (All Available Artworks, Large Artworks, the buying guide)
F13 (--against MAIN) under plotart/ only the new page, the shared collection stylesheet and the three linked pages
    change; each linked page differs only by its one link; no artist page, Studio, Worker or enquiry code changes
"""
import copy, html, json, re, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import plotart_seo as SEO  # noqa: E402
import plotart_search_content as C  # noqa: E402
import plotart_gallery_pages as P  # noqa: E402

PATH = "art-for-business/index.html"
LIMIT = 8
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, ("  [%s]" % str(detail)[:300]) if not ok and detail else ""))


cards = lambda doc: re.findall(r'<li class="pa-coll-work">(.*?)</li>', doc, re.S)
region = lambda doc: C.REGION.search(doc).group(0)
hrefs_of = lambda doc: [re.search(r'<h3 class="pa-coll-title"><a href="([^"]+)"', c).group(1) for c in cards(doc)]
url_of = lambda p, w: "../artists/%s/%s.html" % (p["artist"]["slug"], w["slug"])
big = lambda w: max(w["h_cm"], w["w_cm"]) >= 100

packages = SEO.public_packages(ROOT)
page = (ROOT / "plotart" / PATH).read_text()
launch = SEO.switches()
body = page.split("<main", 1)[1].split("</main>")[0]
vis = re.sub(r"\s+", " ", html.unescape(re.sub(r"<script.*?</script>|<[^>]+>", " ", body, flags=re.S)))

# F1
build = subprocess.run([sys.executable, str(HERE / "build-plotart-artworks.py"), "--check"], capture_output=True, text=True)
check("F1 the page matches its reviewed source and the current public exports", build.returncode == 0, build.stdout + build.stderr)
check("F1 the selection region is current", C.update(page, PATH, packages) == page)

# F2 (independent of the module: recomputed here from the exports)
large = [(p, w) for p in packages for w in p["works"] if w["availability"] == "available" and big(w)]
hrefs = hrefs_of(page)
check("F2 %d works shown (the first %d of %d available large works)" % (len(hrefs), LIMIT, len(large)), len(hrefs) == min(LIMIT, len(large)))
check("F2 every work shown is published, available and 100 cm or more", set(hrefs) <= {url_of(p, w) for p, w in large})
check("F2 no work appears twice", len(set(hrefs)) == len(hrefs))
check("F2 no reserved, sold, not-for-sale or withdrawn work appears",
      not set(hrefs) & {url_of(p, w) for p in packages for w in p["works"] if w["availability"] != "available"})
check("F2 the selection is the start of the large collection's own fair order",
      hrefs == [h for h in hrefs_of((ROOT / "plotart/large-artworks/index.html").read_text())][:LIMIT])
with_large = {p["artist"]["slug"] for p, _ in large}
order = [h.split("/")[2] for h in hrefs]
first_round = order[:len(with_large)]
check("F2 each artist with a large work appears once before any artist appears twice",
      len(set(first_round)) == len(first_round) and (len(order) < len(with_large) or set(first_round) == with_large), order)
count = re.search(r'<p class="pa-coll-count">([^<]+)</p>', page).group(1)
check("F2 the count states the selection honestly", count == "A selection of %d large works by %d artists, from %d available" % (
    len(hrefs), len(set(order)), len(large)), count)
for state in ("reserved", "sold", "not_for_sale", "withdrawn"):
    t = copy.deepcopy(packages)
    p0 = next(p for p in t if any(url_of(p, w) == hrefs[0] for w in p["works"]))
    w0 = next(w for w in p0["works"] if url_of(p0, w) == hrefs[0])
    w0["availability"] = state
    out = C.content(PATH, t)
    check("F2 a selected work marked %s leaves the page and another available work takes its place" % state,
          hrefs[0] not in out and len(re.findall(r'<li class="pa-coll-work">', out)) == min(LIMIT, len(large) - 1))
t = copy.deepcopy(packages)
t[0]["publication"]["state"] = "draft"
try:
    C.content(PATH, t)
    check("F2 an unapproved (draft) export is refused", False)
except ValueError:
    check("F2 an unapproved (draft) export is refused", True)

# F3
by = dict(zip(hrefs, cards(page)))
mism = []
for p, w in large:
    c = by.get(url_of(p, w))
    if c is None:
        continue
    exp = [">%s</a></h3>" % html.escape(w["title"], quote=True), ">%s</a></p>" % html.escape(p["artist"]["display_name"], quote=True),
           '<p class="pa-coll-meta">%s<' % html.escape(w["medium"], quote=True), ">%s</span>" % html.escape(P.size_line(w)[0], quote=True),
           '<p class="pa-coll-price">%s</p>' % html.escape(P.price_line(w), quote=True), 'alt="%s"' % html.escape(P.main_image(w)["alt"], quote=True)]
    miss = [e for e in exp if e not in c]
    if miss:
        mism.append((w["slug"], miss))
check("F3 title, artist, medium (verbatim), size, price and alt text match each export", not mism, mism[:2])
photo = [(p, w) for p, w in large if url_of(p, w) in by and P.main_image(w).get("photo_credit")]
check("F3 every photograph credit is carried (%d)" % len(photo), all(("Photograph: " + html.escape(P.main_image(w)["photo_credit"], quote=True)) in by[url_of(p, w)] for p, w in photo))

# F4
base = ROOT / "plotart" / "art-for-business"
check("F4 every artwork link resolves to an existing artwork page", all((base / h).resolve().exists() for h in hrefs))
artist_links = set(re.findall(r'<p class="pa-coll-artist"><a href="([^"]+)"', page))
check("F4 every artist link resolves to a published gallery", artist_links and all((base / a / "index.html").resolve().exists() for a in artist_links))
derivs = {"../artists/%s/img/%s" % (p["artist"]["slug"], d["file"]): tuple(d["pixels"]) for p in packages for w in p["works"] for i in w["images"] for d in i["derivatives"]}
imgs = re.findall(r'<img src="([^"]+)" srcset="([^"]+)"[^>]*? width="(\d+)" height="(\d+)"', region(page))
srcs = {s for s, *_ in imgs} | {x.split(" ")[0] for _, ss, *_ in imgs for x in ss.split(", ")}
check("F4 every image is an approved derivative that exists (no new image)", srcs <= set(derivs) and all((base / s).resolve().exists() for s in srcs), srcs - set(derivs))
check("F4 every image keeps its own proportions (width/height are the derivative's pixels)",
      len(imgs) == len(hrefs) and all(derivs.get(s) == (int(wd), int(ht)) for s, _, wd, ht in imgs))
css = (ROOT / "plotart/assets/plotart-artworks.css").read_text()
check("F4 no crop: the collection images are never object-fit or fixed to both dimensions", "object-fit" not in css and ".pa-coll-art img{width:auto;height:auto;" in css)
other_links = re.findall(r'href="(\.\./[^"#]+)"', body)
check("F4 every other link in the page body resolves", all((base / (l + ("index.html" if l.endswith("/") else ""))).resolve().exists() for l in other_links),
      [l for l in other_links if not (base / (l + ("index.html" if l.endswith("/") else ""))).resolve().exists()])
for target in ("../large-artworks/", "../artworks/", "../gallery/", "../buy-original-art-ireland.html", "../art-size-calculator.html"):
    check("F4 links to %s" % target, ('href="%s"' % target) in body)

# F5
data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', region(page), re.S).group(1))
g = {n["@type"]: n for n in data["@graph"]}
items = g["CollectionPage"]["mainEntity"]["itemListElement"]
check("F5 CollectionPage + ItemList + BreadcrumbList", set(g) == {"CollectionPage", "BreadcrumbList"} and g["CollectionPage"]["mainEntity"]["@type"] == "ItemList")
check("F5 numberOfItems equals the cards", g["CollectionPage"]["mainEntity"]["numberOfItems"] == len(hrefs) == len(items))
check("F5 item URLs are the artwork canonicals, in page order", [i["url"] for i in items] == [SEO.ORIGIN + h[3:] for h in hrefs])
check("F5 breadcrumb: PlotArt > Art for business",
      [(i["name"], i["item"]) for i in g["BreadcrumbList"]["itemListElement"]] == [("PlotArt", SEO.ORIGIN), ("Art for business", SEO.ORIGIN + "art-for-business/")])
check("F5 no Offer, Service, price, availability or merchant claim",
      not re.search(r'"(?:Offer|Service|LocalBusiness|price|priceCurrency|availability|offers|Product)"', json.dumps(data)))
check("F5 no other structured data on the page", page.count("application/ld+json") == 1)

# F6
head = page.split("</head>")[0]
check("F6 the approved title", "<title>Original Art for Offices &amp; Businesses in Ireland | PlotArt</title>" in head)
check("F6 exactly one H1, the approved heading", re.findall(r"<h1>(.*?)</h1>", page) == ["Original art for workplaces in Ireland."])
check("F6 one meta description of at most 160 characters", len(re.findall(r'<meta name="description" content="([^"]{1,160})">', head)) == 1)
check("F6 Open Graph and Twitter titles match", head.count('content="Original Art for Offices &amp; Businesses in Ireland | PlotArt"') == 2)
if SEO.indexable(PATH, launch):
    check("F6 switched indexable: index, follow and the exact canonical", head.count('<meta name="robots" content="index, follow">') == 1
          and re.findall(r'<link rel="canonical" href="([^"]+)"', head) == ["https://plotnua.ie/plotart/art-for-business/"]
          and '<meta property="og:url" content="https://plotnua.ie/plotart/art-for-business/">' in head)
else:
    check("F6 not switched: noindex, follow and no canonical", '<meta name="robots" content="noindex, follow">' in head and "canonical" not in head)
check("F6 the page has its own switch (other collections' switches do not control it)",
      not SEO.indexable(PATH, dict(launch, art_for_business_indexable=False, large_artworks_indexable=True, artworks_indexable=True))
      and SEO.indexable(PATH, dict(launch, art_for_business_indexable=True, large_artworks_indexable=False, artworks_indexable=False)))

# F7
sm = (ROOT / "sitemap.xml").read_text()
entry = "  <url><loc>https://plotnua.ie/plotart/art-for-business/</loc></url>\n"
listed = SEO.indexable(PATH, launch) and launch.get("art_for_business_in_sitemap") is True
check("F7 sitemap.xml is exactly the generated region for the current switches", SEO.update_sitemap(sm, packages, launch) == sm)
check("F7 the page is listed %s" % ("once" if listed else "not yet (switch off until release approval)"), sm.count("plotart/art-for-business/") == (1 if listed else 0))
on = dict(launch, art_for_business_indexable=True, art_for_business_in_sitemap=True)
check("F7 switched on: exactly one added entry, nothing else changes",
      SEO.update_sitemap(sm, packages, on).count(entry) == 1
      and SEO.update_sitemap(sm, packages, on).replace(entry, "") == SEO.update_sitemap(sm, packages, dict(on, art_for_business_in_sitemap=False)))
check("F7 never listed while the page is not indexable", "art-for-business" not in SEO.update_sitemap(sm, packages, dict(on, art_for_business_indexable=False)))


# F8 (a temporary copy; changes only through the pipeline's own functions)
def git(cwd, *a):
    return subprocess.run(("git",) + a, cwd=cwd, capture_output=True, text=True)


tmp = tempfile.mkdtemp(prefix="pa-biz-")
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
pk = next(p for p in work if any(url_of(p, w) == hrefs[0] for w in p["works"]))
w = next(w for w in pk["works"] if url_of(pk, w) == hrefs[0])
w["availability"] = "sold"
doc = refresh(pk)
check("F8 a sale removes the selected work on the next publication, outside the region unchanged",
      url_of(pk, w) not in region(doc) and C.outside(doc) == outside and len(cards(doc)) == min(LIMIT, len(large) - 1))
ok, out = boundary()
check("F8 ... and the content-only boundary accepts the regenerated regions", ok, out)
sel = hrefs_of(doc)
pk2 = next(p for p in work if any(url_of(p, x) in sel and x.get("price_eur") for x in p["works"]))
w2 = next(x for x in pk2["works"] if url_of(pk2, x) in sel and x.get("price_eur"))
w2["price_eur"] += 300
doc = refresh(pk2)
check("F8 a price change is reflected exactly", '<p class="pa-coll-price">%s</p>' % P.euro(w2["price_eur"]) in region(doc))
ok, out = boundary()
check("F8 ... and the boundary accepts it", ok, out)
doc = dest.read_text()
dest.write_text(doc.replace('<ol class="pa-coll-grid" aria-label="A selection of available large artworks">',
                            '<ol class="pa-coll-grid" aria-label="A selection of available large artworks"><li class="pa-coll-work"><a href="../artists/x/y.html">x</a></li>'))
ok, out = boundary()
check("F8 the boundary refuses a work injected into the region", not ok, out)
git(tmp, "reset", "-q", "--hard", "HEAD~1")
doc = dest.read_text()
dest.write_text(doc.replace("Original art for workplaces in Ireland.", "Corporate art consultancy."))
ok, out = boundary()
check("F8 the boundary refuses an edited introduction (a code change)", not ok, out)
subprocess.run(["rm", "-rf", tmp])

# F9
check("F9 says PlotArt doesn't take payment, source, deliver or install artwork, or offer consultancy",
      "It doesn’t take payment, source, deliver or install artwork, and it doesn’t offer art consultancy" in vis)
claims = re.search(r"\b(?:we|PlotArt) (?:can |will )?(?:deliver|install|arrange|advise|curate|source|consult|procure|manage|hang|frame)"
                   r"|\bour (?:delivery|installation|consultan|advisory|curation|procurement|service)|art consultants?\b(?! *:)"
                   r"|corporate (?:art )?(?:programme|program|collection service)|managed (?:art|purchas|service)|art advisory"
                   r"|procurement service|curation service|book a consultation|free delivery|request a quote|buy now|add to (?:cart|basket)", vis, re.I)
check("F9 no consultancy, curation, procurement, delivery, installation or managed-service offer", not claims, claims and claims.group(0))
check("F9 no tax, allowance or deduction wording (omitted by founder instruction)",
      not re.search(r"\b(?:tax|allowance|deductib\w*|write[- ]?off|capital allowances?|revenue\.ie)\b", vis + head, re.I), re.findall(r"\b(?:tax|allowance)\w*", vis, re.I))

# F10
check("F10 no form, input or enquiry endpoint on the page", not re.search(r"<form|<input|<textarea|<button|data-endpoint|/v1/enquiry", body, re.I))
check("F10 no basket, shortlist or multi-artist enquiry", not re.search(r"\b(?:basket|cart|shortlist (?:tool|button)|add to shortlist|enquire about (?:several|multiple|all))\b", vis, re.I))
check("F10 points to the existing per-work and per-artist enquiry routes",
      "Enquire about this work" in vis and "use the enquiry on their gallery page" in vis and "contact each artist separately" in vis)
work_page = (base / hrefs[0]).resolve().read_text()
check("F10 the existing per-work enquiry route is present on a selected work's page", "Enquire about this work" in work_page and 'class="pa-enq"' in work_page)

# F11
lg = len(cards((ROOT / "plotart/large-artworks/index.html").read_text()))
check("F11 a selection, not a duplicate collection (%d works here, %d in Large Artworks)" % (len(hrefs), lg), len(hrefs) <= LIMIT and (len(hrefs) < lg or lg <= LIMIT))
editorial = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", C.outside(body))))
words = len(editorial.split())
check("F11 substantive practical copy outside the selection (%d words, 350-1100)" % words, 350 <= words <= 1100)
check("F11 covers four settings and six questions to ask the artist",
      len(re.findall(r'<div><h3>', body)) == 4 and len(re.findall(r'<li><strong>', body)) == 6)
sentences = [s.strip().lower() for s in re.split(r"(?<=[.:?!])\s+", editorial) if len(s.split()) >= 6]
dup = [s for s, n in Counter(sentences).items() if n > 1]
check("F11 no sentence repeated", not dup, dup[:2])
phr = {k: len(re.findall(k, vis, re.I)) for k in (r"art for business", r"\bIreland\b", r"\bIrish\b", r"\boffices?\b", r"\bcorporate\b")}
check("F11 target phrases are not stuffed (each at most 3 times in visible text)", all(n <= 3 for n in phr.values()), phr)

# F12
home_hdr = re.search(r'<header class="pa-head.*?</header>', (ROOT / "plotart/large-artworks/index.html").read_text(), re.S).group(0)
check("F12 the header is the shared PlotArt header (identical to Large Artworks)", re.search(r'<header class="pa-head.*?</header>', page, re.S).group(0) == home_hdr)
check("F12 the header and footer carry no link to this page", "art-for-business" not in home_hdr and "art-for-business" not in re.search(r'<footer class="pa-foot">.*?</footer>', page, re.S).group(0))
LINKS = {"plotart/artworks/index.html": ' Buying for an office, hotel or other workplace? Read <a href="../art-for-business/">art for business</a>.',
         "plotart/large-artworks/index.html": ' <a href="../art-for-business/">Art for business</a> has more on buying for a workplace.',
         "plotart/buy-original-art-ireland.html": '\n<p>Buying for an office, hotel or other workplace? See <a href="art-for-business/">art for business</a>.</p>'}
linking = sorted(str(f.relative_to(ROOT)) for f in (ROOT / "plotart").rglob("*.html") if "art-for-business/" in f.read_text() and f.parent.name != "art-for-business")
check("F12 only the three contextual pages link here", linking == sorted(LINKS), linking)
for f, link in LINKS.items():
    check("F12 %s carries its one discreet link" % f, (ROOT / f).read_text().count(link) == 1 and (ROOT / f).read_text().count("art-for-business/") == 1)

# F13
if "--against" in sys.argv:
    ref = sys.argv[sys.argv.index("--against") + 1]
    r = subprocess.run(["git", "diff", "--name-only", ref, "--", "plotart", "worker", ".github"], cwd=ROOT, capture_output=True, text=True)
    new = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "plotart"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    changed = sorted(set(x for x in r.stdout.split() if x) | set(new))
    allowed = sorted(["plotart/art-for-business/index.html", "plotart/assets/plotart-artworks.css", ".github/workflows/image-rights-gate.yml"] + list(LINKS))
    check("F13 only the new page, the collection stylesheet, the gate step and the three linked pages change (vs %s)" % ref,
          r.returncode == 0 and set(changed) <= set(allowed) and "plotart/art-for-business/index.html" in changed, sorted(set(changed) - set(allowed)))
    check("F13 no artist page, Studio, Worker or enquiry code changes", not [x for x in changed if x.startswith(("plotart/artists/", "worker/")) or "enquiry" in x or "pa-enquiry" in x])
    for f, link in LINKS.items():
        old = subprocess.run(["git", "show", "%s:%s" % (ref, f)], cwd=ROOT, capture_output=True, text=True).stdout
        check("F13 %s differs from %s only by its one added link" % (f, ref), (ROOT / f).read_text().replace(link, "", 1) == old)
    oldcss = subprocess.run(["git", "show", "%s:plotart/assets/plotart-artworks.css" % ref], cwd=ROOT, capture_output=True, text=True).stdout
    newcss = (ROOT / "plotart/assets/plotart-artworks.css").read_text()
    kept = [l for l in oldcss.splitlines() if l and l not in newcss.splitlines()]
    check("F13 the collection stylesheet only gains .pa-biz-* rules (existing rules unchanged)",
          kept == ['.pa-coll-label{margin-top:20px;padding-top:18px}.pa-coll-actions .pa-btn,.pa-coll-links .pa-btn{max-width:100%;white-space:normal;text-align:center}}'] and
          '.pa-biz-spaces,.pa-biz-ask{grid-template-columns:1fr}' + kept[0] in newcss, kept)
else:
    print("  ----  F13 comparison with main not run (pass --against <main commit>)")

print("PLOTART ART FOR BUSINESS · %d checks, %d passed, %d failed" % (len(results), sum(results), len(results) - sum(results)))
sys.exit(0 if all(results) else 1)
