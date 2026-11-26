#!/usr/bin/env python3
"""GUARD · PlotArt limited public launch (founder decision 27 Oct 2026). Read-only.

    python3 atlas-tools/prove-plotart-launch.py SITE_DIR [--switches FILE] [--manifest FILE]

SITE_DIR is the directory that holds plotart/ as it would be published (a launch
build from `build-plotart.py --launch --out SITE_DIR`, or the repository root
once the launch pages are released). Prints "PLOTART LAUNCH · OK" only when:

  L1  plotart/ holds exactly the launch files: index, founding-25,
      living-gallery, gallery/index (the Virtual Gallery), invitation and about pages, plotart.css, plotart.js (and f25-apply.js only when
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
  L18 Join PlotArt (Gallery Artist Programme Phase 3, 13 Nov 2026): gallery_application_state is one of four
      states and is never inferred from the endpoint. Nothing of the recruitment is published unless it is "open"
      (founder decision 13 Nov 2026): no join.html, curatorial-policy.html, pa-apply.js, homepage artist band or
      Founding 25 pointer. When open, they are exactly the build (build-plotart-join.py), with one form posting only
      to the approved route and the Worker's own confirmations; the only percentage is the approved 15% wording
      and the only price the approved worked example; no discount, waiver or individual-terms wording.
  L21 Three galleries, Phase A (founder approval 24 Nov 2026): the homepage opens with the one heading "A new home for
      Irish art." and the three gallery entrances exactly as build-plotart-galleries.py writes them; Contemporary (the
      existing gallery/, unchanged collection, order and Featured Artists) shows the founder's credited painting whole, never
      cropped; Spaces and Being stay "In preparation" (no other state is accepted before Phase E): their
      entrances and holding pages show no image, artist or artwork, are noindex and outside the sitemap, and nothing says
      they are open. The three gallery pages carry the same gallery tabs; every PlotArt page carries the one Galleries menu.
      Final curatorial identity (agreed by the founder 25 Nov 2026): Contemporary. · Spaces. · Being. (the full stop only on
      the homepage entrances and the gallery headings; never in navigation), each with the founder's exact tagline on its
      entrance and page and the exact curatorial introduction on its page, in the same heading block (pa-gt) on all three, at
      gallery/, spaces/ and being/. No page names Environment, Landscape Art, Places & Spaces or Portraiture as a gallery or
      links to environment/, landscape/, places-and-spaces/ or portraiture/, which are only generated redirect pages (noindex,
      canonical straight to the final address, outside the sitemap; no chains).
  L22 The homepage availability line (Commercial Conversion Sprint 1, founder approval 26 Nov 2026): one generated
      region directly under the heading, whose works, artists and lowest public price are recomputed here from the
      published galleries independently of the builder; it claims nothing the data does not hold (no "Irish", no
      online purchase) and links only to the available-artworks page; with nothing available there is no line.
  L16 Mobile Gallery (3 Nov 2026): no provider marked participating; the published provider data holds no internal
      notes, contacts, terms or prices; the unconfirmed-participation wording stays; nothing collects or sends
      homeowner information; no structured data. The page alone may be indexed and listed in the sitemap.
"""
import html, json, os, posixpath, re, sys
import plotart_business_rental as BUSINESS
import plotart_seo as SEO
import plotart_search_content as C
import plotart_opportunities as OPP
import plotart_featured as FEAT
import plotart_shell as SHELL
import importlib.util as _ilu
_gx_spec = _ilu.spec_from_file_location("build_plotart_galleries", os.path.join(os.path.dirname(os.path.abspath(__file__)), "build-plotart-galleries.py"))
GX = _ilu.module_from_spec(_gx_spec); _gx_spec.loader.exec_module(GX)
# the founder's entrance artwork for the galleries in preparation (null until an authorised work is supplied; L6, L21)
GX_ENTRANCES = sys.argv[sys.argv.index("--entrances") + 1] if "--entrances" in sys.argv else GX.ENTRANCES
try:
    GX_ART_COUNT = sum(1 for _a in GX.entrances(GX_ENTRANCES).values() if _a)
except (ValueError, OSError):
    GX_ART_COUNT = 0          # L21 reports the problem

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
PAGES = ["index.html", "founding-25.html", "living-gallery.html", "gallery/index.html", "invitation.html", "about.html",
         "mobile-gallery/index.html", "mobile-gallery/gallery.html"] + (["join.html", "curatorial-policy.html"] if launch.get("gallery_application_state") == "open" else []) + list(SEO.GENERATED_PATHS) + list(SEO.EDITORIAL_PATHS) + list(SEO.TOOL_PATHS)  # invitation.html: private Founding Artist invitation (noindex, mailto only, no form)
# Mobile Gallery (founder release authorisation, 3 Nov 2026): a public work-in-progress page (indexable only by its own
# switch) and an illustrative gallery profile that is never indexed while participation is unconfirmed.
MG_FILES = {"mobile-gallery/mobile-gallery.css", "mobile-gallery/mobile-gallery.js", "mobile-gallery/mobile-gallery-data.js",
            "mobile-gallery/img/mg-hero-colin-macaulay-880.webp",
            "mobile-gallery/img/mg-hero-colin-macaulay-600.webp"}
MG_URL = "https://plotnua.ie/plotart/mobile-gallery/"
# The application script ships only in the "open" state (never inferred from the endpoint).
# The homepage hero image: ONE original painting by the founder, credited (founder decision, 29 Oct 2026).
# It is not a Founding 25 submission, not for sale and not part of the collection.
HERO_IMAGES = {"assets/hero/founder-01-abstract.webp"}
# The Living Gallery image (consolidated brief, 29 Oct 2026): the founder's painting in an AI-generated interior visualisation.
LG_IMAGE = "assets/living/plotart-living-gallery-colin-macaulay-artwork.webp"
CAMPAIGN_IMAGES = {"assets/campaigns/one-painting-three-rooms-840.webp", "assets/campaigns/one-painting-three-rooms-1672.webp"}
ALLOWED = {"downloads/plotart-art-buying-checklist.pdf"} | set(PAGES) | MG_FILES | {"assets/plotart.css", "assets/plotart-guides.css", "assets/plotart-artworks.css", "assets/plotart-wall-size.css", "assets/plotart-wall-size.js", "assets/plotart.js", "assets/pa-enquiry.js", "assets/pa-basket.js", LG_IMAGE} | HERO_IMAGES | CAMPAIGN_IMAGES | ({"assets/f25-apply.js"} if launch.get("f25_application_state") == "open" else set()) | ({"assets/pa-apply.js", "assets/plotart-join.css"} if launch.get("gallery_application_state") == "open" else set())
# Join PlotArt (Phase 3, 13 Nov 2026): the application page and the curatorial policy; the script ships only in "open".
GA_STATE = launch.get("gallery_application_state")
GA_EP = launch.get("gallery_application_endpoint")
GA_OPEN = GA_STATE == "open"
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
# Artist opportunity lists (16 Nov 2026): the opportunities page and the lists' stylesheet (plotart_opportunities)
OPP_FILES = {"opportunities/index.html", "commissions/index.html", "assets/plotart-opportunities.css"}
ALLOWED |= OPP_FILES
ALLOWED |= {"assets/plotart-living.css"}
ALLOWED |= {"for-artists.html", "assets/plotart-for-artists.css"}   # the For artists page (17 Nov 2026)
# Art Services & Providers (founder brief 19 Nov 2026): the page and its stylesheet, reached by the "Services" tab
SERVICES_PAGE = "services.html"
# paused 19 Nov 2026 (founder; both providers asked for changes): the page, its stylesheet and the tab exist ONLY while the
# launch switch services_page is on. Off: no services file may exist and no page may link to it or carry the tab (L11).
SERVICES_ON = launch.get("services_page") is True
if SERVICES_ON:
    ALLOWED |= {SERVICES_PAGE, "assets/plotart-services.css"}
    # provider images, each hosted under a recorded written permission (image-rights-records.json; P4 binds every copy)
    ALLOWED |= {"assets/services/" + f for f in ("hang-it-hung-wall-1600.jpg", "hang-it-hung-wall-1600.webp",
                                                  "hang-it-hung-wall-800.webp", "hang-it-logo.png",
                                                  # FastLane Couriers, 22 Nov 2026 (owner-supplied; ORG-FASTLANE / IPO-FASTLANE-20261122)
                                                  "fastlane-van-1077.jpg", "fastlane-van-1077.webp", "fastlane-van-800.webp",
                                                  "fastlane-logo.png",
                                                  # DropBy, 25 Nov 2026 (supplier-supplied; ORG-DROPBY / IPO-DROPBY-20261125)
                                                  "dropby-logo-969.jpg", "dropby-logo-969.webp", "dropby-logo-800.webp",
                                                  # N.I. Couriers logo, 25 Nov 2026 (ORG-NICOURIERS / IPO-NICOURIERS-20261125)
                                                  "nicouriers-logo.png")}
    PAGES.append(SERVICES_PAGE)
# No prices on the Services page (Hang-It asked for its pricing to be removed, 19 Nov 2026): the ordinary L3 rule applies.
ALLOWED |= {"assets/plotart-refine.css", "assets/plotart-refine.js"}   # Refine on All Artworks (founder approval 21 Nov 2026)
# Three galleries, Phase A (founder approval 24 Nov 2026): the holding pages of the two galleries in preparation and the
# galleries stylesheet (L21). They are launch pages, so every L2-L10 rule applies to them as well.
GX_PAGES = ["spaces/index.html", "being/index.html"]
GX_LEGACY = ["environment/index.html", "landscape/index.html", "places-and-spaces/index.html", "portraiture/index.html"]   # former addresses: generated redirects only
PAGES += GX_PAGES
ALLOWED |= set(GX_PAGES) | {"assets/plotart-galleries.css"} | set(GX_LEGACY)
ALLOWED |= {"assets/plotart-beyond.css"}   # Beyond the Gallery on the homepage (founder brief 25 Nov 2026)
ALLOWED |= {"assets/plotart-featured.css"}   # Featured Artists in the Artists' Gallery (17 Nov 2026; was plotart-home.css on the homepage)   # the Living Gallery page refinement (17 Nov 2026)
# Art for Hire (Stage 3B-6): the page, its two assets and the fourth gallery tab exist ONLY when the founder switches
# art_for_hire_page on (release approval). Off (or absent): no hire file may exist and no page may link to it or carry the tab.
HIRE_ON = launch.get("art_for_hire_page") is True
BUSINESS_ON = HIRE_ON and launch.get("business_rental_information") is True
if BUSINESS_ON:
    ALLOWED.add(BUSINESS.PDF)
HIRE_FORM = launch.get("art_for_hire_enquiry_form") is True
HIRE_PAGE = "art-for-hire/index.html"
HIRE_FILES = {HIRE_PAGE, "art-for-hire/art-for-hire.css", "art-for-hire/hire-live.js"}
if HIRE_ON:
    ALLOWED |= HIRE_FILES
HIRE_BEGIN, HIRE_END = b"<!-- pa-hire-catalogue:begin -->", b"<!-- pa-hire-catalogue:end -->"


def outside_hire(raw):
    """The Art for Hire page with its generated catalogue region blanked out (as outside_grid)."""
    a, b = raw.find(HIRE_BEGIN), raw.find(HIRE_END)
    if raw.count(HIRE_BEGIN) != 1 or raw.count(HIRE_END) != 1 or not 0 <= a < b:
        return raw
    return raw[:a] + HIRE_BEGIN + b"<!-- catalogue -->" + raw[b:]

# L1
found = set()
for d, _, fs in os.walk(PA):
    for f in fs:
        found.add(os.path.relpath(os.path.join(d, f), PA).replace(os.sep, "/"))
need(found == ALLOWED, "L1 plotart/ must hold exactly the launch files; extra %s, missing %s" % (sorted(found - ALLOWED), sorted(ALLOWED - found)))

VG_BEGIN, VG_END = b"<!-- pa-vg-collection:begin -->", b"<!-- pa-vg-collection:end -->"


def outside_grid(raw):
    """The Virtual Gallery page with its generated collection region (Direction C2, 5 Nov 2026: the open galleries
    and the twenty-five positions, between the two markers) blanked out. Without exactly one pair of markers the
    page is returned unchanged, so it can never match the pinned fingerprint."""
    a, b = raw.find(VG_BEGIN), raw.find(VG_END)
    if raw.count(VG_BEGIN) != 1 or raw.count(VG_END) != 1 or not 0 <= a < b:
        return raw
    raw = raw[:a] + VG_BEGIN + b"<!-- collection -->" + raw[b:]
    # The opening row (one curated gallery, 26 Nov 2026) above the collection is generated too; its content is checked
    # by L20. Without exactly one pair of its markers the page is returned unchanged (never matches the pin).
    try:
        return FEAT.outside(raw.decode()).encode()
    except ValueError:
        return raw + b"<!-- no featured region -->"


def visible_text(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->|<svg.*?</svg>", " ", s, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", s))

AP_FILE = '<input id="ap-images" type="file" accept="image/jpeg,image/png,image/webp" multiple hidden data-ap-file>'
# Design refinement (founder direction 14 Nov 2026): the 15% appears ONLY once, in plain type, in "The practical details" on
# join.html. No figure, no emphasis, nothing on the homepage.
APPROVED_15_MARKUP = []
APPROVED_15_TEXT = ["PlotArt’s commission is 15% of the price of an original work or signed limited-edition print sold to a collector PlotArt introduced to you"]

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
        # tel: (22 Nov 2026, FastLane Couriers' telephone on the Services page): a phone link, never a site file
        if ref.startswith(("https://", "http://", "mailto:", "#")) or re.fullmatch(r"tel:\+\d{8,15}", ref):
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
    if name not in SEO.GENERATED_PATHS:
        need("€" not in vt and "&euro;" not in s, "L3 %s shows a euro price" % name)
    else:
        try:
            need(C.update(s, name, SEO.public_packages(SITE)) == s, "L3 %s has stale or unapproved collection content" % name)
            need("€" not in visible_text(C.outside(s)), "L3 %s has an ungoverned price outside its collection" % name)
        except ValueError as e:
            need(False, "L3 " + str(e))
    need(not re.search(r"example price|demonstration|fictional", vt, re.I), "L3 %s uses demonstration wording" % name)
    # L4
    vt4 = re.sub(r"\b100% (?:free\b|of your artwork sales\b)", " ", vt, flags=re.I)
    s4 = s
    if name == "join.html":   # the standard Gallery Artist terms, in the approved wording only (founder, 13-14 Nov 2026)
        for _m in APPROVED_15_MARKUP:
            s4 = s4.replace(_m, " ")
        vt4 = visible_text(s4)
        vt4 = re.sub(r"\b100% (?:free\b|of your artwork sales\b)", " ", vt4, flags=re.I)
        for _t in APPROVED_15_TEXT:
            vt4 = vt4.replace(_t, " ")
    need(not re.search(r"\d+(?:\.\d+)?\s?(?:%|per\s?cent)", vt4, re.I), "L4 %s shows a percentage" % name)
    need(not re.search(r"commission (?:rate )?of|\d+\s?(?:%|per\s?cent)\s+commission", vt4, re.I), "L4 %s states a commission rate" % name)
    # L5
    indexable = SEO.indexable(name, launch)
    if indexable:
        canon = SEO.canonical(name)
        need(s.count('<meta name="robots" content="index, follow">') == 1 and 'noindex' not in re.sub(r'<!--.*?-->', '', s.split('</head>')[0], flags=re.S)
             and re.findall(r'<link rel="canonical" href="([^"]+)"', s) == [canon],
             "L5 %s is switched indexable but lacks exact index/canonical" % name)
    else:
        need('<meta name="robots" content="noindex, follow">' in s and 'rel="canonical"' not in s,
             "L5 %s must be exactly 'noindex, follow' with no canonical until its switch is approved" % name)
    # L6
    need('class="pa-proto"' not in s, "L6 %s carries a development banner (removed by founder approval, 29 Oct 2026)" % name)
    # L7
    need(not re.search(r"<form[^>]*\saction=", s), "L7 %s has a form action" % name)
    # The ONE permitted upload (founder approval of development, 29 Oct 2026): artwork images on the Founding 25 form,
    # JPG/PNG/WebP only, sent only to the approved route's /image address.
    F25_FILE = '<input id="f25-images" type="file" accept="image/jpeg,image/png,image/webp" multiple hidden data-f25-file>'
    s7 = s.replace(F25_FILE, "", 1) if name == "founding-25.html" else s.replace(AP_FILE, "", 1) if (name == "join.html" and GA_OPEN) else s
    need(not re.search(r'type="file"|name="(?:address|eircode|phone|dob|date_of_birth)"', s7), "L7 %s asks for an upload (other than artwork images), address, phone or date of birth" % name)
    ep_ok = s.replace('data-endpoint="%s"' % ENDPOINT, "").replace('data-image-endpoint="%s/image"' % ENDPOINT, "") if ENDPOINT else s
    if name == "join.html" and GA_OPEN and GA_EP:
        ep_ok = ep_ok.replace('data-endpoint="%s"' % GA_EP, "", 1).replace('data-image-endpoint="%s/image"' % GA_EP, "", 1)
    # The one approved plain LINK to a workers.dev address (founder decision 17 Nov 2026): the PlotArt Studio, behind its own
    # sign-in, from the footer and the For artists page. Exactly this href, never a form or data endpoint.
    ep_ok = ep_ok.replace('href="https://plotart-studio.colin-a41.workers.dev/"', "")
    need(not re.search(r"workers\.dev|airtable", ep_ok), "L7 %s references a live endpoint outside the approved form" % name)

home = open(os.path.join(PA, "index.html"), encoding="utf-8").read() if os.path.exists(os.path.join(PA, "index.html")) else ""
need(all(('src="%s"' % x) in home for x in HERO_IMAGES) and "Original artwork by Colin MacAulay, founder of PlotArt." in visible_text(home)
     and len(re.findall(r'<img [^>]*alt="Painting by Colin MacAulay', home)) == 1 and len(re.findall(r"<img\b", home)) == 6 + GX_ART_COUNT + home.count("plotnua-mark-master.svg") + home.count('<img class="pa-logo" ') + home.count('<img class="pa-pn-p" ')   # + the PlotArt logo in the header (31 Oct 2026) and the PlotNua house P in the PlotNua link (19 Nov 2026)
     and len(re.findall(r'<img src="mobile-gallery/img/mg-hero-colin-macaulay-880\.webp"', home)) == 1   # the Mobile Gallery illustration (25 Nov 2026)
     , "L6 the homepage images must be exactly the founder's credited painting, the Living Gallery visualisation, the Mobile Gallery illustration, the three-room calculator invitation, the A Home for Art image"
     " and the founder's painting in the Art for Hire film-set illustration (Beyond the Gallery, 25 Nov 2026)"
     " (no featured section: Featured Artists moved to the Artists' Gallery, 17 Nov 2026)")
need("pa-home-featured" not in home and "pa-home-feat" not in home and "plotart-home.css" not in home and "data-pa-home-item" not in home,
     "L6 the homepage still carries the featured artworks section (moved to the Artists' Gallery, founder brief 17 Nov 2026)")
need(all(x in home for x in CAMPAIGN_IMAGES) and 'aria-labelledby="sizePromoH"' in home
     and 'href="art-size-calculator.html" aria-label="Try the PlotArt art size calculator"' in home
     and 'These are illustrative rooms, not photographs of real homes. The painting is not offered for sale.' in visible_text(home),
     "L6 the calculator campaign must be complete, linked, credited and visibly disclosed")
LG_CAP = "Original artwork by Colin MacAulay. The room is an AI-generated interior visualisation for PlotArt, not a real home."
for _n, _s in (("index.html", home), ("living-gallery.html", open(os.path.join(PA, "living-gallery.html"), encoding="utf-8").read() if os.path.exists(os.path.join(PA, "living-gallery.html")) else "")):
    need(_s.count(LG_IMAGE) == 1 and LG_CAP in visible_text(_s) and "AI-generated illustration" in visible_text(_s),
         "L6 %s must show the Living Gallery visualisation once, credited and labelled as an AI-generated illustration" % _n)
# Art at Home (founder, 29 Oct 2026): the existing A Home for Art Discovery image, reused (not a new image),
# linked to the Discovery and captioned as an illustration.
need(re.search(r'<a href="\.\./discovery-a-home-for-art\.html"[^>]*><img src="\.\./assets/img/dfb125ba9dd7cd87\.jpg"', home) is not None
     and "Illustration · not a real home" in visible_text(home), "L6 the Art at Home image must be the Discovery's image, linked to it and captioned as an illustration")
# Three galleries (24 Nov 2026): the gallery entrances replaced the hero; the founder's painting is now the Contemporary Art
# entrance and must still carry no AI-image label.
_hero = re.search(r'<section class="pa-gx".*?</section>', home, re.S)
need(_hero is not None and not re.search(r"(?i)AI-generated|conceptual image", visible_text(_hero.group(0))), "L6 the homepage gallery entrances carry an AI-image label (the Contemporary Art entrance is the founder's painting)")
need(not re.search(r'pa-vg-card|pa-vg-grid|pa-vg-count|galleries reserved|waiting for their artists', home), "L6 the homepage shows empty gallery slots or counters (removed, 29 Oct 2026)")
# The application link is required only while applications are open. The state is read here directly: STATE itself is
# defined with L8 below, and this line raised a NameError in every state but "open" (found closing Founding 25, 13 Nov 2026).
need('href="gallery/"' in home and ('href="founding-25.html#apply"' in home or launch.get("f25_application_state") != "open"), "L6 the homepage must link to the Virtual Gallery and, while applications are open, the Founding 25 application")
OPEN = launch.get("galleries_open") is True     # the gallery opening switch (Phase 3, founder-controlled; L15)
OPEN_FINE = "Artworks in PlotArt galleries are offered by their artists: PlotArt introduces buyers; the artist is the seller."
need(("No artwork is currently available through PlotArt." in visible_text(home)) if not OPEN else (OPEN_FINE in visible_text(home)),
     "L6 the homepage must state availability for the current state (galleries %s)" % ("open" if OPEN else "not open"))
# Founder decision 29 Oct 2026: the introduction is the approved lede, and availability is stated by the
# Virtual Gallery line and the footer (the "Where PlotArt is now" panel was removed).
# Three galleries (founder decisions 24 Nov 2026): the homepage has one heading, "A new home for Irish art.", directly above
# the gallery entrances, and no introductory label or lede (the earlier introduction was retired with the hero).
need(re.findall(r"<h1\b[^>]*>(.*?)</h1>", home, re.S) == ["A new home for Irish art."] and "Three curated galleries" not in visible_text(home),
     "L6 the homepage heading must be exactly 'A new home for Irish art.' with no added label")
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
        oh = man.get("outside_hire_catalogue", {}).get(rel)
        guide_pin = man.get("outside_search_content", {}).get(rel)
        guide_ok = False
        if guide_pin is not None and raw is not None and rel in SEO.GENERATED_PATHS:
            try:
                guide_ok = hashlib.sha256(C.outside(raw.decode()).encode()).hexdigest() == guide_pin
            except ValueError:
                pass
        # the artist opportunity lists (16 Nov 2026): outside their generated region (and, on the Art for Hire page, outside
        # the works catalogue too) the four pages are pinned by "outside_opportunity_lists"; the lists are checked by L19
        # Featured Artists (17 Nov 2026): the Artists' Gallery page's "outside_grid" pin covers everything outside BOTH of its
        # generated regions (the collection and Featured Artists); the homepage has no generated region any more and is
        # pinned in full. A page that matches its full pin must also match its outside-the-regions pin (no stale pin).
        need("outside_home_featured" not in man, "L3 the manifest still pins a homepage featured region (moved to the Artists' Gallery)")
        need(og is None or raw is None or got != sha or hashlib.sha256(outside_grid(raw)).hexdigest() == og,
             "L3 %s: its outside_grid pin is stale (re-pin it with the page)" % rel)
        oo, opp_ok = man.get("outside_opportunity_lists", {}).get(rel), False
        if oo is not None and raw is not None and rel in OPP.PAGES:
            try:
                blank = OPP.outside(raw.decode()).encode()
                opp_ok = hashlib.sha256(outside_hire(blank) if rel == HIRE_PAGE else blank).hexdigest() == oo
            except ValueError:
                pass
        # a page that matches its full pin must also match its outside-the-lists pin, so a re-pin of the page can never
        # leave the lists pin stale (found 16 Nov 2026: 43930cd re-pinned living-gallery.html only, which would have
        # refused the first Living Gallery listing at publish time)
        need(oo is None or raw is None or got != sha or opp_ok,
             "L3 %s: its outside_opportunity_lists pin is stale (re-pin it with the page)" % rel)
        need(got == sha or guide_ok or opp_ok or (og is not None and raw is not None and hashlib.sha256(outside_grid(raw)).hexdigest() == og)
             or (oh is not None and raw is not None and hashlib.sha256(outside_hire(raw)).hexdigest() == oh),
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
_badge = re.findall(r'<span class="pa-open-badge[^"]*">([^<]*)</span>', home)
# Since Join PlotArt (13 Nov 2026) the homepage band is the artist-application band and its badge follows
# gallery_application_state (L18); the Founding 25 state is then shown only on the Founding 25 page.
_HOME_STATE = "open" if GA_OPEN else STATE        # closed recruitment: the homepage keeps the closed Founding 25 band
_HOME_LINE = {"open": "Applications are open.", "paused": "Applications are paused at the moment.", "closed": "Applications have closed."}.get(_HOME_STATE, "Applications are not yet open.")
need(len(_badge) == 1 and html.unescape(_badge[0]) == ("Submissions open" if GA_OPEN else "Applications open" if _HOME_STATE == "open" else _HOME_LINE), "L8 the homepage badge is not the %s wording" % _HOME_STATE)
for other in {"Applications are open.", "Applications are paused at the moment.", "Applications have closed.", "Applications are not yet open."} - {_HOME_LINE}:
    need(other not in visible_text(home), "L8 the homepage shows another state's line: %s" % other)
if STATE == "open":
    need(ENDPOINT is not None and f25.count("<form") == 1 and ('data-f25-form data-endpoint="%s"' % ENDPOINT) in f25, "L9 open: exactly one live form posting to the approved route")
else:
    need("<form" not in f25, "L9 %s: the Founding 25 page must have no form" % STATE)
    need("f25-apply.js" not in f25 and not os.path.exists(os.path.join(PA, "assets", "f25-apply.js")), "L9 %s: no application script" % STATE)
    need("Apply to become a Founding Artist" not in f25v, "L9 %s: no 'Apply to become a Founding Artist' call to action" % STATE)
    need("Applications are open" not in f25v + visible_text(home), "L9 %s: nothing may say applications are open" % STATE)   # the homepage badge reads "Applications open"
    if STATE in ("not_open", "configured_closed"):
        need("Applications are not yet open." in f25v, "L9 %s: the Founding 25 page must say 'Applications are not yet open.'" % STATE)
    for name in PAGES:
        p = os.path.join(PA, name)
        if os.path.exists(p):
            s = open(p, encoding="utf-8").read()
            vt = visible_text(s) + " " + " ".join(re.findall(r'<meta (?:name|property)="[^"]*" content="([^"]*)"', s))
            # "opens on/in" counts only when a date or a time follows ("opens in March", "opens in a few weeks"): the private
            # invitation page's "it opens in the PlotArt Artists' Gallery" names a place, not a date (13 Nov 2026).
            # "New work coming soon" is the approved empty state of a gallery whose artist has withdrawn every work (founder
            # decision 1 Nov 2026); it is about artwork, not applications, so it is set aside here. Without this, closing
            # applications would make the content pipeline refuse a live withdrawal (found by the journey proof, 13 Nov 2026).
            vt = vt.replace("New work coming soon", " ")
            need(not re.search(r"\b(?:open(?:ing)? soon|coming soon|opens? (?:on|in) (?:the )?(?:\d|early|mid|late|spring|summer|autumn|winter|a few|the (?:coming|next|new) |(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b|(?:next|this) )|from (?:January|February|March|April|May|June|July|August|September|October|November|December))", vt, re.I),
                 "L9 %s: %s implies an opening date" % (STATE, name))
            need(not re.search(r"\b(?:are|is) (?:still )?being reviewed\b|already received", vt, re.I), "L9 %s: %s says applications are being reviewed" % (STATE, name))
            if not (name == "join.html" and GA_OPEN):   # Join PlotArt has its own state (L18)
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
    # Gallery order (founder decision 31 Oct 2026): the founder places artists in positions 01-25 and may reserve a
    # position. Item N of the grid (N <= 25) is position N: a published artist's card, or space N (its number, or its
    # number and RESERVED). Cards beyond the 25 positions follow. A space never links, shows an image or names anyone.
    # Direction C2 (founder approval 5 Nov 2026): between the two markers, the open galleries hang as works (one per
    # published gallery, in position order, then any without a position), followed by the index of the twenty-five
    # founding positions. Position N of the index is: the published artist placed there (number, name, link to that
    # gallery), or its number and exactly one of Reserved / In preparation / Available -- never a name, link or image.
    _ra, _rb = vg.find(VG_BEGIN.decode()), vg.find(VG_END.decode())
    _region = vg[_ra:_rb] if (vg.count(VG_BEGIN.decode()) == 1 and vg.count(VG_END.decode()) == 1 and 0 <= _ra < _rb) else ""
    need(bool(_region), "L11 the Virtual Gallery collection region (pa-vg-collection markers) is missing or duplicated")
    # One curated gallery (founder approval 26 Nov 2026): below the opening row, "Explore the Gallery" introduces every
    # other artist with the editorial card (artwork, title and year, photo credit, name, practice and public location,
    # a short introduction from their own biography, View Gallery), in the founder's order, each artist ONCE across the
    # opening row and the cards. No position numbers, no Founding positions index, no prices.
    _gl = re.search(r'\n  <ol class="pa-fa-list pa-gl n-([123])" aria-label="Artists in the gallery">(.*?)\n  </ol>', _region, re.S)
    _items = re.findall(r'\n    <li class="pa-fa-item( is-textonly)?" data-pa-curated="([a-z0-9-]+):([a-z0-9]+)">(.*?)</li>', _gl.group(2), re.S) if _gl else []
    need(not _gl or len(re.findall(r"<li\b", _gl.group(2))) == len(_items), "L11 the gallery holds something other than artist cards")
    need(not re.search(r'pa-vgc-n\b|<span class="pa-vgc-sr">Position|data-pa-position', _region),
         "L11 the gallery shows or carries position numbers again (removed 23 Nov 2026; the founder's arrangement orders it)")
    _cards, _bad_work, _textonly = [], [], 0
    for _to, _sl, _ch, _w in _items:
        _cards.append(_sl)
        _imgs = re.findall(r"<img\b[^>]*>", _w)
        _own = re.compile(r"\.\./artists/%s/img/[a-z0-9-]+\.webp" % re.escape(_sl))
        _urls = []
        for t in _imgs:
            _src = re.search(r'\ssrc="([^"]*)"', t); _set = re.search(r'\ssrcset="([^"]*)"', t)
            _urls += [_src.group(1) if _src else ""] + ([x.strip().split(" ")[0] for x in _set.group(1).split(",")] if _set else [])
        _links = re.findall(r'href="([^"]*)"', _w)
        _textonly += bool(_to)
        if len(_imgs) != (0 if _to else 1) or not all(_own.fullmatch(u) for u in _urls) \
                or not _links or not all(re.fullmatch(r"\.\./artists/%s/(?:[a-z0-9-]+\.html)?" % re.escape(_sl), h) for h in _links):
            _bad_work.append(_sl)
    need(_gl is not None or not GALLERY_SLUGS, "L11 the gallery has published artists but no artist cards")
    need(not _gl or int(_gl.group(1)) == min(len(_items), 3), "L11 the gallery's size class does not match the number of cards")
    need(not _bad_work, "L11 an artist card is malformed, links elsewhere or shows another artist's image (%s)" % _bad_work)
    need(not re.search(r'pa-vgc-(index|plan|pos|line|key)\b|vgIdxH', vg) and "Founding positions" not in vgv
         and not re.search(r"\b(twenty-five|25) (numbered )?positions\b", vgv, re.I),
         "L11 the Artists' Gallery shows the founding positions index again (removed from public view 21 Nov 2026)")
    need("pa-vgc-count" not in vg and not re.search(r"\d+ of 25 galleries", vgv), "L11 the Artists' Gallery still shows the 25-gallery counter")
    need(OPEN or not _cards, "L15 an artist gallery is published but the gallery opening switch is off")
    # every published artist exactly once: the opening row, then the cards; an artist whose opening place is empty (held)
    # is the only one left out, and only while held
    try:
        _arr = FEAT.arrangement_in(vg)
        _opening = [x["artist"] for x in _arr["opening"]]; _held = _arr["held"]
    except ValueError:
        _opening, _held = [], []
        need(False, "L11 the Contemporary gallery's opening row or collection region is missing or duplicated")
    _all = _opening + _cards
    need(len(set(_all)) == len(_all) and sorted(set(_all) | set(_held)) == sorted(GALLERY_SLUGS) and not set(_held) & set(_all),
         "L11 the gallery must introduce every published artist exactly once (opening %s, cards %s, held %s, galleries %s)" % (_opening, _cards, _held, GALLERY_SLUGS))
    try:
        _vg_nf = FEAT.outside(vg)
    except ValueError:
        _vg_nf = vg
    _vgm = _vg_nf.split("<main", 1)[-1].split("</main>")[0]; _vgmv = re.sub(r"\s+", " ", visible_text(_vgm))
    need("founding-25.html" not in _vgm and "Founding 25" not in _vgmv and "Artist first" not in _vgmv, "L11 the Virtual Gallery carries Founding 25 promotion or an 'Artist first' section")
    need('<h2 id="vgColH">Explore the Gallery</h2>' in vg and "Explore More Artists" not in vgv and "Artists in Focus" not in vgv and "twenty-five galleries" not in vgv,
         "L11 the gallery heading is not the approved wording (Explore the Gallery, 26 Nov 2026; Artists in Focus retired)")
    _vgall = vg.split("<main", 1)[-1].split("</main>")[0]
    need(not re.search(r"€|\bEUR\b|Price on request|\bprice\b|\bsold\b|\bcm\b", re.sub(r"\s+", " ", visible_text(_vgall)), re.I),
         "L11 the gallery overview shows prices or sale details (they stay in the artists' galleries and Browse All Artworks)")
    _vgimgs = re.findall(r"<img\b[^>]*>", _vgm)
    # A published gallery with no works on show keeps its place with the empty state and no picture (founder decision
    # 1 Nov 2026): one picture per open gallery, except those. Every picture is a published artist's own work image.
    need(not re.search(r"<picture\b|<svg\b|background-image|url\(", _vgm) and len(_vgimgs) == len(_cards) - _textonly and
         all(re.search(r'src="\.\./artists/(%s)/img/[a-z0-9-]+\.webp"' % "|".join(map(re.escape, GALLERY_SLUGS or ["-"])), t) for t in _vgimgs),
         "L11 the Virtual Gallery shows an image other than a published artist's own work image")
    # (artwork titles in the cards' credit lines are the artists' own titles and may carry quotation marks)
    need(not re.search(r"testimonial|“|”|\bsaid\b", visible_text(re.sub(r"<figcaption\b.*?</figcaption>", " ", _vgm, flags=re.S)), re.I), "L11 the Virtual Gallery carries a quotation or testimonial")
    # search title changed by the founder for the three-gallery Phase A (24 Nov 2026); the address /plotart/gallery/ is unchanged
    need("<title>Contemporary Irish Art Gallery | PlotArt</title>" in vg and vg.count("Contemporary Irish Art Gallery | PlotArt") == 3,
         "L11 the Contemporary Art gallery's search title (title, og:title, twitter:title) is not the approved one")
smp = os.path.join(SITE, "sitemap.xml")
if os.path.exists(smp):
    _sm = re.findall(r"<loc>([^<]*plotart[^<]*)</loc>", open(smp, encoding="utf-8").read())
    _packages = SEO.public_packages(SITE)
    _want_sm = [SEO.canonical(p) for p in SEO.sitemap_paths(_packages, launch)] + ([MG_URL] if launch.get("mobile_gallery_indexable") is True else [])
    need(len(_sm) == len(set(_sm)) and sorted(_sm) == sorted(_want_sm),
         "L11 sitemap must list exactly the approved indexable PlotArt pages, no drafts or withdrawn works")
    _xml = open(smp, encoding="utf-8").read()
    try:
        need(SEO.update_sitemap(_xml, _packages, launch) == _xml, "L11 generated PlotArt sitemap region is stale")
    except ValueError as e:
        need(False, "L11 " + str(e))
    _az = re.search(r'<nav class="pa-vgc-az" aria-labelledby="vgAzH">(.*?)</nav>', vg, re.S)
    _azlinks = re.findall(r'<a href="../artists/([a-z0-9-]+)/" data-pa-track="vg_artist_az">([^<]+)</a>', _az.group(1)) if _az else []
    _azwant = [(p["artist"]["slug"], html.escape(p["artist"]["display_name"], quote=True))
               for p in sorted(_packages, key=lambda p: (p["artist"]["display_name"].casefold(), p["artist"]["slug"]))]
    need(_azlinks == _azwant and (bool(_az) == bool(_packages)), "L11 artist A-Z must match approved public names exactly")
# Three galleries (24 Nov 2026): the Artists' Gallery and Mobile Gallery pills became the one Galleries menu, which must sit
# straight after Discover PlotArt and be exactly the shell's (checked below, with its current link).
# Mobile Gallery is its own pill again, straight after the Galleries menu and before Living Gallery and Art for Hire, the order
# of the homepage's Beyond the Gallery tiles (founder decisions, 25 Nov 2026).
NAV_WANT = ["Discover PlotArt", "Mobile Gallery", "Living Gallery", "PlotNua ↗"]
if HIRE_ON:
    NAV_WANT.insert(3, "Art for Hire")                                                    # the fourth gallery tab (3B-6)
if SERVICES_ON:
    NAV_WANT.insert(len(NAV_WANT) - 1, "Services")                                        # Art Services & Providers (19 Nov 2026)
NAV_CURRENT = {"index.html": "Discover PlotArt", "gallery/index.html": None, "living-gallery.html": "Living Gallery", "founding-25.html": None, "invitation.html": None, "about.html": None,
               "mobile-gallery/index.html": "Mobile Gallery", "mobile-gallery/gallery.html": "Mobile Gallery", "spaces/index.html": None, "being/index.html": None}
# the page each Galleries menu link is current on (the menu itself is then marked as the current section)
DD_CURRENT = {"gallery/index.html": "contemporary", "spaces/index.html": "spaces", "being/index.html": "being"}
NAV_CURRENT.update({p: None for p in SEO.GENERATED_PATHS + SEO.EDITORIAL_PATHS + SEO.TOOL_PATHS if p not in SEO.HOME_PATHS})   # the homepage stays 'Discover PlotArt' (Sprint 1)
NAV_CURRENT.update({"join.html": None, "curatorial-policy.html": None})
NAV_CURRENT[HIRE_PAGE] = "Art for Hire"
NAV_CURRENT[SERVICES_PAGE] = "Services"
for name in PAGES + ([HIRE_PAGE] if HIRE_ON else []):
    p = os.path.join(PA, name)
    if os.path.exists(p):
        s = open(p, encoding="utf-8").read()
        head = re.search(r'<header class="pa-head[^"]*">(.*?)</header>', s, re.S)
        nav = re.search(r'<nav class="pa-pills%s" aria-label="PlotArt">(.*?)</nav>' % (" pa-pills--hire" if HIRE_ON else ""), head.group(1) if head else "", re.S)
        links = [(h, c, re.sub(r"<[^>]+>", "", t)) for h, c, t in re.findall(r'<a class="pa-pill[^"]*" href="([^"]+)"( aria-current="page")?[^>]*>(.*?)</a>', nav.group(1))] if nav else []
        labels = [html.unescape(x[2]) for x in links]
        need(labels == NAV_WANT, "L11 %s navigation is %s, not %s" % (name, labels, NAV_WANT))
        cur = [html.unescape(x[2]) for x in links if x[1]]
        need(cur == ([NAV_CURRENT[name]] if NAV_CURRENT[name] else []), "L11 %s current pill is %s, not %s" % (name, cur, NAV_CURRENT[name]))
        depth = "../" * name.count("/")
        mg_href = "index.html" if name.startswith("mobile-gallery/") else depth + "mobile-gallery/"
        want_hrefs = [depth + "index.html", mg_href, depth + "living-gallery.html"] + ([depth + "art-for-hire/"] if HIRE_ON else []) + ([depth + "services.html"] if SERVICES_ON else []) + [depth + "../index.html"]
        need(len(links) == len(want_hrefs) and [x[0] for x in links] == want_hrefs,
             "L11 %s pills must link to the PlotArt homepage, Mobile Gallery, the Living Gallery, Art for Hire, Services and the PlotNua homepage" % name)
        _dd = SHELL.galleries_menu(depth, DD_CURRENT.get(name), mg_href=mg_href)
        need(nav is not None and nav.group(1).count("data-pa-dd") == 1 and re.match(r'<a class="pa-pill"[^>]*>Discover PlotArt</a>' + re.escape(_dd), nav.group(1)) is not None,
             "L11 %s must carry the one Galleries menu, exactly as the shell writes it, straight after Discover PlotArt" % name)
        hv = visible_text(head.group(1)) if head else ""
        need("Founding 25" not in hv and "About" not in hv, "L11 %s header still offers Founding 25 or About" % name)

if not SERVICES_ON:
    for _d, _, _fs in os.walk(PA):
        for _f in _fs:
            if _f.endswith(".html"):
                _t = open(os.path.join(_d, _f), encoding="utf-8").read()
                need("services.html" not in _t and 'data-pa-track="nav_services' not in _t,
                     "L11 %s links to the paused Services page or carries its tab" % os.path.relpath(os.path.join(_d, _f), PA))

# L21 · three galleries, Phase A (founder approval 24 Nov 2026)
_gx_states = {k: launch.get(k + "_gallery_state") for k in ("spaces", "being")}
try:
    PROV_RECORDS = json.load(open(os.path.join(SITE, "image-provenance-records.json"), encoding="utf-8")).get("records", [])
except (OSError, ValueError):
    PROV_RECORDS = []
need(all(v in SHELL.GALLERY_STATES for v in _gx_states.values()),
     "L21 Spaces and Being must stay in_preparation until Phase E (switches: %s)" % _gx_states)
_retired = [k for k in ("environment_gallery_state", "landscape_gallery_state", "places_and_spaces_gallery_state", "portraiture_gallery_state") if k in launch]
need(not _retired, "L21 retired gallery switches must not come back (%s); the switches are spaces_gallery_state and being_gallery_state" % _retired)
try:
    _gx_arts = GX.entrances(GX_ENTRANCES)
except (ValueError, OSError) as _e:
    _gx_arts = {}
    need(False, "L21 " + str(_e))
try:
    _gx_built = GX.plan(SITE, GX_ENTRANCES)
except ValueError as _e:
    _gx_built = {}
    need(False, "L21 " + str(_e))
for _rel, _doc in _gx_built.items():
    _fp = os.path.join(PA, _rel)
    need(os.path.exists(_fp) and open(_fp, encoding="utf-8").read() == _doc,
         "L21 %s is not exactly what build-plotart-galleries.py writes (run it, then re-pin)" % _rel)
# the homepage entrances: three, in order; only Contemporary Art shows artwork, and only the founder's credited painting
_gx_sec = re.search(r'<section class="pa-gx".*?</section>', home, re.S)
_tiles = re.findall(r'<li class="pa-gx-tile" data-pa-gallery="([a-z_]+)">(.*?)</li>', _gx_sec.group(0) if _gx_sec else "", re.S)
need([k for k, _ in _tiles] == ["contemporary", "spaces", "being"], "L21 the homepage must carry exactly the three gallery entrances, in order")
# the editorial full stop: on the entrance headings, each with the founder's exact tagline
for _k, _t in _tiles:
    _g = GX.GALLERY[_k]
    need(("<h2>%s.</h2>" % _g["title"]) in _t and ('<p class="pa-gx-text">%s</p>' % html.escape(_g["text"], quote=True)) in _t,
         "L21 the %s entrance must read '%s.' with its approved tagline" % (_k, _g["title"]))
for _k, _t in _tiles:
    _imgs = re.findall(r"<img\b[^>]*>", _t)
    _tv = visible_text(_t)
    if _k == "contemporary":
        need(len(_imgs) == 1 and 'src="assets/hero/founder-01-abstract.webp"' in _imgs[0] and "Gallery open" in _tv and 'href="gallery/"' in _t,
             "L21 the Contemporary Art entrance must show only the founder's credited painting and enter gallery/")
    else:
        _a = _gx_arts.get(_k)
        need("In preparation" in _tv and "Gallery open" not in _tv and not re.search(r'href="[^"]*artists/', _t) and ('href="%s"' % GX.HREF[_k]) in _t,
             "L21 the %s entrance must say In preparation, link only to its holding page and never to an artist" % _k)
        if not _a:
            need(not _imgs, "L21 the %s entrance shows an image but no authorised entrance artwork is recorded" % _k)
        else:
            # authorised artwork only (founder refinement 24 Nov 2026): one of the artist's own published images with an
            # ARTIST_SUPPLIED_ARTWORK provenance record for an artwork, the per-use consent reference, and a credit
            _rec = next((r for r in PROV_RECORDS if r.get("asset") == "plotart/" + _a["image"]), None)
            need(len(_imgs) == 1 and ('src="%s"' % _a["image"]) in _imgs[0] and os.path.exists(os.path.join(PA, _a["image"]))
                 and _rec is not None and _rec.get("class") == "ARTIST_SUPPLIED_ARTWORK" and _rec.get("subject") == "artwork"
                 and _rec.get("artist_slug") == _a["artist_slug"] and _rec.get("work_slug")
                 and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{5,}", str(_a["consent_ref"])) is not None
                 and html.escape(_a["credit"], quote=True) in _t and _a["credit"].strip(),
                 "L21 the %s entrance artwork must be an artist's published artwork with a provenance record, a per-use consent reference and a credit" % _k)
# artwork in an entrance is shown whole: the galleries stylesheet never crops (object-fit:cover) and contains the image
_gx_css = open(os.path.join(PA, "assets", "plotart-galleries.css"), encoding="utf-8").read() if os.path.exists(os.path.join(PA, "assets", "plotart-galleries.css")) else ""
need("object-fit:cover" not in _gx_css.replace(" ", "") and re.search(r"\.pa-gx-art img\{[^}]*object-fit:contain", _gx_css) is not None,
     "L21 gallery entrance artwork must be shown whole (object-fit:contain), never cropped")
# the holding pages: in preparation, nothing published in them, nothing implying they are open
for _rel in GX_PAGES:
    _fp = os.path.join(PA, _rel)
    _s = open(_fp, encoding="utf-8").read() if os.path.exists(_fp) else ""
    _m = _s.split("<main", 1)[-1].split("</main>")[0]
    _mv = re.sub(r"\s+", " ", visible_text(_m))
    need(bool(_s) and "In preparation" in _mv and not re.findall(r"<img\b", _m) and "artists/" not in _m and "pa-vg-collection" not in _s
         and "pa-featured-artists" not in _s and not re.search(r"Artists in Focus|Explore More Artists|Gallery open|now open|is open\b", _mv),
         "L21 %s must be a holding page: In preparation, with no artist, artwork, image or gallery section, and nothing saying it is open" % _rel)
    need('<meta name="robots" content="noindex, follow">' in _s, "L21 %s must be noindex while in preparation" % _rel)
# the gallery tabs: the same three tabs on the three gallery pages, the page's own tab current
for _rel, _key in (("gallery/index.html", "contemporary"), ("spaces/index.html", "spaces"), ("being/index.html", "being")):
    _fp = os.path.join(PA, _rel)
    _s = open(_fp, encoding="utf-8").read() if os.path.exists(_fp) else ""
    need(_s.count('<nav class="pa-gtabs"') == 1 and SHELL.gallery_tabs("../", _key) in _s, "L21 %s must carry the gallery tabs with its own tab current" % _rel)
# final curatorial identity (agreed by the founder 25 Nov 2026): the founder's exact headings, taglines and introductions
_GX_WORDS = {"contemporary": ("Contemporary", "Abstraction, expression and experimentation.", None),   # no introduction (founder, 26 Nov 2026)
             "spaces": ("Spaces", "The spaces we inhabit, encounter and imagine.",
                        "Exploring our relationship with the world around us, from natural landscapes and coastlines to urban environments, "
                        "architecture, interiors and imagined places."),
             "being": ("Being", "Life, identity, emotion and existence.",
                       "Exploring what it means to exist through portraiture, figurative art, identity, relationships, emotion and interpretations of life.")}
need({k: (g["title"], g["text"], g["intro"]) for k, g in GX.GALLERY.items()} == _GX_WORDS,
     "L21 the gallery names, taglines and introductions must be exactly the founder's approved wording (25 Nov 2026)")
# each gallery page opens with the same heading block: heading with its full stop, the tagline, then the introduction
for _rel, _key, _hid in (("gallery/index.html", "contemporary", "vgH"), ("spaces/index.html", "spaces", "ghH"), ("being/index.html", "being", "ghH")):
    _fp = os.path.join(PA, _rel)
    _s = open(_fp, encoding="utf-8").read() if os.path.exists(_fp) else ""
    _w = _GX_WORDS[_key]
    _blk = ('<div class="pa-gt"><h1 class="pa-gt-h" id="%s">%s.</h1>\n  <p class="pa-gt-tag">%s</p>%s</div>'
            % (_hid, _w[0], html.escape(_w[1], quote=True), ('\n  <p class="pa-gt-intro">%s</p>' % html.escape(_w[2], quote=True)) if _w[2] else ""))
    if not _w[2]:
        need("pa-gt-intro" not in _s and "Exploring artistic expression" not in _s, "L21 %s must carry no introduction (founder, 26 Nov 2026)" % _rel)
    need(_s.count('class="pa-gt"') == 1 and _blk in _s and _s.count("<h1") == 1,
         "L21 %s must open with the shared heading block: '%s.', its tagline and its introduction" % (_rel, _w[0]))
    if _key != "contemporary":
        need(("<title>%s | In Preparation | PlotArt</title>" % _w[0]) in _s, "L21 %s must carry the approved name in its title" % _rel)
# the shared heading block has one style for all three galleries
need(re.search(r"\.pa-gt \.pa-gt-h\{", _gx_css) is not None and re.search(r"\.pa-gt \.pa-gt-tag\{", _gx_css) is not None
     and re.search(r"\.pa-gt \.pa-gt-intro\{", _gx_css) is not None, "L21 the gallery heading block (pa-gt) must be styled once, for all three galleries")
# no full stop in functional navigation: the Galleries menu, phone Menu, gallery tabs and footer use the plain names on every page
need(all(re.search(r'data-pa-track="nav_gallery_%s(?:_menu)?">%s<' % (k, S_), home) for k, S_ in (("contemporary", "Contemporary"), ("spaces", "Spaces"), ("being", "Being"))),
     "L21 the navigation must name the galleries Contemporary, Spaces and Being, without full stops")
_STOP = re.compile(r'data-pa-track="(?:nav_gallery_|gallery_tab_)[a-z_]+(?:_menu)?">(?:Contemporary|Spaces|Being)\.|<li><a href="[^"]*(?:gallery|spaces|being)/">(?:Contemporary|Spaces|Being)\.</a>')
for _d, _, _fs in os.walk(PA):
    for _f in _fs:
        if _f.endswith(".html"):
            _t = open(os.path.join(_d, _f), encoding="utf-8").read()
            need(not _STOP.search(_t), "L21 the navigation must name the galleries Contemporary, Spaces and Being, without full stops (%s)" % os.path.relpath(os.path.join(_d, _f), PA))
# the former addresses: generated redirects straight to the final address (no chains), noindex, outside the sitemap
for _rel in GX_LEGACY:
    _lg = open(os.path.join(PA, _rel), encoding="utf-8").read() if os.path.exists(os.path.join(PA, _rel)) else ""
    _to = GX.HREF[GX.LEGACY[_rel][0]]
    need(_lg == GX.legacy_redirect(_rel) and '<meta name="robots" content="noindex, follow">' in _lg and ('<link rel="canonical" href="https://plotnua.ie/plotart/%s">' % _to) in _lg
         and ('location.replace("../%s"' % _to) in _lg and ('content="0; url=../%s"' % _to) in _lg and "<main" not in _lg and "<img" not in _lg
         and _to not in [r_.split("/")[0] + "/" for r_ in GX_LEGACY],
         "L21 %s must be exactly the generated permanent redirect straight to %s (noindex, canonical, script and no-script redirect)" % (_rel, _to))
_sm = open(smp, encoding="utf-8").read() if os.path.exists(smp) else ""
need(not any("/" + _r.split("/")[0] + "/" in _sm for _r in GX_LEGACY + GX_PAGES), "L21 no redirect and no holding page may be in the sitemap while in preparation")
_OLD = re.compile(r'href="(?:\.\./)*(?:environment|landscape|places-and-spaces|portraiture)/|nav_gallery_(?:environment|landscape|places_and_spaces|portraiture)|'
                  r'gallery_tab_environment|data-pa-gallery="environment"|>Environment<|Environment\.</h|Landscape Art|Places &amp; Spaces|>Portraiture<|>Contemporary Art<|Contemporary Art\.')
for _d, _, _fs in os.walk(PA):
    for _f in _fs:
        _rp = os.path.relpath(os.path.join(_d, _f), PA).replace(os.sep, "/")
        if _f.endswith(".html") and _rp not in GX_LEGACY:
            _t = open(os.path.join(_d, _f), encoding="utf-8").read()
            need(not _OLD.search(_t), "L21 %s still uses a former gallery name or links to a former gallery address" % _rp)
# every PlotArt page with a header carries the one Galleries menu (the three galleries only), no Artists' Gallery pill, and
# Mobile Gallery exactly once, as its own pill straight after the Galleries menu and before Living Gallery (founder decisions, 25 Nov 2026)
for _d, _, _fs in os.walk(PA):
    for _f in _fs:
        if _f.endswith(".html"):
            _t = open(os.path.join(_d, _f), encoding="utf-8").read()
            if 'class="pa-pills' in _t:
                _navm = re.search(r'<nav class="pa-pills[^"]*" aria-label="PlotArt">(.*?)</nav>', _t, re.S)
                _nv = _navm.group(1) if _navm else ""
                need(_t.count("data-pa-dd") == 1 and 'data-pa-track="nav_virtual_gallery' not in _t
                     and len(re.findall(r'data-pa-track="nav_mobile_gallery"', _nv)) == 1
                     and re.search(r'</details><a class="pa-pill" href="[^"]*"(?: aria-current="page")? data-pa-track="nav_mobile_gallery">Mobile Gallery</a><a class="pa-pill" href="[^"]*"(?: aria-current="page")? data-pa-track="nav_living_gallery">Living Gallery</a>', _nv) is not None,
                     "L21 %s must carry exactly one Galleries menu (three galleries), no Artists’ Gallery pill, and the Mobile Gallery pill straight after the Galleries menu, before Living Gallery" % os.path.relpath(os.path.join(_d, _f), PA))
# Beyond the Gallery (founder brief 25 Nov 2026): straight after the three galleries, the Mobile Gallery, Living Gallery and Art
# for Hire, in that order, each with a picture, a status, a short text and one link to its own page. Every picture is the
# founder's painting in a disclosed illustration; no gallery is named or implied to take part, and nothing claims a live service.
_bg = re.search(r'<!-- pa-galleries:end -->\s*<!-- pa-beyond:begin.*?-->(.*?)<!-- pa-beyond:end -->', home, re.S)
need(_bg is not None and '<h2 id="beyondH">Beyond the Gallery.</h2>' in (_bg.group(1) if _bg else ""),
     "L21 the homepage must carry 'Beyond the Gallery.' straight after the three galleries")
if _bg:
    _bgt = _bg.group(1)
    _tiles = re.findall(r'<li class="pa-bg-tile" data-pa-beyond="([a-z-]+)">(.*?)</li>', _bgt, re.S)
    need([k for k, _ in _tiles] == ["mobile-gallery", "living-gallery", "art-for-hire"],
         "L21 Beyond the Gallery must show Mobile Gallery, Living Gallery and Art for Hire, in that order")
    _bg_href = {"mobile-gallery": "mobile-gallery/", "living-gallery": "living-gallery.html", "art-for-hire": "art-for-hire/"}
    _bg_img = {"mobile-gallery": {"mobile-gallery/img/mg-hero-colin-macaulay-880.webp", "mobile-gallery/img/mg-hero-colin-macaulay-600.webp"},
               "living-gallery": {"assets/living/plotart-living-gallery-colin-macaulay-artwork.webp"},
               "art-for-hire": {"assets/hero/founder-01-abstract.webp"}}
    for _k, _t in _tiles:
        if _k not in _bg_href:
            continue                                   # already refused by the order rule above
        _links = re.findall(r'<a [^>]*href="([^"]+)"', _t)
        _imgs = set(re.findall(r'<img [^>]*src="([^"]+)"', _t)) | set(u.split(" ")[0] for ss in re.findall(r'srcset="([^"]+)"', _t) for u in ss.split(", "))
        need(_links == [_bg_href[_k]], "L21 the %s tile must link only to its own page (%s)" % (_k, _links))
        need(bool(_imgs) and _imgs <= _bg_img[_k], "L21 the %s tile may show only its declared illustration (%s)" % (_k, sorted(_imgs)))
        need(re.search(r'<span class="pa-chip pa-chip--illus">(AI-generated illustration|Illustration)</span>', _t) is not None and "Colin MacAulay" in _t,
             "L21 the %s tile's picture must carry its illustration label and the founder's credit" % _k)
        need('<p class="pa-bg-status">' in _t and "<h3>" in _t, "L21 the %s tile needs its status and title" % _k)
    _bgv = re.sub(r"\s+", " ", visible_text(_bgt))
    need(not re.search(r"Artworld|Doorway|Sol Art|Gormley|Trinity Gallery|Gallery Kinsale|participat|partner|book (a|an|your)|appointments? (are|is) available", _bgv, re.I),
         "L21 Beyond the Gallery must not name a prospective gallery or imply a gallery, booking or appointment is confirmed")
    need("appointments can’t yet be arranged through PlotArt" in _bgv and "no homes are taking part yet" in _bgv,
         "L21 Beyond the Gallery must keep the Mobile Gallery and Living Gallery status sentences")
    need("Not offered for hire." in _bgv, "L21 the Art for Hire picture must say the founder's painting is not offered for hire")

# the homepage states the real status of the Living Gallery and Art for Hire (founder decision 5, 24 Nov 2026)
_hv = re.sub(r"\s+", " ", visible_text(home))
need("no homes are taking part yet" in _hv and not re.search(r"Real art\. Real homes\.|displayed in real homes", _hv),
     "L21 the homepage must present the Living Gallery as a programme in development (no homes are taking part yet)")
need(("Hire enquiries are not yet open." in _hv) == (not HIRE_FORM) and (not HIRE_ON or 'href="art-for-hire/"' in home),
     "L21 the homepage must say Art for Hire enquiries are not yet open exactly while the enquiry form is off")

# L12 · the Founding 25 and the Living Gallery are separate programmes (founder decision 28 Oct 2026)
SEP = "The Founding 25 is the PlotArt Artists’ Gallery. The Living Gallery is a separate, proposed programme. Taking part in it is optional, and it is never a condition of being a Founding Artist."
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
# the artist-facing Living Gallery section in the founder's wording (revised 16 Nov 2026: artists can register interest in
# their Studio's Opportunities section): warm and optional, never a priority, a guarantee, a confirmed placement or a
# public Studio address
art = re.search(r'<section class="pa-sec pa-sec--deep" id="artists">.*?</section>', lgm, re.S)
artv = re.sub(r"\s+", " ", visible_text(art.group(0))) if art else ""
for _lg_need in ("Your art. In someone’s home.", "Imagine your work becoming part of someone’s everyday life.",
                 "Taking part is entirely optional.", "agreed before anything proceeds.",
                 "If you’re already a PlotArt artist, you can register your interest through the Opportunities section of your Artist Studio."):
    need(_lg_need in artv, "L12 the Living Gallery artist section is not the approved wording (missing: %s)" % _lg_need)
need(art is not None and not re.search(r'href="https?://|workers\.dev|<form\b', art.group(0)), "L12 the Living Gallery artist section must not link out, expose a Studio address or carry a form")
need(art is not None and 'href="gallery/" data-pa-track="living_artists_gallery">Explore the Artists’ Gallery</a>' in art.group(0), "L12 the Living Gallery artist section must link to the Artists' Gallery")
need(not re.search(r"confirmed placement|placement is confirmed|will be placed|we will place", artv, re.I), "L12 the Living Gallery artist section implies a confirmed placement")
need(not re.search(r"priority|guarantee|apply now|applications are open|book|sign up", artv, re.I), "L12 the Living Gallery artist section implies priority, a guarantee or an operational service")
need("25 artists. A new home for Irish art." in f25mv, "L12 the Founding 25 programme headline is not the approved wording")

# L13 · the application form contract (founder authorisation 28 Oct 2026). Only in "open":
# the three confirmations are exactly the Worker's; the form asks for nothing the route
# refuses (no Living Gallery interest, publication permission, upload other than artwork images, address, phone or
# date of birth); it links the applications section of the privacy notice; it promises no
# reply date; and its confirmation says nothing is published without the artist's approval.
if STATE == "open":
    wsrc13 = open(os.path.join(ROOT, "worker", "art-space-register", "src", "index.js"), encoding="utf-8").read()
    for const, key in (("F25_ELIGIBILITY_TEXT", "eligibility"), ("F25_OWNERSHIP_TEXT", "ownership"), ("F25_PRIVACY_TEXT", "privacy")):
        m13 = re.search(r'const %s =\s*"([^"]+)";' % const, wsrc13)
        p13 = re.search(r'data-f25-sentence="%s">([^<]*)<' % key, f25)
        need(m13 is not None and p13 is not None and html.unescape(p13.group(1)) == m13.group(1), "L13 the %s confirmation differs from the Worker's %s" % (key, const))
    f25u = f25.replace('<input id="f25-images" type="file" accept="image/jpeg,image/png,image/webp" multiple hidden data-f25-file>', "", 1)
    need('data-image-endpoint="%s/image"' % ENDPOINT in f25 or 'type="file"' not in f25, "L13 artwork images must go only to the approved route's /image address")
    need(not re.search(r'type="file"|name="(?:living_gallery|location_public|address|eircode|phone|dob|date_of_birth|terms)"', f25u),
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
        if SEO.indexable(f, launch):
            need(doc.count('<meta name="robots" content="index, follow">') == 1 and 'noindex' not in re.sub(r'<!--.*?-->', '', doc.split('</head>')[0], flags=re.S)
                 and re.findall(r'<link rel="canonical" href="([^"]+)"', doc) == [SEO.canonical(f)],
                 "L14 %s must have exact public index/canonical" % f)
        else:
            need('<meta name="robots" content="noindex, follow">' in doc and 'rel="canonical"' not in doc,
                 "L14 %s must stay noindex without the artist indexing switch" % f)
        need("pa-ag-check" not in doc and "Private preview" not in doc and "pa-proto" not in doc, "L14 %s carries private-preview material" % f)
        need(all(m == "hello@plotnua.ie" for m in re.findall(r"mailto:([^?\"]+)", doc)) and
             not re.search(r"[A-Za-z0-9._%+-]+@(?!plotnua\.ie)[A-Za-z0-9-]+\.[A-Za-z]", vis), "L14 %s exposes an address other than hello@plotnua.ie" % f)
        need("%" not in vis, "L14 %s quotes a percentage" % f)
        for src in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', main):
            need(src.startswith("img/") and (base + src) in ARTIST_FILES, "L14 %s shows an image outside its own gallery folder: %s" % (f, src))
        # (A gallery opens with at least one artwork, enforced by the publication safeguards; afterwards the artist may
        # withdraw every work and the gallery shows its empty state: founder decisions 1 Nov 2026.)
for asset in _arts:
    need(asset[len("plotart/"):] in ARTIST_FILES, "L14 provenance record for %s describes no published file" % asset)

# L17 · Art for Hire (Stage 3B-6). Switched off: nothing of it exists or is linked. Switched on: the page, its assets and the
# tab are exactly as built, the page is noindex, every card ships hidden (the live check shows it), every card is a work
# that is available in its artist's published gallery, no contact details, prices or forms are in the HTML, and the enquiry
# form is present only with its own switch (legal and privacy approval).
for d, _, fs in os.walk(PA):
    for f in fs:
        if not f.endswith(".html"):
            continue
        rel = os.path.relpath(os.path.join(d, f), PA).replace(os.sep, "/")
        doc = open(os.path.join(d, f), encoding="utf-8").read()
        tab = 'data-pa-track="nav_art_for_hire"' in doc
        if not HIRE_ON:
            need("art-for-hire/" not in doc and not tab and "pa-pills--hire" not in doc, "L17 %s links to Art for Hire or carries its tab, but art_for_hire_page is off" % rel)
        elif 'class="pa-pills' in doc:
            need(tab and "pa-pills--hire" in doc and doc.count('href="') and 'data-pa-track="nav_art_for_hire_menu"' in doc,
                 "L17 %s lacks the Art for Hire tab (pill and Menu) although art_for_hire_page is on" % rel)
_css = open(os.path.join(PA, "assets", "plotart.css"), encoding="utf-8").read() if os.path.exists(os.path.join(PA, "assets", "plotart.css")) else ""
need(("pa-hire-nav:begin" in _css) == HIRE_ON, "L17 plotart.css %s the six-pill navigation block" % ("lacks" if HIRE_ON else "already carries"))
if HIRE_ON:
    _hp = open(os.path.join(PA, HIRE_PAGE), encoding="utf-8").read() if os.path.exists(os.path.join(PA, HIRE_PAGE)) else ""
    _hv = re.sub(r"\s+", " ", visible_text(_hp))
    need(('<meta name="robots" content="index, follow">' in _hp and 'href="https://plotnua.ie/plotart/art-for-hire/"' in _hp) if BUSINESS_ON else ('<meta name="robots" content="noindex, follow">' in _hp and 'rel="canonical"' not in _hp), "L17 the Art for Hire indexing must match the business information switch")
    need(_hp.count(HIRE_BEGIN.decode()) == 1 and _hp.count(HIRE_END.decode()) == 1, "L17 the Art for Hire page needs exactly one catalogue region")
    need("Original art," in _hv and "on hire." in _hv, "L17 the approved headline is missing")
    for _st in ("PlotArt introduces you to the artist.", "Hire prices are agreed directly with the artist.", "Transport and insurance are arranged between you and the artist.",
                "Photography and screen use are not automatically included.", "Film and television screen use can’t yet be arranged through PlotArt."):
        need(_st in _hv, "L17 the Art for Hire page lacks the statement: " + _st)
    _cards = re.findall(r'<li class="pa-hire-card" data-hire-work="([^"]+)" data-hire-ref="PA-([a-z0-9-]+)-\1"[^>]*>', _hp)
    need(len(_cards) == _hp.count('class="pa-hire-card"'), "L17 a card's reference does not match its work")
    need(len(re.findall(r'<li class="pa-hire-card"[^>]* hidden>', _hp)) == len(_cards), "L17 every card must ship hidden (shown only by the live check)")
    for _wid, _slug in _cards:
        _gp = os.path.join(PA, "artists", _slug, "gallery.json")
        _w = next((w for w in json.load(open(_gp, encoding="utf-8"))["works"] if w["id"] == _wid), None) if os.path.exists(_gp) else None
        need(_w is not None and _w.get("availability") == "available", "L17 card %s is not an available work in %s's published gallery" % (_wid, _slug))
    # Version 3 (founder approval, 11 Nov 2026): outside the catalogue region the page may also show the founder's own
    # painting, and only while the image register permits it on the Art for Hire surface and the file matches its record.
    # Inside the catalogue region only published artist images may appear, exactly as before.
    import hashlib as _hl
    _FOUNDER = "assets/hero/founder-01-abstract.webp"
    _rec = next((r for r in json.load(open(os.path.join(ROOT, "image-provenance-records.json"), encoding="utf-8")).get("records", [])
                 if r.get("asset") == "plotart/" + _FOUNDER), None)
    _fp = os.path.join(PA, _FOUNDER)
    _founder_ok = (_rec is not None and _rec.get("class") == "FOUNDER_ORIGINAL_ARTWORK" and "plotart-art-for-hire" in (_rec.get("permitted_surfaces") or [])
                   and os.path.exists(_fp) and _hl.sha256(open(_fp, "rb").read()).hexdigest() == _rec.get("sha256"))
    _main = _hp.split("<main", 1)[-1].split("</main>")[0]
    _inside = _main[_main.find(HIRE_BEGIN.decode()):_main.find(HIRE_END.decode())] if HIRE_BEGIN.decode() in _main else ""
    for _src in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', _inside):
        need(_src.startswith("../artists/") and _src[3:] in ARTIST_FILES, "L17 the Art for Hire catalogue shows an image that is not a published artist image: %s" % _src)
    for _src in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', _main.replace(_inside, "")):
        need((_src.startswith("../artists/") and _src[3:] in ARTIST_FILES) or (_src == "../" + _FOUNDER and _founder_ok),
             "L17 the Art for Hire page shows an image that is neither a published artist image nor the founder painting registered for Art for Hire: %s" % _src)
    _outside_business = _hp
    if BUSINESS_ON:
        try:
            _outside_business = BUSINESS.outside(_hp)
        except ValueError as e:
            need(False, "L19 " + str(e))
    if BUSINESS_ON:
        try:
            need(BUSINESS.verify_document(SITE, ROOT), "L19 rental PDF verification failed")
        except (ValueError, OSError, KeyError) as e:
            need(False, "L19 " + str(e))
    _outside_business_text = visible_text(_outside_business)
    need("€" not in _outside_business_text and "%" not in _outside_business_text and not re.search(r"<form\b", _hp), "L17 the Art for Hire page shows an unapproved price, percentage or form")
    need(all(m == "hello@plotnua.ie" for m in re.findall(r"mailto:([^?\"]+)", _hp)) and not re.search(r"[A-Za-z0-9._%+-]+@(?!plotnua\.ie)[A-Za-z0-9-]+\.[A-Za-z]", _hv),
         "L17 the Art for Hire page exposes an address other than hello@plotnua.ie")
    need(('data-enquiries="on"' in _hp) == HIRE_FORM and ('data-enquiries="off"' in _hp) != HIRE_FORM, "L17 the enquiry form state does not match art_for_hire_enquiry_form")
    _api = re.search(r'<script src="hire-live\.js" data-api="(https://[a-z0-9.-]+\.workers\.dev)" data-enquiries="(?:on|off)" defer></script>', _hp)
    _cfg = json.load(open(os.path.join(ROOT, "atlas-tools", "release", "plotart-gallery-config.json"), encoding="utf-8")).get("enquiry_endpoint") or ""
    need(_api is not None and _cfg == _api.group(1) + "/v1/enquiry", "L17 the Art for Hire page must use the approved enquiry relay")
    for _ref in re.findall(r'(?:href|src)="([^"]+)"', _hp):
        if _ref.startswith(("https://", "http://", "mailto:", "#")):
            continue
        _p = _ref.split("#")[0].split("?")[0]
        _sr = _p.lstrip("/") if _p.startswith("/") else posixpath.normpath(posixpath.join("plotart/art-for-hire", _p))
        if _p.endswith("/"):
            _sr = posixpath.join(_sr, "index.html")
        need(os.path.exists(os.path.join(ROOT, _sr)) and (not _sr.startswith("plotart/") or _sr[len("plotart/"):] in ALLOWED), "L17 the Art for Hire page has a broken or unpublished link: %s" % _ref)

# L18 · Join PlotArt (Gallery Artist Programme Phase 3, 13 Nov 2026)
GA_STATES = ("not_open", "open", "paused", "closed")
need(GA_STATE in GA_STATES, "L18 gallery_application_state is missing or not one of %s" % ", ".join(GA_STATES))
need(GA_EP == "https://plotnua-art-space-register.colin-a41.workers.dev/v1/art-space-register/gallery-application", "L18 gallery_application_endpoint is not the approved route")
# Artist Submissions (founder brief, 20 Nov 2026): Join PlotArt states the state as a submissions line.
GA_LINE = {"open": "Submissions are open.", "paused": "Submissions are paused at the moment.", "closed": "Submissions have closed."}.get(GA_STATE, "Submissions are not yet open.")
_jp, _cp = os.path.join(PA, "join.html"), os.path.join(PA, "curatorial-policy.html")
_join = open(_jp, encoding="utf-8").read() if os.path.exists(_jp) else ""
_pol = open(_cp, encoding="utf-8").read() if os.path.exists(_cp) else ""
_jv, _pv = re.sub(r"\s+", " ", visible_text(_join)), re.sub(r"\s+", " ", visible_text(_pol))
_jsp = os.path.join(PA, "assets", "pa-apply.js")
_ptr = re.search(r"<!-- pa-artist-apply-pointer:begin -->(.*?)<!-- pa-artist-apply-pointer:end -->", f25, re.S)
_galp = os.path.join(PA, "gallery", "index.html")
_gal = open(_galp, encoding="utf-8").read() if os.path.exists(_galp) else ""
_gband = re.search(r"<!-- pa-artist-apply-gallery:begin -->(.*?)<!-- pa-artist-apply-gallery:end -->", _gal, re.S)
if os.path.realpath(SITE) == os.path.realpath(ROOT):   # on the development tree, the pages must be exactly the builder's output for this state
    import subprocess
    _chk = subprocess.run([sys.executable, os.path.join(ROOT, "atlas-tools", "build-plotart-join.py"), "--check", "--switches", SWITCHES], capture_output=True, text=True)
    need(_chk.returncode == 0, "L18 the Join PlotArt pages are not the build for this state: " + (_chk.stdout + _chk.stderr).strip()[-200:])
if not GA_OPEN:
    # closed: nothing of the recruitment is published or linked
    need(not _join and not _pol and not os.path.exists(_jsp), "L18 %s: join.html, curatorial-policy.html and pa-apply.js must not be published" % GA_STATE)
    need("pa-artist-apply" not in home and _ptr is None and "pa-artist-apply" not in f25, "L18 %s: no homepage artist band and no Founding 25 pointer" % GA_STATE)
    need("pa-artist-apply" not in _gal and "join.html" not in _gal and "plotart-join.css" not in _gal, "L18 %s: no Artists' Gallery invitation" % GA_STATE)
    for _n in PAGES:
        _pp = os.path.join(PA, _n)
        if os.path.exists(_pp):
            _ss = open(_pp, encoding="utf-8").read()
            need('href="join.html' not in _ss and 'curatorial-policy.html' not in _ss, "L18 %s: %s links to an unpublished recruitment page" % (GA_STATE, _n))
else:
    need(bool(_join) and bool(_pol), "L18 open: join.html and curatorial-policy.html must both be published")
    _priv = os.path.join(SITE, "privacy.html") if os.path.exists(os.path.join(SITE, "privacy.html")) else os.path.join(ROOT, "privacy.html")
    need("PLOTNUA-PLOTART-ARTIST-APPLICATIONS-PRIVACY-V15" in open(_priv, encoding="utf-8").read(), "L18 open: the privacy notice section for artist applications (V15) must be live")
    need(_jv.count(GA_LINE) == 2, "L18 join.html must state '%s' in its hero and its Apply section" % GA_LINE)
    for _o in {"Submissions are paused at the moment.", "Submissions have closed.", "Submissions are not yet open.", "Applications are open.", "Applications are paused at the moment.", "Applications have closed.", "Applications are not yet open."} - {GA_LINE}:
        need(_o not in _jv, "L18 join.html shows another state's line: %s" % _o)
    for _t in ("The practical details", "There are no fees to submit, to join or to remain.",
               "PlotArt’s commission is 15% of the price of an original work or signed limited-edition print sold to a collector PlotArt introduced to you, once the sale is complete. It doesn’t apply to your independent sales.",
               "A collector is introduced by PlotArt when they reach you through an enquiry carrying a PlotArt reference, or tell you before the sale is agreed that they found you through PlotArt. Collectors you already knew, or who found you another way, are independent.",
               "only the sale of a particular work you were already discussing in writing within those 24 months carries commission.",
               "on the price of the work including any frame, and excluding delivery, insurance, installation and any VAT you charge.",
               "An introduction counts for 24 months.", "Newly commissioned work is agreed between you and the collector and isn’t subject to the commission.",
               "Collectors pay you directly", "There is no exclusivity", "Submitting a portfolio doesn’t guarantee an invitation.", "invitations to join are extended at the gallery’s discretion",
               "Founding Artists keep their own agreement; artists joining now become Gallery Artists.",
               "The full terms are in the PlotArt Gallery Artist Agreement, which you read and accept in PlotArt Studio before your gallery is first published."):
        need(_t in _jv, "L18 join.html lacks the approved wording: %s" % _t)
    # the 15% appears once, inside "The practical details", in plain type: never a heading, figure or emphasis
    _terms = re.search(r'<section class="pa-jn-sec" id="terms">(.*?)</section>', _join, re.S)
    need(_join.count("15%") == 1 and _terms is not None and "15%" in _terms.group(1), "L18 the 15% must appear once, only in The practical details")
    need(not re.search(r"<(?:h1|h2|h3|strong|b|em|big)\b[^>]*>[^<]*\d+\s?%", _join) and 'class="big"' not in _join and 'class="num"' not in _join,
         "L18 no percentage may be a heading, an emphasis or a large figure")
    for _n, _v in (("join.html", _jv), ("curatorial-policy.html", _pv)):
        need(not re.search(r"(?i)deserves? to be (?:discovered|seen)|overlooked|under-?represented|undiscovered|hidden talent|finally get|get noticed", _v),
             "L18 %s implies artists are overlooked or poorly represented elsewhere" % _n)
    need('href="curatorial-policy.html"' in _join and 'href="join.html"' in _pol, "L18 the two pages must link to each other")
    for _h in ("Artistic quality", "A distinctive voice", "A developed body of work", "Commitment to your practice", "Contribution to the gallery"):
        need(_jv.count(_h) == 1 and _pv.count(_h) == 1, "L18 both pages must carry the five criteria once each: %s" % _h)
    need("never influenced by any fee, payment or commission arrangement" in _pv, "L18 the curatorial policy must say gallery order is never influenced by payment")
    for _n, _v in (("join.html", _jv), ("curatorial-policy.html", _pv), ("index.html", re.sub(r"\s+", " ", visible_text(home)))):
        need(not re.search(r"(?i)discount|waive|waiver|individual terms|variation|selection (?:board|panel|committee)|private invitation|invitation[- ]only|\b\d+ (?:places|artists only)\b|limited (?:places|number)", _v),
             "L18 %s mentions discounts, waivers, individual terms, a selection board, private invitations or a limit" % _n)
    _band = re.search(r"<!-- pa-artist-apply:begin -->(.*?)<!-- pa-artist-apply:end -->", home, re.S)
    need(_band is not None and home.count("<!-- pa-artist-apply:begin -->") == 1 and "f25InviteH" not in home, "L18 open: the homepage carries the artist band once, in place of the closed Founding 25 band")
    if _band:
        _bv = re.sub(r"\s+", " ", visible_text(_band.group(1)))
        need('href="join.html"' in _band.group(1) and 'href="gallery/"' in _band.group(1) and "Artist Submissions" in _bv,
             "L18 the homepage band must be the invitation, linking to Join PlotArt and the gallery")
        need(not re.search(r"\d|%|€|commission|fee|exclusiv|deserves", _bv, re.I), "L18 the homepage band carries figures, commercial terms or promotional wording")
    # the Artists' Gallery application link (founder decisions 16 Nov 2026; moved 21 Nov 2026, artwork first): once, as a
    # discreet link in the closing section, after the collection, linking to Join PlotArt's "A gallery of your own." section;
    # never in the introduction, which is the heading and then the artwork
    _ghero = re.search(r'<section class="pa-vg2-hero">.*?</section>', _gal, re.S)
    _gclose = re.search(r'<section class="pa-vg2-close">.*?</section>', _gal, re.S)
    need(_gband is not None and _gal.count("<!-- pa-artist-apply-gallery:begin -->") == 1 and _ghero is not None and _gclose is not None
         and "pa-artist-apply" not in _ghero.group(0) and "<!-- pa-artist-apply-gallery:begin -->" in _gclose.group(0)
         and _gal.index("<!-- pa-artist-apply-gallery:begin -->") > _gal.index("<!-- pa-vg-collection:end -->"),
         "L18 open: the Artists' Gallery carries the application link once, in its closing section, after the collection (not in the introduction)")
    if _gband:
        _gv = re.sub(r"\s+", " ", visible_text(_gband.group(1)))
        need('href="../join.html#your-gallery"' in _gband.group(1) and _gv.strip() == "Artist submissions →", "L18 the Artists' Gallery link must read 'Artist submissions →' and link to Join PlotArt's gallery section")
        need(not re.search(r"\d|%|€|commission|fee|exclusiv|deserves", _gv, re.I), "L18 the Artists' Gallery button carries figures, commercial terms or promotional wording")
    need(re.search(r'<section class="pa-jn-sec" id="your-gallery">\s*<div class="pa-wrap pa-jn-grid">\s*<p class="pa-jn-k">The gallery</p>\s*<div><h2>A gallery of your own\.</h2>', _join) is not None, "L18 Join PlotArt must carry the your-gallery anchor on 'A gallery of your own.'")
    need(_ptr is not None and bool(_ptr.group(1).strip()), "L18 open: the Founding 25 page points to Join PlotArt")
    need("<form" not in _pol and "pa-apply.js" not in _pol, "L18 the curatorial policy has no form")
    need(_join.count("<form") == 1 and ('data-ap-form data-endpoint="%s" data-image-endpoint="%s/image"' % (GA_EP, GA_EP)) in _join, "L18 open: exactly one form posting only to the approved route")
    need('<script src="assets/pa-apply.js" defer></script>' in _join and os.path.exists(_jsp), "L18 open: the application script must ship with the page")
    _wsrc = open(os.path.join(ROOT, "worker", "art-space-register", "src", "index.js"), encoding="utf-8").read()
    for _const, _key in (("F25_ELIGIBILITY_TEXT", "eligibility"), ("F25_OWNERSHIP_TEXT", "ownership"), ("GA_PRIVACY_TEXT", "privacy")):
        _m = re.search(r'const %s =\s*"([^"]+)";' % _const, _wsrc)
        _p = re.search(r'data-ap-sentence="%s">([^<]*)<' % _key, _join)
        need(_m is not None and _p is not None and html.unescape(_p.group(1)) == _m.group(1), "L18 the %s confirmation differs from the Worker's %s" % (_key, _const))
    need('href="../privacy.html#plotart-artist-applications"' in _join, "L18 the form must link the privacy notice's artist applications section")
    need(not re.search(r'name="(?:living_gallery|location_public|address|eircode|phone|dob|date_of_birth|terms)"', _join), "L18 the application asks for something outside the approved form")
    need("nothing is published without your approval" in _jv, "L18 the confirmation must say nothing is published without the artist's approval")
    _js = open(_jsp, encoding="utf-8").read() if os.path.exists(_jsp) else ""
    need("localStorage" not in _js and "sessionStorage" not in _js and "document.cookie" not in _js and "console." not in _js and "credentials: 'omit'" in _js,
         "L18 the application script must store, log and send no credentials")

# L16 · Mobile Gallery (founder release authorisation, 3 Nov 2026): the concept is public, no gallery has joined.
_mgd = os.path.join(PA, "mobile-gallery", "mobile-gallery-data.js")
if os.path.exists(_mgd):
    _d = open(_mgd, encoding="utf-8").read()
    _prov = _d.split("window.MG_PROVIDERS", 1)[-1]
    need("status: 'participating'" not in _d and "evidence: null }" in _d, "L16 a Mobile Gallery provider is marked as participating")
    need(not re.search(r"\bnote:|contact:|commercial: '|€|per appointment|referral fee", _prov), "L16 the published provider data carries internal notes, contacts, terms or prices")
    need(not re.search(r"(?i)\b(?:our|official|approved|founding) partner|participating gallery'(?!\s*:)", _prov), "L16 the provider data claims a partnership")
    _js = open(os.path.join(PA, "mobile-gallery", "mobile-gallery.js"), encoding="utf-8").read()
    need("'Prospective Gallery — Participation Unconfirmed'" in _js and "Illustrative gallery profile." in _js and "Participation has not been confirmed." in _js,
         "L16 the Mobile Gallery cards or profile lose the unconfirmed-participation wording")
    need(not re.search(r"<form|fetch\(|sendBeacon|XMLHttpRequest|workers\.dev|airtable", _js + _d), "L16 Mobile Gallery collects or sends homeowner information")
    _mgi = open(os.path.join(PA, "mobile-gallery", "index.html"), encoding="utf-8").read()
    need("Developing Our Gallery Network" in _mgi and "appointments can’t yet be arranged through PlotArt" in _mgi, "L16 the Mobile Gallery page must say the network is developing and appointments can't yet be arranged")
    need("application/ld+json" not in _mgi + open(os.path.join(PA, "mobile-gallery", "gallery.html"), encoding="utf-8").read(), "L16 Mobile Gallery carries structured data")

# L19 · artist opportunity lists (16 Nov 2026): every list is exactly what the published galleries produce; only published
# artists appear; each artist page's "Open to" line matches its package; no private Opportunities answer appears anywhere.
_pk = SEO.public_packages(os.path.dirname(PA))
for _rel in OPP.PAGES:
    _fp = os.path.join(PA, _rel)
    if not os.path.exists(_fp):
        need(_rel != OPP.HUB, "L19 the artist opportunities page plotart/%s is missing" % _rel)
        continue
    _doc = open(_fp, encoding="utf-8").read()
    try:
        need(_doc == OPP.update(_doc, _rel, _pk, FEAT.choices(os.path.dirname(PA))), "L19 %s: the opportunity list differs from the published galleries" % _rel)
    except ValueError as _e:
        need(False, "L19 %s: %s" % (_rel, _e))
    need(not re.search(r"(?i)\b(?:participating artists?|confirmed (?:artists?|placements?)|now booking|book now|available now)\b", visible_text(OPP.REGION.search(_doc).group(0) if OPP.REGION.search(_doc) else "")),
         "L19 %s: the list presents interest as participation or a booking" % _rel)
_slugs = {p["artist"]["slug"] for p in _pk}
for _p in _pk:
    _a = _p["artist"]
    need(set(_a) <= {"slug", "display_name", "founding", "practice", "medium", "statement", "bio", "website", "instagram", "county", "portrait", "open_for_commissions", "open_to"}, "L19 %s: a published package carries an unexpected artist field" % _a["slug"])
    _ip = os.path.join(PA, "artists", _a["slug"], "index.html")
    if os.path.exists(_ip):
        _line = OPP.artist_line(_p)
        _h = open(_ip, encoding="utf-8").read()
        need((_line in _h) if _line else ("pa-ag-open" not in _h), "L19 artists/%s: the 'Open to' line does not match the published package" % _a["slug"])
for _rel in OPP.PAGES:
    _fp = os.path.join(PA, _rel)
    if os.path.exists(_fp) and OPP.REGION.search(open(_fp, encoding="utf-8").read()):
        for _s in re.findall(r'href="(?:\.\./)*artists/([a-z0-9-]+)/"', OPP.REGION.search(open(_fp, encoding="utf-8").read()).group(0)):
            need(_s in _slugs, "L19 %s lists an artist whose gallery is not published: %s" % (_rel, _s))

# L20 · the Contemporary gallery (one curated gallery, founder approval 26 Nov 2026): both generated regions are exactly
# what the page's own arrangement renders from the published galleries (the opening row: at most three, each the
# founder's work while eligible, never a substitute; then every other artist once, with their chosen or first eligible
# work); every image is a published derivative in that artist's gallery; every link goes to a published gallery or
# artwork page; and nothing outside the regions changes (pinned by the manifest).
_gp = os.path.join(PA, FEAT.PAGE)
if os.path.exists(_gp):
    _doc = open(_gp, encoding="utf-8").read()
    try:
        need(FEAT.consistent(_doc, _pk), "L20 gallery/index.html: the gallery differs from what its arrangement renders from the published galleries")
        _reg = FEAT.region(_doc)
        need(_doc.index(FEAT.FEAT_END) < _doc.index(VG_BEGIN.decode()), "L20 gallery/index.html: the opening row must sit above Explore the Gallery")
        need(len(re.findall(r'class="pa-op-item"', _reg)) <= FEAT.OPEN_MAX and "pa-fa-list" not in _reg and "Artists in Focus" not in _reg,
             "L20 gallery/index.html: the opening row holds more than three artists, or Artists in Focus returned")
        _both = _reg + _doc[_doc.index(VG_BEGIN.decode()):_doc.index(VG_END.decode())]
        for _s, _f in re.findall(r'src="\.\./artists/([a-z0-9-]+)/img/([a-z0-9-]+\.webp)"', _both):
            need(os.path.exists(os.path.join(PA, "artists", _s, "img", _f)), "L20 gallery/index.html: an image is not a published file: %s/%s" % (_s, _f))
        for _h in re.findall(r'href="\.\./(artists/[^"]+)"', _both):
            need(os.path.exists(os.path.join(PA, _h + ("index.html" if _h.endswith("/") else ""))), "L20 gallery/index.html: a link goes nowhere: " + _h)
        _out = re.findall(r'href="(?!\.\./artists/)[^"]*"', _reg)
        need(_out == [], "L20 gallery/index.html: the opening row links outside the artists' galleries")
    except ValueError as _e:
        need(False, "L20 gallery/index.html: %s" % _e)

# L22 · the homepage availability line (Commercial Conversion Sprint 1, founder approval 26 Nov 2026). Recomputed here
# INDEPENDENTLY of plotart_search_content: straight from every published gallery.json, without its helpers. Exactly one
# generated region, directly under the one heading; the three figures must match; the wording may not claim more than
# the data holds ("Irish", "for sale online", "buy online"); the link goes to the available-artworks page only; and with
# nothing available there is no line at all.
if os.path.exists(os.path.join(PA, "index.html")):
    _h = home
    _b, _e = "<!-- pa-guide-collection:begin -->", "<!-- pa-guide-collection:end -->"
    need(_h.count(_b) == 1 and _h.count(_e) == 1, "L22 index.html must carry exactly one availability region")
    if _h.count(_b) == 1 and _h.count(_e) == 1:
        need(re.search(r'<h1 class="pa-gx-h1" id="homeH">A new home for Irish art\.</h1>\s*' + re.escape(_b), _h) is not None,
             "L22 the availability line must sit directly under the homepage heading")
        _reg = _h[_h.index(_b) + len(_b):_h.index(_e)]
        _works, _artists, _prices = 0, set(), []
        _adir = os.path.join(PA, "artists")
        for _gj in sorted(os.path.join(_adir, _d, "gallery.json") for _d in (os.listdir(_adir) if os.path.isdir(_adir) else []) if os.path.exists(os.path.join(_adir, _d, "gallery.json"))):
            _g = json.load(open(_gj, encoding="utf-8"))
            for _w in _g.get("works", []):
                if _w.get("availability") == "available":
                    _works += 1
                    _artists.add(_g["artist"]["slug"])
                    if _w.get("price_eur") and not _w.get("price_on_request"):
                        _prices.append(_w["price_eur"])
        _vt = re.sub(r"\s+", " ", visible_text(_reg)).strip()
        need(not re.search(r"(?i)\birish\b|for sale online|buy online|add to basket", _vt), "L22 the availability line claims more than the published data shows: " + _vt)
        if _works == 0:
            need(_vt == "", "L22 nothing is available, so the homepage must show no availability line")
        else:
            _want = "%d original %s by %d %s" % (_works, "work" if _works == 1 else "works", len(_artists), "artist" if len(_artists) == 1 else "artists")
            if _prices:
                _low = min(_prices)
                _want += ", from €" + "{:,}".format(_low)
            need(_vt.startswith(_want + " · Browse available artworks"), "L22 the availability line must read '%s · Browse available artworks →', found '%s'" % (_want, _vt))
            _links = re.findall(r'<a\b[^>]*href="([^"]+)"', _reg)
            need(_links == ["artworks/"] and os.path.exists(os.path.join(PA, "artworks", "index.html")),
                 "L22 the availability line must link to the available-artworks page only, found %s" % _links)

if problems:
    print("PLOTART LAUNCH · FAILED (%d)" % len(problems))
    for x in problems:
        print("  " + x)
    sys.exit(1)
print("PLOTART LAUNCH · OK — L1-L22 on %d pages · applications %s · artist applications %s · Art for Hire %s (%d demonstration names checked absent)" % (len(PAGES), STATE, GA_STATE, ("ON" + (", enquiry form on" if HIRE_FORM else "")) if HIRE_ON else "off", len(demo_names)))
