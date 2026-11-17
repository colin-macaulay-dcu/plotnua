"""PlotArt homepage · the founder's featured artworks (founder brief 17 Nov 2026; Studio migration 0016).

One generated region on plotart/index.html, between HOME_BEGIN and HOME_END. Everything else on the homepage stays pinned.

  - The founder chooses up to six items in the Review Desk (Homepage): an ARTWORK, or an ARTIST represented by one of their
    published artworks that the founder chooses (never picked automatically). Both name the artwork shown.
  - The publishing pipeline receives only public identifiers (GET /api/pipeline/homepage: gallery address and artwork id)
    and renders the region here ONLY from published galleries (plotart/artists/*/gallery.json): an artwork must be shown
    in its published gallery (plotart_gallery_pages.shown) with a main photograph; a featured artist shows the chosen
    work and links to the gallery. Anything withdrawn, unpublished or no longer shown simply drops out (an artist whose
    chosen work is withdrawn drops out too: nothing else is substituted), so the region can never show what the
    published galleries do not.
  - Images are the artist's own published derivatives (plotart/artists/<slug>/img/...), with their approved alt text;
    nothing new is uploaded, so the existing image-rights and provenance records cover them.
  - Each item carries its identifiers (data-pa-home-item) so the selection can be read back from the page when the
    Studio is unavailable, and so the guards can check the region is exactly what that selection renders.
  - No selection: an empty region, and the homepage looks exactly as before.
"""
import html
import re

import plotart_gallery_pages as P

HOME_BEGIN, HOME_END = "<!-- pa-home-featured:begin -->", "<!-- pa-home-featured:end -->"
REGION = re.compile(re.escape(HOME_BEGIN) + r".*?" + re.escape(HOME_END), re.S)
ITEM = re.compile(r'data-pa-home-item="(artwork|artist):([a-z0-9-]+):([a-z0-9]+)"')
MAX = 6
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){0,6}$")
WORK_ID = re.compile(r"^w[0-9a-z]{4,30}$")
E = lambda s: html.escape(str(s), quote=True)


def check_selection(selection):
    """A selection is a list of {"kind": "artwork"|"artist", "artist": <gallery address>, "work": <artwork id>}, at most six;
    no artwork twice, no artist featured twice."""
    if not isinstance(selection, list) or len(selection) > MAX:
        raise ValueError("the homepage selection must be a list of at most %d items" % MAX)
    seen = set()
    for it in selection:
        if not isinstance(it, dict) or set(it) != {"kind", "artist", "work"} or it["kind"] not in ("artwork", "artist") \
                or not isinstance(it["artist"], str) or not SLUG.match(it["artist"]) or not isinstance(it["work"], str) or not WORK_ID.match(it["work"]):
            raise ValueError("a homepage item carries an unexpected field or value: %r" % (it,))
        k = ("artist", it["artist"]) if it["kind"] == "artist" else (it["artist"], it["work"])
        if k in seen:
            raise ValueError("a homepage item is repeated")
        seen.add(k)
    return selection


def _main(w):
    im = next((i for i in w.get("images") or [] if i.get("role") == "main" and i.get("derivatives")), None)
    return im


def resolve(selection, packages):
    """The items that can be shown, in the founder's order: (kind, package, work, main image)."""
    by = {p["artist"]["slug"]: p for p in packages}
    out, used = [], set()
    for it in check_selection(selection):
        pkg = by.get(it["artist"])
        if not pkg:
            continue
        w = next((x for x in P.shown(pkg) if x.get("id") == it["work"] and _main(x)), None)
        k = ("artist", it["artist"]) if it["kind"] == "artist" else (it["artist"], it["work"])
        if w and k not in used:
            out.append((it["kind"], pkg, w, _main(w)))
            used.add(k)
    return out[:MAX]


def content(selection, packages, base=""):
    items = resolve(selection, packages)
    if not items:
        return ""
    lis = []
    for kind, pkg, w, im in items:
        a = pkg["artist"]
        slug = a["slug"]
        d = P.pick(im, 1200)
        href = "%sartists/%s/%s" % (base, slug, "" if kind == "artist" else w["slug"] + ".html")
        title, sub = (a["display_name"], "View the gallery") if kind == "artist" else (w["title"], a["display_name"])
        lis.append(
            '<li class="pa-hf-item" data-pa-home-item="%s:%s:%s"><a class="pa-hf-link" href="%s" data-pa-track="home_featured_%s">'
            '<span class="pa-hf-art"><img src="%sartists/%s/img/%s" srcset="%s" sizes="(max-width:640px) 92vw, (max-width:1100px) 46vw, 30vw" '
            'width="%d" height="%d" alt="%s" loading="lazy" decoding="async"></span>'
            '<span class="pa-hf-cap"><span class="pa-hf-title">%s</span><span class="pa-hf-sub">%s</span></span></a></li>' % (
                kind, slug, w["id"], E(href), kind,
                base, slug, E(d["file"]), E(P.srcset(im, "%sartists/%s/img/" % (base, slug))), d["pixels"][0], d["pixels"][1], E(im["alt"]),
                E(title), E(sub)))
    return ('<section class="pa-sec pa-home-feat" aria-labelledby="homeFeatH"><div class="pa-wrap">\n'
            '  <div class="pa-hf-head"><p class="pa-eyebrow">Selected by PlotArt</p><h2 id="homeFeatH">Featured artworks</h2></div>\n'
            '  <ul class="pa-hf-grid">%s</ul>\n'
            '  <p class="pa-hf-more"><a href="%sartworks/" data-pa-track="home_featured_all">Browse all available artworks</a></p>\n'
            '</div></section>') % ("".join(lis), base)


def region(doc):
    m = REGION.findall(doc)
    if len(m) != 1:
        raise ValueError("the homepage featured region is missing or repeated")
    return m[0]


def selection_in(doc):
    """The selection the page currently shows (read back from its items)."""
    return [{"kind": kind, "artist": s, "work": w} for kind, s, w in ITEM.findall(region(doc))]


def update(doc, selection, packages):
    region(doc)
    inner = content(selection, packages)
    return REGION.sub(lambda m: HOME_BEGIN + ("\n" + inner + "\n" if inner else "") + HOME_END, doc, count=1)


def outside(doc):
    """The homepage with the featured region emptied: what the launch guard pins."""
    region(doc)
    return REGION.sub(HOME_BEGIN + HOME_END, doc, count=1)


def refresh(root, packages, selection=None):
    """Re-render the region from the published galleries; with no new selection, keep the founder's current one (read
    back from the page), so withdrawn or unpublished work drops out on every publication."""
    path = root / "plotart" / "index.html" if hasattr(root, "__truediv__") else root + "/plotart/index.html"
    doc = open(path, encoding="utf-8").read()
    new = update(doc, selection_in(doc) if selection is None else selection, packages)
    if new != doc:
        open(path, "w", encoding="utf-8").write(new)
    return new != doc
