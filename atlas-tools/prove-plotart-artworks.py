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
A7  sitemap: exactly the generated region for the switches; one entry (the canonical URL) only while artworks_in_sitemap
    and artworks_indexable are on
A8  synchronisation through the content pipeline's own functions: a sale, a withdrawal, a price change and a new
    gallery each change the region accordingly and nothing outside it
A9  the content-only boundary accepts exactly the regenerated region and refuses an edited intro, an injected work
    and a price that differs from the export
A10 fairness: works alternate between artists (no artist twice in a row while another still has works to show)
A11 (--against MAIN) no artist page differs from main; the homepage, Artists' Gallery and buying guide differ only by
    their one added link; the Artists' Gallery collection region is unchanged
A12 stable order (both All Artworks and Large Artworks): artists appear in first-publication order; republishing,
    new approval dates, opportunity selections, commissions, biography/statement/display-name edits and licence
    re-acceptance never reorder either collection; each artist's own work order and the membership are kept; an
    unrecorded new artist is placed after every recorded artist (by licence acceptance, then slug) and stays put
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
    # Refine (21 Nov 2026): on All Artworks a card may carry ONLY the five Refine data attributes, in this order
    return re.findall(r'<li class="pa-coll-work"(?: data-price="[^"]*" data-long="[^"]*" data-artist="[^"]*" data-work="[^"]*"(?: data-county="[^"]*")?)?>(.*?)</li>', doc, re.S)


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
check("A6 the approved title (SEO and analytics package, 26 Nov 2026)", "<title>Original Irish Art for Sale | Paintings &amp; Prints | PlotArt</title>" in head)
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
check("A7 sitemap.xml is exactly the generated PlotArt region for the current switches", SEO.update_sitemap(sm, packages, launch) == sm)
want_listed = SEO.indexable(PATH, launch) and launch.get("artworks_in_sitemap") is True
check("A7 the collection is listed exactly %s, by its canonical URL" % ("once" if want_listed else "never"),
      sm.count("<loc>https://plotnua.ie/plotart/artworks/</loc>") == (1 if want_listed else 0))
check("A7 switching the entry off removes exactly that one line and nothing else",
      SEO.update_sitemap(sm, packages, dict(launch, artworks_in_sitemap=False)) ==
      SEO.update_sitemap(sm, packages, on).replace("  <url><loc>https://plotnua.ie/plotart/artworks/</loc></url>\n", ""))
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
LINKS = {"plotart/index.html": '\n  <p style="font-size:15px;margin:0">Or <a href="artworks/" data-pa-track="home_artworks">browse all available artworks <span aria-hidden="true">→</span></a></p>',
         "plotart/gallery/index.html": '<a href="../artworks/" data-pa-track="vg_artworks">Browse All Artworks →</a>',
         "plotart/buy-original-art-ireland.html": ' To see every work currently on offer in one place, browse <a href="artworks/">all available artworks</a>.'}
LATER = {"plotart/buy-original-art-ireland.html": ['\n<p>Looking for a statement piece? Browse <a href="large-artworks/">large original artworks</a> of 100 cm or more.</p>']}
if "--against" in sys.argv:
    ref = sys.argv[sys.argv.index("--against") + 1]
    show = lambda f: subprocess.run(["git", "show", "%s:%s" % (ref, f)], cwd=ROOT, capture_output=True, text=True).stdout
    r = subprocess.run(["git", "diff", "--name-only", ref, "HEAD", "--", "plotart/artists"], cwd=ROOT, capture_output=True, text=True)
    check("A11 no artist gallery or artwork page differs from %s" % ref, r.returncode == 0 and r.stdout.strip() == "", r.stdout + r.stderr)
    for f, link in LINKS.items():
        new = (ROOT / f).read_text()
        for later in LATER.get(f, ()):            # links added by later approved phases, proved by their own proofs
            new = new.replace(later, "", 1)
        check("A11 %s differs from %s only by the one added collection link" % (f, ref), new.count(link) == 1 and new.replace(link, "", 1) == show(f))
    old, new = show("plotart/gallery/index.html"), (ROOT / "plotart/gallery/index.html").read_text()
    check("A11 the Artists' Gallery collection region is unchanged", old[slice(*P.vg_region(old))] == new[slice(*P.vg_region(new))])
else:
    print("  ----  A11 not run (pass --against <main commit> to compare the galleries with main)")

# A12 stable collection order (16 Nov 2026 regression: five routine opportunity republishes changed approved_at and
# reordered both collections). Covers All Artworks AND Large Artworks. Expected values are an independent fixture,
# not read from C.COLLECTION_ARTIST_ORDER: the order the artists were first published, and the order both pages
# had before the five updates (commit 6ec021f^).
FIRST_PUBLISHED = ["leah-hewson", "ciaran-mccoy", "mark-kavanagh-rasher", "daniel-chester", "anna-marie-savage",
                   "fintan-whelan", "nessa-mccormack", "karen-ebbs",
                   "lena-fawaz", "sarah-fitzgibbon"]   # 17 Nov 2026, in the order both collections already showed them
COLLS = ["artworks/index.html", "large-artworks/index.html"]
slugs_of = lambda rows: [(p["artist"]["slug"], w["slug"]) for p, w in rows]
order_of = lambda pkgs, path: slugs_of(C.collection_order(pkgs, C.COLLECTIONS[path]["keep"]))
first_seen = lambda rows: list(dict.fromkeys(a for a, _ in rows))
baseline = {p: order_of(packages, p) for p in COLLS}

for p in COLLS:
    doc = (ROOT / "plotart" / p).read_text()
    on_page = list(dict.fromkeys(re.findall(r'class="pa-coll-artist"><a href="\.\./artists/([^/]+)/', doc)))
    want = [a for a in FIRST_PUBLISHED if a in on_page]
    # Artists published after this fixture was written are not refused: they must all FOLLOW every recorded artist,
    # in the order they accepted the gallery licence (then slug) - read from the exports, not from
    # C.COLLECTION_ARTIST_ORDER - so a first publication never moves an existing artist (17 Nov 2026: the stricter
    # "only recorded artists" form refused every new artist's first publication).
    acc = {x["artist"]["slug"]: (x["publication"].get("first_approved_at") or x["publication"].get("licence_accepted_at") or "9999", x["artist"]["slug"]) for x in packages}
    newer = sorted((a for a in on_page if a not in FIRST_PUBLISHED), key=lambda a: acc.get(a, ("9999", a)))
    check("A12 %s lists artists in first-publication order (newly published artists after them)" % p,
          on_page == want + newer, on_page)
    check("A12 %s order does not depend on the order the exports are read" % p,
          order_of(list(reversed(packages)), p) == baseline[p])


def mutated(fn):
    pk = copy.deepcopy(packages)
    for x in pk:
        fn(x)
    return pk


ROUTINE = {
    "every gallery republished with a new version and approval date": lambda x: x["publication"].update(
        approved_at="2099-01-01T00:00:00.000Z", version="v99"),
    "approval dates reversed (latest-approved artist first)": lambda x: x["publication"].update(
        approved_at="2026-%02d-01T00:00:00.000Z" % (12 - FIRST_PUBLISHED.index(x["artist"]["slug"]) if x["artist"]["slug"] in FIRST_PUBLISHED else 1)),
    "opportunity selections changed": lambda x: x["artist"].update(open_to=["living_gallery", "art_for_hire", "commissions"]),
    "opportunity selections removed": lambda x: x["artist"].pop("open_to", None),
    "commissions setting toggled": lambda x: x["artist"].update(open_for_commissions=not x["artist"].get("open_for_commissions")),
    "biography and statement edited": lambda x: x["artist"].update(bio="Edited.", statement="Edited."),
    "display name edited": lambda x: x["artist"].update(display_name="Zz " + x["artist"]["display_name"]),
    "gallery licence re-accepted": lambda x: x["publication"].update(licence_accepted_at="2099-01-01T00:00:00.000Z"),
}
for name, fn in ROUTINE.items():
    pk = mutated(fn)
    for p in COLLS:
        check("A12 %s: %s order unchanged" % (name, p), order_of(pk, p) == baseline[p])
# one artist at a time republished (the 16 Nov 2026 pattern)
for i in range(len(packages)):
    pk = copy.deepcopy(packages)
    pk[i]["publication"].update(approved_at="2099-12-31T23:59:59.999Z", version="v100")
    if any(order_of(pk, p) != baseline[p] for p in COLLS):
        check("A12 republishing %s alone leaves both collections in order" % pk[i]["artist"]["slug"], False)
        break
else:
    check("A12 republishing any single artist leaves both collections in order", True)

# each artist's own work order and collection membership are untouched
for p in COLLS:
    keep = C.COLLECTIONS[p]["keep"]
    rows = baseline[p]
    own = all([w for a, w in rows if a == x["artist"]["slug"]] ==
              [w["slug"] for w in x["works"] if w["availability"] == "available" and keep(w)] for x in packages)
    check("A12 %s keeps every artist's own work order and exactly the available works" % p, own)

# a newly published artist not yet recorded: placed after every recorded artist, deterministically, and stays put
src = next(x for x in packages if any(C.is_large(w) and w["availability"] == "available" for w in x["works"]))


def newcomer(slug, accepted, approved, first=None):
    n = copy.deepcopy(src)
    n["artist"].update(slug=slug, display_name="Aaa " + slug)
    n["publication"].update(licence_accepted_at=accepted, approved_at=approved)
    # A newcomer is copied from a real export, so it must not inherit that artist's first_approved_at (25 Nov 2026:
    # once Anna-Marie Savage's gallery was republished by the updated Studio, the copies carried her 12 Nov date and
    # sorted among the real artists, so the fixture, not the ordering, failed). Only a date given here applies.
    n["publication"].pop("first_approved_at", None)
    if first:
        n["publication"]["first_approved_at"] = first
    return n


pk = packages + [newcomer("test-new-b", "2026-12-02T00:00:00Z", "2026-12-03T00:00:00Z"),
                 newcomer("test-new-a", "2026-12-01T00:00:00Z", "2026-12-04T00:00:00Z")]
for p in COLLS:
    seen = first_seen(order_of(pk, p))
    recorded = [a for a in seen if not a.startswith("test-new-")]
    check("A12 %s: unrecorded new artists follow every recorded artist, by licence acceptance" % p,
          seen[len(recorded):] == ["test-new-a", "test-new-b"] and recorded == first_seen(baseline[p]), seen)
    check("A12 %s: existing artists' works keep their positions relative to each other when a new artist arrives" % p,
          [r for r in order_of(pk, p) if not r[0].startswith("test-new-")] == baseline[p])
    pk2 = copy.deepcopy(pk)
    pk2[-1]["publication"].update(approved_at="2099-01-01T00:00:00Z", version="v9")
    check("A12 %s: republishing a new artist does not move it" % p, order_of(pk2, p) == order_of(pk, p))
# A12 correction (17 Nov 2026, Olivia Jones's first publication): newly published artists whose alphabetical order differs
# from the order they were first approved. They follow the recorded artists in FIRST-APPROVAL order, and nothing routine
# moves them: a licence re-acceptance, a republish (new approval date) or an edited name (independent fixture, not read
# from the code).
pkn = packages + [newcomer("test-zed", "2026-12-01T09:00:00Z", "2026-12-01T10:00:00.000Z", first="2026-12-01T10:00:00.000Z"),
                  newcomer("test-amy", "2026-12-02T09:00:00Z", "2026-12-02T10:00:00.000Z", first="2026-12-02T10:00:00.000Z"),
                  newcomer("test-mid", "2026-12-03T09:00:00Z", "2026-12-03T10:00:00.000Z", first="2026-12-03T10:00:00.000Z")]
WANT_NEW = ["test-zed", "test-amy", "test-mid"]
for p in COLLS:
    base_n = order_of(pkn, p)
    check("A12 %s: new artists whose names sort differently follow the recorded artists in first-approval order" % p,
          first_seen(base_n)[-3:] == WANT_NEW and [r for r in base_n if not r[0].startswith("test-")] == baseline[p], first_seen(base_n))
    for label, fn in (("licence re-accepted by every artist", lambda x: x["publication"].update(licence_accepted_at="2099-01-01T00:00:00Z")),
                      ("licence re-accepted by the first newcomer only", lambda x: x["artist"]["slug"] == "test-zed" and x["publication"].update(licence_accepted_at="2099-06-01T00:00:00Z")),
                      ("every gallery republished", lambda x: x["publication"].update(approved_at="2099-01-01T00:00:00.000Z", version="v99")),
                      ("names edited", lambda x: x["artist"].update(display_name="Zz " + x["artist"]["display_name"]))):
        pkm = copy.deepcopy(pkn)
        for x in pkm:
            fn(x)
        check("A12 %s: %s: order unchanged with newly published artists present" % (p, label), order_of(pkm, p) == base_n)
import plotart_gallery as G   # noqa: E402


def fa_ok(v):
    try:
        G.check_first_approved({} if v is ... else {"first_approved_at": v})
        return True
    except G.Refused:
        return False


check("A12 the export check accepts first_approved_at as a UTC timestamp (or absent) and refuses anything else, and only the known publication fields are allowed",
      fa_ok(...) and fa_ok(None) and fa_ok("2026-11-17T21:59:03.412Z") and not fa_ok("yesterday") and not fa_ok(17) and not fa_ok("2026-11-17")
      and "first_approved_at" in G.PUB_KEYS and "check_first_approved(pub)" in open(G.__file__, encoding="utf-8").read().split("def validate_export", 1)[1])

reg = list(C.COLLECTION_ARTIST_ORDER)
_noorder = sorted(x["artist"]["slug"] for x in packages if x["artist"]["slug"] not in reg and not x["publication"].get("first_approved_at"))
check("A12 every published artist has a fixed collection place: recorded in COLLECTION_ARTIST_ORDER, or published with "
      "first_approved_at (a gallery exported by a Studio from before 17 Nov 2026 must be published again by the updated Studio)",
      not _noorder, _noorder)
check("A12 the collection order register has no duplicates and starts with the artists published so far",
      len(reg) == len(set(reg)) and reg[:len(FIRST_PUBLISHED)] == FIRST_PUBLISHED, reg)
unrecorded = sorted({x["artist"]["slug"] for x in packages} - set(reg))
if unrecorded:
    print("  NOTE  not yet in COLLECTION_ARTIST_ORDER (placed by licence acceptance; add at the end in a code release): " + ", ".join(unrecorded))


# ---- R · Refine on All Artworks (founder approval 21 Nov 2026) -----------------------------------------------------------
_aw = (ROOT / "plotart/artworks/index.html").read_text(encoding="utf-8")
_reg = region(_aw)
_rows = C.collection_order(packages)
_attrs = re.findall(r'<li class="pa-coll-work"( data-[^>]*)>', _reg)
_want = [C.refine_attrs(pk, w) for pk, w in _rows]
check("R1 every All Artworks card carries the Refine values derived from its own approved export, in collection order",
      _attrs == _want and len(_attrs) == len(_rows), (len(_attrs), len(_rows)))
_pub_county = {pk["artist"]["slug"]: (pk["artist"].get("county") or "").strip() for pk in packages}
_bad_c = [a for a in _attrs if 'data-county="' in a and re.search(r'data-county="([^"]*)"', a).group(1) != html.escape(_pub_county[re.search(r'data-artist="([^"]*)"', a).group(1)], quote=True)]
_missing_c = [a for a in _attrs if 'data-county="' not in a and _pub_county[re.search(r'data-artist="([^"]*)"', a).group(1)]]
check("R2 artist location only as the artist's public county (no county where none is shared; never an artwork location)",
      not _bad_c and not _missing_c and "artwork-county" not in _reg and "data-location" not in _reg, (_bad_c[:2], _missing_c[:2]))
check("R3 the Refine line, its sheet and 'Available to hire' all SHIP HIDDEN (shown only by the script; hire only by the live check)",
      '<div class="pa-rf" data-rf hidden>' in _reg and '<div class="pa-rf-group pa-rf-hire" data-rf-hire hidden>' in _reg
      and "data-hire" not in _reg and 'data-rf-none hidden' in _reg)
_opts = lambda name: re.findall(r'<input type="checkbox" name="%s" value="([^"]*)">' % name, _reg)
check("R4 the artist and location choices list exactly what the collection holds now; the label is 'Artist location'",
      sorted(_opts("artist")) == sorted({pk["artist"]["slug"] for pk, _ in _rows})
      and sorted(_opts("county")) == sorted({_pub_county[pk["artist"]["slug"]] for pk, _ in _rows} - {""})
      and ">Artist location<" in _reg and "Artist based in" not in _aw, (_opts("artist"), _opts("county")))
check("R5 price and size bands are the approved fixed bands",
      _opts("price") == [v for v, _ in C.REFINE_PRICE] == ["0-1000", "1000-2500", "2500-5000", "5000-10000", "10000-"]
      and _opts("size") == [v for v, _ in C.REFINE_SIZE] == ["0-50", "50-100", "100-150", "150-"])
_lg = (ROOT / "plotart/large-artworks/index.html").read_text(encoding="utf-8")
_galleries = [p.read_text(encoding="utf-8") for p in (ROOT / "plotart/artists").glob("*/*.html")]
check("R6 Refine exists on All Artworks only: not on Large Artworks, not in any artist gallery or artwork page",
      "pa-rf" not in _lg and "plotart-refine" not in _lg and not any("plotart-refine" in g or "data-rf" in g for g in _galleries)
      and _aw.count('<script src="../assets/plotart-refine.js" defer></script>') == 1 and _aw.count('href="../assets/plotart-refine.css"') == 1)
_js = (ROOT / "plotart/assets/plotart-refine.js").read_text(encoding="utf-8")
check("R7 the script fails safe and keeps hire live and fail-closed (catalogue AND live check, validity window, open, ok)",
      "function failSafe()" in _js and "root.hidden = false;" in _js and _js.index("root.hidden = false;") > _js.index("var q = new URLSearchParams")
      and "'../art-for-hire/'" in _js and "/v1/hire-listed" in _js and "catalogue[i.id]" in _js and "j.open !== true" in _js
      and "j.ok !== true" in _js and "until > Date.now()" in _js and ".catch(hireOff)" in _js and "localStorage" not in _js
      and "sendBeacon" not in _js and "gtag" not in _js)
check("R8 filtering never reorders: the script only marks cards (data-rf-out), it never moves or sorts them",
      "data-rf-out" in _js and not re.search(r"\.(sort|appendChild|insertBefore|prepend|append)\(", _js.replace("document.body.style", "")))

# ---- Growth 3 landing pages (28 Nov 2026): each page's rule, its live figures, its limits and its empty state ----------
_ids = {w["id"]: w for p in packages for w in p["works"]}
_avail = C.available(packages)
for _p in C.LANDING:
    _doc = (ROOT / "plotart" / _p).read_text(encoding="utf-8")
    _t, _d = C.hub_meta(_p, packages)
    check("G3 %s: title at most 60 and description at most 160 characters, both on the page" % _p,
          len(_t) <= 60 and len(_d) <= 160 and ("<title>%s</title>" % html.escape(_t, quote=False)) in _doc
          and ('<meta name="description" content="%s">' % html.escape(_d, quote=True)) in _doc, (len(_t), len(_d)))
    _rows = C.collection_order(packages, C.COLLECTIONS[_p]["keep"])
    check("G3 %s: every listed work is published, available and passes the page's rule" % _p,
          all(w["availability"] == "available" and C.COLLECTIONS[_p]["keep"](w) for _, w in _rows))
    check("G3 %s: CollectionPage, ItemList, canonical and sitemap entry" % _p,
          '"@type":"CollectionPage"' in _doc and '"@type":"ItemList"' in _doc
          and ('<link rel="canonical" href="%s">' % SEO.canonical(_p)) in _doc
          and ("<loc>%s</loc>" % SEO.canonical(_p)) in (ROOT / "sitemap.xml").read_text(encoding="utf-8"))
    check("G3 %s: never in the main navigation" % _p, ('href="%s"' % SEO.canonical(_p)) not in (ROOT / "plotart/index.html").read_text(encoding="utf-8")
          and ('href="%s"' % _p.replace("index.html", "")) not in re.search(r'<nav class="pa-pills.*?</nav>', (ROOT / "plotart/index.html").read_text(encoding="utf-8"), re.S).group(0))
    _empty = C.collection([], _p)
    check("G3 %s: graceful empty state" % _p, C.COLLECTIONS[_p]["empty"] in _empty and "pa-coll-grid" not in _empty and "../gallery/" in _empty)
    check("G3 %s: no nationality claim and no meta keywords" % _p, "Irish artist" not in _doc and 'name="keywords"' not in _doc)
check("G3 under €1,000: public prices below the threshold only (never price on request)",
      all(C.priced(w) and w["price_eur"] < 1000 for _, w in C.collection_order(packages, C.is_under_1000))
      and not C.is_under_1000({"price_eur": 900, "price_on_request": True}) and not C.is_under_1000({"price_eur": 1000}))
check("G3 prints: printmaking processes only; a giclée is refused; mixed media is not a print",
      C.is_print({"medium": "Screen print"}) and C.is_print({"medium": "Multi Layered Etched Intaglio Print"})
      and not C.is_print({"medium": "Giclee print"}) and not C.is_print({"medium": "Mixed Media"}))
check("G3 prints: editions read from the artist's own words", C.edition_label({"materials": "300 gsm paper, eidtion of 10."}) == "edition of 10"
      and C.edition_label({"medium": "Monoprint/Acrylic"}) == "one of a kind" and C.edition_label({"medium": "Screen print"}) is None)
check("G3 oil: oil paintings only; mixed media with oil stays mixed media",
      C.is_oil({"medium": "Oil on linen"}) and not C.is_oil({"medium": "Mixed media, raw silk & oil on canvas"}) and not C.is_oil({"medium": "Acrylic on canvas"}))
check("G3 curated allowlists name only published works, and none is both coastal and figurative",
      C.FIGURATIVE_WORKS <= set(_ids) and C.COASTAL_WORKS <= set(_ids) and not (C.FIGURATIVE_WORKS & C.COASTAL_WORKS))
_offices = (ROOT / "plotart/art-for-offices/index.html").read_text(encoding="utf-8")
check("G3 offices: the hire sentence is exactly the approved wording",
      "Alongside artwork sales, we are developing flexible art hire arrangements for commercial spaces, subject to artwork availability and agreement with the individual artist." in _offices)
check("G3 guides: one work per artist, publicly priced",
      all(len({p["artist"]["slug"] for p, _ in r}) == len(r) and all(C.priced(w) for _, w in r)
          for r in (C._lowest_per_artist(C.collection_order(packages, C.COLLECTIONS[g]["keep"])) for g in ("collecting-art-ireland/index.html", "art-gifts-ireland/index.html"))))
_gift = (ROOT / "plotart/art-gifts-ireland/index.html").read_text(encoding="utf-8")
check("G3 gifts: no delivery-time promise and no voucher", "makes no delivery promise" in _gift and not re.search(r"voucher|guaranteed|in time for Christmas", _gift, re.I))
_col = (ROOT / "plotart/collecting-art-ireland/index.html").read_text(encoding="utf-8")
check("G3 collecting: no investment or value claim", not re.search(r"\binvest(?:ment)? (?:opportunit|potential|grade)|appreciat\w* in value|returns? on|asset class", _col, re.I))

print("PLOTART ARTWORKS · %d checks, %d passed, %d failed" % (len(results), sum(results), len(results) - sum(results)))
sys.exit(0 if all(results) else 1)
