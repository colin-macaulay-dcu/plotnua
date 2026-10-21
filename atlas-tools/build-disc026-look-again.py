#!/usr/bin/env python3
"""DISC-026 · "Look again at your house" · integration builder.

Founder approval: V2 visual preview APPROVED FOR INTEGRATION, 15 October 2026.
Copy: the R2 draft (every claim already on the page), unchanged through V1 and V2.

What --apply does to discovery-house-as-power-station.html, and nothing else:
  1. adds <style id="lag-css"> before </head>          (look-again.css)
  2. adds the section directly after <main id="pn-main"> (look-again.html),
     between LOOK-AGAIN:BEGIN / END markers
  3. adds <script id="lag-js"> before </body>           (look-again.js)
  4. adds five id attributes to existing elements so the section's
     "Where the page explains this" links have somewhere to land:
     home-compute (S3), data-centre-heat (S4), anat-roof, anat-battery,
     anat-grid (S7 positions). No text, class or other attribute changes.

Modes:
  --apply   refuses unless the article is the V3 baseline (37139b2b...)
  --check   verifies the applied article: guards L1-L13
  --prove   breaks each guard in memory and shows it fires (no file written)
"""
import hashlib, html, pathlib, re, sys
from search_rail_layer import without_ask_label  # 19 Oct 2026 rail label layer
from derivative_picture_layer import without_derivative_picture  # 20 Oct 2026 WebP hero wrap
from disc026_seo_a_layer import without_seo_a  # 20 Oct 2026 SEO Approach A, revised 1b (title, description, anchors)
from disc026_facts_oct2026_layer import without_facts  # 20 Oct 2026 factual corrections F1-F5 (article passages)
from disc026_bridge_oct2026_layer import without_bridge  # 21 Oct 2026 Stage 2 bridge section (exact, reversible)
HERO_SRC = 'assets/img/fec77c3f0bae107a.jpg'

ROOT = pathlib.Path(__file__).resolve().parent.parent
ART = ROOT / 'discovery-house-as-power-station.html'
FRAG = ROOT / 'atlas-tools' / 'disc026-look-again'
BASELINE_SHA = '37139b2b760bbf073ae543d4d67618b60478cb82fe2c06ba40cb9f81925e9ee1'  # freeze V3

BEGIN = '<!-- LOOK-AGAIN:BEGIN · founder-approved 15 Oct 2026 · built by atlas-tools/build-disc026-look-again.py -->\n'
END = '<!-- LOOK-AGAIN:END -->\n'
MAIN_OPEN = '<main id="pn-main">\n'

# (old, new): each old must occur exactly once in the baseline
ANCHORS = [
    ('  <section class="article-section reveal">\n    <div class="kicker">Home compute &middot; useful heat</div>',
     '  <section class="article-section reveal" id="home-compute">\n    <div class="kicker">Home compute &middot; useful heat</div>'),
    ('  <section class="article-section reveal">\n    <div class="kicker">Data centres &middot; useful heat</div>',
     '  <section class="article-section reveal" id="data-centre-heat">\n    <div class="kicker">Data centres &middot; useful heat</div>'),
    ('      <div class="pos">\n        <span class="pos-where">1 &middot; Roof',
     '      <div class="pos" id="anat-roof">\n        <span class="pos-where">1 &middot; Roof'),
    ('      <div class="pos">\n        <span class="pos-where">2 &middot; Utility room',
     '      <div class="pos" id="anat-battery">\n        <span class="pos-where">2 &middot; Utility room'),
    ('      <div class="pos">\n        <span class="pos-where">7 &middot; The grid connection',
     '      <div class="pos" id="anat-grid">\n        <span class="pos-where">7 &middot; The grid connection'),
]

LABELS = {'is-today': 'Here today', 'is-ie': 'Being worked on in Ireland',
          'is-abroad': 'Operating elsewhere, not in Ireland', 'is-large': 'Large sites in Ireland, not homes'}
DENIAL = 'None of this is available to an Irish homeowner today.'      # the section's own
PAGE_DENIAL = 'None of it is open to an Irish homeowner.'                  # the article's, since a949ccc
NAMED_ALLOWED = ['ESB Networks', 'Tallaght', 'Tandem Compute', 'Sustainable Energy Communities', 'Germany', 'Britain']
NAMED_BANNED = ['heata', 'Thermify', 'Deep Green', 'Zai', 'Sky Fusion', 'SPAN', 'Sunrun', 'Voltus', 'CYANIS',
                'Amazon', 'Bit Warmer', 'paying the households', 'worth investigating']
FILE_LINKS = ['disc026-power-station.html', 'disc026-compute-readiness-check.html']


def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode()).hexdigest()


def frags():
    css = (FRAG / 'look-again.css').read_text()
    sec = (FRAG / 'look-again.html').read_text()
    js = (FRAG / 'look-again.js').read_text()
    return ('<style id="lag-css">\n' + css + '</style>\n',
            BEGIN + sec + END,
            '<script id="lag-js">\n' + js + '</script>\n')


def build(base):
    css, sec, js = frags()
    out = base
    assert out.count('</head>') == 1 and out.count(MAIN_OPEN) == 1 and out.count('</body>') == 1
    out = out.replace('</head>', css + '</head>')
    out = out.replace(MAIN_OPEN, MAIN_OPEN + sec)
    out = out.replace('</body>', js + '</body>')
    for old, new in ANCHORS:
        assert out.count(old) == 1, 'anchor context not unique: ' + old[:60]
        out = out.replace(old, new)
    return out


def unbuild(text):
    """Remove exactly what --apply adds; the result must be the baseline."""
    css, sec, js = frags()
    out = text.replace(css, '', 1).replace(sec, '', 1).replace(js, '', 1)
    for old, new in ANCHORS:
        out = out.replace(new, old, 1)
    return out


def section_of(text):
    a = text.find(BEGIN); b = text.find(END)
    return text[a:b] if a >= 0 and b > a else ''


def visible_text(fragment):
    t = re.sub(r'<svg.*?</svg>', ' ', fragment, flags=re.S)
    t = re.sub(r'<!--.*?-->', ' ', t, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', html.unescape(t))


def explorer_region(text):
    a = text.find('<section class="article-section reveal" id="explore-providers"')
    b = text.find('</section>', a)
    return text[a:b] if a >= 0 else ''


def guards(text, base):
    fails = []
    def need(code, ok, msg):
        if not ok: fails.append(f'{code}: {msg}')
    css, secb, js = frags()
    sec = section_of(text)
    vis = visible_text(sec)
    # L1 inserted exactly once, byte-identical to the fragments
    need('L1', text.count(css) == 1 and text.count(secb) == 1 and text.count(js) == 1 and text.count(BEGIN) == 1,
         'section, style or script missing, duplicated or edited in place')
    # L2 everything else is the V3 baseline
    # (read through the search rail label layer, 19 Oct 2026: search_rail_layer.py)
    # and through the WebP derivative layer, 20 Oct 2026: derivative_picture_layer.py
    # and through the SEO Approach A layer and the October 2026 factual corrections,
    # 20 Oct 2026: disc026_seo_a_layer.py, disc026_facts_oct2026_layer.py (exact, reversible).
    # F5a, the balcony line, is part of this section's own fragment and is held by L1.
    # and through the Stage 2 bridge layer, 21 Oct 2026: disc026_bridge_oct2026_layer.py.
    need('L2', sha(without_derivative_picture(without_ask_label(without_bridge(without_facts(without_seo_a(unbuild(text))))), HERO_SRC)) == BASELINE_SHA,
         'outside the section, the article differs from the V3 baseline')
    # L3 placement: directly after <main>
    need('L3', MAIN_OPEN + BEGIN in text, 'section is not directly after <main id="pn-main">')
    # L4 labels: only the four, one per revelation
    revs = re.findall(r'<div class="lag-rev"[^>]*>(.*?)</p>\s*</div>', sec, flags=re.S)
    mks = re.findall(r'<span class="lag-mk ([a-z-]+)">([^<]*)</span>', sec)
    need('L4', len(revs) == 11 and all(r.count('class="lag-mk ') == 1 for r in revs)
         and all(LABELS.get(k) == v for k, v in mks), 'availability labels: not exactly the four, or a revelation without one')
    # L5 the six discoveries
    names = re.findall(r'<span class="lag-ch-name">([^<]*)</span>', sec)
    need('L5', names == ['Generate', 'Store and share', 'Harvest heat', 'Host computing', 'Connect', 'Earn'],
         'the six discoveries are not all present, in order')
    # L6 the denial sits inside Host computing, and the page's own denial is untouched
    c4 = sec[sec.find('id="lag-c4"'):sec.find('id="lag-c5"')]
    need('L6', DENIAL in c4 and PAGE_DENIAL in re.sub(r'\s+', ' ', html.unescape(unbuild(text))), 'the Irish denial is missing from Host computing')
    # L7 no money, no figures (only 2023 and the chapter numbers 1-6)
    digits = set(re.findall(r'\d+', vis))
    need('L7', not re.search(r'[£€$]|\bEUR\b|\bGBP\b|A\$', vis) and digits <= {'1', '2', '3', '4', '5', '6', '2023'},
         f'currency or a figure in the section: {sorted(digits)}')
    # L8 names: only those already on the page; never the banned ones
    need('L8', all(n in unbuild(text) for n in NAMED_ALLOWED) and not any(n.lower() in vis.lower() for n in NAMED_BANNED),
         'a name in the section that the page does not already carry')
    # L9 every link lands
    ids = set(re.findall(r'\bid="([^"]+)"', text))
    hrefs = re.findall(r'href="([^"]+)"', sec)
    need('L9', all((h[1:] in ids) if h.startswith('#') else (h in FILE_LINKS and (ROOT / h).exists()) for h in hrefs)
         and {'#explore-providers', 'disc026-power-station.html', 'disc026-compute-readiness-check.html'} <= set(hrefs),
         f'a link that does not land, or a required link missing: {hrefs}')
    # L10 Explorer, Property Check, search, navigation untouched
    need('L10', explorer_region(text) == explorer_region(base) and explorer_region(base) != ''
         and text.count('href="disc026-power-station.html"') == base.count('href="disc026-power-station.html"') + 1
         and 'id="pnsOpen"' in text and '<nav class="footer-cols"' in text,
         'Explorer, Property Check, search or footer navigation changed')
    # L11 ids unique across the page
    allids = re.findall(r'\bid="([^"]+)"', text)
    need('L11', len(allids) == len(set(allids)), 'duplicate id on the page')
    # L12 accessibility and motion
    need('L12', 'prefers-reduced-motion' in css and "prefers-reduced-motion" in js and 'aria-labelledby="lag-title"' in sec
         and '<desc id="lag-desc">' in sec and ':focus-visible' in css, 'reduced motion, labelling or focus styling missing')
    # L13 nothing readable is hidden without JS: hidden-until-lit elements live only inside the drawing
    outside_svg = re.sub(r'<svg.*?</svg>', '', sec, flags=re.S)
    need('L13', 'lag-show' not in outside_svg and 'hidden' not in outside_svg,
         'words are hidden until script runs')
    return fails


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--check'
    text = ART.read_text()
    if mode == '--apply':
        if sha(text) != BASELINE_SHA:
            sys.exit('REFUSED: the article is not the V3 baseline (37139b2b...); nothing written')
        out = build(text)
        f = guards(out, text)
        if f:
            sys.exit('REFUSED, nothing written:\n  ' + '\n  '.join(f))
        ART.write_text(out)
        print('APPLIED · new SHA-256', sha(out), '·', len(out.encode()), 'bytes')
        return
    base = unbuild(text)
    if mode == '--check':
        f = guards(text, base)
        if f:
            print('CHECK FAILED\n  ' + '\n  '.join(f)); sys.exit(1)
        print('CHECK OK — L1-L13 pass · SHA-256', sha(text), '·', len(text.encode()), 'bytes')
        return
    if mode == '--prove':
        breaks = [
            ('L1', lambda t: t.replace('<div class="lag-truth">', '<div class="lag-truth"> ', 1)),
            ('L2', lambda t: t.replace('<h2>The energy anatomy of your property</h2>', '<h2>The energy anatomy</h2>', 1)),
            ('L4', lambda t: t.replace('<span class="lag-mk is-abroad">Operating elsewhere, not in Ireland</span>',
                                       '<span class="lag-mk is-abroad">Coming soon</span>', 1)),
            ('L6', lambda t: t.replace('<strong>' + DENIAL + '</strong>', '<strong>Available soon.</strong>', 1)),
            ('L7', lambda t: t.replace('A business pays for the electricity;', 'A business pays &euro;30 a month for the electricity;', 1)),
            ('L8', lambda t: t.replace('In Britain there are occupied homes', 'In Britain, heata has occupied homes', 1)),
            ('L9', lambda t: t.replace('href="#anat-grid"', 'href="#anat-nowhere"', 1)),
            ('L10', lambda t: t.replace('<h2 id="px-title">Explore how suppliers pay for export</h2>', '<h2 id="px-title">Suppliers</h2>', 1)),
            ('L11', lambda t: t.replace('id="anat-roof"', 'id="anat-battery"', 1)),
            ('L13', lambda t: t.replace('<p class="lag-flag">', '<p class="lag-flag" hidden>', 1)),
        ]
        ok = 0
        for code, brk in breaks:
            broken = brk(text)
            assert broken != text, code + ' mutation did not apply'
            fired = [x.split(':')[0] for x in guards(broken, base)]
            hit = code in fired
            ok += hit
            print(f'  {code}: {"caught" if hit else "MISSED"}  (fired: {", ".join(fired) or "none"})')
        print(f'{ok}/{len(breaks)} guards caught their break —', 'PROVEN' if ok == len(breaks) else 'NOT PROVEN')
        sys.exit(0 if ok == len(breaks) else 1)
    sys.exit('usage: --apply | --check | --prove')


if __name__ == '__main__':
    main()
