"""PlotArt · artist opportunity lists (development 16 Nov 2026; founder approval of the architecture and destinations).

Every opportunity an artist can choose in PlotArt Studio has a public list of the PUBLISHED artists who chose to show it,
each name linking to that artist's existing gallery. The ONLY input is the set of approved public gallery packages
(plotart/artists/<slug>/gallery.json), written by the content pipeline from founder-approved Studio exports:
  - an artist appears only while their gallery is published (no package, no listing);
  - an artist appears under an opportunity only while their package carries it in "open_to" (the artist's own choice,
    published as an instant update); EXCEPT Commissions (founder decision 17 Nov 2026), which is shown ONLY while the
    artist's explicit "Open for commissions" setting is on (the setting the enquiry relay checks), whatever open_to says:
    no artist is publicly described as open to commissions unless commission enquiries can actually reach them;
  - nothing else about an artist's Opportunities answers ever reaches the website (the Studio never exports it).

Destinations (founder approval, 16 Nov 2026):
  Living Gallery        plotart/living-gallery.html          (its own page)
  Art for Hire          plotart/art-for-hire/index.html      (its own page, below and separate from the works approved for hire)
  Mobile Gallery        plotart/mobile-gallery/index.html    (its own page)
  all seven             plotart/opportunities/index.html     (new page, outside the main navigation; noindex until the SEO
                                                              workstream decides)
  Commissions           plotart/commissions/index.html       (17 Nov 2026: its own page, outside the main navigation; noindex
                                                              until the SEO workstream decides)
Each page holds ONE generated region (BEGIN ... END). Everything outside it is fixed by the code release and pinned in the
launch manifest; the content pipeline may change only the region, and only to exactly what update() produces from the
published packages (atlas-tools/release/plotart-content-boundary.py checks that).
"""
import plotart_featured as FEAT
import plotart_seo as SEO   # generated search descriptions (26 Nov 2026)   # the founder's representative artworks (one curated gallery, 26 Nov 2026)
import html
import re
from pathlib import Path

E = lambda s: html.escape(str(s), quote=True)
BEGIN, END = "<!-- pa-opportunity-artists:begin -->", "<!-- pa-opportunity-artists:end -->"
REGION = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
HUB = "opportunities/index.html"
COMMISSIONS = "commissions/index.html"

# key: (short label, list heading, what the artists said, programme page or None, anchor on the opportunities page)
OPPORTUNITIES = {
    "exhibitions": ("Exhibitions", "Artists open to exhibitions",
                    "These artists have said they’d welcome conversations about showing their work in physical gallery exhibitions.", None, "exhibitions"),
    "living_gallery": ("Living Gallery", "Artists open to the Living Gallery",
                       "These artists have said they’d welcome conversations about showing their work in someone’s home.", "living-gallery.html", "living-gallery"),
    "art_for_hire": ("Art for Hire", "Artists open to Art for Hire",
                     "These artists have said they’d welcome conversations about hiring out their work. Only the works shown under “Available to hire” have been approved for hire; being listed here doesn’t mean a particular work is available.",
                     "art-for-hire/", "art-for-hire"),
    "mobile_gallery": ("Mobile Gallery", "Artists open to home viewings",
                       "These artists have said they’d welcome conversations about home viewings arranged through participating galleries. No gallery’s participation has been confirmed yet.",
                       "mobile-gallery/", "mobile-gallery"),
    "venues": ("Hotels and workplaces", "Artists open to hotel and workplace displays",
               "These artists have said they’d welcome conversations about showing their work in hotels, offices and other workplaces.", None, "hotels-and-workplaces"),
    "commissions": ("Commissions", "Artists open to commissions",
                    "These artists are currently open to commission enquiries about a new work. Any commission is agreed directly between the artist and the client.", "commissions/", "commissions"),
    "talks": ("Talks and events", "Artists open to talks and events",
              "These artists have said they’d welcome conversations about artist talks and events.", None, "talks-and-events"),
}
KEYS = tuple(OPPORTUNITIES)
NOTE = "Every opportunity is discussed and agreed individually with the artist. Being listed is not a booking, and nothing is confirmed until it’s agreed."
# Which list each page carries (plotart/<path>): the three programme pages carry their own; the opportunities page all seven.
PAGES = {"living-gallery.html": ("living_gallery",), "art-for-hire/index.html": ("art_for_hire",),
         "mobile-gallery/index.html": ("mobile_gallery",), COMMISSIONS: ("commissions",), HUB: KEYS}
MEDIUM = {"painting": "Painting", "drawing": "Drawing", "works_on_paper": "Works on paper", "printmaking": "Printmaking", "photography": "Photography",
          "sculpture": "Sculpture", "ceramics_craft": "Ceramics and craft", "textiles": "Textiles", "mixed_media": "Mixed media",
          "digital_new_media": "Digital and new media", "other": ""}


class Refused(ValueError):
    pass


def check_open_to(v):
    """The gallery export's optional open_to: a non-empty list of known opportunity keys, no repeats, in the fixed order."""
    if not isinstance(v, list) or not v or any(not isinstance(k, str) or k not in OPPORTUNITIES for k in v) or len(set(v)) != len(v) \
            or v != [k for k in KEYS if k in v]:
        raise Refused("open_to must be a non-empty list of known opportunities, in the fixed order, without repeats")
    return v


def open_to(pkg):
    """The opportunities this published artist is listed under. Commissions follows ONLY the explicit "Open for
    commissions" setting (17 Nov 2026): choosing Commissions among the opportunities without it shows nothing publicly."""
    a = pkg["artist"]
    keys = set(a.get("open_to") or []) - {"commissions"}
    if a.get("open_for_commissions") is True:
        keys.add("commissions")
    return [k for k in KEYS if k in keys]


def href(key, base):
    """Where an opportunity is listed, relative to the PlotArt root through `base` ("" from plotart/, "../" one level down)."""
    label, head, said, page, anchor = OPPORTUNITIES[key]
    if key == "commissions":
        return base + page            # the Commissions page explains how a commission works before its list
    return base + (page + "#open-artists" if page else "opportunities/#" + anchor)


def _surname(pkg):
    n = pkg["artist"]["display_name"].strip()
    return (n.split()[-1].lower(), n.lower(), pkg["artist"]["slug"])


def listed(packages, key):
    """Published artists listed under `key`, by surname (neutral: never by position, fee or anything else)."""
    out = []
    for p in packages:
        if p.get("publication", {}).get("state") != "approved":
            raise Refused("an unapproved gallery package was offered to the opportunity lists")
        if key in open_to(p):
            out.append(p)
    return sorted(out, key=_surname)


def _rep(pkg, choice=None):
    """(work, main image) for the artist: the founder's representative artwork from Curate while it is eligible (shown and
    available in the approved gallery, with a main photograph), else their first eligible work; with none eligible, the
    main photograph of the FIRST work in their own published order (founder decision 16 Nov 2026). The same choice the
    gallery page shows (founder requirement 26 Nov 2026: curate each artist's image once). Only an approved package's own
    artwork is ever used: never the portrait, never anything generated or unpublished."""
    w, im = FEAT.representative(pkg, choice)
    if w is not None:
        return w, im
    for w in pkg.get("works") or []:
        for im in w.get("images") or []:
            if im.get("role") == "main" and im.get("derivatives"):
                return w, im
    return None, None


def thumb(pkg, choice=None):
    """The listing thumbnail: the representative artwork (_rep) at its smallest published size; None when there is none."""
    w, im = _rep(pkg, choice)
    if im is None:
        return None
    d = min(im["derivatives"], key=lambda x: x["long_edge"])
    return d["file"], (im.get("alt") or w.get("title") or "").strip(), w.get("title") or ""


# Commissions page price guide (growth round 2, 27 Nov 2026). Under each listed artist: the lowest and highest PUBLIC asking
# price of their works AVAILABLE on PlotArt right now (never "price on request", reserved, sold or withdrawn work), from
# the same approved gallery package as the list itself and refreshed with it at every publication. It is labelled as a
# guide to the artist's current prices, never as a commission price: a commission is priced by the artist. Nothing is
# shown for an artist with no publicly priced available work.
def price_guide(pkg):
    prices = sorted(w["price_eur"] for w in pkg.get("works") or []
                    if w.get("availability") == "available" and w.get("price_eur") and not w.get("price_on_request"))
    if not prices:
        return ""
    eur = lambda n: "€{:,}".format(int(n) if float(n) == int(n) else n)
    span = eur(prices[0]) if prices[0] == prices[-1] else "%s to %s" % (eur(prices[0]), eur(prices[-1]))
    return "Price guide: %s %s" % ("available work" if len(prices) == 1 else "available works", span)


def _rows(pkgs, base, commission_page=False, choices=None):
    def line(p):
        a = p["artist"]
        what = a.get("practice") or MEDIUM.get(a.get("medium"), "")
        guide = price_guide(p) if commission_page else ""
        name = ('<span class="pa-opp-who"><span class="pa-opp-name">%s</span><span class="pa-opp-price">%s</span></span>' % (E(a["display_name"]), E(guide))
                if guide else '<span class="pa-opp-name">%s</span>' % E(a["display_name"]))
        t = thumb(p, (choices or {}).get(a["slug"]))
        img = ('<img class="pa-opp-thumb" src="%sartists/%s/img/%s" alt="%s" width="80" height="80" loading="lazy" decoding="async">'
               % (base, E(a["slug"]), E(t[0]), E(t[1] or ("Artwork by " + a["display_name"])))) if t else '<span class="pa-opp-thumb" aria-hidden="true"></span>'
        # on the Commissions page, an artist whose "Open for commissions" is on links straight to their commission enquiry
        frag = "#commission" if commission_page and a.get("open_for_commissions") is True else ""
        return ('<li><a class="pa-opp-row" href="%sartists/%s/%s" data-pa-track="opportunity_artist">%s%s%s</a></li>'
                % (base, E(a["slug"]), frag, img, name, ('<span class="pa-opp-what">%s</span>' % E(what)) if what else ""))
    return '<ul class="pa-opp-list">%s</ul>' % "".join(line(p) for p in pkgs)


# Art for Hire page (founder brief 22 Nov 2026): the same list, shown as an artwork-led mini gallery straight after the hero.
# The SAME published artists and the SAME artwork (the first work's main photograph, as thumb() chooses), at a larger
# published size; never cropped (contained in its frame). These are artists open to discussing hire: the page never says a
# particular work is available for hire. Up to GALLERY_FIRST cards show at once; any others are one click away.
GALLERY_FIRST = 8
HIRE_SAID = "Original work from PlotArt artists who welcome hire and rental. Every placement is arranged through PlotArt."   # communication standard, founder approval 27 Nov 2026
HIRE_HEAD = "Artists open to hire."
HIRE_INVITE = ('<h3>Seen a work you like?</h3><p>Tell us which piece, and where it would go. Rental enquiries come through PlotArt: we confirm availability, price and dates with the artist for you.</p>'
               '<p class="afx-acts"><a class="afx-btn" href="mailto:hello@plotnua.ie?subject=Art%20for%20Hire%3A%20a%20specific%20work" data-pa-track="hire_ask_work">Ask about a work</a></p>')


def gallery_image(pkg, choice=None):
    """The thumb() artwork at a card size: (src file, srcset, width, height, alt), or None."""
    w, im = _rep(pkg, choice)
    if im is None:
        return None
    ds = sorted(im["derivatives"], key=lambda x: x["long_edge"])
    mid = next((d for d in ds if d["long_edge"] >= 600), ds[-1])
    return mid, ds, (im.get("alt") or w.get("title") or "").strip()


def _gallery(pkgs, base, key="art_for_hire", choices=None):
    def card(p):
        a = p["artist"]
        what = a.get("practice") or MEDIUM.get(a.get("medium"), "")
        g = gallery_image(p, (choices or {}).get(a["slug"]))
        root = "%sartists/%s/img/" % (base, E(a["slug"]))
        if g:
            mid, ds, alt = g
            art = ('<img src="%s%s" srcset="%s" sizes="(max-width:639px) 46vw, (max-width:1023px) 31vw, 23vw" width="%d" height="%d" alt="%s" loading="lazy" decoding="async">'
                   % (root, E(mid["file"]), E(", ".join("%s%s %dw" % (root, d["file"], d["pixels"][0]) for d in ds)), mid["pixels"][0], mid["pixels"][1],
                      E(alt or ("Artwork by " + a["display_name"]))))
        else:
            art = ""
        return ('<li><a class="pa-afg-card" href="%sartists/%s/" data-pa-track="opportunity_artist"><span class="pa-afg-art">%s</span>'
                '<span class="pa-afg-name">%s</span>%s<span class="pa-afg-go">View gallery</span></a></li>'
                % (base, E(a["slug"]), art, E(a["display_name"]), ('<span class="pa-afg-what">%s</span>' % E(what)) if what else ""))
    first, rest = pkgs[:GALLERY_FIRST], pkgs[GALLERY_FIRST:]
    out = '<ul class="pa-afg-grid">%s</ul>' % "".join(card(p) for p in first)
    if rest:
        out += ('<details class="pa-afg-all"><summary>View all %s <span>(%d)</span></summary><ul class="pa-afg-grid">%s</ul></details>'
                % (E(OPPORTUNITIES[key][1][0].lower() + OPPORTUNITIES[key][1][1:]), len(pkgs), "".join(card(p) for p in rest)))
    return out


# Pages that show their list as the artwork-led mini gallery: Art for Hire (22 Nov 2026) and the Living Gallery (preview,
# 22 Nov 2026). The Living Gallery has its own introduction (founder wording) and no invitation.
GALLERY_PAGES = ("art-for-hire/index.html", "living-gallery.html")
LIVING_SAID = ("Discover Irish artists interested in seeing their work displayed in real homes. Explore their galleries and find out "
               "how you could become part of the Living Gallery. Every arrangement is agreed directly with the artist.")   # founder wording, 22 Nov 2026


def section(key, packages, base, hub, commission_page=False, gallery=False, choices=None):
    label, head, said, page, anchor = OPPORTUNITIES[key]
    pkgs = listed(packages, key)
    if not pkgs and not hub:
        return ""          # a programme page shows nothing until someone is listed (the region stays, empty)
    sid = anchor if hub else "open-artists"
    if gallery and key == "living_gallery":      # the Living Gallery's artwork-led mini gallery (preview, 22 Nov 2026)
        return ('<section class="pa-opp pa-afg pa-lgg" id="%s" aria-labelledby="opp-%s-h"><div class="pa-wrap">\n'
                '  <div class="pa-afg-head"><h2 id="opp-%s-h">%s</h2><p class="pa-opp-said">%s</p></div>\n  %s\n'
                '  <p class="pa-opp-more"><a href="%sopportunities/">Every artist opportunity →</a></p>\n</div></section>'
                % (sid, key, key, E(head), E(LIVING_SAID), _gallery(pkgs, base, key, choices), E(base)))
    if gallery:      # the Art for Hire page's artwork-led mini gallery (22 Nov 2026)
        return ('<section class="pa-opp pa-afg" id="%s" aria-labelledby="opp-%s-h"><div class="pa-wrap">\n'
                '  <div class="pa-afg-head"><h2 id="opp-%s-h">%s</h2><p class="pa-opp-said">%s</p></div>\n  %s\n'
                '  <div class="pa-afg-invite">%s</div>\n</div></section>'
                % (sid, key, key, E(HIRE_HEAD), E(HIRE_SAID), _gallery(pkgs, base, choices=choices), HIRE_INVITE))
    about = {"art_for_hire": "About Art for Hire", "commissions": "About commissions"}.get(key, "About the " + label)
    more = ('<p class="pa-opp-more"><a href="%s">%s →</a></p>' % (E(base + page), E(about))) if hub and page else \
           ('<p class="pa-opp-more"><a href="%sopportunities/">Every artist opportunity →</a></p>' % E(base)) if not hub else ""
    body = _rows(pkgs, base, commission_page, choices) if pkgs else '<p class="pa-opp-none">No artists are listed here yet.</p>'
    return ('<section class="pa-opp" id="%s" aria-labelledby="opp-%s-h"><div class="pa-wrap pa-opp-in">\n'
            '  <h2 id="opp-%s-h">%s</h2>\n  <p class="pa-opp-said">%s %s</p>\n  %s\n  %s\n</div></section>'
            % (sid, key, key, E(head), E(said), E(NOTE), body, more))


def content(path, packages, choices=None):
    """choices: {gallery address: artwork id}, the founder's representative artworks (plotart_featured.choices_in of the
    gallery page); None or {} = each artist's first eligible work."""
    hub = path == HUB
    base = "../" * path.count("/")
    return "\n".join(s for s in (section(k, packages, base, hub, path == COMMISSIONS, gallery=path in GALLERY_PAGES, choices=choices) for k in PAGES[path]) if s)


# The commissions page's search title and description (SEO and analytics package, founder approval 26 Nov 2026, section
# 2.4): the number of artists is the number this page lists (open to commissions), computed from the published galleries
# and refreshed with the list at every publication; it is never typed in.
COMMISSIONS_TITLE = "Commission Original Art in Ireland | PlotArt"
COMMISSIONS_LEAD = "Commission a new painting or print from a PlotArt artist."
NUMBER_WORDS = ("No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve")


def commissions_meta(packages):
    n = len(listed(packages, "commissions"))
    if not n:
        return COMMISSIONS_TITLE, COMMISSIONS_LEAD + " Size, price and timescale are agreed with the artist."
    who = "%s PlotArt %s" % (NUMBER_WORDS[n] if n < len(NUMBER_WORDS) else str(n), "artist welcomes" if n == 1 else "artists welcome")
    return COMMISSIONS_TITLE, "%s %s enquiries; size, price and timescale are agreed with the artist." % (COMMISSIONS_LEAD, who)


def update(document, path, packages, choices=None):
    if document.count(BEGIN) != 1 or document.count(END) != 1 or not REGION.search(document):
        raise Refused("Missing or duplicate opportunity region in plotart/" + path)
    inner = content(path, packages, choices)
    document = REGION.sub(lambda m: BEGIN + ("\n" + inner + "\n" if inner else "") + END, document, count=1)
    return SEO.set_meta(document, *commissions_meta(packages)) if path == COMMISSIONS and "<head>" in document else document


def outside(document):
    """The page with its opportunity region blanked out (what the launch manifest pins). On the commissions page the
    generated description (it carries the number of artists) is blanked too; update() == page (guard L19, the content
    boundary) pins it instead."""
    if document.count(BEGIN) != 1 or document.count(END) != 1 or not REGION.search(document):
        raise Refused("Missing or duplicate opportunity region")
    document = REGION.sub(BEGIN + "<!-- opportunity artists -->" + END, document, count=1)
    return SEO.blank_meta(document) if 'name="description" content="%s' % COMMISSIONS_LEAD in document else document


def refresh(root, packages, choices=None):
    """Rewrite every opportunity region from the published packages (the content pipeline, after each gallery change),
    with the representative artworks published on the gallery page unless given."""
    ch = FEAT.choices(root) if choices is None else choices
    for path in PAGES:
        dest = Path(root) / "plotart" / path
        if dest.exists():
            dest.write_text(update(dest.read_text(encoding="utf-8"), path, packages, ch), encoding="utf-8")


def artist_line(pkg, base="../../"):
    """The artist's own gallery page (17 Nov 2026): "Open to" as a row of pills, each linking to its list (Commissions to the
    Commissions page). The same opportunities the lists show (open_to, plus Commissions while "Open for commissions" is on);
    empty when the artist shows nothing. Styled by plotart.css (.pa-ag-opps)."""
    a = pkg["artist"]
    if a.get("open_to"):
        check_open_to(a["open_to"])
    keys = open_to(pkg)
    if not keys:
        return ""
    return ('<div class="pa-ag-opps"><p class="pa-ag-opps-h" id="agOppsH">Open to</p><ul class="pa-ag-pills" aria-labelledby="agOppsH">%s</ul></div>'
            % "".join('<li><a class="pa-ag-pill" href="%s" data-pa-track="artist_opportunity_link">%s</a></li>'
                      % (E(href(k, base)), E(OPPORTUNITIES[k][0])) for k in keys))
