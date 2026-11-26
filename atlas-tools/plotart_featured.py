"""PlotArt Contemporary gallery page · one manually curated gallery (founder approval 26 Nov 2026, migration 0029).

The page (plotart/gallery/index.html) shows ONE arrangement, chosen by the founder in PlotArt Studio (Galleries -> Curate):
  - places 1-3: the prominent opening row (larger artwork presentation), in the generated region FEAT_BEGIN..FEAT_END;
  - places 4 onwards: "Explore the Gallery", in the generated collection region (plotart_gallery_pages.VG_BEGIN..VG_END),
    followed by the Artists A-Z list.
Every artist appears ONCE. Artists in Focus is no longer a separate section (its historical selection is kept in the
Studio, never shown). Each artist is introduced by the same editorial card (the former Artists in Focus card): the
representative artwork, its title and year, the photographic credit where the artist gave one, the artist's name, their
practice and their public location line where they authorised one (plotart_gallery_pages.meta_line), a short
introduction taken verbatim from the start of their own published biography (about 30-45 words, whole sentences), and
"View Gallery". No prices, dimensions, materials or availability: those stay in the artist's own gallery and Browse All
Artworks. Nothing is written or invented here; anything missing is simply left out.

What can be shown comes ONLY from the published galleries (plotart/artists/*/gallery.json):
  - opening row: the founder's chosen work must be shown AND available in the approved, published gallery, with a main
    photograph; otherwise the place is LEFT EMPTY (no substitution; the Studio names the vacancy to the founder);
  - places 4+: the founder's chosen work when it is eligible in the same way, otherwise the artist's first eligible work
    (their own order); with no eligible work the card shows the artist without an artwork image (never a broken one);
  - a published artist the arrangement does not name is added at the end, in the order galleries were first approved
    (never into the opening row, never displacing anyone); an artist whose opening place is empty is not added below.
Images are the artist's own published derivatives, never cropped (CSS: contain, natural proportions), with their alt text.

The arrangement the publishing pipeline receives (gallery addresses and artwork ids only) is
  {"opening": [{"artist", "work"}...<=3], "rest": [{"artist", "work" or null}...], "held": [gallery address...]}
and the page records it (data-pa-opening / data-pa-curated, and a held list), so it can be read back and re-rendered
exactly (arrangement_in), which is how the guards prove the page is what the published galleries render.
"""
import html
import re

import plotart_gallery_pages as P

FEAT_BEGIN, FEAT_END = "<!-- pa-featured-artists:begin -->", "<!-- pa-featured-artists:end -->"   # the opening row's region
REGION = re.compile(re.escape(FEAT_BEGIN) + r".*?" + re.escape(FEAT_END), re.S)
OPEN_ITEM = re.compile(r'data-pa-opening="([a-z0-9-]+):([a-z0-9]+)"')
CUR_ITEM = re.compile(r'data-pa-curated="([a-z0-9-]+):([a-z0-9]+|auto)"')
HELD = re.compile(r"<!-- pa-held:([a-z0-9,-]*) -->")
PAGE = "gallery/index.html"           # under plotart/
BASE = "../"                         # from plotart/gallery/ to plotart/
OPEN_MAX = 3
INTRO_WORDS = (30, 45)               # the short introduction: about 30-45 words of the artist's own published biography
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){0,6}$")
WORK_ID = re.compile(r"^w[0-9a-z]{4,30}$")
E = lambda s: html.escape(str(s), quote=True)
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-ɏ\"'‘“(])")
# The opening row before the founder's first Curate publication (21 Nov 2026), kept only for the old proofs' fixtures.
OPENING = [("carmel-marrinan", "wg1by72jg3b"), ("daniel-chester", "wfhtcyurvgf"), ("clare-o-connor", "w226r60hfsh")]


def intro(bio, words=INTRO_WORDS):
    """The start of the artist's published biography, verbatim: whole sentences of the first paragraph up to the word
    limit (at least the first sentence; a second and third are added while the total stays within it). A first sentence
    longer than the limit is shortened at a word with an ellipsis. A leading one-to-three-word heading line without a full
    stop (e.g. "Statement") is skipped. Whitespace is normalised only. No biography: no introduction (never invented)."""
    lo, hi = words
    if not isinstance(bio, str) or not bio.strip():
        return ""
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", bio.strip()) if p.strip()]
    while len(paras) > 1 and len(paras[0].split()) <= 3 and not re.search(r"[.!?]$", paras[0]):
        paras.pop(0)
    sents = [s for p in paras for s in _SENT.split(p)]   # later paragraphs only while the introduction is still short
    out, n = [], 0
    for s in sents:
        k = len(s.split())
        if out and n + k > hi:
            break
        out.append(s)
        n += k
        if n >= lo:
            break
    if lo <= n <= hi or (n <= hi and len(out) == len(sents)):
        return " ".join(out)
    # still short (the next sentence is long) or one over-long sentence: continue verbatim and stop at a comma or word
    # within the limit, marked with an ellipsis
    words_ = " ".join(sents).split()[:hi - 4]
    text = " ".join(words_)
    cut = max(text.rfind(","), text.rfind(";"))
    if cut > 0 and len(text[:cut].split()) >= lo:
        text = text[:cut]
    return text.rstrip(",;:—–- ") + "…"


def _main(w):
    return next((i for i in w.get("images") or [] if i.get("role") == "main" and i.get("derivatives")), None)


def _eligible(pkg, w):
    """A representative artwork must be shown AND available in its approved, published gallery, with a main photograph."""
    return (pkg.get("publication", {}).get("state") == "approved" and w in P.shown(pkg)
            and w.get("availability") == "available" and _main(w) is not None)


def check_arrangement(arr):
    """The arrangement from PlotArt Studio (or read back from the page), checked: public identifiers only, each artist
    once, at most three opening places. An arrangement already checked is returned as it is."""
    if isinstance(arr, dict) and arr.get("_checked"):
        return arr
    if not isinstance(arr, dict) or set(arr) - {"opening", "rest", "held"}:
        raise ValueError("the gallery arrangement carries an unexpected field")
    op, rest, held = arr.get("opening") or [], arr.get("rest") or [], arr.get("held") or []
    if not isinstance(op, list) or len(op) > OPEN_MAX or not isinstance(rest, list) or not isinstance(held, list):
        raise ValueError("the gallery arrangement is malformed")
    out = {"opening": [], "rest": [], "held": []}
    for it in op:
        if not isinstance(it, dict) or set(it) - {"position", "artist", "work"} or not isinstance(it.get("artist"), str) or not SLUG.match(it["artist"]) \
                or not isinstance(it.get("work"), str) or not WORK_ID.match(it["work"]):
            raise ValueError("an opening place carries an unexpected field or value: %r" % (it,))
        out["opening"].append((it["artist"], it["work"]))
    for it in rest:
        w = it.get("work") if isinstance(it, dict) else None
        if not isinstance(it, dict) or set(it) - {"artist", "work"} or not isinstance(it.get("artist"), str) or not SLUG.match(it["artist"]) \
                or not (w is None or (isinstance(w, str) and WORK_ID.match(w))):
            raise ValueError("a gallery place carries an unexpected field or value: %r" % (it,))
        out["rest"].append((it["artist"], w))
    for s in held:
        if not isinstance(s, str) or not SLUG.match(s):
            raise ValueError("a held opening place is not a gallery address")
        out["held"].append(s)
    names = [s for s, _ in out["opening"]] + [s for s, _ in out["rest"]]
    if len(names) != len(set(names)):
        raise ValueError("an artist appears more than once in the gallery arrangement")
    out["_checked"] = True
    return out


def representative(pkg, choice):
    """(work, main image) the card shows: the chosen work when eligible, else the artist's first eligible work, else
    (None, None)."""
    ws = [w for w in pkg["works"] if _eligible(pkg, w)]
    w = next((x for x in ws if x.get("id") == choice), None) or (ws[0] if ws else None)
    return (w, _main(w)) if w else (None, None)


def _credit(w, im, page):
    year = (", %s" % E(w["year"])) if w.get("year") else ""
    photo = (' · <span class="pa-fa-photo">Photo: %s</span>' % E(im["photo_credit"])) if im.get("photo_credit") else ""
    return '<a href="%s" data-pa-track="gallery_card_work"><i>%s</i></a>%s%s' % (E(page), E(w["title"]), year, photo)


def _text(pkg, gallery, cls=""):
    a = pkg["artist"]
    meta, words = P.meta_line(a), intro(a.get("bio"))
    return ('<div class="pa-fa-text%s"><h3 class="pa-fa-name">%s</h3>%s%s'
            '<p class="pa-fa-act"><a class="pa-fa-cta" href="%s" data-pa-track="gallery_card_artist">View Gallery <span aria-hidden="true">&rarr;</span>'
            '<span class="pa-vgc-sr"> of %s</span></a></p></div>') % (
        cls, E(a["display_name"]), ('<p class="pa-fa-practice">%s</p>' % E(meta)) if meta else "",
        ('<p class="pa-fa-intro">%s</p>' % E(words)) if words else "", E(gallery), E(a["display_name"]))


def _img(im, gallery, sizes, lazy=True):
    d = P.pick(im, 1200)
    return '<img src="%simg/%s" srcset="%s" sizes="%s" width="%d" height="%d" alt="%s"%s decoding="async">' % (
        E(gallery), E(d["file"]), E(P.srcset(im, gallery + "img/")), sizes, d["pixels"][0], d["pixels"][1], E(im["alt"]),
        ' loading="lazy"' if lazy else "")


def _opening_item(pkg, w, im, base):
    slug = pkg["artist"]["slug"]
    gallery = "%sartists/%s/" % (base, slug)
    page = "%s%s.html" % (gallery, w["slug"])
    return ('\n    <li class="pa-op-item" data-pa-opening="%s:%s"><figure class="pa-op-fig">'
            '<a class="pa-op-art" href="%s" data-pa-track="gallery_opening_artwork" tabindex="-1" aria-hidden="true">%s</a>'
            '<figcaption class="pa-fa-credit pa-op-credit">%s</figcaption></figure>%s</li>') % (
        slug, w["id"], E(page), _img(im, gallery, "(max-width:639px) 78vw, 31vw", lazy=False), _credit(w, im, page),
        _text(pkg, gallery, " pa-op-text"))


def _card(pkg, w, im, base, choice):
    slug = pkg["artist"]["slug"]
    gallery = "%sartists/%s/" % (base, slug)
    if w is None:   # no eligible artwork: the artist is introduced without an image (never a broken or unavailable one)
        fig = ""
    else:
        page = "%s%s.html" % (gallery, w["slug"])
        fig = ('<figure class="pa-fa-fig"><a class="pa-fa-art" href="%s" data-pa-track="gallery_card_artwork">%s</a>'
               '<figcaption class="pa-fa-credit">%s</figcaption></figure>') % (
            E(gallery), _img(im, gallery, "(max-width:639px) 92vw, (max-width:1099px) 46vw, 31vw"), _credit(w, im, page))
    return '\n    <li class="pa-fa-item%s" data-pa-curated="%s:%s">%s%s</li>' % (
        "" if fig else " is-textonly", slug, choice or "auto", fig, _text(pkg, gallery))


def resolve(arr, packages):
    """(opening [(pkg, work, image)], rest [(pkg, work|None, image|None, choice|None)]) as the page shows them."""
    a = check_arrangement(arr)
    by = {p["artist"]["slug"]: p for p in packages if p.get("publication", {}).get("state") == "approved"}
    opening = []
    for slug, wid in a["opening"]:
        pkg = by.get(slug)
        w = next((x for x in pkg["works"] if x.get("id") == wid), None) if pkg else None
        if w is not None and _eligible(pkg, w):
            opening.append((pkg, w, _main(w)))
    named = {s for s, _ in a["opening"]} | {s for s, _ in a["rest"]} | set(a["held"])
    rest = []
    for slug, choice in a["rest"] + [(p["artist"]["slug"], None) for p in P.gallery_order(list(by.values())) if p["artist"]["slug"] not in named]:
        pkg = by.get(slug)
        if pkg:
            w, im = representative(pkg, choice)
            rest.append((pkg, w, im, choice))
    return opening, rest


def opening(arr, packages, base=BASE):
    items = resolve(arr, packages)[0]
    if not items:
        return ""
    # on phones and tablets the row scrolls sideways; as a focusable region keyboard users can move it with the arrow keys
    row = '\n  <ol class="pa-op-row n-%d" aria-label="Selected artists" tabindex="0">%s\n  </ol>' % (
        len(items), "".join(_opening_item(p, w, im, base) for p, w, im in items))
    return '<section class="pa-op" aria-label="Selected artists"><div class="pa-wrap">%s\n</div></section>' % row


def collection(arr, packages, base=BASE):
    """Everything between VG_BEGIN and VG_END: the held list, the gallery's artist cards in the founder's order, then
    the Artists A-Z list (every published artist)."""
    a = check_arrangement(arr)
    rest = resolve(a, packages)[1]
    cards = "".join(_card(p, w, im, base, c) for p, w, im, c in rest)
    ol = ('\n  <ol class="pa-fa-list pa-gl n-%d" aria-label="Artists in the gallery">%s\n  </ol>' % (min(len(rest), 3), cards)) if rest else ""
    pkgs = [p for p in packages if p.get("publication", {}).get("state") == "approved"]
    return "%s\n  <!-- pa-held:%s -->%s\n  %s\n  %s" % (P.VG_BEGIN, ",".join(a["held"]), ol, P.artist_index(P.gallery_order(pkgs)), P.VG_END)


def region(doc):
    m = REGION.findall(doc)
    if len(m) != 1:
        raise ValueError("the opening row region is missing or repeated")
    return m[0]


def arrangement_in(doc):
    """The arrangement the page shows, read back from its items (opening, then every card in order, then the held list)."""
    span = P.vg_region(doc)
    if span is None:
        raise ValueError("the gallery collection region is missing or repeated")
    reg = doc[span[0]:span[1]]
    h = HELD.search(reg)
    return {"opening": [{"artist": s, "work": w} for s, w in OPEN_ITEM.findall(region(doc))],
            "rest": [{"artist": s, "work": None if w == "auto" else w} for s, w in CUR_ITEM.findall(reg)],
            "held": [x for x in (h.group(1).split(",") if h else []) if x]}


def shown_artists(doc):
    """Every artist the page introduces, in order (opening row, then the gallery)."""
    a = arrangement_in(doc)
    return [x["artist"] for x in a["opening"]] + [x["artist"] for x in a["rest"]]


def update(doc, arr, packages):
    """Re-render both generated regions from the arrangement and the published galleries."""
    a = check_arrangement(arr)
    first = opening(a, packages)
    doc = REGION.sub(lambda m: FEAT_BEGIN + ("\n" + first + "\n" if first else "") + FEAT_END, doc, count=1)
    span = P.vg_region(doc)
    if span is None:
        raise ValueError("the gallery collection region is missing or repeated")
    return doc[:span[0]] + collection(a, packages) + doc[span[1]:]


def consistent(doc, packages):
    """True when the page is exactly what its own arrangement renders from the published galleries."""
    try:
        return doc == update(doc, arrangement_in(doc), packages)
    except ValueError:      # a doctored page (an artist twice, a malformed item, a missing region) is never consistent
        return False


def outside(doc):
    """The page with the opening row region emptied (the collection region is pinned separately)."""
    region(doc)
    return REGION.sub(FEAT_BEGIN + FEAT_END, doc, count=1)


def refresh(root, packages, arr=None):
    """Re-render the page from the published galleries; with no arrangement from the Studio, keep the one the page shows,
    so withdrawn or unpublished work drops out (and newly published artists are added) on every publication."""
    path = root / "plotart" / PAGE if hasattr(root, "__truediv__") else root + "/plotart/" + PAGE
    doc = open(path, encoding="utf-8").read()
    new = update(doc, arrangement_in(doc) if arr is None else arr, packages)
    if new != doc:
        open(path, "w", encoding="utf-8").write(new)
    return new != doc
