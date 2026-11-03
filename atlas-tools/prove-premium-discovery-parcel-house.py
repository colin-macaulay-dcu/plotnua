#!/usr/bin/env python3
"""PLOTNUA · The Neighbourhood Parcel House: Pass 2 editorial redesign content guard (3 Nov 2026).

Against a pinned snapshot of the production page (atlas-tools/premium-discovery/parcel-house-base.json):

  H  the head may only gain the declared stylesheets and deferred script; the hero only the class
     pn-hero-onetitle; after <main> only the property-check button label changes, to the founder's
     "Could my home work?" (the check itself asks "Could your door take a parcel for the road?");
  C  inside <main> every text block is present verbatim, the same number of times, except the ONE
     declared rewording (the boundary sentence "Being paid to do it cannot.", which read as a
     prohibition) and the declared additions: four chapter labels, the founder's opening line, and
     the favour / paid-network distinction. Links, photographs, ids and governance comments are the
     same multisets (one declared comment added);
  O  the order the narrative needs holds, and nothing presents a paid arrangement as available;
  D  drawings are aria-hidden and wordless; the three drawers are native and collapsed.

  python3 atlas-tools/prove-premium-discovery-parcel-house.py
  python3 atlas-tools/prove-premium-discovery-parcel-house.py --snapshot REF
"""
import hashlib, json, os, re, subprocess, sys
from collections import Counter
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-neighbourhood-parcel-house.html"
BASE = os.path.join(ROOT, "atlas-tools", "premium-discovery", "parcel-house-base.json")
MAIN = '<main id="pn-main">'
CHAPTERS = ["The neighbourhood problem", "The possibility", "The practicalities", "The homeowner decision"]  # 01 and 04 reuse the page's own kickers
LEAD = "What if one ordinary house on every street could make parcel deliveries easier for the entire neighbourhood?"
REWORD = {"Everything above can be done in Ireland today, as a favour between neighbours. Being paid to do it cannot.":
          "Everything above can be done in Ireland today, as a favour between neighbours. An organised, paid network of private homes is a different thing, and we could not find one here."}
TWO = ["Between neighbours", "A favour, arranged privately.",
       "You decide who, when and what you will take. This is the arrangement everything on this page describes.",
       "As a paid network", "Payment does not make it wrong. It makes it a different decision.",
       "Once a home is paid to receive parcels \u2014 by a retailer, a carrier or a network \u2014 further questions follow: insurance, planning, tax, data protection, the contract with whoever is paying, and who is liable when something goes missing or is damaged. Each would need to be checked properly before any money changed hands."]
ALLOWED_HEAD = ['<link rel="stylesheet" href="assets/identity/pn-editorial.css?v=2">',
                '<link rel="stylesheet" href="assets/identity/pn-np-editorial.css?v=1">',
                '<link rel="stylesheet" href="assets/identity/pn-hero-mobile-heading.css?v=1">',
                '<script src="assets/identity/pn-editorial.js?v=1" defer></script>']
CTA_OLD = '<a class="btn-primary" href="disc027-neighbourhood-parcel-house.html">Start the property check</a>'
CTA_NEW = '<a class="btn-primary" href="disc027-neighbourhood-parcel-house.html">Could my home work?</a>'
PHOTO = "assets/img/e0d578046cd29bda.jpg"
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
    s = html.index(MAIN); e = html.index("</main>") + len("</main>")
    head = html[:html.index("</head>")]
    for l in ALLOWED_HEAD: head = head.replace("\n" + l, "")
    pre = html[html.index("</head>"):s].replace(" pn-hero-onetitle", "")
    return head, pre, html[s:e], html[e:].replace(CTA_NEW, CTA_OLD)


def h(x): return hashlib.sha256(x.encode("utf-8")).hexdigest()


def facts(html):
    head, pre, main, post = parts(html)
    r = Read(); r.feed(main); r.flush()
    return {"head": h(head), "pre_main": h(pre), "post_main": h(post),
            "jsonld": [h(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)],
            "blocks": r.blocks, "links": r.links, "imgs": r.imgs, "ids": r.ids,
            "comments": re.findall(r"<!--.*?-->", main, re.S), "hidden_roots": r.hidden_roots,
            "hidden_text": r.hidden_text, "main": main, "post_raw": html[e_(html):]}


def e_(html): return html.index("</main>") + len("</main>")


def main():
    if sys.argv[1:2] == ["--snapshot"]:
        html = subprocess.check_output(["git", "show", sys.argv[2] + ":" + PAGE], cwd=ROOT).decode("utf-8")
        f = facts(html)
        for k in ("hidden_roots", "hidden_text", "main", "post_raw"): f.pop(k)
        f["ref"] = sys.argv[2]
        json.dump(f, open(BASE, "w"), indent=1, ensure_ascii=False); print("base written from", sys.argv[2]); return
    base = json.load(open(BASE)); now = facts(open(os.path.join(ROOT, PAGE), encoding="utf-8").read())
    bad = []; ok = 0
    def check(name, cond, why=""):
        nonlocal ok
        if cond: ok += 1; print("  ok   " + name)
        else: bad.append(name); print("  FAIL " + name + (" · " + why if why else ""))
    check("H1 head (title, meta, canonical, Open Graph) unchanged but for the declared stylesheets and script", now["head"] == base["head"])
    check("H2 structured data unchanged", now["jsonld"] == base["jsonld"])
    check("H3 hero, Before/Possible slider and disclosure unchanged (the approved one-title class aside)", now["pre_main"] == base["pre_main"])
    check("H4 property check, related Discoveries and footer unchanged but for the declared button label",
          now["post_main"] == base["post_main"] and now["post_raw"].count(CTA_NEW) == 1)
    blocks = Counter(now["blocks"])
    for c in CHAPTERS:
        check("D1 chapter label '%s' added once" % c, blocks[c] == 1 and c not in base["blocks"]); blocks[c] -= 1
    check("D1 the founder's opening line added once", blocks[LEAD] == 1); blocks[LEAD] -= 1
    for t in TWO:
        check("D1 favour / paid-network block '%s...'" % t[:28], blocks[t] == 1); blocks[t] -= 1
    want = Counter(base["blocks"])
    for old, new in REWORD.items():
        check("R1 the one declared rewording is in place (boundary sentence no longer reads as a prohibition)",
              want[old] == 1 and blocks[new] == 1 and blocks[old] == 0)
        blocks[new] -= 1; want[old] -= 1
    blocks = +blocks; want = +want
    check("C1 every other text block in <main> present verbatim, the same number of times (%d blocks)" % sum(want.values()),
          blocks == want, "missing %s · extra %s" % (list((want - blocks).elements())[:2], list((blocks - want).elements())[:2]))
    check("C2 links identical (same set, same counts)", Counter(now["links"]) == Counter(base["links"]))
    check("C3 photographs identical (file and alt text)", sorted(map(tuple, now["imgs"])) == sorted(map(tuple, base["imgs"])))
    check("C4 ids and anchors identical", sorted(now["ids"]) == sorted(base["ids"]))
    extra = Counter(now["comments"]) - Counter(base["comments"])
    check("C5 governance comments carried over verbatim (one declared comment added)",
          not (Counter(base["comments"]) - Counter(now["comments"])) and sum(extra.values()) == 1
          and "FOUNDER REFINEMENT (3 Nov 2026)" in next(iter(extra)))
    m = now["main"]; pos = lambda x: m.index(x)
    check("O1 the opening line leads chapter 01, before its question", pos(LEAD) < pos("Could your home become your street"))
    check("O2 the demand figures (chapter 02) precede the possibility; the handover photograph sits beside How it would work",
          pos("140.73 million") < pos(PHOTO) < pos("How it would work") < pos("Not here yet."))
    check("O3 the boundary comes before the paid-network questions, which come before the practicalities",
          pos("Not here yet.") < pos("As a paid network") < pos("Who is responsible") < pos("Responsibility, insurance and being paid, in detail"))
    check("O4 the homeowner decision (place and presence) closes the article, just before the property check",
          pos("Could this work at your house?") > pos("What it changes day to day"))
    check("O5 nothing in <main> says a paid arrangement is available or that PlotNua runs one",
          "PlotNua does not arrange this" in m and not re.search(r"PlotNua (runs|operates|offers) (a|the) (parcel|collection) network", m))
    roots = Counter(now["hidden_roots"])
    check("D2 drawings are aria-hidden and carry no words (chapter numerals 01-06 only)",
          now["hidden_text"] == ["01", "02", "03", "04", "05", "06"]
          and all(r in ("svg.np-street", "svg.np-stacks", "svg.np-cond", "span.pe-chapter-n") for r in roots),
          repr(dict(roots)) + repr(now["hidden_text"]))
    check("D3 the three drawers are native <details>, collapsed in the markup, each with the standard marker",
          m.count('<details class="faq-item is-inline">') == 3 and "<details class=\"faq-item is-inline\" open" not in m
          and m.count('<span class="icon"></span>') == 3)
    print("PARCEL HOUSE EDITORIAL GUARD · %s — %d passed, %d failed" % ("OK" if not bad else "FAILED", ok, len(bad)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
