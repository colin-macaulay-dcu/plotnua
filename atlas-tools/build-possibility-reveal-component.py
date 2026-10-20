#!/usr/bin/env python3
"""POSSIBILITY REVEAL · HOMEPAGE COMPONENT (Phase 4 D2, 19 Oct 2026)

Package the approved L2B Prototype v2 as an isolated homepage component.

MECHANICAL TRANSFORM ONLY. Input: the unmodified prototype (index.html, assets/*).
Output: assets/possibility-reveal/{reveal.css,reveal.js,reveal-data.js} and a markup
snippet for #heroStage. Behaviour, sequencing, timings, camera values, beacon coordinates,
copy, drawings and data are copied byte-for-byte except for these isolation changes:
  1. every CSS rule is scoped under the component root (.pr); :root/html/body -> .pr
  2. @keyframes are renamed pr-* (and their animation references)
  3. every DOM id is namespaced pr-* (markup, CSS, JS, SVG url(#) references)
  4. JS looks up elements inside the component root, not the whole document;
     document-level click/keydown listeners ignore events from outside the component
  5. the prototype's <h1> becomes an <h2> (class pr-title): the page keeps one H1
  6. stage height, top safe inset and two grounds become CSS variables whose
     defaults are the prototype's own values (100svh / 0 / its greens)
  7. image paths point to assets/possibility-reveal/img/
  9. the mounted snippet is kept as stage-snippet.part, not .html, so it is never served
     as a stand-alone page showing the illustration without its label (P8, standard 3)
  8. ONE founder-approved wording change (19 Oct 2026, PN-FDR-2026-10-19-01, standard 3):
     the legend note "...not part of the photograph." reads "...not part of the picture."
     The scene is an AI-generated illustration, so it is not called a photograph.
Images are NOT made here: see build-possibility-reveal-images.py.

  python3 atlas-tools/build-possibility-reveal-component.py --source PROTOTYPE_DIR   build + mount
  python3 atlas-tools/build-possibility-reveal-component.py --check                  guard (no source needed)
  python3 atlas-tools/build-possibility-reveal-component.py --check --source DIR     guard + fresh-transform match

The guard refuses if: a generated file differs from its record; the snippet is not
mounted verbatim in index.html#heroStage; any component CSS rule is unscoped; the
component carries an <h1>, an un-prefixed id or a reserved homepage id; the script
looks anything up outside its root; or commerce is enabled / an offer is active."""
import re, sys, os, hashlib, json
IDS = ['pn','stage','cam','photo','hidden','sc-ground','sc-wind','sc-compute','lens','lensGrip','beacons','lensLabel',
       'layers','paths','bar','pathName','dots','btnReplay','btnHome','caption','more','introTitle','capTitle','moreTitle',
       'irisClip','cylClip','soil','soilEdge','warm']
KF = ['flow','spin','blink','ping','rise']
P = 'pr-'
def rd(p): return open(os.path.join(SRC, p), encoding='utf-8').read()
def transform():
    global css, js, data, snippet

    # ---------------- CSS ----------------
    def scope_sel(sel):
        sel = sel.strip()
        if not sel: return sel
        for i in IDS: sel = re.sub(r'#%s\b' % re.escape(i), '#' + P + i, sel)
        sel = sel.replace('.intro h1', '.intro .pr-title')
        if sel in (':root', 'html', 'body'): return '.pr'
        if sel == '*': return '.pr, .pr *'
        if sel.startswith('[data-mode') or sel.startswith('.lens-over-intro'): return '.pr' + sel   # root-state selectors: the class/attribute sits ON the root
        return '.pr ' + sel
    def scope_block(css):
        out = []; i = 0
        while i < len(css):
            j = css.find('{', i)
            if j < 0: out.append(css[i:]); break
            head = css[i:j]
            lm = re.match(r'(\s*(?:/\*.*?\*/\s*)*)', head, re.S); lead0 = lm.group(1); hs = head[len(lead0):].strip()
            if hs.startswith('@media') or hs.startswith('@supports'):
                depth = 1; k = j + 1
                while depth:
                    if css[k] == '{': depth += 1
                    elif css[k] == '}': depth -= 1
                    k += 1
                out.append(head + '{' + scope_block(css[j+1:k-1]) + '}'); i = k; continue
            if hs.startswith('@keyframes'):
                depth = 1; k = j + 1
                while depth:
                    if css[k] == '{': depth += 1
                    elif css[k] == '}': depth -= 1
                    k += 1
                name = head.strip().split()[1]
                out.append(head.replace(name, P + name) + css[j:k]); i = k; continue
            k = css.find('}', j)
            # keep leading comments/whitespace of the head
            m = re.match(r'(\s*(?:/\*.*?\*/\s*)*)(.*)$', head, re.S)
            lead, sels = m.group(1), m.group(2)
            out.append(lead + ','.join(scope_sel(s) for s in sels.split(',')) + css[j:k+1]); i = k + 1
        return ''.join(out)
    css = rd('assets/reveal.css')
    css = scope_block(css)
    css = re.sub(r'(animation(?:-name)?\s*:\s*)([a-z]+)', lambda m: m.group(1) + (P + m.group(2) if m.group(2) in KF else m.group(2)), css)
    # 6 · integration variables (defaults = the prototype's own values)
    rep = [
     ('.pr .stage{position:relative;width:100%;height:100vh;height:100svh;min-height:560px;max-height:1100px;overflow:hidden;background:#24331f;isolation:isolate}',
      '.pr .stage{position:relative;width:100%;height:var(--pr-stage-h,100vh);height:var(--pr-stage-h,100svh);min-height:var(--pr-stage-min,560px);max-height:var(--pr-stage-max,1100px);overflow:hidden;background:var(--pr-stage-bg,#24331f);isolation:isolate}'),
     ('.pr .layers{position:absolute;z-index:6;top:14px;', '.pr .layers{position:absolute;z-index:6;top:calc(14px + var(--pr-safe-top,0px));'),
     ('.pr .bar{position:absolute;z-index:7;top:14px;', '.pr .bar{position:absolute;z-index:7;top:calc(14px + var(--pr-safe-top,0px));'),
     ('.pr .caption.pos-tr{top:68px;', '.pr .caption.pos-tr{top:calc(68px + var(--pr-safe-top,0px));'),
     ('.pr .more{position:absolute;z-index:9;top:0;', '.pr .more{position:absolute;z-index:9;top:var(--pr-safe-top,0px);'),
     ('background:#0f1c15}', 'background:var(--pr-legend-bg,#0f1c15)}'),
     ('.pr{margin:0;background:#0f1c15;', '.pr{margin:0;background:var(--pr-legend-bg,#0f1c15);'),
     ('.pr .stage{min-height:600px;max-height:none}', '.pr .stage{min-height:var(--pr-stage-min-m,600px);max-height:none}'),
     ('.pr .intro{top:56px;', '.pr .intro{top:calc(56px + var(--pr-safe-top,0px));'),
     ('.pr .bar{top:10px;', '.pr .bar{top:calc(10px + var(--pr-safe-top,0px));'),
    ]
    for a, b in rep:
        n = css.count(a)
        assert n == 1, ('css anchor', n, a)
        css = css.replace(a, b)
    css = '/* PlotNua Possibility Reveal · L2B v2 · homepage component (generated by build_reveal_component.py; do not hand-edit) */\n' + css

    # ---------------- JS ----------------
    js = rd('assets/reveal.js')
    def jrep(a, b, n=1):
        global js
        c = js.count(a); assert c == n, ('js anchor', c, a); js = js.replace(a, b)
    jrep('  var $ = function (s, r) { return (r || document).querySelector(s); };',
         '  var ROOT = document.querySelector("[data-pr-root]");\n  if (!ROOT) return;\n  var $ = function (s, r) { return (r || ROOT).querySelector(s); };')
    jrep('document.querySelectorAll(".scene")', 'ROOT.querySelectorAll(".scene")', 2)
    jrep('document.querySelectorAll(".cam source, .cam img")', 'ROOT.querySelectorAll(".cam source, .cam img")')
    jrep('  document.addEventListener("click", function (e) {\n',
         '  document.addEventListener("click", function (e) {\n    if (!ROOT.contains(e.target)) return;\n')
    jrep('  document.addEventListener("keydown", function (e) {\n',
         '  document.addEventListener("keydown", function (e) {\n    if (e.target !== document.body && !ROOT.contains(e.target)) return;\n')
    for i in IDS:
        js = re.sub(r'(["\'])#%s\b' % re.escape(i), r'\1#' + P + i, js)
        js = re.sub(r'id=\\?"%s"' % re.escape(i), 'id="' + P + i + '"', js)
        js = js.replace('.id === "%s"' % i, '.id === "%s%s"' % (P, i))
    js = js.replace('"#sc-" +', '"#' + P + 'sc-" +')
    # the root is the component element itself (querySelector inside it cannot return it)
    assert js.count('var pn = $("#pr-pn")') == 1
    js = js.replace('var pn = $("#pr-pn")', 'var pn = ROOT')
    assert js.count('"#pr-sc-" +') == 1
    js = '/* PlotNua Possibility Reveal · L2B v2 · homepage component (generated; do not hand-edit) */\n' + js
    data = rd('assets/reveal-data.js')

    # ---------------- markup ----------------
    h = rd('index.html')
    body = h[h.index('<a class="skip"'):h.index('</noscript>') + len('</noscript>')]
    for i in IDS:
        body = re.sub(r'id="%s"' % re.escape(i), 'id="%s%s"' % (P, i), body)
        body = re.sub(r'url\(#%s\)' % re.escape(i), 'url(#%s%s)' % (P, i), body)
        body = re.sub(r'aria-(labelledby|controls)="%s"' % re.escape(i), r'aria-\1="%s%s"' % (P, i), body)
        body = body.replace('href="#%s"' % i, 'href="#%s%s"' % (P, i))
    body = body.replace('<main class="pn" id="pr-pn" data-mode="entry">', '<div class="pr pn" id="pr-pn" data-mode="entry" data-pr-root>')
    # the prototype's skip link sits before <main>; move it inside the component root so its scoped styles apply
    skip = re.search(r'<a class="skip" href="#pr-paths">[^<]*</a>\s*', body).group(0)
    body = body.replace(skip, '', 1).replace('data-pr-root>', 'data-pr-root>\n  ' + skip.strip(), 1)
    assert body.count('</main>') == 1; body = body.replace('</main>', '</div>')
    WORD_OLD = 'Drawings are illustrations, not part of the photograph.'
    WORD_NEW = 'Drawings are illustrations, not part of the picture.'
    assert body.count(WORD_OLD) == 1, 'founder wording change: anchor not found exactly once'
    body = body.replace(WORD_OLD, WORD_NEW)
    assert body.count('<h1 id="pr-introTitle">') == 1
    body = body.replace('<h1 id="pr-introTitle">', '<h2 class="pr-title" id="pr-introTitle">').replace('power station.</h1>', 'power station.</h2>')
    body = body.replace('img/house-L1-L2A', 'assets/possibility-reveal/img/house-L1-L2A')
    # the noscript sits inside the component root
    nos = body[body.index('<noscript>'):]; body = body[:body.index('<noscript>')].rstrip()
    assert body.endswith('</div>'); body = body[:-len('</div>')] + '  ' + nos + '\n</div>'
    snippet = '<!-- POSSIBILITY REVEAL · L2B v2 component (generated by build_reveal_component.py; do not hand-edit) -->\n' + body + '\n<!-- /POSSIBILITY REVEAL -->'

    return {'assets/possibility-reveal/reveal.css': css, 'assets/possibility-reveal/reveal.js': js,
            'assets/possibility-reveal/reveal-data.js': data, 'assets/possibility-reveal/stage-snippet.part': snippet}

ROOTDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORD = os.path.join(ROOTDIR, 'assets/possibility-reveal/component-record.json')
RESERVED = ['heroFrame','heroPhoto','heroCardsDock','heroCopy','heroWordmark','brandMark','atlasFigures','dCarousel',
            'pn-main','top','discover','research','libInfoBtn','libInfo','continuePanel','pnsOpen']
def sha(t): return hashlib.sha256(t.encode('utf-8') if isinstance(t, str) else t).hexdigest()
def die(m): print('REFUSED: ' + m); sys.exit(1)
def mount(index, snip):
    a = index.find('<!-- POSSIBILITY REVEAL · L2B v2 component'); b = index.find('<!-- /POSSIBILITY REVEAL -->')
    if a < 0 or b < 0: die('index.html has no POSSIBILITY REVEAL mount markers')
    return index[:a] + snip + index[b + len('<!-- /POSSIBILITY REVEAL -->'):]
def guard():
    bad = []
    rec = json.load(open(RECORD))
    files = {p: open(os.path.join(ROOTDIR, p), encoding='utf-8').read() for p in rec['outputs']}
    for p, t in files.items():
        if sha(t) != rec['outputs'][p]: bad.append(p + ' differs from its record (hand-edited?)')
    css_t, js_t, snip = files['assets/possibility-reveal/reveal.css'], files['assets/possibility-reveal/reveal.js'], files['assets/possibility-reveal/stage-snippet.part']
    data_t = files['assets/possibility-reveal/reveal-data.js']
    index = open(os.path.join(ROOTDIR, 'index.html'), encoding='utf-8').read()
    if snip not in index: bad.append('the snippet is not mounted verbatim in index.html')
    if index.count('<div class="hero-stage p4-stage" id="heroStage" data-hero="possibility-reveal">') != 1: bad.append('#heroStage is not the possibility-reveal slot')
    if len(re.findall(r'<h1\b', index)) != 1: bad.append('index.html must carry exactly one <h1>')
    if re.search(r'<h1\b', snip): bad.append('the component carries an <h1>')
    if '.pr .lens-over-intro' in css_t or '.pr.lens-over-intro' not in css_t: bad.append('the mobile headline fade-back rule is mis-scoped (the class is set on the component root itself)')
    if re.search(r'part of the photograph', snip): bad.append('the component calls the AI illustration a photograph (PN-FDR-2026-10-19-01, standard 3)')
    for i in re.findall(r'\bid="([^"]+)"', snip):
        if not i.startswith('pr-'): bad.append('un-prefixed id in the component: ' + i)
        if i in RESERVED: bad.append('reserved homepage id reused: ' + i)
    plain = re.sub(r'/\*.*?\*/', '', css_t, flags=re.S)
    def walk(t):
        i = 0
        while True:
            j = t.find('{', i)
            if j < 0: return
            head = t[i:j].strip()
            if head.startswith('@media') or head.startswith('@supports') or head.startswith('@keyframes'):
                d = 1; k = j + 1
                while d:
                    d += t[k] == '{'; d -= t[k] == '}'; k += 1
                if not head.startswith('@keyframes'): walk(t[j+1:k-1])
                elif not head.split()[1].startswith('pr-'): bad.append('unprefixed keyframes ' + head)
                i = k; continue
            for sel in head.split(','):
                if not sel.strip().startswith('.pr'): bad.append('unscoped CSS selector: ' + sel.strip()[:60])
            i = t.find('}', j) + 1
    walk(plain)
    if re.search(r'document\.(getElementById|querySelectorAll?)\((?!"\[data-pr-root\]")', js_t): bad.append('the script looks up elements outside its root')
    if 'commerceEnabled: false' not in data_t: bad.append('commerce is not hard-disabled')
    if re.search(r'status:\s*"active"', data_t): bad.append('an offer is active')
    return bad

if __name__ == '__main__':
    SRC = sys.argv[sys.argv.index('--source') + 1] if '--source' in sys.argv else None
    CHECK = '--check' in sys.argv
    if CHECK:
        bad = guard()
        if SRC:
            fresh = transform()
            for p, t in fresh.items():
                if sha(t) != json.load(open(RECORD))['outputs'].get(p): bad.append(p + ' differs from a fresh transform of the prototype')
        if bad: die('CHECK: ' + '; '.join(bad[:8]))
        print('POSSIBILITY REVEAL COMPONENT · CHECK OK — outputs match their record, mounted verbatim, fully scoped, one H1, commerce off'
              + (', identical to a fresh transform' if SRC else ''))
        sys.exit(0)
    if not SRC: die('--source PROTOTYPE_DIR is required to build')
    outs = transform()
    for p, t in outs.items(): open(os.path.join(ROOTDIR, p), 'w', encoding='utf-8').write(t)
    proto = {f: hashlib.sha256(open(os.path.join(SRC, f), 'rb').read()).hexdigest() for f in ('index.html', 'assets/reveal.css', 'assets/reveal.js', 'assets/reveal-data.js')}
    json.dump({'schema': 'plotnua.possibility-reveal.component.v1', 'source': 'PlotNua Possibility Reveal L2B Prototype v2 (2026-10-18), unmodified except one founder-approved wording change (PN-FDR-2026-10-19-01)',
               'source_sha256': proto, 'outputs': {p: sha(t) for p, t in outs.items()}}, open(RECORD, 'w'), indent=1)
    p = os.path.join(ROOTDIR, 'index.html'); idx = open(p, encoding='utf-8').read(); new = mount(idx, outs['assets/possibility-reveal/stage-snippet.part'])
    if new != idx: open(p, 'w', encoding='utf-8').write(new)
    print('POSSIBILITY REVEAL COMPONENT · built and mounted')
