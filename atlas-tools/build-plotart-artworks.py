#!/usr/bin/env python3
"""Build/check the PlotArt artwork collections (SEO buyer-intent Phase 1 and 2, 13 Nov 2026):
plotart/artworks/ (every published, available work) and plotart/large-artworks/ (those of 100 cm or more on the
longest side, computed from the artist's published dimensions). One shell, one stylesheet, one collection system.

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
# Refine (founder approval 21 Nov 2026): All Artworks ONLY. Two hand-written assets, loaded by that page alone, so Large
# Artworks, the artists' galleries and the shared plotart.js are untouched.
REFINE_CSS = "assets/plotart-refine.css"
REFINE_JS = "assets/plotart-refine.js"

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
.pa-coll-note{max-width:62ch;font-size:15px;line-height:1.65;color:var(--stone);margin:-14px 0 clamp(28px,3.5vw,48px)}
.pa-coll-list{max-width:62ch;margin:0;padding-left:1.2em}
.pa-coll-list li{margin:0 0 12px;line-height:1.65}
@media (prefers-reduced-motion:reduce){.pa-coll-art img{transition:none}.pa-coll-art:hover img{transform:none}}
@media (max-width:1099px){.pa-coll-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.pa-coll-art{height:clamp(240px,38vw,380px)}}
@media (max-width:639px){.pa-coll-grid{grid-template-columns:1fr;gap:44px}.pa-coll-art{height:auto;max-height:none}.pa-coll-art img{max-height:72vh}
.pa-coll-label{margin-top:20px;padding-top:18px}.pa-coll-actions .pa-btn,.pa-coll-links .pa-btn{max-width:100%;white-space:normal;text-align:center}}
'''

BODY = '''
<section class="pa-coll-hero"><div class="pa-wrap">
<p class="pa-eyebrow">PlotArt · Available artworks</p>
<h1>Discover original Irish art for sale.</h1>
<p class="pa-lede">Explore original artwork by artists based or working in Ireland. Every piece is shown whole, with the artist’s own description, dimensions and asking price. When a work stays with you, enquire directly with the artist about buying it.</p>
<p class="pa-coll-how">Each artist is the seller of their own work. Selected works can be bought online through PlotArt’s secure checkout, with delivery and returns shown before you pay; for any work, you can enquire with the artist.</p>
<div class="pa-coll-actions"><a class="pa-btn pa-btn--ghost" href="../gallery/">Meet the artists →</a><a class="pa-btn pa-btn--ghost" href="../buy-original-art-ireland.html">Buying art &amp; prices →</a></div>
</div></section>
<section class="pa-coll-wall" aria-labelledby="collH"><div class="pa-wrap">
<h2 id="collH" class="pa-sr">Available original artworks</h2>
COLLECTION
</div></section>
<section class="pa-coll-more"><div class="pa-wrap">
<h2>Before you choose.</h2>
<p>Measure the wall you have in mind, read the medium and dimensions, and ask the artist about framing, delivery and the total price. Each artist’s gallery tells you more about their practice and the rest of their work. If nothing here suits the space, you can <a href="../commissions/" data-pa-track="artworks_commissions">commission a new work from an Irish artist</a>.</p>
<div class="pa-coll-links"><a class="pa-btn pa-btn--ghost" href="../art-size-calculator.html">What size art fits your wall? →</a><a class="pa-btn pa-btn--ghost" href="../choose-art-for-living-room.html">Choosing art for your living room →</a><a class="pa-btn pa-btn--ghost" href="../abstract-contemporary-art-ireland.html">Abstract &amp; contemporary art →</a><a class="pa-btn pa-btn--ghost" href="../large-artworks/">Large artworks, 100 cm or more →</a><a class="pa-btn pa-btn--ghost" href="../landscape-paintings-ireland/">Landscape paintings →</a><a class="pa-btn pa-btn--ghost" href="../original-art-under-500/">Original art for smaller budgets →</a></div>
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
<p class="pa-coll-how">Every work is shown whole, with the artist’s own dimensions and asking price. The artist is the seller and arranges delivery: PlotArt doesn’t deliver or install artwork. Selected works can be bought online through PlotArt’s secure checkout; for any work, you can enquire with the artist.</p>
<div class="pa-coll-actions"><a class="pa-btn pa-btn--ghost" href="../art-size-calculator.html">What size art fits your wall? →</a><a class="pa-btn pa-btn--ghost" href="../artworks/">Browse All Artworks →</a></div>
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
<p><strong>For a workplace or commercial interior,</strong> consider light, heat and where people will see the work, and ask the artist how it should be cared for.</p>
<p><strong>Need a particular size?</strong> Some PlotArt artists welcome commissions: you can <a href="../commissions/" data-pa-track="large_commissions">commission a work for a specific wall</a>.</p>
<div class="pa-coll-links"><a class="pa-btn pa-btn--ghost" href="../buy-original-art-ireland.html">Buying art &amp; prices →</a><a class="pa-btn pa-btn--ghost" href="../original-art-under-500/">Original art for smaller budgets →</a><a class="pa-btn pa-btn--ghost" href="../gallery/">Meet the artists →</a></div>
</div></section>
'''

# Growth package (27 Nov 2026): two filtered collections on the Large Artworks pattern (one shell, one stylesheet, the
# generated region refreshed at every publication). Outside the main navigation: reached from All Artworks, Large Artworks
# and the buying guide. Their search titles and descriptions come from C.HUB_META (live figures).
UNDER_PATH = "original-art-under-500/index.html"
UNDER_BODY = '''
<section class="pa-coll-hero"><div class="pa-wrap">
<p class="pa-eyebrow">PlotArt · Original art under €500</p>
<h1>Original art under €500.</h1>
<p class="pa-lede">A first original, a gift, or a smaller piece for a particular wall. These are the available works on PlotArt with a published asking price under €500, by artists based or working in Ireland. The list updates whenever artists publish, sell or reprice their work, and starts from the lowest price.</p>
<p class="pa-coll-how">“Original” here means work made by the artist: a one-off painting, drawing or mixed-media piece, or an original print made through a printmaking process. A monoprint is one of a kind; a screen print or etching may be one of a small edition. The medium is shown under each work, and the artwork page carries the artist’s own description, so you can see exactly what you would receive.</p>
<p class="pa-coll-how">Smaller works suit a shelf, a hallway, a desk or a group of pictures. Check a size against your wall or furniture with the free <a href="../art-size-calculator.html">art size calculator</a>. Each artist is the seller of their own work: when a piece appeals, enquire directly with the artist.</p>
<div class="pa-coll-actions"><a class="pa-btn pa-btn--ghost" href="../art-size-calculator.html">What size art fits your wall? →</a><a class="pa-btn pa-btn--ghost" href="../artworks/">Browse All Artworks →</a></div>
</div></section>
<section class="pa-coll-wall" aria-labelledby="collH"><div class="pa-wrap">
<h2 id="collH" class="pa-sr">Available original artworks under €500</h2>
COLLECTION
</div></section>
<section class="pa-coll-more"><div class="pa-wrap">
<h2>Before you buy.</h2>
<ul class="pa-coll-list">
<li><strong>Measure first.</strong> Sizes are the artist’s own, in centimetres. Ask whether the stated size includes a frame or mount.</li>
<li><strong>Know what you are buying.</strong> Is it a one-off work or a print? For a print, ask about the edition size, its number and whether it is signed.</li>
<li><strong>Ask what the price includes.</strong> Framing, any VAT that applies and how the work will reach you are agreed with the artist.</li>
<li><strong>Buying a gift?</strong> Tell the artist, and ask how the work is packed and whether it can be collected or sent.</li>
<li><strong>Get it in writing.</strong> Confirm the work, the total price and the arrangements before you pay.</li>
</ul>
<div class="pa-coll-links"><a class="pa-btn pa-btn--ghost" href="../buy-original-art-ireland.html">Buying art &amp; prices →</a><a class="pa-btn pa-btn--ghost" href="../landscape-paintings-ireland/">Landscape paintings →</a><a class="pa-btn pa-btn--ghost" href="../gallery/">Meet the artists →</a></div>
</div></section>
'''

LANDSCAPE_PATH = "landscape-paintings-ireland/index.html"
LANDSCAPE_BODY = '''
<section class="pa-coll-hero"><div class="pa-wrap">
<p class="pa-eyebrow">PlotArt · Landscape paintings</p>
<h1>Landscape paintings for sale in Ireland.</h1>
<p class="pa-lede">Paintings and mixed-media works of landscape, coast and place, by artists based or working in Ireland: from closely observed woodland and riverbanks to coastal scenes and abstracted views of the land. Every work is shown whole, with the artist’s own dimensions and asking price.</p>
<p class="pa-coll-how">This is a curated selection. PlotArt chooses each work from its title, the artist’s own description and the image, and the page changes as works are sold or published. Some works stay close to a place the artist knows; others move towards abstraction, holding on to its light, colour and structure.</p>
<p class="pa-coll-how">Sizes vary from small framed works on paper to larger paintings. Check a work against your wall with the free <a href="../art-size-calculator.html">art size calculator</a>, or see <a href="../large-artworks/">large artworks of 100 cm or more</a>. When a work stays with you, enquire directly with the artist.SPACES_NOTE</p>
<div class="pa-coll-actions"><a class="pa-btn pa-btn--ghost" href="../art-size-calculator.html">What size art fits your wall? →</a><a class="pa-btn pa-btn--ghost" href="../artworks/">Browse All Artworks →</a></div>
</div></section>
<section class="pa-coll-wall" aria-labelledby="collH"><div class="pa-wrap">
<h2 id="collH" class="pa-sr">Available landscape, coastal and place-based works</h2>
COLLECTION
</div></section>
<section class="pa-coll-more"><div class="pa-wrap">
<h2>Before you choose.</h2>
<ul class="pa-coll-list">
<li><strong>Think about the light.</strong> A landscape changes with the light in the room. Ask the artist how the work is finished, and keep works on paper out of direct sun.</li>
<li><strong>Measure the wall.</strong> Compare the stated dimensions with the wall and the distance the work will be seen from.</li>
<li><strong>Ask about framing.</strong> Check whether the work is framed or glazed, and whether the size given includes the frame.</li>
<li><strong>Get it in writing.</strong> Confirm the work, the total price and the arrangements with the artist before you pay.</li>
</ul>
<div class="pa-coll-links"><a class="pa-btn pa-btn--ghost" href="../buy-original-art-ireland.html">Buying art &amp; prices →</a><a class="pa-btn pa-btn--ghost" href="../original-art-under-500/">Original art for smaller budgets →</a><a class="pa-btn pa-btn--ghost" href="../gallery/">Meet the artists →</a></div>
</div></section>
'''


def spaces_note():
    """Spaces is PlotArt's curated gallery for work about place. While it is in preparation the page says so and links
    nothing (no placeholder is presented as open); it links to Spaces only once the founder's switch opens it."""
    state = SEO.switches().get("spaces_gallery_state")
    if state == "open":
        return ' For a curated gallery of work about place, visit <a href="../spaces/">Spaces</a>.'
    return " PlotArt’s Spaces gallery, a curated home for work about place, is in preparation."


PAGES = {PATH: (TITLE, DESCRIPTION, BODY), LARGE_PATH: (LARGE_TITLE, LARGE_DESCRIPTION, LARGE_BODY),
         UNDER_PATH: (None, None, UNDER_BODY), LANDSCAPE_PATH: (None, None, LANDSCAPE_BODY)}


def relink(fragment):
    """The shell is taken from plotart/index.html, whose links are relative to plotart/. This page sits one folder
    deeper (plotart/artworks/), so every relative href/src gains '../'. Absolute, root, mailto and fragment links stay."""
    return re.sub(r'(href|src|srcset)="(?!https?:|mailto:|tel:|#|/|data:)([^"]*)"', lambda m: '%s="../%s"' % (m.group(1), m.group(2)), fragment)


def render(packages, path=PATH):
    _t, _d, body_copy = PAGES[path]
    # SEO and analytics package (26 Nov 2026, section 2.4): the search title and the description, whose figures are
    # computed from the published galleries and refreshed with the collection at every publication
    title, description = C.hub_meta(path, packages)
    home = (ROOT / "plotart/index.html").read_text()
    header = re.search(r'<header class="pa-head.*?</header>', home, re.S).group(0).replace(' aria-current="page"', "")
    footer = re.search(r'<footer class="pa-foot">.*?</footer>', home, re.S).group(0)
    head = home.split("<head>", 1)[1].split("</head>", 1)[0].replace('\n<link rel="stylesheet" href="assets/plotart-join.css">', '').replace('\n<link rel="stylesheet" href="assets/plotart-home.css">', '').replace('\n<link rel="stylesheet" href="assets/plotart-galleries.css">', '').replace('\n<link rel="stylesheet" href="assets/plotart-beyond.css">', '')  # the Join styles (14 Nov 2026) and featured-artwork styles (17 Nov 2026) belong to the homepage only
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
    refine = C.COLLECTIONS[path].get("refine") is True
    if refine:
        head += '<link rel="stylesheet" href="../' + REFINE_CSS + '">\n'
    body = body_copy.replace("SPACES_NOTE", spaces_note()).replace("COLLECTION", C.BEGIN + "\n" + C.content(path, packages) + "\n" + C.END)
    return ('<!DOCTYPE html>\n<html lang="en-IE" class="no-js">\n<head>' + head + '</head>\n<body class="pa">\n'
            '<a class="pa-skip" href="#main">Skip to content</a>\n' + relink(header) + '\n<main id="main" class="pa-coll">' + body + '</main>\n'
            + relink(footer) + '\n<script src="../assets/plotart.js" defer></script>\n'
            + ('<script src="../' + REFINE_JS + '" defer></script>\n' if refine else '')
            + '<script src="/assets/identity/pn-menu.js?v=1" defer></script>\n</body>\n</html>\n')


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
