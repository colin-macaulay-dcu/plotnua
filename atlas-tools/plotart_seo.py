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
# The artwork collection (SEO buyer-intent Phase 1, 13 Nov 2026): every published, available work on one indexable
# page. Like the guides, only its generated collection region changes when galleries are published.
COLLECTION_PATHS = ("artworks/index.html", "large-artworks/index.html")
# each collection has its own indexing and sitemap switches (prepared separately, released separately)
COLLECTION_SWITCHES = {"artworks/index.html": ("artworks_indexable", "artworks_in_sitemap"),
                       "large-artworks/index.html": ("large_artworks_indexable", "large_artworks_in_sitemap")}
EDITORIAL_PATHS = ("choose-art-for-living-room.html",)
# Commercial Conversion Sprint 1 (founder approval 26 Nov 2026): the homepage's availability line and the living-room
# guide's price-band recommendations are generated regions too, refreshed from published galleries at every publication
# (guard L22 recomputes the homepage figures independently; L3 checks every generated region is current).
HOME_PATHS = ("index.html",)
RECOMMEND_PATHS = EDITORIAL_PATHS
GENERATED_PATHS = GUIDE_PATHS + COLLECTION_PATHS + HOME_PATHS + RECOMMEND_PATHS
TOOL_PATHS = ("art-size-calculator.html",)
SWITCHES = Path(__file__).resolve().parent / "release/plotart-launch-switches.json"


def switches():
    return json.loads(SWITCHES.read_text())


def canonical(path):
    return ORIGIN + (path[:-10] if path.endswith("index.html") else path)


def indexable(path, launch):
    if path == "services.html" and launch.get("services_page") is not True:   # paused 19 Nov 2026: never indexed while withdrawn
        return False
    if path == "art-for-hire/index.html":
        return launch.get("art_for_hire_page") is True and launch.get("business_rental_information") is True
    if path in TOOL_PATHS:
        return launch.get("wall_size_indexable") is True
    if path in GUIDE_PATHS + EDITORIAL_PATHS:
        return launch.get("buyer_guides_indexable") is True
    if path in COLLECTION_PATHS:
        return launch.get(COLLECTION_SWITCHES[path][0]) is True
    key = {"index.html": "home_indexable", "gallery/index.html": "gallery_indexable",
           "about.html": "about_indexable", "founding-25.html": "f25_page_indexable",
           "mobile-gallery/index.html": "mobile_gallery_indexable",
           "commissions/index.html": "commissions_indexable",
           "for-artists.html": "for_artists_indexable",
           "services.html": "services_indexable"}.get(path)
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


# Generated search titles and descriptions (SEO and analytics package, 26 Nov 2026): shared by plotart_search_content
# (the collection and guide pages) and plotart_opportunities (the commissions page).
_META = re.compile(r'(<meta (?:name="description"|property="og:description"|name="twitter:description") content=")[^"]*(">)')
_TITLES = re.compile(r'(<meta (?:property="og:title"|name="twitter:title") content=")[^"]*(">)')


def set_meta(document, title, desc):
    """The page's <title>, description, og: and twitter: title and description set to these (each tag the page has;
    the title and the description are required). Everything else is unchanged."""
    if len(re.findall(r"<title>.*?</title>", document, re.S)) != 1 or len(re.findall(r'<meta name="description" content="[^"]*">', document)) != 1:
        raise ValueError("a generated page must have exactly one <title> and one meta description")
    document = re.sub(r"<title>.*?</title>", lambda m: "<title>" + html.escape(title, quote=False) + "</title>", document, count=1, flags=re.S)
    document = _TITLES.sub(lambda m: m.group(1) + html.escape(title, quote=True) + m.group(2), document)
    return _META.sub(lambda m: m.group(1) + html.escape(desc, quote=True) + m.group(2), document)


def blank_meta(document):
    """The page with its description, og:description and twitter:description emptied (for the manifest's outside pins of
    pages whose descriptions are generated from the published galleries)."""
    return _META.sub(lambda m: m.group(1) + m.group(2), document)


def sitemap_paths(packages, launch):
    paths = [p for p in ("index.html", "gallery/index.html", "about.html", "founding-25.html") + GUIDE_PATHS + EDITORIAL_PATHS + TOOL_PATHS if indexable(p, launch)]
    # The collection is listed only by its own sitemap switch (prepared 13 Nov 2026; off until the founder approves).
    paths += [p for p in COLLECTION_PATHS if indexable(p, launch) and launch.get(COLLECTION_SWITCHES[p][1]) is True]
    if indexable("art-for-hire/index.html", launch):
        paths.append("art-for-hire/index.html")
    if indexable("commissions/index.html", launch):      # founder decision 17 Nov 2026: indexed and in the sitemap
        paths.append("commissions/index.html")
    if indexable("for-artists.html", launch):            # founder brief 17 Nov 2026: artists can find their Studio
        paths.append("for-artists.html")
    if indexable("services.html", launch):               # founder brief 19 Nov 2026: Art Services & Providers, indexed and in the sitemap
        paths.append("services.html")
    for pkg in sorted(packages, key=lambda p: p["artist"]["slug"]):
        # Only the already-approved public export is an input. Never read Studio drafts.
        if pkg["publication"].get("state") != "approved":
            raise ValueError("Unapproved gallery in public sitemap inputs")
        base = "artists/" + pkg["artist"]["slug"] + "/"
        paths.extend(p for p in [base + "index.html"] + [base + w["slug"] + ".html" for w in pkg["works"]
                     if w["availability"] in ("available", "reserved", "sold", "not_for_sale")] if indexable(p, launch))
    return paths


IMAGE_NS = "http://www.google.com/schemas/sitemap-image/1.1"


def sitemap_images(packages, launch):
    """Largest approved derivative of each displayed image, on its own landing page."""
    paths = set(sitemap_paths(packages, launch))  # also refuses draft exports
    images = {}
    for pkg in packages:
        a = pkg["artist"]
        base = "artists/" + a["slug"] + "/"
        entries = [(base + "index.html", [a["portrait"]] if a.get("portrait") else [])]
        entries += [(base + w["slug"] + ".html", w["images"]) for w in pkg["works"]
                    if w["availability"] in ("available", "reserved", "sold", "not_for_sale")]
        for path, pictures in entries:
            if path not in paths:
                continue
            urls = list(dict.fromkeys(ORIGIN + base + "img/" + max(i["derivatives"], key=lambda d: d["long_edge"])["file"]
                                     for i in pictures if i.get("derivatives")))
            if len(urls) > 1000:
                raise ValueError("Image sitemap supports at most 1000 images per page")
            if urls:
                images[path] = urls
    return images


def sitemap_block(packages, launch):
    images = sitemap_images(packages, launch)
    rows = []
    for path in sitemap_paths(packages, launch):
        tags = "".join("<image:image><image:loc>%s</image:loc></image:image>" % html.escape(url)
                       for url in images.get(path, []))
        rows.append("  <url><loc>%s</loc>%s</url>" % (html.escape(canonical(path)), tags))
    return BEGIN + "\n" + "\n".join(rows) + "\n  " + END


def update_sitemap(document, packages, launch):
    """Replace exactly the PlotArt region; everything outside it is byte-identical."""
    if document.count(BEGIN) != 1 or document.count(END) != 1 or not REGION.search(document):
        raise ValueError("Missing or duplicate PlotArt sitemap region")
    return REGION.sub(lambda m: sitemap_block(packages, launch), document, count=1)


def public_packages(root):
    return [json.loads(p.read_text()) for p in sorted((Path(root) / "plotart/artists").glob("*/gallery.json"))]


META_BEGIN = "<!-- pa-artist-search:begin -->"
META_END = "<!-- pa-artist-search:end -->"
META_REGION = re.compile(re.escape(META_BEGIN) + r".*?" + re.escape(META_END), re.S)


OFFER_AVAILABILITY = {"available": "https://schema.org/InStock", "sold": "https://schema.org/SoldOut",
                      "reserved": "https://schema.org/LimitedAvailability"}


def artwork_offer(work, url, seller_id):
    """The one Offer for an artwork page, or None: only a published asking price (never 'price on request') and only for
    an available, reserved or sold work. Prices are whole euro as published; nothing is inferred."""
    price = work.get("price_eur")
    if work.get("price_on_request") or not price or work["availability"] not in OFFER_AVAILABILITY:
        return None
    return {"@type": "Offer", "price": "%g" % price, "priceCurrency": "EUR", "availability": OFFER_AVAILABILITY[work["availability"]],
            "itemCondition": "https://schema.org/NewCondition", "seller": {"@id": seller_id}, "url": url}


def artist_metadata(path, pkg, launch=None):
    """Public facts only. The artwork is a VisualArtwork and, since the SEO and analytics package (founder approval 26 Nov
    2026, section 2.5), also a Product whose one Offer states exactly the published asking price (EUR) and availability, sold
    by the artist (the artist is always the seller). A work with its price on request, or not for sale, has no Offer."""
    launch = switches() if launch is None else launch
    if pkg["publication"].get("state") != "approved" or not indexable(path, launch):
        return ""
    a = pkg["artist"]
    base = "artists/" + a["slug"] + "/"
    shown = [w for w in pkg["works"] if w["availability"] in ("available", "reserved", "sold", "not_for_sale")]
    work = next((w for w in shown if path == base + w["slug"] + ".html"), None)
    if path != base + "index.html" and work is None:
        raise ValueError("Metadata requires an artwork currently shown in this gallery")
    artist_url = canonical(base + "index.html")
    url = canonical(path)
    person = {"@type": "Person", "@id": artist_url + "#artist", "name": a["display_name"], "url": artist_url}
    if a.get("website"):
        person["sameAs"] = [a["website"]]
    image = next((i for i in work["images"] if i["role"] == "main"), None) if work else a.get("portrait")
    graph = [person]
    page = {"@type": "WebPage" if work else "CollectionPage", "@id": url + "#page", "url": url,
            "name": work["title"] + " by " + a["display_name"] if work else a["display_name"] + " | PlotArt",
            "about": {"@id": person["@id"]}, "breadcrumb": {"@id": url + "#breadcrumbs"}}
    image_tags = []
    if image and image.get("derivatives"):
        derivative = max(image["derivatives"], key=lambda d: d["long_edge"])
        image_url = ORIGIN + base + "img/" + derivative["file"]
        image_obj = {"@type": "ImageObject", "@id": url + "#image", "contentUrl": image_url,
                     "url": image_url, "caption": image.get("alt", "")}
        if derivative.get("pixels"):
            image_obj.update(width=derivative["pixels"][0], height=derivative["pixels"][1])
        graph.append(image_obj)
        page["primaryImageOfPage"] = {"@id": image_obj["@id"]}
        esc = lambda x: html.escape(str(x), quote=True)
        image_tags = ['<meta property="og:image" content="%s">' % esc(image_url),
                      '<meta property="og:image:alt" content="%s">' % esc(image.get("alt", "")),
                      '<meta name="twitter:card" content="summary_large_image">',
                      '<meta name="twitter:image" content="%s">' % esc(image_url),
                      '<meta name="twitter:image:alt" content="%s">' % esc(image.get("alt", ""))]
        if derivative.get("pixels"):
            image_tags += ['<meta property="og:image:%s" content="%s">' % (k, v)
                           for k, v in zip(("width", "height"), derivative["pixels"])]
    crumbs = [("PlotArt", ORIGIN), ("Artists’ Gallery", canonical("gallery/index.html")), (a["display_name"], artist_url)]
    if work:
        art = {"@type": ["VisualArtwork", "Product"], "@id": url + "#artwork", "url": url, "name": work["title"],
               "creator": {"@id": person["@id"]}, "artMedium": work["medium"]}
        if work.get("description"):
            art["description"] = work["description"]
        if work.get("year"):
            art["dateCreated"] = str(work["year"])
        for key, field in (("height", "h_cm"), ("width", "w_cm"), ("depth", "d_cm")):
            if work.get(field):
                art[key] = {"@type": "QuantitativeValue", "value": work[field], "unitCode": "CMT"}
        if "primaryImageOfPage" in page:
            art["image"] = image_url
        offer = artwork_offer(work, url, person["@id"])
        if offer:
            art["offers"] = offer
        graph.append(art)
        page["mainEntity"] = {"@id": art["@id"]}
        crumbs.append((work["title"], url))
    else:
        page["mainEntity"] = {"@type": "ItemList", "numberOfItems": len(shown), "itemListElement": [
            {"@type": "ListItem", "position": n, "name": w["title"], "url": canonical(base + w["slug"] + ".html")}
            for n, w in enumerate(shown, 1)]}
    graph.extend([page, {"@type": "BreadcrumbList", "@id": url + "#breadcrumbs", "itemListElement": [
        {"@type": "ListItem", "position": n, "name": name, "item": href} for n, (name, href) in enumerate(crumbs, 1)]}])
    # Never allow public text containing </script> to terminate the JSON script.
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return META_BEGIN + "\n" + "\n".join(image_tags) + '\n<script type="application/ld+json">' + data + "</script>\n" + META_END


def enrich_artist(path, document, pkg, launch=None):
    block = artist_metadata(path, pkg, launch)
    if META_REGION.search(document):
        return META_REGION.sub(lambda m: block, document)
    if not block:
        return document
    if document.count("</head>") != 1:
        raise ValueError("Artist page must have exactly one head")
    return document.replace("</head>", block + "\n</head>", 1)
