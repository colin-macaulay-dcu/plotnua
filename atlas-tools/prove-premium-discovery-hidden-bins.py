#!/usr/bin/env python3
"""PLOTNUA · The Hidden Bins: Pass 2 editorial redesign content guard.

Founder approval of the pilot, 3 Nov 2026: PRESENTATION ONLY. Every sentence, link,
image, id, governance comment, the head (SEO metadata, JSON-LD), the hero slider and the
property check stay exactly as published. The base is a pinned snapshot of the production
page at 202d292 (atlas-tools/premium-discovery/hidden-bins-base.json), so a shallow
checkout suffices.

Allowed, and nothing else:
  D1 two founder narrative labels in <main>: "The Possibility", "The Practicalities";
  D2 decorative drawings and a figure strip, every one aria-hidden: the three bins,
     the three step schematics, the Class 62 figures (each figure is stated in the
     sentence beneath it);
  D3 structural wrappers and classes inside <main>;
  D4 one page stylesheet and one small script in the head (pn-hb-editorial.css / .js; the
     script only opens and closes the nine question cards on phones), and the approved
     mobile heading: pn-hero-mobile-heading.css plus the class pn-hero-onetitle.
  D5 the nine practical questions are native <details> cards, open in the markup.

  python3 atlas-tools/prove-premium-discovery-hidden-bins.py            # prove
  python3 atlas-tools/prove-premium-discovery-hidden-bins.py --snapshot REF   # write the base (once)
"""
import hashlib, json, os, re, subprocess, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-hidden-bins.html"
BASE = os.path.join(ROOT, "atlas-tools", "premium-discovery", "hidden-bins-base.json")
LABELS = ["The Possibility", "The Practicalities"]
ALLOWED_LINKS = ['<link rel="stylesheet" href="assets/identity/pn-hb-editorial.css?v=2">',
                 '<script src="assets/identity/pn-hb-editorial.js?v=1" defer></script>',
                 '<link rel="stylesheet" href="assets/identity/pn-hero-mobile-heading.css?v=1">']
VOID = {"img", "br", "input", "source", "meta", "link", "hr", "wbr", "path", "rect", "circle"}


class Read(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []; self.hidden = 0; self.text = []; self.links = []; self.imgs = []
        self.ids = []; self.heads = []; self.hidden_roots = []; self.hidden_text = []; self.cur = None; self.buf = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"): self.ids.append(a["id"])
        if tag == "a": self.links.append(a.get("href"))
        if tag == "img": self.imgs.append((a.get("src"), a.get("alt")))
        if tag in VOID: return
        hid = a.get("aria-hidden") == "true"
        if hid and not self.hidden: self.hidden_roots.append((tag, a.get("class")))
        self.stack.append((tag, hid))
        if hid: self.hidden += 1
        if tag in ("h1", "h2", "h3", "h4"): self.cur = tag; self.buf = ""

    def handle_endtag(self, tag):
        if tag in VOID: return
        while self.stack:
            t, hid = self.stack.pop()
            if hid: self.hidden -= 1
            if t == tag: break
        if tag == self.cur:
            self.heads.append((tag, " ".join(self.buf.split()))); self.cur = None

    def handle_data(self, d):
        w = " ".join(d.split())
        if self.hidden:
            if w: self.hidden_text.append(w)
            return
        if w: self.text.append(w)
        if self.cur: self.buf += d


def parts(html):
    s = html.index('<main id="pn-main"'); e = html.index("</main>") + len("</main>")
    head = html[:html.index("</head>")]
    for l in ALLOWED_LINKS: head = head.replace("\n" + l, "")
    pre = html[html.index("</head>"):s].replace(" pn-hero-onetitle", "")
    return head, pre, html[s:e], html[e:]


def h(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()


def facts(html):
    head, pre, main, post = parts(html)
    r = Read(); r.feed(main)
    ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    return {"head": h(head), "pre_main": h(pre), "post_main": h(post), "jsonld": [h(x) for x in ld],
            "text": " ".join(r.text), "links": r.links, "imgs": r.imgs, "ids": r.ids, "headings": r.heads,
            "comments": re.findall(r"<!--.*?-->", main, re.S), "hidden_roots": r.hidden_roots,
            "hidden_text": " ".join(r.hidden_text)}


def main():
    if sys.argv[1:2] == ["--snapshot"]:
        html = subprocess.check_output(["git", "show", sys.argv[2] + ":" + PAGE], cwd=ROOT).decode("utf-8")
        f = facts(html); f.pop("hidden_roots"); f.pop("hidden_text")
        f["ref"] = sys.argv[2]
        os.makedirs(os.path.dirname(BASE), exist_ok=True)
        json.dump(f, open(BASE, "w"), indent=1, ensure_ascii=False); print("base written from", sys.argv[2]); return
    base = json.load(open(BASE)); now = facts(open(os.path.join(ROOT, PAGE), encoding="utf-8").read())
    bad = []; ok = 0
    def check(name, cond, why=""):
        nonlocal ok
        if cond: ok += 1; print("  ok   " + name)
        else: bad.append(name); print("  FAIL " + name + (" · " + why if why else ""))
    check("H1 head (title, meta, canonical, Open Graph) unchanged but for the declared stylesheet", now["head"] == base["head"])
    check("H2 structured data (JSON-LD) byte-identical", now["jsonld"] == base["jsonld"])
    check("H3 hero, slider and disclosure unchanged (the proposal class aside)", now["pre_main"] == base["pre_main"])
    check("H4 property check, related Discoveries and footer unchanged", now["post_main"] == base["post_main"])
    t = now["text"]
    for lab in LABELS:
        check("D1 founder label '%s' appears once" % lab, t.count(lab) == 1 and base["text"].count(lab) == 0)
        t = t.replace(lab + " ", "", 1)
    check("C1 every visible sentence in <main> identical and in the same order", t == base["text"],
          "first difference at character %d" % next((i for i, (a, b) in enumerate(zip(t, base["text"])) if a != b), min(len(t), len(base["text"]))))
    check("C2 links identical, in order", now["links"] == base["links"])
    check("C3 photographs identical (file and alt text), in order", [list(x) for x in now["imgs"]] == base["imgs"])
    check("C4 ids and anchors identical", now["ids"] == base["ids"])
    check("C5 headings identical", [list(x) for x in now["headings"]] == base["headings"])
    check("C6 governance comments carried over verbatim", now["comments"] == base["comments"])
    roots = [c for _, c in now["hidden_roots"]]
    want = ["hb-bins", "hb-glyph", "hb-glyph", "hb-glyph", "hb-figs"]
    check("D2 only the declared decorative additions are hidden from assistive technology", roots == want, repr(roots))
    FIGS = ("3.5 m\u00b2 maximum area 1.4 m maximum height 0.6 m setback from the front wall "
            "\u00bd no reduction of the open front garden by more than half")
    check("D2 hidden additions carry no words but the Class 62 figures already stated beneath them", now["hidden_text"] == FIGS, repr(now["hidden_text"][:120]))
    html = open(os.path.join(ROOT, PAGE), encoding="utf-8").read()
    qs = html[html.index('id="practical-questions"'):]; qs = qs[:qs.index("</section>")]
    check("D5 nine question cards, every one open in the markup (all answers on view without scripting)",
          qs.count('<details class="faq-item hb-qa" open>') == 9 and qs.count("<details") == 9)
    print("HIDDEN BINS EDITORIAL GUARD · %s — %d passed, %d failed" % ("OK" if not bad else "FAILED", ok, len(bad)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
