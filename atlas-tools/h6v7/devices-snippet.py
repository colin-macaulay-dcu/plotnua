#!/usr/bin/env python3
"""H6 v7 fix (9 Nov 2026): the Power Station scenes stop drawing flat SVG devices on the photograph.
Battery and EV charger are photographic sprites (transplanted from the approved evening Power Station layer, re-graded to
daylight) composited into H6v7-layer-power-station-*; the heat-pump unit is a photographic sprite (from the approved
evening base) shown in the Air Heat scene and, briefly, in Ground. Leader lines are re-aimed at the devices.
Idempotence-guarded: refuses if already applied."""
import re, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'assets/h6/stage-snippet.part'); s = open(P, encoding='utf-8').read()
if 'H6v7-device-' in s: sys.exit('REFUSED: already applied')
V = '?v=20261109'
def one(t, pat, rep):
    n = len(re.findall(pat, t, re.S))
    if n != 1: sys.exit('REFUSED: %d matches for %r' % (n, pat[:60]))
    return re.sub(pat, lambda m: rep, t, count=1, flags=re.S)
# leaders (scene-local coordinates = image coordinates minus each scene's translation)
s = one(s, r'<line x1="190" y1="310" x2="68\.0" y2="384\.0"', '<line x1="190" y1="310" x2="49.5" y2="366.0"')      # store  (+700,0)  -> battery
s = one(s, r'<rect x="50\.0" y="378\.0" width="20" height="34"', '<rect x="48.0" y="351.0" width="19.5" height="32"')
s = one(s, r'<line x1="202" y1="315" x2="81\.0" y2="366\.0"', '<line x1="202" y1="315" x2="28.0" y2="371.0"')      # charge (+685,-6) -> charger
s = one(s, r'<line x1="187" y1="330" x2="82\.0" y2="397\.0"', '<line x1="187" y1="330" x2="64.5" y2="372.0"')      # grid   (+685,-5) -> battery/inverter
# drawn device groups: remove battery / charger / meter drawings; heat pump becomes the photographic sprite
devs = re.findall(r'<g class="h6p-dev" opacity="0">.*?</g>', s, re.S)
if len(devs) != 5: sys.exit('REFUSED: expected 5 drawn device groups, found %d' % len(devs))
HP = '<image data-href="assets/h6/img/H6v7-device-heatpump.webp%s" x="781" y="413" width="50" height="36" preserveAspectRatio="none"/>' % V
for d in devs:
    if '<rect x="780" y="410"' in d:
        anims = ''.join(re.findall(r'<animate [^>]*/>', d))
        s = s.replace(d, '<g class="h6p-dev" opacity="0">' + anims + HP + '</g>', 1)
    else:
        s = s.replace(d, '', 1)
open(P, 'w', encoding='utf-8').write(s); print('applied')
