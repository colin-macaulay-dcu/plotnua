#!/usr/bin/env python3
"""DISC-015 · The Underground Swimming Pool: page, SEO and integration proof (read-only).

    python3 atlas-tools/prove-disc015-page.py

  S1  one <title>, meta description, canonical, Open Graph and Twitter image, index/follow
  S2  JSON-LD parses; no Product, Offer, price, LocalBusiness or Review data
  S3  exactly one H1
  S4  every local href/src/srcset on the page resolves to a file
  S5  the hero is the shared pn-compare component on the DISC-015 pair, opening on 100 % BEFORE
  S6  the approved AI disclosure is shown under the hero, and the reveal carries "AI-generated illustration"
  S7  sitemap entry, Discovery Library card, search-index entry
  S8  no euro or sterling figure; none of the prohibited claims (easy, cheap, guaranteed, exempt, partner...)
  S9  the approved planning and cost statements are present verbatim
  S10 the section drawing is present: an accessible SVG, all nine labelled parts, and the not-an-engineering-drawing note
  S11 real projects: text and external links only (no image in the section), each with its Explore link;
      the UK examples are labelled as beneath a reinstated garden, the Irish ones as below the house
  S12 the construction image: only the founder-approved DISC-015-Construction-Final (DISC-015-CONSTRUCTION copies)
      may appear; the superseded Construction-Revised and draft images never do
Prints "DISC-015 PAGE · OK" only when every check passes.
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-underground-swimming-pool.html"
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
for pat in (r'<meta name="description" content="[^"]{60,}"', r'<link rel="canonical" href="%s"' % re.escape(URL),
            r'<meta property="og:url" content="%s"' % re.escape(URL),
            r'<meta property="og:image" content="https://plotnua\.ie/assets/disc015/img/DISC-015-og-1200x630\.jpg"',
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
    need("DISC-015-BEFORE-" in f and "DISC-015-POSSIBLE-" in f, "S5 the hero must use the DISC-015 BEFORE/POSSIBLE pair")
    need('>Before</p>' in f and '>Possible</p>' in f, "S5 Before / Possible labels")

# S6
need(s.count("Illustrative AI-generated visualisation. Not an actual installation.") >= 1, "S6 hero disclosure")
rev = re.search(r'<section class="up-reveal".*?</section>', s, re.S)
need(rev and "AI-generated illustration" in rev.group(0), "S6 the reveal image must carry its AI label")

# S7
need(("<loc>%s</loc>" % URL) in read("sitemap.xml"), "S7 sitemap entry")
need(('href="%s"' % PAGE) in read("discoveries.html"), "S7 Discovery Library card")
need(('"%s"' % PAGE) in read("search-index-v1.json"), "S7 search-index entry")

# S8
need(not re.search(r"[€£]\s?\d", flat), "S8 a euro or sterling figure appears")
for bad in ("guarantee", "exempt from planning", "no planning permission", "cheap", "inexpensive", "affordable",
            "easy to build", "any garden", "every garden can", "our partner", "plotnua partner", "official partner",
            "recommended by plotnua", "low maintenance", "maintenance-free"):
    need(bad not in low, "S8 prohibited wording: " + bad)
need("why it isn’t for every garden" in low or "why it isn't for every garden" in low, "S8 the suitability caution")

# S9
for claim in (
    "An underground swimming pool should be treated as a project likely to require planning permission.",
    "We haven’t found published Irish prices for an underground pool.",
    "A Section 5 declaration can give a formal answer on whether specific works are exempt.",
):
    need(claim in flat, "S9 approved statement missing: " + claim[:60])

# S10
sec = re.search(r'<figure class="up-section.*?</figure>', s, re.S)
need(sec, "S10 no section drawing")
if sec:
    g = sec.group(0)
    need('<svg' in g and 'role="img"' in g and '<title id=' in g and '<desc id=' in g, "S10 the drawing is not an accessible SVG")
    need(len(re.findall(r'<li><b>\d</b>', g)) == 9, "S10 nine labelled parts")
    need("not an engineering drawing" in g, "S10 the not-an-engineering-drawing note")
    need("<image" not in g, "S10 the drawing must be pure vector")

# S11
rp = re.search(r'<section class="pd-section" id="real-projects".*?</section>', s, re.S)
need(rp, "S11 no Real Projects section")
if rp:
    r = rp.group(0)
    need("<img" not in r and "<picture" not in r, "S11 no photograph may appear until licensed")
    arts = re.findall(r'<article class="up-project".*?</article>', r, re.S)
    need(len(arts) == 4, "S11 expected four verified projects")
    for a in arts:
        need("Explore this project" in a and re.search(r'href="https://[^"]+"', a), "S11 a project without its Explore link")
    need("In Irish homes, below the house" in r and "In London, beneath a reinstated garden" in r, "S11 the two groups")
    need("has any arrangement with PlotNua" in r, "S11 the no-arrangement statement")

# S12
for bad in ("Construction-Revised", "draft.png", "DISC-015-Construction-Revised"):
    need(bad not in s, "S12 superseded construction image referenced: " + bad)
for m in re.findall(r'assets/disc015/img/(DISC-015-[A-Z]+)', s):
    need(m in ("DISC-015-BEFORE", "DISC-015-POSSIBLE", "DISC-015-POOL", "DISC-015-CONSTRUCTION", "DISC-015-og", "DISC-015-03"),
         "S12 unexpected DISC-015 image " + m)

if problems:
    print("DISC-015 PAGE · FAILED")
    for p in problems:
        print("  " + p)
    sys.exit(1)
print("DISC-015 PAGE · OK (S1-S12)")
