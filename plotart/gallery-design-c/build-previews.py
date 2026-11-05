"""DIRECTION C preview builder (DESIGN EXPLORATION ONLY; never part of a release).
Copies the live Virtual Gallery page (plotart/gallery/index.html at the branch base) and replaces only its
collection section with C1, C2 or Direction A markup, for 1, 5, 15 and 25 open galleries. Leah Hewson's data is
read unchanged from the page and her gallery.json. Every other artist is a clearly labelled MOCK placeholder."""
import re, html, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
base = open(os.path.join(ROOT, 'plotart/gallery/index.html'), encoding='utf-8').read()
leah_json = json.load(open(os.path.join(ROOT, 'plotart/artists/leah-hewson/gallery.json'), encoding='utf-8'))['artist']
SEC = re.compile(r'<section class="pa-vg2-collection".*?</section>', re.S)
live = SEC.search(base).group(0)
# Leah exactly as the live page and her approved gallery show her
m = re.search(r'<li class="pa-gcard is-founding"><a class="pa-gcard-tile" href="([^"]+)".*?<img src="([^"]+)" width="(\d+)" height="(\d+)" alt="([^"]*)".*?pa-gcard-name">([^<]+)</span><span class="pa-gcard-meta">([^<]+)</span>', live, re.S)
href, img600, w, h, alt, name, practice = m.groups()
assert name == leah_json['display_name'] and practice == html.escape(leah_json['practice'], quote=False)
LEAH = dict(pos=1, name=name, href=href, src=img600.replace('-600.', '-1200.'), src600=img600, w=int(w) * 2, h=int(h) * 2, alt=html.unescape(alt), practice=html.unescape(practice), mock=False)

meta = {d['i']: d for d in json.load(open(os.path.join(HERE, 'mock/meta.json')))}
ORDER = [3, 4, 5, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 2, 6, 9, 19, 20, 21, 22, 23, 24, 25]   # positions in the order mocks fill them
MOCKMAP = {3: 1, 4: 2, 5: 5, 7: 6}   # the five-artist view includes a dark and a monochrome mock work
left = [i for i in range(1, 25) if i not in MOCKMAP.values()]
for p in ORDER:
    if p not in MOCKMAP: MOCKMAP[p] = left.pop(0)
def mock(p):
    i = MOCKMAP[p]; d = meta[i]
    return dict(pos=p, name='Mock artist %s' % chr(64 + i), href='#mock', src='mock/mock-%02d-1200.webp' % i, src600='mock/mock-%02d-600.webp' % i,
                w=d['w'], h=d['h'], alt='Mock placeholder artwork (design preview only)', practice='Mock practice · design preview', mock=True)

SCEN = {1: dict(pub=[1], res={2}, prep={6, 9}),
        5: dict(pub=[1, 3, 4, 5, 7], res={2}, prep={6, 9}),
        15: dict(pub=[1, 3, 4, 5, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18], res={2}, prep={6, 9}),
        25: dict(pub=list(range(1, 26)), res=set(), prep=set())}
E = lambda s: html.escape(s, quote=True)
WORD = {'pub': 'Published', 'res': 'Reserved', 'prep': 'In preparation', 'av': 'Available'}

def state(sc, n):
    return 'pub' if n in sc['pub'] else 'res' if n in sc['res'] else 'prep' if n in sc['prep'] else 'av'
def artists(sc): return [LEAH if p == 1 else mock(p) for p in sorted(sc['pub'])]
def img(a):  # srcset widths are the files' true pixel widths (each file's LONG side is 600 or 1200)
    w1200 = a["w"]; w600 = round(a["w"] / 2)
    return (f'<img src="{a["src"]}" srcset="{a["src600"]} {w600}w, {a["src"]} {w1200}w" sizes="(max-width:639px) 100vw, 680px" '
                    f'width="{a["w"]}" height="{a["h"]}" alt="{E(a["alt"])}" loading="lazy" decoding="async">')
def counts(sc):
    c = {k: sum(1 for n in range(1, 26) if state(sc, n) == k) for k in WORD}
    return c
def head(sc):
    return (f'<div class="vgc-head"><div><p class="vgc-eyebrow">The Founding 25</p><h2 id="vgColH">The first twenty-five galleries.</h2></div>'
            f'<p class="vgc-count">{len(sc["pub"])} of 25 galleries open</p></div>')
NOTE_IDX = 'Twenty-five numbered positions, one for each Founding Artist. A gallery opens here when the artist&rsquo;s work is published.'

def c1(sc):
    works = ''.join(f'''<li class="vgc-work"><div class="vgc-art">{img(a)}</div>
      <div class="c1-label"><span class="c1-n"><span class="vgc-sr">Position </span>{a["pos"]:02d}</span><h3 class="vgc-name"><a href="{a["href"]}">{E(a["name"])}</a></h3>
      <p class="vgc-practice">{E(a["practice"])}</p><span class="vgc-enter" aria-hidden="true">Enter the gallery &rarr;</span></div></li>''' for a in artists(sc))
    by = {a['pos']: a for a in artists(sc)}
    def pos(n):
        s = state(sc, n)
        inner = f'<a href="{by[n]["href"]}">{E(by[n]["name"])}</a>' if s == 'pub' else WORD[s]
        return f'<li class="c1-pos is-{s}"><b>{n:02d}</b><span>{inner}</span></li>'
    c = counts(sc)
    key = ''.join(f'<li><b>{c[k]}</b> {WORD[k].lower()}</li>' for k in WORD if c[k])
    return f'''<section class="vgc c1" aria-labelledby="vgColH"><div class="pa-wrap">{head(sc)}
  <ol class="vgc-hang" aria-label="Open galleries">{works}</ol>
  <div class="vgc-index" role="region" aria-labelledby="vgIdx"><h3 id="vgIdx">The Founding 25</h3><p class="vgc-index-note">{NOTE_IDX}</p>
    <ul class="vgc-key" aria-label="Summary">{key}</ul>
    <ol class="c1-list" aria-label="All twenty-five positions">{''.join(pos(n) for n in range(1, 26))}</ol></div></div></section>'''

def c2(sc):
    works = ''.join(f'''<li class="vgc-work"><div class="vgc-art">{img(a)}</div>
      <div class="c2-label"><span class="c2-n" aria-hidden="true">{a["pos"]:02d}</span><div><h3 class="vgc-name"><a href="{a["href"]}"><span class="vgc-sr">Position {a["pos"]:02d}: </span>{E(a["name"])}</a></h3>
      <p class="vgc-practice">{E(a["practice"])}</p><span class="vgc-enter" aria-hidden="true">Enter the gallery &rarr;</span></div></div></li>''' for a in artists(sc))
    by = {a['pos']: a for a in artists(sc)}
    def cell(n):
        s = state(sc, n)
        if s == 'pub':
            return f'<li class="c2-cell is-pub"><a href="{by[n]["href"]}"><b>{n:02d}</b><span>{E(by[n]["name"])}</span></a></li>'
        return f'<li class="c2-cell is-{s}"><b>{n:02d}</b><span>{WORD[s]}</span></li>'
    c = counts(sc)
    key = ''.join(f'<li><span class="k k-{k}" aria-hidden="true"></span><b>{c[k]}</b> {WORD[k].lower()}</li>' for k in WORD if c[k])
    line = ''.join(f'<li class="is-{state(sc, n)}"></li>' for n in range(1, 26))
    names = ''.join(f'<li><b>{a["pos"]:02d}</b><a href="{a["href"]}">{E(a["name"])}</a></li>' for a in artists(sc))
    return f'''<section class="vgc c2" aria-labelledby="vgColH"><div class="pa-wrap">{head(sc)}
  <ol class="vgc-hang" aria-label="Open galleries">{works}</ol>
  <div class="vgc-index" role="region" aria-labelledby="vgIdx"><h3 id="vgIdx">The Founding 25</h3><p class="vgc-index-note">{NOTE_IDX}</p>
    <ol class="c2-line" aria-hidden="true">{line}</ol>
    <ul class="vgc-key c2-key" aria-label="Summary">{key}</ul>
    <ol class="c2-plan" aria-label="All twenty-five positions">{''.join(cell(n) for n in range(1, 26))}</ol>
    <ol class="c2-names" aria-label="Open galleries by position">{names}</ol></div></div></section>'''

def dir_a(sc):  # Direction A exactly as proposed earlier today, same content (A had no "in preparation" state)
    by = {a['pos']: a for a in artists(sc)}
    works = ''.join(f'''<li class="vga-work"><a href="{a["href"]}"><span class="vga-art">{img(a)}</span>
      <span class="vga-label"><span class="vga-n">{a["pos"]:02d}</span><span class="vga-name">{E(a["name"])}</span><span class="vga-practice">{E(a["practice"])}<span class="vga-founding">Founding Artist</span></span></span></a></li>''' for a in artists(sc))
    plates = ''.join(f'<li class="vga-plate is-on"><b>{n:02d}</b><a href="{by[n]["href"]}">{E(by[n]["name"])}</a></li>' if n in by else
                     (f'<li class="vga-plate is-reserved"><b>{n:02d}</b><span>Reserved</span></li>' if n in sc['res'] else f'<li class="vga-plate"><b>{n:02d}</b><span>Open</span></li>') for n in range(1, 26))
    return f'''<section class="vga-wall" aria-labelledby="vgColH"><div class="pa-wrap">
  <div class="vga-head"><h2 id="vgColH">The first twenty-five galleries.</h2><p class="vga-count">{len(sc["pub"])} of 25 galleries open</p></div>
  <ol class="vga-works" aria-label="Open galleries">{works}</ol></div></section>
<section class="vga-index" aria-labelledby="vgIdx"><div class="pa-wrap"><h3 id="vgIdx">Founding positions</h3>
  <p class="vga-note">Twenty-five positions, each held for one Founding Artist. Galleries open here as each artist joins.</p>
  <ol class="vga-plates">{plates}</ol></div></section>'''

BANNER = ('<p style="margin:0;padding:10px 16px;background:#5a3f2f;color:#F2EBE0;font:600 14px/1.4 system-ui,sans-serif;text-align:center">'
          'DESIGN PREVIEW · {label} · not the live site.{mock}</p>')
def page(fn, label, section, css, n):
    hh = SEC.sub(lambda _: section, base, count=1)
    links = ''.join(f'<link rel="stylesheet" href="{c}">\n' for c in css)
    hh = hh.replace('</head>', '<meta name="robots" content="noindex, nofollow">\n' + links + '</head>', 1)
    mk = '' if n == 1 else f' {n - 1} of the {n} open galleries are MOCK placeholders, not real artists.'
    mk += ' Reserved and in-preparation positions are illustrative.' if n < 25 else ''
    hh = hh.replace('<main id="main">', '<main id="main">' + BANNER.format(label=label, mock=mk), 1)
    hh = hh.replace('src="../assets/', 'src="../assets/').replace('<a class="pa-skip"', '<a class="pa-skip"')
    open(os.path.join(HERE, fn), 'w', encoding='utf-8').write(hh)

for n, sc in SCEN.items():
    page(f'c1-{n}.html', f'Direction C1 · Dark Viewing Room · {n} open', c1(sc), ['c-shared.css', 'c1.css'], n)
    page(f'c2-{n}.html', f'Direction C2 · Curated Collection · {n} open', c2(sc), ['c-shared.css', 'c2.css'], n)
    page(f'a-{n}.html', f'Direction A (for comparison) · {n} open', dir_a(sc), ['a.css'], n)
print('built', len(SCEN) * 3, 'pages')
