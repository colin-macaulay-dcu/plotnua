#!/usr/bin/env python3
"""PlotArt · three galleries, Phase A (founder approval 24 Nov 2026). Builds:

  plotart/index.html               the region between the pa-galleries markers: the one heading "A new home for Irish art."
                                   and the three gallery entrances (Contemporary Art · Places & Spaces · Portraiture)
  plotart/gallery/index.html       the region between the pa-gallery-tabs markers (the gallery tabs); the page's own
                                   heading is "Contemporary Art." (the collection, order and Featured Artists are untouched)
  plotart/places-and-spaces/index.html   the holding page of a gallery in preparation (whole page, from the shared shell)
  plotart/portraiture/index.html   the same
  plotart/landscape/index.html     a redirect page: Places & Spaces was named Landscape Art until 24 Nov 2026 (founder's
                                   gallery identity revision); its old address sends visitors on, keeping any query string

  python3 atlas-tools/build-plotart-galleries.py ROOT            write
  python3 atlas-tools/build-plotart-galleries.py ROOT --check    exit 1 if any file differs from what would be written

Only images PlotArt already publishes are used: the founder's own credited painting on the Contemporary Art entrance,
shown whole (never cropped). A gallery in preparation shows a neutral "in preparation" panel instead of artwork, says it
is in preparation, and shows no artist, artwork or image (guard L21). Opening a gallery is Phase E: the shell refuses
any state other than in_preparation for Places & Spaces and Portraiture."""
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
    # Places & Spaces (founder's gallery identity revision, 24 Nov 2026; formerly Landscape Art): natural landscapes, coastlines,
    # countryside, urban environments, streets, cityscapes, architecture, interiors, rural buildings, industrial structures,
    # abandoned and changing spaces, and abstract or imagined interpretations of place.
    "places_and_spaces": {"title": "Places & Spaces", "text": "Exploring the environments we inhabit, encounter and imagine.",
                  "lede": "Exploring the environments we inhabit, encounter and imagine. From natural landscapes and coastlines to urban streets, "
                          "architectural forms and forgotten spaces, this gallery brings together diverse artistic interpretations of place and our relationship with it.",
                  "desc": "Places & Spaces at PlotArt, in preparation: original art exploring the environments we inhabit, encounter and imagine, "
                          "from landscapes and coastlines to streets, architecture and forgotten spaces.",
                  "artists": "PlotArt welcomes expressions of interest from artists whose work explores place: natural landscapes, coastlines and countryside, "
                             "urban streets and cityscapes, architecture and interiors, rural and industrial buildings, abandoned and changing spaces, "
                             "and abstract or imagined interpretations of place.",
                  "icon": '<svg viewBox="0 0 160 100" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><rect x="1" y="1" width="158" height="98" rx="2"/><circle cx="128" cy="24" r="8"/><path d="M1 72 C26 60 42 62 58 68"/><path d="M58 99 V52 H84 V99"/><path d="M84 99 V36 L98 26 L112 36 V99"/><path d="M66 62 H76 M66 74 H76 M92 46 H104 M92 60 H104 M92 74 H104"/><path d="M112 74 C126 68 140 70 159 66"/></svg>'},
    "portraiture": {"title": "Portraiture", "text": "Discover expressive portraits and individual artistic interpretations of the human subject.",
                    "artists": "PlotArt welcomes expressions of interest from artists whose work explores portraiture and the human subject.",
                    "icon": '<svg viewBox="0 0 100 124" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><rect x="1" y="1" width="98" height="122" rx="2"/><ellipse cx="50" cy="50" rx="17" ry="21"/><path d="M18 123 C20 96 34 84 50 84 S80 96 82 123"/></svg>'},
}
HREF = {k: h for k, h, _l, _t in S.GALLERIES}
ENTRANCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "release", "plotart-gallery-entrances.json")
ART_KEYS = {"artist_slug", "image", "width", "height", "alt", "credit", "consent_ref"}


def entrances(path=None):
    """The founder's entrance artwork for the galleries in preparation (null = the neutral panel). Shape-checked here;
    the guard (L21) also checks the image's provenance record and the consent reference."""
    import json
    d = json.load(open(path or ENTRANCES, encoding="utf-8"))
    out = {}
    for key in ("places_and_spaces", "portraiture"):
        art = (d.get(key) or {}).get("artwork")
        if art is not None:
            if set(art) != ART_KEYS or not re.fullmatch(r"artists/%s/img/[a-z0-9-]+-\d{2,5}\.webp" % re.escape(str(art["artist_slug"])), str(art["image"])):
                raise ValueError("plotart-gallery-entrances.json: %s artwork must have exactly %s and an image in that artist's img/ folder" % (key, sorted(ART_KEYS)))
            if not str(art.get("consent_ref") or "").strip():
                raise ValueError("plotart-gallery-entrances.json: %s artwork has no consent_ref (per-use consent, licence §3.2)" % key)
        out[key] = art
    return out


def prep_panel(key, where):
    g = GALLERY[key]
    return ('<div class="pa-gx-prep" data-pa-placeholder="%s" role="img" aria-label="%s is in preparation. No artwork is shown yet.">%s'
            '<p>Artwork will be shown here once %s’s artists have been selected.</p></div>') % (key, E(g["title"]), g["icon"], E(g["title"]))


def tile(key, arts):
    """One entrance. The artwork mount has the same shape on every entrance and holds its own credit, so the status,
    title and description of the three entrances line up whatever is shown above them. Artwork is shown whole."""
    g, state = GALLERY[key], S.gallery_state(key)
    if state == "open":       # Contemporary Art: the existing gallery
        art = '<figure class="pa-gx-art">%s<figcaption class="pa-gx-credit">%s</figcaption></figure>' % (FOUNDER_IMG, FOUNDER_CREDIT)
        status = '<p class="pa-gx-status pa-gx-status--open">Gallery open</p>'
        label = "Enter the %s gallery" % E(g["title"])
    else:
        a = arts.get(key)
        if a:                 # authorised artwork supplied by the founder (L21 checks provenance and consent)
            art = ('<figure class="pa-gx-art" data-pa-entrance-art="%s"><img src="%s" width="%d" height="%d" alt="%s" loading="lazy" decoding="async">'
                   '<figcaption class="pa-gx-credit">%s</figcaption></figure>') % (key, E(a["image"]), int(a["width"]), int(a["height"]), E(a["alt"]), E(a["credit"]))
        else:
            art = '<figure class="pa-gx-art">%s</figure>' % prep_panel(key, "home")
        status = '<p class="pa-gx-status">In preparation</p>'
        label = "About the %s gallery, in preparation" % E(g["title"])
    return ('    <li class="pa-gx-tile" data-pa-gallery="%s">\n      %s\n      <div class="pa-gx-body">%s<h2>%s</h2>'
            '<p class="pa-gx-text">%s</p><a class="pa-gx-go" href="%s" data-pa-track="home_gallery_%s" aria-label="%s">'
            '<span aria-hidden="true">→</span></a></div>\n    </li>\n') % (key, art, status, E(g["title"]), E(g["text"]), HREF[key], key, label)


def home_region(arts=None):
    arts = entrances() if arts is None else arts
    return (HOME_BEGIN + '\n<section class="pa-gx" aria-labelledby="homeH"><div class="pa-wrap">\n'
            '  <h1 class="pa-gx-h1" id="homeH">A new home for Irish art.</h1>\n'
            '  <ul class="pa-gx-tiles" aria-label="PlotArt galleries">\n' + "".join(tile(k, arts) for k, *_ in S.GALLERIES) +
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
               '</div></section>') % (E(g["title"]), E(g["artists"]), key)
    body = (tabs_region(key) + '\n\n<section class="pa-gh" aria-labelledby="ghH"><div class="pa-wrap pa-gh-grid">\n'
            '  <div><p class="pa-eyebrow">A PlotArt gallery</p><h1 id="ghH">%s.</h1>\n'
            '  <p class="pa-gh-lede">%s</p>\n'
            '  <p class="pa-gh-status">In preparation</p>\n'
            '  <p class="pa-gh-note">This gallery is being prepared. It will open once PlotArt has selected its artists and artworks. '
            'Until then, no artists or artworks are shown here.</p>\n'
            '  <div class="pa-gh-acts"><a class="pa-btn pa-btn--solid" href="../gallery/" data-pa-track="%s_to_contemporary">Explore Contemporary Art <span aria-hidden="true">→</span></a>'
            '<a class="pa-btn pa-btn--ghost" href="../artworks/" data-pa-track="%s_to_artworks">Browse All Artworks <span aria-hidden="true">→</span></a></div></div>\n'
            '  <figure class="pa-gh-art">%s</figure>\n'
            '</div></section>%s\n') % (E(g["title"]), E(g.get("lede", g["text"])), key, key, prep_panel(key, "page"), artists)
    title = "%s | In Preparation | PlotArt" % g["title"]          # plain text: the shell escapes the title and description
    desc = g.get("desc") or "%s at PlotArt: a gallery of original Irish art, in preparation. %s" % (g["title"], g["text"])
    fine = OPEN_FINE + " %s is in preparation: no artists or artworks are shown in it yet." % E(g["title"])
    _p, doc = S.artist_page(path, title, desc, body, current=key, fine=fine, styles=("../assets/plotart-galleries.css",))
    return path, doc


# The gallery's former address (Landscape Art, 24 Nov 2026). GitHub Pages cannot send a server 301, so this page is the
# site's established permanent redirect (see discovery-open-your-home-to-art.html): canonical to the new address, noindex,
# an immediate script redirect that keeps any query string and fragment, and a meta refresh for browsers without script.
LEGACY = ("landscape/index.html", "places-and-spaces/")


def legacy_redirect():
    to = "https://plotnua.ie/plotart/" + LEGACY[1]
    return ('<!DOCTYPE html>\n<html lang="en-IE">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Places &amp; Spaces | PlotArt</title>\n<meta name="robots" content="noindex, follow">\n<link rel="canonical" href="%s">\n'
            '<!-- PERMANENT REDIRECT. Landscape Art was renamed Places & Spaces (founder decision, 24 Nov 2026); this is its former\n'
            '     address. Generated by atlas-tools/build-plotart-galleries.py. Not in the sitemap. -->\n'
            '<script>location.replace("../%s" + location.search + location.hash);</script>\n'
            '<noscript><meta http-equiv="refresh" content="0; url=../%s"></noscript>\n'
            '<style>body{font-family:system-ui,sans-serif;background:#27282A;color:#EDEBE7;margin:0;padding:12vh 7vw;line-height:1.6}a{color:#C9D88A}</style>\n'
            '</head>\n<body>\n<p>Landscape Art is now <a href="../%s">Places &amp; Spaces</a>.</p>\n</body>\n</html>\n') % (to, LEGACY[1], LEGACY[1], LEGACY[1])


def replace_region(text, begin, end, new, name):
    if text.count(begin) != 1 or text.count(end) != 1 or text.index(begin) > text.index(end):
        raise ValueError("%s: expected exactly one %s … %s region" % (name, begin, end))
    a, b = text.index(begin), text.index(end) + len(end)
    return text[:a] + new + text[b:]


def plan(root, entrances_path=None):
    pa = os.path.join(root, "plotart")
    out = {}
    home = open(os.path.join(pa, "index.html"), encoding="utf-8").read()
    out["index.html"] = replace_region(home, HOME_BEGIN, HOME_END, home_region(entrances(entrances_path)), "index.html")
    vg = open(os.path.join(pa, "gallery", "index.html"), encoding="utf-8").read()
    out["gallery/index.html"] = replace_region(vg, TABS_BEGIN, TABS_END, tabs_region("contemporary"), "gallery/index.html")
    for key in ("places_and_spaces", "portraiture"):
        path, doc = holding_page(key)
        out[path] = doc
    out[LEGACY[0]] = legacy_redirect()
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
