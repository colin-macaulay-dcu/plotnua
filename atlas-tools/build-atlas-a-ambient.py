#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER: ambient field motion on the primary lockup, and a deliberate
masthead stack under 360px.

TWO THINGS, BOTH NARROW.

A. THE MASTHEAD STACKS ON PURPOSE UNDER 360px. .aa-mast is flex-wrap:wrap, so a
   long organisation name already dropped to a second line -- by accident, left
   wherever space-between happened to leave it. Under 360px it now stacks
   deliberately: the lockup and its label stay together on line one, the
   organisation sits on line two aligned to the masthead's own left edge, with
   10px above it. The lockup stays 60 x 54. Nothing else in the spread moves.

B. THE PRIMARY LOCKUP GAINS CONTINUOUS AMBIENT FIELD MOTION, and it is the ONLY
   placement that may. This is an explicit amendment to the supplied motion
   contract, which said no endless pulse and which the proof enforced by banning
   the words infinite and alternate outright. That ban now holds everywhere
   except .pn-atlas-mark--60.

       dark field   9s   ease-in-out  alternate infinite
                    translate(-0.7%, 0.4%)  scale(1.006)
       sage field  11s   ease-in-out  alternate infinite
                    translate(0.7%, -0.4%)  scale(0.996)

   Opposing directions, so the field reads as breathing rather than sliding.
   9 and 11 are co-prime: the two cycles re-align only every 99 seconds, so
   there is no beat and no visible reset. alternate means each field eases to
   its extreme and back, so no frame ever snaps.

   NO opacity in the ambient keyframes. The entrance settle owns opacity and
   ends at 1 with fill-mode both; the ambient animation touches transform only,
   so nothing pulses in brightness.

THE HOUSE CANNOT MOVE, AND NOW BY TWO MECHANISMS. The hydrator strips its id and
gives it no class, so no selector can reach it; and no rule anywhere names it.
Kept fixed by omission, as before, which is the form that cannot be edited away
by accident.

WHY THE HYDRATOR HAD TO CHANGE. Both field groups were given the same class,
.pn-am-field, so after hydration CSS could not tell the dark field from the sage
field -- opposing drift was not expressible. Each group now also gets
.pn-am-dark or .pn-am-sage. That is the whole change: one extra class per group,
derived from the id that is about to be stripped.

COMPOSITION WITH THE ENTRANCE SETTLE. Both animations run on the same element as
a comma list. The settle keeps its 620ms, its per-group delay and
iteration-count 1; the ambient starts after it finishes (1000ms / 1150ms against
settle ends of 710ms / 860ms), so the handoff happens at translate(0,0)
scale(1), which is exactly where the settle lands. No jump.

REDUCED MOTION is unchanged and still one rule with !important on
.pn-atlas-a .pn-am-field, which covers the lockup too -- so it removes BOTH the
entrance and the ambient animation and lands on the authored static state
immediately.

NO GEOMETRY CHANGES. No file in assets/brand/ is read or written.

Anchored. Four edits, each must match exactly once or the builder refuses and
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


# ------------------------------------------------- 1 . the motion contract
CONTRACT_OLD = """  /* ATLAS A MOTION — the 24px and 20px headings only.

     The supplied motion contract, implemented literally:
       #atlas-house stays stable          -- it carries NO animation
                                             rule at all, so it cannot
                                             move by accident.
       the field gathers and settles      -- the two field groups fade
                                             and scale in, once.
       no spin, orbit, loading-dot,       -- only opacity and a scale
       bounce or endless pulse               that ends at 1. Nothing
                                             turns, travels or repeats;
                                             the builder refuses any
                                             looping keyword in here.
       reduced motion                     -- animation removed entirely,
                                             which lands on the artwork's
                                             own authored state.
       16px micro                         -- an <img>, never in here.
"""

CONTRACT_NEW = """  /* ATLAS A MOTION — the hydrated placements, with ONE amendment.

     THE AMENDMENT, stated before the rules it changes. The supplied contract
     said no endless pulse, and this block enforced it by banning the looping
     keywords outright. That ban is now ABSOLUTE FOR EVERY ATLAS PLACEMENT
     EXCEPT ONE: the primary 60 x 54 ATLAS ASSESSMENT lockup, which alone may
     carry continuous ambient field motion. The 24px popover marks, the 20px
     panel mark, the 16px evidence-row micro signature and any future
     placement remain play-once. Nothing inherits the loop: the ambient rules
     are selector-scoped to .pn-atlas-mark--60 and cannot reach anything else.

     The supplied motion contract, otherwise implemented literally:
       #atlas-house stays stable          -- it carries NO animation rule at
                                             all AND the hydrator gives it no
                                             class, so no selector can reach
                                             it. Fixed by omission, twice.
       the field gathers and settles      -- the two field groups fade and
                                             scale in, once, everywhere.
       ambient drift, LOCKUP ONLY         -- the two fields then breathe in
                                             opposition, 9s and 11s, ease-in-
                                             out, alternate. Co-prime periods,
                                             so they re-align only every 99s
                                             and there is no beat or reset.
                                             Transform only: <=0.7% translate
                                             and <=0.6% scale. No opacity, so
                                             nothing pulses in brightness.
       no spin, orbit, loading-dot        -- still none, anywhere. The drift
       or bounce                             travels under one percent and
                                             eases both ways; it is not a
                                             loading indicator.
       reduced motion                     -- one !important rule removes BOTH
                                             the entrance and the ambient
                                             animation, landing on the
                                             artwork's authored static state
                                             immediately.
       16px micro                         -- an <img>, never in here.
"""

# ----------------------------------------- 2 . the ambient rules + keyframes
AMBIENT_OLD = """  @keyframes pn-atlas-a-settle{
    from{ opacity:0; transform:scale(.90) }
    to{ opacity:1; transform:scale(1) }
  }
"""

AMBIENT_NEW = """  @keyframes pn-atlas-a-settle{
    from{ opacity:0; transform:scale(.90) }
    to{ opacity:1; transform:scale(1) }
  }

  /* AMBIENT FIELD DRIFT — .pn-atlas-mark--60 AND NOTHING ELSE.

     Two animations per group as a comma list: the entrance settle keeps its
     620ms and its iteration-count 1, and the ambient begins after the settle
     has landed (1000ms and 1150ms against settle ends of 710ms and 860ms), so
     the handoff happens at translate(0,0) scale(1) — exactly where the settle
     finishes. Nothing jumps.

     The two periods are co-prime on purpose. Equal periods would breathe in
     lockstep and the turn would read as a beat; 9 and 11 re-align only every
     99 seconds. */
  .pn-atlas-mark--60.pn-am-play .pn-am-dark{
    animation-name:pn-atlas-a-settle, pn-atlas-a-drift-dark;
    animation-duration:620ms, 9s;
    animation-delay:var(--pn-am-d,0ms), 1000ms;
    animation-timing-function:cubic-bezier(.2,.75,.25,1), ease-in-out;
    animation-iteration-count:1, infinite;
    animation-direction:normal, alternate;
    animation-fill-mode:both, none;
  }
  .pn-atlas-mark--60.pn-am-play .pn-am-sage{
    animation-name:pn-atlas-a-settle, pn-atlas-a-drift-sage;
    animation-duration:620ms, 11s;
    animation-delay:var(--pn-am-d,0ms), 1150ms;
    animation-timing-function:cubic-bezier(.2,.75,.25,1), ease-in-out;
    animation-iteration-count:1, infinite;
    animation-direction:normal, alternate;
    animation-fill-mode:both, none;
  }
  /* Transform only. No opacity, no filter, no shadow, no rotation. */
  @keyframes pn-atlas-a-drift-dark{
    from{ transform:translate(0,0) scale(1) }
    to{ transform:translate(-0.7%,0.4%) scale(1.006) }
  }
  @keyframes pn-atlas-a-drift-sage{
    from{ transform:translate(0,0) scale(1) }
    to{ transform:translate(0.7%,-0.4%) scale(0.996) }
  }
"""

# ----------------------------------------------- 3 . the hydrator classes
HYD_OLD = """    Object.keys(DELAYS).forEach(function(id){
      var g = svg.querySelector("#" + id);
      if (!g) return;
      g.removeAttribute("id");   /* ids must stay unique in the page */
      g.classList.add("pn-am-field");
      g.style.setProperty("--pn-am-d", DELAYS[id] + "ms");
    });
"""

HYD_NEW = """    Object.keys(DELAYS).forEach(function(id){
      var g = svg.querySelector("#" + id);
      if (!g) return;
      g.removeAttribute("id");   /* ids must stay unique in the page */
      g.classList.add("pn-am-field");
      /* AND WHICH FIELD IT IS. Both groups used to get only .pn-am-field, so
         after hydration CSS could not tell them apart and the opposing ambient
         drift was not expressible. Derived from the id immediately before it
         is stripped. #atlas-house is not in DELAYS, so it gets neither class
         and no selector can reach it. */
      g.classList.add(id === "atlas-dark-field" ? "pn-am-dark" : "pn-am-sage");
      g.style.setProperty("--pn-am-d", DELAYS[id] + "ms");
    });
"""

# --------------------------------------- 4 . the deliberate stack under 360px
STACK_OLD = """  .aa-mast-lead{ display:flex; align-items:center; gap:16px; }
"""

STACK_NEW = """  .aa-mast-lead{ display:flex; align-items:center; gap:16px; }
  /* UNDER 360px THE MASTHEAD STACKS ON PURPOSE. .aa-mast is flex-wrap:wrap, so
     a long organisation name already dropped to a second line -- but left
     wherever justify-content:space-between happened to put it. Blocking the
     masthead puts the organisation on its own line, aligned to the masthead's
     own left edge, with modest space above. The lockup is untouched: still
     60 x 54, still beside its label. No other assessment rule changes. */
  @media (max-width:360px){
    .aa-mast{ display:block; }
    .aa-mast-r{ display:block; margin-top:10px; }
  }
"""


def build():
    if not PAGE.exists():
        die("your-plot.html not found at " + str(PAGE))

    before = PAGE.read_text(encoding="utf-8")

    if "pn-atlas-a-drift-dark" in before:
        die("the page already carries the ambient keyframes; this builder has "
            "already been applied. Nothing written.")

    src = before
    src = anchored(src, CONTRACT_OLD, CONTRACT_NEW, "1/4 motion contract amendment")
    src = anchored(src, AMBIENT_OLD, AMBIENT_NEW, "2/4 ambient rules and keyframes")
    src = anchored(src, HYD_OLD, HYD_NEW, "3/4 hydrator field classes")
    src = anchored(src, STACK_OLD, STACK_NEW, "4/4 deliberate stack under 360px")

    # THE HOUSE. No STYLESHEET rule may name it. Scoped to the <style> blocks:
    # the hydrator legitimately calls querySelector("#atlas-house") in order to
    # strip that id, and a check that swept the JS too would refuse on the very
    # line that keeps the house safe.
    import re as _re
    styles = "".join(_re.findall(r"<style[^>]*>(.*?)</style>", src, _re.S))
    styles_no_comments = _re.sub(r"/\*.*?\*/", "", styles, flags=_re.S)
    if "#atlas-house" in styles_no_comments or "pn-am-house" in styles_no_comments:
        die("a stylesheet rule now names the house. Nothing written.")
    if 'h.removeAttribute("id")' not in src:
        die("the hydrator no longer strips the house id. Nothing written.")
    if 'classList.add("pn-am-field")' not in src:
        die("the hydrator no longer tags the field groups. Nothing written.")

    # THE LOOP MUST BE SCOPED. Every looping keyword must sit inside a
    # .pn-atlas-mark--60 rule, never in a rule that could reach another mark.
    css = src[src.index("/* ATLAS A MOTION"):src.index("@media (prefers-reduced-motion")]
    rules = __import__("re").sub(r"/\*.*?\*/", "", css, flags=16)  # 16 = DOTALL
    for word in ("infinite", "alternate"):
        for line in rules.splitlines():
            if word in line:
                # walk back to the selector this declaration belongs to
                idx = rules.index(line)
                head = rules[:idx]
                sel = head.rsplit("{", 1)[0].rsplit("}", 1)[-1].strip()
                if "pn-atlas-mark--60" not in sel:
                    die("'%s' appears under selector %r, which is not scoped to "
                        "the 60px lockup. Nothing written." % (word, sel))

    # NOTHING ELSE MAY HAVE MOVED.
    for keep, what in [
        ('<span class="pn-atlas-slot" data-atlas-size="24"></span>', 'the 24px popover slots'),
        ("akMark.setAttribute('data-atlas-size', '20')", 'the 20px panel slot'),
        ("am.src = 'assets/brand/atlas-mark-micro.svg'", 'the gated micro signature'),
        ("if (row.state === 'established' && !row.scope && !row.conflict){", 'the evidence gate'),
        ('.pn-atlas-mark--60{ width:60px; height:54px; }', 'the aspect-correct lockup box'),
        ("mastMark.setAttribute('data-atlas-size', '60')", 'the masthead placement'),
        ('id="pn-atlas-a-template"', 'the single inlined template'),
        ('viewBox="0 0 1157 1038"', 'the supplied viewBox'),
        ('.pn-atlas-a .pn-am-field{ animation:none !important; }', 'the reduced-motion rule'),
    ]:
        if src.count(keep) != before.count(keep):
            die("something unrelated changed: " + what + ". Nothing written.")

    if src == before:
        die("no change produced; refusing to claim a build")

    PAGE.write_text(src, encoding="utf-8")
    print("WROTE " + str(PAGE))
    print("  %d bytes -> %d bytes (+%d)"
          % (len(before.encode()), len(src.encode()),
             len(src.encode()) - len(before.encode())))
    print("  4 anchored edits, each matched exactly once")
    print("  ambient drift scoped to .pn-atlas-mark--60; house unreachable; "
          "stack added under 360px")


if __name__ == "__main__":
    build()
