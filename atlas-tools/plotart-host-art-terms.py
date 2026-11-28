#!/usr/bin/env python3
"""PlotArt · Host Art terms across the published pages (founder brief 28 Nov 2026).

The Living Gallery stays the brand; "Host Art" is the navigation and participation language. On every PlotArt page:
  the header pill and its phone Menu link          Living Gallery      -> Host Art            (same address and tracking id)
  the footer link                                  Living Gallery      -> The Living Gallery  (the brand, for search)
  an artist's "Open to" pills                      Living Gallery      -> Art Hosting
                                                   Hotels and workplaces -> Business and venue hosting
Addresses, anchors and tracking ids never change, so no redirect is needed and search equity is kept.
  python3 atlas-tools/plotart-host-art-terms.py [ROOT] [--check]
--check changes nothing and fails if any page still carries an old label (the shell writes the new ones for new pages)."""
import os, re, sys
ROOT = next((a for a in sys.argv[1:] if not a.startswith("--")), ".")
CHECK = "--check" in sys.argv
PA = os.path.join(ROOT, "plotart")
RULES = [
    (re.compile(r'(data-pa-track="nav_living_gallery">)Living Gallery(</a>)'), r"\1Host Art\2"),
    (re.compile(r'(data-pa-track="nav_living_gallery_menu">)Living Gallery(</a>)'), r"\1Host Art\2"),
    (re.compile(r'(<li><a href="[^"]*living-gallery\.html">)Living Gallery(</a></li>)'), r"\1The Living Gallery\2"),
    # an artist's "Open to" pills, exactly as plotart_opportunities.artist_line now writes them (the artist's choices unchanged)
    (re.compile(r'(data-pa-track="artist_opportunity_link">)Living Gallery(</a>)'), r"\1Art Hosting\2"),
    (re.compile(r'(data-pa-track="artist_opportunity_link">)Hotels and workplaces(</a>)'), r"\1Business and venue hosting\2"),
]
stale, changed = [], 0
for d, _, fs in os.walk(PA):
    for f in sorted(fs):
        if not f.endswith(".html"):
            continue
        p = os.path.join(d, f); s = open(p, encoding="utf-8").read(); t = s
        for rx, rep in RULES:
            t = rx.sub(rep, t)
        if t != s:
            stale.append(os.path.relpath(p, ROOT))
            if not CHECK:
                open(p, "w", encoding="utf-8").write(t); changed += 1
if CHECK:
    print("Host Art terms: %s" % ("%d page(s) still carry an old label: %s" % (len(stale), ", ".join(stale[:5])) if stale else "every page is current"))
    sys.exit(1 if stale else 0)
print("Host Art terms: %d page(s) updated" % changed)
