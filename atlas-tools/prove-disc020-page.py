#!/usr/bin/env python3
"""DISC-020 · Stay in the House You Love: page, SEO, claims and integration proof (read-only).

    python3 atlas-tools/prove-disc020-page.py

  S1  one <title>, meta description, canonical, Open Graph and Twitter image, index/follow
  S2  JSON-LD parses; no Product, Offer, price, LocalBusiness or Review data
  S3  exactly one H1, and it is the approved title; the approved hero question is the subtitle
  S4  every local href/src/srcset on the page resolves to a file
  S5  the hero is the shared pn-compare component on the DISC-020 pair, opening on 100 % BEFORE, with labels
  S6  the approved AI disclosure is under the hero and in the slider; the page names no image as a photograph
  S7  sitemap entry, Discovery Library card (existing category), search-index entry
  S8  prohibited wording absent (guaranteed, affordable, easy, partner, every home, never needs planning ...)
  S9  euro figures appear only as the verified grant figures and the one labelled, sourced, dated advertised figure;
      no sterling figure
  S10 the six chapters in order, and the four ways up (A-D) each with an accessible drawing; the not-to-scale note
  S11 maker claims are marked, and the page says they are not independently tested
  S12 grants: the approved verified statements are present, with eligibility limits (means test, approval first)
  S13 planning and fire statements carry their limits (protected structures; professional design)
  S14 no supplier gallery or supplier link; no supplier is called a partner; the only provider named is the
      source of the advertised figure, inside its labelled box and the sources list
  S15 the closing decision is the shared two-route component: Route B is the existing WhatsApp link, "Free for
      homeowners", no form
  S16 images: only DISC-020 copies that are recorded edits of the two declared masters; no master PNG is served
  S17 the hero AI disclosure is never covered by the Back dock or pill (the page-local step-aside is present)
Prints "DISC-020 PAGE · OK" only when every check passes.
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-stay-in-the-house-you-love.html"
URL = "https://plotnua.ie/" + PAGE
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

# S1
need(len(re.findall(r"<title>[^<]+</title>", s)) == 1, "S1 one <title>")
for pat in (r'<meta name="description" content="[^"]{60,160}"', r'<link rel="canonical" href="%s"' % re.escape(URL),
            r'<meta property="og:url" content="%s"' % re.escape(URL),
            r'<meta property="og:image" content="https://plotnua\.ie/assets/disc020/img/DISC-020-og-1200x630\.jpg"',
            r'<meta name="twitter:card" content="summary_large_image"', r'<meta name="robots" content="index, follow"'):
    need(re.search(pat, s), "S1 missing: " + pat)

# S2
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
need(blocks, "S2 no JSON-LD")
for b in blocks:
    try:
        j = json.dumps(json.loads(b))
    except ValueError as e:
        problems.append("S2 JSON-LD does not parse: %s" % e); continue
    for bad in ('"Product"', '"Offer"', '"price"', '"priceCurrency"', '"AggregateOffer"', '"LocalBusiness"', '"Review"'):
        need(bad not in j, "S2 unsupported structured data: " + bad)

# S3
need(len(re.findall(r"<h1[\s>]", s)) == 1, "S3 exactly one H1")
need("<h1>Stay in the House You Love</h1>" in s, "S3 the H1 is the approved title")
need('<p class="subtitle">What if the home you love could grow with you?</p>' in s, "S3 the approved hero question")

# S4
for ref in set(re.findall(r'(?:href|src)="([^"#?]+)', s)) | {
        u.strip().split(" ")[0] for ss in re.findall(r'(?:srcset|imagesrcset)="([^"]+)"', s) for u in ss.split(",")}:
    if ref.startswith(("http:", "https:", "mailto:", "tel:", "data:", "/")) or not ref:
        continue
    need(os.path.exists(os.path.join(ROOT, ref)), "S4 missing local file: " + ref)

# S5
fig = re.search(r'<figure class="pn-compare pn-compare--hero"[^>]*>.*?</figure>', s, re.S)
need(fig, "S5 no pn-compare hero")
if fig:
    f = fig.group(0)
    need('data-start="100"' in f and 'value="100"' in f, "S5 the hero must open on 100% BEFORE")
    need("DISC-020-BEFORE-" in f and "DISC-020-POSSIBLE-" in f, "S5 the hero must use the DISC-020 BEFORE/POSSIBLE pair")
    need(f.index("pn-compare__possible") < f.index("pn-compare__before"), "S5 BEFORE must be the overlay layer")
    need('>Before</p>' in f and '>Possible</p>' in f, "S5 Before / Possible labels")
    need("DISC-020-BEFORE-M-750" in f and "DISC-020-POSSIBLE-M-750" in f, "S5 the phone crop (stair and lift in view)")
    need('class="pn-compare__range"' in f and "aria-label=" in f, "S5 keyboard/screen-reader control")
need("pn-compare.js" in s and "pn-compare.css" in s, "S5 the shared component's files")

# S6
need(s.count("Illustrative AI-generated visualisation. Not an actual installation.") >= 2, "S6 hero disclosure (slider and below)")
need("photograph of" not in low.replace("not photographs of an actual installation", "").replace("no photographs of them are shown", ""),
     "S6 an image must not be presented as a photograph")

# S7
need(("<loc>%s</loc>" % URL) in read("sitemap.xml"), "S7 sitemap entry")
lib = read("discoveries.html")
card = re.search(r'<a class="lib-card" href="%s" data-cat="([^"]+)">.*?</a>' % re.escape(PAGE), lib, re.S)
need(card, "S7 Discovery Library card")
if card:
    cats = set(re.findall(r'data-filter="([^"]+)"', lib)) - {"All"}
    need(card.group(1) in cats, "S7 the card's category must be an existing Library category")
need(('"%s"' % PAGE) in read("search-index-v1.json"), "S7 search-index entry")

# S8
neg = low.replace("not every home can take a lift", "").replace("no provider named here is a plotnua partner", "")
for bad in ("guarantee", "affordable", "cheap", "inexpensive", "easy to install", "easily", "every home can", "any home can",
            "suitable for every", "all homes", "no planning permission is needed", "never needs planning", "always exempt",
            "our partner", "plotnua partner", "official partner", "recommended by plotnua", "maintenance-free",
            "elderly", "frail", "struggling", "infirm", "fully accessible", "grant will cover", "you will qualify",
            "you qualify", "free lift"):
    need(bad not in neg, "S8 prohibited wording: " + bad)
need("not every home can take a lift" in low, "S8 the suitability caution")

# S9
need(not re.search(r"£\s?\d", flat), "S9 a sterling figure appears")
allowed = {"€40,000", "€37,500", "€62,501", "€75,000", "€20,000", "€8,000", "€11,000", "€19,000"}
euros = {e.rstrip(",") for e in re.findall(r"€\s?\d[\d,]*", flat)}
need(euros <= allowed, "S9 unexpected euro figures: %s" % sorted(euros - allowed))
adv = re.search(r'<div class="sh-advert reveal">.*?</div>', s, re.S)
need(adv, "S9 the advertised figure box")
if adv:
    a = html.unescape(adv.group(0))
    need("Advertised figure" in a and "accesslifts.ie" in a and "4 November 2026" in a and "not a quote" in a,
         "S9 the advertised figure must be labelled, sourced, dated and marked as not a quote")
    need("structural work" in a and "installation" in a and "VAT" in a, "S9 the advertised figure must say what may change the cost")
need(flat.count("€11,000") == 1, "S9 the advertised figure appears once, in its box")

# S10
order = [m for m in re.findall(r'id="lg-ch0(\d)"', s)]
need(order == ["1", "2", "3", "4", "5", "6"], "S10 six chapters in order (found %s)" % order)
ways = re.findall(r'<li class="sh-way[^"]*" aria-labelledby="shWay([A-D])">(.*?)</li>\s*(?=<li class="sh-way|</ul>)', s, re.S)
need([w[0] for w in ways] == ["A", "B", "C", "D"], "S10 the four ways up, A-D")
for k, w in ways:
    need('<svg' in w and 'role="img"' in w and 'aria-label="Illustrative drawing, not to scale' in w and "<image" not in w,
         "S10 way %s: an accessible, pure-vector drawing labelled not to scale" % k)
need("Illustrative drawings by PlotNua, not to scale" in flat, "S10 the not-to-scale caption")
for t in ("Compact through-floor lift", "Enclosed home lift", "Glass or design-led lift", "Alternatives",
          "Stairlift", "Platform lift", "Ground-floor living"):
    need(t in flat, "S10 missing: " + t)

# S11
need(s.count('<span class="sh-maker">Maker claim</span>') >= 5, "S11 maker claims must be marked")
need("we haven’t independently tested them" in flat, "S11 the maker-claim explanation")

# S12
for claim in ("Up to €40,000", "or 100% of the approved cost, whichever is less", "The works it lists include a stair lift or a through-floor lift.",
              "tapering to 30% between €62,501 and €75,000. No grant above €75,000.", "For a house less than 12 months old the maximum is €20,000.",
              "Up to €8,000", "For households with an income of up to €37,500.", "a grant must be approved before any work begins",
              "Eligibility is decided by your local authority"):
    need(claim in flat, "S12 approved grant statement missing: " + claim[:60])
need("means-tested" in low, "S12 the means test")

# S13
for claim in ("Works that affect only the interior of a house are generally exempted development.",
              "doesn’t apply automatically to a protected structure", "A Section 5 declaration from your local authority can give a formal answer.",
              "ask a competent professional to design and confirm it", "Registered Electrical Contractor", "declaration of conformity"):
    need(claim in flat, "S13 approved statement missing: " + claim[:60])

# S14
need("data-pn-supplier-gallery" not in s and "pn-supplier-gallery" not in s, "S14 no supplier gallery")
main_txt = re.search(r'<main id="pn-main">.*?</main>', s, re.S).group(0)
outside = main_txt.replace(adv.group(0) if adv else "", "")
outside = re.sub(r'<section class="pd-section" id="sources".*?</section>', "", outside, flags=re.S)
for name in ("Stiltz", "Pollock", "Stannah", "Aritco", "Cibes", "PVE", "Terry", "Access Lifts", "accesslifts", "John Preston"):
    need(name.lower() not in outside.lower(), "S14 a supplier is named outside the sourced advertised figure: " + name)
need("no provider named here is a PlotNua partner" in flat, "S14 the no-partner statement")

# S15
tr = re.search(r'<div class="pn-tr" data-two-route>.*?</div>\s*</div>\s*</div>', s, re.S)
need(tr, "S15 the shared two-route component")
if tr:
    t = tr.group(0)
    need('href="https://wa.me/353834036695"' in t and "Let PlotNua do the homework" in t and "Free for homeowners." in t,
         "S15 Route B must be the existing free WhatsApp conversation")
    need("Explore the possibilities yourself" in t, "S15 Route A")
need("<form" not in s.lower(), "S15 no form")
need("pn-two-route.css" in s, "S15 the component stylesheet")

# S16
reg = json.loads(read("image-provenance-records.json"))
masters = {r["asset"] for r in reg["records"]}
der = {d["asset"]: d for d in reg["derivatives"]}
used = set(re.findall(r'(assets/(?:disc020|library)/img/DISC-020[^"\s,]+)', s + (card.group(0) if card else "")))
need(used, "S16 no DISC-020 image found")
for u in sorted(used):
    need("MASTER.png" not in u, "S16 a master is served: " + u)
    d = der.get(u)
    need(d and d["derived_from"]["asset"] in ("assets/disc020/img/DISC-020-01-BEFORE-MASTER.png",
                                              "assets/disc020/img/DISC-020-02-POSSIBLE-MASTER.png")
         and d["derived_from"]["asset"] in masters, "S16 %s is not a recorded edit of a declared DISC-020 master" % u)
for m in ("assets/disc020/img/DISC-020-01-BEFORE-MASTER.png", "assets/disc020/img/DISC-020-02-POSSIBLE-MASTER.png"):
    r = next((x for x in reg["records"] if x["asset"] == m), None)
    need(r and r["class"] == "AI_ILLUSTRATION", "S16 %s must be declared AI_ILLUSTRATION" % m)
need(next(x for x in reg["records"] if x["asset"].endswith("DISC-020-01-BEFORE-MASTER.png"))["sha256"].startswith("084810b3"),
     "S16 the BEFORE master is the founder's approved file (sha256 084810b3...)")

# S17
need("sh-dock-away" in s and "DISC-020 · the hero AI disclosure is never hidden" in s, "S17 the dock step-aside is missing")

if problems:
    print("DISC-020 PAGE · FAILED")
    for p in problems:
        print("  " + p)
    sys.exit(1)
print("DISC-020 PAGE · OK (S1-S17)")
