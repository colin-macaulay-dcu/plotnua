"""Bounded collection excerpts for PlotArt's buyer guides. Public exports only.

The editorial copy is pinned separately. The publishing pipeline may refresh
only these generated regions, using the same approved galleries as the directory.
"""
import html
import json
import re
from pathlib import Path

import plotart_gallery_pages as P
import plotart_seo as SEO

BEGIN = "<!-- pa-guide-collection:begin -->"
END = "<!-- pa-guide-collection:end -->"
REGION = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
# Editorial classification, based on Leah's already-published artist statement
# ("abstract language") and practice. New artists are never auto-classified.
ABSTRACT_ARTISTS = frozenset({"leah-hewson"})
E = lambda x: html.escape(str(x), quote=True)


def available(packages, abstract=False):
    rows = []
    for pkg in sorted(packages, key=lambda p: (p["artist"]["display_name"].casefold(), p["artist"]["slug"])):
        if pkg["publication"].get("state") != "approved":
            raise ValueError("Guide input is not an approved public gallery")
        if abstract and pkg["artist"]["slug"] not in ABSTRACT_ARTISTS:
            continue
        rows.extend((pkg, w) for w in pkg["works"] if w["availability"] == "available")
    return rows


def work_url(pkg, work):
    return "artists/%s/%s.html" % (pkg["artist"]["slug"], work["slug"])


def collection_order(packages):
    """Every published, available work for the artwork collection, in a fair, stable order: the artists' galleries in
    publication order, then one work from each artist in turn (each artist's own work order kept), so no single gallery
    fills the top of the page. Reserved, sold, not-for-sale and withdrawn works never appear."""
    queues = []
    for pkg in P.gallery_order(list(packages)):
        if pkg["publication"].get("state") != "approved":
            raise ValueError("Collection input is not an approved public gallery")
        ws = [w for w in pkg["works"] if w["availability"] == "available"]
        if ws:
            queues.append([(pkg, w) for w in ws])
    out = []
    while any(queues):
        for q in queues:
            if q:
                out.append(q.pop(0))
    return out


def collection_card(pkg, w, n):
    """One work in the collection: the artist-approved image, uncropped, linking to its canonical artwork page."""
    a = pkg["artist"]
    im = P.main_image(w)
    d = P.pick(im, 1200)
    prefix = "../artists/%s/img/" % a["slug"]
    url = "../" + work_url(pkg, w)
    eager = n <= 3
    credit = '<p class="pa-coll-credit">Photograph: %s</p>' % E(im["photo_credit"]) if im.get("photo_credit") else ""
    return ('\n    <li class="pa-coll-work"><a class="pa-coll-art" href="%s">'
            '<img src="%s" srcset="%s" sizes="(max-width:639px) 92vw, (max-width:1099px) 46vw, 31vw" width="%d" height="%d" alt="%s"%s decoding="async"></a>'
            '<div class="pa-coll-label"><h3 class="pa-coll-title"><a href="%s">%s</a></h3>'
            '<p class="pa-coll-artist"><a href="../artists/%s/">%s</a></p>'
            '<p class="pa-coll-meta">%s<span aria-hidden="true"> · </span><span class="pa-coll-size">%s</span></p>'
            '<p class="pa-coll-price">%s</p>%s</div></li>') % (
        E(url), E(prefix + d["file"]), E(P.srcset(im, prefix)), d["pixels"][0], d["pixels"][1], E(im["alt"]),
        ' fetchpriority="high"' if n == 1 else ("" if eager else ' loading="lazy"'),
        E(url), E(w["title"]), E(a["slug"]), E(a["display_name"]), E(w["medium"]), E(P.size_line(w)[0]), E(P.price_line(w)), credit)


def collection_data(rows):
    """CollectionPage + ItemList (each item: the canonical artwork page) + BreadcrumbList. Describes the collection;
    makes no merchant, offer or availability claim."""
    url = SEO.canonical("artworks/index.html")
    graph = [{"@type": "CollectionPage", "@id": url + "#page", "url": url, "name": "Original Irish art for sale",
              "isPartOf": {"@type": "WebSite", "name": "PlotArt", "url": SEO.ORIGIN},
              "breadcrumb": {"@id": url + "#breadcrumbs"},
              "mainEntity": {"@type": "ItemList", "numberOfItems": len(rows), "itemListElement": [
                  {"@type": "ListItem", "position": n, "url": SEO.canonical(work_url(pkg, w)),
                   "name": "%s by %s" % (w["title"], pkg["artist"]["display_name"])} for n, (pkg, w) in enumerate(rows, 1)]}},
             {"@type": "BreadcrumbList", "@id": url + "#breadcrumbs", "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "PlotArt", "item": SEO.ORIGIN},
                 {"@type": "ListItem", "position": 2, "name": "Artworks", "item": url}]}]
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return '<script type="application/ld+json">%s</script>' % data


def collection(packages):
    rows = collection_order(packages)
    if not rows:
        return ('<p class="pa-coll-count">No artworks are available just now.</p>'
                '<p class="pa-coll-empty">New work is published as artists add it. <a href="../gallery/">Meet the artists in the Artists’ Gallery</a>.</p>'
                + collection_data(rows))
    artists = len({pkg["artist"]["slug"] for pkg, _ in rows})
    return ('<p class="pa-coll-count">%d original %s by %d %s</p>'
            '\n  <ol class="pa-coll-grid" aria-label="Available artworks">%s\n  </ol>\n  %s') % (
        len(rows), "work" if len(rows) == 1 else "works", artists, "artist" if artists == 1 else "artists",
        "".join(collection_card(pkg, w, n) for n, (pkg, w) in enumerate(rows, 1)), collection_data(rows))


def content(path, packages):
    if path == "artworks/index.html":
        return collection(packages)
    if path == "buy-original-art-ireland.html":
        rows = available(packages)
        if not rows:
            return '<p>No available works are currently published. <a href="gallery/">Visit the artist galleries</a> for the latest collection.</p>'
        body = "".join('<tr><td><a href="artists/%s/">%s</a></td><th scope="row"><a href="%s">%s</a></th><td>%s</td></tr>' % (
            E(pkg["artist"]["slug"]), E(pkg["artist"]["display_name"]), E(work_url(pkg, w)), E(w["title"]), E(P.price_line(w)))
            for pkg, w in rows)
        return ('<p>These are the artist-supplied asking prices for works currently marked available in PlotArt. '
                'They describe this collection, rather than a market-wide price range. Confirm availability and the total cost with the artist before buying.</p>'
                '<div class="pa-guide-table" role="region" aria-label="Current artwork prices" tabindex="0">'
                '<table><caption>Available works and published prices</caption><thead><tr><th scope="col">Artist</th>'
                '<th scope="col">Artwork</th><th scope="col">Asking price</th></tr></thead><tbody>%s</tbody></table></div>'
                '<p class="pa-guide-note">A published price does not by itself confirm whether framing, VAT, delivery or installation is included. '
                'Ask the artist to confirm what applies to the particular work.</p>') % body
    if path != "abstract-contemporary-art-ireland.html":
        raise ValueError("Unknown buyer guide")
    rows = available(packages, abstract=True)[:3]
    if not rows:
        return '<p>No available works are currently featured in this selection. <a href="gallery/">Explore the artist galleries</a> for the latest work.</p>'
    cards = []
    for pkg, w in rows:
        im = P.main_image(w)
        d = P.pick(im, 1200)
        prefix = "artists/%s/img/" % pkg["artist"]["slug"]
        credit = " · Photograph: " + E(im["photo_credit"]) if im.get("photo_credit") else ""
        cards.append('<li><a class="pa-guide-art" href="%s"><img src="%s" srcset="%s" sizes="(max-width:700px) 90vw, 380px" '
                     'width="%d" height="%d" alt="%s" loading="lazy" decoding="async"></a>'
                     '<h3><a href="%s">%s</a></h3><p><a href="artists/%s/">%s</a>%s</p><p>%s · %s</p><p>%s</p></li>' % (
                         E(work_url(pkg, w)), E(prefix + d["file"]), E(P.srcset(im, prefix)), d["pixels"][0], d["pixels"][1], E(im["alt"]),
                         E(work_url(pkg, w)), E(w["title"]), E(pkg["artist"]["slug"]), E(pkg["artist"]["display_name"]), credit,
                         E(w["medium"]), E(P.size_line(w)[0]), E(P.price_line(w))))
    return ('<p>A selection from the available abstract and contemporary work published on PlotArt. '
            'Each link opens the artist-supplied details, dimensions, price and enquiry route.</p>'
            '<ul class="pa-guide-works">%s</ul><p><a class="pa-btn pa-btn--ghost" href="gallery/">Explore all artist galleries →</a></p>') % "".join(cards)


def update(document, path, packages):
    if document.count(BEGIN) != 1 or document.count(END) != 1 or not REGION.search(document):
        raise ValueError("Missing or duplicate buyer-guide collection region")
    return REGION.sub(lambda m: BEGIN + "\n" + content(path, packages) + "\n" + END, document, count=1)


def outside(document):
    if document.count(BEGIN) != 1 or document.count(END) != 1 or not REGION.search(document):
        raise ValueError("Missing or duplicate buyer-guide collection region")
    return REGION.sub(BEGIN + "<!-- collection -->" + END, document, count=1)


def refresh(root, packages):
    for path in SEO.GENERATED_PATHS:
        dest = Path(root) / "plotart" / path
        if dest.exists():
            dest.write_text(update(dest.read_text(), path, packages))
