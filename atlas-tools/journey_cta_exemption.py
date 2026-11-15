"""
THE ONE PERMITTED ADDITION TO A PINNED PREMIUM DISCOVERY: the journey CTA band
(15 Nov 2026, built by atlas-tools/build-discovery-journey-cta.py).

The premium-discovery proofs pin each page's wording, links, images and hero
region against a snapshot. The journey CTA band adds one block directly below
the hero. Rather than re-pin every snapshot (which would bless whatever else
changed at the same time), each proof passes the page through
strip_journey_cta() first. That removes the band ONLY IF it is exactly the
band, and refuses otherwise:

  * at most one fenced block, sitting directly after the hero (or its
    AI-image note);
  * nothing inside it but the stylesheet link, the aside, its kicker and line,
    and one or two buttons -- no image, no script, no form, no other element;
  * every button href ALREADY appears elsewhere on the page, so the band can
    only repeat a journey link the page already carries; it cannot introduce a
    new route.

With the band removed the page is byte-identical to the page before it was
added, so every pinned check still runs in full against the real content.
"""
import re

BEGIN = "<!-- PN-JOURNEY-CTA v1 · BEGIN · built by atlas-tools/build-discovery-journey-cta.py — do not hand-edit -->"
END = "<!-- PN-JOURNEY-CTA v1 · END -->"

_BLOCK = re.compile(r"\n\n" + re.escape(BEGIN) + r"([\s\S]*?)" + re.escape(END))
_SHAPE = re.compile(
    r'^\n<link rel="stylesheet" href="assets/components/pn-journey-cta\.css\?v=1">\n'
    r'<aside class="pn-jcta( pn-jcta--two)?" aria-label="Check your own property">\n'
    r'  <div class="pn-jcta-in">\n'
    r'    <div class="pn-jcta-copy">\n'
    r'      <p class="pn-jcta-k">[^<>]{1,40}</p>\n'
    r'      <p class="pn-jcta-t">[^<>]{1,160}</p>\n'
    r'    </div>\n'
    r'    <div class="pn-jcta-acts">\n'
    r'((?:      <a class="pn-jcta-btn(?: is-alt)?" href="[^"<>]+">[^<>]{1,60} '
    r'<span aria-hidden="true">&rarr;</span></a>\n){1,2})'
    r'    </div>\n'
    r'  </div>\n'
    r'</aside>\n$')
_AFTER_HERO = re.compile(r'(</header>|<p class="pn-hero-note[^"]*">[^<]*</p>)\Z')


class JourneyCtaRefused(Exception):
    pass


def strip_journey_cta(page):
    blocks = list(_BLOCK.finditer(page))
    if not blocks:
        if BEGIN in page or END in page:
            raise JourneyCtaRefused("journey CTA markers present but not in the built form")
        return page
    if len(blocks) != 1:
        raise JourneyCtaRefused("more than one journey CTA block")
    m = blocks[0]
    inner = m.group(1)
    shape = _SHAPE.match(inner)
    if not shape:
        raise JourneyCtaRefused("journey CTA block is not exactly the built band")
    if not _AFTER_HERO.search(page[:m.start()].rstrip()):
        raise JourneyCtaRefused("journey CTA block is not directly below the hero")
    rest = page[:m.start()] + page[m.end():]
    for href in re.findall(r'href="([^"]+)"', shape.group(2)):
        if ('href="%s"' % href) not in rest:
            raise JourneyCtaRefused("journey CTA link is not already on the page: " + href)
    return rest
