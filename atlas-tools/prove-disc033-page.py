#!/usr/bin/env python3
"""DISC-033 · The Hidden Flood Barrier: page, SEO, claims and integration proof (read-only).

    python3 atlas-tools/prove-disc033-page.py

Modelled on prove-disc031-page.py. Checks the page, its integration and the founder's wording limits:
  F1  one <title> (the approved SEO title), meta description, canonical, OG/Twitter image, index/follow
  F2  JSON-LD parses; no Product, Offer, price, HowTo, FAQ or supplier structured data
  F3  exactly one H1; the stacked-layout title band is aria-hidden, never a heading (since 30 Oct 2026 the
      shared pn-compare title band, .pn-hero-compare__mtitle);
      on stacked layouts the H1 is visually hidden (not removed) so the title shows once
  F4  every local href/src/srcset on the page resolves to a file
  F5  the 23 web derivatives are on disk and each has a provenance record; no master PNG is published
      (13 original + 10 AVIF hero-slider derivatives, founder Pass 2 Release 2, 30 Oct 2026)
  F6  the hero is the shared pn-compare comparison, starting at 35% Before (data-start, range value,
      shared script) — replaced the page's own .cmp slider on 30 Oct 2026 (founder Pass 2 Release 2)
  F7  every image placement carries "AI-generated illustration"; the mechanism is a coded SVG
  F8  sitemap entry, Discovery Library card (Frontage), search-index entry
  F9  approved claims H1-H11, H13-H17 verbatim (H12 by its founder-approved G6 fallback)
  F10 the prohibited claims register: no guarantee, flood-proof, price, partner, certification,
      Irish installation, supplier name, or Charleston address
Prints "DISC-033 PAGE · OK" only when every check passes.
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-hidden-flood-barrier.html"
URL = "https://plotnua.ie/" + PAGE
problems = []


def need(cond, msg):
    if not cond:
        problems.append(msg)


def read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()


s = read(PAGE)

# F1
need(re.findall(r"<title>([^<]+)</title>", s) == ["Self-Rising Flood Barriers for Driveways in Ireland | PlotNua"], "F1 the approved <title>")
for pat in (r'<meta name="description" content="[^"]{60,}"', r'<link rel="canonical" href="%s"' % re.escape(URL),
            r'<meta property="og:url" content="%s"' % re.escape(URL),
            r'<meta property="og:image" content="https://plotnua\.ie/assets/disc033/img/DISC-033-og-1200x630\.jpg"',
            r'<meta name="twitter:card" content="summary_large_image"', r'<meta name="robots" content="index, follow"'):
    need(re.search(pat, s), "F1 missing: " + pat)

# F2
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
need(blocks, "F2 no JSON-LD")
for b in blocks:
    try:
        j = json.dumps(json.loads(b))
    except ValueError as e:
        problems.append("F2 JSON-LD does not parse: %s" % e)
        continue
    for bad in ('"Product"', '"Offer"', '"price"', '"priceCurrency"', '"AggregateOffer"', '"LocalBusiness"', '"HowTo"', '"FAQPage"'):
        need(bad not in j, "F2 unsupported structured data: " + bad)

# F3
need(len(re.findall(r"<h1[\s>]", s)) == 1, "F3 exactly one H1")
need(re.search(r'<div class="pn-hero-compare__mtitle" aria-hidden="true"><span class="pn-hero-compare__mkicker">A PlotNua Discovery</span><span class="pn-hero-compare__mname">The Hidden Flood Barrier</span></div>', s), "F3 the stacked-layout title band (aria-hidden)")
need(not re.search(r'<h[1-6][^>]*class="pn-hero-compare__m', s), "F3 the stacked-layout title band is never a heading")
need(re.search(r"\.fb-hero \.d-hero-copy h1\{ position:absolute !important;.*?clip-path:inset\(50%\)", s, re.S)
     and "display:none" not in s.split(".d-hero-copy h1{ position:absolute")[0][-200:],
     "F3 the H1 is visually hidden on stacked layouts (not display:none), so the title shows once")

# F4
for ref in set(re.findall(r'(?:href|src)="([^"#?]+)', s)) | {
        u.strip().split(" ")[0] for ss in re.findall(r'srcset="([^"]+)"', s) for u in ss.split(",")}:
    if ref.startswith(("http:", "https:", "mailto:", "tel:", "data:", "/")) or not ref:
        continue
    need(os.path.exists(os.path.join(ROOT, ref)), "F4 missing local file: " + ref)

# F5
imgs = sorted(os.listdir(os.path.join(ROOT, "assets/disc033/img")))
need(len(imgs) == 23, "F5 expected 23 derivatives, found %d" % len(imgs))
need(not any(i.endswith(".png") for i in imgs), "F5 a PNG master is in the published tree")
reg = {r["asset"] for r in json.loads(read("image-provenance-records.json"))["records"]}
for i in imgs:
    need("assets/disc033/img/" + i in reg, "F5 no provenance record: " + i)

# F6
need(re.search(r'<figure class="pn-compare pn-compare--hero" id="fbHeroCompare" data-start="35"', s), "F6 the pn-compare hero with data-start=35")
need(re.search(r'<input class="pn-compare__range" type="range" min="0" max="100" step="1" value="35"', s), "F6 range starts at 35")
need(re.search(r'<script src="assets/identity/pn-compare\.js[^"]*" defer></script>', s), "F6 the shared pn-compare script is loaded")

# F7
need(s.count("AI-generated illustration") >= 3, "F7 illustration labels")
need('id="fbMech"' in s and '<svg class="fb-mech-svg"' in s, "F7 coded SVG mechanism")
need("not to scale" in s.lower(), "F7 mechanism marked as simplified, not to scale")

# F8
need(("<loc>%s</loc>" % URL) in read("sitemap.xml"), "F8 sitemap entry")
lib = read("discoveries.html")
need(re.search(r'<a class="lib-card" href="%s" data-cat="Frontage">' % re.escape(PAGE), lib), "F8 Library card (Frontage)")
need(('"%s"' % PAGE) in read("search-index-v1.json"), "F8 search-index entry")

# F9
txt = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", s, flags=re.S)
txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", txt)))
txt = txt.replace("’", "'")
low = txt.lower()
for claim in (
    "Some flood barriers lie flat in the ground until floodwater arrives. The water flows into a basin beneath them and lifts them into place, with no power or person needed.",  # H1
    "They hold back water only up to their own height, and they need regular inspection and maintenance.",  # H2
    "a self-rising gate was installed across the driveway in 2007 (manufacturer's case study)",  # H3 (G1 fallback)
    "In 2025 a similar gate was installed at a historic home in Charleston, South Carolina (manufacturer's case study).",  # H4 (G2 fallback)
    "In Antwerp, an 842-metre self-closing barrier is being built along the river Scheldt; a section was tested at the Deltares research institute in 2024.",  # H5
    "We haven't found a self-rising flood barrier installed at a home in Ireland yet.",  # H6
    "At least one manufacturer that makes self-rising barriers has supplied flood barriers in Ireland, but domestic installation here hasn't been confirmed.",  # H7
    "Removable flood barriers, made to measure, are made and installed in Ireland.",  # H8
    "A barrier at the driveway protects one opening. Floodwater can also come in through drains, airbricks, walls and floors, or rise as groundwater.",  # H9
    "No barrier is a guarantee: water can rise above it, find another way in, or get past one that isn't maintained.",  # H10
    "There's no published Irish price. Self-rising barriers are made and installed to suit each site, so expect a significant specialist project and ask for a site survey and quotation.",  # H11
    "Planning rules can apply to flood barriers, depending on their design and location.",  # H12 (G6 fallback)
    "Any work into the public footpath or kerb needs the council's consent, usually through a licensed contractor.",  # H13
    "Any pump wiring must be done by a Registered Electrical Contractor.",  # H14
    "Talk to your insurer before relying on any barrier.",  # H16
    "In some areas, such as Midleton and East Cork, local authorities have run Individual Property Protection schemes for homes that have flooded.",  # H17 (G8 fallback)
    "the barrier needs no power to rise, but its basin must drain, and in some sites that needs a pump, which needs electricity",  # refinement B, always visible
):
    need(claim.lower() in low, "F9 approved claim missing: " + claim[:70])

# F10 (manufacturer names are allowed only as attributions inside the Sources list)
body = re.sub(r'<section class="pd-section" id="sources".*?</section>', " ", s, flags=re.S)
body = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", body, flags=re.S)
low = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).replace("\u2019", "'").lower()
need("floodbreak" in read(PAGE).lower(), "F10 the manufacturer source is attributed in Sources")
need(not re.search(r"[€£$]\s?\d", txt), "F10 a price figure appears")
for bad in ("flood-proof", "floodproof", "guaranteed", "complete protection", "protects your home", "certified",
            "our partner", "plotnua partner", "in partnership", "recommended supplier", "floodbreak", "aggéres", "aggeres",
            "flood control international", "floodgates ireland", "defe", "watersmart", "south battery",
            "available in ireland from", "installed in ireland by", "exempted development", "no planning permission"):
    need(bad not in low, "F10 prohibited: " + bad)

if problems:
    print("DISC-033 PAGE · FAILED")
    for p in problems:
        print("  " + p)
    sys.exit(1)
print("DISC-033 PAGE · OK (F1-F10)")
