"""PLOTNUA · PREMIUM PAGE REGISTRY and the legacy-builder lock (founder decision, 23 Oct 2026).

ONE list of the pages that carry the approved Premium design. Two things read it:

  * atlas-tools/build-identity-stage1.py loads the Premium layer
    (assets/identity/pn-premium-discovery.css, body class pn-pd) on exactly these pages;
  * every legacy LAYOUT builder that can rewrite one of the garden-room family's pages
    calls refuse_if_premium() before it reads or writes anything, so it can never
    regenerate an earlier design over a Premium page (the pattern proven by the
    A Home for Art merge builder's L1 lock, 23 Oct 2026).

Builders that maintain a fenced data region inside a page (the garden-room price
builder, the maker explorer, the search rail, the global header, the identity layer)
are NOT locked: they keep working on Premium pages, and each Premium page's own
content guard proves the result.

Testing: PN_PREMIUM_EXTRA="page.html[,page.html]" adds pages to the registry for one
run (atlas-tools/prove-premium-locks.py uses it to prove every lock refuses).
"""
import os, sys

PREMIUM_PAGES = {
    "concept-modular-garden-offices.html",   # Maker pilot: local review draft, 26 Oct 2026
    "all-in-one-cabins-garden-rooms.html",   # Maker pilot: local review draft, 26 Oct 2026
    "discovery-a-home-for-art.html",       # Stage 2c, live 23 Oct 2026
    "garden-room-prices-ireland.html",     # Batch 1 · 1, founder approval 23 Oct 2026
    "discovery-living-in-the-garden.html", # Batch 1 · Garden Living (founder direction 23 Oct 2026)
    "discovery-garden-retreat.html",       # Batch 1 · Garden Living
    "triq-cube.html",                      # Batch 1 · Garden Living (product page)
    "discovery-hidden-bins.html",            # Batch 2 · standard Discoveries (founder direction 23 Oct 2026)
    "discovery-the-borrowed-garden.html",    # Batch 2 · standard Discoveries (founder direction 23 Oct 2026)
    "discovery-driveway-income.html",        # Batch 2 · standard Discoveries (founder direction 23 Oct 2026)
    "discovery-hidden-cars.html",            # Batch 2 · standard Discoveries (founder direction 23 Oct 2026)
    "discovery-home-exchange.html",          # Batch 2 · standard Discoveries (founder direction 23 Oct 2026)
    "discovery-neighbourhood-parcel-house.html",# Batch 2 · standard Discoveries (founder direction 23 Oct 2026)
    "discovery-your-home-on-screen.html",    # Batch 2 · standard Discoveries (founder direction 23 Oct 2026)
    "about.html",                            # Batch 3 · brand and conversion pages (founder direction 24 Oct 2026)
    "contact.html",                          # Batch 3 · brand and conversion pages (founder direction 24 Oct 2026)
    "artist-register.html",                  # Batch 3 · brand and conversion pages (founder direction 24 Oct 2026)
    "discovery-house-as-power-station.html", # Batch 4 · signature Discoveries (Pass 1, 24 Oct 2026)
    "discovery-above-and-beyond.html",       # Batch 4 · signature Discoveries (Pass 1, 24 Oct 2026)
}


def premium_pages():
    extra = {p.strip() for p in os.environ.get("PN_PREMIUM_EXTRA", "").split(",") if p.strip()}
    return PREMIUM_PAGES | extra


def refuse_if_premium(builder, targets):
    """Exit 2, before anything is read or written, if any target page is Premium."""
    # --check reads and reports only; it never writes, so it may still run its content guards
    # on a Premium page (the gate runs build-garden-retreat-restructure.py --check). Every
    # writing mode, including a builder's default, still refuses.
    if sys.argv[1:] == ["--check"]:
        return
    hit = sorted(set(targets) & premium_pages())
    if hit:
        print("%s · REFUSED: PREMIUM %s carries the approved Premium design; this legacy builder "
              "would regenerate an earlier layout over it -- nothing written" % (builder, ", ".join(hit)))
        sys.exit(2)
