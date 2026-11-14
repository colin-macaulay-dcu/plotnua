#!/usr/bin/env python3
"""Build/check the PlotArt artwork collections (SEO buyer-intent Phase 1 and 2, 13 Nov 2026):
plotart/artworks/ (every published, available work) and plotart/large-artworks/ (those of 100 cm or more on the
longest side, computed from the artist's published dimensions), and plotart/art-for-business/ (SEO commercial Phase 3,
14 Nov 2026: practical buying information for workplaces with a short generated selection of eight large works).
One shell, one stylesheet, one collection system.

    python3 atlas-tools/build-plotart-artworks.py           # write the page and its stylesheet
    python3 atlas-tools/build-plotart-artworks.py --check   # verify both match this source and the public collection

The page's editorial copy and shell are fixed here (a code release). Its collection region -- every published,
available work -- comes only from the approved public gallery exports (plotart/artists/<slug>/gallery.json), through
plotart_search_content.content("artworks/index.html", ...). The content pipeline refreshes exactly that region whenever
a gallery is published, a work is sold or withdrawn, or a price changes (plotart-gallery-publish.py -> C.refresh), and
the content-only boundary re-derives it before anything is released. Nothing reads Studio drafts or the database.
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plotart_seo as SEO  # noqa: E402
import plotart_search_content as C  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PATH = "artworks/index.html"
TITLE = "Original Irish Art for Sale | Buy Art from Irish Artists | PlotArt"
DESCRIPTION = ("Original art for sale by artists based or working in Ireland: paintings and works shown in full, "
               "with sizes and asking prices. Enquire directly with the artist.")
CSS_PATH = "assets/plotart-artworks.css"

CSS = '''/* PlotArt artwork collection (plotart/artworks/, 13 Nov 2026): a gallery wall, not a catalogue.
   Every work hangs uncropped on a shared line; the label sits beneath it. The art carries the colour. */
.pa-coll-hero{padding:clamp(56px,7vw,104px) 0 clamp(36px,4.5vw,60px);border-bottom:1px solid var(--line)}
.pa-coll-hero h1{font-size:clamp(44px,6vw,84px);line-height:1.02;letter-spacing:-.025em;margin:0 0 26px;max-width:15ch}
.pa-coll-hero .pa-lede{max-width:62ch}
.pa-coll-how{max-width:62ch;font-size:15.5px;line-height:1.7;color:var(--stone);margin:22px 0 0}
.pa-coll-actions{display:flex;flex-wrap:wrap;gap:12px 14px;margin-top:30px}
.pa-coll-wall{padding:clamp(40px,5vw,72px) 0 clamp(56px,7vw,104px)}
.pa-coll-count{font-size:12.5px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--bronze-text);margin:0 0 clamp(28px,3.5vw,48px)}
.pa-coll-grid{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:clamp(56px,6vw,96px) clamp(28px,3.4vw,56px)}
.pa-coll-work{min-width:0;display:flex;flex-direction:column}
.pa-coll-art{display:flex;align-items:flex-end;justify-content:center;height:clamp(260px,26vw,400px);text-decoration:none}
.pa-coll-art img{width:auto;height:auto;max-width:100%;max-height:100%;box-shadow:var(--shadow-art);transition:transform .45s ease,box-shadow .45s ease}
.pa-coll-art:hover img{transform:translateY(-3px);box-shadow:0 4px 6px rgba(0,0,0,.3),0 20px 38px rgba(0,0,0,.34),0 44px 74px rgba(0,0,0,.24)}
.pa-coll-label{padding-top:26px;border-top:1px solid var(--line);margin-top:28px}
.pa-coll-title{font-size:clamp(23px,1.9vw,28px);line-height:1.15;margin:0 0 6px}
.pa-coll-title a{color:var(--ivory);text-decoration:none}
.pa-coll-title a:hover{color:var(--terra-hover)}
.pa-coll-label p{margin:0}
.pa-coll-artist{font-size:15.5px;margin-bottom:10px!important}
.pa-coll-artist a{color:var(--lime);text-decoration-color:var(--line-2)}
.pa-coll-meta{font-size:14px;line-height:1.55;color:var(--stone)}
.pa-coll-size{white-space:nowrap}
.pa-coll-price{font-size:15px;color:var(--ivory);margin-top:10px!important;letter-spacing:.01em}
.pa-coll-credit{font-size:12.5px;color:var(--mute);margin-top:6px!important}
.pa-coll-empty{color:var(--stone)}
.pa-coll-more{padding:clamp(44px,5vw,76px) 0;border-top:1px solid var(--line)}
.pa-coll-more h2{font-size:clamp(30px,3.4vw,44px);line-height:1.12;margin:0 0 16px}
.pa-coll-more p{max-width:62ch}
.pa-coll-links{display:flex;flex-wrap:wrap;gap:12px 14px;margin-top:26px}
.pa-biz-sel{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:10px 28px;margin:0 0 clamp(18px,2vw,26px)}
.pa-biz-sel h2{font-size:clamp(30px,3.4vw,44px);line-height:1.12;margin:0}
.pa-biz-sel a{color:var(--lime);text-decoration-color:var(--line-2);font-size:15.5px}
.pa-biz-spaces{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(30px,3.6vw,52px) clamp(32px,4.5vw,72px);margin-top:clamp(26px,3vw,40px)}
.pa-biz-spaces h3{font-size:clamp(22px,1.8vw,26px);line-height:1.2;margin:0 0 10px;padding-top:20px;border-top:1px solid var(--line)}
.pa-biz-spaces p{margin:0;max-width:52ch}
.pa-biz-ask{list-style:none;margin:26px 0 0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px clamp(32px,4.5vw,72px);max-width:1080px}
.pa-biz-ask li{padding-left:18px;border-left:1px solid var(--line-2);max-width:52ch}
.pa-biz-ask strong{color:var(--ivory);font-weight:600}
@media (prefers-reduced-motion:reduce){.pa-coll-art img{transition:none}.pa-coll-art:hover img{transform:none}}
@media (max-width:1099px){.pa-coll-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.pa-coll-art{height:clamp(240px,38vw,380px)}}
@media (max-width:639px){.pa-coll-grid{grid-template-columns:1fr;gap:44px}.pa-coll-art{height:auto;max-height:none}.pa-coll-art img{max-height:72vh}
.pa-biz-spaces,.pa-biz-ask{grid-template-columns:1fr}.pa-coll-label{margin-top:20px;padding-top:18px}.pa-coll-actions .pa-btn,.pa-coll-links .pa-btn{max-width:100%;white-space:normal;text-align:center}}
'''

BODY = '''
<section class="pa-coll-hero"><div class="pa-wrap">
<p class="pa-eyebrow">PlotArt · Available artworks</p>
<h1>Discover original Irish art for sale.</h1>
<p class="pa-lede">Explore original artwork by artists based or working in Ireland. Every piece is shown whole, with the artist’s own description, dimensions and asking price. When a work stays with you, enquire directly with the artist about buying it.</p>
<p class="pa-coll-how">PlotArt introduces you to the artist. It doesn’t take payment or deliver artwork: the artist arranges any sale with you directly.</p>
<div class="pa-coll-actions"><a class="pa-btn pa-btn--ghost" href="../gallery/">Meet the artists →</a><a class="pa-btn pa-btn--ghost" href="../buy-original-art-ireland.html">Buying art &amp; prices →</a></div>
</div></section>
<section class="pa-coll-wall" aria-labelledby="collH"><div class="pa-wrap">
<h2 id="collH" class="pa-sr">Available original artworks</h2>
COLLECTION
</div></section>
<section class="pa-coll-more"><div class="pa-wrap">
<h2>Before you choose.</h2>
<p>Measure the wall you have in mind, read the medium and dimensions, and ask the artist about framing, delivery and the total price. Each artist’s gallery tells you more about their practice and the rest of their work. Buying for an office, hotel or other workplace? Read <a href="../art-for-business/">art for business</a>.</p>
<div class="pa-coll-links"><a class="pa-btn pa-btn--ghost" href="../art-size-calculator.html">What size art fits your wall? →</a><a class="pa-btn pa-btn--ghost" href="../choose-art-for-living-room.html">Choosing art for your living room →</a><a class="pa-btn pa-btn--ghost" href="../abstract-contemporary-art-ireland.html">Abstract &amp; contemporary art →</a><a class="pa-btn pa-btn--ghost" href="../large-artworks/">Large artworks, 100 cm or more →</a></div>
</div></section>
'''


LARGE_PATH = "large-artworks/index.html"
LARGE_TITLE = "Large Original Paintings & Artworks for Sale in Ireland | PlotArt"
LARGE_DESCRIPTION = ("Large original paintings and artworks for sale, each 100 cm or more, by artists based or working in "
                     "Ireland. See sizes and prices, and enquire with the artist.")
LARGE_BODY = '''
<section class="pa-coll-hero"><div class="pa-wrap">
<p class="pa-eyebrow">PlotArt · Large artworks</p>
<h1>Large original artworks for sale in Ireland.</h1>
<p class="pa-lede">Original paintings and works of 100 cm or more on their longest side, by artists based or working in Ireland. A large work can hold a whole wall: above a sofa, at the end of a hallway, in a reception area or a meeting room. It is seen from across the room and changes the space around it.</p>
<p class="pa-coll-how">Every work is shown whole, with the artist’s own dimensions and asking price. PlotArt introduces you to the artist. It doesn’t take payment, deliver or install artwork: the artist arranges any sale with you directly.</p>
<div class="pa-coll-actions"><a class="pa-btn pa-btn--ghost" href="../art-size-calculator.html">What size art fits your wall? →</a><a class="pa-btn pa-btn--ghost" href="../artworks/">All available artworks →</a></div>
</div></section>
<section class="pa-coll-wall" aria-labelledby="collH"><div class="pa-wrap">
<h2 id="collH" class="pa-sr">Available large original artworks</h2>
COLLECTION
</div></section>
<section class="pa-coll-more"><div class="pa-wrap">
<h2>Before you choose a large work.</h2>
<p><strong>Measure the wall and the room.</strong> Check the work’s stated dimensions against the wall you have in mind, and the distance it will usually be seen from. The free <a href="../art-size-calculator.html">PlotArt art size calculator</a> compares a work’s size with your wall or furniture.</p>
<p><strong>Check the way in.</strong> Measure doors, stairs and lifts along the route, especially for a large canvas or panel that can’t be rolled.</p>
<p><strong>Ask about weight and hanging.</strong> Ask the artist whether the work is framed, how much it weighs and what fixings it needs, and make sure the wall can take it.</p>
<p><strong>Agree delivery with the artist.</strong> Collection, delivery, any installation and the total price are arranged directly between you and the artist. Ask for them in writing before you pay.</p>
<p><strong>For a workplace or commercial interior,</strong> consider light, heat and where people will see the work, and ask the artist how it should be cared for. <a href="../art-for-business/">Art for business</a> has more on buying for a workplace.</p>
<div class="pa-coll-links"><a class="pa-btn pa-btn--ghost" href="../buy-original-art-ireland.html">Buying art &amp; prices →</a><a class="pa-btn pa-btn--ghost" href="../gallery/">Meet the artists →</a></div>
</div></section>
'''

BIZ_PATH = "art-for-business/index.html"
BIZ_TITLE = "Original Art for Offices & Businesses in Ireland | PlotArt"
BIZ_DESCRIPTION = ("Original paintings and artworks for offices, receptions, hotels and restaurants, by artists based or "
                   "working in Ireland. See sizes and prices.")
BIZ_BODY = '''
<section class="pa-coll-hero"><div class="pa-wrap">
<p class="pa-eyebrow">PlotArt · Art for business</p>
<h1>Original art for workplaces in Ireland.</h1>
<p class="pa-lede">Original paintings and works for offices, reception areas, meeting rooms, hotels and restaurants, by artists based or working in Ireland. Each work is shown whole, with the artist’s own dimensions and asking price, and you deal with the artist directly.</p>
<p class="pa-coll-how">PlotArt introduces you to the artist. It doesn’t take payment, source, deliver or install artwork, and it doesn’t offer art consultancy: the artist arranges any sale with you directly.</p>
<div class="pa-coll-actions"><a class="pa-btn pa-btn--ghost" href="../large-artworks/">Large artworks →</a><a class="pa-btn pa-btn--ghost" href="../artworks/">All available artworks →</a></div>
</div></section>
<section class="pa-coll-wall" aria-labelledby="collH"><div class="pa-wrap">
<div class="pa-biz-sel"><h2 id="collH">Large works, available now.</h2><a href="../large-artworks/">See every available large artwork →</a></div>
COLLECTION
</div></section>
<section class="pa-coll-more"><div class="pa-wrap">
<h2>Choosing for the space.</h2>
<p>A workplace is seen differently from a home: by more people, often in passing, and under office lighting. A few things to weigh before you shortlist a work.</p>
<div class="pa-biz-spaces">
<div><h3>Reception and entrance areas</h3><p>Work here is usually seen from across the room and on the way past, so scale matters. Works of 100 cm or more tend to hold a wall like this. Compare a work’s size with your wall in the <a href="../art-size-calculator.html">art size calculator</a>.</p></div>
<div><h3>Meeting rooms and boardrooms</h3><p>Here a work is seen from a seat, close up and for an hour at a time. A medium-sized piece hung at seated eye level can suit a room better than the largest canvas. Browse <a href="../artworks/">all available artworks</a>.</p></div>
<div><h3>Hotels, restaurants and cafés</h3><p>Think about daylight, heat, steam and how close guests will be. Ask the artist whether the work is framed or glazed and how it should be cared for in a busy room.</p></div>
<div><h3>Interior designers and architects</h3><p>Every work page gives the artist’s medium, materials and dimensions. Whether a work can be held while a scheme is approved is the artist’s decision: ask them directly.</p></div>
</div>
</div></section>
<section class="pa-coll-more"><div class="pa-wrap">
<h2>What to ask the artist.</h2>
<p>Every enquiry goes to the artist, who replies to you directly. Agree these points with them in writing before you pay.</p>
<ul class="pa-biz-ask">
<li><strong>The total price.</strong> What the asking price includes: framing, VAT where it applies, and delivery.</li>
<li><strong>An invoice.</strong> Whether the artist can invoice your business by name.</li>
<li><strong>Weight and hanging.</strong> Whether the work is framed, what it weighs, and what fixings it needs. Check that the wall can take it.</li>
<li><strong>Delivery and access.</strong> Collection or delivery, who hangs the work, and whether it fits through doors, stairs and lifts on the way in.</li>
<li><strong>Care.</strong> How to look after the work in your space: light, heat, humidity and cleaning.</li>
<li><strong>Timing.</strong> When the work can be collected or delivered.</li>
</ul>
<p style="margin-top:26px">To ask about a particular work, open it and use <em>Enquire about this work</em>. To ask an artist about their wider practice, use the enquiry on their gallery page. If you are considering works by more than one artist, contact each artist separately: each handles their own sales.</p>
<div class="pa-coll-links"><a class="pa-btn pa-btn--ghost" href="../gallery/">Meet the artists →</a><a class="pa-btn pa-btn--ghost" href="../buy-original-art-ireland.html">Buying art &amp; prices →</a><a class="pa-btn pa-btn--ghost" href="../art-size-calculator.html">What size art fits your wall? →</a></div>
</div></section>
'''
PAGES = {PATH: (TITLE, DESCRIPTION, BODY), LARGE_PATH: (LARGE_TITLE, LARGE_DESCRIPTION, LARGE_BODY),
         BIZ_PATH: (BIZ_TITLE, BIZ_DESCRIPTION, BIZ_BODY)}


def relink(fragment):
    """The shell is taken from plotart/index.html, whose links are relative to plotart/. This page sits one folder
    deeper (plotart/artworks/), so every relative href/src gains '../'. Absolute, root, mailto and fragment links stay."""
    return re.sub(r'(href|src|srcset)="(?!https?:|mailto:|tel:|#|/|data:)([^"]*)"', lambda m: '%s="../%s"' % (m.group(1), m.group(2)), fragment)


def render(packages, path=PATH):
    title, description, body_copy = PAGES[path]
    home = (ROOT / "plotart/index.html").read_text()
    header = re.search(r'<header class="pa-head.*?</header>', home, re.S).group(0).replace(' aria-current="page"', "")
    footer = re.search(r'<footer class="pa-foot">.*?</footer>', home, re.S).group(0)
    head = home.split("<head>", 1)[1].split("</head>", 1)[0]
    head = re.sub(r"<title>.*?</title>", "<title>" + html.escape(title) + "</title>", head)
    for kind, key, value in [("name", "description", description), ("property", "og:title", title), ("property", "og:description", description),
                             ("name", "twitter:title", title), ("name", "twitter:description", description), ("property", "og:url", SEO.canonical(path))]:
        head = re.sub(r'<meta ' + kind + '="' + key + '" content="[^"]*">', '<meta ' + kind + '="' + key + '" content="' + html.escape(value, quote=True) + '">', head)
    head = re.sub(r'<link rel="canonical" href="[^"]+">', '<link rel="canonical" href="' + SEO.canonical(path) + '">', head)
    if not SEO.indexable(path, SEO.switches()):
        head = head.replace('<meta name="robots" content="index, follow">', '<meta name="robots" content="noindex, follow">')
        head = re.sub(r'<link rel="canonical" href="[^"]+">\n?', "", head)
    # the homepage's own structured data describes the homepage; this page's data lives in its collection region
    head = re.sub(r'\s*<script type="application/ld\+json">.*?</script>', "", head, flags=re.S)
    head = relink(head) + '<link rel="stylesheet" href="../' + CSS_PATH + '">\n'
    body = body_copy.replace("COLLECTION", C.BEGIN + "\n" + C.content(path, packages) + "\n" + C.END)
    return ('<!DOCTYPE html>\n<html lang="en-IE" class="no-js">\n<head>' + head + '</head>\n<body class="pa">\n'
            '<a class="pa-skip" href="#main">Skip to content</a>\n' + relink(header) + '\n<main id="main" class="pa-coll">' + body + '</main>\n'
            + relink(footer) + '\n<script src="../assets/plotart.js" defer></script>\n<script src="/assets/identity/pn-menu.js?v=1" defer></script>\n</body>\n</html>\n')


def main():
    packages = SEO.public_packages(ROOT)
    expected = {ROOT / "plotart" / p: render(packages, p) for p in PAGES}
    expected[ROOT / "plotart" / CSS_PATH] = CSS
    if "--check" in sys.argv:
        bad = [str(p.relative_to(ROOT)) for p, t in expected.items() if not p.exists() or p.read_text() != t]
        if bad:
            raise SystemExit("ARTWORK COLLECTION · differs from reviewed source: " + ", ".join(bad))
        print("ARTWORK COLLECTIONS · OK — %d pages and styles match reviewed copy and the public collection; nothing written" % len(PAGES))
        return
    for p, t in expected.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(t)
    print("ARTWORK COLLECTIONS · built %s and plotart/%s" % (", ".join("plotart/" + p for p in PAGES), CSS_PATH))


if __name__ == "__main__":
    main()
