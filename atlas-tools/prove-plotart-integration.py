#!/usr/bin/env python3
"""GUARD · PlotArt integration into PlotNua (proposed 27 Oct 2026). Read-only.

    python3 atlas-tools/prove-plotart-integration.py

Prints "PLOTART INTEGRATION · OK" only when:

  N1  every page that carries the PlotNua header (pn_header.HEADER_PAGES) has, in
      BOTH the desktop navigation and the phone row, exactly three destinations in
      this order: Discovery Library, PlotArt, My Plot (renamed from Your Plot, founder
      approval 28 Oct 2026). PlotArt points to plotart/ (/plotart/ on the
      root-absolute 404 page) and never carries aria-current; My Plot points to
      your-plot.html?myplot=1.
  N2  outside the PlotNua header, A Home for Art links exactly the public PlotArt
      introduction, gallery, two buyer guides, calculator, Founding 25 and Living Gallery.
  N3  live artist galleries and applications are distinguished from proposed home matching.
  N4  every declared PlotArt link target exists.
"""
import os, re, sys, glob, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import pn_header  # noqa: E402

problems = []
def need(ok, msg):
    if not ok:
        problems.append(msg)

ORDER = ["Discovery Library", "PlotArt", "GridNua", "My Plot"]   # GridNua added 29 Oct 2026 (founder authorisation)
BAR = re.compile(r"<!-- PLOTNUA HEADER v2 · BAR · BEGIN.*?BAR · END -->", re.S)
ROW = re.compile(r"<!-- PLOTNUA HEADER v2 · ROW · BEGIN.*?ROW · END -->", re.S)

def dests(block):
    return re.findall(r'<a class="pn-hdr-btn [^"]*" href="([^"]+)"([^>]*)>(?:(?!</a>).)*?<span>([^<]+)</span>', block, re.S)

# N1
for page in pn_header.HEADER_PAGES:
    p = os.path.join(ROOT, page)
    t = open(p, encoding="utf-8").read()
    want_art = "/plotart/" if page in pn_header.ROOTABS else "plotart/"
    for name, rx in (("desktop navigation", BAR), ("phone row", ROW)):
        m = rx.findall(t)
        need(len(m) == 1, "N1 %s: %s block not present exactly once" % (page, name))
        if len(m) != 1:
            continue
        d = dests(m[0])
        need([x[2] for x in d] == ORDER, "N1 %s: %s order is %s" % (page, name, [x[2] for x in d]))
        art = [x for x in d if x[2] == "PlotArt"]
        need(len(art) == 1 and art[0][0] == want_art and "aria-current" not in art[0][1],
             "N1 %s: %s PlotArt link is not %s" % (page, name, want_art))
        want_gn = "/gridnua/" if page in pn_header.ROOTABS else "gridnua/"
        gn = [x for x in d if x[2] == "GridNua"]
        need(len(gn) == 1 and gn[0][0] == want_gn and "aria-current" not in gn[0][1],
             "N1 %s: %s GridNua link is not %s" % (page, name, want_gn))
        want_mp = ("/" if page in pn_header.ROOTABS else "") + "your-plot.html?myplot=1"
        mp = [x for x in d if x[2] == "My Plot"]
        need(len(mp) == 1 and mp[0][0] == want_mp, "N1 %s: %s My Plot link is not %s" % (page, name, want_mp))

# N2
outside = {}
for p in glob.glob(os.path.join(ROOT, "*.html")):
    t = BAR.sub("", ROW.sub("", open(p, encoding="utf-8", errors="ignore").read()))
    refs = re.findall(r'(?:href|src)="(/?plotart/[^"]*)"', t)
    if refs:
        outside[os.path.basename(p)] = refs
need(set(outside) <= {"discovery-a-home-for-art.html"}, "N2 pages outside the header linking into PlotArt: %s" % sorted(set(outside) - {"discovery-a-home-for-art.html"}))
hfa = outside.get("discovery-a-home-for-art.html", [])
PUBLIC_TARGETS = ["plotart/", "plotart/founding-25.html", "plotart/living-gallery.html", "plotart/gallery/", "plotart/buy-original-art-ireland.html", "plotart/abstract-contemporary-art-ireland.html", "plotart/art-size-calculator.html"]
need(sorted(hfa) == sorted(PUBLIC_TARGETS), "N2 A Home for Art PlotArt links are %s" % hfa)

# N3
t = open(os.path.join(ROOT, "discovery-a-home-for-art.html"), encoding="utf-8").read()
sec = re.search(r'<section class="pd-section reveal hfa-future".*?</section>', t, re.S)
need(sec is not None, "N3 the A Home for Art PlotArt section is missing")
if sec:
    v = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", sec.group(0))))
    need("Artists’ Gallery of original Irish art" in v and "is now online." in v, "N3 the live gallery status is missing")
    need("Applications have closed." in v and "accepting applications" not in v, "N3 the Founding 25 status must say applications have closed (Gallery Artist Programme Phase 1, 13 Nov 2026)")
    need("This matching service is not live yet." in v, "N3 home matching must remain described as unavailable")
    need("It isn’t running yet." in v, "N3 Living Gallery must remain described as unavailable")
    need("Any sale is arranged directly with the artist." in v, "N3 artist-direct sale explanation missing")
    need('>Explore PlotArt</a>' in sec.group(0), "N3 the Explore PlotArt button is missing")
    need(not re.search(r"Artist galleries are not open|applications are not yet open|a forthcoming programme", v, re.I), "N3 obsolete launch status returned")

# N4
for ref in PUBLIC_TARGETS:
    target = ref + "index.html" if ref.endswith("/") else ref
    need(os.path.exists(os.path.join(ROOT, target)), "N4 %s is missing" % target)

if problems:
    print("PLOTART INTEGRATION · FAILED (%d)" % len(problems))
    for x in problems[:40]:
        print("  " + x)
    sys.exit(1)
print("PLOTART INTEGRATION · OK — N1-N4 · %d header pages carry Discovery Library > PlotArt > GridNua > My Plot; A Home for Art links the seven declared PlotArt destinations; public galleries and proposed home hosting remain distinct" % len(pn_header.HEADER_PAGES))
