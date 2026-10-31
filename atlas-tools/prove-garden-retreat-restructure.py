#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUARD-CAPABILITY PROOF — build-garden-retreat-restructure.py (GR1-GR9).

Each case breaks the published page ONCE, in memory, and runs the builder's
own guards(); every case must be refused. Nothing is written; the page is
hashed before and after.

Run: python3 atlas-tools/prove-garden-retreat-restructure.py
"""
import hashlib
import importlib.util
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("grr", HERE / "build-garden-retreat-restructure.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
PAGE = B.PAGE
before = hashlib.sha256(PAGE.read_bytes()).hexdigest()
SRC = PAGE.read_text(encoding="utf-8")
results = []


def case(label, fn, expect_refused=True, compare=False):
    page = fn(SRC)
    if page == SRC and expect_refused:
        print("  ERROR   %s — mutation did not apply" % label)
        results.append(False)
        return
    errs, _ = B.guards(page, before=SRC if compare else None)
    hit = bool(errs) == expect_refused
    print("  %s %s\n           -> %s" % ("CAUGHT " if hit else "MISSED ", label,
                                          (errs[0] if errs else "passes")[:100]))
    results.append(hit)


def sub(a, b):
    return lambda s: s.replace(a, b, 1)


print("GUARD-CAPABILITY PROOF — GARDEN RETREAT RESTRUCTURE")
print("=" * 78)
case("CONTROL the published page", lambda s: s, expect_refused=False)
case("GR1 the comparison moved below the maker directory",
     lambda s: s.replace('id="compare"', 'id="compare-x"', 1).replace('id="could-it-work"', 'id="compare"', 1))
case("GR2 a 'Check your garden' action appears in the hero",
     sub('>Compare the options</a>', '>Check your garden</a>'))
case("GR2 a hero action points off the page",
     sub('href="#compare">Compare', 'href="your-plot.html">Compare'))
case("GR3 an OGNYX image is put back in the editorial",
     # the card's <img> keeps its src; since 20 Oct 2026 it may sit inside a WebP <picture>
     sub('<img src="assets/img/45a270b7716e4a94.jpg"',
         '<img src="https://www.ognyx.com/cdn/shop/files/x.png"'))
case("GR4 the planning short answer is folded into an accordion",
     lambda s: s.replace('    <div class="rule-group">\n      <h3>The short answer</h3>',
                         '    <details class="faq-item"><summary><h3>Short</h3></summary><div class="rule-group">\n      <h3>The short answer</h3>', 1)
                .replace("That is the useful answer. The rest of this section is why, and where it stops being that simple.</p>\n    </div>",
                         "That is the useful answer. The rest of this section is why, and where it stops being that simple.</p>\n    </div></details>", 1))
case("GR4 the electrical warning is hidden",
     lambda s: re.sub(r'(<div class="practical-item gr-warn">.*?</div>\n)',
                      lambda m: "<details><summary>Electricity</summary>" + m.group(1) + "</details>\n", s, count=1, flags=re.S))
case("GR5 an accordion loses its summary",
     sub('<summary><h3>Base and weight</h3><span class="icon"></span></summary>', '<h3>Base and weight</h3>'))
case("GR6 the long intro sections come back",
     sub('  <section class="article-section reveal" id="three-ways-in">',
         '<p>' + ("A long paragraph of prose. " * 400) + '</p>\n  <section class="article-section reveal" id="three-ways-in">'))
# 31 Oct 2026 (supplier-gallery consolidation): the explorer's intro, which carried
# "Makers are never ranked;", is gone; the same planted sentence goes into the footer.
case("GR7 governance language reaches the reader",
     sub("Makers are not ranked,", "Only makers that passed the publication gate are shown,"))
case("GR8 a zero-confirmation count is shown",
     sub("Three products PlotNua checked directly.", "Irish availability is confirmed for 0 products."))
case("GR9 the page is edited outside main",
     sub("Related Discoveries</h2>", "Related Discoveries, ranked</h2>"), compare=True)
after = hashlib.sha256(PAGE.read_bytes()).hexdigest()
print("-" * 78)
print("%d of %d correct" % (sum(results), len(results)))
print("page byte-identical after the proof: %s" % ("YES" if before == after else "NO"))
sys.exit(0 if all(results) and before == after else 1)
