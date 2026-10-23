#!/usr/bin/env python3
"""PLOTNUA GLOBAL HEADER v2 · the guard (founder approval 23 Oct 2026).

One header for the whole site: every approved page must carry exactly the markup
atlas-tools/pn_header.py renders for it, and nothing else.

  G1  COVERAGE: every page in pn_header.HEADER_PAGES carries the header; every page
      in the sitemap is one of them; the excluded families (Your Plot, the
      property checks and journeys disc0NN-*) and every other page do not
  G2  IDENTITY: each BAR and ROW block is byte-identical to pn_header's rendering
      for that page (only the active page, the (i) on the homepage, the Search seat
      where a page has the rail, and the banner element differ, all by rule)
  G3  ORDER: BAR precedes the search rail and ROW follows it (keyboard order is
      the visual order at every width); exactly one BAR, one ROW
  G4  RETIRED: no page carries the v1 identity header or the homepage's
      hand-built header; the body carries pn-hdr-on; the stylesheet is linked once
  G5  WHATSAPP: one link per header, exactly the approved destination, new tab,
      noopener noreferrer, labelled, no prefilled text; the homepage footer
      contact is unchanged (the homepage has exactly two wa.me links)
  G6  DESTINATIONS: Discovery Library and Your Plot exist; About and Contact are
      not in the primary navigation (they stay in every footer)
  G7  HOMEPAGE: the (i) button exists once, inside the header, controlling the
      existing "What is PlotNua?" panel
  G8  SCOPE: every rule in assets/identity/pn-header.css is under body.pn-hdr-on;
      it hides the old floating tile; it never sets a --p4 token
  G9  ONE RENDERER: the identity builder and the global builder both import
      pn_header and neither carries header markup of its own

Usage: python3 atlas-tools/prove-global-header.py [--dir D]
Mutation proof: atlas-tools/prove-global-header-capability.py
"""
import re, sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = Path(sys.argv[sys.argv.index("--dir") + 1]).resolve() if "--dir" in sys.argv else TOOLS.parent
sys.path.insert(0, str(TOOLS))
import pn_header as H  # noqa: E402

fails = []
def bad(m): fails.append(m)

def block(t, k):
    return re.findall(r"<!-- PLOTNUA HEADER v2 · %s · BEGIN.*?<!-- PLOTNUA HEADER v2 · %s · END -->\n?" % (k, k), t, re.S)

def main():
    pages = sorted(p.name for p in ROOT.glob("*.html"))
    # G1 coverage
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    locs = [l or "index.html" for l in re.findall(r"<loc>https://plotnua\.ie/([^<]*)</loc>", sitemap)]
    for l in locs:
        if l not in H.HEADER_PAGES: bad("G1 sitemap page %s has no place in the global header's page list" % l)
    for name in pages:
        t = (ROOT / name).read_text(encoding="utf-8", errors="replace")
        carries = "PLOTNUA HEADER v2" in t
        if name in H.HEADER_PAGES and not carries: bad("G1 %s must carry the global header" % name)
        if name not in H.HEADER_PAGES and carries: bad("G1 %s carries the global header but is not an approved page" % name)
    for name in H.EXCLUDED:
        if (ROOT / name).exists() and "PLOTNUA HEADER v2" in (ROOT / name).read_text(encoding="utf-8"):
            bad("G1 %s is excluded and must keep its own interface" % name)

    css_link = H.href  # noqa
    for name in H.HEADER_PAGES:
        p = ROOT / name
        if not p.exists(): bad("G1 %s is listed but missing" % name); continue
        t = p.read_text(encoding="utf-8")
        bars, rows = block(t, "BAR"), block(t, "ROW")
        if len(bars) != 1 or len(rows) != 1: bad("G3 %s: expected one BAR and one ROW (%d, %d)" % (name, len(bars), len(rows))); continue
        has_search = H.RAIL_BEGIN in t
        body = t[t.index("<body"):]
        banner = not H.has_own_banner(body)
        want_bar, want_row = H.bar(name, has_search, banner), H.row(name)
        if bars[0].rstrip("\n") != want_bar.rstrip("\n"): bad("G2 %s: the header bar differs from pn_header.py's rendering" % name)
        if rows[0].rstrip("\n") != want_row.rstrip("\n"): bad("G2 %s: the header row differs from pn_header.py's rendering" % name)
        # G3 order around the rail
        if has_search:
            ib, ir0, ir1, iw = t.index(H.MARK["BAR"][0]), t.index(H.RAIL_BEGIN), t.index(H.RAIL_END), t.index(H.MARK["ROW"][0])
            if not (ib < ir0 < ir1 < iw): bad("G3 %s: header bar must precede the search rail and the row follow it" % name)
        # G4 retired headers, body class, stylesheet
        if "PLOTNUA IDENTITY v1 · HEADER" in t or 'class="pn-id-header' in t: bad("G4 %s still carries the v1 identity header" % name)
        if 'class="p4-header"' in t: bad("G4 %s still carries the homepage's hand-built header" % name)
        m = re.search(r'<body class="([^"]*)">', t)
        if not m or "pn-hdr-on" not in m.group(1).split(): bad("G4 %s: body does not carry pn-hdr-on" % name)
        if t.count('href="%s"' % H.href(name, H.CSS)) != 1: bad("G4 %s: pn-header.css must be linked exactly once" % name)
        # G5 WhatsApp
        was = re.findall(r'<a class="pn-hdr-wa" href="([^"]+)" target="([^"]+)" rel="([^"]+)" aria-label="([^"]+)">', bars[0])
        if len(was) != 1 or was[0] != (H.WHATSAPP, "_blank", "noopener noreferrer", H.WHATSAPP_LABEL):
            bad("G5 %s: the header WhatsApp control is not exactly the approved one" % name)
        if re.search(r"wa\.me/[^\"]*\?text=", t): bad("G5 %s: a prefilled WhatsApp message appeared" % name)
        # G6 destinations
        for h in (H.LIBRARY[0], H.PLOT[0]):
            if not (ROOT / h).exists(): bad("G6 destination %s missing" % h)
        nav = "".join(bars + rows)
        for h in ("about.html", "contact.html"):
            if 'href="%s"' % H.href(name, h) in nav: bad("G6 %s: %s is back in the primary navigation" % (name, h))
    # G5 / G7 homepage
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    if home.count("https://wa.me/353834036695") != 2: bad("G5 index.html: expected exactly the header and footer WhatsApp links")
    if 'class="pn-whatsapp" href="https://wa.me/353834036695"' not in home: bad("G5 index.html: the footer WhatsApp contact changed")
    hb = block(home, "BAR")
    if home.count('id="brandInfoBtn"') != 1 or not hb or 'id="brandInfoBtn"' not in hb[0] or 'aria-controls="brandInfo"' not in hb[0] \
            or home.count('id="brandInfo"') != 1:
        bad("G7 index.html: the (i) button must exist once, in the header, controlling the What is PlotNua? panel")
    # G8 stylesheet scope
    css = (ROOT / H.CSS).read_text(encoding="utf-8")
    flat = re.sub(r"@media[^{]*\{", "", re.sub(r"/\*.*?\*/", "", css, flags=re.S))
    for sel in re.findall(r"([^{}]+)\{[^{}]*\}", flat):
        for s in [x.strip() for x in re.split(r",(?![^(]*\))", sel)]:
            if s and not re.match(r"^(html(?:\.[\w-]+|:not\([^)]*\))*\s+)?body\.pn-hdr-on\b", s):
                bad("G8 selector outside body.pn-hdr-on: %r" % s)
    if not re.search(r"body\.pn-hdr-on \.brand-mark\{ display:none", css): bad("G8 the old floating tile is not hidden")
    if re.search(r"--p4-[a-z0-9-]+\s*:", flat): bad("G8 pn-header.css must not set --p4 tokens")
    # G9 one renderer
    for b in ("build-identity-stage1.py", "build-global-header.py"):
        src = (TOOLS / b).read_text(encoding="utf-8")
        if "import pn_header" not in src: bad("G9 %s does not use pn_header.py" % b)
        if re.search(r'class=\\?"pn-hdr', src): bad("G9 %s writes header markup of its own" % b)
    if fails:
        for f in fails: print("FAIL " + f)
        print("GLOBAL HEADER · REFUSED — %d problem(s)" % len(fails)); return 2
    print("GLOBAL HEADER · OK — %d pages carry the one header (%d identity, %d global), byte-identical to pn_header.py; "
          "rail order, retired headers, WhatsApp, destinations, homepage (i), stylesheet scope and one renderer verified; "
          "%d sitemap pages covered; Your Plot and the property checks excluded"
          % (len(H.HEADER_PAGES), len(H.IDENTITY_PAGES), len(H.GLOBAL_PAGES), len(locs)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
