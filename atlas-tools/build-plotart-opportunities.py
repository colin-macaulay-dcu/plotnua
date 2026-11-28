#!/usr/bin/env python3
"""Build/check the PlotArt artist opportunities page (plotart/opportunities/index.html, 16 Nov 2026) and the Commissions
page (plotart/commissions/index.html, 17 Nov 2026).

One page for all seven opportunities an artist can choose in PlotArt Studio, each with the published artists who chose to
show it (plotart_opportunities). It is reached from artists' galleries and the Living Gallery, Art for Hire and Mobile
Gallery lists; it is NOT in the main navigation, and it stays noindex until the SEO workstream decides (plotart_seo).
The page shell is the PlotArt homepage's own header and footer (as the buyer guides), with no navigation pill current.

    python3 atlas-tools/build-plotart-opportunities.py [--check]
"""
import html
import re
import sys
from pathlib import Path

import plotart_opportunities as OPP
import plotart_featured as FEAT
import plotart_seo as SEO
import plotart_shell as S  # the approved analytics head (26 Nov 2026)

ROOT = Path(__file__).resolve().parent.parent
PATH = OPP.HUB
TITLE = "Artist Opportunities | PlotArt"
DESC = ("Irish artists open to exhibitions, Art Hosting with the Living Gallery, Art for Hire, home viewings, business and venue hosting, "
        "commissions and talks. Every opportunity is agreed individually with the artist.")
E = lambda s: html.escape(str(s), quote=True)

BODY = """
<div class="pa-opp-hub">
<section class="pa-opp-hero"><div class="pa-wrap">
<h1>Work with our artists.</h1>
<p class="pa-lede">PlotArt artists tell us which opportunities they’d welcome a conversation about. Each list below links to their galleries. Being listed shows interest, not a booking: every opportunity is discussed and agreed individually with the artist.</p>
<ul class="pa-opp-jumps" aria-label="Opportunities">%(jumps)s</ul>
</div></section>
%(region)s
<section class="pa-opp-contact"><div class="pa-wrap">
<p>To talk to an artist about an opportunity, open their gallery and send an enquiry through PlotArt. For anything else, email <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a>.</p>
</div></section>
</div>
"""


COM_TITLE = "Commission Original Art from Irish Artists | PlotArt"
COM_DESC = ("Commission an original artwork from an artist based or working in Ireland. Enquire through the artist’s PlotArt gallery; "
            "the artist agrees the price, timescale and details with you.")


def com_jsonld():
    """Static structured data for the Commissions page (indexable, 17 Nov 2026): the page, its place in PlotArt and its
    breadcrumb. The artist list is NOT repeated here: it changes with publication and lives only in the generated region."""
    import json as _json
    url = SEO.canonical(OPP.COMMISSIONS)
    data = {"@context": "https://schema.org", "@type": "WebPage", "name": "Commission an original work", "description": COM_DESC, "url": url,
            "inLanguage": "en-IE", "isPartOf": {"@type": "WebSite", "name": "PlotArt", "url": SEO.canonical("index.html")},
            "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "PlotArt", "item": SEO.canonical("index.html")},
                {"@type": "ListItem", "position": 2, "name": "Commissions", "item": url}]}}
    return '<script type="application/ld+json">%s</script>' % _json.dumps(data, ensure_ascii=False, separators=(",", ":"))
COM_BODY = """
<div class="pa-com-page">
<section class="pa-opp-hero pa-com-hero"><div class="pa-wrap">
<p class="pa-eyebrow">PlotArt · Commissions</p>
<h1>Commission an original work.</h1>
<p class="pa-lede">Some PlotArt artists welcome enquiries about new work made for you: a painting for a particular wall, a piece for a home or a workplace, or a gift. Choose an artist below and send an enquiry through their gallery.</p>
<p class="pa-com-intro">The artists listed on this page, all based or working in Ireland, have said they welcome commission enquiries through PlotArt. Each decides for themselves which commissions to take on, and agrees the details directly with you.</p>
<ul class="pa-opp-jumps" aria-label="On this page"><li><a href="#open-artists">Artists open to commissions</a></li><li><a href="#com-agree">What to agree</a></li><li><a href="#com-size">Choosing the size</a></li><li><a href="#com-price">Price guidance</a></li></ul>
</div></section>
<section class="pa-com-how" aria-labelledby="com-how-h"><div class="pa-wrap pa-com-how-in">
<h2 id="com-how-h">How a commission works</h2>
<ol class="pa-steps">
<li><div><h3>Choose an artist</h3><p>Look through the galleries of the artists listed below and find work that speaks to you. You can also <a href="../artworks/" data-pa-track="commissions_artworks">see available original works</a> by every PlotArt artist.</p></div></li>
<li><div><h3>Send an enquiry through PlotArt</h3><p>On the artist’s gallery, use “Enquire about a commission”, or “Enquire through PlotArt”. PlotArt passes your name, email address and message to the artist, who replies to you directly.</p></div></li>
<li><div><h3>Talk through the brief</h3><p>Tell the artist what you have in mind: the room or wall, the size, the colours or mood, your budget and any date that matters. Point to the works in their gallery that drew you to them; most artists find that more useful than a detailed instruction.</p></div></li>
<li><div><h3>Agree it with the artist</h3><p>The artist decides whether to take the commission on. The size, subject, price, timescale, payment and delivery are agreed between you and the artist. PlotArt doesn’t take payment.</p></div></li>
</ol>
</div></section>
%(region)s
<section class="pa-com-guide" id="com-agree" aria-labelledby="com-agree-h"><div class="pa-wrap pa-com-guide-in">
<div><h2 id="com-agree-h">What to agree before work begins</h2>
<p>Every artist works differently, and PlotArt doesn’t set commission terms. These are the questions people typically settle with the artist, ideally in writing, before any work starts.</p></div>
<ul>
<li><strong>The brief.</strong> What the work is about, and how much freedom the artist has. Will you see sketches, colour studies or a photograph of the work in progress, and at what stage?</li>
<li><strong>Size and medium.</strong> The finished dimensions in centimetres, whether they include a frame or mount, and the medium: a painting, a work on paper, a print or mixed media.</li>
<li><strong>Budget.</strong> The total price, and what it covers: framing, any VAT that applies, packing, collection or delivery, and hanging.</li>
<li><strong>Timeline.</strong> When the artist can begin, roughly how long the work will take, and whether there is a date you need it by. Artists’ schedules vary, so ask early if timing matters.</li>
<li><strong>Deposit and payment.</strong> Whether the artist asks for a deposit, when the balance is due, and what happens to the deposit if either of you decides not to go ahead.</li>
<li><strong>Changes.</strong> How much feedback is part of the process, and what happens if you would like changes once the work is finished.</li>
<li><strong>Images and rights.</strong> Copyright usually stays with the artist unless you agree otherwise. Ask whether the artist would like to photograph the finished work, and how you may share images of it.</li>
</ul>
</div></section>
<section class="pa-com-guide" id="com-size" aria-labelledby="com-size-h"><div class="pa-wrap pa-com-guide-in">
<h2 id="com-size-h">Choosing the size</h2>
<div><p>Size is often the reason to commission: a wall, alcove or stairwell where nothing already available is quite right. Measure the space, note the distance from which the work will usually be seen, and look at the light at different times of day.</p>
<p>The free <a href="../art-size-calculator.html" data-pa-track="commissions_size_calculator">art size calculator</a> suggests a size in centimetres for a wall or a piece of furniture, which gives you and the artist a shared starting point. For a large space, look at the <a href="../large-artworks/" data-pa-track="commissions_large">large artworks of 100 cm or more</a> already available: an artist’s existing large work shows how they handle scale.</p>
<p>Large works can take longer to make and to dry, and are harder to move. Talk to the artist early about access, hanging and how the finished work will reach you.</p></div>
</div></section>
<section class="pa-com-guide" id="com-price" aria-labelledby="com-price-h"><div class="pa-wrap pa-com-guide-in">
<h2 id="com-price-h">Price guidance</h2>
<div><p>Commission prices are set by each artist and depend on size, medium, complexity and time. PlotArt doesn’t publish commission prices.</p>
<p>As a guide, the list above shows each artist’s current asking prices: the lowest and highest price of their works available on PlotArt right now, taken from their published gallery and updated whenever they publish or sell work. It is an indication of how the artist prices finished work, not a quote. A commission may cost more or less, so ask the artist for a price based on your brief.</p>
<p>For how artwork prices work more generally, and what to ask before you pay, read <a href="../buy-original-art-ireland.html" data-pa-track="commissions_buying_guide">Buying original art in Ireland</a>. If you would rather choose a finished piece, see <a href="../choose-art-for-living-room.html">choosing art for your living room</a> or browse <a href="../artworks/">all available artworks</a>.</p></div>
</div></section>
<section class="pa-opp-contact pa-com-control"><div class="pa-wrap">
<p>Artists stay in control of their commissions: each artist chooses whether to be listed here, whether to accept a commission, and their own prices, timescales and arrangements. An enquiry isn’t a booking, and nothing is agreed until you and the artist agree it.</p>
<p>Other ways to work with our artists are on <a href="../opportunities/">Artist opportunities</a>. For anything else, email <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a>.</p>
</div></section>
</div>
"""
PAGES = {OPP.HUB: (TITLE, DESC, lambda region: BODY % {"jumps": "".join('<li><a href="#%s">%s</a></li>' % (OPP.OPPORTUNITIES[k][4], E(OPP.OPPORTUNITIES[k][0])) for k in OPP.KEYS), "region": region}),
         OPP.COMMISSIONS: (COM_TITLE, COM_DESC, lambda region: COM_BODY % {"region": region})}


def render(packages, path=PATH):
    title, desc, body = PAGES[path]
    if path == OPP.COMMISSIONS:   # SEO and analytics package (26 Nov 2026): the number of artists comes from the galleries
        title, desc = OPP.commissions_meta(packages)
    home = (ROOT / "plotart/index.html").read_text(encoding="utf-8")
    header = re.search(r'<header class="pa-head.*?</header>', home, re.S).group(0).replace(' aria-current="page"', "")
    footer = re.search(r'<footer class="pa-foot">.*?</footer>', home, re.S).group(0)
    # one level down: every relative link in the shared header and footer gains ../
    fix = lambda s: re.sub(r'(href|src|srcset)="(?!https?:|/|#|mailto:)([^"]+)"', lambda m: '%s="../%s"' % (m.group(1), m.group(2)), s)
    header, footer = fix(header), fix(footer)
    inner = OPP.content(path, packages, FEAT.choices(ROOT))
    region = OPP.BEGIN + ("\n" + inner + "\n" if inner else "") + OPP.END
    robots = SEO.head(path, title, desc) + ("\n" + com_jsonld() if path == OPP.COMMISSIONS else "")
    return """<!DOCTYPE html>
<html lang="en-IE" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
%s<title>%s</title>
<meta name="description" content="%s">
%s
<meta name="theme-color" content="#27282A">
<link rel="icon" href="/assets/brand/plotart-favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/brand/plotart-apple-touch-180.png">
<link rel="preload" href="/plotart/assets/fonts/hanken-grotesk-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/plotart/assets/fonts/instrument-serif-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/plotart/assets/fonts/plotart-fonts.css?v=1">
<link rel="stylesheet" href="../assets/plotart.css">
<link rel="stylesheet" href="../assets/plotart-opportunities.css">
<link rel="stylesheet" href="/assets/identity/pn-section-menu.css?v=1">
<script>document.documentElement.classList.remove('no-js');</script>
</head>
<body class="pa">
<a class="pa-skip" href="#main">Skip to content</a>
%s
<main id="main">%s</main>
%s
<script src="../assets/plotart.js" defer></script>
<script src="/assets/identity/pn-menu.js?v=1" defer></script>
</body>
</html>
""" % (S.ANALYTICS_HEAD, E(title), E(desc), robots, header, body(region), footer)


def main():
    packages = SEO.public_packages(ROOT)
    for path in PAGES:
        page = ROOT / "plotart" / path
        want = render(packages, path)
        if "--check" in sys.argv:
            if not page.exists():
                raise SystemExit("ARTIST OPPORTUNITIES · plotart/%s is missing" % path)
            got = page.read_text(encoding="utf-8")
            if OPP.outside(got) != OPP.outside(want):
                raise SystemExit("ARTIST OPPORTUNITIES · plotart/%s differs from its reviewed source outside the generated lists" % path)
            if got != OPP.update(got, path, packages, FEAT.choices(ROOT)):
                raise SystemExit("ARTIST OPPORTUNITIES · the lists on plotart/%s differ from what the published galleries produce" % path)
            continue
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(want, encoding="utf-8")
        print("ARTIST OPPORTUNITIES · built plotart/%s" % path)
    if "--check" in sys.argv:
        print("ARTIST OPPORTUNITIES · OK — pages match their source; lists match the published galleries; nothing written")


if __name__ == "__main__":
    main()
