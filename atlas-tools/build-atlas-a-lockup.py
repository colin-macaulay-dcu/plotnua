#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER: one Atlas identity lockup, at a size the artwork survives.

WHY THE PREVIOUS SIZES WERE WRONG, MEASURED RATHER THAN FELT.

The supplied viewBox is 1157 x 1038 -- NOT square, 1.1146 : 1. Every rule
shipped so far set a square CSS box, so with the default xMidYMid meet the
artwork fitted to width and 10.3% of the box height was dead space. Nominal px
overstated the mark.

Worse, the house -- the anchor that makes this PlotNua rather than a generic
flowing form -- is 18.1% of the mark's width and 23.3% of its height. So:

      nominal     house drawn        finest sage ribbon
      16px        2.89 x 3.35 px     0.61 px
      20px        3.61 x 4.18 px     0.76 px
      36px        6.50 x 7.53 px     1.37 px
      60px       10.82 x 12.54 px    2.28 px

The 2.00px legibility floor this project already uses is not cleared until
about 53px. A 36px secondary mark would have repeated the same error one step
up, which is why there is now ONE visible mark instead of three.

WHAT THIS BUILDS.

  PRIMARY, and the only new visible placement: the ATLAS ASSESSMENT masthead
  becomes a lockup -- the full approved mark at an ASPECT-CORRECT 60 x 54px
  box, paired with the existing "Atlas assessment" label as one unit. The
  masthead keeps its hairline, its two-ended layout and its right-hand
  organisation label. Its vertical alignment moves from baseline to centre,
  because a 54px-tall child cannot share a baseline with a 10px label.

  REMOVED: the 20px mark beside "Atlas looked at this in other ways." and the
  16px micro mark beside "What Atlas holds on <org>". Neither is replaced.
  Those lines go back to exactly the markup they had before, character for
  character.

  KEPT: the gated evidence-row micro signature, and all four Phase 1
  placements. Nothing about the three-condition gate is touched.

ASPECT-CORRECT, NOT SQUARE. .pn-atlas-mark--60 is 60 x 54px, and the hydrator
learns to read an explicit data-atlas-height so the attribute geometry agrees
with the CSS instead of being overridden by it. The existing 24 / 20 / 16
square classes are left alone -- they are the small placements, where the
letterboxing is a rounding error rather than the whole problem.

NO NEW CONTAINER. No fill, no border, no radius, no shadow, no pill, no badge.
The lockup is the masthead it already was, with the mark inside it.

GOVERNANCE. The AA-001 note said the spread is "Typographic only: no fills, no
boxes, no shadows, no pills, no icons." A 60px mark in that masthead
contradicts it, so the note is amended in the same edit: the restriction
stands, with the Atlas lockup named as the single brand exception. Code and the
rule it states about itself should not disagree.

NO GEOMETRY CHANGES. No file in assets/brand/ is read or written. The mark is
still cloned from the one inlined template.

Anchored. Eight edits, each must match exactly once or the builder refuses and
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
        die("%s: anchor matched %d times, expected exactly 1. Nothing written."
            % (label, n))
    return src.replace(old, new)


# ------------------------------------------------------- 1 . governance note
GOV_OLD = """     AA-001 · THE ATLAS ASSESSMENT — frozen editorial spread.
     Typographic only: no fills, no boxes, no shadows, no pills, no icons.
"""

GOV_NEW = """     AA-001 · THE ATLAS ASSESSMENT — frozen editorial spread.
     Typographic, with ONE named exception: no fills, no boxes, no shadows,
     no pills and no icons — except the Atlas identity lockup in the masthead,
     which is the single brand exception and is not an icon in the sense this
     rule forbids. It carries no container of its own: no fill, no border, no
     radius, no shadow, no pill. It is the approved Atlas A artwork set beside
     the "Atlas assessment" label as one unit, at an aspect-correct 60 x 54px,
     because the measured geometry does not survive below roughly 53px: the
     house is 18.1% of the mark's width, and the finest ribbon falls under the
     2px floor. Nothing else in this spread may add a mark, and no second
     visible Atlas mark may be introduced on this page without that
     measurement being redone.
"""

# ------------------------------------------------------------ 2 . mast layout
MAST_CSS_OLD = """  .aa-mast{
    border-top:1px solid var(--aa-voice); padding-top:9px;
    display:flex; justify-content:space-between; align-items:baseline;
    gap:20px; flex-wrap:wrap;
  }
"""

MAST_CSS_NEW = """  .aa-mast{
    border-top:1px solid var(--aa-voice); padding-top:14px;
    display:flex; justify-content:space-between; align-items:center;
    gap:20px; flex-wrap:wrap;
  }
"""

# --------------------------------------------- 3 . the aspect-correct size
SIZE_OLD = """  .pn-atlas-mark--16{ width:16px; height:16px; }
"""

SIZE_NEW = """  .pn-atlas-mark--16{ width:16px; height:16px; }
  /* ASPECT-CORRECT, NOT SQUARE. The viewBox is 1157x1038, so a square box
     wastes 10.3% of its height and makes the nominal size a lie. 60x54 is the
     artwork's own ratio: 60 / 1.1146 = 53.8, rounded to 54. */
  .pn-atlas-mark--60{ width:60px; height:54px; }
"""

# ------------------------------------- 4 . the three visible-placement rules
VIS_OLD = """  /* ATLAS A ON THE VISIBLE SURFACES.

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

VIS_NEW = """  /* THE ATLAS IDENTITY LOCKUP — the one visible mark on this page.

     Phase 1 put the mark only where Atlas EXPLAINS itself: a popover and a
     collapsed panel, neither of which a homeowner reaches without a click. The
     first correction added three visible marks at 16-20px, which failed on
     sight for a reason the geometry predicts -- at 20px the house renders
     3.6 x 4.2px and the finest ribbon 0.76px, so the identity dissolves into a
     status glyph. The 2px floor is not cleared until about 53px.

     So there is now ONE visible mark, at a size the artwork survives, in the
     one place that is the page's Atlas moment. .aa-mast stays two-ended, so
     the mark and its label share this lead group rather than becoming a third
     flex item; the group is what makes them one lockup rather than an icon
     placed near some words. No container: no fill, border, radius or shadow. */
  .aa-mast-lead{ display:flex; align-items:center; gap:16px; }
"""

# --------------------------------------------- 5 . hydrator, aspect-correct
HYD_OLD = """    var px = parseInt(slot.getAttribute("data-atlas-size"), 10) || 24;
    var svg = tpl.content.firstElementChild.cloneNode(true);
    svg.classList.add("pn-atlas-mark--" + px);
    svg.setAttribute("width", px);
    svg.setAttribute("height", px);
"""

HYD_NEW = """    var px = parseInt(slot.getAttribute("data-atlas-size"), 10) || 24;
    /* ASPECT-CORRECT HEIGHT WHERE ONE IS DECLARED. The viewBox is 1157x1038,
       so a square box letterboxes the artwork and loses 10.3% of its height.
       CSS already sizes the box; setting the attributes to agree keeps the
       intrinsic ratio right before the stylesheet applies, and keeps the two
       from contradicting each other. */
    var ph = parseInt(slot.getAttribute("data-atlas-height"), 10) || px;
    var svg = tpl.content.firstElementChild.cloneNode(true);
    svg.classList.add("pn-atlas-mark--" + px);
    svg.setAttribute("width", px);
    svg.setAttribute("height", ph);
"""

# ------------------------------------------------- 6 . the masthead placement
PLACE_OLD = """    const mastLead = aaEl('span', 'aa-mast-lead');
    const mastMark = aaEl('span', 'pn-atlas-slot');
    mastMark.setAttribute('data-atlas-size', '20');
    mastLead.appendChild(mastMark);
"""

PLACE_NEW = """    const mastLead = aaEl('span', 'aa-mast-lead');
    const mastMark = aaEl('span', 'pn-atlas-slot');
    /* 60 x 54, the artwork's own ratio. Not 20: at 20px the house draws
       3.6 x 4.2px and the mark reads as a status glyph rather than an
       identity. Measured, not guessed. */
    mastMark.setAttribute('data-atlas-size', '60');
    mastMark.setAttribute('data-atlas-height', '54');
    mastLead.appendChild(mastMark);
"""

# ----------------------------------------- 7a . alternatives heading reverted
ALT_OLD = ('    <!-- ATLAS A, 20px, STATIC. The sentence names Atlas as the author of\n'
           '         the alternatives, so the mark belongs to it. Static: this is a\n'
           '         heading the homeowner scrolls to, not an arrival. The slot\n'
           '         hydrates with the rest of the static markup; the heading being\n'
           '         `hidden` until the rail populates does not affect that. -->\n'
           '    <div class="results-gallery-heading has-atlas-mark"'
           ' id="matchAlternativesHeading" hidden><span class="pn-atlas-slot"'
           ' data-atlas-size="20" data-atlas-motion="static"></span>'
           '<span>Atlas looked at this in other ways.</span></div>')

ALT_NEW = ('    <div class="results-gallery-heading" id="matchAlternativesHeading"'
           ' hidden>Atlas looked at this in other ways.</div>')

# ------------------------------------------- 7b . maker band label reverted
MKR_OLD = """      /* ATLAS A, 16px, STATIC, THE SUPPLIED MICRO DERIVATIVE. This label
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

MKR_NEW = ""

# ------------------------------------- 8 . retire the static-slot mechanism
# Both static placements are gone, so nothing in the page sets
# data-atlas-motion any more. A branch with no caller is a comment that looks
# like a mechanism, and the next person would reasonably assume a static slot
# is still a supported option. The one remaining mark animates; if a static
# placement is ever wanted again, this comes back WITH its consumer.
STATIC_OLD = """    /* A STATIC PLACEMENT NEVER RECEIVES THE PLAY CLASS. Without the class
       there is no animation-name, so the fields simply render in their
       authored state. The marks beside the alternatives heading and the maker
       label are quiet signatures on surfaces the homeowner is reading, not
       arrivals, and one settle per heading is enough movement on a page that
       already carries one. */
    if (slot.getAttribute("data-atlas-motion") === "static") return;
    requestAnimationFrame(function(){ svg.classList.add("pn-am-play"); });
"""

STATIC_NEW = """    requestAnimationFrame(function(){ svg.classList.add("pn-am-play"); });
"""


def build():
    if not PAGE.exists():
        die("your-plot.html not found at " + str(PAGE))

    before = PAGE.read_text(encoding="utf-8")

    if "data-atlas-height" in before:
        die("the page already carries data-atlas-height; this builder has "
            "already been applied. Nothing written.")

    src = before
    src = anchored(src, GOV_OLD, GOV_NEW, "1/7 AA-001 governance note")
    src = anchored(src, MAST_CSS_OLD, MAST_CSS_NEW, "2/7 .aa-mast alignment")
    src = anchored(src, SIZE_OLD, SIZE_NEW, "3/7 aspect-correct 60x54 class")
    src = anchored(src, VIS_OLD, VIS_NEW, "4/7 visible-placement CSS")
    src = anchored(src, HYD_OLD, HYD_NEW, "5/7 hydrator aspect-correct height")
    src = anchored(src, PLACE_OLD, PLACE_NEW, "6/7 masthead placement at 60")
    src = anchored(src, ALT_OLD, ALT_NEW, "7a/7 alternatives heading reverted")
    src = anchored(src, MKR_OLD, MKR_NEW, "7b/8 maker band label reverted")
    src = anchored(src, STATIC_OLD, STATIC_NEW, "8/8 retire static-slot mechanism")

    # THE REMOVALS MUST BE COMPLETE. A half-removed mark is worse than either
    # state, so the vocabulary of both retired placements must be gone.
    for gone, what in [
        ('has-atlas-mark" id="matchAlternativesHeading"', 'the alternatives mark'),
        ('aa-find-lab-mark', 'the maker-band mark and its CSS'),
        ('results-gallery-heading.has-atlas-mark', 'the alternatives heading CSS'),
        ('data-atlas-motion', 'the static-slot mechanism, now unused'),
    ]:
        if gone in src:
            die("a retired placement survives: " + what + ". Nothing written.")

    # AND THE KEEPS MUST BE UNTOUCHED, at the same count.
    for keep, what in [
        ('<span class="pn-atlas-slot" data-atlas-size="24"></span>',
         'the 2 popover 24px slots'),
        ("akMark.setAttribute('data-atlas-size', '20')",
         'the "What Atlas Knows" 20px slot'),
        ("am.src = 'assets/brand/atlas-mark-micro.svg'",
         'the gated evidence-row micro mark'),
        ("am.className = 'pn-atlas-mark pn-atlas-mark--16 am-ev-atlas'",
         'the evidence-row micro mark class'),
        ("if (row.state === 'established' && !row.scope && !row.conflict){",
         'the three-condition evidence gate'),
        ('id="pn-atlas-a-template"', 'the single inlined template'),
        ('viewBox="0 0 1157 1038"', 'the supplied viewBox'),
    ]:
        if src.count(keep) != before.count(keep):
            die("a kept placement changed count: " + what + ". Nothing written.")

    # FOUR SLOTS, SIX MENTIONS. The four hydration points are the two popover
    # headings, the "What Atlas Knows" panel and the masthead. The other two
    # mentions are the hydrator's own: its querySelectorAll and the comment
    # above it. Counting mentions rather than slots is why this number is 6.
    if src.count('pn-atlas-slot') != 6:
        die("expected 6 .pn-atlas-slot mentions — 4 slots (2 popover, 1 panel, "
            "1 masthead) plus the hydrator's selector and its comment; found "
            "%d. Nothing written." % src.count('pn-atlas-slot'))

    if src == before:
        die("no change produced; refusing to claim a build")

    PAGE.write_text(src, encoding="utf-8")
    print("WROTE " + str(PAGE))
    print("  %d bytes -> %d bytes (%+d)"
          % (len(before.encode()), len(src.encode()),
             len(src.encode()) - len(before.encode())))
    print("  8 anchored edits, each matched exactly once")
    print("  masthead lockup at 60x54; alternatives and maker-band marks removed")
    print("  evidence gate, micro signature, Phase 1 placements, geometry: verified unchanged")


if __name__ == "__main__":
    build()
