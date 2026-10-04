#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER: make the Atlas A mark visible without being asked for.

THE DEFECT THIS CORRECTS. Phase 1 wired three placements and every one of them
is behind an interaction:

    24px  "What is Atlas?" popover    opacity:0; visibility:hidden until a
                                      click on the inline word "Atlas"
    20px  "What Atlas Knows"          inside a closed <details>, on the
                                      Product Detail screen, two clicks deep
    16px  established evidence rows   same closed panel, and gated to the
                                      552 of 1,783 model-level reads

Mechanically all three are correct: hydrated, sized, gated, animated to the
supplied contract. But a mark nobody sees is not an identity. Meanwhile the
three places the page says "Atlas" OUT LOUD, on first render, carried nothing.

THE CORRECTION. Three new placements, on surfaces that are visible without any
interaction, each beside wording that already names Atlas:

    20px  "Atlas assessment" masthead     aaRenderAssessment() -- the single
                                          place Atlas explains itself on
                                          Results. Settles once, by the
                                          existing contract.
    20px  "Atlas looked at this in        the alternatives rail heading.
          other ways."                    STATIC.
    16px  "What Atlas holds on <org>"     the maker band label. STATIC.
                                          16px, not 18px: the label is 10px
                                          uppercase, and 18px would outweigh
                                          the words it introduces.

ALL FOUR PHASE 1 PLACEMENTS ARE KEPT. Nothing is moved or removed. The 16px
evidence-row signature in particular is the only placement that makes a CLAIM
rather than a label, and the three-condition gate behind it is untouched.

NO NEW GEOMETRY. Every new placement is a .pn-atlas-slot hydrated from the
single inlined #pn-atlas-a-template, so there is still exactly one copy of the
supplied artwork in the page. No file in assets/brand/ is read, written or
referenced by this builder.

TWO MECHANICAL POINTS THAT DECIDED THE IMPLEMENTATION.

1. aaRenderAssessment() REPAINTS. Its host is emptied and re-rendered once the
   lazy detail partitions land (the 451-of-487 defect). A slot created there
   cannot wait for DOMContentLoaded, so both assessment placements call
   window.pnAtlasHydrate() on their own subtree, exactly as the existing 20px
   slot already does.

2. .aa-mast IS display:flex; justify-content:space-between. A slot added as a
   direct child would become a third flex item and break the two-ended
   masthead. The mark and the label therefore go inside one .aa-mast-lead
   wrapper, which keeps the masthead two-ended and leaves .aa-mast-l styling
   untouched (it is matched by class, not by position).

STATIC MEANS STATIC. The hydrator gains one line: a slot marked
data-atlas-motion="static" never receives .pn-am-play, so it cannot animate
even though it shares the hydration path. The motion CSS is not touched, so the
supplied contract -- house fixed, fields settle once, nothing loops -- is
unchanged for the placements that do move.

Anchored. Five edits, each must match exactly once or the builder refuses and
writes nothing.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE.parent / "your-plot.html"


def die(msg):
    sys.stderr.write("REFUSED: " + msg + "\n")
    raise SystemExit(2)


def anchored(src, old, new, label):
    n = src.count(old)
    if n != 1:
        die("%s: anchor matched %d times, expected exactly 1. The page has "
            "moved since this builder was written; re-read the site before "
            "editing. Nothing written." % (label, n))
    return src.replace(old, new)


# ------------------------------------------------------------- edit 1 of 5 CSS
CSS_OLD = """  /* On an evidence row the mark is a quiet trailing signature. */
  .am-ev-atlas{ margin-left:6px; position:relative; top:2px; opacity:.9; }
"""

CSS_NEW = """  /* On an evidence row the mark is a quiet trailing signature. */
  .am-ev-atlas{ margin-left:6px; position:relative; top:2px; opacity:.9; }

  /* ATLAS A ON THE VISIBLE SURFACES.

     Phase 1 put the mark only where Atlas EXPLAINS itself -- a popover and a
     collapsed panel. These three are where the page NAMES Atlas on first
     render, so they are where the mark has to be.

     .aa-mast is justify-content:space-between and must stay two-ended, so the
     mark and the label share one inline-flex wrapper rather than becoming a
     third flex item.

     The maker label is a <p> with an appended footnote superscript, so its
     mark stays inline-block: making that label a flex row would pull the
     superscript out of the text baseline. */
  .aa-mast-lead{ display:inline-flex; align-items:center; gap:8px; }
  .results-gallery-heading.has-atlas-mark{
    display:flex; align-items:center; gap:10px;
  }
  .aa-find-lab-mark{
    display:inline-block; vertical-align:middle;
    margin-right:7px; position:relative; top:-1px;
  }
"""

# -------------------------------------------------------- edit 2 of 5 hydrator
HYD_OLD = """    slot.appendChild(svg);
    slot.setAttribute("data-atlas-done", "1");
    requestAnimationFrame(function(){ svg.classList.add("pn-am-play"); });
"""

HYD_NEW = """    slot.appendChild(svg);
    slot.setAttribute("data-atlas-done", "1");
    /* A STATIC PLACEMENT NEVER RECEIVES THE PLAY CLASS. Without the class
       there is no animation-name, so the fields simply render in their
       authored state. The marks beside the alternatives heading and the maker
       label are quiet signatures on surfaces the homeowner is reading, not
       arrivals, and one settle per heading is enough movement on a page that
       already carries one. */
    if (slot.getAttribute("data-atlas-motion") === "static") return;
    requestAnimationFrame(function(){ svg.classList.add("pn-am-play"); });
"""

# ------------------------------------------------------- edit 3 of 5 masthead
MAST_OLD = """    const mast = aaEl('div', 'aa-mast');
    mast.appendChild(aaEl('span', 'aa-mast-l', 'Atlas assessment'));
"""

MAST_NEW = """    const mast = aaEl('div', 'aa-mast');
    /* ATLAS A, 20px, VISIBLE ON FIRST RENDER OF THE ASSESSMENT.

       This masthead is the single place Atlas explains itself on Results, and
       it is on screen without a click, which is what the Phase 1 placements
       were not. The mark settles once by the existing contract; the house does
       not move, because it carries no animation rule at all.

       The wrapper keeps .aa-mast two-ended: the lead group sits left, the
       organisation stays right. Hydrated here rather than at DOMContentLoaded
       because this host is emptied and repainted when the lazy detail
       partitions land. */
    const mastLead = aaEl('span', 'aa-mast-lead');
    const mastMark = aaEl('span', 'pn-atlas-slot');
    mastMark.setAttribute('data-atlas-size', '20');
    mastLead.appendChild(mastMark);
    mastLead.appendChild(aaEl('span', 'aa-mast-l', 'Atlas assessment'));
    mast.appendChild(mastLead);
    if (window.pnAtlasHydrate) window.pnAtlasHydrate(mastLead);
"""

# --------------------------------------------------- edit 4 of 5 alternatives
ALT_OLD = ('    <div class="results-gallery-heading" id="matchAlternativesHeading"'
           ' hidden>Atlas looked at this in other ways.</div>')

ALT_NEW = ('    <!-- ATLAS A, 20px, STATIC. The sentence names Atlas as the author of\n'
           '         the alternatives, so the mark belongs to it. Static: this is a\n'
           '         heading the homeowner scrolls to, not an arrival. The slot\n'
           '         hydrates with the rest of the static markup; the heading being\n'
           '         `hidden` until the rail populates does not affect that. -->\n'
           '    <div class="results-gallery-heading has-atlas-mark"'
           ' id="matchAlternativesHeading" hidden><span class="pn-atlas-slot"'
           ' data-atlas-size="20" data-atlas-motion="static"></span>'
           '<span>Atlas looked at this in other ways.</span></div>')

# ----------------------------------------------------- edit 5 of 5 maker band
MKR_OLD = """      const blab = aaEl('p', 'aa-find-lab',
        'What Atlas holds on ' + (org || 'the maker'));
"""

MKR_NEW = """      const blab = aaEl('p', 'aa-find-lab',
        'What Atlas holds on ' + (org || 'the maker'));
      /* ATLAS A, 16px, STATIC. This label names Atlas as the HOLDER of
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


def build():
    if not PAGE.exists():
        die("your-plot.html not found at " + str(PAGE))

    before = PAGE.read_text(encoding="utf-8")

    if "aa-mast-lead" in before:
        die("the page already carries .aa-mast-lead; this builder has already "
            "been applied. Nothing written.")

    src = before
    src = anchored(src, CSS_OLD, CSS_NEW, "edit 1/5 CSS")
    src = anchored(src, HYD_OLD, HYD_NEW, "edit 2/5 hydrator static support")
    src = anchored(src, MAST_OLD, MAST_NEW, "edit 3/5 Atlas assessment masthead")
    src = anchored(src, ALT_OLD, ALT_NEW, "edit 4/5 alternatives heading")
    src = anchored(src, MKR_OLD, MKR_NEW, "edit 5/5 maker band label")

    # The Phase 1 placements must survive verbatim. Checked here as well as in
    # the proof, because a builder that silently relocated one would be the
    # worst possible outcome of a visibility fix.
    for keep, what in [
        ('<span class="pn-atlas-slot" data-atlas-size="24"></span>',
         'the 24px popover slots'),
        ("akMark.setAttribute('data-atlas-size', '20')",
         'the "What Atlas Knows" 20px slot'),
        ("am.src = 'assets/brand/atlas-mark-micro.svg'",
         'the 16px evidence-row micro mark'),
    ]:
        if src.count(keep) != before.count(keep):
            die("a Phase 1 placement changed count: " + what + ". Nothing written.")

    # Exactly one copy of the supplied geometry, still.
    if src.count('id="pn-atlas-a-template"') != 1:
        die("the page no longer holds exactly one Atlas template. Nothing written.")

    if src == before:
        die("no change produced; refusing to claim a build")

    PAGE.write_text(src, encoding="utf-8")
    print("WROTE " + str(PAGE))
    print("  %d bytes -> %d bytes (+%d)"
          % (len(before.encode()), len(src.encode()),
             len(src.encode()) - len(before.encode())))
    print("  5 anchored edits, each matched exactly once")
    print("  Phase 1 placements verified unchanged; one template copy intact")


if __name__ == "__main__":
    build()
