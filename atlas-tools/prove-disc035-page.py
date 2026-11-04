#!/usr/bin/env python3
"""DISC-035 · The Outdoor Room: page, SEO, claims and integration proof (read-only).

    python3 atlas-tools/prove-disc035-page.py

  O1  one <title>, meta description, canonical, Open Graph and Twitter image, index/follow
  O2  JSON-LD parses; no Product, Offer, price, LocalBusiness or Review data
  O3  exactly one H1 ("The Outdoor Room"); the approved hero question and supporting line
  O4  every local href/src/srcset on the page resolves to a file
  O5  the hero is the shared pn-compare component on the DISC-035 pair, opening on 100 % BEFORE, with labels,
      keyboard control, the phone crop and the pair's real 1671 x 941 proportions
  O6  the standard slider AI disclosure under the hero and in the slider; no image presented as a photograph
  O7  sitemap entry, Discovery Library card in the Garden category, search-index entry
  O8  six chapters in order with the approved titles; the five possibilities in order, each with a reserved image
      slot holding a PlotNua drawing (no chapter image is substituted)
  O9  chapter 02: rain, wind, drainage, roofing materials, heating, lighting and maintenance; the bespoke diagram
      is pure vector, labelled not to scale, in desktop and phone layouts, with its seven parts
  O10 chapter 03: the comparison table covers all five rooms, with a phone version
  O11 chapter 04: Class 1 at 45 m2 (was 40), Class 3 at 30 m2 (was 25), 27 July 2026, rear only, 25 m2 open space,
      the shared allowances, attached / open-sided / free-standing / side-or-front cases, the building-regulations
      exemption (23 m2), Section 5 (EUR 80), Article 9 restrictions, and no blanket exemption claim
  O12 chapter 05: the shared two-route component; route B is the existing free WhatsApp link (unprefilled) with
      reference OR and the contact page; no form, payment or new endpoint
  O13 the Superior Pergola showcase card comes from the shared builder; the 4% saving is stated for aluminium
      pergolas only, exactly once, with no other percentage; no commission figure or 8%; the referral disclosure
  O14 Apex Verandas, The Outdoor Scene and QOLA are named as researched installers only: no partner claim, no
      link to their sites from the makers section, no photograph
  O15 euro figures appear only where approved (Section 5 fee, the advertised prices, the relative-cost symbols);
      the advertised prices are labelled and dated; no sterling
  O16 images: only DISC-035 copies that are recorded edits of the two declared masters; no master is served
  O17 the hero AI disclosure is never covered by the Back dock or pill (the page-local step-aside is present)
  O18 chapter 06 links DISC-008 Living in the Garden, DISC-001 Garden Retreat and DISC-029 Hidden Bins
Prints "DISC-035 PAGE · OK" only when every check passes.
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-the-outdoor-room.html"
URL = "https://plotnua.ie/" + PAGE
LABEL = "Illustrative AI-generated visualisation. Not an actual installation."
problems = []


def need(cond, msg):
    if not cond:
        problems.append(msg)


def read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()


def text(fragment):
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", fragment, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


s = read(PAGE)
flat = text(s)
low = flat.lower()

# O1
need(len(re.findall(r"<title>[^<]+</title>", s)) == 1, "O1 one <title>")
for pat in (r'<meta name="description" content="[^"]{60,160}"', r'<link rel="canonical" href="%s"' % re.escape(URL),
            r'<meta property="og:url" content="%s"' % re.escape(URL),
            r'<meta property="og:image" content="https://plotnua\.ie/assets/disc035/img/DISC-035-og-1200x630\.jpg"',
            r'<meta name="twitter:card" content="summary_large_image"', r'<meta name="robots" content="index, follow"'):
    need(re.search(pat, s), "O1 missing: " + pat)

# O2
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
need(blocks, "O2 no JSON-LD")
for b in blocks:
    try:
        j = json.dumps(json.loads(b))
    except ValueError as e:
        problems.append("O2 JSON-LD does not parse: %s" % e); continue
    for bad in ('"Product"', '"Offer"', '"price"', '"priceCurrency"', '"AggregateOffer"', '"LocalBusiness"', '"Review"'):
        need(bad not in j, "O2 unsupported structured data: " + bad)

# O3
need(len(re.findall(r"<h1[\s>]", s)) == 1, "O3 exactly one H1")
need("<h1>The Outdoor Room</h1>" in s, "O3 the H1 is the approved title")
need('<p class="subtitle">What if the space outside your back door became your favourite room?</p>' in s, "O3 the approved hero question")
need('<p class="intro">Make more of the space between your house and your garden.</p>' in s, "O3 the approved supporting line")

# O4
for ref in set(re.findall(r'(?:href|src)="([^"#?]+)', s)) | {
        u.strip().split(" ")[0] for ss in re.findall(r'(?:srcset|imagesrcset)="([^"]+)"', s) for u in ss.split(",")}:
    if ref.startswith(("http:", "https:", "mailto:", "tel:", "data:", "/")) or not ref:
        continue
    need(os.path.exists(os.path.join(ROOT, ref)), "O4 missing local file: " + ref)

# O5
fig = re.search(r'<figure class="pn-compare pn-compare--hero"[^>]*>.*?</figure>', s, re.S)
need(fig, "O5 no pn-compare hero")
if fig:
    f = fig.group(0)
    need('data-start="100"' in f and 'value="100"' in f, "O5 the hero must open on 100% BEFORE")
    need("DISC-035-BEFORE-" in f and "DISC-035-POSSIBLE-" in f, "O5 the hero must use the DISC-035 pair")
    need(f.index("pn-compare__possible") < f.index("pn-compare__before"), "O5 BEFORE must be the overlay layer")
    need('>Before</p>' in f and '>Possible</p>' in f, "O5 Before / Possible labels")
    need("DISC-035-BEFORE-M-753" in f and "DISC-035-POSSIBLE-M-753" in f, "O5 the phone crop")
    need('class="pn-compare__range"' in f and "aria-label=" in f and "arrow keys" in f, "O5 keyboard/screen-reader control")
    need(f.count('width="1671" height="941"') == 2, "O5 the images keep the pair's own 1671 x 941 proportions")
need("pn-compare.js" in s and "pn-compare.css" in s, "O5 the shared component's files")

# O6
need(s.count(LABEL) >= 2, "O6 hero disclosure (slider and below)")
need(LABEL in json.loads(read("image-provenance-records.json"))["labels"]["AI_ILLUSTRATION_VARIANTS"],
     "O6 the disclosure is a register-approved AI label")
need("photograph of" not in low, "O6 an image must not be presented as a photograph")

# O7
need(("<loc>%s</loc>" % URL) in read("sitemap.xml"), "O7 sitemap entry")
lib = read("discoveries.html")
card = re.search(r'<a class="lib-card" href="%s" data-cat="([^"]+)">.*?</a>' % re.escape(PAGE), lib, re.S)
need(card and card.group(1) == "Garden", "O7 Discovery Library card in the Garden category")
need(('"%s"' % PAGE) in read("search-index-v1.json"), "O7 search-index entry")

# O8
order = re.findall(r'id="lg-ch0(\d)"', s)
need(order == ["1", "2", "3", "4", "5", "6"], "O8 six chapters in order (found %s)" % order)
for t in ("Five rooms you didn’t know you had.", "Built for Irish weather", "Which one suits your space?",
          "What can you build without planning permission?", "Meet the makers", "Related possibilities"):
    need(t in flat, "O8 chapter title missing: " + t)
rooms = re.findall(r'<h3 id="orR(\d)H">([^<]+)</h3>', s)
need([r[1] for r in rooms] == ["The Covered Patio", "The Glass Room", "The Outdoor Dining Room",
                              "The Flexible Pergola", "The Outdoor Kitchen"], "O8 the five possibilities in order: %s" % rooms)
slots = re.findall(r'<figure class="or-slot or-fig" data-or-slot="(DISC-035-0[3-7]-[A-Z-]+)">(.*?)</figure>', s, re.S)
need(len(slots) == 5, "O8 five reserved image slots")
for name, body in slots:
    need("<svg" in body and "<img" not in body and "<image" not in body,
         "O8 %s holds a PlotNua drawing, not a substitute image" % name)

# O9
wx = re.search(r'<section class="pd-section" id="irish-weather".*?</section>', s, re.S)
need(wx, "O9 chapter 02 section")
if wx:
    w = text(wx.group(0)).lower()
    for t in ("rain", "wind", "drain", "glass", "polycarbonate", "louvres", "fabric", "heater", "light", "looking after it"):
        need(t in w, "O9 chapter 02 topic missing: " + t)
dg = re.search(r'<figure class="or-diagram[^"]*">.*?</figure>', s, re.S)
need(dg, "O9 the weather diagram")
if dg:
    d = dg.group(0)
    need("or-dg-wide" in d and "or-dg-tall" in d, "O9 desktop and phone layouts of the diagram")
    need(d.count("NOT TO SCALE") == 2 and "Not to scale" in d, "O9 the diagram is labelled not to scale")
    need("<image" not in d and "<img" not in d, "O9 the diagram is pure vector")
for t in ("Roof", "Gutter in the beam", "Downpipe inside the post", "Footing", "Sliding glass side", "Heater",
          "Lighting under the beam"):
    need('<span class="or-step-k">%s</span>' % t in s, "O9 step missing: " + t)

# O10
tb = re.search(r'<table class="or-cmp">.*?</table>', s, re.S)
need(tb, "O10 the comparison table")
if tb:
    heads = re.findall(r'<th scope="col">([^<]+)</th>', tb.group(0))
    need(heads == ["Covered Patio", "Glass Room", "Outdoor Dining Room", "Flexible Pergola", "Outdoor Kitchen"],
         "O10 the table covers the five rooms: %s" % heads)
need(s.count('<ul class="or-cmp-cards"') == 1 and len(re.findall(r'<ul class="or-cmp-cards".*?</ul>', s, re.S)[0].split("<li>")) == 6,
     "O10 the phone version lists the five rooms")

# O11
pl = re.search(r'<section class="pd-section pd-gapL" id="planning".*?</section>', s, re.S)
need(pl, "O11 chapter 04 section")
if pl:
    p = text(pl.group(0))
    for t in ("27 July 2026", "Class 1", "45 m", "was 40 m", "Class 3", "30 m", "was 25 m", "to the rear",
              "1 October 1964", "25 m", "Never forward of the front wall", "3 metres", "4 metres",
              "A glass room fixed to the back wall", "sides open", "free-standing pergola", "side or front",
              "protected structure", "Architectural Conservation Area", "Section 5", "€80", "four weeks",
              "Building Regulations", "23 m", "not legal advice", "can’t tell you whether"):
        need(t in p, "O11 planning point missing: " + t)
need('<span class="or-big">45&thinsp;m<sup>2</sup></span>' in s and '<span class="or-big">30&thinsp;m<sup>2</sup></span>' in s,
     "O11 the two allowance figures are 45 m2 (Class 1) and 30 m2 (Class 3)")
for bad in ("no planning permission is needed", "never needs planning", "always exempt", "don’t need planning permission",
            "do not need planning permission", "doesn’t need planning permission", "removable structure",
            "guaranteed exempt", "is exempt from planning permission."):
    need(bad not in low, "O11 blanket exemption wording: " + bad)

# O12
mk = re.search(r'<section class="pd-section" id="meet-the-makers".*?(?=<section class="pd-section" id="sources")', s, re.S)
need(mk, "O12 chapter 05 section")
if mk:
    m = mk.group(0)
    two = re.search(r'<div class="pn-tr" data-two-route>.*?</div>\s*</div>\s*</div>', m, re.S)
    need(two, "O12 the shared two-route component")
    if two:
        t2 = two.group(0)
        need("Explore the makers yourself" in t2 and "Let PlotNua do the homework" in t2, "O12 both routes")
        need("Free for homeowners." in t2, "O12 route B is free")
        # the global header guard (G5) forbids prefilled WhatsApp text, so the reference is asked for in the copy
        need(re.findall(r'href="(https://wa\.me/[^"]+)"', t2) == ["https://wa.me/353834036695"],
             "O12 route B is the existing WhatsApp link, unprefilled")
        need('href="contact.html"' in t2 and 'href="your-plot.html?myplot=1"' in t2, "O12 the contact page and My Plot")
        need("reference OR" in html.unescape(re.sub(r"<[^>]+>", "", t2)), "O12 the reference OR is asked for")
    need("pn-two-route.css" in s and "pn-two-option" not in s, "O12 the component stylesheet")
low_s = s.lower()
for bad in ("<form", "<input type=\"email\"", "fetch(", "xmlhttprequest", "workers.dev", "airtable", "formspree",
            "stripe", "paypal", "checkout"):
    need(bad not in low_s, "O12 no new data collection or payment: " + bad)

# O13
sc = re.search(r"<!-- PN-SHOWCASE-CARDS v1 · built by atlas-tools/build-showcase-cards\.py.*?<!-- /PN-SHOWCASE-CARDS -->", s, re.S)
need(sc and 'href="suppliers/superior-pergola-ireland.html"' in sc.group(0), "O13 the Superior Pergola showcase card from the shared builder")
need(mk and sc and sc.group(0) in mk.group(0), "O13 the showcase card sits in chapter 05")
pct = re.findall(r"\d+(?:\.\d+)?\s?%", flat)
need(pct == ["4%"], "O13 exactly one percentage on the page, the pergola saving: %s" % pct)
need("applies a 4% saving to aluminium pergola installations introduced through PlotNua. It doesn’t apply to verandas, porches or its other products." in flat,
     "O13 the saving is stated for aluminium pergolas only")
for bad in ("8%", "commission", "eight per cent", "4% on all", "4% off verandas"):
    need(bad not in low.replace("commission for regulation of utilities", "").replace("law reform commission", ""), "O13 commission or widened saving: " + bad)
need("may receive a referral fee from Superior Pergola Ireland" in flat and "paid by the supplier" in flat,
     "O13 the referral disclosure")

# O14
neg = low.replace("none is a plotnua partner", "")
for bad in ("plotnua partner", "our partner", "partnered", "official partner", "partner of plotnua", "authorised", "authorized",
            "approved installer", "recommended installer", "accredited by plotnua"):
    need(bad not in neg, "O14 partner wording: " + bad)
if mk:
    lst = re.search(r'<ul class="or-makers.*?</ul>', mk.group(0), re.S)
    need(lst, "O14 the researched-installer list")
    if lst:
        L = lst.group(0)
        for n in ("Apex Verandas", "The Outdoor Scene", "QOLA"):
            need(n in L, "O14 researched installer missing: " + n)
        need("<a " not in L and "<img" not in L, "O14 no link or photograph in the researched-installer list")
need("PlotNua has no commercial relationship with the other installers named here" in flat and "none is a PlotNua partner" in flat,
     "O14 the no-partner statement")
need("No photographs from those installers are shown." in flat, "O14 no installer photographs")

# O15
need(not re.search(r"£\s?\d", flat), "O15 a sterling figure appears")
allowed = {"€80", "€2,500", "€8,100", "€21,000", "€10,895", "€12,795", "€1,000", "€1,200"}
euros = {e.rstrip(",.") for e in re.findall(r"€\s?\d[\d,]*(?:\.\d\d)?", flat)}
need(euros <= allowed, "O15 unexpected euro figures: %s" % sorted(euros - allowed))
adv = re.search(r'<div class="or-advert reveal">.*?</div>', s, re.S)
need(adv and "Advertised figures, checked 4 November 2026" in text(adv.group(0)) and "not quotes" in text(adv.group(0)),
     "O15 the advertised prices are labelled, dated and not quotes")

# O16
reg = json.loads(read("image-provenance-records.json"))
masters = {r["asset"] for r in reg["records"]}
der = {d["asset"]: d for d in reg["derivatives"]}
used = set(re.findall(r'(assets/(?:disc035|library)/img/DISC-035[^"\s,]+)', s + (card.group(0) if card else "")))
need(used, "O16 no DISC-035 image found")
M = ("assets/disc035/img/DISC-035-01-BEFORE-MASTER.png", "assets/disc035/img/DISC-035-02-POSSIBLE-MASTER.png")
for u in sorted(used):
    need("MASTER.png" not in u, "O16 a master is served: " + u)
    d = der.get(u)
    need(d and d["derived_from"]["asset"] in M and d["derived_from"]["asset"] in masters,
         "O16 %s is not a recorded edit of a declared DISC-035 master" % u)
for mpath, h in zip(M, ("399e5bce", "180089ee")):
    r = next((x for x in reg["records"] if x["asset"] == mpath), None)
    need(r and r["class"] == "AI_ILLUSTRATION", "O16 %s must be declared AI_ILLUSTRATION" % mpath)
    need(r and r["sha256"].startswith(h), "O16 %s is the founder's approved file (sha256 %s...)" % (mpath, h))

# O17
need("or-dock-away" in s and "DISC-035 · the hero AI disclosure is never hidden" in s, "O17 the dock step-aside is missing")

# O18
ch6 = s[s.index('id="lg-ch06"'):] if 'id="lg-ch06"' in s else ""
for link in ("discovery-living-in-the-garden.html", "discovery-garden-retreat.html", "discovery-hidden-bins.html"):
    need(ch6.count('href="%s"' % link) >= 2, "O18 related link missing (closing exit and related card): " + link)

if problems:
    print("DISC-035 PAGE · FAILED")
    for p in problems:
        print("  " + p)
    sys.exit(1)
print("DISC-035 PAGE · OK (O1-O18)")
