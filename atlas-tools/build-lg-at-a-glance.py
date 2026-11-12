#!/usr/bin/env python3
"""PLOTNUA · DISC-008 Living in the Garden: "Garden rooms in Ireland, at a glance" (SEO-GRR, 12 Nov 2026).

A short, early answer for the search intent "garden rooms Ireland", placed after the hero and
before chapter 01. It adds no new facts. Every figure and every price summary is read from
the page's own Maker Explorer data (script#mx-data, built by build-maker-explorer.py from the
published garden-room universe), so the block cannot disagree with the explorer further down
the page. Each maker's one-line description must still appear, word for word, on that maker's
published PlotNua profile.

Rules:
  R1  Makers: garden-room makers with BOTH a published, indexable PlotNua profile AND at least one
      garden room in the explorer. Listed A to Z. Never ranked, never "recommended".
  R2  Figures: products, makers, and the number confirmed as available in Ireland, taken from
      the explorer's own tab figures; per maker, the count of its garden rooms in the explorer.
  R3  Prices: no figure is shown. Each maker's explorer price labels are summarised by kind
      (euro price shown, price on enquiry, not currently verified, unavailable...). An
      unknown label refuses the build rather than being guessed.
  R4  Images: only an image already authorised for, and used on, this page or this maker's
      profile, from the maker's permitted host, with its required credit; visualisations are
      labelled. Makers without a suitable garden-room photograph are shown text-only.
  R5  Links: the maker's profile, the prices guide, the garden-offices guide, the explorer
      (#suppliers) and the existing planning chapter (#planning-conditions). No new planning
      statement.
  R6  The DISC-008 content guard declaration (living-garden-added.json, "atAGlance") is written
      from the same output, so the guard sees exactly what was built.

  python3 atlas-tools/build-lg-at-a-glance.py            write the block and the declaration
  python3 atlas-tools/build-lg-at-a-glance.py --check    exit 1 if either is stale
"""
import html, json, os, re, sys
from collections import Counter
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "discovery-living-in-the-garden.html")
ADDED = os.path.join(ROOT, "atlas-tools", "premium-discovery", "living-garden-added.json")
BEGIN = "<!-- PN-LG-AT-A-GLANCE v1 · BEGIN · built by atlas-tools/build-lg-at-a-glance.py from #mx-data — do not hand-edit -->"
END = "<!-- PN-LG-AT-A-GLANCE v1 · END -->"
ANCHOR = '<div class="lg-chapter" id="lg-ch01">'

# R1/R4: the makers, A to Z by display name. "says" must appear verbatim on the profile.
MAKERS = [
    {"explorer": "Don Modular Homes", "name": "Don Modular Homes", "profile": "suppliers/don-modular-homes.html",
     "says": "One steel-framed, factory-finished design, from a 25 m² garden room to a four-bedroom home.",
     "pin": ["steel-framed, factory-finished design", "25 m² garden room to a four-bedroom home"],
     "img": {"src": "https://donmodularhomes.ie/images/don-modular-home-exterior.webp",
             "alt": "Visualisation: dark-clad modular home at dusk with a glazed gable end, in a woodland clearing",
             "kind": "Visualisation", "credit": "© Don Modular Homes", "credit_href": None}},
    {"explorer": "Elm Landscaping (Garden Rooms)", "name": "Elm Landscaping", "profile": "suppliers/elm-landscaping.html",
     "says": "A Co. Clare landscaping company that also supplies timber garden rooms and log cabins.",
     "pin": ["a Co. Clare landscaping company, also supplies timber garden rooms and log cabins"],
     "img": None},  # Elm publishes landscaping photographs, not garden-room photographs (R4)
    {"explorer": "Garden Room Ireland", "name": "Garden Room Ireland", "profile": "suppliers/garden-room-ireland.html",
     "says": "Insulated steel-clad garden rooms, built in Dublin.",
     "pin": ["insulated steel-clad garden rooms in Dublin"],
     "img": {"src": "https://static.wixstatic.com/media/fef4b6_f1486b2ae80e4ed2bfeecde2d7e5ea71~mv2.jpg",
             "alt": "Timber-clad garden room under a mature tree, with a stepping-stone path",
             "kind": "Photograph", "credit": "© Garden Room Ireland", "credit_href": None}},
    {"explorer": "Gardenhouse24 Ireland", "name": "Gardenhouse24", "profile": "suppliers/gardenhouse24.html",
     "says": "Nordic-spruce garden rooms and log cabins, as well as outdoor saunas and hot tubs.",
     "pin": ["Nordic-spruce garden rooms, log cabins, outdoor saunas and wood-fired hot tubs"],
     "img": {"src": "https://d1l23c7hiawhq3.cloudfront.net/media/catalog/product/cache/631d00a18cc6f2d63e06f2111d31fb8f/2/0/20220606161922_img_0390_1.jpg",
             "alt": "A natural-timber ALU CONCEPT 44 A garden room with full-height aluminium sliding glazing on two sides",
             "kind": "Photograph", "credit": "Image: Gardenhouse24", "credit_href": "https://gardenhouse24.ie/"}},
    {"explorer": "NOOK Prefab (espacio NOOK)", "name": "NOOK Prefab", "profile": "suppliers/nook-prefab.html",
     "says": "NOOK 10 and NOOK 20 garden rooms, made in Spain and delivered finished.",
     "pin": ["NOOK 10 and NOOK 20 garden rooms, made in Spain and delivered finished"],
     "img": None},  # NOOK asked to preview listings before publication: photograph left for founder decision
    {"explorer": "The Pod Factory", "name": "The Pod Factory", "profile": "suppliers/the-pod-factory.html",
     "says": "Steel-framed garden studios and garden pods, built in Co. Meath and craned into place.",
     "pin": ["steel-framed garden studios, garden pods", "built in Co. Meath and craned into place"],
     "img": {"src": "https://www.thepodfactory.ie/wp-content/uploads/2023/05/Showroom-Pod-17-scaled.jpg",
             "alt": "A single-storey garden pod with cedar cladding, a dark grey render frame and full-height anthracite glazing",
             "kind": "Photograph", "credit": "Image: The Pod Factory", "credit_href": "https://www.thepodfactory.ie/"}},
]

# R3: explorer price label -> kind. Order matters (first match wins).
PRICE_KINDS = [
    ("hold", re.compile(r"^(Not currently taking orders|Out of stock|Price requires verification)")),
    ("unverified", re.compile(r"^Price not currently verified$")),
    ("unavailable", re.compile(r"^Price unavailable$")),
    ("enquiry", re.compile(r"^Price on (enquiry|request)$")),
    ("gbp", re.compile(r"£")),
    ("eur_exworks", re.compile(r"€.*excluding VAT.*Ex works", re.I | re.S)),
    ("eur_excl", re.compile(r"€.*excl", re.I)),
    ("eur_incl", re.compile(r"€.*incl", re.I)),
    ("eur_nostated", re.compile(r"€.*VAT not stated")),
]
# (one product, several products)
KIND_TEXT = {
    "eur_incl": ("Shows a euro price including VAT", "show a euro price including VAT"),
    "eur_nostated": ("Shows a euro price; VAT is not stated", "show a euro price; VAT is not stated"),
    "eur_excl": ("Shows a euro price excluding VAT", "show a euro price excluding VAT"),
    # NOOK founder rule (6 Nov 2026): its qualification travels with any mention of its price.
    "eur_exworks": ("Shows a starting price, ex works. VAT, delivery, foundations and installation are additional. Irish delivery terms require confirmation",
                    "show a starting price, ex works. VAT, delivery, foundations and installation are additional. Irish delivery terms require confirmation"),
    "gbp": ("Shows a UK sterling price", "show a UK sterling price"),
    "enquiry": ("Price on enquiry", "are priced on enquiry"),
    "unverified": ("Price not currently verified, so none is shown", "have prices not currently verified, so none is shown"),
    "unavailable": ("No published price PlotNua can show", "have no published price PlotNua can show"),
    "hold": ("Not currently available to order", "are not currently available to order"),
}
ORDER = ["eur_incl", "eur_nostated", "eur_excl", "eur_exworks", "gbp", "enquiry", "unverified", "unavailable", "hold"]
AVAIL = {"c": "Confirmed", "u": "Not yet confirmed", "r": "No published Irish route"}


def esc(s):
    return html.escape(s, quote=True)


def explorer_data(src):
    m = re.search(r'<script type="application/json" class="pn-mx-config" id="mx-data">(.*?)</script>', src, re.S)
    if not m:
        sys.exit("REFUSED: the Maker Explorer data (#mx-data) is missing")
    d = json.loads(m.group(1))
    tab = next(t for t in d["tabs"] if t["key"] == "gardenRooms")
    return tab


def price_summary(labels):
    kinds = []
    for lab in labels:
        for k, rx in PRICE_KINDS:
            if rx.search(lab):
                kinds.append(k); break
        else:
            sys.exit("REFUSED: R3 unknown explorer price label %r" % lab)
    c, n = Counter(kinds), len(labels)
    if n == 1:
        return KIND_TEXT[kinds[0]][0] + "."
    parts = []
    for k in ORDER:
        if not c[k]:
            continue
        if c[k] == n:
            parts.append(("Both %s" if n == 2 else "All %d %s" % (n, "%s")) % KIND_TEXT[k][1])
        else:
            parts.append("%d of %d %s" % (c[k], n, KIND_TEXT[k][1]))
    return "; ".join(parts) + "."


def avail_summary(codes):
    c = Counter(codes)
    if len(c) == 1:
        return AVAIL[codes[0]]
    return "; ".join("%s for %d" % (AVAIL[k], v) for k, v in c.items())


def build(src):
    tab = explorer_data(src)
    fig = tab["figures"]
    makers = {m["m"]: m for m in tab["makers"]}
    rows, credits = [], []
    for mk in MAKERS:
        prof = os.path.join(ROOT, mk["profile"])
        if not os.path.exists(prof):
            sys.exit("REFUSED: R1 profile missing: " + mk["profile"])
        ps = html.unescape(open(prof, encoding="utf-8").read())
        if not re.search(r'<meta name="robots" content="index, follow"', ps):
            sys.exit("REFUSED: R1 profile is not indexable: " + mk["profile"])
        for p in mk["pin"]:
            if p not in ps:
                sys.exit("REFUSED: R1 %s no longer says %r" % (mk["profile"], p))
        if mk["explorer"] not in makers or not makers[mk["explorer"]]["p"]:
            sys.exit("REFUSED: R1 %s has no garden rooms in the explorer" % mk["explorer"])
        prods = makers[mk["explorer"]]["p"]
        labels = [p[4] for p in prods]
        codes = [p[3] for p in prods]
        img = mk["img"]
        if img:
            if img["src"] not in ps and img["src"] not in src:
                sys.exit("REFUSED: R4 image is not already used on this page or the profile: " + img["src"])
            tag = '<img class="lg-glance-img" src="%s" alt="%s" width="88" height="66" loading="lazy" decoding="async">' % (esc(img["src"]), esc(img["alt"]))
            fig_html = '<span class="lg-glance-thumb">%s<span class="lg-glance-kind">%s</span></span>' % (tag, esc(img["kind"]))
            c = esc(img["credit"])
            credits.append('<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (esc(img["credit_href"]), c) if img["credit_href"] else c)
        else:
            fig_html = ""
        n = len(prods)
        rows.append(
            '          <tr><th scope="row"><span class="lg-glance-maker">%s<a href="%s">%s</a></span></th>\n'
            '            <td data-l="What they make">%s</td>\n'
            '            <td data-l="Garden rooms on PlotNua">%d</td>\n'
            '            <td data-l="Available in Ireland">%s</td>\n'
            '            <td data-l="Prices on PlotNua">%s</td></tr>' % (
                fig_html, esc(mk["profile"]), esc(mk["name"]), esc(mk["says"]), n,
                esc(avail_summary(codes)), esc(price_summary(labels))))
    lead = ("PlotNua has researched %s garden rooms from %d makers. %s of them are confirmed as available "
            "in Ireland." % ("{:,}".format(fig["products"]), fig["makers"], "{:,}".format(fig["confirmed"])))
    block = """%s
<section class="lg-glance" id="garden-rooms-at-a-glance" aria-labelledby="lg-glance-h">
  <style>
    .lg-glance{margin:0 0 72px;padding:0 0 48px;border-bottom:1px solid rgba(242,235,224,.14)}
    .lg-glance .gr-compare{min-width:720px}
    .lg-glance .gr-compare th,.lg-glance .gr-compare td{padding:14px 14px}
    .lg-glance .gr-compare tbody th{width:26%%}
    .lg-glance-maker{display:flex;align-items:center;gap:14px}
    .lg-glance-thumb{flex:0 0 72px;width:72px}
    .lg-glance-img{display:block;width:72px;height:54px;object-fit:cover;border-radius:2px}
    .lg-glance-kind{display:block;font-size:10.5px;letter-spacing:.04em;opacity:.7;margin-top:3px;font-weight:400}
    .lg-glance a{color:inherit;text-decoration:underline;text-decoration-color:rgba(143,175,138,.6);text-underline-offset:4px}
    .lg-glance a:hover,.lg-glance a:focus-visible{text-decoration-color:currentColor}
    .lg-glance .lg-route-links{margin-top:26px}
    @media (max-width:640px){
      .lg-glance .gr-compare-wrap{overflow:visible}
      .lg-glance .gr-compare,.lg-glance .gr-compare tbody,.lg-glance .gr-compare tr,.lg-glance .gr-compare th,.lg-glance .gr-compare td,.lg-glance .gr-compare caption{display:block;width:auto;min-width:0}
      .lg-glance .gr-compare thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
      .lg-glance .gr-compare tr{padding:18px 0;border-bottom:1px solid rgba(242,235,224,.14)}
      .lg-glance .gr-compare th,.lg-glance .gr-compare td{border:0;padding:4px 0}
      .lg-glance .gr-compare tbody th{width:auto;padding-bottom:10px}
      .lg-glance .gr-compare tr{display:flex;flex-wrap:wrap;column-gap:28px}
      .lg-glance .gr-compare tr>th,.lg-glance .gr-compare tr>td{flex:0 0 100%%}
      .lg-glance .gr-compare td[data-l="Garden rooms on PlotNua"],.lg-glance .gr-compare td[data-l="Available in Ireland"]{flex:0 0 auto}
      .lg-glance .gr-compare td::before{content:attr(data-l);display:block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;opacity:.65;margin-top:6px}
    }
  </style>
  <p class="lg-kicker">At a glance</p>
  <h2 class="lg-title" id="lg-glance-h">Garden rooms in Ireland, compared.</h2>
  <p class="lg-stand">%s Below are the makers with a published PlotNua profile, A to Z: what each makes, how many of its garden rooms PlotNua lists, and how their prices appear.</p>
  <div class="gr-compare-wrap" role="region" aria-label="Garden room makers compared; scroll horizontally on small screens" tabindex="0">
    <table class="gr-compare">
      <caption>Makers with a published PlotNua profile, A to Z. An index, not a ranking; PlotNua has no commercial arrangement with any maker listed here. Counts and price notes come from the Maker Explorer below.</caption>
      <thead><tr><th scope="col">Maker</th><th scope="col">What they make</th><th scope="col">Garden rooms on PlotNua</th><th scope="col">Available in Ireland</th><th scope="col">Prices on PlotNua</th></tr></thead>
      <tbody>
%s
      </tbody>
    </table>
  </div>
  <p class="pd-small" style="margin-top:14px">Images: %s. Images are shown as supplied by each maker; a visualisation is computer-generated, not a photograph.</p>
  <ul class="lg-route-links" role="list">
    <li><a href="garden-room-prices-ireland.html">Compare published prices: garden room prices in Ireland</a></li>
    <li><a href="garden-offices-ireland.html">Working from home: garden offices in Ireland</a></li>
    <li><a href="#suppliers">Every maker and all %s garden rooms</a></li>
    <li><a href="#planning-conditions">What the 2026 planning conditions say</a></li>
  </ul>
</section>
%s
""" % (BEGIN, esc(lead), "\n".join(rows), "; ".join(credits), "{:,}".format(fig["products"]), END)
    return block


class _P(HTMLParser):
    BLOCK = {"p", "h1", "h2", "h3", "h4", "li", "td", "th", "caption", "figcaption", "dt", "dd", "summary", "blockquote"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.blocks, self.links, self.imgs, self.ids, self.skip = [], [], [], [], [], 0

    def handle_starttag(self, t, a):
        a = dict(a)
        if a.get("id"): self.ids.append(a["id"])
        if t == "a" and a.get("href"): self.links.append(a["href"])
        if t == "img" and a.get("src"): self.imgs.append(a["src"])
        if t in ("style", "script", "svg"): self.skip += 1
        if t in ("img", "br", "source", "meta", "link", "input"): return
        self.stack.append([t, []])

    def handle_endtag(self, t):
        if not self.stack: return
        tag, buf = self.stack.pop()
        if tag in ("style", "script", "svg"): self.skip -= 1
        txt = re.sub(r"\s+", " ", "".join(buf)).strip()
        if tag in self.BLOCK and txt: self.blocks.append(txt)
        if self.stack: self.stack[-1][1].append("".join(buf) + " ")

    def handle_data(self, d):
        if self.skip or not self.stack: return
        self.stack[-1][1].append(d)


def _guard_parser():
    """The DISC-008 content guard's own parser, so the declaration is exactly what the guard sees."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("lg_guard", os.path.join(ROOT, "atlas-tools", "prove-premium-discovery-living-garden.py"))
    g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
    return g.Blocks()


def declaration(block):
    p = _guard_parser(); p.feed(block); p.close()
    p.blocks = p.out
    return {"declared": "2026-11-12, SEO-GRR (garden rooms Ireland visibility): an early 'at a glance' comparison "
                        "after the hero, built by atlas-tools/build-lg-at-a-glance.py from the page's Maker Explorer "
                        "data. Founder approval required before release.",
            "blocks": p.blocks, "links": p.links, "imgs": p.imgs, "ids": p.ids}


def splice(src, block):
    if BEGIN in src:
        a = src.index(BEGIN); z = src.index(END) + len(END) + 1
        return src[:a] + block + src[z:]
    i = src.index(ANCHOR)
    return src[:i] + block + src[i:]


def main():
    check = "--check" in sys.argv
    src = open(PAGE, encoding="utf-8").read()
    block = build(src)
    new = splice(src, block)
    added = json.load(open(ADDED, encoding="utf-8"))
    want = declaration(block)
    new_added = dict(added); new_added["atAGlance"] = [want]
    if check:
        bad = []
        if new != src: bad.append("the at-a-glance block on the page is stale or missing")
        if added.get("atAGlance") != [want]: bad.append("the DISC-008 guard declaration (atAGlance) is stale or missing")
        if bad:
            print("AT A GLANCE · STALE: " + "; ".join(bad)); sys.exit(1)
        print("AT A GLANCE · OK — block and guard declaration match the Maker Explorer data and the six profiles")
        return
    open(PAGE, "w", encoding="utf-8").write(new)
    open(ADDED, "w", encoding="utf-8").write(json.dumps(new_added, ensure_ascii=False, indent=1) + "\n")
    print("AT A GLANCE · WROTE block (%d makers) and the atAGlance declaration" % len(MAKERS))


if __name__ == "__main__":
    main()
