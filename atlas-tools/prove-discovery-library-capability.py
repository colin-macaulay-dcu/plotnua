#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAPABILITY PROOF — atlas-tools/prove-discovery-library-images.mjs.

A guard that has never refused anything is a comment. This breaks the proof
once per check and every break must be caught.

CASE 1 IS THE ONE THE FOUNDER ASKED FOR BY NAME: "guard the mapping so
somebody cannot later accidentally replace the result image with a Potential
Asset plate." It is driven with the REAL potential-asset plates from the real
Discovery pages -- the empty wall above the fireplace, the lawn before
anything is planted, the bare roof -- because those are exactly the images the
discarded selector rule chose, and a fixture would prove only that a fixture
works.

A POSITIVE CONTROL IS INCLUDED. A guard that refuses everything proves as
little as one that refuses nothing, so the untouched tree must pass.

HOW. The mapping and the page are real files, so each sabotage is applied IN
PLACE, the proof is run as a subprocess, and the file is restored from an
in-memory copy in a finally block. Both files are hashed before the first
sabotage and after the last, and the hashes are printed.

Run: python3 atlas-tools/prove-discovery-library-capability.py
"""

import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
REGISTER = HERE / "discovery-library-images.json"
LIBRARY = ROOT / "discoveries.html"
PROOF = HERE / "prove-discovery-library-images.mjs"

TOUCHED = [REGISTER, LIBRARY]
for f in TOUCHED + [PROOF]:
    if not f.exists():
        print("missing: " + str(f))
        sys.exit(2)

# REAL potential-asset plates, lifted from the real pages. Each is the image
# the discarded "first non-cmp .imagine-photo" rule actually chose.
REAL_PA = [
    ("Buy Original Irish Art", "discovery-a-home-for-art.html",
     "assets/img/5dc201bef1868b84.jpg", "the wall above the fireplace, empty"),
    ("The Borrowed Garden", "discovery-the-borrowed-garden.html",
     "assets/img/59d566ff7c3a50e8.jpg", "the lawn before anything is planted"),
    ("The House as a Power Station", "discovery-house-as-power-station.html",
     "assets/img/fec77c3f0bae107a.jpg", "the bare roof, annotated"),
]

before = {f: hashlib.sha256(f.read_bytes()).hexdigest() for f in TOUCHED}
results = []


def verdict():
    p = subprocess.run(["node", str(PROOF)], capture_output=True, text=True,
                       cwd=str(ROOT))
    v = {0: "GOVERNED", 1: "DIVERGED"}.get(p.returncode, "NOT ESTABLISHED")
    detail = ""
    for line in p.stdout.splitlines():
        t = line.strip()
        if t.startswith("FAIL") or t.startswith("ERROR"):
            detail = t
            break
    return v, detail


def case(label, mutate, expect):
    saved = {f: f.read_bytes() for f in TOUCHED}
    try:
        mutate()
        got, detail = verdict()
    finally:
        for f, b in saved.items():
            f.write_bytes(b)
    hit = got == expect
    print("  %s %-16s %s" % ("CAUGHT " if hit else "MISSED ", got, label))
    print("          -> %s" % (detail[:106] if detail else "(nothing reported)"))
    return hit


def edit(fn):
    d = json.loads(REGISTER.read_text(encoding="utf-8"))
    fn(d)
    REGISTER.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")


def row(d, title):
    return [c for c in d["cards"] if c["title"] == title][0]


def swap_to(title, card, image):
    """Put a different image on a card, in BOTH the mapping and the page, so
    the two agree and only the potential-asset test can object."""
    def go():
        old = None
        d = json.loads(REGISTER.read_text(encoding="utf-8"))
        r = row(d, title)
        old = r["image"]
        r["image"] = image
        REGISTER.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
        t = LIBRARY.read_text(encoding="utf-8")
        assert t.count('src="%s"' % old) == 1, "library anchor for " + title
        LIBRARY.write_text(t.replace('src="%s"' % old, 'src="%s"' % image, 1),
                           encoding="utf-8")
    return go


def swap_alt(title, alt):
    """Change alt text in BOTH places, so P2 is satisfied and only the
    standalone-alt check can object. GUARD-ORDERING: editing the mapping
    alone was caught by P2, which proved P2 and said nothing about P5."""
    def go():
        d = json.loads(REGISTER.read_text(encoding="utf-8"))
        r = row(d, title)
        old = r["alt"]
        r["alt"] = alt
        REGISTER.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
        t = LIBRARY.read_text(encoding="utf-8")
        assert t.count('alt="%s"' % old) == 1, "library alt anchor " + title
        LIBRARY.write_text(t.replace('alt="%s"' % old, 'alt="%s"' % alt, 1),
                           encoding="utf-8")
    return go


print("CAPABILITY PROOF — DISCOVERY LIBRARY IMAGES")
print("=" * 78)
r = results.append

# ---- P3 . THE FOUNDER'S GUARD, driven with the real before-plates --------
for title, page, img, what in REAL_PA:
    r(case("a result image is replaced by the real potential-asset plate "
           "(%s)" % what,
           swap_to(title, page, img), "DIVERGED"))

# ---- P2 . mapping and page must agree, both directions -------------------
r(case("the mapping is edited but the page is not",
       lambda: edit(lambda d: row(d, "Hidden Cars")
                    .__setitem__("image", "assets/img/458728c46951cf14.jpg")),
       "DIVERGED"))

r(case("the page is edited but the mapping is not",
       lambda: LIBRARY.write_text(
           LIBRARY.read_text(encoding="utf-8")
           .replace('src="assets/img/4a4a1e4b08edaada.jpg"',
                    'src="assets/img/b5cbac3fff9072d4.jpg"', 1),
           encoding="utf-8"),
       "DIVERGED"))

r(case("the governed alt text is changed on the page only",
       lambda: LIBRARY.write_text(
           LIBRARY.read_text(encoding="utf-8")
           .replace('alt="An Irish semi-detached house with two cars',
                    'alt="Some houses and some cars', 1),
           encoding="utf-8"),
       "DIVERGED"))

# ---- P5 . standalone alt text -------------------------------------------
r(case("a card inherits page-sequence alt text beginning \"The same\"",
       swap_alt("Hidden Cars", "The same driveway with the lift in use."),
       "DIVERGED"))

# ---- P4 . the image must be on the page it represents --------------------
r(case("a card is mapped to an image that is not on its Discovery page",
       swap_to("Home Exchange", "discovery-home-exchange.html",
               "assets/img/9aa6c362d5486001.jpg"),
       "DIVERGED"))

# ---- P6 . no supplier image by the back door -----------------------------
r(case("a card is mapped to an externally hosted image",
       swap_to("Hidden Cars", "discovery-hidden-cars.html",
               "https://example.com/supplier.jpg"),
       "DIVERGED"))

# ---- P1 . coverage -------------------------------------------------------
r(case("a card loses its mapping row",
       lambda: edit(lambda d: d["cards"].remove(row(d, "The Hidden Bins"))),
       "NOT ESTABLISHED"))

r(case("the mapping is emptied",
       lambda: edit(lambda d: d.__setitem__("cards", [])),
       "NOT ESTABLISHED"))

# ---- the positive control ------------------------------------------------
print("-" * 78)
got, _ = verdict()
hit = got == "GOVERNED"
r(hit)
print("  %s %-16s POSITIVE CONTROL: the untouched tree is governed" %
      ("CAUGHT " if hit else "MISSED ", got))

after = {f: hashlib.sha256(f.read_bytes()).hexdigest() for f in TOUCHED}
intact = all(before[f] == after[f] for f in TOUCHED)
print("=" * 78)
print("%d of %d checks passed" % (sum(1 for x in results if x), len(results)))
print("every touched file is byte-identical after the proof: %s"
      % ("YES" if intact else "NO"))
for f in TOUCHED:
    print("  %-36s %s" % (f.name, after[f][:12]))
sys.exit(0 if all(results) and intact else 1)
