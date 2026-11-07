#!/usr/bin/env python3
"""Buyer-guide integrity, availability and content-boundary checks. Offline; no artist records changed."""
import copy
import json
import re
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path
from html.parser import HTMLParser

import plotart_search_content as C
import plotart_seo as SEO

ROOT = Path(__file__).resolve().parent.parent
B = runpy.run_path(str(ROOT / 'atlas-tools/build-plotart-buyers.py'))
packages = SEO.public_packages(ROOT)
checks = []


def check(label, ok):
    checks.append(bool(ok))
    print(('PASS ' if ok else 'FAIL ') + label)


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.h1 = 0
        self.ids = []
        self.links = []
        self.images = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.h1 += tag == 'h1'
        if a.get('id'):
            self.ids.append(a['id'])
        if a.get('href'):
            self.links.append(a['href'])
        if tag == 'img':
            self.images.append(a)


for path in SEO.GUIDE_PATHS:
    doc = (ROOT / 'plotart' / path).read_text()
    parsed = Page(doc)
    check(path + ': exact reviewed copy and live collection', doc == B['render'](path, packages))
    check(path + ': one H1 and unique IDs', parsed.h1 == 1 and len(parsed.ids) == len(set(parsed.ids)))
    check(path + ': exact approved generated region', C.update(doc, path, packages) == doc)
    check(path + ': local links and anchors resolve', all(
        (ref[1:] in parsed.ids if ref.startswith('#') else (ROOT / 'plotart' / ref.split('#')[0] / ('index.html' if ref.endswith('/') else '')).exists())
        for ref in parsed.links if not ref.startswith(('https:', 'http:', 'mailto:', '/'))))
    check(path + ': no checkout, new form or purchase claim', not re.search(r'<form|add to cart|buy now|checkout', doc, re.I))
    check(path + ': all images have alt text and explicit dimensions', all('alt' in i and i.get('width') and i.get('height') for i in parsed.images))
    check(path + ': no numeric price outside the generated region', '€' not in C.outside(doc))
check('stylesheet matches reviewed source', (ROOT / 'plotart/assets/plotart-guides.css').read_text() == B['CSS'])
check('artwork display preserves the whole image', 'object-fit:contain' in B['CSS'] and 'object-fit:cover' not in B['CSS'])

# Self-contained fixtures: these checks must work even when there are no real public galleries.
fixture = {
    'artist': {'slug': 'leah-hewson', 'display_name': 'Test Artist'},
    'publication': {'state': 'approved'},
    'works': [{'slug': 'test-work', 'title': 'Test Work', 'availability': 'available', 'price_eur': 4321,
               'medium': 'Acrylic', 'h_cm': 20, 'w_cm': 30,
               'images': [{'role': 'main', 'alt': 'Test art', 'derivatives': [
                   {'file': 'test-work-1200.webp', 'long_edge': 1200, 'pixels': [1200, 800]}]}]}]
}
buy, abstract = SEO.GUIDE_PATHS
check('published asking price comes from the work', '€4,321' in C.content(buy, [fixture]))
check('abstract selection links to the exact artwork', 'artists/leah-hewson/test-work.html' in C.content(abstract, [fixture]))
for state in ('sold', 'reserved', 'archived', 'not_for_sale'):
    p = copy.deepcopy(fixture)
    p['works'][0]['availability'] = state
    check(state + ': no price or artwork in available selections', all('€4,321' not in C.content(path, [p]) and 'test-work.html' not in C.content(path, [p]) for path in SEO.GUIDE_PATHS))
p = copy.deepcopy(fixture)
p['works'][0]['price_eur'] = None
check('price on request does not invent a figure', 'Price on request' in C.content(buy, [p]) and '€' not in C.content(buy, [p]))
p = copy.deepcopy(fixture)
p['artist']['slug'] = 'new-test'
check('new artist is priced but never automatically classified as abstract', '€4,321' in C.content(buy, [p]) and 'new-test' not in C.content(abstract, [p]))
for path in SEO.GUIDE_PATHS:
    check(path + ': empty state has no stale artwork or price', 'test-work.html' not in C.content(path, []) and '€' not in C.content(path, []))
p = copy.deepcopy(fixture)
p['publication']['state'] = 'draft'
try:
    C.content(buy, [p])
    check('draft data is refused', False)
except ValueError:
    check('draft data is refused', True)

with tempfile.TemporaryDirectory(prefix='pa-buyer-boundary-') as temp:
    site = Path(temp)

    def git(*args):
        return subprocess.check_output(['git', *args], cwd=site, text=True, stderr=subprocess.DEVNULL).strip()

    def write(path, text):
        dest = site / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)

    def commit():
        git('add', '.')
        git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'Guide fixture')
        return git('rev-parse', 'HEAD')

    def boundary(base, rel):
        return subprocess.run([sys.executable, str(ROOT / 'atlas-tools/release/plotart-content-boundary.py'), base, rel, '--instant'],
                              cwd=site, capture_output=True, text=True).returncode

    git('init', '-q')
    old = '<main><h1>Pinned guide text</h1>' + C.BEGIN + C.END + '</main>'
    before = {}
    for path in SEO.GUIDE_PATHS:
        before[path] = C.update(old, path, [fixture])
        write('plotart/' + path, before[path])
    write('plotart/artists/leah-hewson/gallery.json', json.dumps(fixture))
    base = commit()
    withdrawn = copy.deepcopy(fixture)
    withdrawn['works'] = []
    write('plotart/artists/leah-hewson/gallery.json', json.dumps(withdrawn))
    for path in SEO.GUIDE_PATHS:
        write('plotart/' + path, C.update(before[path], path, [withdrawn]))
    good = commit()
    check('boundary accepts exact automatic withdrawal cleanup', boundary(base, good) == 0)
    for label, mutate in (
        ('editorial text changed', lambda t: t.replace('Pinned guide text', 'Different guide text')),
        ('unapproved price inserted in region', lambda t: t.replace(C.END, '<p>€1</p>' + C.END)),
        ('collection markers removed', lambda t: t.replace(C.BEGIN, '')),
    ):
        git('reset', '--hard', good)
        path = 'plotart/' + buy
        write(path, mutate((site / path).read_text()))
        bad = commit()
        check('boundary refuses ' + label, boundary(good, bad) != 0)

print('PLOTART BUYERS · %d checks, %d passed, %d failed' % (len(checks), sum(checks), len(checks) - sum(checks)))
sys.exit(0 if all(checks) else 1)
