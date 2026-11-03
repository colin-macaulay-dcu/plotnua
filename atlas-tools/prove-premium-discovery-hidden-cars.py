#!/usr/bin/env python3
"""PLOTNUA · The Hidden Cars: Pass 2 editorial redesign content guard (3 Nov 2026).

Presentation and narrative order only. Against a pinned snapshot of the production page at
45eac1e (atlas-tools/premium-discovery/hidden-cars-base.json), so a shallow checkout suffices:

  H  the head (SEO metadata, preload), JSON-LD, the hero slider and everything after <main>
     (property check, related Discoveries, footer) are unchanged; the head may only gain the
     declared stylesheets and the hero only the class pn-hero-onetitle;
  C  inside <main>: every text block (paragraph, list item, heading, card cell, drawer) is present
     verbatim, the same number of times -- blocks may be re-sequenced into the founder's narrative,
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
PAGE = "discovery-hidden-cars.html"
BASE = os.path.join(ROOT, "atlas-tools", "premium-discovery", "hidden-cars-base.json")
CHAPTERS = ["The problem", "The possibility", "The revelation", "How it works", "Irish feasibility", "The homeowner decision"]
ALLOWED_HEAD = ['<link rel="stylesheet" href="assets/identity/pn-editorial.css?v=2">',
                '<link rel="stylesheet" href="assets/identity/pn-hc-editorial.css?v=2">',
                '<script src="assets/identity/pn-editorial.js?v=1" defer></script>',
                '<link rel="stylesheet" href="assets/identity/pn-hero-mobile-heading.css?v=1">']
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


def parts(html):
    s = html.index('<main id="pn-main"'); e = html.index("</main>") + len("</main>")
    head = html[:html.index("</head>")]
    for l in ALLOWED_HEAD: head = head.replace("\n" + l, "")
    pre = html[html.index("</head>"):s].replace(" pn-hero-onetitle", "")
    return head, pre, html[s:e], html[e:]


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
    pos = lambda s: m.index(s)
    check("O1 the bridge follows the four approaches and the real-world proof (the revelation has landed)",
          pos('Where the cars could go') < pos('class="pn-bridge') and pos('Real homes. Real systems.') < pos('class="pn-bridge'))
    check("O2 the real-world proof follows the lift photograph and precedes the cautions",
          pos('assets/img/9aa6c362d5486001.jpg') < pos('Real homes. Real systems.') < pos('<ul class="dq-qual">'))
    check("O3 'Keep exploring' points down the page", pos('href="#and-afterwards"') < pos('id="and-afterwards"'))
    check("O4 the order of work follows the property questions", pos('id="v2-could-your-property"') < pos('id="v2-pathway"'))
    check("O5 the property check link stays in the opening half (early entry kept)", pos('disc022-hidden-cars-check.html') < pos('id="v2-routes"'))
    # the page's own aria-hidden arrow in "Keep exploring" (unchanged) is the one hidden word that was there before
    hidden_words = [w for w in now["hidden_text"] if w != "\u2193"]
    roots = Counter(now["hidden_roots"]); roots["span."] -= 1; roots = +roots
    check("D2 drawings are aria-hidden and carry no words (chapter numerals 01-06 only)",
          hidden_words == ["01", "02", "03", "04", "05", "06"] and now["hidden_text"].count("\u2193") == 1
          and all(r in ("svg.hc-draw", "svg.hc-swapdraw", "span.pe-chapter-n", "span.pe-fold-icon") for r in roots),
          repr(dict(roots)) + repr(hidden_words))
    ap = m[m.index('hc-approaches'):]; ap = ap[:ap.index("</section>")]
    check("D3 the four approach notes fold on phones only: native <details>, open in the markup (all visible without scripting)",
          ap.count('<details class="pe-fold" open>') == 4 and ap.count("<details") == 4 and ap.count('<span class="dq-note">') == 4)
    print("HIDDEN CARS EDITORIAL GUARD · %s — %d passed, %d failed" % ("OK" if not bad else "FAILED", ok, len(bad)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
