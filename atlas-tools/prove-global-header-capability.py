#!/usr/bin/env python3
"""PLOTNUA GLOBAL HEADER v2 · capability proof for prove-global-header.py.

Copies the site into a scratch folder, plants one fault at a time and requires the
guard to refuse every one of them (and to pass the unmodified copy first).
Usage: python3 atlas-tools/prove-global-header-capability.py
"""
import re, shutil, subprocess, sys, tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
WA = "https://wa.me/353834036695"


def sub1(old, new):
    def f(t):
        if old not in t: raise SystemExit("CAPABILITY · setup string not found: %r" % old[:80])
        return t.replace(old, new, 1)
    return f


def rx1(pat, new):
    def f(t):
        t2, n = re.subn(pat, new, t, count=1, flags=re.S)
        if not n: raise SystemExit("CAPABILITY · setup pattern not found: %r" % pat[:80])
        return t2
    return f


FAULTS = [
    ("header removed from a Discovery", "discovery-hidden-cars.html",
     rx1(r"<!-- PLOTNUA HEADER v2 · BAR · BEGIN.*?BAR · END -->\n?", "")),
    ("header row removed from the homepage", "index.html",
     rx1(r"<!-- PLOTNUA HEADER v2 · ROW · BEGIN.*?ROW · END -->\n?", "")),
    ("header copied onto My Plot (your-plot.html)", "your-plot.html", rx1(r"<body([^>]*)>", r"<body\1><!-- PLOTNUA HEADER v2 · BAR · BEGIN -->x<!-- PLOTNUA HEADER v2 · BAR · END -->")),
    ("header copied onto a property check", None, None),   # filled below
    ("label hand-edited", "about.html", sub1("<span>Discovery Library</span>", "<span>Discoveries</span>")),
    ("active state on the wrong page", "contact.html", sub1('href="plotart/">', 'href="plotart/" aria-current="page">')),
    ("active state lost on the Library", "discoveries.html", sub1(' aria-current="page"', "")),
    ("About back in the primary navigation", "privacy.html",
     sub1('<nav class="pn-hdr-dest" aria-label="Main">', '<nav class="pn-hdr-dest" aria-label="Main"><a href="about.html">About</a>')),
    ("WhatsApp number changed", "terms.html", sub1('class="pn-hdr-wa" href="%s"' % WA, 'class="pn-hdr-wa" href="https://wa.me/353800000000"')),
    ("WhatsApp opens in the same tab", "search.html", sub1('target="_blank" rel="noopener noreferrer" aria-label="Chat', 'target="_self" rel="noopener noreferrer" aria-label="Chat')),
    ("WhatsApp prefilled message", "triq-cube.html", sub1('class="pn-hdr-wa" href="%s"' % WA, 'class="pn-hdr-wa" href="%s?text=Hi"' % WA)),
    ("homepage footer WhatsApp removed", "index.html", sub1('class="pn-whatsapp" href="%s"' % WA, 'class="pn-whatsapp" href="contact.html"')),
    ("header moved after the search rail", "discovery-garden-retreat.html",
     lambda t: _move_bar_after_rail(t)),
    ("v1 identity header left behind", "cookie-policy.html", rx1(r"(<body[^>]*>)", r'\1<header class="pn-id-header"></header>')),
    ("homepage hand-built header back", "index.html", rx1(r"(<body[^>]*>)", r'\1<header class="p4-header"></header>')),
    ("body class missing", "garden-room-prices-ireland.html", rx1(r'<body class="([^"]*) ?pn-hdr-on([^"]*)">', r'<body class="\1\2">')),
    ("stylesheet linked twice", "thanks.html", rx1(r"(</head>)", r'<link rel="stylesheet" href="assets/identity/pn-header.css">\n\1')),
    ("(i) button duplicated outside the header", "index.html", rx1(r"(<main\b[^>]*>)", r'\1<button id="brandInfoBtn"></button>')),
    ("(i) button removed from the header", "index.html",
     rx1(r'<button type="button" class="brand-info" id="brandInfoBtn".*?</button>', "")),
    ("CSS rule escaping the scope", "assets/identity/pn-header.css", lambda t: t + "\n.pn-hdr{ color:red }\n"),
    ("CSS stops hiding the old tile", "assets/identity/pn-header.css", rx1(r"\.brand-mark\{ display:none", ".brand-mark{ display:block")),
    ("CSS sets a homepage token", "assets/identity/pn-header.css", lambda t: t + "\nbody.pn-hdr-on{ --p4-ink:#000 }\n"),
    ("identity builder carries its own header", "atlas-tools/build-identity-stage1.py",
     lambda t: t + '\nX = "<div class=\\"pn-hdr\\">"\n'),
    ("global builder stops using the renderer", "atlas-tools/build-global-header.py", sub1("import pn_header  # noqa: E402", "pn_header = None")),
    ("sitemap page without the header", "sitemap.xml",
     sub1("</urlset>", "<url><loc>https://plotnua.ie/unlisted.html</loc></url></urlset>")),
    # My Plot (founder approval 28 Oct 2026): the link and the read-only script (G6, G10)
    ("My Plot link restarts the journey again", "atlas-tools/pn_header.py", sub1('PLOT = ("your-plot.html?myplot=1", "My Plot")', 'PLOT = ("your-plot.html", "My Plot")')),
    ("My Plot script writes storage", "assets/identity/pn-header.js", sub1("if (n > 0) {", "try { window.localStorage.setItem(KEY, '{}'); } catch (e) {}\n      if (n > 0) {")),
    ("My Plot script makes a network request", "assets/identity/pn-header.js", sub1("if (n > 0) {", "if (window.fetch) fetch('/count?n=' + n);\n      if (n > 0) {")),
    ("My Plot script counts Discovery journeys", "assets/identity/pn-header.js", sub1("return n;\n  }", "n += (Array.isArray(d.journeys) ? d.journeys.length : 0);\n    return n;\n  }")),
    ("My Plot script reads another key", "assets/identity/pn-header.js", sub1("var KEY = 'plotnua.myplot.v1'", "var KEY = 'plotnua.myplot.v2'")),
    ("My Plot script rewrites the link", "assets/identity/pn-header.js", sub1("a.classList.add('is-saved');", "a.classList.add('is-saved'); a.setAttribute('href', 'your-plot.html');")),
    ("My Plot script emptied", "assets/identity/pn-header.js", lambda t: ""),
    # Direction C (founder approval 28 Oct 2026): the Discovery Library compass
    ("Discovery Library icon swapped", "atlas-tools/pn_header.py", sub1('<circle cx="10" cy="10" r="7.25"/>', '<rect x="3" y="3" width="14" height="14" rx="2"/>')),
]


def _move_bar_after_rail(t):
    m = re.search(r"<!-- PLOTNUA HEADER v2 · BAR · BEGIN.*?BAR · END -->\n?", t, re.S)
    t = t[:m.start()] + t[m.end():]
    end = "<!-- PLOTNUA SEARCH RAIL v1 · END -->"
    return t.replace(end, end + "\n" + m.group(0), 1)


def main():
    checks = sorted(p.name for p in ROOT.glob("disc0*.html"))
    if not checks: raise SystemExit("CAPABILITY · no property check page found")
    FAULTS[3] = ("header copied onto a property check", checks[0],
                 rx1(r"<body([^>]*)>", r"<body\1><!-- PLOTNUA HEADER v2 · ROW · BEGIN -->x<!-- PLOTNUA HEADER v2 · ROW · END -->"))
    with tempfile.TemporaryDirectory() as d:
        base = Path(d) / "base"
        base.mkdir()
        for p in ROOT.glob("*.html"): shutil.copy2(p, base / p.name)
        shutil.copy2(ROOT / "sitemap.xml", base / "sitemap.xml")
        for sec in ("gridnua",):   # own-navigation sections listed in the sitemap (29 Oct 2026)
            if (ROOT / sec).is_dir(): shutil.copytree(ROOT / sec, base / sec)
        shutil.copytree(ROOT / "atlas-tools", base / "atlas-tools", ignore=shutil.ignore_patterns("__pycache__"))
        (base / "assets/identity").mkdir(parents=True)
        shutil.copy2(ROOT / "assets/identity/pn-header.css", base / "assets/identity/pn-header.css")
        shutil.copy2(ROOT / "assets/identity/pn-header.js", base / "assets/identity/pn-header.js")

        def run(dirp):
            r = subprocess.run([sys.executable, str(dirp / "atlas-tools/prove-global-header.py"), "--dir", str(dirp)],
                               capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr

        rc, out = run(base)
        if rc != 0: print(out); raise SystemExit("CAPABILITY · the unmodified copy does not pass")
        missed = 0
        for i, (name, rel, fn) in enumerate(FAULTS, 1):
            w = Path(d) / ("m%02d" % i)
            shutil.copytree(base, w)
            f = w / rel
            f.write_text(fn(f.read_text(encoding="utf-8")), encoding="utf-8")
            rc, out = run(w)
            ok = rc != 0 and "REFUSED" in out
            missed += not ok
            print("%s  %-44s %s" % ("caught" if ok else "MISSED", name, (out.strip().splitlines() or [""])[0][:90] if ok else ""))
            shutil.rmtree(w)
        if missed:
            print("CAPABILITY · FAILED — %d of %d planted faults not caught" % (missed, len(FAULTS))); return 2
        print("CAPABILITY · OK — %d planted faults, 0 not caught" % len(FAULTS))
        return 0


if __name__ == "__main__":
    sys.exit(main())
