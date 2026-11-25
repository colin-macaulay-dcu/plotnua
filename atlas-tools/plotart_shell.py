"""PlotArt page shell for artist gallery pages (Phase 3, 29 Oct 2026).

The production content pipeline (atlas-tools/plotart-gallery-publish.py, on main) renders artist gallery pages
WITHOUT the full PlotArt builder. This module reproduces exactly the launch page shell that build-plotart.py's
page() writes for a gallery page (Virtual Gallery pill current, artist fine print, founder-controlled indexing);
prove-plotart-galleries.py requires the two to be byte-identical, so they cannot drift apart.
"""
import html
import plotart_seo as SEO

E = lambda s: html.escape(str(s), quote=True)
ARTIST_FINE = ("Artworks in this gallery are offered by the artist. PlotArt introduces buyers to artists. The artist is the "
               "seller and arranges delivery. Photographs of artworks are supplied by the artist and credited where taken by someone else.")
# Art for Hire (Stage 3B-4): the fourth gallery tab. OFF until the founder releases the Art for Hire page; with it off every
# page this module writes is byte-identical to before. atlas-tools/plotart-hire-nav.py adds the same tab to hand-built pages.
HIRE_NAV = False
HIRE_PILL = ("hire", "art-for-hire/", "Art for Hire", "nav_art_for_hire")
# Services (founder brief 19 Nov 2026): the "Art Services & Providers" page, the last PlotArt tab before PlotNua ↗, on every
# PlotArt page. atlas-tools/plotart-services-nav.py adds the same tab to hand-built and already-published pages.
SERVICES_PILL = ("services", "services.html", "Services", "nav_services")
# Withdrawn 19 Nov 2026 (founder: both providers asked for changes): the tab appears only while the launch switch
# services_page is on, so no publication can restore it by accident.
SERVICES_NAV = SEO.switches().get("services_page") is True


# The existing PlotArt Studio (Cloudflare Access one-time code sign-in). Linked from the footer and the For artists page
# (founder decision 17 Nov 2026); the address itself is public, the Studio stays behind its sign-in.
STUDIO = "https://plotart-studio.colin-a41.workers.dev/"
# Artist Login (founder brief 17 Nov 2026): one off-white pill at the right-hand end of every PlotArt header, outside the
# gallery pills and outside the phone Menu (so it stays visible on phones and is never listed twice). It only links to the
# existing Studio; signing in stays with the Studio's Cloudflare Access one-time code.
LOGIN = '<a class="pa-login" href="%s" data-pa-track="nav_artist_login">Artist Login</a>' % STUDIO
FOOT_ARTISTS = '<li><a href="%s" data-pa-track="footer_artist_studio">Artist Studio</a></li><li><a href="{R}for-artists.html" data-pa-track="footer_for_artists">For artists</a></li>' % STUDIO


# Three galleries (founder approval of Phase A, 24 Nov 2026; FINAL identity approved by the founder 24 Nov 2026):
#   Contemporary (artistic expression) at gallery/, the existing Artists' Gallery (same address, same collection);
#   Environment (the world around us) at environment/; Being (our existence within it) at being/.
# Environment and Being are shown "In preparation" until the founder opens them (launch switches environment_gallery_state /
# being_gallery_state). Functional labels carry no full stop; the full stop is the editorial treatment of the homepage
# entrances and the gallery headings only (build-plotart-galleries.py). Former addresses landscape/, places-and-spaces/ and
# portraiture/ are generated redirect pages. atlas-tools/plotart-galleries-nav.py applies exactly this markup to hand-built and
# already-published pages; prove-plotart-launch.py L11 and L21 check it. Mobile Gallery left the Galleries menu and is its own
# pill again, straight after it (founder brief 25 Nov 2026: restore Mobile Gallery to the primary navigation).
GALLERIES = (("contemporary", "gallery/", "Contemporary", "nav_gallery_contemporary"),
             ("environment", "environment/", "Environment", "nav_gallery_environment"),
             ("being", "being/", "Being", "nav_gallery_being"))
GALLERY_STATES = ("in_preparation",)   # Phase A: no new gallery can be opened; opening is Phase E (guard L21)
FOOT_GALLERIES = ('<li><a href="{R}gallery/">Contemporary</a></li><li><a href="{R}environment/">Environment</a></li>'
                  '<li><a href="{R}being/">Being</a></li><li><a href="{R}mobile-gallery/">Mobile Gallery</a></li>')
PREP_NOTE = '<span class="pa-dd-note">In preparation</span>'


def gallery_state(key):
    """'open' for Contemporary; for a new gallery, its launch switch (anything but 'in_preparation' is refused here)."""
    if key == "contemporary":
        return "open"
    st = SEO.switches().get(key + "_gallery_state")
    if st not in GALLERY_STATES:
        raise ValueError("%s_gallery_state must be one of %s in Phase A, not %r" % (key, GALLERY_STATES, st))
    return st


def galleries_menu(R, current, mg_href=None):
    """The header's Galleries menu: the three galleries only. current: a gallery key marks that page's link (aria-current);
    "vg" (an artist's gallery or artwork page, all of which are in Contemporary today) marks only the menu itself as the
    current section. Mobile Gallery is its own pill again, straight after this menu (mobile_gallery_pill, founder brief
    25 Nov 2026); mg_href is accepted for callers that still pass it and is not used here."""
    keys = {g[0] for g in GALLERIES}
    links = []
    for key, href, label, track in GALLERIES:
        links.append('<a class="pa-dd-link" href="%s%s"%s data-pa-track="%s">%s%s</a>' % (
            R, href, ' aria-current="page"' if key == current else "", track, label,
            PREP_NOTE if gallery_state(key) == "in_preparation" else ""))
    return ('<details class="pa-dd%s" data-pa-dd><summary class="pa-pill pa-pill--dd">Galleries</summary>'
            '<div class="pa-dd-panel">%s</div></details>') % (" is-current" if current in keys | {"vg"} else "", "".join(links))


def mobile_gallery_pill(R, current, mg_href=None):
    """The Mobile Gallery pill (restored to the primary navigation, founder brief 25 Nov 2026): straight after the Galleries
    menu, marked current on the Mobile Gallery's own pages."""
    return '<a class="pa-pill" href="%s"%s data-pa-track="nav_mobile_gallery">Mobile Gallery</a>' % (
        mg_href or R + "mobile-gallery/", ' aria-current="page"' if current == "mg" else "")


def menu_items(nav):
    """The phone Menu links, in header order, from the header navigation (pills and Galleries menu links alike)."""
    import re as _re
    items = []
    for a in _re.findall(r'<a\b[^>]*>.*?</a>', nav, _re.S):
        a2 = _re.sub(r'class="[^"]*"', 'class="%s"' % ('pn-sm-link is-out' if 'pa-pill--out' in a else 'pn-sm-link'), a, 1)
        items.append(_re.sub(r'\sdata-pa-track="([^"]*)"', r' data-pa-track="\1_menu"', a2))
    return items


def gallery_tabs(R, current):
    """The tabs shared by the three gallery pages (Phase A): the same three galleries, the current one marked."""
    tabs = "".join('<li><a class="pa-gtab" href="%s%s"%s data-pa-track="gallery_tab_%s">%s%s</a></li>' % (
        R, href, ' aria-current="page"' if key == current else "", key, label,
        PREP_NOTE.replace("pa-dd-note", "pa-gtab-note") if gallery_state(key) == "in_preparation" else "")
        for key, href, label, _t in GALLERIES)
    return ('<nav class="pa-gtabs" aria-label="PlotArt galleries"><div class="pa-wrap"><ul class="pa-gtabs-list">%s</ul></div></nav>' % tabs)


def artist_page(path, title, desc, body, scripts=("plotart.js",), current="vg", hire_nav=None, fine=ARTIST_FINE, styles=(), services_nav=None):
    hire_nav = HIRE_NAV if hire_nav is None else hire_nav
    services_nav = SERVICES_NAV if services_nav is None else services_nav
    depth = path.count("/")
    R = "../" * depth
    T = "../" * (depth + 1)
    pill = lambda key, href, lbl, track: '<a class="pa-pill" href="%s"%s data-pa-track="%s">%s</a>' % (href, ' aria-current="page"' if key == current else "", track, lbl)
    header = ('<header class="pa-head pa-head--pills">\n  <div class="pa-wrap">\n'
              '    <a class="pa-brand" href="%sindex.html" aria-label="PlotArt home"><img class="pa-logo" src="/assets/brand/plotart-logo-stacked.svg" width="63" height="62" alt=""></a>\n'
              '    <nav class="pa-pills%s" aria-label="PlotArt">%s%s%s%s%s</nav>\n  </div>\n</header>') % (
        R, " pa-pills--hire" if hire_nav else "", pill("home", R + "index.html", "Discover PlotArt", "nav_discover_plotart"),
        galleries_menu(R, current) + mobile_gallery_pill(R, current),
        pill("lg", R + "living-gallery.html", "Living Gallery", "nav_living_gallery"),
        (pill(HIRE_PILL[0], R + HIRE_PILL[1], HIRE_PILL[2], HIRE_PILL[3]) if hire_nav else "")
        + (pill(SERVICES_PILL[0], R + SERVICES_PILL[1], SERVICES_PILL[2], SERVICES_PILL[3]) if services_nav else ""),
        '<a class="pa-pill pa-pill--out" href="%sindex.html" data-pa-track="cross_plotnua_home"><span class="pa-pn" style="display:inline-flex;align-items:baseline;white-space:nowrap"><img class="pa-pn-p" src="/assets/brand/plotnua-icon-transparent.svg" alt="" width="18" height="18" style="display:block;flex:none;max-width:none;width:1.22em;height:1.22em;margin:-0.27em -0.2em 0 -0.29em;position:relative;top:0.215em"><span class="pa-sr">P</span>lotNua</span> <span aria-hidden="true">↗</span></a>' % T)
    # Phone Menu (founder approval 30 Oct 2026): the same links in the shared one-row Menu
    import re as _re
    _nav = _re.search(r'<nav class="pa-pills[^"]*"[^>]*>(.*?)</nav>', header, _re.S).group(1)
    _items = menu_items(_nav)
    _menu = ('<details class="pn-sm" data-pn-menu><summary class="pn-sm-btn"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" '
             'stroke-width="1.6" stroke-linecap="round" aria-hidden="true" focusable="false"><path class="pn-menu-l1" d="M3.5 6h13"/>'
             '<path class="pn-menu-l2" d="M3.5 10h13"/><path class="pn-menu-l3" d="M3.5 14h13"/></svg><span>Menu</span></summary>'
             '<div class="pn-sm-panel">%s</div></details>') % "".join(_items)
    header = header.replace('</nav>\n  </div>\n</header>', '</nav>\n    ' + LOGIN + '\n    ' + _menu + '\n  </div>\n</header>', 1)
    sc = "".join('<script src="%sassets/%s" defer></script>' % (R, s) for s in scripts)
    footlinks = (FOOT_GALLERIES + '<li><a href="{R}living-gallery.html">Living Gallery</a></li>'
                 + ('<li><a href="{R}art-for-hire/">Art for Hire</a></li>' if hire_nav else '') + ('<li><a href="{R}services.html">Services</a></li>' if services_nav else '') +
                 '<li><a href="{R}about.html">About PlotArt</a></li><li><a href="{R}founding-25.html">The Founding 25</a></li>' + FOOT_ARTISTS).format(R=R)
    robots = SEO.head(path, title, desc)
    return path, """<!DOCTYPE html>
<html lang="en-IE" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
{robots}
<meta name="theme-color" content="#27282A">
<link rel="icon" href="/assets/brand/plotart-favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/brand/plotart-apple-touch-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="{R}assets/plotart.css">{styles}
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
""".format(title=E(title), desc=E(desc), robots=robots, R=R, T=T, header=header, body=body, footlinks=footlinks, fine=fine, sc=sc,
           styles="".join('\n<link rel="stylesheet" href="%s">' % s for s in styles))
