#!/usr/bin/env python3
"""PLOTNUA · DISC-026 The House as a Power Station: Pass 2 editorial redesign content guard (3 Nov 2026).

Against a pinned snapshot of the production page (atlas-tools/premium-discovery/power-station-base.json, e0af0cd):

  H  the head may only gain the three declared stylesheets; the hero (Before/Possible slider, its AI
     disclosure) only the class pn-hero-onetitle; everything after <main> is unchanged;
  C  inside <main> every text block is present verbatim, the same number of times, except the declared
     corrections (Phase 0 B3-B7, and B9 from the pre-release recheck), the declared AI label (B8) and the
     declared additions (six chapter labels, the approved chapter, tier, practicalities and route copy).
     Links, images, ids and governance comments are the same multisets, plus only the declared additions;
  P  pinned verbatim: the "Look again" section (markup, script, words), the Provider Explorer between its
     PLOTNUA-PROVIDER-EXPLORER-V1 fence markers, the GridNua banner; pinned anchors resolve;
  O  the six chapters run 01-06 in order; established technologies precede emerging ones; the decision
     closes the article; route B says it is free, sends nothing, books nothing and promises no supplier;
  F  no unsourced cost, saving or payback figure; no categorical heat-pump "bundle" figure; the approved
     AI label sits on the estate illustration;
  D  diagrams A, B, C each have a desktop and a phone variant, role="img", a <title> and a <desc>;
     every <details> is native, collapsed and carries the standard marker; tags balance.

  python3 atlas-tools/prove-premium-discovery-power-station.py
  python3 atlas-tools/prove-premium-discovery-power-station.py --snapshot REF
  python3 atlas-tools/prove-premium-discovery-power-station.py --faults    (fault injection: every mutation must be caught)
  python3 atlas-tools/prove-premium-discovery-power-station.py --diff      (authoring aid: prints undeclared blocks)
"""
import hashlib, html as H, json, os, re, subprocess, sys
from collections import Counter
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-house-as-power-station.html"
BASE = os.path.join(ROOT, "atlas-tools", "premium-discovery", "power-station-base.json")
MAIN = '<main id="pn-main">'
ALLOWED_HEAD = ['<link rel="stylesheet" href="assets/identity/pn-editorial.css?v=2">',
                '<link rel="stylesheet" href="assets/identity/pn-ps-editorial.css?v=1">',
                '<link rel="stylesheet" href="assets/identity/pn-hero-mobile-heading.css?v=1">']
PINNED_IDS = ["look-again", "explore-providers", "data-centre-heat", "home-compute", "anat-roof"]
SEAI_CALC = "https://www.seai.ie/tools/solar-electricity-calculator"
SEAI_COS = "https://www.seai.ie/grants/find-a-registered-professional/solar-pv-companies"
ADDED_LINKS = ["#anat-roof", "#explore-providers", "#look-again", SEAI_CALC, SEAI_COS, "disc026-power-station.html"]
ADDED_IDS = ["ps-decision"]
DG_IDS = ["ps%s-%s-%s" % (k, v, t) for k in "ABC" for v in "dm" for t in "td"]
CHAPTERS = ["The opportunity", "The problem", "The possibility", "What exists today", "The practicalities", "The homeowner decision"]

# Declared corrections, as visible text (old -> new). Phase 0 B3-B7 (founder-approved), B9 (pre-release recheck).
# Phase 1B recheck (3 Nov 2026): the EUR 2,000 boiler scrappage covers fossil-fuel systems only (SEAI announcement
# 29 Sep 2026; Citizens Information, edited 22 Oct 2026); the EUR 4,000 renewable heat bonus also covers electric
# storage heating (SEAI heat pump grant blog, 3 Feb 2026).
CORR = [
 ("B3a", "Up to €14,500 as a bundle for a detached, semi-detached or mid-terrace house. The ceiling is lower for an apartment, and lower again for air-to-air. SEAI.",
  "Up to €6,500 towards the heat pump in a detached, semi-detached or mid-terrace house, and up to €2,000 for central heating upgrades such as radiators. A €4,000 renewable heat bonus is added where it replaces an oil, gas, solid-fuel or electric storage system, and a €2,000 boiler scrappage grant where it replaces a fossil-fuel system: up to €14,500 in all. The amounts are lower for an apartment, and lower again for air-to-air. SEAI."),
 ("B3b", "The same €14,500 ceiling as an air-to-water system, and water-to-water likewise.",
  "The same grant as an air-to-water system (up to €6,500 for a house, and up to €14,500 in all when it replaces an oil, gas or solid-fuel system), and water-to-water likewise."),
 ("B3c", "Up to €14,500 as a bundle for a detached, semi-detached or mid-terrace house, lower for an apartment and lower again for air-to-air. Ground-source and water-to-water sit inside the same ceiling.",
  "Up to €6,500 for a detached, semi-detached or mid-terrace house, plus up to €2,000 for central heating upgrades. A €4,000 renewable heat bonus applies only when it replaces an oil, gas, solid-fuel or electric storage system, and a €2,000 boiler scrappage grant only when it replaces a fossil-fuel system, for up to €14,500 in all. Lower for an apartment and lower again for air-to-air. Ground-source and water-to-water sit inside the same grant."),
 ("B4a", "SEAI uses a Heat Loss Indicator of 2.3 or below. If your house is above it, or nobody knows, a technical assessment establishes the position.",
  "A home built before 2007 needs a technical assessment (SEAI pays €200 towards it), unless a valid BER shows a Heat Loss Indicator of 2.3 or below. A home built from 2007 onwards does not need one."),
 ("B4b", "A Heat Loss Indicator of 2.3 or below, or a technical assessment to establish the position.",
  "A technical assessment for a home built before 2007, unless a valid BER shows a Heat Loss Indicator of 2.3 or below; none for a home built from 2007 onwards."),
 ("B5a", "0% on the supply and installation of panels on a private dwelling.",
  "0% on the supply and installation of panels on a private dwelling, under a single supply-and-install contract. Panels supplied on their own are charged at 23%."),
 ("B5b", "with 0% VAT on supply and installation.",
  "with 0% VAT where the panels are supplied and installed under one contract (23% if supplied on their own)."),
 ("B6a", "The change is in the Finance (No. 2) Bill 2026, published on 19 October 2026, and is not yet law.",
  "The change, for the 2027 and 2028 tax years, is in the Finance (No. 2) Bill 2026, published on 19 October 2026, and is not yet law."),
 ("B6b", "proposes raising the exempt amount to €600; until it is enacted,",
  "proposes raising the exempt amount to €600 for the 2027 and 2028 tax years; until it is enacted,"),
 ("B7", "costs nothing and changes the bill.", "can lower the bill on a time-of-use tariff."),
 ("B9", "Available today. The grant arrives 6 October 2026.", "Available today, with an SEAI grant since 6 October 2026."),
]
AI_LABEL = "Illustrative AI-generated visualisation. Not an actual property."
ADDED = None  # filled below (declared additions, verbatim)
INLINE = {"strong", "em", "b", "i", "sup", "sub", "abbr", "a"}
VOID = {"img", "br", "input", "source", "meta", "link", "hr", "wbr", "path", "rect", "circle"}
DG = re.compile(r'<svg class="ps-dg[\s\S]*?</svg>')


def norm(x): return " ".join(H.unescape(x).replace(" ", " ").split())


class Read(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []; self.buf = ""; self.links = []; self.imgs = []; self.ids = []; self.stack = []; self.bad = 0

    def flush(self):
        w = " ".join(self.buf.replace(" ", " ").split())
        if w: self.blocks.append(w)
        self.buf = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"): self.ids.append(a["id"])
        if tag == "a": self.links.append(a.get("href"))
        if tag == "img": self.imgs.append([a.get("src"), a.get("alt")])
        if tag not in INLINE: self.flush()
        if tag not in VOID: self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID: return
        if self.stack and self.stack[-1] == tag: self.stack.pop()
        else: self.bad += 1
        if tag not in INLINE: self.flush()

    def handle_data(self, d): self.buf += d


def h(x): return hashlib.sha256(x.encode("utf-8")).hexdigest()


def between(t, a, b):
    i = t.index(a); return t[i:t.index(b, i) + len(b)]


def facts(page):
    s = page.index(MAIN); e = page.index("</main>") + len("</main>")
    head = page[:page.index("</head>")]
    for l in ALLOWED_HEAD: head = head.replace("\n" + l, "")
    pre = page[page.index("</head>"):s].replace(" pn-hero-onetitle", "")
    main = page[s:e]
    r = Read(); r.feed(DG.sub("", main)); r.flush()
    return {"head": h(head), "pre_main": h(pre), "post_main": h(page[e:]),
            "jsonld": [h(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)],
            "blocks": r.blocks, "links": r.links, "imgs": r.imgs, "ids": r.ids,
            "comments": re.findall(r"<!--.*?-->", main, re.S),
            "lag": h(between(main, "<!-- LOOK-AGAIN:BEGIN", "<!-- LOOK-AGAIN:END -->")),
            "explorer": h(between(main, "<!-- PLOTNUA-PROVIDER-EXPLORER-V1 · BEGIN", "<!-- PLOTNUA-PROVIDER-EXPLORER-V1 · END -->")),
            "banner": h(between(main, '<aside class="gridnua-banner"', "</aside>")),
            "details": main.count("<details"), "unbalanced": r.bad, "main": main}


def expected_blocks(base):
    out = []; used = Counter()
    for b in base["blocks"]:
        for _id, old, new in CORR:
            if old in b: b = b.replace(old, new); used[_id] += 1
        out.append(b)
    return Counter(out), used


def main():
    if sys.argv[1:2] == ["--snapshot"]:
        page = subprocess.check_output(["git", "show", sys.argv[2] + ":" + PAGE], cwd=ROOT).decode("utf-8")
        f = facts(page); f.pop("main"); f["ref"] = sys.argv[2]
        json.dump(f, open(BASE, "w"), indent=1, ensure_ascii=False); print("base written from", sys.argv[2]); return
    base = json.load(open(BASE)); page = open(os.path.join(ROOT, PAGE), encoding="utf-8").read()
    if sys.argv[1:2] == ["--diff"]:
        now = facts(page); want, used = expected_blocks(base); have = Counter(now["blocks"])
        print(json.dumps(list((have - want).elements()), ensure_ascii=False, indent=1))
        print("MISSING", list((want - have).elements())); return
    if sys.argv[1:2] == ["--faults"]:
        return faults(page, base)
    bad, ok = verify(page, base, True)
    print("POWER STATION EDITORIAL GUARD · %s — %d passed, %d failed" % ("OK" if not bad else "FAILED", ok, len(bad)))
    sys.exit(1 if bad else 0)


FAULTS = [  # (what a careless edit would do, mutation)
 ("a legacy builder regenerates the old heat pump 'bundle' text", lambda t: t.replace("Up to &euro;6,500 towards the heat pump", "Up to &euro;14,500 as a bundle towards the heat pump", 1)),
 ("one existing sentence is dropped", lambda t: t.replace("each supplier sets its own.", "", 1)),
 ("the Look again animation script is altered", lambda t: t.replace("<!-- LOOK-AGAIN:END -->", "<script>/*x*/</script><!-- LOOK-AGAIN:END -->", 1)),
 ("the Provider Explorer fence is hand-edited", lambda t: t.replace("<!-- PLOTNUA-PROVIDER-EXPLORER-V1 · END -->", "<p>edited</p><!-- PLOTNUA-PROVIDER-EXPLORER-V1 · END -->", 1)),
 ("the GridNua banner wording changes", lambda t: (lambda i: t[:i] + t[i:].replace("</p>", " Coming soon.</p>", 1))(t.index('<aside class="gridnua-banner"'))),
 ("the hero slider markup changes", lambda t: t.replace('data-to="100"', 'data-to="50"', 1)),
 ("a drawer ships open", lambda t: t.replace('<details class="faq-item is-inline ps-big">', '<details class="faq-item is-inline ps-big" open>', 1)),
 ("route B is renamed an enquiry", lambda t: t.replace("Start the free guided check", "Begin a free guided enquiry", 1)),
 ("route B stops saying nothing is sent", lambda t: t.replace("nothing is sent to PlotNua or anyone else", "your answers help us", 1)),
 ("an unsourced payback figure is added", lambda t: t.replace("Before anything goes on the roof.", "Before anything goes on the roof. Payback of 6 years is typical.", 1)),
 ("the chapter 01 status boundary is removed", lambda t: t.replace('<p class="ps-boundary">', '<p class="ps-short2">', 1)),
 ("the scrappage grant is tied to electric storage heating again", lambda t: t.replace("and a &euro;2,000 boiler scrappage grant where it replaces a fossil-fuel system", "and a &euro;2,000 boiler scrappage grant where it replaces an electric storage system", 1)),
 ("the phone dimension key loses the 14 m setback", lambda t: t.replace("<strong>14 m</strong>", "<strong>12 m</strong>", 1)),
 ("the phone heat path drops its condition on the model key", lambda t: t.replace("Compute, with CHP where the gas infrastructure exists</span>", "Compute, with CHP</span>", 1)),
 ("the estate image's AI label is removed", lambda t: t.replace('<p class="ps-ai">Illustrative AI-generated visualisation. Not an actual property.</p>', "", 1)),
 ("a new image asset is added", lambda t: t.replace("<h2>Four parts, working together.</h2>", '<h2>Four parts, working together.</h2><img src="assets/img/new.jpg" alt="x">', 1)),
 ("a pinned anchor is lost", lambda t: t.replace('id="explore-providers"', 'id="explore-suppliers"', 1)),
 ("a diagram loses its accessible description", lambda t: t.replace('<desc id="psC-m-d">', '<desc>', 1)),
 ("a wrapper is left unbalanced", lambda t: t.replace('<section class="article-section ps-practical">', '<section class="article-section ps-practical"><div>', 1)),
 ("the chapters are reordered", lambda t: t.replace('<span class="kicker">The problem</span>', '<span class="kicker">The problem.</span>', 1)),
 ("an undeclared stylesheet is added to the head", lambda t: t.replace("</head>", '<link rel="stylesheet" href="x.css">\n</head>', 1)),
]


def faults(page, base):
    caught = 0
    for what, f in FAULTS:
        t = f(page)
        if t == page:
            print("  SKIP  mutation did not apply: %s" % what); continue
        try:
            bad, _ = verify(t, base, False)
        except (ValueError, KeyError) as e:
            bad = ["structure lost (%s)" % e]
        caught += bool(bad)
        print("  %s %s%s" % ("caught" if bad else "MISSED", what, (" · " + bad[0][:70]) if bad else ""))
    print("POWER STATION GUARD FAULT TEST · %s — %d/%d faults caught" % ("OK" if caught == len(FAULTS) else "FAILED", caught, len(FAULTS)))
    sys.exit(0 if caught == len(FAULTS) else 1)


def verify(page, base, loud):
    now = facts(page)
    want, used = expected_blocks(base); have = Counter(now["blocks"])
    bad = []; ok = 0
    def check(name, cond, why=""):
        nonlocal ok
        if cond:
            ok += 1
            if loud: print("  ok   " + name)
        else:
            bad.append(name)
            if loud: print("  FAIL " + name + (" · " + why if why else ""))
    m = now["main"]; text = norm(re.sub(r"<[^>]+>", " ", re.sub(r"<!--.*?-->|<script[\s\S]*?</script>", " ", m)))
    check("H1 head (title, meta, canonical, Open Graph) unchanged but for the three declared stylesheets", now["head"] == base["head"])
    check("H2 structured data unchanged", now["jsonld"] == base["jsonld"])
    check("H3 hero, Before/Possible slider and its AI disclosure unchanged (the approved one-title class aside)", now["pre_main"] == base["pre_main"])
    check("H4 everything after <main> (related Discoveries, footer, Back, dock, scripts) unchanged", now["post_main"] == base["post_main"])
    for _id, old, new in CORR:
        check("R1 declared correction %s applied once: '%s...'" % (_id, new[:46]), used[_id] == 1 and old not in text and new in text,
              "base matches %d" % used[_id])
    for c in CHAPTERS:
        check("D1 chapter label '%s' added once" % c, have[c] == 1 and c not in base["blocks"])
    extra = have - want; missing = want - have
    added = Counter(ADDED + CHAPTERS + [AI_LABEL])
    check("C1 every other text block in <main> present verbatim, the same number of times (%d blocks)" % sum(want.values()),
          not missing, "missing %s" % list(missing.elements())[:2])
    check("C1 nothing added beyond the declared additions (%d declared)" % sum(added.values()),
          extra == added, "undeclared %s · absent %s" % (list((extra - added).elements())[:2], list((added - extra).elements())[:2]))
    check("C2 links: the same multiset, plus only the declared route and SEAI links",
          Counter(now["links"]) == Counter(base["links"]) + Counter(ADDED_LINKS))
    check("C3 images identical (file and alt text): no new image asset",
          sorted(map(tuple, now["imgs"])) == sorted(map(tuple, base["imgs"])))
    check("C4 ids and anchors identical, plus only the declared decision and diagram ids",
          Counter(now["ids"]) == Counter(base["ids"]) + Counter(ADDED_IDS))
    xc = Counter(now["comments"]) - Counter(base["comments"])
    check("C5 governance comments carried over verbatim (three declared comments added: the Pass 2 header, the two phone presentations)",
          not (Counter(base["comments"]) - Counter(now["comments"])) and sum(xc.values()) == 3
          and any("DISC-026 PASS 2 EDITORIAL" in c for c in xc) and any("PHONE MARKERS" in c for c in xc)
          and any("PHONE PRESENTATION" in c for c in xc))
    check("P1 'Look again' (illustration, animation, seven positions, script, words) byte-identical", now["lag"] == base["lag"])
    check("P2 Provider Explorer byte-identical between its PLOTNUA-PROVIDER-EXPLORER-V1 fence markers", now["explorer"] == base["explorer"])
    check("P3 GridNua banner byte-identical (approved wording)", now["banner"] == base["banner"])
    check("P4 pinned anchors resolve: " + ", ".join("#" + i for i in PINNED_IDS), all(now["ids"].count(i) == 1 for i in PINNED_IDS))
    check("P5 the Property Check and Compute Readiness links remain",
          'href="disc026-power-station.html"' in m and 'href="disc026-compute-readiness-check.html"' in m)
    pos = [m.index('<span class="kicker">%s</span>' % c) for c in CHAPTERS]
    check("O1 the six chapters run 01-06 in order", pos == sorted(pos) and all(
        '<span class="pe-chapter-n" aria-hidden="true">%02d</span><span class="kicker">%s</span>' % (i + 1, c) in m for i, c in enumerate(CHAPTERS)))
    check("O2 established technologies precede emerging ones, and the emerging tier says none is a ready product here",
          m.index("Established homeowner technologies") < m.index("Emerging or site-dependent possibilities")
          and "None is offered to Irish homeowners as a ready-to-install product today" in m)
    check("O5 the status boundary is read before the grants: chapter 01 says the computing is not available, ahead of the energy anatomy",
          "ps-boundary" in m and m.index("ps-boundary") < m.index("The energy anatomy of your property"))
    check("O3 the homeowner decision closes the article (after the practicalities and the explorer)",
          pos[5] > m.index("<!-- PLOTNUA-PROVIDER-EXPLORER-V1 · END -->") and m.index('id="ps-decision"') > pos[4])
    note = text[text.index("Let PlotNua do the homework"):]
    check("O4 route B: 'Start the free guided check' to the existing Property Check; free, nothing sent, no booking, no supplier promised",
          '<a class="ps-btn" href="disc026-power-station.html">Start the free guided check</a>' in m
          and all(x in note for x in ("It is free", "nothing is sent to PlotNua or anyone else", "nothing here books an installation",
                                     "promises a supplier or a match")) and "enquiry" not in note[:900].lower())
    check("F1 no unsourced installed-cost, saving or payback figure in the new copy",
          not re.search(r"payback (of|period of) \d|\d+\s*(to|-)\s*\d+\s*years|save[sd]? (you )?€|€[\d,]+ (a|per) year (saving|saved)|typical(ly)? cost", text, re.I))
    check("F2 no heat-pump 'bundle' figure remains; €14,500 appears only with its replacement condition",
          "as a bundle" not in text and "14,500 ceiling" not in text
          and all("replac" in text[max(0, i.start() - 260):i.start() + 40] for i in re.finditer("14,500", text)))
    check("F3 the approved AI label sits on the estate illustration's caption",
          re.search(r'f0e99db16cefc470\.jpg[\s\S]{0,900}?<p class="ps-ai">' + re.escape(AI_LABEL) + "</p>", m) is not None)
    svgs = DG.findall(m)
    check("D2 diagrams A, B, C: desktop and phone variants, each role=img with a unique <title> and <desc>",
          len(svgs) == 6 and all('role="img"' in v and "<title id=" in v and "<desc id=" in v for v in svgs)
          and m.count('<figure class="ps-fig') == 3 and m.count('<figcaption class="ps-cap">') == 3
          and sorted(re.findall(r'<(?:title|desc) id="([^"]+)"', "".join(svgs))) == sorted(DG_IDS)
          and all(m.count('id="%s"' % i) == 1 for i in DG_IDS))
    nd = now["details"]
    check("D3 every drawer is native <details>, collapsed in the markup, with the standard marker (%d, of which 3 new)" % nd,
          nd == base["details"] + 3 and "<details open" not in m and not re.search(r"<details[^>]*\sopen", m)
          and m.count('class="faq-item is-inline ps-big"') == 3)
    check("D4 tags balance inside <main>", now["unbalanced"] == 0)
    css = open(os.path.join(ROOT, "assets/identity/pn-ps-editorial.css"), encoding="utf-8").read()
    check("D5 drawer content is visible on opening; diagrams honour reduced motion",
          "details .reveal{opacity:1!important" in css and "prefers-reduced-motion:reduce" in css)
    check("D6 the tall energy-anatomy section is never left unrevealed on a phone; the Back clears the footer",
          ".article-section.reveal:has(.anat){opacity:1!important" in css and "footer{padding-bottom:" in css)
    check("D7 the legacy drawings are restyled for the dark ground (ivory line work, terracotta labels, ivory markers); phones get the numbered and dimension keys",
          '[stroke="#1F3B2E"]{stroke:#E9E2D6}' in css and 'g[font-size="9.5"] > g[fill="#8FAF8A"]{fill:#F2EBE0' in css
          and m.count('<ol class="anat-key" aria-hidden="true">') == 1 and m.count('<ul class="anat-key is-dims" aria-hidden="true">') == 1
          and all(k in m for k in ("<b>1</b>Roof", "<b>7</b>Grid", "<strong>13 m</strong>", "<strong>14 m</strong>")))
    check("D8 the two computing drawings have phone presentations: the stacked heat path (same glyphs and words) and numbered markers with a key on the model",
          m.count('<svg class="fs-m" viewBox="0 0 340 318" role="img"') == 1 and m.count('<g class="m-mark"') == 1
          and m.count('<ol class="anat-key is-pairs" aria-hidden="true">') == 1
          and all(k in m for k in ("HEAT, AND SOMEWHERE", "FOR IT TO GO", "Compute, with CHP where the gas infrastructure exists", "Homes taking heat from a shared network"))
          and ".fig-strip > svg.fs-m{display:none}" in css and ".m-mark{display:none}" in css)
    check("F4 boiler scrappage is tied to fossil-fuel systems only; the renewable heat bonus also to electric storage",
          "boiler scrappage grant where it replaces a fossil-fuel system" in text
          and "boiler scrappage grant only when it replaces a fossil-fuel system" in text
          and not re.search(r"scrappage grant[^.]{0,80}electric storage", text))
    return bad, ok


ADDED = json.load(open(os.path.join(ROOT, "atlas-tools", "premium-discovery", "power-station-added.json"), encoding="utf-8")) \
    if os.path.exists(os.path.join(ROOT, "atlas-tools", "premium-discovery", "power-station-added.json")) else []

if __name__ == "__main__":
    main()
