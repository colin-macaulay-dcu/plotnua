#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PlotNua — build-ah-card-media-box.py

ONE MEASURED CORRECTION. On the Additional Home grid the four plates
measured [350, 350, 350, 700]: three of the four buildings carry no
authorised photograph, so their media well collapses, and the one that
does carries a 2000x2500 PORTRAIT image.

The gallery media already DECLARES `aspect-ratio:4/3` and the image
already declares `object-fit:cover`, so a fixed 4/3 frame with the
photograph cropped into it is the shape the stylesheet was written for.
It does not happen because the <img> is in flow at height:auto, so the
image's own 1:1.25 proportion sets the box and the declared ratio never
applies. Giving the image the height of its frame realises the ratio
already declared. No new number is introduced.

SCOPE. The selector hangs off `#matchPrimary[data-pn-verdict]`, which is
set ONLY by the residential verdict hero. Garden Room never sets it, so
Garden Room's gallery is untouched — the builder proves this by refusing
if the attribute scope is missing from the rule.

Usage: python3 atlas-tools/build-ah-card-media-box.py [--check|--revert]
"""

import hashlib, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "your-plot.html")
BAK = PAGE + ".bak-cardmedia"
BASELINE = "26e6450ca0567630"

FIND = """  #screen-match-results #altResults > *{ height:100%; }
"""

REPL = """  #screen-match-results #altResults > *{ height:100%; }
  /* M1 - THE PLATE HOLDS THE PHOTOGRAPH; THE PHOTOGRAPH DOES NOT SET THE
     PLATE. Measured on the rendered page: card heights [350,350,350,700].
     Three buildings have no authorised photograph so their media well
     collapses; the fourth has a 2000x2500 portrait, and because the image
     sits in flow at automatic height it overrides the 4/3 frame the
     stylesheet already declares and doubles its plate. The image is given
     the height of the frame it was always meant to fill, and object-fit
     (already declared) crops it. Scoped to the residential verdict hero's
     siblings, so the Garden Room gallery is not reached. */
  #screen-match-results #matchPrimary[data-pn-verdict] ~ #altResults
    .results-gallery-media{ overflow:hidden; }
  #screen-match-results #matchPrimary[data-pn-verdict] ~ #altResults
    .results-gallery-media > img{
    position:absolute; inset:0; width:100%; height:100%; display:block;
  }
"""

SCOPE = '#matchPrimary[data-pn-verdict] ~ #altResults'


def sha16(s): return hashlib.sha256(s.encode()).hexdigest()[:16]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    if mode == "--revert":
        if not os.path.exists(BAK): raise SystemExit("no backup")
        open(PAGE, "w", encoding="utf-8").write(open(BAK, encoding="utf-8").read())
        print("reverted."); return

    src = open(PAGE, encoding="utf-8").read()
    base = sha16(src)
    if base != BASELINE and not os.path.exists(BAK):
        raise SystemExit("REFUSED: baseline %s, expected %s" % (base, BASELINE))

    if src.count(FIND) != 1:
        raise SystemExit("REFUSED: anchor matched %d" % src.count(FIND))
    out = src.replace(FIND, REPL, 1)

    # Every ADDED selector line must carry the residential scope.
    added = [l for l in REPL.splitlines() if l not in FIND.splitlines()]
    sel_lines = [l for l in added
                 if ("{" in l or l.strip().startswith(".results-gallery-media"))
                 and not l.strip().startswith("/*") and "- " not in l]
    blocks = REPL.split("*/", 1)[1]
    for rule in [r for r in blocks.split("}") if r.strip()]:
        if SCOPE not in rule.replace("\n", " ").replace("    ", " ").replace("  ", " ").replace(" ~ ", " ~ "):
            # normalise whitespace before testing
            flat = re.sub(r"\s+", " ", rule)
            if SCOPE not in flat:
                raise SystemExit("REFUSED: an added rule is not scoped to the "
                                 "residential verdict hero:\n%s" % rule.strip())

    # Nothing outside the <style> block may change.
    if out.count("<style") != src.count("<style"):
        raise SystemExit("REFUSED: style block count changed")
    before_style = src.split("</style>")[-1]
    if out.split("</style>")[-1] != before_style:
        raise SystemExit("REFUSED: content after the last </style> changed")

    # No JavaScript may change at all.
    js_src = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", src, re.S)
    js_out = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", out, re.S)
    if js_src != js_out:
        raise SystemExit("REFUSED: this is a CSS-only change; script changed")

    if mode == "--check":
        print("CHECK ONLY. %s -> %s, +%d lines, CSS only, scoped"
              % (base, sha16(out), out.count("\n") - src.count("\n")))
        return

    if not os.path.exists(BAK):
        open(BAK, "w", encoding="utf-8").write(src)
    open(PAGE, "w", encoding="utf-8").write(out)
    print("applied. %s -> %s" % (base, sha16(out)))


if __name__ == "__main__":
    main()
