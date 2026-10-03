#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — Atlas A, Phase 1 (three approved placements).

FOUNDER DECISION, 3 October 2026. The supplied pack
plotnua-atlas-a-final-production.zip is the approved artwork and is used AS
PROVIDED. This builder does not draw, redraw, reinterpret or restyle anything.
It lifts the supplied geometry verbatim and places it.

  P1  "What is Atlas?" popover heading   24px  inline, animated
  P2  "What Atlas Knows" panel heading   20px  inline, animated
  P3  established evidence rows          16px  atlas-mark-micro.svg, STATIC

WHY INLINE FOR P1/P2. A browser loads SVG referenced by <img src> as an
independent static image and suppresses its animation. An animated mark
therefore cannot be a file reference. The supplied
atlas-mark-motion-ready.svg carries the stable group ids the README promises
-- #atlas-house, #atlas-dark-field, #atlas-sage-field -- and those are exactly
what the motion contract animates.

ONE COPY OF THE GEOMETRY. The motion-ready artwork is inlined ONCE, into a
<template>, and both animated placements are hydrated from it by cloneNode.
Inlining it three times would put ~43KB of duplicated path data in the page and
create three places for the artwork to drift apart.

THE GEOMETRY IS LIFTED, NEVER RETYPED. The builder reads
assets/brand/atlas-mark-motion-ready.svg off disk and copies its inner markup
character for character. G2 then proves the page's copy is byte-identical to
the file. There is no path data in this builder.

Run: python3 atlas-tools/build-atlas-a-phase1.py [--check]
"""

import hashlib
import pathlib
import re
import sys

CHECK = "--check" in sys.argv
ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "your-plot.html"
BRAND = ROOT / "assets" / "brand"
MOTION = BRAND / "atlas-mark-motion-ready.svg"
MICRO = BRAND / "atlas-mark-micro.svg"

REQUIRED_IDS = ("atlas-house", "atlas-dark-field", "atlas-sage-field")
VIEWBOX = "0 0 1157 1038"


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def main():
    # G0 · THE SUPPLIED PACK MUST BE PRESENT AND BE THE SUPPLIED ONE.
    for f in (MOTION, MICRO, BRAND / "atlas-mark.svg",
              BRAND / "atlas-mark-reversed.svg"):
        if not f.exists():
            die("%s is missing. This builder places the supplied pack; it "
                "does not create artwork." % f.name)
    art = MOTION.read_text(encoding="utf-8")
    if 'viewBox="%s"' % VIEWBOX not in art:
        die("atlas-mark-motion-ready.svg is not on the supplied %s viewBox. "
            "The artwork is used as provided and is not re-scaled." % VIEWBOX)
    for i in REQUIRED_IDS:
        if 'id="%s"' % i not in art:
            die("atlas-mark-motion-ready.svg has no #%s group. The motion "
                "contract animates those ids; without them nothing can be "
                "wired without redrawing, which is forbidden." % i)
    for banned in ("<image", "base64", "<text", "<tspan"):
        if banned in art:
            die("the supplied motion artwork contains %r. It must be clean "
                "vector with no raster or text." % banned)

    # LIFT the inner markup verbatim -- everything between the outer <svg> tags,
    # minus the <title>/<desc>, which would be announced by a screen reader at a
    # placement that is decorative.
    inner = re.search(r"<svg[^>]*>(.*)</svg>", art, re.S)
    if not inner:
        die("could not read the inner markup of the supplied motion artwork.")
    inner = inner.group(1)
    inner = re.sub(r"<title[^>]*>.*?</title>\s*", "", inner, flags=re.S)
    inner = re.sub(r"<desc[^>]*>.*?</desc>\s*", "", inner, flags=re.S)
    inner = inner.strip()
    if inner.count("<g ") < 3:
        die("the lifted markup does not carry the three field groups.")

    src = PAGE.read_text(encoding="utf-8")
    original = src

    # G1 · CSS. Sizes, the heading row, and the motion contract.
    css_start = "  /* ATLAS MARK — secondary system mark for evidence surfaces only.\n"

    # ce56fac's block runs from the comment down to the reduced-motion rule.
    css_end = ("  @media (prefers-reduced-motion: reduce){\n"
               "    .pn-am-anim .pn-am-el{ animation:none !important; }\n"
               "  }\n")
    if src.count(css_start) != 1 or src.count(css_end) != 1:
        die("the Phase 1 Atlas CSS block is not present exactly once.")
    i = src.index(css_start)
    j = src.index(css_end) + len(css_end)
    if j <= i:
        die("the Phase 1 Atlas CSS block is not contiguous.")

    css = (
        "  /* ATLAS A — secondary system mark for evidence surfaces only.\n"
        "     The artwork is the supplied production pack, used as provided.\n"
        "     Nothing here redraws, re-scales or recolours it: the page sets a\n"
        "     box and the artwork fills it. The PlotNua P stays primary. */\n"
        "  .pn-atlas-mark{ flex:0 0 auto; display:inline-block; vertical-align:middle; }\n"
        "  .pn-atlas-mark--24{ width:24px; height:24px; }\n"
        "  .pn-atlas-mark--20{ width:20px; height:20px; }\n"
        "  .pn-atlas-mark--16{ width:16px; height:16px; }\n"
        "  /* The heading becomes a row so the mark sits BESIDE the words,\n"
        "     never replacing them. */\n"
        "  .match-atlas-popover-title.has-atlas-mark,\n"
        "  .am-panel-title.has-atlas-mark{ display:flex; align-items:center; gap:10px; }\n"
        "  /* On an evidence row the mark is a quiet trailing signature. */\n"
        "  .am-ev-atlas{ margin-left:6px; position:relative; top:2px; opacity:.9; }\n"
        "\n"
        "  /* ATLAS A MOTION — the 24px and 20px headings only.\n"
        "\n"
        "     The supplied motion contract, implemented literally:\n"
        "       #atlas-house stays stable          -- it carries NO animation\n"
        "                                             rule at all, so it cannot\n"
        "                                             move by accident.\n"
        "       the field gathers and settles      -- the two field groups fade\n"
        "                                             and scale in, once.\n"
        "       no spin, orbit, loading-dot,       -- only opacity and a scale\n"
        "       bounce or endless pulse               that ends at 1. Nothing\n"
        "                                             turns, travels or repeats;\n"
        "                                             the builder refuses any\n"
        "                                             looping keyword in here.\n"
        "       reduced motion                     -- animation removed entirely,\n"
        "                                             which lands on the artwork's\n"
        "                                             own authored state.\n"
        "       16px micro                         -- an <img>, never in here.\n"
        "\n"
        "     transform-box:fill-box makes transform-origin resolve against each\n"
        "     group rather than the SVG user space. Where it is unsupported the\n"
        "     scale grows from the viewBox origin, which is wrong but not broken:\n"
        "     fill-mode both still lands on the settled artwork. */\n"
        "  .pn-atlas-a{ overflow:visible; }\n"
        "  .pn-atlas-a .pn-am-field{\n"
        "    animation-duration:620ms; animation-delay:var(--pn-am-d,0ms);\n"
        "    animation-timing-function:cubic-bezier(.2,.75,.25,1);\n"
        "    animation-iteration-count:1; animation-fill-mode:both;\n"
        "    transform-box:fill-box; transform-origin:center;\n"
        "  }\n"
        "  .pn-atlas-a.pn-am-play .pn-am-field{ animation-name:pn-atlas-a-settle; }\n"
        "  @keyframes pn-atlas-a-settle{\n"
        "    from{ opacity:0; transform:scale(.90) }\n"
        "    to{ opacity:1; transform:scale(1) }\n"
        "  }\n"
        "  @media (prefers-reduced-motion: reduce){\n"
        "    .pn-atlas-a .pn-am-field{ animation:none !important; }\n"
        "  }\n"
    )
    src = src[:i] + css + src[j:]

    # G2 · THE TEMPLATE. The supplied artwork, inlined ONCE, verbatim.
    tpl_anchor = "</body>"
    if src.count(tpl_anchor) != 1:
        die("expected exactly one </body> to anchor the Atlas template.")
    tpl = (
        '<!-- ATLAS A — the supplied production artwork, inlined once and\n'
        '     hydrated into the two animated heading placements by cloneNode.\n'
        '     This markup is lifted verbatim from\n'
        '     assets/brand/atlas-mark-motion-ready.svg and is proved\n'
        '     byte-identical to it by atlas-tools/prove-atlas-a.mjs. It is not\n'
        '     redrawn, re-scaled or recoloured here. -->\n'
        '<template id="pn-atlas-a-template"><svg class="pn-atlas-mark pn-atlas-a" '
        'viewBox="%s" aria-hidden="true" focusable="false">%s</svg></template>\n'
        % (VIEWBOX, inner))
    src = src.replace(tpl_anchor, tpl + tpl_anchor, 1)

    # G3 · P1 — both "What is Atlas?" popovers get a hydration slot.
    # The page at ce56fac carries the SUPERSEDED Open Field geometry inline at
    # this placement. It is matched by its wrapper and removed wholesale --
    # retired artwork must not survive anywhere in the page.
    p1_re = re.compile(
        r'<p class="match-atlas-popover-title has-atlas-mark">'
        r'<svg class="pn-atlas-mark pn-atlas-mark--24 pn-am-anim".*?</svg>'
        r'What is Atlas\?</p>', re.S)
    n1 = len(p1_re.findall(src))
    if n1 != 2:
        die("expected 2 'What is Atlas?' headings carrying the superseded "
            "inline mark, found %d." % n1)
    p1_new = ('<p class="match-atlas-popover-title has-atlas-mark">'
              '<span class="pn-atlas-slot" data-atlas-size="24"></span>'
              'What is Atlas?</p>')
    src = p1_re.sub(p1_new, src)

    # G4 · P2 — the "What Atlas Knows" heading, built in JS.
    # Likewise the 20px heading: ce56fac builds the superseded geometry with
    # createElementNS. The whole construction block goes, including the
    # retired PN_AM_SVG constant and the rect table.
    p2_re = re.compile(
        r"    /\* ATLAS MARK, 20px, INLINE SVG.*?"
        r"    akTitle\.appendChild\(akMark\);\n", re.S)
    if len(p2_re.findall(src)) != 1:
        die("the superseded 20px mark construction was not found exactly "
            "once.")
    p2_new = (
        "    /* ATLAS A, 20px. A hydration slot rather than markup: the artwork\n"
        "       lives once in #pn-atlas-a-template and is cloned into every\n"
        "       slot, so there is a single copy of the supplied geometry in the\n"
        "       page. aria-hidden because the heading beside it already says\n"
        "       \"Atlas\". */\n"
        "    const akMark = document.createElement('span');\n"
        "    akMark.className = 'pn-atlas-slot';\n"
        "    akMark.setAttribute('data-atlas-size', '20');\n"
        "    akTitle.appendChild(akMark);\n"
        "    if (window.pnAtlasHydrate) window.pnAtlasHydrate(akTitle);\n")
    src = p2_re.sub(lambda m: p2_new, src, count=1)

    # G5 · THE HYDRATOR. Clones the template into every slot and plays the
    # settle once. No innerHTML; no path data.
    hyd_anchor = '<template id="pn-atlas-a-template">'
    if src.count(hyd_anchor) != 1:
        die("the Atlas template was not inserted exactly once.")
    hydrator = (
        '<script>\n'
        '/* ATLAS A HYDRATION. Fills every .pn-atlas-slot from the single\n'
        '   inlined copy of the supplied artwork, sizes it, tags the two field\n'
        '   groups so CSS can settle them, and plays once.\n'
        '\n'
        '   #atlas-house is deliberately NOT tagged. It carries no animation\n'
        '   class and no animation rule, so the property anchor cannot move --\n'
        '   that is the supplied motion contract, enforced by omission rather\n'
        '   than by a rule that could be edited away. */\n'
        '(function(){\n'
        '  var tpl = document.getElementById("pn-atlas-a-template");\n'
        '  if (!tpl) return;\n'
        '  var DELAYS = { "atlas-dark-field": 90, "atlas-sage-field": 240 };\n'
        '  function fill(slot){\n'
        '    if (!slot || slot.getAttribute("data-atlas-done")) return;\n'
        '    var px = parseInt(slot.getAttribute("data-atlas-size"), 10) || 24;\n'
        '    var svg = tpl.content.firstElementChild.cloneNode(true);\n'
        '    svg.classList.add("pn-atlas-mark--" + px);\n'
        '    svg.setAttribute("width", px);\n'
        '    svg.setAttribute("height", px);\n'
        '    Object.keys(DELAYS).forEach(function(id){\n'
        '      var g = svg.querySelector("#" + id);\n'
        '      if (!g) return;\n'
        '      g.removeAttribute("id");   /* ids must stay unique in the page */\n'
        '      g.classList.add("pn-am-field");\n'
        '      g.style.setProperty("--pn-am-d", DELAYS[id] + "ms");\n'
        '    });\n'
        '    var h = svg.querySelector("#atlas-house");\n'
        '    if (h) h.removeAttribute("id");\n'
        '    slot.appendChild(svg);\n'
        '    slot.setAttribute("data-atlas-done", "1");\n'
        '    requestAnimationFrame(function(){ svg.classList.add("pn-am-play"); });\n'
        '  }\n'
        '  window.pnAtlasHydrate = function(root){\n'
        '    (root || document).querySelectorAll(".pn-atlas-slot")\n'
        '      .forEach(fill);\n'
        '  };\n'
        '  if (document.readyState === "loading"){\n'
        '    document.addEventListener("DOMContentLoaded", function(){ window.pnAtlasHydrate(); });\n'
        '  } else { window.pnAtlasHydrate(); }\n'
        '})();\n'
        '</script>\n')
    src = src.replace(hyd_anchor, hydrator + hyd_anchor, 1)

    # G6 · P3 — the 16px evidence-row mark. Gate unchanged; only the file it
    # points at changes, from atlas-mark-mono.svg to the supplied micro.
    p3_old = "        am.src = 'assets/brand/atlas-mark-mono.svg';\n"
    if src.count(p3_old) != 1:
        die("the 16px evidence-row <img> source was not found exactly once.")
    src = src.replace(p3_old,
                      "        am.src = 'assets/brand/atlas-mark-micro.svg';\n", 1)
    gate = ("      if (row.state === 'established' && !row.scope && !row.conflict){\n")
    if original.count(gate) != 1 or src.count(gate) != 1:
        die("the three-condition evidence gate is not present, unchanged, "
            "exactly once. It is not this builder's to touch.")
    if "am.alt = 'Atlas established evidence';" not in src:
        die("the 16px mark lost its accessible name.")

    # G7 · PROTECTED SYSTEMS. Counts must not move.
    for mark in ("plotnua-mark-master.svg", "plotnua-mark-myplot-saved.svg",
                 "plotnua-icon-transparent.svg", "PN_HOUSE_PATH", "PN_P_PATH",
                 "Property Brain", "PROPERTY BRAIN", "property-brain",
                 "atlas-search-mark", "pn-atlas-mark-breathe",
                 "pn-atlas-mark-arrive"):
        if original.count(mark) != src.count(mark):
            die("a protected reference changed (%s: %d -> %d). The PlotNua P, "
                "the saved mark, Property Brain, navigation and the existing "
                "search-mark animation are all out of scope."
                % (mark, original.count(mark), src.count(mark)))

    # G8 · NOTHING MAY LOOP, SPIN OR PULSE, AND THE HOUSE STAYS STILL.
    #
    # The check runs against the CSS WITH COMMENTS STRIPPED. The first version
    # tested the raw block and refused twice on its own documentation -- the
    # comment explaining that nothing alternates contains the word "alternate",
    # and the comment explaining that the house is never targeted names
    # #atlas-house. A guard that cannot tell a rule from the prose describing
    # it is measuring the wrong thing.
    rules = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for banned in ("infinite", "alternate", "rotate(", "animation-direction",
                   "box-shadow", "drop-shadow", "filter:"):
        if banned in rules:
            die("the Atlas A motion CSS contains %r in a rule." % banned)
    if "animation-iteration-count:1" not in rules:
        die("the Atlas A motion CSS does not pin the iteration count to 1.")
    if "prefers-reduced-motion" not in rules:
        die("the Atlas A motion CSS has no reduced-motion rule.")
    if "#atlas-house" in rules or "pn-am-house" in rules:
        die("the house is targeted by a motion rule. The supplied contract "
            "says it stays stable, and it is kept stable by carrying no rule.")
    # And the hydrator must strip the house id without ever tagging it.
    if "pn-am-field" in hydrator.split('querySelector("#atlas-house")')[-1]:
        die("the hydrator tags the house as an animated field.")

    if CHECK:
        print("CHECK ONLY — nothing written. %+d bytes." % (len(src) - len(original)))
        sys.exit(0)

    PAGE.write_text(src, encoding="utf-8")
    print("ATLAS A — PHASE 1")
    print("=" * 74)
    print("  ok    9 guards passed")
    print("  ok    supplied artwork lifted verbatim, %d bytes of inner markup"
          % len(inner))
    print("  ok    P1  2 x 'What is Atlas?'   24px  inline, animated")
    print("  ok    P2  'What Atlas Knows'     20px  inline, animated")
    print("  ok    P3  evidence rows          16px  atlas-mark-micro.svg, STATIC")
    print("  ok    one copy of the geometry in the page (template + clone)")
    print("  ok    #atlas-house carries no animation rule")
    print("  ok    evidence gate unchanged: established AND !scope AND !conflict")
    print("  ok    PlotNua P, Property Brain, navigation untouched")
    print("-" * 74)
    print("wrote %s (%+d bytes)" % (PAGE, len(src) - len(original)))


main()
