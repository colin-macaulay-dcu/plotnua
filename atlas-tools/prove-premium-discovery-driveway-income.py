#!/usr/bin/env python3
"""PLOTNUA · Driveway Income: Pass 2 editorial redesign content guard (3 Nov 2026).

Presentation and narrative order only. Against a pinned snapshot of the production page at
ce0f130 (atlas-tools/premium-discovery/driveway-income-base.json), so a shallow checkout suffices:

  H  the head (SEO metadata, preload), JSON-LD, the hero slider and everything after <main>
     (property check, related Discoveries, footer) are unchanged; the head may only gain the
     declared stylesheets and the hero only the class pn-hero-onetitle;
  C  inside <main>: every text block (paragraph, list item, heading, card cell, drawer) is present
     verbatim, the same number of times -- blocks may be re-sequenced into the founder's narrative (the outcome photograph moves inside <main>),
     never edited, added or dropped; links, photographs (file and alt text), ids and governance
     comments are the same multisets;
  O  the order rules the page's own governance comments require still hold (the bridge follows
     the revelation; the real-world proof follows the lift photograph and precedes the cautions;
     "Keep exploring" points down the page; the pathway follows the property questions);
  D  the only added words are the six chapter labels; drawings are aria-hidden and carry no words.

  python3 atlas-tools/prove-premium-discovery-hidden-cars.py
  python3 atlas-tools/prove-premium-discovery-hidden-cars.py --snapshot REF
"""
import hashlib, json, os, re, subprocess, sys
from collections import Counter
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-driveway-income.html"
BASE = os.path.join(ROOT, "atlas-tools", "premium-discovery", "driveway-income-base.json")
CHAPTERS = ["The overlooked asset", "The possibility", "The location question", "The practicalities", "The homeowner decision"]  # chapter 03 uses the page's own "The Opportunity" kicker
ALLOWED_HEAD = ['<link rel="stylesheet" href="assets/identity/pn-editorial.css?v=2">',
                '<link rel="stylesheet" href="assets/identity/pn-di-editorial.css?v=1">',
                '<link rel="stylesheet" href="assets/identity/pn-hero-mobile-heading.css?v=1">',
                '<script src="assets/identity/pn-editorial.js?v=1" defer></script>']
OUTCOME = 'assets/img/4a4a1e4b08edaada.jpg'   # the outcome photograph: moved from after </main> to chapter 02
INLINE = {"strong", "em", "b", "i", "sup", "sub", "abbr", "a"}
VOID = {"img", "br", "input", "source", "meta", "link", "hr", "wbr", "path", "rect", "circle"}


class Read(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []; self.hidden = 0; self.blocks = []; self.buf = ""; self.links = []; self.imgs = []
        self.ids = []; self.hidden_roots = []; self.hidden_text = []

    def flush(self):
        w = " ".join(self.buf.split())
        if w: self.blocks.append(w)
        self.buf = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"): self.ids.append(a["id"])
        if tag == "a": self.links.append(a.get("href"))
        if tag == "img": self.imgs.append([a.get("src"), a.get("alt")])
        if tag not in INLINE and not self.hidden: self.flush()
        if tag in VOID: return
        hid = a.get("aria-hidden") == "true"
        if hid and not self.hidden: self.hidden_roots.append(tag + "." + (a.get("class") or ""))
        self.stack.append((tag, hid))
        if hid: self.hidden += 1

    def handle_endtag(self, tag):
        if tag in VOID: return
        while self.stack:
            t, hid = self.stack.pop()
            if hid: self.hidden -= 1
            if t == tag: break
        if tag not in INLINE and not self.hidden: self.flush()

    def handle_data(self, d):
        if self.hidden:
            w = " ".join(d.split())
            if w: self.hidden_text.append(w)
            return
        self.buf += d


def outcome_block(html):
    i = html.index('<section class="imagine-photo reveal'); j = html.index("</section>", i) + len("</section>")
    return html[i:j]


def parts(html):
    s = html.index('<main class="article" id="pn-main">'); e = html.index("</main>") + len("</main>")
    head = html[:html.index("</head>")]
    for l in ALLOWED_HEAD: head = head.replace("\n" + l, "")
    pre = html[html.index("</head>"):s].replace(" pn-hero-onetitle", "")
    main, post = html[s:e], html[e:]
    if OUTCOME in post:            # the published page: the photograph follows </main>
        blk = outcome_block(post); post = post.replace(blk, "", 1); main = main + blk
    post = post.lstrip("\n")
    return head, pre, main, post


def h(x): return hashlib.sha256(x.encode("utf-8")).hexdigest()


def facts(html):
    head, pre, main, post = parts(html)
    r = Read(); r.feed(main); r.flush()
    return {"head": h(head), "pre_main": h(pre), "post_main": h(post),
            "jsonld": [h(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)],
            "blocks": r.blocks, "links": r.links, "imgs": r.imgs, "ids": r.ids,
            "comments": re.findall(r"<!--.*?-->", main, re.S), "hidden_roots": r.hidden_roots,
            "hidden_text": r.hidden_text, "main": main}


def main():
    if sys.argv[1:2] == ["--snapshot"]:
        html = subprocess.check_output(["git", "show", sys.argv[2] + ":" + PAGE], cwd=ROOT).decode("utf-8")
        f = facts(html)
        for k in ("hidden_roots", "hidden_text", "main"): f.pop(k)
        f["ref"] = sys.argv[2]
        json.dump(f, open(BASE, "w"), indent=1, ensure_ascii=False); print("base written from", sys.argv[2]); return
    base = json.load(open(BASE)); now = facts(open(os.path.join(ROOT, PAGE), encoding="utf-8").read())
    bad = []; ok = 0
    def check(name, cond, why=""):
        nonlocal ok
        if cond: ok += 1; print("  ok   " + name)
        else: bad.append(name); print("  FAIL " + name + (" · " + why if why else ""))
    check("H1 head (title, meta, canonical, Open Graph, preload) unchanged but for the declared stylesheets", now["head"] == base["head"])
    check("H2 structured data (JSON-LD) byte-identical", now["jsonld"] == base["jsonld"])
    check("H3 hero, slider and disclosure unchanged (the approved one-title class aside)", now["pre_main"] == base["pre_main"])
    check("H4 property check, related Discoveries and footer unchanged", now["post_main"] == base["post_main"])
    blocks = Counter(now["blocks"])
    for c in CHAPTERS:
        check("D1 chapter label '%s' added once" % c, blocks[c] == 1 and c not in base["blocks"])
        blocks[c] -= 1
    blocks = +blocks; want = Counter(base["blocks"])
    check("C1 every text block in <main> present verbatim, the same number of times (%d blocks)" % sum(want.values()),
          blocks == want, "missing %s · extra %s" % (list((want - blocks).elements())[:2], list((blocks - want).elements())[:2]))
    check("C2 links identical (same set, same counts)", Counter(now["links"]) == Counter(base["links"]))
    check("C3 photographs identical (file and alt text)", sorted(map(tuple, now["imgs"])) == sorted(map(tuple, base["imgs"])))
    check("C4 ids and anchors identical", sorted(now["ids"]) == sorted(base["ids"]))
    check("C5 governance comments carried over verbatim", Counter(now["comments"]) == Counter(base["comments"]))
    m = now["main"]
    pos = lambda x: m.index(x)
    check("O1 In Brief still opens <main>", pos('aria-label="In brief"') < pos('pe-chapter'))
    check("O2 the reported figures keep their caveat beside them (caveat before the figures, same section)",
          pos('These are reported examples, not guaranteed values.') < pos('About &euro;50 a week') < pos('&euro;13 a day, or &euro;65 a week')
          and m.rfind('<section', 0, pos('These are reported examples')) == m.rfind('<section', 0, pos('&euro;13 a day')))
    check("O3 'Before you start' (tax, insurance, planning) precedes the detailed drawers",
          pos('Before you start') < pos('How an arrangement works') and pos('Before you start') < pos('Planning, tax and insurance in detail'))
    check("O4 the outcome photograph and its caption moved whole into <main>", OUTCOME in m and 'The homeowner earns from the space.' in m)
    hidden_words = now["hidden_text"]
    roots = Counter(now["hidden_roots"])
    check("D2 drawings are aria-hidden and carry no words (chapter numerals 01-06 only)",
          hidden_words == ["01", "02", "03", "04", "05", "06"]
          and all(r in ("svg.di-bays", "svg.di-map", "svg.di-tick", "span.pe-chapter-n") for r in roots),
          repr(dict(roots)) + repr(hidden_words))
    check("D3 the demand drawer folds on phones only: native <details>, open in the markup", m.count('<details class="faq-item is-inline pe-fold di-demand" open>') == 1)
    print("DRIVEWAY INCOME EDITORIAL GUARD · %s — %d passed, %d failed" % ("OK" if not bad else "FAILED", ok, len(bad)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
