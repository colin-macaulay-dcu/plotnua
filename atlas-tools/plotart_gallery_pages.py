"""PlotArt artist gallery pages (Phase 1, 29 Oct 2026). Rendered by build-plotart.py from gallery
packages (see plotart_gallery.py). Public fields only; the whole artwork image is always shown
(object-fit: contain), never cropped."""
import html
import re
import plotart_opportunities as OPP  # noqa: E402  (opportunities shown publicly, 16 Nov 2026)
import plotart_seo as SEO
import plotart_gallery as G  # noqa: E402  (exhibition_blocks, Phase C 25 Nov 2026)
from urllib.parse import quote

E = lambda s: html.escape(str(s), quote=True)
ENQUIRY_ADDRESS = "hello@plotnua.ie"     # interim pilot route (founder decision 29 Oct 2026); the relay replaces it
ENQUIRY_NOTICE = "PA-ENQ-2026-11"        # version of the enquiry notice shown under the form (privacy V11; the relay also accepts PA-ENQ-2026-10-29 on pages published earlier)


def enquiry_form(pkg, w, endpoint, commission=False):
    """The buyer-to-artist enquiry form (Phase 3). Rendered only when the relay is switched on (an endpoint is given);
    the mailto link stays as the no-JavaScript fallback. pa-enquiry.js reveals and sends it.
    commission=True (Open for Commissions, 13 Nov 2026): the same form about the artist, marked data-kind="commission";
    the relay accepts it only while the artist's published gallery is open for commissions."""
    if not endpoint:
        return ""
    a = pkg["artist"]
    ref = "PA-%s-%s" % (a["slug"], w["id"]) if w else "PA-%s" % a["slug"]
    about = ("“%s”" % E(w["title"])) if w else ("%s's work" % E(a["display_name"]))
    head = "Ask %s about a commission" % E(a["display_name"]) if commission else "Enquire about %s" % about
    return ('<form class="pa-enq" hidden data-endpoint="%s" data-ref="%s" data-notice="%s"%s novalidate>'
            '<p class="pa-enq-h">%s</p>'
            '<label class="pa-enq-f">Your name<input name="name" required maxlength="80" autocomplete="name"></label>'
            '<label class="pa-enq-f">Your email<input name="email" type="email" required maxlength="254" autocomplete="email"></label>'
            '<label class="pa-enq-f">Your message<textarea name="message" required minlength="10" maxlength="1500" rows="5"></textarea></label>'
            '<p class="pa-enq-notice">PlotArt passes your name, email address and message to %s so they can reply to you directly. '
            '<a href="%sprivacy.html#plotart-enquiries">How we handle enquiries</a></p>'
            '<label class="pa-hp" aria-hidden="true">Leave blank<input name="website" tabindex="-1" autocomplete="off"></label>'
            '<button class="pa-btn pa-btn--solid" type="submit">Send enquiry</button>'
            '<p class="pa-enq-status" role="status" aria-live="polite"></p></form>') % (
        E(endpoint), E(ref), ENQUIRY_NOTICE, ' data-kind="commission"' if commission else "", head, E(a["display_name"]), "../../../")
STATUS = {"available": "Available", "reserved": "Reserved", "sold": "Sold", "not_for_sale": "Not for sale"}
SHOWN = ("available", "reserved", "sold", "not_for_sale")


def shown(pkg):
    return [w for w in pkg["works"] if w["availability"] in SHOWN]


def euro(n):
    return "€{:,}".format(n)


def price_line(w):
    a = w["availability"]
    if a == "available":
        return euro(w["price_eur"]) if w.get("price_eur") else "Price on request"
    return STATUS[a]


def size_line(w):
    dims = [w["h_cm"], w["w_cm"]] + ([w["d_cm"]] if w.get("d_cm") else [])
    f = lambda v: ("%g" % v)
    cm = " × ".join(f(v) for v in dims) + " cm"
    inch = " × ".join("%.1f" % (v / 2.54) for v in dims) + " in"
    return cm, inch


def srcset(img, prefix):
    return ", ".join("%s%s %dw" % (prefix, d["file"], d["pixels"][0]) for d in img["derivatives"])


# The one portrait size the artist's gallery page shows. The import step keeps and records only this derivative
# (PLOTART-PUBLISHING-PORTRAIT-001, 5 Nov 2026): an image that is recorded but shown on no page is refused by the
# provenance guard (P9), which is correct, so the pipeline must not make portrait sizes nothing uses.
PORTRAIT_SHOWN = 600

# The sizes an artwork page shows for each extra view: a thumbnail and the full-size link (PLOTART-PUBLISHING-VIEWS-001,
# 12 Nov 2026). The import step keeps and records only these, for the same reason as the portrait above: a view size
# that no page shows would be a recorded-but-unreferenced image, which the provenance guard (P9) rightly refuses.
VIEW_SHOWN = {"thumb": 600, "full": 2000}


def pick(img, want):
    ds = img["derivatives"]
    best = [d for d in ds if d["long_edge"] >= want]
    return (best[0] if best else ds[-1])


def main_image(w):
    return next(i for i in w["images"] if i["role"] == "main")


# Alt text (page fixes, 27 Nov 2026, fix 10). The artist's own alt text is used verbatim whenever it describes the work;
# only a weak one is composed here, in the builder, from the artist's own title and medium (gallery.json is never
# changed). Weak: missing, fewer than four words, or nothing but the title. An artist's alt that is otherwise good but
# repeated word for word on another of their works keeps every word and is prefixed with the work's own title, so each
# image says which work it is. Artist and artwork pages only; collection and opportunity pages keep the export's alt.
def _words(t):
    return re.findall(r"[^\W_]+", str(t or "").casefold())


def _weak_alt(alt, title):
    w = _words(alt)
    return len(w) < 4 or w == _words(title)


def display_alt(pkg, w, img):
    alt = str((img or {}).get("alt") or "").strip()
    title, name = SEO.clean_title(w["title"]), pkg["artist"]["display_name"]
    imgs = w["images"]
    view = img is not imgs[0] and img.get("role") != "main"
    if _weak_alt(alt, w["title"]):
        if not view:
            # the artist's own short words are kept ("Abstract garden"), unless they only repeat the title
            said = " ".join(alt.split()) if alt and _words(alt) != _words(w["title"]) else ""
            said = _lower_common(said).rstrip(".")
            return ("%s by %s: %s, %s" % (title, name, said, medium_phrase(w))) if said else ("%s by %s, %s" % (title, name, medium_phrase(w)))
        views = [i for i in imgs if i is not imgs[0] and i.get("role") != "main"]
        n = ("" if len(views) == 1 else " %d" % (views.index(img) + 1))
        return ("Detail%s of %s by %s" if "detail" in alt.lower() or not alt else "View%s of %s by %s") % (n, title, name)
    if not view:
        mains = [main_image(x).get("alt", "").strip().casefold() for x in pkg["works"] if x is not w and x.get("images")]
        if alt.casefold() in mains:
            return "%s by %s: %s" % (title, name, _lower_common(" ".join(alt.split())))
    return alt


_COMMON_WORDS = frozenset("""abstract abstracted painting paintings landscape lanscape garden flowers full of colour colours colourful
bright geometric shapes patterns large scale large-scale detail view the a an with background multi coloured""".split())


def _lower_common(t):
    """An artist's alt words for use after a colon: material words and common describing words lower-cased ("Abstract
    Painting" -> "abstract painting"); any other word (a place, a name: "Mediterranean") keeps its capital."""
    return re.sub(r"[A-Za-z-]+", lambda m: m.group(0).lower() if m.group(0).lower() in _COMMON_WORDS or m.group(0).lower() in _MATERIAL_WORDS else m.group(0), t)


KIND_PHRASE = {"Painting": "painting", "Print": "original print", "Mixed Media": "mixed-media work", "Drawing": "drawing"}
MEDIUM_PHRASE_MAX = 40


def medium_phrase(w):
    """The artist's medium for use mid-sentence; a long materials list is named by its kind instead ("mixed-media work")."""
    m = _lower_first(w["medium"])
    if len(m) <= MEDIUM_PHRASE_MAX:
        return m
    return KIND_PHRASE.get(artwork_kind(w["medium"])) or "original work"


def card_image(pkg):
    """The Virtual Gallery card shows the artist's first (artist-ordered) shown work; (None, None) if none are on show."""
    ws = shown(pkg)
    return (ws[0], main_image(ws[0])) if ws else (None, None)


def commission_href(pkg):
    """The no-JavaScript fallback for "Enquire about a commission": an email to PlotArt naming the artist."""
    a = pkg["artist"]
    subj = "PlotArt commission enquiry: %s [PA-%s]" % (a["display_name"], a["slug"])
    body = "Hello,\n\nI'd like to ask %s about commissioning a new work.\n\n" % a["display_name"]
    return "mailto:%s?subject=%s&body=%s" % (ENQUIRY_ADDRESS, quote(subj), quote(body))


def commission_block(pkg, enquiry_endpoint):
    """Open for Commissions (13 Nov 2026; feature section 17 Nov 2026): ONLY when the artist has switched "Open for
    commissions" on in PlotArt Studio (the setting the enquiry relay itself checks). Choosing Commissions among their
    opportunities alone shows the Commissions pill, never this. The button and its form share one wrapper, so
    pa-enquiry.js pairs them; the form is the existing commission enquiry (data-kind="commission")."""
    a = pkg["artist"]
    if a.get("open_for_commissions") is not True:
        return ""
    name = a["display_name"]
    return ('\n<section class="pa-ag-com" id="commission" aria-labelledby="agComH"><div class="pa-wrap pa-ag-com-in">'
            '\n  <div class="pa-ag-com-t"><h2 id="agComH">Open for commissions</h2>'
            '<p>%s welcomes enquiries about new, commissioned work.</p>'
            '<p class="pa-ag-com-more"><a href="../../commissions/" data-pa-track="artist_commissions_page">How commissions work</a></p></div>'
            '\n  <div class="pa-ag-enq-c"><a class="pa-btn pa-btn--solid" href="%s" data-pa-track="artist_commission_enquiry"%s>'
            'Enquire about a commission</a>%s</div>'
            '\n</div></section>\n') % (
        E(name), E(commission_href(pkg)), " data-pa-enquire" if enquiry_endpoint else "", enquiry_form(pkg, None, enquiry_endpoint, commission=True))


def enquiry_href(pkg, w=None):
    a = pkg["artist"]
    if w:
        subj = "PlotArt enquiry: %s by %s [PA-%s-%s]" % (w["title"], a["display_name"], a["slug"], w["id"])
        body = "Hello,\n\nI'd like to ask about \"%s\" by %s.\n\n" % (w["title"], a["display_name"])
    else:
        subj = "PlotArt enquiry: %s [PA-%s]" % (a["display_name"], a["slug"])
        body = "Hello,\n\nI'd like to ask about work by %s.\n\n" % a["display_name"]
    return "mailto:%s?subject=%s&body=%s" % (ENQUIRY_ADDRESS, quote(subj), quote(body))


def meta_line(a):
    # Phase C: the artist's confirmed public location ("Strandhill, Co. Sligo, Ireland") when present, else the county as today
    return " · ".join(x for x in (a.get("practice"), (a.get("location") or {}).get("line") or a.get("county")) if x)


def checks_panel(pkg, blocks):
    """PRIVATE PREVIEW ONLY: what would stop publication, and what needs judgement."""
    warns = pkg["checks"]["warns"]
    li = lambda cls, t: '<li class="%s">%s</li>' % (cls, E(t))
    note = pkg["publication"].get("test_note")
    return ('<aside class="pa-ag-check" aria-label="Publication check (private preview only)"><div class="pa-wrap">'
            '<p class="pa-ag-check-h">Publication check <span>Private preview · never shown on plotnua.ie</span></p>'
            '%s<ul>%s%s</ul>%s</div></aside>') % (
        '<p class="pa-ag-check-note">%s</p>' % E(note) if note else "",
        "".join(li("b", "Stops publication: " + b) for b in blocks) or li("ok", "Nothing stops publication."),
        "".join(li("w", "Check: " + w) for w in warns),
        "")


def empty_works(a):
    """A published gallery with no works on show (founder decision 1 Nov 2026)."""
    first = a["display_name"].split(" ")[0] if " " in a["display_name"] else a["display_name"]
    return ('<div class="pa-ag-empty"><p class="pa-ag-empty-t">New work coming soon</p>'
            '<p class="pa-ag-empty-l">%s isn&#x27;t showing any works at the moment. You can still get in touch through PlotArt.</p></div>') % E(first)



_SENTENCE_END = re.compile(r"[.!?…:;\"”’')\]]\s*$")


# Exhibitions & Achievements (Phase C, 25 Nov 2026): its own section after "About", and a discreet link to it under the
# artist's name; both only when the artist has written something. Same markup as the Studio preview (render.js).
EXHIBITIONS_JUMP = '<p class="pa-ag-jump"><a href="#exhibitions">Exhibitions &amp; Achievements <span aria-hidden="true">\u2193</span></a></p>'


def exhibitions_section(a):
    if not a.get("exhibitions"):
        return ""
    body = "".join(
        ("<h3>%s</h3>" % E(x)) if k == "h" else
        ("<ul>%s</ul>" % "".join("<li>%s</li>" % E(i) for i in x)) if k == "ul" else
        ("<p>%s</p>" % E(x))
        for k, x in G.exhibition_blocks(a["exhibitions"]))
    return """<section class="pa-ag-cv" id="exhibitions" aria-labelledby="agCvH"><div class="pa-wrap pa-ag-about-in">
  <h2 id="agCvH">Exhibitions &amp; Achievements</h2>
  <div class="pa-ag-cv-body">%s</div>
</div></section>
""" % body


def paragraphs(text):
    """A biography's paragraphs (founder brief 18 Nov 2026): a blank line always starts a paragraph, and so does a single
    line break after the end of a sentence (artists press Enter once and expect a new paragraph). A line break in the
    middle of a sentence (text pasted from a document with fixed-width lines) is read as a space, as before.
    Same rule in the Studio preview (worker/plotart-studio/src/render.js)."""
    out = []
    for block in re.split(r"\n\s*\n", str(text or "").replace("\r\n", "\n")):
        cur = ""
        for line in block.split("\n"):
            line = line.strip()
            if not line:
                continue
            cur = (cur + " " + line) if cur else line
            if _SENTENCE_END.search(line):
                out.append(cur); cur = ""
        if cur:
            out.append(cur)
    return out

def work_tile(pkg, w, sizes, track="artist_artwork"):
    """One work in a gallery grid (the artist's Works, and "More by" on an artwork page): uncropped, lazy, with its price line."""
    im = main_image(w)
    d = pick(im, 1200)
    cls = " is-%s" % w["availability"].replace("_", "-")
    return ('\n    <li class="pa-ag-work%s"><a class="pa-ag-tile" href="%s.html" data-pa-track="%s">'
            '<span class="pa-ag-art"><img src="img/%s" srcset="%s" sizes="%s" '
            'width="%d" height="%d" alt="%s" loading="lazy" decoding="async"></span>'
            '<span class="pa-ag-cap"><span class="pa-ag-title">%s</span><span class="pa-ag-sub">%s</span>'
            '<span class="pa-ag-status">%s</span></span></a></li>' % (
                cls, E(w["slug"]), track, E(d["file"]), E(srcset(im, "img/")), sizes, d["pixels"][0], d["pixels"][1], E(display_alt(pkg, w, im)),
                E(w["title"]), E(" · ".join(x for x in (str(w["year"]) if w.get("year") else None, w["medium"], size_line(w)[0]) if x)),
                E(price_line(w))))


# Related collections (page fixes, 27 Nov 2026, fixes 5 and 9): a quiet line linking a work, or an artist's gallery, to the
# PlotArt collections it is actually in, decided by the collections' own tests (plotart_search_content), so the link and
# the collection can never disagree. Only available works are in a collection; a collection is named only while its page
# is indexable. Most specific first, at most three links in the line. Never a list of every collection.
# Release integration (28 Nov 2026): the growth 3 collections with their own tests join the line, in the same
# most-specific-first order (subject, then medium, then size, then price). The broad guides (offices, collecting, gifts)
# are not offered here. A narrower collection supersedes the broader one it sits inside (RELATED_SUPERSEDES), so a coastal
# work names the coastal collection rather than also the landscape one, and a work under €500 names that collection rather
# than also the under-€1,000 one.
RELATED = (  # (key, page under plotart/, link from an artist folder, anchor)
    ("coastal", "coastal-art-ireland/index.html", "../../coastal-art-ireland/", "coastal and seascape art"),
    ("landscape", "landscape-paintings-ireland/index.html", "../../landscape-paintings-ireland/", "landscape and coastal works"),
    ("figurative", "figurative-art-ireland/index.html", "../../figurative-art-ireland/", "figurative and portrait art"),
    ("abstract", "abstract-contemporary-art-ireland.html", "../../abstract-contemporary-art-ireland.html", "abstract and contemporary art"),
    ("prints", "original-prints-ireland/index.html", "../../original-prints-ireland/", "original prints and limited editions"),
    ("oil", "oil-paintings-ireland/index.html", "../../oil-paintings-ireland/", "oil paintings"),
    ("mixed", "mixed-media-art-ireland/index.html", "../../mixed-media-art-ireland/", "mixed media and collage"),
    ("small", "small-artworks/index.html", "../../small-artworks/", "small original artworks"),
    ("under", "original-art-under-500/index.html", "../../original-art-under-500/", "original art under €500"),
    ("under_1000", "original-art-under-1000/index.html", "../../original-art-under-1000/", "original art under €1,000"),
    ("large", "large-artworks/index.html", "../../large-artworks/", "large original artworks"),
)
RELATED_SUPERSEDES = {"coastal": "landscape", "under": "under_1000"}   # narrower key -> the broader key it replaces
RELATED_ADDED = frozenset({"coastal", "figurative", "prints", "oil", "mixed", "small", "under_1000"})   # the growth 3 keys
RELATED_MAX = 3


def related(pkg, w, launch=None, keep_commission_room=True):
    """The RELATED entries this work is in (empty unless it is available). keep_commission_room is the artwork line's rule
    below; the gallery page's line (artist_related_line) has no commission link, so it does not reserve room for one."""
    import plotart_search_content as C   # lazy: plotart_search_content imports this module at the top
    if w["availability"] != "available":
        return []
    launch = SEO.switches() if launch is None else launch
    test = {"coastal": C.is_coastal, "landscape": C.is_landscape, "figurative": C.is_figurative,
            "abstract": lambda x: C.is_abstract(x, pkg), "prints": C.is_print, "oil": C.is_oil, "mixed": C.is_mixed,
            "small": C.is_small, "under": C.is_under, "under_1000": C.is_under_1000, "large": C.is_large}
    rel = [r for r in RELATED if test[r[0]](w) and SEO.indexable(r[1], launch)]
    # The growth 3 collections never take the commission link's place: while the artist is Open for commissions (and the
    # Commissions page is indexable) they only fill the line up to RELATED_MAX - 1, so every work that had room for
    # "commission a new work" keeps it. The original four collections behave exactly as before.
    room = RELATED_MAX - sum(1 for r in rel if r[0] not in RELATED_ADDED)
    if keep_commission_room and pkg["artist"].get("open_for_commissions") is True and SEO.indexable("commissions/index.html", launch):
        room -= 1
    out = []
    for r in rel:
        if r[0] in RELATED_ADDED:
            if room <= 0:
                continue
            room -= 1
        out.append(r)
    keys = {r[0] for r in out}     # a narrower collection that made the line replaces the broader one it sits inside
    return [r for r in out if not any(RELATED_SUPERSEDES.get(k) == r[0] for k in keys)]


def _series(links):
    return links[0] if len(links) == 1 else ", ".join(links[:-1]) + " and " + links[-1]


def related_line(pkg, w, launch=None):
    """The artwork page's line: the collections this work is in, then (room permitting, and only while the artist has
    switched Open for commissions on and the Commissions page is indexable) a link to commission new work."""
    launch = SEO.switches() if launch is None else launch
    rel = related(pkg, w, launch)[:RELATED_MAX]
    parts = []
    if rel:
        parts.append("Also in the %s collection%s." % (_series(['<a href="%s" data-pa-track="artwork_related_collection">%s</a>' % (E(h), E(t)) for _, _, h, t in rel]),
                                                     "s" if len(rel) > 1 else ""))
    if len(rel) < RELATED_MAX and pkg["artist"].get("open_for_commissions") is True and SEO.indexable("commissions/index.html", launch):
        parts.append('You can also <a href="../../commissions/" data-pa-track="artwork_commissions_page">commission a new work</a> from %s.' % E(pkg["artist"]["display_name"]))
    return ('<p class="pa-aw-cta-note">%s</p>' % " ".join(parts)) if parts else ""


def artist_related_line(pkg, launch=None):
    """The gallery page's line under the Works grid: the collections that hold the most of this artist's available works
    (at most three, most works first; ties keep RELATED's order)."""
    launch = SEO.switches() if launch is None else launch
    count = {}
    for w in shown(pkg):
        for r in related(pkg, w, launch, keep_commission_room=False):
            count[r] = count.get(r, 0) + 1
    rel = sorted(count, key=lambda r: (-count[r], RELATED.index(r)))[:RELATED_MAX]
    if not rel:
        return ""
    name = pkg["artist"]["display_name"]
    first = name.split(" ")[0] if " " in name else name
    return '<p class="pa-aw-cta-note">See %s’s work in the %s collection%s.</p>' % (
        E(first), _series(['<a href="%s" data-pa-track="artist_related_collection">%s</a>' % (E(h), E(t)) for _, _, h, t in rel]), "s" if len(rel) > 1 else "")


MORE_BY_MAX = 3   # one row of the gallery grid


def more_by(pkg, w):
    """"More by <artist>" under an artwork (fix 6): the next shown works in the artist's own order (wrapping round), in the
    gallery page's own grid and tiles. Empty when the artist shows no other work."""
    ws = shown(pkg)
    if w not in ws or len(ws) < 2:
        return ""
    i = ws.index(w)
    others = [ws[(i + k) % len(ws)] for k in range(1, len(ws))][:MORE_BY_MAX]
    sizes = {1: "(max-width:639px) 92vw, 720px", 2: "(max-width:639px) 92vw, 520px"}.get(len(others), "(max-width:639px) 92vw, (max-width:1023px) 46vw, 31vw")
    name = pkg["artist"]["display_name"]
    return ('<section class="pa-ag-works" aria-labelledby="awMoreH"><div class="pa-wrap">\n'
            '  <div class="pa-ag-head"><h2 id="awMoreH">More by %s</h2><p><a href="index.html" data-pa-track="artwork_more_by_artist">All works</a></p></div>\n'
            '  <ol class="pa-ag-grid">%s\n  </ol>\n</div></section>\n') % (
        E(name), "".join(work_tile(pkg, x, sizes, "artwork_more_by_artist") for x in others))


def artist_body(pkg, blocks=None, preview=False, enquiry_endpoint=None):
    a = pkg["artist"]
    works = shown(pkg)
    name = a["display_name"]
    tiles = []
    # one or two works sit larger and centred (founder decision 1 Nov 2026): the size hint follows the layout
    sizes = {1: "(max-width:639px) 92vw, 720px", 2: "(max-width:639px) 92vw, 520px"}.get(len(works), "(max-width:639px) 92vw, (max-width:1023px) 46vw, 31vw")
    for w in works:
        tiles.append(work_tile(pkg, w, sizes))
    portrait = ""
    if a.get("portrait"):
        p = a["portrait"]; d = pick(p, PORTRAIT_SHOWN)
        portrait = '<span class="pa-ag-portrait"><img src="img/%s" width="%d" height="%d" alt="%s"></span>' % (
            E(d["file"]), d["pixels"][0], d["pixels"][1], E(p["alt"]))
    links = []
    if a.get("website"):
        links.append('<a href="%s" rel="noopener nofollow" data-pa-track="artist_website">Website <span aria-hidden="true">↗</span></a>' % E(a["website"]))
    if a.get("instagram"):
        links.append('<a href="https://www.instagram.com/%s/" rel="noopener nofollow" data-pa-track="artist_instagram">Instagram <span aria-hidden="true">↗</span></a>' % E(a["instagram"]))
    bio = "".join("<p>%s</p>" % E(p) for p in paragraphs(a["bio"]))
    cv = exhibitions_section(a)
    return """%s
<section class="pa-ag-hero%s"><div class="pa-wrap">
  <nav class="pa-crumb" aria-label="Breadcrumb"><a href="../../gallery/">Artists’ Gallery</a><span aria-hidden="true">/</span><span aria-current="page">%s</span></nav>
  <div class="pa-ag-id">%s<div>
    %s<h1>%s</h1>
    %s%s%s%s
  </div></div>
</div></section>
%s
<section class="pa-ag-works" aria-labelledby="agWorksH"><div class="pa-wrap">
  <div class="pa-ag-head"><h2 id="agWorksH">Works</h2><p>%s</p></div>
  %s%s
</div></section>

<section class="pa-ag-about" aria-labelledby="agAboutH"><div class="pa-wrap pa-ag-about-in">
  <h2 id="agAboutH">About %s</h2>
  <div class="pa-ag-bio">%s%s</div>
</div></section>
%s
<section class="pa-ag-enq"><div class="pa-wrap pa-ag-enq-in">
  <p class="pa-ag-enq-t">Interested in %s's work?</p>
  <p class="pa-ag-enq-l">Send an enquiry through PlotArt and we'll put you in touch with the artist.</p>
  <a class="pa-btn pa-btn--solid" href="%s" data-pa-track="artist_enquiry"%s>Enquire through PlotArt</a>%s
</div></section>
""" % (checks_panel(pkg, blocks) if preview else "",
       " has-portrait" if portrait else "", E(name), portrait,
       '<span class="pa-gcard-badge">Founding Artist</span>' if a.get("founding") else "",
       E(name), (('<p class="pa-ag-meta">%s</p>' % E(meta_line(a))) if meta_line(a) else ""),
       ('<p class="pa-ag-statement">%s</p>' % E(a["statement"])) if a.get("statement") else "",
       EXHIBITIONS_JUMP if cv else "",
       OPP.artist_line(pkg),
       commission_block(pkg, enquiry_endpoint),
       ("%d %s" % (len(works), "artwork" if len(works) == 1 else "artworks")) if works else "None on show right now",
       ('<ol class="pa-ag-grid">%s\n  </ol>' % "".join(tiles)) if works else empty_works(a),
       ("\n  " + artist_related_line(pkg)) if artist_related_line(pkg) else "",
       E(name.split(" ")[0] if " " in name else name), bio,
       ('<p class="pa-ag-links">%s</p>' % "".join(links)) if links else "",
       cv,
       E(name), E(enquiry_href(pkg)), " data-pa-enquire" if enquiry_endpoint else "", enquiry_form(pkg, None, enquiry_endpoint))


def basket_block(w, origin):
    """Multi-artist basket (21 Nov 2026; off unless the founder sets basket_origin in plotart-gallery-config.json). Hidden
    until pa-basket.js confirms with the checkout Worker that this work can be bought online right now; otherwise the page
    is exactly the enquiry page it was. Without JavaScript nothing is shown."""
    # Sprint 1 (founder approval 26 Nov 2026): "Buy online" is the first choice only for a work the checkout confirms live;
    # the note says what happens next (the basket, then payment), and the work's own delivery, cancellation and seller
    # details fill the list from the checkout's answer (pa-basket.js). Nothing here is shown until then.
    return ('<div class="pa-basket" data-pa-basket-origin="%s" data-pa-artwork="%s" hidden>'
            '<a class="pa-btn pa-btn--solid" href="%s/basket?add=%s" data-pa-track="artwork_basket_add">Buy online</a>'
            '<p class="pa-aw-cta-note">Adds this work to your PlotArt basket, where you see the delivery cost and the total before paying securely by card. '
            'Online purchase delivers in the Republic of Ireland only; for delivery elsewhere, please enquire.</p>'
            '<ul class="pa-aw-assure" aria-label="Buying this work online" hidden></ul></div>') % (
        E(origin), E(w["id"]), E(origin), E(w["id"]))


# SEO and analytics package (founder approval 26 Nov 2026, section 2.5): two contextual links on every artwork page, under
# the work's details, in the existing small-note style (no new styles): the size calculator and the available collection.
MORE_LINKS = ('<p class="pa-aw-cta-note"><a href="../../art-size-calculator.html" data-pa-track="artwork_size_calculator">Check this size on your wall</a>'
              ' with the PlotArt art size calculator, or see <a href="../../artworks/" data-pa-track="artwork_more_artworks">more original Irish art for sale</a>.</p>')


def artwork_kind(medium):
    """Painting, Print, Mixed Media or Drawing, read from the artist's own medium wording (None when it says none of
    these). A printmaking process names a print even with added paint or collage (an intaglio with collage is still an
    original print); several processes together, or mixed media named as such, are Mixed Media."""
    m = str(medium or "").lower()
    if re.search(r"screen ?print|monoprint|mono-print|intaglio|etch|lino ?cut|woodcut|lithograph|silkscreen|serigraph|drypoint|giclee", m):
        return "Print"
    if "mixed media" in m or "collage" in m or ("print" in m and re.search(r"paint|ink|pen|pencil", m)):
        return "Mixed Media"
    if re.search(r"\boil\b|acrylic|acyrlic|crylic|paint|gouache|watercolou?r|tempera|enamel|encaustic", m):
        return "Painting"
    if re.search(r"\bpen\b|\bink\b|pencil|charcoal|graphite|pastel", m):
        return "Drawing"
    return None


TITLE_MAX = 60


def artwork_title(pkg, w):
    """The first of these that fits in TITLE_MAX characters (page fixes, 27 Nov 2026, fix 1): '<Title> by <Artist> |
    Original <kind> | PlotArt', then without '| PlotArt' (search shows the site name anyway), then '<Title> by <Artist> |
    PlotArt', '<Title> by <Artist>', and the title alone. The title is the artist's own, less one pair of wrapping quotation
    marks (SEO.clean_title). No price (it goes stale and reads as retail) and no size: both are in the description."""
    title = SEO.clean_title(w["title"])
    base = "%s by %s" % (title, pkg["artist"]["display_name"])
    kind = artwork_kind(w["medium"])
    options = (["%s | Original %s | PlotArt" % (base, kind), "%s | Original %s" % (base, kind)] if kind else []) + \
        ["%s | PlotArt" % base, base, title]
    return next((t for t in options if len(t) <= TITLE_MAX), title)


_MATERIAL_WORDS = frozenset("""oil oils bar acrylic acyrlic crylic paint mixed media on in canvas linen wood wooden panel paper board and
with collage resin varnish lacquer monoprint screen print multi layered etched intaglio ink pen pencil spray reclaimed plywood
gessoed mounted dibond tondo raw silk gouache watercolour watercolor charcoal graphite pastel""".split())


def _lower_first(t):
    """The artist's medium as written, for use mid-sentence: common material words are lower-cased ("Mixed Media on
    Canvas" -> "mixed media on canvas"); any other word, such as a paper maker's name, keeps its capital."""
    return re.sub(r"[A-Za-z]+", lambda m: m.group(0).lower() if m.group(0).lower() in _MATERIAL_WORDS else m.group(0), str(t or "").strip())


DESCRIPTION_MAX = 160


def artwork_description(pkg, w):
    """Section 2.5, reworded in the page fixes (27 Nov 2026, fix 2) to open with the work's own title, so no two works share
    a description: title, artist, medium, size, the price only when the work has a public price, and what the buyer can do
    now. Says "enquire", never "buy online" (whether a work can be bought online is decided live by the checkout). Over
    DESCRIPTION_MAX characters, the last sentence goes first, then the medium."""
    a = pkg["artist"]
    size = " × ".join("%g" % v for v in (w["h_cm"], w["w_cm"])) + " cm"
    head = "%s by %s" % (SEO.clean_title(w["title"]), a["display_name"])
    av = w["availability"]
    if av == "available":
        priced = w.get("price_eur") and not w.get("price_on_request")
        status, tail = ("%s." % euro(w["price_eur"])) if priced else "Price on request.", "Enquire to buy direct from the artist through PlotArt."
    elif av == "reserved":
        status, tail = "Reserved.", "Ask through PlotArt to be told if it becomes available."
    elif av == "sold":
        status, tail = "Sold.", "Ask the artist through PlotArt about their other work."
    else:
        status, tail = "Not for sale.", "Ask the artist through PlotArt about their other work."
    medium = _lower_first(w["medium"])
    kind = {"Painting": "original painting", "Print": "original print", "Mixed Media": "original mixed-media work",
            "Drawing": "original drawing"}.get(artwork_kind(w["medium"]), "original work")
    for text in ("%s: original %s, %s. %s %s" % (head, medium, size, status, tail),
                 "%s: original %s, %s. %s" % (head, medium, size, status),
                 "%s: %s, %s. %s %s" % (head, kind, size, status, tail),
                 "%s: %s, %s. %s" % (head, kind, size, status)):
        if len(text) <= DESCRIPTION_MAX:
            return text
    return text[:DESCRIPTION_MAX - 1].rsplit(" ", 1)[0] + "…"


def artwork_body(pkg, w, prev_w, next_w, preview=False, enquiry_endpoint=None, basket_origin=None):
    a = pkg["artist"]
    imgs = w["images"]
    im = imgs[0]
    d = pick(im, 2000)
    cm, inch = size_line(w)
    rows = [("Medium", w["medium"])]
    if w.get("materials"):
        rows.append(("Materials", w["materials"]))
    rows.append(("Size", "%s (%s)" % (cm, inch)))
    if w.get("year"):
        rows.append(("Year", str(w["year"])))
    dl = "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (E(k), E(v)) for k, v in rows)
    views = ""
    if len(imgs) > 1:
        views = '<ul class="pa-aw-views" aria-label="More views">%s</ul>' % "".join(
            '<li><a href="img/%s"><img src="img/%s" alt="%s" loading="lazy" decoding="async"></a></li>' % (
                E(pick(i, VIEW_SHOWN["full"])["file"]), E(pick(i, VIEW_SHOWN["thumb"])["file"]), E(display_alt(pkg, w, i))) for i in imgs[1:])
    credit = ' <span>Photo: %s</span>' % E(im["photo_credit"]) if im.get("photo_credit") else ""
    avail = w["availability"]
    if avail in ("available", "reserved"):
        cta = ('<a class="pa-btn pa-btn--solid" href="%s" data-pa-track="artwork_enquiry"%s>%s</a>'
               '<p class="pa-aw-cta-note">Buy directly from the artist: your enquiry is passed to %s through PlotArt, and you agree the price, delivery and payment together. Nothing is paid until you have both agreed.</p>%s') % (
            E(enquiry_href(pkg, w)), " data-pa-enquire" if enquiry_endpoint else "",
            "Enquire to purchase" if avail == "available" else "Ask to be told if it becomes available", E(a["display_name"]),
            enquiry_form(pkg, w, enquiry_endpoint))
        if basket_origin and avail == "available":
            cta += basket_block(w, basket_origin)
    else:
        cta = '<a class="pa-btn pa-btn--ghost" href="%s" data-pa-track="artwork_enquiry_other"%s>Ask about %s\'s other work</a>%s' % (
            E(enquiry_href(pkg)), " data-pa-enquire" if enquiry_endpoint else "", E(a["display_name"]), enquiry_form(pkg, None, enquiry_endpoint))
    ai = ""
    if w["ai_involvement"] != "none":
        ai = '<p class="pa-aw-ai"><strong>AI disclosure.</strong> %s</p>' % E(w["ai_note"])
    nav = '<nav class="pa-aw-pn" aria-label="More works by %s">%s<a href="index.html">All works</a>%s</nav>' % (
        E(a["display_name"]),
        ('<a href="%s.html" rel="prev"><span aria-hidden="true">←</span> %s</a>' % (E(prev_w["slug"]), E(prev_w["title"]))) if prev_w else "<span></span>",
        ('<a href="%s.html" rel="next">%s <span aria-hidden="true">→</span></a>' % (E(next_w["slug"]), E(next_w["title"]))) if next_w else "<span></span>")
    return """
<section class="pa-aw"><div class="pa-wrap">
  <nav class="pa-crumb" aria-label="Breadcrumb"><a href="../../gallery/">Artists’ Gallery</a><span aria-hidden="true">/</span><a href="index.html">%s</a><span aria-hidden="true">/</span><span aria-current="page">%s</span></nav>
  <div class="pa-aw-in">
    <figure class="pa-aw-fig"><span class="pa-aw-frame"><img src="img/%s" srcset="%s" sizes="(max-width:1023px) 94vw, 62vw" width="%d" height="%d" alt="%s" decoding="async" fetchpriority="high"></span>%s
      <figcaption>%s, <i>%s</i>%s</figcaption></figure>
    <div class="pa-aw-info">
      <p class="pa-aw-artist"><a href="index.html">%s</a>%s</p>
      <h1>%s</h1>
      <p class="pa-aw-price is-%s">%s</p>
      <div class="pa-aw-cta">%s</div>
      <dl class="pa-aw-dl">%s</dl>
      %s
      %s
      %s
    </div>
  </div>
  %s
</div></section>
%s""" % (E(a["display_name"]), E(w["title"]), E(d["file"]), E(srcset(im, "img/")), d["pixels"][0], d["pixels"][1], E(display_alt(pkg, w, im)), views,
       E(a["display_name"]), E(w["title"]), credit,
       E(a["display_name"]), ' <span class="pa-gcard-badge">Founding Artist</span>' if a.get("founding") else "",
       E(w["title"]), avail.replace("_", "-"), E(price_line(w)), cta, dl,   # the buttons directly under the price (Sprint 1, 26 Nov 2026)
       ('<p class="pa-aw-desc">%s</p>' % E(w["description"])) if w.get("description") else "",
       ai, MORE_LINKS + (("\n      " + related_line(pkg, w)) if related_line(pkg, w) else ""), nav, more_by(pkg, w))


# ---- The Virtual Gallery collection: Direction C2 "The Curated Collection" (founder approval 5 Nov 2026) ----
# One uncropped representative work per published gallery, equal treatment for every artist, then the Artists A-Z
# list (the founding positions index was removed from public view on 21 Nov 2026). The builder writes everything between the two markers below in
# plotart/gallery/index.html (the rest of the page is fixed and pinned by the launch manifest).
VG_BEGIN, VG_END = "<!-- pa-vg-collection:begin -->", "<!-- pa-vg-collection:end -->"
VG_STATES = (("pub", "Published"), ("res", "Reserved"), ("prep", "In preparation"), ("av", "Available"))


def _vg_work(pkg, n):
    """One open gallery on the wall: its first shown work (never cropped), the name, practice and "Enter the gallery".

    Founder brief 23 Nov 2026: no number beside the name. The founding position is not shown or announced; it is kept
    only as data-pa-position on the work, so the publishing and launch guards can still prove no artist's place moves."""
    a = pkg["artist"]
    w, im = card_image(pkg)
    if im is None:   # no works on show (founder decision 1 Nov 2026): the gallery keeps its place, with the empty state
        art = '<div class="pa-vgc-art is-empty"><span>New work coming soon</span></div>'
    else:
        d = pick(im, 1200)
        art = ('<div class="pa-vgc-art"><img src="../artists/%s/img/%s" srcset="%s" sizes="(max-width:639px) 100vw, 680px" '
               'width="%d" height="%d" alt="%s" loading="lazy" decoding="async"></div>') % (
            E(a["slug"]), E(d["file"]), E(srcset(im, "../artists/%s/img/" % a["slug"])), d["pixels"][0], d["pixels"][1], E(im["alt"]))
    pos = (' data-pa-position="%02d"' % n) if n else ""
    return """
    <li class="pa-vgc-work"%s>%s
      <div class="pa-vgc-label"><h3 class="pa-vgc-name"><a href="../artists/%s/" data-pa-track="vg_artist">%s</a></h3>
        <p class="pa-vgc-practice">%s</p><span class="pa-vgc-enter" aria-hidden="true">Enter the gallery &rarr;</span></div></li>""" % (
        pos, art, E(a["slug"]), E(a["display_name"]), E(meta_line(a)))


# The wall's founding positions, read from the page (23 Nov 2026: data-pa-position, no visible numeral): {slug: "NN"}.
WALL_POSITION = re.compile(r'<li class="pa-vgc-work" data-pa-position="(\d\d)">(?:(?!</li>).)*?<h3 class="pa-vgc-name"><a href="\.\./artists/([a-z0-9-]+)/"', re.S)


def wall_positions(region_text):
    return dict((sl, n) for n, sl in WALL_POSITION.findall(region_text))


def vg_positions(pkgs, spaces=25, layout=None):
    """[(n, state, pkg)] for positions 1..spaces, plus the published galleries that hold no position.

    Without a layout: published galleries take positions 1..n in the given order; the rest are available.
    With the founder's layout from PlotArt Studio (Gallery order, 31 Oct 2026) -- {"positions": [{"position", "slug",
    "reserved", "assigned"}], "extra": [slug, ...]} -- position N is the artist placed there if their gallery is
    published here; otherwise RESERVED if the founder reserved it; otherwise IN PREPARATION if an artist is placed there
    whose gallery is not published (the Studio sends only "assigned", never who; a gallery address that is not
    published here counts the same and is never shown); otherwise AVAILABLE. Published galleries without a position
    follow in the layout's "extra" order, then by gallery address. The layout never carries a reservation note."""
    by = {p["artist"]["slug"]: p for p in pkgs}
    out, placed = [], set()
    if layout is None:
        for i, p in enumerate(pkgs[:spaces], 1):
            out.append((i, "pub", p)); placed.add(p["artist"]["slug"])
        out += [(n, "av", None) for n in range(len(out) + 1, spaces + 1)]
        return out, [p for p in pkgs[spaces:]]
    pos = {int(e["position"]): e for e in layout.get("positions", []) if 1 <= int(e["position"]) <= spaces}
    for n in range(1, spaces + 1):
        e = pos.get(n) or {}
        if e.get("slug") in by and e["slug"] not in placed:
            out.append((n, "pub", by[e["slug"]])); placed.add(e["slug"])
        elif e.get("reserved"):
            out.append((n, "res", None))
        elif e.get("assigned") or e.get("slug"):
            out.append((n, "prep", None))
        else:
            out.append((n, "av", None))
    rest = [s for s in layout.get("extra", []) if s in by and s not in placed]
    rest += sorted(s for s in by if s not in placed and s not in rest)
    return out, [by[s] for s in rest]


def artist_index(pkgs):
    if not pkgs:
        return ""
    links = "".join('<li><a href="../artists/%s/" data-pa-track="vg_artist_az">%s</a></li>' %
                    (E(p["artist"]["slug"]), E(p["artist"]["display_name"]))
                    for p in sorted(pkgs, key=lambda p: (p["artist"]["display_name"].casefold(), p["artist"]["slug"])))
    return ('<nav class="pa-vgc-az" aria-labelledby="vgAzH"><h3 id="vgAzH">Artists A–Z</h3>'
            '<ul>%s</ul></nav>') % links


def vg_collection(pkgs, spaces=25, layout=None, featured=()):
    """Everything between VG_BEGIN and VG_END on the Virtual Gallery page: the wall of open
    galleries (in position order, then any without a position) and the Artists A-Z list.
    Shared by the production content pipeline (plotart-gallery-publish.py)."""
    positions, extra = vg_positions(pkgs, spaces, layout)
    # Explore More Artists (founder decision 17 Nov 2026): the wall leaves out the artists featured above it (their gallery
    # addresses, read from the page's Featured Artists region), so nobody appears twice. Everyone else keeps their place
    # (its position kept as data only since 23 Nov 2026); the A-Z list below still names every published artist.
    hide = set(featured)
    works = [_vg_work(p, n) for n, st, p in positions if st == "pub" and p["artist"]["slug"] not in hide] + \
        [_vg_work(p, None) for p in extra if p["artist"]["slug"] not in hide]
    opened = len(works)
    hang = ('\n  <ol class="pa-vgc-hang n-%s" aria-label="Open galleries">%s\n  </ol>' % (min(opened, 3), "".join(works))) if works else ""
    # The "N of 25 galleries open" counter was removed with the twenty-five-gallery framing (founder brief 17 Nov 2026).
    # The public "Founding positions" index (heading, note, occupancy line, published/reserved/available summary and the
    # numbered twenty-five-position table) was removed on 21 Nov 2026 (founder brief "Remove public Founding positions
    # section"): a public presentation change only. The founding records, numbers, agreements, the Studio's Gallery order
    # and Review Desk, and the Founding 25 page are unchanged; the positions still order the wall above.
    return """%s%s
  %s
  %s""" % (VG_BEGIN, hang, artist_index(pkgs), VG_END)


def vg_region(html_text):
    """(start, end) of the generated collection region, markers included; None if the page has no such region."""
    a = html_text.find(VG_BEGIN)
    b = html_text.find(VG_END, a + 1) if a >= 0 else -1
    if a < 0 or b < 0 or html_text.count(VG_BEGIN) != 1 or html_text.count(VG_END) != 1:
        return None
    return a, b + len(VG_END)


def gallery_order(pkgs):
    return sorted(pkgs, key=lambda p: (p["publication"].get("approved_at") or "9999", p["artist"]["display_name"]))


# Search titles and descriptions for particular artist galleries (growth package, 27 Nov 2026). Kept HERE, in the builder,
# keyed by slug, so a Studio publication (which rewrites gallery.json) never overwrites them. Every fact must come from that
# artist's own published biography or statement; the figures ({works}, {from_price}) are computed from the published
# gallery at every build. An artist not listed keeps the standard title and description. Titles at most 60 characters,
# descriptions at most 160 (checked by artist_meta, which falls back to the standard wording rather than publish a longer one).
# Review an entry whenever that artist's biography changes.
ARTIST_META = {
    # bio: "Best known for his appearances on MasterChef Ireland and Hell's Kitchen ... working alongside ... Marco Pierre
    # White"; "Today, Nick channels his creativity into painting". Search Console: most "nick munier" searches are about the
    # restaurateur and TV figure, so the title says plainly that this page is his painting.
    "nick-munier": ("Nick Munier | From MasterChef Ireland to Painting | PlotArt",
                    "Nick Munier, of MasterChef Ireland and Hell’s Kitchen, worked alongside Marco Pierre White. Now he paints: see {works}{from_price} and enquire."),
    # bio: "Dublin-based contemporary artist originally from Cahirciveen, Co. Kerry"; "painting, printmaking, photography and
    # collage"; "Inspired by the Irish landscape, coastal settings"; "vibrant, layered artworks"
    "carolyn-walsh": ("Carolyn Walsh Art | Coastal Mixed-Media Works | PlotArt",
                      "Carolyn Walsh is a Dublin-based artist from Cahirciveen, Co. Kerry, making layered coastal works in paint, print and collage. See {works}{from_price}."),
    # bio: "Hewson won the Whyte's Award for painting at the 190th RHA Annual Exhibition"; "currently Artist in Residence at
    # The Royal Hibernian Academy"; statement: "abstract language that ... extends into print"
    "leah-hewson": ("Leah Hewson | Abstract Paintings & Prints | PlotArt",
                    "Leah Hewson, Artist in Residence at the RHA and winner of the Whyte’s Award for painting at the 190th RHA Annual. See {works}{from_price}."),
    # page fixes (27 Nov 2026, fix 8; the two artists with the most Search Console impressions after the three above).
    # Titles set by founder decision (28 Nov 2026). bio: "Rasher, is a self-taught artist based in Wicklow. His emotionally resonating
    # oil paintings ..."; "noted for being an invited artist of the Royal Hibernian Academy Dublin"
    "mark-kavanagh-rasher": ("Rasher Mark Kavanagh – Oil Paintings | PlotArt",
                             "Rasher, a self-taught painter based in Wicklow and an invited artist of the RHA, makes emotionally resonant oil paintings. See {works}{from_price}."),
    # bio: "his studio occupies a former church organ factory near the historic centre of Göttingen"; "Working with pigments,
    # oils, emulsions and varnishes, he incorporates raw silk powder and fibres"; "layering of translucent and opaque
    # substances". (No nationality wording: the page states what he makes and where his studio is.)
    "fintan-whelan": ("Fintan Whelan – Abstract Paintings | PlotArt",
                      "Fintan Whelan, an abstract painter with a studio in Göttingen, layers pigment, oil and raw silk into translucent surfaces. See {works}{from_price}."),
}
TITLE_LIMIT, DESCRIPTION_LIMIT = 60, 160


def artist_kind(pkg):
    """'Paintings' or 'Prints' when at least three quarters of the works on show are of that kind (artwork_kind, from the
    artist's own medium wording); otherwise 'Art'."""
    kinds = [artwork_kind(w["medium"]) for w in shown(pkg)]
    for k, plural in (("Painting", "Paintings"), ("Print", "Prints")):
        if kinds and kinds.count(k) * 4 >= len(kinds) * 3:
            return plural
    return "Art"


def artist_standard_meta(pkg):
    """The standard title and description (page fixes, 27 Nov 2026, fix 7), built from the published gallery so no two
    artists share one: the kind of work, the artist's published county, how many works are available and the lowest public
    asking price. The county is where the artist says they are based; nothing is said about nationality."""
    a = pkg["artist"]
    name, kind = a["display_name"], artist_kind(pkg)
    title = next(t for t in ("%s | Original %s for Sale | PlotArt" % (name, kind), "%s | Original %s | PlotArt" % (name, kind),
                             "%s | PlotArt" % name, name) if len(t) <= TITLE_LIMIT or t == name)
    available = [w for w in pkg["works"] if w["availability"] == "available"]
    prices = [w["price_eur"] for w in available if w.get("price_eur") and not w.get("price_on_request")]
    place = (", based in Co. %s" % a["county"]) if a.get("county") and re.fullmatch(r"[A-Z][a-z]+", str(a["county"])) else ""
    lead = "Original %s by %s%s" % ({"Art": "art"}.get(kind, kind.lower()), name, place)
    if available:
        now = "%d %s available%s" % (len(available), "work" if len(available) == 1 else "works", (" from " + euro(min(prices))) if prices else "")
        options = ["%s: %s, with sizes, prices and biography. Enquire through PlotArt." % (lead, now),
                   "%s: %s. Enquire through PlotArt." % (lead, now)]
    else:
        options = ["%s: past works, sizes and biography. Ask through PlotArt about new work." % lead]
    options.append("Original work by %s. View artworks, published prices and the artist biography, and enquire through PlotArt." % name)
    return title, next((d for d in options if len(d) <= DESCRIPTION_LIMIT), options[-1])


def artist_meta(pkg):
    """(title, description) of an artist's gallery page: the standard wording, or the ARTIST_META entry with live figures."""
    a = pkg["artist"]
    standard = artist_standard_meta(pkg)
    if a["slug"] not in ARTIST_META:
        return standard
    title, template = ARTIST_META[a["slug"]]
    available = [w for w in pkg["works"] if w["availability"] == "available"]
    prices = [w["price_eur"] for w in available if w.get("price_eur") and not w.get("price_on_request")]
    works = ("%d original %s" % (len(available), "work" if len(available) == 1 else "works")) if available else "the artist’s original work"
    description = template.format(works=works, from_price=(" from " + euro(min(prices))) if prices else "")
    if len(title) > TITLE_LIMIT or len(description) > DESCRIPTION_LIMIT:
        return standard
    return title, description


def gallery_pages(pkg, page, enquiry_endpoint=None, basket_origin=None):
    """Every page of one artist's gallery: [(path under plotart/, html)]. `page` is the page shell
    (plotart_shell.artist_page in production, build-plotart's page() in the builder)."""
    a = pkg["artist"]
    base = "artists/%s/" % a["slug"]
    scripts = ("plotart.js", "pa-enquiry.js") if enquiry_endpoint else ("plotart.js",)
    art_scripts = scripts + ("pa-basket.js",) if basket_origin else scripts
    title, description = artist_meta(pkg)
    out = [page(base + "index.html", title, description, artist_body(pkg, enquiry_endpoint=enquiry_endpoint), scripts)]
    ws = shown(pkg)
    for i, w in enumerate(ws):
        out.append(page(base + w["slug"] + ".html", artwork_title(pkg, w), artwork_description(pkg, w),
                        artwork_body(pkg, w, ws[i - 1] if i else None, ws[i + 1] if i + 1 < len(ws) else None, enquiry_endpoint=enquiry_endpoint, basket_origin=basket_origin), art_scripts))
    return [(path, SEO.enrich_artist(path, doc, pkg)) for path, doc in out]
