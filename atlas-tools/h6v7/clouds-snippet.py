#!/usr/bin/env python3
"""H6 v7 cloud lettering v2 (11 Nov 2026): list the cloud-lettering maps in the snippet's inert asset template (so the
curated public build reaches them) and drop the retired v1 sky maps (sky-src, sky-tgt, sky-flow, sky-time), which h6.js
no longer loads. Idempotent. Then: python3 atlas-tools/build-h6-homepage.py --mount && --check"""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'assets/h6/stage-snippet.part'); s = open(P, encoding='utf-8').read()
V = '?v=20261109'
def tag(f): return '<img src="assets/h6/img/H6v7-%s%s" alt="">' % (f, V)
s = re.sub(r'<img src="assets/h6/img/H6v7-(?:sky|cloud)-[a-z]+\.(?:webp|png)\?v=\d+" alt="">', '', s)
NEW = ''.join(tag('cloud-' + f) for f in ('src.webp', 'fill.webp', 'plate.webp', 'colour.webp', 'density.webp', 'data.webp', 'field.webp'))
assert s.count(tag('water-pool.webp')) == 1
s = s.replace(tag('water-pool.webp'), NEW + tag('water-pool.webp'))
s = s.replace('loads for motion (sky, water)', 'loads for motion (cloud lettering, water)')
open(P, 'w', encoding='utf-8').write(s); print('snippet updated')
