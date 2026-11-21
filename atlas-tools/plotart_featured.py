"""PlotArt Artists' Gallery · Featured Artists (founder brief 17 Nov 2026, "Consolidate artist showcase into Artists'
Gallery"; reuses the homepage curation of the same day and Studio migration 0016 unchanged).

One generated region on plotart/gallery/index.html, between FEAT_BEGIN and FEAT_END, above the complete collection.
Everything else on the page stays pinned, and the collection region below (pa-vg-collection) is never touched here.

  - The founder chooses up to six ARTISTS in the Review Desk (Featured Artists), each represented by one of their published
    artworks that the founder chooses (never picked automatically), and their order. Each artist appears once.
  - The publishing pipeline receives only public identifiers (GET /api/pipeline/featured-artists: gallery address and
    artwork id) and renders the region ONLY from published galleries (plotart/artists/*/gallery.json): the chosen work must
    be shown in its published gallery (plotart_gallery_pages.shown) with a main photograph. Anything withdrawn,
    unpublished or no longer shown simply drops out (an artist whose chosen work is withdrawn drops out too: nothing else
    is substituted), so the region can never show what the published galleries do not.
  - Text is the artist's own approved, published wording only: the display name, the practice line their gallery already
    shows, and a short introduction taken verbatim from the start of their published biography (whole sentences; a
    single over-long sentence is shortened at a word with an ellipsis). Nothing is written or invented here.
  - Images are the artist's own published derivatives (plotart/artists/<slug>/img/...), with their approved alt text and,
    where the artist gave one, the photo credit; nothing new is uploaded, so the existing image-rights and provenance
    records cover them. Images are never cropped (CSS: contain, natural aspect ratio).
  - Each item carries its identifiers (data-pa-featured) so the selection can be read back from the page when the Studio
    is unavailable, and so the guards can check the region is exactly what that selection renders.
  - No selection: an empty region, and the gallery page shows the complete collection only.

Earlier homepage items (kind "artwork" in migration 0016's records) arrive from the Studio already treated as the artist
they belong to; a "kind" field, if present, is accepted for either value and ignored.
"""
import html
import re

import plotart_gallery_pages as P
import plotart_search_content as C   # the All Artworks collection, so the counts below are exactly that page's

FEAT_BEGIN, FEAT_END = "<!-- pa-featured-artists:begin -->", "<!-- pa-featured-artists:end -->"
REGION = re.compile(re.escape(FEAT_BEGIN) + r".*?" + re.escape(FEAT_END), re.S)
ITEM = re.compile(r'data-pa-featured="([a-z0-9-]+):([a-z0-9]+)"')
PAGE = "gallery/index.html"           # under plotart/
BASE = "../"                         # from plotart/gallery/ to plotart/
MAX = 6
INTRO_MAX = 240                      # characters of the published biography used as the short introduction
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){0,6}$")
WORK_ID = re.compile(r"^w[0-9a-z]{4,30}$")
E = lambda s: html.escape(str(s), quote=True)
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-ɏ\"'‘“(])")


def check_selection(selection):
    """A selection is a list of {"artist": <gallery address>, "work": <artwork id>} (an optional "kind" of "artist" or
    "artwork" is accepted and ignored), at most six, each artist once."""
    if not isinstance(selection, list) or len(selection) > MAX:
        raise ValueError("the featured artists selection must be a list of at most %d items" % MAX)
    out, seen = [], set()
    for it in selection:
        if not isinstance(it, dict) or not {"artist", "work"} <= set(it) <= {"kind", "artist", "work"} \
                or it.get("kind", "artist") not in ("artist", "artwork") \
                or not isinstance(it["artist"], str) or not SLUG.match(it["artist"]) or not isinstance(it["work"], str) or not WORK_ID.match(it["work"]):
            raise ValueError("a featured artist item carries an unexpected field or value: %r" % (it,))
        if it["artist"] in seen:
            raise ValueError("an artist is featured more than once")
        seen.add(it["artist"])
        out.append({"artist": it["artist"], "work": it["work"]})
    return out


def _main(w):
    return next((i for i in w.get("images") or [] if i.get("role") == "main" and i.get("derivatives")), None)


def intro(bio):
    """The start of the artist's published biography, verbatim: whole sentences of the first paragraph up to INTRO_MAX
    characters; if the first sentence alone is longer, it is shortened at a word boundary with an ellipsis. A leading
    one-to-three-word heading line without a full stop (e.g. "Statement") is skipped. Whitespace is normalised only. No biography: no introduction (never invented)."""
    if not isinstance(bio, str) or not bio.strip():
        return ""
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", bio.strip()) if p.strip()]
    # a leading one-to-three-word line without a full stop is a heading the artist typed (e.g. "Statement"), not a sentence
    while len(paras) > 1 and len(paras[0].split()) <= 3 and not re.search(r"[.!?]$", paras[0]):
        paras.pop(0)
    para = paras[0]
    out = ""
    for s in _SENT.split(para):
        if len(out) + len(s) + (1 if out else 0) > INTRO_MAX:
            break
        out = (out + " " + s) if out else s
    if out:
        return out
    cut = para[:INTRO_MAX].rsplit(" ", 1)[0].rstrip(",;:—–- ")
    return cut + "…"


def resolve(selection, packages):
    """The artists that can be shown, in the founder's order: (package, work, main image)."""
    by = {p["artist"]["slug"]: p for p in packages}
    out = []
    for it in check_selection(selection):
        pkg = by.get(it["artist"])
        if not pkg:
            continue
        w = next((x for x in P.shown(pkg) if x.get("id") == it["work"] and _main(x)), None)
        if w:
            out.append((pkg, w, _main(w)))
    return out[:MAX]


def _item(pkg, w, im, base):
    a = pkg["artist"]
    slug = a["slug"]
    d = P.pick(im, 1200)
    gallery = "%sartists/%s/" % (base, slug)
    year = (", %s" % E(w["year"])) if w.get("year") else ""
    photo = (' · <span class="pa-fa-photo">Photo: %s</span>' % E(im["photo_credit"])) if im.get("photo_credit") else ""
    meta = P.meta_line(a)
    words = intro(a.get("bio"))
    return (
        '\n    <li class="pa-fa-item" data-pa-featured="%s:%s">'
        '<figure class="pa-fa-fig"><a class="pa-fa-art" href="%s" data-pa-track="gallery_featured_artwork">'
        '<img src="%simg/%s" srcset="%s" sizes="(max-width:639px) 92vw, (max-width:1099px) 46vw, 31vw" width="%d" height="%d" alt="%s" loading="lazy" decoding="async"></a>'
        '<figcaption class="pa-fa-credit"><a href="%s%s.html" data-pa-track="gallery_featured_work"><i>%s</i></a>%s · %s%s</figcaption></figure>'
        '<div class="pa-fa-text"><h3 class="pa-fa-name">%s</h3>%s%s'
        '<p class="pa-fa-act"><a class="pa-fa-cta" href="%s" data-pa-track="gallery_featured_artist">View Gallery <span aria-hidden="true">&rarr;</span>'
        '<span class="pa-vgc-sr"> of %s</span></a></p></div></li>') % (
        slug, w["id"],
        E(gallery),
        E(gallery), E(d["file"]), E(P.srcset(im, gallery + "img/")), d["pixels"][0], d["pixels"][1], E(im["alt"]),
        E(gallery), E(w["slug"]), E(w["title"]), year, E(a["display_name"]), photo,
        E(a["display_name"]),
        ('<p class="pa-fa-practice">%s</p>' % E(meta)) if meta else "",
        ('<p class="pa-fa-intro">%s</p>' % E(words)) if words else "",
        E(gallery), E(a["display_name"]))


def content(selection, packages, base=BASE):
    items = resolve(selection, packages)
    if not items:
        return ""
    more = browse(packages, base)
    return ('<section class="pa-sec pa-fa" aria-labelledby="featArtH"><div class="pa-wrap">\n'
            '  <div class="pa-fa-head%s"><p class="pa-eyebrow">Selected by PlotArt</p><h2 id="featArtH">Featured Artists</h2>'
            '<p class="pa-fa-lede">A changing selection of artists and their work.</p>%s</div>\n'
            '  <ol class="pa-fa-list n-%d">%s\n  </ol>\n'
            '</div></section>') % (" pa-fa-head--browse" if more else "", more, len(items), "".join(_item(p, w, im, base) for p, w, im in items))


def browse(packages, base=BASE):
    """Browse All Artworks (founder brief 21 Nov 2026): a clear way from the Featured Artists heading into the complete
    All Artworks collection and its Refine filters. The counts are taken from exactly the rows that page lists
    (plotart_search_content.collection_order with its own rule), from the same published galleries, so they always
    agree with it and change with every publication that re-renders this region. No published work: no link."""
    rows = C.collection_order(packages, C.COLLECTIONS["artworks/index.html"]["keep"])
    if not rows:
        return ""
    works, artists = len(rows), len({pkg["artist"]["slug"] for pkg, _ in rows})
    return ('<p class="pa-fa-browse"><a class="pa-btn pa-btn--ghost" href="%sartworks/" data-pa-track="gallery_browse_artworks">'
            'Browse All Artworks <span aria-hidden="true">&rarr;</span></a>'
            '<span class="pa-fa-browse-n">Explore %d original %s by %d %s.</span></p>') % (
        base, works, "work" if works == 1 else "works", artists, "artist" if artists == 1 else "artists")


def region(doc):
    m = REGION.findall(doc)
    if len(m) != 1:
        raise ValueError("the Featured Artists region is missing or repeated")
    return m[0]


def selection_in(doc):
    """The selection the page currently shows (read back from its items)."""
    return [{"artist": s, "work": w} for s, w in ITEM.findall(region(doc))]


def update(doc, selection, packages):
    region(doc)
    inner = content(selection, packages)
    return REGION.sub(lambda m: FEAT_BEGIN + ("\n" + inner + "\n" if inner else "") + FEAT_END, doc, count=1)


def outside(doc):
    """The page with the Featured Artists region emptied: what the launch guard pins (with the collection region)."""
    region(doc)
    return REGION.sub(FEAT_BEGIN + FEAT_END, doc, count=1)


def refresh(root, packages, selection=None):
    """Re-render the region from the published galleries; with no new selection, keep the founder's current one (read
    back from the page), so withdrawn or unpublished work drops out on every publication."""
    path = root / "plotart" / PAGE if hasattr(root, "__truediv__") else root + "/plotart/" + PAGE
    doc = open(path, encoding="utf-8").read()
    new = update(doc, selection_in(doc) if selection is None else selection, packages)
    if new != doc:
        open(path, "w", encoding="utf-8").write(new)
    return new != doc
