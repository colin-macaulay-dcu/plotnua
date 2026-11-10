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
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plotart_shell as SHELL  # noqa: E402

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
    gallery = ('<ul class="pa-hire-grid" aria-label="Works available for hire">\n%s\n</ul>' % "\n".join(cards)) if cards else ""
    empty = ('<div class="pa-hire-empty" data-hire-empty%s%s><span class="pa-hire-frame" aria-hidden="true"></span><div>'
             '<h2>No works are available for hire just now.</h2>'
             '<p>Art for Hire is new. Works appear here once their artists choose to offer them and PlotArt has checked each one.</p>'
             '<p>Looking for something specific for a production, shoot or space? Email <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a> and tell us what you need.</p>'
             '</div></div>') % ("" if cards else " data-hire-static", " hidden" if cards else "")
    return """
<section class="pa-hire-hero"><div class="pa-wrap">
  <p class="pa-eyebrow">Art for Hire</p>
  <h1>Original art,<br><em>on hire.</em></h1>
  <div class="pa-hire-intro">
    <p class="pa-lede">An original work by an Irish artist can set the tone of a room, give a shoot its character or make a staged home feel lived in. The works here can be hired for productions, photography, property staging and interiors, and every hire is agreed directly with the artist.</p>
    <p class="pa-hire-for"><strong>For</strong>Production designers and set decorators, photographers, advertising teams, property stagers and interior designers.</p>
  </div>
</div></section>

<section class="pa-hire-gal" aria-labelledby="pa-hire-gal-h"><div class="pa-wrap">
  <div class="pa-hire-gal-h"><h2 id="pa-hire-gal-h">Works for hire</h2><p>Every work is offered by its artist and checked by PlotArt. Price on request.</p></div>
  <p class="pa-hire-note" data-hire-status role="status" hidden></p>
  <noscript><p class="pa-hire-note">Please turn on JavaScript to see which works are available for hire right now.</p></noscript>
  <p class="pa-hire-note" id="pa-hire-closed" data-hire-closed tabindex="-1"%s>Hire enquiries are not yet open.</p>
  %s
  %s
</div></section>

<section class="pa-hire-how" aria-labelledby="pa-hire-how-h"><div class="pa-wrap">
  <p class="pa-eyebrow">How hire works</p>
  <h2 id="pa-hire-how-h">Simple, direct, between you and the artist.</h2>
  <ol class="pa-hire-steps">
    <li><h3>Choose a work</h3><p>Each work here has been offered by its artist and checked by PlotArt. Sizes and media are shown with every work.</p></li>
    <li><h3>Send an enquiry</h3><p>Tell the artist about your project: the dates, where the work would go and how it would be used. Your enquiry goes straight to the artist.</p></li>
    <li><h3>Agree the hire together</h3><p>The fee, dates, insurance, transport, installation and return are agreed directly between you and the artist, in writing.</p></li>
  </ol>
  <div class="pa-hire-know">
    <h2>Good to know</h2>
    <ul>
      <li><strong>PlotArt introduces you to the artist.</strong> We’re not a party to the hire and we don’t take payment.</li>
      <li><strong>Hire prices are agreed directly with the artist.</strong> Every work is price on request.</li>
      <li><strong>Transport and insurance are arranged between you and the artist.</strong></li>
      <li><strong>Photography and screen use are not automatically included.</strong> Any permission must be agreed in writing with the artist.</li>
      <li><strong>Film and television screen use can’t yet be arranged through PlotArt.</strong></li>
    </ul>
  </div>
</div></section>

<section class="pa-hire-artists" aria-label="For PlotArt artists"><div class="pa-wrap">
  <p><strong>For PlotArt artists.</strong> Taking part is optional. Once Art for Hire opens to artists, you’ll be able to choose works to offer from your PlotArt Studio account. Nothing is listed without your consent.</p>
</div></section>
<script src="hire-live.js" data-api="%s" data-enquiries="%s" defer></script>
""" % ("" if cards else " hidden", gallery, empty, E(api), "on" if form else "off")


def build(root, catalogue, api, form=False):
    rows = resolve(root, catalogue)
    cards = [card(it, a, w) for it, a, w in rows]
    path, page = SHELL.artist_page("art-for-hire/index.html", TITLE, DESC, body(cards, api, form), scripts=("plotart.js",),
                                   current="hire", hire_nav=True, fine=FINE, styles=("art-for-hire.css",))
    out = os.path.join(root, "plotart", "art-for-hire")
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page)
    for f in ("art-for-hire.css", "hire-live.js"):
        shutil.copyfile(os.path.join(PUBLIC_HIRE, f), os.path.join(out, f))
    return len(cards)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--catalogue", required=True)
    ap.add_argument("--api", required=True)
    ap.add_argument("--enquiries-form", action="store_true")
    a = ap.parse_args()
    try:
        n = build(a.root, json.load(open(a.catalogue, encoding="utf-8")), a.api, a.enquiries_form)
    except Refused as e:
        sys.exit("REFUSED (nothing written): %s" % e)
    print("Art for Hire page written: %d listed work(s); enquiry form %s" % (n, "built" if a.enquiries_form else "not built"))
