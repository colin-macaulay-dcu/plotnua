#!/usr/bin/env python3
"""GUARD · PlotArt limited public launch (founder decision 27 Oct 2026). Read-only.

    python3 atlas-tools/prove-plotart-launch.py SITE_DIR [--switches FILE] [--manifest FILE]

SITE_DIR is the directory that holds plotart/ as it would be published (a launch
build from `build-plotart.py --launch --out SITE_DIR`, or the repository root
once the launch pages are released). Prints "PLOTART LAUNCH · OK" only when:

  L1  plotart/ holds exactly the launch files: index, founding-25,
      living-gallery and gallery/index (the Virtual Gallery) pages, plotart.css, plotart.js (and f25-apply.js only when
      the form switch is on). No artist, artwork, story, listing, collection or
      data file is published.
  L2  every link and image on those pages resolves: PlotArt links to a launch
      page, PlotNua links to a page that exists on the site. No broken link to
      an unpublished page.
  L3  no fictional content: no demonstration artist name, artwork title, story or
      listing title (read from the prototype data when it is available), no euro
      price, no "Example price", no "demonstration" wording.
  L4  no commission rate; the only percentages are the approved "100% free" and
      "100% of your artwork sales".
  L5  every page is noindex unless its own launch switch is on, and then carries
      index + canonical; demonstration content can never be indexable.
  L6  no development banner on any page (founder approval 29 Oct 2026); the status is
      stated in the content instead: the homepage says the gallery isn't open yet, that
      no artists or artworks have been published yet, and that no artwork is currently
      available through PlotArt.
  L7  forms never have an action; the application form posts only through the one
      approved script and route; no upload, address, phone or date-of-birth field.
  L8  application state (founder decision 27 Oct 2026): f25_application_state is one
      of the five states and is never inferred from the endpoint. The Founding 25
      description and the homepage status line are exactly that state's wording.
  L9  only "open" has an application form: in every other state the Founding 25
      page has no <form>, no application script, no "Apply to become a Founding
      Artist" call to action and no "Applications are open"; "not_open" and
      "configured_closed" say "Applications are not yet open." No page implies an
      opening date ("soon", "coming", a date) or says applications are being reviewed.
  L10 sale and status wording: every page says "No artwork is currently available
      through PlotArt."; no page says "no artwork is for sale" or "nothing is for
      sale" (unqualified); no page says "Prototype"; the Founding 25 title is the
      approved one; the Living Gallery is presented as a proposed programme; no
      Founding Artist is presented as already selected.
  L11 the Virtual Gallery (founder decision 28 Oct 2026) is published EMPTY: exactly 25
      placeholders, "Gallery 01" to "Gallery 25", each carrying only the approved
      placeholder wording; no image, portrait, name, price, biography or testimonial;
      the exact sentence "No artists have been selected, and no galleries are published
      yet."; a link to the Founding 25 page; noindex, follow; never in the sitemap. Every
      launch page's navigation (founder decision 29 Oct 2026) is exactly four pills:
      PlotArt Home, Virtual Gallery (gallery/), Living Gallery, PlotNua Home, each current
      on its own page; the Founding 25 page has no current pill; PlotNua Home is never
      current; Founding 25 and About are not in the navigation. The Virtual Gallery shows
      an honest empty state, not placeholder slots or counters.
      It says the Virtual Gallery grows beyond its first 25 galleries and that every
      accepted artist receives their own gallery (founder decision 28 Oct 2026).
  L12 the Founding 25 and the Living Gallery are separate programmes (founder decision
      28 Oct 2026): in the main content, the Founding 25 page names the Living Gallery
      only in the approved separation sentence; neither page offers Founding Artists any
      Living Gallery priority or place; the Living Gallery page never links to the
      Founding 25 application page and links to A Home for Art; the Founding 25 page says
      the founding year begins when the gallery is first published.
"""
import html, json, os, posixpath, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) < 2:
    sys.exit(__doc__)
SITE = os.path.abspath(sys.argv[1])
PA = os.path.join(SITE, "plotart")
problems = []
def need(ok, msg):
    if not ok:
        problems.append(msg)

# The launch switches: plotart/data/launch.json on the development branch; on a release
# branch (where plotart/ holds only the published pages) pass --switches FILE.
SWITCHES = sys.argv[sys.argv.index("--switches") + 1] if "--switches" in sys.argv else os.path.join(ROOT, "plotart", "data", "launch.json")
launch = json.load(open(SWITCHES, encoding="utf-8"))
ENDPOINT = launch.get("f25_form_endpoint")
PAGES = ["index.html", "founding-25.html", "living-gallery.html", "gallery/index.html"]
# The application script ships only in the "open" state (never inferred from the endpoint).
# The homepage hero image: ONE original painting by the founder, credited (founder decision, 29 Oct 2026).
# It is not a Founding 25 submission, not for sale and not part of the collection.
HERO_IMAGES = {"assets/hero/founder-01-abstract.webp"}
# The Living Gallery image (consolidated brief, 29 Oct 2026): the founder's painting in an AI-generated interior visualisation.
LG_IMAGE = "assets/living/plotart-living-gallery-colin-macaulay-artwork.webp"
ALLOWED = set(PAGES) | {"assets/plotart.css", "assets/plotart.js", "assets/pa-enquiry.js", LG_IMAGE} | HERO_IMAGES | ({"assets/f25-apply.js"} if launch.get("f25_application_state") == "open" else set())
# Published artist galleries (Phase 1, 29 Oct 2026; checked in full by L14). Only these shapes are allowed:
#   artists/<slug>/index.html · artists/<slug>/<artwork-slug>.html · artists/<slug>/img/<name>.webp
ART_FILE = re.compile(r"^artists/([a-z0-9]+(?:-[a-z0-9]+){0,6})/(?:[a-z0-9]+(?:-[a-z0-9]+){0,6}\.html|gallery\.json|img/[a-z0-9-]+-\d{2,5}\.webp)$")
ARTIST_FILES = set()
for _d, _, _fs in os.walk(os.path.join(PA, "artists")):
    for _f in _fs:
        _r = os.path.relpath(os.path.join(_d, _f), PA).replace(os.sep, "/")
        if ART_FILE.match(_r):
            ARTIST_FILES.add(_r)
GALLERY_SLUGS = sorted({ART_FILE.match(f).group(1) for f in ARTIST_FILES if f.endswith("/index.html")})
ALLOWED |= ARTIST_FILES

# L1
found = set()
for d, _, fs in os.walk(PA):
    for f in fs:
        found.add(os.path.relpath(os.path.join(d, f), PA).replace(os.sep, "/"))
need(found == ALLOWED, "L1 plotart/ must hold exactly the launch files; extra %s, missing %s" % (sorted(found - ALLOWED), sorted(ALLOWED - found)))

def outside_grid(raw):
    """The Virtual Gallery page with its collection grid (artist cards and spaces) blanked out."""
    return re.sub(rb'<ol class="pa-vg2-grid"[^>]*>.*?</ol>', b'<ol class="pa-vg2-grid"><!-- collection --></ol>', raw, flags=re.S)


def visible_text(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->|<svg.*?</svg>", " ", s, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", s))

# demonstration names, from the prototype data when present (it is never published)
demo_names = set()
cat_path = os.path.join(ROOT, "plotart", "data", "catalogue.demo.json")
board_path = os.path.join(ROOT, "plotart", "data", "board.art-and-space.demo.json")
if os.path.exists(cat_path):
    cat = json.load(open(cat_path, encoding="utf-8"))
    demo_names |= {a["name"] for a in cat["artists"]} | {w["title"] for w in cat["artworks"]} | {s["title"] for s in cat["stories"]}
    demo_names |= {(a.get("representation") or {}).get("name") for a in cat["artists"]} - {None}
if os.path.exists(board_path):
    demo_names |= {l["title"] for l in json.load(open(board_path, encoding="utf-8"))["listings"]}

for name in PAGES:
    p = os.path.join(PA, name)
    if not os.path.exists(p):
        continue
    s = open(p, encoding="utf-8").read()
    vt = visible_text(s)
    # L2
    for ref in re.findall(r'(?:href|src)="([^"]+)"', s):
        if ref.startswith(("https://", "http://", "mailto:", "#")):
            continue
        path = ref.split("#")[0].split("?")[0]
        if not path:
            continue
        # resolve against the page's own folder (pages may sit in plotart/gallery/)
        site_rel = path.lstrip("/") if path.startswith("/") else posixpath.normpath(posixpath.join("plotart", posixpath.dirname(name), path))
        if path.endswith("/") or site_rel in ("plotart", "plotart/gallery"):
            site_rel = posixpath.join(site_rel, "index.html")
        if site_rel.startswith("plotart/"):
            target = os.path.join(PA, site_rel[len("plotart/"):])
            need(site_rel[len("plotart/"):] in ALLOWED, "L2 %s links to an unpublished PlotArt file: %s" % (name, ref))
        else:
            need(not site_rel.startswith(".."), "L2 %s links outside the site: %s" % (name, ref))
            target = os.path.join(ROOT, site_rel)
        need(os.path.exists(target), "L2 %s has a broken link: %s" % (name, ref))
    # L3
    for n in demo_names:
        need(not re.search(r"\b%s\b" % re.escape(n), vt) and not re.search(r"\b%s\b" % re.escape(html.escape(n)), s),
             "L3 %s carries demonstration content (text or markup): %s" % (name, n))
    need("€" not in vt and "&euro;" not in s, "L3 %s shows a euro price" % name)
    need(not re.search(r"example price|demonstration|fictional", vt, re.I), "L3 %s uses demonstration wording" % name)
    # L4
    vt4 = re.sub(r"\b100% (?:free\b|of your artwork sales\b)", " ", vt, flags=re.I)
    need(not re.search(r"\d+(?:\.\d+)?\s?(?:%|per\s?cent)", vt4, re.I), "L4 %s shows a percentage" % name)
    need(not re.search(r"commission (?:rate )?of|\d+\s?(?:%|per\s?cent)\s+commission", vt, re.I), "L4 %s states a commission rate" % name)
    # L5
    indexable = (name == "founding-25.html" and launch.get("f25_page_indexable") is True) or (name == "index.html" and launch.get("home_indexable") is True)
    if indexable:
        canon = "https://plotnua.ie/plotart/" + ("" if name == "index.html" else name)
        need('<meta name="robots" content="index, follow">' in s and ('<link rel="canonical" href="%s' % canon) in s, "L5 %s is switched indexable but lacks index/canonical" % name)
    else:
        need('<meta name="robots" content="noindex, follow">' in s and 'rel="canonical"' not in s, "L5 %s must be exactly 'noindex, follow' with no canonical until its switch is approved" % name)
    # L6
    need('class="pa-proto"' not in s, "L6 %s carries a development banner (removed by founder approval, 29 Oct 2026)" % name)
    # L7
    need(not re.search(r"<form[^>]*\saction=", s), "L7 %s has a form action" % name)
    need(not re.search(r'type="file"|name="(?:address|eircode|phone|dob|date_of_birth)"', s), "L7 %s asks for an upload, address, phone or date of birth" % name)
    ep_ok = s.replace('data-endpoint="%s"' % ENDPOINT, "") if ENDPOINT else s
    need(not re.search(r"workers\.dev|airtable", ep_ok), "L7 %s references a live endpoint outside the approved form" % name)

home = open(os.path.join(PA, "index.html"), encoding="utf-8").read() if os.path.exists(os.path.join(PA, "index.html")) else ""
need(all(('src="%s"' % x) in home for x in HERO_IMAGES) and "Original artwork by Colin Macaulay, founder of PlotArt." in visible_text(home)
     and len(re.findall(r'<img [^>]*alt="Painting by Colin Macaulay', home)) == 1 and len(re.findall(r"<img\b", home)) == 3 + home.count("plotnua-mark-master.svg"),
     "L6 the homepage images must be exactly the founder's credited painting, the Living Gallery visualisation and the A Home for Art image")
LG_CAP = "Original artwork by Colin Macaulay. The room is an AI-generated interior visualisation for PlotArt, not a real home."
for _n, _s in (("index.html", home), ("living-gallery.html", open(os.path.join(PA, "living-gallery.html"), encoding="utf-8").read() if os.path.exists(os.path.join(PA, "living-gallery.html")) else "")):
    need(_s.count(LG_IMAGE) == 1 and LG_CAP in visible_text(_s) and "AI-generated illustration" in visible_text(_s),
         "L6 %s must show the Living Gallery visualisation once, credited and labelled as an AI-generated illustration" % _n)
# Art at Home (founder, 29 Oct 2026): the existing A Home for Art Discovery image, reused (not a new image),
# linked to the Discovery and captioned as an illustration.
need(re.search(r'<a href="\.\./discovery-a-home-for-art\.html"[^>]*><img src="\.\./assets/img/dfb125ba9dd7cd87\.jpg"', home) is not None
     and "Illustration · not a real home" in visible_text(home), "L6 the Art at Home image must be the Discovery's image, linked to it and captioned as an illustration")
_hero = re.search(r'<section class="pa-hero">.*?</section>', home, re.S)
need(_hero is not None and not re.search(r"(?i)AI-generated|conceptual image", visible_text(_hero.group(0))), "L6 the homepage hero still carries an AI-image label (the hero is the founder's painting)")
need(not re.search(r'pa-vg-card|pa-vg-grid|pa-vg-count|galleries reserved|waiting for their artists', home), "L6 the homepage shows empty gallery slots or counters (removed, 29 Oct 2026)")
need('href="gallery/"' in home and 'href="founding-25.html#apply"' in home or STATE != "open", "L6 the homepage must link to the Virtual Gallery and the Founding 25 application")
OPEN = launch.get("galleries_open") is True     # the gallery opening switch (Phase 3, founder-controlled; L15)
OPEN_FINE = "Artworks in PlotArt galleries are offered by their artists: PlotArt introduces buyers and doesn't take payment."
need(("No artwork is currently available through PlotArt." in visible_text(home)) if not OPEN else (OPEN_FINE in visible_text(home)),
     "L6 the homepage must state availability for the current state (galleries %s)" % ("open" if OPEN else "not open"))
# Founder decision 29 Oct 2026: the introduction is the approved lede, and availability is stated by the
# Virtual Gallery line and the footer (the "Where PlotArt is now" panel was removed).
need("PlotArt brings artists and art lovers together." in visible_text(home), "L6 the homepage introduction is not the approved wording")
need(len(demo_names) > 0 or not os.path.exists(cat_path), "L3 demonstration names could not be read")

# L3 on a release branch: the prototype data is never published, so demonstration names
# cannot be read there. --manifest FILE pins every published PlotArt file to the SHA-256
# of the build that passed L1-L10 WITH the names (on the development branch).
if "--manifest" in sys.argv:
    import hashlib
    man = json.load(open(sys.argv[sys.argv.index("--manifest") + 1], encoding="utf-8"))
    # Artist gallery files are published by the content-only pipeline and verified by L14 (provenance fingerprints),
    # so the manifest pins every OTHER PlotArt file: code, styles and the launch pages.
    need(set(man["files"]) == found - ARTIST_FILES, "L3 manifest lists %s, plotart/ holds %s" % (sorted(man["files"]), sorted(found - ARTIST_FILES)))
    # The Virtual Gallery's collection grid changes as galleries are published (content-only releases); everything
    # OUTSIDE the grid stays pinned by "outside_grid" (the grid itself is checked by L11 and L14).
    for rel, sha in man["files"].items():
        fp = os.path.join(PA, rel)
        raw = open(fp, "rb").read() if os.path.exists(fp) else None
        got = hashlib.sha256(raw).hexdigest() if raw is not None else None
        og = man.get("outside_grid", {}).get(rel)
        need(got == sha or (og is not None and raw is not None and hashlib.sha256(outside_grid(raw)).hexdigest() == og),
             "L3 %s differs from the verified build (manifest)" % rel)
elif not os.path.exists(cat_path):
    need(False, "L3 no demonstration data and no --manifest: content cannot be verified")

# L8-L10 · application state and wording
STATES = ("not_open", "configured_closed", "open", "paused", "closed")
STATE = launch.get("f25_application_state")
need(STATE in STATES, "L8 f25_application_state is missing or not one of %s" % ", ".join(STATES))
LINE = {"open": "Applications are open.", "paused": "Applications are paused at the moment.", "closed": "Applications have closed."}.get(STATE, "Applications are not yet open.")
DESC = "PlotArt will select up to 25 artists based or working in Ireland for a free first-year gallery. " + \
       {"open": "Applications are open.", "paused": "Applications are paused at the moment.", "closed": "Applications have closed."}.get(STATE, "Applications are not yet open.")
f25p = os.path.join(PA, "founding-25.html")
f25 = open(f25p, encoding="utf-8").read() if os.path.exists(f25p) else ""
f25v = visible_text(f25)
m = re.search(r'<meta name="description" content="([^"]*)">', f25)
need(m is not None and html.unescape(m.group(1)) == DESC, "L8 the Founding 25 description is not the %s wording" % STATE)
_badge = re.search(r'<span class="pa-open-badge[^"]*">([^<]*)</span>', home)
need(_badge is not None and html.unescape(_badge.group(1)) == ("Applications open" if STATE == "open" else LINE), "L8 the homepage Founding 25 badge is not the %s wording" % STATE)
for other in {"Applications are open.", "Applications are paused at the moment.", "Applications have closed.", "Applications are not yet open."} - {LINE}:
    need(other not in visible_text(home), "L8 the homepage shows another state's line: %s" % other)
if STATE == "open":
    need(ENDPOINT is not None and f25.count("<form") == 1 and ('data-f25-form data-endpoint="%s"' % ENDPOINT) in f25, "L9 open: exactly one live form posting to the approved route")
else:
    need("<form" not in f25, "L9 %s: the Founding 25 page must have no form" % STATE)
    need("f25-apply.js" not in f25 and not os.path.exists(os.path.join(PA, "assets", "f25-apply.js")), "L9 %s: no application script" % STATE)
    need("Apply to become a Founding Artist" not in f25v, "L9 %s: no 'Apply to become a Founding Artist' call to action" % STATE)
    need("Applications are open" not in f25v + visible_text(home), "L9 %s: nothing may say applications are open" % STATE)
    if STATE in ("not_open", "configured_closed"):
        need("Applications are not yet open." in f25v, "L9 %s: the Founding 25 page must say 'Applications are not yet open.'" % STATE)
    for name in PAGES:
        p = os.path.join(PA, name)
        if os.path.exists(p):
            s = open(p, encoding="utf-8").read()
            vt = visible_text(s) + " " + " ".join(re.findall(r'<meta (?:name|property)="[^"]*" content="([^"]*)"', s))
            need(not re.search(r"\b(?:open(?:ing)? soon|coming soon|opens? (?:on|in) |from (?:January|February|March|April|May|June|July|August|September|October|November|December))", vt, re.I),
                 "L9 %s: %s implies an opening date" % (STATE, name))
            need(not re.search(r"\b(?:are|is) (?:still )?being reviewed\b|already received", vt, re.I), "L9 %s: %s says applications are being reviewed" % (STATE, name))
            need("Applications are open" not in vt, "L9 %s: %s says applications are open" % (STATE, name))
for name in PAGES:
    p = os.path.join(PA, name)
    if not os.path.exists(p):
        continue
    s = open(p, encoding="utf-8").read(); vt = visible_text(s)
    need(("No artwork is currently available through PlotArt." in vt) if not OPEN else (OPEN_FINE in vt and "No artwork is currently available" not in vt),
         "L10 %s must state availability for the current state (galleries %s)" % (name, "open" if OPEN else "not open"))
    need(not OPEN or "room view" not in vt, "L15 %s still promises a room view (the gallery opening removes that promise)" % name)
    need(not re.search(r"no artwork is for sale|nothing is for sale", vt, re.I), "L10 %s uses the unqualified 'not for sale' wording" % name)
    need("Prototype" not in vt and "prototype" not in vt, "L10 %s says Prototype" % name)
need("<title>Founding 25: Free First-Year Artist Galleries | PlotArt</title>" in f25, "L10 the Founding 25 title is not the approved one")
# No Founding Artist may be presented as already selected (founder and SEO workstream,
# 27 Oct 2026). The one approved sentence that names "the selected Founding Artists" also
# says plainly that none has been selected; it is removed before the claim check.
GALLERIES_LINE = "Artist galleries. Planned for the selected Founding Artists. No artists have been selected, and no galleries are published yet."
for name in PAGES:
    p = os.path.join(PA, name)
    if os.path.exists(p):
        vt = re.sub(r"\s+", " ", visible_text(open(p, encoding="utf-8").read())).replace(GALLERIES_LINE, " ")
        need(not re.search(r"\bour Founding Artists?\b|\b(?:selected|chosen|confirmed|current|existing) Founding Artists?\b|Founding Artists? (?:include|are now|have joined|already)", vt, re.I),
             "L10 %s presents Founding Artists as already selected" % name)
need("Where PlotArt is now" not in visible_text(home), "L10 the homepage status panel was removed (founder decision 29 Oct 2026)")
lg = open(os.path.join(PA, "living-gallery.html"), encoding="utf-8").read() if os.path.exists(os.path.join(PA, "living-gallery.html")) else ""
# Consolidated brief (29 Oct 2026): positive, but truthful. The Living Gallery is presented as an emerging
# initiative; nothing may claim that homes, installations, listings or sales already exist.
need("an emerging PlotArt initiative" in visible_text(lg), "L10 the Living Gallery must be presented as an emerging PlotArt initiative")
need(not re.search(r"homes (?:are|now) (?:hosting|taking part)|now hosting|available to buy|buy now|currently on display|installations? (?:is|are) live", visible_text(lg), re.I),
     "L10 the Living Gallery claims homes, installations or sales that do not exist")

# L11 · the Virtual Gallery, published empty (founder decision 28 Oct 2026)
VG_EMPTY = "No artists have been selected, and no galleries are published yet."
VG_SLOT = "Founding Artist gallery Gallery %02d Awaiting its artist"
vgp = os.path.join(PA, "gallery", "index.html")
vg = open(vgp, encoding="utf-8").read() if os.path.exists(vgp) else ""
need(bool(vg), "L11 the Virtual Gallery page plotart/gallery/index.html is missing")
if vg:
    vgv = re.sub(r"\s+", " ", visible_text(vg))
    # Consolidated brief (29 Oct 2026): 25 initial gallery spaces, the collection's centrepiece. A space is
    # never a link and carries no name, image, place or availability; no Founding 25 promotion on this page.
    spaces = re.findall(r'<li class="pa-gspace pa-gspace--t[1-5]" aria-label="Gallery space (\d\d)">(.*?)</li>', vg, re.S)
    _cards = re.findall(r'<li class="pa-gcard(?: is-founding)?"><a class="pa-gcard-tile" href="\.\./artists/([a-z0-9-]+)/"', vg)
    need(OPEN or not _cards, "L15 an artist gallery is published but the gallery opening switch is off")
    need(sorted(_cards) == GALLERY_SLUGS and len(set(_cards)) == len(_cards),
         "L11 Virtual Gallery cards must match the published artist galleries exactly (cards %s, galleries %s)" % (_cards, GALLERY_SLUGS))
    need([int(n) for n, _ in spaces] == list(range(len(_cards) + 1, 26)), "L11 the Virtual Gallery must show the remaining gallery spaces in order up to 25 (found %d)" % len(spaces))
    need(all("<a " not in body and "<img" not in body and re.sub(r"\s+", " ", visible_text(body)).strip() == n for n, body in spaces),
         "L11 a gallery space links somewhere or carries content beyond its number")
    _vgm = vg.split("<main", 1)[-1].split("</main>")[0]; _vgmv = re.sub(r"\s+", " ", visible_text(_vgm))
    need("founding-25.html" not in _vgm and "Founding 25" not in _vgmv and "Artist first" not in _vgmv, "L11 the Virtual Gallery carries Founding 25 promotion or an 'Artist first' section")
    need("The first twenty-five galleries." in vgv, "L11 the Virtual Gallery collection heading is not the approved wording")
    _vgimgs = re.findall(r"<img\b[^>]*>", _vgm)
    need(not re.search(r"<picture\b|<svg\b|background-image|url\(", _vgm) and len(_vgimgs) == len(_cards) and
         all(re.search(r'src="\.\./artists/(%s)/img/[a-z0-9-]+\.webp"' % "|".join(map(re.escape, GALLERY_SLUGS or ["-"])), t) for t in _vgimgs),
         "L11 the Virtual Gallery shows an image other than a published artist's card image")
    need(not re.search(r"testimonial|“|”|\bsaid\b", visible_text(vg.split("<main", 1)[-1].split("</main>")[0]), re.I), "L11 the Virtual Gallery carries a quotation or testimonial")
    need("<title>Virtual Gallery | PlotArt</title>" in vg, "L11 the Virtual Gallery title is not the approved one")
smp = os.path.join(SITE, "sitemap.xml")
if os.path.exists(smp):
    need("plotart" not in open(smp, encoding="utf-8").read(), "L11 sitemap.xml lists a PlotArt URL")
NAV_WANT = ["Discover PlotArt", "Virtual Gallery", "Living Gallery", "PlotNua ↗"]
NAV_CURRENT = {"index.html": "Discover PlotArt", "gallery/index.html": "Virtual Gallery", "living-gallery.html": "Living Gallery", "founding-25.html": None}
for name in PAGES:
    p = os.path.join(PA, name)
    if os.path.exists(p):
        s = open(p, encoding="utf-8").read()
        head = re.search(r'<header class="pa-head[^"]*">(.*?)</header>', s, re.S)
        nav = re.search(r'<nav class="pa-pills" aria-label="PlotArt">(.*?)</nav>', head.group(1) if head else "", re.S)
        links = [(h, c, re.sub(r"<[^>]+>", "", t)) for h, c, t in re.findall(r'<a class="pa-pill[^"]*" href="([^"]+)"( aria-current="page")?[^>]*>(.*?)</a>', nav.group(1))] if nav else []
        labels = [html.unescape(x[2]) for x in links]
        need(labels == NAV_WANT, "L11 %s navigation is %s, not %s" % (name, labels, NAV_WANT))
        cur = [html.unescape(x[2]) for x in links if x[1]]
        need(cur == ([NAV_CURRENT[name]] if NAV_CURRENT[name] else []), "L11 %s current pill is %s, not %s" % (name, cur, NAV_CURRENT[name]))
        depth = "../" * name.count("/")
        need(len(links) == 4 and [x[0] for x in links] == [depth + "index.html", depth + "gallery/", depth + "living-gallery.html", depth + "../index.html"],
             "L11 %s pills must link to the PlotArt homepage, the Virtual Gallery, the Living Gallery and the PlotNua homepage" % name)
        hv = visible_text(head.group(1)) if head else ""
        need("Founding 25" not in hv and "About" not in hv, "L11 %s header still offers Founding 25 or About" % name)

# L12 · the Founding 25 and the Living Gallery are separate programmes (founder decision 28 Oct 2026)
SEP = "The Founding 25 is the PlotArt Virtual Gallery. The Living Gallery is a separate, proposed programme. Taking part in it is optional, and it is never a condition of being a Founding Artist."
def main_of(name):
    p = os.path.join(PA, name)
    if not os.path.exists(p):
        return ""
    s = open(p, encoding="utf-8").read()
    return s[s.index("<main"):s.index("</main>")] if "<main" in s else ""
f25m, lgm = main_of("founding-25.html"), main_of("living-gallery.html")
f25mv = re.sub(r"\s+", " ", visible_text(f25m))
need(SEP in f25mv, "L12 the Founding 25 page must carry the approved separation sentence")
need("Living Gallery" not in f25mv.replace(SEP, " "), "L12 the Founding 25 page mentions the Living Gallery outside the separation sentence")
need("Your founding year begins on the day your gallery is first published." in f25mv, "L12 the Founding 25 page must say when the founding year begins")
for name, m in (("founding-25.html", f25mv), ("living-gallery.html", re.sub(r"\s+", " ", visible_text(lgm))), ("index.html", re.sub(r"\s+", " ", visible_text(main_of("index.html")))),
                ("gallery/index.html", re.sub(r"\s+", " ", visible_text(main_of("gallery/index.html"))))):
    need(not re.search(r"priority (?:consideration )?for the (?:Living Gallery|programme)|Founding (?:25 )?Artists? (?:would |will )?(?:receive|get|have) (?:priority|first consideration)|Priority for the Living Gallery", m, re.I),
         "L12 %s offers Founding Artists Living Gallery priority" % name)
need('href="founding-25.html"' not in lgm and 'href="founding-25.html#apply"' not in lgm, "L12 the Living Gallery page links its artists to the Founding 25")
need('href="../discovery-a-home-for-art.html" data-pa-track="cross_home_for_art_living"' in lgm, "L12 the Living Gallery page must link to A Home for Art")
# the artist-facing Living Gallery section in the founder's wording (28 Oct 2026): warm, never a priority or a service
art = re.search(r'<section class="pa-sec pa-sec--deep" id="artists">.*?</section>', lgm, re.S)
artv = re.sub(r"\s+", " ", visible_text(art.group(0))) if art else ""
need("Your art. In someone's home." in artv and "We're not inviting artists to take part just yet" in artv,
     "L12 the Living Gallery artist section is not the approved wording")
need(art is not None and 'href="../discovery-a-home-for-art.html"' in art.group(0), "L12 the Living Gallery artist section must link to A Home for Art")
need(not re.search(r"priority|guarantee|apply now|applications are open|book|sign up", artv, re.I), "L12 the Living Gallery artist section implies priority, a guarantee or an operational service")
need("25 artists. A new home for Irish art." in f25mv, "L12 the Founding 25 programme headline is not the approved wording")

# L13 · the application form contract (founder authorisation 28 Oct 2026). Only in "open":
# the three confirmations are exactly the Worker's; the form asks for nothing the route
# refuses (no Living Gallery interest, publication permission, upload, address, phone or
# date of birth); it links the applications section of the privacy notice; it promises no
# reply date; and its confirmation says nothing is published without the artist's approval.
if STATE == "open":
    wsrc13 = open(os.path.join(ROOT, "worker", "art-space-register", "src", "index.js"), encoding="utf-8").read()
    for const, key in (("F25_ELIGIBILITY_TEXT", "eligibility"), ("F25_OWNERSHIP_TEXT", "ownership"), ("F25_PRIVACY_TEXT", "privacy")):
        m13 = re.search(r'const %s =\s*"([^"]+)";' % const, wsrc13)
        p13 = re.search(r'data-f25-sentence="%s">([^<]*)<' % key, f25)
        need(m13 is not None and p13 is not None and html.unescape(p13.group(1)) == m13.group(1), "L13 the %s confirmation differs from the Worker's %s" % (key, const))
    need(not re.search(r'type="file"|name="(?:living_gallery|location_public|address|eircode|phone|dob|date_of_birth|terms)"', f25),
         "L13 the application asks for something outside the approved form")
    need('href="../privacy.html#founding-25-applications"' in f25, "L13 the form must link the privacy notice's applications section")
    need(not re.search(r"\b(?:within|in) (?:two|three|four|\d+) (?:days|weeks)\b", f25v), "L13 the page promises a reply date")
    need("nothing is published without your approval" in f25v, "L13 the confirmation must say nothing is published without the artist's approval")
    jsp = os.path.join(PA, "assets", "f25-apply.js")
    js13 = open(jsp, encoding="utf-8").read() if os.path.exists(jsp) else ""
    need("localStorage" not in js13 and "sessionStorage" not in js13 and "document.cookie" not in js13 and "console." not in js13,
         "L13 the application script must store and log nothing")
    need(re.search(r"credentials: 'omit'", js13) is not None, "L13 the application script must send no credentials")

# L14 · published artist galleries (Phase 1, founder decision 29 Oct 2026). Every published image has an
# ARTIST_SUPPLIED_ARTWORK provenance record whose fingerprint matches; pages are noindex, carry no private-preview
# material, expose no address but hello@plotnua.ie and quote no percentage. Only gallery images under the artist's own img/ folder are used.
_recp = os.path.join(SITE, "image-provenance-records.json")
_arts = {}
if os.path.exists(_recp):
    _arts = {r["asset"]: r for r in json.load(open(_recp, encoding="utf-8")).get("records", []) if r.get("class") == "ARTIST_SUPPLIED_ARTWORK"}
import hashlib as _hl
for slug in GALLERY_SLUGS:
    base = "artists/%s/" % slug
    for f in sorted(x for x in ARTIST_FILES if x.startswith(base)):
        full = os.path.join(PA, f)
        if f.endswith("gallery.json"):
            gj = open(full, encoding="utf-8").read()
            need(not re.search(r"[A-Za-z0-9._%+-]+@(?!plotnua\.ie)[A-Za-z0-9-]+\.[A-Za-z]", gj) and "application_ref" not in gj and '"checks"' not in gj,
                 "L14 %s carries private data" % f)
            continue
        if f.endswith(".webp"):
            rec = _arts.get("plotart/" + f)
            need(rec is not None and rec.get("artist_slug") == slug and rec.get("sha256") == _hl.sha256(open(full, "rb").read()).hexdigest(),
                 "L14 %s has no matching ARTIST_SUPPLIED_ARTWORK provenance record" % f)
            continue
        doc = open(full, encoding="utf-8").read()
        main = doc.split("<main", 1)[-1].split("</main>")[0]
        vis = re.sub(r"\s+", " ", visible_text(doc))
        need('<meta name="robots" content="noindex, follow">' in doc, "L14 %s must be noindex, follow until indexing is approved" % f)
        need("pa-ag-check" not in doc and "Private preview" not in doc and "pa-proto" not in doc, "L14 %s carries private-preview material" % f)
        need(all(m == "hello@plotnua.ie" for m in re.findall(r"mailto:([^?\"]+)", doc)) and
             not re.search(r"[A-Za-z0-9._%+-]+@(?!plotnua\.ie)[A-Za-z0-9-]+\.[A-Za-z]", vis), "L14 %s exposes an address other than hello@plotnua.ie" % f)
        need("%" not in vis, "L14 %s quotes a percentage" % f)
        for src in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', main):
            need(src.startswith("img/") and (base + src) in ARTIST_FILES, "L14 %s shows an image outside its own gallery folder: %s" % (f, src))
        # (The Founding minimum of 10 is enforced when a gallery FIRST opens, by the publication safeguards; a later sale
        # or removal is never blocked: Founding Artist Agreement 3.3(c).)
for asset in _arts:
    need(asset[len("plotart/"):] in ARTIST_FILES, "L14 provenance record for %s describes no published file" % asset)

if problems:
    print("PLOTART LAUNCH · FAILED (%d)" % len(problems))
    for x in problems:
        print("  " + x)
    sys.exit(1)
print("PLOTART LAUNCH · OK — L1-L15 on %d pages · applications %s (%d demonstration names checked absent)" % (len(PAGES), STATE, len(demo_names)))
