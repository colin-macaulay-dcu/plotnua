#!/usr/bin/env python3
"""
G3 CORRECTION 1 — DESKTOP READING MEASURE, CSS ONLY
===============================================================================
FOUNDER-AUTHORISED, 7 October 2026, after visual review:

    "The desktop invitation explanatory copy/list has an excessively long
     reading measure. Constrain ONLY the invitation explanatory
     paragraph/list to a comfortable desktop reading measure, approximately
     65-75 characters."

WHAT THIS ADDS. Two max-width declarations, nothing else:

    #bgIntOffer .bg-int-p        max-width: 68ch
    #bgIntOffer .bg-int-facts li max-width: 68ch

WHY IT IS SCOPED TO #bgIntOffer, AND NOT TO .bg-int-p GLOBALLY
  .bg-int-p is used in two places. The INVITATION uses it in markup, and
  intEndState() also assigns it to the paragraphs of the received / not_open /
  unavailable states. The founder scoped this correction to the invitation, so
  an unscoped `.bg-int-p { max-width }` would have silently changed three other
  states nobody reviewed or authorised. The descendant selector confines it to
  the invitation exactly.

WHY max-width AND NOT A MEDIA QUERY
  A max-width in `ch` binds only when the container is wider than the measure.
  At 390px the panel's inner width is about 350px, far below 68ch, so the
  declaration has NO EFFECT on mobile — no breakpoint needed, and no risk of
  getting a breakpoint boundary wrong. Mobile layout is therefore untouched by
  construction rather than by assertion.

WHAT IT CANNOT TOUCH
  No wording. No card width (.bg-int padding and background are not in the
  patch). No form grid (.bg-int-grid is not in the patch). No JS. No engine.
  No Worker. The patch is two selectors inside the existing G3 CSS region.
"""

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "disc025-borrowed-garden-check.html"

ANCHOR = "  .bg-int-cta{margin:20px 0 0;}"

PATCH = """  /* ---- CORRECTION 1 · DESKTOP READING MEASURE ---------------------------
     Founder-authorised after visual review: the invitation's explanatory
     paragraph and its three statements ran to roughly 129 and 138 characters
     per line inside the 1024px content column. Capped at 68ch, mid-way through
     the approved 65-75 band.

     SCOPED TO #bgIntOffer DELIBERATELY. .bg-int-p is also used by
     intEndState() for the received / not_open / unavailable paragraphs, which
     the founder did not include in this correction, so an unscoped rule would
     have changed three unreviewed states.

     No media query is needed: a ch-based max-width binds only where the
     container is wider than the measure, and the panel's inner width at 390px
     (about 350px) is far below 68ch. Mobile is untouched by construction. */
  #bgIntOffer .bg-int-p,
  #bgIntOffer .bg-int-facts li{max-width:68ch;}
  .bg-int-cta{margin:20px 0 0;}"""

MARKER = "CORRECTION 1 · DESKTOP READING MEASURE"

# Regions that must come out byte-identical. The CSS region necessarily
# changes; everything else must not.
FROZEN = [
    ("engine",  "/* PLOTNUA-DISC025-ENGINE-BEGIN */",
                "/* PLOTNUA-DISC025-ENGINE-END */"),
    ("save",    "/* PLOTNUA-JOURNEY-SAVE-BEGIN */",
                "/* PLOTNUA-JOURNEY-SAVE-END */"),
    ("g3-js",   "/* PLOTNUA-G3-INTEREST-BEGIN",
                "/* PLOTNUA-G3-INTEREST-END */"),
    ("g3-html", "<!-- PLOTNUA-G3-HTML-BEGIN",
                "<!-- PLOTNUA-G3-HTML-END -->"),
]

# Declarations the founder ruled out of scope. None may appear in the patch.
FORBIDDEN_IN_PATCH = [
    ("card width",   r"\.bg-int\{"),
    ("form grid",    r"bg-int-grid"),
    ("mobile rules", r"@media"),
    ("font sizes",   r"font-size"),
    ("wording",      r"content\s*:\s*[\"']"),
]


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def region(text, begin, end):
    return text[text.index(begin):text.index(end) + len(end)]


def main():
    check = "--check" in sys.argv

    src = TARGET.read_text(encoding="utf-8")
    before = hashlib.sha256(src.encode("utf-8")).hexdigest()
    print("  TARGET  %s" % TARGET.name)
    print("  BEFORE  %d bytes  sha256 %s" % (len(src.encode("utf-8")), before))
    print()

    if MARKER in src:
        die("Correction 1 is already applied (marker present). This builder "
            "is not re-runnable over its own output.")

    n = src.count(ANCHOR)
    print("  ANCHOR  occurrences=%d" % n)
    if n != 1:
        die("anchor occurs %d times, expected exactly 1" % n)

    # The patch must stay inside the G3 CSS region.
    css = region(src, "/* ---- G3 · EXPRESSION OF INTEREST", "PLOTNUA-G3-CSS-END */")
    if ANCHOR not in css:
        die("the anchor is not inside the G3 CSS region — refusing to patch "
            "CSS belonging to anything else")
    print("  anchor is inside the G3 CSS region")

    # Scope guards on the patch itself.
    for what, pat in FORBIDDEN_IN_PATCH:
        if re.search(pat, PATCH.split("*/", 1)[1] if "*/" in PATCH else PATCH):
            die("the patch touches %s, which the founder ruled out of scope"
                % what)
    print("  patch touches none of: card width, form grid, mobile rules, "
          "font sizes, wording")

    # The patch must be scoped, not global.
    if ".bg-int-p," in PATCH.replace("#bgIntOffer .bg-int-p,", ""):
        die("the patch contains an unscoped .bg-int-p selector")
    if "#bgIntOffer" not in PATCH:
        die("the patch is not scoped to #bgIntOffer")
    print("  patch is scoped to #bgIntOffer")

    # The measure must land in the authorised band.
    m = re.search(r"max-width:(\d+)ch", PATCH)
    if not m:
        die("the patch declares no ch-based max-width")
    ch = int(m.group(1))
    print("  measure %dch (authorised band 65-75)" % ch)
    if not 65 <= ch <= 75:
        die("measure %dch is outside the authorised 65-75 band" % ch)

    frozen_before = {}
    for name, b, e in FROZEN:
        if b not in src or e not in src:
            die("frozen region markers missing: %s" % name)
        frozen_before[name] = hashlib.sha256(
            region(src, b, e).encode("utf-8")).hexdigest()

    if check:
        print("\n  --check: every guard passed. Nothing written.")
        return

    out = src.replace(ANCHOR, PATCH, 1)

    print("\n  FROZEN REGION PROOF")
    for name, b, e in FROZEN:
        sha = hashlib.sha256(region(out, b, e).encode("utf-8")).hexdigest()
        ok = sha == frozen_before[name]
        print("    %-9s %s  %s" % (name, "IDENTICAL" if ok else "CHANGED",
                                   sha[:16]))
        if not ok:
            die("frozen region %s changed" % name)

    # Only CSS may have moved: the executable text must be byte-identical.
    def strip_css(t):
        return re.sub(r"<style>.*?</style>", "<style/>", t, flags=re.S)
    if strip_css(src) != strip_css(out):
        die("something outside <style> changed — this builder is CSS only")
    print("    non-CSS   IDENTICAL (everything outside <style> byte-for-byte)")

    TARGET.write_text(out, encoding="utf-8")
    after = hashlib.sha256(out.encode("utf-8")).hexdigest()
    print("\n  AFTER   %d bytes  sha256 %s" % (len(out.encode("utf-8")), after))
    print("  DELTA   +%d bytes, CSS only"
          % (len(out.encode("utf-8")) - len(src.encode("utf-8"))))


if __name__ == "__main__":
    main()
