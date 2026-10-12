#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PlotNua — build-ah-card-parity.py

ONE COHERENT GRID. Measured on the rendered page at 1280: the four
Additional Home plates stand at [269, 269, 269, 599]. One building has an
authorised image and three do not, so three media wells collapse entirely
and the grid reads as the founder described it — three small text boxes
beside one large picture card.

THE TREATMENT. The three keep the SAME 4/3 frame the stylesheet already
declares, filled with the page's own hair tone and carrying one line of
existing micro-caps saying what is true: Atlas holds no image it may
publish. No photograph is invented, no logo is enlarged, no supplier mark
appears, and no new component is introduced — it is the frame that is
already there, no longer collapsed.

SCOPE. Hung off #matchPrimary[data-pn-verdict], set only by the
residential verdict hero, so the Garden Room gallery is untouched.

Usage: python3 atlas-tools/build-ah-card-parity.py [--check|--revert]
"""

import hashlib, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "your-plot.html")
BAK = PAGE + ".bak-cardparity"
BASELINE = "49f352bb187f7b57"

SCOPE = "#screen-match-results #matchPrimary[data-pn-verdict] ~ #altResults"

FIND = """  #screen-match-results #matchPrimary[data-pn-verdict] ~ #altResults
    .results-gallery-media > img{
    position:absolute; inset:0; width:100%; height:100%; display:block;
  }
"""

REPL = """  #screen-match-results #matchPrimary[data-pn-verdict] ~ #altResults
    .results-gallery-media > img{
    position:absolute; inset:0; width:100%; height:100%; display:block;
  }
  /* P1 - THE NO-IMAGE PLATE. Three of the four buildings have no image
     Atlas may publish, so their media well collapsed and the grid read as
     three small text boxes beside one picture card. The frame stays, at
     the 4/3 the stylesheet already declares, in the page's own hair tone.
     The shipped collapse rule is overridden ONLY inside this grid. */
  #screen-match-results #matchPrimary[data-pn-verdict] ~ #altResults
    .results-gallery-media:has(img.pn-image-fallback){
    display:block; aspect-ratio:4/3; background:var(--pn-hair);
    border-radius:6px; overflow:hidden; position:relative;
  }
  #screen-match-results #matchPrimary[data-pn-verdict] ~ #altResults
    .results-gallery-media > img.pn-image-fallback{ display:none; }
  /* ONE LINE, IN THE EXISTING MICRO-CAPS, SAYING WHAT IS TRUE. Not a
     placeholder for a picture that exists: a statement that none does. */
  #screen-match-results #matchPrimary[data-pn-verdict] ~ #altResults
    .results-gallery-media:has(img.pn-image-fallback)::after{
    content:'No image Atlas may publish';
    position:absolute; inset:auto 0 0 0; padding:0 12px 10px;
    font-size:var(--pn-w-meta); letter-spacing:.06em;
    text-transform:uppercase; color:var(--pn-stone);
  }
"""

FORBIDDEN_IN_ADDED = ["logo", "atlas-final-static", "pn-atlas",
                      "placeholder image", "coming soon"]


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

    # THE LINE-SUBTRACTION TRAP. Computing `added` as "lines of REPL not in
    # FIND" silently DELETES every scope-prefix line, because an identical
    # prefix line appears in FIND — which left the scope guard inspecting
    # rules whose scope had been stripped, and it passed an unscoped
    # mutant. Every rule in REPL is checked instead: FIND's own rule is
    # scoped too, so the stronger test is also the correct one. 
    added = REPL

    # G1 — every added rule carries the residential scope. Checked on the
    #      whole rule with whitespace normalised, because these selectors
    #      wrap across two lines and a continuation line on its own looks
    #      unscoped when it is not.
    # COMMENTS ARE STRIPPED FIRST. Splitting on "}" puts a comment and the
    # rule that follows it in one chunk, and skipping chunks that START
    # with a comment then skips the rule too — which let an unscoped
    # mutant through. Remove the comments, then every chunk is a rule.
    for rule in re.split(r"\}\s*", re.sub(r"/\*.*?\*/", " ", added, flags=re.S)):
        flat = re.sub(r"\s+", " ", rule).strip()
        if not flat or "{" not in flat:
            continue
        if SCOPE.replace("  ", " ") not in flat:
            raise SystemExit("REFUSED: an added rule is not scoped to the "
                             "residential verdict grid:\n%s" % flat[:140])

    # G2 — no supplier mark, no brand asset, no pretend-photograph language.
    low = added.lower()
    for w in FORBIDDEN_IN_ADDED:
        if w in low:
            raise SystemExit("REFUSED: the no-image plate must not carry %r" % w)

    # G3 — CSS only.
    js_src = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", src, re.S)
    js_out = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", out, re.S)
    if js_src != js_out:
        raise SystemExit("REFUSED: this is a CSS-only change; script changed")

    # G4 — the governed fallback machinery may gain references (these new
    #      rules are two of them) but may never LOSE one.
    for t in ["PN_IMAGE_FALLBACK_SRC", "pn-image-fallback", "pnAuthorisedImage("]:
        if out.count(t) < src.count(t):
            raise SystemExit("REFUSED: a %s reference was lost" % t)
    #      and the image itself must still be refused, never shown.
    if "img.pn-image-fallback{ display:none; }" not in re.sub(r"\s+", " ", out):
        raise SystemExit("REFUSED: the fallback image is no longer hidden")

    if mode == "--check":
        print("CHECK ONLY. %s -> %s, +%d lines, 4 guards pass"
              % (base, sha16(out), out.count("\n") - src.count("\n")))
        return

    if not os.path.exists(BAK):
        open(BAK, "w", encoding="utf-8").write(src)
    open(PAGE, "w", encoding="utf-8").write(out)
    print("applied. %s -> %s" % (base, sha16(out)))


if __name__ == "__main__":
    main()
