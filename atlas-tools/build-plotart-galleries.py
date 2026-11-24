#!/usr/bin/env python3
"""PlotArt · three galleries, Phase A (founder approval 24 Nov 2026). Builds:

  plotart/index.html               the region between the pa-galleries markers: the one heading "A new home for Irish art."
                                   and the three gallery entrances (Contemporary Art · Landscape Art · Portraiture)
  plotart/gallery/index.html       the region between the pa-gallery-tabs markers (the gallery tabs); the page's own
                                   heading is "Contemporary Art." (the collection, order and Featured Artists are untouched)
  plotart/landscape/index.html     the holding page of a gallery in preparation (whole page, from the shared shell)
  plotart/portraiture/index.html   the same

  python3 atlas-tools/build-plotart-galleries.py ROOT            write
  python3 atlas-tools/build-plotart-galleries.py ROOT --check    exit 1 if any file differs from what would be written

Only images PlotArt already publishes are used: the founder's own credited painting on the Contemporary Art entrance,
shown whole (never cropped). A gallery in preparation shows a neutral "in preparation" panel instead of artwork, says it
is in preparation, and shows no artist, artwork or image (guard L21). Opening a gallery is Phase E: the shell refuses
any state other than in_preparation for Landscape Art and Portraiture."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plotart_seo as SEO  # noqa: E402
import plotart_shell as S  # noqa: E402
S.HIRE_NAV = SEO.switches().get("art_for_hire_page") is True   # as plotart-gallery-publish.py: the Art for Hire tab follows its switch

E = S.E
OPEN_FINE = "Artworks in PlotArt galleries are offered by their artists: PlotArt introduces buyers; the artist is the seller."
HOME_BEGIN, HOME_END = "<!-- pa-galleries:begin -->", "<!-- pa-galleries:end -->"
TABS_BEGIN, TABS_END = "<!-- pa-gallery-tabs:begin -->", "<!-- pa-gallery-tabs:end -->"
FOUNDER_IMG = ('<img src="assets/hero/founder-01-abstract.webp" width="1332" height="940" alt="Painting by Colin MacAulay: an abstract '
               'of bold yellow outlined shapes over deep violet loops and pink and blue lines on grey" decoding="async" fetchpriority="high">')
FOUNDER_CREDIT = "Original artwork by Colin MacAulay, founder of PlotArt."

GALLERY = {
    "contemporary": {"title": "Contemporary Art", "text": "Discover original contemporary art from Irish artists."},
    "landscape": {"title": "Landscape Art", "text": "Explore Ireland’s landscapes, seascapes and places through original art.",
                  "artists": "PlotArt welcomes expressions of interest from artists whose work explores Ireland’s landscapes, seascapes and places.",
                  "icon": '<svg viewBox="0 0 160 100" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><rect x="1" y="1" width="158" height="98" rx="2"/><circle cx="118" cy="28" r="9"/><path d="M1 74 C28 58 44 60 62 68 S104 52 159 64"/><path d="M1 86 C40 78 82 90 159 80"/></svg>'},
    "portraiture": {"title": "Portraiture", "text": "Discover expressive portraits and individual artistic interpretations of the human subject.",
                    "artists": "PlotArt welcomes expressions of interest from artists whose work explores portraiture and the human subject.",
                    "icon": '<svg viewBox="0 0 100 124" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><rect x="1" y="1" width="98" height="122" rx="2"/><ellipse cx="50" cy="50" rx="17" ry="21"/><path d="M18 123 C20 96 34 84 50 84 S80 96 82 123"/></svg>'},
}
HREF = {k: h for k, h, _l, _t in S.GALLERIES}


def prep_panel(key, where):
    g = GALLERY[key]
    return ('<div class="pa-gx-prep" data-pa-placeholder="%s" role="img" aria-label="%s is in preparation. No artwork is shown yet.">%s'
            '<p>Artwork will be shown here once %s’s artists have been selected.</p></div>') % (key, g["title"], g["icon"], g["title"])


def tile(key):
    g, state = GALLERY[key], S.gallery_state(key)
    if state == "open":       # Contemporary Art: the existing gallery
        art = '<figure class="pa-gx-art">%s</figure>\n      <p class="pa-gx-credit">%s</p>' % (FOUNDER_IMG, FOUNDER_CREDIT)
        status = '<p class="pa-gx-status pa-gx-status--open">Gallery open</p>'
        label = "Enter the %s gallery" % g["title"]
    else:
        art = '<figure class="pa-gx-art">%s</figure>' % prep_panel(key, "home")
        status = '<p class="pa-gx-status">In preparation</p>'
        label = "About the %s gallery, in preparation" % g["title"]
    return ('    <li class="pa-gx-tile" data-pa-gallery="%s">\n      %s\n      <div class="pa-gx-body">%s<h2>%s</h2>'
            '<p class="pa-gx-text">%s</p><a class="pa-gx-go" href="%s" data-pa-track="home_gallery_%s" aria-label="%s">'
            '<span aria-hidden="true">→</span></a></div>\n    </li>\n') % (key, art, status, g["title"], g["text"], HREF[key], key, label)


def home_region():
    return (HOME_BEGIN + '\n<section class="pa-gx" aria-labelledby="homeH"><div class="pa-wrap">\n'
            '  <h1 class="pa-gx-h1" id="homeH">A new home for Irish art.</h1>\n'
            '  <ul class="pa-gx-tiles" aria-label="PlotArt galleries">\n' + "".join(tile(k) for k, *_ in S.GALLERIES) +
            '  </ul>\n</div></section>\n' + HOME_END)


def tabs_region(current):
    return TABS_BEGIN + "\n" + S.gallery_tabs("../", current) + "\n" + TABS_END


def holding_page(key):
    g = GALLERY[key]
    path = HREF[key] + "index.html"
    # For artists: the same in every application state (L18 keeps recruitment links to the Join page while it is open only),
    # so this section points to the For artists page, which always exists.
    artists = ('\n<section class="pa-gh-artists" aria-labelledby="ghArtH"><div class="pa-wrap">\n'
               '  <div><p class="pa-eyebrow">For artists</p><h2 id="ghArtH">%s artists</h2></div>\n'
               '  <div><p>%s</p>\n'
               '  <p><a class="pa-btn pa-btn--ghost" href="../for-artists.html" data-pa-track="%s_for_artists">How PlotArt works with artists <span aria-hidden="true">→</span></a></p></div>\n'
               '</div></section>') % (g["title"], g["artists"], key)
    body = (tabs_region(key) + '\n\n<section class="pa-gh" aria-labelledby="ghH"><div class="pa-wrap pa-gh-grid">\n'
            '  <div><p class="pa-eyebrow">A PlotArt gallery</p><h1 id="ghH">%s.</h1>\n'
            '  <p class="pa-gh-lede">%s</p>\n'
            '  <p class="pa-gh-status">In preparation</p>\n'
            '  <p class="pa-gh-note">This gallery is being prepared. It will open once PlotArt has selected its artists and artworks. '
            'Until then, no artists or artworks are shown here.</p>\n'
            '  <div class="pa-gh-acts"><a class="pa-btn pa-btn--solid" href="../gallery/" data-pa-track="%s_to_contemporary">Explore Contemporary Art <span aria-hidden="true">→</span></a>'
            '<a class="pa-btn pa-btn--ghost" href="../artworks/" data-pa-track="%s_to_artworks">Browse All Artworks <span aria-hidden="true">→</span></a></div></div>\n'
            '  <figure class="pa-gh-art">%s</figure>\n'
            '</div></section>%s\n') % (g["title"], g["text"], key, key, prep_panel(key, "page"), artists)
    title = "%s | In Preparation | PlotArt" % g["title"]
    desc = "%s at PlotArt: a gallery of original Irish art, in preparation. %s" % (g["title"], g["text"])
    fine = OPEN_FINE + " %s is in preparation: no artists or artworks are shown in it yet." % g["title"]
    _p, doc = S.artist_page(path, title, desc, body, current=key, fine=fine, styles=("../assets/plotart-galleries.css",))
    return path, doc


def replace_region(text, begin, end, new, name):
    if text.count(begin) != 1 or text.count(end) != 1 or text.index(begin) > text.index(end):
        raise ValueError("%s: expected exactly one %s … %s region" % (name, begin, end))
    a, b = text.index(begin), text.index(end) + len(end)
    return text[:a] + new + text[b:]


def plan(root):
    pa = os.path.join(root, "plotart")
    out = {}
    home = open(os.path.join(pa, "index.html"), encoding="utf-8").read()
    out["index.html"] = replace_region(home, HOME_BEGIN, HOME_END, home_region(), "index.html")
    vg = open(os.path.join(pa, "gallery", "index.html"), encoding="utf-8").read()
    out["gallery/index.html"] = replace_region(vg, TABS_BEGIN, TABS_END, tabs_region("contemporary"), "gallery/index.html")
    for key in ("landscape", "portraiture"):
        path, doc = holding_page(key)
        out[path] = doc
    return out


def main(root, check=False):
    pa = os.path.join(root, "plotart")
    try:
        files = plan(root)
    except ValueError as e:
        print("REFUSED (nothing written): %s" % e)
        return 2
    stale = []
    for rel, doc in files.items():
        p = os.path.join(pa, rel)
        cur = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        if cur != doc:
            stale.append(rel)
            if not check:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, "w", encoding="utf-8").write(doc)
    print("PLOTART GALLERIES · %d files, %d %s" % (len(files), len(stale), "stale" if check else "written") + (": " + ", ".join(stale) if stale else ""))
    return 1 if (check and stale) else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], "--check" in sys.argv))
