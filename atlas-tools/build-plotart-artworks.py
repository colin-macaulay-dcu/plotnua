#!/usr/bin/env python3
"""Build/check the PlotArt artwork collection, plotart/artworks/ (SEO buyer-intent Phase 1, 13 Nov 2026).

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
<p class="pa-coll-how">PlotArt introduces you to the artist. It doesn’t take payment or deliver artwork: the artist arranges any sale with you directly.</p>
<div class="pa-coll-actions"><a class="pa-btn pa-btn--ghost" href="../gallery/">Meet the artists →</a><a class="pa-btn pa-btn--ghost" href="../buy-original-art-ireland.html">Buying art &amp; prices →</a></div>
</div></section>
<section class="pa-coll-wall" aria-labelledby="collH"><div class="pa-wrap">
<h2 id="collH" class="pa-sr">Available original artworks</h2>
COLLECTION
</div></section>
<section class="pa-coll-more"><div class="pa-wrap">
<h2>Before you choose.</h2>
<p>Measure the wall you have in mind, read the medium and dimensions, and ask the artist about framing, delivery and the total price. Each artist’s gallery tells you more about their practice and the rest of their work.</p>
<div class="pa-coll-links"><a class="pa-btn pa-btn--ghost" href="../art-size-calculator.html">What size art fits your wall? →</a><a class="pa-btn pa-btn--ghost" href="../choose-art-for-living-room.html">Choosing art for your living room →</a><a class="pa-btn pa-btn--ghost" href="../abstract-contemporary-art-ireland.html">Abstract &amp; contemporary art →</a></div>
</div></section>
'''


def relink(fragment):
    """The shell is taken from plotart/index.html, whose links are relative to plotart/. This page sits one folder
    deeper (plotart/artworks/), so every relative href/src gains '../'. Absolute, root, mailto and fragment links stay."""
    return re.sub(r'(href|src|srcset)="(?!https?:|mailto:|tel:|#|/|data:)([^"]*)"', lambda m: '%s="../%s"' % (m.group(1), m.group(2)), fragment)


def render(packages):
    home = (ROOT / "plotart/index.html").read_text()
    header = re.search(r'<header class="pa-head.*?</header>', home, re.S).group(0).replace(' aria-current="page"', "")
    footer = re.search(r'<footer class="pa-foot">.*?</footer>', home, re.S).group(0)
    head = home.split("<head>", 1)[1].split("</head>", 1)[0]
    head = re.sub(r"<title>.*?</title>", "<title>" + html.escape(TITLE) + "</title>", head)
    for kind, key, value in [("name", "description", DESCRIPTION), ("property", "og:title", TITLE), ("property", "og:description", DESCRIPTION),
                             ("name", "twitter:title", TITLE), ("name", "twitter:description", DESCRIPTION), ("property", "og:url", SEO.canonical(PATH))]:
        head = re.sub(r'<meta ' + kind + '="' + key + '" content="[^"]*">', '<meta ' + kind + '="' + key + '" content="' + html.escape(value, quote=True) + '">', head)
    head = re.sub(r'<link rel="canonical" href="[^"]+">', '<link rel="canonical" href="' + SEO.canonical(PATH) + '">', head)
    if not SEO.indexable(PATH, SEO.switches()):
        head = head.replace('<meta name="robots" content="index, follow">', '<meta name="robots" content="noindex, follow">')
        head = re.sub(r'<link rel="canonical" href="[^"]+">\n?', "", head)
    # the homepage's own structured data describes the homepage; this page's data lives in its collection region
    head = re.sub(r'\s*<script type="application/ld\+json">.*?</script>', "", head, flags=re.S)
    head = relink(head) + '<link rel="stylesheet" href="../' + CSS_PATH + '">\n'
    body = BODY.replace("COLLECTION", C.BEGIN + "\n" + C.content(PATH, packages) + "\n" + C.END)
    return ('<!DOCTYPE html>\n<html lang="en-IE" class="no-js">\n<head>' + head + '</head>\n<body class="pa">\n'
            '<a class="pa-skip" href="#main">Skip to content</a>\n' + relink(header) + '\n<main id="main" class="pa-coll">' + body + '</main>\n'
            + relink(footer) + '\n<script src="../assets/plotart.js" defer></script>\n<script src="/assets/identity/pn-menu.js?v=1" defer></script>\n</body>\n</html>\n')


def main():
    expected = {ROOT / "plotart" / PATH: render(SEO.public_packages(ROOT)), ROOT / "plotart" / CSS_PATH: CSS}
    if "--check" in sys.argv:
        bad = [str(p.relative_to(ROOT)) for p, t in expected.items() if not p.exists() or p.read_text() != t]
        if bad:
            raise SystemExit("ARTWORK COLLECTION · differs from reviewed source: " + ", ".join(bad))
        print("ARTWORK COLLECTION · OK — page and styles match reviewed copy and the public collection; nothing written")
        return
    for p, t in expected.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(t)
    print("ARTWORK COLLECTION · built plotart/%s and plotart/%s" % (PATH, CSS_PATH))


if __name__ == "__main__":
    main()
