#!/usr/bin/env python3
"""
PS-1 · FOOTER COPY, FOUNDER-APPROVED FINAL WORDING
===============================================================================
Replaces the homeowner-visible text of the single <p class="bg-foot"> element.
Nothing else. Not structure, not CSS, not JavaScript, not the G3 markup, not
the questions, not decide(), not the result logic, not Save/My Plot, not the
register form, not the consent wording, not the Worker, and no other
homeowner-visible copy.

FOUNDER-APPROVED TEXT, 8 October 2026. The previous, more procedural PS-1
wording is superseded. The approved text is warmer while preserving the
governance: the Property Check does not send PlotNua the homeowner's details;
joining the register is separate and voluntary; its purpose is stated;
registration records interest only; it is not a match; it is not an
introduction; no grower network is implied; nothing is promised.

PUNCTUATION. The approved sentence uses an em dash and four apostrophes. The
page's homeowner copy already uses typographic punctuation via HTML entities
(`We don&rsquo;t collect them`, `The register isn&rsquo;t open yet`), so this
follows that convention: &mdash; and &rsquo;. The builder then asserts that the
DECODED, rendered text equals the approved string character for character, so
the entity choice cannot silently alter what a homeowner reads.
"""

import hashlib
import html as htmllib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "disc025-borrowed-garden-check.html"

# The approved text exactly as the founder issued it: em dash U+2014,
# apostrophes U+2019. This is the acceptance criterion for the RENDERED text.
APPROVED = (
    "PlotNua does the homework. You make the decision. Your Property Check "
    "stays private — answering the questions doesn’t send us your "
    "details. If you’d like to hear from us if someone nearby is looking "
    "for growing space, you can choose to join the register. That simply "
    "tells us you’re interested. It isn’t a match or an "
    "introduction."
)

# The exact element being replaced, matched whole so no neighbouring markup
# can be caught. Must occur once.
OLD_BLOCK = """    <p class="bg-foot">PlotNua does the homework. You make the decision. We do not
      arrange anything or introduce anybody through this Property Check, and
      nothing on this page sends your details anywhere. Local Garden Matching is
      the next capability PlotNua intends to build.</p>"""

NEW_BLOCK = """    <p class="bg-foot">PlotNua does the homework. You make the decision. Your
      Property Check stays private &mdash; answering the questions doesn&rsquo;t
      send us your details. If you&rsquo;d like to hear from us if someone
      nearby is looking for growing space, you can choose to join the register.
      That simply tells us you&rsquo;re interested. It isn&rsquo;t a match or an
      introduction.</p>"""

# Regions that must be byte-identical afterwards.
FROZEN = [
    ("engine",  "/* PLOTNUA-DISC025-ENGINE-BEGIN */",
                "/* PLOTNUA-DISC025-ENGINE-END */"),
    ("save",    "/* PLOTNUA-JOURNEY-SAVE-BEGIN */",
                "/* PLOTNUA-JOURNEY-SAVE-END */"),
    ("g3-js",   "/* PLOTNUA-G3-INTEREST-BEGIN",
                "/* PLOTNUA-G3-INTEREST-END */"),
    ("g3-html", "<!-- PLOTNUA-G3-HTML-BEGIN",
                "<!-- PLOTNUA-G3-HTML-END -->"),
    ("g3-css",  "/* ---- G3 · EXPRESSION OF INTEREST",
                "PLOTNUA-G3-CSS-END */"),
]


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def region(t, b, e):
    return t[t.index(b):t.index(e) + len(e)]


def rendered_text(block):
    """Strip tags, decode entities, collapse whitespace — what a reader sees."""
    inner = re.sub(r"^.*?<p[^>]*>", "", block, flags=re.S)
    inner = re.sub(r"</p>.*$", "", inner, flags=re.S)
    return re.sub(r"\s+", " ", htmllib.unescape(inner)).strip()


def main():
    check = "--check" in sys.argv
    src = TARGET.read_text(encoding="utf-8")
    before = hashlib.sha256(src.encode("utf-8")).hexdigest()

    print("  TARGET  %s" % TARGET.name)
    print("  BEFORE  %d bytes  sha256 %s" % (len(src.encode("utf-8")), before))
    print()

    if before != ("1a20d6edea571e6e3915ae2c746810dd63625acc"
                  "baac9a8918e38d6946e27170"):
        die("the target is not the frozen, deployed artefact "
            "1a20d6edea571e6e... — refusing to patch an unexpected file")
    print("  base is the frozen deployed artefact  OK")

    if APPROVED in src:
        die("the approved wording is already present; this builder is not "
            "re-runnable over its own output")

    n = src.count(OLD_BLOCK)
    print("  bg-foot block occurrences=%d" % n)
    if n != 1:
        die("the bg-foot block occurs %d times, expected exactly 1" % n)

    # The new block must render EXACTLY the approved text.
    got = rendered_text(NEW_BLOCK)
    print()
    print("  RENDERED-TEXT PROOF")
    print("    approved chars %d" % len(APPROVED))
    print("    rendered chars %d" % len(got))
    print("    identical      %s" % (got == APPROVED))
    if got != APPROVED:
        for i, (a, b) in enumerate(zip(APPROVED, got)):
            if a != b:
                die("rendered text diverges at char %d: approved %r, got %r"
                    % (i, a, b))
        die("rendered text differs in length from the approved wording")

    # Governance assertions on the approved text itself.
    print()
    print("  GOVERNANCE ASSERTIONS ON THE APPROVED TEXT")
    required = [
        ("check sends no details", "answering the questions doesn’t send us your details"),
        ("register is a choice",   "you can choose to join the register"),
        ("records interest only",  "simply tells us you’re interested"),
        ("not a match",            "isn’t a match"),
        ("not an introduction",    "or an introduction"),
    ]
    for label, frag in required:
        ok = frag in APPROVED
        print("    %-26s %s" % (label, "present" if ok else "*** MISSING"))
        if not ok:
            die("the approved text lacks the %s statement" % label)

    forbidden = [
        ("promises a match",        r"we will match|guarantee[sd]? (you )?a match"),
        ("implies a network",       r"growers? (are |already )?(waiting|registered|network)"),
        ("implies automation",      r"automatic|automated|algorithm"),
        ("claims insurance",        r"insur"),
        ("says the check sends",    r"Property Check (sends|will send) (us )?your details"),
    ]
    for label, pat in forbidden:
        hit = re.search(pat, APPROVED, re.I)
        print("    %-26s %s" % ("no " + label, "clean" if not hit else "*** " + hit.group(0)))
        if hit:
            die("the approved text %s" % label)

    frozen_before = {name: hashlib.sha256(region(src, b, e).encode()).hexdigest()
                     for name, b, e in FROZEN}

    if check:
        print("\n  --check: every guard passed. Nothing written.")
        return

    out = src.replace(OLD_BLOCK, NEW_BLOCK, 1)

    print()
    print("  FROZEN REGION PROOF")
    for name, b, e in FROZEN:
        sha = hashlib.sha256(region(out, b, e).encode()).hexdigest()
        ok = sha == frozen_before[name]
        print("    %-9s %s  %s" % (name, "IDENTICAL" if ok else "CHANGED", sha[:16]))
        if not ok:
            die("frozen region %s changed" % name)

    # Nothing outside the single <p> may differ.
    a = src.replace(OLD_BLOCK, "@@FOOT@@")
    b = out.replace(NEW_BLOCK, "@@FOOT@@")
    if a != b:
        die("something outside the bg-foot paragraph changed")
    print("    rest-of-file IDENTICAL (only the bg-foot paragraph differs)")

    TARGET.write_text(out, encoding="utf-8")
    after = hashlib.sha256(out.encode("utf-8")).hexdigest()
    print()
    print("  AFTER   %d bytes  sha256 %s" % (len(out.encode("utf-8")), after))
    print("  DELTA   %+d bytes" % (len(out.encode("utf-8")) - len(src.encode("utf-8"))))


if __name__ == "__main__":
    main()
