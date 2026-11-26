#!/usr/bin/env python3
"""PlotArt · Art for Hire page builder (Stage 3B-4, development 10 Nov 2026). NOT RUN ON THE PUBLIC SITE.

Writes ROOT/plotart/art-for-hire/ (index.html, art-for-hire.css, hire-live.js) from:
  * the Studio's hire catalogue (GET /api/pipeline/hire-catalogue: listed works only, approved public fields only), and
  * each artist's EXISTING published gallery (ROOT/plotart/artists/<slug>/gallery.json) for the image, title, medium and
    size. Images are the files already published in plotart/artists/<slug>/img/: nothing is copied or re-cropped.

  python3 atlas-tools/plotart-hire-page.py ROOT --catalogue FILE --api https://<relay> [--enquiries-form]

Refuses (writes nothing) if a catalogue row names a work that is not in that artist's approved, published gallery and
available there, or carries any private field. Every card is written HIDDEN: the page script shows a card only while the
live check confirms it (fails closed). With no listed works the page shows its empty state and nothing else.
--enquiries-form is for the founder's release after legal and privacy approval; without it no enquiry form exists."""
import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plotart_shell as SHELL  # noqa: E402
import plotart_business_rental as BUSINESS
import plotart_hire_scenes as SCENES  # noqa: E402
import plotart_opportunities as OPP  # noqa: E402  (artist opportunity lists, 16 Nov 2026)
import plotart_featured as FEAT  # noqa: E402  (representative artworks, 26 Nov 2026)
import plotart_seo as SEO  # noqa: E402
import plotart_gallery as G  # noqa: E402  (the 32 counties)

E = lambda s: html.escape(str(s), quote=True)
PUBLIC_HIRE = os.path.join(HERE, "..", "worker", "plotart-studio", "public-hire")
GALLERY_TITLES = {"contemporary": "Contemporary", "spaces": "Spaces", "being": "Being"}
PROVINCES = (("Connacht", ("Galway", "Leitrim", "Mayo", "Roscommon", "Sligo")),
             ("Leinster", ("Carlow", "Dublin", "Kildare", "Kilkenny", "Laois", "Longford", "Louth", "Meath", "Offaly", "Westmeath", "Wexford", "Wicklow")),
             ("Munster", ("Clare", "Cork", "Kerry", "Limerick", "Tipperary", "Waterford")),
             ("Ulster", ("Antrim", "Armagh", "Cavan", "Derry", "Donegal", "Down", "Fermanagh", "Monaghan", "Tyrone")))
FORBIDDEN = {"handling_note", "artist_email", "email", "replacement_value", "price_eur", "fee", "private"}
TITLE = "Art for Hire: Original Irish Art for Businesses | PlotArt"   # SEO and analytics package, 26 Nov 2026 (section 2.4)
DESC = ("Proposed terms for renting original Irish art for offices: six-month terms and a clear monthly charge based on the agreed "
        "price. Rentals are being prepared.")
FINE = ("Works offered for hire are listed by their artists and checked by PlotArt. PlotArt introduces hirers to artists: it doesn't take "
        "artwork rent or deposits, arrange transport or insure work. Any PlotArt fee is separately agreed and invoiced. Photographs of artworks are supplied by the artist and credited where taken by someone else.")


class Refused(Exception):
    pass


def size_line(w):
    dims = [w.get("h_cm"), w.get("w_cm")] + ([w["d_cm"]] if w.get("d_cm") else [])
    return " × ".join("%g" % v for v in dims) + " cm" if all(dims[:2]) else None


def card(item, artist, w):
    img = next(i for i in w["images"] if i["role"] == "main")
    base = "../artists/%s/img/" % artist["slug"]
    ds = img["derivatives"]
    mid = next((d for d in ds if d["long_edge"] >= 1200), ds[-1])
    srcset = ", ".join("%s%s %dw" % (base, d["file"], d["pixels"][0]) for d in ds)
    rows = [("Medium", w.get("medium"))]
    if size_line(w):
        rows.append(("Size", size_line(w)))
    county = (item.get("hire") or {}).get("county")
    if county:
        rows.append(("Location", county if county.lower().startswith(("co. ", "county ")) else "Co. " + county))
    rows.append(("Availability", None))
    dl = "".join('<dt>%s</dt><dd>%s</dd>' % (k, E(v)) if v is not None else '<dt>%s</dt><dd data-hire-availability>Checking…</dd>' % k for k, v in rows if v or k == "Availability")
    ref = "PA-%s-%s" % (artist["slug"], w["id"])
    fx = facets(item, artist)
    # Links (11 Nov 2026): the title opens the work's page in the artist's gallery, the artist line opens the gallery itself.
    # data-hire-artist-slug / data-hire-slug let the artist's gallery mark this work while the live check lists it (plotart.js).
    gal = "../artists/%s/" % artist["slug"]
    return ('<li class="pa-hire-card" data-hire-work="%s" data-hire-ref="%s" data-hire-title="%s" data-hire-artist="%s" data-hire-artist-slug="%s" data-hire-slug="%s"%s hidden>\n'
            '  <figure class="pa-hire-art"><a href="%s%s.html" tabindex="-1" aria-hidden="true"><img src="%s%s" srcset="%s" sizes="(max-width:639px) 92vw, (max-width:1100px) 44vw, 30vw" width="%d" height="%d" alt="%s" loading="lazy" decoding="async"></a></figure>\n'
            '  <p class="pa-hire-artist"><a href="%s">%s</a></p>\n  <p class="pa-hire-rel" data-hire-rel hidden></p>\n  <h3><a href="%s%s.html">%s</a></h3>\n  <dl class="pa-hire-dl">%s</dl>\n'
            '  <p class="pa-hire-more"><a href="%s">See more by %s<span class="pa-sr"> in the Artists’ Gallery</span></a></p>\n'
            '  <button type="button" class="pa-btn pa-btn--ghost" data-hire-enquire aria-describedby="pa-hire-closed">Enquire about hire<span class="pa-sr"> of %s by %s</span></button>\n</li>') % (
        E(w["id"]), E(ref), E(w["title"]), E(artist["display_name"]), E(artist["slug"]), E(w["slug"]), fx["attrs"],
        gal, E(w["slug"]), base, E(mid["file"]), E(srcset), mid["pixels"][0], mid["pixels"][1], E(img.get("alt") or w["title"]),
        gal, E(artist["display_name"]), gal, E(w["slug"]), E(w["title"]), dl, gal, E(artist["display_name"]), E(w["title"]), E(artist["display_name"]))


def open_galleries():
    """Galleries a visitor can filter by: Contemporary, and Spaces or Being only once its own launch switch says open."""
    sw = SHELL.SEO.switches()
    return [g for g in GALLERY_TITLES if g == "contemporary" or sw.get("%s_gallery_state" % g) == "open"]


def facets(item, artist):
    """Public facts for the filters (Phase C, 25 Nov 2026), all already public:
    - in: the county the artist shows publicly on their gallery (published package), else the county the work is listed in;
    - delivers: the counties the artist delivers to, present only when public delivery is switched on in the Studio;
    - galleries: the galleries the work is in, limited to galleries open to visitors."""
    loc = artist.get("location") or {}
    where = loc.get("county") if loc.get("county") in G.COUNTIES else None
    if not where:
        c = re.sub(r"^(co\.|county)\s+", "", str((item.get("hire") or {}).get("county") or ""), flags=re.I).strip().title()
        where = c if c in G.COUNTIES else None
    fa = item.get("facets") or {}
    delivers = [c for c in fa.get("delivers", []) if c in G.COUNTIES and c != where]
    gals = [g for g in fa.get("galleries", []) if g in open_galleries()]
    attrs = "".join(' %s="%s"' % (k, E(v)) for k, v in (("data-hire-in", where), ("data-hire-delivers", "|".join(delivers)), ("data-hire-galleries", "|".join(gals))) if v)
    return {"in": where, "delivers": delivers, "galleries": gals, "attrs": attrs}


def filters(rows):
    """The filter bar (Phase C): built only from what the listed cards carry. Hidden until the live check shows works."""
    fx = [facets(it, a) for it, a, w in rows]
    places = {f["in"] for f in fx if f["in"]} | {c for f in fx for c in f["delivers"]}
    gals = [g for g in GALLERY_TITLES if any(g in f["galleries"] for f in fx)]
    where = "".join('<optgroup label="%s">%s</optgroup>' % (p, "".join('<option value="%s">Co. %s</option>' % (c, c) for c in cs if c in places))
                    for p, cs in PROVINCES if any(c in places for c in cs))
    sel = lambda k, lab, opts: ('<div class="pa-hire-fl"><label for="hfl-%s">%s</label><select id="hfl-%s" data-hire-filter="%s">%s</select></div>' % (k, lab, k, k, opts))
    parts = [sel("where", "Where", '<option value="">Anywhere</option>' + where) if places else "",
             sel("gallery", "Gallery", '<option value="">All galleries</option>' + "".join('<option value="%s">%s</option>' % (g, GALLERY_TITLES[g]) for g in gals)) if len(gals) > 1 else "",
             sel("when", "Availability", '<option value="">Any time</option><option value="now">Available now</option>')]
    return ('<form class="pa-hire-filters" data-hire-filters aria-label="Filter works for hire" hidden>%s<p class="pa-hire-count" data-hire-count aria-live="polite"></p></form>\n'
            '  <p class="pa-hire-note" data-hire-nomatch hidden>No works match these choices. <button type="button" class="pa-hire-clear" data-hire-clear>Show all works</button></p>' % "".join(parts))


def resolve(root, catalogue):
    items = catalogue.get("items")
    if not isinstance(items, list):
        raise Refused("catalogue has no items list")
    out, seen = [], set()
    for it in items:
        bad = FORBIDDEN & set(it) | FORBIDDEN & set(it.get("hire") or {})
        if bad:
            raise Refused("catalogue row %s carries private fields: %s" % (it.get("artwork_id"), ", ".join(sorted(bad))))
        slug, wid = it.get("artist_slug"), it.get("artwork_id")
        gp = os.path.join(root, "plotart", "artists", str(slug), "gallery.json")
        if not slug or not wid or not os.path.isfile(gp):
            raise Refused("catalogue row %s: no published gallery for %r" % (wid, slug))
        pkg = json.load(open(gp, encoding="utf-8"))
        if (pkg.get("publication") or {}).get("state") != "approved" or pkg["artist"]["slug"] != slug:
            raise Refused("catalogue row %s: gallery for %s is not an approved publication" % (wid, slug))
        w = next((x for x in pkg["works"] if x["id"] == wid), None)
        if not w or w.get("availability") != "available":
            raise Refused("catalogue row %s: not an available work in %s's published gallery" % (wid, slug))
        if wid in seen:
            raise Refused("catalogue row %s appears twice" % wid)
        fa = it.get("facets")
        if fa is not None:     # Phase C filters (25 Nov 2026): public facets only, from the Studio's catalogue
            if (not isinstance(fa, dict) or not set(fa) <= {"delivers", "galleries"}
                    or not isinstance(fa.get("delivers", []), list) or any(c not in G.COUNTIES for c in fa.get("delivers", []))
                    or not isinstance(fa.get("galleries", []), list) or any(g not in GALLERY_TITLES for g in fa.get("galleries", []))):
                raise Refused("catalogue row %s: facets must be public delivery counties and gallery names only" % wid)
        seen.add(wid)
        out.append((it, pkg["artist"], w))
    return out


def body(cards, api, form, bar=""):
    # Version 3 (founder approval, 11 Nov 2026). The hero's primary action ships as "How it works"; hire-live.js turns it into
    # "See works for hire" only while the live check is showing approved works (data-hire-cta).
    # Premium redesign (founder brief, 16 Nov 2026): one page with a clear path for each audience. Hero, then who it is for,
    # how a hire works, the settings, the catalogue, and (while business rental information is switched on) the bounded
    # business, artist and contact sections. No new forms, data or services; every term and statement is kept.
    business_on = SHELL.SEO.switches().get("business_rental_information") is True
    return """
<section class="afh3-hero" aria-labelledby="afh3-h">
  <div class="afh3-hero-art"><img src="%(art)s" alt="%(alt)s" width="1332" height="940" fetchpriority="high"></div>
  <div class="afh3-hero-copy">
    <h1 id="afh3-h">Original art,<br>on hire.</h1>
    <div class="afh3-hero-row">
      <p class="afh3-sub">Show original work by Irish artists without buying it outright: for film and television, interiors and staged homes, or the walls of your workplace. You agree each hire directly with the artist.</p>
      <p class="afh3-cta"><a class="afh3-btn" href="#afh3-how" data-hire-cta>How it works</a><a class="afh3-link" href="mailto:hello@plotnua.ie?subject=Art%%20for%%20Hire%%20brief">Send a brief</a></p>
    </div>
  </div>
  <p class="afh3-hero-credit">%(credit)s</p>
</section>
<p class="afh3-hero-credit-m">%(credit)s</p>

%(opportunities)s

<section class="afh3-how" id="afh3-how" aria-labelledby="afh3-how-h"><div class="pa-wrap">
  <div class="afh3-how-head"><h2 id="afh3-how-h">How Art for Hire works</h2><p>Three steps, agreed directly between you and the artist.%(business_how)s</p></div>
  <ol class="afh3-steps">
    <li><h3>Discover an artist</h3><p>Browse the artists open to Art for Hire and their galleries, and find work that suits your production, interior or space.</p></li>
    <li><h3>Make an enquiry</h3><p>Tell the artist which work interests you, your dates, where the work will go and how it will be used. Your enquiry goes straight to the artist.</p></li>
    <li><h3>Agree the arrangements</h3><p>The fee, dates, insurance, transport, installation and return are agreed directly between you and the artist, in writing.</p></li>
  </ol>
  <ul class="afh3-know">
    <li><strong>PlotArt introduces you to the artist.</strong> We’re not a party to the artwork hire and we don’t collect artwork rent or deposits. Any PlotArt fee requires a separate agreement.</li>
    <li><strong>Hire prices are agreed directly with the artist.</strong> Every work is price on request.</li>
    <li><strong>Transport and insurance are arranged between you and the artist.</strong></li>
    <li><strong>Photography and screen use are not automatically included.</strong> Any permission must be agreed in writing with the artist.</li>
    <li><strong>Film and television screen use can’t yet be arranged through PlotArt.</strong></li>
  </ul>
</div></section>

<section class="afh3-scenes" aria-labelledby="afh3-scenes-h">
  <div class="pa-wrap afh3-scenes-h"><h2 id="afh3-scenes-h">Where a hired work goes</h2><p>One painting, three settings. The settings are illustrations; the painting is real.</p></div>
  <div class="afh3-scene-row" role="region" aria-label="Three illustrated settings" tabindex="0">%(scenes)s</div>
</section>

<section class="pa-hire-gal afh3-works" id="afh3-works" aria-labelledby="pa-hire-gal-h" data-hire-section%(works_hidden)s><div class="pa-wrap">
  <div class="afh3-works-h"><h2 id="pa-hire-gal-h">Available to hire</h2><p>Every work is offered by its artist and checked by PlotArt. Price on request.</p></div>
  <p class="pa-hire-note" data-hire-status role="status" hidden></p>
  <noscript><p class="pa-hire-note">Please turn on JavaScript to see which works are available for hire right now.</p></noscript>
  <p class="pa-hire-note" id="pa-hire-closed" data-hire-closed tabindex="-1" hidden>Hire enquiries are not yet open.</p>
  %(region)s
</div></section>
%(after)s
%(next)s
<script src="hire-live.js" data-api="%(api)s" data-enquiries="%(enq)s" defer></script>
""" % {"art": SCENES.ART, "alt": SCENES.HERO_ALT, "credit": SCENES.CREDIT, "scenes": SCENES.SCENES, "region": region(cards, bar), "opportunities": OPP.BEGIN + OPP.END, "works_hidden": "" if cards else " hidden",
       "business_how": ' Renting for a workplace? See <a href="#business-rentals">Business rentals</a>.' if business_on else "", "next": NEXT % {"business": business_next(business_on)},
       "api": E(api), "enq": "on" if form else "off",
       "after": BUSINESS.REGION if business_on else ARTISTS_ONLY}


# G · Enquiry and next steps (founder brief 22 Nov 2026): the two audience paths that used to follow the hero, at the close.
NEXT = """<section class="afh-next" id="next-steps" aria-labelledby="afh-next-h"><div class="pa-wrap">
  <h2 id="afh-next-h">Enquiry and next steps</h2>
  <div class="afh-next-grid">
    <div class="afh-next-col">
      <h3>For businesses</h3>
      %(business)s
    </div>
    <div class="afh-next-col">
      <h3>For artists</h3>
      <p>Offer selected works on your own terms from your PlotArt Studio, once Art for Hire opens to artists.</p>
      <p class="afh-close-acts"><a class="afh3-link" href="#for-artists">Read the artist terms</a></p>
    </div>
  </div>
</div></section>"""


def business_next(business_on):
    if business_on:
        return ('<p>Hire original work for a set, an interior or a staged home. Or rent it for your workplace while it remains for sale.</p>\n'
                '      <p class="afh-close-acts"><a class="afh3-btn" href="mailto:hello@plotnua.ie?subject=Business%20art%20purchase%20or%20rental">Discuss hiring art for your space</a>'
                '<a class="afh3-link" href="mailto:hello@plotnua.ie?subject=Art%20for%20Hire%20brief">Send a brief</a></p>')
    return ('<p>Hire original work for a set, an interior or a staged home.</p>\n'
            '      <p class="afh-close-acts"><a class="afh3-btn" href="mailto:hello@plotnua.ie?subject=Art%20for%20Hire%20brief">Discuss hiring art for your space</a></p>')


# Without business rental information: the artists' section alone (the same wording as before the redesign).
ARTISTS_ONLY = """<section class="afh3-artists" id="for-artists" aria-labelledby="afh3-artists-h"><div class="pa-wrap">
  <h2 id="afh3-artists-h">Offer your work for hire</h2>
  <p>For PlotArt artists. Taking part is optional. Once Art for Hire opens to artists, you’ll be able to choose works to offer from your PlotArt Studio account. Nothing is listed without your consent.</p>
</div></section>"""


# The generated catalogue region (Stage 3B-6). Everything outside it is fixed by the page's code release and pinned in
# the launch manifest; scheduled hire publishing may change only this region (plotart-content-boundary.py --hire).
BEGIN, END = "<!-- pa-hire-catalogue:begin -->", "<!-- pa-hire-catalogue:end -->"


def region(cards, bar=""):
    gallery = ('%s\n  <ul class="pa-hire-grid" aria-label="Works available for hire">\n%s\n</ul>' % (bar, "\n".join(cards))) if cards else ""
    # 22 Nov 2026 (founder brief): no public empty state. With no approved works the whole "Available to hire" section ships
    # hidden; hire-live.js shows it only while the live check is showing at least one approved work. The artists' mini
    # gallery above is the page's discovery area.
    return "%s\n  %s\n  %s" % (BEGIN, gallery, END)


def build(root, catalogue, api, form=False, update=False):
    rows = resolve(root, catalogue)
    cards = [card(it, a, w) for it, a, w in rows]
    bar = filters(rows) if rows else ""
    if update:      # scheduled publishing: the catalogue region only; the page itself is the approved code release
        ip = os.path.join(root, "plotart", "art-for-hire", "index.html")
        if not os.path.isfile(ip):
            raise Refused("--update needs the released Art for Hire page; adding the page is a code release")
        page = open(ip, encoding="utf-8").read()
        if page.count(BEGIN) != 1 or page.count(END) != 1:
            raise Refused("the released page has no single catalogue region")
        a, b = page.index(BEGIN), page.index(END) + len(END)
        open(ip, "w", encoding="utf-8").write(page[:a] + region(cards, bar) + page[b:])
        return len(cards)
    css_name = "art-for-hire.css?v=" + hashlib.sha256(open(os.path.join(PUBLIC_HIRE, "art-for-hire.css"), "rb").read()).hexdigest()[:12]
    path, page = SHELL.artist_page("art-for-hire/index.html", TITLE, DESC, body(cards, api, form, bar), scripts=("plotart.js",),
                                   current="hire", hire_nav=True, fine=FINE, styles=(css_name, "../assets/plotart-opportunities.css"))
    # the artist opportunity list (16 Nov 2026): its own region, separate from the works catalogue; published artists only
    page = OPP.update(page, "art-for-hire/index.html", SEO.public_packages(root), FEAT.choices(root))
    out = os.path.join(root, "plotart", "art-for-hire")
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page)
    for f in ("art-for-hire.css", "hire-live.js"):
        shutil.copyfile(os.path.join(PUBLIC_HIRE, f), os.path.join(out, f))
    return len(cards)


def authorised(root, preview, form):
    """The page is built into the site only when the founder has switched it on (launch switches); a private preview
    copy (--preview) may be built anywhere except the repository itself."""
    repo = os.path.abspath(os.path.join(HERE, ".."))
    if preview:
        if os.path.abspath(root) == repo:
            raise Refused("--preview never writes into the repository; build the preview in a copy")
        return
    sw = os.path.join(root, "atlas-tools", "release", "plotart-launch-switches.json")
    launch = json.load(open(sw, encoding="utf-8")) if os.path.isfile(sw) else {}
    if launch.get("art_for_hire_page") is not True:
        raise Refused("the Art for Hire page is not switched on (art_for_hire_page in plotart-launch-switches.json needs the founder's release approval)")
    if form and launch.get("art_for_hire_enquiry_form") is not True:
        raise Refused("the enquiry form is not switched on (art_for_hire_enquiry_form needs the founder's approval after legal and privacy review)")


def relay_base(root):
    cfg = json.load(open(os.path.join(root, "atlas-tools", "release", "plotart-gallery-config.json"), encoding="utf-8"))
    ep = cfg.get("enquiry_endpoint") or ""
    if not re.fullmatch(r"https://[a-z0-9.-]+\.workers\.dev/v1/enquiry", ep):
        raise Refused("no approved enquiry relay in plotart-gallery-config.json")
    return ep[:-len("/v1/enquiry")]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--catalogue", required=True)
    ap.add_argument("--api", help="relay base address (default: the approved relay in plotart-gallery-config.json)")
    ap.add_argument("--enquiries-form", action="store_true")
    ap.add_argument("--update", action="store_true", help="rewrite only the catalogue region of the released page")
    ap.add_argument("--preview", action="store_true", help="a private local preview copy, never the repository")
    a = ap.parse_args()
    try:
        authorised(a.root, a.preview, a.enquiries_form)
        api = a.api if (a.preview and a.api) else relay_base(a.root) if not a.preview else (a.api or "https://relay.invalid")
        if a.api and not a.preview and a.api != api:
            raise Refused("--api may differ from the approved relay only in a preview")
        n = build(a.root, json.load(open(a.catalogue, encoding="utf-8")), api, a.enquiries_form, a.update)
    except Refused as e:
        sys.exit("REFUSED (nothing written): %s" % e)
    print("Art for Hire page %s: %d listed work(s); enquiry form %s" % ("catalogue region updated" if a.update else "written", n, "built" if a.enquiries_form else "not built"))
