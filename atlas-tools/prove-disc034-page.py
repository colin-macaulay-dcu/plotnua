#!/usr/bin/env python3
"""DISC-034 · The Water Wall: page, SEO, claims and integration proof (read-only).

    python3 atlas-tools/prove-disc034-page.py

  W1  one <title>, meta description, canonical, Open Graph and Twitter image, index/follow
  W2  JSON-LD parses; no Product, Offer, price, LocalBusiness or Review data
  W3  exactly one H1 ("The Water Wall"); the approved hero question is the subtitle
  W4  every local href/src/srcset on the page resolves to a file
  W5  the hero is the shared pn-compare component on the DISC-034 pair, opening on 100 % BEFORE, with labels,
      keyboard control and the phone crop
  W6  the approved AI disclosure ("AI-generated illustration — not a real installation.") under the hero and in
      the slider; no image is presented as a photograph
  W7  sitemap entry, Discovery Library card in the Garden category, search-index entry
  W8  prohibited wording absent: water-bill savings, partner / stockist / dealer / authorised claims, ordering,
      buying, reserving or quoting language, availability promises, DIY claims
  W9  euro figures appear only as the dated, sourced advertised prices; every one is labelled as an advertised
      figure; no sterling figure
  W10 the six chapters in order with the approved titles; the bespoke diagram labelled "Not to scale" with all
      six stages (roof, gutter, downpipe filter, storage wall, overflow, garden irrigation), in desktop and phone
      layouts; pure vector, no embedded image
  W11 chapter 04 covers structure and foundations, filled weight, wind, overflow, frost, planning, shared
      boundaries and professional installation, and says a full-sized wall is not a simple DIY project
  W12 chapter 05: Harves and ThinTanks presented as European examples, not confirmed through an Irish distributor;
      Irish slimline tanks; no manufacturer photograph; the no-partner / no-sale statement
  W13 the closing decision is the shared two-route component: Route B is the existing free WhatsApp link (unprefilled, as the
      header guard requires) and asks for reference WW; the contact page and My Plot are linked; no form, no payment, no new endpoint
  W14 images: only DISC-034 copies that are recorded edits of the two declared masters; no master PNG is served
  W15 the hero AI disclosure is never covered by the Back dock or pill (the page-local step-aside is present)
  W16 cross-links to DISC-031 The Natural Swimming Garden and DISC-033 The Hidden Flood Barrier
Prints "DISC-034 PAGE · OK" only when every check passes.
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-the-water-wall.html"
URL = "https://plotnua.ie/" + PAGE
LABEL = "AI-generated illustration — not a real installation."
problems = []


def need(cond, msg):
    if not cond:
        problems.append(msg)


def read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()


s = read(PAGE)
txt = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", s, flags=re.S)
flat = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", txt)))
low = flat.lower()

# W1
need(len(re.findall(r"<title>[^<]+</title>", s)) == 1, "W1 one <title>")
for pat in (r'<meta name="description" content="[^"]{60,160}"', r'<link rel="canonical" href="%s"' % re.escape(URL),
            r'<meta property="og:url" content="%s"' % re.escape(URL),
            r'<meta property="og:image" content="https://plotnua\.ie/assets/disc034/img/DISC-034-og-1200x630\.jpg"',
            r'<meta name="twitter:card" content="summary_large_image"', r'<meta name="robots" content="index, follow"'):
    need(re.search(pat, s), "W1 missing: " + pat)

# W2
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
need(blocks, "W2 no JSON-LD")
for b in blocks:
    try:
        j = json.dumps(json.loads(b))
    except ValueError as e:
        problems.append("W2 JSON-LD does not parse: %s" % e); continue
    for bad in ('"Product"', '"Offer"', '"price"', '"priceCurrency"', '"AggregateOffer"', '"LocalBusiness"', '"Review"'):
        need(bad not in j, "W2 unsupported structured data: " + bad)

# W3
need(len(re.findall(r"<h1[\s>]", s)) == 1, "W3 exactly one H1")
need("<h1>The Water Wall</h1>" in s, "W3 the H1 is the approved title")
need('<p class="subtitle">What if your garden wall could store the rain?</p>' in s, "W3 the approved hero question")

# W4
for ref in set(re.findall(r'(?:href|src)="([^"#?]+)', s)) | {
        u.strip().split(" ")[0] for ss in re.findall(r'(?:srcset|imagesrcset)="([^"]+)"', s) for u in ss.split(",")}:
    if ref.startswith(("http:", "https:", "mailto:", "tel:", "data:", "/")) or not ref:
        continue
    need(os.path.exists(os.path.join(ROOT, ref)), "W4 missing local file: " + ref)

# W5
fig = re.search(r'<figure class="pn-compare pn-compare--hero"[^>]*>.*?</figure>', s, re.S)
need(fig, "W5 no pn-compare hero")
if fig:
    f = fig.group(0)
    need('data-start="100"' in f and 'value="100"' in f, "W5 the hero must open on 100% BEFORE")
    need("DISC-034-BEFORE-" in f and "DISC-034-POSSIBLE-" in f, "W5 the hero must use the DISC-034 BEFORE/POSSIBLE pair")
    need(f.index("pn-compare__possible") < f.index("pn-compare__before"), "W5 BEFORE must be the overlay layer")
    need('>Before</p>' in f and '>Possible</p>' in f, "W5 Before / Possible labels")
    need("DISC-034-BEFORE-M-819" in f and "DISC-034-POSSIBLE-M-819" in f, "W5 the phone crop (filter and storage wall in view)")
    need('class="pn-compare__range"' in f and "aria-label=" in f and "arrow keys" in f, "W5 keyboard/screen-reader control")
    need(f.count('width="1536" height="1024"') == 2, "W5 the images keep their 3:2 proportions")
need("pn-compare.js" in s and "pn-compare.css" in s, "W5 the shared component's files")

# W6
need(s.count(LABEL) >= 2, "W6 hero disclosure (slider and below)")
need(LABEL in json.loads(read("image-provenance-records.json"))["labels"]["AI_ILLUSTRATION_VARIANTS"],
     "W6 the disclosure is a register-approved AI label variant")
need("photograph of" not in low.replace("photographs of a real installation", ""), "W6 an image must not be presented as a photograph")

# W7
need(("<loc>%s</loc>" % URL) in read("sitemap.xml"), "W7 sitemap entry")
lib = read("discoveries.html")
card = re.search(r'<a class="lib-card" href="%s" data-cat="([^"]+)">.*?</a>' % re.escape(PAGE), lib, re.S)
need(card and card.group(1) == "Garden", "W7 Discovery Library card in the Garden category")
if card:
    cats = set(re.findall(r'data-filter="([^"]+)"', lib)) - {"All"}
    need("Garden" in cats, "W7 Garden must be an existing Library category")
need(('"%s"' % PAGE) in read("search-index-v1.json"), "W7 search-index entry")

# W8
neg = (low.replace("no business named here is a plotnua partner", "")
          .replace("none is a plotnua partner", "")
          .replace("not a simple diy project", "")
          .replace("often a weekend job for a confident diyer", "")
          .replace("nothing is ordered, reserved or paid for", "")
          .replace("before anything is ordered", "")
          .replace("not yet confirmed through an irish distributor", "")
          .replace("not confirmed as available through an irish distributor", "")
          .replace("couldn’t find an irish distributor", "")
          .replace("shouldn’t be expected to reduce a water bill", ""))
for bad in ("save money", "saving money", "save on your water", "lower your water bill", "reduce your water bill",
            "cut your water bill", "water bill savings", "pay for itself", "guarantee", "affordable", "cheap",
            "easy to install", "easily", "diy", "plotnua partner", "our partner", "official partner", "partner of plotnua",
            "authorised", "authorized", "stockist", "dealer for", "plotnua sells", "buy now", "buy from plotnua",
            "order now", "pre-order", "preorder", "reserve your", "get a quote", "request a quote", "coming soon",
            "will be available", "available soon", "available in ireland soon", "every garden", "any garden can",
            "suitable for every", "no planning permission is needed", "never needs planning", "always exempt",
            "maintenance-free", "drinking water"):
    need(bad not in neg, "W8 prohibited wording: " + bad)
need("can’t say if or when" in flat, "W8 no availability promise")

# W9
need(not re.search(r"£\s?\d", flat), "W9 a sterling figure appears")
allowed = {"€1,050", "€1,099", "€381.30", "€219.64"}
euros = {e.rstrip(",.") for e in re.findall(r"€\s?\d[\d,]*(?:\.\d\d)?", flat)}
need(euros <= allowed, "W9 unexpected euro figures: %s" % sorted(euros - allowed))
prices = re.findall(r'<p class="ww-price">(.*?)</p>', s, re.S)
need(len(prices) == 3, "W9 three advertised-price lines")
for p in prices:
    t = html.unescape(re.sub(r"<[^>]+>", " ", p))
    need("Advertised figure" in t and "checked 4 November 2026" in t and "VAT" in t,
         "W9 each price is labelled as an advertised figure, dated, with its VAT basis: " + t[:60])

# W10
order = re.findall(r'id="lg-ch0(\d)"', s)
need(order == ["1", "2", "3", "4", "5", "6"], "W10 six chapters in order (found %s)" % order)
for t in ("More than a water butt.", "From the roof to the flower bed.", "Is it right for your garden?",
          "What’s out there?", "Two ways to take the next step."):
    need(t in flat, "W10 chapter title missing: " + t)
dg = re.search(r'<figure class="ww-diagram[^"]*">.*?</figure>', s, re.S)
need(dg, "W10 the How it works diagram")
if dg:
    d = dg.group(0)
    need("ww-dg-wide" in d and "ww-dg-tall" in d, "W10 desktop and phone layouts of the diagram")
    need(d.count("NOT TO SCALE") == 2 and "Not to scale" in d, "W10 the diagram is labelled not to scale")
    need("<image" not in d and "<img" not in d, "W10 the diagram is pure vector")
    for t in ("Roof", "Gutter and downpipe", "Downpipe filter", "Storage wall", "Overflow", "Garden irrigation"):
        need(t in d, "W10 diagram stage missing: " + t)
for t in ("Roof", "Gutter and downpipe", "Downpipe filter", "Storage wall", "Overflow", "Garden irrigation"):
    need('<span class="ww-step-k">%s</span>' % t in s, "W10 step missing: " + t)

# W11
for t in ("About a tonne for every thousand litres", "A footing designed for the load",
          "An existing garden wall isn’t built to carry it", "Wind loading", "Drainage and overflow", "Frost",
          "Planning", "Shared boundaries", "Who should install it", "not a simple DIY project",
          "Section 5 declaration", "2 metres", "1.2 metres", "Registered Electrical Contractor"):
    need(t in flat, "W11 practicality missing: " + t)
need("don’t currently pay domestic water charges" in flat, "W11 the honest water-charges statement")

# W12
out = re.search(r'<section class="pd-section" id="whats-out-there".*?</section>', s, re.S)
need(out, "W12 chapter 05 section")
if out:
    o = html.unescape(re.sub(r"<[^>]+>", " ", out.group(0)))
    need("Harves" in o and "ThinTanks" in o and "Slimline wall tanks" in o, "W12 the European examples and the Irish tanks")
    need("Not yet confirmed through an Irish distributor." in o, "W12 the Irish availability statement")
    need("No manufacturer’s photographs are shown" in o, "W12 no manufacturer photographs")
    need("none is a PlotNua partner" in o and "doesn’t sell, import or install" in o, "W12 the no-partner / no-sale statement")
    need("<img" not in out.group(0) and "<picture" not in out.group(0), "W12 no product image in chapter 05")
need(s.count('<span class="ww-maker">Maker claim</span>') >= 3, "W12 maker claims marked")

# W13
tr = re.search(r'<div class="pn-tr" data-two-route>.*?</div>\s*</div>\s*</div>', s, re.S)
need(tr, "W13 the shared two-route component")
if tr:
    t = tr.group(0)
    wa = re.findall(r'href="(https://wa\.me/[^"]+)"', t)
    # the global header guard (G5) forbids prefilled WhatsApp text, so the reference is asked for in the copy
    need(wa == ["https://wa.me/353834036695"], "W13 Route B must be the existing WhatsApp link, unprefilled")
    need("reference WW" in html.unescape(re.sub(r"<[^>]+>", "", t)), "W13 the reference WW is asked for")
    need("Tell PlotNua you’re interested" in html.unescape(t) and "Free for homeowners." in t, "W13 Route B wording, free")
    need('href="contact.html"' in t, "W13 the existing contact page")
    need('href="your-plot.html?myplot=1"' in t, "W13 My Plot")
    need("Explore the concept yourself" in t, "W13 Route A")
low_s = s.lower()
for bad in ("<form", "<input type=\"email\"", "fetch(", "xmlhttprequest", "workers.dev", "airtable", "formspree",
            "stripe", "paypal", "checkout"):
    need(bad not in low_s, "W13 no new data collection or payment: " + bad)
need("pn-two-route.css" in s, "W13 the component stylesheet")

# W14
reg = json.loads(read("image-provenance-records.json"))
masters = {r["asset"] for r in reg["records"]}
der = {d["asset"]: d for d in reg["derivatives"]}
used = set(re.findall(r'(assets/(?:disc034|library)/img/DISC-034[^"\s,]+)', s + (card.group(0) if card else "")))
need(used, "W14 no DISC-034 image found")
M = ("assets/disc034/img/DISC-034-01-BEFORE-MASTER.png", "assets/disc034/img/DISC-034-02-POSSIBLE-MASTER.png")
for u in sorted(used):
    need("MASTER.png" not in u, "W14 a master is served: " + u)
    d = der.get(u)
    need(d and d["derived_from"]["asset"] in M and d["derived_from"]["asset"] in masters,
         "W14 %s is not a recorded edit of a declared DISC-034 master" % u)
for m, h in zip(M, ("145eff52", "8620f378")):
    r = next((x for x in reg["records"] if x["asset"] == m), None)
    need(r and r["class"] == "AI_ILLUSTRATION", "W14 %s must be declared AI_ILLUSTRATION" % m)
    need(r and r["sha256"].startswith(h), "W14 %s is the founder's approved file (sha256 %s...)" % (m, h))

# W15
need("ww-dock-away" in s and "DISC-034 · the hero AI disclosure is never hidden" in s, "W15 the dock step-aside is missing")

# W16
for link in ("discovery-natural-swimming-garden.html", "discovery-hidden-flood-barrier.html"):
    need(('href="%s"' % link) in s, "W16 cross-link missing: " + link)

if problems:
    print("DISC-034 PAGE · FAILED")
    for p in problems:
        print("  " + p)
    sys.exit(1)
print("DISC-034 PAGE · OK (W1-W16)")
