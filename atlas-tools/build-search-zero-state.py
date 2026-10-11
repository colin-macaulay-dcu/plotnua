#!/usr/bin/env python3
"""
BOUNDED BUILDER — THE SEARCH NO-RESULTS EXPLANATION
===================================================
One anchored edit to the zero-result branch of renderResults() in search.js.

WHY. The old copy said:

    "PlotNua only shows what it can stand behind. If a supplier or product is
     not here, it is because we have not researched it to a standard we would
     publish - not because it does not exist."

That sentence asserts exactly one reason for an absence, and it is often the
wrong one. A supplier can be fully researched, verified first-party and sitting
in a private preview awaiting the supplier's own sign-off. Telling a homeowner
that such a supplier "has not been researched to a standard we would publish"
is not a softening. It is untrue, and it is unfair to the supplier.

The replacement states the real position: research is continuous, and some of
it is not visible yet. It names no supplier, no product and no count, so it
exposes nothing about what is in the pipeline.

WHAT THIS DOES NOT TOUCH. Copy only. The index, the matcher, the scoring, the
tier logic and result eligibility are all outside the replaced block, and G3
proves every byte outside it is identical.

    python3 atlas-tools/build-search-zero-state.py [--stage] [--check]
                                                   [--revert]

--stage writes to /tmp/plotnua-stage/, --check reports without writing,
--revert restores the .bak sidecar. Exit 0 = applied (or already correct).
"""
import difflib
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
SRC = SITE / "search.js"

STAGE = "--stage" in sys.argv
CHECK = "--check" in sys.argv
REVERT = "--revert" in sys.argv
OUT = (pathlib.Path("/tmp/plotnua-stage/search.js") if STAGE else SRC)
BAK = SRC.with_suffix(".js.bak")


def die(msg):
    """A builder that crashes has not refused; it has merely failed."""
    print("REFUSED: " + msg)
    sys.exit(1)


# The exact block being replaced, reproduced byte for byte from search.js.
# If one character of it has moved, the builder refuses rather than guess
# where the copy now lives.
# search.js writes typographic characters literally, not as HTML entities:
# the retired sentence carries a real em dash (U+2014). The replacement
# follows the same convention and uses a real right single quote (U+2019),
# which also means neither apostrophe needs escaping inside the JS string.
OLD = """      h.push('<p class="pns-zero-lead">We have nothing on <strong>' +
             esc(res.query) + '</strong> yet.</p>');
      h.push('<p>PlotNua only shows what it can stand behind. If a supplier or ' +
             'product is not here, it is because we have not researched it to a ' +
             'standard we would publish \u2014 not because it does not exist.</p>');"""

NEW = """      h.push('<p class="pns-zero-lead">We couldn\u2019t find a published ' +
             'result for that search.</p>');
      h.push('<p>PlotNua is continually researching new products and ' +
             'suppliers. Some are still being checked or prepared for ' +
             'publication, so not everything we\u2019ve researched is ' +
             'visible yet.</p>');"""

# The Discoveries link is the one onward route out of a dead end. It sits
# immediately after the replaced block and must survive untouched.
LINK = ("      h.push('<p>You could try a possibility instead: ' +\n"
        "             '<a href=\"discoveries.html\">browse all Discoveries</a>.</p>');")

# Phrases that must not survive anywhere in the file.
RETIRED = [
    "standard we would publish",
    "we have not researched it",
    "only shows what it can stand behind",
    "We have nothing on",
]


def main():
    if not SRC.exists():
        die("search.js is not where this builder expects it.")
    src = SRC.read_text(encoding="utf-8")

    if REVERT:
        if not BAK.exists():
            die("there is no .bak sidecar to revert to.")
        shutil.copyfile(BAK, SRC)
        print("REVERTED search.js from its .bak sidecar.")
        return

    already = NEW in src

    # G1 · THE ANCHOR. Exactly once, or refuse.
    if not already:
        n = src.count(OLD)
        if n != 1:
            die("the zero-result copy block was found %d times, not once. "
                "search.js has moved. Nothing written." % n)

    # G2 · THE ONWARD ROUTE. The founder asked for the Discoveries link to be
    # preserved, so its survival is asserted rather than assumed.
    if src.count(LINK) != 1:
        die("the Discoveries link is not present exactly once in the "
            "zero-result branch. Nothing written.")

    out = src if already else src.replace(OLD, NEW, 1)

    # G3 · NOTHING ELSE MOVED. Everything outside the replaced block must be
    # byte-identical. This is what keeps a copy change from becoming a
    # behaviour change: the index, the matcher, the scoring and result
    # eligibility all live outside it.
    if not already:
        if out.replace(NEW, OLD, 1) != src:
            die("replacing the block did not leave the rest of the file "
                "identical. Nothing written.")

    # G4 · THE RETIRED SENTENCE IS GONE, everywhere, not just here.
    for phrase in RETIRED:
        if phrase in out:
            die("the retired phrase %r still appears in the output. "
                "Nothing written." % phrase)

    # G5 · THE APPROVED COPY IS PRESENT, as approved.
    # The copy is wrapped across source lines, so both sides are unwrapped
    # before comparison: the assertion is about the sentence a homeowner
    # reads, not about where the line breaks fall in the source.
    flat = out.replace("' +\n             '", "")
    for required in ("We couldn\u2019t find a published result for that search.",
                     "PlotNua is continually researching new products and "
                     "suppliers. Some are still being checked or prepared "
                     "for publication, so not everything we\u2019ve "
                     "researched is visible yet."):
        if required not in flat:
            die("the approved copy is not in the output: %r" % required[:48])

    # G6 · THE LINK SURVIVED THE EDIT.
    if out.count(LINK) != 1:
        die("the Discoveries link did not survive. Nothing written.")

    # G7 · NO SUPPLIER OR PRODUCT IS NAMED. The whole point of the correction
    # is that an absence is not explained by naming what is absent.
    for name in ("BIOBUILDS", "Biobuilds", "Hutsmith", "Yard Box",
                 "Power Sheds", "Cosy Cabins", "awaiting approval",
                 "pending approval", "private preview"):
        if name in NEW:
            die("the new copy names %r. The correction must be generic and "
                "must not expose unpublished suppliers." % name)

    print("\nSEARCH ZERO-STATE COPY")
    print("=" * 74)
    if already:
        print("  ok    the approved copy is already in place; nothing to do")
    else:
        print("  ok    G1  the anchor matched exactly once")
        print("  ok    G3  every byte outside the block is unchanged")
    print("  ok    G4  the retired explanation is gone (%d phrases checked)"
          % len(RETIRED))
    print("  ok    G5  the approved heading and body are present")
    print("  ok    G6  the Discoveries link is preserved")
    print("  ok    G7  no supplier or product is named")

    if CHECK:
        print("-" * 74)
        print("CHECK ONLY. Nothing written.")
        if not already:
            d = difflib.unified_diff(src.splitlines(), out.splitlines(),
                                     "search.js", "search.js (proposed)",
                                     lineterm="", n=2)
            print("\n".join(d))
        return

    if already:
        print("-" * 74)
        print("No change needed.")
        return

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not STAGE and not BAK.exists():
        shutil.copyfile(SRC, BAK)
    OUT.write_text(out, encoding="utf-8")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(out.encode("utf-8"))))
    if STAGE:
        print("STAGED ONLY. The deployed tree is untouched.")


if __name__ == "__main__":
    main()
