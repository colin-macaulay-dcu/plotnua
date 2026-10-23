#!/usr/bin/env python3
"""PREMIUM GUIDE PAGE · GARDEN ROOM PRICES IN IRELAND · content-preservation guard.

Batch 1 · page 1 (founder approval 23 Oct 2026: "Wording: presentation-only
initially. Preserve existing SEO headings, pricing, planning and supplier claims.").
The redesign may change presentation only. It is compared with the page as released
at BASE (d9db752), read from a PINNED SNAPSHOT
(atlas-tools/premium-discovery/garden-room-prices-ireland-base.json, fingerprint
BASE_SNAPSHOT_SHA256), so it runs in CI's shallow checkout.

The FIGURES are not this guard's business: they live in the eleven PN-PRICES regions,
written and proved by atlas-tools/build-garden-room-prices.py (rules R1-R7, G-PARENT,
freshness), which this guard runs in --check mode (G5).

  G1  HEAD: title, every meta except theme-color, canonical, the head's external
      scripts (consent, analytics) and the structured-data region unchanged
  G2  IMAGES: the BASE images, plus only the declared WhatsApp icon (a brand mark)
  G3  LINKS: every BASE link target kept with the same count; additions only as
      declared (the in-page navigation and the approved WhatsApp action)
  G4  ANCHORS: every BASE id exactly once (other pages link to them); added ids
      declared; the in-page navigation lists existing sections in page order
  G5  FIGURES: every PN-PRICES region exactly once; the price builder's --check passes
      (as of the page's build date; freshness is the daily freshness workflow's job)
  G6  WORDING: every BASE sentence is on the page; every sentence on the page is BASE
      text or declared below (presentation-only release: navigation labels and the
      approved WhatsApp label)
  G7  ON VIEW: nothing is folded away (no <details>); the cautions in STAY_ON_VIEW are
      on the page
  G8  NO NEW CLAIM: no commercial, ranking, endorsement or guarantee wording that
      BASE did not have, unless declared
  G9  LAYER: the page is a Premium page on the identity layer (registry, body classes,
      theme #27282A, the shared Premium script once), and the legacy stylesheet and
      fonts are gone

Usage: python3 atlas-tools/prove-premium-garden-room-prices.py [--dir D] [--snapshot]
Mutation proof: atlas-tools/prove-premium-garden-room-prices-capability.py
"""
import hashlib, html as H, json, re, subprocess, sys, pathlib
from collections import Counter

TOOLS = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(sys.argv[sys.argv.index("--dir") + 1]).resolve() if "--dir" in sys.argv else TOOLS.parent
PAGE = "garden-room-prices-ireland.html"
BASE = "d9db752c72f1b6b0dda4240e17f957e89074cad6"
SNAP = TOOLS / "premium-discovery" / "garden-room-prices-ireland-base.json"
BASE_SNAPSHOT_SHA256 = "31d2e27e6ddf2a551230b2c01ec1a2fb4dc4f1292910e7c6202b164d5cf75607"
REGIONS = ["JSONLD", "ASOF", "UPDATED", "LEAD", "SPECIALISED", "TABLE", "HELD", "NOAVG", "COMPARE", "FAQ", "METHOD"]

# Declared additions (presentation only). Founder-reviewable.
ADDED_TEXT = {
    "AI-generated illustration": "the required visible label of the hero illustration (PN-FDR-2026-10-19-01)",
    "Chat on WhatsApp": "the approved WhatsApp control, as a secondary action in the closing panel (founder decision 4, 23 Oct 2026)",
    "Why It Is Hard": "in-page navigation label: the section's own kicker",
    "Published Prices": "in-page navigation label: the section's own kicker",
    "Outside The Price": "in-page navigation label: the section's own kicker",
    "Before You Commit": "in-page navigation label: the section's own kicker",
    "Questions": "in-page navigation label: the section's own kicker",
}
ADDED_LINKS = Counter({"#price-ranges": 1, "#why-it-is-hard": 1, "#outside-the-price": 1, "#quote-checklist": 1,
                       "#questions": 1, "https://wa.me/353834036695": 1})
ADDED_IDS = {"short-answer", "why-it-is-hard", "garden-homes"}
ADDED_IMGS = Counter({"assets/brand/plotnua-icon-transparent.svg": 1,
                      "assets/garden-room-prices/garden-room-prices-hero-2026-10-23-1672.jpg": 1})   # hero illustration (founder, 23 Oct 2026)
NAV = ["#price-ranges", "#why-it-is-hard", "#outside-the-price", "#quote-checklist", "#questions"]
STAY_ON_VIEW = [
    "not a census of the Irish garden room market",
    "PlotNua has no commercial arrangement with any of them",
    "Suppliers are not named or ranked here",
    "If two suppliers give different answers to the first four questions",
    "this guide does not put a figure on one",
]
CLAIM_WORDS = r"\b(best|cheapest|recommend\w*|guarantee\w*|partner\w*|sponsor\w*|discount\w*|offer\w*|commission\w*|affiliate\w*|rank\w*|top-rated|trusted|verified|approved supplier|deal\w*)\b"

fails = []
def bad(m): fails.append(m)


def strip_generated(t):
    t = re.sub(r"<!-- PLOTNUA HEADER v2 · (HEAD|BAR|ROW) · BEGIN.*?<!-- PLOTNUA HEADER v2 · \1 · END -->", "", t, flags=re.S)
    t = re.sub(r"<!-- PLOTNUA SEARCH RAIL v1 · BEGIN.*?<!-- PLOTNUA SEARCH RAIL v1 · END -->", "", t, flags=re.S)
    t = re.sub(r"<!-- PLOTNUA IDENTITY v1 · (HEAD|SKIP|TARGET) · BEGIN.*?<!-- PLOTNUA IDENTITY v1 · \1 · END -->", "", t, flags=re.S)
    return t


def without_regions(t):
    return re.sub(r"<!-- PN-PRICES:(\w+) -->.*?<!-- /PN-PRICES:\1 -->", " ", t, flags=re.S)


def body(t):
    return t[t.index("<body"):]


def sentences(t):
    b = without_regions(body(strip_generated(t)))
    b = re.sub(r"<(script|style)\b.*?</\1>|<!--.*?-->", " ", b, flags=re.S)
    b = re.sub(r"</?(p|li|h[1-6]|div|section|header|footer|main|nav|ul|ol|a|b|span|strong|caption|th|td|tr|table|br)\b[^>]*>", "\n", b)
    b = H.unescape(re.sub(r"<[^>]+>", " ", b))
    out = []
    for block in b.split("\n"):
        block = re.sub(r"\s+", " ", block).strip()
        if not block:
            continue
        out += [s.strip() for s in re.split(r"(?<=[.?!])\s+(?=[A-Z0-9“\"‘'(])", block) if s.strip()]
    return out


def links(t):
    b = body(strip_generated(t))
    return Counter(re.findall(r'<a\b[^>]*\bhref="([^"]+)"', b))


def imgs(t):
    b = body(strip_generated(t))
    return Counter(re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', b))


def ids(t):
    return Counter(re.findall(r'\bid="([^"]+)"', body(strip_generated(t))))


def head(t):
    h = strip_generated(t)[:t.index("<body")]
    metas = sorted(m for m in re.findall(r"<meta\b[^>]*>", h) if 'name="theme-color"' not in m)
    return {"title": re.findall(r"<title>.*?</title>", h, re.S),
            "metas": metas,
            "canonical": re.findall(r'<link[^>]+rel="canonical"[^>]*>', h),
            "scripts": re.findall(r'<script\b[^>]*\bsrc="([^"]+)"', h),
            "jsonld": re.findall(r"<!-- PN-PRICES:JSONLD -->.*?<!-- /PN-PRICES:JSONLD -->", h, re.S)}


def snapshot_from(text):
    return {"base": BASE, "page": PAGE, "head": head(text), "sentences": sentences(text),
            "links": dict(links(text)), "imgs": dict(imgs(text)), "ids": sorted(ids(text))}


def main():
    if "--snapshot" in sys.argv:
        text = subprocess.run(["git", "show", "%s:%s" % (BASE, PAGE)], cwd=TOOLS.parent, capture_output=True,
                              text=True, check=True).stdout
        SNAP.parent.mkdir(exist_ok=True)
        data = json.dumps(snapshot_from(text), indent=1, ensure_ascii=False) + "\n"
        SNAP.write_text(data, encoding="utf-8")
        print("snapshot written, sha256 %s" % hashlib.sha256(data.encode()).hexdigest()); return 0
    raw = (TOOLS / "premium-discovery" / SNAP.name).read_bytes() if "--dir" not in sys.argv else (ROOT / "atlas-tools" / "premium-discovery" / SNAP.name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASE_SNAPSHOT_SHA256:
        bad("G0 the BASE snapshot no longer matches its pinned fingerprint")
    base = json.loads(raw)
    t = (ROOT / PAGE).read_text(encoding="utf-8")
    # G1
    now = head(t)
    for k in ("title", "metas", "canonical", "scripts", "jsonld"):
        if now[k] != base["head"][k]:
            bad("G1 head %s changed" % k)
    # G2
    if imgs(t) != Counter(base["imgs"]) + ADDED_IMGS:
        bad("G2 images differ from BASE + declared: %s" % dict(imgs(t) - Counter(base["imgs"]) - ADDED_IMGS or Counter(base["imgs"]) + ADDED_IMGS - imgs(t)))
    # G3
    want = Counter(base["links"]) + ADDED_LINKS
    have = links(t)
    if have != want:
        bad("G3 links differ: missing %s, extra %s" % (dict(want - have), dict(have - want)))
    # G4
    have_ids = ids(t)
    for i in base["ids"]:
        if have_ids.get(i) != 1: bad("G4 id %s must appear exactly once (has %d)" % (i, have_ids.get(i, 0)))
    extra = {i for i in have_ids if i not in base["ids"]} - ADDED_IDS
    if extra: bad("G4 undeclared ids: %s" % sorted(extra))
    nav = re.search(r'<nav class="hfa-nav" data-pd-nav aria-label="On this page">(.*?)</nav>', t, re.S)
    if not nav or re.findall(r'href="([^"]+)"', nav.group(1)) != NAV:
        bad("G4 the in-page navigation is not exactly the declared list")
    else:
        pos = [t.find('id="%s"' % h[1:]) for h in NAV]
        if -1 in pos or pos != sorted(pos): bad("G4 the in-page navigation is not in page order")
    # G5
    for k in REGIONS:
        if len(re.findall(r"<!-- PN-PRICES:%s -->" % k, t)) != 1 or len(re.findall(r"<!-- /PN-PRICES:%s -->" % k, t)) != 1:
            bad("G5 region %s must appear exactly once" % k)
    # Figures are checked as of the page's own build date: agreement with the evidence is this
    # guard's concern; freshness (90 days) stays with the daily garden-room-prices-freshness
    # workflow, so stale prices never block an unrelated release.
    bsrc = (ROOT / "atlas-tools" / "build-garden-room-prices.py").read_text(encoding="utf-8")
    bdate = re.search(r'^BUILD_DATE = "(\d{4}-\d{2}-\d{2})"', bsrc, re.M).group(1)
    r = subprocess.run([sys.executable, str(ROOT / "atlas-tools" / "build-garden-room-prices.py"), "--check",
                        "--today=" + bdate], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0 or "CHECK OK" not in r.stdout:
        bad("G5 the price builder's check fails: %s" % (r.stdout + r.stderr).strip().splitlines()[-1:])
    # G6
    now_s = sentences(t)
    have_s, base_s = Counter(now_s), Counter(base["sentences"])
    missing = [s for s in base_s if have_s[s] < base_s[s]]
    if missing: bad("G6 BASE wording missing: %s" % [m[:70] for m in missing[:4]])
    new = [s for s in have_s if have_s[s] > base_s.get(s, 0) and s not in ADDED_TEXT]
    if new: bad("G6 undeclared wording: %s" % [n[:70] for n in new[:4]])
    # G7
    if "<details" in t: bad("G7 content is folded away inside <details>")
    vis = H.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)\b.*?</\1>", " ", body(t), flags=re.S)))
    vis = re.sub(r"\s+", " ", vis)
    for s in STAY_ON_VIEW:
        if s not in vis: bad("G7 caution not on the page: %r" % s)
    # G8
    base_claims = Counter(w.lower() for s in base["sentences"] for w in re.findall(CLAIM_WORDS, s, re.I))
    now_claims = Counter(w.lower() for s in now_s for w in re.findall(CLAIM_WORDS, s, re.I))
    if now_claims - base_claims: bad("G8 new claim wording: %s" % dict(now_claims - base_claims))
    # G9
    sys.path.insert(0, str(ROOT / "atlas-tools"))
    import importlib; pp = importlib.import_module("premium_pages")
    if PAGE not in pp.PREMIUM_PAGES: bad("G9 the page is not in the Premium registry")
    m = re.search(r'<body class="([^"]*)">', t)
    if not m or m.group(1).split() != ["pn-id", "pn-id--dark", "pn-pd", "pn-hdr-on"]: bad("G9 body classes are not the Premium identity set")
    if '<meta name="theme-color" content="#27282A">' not in t: bad("G9 theme colour is not #27282A")
    if t.count('<script src="assets/identity/pn-premium.js" defer></script>') != 1: bad("G9 the shared Premium script must load once")
    if "Fraunces" in t or "Work+Sans" in t or "--brand-green" in t: bad("G9 the legacy stylesheet or fonts are still on the page")
    if fails:
        for f in fails: print("FAIL " + f)
        print("PREMIUM-GRP · REFUSED — %d problem(s)" % len(fails)); return 2
    print("PREMIUM-GRP · OK — head, %d images, %d links, %d anchors, 11 price regions (builder check OK), "
          "%d BASE sentences all present with %d declared additions, cautions on view, no new claim, Premium layer"
          % (sum(imgs(t).values()), sum(have.values()), len(base["ids"]), len(base_s), len(ADDED_TEXT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
