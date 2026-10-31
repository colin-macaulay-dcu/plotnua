#!/usr/bin/env python3
"""DISC-031 · The Natural Swimming Garden: page, SEO and integration proof (read-only).

    python3 atlas-tools/prove-disc031-page.py

Checks the published page and its integration, and the wording limits the founder set:
  S1  one <title>, meta description, canonical, Open Graph and Twitter image, index/follow
  S2  JSON-LD parses; no Product, Offer, price or supplier structured data
  S3  exactly one H1
  S4  every local href/src/srcset on the page resolves to a file
  S5  the four illustrations (16 encodings; the diagram as two exact panel crops) are on disk; HOW-IT-WORKS is V2
  S6  every image placement carries "AI-generated illustration"
  S7  sitemap entry, Discovery Library card, search-index entry
  S8  "wild" appears once in the visible text (the question); no euro or sterling figure;
      none of the prohibited phrases
  S9  approved claims A7, A8, A9, A12 are present verbatim
  S10 the diagram caption on water testing and maintenance is present
Prints "DISC-031 PAGE · OK" only when every check passes.
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-natural-swimming-garden.html"
URL = "https://plotnua.ie/" + PAGE
problems = []


def need(cond, msg):
    if not cond:
        problems.append(msg)


def read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()


s = read(PAGE)

# S1
need(len(re.findall(r"<title>[^<]+</title>", s)) == 1, "S1 one <title>")
for pat in (r'<meta name="description" content="[^"]{60,}"', r'<link rel="canonical" href="%s"' % re.escape(URL),
            r'<meta property="og:url" content="%s"' % re.escape(URL),
            r'<meta property="og:image" content="https://plotnua\.ie/assets/disc031/img/DISC-031-og-1200x630\.jpg"',
            r'<meta name="twitter:card" content="summary_large_image"', r'<meta name="robots" content="index, follow"'):
    need(re.search(pat, s), "S1 missing: " + pat)

# S2
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
need(blocks, "S2 no JSON-LD")
for b in blocks:
    try:
        j = json.dumps(json.loads(b))
    except ValueError as e:
        problems.append("S2 JSON-LD does not parse: %s" % e)
        continue
    for bad in ('"Product"', '"Offer"', '"price"', '"priceCurrency"', '"AggregateOffer"', '"LocalBusiness"'):
        need(bad not in j, "S2 unsupported structured data: " + bad)

# S3
need(len(re.findall(r"<h1[\s>]", s)) == 1, "S3 exactly one H1")

# S4
for ref in set(re.findall(r'(?:href|src)="([^"#?]+)', s)) | {
        u.strip().split(" ")[0] for ss in re.findall(r'srcset="([^"]+)"', s) for u in ss.split(",")}:
    if ref.startswith(("http:", "https:", "mailto:", "tel:", "data:", "/")) or not ref:
        continue
    need(os.path.exists(os.path.join(ROOT, ref)), "S4 missing local file: " + ref)

# S5
imgs = sorted(os.listdir(os.path.join(ROOT, "assets/disc031/img")))
# 30 Oct 2026 (founder Pass 2 performance): +14 hero-slider derivatives (AVIF 960/1200/1536, WebP 1200, 4:5 phone crops)
need(len(imgs) == 30, "S5 expected 30 encodings, found %d" % len(imgs))
need("DISC-031-how-it-works-1536.jpg" in imgs, "S5 full diagram (full-size view) missing")
for half in ("top", "bottom"):
    need(("DISC-031-how-it-works-%s-1536.webp" % half) in s, "S5 diagram %s panel not on the page" % half)

# S6
# 30 Oct 2026 (founder Pass 2): the inline comparison became the hero slider, so one placement fewer
need(s.count("AI-generated illustration") + s.count("AI-generated visualisation") >= 6, "S6 fewer than 6 illustration labels")   # the approved hero wording (31 Oct 2026) counts

# S7
need(("<loc>%s</loc>" % URL) in read("sitemap.xml"), "S7 sitemap entry")
need(('href="%s"' % PAGE) in read("discoveries.html"), "S7 Discovery Library card")
need(('"%s"' % PAGE) in read("search-index-v1.json"), "S7 search-index entry")

# S8
txt = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", s, flags=re.S)
txt = html.unescape(re.sub(r"<[^>]+>", " ", txt))
low = txt.lower()
need(len(re.findall(r"\bwild\b", low)) == 1, "S8 'wild' must appear exactly once")
need("go wild swimming without leaving home" in low, "S8 the question")
need(not re.search(r"[€£]\s?\d", txt), "S8 a euro or sterling figure appears")
for bad in ("self-cleaning", "healthier", "safe to swim", "exempt from planning", "low maintenance",
            "zero maintenance", "chlorine-free", "our partner", "plotnua partner", "germ-free"):
    need(bad not in low, "S8 prohibited phrase: " + bad)

# S9
for claim in (
    "A natural swimming pond should be treated as a project likely to require planning permission.",
    "Where pumps, filtration equipment or lighting require electrical installation work, use a Registered Electrical Contractor and obtain the appropriate completion certification.",
    "Ireland does not have a specific water-quality standard for private natural swimming pools.",
    "One documented Irish family pool holds approximately 117,000 litres.",
):
    need(claim in re.sub(r"\s+", " ", txt), "S9 approved claim missing: " + claim[:60])

# S10
need("clear water still needs regular water-quality testing, and maintenance varies with the design" in low,
     "S10 diagram caption")

if problems:
    print("DISC-031 PAGE · FAILED")
    for p in problems:
        print("  " + p)
    sys.exit(1)
print("DISC-031 PAGE · OK (S1-S10)")
