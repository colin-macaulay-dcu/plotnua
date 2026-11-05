#!/usr/bin/env python3
"""DISC-036 · Extend the House: the PlotNua drawings (vector, no AI, no third-party imagery).

Writes the page's drawings between their markers in discovery-extend-the-house.html:
  EH-PLAN                             chapter 01: a ground-floor plan before and after (not to scale)
  EH-TYPE-1 .. EH-TYPE-6              chapter 02: six footprint diagrams (house grey, extension terracotta)

The interim drawn hero pair was retired on 5 Nov 2026 when the founder's Before / Possible image pair was
integrated (atlas-tools/build-disc036-images.py); the hero is no longer built here.

    python3 atlas-tools/build-disc036-drawings.py           write
    python3 atlas-tools/build-disc036-drawings.py --check   exit 1 if the page is not built from this file
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "discovery-extend-the-house.html"
CHECK = "--check" in sys.argv

# ---- palette (the anthracite system: ink ground, ivory line, terracotta accent, warm light) -------------
SKY_T, SKY_B = "#24262A", "#3B3732"
LINE = "#E7DED0"
RENDER = "#5A5852"
ROOF = "#33353A"
GLASS = "#1E2023"
LAWN = "#36412F"
WARM = "#F0C988"
TERRA = "#CF8566"



def plan(after):
    """Ground-floor plan, not to scale: the same house; after adds a rear kitchen-dining-living room."""
    g = ['<svg viewBox="0 0 420 340" role="img" aria-labelledby="ehPlan%sT"><title id="ehPlan%sT">%s</title>' % (
        "A" if after else "B", "A" if after else "B",
        "After: the back of the house opened into one kitchen, dining and living room with wide doors to the garden. Not to scale."
        if after else "Before: a small kitchen and a separate back room at the rear of the house, with one door to the garden. Not to scale.")]
    a = g.append
    a('<rect x="60" y="30" width="300" height="190" fill="none" stroke="%s" stroke-width="5"/>' % LINE)
    a('<path d="M60 125 H200 M200 30 V220 M200 150 H360" stroke="%s" stroke-width="3"/>' % LINE)
    a('<text x="130" y="82" text-anchor="middle" class="eh-pl">Front room</text>')
    a('<text x="280" y="96" text-anchor="middle" class="eh-pl">Hall · stairs</text>')
    if not after:
        a('<text x="130" y="178" text-anchor="middle" class="eh-pl">Back room</text>')
        a('<text x="280" y="190" text-anchor="middle" class="eh-pl">Kitchen</text>')
        a('<path d="M300 220 h28" stroke="#2B2D31" stroke-width="7"/>')                      # back door
        a('<path d="M300 220 a28 28 0 0 0 28 -28" stroke="%s" stroke-width="1.5" fill="none"/>' % LINE)
        a('<rect x="60" y="220" width="300" height="80" fill="%s" opacity=".18"/>' % LAWN)
        a('<text x="210" y="268" text-anchor="middle" class="eh-pl is-soft">Garden</text>')
    else:
        a('<rect x="60" y="220" width="300" height="80" fill="%s" fill-opacity=".16" stroke="%s" stroke-width="4"/>' % (TERRA, TERRA))
        a('<path d="M60 150 H200" stroke="none"/>')
        a('<path d="M200 150 V220" stroke="#2B2D31" stroke-width="6" stroke-dasharray="6 6"/>')
        a('<text x="210" y="252" text-anchor="middle" class="eh-pl">Kitchen · dining · living</text>')
        a('<text x="130" y="186" text-anchor="middle" class="eh-pl is-soft">Utility · WC</text>')
        a('<text x="280" y="190" text-anchor="middle" class="eh-pl is-soft">Opened up</text>')
        a('<path d="M90 300 H330" stroke="%s" stroke-width="7"/>' % WARM)                    # glazing
        a('<text x="210" y="326" text-anchor="middle" class="eh-pl is-soft">Wide doors to the garden</text>')
    a('</svg>')
    return "".join(g)


TYPES = [
    # (id, title for the drawing, extension shape as svg)
    ("1", "A rear extension: added across the back of the house.",
     '<rect x="50" y="140" width="140" height="44" class="eh-x"/>'),
    ("2", "A side extension: added beside the house, where there is room at the side.",
     '<rect x="190" y="40" width="44" height="100" class="eh-x"/>'),
    ("3", "A side-return extension: filling the narrow passage beside a back room.",
     '<path d="M150 90 h40 v50 h-40z" class="eh-x"/>'),
    ("4", "A kitchen extension: usually a rear or side-return extension planned around a new kitchen.",
     '<rect x="50" y="140" width="140" height="44" class="eh-x"/><path d="M60 150 h44 v14 h-44z" class="eh-k"/>'),
    ("5", "A wrap-around extension: around the back and along one side, in an L.",
     '<path d="M50 140 h184 v44 h-184z M190 70 h44 v70 h-44z" class="eh-x"/>'),
    ("6", "A two-storey extension: a ground-floor room with another room above it.",
     '<rect x="50" y="140" width="140" height="44" class="eh-x"/><rect x="50" y="140" width="70" height="44" class="eh-x2"/>'),
]


def typ(i, title, shape):
    note = '<text x="120" y="212" text-anchor="middle" class="eh-pl is-soft">two floors</text>' if i == "6" else ""
    return ('<svg viewBox="0 0 260 220" role="img" aria-labelledby="ehType%sT"><title id="ehType%sT">%s Not to scale.</title>'
            '<path d="M20 196 H240" class="eh-gr"/><rect x="50" y="40" width="140" height="100" class="eh-h"/>%s'
            '<text x="120" y="96" text-anchor="middle" class="eh-pl is-soft">house</text>%s</svg>') % (i, i, title, shape, note)


BLOCKS = {"EH-PLAN-BEFORE": plan(False), "EH-PLAN-AFTER": plan(True)}
for i, t, s in TYPES:
    BLOCKS["EH-TYPE-" + i] = typ(i, t, s)


def build(page):
    for k, v in BLOCKS.items():
        pat = re.compile(r"(<!--%s-->).*?(<!--/%s-->)" % (k, k), re.S)
        if not pat.search(page):
            sys.exit("build-disc036-drawings: marker %s not found" % k)
        page = pat.sub(lambda m: m.group(1) + v + m.group(2), page)
    return page


cur = PAGE.read_text(encoding="utf-8")
new = build(cur)
if CHECK:
    print("DISC-036 DRAWINGS · " + ("OK (%d drawings, vector only)" % len(BLOCKS) if new == cur else "NOT BUILT"))
    sys.exit(0 if new == cur else 1)
PAGE.write_text(new, encoding="utf-8")
print("built %d drawings into %s" % (len(BLOCKS), PAGE.name))
