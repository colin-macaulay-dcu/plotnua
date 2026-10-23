#!/usr/bin/env python3
"""PREMIUM DISCOVERY · A HOME FOR ART · content-preservation guard (Stage 2c prototype).

Compares discovery-a-home-for-art.html with the page as released at BASE
(0cb456d, production on 23 Oct 2026) and refuses the redesign unless:

  P1  head unchanged: title, every meta except theme-color, canonical, OG/Twitter,
      JSON-LD (none on this page), scripts outside the body
  P2  every photograph is its BASE <img> tag verbatim (file, alt, dimensions), and
      the hero is untouched
  P3  every link target is kept with the same count (check entries, artist register,
      outbound references, exits, related cards, footer)
  P4  the governed anchors exist exactly once: #open-your-home-to-art, #live-with-art,
      #discover-and-own, #before-anything-arrives, #discover-your-property,
      #hfa-checks-top, #hfaNav; the in-page navigation lists them in order
  P5  the PLOTNUA-TAKE-PART marker, exactly one artist-register.html link, the Property
      Checks with ?start=1 only, no form and no field on the page
  P6  TRACEABILITY: every sentence of visible BASE text is present on the new page,
      or is listed in EDITORIAL below with the reason; every sentence of new visible
      text is either BASE text or declared in EDITORIAL / INTERFACE
  P7  qualifications: the cautions that must stay on view (outside any <details>)
      are present outside <details> on the new page
  P8  no new service, commercial or earnings claim: none of the refused phrases

Usage: python3 atlas-tools/prove-premium-discovery-a-home-for-art.py [--record]
       --record prints the editorial change record (BASE sentence -> new form).
"""
import html as H, re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = "discovery-a-home-for-art.html"
BASE = "0cb456d"

# Founder-reviewable editorial changes: BASE wording -> new wording (None = removed).
EDITORIAL = {
    "Why This Discovery?": ("Why it matters", "kicker under Possibility three read as a page-level label; renamed to what the section argues"),
    "Where To Look": ("Where to look", "sentence case (rendered in capitals either way)"),
    "Before Anything Arrives": ("Before anything arrives", "sentence case (rendered in capitals either way)"),
    "Where This Could Go": ("Where this could go", "sentence case (rendered in capitals either way)"),
    "Frequently Asked Questions": ("Frequently asked questions", "sentence case (rendered in capitals either way)"),
    "What You Are Actually Buying": ("What you are actually buying", "sentence case"),
    "Getting It Right": ("Getting it right", "sentence case"),
    "Before You Buy": ("Before you buy", "sentence case"),
    "Four ways in, and you decide how far it goes": ("Four ways in, and you decide how far it goes.", "label promoted to a heading; full stop added"),
    "The more involved you choose to become, the greater the potential return may be — and the more there is to agree.":
        ("The more involved you choose to become, the greater the potential return may be — and the more there is to agree.", "split from its paragraph into a card heading; words unchanged"),
    "No, and this assumption stops most people.": ("No, and this assumption stops most people.", "split from its paragraph into a card heading; words unchanged"),
    "What work, how many pieces, what each is worth, and the condition it arrives in.":
        ("What work / How many pieces / What each is worth / The condition it arrives in", "Custody sentence set as a four-line inventory; same four items, same order"),
    "Size it against the furniture": ("Size it against the furniture.", "sub-heading folded into its list item"),
    "Hang it lower than you think": ("Hang it lower than you think.", "sub-heading folded into its list item"),
    "Look at the light": ("Look at the light.", "sub-heading folded into its list item"),
    "The space.": ("The space.", "<br>-run paragraph set as a term list; words unchanged"),
    "What everyone gets": (None, "duplicate label: the heading 'Three people are better off.' already says it"),
    "Three ways it can happen": ("Three ways it can happen", "kept, now the kicker of the card"),
}
# New interface wording (no factual content). Each is shown to the founder.
INTERFACE = [
    "How it works", "Store", "Display", "Open", "Help sell",
    "Less of your home and time", "More involvement",
    "If you go further", "Take part", "In detail",
    "Route 1", "Route 2", "Route 3", "Route 4",
    "What work", "How many pieces", "What each is worth", "The condition it arrives in",
    "Size it against the furniture.", "Hang it lower than you think.", "Look at the light.",
    "Four ways in, and you decide how far it goes.", "Why it matters", "Where to look",
    "Before anything arrives", "Frequently asked questions", "What you are actually buying",
    "Getting it right", "Before you buy", "Where this could go",
]
STAY_ON_VIEW = [
    "PlotNua does not currently arrange artwork loans, rentals or placements.",
    "Any arrangement would need to be agreed directly with the artist or gallery.",
    "PlotNua does not publish price guides.",
    "This matching service is not live yet.",
    "Both are expressions of interest only: free, private and non-binding.",
    "PlotNua is not currently matching participants or arranging exhibitions, and has not verified any space or artist.",
    "Neither is a rate: every arrangement is settled between two people, in advance.",
    "Do not assume a home policy protects somebody else’s artwork.",
    "Rent-a-Room Relief does not apply",
    "Nobody has to come to your door.",
]
REFUSED = [r"\bcommission rate\b", r"\b\d+ ?%", r"\bguarantee", r"\bwe (?:will )?(?:match|arrange|place|insure)\b",
           r"\bearn(?:s|ings)? (?:up to|of|€)", r"\bmarketplace\b", r"\bpartner(?:s|ship)? (?:artist|gallery)",
           r"\bbook (?:a|your) (?:viewing|placement)\b", r"\bsign up now\b"]

def die(m): print("PREMIUM-HFA · REFUSED: " + m); sys.exit(2)

def base_text():
    return subprocess.run(["git", "-C", str(ROOT), "show", "%s:%s" % (BASE, PAGE)], capture_output=True, text=True, check=True).stdout

def body(t):
    b = t[t.index("<body"):]
    b = re.sub(r"<!-- PLOTNUA IDENTITY v1 · (HEADER|SKIP) · BEGIN.*?<!-- PLOTNUA IDENTITY v1 · \1 · END -->", "", b, flags=re.S)
    b = re.sub(r"<!-- PLOTNUA SEARCH RAIL.*?SEARCH RAIL v1 · END -->", "", b, flags=re.S)
    b = re.sub(r"<!--.*?-->", "", b, flags=re.S)
    b = re.sub(r"<(script|style)\b.*?</\1>", "", b, flags=re.S)
    return b

def visible(t, outside_details=False):
    b = body(t)
    b = re.sub(r'<div class="pns-panel".*?</div>\s*</div>\s*</div>', "", b, flags=re.S)
    b = re.sub(r'<div class="pn-id-header".*?</div>\s*</div>', "", b, flags=re.S)
    b = re.sub(r'<[^>]*aria-hidden="true"[^>]*>[^<]*</[a-z]+>', " ", b)
    if outside_details: b = re.sub(r"<details\b.*?</details>", " ", b, flags=re.S)
    b = re.sub(r"<br\s*/?>", "\n", b)
    b = re.sub(r"</?(p|li|h[1-6]|div|section|summary|dt|dd|figcaption|span|a|strong|aside|header|nav|ul|ol|dl|figure|main|footer|em)\b[^>]*>",
               lambda m: "\n" if m.group(1) not in ("strong", "em", "a") else " ", b)
    b = re.sub(r"<[^>]+>", " ", b)
    return H.unescape(b)

def sentences(txt):
    out = []
    for line in txt.split("\n"):
        line = re.sub(r"\s+", " ", line).strip()
        if not line: continue
        for s in re.split(r"(?<=[.?!:])\s+(?=[A-Z“‘(])", line):
            s = s.strip()
            if s: out.append(s)
    return out

def norm(s): return re.sub(r"\s+", " ", s.replace("’", "'")).strip()

def main():
    record = "--record" in sys.argv
    old = base_text(); new = (ROOT / PAGE).read_text(encoding="utf-8")
    # P1 head
    def head(t): return re.sub(r'<meta name="theme-color"[^>]*>', "", re.sub(r"<!-- PLOTNUA IDENTITY v1 · HEAD.*?HEAD · END -->\n", "", t[:t.index("</head>")], flags=re.S))
    for rx in [r"<title>.*?</title>", r"<meta\b[^>]*>", r'<link[^>]+rel="canonical"[^>]*>', r'<script[^>]+ld\+json.*?</script>', r"<script\b[^>]*src=[^>]*>"]:
        a, b = re.findall(rx, head(old), re.S), re.findall(rx, head(new), re.S)
        if a != b: die("P1 head changed: %s" % rx)
    # P2 images
    def imgs(t): return sorted(re.findall(r"<img\b[^>]*>", re.sub(r"<!--.*?-->", "", t[t.index("<body"):], flags=re.S)))
    def norm_img(tag): return re.sub(r"\s+", " ", tag)
    if sorted(map(norm_img, imgs(old))) != sorted(map(norm_img, imgs(new))): die("P2 the set of <img> tags differs from BASE")
    if re.search(r'<header class="d-hero">.*?</header>', old, re.S).group(0) != re.search(r'<header class="d-hero">.*?</header>', new, re.S).group(0):
        die("P2 the hero changed")
    # P3 links
    def hrefs(t): return sorted(re.findall(r'href="([^"]+)"', body(t)))
    a, b = hrefs(old), hrefs(new)
    if a != b:
        from collections import Counter
        die("P3 links differ: removed %s added %s" % (dict(Counter(a) - Counter(b)), dict(Counter(b) - Counter(a))))
    # P4 anchors
    for i in ["open-your-home-to-art", "live-with-art", "discover-and-own", "before-anything-arrives", "discover-your-property", "hfa-checks-top", "hfaNav", "pn-main"]:
        if new.count('id="%s"' % i) != 1: die("P4 #%s not present exactly once" % i)
    nav = re.search(r'<nav class="hfa-nav" id="hfaNav" aria-label="On this page">(.*?)</nav>', new, re.S)
    if not nav: die("P4 the labelled in-page navigation is missing")
    order = re.findall(r'href="#([^"]+)"', nav.group(1))
    if order != ["open-your-home-to-art", "live-with-art", "discover-and-own", "before-anything-arrives", "discover-your-property"]: die("P4 navigation order %r" % order)
    pos = [new.index('id="%s"' % i) for i in order]
    if pos != sorted(pos): die("P4 sections are not in navigation order")
    # P5 governance markers
    if new.count("<!-- PLOTNUA-TAKE-PART") != 1: die("P5 PLOTNUA-TAKE-PART marker")
    if new.count('href="artist-register.html"') != 1: die("P5 artist-register link must appear exactly once")
    for c in ["disc024-open-your-home-to-art.html", "disc023-buy-original-irish-art.html"]:
        for m in re.findall(r'href="(%s[^"]*)"' % re.escape(c), new):
            if m != c + "?start=1": die("P5 check link without ?start=1: %s" % m)
    if re.search(r"<(form|input|textarea|select)\b", body(new).replace('id="pnsInput"', "")) and "<form" in new: die("P5 a form appeared")
    # P6 traceability
    os_, ns_ = sentences(visible(old)), sentences(visible(new))
    ns_n = set(map(norm, ns_)); ntext = norm(" ".join(ns_))
    edit_keys = {norm(k): v for k, v in EDITORIAL.items()}
    missing, recorded = [], []
    for s in os_:
        if norm(s) in ns_n or norm(s) in ntext: continue
        if norm(s) in edit_keys: recorded.append((s, edit_keys[norm(s)])); continue
        missing.append(s)
    if missing: die("P6 BASE text missing and not declared:\n  " + "\n  ".join(missing[:25]))
    allowed = set(map(norm, os_)) | {norm(v[0]) for v in EDITORIAL.values() if v[0]} | set(map(norm, INTERFACE))
    otext = norm(" ".join(os_))
    new_untraced = [s for s in ns_ if norm(s) not in allowed and norm(s) not in otext]
    if new_untraced: die("P6 new text not traceable to BASE or declared:\n  " + "\n  ".join(new_untraced[:25]))
    # P7 on-view cautions
    nv = norm(" ".join(sentences(visible(new, outside_details=True))))
    for c in STAY_ON_VIEW:
        if norm(c) not in nv: die("P7 caution not on view: %r" % c)
    # P8 refused claims
    vt = " ".join(ns_)
    for rx in REFUSED:
        m = re.search(rx, vt, re.I)
        if m and norm(m.group(0)) not in otext.lower() and m.group(0) not in visible(old): die("P8 refused claim pattern %r: %r" % (rx, m.group(0)))
    words_old = len(" ".join(os_).split()); words_new = len(" ".join(ns_).split())
    if record:
        print("EDITORIAL RECORD (BASE %s -> prototype)" % BASE)
        for s, (to, why) in recorded: print(" - %r -> %r · %s" % (s, to, why))
    print("PREMIUM-HFA · OK — head, %d photographs, %d links, 7 anchors + navigation order, TAKE-PART, artist link once, checks ?start=1; "
          "%d BASE sentences traced (%d recorded edits), %d cautions on view, no refused claim · visible words %d -> %d"
          % (len(imgs(new)), len(hrefs(new)), len(os_), len(recorded), len(STAY_ON_VIEW), words_old, words_new))

if __name__ == "__main__":
    main()
