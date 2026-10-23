#!/usr/bin/env python3
"""
BOUNDED BUILDER · PlotNua shared identity layer, Phase 5 Stage 1 + Stage 2a + Stage 2b

    python3 atlas-tools/build-identity-stage1.py            apply (idempotent)
    python3 atlas-tools/build-identity-stage1.py --check    verify, write nothing

WHAT IT DOES. Brings eight supporting pages into the approved Phase 4 visual
identity (founder approval, 20 Oct 2026, Stage 1 pilot) WITHOUT editing their
content. Per page it makes exactly four insertions, each fenced by
"PLOTNUA IDENTITY v1" markers:

  H  one block before </head>: the two Phase 4 web fonts (the homepage's own
     Google Fonts URL) and assets/identity/pn-identity.css
  B  the attribute class="pn-id pn-id--<surface>" on the bare <body> tag
  S  a "Skip to main content" link straight after <body>, only where the page
     has none (404.html already has one)
  N  the shared header (wordmark + Main navigation, the homepage's header A)
     straight after the search rail, as on the homepage (thanks.html has no
     rail: after the PlotNua mark)
  D  (Discovery family only, Stage 2a) a second stylesheet link in H to
     assets/identity/pn-identity-discovery.css, and the body class
     pn-id--disc. On these pages H sits straight after the theme-color meta,
     not before </head>, because other builders (SEO Phase 1) recognise their
     own head edits by what immediately precedes </head>. Founder approval, 20 Oct 2026: Discovery Library, Hidden
     Bins and Living in the Garden, after SEO-C2 Release 2 (bc40412).
  T  the browser theme colour: the page's one <meta name="theme-color"> goes
     from the legacy #1F3B2E to the homepage's own value (founder decision 3,
     20 Oct 2026). Only its content attribute changes; every other meta tag is
     guarded byte-identical (I9).

WHAT IT NEVER TOUCHES. index.html (the source of truth), sitemap.xml,
<title>, meta, canonical, Open Graph, JSON-LD, <main>, every <img>, the
search rail region, search.css/search.js (hash-frozen), the footer markup,
forms, page copy, URLs, Atlas data, supplier files.

GUARDS (any failure stops the build and nothing is written):
  I1  REVERSIBLE: removing the four insertions gives back the page's input
      bytes exactly. So protected content cannot have changed.
  I2  every insertion is exactly the generated template for that page
  I3  protected fingerprints (title, meta, canonical, JSON-LD, main, images,
      search rail, footer, forms) identical before and after
  I4  TOKEN PARITY: every --p4-* token in pn-identity.css equals the value in
      index.html body.pn-p4 (read independently from the homepage)
  I5  SCOPE: every rule in pn-identity.css is under body.pn-id, so the file is
      inert on any page that does not carry the class
  I6  index.html carries no identity marker and does not load the file
  I7  exactly the eight Stage 1 pages carry the markers; no other page does
  I8  the header's two Main navigations (one rendered per width), one skip link
      with a real target, one banner landmark at most, correct aria-current
  I9  theme colour: exactly one theme-color meta, equal to index.html's; all
      other meta tags unchanged
  I10 the Discovery layer (its stylesheet link and the pn-id--disc class)
      appears on the approved Discovery pages only, exactly once each
  I11 protected sources are never written: maker-explorer.css/.js,
      provider-explorer.js, search.css/.js and index.html are byte-identical
      before and after every run (the capability proof also compares them
      with the base commit)
  I12 SCOPE: every rule in pn-identity-discovery.css is under
      body.pn-id.pn-id--disc, so it is inert on every other page
  I13 the Premium Discovery layer (pn-premium-discovery.css and the pn-pd
      class) appears on the approved Premium Discovery pages only, exactly
      once each, and only on pages that also carry the Discovery layer
      (Stage 2c; direction approved 23 Oct 2026)
  I14 SCOPE: every rule in pn-premium-discovery.css is under
      body.pn-id.pn-pd, and it never redefines a --p4 token
"""
import hashlib, os, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pn_header  # the one canonical header (global header v2, 23 Oct 2026)

# PN_ROOT lets the capability proof run this exact builder against a scratch copy.
ROOT = Path(os.environ.get("PN_ROOT") or Path(__file__).resolve().parent.parent)
CSS = ROOT / "assets" / "identity" / "pn-identity.css"
CSS_DISC = ROOT / "assets" / "identity" / "pn-identity-discovery.css"
CSS_PREM = ROOT / "assets" / "identity" / "pn-premium-discovery.css"
PROTECTED = ["maker-explorer.css", "maker-explorer.js", "provider-explorer.js", "search.css", "search.js", "index.html"]
CHECK = "--check" in sys.argv

# page -> reading surface. Founder decision 3 (20 Oct 2026): dark-first, not
# dark-only. The three legal pages read on a Warm Ivory sheet; the rest are dark.
PAGES = {
    "about.html": "dark", "contact.html": "dark", "privacy.html": "paper",
    "terms.html": "paper", "cookie-policy.html": "paper",
    "artist-register.html": "dark", "404.html": "dark", "thanks.html": "dark",
    # Stage 2a, Discovery family pilot (founder approval 20 Oct 2026)
    "discoveries.html": "dark", "discovery-hidden-bins.html": "dark",
    "discovery-living-in-the-garden.html": "dark",
    # Stage 2b, the six standard Discoveries (founder approval 22 Oct 2026,
    # Architectural Anthracite Batch 2 + Stage 2b)
    "discovery-the-borrowed-garden.html": "dark", "discovery-driveway-income.html": "dark",
    "discovery-hidden-cars.html": "dark", "discovery-home-exchange.html": "dark",
    "discovery-neighbourhood-parcel-house.html": "dark", "discovery-your-home-on-screen.html": "dark",
    # Stage 2c, Premium Discovery (direction approved 23 Oct 2026; release pending)
    "discovery-a-home-for-art.html": "dark",
}
DISC = {"discoveries.html", "discovery-hidden-bins.html", "discovery-living-in-the-garden.html",
        "discovery-the-borrowed-garden.html", "discovery-driveway-income.html", "discovery-hidden-cars.html",
        "discovery-home-exchange.html", "discovery-neighbourhood-parcel-house.html", "discovery-your-home-on-screen.html",
        "discovery-a-home-for-art.html"}
# Stage 2c: pages that also load the Premium Discovery component layer (I13, I14).
PREMIUM = {"discovery-a-home-for-art.html"}
# 404.html is served for ANY missing address, including nested ones, so its
# additions use root-absolute paths. The site is served at the domain root.
ROOTABS = {"404.html"}
FONTS = ("https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1"
         "&family=Hanken+Grotesk:wght@400;500;600;700&display=swap")
GEN = "generated by atlas-tools/build-identity-stage1.py — do not hand-edit"

def die(m):
    print("BUILD-IDENTITY-STAGE1 · REFUSED: " + m); sys.exit(2)
def sha(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()

def p(page, href): return ("/" + href) if page in ROOTABS else href

def head_block(page):
    return _head_block(page).replace("<!-- PLOTNUA IDENTITY v1 · HEAD · END -->", pn_header.stylesheet_link(page) + "<!-- PLOTNUA IDENTITY v1 · HEAD · END -->")

def _head_block(page):
    return ("<!-- PLOTNUA IDENTITY v1 · HEAD · BEGIN · %s -->\n"
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link rel="stylesheet" href="%s">\n'
            '<link rel="stylesheet" href="%s">\n'
            "%s%s"
            "<!-- PLOTNUA IDENTITY v1 · HEAD · END -->\n") % (GEN, FONTS, p(page, "assets/identity/pn-identity.css"),
                ('<link rel="stylesheet" href="%s">\n' % p(page, "assets/identity/pn-identity-discovery.css")) if page in DISC else "",
                ('<link rel="stylesheet" href="%s">\n' % p(page, "assets/identity/pn-premium-discovery.css")) if page in PREMIUM else "")

def body_attr(page): return ' class="pn-id pn-id--%s%s%s pn-hdr-on"' % (PAGES[page], " pn-id--disc" if page in DISC else "", " pn-pd" if page in PREMIUM else "")

SKIP = ("\n<!-- PLOTNUA IDENTITY v1 · SKIP · BEGIN -->"
        '<a class="pn-id-skip" href="#pn-id-content">Skip to main content</a>'
        "<!-- PLOTNUA IDENTITY v1 · SKIP · END -->")

# The header itself is pn_header.py's (global header v2, founder approval 23 Oct 2026):
# this builder only places it. Pages without their own skip link get one (SKIP, at
# the top of <body>) and its target, which follows the header (TARGET).
TARGET = ("\n<!-- PLOTNUA IDENTITY v1 · TARGET · BEGIN -->"
          '<span id="pn-id-content" tabindex="-1"></span>'
          "<!-- PLOTNUA IDENTITY v1 · TARGET · END -->")

HAS_SKIP = set()
RX = [re.compile(r"<!-- PLOTNUA IDENTITY v1 · HEAD · BEGIN.*?<!-- PLOTNUA IDENTITY v1 · HEAD · END -->\n", re.S),
      re.compile(r"\n<!-- PLOTNUA IDENTITY v1 · SKIP · BEGIN -->.*?<!-- PLOTNUA IDENTITY v1 · SKIP · END -->", re.S),
      re.compile(r"\n<!-- PLOTNUA IDENTITY v1 · HEADER · BEGIN.*?<!-- PLOTNUA IDENTITY v1 · HEADER · END -->", re.S),   # v1 header, stripped on rebuild
      re.compile(r"\n<!-- PLOTNUA IDENTITY v1 · TARGET · BEGIN -->.*?<!-- PLOTNUA IDENTITY v1 · TARGET · END -->", re.S)]
BODY_RX = re.compile(r'<body class="pn-id pn-id--(?:dark|paper)(?: pn-id--disc)?(?: pn-pd)?(?: pn-hdr-on)?">')
THEME_LEGACY = '<meta name="theme-color" content="#1F3B2E">'
def theme_tag(value): return '<meta name="theme-color" content="%s">' % value
HOME_THEME = None   # read from index.html in main(); I9
# Earlier homepage theme colours that this layer wrote and may find on a page
# it is re-applying to: Earth Charcoal (20 Oct 2026), before the
# Architectural Anthracite palette (22 Oct 2026). strip() returns any of them
# to the legacy value so the build is a clean re-application.
PREVIOUS_HOME_THEMES = ("#2A2622",)

def strip(t):
    for rx in RX: t = rx.sub("", t)
    t = pn_header.strip(t)
    if BODY_RX.search(t) and HOME_THEME:
        for v in (HOME_THEME,) + PREVIOUS_HOME_THEMES:
            if theme_tag(v) in t:
                t = t.replace(theme_tag(v), THEME_LEGACY, 1)
                break
    return BODY_RX.sub("<body>", t, count=1)

RAIL_END = "<!-- PLOTNUA SEARCH RAIL v1 · END -->"

def build(page, src):
    if src.count("</head>") != 1: die("%s: expected one </head>" % page)
    if src.count("<body>") != 1: die("%s: expected one bare <body> tag" % page)
    body = src[src.index("<body>"):]
    if 'class="pn-skip"' in src: HAS_SKIP.add(page)
    if src.count(THEME_LEGACY) != 1 or src.count('name="theme-color"') != 1:
        die("I9 %s: expected exactly one legacy theme-color meta" % page)
    out = src.replace(THEME_LEGACY, theme_tag(HOME_THEME), 1)
    if page in DISC:
        # Discovery pages: the head block follows the theme-color meta. Other
        # builders verify their own head edits by adjacency to </head> (SEO
        # Phase 1 checks "JSON-LD + </head>"), so nothing is placed there.
        anchor = theme_tag(HOME_THEME) + "\n"
        if out.count(anchor) != 1: die("%s: theme-color anchor for the head block not found exactly once" % page)
        out = out.replace(anchor, anchor + head_block(page), 1)
    else:
        out = out.replace("</head>", head_block(page) + "</head>", 1)
    out = out.replace("<body>", "<body" + body_attr(page) + ">" + ("" if page in HAS_SKIP else SKIP), 1)
    try:
        out = pn_header.insert(page, out)
    except ValueError as e:
        die(str(e))
    if page not in HAS_SKIP:
        end = pn_header.MARK["ROW"][1]
        if out.count(end) != 1: die("%s: the header row end marker is not present exactly once" % page)
        out = out.replace(end, end + TARGET, 1)
    return out

def fingerprints(t):
    body = t[t.find("<body"):]
    f = {"title": re.findall(r"<title>.*?</title>", t, re.S),
         "meta (all except theme-color)": [m for m in re.findall(r"<meta\b[^>]*>", t) if 'name="theme-color"' not in m],
         "canonical": re.findall(r'<link[^>]+rel="canonical"[^>]*>', t),
         "jsonld": re.findall(r'<script[^>]+application/ld\+json[^>]*>.*?</script>', t, re.S),
         "main": re.findall(r"<main\b.*?</main>", t, re.S),
         "img": re.findall(r"<img\b[^>]*>", body),
         "rail": re.findall(r"<!-- PLOTNUA SEARCH RAIL v1 · BEGIN.*?SEARCH RAIL v1 · END -->", t, re.S),
         "footer": re.findall(r"<footer\b.*?</footer>", t, re.S),
         "form": re.findall(r"<form\b.*?</form>", t, re.S),
         "h1": re.findall(r"<h1\b.*?</h1>", t, re.S),
         "picture": re.findall(r"<picture\b.*?</picture>", t, re.S),
         "svg": re.findall(r"<svg\b.*?</svg>", body, re.S),
         "hero": re.findall(r'<header class="d-hero[^"]*">.*?</header>', t, re.S)}
    return {k: sha("\x00".join(v)) + "/%d" % len(v) for k, v in f.items()}

def top_level(selector_list):
    """Split a selector list at top-level commas only (not inside :is()/:where())."""
    out, depth, cur = [], 0, ""
    for ch in selector_list:
        if ch == "(": depth += 1
        elif ch == ")": depth -= 1
        if ch == "," and depth == 0: out.append(cur); cur = ""
        else: cur += ch
    out.append(cur)
    return [x.strip() for x in out]

def tokens(css_text, scope):
    m = re.search(re.escape(scope) + r"\s*\{([^}]*)\}", css_text)
    if not m: die("no %s block found" % scope)
    return dict(re.findall(r"(--p4-[a-z0-9-]+)\s*:\s*([^;]+);", m.group(1)))

def main():
    global HOME_THEME
    if not CSS.exists(): die("assets/identity/pn-identity.css is missing")
    m = re.findall(r'<meta name="theme-color" content="(#[0-9A-Fa-f]{6})">', (ROOT / "index.html").read_text(encoding="utf-8"))
    if len(m) != 1: die("I9 index.html must carry exactly one theme-color meta")
    HOME_THEME = m[0]
    if HOME_THEME.upper() == "#1F3B2E": die("I9 the homepage theme colour is the legacy value; nothing to align to")
    css = CSS.read_text(encoding="utf-8")
    # I4 token parity, read independently from the homepage's own CSS
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    home_css = re.sub(r"/\*.*?\*/", "", "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", home, re.S)), flags=re.S)
    want = tokens(home_css, "body.pn-p4"); have = tokens(re.sub(r"/\*.*?\*/", "", css, flags=re.S), "body.pn-id")
    if not want: die("I4 homepage tokens not found")
    for k, v in want.items():
        if have.get(k, "").strip() != v.strip(): die("I4 token %s is %r here but %r on the homepage" % (k, have.get(k), v))
    extra = set(have) - set(want)
    if extra: die("I4 tokens not on the homepage: %s" % sorted(extra))
    # I5 scope
    flat = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    flat = re.sub(r"@media[^{]*\{", "", flat)
    for sel in re.findall(r"([^{}]+)\{[^{}]*\}", flat):
        for s in top_level(sel):
            s = s.strip()
            if s and not s.startswith("body.pn-id"): die("I5 selector outside body.pn-id: %r" % s)
    # I12 Discovery layer scope
    if not CSS_DISC.exists(): die("assets/identity/pn-identity-discovery.css is missing")
    dflat = re.sub(r"@media[^{]*\{", "", re.sub(r"/\*.*?\*/", "", CSS_DISC.read_text(encoding="utf-8"), flags=re.S))
    for sel in re.findall(r"([^{}]+)\{[^{}]*\}", dflat):
        for s in top_level(sel):
            s = s.strip()
            if s and not s.startswith("body.pn-id.pn-id--disc"): die("I12 Discovery selector outside body.pn-id.pn-id--disc: %r" % s)
    if re.search(r"--p4-[a-z0-9-]+\s*:", dflat): die("I12 the Discovery layer must not redefine --p4 tokens (they belong to the homepage, I4)")
    # I14 Premium Discovery layer scope
    if not PREMIUM <= DISC: die("I13 a Premium Discovery page must also be an approved Discovery page")
    if not CSS_PREM.exists(): die("assets/identity/pn-premium-discovery.css is missing")
    pflat = re.sub(r"@media[^{]*\{", "", re.sub(r"/\*.*?\*/", "", CSS_PREM.read_text(encoding="utf-8"), flags=re.S))
    for sel in re.findall(r"([^{}]+)\{[^{}]*\}", pflat):
        for s in top_level(sel):
            s = s.strip()
            if s and not s.startswith("body.pn-id.pn-pd"): die("I14 Premium selector outside body.pn-id.pn-pd: %r" % s)
    if re.search(r"--p4-[a-z0-9-]+\s*:", pflat): die("I14 the Premium layer must not redefine --p4 tokens (they belong to the homepage, I4)")
    # I11 protected sources: fingerprint now, re-check after the run
    prot_before = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in PROTECTED if (ROOT / f).exists()}
    # I6 homepage untouched by this layer
    if "PLOTNUA IDENTITY" in home or "pn-identity.css" in home: die("I6 index.html must not carry the identity layer")
    # I7 coverage
    for f in sorted(ROOT.glob("*.html")):
        if f.name not in PAGES and "PLOTNUA IDENTITY v1" in f.read_text(encoding="utf-8", errors="replace"):
            die("I7 %s carries the identity markers but is not a Stage 1 page" % f.name)
        txt = f.read_text(encoding="utf-8", errors="replace")
        if f.name not in DISC and ("pn-identity-discovery.css" in txt or "pn-id--disc" in txt):
            die("I10 %s carries the Discovery layer but is not an approved Discovery page" % f.name)
        if f.name not in PREMIUM and ("pn-premium-discovery.css" in txt or re.search(r'class="[^"]*\bpn-pd\b', txt)):
            die("I13 %s carries the Premium Discovery layer but is not an approved Premium page" % f.name)

    changed = []
    for page in PAGES:
        path = ROOT / page
        cur = path.read_text(encoding="utf-8")
        src = strip(cur)                                   # the page without this layer
        if "PLOTNUA IDENTITY" in src: die("%s: unrecognised identity remnant after strip" % page)
        HAS_SKIP.discard(page)
        out = build(page, src)
        # I1 reversible
        if strip(out) != src: die("I1 %s: removing the insertions does not restore the input" % page)
        # I3 protected fingerprints
        a, b = fingerprints(src), fingerprints(pn_header.strip(out))   # the header is pn_header.py's, proven by prove-global-header.py
        for k in a:
            if a[k] != b[k]: die("I3 %s: protected %s changed" % (page, k))
        # I10 Discovery layer exactly once on each approved Discovery page, never elsewhere
        nd = out.count("pn-identity-discovery.css"); nc = out.count("pn-id--disc")
        if page in DISC and (nd != 1 or nc != 1): die("I10 %s: Discovery layer expected once (link %d, class %d)" % (page, nd, nc))
        if page not in DISC and (nd or nc): die("I10 %s: Discovery layer on a non-Discovery page" % page)
        # I13 Premium layer exactly once on each approved Premium page, never elsewhere
        npl = out.count("pn-premium-discovery.css"); npc = len(re.findall(r'<body class="[^"]*\bpn-pd\b', out))
        if page in PREMIUM and (npl != 1 or npc != 1): die("I13 %s: Premium layer expected once (link %d, class %d)" % (page, npl, npc))
        if page not in PREMIUM and (npl or npc): die("I13 %s: Premium layer on a non-Premium page" % page)
        # I9 theme colour equals the homepage's; it is the only meta that moved
        if out.count(theme_tag(HOME_THEME)) != 1 or out.count('name="theme-color"') != 1:
            die("I9 %s: theme colour is not exactly the homepage's %s" % (page, HOME_THEME))
        # I8 navigation / landmarks
        # two Main navigations in the source (bar and phone row); exactly one is rendered at any width (prove-global-header.py)
        if out.count('aria-label="Main"') != 2: die("I8 %s: expected the header's two Main navigations" % page)
        skips = out.count('class="pn-id-skip"') + out.count('class="pn-skip"')
        if skips != 1: die("I8 %s: expected one skip link, found %d" % (page, skips))
        tgt = re.search(r'class="pn-(?:id-)?skip" href="#([^"]+)"', out).group(1)
        if ('id="%s"' % tgt) not in out: die("I8 %s: skip target #%s missing" % (page, tgt))
        bodypart = out[out.find("<body"):]
        top_headers = len(re.findall(r"<header[\s>]", bodypart))
        if top_headers > 1: die("I8 %s: more than one <header> (banner) element" % page)
        # About and Contact left the primary navigation (founder decision 23 Oct 2026); the
        # Discovery Library is marked current on its own page, in both navigations
        marks = re.findall(r'<a [^>]*aria-current="page"[^>]*>', out)
        if page == "discoveries.html" and len([m for m in marks if 'href="discoveries.html"' in m]) != 2: die("I8 %s: aria-current missing" % page)
        if cur != out:
            changed.append(page)
            if not CHECK: path.write_text(out, encoding="utf-8")
    # I11 protected sources unchanged by this run
    for f, h in prot_before.items():
        if hashlib.sha256((ROOT / f).read_bytes()).hexdigest() != h: die("I11 protected source %s changed during the run" % f)
    if CHECK and changed:
        die("CHECK: %d page(s) not in the Stage 1 identity state: %s -- nothing written" % (len(changed), ", ".join(changed)))
    print("IDENTITY STAGE 1+2a+2b+2c · %s — %d pages (%d Discovery, %d Premium), tokens equal the homepage (%d), theme colour %s, scoped, reversible, protected content unchanged%s"
          % ("CHECK OK" if CHECK else "BUILT", len(PAGES), len(DISC), len(PREMIUM), len(want), HOME_THEME,
             "" if CHECK else (" · written: " + (", ".join(changed) or "none"))))

if __name__ == "__main__":
    main()
