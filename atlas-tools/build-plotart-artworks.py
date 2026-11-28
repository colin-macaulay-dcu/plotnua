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
.pa-coll-browse{max-width:62ch;font-size:15px;line-height:1.7;color:var(--stone);margin:26px 0 0}
.pa-coll-wall h2:not(.pa-sr){font-size:clamp(30px,3.4vw,44px);line-height:1.12;margin:0 0 22px}
.pa-coll-more h2+p,.pa-coll-more h2+ul{margin-top:0}
.pa-coll-more p+h2,.pa-coll-more ul+h2{margin-top:clamp(32px,4vw,52px)}
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
<p class="pa-coll-browse">Browse by medium, size and occasion: <a href="../oil-paintings-ireland/">oil paintings</a>, <a href="../original-prints-ireland/">original prints</a>, <a href="../mixed-media-art-ireland/">mixed media and collage</a>, <a href="../small-artworks/">small artworks</a>, <a href="../figurative-art-ireland/">figurative art</a>, <a href="../coastal-art-ireland/">coastal art</a>, <a href="../art-for-offices/">art for offices</a>, <a href="../art-gifts-ireland/">original art as a gift</a> and <a href="../collecting-art-ireland/">how to start a collection</a>.</p>
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
<div class="pa-coll-links"><a class="pa-btn pa-btn--ghost" href="../buy-original-art-ireland.html">Buying art &amp; prices →</a><a class="pa-btn pa-btn--ghost" href="../original-art-under-500/">Original art for smaller budgets →</a><a class="pa-btn pa-btn--ghost" href="../art-for-offices/">Art for offices &amp; workspaces →</a><a class="pa-btn pa-btn--ghost" href="../gallery/">Meet the artists →</a></div>
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
<div class="pa-coll-links"><a class="pa-btn pa-btn--ghost" href="../buy-original-art-ireland.html">Buying art &amp; prices →</a><a class="pa-btn pa-btn--ghost" href="../original-art-under-1000/">Original art for a first significant purchase →</a><a class="pa-btn pa-btn--ghost" href="../art-gifts-ireland/">Original art as a gift →</a><a class="pa-btn pa-btn--ghost" href="../landscape-paintings-ireland/">Landscape paintings →</a><a class="pa-btn pa-btn--ghost" href="../gallery/">Meet the artists →</a></div>
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
<div class="pa-coll-links"><a class="pa-btn pa-btn--ghost" href="../buy-original-art-ireland.html">Buying art &amp; prices →</a><a class="pa-btn pa-btn--ghost" href="../coastal-art-ireland/">Coastal &amp; seascape art →</a><a class="pa-btn pa-btn--ghost" href="../original-art-under-500/">Original art for smaller budgets →</a><a class="pa-btn pa-btn--ghost" href="../gallery/">Meet the artists →</a></div>
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


# =====================================================================================================================
# Growth 3 landing pages (28 Nov 2026; strategy doc 25, section 3). Ten more pages on this same shell, stylesheet and
# generated region (plotart_search_content.LANDING holds each page's test; C.LANDING_META its live title and
# description). Outside the main navigation: linked from All Artworks, the buying guide and related collections. No euro
# figure appears in this fixed copy except the one declared threshold on the under-€1,000 page (guard L3).
# ---------------------------------------------------------------------------------------------------------------------
def _hero(eyebrow, h1, paras, actions=None):
    acts = actions or '<a class="pa-btn pa-btn--ghost" href="../art-size-calculator.html">What size art fits your wall? →</a><a class="pa-btn pa-btn--ghost" href="../artworks/">Browse All Artworks →</a>'
    return ('\n<section class="pa-coll-hero"><div class="pa-wrap">\n<p class="pa-eyebrow">PlotArt · %s</p>\n<h1>%s</h1>\n%s\n'
            '<div class="pa-coll-actions">%s</div>\n</div></section>' % (eyebrow, h1, "\n".join(paras), acts))


def _wall(label, visible=None):
    head = '<h2 id="collH">%s</h2>' % visible if visible else '<h2 id="collH" class="pa-sr">%s</h2>' % label
    return '\n<section class="pa-coll-wall" aria-labelledby="collH"><div class="pa-wrap">\n%s\nCOLLECTION\n</div></section>' % head


def _more(blocks, links):
    return ('\n<section class="pa-coll-more"><div class="pa-wrap">\n%s\n<div class="pa-coll-links">%s</div>\n</div></section>\n' % (
        "\n".join(blocks), "".join('<a class="pa-btn pa-btn--ghost" href="%s">%s →</a>' % l for l in links)))


def _list(items):
    return '<ul class="pa-coll-list">\n%s\n</ul>' % "\n".join("<li><strong>%s</strong> %s</li>" % i for i in items)


HIRE_LINE = ("Alongside artwork sales, we are developing flexible art hire arrangements for commercial spaces, subject to artwork "
             "availability and agreement with the individual artist.")

U1000_BODY = _hero("Original art under €1,000", "Original art under €1,000.", [
    '<p class="pa-lede">A first significant purchase: a painting, an original print or a mixed-media work with real presence on a wall, bought directly from the artist who made it. These are the available works on PlotArt with a published asking price under €1,000, by artists based or working in Ireland. The list updates whenever artists publish, sell or reprice their work.</p>',
    '<p class="pa-coll-how">This range sits above <a href="../original-art-under-500/">original art for smaller budgets</a>. Here you will find square canvases, acrylic paintings on wood panel, layered works on paper and hand-pulled screen prints: pieces for a living-room wall, a bedroom or a study as much as a shelf. The highest prices come first, so the larger works lead.</p>',
    '<p class="pa-coll-how">Every work is shown whole, with the artist’s own medium, dimensions and asking price. Each artist is the seller of their own work: when a piece appeals, enquire directly with the artist.</p>']) + _wall(
    "Available original artworks under €1,000") + _more([
        "<h2>Making a first significant purchase.</h2>",
        _list([("Start with the wall.", 'Measure it, and compare the work’s dimensions with the furniture below it. The free <a href="../art-size-calculator.html">art size calculator</a> shows the proportion.'),
               ("Painting or print?", 'A painting or mixed-media work exists once. An original print may be one of a small edition: see <a href="../original-prints-ireland/">original prints</a> for how editions work.'),
               ("Look closely at the surface.", "Ask the artist for a detail photograph: texture, varnish and the edges of a canvas or panel. Ask whether the sides are painted or the work is meant to be framed."),
               ("Ask what the price includes.", "Framing, any VAT that applies, packing and collection or delivery are agreed with the artist."),
               ("Keep the records.", "Ask for an invoice that names the title, medium, size and year, and keep the artist’s description with it.")])],
    [("../buy-original-art-ireland.html", "Buying art &amp; prices"), ("../small-artworks/", "Small original artworks"), ("../collecting-art-ireland/", "Starting an art collection")])

PRINTS_BODY = _hero("Original prints", "Original prints and limited editions.", [
    '<p class="pa-lede">Hand-made prints by artists based or working in Ireland: multi-layered screen prints, etched intaglio prints and one-of-a-kind monoprints. Each is made by the artist through a printmaking process, not reproduced from a painting, and is shown here with its size, its asking price and, where the artist states it, its edition.</p>',
    '<p class="pa-coll-how">Prints sit across a wide range: small editioned screen prints on fine paper make a natural first original, while large hand-embellished monoprints hold a wall like a painting. The medium line under each work gives the artist’s own process.</p>']) + _wall(
    "Available original prints") + _more([
        "<h2>What makes a print original.</h2>",
        "<p>An original print starts on a screen, a plate or a block that the artist prepares. Each colour or layer is printed by hand, so every sheet is made separately and can differ slightly from the next. A reproduction, by contrast, copies an existing artwork by photographic or digital means.</p>",
        "<p>Screen prints build an image in flat, saturated layers of colour, one stencil at a time. Intaglio prints are etched into a metal plate and inked into its grooves, which gives a fine, slightly embossed line. A monoprint is printed once and cannot be repeated: like a painting, it is one of a kind.</p>",
        "<h2>Editions and numbers.</h2>",
        "<p>An edition is the number of impressions the artist chooses to print. A pencilled number such as 3/10 means the third of ten. A smaller edition makes each impression scarcer, but size alone does not make a print better: look at the image, the paper and the printing.</p>",
        "<h2>Framing and care.</h2>",
        _list([("Frame behind glazing.", "Use an acid-free mount and keep the print away from direct sun and damp."),
               ("Handle by the edges.", "Unframed sheets should be held by the margins, with clean, dry hands."),
               ("Ask about signing.", "Ask the artist whether the print is signed and numbered, and keep any note or certificate with it.")])],
    [("../original-art-under-500/", "Original art for smaller budgets"), ("../mixed-media-art-ireland/", "Mixed media &amp; collage"), ("../buy-original-art-ireland.html", "Buying art &amp; prices")])

OIL_BODY = _hero("Oil paintings", "Original oil paintings for sale in Ireland.", [
    '<p class="pa-lede">Oil paintings on linen, canvas, panel and paper by artists based or working in Ireland: from expansive abstract canvases and round wooden tondos to landscapes painted on dibond and figures on panel. Every painting is shown whole, with the artist’s own medium line, dimensions and asking price.</p>',
    '<p class="pa-coll-how">Oil paint dries slowly, so a painter can blend, glaze and rework a surface over days or weeks. The result is depth of colour and a range of texture, from thin, translucent layers to heavy, physical brushwork, which is best judged in a close photograph or in person. Ask the artist for detail images before you decide.</p>',
    '<p class="pa-coll-how">Each artist is the seller of their own work: when a painting stays with you, enquire directly with the artist.</p>']) + _wall(
    "Available original oil paintings") + _more([
        "<h2>Living with an oil painting.</h2>",
        _list([("Choose the light.", "Hang it away from direct sun, radiators, fireplaces and damp walls. Even, indirect light shows colour and texture best."),
               ("Ask about varnish.", "Ask whether the painting is varnished. To clean it, dust lightly with a soft, dry brush; never use water or cleaning products."),
               ("Decide on framing.", "Many contemporary oils are shown unframed with painted edges; others suit a floating frame. Ask the artist which they intend."),
               ("Allow for curing.", "A recently finished oil painting can take months to cure fully. Ask when it was completed and how it should be handled."),
               ("Check the weight.", 'Large canvases and panels can be heavy. Ask about fixings, and see <a href="../large-artworks/">large artworks</a> for works of 100 cm or more.')])],
    [("../large-artworks/", "Large artworks"), ("../mixed-media-art-ireland/", "Mixed media &amp; collage"), ("../buy-original-art-ireland.html", "Buying art &amp; prices")])

MIXED_BODY = _hero("Mixed media &amp; collage", "Mixed media and collage art.", [
    '<p class="pa-lede">Works that combine materials: acrylic with collage and resin, spray paint with oil stick and pencil, raw silk with oil, print with ink and pen. By artists based or working in Ireland, each shown whole with the artist’s own account of how it was made.</p>',
    '<p class="pa-coll-how">Mixed media lets an artist build a surface in layers: paint over paper, handwritten text over gesture, resin poured over collage to seal it under a glassy skin. The medium line under each work names the artist’s materials, and the artwork page often explains the process in their own words.</p>',
    '<p class="pa-coll-how">Every work is shown with the artist’s own dimensions and asking price. When a piece appeals, enquire directly with the artist.</p>']) + _wall(
    "Available mixed-media and collage works") + _more([
        "<h2>Before you choose a mixed-media work.</h2>",
        _list([("Read the materials.", "They shape the care a work needs: resin and varnished surfaces are robust, while paper and collage elements need protection from damp and sun."),
               ("Check the support.", "Canvas, wooden panel or paper? Works on paper usually need a frame with glazing; panels may be cradled and ready to hang."),
               ("Look at depth and edges.", "Layered surfaces and deep panels cast shadows. Decide whether the work hangs as it is or in a frame."),
               ("Think about the light.", "Texture changes with the direction of light. A side light brings a layered surface to life; direct sun fades paper and pigment."),
               ("Keep it dust-free.", "Clean only with a soft, dry brush, and ask the artist about anything else.")])],
    [("../abstract-contemporary-art-ireland.html", "Abstract &amp; contemporary art"), ("../original-prints-ireland/", "Original prints"), ("../oil-paintings-ireland/", "Oil paintings")])

OFFICE_BODY = _hero("Art for offices", "Art for offices and workspaces.", [
    '<p class="pa-lede">Original paintings and mixed-media works for receptions, meeting rooms, corridors and shared workspaces, bought directly from artists based or working in Ireland. This selection shows the available works of 80 cm or more on the longest side, largest first: sizes that hold a wall seen from across a room.</p>',
    '<p class="pa-coll-how">Buying for a workplace is mostly about scale, light and the people who pass the work every day. A reception wall is seen from a distance and in passing; a meeting-room wall is seen for an hour at a time, from a chair. Every work is shown with the artist’s own dimensions and asking price, and the artist is the seller: enquire directly about the work you have in mind.</p>',
    '<p class="pa-coll-how">%s See <a href="../art-for-hire/">where Art for Hire stands</a>.</p>' % HIRE_LINE]) + _wall(
    "Available original artworks of 80 cm or more") + _more([
        "<h2>Choosing art for a workplace.</h2>",
        _list([("Measure the wall and the viewing distance.", 'A common guide is a work about two-thirds the width of the furniture or clear wall it hangs above. The <a href="../art-size-calculator.html">art size calculator</a> checks a size in seconds.'),
               ("Check the route in.", "Measure doors, lifts and stairs, especially for a large canvas or panel that cannot be rolled."),
               ("Plan the hanging.", 'Ask the artist about weight and fixings, and check the wall. Independent handlers and installers are listed on <a href="../services.html">art services and providers</a>; PlotArt itself does not deliver or install artwork.'),
               ("Mind the environment.", "Keep works out of direct sun and away from heaters, kitchens and air vents, and ask the artist how the work should be cared for."),
               ("Agree the paperwork.", "Ask for an invoice in the business’s name, and confirm any VAT, delivery and installation in writing before you pay.")])],
    [("../large-artworks/", "Large artworks"), ("../art-for-hire/", "Art for Hire"), ("../buy-original-art-ireland.html", "Buying art &amp; prices")])

SMALL_BODY = _hero("Small artworks", "Small original artworks.", [
    '<p class="pa-lede">Original paintings, prints and mixed-media works of 60 cm or less on the longest side, by artists based or working in Ireland. Small works suit a hallway, a stairwell, a shelf, a bedside wall or a group of pictures hung together, and they are often the easiest way to begin living with original art.</p>',
    '<p class="pa-coll-how">The smallest come first. Every work is shown whole, with the artist’s own dimensions and asking price. A frame or mount can add several centimetres, so ask the artist whether the stated size includes one.</p>']) + _wall(
    "Available original artworks of 60 cm or less") + _more([
        "<h2>Why choose a small work.</h2>",
        "<p>A small painting or print draws you in close. It can be moved from room to room as your home changes, it is simple to frame, and several small works by different artists can grow into a wall of their own over time.</p>",
        "<h2>Hanging small works well.</h2>",
        _list([("Hang at eye level.", "Galleries often centre a work about 145 to 150 cm from the floor. Above a sideboard or desk, leave a hand’s width between furniture and frame."),
               ("Group them.", "For a gallery wall, lay the works out on the floor first and keep the gaps between them even. One stronger piece can anchor the group."),
               ("Hallways and stairs.", "Narrow walls suit upright works; on a stair, follow the line of the steps rather than a level row."),
               ("Shelves and ledges.", "A small framed work can lean on a shelf, layered in front of books or objects. Make sure it is stable."),
               ("Protect works on paper.", "Frame them behind glazing and keep them out of direct sun.")])],
    [("../art-size-calculator.html", "Art size calculator"), ("../choose-art-for-living-room.html", "Choosing art for your living room"), ("../art-gifts-ireland/", "Original art as a gift")])

COLLECTING_BODY = _hero("Starting a collection", "How to start an art collection in Ireland.", [
    '<p class="pa-lede">A collection begins with one work you want to live with, then another. This guide covers the practical side: setting a budget, finding artists, choosing between prints and paintings, and caring for and recording what you buy. It does not treat art as an investment. Buy what you respond to.</p>'],
    '<a class="pa-btn pa-btn--ghost" href="#collH">See where to start →</a><a class="pa-btn pa-btn--ghost" href="../artworks/">Browse All Artworks →</a>') + '''
<section class="pa-coll-more"><div class="pa-wrap">
<h2>Set a budget, and a pace.</h2>
<p>Decide what you are comfortable spending on a single work and over a year. Original prints and small works on paper are a common way in; larger paintings can follow. The selection below shows where each artist’s available work starts.</p>
<h2>Get to know the artists.</h2>
<p>Read each artist’s statement and biography in their gallery, look at the rest of their work, and follow how it develops. Many collections are built around a handful of artists followed over years. Ask questions: artists are usually glad to talk about how a work was made and what it means to them.</p>
<h2>Prints or paintings?</h2>
<p>An original print, made by the artist through a printmaking process, is an original work; it may be one of a small edition. A painting or mixed-media work exists once. Both belong in a collection. Read more about <a href="../original-prints-ireland/">original prints and editions</a>.</p>
<h2>Buy for the wall, not for a return.</h2>
<p>PlotArt makes no claim about what any work may be worth in future. Choose work you want to see every day, at a price you are comfortable with, and judge it by how it holds your attention over time.</p>
<h2>Care and records.</h2>
<p>Keep a simple record of each work: title, artist, medium, dimensions, year, price, date of purchase and the invoice. Photograph the front and the back. Hang works away from direct sun and damp, and keep any care advice from the artist. If you insure your home contents, ask your insurer how artworks should be listed.</p>
</div></section>''' + _wall("A starting point: one work from each artist", "Where to start: one work from each artist.") + _more([
        "<h2>Take the next step.</h2>",
        '<p>When a work stays with you, enquire directly with the artist: they are the seller, and they confirm availability, the total price and how the work reaches you. The <a href="../buy-original-art-ireland.html">buying guide</a> lists what to ask.</p>'],
    [("../buy-original-art-ireland.html", "Buying art &amp; prices"), ("../original-art-under-1000/", "Original art for a first significant purchase"), ("../gallery/", "Meet the artists")])

GIFTS_BODY = _hero("Art as a gift", "Original art as a gift.", [
    '<p class="pa-lede">An original artwork is a personal gift: made by hand, chosen for one person and kept for years. This guide covers how to choose art for someone else, at Christmas or at any time of year, and shows small, publicly priced works by artists based or working in Ireland, one from each artist.</p>'],
    '<a class="pa-btn pa-btn--ghost" href="#collH">See gift-sized works →</a><a class="pa-btn pa-btn--ghost" href="../small-artworks/">Small original artworks →</a>') + '''
<section class="pa-coll-more"><div class="pa-wrap">
<h2>Choosing for someone else.</h2>
<ul class="pa-coll-list">
<li><strong>Think about where it will go.</strong> A small work fits almost any home: a hallway, a desk, a bedside wall or a shelf. Ask, if you can, about a wall they want to fill.</li>
<li><strong>Follow their taste, not yours.</strong> Notice the colours in their home and the art they already have. Bright geometric abstraction, layered coastal works and quiet works on paper suit very different people.</li>
<li><strong>Set the budget first.</strong> Every price shown is the artist’s own published asking price; ask what it includes.</li>
</ul>
<h2>Christmas and other dates.</h2>
<p>Each work is sold by the artist, who arranges collection or delivery directly with you. PlotArt makes no delivery promise. If you need a work by a particular date, such as Christmas, ask the artist before you buy and confirm the arrangement in writing. Allow time for framing if the work needs it.</p>
<h2>All year round.</h2>
<p>Original art marks an occasion that matters: a birthday, a wedding or anniversary, a new home, a retirement or a thank-you. A work by an artist the person already admires, or one connected to a place they love, carries its own story.</p>
<h2>Practical points.</h2>
<ul class="pa-coll-list">
<li><strong>Ready to hang?</strong> Ask whether the work is framed, and how it is packed.</li>
<li><strong>Pass on the story.</strong> Keep the invoice and the artist’s description of the work to give with it.</li>
<li><strong>Something made for them?</strong> Some PlotArt artists welcome <a href="../commissions/">commissions</a>; allow plenty of time.</li>
</ul>
</div></section>''' + _wall("Gift-sized original works, one from each artist", "Gift-sized original works.") + _more([
        "<h2>When a work appeals.</h2>",
        "<p>Enquire directly with the artist. Tell them it is a gift: they confirm availability, the total price, packing and how the work reaches you.</p>"],
    [("../original-art-under-500/", "Original art for smaller budgets"), ("../small-artworks/", "Small original artworks"), ("../buy-original-art-ireland.html", "Buying art &amp; prices")])

FIGURATIVE_BODY = _hero("Figurative art", "Figurative and portrait art.", [
    '<p class="pa-lede">Contemporary figurative painting and mixed media by artists based or working in Ireland: figures, faces and heads that sit between the recognisable and the abstract. Some works hold a single figure or a face in profile; others set two or three figures in a charged, invented space.</p>',
    '<p class="pa-coll-how">This is a curated selection. PlotArt chooses each work from the artist’s own description and image text: a work is here when the artist presents figures, faces or people in it. The page changes as works are sold or published.BEING_NOTE</p>']) + _wall(
    "Available figurative works") + _more([
        "<h2>Looking at figurative work.</h2>",
        "<p>Contemporary figurative art rarely aims at a likeness. Gestural marks, fragments of handwritten text and strong colour carry mood and psychology; a figure may stand for a feeling, a relationship or an idea. Read the artist’s description on each artwork page: several works here come with the artist’s own account of what the figures stand for.</p>",
        "<h2>A figure or face of your own?</h2>",
        '<p>The works here are not commissioned portraits. If you have a particular person, figure or subject in mind, the <a href="../commissions/">commissions page</a> shows the artists who welcome commissions, and how to approach one.</p>',
        "<h2>Before you choose.</h2>",
        _list([("Measure the wall.", "Faces and figures hold attention: think about where the work will be seen from, and how often."),
               ("Ask about framing.", "Works on paper need glazing; canvases and panels may hang as they are."),
               ("Get it in writing.", "Confirm the work, the total price and the arrangements with the artist before you pay.")])],
    [("../commissions/", "Commissions"), ("../mixed-media-art-ireland/", "Mixed media &amp; collage"), ("../artworks/", "All artworks")])

COASTAL_BODY = _hero("Coastal art", "Coastal and seascape art.", [
    '<p class="pa-lede">Coastal works by artists based or working in Ireland, layered in paint, print, ink, pen and pencil. Each is shown whole, with the artist’s own dimensions and asking price.</p>',
    '<p class="pa-coll-how">This is a small, curated collection, and it is growing. PlotArt chooses each work from its title, the artist’s own description and image text, and adds coastal and seascape work as artists publish it. For more work about place, see <a href="../landscape-paintings-ireland/">landscape paintings</a>.SPACES_NOTE</p>']) + _wall(
    "Available coastal works") + _more([
        "<h2>Coast, light and layers.</h2>",
        "<p>Coastal art need not be a literal seascape. Layered paint, printed texture and drawn line can hold the feel of a shoreline: weather, tide lines, rock and light moving on water, more than a view of one particular beach. Small coastal works on paper reward a close look, and several from one series read like a walk along the same stretch of coast.</p>",
        "<h2>Choosing a coastal work.</h2>",
        _list([("Hang a series together.", "Works from one series sit well side by side, in a row or a grid. Ask the artist about choosing more than one."),
               ("Ask about framing.", "Many coastal works are made on heavy paper or board. Ask whether a work is framed and glazed, and whether the size given includes the frame."),
               ("Keep it from the sun.", "Works on paper are sensitive to light: hang them away from direct sun and damp, in a hallway, a bedroom or a study."),
               ("Measure the wall.", 'Small works can look lost on a wide wall; the <a href="../art-size-calculator.html">art size calculator</a> helps you judge a group.')])],
    [("../landscape-paintings-ireland/", "Landscape paintings"), ("../small-artworks/", "Small original artworks"), ("../mixed-media-art-ireland/", "Mixed media &amp; collage")])


def being_note():
    """Being is PlotArt's curated gallery for figurative work. While it is in preparation the page says so and links
    nothing; it links to Being only once the founder's switch opens it (as spaces_note)."""
    if SEO.switches().get("being_gallery_state") == "open":
        return ' For a curated gallery of figurative work, visit <a href="../being/">Being</a>.'
    return " PlotArt’s Being gallery, a curated home for figurative work, is in preparation."


PAGES.update({"original-art-under-1000/index.html": (None, None, U1000_BODY),
              "original-prints-ireland/index.html": (None, None, PRINTS_BODY),
              "oil-paintings-ireland/index.html": (None, None, OIL_BODY),
              "mixed-media-art-ireland/index.html": (None, None, MIXED_BODY),
              "art-for-offices/index.html": (None, None, OFFICE_BODY),
              "small-artworks/index.html": (None, None, SMALL_BODY),
              "collecting-art-ireland/index.html": (None, None, COLLECTING_BODY),
              "art-gifts-ireland/index.html": (None, None, GIFTS_BODY),
              "figurative-art-ireland/index.html": (None, None, FIGURATIVE_BODY),
              "coastal-art-ireland/index.html": (None, None, COASTAL_BODY)})


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
    body = body_copy.replace("SPACES_NOTE", spaces_note()).replace("BEING_NOTE", being_note()).replace("COLLECTION", C.BEGIN + "\n" + C.content(path, packages) + "\n" + C.END)
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
