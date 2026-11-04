#!/usr/bin/env python3
"""PLOTNUA · DISC-005 Home Exchange: six-chapter editorial redesign content guard (4 Nov 2026).

Written BEFORE the page was restructured, against a pinned snapshot of the production page
(atlas-tools/premium-discovery/home-exchange-base.json, taken at f4b648e). The guarded region is
<main> plus the two photographs and the closing panel (#discover-your-property), which becomes chapter 06. Everything from </head> to <main> (header, hero) is pinned.

  H  the head may only gain the declared stylesheets; everything from the closing panel's end to the
     end of the document (related Discoveries, footer, scripts) is unchanged;
  S  the Before/Possible hero slider (figure#exchangeCompare (HOME / AWAY labels)) is unchanged: it starts at BEFORE
     (data-start="100"), carries two separate full-size images and its controls;
  C  every text block in the guarded region is present, the same number of times, except the declared
     declared changes and additions; the text of every collapsible answer (.faq-a) survives verbatim;
  L  every link, image source and id in the guarded region survives (as a set), plus only the declared
     additions; both Atlas / My Plot routes and every inbound anchor still resolve;
  O  the six chapters run 01-06 in order; the qualification and what a home unlocks sit in 02, the three
     routes in 03, the before-you-start checks in 04, the platform note and the Property Check in 05; the
     decision (06) is the closing panel and carries both routes, A and B;
  F  route B is free, has no form, input or script, and promises no matching, budget fit, referral,
     commission, introduction, booking or earnings; no placeholder; no promise of an exchange, cover or saving;
  D  tags balance; every <details> is native and collapsed.

  python3 atlas-tools/prove-premium-discovery-home-exchange.py
  python3 atlas-tools/prove-premium-discovery-home-exchange.py --snapshot REF
  python3 atlas-tools/prove-premium-discovery-home-exchange.py --diff      (authoring aid)
  python3 atlas-tools/prove-premium-discovery-home-exchange.py --faults    (every mutation must be caught)
"""
import html as H, json, os, re, subprocess, sys
from collections import Counter
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-home-exchange.html"
BASE = os.path.join(ROOT, "atlas-tools", "premium-discovery", "home-exchange-base.json")
MAIN = '<main class="article" id="pn-main">'
CLOSE_END = '<section class="related reveal">'
ALLOWED_HEAD = ['<link rel="stylesheet" href="assets/identity/pn-hx-editorial.css?v=1">',
                '<link rel="stylesheet" href="assets/components/pn-two-route.css?v=1">']
ROUTES = ["https://wa.me/353834036695", "your-plot.html?myplot=1"]
INBOUND = ["exchangeCompare", "discover-your-property"]
CHAPTERS = ["Your home could take you places", "Home / Away", "Different ways to exchange",
            "How does it work?", "Finding your next exchange", "Two ways to take the next step"]
IN_CHAPTER = {2: ["hx-unlocks"], 3: ["hx-routes"], 4: ["hx-before"], 5: ["hx-platform", "hx-check"]}
DEC_ID = "discover-your-property"
BLOCK = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "summary", "figcaption", "td", "th", "dt", "dd", "caption",
         "blockquote", "label", "button"}
VOID = {"img", "br", "input", "source", "meta", "link", "hr", "wbr", "path", "rect", "circle", "line", "polyline",
        "polygon", "ellipse", "use", "stop", "col", "area", "base", "embed", "param", "track"}

# ---- declared changes ----------------------------------------------------------------------------------------
# The single article section is split across the chapters and nothing is removed. "What a platform does, and what
# it does not" becomes a visible block in chapter 05 instead of a collapsed answer (its heading was counted twice,
# as <summary> and <h3>; it is now counted once). The Property Check (headline, text and button) moves from the
# closing panel into chapter 05, unchanged; the panel becomes chapter 06 and keeps its exits and independence line.
REMOVED = ["What a platform does, and what it does not"]
REMOVED_LINKS = []
CORR = []
ADDED = []
ADDED_FILE = os.path.join(ROOT, "atlas-tools", "premium-discovery", "home-exchange-added.json")
ADDED_LINKS = ["#hx-unlocks", "#hx-routes", "#hx-before", "#hx-platform", "#hx-check", "#hx-journey",
               "your-plot.html?myplot=1", "https://wa.me/353834036695"]
ADDED_IDS = ["lg-ch01", "lg-ch02", "lg-ch03", "lg-ch04", "lg-ch05", "lg-ch06", "hx-unlocks", "hx-routes", "hx-before",
             "hx-platform", "hx-check", "hx-journey", "hx-routes-h"]
ADDED_IMGS = []
PLACEHOLDER = re.compile(r"\bto research\b|\bTBC\b|\bTBD\b|lorem|placeholder|coming soon", re.I)
EXEMPT = re.compile(r"\bguarantee[ds]? (?:a |an |your )?(?:exchange|swap|cover|saving|savings|safety)\b|\byou will (?:save|find an exchange|be covered|be matched)\b|\b(?:is|are) (?:fully )?covered by (?:the platform|PlotNua)\b|\bsave (?:up to )?(?:&euro;|\u20ac)", re.I)
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


def faqa(region):
    return [norm(re.sub(r"<[^>]+>", " ", x)) for x in re.findall(r'<div class="faq-a">(.*?)</div>', region, re.S)]


def pre_main(src):
    return src[src.index("</head>"):src.index(MAIN)]


def parse(region):
    p = Blocks(); p.feed(region); p.close()
    return p


def snapshot(ref):
    src = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (ref, PAGE)], capture_output=True, text=True, check=True).stdout
    head, body, post = regions(src)
    p = parse(body)
    hero = re.search(r'<figure class="pn-compare pn-compare--hero" id="exchangeCompare".*?</figure>', src, re.S).group(0)
    d = {"ref": ref, "head": head, "post": post, "hero": hero, "pre": pre_main(src), "faqa": faqa(body), "blocks": p.out, "links": sorted(set(p.links)),
         "imgs": sorted(set(p.imgs)), "ids": sorted(set(p.ids))}
    json.dump(d, open(BASE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("snapshot %s: %d blocks, %d links, %d images, %d ids" % (ref, len(p.out), len(d["links"]), len(d["imgs"]), len(d["ids"])))


def load_added():
    if os.path.exists(ADDED_FILE):
        x = json.load(open(ADDED_FILE, encoding="utf-8"))
        return x.get("blocks", []), x.get("imgs", [])
    return [], []


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
    if pre_main(src) != base["pre"]:
        bad.append("H the header or hero region before <main> changed")
    # S
    m = re.search(r'<figure class="pn-compare pn-compare--hero" id="exchangeCompare".*?</figure>', src, re.S)
    if not m or m.group(0) != base["hero"]:
        bad.append("S the Before/Possible hero slider changed")
    elif 'data-start="100"' not in m.group(0) or len(re.findall(r"<img\b", m.group(0))) < 2:
        bad.append("S the slider must start at BEFORE with two images")
    # C
    p = parse(body)
    have, want = Counter(p.out), Counter(base["blocks"])
    for r in REMOVED:
        want[norm(r)] -= 1
    for _c, old, new in CORR:
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
    flat = norm(re.sub(r"<[^>]+>", " ", body))
    for t in base.get("faqa", []):
        if t not in flat: bad.append("C an answer's text changed or was lost: " + t[:90])
    if len(faqa(body)) < len(base.get("faqa", [])) - 1:
        bad.append("C an answer block was lost")
    # L
    links, imgs, ids = set(p.links), set(p.imgs), set(p.ids)
    for l in base["links"]:
        if l not in links and l not in REMOVED_LINKS: bad.append("L link lost: " + l)
    for l in links - set(base["links"]) - set(ADDED_LINKS):
        bad.append("L undeclared link: " + l)
    for i in base["imgs"]:
        if i not in imgs: bad.append("L image lost: " + i)
    for i in imgs - set(base["imgs"]) - set(added_imgs):
        bad.append("L undeclared image: " + i)
    for i in base["ids"]:
        if i not in ids: bad.append("L id lost: " + i)
    for i in ids - set(base["ids"]) - set(ADDED_IDS):
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
        for ch, anchors in IN_CHAPTER.items():
            for anchor in anchors:
                i = body.find('id="%s"' % anchor)
                if not (pos[ch - 1] < i < pos[ch]): bad.append("O #%s must sit in chapter %02d" % (anchor, ch))
        dec = body.find('id="%s"' % DEC_ID)
        if not (body.find("</main>") < dec < pos[5] and pos[5] - dec < 4000):
            bad.append("O the decision must be chapter 06, in the closing panel")
    dec = body[body.find('id="%s"' % DEC_ID):] if 'id="%s"' % DEC_ID in body else ""
    for k in ("Explore the possibilities yourself", "Let PlotNua do the homework"):
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
    if EXEMPT.search(visible):
        bad.append("F an exchange, cover or saving is promised: " + EXEMPT.search(visible).group(0))
    # D
    if p.bad or p.stack:
        bad.append("D tags do not balance (%d mismatches, %d open)" % (p.bad, len(p.stack)))
    for d in p.details:
        if "open" in d: bad.append("D a <details> is open by default")
    return bad


FAULTS = [
    ("hero start moved", lambda s: s.replace('data-start="100"', 'data-start="0"', 1), "S"),
    ("HOME label changed", lambda s: s.replace('data-label-before="Home"', 'data-label-before="Before"', 1), "H"),
    ("a qualification edited", lambda s: s.replace("How many people it can sleep", "How many people it sleeps", 1), "C"),
    ("an answer edited", lambda s: s.replace("You may never meet them.", "You will never meet them.", 1), "C"),
    ("a photograph dropped", lambda s: s.replace('src="assets/img/991355de2bd66bcc.jpg"', 'src="assets/img/x.jpg"', 1), "L"),
    ("Property Check link dropped", lambda s: s.replace('href="disc005-home-exchange.html"', 'href="discoveries.html"', 1), "L"),
    ("WhatsApp route removed", lambda s: s.replace('href="https://wa.me/353834036695" data-tr-route', 'href="contact.html" data-tr-route'), "L"),
    ("chapters reordered", lambda s: s.replace('id="lg-ch02"', 'id="lg-chX"', 1).replace('id="lg-ch05"', 'id="lg-ch02"', 1).replace('id="lg-chX"', 'id="lg-ch05"', 1), "O"),
    ("route A dropped", lambda s: s.replace("Explore the possibilities yourself", "Explore", 99), "O"),
    ("free statement removed", lambda s: s.replace("Free for homeowners", "For homeowners", 99), "F"),
    ("a form added to the decision", lambda s: s.replace('id="discover-your-property"', 'id="discover-your-property"><form></form', 1), "F"),
    ("a matching promise added", lambda s: s.replace("Free for homeowners.", "Free for homeowners. We match you with the best platform.", 1), "F"),
    ("a cover promise added", lambda s: s.replace("</main>", "<p>We guarantee cover for every exchange.</p></main>", 1), "F"),
    ("placeholder published", lambda s: s.replace("</main>", "<p>To research</p></main>", 1), "F"),
    ("details opened", lambda s: s.replace('<details class="faq-item is-inline">', '<details class="faq-item is-inline" open>', 1), "D"),
    ("footer edited", lambda s: s.replace("Related Discoveries", "Related", 1), "H"),
    ("undeclared stylesheet", lambda s: s.replace("</head>", '<link rel="stylesheet" href="x.css">\n</head>', 1), "H"),
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
        print("DISC-005 GUARD FAULTS · %s — %d/%d caught" % ("OK" if not missed else "FAILED", len(FAULTS) - missed, len(FAULTS)))
        return 1 if missed else 0
    bad = check(src, base)
    if "--diff" in sys.argv:
        for b in bad: print(b)
        return 0
    if bad:
        for b in bad[:60]: print("FAIL " + b)
        print("DISC-005 CONTENT GUARD · REFUSED — %d problem(s)" % len(bad)); return 2
    print("DISC-005 CONTENT GUARD · OK — head, hero slider, every text block, link, image and id, six chapters, "
          "one decision with both routes, no placeholders, every answer verbatim, no exchange, cover or saving promised, balanced markup")
    return 0


if __name__ == "__main__":
    sys.exit(main())
