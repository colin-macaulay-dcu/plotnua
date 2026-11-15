#!/usr/bin/env python3
"""
CAPABILITY PROOF for atlas-tools/journey_cta_exemption.py.

The exemption lets the pinned premium-discovery proofs ignore the journey CTA
band. This proves it ignores ONLY that band: each planted fault below must be
refused, and every real page must strip back to a page with no band at all.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from journey_cta_exemption import strip_journey_cta, JourneyCtaRefused, BEGIN, END  # noqa: E402

ROOT = HERE.parent
PAGES = sorted(p for p in ROOT.glob("discovery-*.html") if BEGIN in p.read_text(encoding="utf-8"))
if len(PAGES) != 9:
    sys.exit("JOURNEY CTA EXEMPTION · expected 9 pages carrying the band, found %d" % len(PAGES))

page = (ROOT / "discovery-hidden-bins.html").read_text(encoding="utf-8")
blk = page[page.index(BEGIN):page.index(END) + len(END)]
FAULTS = {
    "a new route inside the band": lambda t: t.replace('href="disc029-hidden-bins-check.html"', 'href="disc999-new.html"', 1),
    "an image inside the band": lambda t: t.replace('<p class="pn-jcta-k">', '<img src="x.jpg" alt=""><p class="pn-jcta-k">', 1),
    "a script inside the band": lambda t: t.replace('</aside>', '<script>1</script></aside>', 1),
    "a third button": lambda t: t.replace(blk, blk.replace('    </div>\n  </div>\n</aside>', '      <a class="pn-jcta-btn" href="disc029-hidden-bins-check.html">More <span aria-hidden="true">&rarr;</span></a>\n      <a class="pn-jcta-btn" href="disc029-hidden-bins-check.html">Again <span aria-hidden="true">&rarr;</span></a>\n    </div>\n  </div>\n</aside>', 1), 1),
    "a second band": lambda t: t.replace("<main", "\n\n" + blk + "\n<main", 1),
    "the band moved below the hero": lambda t: t.replace("\n\n" + blk, "", 1).replace('<section class="related reveal">', "\n\n" + blk + '\n<section class="related reveal">', 1),
    "an unfenced edit to the band's markers": lambda t: t.replace(END, "<!-- end -->", 1),
}
caught = 0
for name, plant in FAULTS.items():
    bad = plant(page)
    assert bad != page, name
    try:
        strip_journey_cta(bad)
        print("  NOT CAUGHT  " + name)
    except JourneyCtaRefused as e:
        caught += 1
        print("  caught      %s (%s)" % (name, e))

clean = 0
for p in PAGES:
    out = strip_journey_cta(p.read_text(encoding="utf-8"))
    if BEGIN not in out and "pn-jcta" not in out and "pn-journey-cta.css" not in out:
        clean += 1
print("JOURNEY CTA EXEMPTION · %d/%d planted faults refused · %d/%d pages strip clean"
      % (caught, len(FAULTS), clean, len(PAGES)))
sys.exit(0 if caught == len(FAULTS) and clean == len(PAGES) else 1)
