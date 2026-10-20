"""PlotNua · WebP derivative <picture> layer (20 Oct 2026, post-crawl maintenance).

build-hero-webp-derivatives.py serves a hash-bound WebP derivative by wrapping
the page's EXISTING <img> in

    <picture style="display:contents"><source type="image/webp" srcset="..." sizes="...">
      <img ...unchanged...>
    </picture>

Governance builders that pin a page to a SHA-256 baseline taken before that
wrap (for example build-disc026-look-again.py) read the page through
without_derivative_picture(text, src) so their checks keep verifying exactly
the text they govern, byte for byte, while the wrap stays governed by the
derivative builder and the provenance guard (P12).

Exact and narrow: it removes ONLY the wrapper around the <img> whose src is the
named source JPEG, only when the <source> lists that source's own -960w and
full-width WebP derivatives, and only when it occurs exactly once. Text without
the wrapper is returned untouched; anything else raises ValueError.
"""
from __future__ import annotations
import re

OPEN = '<picture style="display:contents">'
CLOSE = '</picture>'


def _pattern(src: str):
    stem = re.escape(src[:-4])
    return re.compile(
        r'<picture style="display:contents"><source type="image/webp" srcset="'
        + stem + r'-960w\.webp 960w, ' + stem + r'\.webp \d+w" sizes="[^"<>]*">'
        r'(<img\b[^>]*\bsrc="' + re.escape(src) + r'"[^>]*>)</picture>')


def without_derivative_picture(text: str, src: str) -> str:
    if not src.endswith(".jpg"):
        raise ValueError("derivative picture layer: the source must be the JPEG")
    found = _pattern(src).findall(text)
    if not found:
        if re.search(re.escape(src[:-4]) + r'(-960w)?\.webp', text):
            raise ValueError("derivative picture layer: a derivative of %s appears outside the governed wrap" % src)
        return text
    if len(found) != 1:
        raise ValueError("derivative picture layer: %s is wrapped more than once" % src)
    out = _pattern(src).sub(lambda m: m.group(1), text, count=1)
    if re.search(re.escape(src[:-4]) + r'(-960w)?\.webp', out):
        raise ValueError("derivative picture layer: a derivative of %s remains after unwrapping" % src)
    return out
