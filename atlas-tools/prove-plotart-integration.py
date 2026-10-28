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
  N2  outside the PlotNua header, the ONLY PlotNua page that links into PlotArt is
      discovery-a-home-for-art.html, with exactly one link to plotart/ (the
      "Explore PlotArt" button) and one to plotart/founding-25.html. No PlotNua page
      links to any other PlotArt path.
  N3  the A Home for Art wording beside those links says PlotArt is in development
      and that applications are not yet open, and never invites anyone to apply.
  N4  every PlotArt link target exists in the repository (the three launch pages).
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

ORDER = ["Discovery Library", "PlotArt", "My Plot"]
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
need(sorted(hfa) == ["plotart/", "plotart/founding-25.html"], "N2 A Home for Art PlotArt links are %s" % hfa)

# N3
t = open(os.path.join(ROOT, "discovery-a-home-for-art.html"), encoding="utf-8").read()
sec = re.search(r'<section class="pd-section reveal hfa-future".*?</section>', t, re.S)
need(sec is not None, "N3 the A Home for Art PlotArt section is missing")
if sec:
    v = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", sec.group(0))))
    need("PlotArt is in development." in v, "N3 the section no longer says PlotArt is in development")
    need("applications are not yet open" in v, "N3 the section must say applications are not yet open")
    need('>Explore PlotArt</a>' in sec.group(0), "N3 the 'Explore PlotArt' button is missing")
    need(not re.search(r"\bapply\b(?! to)|applications are open|now open|open soon|join the Founding 25", v, re.I),
         "N3 the section invites applications or implies they are open")

# N4
for target in ["plotart/index.html", "plotart/founding-25.html", "plotart/living-gallery.html"]:
    need(os.path.exists(os.path.join(ROOT, target)), "N4 %s is missing" % target)

if problems:
    print("PLOTART INTEGRATION · FAILED (%d)" % len(problems))
    for x in problems[:40]:
        print("  " + x)
    sys.exit(1)
print("PLOTART INTEGRATION · OK — N1-N4 · %d header pages carry Discovery Library > PlotArt > My Plot; A Home for Art links exactly plotart/ and plotart/founding-25.html" % len(pn_header.HEADER_PAGES))
