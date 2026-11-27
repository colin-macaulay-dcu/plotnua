"""PLOTNUA · self-hosted fonts (prepared 27 Nov 2026, NOT released; same method as PlotArt's fonts of 27 Nov 2026).

The ONE definition of the change on PlotNua pages: the Google Fonts stylesheet link becomes /assets/fonts/pn-fonts.css,
and the two preconnect hints to fonts.googleapis.com / fonts.gstatic.com are removed, so a page contacts no Google
host for fonts. Every family and weight a page asked Google for must be in pn-fonts.css, or the transform refuses.
"""
import json
import re

LOCAL = '<link rel="stylesheet" href="/assets/fonts/pn-fonts.css?v=1">'
PRECONNECT = re.compile(r'[ \t]*<link rel="preconnect" href="https://fonts\.(?:googleapis|gstatic)\.com"(?: crossorigin)?>\n?')
GOOGLE = re.compile(r'([ \t]*)<link (?:href="(https://fonts\.googleapis\.com/css2\?[^"]+)" rel="stylesheet"|rel="stylesheet" href="(https://fonts\.googleapis\.com/css2\?[^"]+)")>(\n?)')
IMPORT = re.compile(r'@import url\("https://fonts\.googleapis\.com/css2\?[^"]+"\);')
PROVIDED = {'Fraunces': (300, 700), 'Work Sans': (300, 600), 'Instrument Serif': (400, 400), 'Hanken Grotesk': (400, 700)}


def _check(url):
    url = url.replace('&amp;', '&')
    for fam in re.findall(r'family=([^&]+)', url):
        name, _, spec = fam.partition(':')
        name = name.replace('+', ' ')
        if name not in PROVIDED:
            raise ValueError('font family not self-hosted: ' + name)
        lo, hi = PROVIDED[name]
        for w in re.findall(r'(?:^|[;,@])(?:[01],)?(?:\d+\.\.\d+,)?(\d{3})(?:\.\.(\d{3}))?', spec.split('@', 1)[-1] if '@' in spec else ''):
            for x in w:
                if x and not (lo <= int(x) <= hi) and 'ital' not in spec:
                    raise ValueError('weight %s of %s not self-hosted' % (x, name))


def transform(text):
    """HTML page: Google Fonts link -> self-hosted stylesheet (once), preconnects removed. Idempotent."""
    urls = [a or b for _, a, b, _ in GOOGLE.findall(text)]
    for u in urls:
        _check(u)
    # Where a generated head block (identity layer or global header, both builder-owned) carries a Google Fonts link,
    # that one becomes the local stylesheet, exactly as the updated builders now write it; otherwise the first one does.
    ms = list(GOOGLE.finditer(text))
    keep = 0
    for k, m in enumerate(ms):
        before = text[:m.start()]
        for begin, end in (("<!-- PLOTNUA IDENTITY v1 · HEAD · BEGIN", "<!-- PLOTNUA IDENTITY v1 · HEAD · END"), ("<!-- PLOTNUA HEADER v2 · HEAD · BEGIN", "<!-- PLOTNUA HEADER v2 · HEAD · END")):
            if before.rfind(begin) > before.rfind(end):
                keep = k
    n = [-1]
    def one(m):
        n[0] += 1
        return m.group(1) + LOCAL + m.group(4) if n[0] == keep and LOCAL not in text else ''
    text = GOOGLE.sub(one, text)
    text = PRECONNECT.sub('', text)
    if re.search(r'fonts\.(googleapis|gstatic)\.com', text):
        raise ValueError('a Google Fonts reference is left')
    return text


def css_transform(text):
    return IMPORT.sub('@import url("/assets/fonts/pn-fonts.css?v=1");', text)


def json_transform(s):
    """The same change for raw HTML stored JSON-escaped in a pinned snapshot: each string literal that mentions Google
    Fonts is decoded, transformed and encoded back in place (formatting elsewhere unchanged); refuses unless the result
    parses to exactly the transformed document."""
    if 'fonts.googleapis.com' not in s and 'fonts.gstatic.com' not in s:
        return s
    def lit(m):
        raw = m.group(0)
        if 'fonts.googleapis.com' not in raw and 'fonts.gstatic.com' not in raw:
            return raw
        val = transform(json.loads(raw))
        return json.dumps(val, ensure_ascii='\\u' in raw)
    out = re.sub(r'"(?:[^"\\]|\\.)*"', lit, s)
    def walk(o):
        if isinstance(o, dict): return {k: walk(v) for k, v in o.items()}
        if isinstance(o, list): return [walk(v) for v in o]
        if isinstance(o, str) and ('fonts.googleapis.com' in o or 'fonts.gstatic.com' in o): return transform(o)
        return o
    if json.loads(out) != walk(json.loads(s)):
        raise ValueError('in-place edit is not exactly the declared change')
    return out
