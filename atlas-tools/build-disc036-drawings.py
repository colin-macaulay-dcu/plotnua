#!/usr/bin/env python3
"""DISC-036 · Extend the House: the PlotNua drawings (vector, no AI, no third-party imagery).

Writes the page's drawings between their markers in discovery-extend-the-house.html:
  EH-HERO-BEFORE / EH-HERO-POSSIBLE   the hero pair: one rear elevation, drawn from ONE shared geometry, so the
                                      two layers can only differ where the extension is (same house, viewpoint,
                                      garden and surroundings by construction)
  EH-PLAN                             chapter 01: a ground-floor plan before and after (not to scale)
  EH-TYPE-1 .. EH-TYPE-6              chapter 02: six footprint diagrams (house grey, extension terracotta)

The hero pair is an interim PlotNua drawing for the private preview. It is designed to be replaced by a
founder-made Before / Possible image pair (the established practice for Discovery heroes); nothing else on
the page depends on it.

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


def hero(possible):
    W, H = 1600, 900
    g = []
    a = g.append
    a('<svg class="eh-draw" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid slice" role="img" aria-hidden="true" focusable="false">' % (W, H))
    a('<defs><linearGradient id="ehSky%s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
      % ("P" if possible else "B", SKY_T, SKY_B))
    a('<radialGradient id="ehGlow%s" cx=".5" cy=".55" r=".7"><stop offset="0" stop-color="%s" stop-opacity=".95"/><stop offset="1" stop-color="#C9893F" stop-opacity=".75"/></radialGradient></defs>'
      % ("P" if possible else "B", WARM))
    sid = "P" if possible else "B"
    a('<rect width="%d" height="%d" fill="url(#ehSky%s)"/>' % (W, H, sid))
    a('<rect x="0" y="660" width="%d" height="%d" fill="%s"/>' % (W, H - 660, LAWN))
    a('<path d="M1350 700 C1420 600 1500 640 1600 590 V700Z" fill="#2E372B"/>')       # far hedge, right
    a('<g transform="translate(-170 0)">')                                             # house centred in the frame
    # distant trees and the neighbour's house (identical in both)
    a('<path d="M0 560 C120 520 180 540 260 515 C340 492 400 520 470 505 L470 640 L0 640Z" fill="#2C302B"/>')
    a('<path d="M1180 520 C1260 480 1330 505 1400 488 C1480 470 1540 500 1600 490 L1600 640 L1180 640Z" fill="#2C302B"/>')
    # the semi-detached pair: neighbour (left half, dimmer) and the house
    a('<path d="M310 330 L560 190 L810 330 Z" fill="%s"/>' % ROOF)
    a('<path d="M810 330 L1060 190 L1310 330 Z" fill="%s"/>' % ROOF)
    a('<rect x="560" y="150" width="40" height="70" fill="%s"/><rect x="1060" y="150" width="40" height="70" fill="%s"/>' % ("#4A4846", "#4A4846"))
    a('<rect x="330" y="330" width="480" height="330" fill="#4B4A45"/>')     # neighbour
    a('<rect x="810" y="330" width="480" height="330" fill="%s"/>' % RENDER)   # the house
    a('<path d="M810 330 V660" stroke="#2A2B2E" stroke-width="3"/>')
    # neighbour's openings (unchanged)
    for x in (400, 640):
        a('<rect x="%d" y="380" width="96" height="110" fill="%s" stroke="#6E6A61" stroke-width="4"/>' % (x, GLASS))
    a('<rect x="400" y="540" width="120" height="96" fill="%s" stroke="#6E6A61" stroke-width="4"/>' % GLASS)
    a('<rect x="640" y="530" width="70" height="130" fill="#3A3833" stroke="#6E6A61" stroke-width="4"/>')
    # the house: first-floor windows (unchanged in both)
    for x in (880, 1120):
        a('<rect x="%d" y="380" width="100" height="112" fill="%s" stroke="%s" stroke-width="5"/>' % (x, GLASS, LINE))
        a('<path d="M%d 380 V492" stroke="%s" stroke-width="3"/>' % (x + 50, LINE))
    a('<path d="M1300 330 V660" stroke="#3F3E3A" stroke-width="8"/>')                       # downpipe
    # ground line
    a('<path d="M250 660 H1850" stroke="#2A2B2E" stroke-width="3"/>')
    # boundary fences (both)
    a('<path d="M300 600 V700 M1320 600 V700" stroke="#6B5A47" stroke-width="6"/>')
    for x in range(250, 300, 22):
        a('<rect x="%d" y="610" width="18" height="90" fill="#5B4C3D"/>' % x)
    for x in range(1330, 1600, 22):
        a('<rect x="%d" y="610" width="18" height="90" fill="#5B4C3D"/>' % x)
    # garden tree, right (both)
    a('<path d="M1460 700 V560" stroke="#4A3D31" stroke-width="12"/>')
    a('<circle cx="1460" cy="520" r="78" fill="#3E4B39"/><circle cx="1410" cy="560" r="52" fill="#384534"/><circle cx="1512" cy="556" r="56" fill="#41503B"/>')
    if not possible:
        # BEFORE: the original ground floor - a small kitchen window, a back door, a narrow patio, a rotary line
        a('<rect x="880" y="545" width="130" height="92" fill="%s" stroke="%s" stroke-width="5"/>' % (GLASS, LINE))
        a('<path d="M945 545 V637" stroke="%s" stroke-width="3"/>' % LINE)
        a('<rect x="1100" y="520" width="80" height="140" fill="#3D3B36" stroke="%s" stroke-width="5"/>' % LINE)
        a('<rect x="1112" y="535" width="56" height="44" fill="%s"/>' % GLASS)
        a('<rect x="830" y="660" width="460" height="26" fill="#6E6A61"/>')
        for x in range(830, 1290, 46):
            a('<path d="M%d 660 V686" stroke="#57544D" stroke-width="2"/>' % x)
        a('<path d="M1225 700 V610 M1185 620 L1265 600 M1185 600 L1265 620" stroke="#8A857A" stroke-width="3" fill="none"/>')
        a('<path d="M560 560 l-30 40 h60z" fill="#4C5A44"/>')                                # a shrub (neighbour)
    else:
        # POSSIBLE: a single-storey rear extension across the house, below the first-floor windows,
        # anthracite cladding, timber soffit, full-width sliding glazing with warm light, a roof light,
        # and a terrace stepping down to the lawn. The first floor, roof and neighbour are untouched.
        a('<rect x="800" y="520" width="500" height="140" fill="#2F3134"/>')                  # the extension
        a('<rect x="800" y="508" width="500" height="16" fill="#3A3C40"/>')                   # parapet / coping
        a('<rect x="1040" y="494" width="150" height="18" fill="#4A4C51" stroke="%s" stroke-width="2"/>' % LINE)  # roof light upstand
        a('<rect x="1050" y="497" width="130" height="10" fill="%s" opacity=".75"/>' % WARM)
        a('<rect x="830" y="540" width="440" height="20" fill="#8A6A4A"/>')                   # timber soffit
        a('<rect x="840" y="560" width="420" height="100" fill="url(#ehGlow%s)"/>' % sid)     # glazing, lit
        for x in (945, 1050, 1155):
            a('<path d="M%d 560 V660" stroke="#2B2D31" stroke-width="5"/>' % x)
        a('<path d="M840 560 H1260" stroke="#2B2D31" stroke-width="4"/>')
        # inside: a table and pendant lights, in silhouette
        a('<path d="M900 628 H1020 M915 628 V660 M1005 628 V660" stroke="#5A3E25" stroke-width="6"/>')
        a('<circle cx="935" cy="578" r="6" fill="#FFF3D6"/><circle cx="985" cy="578" r="6" fill="#FFF3D6"/>')
        a('<path d="M935 560 V572 M985 560 V572" stroke="#5A3E25" stroke-width="2"/>')
        a('<path d="M1090 660 V612 h70 v48" fill="#6A4A30"/>')                              # kitchen island
        # light spilling onto a stone terrace
        a('<path d="M840 660 L1260 660 L1300 700 L800 700 Z" fill="#8C857A"/>')
        a('<path d="M860 660 L1240 660 L1280 698 L820 698 Z" fill="%s" opacity=".18"/>' % WARM)
        for x in range(820, 1290, 58):
            a('<path d="M%d 660 L%d 700" stroke="#6E685F" stroke-width="2"/>' % (x + 20, x))
        a('<path d="M1300 700 v14 h-500 v-14" fill="#76716A"/>')                             # step
        a('<path d="M560 560 l-30 40 h60z" fill="#4C5A44"/>')
        # low planting at the terrace edge
        for x, r in ((1310, 20), (1338, 16), (790, 18), (768, 14)):
            a('<circle cx="%d" cy="%d" r="%d" fill="#4C5E45"/>' % (x, 700 - r + 6, r))
    a('</g></svg>')
    return "".join(g)


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


BLOCKS = {"EH-HERO-BEFORE": hero(False), "EH-HERO-POSSIBLE": hero(True),
          "EH-PLAN-BEFORE": plan(False), "EH-PLAN-AFTER": plan(True)}
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
