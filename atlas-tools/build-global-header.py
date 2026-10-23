#!/usr/bin/env python3
"""PLOTNUA GLOBAL HEADER v2 · placement on the pages that are not on the identity layer.

Founder approval: 23 Oct 2026 (Phase B). The pages on the shared identity layer get
the header from build-identity-stage1.py; every other approved page gets it from
here. Both use atlas-tools/pn_header.py, so the markup is one and the same.

Pages: pn_header.GLOBAL_PAGES (the homepage, Garden Retreat, House as a Power
Station, Above and Beyond, Garden Room Prices, the search page, Triq Cube).
Excluded by decision: Your Plot and the property checks / journeys.

Insertions (fenced, reversible):
  HEAD  fonts + assets/identity/pn-header.css, after the theme-color meta (or the
        viewport meta where a page has none); never next to </head> (SEO Phase 1
        verifies its own edits by adjacency there)
  BAR   before the search rail · ROW after it (pn_header.insert)
  body  the class token pn-hdr-on
Nothing else on a page is touched: the theme colour, the PlotNua tile (now hidden by
pn-header.css), the rail, the Back control and all content stay exactly as they are.

GUARDS
  H1  REVERSIBLE: removing the insertions returns the page's input bytes exactly
  H2  protected fingerprints (title, meta, canonical, JSON-LD, main, rail, footer,
      forms, hero, picture, every image outside the header) identical
  H3  search.css / search.js / maker and provider scripts / referral offers
      byte-identical before and after the run
  H4  the homepage carries no hand-built header any more (p4-header) and its (i)
      button exists exactly once, inside the header

Usage: python3 atlas-tools/build-global-header.py [--check]
"""
import hashlib, os, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pn_header  # noqa: E402

ROOT = Path(os.environ.get("PN_ROOT") or Path(__file__).resolve().parent.parent)
CHECK = "--check" in sys.argv
PROTECTED = ["search.css", "search.js", "maker-explorer.css", "maker-explorer.js", "provider-explorer.js",
             "commercial/referral-offers.json"]
BODY_TAG = re.compile(r"<body(?: class=\"([^\"]*)\")?>")


def die(m):
    print("BUILD-GLOBAL-HEADER · REFUSED: " + m); sys.exit(2)


def sha(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()


def strip(t):
    t = pn_header.strip(t)
    m = BODY_TAG.search(t)
    if m and m.group(1) is not None and "pn-hdr-on" in m.group(1).split():
        cls = " ".join(c for c in m.group(1).split() if c != "pn-hdr-on")
        t = t[:m.start()] + ("<body class=\"%s\">" % cls if cls else "<body>") + t[m.end():]
    return t


def build(page, src):
    if "PLOTNUA HEADER v2" in src: die("%s: unrecognised header remnant after strip" % page)
    if src.count("</head>") != 1: die("%s: expected one </head>" % page)
    m = re.search(r'<meta name="theme-color"[^>]*>\n', src) or re.search(r'<meta name="viewport"[^>]*>\n', src)
    if not m: die("%s: no theme-color or viewport meta to anchor the head block" % page)
    out = src[:m.end()] + pn_header.head_block(page) + src[m.end():]
    b = BODY_TAG.search(out)
    if not b or len(BODY_TAG.findall(out)) != 1: die("%s: expected exactly one plain <body> tag" % page)
    cls = (b.group(1) + " pn-hdr-on") if b.group(1) else "pn-hdr-on"
    out = out[:b.start()] + '<body class="%s">' % cls + out[b.end():]
    try:
        out = pn_header.insert(page, out)
    except ValueError as e:
        die(str(e))
    return out


def fingerprints(t):
    t = pn_header.strip(t)
    body = t[t.find("<body"):]
    f = {"title": re.findall(r"<title>.*?</title>", t, re.S),
         "meta": re.findall(r"<meta\b[^>]*>", t),
         "canonical": re.findall(r'<link[^>]+rel="canonical"[^>]*>', t),
         "jsonld": re.findall(r'<script[^>]+application/ld\+json[^>]*>.*?</script>', t, re.S),
         "main": re.findall(r"<main\b.*?</main>", t, re.S),
         "img": re.findall(r"<img\b[^>]*>", body),
         "rail": re.findall(r"<!-- PLOTNUA SEARCH RAIL v1 · BEGIN.*?SEARCH RAIL v1 · END -->", t, re.S),
         "footer": re.findall(r"<footer\b.*?</footer>", t, re.S),
         "form": re.findall(r"<form\b.*?</form>", t, re.S),
         "hero": re.findall(r'<header class="[^"]*hero[^"]*">.*?</header>', t, re.S),
         "picture": re.findall(r"<picture\b.*?</picture>", t, re.S),
         "scripts": re.findall(r"<script\b.*?</script>", body, re.S)}
    return {k: sha("\x00".join(v)) + "/%d" % len(v) for k, v in f.items()}


def main():
    prot = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in PROTECTED if (ROOT / f).exists()}
    changed = []
    for page in pn_header.GLOBAL_PAGES:
        path = ROOT / page
        cur = path.read_text(encoding="utf-8")
        src = strip(cur)
        out = build(page, src)
        if strip(out) != src: die("H1 %s: removing the insertions does not restore the input" % page)
        a, b = fingerprints(src), fingerprints(out)
        for k in a:
            if a[k] != b[k]: die("H2 %s: protected %s changed" % (page, k))
        if page == "index.html":
            if 'class="p4-header"' in out: die("H4 index.html still carries its hand-built header")
            if out.count('id="brandInfoBtn"') != 1: die("H4 index.html: the (i) button must exist exactly once")
            bar = re.search(r"<!-- PLOTNUA HEADER v2 · BAR · BEGIN.*?BAR · END -->", out, re.S).group(0)
            if 'id="brandInfoBtn"' not in bar: die("H4 index.html: the (i) button is not in the header")
        if cur != out:
            changed.append(page)
            if not CHECK: path.write_text(out, encoding="utf-8")
    for f, h in prot.items():
        if hashlib.sha256((ROOT / f).read_bytes()).hexdigest() != h: die("H3 protected source %s changed during the run" % f)
    if CHECK and changed:
        die("CHECK: %d page(s) not in the global-header state: %s -- nothing written" % (len(changed), ", ".join(changed)))
    print("GLOBAL HEADER v2 · %s — %d pages, reversible, protected content unchanged%s"
          % ("CHECK OK" if CHECK else "BUILT", len(pn_header.GLOBAL_PAGES), "" if CHECK else " · written: " + (", ".join(changed) or "none")))


if __name__ == "__main__":
    main()
