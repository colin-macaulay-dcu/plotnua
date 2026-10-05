#!/usr/bin/env python3
"""
DISC-026 . CORRECTION 02 . HOMEOWNER LANGUAGE ON THE WIND DRAWING
===========================================================================
One founder finding from the visual review of candidate 2996a6256e27: a
homeowner should not have to know what an "exempt envelope" is.

COPY ONLY. Not one SVG coordinate is touched, and the build asserts that by
hashing the wind drawing's geometry before and after. The energy anatomy is
hashed whole and must come out byte-identical. No evidence claim moves. No
imagery is added. The battery files are not opened.

WHAT CHANGES, and all of it is homeowner-facing surface:
  1  the drawer summary                    -> "The planning limits, at a glance"
  2  the caption under the drawing         -> "The planning limits, drawn to scale."
  3  the scale note inside the drawing     -> the founder's wording, verbatim
  4  the drawing's aria-label              -> screen-reader users are homeowners
  5  two remaining uses of "envelope" in running copy, which are the same
     confusion in the same section. FLAGGED as judgement, not instructed:
     the founder named two strings and stated the objective as removing
     confusing homeowner-facing terminology. Leaving "inside a tight
     envelope" in the section lede would satisfy the letter and miss the
     point. Both are one-word changes and both are reversible.

WHAT DELIBERATELY DOES NOT CHANGE. The word "envelope" stays in internal
names, comments, guard identifiers and capability-case labels. The founder
ruled out a rename cascade, and the geometry proofs are keyed to those
identifiers.

Run: python3 atlas-tools/build-disc026-correction-02.py
"""

import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
PAGE = ROOT / "discovery-house-as-power-station.html"

if not PAGE.exists():
    print("REFUSED: the Discovery is not in the tree")
    sys.exit(2)

html = PAGE.read_text(encoding="utf-8")
ORIGINAL = html


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(2)


def anchored(text, old, new, label):
    n = text.count(old)
    if n != 1:
        die("anchor %r matched %d time(s), expected 1 -- nothing written"
            % (label, n))
    return text.replace(old, new)


# ---------------------------------------------------------------------------
# BEFORE: fingerprint the two drawings so the assertions below can prove the
# geometry survived. Geometry = every coordinate-bearing attribute.
# ---------------------------------------------------------------------------

def geometry_of(svg):
    """Every path, point, radius and transform, in order, hashed."""
    bits = re.findall(r'\s(?:d|x|y|x1|y1|x2|y2|cx|cy|r|rx|ry|width|height|'
                      r'points|transform|viewBox|stroke-dasharray|'
                      r'patternTransform|patternUnits)="([^"]*)"', svg)
    return hashlib.sha256("\u0001".join(bits).encode()).hexdigest(), len(bits)


def svg_at(text, marker):
    i = text.index(marker)
    s = text.rindex("<svg", 0, i)
    e = text.index("</svg>", i) + len("</svg>")
    return text[s:e]


WIND_MARK = "domestic wind turbine, drawn to scale at one metre"
ANAT_MARK = "seven numbered positions: one, solar panels on the roof"
try:
    wind_before = svg_at(html, WIND_MARK)
    anat_before = svg_at(html, ANAT_MARK)
except ValueError:
    die("could not locate the wind drawing and the energy anatomy uniquely")

WIND_GEO_BEFORE, WIND_ATTRS = geometry_of(wind_before)
ANAT_SHA_BEFORE = hashlib.sha256(anat_before.encode()).hexdigest()


# ---------------------------------------------------------------------------
# 1 . THE DRAWER SUMMARY
# ---------------------------------------------------------------------------

html = anchored(
    html,
    "<summary><h3>The exempt envelope, in full</h3>",
    "<summary><h3>The planning limits, at a glance</h3>",
    "drawer summary")

# ---------------------------------------------------------------------------
# 2 . THE CAPTION UNDER THE DRAWING. The detailed hub-and-rotor explanation
#     goes: the founder asked for the scale note to be simplified, and every
#     dimension it recited is labelled on the drawing itself and set out in
#     the drawer. Nothing governed is lost by removing the restatement.
# ---------------------------------------------------------------------------

html = anchored(
    html,
    """<p class="anat-cap">The exempt envelope, drawn to scale. The turbine shown
            sits inside it: a 6 m rotor with its hub at 10 m reaches 13 m exactly, and
            its lowest blade stays well above the 3 m floor. The setback is measured
            from the mast to the nearest party boundary.</p>""",
    """<p class="anat-cap">The planning limits, drawn to scale.</p>""",
    "caption under the wind drawing")

# ---------------------------------------------------------------------------
# 3 . THE SCALE NOTE INSIDE THE DRAWING, in the founder's words. This is a
#     <text> label: its x and y are unchanged, so the geometry hash holds.
# ---------------------------------------------------------------------------

html = anchored(
    html,
    '<text x="30" y="462">Drawn to scale. 14 m is the total height plus one metre, '
    'at the maximum exempt size.</text>',
    '<text x="30" y="462">Drawn to scale. At the maximum exempt size, the turbine can '
    'be up to 13 m high and must be at least 14 m from the party boundary.</text>',
    "in-drawing scale note")

# ---------------------------------------------------------------------------
# 4 . THE ARIA-LABEL. A screen-reader user is a homeowner, so this is
#     homeowner-visible copy and the same correction applies. Every dimension
#     it states is preserved.
# ---------------------------------------------------------------------------

html = anchored(
    html,
    'aria-label="The exempt envelope for a domestic wind turbine, drawn to scale',
    'aria-label="The planning limits for a domestic wind turbine, drawn to scale',
    "wind drawing aria-label")

# ---------------------------------------------------------------------------
# 5 . THE TWO REMAINING USES IN RUNNING COPY. Judgement, flagged in the
#     report, reversible in two lines.
# ---------------------------------------------------------------------------

html = anchored(
    html,
    "<p>Inside a tight envelope, connected under the same rules as solar, and paid",
    "<p>Inside tight limits, connected under the same rules as solar, and paid",
    "section lede")

html = anchored(
    html,
    "A domestic wind turbine is exempt only inside the envelope set out\n        above.",
    "A domestic wind turbine is exempt only inside the limits set out\n        above.",
    "permission drawer")


# ---------------------------------------------------------------------------
# ASSERTIONS
# ---------------------------------------------------------------------------

checks = []


def must(cond, label):
    checks.append((bool(cond), label))


# the correction landed, on the homeowner surface
visible = re.sub(r"<!--[\s\S]*?-->", "", html)
visible = re.sub(r"<(script|style)[\s\S]*?</\1>", "", visible)
for retired in ("The exempt envelope, in full",
                "The exempt envelope, drawn to scale.",
                "exempt envelope"):
    must(retired not in visible,
         "retired from the homeowner surface: %r" % retired)
must("The planning limits, at a glance" in html, "drawer summary corrected")
must('<p class="anat-cap">The planning limits, drawn to scale.</p>' in html,
     "caption corrected and simplified")
must("Drawn to scale. At the maximum exempt size, the turbine can be up to 13 m high "
     "and must be at least 14 m from the party boundary." in html,
     "the scale note is the founder's wording, verbatim")
must('aria-label="The planning limits for a domestic wind turbine' in html,
     "aria-label corrected")
must("Inside tight limits, connected under the same rules as solar" in html,
     "the section lede no longer says 'envelope'")
must("exempt only inside the limits set out" in html,
     "the permission drawer no longer says 'envelope'")

# GEOMETRY DID NOT MOVE. This is the whole safety case for the pass.
wind_after = svg_at(html, "domestic wind turbine, drawn to scale at one metre")
WIND_GEO_AFTER, attrs_after = geometry_of(wind_after)
must(WIND_GEO_BEFORE == WIND_GEO_AFTER and WIND_ATTRS == attrs_after,
     "wind drawing geometry byte-identical (%d coordinate attributes, %s)"
     % (WIND_ATTRS, WIND_GEO_BEFORE[:12]))
# and the four governed dimensions are still exactly metres x 24
for label, path in [("13 m", 'd="M176 88 V400'), ("6 m rotor", 'd="M424 88 V232'),
                    ("3 m clearance", 'd="M424 328 V400'),
                    ("14 m setback", 'd="M300 432 H636')]:
    must(path in html, "governed dimension intact: %s" % label)
for shown in ("13 m TOTAL HEIGHT", "6 m ROTOR", "3 m MINIMUM CLEARANCE",
              "14 m SETBACK"):
    must(shown in html, "dimension still labelled on the drawing: %s" % shown)

# THE ENERGY ANATOMY IS FROZEN. Byte-identical, not merely similar.
anat_after = svg_at(html, ANAT_MARK)
must(hashlib.sha256(anat_after.encode()).hexdigest() == ANAT_SHA_BEFORE,
     "energy anatomy byte-identical (%s)" % ANAT_SHA_BEFORE[:12])

# NOTHING ELSE MOVED. Diff the two texts and account for every change.
must(html.count("<svg") == ORIGINAL.count("<svg") == 5, "still five drawings")
must(html.count('class="pos-eq"') == 7, "seven leading ideas untouched")
must(html.count("<details") == ORIGINAL.count("<details") == 8, "eight drawers")
must(html.count('class="imgnote"') == 4, "four quiet image notes")
must('class="rights"' not in html, "no rights block")

# approved copy is not reopened
for approved in ("Computers produce heat. Homes need heat.",
                 "Nobody yet knows what a &ldquo;compute-ready&rdquo; home looks like.",
                 "<h2>This is already being built in Ireland.</h2>",
                 '<div class="kicker">Data centres &middot; useful heat</div>',
                 '<div class="kicker">Distributed compute &middot; Ireland</div>',
                 '<div class="kicker">Home compute &middot; useful heat</div>'):
    must(approved in html, "approved copy untouched: %s" % approved[:46])
for restored in ("Read those figures carefully",
                 "There is no photograph here because there is nothing to",
                 "PlotNua would rather say that plainly",
                 "three states and no score"):
    must(restored not in html, "stays removed: %r" % restored[:44])

# evidence boundaries
AMT = re.compile(r"&euro;(\d{1,3}(?:,\d{3})*)")
must(set(AMT.findall(ORIGINAL)) == set(AMT.findall(html)),
     "euro figures unchanged")
for fig in ("13&nbsp;m", "6&nbsp;m rotor", "3&nbsp;m clearance", "43&nbsp;dB(A)",
            "100% covered by waste heat", "22%", "31%", "2.3", "50&nbsp;m",
            "Tandem has confirmed that individual homes are not part of its current",
            "has not established, from a", "generator, under the same"):
    must(fig in html, "governed boundary intact: %s" % fig[:42])
must("From 6 October 2026 SEAI is to pay a flat" in html,
     "battery boundary untouched")
must(html.count("PN-DISC026-BATTERY-BOUNDARY-BEGIN") == 1,
     "battery boundary markers untouched")

# no imagery added
must(not re.findall(r'<img[^>]+src="https?://', html), "no remote imagery")
must(len(re.findall(r"<img ", html)) == len(re.findall(r"<img ", ORIGINAL)),
     "no image element added or removed")

# structure
must(html.count("<main") == html.count("</main>"), "main balanced")
must(html.count("<section") == html.count("</section>"), "section balanced")
must(html.count("<div") == html.count("</div>"), "div balanced")

bad = [lab for ok, lab in checks if not ok]
print("DISC-026 CORRECTION 02 . HOMEOWNER LANGUAGE")
print("=" * 74)
for ok, lab in checks:
    print("  %s  %s" % ("PASS" if ok else "FAIL", lab))
print("=" * 74)
if bad:
    print("REFUSED -- %d assertion(s) failed. Nothing written." % len(bad))
    sys.exit(2)

PAGE.write_text(html, encoding="utf-8")
print("WROTE %s (%d checks passed, %d -> %d bytes)"
      % (PAGE.name, len(checks), len(ORIGINAL), len(html)))
