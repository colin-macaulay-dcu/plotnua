#!/usr/bin/env python3
"""PREMIUM DISCOVERY · A HOME FOR ART · content-preservation guard (Stage 2c).

Founder approval of the prototype direction: 23 Oct 2026 ("approves the overall
prototype as the foundation for the Premium Discovery design system"), with the
final refinement round recorded in EDITORIAL below.

The redesign may change presentation and the declared wording, nothing else.
It is compared with the page as released at BASE (0cb456d), read from a PINNED
SNAPSHOT (atlas-tools/premium-discovery/a-home-for-art-base.json, fingerprint
in BASE_SNAPSHOT_SHA256 below), so the guard runs in CI's shallow checkout. When
the BASE commit is available locally the snapshot is also re-derived from git
and must match exactly.

  P1  head unchanged: title, every meta except theme-color, canonical, JSON-LD
      (none on this page), external scripts
  P2  every photograph is its BASE <img> tag verbatim (file, alt, dimensions);
      the hero is untouched
  P3  every link target kept, with the same count (check entries, artist register,
      outbound references, exits, related cards, SEO aside, footer)
  P4  the governed anchors exist exactly once, and the labelled in-page
      navigation lists them in page order
  P5  the PLOTNUA-TAKE-PART marker; exactly one artist-register.html link; the
      Property Checks only ever with ?start=1; no form on the page
  P6  TRACEABILITY: every BASE sentence is on the page or declared in EDITORIAL
      (with its reason); every sentence on the page is BASE text or declared
  P7  the cautions in STAY_ON_VIEW are visible outside any <details>
  P8  no new service, commercial, earnings or guarantee claim (REFUSED phrases)
  P9  TAX: every visible paragraph that mentions the Artists' Exemption or
      EUR 50,000 also states Revenue's determination requirement (verified
      against Revenue guidance, 23 Oct 2026: Tax and Duty Manual Part 07-01-10,
      reviewed April 2025; revenue.ie Artists' Exemption pages)

Usage:
  python3 atlas-tools/prove-premium-discovery-a-home-for-art.py            check
  python3 atlas-tools/prove-premium-discovery-a-home-for-art.py --record   + print the editorial record
  python3 atlas-tools/prove-premium-discovery-a-home-for-art.py --dir D    check a copy (capability proof)
  python3 atlas-tools/prove-premium-discovery-a-home-for-art.py --snapshot write the BASE snapshot (needs git history)
Mutation proof: atlas-tools/prove-premium-discovery-capability.py
"""
import hashlib, html as H, json, re, subprocess, sys, pathlib
from collections import Counter

TOOLS = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(sys.argv[sys.argv.index("--dir") + 1]).resolve() if "--dir" in sys.argv else TOOLS.parent
PAGE = "discovery-a-home-for-art.html"
BASE = "0cb456d9b0263e54cdcbbf9363fa4b9dc39ce576"
SNAP = TOOLS / "premium-discovery" / "a-home-for-art-base.json"
BASE_SNAPSHOT_SHA256 = "6855b4d804b830fea5c4fad5db15f469e9c642768ae2147de16497cb35888e39"

# BASE wording -> (new wording or None when removed, reason). Founder-reviewable.
EDITORIAL = {
    # round 1 (prototype, 23 Oct 2026)
    "Why This Discovery?": ("Why it matters", "kicker under Possibility three read as a page-level label"),
    "Where To Look": ("Where to look", "sentence case (shown in capitals either way)"),
    "Before Anything Arrives": ("Before anything arrives", "sentence case"),
    "Frequently Asked Questions": ("Frequently asked questions", "sentence case"),
    "Where This Could Go": ("Where this could go", "sentence case"),
    "What You Are Actually Buying": ("What you are actually buying", "sentence case"),
    "Getting It Right": ("Getting it right", "sentence case"),
    "Before You Buy": ("Before you buy", "sentence case"),
    "What everyone gets": (None, "duplicate label: the card heading already says it"),
    "What work, how many pieces, what each is worth, and the condition it arrives in.":
        ("What work / How many pieces / What each is worth / The condition it arrives in", "Custody set as a four-line inventory; same items, same order"),
    "Size it against the furniture": ("Size it against the furniture.", "sub-heading folded into its list item"),
    "Hang it lower than you think": ("Hang it lower than you think.", "sub-heading folded into its list item"),
    "Look at the light": ("Look at the light.", "sub-heading folded into its list item"),
    # round 2 (final refinement, 23 Oct 2026): shorter headings
    "Four ways in, and you decide how far it goes": ("Four ways in. / You decide how far it goes.", "heading shortened; the second half becomes the line beneath it"),
    "Three people are better off.": ("Who benefits?", "heading shortened (founder's wording); the three explanations are unchanged"),
    "Four routes, and none of them require an introduction.": ("Four routes to original art. / None of them require an introduction.", "heading shortened; the second half becomes the line beneath it"),
    # round 2: genuine repetition removed
    "Can I see how it will look before I buy?": (None, "FAQ repeated 'Try it at home' in Live with art, which says the same and adds the insurance question"),
    "Some galleries and artists will let you take a work home on approval for a few days.": (None, "repeats 'Try it at home'"),
    "It is a courtesy rather than a right, so ask.": (None, "repeats 'Try it at home' (the same sentence, with the insurance question, is kept there)"),
    "A handful of Irish services rent artwork monthly.": ("Renting by the month is covered under Live with art, above.", "repeats 'Rental, where available'; the FAQ now points there"),
    # round 2: tax accuracy (Revenue guidance verified 23 Oct 2026)
    "Under the Artists’ Exemption, an Irish artist’s income from original painting and sculpture is exempt from income tax up to €50,000 a year.":
        ("Under Revenue’s Artists’ Exemption, an artist’s income from original and creative work, including paintings and sculpture, can be exempt from income tax up to €50,000 a year, but only where Revenue has made a determination for that artist’s work. / It does not cover USC or PRSI.",
         "unqualified tax claim corrected: the determination requirement and the USC/PRSI limit added; 'Irish' dropped (residence, not nationality, is the test)"),
}
# Wording that is new on the page and carries no factual content (or is declared above).
INTERFACE = [
    "How it works", "Store", "Display", "Open", "Help sell", "Less of your home and time", "More involvement",
    "If you go further", "Take part", "In detail", "A note on tax", "Route 1", "Route 2", "Route 3", "Route 4", "Cost",
    "What work", "How many pieces", "What each is worth", "The condition it arrives in",
    "Size it against the furniture.", "Hang it lower than you think.", "Look at the light.",
    "Why it matters", "Where to look", "Before anything arrives", "Frequently asked questions",
    "What you are actually buying", "Getting it right", "Before you buy", "Where this could go",
    "Four ways in.", "You decide how far it goes.", "More involvement.", "More possibilities.", "Who benefits?",
    "Four routes to original art.", "None of them require an introduction.",
    "Renting by the month is covered under Live with art, above.", "It does not cover USC or PRSI.",
    "Under Revenue’s Artists’ Exemption, an artist’s income from original and creative work, including paintings and sculpture, can be exempt from income tax up to €50,000 a year, but only where Revenue has made a determination for that artist’s work.",
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
    "the artist is the seller.",
    "but only where Revenue has made a determination for that artist’s work.",
    "It does not cover USC or PRSI.",
]
REFUSED = [r"\bcommission rate\b", r"\b\d+ ?%", r"\bguarantee", r"\bwe (?:will )?(?:match|arrange|place|insure)\b",
           r"\bearn(?:s|ings)? (?:up to|of|€)", r"\bmarketplace\b", r"\bpartner(?:s|ship)? (?:artist|gallery)",
           r"\bbook (?:a|your) (?:viewing|placement)\b", r"\bsign up now\b", r"\btax[- ]free\b", r"\bincome (?:of|up to) €"]
ANCHORS = ["open-your-home-to-art", "live-with-art", "discover-and-own", "before-anything-arrives",
           "discover-your-property", "hfa-checks-top", "hfaNav", "pn-main"]
NAV = ["open-your-home-to-art", "live-with-art", "discover-and-own", "before-anything-arrives", "discover-your-property"]

class Refused(Exception): pass
def die(m): raise Refused(m)

# ---------------------------------------------------------------- extraction
def body(t):
    b = t[t.index("<body"):]
    b = re.sub(r"<!-- PLOTNUA IDENTITY v1 · (HEADER|SKIP) · BEGIN.*?<!-- PLOTNUA IDENTITY v1 · \1 · END -->", "", b, flags=re.S)
    b = re.sub(r"<!-- PLOTNUA SEARCH RAIL.*?SEARCH RAIL v1 · END -->", "", b, flags=re.S)
    b = re.sub(r"<!--.*?-->", "", b, flags=re.S)
    return re.sub(r"<(script|style)\b.*?</\1>", "", b, flags=re.S)

def visible(t, outside_details=False):
    b = body(t)
    b = re.sub(r'<[^>]*aria-hidden="true"[^>]*>[^<]*</[a-z]+>', " ", b)
    if outside_details: b = re.sub(r"<details\b.*?</details>", " ", b, flags=re.S)
    b = re.sub(r"<br\s*/?>", "\n", b)
    b = re.sub(r"</?(p|li|h[1-6]|div|section|summary|dt|dd|figcaption|span|a|strong|aside|header|nav|ul|ol|dl|figure|main|footer|em)\b[^>]*>",
               lambda m: "\n" if m.group(1) not in ("strong", "em", "a") else " ", b)
    return H.unescape(re.sub(r"<[^>]+>", " ", b))

def paragraphs(t):
    out = []
    for m in re.finditer(r"<(p|li|dd)\b[^>]*>(.*?)</\1>", body(t), re.S):
        out.append(re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", m.group(2)))).strip())
    return out

def sentences(txt):
    out = []
    for line in txt.split("\n"):
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            out += [s.strip() for s in re.split(r"(?<=[.?!:])\s+(?=[A-Z“‘(])", line) if s.strip()]
    return out

def norm(s): return re.sub(r"\s+", " ", s.replace("’", "'")).strip()

def head(t):
    h = re.sub(r"<!-- PLOTNUA IDENTITY v1 · HEAD.*?HEAD · END -->\n", "", t[:t.index("</head>")], flags=re.S)
    h = re.sub(r'<meta name="theme-color"[^>]*>', "", h)
    return {"title": re.findall(r"<title>.*?</title>", h, re.S), "meta": re.findall(r"<meta\b[^>]*>", h),
            "canonical": re.findall(r'<link[^>]+rel="canonical"[^>]*>', h),
            "jsonld": re.findall(r'<script[^>]+ld\+json.*?</script>', h, re.S), "scripts": re.findall(r"<script\b[^>]*src=[^>]*>", h)}

def imgs(t): return sorted(re.sub(r"\s+", " ", x) for x in re.findall(r"<img\b[^>]*>", re.sub(r"<!--.*?-->", "", t[t.index("<body"):], flags=re.S)))
def hero(t):
    m = re.search(r'<header class="d-hero">.*?</header>', t, re.S)
    if not m: die("P2 the hero is missing")
    return m.group(0)
def hrefs(t): return sorted(re.findall(r'href="([^"]+)"', body(t)))

def snapshot(t):
    return {"base": BASE, "page": PAGE, "head": head(t), "img": imgs(t), "hero": hero(t),
            "href": hrefs(t), "sentences": sentences(visible(t))}

def snap_sha(s): return hashlib.sha256(json.dumps(s, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

def load_base():
    s = json.loads(SNAP.read_text(encoding="utf-8"))
    if snap_sha(s) != BASE_SNAPSHOT_SHA256: die("P0 the BASE snapshot no longer matches its pinned fingerprint")
    p = subprocess.run(["git", "-C", str(TOOLS.parent), "show", "%s:%s" % (BASE, PAGE)], capture_output=True, text=True)
    if p.returncode != 0:   # CI checks out shallow: the pinned snapshot is the reference
        return s, "pinned snapshot"
    if snapshot(p.stdout) != s: die("P0 the BASE snapshot does not equal %s:%s" % (BASE[:7], PAGE))
    return s, "pinned snapshot = git %s" % BASE[:7]

# ---------------------------------------------------------------- the checks
def check(new, base):
    nh = head(new)                                                     # P1
    for k in nh:
        if nh[k] != base["head"][k]: die("P1 head changed: %s" % k)
    if imgs(new) != base["img"]: die("P2 the set of <img> tags differs from BASE")   # P2
    if hero(new) != base["hero"]: die("P2 the hero changed")
    a, b = Counter(base["href"]), Counter(hrefs(new))                  # P3
    if a != b: die("P3 links differ: removed %s added %s" % (dict(a - b), dict(b - a)))
    for i in ANCHORS:                                                  # P4
        if new.count('id="%s"' % i) != 1: die("P4 #%s not present exactly once" % i)
    nav = re.search(r'<nav class="hfa-nav" id="hfaNav" aria-label="On this page">(.*?)</nav>', new, re.S)
    if not nav: die("P4 the labelled in-page navigation is missing")
    order = re.findall(r'href="#([^"]+)"', nav.group(1))
    if order != NAV: die("P4 navigation order %r" % order)
    pos = [new.index('id="%s"' % i) for i in order]
    if pos != sorted(pos): die("P4 sections are not in navigation order")
    if new.count("<!-- PLOTNUA-TAKE-PART") != 1: die("P5 PLOTNUA-TAKE-PART marker not present exactly once")   # P5
    if new.count('href="artist-register.html"') != 1: die("P5 artist-register.html must be linked exactly once")
    for c in ["disc024-open-your-home-to-art.html", "disc023-buy-original-irish-art.html"]:
        for m in re.findall(r'href="(%s[^"]*)"' % re.escape(c), new):
            if m != c + "?start=1": die("P5 check link without ?start=1: %s" % m)
    if re.search(r"<form\b", new): die("P5 a form appeared on the page")
    os_, ns_ = base["sentences"], sentences(visible(new))
    nv = norm(" ".join(sentences(visible(new, outside_details=True))))  # P7
    for c in STAY_ON_VIEW:
        if norm(c) not in nv: die("P7 caution not on view: %r" % c)
    vt, ot = " ".join(ns_), " ".join(os_)                                # P8
    for rx in REFUSED:
        for m in re.finditer(rx, vt, re.I):
            if not re.search(re.escape(m.group(0)), ot, re.I): die("P8 refused claim %r" % m.group(0))
    for p in paragraphs(new):                                           # P9
        if re.search(r"Artists.{0,2} Exemption|50,000", p) and "determination" not in p:
            die("P9 unqualified Artists' Exemption claim: %r" % p[:120])
    # P6 (last, so P7-P9 report their own faults first)
    ns_n, ntext = set(map(norm, ns_)), norm(" ".join(ns_))
    edits = {norm(k): v for k, v in EDITORIAL.items()}
    missing, recorded = [], []
    for s in os_:
        if norm(s) in ns_n or norm(s) in ntext: continue
        if norm(s) in edits: recorded.append((s, edits[norm(s)])); continue
        missing.append(s)
    if missing: die("P6 BASE text missing and not declared:\n  " + "\n  ".join(missing[:25]))
    allowed = set(map(norm, os_)) | set(map(norm, INTERFACE))
    otext = norm(" ".join(os_))
    untraced = [s for s in ns_ if norm(s) not in allowed and norm(s) not in otext]
    if untraced: die("P6 new text not traceable to BASE or declared:\n  " + "\n  ".join(untraced[:25]))
    return recorded, os_, ns_

def main():
    if "--snapshot" in sys.argv:
        old = subprocess.run(["git", "-C", str(TOOLS.parent), "show", "%s:%s" % (BASE, PAGE)], capture_output=True, text=True, check=True).stdout
        s = snapshot(old); SNAP.parent.mkdir(exist_ok=True)
        SNAP.write_text(json.dumps(s, ensure_ascii=False, sort_keys=True, indent=1) + "\n", encoding="utf-8")
        print("snapshot written; BASE_SNAPSHOT_SHA256 = %s" % snap_sha(s)); return 0
    try:
        base, how = load_base()
        new = (ROOT / PAGE).read_text(encoding="utf-8")
        recorded, os_, ns_ = check(new, base)
    except Refused as e:
        print("PREMIUM-HFA · REFUSED: %s" % e); return 2
    if "--record" in sys.argv:
        print("EDITORIAL RECORD (BASE %s -> this page)" % BASE[:7])
        for s, (to, why) in recorded: print(" - %r -> %r · %s" % (s, to, why))
    w0, w1 = len(" ".join(os_).split()), len(" ".join(ns_).split())
    print("PREMIUM-HFA · OK (%s) — head, %d photographs, %d links, %d anchors + navigation order, TAKE-PART, artist link once, "
          "checks ?start=1; %d BASE sentences traced (%d declared edits), %d cautions on view, no refused claim, tax qualified · visible words %d -> %d"
          % (how, len(imgs(new)), len(hrefs(new)), len(ANCHORS), len(os_), len(recorded), len(STAY_ON_VIEW), w0, w1))
    return 0

if __name__ == "__main__":
    sys.exit(main())
