"""PlotArt page shell for artist gallery pages (Phase 3, 29 Oct 2026).

The production content pipeline (atlas-tools/plotart-gallery-publish.py, on main) renders artist gallery pages
WITHOUT the full PlotArt builder. This module reproduces exactly the launch page shell that build-plotart.py's
page() writes for a gallery page (Virtual Gallery pill current, artist fine print, noindex, follow);
prove-plotart-galleries.py requires the two to be byte-identical, so they cannot drift apart.
"""
import html

E = lambda s: html.escape(str(s), quote=True)
ARTIST_FINE = ("Artworks in this gallery are offered by the artist. PlotArt introduces buyers to artists: it doesn't take "
               "payment or deliver work. Photographs of artworks are supplied by the artist and credited where taken by someone else.")


def artist_page(path, title, desc, body, scripts=("plotart.js",)):
    depth = path.count("/")
    R = "../" * depth
    T = "../" * (depth + 1)
    pill = lambda key, href, lbl, track: '<a class="pa-pill" href="%s"%s data-pa-track="%s">%s</a>' % (href, ' aria-current="page"' if key == "vg" else "", track, lbl)
    header = ('<header class="pa-head pa-head--pills">\n  <div class="pa-wrap">\n'
              '    <a class="pa-brand" href="%sindex.html" aria-label="PlotArt home"><span class="pa-word">PlotArt</span><span class="pa-part"><img src="/assets/brand/plotnua-mark-master.svg" alt="" width="18" height="18"><span>Part of PlotNua</span></span></a>\n'
              '    <nav class="pa-pills" aria-label="PlotArt">%s%s%s%s</nav>\n  </div>\n</header>') % (
        R, pill("home", R + "index.html", "Discover PlotArt", "nav_discover_plotart"),
        pill("vg", R + "gallery/", "Virtual Gallery", "nav_virtual_gallery"),
        pill("lg", R + "living-gallery.html", "Living Gallery", "nav_living_gallery"),
        '<a class="pa-pill pa-pill--out" href="%sindex.html" aria-label="PlotNua homepage" data-pa-track="cross_plotnua_home">PlotNua <span aria-hidden="true">↗</span></a>' % T)
    # Phone Menu (founder approval 30 Oct 2026): the same links in the shared one-row Menu
    import re as _re
    _nav = _re.search(r'<nav class="pa-pills"[^>]*>(.*?)</nav>', header, _re.S).group(1)
    _items = []
    for _a in _re.findall(r'<a\b[^>]*>.*?</a>', _nav, _re.S):
        _a2 = _re.sub(r'class="[^"]*"', 'class="%s"' % ('pn-sm-link is-out' if 'pa-pill--out' in _a else 'pn-sm-link'), _a, 1)
        _items.append(_re.sub(r'\sdata-pa-track="([^"]*)"', r' data-pa-track="\1_menu"', _a2))
    _menu = ('<details class="pn-sm" data-pn-menu><summary class="pn-sm-btn"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" '
             'stroke-width="1.6" stroke-linecap="round" aria-hidden="true" focusable="false"><path class="pn-menu-l1" d="M3.5 6h13"/>'
             '<path class="pn-menu-l2" d="M3.5 10h13"/><path class="pn-menu-l3" d="M3.5 14h13"/></svg><span>Menu</span></summary>'
             '<div class="pn-sm-panel">%s</div></details>') % "".join(_items)
    header = header.replace('</nav>\n  </div>\n</header>', '</nav>\n    ' + _menu + '\n  </div>\n</header>', 1)
    sc = "".join('<script src="%sassets/%s" defer></script>' % (R, s) for s in scripts)
    footlinks = ('<li><a href="{R}gallery/">Virtual Gallery</a></li><li><a href="{R}living-gallery.html">Living Gallery</a></li>'
                 '<li><a href="{R}about.html">About PlotArt</a></li><li><a href="{R}founding-25.html">The Founding 25</a></li>').format(R=R)
    robots = ('<!-- LIMITED LAUNCH: not for indexing until the founder approves indexing. Planned canonical:\n     https://plotnua.ie/plotart/%s -->\n'
              '<meta name="robots" content="noindex, follow">') % E(path)
    return path, """<!DOCTYPE html>
<html lang="en-IE" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
{robots}
<meta name="theme-color" content="#27282A">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="{R}assets/plotart.css">
<link rel="stylesheet" href="/assets/identity/pn-section-menu.css?v=1">
<script>document.documentElement.classList.remove('no-js');</script>
</head>
<body class="pa">
<a class="pa-skip" href="#main">Skip to content</a>
{header}
<main id="main">
{body}
</main>
<footer class="pa-foot">
  <div class="pa-wrap">
    <div>
      <p style="font-family:var(--serif);font-size:30px;letter-spacing:.02em;color:var(--ivory);margin:0 0 6px">PlotArt</p>
      <p style="margin:0 0 14px">Original Art. Real Homes. New Possibilities.</p>
      <p style="margin:0">Part of <a href="{T}index.html">PlotNua</a>, the Irish home-discovery platform.</p>
    </div>
    <div>
      <h2>PlotArt</h2>
      <ul>{footlinks}</ul>
    </div>
    <div>
      <h2>PlotNua</h2>
      <ul><li><a href="{T}discovery-a-home-for-art.html" data-pa-track="cross_home_for_art">A Home for Art</a></li><li><a href="{T}discoveries.html" data-pa-track="cross_discoveries">Discovery Library</a></li><li><a href="{T}privacy.html">Privacy</a></li><li><a href="{T}terms.html#legal-information">Terms &amp; legal information</a></li><li><a href="{T}contact.html">Contact</a></li></ul>
    </div>
    <p class="fine">{fine}</p>
  </div>
</footer>
{sc}
<script src="/assets/identity/pn-menu.js?v=1" defer></script>
</body>
</html>
""".format(title=E(title), desc=E(desc), robots=robots, R=R, T=T, header=header, body=body, footlinks=footlinks, fine=ARTIST_FINE, sc=sc)
