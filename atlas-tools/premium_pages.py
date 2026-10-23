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
    "discovery-a-home-for-art.html",       # Stage 2c, live 23 Oct 2026
    "garden-room-prices-ireland.html",     # Batch 1 · 1, founder approval 23 Oct 2026
}


def premium_pages():
    extra = {p.strip() for p in os.environ.get("PN_PREMIUM_EXTRA", "").split(",") if p.strip()}
    return PREMIUM_PAGES | extra


def refuse_if_premium(builder, targets):
    """Exit 2, before anything is read or written, if any target page is Premium."""
    hit = sorted(set(targets) & premium_pages())
    if hit:
        print("%s · REFUSED: PREMIUM %s carries the approved Premium design; this legacy builder "
              "would regenerate an earlier layout over it -- nothing written" % (builder, ", ".join(hit)))
        sys.exit(2)
