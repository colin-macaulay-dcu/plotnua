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


def pick(img, want):
    ds = img["derivatives"]
    best = [d for d in ds if d["long_edge"] >= want]
    return (best[0] if best else ds[-1])


def main_image(w):
    return next(i for i in w["images"] if i["role"] == "main")


def card_image(pkg):
    """The Virtual Gallery card shows the artist's first (artist-ordered) shown work."""
    w = shown(pkg)[0]
    return w, main_image(w)


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


def artist_body(pkg, blocks=None, preview=False, enquiry_endpoint=None):
    a = pkg["artist"]
    works = shown(pkg)
    name = a["display_name"]
    tiles = []
    for w in works:
        im = main_image(w)
        d = pick(im, 1200)
        cls = " is-%s" % w["availability"].replace("_", "-")
        tiles.append(
            '\n    <li class="pa-ag-work%s"><a class="pa-ag-tile" href="%s.html" data-pa-track="artist_artwork">'
            '<span class="pa-ag-art"><img src="img/%s" srcset="%s" sizes="(max-width:639px) 92vw, (max-width:1023px) 46vw, 31vw" '
            'width="%d" height="%d" alt="%s" loading="lazy" decoding="async"></span>'
            '<span class="pa-ag-cap"><span class="pa-ag-title">%s</span><span class="pa-ag-sub">%s</span>'
            '<span class="pa-ag-status">%s</span></span></a></li>' % (
                cls, E(w["slug"]), E(d["file"]), E(srcset(im, "img/")), d["pixels"][0], d["pixels"][1], E(im["alt"]),
                E(w["title"]), E(" · ".join(x for x in (str(w["year"]) if w.get("year") else None, w["medium"], size_line(w)[0]) if x)),
                E(price_line(w))))
    portrait = ""
    if a.get("portrait"):
        p = a["portrait"]; d = pick(p, 600)
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
  <div class="pa-ag-head"><h2 id="agWorksH">Works</h2><p>%d %s</p></div>
  <ol class="pa-ag-grid">%s
  </ol>
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
       len(works), "artwork" if len(works) == 1 else "artworks", "".join(tiles),
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


def vg_grid(pkgs, spaces=25):
    """The Virtual Gallery collection grid: one card per published artist (in the given order), then the remaining
    numbered spaces up to 25. Shared by build-plotart.py and the production content pipeline."""
    out = []
    for pkg in pkgs:
        a = pkg["artist"]
        w, im = card_image(pkg)
        d = pick(im, 600)
        out.append(("""
    <li class="pa-gcard%s"><a class="pa-gcard-tile" href="../artists/%s/" data-pa-track="vg_artist">
      <span class="pa-gcard-art"><img src="../artists/%s/img/%s" width="%d" height="%d" alt="%s" loading="lazy" decoding="async"></span>
      <span class="pa-gcard-cap">%s<span class="pa-gcard-name">%s</span><span class="pa-gcard-meta">%s</span></span></a></li>""") % (
            " is-founding" if a.get("founding") else "", E(a["slug"]), E(a["slug"]), E(d["file"]), d["pixels"][0], d["pixels"][1], E(im["alt"]),
            '<span class="pa-gcard-badge">Founding Artist</span>' if a.get("founding") else "",
            E(a["display_name"]), E(meta_line(a))))
    for n in range(len(out) + 1, max(spaces, len(out)) + 1):
        out.append("""
    <li class="pa-gspace pa-gspace--t%d" aria-label="Gallery space %02d"><span class="pa-gspace-tile" aria-hidden="true"><span class="pa-gspace-light"></span><span class="pa-gspace-n">%02d</span></span></li>""" % ((n - 1) % 5 + 1, n, n))
    return "".join(out)


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
