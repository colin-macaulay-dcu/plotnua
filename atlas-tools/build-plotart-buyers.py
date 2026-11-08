#!/usr/bin/env python3
"""Build/check the two PlotArt buyer pages from reviewed copy and approved public exports."""
import html
import re
import sys
from pathlib import Path

import plotart_seo as SEO
import plotart_search_content as C

ROOT = Path(__file__).resolve().parent.parent
CSS = '''/* PlotArt buyer pages: editorial reading and uncropped original work. */
.pa-guide-hero{padding:76px 0 60px;border-bottom:1px solid var(--line,rgba(242,235,224,.14))}
.pa-guide-hero h1{font-family:var(--serif);font-weight:400;font-size:clamp(44px,6vw,82px);line-height:1.03;letter-spacing:-.025em;margin:16px 0 26px;max-width:920px}
.pa-guide-hero .pa-lede{max-width:780px}.pa-guide-actions{display:flex;gap:14px;flex-wrap:wrap;margin-top:28px}
.pa-guide-jumps{display:flex;flex-wrap:wrap;gap:12px 26px;padding:28px 0;border-bottom:1px solid rgba(242,235,224,.14);font-size:14px}
.pa-guide-section{padding:58px 0;border-bottom:1px solid rgba(242,235,224,.12)}
.pa-guide-reading{max-width:820px}.pa-guide-section h2{font-family:var(--serif);font-size:clamp(30px,3.5vw,44px);font-weight:400;line-height:1.15;margin:0 0 24px}
.pa-guide-section h3{font-size:19px;line-height:1.35;margin:28px 0 10px}.pa-guide-section p,.pa-guide-section li{line-height:1.8}
.pa-guide-section p{margin:0 0 18px}.pa-guide-section ul,.pa-guide-section ol{padding-left:24px}.pa-guide-section li+li{margin-top:12px}
.pa-guide-note{font-size:14px;opacity:.8}.pa-guide-callout{padding:26px;border-left:2px solid #cf8566;background:rgba(242,235,224,.035);margin:28px 0}
.pa-guide-callout p:last-child{margin-bottom:0}.pa-guide-table{overflow-x:auto;margin:28px 0;max-width:100%}.pa-guide-table:focus-visible{outline:2px solid #cf8566;outline-offset:4px}
.pa-guide-table table{width:100%;border-collapse:collapse;text-align:left;min-width:520px}.pa-guide-table caption{text-align:left;font-size:14px;margin-bottom:14px}
.pa-guide-table th,.pa-guide-table td{border-bottom:1px solid rgba(242,235,224,.15);padding:16px 14px;vertical-align:top}.pa-guide-table tbody th{font-weight:400}.pa-guide-table td:last-child{white-space:nowrap}
.pa-guide-works{list-style:none!important;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:40px 28px;padding:0!important;margin:34px 0}
.pa-guide-works li{margin:0!important;min-width:0}.pa-guide-art{display:flex;align-items:center;justify-content:center;min-height:320px;background:rgba(242,235,224,.025);padding:18px}
.pa-guide-art img{display:block;width:100%;height:360px;object-fit:contain;object-position:center}.pa-guide-works h3{font-family:var(--serif);font-size:27px;font-weight:400;margin:20px 0 10px}
.pa-guide-works p{font-size:14px;line-height:1.6;margin-bottom:8px}.pa-guide-related{display:flex;gap:14px;flex-wrap:wrap;padding:40px var(--gut) 60px}
@media(max-width:700px){.pa-guide-hero{padding:44px 0 38px}.pa-guide-section{padding:40px 0}.pa-guide-works{grid-template-columns:1fr;gap:38px}.pa-guide-art img{height:auto;max-height:520px}.pa-guide-art{min-height:0}.pa-guide-callout{padding:20px}.pa-guide-jumps{gap:12px 20px}.pa-guide-actions .pa-btn{max-width:100%;white-space:normal}}
'''

BUY = '''
<section class="pa-guide-hero"><div class="pa-wrap">
<p class="pa-eyebrow">PlotArt · A buyer’s guide</p>
<h1>Buying original art<br>in Ireland.</h1>
<p class="pa-lede">Find a work you want to live with. Understand what you’re buying, what the price includes and how to take the next step with the artist.</p>
<div class="pa-guide-actions"><a class="pa-btn pa-btn--solid" href="gallery/">Explore original Irish art →</a><a class="pa-btn pa-btn--ghost" href="#art-prices">See current artwork prices ↓</a></div>
<nav class="pa-guide-jumps" aria-label="In this guide"><a href="#where-to-buy">Where to buy</a><a href="#original-or-print">Originals and prints</a><a href="#art-prices">Art prices</a><a href="#choose-art">Choosing a work</a><a href="#how-to-buy">How to enquire</a></nav>
</div></section>
<section class="pa-guide-section" id="where-to-buy"><div class="pa-wrap pa-guide-reading">
<p class="pa-eyebrow">Start with the artist</p><h2>Where can you buy original Irish art?</h2>
<p>You can explore work through an artist’s own studio or website, a physical gallery, an exhibition or an online gallery. The useful starting point is a particular artist and a particular work: who made it, what it is, whether it is available and who will arrange the sale.</p>
<p>PlotArt brings individual artists’ galleries together online. You can read their biographies, see each artwork in full and check its stated medium, dimensions, asking price and availability. When a piece interests you, send an enquiry through PlotArt to the artist.</p>
<div class="pa-guide-callout"><h3>How buying through PlotArt works</h3><p>PlotArt introduces buyers to artists. It does not take payment or deliver artwork. The artist arranges any sale with you directly, including payment, collection or delivery. An enquiry is a way to ask questions; it is not a purchase or a reservation.</p></div>
<p>For names you already know, use <a href="gallery/">Artists A–Z in the Virtual Gallery</a>. If you are beginning with a style, explore <a href="abstract-contemporary-art-ireland.html">abstract and contemporary Irish art</a>.</p>
</div></section>
<section class="pa-guide-section" id="original-or-print"><div class="pa-wrap pa-guide-reading">
<h2>Original painting, original print or reproduction?</h2>
<p>Read the description rather than relying on the word “print” alone. An original print can be a work made through a printmaking process; a reproduction reproduces the image of another artwork. A monoprint may be a unique work, while an edition may contain a stated number of impressions. The artist’s description should explain the particular piece.</p>
<p>Ask what you will receive: a unique work, an editioned print or a reproduction; the materials and support; any edition number; and whether it is signed. If the description combines processes, such as printmaking with hand-applied paint, ask the artist to explain how that work was made.</p>
<p>These distinctions matter when comparing prices. Two pieces with similar colours and dimensions may be different kinds of object. For background on the terminology, see the <a href="https://www.nationalgalleries.org/art-and-artists/glossary-terms/monoprint-0">National Galleries of Scotland’s introduction to monoprints</a>.</p>
</div></section>
<section class="pa-guide-section" id="art-prices"><div class="pa-wrap">
<div class="pa-guide-reading"><p class="pa-eyebrow">The price of a particular work</p><h2>How much does original art cost in Ireland?</h2>
<p>There is no single price that describes original Irish art. Compare the asking price of the specific work with its medium, size, whether it is unique or editioned, the artist’s practice and what is included. A small reproduction and a large, unique work are different purchases.</p>
<p>On PlotArt, the artist supplies the asking price. “Price on request” means you need to ask the artist for that information. The list below shows available works and the prices currently published in their galleries.</p></div>
COLLECTION
<div class="pa-guide-reading"><h3>Compare the total cost</h3><ul><li><strong>Framing:</strong> is the work framed, and are the stated dimensions for the artwork or the frame?</li><li><strong>VAT:</strong> does the quoted total include any VAT that applies?</li><li><strong>Collection or delivery:</strong> who arranges it, where can the work be sent and what will it cost?</li><li><strong>Installation:</strong> does the work need particular fixings or professional installation, and who arranges that?</li></ul>
<p>Ask for the agreed work, price and arrangements in writing before paying. Choose a piece for its artistic and personal appeal.</p></div>
</div></section>
<section class="pa-guide-section" id="choose-art"><div class="pa-wrap pa-guide-reading">
<h2>Choosing a painting or artwork for your home</h2>
<p>Compare proportions before choosing a work with the free <a href="art-size-calculator.html">PlotArt art size calculator</a>. Enter the furniture or clear wall width and the outer artwork dimensions to see the relationship.</p>
<ol><li><strong>Begin with your response.</strong> Spend time with the image and the artist’s description. Look for something you want to return to, beyond a colour match.</li><li><strong>Measure the space.</strong> Check the artwork’s actual dimensions and any frame dimensions. Mark the outline on the wall with removable paper to help judge the scale.</li><li><strong>Read the medium and support.</strong> A work on paper, a canvas and a sculptural object can need different display arrangements. Ask the artist about care, light and hanging.</li><li><strong>Look closely.</strong> Ask for additional photographs or details if surface, texture, condition or colour is important to your decision. A screen cannot show every quality of a physical work.</li><li><strong>Confirm the details.</strong> Availability can change. Ask about the exact piece, the total price and whether an in-person viewing can be arranged.</li></ol>
</div></section>
<section class="pa-guide-section" id="how-to-buy"><div class="pa-wrap pa-guide-reading">
<h2>Ready to ask about a work?</h2><p>Open the artwork page and choose “Enquire about this work”. Give the title and ask about the details that matter to you. PlotArt passes the enquiry to the artist so they can reply directly.</p>
<div class="pa-guide-callout"><h3>A useful first enquiry</h3><p>Is this work still available? Could you confirm the total price, whether it is framed, the overall dimensions and the collection or delivery options? I would also like to know whether a viewing is possible.</p></div>
<p>Take the time you need to understand the work and the arrangements. Each artist’s gallery is a starting point for that conversation.</p>
</div></section>
'''

ABSTRACT = '''
<section class="pa-guide-hero"><div class="pa-wrap">
<p class="pa-eyebrow">PlotArt · Explore the work</p><h1>Abstract &amp; contemporary<br>Irish art.</h1>
<p class="pa-lede">Colour, shape, surface and gesture. Discover work that gives you something new to notice, and meet the artists behind it.</p>
<div class="pa-guide-actions"><a class="pa-btn pa-btn--solid" href="#available-work">Explore available work ↓</a><a class="pa-btn pa-btn--ghost" href="buy-original-art-ireland.html">Read the buying guide →</a></div>
<nav class="pa-guide-jumps" aria-label="On this page"><a href="#available-work">Available work</a><a href="#abstract-art">What is abstract art?</a><a href="#contemporary-art">What is contemporary art?</a><a href="#look-at-art">Looking and choosing</a></nav>
</div></section>
<section class="pa-guide-section" id="available-work"><div class="pa-wrap"><p class="pa-eyebrow">From the published collection</p><h2>A starting point for discovery.</h2>
COLLECTION
</div></section>
<section class="pa-guide-section" id="abstract-art"><div class="pa-wrap pa-guide-reading">
<h2>What is abstract art?</h2><p>Abstract art gives colour, shape, line, texture and relationships between forms a central role. It may move away from a recognisable subject or work without a depicted subject at all. You do not have to identify a scene or an object before responding to it.</p>
<p>For a starting definition, the <a href="https://imma.ie/what-is-art/glossary-of-art-terms/">Irish Museum of Modern Art’s glossary</a> describes abstract art through its emphasis on formal elements rather than depicting subject matter.</p>
<p>When exploring abstract paintings or works on paper, notice where your eye moves, how marks relate to each other and what changes when you look again. An artist’s title or statement can offer another way into the work, without having to settle its meaning for you.</p>
</div></section>
<section class="pa-guide-section" id="contemporary-art"><div class="pa-wrap pa-guide-reading">
<h2>What is contemporary Irish art?</h2><p>Contemporary art refers broadly to current and recent artistic practice. It is not one visual style: it can include painting, printmaking, drawing, sculpture, installation and other approaches. Contemporary work can be abstract or figurative.</p>
<p><a href="https://imma.ie/what-is-art/series-1-1970-now/modern-and-contemporary-art/">IMMA’s introduction to modern and contemporary art</a> explains why the terms overlap in everyday use but describe different ideas in art history.</p>
<p>On PlotArt, begin with an individual artist’s work and account of their practice. The gallery brings their biography, images, medium, dimensions, availability and enquiry route together.</p>
</div></section>
<section class="pa-guide-section" id="look-at-art"><div class="pa-wrap pa-guide-reading">
<h2>How to choose abstract art you want to live with</h2>
<h3>Look at the whole work, then its details</h3><p>Give the composition time before moving to the next image. Look for contrasts, repeated forms and shifts in colour or surface. Explore other works by the artist to see what connects them and what changes.</p>
<h3>Check the physical object</h3><p>“Abstract” describes an approach, rather than a material or a guarantee of uniqueness. Check whether a piece is a painting, an original print, a mixed-media work or a reproduction. Read the dimensions and ask about framing and display.</p>
<h3>Consider scale as well as colour</h3><p>A large work can change the balance of a space; a smaller work can invite a closer encounter. Measure the place you have in mind and consider the distance from which you will usually see it. Ask the artist for more information if you cannot judge the scale from the photographs.</p>
<h3>Make the enquiry specific</h3><p>Ask about the exact piece you like: its availability, total price, materials, framing and collection or delivery. Where a viewing is possible, the artist can explain how to arrange it. PlotArt passes enquiries to the artist and does not take payment.</p>
<p>For price comparisons, originals and editions, and practical questions before buying, read <a href="buy-original-art-ireland.html">Buying original art in Ireland</a>.</p>
</div></section>
'''

PAGES = {
    'buy-original-art-ireland.html': ('Buy Original Irish Art | Prices & Buying Guide | PlotArt',
        'Where to buy original Irish art, how artwork prices work and what to ask before buying. Explore live artist-supplied prices and enquire through PlotArt.', BUY),
    'abstract-contemporary-art-ireland.html': ('Abstract & Contemporary Irish Art | PlotArt',
        'Explore abstract and contemporary Irish art, discover available work and meet the artists. Read a practical introduction to choosing original artwork.', ABSTRACT),
}


def render(path, packages):
    title, desc, body = PAGES[path]
    home = (ROOT / 'plotart/index.html').read_text()
    header = re.search(r'<header class="pa-head.*?</header>', home, re.S).group(0)
    header = header.replace(' aria-current="page"', '')
    footer = re.search(r'<footer class="pa-foot">.*?</footer>', home, re.S).group(0)
    head = home.split('<head>', 1)[1].split('</head>', 1)[0]
    head = re.sub(r'<title>.*?</title>', '<title>'+html.escape(title)+'</title>', head)
    for kind, key, value in [('name','description',desc),('property','og:title',title),('property','og:description',desc),('name','twitter:title',title),('name','twitter:description',desc),('property','og:url',SEO.canonical(path))]:
        head = re.sub(r'<meta '+kind+'="'+key+'" content="[^"]*">', '<meta '+kind+'="'+key+'" content="'+html.escape(value,quote=True)+'">', head)
    head = re.sub(r'<link rel="canonical" href="[^"]+">', '<link rel="canonical" href="'+SEO.canonical(path)+'">', head)
    if not SEO.indexable(path, SEO.switches()):
        head = head.replace('<meta name="robots" content="index, follow">', '<meta name="robots" content="noindex, follow">')
        head = re.sub(r'<link rel="canonical" href="[^"]+">\n?', '', head)
    head += '<link rel="stylesheet" href="assets/plotart-guides.css">\n'
    body = body.replace('COLLECTION', C.BEGIN+'\n'+C.content(path,packages)+'\n'+C.END)
    related = '<div class="pa-wrap pa-guide-related"><a class="pa-btn pa-btn--ghost" href="gallery/">Artist galleries →</a><a class="pa-btn pa-btn--ghost" href="'+('abstract-contemporary-art-ireland.html' if path.startswith('buy-') else 'buy-original-art-ireland.html')+'">'+('Abstract &amp; contemporary art →' if path.startswith('buy-') else 'Buying art &amp; prices →')+'</a></div>'
    return '<!DOCTYPE html>\n<html lang="en-IE" class="no-js">\n<head>'+head+'</head>\n<body class="pa">\n<a class="pa-skip" href="#main">Skip to content</a>\n'+header+'\n<main id="main" class="pa-guide">'+body+related+'</main>\n'+footer+'\n<script src="assets/plotart.js" defer></script>\n<script src="/assets/identity/pn-menu.js?v=1" defer></script>\n</body>\n</html>\n'


def main():
    packages=SEO.public_packages(ROOT)
    expected={ROOT/'plotart'/p:render(p,packages) for p in PAGES}
    expected[ROOT/'plotart/assets/plotart-guides.css']=CSS
    if '--check' in sys.argv:
        bad=[str(p.relative_to(ROOT)) for p,t in expected.items() if not p.exists() or p.read_text()!=t]
        if bad:raise SystemExit('BUYER GUIDES · differ from reviewed source: '+', '.join(bad))
        print('BUYER GUIDES · OK — two pages and styles match reviewed copy and public collection; nothing written')
    else:
        for p,t in expected.items():p.write_text(t)
        print('BUYER GUIDES · built two pages and styles')

if __name__=='__main__':main()
