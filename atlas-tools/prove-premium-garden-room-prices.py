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
  G7  ON VIEW: nothing in the page's own content is folded away (no <details>; the shared
      generated header/search/identity regions are outside this page's content); the cautions in STAY_ON_VIEW are
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
REGIONS = ["JSONLD", "ASOF", "UPDATED", "LEAD", "SPECIALISED", "TABLE", "HELD", "NOAVG", "COMPARE", "FAQ", "METHOD",
           "CHECKED", "VAT", "EXTRAS"]   # the last three: Stage 2 pricing refresh (founder decision, 6 Nov 2026)

# Declared additions. The 26 Oct SEO draft adds only the two scope sentences;
# the original presentation baseline and its fingerprint remain unchanged.
ADDED_TEXT = {
    "PlotNua": "footer heading replacing Company (legal information, founder decision A1-a, 28 Oct 2026)",
    "Legal information": "footer link to the Terms page legal information (legal information, founder decision A1-a, 28 Oct 2026)",
    "This guide covers detached garden rooms and garden offices.": "26 Oct SEO draft: clarify the guide's existing subject",
    "It does not price extensions or attached sunrooms.": "26 Oct SEO draft: distinguish the guide from attached-building queries",
    "AI-generated illustration": "the required visible label of the hero illustration (PN-FDR-2026-10-19-01)",
    "Chat on WhatsApp": "the approved WhatsApp control, as a secondary action in the closing panel (founder decision 4, 23 Oct 2026)",
    "Why It Is Hard": "in-page navigation label: the section's own kicker",
    "Published Prices": "in-page navigation label: the section's own kicker",
    "Outside The Price": "in-page navigation label: the section's own kicker",
    "Before You Commit": "in-page navigation label: the section's own kicker",
    "Questions": "in-page navigation label: the section's own kicker",
}
ADDED_LINKS = Counter({"terms.html#legal-information": 1, "#price-ranges": 1, "#why-it-is-hard": 1, "#outside-the-price": 1, "#quote-checklist": 1,
                       "#questions": 1, "https://wa.me/353834036695": 1,
                       # Stage 2 pricing refresh (founder decision, 6 Nov 2026): the direct link from the
                       # answer to the products (item 6) and the extra-costs note's checklist link (item 5)
                       "discovery-living-in-the-garden.html#explore-makers": 1})
ADDED_LINKS["#quote-checklist"] += 1
# SEO-GR3: the hero's link to the method and the method's place in the in-page navigation; the new
# section's navigation entry; its link to the additional costs.
ADDED_LINKS.update({"#how-these-figures-were-made": 2, "#what-affects-prices": 1, "#outside-the-price": 1})
REMOVED_TEXT = {"Company": "footer heading renamed PlotNua (legal information, founder decision A1-a, 28 Oct 2026)"}

# SEO-GR3 (founder approval 8 Nov 2026: "Garden Room Prices Ireland: search relevance and content
# optimisation", controlled implementation). Wording and structure only: the figures stay in the
# PN-PRICES regions, written and proved by the price builder (G5). Each change is declared here.
GR3 = "SEO-GR3 (8 Nov 2026)"
GR3_HEAD = {   # BASE head element -> its SEO-GR3 replacement (title, Open Graph and Twitter cards)
    "<title>Garden Room Prices in Ireland (2026) | PlotNua</title>":
        "<title>Garden Room Prices &amp; Costs in Ireland (2026) | PlotNua</title>",
    '<meta property="og:title" content="Garden Room Prices in Ireland | PlotNua">':
        '<meta property="og:title" content="Garden Room Prices &amp; Costs in Ireland | PlotNua">',
    '<meta name="twitter:title" content="Garden Room Prices in Ireland | PlotNua">':
        '<meta name="twitter:title" content="Garden Room Prices &amp; Costs in Ireland | PlotNua">',
    '<meta property="og:description" content="What advertised garden room prices in Ireland actually cover, and how to compare two quotes.">':
        '<meta property="og:description" content="Independent research on what garden rooms cost in Ireland: installed rooms and kits, what each price covers, and how to compare quotes.">',
    '<meta name="twitter:description" content="What advertised garden room prices in Ireland actually cover, and how to compare two quotes.">':
        '<meta name="twitter:description" content="Independent research on what garden rooms cost in Ireland: installed rooms and kits, what each price covers, and how to compare quotes.">',
}
GR3_REMOVED = {   # BASE sentences replaced by SEO-GR3 (each replacement is in GR3_ADDED)
    "So treat it as a guide to what is advertised, then use the checklist further down to": "now refers to both ranges",
    "turn any price into one you can actually compare.": "the same sentence, rewrapped",
    "What can sit outside the advertised price": "H2 renamed: Additional garden room costs to consider",
    "A garden room quote checklist": "H2 renamed: How to compare garden room suppliers: a quote checklist",
    "How these figures were made": "H2 renamed: How PlotNua checks garden room price evidence",
}
GR3_ADDED = [
    "So treat these ranges as a guide to what is advertised, then use the checklist further down to turn any price into one you can actually compare.",
    "Additional garden room costs to consider",
    "How to compare garden room suppliers: a quote checklist",
    "How PlotNua checks garden room price evidence",
    # in-page navigation labels: the two sections' own kickers
    "What Affects Price", "The Research",
    # the new section "What affects garden room prices" (no figure, no name, no claim)
    "What affects garden room prices",
    "Two garden rooms of a similar size can be priced very differently.",
    "These are the things that most often explain the difference, and the quote checklist further down turns them into questions for each supplier.",
    "What the price includes",
    "Whether a building is installed and finished on your site, supplied and erected, or sold as a kit is the first thing to establish.",
    "This guide gives a separate range for each kind of price it can publish.",
    "Size and layout",
    "Floor area, height and the rooms inside change what a price buys.",
    "Many prices come without a floor area, and some suppliers measure inside while others measure outside, so ask for the internal floor area.",
    "Construction and finish",
    "Insulation, glazing, cladding and what is finished inside, such as lining, flooring, sockets, lighting and heating, vary between suppliers and between models.",
    "Your garden and access",
    "Sloping or soft ground, tight side access and the distance from the house can change the base, the delivery and the electrical connection.",
    "See the additional costs to consider \u2192",
    # the method section: the snapshot history moves here from the hero, with what it means
    "Snapshot date and later rechecks",
    "The research snapshot is the starting point.",
    "Since then, individual supplier records have been corrected, rechecked or withdrawn on different dates, so not every price was rechecked on the same day.",
    "The full record:",
]
ADDED_TEXT.update({x: GR3 for x in GR3_ADDED})
REMOVED_TEXT.update(GR3_REMOVED)
# SEO GR8 (link to the garden offices guide) and the individual price comparison (commit 1ac9fa8), both on main
# 9 Nov 2026; declared under the founder's approval of 9 Nov 2026 to resolve the gate. Wording as published, except
# two sentences reworded with the same meaning so that no G8 claim word is added (CLAIM_WORDS unchanged).
GR9 = "garden offices link + individual price comparison (founder approval 9 Nov 2026)"
GR9_ADDED = [
    "Exploring a workspace specifically?", "See PlotNua\u2019s garden offices in Ireland guide", ".",
    "Compare actual advertised prices", "Garden room prices \u2014 lowest to highest",
    "Explore individually recorded supplier prices, starting with the lowest price.",
    "These are", "advertised product prices, not like-for-like installed quotations",
    "Use the purchase-basis filter to distinguish kits from installed rooms.",
    "A lower price may exclude VAT, delivery, foundations, fitting or electrics.",
    "Price includes All advertised prices Installed and finished (including base) Installed, foundations excluded Supplied and erected Supply only / kit Installation basis not confirmed",
    "Supplier-advertised product prices, ascending; PlotNua research snapshot 7 October 2026, with subsequent checks.",
    "#", "Supplier and model", "Advertised price", "What the price covers", "Last checked",
    "VAT status is shown for each entry.",
    "An unconfirmed installation basis is not a kit or an installed quote.",
    "Prices may change; follow the supplier link and confirm a current written quotation.",
    "PlotNua does not rate supplier quality or suggest choosing the lowest-priced product simply because it costs less.",
]
ADDED_TEXT.update({x: GR9 for x in GR9_ADDED})
ADDED_LINKS.update({"garden-offices-ireland.html": 1})
ADDED_IDS = {"short-answer", "why-it-is-hard", "garden-homes",
             "what-may-cost-extra",   # Stage 2 item 5 (6 Nov 2026), inside the EXTRAS region
             "what-affects-prices",   # SEO-GR3 (8 Nov 2026): the new section
             # the individual price comparison (founder approval 9 Nov 2026)
             "garden-room-price-ranking", "pr-ranking-heading", "pr-compare-basis", "pr-compare-count", "pr-compare-rows", "pr-compare-data"}
ADDED_IMGS = Counter({"assets/brand/plotnua-icon-transparent.svg": 1,
                      "assets/garden-room-prices/garden-room-prices-hero-2026-10-23-1672.jpg": 1})   # hero illustration (founder, 23 Oct 2026)
NAV = ["#price-ranges", "#what-affects-prices", "#why-it-is-hard", "#outside-the-price", "#quote-checklist",
       "#questions", "#how-these-figures-were-made"]   # SEO-GR3 adds the second and the last
STAY_ON_VIEW = [
    "not a census of the Irish garden room market",
    "PlotNua has no commercial arrangement with any of them",
    "Suppliers are not named or ranked here",
    "If two suppliers give different answers to the first four questions",
    "this guide does not put a figure on one",
]
CLAIM_WORDS = r"\b(best|cheapest|recommend\w*|guarantee\w*|partner\w*|sponsor\w*|discount\w*|offer\w*|commission\w*|affiliate\w*|rank\w*|top-rated|trusted|verified|approved supplier|deal\w*)\b"

fails = []

def seo_gr2_home(h):
    """SEO-GR2 (founder approval 8 Nov 2026): a homepage link "index.html[#x]" is now "/[#x]", the
    homepage's canonical URL. Declared mapping applied to the BASE links; nothing else is relaxed."""
    return "/" + h[len("index.html"):] if h == "index.html" or h.startswith(("index.html#", "index.html?")) else h

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
    # Bounded content revision: only dateModified moves in the frozen head.
    # A different date or any other structured-data change still fails G1.
    # Stage 2 pricing refresh (founder decision, 6 Nov 2026): dateModified is the builder's
    # BUILD_DATE, and the meta description is written by the builder from the published
    # figures (G5 proves it is the one the evidence produces). Only those two strings may
    # move, and the description must keep the approved wording around its two figures.
    t = (ROOT / PAGE).read_text(encoding="utf-8")
    bsrc0 = (ROOT / "atlas-tools" / "build-garden-room-prices.py").read_text(encoding="utf-8")
    bdate0 = re.search(r'^BUILD_DATE = "(\d{4}-\d{2}-\d{2})"', bsrc0, re.M).group(1)
    old_desc = ("How much does a garden room cost in Ireland? Published price ranges from PlotNua's "
                "research, what the advertised price covers, and how to compare quotes.")
    dm = re.search(r'<meta name="description" content="([^"]*)">', t)
    new_desc = dm.group(1) if dm else ""
    # SEO-GR3 (8 Nov 2026): the approved wording names both published ranges and the research totals.
    if not re.fullmatch(r"Independent research on garden room prices in Ireland: \d+ advertised prices from "
                        r"\d+ suppliers\. Installed rooms ran from €[\d,]+ to €[\d,]+; kits from €[\d,]+\.",
                        new_desc):
        bad("G1 the meta description is not the approved figure-bearing wording")
    ld_desc = json.dumps(new_desc, ensure_ascii=True)[1:-1]
    base["head"]["metas"] = sorted(m.replace(old_desc, new_desc) if 'name="description"' in m else m
                                   for m in base["head"]["metas"])
    base["head"]["title"] = [GR3_HEAD.get(x, x) for x in base["head"]["title"]]
    base["head"]["metas"] = sorted(GR3_HEAD.get(m, m) for m in base["head"]["metas"])
    base["head"]["jsonld"] = [x.replace('"dateModified": "2026-10-20"', '"dateModified": "%s"' % bdate0)
                                .replace(old_desc, ld_desc)
                              for x in base["head"]["jsonld"]]
    # G1
    now = head(t)
    for k in ("title", "metas", "canonical", "scripts", "jsonld"):
        if now[k] != base["head"][k]:
            bad("G1 head %s changed" % k)
    # G2
    if imgs(t) != Counter(base["imgs"]) + ADDED_IMGS:
        bad("G2 images differ from BASE + declared: %s" % dict(imgs(t) - Counter(base["imgs"]) - ADDED_IMGS or Counter(base["imgs"]) + ADDED_IMGS - imgs(t)))
    # G3
    want = Counter({seo_gr2_home(k): v for k, v in base["links"].items()}) + ADDED_LINKS
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
    missing = [s for s in missing if s not in REMOVED_TEXT]
    if missing: bad("G6 BASE wording missing: %s" % [m[:70] for m in missing[:4]])
    new = [s for s in have_s if have_s[s] > base_s.get(s, 0) and s not in ADDED_TEXT]
    if new: bad("G6 undeclared wording: %s" % [n[:70] for n in new[:4]])
    # G7
    # The page's OWN content (shared generated regions removed, exactly as the other
    # content checks see it): the site header's phone Menu is a <details> since Pass 2
    # Release 1 (founder-approved one-row phone Menu, 30 Oct 2026) and is governed by
    # pn_header.py / prove-global-header.py, not by this page. Page content folded into
    # <details> still fails here (see the capability proof's G7 case).
    if "<details" in strip_generated(t): bad("G7 content is folded away inside <details>")
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
    print("PREMIUM-GRP · OK — head, %d images, %d links, %d anchors, %d price regions (builder check OK), "
          "%d BASE sentences all present with %d declared additions, cautions on view, no new claim, Premium layer"
          % (sum(imgs(t).values()), sum(have.values()), len(base["ids"]), len(REGIONS), len(base_s), len(ADDED_TEXT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
