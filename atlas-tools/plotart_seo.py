"""Search settings for approved public PlotArt pages, never Studio drafts.

Shared by the public renderer, sitemap publisher and release guard. Private
previews use their own renderer; they must never call this public page shell.
"""
import html
import json
import re
from pathlib import Path

ORIGIN = "https://plotnua.ie/plotart/"
BEGIN = "<!-- plotart-search:begin -->"
END = "<!-- plotart-search:end -->"
REGION = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
GUIDE_PATHS = ("buy-original-art-ireland.html", "abstract-contemporary-art-ireland.html")
SWITCHES = Path(__file__).resolve().parent / "release/plotart-launch-switches.json"


def switches():
    return json.loads(SWITCHES.read_text())


def canonical(path):
    return ORIGIN + (path[:-10] if path.endswith("index.html") else path)


def indexable(path, launch):
    if path in GUIDE_PATHS:
        return launch.get("buyer_guides_indexable") is True
    key = {"index.html": "home_indexable", "gallery/index.html": "gallery_indexable",
           "about.html": "about_indexable", "founding-25.html": "f25_page_indexable",
           "mobile-gallery/index.html": "mobile_gallery_indexable"}.get(path)
    if key:
        return launch.get(key) is True
    if re.fullmatch(r"artists/[a-z0-9]+(?:-[a-z0-9]+){0,6}/[a-z0-9]+(?:-[a-z0-9]+){0,6}\.html", path):
        return launch.get("galleries_open") is True and launch.get("artist_pages_indexable") is True
    return False


def head(path, title, description, launch=None):
    launch = switches() if launch is None else launch
    if not indexable(path, launch):
        return '<meta name="robots" content="noindex, follow">'
    esc = lambda s: html.escape(s, quote=True)
    url = esc(canonical(path))
    return ('<meta name="robots" content="index, follow">\n'
            '<link rel="canonical" href="%s">\n'
            '<meta property="og:type" content="website">\n'
            '<meta property="og:site_name" content="PlotArt">\n'
            '<meta property="og:url" content="%s">\n'
            '<meta property="og:title" content="%s">\n'
            '<meta property="og:description" content="%s">') % (url, url, esc(title), esc(description))


def sitemap_paths(packages, launch):
    paths = [p for p in ("index.html", "gallery/index.html", "about.html", "founding-25.html") + GUIDE_PATHS if indexable(p, launch)]
    for pkg in sorted(packages, key=lambda p: p["artist"]["slug"]):
        # Only the already-approved public export is an input. Never read Studio drafts.
        if pkg["publication"].get("state") != "approved":
            raise ValueError("Unapproved gallery in public sitemap inputs")
        base = "artists/" + pkg["artist"]["slug"] + "/"
        paths.extend(p for p in [base + "index.html"] + [base + w["slug"] + ".html" for w in pkg["works"]
                     if w["availability"] in ("available", "reserved", "sold", "not_for_sale")] if indexable(p, launch))
    return paths


def sitemap_block(packages, launch):
    return BEGIN + "\n" + "\n".join("  <url><loc>%s</loc></url>" % html.escape(canonical(p))
                                     for p in sitemap_paths(packages, launch)) + "\n  " + END


def update_sitemap(document, packages, launch):
    """Replace exactly the PlotArt region; everything outside it is byte-identical."""
    if document.count(BEGIN) != 1 or document.count(END) != 1 or not REGION.search(document):
        raise ValueError("Missing or duplicate PlotArt sitemap region")
    return REGION.sub(lambda m: sitemap_block(packages, launch), document, count=1)


def public_packages(root):
    return [json.loads(p.read_text()) for p in sorted((Path(root) / "plotart/artists").glob("*/gallery.json"))]
