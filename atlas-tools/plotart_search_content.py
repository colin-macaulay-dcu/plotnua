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


LARGE_CM = 100   # Large artworks (SEO buyer-intent Phase 2, 13 Nov 2026): at least this on the longest side


def is_large(w):
    """Computed from the artist's published height and width only (depth is not a side of the picture plane)."""
    return max(float(w.get("h_cm") or 0), float(w.get("w_cm") or 0)) >= LARGE_CM


# One spec per generated collection page. Each lists only published, available works that pass its test; everything
# else (cards, order, structured data) is shared, so both pages stay one system.
COLLECTIONS = {
    "artworks/index.html": {"keep": lambda w: True, "name": "Original Irish art for sale",
                            "crumbs": [("Artworks", "artworks/index.html")], "label": "Available artworks",
                            "count": "original %s", "empty": "No artworks are available just now.",
                            "refine": True},   # the Refine line (founder approval 21 Nov 2026): All Artworks only
    "large-artworks/index.html": {"keep": is_large, "name": "Large original artworks for sale in Ireland",
                                  "crumbs": [("Artworks", "artworks/index.html"), ("Large artworks", "large-artworks/index.html")],
                                  "label": "Available large artworks", "count": "original %s of 100 cm or more",
                                  "empty": "No large artworks are available just now."},
}


# Collection artist order (16 Nov 2026). The artwork collections list artists in the order their galleries were FIRST
# published, so routine republishing (opportunity selections, biography edits, new versions of any kind) never moves an
# artist. publication.approved_at is NOT used: it is the date of the latest approved version and changes on every
# republish (that is what reordered All Artworks and Large Artworks on 16 Nov 2026). The public export carries no
# first-publication date, so the order of the artists published so far is recorded here, taken from the repository
# history (the commit that first added each plotart/artists/<slug>/gallery.json). It is append-only: add each newly
# published artist at the END, in the position the fallback below already gives them, so adding them moves nothing.
# This order is used ONLY by the artwork collections; the Artists' Gallery keeps its own order (P.gallery_order and the
# founder's Studio gallery positions) and is not affected.
COLLECTION_ARTIST_ORDER = (
    "leah-hewson",           # first published 5 Nov 2026
    "ciaran-mccoy",          # 10 Nov 2026
    "mark-kavanagh-rasher",  # 10 Nov 2026
    "daniel-chester",        # 11 Nov 2026
    "anna-marie-savage",     # 12 Nov 2026
    "fintan-whelan",         # 12 Nov 2026
    "nessa-mccormack",       # 12 Nov 2026
    "karen-ebbs",            # 12 Nov 2026
    "lena-fawaz",            # 17 Nov 2026 (recorded in the order both collections already show)
    "sarah-fitzgibbon",      # 17 Nov 2026
)


def collection_artists(packages):
    """Artists in stable collection order. Recorded artists first, in COLLECTION_ARTIST_ORDER. Any artist not yet
    recorded follows them, by when the founder FIRST approved their gallery (publication.first_approved_at: the Studio's
    version 1, which never changes), then by slug, so a new artist has a predictable place that nothing routine moves.

    A12 correction (17 Nov 2026): this used to be licence_accepted_at, but the Studio exports the artist's NEWEST licence
    acceptance, so any re-acceptance (a new licence version, or the Gallery Artist agreement) could move a new artist
    among the others. It passed for Lena Fawaz and Sarah Fitzgibbon only because their alphabetical order matched their
    acceptance order; Olivia Jones's first publication was the first case where it did not, and the gate refused it.
    Galleries exported before first_approved_at existed fall back to licence_accepted_at until they are next published."""
    rank = {s: i for i, s in enumerate(COLLECTION_ARTIST_ORDER)}

    def key(p):
        slug, pub = p["artist"]["slug"], p["publication"]
        if slug in rank:
            return (0, rank[slug], "", slug)
        return (1, 0, pub.get("first_approved_at") or pub.get("licence_accepted_at") or "9999", slug)
    return sorted(packages, key=key)


def collection_order(packages, keep=lambda w: True):
    """Every published, available work for the artwork collection, in a fair, stable order: the artists in stable
    collection order (collection_artists: first publication, never the latest approval date), then one work from each
    artist in turn (each artist's own work order kept), so no single gallery fills the top of the page. Reserved, sold,
    not-for-sale and withdrawn works never appear."""
    queues = []
    for pkg in collection_artists(list(packages)):
        if pkg["publication"].get("state") != "approved":
            raise ValueError("Collection input is not an approved public gallery")
        ws = [w for w in pkg["works"] if w["availability"] == "available" and keep(w)]
        if ws:
            queues.append([(pkg, w) for w in ws])
    out = []
    while any(queues):
        for q in queues:
            if q:
                out.append(q.pop(0))
    return out


def public_county(a):
    """The artist's county ONLY as the artist chose to show it publicly (the Studio publishes it only with their choice;
    blank means not shown). Never the artwork's location, which is private Studio data and is not published."""
    return (a.get("county") or "").strip()


def refine_attrs(pkg, w):
    """Refine (founder approval 21 Nov 2026): the values the All Artworks filters read, taken only from the same
    approved public gallery export the card itself is built from. Nothing new is collected or published: the price,
    the longest side and the artist are already printed on the card, and the county already shows on the artist's
    gallery. data-work is the artwork's id, matched against the live Art for Hire check only in the browser."""
    a = pkg["artist"]
    price = "request" if w.get("price_on_request") or w.get("price_eur") is None else "%d" % int(w["price_eur"])
    longest = max(float(w.get("h_cm") or 0), float(w.get("w_cm") or 0))   # as is_large: the picture plane only
    county = public_county(a)
    return ' data-price="%s" data-long="%s" data-artist="%s" data-work="%s"%s' % (
        price, E("%g" % longest), E(a["slug"]), E(w["id"]), ' data-county="%s"' % E(county) if county else "")


def collection_card(pkg, w, n, refine=False):
    """One work in the collection: the artist-approved image, uncropped, linking to its canonical artwork page."""
    a = pkg["artist"]
    im = P.main_image(w)
    d = P.pick(im, 1200)
    prefix = "../artists/%s/img/" % a["slug"]
    url = "../" + work_url(pkg, w)
    eager = n <= 3
    credit = '<p class="pa-coll-credit">Photograph: %s</p>' % E(im["photo_credit"]) if im.get("photo_credit") else ""
    return ('\n    <li class="pa-coll-work"' + (refine_attrs(pkg, w) if refine else "") + '><a class="pa-coll-art" href="%s">'
            '<img src="%s" srcset="%s" sizes="(max-width:639px) 92vw, (max-width:1099px) 46vw, 31vw" width="%d" height="%d" alt="%s"%s decoding="async"></a>'
            '<div class="pa-coll-label"><h3 class="pa-coll-title"><a href="%s">%s</a></h3>'
            '<p class="pa-coll-artist"><a href="../artists/%s/">%s</a></p>'
            '<p class="pa-coll-meta">%s<span aria-hidden="true"> · </span><span class="pa-coll-size">%s</span></p>'
            '<p class="pa-coll-price">%s</p>%s</div></li>') % (
        E(url), E(prefix + d["file"]), E(P.srcset(im, prefix)), d["pixels"][0], d["pixels"][1], E(im["alt"]),
        ' fetchpriority="high"' if n == 1 else ("" if eager else ' loading="lazy"'),
        E(url), E(w["title"]), E(a["slug"]), E(a["display_name"]), E(w["medium"]), E(P.size_line(w)[0]), E(P.price_line(w)), credit)


def collection_data(rows, path="artworks/index.html"):
    """CollectionPage + ItemList (each item: the canonical artwork page) + BreadcrumbList. Describes the collection;
    makes no merchant, offer or availability claim."""
    spec = COLLECTIONS[path]
    url = SEO.canonical(path)
    crumbs = [("PlotArt", SEO.ORIGIN)] + [(n, SEO.canonical(p)) for n, p in spec["crumbs"]]
    graph = [{"@type": "CollectionPage", "@id": url + "#page", "url": url, "name": spec["name"],
              "isPartOf": {"@type": "WebSite", "name": "PlotArt", "url": SEO.ORIGIN},
              "breadcrumb": {"@id": url + "#breadcrumbs"},
              "mainEntity": {"@type": "ItemList", "numberOfItems": len(rows), "itemListElement": [
                  {"@type": "ListItem", "position": n, "url": SEO.canonical(work_url(pkg, w)),
                   "name": "%s by %s" % (w["title"], pkg["artist"]["display_name"])} for n, (pkg, w) in enumerate(rows, 1)]}},
             {"@type": "BreadcrumbList", "@id": url + "#breadcrumbs", "itemListElement": [
                 {"@type": "ListItem", "position": n, "name": name, "item": href} for n, (name, href) in enumerate(crumbs, 1)]}]
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return '<script type="application/ld+json">%s</script>' % data


def collection(packages, path="artworks/index.html"):
    spec = COLLECTIONS[path]
    rows = collection_order(packages, spec["keep"])
    if not rows:
        return ('<p class="pa-coll-count">%s</p>'
                '<p class="pa-coll-empty">New work is published as artists add it. <a href="../gallery/">Meet the artists in the Artists’ Gallery</a>.</p>'
                % spec["empty"] + collection_data(rows, path))
    artists = len({pkg["artist"]["slug"] for pkg, _ in rows})
    refine = spec.get("refine") is True
    return ('<p class="pa-coll-count"%s>%d %s by %d %s</p>%s'
            '\n  <ol class="pa-coll-grid" aria-label="%s">%s\n  </ol>%s\n  %s') % (
        ' data-rf-count aria-live="polite"' if refine else "",
        len(rows), spec["count"] % ("work" if len(rows) == 1 else "works"), artists, "artist" if artists == 1 else "artists",
        refine_bar(rows) if refine else "",
        spec["label"], "".join(collection_card(pkg, w, n, refine) for n, (pkg, w) in enumerate(rows, 1)),
        '\n  <p class="pa-rf-none" data-rf-none hidden>No works match these choices. '
        '<button type="button" class="pa-rf-clear" data-rf-clear>Clear the filters</button></p>' if refine else "",
        collection_data(rows, path))


# ---- Refine (founder approval 21 Nov 2026): the All Artworks filters --------------------------------------------------
# Fixed price and size bands (half-open, so a work is in exactly one band; 100 cm starts "Large", as LARGE_CM). The
# artist and location choices list only what the collection holds right now, so a choice never leads to nothing.
REFINE_PRICE = [("0-1000", "Under €1,000"), ("1000-2500", "€1,000 – €2,499"), ("2500-5000", "€2,500 – €4,999"),
                ("5000-10000", "€5,000 – €9,999"), ("10000-", "€10,000 and over")]
REFINE_SIZE = [("0-50", "Up to 49 cm"), ("50-100", "50 – 99 cm"), ("100-150", "100 – 149 cm"), ("150-", "150 cm and over")]
CHEVRON = '<svg viewBox="0 0 12 8" aria-hidden="true" focusable="false"><path d="M1 1.5l5 5 5-5" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>'


def _refine_group(key, name, options, note=""):
    items = "".join('<label class="pa-rf-opt"><input type="checkbox" name="%s" value="%s"><span>%s</span></label>' % (key, E(v), E(t))
                    for v, t in options)
    return ('<div class="pa-rf-group" data-rf-group="%s"><button type="button" class="pa-rf-trig" aria-expanded="false" '
            'aria-controls="rf-%s"><span class="pa-rf-name">%s</span><span class="pa-rf-val" data-rf-val></span>%s</button>'
            '<fieldset class="pa-rf-pop" id="rf-%s" hidden><legend class="pa-sr">%s</legend>%s%s</fieldset></div>') % (
        key, key, E(name), CHEVRON, key, E(name), items, '<p class="pa-rf-note">%s</p>' % E(note) if note else "")


def refine_bar(rows):
    """The Refine line. It ships HIDDEN: only plotart-refine.js shows it, so without the script (or if it fails) the
    page is exactly the full collection. "Available to hire" ships hidden too and is shown only while the live,
    fail-closed Art for Hire check names works on this page; it is never decided from this static page."""
    artists = sorted({(p["artist"]["slug"], p["artist"]["display_name"]) for p, _ in rows},
                     key=lambda x: (x[1].split()[-1].casefold(), x[1].casefold(), x[0]))
    counties = sorted({public_county(p["artist"]) for p, _ in rows} - {""}, key=str.casefold)
    groups = (_refine_group("price", "Price", REFINE_PRICE, "Works with the price on request are shown only when no price is chosen.")
              + _refine_group("size", "Size", REFINE_SIZE, "Longest side, from the artist’s own measurements.")
              + _refine_group("artist", "Artist", artists))
    if counties:
        groups += _refine_group("county", "Artist location", [(c, "Co. " + c) for c in counties],
                                "Shown only for artists who have chosen to share their county.")
    return ('\n<div class="pa-rf" data-rf hidden>'
            '<div class="pa-rf-line"><span class="pa-rf-label" aria-hidden="true">Refine</span>'
            '<button type="button" class="pa-rf-open" aria-expanded="false" aria-controls="rf-sheet">Refine<span class="pa-rf-badge" data-rf-badge></span></button>'
            '<div class="pa-rf-sheet" id="rf-sheet" role="group" aria-label="Refine the collection">'
            '<div class="pa-rf-sheet-h"><p class="pa-rf-sheet-t" tabindex="-1">Refine</p>'
            '<button type="button" class="pa-rf-x" data-rf-close aria-label="Close"><span aria-hidden="true">×</span></button></div>'
            + groups +
            '<div class="pa-rf-group pa-rf-hire" data-rf-hire hidden><label class="pa-rf-opt"><input type="checkbox" name="hire" value="1">'
            '<span>Available to hire</span></label></div>'
            '<div class="pa-rf-sheet-f"><button type="button" class="pa-rf-clear" data-rf-clear>Clear</button>'
            '<button type="button" class="pa-btn pa-btn--solid pa-rf-show" data-rf-close><span>Show <span data-rf-n>%d</span> <span data-rf-word>%s</span></span></button></div>'
            '</div>'
            '<button type="button" class="pa-rf-clear pa-rf-clear--line" data-rf-clear hidden>Clear</button>'
            '</div></div>') % (len(rows), "work" if len(rows) == 1 else "works")


def content(path, packages):
    if path in COLLECTIONS:
        return collection(packages, path)
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
