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
import html
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plotart_shell as SHELL  # noqa: E402
import plotart_hire_scenes as SCENES  # noqa: E402

E = lambda s: html.escape(str(s), quote=True)
PUBLIC_HIRE = os.path.join(HERE, "..", "worker", "plotart-studio", "public-hire")
FORBIDDEN = {"handling_note", "artist_email", "email", "replacement_value", "price_eur", "fee", "private"}
TITLE = "Art for Hire: Original Irish Art for Productions, Shoots and Spaces | PlotArt"
DESC = ("Hire original work by Irish artists for productions, photography, property staging and interiors. "
        "PlotArt introduces you to the artist; you agree the hire directly with them.")
FINE = ("Works offered for hire are listed by their artists and checked by PlotArt. PlotArt introduces hirers to artists: it doesn't take "
        "payment, arrange transport or insure work. Photographs of artworks are supplied by the artist and credited where taken by someone else.")


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
    return ('<li class="pa-hire-card" data-hire-work="%s" data-hire-ref="%s" data-hire-title="%s" data-hire-artist="%s" hidden>\n'
            '  <figure class="pa-hire-art"><img src="%s%s" srcset="%s" sizes="(max-width:639px) 92vw, (max-width:1100px) 44vw, 30vw" width="%d" height="%d" alt="%s" loading="lazy" decoding="async"></figure>\n'
            '  <p class="pa-hire-artist">%s</p>\n  <h3>%s</h3>\n  <dl class="pa-hire-dl">%s</dl>\n'
            '  <button type="button" class="pa-btn pa-btn--ghost" data-hire-enquire aria-describedby="pa-hire-closed">Enquire about hire<span class="pa-sr"> of %s by %s</span></button>\n</li>') % (
        E(w["id"]), E(ref), E(w["title"]), E(artist["display_name"]), base, E(mid["file"]), E(srcset), mid["pixels"][0], mid["pixels"][1],
        E(img.get("alt") or w["title"]), E(artist["display_name"]), E(w["title"]), dl, E(w["title"]), E(artist["display_name"]))


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
        seen.add(wid)
        out.append((it, pkg["artist"], w))
    return out


def body(cards, api, form):
    # Version 3 (founder approval, 11 Nov 2026). The hero's primary action ships as "How it works"; hire-live.js turns it into
    # "See works for hire" only while the live check is showing approved works (data-hire-cta).
    return """
<section class="afh3-hero" aria-labelledby="afh3-h">
  <div class="afh3-hero-art"><img src="%(art)s" alt="%(alt)s" width="1332" height="940" fetchpriority="high"></div>
  <div class="afh3-hero-copy">
    <h1 id="afh3-h">Original art,<br>on hire.</h1>
    <div class="afh3-hero-row">
      <p class="afh3-sub">Irish artists’ original work for film and television, interiors and staged homes. You agree each hire directly with the artist.</p>
      <p class="afh3-cta"><a class="afh3-btn" href="#afh3-how" data-hire-cta>How it works</a><a class="afh3-link" href="mailto:hello@plotnua.ie?subject=Art%%20for%%20Hire%%20brief">Send a brief</a></p>
    </div>
  </div>
  <p class="afh3-hero-credit">%(credit)s</p>
</section>
<p class="afh3-hero-credit-m">%(credit)s</p>

<section class="afh3-scenes" aria-labelledby="afh3-scenes-h">
  <div class="pa-wrap afh3-scenes-h"><h2 id="afh3-scenes-h">Where a hired work goes</h2><p>One painting, three settings. The settings are illustrations; the painting is real.</p></div>
  %(scenes)s
</section>

<section class="pa-hire-gal afh3-works" id="afh3-works" aria-labelledby="pa-hire-gal-h"><div class="pa-wrap">
  <div class="afh3-works-h"><h2 id="pa-hire-gal-h">Available to hire</h2><p>Every work is offered by its artist and checked by PlotArt. Price on request.</p></div>
  <p class="pa-hire-note" data-hire-status role="status" hidden></p>
  <noscript><p class="pa-hire-note">Please turn on JavaScript to see which works are available for hire right now.</p></noscript>
  <p class="pa-hire-note" id="pa-hire-closed" data-hire-closed tabindex="-1" hidden>Hire enquiries are not yet open.</p>
  %(region)s
</div></section>

<section class="afh3-how" id="afh3-how" aria-labelledby="afh3-how-h"><div class="pa-wrap">
  <h2 id="afh3-how-h">How a hire works</h2>
  <ol class="afh3-steps">
    <li><h3>Choose a work</h3><p>Each work has been offered by its artist and checked by PlotArt. Every listing shows the size, medium and when it’s available.</p></li>
    <li><h3>Send an enquiry</h3><p>Tell the artist your dates, where the work will go and how it will be used. Your enquiry goes straight to the artist.</p></li>
    <li><h3>Agree it with the artist</h3><p>The fee, dates, insurance, transport, installation and return are agreed directly between you and the artist, in writing.</p></li>
  </ol>
  <ul class="afh3-know">
    <li><strong>PlotArt introduces you to the artist.</strong> We’re not a party to the hire and we don’t take payment.</li>
    <li><strong>Hire prices are agreed directly with the artist.</strong> Every work is price on request.</li>
    <li><strong>Transport and insurance are arranged between you and the artist.</strong></li>
    <li><strong>Photography and screen use are not automatically included.</strong> Any permission must be agreed in writing with the artist.</li>
    <li><strong>Film and television screen use can’t yet be arranged through PlotArt.</strong></li>
  </ul>
</div></section>

<section class="afh3-artists" aria-labelledby="afh3-artists-h"><div class="pa-wrap">
  <h2 id="afh3-artists-h">Offer your work for hire</h2>
  <p>For PlotArt artists. Taking part is optional. Once Art for Hire opens to artists, you’ll be able to choose works to offer from your PlotArt Studio account. Nothing is listed without your consent.</p>
</div></section>
<script src="hire-live.js" data-api="%(api)s" data-enquiries="%(enq)s" defer></script>
""" % {"art": SCENES.ART, "alt": SCENES.HERO_ALT, "credit": SCENES.CREDIT, "scenes": SCENES.SCENES, "region": region(cards),
       "api": E(api), "enq": "on" if form else "off"}


# The generated catalogue region (Stage 3B-6). Everything outside it is fixed by the page's code release and pinned in
# the launch manifest; scheduled hire publishing may change only this region (plotart-content-boundary.py --hire).
BEGIN, END = "<!-- pa-hire-catalogue:begin -->", "<!-- pa-hire-catalogue:end -->"


def region(cards):
    gallery = ('<ul class="pa-hire-grid" aria-label="Works available for hire">\n%s\n</ul>' % "\n".join(cards)) if cards else ""
    empty = ('<div class="pa-hire-empty afh3-empty" data-hire-empty%s%s>'
             '<p><strong>No works are available for hire just now.</strong> Art for Hire is new. Works appear here once their artists choose to offer them and PlotArt has checked each one.</p>'
             '<p>Looking for something specific for a production, shoot or space? Email <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a> and tell us what you need.</p>'
             '</div>') % ("" if cards else " data-hire-static", " hidden" if cards else "")
    return "%s\n  %s\n  %s\n  %s" % (BEGIN, gallery, empty, END)


def build(root, catalogue, api, form=False, update=False):
    rows = resolve(root, catalogue)
    cards = [card(it, a, w) for it, a, w in rows]
    if update:      # scheduled publishing: the catalogue region only; the page itself is the approved code release
        ip = os.path.join(root, "plotart", "art-for-hire", "index.html")
        if not os.path.isfile(ip):
            raise Refused("--update needs the released Art for Hire page; adding the page is a code release")
        page = open(ip, encoding="utf-8").read()
        if page.count(BEGIN) != 1 or page.count(END) != 1:
            raise Refused("the released page has no single catalogue region")
        a, b = page.index(BEGIN), page.index(END) + len(END)
        open(ip, "w", encoding="utf-8").write(page[:a] + region(cards) + page[b:])
        return len(cards)
    path, page = SHELL.artist_page("art-for-hire/index.html", TITLE, DESC, body(cards, api, form), scripts=("plotart.js",),
                                   current="hire", hire_nav=True, fine=FINE, styles=("art-for-hire.css",))
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
