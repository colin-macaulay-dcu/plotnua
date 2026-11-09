#!/usr/bin/env python3
"""H6 v7 (8 Nov 2026): move assets/h6/stage-snippet.part from the evening image set (v6, 1677x938) to the daylight
BEFORE/POSSIBLE pair (1670x942). One-off, deterministic, idempotence-guarded migration:
  * the photograph becomes the BEFORE master; six feature layers + one conditional reflection layer;
  * Wildlife Pond becomes Natural Swimming Pool (its Discovery: discovery-natural-swimming-garden.html);
  * the 3D lawn lettering and the CSS puff smoke are retired: a cloud-morph canvas, a water canvas and a smoke canvas;
  * the eight House as a Power Station scenes are re-registered to the new house (per-scene transforms, see SCENES),
    with drawn devices where the new photograph has none (battery, EV charger, smart meter, heat pump).
Usage: python3 atlas-tools/h6v7/migrate-snippet.py   (refuses if the snippet is already v7)"""
import re, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'assets/h6/stage-snippet.part')
s = open(P, encoding='utf-8').read()
if 'H6v7-' in s: sys.exit('REFUSED: the snippet is already v7')
V = '?v=20261108'; W = (960, 1670); SIZES = '(max-width: 700px) 100vw, 1670px'
def ss(stem, ext='webp'): return ', '.join('assets/h6/img/%s-%d.%s%s %dw' % (stem, w, ext, V, w) for w in W)
def one(t, pat, rep, flags=re.S):
    n = len(re.findall(pat, t, flags))
    if n != 1: sys.exit('REFUSED: expected one match for %r, found %d' % (pat[:70], n))
    return re.sub(pat, lambda m: rep, t, count=1, flags=flags)

ALT = ('A real-looking Irish back garden in soft daylight: a cream two-storey house with a patio, one open lawn, '
       'a stone path through foxgloves and ferns, a mature tree, and clipped hedges under a cloudy sky.')
s = one(s, r'<picture>.*?</picture>',
        '<picture><source type="image/avif" srcset="%s" sizes="%s"><source type="image/webp" srcset="%s" sizes="%s">'
        '<img class="h6p-base" src="assets/h6/img/H6v7-before-1670.webp%s" width="1670" height="942" fetchpriority="high" decoding="async" alt="%s"></picture>'
        % (ss('H6v7-before', 'avif'), SIZES, ss('H6v7-before'), SIZES, V, ALT))
# retire the 3D lawn lettering (it belonged to the evening photograph's lawn)
s = one(s, r'\s*<img class="h6p-letter is-off" id="h6p-letter-shadow"[^>]*>', '')
s = one(s, r'\s*<img class="h6p-letter is-off" id="h6p-letter"[^>]*>', '')
s = one(s, r'\s*<p class="h6p-lawn-text is-off" id="h6p-lawn-text"[^>]*>.*?</p>', '')
# discovery layers, in compositing order (each layer is POSSIBLE pixels + matte over the BEFORE master)
ov = re.findall(r'\s*<img class="h6p-(?:ov|fix)"[^>]*>', s)
if len(ov) != 7: sys.exit('REFUSED: expected 7 layer images, found %d' % len(ov))
first = s.index(ov[0]); 
for o in ov: s = s.replace(o, '', 1)
def layer(k, stem, extra=''):
    return ('\n      <img class="h6p-ov%s" data-d="%s" data-srcset="%s" data-sizes="%s" width="1670" height="942" alt="" decoding="async">'
            % (extra, k, ss(stem), SIZES))
layers = (layer('treehouse', 'H6v7-layer-treehouse') + layer('borrowed-garden', 'H6v7-layer-borrowed-garden')
          + layer('garden-room', 'H6v7-layer-garden-room') + layer('garden-retreat', 'H6v7-layer-garden-retreat')
          + layer('natural-swimming-pool', 'H6v7-layer-natural-swimming-pool')
          + ('\n      <img class="h6p-fix" id="h6p-reflection" data-needs="garden-room natural-swimming-pool" data-srcset="%s" data-sizes="%s" width="1670" height="942" alt="" aria-hidden="true" decoding="async">'
             % (ss('H6v7-layer-garden-room-reflection'), SIZES))
          + layer('power-station', 'H6v7-layer-power-station')
          + '\n      <canvas class="h6p-fx" id="h6p-water" aria-hidden="true"></canvas>'
          + '\n      <canvas class="h6p-fx" id="h6p-smoke" aria-hidden="true"></canvas>'
          + '\n      <canvas class="h6p-fx" id="h6p-sky" aria-hidden="true"></canvas>')
s = s[:first] + layers + s[first:]
s = one(s, r'\s*<div class="h6p-smoke" id="h6p-smoke"[^>]*>.*?</div>', '')
# switch: Wildlife Pond -> Natural Swimming Pool
s = one(s, r'<button type="button" class="h6p-sw" data-d="wildlife-pond" aria-pressed="false" style="--i:4">(.*?)<span class="h6p-lb">Wildlife Pond</span>',
        '<button type="button" class="h6p-sw" data-d="natural-swimming-pool" aria-pressed="false" style="--i:4"><span class="h6p-knob" aria-hidden="true"></span><span class="h6p-lb">Natural Swimming Pool</span>')
s = one(s, r'<p class="h6p-sr" id="h6p-lawn-words">Discover What’s Possible\.\.\.</p>',
        '<p class="h6p-sr" id="h6p-lawn-words">The clouds above the garden gather into the words “Discover what’s possible.”</p>')
# one motion control for everything that moves (sky, water, smoke): WCAG 2.2.2
CLEAR = '<button type="button" class="h6p-g h6p-g-clear" id="h6p-clear" style="--i:7">Clear All</button>'
s = one(s, re.escape(CLEAR), CLEAR + '\n      <button type="button" class="h6p-g h6p-g-motion" id="h6p-motion" aria-pressed="false">Pause motion</button>')

# ---------------- House as a Power Station scenes ----------------
a = s.index('<svg class="h6p-scenes"'); b = s.index('</svg>', a) + 6
svg = s[a:b]
svg = svg.replace('viewBox="0 0 1677 938"', 'viewBox="0 0 1670 942"').replace('width="1677" height="938"', 'width="1670" height="942"')
svg = svg.replace('assets/h6/img/H6-garden-base-v6-960.webp?v=20261103', 'assets/h6/img/H6v7-before-960.webp' + V)
# per-scene transforms, old (1677x938 evening house) -> new (1670x942 daylight house); see SCENES in h6.js for cameras
M = {
  'sun':     (0.6566, 0.0459, -0.0028, 0.9045, 192.1, -37.6),   # affine fitted to the PV array (old quad -> new quad)
  'store':   (1, 0, 0, 1, 700, 0),     # badge over the hedge right of the house; leader to the drawn battery
  'charge':  (1, 0, 0, 1, 685, -6),
  'grid':    (1, 0, 0, 1, 685, -5),
  'air':     (1, 0, 0, 1, 20, 110),    # heat-pump unit on the patio beside the extension (the new house has no flat roof)
  'ground':  (1, 0, 0, 1, -40, 12),
  'wind':    (1, 0, 0, 1, 52, -10),    # mast on the roof plane right of the panels
  'compute': (1, 0, 0, 1, 120, -54),   # badge on the upper rear wall
}
def inv(m):
    a_, b_, c_, d_, e_, f_ = m; det = a_ * d_ - b_ * c_
    ia, ib, ic, id_ = d_ / det, -b_ / det, -c_ / det, a_ / det
    return (ia, ib, ic, id_, -(ia * e_ + ic * f_), -(ib * e_ + id_ * f_))
def mat(m): return 'matrix(%s)' % ' '.join(('%.4f' % v).rstrip('0').rstrip('.') for v in m)
def to_old(k, x, y):
    ia, ib, ic, id_, ie, if_ = inv(M[k]); return (ia * x + ic * y + ie, ib * x + id_ * y + if_)
# drawn devices (new image coordinates). Illustrations, like the scene drawings themselves.
DEV = {
 'store':  '<rect x="752" y="380" width="16" height="30" rx="2.5" fill="#d8d4cc" stroke="#7d7a74" stroke-width=".9"/><rect x="755" y="385" width="10" height="2" rx="1" fill="#7CC47C"/><line x1="760" y1="410" x2="760" y2="430" stroke="#7d7a74" stroke-width="1"/>',
 'charge': '<rect x="754" y="352" width="12" height="18" rx="2" fill="#3c3a38" stroke="#b9b4aa" stroke-width=".8"/><circle cx="760" cy="358" r="1.6" fill="#7CC47C"/><path d="M760 370 C760 392 772 398 790 402" fill="none" stroke="#3c3a38" stroke-width="1.6" stroke-linecap="round"/>',
 'grid':   '<rect x="753" y="390" width="14" height="18" rx="1.5" fill="#e6e2da" stroke="#7d7a74" stroke-width=".9"/><rect x="755.5" y="393" width="9" height="5" fill="#A7C9A0"/>',
 'air':    '<rect x="780" y="410" width="46" height="33" rx="2.5" fill="#e9e6df" stroke="#8f8b84" stroke-width="1"/><circle cx="810" cy="426.5" r="11" fill="#cfcbc3" stroke="#8f8b84" stroke-width=".8"/><circle cx="810" cy="426.5" r="2" fill="#8f8b84"/><line x1="784" y1="415" x2="796" y2="415" stroke="#8f8b84" stroke-width=".8"/><line x1="784" y1="419" x2="796" y2="419" stroke="#8f8b84" stroke-width=".8"/><line x1="784" y1="443" x2="826" y2="443" stroke="rgba(20,16,10,.35)" stroke-width="2"/>',
 'ground': '<rect x="780" y="410" width="46" height="33" rx="2.5" fill="#e9e6df" stroke="#8f8b84" stroke-width="1"/><circle cx="810" cy="426.5" r="11" fill="#cfcbc3" stroke="#8f8b84" stroke-width=".8"/>',
}
def fade_in(inner, delay='0', out=None):
    o = '<animate attributeName="opacity" from="1" to="0" dur="0.5s" begin="indefinite" fill="freeze" data-delay="%s" data-rm="skip"/>' % out if out else ''
    return ('<g class="h6p-dev" opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="indefinite" fill="freeze" data-delay="%s"/>%s%s</g>' % (delay, o, inner))
def rescene(k, body):
    # overrides inside the old geometry, written in old coordinates (computed from the new targets)
    if k == 'store':
        ox, oy = to_old(k, 768, 384)
        body = one(body, r'<line x1="190" y1="310" x2="227" y2="381"', '<line x1="190" y1="310" x2="%.1f" y2="%.1f"' % (ox, oy))
        bx, by = to_old(k, 750, 378)
        body = one(body, r'<rect x="223" y="381" width="17" height="29"', '<rect x="%.1f" y="%.1f" width="20" height="34"' % (bx, by))
    if k == 'charge':
        ox, oy = to_old(k, 766, 360)
        body = one(body, r'<line x1="202" y1="315" x2="246" y2="392"', '<line x1="202" y1="315" x2="%.1f" y2="%.1f"' % (ox, oy))
    if k == 'grid':
        ox, oy = to_old(k, 767, 392)
        body = one(body, r'<line x1="187" y1="330" x2="184" y2="352"', '<line x1="187" y1="330" x2="%.1f" y2="%.1f"' % (ox, oy))
    if k == 'air':
        # electricity from the PV array (new 636,208) down the house's right side to the unit (new 790,410)
        pts = [(636, 208), (690, 236), (742, 262), (776, 300), (786, 350), (790, 408)]
        d = 'M' + ' L'.join('%.1f %.1f' % to_old(k, x, y) for x, y in pts)
        body, n = re.subn(r'd="M684\.0 263\.0[^"]*"', 'd="%s"' % d, body)
        if n != 2: sys.exit('REFUSED: air electricity paths not found (%d)' % n)
        bx, by = to_old(k, 742, 262)
        body = one(body, r'<circle cx="720" cy="283" r="8.5"', '<circle cx="%.1f" cy="%.1f" r="8.5"' % (bx, by))
        body = one(body, r'<polygon points="721,276 716,284 720,284 718,290 724,282 720,282 722,276"',
                   '<polygon points="%s"' % ' '.join('%.1f,%.1f' % (px + bx - 720, py + by - 283) for px, py in
                                                      [(721,276),(716,284),(720,284),(718,290),(724,282),(720,282),(722,276)]))
    if k == 'ground':
        bx, by = to_old(k, 779, 409)
        body = body.replace('<rect x="759" y="299" width="50" height="36"', '<rect x="%.1f" y="%.1f" width="48" height="35"' % (bx, by))
        ia = inv(M[k])
        body, n = re.subn(r'<image data-href=', '<image transform="%s" data-href=' % mat(ia), body)
        if n != 2: sys.exit('REFUSED: expected the two X-ray images in Ground, found %d' % n)
    return body
out = svg; n = 0
for m in re.finditer(r'(<g class="h6p-scene" data-scene="(\w+)">)([\s\S]*?)(?=<g class="h6p-scene"|</svg>)', svg):
    head, k, body = m.group(1), m.group(2), m.group(3)
    if not body.endswith('</g>'): sys.exit('REFUSED: scene %s does not end with </g>' % k)
    inner = rescene(k, body[:-4])
    new = head + '<g transform="%s">' % mat(M[k]) + inner + '</g>' + (fade_in(DEV[k], out='1.4' if k == 'ground' else None) if k in DEV else '') + '</g>'
    out = out.replace(head + body, new, 1); n += 1
if n != 8: sys.exit('REFUSED: expected 8 scenes, found %d' % n)
s = s[:a] + out + s[b:]
open(P, 'w', encoding='utf-8').write(s)
print('migrated', P)
