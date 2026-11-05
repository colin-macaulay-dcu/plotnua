"""PlotArt artist gallery pages (Phase 1, 29 Oct 2026). Rendered by build-plotart.py from gallery
packages (see plotart_gallery.py). Public fields only; the whole artwork image is always shown
(object-fit: contain), never cropped."""
import html
from urllib.parse import quote

E = lambda s: html.escape(str(s), quote=True)
ENQUIRY_ADDRESS = "hello@plotnua.ie"     # interim pilot route (founder decision 29 Oct 2026); the relay replaces it
ENQUIRY_NOTICE = "PA-ENQ-2026-10-29"     # version of the enquiry notice shown under the form (privacy V8)


def enquiry_form(pkg, w, endpoint):
    """The buyer-to-artist enquiry form (Phase 3). Rendered only when the relay is switched on (an endpoint is given);
    the mailto link stays as the no-JavaScript fallback. pa-enquiry.js reveals and sends it."""
    if not endpoint:
        return ""
    a = pkg["artist"]
    ref = "PA-%s-%s" % (a["slug"], w["id"]) if w else "PA-%s" % a["slug"]
    about = ("“%s”" % E(w["title"])) if w else ("%s's work" % E(a["display_name"]))
    return ('<form class="pa-enq" hidden data-endpoint="%s" data-ref="%s" data-notice="%s" novalidate>'
            '<p class="pa-enq-h">Enquire about %s</p>'
            '<label class="pa-enq-f">Your name<input name="name" required maxlength="80" autocomplete="name"></label>'
            '<label class="pa-enq-f">Your email<input name="email" type="email" required maxlength="254" autocomplete="email"></label>'
            '<label class="pa-enq-f">Your message<textarea name="message" required minlength="10" maxlength="1500" rows="5"></textarea></label>'
            '<p class="pa-enq-notice">PlotArt passes your name, email address and message to %s so they can reply to you directly. '
            '<a href="%sprivacy.html#plotart-enquiries">How we handle enquiries</a></p>'
            '<label class="pa-hp" aria-hidden="true">Leave blank<input name="website" tabindex="-1" autocomplete="off"></label>'
            '<button class="pa-btn pa-btn--solid" type="submit">Send enquiry</button>'
            '<p class="pa-enq-status" role="status" aria-live="polite"></p></form>') % (
        E(endpoint), E(ref), ENQUIRY_NOTICE, about, E(a["display_name"]), "../../../")
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


def pick(img, want):
    ds = img["derivatives"]
    best = [d for d in ds if d["long_edge"] >= want]
    return (best[0] if best else ds[-1])


def main_image(w):
    return next(i for i in w["images"] if i["role"] == "main")


def card_image(pkg):
    """The Virtual Gallery card shows the artist's first (artist-ordered) shown work; (None, None) if none are on show."""
    ws = shown(pkg)
    return (ws[0], main_image(ws[0])) if ws else (None, None)


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
    return " · ".join(x for x in (a.get("practice"), a.get("county")) if x)


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


def artist_body(pkg, blocks=None, preview=False, enquiry_endpoint=None):
    a = pkg["artist"]
    works = shown(pkg)
    name = a["display_name"]
    tiles = []
    # one or two works sit larger and centred (founder decision 1 Nov 2026): the size hint follows the layout
    sizes = {1: "(max-width:639px) 92vw, 720px", 2: "(max-width:639px) 92vw, 520px"}.get(len(works), "(max-width:639px) 92vw, (max-width:1023px) 46vw, 31vw")
    for w in works:
        im = main_image(w)
        d = pick(im, 1200)
        cls = " is-%s" % w["availability"].replace("_", "-")
        tiles.append(
            '\n    <li class="pa-ag-work%s"><a class="pa-ag-tile" href="%s.html" data-pa-track="artist_artwork">'
            '<span class="pa-ag-art"><img src="img/%s" srcset="%s" sizes="%s" '
            'width="%d" height="%d" alt="%s" loading="lazy" decoding="async"></span>'
            '<span class="pa-ag-cap"><span class="pa-ag-title">%s</span><span class="pa-ag-sub">%s</span>'
            '<span class="pa-ag-status">%s</span></span></a></li>' % (
                cls, E(w["slug"]), E(d["file"]), E(srcset(im, "img/")), sizes, d["pixels"][0], d["pixels"][1], E(im["alt"]),
                E(w["title"]), E(" · ".join(x for x in (str(w["year"]) if w.get("year") else None, w["medium"], size_line(w)[0]) if x)),
                E(price_line(w))))
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
    bio = "".join("<p>%s</p>" % E(p.strip()) for p in a["bio"].split("\n\n") if p.strip())
    return """%s
<section class="pa-ag-hero%s"><div class="pa-wrap">
  <nav class="pa-crumb" aria-label="Breadcrumb"><a href="../../gallery/">Virtual Gallery</a><span aria-hidden="true">/</span><span aria-current="page">%s</span></nav>
  <div class="pa-ag-id">%s<div>
    %s<h1>%s</h1>
    %s%s
  </div></div>
</div></section>

<section class="pa-ag-works" aria-labelledby="agWorksH"><div class="pa-wrap">
  <div class="pa-ag-head"><h2 id="agWorksH">Works</h2><p>%s</p></div>
  %s
</div></section>

<section class="pa-ag-about" aria-labelledby="agAboutH"><div class="pa-wrap pa-ag-about-in">
  <h2 id="agAboutH">About %s</h2>
  <div class="pa-ag-bio">%s%s</div>
</div></section>

<section class="pa-ag-enq"><div class="pa-wrap pa-ag-enq-in">
  <p class="pa-ag-enq-t">Interested in %s's work?</p>
  <p class="pa-ag-enq-l">Send an enquiry through PlotArt and we'll put you in touch with the artist.</p>
  <a class="pa-btn pa-btn--solid" href="%s" data-pa-track="artist_enquiry"%s>Enquire through PlotArt</a>%s
</div></section>
""" % (checks_panel(pkg, blocks) if preview else "",
       " has-portrait" if portrait else "", E(name), portrait,
       '<span class="pa-gcard-badge">Founding Artist</span>' if a.get("founding") else "",
       E(name), ('<p class="pa-ag-meta">%s</p>' % E(meta_line(a))) if meta_line(a) else "",
       ('<p class="pa-ag-statement">%s</p>' % E(a["statement"])) if a.get("statement") else "",
       ("%d %s" % (len(works), "artwork" if len(works) == 1 else "artworks")) if works else "None on show right now",
       ('<ol class="pa-ag-grid">%s\n  </ol>' % "".join(tiles)) if works else empty_works(a),
       E(name.split(" ")[0] if " " in name else name), bio,
       ('<p class="pa-ag-links">%s</p>' % "".join(links)) if links else "",
       E(name), E(enquiry_href(pkg)), " data-pa-enquire" if enquiry_endpoint else "", enquiry_form(pkg, None, enquiry_endpoint))


def artwork_body(pkg, w, prev_w, next_w, preview=False, enquiry_endpoint=None):
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
                E(pick(i, 2000)["file"]), E(pick(i, 600)["file"]), E(i["alt"])) for i in imgs[1:])
    credit = ' <span>Photo: %s</span>' % E(im["photo_credit"]) if im.get("photo_credit") else ""
    avail = w["availability"]
    if avail in ("available", "reserved"):
        cta = ('<a class="pa-btn pa-btn--solid" href="%s" data-pa-track="artwork_enquiry"%s>%s</a>'
               '<p class="pa-aw-cta-note">Your enquiry comes to PlotArt and is passed to %s. PlotArt doesn\'t take payment: the artist arranges any sale with you directly.</p>%s') % (
            E(enquiry_href(pkg, w)), " data-pa-enquire" if enquiry_endpoint else "",
            "Enquire about this work" if avail == "available" else "Ask to be told if it becomes available", E(a["display_name"]),
            enquiry_form(pkg, w, enquiry_endpoint))
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
  <nav class="pa-crumb" aria-label="Breadcrumb"><a href="../../gallery/">Virtual Gallery</a><span aria-hidden="true">/</span><a href="index.html">%s</a><span aria-hidden="true">/</span><span aria-current="page">%s</span></nav>
  <div class="pa-aw-in">
    <figure class="pa-aw-fig"><span class="pa-aw-frame"><img src="img/%s" srcset="%s" sizes="(max-width:1023px) 94vw, 62vw" width="%d" height="%d" alt="%s" decoding="async" fetchpriority="high"></span>%s
      <figcaption>%s, <i>%s</i>%s</figcaption></figure>
    <div class="pa-aw-info">
      <p class="pa-aw-artist"><a href="index.html">%s</a>%s</p>
      <h1>%s</h1>
      <p class="pa-aw-price is-%s">%s</p>
      <dl class="pa-aw-dl">%s</dl>
      %s
      <div class="pa-aw-cta">%s</div>
      %s
    </div>
  </div>
  %s
</div></section>
""" % (E(a["display_name"]), E(w["title"]), E(d["file"]), E(srcset(im, "img/")), d["pixels"][0], d["pixels"][1], E(im["alt"]), views,
       E(a["display_name"]), E(w["title"]), credit,
       E(a["display_name"]), ' <span class="pa-gcard-badge">Founding Artist</span>' if a.get("founding") else "",
       E(w["title"]), avail.replace("_", "-"), E(price_line(w)), dl,
       ('<p class="pa-aw-desc">%s</p>' % E(w["description"])) if w.get("description") else "",
       cta, ai, nav)


# ---- The Virtual Gallery collection: Direction C2 "The Curated Collection" (founder approval 5 Nov 2026) ----
# One uncropped representative work per published gallery, equal treatment for every artist, then the twenty-five
# founding positions as an index. The builder writes everything between the two markers below in
# plotart/gallery/index.html (the rest of the page is fixed and pinned by the launch manifest).
VG_BEGIN, VG_END = "<!-- pa-vg-collection:begin -->", "<!-- pa-vg-collection:end -->"
VG_STATES = (("pub", "Published"), ("res", "Reserved"), ("prep", "In preparation"), ("av", "Available"))


def _vg_work(pkg, n):
    """One open gallery on the wall: its first shown work (never cropped), the position numeral, name, practice."""
    a = pkg["artist"]
    w, im = card_image(pkg)
    if im is None:   # no works on show (founder decision 1 Nov 2026): the gallery keeps its place, with the empty state
        art = '<div class="pa-vgc-art is-empty"><span>New work coming soon</span></div>'
    else:
        d = pick(im, 1200)
        art = ('<div class="pa-vgc-art"><img src="../artists/%s/img/%s" srcset="%s" sizes="(max-width:639px) 100vw, 680px" '
               'width="%d" height="%d" alt="%s" loading="lazy" decoding="async"></div>') % (
            E(a["slug"]), E(d["file"]), E(srcset(im, "../artists/%s/img/" % a["slug"])), d["pixels"][0], d["pixels"][1], E(im["alt"]))
    num = "%02d" % n if n else ""
    return """
    <li class="pa-vgc-work">%s
      <div class="pa-vgc-label"><span class="pa-vgc-n" aria-hidden="true">%s</span><div><h3 class="pa-vgc-name"><a href="../artists/%s/" data-pa-track="vg_artist">%s%s</a></h3>
        <p class="pa-vgc-practice">%s</p><span class="pa-vgc-enter" aria-hidden="true">Enter the gallery &rarr;</span></div></div></li>""" % (
        art, num, E(a["slug"]), ('<span class="pa-vgc-sr">Position %s: </span>' % num) if n else "", E(a["display_name"]), E(meta_line(a)))


def _vg_pos(n, state, pkg=None):
    """One of the twenty-five positions in the index. Only a published gallery is named or linked: a reserved
    position, one whose artist is not yet published, and an open one carry their number and state, never a name."""
    word = dict(VG_STATES)[state]
    if state == "pub":
        a = pkg["artist"]
        return ('\n      <li class="pa-vgc-pos is-pub"><a href="../artists/%s/" data-pa-track="vg_index"><b><span class="pa-vgc-sr">Position </span>%02d</b>'
                '<span class="pa-vgc-st"><span class="pa-vgc-sr">: </span>%s</span></a></li>') % (E(a["slug"]), n, E(a["display_name"]))
    return ('\n      <li class="pa-vgc-pos is-%s"><b><span class="pa-vgc-sr">Position </span>%02d</b>'
            '<span class="pa-vgc-st"><span class="pa-vgc-sr">: </span>%s</span></li>') % (state, n, word)


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


def vg_collection(pkgs, spaces=25, layout=None):
    """Everything between VG_BEGIN and VG_END on the Virtual Gallery page: the open-count line, the wall of open
    galleries (in position order, then any without a position) and the index of the twenty-five positions.
    Shared by the production content pipeline (plotart-gallery-publish.py)."""
    positions, extra = vg_positions(pkgs, spaces, layout)
    works = [_vg_work(p, n) for n, st, p in positions if st == "pub"] + [_vg_work(p, None) for p in extra]
    count = {k: sum(1 for _, st, _ in positions if st == k) for k, _ in VG_STATES}
    key = "".join('<li><span class="pa-vgc-k is-%s" aria-hidden="true"></span><b>%d</b> %s</li>' % (k, count[k], w.lower())
                  for k, w in VG_STATES if count[k])
    line = "".join('<li class="is-%s"></li>' % st for _, st, _ in positions)
    opened = len(works)
    hang = ('\n  <ol class="pa-vgc-hang n-%s" aria-label="Open galleries">%s\n  </ol>' % (min(opened, 3), "".join(works))) if works else ""
    return """%s
  <p class="pa-vgc-count">%d of %d galleries open</p>%s
  <div class="pa-vgc-index" role="region" aria-labelledby="vgIdxH">
    <h3 id="vgIdxH">Founding positions</h3>
    <p class="pa-vgc-note">Twenty-five numbered positions, one for each Founding Artist. A gallery opens here when the artist&rsquo;s work is published.</p>
    <ol class="pa-vgc-line" aria-hidden="true">%s</ol>
    <ul class="pa-vgc-key" aria-label="Summary of the twenty-five positions">%s</ul>
    <ol class="pa-vgc-plan" aria-label="The twenty-five positions">%s
    </ol>
  </div>
  %s""" % (VG_BEGIN, opened, spaces, hang, line, key, "".join(_vg_pos(n, st, p) for n, st, p in positions), VG_END)


def vg_region(html_text):
    """(start, end) of the generated collection region, markers included; None if the page has no such region."""
    a = html_text.find(VG_BEGIN)
    b = html_text.find(VG_END, a + 1) if a >= 0 else -1
    if a < 0 or b < 0 or html_text.count(VG_BEGIN) != 1 or html_text.count(VG_END) != 1:
        return None
    return a, b + len(VG_END)


def gallery_order(pkgs):
    return sorted(pkgs, key=lambda p: (p["publication"].get("approved_at") or "9999", p["artist"]["display_name"]))


def gallery_pages(pkg, page, enquiry_endpoint=None):
    """Every page of one artist's gallery: [(path under plotart/, html)]. `page` is the page shell
    (plotart_shell.artist_page in production, build-plotart's page() in the builder)."""
    a = pkg["artist"]
    base = "artists/%s/" % a["slug"]
    scripts = ("plotart.js", "pa-enquiry.js") if enquiry_endpoint else ("plotart.js",)
    out = [page(base + "index.html", "%s | Virtual Gallery | PlotArt" % a["display_name"],
                (a.get("statement") or "Original work by %s in the PlotArt Virtual Gallery." % a["display_name"]),
                artist_body(pkg, enquiry_endpoint=enquiry_endpoint), scripts)]
    ws = shown(pkg)
    for i, w in enumerate(ws):
        out.append(page(base + w["slug"] + ".html", "%s by %s | PlotArt" % (w["title"], a["display_name"]),
                        "%s by %s. %s, %s." % (w["title"], a["display_name"], w["medium"], size_line(w)[0]),
                        artwork_body(pkg, w, ws[i - 1] if i else None, ws[i + 1] if i + 1 < len(ws) else None, enquiry_endpoint=enquiry_endpoint), scripts))
    return out
