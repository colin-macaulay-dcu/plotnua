#!/usr/bin/env python3
"""DISC-038 The Hidden Shelter: the interim hero illustration (Stage 3 private preview, 8 Nov 2026).

A PlotNua vector illustration, written here by hand. It is not AI-generated imagery, it reproduces no photograph and
no manufacturer's design, and it is not a drawing of any real product, house or installation. It is a generic,
illustrative section through an ordinary Irish house and back garden:

  BEFORE    the garden as it is today: the house, a patio, a lawn, trees and a hedge, with plain ground below.
  POSSIBLE  the same drawing, same frame, with a generic underground family shelter in section under the lawn:
            an open entrance hatch and stair, an entry room, a living and kitchen room, a bunk room, a shower and
            WC, a plant room (air filtration, water, batteries), a ventilation intake and an escape shaft.

Both files share one coordinate frame (1536 x 1024), so the Before/Possible slider aligns to the pixel. The phone
crop (819 x 1024) is the same drawing seen through a narrower window, so it aligns too.

Usage:  python3 atlas-tools/build-disc038-hero-illustration.py
Writes: assets/disc038/img/DISC-038-{BEFORE,POSSIBLE}.svg, -MASTER.png (3072 wide), -{768,1024,1376,1536}.webp,
        -1024.jpg, -M-819.webp, and DISC-038-og-1200x630.jpg.
"""
import os, subprocess, io
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "disc038", "img")
W, H = 1536, 1024
GROUND = 470            # the lawn line
M_X0 = 690              # phone window: x from 690, 819 wide

FONT = "Inter, 'DejaVu Sans', sans-serif"


def defs():
    return f"""
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#1B2026"/>
    <stop offset=".55" stop-color="#36404A"/>
    <stop offset=".86" stop-color="#7D7468"/>
    <stop offset="1" stop-color="#B99474"/>
  </linearGradient>
  <linearGradient id="soil" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#3E3329"/>
    <stop offset=".45" stop-color="#2F2720"/>
    <stop offset="1" stop-color="#1D1814"/>
  </linearGradient>
  <linearGradient id="lawn" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#6E8A5E"/>
    <stop offset="1" stop-color="#3F5538"/>
  </linearGradient>
  <linearGradient id="render" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#E4DED3"/>
    <stop offset="1" stop-color="#C9C2B6"/>
  </linearGradient>
  <linearGradient id="room" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#F6E7CF"/>
    <stop offset="1" stop-color="#E3CDAA"/>
  </linearGradient>
  <linearGradient id="plant" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#D9D3C8"/>
    <stop offset="1" stop-color="#BDB5A8"/>
  </linearGradient>
  <radialGradient id="glow" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="#FFD9A0" stop-opacity=".85"/>
    <stop offset="1" stop-color="#FFD9A0" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="beam" x1="0" y1="1" x2="0" y2="0">
    <stop offset="0" stop-color="#FFD9A0" stop-opacity=".55"/>
    <stop offset="1" stop-color="#FFD9A0" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="win" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#F7CF8F"/>
    <stop offset="1" stop-color="#E9A866"/>
  </linearGradient>
</defs>"""


def tree(x, base, h, r, tone):
    return (f'<rect x="{x-4}" y="{base-h}" width="8" height="{h}" fill="#3A322B"/>'
            f'<ellipse cx="{x}" cy="{base-h-r*.55}" rx="{r}" ry="{r*1.1}" fill="{tone}"/>'
            f'<ellipse cx="{x-r*.45}" cy="{base-h-r*.1}" rx="{r*.7}" ry="{r*.75}" fill="{tone}" opacity=".9"/>'
            f'<ellipse cx="{x+r*.5}" cy="{base-h-r*.2}" rx="{r*.65}" ry="{r*.7}" fill="{tone}" opacity=".85"/>')


def scene_top():
    s = [f'<rect width="{W}" height="{GROUND+4}" fill="url(#sky)"/>']
    # a few early stars
    for x, y, r in [(980, 70, 1.4), (1210, 120, 1.1), (1390, 60, 1.5), (860, 160, 1), (1480, 190, 1.1), (1110, 40, 1)]:
        s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#F2EBE0" opacity=".7"/>')
    # distant hills
    s.append(f'<path d="M0 {GROUND-58} C 220 {GROUND-110} 420 {GROUND-70} 640 {GROUND-92} S 1040 {GROUND-128} 1260 {GROUND-86} '
             f'S 1460 {GROUND-104} {W} {GROUND-96} L {W} {GROUND} L 0 {GROUND} Z" fill="#2C3530"/>')
    s.append(f'<path d="M0 {GROUND-30} C 300 {GROUND-62} 560 {GROUND-36} 820 {GROUND-52} S 1240 {GROUND-70} {W} {GROUND-44} '
             f'L {W} {GROUND} L 0 {GROUND} Z" fill="#26302B"/>')
    # rear boundary hedge and fence line
    s.append(f'<path d="M640 {GROUND} L640 {GROUND-36} Q 900 {GROUND-52} 1180 {GROUND-40} T {W} {GROUND-48} L {W} {GROUND} Z" fill="#2F4030"/>')
    # trees
    s.append(tree(1010, GROUND, 120, 58, "#3E5639"))
    s.append(tree(1310, GROUND, 150, 70, "#35492F"))
    s.append(tree(1488, GROUND, 110, 54, "#3A5135"))
    # the house: contemporary two-storey, render with a charcoal timber wing
    hx0, hx1, eave, ridge = 120, 610, 250, 120
    s.append(f'<rect x="{hx0}" y="{eave}" width="{hx1-hx0}" height="{GROUND-eave}" fill="url(#render)"/>')
    s.append(f'<path d="M{hx0-14} {eave+4} L{(hx0+hx1)//2} {ridge} L{hx1+14} {eave+4} Z" fill="#30333A"/>')
    s.append(f'<rect x="{hx0-14}" y="{eave}" width="{hx1-hx0+28}" height="8" fill="#23262B"/>')
    s.append(f'<rect x="440" y="{eave+8}" width="{hx1-440}" height="{GROUND-eave-8}" fill="#3B3A38"/>')
    for i in range(441, hx1, 9):
        s.append(f'<line x1="{i}" y1="{eave+8}" x2="{i}" y2="{GROUND}" stroke="#2E2D2B" stroke-width="2"/>')
    # windows (warm, lived-in)
    for (x, y, w, h) in [(160, 290, 92, 70), (290, 290, 92, 70), (470, 286, 104, 74)]:
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#win)" stroke="#23262B" stroke-width="5"/>')
        s.append(f'<line x1="{x+w/2}" y1="{y}" x2="{x+w/2}" y2="{y+h}" stroke="#23262B" stroke-width="3"/>')
    s.append(f'<rect x="168" y="388" width="230" height="{GROUND-388}" fill="url(#win)" stroke="#23262B" stroke-width="6"/>')
    for x in (225, 283, 341):
        s.append(f'<line x1="{x}" y1="388" x2="{x}" y2="{GROUND}" stroke="#23262B" stroke-width="3"/>')
    s.append(f'<rect x="462" y="392" width="118" height="{GROUND-392}" fill="url(#win)" stroke="#23262B" stroke-width="6"/>')
    s.append(f'<ellipse cx="283" cy="{GROUND-2}" rx="190" ry="26" fill="url(#glow)" opacity=".55"/>')
    # patio
    s.append(f'<rect x="{hx1}" y="{GROUND-6}" width="120" height="8" fill="#8C857A"/>')
    for x in range(hx1, hx1+120, 24):
        s.append(f'<line x1="{x}" y1="{GROUND-6}" x2="{x}" y2="{GROUND+2}" stroke="#6E685F" stroke-width="1.5"/>')
    # planters by the patio
    s.append(f'<rect x="{hx1+128}" y="{GROUND-30}" width="44" height="30" rx="3" fill="#4A4540"/>')
    s.append(f'<ellipse cx="{hx1+150}" cy="{GROUND-38}" rx="30" ry="18" fill="#4E6B47"/>')
    return "".join(s)


def ground():
    s = [f'<rect x="0" y="{GROUND}" width="{W}" height="{H-GROUND}" fill="url(#soil)"/>']
    # topsoil and strata, faint
    s.append(f'<rect x="0" y="{GROUND}" width="{W}" height="18" fill="url(#lawn)"/>')
    s.append(f'<rect x="0" y="{GROUND+18}" width="{W}" height="26" fill="#4A3B2E" opacity=".75"/>')
    for i, y in enumerate([560, 660, 760, 880, 960]):
        a = 0.12 + 0.03 * (i % 2)
        s.append(f'<path d="M0 {y} C 260 {y-14} 520 {y+12} 780 {y-6} S 1300 {y+10} {W} {y-4}" stroke="#5A4A3B" stroke-width="2" fill="none" opacity="{a}"/>')
    import random
    rnd = random.Random(38)
    for _ in range(140):
        x, y = rnd.uniform(0, W), rnd.uniform(GROUND + 50, H - 8)
        r = rnd.uniform(1.6, 5.2)
        s.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{r:.1f}" ry="{r*.7:.1f}" fill="#5B4C3E" opacity=".35"/>')
    # house foundations
    s.append(f'<rect x="112" y="{GROUND}" width="506" height="64" fill="#4B4640" opacity=".9"/>')
    s.append(f'<rect x="112" y="{GROUND+64}" width="506" height="10" fill="#3A3631"/>')
    # grass tufts on the lawn edge
    for x in range(740, W, 26):
        s.append(f'<path d="M{x} {GROUND+1} l3 -9 l3 9 M{x+8} {GROUND+1} l2 -7 l2 7" stroke="#86A372" stroke-width="1.5" fill="none" opacity=".75"/>')
    return "".join(s)


def pill(cx, y, text, anchor="middle"):
    w = 12.6 * len(text) + 34
    bx = {"middle": cx - w / 2, "start": cx, "end": cx - w}[anchor]
    return (f'<rect x="{bx:.1f}" y="{y-17}" width="{w:.1f}" height="34" rx="17" fill="#1B1C1E" opacity=".88" stroke="#F2EBE0" stroke-opacity=".28"/>'
            f'<text x="{bx+17:.1f}" y="{y+6}" font-family="{FONT}" font-size="17" font-weight="600" letter-spacing="1.6" fill="#F2EBE0">{text.replace("&", "&amp;")}</text>')


def lead(x1, y1, x2, y2):
    """A leader line ending in a terracotta dot at (x2, y2), the thing being named."""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#F2EBE0" stroke-width="1.6" opacity=".85"/>'
            f'<circle cx="{x2}" cy="{y2}" r="4.5" fill="#CF8566" stroke="#F2EBE0" stroke-width="1.6"/>')


def shelter():
    s = []
    x0, x1, y0, y1 = 830, 1440, 556, 812   # outer shell
    t = 18
    # excavation outline (backfill), subtle
    s.append(f'<path d="M{x0-40} {GROUND+30} L{x0-22} {y1+36} L{x1+26} {y1+36} L{x1+40} {GROUND+30}" fill="#3A2F26" opacity=".55"/>')
    # the shell: reinforced concrete
    s.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" rx="22" fill="#8E8981" stroke="#B4AEA4" stroke-width="2"/>')
    ix0, ix1, iy0, iy1 = x0 + t, x1 - t, y0 + t, y1 - t
    s.append(f'<rect x="{ix0}" y="{iy0}" width="{ix1-ix0}" height="{iy1-iy0}" rx="8" fill="url(#room)"/>')
    floor = iy1
    # rooms: entry 848-930, living 930-1176, bunks 1176-1290, wc 1290-1344, plant 1344-1422
    walls = [930, 1176, 1290, 1344]
    for wx in walls:
        s.append(f'<rect x="{wx-4}" y="{iy0}" width="8" height="{iy1-iy0}" fill="#A69F94"/>')
    # door openings (cut lower parts)
    for wx in walls[:3]:
        s.append(f'<rect x="{wx-5}" y="{floor-120}" width="10" height="120" fill="url(#room)"/>')
    s.append(f'<rect x="{walls[3]-5}" y="{floor-120}" width="10" height="120" fill="url(#plant)"/>')
    # plant room tone
    s.append(f'<rect x="{walls[3]+4}" y="{iy0}" width="{ix1-walls[3]-4}" height="{iy1-iy0}" fill="url(#plant)"/>')
    # floor finish
    s.append(f'<rect x="{ix0}" y="{floor-8}" width="{ix1-ix0}" height="8" fill="#8B6F4E"/>')
    # ceiling lights and glow
    for cx in (1010, 1100, 1232, 888):
        s.append(f'<ellipse cx="{cx}" cy="{iy0+70}" rx="70" ry="60" fill="url(#glow)" opacity=".55"/>')
        s.append(f'<rect x="{cx-16}" y="{iy0}" width="32" height="5" rx="2" fill="#FFF3DC"/>')
    # ENTRY: airlock door to living (a solid door leaf drawn open against the wall)
    s.append(f'<rect x="{walls[0]+6}" y="{floor-118}" width="7" height="110" fill="#5E5A55"/>')
    s.append(f'<rect x="{ix0+10}" y="{floor-62}" width="26" height="54" rx="3" fill="#6D675F"/>')  # coat / kit locker
    # LIVING & KITCHEN
    # kitchen run against the left wall
    s.append(f'<rect x="{walls[0]+18}" y="{floor-66}" width="96" height="58" fill="#E9E2D6" stroke="#B9AE9C"/>')
    s.append(f'<rect x="{walls[0]+18}" y="{floor-70}" width="96" height="6" fill="#4A4744"/>')
    s.append(f'<rect x="{walls[0]+18}" y="{iy0+30}" width="96" height="40" fill="#E9E2D6" stroke="#B9AE9C"/>')
    s.append(f'<rect x="{walls[0]+44}" y="{floor-84}" width="22" height="14" rx="2" fill="#9AA3A8"/>')  # tap/sink
    # table and chairs
    tx = 1072
    s.append(f'<rect x="{tx-48}" y="{floor-58}" width="96" height="7" fill="#7A5C3E"/>')
    s.append(f'<rect x="{tx-40}" y="{floor-51}" width="6" height="43" fill="#7A5C3E"/><rect x="{tx+34}" y="{floor-51}" width="6" height="43" fill="#7A5C3E"/>')
    for cx in (tx-66, tx+60):
        s.append(f'<rect x="{cx}" y="{floor-44}" width="8" height="36" fill="#5B4632"/><rect x="{cx-4}" y="{floor-48}" width="16" height="6" fill="#5B4632"/>')
    s.append(f'<ellipse cx="{tx}" cy="{floor-66}" rx="10" ry="5" fill="#C98F5A"/>')  # a bowl
    # sofa along the right of the living room
    s.append(f'<rect x="1112" y="{floor-48}" width="58" height="40" rx="6" fill="#56636B"/>')
    s.append(f'<rect x="1112" y="{floor-72}" width="14" height="64" rx="5" fill="#4A565D"/>')
    # a shelf of books / supplies
    s.append(f'<rect x="1120" y="{iy0+36}" width="50" height="5" fill="#7A5C3E"/>')
    for i, c in enumerate(["#B5634A", "#4F6B4A", "#C9A877", "#56636B", "#8C6A9A"]):
        s.append(f'<rect x="{1122+i*9}" y="{iy0+16}" width="7" height="20" fill="{c}"/>')
    # BUNK ROOM: two bunks, two tiers each
    for bx in (walls[1]+12, walls[1]+62):
        s.append(f'<rect x="{bx}" y="{iy0+26}" width="6" height="{floor-iy0-34}" fill="#6B5541"/>')
        s.append(f'<rect x="{bx+40}" y="{iy0+26}" width="6" height="{floor-iy0-34}" fill="#6B5541"/>')
        for by in (iy0+64, floor-40):
            s.append(f'<rect x="{bx}" y="{by}" width="46" height="9" fill="#7A5C3E"/>')
            s.append(f'<rect x="{bx+2}" y="{by-12}" width="42" height="12" rx="4" fill="#E9E2D6"/>')
            s.append(f'<rect x="{bx+3}" y="{by-14}" width="12" height="8" rx="3" fill="#F7F2EA"/>')
    # SHOWER & WC
    s.append(f'<rect x="{walls[2]+10}" y="{floor-46}" width="22" height="38" rx="4" fill="#F2F0EC" stroke="#B8B2A8"/>')  # wc
    s.append(f'<rect x="{walls[2]+34}" y="{iy0+24}" width="4" height="{floor-iy0-32}" fill="#9AA3A8"/>')
    s.append(f'<path d="M{walls[2]+36} {iy0+30} q 6 -10 14 0" stroke="#9AA3A8" stroke-width="3" fill="none"/>')
    # PLANT ROOM: filter unit, batteries, water tanks
    px = walls[3] + 12
    s.append(f'<rect x="{px}" y="{iy0+22}" width="30" height="62" rx="3" fill="#5F6A70" stroke="#3B4246"/>')   # filter
    s.append(f'<circle cx="{px+15}" cy="{iy0+40}" r="9" fill="#3B4246"/><path d="M{px+15} {iy0+31} v18 M{px+6} {iy0+40} h18" stroke="#9AA3A8" stroke-width="2"/>')
    s.append(f'<rect x="{px+36}" y="{iy0+30}" width="24" height="40" rx="3" fill="#3E4A3E"/>')                      # batteries
    for i in range(3):
        s.append(f'<rect x="{px+40}" y="{iy0+36+i*11}" width="16" height="7" rx="1" fill="#8FAF8A"/>')
    for i, wx in enumerate((px, px+34)):                                                                       # tanks
        s.append(f'<rect x="{wx}" y="{floor-70}" width="28" height="62" rx="8" fill="#6F8A9A" stroke="#4F6676"/>')
        s.append(f'<rect x="{wx+3}" y="{floor-42}" width="22" height="31" rx="5" fill="#A7C2CF" opacity=".75"/>')
    # ENTRANCE SHAFT and stair (left end), with the hatch standing open at the lawn
    sx0, sx1 = 742, 830
    s.append(f'<rect x="{sx0-14}" y="{GROUND+4}" width="{sx1-sx0+28}" height="{iy1-GROUND+t}" fill="#8E8981" stroke="#B4AEA4" stroke-width="2"/>')
    s.append(f'<rect x="{sx0}" y="{GROUND+4}" width="{sx1-sx0+t+4}" height="{iy1-GROUND-4}" fill="url(#room)"/>')
    # connect shaft to entry room
    s.append(f'<rect x="{sx1-2}" y="{iy0}" width="{t+6}" height="{iy1-iy0}" fill="url(#room)"/>')
    steps = 11
    for i in range(steps):
        stx = sx0 + 4 + i * ((sx1 - sx0 + 60) / steps)
        sty = GROUND + 18 + i * ((iy1 - GROUND - 26) / steps)
        s.append(f'<rect x="{stx:.1f}" y="{sty:.1f}" width="{(sx1-sx0+60)/steps+3:.1f}" height="6" fill="#7A5C3E"/>')
    s.append(f'<line x1="{sx0+10}" y1="{GROUND+6}" x2="{sx1+62}" y2="{iy1-24}" stroke="#4A4744" stroke-width="3"/>')  # handrail
    # light spilling up out of the open hatch
    s.append(f'<path d="M{sx0} {GROUND} L{sx0-40} {GROUND-150} L{sx1+48} {GROUND-150} L{sx1} {GROUND} Z" fill="url(#beam)"/>')
    # the hatch frame flush with the lawn, and the lid standing open (a low steel-and-timber lid on a hinge)
    s.append(f'<rect x="{sx0-18}" y="{GROUND-6}" width="{sx1-sx0+36}" height="10" fill="#3B3E42"/>')
    s.append(f'<path d="M{sx0-16} {GROUND-6} L{sx0-58} {GROUND-96} L{sx0-46} {GROUND-102} L{sx0-4} {GROUND-12} Z" fill="#4A4D52" stroke="#2A2C30" stroke-width="2"/>')
    s.append(f'<path d="M{sx0-50} {GROUND-90} L{sx0-12} {GROUND-14}" stroke="#7A5C3E" stroke-width="5"/>')
    # ESCAPE SHAFT (right end) with a flush hatch under the hedge line
    ex0 = x1 - 4
    s.append(f'<rect x="{ex0}" y="{GROUND+4}" width="40" height="{iy0+40-GROUND}" fill="#8E8981" stroke="#B4AEA4" stroke-width="2"/>')
    s.append(f'<rect x="{ex0+8}" y="{GROUND+4}" width="24" height="{iy0+44-GROUND}" fill="#CFC6B6"/>')
    for y in range(GROUND + 18, iy0 + 40, 16):
        s.append(f'<line x1="{ex0+10}" y1="{y}" x2="{ex0+30}" y2="{y}" stroke="#6B6359" stroke-width="2.5"/>')
    s.append(f'<rect x="{ex0-6}" y="{GROUND-4}" width="52" height="8" fill="#3B3E42"/>')
    s.append(f'<rect x="{x1-26}" y="{iy0+20}" width="22" height="70" fill="#CFC6B6"/>')  # opening into the plant room
    # VENTILATION intake: a low mushroom cowl in the planting, ducted to the plant room
    vx = 1386
    s.append(f'<rect x="{vx-5}" y="{GROUND-30}" width="10" height="{iy0-GROUND+34}" fill="#5F6A70"/>')
    s.append(f'<path d="M{vx-22} {GROUND-30} q 22 -24 44 0 Z" fill="#4A4D52"/>')
    s.append(f'<ellipse cx="{vx+30}" cy="{GROUND-12}" rx="28" ry="16" fill="#4E6B47"/>')
    s.append(f'<ellipse cx="{vx-34}" cy="{GROUND-10}" rx="24" ry="13" fill="#456040"/>')
    # earth cover marker
    s.append(f'<path d="M{x0+16} {GROUND+20} v{y0-GROUND-24} M{x0+10} {GROUND+20} h12 M{x0+10} {y0-4} h12" stroke="#F2EBE0" stroke-width="1.6" opacity=".75"/>')
    return "".join(s)


def labels():
    s = []
    # above ground
    s.append(lead(896, 320, 772, GROUND - 46) + pill(896, 320, "OPEN ENTRANCE HATCH", "start"))
    s.append(lead(1336, 404, 1380, GROUND - 40) + pill(1336, 404, "AIR INTAKE", "end"))
    s.append(lead(1456, 360, 1456, GROUND - 8) + pill(1500, 344, "ESCAPE HATCH", "end"))
    # below ground: two tidy rows, straight leaders up into each room
    fl = 812 - 18 - 30
    row1, row2 = 868, 924
    s.append(lead(800, row1 - 17, 800, fl) + pill(800, row1, "STAIR & ENTRY"))
    s.append(lead(1053, row2 - 17, 1053, fl) + pill(1053, row2, "LIVING & KITCHEN"))
    s.append(lead(1160, row1 - 17, 1233, fl - 40) + pill(1160, row1, "SLEEPING"))
    s.append(lead(1317, row2 - 17, 1317, fl) + pill(1317, row2, "SHOWER & WC", "start") if False else
             lead(1317, row2 - 17, 1317, fl) + pill(1317 + 20, row2, "SHOWER & WC"))
    s.append(lead(1392, row1 - 17, 1392, 700) + pill(1500, row1, "AIR, WATER & POWER", "end") if False else
             lead(1420, row1 - 17, 1392, 700) + pill(1500, row1, "AIR, WATER & POWER", "end"))
    return "".join(s)


def caption():
    return (f'<text x="{W-40}" y="{H-22}" text-anchor="end" font-family="{FONT}" font-size="15" font-weight="700" '
            f'letter-spacing="3" fill="#C9A877" opacity=".9">ILLUSTRATIVE SECTION · NOT TO SCALE</text>')


def svg(possible):
    body = scene_top() + ground() + (shelter() + labels() if possible else "") + caption()
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{defs()}{body}</svg>'


def render(svg_path, png_path, width):
    subprocess.run(["rsvg-convert", "-w", str(width), "-o", png_path, svg_path], check=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, possible in (("BEFORE", False), ("POSSIBLE", True)):
        sp = os.path.join(OUT, f"DISC-038-{name}.svg")
        with open(sp, "w") as f:
            f.write(svg(possible))
        master = os.path.join(OUT, f"DISC-038-{name}-MASTER.png")
        render(sp, master, W * 2)
        im = Image.open(master).convert("RGB")
        for w in (768, 1024, 1376, 1536):
            im.resize((w, round(w * H / W)), Image.LANCZOS).save(os.path.join(OUT, f"DISC-038-{name}-{w}.webp"), "WEBP", quality=86, method=6)
        im.resize((1024, round(1024 * H / W)), Image.LANCZOS).save(os.path.join(OUT, f"DISC-038-{name}-1024.jpg"), "JPEG", quality=86, optimize=True, progressive=True)
        # phone window: the same drawing, 819 x 1024 in the 1536 frame
        sc = im.width / W
        crop = im.crop((round(M_X0 * sc), 0, round((M_X0 + 819) * sc), round(H * sc))).resize((819, 1024), Image.LANCZOS)
        crop.save(os.path.join(OUT, f"DISC-038-{name}-M-819.webp"), "WEBP", quality=86, method=6)
        if possible:
            og = im.resize((1200, 800), Image.LANCZOS).crop((0, 85, 1200, 715))
            og.save(os.path.join(OUT, "DISC-038-og-1200x630.jpg"), "JPEG", quality=86, optimize=True)
    print("written to", OUT)


if __name__ == "__main__":
    main()
