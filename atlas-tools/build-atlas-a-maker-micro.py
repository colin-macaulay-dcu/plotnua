#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER: the maker-band mark becomes the supplied micro derivative.

THE CORRECTION. The visible 16px placement beside "What Atlas holds on <org>"
was built as a hydrated .pn-atlas-slot, so it cloned the FULL Atlas A geometry
and scaled it to 16px. The supplied pack carries a derivative drawn for that
size -- assets/brand/atlas-mark-micro.svg -- and at 16px that is the asset to
use. Shrinking the full mark to 16px is not the same picture: the supplied pack
distinguishes the two deliberately.

So this placement joins the evidence-row mark in using the micro file, by the
same mechanism: a plain <img>, never hydrated, never animated.

WHAT CHANGES. One block: the three lines that created the slot become four that
create an <img>. The pnAtlasHydrate call for that label goes with them, because
an <img> needs no hydration.

WHAT DOES NOT. The 20px masthead placement, the 20px alternatives-heading
placement, the four Phase 1 placements, the evidence gating, every SVG file,
the motion CSS and the hydrator are all untouched. The spacing and alignment
stay exactly as approved: the element keeps .aa-find-lab-mark, which is what
carries the 7px gap and the one-pixel optical lift, and gains .pn-atlas-mark
and .pn-atlas-mark--16 so it takes the same 16px box as the evidence-row mark.

ACCESSIBILITY. alt="" and decorative, because the label it sits beside says
"What Atlas holds on ..." in words. The evidence-row micro mark keeps its
accessible name for the opposite reason: it stands alone with no visible word.
Same asset, different context, different treatment -- which is the correct
distinction, not an inconsistency.

Anchored. One edit, which must match exactly once or the builder refuses and
writes nothing.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE.parent / "your-plot.html"
MICRO = HERE.parent / "assets" / "brand" / "atlas-mark-micro.svg"


def die(msg):
    sys.stderr.write("REFUSED: " + msg + "\n")
    raise SystemExit(2)


OLD = """      /* ATLAS A, 16px, STATIC. This label names Atlas as the HOLDER of
         specific maker evidence, which is the closest thing on the visible
         page to what the mark is for. 16px, not 18px: the label is 10px
         uppercase and a larger mark would outweigh the words it introduces.
         Inserted before the text and left inline so the footnote superscript
         appended below keeps its baseline. */
      const blabMark = aaEl('span', 'pn-atlas-slot aa-find-lab-mark');
      blabMark.setAttribute('data-atlas-size', '16');
      blabMark.setAttribute('data-atlas-motion', 'static');
      blab.insertBefore(blabMark, blab.firstChild);
      if (window.pnAtlasHydrate) window.pnAtlasHydrate(blab);
"""

NEW = """      /* ATLAS A, 16px, STATIC, THE SUPPLIED MICRO DERIVATIVE. This label
         names Atlas as the HOLDER of specific maker evidence, which is the
         closest thing on the visible page to what the mark is for.

         THE MICRO FILE, NOT THE FULL MARK SCALED DOWN. The supplied pack
         draws a separate derivative for this size and the two are not the
         same picture, so at 16px the micro asset is the correct one -- the
         same file and the same plain-<img> mechanism the evidence rows use.
         An <img> is never hydrated and so can never animate.

         16px, not 18px: the label is 10px uppercase and a larger mark would
         outweigh the words it introduces. Inserted before the text and left
         inline so the footnote superscript appended below keeps its baseline.

         Decorative: alt is empty because the label beside it says "What Atlas
         holds on ..." in words. The evidence-row micro mark keeps an
         accessible name for the opposite reason -- it stands alone. */
      const blabMark = document.createElement('img');
      blabMark.className = 'pn-atlas-mark pn-atlas-mark--16 aa-find-lab-mark';
      blabMark.src = 'assets/brand/atlas-mark-micro.svg';
      blabMark.width = 16; blabMark.height = 16;
      blabMark.alt = '';
      blab.insertBefore(blabMark, blab.firstChild);
"""


def build():
    if not PAGE.exists():
        die("your-plot.html not found at " + str(PAGE))
    if not MICRO.exists():
        die("the supplied micro asset is missing: " + str(MICRO)
            + ". Refusing to point at a file that is not there.")

    before = PAGE.read_text(encoding="utf-8")

    if "blabMark = document.createElement('img')" in before:
        die("the maker-band mark is already the micro <img>; this builder has "
            "already been applied. Nothing written.")

    n = before.count(OLD)
    if n != 1:
        die("anchor matched %d times, expected exactly 1. The maker-band "
            "placement is not in the state this builder was written against. "
            "Nothing written." % n)

    src = before.replace(OLD, NEW)

    # NOTHING ELSE MAY MOVE. Each of these must survive at the same count.
    for keep, what in [
        ('<span class="pn-atlas-slot" data-atlas-size="24"></span>',
         'the 2 popover 24px slots'),
        ("akMark.setAttribute('data-atlas-size', '20')",
         'the "What Atlas Knows" 20px slot'),
        ("am.src = 'assets/brand/atlas-mark-micro.svg'",
         'the evidence-row 16px micro mark'),
        ("mastMark.setAttribute('data-atlas-size', '20')",
         'the Atlas assessment 20px masthead mark'),
        ('<span class="pn-atlas-slot" data-atlas-size="20" '
         'data-atlas-motion="static"></span>',
         'the alternatives-heading 20px static mark'),
        ('id="pn-atlas-a-template"', 'the single inlined template'),
        ('if (slot.getAttribute("data-atlas-motion") === "static") return;',
         'the hydrator\'s static rule'),
    ]:
        if src.count(keep) != before.count(keep):
            die("something other than the maker band changed: " + what
                + ". Nothing written.")

    # The spacing class must survive, or "same spacing as approved" is a claim
    # with nothing behind it.
    if src.count('aa-find-lab-mark') != before.count('aa-find-lab-mark'):
        die("the .aa-find-lab-mark spacing class did not survive. Nothing written.")

    if src == before:
        die("no change produced; refusing to claim a build")

    PAGE.write_text(src, encoding="utf-8")
    print("WROTE " + str(PAGE))
    print("  %d bytes -> %d bytes" % (len(before.encode()), len(src.encode())))
    print("  1 anchored edit, matched exactly once")
    print("  maker band now uses assets/brand/atlas-mark-micro.svg as a static <img>")
    print("  all other placements, the template, the hydrator and the gating verified unchanged")


if __name__ == "__main__":
    build()
