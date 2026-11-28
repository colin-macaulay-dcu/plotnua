"""PlotArt page shell for artist gallery pages (Phase 3, 29 Oct 2026).

The production content pipeline (atlas-tools/plotart-gallery-publish.py, on main) renders artist gallery pages
WITHOUT the full PlotArt builder. This module reproduces exactly the launch page shell that build-plotart.py's
page() writes for a gallery page (Virtual Gallery pill current, artist fine print, founder-controlled indexing);
prove-plotart-galleries.py requires the two to be byte-identical, so they cannot drift apart.
"""
import html
import re
import plotart_seo as SEO

E = lambda s: html.escape(str(s), quote=True)

# Analytics (SEO and analytics package, founder approval 26 Nov 2026, section 1.2): the one approved head block, identical
# to PlotNua's except content_group. Consent Mode v2 defaults (Basic: everything denied until the visitor allows statistics;
# exempt from Cookiebot's blocking so it runs first), then the existing Cookiebot banner (domain group b8abbc45..., auto-
# blocking), then the existing GA4 property G-PKKJ0RK6N8, which Cookiebot holds back until consent. It is the first script
# in <head> of every PlotArt page, directly after the viewport meta (charset stays within the first 1024 bytes). Every
# PlotArt builder writes it from here; atlas-tools/plotart-analytics-head.py applies the same block to hand-built and
# already-published pages; prove-plotart-launch.py L23 and prove-plotart-wall-size.py check it is exactly this and nothing else.
COOKIEBOT_CBID = "b8abbc45-15b0-4d27-8f95-83ebd240a305"
GA4_ID = "G-PKKJ0RK6N8"
# Consent migration (prepared 27 Nov 2026, not released): PlotArt pages on plotnua.ie use the shared consent module with
# plotnua.ie's own consent record; Cookiebot and the static Google tag are gone (see seo_pn_consent.py).
import seo_pn_consent as _consent
ANALYTICS_HEAD = _consent.PLOTART_HEAD
_VIEWPORT = re.compile(r'<head>\n<meta charset="utf-8">\n<meta name="viewport" content="[^"]*">\n')


def with_analytics(doc):
    """doc with the approved analytics block directly after its viewport meta (unchanged if it is already there).
    Refuses a page whose head does not open with charset + viewport, or that holds any other copy of the block."""
    m = _VIEWPORT.search(doc)
    if not m or doc.count("<head>") != 1:
        raise ValueError("the page's <head> does not open with the charset and viewport metas")
    if doc[m.end():m.end() + len(ANALYTICS_HEAD)] == ANALYTICS_HEAD and doc.count(ANALYTICS_HEAD) == 1:
        return doc
    if "googletagmanager.com" in doc or "consent.cookiebot.com" in doc or "dataLayer" in doc:
        raise ValueError("the page already carries another analytics or consent script")
    return doc[:m.end()] + ANALYTICS_HEAD + doc[m.end():]


def analytics_ok(doc):
    """True when the approved block is present exactly once, first in <head> after charset and viewport, and the page loads
    no other third-party script (every other <script src> is same-site)."""
    m = _VIEWPORT.search(doc)
    if not m or doc[m.end():m.end() + len(ANALYTICS_HEAD)] != ANALYTICS_HEAD or doc.count(ANALYTICS_HEAD) != 1:
        return False
    rest = doc[:m.end()] + doc[m.end() + len(ANALYTICS_HEAD):]
    return not re.search(r'<script\b[^>]*\bsrc="(?:https?:)?//', rest) and "dataLayer" not in rest and "gtag(" not in rest
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


# Three galleries (founder approval of Phase A, 24 Nov 2026; final curatorial identity agreed by the founder 25 Nov 2026):
#   Contemporary (artistic expression) at gallery/, the existing Artists' Gallery (same address, same collection);
#   Spaces (the spaces we inhabit, encounter and imagine) at spaces/; Being (our existence) at being/.
# Spaces and Being are shown "In preparation" until the founder opens them (launch switches spaces_gallery_state /
# being_gallery_state). Functional labels carry no full stop; the full stop is the editorial treatment of the homepage
# entrances and the gallery headings only (build-plotart-galleries.py). Former addresses environment/, landscape/,
# places-and-spaces/ and portraiture/ are generated redirect pages. atlas-tools/plotart-galleries-nav.py applies exactly this markup to hand-built and
# already-published pages; prove-plotart-launch.py L11 and L21 check it.
GALLERIES = (("contemporary", "gallery/", "Contemporary", "nav_gallery_contemporary"),
             ("spaces", "spaces/", "Spaces", "nav_gallery_spaces"),
             ("being", "being/", "Being", "nav_gallery_being"))
GALLERY_STATES = ("in_preparation",)   # Phase A: no new gallery can be opened; opening is Phase E (guard L21)
FOOT_GALLERIES = ('<li><a href="{R}gallery/">Contemporary</a></li><li><a href="{R}spaces/">Spaces</a></li>'
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
    """The header's Galleries menu: the three galleries. current: a gallery key marks that page's link (aria-current); "vg" (an
    artist's gallery or artwork page, all of which are in Contemporary today) marks only the menu itself as the current section.
    Mobile Gallery is no longer in this menu: it is its own pill again, straight after this menu (founder decisions 25 Nov 2026;
    mobile_gallery_pill). mg_href is accepted for compatibility and ignored."""
    keys = {g[0] for g in GALLERIES}
    links = []
    for key, href, label, track in GALLERIES:
        links.append('<a class="pa-dd-link" href="%s%s"%s data-pa-track="%s">%s%s</a>' % (
            R, href, ' aria-current="page"' if key == current else "", track, label,
            PREP_NOTE if gallery_state(key) == "in_preparation" else ""))
    return ('<details class="pa-dd%s" data-pa-dd><summary class="pa-pill pa-pill--dd">Galleries</summary>'
            '<div class="pa-dd-panel">%s</div></details>') % (" is-current" if current in keys | {"vg"} else "", "".join(links))


def mobile_gallery_pill(href, current=False):
    """Mobile Gallery's own pill in the primary navigation, straight after the Galleries menu and before Living Gallery and
    Art for Hire, the order of the homepage's Beyond the Gallery tiles (founder decision, 25 Nov 2026)."""
    return '<a class="pa-pill" href="%s"%s data-pa-track="nav_mobile_gallery">Mobile Gallery</a>' % (href, ' aria-current="page"' if current else "")


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
        galleries_menu(R, current) + mobile_gallery_pill(R + "mobile-gallery/", current == "mg"),
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
                 '<li><a href="{R}about.html">About PlotArt</a></li>' + FOOT_ARTISTS).format(R=R)
    robots = SEO.head(path, title, desc)
    return path, """<!DOCTYPE html>
<html lang="en-IE" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{analytics}<title>{title}</title>
<meta name="description" content="{desc}">
{robots}
<meta name="theme-color" content="#27282A">
<link rel="icon" href="/assets/brand/plotart-favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/brand/plotart-apple-touch-180.png">
<link rel="preload" href="/plotart/assets/fonts/hanken-grotesk-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/plotart/assets/fonts/instrument-serif-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/plotart/assets/fonts/plotart-fonts.css?v=1">
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
""".format(analytics=ANALYTICS_HEAD, title=E(title), desc=E(desc), robots=robots, R=R, T=T, header=header, body=body, footlinks=footlinks, fine=fine, sc=sc,
           styles="".join('\n<link rel="stylesheet" href="%s">' % s for s in styles))
