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


# Artwork first (founder brief 21 Nov 2026, "Artists' Gallery redesign, option 1"): directly under the introduction, a row of
# three published artworks, then Browse All Artworks, then Featured Artists as a second section. The three are a fixed,
# curated choice (artist gallery address, artwork id), chosen to sit well together: Night Garden (Carmel Marrinan),
# Foxgloves and Gorse (Daniel Chester) and Energetic Labyrinths 12 (Clare O'Connor). Like Featured Artists, a
# work appears only while it is shown and available in its published gallery with a main photograph, and never when the
# same artwork is featured below. A place whose work becomes ineligible is filled deterministically (opening_items).
OPENING = [("carmel-marrinan", "wg1by72jg3b"), ("daniel-chester", "wfhtcyurvgf"), ("clare-o-connor", "w226r60hfsh")]
OPEN_ITEM = re.compile(r'data-pa-opening="([a-z0-9-]+):([a-z0-9]+)"')


def _eligible(pkg, w):
    """An opening work must be shown AND available in its approved, published gallery, with a main photograph."""
    return (pkg.get("publication", {}).get("state") == "approved" and w in P.shown(pkg)
            and w.get("availability") == "available" and _main(w) is not None)


def _portrait(w):
    try:
        return float(w.get("h_cm") or 0) >= float(w.get("w_cm") or 0)
    except (TypeError, ValueError):
        return True


def opening_items(selection, packages, choice=OPENING):
    """The three opening works (founder approval 21 Nov 2026). The curated works always come first, each in its own place,
    whenever eligible. A place whose curated work is sold, withdrawn, unpublished, without a main photograph or already
    featured below is filled by a replacement chosen deterministically from the other eligible published works, so the
    opening never changes between builds unless the published galleries do. A replacement is never a featured artwork or a
    work already in the row, and is preferred, in this order: by an artist not already in the row; by an artist not in
    Featured Artists; in the same orientation as the curated work it replaces (portrait or landscape); not the work its
    artist already shows on the Explore More Artists wall; then by the All Artworks collection's own stable order."""
    by = {p["artist"]["slug"]: p for p in packages}
    sel = check_selection(selection)
    featured_works = {(x["artist"], x["work"]) for x in sel}
    featured_artists = {x["artist"] for x in sel}
    slots = []
    for slug, wid in choice:
        pkg = by.get(slug)
        w = next((x for x in pkg["works"] if x.get("id") == wid), None) if pkg else None
        ok = w is not None and _eligible(pkg, w) and (slug, wid) not in featured_works
        slots.append([(pkg, w) if ok else None, w])                 # [chosen, the curated work (for its orientation)]
    if any(s[0] is None for s in slots):
        pool = [(pkg, w) for pkg, w in C.collection_order([p for p in packages if p.get("publication", {}).get("state") == "approved"])
                if _eligible(pkg, w) and (pkg["artist"]["slug"], w["id"]) not in featured_works]
        rank = {(pkg["artist"]["slug"], w["id"]): n for n, (pkg, w) in enumerate(pool)}
        wall = {}
        for pkg in packages:
            first = P.card_image(pkg)[0] if pkg.get("works") else None
            if first:
                wall[pkg["artist"]["slug"]] = first.get("id")
        for s in slots:
            if s[0] is not None:
                continue
            used = {x[0][0]["artist"]["slug"] for x in slots if x[0] is not None}
            taken = {(x[0][0]["artist"]["slug"], x[0][1]["id"]) for x in slots if x[0] is not None}
            want_portrait = _portrait(s[1]) if s[1] is not None else True
            cands = [(pkg, w) for pkg, w in pool if (pkg["artist"]["slug"], w["id"]) not in taken]
            if not cands:
                continue
            s[0] = min(cands, key=lambda c: (c[0]["artist"]["slug"] in used, c[0]["artist"]["slug"] in featured_artists,
                                             _portrait(c[1]) != want_portrait, wall.get(c[0]["artist"]["slug"]) == c[1]["id"],
                                             rank[(c[0]["artist"]["slug"], c[1]["id"])]))
    return [(pkg, w, _main(w)) for pkg, w in (s[0] for s in slots if s[0] is not None)]


def _opening_item(pkg, w, im, base):
    a = pkg["artist"]
    slug = a["slug"]
    d = P.pick(im, 1200)
    gallery = "%sartists/%s/" % (base, slug)
    page = "%s%s.html" % (gallery, w["slug"])
    return ('\n    <li class="pa-op-item" data-pa-opening="%s:%s"><figure class="pa-op-fig">'
            '<a class="pa-op-art" href="%s" data-pa-track="gallery_opening_artwork" tabindex="-1" aria-hidden="true">'
            '<img src="%simg/%s" srcset="%s" sizes="(max-width:639px) 78vw, 31vw" width="%d" height="%d" alt="%s" decoding="async"></a>'
            '<figcaption class="pa-op-cap"><a class="pa-op-title" href="%s" data-pa-track="gallery_opening_work">%s</a>'
            '<a class="pa-op-artist" href="%s" data-pa-track="gallery_opening_artist">%s</a></figcaption></figure></li>') % (
        slug, w["id"], E(page), E(gallery), E(d["file"]), E(P.srcset(im, gallery + "img/")), d["pixels"][0], d["pixels"][1],
        E(im["alt"]), E(page), E(w["title"]), E(gallery), E(a["display_name"]))


def opening(selection, packages, base=BASE):
    # Browse All Artworks moved beside the heading (founder visual refinements 21 Nov 2026), so the row stands alone
    items = opening_items(selection, packages)
    if not items:
        return ""
    # tabindex: on phones and tablets the row scrolls sideways; as a focusable region keyboard users can move it with the
    # arrow keys (and every title and artist is a link in the tab order)
    row = '\n  <ol class="pa-op-row n-%d" aria-label="Selected artworks" tabindex="0">%s\n  </ol>' % (
        len(items), "".join(_opening_item(p, w, im, base) for p, w, im in items))
    return '<section class="pa-op" aria-label="Selected artworks"><div class="pa-wrap">%s\n</div></section>' % row


def content(selection, packages, base=BASE):
    items = resolve(selection, packages)
    first = opening(selection, packages, base)
    feat = ('<section class="pa-sec pa-fa" aria-labelledby="featArtH"><div class="pa-wrap">\n'
            '  <div class="pa-fa-head"><p class="pa-eyebrow">Selected by PlotArt</p><h2 id="featArtH">Featured Artists</h2>'
            '<p class="pa-fa-lede">A changing selection of artists and their work.</p></div>\n'
            '  <ol class="pa-fa-list n-%d">%s\n  </ol>\n'
            '</div></section>') % (len(items), "".join(_item(p, w, im, base) for p, w, im in items)) if items else ""
    return "\n".join(x for x in (first, feat) if x)


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
