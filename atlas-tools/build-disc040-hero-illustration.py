#!/usr/bin/env python3
"""DISC-040 The Home You Build: interim Before/Possible hero illustration (PRIVATE PREVIEW ONLY).

Draws the same Irish rural site twice, at dusk, from one fixed viewpoint:
  BEFORE   - an undeveloped field behind a dry-stone wall and a galvanised field gate,
             hedgerows, a hawthorn, rolling fields and western hills.
  POSSIBLE - the same field with a contemporary low-energy home: two pitched, dark-roofed
             volumes (larch and lime render) joined by a glazed link, a gravel drive through
             the original gate, native planting and low lights. The wall, gate and hawthorn stay.

Written as code (vector drawing by Claude), the precedent of the DISC-038 interim section drawing.
It is an illustration, not a design, not to scale and not any product or real site.
Deterministic: a fixed random seed, so every run writes identical SVG text.

Outputs (assets/disc040/img/): DISC-040-{BEFORE,POSSIBLE}.svg (1536x960 masters), and via
rsvg-convert + Pillow: -1536/-1376/-1024/-768 .webp and -1024.jpg, phone 4:5 -M-819.webp,
and DISC-040-og-1200x630.jpg (POSSIBLE).
"""
import math, random, subprocess, sys
from pathlib import Path

W, H = 1536, 960
OUT = Path(__file__).resolve().parent.parent / "assets" / "disc040" / "img"


def p(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- shared landscape
def defs():
    return """
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2B3442"/>
    <stop offset=".38" stop-color="#5A5E6A"/>
    <stop offset=".66" stop-color="#B98E6E"/>
    <stop offset=".82" stop-color="#E7B987"/>
    <stop offset="1" stop-color="#F3D2A2"/>
  </linearGradient>
  <radialGradient id="sunglow" cx="0.30" cy="0.47" r="0.55">
    <stop offset="0" stop-color="#FFE4B5" stop-opacity=".85"/>
    <stop offset=".35" stop-color="#F4C08A" stop-opacity=".35"/>
    <stop offset="1" stop-color="#F4C08A" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="hillFar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7C7B86"/><stop offset="1" stop-color="#8E8686"/></linearGradient>
  <linearGradient id="hillMid" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5E6662"/><stop offset="1" stop-color="#6E7162"/></linearGradient>
  <linearGradient id="fieldFar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6F7A55"/><stop offset="1" stop-color="#55633F"/></linearGradient>
  <linearGradient id="meadow" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#7C8452"/><stop offset=".35" stop-color="#5E6B3A"/><stop offset="1" stop-color="#2E3820"/>
  </linearGradient>
  <linearGradient id="meadowLight" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#F2C98F" stop-opacity=".30"/><stop offset=".55" stop-color="#F2C98F" stop-opacity=".06"/><stop offset="1" stop-color="#F2C98F" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="vignette" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0F0E0A" stop-opacity=".25"/><stop offset=".25" stop-color="#0F0E0A" stop-opacity="0"/>
    <stop offset=".78" stop-color="#0F0E0A" stop-opacity="0"/><stop offset="1" stop-color="#0F0E0A" stop-opacity=".45"/>
  </linearGradient>
  <linearGradient id="glassGlow" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#F7C983"/><stop offset=".6" stop-color="#E9A15C"/><stop offset="1" stop-color="#B9733F"/>
  </linearGradient>
  <linearGradient id="glassGlowSoft" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#EDB574"/><stop offset="1" stop-color="#D38E52"/>
  </linearGradient>
  <linearGradient id="larch" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8A6544"/><stop offset="1" stop-color="#6E4F35"/></linearGradient>
  <linearGradient id="larchGable" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#A7805A"/><stop offset="1" stop-color="#94704D"/></linearGradient>
  <linearGradient id="render" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#E4DACB"/><stop offset="1" stop-color="#C9BEAF"/></linearGradient>
  <linearGradient id="renderSide" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#B5AA9B"/><stop offset="1" stop-color="#9E9486"/></linearGradient>
  <linearGradient id="roof" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4A4A4C"/><stop offset="1" stop-color="#2C2C2F"/></linearGradient>
  <linearGradient id="gravel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#B8A88E"/><stop offset="1" stop-color="#7E705C"/></linearGradient>
  <radialGradient id="lamp"><stop offset="0" stop-color="#FFE2A8" stop-opacity=".95"/><stop offset=".4" stop-color="#F5BE72" stop-opacity=".35"/><stop offset="1" stop-color="#F5BE72" stop-opacity="0"/></radialGradient>
  <radialGradient id="spill" cx=".5" cy="0" r=".9"><stop offset="0" stop-color="#F3B56C" stop-opacity=".45"/><stop offset="1" stop-color="#F3B56C" stop-opacity="0"/></radialGradient>
  <filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="10"/></filter>
  <filter id="soft2" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3"/></filter>
</defs>"""


def sky_and_hills():
    s = [f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
         f'<rect width="{W}" height="{H}" fill="url(#sunglow)"/>']
    # soft clouds
    rnd = random.Random(7)
    for i in range(9):
        cx, cy = rnd.uniform(-50, W + 50), rnd.uniform(60, 300)
        rx, ry = rnd.uniform(140, 320), rnd.uniform(14, 30)
        op = rnd.uniform(.18, .32)
        col = "#E9C8A6" if cy > 200 else "#8D8F9C"
        s.append(f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" fill="{col}" opacity="{op:.2f}" filter="url(#soft)"/>')
    # far mountains
    far = [(0, 452)]
    for x in range(0, W + 1, 32):
        y = 440 - 46 * math.sin(x / 210.0) - 24 * math.sin(x / 77.0 + 1.3) - (38 if 820 < x < 1180 else 0) * math.sin((x - 820) / 360 * math.pi)
        far.append((x, y))
    far += [(W, 540), (0, 540)]
    s.append(f'<polygon points="{p(far)}" fill="url(#hillFar)" opacity=".85"/>')
    mid = []
    for x in range(0, W + 1, 24):
        y = 488 - 26 * math.sin(x / 160.0 + .6) - 14 * math.sin(x / 53.0)
        mid.append((x, y))
    mid += [(W, 600), (0, 600)]
    s.append(f'<polygon points="{p(mid)}" fill="url(#hillMid)"/>')
    # patchwork fields with hedgerow lines
    fields = []
    for x in range(0, W + 1, 24):
        y = 520 - 10 * math.sin(x / 130.0) - 6 * math.sin(x / 41.0 + 2)
        fields.append((x, y))
    fields += [(W, 640), (0, 640)]
    s.append(f'<polygon points="{p(fields)}" fill="url(#fieldFar)"/>')
    rnd = random.Random(11)
    # hedgerows: irregular dark lines across far fields
    for row in range(4):
        y0 = 528 + row * 22
        pts = []
        for x in range(-20, W + 40, 18):
            pts.append((x, y0 + 6 * math.sin(x / 90 + row) + rnd.uniform(-1.5, 1.5)))
        s.append(f'<polyline points="{p(pts)}" fill="none" stroke="#33402A" stroke-width="{3.2 + row*1.1:.1f}" stroke-linecap="round" opacity=".85"/>')
    for i in range(16):  # vertical field boundaries
        x = rnd.uniform(0, W)
        s.append(f'<path d="M{x:.0f} {528 + rnd.uniform(0,10):.0f} q {rnd.uniform(-20,20):.0f} 30 {rnd.uniform(-30,30):.0f} 60" stroke="#3A4630" stroke-width="2.4" fill="none" opacity=".8"/>')
    for i in range(40):  # far trees
        x, y = rnd.uniform(0, W), rnd.uniform(520, 600)
        r = rnd.uniform(5, 11)
        s.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r:.1f}" ry="{r*0.8:.1f}" fill="#2F3A26" opacity=".9"/>')
    return "\n".join(s)


def meadow():
    s = []
    top = []
    for x in range(0, W + 1, 16):
        top.append((x, 602 - 18 * math.sin(x / 300.0 + .4) + 10 * math.sin(x / 120.0)))
    top += [(W, H), (0, H)]
    s.append(f'<polygon points="{p(top)}" fill="url(#meadow)"/>')
    s.append(f'<polygon points="{p(top)}" fill="url(#meadowLight)"/>')
    # boundary hedge behind the site (right) and left
    rnd = random.Random(21)
    for (x0, x1, y) in [(-20, 560, 600), (1240, W + 20, 598)]:
        for i in range(int((x1 - x0) / 9)):
            x = x0 + i * 9 + rnd.uniform(-3, 3)
            r = rnd.uniform(9, 17)
            s.append(f'<circle cx="{x:.0f}" cy="{y - rnd.uniform(0, 16):.0f}" r="{r:.1f}" fill="{rnd.choice(["#2C3822","#33412A","#3B4A2F","#283320"])}"/>')
    return "\n".join(s)


def grass(seed, skip=None, n=4200):
    """Short strokes, larger and denser towards the viewer. skip(x,y) -> True to omit."""
    rnd = random.Random(seed)
    cols = ["#6E7A43", "#7D8A4B", "#5C6A37", "#8C8F55", "#A49A5E", "#4D5A30", "#B9A56A"]
    out = []
    for _ in range(n):
        t = rnd.random() ** 0.6
        y = lerp(610, H + 10, t)
        x = rnd.uniform(-10, W + 10)
        if skip and skip(x, y):
            continue
        h = lerp(4, 30, t) * rnd.uniform(.6, 1.3)
        lean = rnd.uniform(-.35, .35) * h
        w = lerp(.7, 2.2, t)
        c = rnd.choice(cols)
        op = lerp(.45, .95, t)
        out.append(f'<path d="M{x:.1f} {y:.1f} q {lean*0.3:.1f} {-h*0.55:.1f} {lean:.1f} {-h:.1f}" stroke="{c}" stroke-width="{w:.2f}" fill="none" stroke-linecap="round" opacity="{op:.2f}"/>')
    # rushes / seed heads catching light
    for _ in range(140):
        t = rnd.random() ** 0.8
        y = lerp(640, H, t); x = rnd.uniform(0, W)
        if skip and skip(x, y):
            continue
        h = lerp(10, 46, t)
        out.append(f'<path d="M{x:.1f} {y:.1f} l {rnd.uniform(-4,4):.1f} {-h:.1f}" stroke="#D9BE84" stroke-width="{lerp(.6,1.6,t):.2f}" opacity=".55"/>')
    return "\n".join(out)


def stone_wall():
    """Dry-stone wall across the foreground, gap with a galvanised gate at left."""
    rnd = random.Random(31)
    s = []
    def wall_y(x):
        return 812 + 0.035 * x - 14 * math.sin(x / 420)
    segs = [(-30, 238), (432, W + 30)]
    for (a, b) in segs:
        x = a
        while x < b:
            for course in range(4):
                w = rnd.uniform(26, 52)
                hgt = rnd.uniform(15, 22)
                yb = wall_y(x) - course * 17
                col = rnd.choice(["#8E8A80", "#7B776D", "#9C978B", "#6D6A62", "#A8A194", "#85806F"])
                rx = rnd.uniform(4, 9)
                s.append(f'<rect x="{x:.1f}" y="{yb - hgt:.1f}" width="{w:.1f}" height="{hgt:.1f}" rx="{rx:.1f}" fill="{col}" stroke="#4E4B45" stroke-width="1.2"/>')
            x += rnd.uniform(26, 44)
        # coping
    for (a, b) in segs:
        x = a
        while x < b:
            w = rnd.uniform(14, 22)
            yb = wall_y(x) - 68
            s.append(f'<rect x="{x:.1f}" y="{yb - 18:.1f}" width="{w:.1f}" height="22" rx="4" fill="{rnd.choice(["#6F6B63","#8A857A","#7C786E"])}" stroke="#4A4741" stroke-width="1" transform="rotate({rnd.uniform(-8,8):.1f} {x+w/2:.1f} {yb-7:.1f})"/>')
            x += w * 0.82
    # moss / light on wall top
    s.append('<path d="M-30 760 Q 120 752 238 762 M432 770 Q 900 790 1566 810" stroke="#B5A773" stroke-width="3" opacity=".35" fill="none"/>')
    # piers
    for px in (238, 410):
        y = wall_y(px)
        s.append(f'<rect x="{px-2:.0f}" y="{y-112:.0f}" width="26" height="114" rx="3" fill="#7F7A70" stroke="#4E4B45" stroke-width="1.4"/>')
        s.append(f'<rect x="{px-6:.0f}" y="{y-120:.0f}" width="34" height="12" rx="3" fill="#8E897E" stroke="#4E4B45" stroke-width="1.2"/>')
    return "\n".join(s), wall_y


def gate(wall_y, open_=False):
    x0, x1 = 262, 410
    yb = wall_y(x0) - 6
    s = []
    if not open_:
        for i in range(5):
            y = yb - 10 - i * 17
            s.append(f'<line x1="{x0}" y1="{y:.0f}" x2="{x1}" y2="{y+3:.0f}" stroke="#B9BDBF" stroke-width="3.2"/>')
        s.append(f'<line x1="{x0}" y1="{yb-10:.0f}" x2="{x1}" y2="{yb-78:.0f}" stroke="#A9ADAF" stroke-width="2.6"/>')
        s.append(f'<line x1="{x0+2}" y1="{yb-6:.0f}" x2="{x0+2}" y2="{yb-84:.0f}" stroke="#C5C9CB" stroke-width="4"/>')
        s.append(f'<line x1="{x1}" y1="{yb-4:.0f}" x2="{x1}" y2="{yb-80:.0f}" stroke="#C5C9CB" stroke-width="4"/>')
    else:  # swung open against the inside of the left pier, seen almost edge-on
        for i in range(5):
            y = yb - 10 - i * 17
            s.append(f'<line x1="{x0}" y1="{y:.0f}" x2="{x0+34}" y2="{y-22:.0f}" stroke="#B9BDBF" stroke-width="3.2"/>')
        s.append(f'<line x1="{x0+34}" y1="{yb-30:.0f}" x2="{x0+34}" y2="{yb-108:.0f}" stroke="#C5C9CB" stroke-width="4"/>')
    return "\n".join(s)


def hawthorn():
    rnd = random.Random(41)
    s = ['<path d="M1268 800 C 1262 740 1250 700 1226 660 M1262 735 C 1290 700 1322 680 1352 668 M1250 700 C 1230 690 1205 690 1180 694" stroke="#3B2E22" stroke-width="9" fill="none" stroke-linecap="round"/>']
    for i in range(70):
        a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(0, 1) ** .5
        cx = 1268 + math.cos(a) * 120 * r; cy = 650 + math.sin(a) * 58 * r
        s.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{rnd.uniform(14,26):.0f}" fill="{rnd.choice(["#2F3B24","#3A4A2C","#46552F","#28331F"])}"/>')
    for i in range(30):  # light on the sunward side
        a = rnd.uniform(math.pi * .9, math.pi * 1.5); r = rnd.uniform(.6, 1)
        cx = 1268 + math.cos(a) * 118 * r; cy = 650 + math.sin(a) * 56 * r
        s.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{rnd.uniform(5,11):.0f}" fill="#8C8A4E" opacity=".55"/>')
    return "\n".join(s)


# ---------------------------------------------------------------- the house (POSSIBLE only)
def house():
    s = []
    # ground shadow and warm spill
    s.append('<ellipse cx="1000" cy="640" rx="470" ry="34" fill="#141711" opacity=".55" filter="url(#soft)"/>')
    s.append('<ellipse cx="760" cy="660" rx="200" ry="40" fill="url(#spill)"/>')
    # ---- main volume (larch), gable facing the viewer-left
    gl, gr = (612, 642), (834, 631)          # gable base
    el, er = (612, 528), (834, 517)          # eaves
    apex = (723, 404)
    s.append(f'<polygon points="{p([gl, gr, er, apex, el])}" fill="url(#larchGable)"/>')
    side_b = (1126, 616); side_t = (1126, 503)
    s.append(f'<polygon points="{p([gr, side_b, side_t, er])}" fill="url(#larch)"/>')
    # vertical boards on side
    for i in range(1, 46):
        t = i / 46
        xb, yb = lerp(gr[0], side_b[0], t), lerp(gr[1], side_b[1], t)
        xt, yt = lerp(er[0], side_t[0], t), lerp(er[1], side_t[1], t)
        s.append(f'<line x1="{xb:.1f}" y1="{yb:.1f}" x2="{xt:.1f}" y2="{yt:.1f}" stroke="#5A3F29" stroke-width="1" opacity=".55"/>')
    # roof plane
    ridge_end = (1015, 392)
    s.append(f'<polygon points="{p([apex, ridge_end, side_t, er])}" fill="url(#roof)"/>')
    for i in range(1, 26):  # standing seams
        t = i / 26
        x1, y1 = lerp(apex[0], ridge_end[0], t), lerp(apex[1], ridge_end[1], t)
        x2, y2 = lerp(er[0], side_t[0], t), lerp(er[1], side_t[1], t)
        s.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#5C5C60" stroke-width="1" opacity=".7"/>')
    # solar array on the roof (parallelogram grid)
    def roof_pt(u, v):  # u along ridge 0..1, v down slope 0..1
        top = (lerp(apex[0], ridge_end[0], u), lerp(apex[1], ridge_end[1], u))
        bot = (lerp(er[0], side_t[0], u), lerp(er[1], side_t[1], u))
        return (lerp(top[0], bot[0], v), lerp(top[1], bot[1], v))
    for c in range(6):
        for r in range(2):
            u0, u1 = .38 + c * .085, .38 + c * .085 + .078
            v0, v1 = .18 + r * .34, .18 + r * .34 + .3
            s.append(f'<polygon points="{p([roof_pt(u0,v0), roof_pt(u1,v0), roof_pt(u1,v1), roof_pt(u0,v1)])}" fill="#1E2430" stroke="#53627A" stroke-width=".9"/>')
    # roof edge highlight (sun from the left)
    s.append(f'<polyline points="{p([el, apex, er])}" fill="none" stroke="#2A2A2C" stroke-width="7" stroke-linejoin="round"/>')
    s.append(f'<polyline points="{p([el, apex])}" fill="none" stroke="#E7C79A" stroke-width="2" opacity=".75"/>')
    s.append(f'<line x1="{apex[0]}" y1="{apex[1]}" x2="{ridge_end[0]}" y2="{ridge_end[1]}" stroke="#77777B" stroke-width="2.4"/>')
    # glazed gable (warm interior)
    gin = [(634, 634), (812, 625), (812, 528), (723, 426), (634, 536)]
    s.append(f'<polygon points="{p(gin)}" fill="url(#glassGlow)"/>')
    # interior hints: back wall shelf line, pendant lights, sofa and table silhouettes
    s.append('<rect x="650" y="588" width="70" height="20" rx="4" fill="#5A3A22" opacity=".85"/>')
    s.append('<rect x="736" y="596" width="56" height="5" fill="#4E3320" opacity=".9"/><line x1="742" y1="601" x2="742" y2="620" stroke="#4E3320" stroke-width="3"/><line x1="786" y1="601" x2="786" y2="618" stroke="#4E3320" stroke-width="3"/>')
    for x, y in [(700, 520), (752, 512), (776, 540)]:
        s.append(f'<line x1="{x}" y1="{y-60}" x2="{x}" y2="{y}" stroke="#7A5233" stroke-width="1"/><circle cx="{x}" cy="{y+4}" r="5" fill="#FFF1C8"/><circle cx="{x}" cy="{y+4}" r="18" fill="url(#lamp)"/>')
    # mullions and transom
    for x in (679, 723, 768):
        s.append(f'<line x1="{x}" y1="{634 - (x-634)*0.05:.0f}" x2="{x}" y2="{ (536 - (x-634)*1.14) if x < 723 else (426 + (x-723)*1.146):.0f}" stroke="#2B2420" stroke-width="3"/>')
    s.append('<line x1="634" y1="572" x2="812" y2="563" stroke="#2B2420" stroke-width="2.4"/>')
    s.append(f'<polygon points="{p(gin)}" fill="none" stroke="#231D19" stroke-width="5" stroke-linejoin="round"/>')
    # reflections on glass
    s.append('<polygon points="640,600 676,560 676,574 640,616" fill="#FFF3D8" opacity=".18"/>')
    # ribbon window on the side
    def side_pt(t, h):  # t along side 0..1, h 0 base..1 eaves
        b = (lerp(gr[0], side_b[0], t), lerp(gr[1], side_b[1], t))
        tp = (lerp(er[0], side_t[0], t), lerp(er[1], side_t[1], t))
        return (lerp(b[0], tp[0], h), lerp(b[1], tp[1], h))
    for (t0, t1, h0, h1) in [(.08, .40, .30, .80), (.52, .66, .0, .80), (.74, .93, .36, .80)]:
        q = [side_pt(t0, h0), side_pt(t1, h0), side_pt(t1, h1), side_pt(t0, h1)]
        s.append(f'<polygon points="{p(q)}" fill="url(#glassGlowSoft)" stroke="#231D19" stroke-width="3"/>')
    # front door canopy shadow under the eaves line
    s.append(f'<polygon points="{p([gr, side_b, (side_b[0], side_b[1]-6), (gr[0], gr[1]-6)])}" fill="#000" opacity=".25"/>')
    # ---- glazed link
    lk = [(1126, 616), (1172, 614), (1172, 548), (1126, 550)]
    s.append(f'<polygon points="{p(lk)}" fill="url(#glassGlowSoft)" stroke="#231D19" stroke-width="3"/>')
    s.append('<polygon points="1120,552 1178,546 1178,538 1120,544" fill="#2E2E31"/>')
    # ---- second volume (lime render), lower, gable to the viewer
    g2l, g2r = (1172, 614), (1302, 608)
    e2l, e2r = (1172, 540), (1302, 534)
    a2 = (1237, 468)
    s.append(f'<polygon points="{p([g2l, g2r, e2r, a2, e2l])}" fill="url(#render)"/>')
    s2b, s2t = (1452, 602), (1452, 528)
    s.append(f'<polygon points="{p([g2r, s2b, s2t, e2r])}" fill="url(#renderSide)"/>')
    r2end = (1378, 462)
    s.append(f'<polygon points="{p([a2, r2end, s2t, e2r])}" fill="url(#roof)"/>')
    for i in range(1, 14):
        t = i / 14
        x1, y1 = lerp(a2[0], r2end[0], t), lerp(a2[1], r2end[1], t)
        x2, y2 = lerp(e2r[0], s2t[0], t), lerp(e2r[1], s2t[1], t)
        s.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#5C5C60" stroke-width="1" opacity=".7"/>')
    s.append(f'<polyline points="{p([e2l, a2, e2r])}" fill="none" stroke="#2A2A2C" stroke-width="6" stroke-linejoin="round"/>')
    s.append(f'<polyline points="{p([e2l, a2])}" fill="none" stroke="#E7C79A" stroke-width="2" opacity=".7"/>')
    # deep-set square window in the render gable, lit
    s.append('<polygon points="1212,590 1262,588 1262,544 1212,546" fill="url(#glassGlow)" stroke="#231D19" stroke-width="3"/>')
    s.append('<polygon points="1208,592 1266,590 1266,586 1208,588" fill="#8F8577"/>')
    # small heat-pump unit beside the render volume
    s.append('<rect x="1312" y="584" width="34" height="22" rx="2" fill="#D7D2C8" stroke="#6E6A62"/><circle cx="1324" cy="595" r="7" fill="#9A958C"/>')
    # rooflight glow
    s.append('<polygon points="1300,500 1330,497 1336,510 1306,513" fill="#F3C07C" opacity=".8"/>')
    return "\n".join(s)


def landscaping(wall_y):
    rnd = random.Random(51)
    s = []
    # gravel drive: from the gate gap down to the viewer, and up to the house
    drive = [(300, 960), (520, 960), (430, 800), (452, 742), (640, 662), (720, 650), (690, 646), (560, 662), (386, 742), (300, 806)]
    s.append(f'<polygon points="{p(drive)}" fill="url(#gravel)"/>')
    for _ in range(900):
        t = rnd.random()
        y = lerp(650, 960, t ** .8)
        # interpolate drive half-width and centre
        if y < 742:
            u = (y - 650) / 92
            cx, hw = lerp(690, 420, u), lerp(30, 36, u)
        elif y < 806:
            u = (y - 742) / 64
            cx, hw = lerp(420, 362, u), lerp(36, 62, u)
        else:
            u = (y - 806) / 154
            cx, hw = lerp(362, 410, u), lerp(62, 110, u)
        x = cx + rnd.uniform(-hw, hw)
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{lerp(.5,1.8,t):.1f}" fill="{rnd.choice(["#D6C8AE","#8D7E68","#A99A80","#6E6252"])}" opacity=".7"/>')
    # native planting beds near the house: grasses, low shrubs, a few purple and gold flowers
    for (cx, cy, rx, n) in [(560, 668, 120, 60), (930, 650, 160, 70), (1360, 640, 150, 60), (780, 690, 80, 26)]:
        for _ in range(n):
            x = cx + rnd.uniform(-rx, rx); y = cy + rnd.uniform(-10, 14)
            r = rnd.uniform(5, 12)
            s.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r:.1f}" ry="{r*.7:.1f}" fill="{rnd.choice(["#3F4C2A","#4F5D33","#5B6B3B","#36421F"])}"/>')
        for _ in range(n // 2):
            x = cx + rnd.uniform(-rx, rx); y = cy + rnd.uniform(-14, 8)
            s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(1.6,3):.1f}" fill="{rnd.choice(["#9C7FB3","#C9A35A","#E2C88A","#B48DBD"])}" opacity=".85"/>')
        for _ in range(n // 2):  # grasses
            x = cx + rnd.uniform(-rx, rx); y = cy + rnd.uniform(-4, 14)
            s.append(f'<path d="M{x:.0f} {y:.0f} q {rnd.uniform(-6,6):.0f} -10 {rnd.uniform(-10,10):.0f} -22" stroke="#C7B27A" stroke-width="1.2" fill="none" opacity=".6"/>')
    # a young birch and a rowan beside the house
    for (tx, ty, h) in [(560, 662, 120), (1480, 640, 140)]:
        s.append(f'<path d="M{tx} {ty} l 2 {-h}" stroke="#D9D2C4" stroke-width="5"/>')
        for _ in range(26):
            a = rnd.uniform(0, 2*math.pi); r = rnd.uniform(0, 1) ** .5
            s.append(f'<circle cx="{tx + math.cos(a)*40*r:.0f}" cy="{ty - h + 10 + math.sin(a)*34*r:.0f}" r="{rnd.uniform(6,11):.0f}" fill="{rnd.choice(["#5B6B33","#6F7D3C","#4B5A2B"])}" opacity=".95"/>')
    # low bollard lights along the drive and a lamp by the door
    for (x, y) in [(470, 735), (560, 690), (640, 668), (400, 790), (318, 812)]:
        s.append(f'<rect x="{x-2}" y="{y-14}" width="4" height="14" fill="#2B2620"/><circle cx="{x}" cy="{y-14}" r="16" fill="url(#lamp)"/>')
    s.append('<circle cx="845" cy="560" r="26" fill="url(#lamp)"/>')
    return "\n".join(s)


def grain(seed):
    rnd = random.Random(seed)
    out = []
    for _ in range(1600):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="1" height="1" fill="{rnd.choice(["#000","#fff"])}" opacity=".06"/>')
    return "\n".join(out)


def scene(possible):
    wall, wall_y = stone_wall()
    if possible:
        def skip(x, y):  # no grass on the drive or under the house
            if 600 < x < 1460 and y < 668:
                return True
            if y > 640:
                if y < 742 and abs(x - lerp(690, 420, (y - 650) / 92)) < 40: return True
                if 742 <= y < 806 and abs(x - lerp(420, 362, (y - 742) / 64)) < 66: return True
                if y >= 806 and abs(x - lerp(362, 410, (y - 806) / 154)) < lerp(62, 110, (y - 806) / 154) + 4: return True
            return False
    else:
        skip = None
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
             '<!-- PlotNua DISC-040 interim hero illustration. AI-generated (vector drawing written as code by Claude). Not a real site, design or product. -->',
             defs(), sky_and_hills(), meadow()]
    if possible:
        parts.append(house())
        parts.append(landscaping(wall_y))
    parts.append(grass(61, skip))
    parts.append(hawthorn())
    parts.append(wall)
    parts.append(gate(wall_y, open_=possible))
    parts.append(f'<rect width="{W}" height="{H}" fill="url(#vignette)"/>')
    parts.append(grain(71))
    parts.append('</svg>')
    return "\n".join(parts)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    for name, possible in (("BEFORE", False), ("POSSIBLE", True)):
        svg = scene(possible)
        sp = OUT / f"DISC-040-{name}.svg"
        sp.write_text(svg)
        master = OUT / f"_DISC-040-{name}-3072.png"
        subprocess.run(["rsvg-convert", "-w", "3072", "-h", "1920", "-o", str(master), str(sp)], check=True)
        im = Image.open(master).convert("RGB")
        for w in (1536, 1376, 1024, 768):
            h = round(w * 960 / 1536)
            im.resize((w, h), Image.LANCZOS).save(OUT / f"DISC-040-{name}-{w}.webp", quality=84, method=6)
        im.resize((1024, 640), Image.LANCZOS).save(OUT / f"DISC-040-{name}-1024.jpg", quality=86, optimize=True, progressive=True)
        # phone 4:5 window centred on the house: x 576..1344 of the 1536 master (768 wide, full height)
        crop = im.crop((576 * 2, 0, 1344 * 2, 1920)).resize((819, 1024), Image.LANCZOS)
        crop.save(OUT / f"DISC-040-{name}-M-819.webp", quality=84, method=6)
        if possible:
            og = im.crop((0, 260, 3072, 260 + 1613)).resize((1200, 630), Image.LANCZOS)
            og.save(OUT / "DISC-040-og-1200x630.jpg", quality=86, optimize=True, progressive=True)
        master.unlink()
    print("written:", sorted(x.name for x in OUT.iterdir()))


if __name__ == "__main__":
    sys.exit(main())
