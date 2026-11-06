#!/usr/bin/env python3
"""PLOTNUA · DISC-008 Living in the Garden: Phase 2 editorial redesign content guard (3 Nov 2026).

Written BEFORE the page was restructured, against a pinned snapshot of the production page
(atlas-tools/premium-discovery/living-garden-base.json, taken at 8398ab7, re-pinned to fd5b1b5 after The Mobile Pods release). The guarded region is
<main> plus the closing Journey panel (#discover-your-property).

  H  the head may only gain the declared stylesheets; everything from the closing panel's end to the
     end of the document (related Discoveries, footer, scripts) is unchanged;
  S  the Before/Possible hero slider (figure#gardenCompare) is unchanged: it starts at BEFORE
     (data-start="100"), carries two separate full-size images and its controls;
  C  every text block in the guarded region is present, the same number of times, except the declared
     removals (the duplicated Journey panels), the declared corrections and the declared additions;
  L  every link, image source and id in the guarded region survives (as a set), plus only the declared
     additions; both Atlas / My Plot routes and every inbound anchor still resolve;
  O  the six chapters run 01-06 in order; the supplier gallery and Maker Explorer sit in chapter 04;
     the decision (chapter 06) is the closing panel and carries both routes, A and B;
  F  route B is free, has no form, input or script, and promises no matching, budget fit, referral,
     commission or introduction; no placeholder ("To research", "TBC", "lorem") is published; the
     garden plan says it is illustrative and not to scale;
  D  tags balance; every <details> is native and collapsed.

  python3 atlas-tools/prove-premium-discovery-living-garden.py
  python3 atlas-tools/prove-premium-discovery-living-garden.py --snapshot REF
  python3 atlas-tools/prove-premium-discovery-living-garden.py --diff      (authoring aid)
  python3 atlas-tools/prove-premium-discovery-living-garden.py --faults    (every mutation must be caught)
"""
import html as H, json, os, re, subprocess, sys
from collections import Counter
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-living-in-the-garden.html"
BASE = os.path.join(ROOT, "atlas-tools", "premium-discovery", "living-garden-base.json")
MAIN = '<main id="pn-main">'
CLOSE_END = '<section class="related reveal">'
ALLOWED_HEAD = ['<link rel="stylesheet" href="assets/identity/pn-editorial.css?v=2">',
                '<link rel="stylesheet" href="assets/identity/pn-lg-editorial.css?v=1">']
ROUTES = ["your-plot.html?discovery=garden-room", "your-plot.html?discovery=residential"]
INBOUND = ["explore-makers", "maker-index", "planning-conditions", "discover-your-property", "suppliers", "sg-track",
           "the-same-building", "compare-garden-rooms", "maker-guides"]
CHAPTERS = ["The opportunity", "The problem", "The possibility", "What exists today", "The practicalities",
            "The homeowner decision"]
BLOCK = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "summary", "figcaption", "td", "th", "dt", "dd", "caption",
         "blockquote", "label", "button"}
VOID = {"img", "br", "input", "source", "meta", "link", "hr", "wbr", "path", "rect", "circle", "line", "polyline",
        "polygon", "ellipse", "use", "stop", "col", "area", "base", "embed", "param", "track"}

# ---- declared changes (filled in as the approved redesign was implemented) -------------------------------
# Removed: the duplicated upper Journey panel ("What are you considering?") and its continue link; the gallery's
# two-option card moves to chapter 06 (its copy is kept, except the corrected homework sentence below).
REMOVED = [
    # the upper Journey panel, a copy of the closing panel offered earlier in the page
    "What are you considering?",
    "A home Somebody will live there. The residential conditions apply.",
    "A room A garden office, studio, kids’ space, extra room, gym or other non-residential garden space.",
    "Nothing is bought or reserved here. This is an early property check, not planning permission.",
    # its "continue" link, which pointed past it
    "Not ready yet? Keep exploring ↓",
    # the gallery's two-option card: its "explore yourself" copy and both labels move to chapter 06 verbatim;
    # its homework sentence ("...options that match your preferences and budget") is retired, because the
    # Phase 2 brief rules out any matching promise, and its two Journey buttons duplicated the closing panel's
    "Tell us what you’re looking for. We’ll use our Atlas research to help you find options that match your preferences and budget.",
    "A garden room →", "A garden home →",
]
REMOVED_LINKS = ["#the-same-building", "#sg-track"]   # targets of the removed continue link and card; both ids remain
CORR = []
ADDED = []          # new text blocks (chapter labels, approved new copy); populated below from ADDED_FILE
ADDED_FILE = os.path.join(ROOT, "atlas-tools", "premium-discovery", "living-garden-added.json")
ADDED_LINKS = ["#explore-makers", "#discover-your-property", "#planning-conditions", "#maker-guides"]
ADDED_IDS = ["lg-ch01", "lg-ch02", "lg-ch03", "lg-ch04", "lg-ch05", "lg-ch06", "lg-plan-t", "lg-plan-d"]
ADDED_IMGS = []     # only already-approved assets may be added; declared in ADDED_FILE
PLACEHOLDER = re.compile(r"\bto research\b|\bTBC\b|\bTBD\b|lorem|placeholder|coming soon", re.I)
PROMISE = re.compile(r"\bmatch(?:es|ed|ing)?\b|\bbudget\b|\bcommission|\breferr|\bintroduc|\bpartner|\bguarantee|\bbest\b", re.I)


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
    a = src.index(MAIN)
    z = src.index(CLOSE_END)
    return src[:src.index("</head>")], src[a:z], src[z:]


def parse(region):
    p = Blocks(); p.feed(region); p.close()
    return p


def snapshot(ref):
    src = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (ref, PAGE)], capture_output=True, text=True, check=True).stdout
    head, body, post = regions(src)
    p = parse(body)
    hero = re.search(r'<figure class="pn-compare pn-compare--hero" id="gardenCompare".*?</figure>', src, re.S).group(0)
    d = {"ref": ref, "head": head, "post": post, "hero": hero, "blocks": p.out, "links": sorted(set(p.links)),
         "imgs": sorted(set(p.imgs)), "ids": sorted(set(p.ids))}
    json.dump(d, open(BASE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("snapshot %s: %d blocks, %d links, %d images, %d ids" % (ref, len(p.out), len(d["links"]), len(d["imgs"]), len(d["ids"])))


def load_added():
    """Declared additions. "supplierCards" (4 Nov 2026, Gardenhouse24): a supplier gallery card added
    after the snapshot is declared here, card by card: its exact text blocks, image and links. Each
    card's image and links must also pass the supplier gallery guard and the Image Rights Gate."""
    if os.path.exists(ADDED_FILE):
        x = json.load(open(ADDED_FILE, encoding="utf-8"))
        blocks, imgs = list(x.get("blocks", [])), list(x.get("imgs", []))
        # "makerAdditions" (6 Nov 2026, Stage 3B East Coast Carpentry): a maker newly published
        # in the Maker Explorer adds exactly one A-Z index entry (its text block and its anchor
        # link), declared here with the founder approval that published it. No image, no card.
        for c in x.get("supplierCards", []) + x.get("showcaseReferences", []) + x.get("makerAdditions", []):
            blocks += c["blocks"]; imgs += c.get("imgs", [])
        return blocks, imgs
    return [], []


def added_links():
    if os.path.exists(ADDED_FILE):
        x = json.load(open(ADDED_FILE, encoding="utf-8"))
        # "showcaseReferences" (4 Nov 2026, Elm Landscaping): a text-only reference to a maker's
        # PlotNua showcase, declared with its exact blocks and internal links. No image, no card.
        return [l for c in x.get("supplierCards", []) + x.get("showcaseReferences", []) + x.get("makerAdditions", [])
                for l in c["links"]]
    return []


def check(src, base):
    bad = []
    added, added_imgs = load_added()
    try:
        head, body, post = regions(src)
    except ValueError:
        return ["H the guarded region markers are missing"]
    # H
    bh = base["head"]
    for l in ALLOWED_HEAD:
        head = head.replace(l + "\n", "").replace(l, "")
    if re.sub(r"\s+", "", head) != re.sub(r"\s+", "", bh):
        bad.append("H the head changed beyond the declared stylesheets")
    if post != base["post"]:
        bad.append("H the page after the closing Journey panel changed")
    # S
    m = re.search(r'<figure class="pn-compare pn-compare--hero" id="gardenCompare".*?</figure>', src, re.S)
    if not m or m.group(0) != base["hero"]:
        bad.append("S the Before/Possible hero slider changed")
    elif 'data-start="100"' not in m.group(0) or len(re.findall(r"<img\b", m.group(0))) < 2:
        bad.append("S the slider must start at BEFORE with two images")
    # C
    p = parse(body)
    have, want = Counter(p.out), Counter(base["blocks"])
    removed = list(REMOVED)
    if os.path.exists(ADDED_FILE):
        # Declared removals (4 Nov 2026, founder approval 'DISC-008 homeowner experience improvement'):
        # the three comparison introductions consolidated into one; each removed block named exactly.
        removed += json.load(open(ADDED_FILE, encoding="utf-8")).get("removedBlocks", [])
    for r in removed:
        want[norm(r)] -= 1
    corr = list(CORR)
    if os.path.exists(ADDED_FILE):
        # Declared text-block corrections (4 Nov 2026, Powersheds Irish availability): an exact
        # old -> new pair for a block that a targeted Atlas correction rewrote.
        corr += [(c.get("why", ""), c["from"], c["to"])
                 for c in json.load(open(ADDED_FILE, encoding="utf-8")).get("blockCorrections", [])]
    for _c, old, new in corr:
        want[norm(old)] -= 1; want[norm(new)] += 1
    for a in added:
        want[norm(a)] += 1
    want = +want
    missing = want - have
    extra = have - want
    for t, n in missing.items():
        bad.append("C missing text block (x%d): %s" % (n, t[:110]))
    for t, n in extra.items():
        bad.append("C undeclared text block (x%d): %s" % (n, t[:110]))
    # L
    links, imgs, ids = set(p.links), set(p.imgs), set(p.ids)
    for l in base["links"]:
        if l not in links and l not in REMOVED_LINKS: bad.append("L link lost: " + l)
    for l in links - set(base["links"]) - set(ADDED_LINKS) - set(added_links()):
        bad.append("L undeclared link: " + l)
    for i in base["imgs"]:
        if i not in imgs: bad.append("L image lost: " + i)
    for i in imgs - set(base["imgs"]) - set(added_imgs):
        bad.append("L undeclared image: " + i)
    rem_ids = json.load(open(ADDED_FILE, encoding="utf-8")).get("removedIds", []) if os.path.exists(ADDED_FILE) else []
    for i in base["ids"]:
        if i not in ids and i not in rem_ids: bad.append("L id lost: " + i)
    ref_ids = []
    if os.path.exists(ADDED_FILE):
        ref_ids = [i for c in json.load(open(ADDED_FILE, encoding="utf-8")).get("showcaseReferences", []) for i in c.get("ids", [])]
    for i in ids - set(base["ids"]) - set(ADDED_IDS) - set(ref_ids):
        bad.append("L undeclared id: " + i)
    for r in ROUTES:
        if 'href="%s"' % r not in body: bad.append("L Atlas / My Plot route missing: " + r)
    for a in INBOUND:
        if 'id="%s"' % a not in src: bad.append("L inbound anchor missing: #" + a)
    # O
    pos = []
    for n, name in enumerate(CHAPTERS, 1):
        i = body.find('id="lg-ch%02d"' % n)
        if i < 0: bad.append("O chapter %02d (%s) missing" % (n, name)); pos.append(-1); continue
        if name.lower() not in norm(re.sub(r"<[^>]+>", " ", body[i:i + 900])).lower():
            bad.append("O chapter %02d is not labelled %s" % (n, name))
        pos.append(i)
    if -1 not in pos and pos != sorted(pos):
        bad.append("O the six chapters are out of order")
    if -1 not in pos:
        for anchor in ('id="suppliers"', 'id="explore-makers"'):
            i = body.find(anchor)
            if not (pos[3] < i < pos[4]): bad.append("O %s must sit in chapter 04" % anchor)
        dec = body.find('id="discover-your-property"')
        if not (body.find("</main>") < dec < pos[5] and pos[5] - dec < 4000):
            bad.append("O the decision must be chapter 06, in the closing panel")
    dec = body[body.find('id="discover-your-property"'):] if 'id="discover-your-property"' in body else ""
    for k in ("Explore yourself", "Let PlotNua do the homework"):
        if k not in dec: bad.append("O route missing from the decision: " + k)
    # F
    if dec:
        if re.search(r"<form\b|<input\b|<textarea\b|<select\b|<script\b|workers\.dev|fetch\s*\(", dec, re.I):
            bad.append("F the decision carries a form, input or script")
        if "Free for homeowners" not in norm(re.sub(r"<[^>]+>", " ", dec)):
            bad.append("F route B must say it is free for homeowners")
        vis = norm(re.sub(r"<!--.*?-->|<[^>]+>", " ", dec, flags=re.S))
        if PROMISE.search(vis):
            bad.append("F the decision makes a commercial promise: " + PROMISE.search(vis).group(0))
    visible = norm(re.sub(r"<!--.*?-->|<script.*?</script>|<style.*?</style>|<[^>]+>", " ", body, flags=re.S))
    if PLACEHOLDER.search(visible):
        bad.append("F placeholder text published: " + PLACEHOLDER.search(visible).group(0))
    plan = re.search(r"<figure class=\"[^\"]*\blg-plan\b.*?</figure>", body, re.S)
    if not plan:
        bad.append("F the garden plan is missing")
    elif not re.search(r"illustrative", plan.group(0), re.I) or not re.search(r"not to scale", plan.group(0), re.I):
        bad.append("F the garden plan must say it is illustrative and not to scale")
    # D
    if p.bad or p.stack:
        bad.append("D tags do not balance (%d mismatches, %d open)" % (p.bad, len(p.stack)))
    for d in p.details:
        if "open" in d: bad.append("D a <details> is open by default")
    return bad


FAULTS = [
    ("hero start moved to POSSIBLE", lambda s: s.replace('data-start="100"', 'data-start="0"', 1), "S"),
    ("a planning fact edited", lambda s: s.replace("The planning minimum is 0.6&nbsp;m", "The planning minimum is 0.5&nbsp;m", 1), "C"),
    # 6 Nov 2026: the figure follows the cost evidence (245 -> 240); the fault now edits whatever it is.
    ("a price figure edited", lambda s: re.sub(r"(\d+)( garden-room products with a euro price)",
                                                lambda m: str(int(m.group(1)) + 1) + m.group(2), s, count=1), "C"),
    ("a price block removed", lambda s: re.sub(r"<li><span class=\"dq-fact\">\d+ do not publish.*?</li>", "", s, count=1, flags=re.S), "C"),
    ("a notice dropped", lambda s: s.replace("Separately, tell Building Control.", "", 1), "C"),
    ("an Atlas route removed", lambda s: s.replace('href="your-plot.html?discovery=residential"', 'href="your-plot.html"'), "L"),
    ("the explorer anchor renamed", lambda s: s.replace('id="explore-makers"', 'id="makers"', 1), "L"),
    ("a supplier link changed", lambda s: s.replace('href="https://yardbox.co.uk/"', 'href="https://example.com/"', 1), "L"),
    ("chapters reordered", lambda s: s.replace('id="lg-ch02"', 'id="lg-chX"', 1).replace('id="lg-ch05"', 'id="lg-ch02"', 1).replace('id="lg-chX"', 'id="lg-ch05"', 1), "O"),
    ("route A dropped", lambda s: s.replace("Explore yourself", "Explore", 99), "O"),
    ("free statement removed", lambda s: s.replace("Free for homeowners", "For homeowners", 99), "F"),
    ("a form added to the decision", lambda s: s.replace('id="discover-your-property">', 'id="discover-your-property"><form></form>', 1), "F"),
    ("a matching promise added", lambda s: s.replace("<p class=\"lg-free\">Free for homeowners.", "<p class=\"lg-free\">Free for homeowners. We match you with the best maker.", 1), "F"),
    ("placeholder published", lambda s: s.replace("</main>", "<p>To research</p></main>", 1), "F"),
    ("plan scale label removed", lambda s: s.replace("not to scale", "", 99).replace("Not to scale", "", 99), "F"),
    ("details opened", lambda s: s.replace('<details class="faq-item">', '<details class="faq-item" open>', 1), "D"),
    ("footer edited", lambda s: s.replace("Related Discoveries", "Related", 1), "H"),
    ("undeclared stylesheet", lambda s: s.replace("</head>", '<link rel="stylesheet" href="x.css">\n</head>', 1), "H"),
    ("an undeclared supplier card is added", lambda s: s.replace('<h3 class="pn-sg-name">Gardenhouse24 Ireland</h3>', '<h3 class="pn-sg-name">Invented Garden Co</h3>', 1), "C"),
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
        print("DISC-008 GUARD FAULTS · %s — %d/%d caught" % ("OK" if not missed else "FAILED", len(FAULTS) - missed, len(FAULTS)))
        return 1 if missed else 0
    bad = check(src, base)
    if "--diff" in sys.argv:
        for b in bad: print(b)
        return 0
    if bad:
        for b in bad[:60]: print("FAIL " + b)
        print("DISC-008 CONTENT GUARD · REFUSED — %d problem(s)" % len(bad)); return 2
    print("DISC-008 CONTENT GUARD · OK — head, hero slider, every text block, link, image and id, six chapters, "
          "one decision with both routes, no placeholders, illustrative plan, balanced markup")
    return 0


if __name__ == "__main__":
    sys.exit(main())
