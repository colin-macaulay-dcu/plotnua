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
# Editorial classification, based on each artist's own published statement or practice line. New artists are never
# auto-classified. Leah Hewson ("abstract language", 5 Nov 2026). Widened 26 Nov 2026 (SEO and analytics package,
# section 2.3, founder approval) to the artists who describe themselves as abstract painters or artists in their own
# published words: Anna Marie Savage ("abstract painter"), Carmel Marrinan ("Abstract Expressionist artist"), Clare
# O'Connor ("Abstract Painter"), Fintan Whelan ("Irish abstract artist"), Karen Ebbs ("Abstract painting and colour are
# central to my practice"), Lena Fawaz ("emerging abstract artist"), Naomi Taitz Duffy ("abstract painter ... geometric
# abstraction"), Nessa McCormack ("I am an abstract painter") and Olivia Jones ("hard-edge geometric abstraction").
# Artists who describe a mix (abstraction and representation, abstraction and pop art, abstract painting and
# photography) are left out.
ABSTRACT_ARTISTS = frozenset({"leah-hewson", "anna-marie-savage", "carmel-marrinan", "clare-o-connor", "fintan-whelan", "karen-ebbs",
                              "lena-fawaz", "naomi-taitz-duffy", "nessa-mccormack", "olivia-jones"})
ABSTRACT_SHOWN = 16      # the abstract page's curated grid: up to this many available works, one artist at a time
# Section 2.6: the abstract page links to these artists' galleries ("[artist]'s abstract work") while they are published
ABSTRACT_LINKED = ("karen-ebbs", "clare-o-connor", "naomi-taitz-duffy", "fintan-whelan")
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


# Original art under €500 (growth package, 27 Nov 2026): every published, AVAILABLE work with a public asking price
# (never "price on request") below this, computed from the artist's own published price at every publication.
UNDER_EUR = 500
UNDER_LABEL = "€500"      # the threshold as the page writes it (P.euro(UNDER_EUR)); the only fixed figure on that page


def is_under(w):
    return bool(w.get("price_eur")) and not w.get("price_on_request") and float(w["price_eur"]) < UNDER_EUR


# Landscape paintings (growth package, 27 Nov 2026). CURATED, NOT COMPUTED: the gallery exports carry no subject field, so
# PlotArt decided each available work by reading its title, the artist's description and alt text, the artist's own
# statement and the image (classification record: 13-landscape-classification.md, 27 Nov 2026). A work is here only if it
# presents a landscape, seascape/coast or a particular place; abstract works whose titles merely mention nature are left
# out. NEEDS REVIEW whenever works are published or changed: a new work is never added automatically, and a listed work
# that is sold or withdrawn simply drops off the page. Keyed by artwork id (stable across title and slug edits).
LANDSCAPE_WORKS = frozenset({
    "wlmcbkhe75h",  # Carmel Marrinan: Over the river (alt text: "Abstract landscape"; a stylised river landscape)
    "wh4ve2xmvb1",  # Carolyn Walsh: Coastal Series 8 (coastal scene; her bio: "inspired by the Irish landscape, coastal settings")
    "w579di55chn",  # Carolyn Walsh: Coastal series 6
    "w32zmc2ceav",  # Carolyn Walsh: Coastal Series 4
    "wrbk7q2jeq1",  # Carolyn Walsh: Coastal Series 5
    "w33b6qij369",  # Carolyn Walsh: Coastal Series 7
    "wychp9cm2em",  # Daniel Chester: Forest Fest (a wild bank in Leitrim; statement: "Painter of landscapes")
    "wfhtcyurvgf",  # Daniel Chester: Foxgloves and Gorse (a wild area at the end of the artist's road)
    "w98mfl2ia7g",  # Daniel Chester: The Crossing (marshland and river in Sligo town)
    "w8cfo8lh75j",  # Louise Shearer: A Room with a View (alt text: "Abstracted view of an Irish landscape")
    "w64kalb4h7x",  # Louise Shearer: Be Here Now (description: "Abstracted landscape")
})


def is_landscape(w):
    return w["id"] in LANDSCAPE_WORKS


def _price_key(row):
    return float(row[1]["price_eur"])


def _plural(n, one, many):
    return "%d %s" % (n, one if n == 1 else many)


def under_note(rows):
    """What the selection holds, by kind of work, from the artist's own medium wording (P.artwork_kind). Prints are named
    separately so nobody mistakes an editioned print for a one-off painting."""
    kinds = [P.artwork_kind(w["medium"]) for _, w in rows]
    parts = [_plural(kinds.count(k), one, many) for k, one, many in (("Painting", "painting", "paintings"), ("Mixed Media", "mixed-media work", "mixed-media works"),
                                                                    ("Drawing", "drawing", "drawings"), ("Print", "original print", "original prints")) if kinds.count(k)]
    other = sum(1 for k in kinds if k is None)
    if other:
        parts.append(_plural(other, "other work", "other works"))
    text = "This selection holds %s." % (parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]) if parts else ""
    if "Print" in kinds:
        text += (" An original print is made by the artist through a printmaking process: a monoprint is one of a kind, while a screen "
                 "print or etching may be one of a small edition. The artwork page gives the artist’s own details.")
    return '<p class="pa-coll-note">%s</p>' % E(text) if text else ""


def size_note(rows):
    """The range of sizes in the selection, from the artist's published height and width (longest side)."""
    sides = sorted(max(float(w.get("h_cm") or 0), float(w.get("w_cm") or 0)) for _, w in rows)
    if not sides:
        return ""
    span = ("%g cm" % sides[0]) if sides[0] == sides[-1] else ("%g cm to %g cm" % (sides[0], sides[-1]))
    return '<p class="pa-coll-note">Longest side, from the artist’s own measurements: %s.</p>' % E(span)


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
    # growth package (27 Nov 2026): lowest price first (ties keep the fair collection order); the note names the prints
    "original-art-under-500/index.html": {"keep": is_under, "name": "Original art under €500",
                                          "crumbs": [("Artworks", "artworks/index.html"), ("Original art under €500", "original-art-under-500/index.html")],
                                          "label": "Available original artworks under €500", "count": "original %s under €500",
                                          "empty": "No original works under €500 are available just now.",
                                          "sort": _price_key, "note": under_note},
    "landscape-paintings-ireland/index.html": {"keep": is_landscape, "name": "Landscape paintings for sale in Ireland",
                                               "crumbs": [("Artworks", "artworks/index.html"), ("Landscape paintings", "landscape-paintings-ireland/index.html")],
                                               "label": "Available landscape, coastal and place-based works", "count": "landscape, coastal and place-based %s",
                                               "empty": "No landscape works are available just now.", "note": size_note},
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
    if spec.get("sort"):
        rows = sorted(rows, key=spec["sort"])     # stable: equal keys keep the fair collection order
    if not rows:
        return ('<p class="pa-coll-count">%s</p>'
                '<p class="pa-coll-empty">New work is published as artists add it. <a href="../gallery/">Meet the artists in the Artists’ Gallery</a>.</p>'
                % spec["empty"] + collection_data(rows, path))
    artists = len({pkg["artist"]["slug"] for pkg, _ in rows})
    refine = spec.get("refine") is True
    return ('<p class="pa-coll-count"%s>%d %s by %d %s</p>%s%s'
            '\n  <ol class="pa-coll-grid" aria-label="%s">%s\n  </ol>%s\n  %s') % (
        ' data-rf-count aria-live="polite"' if refine else "",
        len(rows), spec["count"] % ("work" if len(rows) == 1 else "works"), artists, "artist" if artists == 1 else "artists",
        spec["note"](rows) if spec.get("note") else "",
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


# ---------------------------------------------------------------------------------------------------------------------
# Commercial Conversion Sprint 1 (founder approval 26 Nov 2026)
# The homepage availability line: three figures, all from published, AVAILABLE works only (reserved, sold and not-for-sale
# never count). "Artists" is said, never "Irish artists": nationality is not recorded. "Available", never "for sale
# online": which works can be bought online is decided live by the checkout, not here. No line when nothing is available.
def priced(w):
    """A work with a public asking price (not 'price on request')."""
    return bool(w.get("price_eur")) and not w.get("price_on_request")


def home_figures(packages):
    rows = available(packages)
    prices = [w["price_eur"] for _, w in rows if priced(w)]   # the published values themselves (euro() formats them)
    return len(rows), len({pkg["artist"]["slug"] for pkg, _ in rows}), (min(prices) if prices else None)


def home_line(packages):
    works, artists, low = home_figures(packages)
    if not works:
        return ""
    text = "%d original %s by %d %s" % (works, "work" if works == 1 else "works", artists, "artist" if artists == 1 else "artists")
    if low is not None:
        text += ", from " + P.euro(low)
    return ('<p class="pa-gx-avail">%s <span aria-hidden="true">·</span> <a href="artworks/" data-pa-track="home_browse_artworks">'
            'Browse available artworks<span aria-hidden="true"> →</span></a></p>') % E(text)


# Price-band recommendations for the buying guides: one available, publicly priced work per band, in the artwork
# collection's own fair order (collection_order), never two from the same artist. A band with no such work is left out.
PRICE_BANDS = ((0, 500, "Under €500"), (500, 1500, "€500 to €1,500"), (1500, 5000, "€1,500 to €5,000"), (5000, None, "€5,000 and over"))


def band_picks(packages):
    rows, used, out = collection_order(packages), set(), []   # noqa
    for lo, hi, label in PRICE_BANDS:
        for pkg, w in rows:
            if not priced(w) or pkg["artist"]["slug"] in used:
                continue
            p = float(w["price_eur"])
            if p >= lo and (hi is None or p < hi):
                out.append((label, pkg, w))
                used.add(pkg["artist"]["slug"])
                break
    return out


def band_row(packages, prefix=""):
    picks = band_picks(packages)
    if not picks:
        return ""
    cards = []
    for label, pkg, w in picks:
        im = P.main_image(w)
        d = P.pick(im, 1200)
        img = prefix + "artists/%s/img/" % pkg["artist"]["slug"]
        url = prefix + work_url(pkg, w)
        cards.append('<li><a class="pa-band-art" href="%s"><img src="%s" srcset="%s" sizes="(max-width:700px) 44vw, 240px" width="%d" height="%d" '
                     'alt="%s" loading="lazy" decoding="async"></a><p class="pa-band-label">%s</p><p class="pa-band-t"><a href="%s">%s</a></p>'
                     '<p class="pa-band-m">%s · %s</p></li>' % (
                         E(url), E(img + d["file"]), E(P.srcset(im, img)), d["pixels"][0], d["pixels"][1], E(im["alt"]), E(label),
                         E(url), E(w["title"]), E(pkg["artist"]["display_name"]), E(P.price_line(w))))
    return ('<div class="pa-band" aria-labelledby="bandH"><h2 class="pa-band-h" id="bandH">Available now, by price</h2>'
            '<ul class="pa-band-list">%s</ul><p class="pa-band-more"><a href="%sartworks/">See all available artworks<span aria-hidden="true"> →</span></a></p></div>') % (
                "".join(cards), E(prefix))


def content(path, packages):
    if path in SEO.HOME_PATHS:
        return home_line(packages)
    if path in SEO.RECOMMEND_PATHS:
        return band_row(packages)
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
    # the curated grid: available works by the artists above, one from each in turn (the collection's own fair order)
    rows = collection_order([p for p in packages if p["artist"]["slug"] in ABSTRACT_ARTISTS])[:ABSTRACT_SHOWN]
    by_slug = {p["artist"]["slug"]: p for p in packages}
    linked = ['<a href="artists/%s/">%s’s abstract work</a>' % (E(sl), E(by_slug[sl]["artist"]["display_name"])) for sl in ABSTRACT_LINKED if sl in by_slug]
    further = ('<p>Go further into %s, or see <a href="large-artworks/">large abstract paintings</a> among the works of 100 cm or more.</p>' % series(linked)) if linked else ""
    # Sprint 1 (26 Nov 2026): the selection stays editorial (abstract only, never auto-classified); one generated line
    # points to every available work, at every price, without calling any of it abstract.
    works, _artists, low = home_figures(packages)
    every = ('<p class="pa-band-more">Looking across every style and price? Browse <a href="artworks/">all %d available original %s</a>%s.</p>' % (
        works, "work" if works == 1 else "works", (", from " + E(P.euro(low))) if low is not None else "")) if works else ""
    if not rows:
        return '<p>No available works are currently featured in this selection. <a href="gallery/">Explore the artist galleries</a> for the latest work.</p>' + every
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
            '<ul class="pa-guide-works">%s</ul>%s<p><a class="pa-btn pa-btn--ghost" href="gallery/">Explore all artist galleries →</a></p>%s') % ("".join(cards), further, every)


# ---------------------------------------------------------------------------------------------------------------------
# Search titles and descriptions of the generated pages (SEO and analytics package, founder approval 26 Nov 2026, section
# 2.4). Every figure (works, artists, lowest and highest price, large-work counts) is computed here from the published
# galleries, never typed in, and refreshed with the collection region at every publication (update()), so it never goes
# stale; outside() leaves the descriptions out of the manifest pin, and update() == page (guard L3, the boundary) pins them.
# They say "enquire", never "buy online": whether a work can be bought online is decided live by the checkout.
LIVING_TITLE = "How to Choose Art for Your Living Room | PlotArt"
LIVING_DESCRIPTION = ("Choose living-room art with confidence: sofa proportions in centimetres, colour, placement, light and framing. "
                      "Includes a free printable art-buying checklist.")
KIND_PLURAL = (("Painting", "paintings"), ("Print", "prints"), ("Mixed Media", "mixed-media works"), ("Drawing", "drawings"))


def plural(n, one, many):
    return "%d %s" % (n, one if n == 1 else many)


def series(words):
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def figures(packages):
    """The published, available collection in numbers: works, artists, lowest and highest public asking price, the kinds
    of work, and the large works (100 cm or more on the longest side) with their artists and how many are 150 cm or more."""
    rows = available(packages)
    prices = [w["price_eur"] for _, w in rows if priced(w)]
    large = [(p, w) for p, w in rows if is_large(w)]
    kinds = {P.artwork_kind(w["medium"]) for _, w in rows}
    return {"works": len(rows), "artists": len({p["artist"]["slug"] for p, _ in rows}),
            "low": min(prices) if prices else None, "high": max(prices) if prices else None,
            "kinds": [many for one, many in KIND_PLURAL if one in kinds],
            "large": len(large), "large_artists": len({p["artist"]["slug"] for p, _ in large}),
            "large_150": sum(1 for _, w in large if max(float(w.get("h_cm") or 0), float(w.get("w_cm") or 0)) >= 150),
            "under": _subset(rows, is_under), "landscape": _subset(rows, is_landscape)}


def _subset(rows, keep):
    """(works, artists, lowest public price) of the available works that pass keep."""
    sub = [(p, w) for p, w in rows if keep(w)]
    prices = [w["price_eur"] for _, w in sub if priced(w)]
    return len(sub), len({p["artist"]["slug"] for p, _ in sub}), (min(prices) if prices else None)


def _home(f):
    if not f["works"]:
        return "Original Irish art online: a gallery of original work, each shown with its size and price. Enquire with the artist directly."
    return ("Original Irish art online: %s by %s%s, each shown with its size and price. Enquire with the artist directly." % (
        plural(f["works"], "available work", "available works"), plural(f["artists"], "artist", "artists"),
        (" from " + P.euro(f["low"])) if f["low"] is not None else ""))


def _artworks(f):
    if not f["works"]:
        return "Original paintings, prints and mixed-media works for sale in Ireland. See each size and price and enquire with the artist."
    span = (", from %s to %s" % (P.euro(f["low"]), P.euro(f["high"]))) if f["low"] is not None and f["high"] != f["low"] else \
        (", at %s" % P.euro(f["low"]) if f["low"] is not None else "")
    return "%d original %s by %s, for sale in Ireland%s. Enquire with the artist." % (
        f["works"], series(f["kinds"] or ["works"]), plural(f["artists"], "artist", "artists"), span)


def _large(f):
    if not f["large"]:
        return "Large original works of 100 cm or more for sale in Ireland. See each size and price, and enquire with the artist."
    over = (", %d of them 150 cm and over" % f["large_150"]) if f["large_150"] else ""
    return "%d original %s of 100 cm or more by %s%s. See each size and price, and enquire with the artist." % (
        f["large"], "work" if f["large"] == 1 else "works", plural(f["large_artists"], "artist", "artists"), over)


def _under(f):
    works, artists, low = f["under"]
    if not works:
        return "Original art under €500 by artists based or working in Ireland. See each size and price, and enquire with the artist."
    return "%s under €500 by %s based or working in Ireland, from %s. See sizes and prices, and enquire with the artist." % (
        plural(works, "original work", "original works"), plural(artists, "artist", "artists"), P.euro(low))


def _landscape(f):
    works, artists, low = f["landscape"]
    if not works:
        return "Landscape, coastal and place-based paintings by artists based or working in Ireland. Enquire with the artist."
    return "%s of landscape, coast and place by %s based or working in Ireland%s. See sizes and prices; enquire with the artist." % (
        plural(works, "original work", "original works"), plural(artists, "artist", "artists"), (", from " + P.euro(low)) if low is not None else "")


def _buy(f):
    tail = (" See live prices from %s." % P.euro(f["low"])) if f["low"] is not None else " See the live artwork prices."
    return "Where to buy original Irish art, what it costs, and what to ask about framing, VAT and delivery before you buy." + tail


HUB_META = {
    "index.html": ("PlotArt | Original & Contemporary Irish Art Online", _home),
    "artworks/index.html": ("Original Irish Art for Sale | Paintings & Prints | PlotArt", _artworks),
    "large-artworks/index.html": ("Large Original Paintings for Sale in Ireland | PlotArt", _large),
    "original-art-under-500/index.html": ("Original Art Under €500 in Ireland | PlotArt", _under),
    "landscape-paintings-ireland/index.html": ("Landscape Paintings for Sale in Ireland | PlotArt", _landscape),
    "buy-original-art-ireland.html": ("Buy Original Art in Ireland | Prices & Guide | PlotArt", _buy),
    "abstract-contemporary-art-ireland.html": ("Abstract Art Ireland | Original Irish Abstract Art | PlotArt",
                                               lambda f: "Original Irish abstract art: paintings and prints with sizes and prices, and a short "
                                                         "guide to choosing abstract art you want to live with."),
    "choose-art-for-living-room.html": (LIVING_TITLE, lambda f: LIVING_DESCRIPTION),
}


def hub_meta(path, packages):
    """(title, description) of a generated page, from the published galleries."""
    title, desc = HUB_META[path]
    return title, desc(figures(packages))


def update(document, path, packages):
    if document.count(BEGIN) != 1 or document.count(END) != 1 or not REGION.search(document):
        raise ValueError("Missing or duplicate buyer-guide collection region")
    document = REGION.sub(lambda m: BEGIN + "\n" + content(path, packages) + "\n" + END, document, count=1)
    # a whole page (with a <head>) must carry the generated title and description; a bare region fixture has none
    return SEO.set_meta(document, *hub_meta(path, packages)) if path in HUB_META and "<head>" in document else document


def outside(document):
    """The page outside its generated parts (what the launch manifest pins): the collection region and the generated
    descriptions are blanked (update() == page, checked by guard L3 and the content boundary, pins those)."""
    if document.count(BEGIN) != 1 or document.count(END) != 1 or not REGION.search(document):
        raise ValueError("Missing or duplicate buyer-guide collection region")
    return SEO.blank_meta(REGION.sub(BEGIN + "<!-- collection -->" + END, document, count=1))


def refresh(root, packages):
    for path in SEO.GENERATED_PATHS:
        dest = Path(root) / "plotart" / path
        if dest.exists():
            dest.write_text(update(dest.read_text(), path, packages))
