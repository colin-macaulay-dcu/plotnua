#!/usr/bin/env python3
"""Capability proof for prove-premium-garden-room-prices.py: plant one fault at a time
in a scratch copy and require the guard to refuse each (and to pass the clean copy).
Usage: python3 atlas-tools/prove-premium-garden-room-prices-capability.py
"""
import re, shutil, subprocess, sys, tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
PAGE = "garden-room-prices-ireland.html"


def sub(old, new, count=1):
    def f(t):
        if old not in t: raise SystemExit("CAPABILITY · setup string not found: %r" % old[:80])
        return t.replace(old, new, count)
    return f


def rx(pat, new):
    def f(t):
        t2, n = re.subn(pat, new, t, count=1, flags=re.S)
        if not n: raise SystemExit("CAPABILITY · setup pattern not found: %r" % pat[:80])
        return t2
    return f


FAULTS = [
    ("title changed", PAGE, sub("<title>Garden Room Prices in Ireland (2026) | PlotNua</title>", "<title>Garden Room Prices | PlotNua</title>")),
    ("meta description changed", PAGE, rx(r'(<meta name="description" content=")[^"]*', r"\1Garden room prices.")),
    ("canonical changed", PAGE, sub('href="https://plotnua.ie/garden-room-prices-ireland.html">', 'href="https://plotnua.ie/prices.html">')),
    ("consent script removed", PAGE, rx(r'<script id="Cookiebot"[^>]*></script>\n', "")),
    ("a figure typed by hand", PAGE, sub("&euro;9,995 to &euro;43,650", "&euro;9,500 to &euro;43,650")),
    ("a price region removed", PAGE, rx(r"<!-- PN-PRICES:HELD -->.*?<!-- /PN-PRICES:HELD -->", "")),
    ("an image added", PAGE, sub('<main id="pn-main">', '<main id="pn-main"><img src="assets/x.jpg" alt="">')),
    ("the maker-index link removed", PAGE, rx(r'<a href="discovery-living-in-the-garden.html#maker-index">.*?</a>', "")),
    ("an undeclared link added", PAGE, sub('<a class="pd-btn is-ghost" href="discovery-living-in-the-garden.html#explore-makers">',
                                           '<a href="https://example.com/">x</a><a class="pd-btn is-ghost" href="discovery-living-in-the-garden.html#explore-makers">')),
    ("an anchor renamed", PAGE, sub('id="quote-checklist"', 'id="checklist"')),
    ("navigation out of order", PAGE, sub('<li><a href="#price-ranges">Published Prices</a></li>\n        <li><a href="#why-it-is-hard">Why It Is Hard</a></li>',
                                          '<li><a href="#why-it-is-hard">Why It Is Hard</a></li>\n        <li><a href="#price-ranges">Published Prices</a></li>')),
    ("a checklist question removed", PAGE, rx(r"<li>What warranty applies, and to which parts\?</li>\s*", "")),
    ("a heading reworded", PAGE, sub("A garden room quote checklist", "Your quote checklist")),
    ("an undeclared sentence added", PAGE, sub("<p>Ask every supplier the same questions", "<p>Prices are falling fast. Ask every supplier the same questions")),
    ("content folded into <details>", PAGE, rx(r'(<section class="pd-section reveal" id="garden-homes">)', r"\1<details><summary>More</summary></details>")),
    ("the no-commercial-arrangement caution removed", PAGE, sub(" and PlotNua has no commercial arrangement with any of them", "")),
    ("a recommendation claim added", PAGE, sub("Explore makers and products &rarr;</a>", "Explore makers and products &rarr;</a><span>Our recommended makers</span>")),
    ("Premium class removed from the body", PAGE, sub('class="pn-id pn-id--dark pn-pd pn-hdr-on"', 'class="pn-id pn-id--dark pn-hdr-on"')),
    ("theme colour reverted", PAGE, sub('<meta name="theme-color" content="#27282A">', '<meta name="theme-color" content="#1F3B2E">')),
    ("legacy fonts back", PAGE, sub("</head>", '<link href="https://fonts.googleapis.com/css2?family=Fraunces&display=swap" rel="stylesheet">\n</head>')),
    ("shared Premium script missing", PAGE, sub('<script src="assets/identity/pn-premium.js" defer></script>', "")),
    ("page dropped from the Premium registry", "atlas-tools/premium_pages.py", sub('    "garden-room-prices-ireland.html",     # Batch 1 · 1', "    # removed")),
    ("BASE snapshot tampered", "atlas-tools/premium-discovery/garden-room-prices-ireland-base.json", sub('"page": ', '"page":  ')),
    ("WhatsApp action given a prefilled message", PAGE, sub('class="pd-btn is-ghost pd-wa" href="https://wa.me/353834036695"',
                                                          'class="pd-btn is-ghost pd-wa" href="https://wa.me/353834036695?text=Hi"')),
    # the hero-illustration exception (founder approval 23 Oct 2026) stays exactly that narrow
    ("hero illustration label removed", PAGE, sub("<figcaption>AI-generated illustration</figcaption>", "<figcaption></figcaption>")),
    ("a supplier photograph hot-linked into the hero", PAGE, sub('<img class="pr-hero-img" src="assets/garden-room-prices/garden-room-prices-hero-2026-10-23-1672.jpg"',
                                                                 '<img class="pr-hero-img" src="https://lh3.googleusercontent.com/d/1zfB24bun-dr7Smh0ZeFSX_OaNVDh6DMX=w1600"')),
    ("another site image put in the hero", PAGE, sub('class="pr-hero-img" src="assets/garden-room-prices/garden-room-prices-hero-2026-10-23-1672.jpg"',
                                                     'class="pr-hero-img" src="assets/img/8c60a8f27eb9c697.jpg"')),
    ("the temporary homepage illustration put back in the hero", PAGE, sub('class="pr-hero-img" src="assets/garden-room-prices/garden-room-prices-hero-2026-10-23-1672.jpg"',
                                                                           'class="pr-hero-img" src="assets/possibility-reveal/img/house-L1-L2A-2064.jpg"')),
    ("the hero illustration reused outside the hero", PAGE, sub('<main id="pn-main">', '<main id="pn-main"><img src="assets/garden-room-prices/garden-room-prices-hero-2026-10-23-960.jpg" alt="">')),
    ("an undeclared size added to the hero", PAGE, sub('assets/garden-room-prices/garden-room-prices-hero-2026-10-23-1672.jpg 1672w"', 'assets/garden-room-prices/garden-room-prices-hero-2026-10-23-1672.jpg 1672w, assets/garden-room-prices/garden-room-prices-hero-2026-10-23-2400.jpg 2400w"')),
    ("provenance no longer permits a Discovery surface", "image-provenance-records.json",
     rx(r'("asset": "assets/garden-room-prices/garden-room-prices-hero-2026-10-23-1672\.jpg".*?"permitted_surfaces": \[\s*)"discovery"', r'\1"homepage"')),
    ("provenance claims a named product", "image-provenance-records.json",
     rx(r'("asset": "assets/garden-room-prices/garden-room-prices-hero-2026-10-23-1672\.avif".*?"depicts_named_product": )false', r"\1true")),
    ("a pinned hero file altered", "assets/garden-room-prices/garden-room-prices-hero-2026-10-23-1672.avif", None),
]


def main():
    with tempfile.TemporaryDirectory() as d:
        base = Path(d) / "base"; base.mkdir()
        shutil.copy2(ROOT / PAGE, base / PAGE)
        for f in ("garden-room-recommendation-universe-v1.json", "image-provenance-records.json"):
            shutil.copy2(ROOT / f, base / f)
        sys.path.insert(0, str(TOOLS))
        import importlib.util
        spec = importlib.util.spec_from_file_location("grp", TOOLS / "build-garden-room-prices.py")
        src = (TOOLS / "build-garden-room-prices.py").read_text(encoding="utf-8")
        for f in re.findall(r'^    "(assets/[^"]+)": "[0-9a-f]{64}",$', src, re.M):   # the pinned hero files
            (base / f).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT / f, base / f)
        shutil.copytree(ROOT / "atlas-tools", base / "atlas-tools", ignore=shutil.ignore_patterns("__pycache__", "node_modules"))

        def run(w):
            r = subprocess.run([sys.executable, str(w / "atlas-tools" / "prove-premium-garden-room-prices.py"), "--dir", str(w)],
                               capture_output=True, text=True)
            return r.returncode, (r.stdout + r.stderr).strip()

        rc, out = run(base)
        if rc != 0: print(out); raise SystemExit("CAPABILITY · the clean copy does not pass")
        missed = 0
        for i, (name, rel, fn) in enumerate(FAULTS, 1):
            w = Path(d) / ("m%02d" % i); shutil.copytree(base, w)
            f = w / rel
            if fn is None: f.write_bytes(f.read_bytes() + b"\0")          # alter a binary file
            else: f.write_text(fn(f.read_text(encoding="utf-8")), encoding="utf-8")
            rc, out = run(w)
            ok = rc != 0 and "REFUSED" in out
            missed += not ok
            first = next((l for l in out.splitlines() if l.startswith("FAIL")), out.splitlines()[-1] if out else "")
            print("%s  %-46s %s" % ("caught" if ok else "MISSED", name, first[:96] if ok else out[-120:]))
            shutil.rmtree(w)
        if missed:
            print("PREMIUM-GRP CAPABILITY · FAILED — %d of %d planted faults not caught" % (missed, len(FAULTS))); return 2
        print("PREMIUM-GRP CAPABILITY · OK — %d planted faults, 0 not caught" % len(FAULTS)); return 0


if __name__ == "__main__":
    sys.exit(main())
