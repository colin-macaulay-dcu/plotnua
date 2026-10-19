"""PlotNua · Search rail label layer: the ONE definition of the 19 Oct 2026 change.

On 19 October 2026 (SEO acceleration, item B) the search overlay's question
"What are you looking for?" stopped being an <h2> and became a <p> with the
same class: it is a label for the search field, not a section of the page, and
as an <h2> it made the overlay's question the first heading on pages whose real
H1 comes later. search.css styles .pns-ask by class, so nothing looks different.

The stub is injected identically on every rail page by build-search-rail.py.
Several governance builders pin pages that carry the rail (privacy.html, the
Discovery pages, the register pages) to a git base or a SHA-256 baseline taken
before that change. They read those pages through without_ask_label() so that
their checks keep verifying exactly the text they govern, byte for byte, and
the rail itself stays governed by build-search-rail.py and its baseline.

without_ask_label(text): exact inverse of the change. Text without the new line
is returned untouched. Text with it anywhere but once, inside the rail region,
or alongside the old line, raises ValueError, so nothing else can hide behind
the layer.
"""
from __future__ import annotations

ASK_H2 = '    <h2 class="pns-ask">What are you looking for?</h2>\n'
ASK_P = '    <p class="pns-ask">What are you looking for?</p>\n'
BEGIN = "<!-- PLOTNUA SEARCH RAIL v1 · BEGIN"
END = "<!-- PLOTNUA SEARCH RAIL v1 · END -->"


def with_ask_label(text: str) -> str:
    if ASK_H2 not in text:
        return text
    return text.replace(ASK_H2, ASK_P, 1)


def without_ask_label(text: str) -> str:
    n = text.count(ASK_P)
    if n == 0:
        return text
    if n != 1 or ASK_H2 in text:
        raise ValueError("search rail label layer: the overlay label is not exactly the governed change")
    at, b, e = text.index(ASK_P), text.find(BEGIN), text.find(END)
    if not (0 <= b < at < e):
        raise ValueError("search rail label layer: the overlay label sits outside the search rail region")
    out = text.replace(ASK_P, ASK_H2, 1)
    if with_ask_label(out) != text:
        raise ValueError("search rail label layer is not an exact, reversible edit")
    return out
