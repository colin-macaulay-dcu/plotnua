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
  L6  every page carries the in-development ribbon (or the approved launch notice)
      and says plainly that PlotArt isn't open and nothing is for sale.
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
      launch page's navigation is Virtual Gallery, Living Gallery, About, Founding 25.
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
ALLOWED = set(PAGES) | {"assets/plotart.css", "assets/plotart.js"} | ({"assets/f25-apply.js"} if launch.get("f25_application_state") == "open" else set())

# L1
found = set()
for d, _, fs in os.walk(PA):
    for f in fs:
        found.add(os.path.relpath(os.path.join(d, f), PA).replace(os.sep, "/"))
need(found == ALLOWED, "L1 plotart/ must hold exactly the launch files; extra %s, missing %s" % (sorted(found - ALLOWED), sorted(ALLOWED - found)))

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
    need('class="pa-proto"' in s, "L6 %s has no ribbon" % name)
    need("Prototype" not in re.search(r'<div class="pa-proto"[^>]*>(.*?)</div>', s, re.S).group(1), "L6 %s still carries the prototype ribbon" % name)
    # L7
    need(not re.search(r"<form[^>]*\saction=", s), "L7 %s has a form action" % name)
    need(not re.search(r'type="file"|name="(?:address|eircode|phone|dob|date_of_birth)"', s), "L7 %s asks for an upload, address, phone or date of birth" % name)
    ep_ok = s.replace('data-endpoint="%s"' % ENDPOINT, "") if ENDPOINT else s
    need(not re.search(r"workers\.dev|airtable", ep_ok), "L7 %s references a live endpoint outside the approved form" % name)

home = open(os.path.join(PA, "index.html"), encoding="utf-8").read() if os.path.exists(os.path.join(PA, "index.html")) else ""
need("isn't open yet" in visible_text(home) and "No artwork is currently available through PlotArt." in visible_text(home), "L6 the homepage must say PlotArt isn't open and no artwork is currently available through PlotArt")
need("This is the experience PlotArt is building" in visible_text(home), "L6 the buyer experience must be framed as what PlotArt is building")
need(len(demo_names) > 0 or not os.path.exists(cat_path), "L3 demonstration names could not be read")

# L3 on a release branch: the prototype data is never published, so demonstration names
# cannot be read there. --manifest FILE pins every published PlotArt file to the SHA-256
# of the build that passed L1-L10 WITH the names (on the development branch).
if "--manifest" in sys.argv:
    import hashlib
    man = json.load(open(sys.argv[sys.argv.index("--manifest") + 1], encoding="utf-8"))
    need(set(man["files"]) == found, "L3 manifest lists %s, plotart/ holds %s" % (sorted(man["files"]), sorted(found)))
    for rel, sha in man["files"].items():
        fp = os.path.join(PA, rel)
        got = hashlib.sha256(open(fp, "rb").read()).hexdigest() if os.path.exists(fp) else None
        need(got == sha, "L3 %s differs from the verified build (manifest)" % rel)
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
need(("<strong>The Founding 25.</strong> %s" % LINE) in home, "L8 the homepage Founding 25 status line is not the %s wording" % STATE)
for other in {"Applications are open.", "Applications are paused at the moment.", "Applications have closed.", "Applications are not yet open."} - {LINE}:
    need(("<strong>The Founding 25.</strong> %s" % other) not in home, "L8 the homepage shows another state's line: %s" % other)
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
    need("No artwork is currently available through PlotArt." in vt, "L10 %s must say 'No artwork is currently available through PlotArt.'" % name)
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
need(GALLERIES_LINE in re.sub(r"\s+", " ", visible_text(home)), "L10 the homepage 'Artist galleries' line is not the approved wording")
lg = open(os.path.join(PA, "living-gallery.html"), encoding="utf-8").read() if os.path.exists(os.path.join(PA, "living-gallery.html")) else ""
need("proposed programme" in visible_text(lg) and "isn't running yet" in visible_text(lg), "L10 the Living Gallery must be presented as a proposed programme that isn't running yet")

# L11 · the Virtual Gallery, published empty (founder decision 28 Oct 2026)
VG_EMPTY = "No artists have been selected, and no galleries are published yet."
VG_SLOT = "Founding Artist gallery Gallery %02d Awaiting its artist"
vgp = os.path.join(PA, "gallery", "index.html")
vg = open(vgp, encoding="utf-8").read() if os.path.exists(vgp) else ""
need(bool(vg), "L11 the Virtual Gallery page plotart/gallery/index.html is missing")
if vg:
    vgv = re.sub(r"\s+", " ", visible_text(vg))
    need(VG_EMPTY in vgv, "L11 the Virtual Gallery must say exactly: %s" % VG_EMPTY)
    need(LINE in vgv, "L11 the Virtual Gallery's Founding 25 note is not the %s wording (%s)" % (STATE, LINE))
    grid = re.search(r'<ol class="pa-vg-grid"[^>]*>(.*?)</ol>', vg, re.S)
    need(grid is not None, "L11 the Virtual Gallery grid is missing")
    if grid:
        cards = re.findall(r'<li class="pa-vg-card">(.*?)</li>', grid.group(1), re.S)
        need(len(cards) == 25, "L11 the Virtual Gallery must show exactly 25 placeholders (found %d)" % len(cards))
        for i, c in enumerate(cards, 1):
            got = re.sub(r"\s+", " ", visible_text(c)).strip()
            need(got == ("%02d " % i) + VG_SLOT % i, "L11 placeholder %d carries other content: %r" % (i, got[:80]))
        rest = re.sub(r'<li class="pa-vg-card">.*?</li>', "", grid.group(1), flags=re.S)
        need(len(re.findall(r"<li\b", rest)) == 1 and 'href="../founding-25.html"' in rest, "L11 the grid may hold only the 25 placeholders and the Founding 25 link")
    need(not re.search(r"<img\b|<picture\b|<svg\b|background-image|url\(", vg.split("<main", 1)[-1].split("</main>")[0]), "L11 the Virtual Gallery shows an image (no portrait or artwork may appear)")
    need('href="../founding-25.html"' in vg, "L11 the Virtual Gallery must link to the Founding 25 page")
    need(not re.search(r"testimonial|“|”|\bsaid\b", visible_text(vg.split("<main", 1)[-1].split("</main>")[0]), re.I), "L11 the Virtual Gallery carries a quotation or testimonial")
    need("<title>Virtual Gallery | PlotArt</title>" in vg, "L11 the Virtual Gallery title is not the approved one")
smp = os.path.join(SITE, "sitemap.xml")
if os.path.exists(smp):
    need("plotart" not in open(smp, encoding="utf-8").read(), "L11 sitemap.xml lists a PlotArt URL")
NAV_WANT = ["Virtual Gallery", "Living Gallery", "About", "Founding 25"]
for name in PAGES:
    p = os.path.join(PA, name)
    if os.path.exists(p):
        nav = re.search(r'<nav class="pa-nav" aria-label="PlotArt">(.*?)</nav>', open(p, encoding="utf-8").read(), re.S)
        labels = [html.unescape(x) for x in re.findall(r'<a [^>]*>([^<]+)</a>', nav.group(1))] if nav else []
        need(labels[:4] == NAV_WANT, "L11 %s navigation is %s, not %s" % (name, labels[:4], NAV_WANT))

if problems:
    print("PLOTART LAUNCH · FAILED (%d)" % len(problems))
    for x in problems:
        print("  " + x)
    sys.exit(1)
print("PLOTART LAUNCH · OK — L1-L11 on %d pages · applications %s (%d demonstration names checked absent)" % (len(PAGES), STATE, len(demo_names)))
