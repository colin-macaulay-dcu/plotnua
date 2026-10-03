#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — write the governed Library card images into discoveries.html.

THE MAPPING IS THE SOURCE OF TRUTH, not this file and not the markup.
atlas-tools/discovery-library-images.json records, per Discovery, the image
that best shows THE DISCOVERY REALISED and the standalone alt text for that
card. This builder copies it onto the page and refuses anything else.

NO SELECTOR. Two earlier attempts inferred the card image from structure --
the Results engine, then "the first .imagine-photo that is not a cmp frame".
The second looked principled and systematically chose the POTENTIAL ASSET
plate: the empty wall, the bare lawn, the frontage before the bins are gone.
Discovery pages have different image rhythms and no rule encodes editorial
judgement, so the judgement is written down and this builder just applies it.

Run: python3 atlas-tools/build-discovery-library-images.py [--check]
"""

import json
import pathlib
import re
import sys

CHECK = "--check" in sys.argv
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
LIBRARY = ROOT / "discoveries.html"
REGISTER = HERE / "discovery-library-images.json"
CARD = re.compile(r'<a class="lib-card" href="([^"]+)"[^>]*>(.*?)</a>', re.S)

# The page-side phrases that mark a Potential Asset / before plate. "empty"
# alone is NOT one: Driveway Income's realised image is described as two cars
# in spaces "that stood empty", and a marker that cannot tell a result from a
# description of what it replaced would block the right image.
PA_MARKERS = ["potential asset", "annotated by plotnua",
              "before anything is planted", "standing completely empty"]


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def main():
    rows = json.loads(REGISTER.read_text(encoding="utf-8"))["cards"]
    if not rows:
        die("the mapping lists no cards. An empty mapping would rewrite "
            "nothing and report success.")
    src = LIBRARY.read_text(encoding="utf-8")
    original = src
    cards = list(CARD.finditer(src))

    # G0 · THE PAGE MUST BE THE ONE THIS WAS ANCHORED AGAINST.
    if len(cards) != len(rows):
        die("the page has %d cards and the mapping has %d rows. Every card "
            "must be governed, and every row must describe a real card."
            % (len(cards), len(rows)))
    by_card = {r["card"]: r for r in rows}
    for m in cards:
        if m.group(1) not in by_card:
            die("card %s is on the page but not in the mapping. A card "
                "without a row would keep whatever image it has, unguarded."
                % m.group(1))

    changes = []
    for m in cards:
        row = by_card[m.group(1)]
        im = re.search(r'<img src="([^"]+)" alt="([^"]*)"', m.group(2))
        if not im:
            die("card %s has no <img src=... alt=...> in the shape this "
                "builder edits." % m.group(1))
        old_src, old_alt = im.group(1), im.group(2)
        new_src, new_alt = row["image"], row["alt"]

        # G1 · THE CHOSEN IMAGE MUST BE A LOCAL ASSET THAT EXISTS.
        if re.match(r"^https?:", new_src):
            die("%s maps to an externally hosted image (%s). The Library "
                "carries PlotNua's own assets only." % (row["title"], new_src))
        if not (ROOT / new_src).exists():
            die("%s maps to %s, which is not on disk."
                % (row["title"], new_src))

        # G2 · IT MUST APPEAR ON THE DISCOVERY PAGE IT REPRESENTS. A card
        # showing a picture that is nowhere on the page it links to would be
        # a different kind of lie from the one being fixed.
        page = ROOT / row["card"]
        if not page.exists():
            die("%s links to %s, which is not in the tree."
                % (row["title"], row["card"]))
        page_html = page.read_text(encoding="utf-8")
        if new_src not in page_html:
            die("%s maps to %s, which does not appear on %s."
                % (row["title"], new_src, row["card"]))

        # G3 · AND IT MUST NOT BE A POTENTIAL-ASSET PLATE. This is the whole
        # correction: the page's own description of that image is what says
        # whether it is a before state.
        pm = re.search(r'<img[^>]*src="%s"[^>]*alt="([^"]*)"'
                       % re.escape(new_src), page_html)
        if pm:
            low = pm.group(1).lower()
            hit = [k for k in PA_MARKERS if k in low]
            if hit:
                die("%s maps to %s, which %s describes as a potential asset "
                    "(%r). The Library shows the discovery REALISED."
                    % (row["title"], new_src, row["card"], hit[0]))

        # G4 · STANDALONE ALT TEXT. Page-side descriptions open "The same..."
        # which reads as a non-sequitur on a card seen alone.
        if not new_alt.strip():
            die("%s has no alt text in the mapping." % row["title"])
        if new_alt.strip().lower().startswith("the same"):
            die("%s has alt text beginning \"The same\", which is page "
                "sequence language. Library alt text stands alone."
                % row["title"])

        if new_src != old_src or new_alt != old_alt:
            old_tag = '<img src="%s" alt="%s"' % (old_src, old_alt)
            if src.count(old_tag) != 1:
                die("the <img> tag for %s is not unique (%d matches). "
                    "Refusing rather than editing the wrong one."
                    % (row["card"], src.count(old_tag)))
            src = src.replace(old_tag,
                              '<img src="%s" alt="%s"' % (new_src, new_alt), 1)
            changes.append((row["title"], old_src, new_src, old_alt, new_alt))

    # G5 · NOTHING BUT THE IMAGES AND THEIR DESCRIPTIONS MAY MOVE.
    strip = lambda h: re.sub(r'<img src="[^"]*" alt="[^"]*"', "<img>", h)
    if strip(original) != strip(src):
        die("something other than a card image and its alt text changed. "
            "Titles, lines, categories, pills, links and order are not this "
            "builder's business.")

    if CHECK:
        print("CHECK ONLY — nothing written. %d card(s) would change."
              % len(changes))
        for t, o, n, _, _ in changes:
            print("  %-38s %s -> %s"
                  % (t[:38], o.split("/")[-1], n.split("/")[-1]))
        sys.exit(0)

    LIBRARY.write_text(src, encoding="utf-8")
    print("DISCOVERY LIBRARY IMAGES — GOVERNED MAPPING APPLIED")
    print("=" * 74)
    print("  ok    6 guards passed")
    print("  ok    %d cards governed, %d changed, %d already correct"
          % (len(rows), len(changes), len(rows) - len(changes)))
    print("  ok    no card shows a potential-asset plate")
    print("-" * 74)
    for t, o, n, oa, na in changes:
        print("  %s" % t)
        print("     image  %s  ->  %s" % (o.split("/")[-1], n.split("/")[-1]))
        print("     alt    %s" % (oa[:64] + ("..." if len(oa) > 64 else "")))
        print("         -> %s" % (na[:64] + ("..." if len(na) > 64 else "")))
    print("-" * 74)
    print("wrote %s (%d bytes)" % (LIBRARY, len(src.encode("utf-8"))))


main()
