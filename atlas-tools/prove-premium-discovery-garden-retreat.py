#!/usr/bin/env python3
"""PLOTNUA · DISC-001 Garden Retreat: Phase 2 six-chapter editorial redesign content guard (4 Nov 2026).

Written BEFORE the page was restructured, against a pinned snapshot of the production page
(atlas-tools/premium-discovery/garden-retreat-base.json, taken at f32837f). The guarded region is
<main> plus the closing panel (#discover-your-property), up to the related Discoveries.

  H  the head may only gain the declared stylesheet; everything between </head> and <main> (header,
     search rail, hero, hero notes) and everything from the related Discoveries to the end of the
     document is byte-identical;
  S  the Before/Possible hero slider (figure#grHeroCompare) is unchanged and opens at BEFORE
     (data-start="100") with two separate full-size images;
  G  the Premium Supplier Gallery region and the Maker Explorer section are byte-identical to
     production (suppliers, licensed images, credits, random order, categories, counts, prices,
     links, the TimberIN referral disclosure, OGNYX and Tanktribe conditions);
  C  every text block in the guarded region is present, the same number of times, except the declared
     removals (the "property check is being prepared" headline and its paragraph) and the declared
     additions (chapter openings, chapter 02, the footprint drawing, the chapter 05 group labels, the
     chapter 06 routes);
  L  every link, image source and id in the guarded region survives (as a set), plus only the declared
     additions; every inbound anchor still resolves;
  O  the six chapters run 01-06 in order; the comparison sits in chapter 03; the gallery and the Maker
     Explorer sit in chapter 04; "Could it work", the practical guide and the sources sit in chapter 05,
     the rules group before the guidance group; the decision (chapter 06) is the closing panel and
     carries both routes, A and B; the chapter navigation reaches all six;
  F  route B is the existing WhatsApp channel, free for homeowners, with no form, input or script and no
     matching, budget, referral, commission or assessment promise; no placeholder is published; the
     footprint drawing has a desktop and a phone layout and says it is indicative;
  D  tags balance; every <details> is native and collapsed.

  python3 atlas-tools/prove-premium-discovery-garden-retreat.py
  python3 atlas-tools/prove-premium-discovery-garden-retreat.py --snapshot REF
  python3 atlas-tools/prove-premium-discovery-garden-retreat.py --diff      (authoring aid)
  python3 atlas-tools/prove-premium-discovery-garden-retreat.py --faults    (every mutation must be caught)
"""
import html as H, json, os, re, subprocess, sys
from collections import Counter
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-garden-retreat.html"
BASE = os.path.join(ROOT, "atlas-tools", "premium-discovery", "garden-retreat-base.json")
MAIN = '<main id="pn-main">'
CLOSE_END = '<section class="related reveal">'
ALLOWED_HEAD = ['<link rel="stylesheet" href="assets/identity/pn-gr-editorial.css?v=1">']
WHATSAPP = "https://wa.me/353834036695"
INBOUND = ["suppliers", "explore-makers", "maker-index", "compare", "three-ways-in",
           "could-it-work", "the-practical-part", "where-this-comes-from", "discover-your-property",
           "option-sauna", "option-hot-tub", "option-cold-plunge", "grHeroCompare", "dHeroCopy"]
CHAPTERS = ["The opportunity", "The problem", "The possibility", "What exists today", "The practicalities",
            "The homeowner decision"]
GALLERY_RE = r"<!-- PN-SUPPLIER-GALLERY v1 .*?<!-- /PN-SUPPLIER-GALLERY -->"
EXPLORER_RE = r'  <!-- 6c · PLOTNUA-MAKER-EXPLORER-V1.*?\n  </section>\n'
HERO_RE = r'<figure class="pn-compare pn-compare--hero" id="grHeroCompare".*?</figure>'
BLOCK = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "summary", "figcaption", "td", "th", "dt", "dd", "caption",
         "blockquote", "label", "button"}
VOID = {"img", "br", "input", "source", "meta", "link", "hr", "wbr", "path", "rect", "circle", "line", "polyline",
        "polygon", "ellipse", "use", "stop", "col", "area", "base", "embed", "param", "track"}

# ---- declared changes ------------------------------------------------------------------------------------
# Removed (founder decision I4, Phase 1 report): the closing panel's "This property check is being prepared"
# headline and its paragraph. Its point that nothing on the page assesses a property is still made, visibly,
# in "Could it work for your property?" (GR4 requires it).
REMOVED = ["This property check is being prepared",
           "The real question is not which sauna to buy. It is what kind of retreat your garden could take — "
           "your clear space and where it is, whether power and water reach it, the ground, what is already built "
           "there. PlotNua is building a check that asks those questions. It is not ready, and nothing on this page "
           "assesses your property."]
REMOVED_LINKS = []
CORR = []
ADDED_FILE = os.path.join(ROOT, "atlas-tools", "premium-discovery", "garden-retreat-added.json")
ADDED_LINKS = ["#lg-ch01", "#lg-ch02", "#lg-ch03", "#lg-ch04", "#lg-ch05", "#lg-ch06", "#suppliers",
               "#explore-makers", "#compare", "#the-practical-part", "your-plot.html?myplot=1", WHATSAPP]
ADDED_IDS = ["lg-ch01", "lg-ch02", "lg-ch03", "lg-ch04", "lg-ch05", "lg-ch06", "grNextH", "grFpCap"]
PLACEHOLDER = re.compile(r"\bto research\b|\bTBC\b|\bTBD\b|lorem|placeholder|coming soon", re.I)
PROMISE = re.compile(r"\bmatch(?:es|ed|ing)?\b|\bbudget\b|\bcommission|\breferr|\bintroduc|\bpartner|\bguarantee|"
                     r"\bbest\b|\bwe(?:'|’)ll assess|\bassessed your\b|\bsuitab", re.I)


def norm(s):
    return re.sub(r"\s+", " ", H.unescape(s)).strip()


class Blocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.out, self.links, self.imgs, self.ids, self.bad, self.skip = [], [], [], [], [], 0, 0
        self.details = []

    def handle_starttag(self, t, a):
        a = dict(a)
        if a.get("id"): self.ids.append(a["id"])
        if t == "a" and a.get("href"): self.links.append(a["href"])
        if t in ("img", "source") and (a.get("src") or a.get("srcset")):
            self.imgs.append((a.get("src") or a.get("srcset")).split()[0])
        if t == "details": self.details.append(a)
        if t in ("script", "style", "svg"): self.skip += 1
        if t in VOID: return
        self.stack.append([t, []])

    def handle_endtag(self, t):
        if t in VOID: return
        if not self.stack or self.stack[-1][0] != t:
            self.bad += 1
            while self.stack and self.stack[-1][0] != t: self.stack.pop()
            if not self.stack: return
        tag, buf = self.stack.pop()
        if tag in ("script", "style", "svg"): self.skip -= 1
        txt = norm("".join(buf))
        if tag in BLOCK and txt: self.out.append(txt)
        if self.stack: self.stack[-1][1].append("".join(buf) + " ")

    def handle_data(self, d):
        if self.skip or not self.stack: return
        self.stack[-1][1].append(d)


def regions(src):
    h = src.index("</head>")
    a = src.index(MAIN)
    z = src.index(CLOSE_END)
    return src[:h], src[h:a], src[a:z], src[z:]


def parse(region):
    p = Blocks(); p.feed(region); p.close()
    return p


def grab(rx, s):
    m = re.search(rx, s, re.S)
    return m.group(0) if m else None


def snapshot(ref):
    src = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (ref, PAGE)], capture_output=True, text=True, check=True).stdout
    head, pre, body, post = regions(src)
    p = parse(body)
    d = {"ref": ref, "head": head, "pre": pre, "post": post, "hero": grab(HERO_RE, src),
         "gallery": grab(GALLERY_RE, body), "explorer": grab(EXPLORER_RE, body), "blocks": p.out,
         "links": sorted(set(p.links)), "imgs": sorted(set(p.imgs)), "ids": sorted(set(p.ids))}
    os.makedirs(os.path.dirname(BASE), exist_ok=True)
    json.dump(d, open(BASE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("snapshot %s: %d blocks, %d links, %d images, %d ids" % (ref, len(p.out), len(d["links"]), len(d["imgs"]), len(d["ids"])))


def load_added():
    """Declared additions. "supplierCards" (4 Nov 2026, Gardenhouse24): a supplier gallery card added
    after the snapshot is declared here, card by card: its exact text blocks, image and links. Each
    card's image and links must also pass the supplier gallery guard and the Image Rights Gate."""
    if os.path.exists(ADDED_FILE):
        x = json.load(open(ADDED_FILE, encoding="utf-8"))
        blocks, imgs = list(x.get("blocks", [])), list(x.get("imgs", []))
        for c in x.get("supplierCards", []):
            blocks += c["blocks"]; imgs += c["imgs"]
        for u in x.get("targetedUpdates", []):
            blocks += u.get("blocks", []); imgs += u.get("imgs", [])   # imgs: 10 Nov 2026 (Arctic Wellness card)
        return blocks, imgs
    return [], []


def targeted_updates():
    """Declared targeted supplier updates ("targetedUpdates", 4 Nov 2026, Supplier integration Phase 2):
    exact from -> to edits to the pinned gallery and explorer regions (each must apply exactly once),
    text-block corrections, added text blocks and added links. Nothing else may change."""
    if os.path.exists(ADDED_FILE):
        return json.load(open(ADDED_FILE, encoding="utf-8")).get("targetedUpdates", [])
    return []


MX_DATA_RE = r'(<script type="application/json" class="pn-mx-config" id="mx-data">).*?(</script>)'


def apply_edits(region, edits, what, bad):
    for a, b in edits:
        if region is None or region.count(a) != 1:
            bad.append("G declared %s update no longer applies to the pinned baseline: %s" % (what, a[:80]))
            continue
        region = region.replace(a, b, 1)
    return region


def declared_cards():
    if os.path.exists(ADDED_FILE):
        return [c["supplier"] for c in json.load(open(ADDED_FILE, encoding="utf-8")).get("supplierCards", [])]
    return []


def added_links():
    if os.path.exists(ADDED_FILE):
        x = json.load(open(ADDED_FILE, encoding="utf-8"))
        return ([l for c in x.get("supplierCards", []) for l in c["links"]]
                + [l for u in x.get("targetedUpdates", []) for l in u.get("links", [])])
    return []


def text(s):
    return norm(re.sub(r"<!--.*?-->|<script.*?</script>|<style.*?</style>|<[^>]+>", " ", s, flags=re.S))


def check(src, base):
    bad = []
    added, added_imgs = load_added()
    try:
        head, pre, body, post = regions(src)
    except ValueError:
        return ["H the guarded region markers are missing"]
    # H
    for l in ALLOWED_HEAD:
        head = head.replace(l + "\n", "").replace(l, "")
    if re.sub(r"\s+", "", head) != re.sub(r"\s+", "", base["head"]):
        bad.append("H the head changed beyond the declared stylesheet")
    if pre != base["pre"]:
        bad.append("H the header, hero or hero notes changed")
    if post != base["post"]:
        bad.append("H the page after the closing panel changed")
    # S
    hero = grab(HERO_RE, src)
    if hero != base["hero"]:
        bad.append("S the Before/Possible hero slider changed")
    elif 'data-start="100"' not in hero or len(re.findall(r"<img\b", hero)) < 2:
        bad.append("S the slider must start at BEFORE with two images")
    # G
    # declared supplier cards (supplierCards in ADDED_FILE) are removed, card by card, before the byte
    # comparison; each must appear exactly once; everything else in the region stays byte-identical
    gal = grab(GALLERY_RE, body)
    for name in declared_cards():
        li = re.findall(r'<li data-sg-placement="editorial"><article class="pn-sg-card" aria-label="%s">.*?</article></li>' % re.escape(name), gal or "", re.S)
        if len(li) != 1:
            bad.append("G declared supplier card %s is missing or duplicated" % name)
        else:
            gal = gal.replace(li[0], "", 1)
    base_gal, base_exp = base["gallery"], base["explorer"]
    for u in targeted_updates():
        base_gal = apply_edits(base_gal, u.get("gallery", []), "gallery", bad)
        base_exp = apply_edits(base_exp, u.get("explorer", []), "explorer", bad)
    if gal != base_gal:
        bad.append("G the Premium Supplier Gallery region changed")
    exp = grab(EXPLORER_RE, body)
    if targeted_updates():
        # the explorer's data payload is owned by build-maker-explorer.py --check (G1-G14)
        exp = re.sub(MX_DATA_RE, r"\1\2", exp or "", flags=re.S)
        base_exp = re.sub(MX_DATA_RE, r"\1\2", base_exp or "", flags=re.S)
    if exp != base_exp:
        bad.append("G the Maker Explorer section changed")
    # C
    p = parse(body)
    have, want = Counter(p.out), Counter(base["blocks"])
    for r in REMOVED:
        want[norm(r)] -= 1
    for _c, old, new in CORR:
        want[norm(old)] -= 1; want[norm(new)] += 1
    for u in targeted_updates():
        for old, new in u.get("blockCorrections", []):
            want[norm(old)] -= 1; want[norm(new)] += 1
    for a in added:
        want[norm(a)] += 1
    want = +want
    for t, n in (want - have).items():
        bad.append("C missing text block (x%d): %s" % (n, t[:110]))
    for t, n in (have - want).items():
        bad.append("C undeclared text block (x%d): %s" % (n, t[:110]))
    # L
    links, imgs, ids = set(p.links), set(p.imgs), set(p.ids)
    for l in base["links"]:
        # removedLinks / removedImgs in a targeted update (12 Nov 2026, ISC Aran/Skellig leave): a product
        # that leaves the explorer takes its anchor and lead image with it; each must be declared
        if l not in links and l not in REMOVED_LINKS and l not in {x for u in targeted_updates() for x in u.get("removedLinks", [])}:
            bad.append("L link lost: " + l)
    for l in links - set(base["links"]) - set(ADDED_LINKS) - set(added_links()):
        bad.append("L undeclared link: " + l)
    for i in base["imgs"]:
        if i not in imgs and i not in {x for u in targeted_updates() for x in u.get("removedImgs", [])}:
            bad.append("L image lost: " + i)
    for i in imgs - set(base["imgs"]) - set(added_imgs):
        bad.append("L undeclared image: " + i)
    for i in base["ids"]:
        if i not in ids: bad.append("L id lost: " + i)
    for i in ids - set(base["ids"]) - set(ADDED_IDS) - {i for u in targeted_updates() for i in u.get("ids", [])}:
        bad.append("L undeclared id: " + i)
    for a in INBOUND:
        if 'id="%s"' % a not in src: bad.append("L inbound anchor missing: #" + a)
    # O
    pos = []
    for n, name in enumerate(CHAPTERS, 1):
        i = body.find('id="lg-ch%02d"' % n)
        if i < 0: bad.append("O chapter %02d (%s) missing" % (n, name)); pos.append(-1); continue
        if name.lower() not in text(body[i:i + 600]).lower():
            bad.append("O chapter %02d is not labelled %s" % (n, name))
        pos.append(i)
    if -1 not in pos and pos != sorted(pos):
        bad.append("O the six chapters are out of order")
    if -1 not in pos:
        def inside(anchor, ch):
            i = body.find(anchor)
            hi = pos[ch] if ch < 6 else len(body)
            return pos[ch - 1] < i < hi
        for anchor, ch in (('id="three-ways-in"', 3), ('id="compare"', 3), ('class="gr-fp', 3),
                           ('id="suppliers"', 4), ('id="explore-makers"', 4), ('id="could-it-work"', 5),
                           ('id="the-practical-part"', 5), ('id="where-this-comes-from"', 5)):
            if not inside(anchor, ch): bad.append("O %s must sit in chapter %02d" % (anchor, ch))
        rq, gd = body.find("lg-group is-req"), body.find("lg-group is-guide")
        if not (pos[4] < rq < gd < body.find('id="where-this-comes-from"')):
            bad.append("O chapter 05 must show the requirements group before the guidance group")
        dec = body.find('id="discover-your-property"')
        if not (body.find("</main>") < dec < pos[5] and pos[5] - dec < 1500):
            bad.append("O the decision must be chapter 06, in the closing panel")
    nav = grab(r"<nav class=\"hfa-nav\" data-pd-nav.*?</nav>", body)
    if not nav or [h for h in re.findall(r'href="#(lg-ch0\d)"', nav)] != ["lg-ch0%d" % i for i in range(1, 7)]:
        bad.append("O the chapter navigation must link chapters 01-06 in order")
    dec = body[body.find('id="discover-your-property"'):] if 'id="discover-your-property"' in body else ""
    for k in ("Explore yourself", "Let PlotNua do the homework"):
        if k not in dec: bad.append("O route missing from the decision: " + k)
    # F
    if dec:
        if re.search(r"<form\b|<input\b|<textarea\b|<select\b|<script\b|workers\.dev|fetch\s*\(", dec, re.I):
            bad.append("F the decision carries a form, input or script")
        rb = grab(r'<div class="lg-route is-b">.*?</div>\s*</div>', dec) or ""
        if 'href="%s"' % WHATSAPP not in rb:
            bad.append("F route B must use the existing WhatsApp channel")
        if "Free for homeowners" not in text(rb):
            bad.append("F route B must say it is free for homeowners")
        vis = text(dec)
        if PROMISE.search(vis):
            bad.append("F the decision makes a commercial or assessment promise: " + PROMISE.search(vis).group(0))
    if PLACEHOLDER.search(text(body)):
        bad.append("F placeholder text published: " + PLACEHOLDER.search(text(body)).group(0))
    fp = grab(r"<figure class=\"gr-fp\".*?</figure>", body)
    if not fp:
        bad.append("F the footprint drawing is missing")
    else:
        if not re.search(r"\bindicative\b", text(fp), re.I):
            bad.append("F the footprint drawing must say it is indicative")
        if fp.count("<svg") != 2 or "gr-fp-d" not in fp or "gr-fp-m" not in fp:
            bad.append("F the footprint drawing needs one desktop and one phone layout")
    # D
    if p.bad or p.stack:
        bad.append("D tags do not balance (%d mismatches, %d open)" % (p.bad, len(p.stack)))
    for d in p.details:
        if "open" in d: bad.append("D a <details> is open by default")
    return bad


FAULTS = [
    ("hero start moved to POSSIBLE", lambda s: s.replace('data-start="100" data-subject="the garden"', 'data-start="0" data-subject="the garden"', 1), "S"),
    ("hero copy edited", lambda s: s.replace(">Compare the options</a>", ">Compare options</a>", 1), "H"),
    ("a price edited", lambda s: s.replace("&euro;1,699 &mdash; Timbertrove", "&euro;1,599 &mdash; Timbertrove", 1), "C"),
    ("the referral disclosure removed", lambda s: s.replace("Current commercial relationship: TimberIN", "TimberIN", 1), "G"),
    ("a gallery card reordered", lambda s: s.replace('data-sg-placement="editorial"', 'data-sg-placement="lead"', 1), "G"),
    ("a source link dropped", lambda s: s.replace('href="https://www.safeelectric.ie/"', 'href="https://example.com/"', 1), "L"),
    ("an inbound anchor renamed", lambda s: s.replace('id="could-it-work"', 'id="could-it"', 1), "L"),
    ("chapters reordered", lambda s: s.replace('id="lg-ch02"', 'id="lg-chX"', 1).replace('id="lg-ch05"', 'id="lg-ch02"', 1).replace('id="lg-chX"', 'id="lg-ch05"', 1), "O"),
    ("Could it work moved back above the makers", lambda s: s.replace('id="could-it-work"', 'id="cw-tmp"', 1).replace('id="three-ways-in"', 'id="could-it-work"', 1), "O"),
    ("guidance group placed before rules", lambda s: s.replace("lg-group is-req", "lg-group is-tmp", 1).replace("lg-group is-guide", "lg-group is-req", 1).replace("lg-group is-tmp", "lg-group is-guide", 1), "O"),
    ("route A dropped", lambda s: s.replace("Explore yourself", "Explore", 99), "O"),
    ("free statement removed", lambda s: s.replace("Free for homeowners", "For homeowners", 99), "F"),
    ("WhatsApp swapped for a contact form", lambda s: s.replace('href="%s" data-gr-route' % WHATSAPP, 'href="contact.html" data-gr-route', 1), "F"),
    ("a form added to the decision", lambda s: s.replace('id="discover-your-property"', 'id="discover-your-property"><form></form', 1), "F"),
    ("an assessment promise added", lambda s: s.replace("Free for homeowners.", "Free for homeowners. We&rsquo;ll assess your garden and match you with the best maker.", 1), "F"),
    ("placeholder published", lambda s: s.replace("</main>", "<p>To research</p></main>", 1), "F"),
    ("drawing label removed", lambda s: s.replace("Indicative", "Drawn", 99).replace("indicative", "drawn", 99), "F"),
    ("details opened", lambda s: s.replace('<details class="faq-item gr-acc">', '<details class="faq-item gr-acc" open>', 1), "D"),
    ("targeted update: an undeclared A-Z line for another maker", lambda s: s.replace('        <li><a href="#p-recIy8ghdKxo7PTjP">Hansa24 Group</a>', '        <li><a href="#p-recIy8ghdKxo7PTjP">Auroom Wellness</a> <span>2 saunas &middot; Irish availability not yet confirmed</span></li>\n        <li><a href="#p-recIy8ghdKxo7PTjP">Hansa24 Group</a>', 1), "G"),
    ("targeted update: explorer sauna count edited", lambda s: s.replace('Saunas <span class="mx-n">98</span>', 'Saunas <span class="mx-n">99</span>', 1), "G"),
    ("targeted update: gallery figure edited", lambda s: s.replace('<span class="pn-sg-fig">98</span>', '<span class="pn-sg-fig">97</span>', 1), "G"),
    # SEO-GR4 (8 Nov 2026): the declared line now ends with the maker's approved profile link
    ("targeted update: a declared A-Z line removed", lambda s: s.replace('        <li><a href="#p-recEDHcHJ5dWaWklV">Gardenhouse24 Ireland</a> <span>2 hot tubs &middot; Irish availability not yet confirmed</span> <a class="mx-az-pf" href="suppliers/gardenhouse24.html">Gardenhouse24 profile</a></li>\n', '', 1), "G"),
    ("SEO-GR4: a profile link added to a maker without an approved profile", lambda s: s.replace('Hansa24 Group</a> <span>', 'Hansa24 Group</a> <a class="mx-az-pf" href="suppliers/gardenhouse24.html">Hansa24 profile</a> <span>', 1), "G"),
    ("targeted update: availability wording upgraded", lambda s: s.replace('Gardenhouse24 Ireland</a> <span>4 saunas &middot; Irish availability not yet confirmed', 'Gardenhouse24 Ireland</a> <span>4 saunas &middot; Irish availability confirmed', 1), "G"),
    ("footer edited", lambda s: s.replace("Related Discoveries</h2>", "Related</h2>", 1), "H"),
    ("undeclared stylesheet", lambda s: s.replace("</head>", '<link rel="stylesheet" href="x.css">\n</head>', 1), "H"),
    ("an undeclared supplier card is added", lambda s: s.replace('aria-label="Gardenhouse24 Ireland">', 'aria-label="Invented Garden Co">', 1), "G"),
]


def main():
    if "--snapshot" in sys.argv:
        return snapshot(sys.argv[sys.argv.index("--snapshot") + 1])
    base = json.load(open(BASE, encoding="utf-8"))
    src = open(os.path.join(ROOT, PAGE), encoding="utf-8").read()
    if "--faults" in sys.argv:
        if check(src, base):
            print("FAULTS · the real page must pass first"); return 1
        missed = 0
        for name, fn, code in FAULTS:
            m = fn(src)
            hit = m != src and any(b.startswith(code) for b in check(m, base))
            print("  %s  %s" % ("CAUGHT" if hit else "MISSED", name)); missed += 0 if hit else 1
        print("DISC-001 GUARD FAULTS · %s — %d/%d caught" % ("OK" if not missed else "FAILED", len(FAULTS) - missed, len(FAULTS)))
        return 1 if missed else 0
    bad = check(src, base)
    if "--diff" in sys.argv:
        for b in bad: print(b)
        return 0
    if bad:
        for b in bad[:60]: print("FAIL " + b)
        print("DISC-001 CONTENT GUARD · REFUSED — %d problem(s)" % len(bad)); return 2
    print("DISC-001 CONTENT GUARD · OK — head, header and hero, gallery and explorer byte-identical, every text block, "
          "link, image and id, six chapters, one decision with both routes, indicative footprint drawing, balanced markup")
    return 0


if __name__ == "__main__":
    sys.exit(main())
