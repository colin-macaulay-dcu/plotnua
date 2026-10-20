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

A SECOND GOVERNED CHANGE, 20 October 2026 (post-crawl maintenance, SiteOne
triage D4): the same paragraph gains id="pnsAsk" and the search field gains
aria-labelledby="pnsAsk", so the visible question names the field. Nothing
else in the rail changes. This module now knows both changes, in order:

  2026-10-19  <h2 class="pns-ask">  ->  <p class="pns-ask">
  2026-10-20  <p class="pns-ask">   ->  <p class="pns-ask" id="pnsAsk">
              <input ... id="pnsInput" autocomplete=...
                                    ->  <input ... id="pnsInput" aria-labelledby="pnsAsk" autocomplete=...

with_ask_label(text): brings a rail from either earlier state to the current one.
without_ask_label(text): exact inverse of the change. Text without the new line
is returned untouched. Text with it anywhere but once, inside the rail region,
or alongside the old line, raises ValueError, so nothing else can hide behind
the layer.
"""
from __future__ import annotations

ASK_H2 = '    <h2 class="pns-ask">What are you looking for?</h2>\n'
ASK_P = '    <p class="pns-ask">What are you looking for?</p>\n'
ASK_P_ID = '    <p class="pns-ask" id="pnsAsk">What are you looking for?</p>\n'
INPUT_OLD = '<input type="search" class="pns-input" id="pnsInput" autocomplete="off"'
INPUT_NEW = '<input type="search" class="pns-input" id="pnsInput" aria-labelledby="pnsAsk" autocomplete="off"'
BEGIN = "<!-- PLOTNUA SEARCH RAIL v1 · BEGIN"
END = "<!-- PLOTNUA SEARCH RAIL v1 · END -->"


def _in_rail(text: str, piece: str) -> bool:
    at, b, e = text.find(piece), text.find(BEGIN), text.find(END)
    return 0 <= b < at < e


def with_ask_label(text: str) -> str:
    """Any earlier rail state -> the current one. Text without a rail label is untouched."""
    out = text
    if ASK_H2 in out:
        out = out.replace(ASK_H2, ASK_P_ID, 1)
    elif ASK_P in out:
        out = out.replace(ASK_P, ASK_P_ID, 1)
    if ASK_P_ID in out and INPUT_NEW not in out and out.count(INPUT_OLD) == 1:
        out = out.replace(INPUT_OLD, INPUT_NEW, 1)
    return out


def without_ask_label(text: str) -> str:
    """The current (or the 19 Oct) rail -> the pre-19 Oct rail, exactly."""
    n_id, n_p, n_new = text.count(ASK_P_ID), text.count(ASK_P), text.count(INPUT_NEW)
    if n_id == 0 and n_p == 0:
        if n_new:
            raise ValueError("search rail label layer: the field is labelled but the label is missing")
        return text
    if n_id + n_p != 1 or ASK_H2 in text:
        raise ValueError("search rail label layer: the overlay label is not exactly the governed change")
    label = ASK_P_ID if n_id else ASK_P
    if not _in_rail(text, label):
        raise ValueError("search rail label layer: the overlay label sits outside the search rail region")
    if n_id:
        if n_new != 1 or text.count(INPUT_OLD) != 0 or not _in_rail(text, INPUT_NEW):
            raise ValueError("search rail label layer: the field is not exactly the governed change")
    elif n_new:
        raise ValueError("search rail label layer: a labelled field without its label")
    out = text.replace(label, ASK_H2, 1)
    if n_id:
        out = out.replace(INPUT_NEW, INPUT_OLD, 1)
    # exact and reversible: re-applying the same step(s) gives the input back
    back = out.replace(ASK_H2, label, 1)
    if n_id:
        back = back.replace(INPUT_OLD, INPUT_NEW, 1)
    if back != text:
        raise ValueError("search rail label layer is not an exact, reversible edit")
    return out
