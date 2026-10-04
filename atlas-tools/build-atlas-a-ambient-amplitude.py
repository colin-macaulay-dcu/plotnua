#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER: make the ambient drift visible without making it move fast.

THE OBSERVATION, AND THE ARITHMETIC BEHIND IT. The founder saw the repaired
lockup render and reported the drift as imperceptible. Measured, he is right:

    transform-box is fill-box, so a percentage translate resolves against each
    GROUP's own box, not against the 60px viewport.

      dark field box on screen   59.74 x 53.73 px
      sage field box on screen   45.17 x 49.11 px

    at the old +-0.7% / +-0.4%:
      dark  -0.42 px X, +0.21 px Y
      sage  +0.32 px X, -0.20 px Y

Sub-pixel travel over nine seconds is not slow motion, it is no motion. A
browser cannot even render it as movement; it renders it as a static mark.

THE NEW AMPLITUDE, and what it actually travels:

      dark   translate(-2.5%, 1.5%)  scale(1.018)
             -> -1.49 px X, +0.81 px Y   (1.70 px excursion, +0.54 px per edge)
      sage   translate(2.5%, -1.5%)  scale(0.985)
             -> +1.13 px X, -0.74 px Y   (1.35 px excursion, -0.34 px per edge)

      relative separation at the extremes: 2.62 px X, 1.54 px Y, 3.04 px diagonal

NOTE THE TWO FIELDS DO NOT TRAVEL EQUALLY, and that is a consequence of
fill-box, not a mistake: the sage box is smaller, so the same percentage is
fewer pixels. The opposition is what reads, and 3 px of relative separation
across 9 and 11 seconds is perceptible without being fast -- roughly a third of
a pixel per second.

WHAT IS UNCHANGED. The 9s and 11s periods, ease-in-out, alternate infinite, the
60x54 box, the lockup layout, the fixed house, reduced-motion behaviour, and
every other Atlas placement. Only the six numbers in the two ambient keyframes
move. No rotation, orbit, bounce, opacity, shadow or filter is introduced --
the keyframes still contain nothing but translate and scale.

Anchored. Two edits, each must match exactly once or the builder refuses.
"""

import pathlib
import re
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


DARK_OLD = """  @keyframes pn-atlas-a-drift-dark{
    from{ transform:translate(0,0) scale(1) }
    to{ transform:translate(-0.7%,0.4%) scale(1.006) }
  }
"""

DARK_NEW = """  @keyframes pn-atlas-a-drift-dark{
    from{ transform:translate(0,0) scale(1) }
    to{ transform:translate(-2.5%,1.5%) scale(1.018) }
  }
"""

SAGE_OLD = """  @keyframes pn-atlas-a-drift-sage{
    from{ transform:translate(0,0) scale(1) }
    to{ transform:translate(0.7%,-0.4%) scale(0.996) }
  }
"""

SAGE_NEW = """  @keyframes pn-atlas-a-drift-sage{
    from{ transform:translate(0,0) scale(1) }
    to{ transform:translate(2.5%,-1.5%) scale(0.985) }
  }
"""

# The comment above the ambient rules quotes the old amplitude, so it has to be
# corrected too or the file documents a figure it no longer uses.
NOTE_OLD = """                                             loading indicator.
"""

NOTE_NEW = """                                             loading indicator. Measured at
                                             60x54: dark travels 1.49px X and
                                             0.81px Y, sage 1.13px X and
                                             0.74px Y the other way, so the two
                                             fields separate by about 3px over
                                             nine and eleven seconds. The
                                             earlier +-0.7% was sub-pixel and
                                             read as static -- percentages
                                             resolve against each GROUP's
                                             fill-box, not the 60px viewport,
                                             which is also why the smaller sage
                                             box travels less at the same
                                             percentage.
"""


def build():
    if not PAGE.exists():
        die("your-plot.html not found at " + str(PAGE))

    before = PAGE.read_text(encoding="utf-8")

    if "translate(-2.5%,1.5%)" in before:
        die("the page already carries the wider amplitude; this builder has "
            "already been applied. Nothing written.")

    src = before
    src = anchored(src, DARK_OLD, DARK_NEW, "1/3 dark keyframes")
    src = anchored(src, SAGE_OLD, SAGE_NEW, "2/3 sage keyframes")
    src = anchored(src, NOTE_OLD, NOTE_NEW, "3/3 contract note amplitude")

    # THE KEYFRAMES MUST STILL CONTAIN NOTHING BUT TRANSLATE AND SCALE.
    for name in ("pn-atlas-a-drift-dark", "pn-atlas-a-drift-sage"):
        kf = re.search(r"@keyframes " + name + r"\{([\s\S]*?)\n  \}", src)
        if not kf:
            die("could not read @keyframes " + name + ". Nothing written.")
        body = kf.group(1)
        banned = [w for w in ("opacity", "rotate", "filter", "box-shadow", "skew",
                              "perspective", "matrix") if w in body]
        if banned:
            die(name + " would animate " + ", ".join(banned) + ". Nothing written.")
        # And the amplitude must stay inside the newly approved envelope.
        m = re.search(r"translate\((-?[\d.]+)%,(-?[\d.]+)%\)\s*scale\(([\d.]+)\)", body)
        if not m:
            die("could not parse the end state of " + name + ". Nothing written.")
        x, y, sc = float(m.group(1)), float(m.group(2)), float(m.group(3))
        if abs(x) > 2.6 or abs(y) > 1.6 or abs(sc - 1) > 0.020:
            die("%s exceeds the approved envelope: %s%%, %s%%, %s. Nothing written."
                % (name, x, y, sc))

    # TIMING, DIRECTION AND SCOPE MUST BE UNTOUCHED.
    for keep, what in [
        ('animation-duration:620ms, 9s;', 'the 9s dark period'),
        ('animation-duration:620ms, 11s;', 'the 11s sage period'),
        ('animation-direction:normal, alternate;', 'alternate direction'),
        ('animation-iteration-count:1, infinite;', 'settle once, drift forever'),
        ('animation-timing-function:cubic-bezier(.2,.75,.25,1), ease-in-out;', 'ease-in-out'),
        ('.pn-atlas-mark--60.pn-am-play .pn-am-dark{', 'the dark rule scope'),
        ('.pn-atlas-mark--60.pn-am-play .pn-am-sage{', 'the sage rule scope'),
        ('.pn-atlas-mark--60{ width:60px; height:54px; }', 'the 60x54 box'),
        ('@media (prefers-reduced-motion: reduce){', 'reduced motion'),
        ('.pn-atlas-a .pn-am-field{ animation:none !important; }', 'the reduced-motion rule'),
        ('@media (max-width:360px){', 'the responsive stack'),
        ("mastMark.setAttribute('data-atlas-size', '60')", 'the masthead placement'),
        ('function template(){', 'the lazy template resolution'),
        ("if (row.state === 'established' && !row.scope && !row.conflict){", 'the evidence gate'),
        ('viewBox="0 0 1157 1038"', 'the supplied viewBox'),
        ('id="pn-atlas-a-template"', 'the single template'),
    ]:
        if src.count(keep) != before.count(keep):
            die("something other than the amplitude changed: " + what
                + ". Nothing written.")

    # NO OTHER PLACEMENT MAY HAVE GAINED MOTION.
    styles = "".join(re.findall(r"<style[^>]*>(.*?)</style>", src, re.S))
    rules = re.sub(r"/\*[\s\S]*?\*/", "", styles)
    for block in rules.split("}"):
        if "pn-atlas-a-drift" not in block:
            continue
        sel = (block.split("{")[0] or "").strip().split("\n")[-1].strip()
        if "pn-atlas-mark--60" not in sel and not sel.startswith("@keyframes"):
            die("drift is referenced by %r, which is not the 60px lockup. "
                "Nothing written." % sel)

    if src == before:
        die("no change produced; refusing to claim a build")

    PAGE.write_text(src, encoding="utf-8")
    print("WROTE " + str(PAGE))
    print("  %d bytes -> %d bytes (+%d)"
          % (len(before.encode()), len(src.encode()),
             len(src.encode()) - len(before.encode())))
    print("  3 anchored edits; amplitude widened, timing and scope untouched")
    print("  dark -2.5%/+1.5% scale 1.018 | sage +2.5%/-1.5% scale 0.985")


if __name__ == "__main__":
    build()
